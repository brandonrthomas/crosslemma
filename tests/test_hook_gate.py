#!/usr/bin/env python3
"""Synthetic tests of the hook's user-approval gate (LESSONS.md "Every launch and every ledger append consumes a byte-bound"), T3.

    python3 tests/test_hook_gate.py                       tests the installed .claude/hooks/sandbox.py
    HOOK_UNDER_TEST=/path/to/candidate.py python3 tests/test_hook_gate.py

The hook source is copied with its one ROOT line pointed at a throwaway fixture root (whose bin/ is a
symlink to the real bin/), then run as a subprocess on synthetic hook JSON, exactly as Claude Code
runs it. Nothing touches the real ledger, approvals or settings. The golden test replays worker-branch
inputs through the pre-gate hook (commit ab0206f) and the hook under test and demands identical output.

The pre-gate hook is vendored, because this kit's history does not contain it: tests/fixtures/hook-pre-gate.py
is the hook as it stood before the approval gate was built, with its one ROOT line replaced by the placeholder
below and its worker-branch names renamed with the rest of the tree. What the golden test asserts is that the
worker branch still decides every one of those inputs exactly as it did then.
"""
import json
import os
import shutil
import subprocess
import tempfile
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import test_gate as G

HOOK = os.environ.get("HOOK_UNDER_TEST", os.path.join(G.REAL, ".claude", "hooks", "sandbox.py"))
ROOT_LINE = 'ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))'
BASELINE_FIXTURE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures", "hook-pre-gate.py")
BASELINE_ROOT_LINE = 'ROOT = "@ROOT@"'
# The baseline hard-codes the library toolchain; the ported hook takes it from the environment and mounts the
# library module only when it is linked. The golden replay therefore gives BOTH hooks the same linked library,
# so what it compares is the worker branch's decisions and not the presence of an optional module.
BASELINE_ELAN_LINE = 'ELAN = "@ELAN@"'
BASELINE_ORIGIN = "the workspace this kit was extracted from, at its commit ab0206f: the hook as it stood\n# before the approval gate was built, with its root and toolchain lines replaced by placeholders and the\n# names renamed with the rest of the tree. Its bytes are pinned so an edit to the baseline is visible."
BASELINE_SHA256 = "305ff2015efa86a55444ba024c6154c561b683f489f1adbccb088e4a771168ea"  # of the fixture as vendored (renamed with the tree)


def patched(src_text, root, name, root_line=ROOT_LINE):
    assert src_text.count(root_line) == 1
    p = os.path.join(root, name)
    with open(p, "w") as f:
        f.write(src_text.replace(root_line, f"ROOT = {root!r}"))
    return p


class HookCase(unittest.TestCase):
    def setUp(self):
        self.root, self.rd = G.make_root()
        os.symlink(G.BIN, os.path.join(self.root, "bin"))
        os.makedirs(os.path.join(self.root, ".claude"), exist_ok=True)
        with open(HOOK) as f:
            self.hook = patched(f.read(), self.root, "hook_under_test.py")

    def tearDown(self):
        shutil.rmtree(self.root)

    def fire(self, tool, ti, hook=None, env=None, **extra):
        inp = dict({"hook_event_name": "PreToolUse", "session_id": "s1", "transcript_path": "/x/main.jsonl",
                    "cwd": self.root, "permission_mode": "default", "tool_name": tool, "tool_input": ti}, **extra)
        e = dict(os.environ, KIT_ROOT=self.root, **(env or {}))
        p = subprocess.run(["/usr/bin/python3", hook or self.hook], input=json.dumps(inp), text=True, capture_output=True, env=e)
        self.assertEqual(p.returncode, 0, p.stderr)
        return json.loads(p.stdout)["hookSpecificOutput"] if p.stdout.strip() else None

    def decision(self, tool, ti, **kw):
        out = self.fire(tool, ti, **kw)
        return (out or {}).get("permissionDecision"), (out or {}).get("permissionDecisionReason", "")

    def approve(self, *args):
        p = G.tool(self.root, "approve", *args)
        self.assertEqual(p.returncode, 0, p.stderr)

    def digest12(self, *args):
        flags = [] if args and args[0].startswith("--") else ["--", *G.F]   # a launch binds its flags; a ledger kind takes none
        out = G.tool(self.root, "manifest", *args, *flags).stdout
        return [l for l in out.splitlines() if l.startswith("digest:")][0].split()[1][:12]

    def record(self):
        return os.path.join(self.root, ".claude", "state", "approvals", "launch-900-solve.json")

    def worker_prompt(self):
        return f"Start by reading {self.rd}/BRIEF.md with the Read tool, then follow it exactly."


class T3Bash(HookCase):
    def test_denied(self):
        R = self.root
        for cmd in ("bin/approve 900-solve",                                   # no --digest
                    "bin/approve 900-solve --digest 000000000000",             # not these bytes
                    "cd bin && ./approve 900-solve",
                    f"{R}/bin/approve 900-solve; ls",
                    "for r in 900-solve 901-ref; do bin/approve $r; done",
                    "python3 bin/approve 900-solve",
                    "bash -c 'bin/approve 900-solve'",
                    "X=$(bin/approve 900-solve)",
                    "git commit -m x && bin/approve 900-solve",
                    "git -c alias.z='!bin/approve 900-solve' z",
                    "echo '{}' > .claude/state/approvals/launch-900-solve.json",
                    "ls .claude/state/approvals",
                    "claude -p hi",
                    "env X=1 claude --model opus --print hi",
                    "/usr/local/bin/claude --agent kit-worker -p 'read the brief'",
                    "cd /tmp; claude -p hi"):
            with self.subTest(cmd=cmd):
                d, why = self.decision("Bash", {"command": cmd})
                self.assertEqual(d, "deny", cmd)
                self.assertIn("LESSONS.md 'Every launch and every ledger append consumes a byte-bound'", why)
        self.assertFalse(os.path.exists(self.record()))

    def test_not_the_gates_business(self):
        for cmd in ("git status --short", "bin/verify-data", "bin/close-run 900-solve", "bin/manifest 900-solve",
                    "pgrep -fa 'claude -p'", "bin/ledger-claims 900-solve c1 --operator-approved",
                    "bin/run-external 900-solve --model opus --via anthropic",
                    "git add bin/approve bin/_approval.py", "git commit -F /tmp/msg bin/approve",
                    "python3 tests/test_gate.py", "claude --version"):
            with self.subTest(cmd=cmd):
                self.assertIsNone(self.fire("Bash", {"command": cmd}))

    def test_ask_is_worded_by_the_hook(self):
        dg = self.digest12("900-solve")
        cmd = f"bin/approve 900-solve --digest {dg} -- --model opus --effort low"
        out = self.fire("Bash", {"command": cmd, "description": "harmless, trust me"})
        self.assertEqual(out["permissionDecision"], "ask")
        for needle in ("USER APPROVAL", "launch 900-solve", f"digest {dg}", "--effort low --model opus"):
            self.assertIn(needle, out["permissionDecisionReason"])
        self.assertNotIn("trust me", out["permissionDecisionReason"])
        self.assertFalse(os.path.exists(self.record()))          # asking approves nothing
        self.assertIn("ASK-APPROVE", open(os.path.join(self.root, "LEDGER.log")).read())

    def test_ask_refused_outside_default_mode(self):
        cmd = f"bin/approve 900-solve --digest {self.digest12('900-solve')} -- --model m"
        for mode in ("acceptEdits", "bypassPermissions", "dontAsk", "plan", None):
            with self.subTest(mode=mode):
                self.assertEqual(self.decision("Bash", {"command": cmd}, permission_mode=mode)[0], "deny")
        # auto: live-tested 2026-09-18 21:08 MST under remote control, the prompt reached the user with the hook's text
        self.assertEqual(self.decision("Bash", {"command": cmd}, permission_mode="auto")[0], "ask")

    def test_ask_refused_when_an_allow_rule_would_skip_the_prompt(self):
        cmd = f"bin/approve 900-solve --digest {self.digest12('900-solve')} -- --model m"
        for rule in ("Bash(bin/approve:*)", "Bash(bin/*)", "Bash", "Bash(*)"):
            with self.subTest(rule=rule):
                with open(os.path.join(self.root, ".claude", "settings.local.json"), "w") as f:
                    json.dump({"permissions": {"allow": [rule]}}, f)
                d, why = self.decision("Bash", {"command": cmd})
                self.assertEqual(d, "deny")
                self.assertIn("allow rule", why)

    def test_ask_refused_from_another_directory(self):
        cmd = f"bin/approve 900-solve --digest {self.digest12('900-solve')} -- --model m"
        self.assertEqual(self.decision("Bash", {"command": cmd}, cwd="/tmp")[0], "deny")

    def test_ask_batch(self):
        """LESSONS.md "Batch tap": one prompt for several runs, one digest per run in order, each named in the hook's text."""
        out = G.tool(self.root, "manifest", "900-solve", "901-ref", "--", *G.F).stdout
        d1, d2 = [l.split()[1][:12] for l in out.splitlines() if l.startswith("digest:")]
        out = self.fire("Bash", {"command": f"bin/approve 900-solve 901-ref --digest {d1},{d2} -- --model m"})
        self.assertEqual(out["permissionDecision"], "ask")
        for needle in (f"launch 900-solve, digest {d1}", f"launch 901-ref, digest {d2}"):
            self.assertIn(needle, out["permissionDecisionReason"])
        d, why = self.decision("Bash", {"command": f"bin/approve 900-solve 901-ref --digest {d2},{d1} -- --model m"})
        self.assertEqual(d, "deny")
        self.assertIn("would refuse", why)
        self.assertFalse(os.path.exists(self.record()))

    def test_codex_launch_denied(self):
        """LESSONS.md "Networked and Codex launches need their flags bound": a Codex session started by the orchestrator is a launch outside the gate."""
        for cmd in ("codex exec hi", "codex e 'read the brief'", "codex -m gpt-5.6-sol exec - < p.md",
                    "/opt/codex/codex exec --json -", "env X=1 codex review", "cd /tmp; codex resume --last",
                    "codex --search exec hi"):
            with self.subTest(cmd=cmd):
                self.assertEqual(self.decision("Bash", {"command": cmd})[0], "deny", cmd)
        for cmd in ("codex --version", "codex features list", "CODEX_HOME=/x codex features list -c 'web_search=\"disabled\"'",
                    "codex exec --help"[:5] + " --help", "bin/run-external 900-solve --via codex --model m"):
            with self.subTest(cmd=cmd):
                self.assertIsNone(self.fire("Bash", {"command": cmd}), cmd)

    def test_ask_ledger_kind(self):
        dg = self.digest12("--ledger", "900-solve", "c1")
        out = self.fire("Bash", {"command": f"bin/approve --ledger 900-solve c1 --digest {dg}"})
        self.assertEqual(out["permissionDecision"], "ask")
        self.assertIn("ledger 900-solve ids c1", out["permissionDecisionReason"])


