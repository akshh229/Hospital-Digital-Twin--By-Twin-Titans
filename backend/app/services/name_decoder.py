"""Helpers for decoding seeded patient name ciphers into readable names."""

FIRST_NAMES = {
    "JOHN",
    "JANE",
    "ROBERT",
    "MARIA",
    "DAVID",
    "SARAH",
    "MICHAEL",
    "EMILY",
    "JAMES",
    "LINDA",
    "WILLIAM",
    "PATRICIA",
    "RICHARD",
    "BARBARA",
    "JOSEPH",
    "ELIZABETH",
    "THOMAS",
    "SUSAN",
    "CHARLES",
    "JESSICA",
}

LAST_NAMES = {
    "SMITH",
    "JOHNSON",
    "WILLIAMS",
    "BROWN",
    "JONES",
    "GARCIA",
    "MILLER",
    "DAVIS",
    "RODRIGUEZ",
    "MARTINEZ",
    "HERNANDEZ",
    "LOPEZ",
    "GONZALEZ",
    "WILSON",
    "ANDERSON",
    "THOMAS",
    "TAYLOR",
    "MOORE",
    "JACKSON",
    "MARTIN",
}


def _titlecase_name(value: str) -> str:
    return " ".join(part.title() for part in value.split())


def decode_patient_name(name_cipher: str | None) -> str:
    """Decode an uppercase spaceless name cipher into `First Last`.

    Seed data is generated from curated first/last name lists, so we first try an
    exact list-based split before falling back to a generic heuristic.
    """

    if not name_cipher:
        return "Unknown"

    name = "".join(character for character in name_cipher.upper() if character.isalpha())
    if not name:
        return "Unknown"

    for first_name in sorted(FIRST_NAMES, key=len, reverse=True):
        if not name.startswith(first_name):
            continue

        last_name = name[len(first_name) :]
        if last_name in LAST_NAMES:
            return f"{first_name.title()} {last_name.title()}"

    best_split: tuple[str, str] | None = None
    best_score: tuple[int, int] | None = None

    for split_index in range(2, len(name) - 1):
        first_name = name[:split_index]
        last_name = name[split_index:]
        if not (first_name.isalpha() and last_name.isalpha()):
            continue
        if len(first_name) < 2 or len(last_name) < 2:
            continue

        score = (abs(len(first_name) - len(last_name)), -min(len(first_name), len(last_name)))
        if best_score is None or score < best_score:
            best_split = (first_name, last_name)
            best_score = score

    if best_split is not None:
        return f"{best_split[0].title()} {best_split[1].title()}"

    return _titlecase_name(name_cipher)
