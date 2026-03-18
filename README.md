# 🐉 Jabberwocky

> Generate French sentences that **look and feel syntactically correct** — but mean absolutely nothing.

---

## What is this?

**Jabberwocky** is a Python pipeline that produces French nonsense text: syntactically plausible sentences where content words (nouns, verbs, adjectives, adverbs) are swapped for **pseudowords** — invented forms that respect French orthographic and phonotactic patterns.

Pseudowords are generated with [Wuggy](https://github.com/WuggyGenerator/wuggy), a psycholinguistic tool originally designed for cognitive experiments. The result reads like French to the ear and eye — articles, verb tenses, and sentence structure all hold — but the semantic content dissolves into pure nonsense.

The pipeline runs in two stages:

1. **Bank building** — Wuggy generates a large lexicon of pseudowords, organized by part-of-speech, number (singular/plural), and phonological context (vowel-initial vs. consonant-initial). Saved as `data/bank_fr.json`.
2. **Text transformation** — [spaCy](https://spacy.io/) parses the input text morphosyntactically, then replaces a configurable proportion of content words with pseudowords sampled from the bank. Function words are always preserved.

---

## Project structure

```
jabberwocky/
├── data/
│   ├── Lexique383.tsv          # Optional: Lexique 3.83 frequency lexicon
│   └── bank_fr.json            # Pre-built pseudoword bank
├── outputs/
│   └── pseudowords_fr.txt      # Raw pseudowords from the demo script
├── scripts/
│   ├── build_bank_fr.py        # Builds the pseudoword bank via Wuggy
│   ├── demo_wuggy_fr.py        # Minimal demo: raw pseudoword generation
│   └── jabberwocky_text.py     # Main CLI: transform a French text
└── source/
    └── jw/
        ├── bank/
        │   ├── loader.py       # Loads bank_fr.json into sampler format
        │   ├── mock_data.py    # Hardcoded fallback bank (no Wuggy needed)
        │   └── sampler.py      # Samples pseudowords by POS / number / context
        ├── jabber/
        │   ├── policy.py       # Decides which tokens to replace and how often
        │   └── transform.py    # Core jabberwockify() function
        ├── nlp/
        │   └── spacy_fr.py     # spaCy wrapper → TokenInfo objects
        └── text/
            └── surface.py      # Case preservation, elision constraints
```

---

## Installation

```sh
pip install wuggy spacy
python -m spacy download fr_core_news_sm
```

> Requires **Python 3.10+**

---

## Usage

### Step 1 — Build the pseudoword bank

This only needs to be run once (or when you want to rebuild with different seeds).

**Quick mode** — uses a small hardcoded seed list, no external data needed:

```sh
python scripts/build_bank_fr.py
```

**Recommended mode** — uses [Lexique 3.83](http://www.lexique.org/) for frequency-ranked, high-quality seeds:

```sh
python scripts/build_bank_fr.py \
  --lexique-tsv data/Lexique383.tsv \
  --n-noun 20000 \
  --n-adj  10000 \
  --n-adv   5000 \
  --n-verb 10000
```

The bank is saved to `data/bank_fr.json`.

---

### Step 2 — Transform a text

```sh
python scripts/jabberwocky_text.py \
  --text "Le chat dort tranquillement sur le canapé." \
  --pct  0.6 \
  --seed 42
```

**Output:**
```
Le flane dort viteau sur le canapé.

(replaced=2/8, pct=0.6, seed=42)
```

**Available options:**

| Option | Default | Description |
|--------|---------|-------------|
| `--text` | *(required)* | French input text to transform |
| `--pct` | `0.6` | Proportion of content words to replace (0.0 → 1.0) |
| `--seed` | `0` | Random seed for reproducibility |
| `--bank` | `data/bank_fr.json` | Path to the pseudoword bank |

---

### Step 3 — (Optional) Inspect raw Wuggy output

To quickly see what Wuggy produces for a handful of seed words:

```sh
python scripts/demo_wuggy_fr.py
```

Results are saved to `outputs/pseudowords_fr.txt`.

---

## Strengths

- **Clean separation of concerns.** Four clearly bounded modules: NLP parsing, bank access, replacement logic, and surface utilities. Each layer can be modified or replaced independently.

- **Linguistically informed bank structure.** The bank is indexed by POS, number, and vowel/consonant initial. This makes it possible to partially enforce French elision constraints (e.g. avoid generating "le alune" where "l'alune" is required).

- **Policy-based replacement.** `ReplacementPolicy` separates the *decision logic* from the *transformation logic*. Function words are always preserved; auxiliaries and proper nouns can be optionally protected.

- **Verb morphology heuristics.** The transform layer detects past participle contexts (token preceded by an auxiliary) and applies `-er`/`-ir`/`-re` conjugation patterns to pseudoword verb bases. Better than an uninflected drop-in.

- **Case preservation.** A capitalized word at sentence start stays capitalized after replacement. All-caps tokens are handled too.

- **Reproducibility.** `--seed` seeds Python's `random.Random` — every transformation is fully deterministic.

- **Offline fallback.** `mock_data.py` provides a hardcoded bank so the full pipeline can be tested without Wuggy or any external data.

- **Lexique integration.** `build_bank_fr.py` can ingest Lexique 3.83, rank seed words by frequency, and filter for lemma forms and singular inflections.

---

## Limitations

- **Verb morphology is a heuristic patchwork.** Only the most common patterns (-er, -ir, -re) are handled. Irregular verbs (être, avoir, aller…) and compound tenses beyond passé composé are not covered.

- **No gender agreement.** When a noun is replaced, no gender information propagates to surrounding adjectives or determiners. "Le grande flane" is phonotactically fine but grammatically off.

- **Partial elision only.** `next_token_vowel_constraint` covers `le`, `la`, `l'`, `un`, `une` — but not `du`, `au`, liaison contexts, or *h aspiré*.

- **Modest bank size by default.** The hardcoded seed build produces ~300–440 pseudowords per POS. With high replacement rates on longer texts, repetition becomes noticeable. Use the Lexique build path to fix this.

- **No adjective gender.** Adjectives are replaced respecting number but not gender. A feminine noun may end up with a masculine-looking pseudoword adjective.

- **spaCy `fr_core_news_sm` accuracy.** On informal text, poetry, or old French, POS tagging and morphological analysis can be unreliable, and errors cascade.

- **No `requirements.txt` or `pyproject.toml`.** Dependencies must be installed manually. The `jw` package also relies on a working directory convention rather than a proper install path.

---

## Directions for improvement

- **Add gender to the bank** — assign a probabilistic gender to each pseudoword at build time (inherited from its seed word), then propagate it to adjust surrounding determiners and adjective forms.

- **Use a proper verb conjugator** — replace hand-rolled heuristics with a library like [mlconjug3](https://pypi.org/project/mlconjug3/) applied to pseudoword bases.

- **Expand elision and liaison handling** — build a complete list of French elision triggers; check phonological onset rather than just the first letter.

- **Package the project properly** — add a `pyproject.toml` with declared dependencies and a `pip install -e .` setup to eliminate fragile import path conventions.

- **Add a test suite** — `mock_data.py` is already well-suited as a fixture. Priority targets: case preservation, verb conjugation heuristics, number agreement, policy logic.

- **Support file I/O** — add `--input-file` and `--output-file` arguments for processing full documents.

- **Per-POS replacement rate** — allow independent `--pct-noun`, `--pct-verb`, etc. flags for finer control.

- **Phoneme-level bank** — Wuggy supports phonological plugins; a phoneme-level bank would match syllable count and stress patterns of the original word, which matters for psycholinguistics or TTS testing.

---

## File descriptions

### `scripts/`

| File | Role |
|------|------|
| `demo_wuggy_fr.py` | Minimal standalone script. Loads the Wuggy French plugin, generates up to 100 pseudowords for 6 hardcoded seeds, saves the list to `outputs/pseudowords_fr.txt`. Useful to verify Wuggy is working. |
| `build_bank_fr.py` | Main bank-building script. Accepts an optional Lexique 3.83 TSV; falls back to a small hardcoded seed list. Calls Wuggy per seed and POS, sorts results into buckets, deduplicates, and serialises to `data/bank_fr.json`. Also generates naive plural forms for nouns and adjectives. |
| `jabberwocky_text.py` | Main CLI entry point. Parses arguments, loads the bank, wires up sampler + policy + transform, and prints the result with replacement statistics. |

### `data/`

| File | Role |
|------|------|
| `Lexique383.tsv` | Copy of the [Lexique 3.83](http://www.lexique.org/) database — a large French psycholinguistic lexicon with frequency counts, POS tags, and morphological features. Used optionally by `build_bank_fr.py`. |
| `bank_fr.json` | Pre-built pseudoword bank. JSON indexed by POS → number → initial-type → list of pseudoword strings. |

### `outputs/`

| File | Role |
|------|------|
| `pseudowords_fr.txt` | Raw output of `demo_wuggy_fr.py`. Plain-text pseudowords grouped by seed word. Diagnostic/inspection only — not used by the main pipeline. |

### `source/jw/bank/`

| File | Role |
|------|------|
| `loader.py` | Reads `bank_fr.json` and converts it to the internal dict format: `(pos, number, initial) → List[str]`, with `None` for flat POS categories (VERB, ADV). |
| `sampler.py` | `BankSampler` dataclass. Exposes a `sample(pos, number, needs_vowel_start, rng, avoid)` method with fallback logic for empty buckets and an `avoid` set to reduce within-document repetition. |
| `mock_data.py` | Hardcoded ~15-word bank per bucket. Covers all POS/number/initial combinations. Intended for tests and development without Wuggy. |

### `source/jw/jabber/`

| File | Role |
|------|------|
| `policy.py` | `ReplacementPolicy` frozen dataclass. Holds `pct_replace` and POS keep/replace sets. `should_replace(tok, rng)` encodes the full decision logic. |
| `transform.py` | Core engine. `jabberwockify()` iterates over tokens, applies the policy, samples replacements, applies verb morphology heuristics (present tense or past participle by context), preserves casing, and reconstructs the string with original whitespace. |

### `source/jw/nlp/`

| File | Role |
|------|------|
| `spacy_fr.py` | Thin spaCy wrapper. `SpacyFrenchNLP.parse(text)` returns a list of `TokenInfo` dataclasses (surface form, lemma, POS, morphology dict, trailing whitespace). Also normalises typographic dashes to ASCII hyphens before parsing, to stabilise tokenisation of French dialogue em-dashes. |

### `source/jw/text/`

| File | Role |
|------|------|
| `surface.py` | Pure utilities, no external dependencies. `preserve_case` maps casing from source to replacement. `starts_with_vowel_letter` checks the first character against French vowels. `next_token_vowel_constraint` inspects the previous token to enforce vowel-initial or consonant-initial replacements. |
