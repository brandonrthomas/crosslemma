#!/usr/bin/python3
"""scripts/docs/check_docs.py [ROOT] [--only NAME ...]

The documentation's integrity, checked from the files on every run. It rebuilds the graph of rules, lessons, tools,
templates, pages and tags (nothing is stored, so the graph cannot drift from the files) and reports every broken edge:
  links      a relative link in a published Markdown file whose file, or `#anchor` (GitHub's heading slugs), is missing
  lessons    a pointer `→ **label**` or `LESSONS.md "label"` (in any published file, tool, hook or test) that names no
             lesson, and a lesson nothing points at
  coverage   a tool in bin/ with no reference page or no line in the tools index; a template not listed in
             templates/README.md; a page under docs/ that docs/index.md does not reach
  generated  a generated page that differs from what scripts/docs/gen_reference.py writes now, or a stale extra one
  changelog  a kit-v* tag with no KIT-CHANGELOG.md heading, or a heading with no tag but the newest, which a methods
             session writes before its tag (only where .git holds kit-v* tags; a clone of the public copy has none)
  sanitize   a home-directory path, a private domain, a local workspace name or a session name in a published file
A lesson label is the bold text after "- " or "N. " that ends with "** →", across line wraps; a pointer names it in
full or by its opening words (backticks ignored). Published means every file but HANDOFF.md and history/ (the kit's
working record, which the public export leaves out). Exit 0 and no output when everything holds; otherwise one line per
problem and exit 1. Stdlib only.
"""
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gen_reference  # noqa: E402

