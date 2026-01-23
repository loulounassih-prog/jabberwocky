from __future__ import annotations

import argparse
from pathlib import Path

from jw.bank.loader import load_bank_json
from jw.bank.sampler import BankSampler
from jw.jabber.policy import ReplacementPolicy
from jw.jabber.transform import jabberwockify


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--text", type=str, required=True)
    p.add_argument("--pct", type=float, default=0.6)
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--bank", type=str, default="data/bank_fr.json")
    args = p.parse_args()

    bank = load_bank_json(Path(args.bank))
    sampler = BankSampler(bank)
    policy = ReplacementPolicy(pct_replace=args.pct)

    res = jabberwockify(args.text, sampler=sampler, policy=policy, seed=args.seed)

    print(res.text)
    print(f"\n(replaced={res.replaced}/{res.total_tokens}, pct={args.pct}, seed={args.seed})")


if __name__ == "__main__":
    main()
