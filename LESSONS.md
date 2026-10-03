# Lessons: one line per rule, with the incident that made it (P1)

Written 2026-09-22 by the builder session from the records of two research workspaces on one open problem, whether a 3×3 magic
square of nine distinct perfect squares exists: the source workspace (its `ORCHESTRATOR.md` and `SCHEMAS.md` at `11d2212`, and its
fifteen archived handoffs) and its predecessor (its history file, `HANDOFF.md` and archives to 2026-09-18, and its setup handoff). Each line: **the rule** → the incident (run, method change "mc N",
date, MST) → what the rule prevents. "No recorded incident" means the rule came in with an earlier design (two earlier rule sets and a
sandbox experiment) and nothing on this record shows it being learned the hard way. Run numbers below
`139` are the predecessor's unless marked "(source)"; runs 096–106 and every "(source)" run are the source workspace's.
`RULES.md` (P2) points at these by the bold label.
The runs, claim ids, method changes and handoffs cited here belong to those workspaces' private records, which do not ship with
the kit; each line is the kit's own account of its incident.

## Rule Zero and the tags

- **Whoever produced the work does not get to certify it** → predecessor design; no recorded incident here; the whole apparatus is its
  minimum. Prevents the author's confidence standing in for a check.
- **Certify with artifacts wherever an artifact can; a fresh referee only where none can** → mc17 (2026-09-17 19:24): every Lean claim
  carried a copied list of library hashes that "looked like a lock but was only a label" (editing the library never touched the copy);
  replaced by a master list a script compares. Prevents a certification that cannot fire.
- **Mandatory claim tags; banned words without a tag** → predecessor design; run 015 (2026-09-16) tripped the banned-word scan with
  ordinary prose, so mc3 (owner 02:26, a knowing exception to the non-math-session rule) made `prose_flags` noted-never-blocking and let
  `[PROVED, sketch]` count as tagged. Prevents a prose filter from blocking a correct claim, and prevents untagged assertions.
- **`native_decide` axioms are named per declaration on Lean 4.32** → mc1 (2026-09-16 00:36): the axiom name changed from
  `Lean.ofReduceBool`; `bin/check` matches both. Prevents an undeclared `native_decide` passing the axioms audit.

## Anti-self-deception (the eleven)

1. **Prior art before novelty; a search is a bounded negative; a blocked surface is never "not found"; a "could not reach" list is checked
   against later findings before it goes in a prompt** → mc29 (2026-09-22, after run 094 (source)): a prior-art prompt carried a stale
   "could not reach" list; and run 022's C-031 (2026-09-16) was "a known result, independently re-derived" found only by pass 3 of the
   prior-art search. Prevents calling a known result new and prevents a search reporting a blocked site as absence.
2. **Cite or derive** → no recorded incident on the solver side; its referee-side form is mc16 (below). Prevents a half-remembered theorem
   carrying a proof.
3. **Re-find known objects before believing absence** → ladder 1's solver rungs (runs 011–013, 2026-09-16) and run 021, which re-found the
   rank-47 F2 scheme from the naive 64 before its census counted; run 018 closed on K-a because its engine never reached a known 48.
   Prevents an unvalidated search reporting a negative.
4. **Exact arithmetic** → no recorded incident; `bin/check` counts float tokens as an advisory. Prevents a rounding artefact becoming a claim.
5. **Symmetry / degeneracy audit before believing a search** → no recorded incident in a claim; run 039's audit (2026-09-16) F3 found a
   "closed C2×C2" that was not literally closed. Prevents double counts and missed boundary cases.
6. **Reversal test** → no recorded incident; it is in the referee brief ("try to derive the negation"). Prevents a framework that proves
   anything.
7. **No result-shaped prose; a kill with a reason is a good day** → runs 018, 019, 021, 022 (2026-09-16) all closed on kill criteria with no
   rank-47 claim and were recorded as complete. Prevents progress-shaped text standing in for results.
8. **Silent links first; every claim names them; a declared link is an obligation, not a discharge** → mc16 (2026-09-17 11:08, run 096
   Astra packet): ladder 4's c11 miss came from a referee accepting a declared `silent_links` entry; rule 2 rewritten, price-checked in runs
   110–115 (5/7 → 7/7 catch, 0/5 false positives), and applied to the record, where C-061 earned `GAP` (a composition step "so" was doing
   unsupplied work). Prevents a named obligation being read as a met one.
9. **Artifacts, not diligence; every consequential sentence maps to an inspectable object** → math-orchestrator-6 (2026-09-18) inferred
   from a 1.2 GB `peak_rss_tree` that no referee had compiled the file, told the owner so, then found in `launch.log` that all 14 had; and
   the setup handoff's verification record (2026-09-15) is why "ran-once" is not "works". Prevents narrative certainty.
10. **Mechanism or coverage** → no recorded incident; run 015's scout map (2026-09-16) and the "do not re-open B1 without a new move set"
    closure are the rule in use. Prevents more cases of the same mechanism.
11. **Speed is a region signal** → run 161 (2026-09-18) recorded "Region: mechanical (the solver took 658 s)" beside its claims; no failure
    recorded. Prevents fast mechanical results being read as progress on the hard region.

## Roles

- **Three roles; anything else ad hoc, invoked for one stuck thing, then put down** → owner 2026-09-17: the predecessor's scaffold "grew until
  five agents were needed to settle one count" (R0P). Prevents layers that need readers that need adjudicating.
- **The orchestrator never reads answer keys or label maps** → ladder 1 (run 003, 2026-09-16): the key was moved by rename from the design
  run's output into `data/locked/`, never opened; ladder 4 (2026-09-17): the orchestrator read the evaluator's report, which names the
  planted packets, and recorded that it may never referee those twelve. Prevents a blinded control becoming unblinded by the user.
- **The orchestrator prints a referee's note; never summarises it** → HISTORICAL 2026-09-17 08:08: on the owner's "show me what the ref
  said" the orchestrator read and explained the 048 note, disclosed as a deviation; the source's standing rule since is "print
  `referee.json` verbatim and say where the pointer leads". Prevents the interested party's paraphrase replacing the verdict.
- **Solver sees no prior attempts, no bench brief, no expected answer** → predecessor design; `bin/new-run` refuses inputs from other runs;
  R-3 (2026-09-18) made the exception explicit and on the record (mc23, `--input-approved`). Prevents a solver inheriting the last
  solver's errors and prevents an undeclared input.
- **Checker is a script, not an LLM** → predecessor design; no recorded incident. Prevents a check that argues.
- **Two referees per PROVED claim, one per question (`certify`, `hypotheses`), decorrelated by the question, not the model** → mc14
  (2026-09-17 08:33): the known overclaim 040/c3 was missed by `certify` under Fable (043) and Opus (053) and caught by `hypotheses` under
  Opus (054); its sibling 040/c2 caught once by `certify` (048); ladder 2 showed two models giving identical verdicts on all six packets.
  Prevents spending a second referee on a second model asking the same question.
- **A cross-family certify read** → the source's method change 59 (2026-09-29), from its user's rulings of 14:41 ("sol 5.6
  for cross family on anthropic runs, and opus 5.5 for cross family on openai runs"), 17:02 ("(b) for now: keep both same-family
  reads and add a cross-family certify read. Switch to (a) once the Sol-via-Codex certify reads have been compared with Fable's on
  about ten claims") and 17:16 (VERIFIED and NUMERIC claims too, "so VERIFIED is not a way around it"; an unknown producer blocks
  PROVED until ruled), relayed from analyst-drafted text; the brief behind them was not read here, and no incident of a
  same-family miss is on the record the kit read. Its canary 281 (a Sol certify referee via Codex) died at launch on the socket
  path (the lesson "The egress socket's host side is in a short private directory"), and canary 282, the same packet, held and
  exercised the route. Taken at `kit-v0.4` on the user's "59: make the change now" (2026-09-29), binding every run, since
  no instance had ledgered claims. It qualifies the lesson above: a second model does not replace the second question, and the
  cross-family read is a third read, not a substitute. Not yet calibrated: no OpenAI model has been through a referee ladder
  in the kit (`RULES.md` §7 "Calibrate before trusting"); the reads count before that as a recorded exception (user
  2026-09-29, `kit-v0.4.1`), since the read only adds a requirement. Also at `kit-v0.4.1`: the family is read from the models
  that answered, when the record has them (an Opus 5.5 run that fell back to Opus 4.8 is still Anthropic; one answered by
  another family is unknown); a new instance enables `anthropic,codex` by default and is warned when its routes cover one
  family. Prevents a claim certified only by the family that produced it.
