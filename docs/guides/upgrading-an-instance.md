# Upgrading an instance

This guide helps you bring an instance up to a newer version of the kit: find what changed since the instance was made,
check the instance has no local edits in those files, replace them, run the suites, and run canaries if the hook changed.

An instance is never upgraded automatically, and never by copying the kit over it. The upgrade is a diff against the kit
commit the instance records, put to you, and applied by a session opened in the instance
([RULES.md §11](../../RULES.md#11-working-with-the-operator); → **A session works on the tree it was opened in**). Changing
the tools, hook or rules is method work, so both halves happen in methods sessions, never in a working session
([RULES.md §7](../../RULES.md#7-standing-rules-that-keep-cycles-convergent); → **Method changes never in a math session**;
[A methods session](methods-session.md)).

The examples use a kit at `~/kits/kit` and an instance at `~/kits/my-problem`; `kit-vX.Y.Z` is the target tag.

## Part 1, in a session opened in the kit: the diff

### 1. Read the instance's `KIT-VERSION`

```sh
cat ~/kits/my-problem/KIT-VERSION
```

It names the kit commit the instance was made from (`kit-commit:`), its tag if it had one, the routes and the modules, and
one `upgraded:` line per earlier upgrade. The commit to diff from is the one the last `upgraded:` line says the instance
was brought to, or `kit-commit:` if there is none. The examples below use `46b59bad5ed0`.

### 2. List the files that changed

Diff that commit against the target tag, over exactly what [`bin/new-workspace`](../reference/tools/new-workspace.md) copies:

```sh
git -C ~/kits/kit diff --name-status --no-renames 46b59bad5ed0 kit-vX.Y.Z -- bin harness tests templates .claude/hooks .claude/agents .claude/sandbox RULES.md FLOW.md SCHEMAS.md LESSONS.md CLAUDE.md .gitignore .ignore .claude/no-mcp.json .claude/settings.template.json .claude/worker-net.settings.template.json
```

`M` is a changed file, `A` a new one, `D` one the kit removed (`--no-renames` shows a renamed file as a `D` and an `A`). Read the [changelog](../../KIT-CHANGELOG.md) entries between
the two versions: each says whether the hook or the tools changed and what an instance taking it must do.

Files that are not in that list are the instance's own and are never overwritten from the kit: `PROBLEM.md`,
`prior-art.md`, `DIRECTION.md`, `HANDOFF.md`, `CLAIMS.md`, `LEDGER.log`, the run directories, `data/` and `intake/`. The
two filled settings files are not copied either; when a settings template changed, they are filled again from the new
template (Part 2, step 3).

### 3. Check the instance has no local edits

For each changed file, compare the instance's copy with the kit's at the instance's commit:

```sh
git -C ~/kits/kit show 46b59bad5ed0:bin/check | cmp - ~/kits/my-problem/bin/check && echo unchanged
```

A file that differs was edited in the instance. Stop and put it to the user before anything overwrites it.

### 4. Note what the upgrade will need

- **The hook, the settings templates, the agent definition or a harness note changed**: a canary on every enabled route
  afterwards ([FLOW.md, outside steps](../../FLOW.md#outside-steps--called-not-wired-in);
  → **Settings bind at session start**).
- **A settings template changed**: the instance's filled `.claude/settings.json` or `.claude/worker-net.settings.json`
  must be filled again (Part 2, step 3), and the session restarted.
- **A file whose name the hook keeps from the orchestrator**: the approval tool (`bin/approve`) and the packet tools
  (`bin/packet-block`, `bin/packet-except`). The hook refuses the orchestrator any command naming them except a few plain
  git commands (and, for the approval tool, the plain tap call), so a `git archive … | tar` of them is refused and the
  user copies those with `!` ([hook refusals](../reference/hook-refusals.md)). A `git -C ~/kits/kit …` reads the kit's
  repository, not the instance's, so the hook's git rules for the instance do not apply to it.

### 5. Hand it over

The kit session gives the user the diff, the file list, the result of step 3, and an opening prompt for a session in
the instance. The user rules whether to take it. Both handoffs record it.

## Part 2, in a session opened in the instance: applying it

### 1. Preflight and nothing in flight

Run the instance's handoff preflight. Then check that no worker or queue of this instance is running:

```sh
systemctl --user list-units 'kit-run-*' 'kit-queue-*'
```

This lists the units of every instance on the machine: a unit is named after its run (`kit-run-<run>`) or queue
(`kit-queue-<id>`), not after its instance, so match the names against this instance's runs. Whether an approval is
waiting to be used is a question for the user: the hook refuses the orchestrator any command naming the approvals
directory, so the user looks in `.claude/state/approvals/`.

The hook is live code for every sandboxed command, so it is replaced only with no worker in flight
(→ **Change the hook only as a tested candidate**).

### 2. Commit the ledger first

The ledger has lines since the last commit (the hook appends on every call). Commit it alone, with nothing else in the
command; the hook allows only a plain `git add`, `git commit`, `git status`, `git diff --numstat` or `git diff --stat` that names it
([RULES.md §8](../../RULES.md#8-the-record)):

```sh
git add LEDGER.log
```

```sh
git commit -F .git/UPGRADE-LEDGER-MSG
```

(the message written first to that file; commit messages always come from a file, → **No `cd` in a compound command**).

### 3. Replace the files, the hook last

Extract every changed and added file, except the hook and the user's files, from the target tag:

```sh
git -C ~/kits/kit archive kit-vX.Y.Z -- bin/check bin/_lib.py RULES.md LESSONS.md | tar -x -f - -C ~/kits/my-problem
```

`git archive` keeps each file's mode. Remove any file the diff marked `D`.

The user copies the files the hook keeps from the orchestrator, at the terminal:

```sh
! git -C ~/kits/kit archive kit-vX.Y.Z -- bin/packet-block | tar -x -f - -C ~/kits/my-problem
```

The hook goes last, as a tested candidate (→ **Change the hook only as a tested candidate**): written to a new name,
tested there with the instance's new tests, and only then renamed into place, so that no call ever sees half a hook:

```sh
git -C ~/kits/kit show kit-vX.Y.Z:.claude/hooks/sandbox.py > ~/kits/my-problem/.claude/hooks/sandbox.py.new
```

```sh
HOOK_UNDER_TEST=~/kits/my-problem/.claude/hooks/sandbox.py.new /usr/bin/python3 ~/kits/my-problem/tests/test_hook_gate.py 2>&1 | tail -3
```

```sh
HOOK_UNDER_TEST=~/kits/my-problem/.claude/hooks/sandbox.py.new /usr/bin/python3 ~/kits/my-problem/tests/test_ext.py 2>&1 | tail -3
```

Both end with `OK`; if either fails, stop and tell the user, and delete the candidate. Then:

```sh
mv ~/kits/my-problem/.claude/hooks/sandbox.py.new ~/kits/my-problem/.claude/hooks/sandbox.py
```

If a settings template changed, fill the instance's settings again. The filled files carry the instance's absolute root and
your home directory in place of `@ROOT@` and `@HOME@`; from the instance's root, fill them as
[`bin/new-workspace`](../reference/tools/new-workspace.md) did:

```sh
sed -e "s|@ROOT@|$(pwd -P)|g" -e "s|@HOME@|$HOME|g" .claude/settings.template.json > .claude/settings.json
```

```sh
sed -e "s|@ROOT@|$(pwd -P)|g" -e "s|@HOME@|$HOME|g" .claude/worker-net.settings.template.json > .claude/worker-net.settings.json
```

### 4. Run the suites

```sh
for t in test_gate test_tools test_hook_gate test_ext; do /usr/bin/python3 ~/kits/my-problem/tests/$t.py 2>&1 | tail -3; done
```

```sh
~/kits/my-problem/bin/verify-data
```

Each suite ends with `OK`; compare the counts with the changelog's for the target version. `verify-data` reports no findings.
If anything fails, stop and tell the user. If the user refuses the upgrade, restore the replaced files from git
(`git -C ~/kits/my-problem restore -- <paths>`) and delete the added ones.

**Upgrading past `kit-v0.6.9`: move the locked directory out of the tree.** The instance's answer keys move from
`data/locked/` to a directory outside it, and `kit-env.json` records where. The hook refuses the orchestrator both the
locked directory and `kit-env.json`, so the user does it, at the terminal, after the suites pass. If the instance has no
`kit-env.json`, the user creates one holding only `{"locked_dir": "~/.local/state/crosslemma/my-problem/locked"}`;
otherwise the user adds that field to it. Then:

```sh
! mkdir -p ~/.local/state/crosslemma/my-problem && mv ~/kits/my-problem/data/locked ~/.local/state/crosslemma/my-problem/locked && chmod 700 ~/.local/state/crosslemma/my-problem/locked
```

Then `verify-data` again: it hashes the keys at their new place against their `SHA256SUMS`, and reports any file still
left in `data/locked/`. If git tracked `data/locked/`, the move shows as deletions; commit them (a plain `git add
data/locked` is allowed). The keys stay in the instance's git history: the move keeps a search of the working tree
out of them, not a search of the history. Since `kit-v0.6.26` the hook refuses a git command that would print them
from there (`git log -p`, `git show` of an old commit) unless it names other, plain paths.

**Upgrading past `kit-v0.6.20`: referee bindings and the rulings file.** A referee run counts only if
[`bin/new-run`](../reference/tools/new-run.md) bound it in `data/referee-bindings/<run>.json`; referee runs made before
that have no binding, and their verdicts stop counting (`bin/merge` lists them as invalid). Writing bindings for them by
hand would rest on their own `input/` files, which their workers could write, so whether to do that, or to referee those
claims again, is the user's call. A user's cross-family ruling left in a run as `RUN/.cross-family-referee` is no longer
read; the user moves it into `data/cross-family-rulings.json` (`{"<run>": "<family> <where ruled>"}`), which the hook
refuses the orchestrator to write. Two more changes a session in the instance will meet: a bare `git diff` is refused
(the ledger always has uncommitted lines; name the paths, or use `--stat`), and an instance with a formal-library module
needs `leanchecker` in its toolchain, which the axiom audit now runs.

### 5. Record it in `KIT-VERSION`

Add an `upgraded:` line: the date, the commit upgraded from, the tag and commit upgraded to, which session applied it, and
anything done by hand (for example, which files the user copied). The earlier lines stay.

### 6. Commit

Commit every replaced file and `KIT-VERSION` by explicit paths, with the message from a file, never everything at once
(→ **No `cd` in a compound command**).

### 7. If the settings changed: restart

Settings bind at session start, so if step 3 filled the settings again, end the session and open a fresh one in the
instance before any launch ([RULES.md §9](../../RULES.md#9-the-sandbox--enforced-not-convention)).

### 8. Canaries, if the hook changed

After any change to the hook, the settings, the agent definition or a harness note, run a canary on every route in
`.kit-routes`, each a new run with the canary template (`templates/runs/canary-BRIEF.md`, its `@…@` placeholders filled
for that run) and approved by the user, as in [A new instance](new-instance.md#3-run-the-canaries). Read each
`output/result.md`: **ESCAPES OR ORACLES FOUND** must say none, every **UNSEEN WRITES** line must be absent from the
host's record of the run (as [A new instance](new-instance.md#3-run-the-canaries) says), and Part A must say no.

### 9. Hand off

Record the upgrade in the instance's handoff: from and to, the files, what the user copied, the suites, the canaries
and their results.

## Related

- [A methods session](methods-session.md): how the change reached the kit in the first place.
- [Configuration](../reference/configuration.md): `KIT-VERSION`, `.kit-routes`, `.kit-lean`, `.kit-sage` and the settings.
