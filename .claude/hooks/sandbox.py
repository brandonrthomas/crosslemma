#!/usr/bin/python3
"""
Worker sandbox + ledger hook. One file decides what a worker may touch and what the orchestrator
may not do without a user approval; it is live code for every sandboxed command.

Runs on PreToolUse / PostToolUse / SubagentStart / SubagentStop.
- Orchestrator (the main session): every call ledgered, for this tree's own sessions only (LESSONS.md "The hook
  ledgers only its own tree's sessions"); HANDOFF.md archived before the session first touches it; otherwise
  unrestricted except for the gate (gate_orchestrator below; RULES.md §9): the approval tool but its one plain
  `--digest` call, which becomes the user's tap prompt, worded from the bytes (LESSONS.md "Every launch and every
  ledger append consumes a byte-bound"); writes into, or commands naming, the approvals directory; the packet rules and their exceptions; the
  environment files (kit-env.json, .kit-*); reads of LEDGER.log; a bare headless launch; the messaging and workflow
  tools; every Agent call of a worker type, approved or not; keys typed into another tmux pane and any touch of
  Clatter's files but through its dispatcher. A broken gate refuses gated calls only.
- Workers are headless main processes started by bin/run-external, recognised by KIT_WORKER_RUN in their process
  environment and pre-bound to that run directory (LESSONS.md "Every worker is a headless main process"):
    * Read and Write only inside the bound run dir (by realpath); Bash rewritten into bwrap: the run dir read-write,
      the OS and kit-env.json's modules read-only (bin/_env.py), tmpfs /etc and /tmp, no network, a clean
      environment, the run's limits, the root remounted read-only after the binds. `ledger <text>` goes to a shim
      that queues lines for LEDGER.log, which the worker can never read.
    * Tools: Read, Write, Bash only; a networked worker (KIT_WORKER_NET=1) also WebSearch and WebFetch, with a
      Bash sandbox that shares the network. Granted licence modules come only from KIT_WORKER_MODULES.
- A subagent of any other type is refused every tool; a worker is never a subagent.
- Every worker tool call, denial, binding, start and stop is appended to LEDGER.log.
"""
import hashlib, json, os, re, shlex, stat, sys, time, glob, fnmatch

# The gate's root is this file's own location, never an environment variable: a variable the
# orchestrator can set would move the gate's idea of the tree and so move the gate.
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
# What a worker's sandbox mounts beyond the system comes from the instance's environment file, read by bin/_env.py from
# FILES in the tree and never from an environment variable (a variable the orchestrator can set would move a mount):
# kit-env.json, or for an instance made before kit-v0.5 its .kit-lean / .kit-sage (LESSONS.md "The environment files are
# the user's"). Loaded from this tree's own bin/, as approval_lib() loads the approval code.


def kit_env():
    """(the module, the loaded environment), or (None, None) when this tree has no loadable bin/_env.py: then no module
    is mounted, which is the safe side (a worker without its module fails loudly; it is never given more)."""
    import importlib.util
    try:
        spec = importlib.util.spec_from_file_location("kit_env", os.path.join(ROOT, "bin", "_env.py"))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod, mod.load(ROOT)
    except Exception as e:
        print(f"sandbox hook: bin/_env.py not loaded ({e}); no module is mounted", file=sys.stderr)
        return None, None


def worker_granted():
    """Modules granted to this worker's launch beyond the always-mounted ones: bin/run-external sets KIT_WORKER_MODULES
    after consuming an approval that bound --module, in the worker's process environment, which the worker cannot change
    (as KIT_WORKER_NET); never read from a file in the run directory, which it can."""
    if not os.environ.get("KIT_WORKER_RUN"):
        return ()
    return tuple(m for m in os.environ.get("KIT_WORKER_MODULES", "").split(",") if m)


LEDGER = os.path.join(ROOT, "LEDGER.log")
STATE = os.path.join(ROOT, ".claude", "state")
BIND_DIR = os.path.join(STATE, "bind")
DEBUG = os.path.join(STATE, "hook-debug.jsonl")
RUNS_GLOB = os.path.join(ROOT, "workspace-*", "runs")

ALLOWED_TOOLS = {"Bash", "Read", "Write"}
WORKER_TYPE = "kit-worker"
# LESSONS.md "Every worker is a headless main process" (user 2026-09-22 14:55): workers are never launched as subagents of an orchestrator session; a
# subagent inherits the session's harness text (auto-mode note, attribution guidance, the report request, MCP
# instructions), a headless worker does not. Every worker is a main process started by bin/run-external. The
# per-effort agent variants of LESSONS.md "Networked and Codex launches need their flags bound" are gone with the route; `kit-worker` stays: it is the agent the
# headless no-network route loads, and the type the hook gives an external worker.
WORKER_TYPES = {WORKER_TYPE}
LEDGER_SHIM = os.path.join(ROOT, ".claude", "sandbox", "ledger")
PATH_TOOLS = {"Read": "file_path", "Write": "file_path"}


def now():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


# LESSONS.md "The hook ledgers only its own tree's sessions": the hook ledgers only for sessions of this tree. A session opened elsewhere
# that loads this tree's settings (a copied .claude/, as once happened) would otherwise write CALL lines describing
# another tree's tool calls into this LEDGER.log. A session is foreign when
# neither its project directory (CLAUDE_PROJECT_DIR, set by Claude Code for hook commands) nor the call's cwd lies
# inside ROOT; either one inside makes it ours, so an orchestrator that cd's out of the tree is still recorded. With
# neither known, the session counts as ours (fail closed). Workers (KIT_WORKER_RUN) are never foreign. Decisions do
# not change for a foreign session: the gate still refuses, subagents are still refused tools. Only the ledger stays
# quiet, except for the gate's own lines (DENY-GATE, ASK-APPROVE), which are kept and marked with the foreign project.
FOREIGN = None                     # None: ours; else the foreign session's project directory (or cwd)
FOREIGN_KEPT = {"DENY-GATE", "ASK-APPROVE"}


def inside_root(d):
    rp, root = os.path.realpath(d), os.path.realpath(ROOT)
    return rp == root or rp.startswith(root + os.sep)


def foreign_session(inp):
    """The foreign session's project directory (or cwd), or None when the session is this tree's."""
    if os.environ.get("KIT_WORKER_RUN"):
        return None
    dirs = [d for d in (os.environ.get("CLAUDE_PROJECT_DIR"), inp.get("cwd")) if d]
    if not dirs or any(inside_root(d) for d in dirs):
        return None
    return dirs[0]


def ledger(actor, run, event, detail=""):
    if FOREIGN is not None:
        if event not in FOREIGN_KEPT:
            return
        actor = f"foreign-session({FOREIGN})"
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


UNRECORDED = None   # set when the orchestrator's call could not be written to the ledger (P-12)


def unrecorded_note():
    return {"systemMessage": f"kit hook: LEDGER.log could not be written ({UNRECORDED!r}); this call is not recorded. "
                             "Gated calls are refused until it can be."} if UNRECORDED is not None else {}


