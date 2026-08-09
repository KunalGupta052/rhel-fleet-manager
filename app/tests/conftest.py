import os
import sys

# app/ uses flat imports (`from models import db`, not a proper package),
# matching how it's actually run in production (`cd app && gunicorn app:app`,
# per the Procfile). So tests need app/ on sys.path too, or these imports
# break — this mirrors production rather than fighting it.
APP_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "app")
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)

import pytest
from app import create_app


@pytest.fixture
def app():
    """A fresh Flask app per test, backed by an in-memory SQLite database.
    Nothing here touches the real fleet.db used in dev/production."""
    application = create_app({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
    })
    yield application


@pytest.fixture
def client(app):
    return app.test_client()