- **A referee sees the artifact, its declared `deps`, and `PROBLEM.md`; nothing else** → mc2 (2026-09-16 00:36, owner: "a referee may see
  every file the claim declares it needs"); run 015's first check needed a resume to add `deps`. Prevents a referee reading the brief or
  the solver's reasoning, and prevents the orchestrator choosing what a referee sees.
- **A mutation kills only with its FAIL line** → the source's practice in its repair runs (its runs 304, 352, 357, 2026-09-29/30): a
  mutation counted as a kill whenever the checker exited non-zero, so a crash, an exception or an unrelated part's failure
  passed as proof that a range was exercised. A mutation now names, in `expect_stdout_contains`, the FAIL line its targeted
  part prints, and `bin/check --mutate` counts a kill only with the expected exit and that line; `bin/validate-claims` warns
  when a mutation names none. With it, from the same practice, the solver brief asks for every stated count to be asserted
  against a value fixed before the run (the source's referee gaps on printed counts), and for a table in `result.md` from
  each asserted part to its check and its killing mutation; `templates/runs/repair-BRIEF.md` and `restatement-BRIEF.md` carry
  the source's two forms for fixing such a claim. Taken at `kit-v0.4.7` (user 2026-09-30, "all approved"). From the
  source's method change 78 (its owner's two conditions and its analyst's two clauses), taken at `kit-v0.4.19` (user
  2026-10-01, "integrate the four improvements"): `expect_stdout_contains` is a substring test, so a pin asserts a printed
  value only if it ends the value (`count=17` also matches `count=170`; the skeleton's own example was that pin); FAIL
  lines are printed to stdout, since `sys.exit("FAIL …")` and an assert's message go to stderr, which the checker does not
  read; and no part's FAIL line occurs inside another's. Prevents a coverage claim certified by a mutation that broke
  something else, and a count pinned by a prefix of the wrong number.
- **A referee is given the ledger entries a claim rests on** → the source, 2026-09-29/30: three of its referee sets (on its runs 263,
  305 and 331) reported that they could not compare a premise's quotation with the ledger, since the entry was not in their packet
  (nor in the problem statement's list), and its orchestrator checked the quotations by hand; its user ruled the fix for a
  methods session (2026-09-30 07:34). Taken first here, at `kit-v0.4.5`: for a claim with `ledger` premises, `bin/new-run --role
  referee` writes `input/ledger-premises.md` with `bin/claims-extract --ids` (the extract's fixed rules; the user's
  exclusions still hold; a superseded entry is given and marked), and the brief tells the referee to compare every use of it with
  that statement. Prevents a premise's quotation passing unchecked because its source was not in the packet.
- **A referee of a text claim is given, and told to open, the library definitions the text quotes** → mc22 (2026-09-18, audit 152 (g) →
  §4a item 7): a text proof quoting a library statement could be refereed against the quotation alone. Prevents a misquoted definition
  passing.
- **Outside-reader packet after the second referee gap on one sentence** → C-005 (source, 2026-09-20: run 018's orchestrator-written
  sentence gapped; run 021 restated, held) and C-026 (source, 2026-09-21: run 066's c3 gapped; owner: "a second gap goes to an outside
  reader, not to a third wording" → run 073's packet closed it in one pass); the canonical packet is the predecessor's `RECONCILE-c3.md` (run 070,
  2026-09-17), sent after the author had failed twice, which found the defect the author had accepted twice. Prevents the author rewriting
  a sentence a third time.
- **The packet is the mechanism: self-contained, evidence both ways, the interested party's view last and labelled** → run 135's
  `DISPUTE-174.md` (2026-09-17, 619 lines, all sources verbatim) settled a dispute between two agents in one pass. Prevents a question that
  cannot be written down being handed to anyone.
- **Set-up audit of a brief before a solver launch that carries a new relaxation, list or transcription** → run 061 (source, 2026-09-21):
  its F4 found a leak the orchestrator's own check had missed (the check had looked only for run 005's traces); run 152 (the predecessor,
  2026-09-18) cost 25 minutes and found five ways a brief could pass wrongly; run 159 found a launch-blocking schema contradiction. Prevents
  every claim of a run being about the wrong object.
- **Handoff audit by an outside model, at the operator's discretion (not routine)** → run 059 (source, 2026-09-21), run 095 (source,
  2026-09-22: thirteen findings, four in committed text), run 106 (source, 2026-09-22: ten findings, one a `verify-data` refusal of the
  packet's own file names); the owner's ruling of 16:55 (kit HANDOFF §3) makes it discretionary, against the source's mc30 wording. Prevents
  a handoff carrying the writer's own misreadings forward, without wiring in a layer.

## The cycle and the gates

- **Cycle exit criteria written at step 0, checked mechanically at step 6** → predecessor design; run 159's audit found E3 unsatisfiable as
  frozen (a refutation would have been a script under K-b but c3 was frozen as PROVED text). Prevents a run closing on judgement.
- **One run at a time unless the user rules otherwise for named runs** → ladder 1 caveat (d) (2026-09-16): the owner overlapped runs and
  it was logged; "run them all" (2026-09-22 14:22) covered canaries 100–102 only. Prevents concurrent runs sharing state or the ledger
  interleaving.
- **Every launch and every ledger append consumes a byte-bound, single-use, 30-minute user approval; the tools refuse without it** → mc20
  (2026-09-18): run 149 launched ungated, then run 151 at 12:04 on "agree with all your changes. go", where "go" meant the edits under
  discussion and the launched brief carried edits the owner had not read; "two ungated launches in two sessions, each after a written
  rule against it"; owner: "this has happened over and over". Prose rules did not stop it; a refusal ("no owner approval for these hashes")
  is the stop. Prevents a misread go followed by an ordinary command.
- **The manifest is shown first; the approval binds bytes, ids and flags; any edit voids it** → the second half of run 151 (the brief
  changed after the words); canary 163's live test (a one-byte edit refused with the file named; wrong flags refused). Prevents approving a
  brief and launching a different one.
- **`!` commands do not pass through the hook, which is what makes the approval the user's** → owed from 2026-09-18, done 2026-09-22 13:44:
  the debug log held the orchestrator's `echo nonce-A` and not the owner's `echo nonce-B`. Prevents the gate resting on an untested
  assumption.
- **The tap route needs `--digest` from a manifest the user has seen; never "don't ask again"; the hook words the prompt** → a session of the predecessor
  (2026-09-18): the owner tapped Allow by accident on a Deny test ("a tap can be a reflex: measured"); an allow rule would make the tap
  silent. Prevents a habitual click standing in for reading.
- **Batch tap: one digest per run, in order; one mismatch refuses all** → mc27 (2026-09-22): math-orchestrator-6 found `--digest` took one
  target, so fourteen referee launches needed one ssh batch command by the owner. Prevents fourteen taps or an unbound batch.
- **Batch consent: "do all of X" covers all of X and nothing beside it; a go attached to another instruction covers that instruction only;
  silence is not approval; a user message approves what they had seen when it was sent** → owner 2026-09-18 07:38; run 151 (a go on
  edits read as a launch go); an orchestrator of the source (2026-09-22) wrote "tabled (11:47)" in a commit message when the owner had asked
  a question and not ruled (audit F1), and started a preflight the owner had not asked for (12:34: "I did not say to run the preflight").
  Prevents a permission being read more widely than its words.
- **`bin/lint-brief` before `bin/manifest`** → mc26 (2026-09-22, after run 086 (source)): the brief said "lists it in `deps`", the worker
  put `deps` at the claim's top level, the validator passed it, `bin/check` hashed nothing and a referee would have received no deps.
  Prevents a slot or a misworded field reaching a worker.
- **`bin/close-run` performs steps 2 and 4, prints step 3's and step 5's lines, launches nothing, appends nothing** → mc10 (2026-09-16):
  "one command replaces four plus judgment". Prevents a step skipped or a line composed by hand.
- **Anything that does not falsify something on the record is dropped, not backlogged** → predecessor design; no recorded incident.
  Prevents a backlog.

## Standing rules

- **The evidence boundary: a hypothesis is carried only if the English states it or the supplied material derives it; a referee's own
  derivation never counts; the same boundary governs `silent_links`** → mc16 (above): the alternative "needs a boundary between an obvious
  implication and a non-obvious one, which nobody applies twice the same way". Prevents a referee repairing the claim it was asked to judge.
- **Every English statement is written from the formal statement, never from a summary** → mc14 (2026-09-17): all five defective import
  statements (040/c2, c3, c5, c6, c7) "were written from the predecessor's prose summaries rather than from the Lean statements"; the
  defect was authorship, not mathematics. Prevents an English quantifier wider than the theorem's.
- **Formal statements captured beside the English in `verdict.md`** → mc15 (2026-09-17): "a fidelity read starts from the binder list
  instead of a file hunt". Prevents the adjudicator hunting for the type.
- **A headless referee finishes its checks in its turn** → the source's run 203 (2026-09-26): a referee ended its turn to wait on
  background jobs, so the run ended with no verdict; the source wrote a paragraph by hand into two later briefs, then made it
  part of every referee brief (its method change 49): run long checks in the foreground with a timeout or poll them in the same
  turn, and write `referee.json` before ending the turn. Ported at `kit-v0.3.4`. The solver brief carries the same paragraph
  (`kit-v0.4.6`), and since `kit-v0.4.19` (the source's method change 74, from its runs 346, 352, 357) says how to wait: one
  poll per tool call, a sleep of at most 60 seconds, then the progress file read, deliverables written first. Prevents a
  referee run that spends its budget and leaves nothing.
- **A sentence referee reads every script claim** → the source's method change 41 (2026-09-25 12:37): a script claim earned `[VERIFIED]`
  on the checker's pass alone, with no reader of whether its English said what the script asserted, and a coverage count could be
  written into a script after a first run printed it. `bin/new-run --question sentence` (script claims only) asks exactly that;
  under `kit/claims/2` a VERIFIED or NUMERIC claim is PENDING until a live sentence referee holds; every question's brief says an
  artifact certifying less than the English says is a `gap`, and checks published or source premises against their files;
  `bin/validate-claims` warns when a VERIFIED script appears to use a computer-algebra package. Ported at `kit-v0.3` (user
  2026-09-25, "I want it"). **Not calibrated** in the kit, and no ladder for it is named in the source's handoff, decisions or
  orchestrator files (2026-09-25): `HANDOFF.md` §6 item 12. First live read, the review instance's run 016 (2026-09-29): the solver
  had pinned its count with `expect_stdout_contains`, as the solver skeleton shows, which `bin/check` enforces, and the brief
  counted only the script's own asserts, so the referee returned `gap` on a correct count; since `kit-v0.3.8` (user: "a")
  the brief counts the claim's `expect_*` fields as the checker's assertions, and the frozen-count question applies to a pinned
  value as to an asserted one. Prevents a script's pass standing in for a sentence nobody checked.
- **Premises on every claim; the primary text quoted; a conditional marker** → the source's method change 40 (2026-09-25; its
  user's rulings 12:17 and 12:37): its entries rested on published theorems, notes taken as stated and other entries without the
  record saying so, and a premise could be cited from a secondary account of it. Schema `kit/claims/2` requires `premises` on
  every PROVED and VERIFIED claim; a published or source premise names the primary text and a verbatim quote with its location,
  both in `deps`, so the referee reads them; `bin/ledger-claims` writes a `Premises:` line and `(conditional: …)` in the entry
  header; a ledger premise is a `claim-deps` edge. `kit/claims/1` is accepted for earlier runs. Ported at `kit-v0.3` (user
  2026-09-25, "agreed"). The outside review (F3) found the exemption trusted a brief the worker can edit; since `kit-v0.3.1`
  a launched run's brief must still have the bytes its launch approval bound. Prevents a result's dependence on someone else's theorem being invisible on the record.
- **Dependencies between ledger entries are read by bytes and by name** → the source's method change 36 (2026-09-25): claim ids were
  the only link its record tracked, so an entry whose deps were three other entries' artifacts would not have been flagged when any
  of them was superseded. `bin/claim-deps` reads `CLAIMS.md`: X depends on Y when Y's artifact sha256 is X's artifact or one of its
  deps ("file"), or X's statement or silent links name Y ("names"); `bin/close-run` and `bin/ledger-claims` print the live direct
  dependents of any id a claim supersedes, never refusing. Ported at `kit-v0.3`. Prevents a superseded entry leaving its
  dependents standing unnoticed.
- **No packet carries blocked material** → the source's method changes 42, 47 and 48 (2026-09-25; its user's "c13: agree all,
  route a"): a content rule replaced blocks by source (no worker receives probabilities of success, rankings of routes, or
  evaluations of the record), enforced by a scan of every packet; an outside review of it (the source's run 163) found that packets
  could excuse each other, that files were read by name, and that excepted files counted as open, all fixed; the exception list
  became its user's alone, behind the hook. In the source the block list is written into the scanner. The kit makes it the
  instance's `data/packet-rules.json`, empty at `bin/new-workspace`, filled by the user with `bin/packet-block` (user
  2026-09-25, "agreed"); with no rules the scan does nothing and writes nothing. Ported at `kit-v0.3`. The outside review of
  `kit-v0.3` found the cache trusted on the launch path (F5), text over 50 MB compared by hash alone (F9) and exceptions that
  outlived their file's bytes (F10), all fixed in `kit-v0.3.1`; and that a glob gets past the hook's name-based gate on the lists
  (F6), recorded as deliberate forgery, outside what the gate claims to stop. `kit-v0.3.1` also blocks `DIRECTION.md`,
  `HANDOFF.md` and `handoffs/` from the start (user: "go with your rec"); a handoff audit's packet then needs an exception. From the source's method change 50
  (`kit-v0.3.4`): route-verdict words are an error from any packet file when `data/packet-rules.json` says `"verdicts": true`
  (new instances do) or gives its own pattern, because a verdict can reach a packet through open material, where the text scan
  cannot see it. From the source's method change 58 (`kit-v0.3.9`): a block beats an open root. The source blocked files
  under the open root `problems/` and inside a launched run's `output/`, and each still counted as open material, so its own
  text excused itself and the scan could never flag a copy; a blocked path inside open material is no longer open, and in the
  kit the matching lines of a line rule's file are not open either (the same defect, for the kit's second kind of block);
  `intake/` is blocked from the start. Prevents a worker's
  judgement being shaped by the record's own opinions of where the answer lies.
- **A worker's extract of the ledger is made by a tool** → the source's method change 52 (2026-09-26, its user's "let's do all
  four things"): a worker never receives `CLAIMS.md`, and the extract it received instead had been written by a throwaway script,
  run by run, with nothing to say two extracts followed the same rules. `bin/claims-extract` makes it by fixed rules (live entries;
  header, statement, declarations or artifact type, Claimed, Premises, Supersedes; notes verbatim), and `--through` reproduces an
  earlier one. In the source the entries and notes left out and the library prefix are written into the tool; the kit takes the
  exclusions from the user's list (`data/packet-rules.json` "extract", `! bin/packet-block --extract …`, behind the hook) and
  the library as `--library PREFIX` (user 2026-09-27, "do 52"). The extract names what it leaves out by id, never the
  user's reason. Ported at `kit-v0.3.5`. Prevents two workers being handed the record by different rules, and a left-out
  entry being left in by a script that forgot it.
- **A networked referee's brief carries the network paragraph** → the source's method change 46 (2026-09-25 14:22): the paragraph that
  scopes a networked referee's web access (read the published sources the artifact cites, compare each cited statement with how
  the artifact uses it, log every query, keep downloads, an unreachable source is an unverifiable step) had been added by hand to
  seventeen referee briefs. `bin/new-run` builds it into every question's brief for a run made with `--harness claude-net` or
  `codex-net`. Ported at `kit-v0.3`. Prevents a hand-copied scope line going missing from one brief.
- **The ChatGPT plan's usage limit is detected and reported** → the source's method change 45 (2026-09-25 14:22): a Codex run ended at
  25 minutes on the plan's usage limit ("You've hit your usage limit … try again at <time>"), a cap the launcher cannot see in
  advance, and the record did not say so. `bin/_ext.py planlimit` finds the event in `launch.jsonl`; `RECORD-EXT.md` says whether
  the limit ended the run; `EXIT-EXT` carries `plan_limit=` and the launcher warns with the reset time. Ported at `kit-v0.3`.
  Prevents a quota stop being read as the worker's own ending.
- **A queue stops at the plan's usage limit** → the source's runs 316–319 (2026-09-30 00:09): a queue of four Sol runs met the
  ChatGPT plan's usage limit; each run ended in 2–3 s on it, the queue released the next anyway, and all four were left holding
  launch records with their approvals spent (a run directory is launched once, so each had to be rebuilt). Since `kit-v0.4.5` the
  queue asks `bin/_ext.py queue-stop` after a failed run and, on the usage limit or the provider's capacity refusal, releases
  nothing more (`QUEUE-STOP` names the runs not released; they keep no launch record and go on a new approval); any other
  failure still does not stop the queue. Tested on the real queue loop in a throwaway instance. Prevents one quota stop burning
  every run behind it.
- **Nothing creates or removes files in a tree while its queue releases runs** → the source's run 295 (2026-09-29 21:00): its
  packet scan at release failed with `FileNotFoundError` and nothing launched, its approval spent with the queue's; its
  orchestrator had run the four suites and a commit meanwhile, and a file the scan was walking probably disappeared under it (not
  established). Since `kit-v0.4.5` a file of the scan's index (blocked or open material) that disappears after the walk listed
  it is taken as absent; the packet's own files stay strict. The practice stands: no suites, commits or file moves in a tree
  while its queue releases. Prevents a harmless change in the tree spending an approval.
- **Between an approval and its launch, no scanned file changes; blocked files describe a packet, never quote it** → the
  source's practice (its handoffs of 2026-09-30, "Learned this session"): its rulings file is blocked from every packet, and an
  orchestrator that quoted a pending packet's text there made the packet share twelve words with blocked material, so the
  launch's own scan refused it; and an edit to open or blocked material after the user's approval can change what the
  launch-time scan finds, for a queued run after its approval is already spent. Taken at `kit-v0.4.7` as practice, not a tool:
  while a run awaits its approval or its launch, write about its packet in a handoff, an intake record or any other blocked
  file by description, never by quotation, and edit nothing the scan reads. Prevents an approval spent on a refusal the
  orchestrator caused.
- **A queue for runs approved together** → the source's method change 44 (2026-09-25 14:12, its user's "c16: a"): runs approved in
  one batch launched one at a time, and a later run's 30-minute approval could expire while an earlier run worked. `bin/run-external
  --queue RUN…` checks every run by a dry run, then consumes every approval into one queue record (all or nothing) and releases each
  run once, just before its launch, only with the approved flags and byte-identical files; a refused or failed run does not stop
  the queue; `QUEUE-START` and `QUEUE-RUN` ledger lines; `--detach` runs the whole queue as one user service. The
  source's outside review found the record good for a fixed 24 h; it now lives for the sum of its runs' wall caps plus 30 minutes
  (its method change 48), so a queue cannot outlast the launches it was approved for. Ported at `kit-v0.3`. The
  outside review of `kit-v0.3` (F4) found the release read `launched` and rewrote the record with no lock, so two callers could
  both release one run; since `kit-v0.3.1` each run is released by an atomic rename of its own token. The same review found (F7) that the host's own
  checks (the sandbox installed, the network settings, the route's key) refused only after the approval was spent, so a queue
  could spend all of them on one missing file; since `kit-v0.3.1` they run before any approval, and a queue's per-run
  pre-check (`--check`) runs them too. The lifetime is derived in `bin/_approval.py` from the approved flags (F12).
  Prevents a batch approval decaying into a race against the clock.
- **One approval for several notes; a replaced approval is announced** → the source's method change 43 (2026-09-25; its user's
  "multiple ! approvals at once"): fifteen notes needed fifteen `!` approvals, and an `&&`-joined pair of them approved only the
  first (a probe found the tool writes both; the likely cause was the quoting of a note's apostrophe at the prompt).
  `bin/approve --annotate-batch FILE` (a JSON list of `{id, text}`, every note printed in full) is one approval, consumed by
  `bin/annotate-claim --batch FILE`, which appends all or none; a second approval for the same kind and key says that it
  replaces the unused one. Ported at `kit-v0.3`. Prevents approvals multiplying past what the user will read.
- **A note says whose it is and does not vouch for the entry** → the source's method change 37 (2026-09-25): fourteen of its notes ended
  "The truth as stated is unchanged", an assertion by the orchestrator that no referee had read. `bin/annotate-claim` refuses a note
  saying the entry's truth is unchanged (before the approval is touched), ends every note with "(Note by the orchestrator, not
  refereed.)", and has `--dry-run`, so a refused text never costs an approval. Ported at `kit-v0.3`. Prevents an unrefereed note
  reading as a certification.
- **Computer algebra is an optional module, and its results need a certificate** → the source's method change 39 (2026-09-25; its
  user's rulings 12:17 and 12:37): PARI/GP, mwrank, Singular, Macaulay2, msolve and SageMath were installed for workers, with the
  rule that a package result earns `[VERIFIED]` only through a certificate an exact script re-checks without the package, or two
  independent packages agreeing; else `[NUMERIC]`. SageMath is a conda environment outside `/usr`, so the source mounted it
  read-only at its own path with a shim at `/opt/kit/bin/sage`; each program was run inside the sandbox and its canary 162 passed.
  The kit makes the mount an optional module (user 2026-09-25, "agreed, optional module"): `bin/new-workspace --sage PATH`
  writes `.kit-sage`, read from the file and never from the environment; a declared module that has vanished is a
  `bin/verify-data` finding. Ported at `kit-v0.3`. Prevents a package's output standing in for a proof it did not give.
- **Lean names ending in a prime** → the source's method change 51 (2026-09-26): Lean prints `'A.foo'' depends on axioms: …` for
  `A.foo'`, and `bin/check`'s pattern stopped at the prime, so three declarations of one of its runs had no axioms line and
  failed. The name is now everything up to the last quote before the fixed tail. Ported at `kit-v0.3.4`. Prevents a correct
  Lean claim failing its check on its name.
