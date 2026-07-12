---
name: anti-fabrication
description: Use whenever reporting financial figures, to guarantee every number is real. Numbers come from the toolkit's Decimal math and trace to source rows — never estimated or invented.
---

# Anti-Fabrication

For money, a wrong number is worse than no number. These rules are non-negotiable, and the `figures-guardian` agent enforces them before any output is shown.

## Never

- Never compute a total, percentage, or average in your head — model arithmetic is not trustworthy for money.
- Never report a figure that isn't produced by the toolkit (`aggregate`, `anomalies`, `reconcile`) from `Decimal` math.
- Never guess a category, amount, or date to fill a gap. Uncategorized or unparseable rows are **flagged for the user**, not invented.

## Always

- Compute with the toolkit; amounts are `Decimal`.
- **Tie every reported number to source rows** — a category total is the sum of specific transactions; an anomaly cites the underlying transaction(s).
- **Check the invariants** (below). If any fails, stop and re-run rather than shipping the number.
- When something can't be verified, say so plainly.

## The invariants

- `income − expenses = net`
- the sum of `by_category` values equals the **net of all transactions**
- the report's transaction count equals the count parsed from the file

## References

- **`references/verification-checklist.md`** — the guardian's step-by-step check with a worked pass and a worked reject, why the `by_category` invariant is the *net* (signed) and not gross spend, and how skipped/uncategorized rows must be accounted for.
- **`references/reconciliation-logic.md`** — how `reconcile(a, b)` matches (equal amount, date within tolerance, first unused b-row), the count invariant it must satisfy, and worked matched / only-in-a / only-in-b examples.
