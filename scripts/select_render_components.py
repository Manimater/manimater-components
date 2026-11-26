"""Select components for CI rendering based on changed source files."""

import sys

SMOKE_COMPONENTS = {
    "title_card",
    "bullet_points",
    "function_plot",
    "bar_chart",
}

SHARED_FILES = {
    "manimate/ctx.py",
    "manimate/theme.py",
    "manimate/registry.py",
}


def select_components(paths, components):
    """Return registered component names affected by changed files."""
    paths = set(paths)
    selected = set()

    if paths & SHARED_FILES or any(
        path.startswith("manimate/viz/") for path in paths
    ):
        selected.update(SMOKE_COMPONENTS)

    modules = {
        path[:-3].replace("/", ".")
        for path in paths
        if path.startswith("manimate/components/")
        and path.endswith(".py")
    }

    for component in components:
        if component.fn.__module__ in modules:
            selected.add(component.name)

    return sorted(selected)


def main():
    from manimate.components import load_all
    from manimate.registry import all_components

    load_all()
    paths = sys.stdin.read().splitlines()
    print(" ".join(select_components(paths, all_components())))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
