#!/usr/bin/env python3
"""Tests of the methods-session changes of 2026-09-22 (LESSONS.md). Stdlib only; fixture roots only:

    python3 tests/test_tools.py

Nothing touches the real ledger, claims, approvals or runs, and nothing is launched.
"""
import hashlib
import hashlib
import json
import os
import re
import shutil
import tempfile
import subprocess
import sys
import time
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import test_gate as G


class Base(G.Base):
    pass


class T4MisplacedFields(Base):
    """LESSONS.md "Unknown or misplaced fields are errors": a field in the wrong place is an error (run 086's top-level deps)."""

    def claim(self, **kw):
        c = {"id": "c1", "tag": "PROVED", "statement": "s", "silent_links": ["none"],
             "artifact": {"type": "text", "path": "output/p.md"}}
        c.update(kw)
        return c

    def test_top_level_deps(self):
        import _lib as L
        e = L.validate_claim(self.claim(deps=["output/x.md"]))
        self.assertTrue(any("belongs under artifact" in x for x in e), e)

    def test_unknown_fields(self):
        import _lib as L
        self.assertTrue(any("unknown claim field" in x for x in L.validate_claim(self.claim(note="x"))))
        c = self.claim()
        c["artifact"]["dep"] = ["output/x.md"]
        self.assertTrue(any("unknown artifact field" in x for x in L.validate_claim(c)))
        c = self.claim()
        c["artifact"]["silent_links"] = ["none"]
        self.assertTrue(any("belongs at the claim's top level" in x for x in L.validate_claim(c)))

    def test_well_placed_passes(self):
        import _lib as L
        c = self.claim()
        c["artifact"]["deps"] = ["output/x.md"]
        self.assertEqual(L.validate_claim(c), [])

    def test_check_fails_top_level_deps(self):
        out = os.path.join(self.rd, "output")
        open(os.path.join(out, "p.md"), "w").write("proof\n")
        open(os.path.join(out, "result.md"), "w").write("r\n")
        json.dump({"schema": "kit/claims/1", "run": "900-solve", "problem": "x",
                   "claims": [self.claim(deps=["output/p.md"])]}, open(os.path.join(out, "claims.json"), "w"))
        p = subprocess.run(["/usr/bin/python3", os.path.join(G.BIN, "validate-claims"), self.rd], text=True, capture_output=True)
        self.assertEqual(p.returncode, 1, p.stdout)
        self.assertIn("belongs under artifact", p.stdout)


class T4NewRunSlug(Base):
    def setUp(self):
        super().setUp()
        os.makedirs(os.path.join(self.root, "problems", "x"))
        open(os.path.join(self.root, "problems", "x", "PROBLEM.md"), "w").write("p\n")

    def test_numbered_slug_refused(self):
        p = G.tool(self.root, "new-run", "workspace-9", "902-thing", "--role", "other")
        self.assertNotEqual(p.returncode, 0)
        self.assertIn("adds the run number itself", p.stderr)
        self.assertFalse(os.path.exists(os.path.join(self.root, "workspace-9", "runs", "902-902-thing")))

    def test_plain_slug_numbered(self):
        p = G.tool(self.root, "new-run", "workspace-9", "thing", "--role", "other")
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertTrue(os.path.isdir(os.path.join(self.root, "workspace-9", "runs", "902-thing")))

    def test_template_nests_deps(self):
        p = G.tool(self.root, "new-run", "workspace-9", "solve", "--role", "solver", "--problem", "x")
        self.assertEqual(p.returncode, 0, p.stderr)
        brief = open(os.path.join(self.root, "workspace-9", "runs", "902-solve", "BRIEF.md")).read()
        self.assertIn('"deps": ["output/cases.txt"],  // every other file', brief)
        lint = G.tool(self.root, "lint-brief", "902-solve")
        self.assertNotIn("names deps without artifact", lint.stdout)   # the skeleton itself lints clean on deps
        self.assertIn("unfilled slot", lint.stdout)                     # its slots are still open


class T4Flags(Base):
    def test_bare_flags_order_free(self):
        n = self.A.norm_argv
        self.assertEqual(n(["--network", "--model", "x", "--via", "codex"]), n(["--via", "codex", "--model", "x", "--network"]))
        self.assertEqual(n(["--model", "opus", "--effort", "low"]), ["--effort", "low", "--model", "opus"])  # unchanged for pairs
        self.assertEqual(n(["-p", "hi"]), ["-p", "hi"])                                                        # verbatim otherwise

    def test_network_flag_bound(self):
        self.approve("900-solve", "--", "--model", "gpt", "--via", "codex", "--network")
        self.refused(lambda: self.A.check("launch", "900-solve", self.man(), argv=["--model", "gpt", "--via", "codex"]), "flags")
        self.A.check("launch", "900-solve", self.man(), argv=["--network", "--via", "codex", "--model", "gpt"], require_flags=True)

    def test_require_flags(self):
        """Every launch approval binds its flags (LESSONS.md "A launch approval binds its flags"): the CLI check refuses
        any other flags and accepts exactly the approved ones."""
        self.approve("900-solve", "--", "--model", "gpt")
        cli = lambda *a: G.tool(self.root, "_approval.py", "check", *a)
        self.assertEqual(cli("launch", self.rd, "--require-flags", "--", "--network").returncode, 3)
        self.assertEqual(cli("launch", self.rd, "--", "--network").returncode, 3)
        self.assertEqual(cli("launch", self.rd, "--", "--model", "gpt").returncode, 0)


class T4BatchTap(Base):
    """LESSONS.md "Batch tap": one --digest per target, comma-separated, in target order."""

    def digests(self, *runs):
        out = G.tool(self.root, "manifest", *runs, "--", *G.F).stdout
        return [l.split()[1][:12] for l in out.splitlines() if l.startswith("digest:")]

    def test_batch_digest(self):
        d1, d2 = self.digests("900-solve", "901-ref")
        self.approve("900-solve", "901-ref", "--digest", f"{d1},{d2}", "--", *G.F)
        self.A.check("launch", "901-ref", self.A.launch_manifest(os.path.join(self.root, "workspace-9/runs/901-ref")), argv=G.F, consume=True)

    def test_batch_digest_wrong_order_or_count(self):
        d1, d2 = self.digests("900-solve", "901-ref")
        for args in (["900-solve", "901-ref", "--digest", f"{d2},{d1}", "--", *G.F], ["900-solve", "901-ref", "--digest", d1, "--", *G.F],
                     ["900-solve", "--digest", f"{d1},{d2}", "--", *G.F]):
            with self.subTest(args=args):
                p = G.tool(self.root, "approve", *args)
                self.assertEqual(p.returncode, 3, p.stdout)
        self.assertFalse(os.path.exists(self.A.record_path("launch", "900-solve")))

    def test_batch_digest_stale_bytes(self):
        d1, d2 = self.digests("900-solve", "901-ref")
        open(os.path.join(self.root, "workspace-9/runs/901-ref/BRIEF.md"), "a").write("late\n")
        p = G.tool(self.root, "approve", "900-solve", "901-ref", "--digest", f"{d1},{d2}", "--", *G.F)
        self.assertEqual(p.returncode, 3)
        self.assertIn("901-ref", p.stderr)
        self.assertFalse(os.path.exists(self.A.record_path("launch", "900-solve")))  # all or nothing


class T4HandoffPaths(Base):
    """LESSONS.md "Every backticked tree path in a handoff exists": every tree path HANDOFF.md names in backticks exists."""

    def run_vd(self, text):
        open(os.path.join(self.root, "HANDOFF.md"), "w").write(text)
        os.makedirs(os.path.join(self.root, "lean"), exist_ok=True)
        p = G.tool(self.root, "verify-data", "--write-lean-manifest")
        self.assertEqual(p.returncode, 0, p.stderr)
        return G.tool(self.root, "verify-data")

    def test_missing_path_found(self):
        p = self.run_vd("see `workspace-9/runs/900-solve/BRIEF.md` and `problems/nowhere.md`, `handoffs/<date>.md`\n")
        self.assertIn("names a path that does not exist: problems/nowhere.md", p.stdout)
        self.assertNotIn("900-solve/BRIEF.md", p.stdout)
        self.assertNotIn("<date>", p.stdout)

    def test_absolute_path(self):
        p = self.run_vd(f"`{self.root}/workspace-9/runs/900-solve/gone.md`\n")
        self.assertIn("does not exist: workspace-9/runs/900-solve/gone.md", p.stdout)


class T5WrongTree(Base):
    """LESSONS.md "A session works on the tree it was opened in": a tree with no LEDGER.log is not an instance. Every ledger
    writer refuses there and creates none, bin/approve refuses before writing a record, and bin/verify-data names its root
    first, so a command that ran in the wrong tree (the kit, after a reset `cd`) is loud instead of quietly passing."""

    def setUp(self):
        super().setUp()
        self.led = os.path.join(self.root, "LEDGER.log")
        os.remove(self.led)

    def test_verify_data_names_root_and_creates_no_ledger(self):
        p = G.tool(self.root, "verify-data")
        self.assertEqual(p.stdout.splitlines()[0], f"root: {self.root}")
        self.assertNotEqual(p.returncode, 0)
        self.assertIn("not an instance", p.stderr)
        self.assertFalse(os.path.exists(self.led))

    def test_lib_ledger_refuses(self):
        import _lib as L
        with self.assertRaises(SystemExit):
            L.ledger(None, "TEST", "x")
        self.assertFalse(os.path.exists(self.led))

    def test_approve_refused_before_any_record(self):
        p = G.tool(self.root, "approve", "900-solve", "--", *G.F)
        self.assertEqual(p.returncode, 3, p.stderr)
        self.assertIn("not an instance", p.stderr)
        state = os.path.join(self.root, ".claude", "state", "approvals")
        self.assertEqual([f for _, _, fs in os.walk(state) for f in fs] if os.path.isdir(state) else [], [])
        self.assertFalse(os.path.exists(self.led))

    def test_handoff_archive_refused(self):
        open(os.path.join(self.root, "HANDOFF.md"), "w").write("h\n")
        p = G.tool(self.root, "handoff-archive", "--session", "t")
        self.assertEqual(p.returncode, 2, p.stderr)
        self.assertIn("not an instance", p.stderr)
        self.assertFalse(os.path.exists(os.path.join(self.root, "handoffs")))
        self.assertFalse(os.path.exists(self.led))

    def test_shell_ledger_refuses_then_appends(self):
        # bin/ledger takes its root from its own location, so a copy under the fixture root writes only there
        os.makedirs(os.path.join(self.root, "bin"))
        sh = os.path.join(self.root, "bin", "ledger")
        shutil.copy(os.path.join(G.BIN, "ledger"), sh)
        p = subprocess.run([sh, "TEST", "x"], text=True, capture_output=True)
        self.assertEqual(p.returncode, 2, p.stderr)
        self.assertIn("not an instance", p.stderr)
        self.assertFalse(os.path.exists(self.led))
        open(self.led, "w").close()
        p = subprocess.run([sh, "-r", "900-solve", "TEST", "x"], text=True, capture_output=True)
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn("| orchestrator | 900-solve | TEST | x", open(self.led).read())


class T4TurnCap(unittest.TestCase):
    """LESSONS.md "A brief may not allow more tool calls than `--max-turns`": run-external refuses, before the approval, a brief that allows more tool calls than
    --max-turns. The tool has the real root hardcoded, so it runs on a throwaway run under the real tree's
    workspace-1 that is removed afterwards; a stub `claude` first on PATH proves nothing launches."""

    def test_refused_before_approval(self):
        rd = os.path.join(G.REAL, "workspace-1", "runs", "999-turncap-test-fixture")
        os.makedirs(rd)
        stub = G.tempfile.mkdtemp()
        try:
            open(os.path.join(rd, "BRIEF.md"), "w").write("Budget: at most 400 tool calls.\n")
            open(os.path.join(stub, "claude"), "w").write("#!/bin/sh\ntouch %s/CALLED\n" % stub)
            os.chmod(os.path.join(stub, "claude"), 0o755)
            env = {k: v for k, v in os.environ.items() if k != "KIT_ROOT"}
            env["PATH"] = stub + ":" + env["PATH"]
            p = subprocess.run([os.path.join(G.BIN, "run-external"), "999-turncap-test-fixture", "--model", "opus",
                                "--via", "anthropic"], text=True, capture_output=True, env=env, timeout=60)
            self.assertEqual(p.returncode, 2, p.stderr)
            self.assertIn("allows 400 tool calls but --max-turns is 300", p.stderr)
            self.assertFalse(os.path.exists(os.path.join(stub, "CALLED")))
            self.assertEqual(sorted(os.listdir(rd)), ["BRIEF.md"])
        finally:
            shutil.rmtree(rd)
            shutil.rmtree(stub)


def load_check():
    import importlib.machinery, importlib.util
    spec = importlib.util.spec_from_loader("check_tool", importlib.machinery.SourceFileLoader("check_tool", os.path.join(G.BIN, "check")))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class T6Signatures(unittest.TestCase):
    """LESSONS.md "Every Lean signature is captured": Lean prints a name relative to the file's open namespaces, and an
    artifact may print its own `#check` of a declaration; the parser used to match full names only and read the whole log."""

    def setUp(self):
        self.C = load_check()

    def test_names_relative_to_open_namespaces(self):
        # the source's two lost cases, in synthetic form: a name printed with its namespace opened, twice over
        out = "\n".join([self.C.SIG_MARKER, "criterion : ∀ (G : Grid), G.IsGood ↔ G.sum = 3 * G.e",
                          "Grid.isGood_iff : ∀ (G : Grid),", "  G.IsGood ↔ G.a + G.b + G.c = G.sum"])
        sigs = self.C.parse_signatures(out, ["Pkg.criterion", "Pkg.Grid.isGood_iff"])
        self.assertEqual(sorted(sigs), ["Pkg.Grid.isGood_iff", "Pkg.criterion"])
        self.assertIn("G.a + G.b + G.c = G.sum", sigs["Pkg.Grid.isGood_iff"])

    def test_primed_names(self):
        """LESSONS.md "Lean names ending in a prime": Lean prints `'A.foo'' depends on axioms: [...]` for A.foo'; the parser
        used to stop at the prime and find no axioms line (the source lost three declarations of one run this way)."""
        ax = lambda out: {m.group(1): m.group(2) for m in self.C.AXIOM_RE.finditer(out)}
        f = ax("'A.foo'' depends on axioms: [propext]\n'A.foo''' does not depend on any axioms\n'A.bar' depends on axioms: []\n")
        self.assertEqual(f, {"A.foo'": "propext", "A.foo''": None, "A.bar": ""})

    def test_marker_and_same_suffix(self):
        out = "\n".join(["foo : WRONG", self.C.SIG_MARKER, "foo : ONE", "  continued", "foo : TWO",
                         "'A.foo' depends on axioms: [propext]"])
        sigs = self.C.parse_signatures(out, ["A.foo", "B.foo"])
        self.assertEqual(sigs, {"A.foo": "foo : ONE\n  continued", "B.foo": "foo : TWO"})
        self.assertEqual(self.C.parse_signatures("xfoo : NO\n", ["A.foo"]), {})   # a suffix match needs the dot
        # with per-declaration markers, a #check that errors leaves its declaration missing
        out = "\n".join([self.C.SIG_MARKER, self.C.DECL_MARKER + "A.foo", "error: unknown identifier 'A.foo'",
                         self.C.DECL_MARKER + "B.foo", "foo : TWO"])
        self.assertEqual(self.C.parse_signatures(out, ["A.foo", "B.foo"]), {"B.foo": "foo : TWO"})

    @unittest.skipUnless(os.path.isdir(os.path.join(G.REAL, "lean")), "no formal library linked in this tree")
    def test_check_end_to_end(self):
        root, rd = G.make_root()
        try:
            os.symlink(os.path.realpath(os.path.join(G.REAL, "lean")), os.path.join(root, "lean"))
            if os.path.exists(os.path.join(G.REAL, ".kit-lean")):
                shutil.copy(os.path.join(G.REAL, ".kit-lean"), os.path.join(root, ".kit-lean"))
            out = os.path.join(rd, "output")
            open(os.path.join(out, "T.lean"), "w").write(
                "namespace Foo.Bar\ntheorem baz : 1 + 1 = 2 := rfl\ntheorem qux (n : Nat) : n + 0 = n := rfl\nend Foo.Bar\n"
                "open Foo\n#check @Bar.qux\n")
            open(os.path.join(out, "result.md"), "w").write("r\n")
            json.dump({"schema": "kit/claims/2", "run": "900-solve", "problem": "x", "claims": [
                {"id": "c1", "tag": "PROVED", "statement": "s", "silent_links": ["none"],
                 "premises": [{"kind": "kernel", "what": "Lean"}],
                 "artifact": {"type": "lean", "path": "output/T.lean", "decls": ["Foo.Bar.baz", "Foo.Bar.qux"]}}]},
                open(os.path.join(out, "claims.json"), "w"))
            p = G.tool(root, "check", "900-solve")
            self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
            rec = json.load(open(os.path.join(rd, "check.json")))["claims"][0]
            self.assertEqual(rec["signatures"], {"Foo.Bar.baz": "Bar.baz : 1 + 1 = 2",
                                                 "Foo.Bar.qux": "Bar.qux : ∀ (n : Nat), n + 0 = n"})
            self.assertNotIn("signatures_missing", rec)
        finally:
            shutil.rmtree(root)


def entry(gid, sha, deps=(), statement="s", silent="none", sup=None, run="900-solve", cid="c1"):
    d = ("Deps: " + "; ".join(f"x/{h[:4]} sha256={h}" for h in deps) + "\n") if deps else ""
    return (f"## {gid}  [PROVED]  2026-09-25  run {run}/{cid}\n{statement}\nArtifact (text): x  sha256={sha}\n{d}"
            f"Silent links: {silent}\nCheck: n/a\nReferee: holds\nSupersedes: {sup or '—'}\n\n")


class T7ClaimDeps(Base):
    """LESSONS.md "Dependencies between ledger entries are read by bytes and by name": dependencies by artifact bytes as well as by named ids."""

    HA, HB, HC, HD = ("a" * 64), ("b" * 64), ("c" * 64), ("d" * 64)

    def setUp(self):
        super().setUp()
        A, B, C, D = self.HA, self.HB, self.HC, self.HD
        text = ("# CLAIMS\n\n" + entry("C-001", A) + entry("C-002", B, deps=[A], cid="c2")   # C-002 uses C-001's file, unnamed
                + entry("C-003", C, statement="Taking C-001 as certified", cid="c3")          # names it
                + entry("C-004", D, cid="c4") + "## C-001-note  2026-09-25  C-004 is unrelated\n\n"
                + entry("C-005", A, silent="restates C-001", sup="C-001", cid="c5")           # C-001 restated, same file
                + entry("C-006", D, sup="C-004", cid="c6") + entry("C-007", "e" * 64, deps=[D], cid="c7"))
        open(os.path.join(self.root, "CLAIMS.md"), "w").write(text)
        sys.modules.pop("_lib", None)
        import _lib
        self.L = _lib

    def test_edges(self):
        ent, sup, edges = self.L.claim_graph()
        self.assertEqual(sup, {"C-001", "C-004"})
        self.assertEqual(edges["C-002"], {"C-005": ["file"]})        # the bytes are carried by the live restatement
        self.assertEqual(edges["C-003"], {"C-001": ["names"]})
        self.assertEqual(edges["C-005"], {})                          # its own predecessor is not an edge
        self.assertEqual(edges["C-007"], {"C-006": ["file"]})
        self.assertNotIn("C-004", edges["C-001"])                     # notes are not read

    def test_report(self):
        self.assertEqual(self.L.supersession_lines("C-001"),
                         ["live entries depending on C-001 (bin/claim-deps C-001): C-003 via names"])
        p = G.tool(self.root, "claim-deps")
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn("C-001 (superseded) has live dependents:\n  C-003  depth 1  via names", p.stdout)
        self.assertNotIn("C-004 (superseded) has", p.stdout)          # C-007's file is carried by live C-006
        p = G.tool(self.root, "claim-deps", "C-005")
        self.assertIn("C-002  depth 1  via file", p.stdout)


class T8Notes(Base):
    """LESSONS.md "A note says whose it is and does not vouch for the entry": a note may not vouch for the entry and always says whose it is."""

    def setUp(self):
        super().setUp()
        open(os.path.join(self.root, "CLAIMS.md"), "w").write("# CLAIMS\n\n" + entry("C-001", "a" * 64))

    def test_vouching_refused_before_the_approval(self):
        for text in ("Earlier source: X. The truth as stated is unchanged.", "unchanged, and so is its truth"):
            with self.subTest(text=text):
                p = G.tool(self.root, "annotate-claim", "C-001", text, "--dry-run")
                self.assertEqual(p.returncode, 2, p.stdout)
                self.assertIn("may not say that the entry's truth is unchanged", p.stderr)
        self.approve("--annotate", "C-001", "The truth as stated is unchanged.")
        p = G.tool(self.root, "annotate-claim", "C-001", "The truth as stated is unchanged.")
        self.assertEqual(p.returncode, 2)                                  # refused although approved
        self.assertNotIn("C-001-note", open(os.path.join(self.root, "CLAIMS.md")).read())

    def test_suffix_and_dry_run(self):
        p = G.tool(self.root, "annotate-claim", "C-001", "Earlier source: X.", "--dry-run")
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertTrue(p.stdout.strip().endswith("Earlier source: X. (Note by the orchestrator, not refereed.)"))
        self.assertNotIn("C-001-note", open(os.path.join(self.root, "CLAIMS.md")).read())
        self.approve("--annotate", "C-001", "Earlier source: X.")
        p = G.tool(self.root, "annotate-claim", "C-001", "Earlier source: X.")
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn("  Earlier source: X. (Note by the orchestrator, not refereed.)\n",
                      open(os.path.join(self.root, "CLAIMS.md")).read())


