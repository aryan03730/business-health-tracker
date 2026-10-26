import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


def _test_database_url() -> str:
    """In-memory SQLite by default, or TEST_DATABASE_URL if set.

    WARNING: the tests drop every table in this database before and after each
    test. Point TEST_DATABASE_URL only at a throwaway test database, never at
    the real one (local or Neon).
    """
    url = os.environ.get("TEST_DATABASE_URL")
    if not url:
        return "sqlite:///:memory:"

    from sqlalchemy.engine import make_url

    db_name = make_url(url).database or ""
    if "test" not in db_name.lower():
        pytest.exit(
            f"Refusing to run: TEST_DATABASE_URL points at database '{db_name}'. "
            "The tests delete all tables, so the database name must contain 'test' "
            "(for example bht_test).",
            returncode=2,
        )
    return url


@pytest.fixture
def app():
    from app import create_app
    from models import db

    app = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": _test_database_url()})
    with app.app_context():
        db.drop_all()
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()
