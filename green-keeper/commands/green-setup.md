---
description: Detect this repo's test and type/compile commands and cache them to .green-keeper/config.json so green-keeper (and its hooks) know how to run.
argument-hint: "[--test <cmd>] [--typecheck <cmd>] [--quick <cmd>]"
---

# Green Setup

Configure Green Keeper for this repo. Arguments: `$ARGUMENTS`

## Steps
1. Apply the `runner-detection` skill to infer the `test`, `typecheck`, and (if possible) a fast `quickTest` command from the project files. Honor any explicit `--test`/`--typecheck`/`--quick` overrides in the arguments.
2. Show the detected commands and **confirm with the user** before saving (these will run automatically via hooks).
3. Write `.green-keeper/config.json` with the schema from `runner-detection` (`test`, `typecheck`, `quickTest`, `enforce: true`, `maxAttempts: 3`, `postToolUseTypecheck: false`). Never overwrite an existing config without confirming.
4. Tell the user to add `.green-keeper/state/` to their `.gitignore` (config.json itself is safe to commit and share with the team).
5. Do a quick sanity run of `typecheck` and `quickTest` and report whether the repo currently starts green or red.

Never access the network.
