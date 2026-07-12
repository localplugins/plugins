---
name: statement-parsing
description: Use to figure out a CSV export's columns and build the mapping the money-map toolkit needs. Covers signed-amount vs debit/credit layouts, date formats, and currency symbols.
---

# Statement Parsing

The toolkit's `parse(path, mapping)` and `parse_report(path, mapping)` need a `mapping` describing the CSV's columns. Read the header row and a few sample rows, build the mapping, and confirm it with the user if anything is ambiguous.

## The mapping

```python
{ "date": "<date column>",
  "date_format": "<strptime, e.g. %Y-%m-%d or %m/%d/%Y>",
  "description": "<description column>",
  # amount EITHER as one signed column:
  "amount": "<amount column>",
  # OR as separate columns (omit "amount" then):
  "debit": "<debit column>", "credit": "<credit column>",
  "account": "<optional account column>" }
```

`date`, `date_format`, and `description` are always required. For amounts you need **either** `amount` **or** the `debit`/`credit` pair — the toolkit raises if none is present.

## Decision guide

1. **Find the date column** and infer `date_format` from the samples (`2026-01-05` → `%Y-%m-%d`; `01/05/2026` → `%m/%d/%Y`).
2. **Find the amount source.** One signed column → use `amount`. Two columns → map `debit` (outflow) and `credit` (inflow); omit `amount`.
3. **Confirm the sign convention.** money-map's convention is inflows positive, outflows negative. If a single amount column has outflows as *positive*, tell the user and adjust.
4. **Leave currency symbols/commas/parens alone** — the toolkit parses `$1,234.56` and `(12.30)` itself.
5. **If anything is ambiguous, show the detected mapping and confirm before running.**

Only CSV is supported in v1 — for XLSX, ask the user to export/save as CSV.

## References

- **`references/mapping-examples.md`** — worked mappings for the common bank/card layouts (signed amount, debit/credit, dd/mm dates, account columns, multi-line headers).
- **`references/parsing-edge-cases.md`** — exactly how the toolkit handles currency symbols, parenthesized negatives, ambiguous debit+credit rows, ragged rows, BOM, and which problems are *skipped* (surfaced) vs which *raise*.
