# Layout of an instance

Every file and directory an instance holds, what writes it, and who may read it.

An instance is made by [bin/new-workspace](tools/new-workspace.md) at a new directory outside the kit, for example
`~/kits/my-problem`. Paths below are relative to the instance's root. The rule for the record as a whole is
[RULES.md §8](../../RULES.md#8-the-record); what a worker can reach is [RULES.md §9](../../RULES.md#9-the-sandbox--enforced-not-convention).

**Readers.** *User*: every file ([RULES.md §4](../../RULES.md#4-roles--three-plus-ad-hoc)). *Operator agent*: what the
user gives it, never the never-read list there (credentials, licence and auth files; `data/locked/`; a run's output while
it is in flight; the ledger log). *Orchestrator*: every file except that never-read list and where a row says otherwise. *Worker*: its own run directory only, plus the read-only mounts listed under
[Run directory](#run-directory). *Packet* means the file can reach a worker only by being copied into a run's packet (`BRIEF.md`, `HARNESS-NOTE.md`,
`input/`),
and the packet scan applies ([RULES.md §8](../../RULES.md#8-the-record), → **No packet carries blocked material**).

## Instance root

| path | what it is | written by | read by |
|---|---|---|---|
| `RULES.md`, `SCHEMAS.md`, `FLOW.md`, `LESSONS.md` | the rules, schemas, overview and lessons | copied from the kit by `bin/new-workspace`; changed only in a methods session | orchestrator (reads `RULES.md` at session start); open material for the packet scan |
| `CLAUDE.md` | a two-line pointer: orchestrator to `RULES.md` and `HANDOFF.md`, workers to their brief (→ **`CLAUDE.md` is injected in full into every worker**) | copied | every Claude Code session opened here |
| `DIRECTION.md` | the direction brief, from [templates/DIRECTION.md](../../templates/DIRECTION.md) | `bin/new-workspace` (template); the user or an outside model; header notes by the orchestrator on the user's word | user, orchestrator. Blocked from every packet by default |
| `HANDOFF.md` | the current pointer sheet for the next orchestrator, from [templates/HANDOFF.md](../../templates/HANDOFF.md) | `bin/new-workspace` (template); every orchestrator at its handoff. The hook archives it before the first touch in a session ([bin/handoff-archive](tools/handoff-archive.md)) | orchestrator, read whole with the Read tool (→ **`HANDOFF.md` holds the current pointer and nothing else**). Blocked from every packet by default |
| `LEDGER.log` | the append-only event log, `utc \| actor \| run \| event \| detail` ([event types](ledger-events.md)) | created by `bin/new-workspace`, whose run 001 writes its first line; appended by the hook, [bin/ledger](tools/ledger.md) and every tool that ledgers. The user makes it append-only with `chattr +a` | the user only. The hook refuses the orchestrator's Read, Grep and Glob of it and any Bash command naming it except a plain `git add`, `commit`, `status` or `diff --numstat`/`--stat` (→ **`LEDGER.log` is append-only**) |
| `CLAIMS.md` | the claims record, one entry per claim ([SCHEMAS.md §5](../../SCHEMAS.md#5-claimsmd-entry--appended-by-binledger-claims-run-id-on-the-users-approval)) | created by the first [bin/ledger-claims](tools/ledger-claims.md); appended by it and by [bin/annotate-claim](tools/annotate-claim.md); never edited | user, orchestrator; [bin/ledger-claims](tools/ledger-claims.md), [bin/annotate-claim](tools/annotate-claim.md), [bin/claims-extract](tools/claims-extract.md); open material for the packet scan. Never copied into `input/` under its own name; a worker's view of it is [bin/claims-extract](tools/claims-extract.md)'s output |
| `KIT-VERSION` | the kit commit, tag and path the instance was made from, and its problem, routes, library, SageMath environment and environment file ([fields](configuration.md#kit-version)) | `bin/new-workspace` | user, a methods session upgrading the instance. No tool reads it |
| `kit-env.json` | the environment file: `locked_dir`, modules, licence modules, `worker_path`, the CLIs, `codex_bin_dir`, model families ([fields](configuration.md#kit-envjson-the-environment-file)); absent only in an instance made before `kit-v0.6.9` | `bin/new-workspace`, always (`locked_dir`, plus an `--env` file's fields, and `--lean`/`--sage` as modules when that file names modules); the user, by hand. The hook refuses the orchestrator any write, and any command naming it but a plain read or a plain git add, commit, status, `diff --numstat` or `diff --stat` | `bin/_env.py`, for the hook, the launchers, `bin/new-run`, `bin/check-env`, `bin/verify-data`, the model-family check, and `bin/_lib.py` (the locked directory, for every tool) |
| `.kit-routes` | the routes the instance enables, one per line ([routes](configuration.md#routes)) | `bin/new-workspace --routes`; protected by the hook as `kit-env.json` is | user, orchestrator. No tool reads it |
| `.kit-lean` | the formal-library toolchain path (only with `--lean`) | `bin/new-workspace --lean` (`--lean-toolchain`, default `~/.elan`); protected by the hook as `kit-env.json` is | `bin/_env.py`, which makes it the `lean` module when `kit-env.json` has no `modules` key; `bin/_lib.py`, for `bin/verify-data`'s library findings. From the file, never the environment |
| `lean` | symlink to the linked formal library (only with `--lean`; never a copy) | `bin/new-workspace --lean` | every worker, read-only, as `$KIT_LEAN`, through the `lean` module ([older instances](configuration.md#older-instances-kit-lean-and-kit-sage)); `bin/check` |
| `lean.SHA256SUMS` | the library's master list: `<sha256>  <path relative to lean/>` per `.lean` file | [bin/verify-data](tools/verify-data.md) `--write-lean-manifest` (run by `bin/new-workspace --lean`, then only deliberately) | `bin/verify-data` (→ **The Lean library has a master list**) |
| `.kit-sage` | the SageMath environment path (only with `--sage`) | `bin/new-workspace --sage`; protected by the hook as `kit-env.json` is | `bin/_env.py`, which makes it the `sage` module, mounted read-only for every worker, when `kit-env.json` has no `modules` key; `bin/_lib.py`, for a `bin/verify-data` finding |
| `.verify-data-skip` | path prefixes `HANDOFF.md` may name that do not exist in the tree, one per line (3+ characters, no spaces, `#` comments) | the user, by hand; optional | `bin/verify-data` check 5 |
| `.env.brave`, `.env.exa` | search-gateway keys (a bare key or `NAME=key`); gitignored | the user; optional | the search gateway in `bin/_ext.py` only, outside every sandbox |
| `.gitignore` | ignores `.claude/state/`, `transcripts/`, `.env.*`, `.claude/settings.local.json`, `.ledger-outbox`, `workspace-*/runs/*/downloads/`, `lean/.lake/`, `__pycache__/`, `*.pyc` | copied | git |
| `.ignore` | names `LEDGER.log`, `data/locked/` and `.claude/state/approvals/`, so ripgrep (and with it Claude Code's Grep tool) skips them in a search from the root; `grep -r`, `find` and `rg --no-ignore` do not read it (→ **The orchestrator reads neither the locked data nor the approval records**) | copied | ripgrep, fd |
| `bin/` | the tools ([tools](tools/README.md)) | copied | everyone but workers; open material |
| `harness/` | `notes/` (harness notes, [configuration](configuration.md#harness-notes)), `bin/brave`, `bin/exa`, `bin/exa-contents` (search helpers), `egress-fwd` (the forwarder from a port inside a sandbox to a unix socket: the Codex egress proxy's, and the licence relays' on both routes) | copied | `bin/new-run --harness` copies a note into a run; the sandbox mounts the search helpers (networked runs) and `egress-fwd` (Codex without network; licence runs) at `/opt/kit/bin/` |
| `tests/` | the suites; run on `/usr/bin/python3` | copied | user, methods sessions |
| `templates/` | forms ([templates/README.md](../../templates/README.md)) | copied | orchestrator |
| `.git/` | the instance's repository; `bin/new-workspace` makes one commit unless `--no-commit` | git | user, orchestrator |

`bin/new-workspace` copies only what the rows above say it copies; in particular not `docs/`, `scripts/`, `history/`,
`KIT-CHANGELOG.md`, `README.md`, `LICENSE`, `CONTRIBUTING.md` or `SECURITY.md` (an instance's `HANDOFF.md` comes from
the template).

## `.claude/`

| path | what it is | written by | read by |
|---|---|---|---|
| `.claude/settings.json` | project settings: the sandbox hook on PreToolUse, PostToolUse, SubagentStart and SubagentStop, the transcript mirror on Stop, SubagentStop, SessionEnd and PreCompact, the denials, the `CLAUDE.md` exclusions ([fields](configuration.md#claudesettingstemplatejson)) | `bin/new-workspace`, filled from the template; never committed live in the kit (→ **A scaffold ships its settings as a template, never live**) | Claude Code at session start; `bin/run-external`'s preflight checks it registers the hook |
| `.claude/worker-net.settings.json` | the settings a networked Claude worker loads instead ([fields](configuration.md#claudeworker-netsettingstemplatejson)) | `bin/new-workspace`, filled from the template | Claude Code, for `--via anthropic\|openrouter --network` only |
| `.claude/settings.template.json`, `.claude/worker-net.settings.template.json` | the templates, with `@ROOT@` and `@HOME@` | copied | `bin/new-workspace` |
| `.claude/settings.local.json` | per-user permission rules; gitignored | Claude Code ("don't ask again") | Claude Code. The hook refuses the tap route while any allow rule there would pass `bin/approve` |
| `.claude/no-mcp.json` | `{"mcpServers": {}}`, the empty MCP config of every headless launch | copied | `bin/run-external`, `bin/astra-session` |
| `.claude/hooks/sandbox.py` | the hook: worker sandbox, approval gate, ledger ([what it refuses](hook-refusals.md)) | copied; changed only as a tested candidate (→ **Change the hook only as a tested candidate**) | Claude Code (every tool call); `bin/check` and `bin/check-env` use its `bwrap_command`, `bin/_ext.py` its `run_limits` |
| `.claude/hooks/mirror-transcripts.sh` | copies this project's Claude Code transcripts into `transcripts/claude-projects/`; additive | copied | Claude Code on `Stop`, `SubagentStop`, `SessionEnd`, `PreCompact` |
| `.claude/agents/kit-worker.md` | the worker agent type `kit-worker`: tools Read, Write, Bash; the worker's standing rules | copied | `claude -p --agent kit-worker` on the no-network Claude routes |
| `.claude/sandbox/ledger` | the ledger shim, mounted at `/opt/kit/bin/ledger`: appends to `$KIT_RUN/.ledger-outbox` | copied | workers |
| `.claude/sandbox/kit-shell` | mounted at `/opt/kit/bin/bash` in a Codex sandbox: each command in a nested sandbox (→ **A Codex worker's commands run apart from Codex**), with the licence forwarders `KIT_LICENCE_FWD` names | copied | Codex workers |
| `.claude/sandbox/sage` | mounted at `/opt/kit/bin/sage` by the `sage` module, when `.kit-sage` names an environment with `bin/sage` and `kit-env.json` has no `modules` key, or when `kit-env.json`'s own `sage` module binds it (as `bin/new-workspace --sage --env FILE` writes it) | copied | workers |
| `.claude/state/` | host-side state, gitignored; [below](#claudestate) | the hook and the tools | see below |

### `.claude/state/`

| path | what it is | written by | read by |
|---|---|---|---|
| `approvals/<kind>-<key>.json` | one unused approval: schema (`kit/approval/1`), kind, key, ids, argv, manifest, digest, created, created_utc, expires, nonce | [bin/approve](tools/approve.md) only | the gated tools. The hook refuses the orchestrator any Read, Grep or Glob there (and a Grep or Glob rooted above one without a safe filter), any write, and any Bash command naming `state/approvals` |
| `approvals/used/<kind>-<key>.<utc>.<nonce>.json` | a consumed approval, renamed on use | the consuming tool (atomic rename) | `bin/_approval.py` (to say when the last one was used); `bin/validate-claims` (a launched brief's approved bytes) |
| `approvals/queue/<nonce>.json`, `<nonce>.<run>.token[.taken]` | a queue record (`kit/queue/1`) and one token per queued run | `bin/run-external --queue` through `bin/_approval.py` | `bin/run-external` when it releases each run |
| `bind/agent_<id>` | the run directory a worker is bound to | the hook, at the worker's first file call or start | the hook |
| `ext/<RUN>/logs/` | `launch.log`, `launch.err`, `debug.log`, `launch.jsonl` while the run is live, out of the worker's reach | `bin/run-external`, `bin/_ext.py` | [bin/watch-run](tools/watch-run.md); moved into the run at exit |
| `ext/<RUN>/` | `detached.out`, `detached.exit` (a `--detach` launch), `gateway.url`, `gateway.log`, `egress.log`, `prompt.md`, `codex-exit.json`, `model-catalog.json`, `passwd`, `group`, `probe-home/` (Codex); `licence.log` (a licence run without the network), `licence.socks` (the same, Claude route: the relays' `PORT=SOCKET` list), `hosts` (the same, Codex route: its `/etc/hosts`) | `bin/run-external`, `bin/_ext.py` | the user; the logs are copied into the run (`licence.log` by `bin/run-external` on the Claude route, by `bin/_ext.py record` on Codex) |
| `licence/<RUN>.hosts` | the `/etc/hosts` of a licence-granted Claude worker: each licence host at 127.0.0.1 | the hook, before each command | the worker's sandbox, read-only |
| `ext/queue-<nonce>.out` | a detached queue's output | `bin/run-external --queue --detach` | the user |
| `packet-index.json` | the cached index of blocked text | `bin/_packet.py` via [bin/lint-brief](tools/lint-brief.md) | `bin/lint-brief` without `--packet`. The launch path never reads it |
| `handoff-archived-<session>` | marks a session whose handoff was archived | the hook | the hook |
| `hook-debug.jsonl`, `debug-on` | the hook's debug log, and the file that switches it on (or `KIT_HOOK_DEBUG`) | the hook; the user | the user |

## `data/`

| path | what it is | written by | read by |
|---|---|---|---|
| `data/locked/` (outside the tree since `kit-v0.6.9`: `kit-env.json`'s `locked_dir`, default `~/.local/state/crosslemma/<instance>/locked/`) | answer keys and control label maps ([RULES.md §7](../../RULES.md#7-standing-rules-that-keep-cycles-convergent) "Controls are blinded and locked"); an instance without `locked_dir` keeps `<root>/data/locked` | `bin/new-workspace` makes it (mode 0700; refused if it already exists, empty or not: the default is keyed by the instance's name only); its contents the user's | an evaluator run only, as `input/` (`bin/new-run --role evaluator`). The orchestrator never reads it ([RULES.md §4](../../RULES.md#4-roles--three-plus-ad-hoc)); the hook refuses its Read, Grep, Glob and commands naming it but `bin/new-run --role evaluator` and a plain git add, commit, status, `diff --numstat` or `diff --stat` ([RULES.md §9](../../RULES.md#9-the-sandbox--enforced-not-convention)); `bin/verify-data` hashes it and never reads it as text |
| `data/locked/SHA256SUMS` | the locked files' hashes, `sha256sum` format | the user | `bin/verify-data` check 1 |
| `data/packet-rules.json` | what no packet may carry ([fields](configuration.md#datapacket-rulesjson)) | `bin/new-workspace` (defaults); [bin/packet-block](tools/packet-block.md), the user's, with `!` | `bin/_packet.py`, `bin/claims-extract`. The hook refuses the orchestrator's edits and any command naming it but a plain git add, commit, status, `diff --numstat` or `diff --stat` |
| `data/packet-exceptions.json` | files excepted from the packet rule, by sha256 ([fields](configuration.md#datapacket-exceptionsjson)) | created by the first [bin/packet-except](tools/packet-except.md), the user's | `bin/_packet.py`; `bin/new-run` (`--input-approved` needs the file's bytes on it). Same hook protection |
| `data/referee-bindings/<run>.json` | a referee run's binding: `{schema, referee_run, question, source_run, claim, artifact_sha256, deps_sha256, claim_sha256}`, the bytes it was given and the claim as the solver wrote it | `bin/new-run --role referee` | the earned tag (`bin/merge`, `bin/close-run`, `bin/ledger-claims`); a ledger approval binds it. A `referee.json` in a run with no binding never counts. The hook refuses the orchestrator any write to it; reading and a plain git add, commit, status or `diff --stat` are allowed |
| `data/cross-family-rulings.json` | `{"<run>": "<family> <where the ruling is recorded>"}`: the user's ruling, naming the referee family whose hold counts for that producer run ([RULES.md §7](../../RULES.md#7-standing-rules-that-keep-cycles-convergent)) | the user | the earned tag; a ledger approval binds it. Same hook protection as the bindings |

## `problems/`, `intake/`, `handoffs/`, `transcripts/`

| path | what it is | written by | read by |
|---|---|---|---|
| `problems/<slug>/PROBLEM.md` | the problem statement, from [templates/PROBLEM.md](../../templates/PROBLEM.md) | `bin/new-workspace` (template); the user | copied into every solver and referee run as `input/PROBLEM.md` |
| `problems/<slug>/prior-art.md` | the register of sources opened | `bin/new-workspace` (template); the orchestrator | orchestrator; open material |
| `problems/<slug>/attacks/<name>/README.md` | one attack, from [templates/attacks/README.md](../../templates/attacks/README.md) | the orchestrator | orchestrator; open material |
| `problems/<slug>/sources/`, `sources/SHA256SUMS` | held primary texts, hashed before they are read ([RULES.md §8](../../RULES.md#8-the-record)) | the orchestrator | open material; a `reviews/` directory under `problems/` is not |
| `intake/IN-NNN-slug/` | one outside input: `record.md` (from [templates/intake-record.md](../../templates/intake-record.md)), `verbatim/`, `SHA256SUMS` ([RULES.md, Outside input](../../RULES.md#outside-input)) | the orchestrator, on receipt; not made by `bin/new-workspace` | the operator (the user, or the operator agent) and orchestrators only; blocked from every packet by default; `bin/verify-data` check 6 |
| `handoffs/<date>-<HHMM>-<sha\|uncommitted>-<session>.md` | every archived `HANDOFF.md`; never overwritten | [bin/handoff-archive](tools/handoff-archive.md) (the hook, and `bin/new-workspace` for the first) | user, orchestrator; blocked from every packet by default |
| `transcripts/claude-projects/` | a mirror of the project's Claude Code session transcripts, with the mirror's `.rsync-errors`; gitignored | `.claude/hooks/mirror-transcripts.sh` | the user |

<a id="run-directory"></a>

## Run directory: `workspace-N/runs/NNN-slug/`

One directory per run. `NNN` is one more than the highest run number in any `workspace-*`; [bin/new-run](tools/new-run.md)
assigns it and refuses a slug that starts with digits and a hyphen. One problem is one workspace
([RULES.md §8](../../RULES.md#8-the-record)). A run directory is launched once (→ **A run directory is launched once**).

**Worker reach.** Read and Write: realpath inside the bound run directory only. Bash and Codex: the run directory
read-write; `/usr`, every always-mounted module of `kit-env.json` (where it has no `modules` key, the library,
`$KIT_LEAN`, and the SageMath module from `.kit-lean` / `.kit-sage`) and the `worker_path` directories read-only, a
licence module only when the launch granted it; tmpfs `/etc` and `/tmp`; `/opt/kit/bin` (the ledger shim; `sage` with the
sage module; `bash`, which is `kit-shell`, on Codex; search helpers on networked runs; `egress-fwd` where a forwarder
runs); on Codex also the CLI at `/opt/codex`; no network unless the launch had `--network`, except, for a licence module, its servers through the
relay ([the sandbox](../concepts/sandbox.md#modules-and-licence-servers)).

**Launch manifest.** A launch approval binds every regular file under the run directory except, at its top level,
`.ledger-outbox`, `usage.json`, `time.log`, `licence.log`, `launch*.log`, `launch*.err`, `debug*.log`, `launch*.jsonl`,
`launch*.last.md`, `gateway*.log`, `egress*.log` and `RECORD-EXT.md`; a symlink, a hard link or any other non-regular
file refuses the manifest (`bin/_approval.py`, `launch_manifest`), and any of the left-out names but an empty
`.ledger-outbox` marks the run as launched before. `.modules` is bound like any other file.

### Made by `bin/new-run`

| path | what it is | for | seen by the worker |
|---|---|---|---|
| `BRIEF.md` | the brief: the role's skeleton with `⟨slots⟩` the orchestrator fills ([RULES.md, The brief](../../RULES.md#the-brief)); a "Modules in your sandbox" section with each module's `brief` line, when any applies | every role | yes |
| `.role` | `solver`, `referee`, `evaluator` or `other` | every role | yes (in the run directory) |
| `.limits` | `{"cpu_hours", "threads", "mem_gb"}` ([fields](configuration.md#a-runs-limits)) | every role | yes |
| `HARNESS-NOTE.md` | a copy of `harness/notes/<kind>.md` (`--harness`) | a Codex or networked run | yes |
| `.modules` | the run's licence modules, one per line (`--module NAME`); `bin/run-external --module` must match it ([configuration](configuration.md#runmodules)) | a run with a licence module | yes |
| `input/PROBLEM.md` | the problem statement | solver, referee (and any role given `--problem`) | yes |
| `input/validate-claims.py` | [bin/validate-claims](tools/validate-claims.md), to run last | solver | yes |
| `input/<file>` | each `--input` (and `--input-approved`) file, under its basename; never a record file name | as given | yes |
| `input/claim.json` | the one claim, with `source_run` added and paths rewritten to `input/artifact/` | referee | yes |
| `input/artifact/…` | the claim's artifact and its declared `deps` | referee | yes |
| `input/ledger-premises.md` | `bin/claims-extract --ids` of the claim's `ledger` premises | referee of a claim with `ledger` premises | yes |
| `input/`, `scratch/`, `output/` | `input/` holds the rows above; the others empty | every role | yes |

### Written by the orchestrator, by hand

| path | what it is |
|---|---|
| `.source-run` | the run a restatement was assembled from; decides its model family ([SCHEMAS.md §4](../../SCHEMAS.md#4-earned-tag--binmerge-computes-binledger-claims-enforces)) |
| `PROVENANCE.md` | the record of a run with no worker, or of an outside run ([templates/runs/PROVENANCE.md](../../templates/runs/PROVENANCE.md)) |

### Written by the worker

| path | what it is |
|---|---|
| `output/result.md` | the solver's report, at most 150 lines |
| `output/claims.json` | the solver's claims ([SCHEMAS.md §1](../../SCHEMAS.md#1-outputclaimsjson--written-by-the-solver)) |
| `output/…` | artifacts, deps, proofs, evidence |
| `output/referee.json` | a referee's verdict, six fields ([SCHEMAS.md §3](../../SCHEMAS.md#3-outputrefereejson--written-by-a-referee-run-exactly-these-six-fields)) |
| `output/search-log.md`, `downloads/` | a networked run's queries and downloads; `downloads/` is gitignored and hashed in `RECORD-EXT.md` |
| `scratch/` | the worker's working space |
| `.ledger-outbox` | queued `ledger "…"` entries; the hook (Claude) or `bin/_ext.py record` (Codex) moves them into `LEDGER.log` |

### Left by a launch ([bin/run-external](tools/run-external.md), [bin/limits-exec](tools/limits-exec.md))

| path | route | what it is |
|---|---|---|
| `launch.log`, `launch.err` | Claude | the stream-json transcript and stderr, moved in after the worker stopped |
| `launch.<utc>.log`, `launch.<utc>.err`, … | Claude | an earlier attempt's logs, kept when the launcher retried after an upstream rate limit |
| `debug.log` | Claude | Claude Code's API debug log, with `RUN_EXTERNAL_DEBUG=1` |
| `launch.rollouts/` | Codex | session files copied from inside the sandbox, sorted into `launch.rollout*.jsonl` and removed |
| `launch.jsonl`, `launch.err` | Codex | the event transcript, copied through a pipe with a hash chain |
| `launch.last.md` | Codex | Codex's last message, written from inside the sandbox |
| `launch.rollout.jsonl`, `launch.rollout.sub-N.jsonl` | Codex | the main thread's session file; any other (a sub-agent's) |
| `RECORD-EXT.md` | Codex, or `--network` | the external run record: route, effort and models seen, exit, caps, disclosure, hashes of logs and downloads |
| `gateway.log`, `egress.log` | networked; Codex without network | the search gateway's and the egress proxy's request logs |
| `licence.log` | a licence module, without `--network` | every connection the licence relays carried: `OPEN`, `CLOSE` with bytes each way and seconds, `UNREACHABLE`; never contents |
| `usage.json` | every route | CPU, wall, memory and caps of the run's process tree; `cpu_cap_hit`, `over_cpu_cap` |
| `time.log` | every route | `/usr/bin/time -v` of the launch; holds the exact command, so `--model` is read from it |

The launch's working files stay in a temporary directory of `bin/limits-exec`'s, never in the run; `usage.json`, `time.log`,
the copied logs and `RECORD-EXT.md` are each written to a fresh name and renamed over the run's, so a link the worker left
at the name is replaced, never followed.

### Written by the checker and the verdict

| path | what it is | written by |
|---|---|---|
| `check.json` | per-claim check results ([SCHEMAS.md §2](../../SCHEMAS.md#2-checkjson--written-by-bincheck-a-script-rulesmd-step-2)) | [bin/check](tools/check.md) |
| `check/` | `<id>.stdout`, `<id>.stderr`, `<id>.lean.log`, `<id>.audit.log`, `<id>.build/` (the artifact as compiled), `<id>.audit-<nonce>/` (the compiled file and the kit's audit program), `<id>.mut.<name>.log` | `bin/check` |
| `check.<generated>.json` | a kept check record of a run with ledgered claims; never overwritten | `bin/check` (→ **A ledgered run's check record is kept**) |
| `verdict.md` | the verdict table, model families, notes, premises, formal statements | [bin/merge](tools/merge.md) |

## Outside the instance

| path | what it is | written by | read by |
|---|---|---|---|
| `~/.claude/projects/<project>/` | Claude Code's session transcripts | Claude Code | the mirror hook; `bin/_ext.py` reads a Claude worker's transcript there for `effort_seen` |
| `$XDG_RUNTIME_DIR/kit-egress/` or `/tmp/kit-egress-<uid>/` | a directory of mode 0700, private to the user's Unix account, holding the egress socket of a no-network Codex run, `<NNN>-<hash>.sock`, and the licence relays' sockets of a licence run without the network, `<NNN>-<hash>-lic<i>.sock`, mode 0600, on both routes (→ **The egress socket's host side is in a short private directory**) | `bin/_ext.py` | the egress proxy and the relays; only the socket files are bound into the sandbox |
| `~/.local/state/crosslemma/<instance>/locked/` | the locked directory (`kit-env.json`'s `locked_dir`): answer keys and label maps, outside every workspace | `bin/new-workspace` makes it; the user fills it | an evaluator run only; `bin/verify-data` hashes it |
| `~/.codex/auth.json` | the user's Codex login; a copy lives in the sandbox's private tmpfs for the run | the user | `bin/_ext.py` |
| `~/.config/openrouter/key` (or `$OPENROUTER_KEYFILE`) | the OpenRouter key | the user | `bin/run-external --via openrouter`, `bin/astra-session` |
| user units `kit-run-<RUN>`, `kit-queue-<nonce>` | a detached launch or queue | `bin/run-external --detach` | `systemctl --user` |
