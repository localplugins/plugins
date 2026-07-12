---
name: categorization
description: Use when categorizing transactions or building the money-map categories & rules. Explains the taxonomy, how rules apply, and how to propose new rules from uncategorized items.
---

# Categorization

money-map assigns each transaction a category using **rules** in `money/categories.json`, applied by the toolkit's `categorize(txns, rules)` — the **first matching rule wins**.

## The config

```json
{ "categories": ["Income", "Groceries", "..."],
  "rules": [ { "match": "(?i)stripe", "category": "Software" } ] }
```

`match` is a Python regex tested with `re.search` against the transaction description; `category` must be one of `categories`.

## Decision guide

- **Always categorize via the toolkit** — never hand-label by eyeballing amounts.
- **Order rules most-specific → most-general.** First match wins, so a broad rule placed early will shadow a specific one.
- **Uncategorized transactions are surfaced, never guessed.** For each, propose one concrete new rule (a merchant substring → category) for the user to approve, then append it.
- **Keep categories few and stable.** Add a category only when several transactions genuinely need it.
- **Start from `templates/categories.json`** when no config exists.

## References

- **`references/rule-examples.md`** — a library of real merchant→category rules, how to write a regex `match` (anchoring, alternation, escaping `+`), ordering pitfalls with worked before/after cases, and how to turn an uncategorized batch into proposed rules.
