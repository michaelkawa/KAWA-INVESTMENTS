import unittest

from tools.refi import cash_out_refi


class RefiTests(unittest.TestCase):
    def test_handoff_guardrail_1_example_125k(self):
        # 75% of $160k = $120k loan; $125k purchase, no costs -> about -$5k cash back.
        r = cash_out_refi(appraisal=160_000, ltv=0.75, purchase_price=125_000, closing_cost_pct=0.0)
        self.assertEqual(r.loan_amount, 120_000)
        self.assertEqual(r.cash_back, 120_000)
        self.assertEqual(r.cash_left_in_deal, 5_000)  # 125k in, 120k out

    def test_handoff_guardrail_1_example_115k(self):
        r = cash_out_refi(appraisal=160_000, ltv=0.75, purchase_price=115_000, closing_cost_pct=0.0)
        self.assertEqual(r.cash_left_in_deal, -5_000)  # 5k more out than in

    def test_closing_costs_reduce_cash_back(self):
        r = cash_out_refi(appraisal=160_000, ltv=0.75, purchase_price=115_000, closing_cost_pct=0.03)
        self.assertEqual(r.closing_costs, 3_600)
        self.assertEqual(r.cash_back, 116_400)

    def test_seasoning_cap_applies_inside_window(self):
        r = cash_out_refi(appraisal=160_000, ltv=0.75, purchase_price=125_000,
                          closing_cost_pct=0.0, months_owned=3, seasoning_months=6)
        self.assertTrue(r.seasoning_cap_applied)
        self.assertEqual(r.value_basis, 125_000)
        self.assertEqual(r.loan_amount, 93_750)

    def test_seasoning_cap_includes_rehab(self):
        r = cash_out_refi(appraisal=160_000, ltv=0.75, purchase_price=100_000, rehab=20_000,
                          closing_cost_pct=0.0, months_owned=1, seasoning_months=6)
        self.assertEqual(r.value_basis, 120_000)

    def test_seasoning_not_applied_after_window_or_when_unknown(self):
        done = cash_out_refi(appraisal=160_000, ltv=0.75, purchase_price=125_000,
                             months_owned=7, seasoning_months=6)
        self.assertFalse(done.seasoning_cap_applied)
        unknown = cash_out_refi(appraisal=160_000, ltv=0.75, purchase_price=125_000,
                                seasoning_months=6)
        self.assertFalse(unknown.seasoning_cap_applied)

    def test_cap_never_raises_basis_above_appraisal(self):
        r = cash_out_refi(appraisal=90_000, ltv=0.75, purchase_price=125_000,
                          months_owned=1, seasoning_months=6)
        self.assertEqual(r.value_basis, 90_000)

    def test_payoff_reduces_cash_back(self):
        r = cash_out_refi(appraisal=100_000, ltv=0.75, purchase_price=50_000,
                          payoff=40_000, closing_cost_pct=0.0)
        self.assertEqual(r.cash_back, 35_000)

    def test_rejects_bad_inputs(self):
        with self.assertRaises(ValueError):
            cash_out_refi(appraisal=100_000, ltv=1.2, purchase_price=50_000)
        with self.assertRaises(ValueError):
            cash_out_refi(appraisal=-1, ltv=0.7, purchase_price=50_000)
        with self.assertRaises(ValueError):
            cash_out_refi(appraisal=1, ltv=0.7, purchase_price=1, closing_cost_pct=0.9)


if __name__ == "__main__":
    unittest.main()