class T3OtherTools(HookCase):
    def test_writes_into_approvals(self):
        appr = os.path.join(self.root, ".claude", "state", "approvals")
        for tool, ti in (("Write", {"file_path": appr + "/launch-900-solve.json", "content": "{}"}),
                         ("Edit", {"file_path": ".claude/state/approvals/launch-900-solve.json", "old_string": "a", "new_string": "b"}),
                         ("Write", {"file_path": self.root + "/workspace-9/../.claude/state/approvals/used/x.json", "content": "{}"})):
            with self.subTest(tool=tool, path=ti["file_path"]):
                self.assertEqual(self.decision(tool, ti)[0], "deny")
        self.assertIsNone(self.fire("Write", {"file_path": self.rd + "/BRIEF.md", "content": "x"}))

    def test_packet_lists_are_the_operators(self):
        """LESSONS.md "No packet carries blocked material": the orchestrator may not edit the packet rules or their exceptions, or run bin/packet-block or
        bin/packet-except; a plain git add / commit / status / diff of the lists is allowed."""
        for name in ("packet-exceptions.json", "packet-rules.json"):
            lst = os.path.join(self.root, "data", name)
            for tool, ti in (("Write", {"file_path": lst, "content": "[]"}),
                             ("Edit", {"file_path": "data/" + name, "old_string": "a", "new_string": "b"}),
                             ("Bash", {"command": f"echo '[]' > data/{name}"}),
                             ("Bash", {"command": f"python3 -c \"open('data/{name}','w')\""}),
                             ("Bash", {"command": f"git add data/{name} && echo x"})):
                with self.subTest(tool=tool, ti=ti):
                    d, why = self.decision(tool, ti)
                    self.assertEqual(d, "deny")
                    self.assertIn("user", why)
            for cmd in (f"git add data/{name}", f"git diff --stat data/{name}", f"git commit -q -F /tmp/msg data/{name}"):
                with self.subTest(cmd=cmd):
                    self.assertIsNone(self.fire("Bash", {"command": cmd}))
        for cmd in ('bin/packet-except input/x.md "a ruling"', 'bin/packet-block notes/x.md "why"',
                    'bin/packet-block --extract C-042 "why"'):
            with self.subTest(cmd=cmd):
                self.assertEqual(self.decision("Bash", {"command": cmd})[0], "deny")
        self.assertIsNone(self.fire("Bash", {"command": "bin/lint-brief --packet 900-solve"}))   # the scan itself is the orchestrator's

    def test_environment_files_are_the_operators(self):
        """HANDOFF.md section 6 item 29, pending item P-1 (kit-v0.5): the files that decide what a worker's sandbox mounts
        and reaches (kit-env.json, and the older .kit-lean / .kit-sage / .kit-routes) are the user's. Before this, an
        orchestrator could write .kit-lean naming any directory, which the hook then mounted read-only into every
        worker's sandbox and put on its PATH. Reading them stays allowed; a plain git add / commit / status / diff too."""
        for name in ("kit-env.json", ".kit-lean", ".kit-sage", ".kit-routes"):
            p = os.path.join(self.root, name)
            for tool, ti in (("Write", {"file_path": p, "content": "/home"}),
                             ("Edit", {"file_path": name, "old_string": "a", "new_string": "b"}),
                             ("Bash", {"command": f"echo ~ > {name}"}),
                             ("Bash", {"command": f"cp /tmp/x {self.root}/{name}"}),
                             ("Bash", {"command": f"git add {name} && echo x"})):
                with self.subTest(tool=tool, ti=ti):
                    d, why = self.decision(tool, ti)
                    self.assertEqual(d, "deny", (tool, ti))
                    self.assertIn("user", why)
            for cmd in (f"git add {name}", f"git diff --stat {name}", f"cat {name}"):
                with self.subTest(cmd=cmd):
                    self.assertIsNone(self.fire("Bash", {"command": cmd}))
            self.assertNotEqual(self.decision("Read", {"file_path": p})[0], "deny")

    def test_resume_routes(self):
        self.assertEqual(self.decision("SendMessage", {"to": "worker", "message": "continue"})[0], "deny")
        self.assertEqual(self.decision("Workflow", {"script": "x"})[0], "deny")

    def test_worker_subagent_refused(self):
        """LESSONS.md "Every worker is a headless main process": no worker is launched through the Agent tool, approved or not, and a refusal spends no
        approval (bin/run-external consumes it instead)."""
        for atype in ("kit-worker", "kit-worker-high", "kit-worker-anything"):
            with self.subTest(atype=atype):
                d, why = self.decision("Agent", {"subagent_type": atype, "prompt": self.worker_prompt(), "model": "opus"})
                self.assertEqual(d, "deny")
                self.assertIn("LESSONS.md 'Every worker is a headless main process'", why)
                self.assertIn("bin/run-external", why)
        self.approve("900-solve", "--", "--model", "opus")
        self.assertEqual(self.decision("Agent", {"subagent_type": "kit-worker", "prompt": self.worker_prompt(),
                                                  "model": "opus"})[0], "deny")
        self.assertTrue(os.path.exists(self.record()))            # the approval is still there, unspent

    def test_agent_strip_still_happens(self):
        out = self.fire("Agent", {"subagent_type": "Explore", "prompt": "look", "name": "w", "isolation": "worktree"})
        self.assertEqual(out["permissionDecision"], "allow")
        self.assertEqual(set(out["updatedInput"]), {"subagent_type", "prompt"})

    def test_other_agent_types_untouched_here(self):
        self.assertIsNone(self.fire("Agent", {"subagent_type": "Explore", "prompt": "look around"}))

    def test_broken_gate_refuses_gated_calls_only(self):
        os.remove(os.path.join(self.root, "bin"))
        os.mkdir(os.path.join(self.root, "bin"))                  # no _approval.py to load
        d, why = self.decision("Bash", {"command": "bin/approve 900-solve --digest 0123456789ab"})
        self.assertEqual(d, "deny")
        self.assertIn("gate error", why)
        self.assertIsNone(self.fire("Bash", {"command": "git status"}))
        self.assertIsNone(self.fire("Read", {"file_path": self.rd + "/BRIEF.md"}))

    def test_former_effort_variants_are_not_workers(self):
        """The per-effort types of LESSONS.md "Networked and Codex launches need their flags bound" are retired: a subagent of that type gets no tools."""
        sub = {"agent_id": "a9", "agent_type": "kit-worker-xhigh", "transcript_path": "/x/subagents/a9.jsonl"}
        self.assertEqual(self.decision("Read", {"file_path": self.rd + "/BRIEF.md"}, **sub)[0], "deny")


