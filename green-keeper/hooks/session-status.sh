#!/usr/bin/env bash
# Green Keeper SessionStart: record baseline green/red, reset attempt counter, inject a status line.
# Zero network. Reads .green-keeper/config.json; runs typecheck + quickTest by exit code only.
set -uo pipefail
INPUT=$(cat)
PROJ="${CLAUDE_PROJECT_DIR:-$(printf '%s' "$INPUT" | jq -r '.cwd // "."')}"
SRC=$(printf '%s' "$INPUT" | jq -r '.source // "startup"')
CFG="$PROJ/.green-keeper/config.json"
STATE="$PROJ/.green-keeper/state"

ctx() { jq -Rn --arg s "$1" '{"hookSpecificOutput":{"hookEventName":"SessionStart","additionalContext":$s}}'; }

# Only run on real session starts/resumes, not every compaction.
case "$SRC" in startup|resume) ;; *) exit 0 ;; esac

if [ ! -f "$CFG" ]; then
  ctx "Green Keeper: no config yet — run /green-setup to enable automatic green checks."
  exit 0
fi
mkdir -p "$STATE"
: > "$STATE/attempts"   # reset the Stop-hook attempt counter each session

TYPECHECK=$(jq -r '.typecheck // empty' "$CFG")
QUICK=$(jq -r '.quickTest // .test // empty' "$CFG")
red=0; detail=""
if [ -n "$TYPECHECK" ] && ! ( cd "$PROJ" && eval "$TYPECHECK" ) >/dev/null 2>&1; then red=1; detail="type errors"; fi
if [ -n "$QUICK" ]     && ! ( cd "$PROJ" && eval "$QUICK" )     >/dev/null 2>&1; then red=1; detail="${detail:+$detail, }failing tests"; fi

if [ "$red" -eq 0 ]; then
  echo "green" > "$STATE/baseline"
  ctx "Green Keeper: green ✓ (types + tests clean)."
else
  echo "red" > "$STATE/baseline"
  ctx "Green Keeper: starting with $detail. Run /green to fix — the Stop check won't nag about pre-existing red."
fi
exit 0
