# Parsing edge cases

Exactly how `lib/moneymap.py` handles messy input. The guiding rule: **a bad value is flagged and skipped (surfaced in `.skipped`), never dropped silently or invented; a structural problem raises.**

Use `parse_report(path, mapping)` to get both the clean `.transactions` and the `.skipped` rows. `parse(path, mapping)` is the convenience wrapper that returns only the clean transactions — use `parse_report` whenever you need to show the user what couldn't be parsed.

---

## Amount value formats the toolkit accepts

`_to_decimal` strips everything except digits, `.` and `-`, and treats a leading `(`/trailing `)` as negative. So all of these parse:

| Raw cell | Parsed `Decimal` |
|---|---|
| `1234.56` | `1234.56` |
| `$1,234.56` | `1234.56` |
| `-5` | `-5` |
| `(12.30)` | `-12.30` |
| `$ (1,000.00)` | `-1000.00` |
| `` (empty) | `0` |
| `-` or `.` alone | `0` |

You do **not** need to strip currency symbols, commas, or parentheses yourself — doing so risks corrupting the value. Hand the raw column to the toolkit.

A cell that still can't become a `Decimal` after cleaning (e.g. `USD`, `n/a`, `1.2.3`) raises `RowError("unparseable amount ...")` for that row → the row is **skipped and surfaced**, not zeroed.

---

## Debit + credit rows

With a `debit`/`credit` mapping the amount is `credit - abs(debit)`:

- Debit only → negative (outflow).
- Credit only → positive (inflow).
- **Both populated and non-zero → ambiguous.** Raises `RowError("row has both debit and credit populated (ambiguous)")` → skipped and surfaced.

```csv
Date,Description,Debit,Credit
01/07/2026,GARBLED ROW,142.30,25.00
```

This row appears in `.skipped` with `reason = "row has both debit and credit populated (ambiguous)"`. Show it to the user to fix at the source — don't try to pick which value is "right."

---

## Dates that don't match the format

`datetime.strptime(raw_date.strip(), date_format)` must match exactly. `2026-13-01` (no month 13) or a date that doesn't fit the chosen `date_format` raises `RowError("unparseable date ...")` → skipped and surfaced. If *many* rows skip on the date, the `date_format` itself is probably wrong — recheck the mapping rather than treating them as bad data.

---

## Ragged rows (missing fields)

If a mapped optional value comes back as `None` (a short row where `DictReader` filled missing trailing fields with `None`), the toolkit raises `RowError("ragged row: missing a required field")` for date/description → skipped and surfaced.

---

## Skipped vs raised — the distinction

**Skipped** (per-row, surfaced in `.skipped`, parsing continues) — a bad *value* in one row:

- unparseable amount
- unparseable debit/credit amount
- both debit and credit populated
- unparseable date
- ragged row missing a required field

**Raised** (stops the whole parse — a *structural* problem with the mapping or file):

- mapping has no `amount` and no `debit`/`credit` → `ValueError` from `_validate_mapping`
- a mapped column name isn't in the file's header → `KeyError` on `row[mapping["date"]]` / `row[mapping["description"]]`

A raise means "fix the mapping or the file and rerun," not "this one row is junk." When you hit a raise, re-derive the mapping — don't loop over rows trying to swallow it.

---

## Encoding

Files are opened with `encoding="utf-8-sig"`, so a UTF-8 byte-order-mark at the start of the file (common in Windows/Excel exports) is stripped automatically and won't corrupt the first header name. No action needed.

---

## What to tell the user

After parsing, always report the count of clean transactions **and** the count of skipped rows with their reasons. Skipped rows are written to `skipped.csv` (in `/understand`) so the user can correct them at the source and rerun. Never present a total as if the skipped rows didn't exist.
