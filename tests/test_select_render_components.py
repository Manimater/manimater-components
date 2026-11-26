from types import SimpleNamespace

import pytest

from scripts.select_render_components import (
    SMOKE_COMPONENTS,
    select_components,
)


def component(name, module):
    return SimpleNamespace(
        name=name,
        fn=SimpleNamespace(__module__=module),
    )


COMPONENTS = [
    component("bar_chart", "manimate.components.general"),
    component("function_plot", "manimate.components.general"),
    component("sorting", "manimate.components.algorithms"),
    component("example", "manimate.components.community.example"),
]


def test_core_module_selection():
    assert select_components(
        ["manimate/components/general.py"], COMPONENTS
    ) == ["bar_chart", "function_plot"]


def test_community_module_selection():
    assert select_components(
        ["manimate/components/community/example.py"], COMPONENTS
    ) == ["example"]


@pytest.mark.parametrize("path", [
    "manimate/ctx.py",
    "manimate/theme.py",
    "manimate/registry.py",
    "manimate/viz/layout.py",
])
def test_shared_file_smoke_selection(path):
    assert select_components(
        [path], COMPONENTS
    ) == sorted(SMOKE_COMPONENTS)


def test_combined_changes_without_duplicates():
    assert select_components(
        [
            "manimate/ctx.py",
            "manimate/components/general.py",
            "manimate/components/algorithms.py",
        ],
        COMPONENTS,
    ) == sorted(SMOKE_COMPONENTS | {"sorting"})


@pytest.mark.parametrize("paths", [
    [],
    ["README.md"],
    ["manimate/components/community/deleted.py"],
])
def test_unrelated_or_unregistered_files(paths):
    assert select_components(paths, COMPONENTS) == []
