"""Tests for age-relative cipher"""

import pytest
from app.services.cipher import decrypt_medication, encrypt_medication


class TestCipher:
    def test_encrypt_decrypt_roundtrip(self):
        original = "ASPIRIN"
        encrypted = encrypt_medication(original, 45)
        decrypted = decrypt_medication(encrypted, 45)
        assert decrypted == original

    def test_known_encryption(self):
        # age=45, shift=45%26=19
        encrypted = encrypt_medication("ASPIRIN", 45)
        assert decrypt_medication(encrypted, 45) == "ASPIRIN"

    def test_zero_age(self):
        # shift=0, no change
        assert encrypt_medication("ASPIRIN", 0) == "ASPIRIN"
        assert decrypt_medication("ASPIRIN", 0) == "ASPIRIN"

    def test_age_26(self):
        # shift=26%26=0, no change
        assert encrypt_medication("ASPIRIN", 26) == "ASPIRIN"

    def test_multiple_medications(self):
        meds = ["ASPIRIN", "INSULIN", "MORPHINE", "WARFARIN", "METFORMIN"]
        for med in meds:
            for age in [18, 45, 65, 85]:
                encrypted = encrypt_medication(med, age)
                decrypted = decrypt_medication(encrypted, age)
                assert decrypted == med, f"Failed for {med} with age {age}"

    def test_non_alpha_preserved(self):
        result = encrypt_medication("A-B", 5)
        assert "-" in result

    def test_lowercase_input(self):
        result = decrypt_medication("fwrkitpmr", 45)
        assert result == decrypt_medication("FWRKITPMR", 45)
