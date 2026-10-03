# Schemas — claims.json · check.json · referee.json · CLAIMS.md

**Provenance.** This file and the tools implement the method of the source the kit was extracted from. Where a rule
has a reason worth keeping they cite it as `LESSONS.md "<label>"`, the kit's own index of incidents. Run numbers,
claim ids and dated rulings in this file are the source's, kept as provenance and marked where they appear: they
index a record the kit does not carry, and an instance's own runs with the same numbers are unrelated.

The schemas are fixed before any run in an instance. The tools in `bin/` implement
exactly this; `bin/new-run` embeds the worker-facing copy of the claims schema in every
solver BRIEF (workers cannot read this file). Changing a schema is a method change:
a methods session only, bump the `schema` string, record it in `KIT-CHANGELOG.md` and the handoff.

## 1. `output/claims.json` — written by the solver

```json
{
  "schema": "kit/claims/2",
  "run": "003-slug",
  "problem": "<problems/<name>>",
  "claims": [ { ...claim... } ]
}
```

One claim object per statement the solver wants recorded. Fields:

| field | required | meaning |
|---|---|---|
| `id` | always | `c1`, `c2`, … local to the run. Global ids are assigned by `bin/ledger-claims`. |
| `tag` | always | `PROVED` `VERIFIED` `NUMERIC` `CONJECTURE` `HEURISTIC` `GAP` |
| `statement` | always | one sentence, ≤600 chars, every range and hypothesis explicit. **Written from what the artifact establishes, never from a description or summary of it**: for a `lean` artifact, read the formal statement of every declaration in `decls` and carry each of its hypotheses into the sentence. An English quantifier wider than the theorem's is an overclaim (LESSONS.md "Every English statement is written from the formal statement", after the source's run 040/c2) |
| `artifact.type` | always | `script` `lean` `text` `none` |
| `artifact.path` | type≠none | relative, under `output/`, never `result.md` |
| `artifact.cmd` | script | run from the run dir inside the sandbox; exit 0 = pass. Optional `expect_exit`, `expect_stdout_contains` (a substring: end the value, e.g. `count=17\n`), `expect_stdout_sha256` |
| `artifact.decls` | lean | declaration names whose axioms are audited |
| `artifact.deps` | optional | other files under `output/` the artifact needs (lemma files, data). Copied to the referee run; hashed for staleness |
| `artifact.mutations` | optional (script); VERIFIED coverage claims should have ≥1 | list of `{name, cmd[, expect_exit][, expect_stdout_contains]}`. `cmd` runs in the run dir inside the sandbox, perturbs a copy of the evidence under `scratch/` and re-runs the checker on the copy; it must exit non-zero (`expect_exit` "nonzero" default, or a non-zero int) and, when `expect_stdout_contains` names the targeted part's FAIL line, print it: a crash, or another part's failure, is then not a kill (LESSONS.md "A mutation kills only with its FAIL line"). Under `kit/claims/2` every mutation must name it (`bin/validate-claims` ERR; a warning for `kit/claims/1`). `bin/check --mutate` runs them; one the checker survives fails the claim. Added 2026-09-16 (LESSONS.md "Optional `artifact.mutations`"), optional, so the schema string is unchanged |
| `artifact.native_decide` | lean, if used | must be `true` when any decl depends on a native_decide axiom |
| `range` | VERIFIED, NUMERIC | exactly what was covered |
| `coverage` | VERIFIED | what certifies the range was covered (count printed and asserted, etc.) |
| `silent_links` | PROVED, VERIFIED | list of strings; `["none"]` if none — the links no artifact checks. **A disclosure, not a premise** (LESSONS.md "The evidence boundary"): naming a link locates an obligation and does not discharge it, so a referee may not accept a declared link as given. In particular, describing an object by an equivalent property instead of the definition the declaration uses needs the bridge supplied, not declared |
| `evidence`, `counter_pressure` | CONJECTURE | |
| `nonrigorous_step` | HEURISTIC | |
| `must_show` | GAP | |
| `supersedes` | optional | `null` or a global id `C-NNN` already in CLAIMS.md |
| `premises` | PROVED, VERIFIED under `kit/claims/2` | list of `{kind, what[, source, quote]}`: `kind` ∈ kernel, classical, published, source, ledger, software; everything the claim rests on besides its artifact. A `published` or `source` premise gives `source` (the primary text, under `output/`) and `quote` (a file quoting the statement used, verbatim, with its location), both also in `artifact.deps`; a restatement in a secondary source is not a premise. A `ledger` premise is one `C-NNN`. |

