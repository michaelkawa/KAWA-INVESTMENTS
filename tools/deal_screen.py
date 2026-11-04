"""Deal screening math (guardrails 3, 4, 7 in SESSION-HANDOFF.md).

A screen is NOT deal approval. Every input is user supplied; nothing is looked up.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict


def commercial_value(noi: float, cap_rate: float) -> float:
    """Commercial value = NOI / market cap rate. cap_rate as a decimal (0.07 = 7%)."""
    if cap_rate <= 0 or cap_rate >= 1:
        raise ValueError("cap_rate must be a decimal between 0 and 1 (exclusive)")
    if noi < 0:
        raise ValueError("noi must be >= 0")
    return round(noi / cap_rate, 2)


def mortgage_payment(principal: float, annual_rate: float, years: int = 30) -> float:
    """Monthly principal-and-interest payment, fully amortizing."""
    if principal < 0 or years <= 0 or annual_rate < 0:
        raise ValueError("bad loan inputs")
    n = years * 12
    if annual_rate == 0:
        return round(principal / n, 2)
    r = annual_rate / 12
    return round(principal * r / (1 - (1 + r) ** -n), 2)


@dataclass(frozen=True)
class ScreenResult:
    all_in: float
    all_in_pct_of_value: float
    forced_equity: float
    passes_target: bool
    rent_to_all_in_pct: float
    monthly_noi: float
    monthly_debt_service: float
    monthly_cash_flow: float
    dscr: float | None

    def as_dict(self) -> dict:
        return asdict(self)


def screen_deal(
    *,
    purchase_price: float,
    rehab: float,
    closing_costs: float,
    value: float,
    monthly_rent: float,
    annual_taxes: float,
    annual_insurance: float,
    vacancy_pct: float = 0.08,
    maintenance_pct: float = 0.08,
    mgmt_pct: float = 0.10,
    ltv: float = 0.0,
    rate: float = 0.07,
    years: int = 30,
    target_max_pct: float = 0.65,
) -> ScreenResult:
    """All-in % of value vs a 60-65% target, plus cash flow after reserves.

    `value` must be a supportable ARV or NOI/cap-rate value, not a seller claim.
    Debt is sized as ltv * value (guardrail 1). Opex % are of collected rent.
    """
    if value <= 0:
        raise ValueError("value must be > 0")
    for n, v in (("purchase_price", purchase_price), ("rehab", rehab),
                 ("closing_costs", closing_costs), ("monthly_rent", monthly_rent),
                 ("annual_taxes", annual_taxes), ("annual_insurance", annual_insurance)):
        if v < 0:
            raise ValueError(f"{n} must be >= 0")
    for n, v in (("vacancy_pct", vacancy_pct), ("maintenance_pct", maintenance_pct),
                 ("mgmt_pct", mgmt_pct), ("ltv", ltv), ("target_max_pct", target_max_pct)):
        if not 0 <= v <= 1:
            raise ValueError(f"{n} must be between 0 and 1")

    all_in = purchase_price + rehab + closing_costs
    pct = all_in / value
    collected = monthly_rent * (1 - vacancy_pct)
    opex = collected * (maintenance_pct + mgmt_pct) + (annual_taxes + annual_insurance) / 12
    noi = collected - opex
    debt = mortgage_payment(value * ltv, rate, years) if ltv > 0 else 0.0
    return ScreenResult(
        all_in=round(all_in, 2),
        all_in_pct_of_value=round(pct, 4),
        forced_equity=round(value - all_in, 2),
        passes_target=pct <= target_max_pct,
        rent_to_all_in_pct=round(monthly_rent / all_in, 4) if all_in else 0.0,
        monthly_noi=round(noi, 2),
        monthly_debt_service=debt,
        monthly_cash_flow=round(noi - debt, 2),
        dscr=round(noi / debt, 2) if debt else None,
    )