class T3LedgerIsNotRead(HookCase):
    """LESSONS.md "`LEDGER.log` is append-only": agents write to LEDGER.log and never read it, the orchestrator included."""

    def test_denied(self):
        L = os.path.join(self.root, "LEDGER.log")
        for tool, ti in (("Read", {"file_path": L}), ("Read", {"file_path": "LEDGER.log"}),
                         ("Read", {"file_path": self.root + "/workspace-9/../LEDGER.log"}),
                         ("Grep", {"pattern": "LAUNCH", "path": L}),
                         ("Bash", {"command": "grep LAUNCH-EXT LEDGER.log"}), ("Bash", {"command": "tail -5 LEDGER.log"}),
                         ("Bash", {"command": "git diff LEDGER.log"}), ("Bash", {"command": "git log -p LEDGER.log"}),
                         ("Bash", {"command": "git diff --numstat LEDGER.log; cat LEDGER.log"})):
            with self.subTest(tool=tool, ti=ti):
                self.assertEqual(self.decision(tool, ti)[0], "deny")

    def test_allowed(self):
        for tool, ti in (("Bash", {"command": "git diff --numstat LEDGER.log"}), ("Bash", {"command": "git add LEDGER.log HANDOFF.md"}),
                         ("Bash", {"command": "git status --short"}), ("Bash", {"command": 'bin/ledger -r 900-solve NOTE "text"'}),
                         ("Read", {"file_path": self.root + "/CLAIMS.md"}), ("Grep", {"pattern": "x", "path": self.root + "/bin"}),
                         ("Grep", {"pattern": "x", "glob": "*.py"})):   # a bare Grep from the root: refused since P-4 (T11)
            with self.subTest(tool=tool, ti=ti):
                self.assertIsNone(self.fire(tool, ti))


class T3NetWorker(HookCase):
    """LESSONS.md "Networked and Codex launches need their flags bound": KIT_WORKER_NET=1 on an external worker adds WebSearch/WebFetch and a Bash sandbox that
    shares the network; nothing else changes, and without the marker nothing changes at all."""

    def ext(self, net):
        env = {"KIT_WORKER_RUN": self.rd, "KIT_NET_GATEWAY": "http://127.0.0.1:9/tok"}
        if net:
            env["KIT_WORKER_NET"] = "1"
        return env

    def test_networked(self):
        env = self.ext(True)
        self.assertEqual(self.decision("Read", {"file_path": self.rd + "/BRIEF.md"}, env=env)[0], "allow")
        for tool in ("WebFetch", "WebSearch"):
            self.assertEqual(self.decision(tool, {"url": "https://example.org", "query": "q"}, env=env)[0], "allow")
        out = self.fire("Bash", {"command": "curl -s https://example.org"}, env=env)
        self.assertEqual(out["permissionDecision"], "allow")
        cmd = out["updatedInput"]["command"]
        for needle in ("--share-net", "GATEWAY http://127.0.0.1:9/tok", "/opt/kit/bin/brave", "/etc/resolv.conf", "SSL_CERT_FILE"):
            self.assertIn(needle, cmd)
        self.assertEqual(self.decision("Read", {"file_path": self.root + "/CLAIMS.md"}, env=env)[0], "deny")
        self.assertEqual(self.decision("Agent", {"subagent_type": "x", "prompt": "p"}, env=env)[0], "deny")

    def test_not_networked(self):
        env = self.ext(False)
        self.fire("Read", {"file_path": self.rd + "/BRIEF.md"}, env=env)
        for tool in ("WebFetch", "WebSearch"):
            self.assertEqual(self.decision(tool, {"url": "https://example.org", "query": "q"}, env=env)[0], "deny")
        cmd = self.fire("Bash", {"command": "ls"}, env=env)["updatedInput"]["command"]
        self.assertNotIn("--share-net", cmd)
        self.assertNotIn("GATEWAY", cmd)

    def test_subagent_never_networked(self):
        sub = {"agent_id": "a1", "agent_type": "kit-worker", "transcript_path": "/x/subagents/a1.jsonl"}
        env = {"KIT_WORKER_NET": "1"}
        self.fire("Read", {"file_path": self.rd + "/BRIEF.md"}, env=env, **sub)
        self.assertEqual(self.decision("WebFetch", {"url": "https://example.org"}, env=env, **sub)[0], "deny")
        cmd = self.fire("Bash", {"command": "ls"}, env=env, **sub)["updatedInput"]["command"]
        self.assertNotIn("--share-net", cmd)


class T3SubagentEffort(HookCase):
    """Item 5 of 2026-09-22: at SubagentStop the hook ledgers the effort values the worker's requests carried."""

    def test_effort_ledgered(self):
        tr = os.path.join(self.root, "agent.jsonl")
        with open(tr, "w") as f:
            f.write('{"message":{"x":1},"effort":"low"}\n{"effort":"low"}\n{"other":1}\n')
        base = {"hook_event_name": "SubagentStop", "agent_id": "a7", "transcript_path": "/x/main.jsonl"}
        for atype, tp, want in (("kit-worker", tr, "effort_seen=low*2"),
                                ("kit-worker", self.root + "/missing.jsonl", "effort_seen=no-transcript"),
                                ("kit-worker-low", tr, None),
                                ("Explore", tr, None)):
            with self.subTest(atype=atype):
                inp = dict(base, agent_type=atype, agent_transcript_path=tp)
                subprocess.run(["/usr/bin/python3", self.hook], input=json.dumps(inp), text=True, capture_output=True,
                               env=dict(os.environ, KIT_ROOT=self.root))
                last = open(os.path.join(self.root, "LEDGER.log")).read().splitlines()[-1]
                self.assertIn(f"type={atype}", last)
                if want:
                    self.assertIn(want, last)
                else:
                    self.assertNotIn("effort_seen", last)

    def test_effort_path_derived(self):
        """No agent_transcript_path in the event: <session>/subagents/agent-<id>.jsonl beside the main transcript."""
        main = os.path.join(self.root, "sess.jsonl")
        os.makedirs(os.path.join(self.root, "sess", "subagents"))
        with open(os.path.join(self.root, "sess", "subagents", "agent-a7.jsonl"), "w") as f:
            f.write('{"effort":"high"}\n')
        inp = {"hook_event_name": "SubagentStop", "agent_id": "a7", "agent_type": "kit-worker", "transcript_path": main}
        subprocess.run(["/usr/bin/python3", self.hook], input=json.dumps(inp), text=True, capture_output=True,
                       env=dict(os.environ, KIT_ROOT=self.root))
        self.assertIn("effort_seen=high*1", open(os.path.join(self.root, "LEDGER.log")).read().splitlines()[-1])


