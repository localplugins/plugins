---
description: Make everything green — fix failing tests and type/compile errors with minimal, real changes and re-run until the suite and types pass. No fake-green.
argument-hint: "[test|types|all] (default: all)"
---

# Green

Turn red into green, for real. Arguments: `$ARGUMENTS`

## Workflow
1. **Config.** Read `.green-keeper/config.json`. If missing, run the `/green-setup` flow first (detect + confirm + write config).
2. **Detect red.** Run `typecheck` and `test` (or just the scope named in the argument). Collect the failing tests and type/compile errors.
3. **Fix each red item.** For each failure, delegate to the `fixer` subagent (smallest correct change, obeying `anti-fake-green`), then re-run that item. Iterate until it's green or genuinely stuck.
4. **Guard.** Delegate the accumulated diff to the `green-guardian` subagent. If it rejects anything (fake-green or a test not exercising real behavior), send it back to `fixer` and repeat.
5. **Prove green.** Re-run `typecheck` and `test`; confirm both actually pass.
6. **Report.** Summarize each root cause and the minimal fix. If anything remains red because it needs a human/product decision, say so plainly — never fake it.

Never weaken/skip a test or silence an error to pass. Never access the network.
