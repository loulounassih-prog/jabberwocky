from __future__ import annotations


def main() -> None:
    """Entry point for the jabberwocky CLI."""
    from jw._scripts.jabberwocky_text import main as _main
    _main()


def build_bank() -> None:
    """Entry point for the bank builder."""
    from jw._scripts.build_bank_fr import main as _main
    _main()