# @SLUG@ — ⟨one-line name of the problem⟩

Written ⟨date⟩ for the workspace `@NAME@`. This workspace's own certified claims are in its `CLAIMS.md`; a
fact below is a claim of this workspace only where it cites a `C-NNN` of this workspace. Every other fact carries
a status mark saying where it comes from, and is not a claim of this workspace.

Status marks:
- **[CLASSICAL]** a textbook fact, cited, not derived or checked here.
- **[HELD]** this workspace holds the primary text (register `prior-art.md`; hash in `sources/SHA256SUMS`); it
  is unrefereed here, and what is reported is the source's own statement about itself.
- **[ACCOUNT]** known here only through an outside model's account of a source nobody here has opened.
- **[ELSEWHERE C-NNN]** a claim certified in another workspace made from this kit, at its commit ⟨sha⟩;
  **not re-certified here**.

**Problem type:** ⟨existence / decision / bound / classification / …⟩. **Status:** ⟨OPEN / SOLVED — a solved
problem is what a calibration ladder runs on⟩.

## 1. Statement

⟨The question, in one paragraph, with every quantifier and every side condition explicit. Say what is excluded
(zero, the trivial case, the degenerate case) and why. If there is a normalisation (primitive, reduced, up to
symmetry), say that the normalised and the general question are the same, or say exactly how they differ.⟩

## 2. Reformulation and notation

⟨The equivalent forms a solver may work in, each one a `[CLASSICAL]` fact or a claim id. Fix the notation the
whole workspace uses, so that a claim's English and an artifact's names mean the same thing. A reformulation a
worker might take as the problem must be marked as equivalent here, with the fact that makes it so.⟩

## 3. Target statements

⟨The two to four precise statements a result would be. Each: a name, the statement, what implies what among
them, and which is the weakest that would still count.⟩

## 4. Variants that exist (an argument must not exclude them)

⟨The near-solutions, the degenerate solutions, the solutions of the relaxed problem: the objects a wrong
nonexistence argument would "prove" impossible. Each with a witness a script can check. These are the first
controls of any search.⟩

## 5. Tests for any argument, each answered by naming a step

⟨For a nonexistence argument: which step fails on each variant of §4, by name. For a construction: which step
produces the witness. For a bound: where the constant enters. An argument that cannot name the step is not an
argument yet.⟩

## 6. Self-checks (before any search or enumeration result is believed)

⟨S1, S2, …: the known objects a search must re-find, the counts a script must reproduce, the symmetry it must
account for. Each one is its own `[VERIFIED]` claim before a search result is believed
(→ `LESSONS.md` "Re-find known objects before believing absence").⟩

## 7. What a result looks like here

⟨The expected shape: a rigorous negative, a sharpened statement, a mapped dead end, a bound. A proof is an
outlier. Say which region a fast result would be coming from.⟩

## 8. Formal library (only if the instance links one)

⟨Which library, at which commit; conventions for declarations, namespaces and the axioms allowed; how a claim
cites a declaration. Leave this section out if no library is linked.⟩
