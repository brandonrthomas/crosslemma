"""Shared helpers for the orchestrator tools (bin/check, close-run, merge, ledger-claims, annotate-claim, claim-deps,
claims-extract, new-run, lint-brief, verify-data, check-env, and _ext.py, _packet.py).

What lives here: the ledger writer (which refuses a tree with no LEDGER.log), the worker sandbox the checker runs
artifacts in, the formal-library and SageMath state, the claims record's entries, notes and dependency graph, the
referee files and their validation, and the earned tag with its two cross-family needs (the `certify` hold and the
`sentence` read) and the models a run was answered by (RULES.md §7, §8; SCHEMAS.md §4).

Not a worker tool. Nothing here reads data/locked/ contents; verify-data hashes them only.
The project root is the parent of the directory holding this file, so a tool works from any cwd;
KIT_ROOT overrides it so the tools can be tested against a fixture tree.
"""
import glob
import hashlib
import importlib.machinery
import importlib.util
import json
import os
import re
import stat
import subprocess
import sys
import time

REAL_ROOT = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
ROOT = os.path.realpath(os.environ.get("KIT_ROOT", REAL_ROOT))
LEDGER = os.path.join(ROOT, "LEDGER.log")
CLAIMS_MD = os.path.join(ROOT, "CLAIMS.md")
# The locked directory (answer keys, label maps): kit-env.json `locked_dir`, outside the tree since kit-v0.6.9 (pending
# item P-9); <root>/data/locked for an instance without the field. bin/_env.py is stdlib only and imports nothing here.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _env as _E
LOCKED = _E.load(ROOT).locked_dir
# P-12 (a medium of the code audit): with kit-env.json unreadable, or its locked_dir refused, LOCKED falls back to
# <root>/data/locked while the keys may lie at the default place; every place the locked data can be is guarded.
LOCKED_GUARDED = sorted({LOCKED, os.path.join(ROOT, "data", "locked"), _E.default_locked_dir(ROOT)})


def in_locked(path):
    return any(inside(path, d) for d in LOCKED_GUARDED)
PROBLEMS = os.path.join(ROOT, "problems")
HOOK = os.path.join(REAL_ROOT, ".claude", "hooks", "sandbox.py")

# Claim-form rules live in ONE file, bin/validate-claims (stdlib only; copied into every solver run's
# input/ so the worker runs the same code before finishing — LESSONS.md "`bin/validate-claims` is one piece of code", 2026-09-16).
_spec = importlib.util.spec_from_loader("validate_claims", importlib.machinery.SourceFileLoader(
    "validate_claims", os.path.join(os.path.dirname(os.path.abspath(__file__)), "validate-claims")))
V = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(V)
TAGS, ARTIFACT_TYPES, BANNED, TAG_RE, LOCAL_ID_RE, TAG_RULES = V.TAGS, V.ARTIFACT_TYPES, V.BANNED, V.TAG_RE, V.LOCAL_ID_RE, V.TAG_RULES
validate_claims_doc, validate_claim, validate_mutations, banned_scan = V.validate_claims_doc, V.validate_claim, V.validate_mutations, V.banned_scan

# Schema ids: one prefix for the whole kit. An instance keeps them, so records stay readable across
# instances. Changing one is a method change (SCHEMAS.md).
SCHEMA_PREFIX = "kit"
CLAIMS_SCHEMA = SCHEMA_PREFIX + "/claims/2"   # claims/1 still accepted (bin/validate-claims)
REFEREE_SCHEMA = SCHEMA_PREFIX + "/referee/1"
CHECK_SCHEMA = SCHEMA_PREFIX + "/check/2"
APPROVAL_SCHEMA = SCHEMA_PREFIX + "/approval/1"

REFEREE_VERDICTS = ("holds", "falsified", "gap", "unverifiable")
CLEAN_AXIOMS = {"propext", "Classical.choice", "Quot.sound"}
NATIVE_AXIOM = "Lean.ofReduceBool"  # Lean ≤4.2x; 4.32 emits <decl>._native.native_decide.ax_N_M per declaration


def is_native_axiom(ax):
    return ax == NATIVE_AXIOM or ".native_decide." in ax or ax.endswith("native_decide")


RUN_NAME_RE = re.compile(r"^[0-9]{3}-[a-z0-9][a-z0-9-]*$")
FORBIDDEN_INPUT_NAMES = {"LEDGER.log", "CLAIMS.md", "HANDOFF.md", "RULES.md", "FLOW.md",
                         "ORCHESTRATOR.md", "CLAUDE.md", "BRIEF.md"}


def now():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def die(msg, code=2):
    print(f"error: {msg}", file=sys.stderr)
    sys.exit(code)


CLAIMS_LOCK = os.path.join(ROOT, ".claude", "state", "claims.lock")


def claims_lock():
    """Held for the whole of a CLAIMS.md append (bin/ledger-claims, bin/annotate-claim), from reading the next id to the
    write (P-12: two appends at once could take the same C-NNN). Released when the process ends."""
    import fcntl
    os.makedirs(os.path.dirname(CLAIMS_LOCK), exist_ok=True)
    f = open(CLAIMS_LOCK, "a")
    fcntl.flock(f, fcntl.LOCK_EX)
    return f