- **Every Lean signature is captured** → the source's method change 35 (2026-09-25): Lean prints a declaration's name relative to the
  namespaces the file opens, and an artifact may `#check` a declaration itself; the parser matched full names only and read the whole
  log, so two of the source's runs lost signatures. `bin/check` prints a marker before its own `#check` lines, reads only after it,
  and matches a printed name to the first declaration that equals it or ends in `.<name>`. Ported at `kit-v0.3`. Prevents a
  verdict table missing the formal statement it exists to show.
- **Method changes never in a math session; a dedicated methods session; recorded** → the predecessor: "R0P auditing R0P is what did not
  converge"; the exceptions are on the record as exceptions (mc3 2026-09-16; mc19 2026-09-18, "by knowing waiver and not a precedent").
  The source's cap of one change per five cycles was overridden once ("do all", 2026-09-22) and then removed by its user
  (2026-09-23 21:00 and 2026-09-25 12:17, its method change 33): no limit on the number of changes or on how often methods sessions
  happen. The kit follows (user 2026-09-25, "change to match ud"). Prevents the method drifting under the pressure of a result,
  without rationing the sessions that fix it.
- **Audit budget cap removed; referee every PROVED claim** → mc19 (2026-09-18 00:52): a four-minute mechanical solve earning four PROVED
  claims would have been forbidden its eight referee reads. Prevents a budget rule blocking required checks.
