#!/usr/bin/env python3
"""Synthetic tests of the user-approval gate (LESSONS.md "Every launch and every ledger append consumes a byte-bound"). Stdlib only; run from anywhere:

    python3 tests/test_gate.py

Everything runs against a throwaway fixture root (KIT_ROOT); the real LEDGER.log, CLAIMS.md and
approvals directory are never touched, and nothing is launched. bin/approve is called here as a
subprocess on the FIXTURE root only: that is the test standing in for the user, not an approval.
"""
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import unittest

REAL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BIN = os.path.join(REAL, "bin")
sys.path.insert(0, BIN)


def bind(root, ref, source, claim, question="certify", artifact_sha256=None, deps_sha256=None):
    """The host's record of a referee run (P-12 C3), as bin/new-run writes it: data/referee-bindings/<run>.json."""
    d = os.path.join(root, "data", "referee-bindings")
    os.makedirs(d, exist_ok=True)
    json.dump({"schema": "kit/referee-binding/1", "referee_run": ref, "question": question, "source_run": source,
               "claim": claim, "artifact_sha256": artifact_sha256, "deps_sha256": deps_sha256 or {}},
              open(os.path.join(d, ref + ".json"), "w"))


def make_root():
    root = os.path.realpath(tempfile.mkdtemp(prefix="gate-fixture-"))
    rd = os.path.join(root, "workspace-9", "runs", "900-solve")
    for d in ("input", "output", "scratch"):
        os.makedirs(os.path.join(rd, d))
    w = lambda rel, s, base=rd: open(os.path.join(base, rel), "w").write(s)
    w("BRIEF.md", "brief v1\n")
    w(".limits", '{"cpu_hours": 1, "threads": 1, "mem_gb": 1}\n')
    w("input/a.txt", "input a\n")
    w("launch.log", "excluded\n")
    w(".ledger-outbox", "")
    # A claims/2 document that is valid under the current rules (P-12 H1: bin/ledger-claims re-validates it): two VERIFIED
    # script claims with a mutation each, produced by an Anthropic run and read for their sentence by an OpenAI one.
    script = "print('count=3')\n"
    w("output/s.py", script)
    sha = hashlib.sha256(script.encode()).hexdigest()
    claim = {"id": "c1", "tag": "VERIFIED", "statement": "fixture statement", "range": "the fixture",
             "coverage": "asserted", "silent_links": ["none"], "premises": [{"kind": "software", "what": "Python 3.12"}],
             "artifact": {"type": "script", "path": "output/s.py", "cmd": "python3 output/s.py",
                          "mutations": [{"name": "m", "cmd": "false", "expect_stdout_contains": "FAIL"}]}}
    w("output/claims.json", json.dumps({"schema": "kit/claims/2", "run": "900-solve", "problem": "x",
                                        "claims": [claim, dict(claim, id="c2")]}))
    w("check.json", json.dumps({"generated": "now", "overall": "pass", "doc_errors": [],
                                "claims": [{"id": "c1", "check": "pass", "artifact_sha256": sha},
                                           {"id": "c2", "check": "pass", "artifact_sha256": sha}]}))
    w("verdict.md", "| c1 | VERIFIED | pass | holds |\n")
    w("time.log", '\tCommand being timed: "claude -p go --model opus --effort high"\n')
    ref = os.path.join(root, "workspace-9", "runs", "901-ref")
    for d in ("input", "output"):
        os.makedirs(os.path.join(ref, d))
    w("BRIEF.md", "referee brief\n", ref)
    w("time.log", '\tCommand being timed: "bin/_ext.py codex RD --model gpt-5.6-sol --effort high"\n', ref)
    w("input/claim.json", json.dumps({"source_run": "900-solve", "id": "c1", "artifact": {"type": "none"}}), ref)
    w("output/referee.json", json.dumps({"schema": "kit/referee/1", "run": "900-solve", "claim": "c1",
                                         "verdict": "holds", "pointer": "n/a", "note": ""}), ref)
    bind(root, "901-ref", "900-solve", "c1", "sentence", sha)
    w("CLAIMS.md", "# CLAIMS\n\n## C-001  [VERIFIED]  2026-01-01  run 000-x/c1\nold\n", root)
    w("LEDGER.log", "", root)
    return root, rd


