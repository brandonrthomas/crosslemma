# A new instance

This guide helps you make an instance of the kit for one problem and bring it to the point where its first real run can
be briefed: the instance made, its ledger locked, its suites passed and a canary run on every route it enables.

An instance is a separate directory and git repository holding the kit's tools, rules and hook, plus one problem's record;
its answer keys and label maps live outside it, in its locked directory.
The kit itself never runs work on a problem. See [the record](../concepts/the-record.md) for what lives where, and the
[layout](../reference/layout.md) for every file.

## Before you start

- The kit is installed and its four suites pass ([Install](install.md)).
- The kit is clean at a commit, preferably a tag. [`bin/new-workspace`](../reference/tools/new-workspace.md) refuses a kit
  with uncommitted changes in its tools, hook, harness, tests, templates or rules (`bin/`, `.claude/`, `harness/`, `tests/`,
  `templates/`, `RULES.md`, `FLOW.md`, `SCHEMAS.md`, `LESSONS.md`, `CLAUDE.md`), because the instance's `KIT-VERSION` must name a commit you can diff
  against later.
- You know four things:
  - **where** the instance goes: a new directory outside the kit, and outside `/tmp` (the sandbox mounts its own `/tmp`);
    its directory name also names its locked directory (`~/.local/state/crosslemma/<name>/locked/`), which must not
    exist yet (two instances of one name in different places would otherwise share it);
  - **the problem's slug**: lowercase letters, digits and hyphens, e.g. `my-problem`;
  - **the routes** it enables (below);
  - whether it links **a formal library** (`--lean`) or **SageMath** (`--sage`), and whether its workers need other
    programs, described in **an environment file** (`--env`).

One problem is one instance (→ **One workspace per problem**).

### Choosing routes

