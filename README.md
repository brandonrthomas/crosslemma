# crosslemma

crosslemma ("the kit" in these pages) is a toolkit for working on an open mathematics problem with AI agents, built so
that nothing becomes a result until something other than its author has checked it.

An *orchestrator* (a Claude Code session) designs runs; *workers* (headless Claude Code or OpenAI Codex processes) do
the mathematics inside a sandbox; a *checker* and fresh *referees* (at least one of them from a different model
family than the work's author) decide what a result earns; the *user* (you) approves every launch and every entry in the ledger, bound to
the exact bytes you were shown. Everything is recorded: an append-only log, a claims ledger that is never edited, and a
handoff that the next session verifies before it trusts.

![One cycle of crosslemma: the orchestrator writes a brief, you approve the exact bytes, a sandboxed solver works, a checker script runs its artifacts, referees from another model family read the claims, the earned tag is computed, and you approve the append to the claims ledger.](docs/images/crosslemma.svg)

## Who it is for

One user, on one Linux machine, who wants agents to do real work on a hard problem and wants every claim to carry
its evidence. It is a research tool, not a service: it assumes you read what you approve.

**What it is not.** It is not autonomous: every launch waits for you. It is not a proof assistant, though it can use
one (Lean with Mathlib) and SageMath as optional modules. And its gates stop misreadings and ordinary mistakes by the
agents, not a deliberate forgery by your own user account: [SECURITY.md](SECURITY.md) says exactly what each mechanism
stops and what it does not.

## Where it came from

It was extracted from a research workspace on an open problem, whether a 3×3 magic square of nine distinct perfect
squares exists, and from that workspace's predecessor. Each rule in [RULES.md](RULES.md) points at the incident that
made it, in [LESSONS.md](LESSONS.md): the kit's design rationale, written as a record of what went wrong.

## Start

1. Install the prerequisites: [docs/guides/install.md](docs/guides/install.md) (Linux with bubblewrap and systemd
   user services, the system's Python 3 at `/usr/bin/python3`, the Claude Code CLI; optionally the Codex CLI, Lean with Mathlib, SageMath).
2. Check the kit itself:
   ```sh
   for t in test_gate test_tools test_hook_gate test_ext; do python3 tests/$t.py; done
   ```
3. Make an instance for your problem, outside the kit, and read what it prints:
   ```sh
   bin/new-workspace ~/kits/my-problem --problem my-problem
   ```
4. Write the problem statement in `~/kits/my-problem/problems/my-problem/PROBLEM.md`, open a Claude Code session in
   `~/kits/my-problem`, and follow [docs/guides/new-instance.md](docs/guides/new-instance.md) to the first canary.

Then [a full cycle](docs/guides/a-full-cycle.md) takes a claim from a solver run to the ledger.

## Configuration

An instance is configured by a few files at its root. They are yours: you edit them by hand, and the hook refuses the
orchestrator any write to them.

- **`kit-env.json`, the environment file**: what workers get beyond the system. *Modules* are programs mounted read-only
  with their `PATH` and environment, such as a Lean library or PARI/GP; a module that names licence servers reaches
  them only in a run launched with that module. The file also sets extra directories for every worker's `PATH`, which
  Claude Code and Codex CLIs to use, extra model families, and where the locked answer keys live. Give it to a new
  instance with `bin/new-workspace --env FILE`, and run `bin/check-env` after every change.
- **Routes** (`bin/new-workspace --routes`, default `anthropic,codex`): which providers launch workers, with or without
  the network. The default is one route per model family, because a proved or scripted claim needs a referee from the
  other family.
- **Run limits**: each run's CPU hours, threads and memory, set by `bin/new-run --cpu-hours --threads --mem-gb` and
  enforced on the worker's whole process tree.
- **Settings**: the Claude Code settings are templates in `.claude/`, filled in for the instance by `bin/new-workspace`.
  Never copy a live settings file between trees.

Every field and default: [configuration](docs/reference/configuration.md).

## Documentation

[docs/index.md](docs/index.md) is the map. In short:

- **Concepts**: [the trust model](docs/concepts/trust-model.md), [the approval gate](docs/concepts/approval-gate.md),
  [the sandbox](docs/concepts/sandbox.md), [packets and outside input](docs/concepts/packets-and-outside-input.md),
  [the record](docs/concepts/the-record.md), [roles](docs/concepts/roles.md).
- **Rules** (normative): [RULES.md](RULES.md), [SCHEMAS.md](SCHEMAS.md); one page: [FLOW.md](FLOW.md).
- **Reference**: [every tool](docs/reference/tools/README.md), [what the hook refuses](docs/reference/hook-refusals.md),
  [configuration](docs/reference/configuration.md), [glossary](docs/reference/glossary.md).
- **Changes**: [KIT-CHANGELOG.md](KIT-CHANGELOG.md). **Contributing**: [CONTRIBUTING.md](CONTRIBUTING.md).

## License

Apache License 2.0: see [LICENSE](LICENSE). Copyright 2026 Brandon Thomas.
