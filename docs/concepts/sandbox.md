# The sandbox

This page answers: what can a worker reach, what stops it from reaching anything else, and where does that stop
short?

## Two kinds of session

The kit treats its two kinds of session very differently
([RULES.md §9](../../RULES.md#9-the-sandbox--enforced-not-convention)):

- **The orchestrator** is unrestricted apart from the approval gate. Every call an orchestrator session of this tree
  makes is logged to the ledger; a short list of things is refused (the approval tool, but its one plain digest call,
  which becomes the user's prompt; the approval records; reading the locked data, wherever `locked_dir` puts it; the
  packet lists; the environment files that decide what a worker's sandbox mounts; reading or writing the ledger, a Grep
  or Glob rooted above it included; writing the referee bindings or the cross-family rulings; a git command in the tree
  that prints file contents without naming plain, unprotected paths; a bare headless launch of a model CLI; keys typed
  into another terminal pane; and a few more). A Monitor command is checked exactly as a Bash command is. The full
  list, in the hook's own words, is [hook refusals](../reference/hook-refusals.md).
- **A worker** (a solver, a referee, an evaluator, a canary) is a model process confined to one run directory. The
  rest of this page is about workers.

Both are policed by one file, [`.claude/hooks/sandbox.py`](../../.claude/hooks/sandbox.py), which Claude Code calls
before and after every tool call. A Codex worker is not a Claude Code process, so the hook does not see it; its
sandbox is built by the launcher instead (see "Other routes" below). See [roles](roles.md) for who is who.

## How a worker starts

Every worker is a headless main process, started by [`bin/run-external`](../reference/tools/run-external.md) after
the user's approval. It is never a subagent of the orchestrator's session: a subagent inherits that session's
harness text (mode notes, attribution guidance, a request for a closing report, connector instructions), and a headless
process does not. The hook refuses every agent call of the worker type, approved or not, without spending the approval
(→ **Every worker is a headless main process**).

The launcher sets a variable in the worker's environment naming its run directory. The hook reads it and treats the
process as a worker bound to that run. The marker lives in the environment because the worker cannot change it; a
file in the run directory would not do, since the worker can write there (→ **A headless worker is recognised by**).

## What a worker can use

This section describes the Claude routes; the Codex route builds the same kind of sandbox its own way (below).

**Tools.** Read, Write and Bash, nothing else. Edit, Glob and Grep are withheld because the harness validates Edit input
before hooks run, which would let a worker probe the contents of files it cannot read
(→ **Workers have Read, Write, Bash only**). A networked worker also gets WebSearch and WebFetch, under an approval
that binds `--network`.

**Read and Write.** A path is resolved to its real location and must fall inside the run directory. Symlinks, `..` and
`/proc` tricks resolve outside it and are refused with the same message whether the target exists or not, so the
refusal does not tell the worker what is there (→ **First `Read` binds a worker to one run directory**). The path is
checked, then used; nothing of the worker runs between the two, since its Bash runs in the foreground only
(`run_in_background` is set false) and everything a command started ends with its sandbox
(→ **Host code never writes into a run directory through a name the worker could have made a link**).

**Bash.** Every command is rewritten to run inside a [bubblewrap](https://github.com/containers/bubblewrap) sandbox:

| inside the sandbox | how |
|---|---|
| the run directory | read-write, and the working directory |
| `/usr` (the OS's programs and libraries) | read-only |
| the instance's modules and `worker_path` directories ([below](#modules-and-licence-servers)); on an older instance, its linked formal library and SageMath environment | read-only, at the paths the environment file names |
| `/etc` | an empty tmpfs with a handful of read-only files (alternatives, linker cache, time zone, the system Python's `/etc/pythonX.Y`; on a networked run, name resolution and TLS roots; on a licence run, an `/etc/hosts`), then remounted read-only |
| `/tmp` | a private tmpfs |
| the network | none: the sandbox has its own network namespace. A run launched with `--network` shares the host's; a run granted a licence module reaches its servers through a relay ([below](#the-licence-relay)) |
| the environment | cleared; `HOME` is the run directory; thread caps set |
| the host name | `sandbox` (→ **`bwrap --hostname sandbox`**) |
| `/opt/kit/bin` | read-only: the `ledger` command; the search helpers on a networked run; the forwarder on a licence run; any module mount whose `dest` is there (an older instance's `sage` shim, for one) |
| everything else (the rest of `/home` and `/opt`, the run directory's parents) | not mounted; the sandbox's root is remounted read-only after the binds, so nothing can be written there either; for a tree under `/tmp`, the parent chain lies in the sandbox's private `/tmp` and stays writable, still reaching nothing on the host (→ **The sandbox's root is remounted read-only after the binds**) |

The `ledger` command queues a line that the hook moves into the project ledger; the worker cannot read the ledger back.

The checker, [`bin/check`](../reference/tools/check.md), runs every artifact in this same sandbox, with the same
always-mounted modules, so a script that passed for the worker is checked under the conditions it ran in. Two
exceptions: the checker's sandbox has no network and no licence module, whatever the run was launched with.

## Limits that are enforced

A brief states the run's caps as facts; it does not ask the worker to honour them
(→ **Limits are enforced, not promised**). The caps come from the run's `.limits` file, written by
[`bin/new-run`](../reference/tools/new-run.md) and bound in the approval, and the launch flags. Once the approval is
used, the launcher keeps a copy of that file outside the run, and the hook reads the copy: the worker can rewrite the
run's own file, not the copy (→ **A hook that does not load refuses, and the limits a worker runs under are the approved
ones**).

- **CPU rate and memory.** [`bin/limits-exec`](../reference/tools/limits-exec.md) runs the worker's whole process tree
  in a systemd user scope with a CPU quota and a memory cap.
- **Total CPU.** The same tool watches the scope's CPU time and stops the run at its budget, background jobs included
  (exit 152, `cpu_cap_hit`; → **The whole-run CPU budget is enforced**). On the Claude routes each sandboxed command
  also starts with a per-process CPU limit and thread-pool variables from that copy; the CPU limit binds the command,
  the thread variables are defaults the worker can set again itself. What binds the whole run is the scope's CPU quota,
  memory cap and whole-run budget, fixed at launch.
- **Wall clock.** Every route has a wall-clock cap, one deadline across retries (→ **A wall-clock cap on every route**).
  A retry after an upstream rate limit is decided from the CLI's own words, never from what the worker printed. Stopping
  a detached run (`systemctl --user stop kit-run-NAME`) stops its worker too: the scope is named, and the launcher stops
  it when it is itself stopped (→ **A launch's decisions are its own, and a stop reaches the worker**).
- **Tool calls.** A turn cap on the Claude routes; on Codex the launcher counts tool calls from the transcript
  (→ **A Codex worker's tool calls are capped**). A brief may not promise more calls than the cap.

There is no spending cap: the cost figure in a run's transcript is Claude Code's estimate from a price table, not a
meter (→ **No spending cap on any run**).

## Modules and licence servers

What a worker has beyond the system comes from the instance's environment file, `kit-env.json`
([configuration](../reference/configuration.md#kit-envjson-the-environment-file);
[RULES.md §9](../../RULES.md#9-the-sandbox--enforced-not-convention);
→ **A worker's tools come from the user's environment file**). No program is built into the hook.

- **A module** is a set of read-only mounts, each at its own path unless the file gives another, with additions to
  `PATH` and the environment. A module without licence servers is mounted for every worker, on every route. An instance
  made before the environment file keeps its formal library and SageMath environment as two such modules, mounted
  exactly as before.
- **`worker_path`** directories are mounted read-only for every worker and put on its `PATH`. The order is
  `/opt/kit/bin`, then the modules' entries, then `worker_path`, then `/usr/bin:/bin` (on Codex, `/opt/codex` comes
  second).
- **A licence module**, one that names licence servers, is mounted only for a run whose `RUN/.modules` and whose
  launch (`--module NAME`, bound in the approval) both name it ([licensed software](../guides/licensed-software.md)).
  The launcher tells the hook through the worker's process environment, which the worker cannot change, as it does for
  `--network`; never through a file in the run directory.
- **Refused mount sources.** Whoever wrote the file, a mount source or `PATH` entry that is the root, a home directory
  or one holding it, the instance or any directory inside or holding it (but its library link and the kit's own shims),
  or a credential directory such as `~/.ssh` or `~/.codex` is refused: a module with such a source is not mounted, and
  such a `worker_path` entry is dropped. The orchestrator cannot write the file at
  all (→ **The environment files are the user's**); the refusal also catches the user's own slip. If the hook
  cannot load the environment code, it mounts no module: a worker without its tool fails loudly, and is never given
  more.

### The licence relay

A worker granted a licence module, on a run without `--network`, still has no network. It reaches each licence server
through two pieces:

- **A relay on the host**, outside every sandbox, one per server, started by the launcher before the worker. It listens
  on a unix socket in the user's private socket directory (the one that holds the Codex egress socket) and carries
  every connection to its one fixed host and port. The worker chooses whether to connect, never where. Each connection's
  open and close, with the bytes each way, go to `RUN/licence.log`; its contents never do.
- **A forwarder inside the sandbox**, on 127.0.0.1 at the server's port, passing each connection to the relay's
  socket, which is all of the relay the sandbox sees (mounted at `/opt/kit/licence/<i>.sock`). An `/etc/hosts` names
  each licence host at 127.0.0.1, so a program configured with the server's name and port connects to the forwarder.

On the Claude routes the hook mounts the sockets, the forwarder and the `/etc/hosts`, and starts one forwarder per
server at the start of every command. It takes the sockets only from the worker's process environment, and only if each
is a socket named as the relay names it and the ports are the granted modules' own, in order; otherwise none of this is
mounted, and the licensed program fails to reach its server. On the Codex route the launcher mounts the same pieces into
the Codex sandbox, and `kit-shell` starts the forwarders inside each command's own sandbox, which has its own network
namespace. A run launched with `--network` has the host's network already: it gets the module's mounts and no relay.

The relay carries bytes, not meaning: whatever the server allows a client to do over that port, the worker can do. It
was tested with local stand-in servers on both routes; no real licensed program has been run through it.

## What reaches the worker's context

Beyond its packet (see [packets and outside input](packets-and-outside-input.md)), the kit works to keep the worker's
context empty of anything it did not choose:

- no memory, no skills, and an empty MCP configuration, so no server's instructions arrive
  (→ **No run method shows memory or skills**, → **Headless launches carry `--strict-mcp-config --mcp-config no-mcp.json`**);
- the user-level `CLAUDE.md` files are excluded, and the instance's own `CLAUDE.md` is a two-line pointer, because
  Claude Code injects that file into every worker (→ **`CLAUDE.md` is injected in full into every worker**);
- the parent session's routing variables are dropped, so a worker is answered by the provider the approval named
  (→ **A parent session's routing never reaches a worker**).

What still reaches it is named rather than hidden: the account email, the working directory's path, the sandbox
command line and its mount paths, and a harness note preferring Bash; on the Codex route, also the worker's own queued
ledger lines (its `.ledger-outbox`), never another run's (→ **Worker context residuals are named**).

## The record of a run

The worker's transcript is written outside its reach while it runs and moved into the run directory only after it
stops, so a worker cannot alter its own record (→ **Transcripts are written outside the worker's reach**). A run
directory is launched once: a second launch would show the new worker the first one's transcript and output
(→ **A run directory is launched once**). What the host puts in the run after the worker (its transcript, the usage and
time records, the copied logs, `RECORD-EXT.md`, the checker's output) is written to a fresh name and renamed over the
target, so a link the worker left there is replaced, never followed. The models that answered and the effort their
requests carried are put on the exit line: on the Claude routes from the run's transcript; on Codex from Codex's
session file, copied after everything the worker left running has ended, which Codex's own tools could still have
edited (below). A session file under that name on a Claude route is the worker's, and is removed.

## Other routes

- **Codex.** The whole Codex process runs inside the sandbox, and each command it runs gets a nested sandbox of its own,
  with its own processes and with Codex's home (the login token, the session log) hidden from it. On a run without
  network the only ways out are an egress proxy that allows exact hosts of the model provider and, on a licence run, the
  licence relays
  (→ **A Codex worker's commands run apart from Codex**, → **The Codex egress allowlist is exact hosts**). Before the
  approval is touched, the launcher renders the prompt offline and refuses a launch that would still offer sub-agents
  (→ **A Codex worker has no sub-agents**).
- **Networked runs.** A run gets the web only with `--network` bound in its approval and a harness note for that route
  in its packet. Search keys stay in a gateway outside the sandbox. Every such run leaves `RECORD-EXT.md`: what it could
  read, what network it had, and hashes of what it downloaded
  (→ **Networked and Codex launches need their flags bound in the approval**).

## When the sandbox itself fails

- An exception inside the hook's main routine denies the call. A hook that fails to load (a bad edit) is caught by a
  second command in the settings, which loads it and exits 2 when it cannot, so every call is refused; input the hook
  cannot parse is refused too. The hook is still changed only as a tested candidate, installed by an atomic rename
  (→ **Change the hook only as a tested candidate**, → **A hook that does not load refuses, and the limits a worker runs
  under are the approved ones**).
- An error inside the approval gate refuses gated calls only, and leaves the orchestrator's other work alone. A ledger
  the hook cannot write refuses what needs its record (an approval tap, an agent launch); other calls go through the gate
  as usual, and the user is told they are not recorded.
- The hook only runs because the instance's settings register it. Before touching the approval, the launcher refuses
  a tree whose `.claude/settings.json` does not register the hook on PreToolUse for every tool and on PostToolUse
  (the file is parsed), or, for a networked Claude run, that has no `worker-net.settings.json`. Settings are shipped as
  templates and filled when an instance is made, never copied live; an upgrade refills them
  (→ **A scaffold ships its settings as a template, never live**).
- Settings bind at session start, so a change needs a restart or a headless test and then a canary run
  (→ **Settings bind at session start**). The hook itself is changed only as a tested candidate, installed atomically,
  with no worker in flight (→ **Change the hook only as a tested candidate**).

## What the sandbox does not stop

- **The model provider sees the packet.** A worker is a model behind an API. Everything in its context leaves the
  machine to that provider. The sandbox limits what the worker's tools can touch, not what the provider receives.
- **The residuals above.** They are named, not removed.
- **Codex's own tools.** Codex's in-process tools act as the Codex process, so a model could append to its transcript
  pipe or edit its session log, though not rewrite what the host has already copied.
- **A forger with the user's account.** The orchestrator runs as the user's Unix account; the hook matches by name and
  path, and a deliberate workaround gets past it: `cat L*` reads the ledger without naming it, and only git is guarded
  by what it prints (→ **The ledger is guarded by name; git is guarded by what it prints**). The kit does not claim to
  stop that
  ([RULES.md §6](../../RULES.md#6-approvals--the-gate)).
- **A worker's own account of an escape.** A write can succeed inside the sandbox and reach nothing on the host (its
  private `/tmp`, for one); before the root was remounted read-only, a write to the run directory's parent chain did
  exactly that and looked like an escape. A report of an escape is checked against the host before it is believed
  (→ **The run directory's parent chain is writable inside the sandbox**).
- **A host without a systemd user manager.** No worker runs there: [`bin/limits-exec`](../reference/tools/limits-exec.md)
  refuses when it cannot make the scope, and `bin/run-external` asks it (`--probe`) before the approval is touched, so
  nothing is approved or spent (→ **Limits are enforced, not promised**).

## Related

- [The approval gate](approval-gate.md): what has to happen before a worker starts.
- [Configuration](../reference/configuration.md): the settings files and limits.
- [Glossary](../reference/glossary.md).
