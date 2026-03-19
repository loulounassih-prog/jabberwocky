from __future__ import annotations

from dataclasses import dataclass
from typing import Optional
import random
import hashlib

from jw.bank.sampler import BankSampler
from jw.jabber.policy import ReplacementPolicy
from jw.nlp.spacy_fr import SpacyFrenchNLP, TokenInfo
from jw.text.surface import preserve_case, next_token_vowel_constraint, starts_with_vowel_letter


@dataclass
class TransformResult:
    text: str
    replaced: int
    total_tokens: int


# -----------------------------
# Morphology utilities
# -----------------------------

def _get_number(tok: TokenInfo) -> str:
    # Default to singular when number is missing or unsupported
    n = tok.morph.get("Number")
    if n in ("Sing", "Plur"):
        return n
    return "Sing"


def _get_gender(tok: TokenInfo) -> str:
    # Default to masculine when gender is missing or unsupported
    g = tok.morph.get("Gender")
    if g == "Fem":
        return "Fem"
    return "Masc"


# -----------------------------
# Determiner agreement
# -----------------------------

def _adjust_prev_ce(prev_tok: TokenInfo, next_tok: TokenInfo, next_out_text: str) -> str | None:
    """
    Adjust a previous "ce" before a vowel-initial output word:
      - Fem -> "cette"
      - Otherwise "cet"
      - Return None when no adjustment needed
    """

    if prev_tok.pos != "DET": 
        return None                 # "Ce" is a DET
    
    if not any(ch.isalpha() for ch in next_out_text):
        return None                 # Skip punctuation and numbers

    prev_norm = prev_tok.text.lower().replace("\u2019", "'")        # Normalize ASCII and typographic apostrophes
    prev_lemma = prev_tok.lemma.lower().replace("\u2019", "'")
    if prev_norm != "ce" and prev_lemma != "ce":
        return None

    if not starts_with_vowel_letter(next_out_text):
        return None

    gender = _get_gender(next_tok)
    if gender == "Fem":
        return preserve_case(prev_tok.text, "cette")
    return preserve_case(prev_tok.text, "cet")


def _adjust_det_gender(prev_tok: TokenInfo, gender: str, next_after_det_text: str) -> str | None:
    """
    Adjust a preceding determiner to match the governing NOUN gender.

    For euphonic alternations (ce/cet, mon/ma, ton/ta, son/sa),
    use the surface form of the word immediately following the determiner,
    not necessarily the NOUN itself.
    """
    if prev_tok.pos != "DET":
        return None

    det = prev_tok.text.lower().replace("\u2019", "'")
    vowel = starts_with_vowel_letter(next_after_det_text)

    # ce / cet / cette
    if det in ("ce", "cet", "cette"):
        if gender == "Fem":
            target = "cette"
        else:
            target = "cet" if vowel else "ce"

        if target != det:
            return preserve_case(prev_tok.text, target)
        return None

    # mon / ma ; ton / ta ; son / sa
    # Keep mon/ton/son before feminine vowel-initial words: "mon amie"
    if det in ("mon", "ma"):
        target = "ma" if gender == "Fem" and not vowel else "mon"
        if target != det:
            return preserve_case(prev_tok.text, target)
        return None

    if det in ("ton", "ta"):
        target = "ta" if gender == "Fem" and not vowel else "ton"
        if target != det:
            return preserve_case(prev_tok.text, target)
        return None

    if det in ("son", "sa"):
        target = "sa" if gender == "Fem" and not vowel else "son"
        if target != det:
            return preserve_case(prev_tok.text, target)
        return None

    # Simple one-to-one cases
    masc_to_fem = {
        "un": "une",
        "le": "la",
    }
    fem_to_masc = {
        "une": "un",
        "la": "le",
    }

    if gender == "Fem" and det in masc_to_fem:
        return preserve_case(prev_tok.text, masc_to_fem[det])

    if gender == "Masc" and det in fem_to_masc:
        return preserve_case(prev_tok.text, fem_to_masc[det])

    return None


def _find_left_det_index(tokens: list[TokenInfo], head_index: int) -> int | None:
    """
    Find the determiner that should agree with the current NOUN.
    Allow ADJ/ADV between DET and NOUN, but stop on stronger boundaries.
    """
    for j in range(head_index - 1, -1, -1):
        t = tokens[j]

        if t.pos == "DET":
            return j

        if t.pos in ("ADJ", "ADV"):
            continue

        break

    return None


# -----------------------------
# Adjective feminization
# -----------------------------

