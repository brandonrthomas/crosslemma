# Approving

This guide helps you, the user, approve a launch, a claims append or a note: what you are shown first, the two ways
to give the approval, what each looks like, and how to approve several at once.

Every launch and every append to `CLAIMS.md` needs your approval, and the tools refuse without one
([RULES.md §6](../../RULES.md#6-approvals--the-gate); → **Every launch and every ledger append consumes a byte-bound**).
An approval binds the exact bytes you were shown, the claim ids and the launch flags. It is single-use and lasts 30
minutes. For why it works this way, see [the approval gate](../concepts/approval-gate.md).

## What can be approved

| Kind | Shown by | Approved as | Used by |
|---|---|---|---|
| a launch of one or more runs | `bin/manifest RUN … -- <flags>` | `bin/approve RUN … -- <flags>` | [`bin/run-external`](../reference/tools/run-external.md) |
| an append of claims to `CLAIMS.md` | `bin/manifest --ledger RUN c1 …` | `bin/approve --ledger RUN c1 …` | [`bin/ledger-claims`](../reference/tools/ledger-claims.md) |
| one note on an entry | `bin/manifest --annotate C-NNN "text"` | `bin/approve --annotate C-NNN "text"` | [`bin/annotate-claim`](../reference/tools/annotate-claim.md) |
| several notes | `bin/manifest --annotate-batch FILE` | `bin/approve --annotate-batch FILE` | `bin/annotate-claim --batch FILE` |
| a headless [`bin/astra-session`](../reference/tools/astra-session.md) | `bin/manifest --session -- <arguments>` | `bin/approve --session -- <arguments>` | `bin/astra-session` |

[`bin/manifest`](../reference/tools/manifest.md) takes the same arguments as [`bin/approve`](../reference/tools/approve.md)
and prints the same thing, but approves nothing.

## 1. The orchestrator shows you the manifest

Before asking, the orchestrator runs [`bin/lint-brief`](../reference/tools/lint-brief.md) on a launch and clears its
errors, then shows you the manifest (→ **`bin/lint-brief` before `bin/manifest`**). A launch manifest looks like this
(abbreviated here: the tool prints every sha256 and the digest in full, 64 hex characters each):

```text
== launch 001-context-canary
4b4bab2f…  57  workspace-1/runs/001-context-canary/.limits
7e4fa2eb…   6  workspace-1/runs/001-context-canary/.role
bf503779…  4561  workspace-1/runs/001-context-canary/BRIEF.md
digest: 2296c6b29352…   (3 entries)
flags : --effort low --max-turns 40 --model opus --via anthropic
(read-only: nothing approved)
```

Each line is a file's sha256, size and path: every file the worker will see. The **digest** covers the kind, the run, the
ids and every file's hash. The **flags** are bound separately and compared as a set, so their order does not matter;
`--model` is always among them (→ **A launch approval binds its flags**). `--dry-run` and `--detach` are never part of an
approval.

Read what you are approving. You can read any file directly, or ask for the manifest with `--show`, which also prints
every file's contents. For a claims append, read the verdict table first; the manifest binds `claims.json`, `check.json`,
`verdict.md`, every live `referee.json` of those ids with its binding, the cross-family rulings when there are any,
and `CLAIMS.md`.

## 2a. Approve at your terminal

Run the approval command yourself. In the orchestrator's Claude Code session, prefix it with `!`, which runs it in your
shell without passing through the hook; that is what makes the approval yours
(→ **`!` commands do not pass through the hook**). The orchestrator gives you the command as text, alone in a code block;
it never runs this terminal command itself. With full paths it works from any directory:

```sh
! ~/kits/my-problem/bin/approve 001-context-canary -- --via anthropic --model opus --effort low --max-turns 40
```

```sh
! ~/kits/my-problem/bin/approve --ledger 004-first-attack c1 c3
```

Adding `--digest` with the first twelve characters of the manifest's digest makes the tool refuse unless the bytes are
still the ones the manifest showed.

You see the same printout as the manifest, then `APPROVED until <UTC time>, single use.` The tool writes the approval
record and an `APPROVE` line in the ledger. If it replaces an unused, different approval for the same run, it says so:
only one is kept.

This route works in every permission mode, and it is the only route for the packet lists: `! bin/packet-block …` and
`! bin/packet-except …` are always your act ([RULES.md §8](../../RULES.md#8-the-record)).

## 2b. Approve with a tap

In permission mode **default** or **auto**, the orchestrator may offer the approval for your tap instead. It issues one
plain call from the instance's root, carrying the digest from the manifest you were shown and, for a launch, the flags:
`bin/approve 001-context-canary --digest 2296c6b29352 -- --via anthropic --model opus --effort low --max-turns 40`.

The hook holds that call: it runs only if you allow it. The hook computes a permission prompt from the bytes on disk, not
from anything the orchestrator wrote, and shows it to you:

```text
USER APPROVAL (single use, 30 min): launch 001-context-canary, digest 2296c6b29352, 3 entries,
flags --effort low --max-turns 40 --model opus --via anthropic. Allow = you approve exactly these bytes.
Never choose "don't ask again".
```

Compare the digest, the entry count and the flags with the manifest. **Allow** (once) is the approval. If anything
differs, deny it.

**Never choose "don't ask again".** It writes an allow rule into your settings, which would turn every later approval into
a silent one; while such a rule exists the hook refuses to offer any tap and names the rule for you to remove
(→ **The tap route needs `--digest`**).

The hook also refuses to offer a tap in any other permission mode, for a call without `--digest` (a `--session` call
needs none), for a call made neither from the project root nor by the tool's absolute path inside it, for anything but one
plain command, or when the tool itself would refuse. Each refusal says what it was and spends nothing
([hook refusals](../reference/hook-refusals.md#ask_user_to_approve)). Then use your terminal.

## 3. What happens after

The launch or the append consumes the approval. Until then:

- **Nothing the approval binds may change.** One edited byte, a different flag or a different set of ids voids it, and the
  tool refuses with "no user approval for these hashes" (for a run released from a queue, "no queued approval for
  these hashes"), naming the file or flag that differs. That refusal is the stop: a new manifest, a new approval
  (→ **The manifest is shown first**). The same text is in [RULES.md §6](../../RULES.md#6-approvals--the-gate).
- **Nothing the packet scan reads should change either**, and files that discuss a pending packet describe it rather than
  quote it (→ **Between an approval and its launch, no scanned file changes**).
- **It expires after 30 minutes.** A run approved in one session and launched in another is approved again in the
  launching session, against the bytes as they then are.

Every check the launcher can make without the approval (the brief's turn cap, the harness note, the packet scan, an
earlier launch, the sandbox, settings and key) runs first, so those refusals spend nothing.

## Several at once

**A batch.** Name several runs in one approval: one consent for exactly those runs, all with the same flags:

```sh
! ~/kits/my-problem/bin/approve 007-ref-004-c1-cert 008-ref-004-c1-hyp -- --via anthropic --model opus --effort high
```

A **batch tap** takes one digest per run, comma-separated, in the order of the runs, e.g.
`--digest 1a2b3c4d5e6f,7a8b9c0d1e2f`. One mismatch refuses the whole call (→ **Batch tap**). The orchestrator tells you how
many runs one tap covers.

**A queue.** Runs approved together may launch as a queue:

```sh
bin/run-external --queue 007-ref-004-c1-cert 008-ref-004-c1-hyp --via anthropic --model opus --effort high --detach
```

The queue checks every run first, then uses every approval at its start, and releases each run, one at a time, only with
the approved flags and unchanged bytes, so a later approval cannot expire while an earlier run works
(→ **A queue for runs approved together**). It stops at a run that ended on the plan's usage limit or the provider's
capacity refusal; the runs it did not release need new approvals (→ **A queue stops at the plan's usage limit**). While a
queue releases runs, nothing creates or removes files in its tree: no suites, no commits, no file moves
(→ **Nothing creates or removes files in a tree while its queue releases runs**).

**Several claims** of one run are one `--ledger` approval naming every id. **Several notes** are one `--annotate-batch FILE`
approval: `FILE` is a JSON list of `{"id": "C-NNN", "text": "…"}` inside the tree, every note is printed in full, and
`bin/annotate-claim --batch FILE` appends all of them or none (→ **One approval for several notes**).

## What your words cover

An approval covers exactly what the approval tool named. Your words in the conversation cover only what they say: "do all
of X" covers X and nothing beside it, a go attached to another instruction covers that instruction only, and silence is
not approval ([RULES.md §6, what consent covers](../../RULES.md#what-consent-covers); → **Batch consent**).

## Related

- [A full cycle](a-full-cycle.md): where each approval falls in the cycle.
- [The approval gate](../concepts/approval-gate.md): why, and what it does not stop.
- [Exit codes](../reference/exit-codes.md): a refusal for want of an approval exits 3.
