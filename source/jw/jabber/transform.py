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


def _get_number(tok: TokenInfo) -> str:
    n = tok.morph.get("Number")
    if n in ("Sing", "Plur"):
        return n
    return "Sing"
# Default to singular when number is missing or unsupported

def _get_gender(tok: TokenInfo) -> str:
    g = tok.morph.get("Gender")
    if g == "Fem":
        return "Fem"
    return "Masc"
# Default to masc when gender is missing or unsupported

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
        return None                 # If the next word doesn't contain letters : punctuation, numbers...
    
    prev_norm = prev_tok.text.lower().replace("\u2019", "'")        # To treat the same way the ASCII and typo ' 
    prev_lemma = prev_tok.lemma.lower().replace("\u2019", "'")
    if prev_norm != "ce" and prev_lemma != "ce":
        return None

    if not starts_with_vowel_letter(next_out_text):
        return None

    gender = _get_gender(next_tok)
    if gender == "Fem":
        return preserve_case(prev_tok.text, "cette")
    return preserve_case(prev_tok.text, "cet")



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

def _looks_like_past_participle(w: str) -> bool:            # First naïve way because bleu is treated as pp
    wl = w.lower()
    return any(wl.endswith(suf) for suf in _PAST_PP_ENDINGS)


def _append_ending(base: str, ending: str) -> str:
    if not base:
        return ending
    if base[-1].lower() in _VOWELS and ending[0].lower() in _VOWELS:
        return base[:-1] + ending                           # To remove collisions between vowels
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
    digest = hashlib.md5(wl.encode("utf-8")).digest()$
    root_index = int.from_bytes(digest[:4], "big") % len(_PP_ROOTS)
    root = _PP_ROOTS[root_index]
    
    ending = _PP_ENDINGS_BY_ROOT[root][gender][number]
    return _append_ending(w, ending)


def _guess_subject_number(tokens: list[TokenInfo], verb_index: int) -> str:
    """
    Minimal subject number guess:
    Look left a few tokens for a likely subject (PRON or NOUN), ignoring punctuation/determiners.
    """
    # Search a few tokens to the left for a likely subject.
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
    prev_replaced = False

    for i, tok in enumerate(tokens):
        replaced_this = False

        if not any(ch.isalpha() for ch in tok.text):
            out_text = tok.text
        
        elif not policy.should_replace(tok, rng):
            out_text = tok.text
        
        else:
            prev_text = tokens[i - 1].text if i > 0 else ""
            vowel_constraint = next_token_vowel_constraint(prev_text)

            if tok.pos in ("NOUN", "ADJ"):
                number = _get_number(tok)
                repl = sampler.sample(tok.pos, number, vowel_constraint, rng, avoid=avoid)
                out_text = preserve_case(tok.text, repl)
                replaced_this = True
                replaced += 1
                avoid.add(repl.lower())

            elif tok.pos == "ADV":
                repl = sampler.sample("ADV", None, None, rng, avoid=avoid)
                out_text = preserve_case(tok.text, repl)
                replaced_this = True
                replaced += 1
                avoid.add(repl.lower())

            elif tok.pos == "VERB":
                base = sampler.sample("VERB", None, None, rng, avoid=avoid)

                # If preceded by an AUX token, force a pseudo past participle
                prev_pos = tokens[i - 1].pos if i > 0 else ""
                if prev_pos == "AUX":
                    number = _get_number(tok)
                    gender = _get_gender(tok)
                    flexed = _to_past_participle(base, number, gender)
                else:
                    subj_number = _guess_subject_number(tokens, i)  # Sing/Plur
                    flexed = _to_present_like(base, subj_number)

                out_text = preserve_case(tok.text, flexed)
                replaced_this = True
                replaced += 1
                avoid.add(out_text.lower())
            else:
                # Rare fallback
                out_text = tok.text

        if i > 0 and not prev_replaced:
            prev_tok = tokens[i - 1]
            adj = _adjust_prev_ce(prev_tok, tok, out_text)
            if adj is not None and out_parts:
                out_parts[-1] = adj + prev_tok.whitespace

        out_parts.append(out_text + tok.whitespace)
        prev_replaced = replaced_this

    return TransformResult(text="".join(out_parts), replaced=replaced, total_tokens=len(tokens))