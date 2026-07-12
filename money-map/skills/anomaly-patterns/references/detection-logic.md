# Anomaly detection logic

The exact rules the toolkit uses, with sample rows. Every threshold below is what `lib/moneymap.py` actually implements — don't paraphrase looser numbers to the user.

Two functions produce the flags:

- `anomalies(txns)` → `{ "duplicates": [...], "outliers": [...] }`
- `aggregate(txns)["recurring"]` → list of recurring charges (used to spot recurring *changes* across periods)

---

## Duplicates — `_duplicates`

A transaction is a duplicate when a **later** row shares the exact key of an earlier one:

```
key = (date, amount, normalize(description))
```

`normalize` lowercases, collapses internal whitespace, and strips. The first occurrence is kept; each subsequent match is reported. Note the amount must match **exactly** (same sign, same magnitude) and the date must be the **same day**.

**Trips:**

```
2026-03-14  -49.00  "ACME SaaS Subscription"
2026-03-14  -49.00  "ACME  SaaS  Subscription"   ← duplicate (whitespace-normalized match)
```

**Does not trip** (different day, so not flagged as a duplicate here):

```
2026-03-14  -49.00  "ACME SaaS Subscription"
2026-03-15  -49.00  "ACME SaaS Subscription"
```

Report each duplicate with its date, amount, and description, and note it's often a double-charge worth disputing — but let the user decide.

---

## Outliers — `_outliers`

For each **category**, gather its **outflows only** (`amount < 0`). Then:

- **Skip categories with fewer than 4 outflows** — too little data to call anything unusual.
- Compute the **median magnitude** (`med`) of the category's outflows.
- Flag any transaction whose magnitude **exceeds `med * 3`** (strictly greater), when `med > 0`.

So the test is per-category and relative: a $600 charge is an outlier in a category whose typical spend is $40, but not in one whose typical spend is $500.

**Sample — Groceries (5 outflows):**

```
-42.00, -55.00, -38.00, -61.00, -210.00
```

Median magnitude = 55. Threshold = 165. The `-210.00` row exceeds it → flagged as an outlier. The others don't.

Each flagged outlier is reported with date, amount, description, and category. Present it neutrally: a large but legitimate purchase and an erroneous charge look identical here — surface it, don't judge.

**Deliberately does not flag:** a category with only 3 outflows (below the minimum count), or a large charge that's still within 3× the median.

---

## Recurring charges — `_recurring` (and detecting *changes*)

`aggregate()["recurring"]` finds steady recurring outflows. Grouping is by `normalize(description)` over **outflows only**. A group qualifies when:

- It appears in **at least 3 distinct calendar months** (`YYYY-MM`), and
- Its magnitudes are **tight**: `max - min <= median * 0.05` (within a 5% band), with median > 0.

Each qualifying group is reported as `{ description, amount (the median magnitude), count, months }`.

**Trips — a $15.99 subscription across 4 months:**

```
2026-01-03  -15.99  "NETFLIX.COM"
2026-02-03  -15.99  "NETFLIX.COM"
2026-03-03  -15.99  "NETFLIX.COM"
2026-04-03  -15.99  "NETFLIX.COM"
```

4 distinct months, magnitudes identical → recurring, amount 15.99.

**Does not trip:** the same charge in only 2 months (below the 3-month minimum), or a charge whose amount swings more than 5% (e.g. a utility bill that varies with usage — the band excludes it, by design, so genuine recurring charges aren't confused with variable ones).

### Spotting a recurring *change*

The toolkit surfaces the recurring **set** for a period; a *change* is something you detect by comparing periods:

- **Amount changed** — the same normalized description is recurring in both an earlier run and this one, but at a different median amount (e.g. a subscription that went from $9.99 to $12.99). Show both amounts and the dates.
- **New recurring charge** — a description that's recurring now but wasn't before. Worth confirming the user meant to start it.

When you report a recurring change, cite the underlying transactions on both sides so the user can see the before and after.

---

## Reporting rules (all three)

- Every flag cites its **source transaction(s)** — never a bare claim.
- Give a **one-line why** per flag.
- **No fraud claims.** Duplicates, outliers, and recurring changes are patterns, not verdicts. The user decides what to do.
