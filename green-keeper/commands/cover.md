---
description: Write or update behavioral tests for the code you just changed, and verify they actually exercise the change.
argument-hint: "[file-or-path...] (default: your uncommitted changes)"
---

# Cover

Add real tests for what changed. Arguments: `$ARGUMENTS`

## Workflow
1. **Config.** Read `.green-keeper/config.json` (run `/green-setup` first if missing).
2. **Scope.** Determine the changed code to cover: the paths in the arguments, else the working-tree diff (`git diff` + staged).
3. **Write tests.** For each changed unit, delegate to the `test-writer` subagent (behavioral tests per `test-quality`, matching the repo's framework/layout).
4. **Guard.** Delegate to the `green-guardian` subagent for revert-verification — every new/updated test must fail on the pre-change code and pass after. Reworked if not.
5. **Run.** Execute the new tests; confirm green.
6. **Report.** List the behaviors now covered and where the tests live.

Never write tautological or mock-only tests. Never access the network.
