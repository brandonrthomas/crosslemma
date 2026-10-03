#!/usr/bin/env python3
"""
Worker sandbox + ledger hook. One file decides what a worker may touch and what the orchestrator
may not do without an operator approval; it is live code for every sandboxed command.

Runs on PreToolUse / PostToolUse / SubagentStart / SubagentStop.
- Main (orchestrator) session: no restrictions; hook exits immediately.
- Subagents: bound to exactly one run directory (<root>/workspace-*/runs/<run>/).
    * The first file tool call (normally `Read <run>/BRIEF.md`) binds the agent to that run.
    * Read/Write/Edit/Glob/Grep/NotebookEdit: path must resolve inside the bound run dir.
    * Bash: rewritten to execute inside bwrap with ONLY the run dir mounted rw,
      no network, no /home. `ledger <text>` is intercepted and appended to the
      global ledger (agents can write to the ledger, never read it).
    * Only a small allowlist of tools is permitted (no Agent, Web*, MCP, Skill, ...).
- Every subagent tool call, denial, start and stop is appended to LEDGER.log.
"""
import hashlib, json, os, re, shlex, sys, time, glob

ROOT = "@ROOT@"
LEAN_DIR = os.path.join(ROOT, "lean")   # shared Mathlib lake project, mounted read-only
ELAN = "@ELAN@"              # Lean toolchain, mounted read-only
LEDGER = os.path.join(ROOT, "LEDGER.log")
STATE = os.path.join(ROOT, ".claude", "state")
BIND_DIR = os.path.join(STATE, "bind")
DEBUG = os.path.join(STATE, "hook-debug.jsonl")
RUNS_GLOB = os.path.join(ROOT, "workspace-*", "runs")

ALLOWED_TOOLS = {"Bash", "Read", "Write"}
WORKER_TYPE = "kit-worker"
LEDGER_SHIM = os.path.join(ROOT, ".claude", "sandbox", "ledger")
PATH_TOOLS = {"Read": "file_path", "Write": "file_path"}


def now():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def ledger(actor, run, event, detail=""):
    detail = " ".join(str(detail).split())
    if len(detail) > 400:
        detail = detail[:400] + "…"
    line = f"{now()} | {actor} | {run or '-'} | {event} | {detail}\n"
    with open(LEDGER, "a") as f:
        f.write(line)


def deny(reason, event="PreToolUse"):
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": event,
        "permissionDecision": "deny",
        "permissionDecisionReason": reason}}))
    sys.exit(0)


def allow(updated=None):
    out = {"hookEventName": "PreToolUse", "permissionDecision": "allow"}
    if updated is not None:
        out["updatedInput"] = updated
    print(json.dumps({"hookSpecificOutput": out}))
    sys.exit(0)


def agent_key(inp):
    aid = inp.get("agent_id")
    if aid:
        return "agent:" + str(aid)[:12]
    tp = inp.get("transcript_path", "")
    return "agent:" + hashlib.sha1(tp.encode()).hexdigest()[:12]


def is_subagent(inp):
    return bool(inp.get("agent_id")) or "/subagents/" in inp.get("transcript_path", "")


def run_dirs():
    return [os.path.realpath(d) for d in glob.glob(os.path.join(RUNS_GLOB, "*")) if os.path.isdir(d)]


def run_of(path):
    """Return the run dir containing `path`, or None."""
    rp = os.path.realpath(path)
    for rd in run_dirs():
        if rp == rd or rp.startswith(rd + os.sep):
            return rd
    return None


def get_binding(key):
    p = os.path.join(BIND_DIR, key.replace(":", "_"))
    if os.path.exists(p):
        return open(p).read().strip()
    return None


def set_binding(key, rd):
    os.makedirs(BIND_DIR, exist_ok=True)
    with open(os.path.join(BIND_DIR, key.replace(":", "_")), "w") as f:
        f.write(rd)


def drain_outbox(key, rd):
    if not rd:
        return
    ob = os.path.join(rd, ".ledger-outbox")
    try:
        if os.path.islink(ob) or not os.path.isfile(ob):
            return
        with open(ob, "r+", errors="replace") as f:
            data = f.read(64000)
            f.seek(0); f.truncate()
        for line in data.splitlines():
            if line.strip():
                ledger(key, os.path.basename(rd), "NOTE", line)
    except Exception as e:
        ledger(key, os.path.basename(rd), "ERROR", f"outbox drain: {e!r}")


