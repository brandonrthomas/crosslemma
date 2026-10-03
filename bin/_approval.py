#!/usr/bin/python3
"""User approvals (LESSONS.md "Every launch and every ledger append consumes a byte-bound", 2026-09-18). Shared by bin/approve, bin/manifest, the gated
tools (run-external, astra-session, ledger-claims, annotate-claim) and the hook, which words the tap prompt from the
bytes (the plain `--digest` call) and refuses every other command naming the approval tool.

Principle: approval is an act of the user, bound to the exact bytes the user read, and the tools
refuse without it. An approval is one JSON record under ROOT/.claude/state/approvals/ (outside every
run directory, so no worker can write one; gitignored, so the durable record is the APPROVE ledger
line). It names a kind, a key, a manifest {path relative to ROOT: sha256}, the launch flags (a launch approval
always binds them, --model included, and one without them is refused: LESSONS.md "A launch approval binds its flags"),
and expires 30 minutes after it was written. It is single-use: consuming it is an atomic
rename into approvals/used/, so two racing launches cannot both succeed. Only one live approval per kind and key is
kept; writing a different one replaces it and says so.

`--digest d1,d2,…` pins what the user read: one digest of at least 8 hex characters per target, in target order,
and one mismatch refuses the whole call (LESSONS.md "Batch tap"). A queue (`queue`, `queued`; LESSONS.md "A queue for
runs approved together") checks every run's approval, then consumes them all into a queue record under approvals/queue/
that releases each run once, with the same flags and unchanged bytes; the record lives for the sum of the runs' wall
caps plus 30 minutes.

  launch    key = run name    manifest = every regular file in the run dir except the launch logs
  ledger    key = run name    manifest = claims.json, check.json, verdict.md, every live referee.json
                              of the named ids, CLAIMS.md; ids bound
  annotate  key = C-NNN       manifest = CLAIMS.md and the sha256 of the normalised note text
            key = batch-<12 hex of the file>   manifest = CLAIMS.md and a notes file (LESSONS.md "One approval
                              for several notes; a replaced approval is announced"): one approval for several notes, appended in one
                              write by `bin/annotate-claim --batch FILE`; the approval printout shows every note in full
  session   key = astra       no manifest; the argv of a headless bin/astra-session is bound

Tools written in bash call:  bin/_approval.py check launch RUN_DIR [-- flags…]   (consumes; exit 3 = refused)
Stdlib only at import time: the hook loads this file. The root is the parent of this file's directory;
KIT_ROOT overrides it for fixture tests.
"""
import fnmatch
import glob
import hashlib
import json
import os
import re
import secrets
import sys
import time

REAL_ROOT = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
ROOT = os.path.realpath(os.environ.get("KIT_ROOT", REAL_ROOT))
TTL = 30 * 60
KINDS = ("launch", "ledger", "annotate", "session")
APPROVAL_SCHEMA = "kit/approval/1"   # in step with bin/_lib.py SCHEMA_PREFIX
# Top-level files of a run dir that a launch itself writes; everything else is what the worker sees.
EXCLUDE_TOP = (".ledger-outbox", "usage.json", "time.log", "licence.log", "launch*.log", "launch*.err", "debug*.log",
               "launch*.jsonl", "launch*.last.md", "gateway*.log", "egress*.log", "RECORD-EXT.md")  # LESSONS.md "Networked and Codex launches need their flags bound"


class Refused(Exception):
    pass


def approvals_dir(root=None):
    return os.path.join(root or ROOT, ".claude", "state", "approvals")


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def utc(t=None):
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(t))


def ledger(root, run, event, detail):
    # Never creates LEDGER.log (stdlib-only copy of _lib.append_ledger; LESSONS.md "A session works on the tree it was opened in").
    detail = " ".join(str(detail).split())
    fd = os.open(os.path.join(root or ROOT, "LEDGER.log"), os.O_WRONLY | os.O_APPEND)
    with os.fdopen(fd, "a") as f:
        f.write(f"{utc()} | user | {run or '-'} | {event} | {detail[:400]}\n")


