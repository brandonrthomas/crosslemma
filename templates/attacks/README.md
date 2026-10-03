# Attack: ⟨slug⟩ — ⟨the question, as one line⟩

Operator ruling ⟨date, time⟩: ⟨the words that opened this attack⟩. Written ⟨date⟩ before any run. Every judgement
in this file is `[HEURISTIC]` unless it points at a claim id. The operator may open an attack within a budget the user
has set; the budget (K3), and setting or loosening the kill criteria or the scope, stay the user's. Tightening them,
or parking or closing the attack, narrows it, and the operator may do that (`RULES.md` §4).

## Idea

⟨What is being tried, precisely enough that two solvers would attempt the same thing. Every input the solver will
receive, by name. Every condition or definition the attack introduces, written out, with its source lines if it
is transcribed from somewhere — the transcription is the orchestrator's and is the first thing to certify
(→ `LESSONS.md` "Set-up audit of a brief").⟩

**The question put to the solver, neutrally:** ⟨stated so that either answer is a result; the brief must not hint
which answer is expected.⟩

## Why

- ⟨What a positive answer buys; what a negative answer closes.⟩
- ⟨Why now, and why this before the alternatives.⟩
- ⟨Cost, in runs and in what kind of work.⟩

## Why not

- ⟨The expected outcome, honestly, and how surprising each answer would be.⟩
- ⟨What the attack is *not* a statement about — the sentence every claim must carry so it is not read as more.⟩
- ⟨The silent links: the transcription, the assumed equivalences, the theorems taken as stated.⟩
- ⟨What is left out on purpose, so that it can be named as left out in every claim.⟩

## Milestones

- **M0 Fidelity.** ⟨What the solver must first show about the inputs it was given: that the written-out list is
  what the cited lines say; refereed with the source excerpts as deps. The orchestrator wrote it, so the
  orchestrator does not certify it.⟩
- **M1** `[VERIFIED]`. ⟨An exact-arithmetic script with a printed and asserted count, its mutations that must
  fail, and its controls: a known object re-found, a known failing case that fails.⟩
- **M2** `[PROVED]`. ⟨The written argument, or a formal declaration whose statement is the claim.⟩
- **M3 (optional).** ⟨…⟩

## Exit criteria (all of them)

1. ⟨Mechanical: "M1: `bin/check --mutate` pass; every declared mutation fails as expected; the controls are in
   the script."⟩
2. ⟨"M2: `certify` and `hypotheses` referees both hold; the English states … and the sentence on what is not
   asserted."⟩
3. ⟨"Any script claim whose English names another file lists that file in `deps`."⟩
4. User gate; ledger.

## KILL CRITERIA (written before any run; set or loosened only by the user, tightened by the operator)

- **K1.** ⟨A fidelity difference one rewrite does not close: stop; record as `[GAP]`; nothing built on it is
  ledgered above `[GAP]`.⟩
- **K2.** ⟨A referee gap on the proof that one repair run does not close: stop; ledger what was earned.⟩
- **K3.** Budget: **⟨N⟩** solver runs. More needs a new user ruling.
- **K4.** ⟨Any proposal to widen the question is a new attack with its own README. It is not pursued here.⟩
- ⟨The other answer is not a kill. It is the other answer: stop and bring it to the operator.⟩

## The tests of `PROBLEM.md` §5

⟨Which apply and how; or "not applicable as written, because …".⟩

## Status

**Current (⟨date⟩, end of `⟨session⟩`): ⟨PROPOSED / OPEN / CLOSED / PARKED⟩.** ⟨Claim ids earned, by tag; what
the record now says, in one sentence; what is not certified, by design; the consequence for the workspace's
subject; how much of the budget was used.⟩

History, oldest first:

⟨date⟩: proposed; README written; no run.
