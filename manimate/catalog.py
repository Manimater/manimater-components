"""Export the component catalog: ``manimate-catalog > catalog.json``."""
from __future__ import annotations

import argparse
import json

from . import registry
from .components import load_all


def build_catalog() -> list[dict]:
    load_all()
    return [c.to_catalog() for c in registry.all_components()]


def main(argv: list[str] | None = None) -> int:
    """Write the component catalog as JSON to standard output, or to ``--out`` as UTF-8/LF."""
    parser = argparse.ArgumentParser(prog="manimate-catalog", description="Export the component catalog as JSON.")
    parser.add_argument("--out", metavar="FILE", help="write UTF-8 JSON with LF line endings to FILE")
    args = parser.parse_args(argv)
    data = build_catalog()
    if args.out:
        with open(args.out, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(data, fh, indent=2, ensure_ascii=False)
            fh.write("\n")
        return 0
    print(json.dumps(data, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
