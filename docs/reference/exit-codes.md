# Exit codes

What each exit status of a tool, a launch path or the hook means, and where in the code it is set.

Every code below is from the code itself. A tool not listed for a code never exits with it on purpose. Python tools
built on `argparse` also exit 2 on a malformed command line, and any Python tool exits 1 on an uncaught error. The
run's exit and its caps are also recorded on the `EXIT-EXT` ledger line (`exit=`, `wall_cap_hit=`, `turn_cap_hit=`,
`cpu_cap_hit=`) ([ledger events](ledger-events.md)).

## Table

| code | tool(s) | meaning | source |
|---|---|---|---|
| 0 | every tool | success: nothing refused, nothing found | |
| 0 | [bin/claim-deps](tools/claim-deps.md) | always: a report, never a block | `bin/claim-deps`, `main` |
| 0 | `bin/_ext.py queue-stop` | the queue must stop: the run ended on the plan's usage limit or the provider's capacity refusal (the reason is printed) | `bin/_ext.py`, `main` |
| 0 | [bin/run-external](tools/run-external.md) `--queue` | the queue ran, or stopped; it exits 0 whatever its runs' statuses, each of which is on its `QUEUE-RUN` ledger line | `bin/run-external`, queue loop and `--queue --detach` |
| 1 | [bin/check](tools/check.md) | `overall` is `fail`: a claim failed, `doc_errors` is not empty, or `result.md` is missing or over 150 lines | `bin/check`, `main` |
| 1 | [bin/close-run](tools/close-run.md) | `bin/verify-data` reported findings (nothing else ran), `bin/merge` failed, the check failed, or a claim is FALSIFIED, BLOCKED or PENDING | `bin/close-run`, `main` |
| 1 | [bin/ledger-claims](tools/ledger-claims.md) | nothing appended: a named claim is missing, already recorded, changed since the check, not recordable by its earned tag, or names a supersede target or `ledger` premise not in `CLAIMS.md` | `bin/ledger-claims`, `main` |
| 1 | [bin/lint-brief](tools/lint-brief.md) | an ERR line (with `--packet`: a packet finding) | `bin/lint-brief`, `main` |
| 1 | [bin/validate-claims](tools/validate-claims.md) | an ERR line | `bin/validate-claims`, `main` |
| 1 | [bin/verify-data](tools/verify-data.md) | at least one finding | `bin/verify-data`, `main` |
| 1 | [bin/handoff-archive](tools/handoff-archive.md) | the archive name exists already, or the archive cannot be written | `bin/handoff-archive`, `main` |
| 1 | [bin/check-env](tools/check-env.md) | at least one line is `FAIL`: a required part is missing (Python 3.9 or newer at `/usr/bin/python3`, a working bwrap, GNU time, `timeout`, git, the Claude CLI), `kit-env.json` has a problem, or an always-mounted module's `check` exited non-zero. `WARN` lines do not change the status | `bin/check-env`, `main` |
| 1 | every Python tool that ledgers (`bin/check`, `merge`, `close-run`, `new-run`, `ledger-claims`, `annotate-claim`, `verify-data`, `claims-extract --out`, `bin/_ext.py record`) | no `LEDGER.log` at the root: this tree is not an instance; no ledger line written, though the tool's own output (`check.json`, `verdict.md`, the run directory, the `--out` file) may already be on disk; for `bin/check` this 1 looks like `overall: fail` (→ **A session works on the tree it was opened in**) | `bin/_lib.py`, `append_ledger` |
| 1 | [bin/packet-block](tools/packet-block.md), [bin/packet-except](tools/packet-except.md) | no `LEDGER.log` at the root: an uncaught error after the list file was already written; no ledger line | `bin/_approval.py`, `ledger` |
| 1 | [bin/run-external](tools/run-external.md) | `systemd-run` failed for `--detach` or `--queue --detach` (for a queue, its approvals are already used), or the search gateway or the licence relay did not start (the approval is used; nothing launched) | `bin/run-external`, top level (detach, queue, network and licence blocks) |
| 1 | `bin/_ext.py codex-probe` | Codex, rendering the launch's prompt offline, still offers sub-agents or a disabled feature; `bin/run-external` turns it into a refusal (exit 2) | `bin/_ext.py`, `main` and `probe` |
| 1 | `bin/_ext.py queue-stop` | the queue goes on | `bin/_ext.py`, `main` |
| 1 | `bin/_ext.py codex` | the egress socket's directory is not a private directory of this user, or the socket path is over 107 bytes | `bin/_ext.py`, `egress_sock_path` |
| 1 | [bin/watch-run](tools/watch-run.md) | no run directory, or no transcript yet | `bin/watch-run`, `find_log` |
| 2 | every Python tool using `bin/_lib.py`'s `die` (`bin/new-run`, `check`, `merge`, `close-run`, `ledger-claims`, `annotate-claim`, `claims-extract`, `lint-brief`) | refused: bad arguments, an unknown or ambiguous run, a missing or invalid JSON file, an input `bin/new-run` refuses, a `bin/new-run --module` that is not a licence module of `kit-env.json` (before anything is written), a note `bin/annotate-claim` refuses. Usually before anything is written, but `bin/new-run` can stop after making the run directory (a duplicate input basename, a missing artifact or deps file, unextractable ledger premises), and `bin/close-run` after the check and merge have written their files | `bin/_lib.py`, `die` (default code 2); `bin/lint-brief`'s usage error is its own `sys.exit(2)` |
| 2 | [bin/check](tools/check.md) | a kept check record `check.<generated>.json` exists with other bytes; nothing checked | `bin/check`, `keep_cited_record` |
| 2 | [bin/merge](tools/merge.md) | wrong usage, or no `check.json` | `bin/merge`, `main` |
| 2 | [bin/ledger](tools/ledger.md) | no `LEDGER.log` at the root; nothing appended | `bin/ledger`, top level |
| 2 | [bin/limits-exec](tools/limits-exec.md) | wrong usage, or the run directory does not exist | `bin/limits-exec`, top level |
| 2 | [bin/run-external](tools/run-external.md) | refused by the launcher's own checks, before any approval was touched: bad or unknown arguments, `--budget`, no `--model`, a bad `--via`, `--wall-hours` or `--effort`; no run directory or `BRIEF.md`; a run name not unique across workspaces; the brief allows more tool calls than `--max-turns`; the harness note does not match the flags; the run was launched before; a `--module` that `bin/_ext.py module-check` refuses, or a `--module` set that differs from `RUN/.modules`; the packet carries blocked material or the scan failed; `--queued` with `--detach`; the host preflight (settings, worker-net settings, Codex sub-agent probe, OpenRouter key); the unit is already running; a queue with no run, a bad queue flag, or a run that fails the launch checks | `bin/run-external`, top level, `usage` and `preflight` |
| 2 | [bin/astra-session](tools/astra-session.md) | the OpenRouter key file is unreadable or empty | `bin/astra-session`, top level |
| 2 | [bin/new-workspace](tools/new-workspace.md) | refused: the directory exists or lies inside the kit, a bad slug or route, a missing `--lean`, `--lean-toolchain` or `--sage` target, an `--env` file that is missing or has a problem (before anything is written), the kit is not a git repository or has uncommitted changes, or a step inside the new instance failed | `bin/new-workspace`, `die`, `env_file_problems` |
| 2 | [bin/handoff-archive](tools/handoff-archive.md) | no `HANDOFF.md`, or no `LEDGER.log` at the root | `bin/handoff-archive`, `main` |
| 2 | [bin/verify-data](tools/verify-data.md) | `--write-lean-manifest` with no library linked | `bin/verify-data`, `main` |
| 2 | [bin/packet-block](tools/packet-block.md), [bin/packet-except](tools/packet-except.md) | wrong usage, an empty reason, or (`--lines`) not a regular expression | `bin/packet-block`, `main` and `extract`; `bin/packet-except`, `main` |
| 2 | `bin/_approval.py` | wrong usage, or `--wall-seconds` not a whole number | `bin/_approval.py`, `main` |
| 2 | `bin/_ext.py codex` | no Codex binary, the model catalog could not be made, or (without `--network`) a `--module` that `module-check` refuses; nothing launched. Under `bin/run-external` this comes after the approval was used, and the launcher exits with it | `bin/_ext.py`, `cmd_codex` |
| 2 | `bin/_ext.py module-check`, `licence-relay` | a named module is not in `kit-env.json` or names no licence server, two named modules share a port, or the file has any problem; `module-check` prints each problem. `bin/run-external` turns it into a refusal (exit 2) before any approval | `bin/_ext.py`, `module_check`, `main` |
| 2 | `bin/_ext.py` | unknown subcommand or wrong arguments | `bin/_ext.py`, `main` |
| 3 | [bin/approve](tools/approve.md), [bin/manifest](tools/manifest.md) | refused: the arguments do not parse, a run is not found or has no `BRIEF.md`, a symlink or a file that is not regular in the run directory, a launch approval without `--model` in its flags, a `--digest` that does not match, or is not one digest of at least 8 hex characters per target, a `--ledger` run not yet closed (no `output/claims.json`, `check.json` or `verdict.md`), a malformed notes file; for `bin/approve`, no `LEDGER.log` | `bin/_approval.py`, `approve_main` |
| 3 | `bin/_approval.py check`, `queue`, `queued` | no valid approval for these bytes: none on file, used, expired, other ids, other flags, flags not bound, or bytes changed ("no user approval for these hashes"); a queued run not releasable | `bin/_approval.py`, `main`, `check`, `queue_start`, `queue_take` |
| 3 | [bin/run-external](tools/run-external.md) | the launch approval was refused, a queue's approvals could not all be used, or a queued run could not be released | `bin/run-external`, top level (approval step and `--queue`) |
| 3 | [bin/astra-session](tools/astra-session.md) | a headless session without a valid `--session` approval, or an interactive session without a terminal | `bin/astra-session`, top level |
| 3 | [bin/ledger-claims](tools/ledger-claims.md) | no valid `bin/approve --ledger` approval for exactly these ids and bytes | `bin/ledger-claims`, `main` |
| 3 | [bin/annotate-claim](tools/annotate-claim.md) | no valid `bin/approve --annotate` (or `--annotate-batch`) approval for exactly this text | `bin/annotate-claim`, `main` |
| 3 | [bin/packet-block](tools/packet-block.md) | PATH is not inside the tree (not an approval refusal) | `bin/packet-block`, `main` |
| 3 | [bin/packet-except](tools/packet-except.md) | FILE is not a file inside the tree (not an approval refusal) | `bin/packet-except`, `main` |
| 4 | [bin/lint-brief](tools/lint-brief.md) `--packet` | the packet scan itself failed (an unreadable rules or exceptions file, a blocked text too large to index); nothing was checked. `bin/run-external` refuses with exit 2 | `bin/lint-brief`, `main` |
| 124 | [bin/run-external](tools/run-external.md), `bin/_ext.py codex` | the wall-clock cap (`--wall-hours`) stopped the worker, or the deadline had passed before a retry; `wall_cap_hit=1` | `bin/_ext.py`, `cmd_codex`; `bin/run-external`, the Claude launch loop (`timeout`'s status) |
| 125 | [bin/run-external](tools/run-external.md) `--via codex`, `bin/_ext.py codex` | the tool-call cap (`--max-turns`) stopped a Codex worker; `turn_cap_hit=1`. On the Claude routes the turn cap is Claude Code's own and `turn_cap_hit` comes from the transcript, not from 125 | `bin/_ext.py`, `cmd_codex`; `bin/run-external`, Codex branch |
| 137 | [bin/run-external](tools/run-external.md) (Claude routes) | the worker was killed: by `timeout` 60 s after the wall-clock TERM (counted as the wall cap only if the deadline has passed), or by the memory cap or the user; passed through | `bin/run-external`, the Claude launch loop |
| 152 | [bin/limits-exec](tools/limits-exec.md), [bin/run-external](tools/run-external.md), `bin/_ext.py codex` | the whole-run CPU budget (`cpu_hours`) was used: TERM, then KILL to the run's scope (128 + SIGXCPU); `cpu_cap_hit=true` in `usage.json`; never retried (→ **The whole-run CPU budget is enforced**). `bin/_ext.py codex` returns 152 on any TERM it receives, which it takes to be the budget's | `bin/limits-exec`, top level; `bin/_ext.py`, `cmd_codex` (`on_term`); `bin/run-external`, launch loop |
| other | [bin/run-external](tools/run-external.md), [bin/limits-exec](tools/limits-exec.md) | the worker's own status (`claude -p` or `codex exec`), passed through; with `--detach`, a launch that ends within seconds exits with its status | `bin/run-external`, end of script; `bin/limits-exec`, end of script |

## The hook

`.claude/hooks/sandbox.py` always exits 0. Its decision is the JSON it prints: `allow` (possibly with rewritten
input), `deny` with a reason ([hook refusals](hook-refusals.md)), or `ask` (the approval prompt it words for the tap
route). An orchestrator call the gate has no objection to gets no JSON at all, so Claude Code's own permission
handling applies; input that is not JSON gets no decision either. An error inside the gate refuses gated calls only; any other error
inside the hook is a `deny` ("Sandbox hook error"), never an open sandbox. `.claude/hooks/mirror-transcripts.sh`
always exits 0.

## Reading a refusal

- **2 before 3.** `bin/run-external` runs every check it can make without the approval first, so an exit 2 from its
  own checks means nothing was approved or spent ([RULES.md §6](../../RULES.md#6-approvals--the-gate)). The exception
  is a status passed through after the launch began: on the Codex route `bin/_ext.py codex` returns 2 when it has no
  binary or model catalog, or refuses a module, after the approval was used. A licence module's own checks
  (`--module` against `kit-env.json` and `RUN/.modules`) are among the launcher's, so they spend nothing. Exit 3 means the approval check refused,
  which is the stop: "no user approval for these hashes".
- **3 from the packet tools** is a path outside the tree, not an approval.
- **124, 125, 152** are caps the kit enforces ([RULES.md §9](../../RULES.md#9-the-sandbox--enforced-not-convention)).
  The `EXIT-EXT` ledger line records them (`wall_cap_hit=`, `turn_cap_hit=`, `cpu_cap_hit=`); for a Codex run,
  `RECORD-EXT.md` also notes a wall-clock or tool-call cap. `bin/close-run` does not report them.