def resolve_run(arg, root=None):
    root = root or ROOT
    runs = sorted(os.path.realpath(d) for d in glob.glob(os.path.join(root, "workspace-*", "runs", "*"))
                  if os.path.isdir(d))
    for c in (os.path.realpath(arg), os.path.realpath(os.path.join(root, arg))):
        if c in runs:
            return c
    hits = [d for d in runs if os.path.basename(d) == arg]
    if len(hits) == 1:
        return hits[0]
    raise Refused(f"no unique run directory matches {arg!r}" + (f": {hits}" if hits else ""))


def launch_manifest(rd, root=None):
    root = root or ROOT
    rd = os.path.realpath(rd)
    if not os.path.isfile(os.path.join(rd, "BRIEF.md")):
        raise Refused(f"{rd}/BRIEF.md missing")
    man = {}
    for dp, dn, fn in os.walk(rd):
        for name in sorted(dn + fn):
            p = os.path.join(dp, name)
            rel = os.path.relpath(p, root)
            if os.path.islink(p):
                raise Refused(f"symlink in run directory: {rel}")
            if name in dn:
                continue
            if dp == rd and any(fnmatch.fnmatch(name, pat) for pat in EXCLUDE_TOP):
                continue
            if not os.path.isfile(p):
                raise Refused(f"not a regular file: {rel}")
            if os.lstat(p).st_nlink > 1:   # P-12: its bytes, and a worker's writes, would be shared with a file elsewhere
                raise Refused(f"hard link in run directory: {rel} (another name holds the same file)")
            man[rel] = sha256(p)
    return man


def _claims_md_sha(root):
    p = os.path.join(root, "CLAIMS.md")
    return sha256(p) if os.path.isfile(p) else "absent"


def ledger_manifest(rd, ids, root=None):
    """The bytes being certified (audit 157 F2), not the solver's brief packet."""
    root = root or ROOT
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import _lib as L
    if L.ROOT != os.path.realpath(root):
        raise Refused(f"root mismatch: {L.ROOT} vs {root}")
    name = os.path.basename(rd)
    man = {}
    for rel in ("output/claims.json", "check.json", "verdict.md"):
        p = os.path.join(rd, rel)
        if not os.path.isfile(p):
            raise Refused(f"{name}/{rel} missing (close the run first)")
        man[os.path.relpath(p, root)] = sha256(p)
    with open(os.path.join(rd, "output", "claims.json")) as f:
        have = {c.get("id"): c for c in json.load(f).get("claims", []) if isinstance(c, dict)}
    with open(os.path.join(rd, "check.json")) as f:
        checks = {r["id"]: r for r in json.load(f).get("claims", [])}
    refs = L.referee_files()
    for cid in ids:
        if cid not in have:
            raise Refused(f"{cid}: not in {name}/output/claims.json")
        live, _ = L.live_referees(refs.get((name, cid), []), checks.get(cid), have[cid])
        for r in live:
            man[r["path"]] = sha256(os.path.join(root, r["path"]))
            if r.get("binding"):   # P-12 C3: what the earned tag read the referee's question and bytes from
                man[r["binding"]] = sha256(os.path.join(root, r["binding"]))
    if os.path.isfile(os.path.join(root, "data", "cross-family-rulings.json")):   # the user's rulings, as approved
        man["data/cross-family-rulings.json"] = sha256(os.path.join(root, "data", "cross-family-rulings.json"))
    man["CLAIMS.md"] = _claims_md_sha(root)
    return man


def note_text(text):
    return " ".join(text.split())


def annotate_manifest(text, root=None):
    return {"CLAIMS.md": _claims_md_sha(root or ROOT),
            "note-text": hashlib.sha256(note_text(text).encode()).hexdigest()}


