#!/usr/bin/env bash
# Green Keeper Stop hook: block turn-end on NEWLY-introduced red (baseline was green),
# up to maxAttempts, then yield. Exit-code based. Zero network.
set -uo pipefail
INPUT=$(cat)
PROJ="${CLAUDE_PROJECT_DIR:-$(printf '%s' "$INPUT" | jq -r '.cwd // "."')}"
CFG="$PROJ/.green-keeper/config.json"
STATE="$PROJ/.green-keeper/state"
[ -f "$CFG" ] || exit 0            # not configured -> no-op
mkdir -p "$STATE"

ENFORCE=$(jq -r 'if .enforce == false then "false" else "true" end' "$CFG")
MAXATT=$(jq -r '.maxAttempts // 3' "$CFG")
TYPECHECK=$(jq -r '.typecheck // empty' "$CFG")
QUICK=$(jq -r '.quickTest // .test // empty' "$CFG")
BASELINE=$(cat "$STATE/baseline" 2>/dev/null || echo green)

red=0; detail=""
if [ -n "$TYPECHECK" ] && ! ( cd "$PROJ" && eval "$TYPECHECK" ) >/dev/null 2>&1; then red=1; detail="type errors"; fi
if [ -n "$QUICK" ]     && ! ( cd "$PROJ" && eval "$QUICK" )     >/dev/null 2>&1; then red=1; detail="${detail:+$detail, }failing tests"; fi

if [ "$red" -eq 0 ]; then : > "$STATE/attempts"; exit 0; fi           # green -> allow stop, reset
[ "$ENFORCE" = "true" ]  || { echo "Green Keeper: $detail (enforce off)." >&2; exit 0; }
[ "$BASELINE" = "green" ] || { echo "Green Keeper: pre-existing $detail — not blocking." >&2; exit 0; }

att=$(cat "$STATE/attempts" 2>/dev/null || echo 0); att=$((att + 1)); echo "$att" > "$STATE/attempts"
if [ "$att" -gt "$MAXATT" ]; then
  : > "$STATE/attempts"
  echo "Green Keeper: still red ($detail) after $MAXATT attempts — leaving it for you." >&2
  exit 0
fi
MSG="Green Keeper: this turn introduced $detail. Run the /green workflow now — fix with a minimal change (NO fake-green: never weaken/skip a test or silence an error) and re-run until green. (attempt $att/$MAXATT)"
jq -Rn --arg r "$MSG" '{"decision":"block","reason":$r,"hookSpecificOutput":{"hookEventName":"Stop","additionalContext":$r}}'
exit 0
