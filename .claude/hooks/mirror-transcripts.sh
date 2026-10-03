#!/usr/bin/env bash
# Mirror this project's Claude Code transcripts (main sessions + subagents) into the repo.
# Hooked on Stop / SubagentStop / SessionEnd / PreCompact. Ignores stdin. Copies
# ~/.claude/projects/<this project>/ (session .jsonl, <session>/subagents/*.jsonl + .meta.json)
# to <repo>/transcripts/claude-projects/. Additive: never deletes anything in the mirror.
set -u
ROOT=$(cd "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")/../.." && pwd)
# Claude Code names a project directory after its path, with every non-alphanumeric turned into "-".
SRC="$HOME/.claude/projects/$(printf '%s' "$ROOT" | sed 's/[^A-Za-z0-9]/-/g')"
DST="$ROOT/transcripts/claude-projects"
[ -d "$SRC" ] || exit 0
mkdir -p "$DST"
rsync -a --include='*/' --include='*.jsonl' --include='*.meta.json' --exclude='*' "$SRC/" "$DST/" 2>>"$DST/.rsync-errors" || exit 0
exit 0
