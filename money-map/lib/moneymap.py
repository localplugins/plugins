"""money-map toolkit: deterministic financial-data analysis. Pure Python stdlib.

Amounts are Decimal, signed: inflows positive, outflows negative.
"""
from __future__ import annotations

import csv
import re
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal, InvalidOperation


@dataclass
class Transaction:
    date: date
    amount: Decimal  # signed: + inflow, - outflow
    description: str
    account: str | None = None
    category: str | None = None
    raw: dict = field(default_factory=dict)


@dataclass
class SkippedRow:
    """A source row we could not turn into a Transaction — surfaced, never dropped silently."""
    line: int          # 1-based line number in the source file
    reason: str        # why it was skipped (malformed/ambiguous)
    raw: dict = field(default_factory=dict)  # the original CSV row


@dataclass
class ParseReport:
    """Result of parsing an export: the clean transactions plus the rows we flagged."""
    transactions: list[Transaction] = field(default_factory=list)
    skipped: list[SkippedRow] = field(default_factory=list)


class RowError(ValueError):
    """A single CSV row that cannot be parsed into a Transaction (bad value or ambiguous)."""


_WS = re.compile(r"\s+")


def normalize(desc: str) -> str:
    """Lowercase, collapse internal whitespace, strip. For matching/grouping."""
    return _WS.sub(" ", desc or "").strip().lower()


def _to_decimal(s: str) -> Decimal:
    """Parse a money string ('$1,234.56', '(12.30)', '-5') to a signed Decimal."""
    s = (s or "").strip()
    if not s:
        return Decimal("0")
    neg = s.startswith("(") and s.endswith(")")
    s = re.sub(r"[^0-9.\-]", "", s.strip("()"))
    if s in ("", "-", "."):
        return Decimal("0")
    val = Decimal(s)
    return -val if neg else val


def _validate_mapping(mapping) -> None:
    """Raise a clear error if the mapping has no usable amount source."""
    if not any(k in mapping for k in ("amount", "debit", "credit")):
        raise ValueError(
            "mapping needs an 'amount' column, or 'debit'/'credit' columns, "
            "to determine each transaction's amount"
        )


def _row_amount(row, mapping) -> Decimal:
    """Compute a row's signed amount, raising RowError on a bad value or an ambiguous row."""
    if "amount" in mapping:
        try:
            return _to_decimal(row[mapping["amount"]])
        except InvalidOperation:
            raise RowError(f"unparseable amount {row.get(mapping['amount'], '')!r}")
    try:
        debit = _to_decimal(row.get(mapping.get("debit", ""), ""))
        credit = _to_decimal(row.get(mapping.get("credit", ""), ""))
    except InvalidOperation:
        raise RowError("unparseable debit/credit amount")
    if debit != 0 and credit != 0:
        raise RowError("row has both debit and credit populated (ambiguous)")
    return credit - abs(debit)


def _row_to_txn(row, mapping) -> Transaction:
    """Turn one CSV row into a Transaction, raising RowError on a malformed/ambiguous row."""
    raw_date = row[mapping["date"]]              # KeyError (column absent) is structural: let it raise
    raw_desc = row[mapping["description"]]
    if raw_date is None or raw_desc is None:
        raise RowError("ragged row: missing a required field")
    try:
        d = datetime.strptime(raw_date.strip(), mapping["date_format"]).date()
    except ValueError:
        raise RowError(f"unparseable date {raw_date!r}")
    amt = _row_amount(row, mapping)
    raw_acct = row.get(mapping["account"]) if mapping.get("account") else None
    acct = raw_acct.strip() if raw_acct else None
    return Transaction(date=d, amount=amt, description=raw_desc.strip(), account=acct, raw=dict(row))


def parse_report(path, mapping) -> ParseReport:
    """Parse a CSV export into Transactions, surfacing rows we could not parse.

    Returns a ParseReport with `.transactions` (the clean rows) and `.skipped`
    (a SkippedRow per malformed or ambiguous row). Bad *values* (a junk amount
    or date, a row with both debit and credit populated) are flagged and skipped
    rather than dropped silently or fabricated. Structural problems — a missing
    amount source in the mapping, or a mapped column absent from the file — raise.
    """
    _validate_mapping(mapping)
    report = ParseReport()
    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                report.transactions.append(_row_to_txn(row, mapping))
            except RowError as e:
                report.skipped.append(SkippedRow(line=reader.line_num, reason=str(e), raw=dict(row)))
    return report


