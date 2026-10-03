#!/usr/bin/env python3
"""Tests of the external routes (LESSONS.md "Networked and Codex launches need their flags bound") on the REAL sandboxes, with no model and no internet:

    python3 tests/test_ext.py

- A fake `codex` binary (KIT_CODEX_BIN_DIR) runs inside the real Codex bwrap built by bin/_ext.py and probes it
  from inside: what it can see, the auth copy, the prompt, the ledger shim, and the network. A fake auth file
  (KIT_CODEX_AUTH) stands in for the user's login. A server on this machine's 127.0.0.1 stands in for the web.
- The hook's networked Bash sandbox is run for real, networked and not.
- bin/run-external's refusals and --dry-run are run on a throwaway run under the real tree, removed afterwards,
  with a stub `claude` first on PATH; nothing is approved and nothing launches.
"""
import http.server
import importlib.util
import json
import os
import secrets
import shlex
import shutil
import signal
import socket
import subprocess
import sys
import tempfile
import threading
import time
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import test_gate as G

REAL = G.REAL
EXT = os.path.join(G.BIN, "_ext.py")
PY = "/usr/bin/python3"
# what a fake `codex` answers to the host-side, offline calls every launch makes first (bin/_ext.py codex_host)
HOST_CALLS = ('case "$1 $2" in "debug models") echo \'{"models": []}\'; exit 0;; "debug prompt-input") echo "[]"; exit 0;; '
              '"features list") exit 0;; esac\n')


def local_server():
    """An HTTP server on 127.0.0.1 answering 'hello-from-host'. Returns (server, port)."""
    class H(http.server.BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def do_GET(self):
            b = b"hello-from-host"
            self.send_response(200)
            self.send_header("Content-Length", str(len(b)))
            self.end_headers()
            self.wfile.write(b)
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), H)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, srv.server_address[1]


PROBE = r'''#!/bin/bash
# fake codex: probes its own sandbox, writes findings to the run directory, then exits
case "$1 $2" in   # the host-side, offline calls (bin/_ext.py codex_host): a catalog that offers sub-agents, a clean prompt
  "debug models") echo '{"models": [{"slug": "m", "multi_agent_version": "v2"}]}'; exit 0;;
  "debug prompt-input") [ -f "@BIN@/offer-subagents" ] && echo '[{"text": "use spawn_agent"}]' || echo '[{"text": "ok"}]'; exit 0;;
  "features list") echo "multi_agent                              stable             false"; exit 0;;
esac
mkdir -p "$CODEX_HOME/sessions/2026/09/22"
printf '%s\n' '{"type":"session_meta","payload":{"id":"t-main"}}' '{"type":"turn_context","payload":{"model":"m","effort":"low"}}' > "$CODEX_HOME/sessions/2026/09/22/rollout-x.jsonl"
if [ -f "$KIT_RUN/subagent" ]; then   # a sub-agent's session file, found first by name (canary 015)
  printf '%s\n' '{"type":"session_meta","payload":{"id":"t-sub"}}' '{"type":"turn_context","payload":{"model":"m","effort":"high"}}' > "$CODEX_HOME/sessions/2026/09/22/rollout-a.jsonl"
fi
O="$KIT_RUN/output/probe.txt"
echo '{"type":"thread.started","thread_id":"t-main"}'
{
echo "args: $*"
echo "home-entries: $(ls -A /home 2>/dev/null | wc -l)"
echo "user-home-entries: $(ls -A "@HOME@" 2>/dev/null | wc -l)"
echo "user-home-readable: $([ -r "@HOME@/.codex/auth.json" ] && echo yes || echo no)"
echo "tree-visible: $(ls -A "@REAL@" 2>/dev/null | tr '\n' ' ')"
echo "codex-home: $CODEX_HOME"
echo "auth: $(cat "$CODEX_HOME/auth.json")"
echo "auth-perms: $(stat -c %a "$CODEX_HOME/auth.json")"
echo "rundir-writable: $([ -w "$KIT_RUN" ] && echo yes || echo no)"
echo "lean-mounted: ${KIT_LEAN:-none}"
echo "lean-readonly: $([ -z "$KIT_LEAN" ] && echo n/a || (touch "$KIT_LEAN/x" 2>/dev/null && echo no || echo yes))"
echo "stdin-first-line: $(head -1)"
echo "direct-net: $(curl --noproxy '*' -s -m 3 -o /dev/null -w '%{http_code}' http://127.0.0.1:@PORT@/ 2>/dev/null || echo blocked)"
echo "via-proxy: $(curl -s -m 5 -p -x "$HTTPS_PROXY" -o /dev/null -w '%{http_connect}' http://127.0.0.1:@PORT@/ 2>/dev/null; true)"
echo "proxy-env: ${HTTPS_PROXY:-none}"
echo "gateway-env: ${GATEWAY:-none}"
echo "transcript-visible: $(ls "$KIT_RUN"/launch.jsonl "$KIT_RUN"/launch.err 2>/dev/null | wc -l)"
echo "catalog: $(cat /opt/kit/model-catalog.json 2>/dev/null)"
echo "pidns: $(readlink /proc/self/ns/pid)"
ledger "probe ran" >/dev/null && echo "ledger: ok"
} > "$O" 2>&1
if [ -f "$KIT_RUN/calls" ]; then   # N tool calls, one a tenth of a second
  for i in $(seq "$(cat "$KIT_RUN/calls")"); do
    echo "{\"type\":\"item.started\",\"item\":{\"id\":\"c$i\",\"type\":\"command_execution\"}}"
    echo "{\"type\":\"item.completed\",\"item\":{\"id\":\"m$i\",\"type\":\"agent_message\"}}"
    sleep 0.1
  done
  touch "$KIT_RUN/calls-finished"
fi
[ -n "$PROBE_SLEEP" ] && sleep "$PROBE_SLEEP"
[ -f "$KIT_RUN/sleep" ] && sleep 30
exit 0
'''


class CodexCase(unittest.TestCase):
    def setUp(self):
        self.root, self.rd = G.make_root()
        self.srv, self.port = local_server()
        self.bin = tempfile.mkdtemp(prefix="fake-codex-")
        with open(os.path.join(self.bin, "codex"), "w") as f:
            f.write(PROBE.replace("@PORT@", str(self.port)).replace("@BIN@", self.bin)
                         .replace("@HOME@", os.path.expanduser("~")).replace("@REAL@", REAL))
        os.chmod(os.path.join(self.bin, "codex"), 0o755)
        self.auth = os.path.join(self.bin, "auth.json")
        with open(self.auth, "w") as f:
            f.write('{"fake": "token-for-tests"}')
        with open(os.path.join(self.rd, "HARNESS-NOTE.md"), "w") as f:
            f.write("<!-- harness: codex -->\nnote body\n")
        self.env = dict(os.environ, KIT_ROOT=self.root, KIT_CODEX_BIN_DIR=self.bin, KIT_CODEX_AUTH=self.auth)

    def tearDown(self):
        self.srv.shutdown()
        shutil.rmtree(self.root)
        shutil.rmtree(self.bin)

    def codex(self, *extra, timeout=120):
        return subprocess.run([PY, EXT, "codex", self.rd, "--model", "m", "--effort", "low", *extra],
                              text=True, capture_output=True, env=self.env, timeout=timeout)

    def assertHomeInvisible(self, r, lean=False):
        """Nothing of the user's home is readable inside the sandbox. With no library module linked,
        nothing of the home is visible at all; with one, only the empty parent of its toolchain, and the
        module itself must be read-only — the property a worker must not be able to break."""
        self.assertEqual(r["user-home-readable"], "no")
        if lean:
            self.assertNotEqual(r["lean-mounted"], "none")
            self.assertEqual(r["lean-readonly"], "yes")
        else:
            self.assertEqual(r["home-entries"], "0")
            self.assertEqual(r["user-home-entries"], "0")
            self.assertEqual(r["tree-visible"].split(), [])
            self.assertEqual(r["lean-mounted"], "none")

    def probe(self):
        return dict(l.split(": ", 1) for l in open(os.path.join(self.rd, "output", "probe.txt")).read().splitlines() if ": " in l)