def allow(updated=None):
    out = {"hookEventName": "PreToolUse", "permissionDecision": "allow"}
    if updated is not None:
        out["updatedInput"] = updated
    print(json.dumps(dict({"hookSpecificOutput": out}, **unrecorded_note())))
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


def effort_seen(transcript):
    """Effort values a subagent's requests carried, counted in its transcript (user 2026-09-22, item 5: the
    approval binds the effort variant; this records what the model's requests actually said)."""
    counts = {}
    try:
        with open(transcript, errors="replace") as f:
            for v in re.findall(r'"effort":"([a-z]+)"', f.read()):
                counts[v] = counts.get(v, 0) + 1
    except OSError:
        return None
    return ",".join(f"{k}*{v}" for k, v in sorted(counts.items())) or "none-recorded"   # the source's method change 77


def drain_outbox(key, rd):
    if not rd:
        return
    ob = os.path.join(rd, ".ledger-outbox")
    try:
        if os.path.islink(ob) or not os.path.isfile(ob):
            return
        # P-12 C2: the check above is not the guard; a link made after it is refused by O_NOFOLLOW, and anything but a
        # regular file is left alone
        fd = os.open(ob, os.O_RDWR | os.O_NOFOLLOW | os.O_NONBLOCK)
        with os.fdopen(fd, "r+", errors="replace") as f:
            if not stat.S_ISREG(os.fstat(fd).st_mode):
                return
            data = f.read(64000)
            f.seek(0); f.truncate()
        for line in data.splitlines():
            if line.strip():
                ledger(key, os.path.basename(rd), "NOTE", line)
    except Exception as e:
        ledger(key, os.path.basename(rd), "ERROR", f"outbox drain: {e!r}")


LIMIT_DEFAULTS = {"cpu_hours": 8, "threads": 8, "mem_gb": 16}


def run_limits(rd):
    """RD/.limits written by bin/new-run (LESSONS.md "Limits are enforced, not promised"); defaults when absent or malformed.
    Pending item P-11 (c): once launched, the copy bin/run-external kept at the launch (its approved bytes) is read, from
    the host's state directory, where no worker writes; the run's own file is the worker's to rewrite."""
    lim = dict(LIMIT_DEFAULTS)
    kept = os.path.join(STATE, "ext", os.path.basename(rd), "limits.json")
    try:
        with open(kept if os.path.isfile(kept) else os.path.join(rd, ".limits")) as f:
            d = json.load(f)
        for k in lim:
            if isinstance(d.get(k), (int, float)) and d[k] > 0:
                lim[k] = d[k]
    except Exception:
        pass
    lim["threads"] = max(1, min(64, int(lim["threads"])))
    lim["cpu_seconds"] = max(60, int(float(lim["cpu_hours"]) * 3600))
    return lim


NET_TOOLS = {"WebSearch", "WebFetch"}   # LESSONS.md "Networked and Codex launches need their flags bound": only for a networked external worker
HARNESS_BIN = os.path.join(ROOT, "harness", "bin")


def net_worker():
    """A networked worker is an external main process that bin/run-external started with --network, after consuming
    an approval that bound that flag. The marker is in the process environment, which the worker cannot change;
    a file in the run directory would not do, since the worker can write there."""
    return bool(os.environ.get("KIT_WORKER_RUN")) and os.environ.get("KIT_WORKER_NET") == "1"


def net_bwrap_parts():
    """Extra bwrap arguments for a networked worker's Bash: name resolution and TLS roots under /etc, the search
    helpers, and the environment they need. The network namespace is shared with the host (--share-net)."""
    etc = []
    for f in ("/etc/hosts", "/etc/nsswitch.conf", "/etc/ssl", "/etc/ca-certificates", "/etc/ca-certificates.conf"):
        if os.path.exists(f):
            etc += ["--ro-bind", f, f]
    etc += ["--ro-bind", os.path.realpath("/etc/resolv.conf"), "/etc/resolv.conf"]
    helpers = []
    for h in ("brave", "exa", "exa-contents"):
        helpers += ["--ro-bind", os.path.join(HARNESS_BIN, h), "/opt/kit/bin/" + h]
    env = ["--setenv", "SSL_CERT_FILE", "/etc/ssl/certs/ca-certificates.crt",
           "--setenv", "GATEWAY", os.environ.get("KIT_NET_GATEWAY", ""),
           "--setenv", "SEARXNG_URL", os.environ.get("SEARXNG_URL", "http://localhost:7764")]
    return etc, helpers, env


# The system Python's /etc/pythonX.Y, whichever version /usr/bin/python3 is (it was /etc/python3.12 by name).
PY_ETC = "/etc/" + os.path.basename(os.path.realpath("/usr/bin/python3"))
PY_ETC = PY_ETC if os.path.isdir(PY_ETC) else None
LICENCE_SOCK_RE = re.compile(r"^\d+-[0-9a-f]{8}-lic\d+\.sock$")


def licence_parts(envmod, env, granted, rd, net):
    """(/etc args, mount args, command prefix) for a worker granted a licence module on a run without the network: the
    relay sockets bin/run-external started (KIT_WORKER_LICENCE_SOCKS, in the worker's process environment, which it cannot
    change), the in-sandbox forwarder, and an /etc/hosts naming each licence host at 127.0.0.1. Each socket must be named
    as the relay names it and be a socket, and the ports must be the granted modules' endpoints in order; otherwise
    nothing is mounted (the worker's licensed tool then fails to reach its server, loudly). A networked run has the
    host's network already and gets none of this."""
    import stat
    if net or not envmod or not granted:
        return [], [], ""
    endpoints = envmod.licence_endpoints(env, granted)
    if not endpoints:
        return [], [], ""
    socks = []
    for item in os.environ.get("KIT_WORKER_LICENCE_SOCKS", "").split(","):
        port, _, path = item.partition("=")
        try:
            ok = (port.isdigit() and LICENCE_SOCK_RE.match(os.path.basename(path))
                  and stat.S_ISSOCK(os.stat(path).st_mode))
        except OSError:
            ok = False
        if not ok:
            return [], [], ""
        socks.append((int(port), path))
    if [p for p, _ in socks] != [p for _, p in endpoints]:
        return [], [], ""
    hosts = os.path.join(STATE, "licence", os.path.basename(rd) + ".hosts")
    os.makedirs(os.path.dirname(hosts), exist_ok=True)
    with open(hosts, "w") as f:
        f.write(envmod.hosts_text(endpoints))
    etc = ["--ro-bind", hosts, "/etc/hosts"] + (
        ["--ro-bind", "/etc/nsswitch.conf", "/etc/nsswitch.conf"] if os.path.exists("/etc/nsswitch.conf") else [])
    mounts = ["--ro-bind", os.path.join(ROOT, "harness", "egress-fwd"), "/opt/kit/bin/egress-fwd"]
    prefix, ready = "", []
    for i, (port, path) in enumerate(socks):
        mounts += ["--ro-bind", path, f"/opt/kit/licence/{i}.sock"]
        prefix += f"python3 /opt/kit/bin/egress-fwd {port} /opt/kit/licence/{i}.sock /tmp/.lic{i} & "
        ready.append(f"[ -e /tmp/.lic{i} ]")
    prefix += "for _ in $(seq 100); do " + " && ".join(ready) + " && break; sleep 0.1; done; "
    return etc, mounts, prefix


