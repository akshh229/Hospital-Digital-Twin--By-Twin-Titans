"""Tests for slot-based identity reconciliation."""

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from app.services.identity_reconciler import _assign_slot_parities, reconcile_patient_identity


class TestSlotAssignments:
    def test_single_slot_uses_majority_parity(self):
        assignments = _assign_slot_parities(
            [
                {
                    "sample_slot": 1,
                    "sample_count": 10,
                    "even_count": 8,
                    "odd_count": 2,
                    "even_share": 0.8,
                    "odd_share": 0.2,
                }
            ]
        )

        assert assignments == {
            1: {
                "parity_flag": "even",
                "sample_count": 10,
                "confidence_score": 0.8,
            }
        }

    def test_multiple_slots_claim_even_heaviest_slot_and_rest_odd(self):
        assignments = _assign_slot_parities(
            [
                {
                    "sample_slot": 1,
                    "sample_count": 12,
                    "even_count": 10,
                    "odd_count": 2,
                    "even_share": 10 / 12,
                    "odd_share": 2 / 12,
                },
                {
                    "sample_slot": 2,
                    "sample_count": 12,
                    "even_count": 3,
                    "odd_count": 9,
                    "even_share": 3 / 12,
                    "odd_share": 9 / 12,
                },
            ]
        )

        assert assignments[1]["parity_flag"] == "even"
        assert assignments[1]["confidence_score"] == round(10 / 12, 2)
        assert assignments[2]["parity_flag"] == "odd"
        assert assignments[2]["confidence_score"] == round(9 / 12, 2)


class TestReconcilePatientIdentity:
    def test_reconcile_returns_alias_for_row_slot(self):
        mock_db = MagicMock()
        mock_execute_result = MagicMock()
        mock_execute_result.first.return_value = (2,)
        mock_db.execute.return_value = mock_execute_result

        with patch(
            "app.services.identity_reconciler.ensure_patient_aliases",
            return_value={2: SimpleNamespace(patient_id="odd-uuid")},
        ):
            result = reconcile_patient_identity("P00001", 42, mock_db)

        assert result == "odd-uuid"

    def test_reconcile_raises_when_slot_lookup_fails(self):
        mock_db = MagicMock()
        mock_execute_result = MagicMock()
        mock_execute_result.first.return_value = None
        mock_db.execute.return_value = mock_execute_result

        with patch(
            "app.services.identity_reconciler.ensure_patient_aliases",
            return_value={1: SimpleNamespace(patient_id="even-uuid")},
        ):
            with pytest.raises(ValueError, match="Telemetry row 99 not found"):
                reconcile_patient_identity("P00001", 99, mock_db)
