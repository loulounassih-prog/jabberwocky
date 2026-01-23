from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Tuple, Optional


def load_bank_json(path: str | Path) -> Dict[Tuple[str, Optional[str], Optional[str]], List[str]]:
    """
    Load a Wuggy-generated bank from JSON and convert it to the sampler format.

    JSON format (from build_bank_fr.py):
      bank[pos][number][initial] = list[str]

    Sampler format:
      (pos, number, initial) -> list[str]
    """
    path = Path(path)
    raw = json.loads(path.read_text(encoding="utf-8"))

    bank: Dict[Tuple[str, Optional[str], Optional[str]], List[str]] = {}

    for pos, pos_block in raw.items():
        for number, number_block in pos_block.items():
            for initial, forms in number_block.items():
                key = (
                    pos,
                    None if number == "_" else number,
                    None if initial == "_" else initial,
                )
                bank[key] = list(forms)

    return bank