def bwrap_command(rd, cmd, net=False):
    envmod, env = kit_env()
    mod_args, mod_path, mod_env = envmod.sandbox_parts(env, worker_granted()) if envmod else ([], "", [])
    lic_etc, lic_mounts, lic_prefix = licence_parts(envmod, env, worker_granted(), rd, net)
    lim = run_limits(rd)
    n = str(lim["threads"])
    # Enforced, not promised (audit F9): RLIMIT_CPU per process = the run's whole CPU budget (a single
    # process may never exceed it; the tree cap is the cgroup quota bin/limits-exec sets), and every
    # BLAS/OpenMP thread pool is capped by environment so the worker need not remember to.
    cmd = f"{lic_prefix}ulimit -t {lim['cpu_seconds']}; {cmd}"
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
            "@PYETC@",
            "@NETETC@",
            "@LICETC@",
            "--remount-ro", "/etc",
            "--proc", "/proc",
            "--dev", "/dev",
            "--tmpfs", "/tmp",
            "--bind", rd, rd,
            "--ro-bind", LEDGER_SHIM, "/opt/kit/bin/ledger",
            "@MODMOUNTS@",
            "@NETHELPERS@",
            "@LICMOUNTS@",
            # LESSONS.md "The sandbox's root is remounted read-only after the binds": the root tmpfs read-only after every bind, so the
            # directories bwrap creates for mount points (the run dir's parent chain, /home, /opt/kit) are not
            # writable. Before this a write to ../x succeeded inside and reached nothing, silently. The run dir and
            # /tmp are mounts of their own and stay writable (remount is not recursive).
            "--remount-ro", "/",
            "--chdir", rd,
            "--unshare-all",
            "@SHARENET@",
            "--hostname", "sandbox",
            "--die-with-parent",
            "--clearenv",
            "--setenv", "HOME", rd,
            "--setenv", "TMPDIR", "/tmp",
            "--setenv", "PATH", "/opt/kit/bin:" + mod_path + "/usr/bin:/bin",
            "@MODENV@",
            "--setenv", "KIT_RUN", rd,
            "--setenv", "PYTHONDONTWRITEBYTECODE", "1",
            "--setenv", "OMP_NUM_THREADS", n,
            "--setenv", "OPENBLAS_NUM_THREADS", n,
            "--setenv", "MKL_NUM_THREADS", n,
            "--setenv", "NUMEXPR_NUM_THREADS", n,
            "--setenv", "KIT_THREADS", n,
            "--setenv", "KIT_CPU_HOURS", str(lim["cpu_hours"]),
            "--setenv", "KIT_MEM_GB", str(lim["mem_gb"]),
            "@NETENV@",
            "--", "/bin/bash", "-c", cmd]
    etc, helpers, env = net_bwrap_parts() if net else ([], [], [])
    fill = {"@NETETC@": etc, "@NETHELPERS@": helpers, "@SHARENET@": ["--share-net"] if net else [], "@NETENV@": env,
            "@MODMOUNTS@": mod_args, "@MODENV@": mod_env, "@LICETC@": lic_etc, "@LICMOUNTS@": lic_mounts,
            "@PYETC@": ["--ro-bind", PY_ETC, PY_ETC] if PY_ETC else []}
    out = []
    for a in args:
        out += fill.get(a, [a])
    return " ".join(shlex.quote(a) for a in out)


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


# ---------------------------------------------------------------------------------------------------
# User-approval gate (LESSONS.md "Every launch and every ledger append consumes a byte-bound", 2026-09-18). Orchestrator sessions only; the worker branch
# below is untouched. Approval is an act of the user (bin/approve, run with `!` or allowed by the
# user's tap on a prompt this hook words itself), bound to bytes; the tools refuse without it.
# What this branch does: keeps the orchestrator away from bin/approve and the approval records,
# denies a bare `claude -p`, SendMessage and Workflow (launch routes with no approval), and lets an
# Agent call to kit-worker through only by consuming a valid launch approval for its run.
APPROVE_WORD = re.compile(r"""(?:^|[\s;&|(){}`'"=/])approve(?=$|[\s;&|)`'"])""")
APPROVE_SIMPLE = re.compile(r"^\s*(?:\./|" + re.escape(ROOT) + r"/)?bin/approve(?:\s[^;&|$`<>\n\\(){}!]*)?$")
GIT_SIMPLE = re.compile(r"^\s*git\s+(?:add|diff|log|show|status|commit|restore|mv|rm)\b[^;&|$`<>\n\\(){}!]*$")
CLAUDE_PRINT = re.compile(r"(?:^|[\s;&|(/])claude\s+(?:[^;&|\n]*\s)?(?:-p|--print)(?=\s|$)")
# LESSONS.md "Networked and Codex launches need their flags bound": a Codex session started by the orchestrator is a launch outside the gate, like a bare
# `claude -p`; Codex workers start only inside bin/run-external --via codex, after the approval is consumed.
CODEX_RUN = re.compile(r"(?:^|[\s;&|(/])codex\s+(?:-\S+\s+(?:\S+\s+)?)*(?:exec|e|review|resume|fork|cloud|queue|app-server|exec-server)(?=\s|$)")
RUN_PATH = re.compile(re.escape(ROOT) + r"/workspace-[^/\s\"'`]+/runs/[^/\s\"'`,;:)]+")
# LESSONS.md "`LEDGER.log` is append-only": "agents write to the ledger, never read it" is enforced for the orchestrator too.
# LESSONS.md "No packet carries blocked material": what no packet may carry (data/packet-rules.json) and the exceptions to it
# (data/packet-exceptions.json) are the user's. The user adds to them with `! bin/packet-block …` and
# `! bin/packet-except …`; the orchestrator may not edit either list or run either tool, and may name the lists only in a
# plain git add / commit / status / diff.
PACKET_FILES = {os.path.join(ROOT, "data", "packet-rules.json"), os.path.join(ROOT, "data", "packet-exceptions.json")}
PACKET_WORD = re.compile(r"packet-(?:except|block|rules)")
# HANDOFF.md section 6 item 29, P-1 (kit-v0.5): the files that decide what a worker's sandbox mounts and reaches are the
# user's. An orchestrator could write .kit-lean naming any directory, which this hook then mounted read-only into every
# worker's sandbox and put on its PATH. Reading them is allowed; so is a plain git add / commit / status / diff.
ENV_FILES = {os.path.join(ROOT, n) for n in ("kit-env.json", ".kit-lean", ".kit-sage", ".kit-routes")}
ENV_WORD = re.compile(r"kit-env\.json|\.kit-(?:lean|sage|routes)\b")
ENV_READ_OK = re.compile(r"^\s*(?:cat|head|tail|less|jq|grep|wc|sha256sum|ls|stat|diff|file)\b[^;&|$`<>\n\\(){}!]*$")
LEDGER_GIT_OK = re.compile(r"^\s*git\s+(?:add|commit|status|diff\s+(?:--numstat|--stat))\b[^;&|$`<>\n\\(){}!]*$")
# P-12 H6 (the code audit of 2026-10-02): the pattern above fixes only how the command starts, and `git diff --stat -p`,
# `git status -v`, `git add -p` print contents. Every option must be one of these, which print none; anything else
# not starting with "-" is a path or a revision. `git commit` also takes -m/-F with their value.
PLAIN_GIT_OPTS = {"add": {"-A", "--all", "-u", "--update", "-f", "--force", "-n", "--dry-run", "-v", "--verbose"},
                  "commit": {"-q", "--quiet", "-s", "--signoff"},
                  "status": {"-s", "--short", "--porcelain", "-b", "--branch", "-uno", "--untracked-files=no"},
                  "diff": {"--stat", "--numstat", "--shortstat", "--cached", "--staged", "--name-only", "--name-status"}}