**Schema strings.** New briefs write `kit/claims/2` (LESSONS.md "Premises on every claim; the primary text quoted; a conditional marker"): `premises` is required for
PROVED and VERIFIED. `kit/claims/1` is still accepted for runs made before `kit-v0.3`, and for byte-copy restatements of
their claims; `premises` is optional there.

No other field exists. An unknown field, or a field in the wrong place (a `deps` at the claim's top level, where
nothing reads it), is an error in `bin/validate-claims` and so fails `bin/check` (LESSONS.md "Unknown or misplaced fields are errors", 2026-09-22,
after the source's run 086; the schema string is unchanged: of the claims files on its record only run 086's, restated as
run 087, fails the new rule).

Allowed artifact types by tag: PROVED → lean, text · VERIFIED, NUMERIC → script ·
CONJECTURE, HEURISTIC → script, text, none · GAP → text, none.

`output/result.md` ≤150 lines. Proofs and evidence live in their own files under `output/`.

## 2. `check.json` — written by `bin/check` (a script, RULES.md step 2)

Placed at the run root (orchestrator-owned), logs under `RUN/check/`.

```json
{
  "schema": "kit/check/2", "run": "003-slug", "generated": "<utc>",
  "doc_errors": [],
  "claims": [
    { "id": "c1", "tag": "VERIFIED", "check": "pass",
      "reasons": [], "artifact_sha256": "…", "deps_sha256": {"output/lemmas.md": "…"}, "artifact_exit": 0,
      "stdout_tail": "…", "axioms": {"decl": ["propext"]}, "native_decide": ["decl"],
      "signatures": {"decl": "decl : ∀ (x : ℤ), ..."}, "signatures_missing": [],
      "advisory_float_tokens": 0, "advisory_file_has_sorry": true, "banned_untagged": [],
      "mutations": {"n": 2, "failed_as_expected": 2, "results": [{"name": "drop-one-case", "exit": 1, "failed_as_expected": true, "detail": "exit 1"}]},
      "mutations_missing": true }
  ],
  "result_md": {"exists": true, "lines": 120, "within_limit": true, "banned_untagged": [{"line": 7, "word": "clearly"}]},
  "prose_flags": 1,
  "overall": "pass" | "fail",
  "partial": ["c3"]
}
```