class T5CodexSandbox(CodexCase):
    def test_no_network(self):
        p = self.codex()
        self.assertEqual(p.returncode, 0, p.stderr)
        r = self.probe()
        self.assertHomeInvisible(r)
        self.assertEqual(r["codex-home"], "/opt/codex-home")
        self.assertEqual(r["auth"], '{"fake": "token-for-tests"}')           # the copy is there, from the fd
        self.assertEqual(r["auth-perms"], "600")
        self.assertEqual(r["rundir-writable"], "yes")
        self.assertEqual(r["stdin-first-line"], "<!-- harness: codex -->")  # the prompt starts with the note
        self.assertNotEqual(r["direct-net"], "200")                           # no direct network at all
        self.assertEqual(r["via-proxy"], "403")                               # the proxy refuses a non-allowlisted host
        self.assertEqual(r["gateway-env"], "none")
        self.assertEqual(r["ledger"], "ok")
        self.assertEqual(r["transcript-visible"], "0")                        # the worker cannot see its transcript
        logs = os.path.join(self.root, ".claude", "state", "ext", "900-solve", "logs")
        self.assertTrue(os.path.isfile(os.path.join(logs, "launch.jsonl")))  # written host side, moved in at exit
        for a in ('web_search="disabled"', "--dangerously-bypass-approvals-and-sandbox", "--disable image_generation",
                  "skills.bundled.enabled=false", "analytics.enabled=false", "--ignore-user-config"):
            self.assertIn(a, r["args"])
        self.assertNotIn("--ephemeral", r["args"])                           # the session file is kept, then copied out
        self.assertTrue(os.path.isfile(os.path.join(self.rd, "launch.rollout.jsonl")))
        eff = subprocess.run([PY, EXT, "effort", self.rd, "codex"], text=True, capture_output=True, env=self.env).stdout
        self.assertEqual(eff.strip(), "low*1")
        st = os.path.join(self.root, ".claude", "state", "ext", "900-solve")
        log = open(os.path.join(st, "egress.log")).read()
        self.assertIn(f"REFUSED 127.0.0.1:{self.port}", log)
        self.assertFalse(any("token-for-tests" in open(os.path.join(dp, f), errors="replace").read()
                             for dp, _, fs in os.walk(self.rd) for f in fs if f != "probe.txt"))  # token not left in the run

    def test_network(self):
        with open(os.path.join(self.rd, "HARNESS-NOTE.md"), "w") as f:
            f.write("<!-- harness: codex-net -->\n")
        p = self.codex("--network")
        self.assertEqual(p.returncode, 0, p.stderr)
        r = self.probe()
        self.assertEqual(r["direct-net"], "200")                              # host network shared
        self.assertTrue(r["gateway-env"].startswith("http://127.0.0.1:"))
        self.assertIn('web_search="live"', r["args"])
        self.assertHomeInvisible(r)

    def test_library_linked(self):
        """The other side of the optional module: linked, it is mounted, it is read-only, and the worker's
        toolchain is on PATH. Without this the suite only ever exercises the library-less configuration."""
        lean = os.path.join(self.root, "lean")
        # outside the instance, where a real toolchain lives (~/.elan): bin/_env.py refuses a mount source inside it
        toolchain = os.path.join(tempfile.mkdtemp(prefix="toolchain-"), "toolchain", "bin")
        self.addCleanup(shutil.rmtree, os.path.dirname(os.path.dirname(toolchain)), True)
        os.makedirs(lean, exist_ok=True)
        os.makedirs(toolchain, exist_ok=True)
        open(os.path.join(lean, "Module.lean"), "w").write("-- fixture\n")
        with open(os.path.join(self.root, ".kit-lean"), "w") as f:
            f.write(os.path.dirname(toolchain) + "\n")
        p = self.codex()
        self.assertEqual(p.returncode, 0, p.stderr)
        r = self.probe()
        self.assertHomeInvisible(r, lean=True)
        self.assertEqual(r["lean-mounted"], lean)

    def test_wall_cap(self):
        open(os.path.join(self.rd, "sleep"), "w").close()
        p = self.codex("--wall-hours", "0.001")                               # 3.6 s
        self.assertEqual(p.returncode, 124, p.stderr)
        st = json.load(open(os.path.join(self.root, ".claude", "state", "ext", "900-solve", "codex-exit.json")))
        self.assertTrue(st["timed_out"])
        self.assertTrue(st["main_rollout"])   # stopped at a cap, the session file is still copied (live run 009)

    def test_term_is_an_orderly_stop(self):
        """LESSONS.md "The whole-run CPU budget is enforced": bin/limits-exec stops a run at its CPU cap by TERM to the
        launcher's process; for Codex that is _ext.py, which then stops the worker as at its other caps, so the exit record
        is written and the session file kept (exit 152)."""
        open(os.path.join(self.rd, "sleep"), "w").close()
        q = subprocess.Popen([PY, EXT, "codex", self.rd, "--model", "m", "--effort", "low"], text=True,
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=self.env)
        sd = os.path.join(self.root, ".claude", "state", "ext", "900-solve")
        for _ in range(100):                                                   # the worker is up once it has written
            if os.path.exists(os.path.join(self.rd, "output", "probe.txt")):
                break
            time.sleep(0.2)
        q.send_signal(signal.SIGTERM)
        out, err = q.communicate(timeout=120)
        self.assertEqual(q.returncode, 152, err)
        st = json.load(open(os.path.join(sd, "codex-exit.json")))
        self.assertTrue(st["stopped_by_signal"])
        self.assertTrue(st["main_rollout"])

    def test_own_pid_namespace(self):
        """The script ends whatever the worker left with `kill -KILL -1`, which outside a process namespace would kill every
        process of the user's Unix account (tmux, every session, the user services). Required (the source's review of its port,
        2026-09-30): the worker's sandbox has its own process namespace, seen from inside, and the line is guarded."""
        p = self.codex()
        self.assertEqual(p.returncode, 0, p.stderr)
        inside = self.probe()["pidns"]
        self.assertTrue(inside.startswith("pid:["), inside)
        self.assertNotEqual(inside, os.readlink("/proc/self/ns/pid"))

    def test_kill_all_guard(self):
        """The guard itself: run with `kill` replaced by a function that only prints, on the host it does not fire; in a fresh
        process namespace it does."""
        spec = importlib.util.spec_from_file_location("ext_guard", EXT)
        X = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(X)
        snippet = X.kill_all_in_ns(os.readlink("/proc/self/ns/pid"))
        self.assertIn("kill -KILL -1", snippet)
        shadow = 'kill() { echo "WOULD kill $*"; }\n' + snippet
        host = subprocess.run(["bash", "-c", shadow], text=True, capture_output=True, timeout=30)
        self.assertNotIn("WOULD kill", host.stdout)
        self.assertIn("not in its own process namespace", host.stderr)
        fresh = subprocess.run(["bwrap", "--ro-bind", "/", "/", "--proc", "/proc", "--dev", "/dev", "--unshare-pid",
                                "--die-with-parent", "bash", "-c", shadow], text=True, capture_output=True, timeout=30)
        self.assertIn("WOULD kill -KILL -1", fresh.stdout, fresh.stderr)

    def test_no_subagents(self):
        """LESSONS.md "A Codex worker has no sub-agents": Codex reads the binary's catalog less multi_agent_version, and the
        offline probe refuses a launch whose prompt still offers sub-agents."""
        p = self.codex()
        self.assertEqual(p.returncode, 0, p.stderr)
        r = self.probe()
        self.assertEqual(json.loads(r["catalog"]), {"models": [{"slug": "m"}]})                # the key removed
        self.assertIn('model_catalog_json="/opt/kit/model-catalog.json"', r["args"])
        probe = lambda: subprocess.run([PY, EXT, "codex-probe", self.rd, "m", "low"], text=True, capture_output=True, env=self.env)
        self.assertEqual(probe().returncode, 0, probe().stderr)
        open(os.path.join(self.bin, "offer-subagents"), "w").close()
        q = probe()
        self.assertEqual(q.returncode, 1)
        self.assertIn("the prompt still offers sub-agents ('spawn_agent')", q.stderr)
        open(os.path.join(self.bin, "codex"), "w").write("#!/bin/bash\nexit 3\n")          # no catalog: refused
        self.assertEqual(self.codex().returncode, 2)
        self.assertIn("codex debug models gave no catalog", probe().stderr)

    def test_m1_codex_reads_the_bytes_again(self):
        """P-12 (a medium): with --approval, the Codex launcher re-reads the run's bytes against the used approval just
        before the worker starts, and refuses when there is none with that digest."""
        p = self.codex("--approval", "0" * 64)
        self.assertEqual(p.returncode, 3, p.stderr)
        self.assertIn("no used approval", p.stderr)
        self.assertFalse(os.path.exists(os.path.join(self.rd, "output", "probe.txt")))

    def test_rollouts(self):
        """The main thread's session file is the one whose id is the transcript's thread id; a sub-agent's is kept apart
        (the proof instance's canary 015 recorded the sub-agent's)."""
        open(os.path.join(self.rd, "subagent"), "w").close()
        p = self.codex()
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn("1 session file(s) besides the main thread's", p.stderr)
        self.assertIn('"id":"t-main"', open(os.path.join(self.rd, "launch.rollout.jsonl")).read())
        self.assertIn('"id":"t-sub"', open(os.path.join(self.rd, "launch.rollout.sub-1.jsonl")).read())
        self.assertFalse(os.path.exists(os.path.join(self.rd, "launch.rollouts")))
        st = json.load(open(os.path.join(self.root, ".claude", "state", "ext", "900-solve", "codex-exit.json")))
        self.assertEqual((st["main_rollout"], st["sub_rollouts"]), (True, 1))

    def test_tool_call_cap(self):
        """LESSONS.md "A Codex worker's tool calls are capped": past --max-turns tool calls the worker is stopped (exit 125);
        messages do not count."""
        open(os.path.join(self.rd, "calls"), "w").write("30")
        p = self.codex("--max-turns", "3")
        self.assertEqual(p.returncode, 125, p.stderr)
        self.assertIn("tool-call cap of 3 reached", p.stderr)
        st = json.load(open(os.path.join(self.root, ".claude", "state", "ext", "900-solve", "codex-exit.json")))
        self.assertEqual((st["turn_cap_hit"], st["tool_calls"], st["max_turns"]), (True, 4, 3))
        self.assertTrue(st["main_rollout"])   # stopped at a cap, the session file is still copied (live run 009)
        self.assertFalse(os.path.exists(os.path.join(self.rd, "calls-finished")))
        for f in os.listdir(self.rd):   # a run directory is launched once; clear this one for the second launch
            if f.startswith("launch") or f == "calls-finished":
                os.remove(os.path.join(self.rd, f))
        open(os.path.join(self.rd, "calls"), "w").write("3")
        p = self.codex("--max-turns", "3")
        self.assertEqual(p.returncode, 0, p.stderr)
        st = json.load(open(os.path.join(self.root, ".claude", "state", "ext", "900-solve", "codex-exit.json")))
        self.assertEqual((st["turn_cap_hit"], st["tool_calls"]), (False, 3))

    def test_record(self):
        self.assertEqual(self.codex().returncode, 0)
        os.makedirs(os.path.join(self.rd, "downloads"))
        open(os.path.join(self.rd, "downloads", "paper.pdf"), "w").write("pdf")
        open(os.path.join(self.rd, "launch.jsonl"), "w").write(
            json.dumps({"type": "item.completed", "item": {"type": "command_execution"}}) + "\n"
            + json.dumps({"type": "turn.completed", "usage": {"input_tokens": 5}}) + "\n")
        open(os.path.join(self.rd, ".ledger-outbox"), "w").write("a worker note\n")
        p = subprocess.run([PY, EXT, "record", self.rd, "--via", "codex", "--model", "m", "--exit", "0"],
                           text=True, capture_output=True, env=self.env)
        self.assertEqual(p.returncode, 0, p.stderr)
        rec = open(os.path.join(self.rd, "RECORD-EXT.md")).read()
        for needle in ("downloads/paper.pdf", "launch.jsonl", "egress.log", "1 refused", "command_execution",
                       "token exposure", "moved to the ledger: 1", "effort the model's requests carried: low*1",
                       "models that answered: m*1", "tool calls: 0 of a cap of 300",
                       "session files: the main thread's copied; 0 other"):
            self.assertIn(needle, rec)
        self.assertNotIn("NOT ONE MODEL", rec)
        led = open(os.path.join(self.root, "LEDGER.log")).read()
        self.assertIn("| codex-worker | 900-solve | NOTE | a worker note", led)
        self.assertIn("RECORD-EXT", led)


class T5EgressProxy(unittest.TestCase):
    """The allowlist itself, in process: allowed hosts tunnel, others get 403, non-CONNECT gets 405."""

    def test_allowlist(self):
        spec = importlib.util.spec_from_file_location("ext", EXT)
        X = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(X)
        d = tempfile.mkdtemp()
        srv, port = local_server()
        try:
            sock, logf = os.path.join(d, "s"), os.path.join(d, "log")
            X.start_egress_proxy(sock, logf, allow=("localhost",))

            def ask(req):
                c = socket.socket(socket.AF_UNIX)
                c.connect(sock)
                c.sendall(req)
                data = b""
                while b"\r\n\r\n" not in data:
                    chunk = c.recv(4096)
                    if not chunk:
                        break
                    data += chunk
                return c, data
            c, head = ask(f"CONNECT localhost:{port} HTTP/1.1\r\nHost: x\r\n\r\n".encode())
            self.assertIn(b" 200 ", head)
            c.sendall(b"GET / HTTP/1.0\r\n\r\n")
            body = b""
            while True:
                chunk = c.recv(4096)
                if not chunk:
                    break
                body += chunk
            self.assertIn(b"hello-from-host", body)
            self.assertIn(b" 403 ", ask(b"CONNECT evil.localhost.example:443 HTTP/1.1\r\n\r\n")[1])
            self.assertIn(b" 403 ", ask(b"CONNECT notlocalhost:443 HTTP/1.1\r\n\r\n")[1])
            self.assertIn(b" 405 ", ask(b"GET http://localhost/ HTTP/1.1\r\n\r\n")[1])
            self.assertIn(b" 403 ", ask(f"CONNECT sub.localhost:{port} HTTP/1.1\r\n\r\n".encode())[1])  # exact names only
            self.assertEqual(X.EGRESS_ALLOW, ("chatgpt.com", "api.openai.com", "auth.openai.com"))
        finally:
            srv.shutdown()
            shutil.rmtree(d)


class T5HookNetSandbox(unittest.TestCase):
    """The hook's Bash sandbox, run for real: shares the network only when asked."""

    def test_share_net(self):
        spec = importlib.util.spec_from_file_location("hook", os.path.join(REAL, ".claude", "hooks", "sandbox.py"))
        H = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(H)
        rd = tempfile.mkdtemp()
        srv, port = local_server()
        try:
            probe = f"curl -s -m 3 http://127.0.0.1:{port}/ || echo blocked"
            out = lambda net: subprocess.run(H.bwrap_command(rd, probe, net=net), shell=True, text=True,
                                             capture_output=True, timeout=60).stdout.strip()
            self.assertEqual(out(False), "blocked")
            self.assertEqual(out(True), "hello-from-host")
        finally:
            srv.shutdown()
            shutil.rmtree(rd)


