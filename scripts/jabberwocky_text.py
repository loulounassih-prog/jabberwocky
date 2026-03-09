from __future__ import annotations

import argparse
from pathlib import Path

from jw.bank.loader import load_bank_json
from jw.bank.sampler import BankSampler
from jw.jabber.policy import ReplacementPolicy
from jw.jabber.transform import jabberwockify


def main() -> None:
    p = argparse.ArgumentParser(
        description = "Transforms text into Jabberwocky."
    )
    p.add_argument(
        "--text",
        type=str,
        required=True,
        help = "Input text to transforme"
    )
    p.add_argument(
        "--pct",
        type=float,
        default=0.6,
        help = "Target proportion of tokens to replace (between 0 and 1)"
    )
    p.add_argument(
        "--seed",
        type=int,
        default=0,
        help = "Random seed for reproducible output"
    )
    p.add_argument(
        "--bank",
        type=str,
        default="data/bank_fr.json",
        help = "Path to the pseudo-word JSON file"
    )
    args = p.parse_args()
    if not 0.0 <= args.pct <= 1.0:
        p.error("--pct must be between 0 and 1.")

    bank = load_bank_json(Path(args.bank))

    sampler = BankSampler(bank)

    policy = ReplacementPolicy(pct_replace=args.pct)

    result = jabberwockify(
        args.text,
        sampler=sampler,
        policy=policy,
        seed=args.seed
    )

    print(result.text)
    print(f"\n(replaced={result.replaced}/{result.total_tokens}, pct={args.pct}, seed={args.seed})")


if __name__ == "__main__":
    main()
