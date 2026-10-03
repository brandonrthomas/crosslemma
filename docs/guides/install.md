# Install

This guide helps you put the kit's prerequisites on a machine and confirm, with its four test suites, that the kit works
there before you make an instance.

Nothing here launches a worker or spends model time. The suites work in throwaway fixture trees, or in throwaway runs and
files they remove afterwards; one of them runs the real sandbox with fake model binaries
(→ **Fake binaries test the real sandbox**).

## What you need

Every item below is something the kit's code calls. "Where it comes from" names the file that needs it, so you can check
the claim yourself.

### Required

| Requirement | What it is for | Where it comes from |
|---|---|---|
| **Linux** with a **systemd user manager** and cgroup v2 | each worker runs in a transient user scope with a CPU quota and a memory cap; long runs and queues run as user services (`kit-run-<RUN>`, `kit-queue-<id>`) | [`bin/limits-exec`](../reference/tools/limits-exec.md) (`systemd-run --user --scope`, `cpu.stat` under `/sys/fs/cgroup`); [`bin/run-external`](../reference/tools/run-external.md) `--detach` and `--queue … --detach` |
| **bubblewrap** at `/usr/bin/bwrap` | the worker sandbox: every worker Bash command, every checker run, the whole Codex process | `.claude/hooks/sandbox.py`, [`bin/_ext.py`](../reference/tools/_ext.py.md), `.claude/sandbox/kit-shell` |
| **`/usr/bin/python3`**, 3.9 or newer: the system Python | every tool, the hook and every suite; the sandbox mounts `/usr`, so workers' own `python3` is the same interpreter unless a module or `kit-env.json`'s `worker_path` puts another first on their `PATH` | the `#!/usr/bin/python3` line of each Python tool, and the explicit `/usr/bin/python3` in the shell tools; `.claude/settings.template.json`; [`bin/check-env`](../reference/tools/check-env.md); → **Every tool, hook and test runs on `/usr/bin/python3`** |
| **git** | an instance is made from a committed kit, and records that commit | [`bin/new-workspace`](../reference/tools/new-workspace.md) refuses a kit that is not a git repository or has uncommitted changes in anything it copies |
| **GNU time** at `/usr/bin/time`, coreutils `timeout` | a run's CPU and memory record (`time.log`, `usage.json`); the wall-clock cap on the Claude routes | [`bin/limits-exec`](../reference/tools/limits-exec.md), [`bin/run-external`](../reference/tools/run-external.md) |
| **The Claude Code CLI** (`claude` on `PATH`, or the command an instance's `kit-env.json` names) | the orchestrator's session (the hook is registered in its project settings), and every worker on the `anthropic` and `openrouter` routes, launched headless | `.claude/settings.template.json`; [`bin/run-external`](../reference/tools/run-external.md) |
| **sudo**, once per instance | `chattr +a` on the instance's `LEDGER.log`, so the file is append-only | printed by [`bin/new-workspace`](../reference/tools/new-workspace.md); → **`LEDGER.log` is append-only** |

Python packages: the tools use the standard library only. The worker definition (`.claude/agents/kit-worker.md`) tells
workers only that the sandbox has the system's Python 3, and to check that a package imports before relying on it.
Install whatever packages your workers will need (for example numpy, scipy, sympy) for `/usr/bin/python3`.

### Optional, per route or module

| Option | What it is for | Where it comes from |
|---|---|---|
| **rsync** | the hook that mirrors session transcripts into `transcripts/`; without it the mirror does nothing | `.claude/hooks/mirror-transcripts.sh` |
| **Codex CLI**, logged in (`~/.codex/auth.json`) | the `codex` and `codex-net` routes: a worker of the OpenAI model family | [`bin/_ext.py`](../reference/tools/_ext.py.md); a new instance enables `anthropic,codex` by default ([`bin/new-workspace`](../reference/tools/new-workspace.md) `--routes`), one route of each family, because a `[PROVED]` or script claim needs a referee of the other family ([RULES.md §7](../../RULES.md#7-standing-rules-that-keep-cycles-convergent); → **A cross-family certify read**) |
| An **OpenRouter key file** at `~/.config/openrouter/key` (or the path in `OPENROUTER_KEYFILE`) | the `openrouter` routes | [`bin/run-external`](../reference/tools/run-external.md) |
| A **Lean 4 toolchain** (default `~/.elan`) and a **formal library** (for example a Mathlib-based Lake project) | `lean` artifacts, checked by the kernel; linked per instance with `--lean` | [`bin/new-workspace`](../reference/tools/new-workspace.md), [`bin/check`](../reference/tools/check.md) |
| **SageMath** as a conda environment with `bin/sage` | the optional computer-algebra module, mounted read-only for every worker with `--sage` | [`bin/new-workspace`](../reference/tools/new-workspace.md); → **Computer algebra is an optional module** |
| Any **other program** your workers need (PARI/GP, GAP, a licence-server program) | a module of the instance's `kit-env.json` ([below](#extra-programs-modules)) | [`bin/_env.py`](../reference/tools/_env.py.md) |
| Search gateway keys (`.env.brave`, `.env.exa` in an instance's root), a local SearXNG on `localhost:7764` | networked routes (`*-net`) only | [`bin/_ext.py`](../reference/tools/_ext.py.md) `gateway`; a missing key is reported, never fatal |

Two things to know about the Codex route:

- The Codex sandbox mounts Codex's real binary, which `bin/_ext.py` finds from the `codex` command on your `PATH`: the
  command itself when it is a native binary, or, for the npm package, the binary under its
  `node_modules/@openai/codex-*/vendor/*/bin/` or `vendor/*/bin/`. If it finds none, a Codex launch is refused; name the
  directory in an instance's `kit-env.json` as `codex_bin_dir`
  ([configuration](../reference/configuration.md#the-fields)). `KIT_CODEX_BIN_DIR` overrides both;
  [SCHEMAS.md §7](../../SCHEMAS.md#7-fixed-names) lists it as a test override.
- Every Codex run gets a copy of the login file inside its sandbox, for that run only. Nothing is copied into the kit or an
  instance.

No credential is ever copied into the kit or an instance. Each route's credential is placed by you, the user, where the
table says; [`bin/new-workspace`](../reference/tools/new-workspace.md) names them again when it makes an instance.

## 1. Get the kit

Clone the kit somewhere outside any instance you will make:

```sh
git clone <the kit's repository URL> ~/kits/kit
```

Leave the clone at a tagged commit (`git -C ~/kits/kit describe --tags --exact-match` names it). The kit holds its
settings only as templates: `.claude/settings.template.json` and `.claude/worker-net.settings.template.json`. There must be
no live `.claude/settings.json` in the kit, because a live one would install the kit's hooks into any session opened there
(→ **A scaffold ships its settings as a template, never live**).

## 2. Check the machine

From the kit's root:

```sh
/usr/bin/python3 bin/check-env
```

[`bin/check-env`](../reference/tools/check-env.md) is read-only. It prints one line per part the kit needs, each `ok`,
`WARN` (it works, with a limit) or `FAIL` (a run cannot work), and exits 1 if any line is `FAIL`:

| line | `FAIL` or `WARN` when |
|---|---|
| `python` | `FAIL`: no `/usr/bin/python3`, or one older than 3.9 |
| `bwrap` | `FAIL`: no `/usr/bin/bwrap` (the one the sandboxes run), or it cannot start a sandbox |
| `GNU time`, `timeout`, `git` | `FAIL`: not found (`/usr/bin/time` for GNU time) |
| `systemd user scope` | `FAIL`: [`bin/limits-exec`](../reference/tools/limits-exec.md) cannot enforce a run's CPU quota, memory cap or whole-run CPU budget, so `bin/run-external` refuses every launch |
| `rsync` | `WARN`: the transcript mirror does nothing |
| `claude` | `FAIL`: the Claude Code CLI is not found |
| `codex` | `WARN`: the Codex CLI or its real binary is not found; the Codex route is unavailable |
| `kit-env.json` | `FAIL`: each problem the environment file has; in the kit, which has none, `ok` |
| `module NAME` | each module's `check` command, run inside a worker's sandbox: `FAIL` if it exits non-zero, `WARN` instead for a licence module, whose server is not reached here; `ok` when the module has no check command |

Run it again in each instance you make, and after every change to its `kit-env.json`.

## 3. Run the four suites

From the kit's root:

```sh
for t in test_gate test_tools test_hook_gate test_ext; do /usr/bin/python3 tests/$t.py 2>&1 | tail -3; done
```

Run them with `/usr/bin/python3`, not whatever `python3` your shell finds: the sandbox and the hook use the system
interpreter, and a suite that passes on another one proves nothing about them.

| Suite | What it tests |
|---|---|
| `tests/test_gate.py` | the approval gate: manifests, digests, single use, expiry, voiding by an edited byte, batch and queue records |
| `tests/test_tools.py` | the tools: claim validation, the checker, the merge, the ledger writers, the packet scan; in the kit only, the docs checks |
| `tests/test_hook_gate.py` | the hook, run as Claude Code runs it, on synthetic input; a golden replay of the worker branch |
| `tests/test_ext.py` | the real sandboxes: a fake `codex` inside the real bwrap, the hook's Bash sandbox with and without network, and the launcher's refusals and `--dry-run` with a stub `claude`; nothing launches |

Each suite ends with `OK`. A skip is not a failure; it names its reason. The ones you may see:

- `no formal library linked in this tree`: the Lean end-to-end test, which runs only in an instance made with `--lean`.
- `no SageMath environment on this machine`, `no XDG runtime directory on this machine`, `no systemd user scope here`:
  the machine lacks an optional piece, or a piece whose absence step 2 already showed. The SageMath test looks only at
  `~/miniforge3/envs/sage`, so it skips with SageMath installed anywhere else.
- `no ripgrep here`: the check that `.ignore` keeps ripgrep out of the ledger, the locked data and the approval records;
  it needs `rg` on `PATH`.
- `this tree lies under /tmp, inside the sandbox's own /tmp tmpfs`: the tree is under `/tmp`, which the sandbox replaces
  with its own. Keep the kit and every instance outside `/tmp`.

The changelog records the test counts for each version, in the order test_gate/test_tools/test_hook_gate/test_ext
("Suites 32/121/46/54" at `kit-v0.6.14`), so you can compare.

## If a suite fails

- **`test_ext` fails while creating a sandbox.** bwrap could not make its namespaces. One common cause is a distribution
  that restricts unprivileged user namespaces; check your distribution's policy for bwrap.
- **A failure that names a path in another tree.** Run the suites from the kit's root, with the kit's own `tests/`.
- **Anything else.** Read the failing test's docstring, or its class's or file's: most name the lesson they guard. Do not make an instance on a kit
  whose suites fail; the instance copies the same tools and tests.

## Extra programs: modules

Beyond a formal library and SageMath, which `bin/new-workspace` links for you with `--lean` and `--sage`, whatever your
workers need outside `/usr` (PARI/GP, GAP, a solver built in your home) you describe in the instance's environment file, `kit-env.json`, as a *module*: read-only mounts, `PATH` and
environment additions, a self-test and one line for the brief. For example, with placeholder paths:

```json
{
  "modules": {
    "pari": {
      "binds": ["~/opt/pari"],
      "path": ["~/opt/pari/bin"],
      "check": "gp --version-short",
      "brief": "PARI/GP: run `gp -q`"
    }
  }
}
```

Write the file before you make the instance and give it to `bin/new-workspace --env FILE`, which checks it first
([A new instance](new-instance.md)); afterwards only you edit it, by hand. A file with a `modules` key replaces what
`.kit-lean` and `.kit-sage` would mount, so `bin/new-workspace` writes any `--lean` or `--sage` given beside it into the
instance's `kit-env.json` as the modules `lean` and `sage` ([A new instance](new-instance.md#1-make-it)). A module is mounted for every worker. One that
names licence servers is given only to a run you approve with it ([Licensed software](licensed-software.md)). A mount
source that is the root, a home directory, the instance or a credential directory is refused. Every field is in
[configuration](../reference/configuration.md#kit-envjson-the-environment-file)
(→ **A worker's tools come from the user's environment file**).

The interpreter is not configurable: the tools, the hook and the suites stay on `/usr/bin/python3`, the system Python
the sandbox also uses, so that a suite tests the interpreter the sandbox runs
(→ **Every tool, hook and test runs on `/usr/bin/python3`**).

## Next

[Make an instance for a problem](new-instance.md). Before the instance's first run, you run the same four suites again
inside it (`bin/new-workspace` prints this as a step); there the docs checks skip, since an instance has no
`scripts/docs/`. For the reasons behind the sandbox, see [the sandbox](../concepts/sandbox.md); for terms, the
[glossary](../reference/glossary.md).
