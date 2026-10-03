/-
The kit's axiom audit (bin/check, P-12: the code audit of 2026-10-02). bin/check runs it in a worker's sandbox where no
artifact code runs: `lean --run KitAudit.lean NONCE MODULE DECL...`, with MODULE the artifact compiled by an earlier
sandbox call and copied by the host into a fresh directory first on LEAN_PATH, after `leanchecker MODULE` replayed its
declarations through the kernel. The artifact's own syntax never reaches this file (it is not imported here, only
loaded as data, with no initializer run), and no precomputed axiom list is read: every constant is walked.
Prints one line per declaration: "NONCE AXIOMS decl [a, b]" or "NONCE MISSING decl".
-/
import Lean
open Lean

/-- Every axiom a constant rests on, by walking the kernel's constants: no precomputed list is read (bin/check, P-12). -/
partial def walk (env : Environment) (c : Name) (seen : NameSet) (axs : NameSet) : NameSet × NameSet := Id.run do
  if seen.contains c then return (seen, axs)
  let mut seen := seen.insert c
  let mut axs := axs
  let some ci := env.find? c | return (seen, axs)
  if let .axiomInfo _ := ci then axs := axs.insert c
  let mut used := ci.type.getUsedConstants
  if let some v := ci.value? (allowOpaque := true) then used := used ++ v.getUsedConstants
  if let .inductInfo v := ci then used := used ++ v.ctors.toArray
  for u in used do
    (seen, axs) := walk env u seen axs
  return (seen, axs)

def main (args : List String) : IO UInt32 := do
  match args with
  | nonce :: modName :: decls =>
    initSearchPath (← findSysroot)
    let env ← importModules #[{ module := modName.toName }] {} (trustLevel := 0)
    for d in decls do
      let n := d.toName
      if (env.find? n).isNone then
        IO.println s!"{nonce} MISSING {d}"
      else
        let (_, axs) := walk env n {} {}
        IO.println s!"{nonce} AXIOMS {d} [{String.intercalate ", " (axs.toList.map toString)}]"
    return 0
  | _ => return 2
