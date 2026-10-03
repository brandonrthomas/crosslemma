# A full cycle

This guide helps you take one claim from a solver run to the claims record: brief, lint, manifest, approval, launch,
watch, close, referees, and the append, with the tool for each step.

It follows the cycle in [RULES.md §5](../../RULES.md#5-the-cycle) and [FLOW.md](../../FLOW.md). The orchestrator runs every
command below except the approvals, which are yours ([Approving](approving.md)). Every command runs from the instance's
root, in a session opened there (→ **A session works on the tree it was opened in**). The examples assume an instance at
`~/kits/my-problem` whose next free run number is 004; the tools assign the numbers, so yours will differ.

For what each tag means and how a claim earns one, see [the trust model](../concepts/trust-model.md).

## Before the first cycle

- The instance's canaries have run on every enabled route ([A new instance](new-instance.md)).
- The models you will use have been through each role's ladder (→ **Calibrate before trusting**).
- The session is fresh, has read `RULES.md` and `HANDOFF.md`, and has run the handoff's preflight
  (→ **Fresh orchestrator per cycle**).

## 1. The brief (step 0)

Make the solver run:

```sh
bin/new-run workspace-1 first-attack --role solver --problem my-problem
```

[`bin/new-run`](../reference/tools/new-run.md) creates `workspace-1/runs/004-first-attack/` with `BRIEF.md`, `input/`,
`scratch/`, `output/`, the run's enforced limits (`--cpu-hours`, `--threads`, `--mem-gb`; defaults 8, 8, 16) and a copy of
the problem statement and the claims validator. `--input PATH` copies more inputs; it refuses record files, anything from
`data/locked/`, and, for a solver, any other run's files. Those are copied only by `--input-approved PATH`, for a file you
have excepted by name with `! bin/packet-except`: the tool takes it only when its bytes are on that list, and records
its source and hash on the ledger. A referee takes no `--input` at all.

The orchestrator then fills every `⟨slot⟩` of the skeleton: the task, the gates, what is frozen before running, the classes
every unit of work ends in, the budget, the kill criteria and the **cycle exit criteria**, which are checked mechanically at
the end ([RULES.md §5, the brief](../../RULES.md#the-brief); → **The brief skeleton has fixed sections**;
→ **Cycle exit criteria written at step 0**). The slug and every file in the run are things the worker sees
(→ **A slug, and every file in a run directory, is something the worker sees**).

If the brief carries a new relaxation, list of conditions or transcription of a source, you may call a set-up audit first
([FLOW.md, outside steps](../../FLOW.md#outside-steps--called-not-wired-in)).

## 2. Lint, then manifest

```sh
bin/lint-brief 004-first-attack
```

[`bin/lint-brief`](../reference/tools/lint-brief.md) is read-only. It reports an error for an unfilled slot, a misplaced
`deps`, an unknown artifact field and a packet carrying blocked material, and exits 1; it warns when the brief allows more tool calls than the default turn cap. Clear
every error (→ **`bin/lint-brief` before `bin/manifest`**). Optionally, see what the launch would run, without touching any
approval:

```sh
bin/run-external 004-first-attack --via anthropic --model fable --effort high --dry-run
```

Then the manifest, with the exact flags the launch will use:

```sh
bin/manifest 004-first-attack -- --via anthropic --model fable --effort high
```

[`bin/manifest`](../reference/tools/manifest.md) prints every file the worker will see, the digest and the flags. The
orchestrator shows it to you in full.

## 3. Your approval (gate 1)

You approve those bytes and flags at your terminal or by a tap ([Approving](approving.md);
[RULES.md §6](../../RULES.md#6-approvals--the-gate)). From here until the launch, nothing in the run changes.

## 4. Launch

```sh
bin/run-external 004-first-attack --via anthropic --model fable --effort high --detach
```

[`bin/run-external`](../reference/tools/run-external.md) runs its own checks first, then consumes the approval and starts
the worker as a headless process in the sandbox (→ **Every worker is a headless main process**). The flags must be the
approved ones; `--detach` is not part of the approval, and runs the launch as the user service `kit-run-004-first-attack`
so it survives the session (→ **Long runs launch detached**). A run directory is launched once: a retry is a new run
(→ **A run directory is launched once**).

## 5. Watch

```sh
bin/watch-run 004-first-attack -f
```

[`bin/watch-run`](../reference/tools/watch-run.md) is a read-only view of the transcript (Ctrl-C leaves it; the run goes
on). `--last N` starts from the last N events. For a detached run, `systemctl --user status kit-run-004-first-attack` shows
the service, and `systemctl --user stop kit-run-004-first-attack` stops it, its worker included.

The run ends at its own end, at the turn cap, at the wall-clock cap (`--wall-hours`, default 4 h on the Claude routes and
2 h on Codex) or at the CPU budget (exit 152); its exit line says which (→ **A wall-clock cap on every route**). A detached
run's output is in `.claude/state/ext/004-first-attack/detached.out`.

## 6. Close (steps 2 and 4)

```sh
bin/close-run 004-first-attack
```

[`bin/close-run`](../reference/tools/close-run.md) runs [`bin/verify-data`](../reference/tools/verify-data.md), then
[`bin/check`](../reference/tools/check.md) with the declared mutation tests, then [`bin/merge`](../reference/tools/merge.md),
and prints a summary. It launches nothing and appends nothing (→ **`bin/close-run` performs steps 2 and 4**). Read:

- the verdict table's path (`verdict.md`) and the check's overall result;
- `result.md`'s line count and its prose flags;
- the models that answered, for the run and per claim, and each claim's claimed tag, check result and earned tag so far;
- the `families:` line for each claim: which model family produced it, which the referees came from;
- the `bin/new-run` lines for the referee runs still needed.

It exits 0 only when the check passed and nothing is pending. On a fresh solver run, referees are pending.

## 7. Referee runs (step 3)

A `[PROVED]` claim gets a `certify` read and a `hypotheses` read, plus a `certify` read from the other model family than
its producer's; a `[VERIFIED]` or `[NUMERIC]` claim gets a `sentence` read from the other family
([RULES.md §7](../../RULES.md#7-standing-rules-that-keep-cycles-convergent); → **Two referees per PROVED claim**;
→ **A cross-family certify read**; → **A sentence referee reads every script claim**). The earned tag enforces every
live referee holding and the cross-family hold; it does not count the two questions, and
[`bin/close-run`](../reference/tools/close-run.md) says so when a `[PROVED]` claim has only one, for you to decide.
`bin/close-run` prints the lines to make the runs: first the `certify` and `hypotheses` lines (or the `sentence` line), for
example:

```sh
bin/new-run workspace-1 ref-004-c1-cert --role referee --claim 004-first-attack c1 --question certify
bin/new-run workspace-1 ref-004-c1-hyp --role referee --claim 004-first-attack c1 --question hypotheses
```

A referee run's packet is the one claim, its artifact and declared deps, the problem statement and any ledger entries it
names as premises; its brief is complete as generated. The line for the cross-family read (slug ending `-xcert` or
`-xsent`) is printed by a later `bin/close-run`, once the reads it already has all hold. For a read from the other family
on the Codex route, add
`--harness codex` to the `bin/new-run` line, and launch it with `--via codex --model gpt-5.6-sol --effort high`.

Each referee run goes through the same steps 2 to 5: lint, manifest, your approval, launch, watch. Runs on the same flags
can be approved together and launched as a queue:

```sh
bin/manifest 005-ref-004-c1-cert 006-ref-004-c1-hyp -- --via anthropic --model fable --effort high
bin/run-external --queue 005-ref-004-c1-cert 006-ref-004-c1-hyp --via anthropic --model fable --effort high --detach
```

the second only after your batch approval (→ **A queue for runs approved together**).

## 8. The verdict table (gate 2)

When the referees have finished, close the solver run again:

```sh
bin/close-run 004-first-attack
```

[`bin/merge`](../reference/tools/merge.md) joins every well-formed `referee.json` that names the run into `verdict.md`:
claim, tag, check, referee, earned, with each formal statement beside its English. The earned tag is computed: a live
`falsified` wins, then a failed check, then any `gap`; `[PROVED]` needs every live referee to hold, a live hold on both
questions and a live cross-family `certify` hold (and its check), a `[VERIFIED]` script claim with no mutation run by its check records as `[NUMERIC]`, and under `kit/claims/2` `[VERIFIED]` and `[NUMERIC]` need a live `sentence` hold from the other family
([RULES.md §8, claim form](../../RULES.md#claim-form--the-schemas-are-law-schemasmd); → **Earned tag: falsified > check fail > gap**). A verdict is stale if the artifact or a dep changed after
the referee saw it.

The orchestrator shows you the table and the paths, and prints any referee note verbatim, never a summary
(→ **The orchestrator prints a referee's note; never summarises it**). You can read each `output/referee.json` directly.

## 9. The append (step 5)

For the claims whose earned tag is recordable, [`bin/close-run`](../reference/tools/close-run.md) prints two lines: the
approval (yours) and the append. The orchestrator shows the manifest of the append:

```sh
bin/manifest --ledger 004-first-attack c1
```

You approve it ([Approving](approving.md)); then:

```sh
bin/ledger-claims 004-first-attack c1
```

[`bin/ledger-claims`](../reference/tools/ledger-claims.md) appends each named claim to `CLAIMS.md` at the tag it earned,
with a global id `C-NNN`. It is all-or-nothing: a falsified, blocked or pending claim, a duplicate, or an artifact whose
hash differs from `check.json` refuses the whole append (→ **`ledger-claims` is all-or-nothing**).

## 10. After the append (step 6)

- A falsified claim leads to a new brief; a `gap` is recorded as `[GAP]`. Nothing else is queued
  (→ **Anything that does not falsify something on the record is dropped**).
- Check the brief's cycle exit criteria. Met: close the cycle. Not met: one more solver run, in a new run directory.
- A second referee gap on the same sentence is the moment for an outside-reader packet
  ([FLOW.md, outside steps](../../FLOW.md#outside-steps--called-not-wired-in)).
- The orchestrator commits by explicit paths, with the message from a file (→ **No `cd` in a compound command**), writes
  the handoff on `templates/HANDOFF.md`, runs that handoff's own preflight (→ **The writer runs its own handoff preflight**),
  and says the next cycle starts in a fresh session.

## Related

- [The record](../concepts/the-record.md): where each of these files lives and who writes it.
- [Ledger events](../reference/ledger-events.md): the lines each step writes.
- [SCHEMAS.md](../../SCHEMAS.md): `claims.json`, `check.json`, `referee.json` and the `CLAIMS.md` entry.