def annotate_batch(path, root=None):
    """A notes file: a JSON list of {"id": "C-NNN", "text": "..."}, inside the tree. Returns (key, manifest, notes).
    Only the form is checked here; bin/annotate-claim --batch checks each note as it checks one."""
    root = root or ROOT
    p = os.path.realpath(path if os.path.isabs(path) else os.path.join(root, path))
    if not (p.startswith(os.path.realpath(root) + os.sep) and os.path.isfile(p)):
        raise Refused(f"notes file must be a file inside the tree: {path}")
    try:
        with open(p) as f:
            notes = json.load(f)
    except Exception as e:
        raise Refused(f"notes file is not JSON: {e}")
    if not (isinstance(notes, list) and notes and all(isinstance(n, dict) and set(n) == {"id", "text"}
                                                     and isinstance(n["id"], str) and isinstance(n["text"], str)
                                                     for n in notes)):
        raise Refused('notes file must be a non-empty JSON list of {"id": "C-NNN", "text": "..."}')
    sha = sha256(p)
    return "batch-" + sha[:12], {"CLAIMS.md": _claims_md_sha(root), os.path.relpath(p, root): sha}, notes


def digest(kind, key, ids, manifest):
    blob = json.dumps([kind, key, sorted(ids or []), sorted(manifest.items())], separators=(",", ":"))
    return hashlib.sha256(blob.encode()).hexdigest()


REPEATABLE_FLAGS = {"--module"}   # bin/run-external appends these; every other flag it takes once, the last given winning


def norm_argv(argv):
    """Options compare as a set (order is not part of what was approved): `--k v` pairs, and bare flags such as
    `--network` (an option followed by another option or by nothing; LESSONS.md "Networked and Codex launches need their flags bound"). An argv that does not
    parse as options (a token not starting with -- where an option is expected) is kept verbatim."""
    if argv is None:
        return None
    argv = [str(a) for a in argv]
    groups, i = [], 0
    while i < len(argv):
        if not argv[i].startswith("--"):
            return argv
        if i + 1 < len(argv) and not argv[i + 1].startswith("--"):
            groups.append((argv[i], argv[i + 1])); i += 2
        else:
            groups.append((argv[i],)); i += 1
    names = [g[0].split("=", 1)[0] for g in groups]
    twice = sorted({n for n in names if names.count(n) > 1 and n not in REPEATABLE_FLAGS})
    if twice:   # P-12: sorted, both would be approved, and bin/run-external takes the last
        raise Refused(f"flag given more than once: {', '.join(twice)}; give each once")
    return [x for g in sorted(groups) for x in g]


def record_path(kind, key, root=None):
    return os.path.join(approvals_dir(root), f"{kind}-{key}.json")


def write(kind, key, manifest, ids=None, argv=None, root=None, now=None):
    assert kind in KINDS
    now = time.time() if now is None else now
    rec = {"schema": APPROVAL_SCHEMA, "kind": kind, "key": key, "ids": sorted(ids or []),
           "argv": norm_argv(argv), "manifest": manifest, "digest": digest(kind, key, ids, manifest),
           "created": now, "created_utc": utc(now), "expires": now + TTL, "nonce": secrets.token_hex(8)}
    os.makedirs(os.path.join(approvals_dir(root), "used"), exist_ok=True)
    p = record_path(kind, key, root)
    try:  # a second approval for the same kind and key replaces the first; say so, never silently
        with open(p) as f:
            old = json.load(f)
        if old.get("expires", 0) > now and (old.get("digest"), old.get("argv"), old.get("ids")) != (rec["digest"], rec["argv"], rec["ids"]):
            print(f"note: this replaces the unused approval of {old.get('created_utc')} for {kind} {key} "
                  f"(digest {str(old.get('digest'))[:12]}); only one approval per {kind} {key} is kept")
    except (OSError, ValueError):
        pass
    with open(p + ".tmp", "w") as f:
        json.dump(rec, f, indent=1)
    os.replace(p + ".tmp", p)
    return rec


