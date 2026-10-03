"""The instance's environment file, kit-env.json (kit-v0.5; the user's "we need to generalize", 2026-10-01). Stdlib only.

One file says what this machine offers the kit, so nothing about it is hard-coded in the tools or the hook. It is the
user's: the hook refuses the orchestrator any write to it (LESSONS.md "The environment files are the user's").
Every field is optional:

  {
    "worker_path":   ["/usr/local/bin"],         directories mounted read-only for every worker and put on its PATH, after
                                                 the modules' and before /usr/bin:/bin
    "claude":        "claude",                   the Claude Code CLI, by name on PATH or absolute path
    "codex":         "codex",                    the Codex CLI the same way; its real binary is found from there
    "codex_bin_dir": null,                       the directory of Codex's real binary, when it cannot be found
    "model_families": {"Google": ["gemini"]},    added to the built-in table (Anthropic, OpenAI) that decides the
                                                 cross-family referee rule (RULES.md §7)
    "locked_dir":    "~/.local/state/crosslemma/<name>/locked",   the locked directory (answer keys, label maps),
                                                 outside the instance so no search from it walks there; bin/new-workspace
                                                 sets it; without it an older instance keeps <root>/data/locked
    "modules": {
      "pari": {
        "binds":  ["~/opt/pari", {"src": "...", "dest": "/opt/kit/bin/x"}],   read-only mounts (dest: the source's own path)
        "path":   ["~/opt/pari/bin"],            PATH additions, ahead of worker_path
        "env":    {"GP_DATA_DIR": "~/opt/pari/data"},
        "check":  "gp --version-short",          the self-test bin/check-env runs inside a worker's sandbox
        "brief":  "PARI/GP: `gp -q` ...",        one line every brief carries about the module
        "licence_servers": [{"host": "lic.example.org", "port": 27000}]
      }
    }
  }

`~` is the user's home and `<root>` the instance. A module with `licence_servers` is given only to a run whose launch
asked for it (bin/run-external --module NAME, bound in the approval); the worker then reaches each named host and port and
nothing else, through a relay on the host. Every other module is mounted for every worker.

Refused, whoever wrote the file, with a problem line: a mount source or PATH entry that is the root, a home directory or one
holding it, the instance or any directory inside or holding it, or a credential directory (~/.ssh, ~/.gnupg, ~/.claude,
~/.codex, ~/.config, ~/.aws, ~/.local/share/keyrings); a licence port outside 1024–65535; a host that is not a plain name.
A module with a missing mount source is not mounted, and says so. A `locked_dir` that is the root, a home directory, a
credential directory, the instance or inside or holding it, is refused, and the instance keeps <root>/data/locked.

With no kit-env.json, an instance made before kit-v0.5 keeps its modules exactly: .kit-lean (and <root>/lean) becomes the
module `lean`, .kit-sage the module `sage`.
"""
import json
import os
import re

FAMILY_WORDS = (("Anthropic", ("anthropic", "opus", "fable", "sonnet", "haiku", "claude")),
                ("OpenAI", ("openai", "gpt", "sol", "astra", "codex")))
CREDENTIAL_DIRS = (".ssh", ".gnupg", ".claude", ".codex", ".config", ".aws", ".netrc", ".local/share/keyrings")
HOST_RE = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9.-]{0,251}[A-Za-z0-9])?$")
ENV_NAME_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


class Module:
    def __init__(self, name):
        self.name = name
        self.binds = []            # [(src, dest)]
        self.path = []
        self.env = {}
        self.check = ""
        self.brief = ""
        self.licence_servers = []  # [(host, port)]

    @property
    def on_request(self):
        return bool(self.licence_servers)


class Env:
    def __init__(self, root):
        self.root = root
        self.worker_path = []
        self.claude = "claude"
        self.codex = "codex"
        self.codex_bin_dir = None
        self.families = [(f, tuple(w)) for f, w in FAMILY_WORDS]
        self.modules = {}
        self.problems = []
        self.locked_dir = os.path.join(root, "data", "locked")   # an instance made before kit-v0.6.9


def default_locked_dir(root):
    """Where bin/new-workspace puts a new instance's locked directory: outside every workspace, by the instance's name
    (pending item P-9, user 2026-10-01)."""
    return os.path.join(home(), ".local", "state", "crosslemma", os.path.basename(os.path.realpath(root)), "locked")


