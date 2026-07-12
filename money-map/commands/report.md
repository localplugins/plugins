---
description: Generate a shareable report (spending report / cash-flow summary) from an analyzed export.
argument-hint: "<path-to-export-or-output-folder>"
---

# Report

Produce a clean, shareable summary. Arguments: `$ARGUMENTS`

## Workflow
1. Use the analyzed data (run `/understand` first if needed) — all figures come from the toolkit.
2. Write `report.md` to `money/output/<name>/`: totals (income, expenses, net), spend by category (with each category's share), month-over-month, and top recurring charges.
3. Delegate to the `figures-guardian`: every number must reconcile and trace to source rows.
4. Keep it plain-English and skimmable; note the date range and transaction count.

Never invent a figure. Never access the network.