A route is how a worker reaches a model: `anthropic` (your own Claude Code login), `openrouter` (a key file), `codex` (your
Codex login), and the networked forms `anthropic-net`, `openrouter-net`, `codex-net`. The default, `anthropic,codex`, gives
one route of each model family. A `[PROVED]` claim needs a `certify` read from the other family than its producer's, and a
script claim a `sentence` read from the other family ([RULES.md §7](../../RULES.md#7-standing-rules-that-keep-cycles-convergent);
→ **A cross-family certify read**), so the tool warns about a set of routes of one family only (an `openrouter` route,
whose family is its `--model`'s, silences the warning).

Every enabled route gets a canary before real work on it ([FLOW.md](../../FLOW.md#outside-steps--called-not-wired-in)).
Enable only what you will use. A networked route gives workers the web in runs you approve with `--network`
([RULES.md §9](../../RULES.md#9-the-sandbox--enforced-not-convention)).

## 1. Make it

From the kit's root:

```sh
bin/new-workspace ~/kits/my-problem --problem my-problem
```

With options:

```sh
bin/new-workspace ~/kits/my-problem --problem my-problem --routes anthropic,codex --lean ~/lean/my-library --sage ~/miniforge3/envs/sage
```

- `--lean PATH` links a formal library: `lean` in the instance becomes a symlink to `PATH` (never a copy), the toolchain is
  recorded in `.kit-lean` (`--lean-toolchain`, default `~/.elan`), and the library's master list `lean.SHA256SUMS` is written
  now. Without `--lean` every library rule is inert.
- `--sage PATH` names a SageMath conda environment (it must contain `bin/sage`), recorded in `.kit-sage` and mounted
  read-only for every worker. A claim resting on it earns `[VERIFIED]` only through a certificate an exact script re-checks without the
  package, or a second independent package's agreement; otherwise `[NUMERIC]`
  ([RULES.md §2](../../RULES.md#2-claim-tags--mandatory-on-every-substantive-statement)).
- `--env FILE` gives the instance an environment file: the modules its workers get, licence modules, extra `PATH`
  directories, the CLIs, extra model families, and where the locked directory lives (`locked_dir`) ([configuration](../reference/configuration.md#kit-envjson-the-environment-file)).
  The file is checked against the new instance before anything is written; any problem refuses the whole command
  (exit 2) and nothing is made. Then its fields are written to `kit-env.json`, with `locked_dir` added if it names
  none, and committed with the rest. A file with a
  `modules` key replaces what `.kit-lean` and `.kit-sage` would mount, so `--lean` and `--sage` beside it are written
  into the copy as the modules `lean` and `sage`, mounted exactly as those files would have them (unless the file
  already names a module of that name)
  ([configuration](../reference/configuration.md#older-instances-kit-lean-and-kit-sage)).
  After that the file is yours to edit by hand; the hook refuses the orchestrator any write to it
  (→ **The environment files are the user's**).
- `--network-keys` also prints where the search gateway's keys go. `--no-commit` skips the first commit.

The tool launches nothing. It writes the instance and prints what you must do next. In the instance you will find:

| What | Notes |
|---|---|
| `bin/`, `harness/`, `tests/`, `templates/`, `.claude/hooks/`, `.claude/agents/`, `.claude/sandbox/` | copied from the kit |
| `RULES.md`, `FLOW.md`, `SCHEMAS.md`, `LESSONS.md`, `CLAUDE.md`, `.gitignore`, `.ignore`, `.claude/no-mcp.json`, the two `.claude/*.template.json` | copied; `CLAUDE.md` is a two-line pointer; `.ignore` keeps ripgrep out of the ledger, the locked data and the approval records (not a guard) |
| `.claude/settings.json`, `.claude/worker-net.settings.json` | filled from the kit's templates with the instance's absolute root, which `bin/new-workspace` knows only now (it also goes into `HANDOFF.md` and run 001's brief) |
| `problems/my-problem/PROBLEM.md`, `prior-art.md`, `attacks/` | from the templates; you fill `PROBLEM.md` |
| `DIRECTION.md`, `HANDOFF.md`, `handoffs/` | the first handoff, already archived |
| `LEDGER.log` | holding three lines (run 001's creation, the first handoff's archiving, the first data check); append-only once you lock it |
| `data/packet-rules.json` | `DIRECTION.md`, `HANDOFF.md`, `handoffs/` and `intake/` blocked from every packet from the start, and route-verdict words checked (`"verdicts": true`) |
| the locked directory, outside the tree | `~/.local/state/crosslemma/<instance>/locked/` (mode 0700), or the `--env` file's `locked_dir`; refused if it already exists, empty or not |
| `workspace-1/runs/001-context-canary/` | the first enabled route's canary, briefed and linted |
| `.kit-routes`, `KIT-VERSION` | the routes; the kit's commit, tag and path, the problem, the library, SageMath and the environment file |
| `kit-env.json` | always: it records `locked_dir`; with `--env`, your file's fields too |

## 2. What you do before the first run

The printout ends with a numbered list: lock the ledger, place the credentials, run the suites, run the canaries
(section 3), and read each canary's result. Its summary above that list says the problem statement must be filled
before any brief. In order:

1. **Lock the ledger.** The tool uses no sudo, so it prints the command for you:

   ```sh
   sudo chattr +a ~/kits/my-problem/LEDGER.log
   ```

   Agents write the ledger and never read it; you do (→ **`LEDGER.log` is append-only**).
2. **Place the credentials** for each enabled route, as listed ([Install](install.md#optional-per-route-or-module)). None
   was copied.
3. **Run the four suites inside the instance**, once:

   ```sh
   for t in test_gate test_tools test_hook_gate test_ext; do /usr/bin/python3 ~/kits/my-problem/tests/$t.py 2>&1 | tail -3; done
   ```

   Then check the machine from the instance with `bin/check-env`, which also reports the problems of its
   `kit-env.json` and runs each module's `check` command, where it has one, inside a worker's sandbox
   ([Install](install.md#2-check-the-machine)). It is not on the printout's list.

4. **Write the problem statement.** `problems/my-problem/PROBLEM.md` is a template. You supply or approve it before any
   brief: the statement with every quantifier explicit, the target statements, the variants a wrong argument would exclude,
   the self-checks.

## 3. Run the canaries

A canary is a worker whose task is to test the sandbox and its own starting context, not to do mathematics
(`templates/runs/canary-BRIEF.md`). Run them from **a fresh Claude Code session opened in the instance**: the hook is live
only in a session whose project is the instance, and a session opened elsewhere cannot drive it
(→ **A session works on the tree it was opened in**; → **Settings bind at session start**).

Run 001 is the first enabled route's canary. With the default routes:

```sh
bin/lint-brief 001-context-canary
bin/manifest 001-context-canary -- --via anthropic --model opus --effort low --max-turns 40
```

You approve those bytes and flags ([Approving](approving.md)). Then:

```sh
bin/run-external 001-context-canary --via anthropic --model opus --effort low --max-turns 40
```

For each further route, make a run with that route's harness note and give it the canary brief. For the `codex` route:

```sh
bin/new-run workspace-1 canary-codex --role other --harness codex
```

That prints the run's name (here `002-canary-codex`, the next free number). Fill the canary template into its `BRIEF.md`,
from the instance's root:

```sh
ROOT=$(pwd -P); RUN=002-canary-codex; KIT=$(sed -n 's/^kit-path: //p' KIT-VERSION)
sed -e "s|@RUNDIR@|$ROOT/workspace-1/runs/$RUN|g" -e "s|@RUN@|$RUN|g" -e "s|@ROOT@|$ROOT|g" \
    -e "s|@KITBASE@|$(basename "$KIT")|g" -e "s|@KIT@|$KIT|g" \
    templates/runs/canary-BRIEF.md > workspace-1/runs/$RUN/BRIEF.md
```

Then the same three steps with that route's flags:

```sh
bin/lint-brief 002-canary-codex
bin/manifest 002-canary-codex -- --via codex --model gpt-5.6-sol --effort low
```

and, after your approval, `bin/run-external 002-canary-codex --via codex --model gpt-5.6-sol --effort low`. A networked
route uses `--harness claude-net` or `--harness codex-net` and adds `--network` to the flags.

Watch a canary with [`bin/watch-run`](../reference/tools/watch-run.md) `RUN -f`. When it ends, **read its
`output/result.md` yourself**: Part A's question 1 must say no to every item but the residuals `RULES.md` §9 names (the account email can reach a worker), each yes saying where it appeared and what kind of thing it was, so that a yes can be traced; and the section **ESCAPES OR ORACLES FOUND** must say
none. Each line under **UNSEEN WRITES** (a marker written into a process's descriptor that did not come back in the
worker's own command output) is checked in the host's record of the run: the run's `launch*` files, `RECORD-EXT.md` and
logs; a marker found there is an escape. On the Anthropic route the canary's own subject (probing a sandbox) can trip
the model provider's safety classifier, and the session is then answered by a fallback model, which the launcher flags
(`model_fallback`); that is expected for a canary and recorded, not a failure: what a canary tests is the sandbox, which
the hook enforces whatever model answers. A reported escape is checked against the host before it is believed
([RULES.md §9](../../RULES.md#9-the-sandbox--enforced-not-convention)).

## 4. Then

- **Calibrate before trusting.** Before any verdict on the open problem counts, run the pipeline on a ladder of known
  results with planted errors, and put each model through each role's ladder before it is used in that role
  ([RULES.md §7](../../RULES.md#7-standing-rules-that-keep-cycles-convergent); → **Calibrate before trusting**).
- **Start the cycle**: prior art into `prior-art.md`, a `DIRECTION.md` or an attack README from `templates/`, a brief, the
  two gates ([A full cycle](a-full-cycle.md)).
- **Each cycle ends with a handoff** on `templates/HANDOFF.md`, and the next starts in a fresh session
  (→ **Fresh orchestrator per cycle**). If you want an orchestrator prompt beyond the handoff's own, see
  `templates/orchestrator-prompt.md`.

## What not to do

- **Do not copy an instance, or the kit, by hand.** The settings carry the instance's absolute root; a copied tree would
  install its origin's hook, pointed at its origin's ledger, into your session
  (→ **A scaffold ships its settings as a template, never live**). [`bin/run-external`](../reference/tools/run-external.md)
  refuses to launch from a tree whose settings do not register its own hook.
- **Do not upgrade it by copying the kit over it.** An instance is upgraded only from a diff against `KIT-VERSION`
  ([Upgrading an instance](upgrading-an-instance.md)).
