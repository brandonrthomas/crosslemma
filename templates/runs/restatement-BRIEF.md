# Run ⟨NNN-slug⟩: restatement of ⟨SOURCE-RUN⟩/⟨cid⟩ with the wording its artifact certifies (orchestrator-assembled, no worker)

<!-- The form of an orchestrator-assembled restatement (a form the source used; LESSONS.md "A cross-family certify read" for
     its family). Use it when a referee found a claim's English wider than its artifact and gave, or implied, the sentence
     the artifact does certify, and the fix is wording only: the artifact, its deps, range, coverage, mutations, premises
     and command stay byte for byte. Make the run with `bin/new-run WORKSPACE ⟨slug⟩ --role other`, replace BRIEF.md with
     this, and then, with no worker:
       - copy the source run's artifact and every dep into output/ (byte copies, `cmp`-checked), same names;
       - write output/claims.json: the source claim unchanged except its `statement` (the user-approved sentence),
         any `silent_links` the new wording adds, and `supersedes` only if the source claim is on the record;
       - write output/result.md (a few lines: what changed, from which referee, by whose approval);
       - write RUN/.source-run holding the source run's name: the run's model family is the source run's, shown as
         "restated by the orchestrator"; a restatement of a run of the other family than the orchestrator's needs the
         user's ruling, recorded by the user in data/cross-family-rulings.json (SCHEMAS.md section 4);
       - write PROVENANCE.md (templates/runs/PROVENANCE.md);
     then bin/check, the referee runs its claim needs, and bin/close-run as for any run. The sentence is approved by the
     user AS TEXT before the run is made; nothing else changes without a new ruling. -->

Your run directory is ⟨absolute run dir⟩
Read only what is in it. Work alone.

## Task
No worker. One ⟨[TAG]⟩ claim on byte copies of run ⟨SOURCE-RUN⟩'s `⟨artifact path⟩` and its ⟨N⟩ deps. Run ⟨SOURCE-RUN⟩'s
⟨cid⟩ said ⟨what the old sentence asserted, in one line⟩; its `⟨question⟩` referee (run ⟨NNN⟩) found ⟨what the artifact
does not certify⟩, and gave the sentence the artifact supports. The English here is that sentence; the range, coverage,
mutations, premises and command are run ⟨SOURCE-RUN⟩'s claim ⟨cid⟩ unchanged⟨, with ⟨what⟩ added⟩. The sentence is approved
by the user as text (⟨date⟩, "⟨the user's words⟩"). No mathematics is done here. ⟨Nothing is superseded. | It
supersedes C-NNN.⟩

## Output
output/claims.json, output/result.md, and byte copies of ⟨every file, by name⟩