def _find_governing_noun_gender(tokens: list[TokenInfo], adj_index: int) -> str | None:
    """
    Find the gender of the NOUN that governs the current ADJ.
    Looks left and right a few tokens, skipping DET/ADV/other ADJ.
    Returns 'Masc', 'Fem', or None if no governing noun is found.
    """
    # Look left first (attributive: "une grande maison")
    for j in range(adj_index - 1, max(-1, adj_index - 4), -1):
        t = tokens[j]
        if t.pos == "NOUN":
            return _get_gender(t)
        if t.pos in ("DET", "ADV", "ADJ"):
            continue
        break

    # Look right (predicative: "la maison est grande")
    for j in range(adj_index + 1, min(len(tokens), adj_index + 4)):
        t = tokens[j]
        if t.pos == "NOUN":
            return _get_gender(t)
        if t.pos in ("ADV", "ADJ"):
            continue
        break

    return None


# -----------------------------
# Contraction handling (du/au)
# -----------------------------

# Maps contracted determiners to their de-contracted forms before vowel-initial words.
# "du arbre" is ungrammatical; it must become "de l'arbre".
# "des" and "aux" are intentionally excluded: "des arbres" and "aux arbres" are correct as-is.
_DECONTRACT: dict[str, str] = {
    "du": "de l'",
    "au": "à l'",
    "Du": "De l'",
    "Au": "À l'",
    "DU": "DE L'",
    "AU": "À L'",
}

# -----------------------------
# Contraction handling (du/au)
# -----------------------------


def _adjust_contraction(prev_tok: TokenInfo, out_text: str) -> str | None:
    """
    If the previous token is a contraction (du, au) and the generated pseudo-word
    starts with a vowel despite the onset constraint (sampler fallback),
    de-contract: "du" -> "de l'", "au" -> "à l'".
    Returns the new determiner surface form, or None if no adjustment is needed.
    """
    raw = prev_tok.text.replace("\u2019", "'")
    if raw not in _DECONTRACT:
        return None
    if starts_with_vowel_letter(out_text):
        return _DECONTRACT[raw]
    return None

# -----------------------------
# Verb heuristics (v1)
# -----------------------------

_PAST_PP_ENDINGS = (
    "é", "ée", "és", "ées",
    "i", "ie", "is", "ies",
    "u", "ue", "us", "ues",
)

_PP_ROOTS = ("é", "i", "u")

_PP_ENDINGS_BY_ROOT = {
    "é": {"Masc": {"Sing": "é", "Plur": "és"}, "Fem": {"Sing": "ée", "Plur": "ées"}},
    "i": {"Masc": {"Sing": "i", "Plur": "is"}, "Fem": {"Sing": "ie", "Plur": "ies"}},
    "u": {"Masc": {"Sing": "u", "Plur": "us"}, "Fem": {"Sing": "ue", "Plur": "ues"}},
}

_VOWELS = ("a", "e", "i", "o", "u", "y", "é", "è", "ê")

def _looks_like_past_participle(w: str) -> bool:
    # Naive check — known false positive: "bleu" matches the "eu" suffix
    wl = w.lower()
    return any(wl.endswith(suf) for suf in _PAST_PP_ENDINGS)


def _append_ending(base: str, ending: str) -> str:
    if not base:
        return ending
    if base[-1].lower() in _VOWELS and ending[0].lower() in _VOWELS:
        return base[:-1] + ending      # Drop trailing vowel to avoid vowel clusters
    return base + ending


def _to_past_participle(w: str, number: str, gender: str) -> str:
    """
    Very naive: if not already pp-like, append a common pp ending.
    We pick among ('é','i','u') deterministically for stable results.
    """
    wl = w.lower()
    if _looks_like_past_participle(wl):
        return w

    # Deterministically choose one participle-ending family ("é", "i", or "u") from the pseudo-verb stem.
    digest = hashlib.md5(wl.encode("utf-8")).digest()
    root_index = int.from_bytes(digest[:4], "big") % len(_PP_ROOTS)
    root = _PP_ROOTS[root_index]
    
    ending = _PP_ENDINGS_BY_ROOT[root][gender][number]
    return _append_ending(wl, ending)


def _guess_subject_number(tokens: list[TokenInfo], verb_index: int) -> str:
    """
    Minimal subject number guess:
    Look left a few tokens for a likely subject (PRON or NOUN), ignoring punctuation/determiners.
    """
    for j in range(verb_index - 1, max(-1, verb_index - 6), -1):
        t = tokens[j]

        if t.pos in ("PUNCT", "DET", "ADP", "PART", "CCONJ", "SCONJ"):  
            continue

        if t.pos == "PRON":
            p = t.text.lower()
            if p in ("ils", "elles", "nous", "vous"):
                return "Plur"
            if p in ("je", "j'", "tu", "il", "elle", "on"):
                return "Sing"
            return "Sing"

        if t.pos in ("NOUN", "PROPN"):
            return _get_number(t)

        # If we hit another verb or something weird, stop guessing
        if t.pos in ("VERB", "AUX"):
            break

    return "Sing"


