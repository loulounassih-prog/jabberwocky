from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple


def _starts_with_vowel_letter(word: str) -> bool:
    # v1 heuristic (letters only). We'll improve later (h aspiré, etc.)
    if not word:
        return False
    return word[0].lower() in "aeiouyàâäéèêëîïôöùûüÿœ"


@dataclass
class BankSampler:
    """
    Minimal sampler on top of a dict bank.
    Later, this will sit on top of a real JSONL bank + index.
    """
    bank: Dict[Tuple[str, Optional[str], Optional[str]], List[str]]

    def sample(
        self,
        pos: str,
        number: Optional[str],
        needs_vowel_start: Optional[bool],
        rng,
        avoid: Optional[set[str]] = None,
    ) -> str:
        avoid = avoid or set()

        # Choose bucket key
        if pos in ("NOUN", "ADJ"):
            if number not in ("Sing", "Plur"):
                number = "Sing"

            if needs_vowel_start is None:
                # Try both buckets
                candidates = (
                    self.bank.get((pos, number, "vowel"), [])
                    + self.bank.get((pos, number, "cons"), [])
                )
            else:
                key3 = "vowel" if needs_vowel_start else "cons"
                candidates = self.bank.get((pos, number, key3), [])

        elif pos in ("VERB", "ADV"):
            candidates = self.bank.get((pos, None, None), [])
        else:
            candidates = []

        # Fallback: if bucket empty, try any bucket for this POS
        if not candidates and pos in ("NOUN", "ADJ"):
            candidates = (
                self.bank.get((pos, "Sing", "vowel"), [])
                + self.bank.get((pos, "Sing", "cons"), [])
                + self.bank.get((pos, "Plur", "vowel"), [])
                + self.bank.get((pos, "Plur", "cons"), [])
            )

        if not candidates:
            # Last resort: return original POS placeholder
            return f"<{pos}>"

        # Filter avoid set (anti-repetition per document)
        filtered = [w for w in candidates if w not in avoid]
        if not filtered:
            filtered = candidates

        return rng.choice(filtered)