def _last_used(kind, key, root):
    used = sorted(glob.glob(os.path.join(approvals_dir(root), "used", f"{kind}-{key}.*.json")))
    return os.path.basename(used[-1]).split(".")[-3] if used else None


def check(kind, key, manifest, ids=None, argv=None, consume=False, root=None, now=None, require_flags=False):
    """Return the approval's digest, or raise Refused with the reason. consume=True spends it.
    require_flags=True (a networked or Codex launch, LESSONS.md "Networked and Codex launches need their flags bound"): refuse an approval that bound no flags."""
    now = time.time() if now is None else now
    p = record_path(kind, key, root)
    head = f"no user approval for these hashes ({kind} {key}): "
    try:
        with open(p) as f:
            rec = json.load(f)
    except FileNotFoundError:
        u = _last_used(kind, key, root)
        raise Refused(head + (f"none on file; the last one was used at {u} (approvals are single-use)" if u
                              else "none on file"))
    except Exception as e:
        raise Refused(head + f"approval record unreadable: {e!r}")
    if rec.get("kind") != kind or rec.get("key") != key:
        raise Refused(head + "record is for something else")
    if now >= rec.get("expires", 0):
        raise Refused(head + f"expired at {utc(rec.get('expires', 0))} (approvals last {TTL // 60} minutes)")
    if sorted(ids or []) != rec.get("ids", []):
        raise Refused(head + f"approved ids {rec.get('ids')} != requested {sorted(ids or [])}")
    if (require_flags or kind == "launch") and rec.get("argv") is None:
        raise Refused(head + "this launch needs its flags bound in the approval (approve with `-- <the exact flags>`)")
    if rec.get("argv") is not None and norm_argv(argv or []) != rec["argv"]:
        raise Refused(head + f"approved flags {rec['argv']} != these flags {norm_argv(argv or [])}")
    old = rec.get("manifest", {})
    diff = ([f"changed: {k}" for k in sorted(old) if k in manifest and manifest[k] != old[k]]
            + [f"added: {k}" for k in sorted(manifest) if k not in old]
            + [f"removed: {k}" for k in sorted(old) if k not in manifest])
    if diff:
        raise Refused(head + "bytes differ from what was approved: " + "; ".join(diff))
    if consume:
        dst = os.path.join(approvals_dir(root), "used", f"{kind}-{key}.{utc(now).replace(':', '')}.{rec['nonce']}.json")
        try:
            os.rename(p, dst)
        except FileNotFoundError:
            raise Refused(head + "already used (approvals are single-use)")
    return rec["digest"]


# LESSONS.md 'A queue for runs approved together': a queue. Runs approved together launch one at a
# time, so a later run's approval could expire while an earlier run worked. `bin/run-external --queue` uses every run's
# approval at the start (all checked first, then all consumed) and keeps what they bound in a queue record, here in the
# approvals directory, where the orchestrator cannot write; each run is then released once, just before its launch,
# only with the same flags and only if its bytes still equal what was approved. A queue record lives for the sum of its
# runs' wall-clock caps plus QUEUE_SLACK, the sum computed here from the launch flags (queue_wall_seconds) unless the
# caller gives it (--wall-seconds); a queue cannot outlast the launches it was approved for.
QUEUE_SLACK = 30 * 60


def queue_path(nonce, root=None):
    return os.path.join(approvals_dir(root), "queue", f"{nonce}.json")


def queue_token(nonce, key, root=None):
    """One file per queued run, claimed by an atomic rename when the run is released: two callers racing for the same
    run cannot both win (the outside review's F4; the record's `launched` field alone was read, then rewritten)."""
    return os.path.join(approvals_dir(root), "queue", f"{nonce}.{key}.token")