- **Fresh orchestrator per cycle; the outgoing one closes, records, and says a fresh session starts; the fresh one writes the next brief
  from the record** → owner 2026-09-16 20:05–20:08: orchestrators had "repeatedly prompted the owner for a launch go at the boundary";
  orchestrator-37 did it for run 038 before the owner caught it. Prevents the run's design inheriting the outgoing orchestrator's live
  reading of results, and prevents compaction mid-cycle.
- **The writer runs its own handoff preflight, verbatim, before calling the handoff done** → 2026-09-17: the first gate written expected
  a clean tree, impossible because the hook appends to the ledger on every call, the gate's own included; the next session stopped
  correctly. Prevents an instruction nobody has executed being handed on as a fact.
- **Every backticked tree path in a handoff exists, checked by a script** → mc29 (2026-09-22): "the Boyer path error: handoff paths are
  checked by a script, not by the author's `ls`" (`bin/verify-data` docstring; standing-list item (c) "`ls` handoff paths"). Prevents a
  pointer sheet pointing at nothing.
- **Handoffs restate their labels in full, never a shorthand** → "line B" drifted between the 2026-09-20 16:06 and 20:18 handoffs
  (source; lines 112 and 115) until an orchestrator of the source (2026-09-22) carried its definition verbatim "so it does not drift again".
  Prevents a name meaning two things two sessions apart.
- **Calibrate before trusting: a ladder of known results with planted errors, measuring recovery, catch and false-positive rates** →
  ladders 1 (runs 003–014, Fable, 2026-09-16), 2 (026–031, Astra), 3 (058–063, Opus, 2026-09-17), 4 (082–095 and 097–115, the overclaim
  ladder for `hypotheses`); Opus was not used as a referee until ladder 3 had been run. Prevents a pipeline's verdicts meaning something
  before they have been measured.
- **Controls are blinded and locked; only an evaluator run receives `data/locked/`; the orchestrator handles scores only** → ladder 1's key
  (run 003) and ladder 4's (`KEY.md` written to `output/`, moved unopened); `bin/verify-data` finds a copied key by hash under any name.
  Prevents a control leaking into a solver or the user.
- **A ladder is a coverage challenge, not a rate; small denominators; the designer saw the trap list** → ladder 4's caveats and Astra's
  (2026-09-17). Prevents 5/7 being read as recall.

## The record

- **`LEDGER.log` is append-only (`chattr +a`); agents write, never read; the hook enforces it for the orchestrator** → mc24 (2026-09-18):
  magic-orchestrator-4 tried to grep the ledger for a run's launch flags; the live test of the change was a denied `tail`. Prevents the
  orchestrator reading its own record back as evidence, and prevents any edit.
- **Only a plain `git add`/`commit`/`status`/`diff --numstat` may name the ledger, each alone** → the source's preflight (2026-09-22): a
  compound command naming it was refused while building an audit packet; nothing ran. Prevents a compound command touching the ledger.
- **`CLAIMS.md` is append-only; a changed truth is a superseding claim, never an edit or a note** → C-054 → C-059 (2026-09-17), C-056/57/58 →
  C-060/61/62, C-061 → C-064; 040/c2 stays un-ledgered as the GAP-earning wording it is. Prevents the record saying two things.
- **A changed novelty or an audit finding that leaves the truth as stated is a note (`annotate-claim`)** → mc12 (2026-09-16): C-031 was
  found to be a known result after ledgering; audit 039's findings on C-041/C-047/C-049/C-050 needed recording without changing truth.
  Prevents editing an entry and prevents a supersede for a non-truth change.
- **`HANDOFF.md` is archived before it is touched, never only rewritten; committed at every handoff** → mc6 (owner 2026-09-16 20:55):
  HANDOFF.md had only been committed when the owner directed a commit, "so uncommitted rewrites were recoverable only from the mirrored
  transcripts". Prevents a lost handoff version.
- **`HANDOFF.md` holds the current pointer and nothing else; read whole with the Read tool, never `@HANDOFF.md`** → mc21 (2026-09-18):
  the line-limit instruction ("read lines 1–344") was "inside the file it governs" (§6b, 09:25); the history moved to
  `handoffs/HISTORICAL-…` (1,341 lines) by script, unread by the session that moved it. Prevents a session needing to know how much of
  the file to read before reading it.
- **The opening prompt is in every handoff and repeats the requirement** → owner 2026-09-18 12:49: "so that it propagates without anyone
  remembering it". Prevents the next session starting on a pasted commit message (an orchestrator of the source did, 2026-09-22 11:40).
- **One workspace per problem; run numbers unique across workspaces** → owner 2026-09-16 22:24, runs 040–047 moved to `workspace-2/`;
  all tools resolve runs by name. Prevents two problems' runs interleaving.
- **The Lean library has a master list; `--write-lean-manifest` is the deliberate act of accepting an edit; every `check.json` records the
  library state** → mc17 (above); its first real edit (`Dplus.lean`, 2026-09-17 20:00) was reported by name before acceptance. Prevents a
  library edit silently changing the evidence under a ledgered claim.
- **No record file (`BRIEF.md`, `CLAIMS.md`, …) may be copied into a run's `input/` under its own name** → run 039 (2026-09-16):
  `ORCHESTRATOR.md` copied into an audit packet, renamed after; run 106 (source, 2026-09-22): ten `BRIEF.md` copies in the packet,
  refused by `verify-data`, renamed `brief-copy.md`. Prevents a worker seeing what looks like its own brief or the record.
- **Held sources are hashed before they are read; a worker's downloads are hashed, not committed** → run 094 (source) did it by hand, mc25
  made it `RECORD-EXT.md`; sources under `problems/<p>/sources/` with `SHA256SUMS`. Prevents an unrecorded source.
- **A ledgered run's check record is kept** → the source's method change 56 (2026-09-29): a `CLAIMS.md` entry cites
  `RUN/check.json` by its generation time, and a later `bin/close-run` rewrote a run's record after three of its claims had been
  appended, so the entries pointed at a record that no longer existed. `bin/check` now keeps the current record of a run with
  any ledgered claim as `check.<generated>.json` (a `CHECK-KEPT` ledger line) before re-checking, and never overwrites a kept
  one. Taken at `kit-v0.3.9`. Prevents a ledger entry citing evidence that was silently replaced.

## The sandbox

- **`CLAUDE.md` is injected in full into every worker; the rules file is not named `CLAUDE.md`; both user-scope `CLAUDE.md` files are
  excluded** → canary 001 (`001-context-canary`, 2026-09-16, opus, 25 calls): the worker received the full `~/.claude/CLAUDE.md`, the full
  project `CLAUDE.md`, qmd MCP instructions, other run names and the hostname; the laptop had no user-global file, "which is why zodiac
  never hit this"; canary 002 clean. Prevents the home-lab and rules text reaching a worker.
- **Workers have Read, Write, Bash only: no Edit, Glob, Grep, TodoWrite** → setup 2026-09-15/16: Claude Code validates Edit input before
  hooks run, a substring oracle on any file; TodoWrite removed after canary 001. Prevents a worker probing files it cannot read.
- **First `Read` binds a worker to one run directory; Read/Write elsewhere denied by realpath; Bash rewritten into bwrap with the run dir
  rw, no network, clean env** → zodiac design, ported 2026-09-15; canaries 001/002 (eleven correct denials: exists-vs-not identical
  errors, symlink, `../`, `/proc/1/root`, nested `unshare`/`bwrap`). Prevents escape and existence oracles.
- **`bwrap --hostname sandbox`** → canary 001 saw `hostname=nix`. Prevents a host name leaking.
- **Limits are enforced, not promised** → mc9 (2026-09-16, audit 039 F9: "8-thread cap uncertified; 'CPU s' is summed wall time").
  Prevents a brief asking a worker to honour a cap.
- **A worker's tools come from the user's environment file** → the user, 2026-10-01: "people using this kit will
  likely have different software tools with different requirements. we need to generalize", and on licensed software, "I
  want to implement the network route now". The kit had two tools hard-coded across six files (Lean and SageMath), one
  path to Codex's binary, and one Python's `/etc` directory; the source had added a third tool (Magma) the same way. Since
  `kit-v0.4.24` to `kit-v0.5`, `kit-env.json` describes modules generically: Lean and SageMath are two of them, and an older
  instance keeps its mounts byte for byte. A module that names a licence server is granted per run, bound in the approval,
  and reaches only that server through a relay the worker cannot redirect; `bin/check-env` reports what a machine offers.
  The tools stay on `/usr/bin/python3` (user: "a. keep", against the design's first draft; → **Every tool, hook and test
  runs on `/usr/bin/python3`**). Prevents a new tool needing a hook edit, and a licence or a credential directory reaching a
  worker.