def parse(path, mapping) -> list[Transaction]:
    """Parse a CSV export into Transactions using a column mapping (see plan).

    Convenience wrapper returning only the clean transactions; unparseable rows
    are discarded. Use `parse_report` to also surface the skipped rows so they
    can be flagged for the user instead of dropped silently.
    """
    return parse_report(path, mapping).transactions


def categorize(txns, rules):
    """Assign categories by first matching rule (regex search on description).
    Mutates .category in place; returns (all_txns, uncategorized)."""
    compiled = [(re.compile(r["match"]), r["category"]) for r in rules]
    uncategorized = []
    for t in txns:
        t.category = None
        for pat, cat in compiled:
            if pat.search(t.description):
                t.category = cat
                break
        if t.category is None:
            uncategorized.append(t)
    return txns, uncategorized


def _recurring(txns):
    groups = defaultdict(list)
    for t in txns:
        if t.amount < 0:
            groups[normalize(t.description)].append(t)
    out = []
    for ts in groups.values():
        months = {t.date.strftime("%Y-%m") for t in ts}
        if len(months) >= 3:
            mags = sorted(abs(t.amount) for t in ts)
            med = mags[len(mags) // 2]
            if med > 0 and (mags[-1] - mags[0]) <= med * Decimal("0.05"):
                out.append({"description": ts[0].description, "amount": med,
                            "count": len(ts), "months": len(months)})
    return out


def aggregate(txns) -> dict:
    income = sum((t.amount for t in txns if t.amount > 0), Decimal("0"))
    expenses = sum((-t.amount for t in txns if t.amount < 0), Decimal("0"))
    by_category = defaultdict(lambda: Decimal("0"))
    by_month = defaultdict(lambda: {"income": Decimal("0"), "expenses": Decimal("0"), "net": Decimal("0")})
    for t in txns:
        by_category[t.category or "Uncategorized"] += t.amount
        ym = t.date.strftime("%Y-%m")
        if t.amount > 0:
            by_month[ym]["income"] += t.amount
        else:
            by_month[ym]["expenses"] += -t.amount
        by_month[ym]["net"] += t.amount
    return {"income": income, "expenses": expenses, "net": income - expenses,
            "by_category": dict(by_category),
            "by_month": {k: dict(v) for k, v in by_month.items()},
            "recurring": _recurring(txns)}


def _duplicates(txns):
    seen, dups = set(), []
    for t in txns:
        k = (t.date, t.amount, normalize(t.description))
        if k in seen:
            dups.append({"date": t.date.isoformat(), "amount": str(t.amount), "description": t.description})
        else:
            seen.add(k)
    return dups


def _outliers(txns):
    bycat = defaultdict(list)
    for t in txns:
        if t.amount < 0:
            bycat[t.category or "Uncategorized"].append(t)
    out = []
    for cat, ts in bycat.items():
        if len(ts) < 4:
            continue
        mags = sorted(abs(t.amount) for t in ts)
        med = mags[len(mags) // 2]
        for t in ts:
            if med > 0 and abs(t.amount) > med * 3:
                out.append({"date": t.date.isoformat(), "amount": str(t.amount),
                            "description": t.description, "category": cat})
    return out


def anomalies(txns) -> dict:
    return {"duplicates": _duplicates(txns), "outliers": _outliers(txns)}


def reconcile(a, b, day_tolerance=3) -> dict:
    """Match each a-txn to the first unused b-txn with equal amount and near date."""
    pool = list(b)
    matched, only_a = [], []
    for ta in a:
        hit = None
        for tb in pool:
            if tb.amount == ta.amount and abs((tb.date - ta.date).days) <= day_tolerance:
                hit = tb
                break
        if hit is not None:
            pool.remove(hit)
            matched.append((ta, hit))
        else:
            only_a.append(ta)
    return {"matched": matched, "only_in_a": only_a, "only_in_b": pool}