class T9Premises(Base):
    """LESSONS.md "Premises on every claim; the primary text quoted; a conditional marker": premises on every PROVED/VERIFIED claim under claims/2, the
    primary text and a verbatim quote for a published or source premise, and a conditional marker in the ledger."""

    V2 = "kit/claims/2"

    def claim(self, **kw):
        c = {"id": "c1", "tag": "PROVED", "statement": "s", "silent_links": ["none"],
             "artifact": {"type": "text", "path": "output/p.md", "deps": ["output/src/paper.pdf", "output/q.md"]}}
        c.update(kw)
        return c

    def test_rules(self):
        import _lib as L
        pub = {"kind": "published", "what": "Author 2000, Corollary 2.6", "source": "output/src/paper.pdf", "quote": "output/q.md"}
        self.assertTrue(any("premises missing" in e for e in L.validate_claim(self.claim(), self.V2)))
        self.assertEqual(L.validate_claim(self.claim(), "kit/claims/1"), [])                  # old runs unchanged
        self.assertEqual(L.validate_claim(self.claim(premises=[pub]), self.V2), [])
        self.assertTrue(any("needs `quote`" in e for e in
                            L.validate_claim(self.claim(premises=[dict(pub, quote=None)]), self.V2)))
        c = self.claim(premises=[pub]); c["artifact"]["deps"] = ["output/q.md"]
        self.assertTrue(any("must also be listed in artifact.deps" in e for e in L.validate_claim(c, self.V2)))
        self.assertTrue(any("names one entry" in e for e in
                            L.validate_claim(self.claim(premises=[{"kind": "ledger", "what": "C-001 and C-002"}]), self.V2)))
        self.assertTrue(any("kind" in e for e in L.validate_claim(self.claim(premises=[{"kind": "belief", "what": "x"}]), self.V2)))
        self.assertEqual(L.validate_claims_doc({"schema": "kit/claims/1", "run": "r", "claims": []}, "r")[1], [])
        self.assertTrue(L.validate_claims_doc({"schema": "kit/claims/3", "run": "r", "claims": []}, "r")[1])

    def test_claims1_only_where_named(self):
        """kit/claims/1 is accepted for a run only if its BRIEF.md names it (every run made before claims/2 does)."""
        import _lib as L
        doc = {"schema": "kit/claims/1", "run": "900-solve", "claims": []}
        self.assertTrue(any("kit/claims/1 only" in e for e in L.validate_claims_doc(doc, "900-solve", self.rd)[1]))
        open(os.path.join(self.rd, "BRIEF.md"), "a").write("Restatement: the claims keep schema kit/claims/1.\n")
        self.assertEqual(L.validate_claims_doc(doc, "900-solve", self.rd)[1], [])
        self.assertEqual(L.validate_claims_doc(dict(doc, schema="kit/claims/2"), "900-solve", self.rd)[1], [])

    def test_claims1_needs_the_approved_brief(self):
        """The outside review's F3: a worker that appends "kit/claims/1" to its own brief does not earn the exemption; the
        brief must still have the bytes the launch approval bound. An old brief that named claims/1 when approved keeps it."""
        import _lib as L
        doc = {"schema": "kit/claims/1", "run": "900-solve", "claims": []}
        self.approve("900-solve", "--", *G.F)
        self.A.check("launch", "900-solve", self.man(), argv=G.F, consume=True)          # launched on a claims/2 brief
        open(os.path.join(self.rd, "BRIEF.md"), "a").write("schema kit/claims/1\n")      # the worker edits its brief
        self.assertTrue(any("kit/claims/1 only" in e for e in L.validate_claims_doc(doc, "900-solve", self.rd)[1]))
        ref = os.path.join(self.root, "workspace-9", "runs", "901-ref")
        open(os.path.join(ref, "BRIEF.md"), "w").write("an old brief: schema kit/claims/1\n")
        self.approve("901-ref", "--", *G.F)
        self.A.check("launch", "901-ref", self.A.launch_manifest(ref), argv=G.F, consume=True)
        self.assertEqual(L.validate_claims_doc(dict(doc, run="901-ref"), "901-ref", ref)[1], [])   # approved as it stands

    def test_unknown_ledger_premise_refused(self):
        """The outside review's F8: a ledger premise must name an entry of CLAIMS.md, at append time (and at check time)."""
        cj = os.path.join(self.rd, "output", "claims.json")
        doc = json.load(open(cj))
        doc["claims"][0]["premises"] = [{"kind": "ledger", "what": "C-999"}]
        json.dump(doc, open(cj, "w"))
        self.approve("--ledger", "900-solve", "c1")
        p = G.tool(self.root, "ledger-claims", "900-solve", "c1")
        self.assertEqual(p.returncode, 1, p.stdout + p.stderr)
        self.assertIn("ledger premise(s) C-999 not in CLAIMS.md", p.stdout)
        self.assertNotIn("C-002", open(os.path.join(self.root, "CLAIMS.md")).read())

    def test_claims_before_ledger_lines(self):
        """The outside review's F11: CLAIMS.md is written before the ledger's CLAIM lines, so a failed write leaves no line
        saying an entry exists."""
        self.approve("--ledger", "900-solve", "c1")
        cm = os.path.join(self.root, "CLAIMS.md")
        os.chmod(cm, 0o444)
        try:
            p = G.tool(self.root, "ledger-claims", "900-solve", "c1")
        finally:
            os.chmod(cm, 0o644)
        self.assertNotEqual(p.returncode, 0)
        self.assertNotIn("| CLAIM | C-002", open(os.path.join(self.root, "LEDGER.log")).read())

    def test_ledger_marker(self):
        cj = os.path.join(self.rd, "output", "claims.json")
        doc = json.load(open(cj))
        doc["claims"][0]["premises"] = [{"kind": "ledger", "what": "C-001"}, {"kind": "software", "what": "sympy 1.12"}]
        json.dump(doc, open(cj, "w"))
        self.approve("--ledger", "900-solve", "c1")
        p = G.tool(self.root, "ledger-claims", "900-solve", "c1")
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        text = open(os.path.join(self.root, "CLAIMS.md")).read()
        self.assertIn("## C-002  [VERIFIED]  ", text)
        self.assertIn("run 900-solve/c1  (conditional: ledger)\n", text)
        self.assertIn("Premises: ledger: C-001; software: sympy 1.12\n", text)
        sys.modules.pop("_lib", None)
        import _lib as L
        self.assertEqual(L.global_entries()["C-002"]["cid"], "c1")                               # the header still parses
        self.assertEqual(L.claim_graph()[2]["C-002"], {"C-001": ["premise"]})                  # a ledger premise is an edge
        # the conditional marker on the header line does not swallow the statement
        with open(os.path.join(self.root, "CLAIMS.md"), "a") as f:
            f.write("\n## C-003  [PROVED]  2026-09-25  run 901-x/c1  (conditional: ledger)\nTaking C-001 as certified, s.\n"
                    "Artifact (text): x  sha256=" + "e" * 64 + "\nSilent links: none\nSupersedes: —\n")
        sys.modules.pop("_lib", None)
        import _lib as L
        self.assertEqual(L.ledger_entries()["C-003"]["statement"], "Taking C-001 as certified, s.")
        self.assertEqual(L.claim_graph()[2]["C-003"], {"C-001": ["names"]})


class T10Sentence(Base):
    """LESSONS.md "A sentence referee reads every script claim": the sentence read of script claims, required for
    VERIFIED and NUMERIC under claims/2; "certifies less" is a gap in every referee brief; premises are checked."""

    def setUp(self):
        super().setUp()
        os.makedirs(os.path.join(self.root, "problems", "x"))
        os.makedirs(os.path.join(self.root, "lean"))
        open(os.path.join(self.root, "problems", "x", "PROBLEM.md"), "w").write("p\n")
        out = os.path.join(self.rd, "output")
        open(os.path.join(out, "s.py"), "w").write("import cypari2\nassert 1 + 1 == 2\n")
        open(os.path.join(out, "result.md"), "w").write("r\n")
        self.doc = {"schema": "kit/claims/2", "run": "900-solve", "problem": "x", "claims": [
            {"id": "c1", "tag": "VERIFIED", "statement": "1 + 1 = 2", "range": "one case", "coverage": "asserted",
             "silent_links": ["none"], "premises": [{"kind": "software", "what": "Python 3.12"}],
             "artifact": {"type": "script", "path": "output/s.py", "cmd": "python3 output/s.py",
                          "mutations": [{"name": "m", "cmd": "false", "expect_stdout_contains": "FAIL"}]}},
            {"id": "c2", "tag": "PROVED", "statement": "t", "silent_links": ["none"],
             "premises": [{"kind": "classical", "what": "Lagrange"}], "artifact": {"type": "text", "path": "output/s.py"}}]}
        json.dump(self.doc, open(os.path.join(out, "claims.json"), "w"))
        json.dump({"generated": "now", "overall": "pass", "claims": [
            {"id": "c1", "check": "pass", "artifact_sha256": hashlib.sha256(open(os.path.join(out, "s.py"), "rb").read()).hexdigest()},
            {"id": "c2", "check": "n/a"}]}, open(os.path.join(self.rd, "check.json"), "w"))

    def test_briefs(self):
        p = G.tool(self.root, "new-run", "workspace-9", "sent", "--role", "referee", "--claim", "900-solve", "c1",
                   "--question", "sentence")
        self.assertEqual(p.returncode, 0, p.stderr)
        rd = os.path.join(self.root, "workspace-9", "runs", "902-sent")
        brief = open(os.path.join(rd, "BRIEF.md")).read()
        self.assertIn("the sentence read of a script claim", brief)
        # HANDOFF §6 item 20; the source's method change 78, G1 (kit-v0.4.19): a substring pin asserts a value only if it ends it
        self.assertIn("a printed value one of them pins is asserted only if the pin ends the value", " ".join(brief.split()))
        self.assertIn('"count=17" alone also matches "count=170"', " ".join(brief.split()))
        self.assertIn("A value the script only prints, and nothing pins so, is not asserted", " ".join(brief.split()))
        self.assertIn("open its `source` and `quote` files", brief)                                  # premises note
        self.assertEqual(json.load(open(os.path.join(self.root, "data", "referee-bindings", "902-sent.json")))["question"],
                         "sentence")
        n = len(os.listdir(os.path.join(self.root, "workspace-9", "runs")))
        p = G.tool(self.root, "new-run", "workspace-9", "sent2", "--role", "referee", "--claim", "900-solve", "c2",
                   "--question", "sentence")
        self.assertNotEqual(p.returncode, 0)
        self.assertIn("for script claims", p.stderr)
        self.assertEqual(len(os.listdir(os.path.join(self.root, "workspace-9", "runs"))), n)      # nothing created
        for q in ("certify", "hypotheses"):
            p = G.tool(self.root, "new-run", "workspace-9", "r" + q, "--role", "referee", "--claim", "900-solve", "c2",
                       "--question", q)
            self.assertEqual(p.returncode, 0, p.stderr)
            rd = [d for d in os.listdir(os.path.join(self.root, "workspace-9", "runs")) if d.endswith("r" + q)][0]
            b = open(os.path.join(self.root, "workspace-9", "runs", rd, "BRIEF.md")).read()
            self.assertIn("is a `gap`", b)                                                          # less than the English is a gap
            self.assertIn("certifies LESS" if q == "certify" else "establishes less than the English", b)
            self.assertIn("open its `source` and `quote` files", b)

    def test_long_checks_in_every_referee_brief(self):
        """LESSONS.md "A headless referee finishes its checks in its turn": every referee question's brief says it, once, just
        before the Output section."""
        for q, cid in (("certify", "c2"), ("hypotheses", "c2"), ("sentence", "c1")):
            p = G.tool(self.root, "new-run", "workspace-9", "lc" + q, "--role", "referee", "--claim", "900-solve", cid,
                       "--question", q)
            self.assertEqual(p.returncode, 0, p.stderr)
            rd = [d for d in os.listdir(os.path.join(self.root, "workspace-9", "runs")) if d.endswith("lc" + q)][0]
            b = open(os.path.join(self.root, "workspace-9", "runs", rd, "BRIEF.md")).read()
            self.assertEqual(b.count("**Long checks.** You run headless"), 1, q)
            self.assertIn("Write output/referee.json before you end your turn.\n\n## Output: `output/referee.json`", b)
            # P-15 (user 2026-10-03: "a"): a worker's Bash runs in the foreground; no brief offers a background job
            self.assertNotIn("in the background and poll", b)
            self.assertIn("in the foreground", b)
            self.assertNotIn("{long_checks}", b)

    def test_network_referee(self):
        """LESSONS.md "A networked referee's brief carries the network paragraph": a networked referee's brief carries the network paragraph."""
        for q, net in (("certify", True), ("hypotheses", True), ("certify", False)):
            args = ["new-run", "workspace-9", f"n{q}{int(net)}", "--role", "referee", "--claim", "900-solve", "c2", "--question", q]
            p = G.tool(self.root, *args, *(["--harness", "claude-net"] if net else []))
            self.assertEqual(p.returncode, 0, p.stderr)
            rd = [d for d in os.listdir(os.path.join(self.root, "workspace-9", "runs")) if d.endswith(f"n{q}{int(net)}")][0]
            rd = os.path.join(self.root, "workspace-9", "runs", rd)
            self.assertEqual("**Network (this run only).**" in open(os.path.join(rd, "BRIEF.md")).read(), net)
            self.assertEqual(os.path.exists(os.path.join(rd, "HARNESS-NOTE.md")), net)
        p = G.tool(self.root, "new-run", "workspace-9", "nsent", "--role", "referee", "--claim", "900-solve", "c1",
                   "--question", "sentence", "--harness", "claude-net")
        self.assertEqual(p.returncode, 0, p.stderr)

    def test_earned_needs_sentence(self):
        import _lib as L
        c = self.doc["claims"][0]
        self.assertEqual(L.earned_tag("VERIFIED", "pass", [], *L.sentence_need(self.doc, c, []))[0], "PENDING")
        live = [{"question": "sentence", "verdict": "holds"}]
        self.assertEqual(L.earned_tag("VERIFIED", "pass", ["holds"], *L.sentence_need(self.doc, c, live))[0], "VERIFIED")
        old = dict(self.doc, schema="kit/claims/1")
        self.assertEqual(L.earned_tag("VERIFIED", "pass", [], *L.sentence_need(old, c, []))[0], "VERIFIED")
        self.assertEqual(L.earned_tag("VERIFIED", "pass", ["gap"], *L.sentence_need(self.doc, c, []))[0], "GAP")

    def test_package_warning(self):
        p = subprocess.run(["/usr/bin/python3", os.path.join(G.BIN, "validate-claims"), self.rd], text=True, capture_output=True)
        self.assertIn("appears to use cypari2", p.stdout)


class T11Packet(Base):
    """LESSONS.md "No packet carries blocked material": the packet scan, driven by the instance's data/packet-rules.json."""

    SECRET = "the route of the quiet lemma has a probability of eleven percent in our honest estimate today"
    COMMON = "every entry of the square is the square of a positive integer and the nine are distinct here"
    RANK = r"\bI rank\b|\brecommend|\bprobabilit|\b\d+(?:\.\d+)?\s?%"

    def setUp(self):
        super().setUp()
        w = lambda rel, t: (os.makedirs(os.path.dirname(os.path.join(self.root, rel)), exist_ok=True),
                            open(os.path.join(self.root, rel), "w").write(t))
        w("notes/opinions.md", f"# register\n{self.SECRET}.\n{self.COMMON}.\n")
        w("problems/x/PROBLEM.md", f"# problem\n{self.COMMON}.\n")
        w("workspace-1/runs/005-attack-audit/BRIEF.md", "audit\n")
        w("workspace-1/runs/005-attack-audit/output/result.md",
          "I rank the first direction above the second because its lemma is shorter and cleaner to state.\n"
          "The quartic has no rational point other than the trivial ones by a two-descent written out below.\n")
        self.rules({"blocked": [{"path": "notes/opinions.md", "why": "the user's register"},
                                {"path": "workspace-1/runs/080-direction-audit-2", "why": "a direction audit"}],
                    "lines": [{"path": "workspace-1/runs/005-attack-audit", "match": self.RANK, "why": "run 005's ranking lines"}]})
        sys.modules.pop("_packet", None)
        sys.modules.pop("_lib", None)
        import _packet
        self.P = _packet

    def rules(self, r):
        os.makedirs(os.path.join(self.root, "data"), exist_ok=True)
        json.dump(r, open(os.path.join(self.root, "data", "packet-rules.json"), "w"))

    def put(self, name, text):
        p = os.path.join(self.rd, "input", name)
        open(p, "w").write(text)
        return p

    def test_route_verdicts(self):
        """The source's method change 50: with "verdicts": true a route-verdict word is an error from any file of the packet,
        the brief included; ordinary prose ("rank 0", "declared dead", "Pursue the route") is not; off without the key."""
        self.rules({"blocked": [], "lines": []})
        self.put("v.md", "the direction was PARKed\n")
        self.assertEqual(self.P.findings(self.rd), ([], []))                                  # off: no key
        os.remove(os.path.join(self.rd, "input", "v.md"))
        self.rules({"blocked": [], "lines": [], "verdicts": True})
        for i, line in enumerate(("the fibre-by-fibre direction PARKed (its ranking #7)", "It is ranked first.",
                                  "the only direction classed PURSUE", "each with a class PURSUE / PARK / DEAD",
                                  "Status: parked by the user", "#2 in the ranking", "the most promising route",
                                  "a long shot", "worth pursuing now")):
            with self.subTest(line=line):
                p = self.put(f"v{i}.md", f"intro\n{line}\n")
                e = self.P.findings(self.rd)[0]
                self.assertEqual(len(e), 1, e)
                self.assertIn(f"v{i}.md:2: route-verdict word", e[0])
                os.remove(p)
        self.put("ok.md", "Y^2 = X^3 - X has rank 0; the matrix has rank 6. Directions declared dead: blind search.\n"
                          "Pursue the route to its end. Parker fields are classified. A ranking of routes is not wanted.\n")
        self.assertEqual(self.P.findings(self.rd), ([], []))
        open(os.path.join(self.rd, "BRIEF.md"), "w").write("Report the route; do not rank anything.\nPARK nothing.\n")
        self.assertIn("BRIEF.md:2: route-verdict word 'PARK'", self.P.findings(self.rd)[0][0])   # the brief is scanned too
        self.rules({"blocked": [], "lines": [], "verdicts": r"\bdoomed\b"})                    # an instance's own pattern
        open(os.path.join(self.rd, "BRIEF.md"), "w").write("this route is doomed\n")
        self.assertIn("route-verdict word 'doomed'", self.P.findings(self.rd)[0][0])

    def test_no_rules_nothing_blocked(self):
        os.remove(os.path.join(self.root, "data", "packet-rules.json"))
        self.put("z.md", f"context: {self.SECRET}\n")
        self.assertEqual(self.P.findings(self.rd), ([], []))

    def test_scan(self):
        self.assertEqual(self.P.findings(self.rd), ([], []))
        self.put("x.md", f"note: {self.COMMON}.\n")                                          # open text: fine
        self.put("y.md", "The quartic has no rational point other than the trivial ones by a two-descent written out below.\n")
        self.assertEqual(self.P.findings(self.rd)[0], [])                                    # a line-rule file, not a ranking line: fine
        self.put("z.md", f"context: {self.SECRET}\n")
        e, w = self.P.findings(self.rd)
        self.assertEqual(len(e), 1)
        self.assertIn("z.md: shares text with blocked notes/opinions.md", e[0])
        os.remove(os.path.join(self.rd, "input", "z.md"))
        self.put("r.md", "I rank the first direction above the second because its lemma is shorter and cleaner to state.\n")
        self.assertIn("run 005's ranking lines", self.P.findings(self.rd)[0][0])
        os.remove(os.path.join(self.rd, "input", "r.md"))
        shutil.copyfile(os.path.join(self.root, "notes", "opinions.md"), os.path.join(self.rd, "input", "copy.md"))
        self.assertIn("byte-identical to blocked notes/opinions.md", self.P.findings(self.rd)[0][0])
        sha = hashlib.sha256(open(os.path.join(self.rd, "input", "copy.md"), "rb").read()).hexdigest()
        json.dump([{"sha256": sha, "path": "notes/opinions.md", "ruling": "test"}],
                  open(os.path.join(self.root, "data", "packet-exceptions.json"), "w"))
        self.assertEqual(self.P.findings(self.rd)[0], [])                                    # excepted by the user
        self.put("n.md", "see notes/opinions.md\n")
        self.assertTrue(any("names blocked material" in x for x in self.P.findings(self.rd)[1]))

    def mkrun(self, name, launched, text=None, where="output/quote.md"):
        rd = os.path.join(self.root, "workspace-9", "runs", name)
        os.makedirs(os.path.join(rd, os.path.dirname(where)), exist_ok=True)
        open(os.path.join(rd, "BRIEF.md"), "w").write("b\n")
        if launched:
            open(os.path.join(rd, "launch.log"), "w").write("{}\n")
        if text:
            open(os.path.join(rd, where), "w").write(text)
        return rd

    def test_what_excuses_a_packet(self):
        """Only open material excuses a packet: the output/ of an EARLIER run that was launched or checked. Its own run,
        a sibling packet, a later run and a run never launched do not."""
        self.put("z.md", f"context: {self.SECRET}\n")
        self.assertTrue(self.P.findings(self.rd)[0])
        self.mkrun("901-later", True, f"{self.SECRET}\n")                               # later, launched
        self.mkrun("898-never", False, f"{self.SECRET}\n")                              # earlier, never launched
        self.mkrun("897-packet", True, f"{self.SECRET}\n", where="input/quote.md")      # earlier, but a packet
        self.assertTrue(self.P.findings(self.rd)[0])
        self.mkrun("896-early", True, f"{self.SECRET}\n")                               # earlier, launched: open
        self.assertEqual(self.P.findings(self.rd)[0], [])

    def test_every_file_is_read(self):
        """A packet file is read as text whatever its name; a blocked run's transcript is indexed, minus what the run
        was given in its own input/."""
        for name in ("notes", "z.log", "z.rst"):
            with self.subTest(name=name):
                p = self.put(name, f"context: {self.SECRET}\n")
                self.assertTrue(self.P.findings(self.rd)[0], name)
                os.remove(p)
        b = os.path.join(self.root, "workspace-1", "runs", "080-direction-audit-2")
        os.makedirs(os.path.join(b, "input"))
        open(os.path.join(b, "BRIEF.md"), "w").write("audit\n")
        given = "the square of a positive integer is recorded in a table of nine cells for the audit here"
        said = "our estimate for the lemma route is twelve percent and falling after the second reading today"
        open(os.path.join(b, "input", "given.md"), "w").write(given + "\n")
        open(os.path.join(b, "launch.log"), "w").write(json.dumps({"read": given, "wrote": said}) + "\n")
        self.put("g.md", given + "\n")
        self.assertEqual(self.P.findings(self.rd)[0], [])                               # what the run was given: not blocked
        self.put("s.md", said + "\n")
        self.assertIn("080-direction-audit-2/launch.log", self.P.findings(self.rd)[0][0])   # what it said: blocked

    def test_exception_is_neither_blocked_nor_open(self):
        """An excepted file in an open run does not make its text open for other packets."""
        early = self.mkrun("896-early", True, f"{self.SECRET}\n", where="output/excepted.md")
        sha = hashlib.sha256(open(os.path.join(early, "output", "excepted.md"), "rb").read()).hexdigest()
        json.dump([{"sha256": sha, "path": os.path.relpath(os.path.join(early, "output", "excepted.md"), self.root), "ruling": "test"}],
                  open(os.path.join(self.root, "data", "packet-exceptions.json"), "w"))
        self.put("z.md", f"context: {self.SECRET}\n")
        self.assertTrue(self.P.findings(self.rd)[0])

    def test_launch_path_ignores_a_doctored_cache(self):
        """The outside review's F5: the cache is orchestrator-writable state; the launch path's scan (lint-brief --packet)
        rebuilds the index, so an emptied cache with a matching fingerprint does not let a packet through."""
        self.put("z.md", f"context: {self.SECRET}\n")
        self.assertTrue(self.P.findings(self.rd)[0])                                     # builds and caches the index
        cache = os.path.join(self.root, self.P.CACHE)
        c = json.load(open(cache)); c["hashes"], c["text"] = {}, {}
        json.dump(c, open(cache, "w"))
        self.assertEqual(self.P.findings(self.rd)[0], [])                                # the cache is trusted off the launch path
        p = G.tool(self.root, "lint-brief", "--packet", "900-solve")
        self.assertEqual(p.returncode, 1, p.stdout)                                      # but never on it
        self.assertIn("shares text with blocked notes/opinions.md", p.stdout)

    def test_large_text_is_a_failure_not_a_hash(self):
        """The outside review's F9: text too large to index fails the scan (blocked) or the packet (a packet file), never a
        silent comparison by hash alone."""
        self.P.MAX_BYTES = 200
        try:
            self.put("big.md", "word " * 100)
            self.assertTrue(any("too large to scan" in e for e in self.P.findings(self.rd, use_cache=False)[0]))
            os.remove(os.path.join(self.rd, "input", "big.md"))
            open(os.path.join(self.root, "notes", "opinions.md"), "a").write("word " * 100)
            with self.assertRaises(self.P.TooLarge):
                self.P.findings(self.rd, use_cache=False)
        finally:
            self.P.MAX_BYTES = 50_000_000

    def test_exception_follows_its_file(self):
        """The outside review's F10: an exception is live only while its file still has the excepted bytes; a malformed
        list is a failed scan, not an empty one."""
        shutil.copyfile(os.path.join(self.root, "notes", "opinions.md"), os.path.join(self.rd, "input", "copy.md"))
        sha = hashlib.sha256(open(os.path.join(self.rd, "input", "copy.md"), "rb").read()).hexdigest()
        ex = os.path.join(self.root, "data", "packet-exceptions.json")
        json.dump([{"sha256": sha, "path": "notes/opinions.md", "ruling": "test"}], open(ex, "w"))
        self.assertEqual(self.P.findings(self.rd, use_cache=False)[0], [])
        open(os.path.join(self.root, "notes", "opinions.md"), "a").write("revised by the user\n")
        self.assertTrue(self.P.findings(self.rd, use_cache=False)[0])                    # the old bytes are no longer excepted
        open(ex, "w").write('{"not": "a list"}')
        with self.assertRaises(ValueError):
            self.P.findings(self.rd, use_cache=False)

    def test_lint_refuses_and_a_bad_rules_file_is_a_failed_scan(self):
        self.put("z.md", f"context: {self.SECRET}\n")
        p = G.tool(self.root, "lint-brief", "--packet", "900-solve")
        self.assertEqual(p.returncode, 1, p.stdout)
        self.assertIn("packet: input/z.md: shares text with blocked notes/opinions.md", p.stdout)
        open(os.path.join(self.root, "data", "packet-rules.json"), "w").write("{not json")
        p = G.tool(self.root, "lint-brief", "--packet", "900-solve")
        self.assertEqual(p.returncode, 4, p.stdout + p.stderr)                          # a scan that could not read its rules


