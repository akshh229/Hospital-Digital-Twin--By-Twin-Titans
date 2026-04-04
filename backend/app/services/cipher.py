"""
Age-Relative Cipher Service

Medication names are encrypted using patient age as the cipher key.
shift = age % 26
Each letter is shifted forward (encrypt) or backward (decrypt) in the alphabet.
"""


def decrypt_medication(cipher_text: str, age: int) -> str:
    """
    Decrypt medication name using age-relative shift cipher.

    Algorithm:
        shift = age % 26
        For each uppercase letter: shift backward in A-Z (with wraparound)

    Args:
        cipher_text: Encrypted medication name (uppercase alphabetic)
        age: Patient age (determines shift amount)

    Returns:
        Decrypted medication name

    Example:
        decrypt_medication("FWRKITPMR", 45) -> "ASPIRIN"
        (45 % 26 = 19, so each letter shifts back 19 positions)
    """
    shift = age % 26
    result = []

    for char in cipher_text.upper():
        if char.isalpha():
            pos = ord(char) - ord("A")
            new_pos = (pos - shift) % 26
            result.append(chr(ord("A") + new_pos))
        else:
            result.append(char)

    return "".join(result)


def encrypt_medication(plain_text: str, age: int) -> str:
    """
    Encrypt medication name using age-relative shift cipher.
    Inverse of decrypt_medication - used for testing and data generation.
    """
    shift = age % 26
    result = []

    for char in plain_text.upper():
        if char.isalpha():
            pos = ord(char) - ord("A")
            new_pos = (pos + shift) % 26
            result.append(chr(ord("A") + new_pos))
        else:
            result.append(char)

    return "".join(result)
