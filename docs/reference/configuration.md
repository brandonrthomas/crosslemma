# Configuration

Every configuration file an instance has, each field, its default, and the code that reads it.

Where each file lives is in [Layout](layout.md). Names shared by the tools, the hook and the suites (environment
variables, the worker agent type, unit names) are fixed in [SCHEMAS.md §7](../../SCHEMAS.md#7-fixed-names).

## `kit-env.json`, the environment file

What this machine offers an instance's workers beyond the system: extra programs (*modules*), extra directories on every
worker's `PATH`, the two CLIs, and extra model families. One JSON object at the instance's root, read by
[bin/_env.py](tools/_env.py.md) for the hook, the Codex route, [bin/run-external](tools/run-external.md),
[bin/new-run](tools/new-run.md), [bin/check-env](tools/check-env.md), [bin/verify-data](tools/verify-data.md) and the
model-family check. Its fields are listed in
[SCHEMAS.md §8](../../SCHEMAS.md#8-kit-envjson--the-instances-environment-file-the-users); the docstring of
`bin/_env.py` is the full reference ([RULES.md §9](../../RULES.md#9-the-sandbox--enforced-not-convention),
→ **A worker's tools come from the user's environment file**). Every field is optional, and an instance may have no
file at all. `~` (the user's home) and `<root>` (the instance) are expanded in `worker_path`, `locked_dir` and every
module's paths and values; `codex_bin_dir` expands `~` only; `claude` and `codex` are used as written (a name on `PATH`
or an absolute path).

**It is the user's.** The hook refuses the orchestrator any Write or Edit of it, and any Bash command naming it other
than one plain read (`cat`, `head`, `tail`, `less`, `jq`, `grep`, `wc`, `sha256sum`, `ls`, `stat`, `diff`, `file`, with no
pipe, redirection or substitution) or a plain `git add`, `git commit`, `git status` or `git diff` (with no option
that writes a file or runs a program); the Read tool may read it. The same holds for `.kit-lean`, `.kit-sage` and
`.kit-routes` (→ **The environment files are the user's**). You edit the file by hand, give it to a new instance with `bin/new-workspace --env FILE`, and run
`bin/check-env` after every change.

### The fields

- **`worker_path`**: directories mounted read-only at their own path for every worker, and put on its `PATH` after the
  modules' entries and before `/usr/bin:/bin`. A directory that does not exist is skipped with a problem line.
- **`claude`**: the Claude Code CLI, by name on `PATH` or as an absolute path; default `claude`. `bin/run-external` starts
  every Claude-route worker with it.
- **`codex`**, **`codex_bin_dir`**: the Codex route mounts Codex's real binary, not the `codex` command. The binary's
  directory is, in order: `KIT_CODEX_BIN_DIR` from the environment (a test override); `codex_bin_dir`; else found from
  the `codex` command (default `codex` on `PATH`): its own directory when it is a native binary, otherwise, for the npm
  package's script, `node_modules/@openai/codex-*/vendor/*/bin/` or `vendor/*/bin/` inside the package. When none is
  found, a Codex launch is refused.
- **`locked_dir`**: the locked directory (answer keys, label maps), outside the instance so that no search from it walks
  there. `bin/new-workspace` uses the `--env` file's `locked_dir` if it has one, else makes
  `~/.local/state/crosslemma/<instance>/locked/` (created with mode 0700), and records it here; it refuses a path that
  exists and is not an empty directory. Without the field an instance keeps `<root>/data/locked`; `bin/verify-data`
  reports keys left there after a move. Refused by the loader (`<root>/data/locked` is then used): a relative path, the
  root, a home directory, `/home` or a directory holding a home, a credential directory, the instance or anything inside
  or holding it.
- **`model_families`**: `{"Family": ["word", …]}`, added after the built-in Anthropic and OpenAI words. A model's family
  is the first family, built-in ones first, one of whose words is a whole part of the model's name (split at every
  character that is not a letter or digit), or begins a part and is followed there by a digit (`gpt5`, `opus4`); never
  any other prefix (`kit-v0.6.22`). The family decides the cross-family referee rule
  ([RULES.md §7](../../RULES.md#7-standing-rules-that-keep-cycles-convergent)): the read counts from any known family
  other than the producer's, an added one included (`bin/_lib.py`, `cross_family_need`; since `kit-v0.6.7`). An added
  family is not covered by §7's exception for reads before their ladders, which names the two built-in families: its
  models referee only after their own ladder ("Calibrate before trusting", kept by the session; the code does not check
  calibration).
- **`modules`**: below.
- There is no `python` field (removed in `kit-v0.5.0`; `bin/_env.py` ignores the key). Every tool, the hook and the
  sandboxes use `/usr/bin/python3` by name.

### Modules

A module is a named set of read-only mounts with its `PATH` and environment additions:

| key | meaning |
|---|---|
| `binds` | paths, each mounted at its own path, or `{"src": …, "dest": …}` to mount it elsewhere |
| `path` | `PATH` entries, ahead of `worker_path` |
| `env` | environment variables; `PATH`, `HOME`, `LD_PRELOAD` and `LD_LIBRARY_PATH` are refused |
| `check` | a command `bin/check-env` runs inside a worker's sandbox with the module mounted |
| `brief` | one line: every brief whose worker has the module names it under "Modules in your sandbox" |
| `licence_servers` | `[{"host": …, "port": …}]`: makes it a *licence module* ([licensed software](../guides/licensed-software.md#a-licence-server-program-a-licence-module)) |

A module without `licence_servers` is mounted for every worker on every route, and for the checker's sandbox. A licence
module is mounted only for a run whose `RUN/.modules` and whose launch (`--module NAME`) both name it. For example, with
placeholder paths:

```json
{
  "worker_path": ["~/opt/tools/bin"],
  "modules": {
    "pari": {
      "binds": ["~/opt/pari"],
      "path": ["~/opt/pari/bin"],
      "env": {"GP_DATA_DIR": "~/opt/pari/share/pari"},
      "check": "gp --version-short",
      "brief": "PARI/GP: run `gp -q`; its data is in $GP_DATA_DIR"
    }
  }
}
```

### What is refused

Whoever wrote the file, `bin/_env.py` refuses, with a problem line:

- a mount source or `PATH` entry that is the root; a home directory, `/home`, or a directory holding a home directory;
  the instance, or a directory inside or holding it (but the instance's library link `lean` and the kit's own shim files
  under `.claude/sandbox/`); or a credential directory or anything in one: `~/.ssh`, `~/.gnupg`, `~/.claude`,
  `~/.codex`, `~/.config`, `~/.aws`, `~/.netrc`, `~/.local/share/keyrings`;
- an environment variable named `PATH`, `HOME`, `LD_PRELOAD` or `LD_LIBRARY_PATH`, or not a valid name;
- a licence server whose host is not a plain name (letters, digits, dots, hyphens) or whose port is not a whole number
  from 1024 to 65535, and two servers of one module on one port.

A module with any of these, or with a mount source that does not exist, is not mounted at all; the other modules are.
A refused `worker_path` entry is left out alone. A file that does not parse as a JSON object mounts no module at all.

The problem lines appear as `FAIL` in `bin/check-env`, as findings of `bin/verify-data` (so `bin/close-run`, which runs it
first, stops too), as a refusal of `bin/new-workspace --env`, and as a refusal of any `bin/run-external --module` launch.
The hook mounts what is left and says nothing.

### Older instances: `.kit-lean` and `.kit-sage`

With no `kit-env.json`, or one without a `modules` key, `bin/_env.py` makes two modules from the files
`bin/new-workspace --lean` and `--sage` write, mounted exactly as before (a golden test shows the worker's sandbox command
unchanged byte for byte):

- `lean`, when `<root>/lean` and the toolchain (`.kit-lean`'s path, default `~/.elan`) are both directories: both
  mounted at their own paths, the toolchain's `bin/` on `PATH`, `ELAN_HOME` and `KIT_LEAN` set.
- `sage`, when `.kit-sage` names a directory holding `bin/sage` and the kit's shim `.claude/sandbox/sage` exists: the
  environment at its own path, the shim at `/opt/kit/bin/sage`, `KIT_SAGE` set.

A `modules` key replaces both: `.kit-lean` and `.kit-sage` are then not mounted, although `bin/verify-data` still reads
them for its library findings. To keep a linked library beside modules of your own, pass `--lean` (and `--sage`) with `--env`:
`bin/new-workspace` adds them to the file's `modules` as `lean` and `sage`, as below. For an existing instance, add the
entry by hand; [bin/check](tools/check.md) finds the library through `KIT_LEAN`:

```json
"lean": {"binds": ["~/.elan", "<root>/lean"], "path": ["~/.elan/bin"],
         "env": {"ELAN_HOME": "~/.elan", "KIT_LEAN": "<root>/lean"}}
```

### `RUN/.modules`

The licence modules a run's worker is to have, one name per line, written by `bin/new-run --module NAME` (repeatable).
`bin/new-run` refuses a name that is not a licence module of `kit-env.json`, and puts each module's `brief` line in the
brief. The file is a regular file in the run directory, so the launch approval binds it with the run's other bytes.
`bin/run-external` refuses, before any approval, a launch whose `--module` set differs from it. A run without the file
takes no `--module`.

### The licence route's environment variables

Set by the launch, never read from a file in the run directory ([SCHEMAS.md §7](../../SCHEMAS.md#7-fixed-names)).
None is set by hand. `bin/check-env` also sets `KIT_WORKER_RUN` and `KIT_WORKER_MODULES` (to every licence module) in its
own environment for its module checks.

| variable | set by | read by | value |
|---|---|---|---|
| `KIT_WORKER_MODULES` | `bin/run-external`, Claude routes, in the worker's process environment | the hook | the granted licence modules, comma-separated; honoured only beside `KIT_WORKER_RUN` |
| `KIT_WORKER_LICENCE_SOCKS` | `bin/run-external`, Claude routes without `--network` | the hook | `PORT=SOCKET,…`: each relay's port and host socket, in the module's order |
| `KIT_LICENCE_FWD` | `bin/_ext.py codex`, inside the Codex sandbox, without `--network` | `.claude/sandbox/kit-shell` | `PORT=/opt/kit/licence/<i>.sock …`, space-separated |

## A run's `.limits`

JSON at `RUN/.limits`, written by [bin/new-run](tools/new-run.md) from `--cpu-hours`, `--threads` and `--mem-gb`. It
is part of the launch manifest, so an approval binds it. Once the approval is used, `bin/run-external` keeps a copy at
`.claude/state/ext/<run>/limits.json`, outside the run, where no worker writes. Read by the hook (`run_limits`) for
every sandboxed command on the Claude routes, from that copy once it exists (the run's own file is the worker's to
rewrite); through the same function by `bin/_ext.py codex`, once, before the worker starts, for the whole Codex
sandbox (`ulimit -t` and the thread variables there, and `KIT_CPU_HOURS` and `KIT_MEM_GB` as on the Claude routes); and
by [bin/limits-exec](tools/limits-exec.md), once at launch, for the worker's whole process tree. The hook's per-command
CPU limit binds each command; its thread variables are defaults a worker can set again inside a command; what binds the
whole run is `bin/limits-exec`'s column, fixed at launch
([RULES.md §9](../../RULES.md#9-the-sandbox--enforced-not-convention), → **Limits are enforced, not promised**).

| field | default | `bin/new-run` flag | the hook does | `bin/limits-exec` does |
|---|---|---|---|---|
| `cpu_hours` | 8 | `--cpu-hours` (8.0) | `ulimit -t` = max(60, cpu_hours × 3600) s per command; `KIT_CPU_HOURS` | the whole-run CPU budget: at that much cgroup CPU time, TERM to the command, KILL to the rest of the scope after `cpu_grace_seconds`; exit 152 (→ **The whole-run CPU budget is enforced**). Clamped to 0.0001–1000 |
| `threads` | 8 | `--threads` (8) | clamped to 1–64; `OMP_NUM_THREADS`, `OPENBLAS_NUM_THREADS`, `MKL_NUM_THREADS`, `NUMEXPR_NUM_THREADS`, `KIT_THREADS` | `CPUQuota` = threads × 100 %. Clamped to 1–64 |
| `mem_gb` | 16 | `--mem-gb` (16.0) | `KIT_MEM_GB` (the variable only) | `MemoryMax` = mem_gb × 1024 MiB and `MemorySwapMax=0`. Clamped to 0.5–512 |
| `cpu_grace_seconds` | 30 | none; no tool writes it | not read | seconds between the TERM and the KILL at the CPU budget. Clamped to 1–600 |

- `bin/new-run` refuses a non-positive `--cpu-hours`, `--threads` or `--mem-gb`.
- The hook falls back to the default for a field that is missing or not a positive number, and for an unreadable file.
  `bin/limits-exec` falls back to the default for a field it cannot parse, then clamps.
- Without a working `systemd-run --user --scope`, no worker runs: `bin/run-external` refuses every launch before any
  approval (`bin/limits-exec --probe`), and `bin/limits-exec` itself exits 2 without running the command. `bin/check-env`
  reports it as `FAIL`.

## `data/packet-rules.json`

What no worker's packet may carry ([RULES.md §8](../../RULES.md#8-the-record), → **No packet carries blocked
material**). The user's: added to with `! bin/packet-block …` ([bin/packet-block](tools/packet-block.md)); an
entry is removed by editing the file by hand. The hook refuses the orchestrator's edits and any command naming it
other than a plain `git add`, `git commit`, `git status` or `git diff`
([RULES.md §9](../../RULES.md#9-the-sandbox--enforced-not-convention)). Read by `bin/_packet.py` (the packet scan, run by
[bin/lint-brief](tools/lint-brief.md) and, before any approval, by [bin/run-external](tools/run-external.md)) and by
[bin/claims-extract](tools/claims-extract.md) (`extract`).

| key | form | meaning |
|---|---|---|
| `blocked` | list of `{"path", "why", "added_utc"}` | `path`, root-relative, a file or directory, is out of every packet whole. A blocked run directory is blocked except its `input/`, `downloads/` and `.lake/`; its launch transcripts are indexed less what they quote from their own `input/` and `BRIEF.md`. `path` is required; `why` is reported with a finding |
| `lines` | list of `{"path", "match", "why", "added_utc"}` | only the lines of `path` (a file or a run directory) matching the regular expression `match`, case-insensitive, are blocked (in a run directory: not its `input/`, `downloads/`, `.lake/` or launch transcripts); the file's other lines are not |
| `verdicts` | `true`, a regular expression string, or absent | `true`: the kit's route-verdict pattern (`VERDICT_RE`: "ranking #7", PARK, PURSUE, DEAD, "most promising", …); a string: that pattern instead; absent, `false` or empty: off. A match on any line of any packet file is an error |
| `extract` | `{"entries": [{"id", "why", "added_utc"}], "notes": [{"id", "date", "why", "added_utc"}]}` | entries, and notes of one date, that `bin/claims-extract` leaves out of every worker's extract (`bin/packet-block --extract C-NNN`, `--extract-note C-NNN DATE`) |

Default, written by [bin/new-workspace](tools/new-workspace.md):

```json
{
 "blocked": [
  {"path": "DIRECTION.md", "why": "the direction brief's ranking of mechanisms (a default)"},
  {"path": "HANDOFF.md", "why": "the orchestrator's pointer sheet (a default)"},
  {"path": "handoffs", "why": "archived pointer sheets (a default)"},
  {"path": "intake", "why": "outside input: operator and orchestrators only (a default)"}
 ],
 "lines": [],
 "verdicts": true
}
```

- No file: nothing is blocked and the verdict check is off.
- A file that does not parse, or an entry without `path` (or `match` in `lines`), fails the scan:
  `bin/lint-brief --packet` exits 4 and `bin/run-external` refuses.
- Open material, which can excuse a shared 12-word run of text: `problems/`, `lean/`, `CLAIMS.md`,
  `SCHEMAS.md`, `RULES.md`, `FLOW.md`, `LESSONS.md`, `templates/`, `bin/`, `tests/`, `.claude/hooks/`,
  `.claude/sandbox/`, `harness/`, and the `output/` of every earlier run that is neither blocked nor under a line rule
  and was launched or checked; less any `reviews/`, `.lake/` or `downloads/` directory under the former, and any
  `scratch/`, `downloads/` or `.lake/` under a run's `output/`. A blocked path inside open material is not open
  (`bin/_packet.py`, `open_files`).

## `data/packet-exceptions.json`

The user's file-by-file exceptions to the packet rule, made by `! bin/packet-except FILE "ruling"`
([bin/packet-except](tools/packet-except.md)); absent until the first one. Same hook protection as the rules file.
Read by `bin/_packet.py`, for the packet scan and for `bin/new-run --input-approved`, which takes another run's file only
while its bytes are on this list.

| field | meaning |
|---|---|
| `sha256` | the excepted bytes |
| `path` | the file, root-relative |
| `ruling` | the user's words |
| `added_utc` | when it was added |

The file is a JSON list of these objects. An exception is live only while the file at `path` still has the bytes
`sha256` names; an edit ends it. An excepted file may go into a packet; it is neither blocked nor open material for
any other packet. A list that is not a list of objects with `sha256` and `path` fails the scan.

## `KIT-VERSION`

Written once by [bin/new-workspace](tools/new-workspace.md), one `key: value` per line. No tool reads it; it names
the commit a methods session diffs against when it upgrades the instance. `bin/new-workspace` refuses to make an
instance while the kit has uncommitted changes in anything it copies (`KIT_DIRTY_PATHS`: its directories and files,
`.gitignore` and `.ignore` included).

| key | value |
|---|---|
| `kit-commit` | the kit's `HEAD`, 12-character short sha |
| `kit-tag` | the tag on that commit, or `-` |
| `kit-path` | the kit's absolute path |
| `made` | local time, `%Y-%m-%dT%H:%M:%S%z` |
| `problem` | the `--problem` slug |
| `routes` | the enabled routes, comma-separated |
| `lean` | the linked library's real path, or `-` |
| `sage` | the SageMath environment's real path, or `-` |
| `env` | `kit-env.json from <the --env file's real path>`, or `-` |

The last line is a comment: an instance is upgraded only by a methods session with a diff against this commit.

## Other instance files

| file | form | written by | read by |
|---|---|---|---|
| `.kit-routes` | a `#` comment, then one route per line | `bin/new-workspace --routes` | no tool; it is what "a canary on every enabled route" means. The hook protects it as it does `kit-env.json` |
| `.kit-lean` | one line: the library toolchain's path | `bin/new-workspace --lean`, from `--lean-toolchain PATH` (default `~/.elan`) | `bin/_env.py`, for the `lean` module, only without a `modules` key in `kit-env.json` ([above](#older-instances-kit-lean-and-kit-sage)); `bin/_lib.py` for `bin/verify-data`'s library findings (absent: `~/.elan`; its presence makes a missing `lean/` a finding). The hook protects it as it does `kit-env.json` |
| `.kit-sage` | one line: a SageMath conda environment with `bin/sage` | `bin/new-workspace --sage PATH` | `bin/_env.py`, for the `sage` module, as `.kit-lean`; `bin/_lib.py`: a path without `bin/sage` is a `bin/verify-data` finding. The hook protects it as it does `kit-env.json` |
| `lean.SHA256SUMS` | `<sha256>  <path relative to lean/>` per `.lean` file, sorted | `bin/verify-data --write-lean-manifest` | `bin/verify-data` |
| `<locked directory>/SHA256SUMS` | `sha256sum` output for every file under the locked directory (`locked_dir`) | the user | `bin/verify-data` |
| `.verify-data-skip` | path prefixes, one per line, at least 3 characters, no whitespace; `#` comments | the user | `bin/verify-data`, for paths `HANDOFF.md` names that are not in the tree |
| `.env.brave`, `.env.exa` | a bare key, or `NAME=key` (an `export ` prefix and quotes allowed; `#` comments skipped) | the user | the search gateway (`bin/_ext.py`, `start_gateway`); a missing key is reported, never fatal |
| `.claude/no-mcp.json` | `{"mcpServers": {}}` | copied | every Claude-route launch of `bin/run-external`, and `bin/astra-session -p`, with `--strict-mcp-config` |

## `.claude/settings.template.json`

The project settings, shipped as a template and filled by `bin/new-workspace` into `.claude/settings.json`
([RULES.md §9](../../RULES.md#9-the-sandbox--enforced-not-convention), → **A scaffold ships its settings as a template,
never live**). Placeholders: `@ROOT@` (the instance's real path) and `@HOME@` (the user's home); `bin/new-workspace`
asserts neither is left. Settings bind at session start (→ **Settings bind at session start**).

| field | value | why |
|---|---|---|
| `permissions.deny` | `WebFetch`, `WebSearch`, `Bash(curl:*)`, `Bash(wget:*)`, and four MCP tool prefixes (`mcp__claude_ai_Gmail`, `mcp__claude_ai_Google_Calendar`, `mcp__claude_ai_Google_Drive`, `mcp__qmd`) | no web or connector tools in the project |
| `deniedMcpServers` | `{"serverName": "qmd"}`, `{"serverUrl": "https://*"}`, `{"serverUrl": "http://*"}` | → **MCP servers denied project-wide** |
| `hooks.PreToolUse`, `PostToolUse`, `SubagentStart`, `SubagentStop` | `/usr/bin/python3 @ROOT@/.claude/hooks/sandbox.py`, timeout 20 s | the sandbox, the gate and the ledger on every call |
| `hooks.PreToolUse` (a second entry) | a load check: Python loads `sandbox.py` as a module, and the command exits 2 when it cannot | a hook broken by an edit refuses every call instead of making no decision; the first command stays exactly as it is |
| `hooks.SubagentStop` (second), `Stop`, `SessionEnd`, `PreCompact` | `@ROOT@/.claude/hooks/mirror-transcripts.sh`, timeout 60 s | mirror transcripts into `transcripts/` |
| `claudeMdExcludes` | `@HOME@/CLAUDE.md`, `@HOME@/.claude/CLAUDE.md` | → **`CLAUDE.md` is injected in full into every worker** |
| `includeGitInstructions` | `false` | |
| `env.BASH_DEFAULT_TIMEOUT_MS` | `"600000"` | 10 min default Bash timeout |
| `env.BASH_MAX_TIMEOUT_MS` | `"3600000"` | 60 min maximum |

`bin/run-external` refuses every launch (before any approval) when `.claude/settings.json` is missing or does not name
`@ROOT@/.claude/hooks/sandbox.py`. The hook refuses the tap route while an allow rule in `.claude/settings.json`,
`.claude/settings.local.json` or the user-scope settings would let `bin/approve` through.

## `.claude/worker-net.settings.template.json`

Filled by `bin/new-workspace` into `.claude/worker-net.settings.json`. A networked Claude worker
(`--via anthropic|openrouter --network`) loads it with `--settings … --setting-sources local` in place of the project
settings, whose `deny` list would remove its web tools. `bin/run-external` refuses such a launch when the file is
missing.

| field | value |
|---|---|
| `permissions.deny` | the four MCP tool prefixes above (no web denial) |
| `deniedMcpServers` | the same three entries as the project settings |
| `env` | `BASH_DEFAULT_TIMEOUT_MS` 600000 and `BASH_MAX_TIMEOUT_MS` 3600000, as the project settings: the hour per call a brief promises (a networked worker does not load the project settings) |
| `hooks.PreToolUse`, `hooks.PostToolUse` | the same `sandbox.py` command, timeout 20 s, and the same load check on PreToolUse |
| `claudeMdExcludes` | as above |
| `includeGitInstructions` | `false` |
| `autoMemoryEnabled` | `false` |

## Template tokens

`bin/new-workspace` fills these in `templates/PROBLEM.md`, `prior-art.md`, `DIRECTION.md`, `HANDOFF.md` and the canary
brief: `@ROOT@` (instance path), `@HOME@`, `@NAME@` (the instance directory's name), `@SLUG@` (the problem slug),
`@KIT@` (the kit's path), `@KITBASE@` (its directory name), and for the canary `@RUN@` and `@RUNDIR@`.

## Harness notes

`harness/notes/<kind>.md`, copied into a run as `RUN/HARNESS-NOTE.md` by `bin/new-run --harness <kind>`. The note is
part of the packet, so the approval binds it. Its first line is `<!-- harness: <kind> -->`; `bin/run-external` reads
the kind from that line and refuses the launch, before the approval, unless it is the one the flags need
(→ **Networked and Codex launches need their flags bound in the approval and a matching `HARNESS-NOTE.md`**).

| kind | needed by | delivered as | says |
|---|---|---|---|
| none | `--via anthropic` or `openrouter` without `--network` (a run holding a note is refused) | the `kit-worker` agent file instead | |
| `claude-net` | `--via anthropic` or `openrouter` with `--network` | `--append-system-prompt` | tools Read, Write, Bash, WebSearch, WebFetch; search helpers `brave`, `exa`, `exa-contents`; local SearXNG; scholarly APIs; log every query in `output/search-log.md`, save downloads under `downloads/` |
| `codex` | `--via codex` | the start of the prompt, then a blank line, then the task | a shell, no network, no web search, no other agents |
| `codex-net` | `--via codex --network` | as `codex` | as `codex`, with the network section of `claude-net` |

[bin/lint-brief](tools/lint-brief.md) warns when a `-net` note sits beside a brief that says "no network".
`bin/new-run --role referee` with a `-net` harness adds the network paragraph to the referee brief
(→ **A networked referee's brief carries the network paragraph**).

## Routes

A route is a way to launch a worker: a `--via` value with or without `--network`. An instance enables routes with
`bin/new-workspace --routes`, recorded in `.kit-routes` and `KIT-VERSION`; default `anthropic,codex`, one route of each
model family, because a `[PROVED]` or script claim needs a referee of the other family
([RULES.md §7](../../RULES.md#7-standing-rules-that-keep-cycles-convergent)). `bin/new-workspace` warns when every
enabled route runs one family. The flags below are each route's canary flags as `bin/new-workspace` prints them.

| route | `--via` | network | harness note | family | credential, placed by the user | canary flags |
|---|---|---|---|---|---|---|
| `anthropic` | `anthropic` | none | none | Anthropic | the user's own Claude Code login | `--via anthropic --model opus --effort low --max-turns 40` |
| `openrouter` | `openrouter` | none | none | the `--model`'s | `~/.config/openrouter/key` or `$OPENROUTER_KEYFILE` | `--via openrouter --model <model id> --effort low --max-turns 40` |
| `codex` | `codex` | the egress proxy only | `codex` | OpenAI | a logged-in `~/.codex/auth.json` | `--via codex --model gpt-5.6-sol --effort low` |
| `anthropic-net` | `anthropic` | yes | `claude-net` | Anthropic | as `anthropic` | `--via anthropic --model opus --effort low --max-turns 40 --network` |
| `openrouter-net` | `openrouter` | yes | `claude-net` | the `--model`'s | as `openrouter` | `--via openrouter --model <model id> --effort low --max-turns 40 --network` |
| `codex-net` | `codex` | yes | `codex-net` | OpenAI | as `codex` | `--via codex --model gpt-5.6-sol --effort low --network` |

A model's family is read from its name (`bin/_env.py`, `model_family`, through `bin/_lib.py`): Anthropic for `anthropic`,
`opus`, `fable`, `sonnet`, `haiku`, `claude`; OpenAI for `openai`, `gpt`, `sol`, `astra`, `codex`; then any family
`kit-env.json`'s `model_families` adds ([above](#the-fields)); otherwise unknown. A word counts when it is one of the
name's parts between characters that are not letters or digits, or begins a part and is followed there by a digit
([SCHEMAS.md §4](../../SCHEMAS.md#4-earned-tag--binmerge-computes-binledger-claims-enforces)).

### `bin/run-external` flags

Defaults from [bin/run-external](tools/run-external.md). "Bound" means the flag is part of what the launch approval
binds; options compare as a set, so order does not matter ([RULES.md §6](../../RULES.md#6-approvals--the-gate),
→ **A launch approval binds its flags**). A launch approval must bind `--model`.

| flag | default | bound | meaning |
|---|---|---|---|
| `--model ID` | required | yes | the model; on Claude routes an alias or id, on Codex an exact id |
| `--via` | `openrouter` | yes | `openrouter`, `anthropic` or `codex` |
| `--effort` | `high` | yes | Claude routes: `low medium high xhigh max`; Codex: `minimal low medium high xhigh max`; anything else refused (→ **`bin/run-external` checks `--effort` per route**) |
| `--max-turns N` | `300` | yes | Claude routes: Claude Code's turn cap; Codex: a cap on tool calls counted from the transcript, exit 125. A brief saying "at most N tool calls" with N above it is refused |
| `--wall-hours H` | 4 (Claude routes), 2 (Codex) | yes | one deadline for the whole launch, retries included; exit 124 (→ **A wall-clock cap on every route**) |
| `--network` | off | yes | the web for this worker; needs the matching harness note |
| `--module NAME` | none | yes | a licence module for this worker, repeatable; refused before any approval unless it is a licence module of `kit-env.json` and the set equals `RUN/.modules` ([above](#runmodules)) |
| `--prompt TEXT` | "Start by reading RUN/BRIEF.md …, then follow it exactly. Your run directory is RUN." | yes | the task prompt |
| `--retries N` | `3` | yes | Claude routes: resumes after an upstream rate limit, waiting 30 s, 60 s, 120 s, … |
| `--dry-run` | | no | prints what would run; touches no approval |
| `--detach` | | no | runs the launch as user unit `kit-run-<RUN>` (a queue: `kit-queue-<nonce>`) |
| `--queue RUN…` | | no | runs approved together, one at a time; every approval is used at the start; the queue lives for the sum of the runs' wall caps plus 30 min |
| `--budget` | | | refused: no run has a spending cap (→ **No spending cap on any run**) |

Internal flags, never typed: `--check` (a queue's pre-check), `--queued NONCE`, `--queue-run`.

What each route starts:

| route | process | settings | environment set for the worker |
|---|---|---|---|
| Claude, no network | `claude -p … --agent kit-worker --tools Read,Write,Bash --setting-sources project,local --disable-slash-commands --strict-mcp-config --mcp-config .claude/no-mcp.json --output-format stream-json` | the project's, and `.claude/settings.local.json` if present | `KIT_WORKER_RUN`, `CLAUDE_CODE_DISABLE_AUTO_MEMORY=1`, `CLAUDE_CODE_DISABLE_BUNDLED_SKILLS=1`; with `--module`, `KIT_WORKER_MODULES`, and without `--network` `KIT_WORKER_LICENCE_SOCKS`; every inherited `CLAUDE*` and `ANTHROPIC_*` variable dropped |
| Claude, network | as above with `--tools Read,Write,Bash,WebSearch,WebFetch` and the harness note appended, no `--agent` | `.claude/worker-net.settings.json`, and `.claude/settings.local.json` if present | as above, plus `KIT_WORKER_NET=1`, `KIT_NET_GATEWAY`, `SEARXNG_URL=http://localhost:7764` |
| `--via openrouter` | as the Claude route | as the Claude route | plus `ANTHROPIC_BASE_URL=https://openrouter.ai/api`, the key as `ANTHROPIC_AUTH_TOKEN`, `ANTHROPIC_API_KEY` set empty, `CLAUDE_CODE_DISABLE_EXPERIMENTAL_BETAS=1`, `CLAUDE_CODE_ATTRIBUTION_HEADER=0` |
| Codex | `codex exec` inside bubblewrap (`bin/_ext.py codex`), with 20 Codex features disabled, `web_search` disabled (live with `--network`), bundled skills and analytics off, and a model catalog without `multi_agent_version` | `--ignore-user-config --ignore-rules` | `CODEX_HOME` a private tmpfs holding a copy of the auth file; without `--network`, `HTTPS_PROXY` and the others point at the egress proxy, which passes only `chatgpt.com`, `api.openai.com`, `auth.openai.com` (→ **The Codex egress allowlist is exact hosts, analytics off**); with a licence module and no `--network`, `KIT_LICENCE_FWD` |

Every route runs under `bin/limits-exec` with the run's `.limits`. The `claude` in the first row is `kit-env.json`'s
`claude` (default `claude` on `PATH`); the Codex route runs the real binary found as [above](#the-fields), mounted at
`/opt/codex`.

## Environment variables

Read by the tools; none is needed for ordinary use. The fixed ones are in [SCHEMAS.md §7](../../SCHEMAS.md#7-fixed-names).

| variable | read by | default | effect |
|---|---|---|---|
| `KIT_ROOT` | every Python tool and suite, not the hook | the tools' own tree | points the tools at a fixture tree; the launchers unset it for the approval check |
| `OPENROUTER_KEYFILE` | `bin/run-external`, `bin/astra-session` | `~/.config/openrouter/key` | the OpenRouter key file |
| `RUN_EXTERNAL_DEBUG` | `bin/run-external` | unset | any non-empty value: Claude Code's API debug log as `RUN/debug.log` |
| `KIT_SESSION` | `bin/handoff-archive` | `unknown` | the session name in an archive's file name (`--session` wins) |
| `KIT_HOOK_DEBUG` | the hook | unset | logs every hook input to `.claude/state/hook-debug.jsonl` |
| `BRAVE_KEYFILE`, `EXA_KEYFILE` | `bin/_ext.py` | `.env.brave`, `.env.exa` at the root | the search gateway's key files |
| `KIT_CODEX_BIN_DIR`, `KIT_CODEX_AUTH` | `bin/_ext.py`, `bin/check-env` (the first) | `kit-env.json`'s `codex_bin_dir`, else found from the `codex` command ([above](#the-fields)); `~/.codex/auth.json` | test overrides |
| `XDG_RUNTIME_DIR` | `bin/_ext.py` | `/tmp/kit-egress-<uid>/` when unset or not a directory | where the private socket directory is made: the egress socket and the licence relays' sockets |
| `KIT_WORKER_MODULES`, `KIT_WORKER_LICENCE_SOCKS`, `KIT_LICENCE_FWD` | the hook; `kit-shell` | unset | set by the launch, never by hand ([above](#the-licence-routes-environment-variables)) |
| `ASTRA_MODEL`, `ASTRA_PRO_MODEL`, `ASTRA_FABLE_MODEL`, `ASTRA_EFFORT` | [bin/astra-session](tools/astra-session.md) | `openai/gpt-6-astra`, `openai/gpt-6-astra-pro`, `~anthropic/claude-fable-latest`, `medium` | the external-orchestrator session's models and effort |