def queue_wall_seconds(argv, n):
    """The sum of n runs' wall-clock caps under these launch flags: --wall-hours if given, else the route's default
    (bin/run-external: 4 h on the Claude routes, 2 h on Codex). The one place a queue's lifetime is computed (the outside
    review's F12: the launcher used to compute it, untested)."""
    argv = list(argv or [])
    via = argv[argv.index("--via") + 1] if "--via" in argv[:-1] else "openrouter"
    hours = float(argv[argv.index("--wall-hours") + 1]) if "--wall-hours" in argv[:-1] else (2.0 if via == "codex" else 4.0)
    return int(hours * 3600 * n)


def queue_start(rds, argv=None, require_flags=False, root=None, now=None, wall_seconds=None):
    """Consume the launch approvals of every run in rds (all or none) and write the queue record. Returns its nonce.
    `wall_seconds` is the sum of the queued runs' wall-clock caps; the record expires that long plus QUEUE_SLACK after
    the start."""
    now = time.time() if now is None else now
    jobs = [(os.path.basename(os.path.realpath(rd)), launch_manifest(rd, root)) for rd in rds]
    if len({k for k, _ in jobs}) != len(jobs):
        raise Refused("a run is named twice in the queue")
    for key, man in jobs:                       # every approval is checked before any is used
        check("launch", key, man, argv=argv or [], require_flags=require_flags, root=root, now=now)
    runs = {}
    for key, man in jobs:
        try:
            dg = check("launch", key, man, argv=argv or [], consume=True, require_flags=require_flags, root=root, now=now)
        except Refused as e:   # P-12: an approval taken between the check and here; say which ones this queue spent
            raise Refused(f"{e}; the queue did not start, and these approvals are spent, nothing launched: "
                          f"{', '.join(runs) or 'none'} (each needs a new approval)")
        runs[key] = {"manifest": man, "argv": norm_argv(argv or []), "digest": dg, "launched": None}
    nonce = secrets.token_hex(8)
    rec = {"schema": "kit/queue/1", "nonce": nonce, "order": [k for k, _ in jobs], "runs": runs,
           "created": now, "created_utc": utc(now), "expires": now + max(0, int(queue_wall_seconds(argv, len(jobs)) if wall_seconds is None else wall_seconds)) + QUEUE_SLACK}
    os.makedirs(os.path.dirname(queue_path(nonce, root)), exist_ok=True)
    for key in runs:
        open(queue_token(nonce, key, root), "w").close()
    with open(queue_path(nonce, root) + ".tmp", "w") as f:
        json.dump(rec, f, indent=1)
    os.replace(queue_path(nonce, root) + ".tmp", queue_path(nonce, root))
    return nonce


def queue_take(nonce, rd, argv=None, root=None, now=None):
    """Release one run of a queue for launch; raise Refused unless its bytes and flags are the ones approved."""
    now = time.time() if now is None else now
    key = os.path.basename(os.path.realpath(rd))
    head = f"no queued approval for these hashes (launch {key}, queue {nonce}): "
    if not re.fullmatch(r"[0-9a-f]{16}", nonce or ""):
        raise Refused(head + "not a queue id")
    try:
        with open(queue_path(nonce, root)) as f:
            rec = json.load(f)
    except (OSError, ValueError) as e:
        raise Refused(head + f"no queue record ({e.__class__.__name__})")
    if now >= rec.get("expires", 0):
        raise Refused(head + f"the queue expired at {utc(rec.get('expires', 0))}")
    ent = rec.get("runs", {}).get(key)
    if ent is None:
        raise Refused(head + "this run is not in the queue")
    if ent.get("launched"):
        raise Refused(head + f"already released at {ent['launched']} (each queued run launches once)")
    if norm_argv(argv or []) != ent.get("argv"):
        raise Refused(head + f"approved flags {ent.get('argv')} != these flags {norm_argv(argv or [])}")
    man = launch_manifest(rd, root)
    old = ent.get("manifest", {})
    diff = ([f"changed: {k}" for k in sorted(old) if k in man and man[k] != old[k]]
            + [f"added: {k}" for k in sorted(man) if k not in old] + [f"removed: {k}" for k in sorted(old) if k not in man])
    if diff:
        raise Refused(head + "bytes differ from what was approved: " + "; ".join(diff))
    try:   # the claim itself: exactly one caller can rename the token
        os.rename(queue_token(nonce, key, root), queue_token(nonce, key, root) + ".taken")
    except FileNotFoundError:
        raise Refused(head + "already released (each queued run launches once)")
    ent["launched"] = utc(now)
    with open(queue_path(nonce, root) + ".tmp", "w") as f:
        json.dump(rec, f, indent=1)
    os.replace(queue_path(nonce, root) + ".tmp", queue_path(nonce, root))
    return ent["digest"]