class T3WorkerBranchUnchanged(HookCase):
    def test_golden(self):
        import hashlib
        with open(BASELINE_FIXTURE, "rb") as f:
            raw = f.read()
        self.assertEqual(hashlib.sha256(raw).hexdigest(), BASELINE_SHA256)
        lean = os.path.join(self.root, "lean")
        # outside the instance, where a real toolchain lives (~/.elan): bin/_env.py refuses a mount source inside it
        toolchain = os.path.join(tempfile.mkdtemp(prefix="toolchain-"), "toolchain")
        self.addCleanup(shutil.rmtree, os.path.dirname(toolchain), True)
        for d in (lean, os.path.join(toolchain, "bin")):
            os.makedirs(d, exist_ok=True)
        src = raw.decode().replace(BASELINE_ELAN_LINE, f"ELAN = {toolchain!r}")
        assert src != raw.decode(), "the baseline's toolchain line moved"
        old = patched(src, self.root, "hook_baseline.py", BASELINE_ROOT_LINE)
        with open(os.path.join(self.root, ".kit-lean"), "w") as f:
            f.write(toolchain + "\n")     # the tree, not the environment, says where the toolchain is
        sub = {"agent_id": "a1", "agent_type": "kit-worker", "transcript_path": "/x/subagents/a1.jsonl"}
        seq = [("Bash", {"command": "echo before binding"}, sub, None),
               ("Read", {"file_path": self.rd + "/BRIEF.md"}, sub, None),
               ("Bash", {"command": "bin/approve 900-solve; claude -p hi; ls .claude/state/approvals"}, sub, None),
               ("Read", {"file_path": self.root + "/CLAIMS.md"}, sub, None),
               ("Read", {"file_path": self.root + "/workspace-9/runs/901-ref/BRIEF.md"}, sub, None),
               ("Write", {"file_path": self.rd + "/output/result.md", "content": "x"}, sub, None),
               ("Grep", {"pattern": "x"}, sub, None),
               ("Agent", {"subagent_type": "kit-worker", "prompt": self.worker_prompt()}, sub, None),
               ("SendMessage", {"to": "x", "message": "y"}, sub, None),
               ("Bash", {"command": "ls"}, dict(sub, agent_id="a2", agent_type="Explore"), None),
               ("Read", {"file_path": self.rd + "/BRIEF.md"}, {}, {"KIT_WORKER_RUN": self.rd}),
               ("Bash", {"command": "bin/approve 900-solve"}, {}, {"KIT_WORKER_RUN": self.rd}),
               ("Agent", {"subagent_type": "kit-worker", "prompt": self.worker_prompt()}, {}, {"KIT_WORKER_RUN": self.rd})]
        outs = []
        for hook in (old, self.hook):
            shutil.rmtree(os.path.join(self.root, ".claude", "state"), ignore_errors=True)
            outs.append([self.fire(t, ti, hook=hook, env=env, **extra) for t, ti, extra, env in seq])
        self.assertEqual(len(outs[0]), len(seq))
        for (t, ti, _, _), a, b in zip(seq, *outs):
            self.assertIsNotNone(a, (t, ti))                      # every worker call gets an explicit decision
            self.assertEqual(a, strip_intended(b), (t, ti))


def strip_intended(out):
    """The one intended change to the worker branch since the baseline, removed so the rest must match byte for byte:
    LESSONS.md "The sandbox's root is remounted read-only after the binds" adds `--remount-ro /` to the worker's bwrap line, exactly once."""
    cmd = ((out or {}).get("updatedInput") or {}).get("command")
    if not cmd:
        return out
    assert cmd.count(" --remount-ro / ") == 1, cmd
    return dict(out, updatedInput=dict(out["updatedInput"], command=cmd.replace(" --remount-ro / ", " ", 1)))


class T3ForeignSession(HookCase):
    """LESSONS.md "The hook ledgers only its own tree's sessions": a session whose project directory and cwd both lie outside the tree writes nothing to its
    ledger, except the gate's own lines, marked foreign; decisions are unchanged. Either one inside makes it ours."""

    def fire_env(self, tool, ti, env, **extra):
        """Like fire(), but with exactly this CLAUDE_PROJECT_DIR (None: unset), whatever the calling shell has."""
        inp = dict({"hook_event_name": "PreToolUse", "session_id": "s1", "transcript_path": "/x/main.jsonl",
                    "cwd": self.root, "permission_mode": "default", "tool_name": tool, "tool_input": ti}, **extra)
        e = {k: v for k, v in os.environ.items() if k not in ("CLAUDE_PROJECT_DIR", "KIT_WORKER_RUN")}
        e["KIT_ROOT"] = self.root
        e.update({k: v for k, v in env.items() if v is not None})
        p = subprocess.run(["/usr/bin/python3", self.hook], input=json.dumps(inp), text=True, capture_output=True, env=e)
        self.assertEqual(p.returncode, 0, p.stderr)
        return json.loads(p.stdout)["hookSpecificOutput"] if p.stdout.strip() else None

    def ledger_lines(self):
        return open(os.path.join(self.root, "LEDGER.log")).read().splitlines()

    def test_foreign_session_is_not_ledgered(self):
        other = "/nonexistent/another-tree"
        for tool, ti in (("Bash", {"command": "ls", "description": "list"}), ("Read", {"file_path": other + "/x.md"}),
                         ("Write", {"file_path": other + "/y.md", "content": "c"})):
            with self.subTest(tool=tool):
                self.assertIsNone(self.fire_env(tool, ti, {"CLAUDE_PROJECT_DIR": other}, cwd=other))
        self.assertEqual(self.ledger_lines(), [])

    def test_gate_still_refuses_and_is_recorded_as_foreign(self):
        other = "/nonexistent/another-tree"
        out = self.fire_env("Bash", {"command": "cat LEDGER.log"}, {"CLAUDE_PROJECT_DIR": other}, cwd=other)
        self.assertEqual(out["permissionDecision"], "deny")
        out = self.fire_env("Bash", {"command": "claude -p hi"}, {"CLAUDE_PROJECT_DIR": other}, cwd=other)
        self.assertEqual(out["permissionDecision"], "deny")
        lines = self.ledger_lines()
        self.assertEqual(len(lines), 2, lines)
        for l in lines:
            self.assertIn(f"| foreign-session({other}) | - | DENY-GATE |", l)

    def test_foreign_subagent_decision_unchanged_and_quiet(self):
        other = "/nonexistent/another-tree"
        sub = {"agent_id": "k1", "agent_type": "Explore", "transcript_path": "/x/subagents/k1.jsonl", "cwd": other}
        out = self.fire_env("Bash", {"command": "ls"}, {"CLAUDE_PROJECT_DIR": other}, **sub)
        self.assertEqual(out["permissionDecision"], "deny")
        self.assertEqual(self.ledger_lines(), [])

    def test_foreign_subagent_start_stop_quiet(self):
        """SubagentStart / SubagentStop of a foreign session write nothing; the same events of ours are ledgered."""
        other = "/nonexistent/another-tree"
        for event in ("SubagentStart", "SubagentStop"):
            for proj, cwd, expect in ((other, other, 0), (self.root, self.root, 1)):
                with self.subTest(event=event, foreign=expect == 0):
                    before = len(self.ledger_lines())
                    self.fire_env("Bash", {}, {"CLAUDE_PROJECT_DIR": proj}, hook_event_name=event,
                                  agent_id="k2", agent_type="Explore", cwd=cwd)
                    self.assertEqual(len(self.ledger_lines()) - before, expect, self.ledger_lines())

    def test_foreign_session_does_not_archive_our_handoff(self):
        open(os.path.join(self.root, "HANDOFF.md"), "w").write("# handoff\n")
        other = "/nonexistent/another-tree"
        self.fire_env("Bash", {"command": "cat HANDOFF.md"}, {"CLAUDE_PROJECT_DIR": other}, cwd=other)
        state = os.path.join(self.root, ".claude", "state")
        self.assertFalse([f for f in os.listdir(state) if f.startswith("handoff-archived-")])
        self.assertEqual(self.ledger_lines(), [])

    def test_ours_when_either_is_inside(self):
        other = "/nonexistent/another-tree"
        cases = (("project inside, cwd outside (the orchestrator cd'd out)", self.root, other),
                 ("project outside, cwd inside (a foreign session working here)", other, os.path.join(self.root, "workspace-9")),
                 ("both inside", self.root, self.root),
                 ("project unset, cwd inside", None, self.root),
                 ("nothing known: fail closed", None, None))
        for i, (why, proj, cwd) in enumerate(cases):
            with self.subTest(why=why):
                extra = {"cwd": cwd} if cwd else {"cwd": ""}
                self.assertIsNone(self.fire_env("Bash", {"command": "ls", "description": f"case{i}"},
                                                {"CLAUDE_PROJECT_DIR": proj}, **extra))
                self.assertIn(f"| orchestrator | - | CALL | Bash case{i}", self.ledger_lines()[-1])

    def test_worker_is_never_foreign(self):
        other = "/nonexistent/another-tree"
        env = {"CLAUDE_PROJECT_DIR": other, "KIT_WORKER_RUN": self.rd}
        out = self.fire_env("Read", {"file_path": self.rd + "/BRIEF.md"}, env, cwd=other)
        self.assertEqual(out["permissionDecision"], "allow")
        self.assertTrue(any(("| CALL | Read " + self.rd) in l for l in self.ledger_lines()), self.ledger_lines())

    def test_symlinked_path_into_the_tree_is_ours(self):
        link = os.path.join(os.path.dirname(self.root), os.path.basename(self.root) + "-link")
        os.symlink(self.root, link)
        try:
            self.assertIsNone(self.fire_env("Bash", {"command": "ls", "description": "vialink"},
                                            {"CLAUDE_PROJECT_DIR": link}, cwd=link))
            self.assertIn("CALL | Bash vialink", self.ledger_lines()[-1])
        finally:
            os.unlink(link)