def tool(root, name, *args, stdin=None):
    env = dict(os.environ, KIT_ROOT=root)
    return subprocess.run(["/usr/bin/python3", os.path.join(BIN, name), *args], env=env, text=True,
                          capture_output=True, stdin=stdin or subprocess.DEVNULL)


F = ["--model", "m"]   # the launch flags every fixture approval binds


def sandbox_installed(root):
    """Whether bin/run-external's preflight passes in this tree: the kit itself has no live settings (by design), an
    instance has them. A launch refusal test expects "no user approval" (exit 3) in an instance and the preflight's
    "sandbox is not installed" (exit 2) in the kit: either way before any approval is touched."""
    s = os.path.join(root, ".claude", "settings.json")
    return os.path.isfile(s) and os.path.join(root, ".claude", "hooks", "sandbox.py") in open(s).read()


def refusal(root):
    return (3, "no user approval") if sandbox_installed(root) else (2, "sandbox is not installed")


class Base(unittest.TestCase):
    def setUp(self):
        self.root, self.rd = make_root()
        os.environ["KIT_ROOT"] = self.root
        for m in ("_approval", "_lib"):
            sys.modules.pop(m, None)
        import _approval
        self.A = _approval
        self.assertEqual(self.A.ROOT, self.root)

    def tearDown(self):
        os.environ.pop("KIT_ROOT", None)
        shutil.rmtree(self.root)

    def man(self):
        return self.A.launch_manifest(self.rd)

    def approve(self, *args):
        p = tool(self.root, "approve", *args)
        self.assertEqual(p.returncode, 0, p.stderr)
        return p.stdout

    def refused(self, fn, needle):
        with self.assertRaises(self.A.Refused) as cm:
            fn()
        self.assertIn(needle, str(cm.exception))