- **The environment files are the user's** → found by reading the hook while generalizing the kit's software
  assumptions (2026-10-01, pending item P-1): the hook decides what to mount into every worker's sandbox, and what to put
  on its PATH, from `.kit-lean` and `.kit-sage`, and nothing refused the orchestrator a write to them, so a path written
  there (a home directory) would have been mounted read-only for every worker. A test showed all twenty writes and
  commands allowed. Since `kit-v0.4.22` the hook refuses the orchestrator any write to `kit-env.json`, `.kit-lean`,
  `.kit-sage` and `.kit-routes`, and any command naming them but a plain read or plain git; the user edits them by
  hand. Prevents an orchestrator widening every worker's sandbox with an ordinary file write.
- **The orchestrator reads neither the locked data nor the approval records, and its searches reach none of them nor the
  ledger** → pending item P-4 (the kit, 2026-10-01; user "yes"): the hook refused a Read of `LEDGER.log` by name, but a
  Grep with no path, run from the tree root, printed its lines; nothing refused a Read of `data/locked/` or of the
  approvals directory. Tests showed all three allowed. Since `kit-v0.6.6` the hook refuses Read, Grep and Glob inside
  `data/locked/` and the approvals directory, any command naming `data/locked` but a plain `bin/new-run … --role
  evaluator` or plain git, and a Grep rooted above the ledger, a locked file or an approval record unless its glob or
  type filter matches none of them. Residual: a recursive search typed in a Bash command walks the same files, since
  the hook matches names, not what a program reads (pending item P-9). Since `kit-v0.6.8` an `.ignore` at the instance's
  root names all three, so ripgrep and the Grep tool skip them by default; `grep -r`, `find` and `rg --no-ignore` still
  walk them. Prevents an ordinary search reading an answer key or the log.
- **An orchestrator types into no other pane and touches no mailbox** → the kit's evaluation of Clatter, the machine's
  inter-session bus (2026-09-30, `HANDOFF.md` §6 item 26): the hook refused a message or a keystroke that named the approval
  tool, but let an instance orchestrator run `tmux send-keys` with text from a file, or a bare Enter, into any pane (one that
  may hold a pending permission prompt, or the user's input line), and write into any session's Clatter mailbox, where
  `from` is self-declared. The source's user approved the narrow fix and asked the kit for the tested version: since
  `kit-v0.4.10` the hook refuses an orchestrator keys or buffers into a pane (`send-keys`, `send`, `paste-buffer`,
  `load-buffer`, `set-buffer`), any touch of `~/.claude/clatter/` but through its dispatcher `bus.sh`, and the dispatcher's
  `mode` and `clear`; peers, ask, send, broadcast, recv, status and doctor stay. A worker's sandbox has neither tmux nor the bus
  (probed). Not closed by this: the relay's own Enter on a pending prompt (a live test by Clatter's agent, 2026-09-30, found
  that it approved one; Clatter v0.1.3 types only into an empty input box and defers otherwise), and a session outside
  every instance (an analyst's) that receives an approval command as text (a user-level guard, the user's). Prevents an
  orchestrator answering another session's prompt or forging another session's message by an ordinary command. Since
  `kit-v0.4.13` (the user's ruling of the analyst's point 2, `HANDOFF.md` §6 item 27 (a)) the send script `bus-send.sh` is
  allowed too, because Clatter's own inbox tells a session to answer through it with `--reply-to` (a threaded reply, which
  the dispatcher cannot give), but not with its `--from` or `--from-session`, which set any sender name and session id. The
  check drops quotes and backslashes first; a flag built from a variable passes it: this stops an accident, not a forger.
  Since `kit-v0.4.19` (the source's method change 69, "any touch" in its owner's words) reading counts: no Read, Grep or Glob
  under `~/.claude/clatter/` (another session's mailbox, the relay's log), and no Grep or Glob rooted above it, which would
  walk into it; a `~` path is expanded before the check (a Write to `~/.claude/clatter/…` had passed it).
- **A kill-all runs only where it cannot reach past the run** → the source's review of its port of `kit-v0.3.7`
  (2026-09-30, relayed by the user): the Codex script ends with `kill -KILL -1`, safe only because the sandbox has its own
  process namespace (`--unshare-all`); outside one it kills every process of the user's Unix account (tmux, every session, the
  user services), and nothing but an indirect dry-run check stood between a later edit and that. Since `kit-v0.4.9` a test
  reads the worker's process namespace from inside the sandbox and fails if it is the host's (shown failing with the
  namespace removed), and the line itself runs only when the script's namespace differs from the host's, passed in when the
  sandbox is built (tested with `kill` shadowed, on the host and in a fresh namespace). The same class of risk in the CPU
  cap's sweep (`kit-v0.4.6`): it now kills only inside this run's own transient scope (`run-*.scope`). Prevents a cleanup
  line becoming a machine-wide kill after an unrelated edit.
- **The whole-run CPU budget is enforced** → the source's run 346 (2026-09-30): 11.13 CPU-hours against a budget of 8, only flagged
  `over_cpu_cap` afterwards, while every solver brief stated the budget as "enforced by the sandbox"; the sandbox enforced a rate
  (CPUQuota), memory and a per-command `ulimit -t`, not the total. The kit had the same sentence and the same gap. Since
  `kit-v0.4.6` `bin/limits-exec` watches the run's cgroup and at the budget sends TERM to the launcher's process (Claude:
  `timeout` passes it to the worker; Codex: `_ext.py` stops the worker as at its other caps, keeping its session file), then
  after `cpu_grace_seconds` kills everything left in the scope, background jobs included: exit 152, `cpu_cap_hit` in `usage.json`
  and on `EXIT-EXT`; never retried. Tested on a real systemd scope with real burners. Prevents a brief stating a cap that
  nothing enforces.
- **Agent-tool `name`, `isolation`, `team_name` are stripped from every orchestrator Agent call** → run 003 (a `name` replaced
  `agent_type` in the hook input and every tool was denied, 0 calls); canary 024 (2026-09-16): the Astra orchestrator added
  `isolation: worktree` and Claude Code's worktree guard refused every bwrap-rewritten command. Prevents a launch that the hook cannot see.
- **Headless launches carry `--strict-mcp-config --mcp-config no-mcp.json`** → canary 001 (qmd instructions reached the worker);
  canaries 024/025 clean. Prevents user-scope MCP instructions in a worker.
- **MCP servers denied project-wide (`deniedMcpServers`)** → canary 102 (source, 2026-09-22): a subagent from an interactive session
  received the instructions of qmd and the claude.ai connectors; owner 14:40 "fix". Prevents connector text in any session of the project.
- **Settings bind at session start; a settings change needs a restart or a headless test, then a canary** → canary 103 (source): a subagent
  of the session that made the MCP change still saw qmd's instructions. Prevents trusting a change the running session has not loaded.