class T5SageModule(unittest.TestCase):
    """LESSONS.md "Computer algebra is an optional module, and its results need a certificate": a SageMath environment
    named in <root>/.kit-sage is mounted read-only for workers on both routes, with the shim at /opt/kit/bin/sage and
    python3 still /usr/bin/python3; without .kit-sage nothing is mounted. A fake environment (bin/sage prints a marker)
    tests the mechanism anywhere; the real environment, when this machine has one, is run too."""

    ROOT_LINE = 'ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))'

    def setUp(self):
        self.root, self.rd = G.make_root()
        shutil.copytree(os.path.join(REAL, ".claude", "sandbox"), os.path.join(self.root, ".claude", "sandbox"))
        os.symlink(os.path.join(REAL, "bin"), os.path.join(self.root, "bin"))   # bin/_env.py reads the module files
        self.env = tempfile.mkdtemp(prefix="fake-sage-env-")
        os.makedirs(os.path.join(self.env, "bin"))
        with open(os.path.join(self.env, "bin", "sage"), "w") as f:
            f.write('#!/bin/sh\necho "fake-sage $*"\n')
        os.chmod(os.path.join(self.env, "bin", "sage"), 0o755)

    def tearDown(self):
        shutil.rmtree(self.root)
        shutil.rmtree(self.env)

    def hook(self):
        src = open(os.environ.get("HOOK_UNDER_TEST", os.path.join(REAL, ".claude", "hooks", "sandbox.py"))).read()
        assert src.count(self.ROOT_LINE) == 1
        path = os.path.join(self.root, ".claude", "hook_sage.py")
        open(path, "w").write(src.replace(self.ROOT_LINE, f"ROOT = {self.root!r}"))
        spec = importlib.util.spec_from_file_location("hook_sage", path)
        H = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(H)
        return H

    def link(self, env):
        with open(os.path.join(self.root, ".kit-sage"), "w") as f:
            f.write(env + "\n")

    def probe(self, H, extra=""):
        cmd = ("command -v sage; command -v python3; sage -c hi; echo \"env=${KIT_SAGE:-none}\"; "
               f"(echo x > \"${{KIT_SAGE:-/nonexistent}}/escape.txt\") 2>/dev/null && echo env-writable || echo env-read-only{extra}")
        return subprocess.run(H.bwrap_command(self.rd, cmd), shell=True, text=True, capture_output=True, timeout=300).stdout

    def test_not_linked_nothing_mounted(self):
        H = self.hook()
        cmd = H.bwrap_command(self.rd, "true")
        self.assertNotIn("/opt/kit/bin/sage", cmd)
        self.assertNotIn("KIT_SAGE", cmd)

    def test_linked_fake_env(self):
        self.link(self.env)
        H = self.hook()
        cmd = H.bwrap_command(self.rd, "true")
        self.assertEqual(cmd.count(f"--ro-bind {self.env} {self.env}"), 1)
        self.assertEqual(cmd.count("/opt/kit/bin/sage"), 1)
        out = self.probe(H).split("\n")
        self.assertEqual(out[:5], ["/opt/kit/bin/sage", "/usr/bin/python3", "fake-sage -c hi", f"env={self.env}", "env-read-only"])
        self.assertFalse(os.path.exists(os.path.join(self.env, "escape.txt")))

    def test_declared_env_without_sage_not_mounted(self):
        os.remove(os.path.join(self.env, "bin", "sage"))
        self.link(self.env)
        self.assertNotIn("/opt/kit/bin/sage", self.hook().bwrap_command(self.rd, "true"))
        p = G.tool(self.root, "verify-data")
        self.assertIn("the computer-algebra module is missing", p.stdout)

    def test_real_sage(self):
        real = os.path.expanduser("~/miniforge3/envs/sage")
        if not os.path.isfile(os.path.join(real, "bin", "sage")):
            self.skipTest("no SageMath environment on this machine")
        self.link(real)
        H = self.hook()
        cmd = ("command -v sage; command -v python3; sage -c 'print(factor(2^32+1))'; "
               f"(echo x > {real}/escape.txt) 2>/dev/null && echo env-writable || echo env-read-only")
        out = subprocess.run(H.bwrap_command(self.rd, cmd), shell=True, text=True, capture_output=True, timeout=300).stdout.split()
        self.assertEqual(out, ["/opt/kit/bin/sage", "/usr/bin/python3", "641", "*", "6700417", "env-read-only"])

    def test_codex_route(self):
        """The Codex sandbox (bin/_ext.py) gets the same mount from the same file: a fake `codex` runs the probe inside it."""
        self.link(self.env)
        bindir = tempfile.mkdtemp(prefix="fake-codex-")
        try:
            with open(os.path.join(bindir, "codex"), "w") as f:
                f.write("#!/bin/bash\n" + HOST_CALLS + "{ command -v sage; command -v python3; sage -c hi; echo \"env=$KIT_SAGE\"; } "
                        '> "$KIT_RUN/output/sage.txt" 2>&1\nexit 0\n')
            os.chmod(os.path.join(bindir, "codex"), 0o755)
            auth = os.path.join(bindir, "auth.json")
            open(auth, "w").write('{"fake": "token-for-tests"}')
            open(os.path.join(self.rd, "HARNESS-NOTE.md"), "w").write("<!-- harness: codex -->\n")
            env = dict(os.environ, KIT_ROOT=self.root, KIT_CODEX_BIN_DIR=bindir, KIT_CODEX_AUTH=auth)
            p = subprocess.run([PY, EXT, "codex", self.rd, "--model", "m", "--effort", "low"], text=True, capture_output=True,
                               env=env, timeout=300)
            self.assertEqual(p.returncode, 0, p.stderr)
            self.assertEqual(open(os.path.join(self.rd, "output", "sage.txt")).read().split("\n")[:4],
                             ["/opt/kit/bin/sage", "/usr/bin/python3", "fake-sage -c hi", f"env={self.env}"])
        finally:
            shutil.rmtree(bindir)


class T5CommandsApartFromCodex(unittest.TestCase):
    """LESSONS.md "A Codex worker's commands run apart from Codex": a command started through the sandbox user's shell
    ($SHELL, and the login shell in /etc/passwd) runs in its own sandbox: it cannot see or write any descriptor of the
    Codex process (the transcript, the prompt), cannot read Codex's home (the token, the session log), and on a run
    without the network cannot reach the egress proxy; the run directory and /tmp stay writable. The transcript reaches
    the host through a pipe, with a hash chain the record checks."""

    ATTACK = r"""
out="$KIT_RUN/output/attack.txt"; : > "$out"
w=0; for f in /proc/[0-9]*/fd/*; do (printf 'FORGED\n' >> "$f") 2>/dev/null && w=$((w+1)); done
echo "fd-writes-outside-self: $w" >> "$out"
echo "pids: $(ls /proc | grep -cE '^[0-9]+$')" >> "$out"
[ -r /opt/codex-home/auth.json ] && echo "token: readable" >> "$out" || echo "token: hidden" >> "$out"
python3 -c "import socket,sys; s=socket.socket(); s.settimeout(2); s.connect(('127.0.0.1', int(sys.argv[1]))); print('proxy: reachable')" "$PORT" >> "$out" 2>/dev/null || echo "proxy: unreachable" >> "$out"
python3 -c "import socket; s=socket.socket(socket.AF_UNIX); s.settimeout(2); s.connect('/opt/kit/egress.sock'); print('proxy-socket: reachable')" >> "$out" 2>/dev/null || echo "proxy-socket: unreachable" >> "$out"
v=0; for d in "/run/user/$HOSTUID/kit-egress" "/tmp/kit-egress-$HOSTUID" "$(dirname "$HOSTSOCK")"; do [ -e "$d" ] && v=$((v+1)); done
echo "host-socket-dirs-visible: $v" >> "$out"
python3 -c "import socket,sys; s=socket.socket(socket.AF_UNIX); s.settimeout(2); s.connect(sys.argv[1]); print('host-socket: reachable')" "$HOSTSOCK" >> "$out" 2>/dev/null || echo "host-socket: unreachable" >> "$out"
echo ok > "$KIT_RUN/scratch/inner.txt" && echo "rundir: writable" >> "$out"
echo ok > /tmp/inner.txt && echo "tmp: writable" >> "$out"
echo "nested-bash: $(bash -c 'echo "$KIT_CMD_SANDBOXED/$(ls /proc | grep -cE "^[0-9]+$")"')" >> "$out"
(echo x > /opt/kit/x) 2>/dev/null && echo "opt: writable" >> "$out" || echo "opt: read-only" >> "$out"
"""

    def test_commands_run_apart(self):
        sys.path.insert(0, G.BIN)
        spec = importlib.util.spec_from_file_location("ext_apart", EXT)
        X = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(X)
        root, rd = G.make_root()
        os.makedirs(os.path.join(rd, "scratch"), exist_ok=True)
        bindir = tempfile.mkdtemp(prefix="fake-codex-")
        try:
            with open(os.path.join(bindir, "codex"), "w") as f:
                f.write("#!/bin/bash\n" + HOST_CALLS +
                        'echo \'{"type":"honest","n":1}\'\n'
                        'echo "shell: $SHELL login: $(getent passwd worker | cut -d: -f7) path: $(command -v bash)" >&2\n'
                        # like Codex 0.155 (canary 006): `bash` from PATH, -lc, output captured through its own pipes
                        # LESSONS.md "The egress socket's host side is in a short private directory": where it now is
                        f'PORT={X.EGRESS_PORT} HOSTUID={os.getuid()} HOSTSOCK={shlex.quote(X.egress_sock_path(rd))} '
                        f'"$(command -v bash)" -lc {shlex.quote(self.ATTACK)} < /dev/null > /tmp/cmd.out 2>&1\n'
                        "printf '{\"type\":\"injected\"}\\n' > /proc/self/fd/1\n"   # the Codex process itself: a residual
                        'echo \'{"type":"honest","n":2}\'\n'
                        "exit 0\n")
            os.chmod(os.path.join(bindir, "codex"), 0o755)
            auth = os.path.join(bindir, "auth.json")
            open(auth, "w").write('{"fake": "token-for-tests"}')
            open(os.path.join(rd, "HARNESS-NOTE.md"), "w").write("<!-- harness: codex -->\n")
            env = dict(os.environ, KIT_ROOT=root, KIT_CODEX_BIN_DIR=bindir, KIT_CODEX_AUTH=auth)
            p = subprocess.run([PY, EXT, "codex", rd, "--model", "m", "--effort", "low"], text=True, capture_output=True,
                               env=env, timeout=300)
            self.assertEqual(p.returncode, 0, p.stderr)
            sd = os.path.join(root, ".claude", "state", "ext", "900-solve")
            log = open(os.path.join(sd, "logs", "launch.jsonl")).read()
            err = open(os.path.join(sd, "logs", "launch.err")).read()
            self.assertIn("shell: /opt/kit/bin/bash login: /opt/kit/bin/bash path: /opt/kit/bin/bash", err)
            self.assertTrue(log.startswith('{"type":"honest","n":1}\n'), log)         # nothing truncated or rewritten
            self.assertIn('{"type":"honest","n":2}', log)
            self.assertNotIn("FORGED", log + err)                                      # no command reached a Codex descriptor
            r = dict(l.split(": ", 1) for l in open(os.path.join(rd, "output", "attack.txt")).read().splitlines())
            self.assertEqual(r["token"], "hidden")
            self.assertEqual(r["proxy"], "unreachable")
            self.assertEqual(r["proxy-socket"], "unreachable")                        # the proxy's socket too (ud, 2026-09-26)
            self.assertEqual(r["host-socket-dirs-visible"], "0")                      # its host side is neither seen ...
            self.assertEqual(r["host-socket"], "unreachable")                          # ... nor reached
            self.assertEqual((r["rundir"], r["tmp"], r["opt"]), ("writable", "writable", "read-only"))
            self.assertLess(int(r["pids"]), 6)                                         # only the command's own processes
            sb, n = r["nested-bash"].split("/")
            self.assertEqual(sb, "1")                                                 # a bash inside is the real one ...
            self.assertLess(int(n), 8)                                                 # ... in the same inner namespace
            chain = json.load(open(os.path.join(sd, "codex-exit.json")))["transcript_chain"]["launch.jsonl"]
            shutil.copy(os.path.join(sd, "logs", "launch.jsonl"), os.path.join(rd, "launch.jsonl"))
            self.assertEqual(X.chain_of(os.path.join(rd, "launch.jsonl")), (chain["lines"], chain["sha256"]))
            self.assertIn("matches", X.chain_line(rd, {"transcript_chain": {"launch.jsonl": chain}}))
            open(os.path.join(rd, "launch.jsonl"), "a").write("tampered afterwards\n")
            self.assertIn("DOES NOT MATCH", X.chain_line(rd, {"transcript_chain": {"launch.jsonl": chain}}))
        finally:
            shutil.rmtree(root)
            shutil.rmtree(bindir)