def _guess_tense_from_surface(tok: TokenInfo) -> str:
    """
    Fallback tense detection based on the surface form of the original verb,
    used when spaCy's morphological analysis is unreliable (e.g. fr_core_news_sm
    conflates conditional and imperfect under Tense=Imp).
    Returns 'Cnd', 'Imp', 'Fut', or 'Pres'.
    """
    w = tok.text.lower()
    if w.endswith(("rais", "rait", "raient", "rions", "riez")):
        return "Cnd"
    if w.endswith(("ais", "ait", "aient", "ions", "iez")):
        return "Imp"
    if w.endswith(("rai", "ras", "ra", "rons", "rez", "ront")):
        return "Fut"
    return "Pres"


def _to_present_like(w: str, number: str) -> str:
    """
    Make a pseudo-form that looks like a present tense form.

    v1:
      - If infinitive-looking, do a tiny conjugation heuristic
      - Otherwise: Singular ends with e/s/t; Plural ends with 'ent'
    """
    wl = w.lower()

    if wl.endswith("er"):
        stem = w[:-2]
        return stem + ("ent" if number == "Plur" else "e")
    if wl.endswith("ir"):
        stem = w[:-2]
        return stem + ("issent" if number == "Plur" else "it")
    if wl.endswith("re"):
        stem = w[:-2]
        return stem + ("ent" if number == "Plur" else "t")

    if number == "Plur":
        if wl.endswith("ent"):
            return w
        if wl.endswith("e"):
            return w[:-1] + "ent"               # avoid "....eent"
        return w + "ent"

    if wl.endswith(("e", "s", "t", "é", "è", "ê")):
        return w
    return w + "e"


def _to_imperfect_like(w: str, number: str) -> str:
    """
    Produce a pseudo-form that looks like an imperfect tense conjugation.
    Singular: stem + "ait", Plural: stem + "aient"
    """
    wl = w.lower()
    # Strip common infinitive endings to get the stem
    if wl.endswith("er") or wl.endswith("ir") or wl.endswith("re"):
        stem = w[:-2]
    elif wl.endswith("e"):
        stem = w[:-1]
    else:
        stem = w
    return stem + ("aient" if number == "Plur" else "ait")


def _to_future_like(w: str, number: str) -> str:
    """
    Produce a pseudo-form that looks like a future tense conjugation.
    Built on the infinitive stem: stem + "era" / "eront"
    """
    wl = w.lower()
    if wl.endswith("re"):
        stem = w[:-1]   # "trame" -> "tramr" is ugly; keep the e: "tramer" -> "tramere"
    elif wl.endswith("e"):
        stem = w
    else:
        stem = w
    return stem + ("ont" if number == "Plur" else "a")


def _to_conditional_like(w: str, number: str) -> str:
    """
    Produce a pseudo-form that looks like a conditional conjugation.
    Conditional = future stem + imperfect ending: stem + "erait" / "eraient"
    """
    wl = w.lower()
    if wl.endswith("re"):
        stem = w[:-1]
    elif wl.endswith("e"):
        stem = w
    else:
        stem = w
    return stem + ("raient" if number == "Plur" else "rait")


def _to_gerund_like(w: str) -> str:
    """
    Produce a pseudo-form that looks like a gerund (gérondif).
    Stem + "ant"
    """
    wl = w.lower()
    if wl.endswith("er") or wl.endswith("ir") or wl.endswith("re"):
        stem = w[:-2]
    elif wl.endswith("e"):
        stem = w[:-1]
    else:
        stem = w
    return stem + "ant"


def _feminize_adj(w: str) -> str:
    """
    Naive feminine form heuristic for pseudo-adjectives.
    Covers the most common French adjective patterns:
      -al  -> -ale   (grival -> grivale)
      -if  -> -ive   (cravif -> cravive)
      -eux -> -euse  (glavreux -> glavreuse)
      -ien -> -ienne (not in mock but common)
      -on  -> -onne  (not in mock but common)
      -el  -> -elle  (tranchel -> tranchelle)
      -et  -> -ette  (not in mock but common)
      already ends in -e -> unchanged (trusque -> trusque)
    """
    wl = w.lower()

    if wl.endswith("eux"):
        return w[:-3] + "euse"
    if wl.endswith("if"):
        return w[:-2] + "ive"
    if wl.endswith("ien"):
        return w + "ne"
    if wl.endswith("el"):
        return w + "le"
    if wl.endswith("et"):
        return w + "te"
    if wl.endswith("on"):
        return w + "ne"
    if wl.endswith("al"):
        return w + "e"
    if wl.endswith("e"):
        return w   # already feminine-compatible
    # Default: append "e"
    return w + "e"