- **Every worker is a headless main process (`bin/run-external`); the hook refuses worker subagents** → mc5 (2026-09-16 09:44: canary
  024's Astra subagent cited the harness's subagent note over the brief and wrote no `result.md`) and mc31 (2026-09-22 14:55: canary 103, a
  subagent, carried the auto-mode note, attribution guidance, a closing-report request and qmd's instructions; canary 105, headless, none).
  Prevents harness text reaching a worker.
- **A headless worker is recognised by `KIT_WORKER_RUN` in its environment, pre-bound to that run** → mc5 (the source's name
  was `MATHS_WORKER_RUN`); a networked worker by `KIT_WORKER_NET=1` (mc25; the source's `MATHS_WORKER_NET`), in the environment because "the worker cannot change it; a file in the run directory would not do".
  Prevents a worker flipping its own mode.
- **`bin/run-external` checks `--effort` per route** → 2026-09-22 (mc25): Codex accepted `--effort bogus` silently. Prevents a run at an
  unknown effort.
- **No run method shows memory or skills** → canary 098 (source): a headless worker's start-up listed 18 skills and an auto-memory path (as
  runs 081 and 086 had); `--disable-slash-commands`, `CLAUDE_CODE_DISABLE_AUTO_MEMORY=1`, `CLAUDE_CODE_DISABLE_BUNDLED_SKILLS=1`; canaries
  100/101 showed none. Prevents skills and memory reaching a worker.
- **A brief may not allow more tool calls than `--max-turns`; the default is 300** → mc28 (2026-09-22, run 081 (source): the brief allowed
  150 calls, the launcher's default was 80; owner 13:37 remark, 14:23 ruling). Prevents a worker cut off below its brief's budget.
- **A Codex worker's commands run apart from Codex** → this session's Codex canary 005 in the review instance (2026-09-25, GPT-5.6
  Sol): through `/proc/1/fd/0` and `/1` a worker read the host-side prompt and the launch log; reproduced here with the kit's
  real sandbox, a worker *rewrote* the transcript (the host file held only its forged line). On the Codex route the model
  process runs inside the sandbox, the worker's commands ran beside it as the same user in the same process namespace, and
  Codex's stdout was the host's log file itself; the same exposure let commands read the user's token (ruled acceptable on
  2026-09-22) and reach the model provider through the egress proxy on a no-network run. Since `kit-v0.3.1` (user:
  "yes"): `.claude/sandbox/kit-shell`, installed as `/opt/kit/bin/bash` (first on `PATH`, the sandbox user's login shell and
  `$SHELL`), runs each command in a nested `bwrap`
  with its own process namespace and `/proc`, Codex's home an empty tmpfs, and no network on a run without it; Codex's output
  reaches the host through pipes, copied with a sha256 chain that `RECORD-EXT.md` checks. Mount order matters: a fresh `/proc`
  goes after the root bind, or the outer one covers it. **Residuals, named:** Codex's in-process tools (its patch tool) act as
  the Codex process, so a model could append to the transcript pipe or edit the session log, though never rewrite what the
  host has copied. The first live test (canary 006) showed Codex 0.155 ignoring both `$SHELL` and a login shell named
  `kit-shell` and running `/usr/bin/bash -lc …`, the first `bash` on its `PATH`; the pipes held (chain matched), the nesting did
  not. Hence the name `bash`, confirmed live by the review instance's run 007 (2026-09-25): every command ran as
  `/opt/kit/bin/bash -lc …`, nested (the marker set, pid 1 the inner `bwrap`, six processes visible), the token unreadable,
  the proxy unreachable, the chain matching; a command's writes to the descriptors it could see landed only in its own
  captured output. The ud orchestrator then suspected, and a test here confirmed (2026-09-26), that the egress proxy's unix
  socket (`/opt/kit/egress.sock`, bound on a no-network run) stayed reachable from the nested sandbox: a read-only mount does
  not stop a `connect()` to a socket, and the command's own network namespace blocks only TCP; a command got `200 Connection
  established` to `chatgpt.com:443`. Since `kit-v0.3.3` the wrapper covers the socket with `/dev/null` on such a run, and the
  test dials it. Prevents a worker editing the record of what it did.
- **The egress socket's host side is in a short private directory** → the source's run 281 (2026-09-29, a no-network Codex
  referee canary): the launch died at bind with "AF_UNIX path too long", after its approval was spent; the proxy's socket was
  `.claude/state/ext/<run>/egress.sock`, 110 bytes for that root and slug, over Linux's 107. Nothing reached the model; the
  defect was latent because earlier no-network Codex runs had short slugs. The kit had the same code (a test here reproduced the
  error with a long slug). Since `kit-v0.3.9`, from the source's method change 60: the socket is `$XDG_RUNTIME_DIR/kit-egress/`
  or, with that unset, `/tmp/kit-egress-<uid>/` (mode 0700, refused otherwise), named by run number and a hash of the run
  path, removed at exit; only the socket file is bound in; neither directory is visible or connectable inside, for Codex or
  its commands (tested for both places); a Codex run with no exit record is recorded as never started. The source's canary
  282 held on it. Prevents a launch that the approval allows and the operating system refuses.
- **A run directory is launched once** → the outside review of `kit-v0.3` (F2): a relaunch renamed the earlier transcript to
  `launch.<time>.log` *after* the approval, inside the run directory, where the manifest's exclusions hid it and the new worker
  could read it; an earlier worker's `output/` stayed too. This session had already sidestepped it by hand (canary 002, refused
  at capacity, was retried as a new run 004). Since `kit-v0.3.1` `bin/run-external` refuses, before the approval, a run holding
  any earlier launch record, and since `kit-v0.3.4` any file in `output/` (the source's stricter form, its method change 55).
  Prevents a solver seeing a prior attempt through its own run directory.
- **A launch approval binds its flags** → the outside review of `kit-v0.3` (GPT-5.6 Sol, 2026-09-25, finding F1): an approval given
  without `-- <flags>` recorded none, and the check then skipped the flags, so an ordinary Claude or OpenRouter launch could run
  any model, effort, prompt, turn or wall cap on an approval of the bytes alone; a test locked the behaviour in. Only networked
  and Codex launches required bound flags. Since `kit-v0.3.1` (user: "yes") `bin/approve` and `bin/manifest` refuse a launch
  without flags naming `--model`, and a stored record that bound none refuses at launch. Prevents the user's word on the bytes
  standing in for a word on how they run.
- **Networked and Codex launches need their flags bound in the approval and a matching `HARNESS-NOTE.md`; every such run leaves
  `RECORD-EXT.md`** → mc25 (2026-09-22): the three one-off harnesses (runs 025, 026, 094 (source)) had been recorded by hand. Prevents a
  networked run without a record or with an unapproved network.
- **The Codex egress allowlist is exact hosts, analytics off** → canary 096 (source): 497,893 bytes uploaded to `ab.chatgpt.com` through a
  subdomain rule (metrics, from the binary's endpoint name; payload not seen); owner 14:04 "tighten then 097". Prevents an unlisted host.
- **Transcripts are written outside the worker's reach and moved in at exit** → owner 2026-09-22 14:32 item 2. Prevents a worker altering
  its own transcript.
- **Long runs launch detached as a user service** → 2026-09-16: the orchestrator's background Bash tool has a hard 1-hour timeout that
  would kill a launcher (`setsid nohup` era); 2026-09-22 item 3 made it `--detach`. Prevents a run dying with the tool call.
- **The effort the model's requests actually carried is recorded on every route** → canaries 098–102 (source) showed `"effort":"low"` on
  every request of the Claude routes whatever was approved; item 5 (14:32). Prevents an approved effort being assumed.
- **Every tool, hook and test runs on `/usr/bin/python3`, never the shell's `python3`** → item 7 (2026-09-22): the shell's `python3` is 3.14,
  the sandbox's 3.12. Prevents a test passing on the wrong interpreter.
- **A worker's upstream rate limit is retried and resumed by the launcher** → run 034 (2026-09-16): OpenRouter returned a rate-limit error
  object under HTTP 200, which Claude Code reported as malformed and did not retry. Prevents a run lost to a transient.
- **Worker context residuals are named, not hidden** → canaries 002 and 025: owner email (account-level), cwd, bwrap command line, a
  harness note preferring Bash. Prevents a claim of a clean context.
- **A scaffold ships its settings as a template, never live** → this kit's own P3, 2026-09-22: copying the source's
  `.claude/` into the builder's working directory installed the source tree's hooks into the builder's *own* session, pointed
  at the source root; the next Bash call was gated by the source's approval hook and 35 `CALL` lines were appended to the
  source tree's ledger before it was caught (append-only, nothing else there changed). Prevents a copied workspace hijacking
  the session of whoever copies it and writing into the tree it came from.
- **The run directory's parent chain is writable inside the sandbox, and nothing written there reaches the host** → the kit's
  P5, 2026-09-22, canary 002 on the Codex route: the worker wrote `../000-nope/output/probe.md` via its patch tool, declared an
  escape and aborted its canary; the host held no such file, and the same write inside the hook's own bwrap on the Claude
  route landed in bwrap's private root tmpfs and vanished with it. Not an escape, a residual, shared with the source: a worker
  can believe it escaped, and files written there are lost silently. Candidate hardening for a methods session: remount the
  parent chain read-only after the binds, with a canary. Prevents a canary's self-report being read as a host escape without
  checking the host. (Closed by the next lesson; the check against the host stays.)
- **The sandbox's root is remounted read-only after the binds** → the source's method change 32 (2026-09-22 19:59, its user's
  "implement #6, test them"), ported to the kit at `kit-v0.3`: both worker sandboxes (the hook's Bash bwrap and the Codex bwrap)
  end their binds with `--remount-ro /`, so the directories bwrap makes for mount points (the run directory's parent chain,
  `/home`, `/opt`, `/`) cannot be written; the run directory, `/tmp` and the Codex home are mounts of their own and stay
  writable. The source's canaries 107 (Claude) and 108 (Codex) passed; `tests/test_ext.py` probes both sandboxes with real
  `bwrap`. Residual, found by a throwaway instance under `/tmp` (2026-09-25): the sandbox's own `/tmp` is a tmpfs
  the remount does not reach, so a tree under `/tmp` keeps its parent chain writable inside (still reaching nothing on the host);
  instances live under `~/workspace`, and the probe skips such a tree. Prevents a write that succeeds inside and vanishes, and a
  worker's belief that it escaped.
- **The hook ledgers only its own tree's sessions** → the settings incident of the lesson two above, from the receiving side:
  the source's method change 32 made its hook write nothing to its ledger for a session whose project directory
  (`CLAUDE_PROJECT_DIR`) and cwd both lie outside the tree, except the gate's own lines (`DENY-GATE`, `ASK-APPROVE`), marked
  `foreign-session(<dir>)`; decisions are unchanged, workers are never foreign, and with neither directory known the session
  counts as the tree's own (fail closed). Ported at `kit-v0.3`. Prevents one tree's ledger recording another tree's work.
- **A launch's decisions are its own, and a stop reaches the worker** → the kit's code audit (2026-10-02, P-12 H4, H5;
  `T5P12RetryTrigger`, `T5P12StopEndsTheWorker`): `bin/run-external` retried, with fresh CPU caps, whenever the transcript
  held a rate-limit phrase, the worker's own output included; and `systemctl --user stop kit-run-NAME` left the worker
  running, since `bin/limits-exec`'s scope lies outside the service's cgroup (shown live on 2026-10-02). Now the retry
  reads the CLI's own words only, and the scope is named and stopped on TERM. Prevents a worker buying itself caps, and
  a stopped run that is not stopped.
- **The approval holds until the worker starts, and binds the claim** → the kit's code audit (2026-10-02, P-12 mediums;
  `T37P12MediumRest`, `T5P12HostWrites`, `test_launched_once_counts_the_licence_log_and_the_outbox`): the approval was used,
  then the launch set up for seconds to minutes (a gateway, Codex's catalog) with nobody reading the bytes again;
  `licence.log` and a written outbox were unhashed and not counted as an earlier launch; a verdict bound the artifact's
  bytes but not the claim's, so a statement could widen under a holding referee; a PROVED claim missing from
  `check.json` showed as earned; CLAIMS.md appends took no lock and spent the approval before the entry was built; and
  `bin/verify-data` hashed every run file though a copy has its original's size. Now `_approval.verify_launch` just
  before each route starts, both names in the launched-once check, `claim_sha256` in the binding, the check required for
  PROVED, `L.claims_lock()` from the next id to the write, and a size filter before hashing. Prevents an approval that
  certifies bytes the worker never saw, and a verdict on a claim nobody refereed.
- **The axiom audit runs where the artifact's syntax cannot reach** → the same audit, shown live on 2026-10-02 (Lean
  4.32; `T38P12LeanAudit`): `bin/check` appended `#print axioms` to the artifact's file, and a `macro_rules` in the artifact
  made a theorem proved by `sorry` print "does not depend on any axioms", exit 0, check pass. Lean 4.32 also keeps
  precomputed axiom lists in each compiled file, which the artifact's compile-time code writes. Now the compiled
  artifact is replayed through the kernel (`leanchecker`) and its declarations walked by `harness/lean/KitAudit.lean` in a
  sandbox call that runs no artifact code. Prevents a kernel certificate the artifact wrote about itself.
- **A launcher fails cleanly and touches nothing it has not checked** → the kit's code audit (2026-10-02, P-12 low
  findings; `T40P12LowLauncher`, `test_a_run_name_used_twice_is_refused`, `test_detach_touches_nothing_before_its_unit_check`):
  a run directory made by hand under a name already used shared the first's host state, approvals and binding; `--detach`
  emptied a running launch's output before asking whether it ran, and spliced a path into a `bash -c` script; a queue
  that failed partway did not say which approvals it had spent; a failed `bin/new-run` left a half-built run; the
  networked worker's settings lacked `deniedMcpServers`. (`egress-fwd`'s sockets, also found, were measured: no leak, as
  CPython closes each when its thread ends; left as is.) Prevents a failure that leaves the next run worse off.
