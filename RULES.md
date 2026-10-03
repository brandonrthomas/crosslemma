# Rules

**This file is law in a workspace made from this kit.** It is the method, stated as rules. Every rule here was learned from a
failure or designed against one; `LESSONS.md` gives the incident behind each, by the bold label the rule carries. Where a rule
and this kit's code disagree, the code is what runs: say so and fix one of them.

**This file is not `CLAUDE.md`, on purpose** (→ **`CLAUDE.md` is injected in full into every worker**). `CLAUDE.md` in an instance is a
two-line pointer, and the user-scope and home `CLAUDE.md` files are excluded by `claudeMdExcludes`. The orchestrator reads this
file and `HANDOFF.md` explicitly at session start.

**Words.** Three terms (user rulings 2026-10-01). The **user** is the human being who runs the workspace: they approve,
rule, and may read any file. The **operator agent** is an agent the user designates to act as operator (in practice, the
user's analyst); it may give direction not requiring the user's approval, within the operator's list in §4. P7 (not
built) is the charter and the safeguards for running an operator agent unattended. The **operator** is either of them:
the user, or the operator agent where one acts. Every approval stays the user's. (P7, if built, would let a designated
agent sign approvals; that requires amending this line by the user's ruling.) **The test for what is whose:** anything
that could widen what a worker sees, what a claim asserts, what the ledger holds or what the gate lets through belongs to
the user; anything that only orders, reads or reports work inside those bounds may belong to the operator. The **orchestrator**
is the session doing the work. A **worker** is a sandboxed model process in one run directory. The names of environment
variables, the worker agent type, the tools' approval flag and the approval prompt text are fixed and listed in `SCHEMAS.md` §7.

---

## 1. Rule Zero

> **Whoever produced the work does not get to certify it.**