class T1Approval(Base):
    def test_manifest_scope(self):
        m = self.man()
        self.assertIn("workspace-9/runs/900-solve/BRIEF.md", m)
        self.assertIn("workspace-9/runs/900-solve/.limits", m)
        self.assertIn("workspace-9/runs/900-solve/input/a.txt", m)
        self.assertNotIn("workspace-9/runs/900-solve/launch.log", m)
        self.assertNotIn("workspace-9/runs/900-solve/.ledger-outbox", m)

    def test_none_on_file(self):
        self.refused(lambda: self.A.check("launch", "900-solve", self.man()), "none on file")

    def test_ok_then_single_use(self):
        self.approve("900-solve", "--", *F)
        dg = self.A.check("launch", "900-solve", self.man(), argv=F)           # a look does not spend it
        self.assertEqual(dg, self.A.check("launch", "900-solve", self.man(), argv=F, consume=True))
        self.refused(lambda: self.A.check("launch", "900-solve", self.man(), argv=F, consume=True), "single-use")

    def test_expired(self):
        self.approve("900-solve", "--", *F)
        self.refused(lambda: self.A.check("launch", "900-solve", self.man(), argv=F, now=time.time() + self.A.TTL + 1), "expired")
        self.A.check("launch", "900-solve", self.man(), argv=F, now=time.time() + self.A.TTL - 5)

    def test_edits_void_it(self):
        for rel, act, needle in (("BRIEF.md", "edit", "changed: workspace-9/runs/900-solve/BRIEF.md"),
                                 (".limits", "edit", "changed: workspace-9/runs/900-solve/.limits"),
                                 ("input/a.txt", "rm", "removed: workspace-9/runs/900-solve/input/a.txt"),
                                 ("input/new.txt", "edit", "added: workspace-9/runs/900-solve/input/new.txt"),
                                 ("scratch/seed.py", "edit", "added: workspace-9/runs/900-solve/scratch/seed.py")):
            with self.subTest(rel=rel):
                self.approve("900-solve", "--", *F)
                p = os.path.join(self.rd, rel)
                keep = open(p).read() if os.path.exists(p) else None
                os.remove(p) if act == "rm" else open(p, "a").write("x")
                self.refused(lambda: self.A.check("launch", "900-solve", self.man(), argv=F, consume=True), needle)
                os.remove(p) if keep is None else open(p, "w").write(keep)
                self.A.check("launch", "900-solve", self.man(), argv=F, consume=True)   # restored bytes: valid again

    def test_symlink_refused(self):
        os.symlink("/etc/hostname", os.path.join(self.rd, "input", "link"))
        self.refused(self.man, "symlink")
        p = tool(self.root, "approve", "900-solve", "--", *F)
        self.assertEqual(p.returncode, 3)
        self.assertFalse(os.path.exists(self.A.record_path("launch", "900-solve")))

    def test_wrong_kind_and_key(self):
        self.approve("900-solve", "--", *F)
        self.refused(lambda: self.A.check("ledger", "900-solve", self.man()), "none on file")
        self.refused(lambda: self.A.check("launch", "901-ref", self.man(), argv=F), "none on file")

    def test_batch(self):
        out = self.approve("900-solve", "901-ref", "--", *F)
        self.assertEqual(out.count("APPROVED until"), 2)
        self.A.check("launch", "900-solve", self.man(), argv=F, consume=True)
        self.A.check("launch", "901-ref", self.A.launch_manifest(os.path.join(self.root, "workspace-9/runs/901-ref")), argv=F, consume=True)

    def test_flags_bound(self):
        self.approve("900-solve", "--", "--model", "opus", "--effort", "xhigh")
        self.refused(lambda: self.A.check("launch", "900-solve", self.man(), argv=["--model", "fable", "--effort", "xhigh"]), "flags")
        self.refused(lambda: self.A.check("launch", "900-solve", self.man(), argv=[]), "flags")
        self.A.check("launch", "900-solve", self.man(), argv=["--effort", "xhigh", "--model", "opus"])  # order is free

    def test_launch_approval_needs_flags(self):
        """LESSONS.md "A launch approval binds its flags": no flags, or flags without --model, is refused before any
        record is written; a record that bound none (written before this rule) refuses at launch."""
        for args in ((), ("--",), ("--", "--effort", "low")):
            with self.subTest(args=args):
                p = tool(self.root, "approve", "900-solve", *args)
                self.assertEqual(p.returncode, 3, p.stdout)
                self.assertIn("binds its flags", p.stderr)
                self.assertFalse(os.path.exists(self.A.record_path("launch", "900-solve")))
        self.approve("900-solve", "--", *F)
        rec = json.load(open(self.A.record_path("launch", "900-solve")))
        rec["argv"] = None
        json.dump(rec, open(self.A.record_path("launch", "900-solve"), "w"))
        self.refused(lambda: self.A.check("launch", "900-solve", self.man(), argv=["--model", "anything"]), "flags bound")

    def test_digest_pin(self):
        out = tool(self.root, "manifest", "900-solve", "--", *F).stdout
        self.assertIn("read-only", out)
        self.assertFalse(os.path.exists(self.A.record_path("launch", "900-solve")))
        dg = [l for l in out.splitlines() if l.startswith("digest:")][0].split()[1]
        open(os.path.join(self.rd, "BRIEF.md"), "a").write("late edit\n")
        p = tool(self.root, "approve", "900-solve", "--digest", dg[:12], "--", *F)
        self.assertEqual(p.returncode, 3)
        self.assertFalse(os.path.exists(self.A.record_path("launch", "900-solve")))
        open(os.path.join(self.rd, "BRIEF.md"), "w").write("brief v1\n")
        self.approve("900-solve", "--digest", dg[:12], "--", *F)

    def test_approve_ledgers(self):
        self.approve("900-solve", "--", *F)
        self.assertIn("| user | 900-solve | APPROVE | kind=launch", open(os.path.join(self.root, "LEDGER.log")).read())


