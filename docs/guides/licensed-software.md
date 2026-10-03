# Licensed software

How to use a licensed program (Magma, Mathematica, Maple and the like) with the kit, without putting its licence where an
agent can read it.

There are two routes, and which one you use depends on the licence:

- **The licence is a file** (a key file, a node-locked licence, anything a program reads from disk): you run the program
  yourself, outside the kit, and bring its results in as outside input ([below](#a-licence-file-you-run-it-the-result-comes-in-as-outside-input)).
- **The program checks its licence out from a licence server** on the network, a host and a port: you can describe it
  as a *licence module*, and a run you approve gets the program and a way to that server and nothing else
  ([below](#a-licence-server-program-a-licence-module)).

Both routes are in [RULES.md §9](../../RULES.md#9-the-sandbox--enforced-not-convention)
(→ **A worker's tools come from the user's environment file**).

## Why a licence file is never mounted

A worker runs as your user account inside its sandbox, and it can inspect anything it starts: the program's open files,
its memory, and any licence file mounted beside it. Whatever a worker reads can reach its model's context, the model
provider, and the run's transcript. An orchestrator session is no different: what it reads goes to its provider too. So a
licence file belongs in no worker's sandbox and no session's context
([the sandbox](../concepts/sandbox.md); [SECURITY.md](../../SECURITY.md)).

Free programs with no secrets (PARI/GP, GAP, SageMath, Lean) are a different matter: they can be made available to
workers read-only, as modules of the instance's `kit-env.json`
([configuration](../reference/configuration.md#kit-envjson-the-environment-file)).

## A licence file: you run it, the result comes in as outside input

1. **Run the program yourself, outside every kit session**: in your own terminal, not through the orchestrator. Never
   paste the licence, or output that contains it, into a session or a message.
2. **Hand the result to the orchestrator as outside input.** Before anything acts on it, the orchestrator writes an
   intake record from [`templates/intake-record.md`](../../templates/intake-record.md): the files verbatim, their
   sha256, where they came from (the program and its version), and who has seen them
   ([RULES.md, Outside input](../../RULES.md#outside-input), rule 1; → **Outside input has an intake record first**).
3. **Rule each item's class**: usually *data* (explicit points, a map, a list of cases, a certificate) or *framing*
   (a suggested approach). Until you rule, an item is record-only (rule 2).
4. **Let it into a run only by name.** `intake/` is blocked from packets (a new instance blocks it from the start), so
   a file from it enters a worker's packet only as you except it, by its sha256, with your own
   `! bin/packet-except …` ([bin/packet-except](../reference/tools/packet-except.md); rule 8). The approval of that run
   then binds the file's bytes, like every other input.

## A licence-server program: a licence module

A module is a set of read-only mounts with `PATH` and environment additions, described in the instance's
`kit-env.json`. A module that names `licence_servers` is a licence module: it is mounted only for a run whose
`RUN/.modules` and whose launch both name it, and that run's worker reaches each named host and port through a relay on
the host, and nothing else ([the sandbox](../concepts/sandbox.md#the-licence-relay)).

### 1. Describe it in `kit-env.json`

The file is yours: the hook refuses the orchestrator any write to it (→ **The environment files are the user's**).
Edit it by hand. For example, with placeholder names, paths and server:

```json
{
  "modules": {
    "cas": {
      "binds": ["~/opt/cas"],
      "path": ["~/opt/cas/bin"],
      "env": {"CAS_LICENSE_SERVER": "lic.example.org:27000"},
      "check": "cas --version",
      "brief": "CAS: run `cas -q`; its licence comes from the server, nothing to set up",
      "licence_servers": [{"host": "lic.example.org", "port": 27000}]
    }
  }
}
```

- **Mount the program, never a licence file.** If the program also needs a licence file on disk, use the first route.
- **`licence_servers`**: each a plain host name and a port from 1024 to 65535, one server per port. List every port the
  program connects to; a connection to any other port goes nowhere. Two modules granted to one run may not share a port.
- **Point the program at the name.** Inside the sandbox each licence host's name resolves to 127.0.0.1, where a
  forwarder listens on the server's port. A program set to connect to the server's address rather than its name does
  not reach it.
- `env` is how this example tells the program where its server is; use whatever your program reads. `brief` is the line
  the worker's brief will carry about the module.

A `modules` key replaces an older instance's `.kit-lean` and `.kit-sage`; to keep them, describe them in the file too
([configuration](../reference/configuration.md#older-instances-kit-lean-and-kit-sage)).

### 2. Check it

```sh
bin/check-env
```

[bin/check-env](../reference/tools/check-env.md) reports the file's problems as `FAIL` and runs each module's `check`
inside a worker's sandbox. It starts no relay, so a licence module's check that needs its server shows `WARN`, not `FAIL`.

### 3. Make the run with the module

```sh
bin/new-run workspace-1 my-slug --role solver --problem my-problem --module cas
```

[bin/new-run](../reference/tools/new-run.md) refuses a name that is not a licence module of `kit-env.json`. It writes
`RUN/.modules` (one name per line), which the launch approval binds with the run's other bytes, and puts the module's
`brief` line in the brief under "Modules in your sandbox". The launch line it prints does not carry `--module`: add it.

### 4. Approve and launch with the same flag

```sh
bin/manifest 004-my-slug -- --via anthropic --model opus --effort high --module cas
```

After your approval of those bytes and flags:

```sh
bin/run-external 004-my-slug --via anthropic --model opus --effort high --module cas
```

`--module` is bound in the approval like `--network`. Before the approval is touched,
[bin/run-external](../reference/tools/run-external.md) refuses (exit 2, nothing spent) a `--module` that is not a
licence module of `kit-env.json`, any `--module` while the file has a problem, and a `--module` set that differs from
`RUN/.modules`, including a launch without `--module` for a run whose `RUN/.modules` names one. The same works with
`--via codex`. `--dry-run` makes those checks too, but on the Codex route the sandbox command it prints leaves out the
licence mounts.

### What the worker can and cannot reach

- **Can**: the module's mounts; each named host and port, through the relay; anything the server lets a client do over
  that port, such as checking out a licence. It can inspect the program it runs, so the module must hold no secret.
- **Cannot**: any other host or port, or name resolution beyond the licence hosts. The relay, outside the sandbox,
  decides where every connection goes; the worker only chooses whether to connect.
- **On a run launched with `--network`** the module is mounted, no relay is started, and the worker reaches the server
  as it reaches the rest of the network.

### `RUN/licence.log`

Every connection the relays carried, one line each, timestamped: `OPEN host:port`, then
`CLOSE host:port out=<bytes> in=<bytes> seconds=<s>`, or `UNREACHABLE host:port (<error type>)` when the server could not be
reached; never the contents. The launcher writes it outside the run while the worker runs and copies it into the run
afterwards (on the Codex route through `bin/_ext.py record`). A run with `--network` has none.

### What has been tested

Tested, with local stand-in servers (`tests/test_ext.py`, `T7LicenceRoute`): a command in the Claude route's sandbox,
and one in `kit-shell` inside a sandbox shaped like the Codex one, reached the named server through a real relay and was
refused a second server; a socket that is not the relay's is not mounted; a run not granted the module gets neither the
module nor the sockets; `module-check` refuses an unknown module and one without licence servers. `bin/run-external`
refuses a `--module` that is unknown or differs from `RUN/.modules`, before any approval, and its dry run shows
`--module` among the flags the approval binds.

Not tested: a real licensed program, a real licence server, a server on another machine, and a full launch through
`bin/run-external` with a worker using the module.

## What such a result can earn

A result that rests on a computer-algebra package earns `[VERIFIED]` only if an exact script that does not use the
package re-checks a certificate the package produced, or two independent packages agree; otherwise it is `[NUMERIC]`.
The package is named in the claim's `silent_links` either way
([RULES.md §2](../../RULES.md#2-claim-tags--mandatory-on-every-substantive-statement), "Computer algebra";
→ **Computer algebra is an optional module, and its results need a certificate**). This holds on both routes.

So ask the licensed program for something checkable, not just an answer: the explicit objects, the identity, the
certificate. A worker's free script then re-checks it inside the sandbox, and that check is what the claim stands on.
The licensed program's role is to find; the kit's is to verify.

## Never

- A licence file anywhere under an instance's directory, or in any path a worker's sandbox mounts.
- An agent asked to install or configure the licensed program, or to run it other than as a licence module you
  described.
- The licensed program's output from outside the kit entered into a run without an intake record.
