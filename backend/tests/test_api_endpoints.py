"""Integration tests for API endpoints"""

from datetime import datetime
from uuid import uuid4
import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch
from app.main import app
from app.database import get_db


def make_operations_overview_payload():
    now = datetime(2026, 4, 5, 9, 0, 0).isoformat()
    return {
        "summary": {
            "total_patients": 14,
            "icu_capacity": 12,
            "icu_occupied": 12,
            "overflow_patients": 2,
            "active_alerts": 1,
            "average_risk_score": 54,
            "attention_patients": 3,
            "updated_at": now,
        },
        "simulation": {
            "is_paused": False,
            "speed": 1.0,
            "active_scenario": "baseline",
            "crisis_level": 0,
            "crisis_label": "Nominal operations",
            "virtual_admissions": 2,
            "active_interventions": [
                {
                    "id": "open-surge-beds",
                    "label": "Surge beds active",
                    "value": "+2 beds",
                    "effect": "Expanded live ICU capacity to absorb overflow demand.",
                    "can_step_down": False,
                    "step_down_label": None,
                    "can_clear": True,
                    "clear_label": "Clear surge beds",
                }
            ],
            "updated_at": now,
            "last_action": "apply_intervention",
            "last_action_label": "Applied surge beds",
            "last_action_at": now,
        },
        "briefing": {
            "headline": "Capacity strain requires intervention",
            "summary": "The command room is balancing queue relief and reserve protection.",
            "changes": ["2 patients are waiting beyond the live ICU map."],
        },
        "trust": {
            "telemetry_state": "live",
            "simulator_status": "running",
            "data_source": "Live telemetry with simulated crisis overlay",
            "confidence_label": "high",
            "confidence_reason": "Telemetry is current.",
            "last_telemetry_at": now,
            "telemetry_age_seconds": 5,
        },
        "recommended_actions": [
            {
                "id": "open-surge-beds",
                "action_type": "intervention",
                "control_action": None,
                "priority": "warning",
                "title": "Open surge beds or accelerate step-down transfers",
                "rationale": "Queue pressure exceeds current capacity.",
                "owner": "Hospital ops lead",
                "state": "active",
                "state_label": "2 surge beds active",
                "state_reason": "Surge capacity is already engaged and can still be expanded by one additional step.",
                "can_apply": True,
                "apply_label": "Add 2 more surge beds",
                "projected_summary": "Projected to release queue pressure within the next 30 minutes.",
                "projected_window_minutes": 30,
                "projected_metrics": [
                    {
                        "key": "overflow_patients",
                        "label": "Overflow queue",
                        "current_value": 2,
                        "projected_value": 0,
                        "delta": -2,
                        "unit": "patients",
                    }
                ],
                "observed_summary": "Observed ICU capacity move from 12 to 14 beds while overflow shifted from 4 to 2.",
                "observed_metrics": [
                    {
                        "key": "icu_capacity",
                        "label": "ICU capacity",
                        "baseline_value": 12,
                        "current_value": 14,
                        "delta": 2,
                        "unit": "beds",
                    }
                ],
            }
        ],
        "scenario_comparison": {
            "baseline_label": "Baseline operations",
            "current_label": "Nominal operations",
            "summary_metrics": [],
            "resource_metrics": [],
        },
        "replay_frames": [
            {
                "id": "current-state",
                "timestamp": now,
                "title": "Current command state",
                "severity": "warning",
                "phase_label": "Current state",
                "summary": "Latest reconstructed checkpoint.",
                "icu_occupied": 12,
                "overflow_patients": 2,
                "active_alerts": 1,
                "attention_patients": 3,
                "focus_note": "Overflow pressure is the leading issue.",
            }
        ],
        "bed_heatmap": [],
        "triage_queue": [],
        "resource_cards": [],
        "resource_forecast": [],
        "timeline": [],
        "operator_activity": [
            {
                "id": "evt-surge",
                "timestamp": now,
                "action_key": "apply_intervention",
                "action_label": "Applied surge beds",
                "event_type": "intervention",
                "severity": "warning",
                "title": "Surge beds opened",
                "description": "Two surge-capacity beds were activated and queue pressure was reduced.",
                "intervention_id": "open-surge-beds",
                "scenario_label": "Nominal operations",
                "speed": None,
            }
        ],
        "incident_handoff": {
            "title": "Nominal operations incident handoff",
            "generated_at": now,
            "status": "watch",
            "status_label": "Monitored pressure",
            "scenario_label": "Nominal operations",
            "summary": "Nominal operations is currently running with ICU occupancy at 12/12 beds, 2 patients in overflow, and 1 active telemetry alert.",
            "command_snapshot": [
                {
                    "key": "icu_occupied",
                    "label": "ICU occupied",
                    "value": "12/12 beds",
                }
            ],
            "immediate_risks": [
                "2 patients still exceed live ICU routing capacity."
            ],
            "active_interventions": [
                "Surge beds active (+2 beds): Expanded live ICU capacity to absorb overflow demand."
            ],
            "recent_actions": [
                "09:00 UTC | Applied surge beds"
            ],
            "next_steps": [
                "Open surge beds or accelerate step-down transfers (Owner: Hospital ops lead)"
            ],
            "export_filename": "icu-incident-handoff-20260405-090000",
            "markdown": "# Nominal operations incident handoff",
        },
    }


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
        assert data["service"] == "st-jude-icu-digital-twin-backend"

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


