# Flow — one page

`RULES.md` is the law; this is how a cycle actually runs. Terms are `RULES.md` "Words": **user**, **operator agent**, **operator**, **orchestrator**, **worker**.

## The cycle

```
   user names the problem or attack
            │
   0  orchestrator writes the brief ──────────────────────────► GATE 1  (user)
            │                                   lint-brief → manifest → approval → launch
   1  solver run            (worker, sandboxed, clean-room)
   2  checker               (script: artifacts run, axioms audited, form validated)
   3  referee run(s)        (worker, fresh; two per [PROVED] claim, one per question, + a cross-family certify;
                            one per script claim, from the other family)
   4  verdict table         (claim | tag | check | referee | earned) ─► GATE 2  (user)
            │                                   manifest → approval → append
   5  approved claims appended at the tag they EARNED, not the tag claimed
   6  exit criteria met → close · not met → one more solver run · else DROPPED
            │
   handoff (written, preflighted by its writer, archived, committed) → fresh session
```

Steps 2 and 4 are one command (`bin/close-run`), which launches nothing and appends nothing: it prints the verdict table, the
referee line for every `[PROVED]` claim still lacking a `holds`, and the exact approval and append lines for step 5.

## The two gates

Both are the same mechanism, and neither is a conversation:

1. The orchestrator shows a **manifest** — path, size and hash of every file the worker will see, one digest, the exact flags.
2. The **user** approves those bytes, at the terminal or by a prompt the hook words from the bytes themselves.
3. The tool consumes the approval. Single-use, 30 minutes. Any edited byte, changed flag or different claim id voids it, and the
   refusal is the stop.

A misread go therefore ends in a refusal rather than a launch. That is the whole point of the gate: prose rules did not stop it.

## Roles, in one line each

- **Orchestrator** — writes briefs, runs the scripts, shows tables and paths, hands off. Never certifies its own work, never
  reads answer keys, never summarizes a referee's note, never launches or appends without an approval.
- **Solver** — one run directory, no prior attempts, no expected answer. Its files under `output/` are the whole deliverable;
  there is no report channel.
- **Checker** — a script. Runs each artifact in the same sandbox the worker had, audits axioms, validates form. It does not argue.
- **Referee** — fresh context, one claim, its artifact and declared deps, the problem statement. Two per `[PROVED]` claim:
  `certify` ("does the artifact certify the statement at this tag?") and `hypotheses` ("does the English carry every restriction
  the artifact needs?"). One per `[VERIFIED]` or `[NUMERIC]` claim: `sentence` ("does the English say exactly what the script
  asserts, on the stated range?"). Decorrelation of the pair comes from the question, not from the model; beside it, a `certify`
  read from the other model family than the producer's, and a script claim's `sentence` read from the other family too. Any
  `gap` makes the claim `[GAP]`.
- **User** — sees every file directly, approves bytes, and rules on everything on the user's list (`RULES.md` §4): what
  could widen what a worker sees, what a claim asserts, what the ledger holds or what the gate lets through.
- **Operator** — the user, or an operator agent the user designates: sets the purpose within the declared session type,
  rules on procedural deviations, decides when an outside check is worth it, receives the reports.

## Outside steps — called, not wired in

None is required; none is an exit condition. Each is a *packet*: self-contained, evidence both ways, the interested party's view
last and labelled. If the question cannot be written down that way, it is not ready to hand to anyone.

| step | reach for it when |
|---|---|
| **Outside-reader packet** | a referee has gapped the *same sentence* twice. The author has failed twice; a third rewrite by the author is the pattern this replaces. Not after a first gap. |
| **Set-up audit of a brief** | the brief carries a new relaxation, a new list of conditions, or a new transcription of a source — anything where a wrong reading would make every claim of the run about the wrong object. Not for a brief reusing a list already certified. |
| **Handoff audit** | the session changed method, or committed record text the operator had not read first. Useful, not routine: the operator calls it. |
| **Calibration ladder** | before a model's verdicts count in a role it has not been measured in, and after any change to a referee brief. Measures recovery, catch and false-positive rates — as coverage, not as recall. |
| **Canary** | after any change to the hook, settings, an agent definition, a harness note, or a route; and once per route an instance enables, before real work. |

## An analyst, and the operator agent

Nothing in the method depends on an analyst. The user may keep an ongoing one at their own discretion, for design
questions, second readings and "what did this miss?", and may designate it the **operator agent** (`RULES.md` "Words"):
it then gives direction within the operator's list in `RULES.md` §4 (ordering work inside the session type the user
declared, procedural deviations that loosen nothing, the choice among allowed outside checks) and never does anything
on the user's list, approvals first among them.

What it never becomes, operator agent or not: a step in the cycle, a gate, or a source of claims. Anything an analyst
produces is **uncertified** until it is checked against the record point by point, and it reaches the record only the way
anything else does — through a run, a claim, and a referee. What it hands in is outside input: an intake record comes
first (`RULES.md` "Outside input"), and classing it as anything that can enter a packet or a claim is the user's.

Session prompts, forms rather than rules: `templates/analyst-prompt.md` for the analyst, `templates/orchestrator-prompt.md`
for an instance's orchestrator. Each ends with an appendix for a channel over Clatter between the two, which the user
opens and closes (`RULES.md` §4, item 8), with its minimum conditions. P7 is the charter for running an operator agent
unattended; it is not built.

## What a session looks like from the outside

A fresh orchestrator per cycle. It reads the rules and the handoff, runs the handoff's preflight verbatim one command at a time,
and stops. It says what it is about to read before reading it. It writes the next brief from the record — not from the previous
orchestrator's live reading of the results — and stops at the gate. At the end it closes the cycle, records findings and
candidate directions with their evidence, writes the handoff, runs that handoff's own preflight, and says that the next cycle
starts in a fresh session. It never offers to launch that cycle itself.

Costs are stated before they are spent. Whatever the operator must see is in the final message of the turn.
