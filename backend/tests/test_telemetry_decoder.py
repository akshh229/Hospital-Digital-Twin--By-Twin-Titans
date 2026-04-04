"""Tests for telemetry hex decoder"""

import pytest
from app.services.telemetry_decoder import decode_telemetry, encode_telemetry


class TestDecodeTelemetry:
    def test_valid_payload(self):
        # BPM=72 (0x0048), SpO2=98 (0x0062)
        result = decode_telemetry("00480062")
        assert result["bpm"] == 72
        assert result["oxygen"] == 98
        assert result["quality_flag"] == "good"
        assert result["parity_flag"] == "even"

    def test_odd_bpm_parity(self):
        # BPM=75 (0x004B), SpO2=97 (0x0061)
        result = decode_telemetry("004b0061")
        assert result["bpm"] == 75
        assert result["oxygen"] == 97
        assert result["parity_flag"] == "odd"

    def test_bpm_out_of_range_low(self):
        # BPM=10 (too low)
        result = decode_telemetry("000a0062")
        assert result["quality_flag"] == "bad"

    def test_bpm_out_of_range_high(self):
        # BPM=300 (too high)
        result = decode_telemetry("012c0062")
        assert result["quality_flag"] == "bad"

    def test_spo2_out_of_range(self):
        # SpO2=30 (too low)
        result = decode_telemetry("0048001e")
        assert result["quality_flag"] == "bad"

    def test_missing_data(self):
        result = decode_telemetry("0048")
        assert result["quality_flag"] == "missing"
        assert result["bpm"] is None

    def test_invalid_hex(self):
        result = decode_telemetry("NOTHEX")
        assert result["quality_flag"] == "bad"

    def test_empty_string(self):
        result = decode_telemetry("")
        assert result["quality_flag"] == "bad"
        assert result["bpm"] is None


class TestEncodeTelemetry:
    def test_encode_decode_roundtrip(self):
        encoded = encode_telemetry(72, 98)
        decoded = decode_telemetry(encoded)
        assert decoded["bpm"] == 72
        assert decoded["oxygen"] == 98

    def test_encode_known_values(self):
        encoded = encode_telemetry(72, 98)
        assert encoded == "00480062"

    def test_encode_boundary_values(self):
        encoded = encode_telemetry(220, 100)
        decoded = decode_telemetry(encoded)
        assert decoded["bpm"] == 220
        assert decoded["oxygen"] == 100
        assert decoded["quality_flag"] == "good"