def verify_launch(rd, digest, root=None):
    """P-12 (a medium of the code audit): the run's bytes read again just before its worker starts, against the approval
    used for it (a used record, or a queue's entry) with this digest. Between using the approval and the start, the
    launcher sets up (a gateway, Codex's catalog), and the bytes could change in that window. Raises Refused."""
    key = os.path.basename(os.path.realpath(rd))
    head = f"no used approval matching these hashes (launch {key}): "
    old = None
    for p in sorted(glob.glob(os.path.join(approvals_dir(root), "used", f"launch-{key}.*.json"))):
        try:
            rec = json.load(open(p))
        except (OSError, ValueError):
            continue
        if rec.get("digest") == digest:
            old = rec.get("manifest", {})
    for p in sorted(glob.glob(os.path.join(approvals_dir(root), "queue", "*.json"))):
        try:
            ent = (json.load(open(p)).get("runs") or {}).get(key) or {}
        except (OSError, ValueError, AttributeError):
            continue
        if ent.get("digest") == digest:
            old = ent.get("manifest", {})
    if old is None:
        raise Refused(head + f"none with digest {str(digest)[:12]}")
    man = launch_manifest(rd, root)
    diff = ([f"changed: {k}" for k in sorted(old) if k in man and man[k] != old[k]]
            + [f"added: {k}" for k in sorted(man) if k not in old] + [f"removed: {k}" for k in sorted(old) if k not in man])
    if diff:
        raise Refused(f"the run's bytes changed after its approval was used, before its worker started: " + "; ".join(diff))


def _print_manifest(title, man, dg, argv, root, show):
    print(f"== {title}")
    for rel in sorted(man):
        p = os.path.join(root, rel)
        size = os.path.getsize(p) if os.path.isfile(p) else "-"
        print(f"{man[rel]}  {size:>9}  {rel}")
    print(f"digest: {dg}   ({len(man)} entries)")
    if argv is not None:
        print("flags : " + " ".join(norm_argv(argv)))
    if show:
        for rel in sorted(man):
            p = os.path.join(root, rel)
            if os.path.isfile(p):
                print(f"\n----- {rel}")
                with open(p, errors="replace") as f:
                    sys.stdout.write(f.read())


