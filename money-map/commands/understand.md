---
description: Understand a bank or card export — categorize every transaction, summarize cash flow, and flag anomalies. The hero command.
argument-hint: "<path-to-export.csv>"
---

# Understand

Make sense of a financial export. Arguments: `$ARGUMENTS`

## Workflow
1. **Config.** Ensure `money/categories.json` exists; if not, run the `/money-setup` flow first.
2. **Analyze.** Delegate to the `analyst` subagent: detect the column mapping, then run the toolkit (`parse_report` → `categorize` → `aggregate` → `anomalies`) — all figures from `Decimal` math, never estimated.
3. **Surface skipped rows.** `parse_report` returns the clean transactions plus `.skipped` — rows that couldn't be parsed (malformed amount/date) or were ambiguous (both debit and credit populated). Flag these for the user; never drop or fabricate them silently.
4. **Surface uncategorized** transactions and propose new rules; never guess a category.
5. **Verify.** Delegate the draft to the `figures-guardian` subagent — it checks the invariants and that every number traces to source rows; if it rejects, redo and re-check.
6. **Write** to `money/output/<name>/`:
   - `categorized.csv` — every transaction with its category
   - `report.md` — plain-English summary (income, spend by category, net cash flow, recurring)
   - `anomalies.md` — flagged duplicates / outliers / recurring changes
   - `skipped.csv` — rows that couldn't be parsed (malformed/ambiguous), for the user to fix — written only when there are any
7. Summarize the highlights and list any skipped rows and uncategorized items for the user to resolve.

Never connect to the network or the user's accounts. Never invent a number.
