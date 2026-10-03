# The record

This page answers: where is everything recorded in an instance, who writes each part, and who may read it?

## The map

An instance keeps its record in a few places, each with one job ([RULES.md §8](../../RULES.md#8-the-record)). The full
directory layout is in [layout](../reference/layout.md).

| where | what it holds | written by | read by |
|---|---|---|---|
| `LEDGER.log` | one line per event: every orchestrator call, every worker call, every launch, approval and append | the hook and the tools, append-only | the user; no agent |
| `CLAIMS.md` | one entry per recorded claim, at its earned tag, plus notes | [`bin/ledger-claims`](../reference/tools/ledger-claims.md) and [`bin/annotate-claim`](../reference/tools/annotate-claim.md), on approvals | anyone in the instance; workers get an extract |
| `workspace-N/runs/NNN-slug/` | one run: its packet, its output, its check, its transcript | `bin/new-run`, the worker, the checker, the launcher | the user and the orchestrator; the worker sees only its own |
| `HANDOFF.md` and `handoffs/` | the pointer sheet for the next session, and every earlier version | each session at its end; the hook archives it before a session's first touch | the next orchestrator; blocked from every packet |
| `problems/<name>/` | the problem statement, the prior-art register, attack boards, held sources | the user and the orchestrator | the user and the orchestrator; a packet copies `PROBLEM.md` |
| `intake/` | outside input: one folder per input, verbatim, hashed | the orchestrator, on receipt | the operator and orchestrators only |
| `data/locked/` (the locked directory: outside the tree since `kit-v0.6.9`, at `kit-env.json`'s `locked_dir`) | answer keys and control label maps | the user, or a design run's output moved unopened | an evaluator run only |
| `data/packet-rules.json`, `data/packet-exceptions.json` | what no packet may carry, and the files excepted | the user, through `bin/packet-block` and `bin/packet-except` | the scan |
| git history | every committed state of all of the above | commits with explicit paths | the user; agents within the same limits as for the files themselves |

Everything else refers to a claim by its id. No file restates a claim: a claim lives in exactly one place
([RULES.md §8](../../RULES.md#8-the-record)). Each problem has its own `workspace-N/`, and run numbers are unique
across workspaces (→ **One workspace per problem**).

## The ledger log

`LEDGER.log` is one line per event, in the form `utc | actor | run | event | detail`. The actor is `orchestrator`,
`user` (for approvals and the packet lists), a worker's key, `codex-worker` (a Codex worker's queued lines),
`hook`, or `foreign-session(<dir>)` (the gate's own lines in a session from outside the tree). Every event type and the tool that writes
it is listed in [ledger events](../reference/ledger-events.md).

Agents write it and never read it, and the hook enforces that for the orchestrator too: a Read of the file is refused,
and so is any shell command naming it, except a plain `git add`, `commit`, `status`, `diff --numstat` or `diff --stat` on its own
(→ **`LEDGER.log` is append-only**, → **Only a plain `git add`/`commit`/`status`/`diff --numstat`**;
[RULES.md §8](../../RULES.md#8-the-record)). The reason is that
an orchestrator reading its own log back would be treating its own account of events as evidence. The user reads
it.

A worker writes to it through a `ledger` command inside its sandbox. The line is queued in the run directory and moved
into the ledger by the hook (or, on the Codex route, by the launcher at exit), marked as the worker's.

Some properties are set outside the kit's tools:

- **Append-only at the file system.** [`bin/new-workspace`](../reference/tools/new-workspace.md) creates the ledger and
  prints the `chattr +a` command for the user to run; it uses no sudo itself.
- **Only this tree.** The hook writes nothing for a session whose project directory and working directory both lie
  outside the tree, except the gate's own lines, marked as a foreign session
  (→ **The hook ledgers only its own tree's sessions**). The ledger writers refuse a tree with no `LEDGER.log`, so a
  command run in the wrong directory does not start a stray ledger (→ **A session works on the tree it was opened in**).

## The claims record

`CLAIMS.md` holds one entry per recorded claim: a global id `C-NNN`, the earned tag, the date, the run and claim id,
the statement, the artifact with its hash, the check record it passed, the referees, and, for claims under the current
schema, the premises. The exact form is [SCHEMAS.md §5](../../SCHEMAS.md#5-claimsmd-entry--appended-by-binledger-claims-run-id-on-the-users-approval).

It is append-only. Three things can happen after an entry is written:

- **A changed truth** is a new claim that supersedes the old one. The old entry stays
  (→ **`CLAIMS.md` is append-only**). [`bin/claim-deps`](../reference/tools/claim-deps.md) lists the live entries that
  depended on a superseded one, by artifact hash and by name, so none is left standing unnoticed
  (→ **Dependencies between ledger entries are read by bytes and by name**).
- **A changed novelty, or an audit finding that leaves the truth as stated,** is a note. A note ends with a fixed line
  saying it is the orchestrator's and was not refereed, and a note claiming the entry's truth is unchanged is refused
  (→ **A changed novelty**, → **A note says whose it is and does not vouch for the entry**).
- **Nothing else.** No entry is edited.

An append is all-or-nothing and refuses a changed artifact, a duplicate, or a supersede target that is not on the
record (→ **`ledger-claims` is all-or-nothing**). An entry cites the run's `check.json` by its generation time, so
before a run with ledgered claims is re-checked the old check record is kept under its own name
(→ **A ledgered run's check record is kept**).

## A run directory

A run is the unit of evidence. Its directory holds:

| file | what it is | written by |
|---|---|---|
| `BRIEF.md`, `HARNESS-NOTE.md`, `input/` | the packet | `bin/new-run` and the orchestrator, before the approval |
| `.role`, `.limits` | the run's role and its enforced caps | `bin/new-run` |
| `scratch/` | the worker's working space | the worker |
| `output/` | the deliverable: `result.md` and `claims.json`, or a referee's `referee.json` | the worker |
| `launch.log` or `launch.jsonl`, `launch.err` | the transcript, moved in after the worker stops | the launcher |
| `usage.json`, `time.log` | CPU, memory and wall time actually used | `bin/limits-exec` |
| `RECORD-EXT.md` | for a Codex or networked run: what it could read, its network, hashes of its downloads | the launcher |
| `check.json`, `check/` | the checker's verdict per claim, and its logs | [`bin/check`](../reference/tools/check.md) |
| `verdict.md` | the verdict table, formal statements beside the English | [`bin/merge`](../reference/tools/merge.md) |

A referee's verdict lives in the referee run's own `output/referee.json`, which names the run and claim it judged; it
counts only for a run `bin/new-run` bound as a referee, in `data/referee-bindings/` (below).
The orchestrator prints a referee's note as written and never summarises it; the operator can open the file directly
(→ **The orchestrator prints a referee's note; never summarises it**).

One more file can appear, recording a decision rather than a result: `.source-run`, naming the run a restatement was
assembled from. Two records that decide an earned tag live outside every run, where no worker can write them:
`data/referee-bindings/<run>.json`, `bin/new-run`'s record of a referee run (its question, its claim, the bytes it was
given), and `data/cross-family-rulings.json`, the user's rulings on whose hold counts for an unknown producer
([SCHEMAS.md §4](../../SCHEMAS.md#4-earned-tag--binmerge-computes-binledger-claims-enforces)).

## The handoff

`HANDOFF.md` is a pointer sheet for the next session: paths, hashes, the status of the cycle's exit criteria, what
this session read, the rulings, a preflight, and the opening prompt for the next session
([RULES.md §7](../../RULES.md#7-standing-rules-that-keep-cycles-convergent)). It holds the current pointer and nothing
else; history lives in the archived copies (→ **`HANDOFF.md` holds the current pointer and nothing else**).

- The hook runs [`bin/handoff-archive`](../reference/tools/handoff-archive.md) before the first call of a session that
  touches the file, and refuses the call if archiving fails, so the version each session starts from is kept; a
  second rewrite within one session is not archived separately
  (→ **`HANDOFF.md` is archived before it is touched**).
- The writer runs the handoff's own preflight, verbatim, before calling it done
  (→ **The writer runs its own handoff preflight**), and every path it names in backticks is checked by
  `bin/verify-data` (→ **Every backticked tree path in a handoff exists**).
- Every handoff carries the opening prompt for the next session and the requirement to carry it
  (→ **The opening prompt is in every handoff**).

## Checks over the whole record

[`bin/verify-data`](../reference/tools/verify-data.md) is the guard that runs first in every `bin/close-run`. It checks
the locked data against its hashes and looks for a copy of any locked file anywhere in runs or problems, under any
name; looks for record files in any run's `input/`; checks a linked formal library against its master list; checks
the handoff's paths; and checks every intake record's name and hashes. A finding stops `bin/close-run`.

The orchestrator's own session transcripts are mirrored into the instance by a hook at the end of each turn, outside
version control.

## Where to look

| question | look in |
|---|---|
| What has this instance established? | `CLAIMS.md` |
| What exactly happened in run N, and when? | `LEDGER.log` (the user), then the run directory |
| Why did a claim earn less than it claimed? | the entry's `Claimed:` line, then the run's `verdict.md` and the referee's `referee.json` |
| What was approved, with which flags? | the `APPROVE` lines on the ledger |
| What did the worker actually see? | the run's `BRIEF.md`, `HARNESS-NOTE.md` and `input/`; the `APPROVE` line carries the digest and flags; the per-file hashes are in the used approval record under `.claude/state/approvals/`, which is not committed |
| Where did an outside idea come from? | `intake/IN-NNN-…/record.md` |
| Where does the work stand? | `HANDOFF.md`, and `handoffs/` for earlier versions |

## What the record does not guarantee

- **The ledger log's integrity rests partly on the user.** Append-only at the file-system level is a step the user
  takes. The hook keeps the orchestrator from reading or naming the ledger by name, which stops an ordinary command,
  not a deliberate one ([RULES.md §6](../../RULES.md#6-approvals--the-gate)).
- **The locked directory is guarded by name and by place, not by permissions.** The hook refuses the orchestrator its
  Read, Grep and Glob, and commands naming it (since `kit-v0.6.6`); since `kit-v0.6.9` it lies outside the tree, so no
  search from the instance walks it. A command that builds its path some other way is the deliberate forgery the kit
  does not claim to stop; the rule that the orchestrator never reads it, the tools refusing to copy it into packets and
  `bin/verify-data` finding copies by hash stand behind that (→ **The orchestrator never reads answer keys or label
  maps**).
- **A note is the orchestrator's word.** It is labelled as unrefereed for exactly that reason.

## Related

- [The trust model](trust-model.md): how an entry's tag is earned.
- [Packets and outside input](packets-and-outside-input.md): what of the record a worker may see.
- [Glossary](../reference/glossary.md).
