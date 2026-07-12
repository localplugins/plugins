# Rule examples and patterns

How `categorize()` works, a library of rules to copy, and how to turn uncategorized transactions into proposed rules.

---

## How matching works

The toolkit compiles each rule's `match` into a regex and runs `pattern.search(description)` against the raw transaction description. For each transaction it walks the rules **in order** and stops at the **first** one that matches. If none match, the transaction is returned in the `uncategorized` list with `category = None`.

Because it's `search` (not `match`/`fullmatch`), the pattern can hit **anywhere** in the description — you don't need to describe the whole string, just a distinctive fragment.

```
description: "SQ *BLUE BOTTLE COFFEE OAKLAND"
rule match:  "(?i)blue bottle"   → matches (substring found)
```

---

## Writing a `match` regex

- **Case-insensitive:** start with `(?i)`. Merchant strings arrive in every case (`NETFLIX.COM`, `Netflix`, `netflix`); `(?i)` covers them all.
- **Alternation:** use `|` to group several merchants into one rule: `(?i)uber|lyft|shell|chevron`.
- **Escape regex metacharacters** in merchant names. `disney+` must be written `disney\\+` (the `+` is a regex quantifier). Same for `.` if you need a literal dot, though a bare `.` usually still matches fine as "any char."
- **Word boundaries / spacing** help avoid false hits: `bp ` (with trailing space) avoids matching the `bp` inside `shopbop`.
- **Keep patterns readable** — a rule is a merchant fingerprint, not a puzzle. Several small rules beat one giant regex.

---

## A starter rule library

Copy what fits, then reorder most-specific first.

```json
{
  "rules": [
    { "match": "(?i)payroll|salary|direct deposit|stripe payout", "category": "Income" },
    { "match": "(?i)stripe|aws|amazon web services|github|notion|figma|vercel", "category": "Software" },
    { "match": "(?i)whole foods|trader joe|safeway|aldi|kroger|costco", "category": "Groceries" },
    { "match": "(?i)restaurant|cafe|coffee|blue bottle|chipotle|doordash|ubereats", "category": "Dining" },
    { "match": "(?i)uber|lyft|shell|chevron|bp |transit|parking|caltrain", "category": "Transport" },
    { "match": "(?i)netflix|spotify|hulu|disney\\+|hbo|prime video", "category": "Subscriptions" },
    { "match": "(?i)rent|landlord|properties|apartments", "category": "Rent" },
    { "match": "(?i)pg&e|comcast|xfinity|water dept|electric|internet", "category": "Utilities" },
    { "match": "(?i)pharmacy|cvs|walgreens|clinic|dental|copay", "category": "Health" },
    { "match": "(?i)fee|interest charge|overdraft|service charge", "category": "Fees" }
  ]
}
```

---

## Ordering matters — worked example

**Problem:** everything lands in `Software` even though some rows are groceries.

```json
[
  { "match": "(?i)amazon", "category": "Software" },
  { "match": "(?i)amazon fresh|whole foods", "category": "Groceries" }
]
```

`AMAZON FRESH #22` hits the first rule (`amazon`) and never reaches the grocery rule. First match wins.

**Fix — specific before general:**

```json
[
  { "match": "(?i)amazon fresh|whole foods", "category": "Groceries" },
  { "match": "(?i)amazon web services|aws", "category": "Software" },
  { "match": "(?i)amazon", "category": "Shopping" }
]
```

Now `AMAZON FRESH` → Groceries, `AMAZON WEB SERVICES` → Software, and a plain `AMAZON.COM` order → Shopping. General catch-alls go last.

---

## Turning uncategorized rows into rules

After `categorize()`, the `uncategorized` list holds the transactions that matched nothing. Work through them like this:

1. **Group by a common merchant fragment.** Say these are uncategorized:

   ```
   2026-03-06  -6.75   BLUE BOTTLE COFFEE OAKLAND
   2026-03-19  -5.25   BLUE BOTTLE COFFEE SF
   2026-03-22  -48.00  PHILZ COFFEE #4
   ```

2. **Propose a concrete rule** to the user, with the category it would use:

   > 3 uncategorized coffee purchases. Add rule `(?i)blue bottle|philz|coffee → Dining`?

3. **On approval, append** the rule to `money/categories.json` (place it correctly in the order — specific before any broader Dining rule) and re-run `categorize()`.

Never assign a category to an uncategorized row without an approved rule. The whole point is that categorization is rule-driven and reproducible — a one-off silent guess breaks that.

---

## Categories vs Uncategorized in totals

`aggregate()` sums by `t.category or "Uncategorized"`, so uncategorized transactions **do** appear in `by_category` under the `Uncategorized` bucket — they are never folded into another category or hidden. That's intentional: the user should see how much money is still unclassified.
