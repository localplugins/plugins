#!/usr/bin/env python3
"""Unit tests for the money-map toolkit. Pure stdlib (unittest)."""
import datetime
import os
import sys
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "money-map" / "lib"))
import moneymap as mm  # noqa: E402


class TestCore(unittest.TestCase):
    def test_normalize(self):
        self.assertEqual(mm.normalize("  Whole   FOODS  "), "whole foods")

    def test_to_decimal(self):
        self.assertEqual(mm._to_decimal("$1,234.56"), Decimal("1234.56"))
        self.assertEqual(mm._to_decimal("(12.30)"), Decimal("-12.30"))
        self.assertEqual(mm._to_decimal(""), Decimal("0"))

    def test_transaction_defaults(self):
        t = mm.Transaction(date=datetime.date(2026, 1, 2), amount=Decimal("-5"),
                           description="Cafe", raw={"a": "1"})
        self.assertIsNone(t.category)
        self.assertIsNone(t.account)
        self.assertEqual(t.raw, {"a": "1"})


def _write_csv(text):
    fd, path = tempfile.mkstemp(suffix=".csv")
    os.write(fd, text.encode("utf-8"))
    os.close(fd)
    return path


class TestParse(unittest.TestCase):
    def test_signed_amount(self):
        p = _write_csv("Date,Description,Amount\n2026-01-05,Cafe,-4.50\n2026-01-06,Payroll,2000.00\n")
        txns = mm.parse(p, {"date": "Date", "date_format": "%Y-%m-%d",
                            "description": "Description", "amount": "Amount"})
        os.unlink(p)
        self.assertEqual(len(txns), 2)
        self.assertEqual(txns[0].amount, Decimal("-4.50"))
        self.assertEqual(txns[1].amount, Decimal("2000.00"))
        self.assertEqual(txns[0].description, "Cafe")

    def test_debit_credit(self):
        p = _write_csv("Date,Description,Debit,Credit\n2026-01-05,Cafe,4.50,\n2026-01-06,Payroll,,2000\n")
        txns = mm.parse(p, {"date": "Date", "date_format": "%Y-%m-%d",
                            "description": "Description", "debit": "Debit", "credit": "Credit"})
        os.unlink(p)
        self.assertEqual(txns[0].amount, Decimal("-4.50"))
        self.assertEqual(txns[1].amount, Decimal("2000"))

    def test_malformed_amount_row_skipped_and_surfaced(self):
        # A junk amount row must be skipped and surfaced, not raise and abort parse().
        p = _write_csv("Date,Description,Amount\n"
                       "2026-01-05,Cafe,-4.50\n"
                       "2026-01-06,Junk,1.2.3\n"
                       "2026-01-07,Payroll,2000.00\n")
        mapping = {"date": "Date", "date_format": "%Y-%m-%d",
                   "description": "Description", "amount": "Amount"}
        report = mm.parse_report(p, mapping)
        os.unlink(p)
        self.assertEqual([t.description for t in report.transactions], ["Cafe", "Payroll"])
        self.assertEqual(len(report.skipped), 1)
        self.assertEqual(report.skipped[0].raw["Description"], "Junk")
        self.assertIn("1.2.3", report.skipped[0].reason)

    def test_parse_discards_bad_rows_but_keeps_good(self):
        # The parse() convenience returns only clean rows (never raises on junk).
        p = _write_csv("Date,Description,Amount\n"
                       "2026-01-06,Junk,--5\n"
                       "2026-01-07,Payroll,2000.00\n")
        mapping = {"date": "Date", "date_format": "%Y-%m-%d",
                   "description": "Description", "amount": "Amount"}
        txns = mm.parse(p, mapping)
        os.unlink(p)
        self.assertEqual([t.description for t in txns], ["Payroll"])

    def test_missing_amount_mapping_raises(self):
        # A mapping with no amount source is a usage error: raise clearly, don't yield zeros.
        p = _write_csv("Date,Description,Amount\n2026-01-05,Cafe,-4.50\n")
        mapping = {"date": "Date", "date_format": "%Y-%m-%d", "description": "Description"}
        with self.assertRaisesRegex(ValueError, "amount"):
            mm.parse(p, mapping)
        os.unlink(p)

    def test_both_debit_and_credit_row_flagged(self):
        # A row with both debit AND credit populated is ambiguous: flag it, don't net silently.
        p = _write_csv("Date,Description,Debit,Credit\n"
                       "2026-01-05,Ambiguous,4.50,2000\n"
                       "2026-01-06,Payroll,,2000\n")
        mapping = {"date": "Date", "date_format": "%Y-%m-%d",
                   "description": "Description", "debit": "Debit", "credit": "Credit"}
        report = mm.parse_report(p, mapping)
        os.unlink(p)
        self.assertEqual([t.description for t in report.transactions], ["Payroll"])
        self.assertEqual(len(report.skipped), 1)
        self.assertEqual(report.skipped[0].raw["Description"], "Ambiguous")
        self.assertIn("both", report.skipped[0].reason.lower())

    def test_ragged_row_skipped_not_aborting(self):
        # A short/ragged row (missing trailing fields) must be skipped, not abort parse().
        p = _write_csv("Date,Description,Amount\n"
                       "2026-01-05,Cafe,-4.50\n"
                       "2026-01-06\n"
                       "2026-01-07,Payroll,2000.00\n")
        mapping = {"date": "Date", "date_format": "%Y-%m-%d",
                   "description": "Description", "amount": "Amount"}
        report = mm.parse_report(p, mapping)
        os.unlink(p)
        self.assertEqual([t.description for t in report.transactions], ["Cafe", "Payroll"])
        self.assertEqual(len(report.skipped), 1)


