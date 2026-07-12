# Reconciliation logic

How `reconcile(a, b, day_tolerance=3)` works and the count invariant the `figures-guardian` checks. Used by `/reconcile` (bank vs books, card vs statement, etc.).

---

## The matching rule

`reconcile` takes two lists of transactions, `a` and `b`, and a `day_tolerance` (default **3** days). It walks each transaction in `a` in order and matches it to the **first unused** transaction in `b` that satisfies both:

- **equal amount** — `tb.amount == ta.amount` (exact `Decimal` equality, including sign), and
- **near date** — `abs((tb.date - ta.date).days) <= day_tolerance`.

A matched `b`-transaction is removed from the pool so it can't match twice — matching is **one-to-one and greedy**. The result is:

```python
{
  "matched":    [(ta, tb), ...],   # pairs
  "only_in_a":  [ta, ...],         # a-rows with no match in b
  "only_in_b":  [tb, ...],         # b-rows never consumed
}
```

The date tolerance absorbs posting lag — a charge dated the 14th in your books may post at the bank on the 15th or 16th. It is **not** a fuzzy amount match: amounts must be exactly equal, so a $49.00 charge never matches a $49.50 one.

---

## The count invariant

The guardian checks that nothing was invented or lost:

```
len(matched) + len(only_in_a) == len(a)
len(matched) + len(only_in_b) == len(b)
```

Every `a`-row is either matched or in `only_in_a`; every `b`-row is either matched (consumed) or left in `only_in_b`. If these don't add up, the reconciliation output is wrong — reject.

---

## Worked example

**a = books-q1.csv** (3 rows), **b = bank-q1.csv** (3 rows):

```
a1  2026-02-14  -49.00  "Domain renewal"
a2  2026-03-10  -18.00  "Coffee run"
a3  2026-03-30  -12.50  "Bank fee (accrued)"

b1  2026-03-12  -18.00  "SQ *COFFEE"
b2  2026-03-31  -35.00  "SERVICE CHARGE"
b3  2026-02-15  -49.00  "DOMAIN RENEWAL"
```

Walk `a`:

- **a1** (-49.00, 02-14): b3 is -49.00 on 02-15 → 1 day apart, within tolerance → **match (a1, b3)**. b3 removed.
- **a2** (-18.00, 03-10): b1 is -18.00 on 03-12 → 2 days apart → **match (a2, b1)**. b1 removed.
- **a3** (-12.50, 03-30): no remaining b-row has amount -12.50 → **only_in_a**.

Left in the pool: **b2** (-35.00) → **only_in_b**.

```
Matched: 2
Only in a (1): 2026-03-30  -12.50  "Bank fee (accrued)"   ← recorded, not on bank yet
Only in b (1): 2026-03-31  -35.00  "SERVICE CHARGE"        ← on bank, not in books
```

Invariant: `2 + 1 = 3 = len(a)` ✓ and `2 + 1 = 3 = len(b)` ✓.

---

## Reporting

- List the unmatched rows on **each** side with date, amount, and description — that's the actionable output (what's missing or extra).
- State the matched count and both totals so the user can see the invariant holds.
- **Never invent a match** to make the two sides tie out. An exact-amount, near-date match is the only match; everything else is genuinely unmatched and should be shown as such.

---

## Edge notes

- **Order sensitivity:** because matching is greedy and first-unused, when several `b`-rows share the same amount and fall within tolerance, the earliest-listed eligible one is taken. This is deterministic for a given input ordering.
- **Duplicates across files:** two identical `a`-rows will each try to consume a distinct `b`-row; if only one matching `b`-row exists, the second `a`-row correctly falls into `only_in_a`.
- **Sign matters:** a +49.00 refund does not reconcile against a -49.00 charge. If you expect those to net, that's a different question than reconciliation.
