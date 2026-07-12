---
description: Reconcile two sets of records (e.g. bank vs books) and list every mismatch with the source rows.
argument-hint: "<file-a.csv> <file-b.csv>"
---

# Reconcile

Find what doesn't match between two exports. Arguments: `$ARGUMENTS`

## Workflow
1. Parse both files (the `analyst` maps columns via `statement-parsing`).
2. Run the toolkit's `reconcile(a, b)` — it matches transactions by amount + near date and returns `matched`, `only_in_a`, `only_in_b`.
3. Report the unmatched rows on each side with date, amount, and description, so the user can see exactly what's missing or extra.
4. Delegate the figures to the `figures-guardian` — counts must add up (matched + only_in_a = len(a)).

Never invent a match. Never access the network.
