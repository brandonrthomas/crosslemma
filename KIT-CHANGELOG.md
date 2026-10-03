# Kit changelog

One entry per kit version an instance can be made at. An instance records its kit commit in `KIT-VERSION` and is upgraded
only by a methods session with a diff against that commit, never automatically (operator ruling, 2026-09-22).

## kit-v0.6.32 — 2026-10-03 — the README's configuration section

The user: "can we include a blurb about configuration in the public readme?". README.md gains a Configuration section
(the environment file, routes, run limits, settings templates), linking the configuration reference. The reference's
two passages on how a model name finds its family still said a word counts when the name begins with it, wrong since
`kit-v0.6.22`; both now say a whole part of the name, or one followed by a digit. No tool or test changed.

## kit-v0.6.31 — 2026-10-03 — P-16; the README's diagram; the review for ud

- **P-16** (found reviewing the kit's changes for the source; the user: "now fix p16"): a networked Claude worker loads
  `.claude/worker-net.settings.json` and the local settings, not the project settings, so it lacked their Bash timeouts
  (`BASH_DEFAULT_TIMEOUT_MS` 600000, `BASH_MAX_TIMEOUT_MS` 3600000), and with them the hour per call the briefs promise
  since `kit-v0.6.30`. The worker-net template now carries the same `env` block (test failing first:
  `T42P11Settings.test_p16_the_networked_worker_has_the_bash_timeouts`). An instance takes it when its worker-net
  settings are filled again.
- **The README's diagram:** `docs/images/crosslemma.svg` (one cycle, by lane: you, the orchestrator, the sandbox, the
  computed tag, the record; the four mechanisms) replaces the small Mermaid chart; `docs/images/crosslemma.mmd` is a
  Mermaid version of the cycle.
- **The kit's own record:** `history/report-ud-relevance-2026-10-03.md` (every kit change since `kit-v0.4.20` mapped
  onto the source's code at `2450a30`, in four tiers, with recommended actions) and the ud prompt revised from it, P-16
  included.
Suites: 32, 168 (one skip), 63, 64.

## kit-v0.6.30 — 2026-10-03 — P-15: the briefs say what the hook does; the ud prompt revised

The user: "a and commit" (P-15, option (a)). Since `kit-v0.6.20` the hook runs a worker's Bash in the foreground only
(the race of the audit's C2), but `bin/new-run`'s solver brief and its referee long-checks note still offered background
jobs to poll. Now both say: every command in the foreground, one per call, with an explicit timeout (an hour at most);
no job outlives its call; longer work in resumable parts. The orchestrator and analyst templates say the same.
Tests failing first: `T44P15Foreground`, and the referee brief's pinned ending (`T10Sentence`). Option (b), workers
without Read and Write so the background option is safe again, is recorded, not built.
Also: `history/prompt-ud-port-2026-10-02.md` revised at this version against the source's `2b18f32` (the kit's own
record). Suites: 32, 167 (one skip), 63, 64.

## kit-v0.6.29 — 2026-10-03 — after the proof instance's kit-v0.6.28 canaries

The proof instance's report on canaries 021 and 022 (relayed by the user, 2026-10-03 ~01:17; the user: "make the three
changes"):
- `bin/manifest` prints its approval line with the absolute path of the tree's own approval tool, so a `!` command works
  from any directory; the hook offers the tap for that form from anywhere (`T43P14ApprovalLine`, and the tap test). The
  instance's opening prompt asks for full paths, which the relative line did not give.
- `templates/runs/canary-BRIEF.md`: Part A's question 1 asks, for each yes, where it appeared and what kind of thing it
  was, in the worker's own words, never its content (canaries 021 and 022 answered (e) and (f) differently from earlier
  ones, and nobody could trace why); step 14: a descriptor that points at `/dev/null` is recorded as such, not as an
  UNSEEN WRITE (canary 022 listed two). The new-instance guide says how to read it.
Suites: 32, 166 (one skip), 63, 64. No hook change.

## kit-v0.6.28 — 2026-10-02 — the analyst's reply block

`templates/analyst-prompt.md` §10 ("Speaking with the user") gains the reply block, in the user's words (2026-10-02
23:09–23:10, relayed by the source's analyst, given here by the user): a reply covering questions the orchestrator put to
the user ends with a code block the user can paste to the orchestrator as is, one short line per question in the user's
terse style, under the orchestrator's own numbers; advice in the user's voice, not a ruling; never an approval command,
a digest to approve, or anything that reads as the user's terminal act. The appendix's "advise the user in your pane"
now points at it, and §8's marker on relayed pastes excepts it (the user, 23:17: "I want the reply block excempt").

P-14, the proof instance's report after its `kit-v0.6.27` canaries (the user: "do your suggestions"; tests failing
first: `T43P14ApprovalLine`, `T19P14GitC`):
- `bin/manifest` prints, after the hashes, the exact approval line for what it showed (each target's 12-hex digest, in
  order, and the flags): an orchestrator had given the command from memory in a wrong form.
- The hook reads `git -C <the tree's root> …` as the plain form (`git -C <root> add LEDGER.log` was refused).
- `templates/runs/canary-BRIEF.md`: `/proc/*/mountinfo` is an expected outcome (the named mount-path residual), and step
  14 writes a marker per descriptor and counts a write as its own command's output when the marker comes back; one that
  does not is an UNSEEN WRITE, checked in the host's record, not called an escape (every Codex canary had flagged its own
  command's pipes). The guides say how to read it.
- An Anthropic canary answered by a fallback model after the provider's safety classifier is expected and recorded
  (the new-instance guide); the canary tests the sandbox, which does not depend on the model.
Suites: 32, 166 (one skip), 63, 64. The hook changed: canaries after an instance's upgrade. Also in this tag: the proof instance's upgrade prompt, `history/prompt-proof-upgrade-v0627-2026-10-02.md`
(the kit's own record).

## kit-v0.6.27 — 2026-10-02 — the docs brought up to the code

The user: "let's update documentation". The pages describing what `kit-v0.6.20` to `v0.6.26` changed now say so:
- concepts: the sandbox (the orchestrator's refusals, a worker's Bash in the foreground, the limits copy, a stopped
  detached run, host writes by rename, the load check, the parsed registration, the git rule), the trust model (the
  bindings, the rulings file, the Lean audit, PROVED needing its check; its diagram had said `hypotheses` was not
  enforced, wrong since `kit-v0.6.1`), the approval gate (the re-read before the start, flags given twice, the claims
  lock; it had said the hook let the orchestrator Read the approvals directory, wrong since `kit-v0.6.6`), roles, the
  record;
- guides: upgrading an instance (`.ignore` in the diff's list; a step for instances passing `kit-v0.6.20`), a new
  instance, approving, a full cycle;
- reference: configuration (P-10's plain `git diff`; the limits copy; the load check), layout, glossary;
  `SECURITY.md` (a paragraph on the earned tag);
- the generated pages regenerated; RULES.md points at the five lessons that lacked a pointer.
- `T23DocsIntegrity.test_the_kit_itself_passes`: the whole docs checker on the kit's own tree (it ran on fixtures only,
  so the kit's own check had failed since `kit-v0.6.21` unnoticed). For that, `scripts/docs/check_docs.py`'s changelog
  check allows the newest heading untagged (a methods session writes it before its tag; any older untagged heading is
  still refused), and skips a tree with no `kit-v*` tags (a clone of the public copy), which it used to report heading
  by heading (the user: "fix the checker issue").

Suites: 32, 164 (one skip), 62, 64.

## kit-v0.6.26 — 2026-10-02 — P-13, route (a): git guarded by what it prints

The user: "2: cheap route". Test failing first: `T18P13GitContents` (test_hook_gate). In the tree, a git command that
prints file contents (`show`, `log`/`reflog` with a patch option, `diff` and `stash show -p` without a summary option,
`grep`, `blame`) must name plain paths, none of them the ledger, the locked data, an approval record or a directory
holding one; `cat-file`, `archive`, `format-patch`, `whatchanged`, `difftool`, `fast-export`, `bundle`, `range-diff`, an
unknown subcommand (an alias) and `git -c` with other than a few harmless keys are refused; git on another repository
is not the tree's. A bare `git diff` in an instance is refused (the ledger always has uncommitted lines): name the paths.
With the ledger unwritable, the hook now refuses what needs its record (an approval tap, an agent launch) and lets the
rest through the gate as usual. Suites: 32, 163 (one skip), 62, 64.

## kit-v0.6.25 — 2026-10-02 — P-10; P-11 (c), (d), (g)

The user: "let's do 4, 5, 6, 7". Each had a test that failed first (`T17P11P10` in test_hook_gate, `T42P11Settings`):
- **P-11 (c)** `bin/run-external` keeps the approved `.limits` at `.claude/state/ext/<run>/limits.json` once the approval
  is used; the hook reads that copy, not the run's own file, which the worker can rewrite.
- **P-11 (d)** Both settings templates carry a second PreToolUse command that loads the hook and exits 2 when it cannot;
  the hook's own command is unchanged (the user-level guard matches it exactly). Unparseable hook input exits 2.
  An instance takes this when its settings are refilled from the templates.
- **P-11 (g)** The preflight parses the settings: the hook registered on PreToolUse for every tool and on PostToolUse
  (`bin/_ext.py hook-registered`).
- **P-10** A plain `git diff` of the packet lists, the environment files and the bindings and rulings is allowed
  (reading them is); the ledger and the locked data stay at `--stat`/`--numstat`.

Suites: 32, 163 (one skip), 60, 64. The hook and the settings templates changed: canaries after an instance's upgrade.

## kit-v0.6.24 — 2026-10-02 — P-12: housekeeping

The user: "commit and do housekeeping items". Tests failed first where a behaviour changed (`T41P12Housekeeping`,
`T31LockedOutsideTheTree`):
- `bin/_approval.py`: the queue's lifetime comment says where the sum is computed; the unused `QUEUE_TTL` removed.
- The hook names the approvals directory once (`APPROVALS_DIR`).
- `bin/new-workspace` refuses a locked directory that already exists, empty or not: the default is keyed by the
  instance's name only, so an empty one may be another instance's of the same name.
- `_lib.models_seen` reads a run's transcripts once per process while their size and modification time hold; the tools
  asked once per claim and per referee.
- Not done: splitting `_lib.py` and `bin/new-run` for size (closed by the user: "ignore fifth item going forward").

Suites: 32, 161 (one skip), 57, 64.

## kit-v0.6.23 — 2026-10-02 — P-12: seven low findings, the launcher's

The user: "do launcher robustness items". Each change had a test that failed first (`T40P12LowLauncher`;
`T5RunExternal.test_a_run_name_used_twice_is_refused`, `test_detach_touches_nothing_before_its_unit_check`):
- `bin/run-external` refuses a run whose name is not unique across workspaces (host state, approvals and bindings are
  keyed by it).
- `--detach` asks whether its unit runs before emptying `detached.out`, and passes the exit file as an argument, not
  spliced into its `bash -c` script.
- A queue that fails partway through using its approvals names the ones it spent.
- A failed `bin/new-run` removes the run directory (and binding) it made.
- `.claude/worker-net.settings.template.json` carries the project settings' `deniedMcpServers` (an instance's filled
  file takes it at its upgrade).
- `harness/egress-fwd`'s sockets, also found: measured (40 connections, open descriptors 4 to 5), no leak; unchanged.

Suites: 32, 158 (one skip), 57, 64.

## kit-v0.6.22 — 2026-10-02 — P-12: five low findings, the gate's

The user: "let's hit the 5 gate hardening fixes". Each had a test that failed first (`T39P12LowGate`, `T16P12LowGate`):
- `bin/ledger` makes every field one line (it wrote a forged `CLAIM` line from one call); SCHEMAS.md §6 now says
  `bin/handoff-archive` writes a `HANDOFF-ARCHIVE` line, and it says so when that write fails.
- The launch manifest refuses a hard link in a run directory.
- `bin/ledger-claims` re-hashes the deps `check.json` recorded, as it does the artifact.
- `model_family` takes a family word as a whole token, or one followed by a digit (`gpt5`, `opus4`), never any prefix.
- An unwritable ledger makes the hook refuse gated calls only; the rest go on with a message that they are not
  recorded.

Suites: 32, 155 (one skip), 57, 62. The hook changed: canaries after an instance's upgrade.

## kit-v0.6.21 — 2026-10-02 — P-12: the six high and twelve medium findings fixed; P-13 recorded

The user: "commit and move to high findings", "let's hit a few of the medium issues", "let's do the rest of the
mediums", "commit current state". Each fix had a test that failed first (`T35P12High`, `T36P12Medium`,
`T37P12MediumRest`, `T38P12LeanAudit` in test_tools; `T14P12High`, `T15P12Medium` in test_hook_gate;
`T5P12RetryTrigger`, `T5P12StopEndsTheWorker` and two more in test_ext). The shared fixture is now a valid claims/2
document.
- **High:** `bin/ledger-claims` validates the document and each claim itself (a worker-declared `kit/claims/1` is
  refused) and turns line breaks inside a field into spaces; a VERIFIED claim with no mutation record from its check
  (none declared, or not run without `--mutate`) earns NUMERIC; the retry after an upstream rate limit reads the CLI's
  own words only (`_ext.py upstream-limited`); `bin/limits-exec` names its scope and stops it on TERM, so stopping a
  detached run ends its worker (shown live); "plain git" in the hook is a list of options that print no contents.
- **Medium:** the orchestrator's Write/Edit of `LEDGER.log` refused; a Glob rooted above the protected files refused;
  every place the locked data can be is guarded when `kit-env.json` is unreadable; a launch flag given twice refused
  (`--module` excepted); the run's bytes read again just before each route starts (`_approval.verify_launch`);
  `licence.log` and a non-empty outbox count as an earlier launch; the binding records the claim's hash
  (`claim_sha256`), and PROVED needs its check; CLAIMS.md appends lock and spend the approval last; `bin/verify-data`
  hashes only files of a locked file's size.
- **The Lean axiom audit** (`bin/check`): no longer appended to the artifact's file, where its macros applied (a
  `macro_rules` for `#print axioms` hid a `sorry`, shown on Lean 4.32). The artifact is compiled in the sandbox, its
  compiled file replayed through the kernel (`leanchecker`) and walked by `harness/lean/KitAudit.lean` (new) in a sandbox
  call that runs no artifact code.
