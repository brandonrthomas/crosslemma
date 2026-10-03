# Packets and outside input

This page answers: what goes into a worker's packet, what never does, and how anything from outside the instance's
own runs is allowed in?

## The packet is what the worker is given

A worker sees its run directory and nothing else of the instance (see [the sandbox](sandbox.md)). Its packet is
what it is given there: `BRIEF.md`, a `HARNESS-NOTE.md` on a Codex or networked route, and the files under `input/`;
those are the files the packet scan reads. Every other file in the run directory is visible to the worker too, and
even the slug in the directory's name is something the worker reads, which is why a slug never announces the answer
(→ **A slug, and every file in a run directory, is something the worker sees**).

The launch approval binds the packet and every other regular file in the run directory except the launch's own
records, hashed (see [the approval gate](approval-gate.md)). A user approving a launch is approving the packet.

## What each role receives

[`bin/new-run`](../reference/tools/new-run.md) builds the run directory and its brief skeleton, and copies the inputs
it is given. What it puts in depends on the role:

| role | what its packet holds |
|---|---|
| solver | its brief (with the claims schema embedded), `input/PROBLEM.md`, the inputs the orchestrator names, and `input/validate-claims.py`, the same form validator the checker uses (→ **`bin/validate-claims` is one piece of code**) |
| referee | its brief for one question, `input/claim.json` (one claim), `input/artifact/` (the artifact and the files the claim declares as `deps`), `input/PROBLEM.md`, and, for a claim resting on other entries, `input/ledger-premises.md` |
| evaluator | the locked answer keys or label maps it scores against; it emits scores only |
| other | a bare brief, filled by hand (a canary, an audit, an outside reader) |

A referee's packet is decided by the claim, not by the orchestrator: the solver declared the `deps`, so the choice is
on the record (→ **A referee sees the artifact, its declared `deps`**). A referee of a text claim is also pointed at
the library definitions the text quotes (→ **A referee of a text claim**), and a referee of a claim with ledger
premises gets those entries, extracted by a tool (→ **A referee is given the ledger entries a claim rests on**).

## What never goes in

These are refused by the tools, not left to care:

- **Answer keys and label maps** (`data/locked/`), except for an evaluator. `bin/new-run` refuses to copy them, and
  [`bin/verify-data`](../reference/tools/verify-data.md) finds a copy by hash under any name
  (→ **Controls are blinded and locked**).
- **Record files under their own names**: the ledger, `CLAIMS.md`, `HANDOFF.md`, the rules, `CLAUDE.md`, another
  run's `BRIEF.md` (→ **No record file**).
