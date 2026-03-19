from __future__ import annotations

from dataclasses import dataclass, field
from typing import Set
from random import Random

from jw.nlp.spacy_fr import TokenInfo


# Words we keep
DEFAULT_KEEP_POS: Set[str] = {
    "DET", "ADP", "PRON", "CCONJ", "SCONJ", "PART", "PUNCT", "SPACE",
    "SYM", "X", "NUM"
}

# Specific tokens we always keep (normalized lowercase)
DEFAULT_KEEP_TEXT: Set[str] = {"ne", "n'", "pas"}

# Content words we replace
DEFAULT_REPLACE_POS: Set[str] = {
    "NOUN", "VERB", "ADJ", "ADV",
}


@dataclass(frozen=False)
class ReplacementPolicy:
    """
    Simple policy:
    - keep function words and auxiliaries
    - a replacement probability
    """

    pct_replace: float = 0.6
    # Per-POS override rates. Keys are spaCy POS tags (e.g. "NOUN", "VERB").
    # If a POS is not in this dict, pct_replace is used as fallback.
    pct_by_pos: dict = field(default_factory=dict)

    # Create per-instance copies of mutable default sets.
    keep_pos: Set[str] = field(default_factory=lambda : set(DEFAULT_KEEP_POS))
    replace_pos: Set[str] = field(default_factory=lambda : set(DEFAULT_REPLACE_POS))
    keep_text: Set[str] = field(default_factory=lambda : set(DEFAULT_KEEP_TEXT))

    keep_auxiliaries: bool = True
    keep_proper_nouns: bool = True

    def should_replace(self, tok: TokenInfo, rng: Random) -> bool:
        text_norm = tok.text.lower().replace("\u2019", "'")         # Normalize apostrophes
        lemma_norm = tok.lemma.lower().replace("\u2019", "'")

        if text_norm in self.keep_text or lemma_norm in self.keep_text:
            return False

        if tok.pos in self.keep_pos:
            return False

        if self.keep_auxiliaries and tok.pos == "AUX":
            return False

        if self.keep_proper_nouns and tok.pos == "PROPN":
            return False

        if tok.pos not in self.replace_pos:
            return False

        pct = self.pct_by_pos.get(tok.pos, self.pct_replace)

        if pct <= 0.0:
            return False
        if pct >= 1.0:
            return True

        return rng.random() < pct
    