# A methods session

This guide helps you change the method itself (a tool, the hook, a test, a template or a rule file) and land the change:
in the kit, with its tests shown failing first, the four suites, a changelog entry and a tag; and in an instance, where a
methods session applies a kit upgrade.

## What a methods session is

A session whose purpose the user has set as method work. Method changes never happen in a working session, the one
that runs workers and appends claims; there is no limit on how many changes a methods session makes or how often one is
held, and any exception to the separation is recorded as an exception, never as a precedent
([RULES.md §7](../../RULES.md#7-standing-rules-that-keep-cycles-convergent); → **Method changes never in a math session**).
The reason: a method changed under the pressure of a result drifts toward the result.

Changes land in **the kit** first. An instance takes them only as an upgrade, from a diff against its `KIT-VERSION`
([Upgrading an instance](upgrading-an-instance.md)), so that instances do not drift from the kit or from each other.

## In the kit

### 1. Open a session in the kit, and preflight

Open the session with the kit as its project directory (→ **A session works on the tree it was opened in**). The kit has no
ledger and no live hook: it holds its settings only as templates (→ **A scaffold ships its settings as a template, never
live**). Check, one command at a time:

```sh
git -C ~/kits/kit describe --tags --exact-match
git -C ~/kits/kit status --short
ls ~/kits/kit/.claude
```

The tag is the version you start from; the status is empty; `.claude` holds no `settings.json`. A clone of the public
copy has no tags (`scripts/export-public` makes one commit and no tag), so `describe` fails there: read the version from
the top heading of `KIT-CHANGELOG.md` instead. Then run the four suites
([Install](install.md#3-run-the-four-suites)) so you know they pass before you change anything.

### 2. The ruling

Write down what the user asked for, in their words, with the time, in the kit's handoff. A change goes only as far as
those words (→ **Never read a permission more widely than its words**). If a rule and the code disagree, the code is what
runs: say so, and fix one of them ([RULES.md](../../RULES.md), its opening paragraph).

### 3. A test that fails on the current code

Before changing a tool, write the test that the change must pass, and run it against the code as it stands:

```sh
/usr/bin/python3 ~/kits/kit/tests/test_tools.py
```

Show the failure: it is the evidence that the test detects the defect, and the changelog entry will say "new tests fail on
the previous code". A test that passes before the change certifies nothing about it
(→ **Certify with artifacts wherever an artifact can**). Put a tool's test in
`tests/test_tools.py`, the approval gate's in `tests/test_gate.py`, the hook's in `tests/test_hook_gate.py`, and anything
that runs the real sandbox in `tests/test_ext.py`. Tests run on fixture roots, never on a real ledger, and always on
`/usr/bin/python3` (→ **Every tool, hook and test runs on `/usr/bin/python3`**).

### 4. Make the change

- **A tool.** Its docstring is its usage text and the source of its reference page, so change both together.
- **The hook** (`.claude/hooks/sandbox.py`). Change a copy, test the copy, then install it
  (→ **Change the hook only as a tested candidate**):

  ```sh
  cp ~/kits/kit/.claude/hooks/sandbox.py /tmp/hook-candidate.py
  ```

  Edit `/tmp/hook-candidate.py`, then run the hook suite against it; its golden replay checks that the worker branch still
  decides every recorded input exactly as before:

  ```sh
  HOOK_UNDER_TEST=/tmp/hook-candidate.py /usr/bin/python3 ~/kits/kit/tests/test_hook_gate.py
  ```

  `tests/test_ext.py` reads `HOOK_UNDER_TEST` too (its sandbox tests import the hook), so run it against the candidate as
  well:

  ```sh
  HOOK_UNDER_TEST=/tmp/hook-candidate.py /usr/bin/python3 ~/kits/kit/tests/test_ext.py
  ```

  Install it by a copy to a new name and a rename, so no call sees a half-written hook:

  ```sh
  cp /tmp/hook-candidate.py ~/kits/kit/.claude/hooks/sandbox.py.new
  ```

  ```sh
  mv ~/kits/kit/.claude/hooks/sandbox.py.new ~/kits/kit/.claude/hooks/sandbox.py
  ```

- **The sandbox.** Test it for real, with fake binaries in `tests/test_ext.py`, rather than by reading its command line
  (→ **Fake binaries test the real sandbox**).
- **A rule.** A rule in `RULES.md` carries a pointer to its lesson (`→ **label**`), and the lesson in `LESSONS.md` names the
  incident that made it. A new rule gets both.

### 5. The four suites, and the docs

```sh
for t in test_gate test_tools test_hook_gate test_ext; do /usr/bin/python3 ~/kits/kit/tests/$t.py 2>&1 | tail -3; done
```

Every suite ends with `OK`. Note the four counts for the changelog.

If a docstring, a lesson label, a ledger event or a hook refusal changed, regenerate the reference pages and check the
documentation ([how the docs are written](../conventions.md)):

```sh
/usr/bin/python3 ~/kits/kit/scripts/docs/gen_reference.py
```

```sh
/usr/bin/python3 ~/kits/kit/scripts/docs/check_docs.py
```

The checker prints nothing and exits 0 when every link, lesson pointer, generated page, tag and published file is in order.
Its changelog check compares the `KIT-CHANGELOG.md` headings with the repository's `kit-v*` tags; the newest heading
may be untagged, since you write it before you tag, and in a clone of the public copy, which has no tags, the check is
skipped. The suites run the whole checker on the kit's own tree (`tests/test_tools.py`).

### 6. The changelog entry

Add an entry at the top of `KIT-CHANGELOG.md`, headed with the new tag, the date and a title:

```text
## kit-vX.Y.Z — YYYY-MM-DD — what changed, in a few words
```

Under it: on whose word; whether **the hook changed** or **tools changed**; each change, one line each; "New tests fail on
the previous code. Suites a/b/c/d." with the four counts; and what an instance taking this version must do (for example
"An instance taking this changes its hook: canaries on its routes after"). One entry per version an instance can be made
at.

### 7. Commit and tag

Commit by explicit paths, with the message from a file (→ **No `cd` in a compound command**):

```sh
git -C ~/kits/kit add -- bin/check tests/test_tools.py KIT-CHANGELOG.md
```

```sh
git -C ~/kits/kit commit -F /tmp/kit-commit-msg.txt
```

Then tag the commit with the version the changelog names:

```sh
git -C ~/kits/kit tag kit-vX.Y.Z
```

The docs checker refuses a tag with no changelog heading and a heading with no tag, but the newest.
[`bin/new-workspace`](../reference/tools/new-workspace.md) refuses a kit with uncommitted changes in its tools, hook, tests,
templates and rule files, so new instances are made at a commit. Its check does not cover `.gitignore`, which it also
copies: commit that too before making an instance.

### 8. Hand off

Record the change in the kit's handoff: the ruling, the files, the suites, and which instances it concerns. If an instance
should take it, write the diff and an opening prompt for a session in that instance
([Upgrading an instance](upgrading-an-instance.md#part-1-in-a-session-opened-in-the-kit-the-diff)).

## In an instance

A methods session in an instance applies a kit upgrade, from the diff and opening prompt a kit methods session handed over
([Upgrading an instance](upgrading-an-instance.md#part-2-in-a-session-opened-in-the-instance-applying-it)). In short:

- nothing in flight: no worker, no queue (from the unit list), and no approval waiting (the user's check: the hook
  keeps the orchestrator out of the approvals directory);
- the ledger's pending lines committed first, alone;
- the files replaced from the target tag, the hook last, tested as a candidate and renamed into place;
- the four suites run in the instance;
- `KIT-VERSION` given an `upgraded:` line; a commit by explicit paths;
- after a change to the hook, the settings, the agent definition or a harness note, a canary on every enabled route
  ([FLOW.md, outside steps](../../FLOW.md#outside-steps--called-not-wired-in); → **Settings bind at session start**).

If the instance needs a change the kit does not have, put it to the user as a change to the kit, so that the instance
takes it back as an upgrade rather than drifting from the kit.

## Related

- [Lessons](../../LESSONS.md): the incident behind every rule, which is what a methods session is usually answering.
- [Configuration](../reference/configuration.md): the settings templates and the files an instance records.