- **P-13** recorded in `HANDOFF.md`: the ledger is unread by name only; possible solutions noted.

**For an instance:** the hook changed again (canaries after the upgrade); a Lean instance needs `leanchecker` in its
toolchain. **The source (ud)** has the Lean hole. Suites: 32, 150 (one skip), 56, 62.

## kit-v0.6.20 — 2026-10-02 — P-12: the code audit's three critical findings fixed

The user: "let's do the p12 fixes now". Each fix had a test that failed first (`T13P12Critical`, `T33P12HostWrites`,
`T34P12Bindings`, `T5P12HostWrites`, and the referee binding in `T2Tools.test_ledger_approval_voided`):
- **C1** The hook gates any tool that runs a shell command (Monitor) as it gates Bash; the tap on the approval tool is
  offered from Bash only. The user-level guards' matcher is the user's file (`~/.claude/settings.json`).
- **C2** Host code never writes into a run directory through a link: `_lib.write_in_run` (no link followed below the
  run; a fresh name renamed over the target) for `bin/check`'s logs and `check.json`, `bin/limits-exec`'s `usage.json`
  and `time.log` (its working files now in a temporary directory of its own), `_ext.py record`'s copied logs and
  `RECORD-EXT.md`, and the licence log; `mv -T` for the transcripts; both outbox drains on `O_NOFOLLOW`; a worker's Bash
  in the foreground only (`run_in_background` set false).
- **C3** A referee run is bound by `bin/new-run` in `data/referee-bindings/<run>.json` (question, claim, the bytes given);
  the earned tag reads only that, and a `referee.json` in a run with no binding never counts. The user's cross-family
  rulings are read from `data/cross-family-rulings.json`, never from `RUN/.cross-family-referee`. The hook refuses the
  orchestrator any write to either; a ledger approval binds both. The Codex sandbox ends the worker's processes before
  copying its session files, and the launcher clears session-file names it did not sort.
- Also: an unreadable `referee.json` is an error under its claim; `bin/new-run` refuses a linked artifact or dep.

**For an instance:** referee runs made before this version have no binding and stop counting; a ruling left in a run
directory is ignored, with a note; the user writes the rulings file. The hook changed: canaries on both routes after
the upgrade. Suites: 32, 132 (one skip), 51, 58.

## kit-v0.6.19 — 2026-10-02 — handoff only: the open work pointed to

`HANDOFF.md` points to the ud prompt (`history/prompt-ud-port-2026-10-02.md`) and to P-12 from §1's reading list, §6
item 30 (a new (e)), §7 (a risk for the three critical findings) and §10's opening prompt (user: "Ensure we point to the
UD prompt and include p12 issues in the handoff"). §7's stale line on the proof instance's version (`kit-v0.3.8`) now
reads `kit-v0.6.12`, and §10 no longer says every pending item is closed. No tool, rule or test changed.

## kit-v0.6.18 — 2026-10-02 — the code audit, recorded (P-12)

The user ran the vibe-code-auditor skill on the kit. Its 38 findings (3 critical, 6 high, 12 medium, 17 low), each
checked against the code, are recorded in `HANDOFF.md` §6 as P-12, pending work, the critical first: the Monitor tool
outside the gate and the user-level guards; host writes that follow a worker's symlinks; earned tags resting on files a
worker can write. No tool, rule or test changed.

## kit-v0.6.17 — 2026-10-02 — the prompt for the source (ud)

`history/prompt-ud-port-2026-10-02.md` (the kit's own record, never published) was written on the user's word. It
lists what the source might take from `kit-v0.4.20` to `kit-v0.6.16`, as checked against the source's git objects at
`b5f956c`, most important first:
- its hook's missing guards on the locked data, the approvals and searches;
- P-3's B1–B6 as they stand there;
- its packet tool's order;
- the files that decide its mounts;
- the user's disk ruling;
- the words and the list of the user's acts.

Each item is offered for the source's owner to rule on, one at a time. No tool, rule or test changed.

## kit-v0.6.16 — 2026-10-02 — P-11's small fixes

The user: "Make the small changes and mark the rest as pending work". Each fix had a test that failed first
(`T32SmallFixesP11`; `T5RunExternal.test_dry_run`):
- **(a)** `bin/new-workspace` commits `kit-env.json` always (`commit_paths`). Since `kit-v0.6.9` it wrote the file
  always but committed it only with `--env`, so most new instances started with an untracked file.
- **(b)** Its dirty-kit check covers everything it copies (`KIT_DIRTY_PATHS = COPY_DIRS + COPY_FILES`), `.gitignore`
  and `.ignore` included.
- **(e)** The Codex sandbox sets `KIT_CPU_HOURS` and `KIT_MEM_GB`, as the hook does on the Claude routes
  (`SCHEMAS.md` §7: the caps a worker's scripts read).
- **(f)** `bin/check-env` tests `/usr/bin/bwrap`, the one the sandboxes run, not the first `bwrap` on `PATH`.

Pending work in `HANDOFF.md` (P-11): (c) a worker can rewrite the `.limits` the hook re-reads; (d) the hook makes no
decision when it fails to load; (g) the launcher's preflight greps the settings. The install and configuration pages
are updated. Suites 32/124/46/54; the docs checker passes. An instance taking this changes `bin/_ext.py` (the Codex
route), so a Codex canary follows; the hook is unchanged.

## kit-v0.6.15 — 2026-10-02 — the last five docs pages fact-checked

The factual review the handoff owed before publishing (user: "Do the factual review"), covering install,
new-instance, the sandbox, layout and configuration. Five fresh-context reviewers (Opus, read-only) each checked one
page's every sentence against the code. Every finding was checked here against the code before it was applied:
- **Findings:** 59 in all.
  - Install: 12. Configuration: 11. New-instance: 9 (and one borderline). Sandbox: 10. Layout: 17.
  - Install also had a stale tool docstring, `bin/new-workspace`'s `env_file_problems`.
- **Corrected,** among them:
  - pages still describing the kit before 2026-10-01's changes: limits refused without a systemd scope; the locked
    directory outside the tree; `kit-env.json` always written; the P-4 hook refusals; `.ignore`; the removed
    `python` field; `--lean`/`--sage` merged into an `--env` file, not refused;
  - wrong counts and lists: a fresh ledger's three lines; `licence.log` in the manifest's exclusions;
  - overclaims about what the hook and the limits guarantee.
- **Recorded, not fixed:** code gaps the review found, put to the user as P-11 in `HANDOFF.md`:
  - (a) `kit-env.json` not committed without `--env`;
  - (b) the dirty check omitting `.gitignore` and `.ignore`;
  - (c) the worker can rewrite `.limits`, which the hook re-reads;
  - (d) the hook fails open on a load error;
  - (e) no `KIT_CPU_HOURS` or `KIT_MEM_GB` on Codex;
  - (f) `check-env` checks a different `bwrap`;
  - (g) the preflight greps the settings.

Suites 32/121/46/54; the docs checker passes.

## kit-v0.6.14 — 2026-10-01 — a test that refused to run in every instance

The proof instance's note for the kit, from its upgrade to `kit-v0.6.12`: `tests/test_ext.py`'s
`test_module_bound_in_the_approval` wrote a `kit-env.json` into the real tree. It refused to run wherever one already
existed, and since `kit-v0.6.9` every new instance has one, so no instance exercised the check that `--module` is bound
in the approval.
- **The fix:** the test now runs in a throwaway copy of the tree (`bin/`, `harness/`, `.claude/` without its state or
  filled settings) with an environment file of its own. It asserts that the real tree's file, if any, is unchanged.
- **The launcher is unchanged:** it still reads only the file beside it, and no variable may move what a sandbox
  mounts.
- **Shown failing first** with a stand-in `kit-env.json` in the kit root, as an instance has; it passes with it there.
- **Explained along the way:** `T5RunExternal`'s fixture run under the real tree is what briefly creates
  `workspace-1/` in the kit root.

`HANDOFF.md`:
- the proof instance's upgrade is recorded (`kit-v0.6.12`; canaries 017 and 018 held, by its commit subjects);
- §0 item 7 expects its new `KIT-VERSION`.

Suites 32/121/46/54. An instance takes this as one file, `tests/test_ext.py`; no canary is needed.

## kit-v0.6.13 — 2026-10-01 — handoff only: P-10 deferred

`HANDOFF.md` §6 item 29: P-10 (a plain `git diff` of the packet lists or the environment files refused) is marked for
later (user: "mark p10 for us to do later"). No tool, rule or test changed.

## kit-v0.6.12 — 2026-10-01 — a handoff records no disk figure

The user's ruling (20:15): "we no longer report disk space as part of a handoff. disk space should always be checked by
the new session agent as source of truth".
- `RULES.md` §7 gains the rule, with its reason: a recorded figure goes stale between sessions and invites a false
  stop or a false all-clear.
- `templates/HANDOFF.md` §0 keeps its `df` line, with no expected figure.
- `templates/orchestrator-prompt.md` §1 has the session read disk space itself and report it.
- The kit's own handoff drops its figures (§0 item 8, §7).

Also in `HANDOFF.md`:
- the proof instance's upgrade prompt, reconciled with that instance's own opening prompt, now targets
  `kit-v0.6.12`, whose three changed files are already among its 58;
- a new pending item, P-10: a plain `git diff` of the packet lists or the environment files is refused though the
  hook's messages and RULES §9 allow it.

Suites unchanged, 32/121/46/54; the docs checker passes.

## kit-v0.6.11 — 2026-10-01 — handoff only: the proof instance's upgrade prompt at kit-v0.6.10

`HANDOFF.md` §6 item 30 (d), on the user's "d" (the proof instance first, publishing after): the upgrade from `kit-v0.4.1`
is 58 files (51 changed, 7 new, `.ignore` among them), none with local edits. The settings templates are unchanged. The
locked directory moves out by the user's `!` commands; git tracked three locked files there, whose keys stay in that
instance's history. The prompt replaces the `kit-v0.5.0` one. Also: §0's note on the suites no longer names a path in
backticks that the kit does not have. No tool, rule or test changed.

## kit-v0.6.10 — 2026-10-01 — P-6: channel parity made quieter

The user's five points on the analyst channel ("p6 as recommended"), in kit terms ("the owner" became "the user";
"DECISIONS context lines" became "the handoff's §4 lines"):
- **`templates/orchestrator-prompt.md`'s appendix, the parity condition:**
  - one message per step, not per action, sent when a step completes or something is put to the user; record-keeping
    rides along in the next substantive message;
  - mechanical commands (`/clat recv`, status) produce no report, and nothing new means no message;
  - no receipt confirmations.
  
  Everything else stands: full manifests and printouts, the user's substantive words verbatim with times, errors in the
  message about their step, results verbatim, and the two closing lines.
- **`templates/analyst-prompt.md`'s appendix:** the analyst writes only when it would change a decision; no
  acknowledgements; small corrections ride along; no receipt confirmations.
- **`docs/guides/analyst.md`'s list** says the same.

No tool, rule or test changed. Suites 32/121/46/54; the docs checker passes.

## kit-v0.6.9 — 2026-10-01 — P-9: the locked directory moves out of the instance tree

Design (A), ruled by the user ("a"): answer keys and label maps live outside the instance, so no search from the
instance, or from the directory that holds the workspaces, walks them.
- **Where the path lives:** `kit-env.json`'s new field `locked_dir` (`bin/_env.py`; the user's file, already refused
  to the orchestrator).
  - `bin/new-workspace` makes `~/.local/state/crosslemma/<instance>/locked/` (mode 0700) and records it. It refuses
    when that directory already holds files, so one instance never takes another's keys.
  - `bin/new-workspace` now always writes `kit-env.json`; an `--env` file's fields go into it.
  - An instance without the field keeps `<root>/data/locked`.
  - The loader refuses a `locked_dir` that is the root, a home directory, a credential directory, or the instance
    (or anything inside or holding it), and falls back to `data/locked`.
