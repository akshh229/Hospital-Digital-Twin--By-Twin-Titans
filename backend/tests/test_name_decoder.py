"""Tests for seeded patient name decoding."""

from app.services.name_decoder import decode_patient_name


def test_decodes_seeded_name_using_known_name_lists():
    assert decode_patient_name("RICHARDJOHNSON") == "Richard Johnson"


def test_returns_unknown_for_missing_name():
    assert decode_patient_name("") == "Unknown"


def test_falls_back_to_reasonable_split_for_unknown_name():
    assert decode_patient_name("ANNLEE") == "Ann Lee"