`check` per claim: `pass` (artifact ran and met every expectation; Lean decls depend only on
`propext`, `Classical.choice`, `Quot.sound`, plus native_decide axioms only if declared, no
`sorryAx`, as found by the kit's own audit of the compiled artifact after a kernel replay, never by the artifact's file), `fail` (any expectation missed, or the claim is malformed), `n/a` (text or no
artifact: nothing a script can certify). `overall` is pass only if every claim is pass/n/a,
`doc_errors` is empty, and result.md exists and is ≤150 lines. Banned words on untagged
lines of result.md are counted in `prose_flags` and listed in `result_md.banned_untagged`;
they are noted on the record (verdict.md, CLAIMS.md `Prose:` line) and never block (check/2,
the source's user ruling 2026-09-16). A tag counts as present on a line if `[TAG` opens a bracket, so
`[PROVED, sketch]` and `[VERIFIED upper bound; =108 NUMERIC]` are tagged lines. `partial` is present when `--claim` was used; other claims' records are kept
from the previous check.json. Artifacts run inside the same bwrap sandbox the worker had.
With `--mutate` (LESSONS.md "Optional `artifact.mutations`") each declared mutation runs in the sandbox after a passing
artifact; `mutations` records the outcome and a mutation the checker survives makes the claim
`fail` ("the artifact does not certify the stated coverage"). `mutations_missing` marks
a VERIFIED script claim with no mutation record from this check: none declared, or declared and not run (a check
without `--mutate`, which also sets `mutations_declared`); the earned tag records such a claim as NUMERIC (§4).
Logs: `RUN/check/<id>.mut.<name>.log`.
Every check.json also records `library: {"root": "lean", "files": N, "digest": "<sha256>"}`, the
state of the shared Lean library when the check ran (LESSONS.md "The Lean library has a master list"), computed by the same function
`bin/verify-data` uses to guard it. The source's runs checked before 2026-09-17 19:30 MST lack the field; their
check records are not rewritten, because ledger entries cite them by generation time.
For the same reason (LESSONS.md "A ledgered run's check record is kept"), before `bin/check` (and so `bin/close-run`)
re-checks a run that has any claim in `CLAIMS.md`, it keeps the current record as `RUN/check.<generated>.json` (characters
outside `[0-9A-Za-z.-]` of the `generated` value replaced by `-`), with a `CHECK-KEPT` ledger line; a kept file is never
overwritten (the same bytes are accepted, other bytes refused, exit 2, before anything is checked). A ledger entry's `Check:`
line then names either `check.json` or the kept file with that generation time.
For a `lean` artifact `bin/check` also runs `#check @decl` on every declaration and stores the
printed type in `signatures` (LESSONS.md "Formal statements captured beside the English", 2026-09-17); `bin/merge` puts each claim's English
statement and its formal statements side by side under a **Formal statements** heading in
`verdict.md`, so a fidelity read starts from the binder list instead of a file hunt. A declaration
whose type could not be parsed is listed in `signatures_missing`, which is advisory and never
fails a claim. Both fields are additive and optional, so the schema string is unchanged.

## 3. `output/referee.json` — written by a referee run, exactly these six fields

```json
{ "schema": "kit/referee/1", "run": "003-slug", "claim": "c1",
  "verdict": "holds" | "falsified" | "gap" | "unverifiable",
  "pointer": "input/artifact/proof-c1.md:L42",
  "note": "≤3 non-empty lines, ≤600 chars" }
```

**Two questions, one referee each (LESSONS.md "Two referees per PROVED claim, one per question", 2026-09-17).** `bin/new-run --role referee`
takes `--question`:

| question | brief asks | default |
|---|---|---|
| `certify` | does the artifact certify the statement at the stated tag? | yes; text unchanged since the source's ladder 1, so its runs 003–014 and 026–031 calibrate it |
| `hypotheses` | does the English carry every restriction the artifact needs? Enumerate the formal hypotheses, match each to the words that carry it, report the unmatched | — |
| `sentence` | (script claims; LESSONS.md "A sentence referee reads every script claim") does the English say exactly what the script asserts (exit conditions, not printed values), on exactly the stated range; is each asserted part exercised by a declared mutation; was a coverage count frozen from the run's own output; does a package-backed VERIFIED meet the computer-algebra rule | required for VERIFIED and NUMERIC under `kit/claims/2` |

Every question's brief: an artifact that certifies less than the English says is
a `gap`, never `holds` with a caveat, with the sentence the artifact does support in the note; and a claim's
`published` or `source` premises are checked against their `source` and `quote` files.

A PROVED claim gets one of each; `bin/new-run` records which in the run's binding, `data/referee-bindings/<run>.json`
(P-12 C3: outside every run directory, which the worker writes), and `bin/merge`
prints `verdict/question`. The earned-tag rules below resolve disagreement: one `gap` against one
`holds` gives `[GAP]`, and PROVED needs *every* live referee to hold and a live hold on *both*
questions. No adjudicating agent exists, by design; the ≤3-line note bound is what lets the user read
both verdicts and rule. A PROVED claim holding on one question only is PENDING, and `bin/close-run`
prints the run for the missing question (P-3 B4, `kit-v0.6.1`).

A referee run is created by `bin/new-run … --role referee --claim RUN ID` and receives only
`input/claim.json`, `input/artifact/…` (the artifact and its declared `deps`), `input/PROBLEM.md`, and, when the claim has `ledger`
premises, `input/ledger-premises.md` (those entries, by `bin/claims-extract --ids`; LESSONS.md "A referee is given the
ledger entries a claim rests on").
The source's user ruling 2026-09-16: a referee may see every file the claim declares it needs; the solver
declares them in `deps`, so the choice is on the record, not the orchestrator's. Any extra field, a longer note, or
an unknown verdict makes the file INVALID: `bin/merge` lists it and ignores it. A finding
that is not typed does not exist (`RULES.md` §7).

A verdict is bound to the artifact the referee saw: `bin/new-run` copies the artifact into the
referee run's `input/artifact/`, and `bin/merge` / `bin/ledger-claims` hash that copy against
the sha256 in check.json. If the solver's artifact changed after the referee run was created,
the verdict is STALE and does not count; referee the current file again. The same applies to
any `deps` file.

## 4. Earned tag — `bin/merge` computes, `bin/ledger-claims` enforces

| condition (first match wins) | earned |
|---|---|
| any live referee `falsified` | FALSIFIED → not recorded; new brief |
| check `fail` | BLOCKED → not recorded |
| any live referee `gap` | `[GAP]` (recorded with the referee pointer, whatever was claimed) |
| claimed PROVED, check pass or n/a, every live referee `holds` (≥1), no live hold on one of the two questions (`certify`, `hypotheses`) | PENDING → not recorded (needs the missing question) |
| claimed PROVED, check pass or n/a, every live referee `holds`, both questions held, no live `certify` hold from the other model family | PENDING → not recorded (needs the cross-family read) |
| claimed PROVED, check pass or n/a, every live referee `holds`, both questions held, the cross-family `certify` hold | `[PROVED]` |
| claimed PROVED otherwise | PENDING → not recorded (needs a referee) |
| claimed VERIFIED / NUMERIC under `kit/claims/2`, check pass, no live `sentence` referee holding | PENDING → not recorded |
| claimed VERIFIED / NUMERIC under `kit/claims/2`, check pass, no live `sentence` hold from the other model family | PENDING → not recorded |
| claimed VERIFIED, a script with no declared mutation (`mutations_missing`), otherwise as below | `[NUMERIC]` (a coverage claim with no mutation test) |
| claimed VERIFIED / NUMERIC, check pass | as claimed (the artifact certifies; under claims/1 a referee is optional) |
| claimed CONJECTURE / HEURISTIC / GAP, well-formed | as claimed |

PROVED always needs a referee because the one thing no script checks is whether the formal
or written statement says what the English statement says.

**The cross-family read** (LESSONS.md "A cross-family certify read"; the source's method change 59). Families
(`bin/_lib.py` `model_family`): Anthropic (anthropic, opus, fable, sonnet, haiku, claude) and OpenAI (openai, gpt, sol,
astra, codex), matched against the words of the models that answered, from the run's own record (`models_seen`), or, with
none recorded, of the `--model` of the run's launch in `RUN/time.log`; answered by another family than the approved model's,
or by two, the producer is unknown (`kit-v0.4.1`). A run with no launch (a restatement the orchestrator assembled) takes the
family of the run named in `RUN/.source-run`, which the orchestrator writes when it assembles the run, and is shown as
"restated by the orchestrator (Anthropic)". An unknown producer, or a restatement of a run of the other family than the
orchestrator's, is met only through the user's ruling, which the user records in `data/cross-family-rulings.json`
(`{"<run>": "<family> <where the ruling is recorded>"}`; the hook refuses the orchestrator any write to it, P-12 C3): the family named is **the referee's whose hold then counts, not the producer's**
(the source's orchestrator once read it the other way). `bin/merge` (`verdict.md`, "Model
families"), `bin/close-run` and `bin/ledger-claims` print every claim's family line; `bin/close-run` names the missing
cross-family run. In the kit the rule binds every run (no instance had ledgered claims when it came in); an entry already
in `CLAIMS.md` is never recomputed. Independence from outside inputs (`RULES.md` §8 "Outside input" rule 7) is the
orchestrator's check, recorded with the user's rulings.

## 5. `CLAIMS.md` entry — appended by `bin/ledger-claims RUN ID…` on the user's approval

```
## C-007  [VERIFIED]  2026-09-16  run 003-slug/c1
<statement>
Claimed: [PROVED]; earned [GAP] because a referee found a gap.        (only when they differ)
Artifact (script): workspace-1/runs/003-slug/output/count.py  sha256=…  cmd=`…` exit=0
Range: …            Coverage: …            Silent links: …
Check: pass (workspace-1/runs/003-slug/check.json, generated <utc>)
Prose: 3 untagged banned word(s) in result.md (technical flag, not blocking; lines 26, 84, 108)   (only when nonzero)
Referee: holds (workspace-1/runs/004-ref/output/referee.json → pointer)
Supersedes: C-003 | —
```
Since `kit/claims/2`: a `Premises:` line (kind: what, with the source and quote
files) before `Silent links:`, and when any premise is `published`, `source` or `ledger` the header ends
`  (conditional: <kinds>)`, after the run/claim field, so the header pattern still parses. Entries appended before
`kit/claims/2` carry no marker.

Notes (LESSONS.md "A changed novelty or an audit finding"): `bin/annotate-claim C-NNN "text"`, on the user's `bin/approve --annotate C-NNN "text"`, appends

```
## C-007-note  2026-09-16  <one line: novelty found later, audit finding, pointer to a later run>
```

at the end of the file, ending with "(Note by the orchestrator, not refereed.)" (LESSONS.md "A note says whose it is and does not vouch for the entry";
`--dry-run` prints the line without appending). A note never changes what the entry says is true (that is a
new claim with `supersedes`); it records what was learned about the entry afterwards, and it may not vouch
for the entry: text saying its truth is unchanged is refused. `bin/merge`,
`bin/ledger-claims` and `bin/close-run` print the notes on any id a run's claim is ledgered
under or supersedes. Note headers do not count as entries (`C-NNN-note` never matches the
entry pattern), so numbering is unaffected.

All-or-nothing per invocation. Refused: ids not in claims.json or check.json, already
recorded `(run, id)`, artifact whose sha256 differs from check.json, earned FALSIFIED /
BLOCKED / PENDING, `supersedes` naming an id not in CLAIMS.md, a `ledger` premise naming an id not in
CLAIMS.md, and any append without the user's approval record: `bin/approve --ledger RUN ID…`, bound to
the run's check.json, verdict files and claims and to exactly these ids, consumed by the append.
`--operator-approved` is still accepted and means nothing: the approval record is the approval. CLAIMS.md is
written, and flushed, before the ledger's `CLAIM` lines.

## 6. Tool summary

| tool | reads | writes |
|---|---|---|
| `bin/limits-exec RUN_DIR -- cmd…` | RUN_DIR/.limits | runs cmd in a systemd user scope (CPUQuota, MemoryMax) and stops it at the whole-run CPU budget (TERM to cmd, then after `cpu_grace_seconds`, default 30, KILL to everything left in the scope; exit 152); `RUN_DIR/usage.json` (`cpu_cap_hit`, `over_cpu_cap`, …), `time.log`. Used by `bin/run-external` |
| `bin/new-run WS SLUG --role solver --problem P [--input F…] [--cpu-hours H --threads N --mem-gb G]` (SLUG without a number: the tool adds NNN and refuses a slug that starts with one) | problems/P/PROBLEM.md, inputs (never data/locked, record files, other runs) | `WS/runs/NNN-SLUG/{BRIEF.md,.role,.limits,input/,scratch/,output/}` |
| `bin/new-run WS SLUG --role referee --claim RUN ID [--question certify\|hypotheses\|sentence]` | that claim, its artifact and declared deps, PROBLEM.md, the ledger entries it names as premises | same, with the referee BRIEF for that question, and `input/ledger-premises.md` when the claim has `ledger` premises (`bin/claims-extract --ids`) |
| `bin/validate-claims [RUN]` (stdlib; copied into solver runs as `input/validate-claims.py`) | output/claims.json, output/result.md, file existence under output/ | stdout ERR/WARN lines; exit 1 on any ERR. bin/check imports its rules |
| `bin/check RUN [--claim ID…] [--timeout S] [--mutate]` | output/claims.json, artifacts (run in bwrap) | `RUN/check.json`, `RUN/check/`; for a run with ledgered claims the previous record kept first as `RUN/check.<generated>.json` |
| `bin/close-run RUN [--no-mutate]` | runs verify-data, check --mutate, merge; check.json, referee files, CLAIMS.md notes | stdout: verdict path, result.md lines, prose flags, per-claim earned tags, the referee `new-run` line per PROVED claim lacking `holds`, the `ledger-claims` line to run on the user's go. Launches nothing, appends nothing |
| `bin/merge RUN` | check.json, every referee.json naming RUN | `RUN/verdict.md`, stdout |
| `bin/ledger-claims RUN ID…` (consumes `bin/approve --ledger RUN ID…`) | the above, existing notes | appends `CLAIMS.md` |
| `bin/claim-deps [C-NNN …]` (read-only) | CLAIMS.md | stdout: X depends on Y when Y's artifact sha256 is X's artifact or one of its deps ("file"), or X's statement or silent links name Y ("names"), or X's Premises line lists Y as a `ledger` premise ("premise"); a file restated under a live entry counts as the live entry's; no argument lists the live entries depending directly on a superseded one; `bin/close-run` and `bin/ledger-claims` print the same for any id a claim supersedes. Never blocks |
| `bin/annotate-claim C-NNN "text"` · `bin/annotate-claim --batch FILE` · `--dry-run` | CLAIMS.md headers; FILE, a JSON list of `{id, text}` | appends a `## C-NNN-note` line to `CLAIMS.md` (a batch: all or none, one approval from `bin/approve --annotate-batch FILE`) |
| `bin/handoff-archive [--session S]` | HANDOFF.md, git state | `handoffs/<date>-<sha|uncommitted>-<session>.md` (never overwrites) |
| `bin/run-external RUN --model ID [--via openrouter\|anthropic\|codex] [--effort E] [--max-turns N] [--network] [--wall-hours H] [--dry-run] [--detach]` · `bin/run-external --queue RUN… [flags] [--detach]` | RUN/BRIEF.md, RUN/HARNESS-NOTE.md, the launch approval | launches one worker (Codex: after the offline sub-agent probe; `--max-turns` caps its tool calls); `RUN/launch.log` (Claude) or `RUN/launch.jsonl` + `launch.rollout.jsonl` (the main thread's session file) and any `launch.rollout.sub-N.jsonl` (Codex), moved in at exit; `RUN/RECORD-EXT.md` for Codex or `--network`; `LAUNCH-EXT`, `EXIT-EXT` (with `effort_seen=`, `models_seen=`, `model_fallback=`, `wall_cap_hit=`, `turn_cap_hit=`), `RECORD-EXT` ledger lines |
| `bin/watch-run RUN [-f] [--last N] [--full] [--thinking]` (read-only) | the run's transcript, live or finished | stdout |
| `bin/lint-brief RUN` · `bin/lint-brief --packet RUN` (read-only) | RUN/BRIEF.md, RUN/HARNESS-NOTE.md, RUN/input/; data/packet-rules.json, data/packet-exceptions.json | stdout ERR/WARN: unfilled slots, `deps` not tied to `artifact`, unknown `artifact.x`, a tool-call cap above the default `--max-turns`, the packet scan (a byte copy of, or a 12-word run shared with, blocked material no open material excuses; WARN for a blocked name); exit 1 on any ERR, `--packet` exit 4 if the scan itself failed. Run before `bin/manifest` |
| `bin/packet-block PATH "why"` · `--lines REGEX PATH "why"` · `--extract C-NNN "why"` · `--extract-note C-NNN DATE "why"` · `--list` (the user's) | — | appends to `data/packet-rules.json` (`--extract*`: under `"extract"`, the entries and notes `bin/claims-extract` leaves out); a `PACKET-BLOCK` ledger line |
| `bin/claims-extract [--through C-NNN] [--ids C-NNN …] [--library PREFIX …] [--supplied PREFIX=PATH …] [--date D] [--out FILE]` (read-only but `--out`) | CLAIMS.md; data/packet-rules.json `"extract"` | the worker's view of the ledger: live entries, each its header, statement, `Lean declarations:` or `Artifact type:`, and its Claimed, Premises and Supersedes lines; then the notes on them, verbatim; less the user's excluded entries (with their notes) and notes; a header saying what is left out, by id, and where each declaration prefix is. `--through` reads the ledger as of that entry; `--ids` gives exactly the entries named, superseded ones marked "Superseded by" (a referee's `input/ledger-premises.md`, written by `bin/new-run`). stdout, or FILE (never a record file name) and a `CLAIMS-EXTRACT` ledger line with its sha256 |
| `bin/packet-except FILE "ruling"` · `--list` (the user's) | FILE | appends its sha256 to `data/packet-exceptions.json`; a `PACKET-EXCEPT` ledger line |
| `bin/verify-data [--write-lean-manifest]` | hashes of data/locked/**, runs, problems, and every `lean/**/*.lean` against `lean.SHA256SUMS`; the backticked tree paths of HANDOFF.md; every `intake/IN-NNN-slug/` record's name, `record.md` and `SHA256SUMS` against its `verbatim/` | stdout; exit 1 on any finding. `--write-lean-manifest` rewrites the master list, which is the deliberate act of accepting a library edit |

The tools that act on the record append their lines to LEDGER.log via the orchestrator actor (some several, e.g.
`bin/run-external`'s LAUNCH-EXT and EXIT-EXT); `bin/handoff-archive` writes one `HANDOFF-ARCHIVE` line per archive;
`bin/lint-brief`, `bin/manifest`, `bin/watch-run`, `bin/check-env` and `bin/limits-exec` write none, and
`bin/new-workspace` creates the empty ledger. Every line is one line: a field's own line breaks become spaces.
`KIT_ROOT=<dir>` points them at a fixture tree for testing.

## 7. Fixed names

Names the tools, the hook and the suites share. Renaming one is a method change.

| name | what it is |
|---|---|
| `KIT_ROOT` | fixture-root override of every Python tool and suite (never read by the hook, which takes its root from its own path; the two launchers unset it for their approval check) |
| `KIT_RUN` | the run directory, inside the sandbox |
| `KIT_LEAN` | the linked library, inside the sandbox; unset when none is linked. The toolchain is read from `.kit-lean`, never from the environment |
| `KIT_THREADS`, `KIT_CPU_HOURS`, `KIT_MEM_GB` | the caps a worker's own scripts read, from the run's `.limits` |
| `KIT_WORKER_RUN` | the marker that makes a headless process a worker |
| `KIT_WORKER_NET`, `KIT_NET_GATEWAY` | the marker of a networked worker, and the search gateway's URL |
| `KIT_SESSION` | the session tag in an archived handoff's name |
| `KIT_HOOK_DEBUG` | the hook's debug-log switch |
| `KIT_CODEX_BIN_DIR`, `KIT_CODEX_AUTH` | test overrides for the external CLI and its auth file |
| `kit-worker` | the worker agent type (`.claude/agents/kit-worker.md`) |
| `kit-run-<RUN>` | the systemd user unit of a detached run |
| `/opt/kit/bin` | the in-sandbox mount holding the ledger shim and the search helpers |
| `--operator-approved` | a flag `bin/ledger-claims` and `bin/annotate-claim` still accept and ignore: the user's approval record is what they require |
| `USER APPROVAL (single use, 30 min): …` | the opening of the prompt text the hook computes from the bytes |
| `no user approval for these hashes` | the refusal that is the stop |
| `kit-env.json` | the instance's environment file (§8) |
| `RUN/.modules` | the licence modules a run's brief names, one per line (`bin/new-run --module`) |
| `KIT_WORKER_MODULES`, `KIT_WORKER_LICENCE_SOCKS` | set by `bin/run-external` in a worker's process environment: its granted licence modules, and `PORT=SOCKET,…` of their relays |
| `/opt/kit/licence/<i>.sock`, `KIT_LICENCE_FWD` | a relay socket inside the sandbox, and the forwarders `kit-shell` starts for a Codex worker's commands |
| `RUN/licence.log` | every licence connection a run's relays carried: open, close, byte counts; never contents |

## 8. `kit-env.json` — the instance's environment file, the user's

Read by `bin/_env.py` (its docstring is the full reference) for the hook, the Codex route, the launcher, `bin/check-env` and
`bin/verify-data`. The hook refuses the orchestrator any write to it (→ **The environment files are the user's**).
Every field is optional; `~` is the user's home and `<root>` the instance.

| field | type | meaning |
|---|---|---|
| `worker_path` | list of directories | mounted read-only for every worker and put on its `PATH`, after the modules' entries, before `/usr/bin:/bin` |
| `claude`, `codex` | command or absolute path | the CLIs; default `claude` and `codex` on `PATH`; Codex's real binary is found from its command |
| `codex_bin_dir` | directory | where Codex's real binary is, when it cannot be found |
| `model_families` | `{family: [words]}` | added to the built-in Anthropic and OpenAI words that decide a model's family (RULES.md §7) |
| `locked_dir` | path | the locked directory (answer keys, label maps), outside the instance; `bin/new-workspace` sets `~/.local/state/crosslemma/<instance>/locked`; without it, `<root>/data/locked`. Refused: the root, a home directory, a credential directory, the instance or anything inside or holding it |
| `modules.NAME.binds` | list of paths, or `{src, dest}` | read-only mounts; `dest` defaults to the source's own path |
| `modules.NAME.path`, `.env` | list; object | `PATH` and environment additions (not `PATH`, `HOME`, `LD_PRELOAD`, `LD_LIBRARY_PATH`) |
| `modules.NAME.check` | command | the self-test `bin/check-env` runs inside a worker's sandbox |
| `modules.NAME.brief` | one line | what every brief whose worker has the module says about it |
| `modules.NAME.licence_servers` | list of `{host, port}` | makes the module a licence module: given only to a run whose `RUN/.modules` and launch (`--module NAME`) both name it; port 1024–65535, one per port |

Refused, with a problem line, whoever wrote the file: a mount source or `PATH` entry that is the root, a home directory or one
holding it, the instance or a directory inside or holding it (but its library link `lean` and the kit's own shims under
`.claude/sandbox/`), or a credential directory (`~/.ssh`, `~/.gnupg`, `~/.claude`, `~/.codex`, `~/.config`, `~/.aws`, `~/.netrc`,
`~/.local/share/keyrings`). A module with a missing source is not mounted. With no file, an instance made before `kit-v0.5`
keeps its `.kit-lean` and `.kit-sage` modules exactly.
