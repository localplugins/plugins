---
name: anomaly-patterns
description: Use when flagging anomalies in transaction data. Defines what money-map surfaces — duplicates, outliers, and changes in recurring charges.
---

# Anomaly Patterns

The toolkit's `anomalies()` and `aggregate()["recurring"]` do the detection with deterministic `Decimal` math. Your job is to explain what they found in plain English and cite the rows behind each flag.

## What money-map flags

- **Duplicate** — the same charge twice: identical date, amount, and normalized description. Often a double-charge worth disputing.
- **Outlier** — an unusually large expense for its category (magnitude more than 3× the category's median, and only in categories with at least 4 outflows). Could be legitimate or an error — surface it, don't judge.
- **Recurring change** — a recurring charge whose amount changed, or a new recurring charge that started. Compare this period's recurring set (`aggregate()["recurring"]`) to prior periods.

## How to report

- Show the specific transaction(s) behind each flag: date, amount, description.
- Explain *why* it was flagged in one line.
- **Never claim fraud.** Describe the pattern; let the user decide.

## References

- **`references/detection-logic.md`** — the exact rules `_duplicates`, `_outliers`, and `_recurring` use (thresholds, the median-based outlier test, the ≥3-month / 5%-band recurring test), with sample rows for each and notes on what deliberately does *not* trip a flag.