def append_ledger(path, line):
    """Append to an existing LEDGER.log; never create one. A tree without a ledger is not an instance (the kit itself, or a
    command that ran in the wrong directory), and creating one there would hide that (LESSONS.md "A session works on the
    tree it was opened in")."""
    try:
        fd = os.open(path, os.O_WRONLY | os.O_APPEND)
    except FileNotFoundError:
        sys.exit(f"ledger: no LEDGER.log at {os.path.dirname(path)}: this tree is not an instance (the kit, or a command run "
                 "in the wrong directory); nothing appended")
    with os.fdopen(fd, "a") as f:
        f.write(line)


def ledger(run, event, detail):
    detail = " ".join(str(detail).split())
    append_ledger(LEDGER, f"{now()} | orchestrator | {run or '-'} | {event} | {detail[:400]}\n")


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


# A formal-library module is OPTIONAL: an instance links one or has none. Every library rule is
# conditional on the directory existing, so a tree without one is not a finding.
LEAN_DIR = os.path.join(ROOT, "lean")


def has_lean():
    """The one definition of "this instance links a library module": the directory is there."""
    return os.path.isdir(LEAN_DIR)


def lean_declared():
    """An instance that linked a module wrote <root>/.kit-lean. Its presence is what tells a vanished
    lean/ (a finding) apart from an instance that never had one (not a finding)."""
    return os.path.isfile(os.path.join(ROOT, ".kit-lean"))


def lean_toolchain():
    """Where the module's toolchain lives, from <root>/.kit-lean, else the default. From a FILE and never
    from the environment: a variable the orchestrator can set would add a mount inside the sandbox."""
    try:
        with open(os.path.join(ROOT, ".kit-lean")) as f:
            p = f.read().strip()
        if p:
            return os.path.expanduser(p)
    except OSError:
        pass
    return os.path.expanduser("~/.elan")


def sage_env():
    """The optional computer-algebra module (LESSONS.md "Computer algebra is an optional module, and its results need a certificate"): a SageMath conda environment
    named in <root>/.kit-sage by bin/new-workspace --sage, else None. From a FILE and never from the environment, like
    the library's toolchain: a variable the orchestrator can set would add a mount inside the sandbox."""
    try:
        with open(os.path.join(ROOT, ".kit-sage")) as f:
            p = f.read().strip()
        return os.path.expanduser(p) if p else None
    except OSError:
        return None


def has_sage():
    """The module is mounted for workers when .kit-sage names an environment that has bin/sage."""
    e = sage_env()
    return bool(e) and os.path.isfile(os.path.join(e, "bin", "sage"))


def sage_drift():
    """A declared module that is not there is a finding, as a vanished library is: a package-backed claim can no longer
    be re-checked. Never having one is not a finding."""
    if sage_env() and not has_sage():
        return [f"the computer-algebra module is missing: .kit-sage names {sage_env()}, which has no bin/sage (claims "
                "that rest on it cannot be re-checked; fix .kit-sage or reinstall the environment)"]
    return []


def lean_files():
    """Every Lean source under lean/, excluding the build tree, as paths relative to lean/."""
    out = []
    for dp, dn, fn in os.walk(LEAN_DIR):
        dn[:] = [d for d in dn if d not in (".lake", "__pycache__")]
        for f in fn:
            if f.endswith(".lean"):
                out.append(os.path.relpath(os.path.join(dp, f), LEAN_DIR))
    return sorted(out)


def library_lines():
    """`<sha256>  <relpath>` for every Lean source, sorted by path: the master list's format."""
    return [f"{sha256(os.path.join(LEAN_DIR, rel))}  {rel}" for rel in lean_files()]


def library_state():
    """What the shared formal library was when this ran. Recorded per run by bin/check and compared
    against lean.SHA256SUMS by bin/verify-data, so one function decides both. With no library linked:
    files 0, digest None, which is what such a run ran against."""
    if not has_lean():
        return {"root": None, "files": 0, "digest": None}
    lines = library_lines()
    h = hashlib.sha256(("\n".join(lines) + "\n").encode()).hexdigest()
    return {"root": "lean", "files": len(lines), "digest": h}


def library_manifest_path():
    """The instance's own record of the library it accepted: beside the link, never inside the linked module,
    which may be shared between instances or read-only."""
    return os.path.join(ROOT, "lean.SHA256SUMS")


def library_drift():
    """Findings comparing lean.SHA256SUMS against the files on disk. Empty list = no drift."""
    if not has_lean():
        # A declared module that is not there is exactly what this check exists to catch.
        return ([f"lean/ is missing, but {os.path.join('.kit-lean')} declares a library module: the evidence "
                 f"under every claim that imports it is gone (restore it, or remove .kit-lean)"]
                if lean_declared() else [])
    if not os.path.isdir(lean_toolchain()):
        return [f"the library module's toolchain is missing: {lean_toolchain()} (claims cannot be re-checked "
                f"and workers get no toolchain; fix .kit-lean or install it)"]
    mp = library_manifest_path()
    if not os.path.isfile(mp):
        return ["lean.SHA256SUMS missing (the Lean library has no master list; create it with: "
                "bin/verify-data --write-lean-manifest)"]
    want = {}
    for line in open(mp):
        parts = line.split(None, 1)
        if len(parts) == 2:
            want[parts[1].strip()] = parts[0]
    got = {l.split(None, 1)[1].strip(): l.split(None, 1)[0] for l in library_lines()}
    f = []
    for rel in sorted(set(want) | set(got)):
        if rel not in got:
            f.append(f"lean.SHA256SUMS lists a missing file: lean/{rel}")
        elif rel not in want:
            f.append(f"Lean file not in lean.SHA256SUMS: lean/{rel}")
        elif want[rel] != got[rel]:
            f.append(f"LEAN LIBRARY CHANGED: lean/{rel} (claims checked before this edit recorded the old state)")
    return f


