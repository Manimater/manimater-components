"""Export the component catalog: ``manimate-catalog > catalog.json``."""
from __future__ import annotations

import json

from . import registry
from .components import load_all
from .components.community import FAILED


def build_catalog() -> list[dict]:
    load_all()
    if FAILED:
        raise RuntimeError(
            "community components failed to import: "
            + "; ".join(f"{name} ({error})" for name, error in FAILED.items())
        )
    return [c.to_catalog() for c in registry.all_components()]


def main() -> int:
    """Write the component catalog as JSON to standard output."""
    print(json.dumps(build_catalog(), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
