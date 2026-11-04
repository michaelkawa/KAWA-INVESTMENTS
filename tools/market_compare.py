"""Market comparison on one sheet (guardrail 7 in SESSION-HANDOFF.md).

Compares price, rent, taxes and insurance for each market using the same formulas.
Inputs are user supplied; nothing is looked up. A ranking is a screen, not a recommendation.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, asdict

from .deal_screen import mortgage_payment


@dataclass(frozen=True)
class MarketRow:
    name: str
    price: float
    monthly_rent: float
    rent_to_price_pct: float
    annual_noi: float
    cap_rate: float
    dscr: float | None
    annual_cash_flow: float
    cash_on_cash: float | None

    def as_dict(self) -> dict:
        return asdict(self)


def evaluate_market(
    *,
    name: str,
    price: float,
    monthly_rent: float,
    annual_taxes: float,
    annual_insurance: float,
    vacancy_pct: float = 0.08,
    maintenance_pct: float = 0.08,
    mgmt_pct: float = 0.10,
    ltv: float = 0.75,
    rate: float = 0.07,
    years: int = 30,
    closing_pct: float = 0.03,
) -> MarketRow:
    """One market's numbers. Debt is ltv * price; cash invested is the down payment plus closing."""
    if price <= 0:
        raise ValueError(f"{name}: price must be > 0")
    for n, v in (("monthly_rent", monthly_rent), ("annual_taxes", annual_taxes),
                 ("annual_insurance", annual_insurance)):
        if v < 0:
            raise ValueError(f"{name}: {n} must be >= 0")
    for n, v in (("vacancy_pct", vacancy_pct), ("maintenance_pct", maintenance_pct),
                 ("mgmt_pct", mgmt_pct), ("ltv", ltv), ("closing_pct", closing_pct)):
        if not 0 <= v <= 1:
            raise ValueError(f"{name}: {n} must be between 0 and 1")

    collected = monthly_rent * 12 * (1 - vacancy_pct)
    noi = collected * (1 - maintenance_pct - mgmt_pct) - annual_taxes - annual_insurance
    debt = mortgage_payment(price * ltv, rate, years) * 12 if ltv > 0 else 0.0
    cash_flow = noi - debt
    invested = price * (1 - ltv) + price * closing_pct
    return MarketRow(
        name=name,
        price=round(price, 2),
        monthly_rent=round(monthly_rent, 2),
        rent_to_price_pct=round(monthly_rent / price, 4),
        annual_noi=round(noi, 2),
        cap_rate=round(noi / price, 4),
        dscr=round(noi / debt, 2) if debt else None,
        annual_cash_flow=round(cash_flow, 2),
        cash_on_cash=round(cash_flow / invested, 4) if invested > 0 else None,
    )


def compare_markets(markets: list[dict], *, sort_by: str = "cap_rate") -> list[MarketRow]:
    """Evaluate every market with identical assumptions unless a row overrides them, best first."""
    if not markets:
        raise ValueError("no markets given")
    if sort_by not in MarketRow.__dataclass_fields__ or sort_by == "name":
        raise ValueError(f"cannot sort by {sort_by}")
    rows = [evaluate_market(**m) for m in markets]
    # None (no debt / no cash invested) sorts last.
    return sorted(rows, key=lambda r: (getattr(r, sort_by) is None, -(getattr(r, sort_by) or 0)))


def compare_from_json(text: str, *, sort_by: str = "cap_rate") -> list[dict]:
    data = json.loads(text)
    if not isinstance(data, list):
        raise ValueError("expected a JSON list of market objects")
    return [r.as_dict() for r in compare_markets(data, sort_by=sort_by)]
