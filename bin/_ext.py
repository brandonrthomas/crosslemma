#!/usr/bin/python3
"""External routes of bin/run-external (LESSONS.md "Networked and Codex launches need their flags bound", 2026-09-22): the Codex worker, networked workers, and
the record every external run leaves. Called by bin/run-external only; never launches anything by itself when
run with --dry-run. Stdlib only.

  _ext.py gateway STATE_DIR PORTFILE
        Key-holding search gateway on 127.0.0.1 (outside every sandbox). Routes /TOKEN/brave, /TOKEN/exa,
        /TOKEN/exa-contents, /TOKEN/status. Keys from ROOT/.env.brave and ROOT/.env.exa (a bare key or NAME=key;
        override with BRAVE_KEYFILE / EXA_KEYFILE); a missing key is reported, never fatal. Writes the URL
        (with its token) to PORTFILE when ready; logs every request, never a key, to STATE_DIR/gateway.log.

  _ext.py codex RUN_DIR --model M --effort E --wall-hours H [--max-turns N] [--network] [--module NAME ...]
                [--prompt TEXT] [--dry-run]
        Runs `codex exec` as a worker. The WHOLE codex process runs inside bwrap: the run directory read-write,
        /usr, the system Python's /etc, the codex binary, kit-env.json's modules and worker_path read-only (bin/_env.py),
        the user's home otherwise invisible, a clean environment, the root remounted read-only after the binds.
        Each command the model runs goes through .claude/sandbox/kit-shell, in a sandbox of its own (its own
        processes; Codex's home, with the token and the session log, hidden; no network on a run without it;
        LESSONS.md "A Codex worker's commands run apart from Codex"). With --module, a granted licence module's
        mounts and its relays (one socket per licence server, RUN_DIR/licence.log) are added.
        CODEX_HOME is a private tmpfs holding one file, a copy of ~/.codex/auth.json (the user's ruling
        2026-09-22: the token copy lives inside the sandbox for the run). 20 Codex features and the bundled
        skills are off (the source's canaries); Codex's own sandbox is bypassed because bwrap is the sandbox.
        Without --network the sandbox has its own network namespace: the only way out is the egress proxy, whose
        socket lives in a short directory private to this user (only the socket file is bound in), and which passes
        CONNECT requests to the model provider's exact hosts only; web search is disabled.
        With --network the host network is shared, live web search is on, and the search gateway is started.
        The prompt is RUN_DIR/HARNESS-NOTE.md, a blank line, then the task. Wall-clock cap: --wall-hours (exit
        124); tool-call cap: --max-turns, counted from the transcript as it arrives (exit 125). Codex reads a copy
        of the binary's model catalog with multi_agent_version removed (no sub-agents). Logs: STATE/logs/launch.jsonl
        (events, reaching the host through a pipe and recorded with a running sha256 chain) and launch.err, outside
        the sandbox (bin/run-external moves them into RUN_DIR at exit);
        RUN_DIR/launch.last.md (Codex's last message, written from inside); the main thread's session file as
        RUN_DIR/launch.rollout.jsonl, any other (a sub-agent's) as launch.rollout.sub-N.jsonl.

  _ext.py codex-probe RUN_DIR MODEL EFFORT [--network]
        Before the approval (bin/run-external's preflight): Codex renders this launch's prompt and feature list on
        the host, offline, with the launch's own settings; exit 1 and the reasons if either still offers sub-agents
        or a disabled feature is on.

  _ext.py models RUN_DIR MODEL
        One line for EXIT-EXT: the models that answered, "yes"/"no" for a fallback or a mixed run, and why.

  _ext.py effort RUN_DIR VIA · planlimit RUN_DIR · capacity RUN_DIR
        One value each for EXIT-EXT: the effort the requests carried; whether the plan's usage limit was hit (and
        when to try again); whether the provider refused at capacity.

  _ext.py hook-registered SETTINGS|- HOOK_COMMAND
        Exit 0 when the settings run that hook command on PreToolUse for every tool and on PostToolUse (P-11 (g)).

  _ext.py upstream-limited LAUNCH_LOG LAUNCH_ERR
        Exit 0 when a Claude-route launch ended on an upstream rate limit (bin/run-external retries it), judged from the
        CLI's own words only, never a tool result or the model's text (P-12 H4).

  _ext.py cli claude|codex · module-check NAME ... · licence-relay RUN_DIR SOCKFILE NAME ...
        The CLI kit-env.json names; the --module names checked against the environment file before the approval
        (unknown, not a licence module, a shared port: exit 2 and the problems; bin/run-external compares them with
        RUN_DIR/.modules itself); one licence relay, run until killed, logging opens and closes with
        byte counts, never contents (LESSONS.md "A worker's tools come from the user's environment file").

  _ext.py queue-stop RUN
        For bin/run-external's queue, after each run: exit 0 and the reason when the run ended on the plan's usage limit or
        the provider's capacity refusal (the queue then releases nothing more); exit 1 otherwise.

  _ext.py record RUN_DIR --via V --model M [--network] [--exit N]
        After any external run: copies the gateway and egress logs into RUN_DIR, hashes the transcript, the logs
        and everything under RUN_DIR/downloads/, summarises the transcript, and writes RUN_DIR/RECORD-EXT.md with
        the disclosure (what the model could read, what network it had, token exposure). One ledger line.
        For Codex it also moves RUN_DIR/.ledger-outbox into the ledger (the hook does that for Claude workers).
"""
import glob
import hashlib
import http.server
import json
import os
import re
import secrets
import shutil
import signal
import socket
import stat
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _lib as L
import _env as E

ROOT = L.ROOT
REAL_ROOT = L.REAL_ROOT
HARNESS = os.path.join(REAL_ROOT, "harness")
LEDGER_SHIM = os.path.join(REAL_ROOT, ".claude", "sandbox", "ledger")


def module_parts(granted=()):
    """(bwrap args, PATH prefix, env args) of the modules a worker gets, from the instance's environment file, the same
    as the hook gives a Claude worker (bin/_env.py; LESSONS.md "The environment files are the user's")."""
    return E.sandbox_parts(E.load(ROOT), granted)


def run_modules(rd):
    """The licence modules a run was launched with: RUN/.modules, which bin/run-external made the launch match."""
    try:
        with open(os.path.join(rd, ".modules")) as f:
            return tuple(l.strip() for l in f if l.strip())
    except OSError:
        return ()


def module_names(granted=()):
    return [m.name for m in E.granted_modules(E.load(ROOT), granted)]


# LESSONS.md "A Codex worker's commands run apart from Codex": installed as /opt/kit/bin/bash, which is first on PATH, the
# sandbox user's login shell and $SHELL, so every command Codex runs gets its own sandbox inside this one
KIT_SHELL = os.path.join(REAL_ROOT, ".claude", "sandbox", "kit-shell")


def find_codex_bin_dir(codex, configured, environ):
    """The directory of Codex's real binary (kit-v0.5; it was one hard-coded Homebrew path): KIT_CODEX_BIN_DIR (tests), else
    kit-env.json's codex_bin_dir, else found from the `codex` command (kit-env.json's "codex", default on PATH): a native
    binary's own directory, or the npm package's node_modules/@openai/codex-*/vendor/*/bin/ or vendor/*/bin/. None when
    none is found; the launcher then refuses with "no codex binary"."""
    if environ.get("KIT_CODEX_BIN_DIR"):
        return environ["KIT_CODEX_BIN_DIR"]
    if configured:
        return os.path.expanduser(configured)
    exe = codex if os.path.isabs(codex) else shutil.which(codex)
    if not exe or not os.path.exists(exe):
        return None
    real = os.path.realpath(exe)
    try:
        with open(real, "rb") as f:
            if f.read(4) == b"\x7fELF":
                return os.path.dirname(real)
    except OSError:
        return None
    pkg = os.path.dirname(os.path.dirname(real))   # .../@openai/codex/bin/codex.js -> .../@openai/codex
    hits = sorted(glob.glob(os.path.join(pkg, "node_modules", "@openai", "codex-*", "vendor", "*", "bin", "codex"))
                  + glob.glob(os.path.join(pkg, "vendor", "*", "bin", "codex")))
    return os.path.dirname(hits[0]) if hits else None


