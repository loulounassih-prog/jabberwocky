from __future__ import annotations

import argparse
from pathlib import Path

from jw.bank.loader import load_bank_json
from jw.bank.sampler import BankSampler
from jw.jabber.policy import ReplacementPolicy
from jw.jabber.transform import jabberwockify


def main() -> None:
    p = argparse.ArgumentParser(
        description="Transforms text into Jabberwocky."
    )
    p.add_argument(
        "--text",
        type=str,
        help="Input text to transform (mutually exclusive with --input-file)"
    )
    p.add_argument(
        "--input-file",
        type=str,
        help="Path to a text file to transform"
    )
    p.add_argument(
        "--output-file",
        type=str,
        help="Path to write the output (default: print to stdout)"
    )
    p.add_argument(
        "--pct",
        type=float,
        default=0.6,
        help="Target proportion of tokens to replace (between 0 and 1)"
    )
    p.add_argument(
        "--pct-noun",
        type=float,
        default=None,
        help="Replacement rate for nouns (overrides --pct)"
    )
    p.add_argument(
        "--pct-verb",
        type=float,
        default=None,
        help="Replacement rate for verbs (overrides --pct)"
    )
    p.add_argument(
        "--pct-adj",
        type=float,
        default=None,
        help="Replacement rate for adjectives (overrides --pct)"
    )
    p.add_argument(
        "--pct-adv",
        type=float,
        default=None,
        help="Replacement rate for adverbs (overrides --pct)"
    )
    p.add_argument(
        "--seed",
        type=int,
        default=0,
        help="Random seed for reproducible output"
    )
    p.add_argument(
        "--bank",
        type=str,
        default="data/bank_fr.json",
        help="Path to the pseudo-word JSON file"
    )
    args = p.parse_args()

    if not args.text and not args.input_file:
        p.error("One of --text or --input-file is required.")
    if args.text and args.input_file:
        p.error("--text and --input-file are mutually exclusive.")
    if not 0.0 <= args.pct <= 1.0:
        p.error("--pct must be between 0 and 1.")

    if args.input_file:
        text = Path(args.input_file).read_text(encoding="utf-8")
    else:
        text = args.text

    bank = load_bank_json(Path(args.bank))
    sampler = BankSampler(bank)
    pct_by_pos = {}
    if args.pct_noun is not None:
        pct_by_pos["NOUN"] = args.pct_noun
    if args.pct_verb is not None:
        pct_by_pos["VERB"] = args.pct_verb
    if args.pct_adj is not None:
        pct_by_pos["ADJ"] = args.pct_adj
    if args.pct_adv is not None:
        pct_by_pos["ADV"] = args.pct_adv

    policy = ReplacementPolicy(pct_replace=args.pct, pct_by_pos=pct_by_pos)

    result = jabberwockify(text, sampler=sampler, policy=policy, seed=args.seed)

    output = result.text + f"\n\n(replaced={result.replaced}/{result.total_tokens}, pct={args.pct}, seed={args.seed})"

    if args.output_file:
        Path(args.output_file).write_text(output, encoding="utf-8")
        print(f"Output written to {args.output_file}")
    else:
        print(output)


if __name__ == "__main__":
    main()