def plan(args, root=None):
    """Parse bin/approve's arguments into (options, jobs) without writing anything; raises Refused.
    A job is (kind, key, ids, manifest, argv, ledger run). The hook uses this to word its prompt."""
    import argparse
    root = root or ROOT
    args = list(args)
    argv = None
    if "--" in args:
        i = args.index("--")
        args, argv = args[:i], args[i + 1:]
    ap = argparse.ArgumentParser(prog="bin/approve | bin/manifest", exit_on_error=False)
    ap.add_argument("targets", nargs="*")
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--ledger", action="store_true", help="RUN c1 c2 …: a CLAIMS.md append")
    g.add_argument("--annotate", action="store_true", help='C-NNN "text": a CLAIMS.md note')
    g.add_argument("--annotate-batch", action="store_true", help="FILE: several CLAIMS.md notes, one approval")
    g.add_argument("--session", action="store_true", help="a headless bin/astra-session; its argv after --")
    ap.add_argument("--digest", help="refuse unless the digest starts with this (≥ 8 hex chars)")
    ap.add_argument("--show", action="store_true", help="also print the contents of every file")
    try:
        a = ap.parse_args(args)
    except SystemExit as e:
        if not e.code:
            raise  # --help
        raise Refused("bad arguments")
    except argparse.ArgumentError as e:
        raise Refused(f"bad arguments: {e}")
    jobs = []
    if a.session:
        if a.targets or argv is None:
            raise Refused("usage: --session -- <astra-session arguments>")
        jobs.append(("session", "astra", [], {}, argv, None))
    elif a.annotate:
        if len(a.targets) != 2 or argv is not None:
            raise Refused('usage: --annotate C-NNN "text"')
        jobs.append(("annotate", a.targets[0], [], annotate_manifest(a.targets[1], root), None, None))
    elif a.annotate_batch:
        if len(a.targets) != 1 or argv is not None:
            raise Refused("usage: --annotate-batch FILE")
        key, man, _ = annotate_batch(a.targets[0], root)
        jobs.append(("annotate", key, [], man, None, None))
    elif a.ledger:
        if len(a.targets) < 2 or argv is not None:
            raise Refused("usage: --ledger RUN c1 [c2 …]")
        rd = resolve_run(a.targets[0], root)
        ids = a.targets[1:]
        jobs.append(("ledger", os.path.basename(rd), ids, ledger_manifest(rd, ids, root), None, os.path.basename(rd)))
    else:
        if not a.targets:
            raise Refused("usage: RUN [RUN …] [--digest HEX] -- <launch flags>")
        # every launch approval binds its flags, --model at least: an approval with none would let any model, effort,
        # prompt or cap launch on the user's word about the bytes alone (LESSONS.md "A launch approval binds its flags")
        if argv is None or "--model" not in argv:
            raise Refused("a launch approval binds its flags: approve with `-- <the exact launch flags>`, --model included")
        for t in a.targets:
            rd = resolve_run(t, root)
            jobs.append(("launch", os.path.basename(rd), [], launch_manifest(rd, root), argv, os.path.basename(rd)))
    # Batch tap (LESSONS.md "Batch tap"): --digest d1,d2,… names one digest per target, in the order of the targets, so
    # one prompt can approve several runs, each still bound to the bytes the user saw in bin/manifest's printout.
    pins = [d.strip().lower() for d in a.digest.split(",")] if a.digest else []
    if a.digest and (len(pins) != len(jobs) or any(len(d) < 8 for d in pins)):
        raise Refused("--digest takes one digest of at least 8 hex characters per target, comma-separated, in target order")
    for n, (kind, key, ids, man, av, _) in enumerate(jobs):
        dg = digest(kind, key, ids, man)
        if pins and not dg.startswith(pins[n]):
            raise Refused(f"{kind} {key}: digest is {dg}, not {pins[n]}…: the bytes are not the ones that digest named")
    return a, jobs