_ENV0 = E.load(ROOT)
CODEX_BIN_DIR = find_codex_bin_dir(_ENV0.codex, _ENV0.codex_bin_dir, os.environ) or "/nonexistent-codex-bin-dir"
CODEX_AUTH = os.environ.get("KIT_CODEX_AUTH", os.path.expanduser("~/.codex/auth.json"))
SEARXNG_URL = "http://localhost:7764"
# The model provider's hosts, exact names only (user 2026-09-22 14:04 after canary 096: a subdomain rule let Codex's
# metrics upload to ab.chatgpt.com through). Everything else is refused and logged.
EGRESS_ALLOW = ("chatgpt.com", "api.openai.com", "auth.openai.com")
EGRESS_PORT = 3128                              # inside the sandbox's own network namespace
CODEX_DISABLE = ("apps plugins remote_plugin plugin_sharing auth_elicitation tool_call_mcp_elicitation skill_search "
                 "skill_mcp_dependency_install tool_suggest multi_agent memories hooks goals personality browser_use "
                 "browser_use_external browser_use_full_cdp_access computer_use in_app_local_automation "
                 "image_generation").split()
# LESSONS.md "A Codex worker has no sub-agents": the model catalog's `multi_agent_version: v2` (gpt-5.6-sol and gpt-6-sol in
# codex-cli 0.158.0) gives the model spawn_agent and the other collaboration tools whatever `--disable multi_agent` says (the
# proof instance's canary 015 spawned one). Codex is given its own catalog with the key removed from every model, and a
# launch is refused unless Codex, rendering the prompt offline with the launch's own settings, mentions none of these.
SUBAGENT_MARKERS = ("spawn_agent", "collaboration.", "<multi_agent_mode>")
CATALOG_IN_SANDBOX = "/opt/kit/model-catalog.json"
NON_TOOL_ITEMS = ("agent_message", "reasoning", "error", "todo_list", "user_message")   # every other item is a tool call


def state_dir(rd):
    """Host-side files of a run that the worker must not be able to touch while it runs."""
    d = os.path.join(ROOT, ".claude", "state", "ext", os.path.basename(rd))
    os.makedirs(d, exist_ok=True)
    return d


def egress_sock_path(rd):
    """The host path of a no-network Codex run's egress socket (LESSONS.md "The egress socket's host side is in a short
    private directory"; the source's method change 60). It was state_dir(rd)/egress.sock, which passes Linux's 107-byte
    limit on a unix socket path for a long enough root and slug (the source's run 281 died at bind, after its approval was
    spent). Now a short directory private to this user: $XDG_RUNTIME_DIR/kit-egress/, or /tmp/kit-egress-<uid>/ when
    XDG_RUNTIME_DIR is unset (a detached process may lack it); created mode 0700 and refused unless it is a real directory
    of this user with no group or other access. Only the socket file is bound into the sandbox, never the directory. The
    name is the run number and a hash of the run directory's path, so fixture roots and real runs never share a socket."""
    uid = os.getuid()
    xdg = os.environ.get("XDG_RUNTIME_DIR")
    base = os.path.join(xdg, "kit-egress") if xdg and os.path.isdir(xdg) else f"/tmp/kit-egress-{uid}"
    try:
        os.mkdir(base, 0o700)
    except FileExistsError:
        pass
    st = os.lstat(base)
    if not os.path.isdir(base) or os.path.islink(base) or st.st_uid != uid or st.st_mode & 0o077:
        raise SystemExit(f"_ext.py: refusing the egress socket directory {base}: not a private directory of this user")
    rd = os.path.realpath(rd)
    tag = hashlib.sha256(rd.encode()).hexdigest()[:8]
    p = os.path.join(base, f"{os.path.basename(rd).split('-', 1)[0]}-{tag}.sock")
    if len(p.encode()) > 107:
        raise SystemExit(f"_ext.py: the egress socket path {p} is longer than a unix socket allows (107 bytes)")
    return p


# ------------------------------------------------------------------------------------------ licence relay
LICENCE_SOCK_RE = re.compile(r"^\d+-[0-9a-f]{8}-lic\d+\.sock$")


def licence_sock_path(rd, i):
    """The host path of a run's i-th licence relay socket: beside its egress socket, in the same private directory."""
    return egress_sock_path(rd)[:-len(".sock")] + f"-lic{i}.sock"


def _licence_conn(c, host, port, logf):
    t0 = time.time()
    try:
        u = socket.create_connection((host, port), timeout=15)
        u.settimeout(None)
    except OSError as e:
        log_to(logf, f"UNREACHABLE {host}:{port} ({type(e).__name__})")
        c.close()
        return
    log_to(logf, f"OPEN {host}:{port}")
    sent = [0, 0]

    def pipe(a, b, k):
        try:
            while True:
                d = a.recv(65536)
                if not d:
                    break
                b.sendall(d)
                sent[k] += len(d)
        except OSError:
            pass
        finally:
            for x in (a, b):
                try:
                    x.shutdown(socket.SHUT_RDWR)
                except OSError:
                    pass
    t = [threading.Thread(target=pipe, args=(c, u, 0), daemon=True), threading.Thread(target=pipe, args=(u, c, 1), daemon=True)]
    for x in t:
        x.start()
    for x in t:
        x.join()
    c.close()
    u.close()
    log_to(logf, f"CLOSE {host}:{port} out={sent[0]} in={sent[1]} seconds={time.time() - t0:.1f}")


def start_licence_relays(rd, endpoints, logf):
    """One relay per licence endpoint, for a run granted a licence module (bin/_env.py; the user's "I want to implement
    the network route now", 2026-10-01). Each listens on a unix socket in the run's private socket directory and carries
    every connection to its one fixed host and port: the relay, outside the sandbox, decides where a connection goes;
    the worker only chooses whether to connect. Each connection's open and close, with byte counts, go to `logf`, never
    its contents. Returns [(port, socket path)] in endpoint order (threads: they end with this process)."""
    out = []
    for i, (host, port) in enumerate(endpoints):
        p = licence_sock_path(rd, i)
        try:
            os.unlink(p)
        except FileNotFoundError:
            pass
        srv = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        srv.bind(p)
        os.chmod(p, 0o600)
        srv.listen(32)

        def accept(srv=srv, host=host, port=port):
            while True:
                try:
                    c, _ = srv.accept()
                except OSError:
                    return
                threading.Thread(target=_licence_conn, args=(c, host, port, logf), daemon=True).start()
        threading.Thread(target=accept, daemon=True).start()
        out.append((port, p))
    log_to(logf, "licence relays up: " + ", ".join(f"{h}:{pt}" for h, pt in endpoints))
    return out


def module_check(names):
    """Problems with a launch's --module NAMEs, before any approval: unknown, not a licence module (those are mounted
    for every worker without asking), two granted modules on one port, or the environment file's own problems."""
    env = E.load(ROOT)
    bad = [f"kit-env.json: {p}" for p in env.problems]
    for n in names:
        m = env.modules.get(n)
        if not m:
            bad.append(f"no module {n} in kit-env.json")
        elif not m.on_request:
            bad.append(f"module {n} names no licence server: it is mounted for every worker, with no --module")
    ports = [pt for _, pt in E.licence_endpoints(env, names)]
    if len(ports) != len(set(ports)):
        bad.append("two granted modules share a licence port")
    return bad


def log_to(path, msg):
    with open(path, "a") as f:
        f.write(time.strftime("%Y-%m-%dT%H:%M:%S%z ") + msg + "\n")


# ------------------------------------------------------------------------------------------ search gateway
def read_key(path):
    for line in open(path):
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        if s.startswith("export "):
            s = s[7:].strip()
        m = re.match(r"^[A-Za-z_][A-Za-z0-9_]*\s*=\s*(.+)$", s)
        if m:
            s = m.group(1).strip()
        return s.strip("\"'")
    raise ValueError("no key")


