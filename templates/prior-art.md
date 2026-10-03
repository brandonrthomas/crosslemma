# Prior art — @SLUG@ (register of @NAME@)

**Rule of this register:** it holds **only sources this workspace has itself opened**. An outside model's account
of a source is a search lead, not an entry. Leads are listed at the end, by pointer, and carry no weight until
someone here opens the source.

Entry ids are `PA-n`. Reading-status tags: `[SOURCE-READ]` the primary text is held under
`problems/@SLUG@/sources/` (hash in `sources/SHA256SUMS`) and was read whole by the session named in the entry;
`[SOURCE-READ: part]` says which part. Reading is not certifying: **no entry below has been refereed here**, and
"states", "claims" report the source's own words about itself. A search is a bounded negative: every entry and
every lead says what was searched and what was not reached, and **a blocked surface is never "not found"**
(→ `LESSONS.md` "Prior art before novelty").

Notation used in the entries: ⟨the workspace's notation, from `PROBLEM.md` §2⟩.

---

## PA-1 — ⟨Author (year), what it establishes in ten words⟩ `[SOURCE-READ]`
- ⟨Full citation; venue; DOI or URL; licence if held; refereed or not.⟩ Held: `sources/⟨file⟩` (sha256
  `⟨first 16 hex⟩…`), ⟨how it got here: uploaded by the user on ⟨date⟩ / fetched by an outside model in run
  ⟨NNN⟩⟩; read whole by `⟨session⟩` (⟨date⟩). Unrefereed here.
- States: ⟨the source's own statements, with its theorem numbers, in its own terms.⟩
- Bears on: ⟨which target statement of `PROBLEM.md` §3, and how; what is the same as an earlier entry and what is
  new relative to sources opened here. Mark the orchestrator's readings as such: "(orchestrator's reading,
  uncertified)".⟩
- Not in it: ⟨what a reader might expect and would not find.⟩

## Leads — outside accounts, NOT opened here; pointers only
- ⟨Run `workspace-1/runs/NNN-…/output/…` (⟨model⟩, ⟨date⟩): the sources it named, one line each. When one is
  opened here, say "Opened here since: … (PA-n)" on this bullet, so the lead and the entry stay tied.⟩
- ⟨Surfaces searched and not reached, by name (a database behind a paywall, a site that refused), so that a
  later session does not read the gap as absence.⟩