CHECKS = ("links", "lessons", "coverage", "generated", "changelog", "sanitize")
SKIP_DIRS = {".git", "history", "handoffs", "__pycache__", "state", "node_modules"}
UNPUBLISHED = {"HANDOFF.md"}
# Spelled so that this file does not match its own patterns.
SANITIZE = [
    # Homebrew's standard prefix and the sandbox tests' escape probes are not anyone's home.
    (re.compile(r"/home/(?!linuxbrew\b|escape-)[a-z_][a-z0-9_-]*"), "a home-directory path"),
    (re.compile(r"branclou[d]|branbo[x]|\bntf[y]\."), "a private domain"),
    (re.compile(r"\bmaths-2-uniform-directio[n]\b|\bmaths-analys[t](?:-\d+)?\b|\bmaths-[2]\b(?!-)|\bmaths-[2]-[0-9a-z]{2}\b"), "a local workspace name"),
    (re.compile(r"~/workspac[e]/(?!<)[\w.-]+"), "a local workspace path"),
    (re.compile(r"\bmaths-kit-(?:[0-9a-f]{2}|b\d+|builder-\d+)\b|\bud-orchestrato[r]-\d+|\bschur-number[s]-\d+\b|"
                r"\bkit-revie[w]-\d+\b"), "a session or instance name"),
]
SANITIZE_ALLOW = "sanitize: fixture"
LINK = re.compile(r"\[([^\]]*)\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
POINTER = re.compile(r"→ \*\*((?:(?!\*\*).)+?)\*\*")
LABEL = re.compile(r"^(?:- |\d+\. )\*\*((?:(?!\*\*).)+?)\*\*\s*→", re.M | re.S)


def published(root):
    for d, dirs, files in os.walk(root):
        dirs[:] = sorted(x for x in dirs if x not in SKIP_DIRS and not (d == root and x.startswith("workspace-")))
        for f in sorted(files):
            rel = os.path.relpath(os.path.join(d, f), root)
            if rel in UNPUBLISHED or f.endswith((".pyc", ".png", ".jpg", ".gz", ".olean")):
                continue
            yield rel


def read(root, rel):
    try:
        with open(os.path.join(root, rel), encoding="utf-8") as f:
            return f.read()
    except (UnicodeDecodeError, OSError):
        return None


def norm(s):
    return " ".join(s.replace("`", "").split())


def lesson_labels(text):
    return [norm(m.group(1)) for m in LABEL.finditer(text)]


def resolves(ref, labels):
    r = norm(ref)
    return any(l == r or l.startswith(r) for l in (norm(x) for x in labels))


def strip_code(md):
    md = re.sub(r"^```.*?^```", "", md, flags=re.M | re.S)
    return re.sub(r"`[^`\n]*`", "", md)


def anchors(md):
    out, seen = set(), {}
    for m in re.finditer(r"^#{1,6}\s+(.+?)\s*#*\s*$", re.sub(r"^```.*?^```", "", md, flags=re.M | re.S), re.M):
        t = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", m.group(1)).lower()
        slug = re.sub(r"[^\w\- ]", "", t).replace(" ", "-")
        n = seen.get(slug, 0)
        seen[slug] = n + 1
        out.add(slug if n == 0 else f"{slug}-{n}")
    out |= set(re.findall(r'<a\s+(?:id|name)="([^"]+)"', md))
    return out


def check_links(root, files):
    probs = []
    for rel in files:
        if not rel.endswith(".md"):
            continue
        text = read(root, rel)
        if text is None:
            continue
        for m in LINK.finditer(strip_code(text)):
            target = m.group(2)
            if re.match(r"^[a-z]+:", target):
                continue
            path, _, frag = target.partition("#")
            dest = os.path.normpath(os.path.join(os.path.dirname(rel), path)) if path else rel
            full = os.path.join(root, dest)
            if dest.startswith("..") or not os.path.exists(full):
                probs.append(f"{rel}: link to {target}: no such file")
            elif frag and dest.endswith(".md") and frag not in anchors(read(root, dest) or ""):
                probs.append(f"{rel}: link to {target}: no heading #{frag} in {dest}")
    return probs


def check_lessons(root, files):
    les = read(root, "LESSONS.md")
    if les is None:
        return []
    labels = lesson_labels(les)
    probs, pointed = [], set()
    srcs = [f for f in files if f.endswith(".md") or f.startswith(("bin/", "tests/", ".claude/hooks/"))]
    for rel in srcs:
        text = read(root, rel)
        if text is None:
            continue
        if rel.endswith(".md"):                          # a pointer shown as an example in code is not a pointer
            text = re.sub(r"^```.*?^```", "", text, flags=re.M | re.S)
            text = re.sub(r"`[^`\n]*`", lambda m: "" if re.search(r"→|LESSONS\.md", m.group(0)) else m.group(0), text)
        else:
            text = re.sub(r"\n[ \t]*#+ ?", "\n", text)   # a citation wrapped across comment lines
        flat = " ".join(text.split())
        # Tests cite lessons as LESSONS.md "label" only; their fixtures hold arrow pointers that are data.
        refs = ([] if rel.startswith("tests/") else POINTER.findall(flat)) + gen_reference.LESSON_CITE.findall(flat)
        for ref in refs:
            ok = [l for l in labels if l == norm(ref) or l.startswith(norm(ref))]
            if not ok:
                probs.append(f"{rel}: → **{norm(ref)}** names no lesson")
            elif rel != "LESSONS.md":
                pointed.update(ok)
    for l in labels:
        if l not in pointed:
            probs.append(f"LESSONS.md: nothing points at lesson **{l}**")
    return probs


def reachable(root, start):
    seen, todo = set(), [start]
    while todo:
        rel = todo.pop()
        if rel in seen or not os.path.isfile(os.path.join(root, rel)):
            continue
        seen.add(rel)
        for m in LINK.finditer(strip_code(read(root, rel) or "")):
            p = m.group(2).partition("#")[0]
            if p and not re.match(r"^[a-z]+:", p):
                d = os.path.normpath(os.path.join(os.path.dirname(rel), p))
                if d.endswith(".md") and d.startswith("docs"):
                    todo.append(d)
    return seen


def check_coverage(root, files):
    probs = []
    idx = read(root, "docs/reference/tools/README.md") or ""
    for n in gen_reference.tools(root):
        if not os.path.isfile(os.path.join(root, "docs", "reference", "tools", n + ".md")):
            probs.append(f"bin/{n}: no reference page docs/reference/tools/{n}.md")
        elif f"]({n}.md)" not in idx:
            probs.append(f"bin/{n}: not in docs/reference/tools/README.md")
    treadme = read(root, "templates/README.md")
    if treadme is not None:
        for rel in files:
            if rel.startswith("templates/") and rel != "templates/README.md":
                if f"`{rel[len('templates/'):]}`" not in treadme:
                    probs.append(f"{rel}: not listed in templates/README.md")
    if os.path.isfile(os.path.join(root, "docs", "index.md")):
        reach = reachable(root, "docs/index.md")
        for rel in files:
            if rel.startswith("docs/") and rel.endswith(".md") and rel not in reach:
                probs.append(f"{rel}: not reached from docs/index.md")
    return probs


def check_generated(root):
    probs, want = [], gen_reference.render(root)
    for rel, text in want.items():
        if read(root, rel) != text:
            probs.append(f"{rel}: differs from what scripts/docs/gen_reference.py writes now (regenerate it)")
    tdir = os.path.join(root, "docs", "reference", "tools")
    if os.path.isdir(tdir):
        for f in sorted(os.listdir(tdir)):
            if f"docs/reference/tools/{f}" not in want:
                probs.append(f"docs/reference/tools/{f}: no tool of that name (a stale generated page)")
    return probs


def check_changelog(root):
    if not os.path.isdir(os.path.join(root, ".git")):
        return []
    tags = set(subprocess.run(["git", "-C", root, "tag", "-l", "kit-v*"], capture_output=True, text=True).stdout.split())
    if not tags:   # a clone of the public copy (one commit, no tags): nothing to compare the headings with
        return []
    order = re.findall(r"^## (kit-v[0-9][\w.]*)", read(root, "KIT-CHANGELOG.md") or "", re.M)
    heads = set(order)
    # The newest entry (the first heading) may be untagged: a methods session writes it, then commits and tags. Any other
    # untagged heading is a tag forgotten; the handoff's preflight (`git describe --tags --exact-match`) catches an
    # untagged commit after the fact.
    pending = {order[0]} if order and order[0] not in tags else set()
    return ([f"KIT-CHANGELOG.md: tag {t} has no heading" for t in sorted(tags - heads)]
            + [f"KIT-CHANGELOG.md: heading {h} has no tag" for h in sorted(heads - tags - pending)])


def check_sanitize(root, files):
    probs = []
    for rel in files:
        text = read(root, rel)
        if text is None:
            continue
        for i, line in enumerate(text.splitlines(), 1):
            if SANITIZE_ALLOW in line:
                continue
            for pat, what in SANITIZE:
                for m in pat.finditer(line):
                    probs.append(f"{rel}:{i}: {what} ({m.group(0)})")
    return probs


def check(root, only=None):
    files = list(published(root))
    sel = [only] if isinstance(only, str) else (only or CHECKS)
    probs = []
    for name in sel:
        if name == "links":
            probs += check_links(root, files)
        elif name == "lessons":
            probs += check_lessons(root, files)
        elif name == "coverage":
            probs += check_coverage(root, files)
        elif name == "generated":
            probs += check_generated(root)
        elif name == "changelog":
            probs += check_changelog(root)
        elif name == "sanitize":
            probs += check_sanitize(root, files)
    return probs


if __name__ == "__main__":
    args = sys.argv[1:]
    only = []
    while "--only" in args:
        i = args.index("--only")
        only.append(args[i + 1])
        del args[i:i + 2]
    r = os.path.abspath(args[0]) if args else os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    p = check(r, only or None)
    for line in p:
        print(line)
    sys.exit(1 if p else 0)
