from __future__ import annotations


def main() -> None:
    """Entry point for the jabberwocky CLI."""
    import sys
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'scripts'))
    from jabberwocky_text import main as _main
    _main()


def build_bank() -> None:
    """Entry point for the bank builder."""
    import sys
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'scripts'))
    from build_bank_fr import main as _main
    _main()