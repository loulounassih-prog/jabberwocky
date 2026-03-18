from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Tuple, Optional


def load_bank_json(path: str | Path) -> Dict[Tuple[str, Optional[str], Optional[str]], List[Tuple[str, str]]]:
    """
    Load a Wuggy-generated bank from JSON.

    Each entry is a (form, gender) tuple.
    For VERB and ADV the gender is always "_".

    JSON format:
      bank[pos][number][initial] = list of [form, gender] or list of str (legacy)
    """
    path = Path(path)
    raw = json.loads(path.read_text(encoding="utf-8"))

    bank: Dict[Tuple[str, Optional[str], Optional[str]], List[Tuple[str, str]]] = {}

    for pos, pos_block in raw.items():
        for number, number_block in pos_block.items():
            for initial, forms in number_block.items():
                key = (
                    pos,
                    None if number == "_" else number,
                    None if initial == "_" else initial,
                )
                # Support both legacy str entries and new [form, gender] entries
                entries: List[Tuple[str, str]] = []
                for item in forms:
                    if isinstance(item, list):
                        entries.append((item[0], item[1]))
                    else:
                        legacy_gender = "_" if pos in ("VERB", "ADV") else "Masc"
                        entries.append((str(item), legacy_gender))
                bank[key] = entries

    return bank