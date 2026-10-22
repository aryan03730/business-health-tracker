"""Rule-based suggestions (scope doc, section 6).

Each rule is a plain-language check. Rules are tried in order and every match is
returned; the first match is the one shown on the dashboard. Edit the wording here.
"""
from __future__ import annotations

import math

from calculations import GREEN_MARGIN, Inputs, Results

# A sales gap of up to this share of break-even units counts as "small".
SMALL_GAP_SHARE = 0.20
# Cost per unit above this share of the selling price triggers a supplier review.
HIGH_UNIT_COST_SHARE = 0.50
# Payback slower than this (months) is called out even when profitable.
SLOW_PAYBACK_MONTHS = 24


def _units(n: int) -> str:
    return f"{n:,} unit" + ("" if n == 1 else "s")


def build_suggestions(inputs: Inputs, results: Results) -> list[str]:
    out: list[str] = []
    gap = results.sales_gap_units
    be = results.break_even_units

    # 1. Loss, but close to break-even: a targeted push can close the gap.
    if results.status == "red" and gap <= be * SMALL_GAP_SHARE:
        out.append(
            f"You are {_units(gap)} short of break-even each month. A short, targeted "
            f"promotion to your regular customers could close that gap."
        )

    # 2. Loss and far from break-even: sales alone may not fix it.
    if results.status == "red" and gap > be * SMALL_GAP_SHARE:
        out.append(
            f"You need to sell {_units(gap)} more a month to cover your costs. Look at your "
            f"largest monthly cost first, and consider testing a small price increase."
        )

    # 3. Thin margin per unit.
    if inputs.cost_per_unit > inputs.selling_price * HIGH_UNIT_COST_SHARE:
        out.append(
            "Each unit costs you more than half of its selling price. Ask your supplier "
            "for better terms, or get a quote from at least one other supplier."
        )

    # 4. Just above break-even: build a cushion.
    if results.status == "yellow":
        target = math.ceil(round(be * (1 + GREEN_MARGIN), 9))
        out.append(
            f"You are covering your costs, but only just. Aim for about {_units(target)} "
            f"a month to give yourself a safety cushion."
        )

    # 5. Profitable but slow to earn back the investment.
    if results.payback_months is not None and results.payback_months > SLOW_PAYBACK_MONTHS:
        out.append(
            f"At this rate it takes about {results.payback_months:g} months to earn back your "
            f"investment. Growing monthly sales is the quickest way to shorten that."
        )

    # 6. Healthy.
    if results.status == "green":
        out.append(
            "You are comfortably above break-even. Keep checking each month, and set aside "
            "part of the profit as a cash reserve."
        )

    return out
