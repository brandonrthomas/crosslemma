"""Packet scan (LESSONS.md "No packet carries blocked material").

A content rule: no worker receives what an instance has ruled out of every packet, typically probabilities of success,
rankings of routes, or evaluations of the record. What is ruled out is the instance's own list, data/packet-rules.json,
which only the user edits (bin/packet-block, with !):
  "blocked": [{"path": "<root-relative file or directory>", "why": "..."}]   out of every packet whole
  "lines":   [{"path": "<file or run directory>", "match": "<regex>", "why": "..."}]   only the matching lines out
  "verdicts": true | "<regex>" | false   route-verdict words ("ranking #7", PARK, PURSUE, DEAD, …) refused on any line of
                                         any packet file, whatever its source; true (VERDICT_RE) in a new instance
  "extract": the entries and notes bin/claims-extract leaves out of a worker's view of the ledger (not read here)
A file the user rules out of the rule by name (data/packet-exceptions.json, by sha256; bin/packet-except) may go in.
With no rules file, or an empty one, nothing is blocked. A blocked run is blocked whole except its input/ (copies of
open material), its downloads/ and what its launch transcripts quote back from its own input/.

bin/lint-brief calls findings(RUN_DIR) on what the worker sees (BRIEF.md, HARNESS-NOTE.md, input/):
  ERR   a file byte-identical to a blocked file (unless the same bytes are also open material)
  ERR   text shared with a blocked source: a 12-word run of words (case-folded) found in it, unless the same run of
        words also occurs in open material: OPEN, or the output/ of an EARLIER run that is not blocked and was launched
        or checked (a launch transcript or a check.json on file); a blocked path inside either, and the matching lines
        of a line rule's file, are not open material. A packet (BRIEF.md, HARNESS-NOTE.md, input/) is never
        open material, so two packets cannot excuse each other, and neither can a run made or written later. Every file
        of a packet is read as text, whatever its name; every blocked file that decodes as text is indexed, blocked
        runs' launch transcripts included; binary files are compared by hash only. A file on the exceptions list is
        neither blocked nor open.
  ERR   a line of any packet file matching the instance's route-verdict pattern ("verdicts")
  WARN  a line naming a blocked path by its last component (its existence reaches the worker, not its text)
Limit: text that an open run has quoted from a blocked source counts as open, and so does text copied into a tool or
rule file. The scan is a net under the rule, not the rule; packets are still built from open material only. The index
of blocked text is cached under .claude/state/ and rebuilt when any file it was built from changes; the launch path
(findings(..., use_cache=False), bin/lint-brief --packet) never reads the cache, which the orchestrator can write. A
file that vanishes while the scan walks the tree is skipped, not an error. Stdlib only.
KIT_ROOT points it at a fixture tree.
"""
import hashlib
import json
import os
import re

import _lib as L

N = 12
MAX_BYTES = 50_000_000   # a larger file is compared by hash only

RULES = os.path.join("data", "packet-rules.json")
OPEN = ("problems", "lean", "CLAIMS.md", "SCHEMAS.md", "RULES.md", "FLOW.md", "LESSONS.md", "templates", "bin", "tests",
        ".claude/hooks", ".claude/sandbox", "harness")   # rules, tools and the open record; not evaluations. Text copied
                                                          # into one of them becomes open: the same limit as quoting
EXCEPTIONS = os.path.join("data", "packet-exceptions.json")
CACHE = os.path.join(".claude", "state", "packet-index.json")
INF = 10 ** 9   # "never seen in open material"


def rules():
    """(blocked [(path, why)], lines [(path, compiled regex, why)]) from data/packet-rules.json; empty without it.
    A malformed file raises: a scan that cannot read its rules has not scanned (bin/lint-brief --packet exits 4)."""
    p = os.path.join(L.ROOT, RULES)
    if not os.path.isfile(p):
        return [], []
    with open(p) as f:
        r = json.load(f)
    blocked = [(e["path"].strip("/"), e.get("why", "")) for e in r.get("blocked", [])]
    lines = [(e["path"].strip("/"), re.compile(e["match"], re.I), e.get("why", "")) for e in r.get("lines", [])]
    return blocked, lines