- **Every reader follows it:**
  - `bin/_lib.py` (`LOCKED`), and through it `bin/new-run` (the evaluator's inputs; the refusals);
  - `bin/verify-data`: the hashes, `SHA256SUMS` and the copy scan. It also reports keys left in an in-tree
    `data/locked/` after a move, and still finds their copies.
  - **The hook changed** (a candidate, 46/46, an atomic rename): it guards the configured path. Read, Grep and Glob
    there are refused, and so is a Grep rooted above it without a safe filter. Commands naming it (absolute, `~/`,
    `$HOME/`) are refused, except a plain `bin/new-run … --role evaluator` and plain git.
- **Tests failed first:** `T31LockedOutsideTheTree` (four cases) and `T12LockedOutside` (the hook).
- **Docs:**
  - `RULES.md` §8 says `data/locked/` names the locked directory wherever it lives;
  - `SCHEMAS.md` §8 has the field;
  - the record, layout and configuration pages.
  - The upgrade guide gets the migration step: the user moves the directory and adds the field, by `!` commands, since
    the hook refuses both to the orchestrator.
  - Fixed: the record page still said the hook did not bar `data/locked/`, which had been false since `kit-v0.6.6`.
- **Known limit:** where git tracked `data/locked/`, the keys stay in the instance's history; the move keeps searches of
  the working tree out, not searches of the history.

Suites 32/121/46/54; the docs checker passes. An instance taking this changes its hook: canaries by the rule.

## kit-v0.6.8 — 2026-10-01 — P-9, interim: an `.ignore` keeps ripgrep out of the ledger, the locked data, the approvals

P-9: a recursive search typed in a shell walks what the hook protects. The user's interim ruling: keep the rule, and
close the accidental walk cheaply.
- **A new `.ignore` at the kit's root**, copied into every instance by `bin/new-workspace` (`COPY_FILES`, as
  `.gitignore`), names `/LEDGER.log`, `/data/locked/` and `/.claude/state/approvals/`. Ripgrep, which Claude Code's Grep
  tool runs, and fd skip them by default.
- **Checked here:** `rg` honours the file; `grep -r` does not. That is what `.ignore` says, along with `find` and
  `rg --no-ignore`, which also ignore it. It is a convenience, not a guard: the hook and the never-read rule guard.
- **"`--exclude-dir` in any grep the tools issue":** no kit tool issues a recursive grep, so there was nothing to change.
- **Tests:** `T30IgnoreFile`, with two cases:
  - `new-workspace` copies the file, which names all three paths;
  - ripgrep skips them, shown failing with the entries removed first.
  
  The first version of the ripgrep test hung: `rg` with no path reads stdin. It now gives `.` and an empty stdin. The
  stray process was stopped and its temporary directory removed.
- **Not done:** moving `data/locked/` out of the instance tree. That needs a design choice, which has been put to the
  user.

The layout reference and the P-4 lesson are updated. Suites 32/117/45/54; the docs checker passes. An instance gets
`.ignore` as one new file; no canary is needed for it.

## kit-v0.6.7 — 2026-10-01 — P-5: an added model family is a family like the two built in

`kit-env.json`'s `model_families` lets an instance declare a family beyond Anthropic and OpenAI, for a user with another
provider. The cross-family rule still knew only the pair: it wanted OpenAI for an Anthropic producer and Anthropic for
any other. An added family's referees therefore counted only through a per-run ruling, and an added family's producer
could take only an Anthropic read. Now the cross-family read is a hold from any known family other than the producer's
(`bin/_lib.py` `cross_family_need`; user: "a").
- **Unchanged:** an unknown family never counts; a user ruling in `RUN/.cross-family-referee` still names the family
  exactly.
- **The ladder:** RULES §7's exception for reads before their ladders names the two built-in families. An added
  family's models referee only after their own ladder ("Calibrate before trusting"); the code does not check
  calibration. No new ruling was needed: this is the existing rule, now stated in §7.
- **Tests:** `T17CrossFamily.test_an_added_family_counts` failed first.
- **Docs:** `RULES.md` §7 and the configuration reference.

Suites 32/115/45/54; the docs checker passes. No hook change.

## kit-v0.6.6 — 2026-10-01 — P-4: the possible gaps tested and closed

The user's "yes" to the recommendations. Each gap had a test that failed on the old code first; all of them were real.
- **The ledger and the locked data are no longer reachable by search, and the approval records no longer readable.**
  The hook changed, a candidate tested on the suite (45/45) before an atomic rename.
  - A Grep with no path from the tree root printed `LEDGER.log`'s lines. Now a Grep rooted above the ledger, a locked
    file or an approval record is refused, unless its glob or type filter matches none of them. The hook checks the
    filter against their names, never their contents. A negated glob, or a type it cannot map, counts as no filter.
  - Nothing refused `data/locked/`. Now Read, Grep and Glob inside it are refused, and so is any command naming it, but
    a plain `bin/new-run … --role evaluator` and plain git add, commit, status or diff.
  - A Read of the approvals directory was allowed. Now Read, Grep and Glob there are refused (RULES §9: "anything
    touching").
  - The old test asserting a bare Grep from the root was allowed now asserts a filtered one.
- **`bin/packet-block` and `bin/packet-except` ledger before they change the list.** The new list is staged, the line
  written, and then the list replaced; with no ledger the tool refuses and the list is unchanged. Before this, the list
  changed and a failed append left no record.
- **Recorded as a residual, not fixed:** a Codex worker can read its own `.ledger-outbox`, its own queued lines and never
  another run's (RULES §9, worker context residuals).
- **Found while doing this, not fixed:** a recursive `grep` or `rg` typed in a Bash command walks the same files, since
  the hook matches names, not what a program reads (new pending item P-9).

`RULES.md` §9, a new lesson, the roles page and the layout reference are updated. Tests: `T11P4Gaps` (hook) and
`T29PacketListLedgerFirst` (tools). Suites 32/114/45/54; the docs checker passes. An instance taking this changes its
hook: canaries by the rule.

## kit-v0.6.5 — 2026-10-01 — P-8, step 2: "user" and "operator" sorted by the §4 rule

The user's "go" for the sweep. Each "user" that `kit-v0.6.0` wrote was sorted by `RULES.md` §4's test, keeping "user"
wherever a line could fall either way. A line moved to "operator" only when it is about reports, reading or
direction inside the bounds:
- **Reports:** the final message, the tables shown, the paths `bin/merge` prints, PROVENANCE's "shown to".
- **Outside checks:** RULES §10's heading and text (an independence question stays the user's), the handoff audit's
  discretion, the outside-reader question.
- **Purpose:** the purpose within the declared session type, and the queue order; a queue still needs the user's
  approval.
- **Consent wording:** "the operator's words"; "an operator message covers" (not "approves"); deviations go to the
  operator, and to the user when they widen.
- **Reading:** referee notes; `intake/` access, with exceptions staying the user's (also the default packet-rule text a
  new instance writes).
- **Rulings records:** the user's, and the operator agent's marked as its own.
- **Definitions:** an operator-agent row and readers line in the docs.

Kept as "user":
- all of `SCHEMAS.md`, the hook, and the tools but two lines;
- the analyst template;
- `LESSONS.md`'s attributions;
- the packet briefs that outside readers receive.