def start_gateway(sd):
    """Start the gateway in a thread of this process; returns its base URL (with the token)."""
    token = secrets.token_hex(16)
    logf = os.path.join(sd, "gateway.log")
    keys = {}
    for name, env, default in (("brave", "BRAVE_KEYFILE", ".env.brave"), ("exa", "EXA_KEYFILE", ".env.exa")):
        try:
            keys[name] = read_key(os.environ.get(env, os.path.join(REAL_ROOT, default)))
        except Exception as e:
            keys[name] = None
    log_to(logf, "gateway up; keys present: " + json.dumps({k: bool(v) for k, v in keys.items()}))

    class H(http.server.BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.0"

        def log_message(self, *a):
            pass

        def _send(self, code, body):
            body = body.encode() if isinstance(body, str) else body
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _relay(self, req, tag, timeout):
            try:
                resp = urllib.request.urlopen(req, timeout=timeout)
            except urllib.error.HTTPError as e:
                resp = e
            except Exception as e:
                log_to(logf, f"{tag} -> gateway error {type(e).__name__}")
                return self._send(502, json.dumps({"error": f"gateway: {type(e).__name__}"}))
            data = resp.read()
            log_to(logf, f"{tag} -> {resp.getcode()} {len(data)}B")
            self._send(resp.getcode(), data)

        def do_GET(self):
            parts = self.path.split("/", 2)
            if len(parts) < 3 or not secrets.compare_digest(parts[1], token):
                log_to(logf, "request without the token -> 403")
                return self._send(403, '{"error":"forbidden"}')
            route, _, query = parts[2].partition("?")
            q = urllib.parse.parse_qs(query)
            if route == "status":
                return self._send(200, json.dumps({k: bool(v) for k, v in keys.items()}))
            if route == "brave":
                if not keys["brave"]:
                    log_to(logf, "brave -> 503 refused: no key configured")
                    return self._send(503, '{"error":"no brave key configured"}')
                term = (q.get("q") or [""])[0]
                url = "https://api.search.brave.com/res/v1/web/search?" + urllib.parse.urlencode(
                    {"q": term, "count": (q.get("count") or ["10"])[0]})
                req = urllib.request.Request(url, headers={"X-Subscription-Token": keys["brave"], "Accept": "application/json"})
                return self._relay(req, f"brave q={term!r}", 60)
            if route in ("exa", "exa-contents"):
                if not keys["exa"]:
                    log_to(logf, f"{route} -> 503 refused: no key configured")
                    return self._send(503, '{"error":"no exa key configured"}')
                if route == "exa":
                    term = (q.get("q") or [""])[0]
                    payload = {"query": term, "numResults": int((q.get("n") or ["10"])[0]),
                               "contents": {"text": {"maxCharacters": 3000}}}
                    url, tag = "https://api.exa.ai/search", f"exa q={term!r}"
                else:
                    target = (q.get("url") or [""])[0]
                    payload, url, tag = {"urls": [target], "text": True}, "https://api.exa.ai/contents", f"exa-contents url={target!r}"
                req = urllib.request.Request(url, data=json.dumps(payload).encode(), method="POST",
                                             headers={"x-api-key": keys["exa"], "Content-Type": "application/json"})
                return self._relay(req, tag, 120)
            log_to(logf, f"{route[:40]!r} -> 404 unknown route")
            return self._send(404, '{"error":"unknown route"}')

    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), H)
    srv.daemon_threads = True
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return f"http://127.0.0.1:{srv.server_address[1]}/{token}"


# ------------------------------------------------------------------------------------------ egress proxy
def start_egress_proxy(sock_path, logf, allow=EGRESS_ALLOW):
    """A CONNECT-only proxy on a unix socket, host side. Passes host:port only when the host is exactly one of
    `allow` (no subdomains); refuses everything else with 403. Logs every request and the bytes carried."""
    if os.path.exists(sock_path):
        os.unlink(sock_path)
    srv = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    srv.bind(sock_path)
    os.chmod(sock_path, 0o600)
    srv.listen(64)

    def allowed(host):
        host = host.lower().rstrip(".")
        return host in allow

    def pipe(a, b, counter, key):
        try:
            while True:
                d = a.recv(65536)
                if not d:
                    break
                b.sendall(d)
                counter[key] += len(d)
        except OSError:
            pass
        finally:
            for s in (a, b):
                try:
                    s.shutdown(socket.SHUT_RDWR)
                except OSError:
                    pass

    def handle(c):
        try:
            head = b""
            while b"\r\n\r\n" not in head and len(head) < 16384:
                d = c.recv(4096)
                if not d:
                    return c.close()
                head += d
            line = head.split(b"\r\n", 1)[0].decode("latin-1")
            m = re.match(r"^CONNECT ([A-Za-z0-9.\-]+):([0-9]{1,5}) HTTP/1\.[01]$", line)
            if not m:
                log_to(logf, f"REFUSED (not a CONNECT) {line[:120]!r}")
                c.sendall(b"HTTP/1.1 405 Method Not Allowed\r\nContent-Length: 0\r\n\r\n")
                return c.close()
            host, port = m.group(1), int(m.group(2))
            if not allowed(host):
                log_to(logf, f"REFUSED {host}:{port}")
                c.sendall(b"HTTP/1.1 403 Forbidden\r\nContent-Length: 0\r\n\r\n")
                return c.close()
            try:
                u = socket.create_connection((host, port), timeout=30)
                u.settimeout(None)
            except OSError as e:
                log_to(logf, f"ALLOWED {host}:{port} upstream error {type(e).__name__}")
                c.sendall(b"HTTP/1.1 502 Bad Gateway\r\nContent-Length: 0\r\n\r\n")
                return c.close()
            c.sendall(b"HTTP/1.1 200 Connection established\r\n\r\n")
            rest = head.split(b"\r\n\r\n", 1)[1]
            if rest:
                u.sendall(rest)
            n = {"up": len(rest), "down": 0}
            t = threading.Thread(target=pipe, args=(c, u, n, "up"), daemon=True)
            t.start()
            pipe(u, c, n, "down")
            t.join(timeout=5)
            log_to(logf, f"ALLOWED {host}:{port} up={n['up']}B down={n['down']}B")
        except Exception as e:
            log_to(logf, f"proxy error {type(e).__name__}")
            try:
                c.close()
            except OSError:
                pass

    def serve():
        while True:
            try:
                c, _ = srv.accept()
            except OSError:
                return
            threading.Thread(target=handle, args=(c,), daemon=True).start()

    threading.Thread(target=serve, daemon=True).start()
    log_to(logf, "egress proxy up; allowlist: " + ", ".join(allow))
    return srv


# ------------------------------------------------------------------------------------------ codex worker
def etc_binds(network):
    """/etc files the sandbox needs. TLS roots always (the tunnel to the provider is TLS end to end); name
    resolution only with --network (without it the proxy resolves names, host side)."""
    files = ["/etc/alternatives", "/etc/ld.so.cache", "/etc/localtime", E.python_etc() or "/nonexistent",
             "/etc/ssl", "/etc/ca-certificates", "/etc/ca-certificates.conf", "/etc/mime.types"]
    if network:
        files += ["/etc/hosts", "/etc/nsswitch.conf"]
    out = []
    for f in files:
        if os.path.exists(f):
            out += ["--ro-bind", f, f]
    if network:
        out += ["--ro-bind", os.path.realpath("/etc/resolv.conf"), "/etc/resolv.conf"]
    return out


def codex_host(sd, args, timeout=120):
    """This Codex binary run on the host, offline (its own network namespace) and with an empty home of its own, so what
    it prints depends on the binary and the arguments only: the user's login and config are never read."""
    home = os.path.join(sd, "probe-home")
    os.makedirs(home, exist_ok=True)
    argv = ["env", "-i", "PATH=/usr/bin:/bin", f"HOME={home}", f"CODEX_HOME={home}", "bwrap", "--dev-bind", "/", "/",
            "--unshare-net", "--die-with-parent", os.path.join(CODEX_BIN_DIR, "codex")] + args
    return subprocess.run(argv, capture_output=True, text=True, timeout=timeout, stdin=subprocess.DEVNULL)


def make_catalog(sd):
    """The binary's own model catalog with `multi_agent_version` removed from every model, at sd/model-catalog.json."""
    r = codex_host(sd, ["debug", "models"])
    try:
        cat = json.loads(r.stdout)
        models = cat["models"]
    except (ValueError, KeyError, TypeError):
        raise RuntimeError(f"codex debug models gave no catalog (exit {r.returncode}): {r.stderr.strip()[-300:]}")
    for m in models:
        m.pop("multi_agent_version", None)
    path = os.path.join(sd, "model-catalog.json")
    with open(path, "w") as f:
        json.dump(cat, f)
    return path


def codex_config(effort, network, catalog):
    """The settings every Codex worker runs with; the offline probe renders the prompt with the same ones."""
    cx = ["-c", f'model_reasoning_effort="{effort}"', "-c", 'web_search="live"' if network else 'web_search="disabled"']
    for f in CODEX_DISABLE:
        cx += ["--disable", f]
    return cx + ["-c", "skills.bundled.enabled=false", "-c", "analytics.enabled=false",   # no metrics upload (canary 096)
                 "-c", f'model_catalog_json="{catalog}"']