COMMIT_VALUE_OPTS = {"-m", "--message", "-F", "--file"}


CONTENT_GIT_OK = re.compile(r"^\s*git\s+(?:add|commit|status|diff)\b[^;&|$`<>\n\\(){}!]*$")


def ledger_git_ok(cmd, contents=False):
    """A plain git add, commit, status or `diff --stat` (or --numstat) that prints no file's contents. With contents=True
    (files the orchestrator may read: the packet lists, the environment files, the bindings and rulings; pending item
    P-10), a plain `git diff` of them too, its options from the same list."""
    m = re.match(r"""^\s*git\s+-C\s+(?:'([^']*)'|"([^"]*)"|(\S+))\s+(.*)$""", cmd, re.S)
    if m:   # P-14 (d): `git -C <this tree's root>` is the plain form run from the root; any other directory is not
        d = os.path.expanduser(m.group(1) or m.group(2) or m.group(3))
        if os.path.realpath(d if os.path.isabs(d) else os.path.join(ROOT, d)) != os.path.realpath(ROOT):
            return False
        cmd = "git " + m.group(4)
    if not (CONTENT_GIT_OK if contents else LEDGER_GIT_OK).match(cmd):
        return False
    try:
        argv = shlex.split(cmd)
    except ValueError:
        return False
    sub, rest, i = argv[1], argv[2:], 0
    while i < len(rest):
        x = rest[i]
        if x == "--":
            break
        if sub == "commit" and x in COMMIT_VALUE_OPTS:
            i += 2
            continue
        if sub == "commit" and (x.startswith(("--message=", "--file=")) or re.match(r"^-[mF].", x)):
            i += 1
            continue
        if x.startswith("-") and not (x in PLAIN_GIT_OPTS[sub] or (sub == "diff" and re.match(r"^--stat=\d+(,\d+)*$", x))):
            return False
        i += 1
    return True
# P-12 C3 (the code audit of 2026-10-02): the earned tag reads a referee's question and the bytes it was given from
# bin/new-run's binding, and a cross-family ruling from the user's list, never from a run directory. The orchestrator
# reads both and commits them (plain git add / commit / status / diff --stat); it writes neither.
BINDINGS_DIR = os.path.join(ROOT, "data", "referee-bindings")
RULINGS_FILE = os.path.join(ROOT, "data", "cross-family-rulings.json")
RECORD_WORD = re.compile(r"referee-bindings|cross-family-rulings")
ASK_MODES = {"default", "auto"}  # modes in which a hook `ask` is known to reach the user as a prompt (live-tested)
# LESSONS.md "An orchestrator types into no other pane and touches no mailbox" (user 2026-09-30, the kit's evaluation of
# Clatter, gap 2): the bus only through its dispatcher; no keys or buffers into a pane; nothing else under ~/.claude/clatter/.
# The send script itself is allowed for a threaded reply (`--reply-to`), but not its `--from` / `--from-session`, which set
# any sender (HANDOFF.md section 6 item 27 (a)); quotes and backslashes are dropped first, as the shell joins them away.
CLATTER_DIR = os.path.realpath(os.path.expanduser("~/.claude/clatter"))
CLATTER_PATH = re.compile(r"\.claude/clatter/(?!scripts/bus(?:-send)?\.sh\b)")
CLATTER_SEND = re.compile(r"bus-send")
CLATTER_FORGE = re.compile(r"--from")


def in_clatter(rp):
    return bool(rp) and (rp == CLATTER_DIR or rp.startswith(CLATTER_DIR + os.sep))
# Pending item P-4 (user 2026-10-01): beside the ledger, nothing the orchestrator reads by any route: the locked data and
# the approval records. Read, Grep and Glob inside them are refused, and a Grep rooted above any protected file (the tree
# root, typically) needs a glob or type filter that matches none of them; a command naming data/locked is refused but a
# plain `bin/new-run … --role evaluator` (the one tool that copies from it, into an evaluator run) and plain git.
# Since kit-v0.6.9 (pending item P-9) the locked directory lies outside the tree, where kit-env.json's `locked_dir` says
# (read from the file, never from an environment variable); an instance without the field keeps <root>/data/locked.
_KENV = kit_env()[1]
LOCKED_DIR = os.path.realpath(_KENV.locked_dir) if _KENV else os.path.join(ROOT, "data", "locked")
APPROVALS_DIR = os.path.join(ROOT, ".claude", "state", "approvals")
_HOME = os.path.realpath(os.path.expanduser("~"))
# P-12 (a medium of the code audit): an unreadable kit-env.json, or a refused locked_dir, leaves LOCKED_DIR at
# <root>/data/locked while the keys may lie at the default place (bin/_env.py default_locked_dir, kept in step here):
# every place the locked data can be is guarded.
LOCKED_DIRS = sorted({LOCKED_DIR, os.path.join(ROOT, "data", "locked"),
                      os.path.join(_HOME, ".local", "state", "crosslemma", os.path.basename(ROOT), "locked")})
_LOCKED_RELS = [d[len(_HOME) + 1:] for d in LOCKED_DIRS if d.startswith(_HOME + os.sep)]
LOCKED_WORD = re.compile("|".join([r"data/locked\b"] + [re.escape(d) for d in LOCKED_DIRS]
                                  + [p + re.escape(r) for r in _LOCKED_RELS for p in (r"~/", r"\$HOME/", r"\$\{HOME\}/")]))
NEW_RUN_EVALUATOR = re.compile(r"^\s*(?:\./|" + re.escape(ROOT) + r"/)?bin/new-run\s[^;&|$`<>\n\\(){}!]*--role[ =]evaluator\b"
                               r"[^;&|$`<>\n\\(){}!]*$")
GREP_TYPE_GLOBS = {"py": ["*.py", "*.pyi"], "md": ["*.md", "*.markdown", "*.mdown", "*.mdwn", "*.mkd", "*.mkdn", "*.mdx"],
                   "markdown": ["*.md", "*.markdown", "*.mdown", "*.mdwn", "*.mkd", "*.mkdn", "*.mdx"],
                   "sh": ["*.sh", "*.bash", "*.zsh"], "lean": ["*.lean"], "tex": ["*.tex", "*.ltx", "*.sty", "*.cls"],
                   "toml": ["*.toml"], "yaml": ["*.yaml", "*.yml"], "c": ["*.c", "*.h"], "rust": ["*.rs"]}