- **The ledger is guarded by name; git is guarded by what it prints** → pending item P-13 (2026-10-02, found fixing P-12
  H6; route (a), the user's "cheap route"; `T18P13GitContents`): the hook refused commands that *name* `LEDGER.log`, so
  `git show HEAD`, `git log -p` and a bare `git diff` (the ledger always has uncommitted lines) printed it, and the proof
  instance's old answer keys from its history. Now a content-printing git command in the tree must name plain,
  unprotected paths. What other programs read stays out of the hook's sight (`cat L*` is still a tripwire's matter);
  route (b), encrypting each line to the user's key, would close that, and is not taken. Prevents the commonest
  accidental read of the record.
- **A hook that does not load refuses, and the limits a worker runs under are the approved ones** → pending item P-11
  (c), (d), (g) (2026-10-02; `T17P11P10`, `T42P11Settings`): the hook re-read `RUN/.limits`, which the worker writes; a
  hook broken by an edit made no decision, which Claude Code takes as allow; and the launcher took a settings file that
  named the hook anywhere as one that registered it. Now a launch-time copy outside the run, a load check that exits 2,
  and the registration parsed. Prevents a sandbox that holds only while nobody edits it.
- **A change to what a worker can do is a change to its briefs** → pending item P-15 (2026-10-03; `T44P15Foreground`): to
  close a race, `kit-v0.6.20` set a worker's `run_in_background` false, and the solver and referee briefs went on telling
  workers to start long jobs in the background and poll them, which then blocked until the call's timeout; the source's
  briefs had just adopted that option. Found eight tags later, writing the source's prompt; no canary exercised it. Now
  the briefs say foreground, an hour at most per call, longer work in resumable parts. Prevents a worker following its
  brief into a call that cannot do what the brief says.
