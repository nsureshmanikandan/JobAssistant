import pytest
from fastapi.testclient import TestClient
from sqlmodel import SQLModel, create_engine, Session
from sqlalchemy.pool import StaticPool
from app.main import app
from app.db import session as db_session


@pytest.fixture
def client():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    SQLModel.metadata.create_all(engine)

    def override_get_session():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[db_session.get_session] = override_get_session
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_get_criteria_returns_defaults(client):
    response = client.get("/settings/criteria")
    assert response.status_code == 200
    body = response.json()
    assert body["location"] == "Chennai"
    assert body["salary_min_lakhs"] == 45


def test_put_criteria_updates_fields(client):
    response = client.put(
        "/settings/criteria",
        json={"location": "Bangalore", "salary_min_lakhs": 50, "salary_max_lakhs": 70},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["location"] == "Bangalore"
    assert body["salary_min_lakhs"] == 50
    assert body["salary_max_lakhs"] == 70

    # Persisted, not just echoed back
    follow_up = client.get("/settings/criteria")
    assert follow_up.json()["location"] == "Bangalore"
