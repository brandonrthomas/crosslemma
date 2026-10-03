# Run ⟨NNN-slug⟩: audit of a handoff document, before the session that wrote it ends

Your run directory is ⟨absolute run directory⟩
Read only what is under `input/`. Work alone. You have no network and need none.

## Who you are here
An outside party with no stake. A research workspace is run by an AI "orchestrator" session under a human
user. Each session ends by writing a handoff: the only thing the next session inherits. The orchestrator wrote
the handoff you are auditing, so by the workspace's first rule ("whoever produced the work does not get to
certify it") it may not certify it. You are asked for a **mechanical fidelity check, not an opinion** on the
design or the plan. A human reads your findings whole and decides; the orchestrator then corrects the handoff.

⟨Two or three sentences on the session: what it did, in what commits, whether it made any claim.⟩ **The handoff
you audit is the file committed as `⟨sha⟩`**; the orchestrator will amend it after your findings, with the
user, and commit again. **The message file holds the orchestrator's texts but not its tool calls**, so what
it says it read, ran or found is checkable only against the record files.

## Inputs
- `input/HANDOFF-under-audit.md`: the document. Its §0 describes the state it expects after the final commit.
- `input/USER-MESSAGES.md`: everything the user sent in the session, verbatim, each item preceded by
  every text the orchestrator wrote since the previous item. **Only the USER blocks are evidence of what the
  user ruled.** Terminal blocks are commands the user ran (approvals are among them). The ORCHESTRATOR
  blocks are the interested party's words, there so that a "go" can be understood.
- `input/record/`: `previous-HANDOFF.md`; `rules-copy.md` (the rules as they stand, under another name because a
  run input may not carry a record file's name); `SCHEMAS.md`; `diffs/<commit>.diff` and `.stat.txt` for the
  session's commits; `git-and-tree.txt` (git log with files, run directories, `git status`, the data check, at
  packet time; its first line says what it leaves out); `tests-output.txt` (the suites at packet time); ⟨any
  extracts the orchestrator made by script, each named as such⟩.

## What to check
1. **The user's rulings** (handoff §4, and every sentence elsewhere that says the user decided, agreed,
   asked, allowed, approved, ruled, chose or confirmed something). For each, find the user's own words.
   Report any ruling **wider than the words**, narrower, misdated by more than a few minutes, put in the
   user's mouth when it was the orchestrator's suggestion left unanswered, or missing. The rules: "never
   assume a question is a command, and never read a permission more widely than its words"; "silence is not
   approval". ⟨Point at the messages that need particular attention, by number.⟩
2. **Pointers.** Commit ids, run numbers and names, test counts, file paths, times, hashes: does the target say
   what the handoff says? Check each against `input/record/`.
3. **Status language.** Anything stated as established that the record shows is only the orchestrator's or a
   worker's unverified statement, or that the packet cannot show. Whether the handoff's descriptions of what the
   tools do match the diffs: a description wider than the code is `overstated-status`. Do not review the code
   for bugs; only check the handoff's sentences against it.
4. **The error list and the disclosure.** From the messages, is the error list complete? List errors,
   corrections by the user, deviations from what the orchestrator had said it would do, reversals, or things
   done before the user had answered, that are visible in the messages and absent from it. Is anything in
   "read", "what left this machine", "launched", "network", or the commits line understated or missing?
5. **What a fresh session would get wrong.** Reading only the handoff: an instruction that could be taken as
   permission to launch, brief, create, read or fetch something without asking; an agenda item whose first step
   is unclear; a contradiction between sections, or with the rules. The opening prompt is part of this. Any
   "practice that worked" line that reads as a rule the user made when it is the orchestrator's habit.
6. **The preflight block** (§0): is every expected value consistent with `git-and-tree.txt` and
   `tests-output.txt`, given that the handoff will be amended and committed once more after you finish?

Do not audit the mathematics, the design choices, the code's correctness or the prose style. If something is
outside what your inputs let you check, say "not checkable from the packet" rather than guess.

## Output
`output/findings.md`, at most 150 lines. First a table, one row per finding, most serious first:

`| id | type | where in the handoff (§ and a few quoted words) | evidence (file, and message number or line) | what is wrong, ≤ 2 lines | suggested wording or fix, ≤ 2 lines |`

`type` is exactly one of: `wider-than-words`, `narrower-than-words`, `not-the-users-ruling`, `missing`,
`wrong-pointer`, `overstated-status`, `error-list-gap`, `unsafe-for-next-session`, `inconsistent`, `minor`.
Then "Checked and found correct". Then "Not checkable from the packet". Then one line:
`VERDICT: hand off as is | hand off after the fixes above | do not hand off`.
Write the file as you go (append with `cat >> output/findings.md <<'EOF' … EOF`), so that a cut-off run still
leaves its findings. Your final message is the report, the same text as the file.
