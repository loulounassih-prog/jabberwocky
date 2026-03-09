from __future__ import annotations


VOWEL_CHARS = set("aeiouyàâäéèêëîïôöùûüÿœ")


def starts_with_vowel_letter(s: str) -> bool:
    """
    v1 heuristic: vowel by first letter only (not vowel sound).
    We'll improve later (h aspiré, etc.).
    """
    if not s:
        return False
    return s[0].lower() in VOWEL_CHARS


def preserve_case(src: str, repl: str) -> str:
    """
    Preserve basic casing:
    - "Chat" -> "Flane"
    - "CHAT" -> "FLANE"
    - "chat" -> "flane"
    """
    if not src:
        return repl

    if src.isupper():
        return repl.upper()
    if src[0].isupper() and src[1:].islower():
        if repl:
            return repl[0].upper() + repl[1:]
        return repl
    return repl.lower()


def next_token_vowel_constraint(prev_token_text: str) -> bool | None:
    """
    Decide constraint for the NEXT token (heuristic):

    Returns:
      - True  => next token should start with a vowel letter
      - False => next token should start with a consonant letter
      - None  => no constraint
    """
    if not prev_token_text:
        return None

    # Normalize minimal (lowercase + straight apostrophe)
    p = prev_token_text.lower().replace("\u2019", "'")

    # Elision: any token ending with apostrophe forces vowel start
    if len(p) > 1 and p.endswith("'"):
        return True

    # Elidable full forms that should NOT be followed by a vowel-start word,
    # because normally we would elide ("le ami" -> "l'ami", "je aime" -> "j'aime").
    # v1 heuristic: enforce consonant after these.
    if p in (
        "le", "la", "de", "je", "me", "te", "se", "que", "si", "ne",
        "un", "une",
        "lorsque", "puisque", "jusque", "quelque",
    ):
        return False

    return None
