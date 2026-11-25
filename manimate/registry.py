"""Component registry: one declaration drives validation, the LLM catalog, and docs."""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Callable

from .plugins import PLUGINS

PARAM_TYPES = {"string", "number", "integer", "boolean", "string[]", "number[]", "object[]"}
MAX_STRING = 300
MAX_LIST = 8


@dataclass
class Param:
    type: str
    description: str
    required: bool = False
    default: Any = None
    choices: list | None = None
    item_hint: str | None = None  # describes object[] items for the LLM
    validator: Callable[[Any], str | None] | None = None  # returns an error message or None

    def __post_init__(self):
        if self.type not in PARAM_TYPES:
            raise ValueError(f"unknown param type {self.type!r}")

    def to_catalog(self) -> dict:
        out: dict[str, Any] = {"type": self.type, "required": self.required, "description": self.description}
        if self.default is not None:
            out["default"] = self.default
        if self.choices:
            out["choices"] = self.choices
        if self.item_hint:
            out["items"] = self.item_hint
        return out


@dataclass
class Component:
    name: str
    description: str
    domain: str
    params: dict[str, Param]
    example: dict[str, Any]
    fn: Callable
    plugin: str | None = None  # a key of plugins.PLUGINS when the component draws with a community Manim plugin

    validator: Callable[[dict[str, Any]], str | None] | None = None

    def to_catalog(self) -> dict:
        entry = {
            "name": self.name,
            "domain": self.domain,
            "description": self.description,
            "params": {k: p.to_catalog() for k, p in self.params.items()},
            "example": self.example,
        }
        if self.plugin:
            entry["plugin"] = PLUGINS[self.plugin].to_catalog()
        return entry


_REGISTRY: dict[str, Component] = {}


def component(name: str, description: str, params: dict[str, Param], example: dict[str, Any], domain: str = "general",
              plugin: str | None = None,
              validator: Callable[[dict[str, Any]], str | None] | None = None):
    """Register a function ``fn(ctx, **params)`` as a storyboard component.

    ``plugin`` names the community Manim plugin it wraps (a key of ``plugins.PLUGINS``), so the catalog and the website
    can credit it.
    """
    if plugin is not None and plugin not in PLUGINS:
        raise ValueError(f"component {name!r} names unknown plugin {plugin!r}; add it to manimate/plugins.py")

    def deco(fn: Callable) -> Callable:
        if name in _REGISTRY:
            raise ValueError(f"duplicate component {name!r}")
        _REGISTRY[name] = Component(name, description, domain, params, example, fn, plugin, validator)
        return fn

    return deco


def get(name: str) -> Component | None:
    return _REGISTRY.get(name)


def all_components() -> list[Component]:
    return sorted(_REGISTRY.values(), key=lambda c: (c.domain != "general", c.domain, c.name))


def _is_number(v: Any) -> bool:
    if isinstance(v, bool):
        return False
    if isinstance(v, int):
        return True
    return isinstance(v, float) and math.isfinite(v)


def _is_integer(v: Any) -> bool:
    return _is_number(v) and (
        isinstance(v, int) or v.is_integer()
    )


def _check_type(ptype: str, v: Any) -> str | None:
    if ptype == "string":
        if not isinstance(v, str):
            return "must be a string"
        if len(v) > MAX_STRING:
            return f"too long (max {MAX_STRING} chars)"
    elif ptype == "number":
        if not _is_number(v):
            return "must be a number"
    elif ptype == "integer":
        if not _is_integer(v):
            return "must be an integer"
    elif ptype == "boolean":
        if not isinstance(v, bool):
            return "must be true or false"
    elif ptype in ("string[]", "number[]", "object[]"):
        if not isinstance(v, list):
            return "must be a list"
        if len(v) > MAX_LIST:
            return f"too many items (max {MAX_LIST})"
        want = {"string[]": lambda x: isinstance(x, str) and len(x) <= MAX_STRING,
                "number[]": _is_number,
                "object[]": lambda x: isinstance(x, dict)}[ptype]
        if not all(want(x) for x in v):
            return f"items must all be of type {ptype[:-2]}"
    return None


def validate_params(comp: Component, params: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    """Return (clean_params, errors). Unknown params are dropped; defaults are applied."""
    errors: list[str] = []
    clean: dict[str, Any] = {}
    for key, spec in comp.params.items():
        if key not in params or params[key] is None:
            if spec.required:
                errors.append(f"missing required param '{key}'")
            elif spec.default is not None:
                clean[key] = spec.default
            continue
        v = params[key]
        if spec.type == "integer" and _is_integer(v):
            v = int(v)
        err = _check_type(spec.type, v)
        if err is None and spec.choices is not None and v not in spec.choices:
            err = f"must be one of {spec.choices}"
        if err is None and spec.validator is not None:
            err = spec.validator(v)
        if err:
            errors.append(f"param '{key}' {err}")
        else:
            clean[key] = v
    if not errors and comp.validator is not None:
        err = comp.validator(clean)
        if err:
            errors.append(err)

    return clean, errors