def under(rp, d):
    d = os.path.realpath(d)
    return rp == d or rp.startswith(d + os.sep)


def protected_files():
    """The files no orchestrator search may reach: the ledger, every locked file, every approval record (their names only
    are listed here; this hook never opens them)."""
    out = [os.path.realpath(LEDGER)]
    for d in LOCKED_DIRS + [APPROVALS_DIR]:
        for dp, _, fn in os.walk(d):
            out += [os.path.realpath(os.path.join(dp, f)) for f in fn]
    return out


def expand_braces(g):
    m = re.search(r"\{([^{}]*)\}", g)
    if not m:
        return [g]
    return [x for alt in m.group(1).split(",") for x in expand_braces(g[:m.start()] + alt + g[m.end():])]


def search_filter_safe(ti, root_rp, reached):
    """A Grep's glob/type filter that matches none of the protected files it would reach. No filter, a negated glob, or a
    type this hook cannot map to file patterns is not safe."""
    globs = expand_braces(str(ti["glob"])) if ti.get("glob") else []
    if ti.get("type"):
        t = GREP_TYPE_GLOBS.get(str(ti["type"]))
        if t is None:
            return False
        globs += t
    if not globs or any(g.startswith("!") for g in globs):
        return False
    globs += [g.replace("**/", "") for g in globs if "**/" in g]   # `**/` matches no directory too
    for f in reached:
        rel, base = os.path.relpath(f, root_rp), os.path.basename(f)
        if any(fnmatch.fnmatch(base, g) or fnmatch.fnmatch(rel, g) or fnmatch.fnmatch(rel, "*/" + g) for g in globs):
            return False
    return True
# Pending item P-13, route (a) (user 2026-10-02 21:34: "cheap route"): the ledger and the locked data are guarded by name, and
# a git command that names neither printed them (`git show HEAD`, `git log -p`, a bare `git diff`: the ledger always has
# uncommitted lines). In this tree, a git command that prints file contents must name its paths, none of them protected
# nor a directory holding one; git on another repository (`git -C <kit> show tag:path`) is not this tree's. What a
# program reads beyond git stays out of the hook's sight: the rule against reading the ledger holds by name otherwise.
GIT_QUIET = {"status", "add", "commit", "rm", "mv", "restore", "checkout", "switch", "branch", "tag", "rev-parse",
             "describe", "ls-files", "ls-tree", "remote", "fetch", "push", "pull", "merge", "rebase", "reset", "init",
             "clone", "worktree", "clean", "gc", "fsck", "count-objects", "rev-list", "ls-remote", "cherry-pick", "revert",
             "show-ref", "symbolic-ref", "check-ignore", "var", "help", "version", "config", "shortlog", "bisect",
             "notes", "submodule", "am", "apply", "merge-base", "name-rev", "for-each-ref", "check-attr", "mergetool"}
GIT_NEVER = {"cat-file", "archive", "format-patch", "whatchanged", "difftool", "fast-export", "bundle", "range-diff"}
GIT_NAMED = {"grep", "blame", "annotate"}                  # print contents; allowed with named, unprotected paths
GIT_SUMMARY = {"--stat", "--numstat", "--shortstat", "--name-only", "--name-status", "--no-patch", "-s", "--summary",
               "--compact-summary", "--dirstat", "--raw"}
GIT_PATCH = re.compile(r"^(?:-p|-u|--patch(?:-with-stat|-with-raw)?|-U\d*|--unified(?:=.*)?|--word-diff(?:=.*)?|"
                       r"--color-words(?:=.*)?|-L.*|--cc|-c|-m|--full-diff|--ext-diff|--textconv|--binary|--output(?:=.*)?)$")
GIT_SAFE_CONFIG = {"user.name", "user.email", "color.ui", "core.quotepath", "commit.gpgsign", "advice.detachedhead"}
SHELLS = {"sh", "bash", "dash", "zsh"}
WRAPPERS = {"env", "sudo", "nice", "nohup", "time", "command", "exec", "stdbuf", "timeout", "xargs", "ionice"}


def _git_path_protected(p, base):
    """A pathspec that is protected, holds a protected file, or cannot be read as a plain path (a glob, a magic form)."""
    if not p or any(ch in p for ch in "*?[") or p.startswith(":"):
        return True
    rp = os.path.realpath(p if os.path.isabs(p) else os.path.join(base, p))
    for f in protected_files() + LOCKED_DIRS + [APPROVALS_DIR]:
        f = os.path.realpath(f)
        if rp == f or f.startswith(rp.rstrip(os.sep) + os.sep) or rp.startswith(f + os.sep):
            return True
    return False


def _git_problem(argv, cwd):
    """Why one git invocation (its argv after `git`) would print a protected file's contents, or None."""
    repo, i = cwd, 0
    while i < len(argv) and argv[i].startswith("-"):
        o = argv[i]
        if o == "-C" and i + 1 < len(argv):
            repo = os.path.join(repo, os.path.expanduser(argv[i + 1])); i += 2; continue
        if o == "-c" and i + 1 < len(argv):
            if argv[i + 1].split("=", 1)[0].lower() not in GIT_SAFE_CONFIG:
                return f"`git -c {argv[i + 1]}` sets what git runs or prints; not here"
            i += 2; continue
        if o.startswith(("--git-dir=", "--work-tree=")):
            repo = os.path.join(repo, o.split("=", 1)[1]); i += 1; continue
        i += 1
    if not inside_root(os.path.realpath(repo)):
        return None   # another repository
    if i >= len(argv):
        return None
    sub, rest = argv[i], argv[i + 1:]
    if sub == "stash":
        if rest[:1] != ["show"]:
            return None
        sub, rest = "stash show", rest[1:]
    if sub in GIT_QUIET:
        return None
    if sub in GIT_NEVER:
        return f"`git {sub}` prints the repository's contents whole; not in this tree"
    if sub not in GIT_NAMED | {"diff", "show", "log", "reflog", "stash show"}:
        return f"`git {sub}` is not a git command this hook knows (an alias?); not in this tree"
    base = os.path.realpath(cwd)
    opts = [x for x in rest if x.startswith("-") and x != "--"]
    dd = rest.index("--") if "--" in rest else None
    paths = rest[dd + 1:] if dd is not None else []
    args = [x for x in (rest[:dd] if dd is not None else rest) if not x.startswith("-")]
    if sub == "log" or sub == "reflog":
        if not any(GIT_PATCH.match(o) for o in opts):
            return None
    elif sub == "stash show":
        if not any(GIT_PATCH.match(o) for o in opts):
            return None
    elif sub in ("diff", "show"):
        if any(o.split("=", 1)[0] in GIT_SUMMARY for o in opts) and not any(GIT_PATCH.match(o) for o in opts):
            return None
        if sub == "show":
            for x in args:
                if ":" in x:
                    path = x.split(":", 1)[1]
                    if _git_path_protected(path[2:] if path.startswith("./") else path,
                                           base if path.startswith("./") else os.path.realpath(repo)):
                        return f"`git show {x}` reads a protected file"
                    paths.append(path if not path.startswith("./") else path[2:])
        else:
            paths += [x for x in args if os.path.exists(os.path.join(base, x))]
    elif sub == "blame" or sub == "annotate":
        paths += args[-1:]
    elif sub == "grep":
        pass   # its paths only after `--`
    if not paths:
        return (f"`git {sub}` here prints file contents with no path named, which would include the ledger (it always has "
                "uncommitted lines) or the locked data; name the paths after `--` (git diff -- HANDOFF.md bin/), or use "
                "--stat / --name-only")
    bad = [x for x in paths if _git_path_protected(x, base)]
    if bad:
        return (f"`git {sub}` names {', '.join(bad)}: the ledger, the locked data or an approval record, a directory "
                "holding one, or a pattern; name plain paths that hold none of them")
    return None


