# Glossary

What each of the kit's terms means, with the section of `RULES.md` or `SCHEMAS.md` that defines or uses it.

Where this page and a normative file differ, the normative file is right ([conventions](../conventions.md)). Terms are
in alphabetical order; a term in *italics* inside a definition has its own entry.

- **`!` command**: a command the *user* types at the Claude Code prompt behind the shell-escape prefix `!`. It does
  not pass through the *hook*, which is what makes an *approval* given that way the user's
  ([RULES.md §6](../../RULES.md#6-approvals--the-gate), → **`!` commands do not pass through the hook**).
- **analyst**: a model session the user may keep, at their discretion, outside the trust chain, for design questions
  and second readings; the user may designate it the *operator agent*. It is no role of the method; what it hands in is *outside input*
  ([RULES.md, Outside input](../../RULES.md#outside-input); [§12](../../RULES.md#12-dropped--and-why)).
- **approval**: the user's act, bound to the exact bytes they read: a single-use record written by
  [bin/approve](tools/approve.md), valid for 30 minutes, naming a kind (launch, ledger, annotate, session), a key, a
  *manifest* and, for a launch, the flags. The tool it gates consumes it; any change to a bound byte, flag or id voids
  it ([RULES.md §6](../../RULES.md#6-approvals--the-gate)).
- **artifact**: the inspectable object that certifies a *claim*: a script, a Lean file, a text, or none
  (`artifact.type`), under the run's `output/` ([RULES.md §1](../../RULES.md#1-rule-zero);
  [SCHEMAS.md §1](../../SCHEMAS.md#1-outputclaimsjson--written-by-the-solver)).
- **batch consent**: naming several things in one approval, or in one instruction, consents to exactly those things
  and nothing beside them ([RULES.md, What consent covers](../../RULES.md#what-consent-covers)).
- **blocked root**: a path listed under `"blocked"` in `data/packet-rules.json`, a file or a directory with everything
  under it, kept out of every *packet* whole. A block beats an open root: a blocked path inside *open material* is not
  open ([RULES.md §8](../../RULES.md#8-the-record); [configuration](configuration.md#datapacket-rulesjson)).
- **brief**: `RUN/BRIEF.md`, the worker's task: a skeleton with fixed sections made by [bin/new-run](tools/new-run.md),
  filled by the *orchestrator* and linted before the gate ([RULES.md, The brief](../../RULES.md#the-brief)).
- **canary**: a *run* whose worker tests the *sandbox* and its own starting context instead of doing mathematics, from
  `templates/runs/canary-BRIEF.md`. Run 001 of a new *instance* is one; one precedes real work on every enabled *route*,
  and one follows any change to settings, the hook, an agent, a *harness note* or a *route*
  ([FLOW.md](../../FLOW.md#outside-steps--called-not-wired-in)). `RULES.md` §9, "Settings bind at session start", names
  only agents and settings ([RULES.md §9](../../RULES.md#9-the-sandbox--enforced-not-convention)).
- **checker**: [bin/check](tools/check.md), a script and not a model. It validates `claims.json`, runs every artifact
  in the worker's sandbox, audits Lean axioms from the compiled artifact after a kernel replay (never in the
  artifact's own file), runs declared *mutations* with `--mutate`, and writes `check.json`
  ([RULES.md §4](../../RULES.md#4-roles--three-plus-ad-hoc);
  [SCHEMAS.md §2](../../SCHEMAS.md#2-checkjson--written-by-bincheck-a-script-rulesmd-step-2)).
- **claim**: one statement a *solver* wants recorded: an object in `output/claims.json` with an id, a *claim tag*, a
  one-sentence statement, an *artifact* and the fields its tag requires
  ([SCHEMAS.md §1](../../SCHEMAS.md#1-outputclaimsjson--written-by-the-solver)).
- **claim tag**: one of `[PROVED]`, `[VERIFIED]`, `[NUMERIC]`, `[CONJECTURE]`, `[HEURISTIC]`, `[GAP]`, mandatory on every
  substantive statement, each with its bar
  ([RULES.md §2](../../RULES.md#2-claim-tags--mandatory-on-every-substantive-statement)).
- **cross-family read**: a referee read from the other *model family* than the *producer's*: a `certify` read for a
  `[PROVED]` claim, a `sentence` read for a `[VERIFIED]` or `[NUMERIC]` claim under `kit/claims/2`. Without a live hold
  from it the claim is PENDING. An unknown producer is met only by the user's ruling, in
  `data/cross-family-rulings.json` ([RULES.md §7](../../RULES.md#7-standing-rules-that-keep-cycles-convergent);
  [SCHEMAS.md §4](../../SCHEMAS.md#4-earned-tag--binmerge-computes-binledger-claims-enforces)).
- **crosslemma**: the project's name; in running prose, "the *kit*".
- **cycle**: steps 0 to 6, from the brief through the solver run, check, referees and verdict table to the record and
  the exit criteria, with a user gate at steps 0 and 4 ([RULES.md §5](../../RULES.md#5-the-cycle)).
- **digest**: the sha256 of an approval's kind, key, ids and manifest. [bin/manifest](tools/manifest.md) prints it;
  the *tap* route's `--digest` must match its opening hex characters ([RULES.md §6](../../RULES.md#6-approvals--the-gate)).
- **earned tag**: the tag a claim is recorded at, computed by [bin/merge](tools/merge.md) and enforced by
  [bin/ledger-claims](tools/ledger-claims.md) from the check and the live referee verdicts; FALSIFIED, BLOCKED and
  PENDING are not recorded ([SCHEMAS.md §4](../../SCHEMAS.md#4-earned-tag--binmerge-computes-binledger-claims-enforces);
  [RULES.md, Claim form](../../RULES.md#claim-form--the-schemas-are-law-schemasmd)).
- **egress proxy**: the host-side, CONNECT-only proxy of a Codex run without network. It passes only the exact
  provider hosts on its allowlist and logs every request; the sandbox reaches it through one bound unix socket
  ([RULES.md §9](../../RULES.md#9-the-sandbox--enforced-not-convention)).
- **environment file**: `kit-env.json` at an *instance*'s root: what a worker's sandbox gets beyond the system (*modules*,
  extra `PATH` directories), the two CLIs, and added *model families*. It is the user's: the hook refuses the
  orchestrator any write to it, as to `.kit-lean`, `.kit-sage` and `.kit-routes`, which `RULES.md` calls the
  environment files with it ([SCHEMAS.md §8](../../SCHEMAS.md#8-kit-envjson--the-instances-environment-file-the-users); [RULES.md §9](../../RULES.md#9-the-sandbox--enforced-not-convention);
  → **The environment files are the user's**; [configuration](configuration.md#kit-envjson-the-environment-file)).
- **evaluator**: the one role that may receive `data/locked/` inputs (answer keys, label maps); it emits scores only
  ([RULES.md §7](../../RULES.md#7-standing-rules-that-keep-cycles-convergent), "Controls are blinded and locked").
- **exception**: a file the user excepts from the packet rule by its sha256 in `data/packet-exceptions.json`
  ([bin/packet-except](tools/packet-except.md)); it may go into a packet although it carries blocked material, while it
  keeps those bytes ([RULES.md §8](../../RULES.md#8-the-record)). A departure from a rule that the user rules is
  also "recorded as an exception, never as a precedent" ([RULES.md §7](../../RULES.md#7-standing-rules-that-keep-cycles-convergent)).
- **gap**: a known hole. As a tag, `[GAP]` says exactly what must be shown; as a referee verdict, `gap` says the
  artifact certifies less than the English. A live `gap` verdict makes the earned tag `[GAP]` unless a live `falsified`
  verdict or a failed check decides it first
  ([SCHEMAS.md §4](../../SCHEMAS.md#4-earned-tag--binmerge-computes-binledger-claims-enforces);
  [RULES.md §2](../../RULES.md#2-claim-tags--mandatory-on-every-substantive-statement);
  [SCHEMAS.md §3](../../SCHEMAS.md#3-outputrefereejson--written-by-a-referee-run-exactly-these-six-fields)).
- **handoff**: `HANDOFF.md`, the pointer sheet one orchestrator leaves the next: paths, hashes, exit-criteria status, a
  disclosure of what it read, the preflight and the next session's opening prompt. Archived before it is touched; no
  history ([RULES.md §7](../../RULES.md#7-standing-rules-that-keep-cycles-convergent);
  [§8](../../RULES.md#8-the-record)).
- **harness note**: `RUN/HARNESS-NOTE.md`, the environment rules for a Codex or networked worker, copied from
  `harness/notes/` by `bin/new-run --harness`. It is part of the packet and must match the launch flags
  ([RULES.md §9](../../RULES.md#9-the-sandbox--enforced-not-convention); [configuration](configuration.md#harness-notes)).
- **hook**: `.claude/hooks/sandbox.py`, run by Claude Code on every tool call of every session in the tree. It binds
  and sandboxes workers, holds the orchestrator to the approval gate, and ledgers every call of a session of its own
  tree (a session from outside it leaves only the gate's own lines)
  ([RULES.md §9](../../RULES.md#9-the-sandbox--enforced-not-convention); [hook refusals](hook-refusals.md)).
- **instance**: one workspace made from *the kit* by [bin/new-workspace](tools/new-workspace.md) for one problem,
  outside the kit, with its own record, its copy of the rules and its filled settings. It is driven only from a session
  opened in it ([RULES.md](../../RULES.md#rules); [§11](../../RULES.md#11-working-with-the-operator)).
- **intake record**: `intake/IN-NNN-slug/`, holding `record.md`, `verbatim/` and `SHA256SUMS`, written on receipt of
  *outside input* before anything acts on it ([RULES.md, Outside input](../../RULES.md#outside-input), rule 1).
- **kit, the**: this repository, *crosslemma*: the rules, schemas, tools, hook and templates instances are made from.
  It carries no problem content, no claims record and no ledger log
  ([RULES.md](../../RULES.md#rules); [§12](../../RULES.md#12-dropped--and-why)).
- **ledger (`CLAIMS.md`)**: the claims record: append-only, one entry per claim under a global id `C-NNN`, appended by
  [bin/ledger-claims](tools/ledger-claims.md) on an approval, superseded and never edited. By rule a worker's view of it is
  [bin/claims-extract](tools/claims-extract.md)'s output; the tools refuse only the name `CLAIMS.md` in a packet ([RULES.md §8](../../RULES.md#8-the-record);
  [SCHEMAS.md §5](../../SCHEMAS.md#5-claimsmd-entry--appended-by-binledger-claims-run-id-on-the-users-approval)).
  The word has two senses in the normative files: `RULES.md` also says "the ledger" for `LEDGER.log` (in §8, §9 and
  §11). These docs say "ledger log" for `LEDGER.log` and "claims record" for `CLAIMS.md` where the difference matters.
- **ledger log (`LEDGER.log`)**: the append-only event log, `utc | actor | run | event | detail`, written by the hook
  and the tools ([event types](ledger-events.md)), one line per entry. Agents write it and never read it; the user
  reads it ([RULES.md §8](../../RULES.md#8-the-record)). The hook refuses the orchestrator a command naming it but a
  plain git add, commit, status or `diff --stat`, any write or edit of it, and a git command in the tree that prints
  file contents without naming plain, unprotected paths.
- **licence module**: a *module* that names licence servers, a host and a port each. It is mounted only for a run whose
  `RUN/.modules` ([bin/new-run](tools/new-run.md) `--module`) and whose launch ([bin/run-external](tools/run-external.md)
  `--module`, bound in the *approval*) both name it; its worker then reaches those servers through the *licence relay*
  and nothing else ([RULES.md §9](../../RULES.md#9-the-sandbox--enforced-not-convention); [licensed software](../guides/licensed-software.md)).
- **licence relay**: a process on the host, outside every sandbox, one per licence server of a run granted a *licence
  module* without `--network`. It listens on a unix socket in the user's private socket directory and carries each
  connection to its one fixed host and port, logging open, close and byte counts to `RUN/licence.log`, never contents.
  Inside the sandbox a forwarder on 127.0.0.1 at the server's port passes connections to it
  ([RULES.md §9](../../RULES.md#9-the-sandbox--enforced-not-convention); [the sandbox](../concepts/sandbox.md#the-licence-relay)).
- **live referee**: a well-formed `referee.json` of a run `bin/new-run` bound as a referee
  (`data/referee-bindings/<run>.json`), whose bound artifact and deps have the hashes `check.json` recorded and whose
  bound claim is the claim as it now stands; any other verdict is *stale* or invalid and does not count
  ([SCHEMAS.md §3](../../SCHEMAS.md#3-outputrefereejson--written-by-a-referee-run-exactly-these-six-fields)).
- **manifest**: path, size and sha256 of every file an approval binds, one *digest*, and the flags, printed by
  [bin/manifest](tools/manifest.md) (read-only) and by `bin/approve`. A launch manifest is every regular file of the run
  directory but the launch's own records ([RULES.md §6](../../RULES.md#6-approvals--the-gate);
  [layout](layout.md#run-directory)).
- **mathematics session**: a session that works the record (runs, referees, the ledger) and changes no tool, hook, test
  or rule; `RULES.md` calls it a working session
  ([RULES.md §7](../../RULES.md#7-standing-rules-that-keep-cycles-convergent)).
- **methods session**: a dedicated session that changes the method (tools, hook, tests, rules), recorded in the
  handoff; never a working session ([RULES.md §7](../../RULES.md#7-standing-rules-that-keep-cycles-convergent)).
- **model family**: Anthropic or OpenAI, or a family the *environment file* adds, read from a model's name (a family's
  word as a whole part of the name, or followed by a digit: `gpt5`, `opus4`); a run's
  family is read from the models that answered it, else from its approved `--model`. Answered by another family than
  the approved one, by two, or by a model of no known family, the producer is unknown ([SCHEMAS.md §4](../../SCHEMAS.md#4-earned-tag--binmerge-computes-binledger-claims-enforces)).
- **module**: a set of read-only mounts with `PATH` and environment additions, a self-test and a line for the brief,
  described in the *environment file*. One without licence servers is mounted for every worker and in the *checker*'s
  sandbox; one with them is a *licence module*. An instance whose environment file has no `modules` key gets its linked
  library and SageMath environment as the modules `lean` and `sage`
  ([SCHEMAS.md §8](../../SCHEMAS.md#8-kit-envjson--the-instances-environment-file-the-users); [configuration](configuration.md#modules)).
- **mutation**: an entry of `artifact.mutations`: a command that perturbs a copy of the evidence under `scratch/` and
  re-runs the checker, which must then exit non-zero (or with the given `expect_exit`) and, when
  `expect_stdout_contains` names the targeted part's FAIL line, print it. Without `expect_stdout_contains` a bare
  non-zero exit counts as a kill and `bin/validate-claims` warns; `RULES.md` §8 states it differently: a mutation kills
  only with its FAIL line. `bin/check --mutate` runs them; a mutation the checker survives fails the claim ([SCHEMAS.md §1](../../SCHEMAS.md#1-outputclaimsjson--written-by-the-solver);
  [RULES.md, Claim form](../../RULES.md#claim-form--the-schemas-are-law-schemasmd)).
- **note**: a `## C-NNN-note` line appended to `CLAIMS.md` by [bin/annotate-claim](tools/annotate-claim.md) on an
  approval: something learned about an entry that leaves its truth as stated, ending "(Note by the orchestrator, not
  refereed.)" ([SCHEMAS.md §5](../../SCHEMAS.md#5-claimsmd-entry--appended-by-binledger-claims-run-id-on-the-users-approval);
  [RULES.md §8](../../RULES.md#8-the-record)).
- **open material**: what can excuse text a packet shares with blocked material: the rules, tools, problem files, the
  claims record, and the `output/` of earlier runs that were launched or checked and are not blocked. A packet never is
  ([RULES.md §8](../../RULES.md#8-the-record)).
- **operator**: either the user or the operator agent, whichever directs the workspace ([RULES.md](../../RULES.md#rules),
  "Words").
- **operator agent**: an agent the user designates to act as operator (in practice, the analyst); it may give direction
  within the operator's list in [RULES.md §4](../../RULES.md#4-roles--three-plus-ad-hoc), and every approval stays the
  user's. P7, the charter for running one unattended, is not built.
- **orchestrator**: the session doing the work. Writes briefs and run directories, runs the scripts, shows tables and
  paths, hands off; never certifies its own work and never launches or appends without an approval
  ([RULES.md](../../RULES.md#rules); [§4](../../RULES.md#4-roles--three-plus-ad-hoc)).
- **outside input**: anything that enters the workspace other than through its own runs: another model session or
  workspace, a local agent, the analyst's text, and anything relayed from them. The user's own rulings are not
  ([RULES.md, Outside input](../../RULES.md#outside-input)).
- **packet**: what a worker sees: its `BRIEF.md`, `HARNESS-NOTE.md` and `input/`, scanned for blocked material before
  any launch ([RULES.md §8](../../RULES.md#8-the-record)). `RULES.md` §4 also uses the word for a self-contained
  question handed to an ad hoc role ([§4](../../RULES.md#4-roles--three-plus-ad-hoc)).
- **premise**: something a claim rests on besides its artifact, of kind kernel, classical, published, source, ledger or
  software; required for `[PROVED]` and `[VERIFIED]` under `kit/claims/2`
  ([SCHEMAS.md §1](../../SCHEMAS.md#1-outputclaimsjson--written-by-the-solver)).
- **producer**: the run whose worker made a claim; its *model family* decides which family the *cross-family read* must
  come from ([SCHEMAS.md §4](../../SCHEMAS.md#4-earned-tag--binmerge-computes-binledger-claims-enforces)).
- **queue**: runs approved together and launched one at a time by `bin/run-external --queue`, every approval used at
  the start ([RULES.md §6](../../RULES.md#6-approvals--the-gate)).
- **referee**: a fresh, sandboxed worker that reads one claim, its artifact, its declared deps and the problem statement,
  and writes `referee.json`: `holds`, `falsified`, `gap` or `unverifiable`, one pointer, a note of at most 3 lines; its
  question and the bytes it was given are recorded outside its run, in its binding
  ([RULES.md §4](../../RULES.md#4-roles--three-plus-ad-hoc);
  [SCHEMAS.md §3](../../SCHEMAS.md#3-outputrefereejson--written-by-a-referee-run-exactly-these-six-fields)).
- **referee question**: what a referee brief asks (`bin/new-run --question`). `certify` (the default): does the artifact
  certify the statement at the stated tag? `hypotheses`: does the English carry every restriction the artifact needs?
  `sentence` (script claims): does the English say exactly what the script asserts, on exactly the stated range? `RULES.md`
  §7 asks for a `certify` and a `hypotheses` read on every `[PROVED]` claim, and the earned tag enforces both, beside a
  live `certify` hold from the other family; `bin/close-run` prints the run for a missing question
  ([SCHEMAS.md §3](../../SCHEMAS.md#3-outputrefereejson--written-by-a-referee-run-exactly-these-six-fields);
  [RULES.md §7](../../RULES.md#7-standing-rules-that-keep-cycles-convergent)).
- **route**: a way to launch a worker: `--via anthropic`, `openrouter` or `codex`, with or without `--network`. An
  instance enables its routes when it is made ([RULES.md §9](../../RULES.md#9-the-sandbox--enforced-not-convention);
  [configuration](configuration.md#routes)).
- **run**: one unit of work in its own *run directory*: a solver, referee, evaluator or other worker, or a record with
  no worker ([RULES.md §5](../../RULES.md#5-the-cycle); [§10](../../RULES.md#10-outside-checks--the-operators-never-a-gate)).
- **run directory**: `workspace-N/runs/NNN-slug/`: `BRIEF.md`, `input/`, `scratch/`, `output/` and the records the run
  leaves. Run numbers are unique across workspaces; a run directory is launched once
  ([RULES.md §8](../../RULES.md#8-the-record); [layout](layout.md#run-directory)).
- **sandbox**: the enforced boundary around a worker: bound to one run directory by realpath, Bash in bubblewrap with the
  run directory read-write, the system and the instance's *modules* read-only, no network (but a *licence module*'s
  servers, through the *licence relay*, or the host's network on a run launched with `--network`), a clean environment,
  under enforced limits
  ([RULES.md §9](../../RULES.md#9-the-sandbox--enforced-not-convention)).
- **silent link**: a link of a claim's argument that no artifact checks, named in `silent_links`; naming it states an
  obligation and does not discharge it
  ([RULES.md §3](../../RULES.md#3-anti-self-deception--the-failures-that-actually-happen), item 8;
  [SCHEMAS.md §1](../../SCHEMAS.md#1-outputclaimsjson--written-by-the-solver)).
- **solver**: a worker that attacks the problem in a clean room and writes `output/result.md` and `output/claims.json`
  ([RULES.md §4](../../RULES.md#4-roles--three-plus-ad-hoc)).
- **source workspace, the**: the research project the kit was extracted from, on whether a 3×3 magic square of nine
  distinct perfect squares exists. Its run numbers and claim ids in the kit's files are provenance, not an instance's
  ([SCHEMAS.md, Provenance](../../SCHEMAS.md#schemas--claimsjson--checkjson--refereejson--claimsmd);
  [RULES.md §12](../../RULES.md#12-dropped--and-why)).
- **stale**: said of a verdict whose artifact or deps changed after the referee run was made; it does not count
  ([RULES.md §7](../../RULES.md#7-standing-rules-that-keep-cycles-convergent);
  [SCHEMAS.md §3](../../SCHEMAS.md#3-outputrefereejson--written-by-a-referee-run-exactly-these-six-fields)).
- **supersede**: to replace a recorded claim by a new entry whose `supersedes` names the old `C-NNN`; the old entry is
  never edited ([RULES.md §8](../../RULES.md#8-the-record);
  [SCHEMAS.md §1](../../SCHEMAS.md#1-outputclaimsjson--written-by-the-solver)).
- **tap**: approving by allowing the prompt the hook words from the bytes, when the orchestrator offers one plain
  `bin/approve RUN --digest <hex> -- <flags>`. Never "don't ask again"; only in the `default` and `auto` permission
  modes ([RULES.md §6](../../RULES.md#6-approvals--the-gate), → **The tap route needs `--digest`**).
- **user**: the human being who runs the workspace (see [roles](../concepts/roles.md#the-user)). Reads every file,
  approves, rules ([RULES.md](../../RULES.md#rules); [§4](../../RULES.md#4-roles--three-plus-ad-hoc)). Called
  "operator" in the kit before `kit-v0.6.0`; from `kit-v0.6.2` "operator" means the user or the operator agent.
- **verdict table**: `RUN/verdict.md`, written by [bin/merge](tools/merge.md): claim, tag, check, referee, earned, with
  the model families, notes, premises and formal statements ([RULES.md §5](../../RULES.md#5-the-cycle), step 4;
  [SCHEMAS.md §4](../../SCHEMAS.md#4-earned-tag--binmerge-computes-binledger-claims-enforces)).
- **worker**: a sandboxed model process in one run directory, launched headless by
  [bin/run-external](tools/run-external.md), never as a subagent. Read, Write and Bash only (plus web tools on a
  networked run) ([RULES.md](../../RULES.md#rules); [§9](../../RULES.md#9-the-sandbox--enforced-not-convention)).