- **Prior attempts, for a solver.** A solver gets no input from another run. The one way round is `--input-approved`,
  for a file the user has excepted by name (`! bin/packet-except`); the tool takes it only when its bytes are on that
  list, and its source and hash go on the ledger
  (→ **Solver sees no prior attempts, no bench brief, no expected answer**,
  → **`--input-approved` puts a user-excepted input's source and hash on the ledger**).
- **`CLAIMS.md` under its own name** (one of the record files above). The rule is that a worker's view of the record
  is an extract made by [`bin/claims-extract`](../reference/tools/claims-extract.md) by fixed rules, less the entries
  and notes the user has excluded (→ **A worker's extract of the ledger is made by a tool**). The tools refuse
  only the name: `RULES.md` §8 notes that a packet copies record files under other names, and `CLAIMS.md` is open
  material, so the packet scan does not catch a renamed copy either.
- **Blocked material** (next section).

## Blocked material and the packet scan

Some text in an instance should shape no worker's judgement: probabilities of success, rankings of routes,
evaluations of the record. An instance lists it in `data/packet-rules.json`
([RULES.md §8](../../RULES.md#8-the-record), → **No packet carries blocked material**). The list is the user's:
the user adds to it with [`bin/packet-block`](../reference/tools/packet-block.md), run with `!`, and removes an
entry by editing the list by hand; the hook refuses the orchestrator both. A rule blocks a file or directory whole, or only the lines of a file
that match a pattern. A new instance starts with `DIRECTION.md`, `HANDOFF.md`, `handoffs/` and `intake/` blocked, and
with route-verdict words ("most promising", PURSUE, a ranking number) flagged in any packet file.

[`bin/lint-brief`](../reference/tools/lint-brief.md) scans every packet file, whatever its name, and reports:

- a file byte-identical to a blocked file;
- a run of twelve words shared with blocked text, unless the same words also appear in **open material**: the
  problem files, the rules, the tools, the claims record, and the output of earlier runs that were launched or
  checked and are not blocked themselves;
- a line naming a blocked path (a warning: the name reaches the worker, not the text).

A packet is never open material, so two packets cannot excuse each other. A blocked path inside open material is not
open either, so blocked text cannot excuse itself. The launcher runs the same scan, rebuilding its index rather than
trusting a cache, and refuses before it touches the approval.

The user can except one file by its hash with [`bin/packet-except`](../reference/tools/packet-except.md); an edit
to the file ends the exception.

Two practices go with the scan. Files that are blocked describe a pending packet; they never quote it, or the packet
would share twelve words with blocked material and be refused. And nothing the scan reads changes between an approval
and its launch (→ **Between an approval and its launch, no scanned file changes**).

**What the scan is not.** It is a net under the rule, not the rule; packets are still built from open material only.
It cannot see a verdict that an open run once quoted, which is why the verdict-word pattern exists. The hook recognises
the two lists by name, so a glob or a constructed path gets past it: that is deliberate forgery, outside what the kit
claims to stop.

## Outside input

Outside input is anything that enters the instance other than through its own runs: a model session the user runs
elsewhere, another workspace, a local agent, an analyst's text, and any result, target, framing, data or tool relayed
from them. The user's own rulings are not outside input; text an analyst drafted is, even when the user relays
it ([RULES.md §8, "Outside input"](../../RULES.md#outside-input), → **Outside input has an intake record first**).

The source workspace learned this the hard way: an outside result framed a run through its brief, was quoted as a
premise in the run's output, and ended up under a ledgered claim's last clause without ever being verified there.
Because copies of it lay in open material, they excused the same text in later packets.

How it comes in:

1. **An intake record first.** Before anything acts on it, the orchestrator writes `intake/IN-NNN-slug/record.md` from
   [the intake template](../../templates/intake-record.md), with the text or files verbatim under `verbatim/` and
   their hashes. `bin/verify-data` checks the record's name and hashes.
2. **Each item is classed by the user**: target statement, premise, framing, data, tool, or record-only. Until the
   user rules, it is record-only.
3. **The class decides the use.** A premise enters the record only through a verify-or-refute run whose packet holds
   the target statement and not the outside text, or as a conditional premise under its own ruling. Framing enters a brief only under a ruling,
   in a paragraph tagged as outside input that was not verified here. A message saying "assume it is true" never makes
   a premise.
4. **The orchestrator counts independence.** The record lists who has seen each input. When referees or a replicate
   are chosen, the model family of every outside input a claim rests on, or that framed the run producing it, counts
   as well as the producer's. No tool computes this; it is the orchestrator's check, recorded with the user's
   rulings ([SCHEMAS.md §4](../../SCHEMAS.md#4-earned-tag--binmerge-computes-binledger-claims-enforces)).

`intake/` itself never goes into a packet unless the user excepts a file. Rulings on outside input are recorded
with the IN id where the instance records rulings.

## Packets for outside steps

The same idea, a self-contained packet, is how the kit asks anyone else a question. An outside-reader packet, a set-up
audit of a brief, and a handoff audit each carry everything needed, the evidence both ways, and the interested party's
view last and labelled. If a question cannot be written down that way, it is not ready to hand to anyone
([RULES.md §4](../../RULES.md#4-roles--three-plus-ad-hoc), → **The packet is the mechanism**). The forms are in
[templates](../../templates/README.md); when each tends to pay is in
[RULES.md §10](../../RULES.md#10-outside-checks--the-operators-never-a-gate).

## What this does not stop

- **What the orchestrator writes into a brief.** The brief is the orchestrator's text. The scan catches copies of
  blocked material, not a paraphrase of it; `--input-approved` and every input the orchestrator names are visible to
  the user in the launch manifest, which is where they are checked.
- **What the model already knows.** A packet controls what a worker is given, not what its training contains.
- **Outside input nobody records.** The intake rule depends on the orchestrator recognising outside input when it
  arrives; nothing detects an unrecorded one.

## Related

- [The record](the-record.md): where intake records, rulings and the claims record live.
- [Roles](roles.md): who builds packets and who receives them.
- [Glossary](../reference/glossary.md).