On review, two calls were ruled (the analyst's reasons; approved by the user):
- **Parallel runs stay the user's**, "One run at a time unless the user rules otherwise": overlapping runs skew
  measurements a claim may rest on, load a shared machine, and exceed budgets set for one run at a time.
- **An attack may be opened by the operator** within the user's budget. The README template now says that the budget,
  and setting or loosening the kill criteria or the scope, are the user's; tightening them, parking or closing an
  attack are the operator's.

Also: the attack template's "⟨his words⟩" now reads "⟨the words⟩"; SECURITY.md's "the user's own user account" now reads
"the user's own account". Suites 32/112/42/54; the docs checker passes. No hook change.

## kit-v0.6.4 — 2026-10-01 — P-8, step 1: the operator agent as practised; the user's acts and the operator's

The user corrected the record: "operator isn't always the user though. I've been using analyst as operator for several
sessions now". The rule that sorts acts between them was drafted with the analyst over three messages; the user adopted
it ("yes").
- **`RULES.md` "Words":**
  - the operator agent is an agent the user designates (in practice, the analyst), not only P7's;
  - P7 is the charter for running one unattended;
  - one test decides what is whose: anything that could widen what a worker sees, what a claim asserts, what the ledger
    holds or what the gate lets through is the user's; ordering, reading and reporting inside those bounds may be the
    operator's;
  - the approval line and its P7 clause are unchanged.
- **`RULES.md` §4:**
  - an operator-agent row in the roles table;
  - a new subsection, "The user's acts, and the operator's": nine items for the user alone, the operator's list, and the
    files no agent reads.
- **§11** is renamed "Working with the operator".
- **`FLOW.md`** ("An analyst, and the operator agent"), **both session-prompt templates** and four docs pages now
  describe the analyst as practised. They no longer call the Clatter channel "outside the kit's design": the user opens
  and closes it (item 8). The user's list replaces the templates' own lists of what stays the user's.

Not yet done (step 2): sorting the "user" lines `kit-v0.6.0` wrote everywhere by this rule. No tool, hook or test
changed. Suites 32/112/42/54; the docs checker passes.

## kit-v0.6.3 — 2026-10-01 — handoff only: P-7 closed (the guard fails closed); P-8 recorded

`HANDOFF.md` §6 item 29:
- **P-7 is closed** outside the kit, in the user's own file `~/.claude/hooks/guard-approve.sh`, which now fails closed.
  Its tests live beside it, `guard-approve-test.py`, 11 cases; the four fail-closed cases failed on the old guard first.
- **P-8 records** that the analyst has been acting as operator agent, and the plan for "Words", `FLOW.md`, the
  templates and the user/operator sort, all put to the user.

No tool, rule or test of the kit changed.

## kit-v0.6.2 — 2026-10-01 — three terms: user, operator agent, operator; the P7 clause

The user's rulings: "there should be three terms: user (human being), operator agent (specific to an agent acting as
operator), and operator (either the user or the operator agent)". And on the approval line: "Keep it as written …
Add one clause after the sentence".
- `RULES.md` "Words" defines the three terms and keeps "Every approval stays the user's.", followed by the user's clause
  verbatim: "(P7, if built, would let a designated agent sign approvals; that requires amending this line by the user's
  ruling.)". The glossary (user, operator, operator agent) and the roles page say the same.
- What an agent reads at the gate (the user: "Rename those in the same change"):
  - The kit hook's tap prompt and refusals already said "user" (`kit-v0.6.0`). Its function `ask_operator_to_approve` is
    now `ask_user_to_approve`, also the heading of the hook-refusals page: a candidate copy, two lines differing, an
    atomic rename.
  - The user-level guard (`~/.claude/hooks/guard-approve.sh`, outside the kit) is backed up as
    `guard-approve.sh.bak-20261001-1808`. Its message now says "the user" where it named a person and "him" and "he".
    Pipe-tested: 7 cases. Seen live.
- **Not yet done:** the uses of "user" that `kit-v0.6.0` wrote everywhere are not yet sorted into user (the human's
  acts) and operator (direction either may give). That sweep waits on the user's word.

Suites 32/112/42/54; the docs checker passes. An instance taking this changes its hook (one function name):
canaries by the rule.

## kit-v0.6.1 — 2026-10-01 — P-3, part 2: the code does what the rules say (B1–B6)

Pending item P-3's behaviour changes, all taken (user: "B1-6: yes to all"). Each has a test that failed first.
- **B1:** `bin/new-run` refuses `--input` for a referee. A referee sees the claim, its artifact and declared deps, the
  problem statement and its ledger premises, nothing else (`RULES.md` §7).
- **B2:** `--input-approved` takes a file only when its bytes are on the user's exceptions list,
  `data/packet-exceptions.json`. The list is written only by `! bin/packet-except`, and its entries are live only while
  the file keeps those bytes. Before this, the user's exception was the orchestrator's word.
- **B3:** `bin/limits-exec` refuses, and runs nothing, where no systemd user scope can be made. `limits-exec --probe`
  answers the same question, and `bin/run-external`'s preflight asks it before the approval is touched. `bin/check-env`
  now reports a missing scope as FAIL, not WARN. Before this, the worker ran with `enforced=false`.
- **B4:** `[PROVED]` needs a live hold on both questions, `certify` and `hypotheses`, besides every live referee holding
  and the cross-family `certify` hold (`bin/_lib.py` `earned_tag`, `proved_questions`; `merge`, `close-run`,
  `ledger-claims`). `bin/close-run` prints the `new-run` line for the missing question. Before this, one cross-family
  `certify` hold could earn `[PROVED]` alone.
- **B5:** under `kit/claims/2`, a mutation that names no FAIL line (`expect_stdout_contains`) is a form error in
  `bin/validate-claims`, so `bin/check` fails the claim. It stays a warning for `kit/claims/1`.
- **B6:** a VERIFIED script claim with no declared mutation (`mutations_missing`) earns `[NUMERIC]`.

Entries already in `CLAIMS.md` are never recomputed; these rules bind every append from now on. Rules, schemas, the
earned-tag lesson, five docs pages and the tools' docstrings are updated. Tests: `T28RulesVsCode` (B1, B2, B4–B6) and
`T5NoUserManager` (B3, with a fake `systemd-run`); the T10 and T17 fixtures were brought under the new rules. Suites
32/112/42/54; the docs checker passes. An instance taking this changes no hook or harness note.

## kit-v0.6.0 — 2026-10-01 — "user" for the human who approves; "operator" for P7's agent

The user ruled (P-3 fix 1, reading (b): "make all 8 fixes except 1: "user", not "operator" or "owner"; currently human
owner approves and the optional operator agent can give direction not requiring user approval"; then "b."):
- The **user** is the human who runs the workspace: approves, rules, reads any file. The **operator** is an optional
  agent under the operator charter (P7, not built) that may give direction not requiring the user's approval; every
  approval stays the user's (`RULES.md` "Words", §4).
- **Fixed names changed** (`SCHEMAS.md` §7): the tap prompt opens `USER APPROVAL (single use, 30 min): …`; the refusal
  that is the stop reads `no user approval for these hashes` (it was "operator", and `RULES.md` quoted "owner").
- Every other use for the human, kit-wide: rules, lessons, schemas, flow, tools' docstrings and messages, the hook's
  messages and comments, harness notes, `kit-shell`'s comment, templates, tests, docs, README, SECURITY, CONTRIBUTING.
  777 replacements by a script that kept "operator charter", "operator agent" and the legacy flag; then the
  definitions, the glossary and the roles page by hand.
- **Kept:** `--operator-approved`, the legacy flag `bin/ledger-claims` and `bin/annotate-claim` accept and ignore (a
  rename would break any old command line for nothing); `LESSONS.md`'s "owner" where an incident quotes the source's
  owner; this changelog's earlier entries and `HANDOFF.md`'s record, which say "operator" for the human.

**The hook changed** (its prompt text and refusal messages), and the worker agent file is unchanged but the three
harness notes changed, so an instance taking this runs canaries on its routes. The user-level guard
(`~/.claude/hooks/guard-approve.sh`) matches commands, not this text, and is unaffected. Suites 32/107/42/52; the docs
checker passes.

## kit-v0.5.5 — 2026-10-01 — P-3, part 1: the rule files brought up to the code

Seven of the eight text fixes of pending item P-3 (operator: "make all 8 fixes except 1"). **Text only: no tool, hook
or test changed.**
- `RULES.md` §8: the ledger is written by the hook and the kit's tools (not only `bin/ledger`); `git diff --stat` is
  one of the commands that may name it, as the hook allows.
- `RULES.md` §7: the cost figure is Claude Code's own estimate (`total_cost_usd`, from its price table); the kit keeps
  no price table.
- `RULES.md` "Words" and §4: an agent as operator is P7, not built in this version.
- `SCHEMAS.md`: `--question sentence` in §6's `new-run` line; what a referee receives, `input/ledger-premises.md`
  included (§3, §6); `bin/claim-deps`'s `premise` edge; which tools write ledger lines (not "every tool, one line").
- `LESSONS.md`: the headless-worker lesson names `KIT_WORKER_RUN` and `KIT_WORKER_NET`, the source's `MATHS_WORKER_*`
  marked as the source's.
- `FLOW.md`: cites `RULES.md` "Words", not a "§0" it does not have.
- Docs: two pages that restated the old ledger exception.

Open: fix 1, the refusal text `RULES.md` quotes ("no owner approval"), where the operator ruled "user", which has two
readings put to the operator. Not ruled: P-3's behaviour changes B1–B6. Suites 32/107/42/52; the docs checker passes.
An instance takes this as rule and docs text only; no canary.

## kit-v0.5.4 — 2026-10-01 — P-2: the tools' docstrings brought up to the code

Pending item P-2 (operator: "b: fix all as you outlined"): every docstring on the list, re-checked against its code
first, then corrected. **Text only: no behaviour changed.** One message text changed: `bin/validate-claims` cited an
`ORCHESTRATOR.md` the kit lacks and now cites `RULES.md` §2.

Corrected, in brief:
- `run-external`: three routes, not "routed at OpenRouter"; route-neutral model ids; the effort and turn-cap checks;
  the CPU budget (exit 152), the queue stop, the EXIT-EXT fields, the dropped `ANTHROPIC_*` variables.
- `new-workspace`: `--env` in the usage line; the packet rules start with four blocks and "verdicts", not empty.
- `check`: a mutation's FAIL line; signatures and the library record.
- `annotate-claim`, `ledger-claims`: usage lines without the ignored `--operator-approved`; `--batch`; the refusals
  and the family, notes, dependents and MODEL lines.
- `new-run`: `--question` (with `sentence`), the caps, `--harness`, `--module`; what a referee gets, including
  `input/ledger-premises.md`.
- `close-run`: the sentence, cross-family, family and MODEL lines.
- `lint-brief`: the packet-index cache it writes; the route-verdict error.
- `limits-exec`: exit 152; it writes no ledger line.
- `verify-data`: the `root:` line, the environment file's problems, `.verify-data-skip`.
- `astra-session`: no subagent workers; a worker's effort and routing are its own; the terminal or approval it needs.
- `_approval.py`: every launch approval binds its flags; batch digests; the queue record; no Agent gate.
- `_packet.py`: "verdicts" and "extract"; the launch path never reads the cache; a vanished file is skipped.
- `_ext.py`: modules, the command sandbox, the egress socket's place, the transcript chain, the subcommands.
- `_lib.py`: what it holds and who uses it. `watch-run`: lesson citations in place of the source's change numbers.
- **The hook's header** (`.claude/hooks/sandbox.py`): workers are headless main processes; Read, Write, Bash; the
  gate's refusals as they stand. A tested candidate: its code, the module docstring removed, is identical to the old
  hook's by AST comparison; installed by an atomic rename.

The reference pages are regenerated. Suites 32/107/42/52; the docs checker passes. An instance taking this changes its
hook's bytes (comment only), so canaries follow by the rule, which an upgrade with other hook changes already owes.

## kit-v0.5.3 — 2026-10-01 — the orchestrator template from the source's revision 2

The source's analyst revised the source's orchestrator prompt, which began as the kit's own (revision 2, six marked
changes). Three of them fit the kit, taken on the operator's go ("1. approved 2. approved 3. approved 4. approved"):
- **Tiered opening reads** (R2-1). `templates/orchestrator-prompt.md` §1 and `templates/HANDOFF.md` §1 now read in
  three tiers:
  - always whole: `RULES.md`, the handoff, `SCHEMAS.md`, the problem statement;
  - as an index only: `CLAIMS.md`, by its header lines, counted by `grep`;
  - by id, only after the operator sets the session's purpose: entries, notes, intake records, attack READMEs,
    prior-art.

  The handoff template had said `CLAIMS.md` whole.
