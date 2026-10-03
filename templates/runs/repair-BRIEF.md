<!-- The task sections of a repair run (a form the source used): a solver run that finishes the repair of a finite check a
     referee found wider in its English than in what it certifies, and states exactly what it certifies. Make the run
     with `bin/new-run WORKSPACE ⟨slug⟩ --role solver --problem ⟨p⟩`, give it the earlier run's output files as inputs (byte
     copies, by the user's file exception: --input-approved), and replace the generated skeleton's ⟨Task⟩, ⟨Gates⟩,
     ⟨Frozen before running⟩, ⟨Classes every start ends in⟩, ⟨Kill criteria⟩ and ⟨E2…⟩ slots with the sections below,
     filled. Everything else in the generated brief stays (budget, rules, schema, kill rule, the asserted-part table). Delete
     this comment. A wording-only fix, the artifact unchanged, is a restatement instead (restatement-BRIEF.md). -->

## Task
⟨The claim being repaired: "the ledger entry C-NNN [TAG]" or "run NNN's claim cK"⟩ was ⟨stated | restated⟩ by an earlier run, whose
claim ⟨cK⟩ is in `input/claims.json` (its sentence there is the target). That run's output is supplied as ⟨every input file, by
name⟩ (byte copies of its output). A `⟨question⟩` referee found that its sentence asserts more than its check and mutations
certify. Your job: finish the repair, then write the one sentence the check does certify. Either direction is a complete
result: the target sentence at full width with a check that certifies all of it, or a narrower sentence with the reason for
each part left out. ⟨Anything that is NOT the target, and stays out.⟩

What is to be repaired (the referee's findings, in the orchestrator's words; one item per finding):
(R1) ⟨a wording the artifact does not support, and what it must say instead⟩;
(R2) ⟨a range or loop no mutation truncates: for EVERY range named in the claim's `range` or `coverage`, add a truncation mutation
     that shortens that loop in a copy of the evidence under scratch/ and kills the checker; keep the existing mutations that still
     apply⟩;
(R3) `output/result.md` carries a table mapping each range to the mutation that kills it, and each asserted part to its check and
     mutation.
Re-run every mutation, old and new, against the repaired script and log each run (mutation, exit code, the FAIL lines printed)
under output/. A part you cannot make a mutation kill is left out of the sentence, or the claim is [NUMERIC]; say which and why.

Phase 1 (`output/plan.md`): the list of ranges and asserted parts, one line each, with the check and the mutation you will give
it⟨, and any definition the sentence needs⟩. Then `ledger "plan frozen"`. Phase 2: the repaired script (exact arithmetic kept),
its data and helpers, the mutations, `output/result.md`, `output/claims.json` with exactly one claim: ⟨cK⟩, ⟨[TAG]⟩ (or
[NUMERIC]), ⟨`"supersedes": "C-NNN"` | no supersede⟩, its statement written from what the repaired script asserts, its premises,
and `silent_links` naming what the script does not check.

### Gates
G1. No Phase 2 before `output/plan.md` exists and `ledger "plan frozen"` is logged.

### Frozen before running
The plan, every expected count and the list of ranges (G1); a later change is reported as post-hoc, with the reason.

### Classes every start ends in
FULL (the target sentence certified at full width) / NARROWED (a narrower sentence, each omission with its reason) / NUMERIC.

## Kill criteria
K-a. A part turns out false on the stated data: stop repairing that part, report the true value with the check that shows it,
     and leave the part out of the sentence; that is a complete result.
K-b. A truncation mutation cannot be made to fail for a range: narrow the range, or leave the part out, and say so.

## Cycle exit criteria (after E1)
E2. `output/plan.md` holds the list of ranges and asserted parts; G1 marked. E3. Exactly one claim, ⟨cK⟩⟨, with
`"supersedes": "C-NNN"`⟩; its class (FULL / NARROWED / NUMERIC) stated in the first lines of `output/result.md`. E4. Every range
and every asserted part of the statement has a declared mutation that kills it (non-zero exit with the targeted part's FAIL line,
named in `expect_stdout_contains`), mapped in `output/result.md`, and every mutation's re-run is logged under output/; or the part
is absent from the statement.