LIMIT_DEFAULTS = {"cpu_hours": 8, "threads": 8, "mem_gb": 16}


def run_limits(rd):
    """RD/.limits written by bin/new-run (LESSONS.md "Limits are enforced, not promised"); defaults when absent or malformed."""
    lim = dict(LIMIT_DEFAULTS)
    try:
        with open(os.path.join(rd, ".limits")) as f:
            d = json.load(f)
        for k in lim:
            if isinstance(d.get(k), (int, float)) and d[k] > 0:
                lim[k] = d[k]
    except Exception:
        pass
    lim["threads"] = max(1, min(64, int(lim["threads"])))
    lim["cpu_seconds"] = max(60, int(float(lim["cpu_hours"]) * 3600))
    return lim


def bwrap_command(rd, cmd):
    lim = run_limits(rd)
    n = str(lim["threads"])
    # Enforced, not promised (audit F9): RLIMIT_CPU per process = the run's whole CPU budget (a single
    # process may never exceed it; the tree cap is the cgroup quota bin/limits-exec sets), and every
    # BLAS/OpenMP thread pool is capped by environment so the worker need not remember to.
    cmd = f"ulimit -t {lim['cpu_seconds']}; {cmd}"
    args = ["env", "-i", "PATH=/usr/bin:/bin", "bwrap",
            "--ro-bind", "/usr", "/usr",
            "--symlink", "usr/lib", "/lib",
            "--symlink", "usr/lib64", "/lib64",
            "--symlink", "usr/bin", "/bin",
            "--symlink", "usr/sbin", "/sbin",
            "--tmpfs", "/etc",
            "--ro-bind", "/etc/alternatives", "/etc/alternatives",
            "--ro-bind", "/etc/ld.so.cache", "/etc/ld.so.cache",
            "--ro-bind", "/etc/localtime", "/etc/localtime",
            "--ro-bind", "/etc/python3.12", "/etc/python3.12",
            "--remount-ro", "/etc",
            "--proc", "/proc",
            "--dev", "/dev",
            "--tmpfs", "/tmp",
            "--bind", rd, rd,
            "--ro-bind", LEDGER_SHIM, "/opt/kit/bin/ledger",
            "--ro-bind", ELAN, ELAN,
            "--ro-bind", LEAN_DIR, LEAN_DIR,
            "--chdir", rd,
            "--unshare-all",
            "--hostname", "sandbox",
            "--die-with-parent",
            "--clearenv",
            "--setenv", "HOME", rd,
            "--setenv", "TMPDIR", "/tmp",
            "--setenv", "PATH", "/opt/kit/bin:" + ELAN + "/bin:/usr/bin:/bin",
            "--setenv", "ELAN_HOME", ELAN,
            "--setenv", "KIT_LEAN", LEAN_DIR,
            "--setenv", "KIT_RUN", rd,
            "--setenv", "PYTHONDONTWRITEBYTECODE", "1",
            "--setenv", "OMP_NUM_THREADS", n,
            "--setenv", "OPENBLAS_NUM_THREADS", n,
            "--setenv", "MKL_NUM_THREADS", n,
            "--setenv", "NUMEXPR_NUM_THREADS", n,
            "--setenv", "KIT_THREADS", n,
            "--setenv", "KIT_CPU_HOURS", str(lim["cpu_hours"]),
            "--setenv", "KIT_MEM_GB", str(lim["mem_gb"]),
            "--", "/bin/bash", "-c", cmd]
    return " ".join(shlex.quote(a) for a in args)


HANDOFF = os.path.join(ROOT, "HANDOFF.md")
HANDOFF_RE = re.compile(r"HANDOFF\.md")


def touches_handoff(tool, ti):
    if tool in ("Write", "Edit", "MultiEdit", "NotebookEdit"):
        p = ti.get("file_path") or ""
        return os.path.realpath(p) == HANDOFF if p else False
    if tool == "Bash":
        return bool(HANDOFF_RE.search(ti.get("command", "")))
    return False