def home():
    return os.path.realpath(os.path.expanduser("~"))


def expand(p, root):
    return os.path.expanduser(str(p).replace("<root>", root))


def unsafe(src, root):
    """Why `src` may not be mounted for workers, or None."""
    r = os.path.realpath(src)
    h, rt = home(), os.path.realpath(root)
    if r == "/":
        return "the root"
    if r == h or h.startswith(r + os.sep):
        return "a home directory, or a directory holding one"
    if os.path.dirname(r) == "/home" or r == "/home":
        return "a home directory, or a directory holding one"
    if os.path.abspath(src) == os.path.join(rt, "lean"):
        return None   # the instance's library link (bin/new-workspace --lean), mounted at its own path as it always was
    shims = os.path.join(rt, ".claude", "sandbox") + os.sep
    if r.startswith(shims) and os.path.isfile(r):
        return None   # the kit's own shims (the ledger shim, the Sage shim), which the hook has always mounted
    if r == rt or rt.startswith(r + os.sep) or r.startswith(rt + os.sep):
        # <root>/lean is a link to a library outside the instance; its target is checked, not the link
        return "the instance, or a directory inside or holding it"
    for c in CREDENTIAL_DIRS:
        cd = os.path.join(h, c)
        if r == cd or r.startswith(cd + os.sep):
            return f"a credential directory (~/{c})"
    return None


def _module(name, spec, root, problems):
    m = Module(name)
    if not isinstance(spec, dict):
        problems.append(f"{name}: a module is an object")
        return None
    for b in spec.get("binds", []):
        src, dest = (b.get("src"), b.get("dest")) if isinstance(b, dict) else (b, None)
        if not src:
            problems.append(f"{name}: a bind with no source")
            return None
        s = expand(src, root)
        why = unsafe(s, root)
        if why:
            problems.append(f"{name}: refused mount source {src} ({why})")
            return None
        if not os.path.exists(s):
            problems.append(f"{name}: mount source {src} does not exist; module not mounted")
            return None
        m.binds.append((s, dest or s))
    for p in spec.get("path", []):
        e = expand(p, root)
        if unsafe(e, root):
            problems.append(f"{name}: refused PATH entry {p}")
            return None
        m.path.append(e)
    for k, v in (spec.get("env") or {}).items():
        if not ENV_NAME_RE.match(str(k)) or k in ("PATH", "HOME", "LD_PRELOAD", "LD_LIBRARY_PATH"):
            problems.append(f"{name}: refused environment variable {k}")
            return None
        m.env[k] = expand(v, root)
    m.check = str(spec.get("check", ""))
    m.brief = str(spec.get("brief", ""))
    for srv in spec.get("licence_servers", []):
        host, port = (srv.get("host"), srv.get("port")) if isinstance(srv, dict) else (None, None)
        if not (isinstance(host, str) and HOST_RE.match(host)) or not (isinstance(port, int) and 1024 <= port <= 65535):
            problems.append(f"{name}: refused licence server {srv!r} (a plain host name and a port 1024-65535)")
            return None
        if any(p == port for _, p in m.licence_servers):
            problems.append(f"{name}: two licence servers on port {port} (each is one listener on 127.0.0.1 in the sandbox)")
            return None
        m.licence_servers.append((host, port))
    return m


def _old_modules(root, problems):
    """.kit-lean / .kit-sage of an instance made before kit-v0.5, as the hook mounted them."""
    out = {}

    def read(name):
        try:
            with open(os.path.join(root, name)) as f:
                return f.read().strip()
        except OSError:
            return ""
    lean_dir = os.path.join(root, "lean")
    elan = os.path.expanduser(read(".kit-lean") or "~/.elan")
    if os.path.isdir(lean_dir) and os.path.isdir(elan):
        spec = {"binds": [elan, lean_dir], "path": [elan + "/bin"],
                "env": {"ELAN_HOME": elan, "KIT_LEAN": lean_dir}}
        m = _module("lean", spec, root, problems)
        if m:
            out["lean"] = m
    sage = read(".kit-sage")
    shim = os.path.join(root, ".claude", "sandbox", "sage")
    if sage:
        s = os.path.expanduser(sage)
        if os.path.isfile(os.path.join(s, "bin", "sage")) and os.path.isfile(shim):
            m = _module("sage", {"binds": [s, {"src": shim, "dest": "/opt/kit/bin/sage"}], "env": {"KIT_SAGE": s}},
                        root, problems)
            if m:
                out["sage"] = m
    return out