def run_dirs():
    return sorted(os.path.realpath(d) for d in glob.glob(os.path.join(ROOT, "workspace-*", "runs", "*"))
                  if os.path.isdir(d))


def resolve_run(arg):
    """Accept an absolute path, a path relative to ROOT, or a bare run name (must be unique)."""
    cands = [os.path.realpath(arg), os.path.realpath(os.path.join(ROOT, arg))]
    for c in cands:
        if os.path.isdir(c) and c in run_dirs():
            return c
    hits = [d for d in run_dirs() if os.path.basename(d) == arg]
    if len(hits) == 1:
        return hits[0]
    if len(hits) > 1:
        die(f"run name {arg} is ambiguous across workspaces: {hits}")
    die(f"no run directory matches {arg!r}")


def inside(path, base):
    rp, rb = os.path.realpath(path), os.path.realpath(base)
    return rp == rb or rp.startswith(rb + os.sep)


def load_json(path, what):
    try:
        with open(path) as f:
            return json.load(f)
    except FileNotFoundError:
        die(f"{what} missing: {path}")
    except json.JSONDecodeError as e:
        die(f"{what} is not valid JSON ({path}): {e}")


def write_in_run(rd, rel, data, append=False):
    """Write RD/REL from the host without following a symlink anywhere below RD (P-12 C2). A worker can plant a symlink
    at any name in its run directory, and a host write that followed one would reach any file the user can write. Each
    directory below RD is opened with O_NOFOLLOW (made when missing); the file goes to a fresh name and is renamed over
    REL, which replaces a symlink there instead of following it. With append=True the file itself is opened O_NOFOLLOW.
    RD is the run directory's real path; its parents are not the worker's to write."""
    if isinstance(data, str):
        data = data.encode()
    parts = [p for p in rel.split("/") if p]
    if not parts or any(p in (".", "..") for p in parts):
        raise ValueError(f"write_in_run: bad relative path {rel!r}")
    fl = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    dfd = os.open(rd, fl)
    try:
        for p in parts[:-1]:
            try:
                os.mkdir(p, 0o755, dir_fd=dfd)
            except FileExistsError:
                pass
            nfd = os.open(p, fl, dir_fd=dfd)
            os.close(dfd)
            dfd = nfd
        name = parts[-1]
        if append:
            fd = os.open(name, os.O_WRONLY | os.O_APPEND | os.O_CREAT | os.O_NOFOLLOW, 0o644, dir_fd=dfd)
            with os.fdopen(fd, "ab") as f:
                f.write(data)
            return
        tmp = f".{name}.{os.getpid()}.{os.urandom(4).hex()}.tmp"
        fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o644, dir_fd=dfd)
        try:
            with os.fdopen(fd, "wb") as f:
                f.write(data)
            os.replace(tmp, name, src_dir_fd=dfd, dst_dir_fd=dfd)
        except BaseException:
            try:
                os.unlink(tmp, dir_fd=dfd)
            except OSError:
                pass
            raise
    finally:
        os.close(dfd)


def read_in_run(rd, rel):
    """The bytes of RD/REL, read without following a symlink anywhere below RD, from a regular file only (P-12)."""
    parts = [p for p in rel.split("/") if p]
    if not parts or any(p in (".", "..") for p in parts):
        raise ValueError(f"read_in_run: bad relative path {rel!r}")
    fl = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    dfd = os.open(rd, fl)
    try:
        for p in parts[:-1]:
            nfd = os.open(p, fl, dir_fd=dfd)
            os.close(dfd)
            dfd = nfd
        fd = os.open(parts[-1], os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=dfd)
        with os.fdopen(fd, "rb") as f:
            if not stat.S_ISREG(os.fstat(fd).st_mode):
                raise OSError(f"not a regular file: {rel}")
            return f.read()
    finally:
        os.close(dfd)


def write_json(path, obj):
    d, n = os.path.split(os.path.abspath(path))
    write_in_run(os.path.realpath(d), n, json.dumps(obj, indent=2, sort_keys=False) + "\n")   # a link at the name is replaced, never followed


def _bwrap_command():
    spec = importlib.util.spec_from_file_location("sandbox_hook", HOOK)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.bwrap_command