def git_contents_problem(cmd, cwd, depth=0):
    """The first reason a git invocation in `cmd` would print a protected file's contents, or None."""
    if depth > 3:
        return "nested too deep to read"
    try:
        lx = shlex.shlex(cmd, posix=True, punctuation_chars=True)
        lx.whitespace_split = True
        toks = list(lx)
    except ValueError:
        return "the command does not parse" if re.search(r"\bgit\b", cmd) else None
    segs, cur = [], []
    for t in toks:
        if t and all(ch in "();&|<>" for ch in t):
            segs.append(cur); cur = []
        else:
            cur.append(t)
    segs.append(cur)
    for seg in segs:
        j = 0
        while j < len(seg) and (re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", seg[j]) or os.path.basename(seg[j]) in WRAPPERS
                                or (j > 0 and (seg[j].startswith("-") or seg[j].replace(".", "").isdigit()))):
            j += 1
        if j < len(seg) and os.path.basename(seg[j]) == "git":
            why = _git_problem(seg[j + 1:], cwd)
            if why:
                return why
        if j < len(seg) and os.path.basename(seg[j]) in SHELLS and "-c" in seg[j + 1:]:
            k = seg.index("-c", j + 1)
            if k + 1 < len(seg):
                why = git_contents_problem(seg[k + 1], cwd, depth + 1)
                if why:
                    return why
        if j < len(seg) and seg[j] == "eval":
            why = git_contents_problem(" ".join(seg[j + 1:]), cwd, depth + 1)
            if why:
                return why
    return None


CLATTER_BUS = re.compile(r"\.claude/clatter/scripts/bus\.sh['\"]?\s+([A-Za-z-]+)")
CLATTER_BUS_OK = {"peers", "ask", "send", "broadcast", "recv", "status", "doctor"}
TMUX_KEYS = re.compile(r"\btmux\b[^\n]*?\s(?:send-keys|send|paste-buffer|pasteb|load-buffer|loadb|set-buffer|setb)\b")
DENIED_ORCH_TOOLS = {"SendMessage": "continuing a finished worker is a launch with no approval",
                     "Workflow": "a workflow can spawn workers with no approval"}
SETTINGS_FILES = [os.path.join(ROOT, ".claude", "settings.json"), os.path.join(ROOT, ".claude", "settings.local.json"),
                  os.path.expanduser("~/.claude/settings.json"), os.path.expanduser("~/.claude/settings.local.json")]


def approval_lib():
    import importlib.util
    spec = importlib.util.spec_from_file_location("_approval", os.path.join(ROOT, "bin", "_approval.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def gate_deny(why):
    try:
        ledger("orchestrator", None, "DENY-GATE", why)
    except Exception:   # P-12: an unwritable ledger never turns a refusal into a crash; the refusal stands
        pass
    deny("User-approval gate (LESSONS.md 'Every launch and every ledger append consumes a byte-bound'): " + why)


def allow_rule_covers_approve():
    """An allow rule that would let bin/approve through without a prompt (e.g. written by a "don't ask
    again" tap). Returns the rule, or None."""
    import fnmatch
    probes = ("bin/approve RUN --digest 0123456789ab", ROOT + "/bin/approve RUN --digest 0123456789ab")
    for sf in SETTINGS_FILES:
        try:
            with open(sf) as f:
                rules = (json.load(f).get("permissions") or {}).get("allow") or []
        except FileNotFoundError:
            continue
        except Exception:
            return f"{sf} (unreadable)"
        for r in rules:
            if not isinstance(r, str) or not r.startswith("Bash"):
                continue
            pat = r[5:-1].replace(":*", "*") if r.startswith("Bash(") and r.endswith(")") else "*"
            if "approve" in r or any(fnmatch.fnmatch(p, pat) for p in probes):
                return f"{r} in {sf}"
    return None


def ask_user_to_approve(inp, cmd):
    """The orchestrator's Bash call is exactly `bin/approve …`: the user's tap on the prompt is the
    approval. The prompt text is computed here, from the bytes, not taken from the orchestrator."""
    if inp.get("permission_mode") not in ASK_MODES:
        gate_deny(f"bin/approve can be offered for the user's tap only in permission mode {sorted(ASK_MODES)} "
                  f"(now {inp.get('permission_mode')!r}). The user runs it with `!`, or switches mode.")
    rule = allow_rule_covers_approve()
    if rule:
        gate_deny(f"an allow rule would let bin/approve through without the user's tap: {rule}. Remove it first.")
    if not cmd.lstrip().startswith(ROOT) and os.path.realpath(inp.get("cwd") or "") != ROOT:
        gate_deny("run bin/approve from the project root.")
    try:
        args = shlex.split(cmd)[1:]
    except ValueError as e:
        gate_deny(f"bin/approve arguments do not parse: {e}")
    head = args[:args.index("--")] if "--" in args else args
    if "--session" not in head and not any(x == "--digest" or x.startswith("--digest=") for x in head):
        if True:
            gate_deny("an orchestrator call to bin/approve must carry --digest <12 hex> from a bin/manifest "
                      "printout the user has seen (several targets: one digest per target, comma-separated, in order).")
    A = approval_lib()
    try:
        a, jobs = A.plan(args, ROOT)
    except A.Refused as e:
        gate_deny(f"bin/approve would refuse: {e}")
    parts = []
    for kind, key, ids, man, av, _ in jobs:
        parts.append(f"{kind} {key}" + (f" ids {','.join(ids)}" if ids else "") + f", digest {A.digest(kind, key, ids, man)[:12]}, "
                     f"{len(man)} entries" + (f", flags {' '.join(A.norm_argv(av))}" if av is not None else ", flags not bound"))
    text = "USER APPROVAL (single use, 30 min): " + " | ".join(parts) + ". Allow = you approve exactly these bytes. Never choose \"don't ask again\"."
    ledger("orchestrator", None, "ASK-APPROVE", text)
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "ask",
                                             "permissionDecisionReason": text}}))
    sys.exit(0)