class T9ClatterGate(HookCase):
    """LESSONS.md "An orchestrator types into no other pane and touches no mailbox" (the user's approval of 2026-09-30, after
    the kit's evaluation of Clatter, HANDOFF.md section 6 item 26, gap 2): an instance orchestrator may use the bus only
    through its dispatcher (peers, ask, send, broadcast, recv, status, doctor); raw `tmux send-keys` (or a paste) into a pane,
    any other touch of ~/.claude/clatter/ (mailboxes, registry, relay, mode files) and the dispatcher's `mode` and `clear` are
    refused. Nothing here is sent; the hook only decides."""

    BUS = os.path.expanduser("~/.claude/clatter/scripts/bus.sh")
    MBOX = os.path.expanduser("~/.claude/clatter/mailbox/0000-0000/1-x.json")

    def test_dispatcher_allowed(self):
        for sub in ("peers", "status", "recv", "doctor", "send peer-session 'run 017 held'",
                    "ask peer-session 'which order?'", "broadcast 'hello'"):
            with self.subTest(sub=sub):
                self.assertNotEqual(self.decision("Bash", {"command": f"bash {self.BUS} {sub}"})[0], "deny")

    def test_dispatcher_mode_and_clear_refused(self):
        for sub in ("mode auto", "mode manual", "clear"):
            with self.subTest(sub=sub):
                d, why = self.decision("Bash", {"command": f"bash {self.BUS} {sub}"})
                self.assertEqual(d, "deny", sub)
                self.assertIn("Clatter", why)

    def test_tmux_keys_refused(self):
        for cmd in ("tmux send-keys -t %3 Enter", "tmux send-keys -t %3 -l \"$(cat /tmp/c.txt)\"",
                    "tmux send -t %3 x", "tmux paste-buffer -t %3", "tmux load-buffer /tmp/x && tmux paste-buffer -t %3",
                    "/usr/bin/tmux set-buffer x"):
            with self.subTest(cmd=cmd):
                d, why = self.decision("Bash", {"command": cmd})
                self.assertEqual(d, "deny", cmd)
                self.assertIn("pane", why)
        self.assertNotEqual(self.decision("Bash", {"command": "tmux ls"})[0], "deny")   # reading is not typing

    def test_clatter_files_refused(self):
        d, _ = self.decision("Write", {"file_path": self.MBOX, "content": "{}"})
        self.assertEqual(d, "deny")
        for cmd in (f"echo '{{}}' > {self.MBOX}", "cat ~/.claude/clatter/relay/relay.log",
                    "echo '*/x*' >> ~/.claude/clatter/manual-patterns", "bash ~/.claude/clatter/scripts/bus-mode.sh manual",
                    "bash ~/.claude/clatter/scripts/bus-clear.sh", "bash ~/.claude/clatter/scripts/bus-send.shx a b"):
            with self.subTest(cmd=cmd):
                self.assertEqual(self.decision("Bash", {"command": cmd})[0], "deny", cmd)

    def test_clatter_reads_refused(self):
        """The source's method change 69 (kit-v0.4.19): "any touch" covers reading too, so another session's mailbox and
        the relay's log are not read with Read, Grep or Glob; a `~` path is expanded first; a Grep or Glob rooted above
        ~/.claude/clatter/ (which would walk into it) is refused as well."""
        home = os.path.expanduser("~")
        for tool, ti in (("Read", {"file_path": self.MBOX}),
                         ("Read", {"file_path": "~/.claude/clatter/relay/relay.log"}),
                         ("Grep", {"pattern": "from", "path": os.path.join(home, ".claude", "clatter")}),
                         ("Glob", {"pattern": "**/*.json", "path": "~/.claude/clatter/mailbox"}),
                         ("Grep", {"pattern": "approve", "path": os.path.join(home, ".claude")}),
                         ("Glob", {"pattern": ".claude/clatter/**", "path": home}),
                         ("Write", {"file_path": "~/.claude/clatter/mailbox/0000/1-x.json", "content": "{}"})):
            with self.subTest(tool=tool, ti=ti):
                d, why = self.decision(tool, ti)
                self.assertEqual(d, "deny", (tool, ti))
                self.assertIn("clatter", why)
        for tool, ti in (("Read", {"file_path": self.rd + "/BRIEF.md"}), ("Grep", {"pattern": "x", "path": self.rd}),
                         ("Glob", {"pattern": "*.md", "path": self.rd})):
            with self.subTest(tool=tool, ti=ti):
                self.assertNotEqual(self.decision(tool, ti)[0], "deny", (tool, ti))

    SEND = os.path.expanduser("~/.claude/clatter/scripts/bus-send.sh")

    def test_send_script_allowed(self):
        """HANDOFF.md section 6 item 27 (a): the send script itself, for a threaded reply (`--reply-to`), which the
        dispatcher cannot give."""
        for cmd in (f"bash {self.SEND} peer-session response 're: 017' 'held' --reply-to 1727700000000-ab12",
                    f"bash {self.SEND} peer-session notify 'report' \"$(cat /tmp/report.md)\"",
                    "bash $HOME/.claude/clatter/scripts/bus-send.sh peer-session notify s 'b'"):
            with self.subTest(cmd=cmd):
                self.assertNotEqual(self.decision("Bash", {"command": cmd})[0], "deny", cmd)

    def test_send_script_sender_flags_refused(self):
        """Its `--from` and `--from-session` set any sender name and session id: refused, in any spelling the shell
        joins back into the flag."""
        for tail in ("--from peer-session", "--from-session 0000-0000", "--reply-to 1-ab --from x", "\"--from\" x",
                     "'--fr''om' x", "--fr\\om x", "--from=x"):
            cmd = f"bash {self.SEND} peer-session notify s 'b' {tail}"
            with self.subTest(cmd=cmd):
                d, why = self.decision("Bash", {"command": cmd})
                self.assertEqual(d, "deny", cmd)
                self.assertIn("sender", why)

    def test_worker_unchanged(self):
        """The worker's branch is not this gate's: a worker's tmux or bus command is rewritten into its sandbox, where
        neither exists (the kit's probe of 2026-09-30)."""
        env = {"KIT_WORKER_RUN": self.rd}
        self.fire("Read", {"file_path": self.rd + "/BRIEF.md"}, env=env)
        out = self.fire("Bash", {"command": "tmux send-keys -t %3 Enter"}, env=env)
        self.assertIn("bwrap", ((out or {}).get("updatedInput") or {}).get("command", ""))



