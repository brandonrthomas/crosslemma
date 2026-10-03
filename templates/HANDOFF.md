# Handoff — @NAME@ (written ⟨date, time⟩; the commit that holds this file is the authority on time. ⟨One sentence: what this session did and did not do — "NO MATHEMATICS, NO CLAIM" if so. What is in flight: nothing, or the run by name.⟩ Nothing is to be briefed or launched on the strength of this file alone.)

## CURRENT POINTER — this whole file. No historical tail: read it whole, with the Read tool, never by reference.

Written by `⟨session⟩`. The pointer this one replaces is archived by the hook under `handoffs/`.

### 0. Preflight — verify, do not inherit. One command per Bash call, in a session opened in this directory.
Every command names this tree by its absolute path except the ledger line, which the hook allows only as a plain
`git diff`; `pwd` comes first so that one relative command is known to run here.
```
pwd                                   # expected: @ROOT@ (else stop: this session is not at this tree's root)
git -C @ROOT@ log --oneline -1        # expected: the commit that holds this file
git -C @ROOT@ status --short          # expected: ` M LEDGER.log` and nothing else (plus one `?? handoffs/<date>-<sha>-<session>.md`
                                      #   if a Bash command of yours has named HANDOFF.md: the archive hook, byte-identical to HEAD's copy)
git diff --numstat LEDGER.log         # expected: N insertions, 0 deletions. ALONE: the hook denies any compound command naming the ledger
@ROOT@/bin/verify-data                # expected: root: @ROOT@, then locked files ⟨N⟩; runs scanned ⟨N⟩; ⟨formal library: none linked | lean files N (digest …)⟩; findings 0
pgrep -fa 'claude -p' | grep '[/]@NAME@/workspace-'   # expected: nothing (no worker of this tree in flight; the [/] keeps the
                                      #   check's own shell wrapper from matching itself; other trees' workers do not count)
pgrep -fa 'codex exec' | grep '[/]@NAME@/workspace-'  # expected: nothing (no Codex worker of this tree in flight)
/usr/bin/python3 @ROOT@/tests/test_gate.py       # expected: Ran 32 tests … OK   (nothing is launched)
/usr/bin/python3 @ROOT@/tests/test_hook_gate.py  # expected: Ran 33 tests … OK
df -h @ROOT@                          # read it: this file records no figure; the session's reading is the truth; a run needs room
```
`LEDGER.log` is always modified (the hook appends on every tool call, and it is append-only); what must hold is
that its diff is append-only. Commit it at your own handoff. If anything else differs, stop and tell the user.
**Work on this tree only from a session opened in it** (a `cd` that leaves a session's project directory is reset;
→ `LESSONS.md` "A session works on the tree it was opened in"). **Never put a `cd` in a compound Bash command.**
**Never name `LEDGER.log` inside a compound command.** Every path this file names in backticks exists;
`bin/verify-data` checks it.

### 1. Read, in these tiers, then stop and talk to the operator
**Always, whole, in this order:**
1. `RULES.md` in full; `FLOW.md`.
2. This file, whole, with the Read tool; then run §0's preflight (the order of §7's opening prompt).
3. `SCHEMAS.md`.
4. `problems/@SLUG@/PROBLEM.md`.

**As an index only:**
5. `CLAIMS.md` by its header lines (⟨N⟩ entries; superseded `[GAP]`s: ⟨ids⟩; notes: ⟨ids⟩); count entries and notes with
   `grep`, and they must match. ⟨"No live gap." or the live gaps, by id.⟩

**Only after the operator sets the session's purpose, by id or path, the parts the chosen work touches:**
6. The entries and notes of `CLAIMS.md` it names; the intake records under `intake/`.
7. ⟨the attack READMEs that are live, by path⟩; `problems/@SLUG@/prior-art.md`.

Then §3. Stop at every gate.

### 2. What this session did (commits `⟨sha⟩`, …)
⟨Numbered items. Each: what was done, on whose word (the user's, or the operator agent's marked as its own, quoted with the time), what it produced
by path, what was launched and approved, what was appended. A worker's report is a report, not a result, until a
claim id stands behind it.⟩

