import unittest

from tools.deal_screen import commercial_value, mortgage_payment, screen_deal
from tools.cli import main


class ScreenTests(unittest.TestCase):
    def test_commercial_value(self):
        self.assertEqual(commercial_value(70_000, 0.07), 1_000_000)

    def test_commercial_value_rejects_bad_cap(self):
        for bad in (0, -0.01, 1, 5):
            with self.assertRaises(ValueError):
                commercial_value(1000, bad)

    def test_mortgage_payment_known_value(self):
        # $100,000 at 6% for 30 years = $599.55/month (standard amortization table).
        self.assertEqual(mortgage_payment(100_000, 0.06, 30), 599.55)

    def test_mortgage_zero_rate(self):
        self.assertEqual(mortgage_payment(120_000, 0.0, 10), 1000.0)

    def _base(self, **over):
        kw = dict(purchase_price=100_000, rehab=20_000, closing_costs=5_000, value=200_000,
                  monthly_rent=1_800, annual_taxes=2_400, annual_insurance=1_200)
        kw.update(over)
        return screen_deal(**kw)

    def test_all_in_pct_and_target(self):
        r = self._base()
        self.assertEqual(r.all_in, 125_000)
        self.assertEqual(r.all_in_pct_of_value, 0.625)
        self.assertTrue(r.passes_target)
        self.assertEqual(r.forced_equity, 75_000)

    def test_fails_target_when_over_65pct(self):
        r = self._base(purchase_price=125_000)
        self.assertFalse(r.passes_target)

    def test_turnkey_near_ceiling_has_no_forced_equity(self):
        r = self._base(purchase_price=160_000, rehab=0, closing_costs=0, value=160_000)
        self.assertEqual(r.forced_equity, 0)
        self.assertFalse(r.passes_target)

    def test_cash_flow_math(self):
        r = self._base()
        collected = 1_800 * 0.92
        noi = collected - collected * 0.18 - 300
        self.assertAlmostEqual(r.monthly_noi, round(noi, 2), places=2)
        self.assertEqual(r.monthly_debt_service, 0.0)
        self.assertIsNone(r.dscr)

    def test_debt_sized_on_value_times_ltv(self):
        r = self._base(ltv=0.75, rate=0.06)
        self.assertEqual(r.monthly_debt_service, mortgage_payment(150_000, 0.06, 30))
        self.assertAlmostEqual(r.monthly_cash_flow, round(r.monthly_noi - r.monthly_debt_service, 2), places=2)
        self.assertIsNotNone(r.dscr)

    def test_rejects_bad_inputs(self):
        with self.assertRaises(ValueError):
            self._base(value=0)
        with self.assertRaises(ValueError):
            self._base(vacancy_pct=1.5)
        with self.assertRaises(ValueError):
            self._base(rehab=-1)


class CliTests(unittest.TestCase):
    def test_cap_command(self):
        self.assertEqual(main(["cap", "--noi", "70000", "--cap-rate", "0.07"]), 0)

    def test_bad_input_returns_2(self):
        self.assertEqual(main(["cap", "--noi", "70000", "--cap-rate", "0"]), 2)

    def test_missing_required_returns_2(self):
        self.assertEqual(main(["refi", "--appraisal", "100000"]), 2)

    def test_refi_command(self):
        self.assertEqual(main(["refi", "--appraisal", "160000", "--ltv", "0.75",
                               "--purchase-price", "125000"]), 0)


if __name__ == "__main__":
    unittest.main()
