from __future__ import annotations

from dataclasses import dataclass
from random import Random
from typing import Dict, List, Optional, Tuple


@dataclass
class BankSampler:

    bank: Dict[Tuple[str, Optional[str], Optional[str]], List[Tuple[str, str]]]
    """Sample pseudowords from the bank based on POS, number, and onset constraints."""

    def sample(
        self,
        pos: str,
        number: Optional[str],
        needs_vowel_start: Optional[bool],
        rng: Random,
        avoid: Optional[set[str]] = None,
    ) -> Tuple[str, str]:
        """
        Return (form, gender) matching the requested grammatical constraints.
        Gender is '_' for VERB and ADV.
        """
        if avoid is None:
            avoid = set()

        # Select the most specific bucket
        if pos in ("NOUN", "ADJ"):
            if number not in ("Sing", "Plur"):
                number = "Sing"

            if needs_vowel_start is None:
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

        # Fallback: relax number constraint but keep onset
        if not candidates and pos in ("NOUN", "ADJ") and needs_vowel_start is not None:
            key3 = "vowel" if needs_vowel_start else "cons"
            candidates = (
                self.bank.get((pos, "Sing", key3), [])
                + self.bank.get((pos, "Plur", key3), [])
            )

        # Fallback: ignore all constraints
        if not candidates and pos in ("NOUN", "ADJ"):
            candidates = (
                self.bank.get((pos, "Sing", "vowel"), [])
                + self.bank.get((pos, "Sing", "cons"), [])
                + self.bank.get((pos, "Plur", "vowel"), [])
                + self.bank.get((pos, "Plur", "cons"), [])
            )

        if not candidates:
            fallback_gender = "_" if pos in ("VERB", "ADV") else "Masc"
            return (f"<{pos}>", fallback_gender)

        # Prefer unused candidates
        filtered = [e for e in candidates if e[0].lower() not in avoid]
        if not filtered:
            filtered = candidates

        return rng.choice(filtered)