- **Small gaps in the gate, closed** → the kit's code audit (2026-10-02, P-12 low findings; `T39P12LowGate`,
  `T16P12LowGate`): `bin/ledger` kept line breaks, and one call wrote a forged `CLAIM` line of its own (shown); a hard
  link in a run passed the launch manifest; `bin/ledger-claims` re-checked the artifact's hash but not its deps'; a
  model name took a family by any prefix ("solar-1" OpenAI's by "sol"); and an unwritable ledger made the hook refuse
  every orchestrator call, the ones to fix it included. Now one line per entry, hard links refused, deps re-hashed, a
  family word a whole token (or one followed by a digit), and gated calls only refused. Prevents a small gap becoming
  the way round a large rule.
- **The guards cover every route and every place** → the kit's code audit (2026-10-02, P-12 mediums; `T15P12Medium`,
  `T36P12Medium`): the orchestrator's Write or Edit of `LEDGER.log` was not refused; a Glob rooted above the protected
  files was (the check was Grep's only); an unreadable `kit-env.json`, or a refused `locked_dir`, moved the hook's and
  `bin/new-run`'s locked guard to `<root>/data/locked` while the keys lay at the default place; and a launch flag given
  twice was sorted into the approval while `bin/run-external` took the last. Prevents a guard that holds on one route
  and not its twin.
- **"A plain git command" is a list of options, not a pattern on how it starts** → the same audit (H6; `T14P12High`):
  `git diff --stat -p LEDGER.log` passed the ledger's allowance and printed its lines, as `--patch`, `-U`, `--output=`,
  `git status -v`, `git add -p` and `git commit -v` could. Prevents a read of the ledger or the locked data dressed as a
  commit step.
- **Host code never writes into a run directory through a name the worker could have made a link** → the kit's code audit
  (2026-10-02, P-12 C2; tests `T33P12HostWrites`, `T5P12HostWrites`): `bin/limits-exec` wrote `usage.json` into the file a
  worker's link named, `_ext.py record` wrote `RECORD-EXT.md` the same way, and `bin/check` wrote its logs into a directory
  the checked script had replaced with a link; the outbox drains (hook and `_ext.py`) truncated a file through a link that
  appeared after their check. Now `_lib.write_in_run` (no link followed below the run; a fresh name renamed over the
  target), the launch's working files in a temporary directory, the drains on `O_NOFOLLOW`, and a worker's Bash in the
  foreground only. Prevents a worker turning a host write into a write anywhere the user can write.
- **What decides an earned tag is never in a run directory** → the same audit (P-12 C3; `T34P12Bindings`): any run's
  `output/referee.json` counted as a referee's, a solver's own included; the question came from `RUN/.ref-question`, the
  bytes a referee saw from its own `input/` (a deleted `input/claim.json` skipped the staleness check); the user's
  cross-family ruling was read from the solver's run directory; and a session file a worker left at
  `launch.rollout.jsonl` decided the models a run was answered by. Now `data/referee-bindings/<run>.json`
  (`bin/new-run`'s), `data/cross-family-rulings.json` (the user's), both refused to the orchestrator's hand, and the
  launcher clears the session-file names it does not sort itself. Prevents a producer certifying its own claim (Rule Zero).
- **A tool that runs a shell command is gated as Bash is** → the same audit (P-12 C1): the gate examined Bash only, so a
  Monitor call could read the ledger or the locked data or name the approval tool; the user-level guards are matched on
  `Bash` alone. Prevents a second shell route around the gate.
- **Change the hook only as a tested candidate, installed atomically, with no worker in flight** → the hook is live code for every
  sandboxed command and for `bin/check`; six hook changes on 2026-09-22 each went candidate → `HOOK_UNDER_TEST=` → `cp` + `mv`; a golden
  replay of the worker branch guards the port. Prevents a half-written hook opening or closing the sandbox mid-run.
- **Fake binaries test the real sandbox** → `tests/test_ext.py` (mc25) runs a fake `codex` inside the real bwrap; the first probe
  "went through the proxy by accident (curl honours proxy variables)". Prevents trusting a reading of the bwrap line.

## Working with the owner

- **Never assume a question is a command** → owner 2026-09-17 08:09; an orchestrator of the source (2026-09-22) read a question as a ruling in a
  commit message; magic-orchestrator-4 (2026-09-18) added work "as though silence were approval". Prevents work starting on a question.
- **Never read a permission more widely than its words; deviations before choices; two readings → state both, act on neither** →
  magic-orchestrator-4 (2026-09-18 14:20): a K-c change made beyond what was ruled, put to the owner, kept; ORCHESTRATOR "What consent
  covers". Prevents an approval covering what it did not name.
- **Whatever the operator must see goes in the final message** → source §5 standing rule (2026-09-21/22). Prevents a finding buried mid-chain.
- **The classifier stop: when the permission classifier refuses, stop and ask for a mode switch; never route around it** → 2026-09-16 (two
  hook edits refused as self-modification; the owner applied the patch); 2026-09-20 (a `--dangerously-skip-permissions` file refused;
  `bin/new-run` sometimes denied outright); 2026-09-22 13:45 (three writes refused: "Expose Local Services", no reason, "Self-Modification";
  owner "switched"). Prevents the safety layer being defeated by the thing it guards.
- **Read a tool's usage from its source, never by running a launch or ledger tool with `--help`** → magic-orchestrator-4 (2026-09-18) ran
  `bin/run-external --help`, which died on "--model is required" before doing anything; `-h` now answers first. Prevents a launch by
  curiosity.
- **No `cd` in a compound command; commit with explicit paths, never `git add -A`; commit messages from a file** → 2026-09-22: a `cd` left
  the shell in `.claude/agents`; the hook refuses any command naming the approval tool even in a commit message (`git commit -F`).
  Prevents a stray cwd and prevents the ledger or a key being committed.
- **A session works on the tree it was opened in; commands name their tree; a tree with no ledger is refused** → 2026-09-23, the kit's
  a kit methods session upgrading the proof instance from the kit directory: a standalone `cd` into the instance came back
  "Shell cwd was reset to" the kit (tested: a `cd` inside the session's project directory persists, one outside it is undone), so
  eight preflight commands ran against the kit, where the same `bin/` and `tests/` exist; `bin/verify-data` ran there and created a
  stray `LEDGER.log`, because every ledger writer opened the file in append mode. The user reports the same failure several
  times in the kit's build and in the source. Both the builder (P5) and this session drove an instance from the kit, outside the
  instance's hook. Prevents a check passing on the wrong tree and a record written where nobody reads it.
- **A duplicated scaffold carries the sibling's examples; the kit ships its own** → the source's `ORCHESTRATOR.md` scaffold note
  (2026-09-19): every run number, claim id and path in a worked example "refer to the sibling … and to nothing in this tree"; it names
  `handoffs/HISTORICAL-…` as if local. Prevents a reader following an example into a file that does not exist.
- **The user's analyst's notes are uncertified; check each point against the record and say which hold** → source §5 (2026-09-22).
  Prevents a pasted assessment becoming a ruling.
- **Outside input has an intake record first** → the source's outside input W1 (2026-09-26 to 09-29): relayed into the workspace
  from outside its runs, it framed a run through the run's brief and operations list; its statements were quoted as
  premises in that run's output and in a restatement's, a byte copy of its extract sat in the run's `output/`, and one
  ledgered claim's last clause rested on W1's ceiling, an outside result never verified there (cut from tool extracts by the
  source's method change 62). Because those copies lay in open material, they excused the W1 text in any later packet. The
  source's method changes 57 and 58 (2026-09-29): an intake record with the verbatim text and its hashes before anything acts
  on outside input; each item record-only until its user classes it; a premise only through a verify-or-refute claim or a
  ruled conditional source premise; framing only under a ruling, tagged; analyst-drafted text marked; the families of the
  inputs a claim rests on counted for independence; `intake/` out of every packet; its records checked by `bin/verify-data`.
  The source back-registered eight records. Taken at `kit-v0.3.9` (user 2026-09-29: "adopt"), without the source's own
  items. Prevents an outside result entering the record as if this workspace had established it.
- **State a cost before spending it; a worker's cost figure for a routed model is not trustworthy** → canary 024: Claude Code's $0.73 was
  computed from its own price table; run 039's "$8.44" likewise. Prevents a spend estimate read as a meter.
- **A wall-clock cap on every route** → the source's method change 38 (2026-09-25 12:37): only the Codex route had a wall cap (default
  1 h), and Claude workers were stopped by hand-set timers. `bin/run-external` now caps every launch: default 4 h on the Claude
  routes, where the worker runs under `timeout --kill-after=60` with one deadline across its rate-limit retries, and 2 h on Codex;
  `EXIT-EXT` carries `wall_cap_hit=`. Ported at `kit-v0.3`; not yet exercised on a live launch in the kit or the source (a canary
  needs an approval). Prevents a worker running unbounded in time.
- **A Codex worker's tool calls are capped** → `HANDOFF.md` §6 item 10 (the user, 2026-09-22 20:36, found in the source): a
  Claude launch is capped by `--max-turns`, a Codex launch was capped only by its wall clock, since the Codex CLI has no turn
  cap, so the approval bound no turn count for it and a Codex worker in a loop ran until the wall cap. User 2026-09-28,
  option (a): the host's copy of the transcript counts the tool calls (every item but messages and reasoning) as they start,
  and past `--max-turns` stops the worker (exit 125, `turn_cap_hit=1` on `EXIT-EXT`; for Claude the same field reads Claude
  Code's own `error_max_turns`). The brief-versus-cap check now applies to Codex too. A call is counted when it starts, so the
  one past the cap may begin before the stop. Seen live on 2026-09-29 (the review instance's run 009, exit 125), where the stop
  also lost the session file, and so the record of model and effort, because the whole sandbox was stopped before its
  script copied it (the wall cap, run 011, the same); since `kit-v0.3.7` a cap sends TERM to the codex process only, the
  script copies the session files and ends whatever the worker left running, and the sandbox is stopped 30 s later only if it
  has not ended. Prevents an unbounded Codex worker and an approval that binds a cap nothing enforces.
- **A Codex worker has no sub-agents** → the proof instance's canary 015 (2026-09-25): under `--disable multi_agent` the worker
  had `collaboration.*` tools and spawned a sub-agent in its sandbox, so the harness note's "There are no other agents" was
  false. Root cause, found offline on 2026-09-28 with `codex debug prompt-input` (codex-cli 0.158.0): the model catalog sets
  `multi_agent_version: v2` for gpt-5.6-sol and gpt-6-sol, and that turns the tools on whatever the feature flag says; no
  feature flag removes them (each of the 34 still on was tried), and `agents.max_threads=0` is rejected by `codex exec`. Codex
  now reads a copy of its binary's own catalog with the key removed (`-c model_catalog_json`); `codex exec` then records
  `multi_agent_version: disabled` where it recorded `v2`. Before the approval, Codex renders the launch's prompt and features
  offline with the launch's own settings and the launch is refused if either still offers sub-agents. The same canary recorded
  the sub-agent's session file as the run's (the first one found): the main thread's is now the one whose id is the chained
  transcript's thread id, any other is kept as `launch.rollout.sub-N.jsonl` and named on the record. Not yet seen on a live,
  logged-in launch, where Codex may fetch its catalog from the provider. Prevents a worker the brief says is alone having help.
- **The model a worker ran on is recorded** → the proof instance's canaries 014 and 001 (2026-09-23, 09-26): Opus 5.5's
  safeguards flagged the canary brief at the first turn and Claude Code answered the rest of the session with Opus 4.8
  (`model_refusal_fallback`, 1 message from 5.5, about 35 from 4.8), under an approval that bound `--model opus`, and nothing
  in the record said so. The models that answered are read from the run's own transcript (each assistant message's model,
  every fallback event; Codex: the main thread's turn contexts) onto `EXIT-EXT` (`models_seen=`, `model_fallback=`),
  `RECORD-EXT.md` and a warning; `bin/close-run` and `bin/ledger-claims` print a `MODEL:` line for the run and for each
  referee behind a claim. Recorded and flagged, never refused (user 2026-09-28). On the Claude routes the requested name
  (an alias, a routed id) is not compared with the answering model's id, so only a fallback event or a second model is caught. A recalibration (`HANDOFF.md` §6 item 12)
  needs this: a ladder could otherwise measure a model other than the one it names. Prevents an approved model read as an
  observed one.
- **A parent session's routing never reaches a worker** → the source's caveat of 2026-09-16, `HANDOFF.md` §6 item 5: the
  launcher dropped the parent's `CLAUDE*` variables only, so a parent routed elsewhere (`ANTHROPIC_BASE_URL`, a token, a model
  override) would have routed a `--via anthropic` worker too. Every `ANTHROPIC_*` variable is dropped as well; the OpenRouter
  route sets its own on the worker's command line (2026-09-28). Prevents a worker answered by a provider nobody approved.
- **No spending cap on any run** → the source's user, 2026-09-25 12:17 (its method change 34): `--max-budget-usd` (default 40)
  was a cap computed from the same price table, so it capped a figure that is not a meter; the launcher no longer passes it and
  refuses `--budget`; the turn cap and the wall cap are the caps. Ported at `kit-v0.3` ("change to match ud", 2026-09-25). An agent
  user's allocated budget (`HANDOFF.md` §9 item 5) needs a real meter, which this was not. Prevents a false sense of a
  spending limit.

## Schemas and tools (SCHEMAS.md)

- **Unknown or misplaced fields are errors** → mc26 (run 086 (source), above). Prevents a silent no-op field.
- **Optional `artifact.mutations`; `bin/check --mutate`; a coverage claim without a mutation test is NUMERIC, not VERIFIED** → mc8
  (2026-09-16, audit 039 F7): run 037's `summarize47.py` "never asserts 240"; run 136's strata scripts never asserted their own case counts
  either (pinned by `expect_stdout_contains` plus three mutations, 11/11 failed as expected). Prevents a checker that only prints counts
  certifying coverage.
- **`bin/validate-claims` is one piece of code for worker and checker; copied into every solver run; run last** → mc7 (2026-09-16): two
  of three metadata resumes (015 `deps`, 035 c6/c8) were form errors; run 037's E1 self-check gave the first clean first check. Prevents a
  resume for a form error.
- **`referee.json` has exactly six fields; a note over 3 lines or 600 chars is INVALID and does not exist** → run 006 (`run` field was
  the referee's own run, INVALID, re-run as 010); runs 042/044/045 (2026-09-16, notes of 702/872/711 chars; the brief had omitted the
  character bound → mc13). Prevents an unbounded finding that needs another reader.
- **A verdict is bound to the artifact copy the referee saw; a changed artifact or dep makes it STALE** → the fixture record (2026-09-16
  07:27Z) and mc2/mc17. Prevents a verdict outliving its object.
- **Earned tag: falsified > check fail > gap > PROVED needs every live referee to hold; PENDING is not recorded** → predecessor design;
  `close-run` names a PROVED claim with one referee and does not refuse it (owner decides). Prevents disagreement needing an adjudicator.
  Since `kit-v0.6.1` (the kit's pending item P-3, where `RULES.md` §7 and the code disagreed; user 2026-10-01 "B1-6: yes to
  all"): PROVED also needs a live hold on both questions, and a VERIFIED script claim with no mutation earns NUMERIC.
- **`ledger-claims` is all-or-nothing and refuses a changed artifact, a duplicate, a missing supersede target** → fixture record. Prevents
  a partial append.
- **The append validates what it records, and no field writes a line of its own** → the kit's code audit (2026-10-02, P-12
  H1, H2; `T35P12High`): `bin/ledger-claims` never read the document's errors, so a worker that declared `kit/claims/1` in
  its own `claims.json` skipped the premises, sentence and cross-family rules; and a newline in a `range` wrote a forged
  `## C-099  [PROVED]` header and a `Supersedes:` line into CLAIMS.md. Now it validates the document and each claim
  itself and turns every line break inside a field into a space. Prevents the producer's file deciding its own rules
  or the record's shape.
- **A VERIFIED claim needs a mutation run by its check** → the same audit (H3): `mutations_missing` was set only under
  `--mutate`, so a plain re-check (`bin/check RUN`) after `close-run` let a claim with no mutation, or one never run,
  earn `[VERIFIED]`. Prevents a coverage claim passing on an untested checker.
- **`--input-approved` puts a user-excepted input's source and hash on the ledger** → mc23 (R-3, 2026-09-18). Prevents an undeclared
  exception to the no-prior-inputs rule.
- **The brief skeleton has fixed sections (Gates, Frozen before running, Classes every start ends in, Budget table)** → mc11 (2026-09-16):
  "the least mechanical step has the same skeleton every time"; run 038's design decisions (gauge-fixing, NUMERIC-ONLY class) were the
  case. Prevents a brief omitting what every recent brief had carried by hand.
- **A brief's compressed sentence is a claim; write the chain out** → audit 159 A1 (2026-09-18): "through X and Y, T gives (★)" hid four
  unformalised obligations. Prevents a hidden step in a frozen statement.
- **A slug, and every file in a run directory, is something the worker sees; a slug never starts with a number** → run 158 → 160
  (2026-09-18, "proof" in the slug; neutral slug); mc29 (`new-run` adds the number). Prevents the run's name telling the worker the answer
  or breaking numbering.
- **`usage.json`'s memory figure does not capture a sandboxed compile; check `launch.log` for what a referee opened** → math-orchestrator-6
  (2026-09-18). Prevents reading speed or memory as care.