def _txn(desc, amt="-1", d="2026-01-01"):
    return mm.Transaction(date=datetime.date.fromisoformat(d), amount=Decimal(amt), description=desc)


class TestCategorize(unittest.TestCase):
    def test_rules_and_uncategorized(self):
        txns = [_txn("STRIPE PAYOUT"), _txn("Whole Foods Market"), _txn("Mystery LLC")]
        rules = [{"match": "(?i)stripe", "category": "Software"},
                 {"match": "(?i)whole foods", "category": "Groceries"}]
        all_t, uncat = mm.categorize(txns, rules)
        self.assertEqual(all_t[0].category, "Software")
        self.assertEqual(all_t[1].category, "Groceries")
        self.assertIsNone(all_t[2].category)
        self.assertEqual([t.description for t in uncat], ["Mystery LLC"])

    def test_first_match_wins(self):
        txns = [_txn("STRIPE WHOLE FOODS")]
        rules = [{"match": "(?i)stripe", "category": "Software"},
                 {"match": "(?i)whole foods", "category": "Groceries"}]
        all_t, _ = mm.categorize(txns, rules)
        self.assertEqual(all_t[0].category, "Software")


class TestAggregate(unittest.TestCase):
    def test_totals(self):
        txns = [_txn("pay", "3000", "2026-01-01"), _txn("rent", "-1000", "2026-01-02"),
                _txn("food", "-200", "2026-01-03")]
        for t, c in zip(txns, ["Income", "Rent", "Groceries"]):
            t.category = c
        agg = mm.aggregate(txns)
        self.assertEqual(agg["income"], Decimal("3000"))
        self.assertEqual(agg["expenses"], Decimal("1200"))
        self.assertEqual(agg["net"], Decimal("1800"))
        self.assertEqual(agg["by_category"]["Rent"], Decimal("-1000"))
        self.assertEqual(agg["by_month"]["2026-01"]["expenses"], Decimal("1200"))

    def test_recurring(self):
        txns = [_txn("Netflix", "-15.99", f"2026-0{m}-10") for m in (1, 2, 3)]
        rec = mm.aggregate(txns)["recurring"]
        self.assertEqual(len(rec), 1)
        self.assertEqual(rec[0]["months"], 3)
        self.assertEqual(rec[0]["amount"], Decimal("15.99"))


class TestAnomalies(unittest.TestCase):
    def test_duplicates(self):
        txns = [_txn("Cafe", "-4.50", "2026-01-05"), _txn("Cafe", "-4.50", "2026-01-05")]
        dups = mm.anomalies(txns)["duplicates"]
        self.assertEqual(len(dups), 1)

    def test_outliers(self):
        txns = [_txn("a", "-10"), _txn("b", "-12"), _txn("c", "-11"), _txn("d", "-500")]
        for t in txns:
            t.category = "Shopping"
        out = mm.anomalies(txns)["outliers"]
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0]["amount"], "-500")


class TestReconcile(unittest.TestCase):
    def test_match_and_unmatched(self):
        a = [_txn("x", "-10", "2026-01-05"), _txn("y", "-20", "2026-01-06")]
        b = [_txn("x2", "-10", "2026-01-06"), _txn("z", "-99", "2026-01-06")]
        res = mm.reconcile(a, b)
        self.assertEqual(len(res["matched"]), 1)
        self.assertEqual(res["only_in_a"][0].amount, Decimal("-20"))
        self.assertEqual(res["only_in_b"][0].amount, Decimal("-99"))


if __name__ == "__main__":
    unittest.main()
