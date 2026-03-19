from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Dict, List, Tuple

from wuggy import WuggyGenerator

PLUGIN = "orthographic_english"

# Reliable English seeds (common, unambiguous words) as fallback when no
# corpus TSV is provided.  Verbs are given in their base / infinitive form.
SEEDS = {
    "NOUN": [
        "table", "house", "truck", "garden", "stone", "tree",
        "school", "storm", "bridge", "river", "window", "market",
    ],
    "ADJ": [
        "fast", "small", "tall", "calm", "sad", "pretty",
        "strange", "old", "useful", "bright", "dark", "bold",
    ],
    "VERB": [
        "eat", "move", "take", "watch", "fall", "search",
        "arrive", "listen", "forget", "build", "carry", "speak",
    ],
    "ADV": [
        "fast", "often", "well", "still", "always",
        "away", "together", "here", "soon", "never",
    ],
}

N_PER_SEED = 50
DEFAULT_MAX_FINAL_PER_POS = 0

OUT_PATH = Path("data") / "bank_en.json"

VOWELS = set("aeiouy")


# ---------------------------------------------------------------------------
# Phonology / morphology helpers
# ---------------------------------------------------------------------------

def starts_with_vowel_letter(w: str) -> bool:
    return bool(w) and (w[0].lower() in VOWELS)


def naive_plural(w: str) -> str:
    """Very naive English pluralisation used for pseudowords.

    Rules applied in order:
    - already ends with s / x / z  → unchanged
    - ends with ch / sh             → + es
    - ends with consonant + y       → strip y, + ies
    - otherwise                     → + s
    """
    if not w:
        return w
    if w.endswith(("s", "x", "z")):
        return w
    if w.endswith(("ch", "sh")):
        return w + "es"
    if w.endswith("y") and len(w) >= 2 and w[-2].lower() not in VOWELS:
        return w[:-1] + "ies"
    return w + "s"


def naive_past(w: str) -> str:
    """Naive English simple-past formation for pseudowords.

    - ends with e         → + d
    - ends with consonant + y → strip y, + ied
    - ends with consonant (CVC short)  → double + ed  (heuristic)
    - otherwise           → + ed
    """
    if not w:
        return w
    if w.endswith("e"):
        return w + "d"
    if w.endswith("y") and len(w) >= 2 and w[-2].lower() not in VOWELS:
        return w[:-1] + "ied"
    # Rough CVC doubling: short word (≤4 chars) ending in single consonant
    if len(w) >= 2 and w[-1].lower() not in VOWELS and w[-2].lower() in VOWELS and len(w) <= 4:
        return w + w[-1] + "ed"
    return w + "ed"


# ---------------------------------------------------------------------------
# Float / field helpers (identical logic to the French script)
# ---------------------------------------------------------------------------

def _parse_float(val: str) -> float:
    if not val:
        return 0.0
    try:
        return float(val.replace(",", "."))
    except ValueError:
        return 0.0


def _pick(row: Dict[str, str], *names: str) -> str:
    for name in names:
        v = row.get(name)
        if v:
            return v
    return ""


def _normalize_row(row: Dict[str, str]) -> Dict[str, str]:
    return {(k or "").strip().lower(): (v or "").strip() for k, v in row.items()}


# ---------------------------------------------------------------------------
# POS detection for English corpora
# English corpora (e.g. SUBTLEX-US, CELEX) use different tag conventions.
# We try several common column names / values.
# ---------------------------------------------------------------------------

def _pos_from_row(row: Dict[str, str]) -> str:
    """Return a normalised POS tag (NOUN | ADJ | ADV | VERB | '') from a row."""
    cgram = _pick(row, "dom_pos", "pos", "cgram", "partofspeech", "wclass", "class")
    if not cgram:
        return ""
    tag = cgram.split(":")[0].strip().upper()

    # SUBTLEX-US tags
    mapping = {
        "NOUN": "NOUN",
        "NN": "NOUN", "NNS": "NOUN", "NNP": "NOUN", "NNPS": "NOUN",
        "VB": "VERB", "VBD": "VERB", "VBG": "VERB", "VBN": "VERB",
        "VBP": "VERB", "VBZ": "VERB", "VERB": "VERB", "VER": "VERB",
        "ADJ": "ADJ", "JJ": "ADJ", "JJR": "ADJ", "JJS": "ADJ",
        "ADV": "ADV", "RB": "ADV", "RBR": "ADV", "RBS": "ADV",
        # CELEX / BNC
        "N": "NOUN", "V": "VERB", "A": "ADJ",
    }
    return mapping.get(tag, "")


