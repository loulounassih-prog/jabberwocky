from __future__ import annotations

from pathlib import Path
from wuggy import WuggyGenerator


PLUGIN = "orthographic_french"
SEEDS = ["table", "maison", "pomme", "manger", "chanson", "rapide"]
N_PER_SEED = 100

OUT_DIR = Path("outputs")
OUT_FILE = OUT_DIR / "pseudowords_fr.txt"

def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    wg = WuggyGenerator()

    # print("Supported official plugins:", wg.supported_official_language_plugin_names)

    wg.download_language_plugin(PLUGIN, auto_download=True)

    wg.load(PLUGIN)

    lines: list[str] = []
    lines.append(f"# plugin={PLUGIN} n_per_seed={N_PER_SEED}\n")

    for seed in SEEDS:
        print(f"\n=== Seed: {seed} ===")
        lines.append(f"\n## seed={seed}\n")

        # generate_classic renvoie une liste de dicts (pseudoword + stats)
        results = wg.generate_classic([seed], ncandidates_per_sequence=N_PER_SEED)

        # On récupère ce qui ressemble à un pseudoword
        count = 0
        for r in results:
            pw = r.get("pseudoword") if isinstance(r, dict) else str(r)
            if not pw:
                continue
            count += 1
            print(pw)
            lines.append(pw + "\n")

        if count == 0:
            print("(!) Aucun pseudo-mot généré pour ce seed (rare).")

    OUT_FILE.write_text("".join(lines), encoding="utf-8")
    print(f"\nSaved -> {OUT_FILE.resolve()}")


if __name__ == "__main__":
    main()