class T5EgressSocketPlace(CodexCase):
    """LESSONS.md "The egress socket's host side is in a short private directory" (the source's method change 60): the host
    side of the no-network egress proxy's socket was .claude/state/ext/RUN/egress.sock, which passes Linux's 107-byte limit
    for a long enough root and slug (the source's run 281 died at bind, after its approval was spent). It is now in
    $XDG_RUNTIME_DIR/kit-egress/, or /tmp/kit-egress-<uid>/ when XDG_RUNTIME_DIR is unset (a detached process may lack it).
    Inside the sandbox neither directory is visible or connectable, at the Codex level or at the command level, for both;
    the bound socket stays reachable for Codex and unreachable for its commands."""

    PLACE = r'''
O="$KIT_RUN/output/place.txt"
probe() {   # $1 label; the host directories and host socket path baked in at test time
  for d in @DIRS@; do [ -e "$d" ] && echo "$1-hostdir: visible $d" || echo "$1-hostdir: invisible"; done
  python3 -c "import socket,sys; s=socket.socket(socket.AF_UNIX); s.settimeout(2); s.connect(sys.argv[1]); print('$1-hostsock: reachable')" "@SOCK@" 2>/dev/null || echo "$1-hostsock: unreachable"
  python3 -c "import socket; s=socket.socket(socket.AF_UNIX); s.settimeout(2); s.connect('/opt/kit/egress.sock'); print('$1-boundsock: reachable')" 2>/dev/null || echo "$1-boundsock: unreachable"
}
{
probe codex
echo "via-proxy: $(curl -s -m 5 -p -x "$HTTPS_PROXY" -o /dev/null -w '%{http_connect}' http://127.0.0.1:9/ 2>/dev/null; true)"
"$(command -v bash)" -lc "$(declare -f probe); probe cmd" < /dev/null
} > "$O" 2>&1
exit 0
'''

    def ext(self):
        spec = importlib.util.spec_from_file_location("ext_place", EXT)
        X = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(X)
        return X

    def run_place(self, xdg):
        env = dict(self.env)
        env.pop("XDG_RUNTIME_DIR", None)
        saved = os.environ.pop("XDG_RUNTIME_DIR", None)
        if xdg:
            env["XDG_RUNTIME_DIR"] = os.environ["XDG_RUNTIME_DIR"] = xdg
        try:
            sock = self.ext().egress_sock_path(os.path.realpath(self.rd))
        finally:
            os.environ.pop("XDG_RUNTIME_DIR", None)
            if saved is not None:
                os.environ["XDG_RUNTIME_DIR"] = saved
        dirs = [f"/run/user/{os.getuid()}/kit-egress", f"/tmp/kit-egress-{os.getuid()}", os.path.dirname(sock)]
        with open(os.path.join(self.bin, "codex"), "w") as f:
            f.write("#!/bin/bash\n" + HOST_CALLS +
                    self.PLACE.replace("@DIRS@", " ".join(shlex.quote(d) for d in dirs)).replace("@SOCK@", sock))
        p = subprocess.run([PY, EXT, "codex", self.rd, "--model", "m", "--effort", "low"], text=True,
                           capture_output=True, env=env, timeout=120)
        self.assertEqual(p.returncode, 0, p.stderr)
        return sock, open(os.path.join(self.rd, "output", "place.txt")).read()

    def check(self, sock, r, base):
        self.assertTrue(sock.startswith(base + "/"), sock)
        self.assertLessEqual(len(sock.encode()), 107)
        for lvl in ("codex", "cmd"):
            self.assertNotIn(f"{lvl}-hostdir: visible", r)
            self.assertEqual(r.count(f"{lvl}-hostdir: invisible"), 3, r)
            self.assertIn(f"{lvl}-hostsock: unreachable", r)
        self.assertIn("codex-boundsock: reachable", r)                  # Codex reaches the proxy ...
        self.assertIn("via-proxy: 403", r)                               # ... which still refuses a host not on its list
        self.assertIn("cmd-boundsock: unreachable", r)                   # its commands do not
        st = os.stat(base)
        self.assertEqual((st.st_uid, st.st_mode & 0o777), (os.getuid(), 0o700))
        self.assertFalse(os.path.exists(sock))                           # removed at exit

    def test_xdg_runtime_dir(self):
        xdg = f"/run/user/{os.getuid()}"
        if not os.path.isdir(xdg):
            self.skipTest("no XDG runtime directory on this machine")
        sock, r = self.run_place(xdg)
        self.check(sock, r, os.path.join(xdg, "kit-egress"))

    def test_fallback_without_xdg(self):
        sock, r = self.run_place(None)
        self.check(sock, r, f"/tmp/kit-egress-{os.getuid()}")

    def test_long_slug(self):
        """The source's run 281: a run directory whose state path would put the socket past 107 bytes now launches."""
        long_rd = os.path.join(os.path.dirname(self.rd), "900-" + "a-very-long-slug-" * 6)
        os.rename(self.rd, long_rd)
        self.rd = long_rd
        self.assertGreater(len(os.path.join(self.root, ".claude", "state", "ext", os.path.basename(long_rd), "egress.sock")), 107)
        p = self.codex()
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertEqual(self.probe()["via-proxy"], "403")

    def test_record_of_a_run_that_never_started(self):
        X = self.ext()
        self.assertIn("the worker never started", X.chain_line(self.rd, {}))
        self.assertIn("before kit-v0.3.1", X.chain_line(self.rd, {"exit": 0, "wall_seconds": 1}))


class T5CpuCap(unittest.TestCase):
    """LESSONS.md "The whole-run CPU budget is enforced" (the source's run 346: 11.13 CPU-hours against a budget of 8, only
    flagged): bin/limits-exec watches the run's cgroup and, at the cap, sends TERM to the launcher's process, then after the
    run's grace period kills whatever is left in the scope, background jobs included; exit 152 (128 + SIGXCPU) and
    cpu_cap_hit in usage.json. Real systemd scope, real processes."""

    def setUp(self):
        if subprocess.run(["systemd-run", "--user", "--scope", "--quiet", "--", "true"], capture_output=True).returncode != 0:
            self.skipTest("no systemd user scope here")
        self.mark = "cpucap" + secrets.token_hex(6)   # made at run time: no shell's command line carries it
        self.root, self.rd = G.make_root()
        json.dump({"cpu_hours": 0.0008, "threads": 1, "mem_gb": 1, "cpu_grace_seconds": 2},   # 2.9 CPU-seconds
                  open(os.path.join(self.rd, ".limits"), "w"))

    def tearDown(self):
        subprocess.run(["pkill", "-KILL", "-f", self.mark], capture_output=True)
        shutil.rmtree(self.root)

    def burn(self, ignore_term=False):
        return ("import signal\nsignal.signal(signal.SIGTERM, signal.SIG_IGN)\n" if ignore_term else "") + \
               f"x = 0\nwhile True:\n    x += 1  # {self.mark}"

    def run_limited(self, *cmd):
        t = time.time()
        p = subprocess.run([os.path.join(G.BIN, "limits-exec"), self.rd, "--", *cmd], text=True, capture_output=True,
                           timeout=60)
        return p, time.time() - t, json.load(open(os.path.join(self.rd, "usage.json")))

    def test_stopped_at_the_cap(self):
        p, wall, u = self.run_limited(PY, "-c", self.burn())
        self.assertEqual(p.returncode, 152, p.stdout + p.stderr)
        self.assertTrue(u["cpu_cap_hit"])
        self.assertLess(wall, 30)
        self.assertLess(u["cpu_seconds"], 15)

    def test_a_background_job_that_ignores_term(self):
        p, wall, u = self.run_limited("bash", "-c", f"{PY} -c {shlex.quote(self.burn(ignore_term=True))} & wait")
        self.assertEqual(p.returncode, 152, p.stdout + p.stderr)
        self.assertTrue(u["cpu_cap_hit"])
        self.assertLess(wall, 40)
        self.assertEqual(subprocess.run(["pgrep", "-f", self.mark], capture_output=True).stdout, b"")       # none left

    def test_under_the_cap(self):
        p, wall, u = self.run_limited("true")
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        self.assertFalse(u["cpu_cap_hit"])



class T5NoUserManager(unittest.TestCase):
    """Pending item P-3, B3 (user 2026-10-01: "B1-6: yes to all"): RULES.md says limits are enforced, not promised, but with
    no systemd user manager bin/limits-exec ran the command anyway (enforced=false). It now refuses and runs nothing, and
    bin/run-external asks it (--probe) before the approval is touched. A fake systemd-run that fails stands in for a host
    without a user manager."""

    def setUp(self):
        self.root, self.rd = G.make_root()
        self.fake = os.path.join(self.root, "fakebin")
        os.makedirs(self.fake)
        open(os.path.join(self.fake, "systemd-run"), "w").write("#!/bin/sh\nexit 1\n")
        os.chmod(os.path.join(self.fake, "systemd-run"), 0o755)
        self.env = dict(os.environ, PATH=self.fake + ":" + os.environ.get("PATH", ""))

    def tearDown(self):
        shutil.rmtree(self.root)

    def test_refused_and_nothing_runs(self):
        mark = os.path.join(self.rd, "ran")
        p = subprocess.run([os.path.join(G.BIN, "limits-exec"), self.rd, "--", "touch", mark], text=True,
                           capture_output=True, env=self.env)
        self.assertNotEqual(p.returncode, 0, p.stdout)
        self.assertIn("cannot be enforced", p.stderr)
        self.assertFalse(os.path.exists(mark))
        q = subprocess.run([os.path.join(G.BIN, "limits-exec"), "--probe"], text=True, capture_output=True, env=self.env)
        self.assertNotEqual(q.returncode, 0)

    def test_run_external_asks_before_the_approval(self):
        src = open(os.path.join(G.BIN, "run-external")).read()
        pre = src[src.index("preflight() {"):src.index("\n}\n", src.index("preflight() {"))]
        self.assertIn('limits-exec" --probe', pre)

