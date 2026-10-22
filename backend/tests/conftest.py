import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


@pytest.fixture
def app():
    from app import create_app
    from models import db

    # Uses TEST_DATABASE_URL (e.g. a local PostgreSQL test database) if set,
    # otherwise an in-memory SQLite database so tests run on a clean clone.
    url = os.environ.get("TEST_DATABASE_URL", "sqlite:///:memory:")
    app = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": url})
    with app.app_context():
        db.drop_all()
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()
