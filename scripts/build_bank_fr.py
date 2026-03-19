from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Dict, List, Tuple

from wuggy import WuggyGenerator

PLUGIN = "orthographic_french"

# Seeds simples, fiables (pas d'accents) pour démarrer.
# Plus tard, on remplacera par des seeds extraites de Lexique382.
SEEDS = {
    "NOUN": [
        "table", "maison", "camion", "chanson", "pierre", "jardin", "arbre", "école", "orage",
        "livre", "porte", "fenêtre", "route", "ville", "pays", "monde", "temps", "vie", "main",
        "tête", "eau", "feu", "terre", "ciel", "nuit", "jour", "an", "enfant", "femme", "homme",
        "chat", "chien", "oiseau", "fleur", "soleil", "lune", "étoile", "mer", "montagne", "forêt",
        "bureau", "chaise", "lampe", "mur", "sol", "toit", "escalier", "couloir", "cuisine", "chambre",
        "voiture", "train", "avion", "bateau", "vélo", "rue", "pont", "gare", "marché", "place",
        "travail", "projet", "idée", "question", "réponse", "histoire", "image", "son", "lettre", "mot",
        "couleur", "forme", "taille", "poids", "vitesse", "force", "chaleur", "lumière", "bruit", "odeur",
        "famille", "ami", "voisin", "médecin", "professeur", "élève", "patron", "collègue", "client", "chef",
        "repas", "pain", "fruit", "légume", "viande", "poisson", "fromage", "vin", "café", "sucre",
        "printemps", "été", "automne", "hiver", "matin", "soir", "semaine", "mois", "siècle", "instant",
        "problème", "solution", "résultat", "effet", "cause", "raison", "but", "moyen", "étape", "fin",
        "animal", "plante", "roche", "sable", "vague", "nuage", "vent", "pluie", "neige", "glace",
        "roman", "poème", "chanson", "tableau", "sculpture", "film", "pièce", "concert", "spectacle", "musée",
        "santé", "maladie", "douleur", "soin", "médicament", "hôpital", "opération", "guérison", "repos", "sport",
    ],
    "ADJ": [
        "rapide", "petit", "grand", "calme", "triste", "joli", "étrange", "ancien", "utile",
        "beau", "bon", "mauvais", "fort", "faible", "long", "court", "haut", "bas", "large", "étroit",
        "chaud", "froid", "doux", "dur", "lisse", "rugueux", "léger", "lourd", "vide", "plein",
        "jeune", "vieux", "nouveau", "premier", "dernier", "seul", "même", "autre", "tel", "quel",
        "simple", "complexe", "facile", "difficile", "possible", "impossible", "certain", "probable", "rare", "commun",
        "rouge", "bleu", "vert", "jaune", "blanc", "noir", "gris", "brun", "rose", "violet",
        "heureux", "malheureux", "content", "fâché", "surpris", "effrayé", "courageux", "timide", "généreux", "avare",
        "intelligent", "stupide", "sage", "fou", "sincère", "faux", "loyal", "traître", "poli", "impoli",
        "propre", "sale", "frais", "pourri", "vivant", "mort", "naturel", "artificiel", "sauvage", "domestique",
        "public", "privé", "national", "local", "urbain", "rural", "moderne", "traditionnel", "officiel", "secret",
        "important", "insignifiant", "urgent", "prioritaire", "nécessaire", "inutile", "suffisant", "insuffisant", "exact", "approximatif",
        "profond", "superficiel", "global", "partiel", "total", "nul", "unique", "multiple", "principal", "secondaire",
        "normal", "bizarre", "habituel", "exceptionnel", "ordinaire", "extraordinaire", "réel", "fictif", "actuel", "futur",
        "rapide", "lent", "violent", "pacifique", "brutal", "délicat", "grossier", "raffiné", "vulgaire", "élégant",
        "sombre", "lumineux", "brillant", "terne", "transparent", "opaque", "solide", "liquide", "gazeux", "élastique",
    ],
    "VERB": [
        "mange", "avance", "prend", "regarde", "tombe", "cherche", "arrive", "écoute", "oublie",
        "parle", "marche", "court", "saute", "nage", "vole", "tourne", "glisse", "pousse", "tire",
        "ouvre", "ferme", "monte", "descend", "entre", "sort", "passe", "reste", "part", "revient",
        "dit", "crie", "chante", "rit", "pleure", "pense", "rêve", "comprend", "apprend", "sait",
        "aime", "déteste", "veut", "peut", "doit", "fait", "donne", "prend", "garde", "perd",
        "commence", "finit", "continue", "arrête", "change", "grandit", "diminue", "augmente", "améliore", "détruit",
        "construit", "crée", "invente", "découvre", "observe", "analyse", "compare", "mesure", "calcule", "résout",
        "aide", "protège", "défend", "attaque", "blesse", "soigne", "sauve", "tue", "vit", "meurt",
        "mange", "boit", "dort", "se réveille", "respire", "bouge", "touche", "sent", "voit", "entend",
        "travaille", "joue", "lit", "écrit", "dessine", "peint", "choisit", "décide", "accepte", "refuse",
        "demande", "répond", "explique", "montre", "cache", "cherche", "trouve", "perd", "récupère", "range",
        "prépare", "cuisine", "nettoie", "répare", "fabrique", "assemble", "installe", "utilise", "manipule", "transporte",
        "voyage", "visite", "explore", "retourne", "s'approche", "s'éloigne", "suit", "précède", "accompagne", "guide",
        "réussit", "échoue", "essaie", "renonce", "persiste", "hésite", "doute", "croit", "espère", "craint",
        "appelle", "invite", "accueille", "présente", "rencontre", "salue", "remercie", "excuse", "félicite", "console",
    ],
    "ADV": [
        "vite", "hier", "souvent", "bien", "encore", "toujours", "ailleurs", "ensemble", "ici",
        "là", "tôt", "tard", "avant", "après", "maintenant", "jamais", "parfois", "souvent", "rarement",
        "très", "assez", "trop", "peu", "beaucoup", "plutôt", "vraiment", "presque", "environ", "seulement",
        "ainsi", "donc", "pourtant", "cependant", "néanmoins", "toutefois", "certes", "effectivement", "évidemment", "apparemment",
        "lentement", "rapidement", "doucement", "fortement", "légèrement", "profondément", "simplement", "clairement", "précisément", "exactement",
        "complètement", "partiellement", "totalement", "nullement", "absolument", "relativement", "particulièrement", "généralement", "habituellement", "normalement",
        "haut", "bas", "loin", "près", "dedans", "dehors", "dessus", "dessous", "devant", "derrière",
        "volontiers", "soudain", "brusquement", "progressivement", "finalement", "heureusement", "malheureusement", "curieusement", "bizarrement", "étrangement",
        "intensément", "patiemment", "courageusement", "tranquillement", "silencieusement", "bruyamment", "délicatement", "brutalement", "tendrement", "froidement",
        "simultanément", "successivement", "alternativement", "mutuellement", "réciproquement", "collectivement", "individuellement", "personnellement", "directement", "indirectement",
        "probablement", "certainement", "assurément", "définitivement", "provisoirement", "temporairement", "spontanément", "intentionnellement", "accidentellement", "naturellement",
        "uniquement", "exclusivement", "principalement", "essentiellement", "fondamentalement", "superficiellement", "globalement", "localement", "officiellement", "secrètement",
        "récemment", "anciennement", "actuellement", "prochainement", "immédiatement", "progressivement", "graduellement", "rapidement", "lentement", "subitement",
        "également", "différemment", "semblablement", "contrairement", "inversement", "parallèlement", "perpendiculairement", "proportionnellement", "approximativement", "précisément",
        "joyeusement", "tristement", "anxieusement", "sereinement", "violemment", "paisiblement", "furieusement", "calmement", "nerveusement", "passionnément",
    ],
}