def jabberwockify(
    text: str,
    sampler: BankSampler,
    policy: ReplacementPolicy,
    nlp: Optional[SpacyFrenchNLP] = None,
    seed: Optional[int] = None,
) -> TransformResult:

    rng = random.Random(seed)
    nlp = nlp or SpacyFrenchNLP()

    tokens = nlp.parse(text)

    out_parts: list[str] = []
    replaced = 0

    avoid: set[str] = set()
    out_gender: Optional[str] = None

    for i, tok in enumerate(tokens):
        replaced_this = False

        if not any(ch.isalpha() for ch in tok.text):
            out_text = tok.text
            out_gender = None

        elif not policy.should_replace(tok, rng):
            out_text = tok.text
            out_gender = None

        else:
            prev_text = tokens[i - 1].text if i > 0 else ""
            vowel_constraint = next_token_vowel_constraint(prev_text)

            if tok.pos == "NOUN":
                number = _get_number(tok)
                form, gender = sampler.sample("NOUN", number, vowel_constraint, rng, avoid=avoid)
                out_text = preserve_case(tok.text, form)
                out_gender = gender
                replaced_this = True
                replaced += 1
                avoid.add(form.lower())

            elif tok.pos == "ADJ":
                number = _get_number(tok)
                form, _ = sampler.sample("ADJ", number, vowel_constraint, rng, avoid=avoid)
                # Apply feminine form if the governing noun is feminine
                noun_gender = _find_governing_noun_gender(tokens, i)
                if noun_gender == "Fem":
                    form = _feminize_adj(form)
                out_text = preserve_case(tok.text, form)
                out_gender = None
                replaced_this = True
                replaced += 1
                avoid.add(form.lower())

            elif tok.pos == "ADV":
                form, _ = sampler.sample("ADV", None, None, rng, avoid=avoid)
                out_text = preserve_case(tok.text, form)
                out_gender = None
                replaced_this = True
                replaced += 1
                avoid.add(form.lower())

            elif tok.pos == "VERB":
                base, _ = sampler.sample("VERB", None, None, rng, avoid=avoid)
                prev_pos = tokens[i - 1].pos if i > 0 else ""
                number = _get_number(tok)
                verbform = tok.morph.get("VerbForm", "Fin")

                if prev_pos == "AUX":
                    # Past participle (passé composé)
                    gender = _get_gender(tok)
                    flexed = _to_past_participle(base, number, gender)
                elif verbform == "Inf":
                    # Infinitive: leave the base form unchanged
                    flexed = base
                elif verbform == "Part":
                    # Present participle / gerund
                    flexed = _to_gerund_like(base)
                else:
                    # Finite form — detect tense from surface
                    surface_tense = _guess_tense_from_surface(tok)
                    mood_map = {"Cnd": "Cnd", "Imp": "Ind", "Fut": "Ind", "Pres": "Ind"}
                    tense_map = {"Cnd": "Pres", "Imp": "Imp", "Fut": "Fut", "Pres": "Pres"}
                    subj_number = _guess_subject_number(tokens, i)
                    flexed = _to_present_like(base, subj_number)
                    if surface_tense == "Cnd":
                        flexed = _to_conditional_like(base, subj_number)
                    elif surface_tense == "Imp":
                        flexed = _to_imperfect_like(base, subj_number)
                    elif surface_tense == "Fut":
                        flexed = _to_future_like(base, subj_number)

                out_text = preserve_case(tok.text, flexed)
                out_gender = None
                replaced_this = True
                replaced += 1
                avoid.add(out_text.lower())

            else:
                out_text = tok.text
                out_gender = None

        # Adjust the determiner governed by the current NOUN,
        # even if ADJ/ADV appear between DET and NOUN.
        if tok.pos == "NOUN":
            det_index = _find_left_det_index(tokens, i)

            if det_index is not None:
                det_tok = tokens[det_index]

                if out_gender is not None:
                    if det_index + 1 == i:
                        next_after_det_text = out_text
                    elif det_index + 1 < len(out_parts):
                        next_after_det_text = out_parts[det_index + 1].rstrip()
                    else:
                        next_after_det_text = out_text

                    gendered = _adjust_det_gender(det_tok, out_gender, next_after_det_text)
                    if gendered is not None and det_index < len(out_parts):
                        out_parts[det_index] = gendered + det_tok.whitespace

        if replaced_this and i > 0:
            contraction = _adjust_contraction(tokens[i - 1], out_text)
            if contraction is not None and (i - 1) < len(out_parts):
                out_parts[i - 1] = contraction + tokens[i - 1].whitespace

        out_parts.append(out_text + tok.whitespace)

    return TransformResult(text="".join(out_parts), replaced=replaced, total_tokens=len(tokens))