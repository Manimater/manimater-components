"""Community components: add one file to this folder and it is registered.

Every module here whose name does not start with an underscore is imported by ``load_all()``, so a contribution is a
single ``<your_component>.py`` file (plus a test). Start from ``_template.py``. See ``docs/WRITING_A_COMPONENT.md``.
"""
from __future__ import annotations

import importlib
import logging
import pkgutil

# Module name -> "ExceptionType: message" for community files that failed to import.
FAILED: dict[str, str] = {}
_log = logging.getLogger(__name__)


def load() -> None:
    """Import every non-underscore module, recording failures instead of stopping.

    One broken third-party file must not take the rest of the library down. The
    catalog and the tests check ``FAILED`` so CI still fails loudly.
    """
    for mod in sorted(m.name for m in pkgutil.iter_modules(__path__)):
        if mod.startswith("_"):
            continue
        try:
            importlib.import_module(f"{__name__}.{mod}")
        except Exception as exc:  # noqa: BLE001 - isolate one contribution from the rest
            FAILED[mod] = f"{type(exc).__name__}: {exc}"
            _log.warning("community component %s failed to import: %s", mod, FAILED[mod])