That is the whole rule. Everything below is the minimum apparatus that makes it hold. Certify with **artifacts** wherever an
artifact can certify (a proof assistant's kernel, an exact-arithmetic script, a coverage certificate, a known-solution re-find).
Use a fresh-context **referee** only where no artifact can — chiefly "does the formal statement say what the English claims?"
(→ **Whoever produced the work does not get to certify it**)

An artifact that cannot detect the thing it is supposed to guard is not an artifact
(→ **Certify with artifacts wherever an artifact can**).

## 2. Claim tags — mandatory on every substantive statement

| Tag | Meaning | Bar |
|---|---|---|
| `[PROVED]` | Complete proof | A referee finds no gap. Prefer machine-checked. |
| `[VERIFIED]` | Finite computational fact | Script in the repository, exit 0, exact arithmetic, range stated exactly, coverage certificate for range claims. |
| `[NUMERIC]` | Holds on a tested range or sample | State the range. Says nothing beyond it. |
| `[CONJECTURE]` | Believed, unproved | Evidence and the strongest counter-pressure. |
| `[HEURISTIC]` | Plausibility argument | Name the non-rigorous step. |
| `[GAP]` | Known hole | Say exactly what must be shown. An argument with a `[GAP]` is not a proof. |

Banned without the matching tag: *proves, shows, establishes, therefore, it follows, clearly, obviously, WLOG* (unless
discharged). A tag may carry a qualifier inside the brackets (`[PROVED, sketch]`). Untagged banned words are counted as
`prose_flags`: noted on the record, never blocking (→ **Mandatory claim tags**). A proof-assistant axiom audit showing an
incompleteness axiom is a `[GAP]`; a compile-time-evaluation axiom must be declared (→ **`native_decide` axioms**).

**Computer algebra.** A claim whose artifact rests on a computer-algebra package (PARI/GP, cypari2, mwrank, Singular, Macaulay2,
msolve, SageMath, or the like) earns `[VERIFIED]` only if an exact script that does not use the package re-checks a certificate
the package produced (points, maps, identities, Gröbner or rational certificates), or two independent packages agree on the
fact; otherwise `[NUMERIC]`. The package is named in `silent_links` either way; sympy is a named silent link. An instance may
link SageMath as an optional module (`bin/new-workspace --sage`), mounted read-only for every worker
(→ **Computer algebra is an optional module, and its results need a certificate**).

## 3. Anti-self-deception — the failures that actually happen

1. **Prior art before novelty.** Search before calling anything new; record with links. A search is a bounded negative: say what
   was searched and what was not reached. **A blocked surface is never "not found".** A "could not reach" list is checked against
   later sessions' findings before it goes into another prompt (→ **Prior art before novelty**).
2. **Cite or derive.** Never invoke a half-remembered theorem. Look it up or prove it here (→ **Cite or derive**).
3. **Re-find known objects before believing absence.** Unvalidated search code proves nothing (→ **Re-find known objects**).
4. **Exact arithmetic.** Integers and rationals. Floats need a stated error bound the conclusion survives (→ **Exact arithmetic**).
5. **Symmetry and degeneracy audit** before believing a search: double counts, missed boundary cases (→ **Symmetry / degeneracy audit**).
6. **Reversal test.** Try to derive the negation. If it feels as easy, the framework is wrong (→ **Reversal test**).
7. **No result-shaped prose.** "No progress; killed X because Y" is a good day (→ **No result-shaped prose**).
8. **Silent links first.** Loud links fail visibly; silent ones (enumeration completeness, reductions, "uniformly in magnitude")
   do not. Verification effort goes to silent links, and every claim names its own (→ **Silent links first**).
9. **Artifacts, not diligence.** Never certify care narratively. Every consequential sentence maps to an inspectable object, and
   an inference from a number is not an observation of the thing (→ **Artifacts, not diligence**).
10. **Mechanism or coverage.** Before another case: does it buy a new mechanism (pursue) or more coverage of the same one (stop)?
    (→ **Mechanism or coverage**)
11. **Speed is a region signal.** Fast progress means the machine-compressible region. Say which region a result came from
    (→ **Speed is a region signal**).

## 4. Roles — three, plus ad hoc

| role | who | gets | emits | never |
|---|---|---|---|---|
| **Orchestrator** | the session | briefs, verdict tables, results, scores | briefs, run directories, ledger appends via script | reads answer keys or control label maps; edits the ledger by hand; summarizes a referee's prose to the operator; launches or appends without an approval; goes near the approval tool except to offer it for the user's tap |
| **Solver** | a worker, sandboxed, clean-room | the problem statement, its brief, rules, inputs copied into `input/` | `output/result.md` (≤150 lines) + `output/claims.json` | sees prior attempts, the bench brief, or the expected answer |
| **Checker** | a script — not a model | `claims.json` + artifacts | `check.json`: pass/fail per claim | argues |
| **Referee** | a worker, fresh, sandboxed. **Two per `[PROVED]` claim, one per question, plus a `certify` read from the other model family; one per `[VERIFIED]` or `[NUMERIC]` claim, from the other family** | one claim, its artifact, the files the claim declares as `deps`, the problem statement | `referee.json`: `holds` / `falsified` / `gap` / `unverifiable`, one pointer, ≤3 lines | sees the brief, the solver's reasoning, or other referees |
| **User** | the human being | every file, directly | rulings, approvals: the user's list below | — |
| **Operator agent** | an agent the user designates (in practice, the analyst) | what the user gives it; files outside the never-read list | direction within the operator's list below | does anything on the user's list; reads a never-read file |

Each "never" in that table has an incident behind it (→ **The orchestrator never reads answer keys or label maps**,
→ **The orchestrator prints a referee's note; never summarises it**, → **Solver sees no prior attempts, no bench brief, no
expected answer**, → **Checker is a script, not an LLM**, → **A referee sees the artifact, its declared `deps`**).

### The user's acts, and the operator's (user ruling 2026-10-01)

By the test in "Words". **The user's alone:**
1. Approvals and taps, and every `!` command.
2. Credentials and `sudo`.
3. The safety layer: the hook, settings, the user-level guard, and the environment files.
4. Declaring the session type (mathematics or methods); every ruling that changes a method or a rule; and rule
   interpretations and security questions, which are put to the user, not the operator agent.
5. Deviations from a rule or form that widen what a claim or packet may carry.
6. Independence rulings, when no model family is independent of both the producer and the framing (§8 "Outside input"
   rule 7; `data/cross-family-rulings.json`).
7. Classing outside input as anything that can enter a packet or a claim (target, framing, premise, data). Filing it
   as record-only may be done by the operator.
8. Opening and closing the analyst channel, and Clatter's manual mode.
9. Input and packet exceptions: `--input-approved`, and anything that puts outside text or another run's files into a
   packet.

**The operator's** (the user, or the operator agent): setting the purpose within the session type the user declared;
procedural deviations that loosen nothing; choosing among the outside checks the rules already allow; receiving
reports, and reading files except the never-read list.

**Never read by any agent, the operator agent included:** credentials, licence and auth files; `data/locked/`; a run's
output while it is in flight; the ledger log (§8).

Cut deliberately: delegator, reconciler, propagator. Reconciliation is a script. Propagation does not exist because **a claim
lives in exactly one place**.

**What was cut is the standing pipeline, not the roles.** Any of them may be invoked *ad hoc*, for one stuck thing. The
discriminator is not which role it is but why it is called:

- **Invoke one** when a specific question is stuck *and* whoever is stuck on it is an interested party.
- **Do not wire one in.** A role that runs every cycle stops being a check and becomes a layer; layers need readers, and readers
  need adjudicating (→ **Three roles; anything else ad hoc**).

**The packet is the mechanism, not the role.** If the question cannot be written down self-contained — the evidence both ways,
the interested party's view last and labelled — it is not ready to hand to anyone (→ **The packet is the mechanism**).

## 5. The cycle

```
0  User names the problem or attack. Orchestrator writes the brief: task, inputs, kill
   criteria, CYCLE EXIT CRITERIA, output schema.                        → USER GATE
1  Solver run                      → output/result.md + claims.json
2  Checker (script)                → check.json
3  Referee run(s)                  → referee.json
4  Verdict table (claim | tag | check | referee | earned), with each formal statement beside
   its English. Orchestrator shows the table and the paths; the user reads
   referee.json directly if wanted.                                     → USER GATE
5  Approved claims are appended to the record at the tag they earned.
   falsified → new brief. gap → recorded as [GAP]. Nothing else is queued.
6  Exit criteria met → close the cycle. Not met → one more solver run. Anything that does
   not falsify something on the record is DROPPED, not backlogged.
```

`bin/close-run` performs steps 2 and 4, prints the referee line for every `[PROVED]` claim still lacking a `holds`, and prints
the exact approval and append lines for step 5. It launches nothing and appends nothing (→ **`bin/close-run` performs steps 2 and 4**).

**Cycle exit criteria are written at step 0 and checked mechanically at step 6** (→ **Cycle exit criteria written at step 0**).
**One run at a time** unless the user rules otherwise for named runs (→ **One run at a time unless the user rules**).
Nothing that fails to falsify something on the record is queued (→ **Anything that does not falsify something on the record**).

### The brief

- **The skeleton has fixed sections** — gates with their pass criteria, what is frozen before the run starts, the exhaustive list of
  classes a unit of work can end in, and a budget block stating the enforced caps as facts — so the least mechanical step has the
  same shape every time (→ **The brief skeleton has fixed sections**).
- **A compressed sentence in a brief is a claim.** Write the chain out; what it hides then becomes visible
  (→ **A brief's compressed sentence is a claim**).
- **The slug, and every file in the run directory, is something the worker sees.** A slug never announces the answer, and never
  starts with a number — the tool assigns that (→ **A slug, and every file in a run directory, is something the worker sees**).

## 6. Approvals — the gate

**Every launch and every append to the claims record needs a user approval, and the tools refuse without one**
(→ **Every launch and every ledger append consumes a byte-bound, single-use, 30-minute user approval**). Approval is an act of the user, bound to the
exact bytes the user read:

1. The orchestrator runs `bin/lint-brief RUN` and clears its errors, then `bin/manifest RUN -- <launch flags>` (read-only) and
   shows the printout: path, size and hash of every file the worker will see, one digest, the flags
   (→ **`bin/lint-brief` before `bin/manifest`**). A launch approval always binds its flags, `--model` included; an approval of
   the bytes alone would let any model, effort, prompt or cap launch (→ **A launch approval binds its flags**).
2. The user approves, either at the terminal with the shell-escape prefix — those commands do not pass through the hook,
   which is what makes the approval the user's (→ **`!` commands do not pass through the hook**) — or by allowing a prompt
   whose text the hook computes from the bytes. Never "don't ask again" (→ **The tap route needs `--digest`**).
3. The launch or the append consumes the approval. It is single-use, lasts 30 minutes, and any edit to a bound byte, a different
   flag or a different id set voids it: "no user approval for these hashes", which is the stop
   (→ **The manifest is shown first**). A flag given twice is refused, and the launch reads the bytes again just
   before its worker starts, after its set-up; a name the approval leaves unhashed (`licence.log`, a non-empty
   outbox) makes the run one launched before (→ **The approval holds until the worker starts, and binds the claim**). A
   launch refuses a run name used in two workspaces, and a failed `bin/new-run` removes what it made (→ **A launcher fails
   cleanly and touches nothing it has not checked**).

Several runs in one call is batch consent; a batch tap takes one digest per run, in order, and one mismatch refuses the whole
call (→ **Batch tap**). Tell the user how many runs one tap covers. Several notes take one approval the same way:
`bin/approve --annotate-batch FILE`, every note printed in full, appended all or none (→ **One approval for several notes; a
replaced approval is announced**). Runs approved together may launch as a **queue**: `bin/run-external --queue RUN1 RUN2 …`
uses every approval at its start and releases each run, one at a time, only with the approved flags and unchanged bytes, so a
later run's approval cannot expire while an earlier run works (→ **A queue for runs approved together**). A queue stops at a run
that ended on the plan's usage limit or the provider's capacity refusal and releases nothing more (→ **A queue stops at the plan's
usage limit**); while a queue releases, nothing creates or removes files in its tree (→ **Nothing creates or removes files in a
tree while its queue releases runs**); between an approval and its launch nothing the scan reads changes, and blocked files
describe a pending packet, never quote it (→ **Between an approval and its launch, no scanned file changes**). Every check the launcher can
make without the approval (the brief's turn cap, the harness note, the packet, an earlier launch, the host's sandbox,
settings and key) runs before the approval is touched, for a queue before any of its approvals is. Runs approved in one session and launched in another are
approved in the launching session, against the bytes as they then are.

**Limit, accepted by design:** the orchestrator runs as the user's Unix account, so a deliberate forgery is possible. What this stops
is a misreading followed by an ordinary command.

### What consent covers

An approval covers exactly what the approval tool named, and naming several things in one call is batch consent. For work that
needs no approval record, the same holds for the operator's words: "do all of X" covers all of X and nothing beside it. A
go attached to another instruction covers that instruction only. An operator message covers what the operator had seen
when it was sent. Deviations from what was ruled are put to the operator before the choices that depend on them, and to
the user when they widen what a claim or packet may carry (§4, item 5). **Silence is not approval,
and a status update is not a go** (→ **Batch consent**, → **Never read a permission more widely than its words**).

## 7. Standing rules that keep cycles convergent

- **Referee output is typed and bounded.** A finding that is not `falsified` or `gap` does not exist after step 4. A note over
  three lines or 600 characters makes the file invalid and the verdict does not count (→ **`referee.json` has exactly six fields**).
- **The evidence boundary.** A hypothesis is carried by a claim's English only if the English states it, or the material supplied
  with the claim derives it. Notation and unpacking a definition count as stating it; a referee deriving it does not, however
  short the derivation. The same boundary governs silent links: **declaring a link names an obligation and does not discharge
  it.** One rule covers both, deliberately, because the alternative is a boundary between an obvious implication and a non-obvious
  one, which nobody applies twice the same way. Where reproducibility matters more than convenience, move the claim into a formal
  declaration whose statement *is* the claim, rather than adding a reviewer (→ **The evidence boundary**).
- **Every English statement is written from what the artifact establishes**, never from a description or summary of it. For a
  formal artifact that means reading the statement of every declaration cited and carrying each hypothesis into the sentence
  (→ **Every English statement is written from the formal statement**). The verdict table puts the formal statement beside the
  English so a fidelity read starts from the binder list (→ **Formal statements captured beside the English**).
- **Two referees, two questions, a cross-family certify read, no adjudicator.** A `[PROVED]` claim gets a `certify` read and a
  `hypotheses` read. Decorrelation between those two comes from asking different questions, not from using different models: on
  the record, two models gave identical verdicts on every packet of one ladder, while the two questions disagreed on a real
  overclaim — `certify` missed it under two models and `hypotheses` caught it. **A second model never replaces the second
  question.** Beside the pair, a claim gets a `certify` read from another model family than its producer's (built in, Anthropic:
  Opus, Fable, Sonnet, Haiku, and OpenAI: GPT, Sol, Astra; and any family the user adds in `kit-env.json`, whose models
  referee only after their ladders, "Calibrate before trusting" below, since the exception below names the two built-in
  families; the code counts the read either way), which guards against a blind spot the producer's family shares and a second
  question to the same family cannot reach; the source adopted it pending a comparison of the two families' certify reads on
  about ten claims, after which the pair may be split instead (→ **A cross-family certify read**). **An exception, recorded as
  one (user 2026-09-29):** until a model of each family has been through the `certify` and `sentence` ladders, its
  cross-family reads count before "Calibrate before trusting" below is met, because the read only adds a requirement (the
  same-family reads must still hold); its likely failure, a false `gap`, blocks a claim the operator can read the note of. A
  family is read from the models that answered (the run's record), or, with none recorded, the run's approved `--model`; an
  answer from another family than the approved one, or from two, is an unknown producer. An unknown producer, or a restatement the orchestrator assembled from a run of the other family,
  is met only by the user's ruling, recorded in `data/cross-family-rulings.json` (never in a run directory, which the worker
  writes), which names the family of the referee whose
  hold then counts, not the producer's. The referee's family should also differ from
  that of every outside input the claim rests on (§8 "Outside input" rule 7); where no family is independent of both, the
  user rules. Disagreement needs no agent to resolve: any `gap` makes the claim `[GAP]`, `[PROVED]` needs every live referee
  to hold and a live cross-family `certify` hold, and the three-line bound is what lets the user adjudicate by reading. A new layer must emit something a script consumes, not prose that needs
  another reader (→ **Two referees per PROVED claim, one per question**). **A script claim gets a `sentence` read**: does its
  English say exactly what the checker asserts (the script's exit conditions and the values the claim's `expect_*` fields pin,
  a substring pin only where it ends the value, not the values it only prints), on exactly the stated range; does a
  declared mutation exercise each asserted part; was a coverage count frozen from the run's own output. Under `kit/claims/2` a
  `[VERIFIED]` or `[NUMERIC]` claim is pending until a live `sentence` referee of the other model family holds. Every question's brief says that an
  artifact certifying less than the English says is a `gap` (→ **A sentence referee reads every script claim**).
- **A referee sees the artifact, its declared deps, and the problem statement — nothing else.** The solver declares the deps, so
  the choice is on the record, not the orchestrator's (→ **A referee sees the artifact, its declared `deps`**). A referee of a
  text claim is given, and told to open, the library definitions the text quotes (→ **A referee of a text claim**). A referee of a
  claim with `ledger` premises is given those entries, extracted by `bin/claims-extract --ids`, as `input/ledger-premises.md`
  (→ **A referee is given the ledger entries a claim rests on**).
- **A verdict is bound to the artifact the referee saw.** If the artifact or any dep changed afterwards, the verdict is stale and
  does not count (→ **A verdict is bound to the artifact copy**).
- **Referee every `[PROVED]` claim.** There is no audit budget cap (§12) (→ **Audit budget cap removed**).
- **Check what a referee actually opened**, in its transcript, not by inferring it from a memory or timing figure
  (→ **`usage.json`'s memory figure does not capture a sandboxed compile**).
- **Method changes never happen in a working session.** A dedicated methods session, recorded in the handoff. There is no limit
  on how many changes a methods session makes or on how often methods sessions happen. An exception to the separation is
  recorded as an exception, never as a precedent (→ **Method changes never in a math session**).
- **Fresh orchestrator per cycle.** Hand off before compaction, not after. The handoff is a pointer sheet — paths, hashes,
  exit-criteria status, a disclosure ledger of what this orchestrator read — certified by the user. A new cycle starts in a
  fresh session, and the outgoing orchestrator's last message says so; it never offers to launch the next cycle itself. The fresh
  orchestrator writes the next brief from the record, so the run's design does not inherit the outgoing orchestrator's live
  reading of the results (→ **Fresh orchestrator per cycle**).
- **A handoff records no disk figure.** The new session reads disk space itself, as the source of truth (user ruling
  2026-10-01); a recorded figure goes stale between sessions and invites a false stop or a false all-clear.
- **Run your own preflight before calling a handoff done.** A handoff that gives the next session a gate must have had that gate
  executed, verbatim, by the session that wrote it. An instruction nobody has executed is a claim with no artifact
  (→ **The writer runs its own handoff preflight**). Every path the handoff names in backticks must exist; a script checks it,
  not the author's `ls` (→ **Every backticked tree path in a handoff exists**).
- **Handoffs restate their labels.** A shorthand for a line of work is written out in full every time, or it drifts between
  sessions (→ **Handoffs restate their labels**).
- **Calibrate before trusting.** Before the pipeline's verdicts mean anything, run it on a ladder of known results with planted
  errors and measure recovery rate, referee catch rate and referee false-positive rate. A model is not used in a role before it
  has been through that role's ladder. Read a ladder as a coverage challenge, not as a recall figure: the denominators are small,
  and a designer who was shown the trap list writes adversarial plants, not natural ones
  (→ **Calibrate before trusting**, → **A ladder is a coverage challenge**).
- **Controls are blinded and locked.** Known-answer problems mixed into a solver's set are labelled by a map in `data/locked/`
  that only an evaluator run receives. The orchestrator handles scores only, and a script finds a copied key by hash under any
  name (→ **Controls are blinded and locked**).
- **State a cost before spending it.** A launcher's cost figure for a routed model is Claude Code's own estimate from its
  price table (`total_cost_usd`; the kit keeps no price table) and is not a meter (→ **State a cost before spending it**).

## 8. The record

```
LEDGER.log        append-only. utc | actor | run | event | detail. Written by the hook and
                  the kit's tools in bin/ only. Agents write, never read — the hook enforces it
                  for the orchestrator too. Only a plain git add, commit, status, diff --numstat
                  or diff --stat may name it, each as a command of its own, never compound.
CLAIMS.md         one entry per claim, by id, tag, artifact pointer, run. Appended by script from
                  approved claims. Superseded by a new entry that references the old; never
                  edited. A changed novelty, or an audit finding that leaves the truth as stated,
                  is a note, not an edit and not a supersede.
HANDOFF.md        pointer sheet for the next orchestrator. Rewritten and committed at each
                  handoff, and archived before its first touch, never only rewritten. It holds
                  the current pointer and nothing else: read it whole with the Read tool, never
                  by reference. No historical tail; a script flags one.
problems/<name>/  PROBLEM.md, prior-art.md, attacks/<name>/README.md
workspace-N/runs/NNN-slug/   BRIEF.md · input/ · scratch/ · output/
                  one workspace per problem; run numbers unique across workspaces.
data/locked/      answer keys and label maps. Never copied into a solver run. Since kit-v0.6.9 it lies OUTSIDE
                  the tree, at kit-env.json's locked_dir (made by bin/new-workspace at
                  ~/.local/state/crosslemma/<instance>/locked/), so no search from the instance walks it; an
                  instance without the field keeps <root>/data/locked. `data/locked/` in these rules and the docs
                  names the locked directory wherever it lives.
intake/           outside input, one folder per input: IN-NNN-slug/record.md, verbatim/, SHA256SUMS
                  (from templates/intake-record.md); operator and orchestrators only.
data/packet-rules.json, data/packet-exceptions.json
                  what no worker's packet may carry, and the files excepted from that; the user's.
bin/              the tools. harness/  route notes and the search helpers.
```

Everything else references a claim by id. **No file restates a claim**, and one problem is one workspace, with run numbers unique
across workspaces (→ **One workspace per problem**).

- The ledger is written by agents and never read by them; the user reads it
  (→ **`LEDGER.log` is append-only**, → **Only a plain `git add`/`commit`/`status`/`diff --numstat`**).
- The claims record is append-only. **A changed truth is a superseding claim**; a changed novelty or a finding that leaves the
  truth as stated is a note (→ **`CLAIMS.md` is append-only**, → **A changed novelty**).
- **The handoff is archived before it is touched** and carries no history (→ **`HANDOFF.md` is archived before it is touched**,
  → **`HANDOFF.md` holds the current pointer and nothing else**).
- **Every handoff contains the opening prompt for the next session, and repeats the requirement to contain it**, so it propagates
  without anyone remembering it (→ **The opening prompt is in every handoff**).
- **No packet carries blocked material.** An instance lists in `data/packet-rules.json` what no worker may receive (typically
  probabilities of success, rankings of routes, evaluations of the record): files and runs out whole, or only the matching lines
  of a file. `bin/lint-brief` scans every packet (`BRIEF.md`, `HARNESS-NOTE.md`, `input/`) for a byte copy of blocked material or
  a 12-word run shared with it that no open material excuses, and `bin/run-external` refuses such a launch before touching the
  approval. Only the output of an earlier run that was launched or checked counts as open; a packet never does; a block beats
  an open root, so a blocked path inside open material, and the matching lines of a line rule's file, are not open. Both lists are
  the user's (`! bin/packet-block …`, `! bin/packet-except …`), and the hook refuses the orchestrator's edits to them. A new
  instance starts with `DIRECTION.md`, `HANDOFF.md`, `handoffs/` and `intake/` blocked, and with `"verdicts": true`: a route-verdict word
  ("ranking #7", PARK, PURSUE, DEAD, "most promising", …) is an error on any line of any packet file; an evaluator run is added
  when it is made. The launch
  path's scan rebuilds its index and never trusts the cache. The hook recognises the lists by name, so a glob or a constructed
  path gets past it: that is deliberate forgery, which this kit does not claim to stop (§6's limit). The scan is a net under
  the rule, not the rule: packets are still built from open material only (→ **No packet carries blocked material**).
- **No record file name may appear in a run's `input/`.** A packet copies them under other names; a script refuses the rest
  (→ **No record file (`BRIEF.md`, `CLAIMS.md`, …) may be copied into a run's `input/`**).
- **A worker's view of the ledger is `bin/claims-extract`'s output**, made by fixed rules, less the entries and notes on the
  user's list (`! bin/packet-block --extract …`); `--out` ledgers its hash, and the extract is scanned like any packet file
  (→ **A worker's extract of the ledger is made by a tool**).
- **Held sources are hashed before they are read**, under `problems/<name>/sources/`; what a networked worker downloads is hashed
  in the run's record, not committed (→ **Held sources are hashed**).
- A shared formal library, if the instance links one, has a master list; accepting an edit is a deliberate command, and every
  check records the library state it ran against (→ **The Lean library has a master list**).

### Outside input

Outside input is anything that enters the workspace other than through its own runs: a model session the user runs
elsewhere, another workspace, a local agent, the user's analyst's text, and any result, target, framing, data or tool relayed
from them. The user's own rulings are not outside input; text an analyst drafted is, even when the user relays it as
theirs (the user's explicit requests in it are theirs; its factual claims are checked like any outside input)
(→ **Outside input has an intake record first**).

1. **Intake record first.** On receipt, before anything acts on it, the orchestrator writes `intake/IN-NNN-slug/record.md` from
   `templates/intake-record.md`, the text or files verbatim under `verbatim/`, their sha256 in the folder's `SHA256SUMS`. A
   record may hold several items. `bin/verify-data` checks every record's name and hashes.
2. **Class, ruled by the user, per item:** target statement, premise, framing, data, tool, or record-only. Until ruled:
   record-only.
3. **Premise** only (a) as a claim of this workspace's record from a verify-or-refute run whose packet holds the target
   statement and not the outside text, or (b) as a conditional `source` premise under its own ruling naming the IN id, with
   the verbatim file as the source. Never by message ("assume it is true").
4. **Framing** into a brief or packet only under a ruling, as a paragraph tagged `[FRAMING, outside input IN-NNN, not verified
   here]`. A list of suggested methods only if the user supplies it.
5. **Target statement** into a brief only as ruled, with neutral obligations.
6. **Analyst-drafted.** A ruling, brief text or target drafted by the user's analyst says "analyst-drafted"; when that text
   itself enters a packet, ruling or target, it also gets an intake record.
7. **Independence.** A record's "seen by" lists every run, model family, analyst session and outside-model session that
   received it, and is updated whenever an item enters a packet, brief or message. When choosing referees or a replicate, count
   the family of each outside input a claim rests on or that framed the run producing it, as well as the family of the
   claim's producer.
8. `intake/` is the operator's and the orchestrators' only: never in a packet except as the user excepts a file
   (`bin/packet-except`); a new instance blocks it from the start.

Rulings on outside input are recorded where the instance records rulings (the handoff's rulings section), with the IN id.

### Claim form — the schemas are law (`SCHEMAS.md`)

- **An unknown field, or a field in the wrong place, is an error**, not a silent no-op (→ **Unknown or misplaced fields are errors**).
- **Every `[PROVED]` and `[VERIFIED]` claim lists its premises**: everything it rests on besides its artifact, each one a kernel,
  classical, published, source, ledger or software premise. A published or source premise is the primary text, held in the run,
  with a file quoting the statement used verbatim and with its location, both in the claim's `deps`; a premise is used only as
  quoted. An entry that rests on a published theorem, a source taken as stated, or another entry says `(conditional: …)` in its
  header, and a ledger premise is a dependency edge (→ **Premises on every claim; the primary text quoted; a conditional
  marker**).
- **The form validator is one piece of code** for the worker and for the checker, copied into every solver run and run last, so both
  sides apply the same rules (→ **`bin/validate-claims` is one piece of code**).
- **A coverage claim needs a checker that fails when the range is truncated**, declared as mutations the checker runs. A coverage
  claim with no mutation test run by its check (none declared, or a check without `--mutate`) is `[NUMERIC]`, not
  `[VERIFIED]`, and the earned tag records it so (→ **Optional `artifact.mutations`**, → **A VERIFIED claim needs a
  mutation run by its check**). A mutation kills only with its targeted part's FAIL line, named in `expect_stdout_contains`,
  which under `kit/claims/2` every mutation must name; a crash is not a kill. FAIL lines go to stdout and no
  part's occurs inside another's; a substring pin asserts a printed value only if it ends the value (→ **A mutation kills
  only with its FAIL line**).
- **The earned tag is computed, not claimed:** any live `falsified` wins, then a failed check, then any `gap`; `[PROVED]` needs every
  live referee to hold, a live hold on both questions (`certify` and `hypotheses`), its check (pass or n/a), and a live `certify` hold from the other
  model family, and under `kit/claims/2` `[VERIFIED]` and
  `[NUMERIC]` need a live `sentence` referee of the other family that holds; anything pending is not recorded (→ **Earned tag: falsified > check fail > gap**).
- **Appends are all-or-nothing** and refuse a changed artifact, a duplicate, or a supersede target that is not on the record
  (→ **`ledger-claims` is all-or-nothing**). The append validates the document and each claim itself, never trusting a
  schema the worker declared, and writes every field on its own line, a field's own line breaks made spaces
  (→ **The append validates what it records, and no field writes a line of its own**).
- **A ledgered run's check record is kept.** An entry cites `check.json` by its generation time, so before a run with any
  ledgered claim is re-checked, `bin/check` keeps the record as `check.<generated>.json` and never overwrites a kept one
  (→ **A ledgered run's check record is kept**).
- **A user-excepted input from another run carries its source and hash onto the ledger**, and is taken only when its bytes
  are on the user's exceptions list (`data/packet-exceptions.json`) (→ **`--input-approved` puts a
  user-excepted input's source and hash on the ledger**).

## 9. The sandbox — enforced, not convention

- **Orchestrator session:** every call logged. Unrestricted except for the approval gate. Denied: any command naming the approval
  tool other than the one plain digest call; anything touching the approvals directory, reads included; a Read, Grep or Glob
  of `data/locked/`, and any command naming it but a plain `bin/new-run … --role evaluator` or a plain git add, commit,
  status or diff (with no option that prints a file's contents: → **"A plain git command" is a list of options, not a
  pattern on how it starts**); a Grep or Glob rooted above the ledger, a locked file or an approval record unless its glob or type filter (a Glob's pattern)
  matches none of them, every place the locked data can be guarded even when `kit-env.json` is unreadable
  (→ **The orchestrator reads neither the locked data nor the approval records**); any write or edit of the ledger
  (appended only, by the hook and the tools); a launch flag given twice (but `--module`) (→ **The guards cover every
  route and every place**); any edit of the
  packet rules or their exceptions, and any command naming
  them or their tools other than a plain git add, commit, status or diff; a bare headless launch of any provider's
  CLI; the messaging and workflow tools; every agent call of a worker type; keys or buffers typed into a tmux pane, and any
  touch of Clatter's files but through its dispatcher's peers, ask, send, broadcast, recv, status and doctor, or its
  send script for a threaded reply without the sender flags `--from` and `--from-session`; reading counts as touching
  (no Read, Grep or Glob there, nor a Grep or Glob rooted above it)
  (→ **An orchestrator types into no other pane and touches no mailbox**); any write to the environment files that decide
  what a worker's sandbox mounts (`kit-env.json`, `.kit-lean`, `.kit-sage`, `.kit-routes`), and any command naming them
  but a plain read or a plain git add, commit, status or diff (→ **The environment files are the user's**); any write
  to the referee bindings (`data/referee-bindings/`, `bin/new-run`'s) or the cross-family rulings
  (`data/cross-family-rulings.json`, the user's), and any command naming them but a plain read or a plain git add,
  commit, status or `diff --stat`. A tool that runs a shell command other than Bash (Monitor) is gated as Bash is, and
  never offers the tap on the approval tool (→ **A tool that runs a shell command is gated as Bash is**). A failure inside
  the gate refuses gated calls only; a ledger that cannot be written refuses what needs its record (an approval tap, an
  agent launch) and lets the rest through the gate as usual, the user told that they are not recorded (→ **Small gaps in
  the gate, closed**). In the tree, a git command that prints file contents (`show`, `log -p`, `diff` without `--stat`,
  `grep`, `blame`) must name its paths, none of them the ledger, the locked data, an approval record or a directory
  holding one; `cat-file`, `archive`, `format-patch` and an unknown subcommand (an alias) are refused; git on another
  repository is not the tree's (→ **The ledger is guarded by name; git is guarded by what it prints**). A hook that does not load, or input it cannot read,
  refuses every call: the settings carry a second command that loads the hook and exits 2 when it cannot,
  and the launcher refuses a tree whose settings do not register the hook on PreToolUse for every tool (→ **A
  hook that does not load refuses, and the limits a worker runs under are the approved ones**).
- **Worker:** first `Read` binds it to one run directory; Read and Write elsewhere denied by realpath. Bash is rewritten into a
  bubblewrap sandbox, in the foreground only (nothing of the worker outlives its call to race a Read or Write check; the
  briefs say so, an hour at most per call, → **A change to what a worker can do is a change to its briefs**): run
  directory read-write; the OS and any linked library read-only; tmpfs `/etc` and `/tmp`; no network;
  clean environment; a shim queues ledger entries the worker cannot read back
  (→ **First `Read` binds a worker to one run directory**, → **`bwrap --hostname sandbox`**).
- **A worker's tools beyond the system come from the user's environment file**, `kit-env.json` (`SCHEMAS.md` §8): modules
  mounted read-only for every worker; a module that names licence servers only for a run whose `RUN/.modules` and launch
  (`--module`, bound in the approval) both name it, which then reaches those hosts and ports and nothing else, through a
  relay on the host that logs every connection. A mount source that is the root, a home directory, the instance or a
  credential directory is refused whoever writes the file. A licensed program whose licence is a file is run by the
  user outside the kit, its results outside input (→ **A worker's tools come from the user's environment file**).
- **Workers have Read, Write and Bash only. No Edit, Glob or Grep** — the harness validates Edit input before hooks run, which is
  a substring oracle on any file (→ **Workers have Read, Write, Bash only**).
- **Limits are enforced, not promised.** The run's limits file, as kept by the launcher at the launch outside the run (the run's
  own copy is the worker's to rewrite), gives every sandboxed command its CPU ceiling and thread caps, and
  the launcher runs the worker under a cgroup quota and memory cap. Briefs state the caps as facts; they do not ask the worker to
  honour them; a host that cannot enforce them (no systemd user scope) runs no worker, and the launcher refuses before the
  approval is touched (→ **Limits are enforced, not promised**). The whole-run CPU budget is one of them: the run is stopped when its
  process tree has used it (exit 152, `cpu_cap_hit=`; → **The whole-run CPU budget is enforced**). Every kill-all is guarded so it cannot reach past
  the run: the Codex cleanup only inside the worker's own process namespace, the CPU cap's sweep only inside the run's own
  scope (→ **A kill-all runs only where it cannot reach past the run**). No run has a spending cap: the launcher's cost figure is a price-table
  estimate, not a meter, so it caps nothing real (→ **No spending cap on any run**). Every route has a wall-clock cap
  (`--wall-hours`, 4 h on the Claude routes and 2 h on Codex by default), one deadline across a launch's retries, reported as
  `wall_cap_hit=` on its exit line (→ **A wall-clock cap on every route**).
- **Every worker is a headless main process.** Never a subagent: a subagent inherits the orchestrator session's harness text, and
  a headless process does not. The hook refuses every agent call of a worker type, approved or not, and spends no approval doing
  it (→ **Every worker is a headless main process**). A headless worker is recognised by a variable in its environment, which the
  worker cannot change; a file in the run directory would not do (→ **A headless worker is recognised by**).
- **No run method shows memory or skills**, and headless launches carry an empty MCP config so no server's instructions reach a
  worker; the project denies MCP servers outright (→ **No run method shows memory or skills**, → **Headless launches carry
  `--strict-mcp-config --mcp-config no-mcp.json`**, → **MCP servers denied project-wide**).
- **Settings bind at session start.** After changing agents or settings, restart or test headless, then re-run a canary
  (→ **Settings bind at session start**).
- **The launcher checks effort per route**, and the effort the model's requests actually carried is recorded for every route: an
  approved effort is not an observed one (→ **`bin/run-external` checks `--effort` per route**, → **The effort the model's
  requests actually carried**).
- **A brief may not allow more tool calls than the turn cap**; the launcher refuses before touching the approval
  (→ **A brief may not allow more tool calls than `--max-turns`**). On Codex, which has no turn cap, `--max-turns` caps the
  worker's tool calls, counted from its transcript (→ **A Codex worker's tool calls are capped**).
- **The models that answered are recorded**, from the run's own transcript, and a run not answered by the one model its
  approval named is flagged on its exit line and by `bin/close-run` and `bin/ledger-claims`, never refused (→ **The model a
  worker ran on is recorded**). A parent session's `ANTHROPIC_*` routing never reaches a worker (→ **A parent session's routing
  never reaches a worker**).
- **The launcher retries and resumes a run cut short by an upstream rate limit**, rather than losing it to a transient
  (→ **A worker's upstream rate limit is retried and resumed by the launcher**).
- **Transcripts are written outside the worker's reach** and moved into the run only after it stops, so a worker cannot alter its
  own transcript (→ **Transcripts are written outside the worker's reach**). On the Codex route the model process runs inside
  the sandbox, so its commands run apart from it: each in a sandbox of its own with its own processes, Codex's home (the token,
  the session log) hidden, and no network on a run without it; the transcript reaches the host through a pipe, with a hash
  chain the record checks (→ **A Codex worker's commands run apart from Codex**). The egress proxy's socket lives on the host
  in a short directory private to the user's Unix account, and only the socket file is bound in (→ **The egress socket's host side
  is in a short private directory**). A Codex worker has no sub-agents: Codex reads
  a model catalog without them, and a launch whose prompt, rendered offline first, still offers them is refused before the
  approval (→ **A Codex worker has no sub-agents**).
- **A run directory is launched once**: a run holding an earlier launch's record or output is refused before the approval,
  because the new worker would read the previous attempt; a retry is a new run (→ **A run directory is launched once**). Long
  runs launch detached (→ **Long runs launch detached**).
- **No internet for anyone without the user's permission for that specific use.** A networked or external-CLI launch needs its
  flags bound in the approval and a matching harness note, and leaves a record of what it could read, what network it had, and
  what it downloaded. An egress allowlist names exact hosts, never subdomains
  (→ **Networked and Codex launches need their flags bound in the approval**, → **The Codex egress allowlist is exact hosts**).
- **Worker context residuals are named, not hidden**: the account email, the working directory path, the sandbox command line and
  its mount paths, a harness note preferring Bash, and, on the Codex route, the worker's own `.ledger-outbox`, its own
  queued lines and never another run's (→ **Worker context residuals are named**). The sandbox's root is remounted
  read-only after the binds, so the run directory's parent chain, `/home` and `/opt` cannot be written inside it; a worker's
  report of an escape is still checked against the host before it is believed (→ **The run directory's parent chain is
  writable inside the sandbox**, → **The sandbox's root is remounted read-only after the binds**).
- **Settings are shipped as a template and installed by the tool that makes a workspace**, never committed live. A live
  `settings.json` takes effect the moment someone opens a session where it sits, so a copied scaffold silently installs its
  origin's hooks — and its origin's ledger — into the copier's session. The kit therefore holds
  `.claude/settings.template.json` and `.claude/worker-net.settings.template.json` with `@ROOT@` and `@HOME@` placeholders,
  and an instance gets the filled files (→ **A scaffold ships its settings as a template, never live**). **The hook ledgers
  only its own tree's sessions**: a session whose project directory and cwd both lie outside the tree writes nothing to the
  ledger except the gate's own lines, marked `foreign-session(<dir>)`, and never archives the handoff; every decision is
  unchanged (→ **The hook ledgers only its own tree's sessions**).
- **A launch's own decisions read only the launcher's own words, and stopping a launch ends its worker.** A retry after an
  upstream rate limit is decided from the CLI's stderr and events, never from a tool result or the model's text; a
  stopped detached run stops the worker's scope too (→ **A launch's decisions are its own, and a stop reaches the
  worker**).
- **Host code never writes into a run directory through a name the worker could have made a link.** The launcher's working
  files stay outside the run; whatever the host puts in the run (logs, records, the checker's output) is written to a
  fresh name and renamed over the target, so a link there is replaced, never followed (→ **Host code never writes into a
  run directory through a name the worker could have made a link**).
- **A proof assistant's axiom audit never reads the artifact's own file.** The artifact is compiled in the sandbox; its
  compiled file is replayed through the kernel and audited by the kit's own program in a second sandbox call that runs
  no artifact code (→ **The axiom audit runs where the artifact's syntax cannot reach**).
- **What decides an earned tag is never in a run directory.** A referee run's question, claim and given bytes are
  `bin/new-run`'s binding in `data/referee-bindings/`; the cross-family rulings are the user's, in
  `data/cross-family-rulings.json`. A `referee.json` in a run with no binding never counts (→ **What decides an earned
  tag is never in a run directory**).
- **Change the hook only as a tested candidate, installed atomically, with no worker in flight.** The hook is live code for every
  sandboxed command and for the checker (→ **Change the hook only as a tested candidate**). **Test the real sandbox with fake
  binaries** rather than trusting a reading of its command line (→ **Fake binaries test the real sandbox**).
- **Every tool, hook command and test runs on the system interpreter the sandbox uses**, never the shell's
  (→ **Every tool, hook and test runs on `/usr/bin/python3`**).
- The agent-tool fields that would hide a launch from the hook are stripped from every orchestrator call rather than trusted to be
  omitted (→ **Agent-tool `name`, `isolation`, `team_name` are stripped**).

## 10. Outside checks — the operator's, never a gate

None of these is a required step, and none is an exit condition of any phase. They are called when the record says they tend to
pay, and the operator decides among them (an independence question is the user's, §4 item 6). Where each has paid off, in kind:

| check | when it tends to help | what it has found |
|---|---|---|
| **Outside-reader packet** (→ **Outside-reader packet after the second referee gap**) | after the *second* referee gap on the same sentence — the author has then failed twice. Not after a first gap | two sentence-level disputes each closed in one pass; in another, the reader found the defect the author had accepted twice |
| **Set-up audit of a brief** (→ **Set-up audit of a brief**) | before a solver brief carrying a new relaxation, a new list of conditions, or a new transcription of a source, where a wrong reading would make every claim of the run about the wrong object. Not for a brief that reuses a list already certified | five ways a brief could pass while wrong, for about twenty-five minutes of model time; a launch-blocking contradiction between two exit criteria; an input leak the author's own check had missed |
| **Handoff audit** (→ **Handoff audit by an outside model**) | after a session that changed method, or that committed record text the operator had not read first | thirteen findings on one handoff, four of them in text already committed; ten on another, including a packet whose own file names the data guard refuses |

The kit does **not** carry the source's wording that a handoff audit is "routine" after a method change: on this record it is
useful and it is still the operator's call (§12). An audit runs on the text as committed and is itself recorded as a no-worker run.

## 11. Working with the operator

- **Do what was asked; nothing more.** No unrequested files or documentation.
- **Never assume a question is a command.** A question gets an answer, and the work waits for the go
  (→ **Never assume a question is a command**).
- **Never read a permission more widely than its words.** When the words admit two readings and one of them changes a ruling,
  state both, act on neither, and let the user pick (→ **Never read a permission more widely than its words**).
- **Whatever the operator must see goes in the final message of a turn** (→ **Whatever the operator must see goes in the final message**).
- **When the permission classifier refuses, stop and say so.** Ask for a mode switch; never route around it
  (→ **The classifier stop**).
- **Read a tool's usage from its source**, never by running a launch or ledger tool with `--help`
  (→ **Read a tool's usage from its source**).
- **Commit with explicit paths**, never everything at once; commit messages come from a file, because a message naming a gated
  tool is refused. No `cd` inside a compound command (→ **No `cd` in a compound command**).
- **A session works on the tree it was opened in.** A `cd` that leaves the session's project directory is undone, and the kit and
  every instance have the same `bin/` and `tests/`, so a command meant for one tree runs quietly in another. An instance is
  driven only from a session opened in it; a kit methods session that upgrades an instance hands over the diff and an opening
  prompt, and a session in the instance applies them. Commands in a handoff name their tree (`git -C <root>`, absolute tool
  paths), and the ledger writers refuse a tree with no `LEDGER.log` (→ **A session works on the tree it was opened in**).
- **Lead with the finding and its tag; then what failed; then next steps.** If a session produced nothing, one line says so.
- An assessment pasted in from elsewhere is uncertified: check each point against the record and say which hold
  (→ **The user's analyst's notes are uncertified**). It is outside input: an intake record comes first (§8 "Outside input").
- **This kit ships its own examples.** A workspace copied from another carries the sibling's run numbers and claim ids in its
  worked examples, which point at files that do not exist here. Every example in an instance is that instance's own, or it is
  marked as coming from elsewhere (→ **A duplicated scaffold carries the sibling's examples**).

## 12. Dropped — and why

Each of these is in the source method and deliberately not in this kit.

| dropped | reason |
|---|---|
| **The subagent worker route** | a subagent inherits the orchestrator session's harness text — the auto-mode note, attribution guidance, a request for a closing report, and any MCP server's instructions. Only its refusal is kept, live in the hook (→ **Every worker is a headless main process**). |
| **Per-effort worker agent types** | built and retired with that route; an effort flag on the launcher does their work. |
| **Audit budget ≤ solve budget per cycle** | already removed upstream: a four-minute mechanical solve can earn four `[PROVED]` claims, and the cap would then forbid the two referee questions each one needs. Referee every `[PROVED]` claim (→ **Audit budget cap removed**). |
| **"Consent is per-call"** | superseded by batch consent: naming several things in one approval is one consent for exactly those things (§6). |
| **A standing analyst** | left out by ruling. The user may attach an ongoing analyst at their discretion; `FLOW.md` says so, and nothing in the method depends on one. |
| **"A handoff audit is routine after a session that changed method"** | reads like a default. Outside checks are the operator's discretion (§10). |
| **`TodoWrite` in the worker allowlist** | removed after the first live canary; the source's prose still lists it, the code does not. The code is right. |
| **"Agent types load at session start"** | only the settings half of that sentence held up in practice; agent types were picked up without a restart. Settings do bind at session start (§9). |
| **All problem content** | every claim, run, ladder score, problem statement, prior-art register, attack board and source. The ladder's *design* comes along; its scores do not. |
| **The problem-specific data check** | one branch of the data guard skipped a path belonging to one problem's third-party clone. An instance adds its own exclusions if it needs them. |
| **A required formal library** | a proof assistant is an optional module an instance links, never a copy. Every rule about it is conditional on the instance having one. |
| **Home-lab specifics** | hostnames, machine names, key locations, absolute home paths, and the owner's name in rules. Credentials never enter the tree; an instance's setup lists which keys the user must place. |
| **The sibling's history file** | the source's rules name an archived history file that exists only in its sibling. An instance's rules name only its own files (→ **A duplicated scaffold carries the sibling's examples**). |