N_PER_SEED = 10
DEFAULT_MAX_FINAL_PER_POS = 0

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


def _pos_from_row(row: Dict[str, str]) -> str:
    cgram = _pick(row, "cgram", "cgram_ortho", "cgramortho", "pos")
    if not cgram:
        return ""
    return cgram.split(":")[0].upper()


def _is_singular(row: Dict[str, str]) -> bool | None:
    number = _pick(row, "nombre", "number")
    if not number:
        return None
    n = number.strip().lower()
    if n in ("s", "sing", "singulier", "sg", "1"):
        return True
    if n in ("p", "plur", "plural", "pl", "2"):
        return False
    return None


def _normalize_row(row: Dict[str, str]) -> Dict[str, str]:
    return {(k or "").strip().lower(): (v or "").strip() for k, v in row.items()}


def _load_lexique_seeds(path: Path, limits: Dict[str, int]) -> Dict[str, List[str]]:
    candidates: Dict[str, List[Tuple[str, float]]] = {
        "NOUN": [],
        "ADJ": [],
        "ADV": [],
        "VERB": [],
    }

    with path.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f, delimiter="\t")
        if not reader.fieldnames:
            raise ValueError("Lexique TSV: missing header")
        fieldnames = [(n or "").strip().lower() for n in reader.fieldnames]
        has_islem = "islem" in fieldnames

        for row in reader:
            row_norm = _normalize_row(row)
            pos_tag = _pos_from_row(row_norm)
            if pos_tag == "NOM":
                pos = "NOUN"
            elif pos_tag == "ADJ":
                pos = "ADJ"
            elif pos_tag == "ADV":
                pos = "ADV"
            elif pos_tag in ("VER", "VERB"):
                pos = "VERB"
            else:
                continue

            if pos in ("NOUN", "ADJ"):
                sing = _is_singular(row_norm)
                if sing is False:
                    continue

            if pos == "VERB":
                lemma = _pick(row_norm, "lemme", "lemma")
                if not lemma:
                    continue
                if has_islem:
                    if row_norm.get("islem") != "1":
                        continue
                else:
                    ortho = _pick(row_norm, "ortho", "orth", "forme", "form")
                    if ortho and ortho != lemma:
                        continue
                form = lemma
                freq = _parse_float(
                    _pick(
                        row_norm,
                        "freqlemfilms2",
                        "freqlemfilms",
                        "freqlem",
                        "freqlivres",
                        "freqfilms2",
                        "freqfilms",
                        "freq",
                    )
                )
            else:
                form = _pick(row_norm, "ortho", "orth", "forme", "form")
                if not form:
                    form = _pick(row_norm, "lemme", "lemma")
                if not form:
                    continue
                freq = _parse_float(
                    _pick(row_norm, "freqfilms2", "freqfilms", "freqlivres", "freq")
                )

            form = form.strip()
            if not form:
                continue
            candidates[pos].append((form, freq))

    seeds: Dict[str, List[str]] = {}
    for pos, items in candidates.items():
        items.sort(key=lambda x: (-x[1], x[0]))
        seen = set()
        out = []
        limit = limits.get(pos, 0)
        for form, _ in items:
            form_norm = form.casefold()
            if form_norm in seen:
                continue
            seen.add(form_norm)
            out.append(form)
            if limit and len(out) >= limit:
                break
        seeds[pos] = out
    return seeds


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--lexique-tsv", type=str, default="")
    p.add_argument("--n-noun", type=int, default=20)
    p.add_argument("--n-adj", type=int, default=20)
    p.add_argument("--n-adv", type=int, default=20)
    p.add_argument("--n-verb", type=int, default=20)
    args = p.parse_args()

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    if args.lexique_tsv:
        limits = {
            "NOUN": args.n_noun,
            "ADJ": args.n_adj,
            "ADV": args.n_adv,
            "VERB": args.n_verb,
        }
        seeds_by_pos = _load_lexique_seeds(Path(args.lexique_tsv), limits)
    else:
        seeds_by_pos = SEEDS

    wg = WuggyGenerator()
    wg.download_language_plugin(PLUGIN, auto_download=True)
    wg.load(PLUGIN)

    # JSON-friendly structure:
    # bank[pos][number][initial] = list[str]
    bank: Dict[str, Dict[str, Dict[str, List[List[str]]]]] = {
        "NOUN": {"Sing": {"vowel": [], "cons": []}, "Plur": {"vowel": [], "cons": []}},
        "ADJ":  {"Sing": {"vowel": [], "cons": []}, "Plur": {"vowel": [], "cons": []}},
        "VERB": {"_": {"_": []}},  # flat
        "ADV":  {"_": {"_": []}},  # flat
    }

    def add_bucket(pos: str, form: str, gender: str = "Masc") -> None:
        form = form.strip()
        if not form:
            return
        if pos in ("VERB", "ADV"):
            bank[pos]["_"]["_"].append([form, "_"])
            return

        initial = "vowel" if starts_with_vowel_letter(form) else "cons"
        bank[pos]["Sing"][initial].append([form, gender])
        plur = naive_plural(form)
        bank[pos]["Plur"][initial].append([plur, gender])

    avoid = {seed.casefold() for seeds in seeds_by_pos.values() for seed in seeds}

    # Build a gender map from Lexique if available, else empty
    seed_genders: Dict[str, str] = {}
    if args.lexique_tsv:
        with Path(args.lexique_tsv).open(encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f, delimiter="\t")
            for row in reader:
                row_norm = _normalize_row(row)
                ortho = _pick(row_norm, "ortho", "orth", "forme", "form")
                genre = _pick(row_norm, "genre", "gender", "gen")
                if ortho and genre:
                    g = genre.strip().lower()
                    if g in ("m", "mas", "masc", "masculin"):
                        seed_genders[ortho.casefold()] = "Masc"
                    elif g in ("f", "fem", "fém", "feminin", "féminin"):
                        seed_genders[ortho.casefold()] = "Fem"

    for pos, seeds in seeds_by_pos.items():
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

                if pw.casefold() in avoid:
                    continue
                # Inherit gender from the seed word via Lexique when available.
                # If Lexique gives nothing, default to Masc for now.
                gender = seed_genders.get(seed.casefold(), "Masc")
                add_bucket(pos, pw, gender)
                count += 1

            print(f"  generated={count}")

    # Deduplicate while preserving order
    def dedup(lst: List[List[str]]) -> List[List[str]]:
        seen = set()
        out = []
        for entry in lst:
            form = entry[0]
            norm = form.casefold()
            if norm in seen:
                continue
            seen.add(norm)
            out.append(entry)
        return out

    for pos in bank:
        for number in bank[pos]:
            for initial in bank[pos][number]:
                bank[pos][number][initial] = dedup(bank[pos][number][initial])

    OUT_PATH.write_text(json.dumps(bank, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nSaved -> {OUT_PATH.resolve()}")
    print("Counts:")
    print("  NOUN sing vowel:", len(bank["NOUN"]["Sing"]["vowel"]), "cons:", len(bank["NOUN"]["Sing"]["cons"]))
    print("  NOUN plur vowel:", len(bank["NOUN"]["Plur"]["vowel"]), "cons:", len(bank["NOUN"]["Plur"]["cons"]))
    print("  ADJ  sing vowel:", len(bank["ADJ"]["Sing"]["vowel"]), "cons:", len(bank["ADJ"]["Sing"]["cons"]))
    print("  ADJ  plur vowel:", len(bank["ADJ"]["Plur"]["vowel"]), "cons:", len(bank["ADJ"]["Plur"]["cons"]))
    print("  VERB:", len(bank["VERB"]["_"]["_"]))
    print("  ADV :", len(bank["ADV"]["_"]["_"]))


if __name__ == "__main__":
    main()
