from __future__ import annotations

import streamlit as st
from pathlib import Path

from jw.bank.loader import load_bank_json
from jw.bank.sampler import BankSampler
from jw.jabber.policy import ReplacementPolicy
from jw.jabber.transform import jabberwockify


# ----------------------------
# Page config
# ----------------------------
st.set_page_config(
    page_title="Jabberwocky",
    page_icon="🐉",
    layout="centered",
)

# Hide Streamlit default UI elements
st.markdown("""
<style>
#MainMenu {visibility: hidden;}
header {visibility: hidden;}
footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)


# ----------------------------
# Bank loader (cached)
# ----------------------------
@st.cache_resource
def load_sampler(bank_path: str) -> BankSampler:
    bank = load_bank_json(Path(bank_path))
    return BankSampler(bank)


# ----------------------------
# Header
# ----------------------------
st.markdown("# 🐉 Jabberwocky")
st.markdown(
    "Generate syntactically correct French sentences — but completely devoid of meaning. "
    "Function words (determiners, prepositions, pronouns) are always preserved. "
    "Only content words are replaced by phonotactically plausible pseudowords."
)

st.divider()

# ----------------------------
# Input
# ----------------------------
st.markdown("#### Input text")
text = st.text_area(
    label="Input text",
    value="Le chat dort tranquillement sur le canapé.",
    height=120,
    label_visibility="collapsed",
    placeholder="Enter a French sentence...",
)

st.markdown("#### Parameters")

col1, col2 = st.columns(2)
with col1:
    pct = st.slider(
        "Replacement rate",
        min_value=0.0,
        max_value=1.0,
        value=0.6,
        step=0.05,
        help="Global proportion of content words to replace.",
    )
with col2:
    seed = st.number_input(
        "Random seed",
        min_value=0,
        max_value=9999,
        value=42,
        step=1,
        help="Same seed = same output. Change it to get a different transformation.",
    )

st.markdown(
    "**Per-category control** *(optional — overrides the global rate for each category)*"
)

col3, col4, col5, col6 = st.columns(4)
with col3:
    pct_noun = st.slider("Nouns", 0.0, 1.0, pct, 0.05, key="noun",
                         help="Replacement rate for nouns.")
with col4:
    pct_verb = st.slider("Verbs", 0.0, 1.0, pct, 0.05, key="verb",
                         help="Replacement rate for verbs.")
with col5:
    pct_adj = st.slider("Adjectives", 0.0, 1.0, pct, 0.05, key="adj",
                        help="Replacement rate for adjectives.")
with col6:
    pct_adv = st.slider("Adverbs", 0.0, 1.0, pct, 0.05, key="adv",
                        help="Replacement rate for adverbs.")

st.divider()

# ----------------------------
# Transform
# ----------------------------
if st.button("Transform 🐉", type="primary", use_container_width=True):
    if not text.strip():
        st.warning("Please enter a text to transform.")
    else:
        with st.spinner("Transforming..."):
            sampler = load_sampler("data/bank_fr.json")
            policy = ReplacementPolicy(
                pct_replace=pct,
                pct_by_pos={
                    "NOUN": pct_noun,
                    "VERB": pct_verb,
                    "ADJ":  pct_adj,
                    "ADV":  pct_adv,
                },
            )
            result = jabberwockify(
                text,
                sampler=sampler,
                policy=policy,
                seed=int(seed),
            )

        # ----------------------------
        # Results
        # ----------------------------
        st.markdown("#### Result")

        st.text_area(
            label="Result",
            value=result.text,
            height=120,
            label_visibility="collapsed",
            disabled=True,
        )

        # Copy button
        st.code(result.text, language=None)

        # Stats
        pct_replaced = result.replaced / result.total_tokens * 100 if result.total_tokens else 0
        col_a, col_b, col_c = st.columns(3)
        with col_a:
            st.metric("Words replaced", result.replaced)
        with col_b:
            st.metric("Total tokens", result.total_tokens)
        with col_c:
            st.metric("Actual rate", f"{pct_replaced:.1f}%")

        st.divider()

        # Side-by-side comparison
        st.markdown("#### Side-by-side comparison")
        col_orig, col_jabber = st.columns(2)
        with col_orig:
            st.markdown("**Original**")
            st.markdown(
                f"<div style='background:var(--background-color, #f8f8f8);"
                f"border-radius:8px;padding:12px;font-size:14px;line-height:1.6'>"
                f"{text}</div>",
                unsafe_allow_html=True,
            )
        with col_jabber:
            st.markdown("**Jabberwocky**")
            st.markdown(
                f"<div style='background:var(--background-color, #f8f8f8);"
                f"border-radius:8px;padding:12px;font-size:14px;line-height:1.6'>"
                f"{result.text}</div>",
                unsafe_allow_html=True,
            )

# ----------------------------
# Footer
# ----------------------------
st.divider()
st.markdown(
    "<div style='text-align:center;font-size:12px;color:gray'>"
    "Jabberwocky — MODAL HSS project, École Polytechnique · "
    "Inspired by Lewis Carroll's poem (1871)"
    "</div>",
    unsafe_allow_html=True,
)