- **The upgrade record** (R2-2's clause). An instance records an upgrade in `KIT-VERSION`'s `upgraded:` line and in its
  handoff. A kit change goes to the kit's rules, lessons and changelog.
- **Channel parity** (R2-4), a new minimum condition in the appendix: while the channel is on, the analyst is told
  everything the operator is told, in the same turn and unasked. Every message ends with "Pending on the operator:" and
  "Uncommitted:". It replaces the appendix's "Report" line and keeps that line's rule: manifests go without the
  approval command.

`docs/guides/analyst.md` lists the parity condition too. R2-6 (the tap call's flags) has been in since `kit-v0.4.20`;
R2-3 and R2-5 are the source's alone. No tool, rule or test changed. An instance takes this as two template files and
one docs page; no canary is needed.

## kit-v0.5.2 — 2026-10-01 — handoff: the next session's plan

`HANDOFF.md` §6 item 30 records the operator's plan for the next session:
- the orchestrator template from the source's revision 2, all agreed;
- the pending items P-2 to P-5;
- a prompt for the source;
- then maybe publishing or the proof instance's upgrade, whose prompt is kept there in full.

§10's opening prompt points at that plan. No tool, rule or test changed.

## kit-v0.5.1 — 2026-10-01 — handoff only: the proof instance's upgrade prompt at kit-v0.5.0

`HANDOFF.md` §6 item 29: the proof instance's upgrade from `kit-v0.4.1` now targets `kit-v0.5.0`: 36 files (30 changed,
6 new), none with local edits. Its canaries are due for the hook, the agent file and the harness notes. No tool, rule
or test changed.

## kit-v0.5.0 — 2026-10-01 — crosslemma: the kit generalized, documented, and ready to export

The project is named **crosslemma** (operator, 16:16). This version closes the generalization of `kit-v0.4.24` to
`kit-v0.4.27` (operator: "we need to generalize"):
- `kit-env.json` describes a machine's tools as modules; licence-server programs are reached through a relay.
- Codex is found by search, not one hard-coded path.
- `bin/check-env` reports what a machine offers.
- The tools stay on `/usr/bin/python3` ("a. keep").

**Tools changed**, from a fact-check of the new code by the docs writer:
- `bin/new-workspace --env` with `--lean` or `--sage` writes those as the modules `lean` and `sage` of the copied file,
  where it refused them before.
- A Codex dry run with `--module` shows the licence mounts.
- A run's record names its granted licence modules and hashes `licence.log`, which the run manifest leaves out.
- The environment file's unused `python` field is gone.
- The worker agent file and the three harness notes name the system's Python 3, not 3.12 (an instance taking this
  runs canaries).

**Docs:** eight pages updated for the change and fact-checked; 39 errors in pre-existing text corrected. Untested: a
real licensed program; a full `run-external --module` launch. Suites 32/107/42/52. An instance taking this changes
its hook, agent file and harness notes: canaries on its routes after.

## kit-v0.4.27 — 2026-10-01 — generalizing, step 4: the environment file in use; its rule, lesson and schema

**Tools changed.**
- `bin/new-workspace --env FILE` checks an environment file against the new instance before writing anything, then
  copies it to `kit-env.json`. It is refused with `--lean` or `--sage` when it names its own modules: those flags would
  then not be mounted.
- `bin/verify-data` reports the file's problems.
- `bin/new-run --module NAME` records a run's licence modules in `RUN/.modules`, bound with the run's bytes, and every
  brief names the modules its worker will have (each module's `brief` line).
- `bin/run-external` refuses, before any approval, a `--module` set that differs from `RUN/.modules`.

`RULES.md` §9 has the rule; the new lesson is **A worker's tools come from the operator's environment file**;
`SCHEMAS.md` §8 gives the file's fields, and §7 the new fixed names. The interpreter stays `/usr/bin/python3` (operator: "a.
keep"). Suites 32/107/42/52.

## kit-v0.4.26 — 2026-10-01 — generalizing, step 3: the CLIs found, the Python's /etc, bin/check-env

**The hook changed** (a tested candidate, an atomic rename). **Tools changed.**
- Codex's real binary is found from the `codex` command: a native binary's own directory, or the npm package's
  `node_modules/@openai/codex-*/vendor/*/bin/`. `kit-env.json`'s `codex_bin_dir` or `KIT_CODEX_BIN_DIR` override it.
  It was one hard-coded Homebrew path for x86-64.
- The worker's CLI is `kit-env.json`'s `claude` (default `claude` on `PATH`).
- Both sandboxes mount the system Python's `/etc/pythonX.Y` for whichever version `/usr/bin/python3` is (it was
  `/etc/python3.12` by name). The golden test is still byte-identical here.
- New `bin/check-env` reports each part the kit needs as ok, WARN or FAIL, plus the environment file's problems, and
  runs each module's self-test inside a worker's sandbox.

**Not changed, on purpose:** the tools stay on `/usr/bin/python3`. The design's `#!/usr/bin/env python3` would run them
on the shell's Python, the failure **Every tool, hook and test runs on `/usr/bin/python3`** records (the shell's was
3.14 and the sandbox's 3.12); put to the operator. Suites 32/104/42/52. An instance taking this changes its hook:
canaries on its routes after.

## kit-v0.4.25 — 2026-10-01 — generalizing, step 2: the licence-server route

The operator, 15:30: "I want to implement the network route now". A module in `kit-env.json` that names
`licence_servers` (a host and a port of 1024 or more, one per port) is mounted only for a run launched with
`bin/run-external --module NAME`. The flag is bound in the approval, like `--network`, and checked before the approval
is touched (`_ext.py module-check`). **The hook changed** (a tested candidate, an atomic rename). **Tools changed.**
- **The host side:** `_ext.py` runs one relay per endpoint, on a socket in the run's private socket directory. Each
  carries a connection to its one fixed host and port, and logs its open and close with byte counts, never its contents
  (`RUN/licence.log`).
- **The Claude route:** the hook mounts the relay sockets and the existing forwarder, and an `/etc/hosts` naming each
  licence host at 127.0.0.1. It starts a forwarder per endpoint before each command. It takes the sockets only from the
  worker's process environment, and only if each is a socket named as the relay names it and the ports match.
- **The Codex route:** `_ext.py codex --module`. `kit-shell` starts the forwarders inside each command's own sandbox.
- **A networked run** has the host network already and gets the module's mounts only.

Live tests (`T7LicenceRoute`): a sandboxed command reaches the named server through the relay and is refused a second
one, on the Claude route and inside `kit-shell` nested in a Codex-shaped sandbox. A socket not the relay's is not
mounted; nothing is mounted for a run not granted. Untested: a real licensed program. Suites 32/97/42/52. An instance
taking this changes its hook: canaries on its routes after.

## kit-v0.4.24 — 2026-10-01 — generalizing, step 1: one environment loader, generic modules

`bin/_env.py` reads `kit-env.json`, the operator's environment file, and the hook, the Codex route and the model-family
check use it. **The hook changed** (a tested candidate kept beside the live hook so its root resolves, installed by an
atomic rename). **Tools changed.**
- A module is a set of read-only mounts with `PATH` and environment additions. Lean and SageMath are no longer special
  cases: an instance with no `kit-env.json` gets exactly its old `.kit-lean` / `.kit-sage` mounts, and the golden test
  shows the worker's sandbox command unchanged byte for byte.
- `worker_path` adds read-only directories to every worker's `PATH`.
- Model families can be added to the built-in table.
- Whoever writes the file, a mount source that is the root, a home directory, the instance (other than its library
  link and the kit's own shims) or a credential directory is refused: P-1's second half.
- If the loader cannot be loaded, no module is mounted.
- Fixtures moved their fake toolchains outside the instance.
- Fixed: a new test's clean-up left the environment empty for later tests.

Still to come in this change: the licence-server route, the CLIs' and the interpreter's places, `bin/check-env`, the
rules, a lesson and the docs. Suites 32/97/42/45.

## kit-v0.4.23 — 2026-10-01 — the documentation fact-checked

Two Opus reviewers checked every factual sentence of 15 pages against `RULES.md`, `SCHEMAS.md` and the code, then applied
their own findings (66 in all).
- Corrected: `SECURITY.md`'s network section was backwards (a `--network` run shares the host network; the exact-host
  egress proxy is for Codex runs without it); the README diagram (a failed check is BLOCKED, not GAP); the upgrade
  guide installed the hook before testing it; credentials that do reach a worker's process are now named.
- Where `RULES.md` and the code disagree, a page now describes the code and says that `RULES.md` words it differently,
  without deciding which is right. Those disagreements are `HANDOFF.md` §6 item 29, P-3.
No tool, hook, test or rule changed.

## kit-v0.4.22 — 2026-10-01 — the environment files are the operator's (pending item P-1); licensed software

**The hook changed** (a tested candidate, `HOOK_UNDER_TEST`, installed by an atomic rename). The hook now refuses the
orchestrator any write to `kit-env.json`, `.kit-lean`, `.kit-sage` and `.kit-routes`, and any command naming them except a
plain read or a plain git add, commit, status or diff. The hook reads `.kit-lean` and `.kit-sage` to decide what to mount
into every worker's sandbox, so a path written there would have been mounted for every worker; a new test showed all
twenty such writes and commands allowed before. New lesson **The environment files are the operator's**; `RULES.md` §9.
New guide `docs/guides/licensed-software.md`: the supported way to use a licensed program today is to run it outside the
kit and bring its results in as outside input (operator: "Add route 1 to the docs"). Suites 32/90/42/45. An instance
taking this changes its hook: canaries on its routes after.

## kit-v0.4.21 — 2026-10-01 — Apache-2.0; pending items recorded

`LICENSE`: the Apache License 2.0 (operator: "apache2"), copyright 2026 Brandon Thomas; `README.md` says so. `HANDOFF.md` §6
item 29: four pending items (a writable module file the hook mounts from; stale docstrings; rules versus code; four
untested gaps), and the rulings on licensed software. No tool, hook, test or rule changed.

## kit-v0.4.20 — 2026-10-01 — public documentation, its checker, and a clean export

For publication on GitHub (operator, 2026-10-01). **No tool, hook or rule changed.** New: `README.md`, `SECURITY.md`,
`CONTRIBUTING.md`, and `docs/`: an index, conventions, six concept pages, seven guides, four hand-written reference pages,
and 29 reference pages generated from the code by `scripts/docs/gen_reference.py` (one per tool, the hook's refusals, the
ledger's event types). `scripts/docs/check_docs.py` rebuilds the graph of rules, lessons, tools, templates, pages and tags
on every run and refuses: a dangling link or lesson pointer; a lesson nothing points at; a tool or template with no
reference entry; a page the index does not reach; a stale generated page; a changelog out of step with the tags;
machine-specific text in a published file. Its tests are in `tests/test_tools.py` (T23DocsIntegrity, skipped in an
instance, which gets neither `docs/` nor `scripts/`).

`scripts/export-public` makes the public copy:
- one new commit, with no history;
- the working record (`HANDOFF.md`, `history/`) left out;
- an identity refused if it carries the hostname or a private domain;
- the exported tree checked before the commit;
- never pushed.

Session names, local paths and the predecessor workspace's name are taken out of the lessons, the changelog, the templates
and the tests. The orchestrator template's tap call now carries the launch flags, without which a launch approval is refused.
Suites 32/90/41/45. Most pages were written by subagents and pass the checker; a factual review of them is still to come
(`HANDOFF.md` §6 item 29).

## kit-v0.4.19 — 2026-10-01 — four of the source's improvements, and its count format

From the source's method changes 69–78 (read from its git objects at `901197e`; operator: "integrate the four improvements. do
mc77"). **The hook changed** (a tested candidate, installed by an atomic rename). **Tools changed.**
- The hook refuses an orchestrator's Read, Grep or Glob under `~/.claude/clatter/`, and a Grep or Glob rooted above it. A `~`
  path is expanded before every file check; a Write to `~/.claude/clatter/…` had passed. (Its 69, plus the rooted-above case.)
- The solver skeleton's example pin ends its value (`count=17\n`). The sentence brief counts a substring pin as asserted only
  when it ends the value. (Its 78, G1.)
- The kill rule says FAIL lines go to stdout and no part's FAIL line occurs inside another's. (Its 78.)
- The solver's long-wait paragraph says how to wait: one poll per tool call. (Its 74.)
- Counts in the effort and model records are joined with `*` (`gpt-5.6-sol*1`, was `gpt-5.6-solx1`). Nothing parses them
  back. (Its 77.)

Not changed, recorded: `&gt;` in an approval printout is the client escaping a `!` command's output, not a kit tool (its item
8). New tests fail on the previous code. Suites 32/80/41/45. An instance taking this changes its hook: canaries on its routes
after.