class T11P4Gaps(HookCase):
    """Pending item P-4 (user 2026-10-01: "yes" to the recommendations): (1) a Grep from the tree root, or above it, read
    LEDGER.log's lines: refused unless a glob or type filter matches no protected file (the ledger, a locked file, an
    approval record); (2) nothing refused the orchestrator data/locked/: Read, Grep and Glob inside it and Bash naming it
    are refused, but a plain `bin/new-run … --role evaluator` and plain git add / commit / status / diff; (4b) a Read
    of the approvals directory was allowed, though RULES.md §9 says anything touching it is refused."""

    def setUp(self):
        super().setUp()
        self.locked = os.path.join(self.root, "data", "locked")
        os.makedirs(self.locked, exist_ok=True)
        open(os.path.join(self.locked, "key.json"), "w").write('{"answer": 42}\n')
        self.appr = os.path.join(self.root, ".claude", "state", "approvals")
        os.makedirs(self.appr, exist_ok=True)
        open(os.path.join(self.appr, "launch-900-solve.json"), "w").write("{}\n")

    def deny(self, tool, ti):
        return self.decision(tool, ti)[0] == "deny"

    def test_grep_from_the_root_needs_a_safe_filter(self):
        R = self.root
        self.assertTrue(self.deny("Grep", {"pattern": "x"}))                                   # cwd is the root
        self.assertTrue(self.deny("Grep", {"pattern": "x", "path": R}))
        self.assertTrue(self.deny("Grep", {"pattern": "x", "path": os.path.dirname(R)}))       # above the root
        self.assertTrue(self.deny("Grep", {"pattern": "x", "path": R, "glob": "*.log"}))       # matches the ledger
        self.assertTrue(self.deny("Grep", {"pattern": "x", "path": R, "glob": "*"}))
        self.assertTrue(self.deny("Grep", {"pattern": "x", "path": R, "glob": "*.json"}))      # a locked file, an approval
        self.assertTrue(self.deny("Grep", {"pattern": "x", "path": R, "glob": "*.{py,json}"}))
        self.assertTrue(self.deny("Grep", {"pattern": "x", "path": R, "type": "nosuchtype"}))  # unknown type: no filter
        self.assertFalse(self.deny("Grep", {"pattern": "x", "path": R, "glob": "*.py"}))
        self.assertFalse(self.deny("Grep", {"pattern": "x", "path": R, "glob": "*.{py,md}"}))
        self.assertFalse(self.deny("Grep", {"pattern": "x", "path": R, "type": "py"}))
        self.assertFalse(self.deny("Grep", {"pattern": "x", "path": os.path.join(R, "workspace-9")}))   # below: as before
        self.assertFalse(self.deny("Glob", {"pattern": "**/*.md", "path": R}))                 # names only: allowed

    def test_locked_data_refused(self):
        k = os.path.join(self.locked, "key.json")
        self.assertTrue(self.deny("Read", {"file_path": k}))
        self.assertTrue(self.deny("Grep", {"pattern": "x", "path": self.locked}))
        self.assertTrue(self.deny("Glob", {"pattern": "*", "path": self.locked}))
        for cmd in ("cat data/locked/key.json", f"ls {self.locked}", "cp data/locked/key.json /tmp/x",
                    "bin/new-run workspace-9 s --role solver --input data/locked/key.json",
                    "bin/new-run workspace-9 e --role evaluator --input data/locked/key.json; cat data/locked/key.json"):
            with self.subTest(cmd=cmd):
                self.assertTrue(self.deny("Bash", {"command": cmd}), cmd)
        for cmd in ("bin/new-run workspace-9 ev --role evaluator --input data/locked/key.json",
                    "git add data/locked/SHA256SUMS", "git status --short data/locked"):
            with self.subTest(cmd=cmd):
                self.assertFalse(self.deny("Bash", {"command": cmd}), cmd)

    def test_approvals_directory_not_read(self):
        f = os.path.join(self.appr, "launch-900-solve.json")
        self.assertTrue(self.deny("Read", {"file_path": f}))
        self.assertTrue(self.deny("Grep", {"pattern": "x", "path": self.appr}))
        self.assertTrue(self.deny("Glob", {"pattern": "*", "path": self.appr}))


class T12LockedOutside(HookCase):
    """Pending item P-9 (user 2026-10-01: "a"): with the locked directory outside the tree (kit-env.json `locked_dir`), the
    hook guards it at its own path: Read, Grep and Glob there, a Grep rooted above it without a safe filter, and a command
    naming it but a plain `bin/new-run … --role evaluator`, are refused."""

    def setUp(self):
        super().setUp()
        self.out = os.path.realpath(tempfile.mkdtemp(prefix="locked-out-"))
        self.locked = os.path.join(self.out, "locked")
        os.makedirs(self.locked)
        open(os.path.join(self.locked, "key.json"), "w").write("{}\n")
        json.dump({"locked_dir": self.locked}, open(os.path.join(self.root, "kit-env.json"), "w"))

    def tearDown(self):
        shutil.rmtree(self.out, ignore_errors=True)
        super().tearDown()

    def deny(self, tool, ti):
        return self.decision(tool, ti)[0] == "deny"

    def test_guarded_at_its_own_path(self):
        k = os.path.join(self.locked, "key.json")
        self.assertTrue(self.deny("Read", {"file_path": k}))
        self.assertTrue(self.deny("Grep", {"pattern": "x", "path": self.locked}))
        self.assertTrue(self.deny("Glob", {"pattern": "*", "path": self.locked}))
        self.assertTrue(self.deny("Grep", {"pattern": "x", "path": self.out}))            # rooted above it
        self.assertTrue(self.deny("Bash", {"command": f"cat {k}"}))
        self.assertTrue(self.deny("Bash", {"command": f"ls {self.locked}"}))
        self.assertFalse(self.deny("Bash", {"command": f"bin/new-run workspace-9 ev --role evaluator --input {k}"}))
        self.assertFalse(self.deny("Grep", {"pattern": "x", "path": self.out, "glob": "*.py"}))


