"""Tests for safe seed bootstrap helpers."""

from seed_data.load_seeds import seed_dataset_ready


def test_seed_dataset_ready_requires_all_core_tables():
    counts = {
        "staging_demographics": 20,
        "staging_telemetry": 100,
        "staging_prescriptions": 50,
        "clean_telemetry": 100,
        "clean_prescriptions": 50,
        "clean_demographics": 20,
        "patient_alias": 20,
    }

    assert seed_dataset_ready(counts) is True


def test_seed_dataset_ready_detects_missing_bootstrap_tables():
    counts = {
        "staging_demographics": 20,
        "staging_telemetry": 100,
        "staging_prescriptions": 50,
        "clean_telemetry": 100,
        "clean_prescriptions": 50,
        "clean_demographics": 0,
        "patient_alias": 20,
    }

    assert seed_dataset_ready(counts) is False