class T2Tools(Base):
    def claims(self):
        return open(os.path.join(self.root, "CLAIMS.md")).read()

    def test_ledger_claims_refuses_without_approval(self):
        before = self.claims()
        for args in (["900-solve", "c1"], ["900-solve", "c1", "--operator-approved"]):
            p = tool(self.root, "ledger-claims", *args)
            self.assertEqual(p.returncode, 3, p.stdout + p.stderr)
            self.assertIn("no user approval", p.stderr)
        self.assertEqual(before, self.claims())

    def test_ledger_claims_once(self):
        out = self.approve("--ledger", "900-solve", "c1")
        self.assertIn("workspace-9/runs/901-ref/output/referee.json", out)   # the live referee is bound
        p = tool(self.root, "ledger-claims", "900-solve", "c1")
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        self.assertIn("## C-002  [VERIFIED]", self.claims())
        after = self.claims()
        p = tool(self.root, "ledger-claims", "900-solve", "c2")
        self.assertEqual(p.returncode, 3)
        self.assertEqual(after, self.claims())

    def test_ledger_approval_voided(self):
        ref = os.path.join(self.root, "workspace-9/runs/901-ref/output/referee.json")
        cases = (("CLAIMS.md", os.path.join(self.root, "CLAIMS.md"), "\n"),
                 ("check.json", os.path.join(self.rd, "check.json"), "\n"),
                 ("verdict.md", os.path.join(self.rd, "verdict.md"), "x\n"),
                 ("referee.json", ref, "\n"),
                 ("referee binding", os.path.join(self.root, "data/referee-bindings/901-ref.json"), "\n"))   # P-12 C3
        for label, path, tail in cases:
            with self.subTest(changed=label):
                keep = open(path).read()
                self.approve("--ledger", "900-solve", "c1")
                open(path, "a").write(tail)
                before = self.claims()
                p = tool(self.root, "ledger-claims", "900-solve", "c1")
                self.assertEqual(p.returncode, 3, p.stdout + p.stderr)
                self.assertIn("changed:", p.stderr)
                self.assertEqual(before, self.claims())
                open(path, "w").write(keep)

    def test_ledger_ids_bound(self):
        self.approve("--ledger", "900-solve", "c1")
        p = tool(self.root, "ledger-claims", "900-solve", "c1", "c2")
        self.assertEqual(p.returncode, 3)
        self.assertIn("approved ids", p.stderr)

    def test_annotate(self):
        before = self.claims()
        p = tool(self.root, "annotate-claim", "C-001", "a note", "--operator-approved")
        self.assertEqual(p.returncode, 3)
        self.approve("--annotate", "C-001", "a note")
        p = tool(self.root, "annotate-claim", "C-001", "another note")
        self.assertEqual(p.returncode, 3)
        self.assertIn("changed: note-text", p.stderr)
        self.assertEqual(before, self.claims())
        p = tool(self.root, "annotate-claim", "C-001", "a   note")            # whitespace is normalised
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn("## C-001-note", self.claims())
        self.assertEqual(tool(self.root, "annotate-claim", "C-001", "a note").returncode, 3)

    def test_and_joined_pair(self):
        """The source's 2026-09-23 report that an `&&`-joined pair of `!` approvals approved only the first (cause unknown). Probe:
        each kind of pair, joined by && in one shell as `!` runs them, on a fixture root."""
        ap = lambda *a: " ".join(["/usr/bin/python3", os.path.join(BIN, "approve")] + [f"'{x}'" for x in a])
        sh = lambda cmd: subprocess.run(["bash", "-c", cmd], env=dict(os.environ, KIT_ROOT=self.root), text=True,
                                        capture_output=True, stdin=subprocess.DEVNULL)
        p = sh(ap("900-solve", "--", "--model", "opus") + " && " + ap("901-ref", "--", "--model", "opus"))
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertTrue(os.path.exists(self.A.record_path("launch", "900-solve")))
        self.assertTrue(os.path.exists(self.A.record_path("launch", "901-ref")))
        p = sh(ap("--annotate", "C-001", "note one") + " && " + ap("--ledger", "900-solve", "c1"))
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertTrue(os.path.exists(self.A.record_path("annotate", "C-001")))
        self.assertTrue(os.path.exists(self.A.record_path("ledger", "900-solve")))

    def test_annotate_batch(self):
        """LESSONS.md "One approval for several notes; a replaced approval is announced": one approval for a file of notes."""
        open(os.path.join(self.root, "CLAIMS.md"), "a").write("\n## C-002  [VERIFIED]  2026-01-01  run 000-x/c2\nold\n")
        nf = os.path.join(self.root, "notes.json")
        json.dump([{"id": "C-001", "text": "first note"}, {"id": "C-002", "text": "second  note"}], open(nf, "w"))
        before = self.claims()
        self.assertEqual(tool(self.root, "annotate-claim", "--batch", nf).returncode, 3)      # no approval
        p = tool(self.root, "manifest", "--annotate-batch", nf)
        self.assertIn("note on C-001: first note", p.stdout)
        self.assertIn("note on C-002: second note", p.stdout)                                # printed in full
        out = self.approve("--annotate-batch", nf)
        self.assertIn("note on C-002: second note", out)
        json.dump([{"id": "C-001", "text": "first note, edited"}], open(nf, "w"))
        p = tool(self.root, "annotate-claim", "--batch", nf)
        self.assertEqual(p.returncode, 3, p.stderr)                                           # another file, no approval
        json.dump([{"id": "C-001", "text": "first note"}, {"id": "C-002", "text": "second  note"}], open(nf, "w"))
        self.assertEqual(before, self.claims())
        p = tool(self.root, "annotate-claim", "--batch", nf)
        self.assertEqual(p.returncode, 0, p.stderr)
        after = self.claims()
        self.assertIn("## C-001-note", after)
        self.assertIn("  second note (Note by the orchestrator, not refereed.)", after)
        self.assertEqual(tool(self.root, "annotate-claim", "--batch", nf).returncode, 3)      # single use
        json.dump([{"id": "C-001", "text": "The truth as stated is unchanged."}], open(nf, "w"))
        self.approve("--annotate-batch", nf)
        self.assertEqual(tool(self.root, "annotate-claim", "--batch", nf).returncode, 2)      # a vouching note: none appended
        self.assertEqual(after, self.claims())

    def test_same_key_replacement_is_announced(self):
        self.approve("900-solve", "--", "--model", "opus")
        out = self.approve("900-solve", "--", "--model", "fable")
        self.assertIn("replaces the unused approval", out)
        self.assertNotIn("replaces", self.approve("901-ref", "--", *F))

    def test_check_cli(self):
        cli = lambda *a: tool(self.root, "_approval.py", "check", *a)
        self.assertEqual(cli("launch", self.rd).returncode, 3)
        self.approve("900-solve", "--", "--model", "opus")
        self.assertEqual(cli("launch", self.rd, "--", "--model", "fable").returncode, 3)
        self.assertEqual(cli("launch", self.rd, "--", "--model", "opus").returncode, 0)
        self.assertEqual(cli("launch", self.rd, "--", "--model", "opus").returncode, 3)
        self.assertEqual(cli("session", "astra", "--", "-p", "hi").returncode, 3)
        self.approve("--session", "--", "-p", "hi")
        self.assertEqual(cli("session", "astra", "--", "-p", "other").returncode, 3)
        self.assertEqual(cli("session", "astra", "--", "-p", "hi").returncode, 0)


