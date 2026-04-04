"""Helpers for reconstructing missing oxygen samples in chart timelines."""

from datetime import timedelta
from statistics import median
from typing import Any


def interpolate_oxygen_series(data_points: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Fill oxygen gaps with interpolated points while keeping BPM real-only.

    The dashboard charts BPM from decoded telemetry values and overlays a
    reconstructed oxygen trace so long gaps from dropped/corrupted frames do not
    create misleading empty stretches.
    """

    if len(data_points) < 2:
        return data_points

    intervals = []
    for left, right in zip(data_points, data_points[1:]):
        delta_seconds = (right["timestamp"] - left["timestamp"]).total_seconds()
        if delta_seconds > 0:
            intervals.append(delta_seconds)

    if not intervals:
        return data_points

    expected_step = median(intervals)
    if expected_step <= 0:
        return data_points

    rebuilt: list[dict[str, Any]] = []

    for current, following in zip(data_points, data_points[1:]):
        rebuilt.append(current)

        gap_seconds = (following["timestamp"] - current["timestamp"]).total_seconds()
        missing_slots = max(0, round(gap_seconds / expected_step) - 1)

        if missing_slots == 0:
            continue

        for index in range(1, missing_slots + 1):
            fraction = index / (missing_slots + 1)
            interpolated_oxygen = round(
                current["oxygen"] + (following["oxygen"] - current["oxygen"]) * fraction
            )
            rebuilt.append(
                {
                    "timestamp": current["timestamp"]
                    + timedelta(seconds=gap_seconds * fraction),
                    "bpm": None,
                    "oxygen": interpolated_oxygen,
                    "quality_flag": "interpolated",
                }
            )

    rebuilt.append(data_points[-1])
    rebuilt.sort(key=lambda point: point["timestamp"])
    return rebuilt
