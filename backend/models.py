import uuid
from datetime import datetime, timezone

from flask_sqlalchemy import SQLAlchemy

from calculations import Inputs

db = SQLAlchemy()


def _new_id() -> str:
    # Random, non-sequential id so shared links cannot be guessed by counting.
    return uuid.uuid4().hex[:12]


class Scenario(db.Model):
    __tablename__ = "scenarios"

    id = db.Column(db.String(32), primary_key=True, default=_new_id)
    name = db.Column(db.String(120), nullable=False, default="My business")
    initial_investment = db.Column(db.Numeric(16, 2), nullable=False)
    monthly_running_costs = db.Column(db.Numeric(16, 2), nullable=False)
    selling_price = db.Column(db.Numeric(16, 2), nullable=False)
    cost_per_unit = db.Column(db.Numeric(16, 2), nullable=False)
    units_sold = db.Column(db.BigInteger, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False,
                           default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False,
                           default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc))

    def apply(self, inputs: Inputs, name: str | None = None) -> None:
        self.initial_investment = inputs.initial_investment
        self.monthly_running_costs = inputs.monthly_running_costs
        self.selling_price = inputs.selling_price
        self.cost_per_unit = inputs.cost_per_unit
        self.units_sold = inputs.units_sold
        if name is not None:
            self.name = name

    def to_inputs(self) -> Inputs:
        return Inputs(
            initial_investment=float(self.initial_investment),
            monthly_running_costs=float(self.monthly_running_costs),
            selling_price=float(self.selling_price),
            cost_per_unit=float(self.cost_per_unit),
            units_sold=int(self.units_sold),
        )