class T1Queue(Base):
    """LESSONS.md 'A queue for runs approved together': a queue uses every approval at its start and releases each run
    once, just before its launch, only with the same flags and bytes."""

    def rd2(self):
        return os.path.join(self.root, "workspace-9/runs/901-ref")

    def test_queue(self):
        self.approve("900-solve", "901-ref", "--", "--model", "opus")
        nonce = self.A.queue_start([self.rd, self.rd2()], argv=["--model", "opus"])
        self.assertFalse(os.path.exists(self.A.record_path("launch", "900-solve")))        # both approvals used now
        self.assertFalse(os.path.exists(self.A.record_path("launch", "901-ref")))
        self.refused(lambda: self.A.queue_take(nonce, self.rd, argv=["--model", "fable"]), "approved flags")
        self.A.queue_take(nonce, self.rd, argv=["--model", "opus"])
        self.refused(lambda: self.A.queue_take(nonce, self.rd, argv=["--model", "opus"]), "already released")
        open(os.path.join(self.rd2(), "BRIEF.md"), "a").write("edited after the queue started\n")
        self.refused(lambda: self.A.queue_take(nonce, self.rd2(), argv=["--model", "opus"]), "bytes differ")
        self.refused(lambda: self.A.queue_take("0" * 16, self.rd2(), argv=["--model", "opus"]), "no queue record")
        self.refused(lambda: self.A.queue_take("../../x", self.rd2(), argv=["--model", "opus"]), "not a queue id")

    def test_queue_release_is_atomic(self):
        """The outside review's F4: a run is released by claiming its token, so a caller that read `launched: null` after
        another caller claimed it is still refused; two processes racing for one run give exactly one release."""
        self.approve("900-solve", "901-ref", "--", "--model", "opus")
        nonce = self.A.queue_start([self.rd, self.rd2()], argv=["--model", "opus"])
        tok = self.A.queue_token(nonce, "900-solve")
        os.rename(tok, tok + ".taken")                       # another caller won the claim; the record still says null
        self.assertIsNone(json.load(open(self.A.queue_path(nonce)))["runs"]["900-solve"]["launched"])
        self.refused(lambda: self.A.queue_take(nonce, self.rd, argv=["--model", "opus"]), "already released")
        cmd = ["/usr/bin/python3", os.path.join(BIN, "_approval.py"), "queued", nonce, self.rd2(), "--", "--model", "opus"]
        env = dict(os.environ, KIT_ROOT=self.root)
        procs = [subprocess.Popen(cmd, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) for _ in range(4)]
        self.assertEqual(sorted(p.wait() for p in procs), [0, 3, 3, 3])

    def test_queue_expires_and_is_all_or_nothing(self):
        self.approve("900-solve", "--", "--model", "opus")
        self.refused(lambda: self.A.queue_start([self.rd, self.rd2()], argv=["--model", "opus"]), "901-ref")
        self.assertTrue(os.path.exists(self.A.record_path("launch", "900-solve")))         # nothing used
        nonce = self.A.queue_start([self.rd], argv=["--model", "opus"])
        life = self.A.queue_wall_seconds(["--model", "opus"], 1) + self.A.QUEUE_SLACK      # one run, 4 h default, + 30 min
        self.refused(lambda: self.A.queue_take(nonce, self.rd, argv=["--model", "opus"], now=time.time() + life + 1), "expired")
        self.A.queue_take(nonce, self.rd, argv=["--model", "opus"])

    def test_cli(self):
        self.approve("900-solve", "--", "--model", "opus")
        cli = lambda *a: tool(self.root, "_approval.py", *a)
        p = cli("queue", "900-solve", "--", "--model", "opus")
        self.assertEqual(p.returncode, 0, p.stderr)
        nonce = p.stdout.strip()
        self.assertEqual(cli("queued", nonce, "900-solve", "--", "--model", "opus").returncode, 0)
        self.assertEqual(cli("queued", nonce, "900-solve", "--", "--model", "opus").returncode, 3)
        self.assertEqual(cli("queue", "901-ref", "--", "--model", "opus").returncode, 3)     # no approval

    def test_lifetime_is_the_wall_caps(self):
        """LESSONS.md 'A queue for runs approved together': a queue lives for its runs' wall caps plus 30 minutes, not a fixed day."""
        self.approve("900-solve", "--", "--model", "opus")
        t0 = time.time()
        nonce = self.A.queue_start([self.rd], argv=["--model", "opus"], now=t0, wall_seconds=4 * 3600)
        self.refused(lambda: self.A.queue_take(nonce, self.rd, argv=["--model", "opus"], now=t0 + 4 * 3600 + 1801), "expired")
        self.A.queue_take(nonce, self.rd, argv=["--model", "opus"], now=t0 + 4 * 3600 + 1799)
        cli = lambda *a: tool(self.root, "_approval.py", *a)
        self.approve("901-ref", "--", "--model", "opus")
        self.assertEqual(cli("queue", "901-ref", "--wall-seconds", "x", "--", "--model", "opus").returncode, 2)
        p = cli("queue", "901-ref", "--wall-seconds", "60", "--", "--model", "opus")
        self.assertEqual(p.returncode, 0, p.stderr)
        rec = json.load(open(self.A.queue_path(p.stdout.strip())))
        self.assertAlmostEqual(rec["expires"] - rec["created"], 60 + self.A.QUEUE_SLACK, delta=1)

    def test_lifetime_derived_from_the_approved_flags(self):
        """The outside review's F12: the lifetime is derived in one place from the approved flags (route default or
        --wall-hours, times the number of runs) and bin/run-external passes none, so the CLI path is the launcher's path."""
        W = self.A.queue_wall_seconds
        self.assertEqual(W(["--model", "m"], 1), 4 * 3600)                                   # a Claude route: 4 h
        self.assertEqual(W(["--model", "m", "--via", "codex"], 3), 3 * 2 * 3600)             # Codex: 2 h each
        self.assertEqual(W(["--via", "codex", "--wall-hours", "1.5", "--model", "m"], 2), int(1.5 * 3600 * 2))
        self.approve("900-solve", "901-ref", "--", "--model", "m", "--via", "codex")
        p = tool(self.root, "_approval.py", "queue", "900-solve", "901-ref", "--require-flags", "--", "--model", "m", "--via", "codex")
        self.assertEqual(p.returncode, 0, p.stderr)
        rec = json.load(open(self.A.queue_path(p.stdout.strip())))
        self.assertAlmostEqual(rec["expires"] - rec["created"], 2 * 2 * 3600 + self.A.QUEUE_SLACK, delta=1)
        self.assertNotIn("--wall-seconds", open(os.path.join(BIN, "run-external")).read())   # the launcher computes none