class T13P12Critical(HookCase):
    """P-12, the code audit of 2026-10-02 (user 2026-10-02: "let's do the p12 fixes now"), the hook's part of the critical
    findings. (C1) the Monitor tool runs a shell command, and the gate examined Bash only: a Monitor call could read the
    ledger or the locked data, or name the approval tool. (C2) a worker's Read and Write are checked by real path, then
    used; a worker command left running in the background could swap a path between the two, so a worker's Bash runs in
    the foreground only (its sandbox, and everything in it, ends with the call); and the outbox is drained without
    following a symlink even when one appears after the check."""

    def mon(self, cmd):
        return {"command": cmd, "description": "d", "timeout_ms": 1000}

    def test_c1_monitor_is_gated_like_bash(self):
        for cmd in ("tail -f LEDGER.log", "cat data/locked/key.json", "ls .claude/state/approvals",
                    "bin/approve 900-solve --digest 000000000000", "claude -p hi", "tmux send-keys -t 1 x Enter",
                    "cat kit-env.json > /tmp/x; echo {} > kit-env.json"):
            with self.subTest(cmd=cmd):
                self.assertEqual(self.decision("Monitor", self.mon(cmd))[0], "deny")
        self.assertIsNone(self.fire("Monitor", self.mon("tail -f build.log | grep --line-buffered ERROR")))

    def test_c1_the_tap_is_offered_from_bash_only(self):
        cmd = f"bin/approve 900-solve --digest {self.digest12('900-solve')} -- {' '.join(G.F)}"
        self.assertEqual(self.decision("Bash", {"command": cmd})[0], "ask")
        # the absolute form bin/manifest prints is offered too, from any directory (P-14 follow-up)
        self.assertEqual(self.decision("Bash", {"command": f"{self.root}/{cmd}"}, cwd="/tmp")[0], "ask")
        d, why = self.decision("Monitor", self.mon(cmd))
        self.assertEqual(d, "deny")
        self.assertIn("Bash", why)
        self.assertFalse(os.path.exists(self.record()))

    def test_c2_worker_bash_runs_in_the_foreground(self):
        env = {"KIT_WORKER_RUN": self.rd}
        self.fire("Read", {"file_path": self.rd + "/BRIEF.md"}, env=env)
        out = self.fire("Bash", {"command": "sleep 1", "run_in_background": True}, env=env)
        self.assertEqual(out["permissionDecision"], "allow")
        self.assertIs(out["updatedInput"].get("run_in_background"), False)
        out = self.fire("Bash", {"command": "ls"}, env=env)   # absent stays absent (the golden replay's inputs)
        self.assertNotIn("run_in_background", out["updatedInput"])

    def test_c2_outbox_symlink_not_followed_after_the_check(self):
        import importlib.util
        victim = os.path.join(self.root, "victim.txt")
        open(victim, "w").write("the user's file\n")
        ob = os.path.join(self.rd, ".ledger-outbox")
        os.remove(ob)
        os.symlink(victim, ob)
        spec = importlib.util.spec_from_file_location("hook_c2", self.hook)
        H = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(H)
        real_islink = os.path.islink
        os.path.islink = lambda p: False   # the link appears between the check and the open
        try:
            H.drain_outbox("agent:x", self.rd)
        finally:
            os.path.islink = real_islink
        self.assertEqual(open(victim).read(), "the user's file\n")
        self.assertNotIn("the user's file", open(os.path.join(self.root, "LEDGER.log")).read())

    def test_c3_bindings_and_rulings_are_not_the_orchestrators(self):
        """The referee bindings are bin/new-run's, the cross-family rulings the user's: the orchestrator reads them and
        commits them, never writes them by hand."""
        b = os.path.join(self.root, "data", "referee-bindings", "901-ref.json")
        r = os.path.join(self.root, "data", "cross-family-rulings.json")
        for tool, ti in (("Write", {"file_path": b, "content": "{}"}), ("Edit", {"file_path": b, "old_string": "a", "new_string": "b"}),
                         ("Write", {"file_path": r, "content": "{}"}),
                         ("Bash", {"command": f"echo '{{}}' > {b}"}), ("Bash", {"command": "rm data/referee-bindings/901-ref.json"}),
                         ("Bash", {"command": "python3 -c 'open(\"data/cross-family-rulings.json\",\"w\")'"}),
                         ("Monitor", {"command": "sed -i s/a/b/ data/cross-family-rulings.json", "description": "d", "timeout_ms": 1000})):
            with self.subTest(tool=tool, ti=ti):
                self.assertEqual(self.decision(tool, ti)[0], "deny")
        for cmd in ("cat data/cross-family-rulings.json", "git add data/referee-bindings data/cross-family-rulings.json",
                    "ls data/referee-bindings", "git status --short"):
            with self.subTest(cmd=cmd):
                self.assertIsNone(self.fire("Bash", {"command": cmd}))
        self.assertIsNone(self.fire("Read", {"file_path": b}))


class T14P12High(HookCase):
    """P-12 H6 (the code audit of 2026-10-02; user 2026-10-02: "commit and move to high findings"): "a plain git add,
    commit, status or diff --stat" of the ledger or a locked file was a pattern on the command's start, so any option
    after it passed: `git diff --stat -p` printed the ledger's lines, as `--patch`, `-U`, `--word-diff`, `--output=`,
    `git status -v`, `git add -p` and `git commit -v` could. Now the options are a list of the ones that print no
    contents."""

    def test_options_that_print_contents_are_refused(self):
        for cmd in ("git diff --stat -p LEDGER.log", "git diff --numstat --patch LEDGER.log", "git diff --stat -U3 LEDGER.log",
                    "git diff --stat --word-diff LEDGER.log", "git diff --stat --output=/tmp/x LEDGER.log",
                    "git diff --stat --ext-diff LEDGER.log", "git diff --stat --textconv LEDGER.log",
                    "git status -v LEDGER.log", "git add -p LEDGER.log", "git add --patch LEDGER.log",
                    "git add -i LEDGER.log", "git commit -v -m x LEDGER.log", "git commit -p LEDGER.log",
                    "git diff LEDGER.log", "git diff --stat -p data/locked/key.json", "git -c x=y diff --stat LEDGER.log"):
            with self.subTest(cmd=cmd):
                self.assertEqual(self.decision("Bash", {"command": cmd})[0], "deny")

    def test_plain_forms_still_allowed(self):
        for cmd in ("git add LEDGER.log", "git add -A LEDGER.log", "git diff --stat LEDGER.log",
                    "git diff --numstat -- LEDGER.log", "git diff --stat=120 --cached LEDGER.log",
                    "git commit -F /tmp/m LEDGER.log", "git commit -q -m 'ledger lines' -- LEDGER.log",
                    "git status --short LEDGER.log", "git add data/locked", "git diff --stat HEAD~1 -- data/locked"):
            with self.subTest(cmd=cmd):
                self.assertIsNone(self.fire("Bash", {"command": cmd}))


class T15P12Medium(HookCase):
    """P-12 mediums (the code audit of 2026-10-02; user 2026-10-02: "let's hit a few of the medium issues"): the
    orchestrator's Write or Edit of LEDGER.log was not refused; a Glob rooted above the ledger, a locked file or an approval
    record was (the rooted-above check was Grep's only); and an unreadable kit-env.json, or a refused `locked_dir`, moved the
    locked-data guard to <root>/data/locked, leaving the real place unguarded."""

    def test_ledger_not_written_by_hand(self):
        led = os.path.join(self.root, "LEDGER.log")
        for tool, ti in (("Write", {"file_path": led, "content": ""}),
                         ("Edit", {"file_path": led, "old_string": "a", "new_string": "b"}),
                         ("MultiEdit", {"file_path": led, "edits": []})):
            with self.subTest(tool=tool):
                self.assertEqual(self.decision(tool, ti)[0], "deny")

    def test_glob_rooted_above_the_protected_files(self):
        for ti in ({"pattern": "*", "path": self.root}, {"pattern": "**/*"}, {"pattern": "LEDGER*", "path": self.root},
                   {"pattern": "**/*.log"}):
            with self.subTest(ti=ti):
                self.assertEqual(self.decision("Glob", ti)[0], "deny")
        for ti in ({"pattern": "**/*.py", "path": self.root}, {"pattern": "*.md"}, {"pattern": "*", "path": self.rd}):
            with self.subTest(ti=ti):
                self.assertIsNone(self.fire("Glob", ti))

    def test_an_unreadable_env_file_guards_every_locked_place(self):
        sys.path.insert(0, G.BIN)
        import _env
        default = _env.default_locked_dir(self.root)
        for content in ("{", '{"locked_dir": "/"}'):
            open(os.path.join(self.root, "kit-env.json"), "w").write(content)
            for p in (os.path.join(default, "key.json"), os.path.join(self.root, "data", "locked", "key.json")):
                with self.subTest(content=content, p=p):
                    self.assertEqual(self.decision("Read", {"file_path": p})[0], "deny")
                    self.assertEqual(self.decision("Bash", {"command": f"cat {p}"})[0], "deny")