class T5QueueStop(unittest.TestCase):
    """LESSONS.md "A queue stops at the plan's usage limit" (the source's runs 316-319, 2026-09-30): each queued Codex run ended
    in 2-3 s on the ChatGPT plan's usage limit, and the queue went on releasing the next, so every run was left holding a launch
    record (a run directory is launched once). The queue now stops at a run that ended on the usage limit or on the provider's
    capacity refusal; the runs after it are not released, keep no launch record, and can go on a new approval. The real queue
    loop of bin/run-external runs here in a throwaway instance (a copy of bin/ and a ledger); no run launches."""

    LIMIT = {"type": "turn.failed", "error": {"message": "You've hit your usage limit. Upgrade or try again at 2:15 AM."}}
    CAPACITY = {"type": "error", "message": "Selected model is at capacity. Please try a different model."}
    OTHER = {"type": "turn.failed", "error": {"message": "stream disconnected before completion"}}

    def setUp(self):
        self.root = os.path.realpath(tempfile.mkdtemp(prefix="queue-fixture-"))
        shutil.copytree(G.BIN, os.path.join(self.root, "bin"))
        open(os.path.join(self.root, "LEDGER.log"), "w").close()
        for r in ("901-qa", "902-qb"):
            os.makedirs(os.path.join(self.root, "workspace-1", "runs", r))
            open(os.path.join(self.root, "workspace-1", "runs", r, "BRIEF.md"), "w").write("brief\n")

    def tearDown(self):
        shutil.rmtree(self.root)

    def first_ended(self, event):
        open(os.path.join(self.root, "workspace-1", "runs", "901-qa", "launch.jsonl"), "w").write(json.dumps(event) + "\n")

    def helper(self):
        env = {k: v for k, v in os.environ.items() if k != "KIT_ROOT"}
        return subprocess.run([PY, os.path.join(self.root, "bin", "_ext.py"), "queue-stop", "901-qa"],
                              text=True, capture_output=True, env=env, timeout=30)

    def queue(self):
        env = {k: v for k, v in os.environ.items() if k != "KIT_ROOT"}
        subprocess.run([os.path.join(self.root, "bin", "run-external"), "--queue-run", "0123456789abcdef", "901-qa", "902-qb",
                        "--", "--via", "codex", "--model", "m"], text=True, capture_output=True, env=env, timeout=120)
        return open(os.path.join(self.root, "LEDGER.log")).read()

    def test_helper(self):
        for event, stops in ((self.LIMIT, True), (self.CAPACITY, True), (self.OTHER, False)):
            with self.subTest(event=event):
                self.first_ended(event)
                p = self.helper()
                self.assertEqual(p.returncode, 0 if stops else 1, p.stdout + p.stderr)
                if stops:
                    self.assertIn("usage limit" if event is self.LIMIT else "capacity", p.stdout)
        os.remove(os.path.join(self.root, "workspace-1", "runs", "901-qa", "launch.jsonl"))
        self.assertEqual(self.helper().returncode, 1)                                 # never launched: go on

    def test_queue_stops_at_the_usage_limit(self):
        self.first_ended(self.LIMIT)
        led = self.queue()
        self.assertIn("901-qa", led)
        self.assertIn("QUEUE-STOP", led)
        self.assertNotIn("| 902-qb | QUEUE-RUN", led)                                 # never released ...
        self.assertIn("not released: 902-qb", led)                                   # ... and named on the stop line
        self.assertEqual(sorted(os.listdir(os.path.join(self.root, "workspace-1", "runs", "902-qb"))), ["BRIEF.md"])

    def test_queue_goes_on_after_another_failure(self):
        self.first_ended(self.OTHER)
        led = self.queue()
        self.assertNotIn("QUEUE-STOP", led)
        self.assertIn("902-qb", led)                                                  # a failed run does not stop the queue


PARENT_PROBE = r'''
T=@TAG@
w() { if (echo x > "$1") 2>/dev/null; then echo "$2: writable"; else echo "$2: read-only"; fi; }
w "$KIT_RUN/ok-$T" rundir
w /tmp/ok-$T tmp
w "$KIT_RUN/../escape-$T" parent
w "$KIT_RUN/../../escape-$T" grandparent
w /home/escape-$T home
w @HOME@/escape-$T user-home
w /opt/escape-$T opt
w /escape-$T root
if mkdir "$KIT_RUN/../newdir-$T" 2>/dev/null; then echo "mkdir-parent: writable"; else echo "mkdir-parent: read-only"; fi
[ -n "$CODEX_HOME" ] && w "$CODEX_HOME/ok-$T" codex-home
true
'''


class T5ParentChainReadOnly(unittest.TestCase):
    """LESSONS.md "The sandbox's root is remounted read-only after the binds": inside both worker sandboxes the directories bwrap makes
    for mount points (the run dir's parent chain, /home, /opt, /) are read-only; the run dir, /tmp and CODEX_HOME are
    writable. The run is a throwaway under the REAL tree, because a fixture under /tmp sits inside the sandbox's own
    /tmp tmpfs and would not show the parent chain. Nothing may reach the host."""

    TAG = "parent-chain-probe"

    def setUp(self):
        if os.path.realpath(REAL).startswith("/tmp/"):
            # the sandbox's own /tmp is a tmpfs of its own, which the root's read-only remount does not reach: a tree
            # under /tmp keeps its parent chain writable inside the sandbox (writes still reach nothing on the host)
            self.skipTest("this tree lies under /tmp, inside the sandbox's own /tmp tmpfs")
        self.runs = os.path.join(REAL, "workspace-1", "runs")
        self.rd = os.path.join(self.runs, "999-parent-chain-fixture")
        for d in ("input", "output", "scratch"):
            os.makedirs(os.path.join(self.rd, d))
        open(os.path.join(self.rd, "BRIEF.md"), "w").write("brief\n")
        open(os.path.join(self.rd, ".limits"), "w").write('{"cpu_hours": 1, "threads": 1, "mem_gb": 1}\n')
        self.probe = PARENT_PROBE.replace("@TAG@", self.TAG).replace("@HOME@", os.path.expanduser("~"))
        self.escapes = [os.path.join(self.runs, f"escape-{self.TAG}"), os.path.join(REAL, "workspace-1", f"escape-{self.TAG}"),
                        os.path.join(self.runs, f"newdir-{self.TAG}"), f"/home/escape-{self.TAG}",
                        os.path.join(os.path.expanduser("~"), f"escape-{self.TAG}"), f"/opt/escape-{self.TAG}", f"/escape-{self.TAG}"]
        self.assertFalse([p for p in self.escapes if os.path.lexists(p)], "leftover from an earlier run")

    def tearDown(self):
        leaked = [p for p in self.escapes if os.path.lexists(p)]
        shutil.rmtree(self.rd)
        shutil.rmtree(os.path.join(REAL, ".claude", "state", "ext", "999-parent-chain-fixture"), ignore_errors=True)
        self.assertEqual(leaked, [], "a sandbox write reached the host")

    def check(self, text, codex=False):
        r = dict(l.split(": ", 1) for l in text.splitlines() if ": " in l)
        want = {"rundir": "writable", "tmp": "writable", "parent": "read-only", "grandparent": "read-only",
                "home": "read-only", "user-home": "read-only", "opt": "read-only", "root": "read-only",
                "mkdir-parent": "read-only"}
        if codex:
            want["codex-home"] = "writable"
        self.assertEqual({k: r.get(k) for k in want}, want, text)
        self.assertTrue(os.path.isfile(os.path.join(self.rd, f"ok-{self.TAG}")))   # the run dir write did land

    def test_hook_bash_sandbox(self):
        path = os.environ.get("HOOK_UNDER_TEST", os.path.join(REAL, ".claude", "hooks", "sandbox.py"))
        spec = importlib.util.spec_from_file_location("hook", path)
        H = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(H)
        for net in (False, True):
            with self.subTest(net=net):
                p = subprocess.run(H.bwrap_command(self.rd, self.probe, net=net), shell=True, text=True,
                                   capture_output=True, timeout=60)
                self.assertEqual(p.returncode, 0, p.stderr)
                self.check(p.stdout)

    def test_codex_sandbox(self):
        root, _ = G.make_root()
        bindir = tempfile.mkdtemp(prefix="fake-codex-")
        try:
            with open(os.path.join(bindir, "codex"), "w") as f:
                f.write("#!/bin/bash\n" + HOST_CALLS + "{\n" + self.probe + '\n} > "$KIT_RUN/output/parent.txt" 2>&1\nexit 0\n')
            os.chmod(os.path.join(bindir, "codex"), 0o755)
            auth = os.path.join(bindir, "auth.json")
            open(auth, "w").write('{"fake": "token-for-tests"}')
            env = dict(os.environ, KIT_ROOT=root, KIT_CODEX_BIN_DIR=bindir, KIT_CODEX_AUTH=auth)
            for net, note in ((False, "codex"), (True, "codex-net")):
                with self.subTest(net=net):
                    open(os.path.join(self.rd, "HARNESS-NOTE.md"), "w").write(f"<!-- harness: {note} -->\n")
                    p = subprocess.run([PY, EXT, "codex", self.rd, "--model", "m", "--effort", "low"]
                                       + (["--network"] if net else []), text=True, capture_output=True, env=env, timeout=120)
                    self.assertEqual(p.returncode, 0, p.stderr)
                    self.check(open(os.path.join(self.rd, "output", "parent.txt")).read(), codex=True)
                    os.remove(os.path.join(self.rd, f"ok-{self.TAG}"))
        finally:
            shutil.rmtree(root)
            shutil.rmtree(bindir)


class T5PlanLimit(unittest.TestCase):
    """LESSONS.md "The ChatGPT plan's usage limit is detected and reported": the ChatGPT plan's usage limit is found in Codex's event log."""

    def test_detect(self):
        sys.path.insert(0, G.BIN)
        spec = importlib.util.spec_from_file_location("ext_pl", EXT)
        X = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(X)
        rd = tempfile.mkdtemp()
        try:
            self.assertIsNone(X.plan_limit(rd))
            msg = ("You’ve hit your usage limit. Upgrade to Pro (https://chatgpt.com/explore/pro), visit "
                   "https://chatgpt.com/codex/settings/usage to purchase more credits or try again at Sep 23rd, 2026 12:01 AM.")
            with open(os.path.join(rd, "launch.jsonl"), "w") as f:
                f.write(json.dumps({"type": "item.completed", "item": {"text": "a usage limit is discussed"}}) + "\n")
            self.assertIsNone(X.plan_limit(rd))                                   # prose about limits is not the event
            with open(os.path.join(rd, "launch.jsonl"), "a") as f:
                f.write(json.dumps({"type": "turn.failed", "error": {"message": msg}}) + "\n")
            self.assertEqual(X.plan_limit(rd), "Sep 23rd, 2026 12:01 AM")
        finally:
            shutil.rmtree(rd)

    def test_capacity(self):
        """A model at capacity is its own report (the lines are the ones Codex wrote for a real refusal on 2026-09-25)."""
        spec = importlib.util.spec_from_file_location("ext_cap", EXT)
        X = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(X)
        rd = tempfile.mkdtemp()
        try:
            with open(os.path.join(rd, "launch.jsonl"), "w") as f:
                f.write('{"type":"thread.started","thread_id":"01a0db08-96b3-7542-9029-4c4da0b2b5ca"}\n{"type":"turn.started"}\n')
            self.assertIsNone(X.at_capacity(rd))
            with open(os.path.join(rd, "launch.jsonl"), "a") as f:
                f.write('{"type":"error","message":"Selected model is at capacity. Please try a different model."}\n'
                        '{"type":"turn.failed","error":{"message":"Selected model is at capacity. Please try a different model."}}\n')
            self.assertEqual(X.at_capacity(rd), "Selected model is at capacity. Please try a different model.")
            self.assertIsNone(X.plan_limit(rd))                                   # not the plan's usage limit
            p = subprocess.run([PY, EXT, "capacity", rd], text=True, capture_output=True)
            self.assertEqual(p.stdout.strip(), "yes")
        finally:
            shutil.rmtree(rd)


