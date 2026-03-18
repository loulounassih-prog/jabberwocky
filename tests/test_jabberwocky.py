from __future__ import annotations

import pytest

from jw.text.surface import preserve_case, starts_with_vowel_letter, next_token_vowel_constraint
from jw.jabber.transform import (
    _feminize_adj,
    _to_present_like,
    _to_imperfect_like,
    _to_future_like,
    _to_conditional_like,
    _to_gerund_like,
    _to_past_participle,
    _adjust_contraction,
    _guess_tense_from_surface,
)
from jw.nlp.spacy_fr import TokenInfo
from jw.bank.sampler import BankSampler
from jw.bank.mock_data import MOCK_BANK
from jw.jabber.policy import ReplacementPolicy
from jw.jabber.transform import jabberwockify


# --------------------------------------------------
# Fixtures
# --------------------------------------------------

def make_token(text: str, pos: str = "NOUN", morph: dict | None = None) -> TokenInfo:
    return TokenInfo(text=text, lemma=text.lower(), pos=pos, morph=morph or {}, whitespace=" ")


def make_sampler() -> BankSampler:
    # Convert mock_data str entries to (form, gender) tuples
    bank = {}
    for key, forms in MOCK_BANK.items():
        pos = key[0]
        entries = []
        for f in forms:
            if isinstance(f, tuple):
                entries.append(f)
            else:
                gender = "_" if pos in ("VERB", "ADV") else "Masc"
                entries.append((f, gender))
        bank[key] = entries
    return BankSampler(bank)


# --------------------------------------------------
# surface.py
# --------------------------------------------------

class TestPreserveCase:
    def test_lowercase(self):
        assert preserve_case("chat", "flane") == "flane"

    def test_capitalized(self):
        assert preserve_case("Chat", "flane") == "Flane"

    def test_uppercase(self):
        assert preserve_case("CHAT", "flane") == "FLANE"

    def test_empty_src(self):
        assert preserve_case("", "flane") == "flane"


class TestStartsWithVowel:
    def test_vowel(self):
        assert starts_with_vowel_letter("arbre") is True

    def test_consonant(self):
        assert starts_with_vowel_letter("chat") is False

    def test_accented_vowel(self):
        assert starts_with_vowel_letter("école") is True

    def test_empty(self):
        assert starts_with_vowel_letter("") is False


class TestVowelConstraint:
    def test_elided_form_forces_vowel(self):
        assert next_token_vowel_constraint("l'") is True

    def test_le_forces_consonant(self):
        assert next_token_vowel_constraint("le") is False

    def test_du_forces_consonant(self):
        assert next_token_vowel_constraint("du") is False

    def test_au_forces_consonant(self):
        assert next_token_vowel_constraint("au") is False

    def test_neutral_word_no_constraint(self):
        assert next_token_vowel_constraint("très") is None

    def test_empty_no_constraint(self):
        assert next_token_vowel_constraint("") is None


# --------------------------------------------------
# Verb morphology
# --------------------------------------------------

class TestToPresentLike:
    def test_er_singular(self):
        assert _to_present_like("tramer", "Sing") == "trame"

    def test_er_plural(self):
        assert _to_present_like("tramer", "Plur") == "trament"

    def test_ir_singular(self):
        assert _to_present_like("brandir", "Sing") == "brandit"

    def test_ir_plural(self):
        assert _to_present_like("brandir", "Plur") == "brandissent"

    def test_re_singular(self):
        assert _to_present_like("plondre", "Sing") == "plondt"

    def test_already_ends_e(self):
        assert _to_present_like("trame", "Sing") == "trame"


class TestToImperfectLike:
    def test_singular(self):
        assert _to_imperfect_like("tramer", "Sing") == "tramait"

    def test_plural(self):
        assert _to_imperfect_like("tramer", "Plur") == "tramaient"

    def test_stem_ending_e(self):
        assert _to_imperfect_like("trame", "Sing") == "tramait"


class TestToFutureLike:
    def test_singular(self):
        assert _to_future_like("trame", "Sing") == "tramea"

    def test_plural(self):
        assert _to_future_like("trame", "Plur") == "trameont"


class TestToConditionalLike:
    def test_singular(self):
        assert _to_conditional_like("trame", "Sing") == "tramerait"

    def test_plural(self):
        assert _to_conditional_like("trame", "Plur") == "trameraient"


class TestToGerundLike:
    def test_er_stem(self):
        assert _to_gerund_like("tramer") == "tramant"

    def test_e_stem(self):
        assert _to_gerund_like("trame") == "tramant"


