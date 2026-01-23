from __future__ import annotations

# Minimal mock pseudo-lexicon (expanded).
# Goal: enough diversity per bucket to test the full Jabberwocky pipeline
# without depending on Wuggy yet.

MOCK_BANK = {
    # -------------------------
    # NOUNS
    # -------------------------
    ("NOUN", "Sing", "vowel"): [
        "alune", "ébrume", "orave", "ivelle", "aurine", "éclame", "obine", "ulisse",
        "aroude", "élanve", "ondule", "avrine", "érablet", "ozanne", "urcelle",
    ],
    ("NOUN", "Sing", "cons"): [
        "flane", "brinot", "trupel", "gronde", "plorin", "cravon", "dribel", "fruste",
        "clapon", "brumet", "trancel", "pradone", "glavre", "triquel", "brandel",
    ],
    ("NOUN", "Plur", "vowel"): [
        "alunes", "ébrumes", "oraves", "ivelles", "aurines", "éclames", "obines", "ulisses",
        "aroudes", "élanves", "ondures", "avrines", "érablets", "ozannes", "urcelles",
    ],
    ("NOUN", "Plur", "cons"): [
        "flanes", "brinots", "trupels", "grondes", "plorins", "cravons", "dribels", "frustes",
        "clapons", "brumets", "trancels", "pradones", "glavres", "triquels", "brandels",
    ],

    # -------------------------
    # ADJECTIVES (very naive; just for replacement tests)
    # -------------------------
    ("ADJ", "Sing", "vowel"): [
        "azide", "élune", "obral", "aurif", "écrin", "ivane", "onduleux", "urtil",
        "avide", "ébrin", "orif", "ultral", "arideux", "élif", "ozif",
    ],
    ("ADJ", "Sing", "cons"): [
        "grival", "trusque", "plorin", "crifal", "brusque", "drivel", "frugal", "claron",
        "brandif", "tranchel", "glavreux", "prustal", "brindeux", "cravif", "trivel",
    ],
    ("ADJ", "Plur", "vowel"): [
        "azides", "élunes", "obrals", "aurifs", "écrins", "ivanes", "onduleux", "urtils",
        "avides", "ébrins", "orifs", "ultrals", "arideux", "élifs", "ozifs",
    ],
    ("ADJ", "Plur", "cons"): [
        "grivals", "trusques", "plorins", "crifals", "brusques", "drivels", "frugals", "clarons",
        "brandifs", "tranchels", "glavreux", "prustals", "brindeux", "cravifs", "trivels",
    ],

    # -------------------------
    # VERBS (surface forms only, v1)
    # -------------------------
    ("VERB", None, None): [
        "trame", "plonde", "grente", "bronde", "fronde", "crave", "drible", "glave",
        "pruste", "brandit", "tranche", "clapone", "brume", "triquette", "grondit",
    ],

    # -------------------------
    # ADVERBS (invariable, v1)
    # -------------------------
    ("ADV", None, None): [
        "viteau", "doucemental", "brusquementif", "calmementou", "franchementil",
        "rapidementin", "lentementar", "clairemento", "sombrementa", "fortementu",
        "doucillement", "gravementor", "souplementi", "sûrementa", "tardivement",
    ],
}