class T1PacketLists(Base):
    """LESSONS.md "No packet carries blocked material": the user adds packet exceptions with bin/packet-except and blocks with bin/packet-block;
    each addition is ledgered as the user's."""

    def test_except_add_list_ledger(self):
        f = os.path.join(self.rd, "input", "a.txt")
        p = tool(self.root, "packet-except", f, "user ruling, test")
        self.assertEqual(p.returncode, 0, p.stderr)
        lst = json.load(open(os.path.join(self.root, "data", "packet-exceptions.json")))
        self.assertEqual([e["path"] for e in lst], ["workspace-9/runs/900-solve/input/a.txt"])
        self.assertIn("| user | - | PACKET-EXCEPT |", open(os.path.join(self.root, "LEDGER.log")).read())
        self.assertIn("already excepted", tool(self.root, "packet-except", f, "again").stdout)
        self.assertEqual(len(json.load(open(os.path.join(self.root, "data", "packet-exceptions.json")))), 1)
        self.assertIn("a.txt", tool(self.root, "packet-except", "--list").stdout)
        outside = tempfile.NamedTemporaryFile(delete=False)
        self.assertEqual(tool(self.root, "packet-except", outside.name, "r").returncode, 3)
        os.unlink(outside.name)

    def test_block_add_list_ledger(self):
        d = os.path.join(self.root, "workspace-9", "runs", "901-ref")
        self.assertEqual(tool(self.root, "packet-block", d, "an evaluation run").returncode, 0)
        self.assertEqual(tool(self.root, "packet-block", "--lines", r"\bI rank\b", self.rd, "ranking lines").returncode, 0)
        r = json.load(open(os.path.join(self.root, "data", "packet-rules.json")))
        self.assertEqual([e["path"] for e in r["blocked"]], ["workspace-9/runs/901-ref"])
        self.assertEqual([(e["path"], e["match"]) for e in r["lines"]], [("workspace-9/runs/900-solve", r"\bI rank\b")])
        self.assertIn("PACKET-BLOCK", open(os.path.join(self.root, "LEDGER.log")).read())
        self.assertIn("already on the list", tool(self.root, "packet-block", d, "again").stdout)
        self.assertEqual(tool(self.root, "packet-block", "--lines", "(", self.rd, "bad").returncode, 2)
        self.assertEqual(tool(self.root, "packet-block", "/nonexistent/x", "r").returncode, 3)
        self.assertIn("901-ref", tool(self.root, "packet-block", "--list").stdout)

    def test_block_extract(self):
        """The source's method change 52: the entries and notes bin/claims-extract leaves out are the user's, on the same list."""
        self.assertEqual(tool(self.root, "packet-block", "--extract", "C-042", "a heuristic model").returncode, 0)
        self.assertEqual(tool(self.root, "packet-block", "--extract-note", "C-032", "2026-09-24", "an evaluation").returncode, 0)
        x = json.load(open(os.path.join(self.root, "data", "packet-rules.json")))["extract"]
        self.assertEqual([e["id"] for e in x["entries"]], ["C-042"])
        self.assertEqual([(e["id"], e["date"]) for e in x["notes"]], [("C-032", "2026-09-24")])
        self.assertIn("PACKET-BLOCK | extract-entries C-042 why=a heuristic model", open(os.path.join(self.root, "LEDGER.log")).read())
        self.assertIn("already on the list", tool(self.root, "packet-block", "--extract", "C-042", "again").stdout)
        for bad in (["--extract", "42", "r"], ["--extract", "C-042", " "], ["--extract-note", "C-032", "Sept", "r"]):
            self.assertEqual(tool(self.root, "packet-block", *bad).returncode, 2, bad)
        self.assertIn("C-032-note 2026-09-24", tool(self.root, "packet-block", "--list").stdout)


