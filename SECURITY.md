# Security

What the kit's mechanisms stop, what they do not, and how to report a problem. The rules are the authority: this page
summarises [RULES.md §6](RULES.md#6-approvals--the-gate) and [§9](RULES.md#9-the-sandbox--enforced-not-convention);
[the approval gate](docs/concepts/approval-gate.md) and [the sandbox](docs/concepts/sandbox.md) explain them.

## The threat model

The kit guards against **agents**: an orchestrator that misreads an instruction, overreaches, or takes an ordinary
command for permission; a worker that tries to read beyond its run, reach the network, or outlast its budget; text
from outside (another model's output, an analyst's notes, a paper) steering a run it should not reach.

It does **not** guard against **the user's own account acting deliberately**. The orchestrator runs as your
user, so a deliberate forgery of an approval is possible; the kit says so itself: "What this stops is a misreading
followed by an ordinary command" ([RULES.md §6](RULES.md#6-approvals--the-gate), "Limit, accepted by design").

## What each mechanism stops

**The approval gate.** Every launch and every append to the claims ledger needs an approval that is the user's
act, bound to the exact bytes, claim ids and launch flags shown by [bin/manifest](docs/reference/tools/manifest.md),
single-use, and expiring after 30 minutes; a changed byte or flag voids it (→ **Every launch and every ledger append
consumes a byte-bound**). The user approves either with a `!` command at the terminal, which bypasses the session's
hooks, or by allowing a prompt whose text the hook computes from the bytes, offered only in permission mode default or
auto (→ **The tap route needs `--digest`**). Stops: a run launched or a claim recorded on an agent's own initiative, or
on bytes the user did not see.

**The hook on the orchestrator.** [What it refuses](docs/reference/hook-refusals.md), in its own words, includes: any
command naming the approval tool, except the one plain call that becomes a tap and a plain `git add`, `diff`, `log`,
`show`, `status`, `commit`, `restore`, `mv` or `rm`; the approvals directory; editing the packet rules and their
exceptions, and any command naming them or their tools except a plain `git add`, `commit`, `status` or `diff`;
reading or writing the append-only log, and a git command in the tree that prints file contents without naming plain
paths that hold no protected file; writing the referee bindings or the cross-family rulings; a bare headless launch of
any provider's CLI; the messaging and workflow tools; any agent call of a worker type; keys typed into another terminal
pane; and the message bus's files (→ **An orchestrator types into no other pane and touches no mailbox**). A Monitor
command is checked as a Bash command is. [RULES.md §9](RULES.md#9-the-sandbox--enforced-not-convention) words the
approval tool's git exception more narrowly than the code. Stops: an orchestrator routing around the gate with an
ordinary tool call.

**The worker sandbox.** Every worker is a headless process that the hook binds to its one run directory from the
launch's environment, before its first tool call; its Read and Write elsewhere are refused, and every shell command runs
in bubblewrap with that directory writable, the system read-only, a private `/tmp`, a clean environment and, unless the
run was approved with `--network`, no network (→ **First `Read` binds a worker to one run directory**,
→ **A headless worker is recognised by**). [RULES.md §9](RULES.md#9-the-sandbox--enforced-not-convention) says the
worker's first `Read` binds it. Codex workers run inside the same kind of sandbox, in their own process namespace
(→ **A kill-all runs only where it cannot reach past the run**). CPU time, memory, wall-clock time and tool calls are
capped and enforced, not just requested, from a copy of the approved limits the worker cannot rewrite
(→ **Limits are enforced, not promised**). What the host writes into a run after its worker (logs, usage, records, the
checker's output) is written to a fresh name and renamed over the target, so a link the worker planted is replaced,
never followed (→ **Host code never writes into a run directory through a name the worker could have made a link**). A
hook that does not load refuses every call, through a load check in the settings. Stops: a worker reading another run,
the record or your files; a worker without `--network` reaching the internet; a runaway job; a worker turning a host
write into a write anywhere your account can write.

**The earned tag.** What decides a claim's earned tag lives outside every run directory, where no worker writes: a
referee run's question and the bytes it was given are bound by [bin/new-run](docs/reference/tools/new-run.md) in
`data/referee-bindings/`, and the cross-family rulings are the user's, in `data/cross-family-rulings.json`; a
`referee.json` in a run with no binding never counts. A proof assistant's axiom audit runs from the compiled artifact,
after a kernel replay, in a sandbox call that runs no artifact code (→ **What decides an earned tag is never in a run
directory**, → **The axiom audit runs where the artifact's syntax cannot reach**). Stops: a producer certifying its own
claim, by writing a verdict, a ruling or an audit result for it.

**The network.** A run gets the network only when the user's approval bound its `--network` flag, with a matching
harness note (→ **Networked and Codex launches need their flags bound**). Such a run shares the host's network: the open
web, and services listening on this machine's localhost. It leaves `RECORD-EXT.md`, with hashes of its gateway and
egress logs and of every file under its `downloads/`. A Codex run **without** `--network` has a network namespace of its
own, and its only way out is an egress proxy that passes the model provider's hosts, named exactly, and nothing else
(→ **The Codex egress allowlist is exact hosts**).

**Packets and outside input.** What a worker may be given is scanned against blocked material, including every
outside input's text, before launch (→ **No packet carries blocked material**); outside input gets an intake record
before anything acts on it ([RULES.md §8](RULES.md#outside-input)). Stops: an answer key, a sibling run's output or
someone's framing reaching a worker by accident.

**Credentials.** No tool copies a credential into an instance's tree; [bin/new-workspace](docs/reference/tools/new-workspace.md)
only names where each route's credential lives. Two reach a running worker: each Codex run gets a copy of the user's
`~/.codex/auth.json` in its sandbox's private tmpfs, for the Codex process, with Codex's home hidden from the commands the
model runs; and on the OpenRouter route the key is in the environment of the worker's Claude Code process. The clean
environment applies to the commands a worker runs.

## What none of this stops

- A deliberate act by your own user account: a script run outside the hook, an approval record forged by hand.
- You approving something you should not have. The gate shows you the exact bytes; reading them is yours.
- What the model providers do with what you send them. Prompts and packets go to Anthropic, OpenAI or OpenRouter
  under your accounts and their terms.
- Anything a run approved with `--network` can reach: the open web and services on this machine's localhost.
- A kernel or bubblewrap escape. The sandbox is ordinary Linux namespaces, not a virtual machine.

## Reporting a problem

Please report a way around a gate, a sandbox escape, or a credential exposure privately, through this repository's
security advisories on GitHub, not in a public issue. Include the kit version (`KIT-VERSION` in an instance, or the tag; a clone of
the public copy has no tags, so the top heading of `KIT-CHANGELOG.md`),
what you ran, and what happened.
