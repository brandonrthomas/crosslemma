# How these docs are written

For anyone, human or agent, who writes or changes a page under `docs/`. The checker
(`python3 scripts/docs/check_docs.py`) enforces the parts marked **checked**.

## Two kinds of page

- **Normative**: [`RULES.md`](../RULES.md), [`SCHEMAS.md`](../SCHEMAS.md), the tools' own docstrings, and the code. They
  say what the kit does and refuses. [`LESSONS.md`](../LESSONS.md) says why: each rule's incident.
- **Explanatory**: everything under `docs/`. A page explains and shows; it never adds a rule. Where a page states what
  the kit requires, it cites the rule rather than restating it in new words, because two wordings of one rule drift
  apart.

If a page and a normative file disagree, the normative file is right and the page has a bug.

## Citing

- **A rule**: link its section, e.g. `[RULES.md §6](../RULES.md#6-approvals--the-gate)`. Anchors are GitHub's
  heading slugs. **Checked**: the file and the heading exist.
- **A lesson**: `→ **Label**`, as `RULES.md` does, with the lesson's bold label in full or its opening words.
  **Checked**: it names a lesson.
- **A tool**: link its generated page, e.g. `[bin/new-run](reference/tools/new-run.md)`.
- **Any other file**: a relative link. **Checked**: it exists.

## Generated pages

Everything in `docs/reference/tools/`, plus `docs/reference/hook-refusals.md` and `docs/reference/ledger-events.md`,
is written by `scripts/docs/gen_reference.py` from the code. Never edit one; change the docstring or code and run the
generator. **Checked**: each matches what the generator writes now.

## Names and what a page never contains

- The project is **crosslemma**; in running prose it is "the kit". An instance is "an instance"; the person who
  approves is "the user", an agent the user designates to direct work is "the operator agent", and "the operator"
  is either of them (`RULES.md` "Words").
- The kit was derived from **the source workspace**: a research project on whether a 3×3 magic square of nine
  distinct perfect squares exists. Its incidents are cited as "the source's run N".
- No absolute home paths, hostnames, private domains, local workspace names or session names. Examples use
  placeholders such as `~/kits/my-problem`. **Checked** in every published file.
- No credentials, ever, including in examples.

Use the terms in the [glossary](reference/glossary.md) as defined there.

## Style

Each page opens with one sentence saying what question it answers. Then short sections, plain sentences, examples
that run as written. Guides use "you". Diagrams are Mermaid, which GitHub renders.

## Pages must be reachable

Every page under `docs/` is linked from [the index](index.md), directly or through a page it links. **Checked**.

## Who reads these

Humans reading on GitHub, and agents working in the kit: an orchestrator or a methods session may read any page.
A worker never does: a worker sees its run's packet and nothing else (→ **First `Read` binds a worker to one run
directory**).