class T5RunExternal(unittest.TestCase):
    """Refusals and --dry-run on a throwaway run under the real tree; a stub `claude` proves nothing launches."""

    def setUp(self):
        self.rd = os.path.join(REAL, "workspace-1", "runs", "999-ext-test-fixture")
        os.makedirs(self.rd, exist_ok=True)
        open(os.path.join(self.rd, "BRIEF.md"), "w").write("brief\n")
        self.stub = tempfile.mkdtemp()
        with open(os.path.join(self.stub, "claude"), "w") as f:
            f.write(f"#!/bin/sh\ntouch {self.stub}/CALLED\n")
        os.chmod(os.path.join(self.stub, "claude"), 0o755)
        self.env = {k: v for k, v in os.environ.items() if k != "KIT_ROOT"}
        self.env["PATH"] = self.stub + ":" + self.env["PATH"]

    def tearDown(self):
        called = os.path.exists(os.path.join(self.stub, "CALLED"))
        shutil.rmtree(self.rd)
        shutil.rmtree(self.stub)
        shutil.rmtree(os.path.join(REAL, ".claude", "state", "ext", "999-ext-test-fixture"), ignore_errors=True)
        for d in (os.path.dirname(self.rd), os.path.dirname(os.path.dirname(self.rd)), os.path.join(REAL, ".claude", "state", "ext"),
                  os.path.join(REAL, ".claude", "state")):
            try:                      # leave the tree as it was found
                os.rmdir(d)
            except OSError:
                pass
        self.assertFalse(called, "a launch reached `claude`")

    def run_ext(self, *args):
        return subprocess.run([os.path.join(G.BIN, "run-external"), "999-ext-test-fixture", *args],
                              text=True, capture_output=True, env=self.env, timeout=60)

    def note(self, kind):
        open(os.path.join(self.rd, "HARNESS-NOTE.md"), "w").write(f"<!-- harness: {kind} -->\n")

    def test_note_must_match(self):
        for args, have in ((["--via", "codex"], None), (["--via", "codex"], "codex-net"),
                           (["--via", "codex", "--network"], "codex"), (["--via", "anthropic", "--network"], None),
                           (["--via", "anthropic"], "claude-net")):
            with self.subTest(args=args, have=have):
                if have:
                    self.note(have)
                elif os.path.exists(os.path.join(self.rd, "HARNESS-NOTE.md")):
                    os.remove(os.path.join(self.rd, "HARNESS-NOTE.md"))
                p = self.run_ext("--model", "m", *args)
                self.assertEqual(p.returncode, 2, p.stderr)
                self.assertIn("HARNESS-NOTE.md", p.stderr)

    def test_effort_checked(self):
        """Codex accepts any effort string silently, so the launcher checks it, per route, before the approval."""
        self.note("codex")
        for eff, rc in (("bogus", 2), ("minimal", 0), ("max", 0)):
            self.assertEqual(self.run_ext("--model", "m", "--via", "codex", "--effort", eff, "--dry-run").returncode, rc, eff)
        os.remove(os.path.join(self.rd, "HARNESS-NOTE.md"))
        self.assertEqual(self.run_ext("--model", "opus", "--via", "anthropic", "--effort", "minimal", "--dry-run").returncode, 2)
        self.assertEqual(self.run_ext("--model", "opus", "--via", "anthropic", "--effort", "xhigh", "--dry-run").returncode, 0)

    def test_detach_refusal_reported(self):
        """--detach runs the launch as a user service; a refusal inside it (no approval) comes back at once, and the
        service's environment still has the stub first on PATH, so nothing could have launched."""
        self.note("codex")
        p = self.run_ext("--model", "gpt-5.6-sol", "--via", "codex", "--effort", "low", "--detach")
        rc, why = G.refusal(REAL)
        self.assertEqual(p.returncode, rc, p.stdout + p.stderr)
        self.assertIn(why, p.stderr)
        if not G.sandbox_installed(REAL):   # the kit: refused before any service is started, which is the point
            self.assertFalse(os.path.exists(os.path.join(REAL, ".claude", "state", "ext", "999-ext-test-fixture", "detached.exit")))
            return
        self.assertIn("ended at once with exit 3", p.stderr)
        sd = os.path.join(REAL, ".claude", "state", "ext", "999-ext-test-fixture")
        self.assertEqual(open(os.path.join(sd, "detached.exit")).read().strip(), "3")
        st = subprocess.run(["systemctl", "--user", "is-active", "kit-run-999-ext-test-fixture"], capture_output=True, text=True)
        self.assertNotEqual(st.stdout.strip(), "active")

    def test_no_approval(self):
        self.note("codex")
        p = self.run_ext("--model", "gpt-5.6-sol", "--via", "codex")
        rc, why = G.refusal(REAL)
        self.assertEqual(p.returncode, rc, p.stderr)
        self.assertIn(why, p.stderr)

    def test_module_refused_before_approval(self):
        """--module names a licence module of kit-env.json, checked before any approval is touched: exit 2, not 3."""
        p = self.run_ext("--model", "opus", "--via", "anthropic", "--module", "nosuch")
        self.assertEqual(p.returncode, 2, p.stdout + p.stderr)
        self.assertIn("nosuch", p.stderr)

    def test_module_bound_in_the_approval(self):
        """Runs in a throwaway copy of the tree with an environment file of its own: since kit-v0.6.9 every instance has a
        kit-env.json (the user's), which this test must never write; the launcher reads only the file beside it, by
        design (no variable may move what a worker's sandbox mounts). The proof instance's note of 2026-10-01: the old
        form refused to run wherever the file existed, so no instance exercised it."""
        root = os.path.realpath(tempfile.mkdtemp(prefix="module-fixture-"))
        self.addCleanup(shutil.rmtree, root, True)
        for d in ("bin", "harness"):
            shutil.copytree(os.path.join(REAL, d), os.path.join(root, d), ignore=shutil.ignore_patterns("__pycache__"))
        shutil.copytree(os.path.join(REAL, ".claude"), os.path.join(root, ".claude"),
                        ignore=shutil.ignore_patterns("state", "settings.json", "settings.local.json", "worker-net.settings.json",
                                                      "__pycache__"))
        open(os.path.join(root, "LEDGER.log"), "w").close()
        rd = os.path.join(root, "workspace-1", "runs", "999-ext-test-fixture")
        os.makedirs(rd)
        open(os.path.join(rd, "BRIEF.md"), "w").write("brief\n")
        tool = tempfile.mkdtemp(prefix="licensed-tool-")
        self.addCleanup(shutil.rmtree, tool, True)
        json.dump({"modules": {"lic": {"binds": [tool], "licence_servers": [{"host": "localhost", "port": 27000}]}}},
                  open(os.path.join(root, "kit-env.json"), "w"))
        before = open(os.path.join(REAL, "kit-env.json")).read() if os.path.exists(os.path.join(REAL, "kit-env.json")) else None
        run = lambda *args: subprocess.run([os.path.join(root, "bin", "run-external"), "999-ext-test-fixture", *args],
                                           text=True, capture_output=True, env=self.env, timeout=60)
        p = run("--model", "opus", "--via", "anthropic", "--module", "lic", "--dry-run")
        self.assertEqual(p.returncode, 2, p.stdout + p.stderr)            # a module the run's brief never mentions
        self.assertIn(".modules", p.stderr)
        open(os.path.join(rd, ".modules"), "w").write("lic\n")        # bin/new-run --module lic recorded it
        p = run("--model", "opus", "--via", "anthropic", "--module", "lic", "--dry-run")
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn("approval flags: --model opus --via anthropic --module lic", p.stdout)
        p = run("--model", "opus", "--via", "anthropic")
        self.assertEqual(p.returncode, 2, p.stdout + p.stderr)            # the brief promises a module the launch lacks
        self.assertIn(".modules", p.stderr)
        open(os.path.join(rd, "HARNESS-NOTE.md"), "w").write("<!-- harness: codex -->\n")
        p = run("--model", "gpt-5.6-sol", "--via", "codex", "--module", "lic", "--dry-run")
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn("/opt/kit/licence/0.sock", p.stdout)                # the Codex sandbox gets the relay socket
        after = open(os.path.join(REAL, "kit-env.json")).read() if os.path.exists(os.path.join(REAL, "kit-env.json")) else None
        self.assertEqual(before, after)                                   # the real tree's file, if any, untouched

    def test_dry_run(self):
        self.note("codex")
        p = self.run_ext("--model", "gpt-5.6-sol", "--via", "codex", "--dry-run")
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn("--unshare-all", p.stdout)
        for var in ("KIT_THREADS", "KIT_CPU_HOURS", "KIT_MEM_GB"):   # P-11 (e): a Codex worker reads its caps as a Claude one does
            self.assertIn(var, p.stdout)
        self.assertNotIn("--share-net", p.stdout)
        self.assertIn("egress.sock", p.stdout)
        self.note("claude-net")
        p = self.run_ext("--model", "opus", "--via", "anthropic", "--network", "--dry-run")
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn("WebSearch,WebFetch", p.stdout)
        for needle in ("--disable-slash-commands", "CLAUDE_CODE_DISABLE_AUTO_MEMORY=1", "CLAUDE_CODE_DISABLE_BUNDLED_SKILLS=1"):
            self.assertIn(needle, p.stdout)   # user 2026-09-22: no run method shows memory or skills
        self.assertIn("approval flags: --model opus --via anthropic --network", p.stdout)
        self.assertEqual(sorted(os.listdir(self.rd)), ["BRIEF.md", "HARNESS-NOTE.md"])

    def test_wall_cap_defaults(self):
        """LESSONS.md "A wall-clock cap on every route": a wall-clock cap on every route, 4 h on Claude routes and 2 h on Codex."""
        p = self.run_ext("--model", "opus", "--via", "anthropic", "--dry-run")
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn("under timeout: wall-clock cap 4 h", p.stdout)
        p = self.run_ext("--model", "opus", "--via", "anthropic", "--wall-hours", "1.5", "--dry-run")
        self.assertIn("under timeout: wall-clock cap 1.5 h", p.stdout)
        self.assertIn("approval flags: --model opus --via anthropic --wall-hours 1.5", p.stdout)
        self.note("codex")
        p = self.run_ext("--model", "gpt-5.6-sol", "--via", "codex", "--dry-run")
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn("wall-hours=2;", p.stdout)
        src = open(os.path.join(G.BIN, "run-external")).read()
        self.assertIn('timeout --kill-after=60 "$REMAIN"', src)            # the Claude worker runs under timeout
        self.assertEqual(src.count("max-budget-usd"), 1)                   # only the header sentence names it

    def test_turn_cap_default_shared(self):
        """HANDOFF §6 item 6: bin/lint-brief and bin/run-external hold the same default turn cap."""
        import re
        src = open(os.path.join(G.BIN, "run-external")).read()
        lint = open(os.path.join(G.BIN, "lint-brief")).read()
        self.assertEqual(re.search(r"\bMAXTURNS=(\d+);", src).group(1), re.search(r"^DEFAULT_MAX_TURNS = (\d+)", lint, re.M).group(1))

    def test_inherited_routing_dropped(self):
        """The source's caveat of 2026-09-16: a parent session's ANTHROPIC_* variables (a base URL, a token) never reach a
        worker. The launcher's own line runs here with them set; it comes before the worker's command line."""
        src = open(os.path.join(G.BIN, "run-external")).read()
        line = next(l for l in src.splitlines() if l.startswith("for v in $(env | grep -oE"))
        self.assertLess(src.index(line), src.index('"$CLAUDE_BIN" -p "$P"'))
        env = dict(os.environ, ANTHROPIC_BASE_URL="http://elsewhere", ANTHROPIC_AUTH_TOKEN="t", CLAUDECODE="1", KEEP_ME="1")
        out = subprocess.run(["bash", "-c", line + "\nenv"], text=True, capture_output=True, env=env).stdout
        self.assertNotIn("ANTHROPIC_", out)
        self.assertNotIn("CLAUDECODE", out)
        self.assertIn("KEEP_ME=1", out)

    def test_no_spending_cap(self):
        """LESSONS.md "No spending cap on any run" (user 2026-09-25): no run has a spending cap; --budget is refused before anything else."""
        p = self.run_ext("--model", "opus", "--via", "anthropic", "--dry-run")
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn("--max-turns 300", p.stdout)
        self.assertNotIn("budget", p.stdout)
        p = self.run_ext("--model", "opus", "--via", "anthropic", "--budget", "40")
        self.assertEqual(p.returncode, 2, p.stderr)
        self.assertIn("no run has a spending cap", p.stderr)
        self.assertEqual(sorted(os.listdir(self.rd)), ["BRIEF.md"])

    def test_launched_once(self):
        """LESSONS.md "A run directory is launched once": a run holding an earlier launch's record is refused before the
        approval is touched, whatever the record file is called."""
        for f in ("launch.jsonl", "launch.20260925T000000Z.log", "RECORD-EXT.md", "usage.json", "output/result.md"):
            with self.subTest(f=f):
                os.makedirs(os.path.dirname(os.path.join(self.rd, f)), exist_ok=True)
                open(os.path.join(self.rd, f), "w").write("earlier attempt\n")
                p = self.run_ext("--model", "opus", "--via", "anthropic", "--dry-run")
                self.assertEqual(p.returncode, 2, p.stderr)
                self.assertIn("was launched before", p.stderr)
                os.remove(os.path.join(self.rd, f))
        self.assertEqual(self.run_ext("--model", "opus", "--via", "anthropic", "--dry-run").returncode, 0)

    def test_launched_once_counts_the_licence_log_and_the_outbox(self):
        """P-12 (a medium of the code audit): licence.log and a non-empty .ledger-outbox are left out of the approval's
        hashes, and were left out of this check too, so either could carry unapproved bytes to the worker."""
        for f in ("licence.log", ".ledger-outbox"):
            with self.subTest(f=f):
                open(os.path.join(self.rd, f), "w").write("earlier, or planted\n")
                p = self.run_ext("--model", "opus", "--via", "anthropic", "--dry-run")
                self.assertEqual(p.returncode, 2, p.stderr)
                self.assertIn("was launched before", p.stderr)
                os.remove(os.path.join(self.rd, f))
        open(os.path.join(self.rd, ".ledger-outbox"), "w").close()   # bin/new-run's empty outbox is no earlier launch
        self.assertEqual(self.run_ext("--model", "opus", "--via", "anthropic", "--dry-run").returncode, 0)

    def test_a_run_name_used_twice_is_refused(self):
        """P-12 (a low finding): host state, approvals and bindings are keyed by the run's name, which bin/new-run makes
        unique across workspaces; a second directory of the same name (made by hand) shared them. Refused before the
        approval is touched."""
        twin = os.path.join(REAL, "workspace-2", "runs", "999-ext-test-fixture")
        os.makedirs(twin)
        self.addCleanup(shutil.rmtree, os.path.join(REAL, "workspace-2"), True)
        open(os.path.join(twin, "BRIEF.md"), "w").write("twin\n")
        p = self.run_ext("--model", "opus", "--via", "anthropic", "--dry-run")
        self.assertEqual(p.returncode, 2, p.stderr)
        self.assertIn("not unique", p.stderr)

    def test_detach_touches_nothing_before_its_unit_check(self):
        """P-12 (two low findings): --detach emptied detached.out and removed detached.exit before asking whether the run's
        unit was already running, so a second launch wiped the first one's output; and it pasted the exit file's path
        into a `bash -c` script. Read from the source: a live detach needs an installed sandbox."""
        src = open(os.path.join(G.BIN, "run-external")).read()
        blk = src[src.index('if [ "$DETACH" = 1 ]; then'):]
        self.assertLess(blk.index('is-active --quiet "$UNIT"'), blk.index(': > "$OUT"'))
        self.assertNotIn("\"'\"$EXITF\"'\"", src)   # the path spliced into the script text
        self.assertIn('run-external "$EXITF" "$0"', src)

    def test_packet_scan_before_the_approval(self):
        """LESSONS.md "No packet carries blocked material": run-external runs the packet scan on the real tree, and refuses on a finding, before the approval
        is touched (read from the source: a live refusal would need a rules file in this tree)."""
        src = open(os.path.join(G.BIN, "run-external")).read()
        scan = src.index('PKT=$(env -u KIT_ROOT /usr/bin/python3 "$ROOT/bin/lint-brief" --packet "$RD"')
        self.assertLess(scan, src.index('"$ROOT/bin/_approval.py" check launch'))
        self.assertLess(scan, src.index('if [ "$DRY" = 1 ]; then'))                    # a dry run is scanned too
        p = self.run_ext("--model", "opus", "--via", "anthropic", "--dry-run")          # no rules here: nothing blocked
        self.assertEqual(p.returncode, 0, p.stderr)

    def test_queue_refusals(self):
        """LESSONS.md 'A queue for runs approved together': the queue refuses without approvals, refuses a run that fails the
        launch checks before any approval is touched, and releases nothing for an unknown queue id."""
        queue = lambda: subprocess.run([os.path.join(G.BIN, "run-external"), "--queue", "999-ext-test-fixture", "--model",
                                        "opus", "--via", "anthropic"], text=True, capture_output=True, env=self.env, timeout=60)
        p = queue()
        if G.sandbox_installed(REAL):
            self.assertEqual(p.returncode, 3, p.stderr)
            self.assertIn("no user approval", p.stderr)
        else:   # the kit: each run's --check meets the preflight before any approval is touched (the outside review's F7)
            self.assertEqual(p.returncode, 2, p.stderr)
            self.assertIn("fails the launch checks", p.stderr)
        open(os.path.join(self.rd, "BRIEF.md"), "w").write("Budget: at most 400 tool calls.\n")
        p = queue()
        self.assertEqual(p.returncode, 2, p.stderr)
        self.assertIn("fails the launch checks", p.stderr)
        open(os.path.join(self.rd, "BRIEF.md"), "w").write("brief\n")
        p = self.run_ext("--model", "opus", "--via", "anthropic", "--queued", "0123456789abcdef")
        rc, why = (3, "no queue record") if G.sandbox_installed(REAL) else G.refusal(REAL)
        self.assertEqual(p.returncode, rc, p.stderr)
        self.assertIn(why, p.stderr)
        p = self.run_ext("--model", "opus", "--via", "anthropic", "--queued", "0123456789abcdef", "--detach")
        self.assertEqual(p.returncode, 2, p.stderr)
        self.assertIn("do not go together", p.stderr)
        src = open(os.path.join(G.BIN, "run-external")).read()            # the wall cap reads 137 only past the deadline
        self.assertIn('[ $RC -eq 137 ] && [ "$(date +%s)" -ge "$DEADLINE" ]', src)
        self.assertEqual(sorted(os.listdir(self.rd)), ["BRIEF.md"])