# Route verdicts, whatever file carries them (LESSONS.md "No packet carries blocked material"; the source's method change 50):
# the text scan sees only what is copied from blocked material, and a verdict can reach a packet through open material (the
# source found "ranking #7" and "PARKed" in its open register). An instance turns this on in data/packet-rules.json with
# "verdicts": true (this pattern) or its own regex. The class words PURSUE and DEAD count in capitals only (lowercase "pursue"
# and "dead" are ordinary prose); matrix and curve ranks ("rank 6") do not match.
VERDICT_RE = re.compile(r"(?i:\branking\s*#\s*\d|#\s*\d+\s+in\s+(?:the|its|a|our|their)\s+ranking|"
                        r"\branked\s+(?:#\s*\d|first|second|third|last|highest|lowest|top)\b|\bpark(?:s|ed|ing)?\b|"
                        r"\bworth\s+pursuing\b|\b(?:most|least)\s+promising\b|\blong\s+shots?\b|\bbest\s+route\b)|"
                        r"\bPURSUE\b|\bDEAD\b")


def verdict_rule():
    """The instance's route-verdict pattern: VERDICT_RE for "verdicts": true, its own regex for a string, None when off."""
    p = os.path.join(L.ROOT, RULES)
    if not os.path.isfile(p):
        return None
    v = json.load(open(p)).get("verdicts")
    return VERDICT_RE if v is True else re.compile(v) if isinstance(v, str) and v else None


def _name_re(blocked, lines):
    names = sorted({os.path.basename(p) for p, _ in blocked} | {os.path.basename(p) for p, _, _ in lines} - {""})
    return re.compile("|".join(re.escape(n) for n in names), re.I) if names else None




def _walk(base, skip, launch=False):
    p = os.path.join(L.ROOT, base)
    if os.path.isfile(p):
        return [p]
    out = []
    for dp, dn, fn in os.walk(p):
        dn[:] = sorted(d for d in dn if d not in skip)
        out += [os.path.join(dp, f) for f in sorted(fn) if launch or not f.startswith("launch")]
    return out


class TooLarge(Exception):
    """A text file over MAX_BYTES: never silently compared by hash alone (the outside review's F9)."""


def _text(path, strict=False):
    """The file as text, whatever its name; None for a binary file (a NUL byte in its first 8 KiB). A text file over
    MAX_BYTES raises TooLarge when `strict` (blocked material, a packet file); otherwise it is None, which for open
    material only means it excuses nothing."""
    try:
        if os.path.getsize(path) > MAX_BYTES:
            with open(path, "rb") as f:
                head = f.read(8192)
            if b"\x00" in head:
                return None
            if strict:
                raise TooLarge(os.path.relpath(path, L.ROOT))
            return None
        with open(path, "rb") as f:
            raw = f.read()
    except OSError:
        return None
    if b"\x00" in raw[:8192]:
        return None
    return raw.decode("utf-8", errors="replace")


def _words(text):
    """The words of a text, case-folded, with the workspace's own path taken out first: every brief names its run
    directory, and a path is not content (it made every packet share 12 words with every blocked brief)."""
    for root in {L.ROOT, L.REAL_ROOT}:
        text = text.replace(root, " ")
    return re.findall(r"\w+", text.lower())


def _hashes(text):
    """64-bit hashes of every 12-word run of the text (see _words)."""
    w = _words(text)
    return {hashlib.blake2b(" ".join(w[i:i + N]).encode(), digest_size=8).hexdigest() for i in range(len(w) - N + 1)}


def _exception_entries():
    """The user's exceptions list as written; a malformed list raises, which is a failed scan, never "no exceptions"."""
    p = os.path.join(L.ROOT, EXCEPTIONS)
    if not os.path.isfile(p):
        return []
    with open(p) as f:
        entries = json.load(f)
    if not isinstance(entries, list) or not all(isinstance(e, dict) and "sha256" in e and "path" in e for e in entries):
        raise ValueError(f"{EXCEPTIONS} is malformed: a list of {{sha256, path, ruling}} objects expected")
    return entries


def exceptions():
    """{sha256: entry} for the exceptions that are live: an exception names a file of the tree and is live only while that
    file still has the excepted bytes (the outside review's F10: by hash alone, old bytes stayed excepted forever)."""
    out = {}
    for e in _exception_entries():
        fp = os.path.join(L.ROOT, e["path"])
        if os.path.isfile(fp) and _sha(fp) == e["sha256"]:
            out[e["sha256"]] = e
    return out


def _sha(p):
    """sha256 of a file of the index, or None when it disappeared after the walk listed it: a tree changing during a scan
    (the source's run 295, a queue releasing while suites and a commit ran) is scanned as it now stands, not crashed on."""
    try:
        return L.sha256(p)
    except FileNotFoundError:
        return None