def probe(sd, model, effort, network):
    """[problems]: what the offline rendering of this launch's prompt and features shows that the kit rules out."""
    try:
        catalog = make_catalog(sd)
    except (RuntimeError, OSError, subprocess.TimeoutExpired) as e:
        return [f"the model catalog could not be made: {e}"]
    cfg = codex_config(effort, network, catalog)
    out = []
    r = codex_host(sd, ["debug", "prompt-input", "-c", f'model="{model}"'] + cfg + ["probe"])
    if r.returncode != 0 or not r.stdout.strip().startswith("["):
        out.append(f"codex debug prompt-input failed (exit {r.returncode}): {r.stderr.strip()[-300:]}")
    else:
        out += [f"the prompt still offers sub-agents ({m!r})" for m in SUBAGENT_MARKERS if m in r.stdout]
    r = codex_host(sd, ["features", "list"] + cfg)
    on = {ln.split()[0] for ln in r.stdout.splitlines() if ln.split() and ln.split()[-1] == "true"}
    if r.returncode != 0 or not r.stdout.strip():
        out.append(f"codex features list failed (exit {r.returncode})")
    out += [f"feature {f} is still on" for f in CODEX_DISABLE if f in on]
    return out


def kill_all_in_ns(host_pidns):
    """The script's last step ends whatever the worker left running: `kill -KILL -1`, every process the script can signal.
    Inside the sandbox's own process namespace that is the sandbox's processes only; outside one it would be every process
    of the user's Unix account (tmux, every session, the user services). So it runs only when the script's process namespace
    differs from the host's, given when the sandbox is built (the source's review of this line, 2026-09-30; tests
    test_own_pid_namespace and test_kill_all_guard)."""
    return (f'if [ "$(readlink /proc/self/ns/pid)" != "{host_pidns}" ]; then kill -KILL -1 2>/dev/null; '
            'else echo "codex-worker: not in its own process namespace; the remaining processes are left" >&2; fi\n')


def codex_argv(rd, sd, model, effort, network, auth_fd, limits, gateway=None, catalog=None, sock=None, granted=(),
               licence=None):
    """The full bwrap command line for one Codex worker. `auth_fd` is an open descriptor of the auth file; `sock` the host
    path of the egress socket (egress_sock_path(rd) when not given)."""
    n = str(limits["threads"])
    with open(os.path.join(sd, "passwd"), "w") as f:
        f.write(f"worker:x:{os.getuid()}:{os.getgid()}:worker:{rd}:/opt/kit/bin/bash\n")
    with open(os.path.join(sd, "group"), "w") as f:
        f.write(f"worker:x:{os.getgid()}:\n")
    # A licence module on a run without the network: the relay sockets, an /etc/hosts naming each licence host at
    # 127.0.0.1, and KIT_LICENCE_FWD for kit-shell, which starts a forwarder in each command's own sandbox.
    lic_etc, lic_mounts, lic_env = [], [], []
    if licence and not network:
        endpoints = E.licence_endpoints(E.load(ROOT), granted)
        with open(os.path.join(sd, "hosts"), "w") as f:
            f.write(E.hosts_text(endpoints))
        lic_etc = ["--ro-bind", os.path.join(sd, "hosts"), "/etc/hosts"] + (
            ["--ro-bind", "/etc/nsswitch.conf", "/etc/nsswitch.conf"] if os.path.exists("/etc/nsswitch.conf") else [])
        for i, (_, path) in enumerate(licence):
            lic_mounts += ["--ro-bind", path, f"/opt/kit/licence/{i}.sock"]
        lic_env = ["--setenv", "KIT_LICENCE_FWD", " ".join(f"{pt}=/opt/kit/licence/{i}.sock" for i, (pt, _) in enumerate(licence))]
    a = ["env", "-i", "PATH=/usr/bin:/bin", "bwrap",
         "--ro-bind", "/usr", "/usr", "--symlink", "usr/lib", "/lib", "--symlink", "usr/lib64", "/lib64",
         "--symlink", "usr/bin", "/bin", "--symlink", "usr/sbin", "/sbin",
         "--tmpfs", "/etc"] + etc_binds(network) + [
         "--ro-bind", os.path.join(sd, "passwd"), "/etc/passwd", "--ro-bind", os.path.join(sd, "group"), "/etc/group"] + lic_etc + [
         "--remount-ro", "/etc",
         "--proc", "/proc", "--dev", "/dev", "--tmpfs", "/tmp",
         "--bind", rd, rd,
         "--ro-bind", LEDGER_SHIM, "/opt/kit/bin/ledger",
         "--ro-bind", KIT_SHELL, "/opt/kit/bin/bash",   # found first on PATH, and the login shell
         "--ro-bind", CODEX_BIN_DIR, "/opt/codex"] + (
         ["--ro-bind", catalog, CATALOG_IN_SANDBOX] if catalog else []) + [
         "--tmpfs", "/opt/codex-home",
         "--perms", "0600", "--file", str(auth_fd), "/opt/codex-home/auth.json"]
    mod_args, mod_path, mod_env = module_parts(granted)
    a += mod_args + lic_mounts
    if network:
        for h in ("brave", "exa", "exa-contents"):
            a += ["--ro-bind", os.path.join(HARNESS, "bin", h), "/opt/kit/bin/" + h]
    else:
        a += ["--ro-bind", os.path.join(HARNESS, "egress-fwd"), "/opt/kit/bin/egress-fwd",
              "--bind", sock or egress_sock_path(rd), "/opt/kit/egress.sock"]   # the socket file only
    # LESSONS.md "The sandbox's root is remounted read-only after the binds": the root tmpfs read-only after every bind and file, so
    # the directories bwrap creates for mount points (the run dir's parent chain, /home, /opt) are not writable; a
    # write to ../x used to succeed inside and reach nothing. The run dir, /tmp and /opt/codex-home are mounts of
    # their own and stay writable (remount is not recursive); the egress socket still connects.
    a += ["--remount-ro", "/"]
    a += ["--chdir", rd, "--unshare-all"] + (["--share-net"] if network else []) + [
          "--hostname", "sandbox", "--die-with-parent", "--clearenv",
          "--setenv", "HOME", rd, "--setenv", "TMPDIR", "/tmp", "--setenv", "LANG", "C.UTF-8", "--setenv", "TERM", "dumb",
          "--setenv", "PATH", "/opt/kit/bin:/opt/codex:" + mod_path + "/usr/bin:/bin",
          "--setenv", "CODEX_HOME", "/opt/codex-home", "--setenv", "SSL_CERT_FILE", "/etc/ssl/certs/ca-certificates.crt",
          "--setenv", "KIT_RUN", rd, "--setenv", "PYTHONDONTWRITEBYTECODE", "1",
          "--setenv", "SHELL", "/opt/kit/bin/bash", "--setenv", "KIT_CMD_NET", "1" if network else "0"] + (
          mod_env + lic_env) + [
          "--setenv", "OMP_NUM_THREADS", n, "--setenv", "OPENBLAS_NUM_THREADS", n, "--setenv", "MKL_NUM_THREADS", n,
          "--setenv", "NUMEXPR_NUM_THREADS", n, "--setenv", "KIT_THREADS", n,
          # P-11 (e): the caps a worker's own scripts read (SCHEMAS.md §7), as the hook sets them on the Claude routes
          "--setenv", "KIT_CPU_HOURS", str(limits["cpu_hours"]), "--setenv", "KIT_MEM_GB", str(limits["mem_gb"])]
    if network:
        a += ["--setenv", "SEARXNG_URL", SEARXNG_URL] + (["--setenv", "GATEWAY", gateway] if gateway else [])
    else:
        px = f"http://127.0.0.1:{EGRESS_PORT}"
        for v in ("HTTPS_PROXY", "https_proxy", "HTTP_PROXY", "http_proxy", "ALL_PROXY", "all_proxy"):
            a += ["--setenv", v, px]
    script = f"ulimit -t {limits['cpu_seconds']}\n"
    if not network:
        script += (f"python3 /opt/kit/bin/egress-fwd {EGRESS_PORT} /opt/kit/egress.sock /tmp/.fwd-ready &\n"
                   "for i in $(seq 100); do [ -e /tmp/.fwd-ready ] && break; sleep 0.1; done\n")
    # Not `exec`: after codex exits, its session files (the only place Codex records the effort and model it ran at) are
    # copied into the run, then the exit status is passed on (user 2026-09-22 14:32, item 5). Every one of them: a
    # sub-agent has a session file of its own, and the first found was once the sub-agent's (canary 015); the host
    # names the main thread's by the thread id of the transcript it copied (sort_rollouts).
    # P-12 C3: what the worker left is ended first (only inside its own namespace), so nothing of it can write the session
    # files' copies while they are made.
    script += ('"$@"; rc=$?\n'
               + kill_all_in_ns(os.readlink("/proc/self/ns/pid")) +
               'rm -rf "$KIT_RUN/launch.rollouts"; mkdir -p "$KIT_RUN/launch.rollouts"\n'
               'find /opt/codex-home/sessions -name "rollout-*.jsonl" 2>/dev/null | sort | while read -r f; do\n'
               '  cp "$f" "$KIT_RUN/launch.rollouts/"\n'
               'done\n'
               'exit $rc\n')
    cx = ["/opt/codex/codex", "exec", "--model", model] + codex_config(effort, network, CATALOG_IN_SANDBOX) + [
           "--dangerously-bypass-approvals-and-sandbox",
           "--skip-git-repo-check", "--ignore-rules", "--ignore-user-config",   # not --ephemeral: see script
           "--cd", rd, "--json", "-o", os.path.join(rd, "launch.last.md"), "-"]
    return a + ["--", "/bin/bash", "-c", script, "codex-worker"] + cx