## kit-v0.4.18 — 2026-10-01 — handoff only: the operator's four answers; the proof instance's upgrade prompt

`HANDOFF.md` §6 item 27: the review instance retired; the recalibration stays tabled; `emr` is not raised again. An opening prompt
is written for the proof instance's upgrade from `kit-v0.4.1` to `kit-v0.4.17` (25 files; no local edits found). No tool,
rule or test of the kit changed.

## kit-v0.4.17 — 2026-09-30 — handoff only: the source's sync package; the guard names the source

`HANDOFF.md` §6 item 27: the source workspace was read from git objects only. It had done six of the earlier list's items and
none of the Clatter items. A methods prompt and source versions of both session prompts were drafted for the operator to
hand over. On the operator's word, the user-level guard also lets the source's own plain approval call through to its hook
(its tap route). No tool, rule or test of the kit changed.

## kit-v0.4.16 — 2026-09-30 — two session-prompt templates: the analyst and the orchestrator

`HANDOFF.md` §6 item 27 (b)–(d), the operator's ruling: `templates/analyst-prompt.md` and `templates/orchestrator-prompt.md`,
adapted from the source's analyst's drafts (recorded by path and sha256) in the kit's names. Each has a channel over Clatter
as an appendix marked not kit method, with its minimum conditions. Both approval routes are described; taps behind a
Clatter relay older than v0.1.3 are excluded. `FLOW.md` and `templates/README.md` point at both. New instances get them with
`templates/`; nothing else changed. Suites 32/80/40/45.

## kit-v0.4.15 — 2026-09-30 — handoff only: tap approvals restored

`HANDOFF.md` §6 item 26: on the operator's word, the user-level guard outside the kit is narrowed. It lets a plain call to
an instance's own approval tool through to that instance's hook, which offers the tap; only when the session was opened in
that instance. Every other session and form is still denied. `RULES.md` §6's tap is usable again. No tool, rule or test of
the kit changed.

## kit-v0.4.14 — 2026-09-30 — handoff only: Clatter's own fixes; the relay's Enter settled

`HANDOFF.md` §6 item 26: Clatter's agent fixed the four items of the kit's review (operator-approved). A live test found
that the old relay's blind Enter approved a pending permission prompt; since Clatter v0.1.3 it types only into an empty
input box and defers otherwise. `bus-send.sh` takes no sender flags. Checked here against Clatter's repository. One gap is
open: `emr` still runs the old relay. No tool, rule or test of the kit changed; one lesson's sentence updated.

## kit-v0.4.13 — 2026-09-30 — the hook allows Clatter's send script, not its sender flags

`HANDOFF.md` §6 item 27 (a), the operator's ruling: **the hook changed** (a tested candidate, `HOOK_UNDER_TEST`, installed by an
atomic rename). An instance orchestrator may run `~/.claude/clatter/scripts/bus-send.sh`, which Clatter's inbox names for a
threaded reply (`--reply-to`), but not with `--from` or `--from-session`, which set any sender name and session id; quotes
and backslashes are dropped before the check. Every other script under `~/.claude/clatter/` stays refused. Two new
T9ClatterGate tests fail on the previous hook. Suites 32/80/40/45. An instance taking this changes its hook: canaries on its
routes after.

## kit-v0.4.12 — 2026-09-30 — handoff only: two prompt templates and a hook tweak ruled, not yet built

`HANDOFF.md` §6 item 27: the operator agreed the analyst's two prompt drafts (held outside the kit, by path and sha256) go
in as templates with the eight review points, the bus channel as an appendix outside the kit's design until P7, and that
the hook allow `bus-send.sh` without its sender-forging flags. Recorded before compaction; nothing built yet.

## kit-v0.4.11 — 2026-09-30 — handoff only: a user-level guard on the approval tool

`HANDOFF.md` §6 item 26: on the operator's "add guard everywhere", a user-level hook outside the kit
(`~/.claude/hooks/guard-approve.sh`) denies any session's command naming the approval tool; the operator's `!` approvals
are unaffected, and the instance hook's tap route is unusable while it stands. No tool, rule or test of the kit changed.

## kit-v0.4.10 — 2026-09-30 — the hook keeps an orchestrator out of other panes and Clatter's files

The source's operator approved (2026-09-30, relaying the source's review of the kit's Clatter evaluation) the narrow fix for gap 2,
"the kit agent can supply the tested version". **The hook changed** (a tested candidate, `HOOK_UNDER_TEST`, installed by an atomic
rename): an instance orchestrator is refused keys or buffers into a tmux pane, any touch of `~/.claude/clatter/` but through the
dispatcher `bus.sh`, and the dispatcher's `mode` and `clear`; its peers, ask, send, broadcast, recv, status and doctor stay. Workers
are unchanged (their sandbox has neither). New tests (T9ClatterGate) fail on the previous hook except the two that guard what stays
allowed. Suites 32/80/38/45. An instance taking this changes its hook: canaries on its routes after.

## kit-v0.4.9 — 2026-09-30 — the kill-all lines guarded

From the source's review of its port of `kit-v0.3.7` (relayed by the operator): the Codex script's `kill -KILL -1` is safe only
inside the sandbox's process namespace. **Tools changed.** Required: a test reads the worker's process namespace from inside the
sandbox and fails if it is the host's (shown failing with `--unshare-all` removed). Recommended, taken: the line runs only when the
script's namespace differs from the host's (`bin/_ext.py` `kill_all_in_ns`; tested with `kill` shadowed on the host and in a
fresh namespace). The same risk in `kit-v0.4.6`'s CPU-cap sweep: it now kills only inside the run's own transient scope.
Suites 32/80/33/45.

## kit-v0.4.8 — 2026-09-30 — handoff only: Clatter evaluated on paper and probed offline