def blocked_files(blocked):
    out = []
    for base, why in blocked:
        out += [(p, why) for p in _walk(base, ("input", "downloads", ".lake"), launch=True)]   # transcripts too
    return out


def _run_number(path):
    """0 for OPEN material outside the runs; the run's number for a file of a run directory."""
    m = re.search(r"/workspace-\d+/runs/(\d+)-", "/" + os.path.relpath(path, L.ROOT))
    return int(m.group(1)) if m else 0


def _ran(rd):
    """A run whose output/ can count as open: it was launched (a transcript on file) or checked (a check.json)."""
    return any(os.path.exists(os.path.join(rd, f)) for f in ("launch.log", "launch.jsonl", "check.json"))


def open_files(blocked, lines):
    """OPEN (the problem files without reviews/, the library, the claims, the rules, the tools, the harness), and the
    output/ of every run that is neither blocked nor under a line rule and was launched or checked. Never a packet."""
    blocked_runs = {os.path.realpath(os.path.join(L.ROOT, b)) for b, _ in blocked}
    blocked_runs |= {os.path.realpath(os.path.join(L.ROOT, b)) for b, _, _ in lines}
    out = []
    for base in OPEN:
        out += _walk(base, ("reviews", ".lake", "downloads"))
    for rd in L.run_dirs():   # the tests' throwaway runs (*-test-fixture) are not material, and would void the cache
        if rd not in blocked_runs and not rd.endswith("-test-fixture") and _ran(rd):
            out += _walk(os.path.relpath(os.path.join(rd, "output"), L.ROOT), ("scratch", "downloads", ".lake"))
    # A block beats an open root (the source's method change 58): a blocked path inside OPEN or inside an open run's
    # output/ is not open material, so its own text cannot excuse itself. A line rule's file stays open less its matching
    # lines (blocked_index).
    bases = [os.path.realpath(os.path.join(L.ROOT, b)) for b, _ in blocked]
    under = lambda p: any(p == b or p.startswith(b + os.sep) for b in bases)
    return [p for p in out if not under(os.path.realpath(p))]


def _fingerprint(files):
    h = hashlib.sha256()
    for p in sorted(files):
        try:
            st = os.stat(p)
            h.update(f"{os.path.relpath(p, L.ROOT)}\0{st.st_size}\0{st.st_mtime_ns}\n".encode())
        except OSError:
            pass
    h.update(open(__file__, "rb").read())
    return h.hexdigest()


