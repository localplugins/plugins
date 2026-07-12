# Mapping examples

Worked column mappings for the layouts you'll actually see. Read the header and 2-3 sample rows, match against the closest example, and adjust the column names to the file's exact headers.

---

## 1. Single signed amount column (most common)

```csv
Date,Description,Amount
2026-03-01,PAYROLL ACME INC,4200.00
2026-03-02,WHOLE FOODS MARKET #123,-86.44
2026-03-03,NETFLIX.COM,-15.99
```

Outflows are negative, inflows positive — this matches money-map's convention directly.

```python
{
  "date": "Date",
  "date_format": "%Y-%m-%d",
  "description": "Description",
  "amount": "Amount",
}
```

---

## 2. Separate debit / credit columns

```csv
Date,Description,Debit,Credit
01/05/2026,COSTCO WHOLESALE,142.30,
01/06/2026,REFUND - RETURN,,25.00
```

Only one of Debit/Credit is populated per row. The toolkit computes `credit - abs(debit)`, so debit becomes a negative outflow and credit a positive inflow. **Omit `amount`.**

```python
{
  "date": "Date",
  "date_format": "%m/%d/%Y",
  "description": "Description",
  "debit": "Debit",
  "credit": "Credit",
}
```

A row with **both** Debit and Credit populated is ambiguous — the toolkit skips it and surfaces it in `.skipped`. See `parsing-edge-cases.md`.

---

## 3. Signed amount with an account column

Useful when one export covers several accounts, or for `/clean` across files.

```csv
Posted,Account,Memo,Amount
2026-02-10,Checking ...4821,ACH RENT MAPLE PROPERTIES,-2100.00
2026-02-11,Checking ...4821,TRADER JOES #55,-63.20
```

```python
{
  "date": "Posted",
  "date_format": "%Y-%m-%d",
  "description": "Memo",
  "amount": "Amount",
  "account": "Account",
}
```

`account` is optional; include it whenever the file has one so downstream output can keep accounts distinct.

---

## 4. Day-first dates (non-US exports)

```csv
Transaction Date,Details,Amount
05/03/2026,SAINSBURYS,-41.10
14/03/2026,SALARY,3100.00
```

`05/03/2026` here means 5 March, not 3 May. Confirm with the user which is day and which is month before committing to a format.

```python
{
  "date": "Transaction Date",
  "date_format": "%d/%m/%Y",
  "description": "Details",
  "amount": "Amount",
}
```

---

## 5. Outflows stored as positive (sign flip needed)

Some card exports list every charge as a positive number.

```csv
Date,Description,Amount
2026-03-02,WHOLE FOODS,86.44
2026-03-01,PAYMENT THANK YOU,-500.00
```

Here `86.44` is a *purchase* (should be negative in money-map's convention). The toolkit does **not** guess sign intent — there's no "flip sign" flag in the mapping. When you detect this, tell the user the file's sign is inverted from money-map's convention and agree on a fix before running: usually the cleanest path is to map the column and confirm the interpretation, or preprocess the file so outflows are negative. Never silently proceed with an inverted sign — the totals would be wrong.

---

## Common `date_format` codes

| Sample | `date_format` |
|---|---|
| `2026-01-05` | `%Y-%m-%d` |
| `01/05/2026` | `%m/%d/%Y` |
| `05/01/2026` (day-first) | `%d/%m/%Y` |
| `Jan 5, 2026` | `%b %d, %Y` |
| `05-Jan-2026` | `%d-%b-%Y` |
| `2026/01/05` | `%Y/%m/%d` |

The toolkit calls `datetime.strptime(raw_date.strip(), date_format)` — the format must match the sample exactly. A date that doesn't match is skipped and surfaced, not dropped.

---

## Confirmation checklist before running

- Date column and `date_format` reproduce a sample date correctly.
- Amount source chosen: `amount`, or `debit`+`credit`.
- Sign convention verified (outflows negative).
- Optional `account` mapped if present.
- Detected mapping shown to the user when anything was ambiguous.