def load(root, path=None):
    """The environment of the instance at `root`, from `path` (default <root>/kit-env.json)."""
    e = Env(root)
    p = path or os.path.join(root, "kit-env.json")
    d = {}
    if os.path.isfile(p):
        try:
            with open(p) as f:
                d = json.load(f)
            if not isinstance(d, dict):
                raise ValueError("not an object")
        except (OSError, ValueError) as x:
            e.problems.append(f"kit-env.json: unreadable ({x}); no module is mounted")
            return e
    e.claude = d.get("claude") or e.claude
    e.codex = d.get("codex") or e.codex
    e.codex_bin_dir = d.get("codex_bin_dir") or None
    for wp in d.get("worker_path", []):
        x = expand(wp, root)
        why = unsafe(x, root)
        if why:
            e.problems.append(f"worker_path: refused {wp} ({why})")
        elif os.path.isdir(x):
            e.worker_path.append(x)
        else:
            e.problems.append(f"worker_path: {wp} does not exist")
    for fam, words in (d.get("model_families") or {}).items():
        if isinstance(words, list) and all(isinstance(w, str) and w for w in words):
            e.families.append((str(fam), tuple(w.lower() for w in words)))
        else:
            e.problems.append(f"model_families: {fam} needs a list of words")
    if d.get("locked_dir"):
        x = os.path.realpath(expand(d["locked_dir"], root))
        why = unsafe(x, root) or ("not an absolute path" if not os.path.isabs(expand(d["locked_dir"], root)) else None)
        if why:
            e.problems.append(f"locked_dir: refused {d['locked_dir']} ({why}); <root>/data/locked is used")
        else:
            e.locked_dir = x
    e.modules = _old_modules(root, e.problems) if "modules" not in d else {}
    for name, spec in (d.get("modules") or {}).items():
        m = _module(name, spec, root, e.problems)
        if m:
            e.modules[name] = m
    return e


def model_family(model, env=None):
    """The family whose word is a whole token of the model's name, or a token's start followed by a digit (`gpt5`,
    `opus4`); never any prefix (P-12: "solar-1" was OpenAI's by "sol", "claudette" Anthropic's)."""
    m = (model or "").lower().strip("'\"")
    parts = [p for p in re.split(r"[^a-z0-9]+", m) if p]
    def has(w):
        return any(p == w or (p.startswith(w) and p[len(w):len(w) + 1].isdigit()) for p in parts)
    for fam, words in (env.families if env else [(f, w) for f, w in FAMILY_WORDS]):
        if any(has(w) for w in words):
            return fam
    return None


def granted_modules(env, granted=()):
    return [m for n, m in sorted(env.modules.items()) if not m.on_request or n in set(granted)]


def sandbox_parts(env, granted=()):
    """(bwrap args, PATH prefix ending in ':' or '', env args) for every module a worker gets, plus worker_path."""
    args, path, envargs = [], [], []
    for m in granted_modules(env, granted):
        for src, dest in m.binds:
            args += ["--ro-bind", src, dest]
        path += m.path
        for k, v in m.env.items():
            envargs += ["--setenv", k, v]
    for d in env.worker_path:
        args += ["--ro-bind", d, d]
        path.append(d)
    return args, "".join(p + ":" for p in path), envargs


def licence_endpoints(env, granted=()):
    return [hp for m in granted_modules(env, granted) for hp in m.licence_servers]


def brief_lines(env, granted=()):
    return "\n".join(f"- {m.name}: {m.brief}" for m in granted_modules(env, granted) if m.brief)


def hosts_text(endpoints):
    """The /etc/hosts a licence-granted worker sees: each licence host at 127.0.0.1, where its forwarder listens."""
    return "127.0.0.1 localhost\n" + "".join(f"127.0.0.1 {h}\n" for h, _ in endpoints if h != "localhost")


def python_etc(interp="/usr/bin/python3"):
    """The system Python's configuration directory, /etc/pythonX.Y for whichever version `interp` is, which both sandboxes
    mount read-only (it was mounted as /etc/python3.12 by name); None when that directory does not exist."""
    p = "/etc/" + os.path.basename(os.path.realpath(interp))
    return p if os.path.isdir(p) else None