def gate_orchestrator(inp, tool, ti):
    """Returns normally when the call is none of the gate's business."""
    if tool in DENIED_ORCH_TOOLS:
        gate_deny(f"{tool} is not available to the orchestrator here: {DENIED_ORCH_TOOLS[tool]}.")
    if tool != "Bash" and isinstance(ti.get("command"), str):
        # P-12 C1 (the code audit of 2026-10-02): Monitor, or any other tool that runs a shell command, is gated as Bash
        # is; the tap on bin/approve is offered for one plain Bash call only.
        if APPROVE_WORD.search(ti["command"]):
            gate_deny(f"{tool} runs a shell command, and a command naming bin/approve is offered for the user's tap from "
                      "Bash only, as one plain `bin/approve RUN --digest <12 hex> [-- flags]` call.")
        tool = "Bash"
    appr = APPROVALS_DIR
    if tool in ("Read", "Grep", "Glob"):
        p = os.path.expanduser(ti.get("file_path") or ti.get("path") or "")
        rp = os.path.realpath(p if os.path.isabs(p) else os.path.join(inp.get("cwd") or ROOT, p)) if p else ""
        if tool in ("Grep", "Glob") and not rp:   # with no path, the session's cwd is searched
            rp = os.path.realpath(inp.get("cwd") or ROOT)
        if rp and rp == os.path.realpath(LEDGER):
            gate_deny("LEDGER.log is written by agents and never read by them; the user reads it.")
        if rp and (any(under(rp, d) for d in LOCKED_DIRS) or under(rp, APPROVALS_DIR)):
            gate_deny("data/locked/ (answer keys, label maps) and the approval records are never read by the orchestrator "
                      "(RULES.md §4, the never-read list; §9). An evaluator run receives locked files through bin/new-run.")
        if tool in ("Grep", "Glob") and rp:   # P-12: a Glob rooted above them too, its pattern the filter
            reached = [f for f in protected_files() if f.startswith(rp.rstrip(os.sep) + os.sep)]
            if reached and not search_filter_safe(ti if tool == "Grep" else {"glob": ti.get("pattern")}, rp, reached):
                gate_deny("this Grep would read the ledger, the locked data or an approval record: search a subdirectory "
                          "(bin/, workspace-N/, problems/ …), or add a glob (or a type: py, md, sh, lean, tex …) that "
                          "matches none of them.")
        # The source's method change 69 (kit-v0.4.19): "any touch" includes reading another session's mailbox or the
        # relay's log; a Grep or Glob rooted above ~/.claude/clatter/ would walk into it, so that is refused too.
        if rp and (in_clatter(rp) or (tool in ("Grep", "Glob") and CLATTER_DIR.startswith(rp.rstrip(os.sep) + os.sep))):
            gate_deny("nothing under ~/.claude/clatter/ is read but through Clatter's dispatcher "
                      "(`bash ~/.claude/clatter/scripts/bus.sh recv`), and no Grep or Glob is rooted above it.")
        return
    if tool in ("Write", "Edit", "MultiEdit", "NotebookEdit"):
        p = os.path.expanduser(ti.get("file_path") or ti.get("notebook_path") or "")
        rp = os.path.realpath(p if os.path.isabs(p) else os.path.join(inp.get("cwd") or ROOT, p)) if p else ""
        if rp == appr or rp.startswith(appr + os.sep):
            gate_deny("approval records are written by bin/approve, which only the user runs.")
        if rp == os.path.realpath(LEDGER):   # P-12: appended by the hook and the tools only, never rewritten
            gate_deny("LEDGER.log is append-only and written by the hook and the tools; an entry goes in through bin/ledger.")
        if in_clatter(rp):
            gate_deny("nothing under ~/.claude/clatter/ is written by the orchestrator: a message goes through the bus's "
                      "dispatcher (`bash ~/.claude/clatter/scripts/bus.sh send …`), which writes the mailbox itself.")
        if rp in {os.path.realpath(f) for f in ENV_FILES}:
            gate_deny("the environment files (kit-env.json, .kit-lean, .kit-sage, .kit-routes) decide what a worker's sandbox "
                      "mounts and reaches; they are the user's, who edits them by hand. Reading them is allowed.")
        if rp in {os.path.realpath(f) for f in PACKET_FILES}:
            gate_deny("the packet rules and their exceptions are the user's: `! bin/packet-block PATH \"why\"` and "
                      "`! bin/packet-except FILE \"ruling\"`.")
        if rp and (under(rp, BINDINGS_DIR) or rp == os.path.realpath(RULINGS_FILE)):
            gate_deny("a referee binding is bin/new-run's record and a cross-family ruling is the user's (data/referee-bindings/, "
                      "data/cross-family-rulings.json); the orchestrator reads and commits them, never writes them.")
        return
    if tool == "Bash":
        cmd = ti.get("command", "")
        if "LEDGER.log" in cmd and not ledger_git_ok(cmd):
            gate_deny("LEDGER.log is written by agents and never read by them. Allowed: a plain git add / commit / "
                      "status / `git diff --numstat` that names it; entries go in through bin/ledger.")
        if "state/approvals" in cmd:
            gate_deny("commands that name the approvals directory are the user's.")
        if LOCKED_WORD.search(cmd) and not (ledger_git_ok(cmd) or NEW_RUN_EVALUATOR.match(cmd)):
            gate_deny("the locked directory (data/locked/, or kit-env.json's locked_dir) is never read by the orchestrator: "
                      "a command naming it may only be a plain "
                      "`bin/new-run … --role evaluator` (which copies locked files into an evaluator run) or a plain git "
                      "add / commit / status / diff --stat.")
        if ENV_WORD.search(cmd) and not (ledger_git_ok(cmd, contents=True) or ENV_READ_OK.match(cmd)):
            gate_deny("the environment files (kit-env.json, .kit-lean, .kit-sage, .kit-routes) are the user's: a command "
                      "naming them may only read them (one plain cat, head, jq, grep …) or be a plain git add / commit / "
                      "status / diff.")
        if PACKET_WORD.search(cmd) and not ledger_git_ok(cmd, contents=True):
            gate_deny("the packet rules, their exceptions, bin/packet-block and bin/packet-except are the user's: the "
                      "user runs `! bin/packet-block …` or `! bin/packet-except …`. Allowed here: a plain git add / commit / "
                      "status / diff of the lists.")
        why = git_contents_problem(cmd, inp.get("cwd") or ROOT) if re.search(r"\bgit\b", cmd) else None
        if why:
            gate_deny("git here may not print the ledger or the locked data (P-13): " + why + ".")
        if RECORD_WORD.search(cmd) and not (ledger_git_ok(cmd, contents=True) or ENV_READ_OK.match(cmd)):
            gate_deny("the referee bindings (bin/new-run's) and the cross-family rulings (the user's) are never written by the "
                      "orchestrator: a command naming them may only read them (one plain cat, head, jq, ls …) or be a plain "
                      "git add / commit / status / diff --stat.")
        if TMUX_KEYS.search(cmd):
            gate_deny("no keys or buffers into a tmux pane: another pane may hold a pending prompt, the user's input line "
                      "or another session. Peers are reached through Clatter's dispatcher (bus.sh send/ask).")
        m = CLATTER_BUS.search(cmd)
        if m and m.group(1) not in CLATTER_BUS_OK:
            gate_deny(f"Clatter's `{m.group(1)}` changes how the relay treats a session; it is the user's. The orchestrator "
                      f"uses the dispatcher's {', '.join(sorted(CLATTER_BUS_OK))}.")
        if CLATTER_SEND.search(cmd) and CLATTER_FORGE.search(re.sub(r"[\"'\\]", "", cmd)):
            gate_deny("Clatter's bus-send.sh `--from` and `--from-session` set the sender a peer sees; a message goes out "
                      "as this session. A body that must hold that text goes in a file, sent as \"$(cat FILE)\".")
        if CLATTER_PATH.search(cmd):
            gate_deny("nothing under ~/.claude/clatter/ is touched but through Clatter's dispatcher "
                      "(`bash ~/.claude/clatter/scripts/bus.sh …`): no mailbox, registry, relay or mode file.")
        if CLAUDE_PRINT.search(cmd):
            gate_deny("a bare `claude -p` is a launch outside the gate; the user runs it with `!` if it is wanted.")
        if CODEX_RUN.search(cmd):
            gate_deny("a bare `codex exec` (or review, resume, fork, cloud) is a launch outside the gate; Codex workers start "
                      "through bin/run-external --via codex after a user approval.")
        if APPROVE_WORD.search(cmd):
            if APPROVE_SIMPLE.match(cmd):
                ask_user_to_approve(inp, cmd)
            if GIT_SIMPLE.match(cmd):
                return
            gate_deny("bin/approve is the user's act. Offer it for the user's tap as one plain command, "
                      "`bin/approve RUN --digest <12 hex> [-- flags]`, after showing bin/manifest's printout; "
                      "anything else that names it is refused (for a commit message, use `git commit -F <file>`).")
        return
    if tool == "Agent" and str(ti.get("subagent_type") or "").startswith(WORKER_TYPE):
        gate_deny(f"workers are not launched as subagents (LESSONS.md 'Every worker is a headless main process'): a subagent inherits this session's harness "
                  f"text. Launch it headless: bin/run-external RUN --via anthropic --model M --effort E, after the user's "
                  f"approval of those flags. No approval is consumed by this refusal.")


