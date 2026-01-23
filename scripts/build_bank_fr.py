from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List

from wuggy import WuggyGenerator

PLUGIN = "orthographic_french"

# Seeds simples, fiables (pas d'accents) pour démarrer.
# Plus tard, on remplacera par des seeds extraites de Lexique382.
SEEDS = {
    "NOUN": ["table", "maison", "camion", "chanson", "pierre", "jardin",
         "arbre", "école", "orage"],
    "ADJ":  ["rapide", "petit", "grand", "calme", "triste", "joli",
         "étrange", "ancien", "utile"],
    "VERB": ["mange", "avance", "prend", "regarde", "tombe", "cherche",
         "arrive", "écoute", "oublie"],
    "ADV":  ["vite", "hier", "souvent", "bien", "encore", "toujours",
         "ailleurs", "ensemble", "ici"],

}

N_PER_SEED = 50

OUT_PATH = Path("data") / "bank_fr.json"


VOWELS = set("aeiouyàâäéèêëîïôöùûüÿœ")


def starts_with_vowel_letter(w: str) -> bool:
    return bool(w) and (w[0].lower() in VOWELS)


def naive_plural(w: str) -> str:
    # v1: plural "s" unless already ends with s/x/z
    if not w:
        return w
    if w.endswith(("s", "x", "z")):
        return w
    return w + "s"


def main() -> None:
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    wg = WuggyGenerator()
    wg.download_language_plugin(PLUGIN, auto_download=True)
    wg.load(PLUGIN)

    # JSON-friendly structure:
    # bank[pos][number][initial] = list[str]
    bank: Dict[str, Dict[str, Dict[str, List[str]]]] = {
        "NOUN": {"Sing": {"vowel": [], "cons": []}, "Plur": {"vowel": [], "cons": []}},
        "ADJ":  {"Sing": {"vowel": [], "cons": []}, "Plur": {"vowel": [], "cons": []}},
        "VERB": {"_": {"_": []}},  # flat
        "ADV":  {"_": {"_": []}},  # flat
    }

    def add_bucket(pos: str, form: str) -> None:
        form = form.strip()
        if not form:
            return
        if pos in ("VERB", "ADV"):
            bank[pos]["_"]["_"].append(form)
            return

        initial = "vowel" if starts_with_vowel_letter(form) else "cons"
        bank[pos]["Sing"][initial].append(form)
        bank[pos]["Plur"][initial].append(naive_plural(form))

    for pos, seeds in SEEDS.items():
        print(f"\n=== {pos} ===")
        for seed in seeds:
            print(f"seed={seed}")
            try:
                results = wg.generate_classic([seed], ncandidates_per_sequence=N_PER_SEED)
            except Exception as e:
                print(f"  (!) seed failed: {seed} -> {type(e).__name__}: {e}")
                continue

            count = 0
            for r in results:
                if isinstance(r, dict) and "pseudoword" in r:
                    pw = r["pseudoword"]
                else:
                    pw = str(r)

                add_bucket(pos, pw)
                count += 1

            print(f"  generated={count}")

    # Deduplicate while preserving order
    def dedup(lst: List[str]) -> List[str]:
        seen = set()
        out = []
        for x in lst:
            x_norm = x.lower()
            if x_norm in seen:
                continue
            seen.add(x_norm)
            out.append(x)
        return out

    for pos in bank:
        for number in bank[pos]:
            for initial in bank[pos][number]:
                bank[pos][number][initial] = dedup(bank[pos][number][initial])

    OUT_PATH.write_text(json.dumps(bank, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nSaved -> {OUT_PATH.resolve()}")
    print("Counts:")
    print("  NOUN sing vowel:", len(bank["NOUN"]["Sing"]["vowel"]), "cons:", len(bank["NOUN"]["Sing"]["cons"]))
    print("  ADJ  sing vowel:", len(bank["ADJ"]["Sing"]["vowel"]), "cons:", len(bank["ADJ"]["Sing"]["cons"]))
    print("  VERB:", len(bank["VERB"]["_"]["_"]))
    print("  ADV :", len(bank["ADV"]["_"]["_"]))


if __name__ == "__main__":
    main()
