# Roles

This page answers: who does what in an instance (the user, the orchestrator, the workers, the checker, an
analyst), and what each one never does?

## A fixed set of roles, and the rest on demand

[RULES.md §4](../../RULES.md#4-roles--three-plus-ad-hoc) keeps a short, fixed list of roles: its table names the
orchestrator, the solver, the checker, the referee and the user, and gives for each what it gets, what it emits
and what it never does. The checker is a script, not a model. This page explains why the lines fall where they do.

Everything else (a reconciler, an outside reader, an auditor) is called for one stuck thing and then put down. A role
that runs every cycle stops being a check and becomes a layer, and layers need readers who then need adjudicating
(→ **Three roles; anything else ad hoc**).

| who | is | sees | produces |
|---|---|---|---|
| user | a person | every file, directly | rulings and approvals (the user's list, [RULES.md §4](../../RULES.md#4-roles--three-plus-ad-hoc)) |
| operator agent | an agent the user designates (in practice, the analyst) | what the user gives it, never the never-read files | direction within the operator's list |
| orchestrator | a model session in the instance | everything except the ledger log's contents, the locked data and the approval records | briefs, run directories, verdict tables, handoffs; never the ledger log by hand, the referee bindings (`bin/new-run` writes them) or the cross-family rulings (the user's) |
| solver | a sandboxed worker | its packet: the problem, its brief, its inputs | `output/result.md` and `output/claims.json` |
| referee | a sandboxed worker, fresh | one claim, its artifact and declared deps, the problem | `output/referee.json`: one verdict, one pointer, three lines at most |
| evaluator | a sandboxed worker | the locked keys it scores against | scores only |
| checker | a script | the claims and their artifacts | `check.json`: pass, fail or n/a per claim |

Terms are as in the [glossary](../reference/glossary.md).

## The user

The user is the person who runs the instance. Every launch and every append to the claims record is their act,
bound to bytes they were shown (see [the approval gate](approval-gate.md)). They rule on deviations, class outside
input, decide when an outside check is worth calling, and read anything directly, the ledger and a referee's note
included.

The rules use three terms ([RULES.md](../../RULES.md#rules), "Words"): the **user**, the human being; the **operator
agent**, an agent the user designates to act as operator (in practice, the analyst), which may give direction not
requiring the user's approval; and the **operator**, either of them. Every approval stays the user's. What is whose
follows one test: anything that could widen what a worker sees, what a claim asserts, what the ledger holds or what the
gate lets through is the user's; ordering, reading and reporting work inside those bounds may be the operator's. The
two lists, and what no agent reads, are in [RULES.md §4](../../RULES.md#4-roles--three-plus-ad-hoc). P7, the charter
for running an operator agent unattended, is not built; the rule that approvals are the user's would change only by
the user's ruling, amending that line.

Some acts belong to the user alone, and the hook refuses them to the orchestrator: writing approvals, and changing
what no packet may carry (`! bin/packet-block`, `! bin/packet-except`).

## The orchestrator

The orchestrator is the session doing the work. It writes briefs, makes run directories, runs the scripts, shows the
operator tables and paths, and writes the handoff. It is unrestricted apart from the approval gate, and every call it
makes is logged ([RULES.md §9](../../RULES.md#9-the-sandbox--enforced-not-convention)).

What it never does, and why:

- **Certify its own work.** It is an interested party in every claim it briefed for
  (→ **Whoever produced the work does not get to certify it**).
- **Read answer keys or control label maps.** A blinded control stops being blind the moment the orchestrator knows
  the labels (→ **The orchestrator never reads answer keys or label maps**). Nothing in the hook blocks this; the rule
  is kept by practice, and copies are found by hash (see [the record](the-record.md)).
- **Summarise a referee's note.** It prints the note and says where the pointer leads; its paraphrase would replace
  the verdict with the interested party's reading (→ **The orchestrator prints a referee's note; never summarises it**).
- **Launch or append without an approval.** The tools refuse it (→ **Every launch and every ledger append consumes a
  byte-bound**).
- **Change the method in a working session.** Tools, hook and rules change only in a dedicated methods session
  (→ **Method changes never in a math session**). See [a methods session](../guides/methods-session.md).
- **Read the ledger log.** It writes to `LEDGER.log`; the user reads it (→ **`LEDGER.log` is append-only**).

**A fresh orchestrator per cycle.** A session hands off before its context is compacted, says that the next cycle
starts in a fresh session, and never offers to launch that cycle itself. The next orchestrator writes its brief from the
record, not from the last one's live reading of the results (→ **Fresh orchestrator per cycle**). What a session looks
like from outside is in [FLOW.md](../../FLOW.md#what-a-session-looks-like-from-the-outside).

**A session works on the tree it was opened in.** The kit and every instance have the same `bin/` and `tests/`, so a
command meant for one tree can run quietly in another. An instance is driven only from a session opened in it
(→ **A session works on the tree it was opened in**).

## Workers

A worker is a model process in one run directory, started headless by the launcher and confined by
[the sandbox](sandbox.md). It has no report channel: its files under `output/` are its whole deliverable.

**Solver.** Gets the problem statement, its brief and its inputs, and no prior attempt, bench brief or expected answer
(→ **Solver sees no prior attempts, no bench brief, no expected answer**). A solver that starts clean cannot inherit
the last solver's errors. It writes a short `result.md` and a `claims.json` in the schema of
[SCHEMAS.md §1](../../SCHEMAS.md#1-outputclaimsjson--written-by-the-solver), and runs the same form validator the
checker will.

**Referee.** A fresh worker that answers one typed question about one claim: `certify`, `hypotheses` or `sentence`
([SCHEMAS.md §3](../../SCHEMAS.md#3-outputrefereejson--written-by-a-referee-run-exactly-these-six-fields)). It sees
the artifact and the files the claim declares, never the brief, the solver's reasoning or other referees. Which
referees a claim needs is on [the trust model](trust-model.md) page.

**Evaluator.** The only role that receives locked data. It scores a solver set against a key and emits scores; the
orchestrator handles the scores only (→ **Controls are blinded and locked**).

**Canary and other runs.** A canary checks a route's context and sandbox before real work, and again after any change
to the hook, settings, an agent definition, a harness note or a route ([FLOW.md](../../FLOW.md#outside-steps--called-not-wired-in)).
Audits and outside readings are runs too, built from [templates](../../templates/README.md).

## The checker

[`bin/check`](../reference/tools/check.md) is the checker: it validates the claims' form, runs every artifact in the
worker's sandbox, audits a proof assistant's axioms, and runs declared mutations. It is a script so that the check
cannot argue (→ **Checker is a script, not an LLM**). [`bin/close-run`](../reference/tools/close-run.md) runs it with
the merge that builds the verdict table.

## An analyst, and the operator agent

Nothing in the method depends on an analyst. A user may keep a standing conversation outside the trust chain for
design questions and second readings, and may designate it the operator agent, which then gives direction within the
operator's list ([FLOW.md](../../FLOW.md#an-analyst-and-the-operator-agent);
[RULES.md §4](../../RULES.md#4-roles--three-plus-ad-hoc)). Either way it is never a step, a gate or a source of claims.
What it hands in is outside input and goes through an intake record first; its notes are uncertified until checked
against the record point by point (→ **The user's analyst's notes are uncertified**). See
[an analyst](../guides/analyst.md).

## Called for one thing

These are invoked when a specific question is stuck and whoever is stuck on it is an interested party
([RULES.md §4](../../RULES.md#4-roles--three-plus-ad-hoc)), and each is a packet, not a standing step; when each tends
to pay is in [RULES.md §10](../../RULES.md#10-outside-checks--the-operators-never-a-gate):

- **Outside reader**, after a referee has gapped the same sentence twice (→ **Outside-reader packet after the second
  referee gap**).
- **Set-up audit of a brief**, when a brief carries a new relaxation, list of conditions or transcription of a source
  (→ **Set-up audit of a brief**).
- **Handoff audit**, when the operator calls one (→ **Handoff audit by an outside model**).

A **methods session**, which changes the method itself, is a separate kind of session, not one of these packets
([RULES.md §7](../../RULES.md#7-standing-rules-that-keep-cycles-convergent)).

## What the role lines do not stop

- **Shared blind spots.** Roles separate who produces from who certifies, but every role may be played by models with
  common failures. The cross-family read and calibration ladders exist for this; they reduce it, they do not remove it.
- **An orchestrator that ignores a practice rule.** The hook enforces what it can name: approvals, the ledger, the
  locked data, the packet lists, launches, other terminal panes. A recursive `grep` typed in a shell command can still
  walk the ledger and the locked data, since the hook matches names, not what a program reads; rules such as that one,
  or never summarising a note, are kept by the session and checked by the user.
- **A forger with the user's account** ([RULES.md §6](../../RULES.md#6-approvals--the-gate)).

## Related

- [FLOW.md](../../FLOW.md): the cycle and the roles in one page.
- [A full cycle](../guides/a-full-cycle.md): the roles at work, step by step.