class TestOperationsEndpoints:
    def test_overview_serializes_nested_patient_ids(self, client, mock_db):
        alert_result = MagicMock()
        alert_result.mappings.return_value.all.return_value = []
        mock_db.execute.return_value = alert_result

        patients = [
            {
                "patient_id": uuid4(),
                "patient_raw_id": f"P{i:05d}",
                "parity_flag": "even",
                "name": f"Patient {i}",
                "age": 30 + i,
                "ward": f"ICU-{(i % 3) + 1}",
                "last_bpm": 72 + (i % 5),
                "last_oxygen": 98 - (i % 3),
                "last_vitals_timestamp": datetime(2026, 4, 4, 12, 0, 0).isoformat(),
                "quality_flag": "good",
                "prescription_count": 2,
                "has_active_alert": i == 1,
            }
            for i in range(1, 14)
        ]

        with patch("app.services.operations_center._load_patients", return_value=patients):
            with patch(
                "app.services.operations_center.get_simulation_state",
                return_value={
                    "is_paused": False,
                    "speed": 1.0,
                    "active_scenario": "baseline",
                    "crisis_level": 0,
                    "crisis_label": "Baseline operations",
                    "virtual_admissions": 0,
                    "surge_bed_bonus": 2,
                    "oxygen_reserve_bonus": 0,
                    "staffing_support_bonus": 0,
                    "updated_at": datetime(2026, 4, 4, 12, 0, 0).isoformat(),
                    "last_action": "reset",
                },
            ):
                with patch(
                    "app.services.operations_center.get_simulation_events",
                    return_value=[],
                ):
                    response = client.get("/api/ops/overview")

        assert response.status_code == 200
        data = response.json()
        patient_ids = {str(patient["patient_id"]) for patient in patients}
        assert len(data["bed_heatmap"]) == 14
        assert len(data["triage_queue"]) == 0
        assert "briefing" in data
        assert "trust" in data
        assert "recommended_actions" in data
        assert "scenario_comparison" in data
        assert "replay_frames" in data
        assert isinstance(data["recommended_actions"], list)
        assert data["recommended_actions"][0]["action_type"] in {"intervention", "control", "advisory"}
        assert data["recommended_actions"][0]["state"] in {
            "recommended",
            "active",
            "saturated",
            "recently_applied",
        }
        assert "projected_metrics" in data["recommended_actions"][0]
        assert "observed_metrics" in data["recommended_actions"][0]
        assert data["recommended_actions"][0]["projected_window_minutes"] == 30
        assert isinstance(data["simulation"]["active_interventions"], list)
        assert data["simulation"]["active_interventions"][0]["id"] == "open-surge-beds"
        assert data["simulation"]["last_action_label"]
        assert isinstance(data["scenario_comparison"]["summary_metrics"], list)
        assert isinstance(data["replay_frames"], list)
        assert isinstance(data["operator_activity"], list)
        assert data["incident_handoff"]["title"]
        assert data["incident_handoff"]["markdown"].startswith("# ")
        assert data["bed_heatmap"][0]["patient"]["patient_id"] in patient_ids
        assert isinstance(data["bed_heatmap"][0]["patient"]["risk_reasons"], list)
        assert data["trust"]["telemetry_state"] in {"live", "watch", "paused"}
        assert all(
            event["patient_id"] is None or isinstance(event["patient_id"], str)
            for event in data["timeline"]
        )

    def test_control_endpoint_accepts_apply_intervention(self, client):
        payload = make_operations_overview_payload()

        with patch(
            "app.api.operations.apply_simulation_action",
            return_value=payload,
        ) as apply_action:
            response = client.post(
                "/api/ops/control",
                json={
                    "action": "apply_intervention",
                    "intervention_id": "open-surge-beds",
                },
            )

        assert response.status_code == 200
        assert response.json()["simulation"]["last_action"] == "apply_intervention"
        apply_action.assert_called_once()
        assert apply_action.call_args.kwargs["intervention_id"] == "open-surge-beds"

    @pytest.mark.parametrize(
        ("action", "expected_last_action"),
        [
            ("step_down_intervention", "step_down_intervention"),
            ("clear_intervention", "clear_intervention"),
        ],
    )
    def test_control_endpoint_accepts_intervention_lifecycle_actions(
        self,
        client,
        action,
        expected_last_action,
    ):
        payload = make_operations_overview_payload()
        payload["simulation"]["last_action"] = expected_last_action

        with patch(
            "app.api.operations.apply_simulation_action",
            return_value=payload,
        ) as apply_action:
            response = client.post(
                "/api/ops/control",
                json={
                    "action": action,
                    "intervention_id": "open-surge-beds",
                },
            )

        assert response.status_code == 200
        assert response.json()["simulation"]["last_action"] == expected_last_action
        apply_action.assert_called_once()
        assert apply_action.call_args.kwargs["intervention_id"] == "open-surge-beds"
