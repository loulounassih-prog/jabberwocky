from __future__ import annotations

from dataclasses import dataclass, field
from typing import Set

from jw.nlp.spacy_fr import TokenInfo


# Function words we usually keep
DEFAULT_KEEP_POS: Set[str] = {
    "DET", "ADP", "PRON", "CCONJ", "SCONJ", "PART", "PUNCT", "SPACE",
    "SYM", "X"
}

# Content words we may replace
DEFAULT_REPLACE_POS: Set[str] = {
    "NOUN", "VERB", "ADJ", "ADV",
    # "PROPN",  # optional (names). kept by default in policy below.
}


@dataclass(frozen=True)
class ReplacementPolicy:
    """
    Minimal policy:
    - keep function words
    - keep auxiliaries (AUX)
    - replace content words with probability pct_replace
    """
    pct_replace: float = 0.6

    # IMPORTANT: use default_factory for mutable defaults (set)
    keep_pos: Set[str] = field(default_factory=lambda: set(DEFAULT_KEEP_POS))
    replace_pos: Set[str] = field(default_factory=lambda: set(DEFAULT_REPLACE_POS))

    keep_auxiliaries: bool = True
    keep_proper_nouns: bool = True

    def should_replace(self, tok: TokenInfo, rng) -> bool:
        
        # Keep function words and punctuation
        if tok.pos in self.keep_pos:
            return False

        # Keep auxiliaries to preserve grammatical scaffolding
        if self.keep_auxiliaries and tok.pos == "AUX":
            return False

        # Keep proper nouns (names) by default
        if self.keep_proper_nouns and tok.pos == "PROPN":
            return False

        # Only replace specific POS categories
        if tok.pos not in self.replace_pos:
            return False

        # Percentage gate
        if self.pct_replace <= 0.0:
            return False
        if self.pct_replace >= 1.0:
            return True

        return rng.random() < self.pct_replace
