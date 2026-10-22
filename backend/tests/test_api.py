WORKED_EXAMPLE = {
    "name": "Worked example (test case)",
    "initial_investment": 100000,
    "monthly_running_costs": 30000,
    "selling_price": 150,
    "cost_per_unit": 50,
    "units_sold": 250,
}


def create(client, body=None):
    return client.post("/scenarios", json=body or WORKED_EXAMPLE)


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.get_json() == {"status": "ok"}


def test_create_returns_id_inputs_and_results(client):
    r = create(client)
    assert r.status_code == 201
    body = r.get_json()
    assert body["id"]
    assert body["name"] == "Worked example (test case)"
    assert body["inputs"]["units_sold"] == 250
    assert body["results"] == {
        "profit_per_unit": 100,
        "break_even_units": 300,
        "break_even_sales": 45000,
        "monthly_profit": -5000,
        "sales_gap_units": 50,
        "payback_months": None,
        "status": "red",
    }


def test_get_scenario(client):
    sid = create(client).get_json()["id"]
    r = client.get(f"/scenarios/{sid}")
    assert r.status_code == 200
    assert r.get_json()["results"]["break_even_units"] == 300


def test_update_scenario_recalculates(client):
    sid = create(client).get_json()["id"]
    r = client.put(f"/scenarios/{sid}", json={**WORKED_EXAMPLE, "units_sold": 400})
    assert r.status_code == 200
    res = r.get_json()["results"]
    assert res["monthly_profit"] == 10000
    assert res["payback_months"] == 10
    assert res["status"] == "green"
    assert client.get(f"/scenarios/{sid}").get_json()["inputs"]["units_sold"] == 400


def test_dashboard_for_worked_example(client):
    sid = create(client).get_json()["id"]
    r = client.get(f"/scenarios/{sid}/dashboard")
    assert r.status_code == 200
    d = r.get_json()
    assert d["status"] == "red"
    assert d["sales_gap_units"] == 50
    assert d["monthly_profit"] == -5000
    assert d["payback_months"] is None
    assert "50 units short" in d["suggestion"]


def test_default_name_when_missing(client):
    body = {k: v for k, v in WORKED_EXAMPLE.items() if k != "name"}
    assert create(client, body).get_json()["name"] == "My business"


def test_unknown_scenario_is_404_json(client):
    for path in ("/scenarios/nope", "/scenarios/nope/dashboard"):
        r = client.get(path)
        assert r.status_code == 404
        assert r.get_json()["error"] == "not_found"
    r = client.put("/scenarios/nope", json=WORKED_EXAMPLE)
    assert r.status_code == 404


def test_validation_error_lists_fields(client):
    r = create(client, {**WORKED_EXAMPLE, "selling_price": 40, "units_sold": -1})
    assert r.status_code == 400
    body = r.get_json()
    assert body["error"] == "validation_error"
    assert "higher than the cost per unit" in body["fields"]["selling_price"]
    assert "cannot be negative" in body["fields"]["units_sold"]


def test_invalid_update_does_not_change_saved_values(client):
    sid = create(client).get_json()["id"]
    r = client.put(f"/scenarios/{sid}", json={**WORKED_EXAMPLE, "selling_price": 0})
    assert r.status_code == 400
    assert client.get(f"/scenarios/{sid}").get_json()["inputs"]["selling_price"] == 150


def test_non_json_body_is_400(client):
    r = client.post("/scenarios", data="not json", content_type="text/plain")
    assert r.status_code == 400
    assert r.get_json()["error"] == "validation_error"


def test_name_too_long(client):
    r = create(client, {**WORKED_EXAMPLE, "name": "x" * 121})
    assert r.status_code == 400
    assert "name" in r.get_json()["fields"]


def test_unknown_route_is_json_404(client):
    r = client.get("/does-not-exist")
    assert r.status_code == 404
    assert r.is_json


def test_wrong_method_is_405(client):
    r = client.delete("/scenarios/abc")
    assert r.status_code == 405
    assert r.is_json
