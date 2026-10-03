# Run ⟨NNN-slug⟩: audit of a solver run's set-up, before it is launched

Your run directory is ⟨absolute run directory⟩
Read only what is in it. Work alone. You have no network and need none.

## Who you are here
An outside party with no stake. A research workspace is run by an AI "orchestrator" session under a human
user. Its first rule: whoever produced the work does not get to certify it. The orchestrator has set up a
solver run (run ⟨NNN⟩) and wrote ⟨its texts: a list of conditions written out from sources / a transcription /
a relaxation⟩ and the run's brief. Before the run is launched the user wants both checked by someone who did
not write them. A human reads your findings whole and decides; the orchestrator then corrects the texts. The
solver has not run; nothing in your packet is a result.

**You are not asked whether the sources' theorems are true**, and you are not asked to answer the solver's
question. If you happen to see the answer, do not put it in your findings unless a finding cannot be stated
without it; say then that you did.

## Inputs
- `input/⟨text-under-audit⟩.md`: the text under audit (1): ⟨what it is⟩.
- `input/run⟨NNN⟩-brief-copy.md`: the text under audit (2): a byte copy of the run's brief, under another name
  because a run input may not carry that file's name. ⟨Which parts are written by a tool and the same in every
  solver run; the rest is the orchestrator's.⟩
- ⟨`input/⟨source⟩.md`, …: the sources, whole, byte copies; the line numbers in the text under audit refer to
  them. Their licence, if held.⟩
- `input/PROBLEM.md`: the problem file, which the solver also receives.
- `input/attack-README.md`: the orchestrator's plan for this line of work (idea, milestones, exit and kill
  criteria). The solver does **not** receive it.
The solver receives exactly: ⟨the list⟩, and a form validator script that is not in your packet.

## What to check
1. **Fidelity.** For each condition ⟨T0 … Tn⟩ and each bridge: is it equivalent to what the cited lines of the
   sources state (taking the sources' statements as stated)? List every difference in either direction (demands
   more; demands less), every wrong line reference or misquotation, and anything the cited statements presuppose
   that the written form does not carry.
2. **Neutrality.** Does the brief, the text under audit or `PROBLEM.md` tell or hint which answer is expected?
   Quote the words.
3. **Controls and mutations.** Are the controls and the required mutations sound and sufficient to show that a
   checker script is not vacuous? Is each control computable from what the solver is given?
4. **Well-posedness.** Is the question well-posed as written? Is any definition ambiguous? Would two careful
   readers implement it identically?
5. **The referee arrangement and the exit criteria.** Anything that would let a claim be recorded whose statement
   a referee cannot check from the files it will see.
6. **What is missing, and what you would change before launch.**

Do not audit the prose style or the choice of problem. If something is outside what your inputs let you check,
say "not checkable from the packet" rather than guess.

## Output
`output/findings.md`, at most 150 lines. First a table, one row per finding, most serious first:

`| id | type | where (file, § or line, a few quoted words) | evidence (file and line) | what is wrong, ≤ 2 lines | suggested wording or fix, ≤ 2 lines |`

`type` is exactly one of: `unfaithful-stronger`, `unfaithful-weaker`, `wrong-reference`, `ambiguous`,
`leaks-answer`, `unsound-control`, `uncheckable-by-referee`, `missing`, `minor`.
Then "Checked and found correct": a short list of what you verified (so that silence can be told from
agreement). Then "Not checkable from the packet". Then one line:
`VERDICT: launch as is | launch after the fixes above | do not launch`.
Write the file as you go (append with `cat >> output/findings.md <<'EOF' … EOF`), so that a cut-off run still
leaves its findings. You may use Python for searching the files and for exact arithmetic.
Then run `ledger "⟨NNN⟩ done"`.
