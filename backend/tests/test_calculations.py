import pytest

from calculations import (
    Inputs,
    ValidationError,
    break_even_units,
    calculate,
    payback_months,
    sales_gap_units,
    status,
    validate_inputs,
)
from suggestions import build_suggestions

# Worked example from the scope document (section 5). A test case, not real business data.
WORKED_EXAMPLE = {
    "initial_investment": 100_000,
    "monthly_running_costs": 30_000,
    "selling_price": 150,
    "cost_per_unit": 50,
    "units_sold": 250,
}


def test_worked_example_matches_scope_document():
    r = calculate(validate_inputs(WORKED_EXAMPLE))
    assert r.profit_per_unit == 100
    assert r.break_even_units == 300
    assert r.break_even_sales == 45_000
    assert r.monthly_profit == -5_000
    assert r.sales_gap_units == 50
    assert r.status == "red"
    assert r.payback_months is None


def test_worked_example_suggestion_is_targeted_promotion():
    inputs = validate_inputs(WORKED_EXAMPLE)
    s = build_suggestions(inputs, calculate(inputs))
    assert s[0].startswith("You are 50 units short of break-even")
    assert "promotion" in s[0]
    assert not any("supplier" in x for x in s)  # cost is 1/3 of price, under the 1/2 rule


def test_profitable_business_has_payback_and_green_status():
    r = calculate(validate_inputs({**WORKED_EXAMPLE, "units_sold": 400}))
    assert r.monthly_profit == 10_000
    assert r.payback_months == 10
    assert r.sales_gap_units == -100
    assert r.status == "green"


@pytest.mark.parametrize(
    "units, expected",
    [(250, "red"), (299, "red"), (300, "yellow"), (329, "yellow"), (330, "green")],
)
def test_status_thresholds_around_break_even(units, expected):
    r = calculate(validate_inputs({**WORKED_EXAMPLE, "units_sold": units}))
    assert r.status == expected


def test_status_function_directly():
    assert status(-1, 0, 10) == "red"
    assert status(0, 10, 10) == "yellow"
    assert status(5, 11, 10) == "green"


def test_fractional_break_even_rounds_gap_up():
    # 1000 / 3 = 333.33 units -> you need 334 whole units
    assert sales_gap_units(break_even_units(1000, 3), 0) == 334


def test_payback_not_reached_without_profit():
    assert payback_months(100_000, 0) is None
    assert payback_months(100_000, -5) is None
    assert payback_months(0, 500) == 0


def test_break_even_impossible_when_unit_profit_not_positive():
    with pytest.raises(ValueError):
        break_even_units(30_000, 0)


def test_zero_running_costs():
    r = calculate(Inputs(0, 0, 10, 4, 0))
    assert r.break_even_units == 0
    assert r.monthly_profit == 0
    assert r.status == "green"


def test_high_unit_cost_triggers_supplier_suggestion():
    inputs = validate_inputs({**WORKED_EXAMPLE, "cost_per_unit": 90})
    assert any("supplier" in s for s in build_suggestions(inputs, calculate(inputs)))


def test_large_gap_suggests_cost_review():
    inputs = validate_inputs({**WORKED_EXAMPLE, "units_sold": 100})
    s = build_suggestions(inputs, calculate(inputs))
    assert s[0].startswith("You need to sell 200 units more a month")


def test_yellow_suggests_cushion():
    inputs = validate_inputs({**WORKED_EXAMPLE, "units_sold": 310})
    s = build_suggestions(inputs, calculate(inputs))
    assert "about 330 units" in s[0]


def test_every_status_gets_at_least_one_suggestion():
    for units in (100, 250, 310, 400):
        inputs = validate_inputs({**WORKED_EXAMPLE, "units_sold": units})
        assert build_suggestions(inputs, calculate(inputs))


# ---- validation ----

def test_accepts_numeric_strings():
    i = validate_inputs({k: str(v) for k, v in WORKED_EXAMPLE.items()})
    assert i.units_sold == 250 and i.selling_price == 150


@pytest.mark.parametrize(
    "field, value, message_part",
    [
        ("selling_price", 0, "greater than zero"),
        ("selling_price", -10, "greater than zero"),
        ("cost_per_unit", -1, "cannot be negative"),
        ("monthly_running_costs", -1, "cannot be negative"),
        ("initial_investment", -1, "cannot be negative"),
        ("units_sold", -3, "cannot be negative"),
        ("units_sold", 2.5, "whole number"),
        ("units_sold", "abc", "must be a number"),
        ("selling_price", None, "is required"),
        ("selling_price", "", "is required"),
        ("selling_price", True, "must be a number"),
        ("selling_price", "nan", "must be a number"),
        ("initial_investment", 1e15, "too large"),
    ],
)
def test_invalid_values(field, value, message_part):
    with pytest.raises(ValidationError) as exc:
        validate_inputs({**WORKED_EXAMPLE, field: value})
    assert message_part in exc.value.errors[field]


def test_selling_price_below_or_equal_to_cost_is_rejected():
    for cost in (150, 200):
        with pytest.raises(ValidationError) as exc:
            validate_inputs({**WORKED_EXAMPLE, "cost_per_unit": cost})
        assert "higher than the cost per unit" in exc.value.errors["selling_price"]


def test_missing_fields_are_all_reported():
    with pytest.raises(ValidationError) as exc:
        validate_inputs({})
    assert set(exc.value.errors) == {
        "initial_investment", "monthly_running_costs", "selling_price", "cost_per_unit", "units_sold",
    }


def test_non_object_body_is_rejected():
    with pytest.raises(ValidationError):
        validate_inputs([1, 2, 3])
