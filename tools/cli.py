"""Command line front end: python -m tools.cli {refi|screen|cap} --key value ..."""
from __future__ import annotations

import argparse
import json
import sys

from . import deal_screen, market_compare, refi

_REFI = ["appraisal", "ltv", "purchase_price", "rehab", "acquisition_costs", "payoff",
         "closing_cost_pct", "months_owned", "seasoning_months"]
_SCREEN = ["purchase_price", "rehab", "closing_costs", "value", "monthly_rent",
           "annual_taxes", "annual_insurance", "vacancy_pct", "maintenance_pct",
           "mgmt_pct", "ltv", "rate", "years", "target_max_pct"]


def _add(p: argparse.ArgumentParser, names: list[str]) -> None:
    for n in names:
        p.add_argument(f"--{n.replace('_', '-')}", dest=n, type=float, default=None)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="tools.cli")
    sub = ap.add_subparsers(dest="cmd", required=True)
    _add(sub.add_parser("refi"), _REFI)
    _add(sub.add_parser("screen"), _SCREEN)
    mk = sub.add_parser("markets", help="compare markets from a JSON list file")
    mk.add_argument("file")
    mk.add_argument("--sort-by", default="cap_rate")
    cap = sub.add_parser("cap")
    _add(cap, ["noi", "cap_rate"])
    a = ap.parse_args(argv)
    if a.cmd == "markets":
        try:
            with open(a.file, encoding="utf-8") as f:
                print(json.dumps(market_compare.compare_from_json(f.read(), sort_by=a.sort_by), indent=2))
        except (OSError, TypeError, ValueError) as e:
            print(f"error: {e}", file=sys.stderr)
            return 2
        return 0
    kw = {k: v for k, v in vars(a).items() if k != "cmd" and v is not None}
    try:
        if a.cmd == "refi":
            out = refi.cash_out_refi(**kw).as_dict()
        elif a.cmd == "screen":
            if "years" in kw:
                kw["years"] = int(kw["years"])
            out = deal_screen.screen_deal(**kw).as_dict()
        else:
            out = {"value": deal_screen.commercial_value(**kw)}
    except (TypeError, ValueError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    print(json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
