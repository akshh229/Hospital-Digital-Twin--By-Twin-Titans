"""Integration tests for API endpoints"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch
from app.main import app
from app.database import get_db


@pytest.fixture
def mock_db():
    db = MagicMock()
    yield db


@pytest.fixture
def client(mock_db):
    app.dependency_overrides[get_db] = lambda: mock_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


class TestHealthEndpoint:
    def test_health_check(self):
        with TestClient(app) as c:
            response = c.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "lazarus-backend"

    def test_root_endpoint(self):
        with TestClient(app) as c:
            response = c.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data


class TestPatientEndpoints:
    def test_list_patients(self, client, mock_db):
        mock_result = MagicMock()
        mock_result._mapping = {
            "patient_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
            "patient_raw_id": "P00001",
            "parity_flag": "even",
            "name_cipher": "JOHNSMITH",
            "age": 45,
            "ward": "ICU-1",
            "last_bpm": 72,
            "last_oxygen": 98,
            "last_vitals_timestamp": None,
            "quality_flag": "good",
            "prescription_count": 3,
            "has_active_alert": False,
        }
        mock_db.execute.return_value = [mock_result]

        response = client.get("/api/patients")
        assert response.status_code == 200
        assert response.json()[0]["name"] == "John Smith"


class TestAlertEndpoints:
    def test_list_alerts(self, client, mock_db):
        mock_db.execute.return_value = []

        response = client.get("/api/alerts")
        assert response.status_code == 200
        assert response.json() == []