`HANDOFF.md` §6 item 26: the findings (workers cannot reach the bus; an instance orchestrator may use the bus and tmux freely
short of naming the approval tool; messages are unauthenticated; approval commands travel as text to a session with no gate;
the relay's Enter on a pending permission prompt unverified) and candidate fixes, not ruled. No tool, rule or test changed.

## kit-v0.4.7 — 2026-09-30 — the source's briefing practices: a strict kill rule, asserted counts, two run forms

The practices of the source's methods list (2026-09-30), on the operator's "all approved". **Tools, rules and templates changed.**
- **A mutation kills only with its FAIL line:** an optional `expect_stdout_contains` per mutation; `bin/check --mutate` counts a
  kill only with the expected exit and that line, so a crash or another part's failure is not a kill; `bin/validate-claims`
  accepts the field and warns when a mutation names none (older runs stay valid). Tested with the real checker.
- **The solver brief** asks for that line, for every stated count asserted against a value fixed before the run, and for a
  table in `result.md` from each asserted part to its check and its killing mutation.
- **Two run forms:** `templates/runs/restatement-BRIEF.md` (an orchestrator-assembled restatement on byte copies, no worker,
  `.source-run` written) and `templates/runs/repair-BRIEF.md` (the task sections of a repair run), from the source's runs 205
  and 304, read from its git objects. `templates/runs/README.md` corrected: a no-worker restatement holds its copies under
  `output/`, where the claim's artifact must be.
- **A practice:** between an approval and its launch nothing the scan reads changes, and blocked files describe a pending
  packet, never quote it.
New tests fail on the previous code. Suites 32/80/33/43.

## kit-v0.4.6 — 2026-09-30 — the whole-run CPU budget enforced; the solver's long-wait paragraph; one note suffix

The source's methods list of 2026-09-30 19:20 (relayed by the operator), part 1: the items the kit shared and had not fixed, on
the operator's "we can work on part one while ud works on part 2". **Tools changed.**
- **The whole-run CPU budget is enforced** (its item 3; its run 346, 11.13 CPU-h of 8, only flagged): `bin/limits-exec` watches
  the run's cgroup; at the budget TERM to the launcher's process (Claude through `timeout`; Codex through `_ext.py`, which now
  stops the worker in order on TERM and keeps its session file), then after `cpu_grace_seconds` (`.limits`, default 30) KILL to
  everything left in the scope; exit 152, `cpu_cap_hit` in `usage.json` and on `EXIT-EXT`; never retried. The rule already said
  enforced; the code now agrees. Tested on a real systemd scope (a burner; a background job ignoring TERM; a run under the cap).
- **The solver brief says what a headless turn's end does** (its item 4; its runs 203, 338): ending the turn ends the run and stops
  background jobs; and what the CPU budget's enforcement does.
- **`bin/annotate-claim` appends its fixed ending once** (its item 7), leaving the approved text as given.
Not taken: its item 8 (`&gt;` in the approval printout: nothing in the kit's code escapes; probably the harness's display of the
hook's text) and item 5 (its own `DECISIONS.md`). New tests fail on the previous code. Suites 32/76/33/43.

## kit-v0.4.5 — 2026-09-30 — three defects the source found in its own tools, fixed here first

From the source's queued methods items (its `HANDOFF.md` at `89872a3`; its `DECISIONS.md` OD-72 to OD-74, read from git
objects), on the operator's "go". The source has not changed these tools yet. **Tools changed.**
- **A referee is given the ledger entries a claim rests on:** `bin/new-run --role referee` writes `input/ledger-premises.md` for a
  claim with `ledger` premises, by the new `bin/claims-extract --ids` (the extract's rules and the operator's exclusions; a
  superseded entry given and marked), and the brief says to compare every use with it. Three of the source's referee sets could not.
- **A queue stops at the plan's usage limit** (or a capacity refusal): the queue asks `bin/_ext.py queue-stop` after a failed run
  and releases nothing more (`QUEUE-STOP`); the source's four runs 316–319 were all burned by one quota stop. Tested on the real
  queue loop in a throwaway instance.
- **The packet scan takes a file that vanished after the walk as absent** (the source's run 295 failed its scan at release with
  `FileNotFoundError`); the packet's own files stay strict. The practice: nothing creates or removes files while a queue releases.
- `.cross-family-referee` names the referee's family, not the producer's (wording; the source's orchestrator misread it once).
New tests fail on the previous code, except the guard that a queue goes on after an ordinary failure. Suites 32/74/33/39.

## kit-v0.4.4 — 2026-09-30 — handoff only: the recalibration tabled

`HANDOFF.md` §6 item 12: the operator tabled ladder 2 ("I want to table that run"); the design and its cost estimate, as put to
him on 2026-09-29, are kept there. The calibration exception of `kit-v0.4.1` stays in force. No tool, rule or test changed.

## kit-v0.4.3 — 2026-09-29 — the handoff template's worker check; settings.local.json ignored

On the operator's "yes". `templates/HANDOFF.md` §0 checks for a worker of this tree only
(`pgrep -fa 'claude -p' | grep '[/]@NAME@/workspace-'`, and the same for `codex exec`): the old line matched every worker on
the machine and its own shell wrapper, and both instance sessions of 2026-09-29 stopped on it; the pattern was tested with a
stand-in worker (matched) and its own wrapper (not). Its stale `test_gate` count corrected (32). `.gitignore` names
`.claude/settings.local.json`, which Claude Code writes on "don't ask again" and which only a user's global ignore kept out of
git. The kit's `HANDOFF.md` records the proof instance's upgrade to `kit-v0.4.1` and canary 016. An instance at `kit-v0.4.1`
lacks only the template and `.gitignore`; neither changes how it runs.

## kit-v0.4.2 — 2026-09-29 — handoff only: the live tests passed

`HANDOFF.md` only. The review instance, upgraded to `kit-v0.4.1` by a session opened there, ran a Codex context canary (017,
exit 0) and a Codex run capped at three tool calls (018, exit 125, session file kept): `kit-v0.3.7`'s cap fix, `kit-v0.3.9`'s
socket place and `kit-v0.4`'s Codex note line are seen live. New open item: nested user namespaces inside the sandboxes
(bwrap `--disable-userns`), for a methods session. No tool, rule or test changed; an instance at `kit-v0.4.1` is current.

## kit-v0.4.1 — 2026-09-29 — the cross-family rule's loose ends

On the operator's "2. agree" to four follow-ups of `kit-v0.4` (`HANDOFF.md` §6 item 23). **Tools and rules changed.**
- **The family is read from the models that answered** when the run's record has them (`models_seen`), else from the approved
  `--model`; answered by another family than the approved one, or by two, the producer is unknown (a ruling needed). A
  fallback within a family (Opus 5.5 to 4.8) changes nothing.
- **A new instance enables `anthropic,codex` by default** (`bin/new-workspace` `DEFAULT_ROUTES`), and is warned when its routes
  cover one model family only; openrouter's family is its model's, per run.
- **`bin/packet-block` blocks a path that does not exist yet**, with a warning (the proof instance's `intake/` needed a
  `mkdir` first); a path outside the tree is still refused.
- **Recorded exception** (`RULES.md` §7): cross-family reads count before a model of each family has been through the
  `certify` and `sentence` ladders, because the read only adds a requirement; the recalibration closes it.
New tests fail on the previous code (T17 `test_answered_family`, T18RoutesAndBlocks). Suites 32/71/33/36.

## kit-v0.4 — 2026-09-29 — a cross-family referee read

Taken from the source's method change 59 on the operator's "59: make the change now". **What earns a tag changed**, which is
why the minor version moves. A `[PROVED]` claim now needs, beside its `certify` and `hypotheses` reads, a live `certify` hold
from the other model family than its producer's (Anthropic / OpenAI); a `[VERIFIED]` or `[NUMERIC]` claim under
`kit/claims/2` needs its `sentence` read from the other family. Families come from the run's approved `--model`
(`bin/_lib.py` `run_family`); a restatement takes its source run's family (`RUN/.source-run`); an unknown producer, or a
restatement of a run of the other family than the orchestrator's, needs the operator's ruling (`RUN/.cross-family-referee`).
`bin/merge`, `bin/close-run` and `bin/ledger-claims` print each claim's family line; `bin/close-run` names the missing
cross-family run instead of offering the same-family pair again (a kit addition). The Codex harness notes say to `cd` into
`$KIT_LEAN` in the same command. `RULES.md` §4, §7 ("a second model never replaces the second question"; the cross-family read
is a third read) and §8, `SCHEMAS.md` §4, `FLOW.md`, `LESSONS.md` "A cross-family certify read".
Differences from the source: no run-number cutoff (the rule binds every run; no instance had ledgered claims), and the
orchestrator's family is one constant. **Consequences to put to the operator:** an instance that enables only the `anthropic`
route cannot meet the rule without a ruling per run (an OpenAI read needs the `codex` route or an OpenAI model on
`openrouter`); and `RULES.md` §7 "Calibrate before trusting" says a model is not used in a role before that role's ladder, while
no OpenAI model has been through a referee ladder in the kit. New tests fail on the previous code (four in T17CrossFamily; the
`close-run` one also caught a mutation). Suites 32/68/33/36. A harness note changed: a Codex canary is due before real work.

## kit-v0.3.9 — 2026-09-29 — four changes from the source: the egress socket, a block beats an open root, kept check records, outside input

Taken from the source's method changes 56–60 (committed there 2026-09-29, read from its git objects only), on the operator's
"1. yes 2. adopt". **Tools, rules and a template changed.**
- **The egress socket's host side** (its change 60): a no-network Codex run's proxy socket moves from
  `.claude/state/ext/<run>/egress.sock`, which passes Linux's 107-byte limit for a long root and slug (the launch then dies at
  bind after the approval is spent; reproduced here), to `$XDG_RUNTIME_DIR/kit-egress/` or `/tmp/kit-egress-<uid>/` (0700);
  neither directory visible or connectable inside; a run with no exit record is recorded as never started.
- **A block beats an open root** (the generic half of its change 58): a blocked path inside open material, or inside a
  launched run's `output/`, no longer excuses its own text; the kit also takes a line rule's matching lines out of open
  material (the same defect for the kit's other kind of block). The source's own blocked paths are not taken.
- **A ledgered run's check record is kept** (its change 56): `bin/check` keeps `check.<generated>.json` before re-checking a
  run with ledgered claims (`CHECK-KEPT`), never overwriting one.
- **Outside input** (its changes 57, 58): `RULES.md` §8 "Outside input" (intake record first; classes ruled per item;
  premise only by a verify-or-refute claim or a ruled conditional source premise; framing only under a ruling, tagged;
  analyst-drafted marked; input families counted for independence); `templates/intake-record.md`; `intake/` blocked in a new
  instance's `data/packet-rules.json` (`bin/new-workspace`'s `DEFAULT_PACKET_RULES`); `bin/verify-data` check 6. The source's
  own records and rulings are not taken.
Not taken: its change 59 (cross-family referees; ruling pending), 61 (Magma), 62 (one claim of its own). Every new test fails on
the previous code except the two that guard unchanged behaviour (an unledgered run rewritten, the same bytes already kept).
Suites 32/64/33/36. Not yet seen on a live launch here; the proof instance (at `kit-v0.3.8`) does not have it.

## kit-v0.3.8 — 2026-09-29 — the sentence referee counts the claim's pinned output

`HANDOFF.md` §6 item 20, on the operator's "a". **A referee brief changed** (`bin/new-run --question sentence`): the checker's
assertions are the script's exit conditions and the claim's `expect_exit`, `expect_stdout_contains`, `expect_stdout_sha256`,
which `bin/check` enforces; a value only printed, and pinned by none of them, is still not asserted; the frozen-count question
covers a pinned value too. The live read that found it (the review instance's run 016) returned `gap` on a correct, pinned
count. The new test fails on the previous brief. Suites 32/54/33/32. §6 item 14 ruled: the review instance is kept.

## kit-v0.3.7 — 2026-09-29 — a capped Codex run keeps its session file; the live canary pass

The live pass of `kit-v0.3.6` in the review instance (runs 008–016, operator's approvals, all at `--effort low`; `HANDOFF.md`
§6 item 13): every item exercised, one bug found. **Tools changed.**
- A Codex run stopped at its tool-call cap (run 009) or its wall cap (run 011) recorded no model, effort or
  `multi_agent_version`: the whole sandbox was stopped before its script copied the session files. A cap now sends TERM to
  the codex process only; the script copies them and ends whatever the worker left running; the sandbox is stopped 30 s
  later only if it has not ended. Both cap tests assert the session file and fail on the previous code.
- Confirmed live: no Codex sub-agents (`multi_agent_version: disabled`, run 010); the model fallback flagged (run 008).
- New open item: the `sentence` referee does not count `expect_stdout_contains` (run 016; `HANDOFF.md` §6 item 20).
Suites 32/54/33/32. The instance's upgrade to this tag is not done; the fix is not yet seen live.

## kit-v0.3.6 — 2026-09-28 — the model on the record; no Codex sub-agents; a Codex tool-call cap

`HANDOFF.md` §6 items 5, 6, 10, 15, 16 and 17, on the operator's "1. yes 2. a 3. your rec 4. yes". **Tools changed.**
- **The models that answered are recorded** (15): from the run's own transcript onto `EXIT-EXT` (`models_seen=`,
  `model_fallback=`), `RECORD-EXT.md` and a warning; `bin/close-run` and `bin/ledger-claims` print a `MODEL:` line for the run
  and its referees. Flagged, never refused.
- **No Codex sub-agents** (16): the model catalog's `multi_agent_version: v2` turned them on whatever the flag said; Codex
  reads its binary's catalog without the key, and `bin/run-external`'s preflight refuses a Codex launch whose prompt, rendered
  offline with the launch's settings, still offers them (`bin/_ext.py codex-probe`), before the approval.
- **The main thread's session file** (17): chosen by the transcript's thread id; any other kept as `launch.rollout.sub-N.jsonl`.
- **A Codex tool-call cap** (10, option a): `--max-turns` now applies to Codex, counted from the transcript (exit 125,
  `turn_cap_hit=` on `EXIT-EXT` for every route); the brief-versus-cap check covers Codex.
- **Inherited `ANTHROPIC_*` variables dropped** (5); **one test ties the two default turn caps** (6).
Every new test fails on the previous code, except item 6's, which guards values that already agreed. Suites 32/54/33/32. Not yet
exercised on a live launch: the next canary pass (the review instance) is planned for that.

## kit-v0.3.5 — 2026-09-27 — the source's `bin/claims-extract`

Taken from the source (its method change 52) on the operator's "do 52". **Tools added and changed.**
- `bin/claims-extract` (new): a worker's view of `CLAIMS.md` by fixed rules (live entries; header, statement, Lean declarations
  or artifact type, Claimed, Premises, Supersedes; the notes on them verbatim), `--through C-NNN` for the ledger as of an
  entry, `--out` ledgers its sha256. Where the source hard-codes them, the kit reads the excluded entries and notes from
  `data/packet-rules.json` "extract" and takes the library prefix as `--library PREFIX`; the extract names what it leaves out
  by id, never the operator's reason. It also handles `Artifact: none` and a statement over several lines, which the kit's
  ledger can write.
- `bin/packet-block --extract C-NNN "why"`, `--extract-note C-NNN DATE "why"`: the operator adds to that list, ledgered; the
  hook's existing gate on `packet-block` and the list covers both.
Every new test fails on the previous code. Suites 32/52/33/27. `HANDOFF.md` §6 item 19 closed.

## kit-v0.3.4 — 2026-09-27 — four changes from the source's methods sessions of 2026-09-26

Taken from the source (its method changes 49–52 and 55), on the operator's "yes". **Tools changed.**
- Every referee brief says a headless referee must finish its checks and write `referee.json` in its turn (its 49).
- `bin/check` parses the axioms line of a Lean name ending in a prime (its 51).
- A run with any file in `output/` also counts as launched (its stricter 55).
- Route-verdict words in a packet (its 50), configurable: `"verdicts": true` in `data/packet-rules.json` (new instances) or an
  instance's own pattern; off without the key.
Not taken yet: its `bin/claims-extract` (52), which hard-codes its own exclusions and library prefix (`HANDOFF.md` §6 item 19).
Every new test fails on the previous code. Suites 31/50/33/27.