def sandbox_run(rd, cmd, timeout):
    """Run `cmd` inside the worker sandbox for run dir `rd` (same bwrap the hook builds)."""
    full = _bwrap_command()(rd, cmd)
    try:
        p = subprocess.run(full, shell=True, capture_output=True, text=True, timeout=timeout)
        return p.returncode, p.stdout, p.stderr, False
    except subprocess.TimeoutExpired as e:
        return None, (e.stdout or "") if isinstance(e.stdout, str) else "", (e.stderr or "") if isinstance(e.stderr, str) else "", True


ENTRY_RE = re.compile(r"^## (C-\d+)\s+\[([A-Z]+)\]\s+(\S+)\s+run (\S+)/(\S+)", re.M)
NOTE_RE = re.compile(r"^## (C-\d+)-note\s+(\S+)\s+(.*\S)\s*$", re.M)


def _claims_text():
    try:
        with open(CLAIMS_MD) as f:
            return f.read()
    except FileNotFoundError:
        return ""


def global_entries():
    """C-NNN -> {tag, date, run, cid} for every entry header in CLAIMS.md."""
    return {m.group(1): {"tag": m.group(2), "date": m.group(3), "run": m.group(4), "cid": m.group(5)}
            for m in ENTRY_RE.finditer(_claims_text())}


def global_ids():
    """(run, local id) -> C-NNN."""
    return {(v["run"], v["cid"]): k for k, v in global_entries().items()}


def claim_notes():
    """C-NNN -> ["<date>  <text>", ...] from bin/annotate-claim entries (LESSONS.md "A changed novelty or an audit finding")."""
    out = {}
    for m in NOTE_RE.finditer(_claims_text()):
        out.setdefault(m.group(1), []).append(f"{m.group(2)}  {m.group(3)}")
    return out


def notes_for(run, cid, supersedes=None):
    """Lines to show for a local claim: notes on its own ledgered id (if any) and on the id it supersedes."""
    notes, gids, lines = claim_notes(), global_ids(), []
    own = gids.get((run, cid))
    if own and notes.get(own):
        lines += [f"note on {own} (this claim, already ledgered): {n}" for n in notes[own]]
    if supersedes and notes.get(supersedes):
        lines += [f"note on {supersedes} (superseded by this claim): {n}" for n in notes[supersedes]]
    return lines


BINDINGS = os.path.join(ROOT, "data", "referee-bindings")
RULINGS = os.path.join(ROOT, "data", "cross-family-rulings.json")
BINDING_SCHEMA = SCHEMA_PREFIX + "/referee-binding/1"


def binding_path(name):
    return os.path.join(BINDINGS, name + ".json")


