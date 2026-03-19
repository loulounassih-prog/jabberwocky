from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional
import os

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

    def __init__(self, model: str = "fr_core_news_md") -> None:
        self.model_name = model
        self.nlp = spacy.load(model)

    def parse(self, text: str) -> List[TokenInfo]:
        # Normalize typographic dashes to ASCII hyphens to stabilise tokenisation of French dialogue
        text = text.translate(
            {
                0x2010: 0x2D,  # hyphen
                0x2011: 0x2D,  # non-breaking hyphen
                0x2012: 0x2D,  # figure dash
                0x2013: 0x2D,  # en dash
                0x2014: 0x2D,  # em dash
                0x2212: 0x2D,  # minus sign
                0x00AD: 0x2D,  # soft hyphen
                0xFE63: 0x2D,  # small hyphen-minus
                0xFF0D: 0x2D,  # fullwidth hyphen-minus
                0x2043: 0x2D,  # hyphen bullet
            }
        )
        doc = self.nlp(text)
        debug = os.getenv("JW_DEBUG") == "1"
        if debug:
            for i, t in enumerate(doc):
                if any(ord(ch) > 127 for ch in t.text):
                    start = max(0, i - 2)
                    end = min(len(doc), i + 3)
                    ctx = [tok.text for tok in doc[start:end]]
                    print(f"JW_DEBUG non-ascii context: {ctx}")
                    print(f"JW_DEBUG non-ascii ords: {[ord(ch) for ch in t.text]}")
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
