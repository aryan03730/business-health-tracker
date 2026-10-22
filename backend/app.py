import os
from dataclasses import asdict

from flask import Flask, jsonify, request
from flask_cors import CORS
from werkzeug.exceptions import HTTPException

from calculations import ValidationError, calculate, validate_inputs
from models import Scenario, db
from suggestions import build_suggestions

MAX_NAME_LENGTH = 120


def _database_url() -> str:
    url = os.environ.get("DATABASE_URL", "postgresql+psycopg://bht:bht@localhost:5432/bht")
    # Hosts such as Render and Neon hand out postgres:// or postgresql:// URLs;
    # SQLAlchemy needs the driver named explicitly.
    if url.startswith("postgres://"):
        url = "postgresql+psycopg://" + url[len("postgres://"):]
    elif url.startswith("postgresql://"):
        url = "postgresql+psycopg://" + url[len("postgresql://"):]
    return url


def _clean_name(data: dict) -> str | None:
    name = data.get("name")
    if name is None:
        return None
    if not isinstance(name, str):
        raise ValidationError({"name": "Name must be text."})
    name = name.strip()
    if not name:
        return None
    if len(name) > MAX_NAME_LENGTH:
        raise ValidationError({"name": f"Name must be {MAX_NAME_LENGTH} characters or fewer."})
    return name


def _json_body() -> dict:
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        raise ValidationError({"_": "Send the inputs as a JSON object."})
    return data


def _scenario_payload(s: Scenario) -> dict:
    inputs = s.to_inputs()
    return {
        "id": s.id,
        "name": s.name,
        "inputs": asdict(inputs),
        "results": calculate(inputs).to_dict(),
        "created_at": s.created_at.isoformat(),
        "updated_at": s.updated_at.isoformat(),
    }


def _get_or_404(scenario_id: str) -> Scenario:
    s = db.session.get(Scenario, scenario_id)
    if s is None:
        raise LookupError
    return s


def create_app(config: dict | None = None) -> Flask:
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = _database_url()
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {"pool_pre_ping": True}
    app.json.sort_keys = False
    if config:
        app.config.update(config)

    origins = os.environ.get("CORS_ORIGINS", "*")
    CORS(app, origins=[o.strip() for o in origins.split(",")])

    db.init_app(app)
    with app.app_context():
        db.create_all()

    # ---- errors: always JSON, never an HTML stack trace ----

    @app.errorhandler(ValidationError)
    def handle_validation(err: ValidationError):
        return jsonify(error="validation_error",
                       message="Some inputs need fixing.",
                       fields=err.errors), 400

    @app.errorhandler(LookupError)
    def handle_not_found(_err):
        return jsonify(error="not_found", message="Scenario not found."), 404

    @app.errorhandler(HTTPException)
    def handle_http(err: HTTPException):
        return jsonify(error=err.name.lower().replace(" ", "_"), message=err.description), err.code

    @app.errorhandler(Exception)
    def handle_unexpected(err: Exception):
        app.logger.exception(err)
        return jsonify(error="server_error", message="Something went wrong on our side."), 500

    # ---- routes ----

    @app.get("/health")
    def health():
        return jsonify(status="ok")

    @app.post("/scenarios")
    def create_scenario():
        data = _json_body()
        inputs = validate_inputs(data)
        s = Scenario()
        s.apply(inputs, _clean_name(data))
        db.session.add(s)
        db.session.commit()
        return jsonify(_scenario_payload(s)), 201

    @app.get("/scenarios/<scenario_id>")
    def get_scenario(scenario_id):
        return jsonify(_scenario_payload(_get_or_404(scenario_id)))

    @app.put("/scenarios/<scenario_id>")
    def update_scenario(scenario_id):
        s = _get_or_404(scenario_id)
        data = _json_body()
        inputs = validate_inputs(data)
        s.apply(inputs, _clean_name(data))
        db.session.commit()
        return jsonify(_scenario_payload(s))

    @app.get("/scenarios/<scenario_id>/dashboard")
    def dashboard(scenario_id):
        s = _get_or_404(scenario_id)
        inputs = s.to_inputs()
        results = calculate(inputs)
        suggestions = build_suggestions(inputs, results)
        return jsonify(
            id=s.id,
            name=s.name,
            status=results.status,
            monthly_profit=results.monthly_profit,
            break_even_units=results.break_even_units,
            break_even_sales=results.break_even_sales,
            units_sold=inputs.units_sold,
            sales_gap_units=results.sales_gap_units,
            payback_months=results.payback_months,
            suggestion=suggestions[0] if suggestions else None,
            other_suggestions=suggestions[1:],
        )

    return app


if __name__ == "__main__":
    create_app().run(debug=True, port=int(os.environ.get("PORT", 5000)))