class T7LicenceRoute(unittest.TestCase):
    """The licence-server route (kit-v0.5; the user's "I want to implement the network route now", 2026-10-01): a
    module that names a licence server is given only to a run launched with --module NAME; the worker reaches that host
    and port and nothing else, through a relay on the host (bin/_ext.py) and the existing in-sandbox forwarder. Live:
    a sandboxed command talks to a local server through the relay and cannot reach a second one."""
    ROOT_LINE = 'ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))'

    def setUp(self):
        import socket
        import threading
        self.root, self.rd = G.make_root()
        self.addCleanup(shutil.rmtree, self.root, True)
        shutil.copytree(os.path.join(REAL, ".claude", "sandbox"), os.path.join(self.root, ".claude", "sandbox"))
        for d in ("bin", "harness"):
            os.symlink(os.path.join(REAL, d), os.path.join(self.root, d))
        self.tool = tempfile.mkdtemp(prefix="licensed-tool-")
        self.free = tempfile.mkdtemp(prefix="free-tool-")
        for d in (self.tool, self.free):
            self.addCleanup(shutil.rmtree, d, True)
        self.servers = []
        self.ports = []
        for tag in (b"named", b"other"):
            srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            srv.bind(("127.0.0.1", 0))
            srv.listen(8)
            self.servers.append(srv)
            self.ports.append(srv.getsockname()[1])

            def serve(s=srv, tag=tag):
                while True:
                    try:
                        c, _ = s.accept()
                    except OSError:
                        return
                    d = c.recv(64)
                    c.sendall(tag + b":" + d)
                    c.close()
            threading.Thread(target=serve, daemon=True).start()
        self.addCleanup(lambda: [s.close() for s in self.servers])
        json.dump({"modules": {"lic": {"binds": [self.tool],
                                       "licence_servers": [{"host": "localhost", "port": self.ports[0]}]},
                               "free": {"binds": [self.free]}}},
                  open(os.path.join(self.root, "kit-env.json"), "w"))
        sys.path.insert(0, os.path.join(REAL, "bin"))
        import _ext
        self.X = _ext
        self.log = os.path.join(self.root, "licence.log")
        self.socks = self.X.start_licence_relays(self.rd, [("localhost", self.ports[0])], self.log)
        self.addCleanup(lambda: [os.unlink(p) for _, p in self.socks if os.path.exists(p)])
        self.env0 = dict(os.environ)
        self.addCleanup(lambda: (os.environ.clear(), os.environ.update(self.env0)))

    def hook(self):
        src = open(os.environ.get("HOOK_UNDER_TEST", os.path.join(REAL, ".claude", "hooks", "sandbox.py"))).read()
        assert src.count(self.ROOT_LINE) == 1
        path = os.path.join(self.root, ".claude", "hook_lic.py")
        open(path, "w").write(src.replace(self.ROOT_LINE, f"ROOT = {self.root!r}"))
        spec = importlib.util.spec_from_file_location("hook_lic", path)
        H = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(H)
        return H

    def grant(self, socks=None):
        os.environ.update(KIT_WORKER_RUN=self.rd, KIT_WORKER_MODULES="lic",
                          KIT_WORKER_LICENCE_SOCKS=socks if socks is not None else
                          ",".join(f"{port}={p}" for port, p in self.socks))

    def test_only_the_named_server_is_reached(self):
        self.grant()
        probe = ("python3 - <<'EOF'\nimport socket\n"
                 "def talk(port):\n"
                 "    try:\n"
                 "        s = socket.create_connection(('localhost', port), timeout=5); s.sendall(b'ping')\n"
                 "        d = s.recv(64); s.close(); return d.decode() or 'empty'\n"
                 "    except OSError as e:\n"
                 "        return 'refused:' + type(e).__name__\n"
                 f"print('named=' + talk({self.ports[0]}))\nprint('other=' + talk({self.ports[1]}))\n"
                 "print('hosts=' + open('/etc/hosts').read().replace(chr(10), '|'))\nEOF")
        cmd = self.hook().bwrap_command(self.rd, probe)
        self.assertIn(f"--ro-bind {self.tool} {self.tool}", cmd)
        p = subprocess.run(cmd, shell=True, text=True, capture_output=True, timeout=120)
        out = dict(l.split("=", 1) for l in p.stdout.splitlines() if "=" in l)
        self.assertEqual(out.get("named"), "named:ping", p.stdout + p.stderr)
        self.assertTrue(out.get("other", "").startswith("refused:"), p.stdout + p.stderr)
        self.assertIn("127.0.0.1 localhost", out.get("hosts", ""))
        self.assertIn(f"OPEN localhost:{self.ports[0]}", open(self.log).read())

    def test_not_granted_nothing(self):
        os.environ.update(KIT_WORKER_RUN=self.rd, KIT_WORKER_LICENCE_SOCKS=",".join(f"{a}={b}" for a, b in self.socks))
        cmd = self.hook().bwrap_command(self.rd, "true")
        self.assertNotIn("/opt/kit/licence", cmd)
        self.assertNotIn(self.tool + " " + self.tool, cmd.replace("--ro-bind ", ""))   # an on-request module stays out

    def test_a_socket_not_the_relays_is_refused(self):
        fake = os.path.join(self.root, "not-a-socket")
        open(fake, "w").close()
        self.grant(f"{self.ports[0]}={fake}")
        self.assertNotIn(fake, self.hook().bwrap_command(self.rd, "true"))

    def test_codex_command_shell(self):
        """kit-shell, as a Codex worker's command shell: inside an outer sandbox shaped like the Codex one (no network,
        the relay socket and the forwarder under /opt/kit), a command's own sandbox reaches the named server and only it."""
        probe = ("python3 -c \"import socket\n"
                 "def talk(p):\n"
                 "    try:\n"
                 "        s = socket.create_connection(('localhost', p), timeout=5); s.sendall(b'ping'); d = s.recv(64)\n"
                 "        return d.decode()\n"
                 "    except OSError as e:\n"
                 "        return 'refused:' + type(e).__name__\n"
                 f"print('named=' + talk({self.ports[0]})); print('other=' + talk({self.ports[1]}))\"")
        outer = ["bwrap", "--dev-bind", "/", "/", "--tmpfs", "/opt", "--tmpfs", "/opt/codex-home", "--tmpfs", "/tmp",
                 "--ro-bind", os.path.join(REAL, "harness", "egress-fwd"), "/opt/kit/bin/egress-fwd",
                 "--ro-bind", self.socks[0][1], "/opt/kit/licence/0.sock",
                 "--ro-bind", "/dev/null", "/opt/kit/egress.sock",
                 "--bind", self.rd, self.rd, "--proc", "/proc", "--dev", "/dev",
                 "--unshare-all", "--die-with-parent", "--chdir", self.rd,
                 "--setenv", "KIT_RUN", self.rd, "--setenv", "KIT_CMD_NET", "0",
                 "--setenv", "KIT_LICENCE_FWD", f"{self.ports[0]}=/opt/kit/licence/0.sock",
                 "/bin/bash", os.path.join(REAL, ".claude", "sandbox", "kit-shell"), "-c", probe]
        p = subprocess.run(outer, text=True, capture_output=True, timeout=120)
        out = dict(l.split("=", 1) for l in p.stdout.splitlines() if "=" in l)
        self.assertEqual(out.get("named"), "named:ping", p.stdout + p.stderr)
        self.assertTrue(out.get("other", "").startswith("refused:"), p.stdout + p.stderr)

    def test_module_check(self):
        run = lambda *m: subprocess.run(["/usr/bin/python3", os.path.join(REAL, "bin", "_ext.py"), "module-check", *m],
                                        capture_output=True, text=True, env=dict(os.environ, KIT_ROOT=self.root))
        self.assertEqual(run("lic").returncode, 0)
        for bad in ("nosuch", "free"):
            with self.subTest(module=bad):
                r = run(bad)
                self.assertEqual(r.returncode, 2, r.stdout + r.stderr)


