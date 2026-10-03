# Contributing

How a change to the kit lands: its tools, hook, tests, rules, templates and documentation alike.

## Report first

Open an issue that says what happened, what you expected, and the kit version (the tag, or `KIT-VERSION` in an
instance; a clone of the public copy has no tags, so give the top heading of `KIT-CHANGELOG.md`). A security problem goes through a private advisory instead: see [SECURITY.md](SECURITY.md).

A pull request is welcome as a proposal. Text and code from outside are outside input to the kit, so a maintainer
reads it, checks every claim in it against the code, and lands the change through a methods session as below.

## A change lands in a methods session

The kit changes its method only in a session given to that purpose, never in the middle of mathematics
(→ **Method changes never in a math session**; [RULES.md §7](RULES.md#7-standing-rules-that-keep-cycles-convergent)).
A change to `docs/` goes the same way: that is the maintainers' practice, by the user's ruling of 2026-10-01, not a
rule of `RULES.md`. In such a session, each change:

1. **A tool, hook or rule change has a test first, shown failing** on the code as it is. A fix whose test never failed
   has not shown it fixes anything. A documentation-only change has no such test; it passes the docs checker instead
   (step 4).
2. **Is made.** A change to the hook is made as a candidate copy, tested with
   `HOOK_UNDER_TEST=/path/to/candidate.py python3 tests/test_hook_gate.py`, then installed by an atomic rename.
3. **Passes the four suites:**
   ```sh
   for t in test_gate test_tools test_hook_gate test_ext; do python3 tests/$t.py; done
   ```
4. **Keeps the documentation whole.** If a tool's docstring, a lesson label, a ledger event or a hook refusal changed,
   regenerate the reference pages; then, for every change, run the checker:
   ```sh
   python3 scripts/docs/gen_reference.py
   python3 scripts/docs/check_docs.py
   ```
   The checker refuses a dangling link or lesson pointer, a lesson nothing points at, a tool without a reference page,
   a stale generated page, a changelog out of step with the tags (the newest heading may be untagged while you write
   it), and machine-specific text in a published file. In a clone of the public copy, which has no tags, the changelog
   check is skipped. The suites run the whole checker on the kit's own tree.
   [docs/conventions.md](docs/conventions.md) says how pages cite the rules.
5. **Is recorded**: a rule in [RULES.md](RULES.md) points at its lesson; a new lesson in [LESSONS.md](LESSONS.md) says
   the incident and what the rule prevents; [KIT-CHANGELOG.md](KIT-CHANGELOG.md) gets an entry under a new tag, saying
   whether tools, the hook or rules changed (an instance that takes a hook change runs canaries after).
6. **Is committed** by explicit paths, with the message from a file, and tagged `kit-vX.Y.Z`. No `cd` inside a
   compound command (→ **No `cd` in a compound command**).

## Instances take changes by upgrade

An instance never changes its own tools. It records the kit commit it was made or last upgraded at in `KIT-VERSION`;
a kit methods session hands it the diff from that commit, and a session opened in the instance applies it, runs the
suites, and runs a canary on each enabled route after any change to the hook, the settings, an agent definition, a
harness note or a route ([FLOW.md](FLOW.md#outside-steps--called-not-wired-in)). See
[upgrading an instance](docs/guides/upgrading-an-instance.md).

## Style

Code: the standard library only, and the style of the file you are in. Prose: plain sentences, the terms of the
[glossary](docs/reference/glossary.md), nothing machine-specific.