class T2RealTools(unittest.TestCase):
    """The two bash tools resolve the root from their own location, so their refusal is tested on the real tree
    with a throwaway run that has no approval. A refusal must come before any side effect: no log, no ledger line, no process.
    Belt and braces: a stub `claude` is first on PATH, so even a broken gate could not start a worker here."""

    RUN = "999-gate-test-fixture"

    def setUp(self):
        self.rd = os.path.join(REAL, "workspace-1", "runs", self.RUN)
        os.makedirs(self.rd, exist_ok=True)
        open(os.path.join(self.rd, "BRIEF.md"), "w").write("brief\n")
        self.stub = tempfile.mkdtemp(prefix="gate-stub-")
        self.marker = os.path.join(self.stub, "CLAUDE-WAS-CALLED")
        with open(os.path.join(self.stub, "claude"), "w") as f:
            f.write(f"#!/bin/sh\ntouch {self.marker}\nexit 97\n")
        os.chmod(os.path.join(self.stub, "claude"), 0o755)
        self.env = {k: v for k, v in os.environ.items() if k != "KIT_ROOT"}
        self.env["PATH"] = self.stub + ":" + self.env["PATH"]

    def tearDown(self):
        called = os.path.exists(self.marker)
        shutil.rmtree(self.stub)
        shutil.rmtree(self.rd)
        for d in (os.path.dirname(self.rd), os.path.dirname(os.path.dirname(self.rd))):
            try:                      # leave the tree as it was found: no empty workspace-1/runs/ behind
                os.rmdir(d)
            except OSError:
                pass
        self.assertFalse(called, "the gate let a launch through to `claude`")

    def test_run_external_refuses(self):
        logs = set(os.listdir(self.rd))
        p = subprocess.run([os.path.join(BIN, "run-external"), self.RUN, "--model", "opus", "--via", "anthropic"],
                           text=True, capture_output=True, stdin=subprocess.DEVNULL, timeout=60, env=self.env)
        rc, why = refusal(REAL)
        self.assertEqual(p.returncode, rc, p.stdout + p.stderr)
        self.assertIn(why, p.stderr)
        self.assertEqual(logs, set(os.listdir(self.rd)))

    def test_astra_session_refuses(self):
        key = tempfile.NamedTemporaryFile("w", suffix=".key", delete=False)
        key.write("not-a-key\n"); key.close()
        env = dict(self.env, OPENROUTER_KEYFILE=key.name)
        try:
            for args, needle in (([], "needs a terminal"), (["-p", "gate test, must never run"], "no user approval")):
                p = subprocess.run([os.path.join(BIN, "astra-session"), *args], text=True, capture_output=True,
                                   stdin=subprocess.DEVNULL, timeout=60, env=env)
                self.assertEqual(p.returncode, 3, p.stdout + p.stderr)
                self.assertIn(needle, p.stderr)
        finally:
            os.unlink(key.name)


if __name__ == "__main__":
    import warnings
    unittest.main(verbosity=2, warnings="ignore")