def sort_rollouts(rd, transcript):
    """RD/launch.rollouts/ -> RD/launch.rollout.jsonl (the session file whose id is the transcript's thread id) and
    RD/launch.rollout.sub-N.jsonl (any other: a sub-agent's). Returns (main found, number of others)."""
    src = os.path.join(rd, "launch.rollouts")
    tid = None
    if os.path.isfile(transcript):
        for line in open(transcript, errors="replace"):
            try:
                e = json.loads(line)
            except ValueError:
                continue
            if isinstance(e, dict) and e.get("type") == "thread.started":
                tid = e.get("thread_id")
                break
    main, subs = False, 0
    for f in glob.glob(os.path.join(rd, "launch.rollout*.jsonl")):   # P-12 C3: only what is sorted here is the record
        os.remove(f)
    if os.path.isdir(src) and not os.path.islink(src):
        for f in sorted(os.listdir(src)):
            p = os.path.join(src, f)
            if not os.path.isfile(p) or os.path.islink(p):
                continue
            sid = None
            try:
                first = json.loads(open(p, errors="replace").readline())
                sid = (first.get("payload") or {}).get("id") if first.get("type") == "session_meta" else None
            except (ValueError, AttributeError):
                pass
            if tid and sid == tid and not main:
                os.replace(p, os.path.join(rd, "launch.rollout.jsonl"))
                main = True
            else:
                subs += 1
                os.replace(p, os.path.join(rd, f"launch.rollout.sub-{subs}.jsonl"))
        shutil.rmtree(src, ignore_errors=True)
    return main, subs


def descendants(pid):
    """Every process below `pid`, by /proc's children lists (the sandbox's processes, seen from the host)."""
    out, todo = [], [pid]
    while todo:
        q = todo.pop()
        for task in glob.glob(f"/proc/{q}/task/*/children"):
            try:
                kids = [int(x) for x in open(task).read().split()]
            except OSError:
                continue
            out += kids
            todo += kids
    return out


def stop_codex(p):
    """Stop a Codex worker at a cap without losing its session files (live run 009 of the review instance, 2026-09-29:
    stopping the sandbox also stopped the script that copies them, so a capped run recorded no model and no effort).
    TERM goes to the codex process inside the sandbox; the sandbox's script then copies the session files and exits.
    Returns at once; if the sandbox has not ended 30 s later, it is terminated, and killed 30 s after that."""
    for pid in descendants(p.pid):
        try:
            if open(f"/proc/{pid}/comm").read().strip() == "codex":
                os.kill(pid, signal.SIGTERM)
        except OSError:
            pass

    def fallback():
        if p.poll() is None:
            p.terminate()
            time.sleep(30)
            if p.poll() is None:
                p.kill()
    timer = threading.Timer(30, fallback)
    timer.daemon = True   # never holds up the launcher's own exit
    timer.start()