## kit-v0.3.3 — 2026-09-26 — a no-network Codex command cannot reach the proxy's socket

Found by the ud orchestrator while porting the Codex fix, confirmed here by test: on a run without the network, a command in
the nested sandbox could still `connect()` to the egress proxy's unix socket (`/opt/kit/egress.sock`) and reach the provider's
hosts; its own network namespace blocked only TCP, and a read-only mount does not stop a socket connect. The wrapper
(`.claude/sandbox/kit-shell`) now covers the socket with `/dev/null` on such a run; `T5CommandsApartFromCodex` dials it and
fails on the previous wrapper. One file an instance copies changed (and its test). Suites 31/47/33/27.

## kit-v0.3.2 — 2026-09-25 — handoff only: the proof instance upgraded; three open items

`HANDOFF.md`: the proof instance at `kit-v0.3.1` (§0 item 7, §6 item 11 closed); §6 items 15–17 from its canaries (a silent
model fallback on the Claude route; Codex multi-agent live despite the flag; the wrong rollout copied). Nothing an instance
copies changed.

## kit-v0.3.1 — 2026-09-25 — the outside review's fixes; a Codex worker's commands run apart from Codex

A methods session, on the operator's "1: yes 2: yes 3: yes" to GPT-5.6 Sol's review of `kit-v0.3` (run 003 in
a review instance: 13 findings, all confirmed). **Tools, the hook's sandbox shim and the method changed.**

- **Approvals:** every launch approval binds its flags, `--model` included (F1); the host's own checks run before any approval,
  and a queue pre-checks each run with them (F7); a queued run is released by an atomic claim (F4); the queue's lifetime is
  derived in one place (F12).
- **Launches:** a run directory is launched once, so no worker sees a previous attempt (F2).
- **The record:** the `kit/claims/1` exemption needs the brief the launch approval bound (F3); a `ledger` premise must exist (F8);
  `CLAIMS.md` is written before its ledger lines (F11); `SCHEMAS.md` on approvals (F13).
- **The packet scan:** the launch path rebuilds its index (F5); oversized text fails loudly (F9); an exception follows its
  file's bytes (F10); F6 recorded as outside the gate's stated limit; new instances block `DIRECTION.md`, `HANDOFF.md` and
  `handoffs/` from the start.
- **The Codex route** (found by this session's canaries, not by the review): commands run in their own nested sandbox through
  `.claude/sandbox/kit-shell`, installed as `/opt/kit/bin/bash`, with Codex's home (the token, the session log) hidden and no
  network on a run without it; the transcript reaches the host through pipes with a sha256 chain the record checks. Verified
  live (run 007). Residual: Codex's in-process patch tool.
- **Smaller:** run 001 is the first enabled route's canary; a Codex "model at capacity" refusal is reported as that; the canary
  template's Part B clarified, with a `/proc` descriptor probe.

Verified: suites 31/47/33/27; every new test fails on the previous code (F4's test errors there, lacking the token function);
the instance creation path; live Codex runs 005–007. Not exercised on a real launch: `HANDOFF.md` §6 item 13.

## kit-v0.3 — 2026-09-25 — the source's method changes 32–48, ported

A methods session, on the operator's evaluation rulings of 2026-09-25 (`HANDOFF.md` §3). One kit commit per source change,
renamed through the port's map, each with its tests and its `LESSONS.md` line; the suites pass after each. **Tools, the hook,
the schema and the method changed.**

- **Sandbox** (32): both sandboxes remount their root read-only after the binds; the hook ledgers only its own tree's sessions.
- **Method** (33, 34, 38): no limit on method changes or methods sessions; no spending cap on any run; a wall-clock cap on every
  route (4 h Claude, 2 h Codex).
- **Record** (35, 36, 37, 40, 41): every Lean signature captured; `bin/claim-deps`; notes do not vouch; schema `kit/claims/2` with
  `premises` and a conditional marker (`kit/claims/1` only where a run's brief names it); a `sentence` referee for every script
  claim, without which VERIFIED and NUMERIC stay pending.
- **Approvals and launches** (43, 44, 45, 46, 48): one approval for several notes; a queue for runs approved together, living for
  its runs' wall caps plus 30 minutes; the ChatGPT plan's usage limit detected; the network paragraph built into networked
  referees' briefs.
- **Computer algebra** (39), redesigned: the trust rule in `RULES.md` §2; SageMath as an optional module, `bin/new-workspace
  --sage`, `.kit-sage`.
- **The packet scan** (42, 47, 48), redesigned: what no packet may carry is the instance's `data/packet-rules.json`, empty at
  creation, filled by the operator with the new `bin/packet-block`; `bin/packet-except`; both lists behind the hook.
- **The outside review's fixes** (47): header parsing, per-declaration signature markers, the wall-cap exit codes, `--queued`
  with `--detach` refused.

Verified: suites 29/41/33/24 (one skip: the Lean end-to-end test, which ran and passed in a throwaway instance with a library
linked); a throwaway instance with both modules and both routes passed its suites, its data check and a live packet refusal
(dry run). Found by that instance: a missed test edit, fixed, and a residual for trees under `/tmp`, recorded. Not exercised on
a real launch: `HANDOFF.md` §6 item 13. The proof instance stays at `kit-v0.1.2` (§6 item 11).

## kit-v0.2.1 — 2026-09-23 — handoff only: recalibration recorded

`HANDOFF.md` §6 item 12: recalibrate for the current models (Opus 5.5 is new) with a ladder harder than ladder 1, at a time the
operator chooses. Nothing an instance copies changed; an instance at `kit-v0.2` is at this version's method.

## kit-v0.2 — 2026-09-23 — a session works on the tree it was opened in

A methods session, on the operator's "agree, go" (10:43 MST) to three fixes, after a reset `cd` ran eight preflight
commands against the kit instead of the proof instance (`LESSONS.md` "A session works on the tree it was opened in"). **Tools
changed**; the hook did not.

- **Rule** (`RULES.md` §11): an instance is driven only from a session opened in it; a kit methods session that upgrades an
  instance puts the diff to the operator and writes the opening prompt, and a session in the instance applies it.
- **Tools**: no ledger writer creates `LEDGER.log` any more. `_lib.ledger` (via the new `_lib.append_ledger`), the Codex
  outbox drain in `_ext.py`, `_approval.ledger` and `bin/ledger` open it without create and stop with "this tree is not an
  instance"; `bin/approve` refuses before writing any record, so an approval never exists without its ledger line;
  `bin/handoff-archive` refuses before archiving. `bin/verify-data` prints `root: <tree>` first (and so does `bin/close-run`,
  which runs it first). The hook's own ledger writer is unchanged: it runs only where it is registered, in an instance.
- **Tests**: `tests/test_tools.py` +5 (`T5WrongTree`: 21 tests). All five fail on `kit-v0.1.2`'s tools and pass on these.
- **Template**: `templates/HANDOFF.md`'s preflight names the tree by absolute path (`git -C @ROOT@`, `@ROOT@/bin/…`), except the
  ledger line, which the hook allows only as a plain `git diff`; a `pwd` check comes first to cover it.
- The proof instance stays at `kit-v0.1.2` until the operator rules on this diff (`HANDOFF.md` §6 item 11).

## kit-v0.1.2 — 2026-09-23 — `SCHEMAS.md` brought up to date; the proof instance upgraded

A methods session, on the operator's "5. update SCHEMAS.md" and "1a: a / 1b: a" (2026-09-23 MST). No tool, hook, test or
template changed.

- `SCHEMAS.md`: the provenance paragraph no longer says the code "still cites" numbered method changes (the port converted
  them to lesson labels); every run number and dated ruling of the source is marked as the source's, so an instance's own runs
  with the same numbers are not mistaken for them; `ORCHESTRATOR.md` and "HANDOFF.md next-step 2", which the kit does not
  have, are gone; the library's master list is `lean.SHA256SUMS`, as the code names it, not `lean/SHA256SUMS`.
- The proof instance upgraded from `3b1b23b` to this tag: `RULES.md`, `LESSONS.md` and `SCHEMAS.md` replaced
  by this tag's bytes (every other copied file was already identical), `KIT-VERSION` rewritten with an `upgraded:` line,
  recorded in its handoff.

## kit-v0.1.1 — 2026-09-22 — the build record moves under `history/`; a dangling reference fixed

A methods session, on the operator's ruling of `HANDOFF.md` §6 item 2 (20:51 MST, "agree" to four suggestions). No tool,
hook, test or template changed.

- `PLAN.md`, `INVENTORY.md`, `PORT-DIFF.md` → `history/`. They are the port's audit trail, not the method. A public release is
  a fresh repository from a tagged export without `history/` or `HANDOFF.md`; this repository's git history carries all three,
  so it is never the thing pushed.
- `RULES.md` §0 said the fixed names were "listed in `PORT-DIFF.md`", a file `bin/new-workspace` never copies: every instance,
  the proof instance included, pointed at a file it lacked. The names are now `SCHEMAS.md` §7, written from the live code (the
  port-time `KIT_LEAN_TOOLCHAIN` is gone since the fresh-read fixes; `.kit-lean` replaced it). The proof instance is unchanged
  and gets this only by a methods-session diff.
- `LESSONS.md` says in its header that the records it cites are private and do not ship. It still ships.

## kit-v0.1 — 2026-09-22 — first complete kit; proven by instantiation

Built in one session from the source workspace at its commit `11d2212`, in six phases, each ending at an
operator gate:

- **P1** `8213b38` — `INVENTORY.md` (every source file classified), `LESSONS.md` (one line per rule with its incident).
- **P2** `939a5f1` — `RULES.md` (the law, no run numbers or dated rulings, every rule pointing to its lesson, a dropped list
  with reasons), `FLOW.md` (one page).
- **P3** `6605bd4` `7c9af50` `6280ada` `1a13b2b` `d5d628b` `57b68a8` — the port: tooling copied whole; root derived from each
  tool's location; the formal library made optional; schema ids `kit/*`; `maths-*` → `kit-*`, owner → operator; the source,
  the machine and the problem stripped; a fresh reader's twelve findings fixed (worst: a hand-copied kit would have launched an
  unsandboxed worker after a valid approval — `run-external` now refuses unless the hook is registered); citations converted to
  lesson labels. 72 tests. `PORT-DIFF.md` explains every hunk.
- **P4** `d9f559b` `3b1b23b` — `templates/` (twelve forms) and `bin/new-workspace`, which fills the settings templates with the
  instance's root, writes the problem skeleton, the handoff, the ledger, `.kit-routes`, `.kit-lean`, `KIT-VERSION`, run 001 as the
  context canary, archives the first handoff, and refuses to finish unless the instance passes its own data check.
- **P5** (in the proof instance, made at `3b1b23b`) — calibration ladder 1 on S(3) through the instance's tools alone:
  canaries on both enabled routes; design run; six `certify` referees; three solvers; the evaluator with the locked key.
  **Catch 3/3, exact verdict 3/3, false positives 0/3, pointer hits 3/3, recovery 3/3 — the source's ladder 1 numbers,
  on a different problem, with no proof assistant.** 13 runs, 30.6 min wall, ≈$13.5 nominal.
- **P6** this commit — `KIT-CHANGELOG.md`, the tmpfs lesson and rule, `HANDOFF.md` for the next project, the tag.

Known residuals at this version are in `HANDOFF.md` §6. Not in this version: an agent as operator (P7, charter in
`HANDOFF.md` §9); a read-only remount of the sandbox's parent chain; a turn or request cap on the Codex route (its only
model-side cap is wall time); a ladder for the `hypotheses` referee question.