class T5P12HostWrites(unittest.TestCase):
    """P-12 C2 and C3 (the code audit of 2026-10-02; user 2026-10-02: "let's do the p12 fixes now"): bin/limits-exec wrote
    its working files, usage.json and time.log into the run directory, and _ext.py copied its logs and wrote RECORD-EXT.md
    there, each through any symlink the worker had left at the name; _ext.py drained the outbox after an islink check
    that is not a guard; and a session file left by the worker under launch.rollout.jsonl decided the models a Codex run
    was answered by when the main thread's was not found."""

    def setUp(self):
        self.root, self.rd = G.make_root()
        self.vd = os.path.realpath(tempfile.mkdtemp(prefix="victim-"))
        self.vf = os.path.join(self.vd, "f.txt")
        open(self.vf, "w").write("the user's file\n")
        self.env = dict(os.environ, KIT_ROOT=self.root)

    def tearDown(self):
        shutil.rmtree(self.root, True)
        shutil.rmtree(self.vd, True)

    def untouched(self):
        self.assertEqual(sorted(os.listdir(self.vd)), ["f.txt"])
        self.assertEqual(open(self.vf).read(), "the user's file\n")

    def test_limits_exec(self):
        if subprocess.run(["systemd-run", "--user", "--scope", "--quiet", "--", "true"], capture_output=True).returncode != 0:
            self.skipTest("no systemd user scope here")
        plant = "; ".join(f"ln -sfn {self.vf} {self.rd}/{n}" for n in (".cpu.stat", ".mem.peak", ".cpu.cap", "usage.json",
                                                                       "time.log"))
        p = subprocess.run([os.path.join(G.BIN, "limits-exec"), self.rd, "--", "bash", "-c", plant], text=True,
                           capture_output=True, timeout=60)
        self.untouched()
        u = json.load(open(os.path.join(self.rd, "usage.json")))
        self.assertFalse(os.path.islink(os.path.join(self.rd, "usage.json")))
        self.assertFalse(u["cpu_cap_hit"], p.stdout + p.stderr)   # a worker's .cpu.cap is not the host's
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        self.assertIn("Command being timed", open(os.path.join(self.rd, "time.log")).read())
        self.assertFalse(os.path.islink(os.path.join(self.rd, "time.log")))

    def test_record(self):
        sd = os.path.join(self.root, ".claude", "state", "ext", "900-solve")
        os.makedirs(sd)
        open(os.path.join(sd, "egress.log"), "w").write("host log\n")
        for n in ("egress.log", "RECORD-EXT.md"):
            os.symlink(self.vf, os.path.join(self.rd, n))
        p = subprocess.run([PY, EXT, "record", self.rd, "--via", "codex", "--model", "m", "--exit", "0"],
                           text=True, capture_output=True, env=self.env)
        self.assertEqual(p.returncode, 0, p.stderr)
        self.untouched()
        self.assertEqual(open(os.path.join(self.rd, "egress.log")).read(), "host log\n")
        self.assertIn("Hashes", open(os.path.join(self.rd, "RECORD-EXT.md")).read())

    def call(self, code):
        return subprocess.run([PY, "-c", "import sys, os; sys.path.insert(0, %r); sys.argv = ['_ext.py']\n"
                               "import importlib.util as u\ns = u.spec_from_file_location('ext', %r); X = u.module_from_spec(s)\n"
                               "s.loader.exec_module(X)\n" % (G.BIN, EXT) + code],
                              text=True, capture_output=True, env=self.env)

    def test_outbox_symlink_not_followed_after_the_check(self):
        ob = os.path.join(self.rd, ".ledger-outbox")
        os.remove(ob)
        os.symlink(self.vf, ob)
        p = self.call(f"os.path.islink = lambda p: False\ntry:\n    X.drain_outbox({self.rd!r})\nexcept OSError:\n    pass\n")
        self.assertEqual(p.returncode, 0, p.stderr)
        self.untouched()
        self.assertNotIn("the user's file", open(os.path.join(self.root, "LEDGER.log")).read())

    def test_a_planted_session_file_is_not_the_record(self):
        open(os.path.join(self.rd, "launch.rollout.jsonl"), "w").write(
            json.dumps({"type": "turn_context", "payload": {"model": "m"}}) + "\n")
        open(os.path.join(self.rd, "launch.rollout.sub-1.jsonl"), "w").write("{}\n")
        p = self.call(f"print(X.sort_rollouts({self.rd!r}, '/nonexistent'))")
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertEqual(p.stdout.strip(), "(False, 0)")
        self.assertEqual([f for f in os.listdir(self.rd) if f.startswith("launch.rollout")], [])


class T5P12RetryTrigger(unittest.TestCase):
    """P-12 H4 (the code audit of 2026-10-02): bin/run-external retried a Claude-route launch (with fresh CPU caps) when
    its transcript held an upstream rate-limit phrase anywhere, the worker's own tool output and text included, so a worker
    could print the phrase and buy itself another attempt. Now only the CLI's own events count: its stderr, and the
    transcript's lines but the tool results and the model's own messages."""

    def setUp(self):
        self.d = tempfile.mkdtemp(prefix="retry-")
        self.log, self.err = os.path.join(self.d, "launch.log"), os.path.join(self.d, "launch.err")
        open(self.err, "w").close()

    def tearDown(self):
        shutil.rmtree(self.d, True)

    def limited(self, *events, err=""):
        open(self.log, "w").write("".join(json.dumps(e) + "\n" for e in events))
        open(self.err, "w").write(err)
        return subprocess.run([PY, EXT, "upstream-limited", self.log, self.err], capture_output=True).returncode == 0

    def test_the_workers_words_do_not_count(self):
        said = "API Error: rate_limit_error (malformed response (HTTP 200))"
        self.assertFalse(self.limited({"type": "user", "message": {"content": [{"type": "tool_result", "content": said}]}}))
        self.assertFalse(self.limited({"type": "assistant", "message": {"model": "claude-opus-5-5",
                                                                        "content": [{"type": "text", "text": said}]}}))
        self.assertFalse(self.limited({"type": "system", "subtype": "init"}))
        self.assertTrue(self.limited({"type": "assistant", "message": {"model": "<synthetic>",
                                                                       "content": [{"type": "text", "text": said}]}}))
        self.assertTrue(self.limited({"type": "result", "subtype": "error_during_execution", "result": said}))
        self.assertTrue(self.limited(err="rate-limited upstream\n"))


class T5P12StopEndsTheWorker(unittest.TestCase):
    """P-12 H5 (the code audit of 2026-10-02, "unconfirmed" there): a detached run is a user service (kit-run-NAME), but
    bin/limits-exec puts the worker in a scope of its own, outside the service's cgroup, so `systemctl --user stop
    kit-run-NAME` ended the launcher and left the worker running. Real systemd, real processes."""

    def setUp(self):
        if subprocess.run(["systemd-run", "--user", "--scope", "--quiet", "--", "true"], capture_output=True).returncode != 0:
            self.skipTest("no systemd user scope here")
        self.mark = "stopend" + secrets.token_hex(6)
        self.unit = "kit-p12test-" + secrets.token_hex(4)
        self.root, self.rd = G.make_root()

    def tearDown(self):
        subprocess.run(["systemctl", "--user", "stop", self.unit], capture_output=True)
        subprocess.run(["pkill", "-KILL", "-f", self.mark], capture_output=True)
        shutil.rmtree(self.root, True)

    def alive(self):
        return subprocess.run(["pgrep", "-f", self.mark], capture_output=True).returncode == 0

    def test_stopping_the_service_ends_the_worker(self):
        worker = f"import time\nwhile True:\n    time.sleep(0.2)  # {self.mark}"
        subprocess.run(["systemd-run", "--user", "--unit", self.unit, "--collect", "--quiet",
                        os.path.join(G.BIN, "limits-exec"), self.rd, "--", PY, "-c", worker], check=True)
        for _ in range(50):
            if self.alive():
                break
            time.sleep(0.2)
        self.assertTrue(self.alive(), "the worker never started")
        subprocess.run(["systemctl", "--user", "stop", self.unit], capture_output=True, timeout=60)
        for _ in range(50):
            if not self.alive():
                break
            time.sleep(0.2)
        self.assertFalse(self.alive(), "the worker outlived its stopped service")


if __name__ == "__main__":
    unittest.main(verbosity=2, warnings="ignore")
