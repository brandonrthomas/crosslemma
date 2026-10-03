# Provenance — run ⟨NNN-slug⟩

Written by `⟨session⟩` on ⟨date⟩ (⟨timezone⟩), after the run. Every file under `input/` is a byte copy
(`cmp`-checked) of a file named below; this file is the only text here written about them. **Nothing in this run
is a claim.**

## Why
⟨The operator's words that called for it, with the time; what form it follows (the template, or an earlier run of
this workspace by number); what the orchestrator read before writing the brief.⟩

## The run
- ⟨Launch: the exact `bin/run-external` line; the approval (digest, flags, how the user gave it); detached or
  not. Or: "no worker; the orchestrator assembled the files under `input/` and wrote nothing else".⟩
- ⟨End state: exit code, wall time, CPU time from `usage.json`; turns; tokens and cost as the launcher reported
  them, with the caveat that a launcher's cost figure for a routed model is not a meter.⟩
- ⟨Anything in `launch.err`.⟩

## The packet (`input/`, ⟨N⟩ files)
- ⟨Each file: what it is, where it was copied from, its sha256 prefix, and under what name if the name had to
  change (a record file may not keep its name inside a run's `input/`).⟩
- ⟨What is deliberately **not** in the packet, and why: the texts no worker may see, the ledger, the handoff,
  anything from another workspace.⟩
- ⟨Checked before launch: `bin/verify-data` clean; a script scan for keys, tokens and the user's email
  (counts only); redactions made, by file.⟩

## Limits
⟨What the auditor or reader was asked not to judge; what it could not see; whose tags its verdicts are (an
outside model's statements, uncertified here).⟩

## Outcome
⟨The output file; the number and kinds of findings; the verdict line verbatim; how it was shown to the operator
(whole, with the orchestrator's position marked as the interested party's); the user's ruling, quoted, with
the time; what was applied, item by item, and to which files; whether the corrected text was audited again.⟩

## What left this machine
⟨To which provider, through whose credential: the packet, named; everything the model wrote. What did not leave:
no key file, nothing from another workspace, no credentials. Whether a credential copy was inside the sandbox for
the run's duration.⟩
