# Verification checklist

How the `figures-guardian` verifies a draft before it's shown, with worked pass/reject cases. The guardian re-runs the toolkit on the same parsed data and checks that the report's numbers match and reconcile — it does not trust the analyst's narrative.

---

## The four checks

1. **Provenance** — every figure in the report traces to toolkit output (`aggregate`, `anomalies`, `reconcile`), not to model arithmetic. When in doubt, re-run the function and compare.
2. **Invariants** — all three must hold (see below). Any mismatch is a fail.
3. **Source rows** — each category total, anomaly, and recurring claim ties to specific transactions that exist in the source file. Spot-check the cited rows.
4. **No fabrication** — uncategorized and unparseable rows are flagged, not folded silently into a total.

---

## The invariants, precisely

From `aggregate()`:

```
income   = sum of amounts where amount > 0
expenses = sum of -amount where amount < 0        (a positive magnitude)
net      = income - expenses
```

**Invariant 1 — `income - expenses = net`.** Direct from the definitions above.

**Invariant 2 — the sum of `by_category` equals the net of all transactions.** This is the one people misread. `by_category` sums the **signed** amount into each category (`by_category[cat] += t.amount`). Positive amounts (income) and negative amounts (spend) both land in it. So:

```
sum(by_category.values()) == income - expenses == net
```

It equals **net**, *not* total spend. If someone "checks" it against gross expenses, it will look wrong — that's a misread of the invariant, not a real failure. (The category *spend* shares shown in a report are a separate, presentational computation over the negative amounts; they don't change this invariant.)

**Invariant 3 — count.** The transaction count in the report equals the number of clean transactions the toolkit parsed (`len(report.transactions)`). Skipped rows are counted and reported separately — they are **not** part of this total and must never be quietly added to make a number look complete.

---

## Worked pass

```
Parsed: 6 transactions, 0 skipped
income   =  4200.00
expenses =  2261.28
net      =  1938.72
by_category (signed):
  Income          4200.00
  Rent           -2100.00
  Groceries        -86.44
  Transport        -52.10
  Subscriptions    -15.99
  Uncategorized     -6.75
```

- Invariant 1: `4200.00 - 2261.28 = 1938.72` ✓
- Invariant 2: `4200.00 - 2100.00 - 86.44 - 52.10 - 15.99 - 6.75 = 1938.72` = net ✓
- Invariant 3: report says "6 transactions" and 6 were parsed ✓

**Verdict:** pass — "income − expenses = net = 1938.72; by_category sums to net; count matches."

---

## Worked reject

Draft says expenses are **$2,254.53** and calls it "6 transactions."

- The toolkit's `aggregate` returns `expenses = 2261.28`. The draft's figure differs by `6.75` — exactly the uncategorized coffee charge.
- Diagnosis: the analyst dropped the uncategorized row from the expense total instead of leaving it in `Uncategorized`. That's a fabrication (a silently adjusted total) and breaks invariant 2.

**Verdict:** reject — "expenses reported 2254.53 but aggregate() returns 2261.28; the 6.75 Uncategorized row was excluded from the total. Re-run and keep it in Uncategorized." The analyst redoes it; the guardian re-checks.

---

## When to reject

- Any invariant fails.
- A figure can't be reproduced by re-running the toolkit.
- A cited source row doesn't exist in the file.
- A skipped or uncategorized row was absorbed into a total to make it look clean.

**When unsure, reject.** A rejected draft costs a re-run; a shipped wrong number costs the user's trust. Never access the network during verification.