class T12ClaimsExtract(Base):
    """The source's method change 52 (LESSONS.md "A worker's extract of the ledger is made by a tool"): the worker's view of
    the ledger is made by fixed rules; what it leaves out beyond them is the user's list."""

    LEDGER = (
        "# CLAIMS\n\nintro\n\n"
        "## C-001  [PROVED]  2026-09-20  run 008-a/c1\nStatement one.\n"
        "Artifact (lean): x/A.lean  sha256=aa  decls=Lib.foo,Run7.bar  axioms={}\nSilent links: none\n"
        "Check: pass (x)\nReferee: holds (x)\nSupersedes: —\n\n"
        "## C-002  [GAP]  2026-09-20  run 009-b/c1\nStatement two.\nClaimed: [PROVED]; earned [GAP] because a referee found a gap.\n"
        "Artifact (text): x/p.md  sha256=bb\nDeps: x/q.md sha256=cc\nSilent links: s\nCheck: n/a (x)\nReferee: gap (x)\n"
        "Supersedes: —\n\n"
        "## C-001-note  2026-09-21  A note on one.\n\n"
        "## C-002-note  2026-09-21  A note on two, superseded later.\n\n"
        "## C-032  [PROVED]  2026-09-22  run 010-c/c1  (conditional: source)\nStatement three,\nover two lines.\n"
        "Artifact (text): x/r.md  sha256=dd\nPremises: source: a note as stated\nSilent links: none\nCheck: n/a (x)\n"
        "Referee: holds (x)\nSupersedes: C-002\n\n"
        "## C-042  [NUMERIC]  2026-09-23  run 011-d/c1\nA model sum.\nArtifact (script): x/s.py  sha256=ee  cmd=`x` exit=0\n"
        "Range: r\nCheck: pass (x)\nReferee: none\nSupersedes: —\n\n"
        "## C-042-note  2026-09-24  A note on the model.\n\n"
        "## C-032-note  2026-09-24  An evaluation's reading.\n\n"
        "## C-032-note  2026-09-25  A premise marker.\n\n"
        "## C-043  [PROVED]  2026-09-26  run 012-e/c1\nStatement five.\n"
        "Artifact (lean): x/B.lean  sha256=ff  decls=TB.baz  axioms={}\nSilent links: none\nCheck: pass (x)\n"
        "Referee: holds (x)\nSupersedes: —\n\n"
        "## C-044  [CONJECTURE]  2026-09-26  run 013-f/c1\nStatement six.\nArtifact: none\nEvidence: e\nCheck: n/a (x)\n"
        "Referee: none\nSupersedes: —\n\n")

    def setUp(self):
        super().setUp()
        open(os.path.join(self.root, "CLAIMS.md"), "w").write(self.LEDGER)

    def rules(self, extract):
        os.makedirs(os.path.join(self.root, "data"), exist_ok=True)
        json.dump({"blocked": [], "lines": [], "extract": extract},
                  open(os.path.join(self.root, "data", "packet-rules.json"), "w"))

    def test_rules(self):
        self.rules({"entries": [{"id": "C-042", "why": "a heuristic model"}, {"id": "C-043", "why": "its lemma"}],
                    "notes": [{"id": "C-032", "date": "2026-09-24", "why": "an evaluation"}]})
        p = G.tool(self.root, "claims-extract", "--library", "Lib", "--supplied", "Run7=input/Run7.lean", "--date", "2026-01-01")
        self.assertEqual(p.returncode, 0, p.stderr)
        out = p.stdout
        body = out[out.index("## C-001  "):]
        self.assertEqual(body,
            "## C-001  [PROVED]  2026-09-20  run 008-a/c1\nStatement one.\n"
            "Lean declarations: Lib.foo, Run7.bar\nSupersedes: —\n\n"
            "## C-032  [PROVED]  2026-09-22  run 010-c/c1  (conditional: source)\nStatement three,\nover two lines.\n"
            "Artifact type: text\nPremises: source: a note as stated\nSupersedes: C-002\n\n"
            "## C-044  [CONJECTURE]  2026-09-26  run 013-f/c1\nStatement six.\nArtifact type: none\nSupersedes: —\n\n"
            "# Notes on live entries (verbatim; the orchestrator's, not refereed)\n\n"
            "## C-001-note  2026-09-21  A note on one.\n\n## C-032-note  2026-09-25  A premise marker.\n")
        head = " ".join(out[:out.index("## C-001  ")].split())
        self.assertIn("(entries C-001 to C-044). It lists 3 of the 5 entries", head)
        self.assertIn("superseded entries (C-002)", head)
        self.assertIn("entries the user excludes (C-042, C-043) and their notes", head)
        self.assertIn("the notes of 2026-09-24 on C-032.", head)
        self.assertNotIn("heuristic", out)                                   # the user's why stays on the list
        self.assertIn("Lib.* are in the library mounted at $KIT_LEAN; Run7.* are in input/Run7.lean.",
                      head)   # TB.* only in the left-out C-043: no "not supplied" list
        p = G.tool(self.root, "claims-extract", "--through", "C-032", "--date", "2026-01-01")
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn("(entries C-001 to C-032). It lists 2 of the 2 entries", " ".join(p.stdout.split()))
        self.assertIn("No declarations are supplied: the prefixes (Lib.*, Run7.*) are in files not supplied",
                      " ".join(p.stdout.split()))
        self.assertNotIn("C-032-note  2026-09-25", p.stdout)   # written after C-042, so not in the ledger as of C-032
        self.assertNotEqual(G.tool(self.root, "claims-extract", "--through", "C-099").returncode, 0)
        dst = os.path.join(self.root, "x.md")
        p = G.tool(self.root, "claims-extract", "--out", dst, "--library", "Lib", "--date", "2026-01-01")
        self.assertEqual(p.returncode, 0, p.stderr)
        h = hashlib.sha256(open(dst, "rb").read()).hexdigest()
        self.assertIn(f"| CLAIMS-EXTRACT | out={dst} through=C-044 entries=3 notes=2 sha256={h}",
                      open(os.path.join(self.root, "LEDGER.log")).read())
        self.assertNotEqual(G.tool(self.root, "claims-extract", "--out", os.path.join(self.root, "CLAIMS.md")).returncode, 0)

    def test_no_list_keeps_every_live_entry(self):
        """Without an "extract" list (or without data/packet-rules.json) nothing beyond the fixed rules is left out."""
        p = G.tool(self.root, "claims-extract", "--library", "Lib", "--date", "2026-01-01")
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn("It lists 5 of the 5 entries", " ".join(p.stdout.split()))
        self.assertIn("## C-042-note  2026-09-24", p.stdout)
        self.assertIn("other prefixes (Run7.*, TB.*) are in files not supplied", " ".join(p.stdout.split()))
        self.assertNotIn("the user excludes", p.stdout)
        self.rules({})
        self.assertIn("It lists 5 of the 5 entries", " ".join(G.tool(self.root, "claims-extract").stdout.split()))
        open(os.path.join(self.root, "data", "packet-rules.json"), "w").write("{not json")
        self.assertNotEqual(G.tool(self.root, "claims-extract").returncode, 0)   # an unreadable list is not an empty one


class T13ModelRecord(Base):
    """LESSONS.md "The model a worker ran on is recorded" (the proof instance's canaries 014 and 001: Opus 5.5 refused at the
    first turn and Claude Code answered the rest of the session with Opus 4.8, under an approval that named opus)."""

    FALLBACK = [{"type": "system", "subtype": "init", "model": "claude-opus-5-5"},
                {"type": "assistant", "message": {"model": "claude-opus-5-5"}},
                {"type": "system", "subtype": "model_refusal_fallback", "original_model": "claude-opus-5-5",
                 "fallback_model": "claude-opus-4-8", "trigger": "refusal", "api_refusal_category": "cyber"},
                {"type": "assistant", "message": {"model": "claude-opus-4-8"}},
                {"type": "assistant", "message": {"model": "<synthetic>"}}]

    def write(self, run, name, events):
        open(os.path.join(self.root, "workspace-9", "runs", run, name), "w").write("\n".join(map(json.dumps, events)) + "\nnot json\n")

    def lib(self):
        sys.modules.pop("_lib", None)
        sys.path.insert(0, G.BIN)
        import _lib
        return _lib

    def test_seen_and_flag(self):
        L = self.lib()
        self.write("900-solve", "launch.log", [{"type": "assistant", "message": {"model": "claude-opus-5-5"}}] * 3)
        self.assertEqual(L.models_seen(self.rd), ({"claude-opus-5-5": 3}, []))
        self.assertIsNone(L.model_flag(self.rd, "opus"))                              # an alias is not compared
        self.write("900-solve", "launch.20260101T000000Z.log", self.FALLBACK)           # an earlier attempt counts too
        counts, falls = L.models_seen(self.rd)
        self.assertEqual(counts, {"claude-opus-5-5": 4, "claude-opus-4-8": 1})
        self.assertEqual(falls, ["claude-opus-5-5->claude-opus-4-8 (refusal/cyber)"])
        self.assertIn("fallback claude-opus-5-5->claude-opus-4-8", L.model_flag(self.rd))
        for f in ("launch.log", "launch.20260101T000000Z.log"):
            os.remove(os.path.join(self.rd, f))
        self.write("900-solve", "launch.rollout.jsonl", [{"type": "turn_context", "payload": {"model": "gpt-5.6-sol"}}])
        self.assertIsNone(L.model_flag(self.rd, "gpt-5.6-sol"))
        self.assertEqual(L.model_flag(self.rd, "gpt-6-astra"), "requested gpt-6-astra, answered by gpt-5.6-sol")

    def test_close_run_and_ledger_claims_say_so(self):
        self.write("901-ref", "launch.log", self.FALLBACK)
        p = G.tool(self.root, "close-run", self.rd, "--no-mutate")
        self.assertIn("MODEL: 901-ref was not answered by one model (fallback claude-opus-5-5->claude-opus-4-8", p.stdout)
        self.assertNotIn("MODEL: 900-solve", p.stdout)
        self.write("900-solve", "launch.log", self.FALLBACK)
        self.assertIn("MODEL: 900-solve was not answered", G.tool(self.root, "close-run", self.rd, "--no-mutate").stdout)
        L = self.lib()
        refs = L.referee_files()[("900-solve", "c1")]
        self.assertEqual([l.split(" was")[0] for l in L.model_lines(self.rd, refs)], ["MODEL: 900-solve", "MODEL: 901-ref"])
        self.assertEqual([l.split(" was")[0] for l in L.model_lines(self.rd, refs, run=False)], ["MODEL: 901-ref"])


class T14KeptCheck(Base):
    """LESSONS.md "A ledgered run's check record is kept" (the source's method change 56): a CLAIMS.md entry cites RUN/check.json
    by its generation time, and a later bin/close-run rewrote a run's record after its claims were appended. bin/check keeps the
    current record of a run with ledgered claims as check.<generated>.json before rewriting it."""

    GEN = "2026-01-01T00:00:00Z"
    KEPT = "check.2026-01-01T00-00-00Z.json"

    def set_record(self):
        path = os.path.join(self.rd, "check.json")
        with open(path, "w") as f:
            json.dump({"schema": "kit/check/2", "run": "900-solve", "generated": self.GEN, "claims": []}, f)
        return path, open(path, "rb").read()

    def ledger_it(self):
        with open(os.path.join(self.root, "CLAIMS.md"), "a") as f:
            f.write("\n## C-002  [VERIFIED]  2026-01-01  run 900-solve/c1\ns\n")

    def kept(self):
        return sorted(n for n in os.listdir(self.rd) if n.startswith("check.") and n != "check.json")

    def test_unledgered_run_rewritten_as_before(self):
        path, old = self.set_record()
        G.tool(self.root, "check", "900-solve")
        self.assertNotEqual(open(path, "rb").read(), old)
        self.assertEqual(self.kept(), [])

    def test_ledgered_run_keeps_the_cited_record(self):
        path, old = self.set_record()
        self.ledger_it()
        p = G.tool(self.root, "check", "900-solve")
        self.assertEqual(self.kept(), [self.KEPT], p.stdout + p.stderr)
        self.assertEqual(open(os.path.join(self.rd, self.KEPT), "rb").read(), old)
        self.assertNotEqual(json.load(open(path))["generated"], self.GEN)
        self.assertIn(self.KEPT, p.stdout)
        self.assertIn("CHECK-KEPT", open(os.path.join(self.root, "LEDGER.log")).read())

    def test_same_bytes_already_kept(self):
        path, old = self.set_record()
        self.ledger_it()
        open(os.path.join(self.rd, self.KEPT), "wb").write(old)
        G.tool(self.root, "check", "900-solve")
        self.assertEqual(self.kept(), [self.KEPT])
        self.assertNotEqual(json.load(open(path))["generated"], self.GEN)

    def test_other_bytes_under_the_kept_name_refused(self):
        path, old = self.set_record()
        self.ledger_it()
        open(os.path.join(self.rd, self.KEPT), "w").write("{}\n")
        p = G.tool(self.root, "check", "900-solve")
        self.assertEqual(p.returncode, 2, p.stdout + p.stderr)
        self.assertIn("refusing", p.stderr)
        self.assertEqual(open(path, "rb").read(), old)        # the record is not rewritten


def default_packet_rules():
    """bin/new-workspace's DEFAULT_PACKET_RULES, read without running the tool (it makes an instance and commits)."""
    import importlib.machinery
    import importlib.util
    loader = importlib.machinery.SourceFileLoader("new_workspace", os.path.join(G.BIN, "new-workspace"))
    spec = importlib.util.spec_from_loader("new_workspace", loader)
    m = importlib.util.module_from_spec(spec)
    loader.exec_module(m)
    return m.DEFAULT_PACKET_RULES


class T15Intake(Base):
    """LESSONS.md "Outside input has an intake record first" (the source's method changes 57 and 58): outside input lives under
    intake/, which a new instance blocks from every packet (text, bytes, and a warning on its name), and bin/verify-data checks
    every intake record's name, record.md and hashes."""

    TEXT = "the outside worker says the ceiling on the curvature is linear in the centre root for every square it tried"

    def setUp(self):
        super().setUp()
        self.d = os.path.join(self.root, "intake", "IN-001-w1")
        os.makedirs(os.path.join(self.d, "verbatim"))
        open(os.path.join(self.d, "record.md"), "w").write("# IN-001 — w1\n")
        self.v = os.path.join(self.d, "verbatim", "passage-1.txt")
        open(self.v, "w").write(self.TEXT + ".\n")
        h = hashlib.sha256(open(self.v, "rb").read()).hexdigest()
        open(os.path.join(self.d, "SHA256SUMS"), "w").write(f"{h}  verbatim/passage-1.txt\n")
        os.makedirs(os.path.join(self.root, "data"), exist_ok=True)
        json.dump(default_packet_rules(), open(os.path.join(self.root, "data", "packet-rules.json"), "w"))
        sys.modules.pop("_packet", None)
        sys.modules.pop("_lib", None)
        import _packet
        self.P = _packet

    def put(self, name, text):
        open(os.path.join(self.rd, "input", name), "w").write(text)

    def test_new_instance_blocks_intake(self):
        self.assertIn("intake", [e["path"] for e in default_packet_rules()["blocked"]])

    def test_packet_blocks_intake(self):
        self.assertEqual(self.P.findings(self.rd)[0], [])
        self.put("x.md", f"context: {self.TEXT}\n")
        e = self.P.findings(self.rd)[0]
        self.assertEqual(len(e), 1, e)
        self.assertIn("shares text with blocked intake/IN-001-w1/verbatim/passage-1.txt", e[0])
        os.remove(os.path.join(self.rd, "input", "x.md"))
        shutil.copyfile(self.v, os.path.join(self.rd, "input", "copy.txt"))
        self.assertIn("byte-identical to blocked intake/IN-001-w1", self.P.findings(self.rd)[0][0])
        os.remove(os.path.join(self.rd, "input", "copy.txt"))
        self.put("n.md", "see intake/IN-001-w1/record.md\n")
        self.assertTrue(any("names blocked material" in x for x in self.P.findings(self.rd)[1]))

    def verify(self):
        p = G.tool(self.root, "verify-data")
        return [l.strip() for l in p.stdout.splitlines() if "intake" in l]

    def test_verify_data_intake(self):
        self.assertEqual(self.verify(), [])
        open(os.path.join(self.root, "intake", "README.md"), "w").write("a file beside the records is not a record\n")
        self.assertEqual(self.verify(), [])
        open(self.v, "a").write("edited\n")
        self.assertTrue(any("intake file changed: intake/IN-001-w1/verbatim/passage-1.txt" in l for l in self.verify()))
        open(os.path.join(self.d, "verbatim", "extra.txt"), "w").write("x\n")
        self.assertTrue(any("intake file not in SHA256SUMS: intake/IN-001-w1/verbatim/extra.txt" in l for l in self.verify()))
        os.remove(os.path.join(self.d, "record.md"))
        self.assertTrue(any("intake record missing: intake/IN-001-w1/record.md" in l for l in self.verify()))
        os.makedirs(os.path.join(self.root, "intake", "IN-001-again"))
        self.assertTrue(any("intake id used twice: IN-001" in l for l in self.verify()))
        os.makedirs(os.path.join(self.root, "intake", "w2-notes"))
        self.assertTrue(any("intake folder not named IN-NNN-slug: intake/w2-notes" in l for l in self.verify()))


