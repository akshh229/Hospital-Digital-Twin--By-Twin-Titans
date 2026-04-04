"""
Telemetry Hex Decoder Service

Decodes hexadecimal payloads from corrupted sensor logs into:
- BPM (heart rate) - bytes 0-1
- SpO2 (oxygen saturation) - bytes 2-3

Validates ranges and assigns quality flags.
"""

from typing import Dict, Optional, Union
from app.config import settings


def decode_telemetry(hex_payload: str) -> Dict[str, Optional[Union[int, str]]]:
    """
    Decode hex string to BPM and SpO2 with quality validation.

    Frame layout (configurable via settings):
      Bytes 0-1: BPM (uint16, big-endian by default)
      Bytes 2-3: SpO2 (uint16, big-endian by default)

    Args:
        hex_payload: Hexadecimal string from sensor

    Returns:
        dict: {
            'bpm': int or None,
            'oxygen': int or None,
            'quality_flag': 'good' | 'bad' | 'missing',
            'parity_flag': 'even' | 'odd' | None
        }
    """
    try:
        if not hex_payload:
            return {
                "bpm": None,
                "oxygen": None,
                "quality_flag": "bad",
                "parity_flag": None,
            }

        payload_bytes = bytes.fromhex(hex_payload.strip())

        if len(payload_bytes) < settings.SPO2_OFFSET + settings.SPO2_LENGTH:
            return {
                "bpm": None,
                "oxygen": None,
                "quality_flag": "missing",
                "parity_flag": None,
            }

        bpm_bytes = payload_bytes[
            settings.BPM_OFFSET : settings.BPM_OFFSET + settings.BPM_LENGTH
        ]
        bpm = int.from_bytes(bpm_bytes, byteorder=settings.TELEMETRY_BYTE_ORDER)

        spo2_bytes = payload_bytes[
            settings.SPO2_OFFSET : settings.SPO2_OFFSET + settings.SPO2_LENGTH
        ]
        spo2 = int.from_bytes(spo2_bytes, byteorder=settings.TELEMETRY_BYTE_ORDER)

        bpm_valid = settings.BPM_MIN <= bpm <= settings.BPM_MAX
        spo2_valid = settings.SPO2_MIN <= spo2 <= settings.SPO2_MAX

        if not (bpm_valid and spo2_valid):
            return {
                "bpm": bpm,
                "oxygen": spo2,
                "quality_flag": "bad",
                "parity_flag": None,
            }

        parity = "even" if bpm % 2 == 0 else "odd"

        return {
            "bpm": bpm,
            "oxygen": spo2,
            "quality_flag": "good",
            "parity_flag": parity,
        }

    except (ValueError, IndexError, TypeError):
        return {"bpm": None, "oxygen": None, "quality_flag": "bad", "parity_flag": None}


def encode_telemetry(bpm: int, spo2: int) -> str:
    """
    Inverse operation - encode BPM and SpO2 to hex string.
    Useful for testing and data generation.
    """
    bpm_bytes = bpm.to_bytes(
        settings.BPM_LENGTH, byteorder=settings.TELEMETRY_BYTE_ORDER
    )
    spo2_bytes = spo2.to_bytes(
        settings.SPO2_LENGTH, byteorder=settings.TELEMETRY_BYTE_ORDER
    )
    return (bpm_bytes + spo2_bytes).hex()
