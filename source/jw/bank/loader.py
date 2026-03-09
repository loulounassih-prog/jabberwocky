from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Tuple, Optional
BankDict = Dict[Tuple[str, Optional[str], Optional[str]], List[str]]


def load_bank_json(path: str | Path) -> BankDict
    """
    Load a Wuggy-generated bank from JSON and convert it to the sampler format.

    JSON format (from build_bank_fr.py):
      bank[pos][number][initial] = list[str]

    Sampler format:
      (pos, number, initial) -> list[str]
    """
    path = Path(path)

    if not path.exist() :
      raise FileNotFoundError(f"Bank file not found: {path}")
    
    if not path.is_file()
      raise FileNotFoundError(f"Bank file is not a file: {path}")
    
    try :
      raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc :
       raise ValueError(f"Invalid bank JSON file: {path}") from exc

    bank: BankDict = {}

    for pos, pos_block in raw.items():
        for number, number_block in pos_block.items():
            for initial, forms in number_block.items():
                key = (
                    pos,
                    None if number == "_" else number,
                    None if initial == "_" else initial,
                )
                bank[key] = [form for form in forms if form]

    return bank