def blocked_index(use_cache=True):
    """({sha256: [source, why]}, {12-word hash: [source, why]}): blocked files and blocked text, open material removed."""
    blocked, lines = rules()
    bf, of = blocked_files(blocked), open_files(blocked, lines)
    partial = [(p, rx, why) for base, rx, why in lines for p in _walk(base, ("input", "downloads", ".lake"))]
    ex, rf = os.path.join(L.ROOT, EXCEPTIONS), os.path.join(L.ROOT, RULES)
    excepted = [os.path.join(L.ROOT, e["path"]) for e in _exception_entries()]
    fp = _fingerprint([p for p, _ in bf] + of + [p for p, _, _ in partial] + excepted
                      + [f for f in (ex, rf) if os.path.isfile(f)])
    cache = os.path.join(L.ROOT, CACHE)
    if use_cache:   # never on the launch path: the cache is orchestrator-writable state (the outside review's F5)
        try:
            with open(cache) as f:
                c = json.load(f)
            if c.get("fingerprint") == fp:
                return c["hashes"], c["text"]
        except (OSError, ValueError):
            pass
    exc = exceptions()
    hashes, text = {}, {}
    given = {}   # per blocked run: the 12-word runs of its own input/, which its transcripts quote back
    for p, why in bf:
        h = _sha(p)
        if h is None or h in exc:
            continue
        rel = os.path.relpath(p, L.ROOT)
        hashes.setdefault(h, [rel, why, INF])
        t = _text(p, strict=True)   # blocked text too large to index fails the scan (TooLarge), never silently
        if not t:
            continue
        sh = _hashes(t)
        if os.path.basename(p).startswith("launch"):   # a transcript: what the run produced, not what it was given
            rd = os.path.dirname(p)
            if rd not in given:
                given[rd] = set()
                for q in _walk(os.path.relpath(os.path.join(rd, "input"), L.ROOT), ()):
                    tq = _text(q)
                    if tq:
                        given[rd] |= _hashes(tq)
                given[rd] |= _hashes(_text(os.path.join(rd, "BRIEF.md")) or "")
            sh -= given[rd]
        for s in sh:
            text.setdefault(s, [rel, why, INF])
    for p, rx, why in partial:
        t = _text(p, strict=True)
        if t and _sha(p) not in exc:
            rel = os.path.relpath(p, L.ROOT)
            for line in t.splitlines():
                if rx.search(line):
                    for s in _hashes(line):
                        text.setdefault(s, [rel, why, INF])
    def seen(e, n):   # the earliest open appearance (0 = outside the runs): open for every later run's packet
        e[2] = min(e[2], n)
    line_rules = {}   # an open file under a line rule: its matching lines are not open material (a block beats an open root)
    for p, rx, _ in partial:
        line_rules.setdefault(os.path.realpath(p), []).append(rx)
    for p in of:
        h = _sha(p)
        if h is None or h in exc:   # gone since the walk; or an excepted file, neither blocked nor open
            continue
        n = _run_number(p)
        e = hashes.get(h)
        if e is not None:
            seen(e, n)
        t = _text(p)
        rxs = line_rules.get(os.path.realpath(p))
        if t and rxs:
            t = "\n".join(l for l in t.splitlines() if not any(rx.search(l) for rx in rxs))
        if t:
            for s in _hashes(t):
                e = text.get(s)
                if e is not None:
                    seen(e, n)
    os.makedirs(os.path.dirname(cache), exist_ok=True)
    with open(cache + ".tmp", "w") as f:
        json.dump({"fingerprint": fp, "hashes": hashes, "text": text}, f)
    os.replace(cache + ".tmp", cache)
    return hashes, text


def packet_files(rd):
    out = [os.path.join(rd, f) for f in ("BRIEF.md", "HARNESS-NOTE.md") if os.path.isfile(os.path.join(rd, f))]
    for dp, dn, fn in os.walk(os.path.join(rd, "input")):
        out += [os.path.join(dp, f) for f in fn]
    return sorted(out)


def findings(rd, use_cache=True):
    """(errors, warnings) for the packet of run directory rd. bin/lint-brief --packet, the launch path, passes
    use_cache=False: the index is rebuilt from the files themselves."""
    verdicts = verdict_rule()
    if rules() == ([], []) and verdicts is None:   # nothing to find: no index built, nothing written under .claude/state/
        return [], []
    exc = exceptions()
    hashes, text = blocked_index(use_cache) if rules() != ([], []) else ({}, {})
    name_re = _name_re(*rules())
    me = _run_number(os.path.join(rd, "BRIEF.md")) or INF   # only material older than the packet's run excuses it
    blocked = lambda e: e[2] >= me
    errs, warns = [], []
    for p in packet_files(rd):
        rel = os.path.relpath(p, rd)
        h = L.sha256(p)
        if h in exc:
            continue
        if h in hashes and blocked(hashes[h]):
            errs.append(f"{rel}: byte-identical to blocked {hashes[h][0]} ({hashes[h][1]})")
            continue
        try:
            t = _text(p, strict=True)
        except TooLarge:
            errs.append(f"{rel}: a text file over {MAX_BYTES} bytes, too large to scan; split it or leave it out")
            continue
        if t is None:   # binary: compared by hash above, nothing to read
            continue
        srcs = {}
        w = _words(t)
        for i in range(len(w) - N + 1):
            s = " ".join(w[i:i + N])
            k = hashlib.blake2b(s.encode(), digest_size=8).hexdigest()
            if k in text and blocked(text[k]):
                srcs.setdefault(tuple(text[k][:2]), s)
        for (src, why), s in sorted(srcs.items()):
            errs.append(f"{rel}: shares text with blocked {src} ({why}): \"…{s}…\"")
        for n, line in enumerate(t.splitlines(), 1):
            v = verdicts.search(line) if verdicts else None
            if v:
                errs.append(f"{rel}:{n}: route-verdict word {v.group(0)!r}: no worker receives rankings or evaluations of "
                            "routes; cut the line, or the user excepts the file")
            m = name_re.search(line) if name_re else None
            if m:
                warns.append(f"{rel}:{n}: names blocked material ({m.group(0)!r}); its existence reaches the worker")
    return errs, warns
