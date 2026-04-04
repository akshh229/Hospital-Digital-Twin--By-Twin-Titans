"""Tests for oxygen interpolation used in patient vitals charts."""

from datetime import datetime, timedelta

from app.services.vitals_interpolator import interpolate_oxygen_series


class TestVitalsInterpolator:
    def test_interpolates_missing_oxygen_point_without_faking_bpm(self):
        start = datetime(2026, 1, 1, 12, 0, 0)
        data_points = [
            {"timestamp": start, "bpm": 70, "oxygen": 96, "quality_flag": "good"},
            {
                "timestamp": start + timedelta(minutes=1),
                "bpm": 72,
                "oxygen": 97,
                "quality_flag": "good",
            },
            {
                "timestamp": start + timedelta(minutes=2),
                "bpm": 74,
                "oxygen": 97,
                "quality_flag": "good",
            },
            {
                "timestamp": start + timedelta(minutes=4),
                "bpm": 76,
                "oxygen": 99,
                "quality_flag": "good",
            },
        ]

        rebuilt = interpolate_oxygen_series(data_points)

        assert len(rebuilt) == 5
        interpolated = rebuilt[3]
        assert interpolated["timestamp"] == start + timedelta(minutes=3)
        assert interpolated["bpm"] is None
        assert interpolated["oxygen"] == 98
        assert interpolated["quality_flag"] == "interpolated"

    def test_leaves_short_series_unchanged(self):
        start = datetime(2026, 1, 1, 12, 0, 0)
        data_points = [
            {"timestamp": start, "bpm": 70, "oxygen": 96, "quality_flag": "good"}
        ]

        assert interpolate_oxygen_series(data_points) == data_points
