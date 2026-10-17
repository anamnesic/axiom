"""Module execution entry point for ``python -m axiom``."""

from __future__ import annotations

import sys
from axiom.cli import main

if __name__ == "__main__":
    sys.exit(main())
