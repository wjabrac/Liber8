"""Default entrypoint for the LIBR8 CLI."""

from __future__ import annotations

import sys
from typing import Sequence

from src.cli import main as cli_main


def main(argv: Sequence[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv[1:]

    if not argv:
        print("No command provided; showing CLI help.")
        argv = ["--help"]

    try:
        return cli_main(argv)
    except SystemExit as exc:
        code = exc.code
        return code if isinstance(code, int) else 0


if __name__ == "__main__":
    raise SystemExit(main())