def run_limits(rd):
    """RD/.limits, read by the hook's own function so the Codex worker gets the same caps as a Claude worker."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("sandbox_hook", L.HOOK)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.run_limits(rd)


def cmd_codex(args):
    import argparse
    ap = argparse.ArgumentParser(prog="_ext.py codex")
    ap.add_argument("rd")
    ap.add_argument("--model", required=True)
    ap.add_argument("--effort", default="high")
    ap.add_argument("--wall-hours", type=float, default=2.0)   # LESSONS.md 'A wall-clock cap on every route': bin/run-external always passes it
    ap.add_argument("--network", action="store_true")
    ap.add_argument("--max-turns", type=int, default=300)   # LESSONS.md "A Codex worker's tool calls are capped": bin/run-external passes it
    ap.add_argument("--prompt")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--module", action="append", default=[])   # a licence module, bound in the launch approval
    ap.add_argument("--approval")   # the used approval's digest: the bytes are read again against it before the start
    a = ap.parse_args(args)
    granted = tuple(a.module)
    rd = os.path.realpath(a.rd)
    sd = state_dir(rd)
    note = open(os.path.join(rd, "HARNESS-NOTE.md")).read()
    task = a.prompt or (f"Start by reading {rd}/BRIEF.md (print it with cat), then follow it exactly. "
                        f"Your run directory is {rd}.")
    prompt = note.rstrip("\n") + "\n\n" + task + "\n"
    if not os.access(os.path.join(CODEX_BIN_DIR, "codex"), os.X_OK):
        print(f"_ext.py codex: no codex binary at {CODEX_BIN_DIR}", file=sys.stderr)
        return 2
    lim = run_limits(rd)
    gateway = None
    if a.dry_run:
        import shlex
        lic = [(pt, f"<licence socket {i}>") for i, (_, pt) in enumerate(E.licence_endpoints(E.load(ROOT), granted))]
        argv = codex_argv(rd, sd, a.model, a.effort, a.network, 99, lim, "<gateway url>" if a.network else None,
                          os.path.join(sd, "model-catalog.json"), granted=granted, licence=lic or None)
        print(" ".join(shlex.quote(x) for x in argv))
        print(f"--- stdin (prompt, {len(prompt)} chars): HARNESS-NOTE.md, a blank line, then:\n{task}")
        print(f"--- tool-call cap: {a.max_turns} (the worker is stopped at the next one)")
        return 0
    try:
        catalog = make_catalog(sd)
    except (RuntimeError, OSError, subprocess.TimeoutExpired) as e:
        print(f"_ext.py codex: refused: {e}", file=sys.stderr)
        return 2
    sock = None
    if a.network:
        gateway = start_gateway(sd)
    else:
        sock = egress_sock_path(rd)   # a short private directory, not state_dir(rd): the 107-byte limit
        start_egress_proxy(sock, os.path.join(sd, "egress.log"))
    licence = None
    if granted and not a.network:
        bad = module_check(granted)
        if bad:
            print("_ext.py codex: refused: " + "; ".join(bad), file=sys.stderr)
            return 2
        licence = start_licence_relays(rd, E.licence_endpoints(E.load(ROOT), granted), os.path.join(sd, "licence.log"))
    with open(os.path.join(sd, "prompt.md"), "w") as f:
        f.write(prompt)
    auth = open(CODEX_AUTH, "rb")
    argv = codex_argv(rd, sd, a.model, a.effort, a.network, auth.fileno(), lim, gateway, catalog, sock, granted, licence)
    t0 = time.time()
    timed_out = False
    logs = os.path.join(sd, "logs")   # outside the sandbox; bin/run-external moves them into the run at exit
    os.makedirs(logs, exist_ok=True)
    # LESSONS.md "A Codex worker's commands run apart from Codex": the transcript reaches the host through pipes this
    # process reads; no process in the sandbox ever holds the host's log files, so none can truncate or rewrite them
    # (Codex's stdout used to be the file itself, and a worker rewrote it through /proc/1/fd/1). Each stream is copied
    # line by line with a running sha256 chain, recorded beside it.
    # LESSONS.md "A Codex worker's tool calls are capped": Codex has no turn cap of its own, so the copy of its transcript
    # counts the tool calls (items other than messages and reasoning) as they start, and past --max-turns stops the worker.
    import threading
    chains = {}
    calls, cap = set(), {"hit": False}

    def copy(stream, path, name):
        h, n = hashlib.sha256(b"kit-transcript-chain/1"), 0
        with open(path, "wb") as f:
            for line in iter(stream.readline, b""):
                f.write(line)
                f.flush()
                h = hashlib.sha256(h.digest() + line)
                n += 1
                if name == "launch.jsonl" and not cap["hit"]:
                    try:
                        e = json.loads(line)
                        it = e.get("item") if e.get("type") in ("item.started", "item.completed") else None
                    except (ValueError, AttributeError):
                        it = None
                    if isinstance(it, dict) and it.get("type") not in NON_TOOL_ITEMS:
                        calls.add(it.get("id") or f"line-{n}")
                        if len(calls) > a.max_turns:
                            cap["hit"] = True
                            stop_codex(p)
        chains[name] = {"lines": n, "sha256": h.hexdigest()}

    if a.approval:   # P-12 (a medium): the set-up above took time after the approval was used; the bytes again, last
        import _approval as A
        try:
            A.verify_launch(rd, a.approval, ROOT)
        except A.Refused as e:
            print(f"_ext.py codex: refused: {e}", file=sys.stderr)
            if sock and os.path.exists(sock):
                os.unlink(sock)
            return 3
    with open(os.path.join(sd, "prompt.md"), "rb") as pin:
        p = subprocess.Popen(argv, stdin=pin, stdout=subprocess.PIPE, stderr=subprocess.PIPE, pass_fds=(auth.fileno(),))
        auth.close()
        # LESSONS.md "The whole-run CPU budget is enforced": bin/limits-exec stops a run at its CPU cap with TERM to this
        # process; stop the worker as at the other caps, so the exit record is written and the session file kept.
        term = {"hit": False}

        def on_term(signum, frame):
            if not term["hit"]:
                term["hit"] = True
                stop_codex(p)
        signal.signal(signal.SIGTERM, on_term)
        readers = [threading.Thread(target=copy, args=(p.stdout, os.path.join(logs, "launch.jsonl"), "launch.jsonl")),
                   threading.Thread(target=copy, args=(p.stderr, os.path.join(logs, "launch.err"), "launch.err"))]
        for r in readers:
            r.start()
        try:
            rc = p.wait(timeout=a.wall_hours * 3600)
        except subprocess.TimeoutExpired:
            timed_out = True
            stop_codex(p)
            rc = p.wait()
        for r in readers:
            r.join(timeout=60)
    if sock and os.path.exists(sock):   # the socket does not outlive its run
        os.unlink(sock)
    main, subs = sort_rollouts(rd, os.path.join(logs, "launch.jsonl"))
    with open(os.path.join(sd, "codex-exit.json"), "w") as f:
        json.dump({"exit": rc, "wall_seconds": round(time.time() - t0, 1), "timed_out": timed_out,
                   "wall_hours_cap": a.wall_hours, "transcript_chain": chains, "tool_calls": len(calls),
                   "max_turns": a.max_turns, "turn_cap_hit": cap["hit"], "main_rollout": main, "sub_rollouts": subs,
                   "stopped_by_signal": term["hit"]}, f)
    if subs:
        print(f"_ext.py codex: WARNING: {subs} session file(s) besides the main thread's: a sub-agent ran", file=sys.stderr)
    if term["hit"]:
        print("_ext.py codex: stopped by TERM (the run's CPU budget, bin/limits-exec); the worker was stopped", file=sys.stderr)
        return 152
    if timed_out:
        print(f"_ext.py codex: wall-clock cap of {a.wall_hours} h reached; the worker was stopped", file=sys.stderr)
        return 124
    if cap["hit"]:
        print(f"_ext.py codex: tool-call cap of {a.max_turns} reached; the worker was stopped", file=sys.stderr)
        return 125
    return rc


# ------------------------------------------------------------------------------------------ record
def sha256(p):
    return L.sha256(p)


def summarise_codex(path):
    s = {"events": 0, "items": {}, "usage": None, "errors": 0}
    for line in open(path, errors="replace"):
        try:
            e = json.loads(line)
        except ValueError:
            continue
        s["events"] += 1
        it = e.get("item") if isinstance(e.get("item"), dict) else None
        if e.get("type") == "item.completed" and it:
            s["items"][it.get("type")] = s["items"].get(it.get("type"), 0) + 1
        if e.get("type") == "turn.completed":
            s["usage"] = e.get("usage")
        if e.get("type") in ("error", "turn.failed"):
            s["errors"] += 1
    return s


def summarise_claude(path):
    s = {"tools": {}, "result": None}
    for line in open(path, errors="replace"):
        try:
            e = json.loads(line)
        except ValueError:
            continue
        if e.get("type") == "assistant":
            for c in (e.get("message") or {}).get("content") or []:
                if isinstance(c, dict) and c.get("type") == "tool_use":
                    s["tools"][c.get("name")] = s["tools"].get(c.get("name"), 0) + 1
        if e.get("type") == "result":
            s["result"] = {k: e.get(k) for k in ("subtype", "is_error", "num_turns", "duration_ms", "total_cost_usd")}
    return s


def effort_seen(rd, via):
    """What effort the model's requests actually carried, from the run's own records (item 5 of 2026-09-22):
    Codex: the session file's turn contexts; Claude: the session transcript Claude Code keeps under
    ~/.claude/projects/. Returns {value: count}, or {} when the record holds nothing."""
    counts = {}
    if via == "codex":
        path = os.path.join(rd, "launch.rollout.jsonl")
        if not os.path.isfile(path):
            return counts
        for line in open(path, errors="replace"):
            try:
                e = json.loads(line)
            except ValueError:
                continue
            if e.get("type") == "turn_context":
                pl = e.get("payload") or {}
                v = pl.get("effort") or pl.get("reasoning_effort") or (pl.get("reasoning") or {}).get("effort")
                if v:
                    counts[v] = counts.get(v, 0) + 1
        return counts
    log = os.path.join(rd, "launch.log")
    sid = None
    if os.path.isfile(log):
        for line in open(log, errors="replace"):
            try:
                e = json.loads(line)
            except ValueError:
                continue
            if e.get("type") == "system" and e.get("subtype") == "init":
                sid = e.get("session_id"); break
    if not sid:
        return counts
    proj = os.path.expanduser("~/.claude/projects/" + re.sub(r"[^A-Za-z0-9]", "-", REAL_ROOT))
    tr = os.path.join(proj, sid + ".jsonl")
    if os.path.isfile(tr):
        for v in re.findall(r'"effort":"([a-z]+)"', open(tr, errors="replace").read()):
            counts[v] = counts.get(v, 0) + 1
    return counts


def fmt_effort(counts):
    return ",".join(f"{k}*{v}" for k, v in sorted(counts.items())) or "none-recorded"   # the source's method change 77


def drain_outbox(rd):
    ob = os.path.join(rd, ".ledger-outbox")
    if os.path.islink(ob) or not os.path.isfile(ob):
        return 0
    # P-12 C2: the check above is not the guard; O_NOFOLLOW refuses a link made after it, and only a regular file is read
    fd = os.open(ob, os.O_RDWR | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(fd, "r+", errors="replace") as f:
        if not stat.S_ISREG(os.fstat(fd).st_mode):
            return 0
        data = f.read(64000)
        f.seek(0); f.truncate()
    n = 0
    for line in data.splitlines():
        if line.strip():
            L.append_ledger(L.LEDGER, f"{L.now()} | codex-worker | {os.path.basename(rd)} | NOTE | {' '.join(line.split())[:400]}\n")
            n += 1
    return n


def plan_limit(rd):
    """LESSONS.md "The ChatGPT plan's usage limit is detected and reported": the ChatGPT plan's usage limit is a cap the
    launcher cannot see in advance (it ended one of the source's runs at 25 minutes). Codex reports it as an `error` / `turn.failed`
    event: "You've hit your usage limit. … try again at <time>." Returns None, or the text after "try again at"."""
    p = os.path.join(rd, "launch.jsonl")
    if not os.path.isfile(p):
        return None
    for line in open(p, errors="replace"):
        if "usage limit" not in line:
            continue
        try:
            e = json.loads(line)
        except ValueError:
            continue
        msg = e.get("message") or (e.get("error") or {}).get("message") or ""
        if e.get("type") in ("error", "turn.failed") and "usage limit" in msg:
            m = re.search(r"try again at (.+?)\.?$", msg)
            return m.group(1) if m else "unknown time"
    return None


def at_capacity(rd):
    """Codex's refusal to start because the model is busy (seen live 2026-09-25: "Selected model is at capacity. Please try
    a different model."), an `error` / `turn.failed` event like the plan's usage limit. Nothing ran; the approval was
    spent. Returns the message, or None."""
    p = os.path.join(rd, "launch.jsonl")
    if not os.path.isfile(p):
        return None
    for line in open(p, errors="replace"):
        if "capacity" not in line:
            continue
        try:
            e = json.loads(line)
        except ValueError:
            continue
        msg = e.get("message") or (e.get("error") or {}).get("message") or ""
        if e.get("type") in ("error", "turn.failed") and "at capacity" in msg:
            return msg
    return None


def queue_stop(rd):
    """LESSONS.md "A queue stops at the plan's usage limit": why a queue must not release its next run after this one, or
    None. A run that ended on the ChatGPT plan's usage limit or on the provider's capacity refusal says the next would end the
    same way, and a released run keeps a launch record (a run directory is launched once)."""
    t = plan_limit(rd)
    if t:
        return f"the ChatGPT plan's usage limit (try again at {t})"
    m = at_capacity(rd)
    return f"the provider's capacity refusal ({m})" if m else None


def chain_of(path):
    """(lines, sha256) of a transcript file by the host-side copy's chain (see cmd_codex)."""
    h, n = hashlib.sha256(b"kit-transcript-chain/1"), 0
    with open(path, "rb") as f:
        for line in iter(f.readline, b""):
            h = hashlib.sha256(h.digest() + line)
            n += 1
    return n, h.hexdigest()


def chain_line(rd, cx):
    """The record's line on the transcript's integrity: the chain the host computed while copying, against the file as it
    stands now."""
    want = (cx or {}).get("transcript_chain", {}).get("launch.jsonl")
    p = os.path.join(rd, "launch.jsonl")
    if not cx:   # no exit record at all: the launch died before Codex started (the source's run 281)
        return "- transcript chain: none recorded (the worker never started: no exit record)"
    if not want:
        return "- transcript chain: none recorded (launched before kit-v0.3.1)"
    if not os.path.isfile(p):
        return "- transcript chain: recorded, but launch.jsonl is missing"
    n, h = chain_of(p)
    ok = (n, h) == (want["lines"], want["sha256"])
    return (f"- transcript chain: {'matches' if ok else 'DOES NOT MATCH'} the host's copy ({want['lines']} lines, "
            f"sha256 {want['sha256'][:16]}…); written through a pipe the worker's commands cannot reach")


def cmd_record(args):
    import argparse
    ap = argparse.ArgumentParser(prog="_ext.py record")
    ap.add_argument("rd")
    ap.add_argument("--via", required=True)
    ap.add_argument("--model", required=True)
    ap.add_argument("--network", action="store_true")
    ap.add_argument("--exit", type=int, default=None)
    a = ap.parse_args(args)
    rd = os.path.realpath(a.rd)
    name = os.path.basename(rd)
    sd = state_dir(rd)
    for f in ("gateway.log", "egress.log", "licence.log"):
        if os.path.isfile(os.path.join(sd, f)):   # P-12 C2: over any link the worker left at the name, never through it
            with open(os.path.join(sd, f), "rb") as src:
                L.write_in_run(rd, f, src.read())
    notes = drain_outbox(rd) if a.via == "codex" else None
    transcript = os.path.join(rd, "launch.jsonl" if a.via == "codex" else "launch.log")
    eff = effort_seen(rd, a.via)
    files = [p for p in (transcript, os.path.join(rd, "launch.err"), os.path.join(rd, "launch.last.md"),
                         os.path.join(rd, "launch.rollout.jsonl"),
                         os.path.join(rd, "gateway.log"), os.path.join(rd, "egress.log"),
                         os.path.join(rd, "licence.log")) if os.path.isfile(p)]
    files += sorted(glob.glob(os.path.join(rd, "launch.rollout.sub-*.jsonl")))
    seen, _ = L.models_seen(rd)
    mflag = L.model_flag(rd, a.model)
    mav = set()
    if a.via == "codex" and os.path.isfile(os.path.join(rd, "launch.rollout.jsonl")):
        for line in open(os.path.join(rd, "launch.rollout.jsonl"), errors="replace"):
            if '"turn_context"' in line:
                try:
                    mav.add(str((json.loads(line).get("payload") or {}).get("multi_agent_version")))
                except (ValueError, AttributeError):
                    pass
    dl = os.path.join(rd, "downloads")
    downloads = []
    if os.path.isdir(dl):
        for dp, dn, fn in os.walk(dl):
            dn.sort()
            for f in sorted(fn):
                p = os.path.join(dp, f)
                if os.path.isfile(p) and not os.path.islink(p):
                    downloads.append(p)
    summary = (summarise_codex(transcript) if a.via == "codex" else summarise_claude(transcript)) if os.path.isfile(transcript) else {}
    egress = {"allowed": 0, "refused": 0}
    if os.path.isfile(os.path.join(rd, "egress.log")):
        for line in open(os.path.join(rd, "egress.log")):
            egress["allowed"] += " ALLOWED " in line
            egress["refused"] += " REFUSED " in line
    gw = 0
    if os.path.isfile(os.path.join(rd, "gateway.log")):
        gw = sum(1 for line in open(os.path.join(rd, "gateway.log")) if " -> " in line)
    cx = {}
    try:
        cx = json.load(open(os.path.join(sd, "codex-exit.json")))
    except Exception:
        pass
    if a.via == "codex":
        net = ("host network shared: open web, this machine's localhost, live web search" if a.network else
               "own network namespace; out only through the egress proxy, allowlist " + ", ".join(EGRESS_ALLOW)
               + f"; web search disabled; {egress['allowed']} tunnels allowed, {egress['refused']} refused")
        token = ("a copy of the user's ~/.codex/auth.json lived in the sandbox's private tmpfs for the run, for the Codex "
                 "process; the model's commands ran with Codex's home hidden and could not read it; it is gone with the sandbox")
        reads = ("the run directory (read-write); /usr, the CLI binary"
                 + "".join(f", the module {n}" for n in module_names(run_modules(rd)))
                 + " (read-only); nothing else of the user's home")
    else:
        net = ("Bash sandbox shares the host network (open web, this machine's localhost); WebSearch and WebFetch run in "
               "the Claude Code process on the host" if a.network else "none")
        token = "none in the sandbox (the route's key, if any, stays in the host process's environment)"
        reads = ("Read/Write: the run directory only (hook); Bash: the run directory and /usr"
                 + "".join(f", the module {n}" for n in module_names(run_modules(rd))) + " (read-only)")
    lines = [f"# External run record — {name}", "",
             f"Written by bin/_ext.py record at {L.now()} (LESSONS.md 'Networked and Codex launches need their flags bound'). Every hash below is of the file as it "
             "stood when the run ended. The transcript and the launcher's logs were written outside the worker's reach "
             "and moved in after it stopped; launch.last.md and downloads/ were written from inside the sandbox.", "",
             f"- route: `--via {a.via}`, model `{a.model}`, network: {'on' if a.network else 'off'}",
             f"- effort the model's requests carried: {fmt_effort(eff)} "
             + ("(Codex session file, turn contexts)" if a.via == "codex" else "(Claude Code session transcript)"),
             "- models that answered: " + (", ".join(f"{m}*{n}" for m, n in sorted(seen.items())) or "none recorded")
             + (f"; NOT ONE MODEL: {mflag}" if mflag else ""),
             f"- exit: {a.exit if a.exit is not None else cx.get('exit', '?')}"
             + (f"; wall {cx.get('wall_seconds')} s of a {cx.get('wall_hours_cap')} h cap"
                + ("; STOPPED AT THE CAP" if cx.get("timed_out") else "") if cx else ""),
             (f"- ChatGPT plan usage limit: HIT, the run was ended by it (Codex: try again at {plan_limit(rd)})"
              if a.via == "codex" and plan_limit(rd) else
              "- ChatGPT plan usage limit: not hit" if a.via == "codex" else "- ChatGPT plan usage limit: n/a (Claude route)"),
             (f"- model at capacity: YES, the provider refused to start the run ({at_capacity(rd)}); nothing ran"
              if a.via == "codex" and at_capacity(rd) else "- model at capacity: no" if a.via == "codex" else
              "- model at capacity: n/a (Claude route)"),
             chain_line(rd, cx) if a.via == "codex" else "- transcript chain: n/a (Claude route: Claude Code writes it on the host)",
             (f"- tool calls: {cx.get('tool_calls', '?')} of a cap of {cx.get('max_turns', '?')}"
              + ("; STOPPED AT THE TOOL-CALL CAP" if cx.get("turn_cap_hit") else "")) if a.via == "codex" else
             "- tool calls: capped by Claude Code's --max-turns",
             (f"- session files: the main thread's {'copied' if cx.get('main_rollout') else 'NOT FOUND'}; "
              f"{cx.get('sub_rollouts', 0)} other (a sub-agent's){'; A SUB-AGENT RAN' if cx.get('sub_rollouts') else ''}; "
              f"multi_agent_version in the turn contexts: {', '.join(sorted(mav)) or 'none'}") if a.via == "codex" else
             "- session files: n/a (Claude route)",
             f"- what the model could read: {reads}",
             f"- network: {net}",
             f"- token exposure: {token}",
             f"- search gateway requests: {gw}" if a.network else "- search gateway: not started",
             f"- worker ledger notes moved to the ledger: {notes}" if notes is not None else "- worker ledger notes: moved by the hook",
             f"- transcript summary: `{json.dumps(summary, sort_keys=True)}`", "",
             "## Hashes (sha256, bytes, path relative to the run directory)", "```"]
    for p in files + downloads:
        lines.append(f"{sha256(p)}  {os.path.getsize(p):>10}  {os.path.relpath(p, rd)}")
    lines += ["```", f"downloads: {len(downloads)} files", ""]
    L.write_in_run(rd, "RECORD-EXT.md", "\n".join(lines))
    tsha = sha256(transcript)[:16] if os.path.isfile(transcript) else "-"
    L.ledger(name, "RECORD-EXT", f"via={a.via} model={a.model} network={'on' if a.network else 'off'} effort_seen={fmt_effort(eff)} "
             f"models_seen={fmt_effort(seen)} model_fallback={'yes' if mflag else 'no'} "
             f"transcript={os.path.basename(transcript)}@{tsha} downloads={len(downloads)} gateway={gw} "
             f"egress_allowed={egress['allowed']} egress_refused={egress['refused']}")
    print(f"_ext.py record: {os.path.relpath(os.path.join(rd, 'RECORD-EXT.md'), ROOT)} ({len(files)} logs, {len(downloads)} downloads)")
    return 0


def cmd_gateway(args):
    sd, portfile = args
    url = start_gateway(sd)
    with open(portfile + ".tmp", "w") as f:
        f.write(url)
    os.replace(portfile + ".tmp", portfile)
    while True:
        time.sleep(3600)


UPSTREAM_LIMIT = re.compile(r"malformed response \(HTTP 200\)|rate-limited upstream|rate_limit_error")


def upstream_limited(log, err):
    """Whether a Claude-route launch ended on an upstream rate limit (bin/run-external's retry). P-12 H4: only the CLI's own
    words count, its stderr and its transcript's events, never a tool result or the model's own message, which the worker
    writes: a worker that printed the phrase bought a retry with fresh caps."""
    try:
        if UPSTREAM_LIMIT.search(open(err, errors="replace").read()):
            return True
    except OSError:
        pass
    try:
        lines = open(log, errors="replace")
    except OSError:
        return False
    with lines:
        for line in lines:
            if not UPSTREAM_LIMIT.search(line):
                continue
            try:
                e = json.loads(line)
            except ValueError:
                continue   # not an event of the CLI's
            if not isinstance(e, dict) or e.get("type") == "user":
                continue   # tool results
            if e.get("type") == "assistant" and (e.get("message") or {}).get("model") != "<synthetic>":
                continue   # the model's own text; the CLI's error messages are "<synthetic>"
            return True
    return False


def hook_registered(settings, hook):
    """Whether settings (a dict) run `hook` on PreToolUse for every tool and on PostToolUse (pending item P-11 (g):
    bin/run-external's preflight only looked for the path anywhere in the file)."""
    def on(event):
        for e in ((settings.get("hooks") or {}).get(event) or []):
            if isinstance(e, dict) and e.get("matcher") in (None, "", "*") and \
                    any(isinstance(h, dict) and h.get("command") == hook for h in e.get("hooks") or []):
                return True
        return False
    return isinstance(settings, dict) and on("PreToolUse") and on("PostToolUse")


def main():
    if len(sys.argv) < 2:
        print(__doc__, file=sys.stderr)
        return 2
    cmd, rest = sys.argv[1], sys.argv[2:]
    if cmd == "codex":
        return cmd_codex(rest)
    if cmd == "record":
        return cmd_record(rest)
    if cmd == "effort" and len(rest) == 2:   # _ext.py effort RUN_DIR VIA -> one line for bin/run-external
        print(fmt_effort(effort_seen(os.path.realpath(rest[0]), rest[1])))
        return 0
    if cmd == "planlimit" and len(rest) == 1:   # _ext.py planlimit RUN_DIR -> "hit (try again at …)" or "no"
        t = plan_limit(os.path.realpath(rest[0]))
        print(f"hit (try again at {t})" if t else "no")
        return 0
    if cmd == "upstream-limited" and len(rest) == 2:   # _ext.py upstream-limited LAUNCH_LOG LAUNCH_ERR -> exit 0 if so, else 1
        return 0 if upstream_limited(rest[0], rest[1]) else 1
    if cmd == "hook-registered" and len(rest) == 2:   # _ext.py hook-registered SETTINGS|- HOOK_COMMAND -> exit 0 if so
        try:
            d = json.load(sys.stdin if rest[0] == "-" else open(rest[0]))
        except (OSError, ValueError):
            return 1
        return 0 if hook_registered(d, rest[1]) else 1
    if cmd == "capacity" and len(rest) == 1:   # _ext.py capacity RUN_DIR -> "yes" or "no"
        print("yes" if at_capacity(os.path.realpath(rest[0])) else "no")
        return 0
    if cmd == "queue-stop" and len(rest) == 1:   # _ext.py queue-stop RUN -> exit 0 and why the queue stops, or exit 1
        why = queue_stop(L.resolve_run(rest[0]))
        if why:
            print(why)
        return 0 if why else 1
    if cmd == "models" and len(rest) == 2:   # _ext.py models RUN_DIR MODEL -> "<models> <flag>" for bin/run-external
        rd = os.path.realpath(rest[0])
        flag = L.model_flag(rd, rest[1])
        print(fmt_effort(L.models_seen(rd)[0]), "yes" if flag else "no", flag or "")
        return 0
    if cmd == "codex-probe":   # _ext.py codex-probe RUN_DIR MODEL EFFORT [--network] -> exit 1 and the problems, or 0
        rd = os.path.realpath(rest[0])
        bad = probe(state_dir(rd), rest[1], rest[2], "--network" in rest[3:])
        for b in bad:
            print(f"codex-probe: {b}", file=sys.stderr)
        return 1 if bad else 0
    if cmd == "gateway" and len(rest) == 2:
        return cmd_gateway(rest)
    if cmd == "cli" and rest in (["claude"], ["codex"]):   # _ext.py cli claude|codex -> the CLI kit-env.json names
        print(getattr(E.load(ROOT), rest[0]))
        return 0
    if cmd == "module-check" and rest:   # _ext.py module-check NAME... -> exit 0, or 2 and the problems
        bad = module_check(rest)
        for b in bad:
            print(f"module-check: {b}", file=sys.stderr)
        return 2 if bad else 0
    if cmd == "licence-relay" and len(rest) >= 3:   # _ext.py licence-relay RUN_DIR SOCKFILE NAME... (runs until killed)
        rd, sockfile, names = os.path.realpath(rest[0]), rest[1], rest[2:]
        if module_check(names):
            return 2
        socks = start_licence_relays(rd, E.licence_endpoints(E.load(ROOT), names), os.path.join(state_dir(rd), "licence.log"))
        with open(sockfile + ".tmp", "w") as f:
            f.write(",".join(f"{pt}={p}" for pt, p in socks))
        os.replace(sockfile + ".tmp", sockfile)
        while True:
            time.sleep(3600)
    print(__doc__, file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