def gate_relevant(tool, ti):
    cmd = ti.get("command") if isinstance(ti.get("command"), str) else None   # Bash, Monitor: any tool running a command (P-12 C1)
    return (tool in DENIED_ORCH_TOOLS or tool in ("Read", "Grep", "Glob", "Write", "Edit", "MultiEdit", "NotebookEdit", "Agent")
            or (cmd is not None and LOCKED_WORD.search(cmd))
            or (cmd is not None and any(w in cmd for w in ("approv", "claude", "codex", "LEDGER.log",
                                                           "packet-", "tmux", "clatter", "bus-send",
                                                           "kit-env", ".kit-", "locked", "referee-bindings",
                                                           "cross-family-rulings", "git"))))


def main():
    raw = sys.stdin.read()
    try:
        inp = json.loads(raw)
    except Exception:   # P-11 (d): no input it can read, no decision it can make: refused, not let through
        print("sandbox hook: the hook input is not JSON; the call is refused", file=sys.stderr)
        sys.exit(2)
    event = inp.get("hook_event_name", "")
    global FOREIGN
    FOREIGN = foreign_session(inp)
    os.makedirs(STATE, exist_ok=True)
    if os.environ.get("KIT_HOOK_DEBUG") or os.path.exists(os.path.join(STATE, "debug-on")):
        with open(DEBUG, "a") as f:
            f.write(json.dumps({k: v for k, v in inp.items() if k != "tool_response"})[:2000] + "\n")

    if event in ("SubagentStart", "SubagentStop"):
        key = agent_key(inp)
        drain_outbox(key, get_binding(key))
        extra = ""
        if event == "SubagentStop" and inp.get("agent_type") in WORKER_TYPES:
            tp = inp.get("agent_transcript_path")
            if not tp and inp.get("transcript_path") and inp.get("agent_id"):   # layout seen 2026-09-22 (canary 102)
                main = inp["transcript_path"]
                tp = os.path.join(main[:-len(".jsonl")] if main.endswith(".jsonl") else main,
                                  "subagents", f"agent-{inp['agent_id']}.jsonl")
            seen = effort_seen(tp) if tp else None
            extra = f" effort_seen={seen if seen is not None else 'no-transcript'}"
        ledger(key, get_binding(key) and os.path.basename(get_binding(key)),
               event.replace("Subagent", "").upper(),
               f"type={inp.get('agent_type','?')}{extra}")
        sys.exit(0)

    ext_run = os.environ.get("KIT_WORKER_RUN")
    if ext_run and not is_subagent(inp):
        # LESSONS.md "Every worker is a headless main process": a headless worker is a `claude -p` MAIN process launched by bin/run-external
        # with KIT_WORKER_RUN=<run dir>. Treat it exactly like a kit-worker subagent, pre-bound to
        # that run. User-approved 2026-09-16 09:44 MST.
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
            global UNRECORDED
            try:
                ledger("orchestrator", None, "CALL", f"{t0} {d}")
            except Exception as e:
                # P-12 (a low finding): this used to raise into the catch-all and refuse every call, the ones that would
                # show and fix the problem included. As a failing gate does (RULES.md §9), gated calls are refused and
                # the rest go on, the user told that they are not recorded.
                UNRECORDED = e
                if t0 == "Agent" or APPROVE_WORD.search(str(ti0.get("command") or "")):   # what needs its record
                    gate_deny(f"LEDGER.log could not be written ({e!r}); a gated call is not made unrecorded")
            if touches_handoff(t0, ti0) and FOREIGN is None:   # a foreign session's HANDOFF.md is its own
                # LESSONS.md "`HANDOFF.md` is archived before it is touched" (user direction 2026-09-16 20:55): every rewrite of HANDOFF.md keeps the
                # previous version. Archive once per session, before the first call that touches it.
                archive_handoff_once(inp)
            if gate_relevant(t0, ti0):
                try:
                    gate_orchestrator(inp, t0, ti0)
                except SystemExit:
                    raise
                except Exception as e:  # a broken gate refuses gated calls; it never opens them and never blocks the rest
                    gate_deny(f"gate error, call refused: {e!r}")
            if t0 == "Agent":
                # Worker launches must not carry `name` (replaces agent_type in hook input, run 003)
                # or `isolation` (a git worktree guard then refuses the bwrap-rewritten Bash, run 024).
                # Strip them rather than trust the launching model to omit them. User-approved 08:04 MST.
                bad = {k: ti0[k] for k in ("name", "isolation", "team_name") if ti0.get(k)}
                if bad:
                    if UNRECORDED is None:
                        ledger("orchestrator", None, "REWRITE", f"Agent: stripped {bad}")
                    allow({k: v for k, v in ti0.items() if k not in bad})
            if UNRECORDED is not None:
                print(json.dumps(unrecorded_note()))
        sys.exit(0)

    key = agent_key(inp)
    drain_outbox(key, get_binding(key))
    if event == "PreToolUse" and inp.get("agent_type") not in WORKER_TYPES:
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

    net = net_worker()
    if tool not in ALLOWED_TOOLS and not (net and tool in NET_TOOLS):
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
        out = dict(ti, command=bwrap_command(bound, cmd, net=net))
        if "run_in_background" in out:   # P-12 C2: nothing of the worker outlives its call to race a Read or Write check
            out["run_in_background"] = False
        allow(out)

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
