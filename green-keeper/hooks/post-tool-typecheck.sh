#!/usr/bin/env bash
# Green Keeper PostToolUse (opt-in): after a code edit, run the fast typecheck and surface new type errors.
# Report-only (cannot block). Off unless config.postToolUseTypecheck == true. Zero network.
set -uo pipefail
INPUT=$(cat)
PROJ="${CLAUDE_PROJECT_DIR:-$(printf '%s' "$INPUT" | jq -r '.cwd // "."')}"
CFG="$PROJ/.green-keeper/config.json"
[ -f "$CFG" ] || exit 0
[ "$(jq -r '.postToolUseTypecheck // false' "$CFG")" = "true" ] || exit 0
TYPECHECK=$(jq -r '.typecheck // empty' "$CFG")
[ -n "$TYPECHECK" ] || exit 0
if ! out=$( cd "$PROJ" && eval "$TYPECHECK" 2>&1 ); then
  tail=$(printf '%s' "$out" | tail -5)
  jq -Rn --arg s "Green Keeper: that edit left type errors — consider fixing before moving on:
$tail" '{"hookSpecificOutput":{"hookEventName":"PostToolUse","additionalContext":$s}}'
fi
exit 0