def _is_singular(row: Dict[str, str]) -> bool | None:
    number = _pick(row, "number", "nombre", "morph")
    if not number:
        return None
    n = number.strip().lower()
    if n in ("s", "sing", "singular", "sg"):
        return True
    if n in ("p", "plur", "plural", "pl"):
        return False
    return None


# ---------------------------------------------------------------------------
# Load seeds from an English corpus TSV
# Supported corpora (tab-separated, UTF-8):
#   • SUBTLEX-US  (columns: Word, Dom_PoS_SUBTLEX, SUBTLWF, …)
#   • CELEX-style (columns: Ortho / Phono / Word, PoS, Freq, …)
#   • Any TSV with columns that match the _pick() fallback chain below.
# ---------------------------------------------------------------------------

def _load_corpus_seeds(path: Path, limits: Dict[str, int]) -> Dict[str, List[str]]:
    candidates: Dict[str, List[Tuple[str, float]]] = {
        "NOUN": [],
        "ADJ": [],
        "ADV": [],
        "VERB": [],
    }

    with path.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f, delimiter="\t")
        if not reader.fieldnames:
            raise ValueError("Corpus TSV: missing header")

        fieldnames = [(n or "").strip().lower() for n in reader.fieldnames]
        has_islem = "islem" in fieldnames  # CELEX lemma flag

        for row in reader:
            row_norm = _normalize_row(row)
            pos = _pos_from_row(row_norm)
            if pos not in candidates:
                continue

            # For nouns and adjectives, keep only singular / base forms.
            if pos in ("NOUN", "ADJ"):
                sing = _is_singular(row_norm)
                if sing is False:
                    continue

            # For verbs, prefer lemma / base form.
            if pos == "VERB":
                lemma = _pick(row_norm, "lemma", "lemme", "baseform", "base")
                if not lemma:
                    continue
                if has_islem:
                    if row_norm.get("islem") != "1":
                        continue
                else:
                    ortho = _pick(row_norm, "word", "ortho", "orth", "forme", "form")
                    if ortho and ortho.lower() != lemma.lower():
                        continue
                form = lemma
                freq = _parse_float(
                    _pick(
                        row_norm,
                        "subtlwf",        # SUBTLEX per-million word frequency
                        "freqcount",
                        "freq",
                        "zipf",
                        "freqlemfilms2",
                        "freqlem",
                    )
                )
            else:
                form = _pick(row_norm, "word", "ortho", "orth", "forme", "form")
                if not form:
                    form = _pick(row_norm, "lemma", "lemme", "baseform")
                if not form:
                    continue
                freq = _parse_float(
                    _pick(row_norm, "subtlwf", "freqcount", "freq", "zipf", "freqfilms2")
                )

            form = form.strip()
            if not form:
                continue
            candidates[pos].append((form, freq))

    seeds: Dict[str, List[str]] = {}
    for pos, items in candidates.items():
        items.sort(key=lambda x: (-x[1], x[0]))
        seen: set[str] = set()
        out: List[str] = []
        limit = limits.get(pos, 0)
        for form, _ in items:
            norm = form.casefold()
            if norm in seen:
                continue
            seen.add(norm)
            out.append(form)
            if limit and len(out) >= limit:
                break
        seeds[pos] = out
    return seeds


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    p = argparse.ArgumentParser(
        description="Build a Jabberwocky pseudoword bank for English using Wuggy."
    )
    p.add_argument(
        "--corpus-tsv",
        type=str,
        default="",
        help=(
            "Path to a tab-separated word corpus (e.g. SUBTLEX-US or CELEX). "
            "If omitted, the built-in seed lists are used."
        ),
    )
    p.add_argument("--n-noun", type=int, default=20, help="Max noun seeds from corpus")
    p.add_argument("--n-adj",  type=int, default=20, help="Max adjective seeds from corpus")
    p.add_argument("--n-adv",  type=int, default=20, help="Max adverb seeds from corpus")
    p.add_argument("--n-verb", type=int, default=20, help="Max verb seeds from corpus")
    args = p.parse_args()

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    if args.corpus_tsv:
        limits = {
            "NOUN": args.n_noun,
            "ADJ":  args.n_adj,
            "ADV":  args.n_adv,
            "VERB": args.n_verb,
        }
        seeds_by_pos = _load_corpus_seeds(Path(args.corpus_tsv), limits)
    else:
        seeds_by_pos = SEEDS

    # ------------------------------------------------------------------
    # Wuggy setup
    # ------------------------------------------------------------------
    wg = WuggyGenerator()
    wg.download_language_plugin(PLUGIN, auto_download=True)
    wg.load(PLUGIN)

    # ------------------------------------------------------------------
    # Bank structure
    #
    # English nouns: singular / plural  ×  vowel-initial / cons-initial
    # English adjectives: flat (no grammatical gender, no inflection needed)
    # English verbs: base form + past form stored side by side
    # English adverbs: flat
    #
    # bank[pos][slot][initial] = [[form, extra_info], …]
    # ------------------------------------------------------------------
    bank: Dict[str, Dict[str, Dict[str, List[List[str]]]]] = {
        "NOUN": {
            "Sing": {"vowel": [], "cons": []},
            "Plur": {"vowel": [], "cons": []},
        },
        "ADJ":  {"_": {"vowel": [], "cons": []}},
        "VERB": {"_": {"_": []}},   # [base_form, past_form]
        "ADV":  {"_": {"_": []}},   # [adverb, "_"]
    }

    avoid = {seed.casefold() for seeds in seeds_by_pos.values() for seed in seeds}

    def add_bucket(pos: str, form: str) -> None:
        form = form.strip()
        if not form:
            return

        if pos == "ADV":
            bank["ADV"]["_"]["_"].append([form, "_"])
            return

        if pos == "VERB":
            past = naive_past(form)
            bank["VERB"]["_"]["_"].append([form, past])
            return

        if pos == "ADJ":
            initial = "vowel" if starts_with_vowel_letter(form) else "cons"
            bank["ADJ"]["_"][initial].append([form, "_"])
            return

        # NOUN
        initial = "vowel" if starts_with_vowel_letter(form) else "cons"
        bank["NOUN"]["Sing"][initial].append([form, "Sing"])
        plur = naive_plural(form)
        bank["NOUN"]["Plur"][initial].append([plur, "Plur"])

    # ------------------------------------------------------------------
    # Generation loop
    # ------------------------------------------------------------------
    for pos, seeds in seeds_by_pos.items():
        print(f"\n=== {pos} ===")
        for seed in seeds:
            print(f"  seed={seed}")
            try:
                results = wg.generate_classic(
                    [seed], ncandidates_per_sequence=N_PER_SEED
                )
            except Exception as e:
                print(f"  (!) seed failed: {seed} -> {type(e).__name__}: {e}")
                continue

            count = 0
            for r in results:
                if isinstance(r, dict) and "pseudoword" in r:
                    pw = r["pseudoword"]
                else:
                    pw = str(r)

                if pw.casefold() in avoid:
                    continue
                add_bucket(pos, pw)
                count += 1

            print(f"    generated={count}")

    # ------------------------------------------------------------------
    # Deduplication
    # ------------------------------------------------------------------
    def dedup(lst: List[List[str]]) -> List[List[str]]:
        seen: set[str] = set()
        out = []
        for entry in lst:
            norm = entry[0].casefold()
            if norm in seen:
                continue
            seen.add(norm)
            out.append(entry)
        return out

    for pos in bank:
        for slot in bank[pos]:
            for initial in bank[pos][slot]:
                bank[pos][slot][initial] = dedup(bank[pos][slot][initial])

    # ------------------------------------------------------------------
    # Save
    # ------------------------------------------------------------------
    OUT_PATH.write_text(
        json.dumps(bank, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"\nSaved -> {OUT_PATH.resolve()}")
    print("Counts:")
    print("  NOUN sing vowel :", len(bank["NOUN"]["Sing"]["vowel"]))
    print("  NOUN sing cons  :", len(bank["NOUN"]["Sing"]["cons"]))
    print("  NOUN plur vowel :", len(bank["NOUN"]["Plur"]["vowel"]))
    print("  NOUN plur cons  :", len(bank["NOUN"]["Plur"]["cons"]))
    print("  ADJ  vowel      :", len(bank["ADJ"]["_"]["vowel"]))
    print("  ADJ  cons       :", len(bank["ADJ"]["_"]["cons"]))
    print("  VERB            :", len(bank["VERB"]["_"]["_"]))
    print("  ADV             :", len(bank["ADV"]["_"]["_"]))


if __name__ == "__main__":
    main()