class T16BlockBeatsOpenRoot(Base):
    """LESSONS.md "No packet carries blocked material" (the source's method change 58): a blocked path inside an open root, or
    inside a launched run's output/, is not open material, so its own text cannot excuse itself; the same for the matching
    lines of a line rule on an open file. Text that another open file also carries stays open (the quoting limit)."""

    OWN = "the extract says to take the ceiling of the curvature as true for this run and to cite it as a source"
    MINE = "the twisted curvature at an offset prime is divisible by a large power of that prime in every solution"

    def setUp(self):
        super().setUp()
        sys.modules.pop("_packet", None)
        sys.modules.pop("_lib", None)
        import _packet
        self.P = _packet

    def rules(self, r):
        os.makedirs(os.path.join(self.root, "data"), exist_ok=True)
        json.dump(r, open(os.path.join(self.root, "data", "packet-rules.json"), "w"))

    def write(self, rel, text):
        p = os.path.join(self.root, rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        open(p, "w").write(text)
        return p

    def put(self, text):
        open(os.path.join(self.rd, "input", "x.md"), "w").write(f"context: {text}\n")

    def opened(self):
        blocked, lines = self.P.rules()
        return {os.path.relpath(q, self.root) for q in self.P.open_files(blocked, lines)}

    def test_blocked_file_under_an_open_root(self):
        rel = "problems/x/outside/extract.md"
        self.write(rel, self.OWN + ".\n")
        self.rules({"blocked": [{"path": rel, "why": "outside input"}], "lines": []})
        self.assertNotIn(rel, self.opened())
        self.put(self.OWN)
        e = self.P.findings(self.rd)[0]
        self.assertEqual(len(e), 1, e)
        self.assertIn(f"shares text with blocked {rel}", e[0])
        self.write("problems/open-copy.md", self.OWN + ".\n")                                # quoted in open material
        self.assertEqual(self.P.findings(self.rd)[0], [])

    def test_blocked_file_inside_a_launched_run(self):
        rd = os.path.join("workspace-1", "runs", "196-one-route")
        rel = os.path.join(rd, "output", "assumed-results.md")
        self.write(os.path.join(rd, "launch.log"), "ran\n")                                  # launched: its output/ is open
        self.write(rel, self.OWN + ".\n")
        self.write(os.path.join(rd, "output", "result.md"), self.MINE + ".\n")
        self.rules({"blocked": [{"path": rel, "why": "a copy of outside input"}], "lines": []})
        opened = self.opened()
        self.assertNotIn(rel, opened)
        self.assertIn(os.path.join(rd, "output", "result.md"), opened)                       # the run's own work stays open
        self.put(self.OWN)
        self.assertIn(f"shares text with blocked {rel}", self.P.findings(self.rd)[0][0])
        self.put(self.MINE)
        self.assertEqual(self.P.findings(self.rd)[0], [])

    def test_line_rule_on_an_open_file(self):
        rel = "problems/x/prior-art.md"
        self.write(rel, f"# register\nWe rank this first: {self.OWN}.\n{self.MINE}.\n")
        self.rules({"blocked": [], "lines": [{"path": rel, "match": r"\brank\b", "why": "the register's rankings"}]})
        self.put(self.OWN)
        e = self.P.findings(self.rd)[0]
        self.assertEqual(len(e), 1, e)
        self.assertIn(f"shares text with blocked {rel}", e[0])
        self.put(self.MINE)                                                                   # its other lines stay open
        self.assertEqual(self.P.findings(self.rd)[0], [])


class T17CrossFamily(Base):
    """LESSONS.md "A cross-family certify read" (the source's method change 59): a run's model family is read from the --model
    of its launch (time.log), or, for a run with no launch (a restatement the orchestrator assembled), from the run named in
    RUN/.source-run. A PROVED claim needs a live certify referee of the other family that holds, and a VERIFIED/NUMERIC claim
    that needs a sentence read needs that read from the other family. An unknown producer, or a restatement of a run of the
    other family than the orchestrator's, is met only by the user's ruling recorded in data/cross-family-rulings.json. In the kit
    the rule binds every run (no instance had ledgered claims when it came in)."""

    def mk(self, name, model=None, source=None, ruling=None):
        rd = os.path.join(self.root, "workspace-9", "runs", name)
        os.makedirs(os.path.join(rd, "output"), exist_ok=True)
        if model:
            route = "claude -p go --model %s --effort max" if model in ("opus", "fable") else \
                "/usr/bin/python3 bin/_ext.py codex RD --model %s --effort high"
            open(os.path.join(rd, "time.log"), "w").write('\tCommand being timed: "bash -c ... ' + route % model + '"\n')
        if source:
            open(os.path.join(rd, ".source-run"), "w").write(source + "\n")
        if ruling:   # the user's ruling, in data/cross-family-rulings.json since P-12 C3
            rp = os.path.join(self.root, "data", "cross-family-rulings.json")
            os.makedirs(os.path.dirname(rp), exist_ok=True)
            cur = json.load(open(rp)) if os.path.exists(rp) else {}
            cur[name] = ruling
            json.dump(cur, open(rp, "w"))
        return rd

    def lib(self):
        sys.modules.pop("_lib", None)
        import _lib
        return _lib

    def test_run_family(self):
        L = self.lib()
        f = lambda n: L.run_family(os.path.join(self.root, "workspace-9", "runs", n))
        self.mk("283-a", "opus"); self.mk("284-b", "gpt-5.6-sol"); self.mk("285-c", source="284-b")
        self.mk("286-d"); self.mk("287-e", "mystery-model"); self.mk("288-f", "gpt-6-astra"); self.mk("289-g", "fable")
        self.mk("290-h", "anthropic/claude-opus-5-5"); self.mk("291-i", "openai/gpt-6-astra")   # routed ids
        self.assertEqual((f("283-a")["family"], f("283-a")["model"]), ("Anthropic", "opus"))
        self.assertEqual(f("284-b")["family"], "OpenAI")
        self.assertEqual(f("288-f")["family"], "OpenAI")
        self.assertEqual(f("289-g")["family"], "Anthropic")
        self.assertEqual(f("290-h")["family"], "Anthropic")
        self.assertEqual(f("291-i")["family"], "OpenAI")
        self.assertEqual((f("285-c")["family"], f("285-c")["restated"]), ("OpenAI", True))
        self.assertEqual(f("286-d")["family"], "unknown")
        self.assertEqual(f("287-e")["family"], "unknown")

    def test_answered_family(self):
        """kit-v0.4.1 (user 2026-09-29, "agree"): the family is read from the models that answered when the record has
        them; answered by another family than the approved one, or by two, the producer is unknown (the user rules)."""
        L = self.lib()
        f = lambda n: L.run_family(os.path.join(self.root, "workspace-9", "runs", n))
        said = lambda rd, *ms: open(os.path.join(rd, "launch.log"), "w").write(
            "".join(json.dumps({"type": "assistant", "message": {"model": m}}) + "\n" for m in ms))
        said(self.mk("300-a", "opus"), "claude-opus-5-5", "claude-opus-4-8")                    # a fallback, same family
        said(self.mk("301-b", "opus"), "gpt-5.6-sol")                                           # another family answered
        said(self.mk("302-c", "mystery-model"), "claude-opus-5-5")                              # the answer names it
        said(self.mk("303-d", "opus"), "claude-opus-5-5", "gpt-5.6-sol")                        # two families
        self.mk("304-e", "opus")                                                                # no transcript: approved
        self.assertEqual(f("300-a")["family"], "Anthropic")
        self.assertEqual(f("301-b")["family"], "unknown")
        self.assertIn("answered by gpt-5.6-sol", f("301-b")["how"])
        self.assertEqual(f("302-c")["family"], "Anthropic")
        self.assertEqual(f("303-d")["family"], "unknown")
        self.assertEqual((f("304-e")["family"], f("304-e")["how"]), ("Anthropic", "launch"))

    def need(self, L, solver, tag, live, schema="kit/claims/2"):
        rd = os.path.join(self.root, "workspace-9", "runs", solver)
        return L.cross_family_need(rd, {"schema": schema}, {"tag": tag}, live)

    def test_an_added_family_counts(self):
        """Pending item P-5 (user 2026-10-01: "a"): a family added in kit-env.json is a family like the two built in. The
        cross-family read is a hold from any known family other than the producer's; it was OpenAI for an Anthropic
        producer and Anthropic for every other, so an added family's reads counted only through a per-run ruling."""
        json.dump({"model_families": {"Google": ["gemini"]}}, open(os.path.join(self.root, "kit-env.json"), "w"))
        L = self.lib()
        self.mk("310-g", "gemini-3-pro"); self.mk("311-p", "opus"); self.mk("312-rg", "gemini-3-pro")
        self.mk("313-rs", "gpt-5.6-sol"); self.mk("314-rf", "fable"); self.mk("315-unk", "mystery-model")
        self.assertEqual(L.run_family(os.path.join(self.root, "workspace-9", "runs", "310-g"))["family"], "Google")
        ref = lambda run, q="certify": {"referee_run": run, "question": q, "verdict": "holds"}
        holds = lambda solver, live: self.need(L, solver, "PROVED", live)[1]
        self.assertTrue(holds("310-g", [ref("313-rs")]))        # a Google producer, an OpenAI read: was refused
        self.assertTrue(holds("311-p", [ref("312-rg")]))        # an Anthropic producer, a Google read: was refused
        self.assertTrue(holds("310-g", [ref("314-rf")]))        # an Anthropic read of a Google producer: as before
        self.assertFalse(holds("310-g", [ref("312-rg")]))       # the producer's own family never counts
        self.assertFalse(holds("311-p", [ref("314-rf")]))
        self.assertFalse(holds("310-g", [ref("315-unk")]))      # an unknown family never counts
        self.assertFalse(holds("310-g", [ref("313-rs", "hypotheses")]))   # the certify question, as before

    def test_earned_tag_rows(self):
        L = self.lib()
        self.mk("283-p", "opus"); self.mk("282-old", "opus"); self.mk("290-rf", "fable"); self.mk("291-rs", "gpt-5.6-sol")
        self.mk("292-unk"); self.mk("293-src", "gpt-6-astra"); self.mk("294-rst", source="293-src")
        self.mk("295-ruled", ruling="OpenAI HANDOFF-2026-09-29")
        self.mk("296-sol", "gpt-5.6-sol")
        fab = {"referee_run": "290-rf", "question": "certify", "verdict": "holds"}
        hyp = {"referee_run": "290-rf", "question": "hypotheses", "verdict": "holds"}
        sol = {"referee_run": "291-rs", "question": "certify", "verdict": "holds"}
        tag = lambda solver, t, live: L.earned_tag(t, "pass" if t != "PROVED" else "n/a",
                                                   [r["verdict"] for r in live], *L.sentence_need(
                                                       {"schema": "kit/claims/2"}, {"tag": t}, live),
                                                   *self.need(L, solver, t, live)[:2],
                                                   questions=L.proved_questions(live))[0]
        self.assertEqual(tag("283-p", "PROVED", [fab, hyp]), "PENDING")           # same family only
        self.assertEqual(tag("283-p", "PROVED", [fab, hyp, sol]), "PROVED")       # + a cross-family certify hold
        self.assertEqual(tag("283-p", "PROVED", [fab, hyp, dict(sol, question="hypotheses")]), "PENDING")  # certify only
        self.assertEqual(tag("282-old", "PROVED", [fab, hyp]), "PENDING")         # every run binds in the kit
        self.assertEqual(tag("296-sol", "PROVED", [sol, fab, hyp]), "PROVED")     # an OpenAI producer: an Anthropic read
        self.assertEqual(tag("296-sol", "PROVED", [sol, fab]), "PENDING")         # P-3 B4: hypotheses missing
        self.assertEqual(tag("296-sol", "PROVED", [sol]), "PENDING")
        sf = {"referee_run": "290-rf", "question": "sentence", "verdict": "holds"}
        ss = {"referee_run": "291-rs", "question": "sentence", "verdict": "holds"}
        self.assertEqual(tag("283-p", "VERIFIED", [sf]), "PENDING")                # VERIFIED is no way around it
        self.assertEqual(tag("283-p", "VERIFIED", [ss]), "VERIFIED")
        self.assertEqual(tag("292-unk", "PROVED", [fab, sol]), "PENDING")         # unknown producer blocks
        self.assertEqual(tag("294-rst", "PROVED", [fab, sol]), "PENDING")         # restated from an OpenAI run: a ruling
        self.assertEqual(tag("295-ruled", "PROVED", [fab, hyp]), "PENDING")       # ruled OpenAI: Fable does not count
        self.assertEqual(tag("295-ruled", "PROVED", [fab, sol, hyp]), "PROVED")
        self.assertIn("restated by the orchestrator (Anthropic)", self.need(L, "294-rst", "PROVED", [fab])[2])
        self.assertEqual(self.need(L, "283-p", "CONJECTURE", [])[:2], (False, False))
        self.assertEqual(tag("283-p", "VERIFIED", []), "PENDING")                  # nothing yet: still pending

    def proved_run(self, refs):
        """Run 283-p (Opus) with one PROVED text claim, and a referee run per (name, model, question) that holds."""
        rd = self.mk("283-p", "opus")
        open(os.path.join(rd, "output", "p.md"), "w").write("proof\n")
        json.dump({"schema": "kit/claims/2", "run": "283-p", "problem": "x", "claims": [
            {"id": "c1", "tag": "PROVED", "statement": "s", "silent_links": ["none"], "premises": [{"kind": "classical", "what": "induction"}],
             "artifact": {"type": "text", "path": "output/p.md"}}]}, open(os.path.join(rd, "output", "claims.json"), "w"))
        json.dump({"generated": "g", "overall": "pass", "claims": [{"id": "c1", "tag": "PROVED", "check": "n/a",
                   "artifact_sha256": hashlib.sha256(b"proof\n").hexdigest()}]}, open(os.path.join(rd, "check.json"), "w"))
        for name, model, q in refs:
            r = self.mk(name, model)
            os.makedirs(os.path.join(r, "input", "artifact"))
            open(os.path.join(r, "input", "artifact", "p.md"), "w").write("proof\n")
            json.dump({"source_run": "283-p", "id": "c1", "artifact": {"type": "text", "path": "input/artifact/p.md"}},
                      open(os.path.join(r, "input", "claim.json"), "w"))
            G.bind(self.root, name, "283-p", "c1", q, hashlib.sha256(b"proof\n").hexdigest())
            json.dump({"schema": "kit/referee/1", "run": "283-p", "claim": "c1", "verdict": "holds", "pointer": "p",
                       "note": ""}, open(os.path.join(r, "output", "referee.json"), "w"))
        return rd

    def test_close_run_names_the_cross_family_read(self):
        """Two same-family reads that hold: close-run asks for the cross-family certify run, not the same two again."""
        self.proved_run((("296-ref-f", "fable", "certify"), ("298-ref-h", "fable", "hypotheses")))
        out = G.tool(self.root, "close-run", "283-p", "--no-mutate").stdout
        self.assertIn("families: producer: Anthropic (opus)", out)
        self.assertIn("missing the cross-family read", out)
        self.assertIn("ref-283-c1-xcert --role referee --claim 283-p c1 --question certify", out)
        self.assertNotIn("ref-283-c1-cert ", out)
        self.assertIn("c1: PENDING (PROVED needs a cross-family certify referee that holds)", out)

    def test_merge_shows_families(self):
        rd = self.proved_run((("296-ref-f", "fable", "certify"), ("297-ref-s", "gpt-5.6-sol", "certify")))
        p = G.tool(self.root, "merge", "283-p")
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        v = open(os.path.join(rd, "verdict.md")).read()
        self.assertIn("producer: Anthropic (opus)", v)
        self.assertIn("297-ref-s certify OpenAI (gpt-5.6-sol) holds", v)
        self.assertIn("cross-family certify: holds", v)
        self.assertIn("| c1 | PROVED |", v)


class T18RoutesAndBlocks(Base):
    """kit-v0.4.1 (user 2026-09-29, "agree"): a new instance enables a route of each family by default, and is warned when
    its routes cover one family only (LESSONS.md "A cross-family certify read"); the user can block a path before it
    exists (the proof instance's intake/ needed a mkdir first)."""

    def nw(self):
        import importlib.machinery
        import importlib.util
        loader = importlib.machinery.SourceFileLoader("new_workspace2", os.path.join(G.BIN, "new-workspace"))
        spec = importlib.util.spec_from_loader("new_workspace2", loader)
        m = importlib.util.module_from_spec(spec)
        loader.exec_module(m)
        return m

    def test_default_routes_cover_both_families(self):
        m = self.nw()
        self.assertEqual(m.DEFAULT_ROUTES, "anthropic,codex")
        self.assertIsNone(m.family_warning(m.DEFAULT_ROUTES.split(",")))
        for one in (["anthropic"], ["anthropic", "anthropic-net"], ["codex", "codex-net"]):
            self.assertIn("one model family", m.family_warning(one))
        self.assertIsNone(m.family_warning(["anthropic", "codex-net"]))
        self.assertIsNone(m.family_warning(["openrouter"]))          # its family is its --model's, per run

    def test_block_a_path_not_yet_made(self):
        p = G.tool(self.root, "packet-block", os.path.join(self.root, "intake"), "outside input")
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        self.assertIn("does not exist yet", p.stdout + p.stderr)
        rules = json.load(open(os.path.join(self.root, "data", "packet-rules.json")))
        self.assertEqual([e["path"] for e in rules["blocked"]], ["intake"])
        q = G.tool(self.root, "packet-block", "/etc/nowhere-kit", "outside the tree")
        self.assertEqual(q.returncode, 3, q.stdout + q.stderr)


class T19LedgerPremises(Base):
    """LESSONS.md "A referee is given the ledger entries a claim rests on" (the source's queued methods item, its user's
    ruling of 2026-09-30 07:34): three of its referee sets could not compare a premise's quotation with the ledger. A referee of a
    claim with `ledger` premises gets those entries, extracted by bin/claims-extract --ids under the extract's fixed rules and
    the user's exclusions, as input/ledger-premises.md."""

    def setUp(self):
        super().setUp()
        open(os.path.join(self.root, "CLAIMS.md"), "w").write(T12ClaimsExtract.LEDGER)
        os.makedirs(os.path.join(self.root, "problems", "x"), exist_ok=True)
        open(os.path.join(self.root, "problems", "x", "PROBLEM.md"), "w").write("p\n")
        out = os.path.join(self.rd, "output")
        open(os.path.join(out, "p.md"), "w").write("proof using C-001\n")
        self.doc = {"schema": "kit/claims/2", "run": "900-solve", "problem": "x", "claims": [
            {"id": "c1", "tag": "PROVED", "statement": "t", "silent_links": ["none"],
             "premises": [{"kind": "ledger", "what": "C-001"}, {"kind": "ledger", "what": "C-002"},
                          {"kind": "classical", "what": "Lagrange"}], "artifact": {"type": "text", "path": "output/p.md"}},
            {"id": "c2", "tag": "PROVED", "statement": "u", "silent_links": ["none"],
             "premises": [{"kind": "classical", "what": "Lagrange"}], "artifact": {"type": "text", "path": "output/p.md"}}]}
        json.dump(self.doc, open(os.path.join(out, "claims.json"), "w"))
        json.dump({"generated": "now", "overall": "pass", "claims": [{"id": "c1", "check": "n/a"}, {"id": "c2", "check": "n/a"}]},
                  open(os.path.join(self.rd, "check.json"), "w"))

    def test_extract_ids(self):
        p = G.tool(self.root, "claims-extract", "--ids", "C-001", "C-002")
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn("Statement one.", p.stdout)
        self.assertIn("Statement two.", p.stdout)                                  # superseded, but a premise names it
        self.assertIn("Superseded by: C-032", p.stdout)
        self.assertNotIn("A model sum.", p.stdout)                                 # only the entries asked for
        self.assertIn("A note on one.", p.stdout)
        self.assertIn("the entries C-001 and C-002", p.stdout)
        os.makedirs(os.path.join(self.root, "data"), exist_ok=True)
        json.dump({"blocked": [], "lines": [], "extract": {"entries": [{"id": "C-001", "why": "w"}]}},
                  open(os.path.join(self.root, "data", "packet-rules.json"), "w"))
        q = G.tool(self.root, "claims-extract", "--ids", "C-001", "C-002")
        self.assertNotIn("Statement one.", q.stdout)                               # the user's exclusion still holds
        self.assertIn("entries the user excludes (C-001)", q.stdout)
        r = G.tool(self.root, "claims-extract", "--ids", "C-999")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("C-999", r.stderr)

    def test_referee_packet_carries_them(self):
        p = G.tool(self.root, "new-run", "workspace-9", "ref-lp", "--role", "referee", "--claim", "900-solve", "c1",
                   "--question", "certify")
        self.assertEqual(p.returncode, 0, p.stderr)
        rd = [os.path.join(self.root, "workspace-9", "runs", d) for d in os.listdir(os.path.join(self.root, "workspace-9", "runs"))
              if d.endswith("ref-lp")][0]
        lp = open(os.path.join(rd, "input", "ledger-premises.md")).read()
        self.assertIn("Statement one.", lp)
        self.assertIn("Statement two.", lp)
        brief = " ".join(open(os.path.join(rd, "BRIEF.md")).read().split())
        self.assertIn("input/ledger-premises.md", brief)
        p = G.tool(self.root, "new-run", "workspace-9", "ref-np", "--role", "referee", "--claim", "900-solve", "c2",
                   "--question", "certify")
        self.assertEqual(p.returncode, 0, p.stderr)
        rd2 = [os.path.join(self.root, "workspace-9", "runs", d) for d in os.listdir(os.path.join(self.root, "workspace-9", "runs"))
               if d.endswith("ref-np")][0]
        self.assertFalse(os.path.exists(os.path.join(rd2, "input", "ledger-premises.md")))
        self.assertNotIn("ledger-premises", open(os.path.join(rd2, "BRIEF.md")).read())


class T20ScanVanishedFile(Base):
    """The source's run 295 (2026-09-29): a queued run's packet scan failed with FileNotFoundError, the tree having changed
    while the queue released runs (suites and a commit ran meanwhile); nothing launched and its approval was spent. A file
    of the index (blocked or open material) that disappears during the scan is taken as absent, not a crash."""

    def test_vanished_file(self):
        os.makedirs(os.path.join(self.root, "data"), exist_ok=True)
        os.makedirs(os.path.join(self.root, "problems", "x"), exist_ok=True)
        open(os.path.join(self.root, "problems", "x", "PROBLEM.md"), "w").write("open text\n")
        open(os.path.join(self.root, "notes.md"), "w").write("blocked text of the register\n")
        json.dump({"blocked": [{"path": "notes.md", "why": "w"}], "lines": []},
                  open(os.path.join(self.root, "data", "packet-rules.json"), "w"))
        sys.modules.pop("_packet", None)
        sys.modules.pop("_lib", None)
        import _packet
        real_walk = _packet._walk
        ghost = os.path.join(self.root, "problems", "x", "gone.md")                  # listed by the walk, then removed
        _packet._walk = lambda base, skip, launch=False: real_walk(base, skip, launch) + (
            [ghost, os.path.join(self.root, "notes-gone.md")] if base in ("problems", "notes.md") else [])
        try:
            self.assertEqual(_packet.findings(self.rd, use_cache=False)[0], [])
        finally:
            _packet._walk = real_walk


class T21SourceListPartOne(Base):
    """The source's methods list of 2026-09-30, items the kit shared (kit-v0.4.6): the solver brief says that a headless worker
    ending its turn ends the run (the source's runs 203, 338) and what the CPU budget's enforcement does; a note that already
    ends with the fixed suffix does not get it twice (bin/annotate-claim)."""

    def test_solver_brief(self):
        os.makedirs(os.path.join(self.root, "problems", "x"), exist_ok=True)
        open(os.path.join(self.root, "problems", "x", "PROBLEM.md"), "w").write("p\n")
        p = G.tool(self.root, "new-run", "workspace-9", "solve", "--role", "solver", "--problem", "x")
        self.assertEqual(p.returncode, 0, p.stderr)
        rd = [os.path.join(self.root, "workspace-9", "runs", d) for d in os.listdir(os.path.join(self.root, "workspace-9", "runs"))
              if d.endswith("-solve") and d != "900-solve"][0]                    # the run new-run made, not the fixture's
        b = " ".join(open(os.path.join(rd, "BRIEF.md")).read().split())
        self.assertIn("when you end your turn, the run ends, so write your deliverables before you end it", b)   # P-15
        self.assertIn("the run is stopped when its whole process tree has used them", b)

    def test_note_suffix_once(self):
        import importlib.machinery
        import importlib.util
        loader = importlib.machinery.SourceFileLoader("annotate_claim", os.path.join(G.BIN, "annotate-claim"))
        spec = importlib.util.spec_from_loader("annotate_claim", loader)
        m = importlib.util.module_from_spec(spec)
        loader.exec_module(m)
        entries = {"C-001": {}}
        line, _ = m.note_line("C-001", "A finding.", entries)
        self.assertEqual(line.count(m.NOTE_SUFFIX), 1)
        line, text = m.note_line("C-001", "A finding. " + m.NOTE_SUFFIX, entries)
        self.assertEqual(line.count(m.NOTE_SUFFIX), 1)
        self.assertEqual(text, "A finding. " + m.NOTE_SUFFIX)                  # the text the approval binds is unchanged


class T22StrictKill(Base):
    """LESSONS.md "A mutation kills only with its FAIL line" (the source's practice in its runs 304, 352, 357): a mutation
    may name, in expect_stdout_contains, the FAIL line its targeted part prints; bin/check --mutate then counts a kill only
    with the expected exit AND that line, so a crash or another part's failure is not a kill. Without the field the old rule
    holds and bin/validate-claims warns. The solver brief asks for it, for counts asserted against values fixed before
    running, and for a table in result.md from each asserted part to its check and its killing mutation."""

    SCRIPT = ("import sys, os\n"
              "d = sys.argv[1] if len(sys.argv) > 1 else 'output'\n"
              "cases = open(os.path.join(d, 'cases.txt')).read().split()\n"
              "if len(cases) != 3:\n    print('FAIL count: expected 3 cases, got', len(cases)); sys.exit(1)\n"
              "print('count=3')\n")

    def setUp(self):
        super().setUp()
        out = os.path.join(self.rd, "output")
        open(os.path.join(out, "check.py"), "w").write(self.SCRIPT)
        open(os.path.join(out, "cases.txt"), "w").write("a\nb\nc\n")
        open(os.path.join(out, "result.md"), "w").write("r\n")

    def claim(self, muts):
        doc = {"schema": "kit/claims/2", "run": "900-solve", "problem": "x", "claims": [
            {"id": "c1", "tag": "VERIFIED", "statement": "there are 3 cases", "range": "the file", "coverage": "asserted",
             "silent_links": ["none"], "premises": [{"kind": "software", "what": "Python 3.12"}],
             "artifact": {"type": "script", "path": "output/check.py", "cmd": "python3 output/check.py",
                          "deps": ["output/cases.txt"], "mutations": muts}}]}
        json.dump(doc, open(os.path.join(self.rd, "output", "claims.json"), "w"))

    DROP = "mkdir -p scratch/m && sed 1d output/cases.txt > scratch/m/cases.txt && python3 output/check.py scratch/m"
    CRASH = "python3 -c 'raise SystemExit(1)'"

    def test_validator(self):
        sys.path.insert(0, G.BIN)
        import importlib.machinery
        import importlib.util
        loader = importlib.machinery.SourceFileLoader("vc22", os.path.join(G.BIN, "validate-claims"))
        spec = importlib.util.spec_from_loader("vc22", loader)
        V = importlib.util.module_from_spec(spec)
        loader.exec_module(V)
        ok = {"type": "script", "mutations": [{"name": "m", "cmd": "x", "expect_stdout_contains": "FAIL count"}]}
        self.assertEqual(V.validate_mutations(ok), [])
        bad = {"type": "script", "mutations": [{"name": "m", "cmd": "x", "expect_stdout_contains": ""}]}
        self.assertTrue(V.validate_mutations(bad))
        c = {"tag": "VERIFIED", "artifact": {"type": "script", "mutations": [{"name": "m", "cmd": "x"}]}}
        self.assertTrue(any("names no FAIL line" in w for w in V.claim_warnings(c)))

    def check(self):
        G.tool(self.root, "check", "900-solve", "--mutate")
        return json.load(open(os.path.join(self.rd, "check.json")))["claims"][0]

    def test_a_crash_is_not_a_kill(self):
        self.claim([{"name": "crash", "cmd": self.CRASH, "expect_stdout_contains": "FAIL count"}])
        r = self.check()
        self.assertEqual(r["check"], "fail", r)
        self.assertEqual(r["mutations"]["failed_as_expected"], 0)
        self.assertIn("FAIL line", r["mutations"]["results"][0]["detail"])

    def test_the_targeted_fail_line_kills(self):
        self.claim([{"name": "drop", "cmd": self.DROP, "expect_stdout_contains": "FAIL count"}])
        r = self.check()
        self.assertEqual(r["check"], "pass", r)
        self.assertEqual(r["mutations"]["failed_as_expected"], 1)

    def test_solver_brief(self):
        os.makedirs(os.path.join(self.root, "problems", "x"), exist_ok=True)
        open(os.path.join(self.root, "problems", "x", "PROBLEM.md"), "w").write("p\n")
        p = G.tool(self.root, "new-run", "workspace-9", "solve", "--role", "solver", "--problem", "x")
        self.assertEqual(p.returncode, 0, p.stderr)
        rd = [os.path.join(self.root, "workspace-9", "runs", d) for d in os.listdir(os.path.join(self.root, "workspace-9", "runs"))
              if d.endswith("-solve") and d != "900-solve"][0]
        b = " ".join(open(os.path.join(rd, "BRIEF.md")).read().split())
        self.assertIn('"expect_stdout_contains": "FAIL', b)
        self.assertIn("a crash, or a failure of another part, is not a kill", b)
        self.assertIn("asserted by the script against a value fixed before it runs", b)
        self.assertIn("| asserted part | check | mutation that kills it |", b)
        # The source's method changes 78 and 74 (kit-v0.4.19): a pin ends its value; FAIL lines on stdout and distinct;
        # how a headless worker waits (since P-15, kit-v0.6.30: in the foreground, longer work in resumable parts).
        self.assertIn('"expect_stdout_contains": "count=17\\n"', b)
        self.assertIn("Print FAIL lines with print()", b)
        self.assertIn("No part's FAIL line may occur inside another's", b)
        self.assertIn("Split a computation longer than an hour into resumable parts", b)


class T24Environment(unittest.TestCase):
    """bin/_env.py (kit-v0.5, the user's "we need to generalize", 2026-10-01): one environment file, kit-env.json, in
    place of the hard-coded Lean and Sage cases. A module is mounted read-only for workers at its own path (or a named
    destination) with PATH and environment additions; a module that names a licence server is given only to a run whose
    launch asked for it. An instance with no kit-env.json keeps its .kit-lean / .kit-sage modules exactly. Whoever writes
    the file, a mount source that is the root, a home directory, the instance or any directory holding it, or a
    credential directory is refused (pending item P-1, its second half)."""

    def setUp(self):
        import tempfile
        self.home = tempfile.mkdtemp(prefix="env-home-")
        self.addCleanup(shutil.rmtree, self.home, True)
        self.root = os.path.join(self.home, "kits", "inst")
        os.makedirs(self.root)
        env0 = dict(os.environ)

        def restore():
            os.environ.clear()
            os.environ.update(env0)
        self.addCleanup(restore)
        os.environ["HOME"] = self.home
        sys.path.insert(0, os.path.join(G.REAL, "bin"))
        import importlib
        import _env
        self.E = importlib.reload(_env)

    def mk(self, *parts):
        p = os.path.join(self.home, *parts)
        os.makedirs(p, exist_ok=True)
        return p

    def write_env(self, d):
        json.dump(d, open(os.path.join(self.root, "kit-env.json"), "w"))

    def test_defaults(self):
        e = self.E.load(self.root)
        self.assertEqual(e.problems, [])
        self.assertEqual(e.modules, {})
        self.assertEqual(e.worker_path, [])
        self.assertEqual(self.E.model_family("claude-opus-5-5", e), "Anthropic")
        self.assertEqual(self.E.model_family("gpt-5.6-sol", e), "OpenAI")
        self.assertIsNone(self.E.model_family("gemini-3-pro", e))

    def test_old_instance_files_become_modules(self):
        elan = self.mk(".elan")
        lib = self.mk("library")
        os.symlink(lib, os.path.join(self.root, "lean"))
        open(os.path.join(self.root, ".kit-lean"), "w").write(elan + "\n")
        sage = self.mk("conda", "sage")
        os.makedirs(os.path.join(sage, "bin"))
        open(os.path.join(sage, "bin", "sage"), "w").close()
        open(os.path.join(self.root, ".kit-sage"), "w").write(sage + "\n")
        os.makedirs(os.path.join(self.root, ".claude", "sandbox"))
        open(os.path.join(self.root, ".claude", "sandbox", "sage"), "w").close()   # the shim every instance carries
        e = self.E.load(self.root)
        self.assertEqual(sorted(e.modules), ["lean", "sage"])
        args, path, envargs = self.E.sandbox_parts(e)
        self.assertIn(elan, args)
        self.assertIn(os.path.join(self.root, "lean"), args)
        self.assertTrue(path.startswith(elan + "/bin:"), path)
        self.assertIn("KIT_LEAN", envargs)
        self.assertIn("/opt/kit/bin/sage", args)
        self.assertIn("KIT_SAGE", envargs)

    def test_a_generic_module(self):
        pari = self.mk("opt", "pari")
        self.write_env({"worker_path": [], "modules": {"pari": {"binds": ["~/opt/pari"], "path": ["~/opt/pari/bin"],
                                                                "env": {"GP_DATA_DIR": "~/opt/pari/data"},
                                                                "brief": "PARI/GP: run `gp -q`."}}})
        e = self.E.load(self.root)
        self.assertEqual(e.problems, [])
        args, path, envargs = self.E.sandbox_parts(e)
        self.assertEqual(args[args.index(pari) - 1], "--ro-bind")
        self.assertTrue(path.startswith(pari + "/bin:"))
        self.assertIn(os.path.join(pari, "data"), envargs)
        self.assertIn("PARI/GP", self.E.brief_lines(e))

    def test_dangerous_mount_sources_refused(self):
        self.mk(".ssh")
        self.mk(".config")
        for bad in ("/", "~", "~/kits", self.root, os.path.join(self.root, "data"), "~/.ssh", "~/.config", "/home"):
            with self.subTest(src=bad):
                self.write_env({"modules": {"m": {"binds": [bad]}}})
                e = self.E.load(self.root)
                self.assertEqual(e.modules, {}, bad)
                self.assertTrue(any("m:" in p for p in e.problems), e.problems)
                self.assertEqual(self.E.sandbox_parts(e)[0], [])
        self.write_env({"worker_path": ["~"]})
        e = self.E.load(self.root)
        self.assertEqual(e.worker_path, [])
        self.assertTrue(e.problems)

    def test_licence_server_modules_only_on_request(self):
        tool = self.mk("opt", "mathtool")
        self.write_env({"modules": {"mt": {"binds": [tool], "path": [tool + "/bin"],
                                           "licence_servers": [{"host": "lic.example.org", "port": 16286}]}}})
        e = self.E.load(self.root)
        self.assertEqual(e.problems, [])
        self.assertTrue(e.modules["mt"].on_request)
        self.assertNotIn(tool, self.E.sandbox_parts(e)[0])
        self.assertIn(tool, self.E.sandbox_parts(e, granted={"mt"})[0])
        self.assertEqual(self.E.licence_endpoints(e, {"mt"}), [("lic.example.org", 16286)])
        self.write_env({"modules": {"mt": {"binds": [tool], "licence_servers": [{"host": "a.example.org", "port": 27000},
                                                                         {"host": "b.example.org", "port": 27000}]}}})
        self.assertNotIn("mt", self.E.load(self.root).modules)     # one listener per port inside the sandbox
        self.assertIn("127.0.0.1 lic.example.org", self.E.hosts_text([("lic.example.org", 16286)]))
        for bad in ({"host": "lic.example.org", "port": 80}, {"host": "a b", "port": 27000}, {"host": "x", "port": "y"}):
            with self.subTest(server=bad):
                self.write_env({"modules": {"mt": {"binds": [tool], "licence_servers": [bad]}}})
                e = self.E.load(self.root)
                self.assertNotIn("mt", e.modules)

    def test_model_families_extend(self):
        self.write_env({"model_families": {"Google": ["gemini"]}})
        e = self.E.load(self.root)
        self.assertEqual(self.E.model_family("gemini-3-pro", e), "Google")
        self.assertEqual(self.E.model_family("claude-fable-5-1", e), "Anthropic")

    def test_python_etc_follows_the_interpreter(self):
        """The sandboxes mount the system Python's /etc/pythonX.Y, whichever version /usr/bin/python3 is, not 3.12 by name."""
        link = os.path.join(self.home, "python3")
        os.symlink("/usr/bin/python3.11", link)
        want = "/etc/python3.11" if os.path.isdir("/etc/python3.11") else None
        self.assertEqual(self.E.python_etc(link), want)
        real = "/etc/" + os.path.basename(os.path.realpath("/usr/bin/python3"))
        self.assertEqual(self.E.python_etc(), real if os.path.isdir(real) else None)

    def test_malformed_file_is_a_problem_not_a_crash(self):
        open(os.path.join(self.root, "kit-env.json"), "w").write("{not json")
        e = self.E.load(self.root)
        self.assertTrue(e.problems)
        self.assertEqual(e.modules, {})


class T25CodexLocation(unittest.TestCase):
    """bin/_ext.py finds Codex's real binary from the `codex` command (kit-v0.5): the npm package's
    vendor/<target>/bin/codex, or a native binary's own directory; kit-env.json's codex_bin_dir, or KIT_CODEX_BIN_DIR, first.
    It was one hard-coded Homebrew path."""

    def setUp(self):
        import tempfile
        self.t = tempfile.mkdtemp(prefix="codex-loc-")
        self.addCleanup(shutil.rmtree, self.t, True)
        sys.path.insert(0, os.path.join(G.REAL, "bin"))
        import _ext
        self.X = _ext

    def test_npm_package(self):
        pkg = os.path.join(self.t, "lib", "node_modules", "@openai", "codex")
        vend = os.path.join(pkg, "node_modules", "@openai", "codex-linux-arm64", "vendor", "aarch64-unknown-linux-musl", "bin")
        os.makedirs(os.path.join(pkg, "bin"))
        os.makedirs(vend)
        open(os.path.join(pkg, "bin", "codex.js"), "w").write("#!/usr/bin/env node\n")
        open(os.path.join(vend, "codex"), "w").write("x")
        os.makedirs(os.path.join(self.t, "bin"))
        os.symlink(os.path.join(pkg, "bin", "codex.js"), os.path.join(self.t, "bin", "codex"))
        self.assertEqual(self.X.find_codex_bin_dir(os.path.join(self.t, "bin", "codex"), None, {}), vend)

    def test_native_binary(self):
        d = os.path.join(self.t, "native")
        os.makedirs(d)
        open(os.path.join(d, "codex"), "wb").write(b"\x7fELF" + b"\0" * 60)
        self.assertEqual(self.X.find_codex_bin_dir(os.path.join(d, "codex"), None, {}), d)

    def test_overrides_first(self):
        self.assertEqual(self.X.find_codex_bin_dir("codex", "/opt/x", {}), "/opt/x")
        self.assertEqual(self.X.find_codex_bin_dir("codex", "/opt/x", {"KIT_CODEX_BIN_DIR": "/opt/y"}), "/opt/y")


class T26CheckEnv(unittest.TestCase):
    """bin/check-env (kit-v0.5): what this machine offers the kit, required parts and optional ones, the environment
    file's problems and each module's self-test inside a worker's sandbox; exit 1 on any FAIL."""

    def run_check(self, root):
        return subprocess.run(["/usr/bin/python3", os.path.join(G.BIN, "check-env")], capture_output=True, text=True,
                              env=dict(os.environ, KIT_ROOT=root), timeout=120)

    def setUp(self):
        self.root, self.rd = G.make_root()
        self.addCleanup(shutil.rmtree, self.root, True)
        shutil.copytree(os.path.join(G.REAL, ".claude"), os.path.join(self.root, ".claude"),
                        ignore=shutil.ignore_patterns("state", "settings.json", "settings.local.json"))
        for d in ("bin", "harness"):
            os.symlink(os.path.join(G.REAL, d), os.path.join(self.root, d))

    def test_reports_the_machine(self):
        p = self.run_check(self.root)
        for item in ("python", "bwrap", "systemd user scope", "claude", "codex", "kit-env.json"):
            with self.subTest(item=item):
                self.assertRegex(p.stdout, rf"(?m)^(ok|WARN|FAIL)\s+{re.escape(item)}\b")

    def test_a_module_self_test_runs_in_the_sandbox(self):
        import tempfile
        tool = tempfile.mkdtemp(prefix="tool-")
        self.addCleanup(shutil.rmtree, tool, True)
        open(os.path.join(tool, "hello"), "w").write("#!/bin/sh\necho hello-from-module\n")
        os.chmod(os.path.join(tool, "hello"), 0o755)
        json.dump({"modules": {"good": {"binds": [tool], "path": [tool], "check": "hello"},
                               "bad": {"binds": [tool], "path": [tool], "check": "false"}}},
                  open(os.path.join(self.root, "kit-env.json"), "w"))
        p = self.run_check(self.root)
        self.assertRegex(p.stdout, r"(?m)^ok\s+module good\b")
        self.assertRegex(p.stdout, r"(?m)^FAIL\s+module bad\b")
        self.assertEqual(p.returncode, 1, p.stdout)

    def test_environment_problems_fail(self):
        json.dump({"modules": {"home": {"binds": ["~"]}}}, open(os.path.join(self.root, "kit-env.json"), "w"))
        p = self.run_check(self.root)
        self.assertRegex(p.stdout, r"(?m)^FAIL\s+kit-env.json\b.*home")
        self.assertEqual(p.returncode, 1)


class T27EnvironmentInUse(Base):
    """kit-v0.5: an instance's environment file in use. bin/new-workspace --env FILE checks the file against the new
    instance before writing anything; bin/verify-data reports the file's problems; bin/new-run --module NAME records a
    run's licence modules in RUN/.modules (bound with the run's bytes) and every brief names the modules its worker has."""

    def setUp(self):
        super().setUp()
        import tempfile
        self.tool = tempfile.mkdtemp(prefix="tool-")
        self.addCleanup(shutil.rmtree, self.tool, True)
        os.makedirs(os.path.join(self.root, "problems", "x"), exist_ok=True)
        open(os.path.join(self.root, "problems", "x", "PROBLEM.md"), "w").write("p\n")

    def env(self, d):
        json.dump(d, open(os.path.join(self.root, "kit-env.json"), "w"))

    def nw(self):
        import importlib.machinery
        import importlib.util
        loader = importlib.machinery.SourceFileLoader("new_workspace_env", os.path.join(G.BIN, "new-workspace"))
        spec = importlib.util.spec_from_loader("new_workspace_env", loader)
        mod = importlib.util.module_from_spec(spec)
        loader.exec_module(mod)
        return mod

    def test_new_workspace_checks_the_file(self):
        nw = self.nw()
        good = os.path.join(self.tool, "good.json")
        json.dump({"modules": {"pari": {"binds": [self.tool]}}}, open(good, "w"))
        self.assertEqual(nw.env_file_problems(good, "/nonexistent/new-instance", lean=None, sage=None), [])
        bad = os.path.join(self.tool, "bad.json")
        json.dump({"modules": {"h": {"binds": ["~"]}}}, open(bad, "w"))
        self.assertTrue(nw.env_file_problems(bad, "/nonexistent/new-instance", lean=None, sage=None))
        self.assertEqual(nw.env_file_problems(good, "/x", lean="/lib", sage=None), [])   # --lean beside the file's modules
        d = nw.with_flag_modules({"modules": {"pari": {"binds": [self.tool]}}}, "/kits/i", lean="/lib", toolchain="/tc",
                                 sage="/sage")
        self.assertEqual(sorted(d["modules"]), ["lean", "pari", "sage"])   # what .kit-lean / .kit-sage would have mounted
        self.assertEqual(d["modules"]["lean"]["binds"], ["/tc", "<root>/lean"])
        self.assertIn({"src": "<root>/.claude/sandbox/sage", "dest": "/opt/kit/bin/sage"}, d["modules"]["sage"]["binds"])

    def test_verify_data_reports_the_file(self):
        self.env({"modules": {"h": {"binds": ["~"]}}})
        p = G.tool(self.root, "verify-data")
        self.assertIn("kit-env.json", p.stdout + p.stderr)

    def test_new_run_records_modules_and_briefs_name_them(self):
        self.env({"modules": {"lic": {"binds": [self.tool], "brief": "LicTool: run `lictool`.",
                                      "licence_servers": [{"host": "lic.example.org", "port": 27000}]},
                              "free": {"binds": [self.tool], "brief": "FreeTool: run `freetool`."}}})
        p = G.tool(self.root, "new-run", "workspace-9", "mods", "--role", "solver", "--problem", "x", "--module", "lic")
        self.assertEqual(p.returncode, 0, p.stderr)
        rd = os.path.join(self.root, "workspace-9", "runs", [d for d in os.listdir(os.path.join(self.root, "workspace-9", "runs"))
                                                             if d.endswith("-mods")][0])
        self.assertEqual(open(os.path.join(rd, ".modules")).read().split(), ["lic"])
        b = open(os.path.join(rd, "BRIEF.md")).read()
        self.assertIn("LicTool: run `lictool`.", b)
        self.assertIn("FreeTool: run `freetool`.", b)
        n = len(os.listdir(os.path.join(self.root, "workspace-9", "runs")))
        p = G.tool(self.root, "new-run", "workspace-9", "mods2", "--role", "solver", "--problem", "x", "--module", "free")
        self.assertNotEqual(p.returncode, 0)                                  # not a licence module
        self.assertEqual(len(os.listdir(os.path.join(self.root, "workspace-9", "runs"))), n)   # nothing created


KIT_SCRIPTS_DOCS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts", "docs")


@unittest.skipUnless(os.path.isfile(os.path.join(KIT_SCRIPTS_DOCS, "check_docs.py")), "the kit's own docs tools (not in an instance)")
class T23DocsIntegrity(unittest.TestCase):
    """The public documentation (kit-v0.5, the user's documentation plan of 2026-10-01): the docs checker rebuilds, on
    every run, the graph of rules, lessons, tools, templates, pages and tags from the files, and refuses a dangling link
    or lesson pointer, an orphan lesson, a tool or template with no reference entry, a stale generated page, a changelog
    out of step with the tags, or a machine path or session name in a published file. Each case is a fixture with one
    break, so the checker is seen to fail before it is seen to pass."""

    @classmethod
    def setUpClass(cls):
        sys.path.insert(0, KIT_SCRIPTS_DOCS)
        import check_docs, gen_reference
        cls.C, cls.R = check_docs, gen_reference

    def setUp(self):
        import tempfile
        self.root = tempfile.mkdtemp(prefix="docs-fixture-")
        self.addCleanup(shutil.rmtree, self.root, True)
        self.w("LESSONS.md", "# Lessons\n- **Batch consent: one go covers one thing** → incident.\n"
                             "2. **Cite or derive** → none.\n- **A label that wraps onto\n  the next line** → x.\n")
        self.w("RULES.md", "# Rules\n## 6. Approvals — the gate\nText (→ **Batch consent**). (→ **Cite or derive**)\n"
                           "(→ **A label that wraps onto the next line**)\n")
        self.w("bin/tool-a", '#!/usr/bin/python3\n"""bin/tool-a X\n\nDoes a. LESSONS.md "Cite or derive"."""\nprint(1)\n')
        self.w("templates/README.md", "| `form.md` | a form |\n")
        self.w("templates/form.md", "a form\n")
        self.w("docs/index.md", "# Index\nSee [the gate](../RULES.md#6-approvals--the-gate). [Tools](reference/tools/README.md),\n"
                                "[events](reference/ledger-events.md).\n")
        self.R.write_all(self.root)

    def w(self, rel, text):
        p = os.path.join(self.root, rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        open(p, "w").write(text)

    def problems(self, only=None):
        return self.C.check(self.root, only=only)

    def test_clean_fixture_passes(self):
        self.assertEqual(self.problems(), [])

    def test_label_forms_and_prefix_pointers(self):
        labels = self.C.lesson_labels(open(os.path.join(self.root, "LESSONS.md")).read())
        self.assertIn("A label that wraps onto the next line", labels)
        self.assertIn("Cite or derive", labels)
        self.assertTrue(self.C.resolves("Batch consent", labels))
        self.assertTrue(self.C.resolves("`Cite` or derive", ["`Cite` or derive; more"]))
        self.assertFalse(self.C.resolves("Batches", labels))          # not a prefix of any label
        self.assertFalse(self.C.resolves("consent", labels))          # a middle, not a start

    def test_github_anchors(self):
        a = self.C.anchors("## 6. Approvals — the gate\n### `bin/new-run`\n## Same\n## Same\n")
        self.assertEqual(a, {"6-approvals--the-gate", "binnew-run", "same", "same-1"})

    def test_broken_link(self):
        self.w("docs/index.md", "[x](../RULES.md#7-no-such) [y](missing.md)\n")
        p = self.problems("links")
        self.assertEqual(len(p), 2, p)

    def test_dangling_pointer_and_orphan_lesson(self):
        self.w("RULES.md", "# Rules\n(→ **No such lesson**) (→ **Cite or derive**)\n")
        p = self.problems("lessons")
        self.assertTrue(any("No such lesson" in x for x in p), p)
        self.assertTrue(any("Batch consent" in x and "nothing points" in x for x in p), p)

    def test_tool_and_template_coverage(self):
        self.w("bin/tool-b", "#!/usr/bin/env bash\n# bin/tool-b: does b.\necho b\n")
        self.w("templates/other.md", "x\n")
        p = self.problems("coverage")
        self.assertTrue(any("tool-b" in x for x in p), p)
        self.assertTrue(any("other.md" in x for x in p), p)

    def test_stale_generated_page(self):
        page = os.path.join(self.root, "docs", "reference", "tools", "tool-a.md")
        open(page, "a").write("hand edit\n")
        self.assertTrue(any("tool-a.md" in x for x in self.problems("generated")))

    def test_published_files_are_clean(self):
        self.w("docs/guide.md", "Run it from /home/someone/kit as maths-kit-b8 did, or ud-orchestrator-36.\n")  # sanitize: fixture
        self.w("HANDOFF.md", "/home/someone is fine here: not published.\n")  # sanitize: fixture
        p = self.problems("sanitize")
        self.assertEqual(sum("docs/guide.md" in x for x in p), 3, p)
        self.assertFalse(any("HANDOFF.md" in x for x in p), p)

    def test_the_kit_itself_passes(self):
        """The checks above ran on fixtures only, so the kit's own pages drifted unnoticed: from kit-v0.6.21 to v0.6.25
        five lessons had no rule pointing at them and five generated pages were stale (found 2026-10-02 updating the
        docs). The kit's own tree, every check (the changelog's newest entry may be untagged: a methods session writes it
        before its tag)."""
        self.assertEqual(self.C.check(G.REAL), [])

    def test_changelog_matches_tags(self):
        subprocess.run(["git", "init", "-q", self.root], check=True)
        subprocess.run(["git", "-C", self.root, "-c", "user.name=t", "-c", "user.email=t@example.invalid", "commit", "-q",
                        "--allow-empty", "-m", "x"], check=True)
        subprocess.run(["git", "-C", self.root, "tag", "kit-v0.1"], check=True)
        self.w("KIT-CHANGELOG.md", "# Kit changelog\n## kit-v0.3 — d — t\n## kit-v0.2 — d — t\n")
        subprocess.run(["git", "-C", self.root, "tag", "-d", "kit-v0.1"], check=True, capture_output=True)
        self.assertEqual(self.problems("changelog"), [])   # no tags at all (a clone of the public copy): skipped
        subprocess.run(["git", "-C", self.root, "tag", "kit-v0.1"], check=True)
        p = self.problems("changelog")
        self.assertTrue(any("tag kit-v0.1 has no heading" in x for x in p), p)
        self.assertTrue(any("heading kit-v0.2 has no tag" in x for x in p), p)   # an older entry: its tag was forgotten
        self.assertFalse(any("kit-v0.3" in x for x in p), p)   # the newest entry, being written before its tag: allowed
        self.w("KIT-CHANGELOG.md", "# Kit changelog\n## kit-v0.2 — d — t\n## kit-v0.1 — d — t\n")
        subprocess.run(["git", "-C", self.root, "tag", "kit-v0.2"], check=True)
        self.assertEqual(self.problems("changelog"), [])

    def test_export_public(self):
        """scripts/export-public: one new commit, exactly the given identity, the working record left out, nothing pushed;
        an identity carrying this machine's hostname is refused and leaves nothing behind."""
        import socket
        kit = os.path.dirname(KIT_SCRIPTS_DOCS)
        shutil.copytree(KIT_SCRIPTS_DOCS, os.path.join(self.root, "scripts", "docs"))
        self.w("HANDOFF.md", "working record: /home/someone/kit\n")  # sanitize: fixture
        self.w("history/PLAN.md", "old plan\n")
        g = ["git", "-C", self.root, "-c", "user.name=t", "-c", "user.email=t@example.invalid"]
        subprocess.run(["git", "init", "-q", self.root], check=True)
        subprocess.run(g + ["add", "-A"], check=True)
        subprocess.run(g + ["commit", "-q", "-m", "x"], check=True)
        out = self.root + "-public"
        self.addCleanup(shutil.rmtree, out, True)
        exp = os.path.join(kit, "export-public")
        host = socket.gethostname().split(".")[0]
        bad = subprocess.run([sys.executable, exp, out, "--from", self.root, "--name", "A Person",
                              "--email", f"someone@{host}.example.org"], capture_output=True, text=True)
        self.assertEqual(bad.returncode, 2, bad.stdout + bad.stderr)
        self.assertIn("hostname", bad.stderr)
        self.assertFalse(os.path.exists(out))
        inside = subprocess.run([sys.executable, exp, os.path.join(self.root, "pub"), "--from", self.root, "--name", "A Person",
                                 "--email", "a.person@example.org"], capture_output=True, text=True)
        self.assertEqual(inside.returncode, 2)
        ok = subprocess.run([sys.executable, exp, out, "--from", self.root, "--name", "A Person", "--email", "a.person@example.org"],
                            capture_output=True, text=True)
        self.assertEqual(ok.returncode, 0, ok.stdout + ok.stderr)
        log = subprocess.run(["git", "-C", out, "log", "--format=%an <%ae>|%cn <%ce>"], capture_output=True, text=True).stdout
        self.assertEqual(log.strip().splitlines(), ["A Person <a.person@example.org>|A Person <a.person@example.org>"])
        self.assertFalse(os.path.exists(os.path.join(out, "history")))
        self.assertNotIn("/home/", open(os.path.join(out, "HANDOFF.md")).read())
        self.assertEqual(subprocess.run(["git", "-C", out, "remote"], capture_output=True, text=True).stdout, "")



class T28RulesVsCode(Base):
    """Pending item P-3, B1-B6 (user 2026-10-01: "B1-6: yes to all"): where RULES.md and the code disagreed, the code now
    does what the rule says. B1 a referee gets no --input; B2 --input-approved needs the file on the user's exceptions list;
    B4 [PROVED] needs a live hold on both questions; B5 a mutation must name its FAIL line under kit/claims/2; B6 a VERIFIED
    script claim with no mutation earns [NUMERIC]. (B3, limits that cannot be enforced, is in test_ext.py.)"""

    def setUp(self):
        super().setUp()
        os.makedirs(os.path.join(self.root, "problems", "x"), exist_ok=True)
        open(os.path.join(self.root, "problems", "x", "PROBLEM.md"), "w").write("p\n")
        out = os.path.join(self.rd, "output")
        open(os.path.join(out, "p.md"), "w").write("proof\n")
        open(os.path.join(out, "extra.md"), "w").write("extra\n")
        json.dump({"schema": "kit/claims/2", "run": "900-solve", "problem": "x", "claims": [
            {"id": "c1", "tag": "PROVED", "statement": "t", "silent_links": ["none"],
             "premises": [{"kind": "classical", "what": "Lagrange"}], "artifact": {"type": "text", "path": "output/p.md"}}]},
            open(os.path.join(out, "claims.json"), "w"))

    def test_b1_a_referee_gets_no_input(self):
        p = G.tool(self.root, "new-run", "workspace-9", "ref-in", "--role", "referee", "--claim", "900-solve", "c1",
                   "--input", os.path.join(self.rd, "output", "extra.md"))
        self.assertNotEqual(p.returncode, 0, p.stdout)
        self.assertIn("a referee gets no --input", p.stderr)
        p = G.tool(self.root, "new-run", "workspace-9", "ref-ok", "--role", "referee", "--claim", "900-solve", "c1")
        self.assertEqual(p.returncode, 0, p.stderr)

    def test_b2_input_approved_needs_the_users_exception(self):
        f = os.path.join(self.rd, "output", "extra.md")
        p = G.tool(self.root, "new-run", "workspace-9", "solve-a", "--role", "solver", "--problem", "x", "--input-approved", f)
        self.assertNotEqual(p.returncode, 0, p.stdout)
        self.assertIn("not on the user's exceptions list", p.stderr)
        os.makedirs(os.path.join(self.root, "data"), exist_ok=True)
        json.dump([{"path": "workspace-9/runs/900-solve/output/extra.md", "sha256": hashlib.sha256(open(f, "rb").read()).hexdigest(),
                    "ruling": "r"}],
                  open(os.path.join(self.root, "data", "packet-exceptions.json"), "w"))
        p = G.tool(self.root, "new-run", "workspace-9", "solve-b", "--role", "solver", "--problem", "x", "--input-approved", f)
        self.assertEqual(p.returncode, 0, p.stderr)
        open(f, "a").write("changed\n")   # the exception is by hash: changed bytes are not excepted
        p = G.tool(self.root, "new-run", "workspace-9", "solve-c", "--role", "solver", "--problem", "x", "--input-approved", f)
        self.assertNotEqual(p.returncode, 0, p.stdout)

    def lib(self):
        sys.path.insert(0, G.BIN)
        sys.modules.pop("_lib", None)
        import _lib
        return _lib

    def test_b4_proved_needs_both_questions(self):
        L = self.lib()
        cert = {"question": "certify", "verdict": "holds"}
        hyp = {"question": "hypotheses", "verdict": "holds"}
        tag = lambda live: L.earned_tag("PROVED", "n/a", [r["verdict"] for r in live], False, False, True, True,
                                        questions=L.proved_questions(live))
        self.assertEqual(tag([cert])[0], "PENDING")
        self.assertIn("hypotheses", tag([cert])[1])
        self.assertEqual(tag([hyp])[0], "PENDING")
        self.assertEqual(tag([cert, hyp])[0], "PROVED")
        self.assertEqual(tag([cert, dict(hyp, verdict="gap")])[0], "GAP")

    def test_b5_a_mutation_names_its_fail_line(self):
        L = self.lib()
        c = {"id": "c1", "tag": "VERIFIED", "statement": "s", "range": "r", "coverage": "c", "silent_links": ["none"],
             "premises": [{"kind": "software", "what": "Python"}],
             "artifact": {"type": "script", "path": "output/p.md", "cmd": "true",
                          "mutations": [{"name": "m", "cmd": "false"}]}}
        errs = L.validate_claim(c, "kit/claims/2")
        self.assertTrue(any("names no FAIL line" in e for e in errs), errs)
        self.assertFalse(any("names no FAIL line" in e for e in L.validate_claim(c, "kit/claims/1")))
        c["artifact"]["mutations"][0]["expect_stdout_contains"] = "FAIL x"
        self.assertFalse(any("FAIL line" in e for e in L.validate_claim(c, "kit/claims/2")))

    def test_b6_no_mutation_earns_numeric(self):
        L = self.lib()
        e = L.earned_tag("VERIFIED", "pass", ["holds"], True, True, True, True, mutations_missing=True)
        self.assertEqual(e[0], "NUMERIC", e)
        self.assertIn("no mutation", e[1])
        self.assertEqual(L.earned_tag("VERIFIED", "pass", ["holds"], True, True, True, True)[0], "VERIFIED")
        self.assertEqual(L.earned_tag("NUMERIC", "pass", ["holds"], True, True, True, True, mutations_missing=True)[0], "NUMERIC")


class T29PacketListLedgerFirst(Base):
    """Pending item P-4 (user 2026-10-01: "yes"): bin/packet-block and bin/packet-except changed their list before
    writing the ledger line, so a failed append left an unrecorded change. The list now changes only after its line is
    on the ledger; with no ledger the tool refuses and the list is as it was."""

    def lists(self):
        out = {}
        for n in ("packet-rules.json", "packet-exceptions.json"):
            p = os.path.join(self.root, "data", n)
            out[n] = open(p).read() if os.path.exists(p) else None
        return out

    def test_no_ledger_no_change(self):
        f = os.path.join(self.rd, "output", "claims.json")
        os.remove(os.path.join(self.root, "LEDGER.log"))
        before = self.lists()
        for args in (("packet-block", os.path.join(self.root, "problems"), "why"), ("packet-block", "--extract", "C-001", "why"),
                     ("packet-except", f, "a ruling")):
            with self.subTest(args=args):
                p = G.tool(self.root, *args)
                self.assertNotEqual(p.returncode, 0, p.stdout)
                self.assertEqual(self.lists(), before, args)
                self.assertFalse(any(n.endswith(".tmp") for n in os.listdir(os.path.join(self.root, "data")))
                                 if os.path.isdir(os.path.join(self.root, "data")) else False)

    def test_with_ledger_both_change(self):
        p = G.tool(self.root, "packet-block", os.path.join(self.root, "problems"), "why")
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn("problems", self.lists()["packet-rules.json"])
        self.assertIn("PACKET-BLOCK", open(os.path.join(self.root, "LEDGER.log")).read())


class T30IgnoreFile(unittest.TestCase):
    """Pending item P-9, interim (user 2026-10-01): a recursive search typed in a shell walks what the hook protects. The
    accidental walk is closed for ripgrep (which Claude Code's Grep tool runs) by an `.ignore` at an instance's root naming
    the ledger, the locked data and the approval records; `grep -r` does not read it, which the residual records."""

    def test_the_kit_ships_it_and_new_workspace_copies_it(self):
        sys.path.insert(0, G.BIN)
        import importlib.machinery, importlib.util
        loader = importlib.machinery.SourceFileLoader("new_workspace_ign", os.path.join(G.BIN, "new-workspace"))
        spec = importlib.util.spec_from_loader("new_workspace_ign", loader)
        NW = importlib.util.module_from_spec(spec)
        loader.exec_module(NW)
        self.assertIn(".ignore", NW.COPY_FILES)
        lines = open(os.path.join(G.REAL, ".ignore")).read().split()
        for want in ("/LEDGER.log", "/data/locked/", "/.claude/state/approvals/"):
            self.assertIn(want, lines)

    def test_ripgrep_skips_them(self):
        rg = shutil.which("rg")
        if not rg:
            self.skipTest("no ripgrep here")
        root = tempfile.mkdtemp(prefix="ign-")
        try:
            for rel in ("LEDGER.log", "data/locked/key.json", ".claude/state/approvals/a.json", "bin/tool.py"):
                os.makedirs(os.path.dirname(os.path.join(root, rel)) or root, exist_ok=True)
                open(os.path.join(root, rel), "w").write("needle\n")
            shutil.copy(os.path.join(G.REAL, ".ignore"), root)
            out = subprocess.run([rg, "-l", "--hidden", "needle", "."], cwd=root, capture_output=True, text=True,
                                 stdin=subprocess.DEVNULL, timeout=30).stdout.split()   # a path and no stdin: rg reads stdin otherwise
            out = [o[2:] if o.startswith("./") else o for o in out]
            self.assertEqual(sorted(out), ["bin/tool.py"])
        finally:
            shutil.rmtree(root)


class T31LockedOutsideTheTree(Base):
    """Pending item P-9 (user 2026-10-01: "a"): the locked directory moves out of the instance tree, so no search from the
    instance (or from ~/workspace) walks it. kit-env.json's `locked_dir` names it; bin/new-workspace makes it at
    ~/.local/state/crosslemma/<instance>/locked/ and records it; without the field an older instance keeps
    <root>/data/locked. Every reader follows the field: _lib.LOCKED, bin/new-run, bin/verify-data (and the hook,
    test_hook_gate.py T12)."""

    def setUp(self):
        super().setUp()
        self.out = os.path.realpath(tempfile.mkdtemp(prefix="locked-out-"))
        self.locked = os.path.join(self.out, "locked")
        os.makedirs(self.locked)
        open(os.path.join(self.locked, "key.json"), "w").write('{"answer": 42}\n')
        os.makedirs(os.path.join(self.root, "problems", "x"), exist_ok=True)
        open(os.path.join(self.root, "problems", "x", "PROBLEM.md"), "w").write("p\n")

    def tearDown(self):
        shutil.rmtree(self.out, ignore_errors=True)
        super().tearDown()

    def env(self, d):
        json.dump(d, open(os.path.join(self.root, "kit-env.json"), "w"))

    def envmod(self):
        sys.path.insert(0, G.BIN)
        sys.modules.pop("_env", None)
        import _env
        return _env

    def test_the_field(self):
        E = self.envmod()
        self.assertEqual(E.load(self.root).locked_dir, os.path.join(self.root, "data", "locked"))   # no field: as before
        self.env({"locked_dir": self.locked})
        e = E.load(self.root)
        self.assertEqual((e.locked_dir, e.problems), (self.locked, []))
        for bad in (os.path.join(self.root, "data", "locked2"), "~", "/", "~/.ssh/locked"):
            with self.subTest(bad=bad):
                self.env({"locked_dir": bad})
                e = E.load(self.root)
                self.assertTrue(any("locked_dir" in p for p in e.problems), e.problems)
                self.assertEqual(e.locked_dir, os.path.join(self.root, "data", "locked"))
        self.assertEqual(E.default_locked_dir("/w/example-1"),
                         os.path.join(E.home(), ".local", "state", "crosslemma", "example-1", "locked"))

    def test_lib_and_new_run_follow_it(self):
        self.env({"locked_dir": self.locked})
        p = subprocess.run(["/usr/bin/python3", "-c", "import sys; sys.path.insert(0, sys.argv[1]); import _lib; print(_lib.LOCKED)",
                            G.BIN], env=dict(os.environ, KIT_ROOT=self.root), capture_output=True, text=True)
        self.assertEqual(p.stdout.strip(), self.locked, p.stderr)
        k = os.path.join(self.locked, "key.json")
        p = G.tool(self.root, "new-run", "workspace-9", "solve-k", "--role", "solver", "--problem", "x", "--input", k)
        self.assertNotEqual(p.returncode, 0)
        self.assertIn("locked", p.stderr)
        p = G.tool(self.root, "new-run", "workspace-9", "eval-k", "--role", "evaluator", "--input", k)
        self.assertEqual(p.returncode, 0, p.stderr)

    def test_verify_data_follows_it(self):
        self.env({"locked_dir": self.locked})
        p = G.tool(self.root, "verify-data")
        self.assertIn("locked files: 1", p.stdout)
        shutil.copy(os.path.join(self.locked, "key.json"), os.path.join(self.rd, "output", "copy.json"))
        p = G.tool(self.root, "verify-data")
        self.assertIn("LOCKED CONTENT COPIED", p.stdout)
        os.remove(os.path.join(self.rd, "output", "copy.json"))
        os.makedirs(os.path.join(self.root, "data", "locked"), exist_ok=True)       # a key left in the tree after the move
        open(os.path.join(self.root, "data", "locked", "old.json"), "w").write("{}\n")
        p = G.tool(self.root, "verify-data")
        self.assertIn("data/locked/ in the tree still holds", p.stdout)

    def test_new_workspace_makes_and_records_it(self):
        sys.path.insert(0, G.BIN)
        import importlib.machinery, importlib.util
        loader = importlib.machinery.SourceFileLoader("new_workspace_lk", os.path.join(G.BIN, "new-workspace"))
        spec = importlib.util.spec_from_loader("new_workspace_lk", loader)
        NW = importlib.util.module_from_spec(spec)
        loader.exec_module(NW)
        target = os.path.join(self.out, "fresh", "locked")
        d, path = NW.locked_plan({"claude": "claude"}, "/w/x-1", default=target)
        self.assertEqual((d["locked_dir"], path, d["claude"]), (target, target, "claude"))
        d, path = NW.locked_plan({"locked_dir": self.locked}, "/w/x-1", default=target)   # the user's own path wins
        self.assertEqual(path, self.locked)
        self.assertIn("not empty", NW.locked_problem(self.locked))                     # another instance's keys
        self.assertIsNone(NW.locked_problem(target))
        # P-12 (a low finding): the default is keyed by the instance's directory name only, so an empty directory there
        # may be another instance's (same name, another parent) before its keys arrive: it is refused too
        empty = os.path.join(self.out, "empty", "locked")
        os.makedirs(empty)
        self.assertIn("already exists", NW.locked_problem(empty))


class T32SmallFixesP11(unittest.TestCase):
    """Pending item P-11 (user 2026-10-02: "Make the small changes"), found by the docs review: (a) bin/new-workspace
    committed kit-env.json only with --env, though it writes the file always since kit-v0.6.9; (b) its dirty-kit check
    omitted .gitignore and .ignore, which it copies; (f) bin/check-env tested the bwrap on PATH while the sandboxes run
    /usr/bin/bwrap. ((e), Codex's KIT_CPU_HOURS and KIT_MEM_GB, is in test_ext.py.)"""

    def nw(self):
        sys.path.insert(0, G.BIN)
        import importlib.machinery, importlib.util
        loader = importlib.machinery.SourceFileLoader("new_workspace_p11", os.path.join(G.BIN, "new-workspace"))
        spec = importlib.util.spec_from_loader("new_workspace_p11", loader)
        NW = importlib.util.module_from_spec(spec)
        loader.exec_module(NW)
        return NW

    def test_a_kit_env_always_committed(self):
        NW = self.nw()
        for lean, sage, env in ((None, None, False), ("/lib", None, False), (None, "/sage", True)):
            with self.subTest(lean=lean, sage=sage, env=env):
                self.assertIn("kit-env.json", NW.commit_paths(lean, sage))

    def test_b_dirty_check_covers_every_copied_file(self):
        NW = self.nw()
        for p in (".gitignore", ".ignore") + tuple(NW.COPY_DIRS) + tuple(NW.COPY_FILES):
            with self.subTest(p=p):
                self.assertTrue(any(p == d or p.startswith(d.rstrip("/") + "/") for d in NW.KIT_DIRTY_PATHS), p)

    def test_f_check_env_tests_the_sandboxes_bwrap(self):
        if not os.path.exists("/usr/bin/bwrap"):
            self.skipTest("no /usr/bin/bwrap here")
        root, _ = G.make_root()
        self.addCleanup(shutil.rmtree, root, True)
        shutil.copytree(os.path.join(G.REAL, ".claude"), os.path.join(root, ".claude"),
                        ignore=shutil.ignore_patterns("state", "settings.json", "settings.local.json"))
        for d in ("bin", "harness"):
            os.symlink(os.path.join(G.REAL, d), os.path.join(root, d))
        fake = tempfile.mkdtemp(prefix="fakebw-")
        self.addCleanup(shutil.rmtree, fake, True)
        open(os.path.join(fake, "bwrap"), "w").write("#!/bin/sh\nexit 1\n")
        os.chmod(os.path.join(fake, "bwrap"), 0o755)
        p = subprocess.run(["/usr/bin/python3", os.path.join(G.BIN, "check-env")], capture_output=True, text=True,
                           env=dict(os.environ, KIT_ROOT=root, PATH=fake + ":" + os.environ["PATH"]), timeout=120)
        self.assertRegex(p.stdout, r"(?m)^ok\s+bwrap\b.*/usr/bin/bwrap", p.stdout)


class T33P12HostWrites(Base):
    """P-12 C2 (the code audit of 2026-10-02; user 2026-10-02: "let's do the p12 fixes now"): host code wrote into a run
    directory through names a worker can make symlinks: bin/check's logs and check.json (while the worker's own script runs
    in the sandbox), bin/limits-exec's working files, usage.json and time.log, and _ext.py's copied logs and RECORD-EXT.md.
    A write that follows such a link reaches any file the user can write. Now every such write goes through
    _lib.write_in_run (no symlink followed below the run directory; the file renamed over the name)."""

    def lib(self):
        sys.modules.pop("_lib", None)
        sys.path.insert(0, G.BIN)
        import _lib
        return _lib

    def victim(self):
        d = os.path.realpath(tempfile.mkdtemp(prefix="victim-"))
        self.addCleanup(shutil.rmtree, d, True)
        open(os.path.join(d, "f.txt"), "w").write("the user's file\n")
        return d, os.path.join(d, "f.txt")

    def test_write_in_run(self):
        L = self.lib()
        vd, vf = self.victim()
        os.symlink(vf, os.path.join(self.rd, "usage.json"))
        L.write_in_run(self.rd, "usage.json", "{}\n")
        self.assertEqual(open(vf).read(), "the user's file\n")
        self.assertFalse(os.path.islink(os.path.join(self.rd, "usage.json")))
        self.assertEqual(open(os.path.join(self.rd, "usage.json")).read(), "{}\n")
        os.symlink(vd, os.path.join(self.rd, "check"))
        with self.assertRaises(OSError):
            L.write_in_run(self.rd, "check/c1.stdout", "x")
        os.symlink(vf, os.path.join(self.rd, "licence.log"))
        with self.assertRaises(OSError):
            L.write_in_run(self.rd, "licence.log", "x", append=True)
        self.assertEqual(sorted(os.listdir(vd)), ["f.txt"])
        self.assertEqual(open(vf).read(), "the user's file\n")
        L.write_in_run(self.rd, "new/sub/x.txt", "made")
        self.assertEqual(open(os.path.join(self.rd, "new", "sub", "x.txt")).read(), "made")

    def test_check_does_not_write_through_a_workers_link(self):
        """The worker's script runs in the sandbox during bin/check and plants the links there."""
        if not os.path.exists("/usr/bin/bwrap"):
            self.skipTest("no bwrap")
        vd, vf = self.victim()
        out = os.path.join(self.rd, "output")
        open(os.path.join(out, "s.sh"), "w").write(
            f"rm -rf check; ln -s {vd} check; ln -s {vf} check.json.tmp; ln -s {vf} check.json; echo ok\n")
        open(os.path.join(out, "result.md"), "w").write("r\n")
        json.dump({"schema": "kit/claims/2", "run": "900-solve", "problem": "x", "claims": [
            {"id": "c1", "tag": "NUMERIC", "statement": "s", "range": "r", "coverage": "c", "silent_links": ["none"],
             "premises": [{"kind": "software", "what": "bash"}],
             "artifact": {"type": "script", "path": "output/s.sh", "cmd": "bash output/s.sh"}}]},
            open(os.path.join(out, "claims.json"), "w"))
        G.tool(self.root, "check", "900-solve")
        self.assertEqual(sorted(os.listdir(vd)), ["f.txt"])
        self.assertEqual(open(vf).read(), "the user's file\n")


class T34P12Bindings(Base):
    """P-12 C3 (the code audit of 2026-10-02; user 2026-10-02: "let's do the p12 fixes now"): an earned tag rested on files
    a worker can write. Any run's output/referee.json counted as a referee's, a solver's own included; the question came
    from RUN/.ref-question and the bytes a referee saw from its own input/ (a missing input/claim.json skipped the
    staleness check); and the user's cross-family ruling was read from the solver's run directory. Now a referee run is
    one bin/new-run bound in data/referee-bindings/<run>.json (question, claim, the bytes it was given), and a ruling is
    read from data/cross-family-rulings.json; the workers write neither."""

    def lib(self):
        sys.modules.pop("_lib", None)
        sys.path.insert(0, G.BIN)
        import _lib
        return _lib

    def recs(self, L):
        return L.referee_files().get(("900-solve", "c1"), [])

    def test_a_solvers_own_referee_json_does_not_count(self):
        json.dump({"schema": "kit/referee/1", "run": "900-solve", "claim": "c1", "verdict": "holds", "pointer": "n/a",
                   "note": ""}, open(os.path.join(self.rd, "output", "referee.json"), "w"))
        L = self.lib()
        own = [r for r in self.recs(L) if r["referee_run"] == "900-solve"]
        self.assertEqual(len(own), 1)
        self.assertIn("no binding", own[0].get("error", ""))
        live, _ = L.live_referees(self.recs(L), None)
        self.assertEqual([r["referee_run"] for r in live], ["901-ref"])

    def test_the_question_is_the_bindings(self):
        ref = os.path.join(self.root, "workspace-9", "runs", "901-ref")
        b = os.path.join(self.root, "data", "referee-bindings", "901-ref.json")
        doc = json.load(open(b)); doc["question"] = "hypotheses"; json.dump(doc, open(b, "w"))
        open(os.path.join(ref, ".ref-question"), "w").write("certify\n")   # the worker's word
        self.assertEqual([r["question"] for r in self.recs(self.lib())], ["hypotheses"])

    def test_staleness_from_the_bound_bytes(self):
        """The referee was given bytes A; the claim's artifact is now B. Rewriting its own copy to B, or deleting its
        input/claim.json, no longer makes the old verdict count."""
        ref = os.path.join(self.root, "workspace-9", "runs", "901-ref")
        b = os.path.join(self.root, "data", "referee-bindings", "901-ref.json")
        doc = json.load(open(b)); doc["artifact_sha256"] = "a" * 64; json.dump(doc, open(b, "w"))
        os.remove(os.path.join(ref, "input", "claim.json"))
        L = self.lib()
        live, stale = L.live_referees(self.recs(L), {"artifact_sha256": "b" * 64})
        self.assertEqual((len(live), len(stale)), (0, 1))

    def test_an_unreadable_referee_json_is_visible(self):
        open(os.path.join(self.root, "workspace-9", "runs", "901-ref", "output", "referee.json"), "w").write("{not json")
        r = self.recs(self.lib())
        self.assertEqual(len(r), 1)
        self.assertIn("unreadable", r[0]["error"])

    def test_new_run_writes_the_binding(self):
        os.makedirs(os.path.join(self.root, "problems", "x"))
        open(os.path.join(self.root, "problems", "x", "PROBLEM.md"), "w").write("p\n")
        out = os.path.join(self.rd, "output")
        open(os.path.join(out, "p.md"), "w").write("proof\n")
        json.dump({"schema": "kit/claims/2", "run": "900-solve", "problem": "x", "claims": [
            {"id": "c1", "tag": "PROVED", "statement": "t", "silent_links": ["none"],
             "premises": [{"kind": "classical", "what": "Lagrange"}], "artifact": {"type": "text", "path": "output/p.md"}}]},
            open(os.path.join(out, "claims.json"), "w"))
        p = G.tool(self.root, "new-run", "workspace-9", "hyp", "--role", "referee", "--claim", "900-solve", "c1",
                   "--question", "hypotheses")
        self.assertEqual(p.returncode, 0, p.stderr)
        b = json.load(open(os.path.join(self.root, "data", "referee-bindings", "902-hyp.json")))
        self.assertEqual((b["schema"], b["referee_run"], b["question"], b["source_run"], b["claim"], b["artifact_sha256"]),
                         ("kit/referee-binding/1", "902-hyp", "hypotheses", "900-solve", "c1",
                          hashlib.sha256(b"proof\n").hexdigest()))
        self.assertFalse(os.path.exists(os.path.join(self.root, "workspace-9", "runs", "902-hyp", ".ref-question")))

    def test_a_ruling_in_the_run_directory_is_not_read(self):
        L = self.lib()
        os.makedirs(os.path.join(self.root, "workspace-9", "runs", "295-ruled", "output"))
        open(os.path.join(self.root, "workspace-9", "runs", "295-ruled", ".cross-family-referee"), "w").write("Anthropic x\n")
        rd = os.path.join(self.root, "workspace-9", "runs", "295-ruled")
        req, holds, line = L.cross_family_need(rd, {"schema": "kit/claims/2"}, {"tag": "PROVED"}, [])
        self.assertIn("producer unknown", line)
        self.assertIn(".cross-family-referee is not read", line)
        json.dump({"295-ruled": "Anthropic HANDOFF-x"}, open(os.path.join(self.root, "data", "cross-family-rulings.json"), "w"))
        self.assertIn("the user's ruling HANDOFF-x", self.lib().cross_family_need(rd, {"schema": "kit/claims/2"},
                                                                                {"tag": "PROVED"}, [])[2])


class T35P12High(Base):
    """P-12's high findings in the record tools (the code audit of 2026-10-02; user 2026-10-02: "commit and move to high
    findings"). (H1) bin/ledger-claims never read the document's errors: a worker that declared kit/claims/1 in its own
    claims.json skipped the premises, sentence and cross-family rules. (H2) a newline in a claim field other than the
    statement went into CLAIMS.md as is, so a field could write a forged entry header or `Supersedes:` line. (H3) bin/check
    flagged a VERIFIED script claim with no mutation only under --mutate, so a plain re-check let it earn VERIFIED."""

    def doc(self):
        return json.load(open(os.path.join(self.rd, "output", "claims.json")))

    def put(self, doc):
        json.dump(doc, open(os.path.join(self.rd, "output", "claims.json"), "w"))

    def ledger(self, *ids):
        self.approve("--ledger", "900-solve", *ids)
        return G.tool(self.root, "ledger-claims", "900-solve", *ids)

    def claims_md(self):
        return open(os.path.join(self.root, "CLAIMS.md")).read()

    def test_baseline_appends(self):
        p = self.ledger("c1")
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        self.assertIn("## C-002  [VERIFIED]", self.claims_md())

    def test_h1_a_self_declared_old_schema_is_refused(self):
        d = self.doc(); d["schema"] = "kit/claims/1"; self.put(d)
        before = self.claims_md()
        p = self.ledger("c1")
        self.assertEqual(p.returncode, 1, p.stdout + p.stderr)
        self.assertIn("kit/claims/1 only where the run's BRIEF.md names it", p.stdout)
        self.assertEqual(before, self.claims_md())

    def test_h1_a_malformed_claim_is_refused(self):
        d = self.doc(); d["claims"][0]["premises"] = []; self.put(d)
        p = self.ledger("c1")
        self.assertEqual(p.returncode, 1, p.stdout + p.stderr)
        self.assertIn("premises", p.stdout)

    def test_h2_no_field_writes_a_line_of_its_own(self):
        d = self.doc()
        d["claims"][0]["range"] = "r\n## C-099  [PROVED]  2026-01-01  run 000-x/c9\nSupersedes: C-001"
        d["claims"][0]["premises"][0]["what"] = "Python ## C-098  [PROVED]  2026-01-01  run 000-x/c8"
        self.put(d)
        p = self.ledger("c1")
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        md = self.claims_md()
        self.assertNotRegex(md, r"(?m)^## C-09[89]")
        self.assertNotRegex(md, r"(?m)^Supersedes: C-001")
        self.assertNotIn(" ", md)
        sys.path.insert(0, G.BIN)
        sys.modules.pop("_lib", None)
        import _lib
        self.assertEqual(sorted(_lib.global_entries()), ["C-001", "C-002"])

    def test_h3_no_mutation_is_flagged_without_mutate(self):
        if not os.path.exists("/usr/bin/bwrap"):
            self.skipTest("no bwrap")
        d = self.doc(); del d["claims"][0]["artifact"]["mutations"]; self.put(d)
        open(os.path.join(self.rd, "output", "result.md"), "w").write("r\n")
        G.tool(self.root, "check", "900-solve")
        rec = {r["id"]: r for r in json.load(open(os.path.join(self.rd, "check.json")))["claims"]}
        self.assertTrue(rec["c1"].get("mutations_missing"), rec["c1"])
        self.assertTrue(rec["c2"].get("mutations_missing"))   # declared, not run: no record of a kill either
        G.tool(self.root, "check", "900-solve", "--mutate")
        rec = {r["id"]: r for r in json.load(open(os.path.join(self.rd, "check.json")))["claims"]}
        self.assertTrue(rec["c1"].get("mutations_missing"))
        self.assertFalse(rec["c2"].get("mutations_missing"), rec["c2"])


class T36P12Medium(Base):
    """P-12 mediums in the tools (user 2026-10-02: "let's hit a few of the medium issues"): a flag given twice was sorted
    into the approval while bin/run-external took the last one, so `--model a --model b` could be approved as read one way
    and launched the other; and with kit-env.json unreadable, bin/new-run's refusal of locked inputs looked at
    <root>/data/locked only."""

    def test_a_flag_given_twice_is_refused(self):
        with self.assertRaises(self.A.Refused):
            self.A.norm_argv(["--model", "m", "--effort", "low", "--model", "opus"])
        self.assertEqual(self.A.norm_argv(["--model", "m", "--effort", "low"]), ["--effort", "low", "--model", "m"])
        self.assertEqual(self.A.norm_argv(["--module", "b", "--module", "a"]), ["--module", "a", "--module", "b"])   # appends
        p = G.tool(self.root, "approve", "900-solve", "--", "--model", "m", "--model", "opus")
        self.assertNotEqual(p.returncode, 0)
        self.assertFalse(os.path.exists(os.path.join(self.root, ".claude", "state", "approvals", "launch-900-solve.json")))

    def test_new_run_guards_every_locked_place(self):
        open(os.path.join(self.root, "kit-env.json"), "w").write("{")
        sys.path.insert(0, G.BIN)
        import _env
        d = _env.default_locked_dir(self.root)
        self.addCleanup(shutil.rmtree, os.path.dirname(d), True)
        os.makedirs(d)
        open(os.path.join(d, "key.json"), "w").write("{}\n")
        os.makedirs(os.path.join(self.root, "problems", "x"))
        open(os.path.join(self.root, "problems", "x", "PROBLEM.md"), "w").write("p\n")
        p = G.tool(self.root, "new-run", "workspace-9", "s", "--role", "solver", "--problem", "x",
                   "--input", os.path.join(d, "key.json"))
        self.assertNotEqual(p.returncode, 0, p.stdout)
        self.assertIn("locked", p.stderr)


class T37P12MediumRest(Base):
    """The rest of P-12's mediums (user 2026-10-02: "let's do the rest of the mediums"). (M1) the approval was used, then
    the launch set up (a gateway, Codex's catalog: seconds to minutes) before the worker started, and nothing looked at the
    bytes again; now the launch re-reads them against the used approval just before the worker starts. (M3) a verdict was
    tied to the artifact's bytes only, so a claim's statement could change under a holding referee; and a PROVED claim
    missing from check.json showed as earned. (M4) CLAIMS.md appends took no lock. (M5) bin/verify-data hashed every run
    file on every close-run, though a copy of a locked file has its size."""

    def test_m1_the_bytes_are_read_again_before_the_worker_starts(self):
        self.approve("900-solve", "--", *G.F)
        dg = self.A.check("launch", "900-solve", self.A.launch_manifest(self.rd), argv=G.F, consume=True)
        self.A.verify_launch(self.rd, dg)                       # unchanged: passes
        open(os.path.join(self.rd, "BRIEF.md"), "a").write("one more line\n")
        with self.assertRaises(self.A.Refused) as cm:
            self.A.verify_launch(self.rd, dg)
        self.assertIn("changed: workspace-9/runs/900-solve/BRIEF.md", str(cm.exception))
        with self.assertRaises(self.A.Refused):
            self.A.verify_launch(self.rd, "0" * 64)            # no used approval with that digest

    def test_m1_queued(self):
        self.approve("900-solve", "--", *G.F)
        nonce = self.A.queue_start([self.rd], argv=G.F)
        dg = self.A.queue_take(nonce, self.rd, argv=G.F)
        self.A.verify_launch(self.rd, dg)
        open(os.path.join(self.rd, "input", "a.txt"), "w").write("swapped\n")
        with self.assertRaises(self.A.Refused):
            self.A.verify_launch(self.rd, dg)

    def test_m1_wired_before_each_route_starts(self):
        src = open(os.path.join(G.BIN, "run-external")).read()
        v = src.index('_approval.py" verify launch "$RD" "$APPROVAL"')
        self.assertLess(v, src.index('"$ROOT/bin/limits-exec" "$RD" -- \\\n    timeout'))
        self.assertIn('--approval "$APPROVAL"', src)
        self.assertIn("A.verify_launch(rd, a.approval", open(os.path.join(G.BIN, "_ext.py")).read())

    def lib(self):
        sys.modules.pop("_lib", None)
        sys.path.insert(0, G.BIN)
        import _lib
        return _lib

    def test_m3_a_changed_claim_makes_the_verdict_stale(self):
        L = self.lib()
        b = os.path.join(self.root, "data", "referee-bindings", "901-ref.json")
        doc = json.load(open(os.path.join(self.rd, "output", "claims.json")))
        c1 = doc["claims"][0]
        bd = json.load(open(b)); bd["claim_sha256"] = L.claim_digest(c1); json.dump(bd, open(b, "w"))
        chk = {"artifact_sha256": bd["artifact_sha256"]}
        recs = L.referee_files()[("900-solve", "c1")]
        self.assertEqual(len(L.live_referees(recs, chk, c1)[0]), 1)
        self.assertEqual(len(L.live_referees(recs, chk, dict(c1, statement="a wider statement"))[1]), 1)

    def test_m3_new_run_binds_the_claim(self):
        os.makedirs(os.path.join(self.root, "problems", "x"))
        open(os.path.join(self.root, "problems", "x", "PROBLEM.md"), "w").write("p\n")
        L = self.lib()
        c1 = json.load(open(os.path.join(self.rd, "output", "claims.json")))["claims"][0]
        p = G.tool(self.root, "new-run", "workspace-9", "sent", "--role", "referee", "--claim", "900-solve", "c1",
                   "--question", "sentence")
        self.assertEqual(p.returncode, 0, p.stderr)
        b = json.load(open(os.path.join(self.root, "data", "referee-bindings", "902-sent.json")))
        self.assertEqual(b["claim_sha256"], L.claim_digest(c1))

    def test_m3_an_unchecked_proved_claim_is_not_earned(self):
        L = self.lib()
        q = frozenset({"certify", "hypotheses"})
        self.assertEqual(L.earned_tag("PROVED", "n/a", ["holds", "holds"], questions=q)[0], "PROVED")
        self.assertEqual(L.earned_tag("PROVED", "unchecked", ["holds", "holds"], questions=q)[0], "PENDING")

    def test_m4_appends_wait_for_the_lock(self):
        import fcntl
        self.approve("--ledger", "900-solve", "c1")
        L = self.lib()
        os.makedirs(os.path.dirname(L.CLAIMS_LOCK), exist_ok=True)
        lk = open(L.CLAIMS_LOCK, "a")
        fcntl.flock(lk, fcntl.LOCK_EX)
        before = open(os.path.join(self.root, "CLAIMS.md")).read()
        proc = subprocess.Popen(["/usr/bin/python3", os.path.join(G.BIN, "ledger-claims"), "900-solve", "c1"],
                                env=dict(os.environ, KIT_ROOT=self.root), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        time.sleep(1.5)
        self.assertIsNone(proc.poll(), "the append did not wait for the lock")
        self.assertEqual(open(os.path.join(self.root, "CLAIMS.md")).read(), before)
        fcntl.flock(lk, fcntl.LOCK_UN); lk.close()
        out, err = proc.communicate(timeout=30)
        self.assertEqual(proc.returncode, 0, out + err)
        self.assertIn("## C-002  [VERIFIED]", open(os.path.join(self.root, "CLAIMS.md")).read())

    def test_m5_verify_data_hashes_only_files_a_copy_could_be(self):
        locked = os.path.join(self.root, "data", "locked")
        os.makedirs(locked)
        open(os.path.join(locked, "key.json"), "w").write('{"answer": 42}\n')
        h = hashlib.sha256(b'{"answer": 42}\n').hexdigest()
        open(os.path.join(locked, "SHA256SUMS"), "w").write(f"{h}  ./key.json\n")
        for i in range(20):
            open(os.path.join(self.rd, "scratch", f"f{i}.txt"), "w").write("x" * (100 + i))
        open(os.path.join(self.rd, "scratch", "copy.json"), "w").write('{"answer": 42}\n')
        code = ("import sys, runpy; sys.path.insert(0, %r); import _lib as L\n"
                "n = [0]; real = L.sha256\n"
                "def count(p):\n    n[0] += 1\n    return real(p)\n"
                "L.sha256 = count; sys.argv = ['verify-data']\n"
                "try:\n    runpy.run_path(%r, run_name='__main__')\nexcept SystemExit:\n    pass\n"
                "print('HASHED', n[0])\n") % (G.BIN, os.path.join(G.BIN, "verify-data"))
        p = subprocess.run(["/usr/bin/python3", "-c", code], env=dict(os.environ, KIT_ROOT=self.root), capture_output=True, text=True)
        self.assertIn("LOCKED CONTENT COPIED: workspace-9/runs/900-solve/scratch/copy.json", p.stdout)
        n = int(p.stdout.split("HASHED")[1].split()[0])
        self.assertLess(n, 10, p.stdout)


def _lean_ready():
    elan = os.path.expanduser("~/.elan")
    return (os.path.isdir(os.path.join(elan, "toolchains", "leanprover--lean4---v4.32.0")) and shutil.which("lake")
            and os.path.exists("/usr/bin/bwrap"))


@unittest.skipUnless(_lean_ready(), "no Lean 4.32 toolchain (elan) or no bwrap here")
class T38P12LeanAudit(Base):
    """P-12 (a medium of the code audit, found graver when shown live on 2026-10-02): bin/check appended `#print axioms`
    to the artifact's own file, so the artifact's macros applied to it. A `macro_rules` for `#print axioms` made a theorem
    proved by `sorry` print "does not depend on any axioms", and Lean exited 0. Now the artifact is compiled, its
    compiled file replayed through the kernel (leanchecker) in a sandbox where no artifact code runs, and the axioms are
    collected there by the kit's own program (harness/lean/KitAudit.lean), walking the kernel's constants."""

    LIE = ("theorem main_thm : 2 + 2 = 5 := sorry\n\nmacro_rules\n"
           "  | `(#print axioms $id) => `(#eval IO.println s!\"'{$(Lean.quote id.getId.toString)}' does not depend on any axioms\")\n")

    def setUp(self):
        super().setUp()
        lean = os.path.join(self.root, "lean")
        os.makedirs(lean)
        open(os.path.join(lean, "lean-toolchain"), "w").write("leanprover/lean4:v4.32.0\n")
        open(os.path.join(lean, "lakefile.toml"), "w").write('name = "kitlib"\n\n[[lean_lib]]\nname = "Kitlib"\n')
        open(os.path.join(lean, "Kitlib.lean"), "w").write("def kitlibMarker := 1\n")
        open(os.path.join(self.root, ".kit-lean"), "w").write("~/.elan\n")
        r = subprocess.run(["lake", "env", "true"], cwd=lean, capture_output=True, text=True, timeout=300)
        self.assertEqual(r.returncode, 0, r.stderr)
        open(os.path.join(self.rd, "output", "result.md"), "w").write("r\n")
        # the checker's sandbox is the hook of the tree its tools are in: copies, so this tree's module is mounted
        shutil.copytree(G.BIN, os.path.join(self.root, "bin"), ignore=shutil.ignore_patterns("__pycache__"))
        shutil.copytree(os.path.join(G.REAL, "harness"), os.path.join(self.root, "harness"))
        for d in ("hooks", "sandbox"):
            shutil.copytree(os.path.join(G.REAL, ".claude", d), os.path.join(self.root, ".claude", d))

    def check(self, src, decls):
        open(os.path.join(self.rd, "output", "T.lean"), "w").write(src)
        json.dump({"schema": "kit/claims/2", "run": "900-solve", "problem": "x", "claims": [
            {"id": "c1", "tag": "PROVED", "statement": "s", "silent_links": ["none"],
             "premises": [{"kind": "kernel", "what": "Lean"}],
             "artifact": {"type": "lean", "path": "output/T.lean", "decls": decls}}]},
            open(os.path.join(self.rd, "output", "claims.json"), "w"))
        p = subprocess.run(["/usr/bin/python3", os.path.join(self.root, "bin", "check"), "900-solve", "--timeout", "600"],
                           env=dict(os.environ, KIT_ROOT=self.root), capture_output=True, text=True, stdin=subprocess.DEVNULL)
        return p, json.load(open(os.path.join(self.rd, "check.json")))["claims"][0]

    def test_a_macro_cannot_hide_sorry(self):
        p, rec = self.check(self.LIE, ["main_thm"])
        self.assertEqual(rec["check"], "fail", p.stdout + p.stderr)
        self.assertIn("main_thm depends on sorryAx", " ".join(rec["reasons"]))
        self.assertEqual(rec["axioms"], {"main_thm": ["sorryAx"]})

    def test_clean_and_classical_pass(self):
        p, rec = self.check("theorem a : 2 + 2 = 4 := rfl\ntheorem b (p : Prop) : p \u2228 \u00acp := Classical.em p\n", ["a", "b"])
        self.assertEqual(rec["check"], "n/a" if rec["check"] == "n/a" else "pass", p.stdout + p.stderr)
        self.assertEqual(rec["axioms"]["a"], [])
        self.assertEqual(sorted(rec["axioms"]["b"]), ["Classical.choice", "Quot.sound", "propext"])
        self.assertEqual(rec["signatures"]["a"], "a : 2 + 2 = 4")

    def test_an_unknown_declaration_fails(self):
        p, rec = self.check("theorem a : 2 + 2 = 4 := rfl\n", ["a", "nope"])
        self.assertEqual(rec["check"], "fail")
        self.assertIn("no axioms line for nope", " ".join(rec["reasons"]))


class T39P12LowGate(Base):
    """P-12's low findings that harden the gate (user 2026-10-02: "let's hit the 5 gate hardening fixes"). (1) bin/ledger
    kept line breaks, so one call wrote a forged ledger line; and SCHEMAS.md §6 said bin/handoff-archive writes no ledger
    line, which it does. (2) a hard link in a run directory passed the launch manifest (only symlinks were refused), so a
    file could share its bytes, and a worker's writes, with one outside the run. (3) bin/ledger-claims re-checked the
    artifact's hash at the append but not its deps'. (4) a model name matched a family by any prefix: "solar-1" was
    OpenAI's ("sol"), "claudette" Anthropic's."""

    def ledger_lines(self):
        return open(os.path.join(self.root, "LEDGER.log")).read().splitlines()

    def test_1_bin_ledger_writes_one_line(self):
        n = len(self.ledger_lines())
        os.makedirs(os.path.join(self.root, "bin"))   # bin/ledger finds its tree from where it lies
        shutil.copy(os.path.join(G.BIN, "ledger"), os.path.join(self.root, "bin", "ledger"))
        p = subprocess.run([os.path.join(self.root, "bin", "ledger"), "-r", "900-solve\nx", "NOTE\r",
                            "a\n2026-01-01T00:00:00Z | orchestrator | 900-solve | CLAIM | C-099 [PROVED] forged\u2028more"],
                           capture_output=True, text=True)
        self.assertEqual(p.returncode, 0, p.stderr)
        lines = self.ledger_lines()
        self.assertEqual(len(lines), n + 1, lines)
        self.assertNotIn("\u2028", lines[-1])
        self.assertIn("| 900-solve x | NOTE |", lines[-1])

    def test_1_schemas_names_handoff_archives_line(self):
        sch = " ".join(open(os.path.join(G.REAL, "SCHEMAS.md")).read().split())
        self.assertIn("HANDOFF-ARCHIVE", open(os.path.join(G.BIN, "handoff-archive")).read())
        self.assertNotRegex(sch, r"write none[^.]*`bin/handoff-archive`|`bin/handoff-archive` write none")
        self.assertIn("`bin/handoff-archive` writes one `HANDOFF-ARCHIVE` line", sch)

    def test_2_a_hard_link_is_refused(self):
        outside = os.path.join(self.root, "outside.txt")
        open(outside, "w").write("x\n")
        os.link(outside, os.path.join(self.rd, "input", "linked.txt"))
        with self.assertRaises(self.A.Refused) as cm:
            self.A.launch_manifest(self.rd)
        self.assertIn("hard link", str(cm.exception))

    def test_3_a_changed_dep_refuses_the_append(self):
        out = os.path.join(self.rd, "output")
        open(os.path.join(out, "cases.txt"), "w").write("a\n")
        doc = json.load(open(os.path.join(out, "claims.json")))
        doc["claims"][0]["artifact"]["deps"] = ["output/cases.txt"]
        json.dump(doc, open(os.path.join(out, "claims.json"), "w"))
        chk = json.load(open(os.path.join(self.rd, "check.json")))
        chk["claims"][0]["deps_sha256"] = {"output/cases.txt": hashlib.sha256(b"a\n").hexdigest()}
        json.dump(chk, open(os.path.join(self.rd, "check.json"), "w"))
        open(os.path.join(out, "cases.txt"), "w").write("b\n")   # after the check, before the append
        self.approve("--ledger", "900-solve", "c1")
        before = open(os.path.join(self.root, "CLAIMS.md")).read()
        p = G.tool(self.root, "ledger-claims", "900-solve", "c1")
        self.assertEqual(p.returncode, 1, p.stdout + p.stderr)
        self.assertIn("deps file output/cases.txt changed since check.json", p.stdout)
        self.assertEqual(before, open(os.path.join(self.root, "CLAIMS.md")).read())

    def test_4_a_family_word_is_a_whole_token(self):
        sys.path.insert(0, G.BIN)
        import _env
        for m, fam in (("opus", "Anthropic"), ("claude-opus-5-5", "Anthropic"), ("anthropic/claude-fable-5-1", "Anthropic"),
                       ("gpt-5.6-sol", "OpenAI"), ("gpt5", "OpenAI"), ("gpt4o", "OpenAI"), ("openai/gpt-6-astra", "OpenAI"),
                       ("opus4", "Anthropic"), ("solar-1", None), ("claudette", None), ("codexterity", None), ("gptx", None)):
            with self.subTest(m=m):
                self.assertEqual(_env.model_family(m), fam)


class T40P12LowLauncher(Base):
    """P-12's low findings in the launcher and the run tools (user 2026-10-02: "do launcher robustness items"). (9) a
    queue that failed partway through using its approvals said nothing of the ones already spent. (10) a bin/new-run that
    died after making the run directory left it half built. (12) the networked worker's settings lacked the
    deniedMcpServers list the project settings carry."""

    def test_9_a_queue_names_what_it_spent(self):
        rd2 = os.path.join(self.root, "workspace-9", "runs", "902-two")
        os.makedirs(rd2)
        open(os.path.join(rd2, "BRIEF.md"), "w").write("two\n")
        self.approve("900-solve", "--", *G.F)
        self.approve("902-two", "--", *G.F)
        real = self.A.check

        def flaky(kind, key, *a, **k):
            if k.get("consume") and key == "902-two":
                raise self.A.Refused("already used (approvals are single-use)")
            return real(kind, key, *a, **k)
        self.A.check = flaky
        try:
            with self.assertRaises(self.A.Refused) as cm:
                self.A.queue_start([self.rd, rd2], argv=G.F)
        finally:
            self.A.check = real
        self.assertIn("spent, nothing launched: 900-solve", str(cm.exception))

    def test_10_a_failed_new_run_leaves_nothing(self):
        os.makedirs(os.path.join(self.root, "problems", "x"))
        open(os.path.join(self.root, "problems", "x", "PROBLEM.md"), "w").write("p\n")
        for d in ("a", "b"):
            os.makedirs(os.path.join(self.root, "in", d))
            open(os.path.join(self.root, "in", d, "x.txt"), "w").write(d + "\n")
        runs = os.path.join(self.root, "workspace-9", "runs")
        before = sorted(os.listdir(runs))
        p = G.tool(self.root, "new-run", "workspace-9", "s", "--role", "solver", "--problem", "x",
                   "--input", os.path.join(self.root, "in", "a", "x.txt"), "--input", os.path.join(self.root, "in", "b", "x.txt"))
        self.assertNotEqual(p.returncode, 0)
        self.assertIn("duplicate input basename", p.stderr)
        self.assertEqual(sorted(os.listdir(runs)), before)

    def test_12_the_networked_worker_denies_mcp_servers(self):
        t = lambda n: json.load(open(os.path.join(G.REAL, ".claude", n)))
        self.assertEqual(t("worker-net.settings.template.json").get("deniedMcpServers"),
                         t("settings.template.json")["deniedMcpServers"])


class T41P12Housekeeping(Base):
    """P-12's housekeeping (user 2026-10-02: "do housekeeping items"): bin/merge, close-run and ledger-claims re-read every
    run's transcripts once per claim and per referee (run_family, model_flag); a transcript is now read once per process
    while its size and modification time stay the same."""

    def test_a_transcript_is_read_once_while_unchanged(self):
        sys.modules.pop("_lib", None)
        sys.path.insert(0, G.BIN)
        import _lib as L
        log = os.path.join(self.rd, "launch.log")
        open(log, "w").write(json.dumps({"type": "assistant", "message": {"model": "claude-opus-5-5"}}) + "\n")
        self.assertEqual(L.models_seen(self.rd)[0], {"claude-opus-5-5": 1})
        os.chmod(log, 0)                                   # unreadable now; same size and mtime
        try:
            self.assertEqual(L.models_seen(self.rd)[0], {"claude-opus-5-5": 1})
        finally:
            os.chmod(log, 0o644)
        open(log, "a").write(json.dumps({"type": "assistant", "message": {"model": "claude-opus-4-8"}}) + "\n")
        self.assertEqual(L.models_seen(self.rd)[0], {"claude-opus-5-5": 1, "claude-opus-4-8": 1})   # changed: read again
        L.models_seen(self.rd)[0]["x"] = 9                 # a caller's change does not reach the cache
        self.assertNotIn("x", L.models_seen(self.rd)[0])

    def test_one_approvals_path_in_the_hook(self):
        src = open(os.path.join(G.REAL, ".claude", "hooks", "sandbox.py")).read()
        self.assertEqual(src.count('os.path.join(ROOT, ".claude", "state", "approvals")'), 1)

    def test_no_stale_queue_comment(self):
        src = open(os.path.join(G.BIN, "_approval.py")).read()
        self.assertNotIn("bin/run-external passes\n# that sum", src)
        self.assertNotIn("QUEUE_TTL", src)


class T42P11Settings(unittest.TestCase):
    """P-11 (d) and (g) (user 2026-10-02: "let's do 4, 5, 6, 7"). (d) the settings carry a second PreToolUse command that
    loads the hook and exits 2 when it cannot, so a hook broken by an edit refuses calls instead of making no decision;
    the hook's own command is unchanged (the user-level guard matches it exactly). (g) bin/run-external's preflight
    checked only that the settings named the hook somewhere; now the hook must be registered on PreToolUse for every
    tool (and on PostToolUse)."""

    def filled(self, root, name="settings.template.json"):
        t = open(os.path.join(G.REAL, ".claude", name)).read()
        return json.loads(t.replace("@ROOT@", root).replace("@HOME@", os.path.expanduser("~")))

    def test_d_the_load_check_blocks_a_broken_hook(self):
        root = os.path.realpath(tempfile.mkdtemp(prefix="loadchk-"))
        self.addCleanup(shutil.rmtree, root, True)
        os.makedirs(os.path.join(root, ".claude", "hooks"))
        for name in ("settings.template.json", "worker-net.settings.template.json"):
            pre = [h["command"] for e in self.filled(root, name)["hooks"]["PreToolUse"] for h in e["hooks"]]
            with self.subTest(name=name):
                self.assertIn(f"/usr/bin/python3 {root}/.claude/hooks/sandbox.py", pre)   # unchanged, for the guard
                chk = [c for c in pre if "|| " in c]
                self.assertEqual(len(chk), 1, pre)
                hook = os.path.join(root, ".claude", "hooks", "sandbox.py")
                open(hook, "w").write("import os\nX = 1\n")
                self.assertEqual(subprocess.run(["sh", "-c", chk[0]], capture_output=True, stdin=subprocess.DEVNULL).returncode, 0)
                open(hook, "w").write("def broken(:\n")
                r = subprocess.run(["sh", "-c", chk[0]], capture_output=True, text=True, stdin=subprocess.DEVNULL)
                self.assertEqual(r.returncode, 2)
                self.assertIn("refused", r.stderr)

    def test_p16_the_networked_worker_has_the_bash_timeouts(self):
        """P-16 (found 2026-10-03 in the review for ud): a networked Claude worker loads the worker-net settings (and a local
        file), not the project settings, so it lacked the Bash timeouts they set, and with them the hour per call the briefs
        promise (kit-v0.6.30)."""
        proj, net = self.filled("/w/inst"), self.filled("/w/inst", "worker-net.settings.template.json")
        for k in ("BASH_DEFAULT_TIMEOUT_MS", "BASH_MAX_TIMEOUT_MS"):
            with self.subTest(k=k):
                self.assertEqual((net.get("env") or {}).get(k), proj["env"][k])
        self.assertEqual(proj["env"]["BASH_MAX_TIMEOUT_MS"], "3600000")   # the hour the briefs say

    def test_g_registration_is_parsed(self):
        sys.path.insert(0, G.BIN)
        root = "/w/inst"
        good = self.filled(root)
        hook = f"/usr/bin/python3 {root}/.claude/hooks/sandbox.py"
        ok = lambda d: subprocess.run(["/usr/bin/python3", os.path.join(G.BIN, "_ext.py"), "hook-registered", "-", hook],
                                      input=json.dumps(d), text=True, capture_output=True).returncode == 0
        self.assertTrue(ok(good))
        only_named = {"note": hook, "hooks": {"PostToolUse": good["hooks"]["PostToolUse"]}}
        self.assertFalse(ok(only_named))
        matched = json.loads(json.dumps(good))
        matched["hooks"]["PreToolUse"][0]["matcher"] = "Read"
        self.assertFalse(ok(matched))
        no_post = json.loads(json.dumps(good)); del no_post["hooks"]["PostToolUse"]
        self.assertFalse(ok(no_post))


class T44P15Foreground(Base):
    """P-15 (found 2026-10-03; user: "a and commit"): since kit-v0.6.20 the hook sets a worker's run_in_background false,
    so a worker's every command ends with its call; the solver brief still said long computations run in the background
    and are polled. No brief, template or harness note offers a background job to a worker."""

    def test_no_brief_offers_a_background_job(self):
        os.makedirs(os.path.join(self.root, "problems", "x"))
        open(os.path.join(self.root, "problems", "x", "PROBLEM.md"), "w").write("p\n")
        p = G.tool(self.root, "new-run", "workspace-9", "s", "--role", "solver", "--problem", "x")
        self.assertEqual(p.returncode, 0, p.stderr)
        rd = [d for d in os.listdir(os.path.join(self.root, "workspace-9", "runs")) if d.endswith("-s")][0]
        b = " ".join(open(os.path.join(self.root, "workspace-9", "runs", rd, "BRIEF.md")).read().split())
        self.assertNotIn("run in the background", b)
        self.assertIn("in the foreground", b)
        self.assertIn("ends with its call", b)
        for rel in ("templates/orchestrator-prompt.md", "templates/analyst-prompt.md"):
            t = " ".join(open(os.path.join(G.REAL, rel)).read().split())
            with self.subTest(rel=rel):
                self.assertNotIn("while a background job runs", t)


class T43P14ApprovalLine(Base):
    """P-14 (c) (the proof instance's report, 2026-10-02; user: "do your suggestions"): an orchestrator gave the approval
    command from memory in a wrong form. bin/manifest now prints, after the hashes, the exact line that approves what it
    showed: the targets, each one's 12-hex digest in order, and the flags; the one form the hook offers for the tap."""

    def line(self, *args):
        p = G.tool(self.root, "manifest", *args)
        self.assertEqual(p.returncode, 0, p.stderr)
        got = [l for l in p.stdout.splitlines() if l.startswith("approve exactly this: ")]
        self.assertEqual(len(got), 1, p.stdout)
        return got[0][len("approve exactly this: "):]

    def test_a_launch(self):
        import shlex
        cmd = self.line("900-solve", "--", *G.F)
        argv = shlex.split(cmd)
        # an absolute path (P-14 follow-up): a `!` command works from any directory, and the hook offers the tap for it
        self.assertEqual(argv[0], os.path.join(self.root, "bin", "approve"))
        self.assertEqual(argv[1:3], ["900-solve", "--digest"])
        self.assertEqual(argv[4:], ["--", *G.F])
        a, jobs = self.A.plan(argv[1:], self.root)            # the line is accepted as it stands
        self.assertEqual(len(jobs), 1)
        self.assertEqual(self.A.digest(*jobs[0][:4])[:12], argv[3])

    def test_a_batch_and_a_ledger_append(self):
        rd2 = os.path.join(self.root, "workspace-9", "runs", "902-two")
        os.makedirs(rd2)
        open(os.path.join(rd2, "BRIEF.md"), "w").write("two\n")
        import shlex
        argv = shlex.split(self.line("900-solve", "902-two", "--show", "--", *G.F))
        self.assertEqual(argv[1:3], ["900-solve", "902-two"])
        self.assertNotIn("--show", argv)
        self.assertEqual(len(argv[argv.index("--digest") + 1].split(",")), 2)
        argv = shlex.split(self.line("--ledger", "900-solve", "c1"))
        self.assertEqual(argv[1:4], ["--ledger", "900-solve", "c1"])
        self.assertNotIn("--", argv)


if __name__ == "__main__":
    unittest.main(verbosity=2, warnings="ignore")