### 3. Where things stand, and what comes next — each item put to the operator before it is taken (to the user if it is on the user's list, `RULES.md` §4)
- ⟨The state of the record in one paragraph: which target statements are open, which attacks are open, closed or
  parked, which claims are live.⟩
- **Agenda, as the record leaves it:** ⟨numbered; each with its first concrete step and the ruling it needs.⟩
- ⟨What is deliberately in no claim, and by whose decision.⟩

### 4. Rulings of this session (⟨timezone⟩; times approximate to the minute), in force — the user's, and the operator agent's marked as its own; the words quoted
- ⟨time⟩ "⟨words⟩": ⟨what it answered⟩.
- Approvals: ⟨each run and append, how it was approved (terminal, tap, batch), with the digest⟩. Network: ⟨which
  runs, by whose approval of `--network`⟩.

### 5. Standing rules — carried; `RULES.md` is the authority
Every launch and every `CLAIMS.md` append consumes a user approval bound to bytes, ids and flags
(`bin/manifest` shown first, then the user's act, then the tool). The hook refuses any Bash command naming the
approval tool except the one plain `--digest` call, anything naming the approvals directory, a bare headless launch,
the messaging and workflow tools, any Agent call of a worker type, any edit of the packet rules or their exceptions
(`data/packet-rules.json`, `data/packet-exceptions.json`) and any command naming them or `bin/packet-block` /
`bin/packet-except` except a plain git add / commit / status / diff, and anything naming `LEDGER.log` except a plain
`git add` / `commit` / `status` / `diff --numstat`, each alone. Commit messages go in a file (`git commit -F`).
Commit by explicit paths. Never assume a question is a command, and never read a permission more widely than its
words. Silence is not approval. Deviations before choices. Print a referee's note; never summarize it.
**Whatever the operator must see goes in the final message of a turn.**
**Practice that worked this session (habits, not rulings):**
- ⟨…⟩

### 6. Open, for the operator (the user's list marked as the user's)
- ⟨Residuals, each disclosed: what nobody has certified; what an outside model reported that is uncertified; what
  the sandbox cannot hide; what waits on the user's act.⟩

### 7. Opening prompt for the next session — REQUIRED IN EVERY HANDOFF
**Every handoff must contain this section and must repeat this requirement, so that it propagates without anyone
remembering it. The outgoing orchestrator's last message prints the block for the user.** The user starts
the next session in this directory by pasting it as plain text (never by file reference).
```
You are a fresh orchestrator for @ROOT@. ⟨Two or three sentences of state: what is finished, what is open,
what is in flight (nothing), what CLAIMS.md holds.⟩ Read RULES.md in full, then HANDOFF.md in full with the Read
tool, and run its section 0 preflight verbatim, one command per call, from the project root; if anything
differs, stop and tell me. Then read what HANDOFF.md section 1 lists. Then stop and ask me what this session is
for; HANDOFF.md section 3 lists what the record leaves open. Tell me what you are about to read before you read
it, and draft nothing until I say so. Launch nothing, brief nothing and create no run until I say so. You have
no network; a worker has network only in a run I approve with --network. Every launch and every CLAIMS.md
append goes through the approval gate: you show bin/manifest, I approve, then you launch. Give me each approval
command alone in its own code block, with full paths. Never go near bin/approve except the one plain --digest
call made for my tap. Never summarize a referee's note to me: print it. Never assume a question is a command,
and never read a permission more widely than its words.
```

### 8. Disclosure for this session
**Read:** ⟨every file, by path; "in parts" with line ranges; what was read outside the tree.⟩ **Not read:**
⟨`data/locked/`, any referee note, the ledger, …⟩. **Launched:** ⟨…⟩. **Appended to `CLAIMS.md`:** ⟨…⟩.
**Network by the orchestrator:** ⟨none, or each use with the user's permission for it⟩. **What left this
machine:** ⟨to which provider, what⟩. **Orchestrator errors and deviations this session:** ⟨numbered; none caught
by an artifact unless said so⟩. The user's messages and the consent chronology exist only in the session
transcript.