class T16P12LowGate(HookCase):
    """P-12 (a low finding): when LEDGER.log could not be written, the hook's first act, logging the call, raised, and its
    catch-all denied every orchestrator call, the commands to see and fix the problem included. Now, as RULES.md §9 says
    of a failing gate, a gated call is refused and any other goes on, with a message to the user that it is not recorded."""

    def test_a_ledger_failure_refuses_gated_calls_only(self):
        led = os.path.join(self.root, "LEDGER.log")
        os.remove(led)
        os.mkdir(led)   # unwritable as a file
        p = subprocess.run(["/usr/bin/python3", self.hook], input=json.dumps(
            {"hook_event_name": "PreToolUse", "session_id": "s1", "transcript_path": "/x/main.jsonl", "cwd": self.root,
             "permission_mode": "default", "tool_name": "Bash", "tool_input": {"command": "git status --short"}}),
            text=True, capture_output=True, env=dict(os.environ, KIT_ROOT=self.root))
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn("not recorded", json.loads(p.stdout)["systemMessage"])
        self.assertNotIn("hookSpecificOutput", json.loads(p.stdout))   # no decision: the call goes on
        self.assertEqual(self.decision("Bash", {"command": "cat LEDGER.log"})[0], "deny")   # the gate still decides
        self.assertEqual(self.decision("Bash", {"command": "git show HEAD"})[0], "deny")
        self.assertEqual(self.decision("Read", {"file_path": os.path.join(self.root, "LEDGER.log")})[0], "deny")


class T17P11P10(HookCase):
    """Pending items P-11 (c), (d) and P-10 (user 2026-10-02: "let's do 4, 5, 6, 7"). (c) the hook read RUN/.limits on every
    worker Bash call, and the worker can write that file, so its per-command CPU ceiling and thread caps were the
    worker's to raise; now a launch-time copy outside the run is read. (d) a hook that failed to load made no decision,
    and Claude Code lets a call through on that; unparseable input did the same. (P-10) a plain `git diff` of the
    packet lists, the environment files or the records was refused, though reading them is allowed and the messages
    said so."""

    def test_c_the_launch_copy_of_the_limits_rules(self):
        sd = os.path.join(self.root, ".claude", "state", "ext", "900-solve")
        os.makedirs(sd)
        open(os.path.join(sd, "limits.json"), "w").write('{"cpu_hours": 1, "threads": 2, "mem_gb": 1}\n')
        open(os.path.join(self.rd, ".limits"), "w").write('{"cpu_hours": 1000, "threads": 64, "mem_gb": 512}\n')   # the worker's
        env = {"KIT_WORKER_RUN": self.rd}
        self.fire("Read", {"file_path": self.rd + "/BRIEF.md"}, env=env)
        cmd = self.fire("Bash", {"command": "ls"}, env=env)["updatedInput"]["command"]
        self.assertIn("ulimit -t 3600", cmd)
        self.assertIn("KIT_THREADS 2", cmd)

    def test_d_unparseable_input_blocks(self):
        p = subprocess.run(["/usr/bin/python3", self.hook], input="{not json", text=True, capture_output=True)
        self.assertEqual(p.returncode, 2)
        self.assertIn("refused", p.stderr)

    def test_p10_a_plain_diff_of_readable_files(self):
        os.makedirs(os.path.join(self.root, "data"), exist_ok=True)
        for f in ("data/packet-rules.json", "kit-env.json", "data/cross-family-rulings.json"):
            open(os.path.join(self.root, f), "w").write("{}\n")
        for cmd in ("git diff data/packet-rules.json", "git diff --cached kit-env.json", "git diff data/cross-family-rulings.json"):
            with self.subTest(cmd=cmd):
                self.assertIsNone(self.fire("Bash", {"command": cmd}))
        for cmd in ("git diff LEDGER.log", "git diff data/locked/key.json", "git diff --output=/tmp/x data/packet-rules.json"):
            with self.subTest(cmd=cmd):
                self.assertEqual(self.decision("Bash", {"command": cmd})[0], "deny")


class T18P13GitContents(HookCase):
    """Pending item P-13, route (a) (user 2026-10-02 21:34: "cheap route"): the ledger and the locked data were unread by
    name only, so a git command that names neither printed them: `git show HEAD`, `git log -p`, a bare `git diff` (the
    ledger always has uncommitted lines), `git grep`. In this tree a git command that prints file contents must now name
    its paths, none of them protected, nor a directory holding one; git run on another repository is not this tree's."""

    def deny(self, cmd):
        return self.decision("Bash", {"command": cmd})[0] == "deny"

    def test_contents_without_paths_refused(self):
        for cmd in ("git show HEAD", "git show", "git log -p", "git log --patch -3", "git log -U5", "git diff", "git diff HEAD~1",
                    "git diff --cached", "git grep answer", "git cat-file -p HEAD:x", "git archive HEAD", "git format-patch -1",
                    "git whatchanged", "git reflog -p", "git stash show -p", "git log -p | head -50", "git diff -- .",
                    "git diff -- data", "git diff -- 'L*'", "git show HEAD -- ':(glob)**'", "bash -c 'git show HEAD'",
                    "git -c alias.z=show z HEAD", "git z HEAD", "git --no-pager log -p", "X=1 git show HEAD",
                    "git log -p -- . ':!LEDGER.log'", "git difftool HEAD"):
            with self.subTest(cmd=cmd):
                self.assertTrue(self.deny(cmd), cmd)

    def test_plain_and_named_forms_allowed(self):
        kit = G.REAL
        os.makedirs(os.path.join(self.root, "data"), exist_ok=True)
        open(os.path.join(self.root, "data", "packet-rules.json"), "w").write("{}\n")
        for cmd in ("git status --short", "git log --oneline -5", "git log --stat -3", "git show --stat HEAD",
                    "git show HEAD:bin/check", "git diff --stat", "git diff --name-only", "git diff -- HANDOFF.md bin/",
                    "git log -p -- HANDOFF.md", "git grep -n answer -- bin", "git blame bin/check", "git add HANDOFF.md",
                    "git commit -F /tmp/m", "git rev-parse --short HEAD", "git describe --tags --exact-match",
                    f"git -C {kit} show kit-v0.6.12:bin/check", f"git -C {kit} diff --name-status a b -- bin",
                    "git diff data/packet-rules.json"):
            with self.subTest(cmd=cmd):
                self.assertFalse(self.deny(cmd), cmd)


class T19P14GitC(HookCase):
    """P-14 (d): `git -C <root> add LEDGER.log` was refused though `git add LEDGER.log` from the root passes: the plain-git
    allowance read only a command that starts `git add`. `-C` naming the tree's own root is now read as the plain form;
    any other directory is not."""

    def test_c_naming_the_root(self):
        R = self.root
        for cmd in (f"git -C {R} add LEDGER.log", f"git -C {R} commit -F /tmp/m LEDGER.log", f"git -C {R} diff --stat LEDGER.log",
                    f"git -C '{R}' status --short LEDGER.log"):
            with self.subTest(cmd=cmd):
                self.assertIsNone(self.fire("Bash", {"command": cmd}))
        for cmd in ("git -C /tmp add LEDGER.log", f"git -C {R} diff -p LEDGER.log", f"git -C {R}/bin add LEDGER.log",
                    f"git -C {R} -C x add LEDGER.log"):
            with self.subTest(cmd=cmd):
                self.assertEqual(self.decision("Bash", {"command": cmd})[0], "deny")


if __name__ == "__main__":
    unittest.main(verbosity=2, warnings="ignore")
