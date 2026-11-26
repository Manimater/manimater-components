"""Export the component catalog: ``manimate-catalog --out catalog.json``."""

import argparse
import json
from pathlib import Path

from . import registry
from .components import load_all


def build_catalog() -> list[dict]:
    load_all()
    return [c.to_catalog() for c in registry.all_components()]


def main() -> int:
    """Write the component catalog as JSON."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out",
        type=Path,
        help="Write the catalog to a UTF-8 file with LF line endings.",
    )
    args = parser.parse_args()

    content = json.dumps(build_catalog(), indent=2, ensure_ascii=False)

    if args.out is None:
        print(content)
    else:
        args.out.write_text(
            content + "\n", encoding="utf-8", newline="\n"
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
