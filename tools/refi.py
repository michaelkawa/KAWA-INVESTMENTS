"""Cash-out refinance math (guardrails 1 and 2 in SESSION-HANDOFF.md).

Refi cash is loan-to-value times the lender's value basis, minus payoff and costs.
It is NOT appraisal minus purchase price. During a lender's seasoning window the
value basis is commonly capped at purchase price plus documented improvements.
That cap is an ASSUMPTION here: pass the lender's real rule in as inputs.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict


@dataclass(frozen=True)
class RefiResult:
    value_basis: float
    loan_amount: float
    payoff: float
    closing_costs: float
    cash_back: float
    all_in_cost: float
    cash_left_in_deal: float
    seasoning_cap_applied: bool

    def as_dict(self) -> dict:
        return asdict(self)


def _check(name: str, value: float, *, lo: float = 0.0, hi: float | None = None) -> None:
    if value < lo or (hi is not None and value > hi):
        raise ValueError(f"{name}={value} out of range")


def cash_out_refi(
    *,
    appraisal: float,
    ltv: float,
    purchase_price: float,
    rehab: float = 0.0,
    acquisition_costs: float = 0.0,
    payoff: float = 0.0,
    closing_cost_pct: float = 0.03,
    months_owned: float | None = None,
    seasoning_months: float = 0.0,
) -> RefiResult:
    """Compute refi proceeds.

    payoff: existing loan balance paid off at refi (0 if bought with cash).
    cash_back = loan - payoff - closing_costs.
    cash_left_in_deal = (price + rehab + acquisition costs) - cash_back when the
    purchase was cash-funded; with a payoff, the payoff is already part of cash_back.
    Seasoning cap applies when months_owned < seasoning_months: the basis becomes
    min(appraisal, purchase_price + rehab). If months_owned is None the cap is
    NOT applied; the caller must say so.
    """
    for n, v in (("appraisal", appraisal), ("purchase_price", purchase_price),
                 ("rehab", rehab), ("acquisition_costs", acquisition_costs),
                 ("payoff", payoff), ("seasoning_months", seasoning_months)):
        _check(n, v)
    _check("ltv", ltv, lo=0.0, hi=1.0)
    _check("closing_cost_pct", closing_cost_pct, lo=0.0, hi=0.25)

    capped = months_owned is not None and months_owned < seasoning_months
    basis = min(appraisal, purchase_price + rehab) if capped else appraisal
    loan = round(basis * ltv, 2)
    costs = round(loan * closing_cost_pct, 2)
    cash_back = round(loan - payoff - costs, 2)
    all_in = round(purchase_price + rehab + acquisition_costs, 2)
    return RefiResult(
        value_basis=round(basis, 2),
        loan_amount=loan,
        payoff=round(payoff, 2),
        closing_costs=costs,
        cash_back=cash_back,
        all_in_cost=all_in,
        cash_left_in_deal=round(all_in - cash_back, 2),
        seasoning_cap_applied=capped,
    )