def approve_main(args, do_write):
    """bin/approve (do_write=True, the user's act) and bin/manifest (do_write=False, read-only)."""
    root = ROOT
    try:
        a, jobs = plan(args, root)
    except Refused as e:
        print(f"refused: {e}", file=sys.stderr)
        return 3
    if do_write and not os.path.isfile(os.path.join(root, "LEDGER.log")):
        # checked before any record is written, so an approval never exists without its ledger line
        print(f"refused: no LEDGER.log at {root}: this tree is not an instance (the kit, or a command run in the wrong "
              "directory); nothing approved", file=sys.stderr)
        return 3
    for kind, key, ids, man, av, run in jobs:
        dg = digest(kind, key, ids, man)
        _print_manifest(f"{kind} {key}" + (f" ids={','.join(ids)}" if ids else ""), man, dg, av, root, a.show)
        if kind == "annotate" and key.startswith("batch-"):   # what is approved is the notes: print them in full
            for n in annotate_batch(a.targets[0], root)[2]:
                print(f"  note on {n['id']}: {note_text(n['text'])}")
        if do_write:
            rec = write(kind, key, man, ids, av, root)
            ledger(root, run, "APPROVE", f"kind={kind} key={key} digest={dg} entries={len(man)}"
                   + (f" ids={','.join(ids)}" if ids else "") + (f" flags={' '.join(rec['argv'])}" if rec["argv"] is not None else "")
                   + f" expires={utc(rec['expires'])}")
            print(f"APPROVED until {utc(rec['expires'])}, single use.")
        else:
            print("(read-only: nothing approved)")
    if not do_write:   # P-14 (c): the exact line that approves what was just shown, so nobody gives it from memory
        import shlex
        head = list(args[:args.index("--")] if "--" in args else args)
        tail = args[args.index("--") + 1:] if "--" in args else None
        keep, i = [], 0
        while i < len(head):
            if head[i] == "--show":
                i += 1
            elif head[i] == "--digest":
                i += 2
            elif head[i].startswith("--digest="):
                i += 1
            else:
                keep.append(head[i]); i += 1
        dgs = ",".join(digest(kind, key, ids, man)[:12] for kind, key, ids, man, _, _ in jobs)
        line = shlex.quote(os.path.join(root, "bin", "approve")) + " " + shlex.join(keep + ["--digest", dgs]) + (" -- " + shlex.join(tail) if tail is not None else "")
        print(f"approve exactly this: {line}")
        print("  (the user's act: with `!` at the terminal, or the user's tap on this one plain call)")
    return 0


def main():
    a = sys.argv[1:]
    argv = None
    if "--" in a:
        i = a.index("--")
        a, argv = a[:i], a[i + 1:]
    req = "--require-flags" in a
    a = [x for x in a if x != "--require-flags"]
    wall = None
    if "--wall-seconds" in a:   # the queue's lifetime: the sum of its runs' wall caps
        i = a.index("--wall-seconds")
        try:
            wall = int(a[i + 1])
        except (IndexError, ValueError):
            print("refused: --wall-seconds takes a whole number of seconds", file=sys.stderr)
            return 2
        a = a[:i] + a[i + 2:]
    usage = ("usage: _approval.py check launch RUN_DIR [--require-flags] [-- flags…] | check session KEY -- argv… | "
             "queue RUN_DIR… [--require-flags] [--wall-seconds S] [-- flags…] | queued NONCE RUN_DIR [-- flags…] | "
             "verify launch RUN_DIR DIGEST")
    if a[:1] == ["queue"] and len(a) >= 2:
        try:
            print(queue_start([resolve_run(x) for x in a[1:]], argv=argv or [], require_flags=req, wall_seconds=wall))
        except Refused as e:
            print(f"refused: {e}", file=sys.stderr)
            return 3
        return 0
    if a[:1] == ["queued"] and len(a) == 3:
        try:
            print(queue_take(a[1], resolve_run(a[2]), argv=argv or []))
        except Refused as e:
            print(f"refused: {e}", file=sys.stderr)
            return 3
        return 0
    if a[:2] == ["verify", "launch"] and len(a) == 4:   # verify launch RUN_DIR DIGEST: just before the worker starts
        try:
            verify_launch(resolve_run(a[2]), a[3])
        except Refused as e:
            print(f"refused: {e}", file=sys.stderr)
            return 3
        return 0
    if len(a) != 3 or a[0] != "check" or a[1] not in ("launch", "session"):
        print(usage, file=sys.stderr)
        return 2
    try:
        if a[1] == "launch":
            rd = resolve_run(a[2])
            print(check("launch", os.path.basename(rd), launch_manifest(rd), argv=argv or [], consume=True, require_flags=req))
        else:
            print(check("session", a[2], {}, argv=argv or [], consume=True))
    except Refused as e:
        print(f"refused: {e}", file=sys.stderr)
        return 3
    return 0


if __name__ == "__main__":
    sys.exit(main())
