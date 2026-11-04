import json
import os
import tempfile
import unittest

from tools.cli import main
from tools.market_compare import compare_from_json, compare_markets, evaluate_market

BASE = dict(price=100_000, monthly_rent=1_200, annual_taxes=1_800, annual_insurance=1_000)


class MarketTests(unittest.TestCase):
    def test_noi_and_cap_rate(self):
        r = evaluate_market(name="A", **BASE)
        collected = 1_200 * 12 * 0.92
        noi = collected * (1 - 0.18) - 2_800
        self.assertAlmostEqual(r.annual_noi, round(noi, 2), places=2)
        self.assertAlmostEqual(r.cap_rate, round(noi / 100_000, 4), places=4)
        self.assertEqual(r.rent_to_price_pct, 0.012)

    def test_cash_on_cash_uses_down_payment_plus_closing(self):
        r = evaluate_market(name="A", ltv=0.75, closing_pct=0.03, **BASE)
        invested = 25_000 + 3_000
        self.assertAlmostEqual(r.cash_on_cash, round(r.annual_cash_flow / invested, 4), places=4)

    def test_all_cash_has_no_dscr(self):
        r = evaluate_market(name="A", ltv=0.0, **BASE)
        self.assertIsNone(r.dscr)
        self.assertEqual(r.annual_cash_flow, r.annual_noi)

    def test_high_taxes_hurt_ranking(self):
        low = dict(name="low-tax", **BASE)
        high = dict(name="high-tax", **{**BASE, "annual_taxes": 6_000})
        rows = compare_markets([high, low])
        self.assertEqual([r.name for r in rows], ["low-tax", "high-tax"])

    def test_sort_by_cash_flow(self):
        a = dict(name="a", **BASE)
        b = dict(name="b", **{**BASE, "monthly_rent": 1_600})
        self.assertEqual(compare_markets([a, b], sort_by="annual_cash_flow")[0].name, "b")

    def test_none_sorts_last(self):
        a = dict(name="cash", ltv=0.0, **BASE)
        b = dict(name="debt", ltv=0.75, **BASE)
        self.assertEqual(compare_markets([a, b], sort_by="dscr")[0].name, "debt")

    def test_rejects_bad_input(self):
        with self.assertRaises(ValueError):
            compare_markets([])
        with self.assertRaises(ValueError):
            evaluate_market(name="x", **{**BASE, "price": 0})
        with self.assertRaises(ValueError):
            evaluate_market(name="x", ltv=2, **BASE)
        with self.assertRaises(ValueError):
            compare_markets([dict(name="a", **BASE)], sort_by="name")
        with self.assertRaises(ValueError):
            compare_from_json("{}")

    def test_cli_markets_file(self):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "m.json")
            with open(path, "w") as f:
                json.dump([dict(name="a", **BASE)], f)
            self.assertEqual(main(["markets", path]), 0)
            self.assertEqual(main(["markets", os.path.join(d, "missing.json")]), 2)


if __name__ == "__main__":
    unittest.main()
