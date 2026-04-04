"""Tests for alert engine"""

import pytest
from unittest.mock import MagicMock
from datetime import datetime
from app.services.alert_engine import process_vitals_for_alerts


class TestAlertEngine:
    def test_normal_vitals_no_alert(self):
        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_query.filter_by.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.first.return_value = None
        mock_db.query.return_value = mock_query

        process_vitals_for_alerts("test-uuid", 72, 98, mock_db)

        mock_db.add.assert_not_called()
        mock_db.commit.assert_called_once()

    def test_abnormal_high_bpm_creates_alert(self):
        mock_db = MagicMock()

        # First query (open alert check) -> None
        # Second query (recent closed check) -> None
        open_query = MagicMock()
        open_query.filter_by.return_value = open_query
        open_query.order_by.return_value = open_query
        open_query.first.return_value = None

        closed_query = MagicMock()
        closed_query.filter_by.return_value = closed_query
        closed_query.filter.return_value = closed_query
        closed_query.order_by.return_value = closed_query
        closed_query.first.return_value = None

        mock_db.query.side_effect = [open_query, closed_query]

        process_vitals_for_alerts("test-uuid", 150, 95, mock_db)

        mock_db.add.assert_called_once()
        alert = mock_db.add.call_args[0][0]
        assert alert.status == "pending"
        assert alert.last_bpm == 150

    def test_abnormal_low_bpm_creates_alert(self):
        mock_db = MagicMock()

        open_query = MagicMock()
        open_query.filter_by.return_value = open_query
        open_query.order_by.return_value = open_query
        open_query.first.return_value = None

        closed_query = MagicMock()
        closed_query.filter_by.return_value = closed_query
        closed_query.filter.return_value = closed_query
        closed_query.order_by.return_value = closed_query
        closed_query.first.return_value = None

        mock_db.query.side_effect = [open_query, closed_query]

        process_vitals_for_alerts("test-uuid", 45, 95, mock_db)

        mock_db.add.assert_called_once()
        alert = mock_db.add.call_args[0][0]
        assert alert.last_bpm == 45

    def test_open_alert_gets_updated(self):
        mock_db = MagicMock()
        mock_alert = MagicMock()
        mock_alert.status = "open"
        mock_alert.consecutive_abnormal_count = 1
        mock_alert.consecutive_normal_count = 0

        mock_query = MagicMock()
        mock_query.filter_by.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.first.return_value = mock_alert
        mock_db.query.return_value = mock_query

        process_vitals_for_alerts("test-uuid", 150, 95, mock_db)

        assert mock_alert.last_bpm == 150
        assert mock_alert.consecutive_abnormal_count == 2
        mock_db.commit.assert_called_once()

    def test_normal_closes_alert_after_debounce(self):
        mock_db = MagicMock()
        mock_alert = MagicMock()
        mock_alert.status = "open"
        mock_alert.consecutive_normal_count = 1
        mock_alert.consecutive_abnormal_count = 0

        mock_query = MagicMock()
        mock_query.filter_by.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.first.return_value = mock_alert
        mock_db.query.return_value = mock_query

        process_vitals_for_alerts("test-uuid", 72, 98, mock_db)

        assert mock_alert.status == "closed"
        assert mock_alert.closed_at is not None
