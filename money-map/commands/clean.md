---
description: Turn messy or multi-format CSV exports into one clean, categorized, analysis-ready file.
argument-hint: "<path-or-paths.csv>"
---

# Clean

Produce one tidy dataset from raw exports. Arguments: `$ARGUMENTS`

## Workflow
1. Parse each input with the toolkit's `parse_report` (map columns via `statement-parsing`); dates and amounts are normalized through `Decimal`.
2. Categorize with the rules in `money/categories.json`.
3. Write a single `categorized.csv` to `money/output/<name>/` with consistent columns (date, description, amount, category, account, source-file).
4. Collect `.skipped` from every input — rows that couldn't be parsed (malformed amount/date) or were ambiguous (both debit and credit populated). List them for the user to fix — never drop or fabricate them silently.

Never access the network.
