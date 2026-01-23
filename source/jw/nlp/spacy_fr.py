from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import spacy


@dataclass(frozen=True)
class TokenInfo:
    """
    Minimal token representation for our pipeline.
    We keep whitespace to reconstruct the original formatting.
    """
    text: str
    lemma: str
    pos: str                # spaCy coarse POS, e.g. "NOUN", "VERB", "ADJ", "AUX", ...
    morph: Dict[str, str]   # simplified morph features, e.g. {"Gender": "Masc", "Number": "Sing"}
    whitespace: str         # token.whitespace_


class SpacyFrenchNLP:
    """
    Thin wrapper around spaCy French model.
    Keeps the rest of the code independent from spaCy specifics.
    """

    def __init__(self, model: str = "fr_core_news_sm") -> None:
        self.model_name = model
        self.nlp = spacy.load(model)

    def parse(self, text: str) -> List[TokenInfo]:
        doc = self.nlp(text)
        out: List[TokenInfo] = []

        for t in doc:
            # Convert spaCy MorphAnalysis -> simple dict (take first value if multiple)
            morph_dict: Dict[str, str] = {}
            for k, vals in t.morph.to_dict().items():
                if not vals:
                    continue
                # spaCy sometimes provides list-like strings; keep first if multiple
                if isinstance(vals, list):
                    morph_dict[k] = vals[0]
                else:
                    morph_dict[k] = str(vals)

            out.append(
                TokenInfo(
                    text=t.text,
                    lemma=t.lemma_,
                    pos=t.pos_,
                    morph=morph_dict,
                    whitespace=t.whitespace_,
                )
            )

        return out