def claim_digest(c):
    """The claim as the solver wrote it, as bytes: a verdict is on this claim, not only on its artifact (P-12)."""
    return hashlib.sha256(json.dumps(c, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()


def write_binding(name, question, source_run, claim, artifact_sha256, deps_sha256, claim_sha256=None):
    """bin/new-run's record of a referee run, outside every run directory (P-12 C3): which claim it reads, on which
    question, and the bytes it was given. No worker can write it; the earned tag reads the referee's question and the
    bytes it saw from here, never from the run."""
    p = binding_path(name)
    if os.path.lexists(p):
        die(f"a binding for {name} already exists: {os.path.relpath(p, ROOT)}")
    os.makedirs(BINDINGS, exist_ok=True)
    write_json(p, {"schema": BINDING_SCHEMA, "referee_run": name, "question": question, "source_run": source_run,
                   "claim": claim, "artifact_sha256": artifact_sha256, "deps_sha256": deps_sha256 or {},
                   "claim_sha256": claim_sha256})


def read_binding(name):
    try:
        with open(binding_path(name)) as f:
            b = json.load(f)
    except (OSError, ValueError):
        return None
    ok = (isinstance(b, dict) and b.get("schema") == BINDING_SCHEMA and b.get("referee_run") == name
          and all(isinstance(b.get(k), str) for k in ("question", "source_run", "claim")))
    return b if ok else None


def referee_files():
    """Every run's output/referee.json, keyed by (solver run name, claim id). A referee run is one bin/new-run bound in
    data/referee-bindings/<run>.json (P-12 C3): its question, its claim and the bytes it was given come from there. An
    output/referee.json in a run with no binding is recorded as an error under the claim it names, and never counts."""
    out = {}
    for rd in run_dirs():
        p = os.path.join(rd, "output", "referee.json")
        if not os.path.isfile(p):
            continue
        name = os.path.basename(rd)
        b = read_binding(name)
        rec = {"referee_run": name, "path": os.path.relpath(p, ROOT), "artifact_sha256": None}
        try:
            with open(p) as f:
                doc = json.load(f)
        except Exception as e:
            doc, errs = None, [f"unreadable: {e}"]
        else:
            errs = validate_referee(doc)
        named = (str(doc.get("run")), str(doc.get("claim"))) if isinstance(doc, dict) else ("?", "?")
        if b is None:
            errs.insert(0, f"no binding in {os.path.relpath(binding_path(name), ROOT)}: not a referee run bin/new-run made "
                           "(or one made before kit-v0.6.20); it does not count")
            key = named
        else:
            key = (b["source_run"], b["claim"])
            rec.update(question=b["question"], artifact_sha256=b.get("artifact_sha256"), claim_sha256=b.get("claim_sha256"),
                       deps_sha256=b.get("deps_sha256") or {}, binding=os.path.relpath(binding_path(name), ROOT))
            if isinstance(doc, dict):   # file under the run/claim the referee was given; a wrong run/claim field is an error
                if doc.get("run") != b["source_run"]:
                    errs.append(f"run field {doc.get('run')!r} must be {b['source_run']!r} (the run the claim came from)")
                if doc.get("claim") != b["claim"]:
                    errs.append(f"claim field {doc.get('claim')!r} must be {b['claim']!r}")
        if errs:
            rec["error"] = "; ".join(errs)
        else:
            rec.update(verdict=doc["verdict"], pointer=doc["pointer"], note=doc.get("note", ""))
        out.setdefault(key, []).append(rec)
    return out


def validate_referee(doc):
    e = []
    if not isinstance(doc, dict):
        return ["referee.json top level is not an object"]
    if doc.get("schema") != REFEREE_SCHEMA:
        e.append(f"schema {doc.get('schema')!r} != {REFEREE_SCHEMA!r}")
    if not isinstance(doc.get("run"), str):
        e.append("run missing")
    if not isinstance(doc.get("claim"), str):
        e.append("claim missing")
    if doc.get("verdict") not in REFEREE_VERDICTS:
        e.append(f"verdict {doc.get('verdict')!r} not in {REFEREE_VERDICTS}")
    ptr = doc.get("pointer")
    if not isinstance(ptr, str) or not ptr.strip():
        e.append("pointer missing (file:line or decl name or 'n/a')")
    note = doc.get("note", "")
    if not isinstance(note, str):
        e.append("note must be a string")
    else:
        lines = [l for l in note.splitlines() if l.strip()]
        if len(lines) > 3:
            e.append(f"note has {len(lines)} lines; limit 3")
        if len(note) > 600:
            e.append(f"note is {len(note)} chars; limit 600")
    extra = set(doc) - {"schema", "run", "claim", "verdict", "pointer", "note"}
    if extra:
        e.append(f"unexpected fields {sorted(extra)} (referee output is typed and bounded)")
    return e


def sentence_need(doc, claim, live):
    """(required, holds) for the sentence read (LESSONS.md "A sentence referee reads every script claim"): a VERIFIED or NUMERIC claim of a
    kit/claims/2 document earns its tag only with a live `sentence` referee that holds. Older documents: not required."""
    required = (doc or {}).get("schema") == V.SCHEMA and (claim or {}).get("tag") in ("VERIFIED", "NUMERIC")
    holds = any(r.get("question") == "sentence" and r.get("verdict") == "holds" for r in live)
    return required, holds


# LESSONS.md "A cross-family certify read" (the source's method change 59): the model family of a producer and its referees.
ORCHESTRATOR_FAMILY = "Anthropic"   # the orchestrator is a Claude Code session: a restatement it assembled is partly its words
_MODEL_RE = re.compile(r"--model\s+(\S+)")


def model_family(model):
    """The model family of a model id, from the instance's environment file's table (bin/_env.py: the built-in Anthropic
    and OpenAI words, plus any family the user added), or "unknown"."""
    import _env
    return _env.model_family(model, _env.load(ROOT)) or "unknown"


def run_family(rd, _depth=0):
    """{family, model, how, restated} of a run: from the --model of its launch (the last one in RUN/time.log, which holds
    the exact command on every route), or, for a run with no launch (a restatement the orchestrator assembled), from the run
    named in RUN/.source-run, which the orchestrator writes when it assembles the run. When the run's own record names the
    models that answered (models_seen), they decide: one family, the same as the approved model's (or the approved model's
    family unknown), is that family; another family, or two, is "unknown", which needs the user's ruling."""
    try:
        with open(os.path.join(rd, "time.log"), errors="replace") as f:
            models = _MODEL_RE.findall(f.read())
    except OSError:
        models = []
    if models:
        approved = models[-1].strip("'\"")
        fam = model_family(approved)
        answered = sorted(models_seen(rd)[0])   # kit-v0.4.1: the models that answered decide, when the record has them
        if answered:
            seen = {model_family(m) for m in answered}
            if len(seen) != 1 or "unknown" in seen or (fam != "unknown" and seen != {fam}):
                return {"family": "unknown", "model": approved, "restated": False,
                        "how": f"approved {approved}, answered by {', '.join(answered)}: the user's ruling needed"}
            fam = seen.pop()
        return {"family": fam, "model": approved, "how": "launch", "restated": False}
    try:
        src = open(os.path.join(rd, ".source-run")).read().strip()
    except OSError:
        src = ""
    if src and _depth < 5:
        srd = next((d for d in run_dirs() if os.path.basename(d) == src), None)
        if srd:
            f = run_family(srd, _depth + 1)
            return {"family": f["family"], "model": f["model"], "how": f"restated from {src}", "restated": True}
    return {"family": "unknown", "model": None, "how": "no launch record" + (f"; .source-run {src!r} not found" if src else ""),
            "restated": False}


def cross_family_need(rd, doc, claim, live):
    """(required, holds, line) for the cross-family read. Required for a PROVED claim (a live `certify` referee of another
    known family than the producer's must hold: the built-in Anthropic and OpenAI, or one added in kit-env.json) and for a VERIFIED/NUMERIC claim that needs a `sentence` read (that read from the other family). An
    unknown producer, or a restatement of a run of the other family than the orchestrator's (its wording partly the
    orchestrator's), is met only through the user's ruling, recorded in data/cross-family-rulings.json as
    {"<run>": "<family> <where ruled>"} (P-12 C3: never in the run directory, which the worker writes): a hold from that
    family then counts. `line` is the display for verdict.md and the tools."""
    tag = (claim or {}).get("tag")
    q = "certify" if tag == "PROVED" else ("sentence" if sentence_need(doc, claim, [])[0] else None)
    prod = run_family(rd)
    names = {os.path.basename(d): d for d in run_dirs()}
    refs = []
    for r in live:
        f = run_family(names[r["referee_run"]]) if r.get("referee_run") in names else {"family": "unknown", "model": None}
        refs.append((r, f))
    try:
        with open(RULINGS) as f:
            rv = json.load(f).get(os.path.basename(rd))
        ruling = rv.split() if isinstance(rv, str) else []
    except (OSError, ValueError, AttributeError):
        ruling = []
    old = os.path.lexists(os.path.join(rd, ".cross-family-referee"))
    any_other = False   # set when no ruling names the family: then any known family other than the producer's counts
    if ruling:
        want, why = ruling[0], "the user's ruling " + " ".join(ruling[1:])
    elif prod["family"] == "unknown":
        want, why = None, "producer unknown: the user's ruling needed"
    elif prod["restated"] and prod["family"] != ORCHESTRATOR_FAMILY:
        want, why = None, (f"restated by the orchestrator ({ORCHESTRATOR_FAMILY}) from a {prod['family']} run: "
                           "the user's ruling needed")
    else:   # any known family other than the producer's (P-5, user 2026-10-01: a family added in kit-env.json is one too)
        want, why, any_other = None, f"another family than {prod['family']}", True
    other = (lambda fam: fam == want) if want is not None else \
        (lambda fam: any_other and fam not in ("unknown", prod["family"]))
    holds = bool(q) and any(r.get("question") == q and r.get("verdict") == "holds" and other(f["family"]) for r, f in refs)
    required = bool(q)
    who = f"{prod['family']} ({prod['model'] or prod['how']})"
    if prod["restated"]:
        who += f", {prod['how']}; restated by the orchestrator ({ORCHESTRATOR_FAMILY})"
    rtxt = "; ".join(f"{r['referee_run']} {r.get('question')} {f['family']} ({f['model']}) {r.get('verdict')}" for r, f in refs)
    state = ("holds" if holds else "missing") if q else "n/a"
    line = f"producer: {who}; referees: {rtxt or 'none'}; cross-family {q or 'read'}: {state} ({why})"
    if old:
        line += ("; RUN/.cross-family-referee is not read (P-12 C3, kit-v0.6.20): the user's ruling goes in "
                 "data/cross-family-rulings.json")
    return required, holds, line


def proved_questions(live):
    """The referee questions with a live `holds` among a claim's live referee records (P-3 B4: a PROVED claim needs both
    `certify` and `hypotheses`, RULES.md §7)."""
    return frozenset(r.get("question") for r in live if r.get("verdict") == "holds")


def earned_tag(claim_tag, check_status, ref_verdicts, sentence_required=False, sentence_holds=False,
               cross_required=False, cross_holds=False, questions=frozenset(), mutations_missing=False):
    """Apply the earned-tag rules from SCHEMAS.md. Returns (earned, reason).

    earned is one of: a tag name, 'FALSIFIED', 'BLOCKED' (check failed), 'PENDING' (needs a referee).
    questions: proved_questions(live); PROVED needs a live hold on both certify and hypotheses (P-3 B4, user 2026-10-01).
    mutations_missing: check.json's flag for a VERIFIED script claim with no declared mutation; it earns NUMERIC
    (P-3 B6: RULES.md §8, a coverage claim with no mutation test is [NUMERIC]).
    """
    if "falsified" in ref_verdicts:
        return "FALSIFIED", "a referee falsified it"
    if check_status == "fail":
        return "BLOCKED", "check failed"
    if "gap" in ref_verdicts:
        return "GAP", "a referee found a gap"
    holds = bool(ref_verdicts) and all(v == "holds" for v in ref_verdicts)
    if claim_tag == "PROVED":
        missing = [q for q in ("certify", "hypotheses") if q not in questions]
        if holds and missing:
            return "PENDING", f"PROVED needs a live hold on both questions; missing: {', '.join(missing)}"
        if holds and cross_required and not cross_holds:
            return "PENDING", "PROVED needs a cross-family certify referee that holds"
        if check_status not in ("pass", "n/a"):   # P-12: unchecked (not in check.json) is not a check that passed
            return "PENDING", f"PROVED needs its check (bin/check); check is {check_status!r}"
        return ("PROVED", "check pass + referee holds") if holds else ("PENDING", "PROVED needs a referee verdict of holds")
    if claim_tag in ("VERIFIED", "NUMERIC"):
        if check_status == "pass":
            if sentence_required and not sentence_holds:
                return "PENDING", f"{claim_tag} needs a `sentence` referee that holds (claims/2)"
            if cross_required and not cross_holds:
                return "PENDING", f"{claim_tag} needs a cross-family `sentence` referee that holds"
            if claim_tag == "VERIFIED" and mutations_missing:
                return "NUMERIC", "VERIFIED with no mutation test: the checker is not shown to fail on a truncated range"
            return claim_tag, "artifact certifies" + (" + sentence referee holds" if sentence_required else "")
        return "PENDING", f"{claim_tag} needs check pass"
    if claim_tag in ("CONJECTURE", "HEURISTIC", "GAP"):
        if check_status in ("pass", "n/a"):
            return claim_tag, "no certification needed beyond well-formedness"
        return "PENDING", "malformed"
    return "PENDING", "unknown tag"


def live_referees(records, check_rec, claim=None):
    """Well-formed referee records whose artifact copy matches the artifact check.json hashed and, given the claim, whose
    bound claim is this one byte for byte (P-12: a changed statement, range or premise list stales the verdict too).
    Returns (live, stale). A verdict on a file or a claim that has since changed is stale and does not count."""
    live, stale = [], []
    want = (check_rec or {}).get("artifact_sha256")
    for r in records:
        if "error" in r:
            continue
        want_deps = (check_rec or {}).get("deps_sha256") or {}
        got_deps = r.get("deps_sha256") or {}
        if want is not None and r.get("artifact_sha256") != want:   # the bound bytes (P-12 C3), not the referee's copy
            stale.append(r)
        elif claim is not None and r.get("claim_sha256") is not None and r["claim_sha256"] != claim_digest(claim):
            stale.append(r)
        elif sorted(got_deps.values()) != sorted(want_deps.values()):
            stale.append(r)
        else:
            live.append(r)
    return live, stale


# LESSONS.md "Dependencies between ledger entries are read by bytes and by name": dependencies between ledger entries, read from CLAIMS.md.
# Claim ids were the only link the record tracked, so an entry whose deps are the artifacts of three others (the
# source's C-060) would not have been flagged by a supersession of any of them. An entry X depends on an entry Y when
#   "file": Y's artifact sha256 is X's artifact or one of X's deps (the same bytes, wherever the copy lives), or
#   "names": X's statement or silent links name Y's id;
#   "premise": X's Premises line lists Y as a ledger premise.
# Notes are not read: a note records what was learned about an entry, it creates no dependency.
_SHA_RE = re.compile(r"sha256=([0-9a-f]{64})")
_ID_RE = re.compile(r"\bC-(\d{3,})\b(?!-note)")


def ledger_entries():
    """C-NNN -> {tag, statement, artifact_sha, deps_shas, text (statement + silent links), supersedes}."""
    text = _claims_text()
    heads = list(ENTRY_RE.finditer(text))
    out = {}
    for i, m in enumerate(heads):
        end = heads[i + 1].start() if i + 1 < len(heads) else len(text)
        nl = text.find("\n", m.end())   # the body starts after the whole header line, whatever follows the run/claim
        body = text[(nl + 1 if 0 <= nl < end else end):end]   # field (the conditional marker must not swallow the statement)
        cut = re.search(r"^## C-\d+-note", body, re.M)   # notes appended after an entry are not part of it
        body = body[:cut.start()] if cut else body
        lines = body.strip("\n").splitlines()
        e = {"tag": m.group(2), "statement": lines[0] if lines else "", "artifact_sha": None, "deps_shas": set(),
             "silent_links": "", "supersedes": None, "ledger_premises": set()}
        for ln in lines[1:]:
            if ln.startswith("Artifact (") and _SHA_RE.search(ln):
                e["artifact_sha"] = _SHA_RE.search(ln).group(1)
            elif ln.startswith("Deps: "):
                e["deps_shas"] = set(_SHA_RE.findall(ln))
            elif ln.startswith("Premises: "):
                e["ledger_premises"] = set(re.findall(r"(?:^|; )ledger: (C-\d{3,})", ln[len("Premises: "):]))
            elif ln.startswith("Silent links: "):
                e["silent_links"] = ln[len("Silent links: "):]
            elif ln.startswith("Supersedes: "):
                s = ln[len("Supersedes: "):].strip()
                e["supersedes"] = s if s.startswith("C-") else None
        out[m.group(1)] = e
    return out


def claim_graph():
    """(entries, superseded ids, edges) with edges[X] = {Y: sorted kinds} meaning X depends on Y."""
    ent = ledger_entries()
    superseded = {e["supersedes"] for e in ent.values() if e["supersedes"]}
    by_sha = {}
    for gid, e in ent.items():
        if e["artifact_sha"]:
            by_sha.setdefault(e["artifact_sha"], set()).add(gid)
    for h, users in by_sha.items():   # a file restated under a live entry is carried by the live entry
        live = {g for g in users if g not in superseded}
        if live:
            by_sha[h] = live
    edges = {}
    for x, e in ent.items():
        d = {}
        for h in e["deps_shas"] | ({e["artifact_sha"]} if e["artifact_sha"] else set()):
            for y in by_sha.get(h, ()):
                if y != x:
                    d.setdefault(y, set()).add("file")
        for n in _ID_RE.findall(e["statement"] + " " + e["silent_links"]):
            y = f"C-{n}"
            if y != x and y in ent:
                d.setdefault(y, set()).add("names")
        for y in e["ledger_premises"]:
            if y != x and y in ent:
                d.setdefault(y, set()).add("premise")
        d.pop(e["supersedes"], None)   # an entry's own predecessor is on its Supersedes line already
        edges[x] = {y: sorted(k) for y, k in d.items()}
    return ent, superseded, edges


def dependents(gid):
    """Entries that depend on gid, directly or through other entries: [(C-NNN, depth, kinds, live?)]."""
    ent, superseded, edges = claim_graph()
    out, seen, frontier, depth = [], {gid}, [gid], 0
    while frontier:
        depth += 1
        nxt = []
        for x in sorted(edges):
            if x in seen:
                continue
            hit = [y for y in frontier if y in edges[x]]
            if hit:
                kinds = sorted({k for y in hit for k in edges[x][y]})
                out.append((x, depth, kinds, x not in superseded))
                seen.add(x)
                nxt.append(x)
        frontier = nxt
    return out


def supersession_lines(sup):
    """Printed by bin/close-run and bin/ledger-claims for a claim that supersedes `sup` (LESSONS.md "Dependencies between ledger entries are read by bytes and by name"): the live entries
    that depend on `sup` directly. Informational; nothing is refused on it."""
    if not sup:
        return []
    rows = [r for r in dependents(sup) if r[3] and r[1] == 1]
    return [f"live entries depending on {sup} (bin/claim-deps {sup}): " +
            (", ".join(f"{g} via {'+'.join(k)}" for g, _, k, _ in rows) if rows else "none")]


_SEEN = {}


def models_seen(rd):
    """The models a run's requests were answered by, from its own record (LESSONS.md "The model a worker ran on is
    recorded"): Claude, the model of every assistant message in launch.log and any earlier attempt's launch.<ts>.log, and
    every *fallback system event (Claude Code answered with another model after a refusal, seen 2026-09-23 and 09-26:
    Opus 5.5 -> Opus 4.8 for the session); Codex, the model of every turn context in the main thread's
    launch.rollout.jsonl. Returns ({model: count}, [fallback text, ...]), both empty for a run never launched."""
    counts, falls = {}, []
    ro = os.path.join(rd, "launch.rollout.jsonl")
    logs = [ro] if os.path.isfile(ro) else sorted(p for p in glob.glob(os.path.join(rd, "launch*.log")))
    # P-12 (housekeeping): read once per process while every log keeps its size and modification time; the tools ask
    # once per claim and per referee
    key = (rd, tuple((p, os.stat(p).st_size, os.stat(p).st_mtime_ns) for p in logs))
    if key in _SEEN:
        return dict(_SEEN[key][0]), list(_SEEN[key][1])
    for p in logs:
        for line in open(p, errors="replace"):
            try:
                e = json.loads(line)
            except ValueError:
                continue
            if not isinstance(e, dict):
                continue
            if p == ro:
                m = (e.get("payload") or {}).get("model") if e.get("type") == "turn_context" else None
            else:
                m = (e.get("message") or {}).get("model") if e.get("type") == "assistant" else None
                if e.get("type") == "system" and "fallback" in str(e.get("subtype", "")):
                    falls.append(f"{e.get('original_model', '?')}->{e.get('fallback_model', '?')} "
                                 f"({e.get('trigger', '?')}/{e.get('api_refusal_category') or '-'})")
            if isinstance(m, str) and m and m != "<synthetic>":   # Claude Code's own placeholder messages
                counts[m] = counts.get(m, 0) + 1
    _SEEN[key] = (dict(counts), list(falls))
    return counts, falls


def model_flag(rd, requested=None):
    """None, or one line saying the run was not answered by one model: a fallback event, more than one model, or
    (Codex, whose ids are exact) a model other than the one requested. On the Claude routes the requested name (an alias
    such as opus, a routed id) is not compared, so a whole run answered by another model with no fallback event and no
    second model is not caught here."""
    counts, falls = models_seen(rd)
    why = []
    if falls:
        why.append("fallback " + "; ".join(falls))
    if len(counts) > 1:
        why.append("answered by " + ", ".join(f"{m}*{n}" for m, n in sorted(counts.items())))
    elif requested and counts and os.path.isfile(os.path.join(rd, "launch.rollout.jsonl")) and requested not in counts:
        why.append(f"requested {requested}, answered by {next(iter(counts))}")
    return "; ".join(why) or None


def model_lines(rd, records=(), run=True):
    """One line for the run (unless run=False) and for each referee run in `records` (referee_files() records) that was not answered by one
    model: bin/close-run and bin/ledger-claims print them, never refusing (user 2026-09-28: record and flag)."""
    byname = {os.path.basename(d): d for d in run_dirs()}
    out = []
    for name, d in [(os.path.basename(rd), rd)] * run + [(r.get("referee_run"), byname.get(r.get("referee_run"))) for r in records]:
        f = model_flag(d) if d else None
        line = f"MODEL: {name} was not answered by one model ({f}); its approval named one"
        if f and line not in out:
            out.append(line)
    return out
