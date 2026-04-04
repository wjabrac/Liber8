"""Default entrypoint for the LIBR8 CLI."""

from __future__ import annotations

import sys
from typing import Sequence

from src.cli import main as cli_main


def main(argv: Sequence[str] | None = None) -> int:
    if argv is None:
        if len(sys.argv) > 1:
            argv = sys.argv[1:]
        else:
            argv = ["run", "run cognition loop", "--storage-dir", ".storage", "--backend", "fallback"]
    return cli_main(argv)


if __name__ == "__main__":
    raise SystemExit(main())
