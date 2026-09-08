import os
import pytest
import sqlite3

# Point to a test database instead of production
os.environ["DB_FILE"] = "test_smarthome.db"

from app.main import app
from app.db.connection import get_db_connection, run_migrations
from fastapi.testclient import TestClient


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    if os.path.exists("test_smarthome.db"):
        try:
            os.remove("test_smarthome.db")
        except Exception:
            pass

    # Run migrations on test DB
    run_migrations()

    yield

    if os.path.exists("test_smarthome.db"):
        try:
            os.remove("test_smarthome.db")
        except Exception:
            pass


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture
def db_conn():
    conn = get_db_connection()
    yield conn
    conn.close()
