"""Core business-health calculations.

All figures use a single monthly view and a single currency. These functions are
pure (no database, no Flask) so they can be tested in isolation.
"""
from __future__ import annotations

import math
import re
from dataclasses import dataclass, asdict

# Status thresholds (scope doc, section 10, decision 1).
# Red:    monthly result is a loss.
# Yellow: break-even or profitable, but units sold are less than GREEN_MARGIN above break-even.
# Green:  units sold are at least GREEN_MARGIN above break-even.
GREEN_MARGIN = 0.10

FIELDS = {
    "initial_investment": "Initial investment",
    "monthly_running_costs": "Monthly running costs",
    "selling_price": "Selling price per unit",
    "cost_per_unit": "Cost per unit",
    "units_sold": "Units sold this month",
}

MAX_VALUE = 1_000_000_000_000  # keeps numbers sane and inside the DB column size

# Text accepted as a number, after commas, "$" and spaces are removed.
# Must match NUMBER_PATTERN in frontend/src/validation.js.
NUMBER_PATTERN = re.compile(r"-?(\d+\.?\d*|\.\d+)")


class ValidationError(ValueError):
    """Raised when inputs are missing or invalid. `errors` maps field -> message."""

    def __init__(self, errors: dict[str, str]):
        super().__init__("Invalid inputs")
        self.errors = errors


@dataclass(frozen=True)
class Inputs:
    initial_investment: float
    monthly_running_costs: float
    selling_price: float
    cost_per_unit: float
    units_sold: int


@dataclass(frozen=True)
class Results:
    profit_per_unit: float
    break_even_units: float
    break_even_sales: float
    monthly_profit: float
    sales_gap_units: int
    payback_months: float | None
    status: str

    def to_dict(self) -> dict:
        return asdict(self)


def _to_number(raw, label: str) -> float:
    if isinstance(raw, bool):
        raise ValueError(f"{label} must be a number.")
    if raw is None:
        raise ValueError(f"{label} is required.")
    if isinstance(raw, str):
        text = re.sub(r"[,$\s]", "", raw)  # same cleanup as the frontend
        if text == "":
            raise ValueError(f"{label} is required.")
        if not NUMBER_PATTERN.fullmatch(text):
            raise ValueError(f"{label} must be a number.")
        raw = text
    elif not isinstance(raw, (int, float)):
        raise ValueError(f"{label} must be a number.")
    value = float(raw)
    if math.isnan(value) or math.isinf(value):
        raise ValueError(f"{label} must be a number.")
    if value > MAX_VALUE:
        raise ValueError(f"{label} is too large.")
    return value


def validate_inputs(data: dict) -> Inputs:
    """Check raw input (e.g. JSON) and return clean Inputs, or raise ValidationError."""
    if not isinstance(data, dict):
        raise ValidationError({"_": "Send the inputs as a JSON object."})

    errors: dict[str, str] = {}
    values: dict[str, float] = {}

    for field, label in FIELDS.items():
        try:
            values[field] = _to_number(data.get(field), label)
        except ValueError as exc:
            errors[field] = str(exc)

    def check(field, ok, message):
        if field in values and field not in errors and not ok(values[field]):
            errors[field] = message

    check("initial_investment", lambda v: v >= 0, "Initial investment cannot be negative.")
    check("monthly_running_costs", lambda v: v >= 0, "Monthly running costs cannot be negative.")
    check("selling_price", lambda v: v > 0, "Selling price must be greater than zero.")
    check("cost_per_unit", lambda v: v >= 0, "Cost per unit cannot be negative.")
    check("units_sold", lambda v: v >= 0, "Units sold cannot be negative.")
    check("units_sold", lambda v: v == int(v), "Units sold must be a whole number.")

    if (
        "selling_price" in values and "cost_per_unit" in values
        and "selling_price" not in errors and "cost_per_unit" not in errors
        and values["selling_price"] <= values["cost_per_unit"]
    ):
        errors["selling_price"] = (
            "Selling price must be higher than the cost per unit, "
            "otherwise every sale loses money and break-even is not possible."
        )

    if errors:
        raise ValidationError(errors)

    return Inputs(
        initial_investment=values["initial_investment"],
        monthly_running_costs=values["monthly_running_costs"],
        selling_price=values["selling_price"],
        cost_per_unit=values["cost_per_unit"],
        units_sold=int(values["units_sold"]),
    )


def profit_per_unit(selling_price: float, cost_per_unit: float) -> float:
    return selling_price - cost_per_unit


def break_even_units(monthly_running_costs: float, unit_profit: float) -> float:
    if unit_profit <= 0:
        raise ValueError("Break-even is not possible when profit per unit is zero or negative.")
    return monthly_running_costs / unit_profit


def break_even_sales(be_units: float, selling_price: float) -> float:
    return be_units * selling_price


def monthly_profit(units_sold: int, unit_profit: float, monthly_running_costs: float) -> float:
    return units_sold * unit_profit - monthly_running_costs


def sales_gap_units(be_units: float, units_sold: int) -> int:
    """Whole units still needed to break even. Zero or negative means costs are covered."""
    return math.ceil(round(be_units - units_sold, 9))


def payback_months(initial_investment: float, profit: float) -> float | None:
    """Months to earn back the investment. None while the business is not making a profit."""
    if profit <= 0:
        return None
    return initial_investment / profit


def status(profit: float, units_sold: int, be_units: float) -> str:
    if profit < 0:
        return "red"
    if units_sold >= be_units * (1 + GREEN_MARGIN):
        return "green"
    return "yellow"


def calculate(inputs: Inputs) -> Results:
    unit_profit = profit_per_unit(inputs.selling_price, inputs.cost_per_unit)
    be_units = break_even_units(inputs.monthly_running_costs, unit_profit)
    profit = monthly_profit(inputs.units_sold, unit_profit, inputs.monthly_running_costs)
    payback = payback_months(inputs.initial_investment, profit)

    return Results(
        profit_per_unit=round(unit_profit, 2),
        break_even_units=round(be_units, 2),
        break_even_sales=round(break_even_sales(be_units, inputs.selling_price), 2),
        monthly_profit=round(profit, 2),
        sales_gap_units=sales_gap_units(be_units, inputs.units_sold),
        payback_months=None if payback is None else round(payback, 1),
        status=status(profit, inputs.units_sold, be_units),
    )