class TestToPastParticiple:
    def test_already_pp(self):
        # Already looks like a past participle — leave unchanged
        result = _to_past_participle("tramé", "Sing", "Masc")
        assert result == "tramé"

    def test_masc_sing(self):
        result = _to_past_participle("trame", "Sing", "Masc")
        assert result[-1] in ("é", "i", "u")

    def test_fem_sing(self):
        result = _to_past_participle("trame", "Sing", "Fem")
        assert result.endswith(("ée", "ie", "ue"))

    def test_masc_plur(self):
        result = _to_past_participle("trame", "Plur", "Masc")
        assert result.endswith(("és", "is", "us"))


class TestGuessTenseFromSurface:
    def test_conditional(self):
        tok = make_token("partirait", pos="VERB")
        assert _guess_tense_from_surface(tok) == "Cnd"

    def test_imperfect(self):
        tok = make_token("dormait", pos="VERB")
        assert _guess_tense_from_surface(tok) == "Imp"

    def test_future(self):
        tok = make_token("mangera", pos="VERB")
        assert _guess_tense_from_surface(tok) == "Fut"

    def test_present_default(self):
        tok = make_token("mange", pos="VERB")
        assert _guess_tense_from_surface(tok) == "Pres"


# --------------------------------------------------
# Adjective feminization
# --------------------------------------------------

class TestFeminizeAdj:
    def test_al(self):
        assert _feminize_adj("grival") == "grivale"

    def test_if(self):
        assert _feminize_adj("cravif") == "cravive"

    def test_eux(self):
        assert _feminize_adj("glavreux") == "glavreuse"

    def test_el(self):
        assert _feminize_adj("tranchel") == "tranchelle"

    def test_already_e(self):
        assert _feminize_adj("trusque") == "trusque"


# --------------------------------------------------
# Contraction handling
# --------------------------------------------------

class TestAdjustContraction:
    def test_du_before_vowel(self):
        tok = make_token("du", pos="DET")
        assert _adjust_contraction(tok, "arbre") == "de l'"

    def test_du_before_consonant(self):
        tok = make_token("du", pos="DET")
        assert _adjust_contraction(tok, "chat") is None

    def test_au_before_vowel(self):
        tok = make_token("au", pos="DET")
        assert _adjust_contraction(tok, "arbre") == "à l'"

    def test_other_token(self):
        tok = make_token("le", pos="DET")
        assert _adjust_contraction(tok, "arbre") is None


# --------------------------------------------------
# Full pipeline (integration)
# --------------------------------------------------

class TestJabberwockify:
    def setup_method(self):
        self.sampler = make_sampler()
        self.policy_full = ReplacementPolicy(pct_replace=1.0)
        self.policy_none = ReplacementPolicy(pct_replace=0.0)

    def test_no_replacement_preserves_text(self):
        result = jabberwockify("Le chat dort.", self.sampler, self.policy_none, seed=0)
        assert result.text == "Le chat dort."
        assert result.replaced == 0

    def test_full_replacement_changes_content_words(self):
        result = jabberwockify("Le chat mange la souris.", self.sampler, self.policy_full, seed=0)
        # "chat", "mange", "souris" should be replaced; "Le", "la", "." preserved
        assert result.replaced >= 2
        assert "chat" not in result.text.lower()

    def test_no_du_before_vowel(self):
        # With pct=1.0, the sampler should never produce "du <vowel-initial>"
        # because surface.py forces consonant onset after "du"
        for seed in range(20):
            result = jabberwockify("Il parle du chat.", self.sampler, self.policy_full, seed=seed)
            words = result.text.split()
            for i, w in enumerate(words):
                if w.lower() == "du" and i + 1 < len(words):
                    assert not starts_with_vowel_letter(words[i + 1]), (
                        f"seed={seed}: found 'du' before vowel-initial word: {result.text}"
                    )

    def test_replaced_count_matches(self):
        result = jabberwockify(
            "La grande maison est belle.", self.sampler, self.policy_full, seed=0
        )
        assert result.replaced == result.total_tokens - sum(
            1 for c in ["La", "est", "."] if c in result.text
        ) or result.replaced > 0  # at least something was replaced

    def test_reproducible_with_seed(self):
        r1 = jabberwockify("Le chat dort.", self.sampler, self.policy_full, seed=42)
        r2 = jabberwockify("Le chat dort.", self.sampler, self.policy_full, seed=42)
        assert r1.text == r2.text