def archive_handoff_once(inp):
    """Run bin/handoff-archive before the first HANDOFF.md-touching call of this orchestrator session.
    A failed archive denies the call: losing a handoff version is worse than a retried edit."""
    sid = str(inp.get("session_id") or "nosession")
    mark = os.path.join(STATE, "handoff-archived-" + re.sub(r"[^A-Za-z0-9_-]", "_", sid)[:40])
    if os.path.exists(mark) or not os.path.isfile(HANDOFF):
        return
    import subprocess
    p = subprocess.run([sys.executable, os.path.join(ROOT, "bin", "handoff-archive"), "--session", sid[:8]],
                       capture_output=True, text=True, timeout=15)
    if p.returncode != 0:
        ledger("orchestrator", None, "DENY", f"handoff-archive failed: {(p.stderr or p.stdout).strip()[:200]}")
        deny("HANDOFF.md is archived before it is touched, and bin/handoff-archive failed: "
             + (p.stderr or p.stdout).strip()[:300])
    with open(mark, "w") as f:
        f.write(p.stdout)
    ledger("orchestrator", None, "HANDOFF-ARCHIVE", p.stdout.strip()[:300])


def main():
    raw = sys.stdin.read()
    try:
        inp = json.loads(raw)
    except Exception:
        sys.exit(0)
    event = inp.get("hook_event_name", "")
    os.makedirs(STATE, exist_ok=True)
    if os.environ.get("KIT_HOOK_DEBUG") or os.path.exists(os.path.join(STATE, "debug-on")):
        with open(DEBUG, "a") as f:
            f.write(json.dumps({k: v for k, v in inp.items() if k != "tool_response"})[:2000] + "\n")

    if event in ("SubagentStart", "SubagentStop"):
        key = agent_key(inp)
        drain_outbox(key, get_binding(key))
        ledger(key, get_binding(key) and os.path.basename(get_binding(key)),
               event.replace("Subagent", "").upper(),
               f"type={inp.get('agent_type','?')}")
        sys.exit(0)

    ext_run = os.environ.get("KIT_WORKER_RUN")
    if ext_run and not is_subagent(inp):
        # LESSONS.md "Every worker is a headless main process": a headless worker is a `claude -p` MAIN process launched by bin/run-external
        # with KIT_WORKER_RUN=<run dir>. Treat it exactly like a kit-worker subagent, pre-bound to
        # that run. Operator-approved 2026-09-16 09:44 MST.
        rd = run_of(ext_run)
        if rd is None:
            ledger("hook", None, "DENY", f"KIT_WORKER_RUN={ext_run} is not a run dir")
            if event == "PreToolUse":
                deny("KIT_WORKER_RUN does not name a run directory.")
            sys.exit(0)
        inp["agent_id"] = "ext-" + hashlib.sha1(str(inp.get("session_id", ext_run)).encode()).hexdigest()[:8]
        inp["agent_type"] = WORKER_TYPE
        if get_binding(agent_key(inp)) is None:
            set_binding(agent_key(inp), rd)
            ledger(agent_key(inp), os.path.basename(rd), "START", f"type=external main-process worker, pre-bound to {rd}")

    if not is_subagent(inp):
        # orchestrator session: unrestricted, but every call is recorded
        if event == "PreToolUse":
            ti0 = inp.get("tool_input", {}) or {}
            t0 = inp.get("tool_name", "")
            d = ti0.get("description") or ti0.get("file_path") or ti0.get("command") or ti0.get("prompt") or ""
            ledger("orchestrator", None, "CALL", f"{t0} {d}")
            if touches_handoff(t0, ti0):
                # LESSONS.md "`HANDOFF.md` is archived before it is touched" (operator direction 2026-09-16 20:55): every rewrite of HANDOFF.md keeps the
                # previous version. Archive once per session, before the first call that touches it.
                archive_handoff_once(inp)
            if t0 == "Agent":
                # Worker launches must not carry `name` (replaces agent_type in hook input, run 003)
                # or `isolation` (a git worktree guard then refuses the bwrap-rewritten Bash, run 024).
                # Strip them rather than trust the launching model to omit them. Operator-approved 08:04 MST.
                bad = {k: ti0[k] for k in ("name", "isolation", "team_name") if ti0.get(k)}
                if bad:
                    ledger("orchestrator", None, "REWRITE", f"Agent: stripped {bad}")
                    allow({k: v for k, v in ti0.items() if k not in bad})
        sys.exit(0)

    key = agent_key(inp)
    drain_outbox(key, get_binding(key))
    if event == "PreToolUse" and inp.get("agent_type") != WORKER_TYPE:
        ledger(key, None, "DENY", f"agent_type={inp.get('agent_type')} is not {WORKER_TYPE}")
        deny(f"Only {WORKER_TYPE} agents may use tools in this project.")
    tool = inp.get("tool_name", "")
    ti = inp.get("tool_input", {}) or {}
    cwd = inp.get("cwd", ROOT)
    bound = get_binding(key)
    run_name = os.path.basename(bound) if bound else None

    if event == "PostToolUse":
        resp = inp.get("tool_response")
        size = len(json.dumps(resp)) if resp is not None else 0
        ledger(key, run_name, "DONE", f"{tool} resp_bytes={size}")
        sys.exit(0)

    if event != "PreToolUse":
        sys.exit(0)

    if tool not in ALLOWED_TOOLS:
        ledger(key, run_name, "DENY", f"{tool} not in subagent allowlist")
        if tool in ("SubagentHandback", "SendMessage"):
            deny("No report channel exists here and none is needed: the files you wrote under output/ are "
                 "your complete deliverable and are read from disk by the orchestrator. Do not retry this or any "
                 "messaging tool. End your turn now with a one-line plain-text summary.")
        deny(f"Tool {tool} is not available to sandboxed agents. Allowed: {sorted(ALLOWED_TOOLS)}")

    if tool in PATH_TOOLS:
        for fld in ("pattern", "glob"):
            v = ti.get(fld) if tool in ("Glob", "Grep") else None
            if tool == "Grep" and fld == "pattern":
                continue  # Grep pattern is a regex, not a path
            if v and (v.startswith("/") or v.startswith("~") or ".." in v):
                ledger(key, run_name, "DENY", f"{tool} {fld}={v} (escaping pattern)")
                deny(f"{tool} {fld} must be relative to your run directory and must not contain '..'.")
        p = ti.get(PATH_TOOLS[tool])
        if not p:
            if tool in ("Glob", "Grep") and bound:
                p = bound
                ti = dict(ti, path=bound)
            else:
                ledger(key, run_name, "DENY", f"{tool} without explicit path")
                deny("Give an explicit absolute path inside your run directory.")
        if not os.path.isabs(p):
            p = os.path.join(bound or cwd, p)
        rd = run_of(p)
        if rd is None:
            ledger(key, run_name, "DENY", f"{tool} {p} (outside runs)")
            deny(f"Access denied: {p} is outside your run directory. "
                 f"You may only touch files under your run directory (absolute paths).")
        if bound is None:
            set_binding(key, rd)
            bound, run_name = rd, os.path.basename(rd)
            ledger(key, run_name, "BIND", f"bound to {rd}")
        if rd != bound:
            ledger(key, run_name, "DENY", f"{tool} {p} (other run {os.path.basename(rd)})")
            deny(f"Access denied: {p} is outside your run directory. "
                 f"You may only touch files under your run directory (absolute paths).")
        ledger(key, run_name, "CALL", f"{tool} {p}")
        allow(dict(ti))

    if tool == "Bash":
        cmd = ti.get("command", "")
        if bound is None:
            ledger(key, run_name, "DENY", f"Bash before binding: {cmd[:150]}")
            deny("Before running any command, Read the BRIEF.md in your run directory "
                 "(absolute path) so the sandbox can bind you to it.")
        ledger(key, run_name, "CALL", f"Bash {cmd[:300]}")
        allow(dict(ti, command=bwrap_command(bound, cmd)))

    # any other allowlisted tool without a path
    ledger(key, run_name, "CALL", tool)
    allow()


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception as e:  # never let a hook crash open the sandbox
        try:
            ledger("hook", None, "ERROR", repr(e))
        except Exception:
            pass
        deny(f"Sandbox hook error: {e!r}")
