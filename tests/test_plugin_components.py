"""Components that wrap community Manim plugins (physics, ml, datastructures, chemistry packs).

The algorithm helpers are plain Python and always tested. The plugin-backed components run only where the plugin is
installed (``scripts/install_plugins.sh``): each one is executed against a real Scene in dry-run mode, followed by the
same fade-out the storyboard scene performs, because pymunk state left on a mobject once broke that fade.
"""
from __future__ import annotations

import importlib.util

import pytest

from manimate import registry
from manimate.components import load_all
from manimate.components.chemistry import (
    _plugin_safe, formula_counts, parse_equation, shell_counts, side_totals,
)
from manimate.components.circuits import _elements_ok as _circuit_ok, _slots, parse_elements
from manimate.components.databases import _cell, _ops_ok, _split_row
from manimate.components.datastructures import (
    build_bst, parse_edges, parse_stack_ops, sort_steps, traversal_order, walk,
)

load_all()

PLUGIN_COMPONENTS = {
    "manim_physics": ["electric_field", "standing_wave", "pendulum", "falling_objects", "lens_rays"],
    "manim_ml": ["neural_network"],
    "manim_dsa": ["array_sort", "stack_operations", "graph_traversal", "binary_search_tree"],
    "manim_chemistry": ["bohr_atom", "molecule_structure", "chemical_equation"],
    "manim_databases": ["database_table", "btree_index"],
    "manim_eng": ["circuit_diagram"],
}


def _apply(values, ops):
    a = list(values)
    for kind, i, j in ops:
        if kind == "swap":
            a[i], a[j] = a[j], a[i]
    return a


@pytest.mark.parametrize("algorithm", ["bubble", "selection", "insertion"])
@pytest.mark.parametrize("values", [[5, 2, 8, 1, 9], [1, 2, 3], [9, 8, 7, 6, 5, 4, 3, 2], [4, 4, 1], [2, 1]])
def test_sort_steps_sort_the_array(values, algorithm):
    assert _apply(values, sort_steps(values, algorithm)) == sorted(values)


def test_stack_ops_parse_and_reject():
    assert parse_stack_ops(["push 3", "PUSH -4", "pop"]) == [("push", 3), ("push", -4), ("pop", None)]
    with pytest.raises(ValueError):
        parse_stack_ops(["push"])
    comp = registry.get("stack_operations")
    assert comp.params["operations"].validator(["pop"]) == "cannot pop from an empty stack"
    assert comp.params["operations"].validator(["push 1", "pop"]) is None


def test_traversals():
    adj = parse_edges(["A-B", "A-C", "B-D", "C-D", "D-E"])
    assert [n for n, _ in traversal_order(adj, "A", "bfs")] == ["A", "B", "C", "D", "E"]
    assert [n for n, _ in traversal_order(adj, "A", "dfs")] == ["A", "B", "D", "C", "E"]
    # every node except the start is reached from a node that was already visited
    order = traversal_order(adj, "A", "bfs")
    seen = {order[0][0]}
    for node, parent in order[1:]:
        assert parent in seen
        seen.add(node)


def test_bst_walks():
    root = build_bst([8, 3, 10, 1, 6, 14])
    assert walk(root, "inorder") == [1, 3, 6, 8, 10, 14]
    assert walk(root, "preorder") == [8, 3, 1, 6, 10, 14]
    assert walk(root, "postorder") == [1, 6, 3, 14, 10, 8]


def test_typing_override_is_backported_for_manim_dsa():
    # manim-dsa 0.4.0 imports typing.override (Python 3.12+); the renderer image runs 3.11, where this once made every
    # data-structure component fall back to a callout
    import typing

    from manimate.components._plugin import _backport_typing

    _backport_typing()
    assert hasattr(typing, "override")


def test_shell_counts():
    assert shell_counts(1) == [1]
    assert shell_counts(11) == [2, 8, 1]
    assert shell_counts(17) == [2, 8, 7]
    assert shell_counts(18) == [2, 8, 8]


def test_formula_counts_handle_parentheses_and_repeats():
    assert dict(formula_counts("Ca(OH)2")) == {"Ca": 1, "O": 2, "H": 2}
    assert dict(formula_counts("CH3COOH")) == {"C": 2, "H": 4, "O": 2}
    assert dict(formula_counts("Al2(SO4)3")) == {"Al": 2, "S": 3, "O": 12}
    for bad in ["Xx2", "(OH", "OH)", "h2o"]:
        with pytest.raises(ValueError):
            formula_counts(bad)


def test_plugin_formula_only_when_it_renders_faithfully():
    # manim-chemistry's ChemicalFormula turns Ca(OH)2 into "CaO" and CH3COOH into "CHO", so those must not use it
    assert _plugin_safe("H2O") and _plugin_safe("C6H12O6") and _plugin_safe("NaCl")
    assert not _plugin_safe("Ca(OH)2") and not _plugin_safe("CH3COOH")


def test_equation_balance_check():
    left, right = parse_equation("2H2 + O2 -> 2H2O")
    assert side_totals(left) == side_totals(right)
    left, right = parse_equation("H2 + O2 -> H2O")
    assert side_totals(left) != side_totals(right)
    left, right = parse_equation("Ca(OH)2 + 2HCl = CaCl2 + 2H2O")
    assert side_totals(left) == side_totals(right)
    for bad in ["H2 + O2", "H2 -> -> O2", "H2 + -> O2", "2 -> H2", "Zz + O2 -> ZzO2"]:
        with pytest.raises(ValueError):
            parse_equation(bad)


def test_database_operations_and_cells():
    assert _split_row("3, carol, shipped, 200") == [3, "carol", "shipped", 200]
    assert _cell(" -4 ") == -4 and _cell("4.5") == "4.5"
    assert _ops_ok(["insert 3, carol", "update row 2 status shipped", "delete row 1", "select row 2"]) is None
    assert _ops_ok(["drop table"]) is not None
    assert _ops_ok(["delete row 1"] * 6) is not None


def test_circuit_elements_parse_and_reject():
    assert parse_elements(["cell:12 V", "Battery", "resistor : R_1", "closed_switch:S"]) == [
        ("cell", "12 V"), ("cell", ""), ("resistor", "R_1"), ("closed_switch", "S")]
    assert _circuit_ok(["cell:9 V", "resistor:R = 10 Ω"]) is None
    assert _circuit_ok([]) is not None and _circuit_ok(["resistor"] * 7) is not None
    assert "unknown element type" in _circuit_ok(["lamp:L"])


def test_circuit_labels_cannot_carry_latex_commands():
    # labels are typeset by LaTeX, so anything that could be a command (or read a file) must be refused
    for bad in [r"resistor:\input{/etc/passwd}", r"resistor:\write18{x}", "resistor:R{1}", "resistor:$x$", "resistor:" + "R" * 15]:
        assert _circuit_ok(["cell", bad]) is not None, bad
    assert registry.get("circuit_diagram").params["current"].validator(r"\input{x}") is not None


def test_circuit_slots_cover_every_loop_size():
    for n in range(1, 7):
        slots = _slots(n)
        assert len(slots) == n and len({(round(x, 1), round(y, 1)) for x, y, _ in slots}) == n


def test_parameter_validators_reject_bad_values():
    assert registry.get("electric_field").params["charges"].validator([0, 1]) is not None
    assert registry.get("electric_field").params["charges"].validator([1, -1]) is None
    assert registry.get("neural_network").params["layers"].validator([3]) is not None
    assert registry.get("neural_network").params["layers"].validator([3, 9]) is not None
    assert registry.get("binary_search_tree").params["values"].validator([1, 1, 2]) is not None
    assert registry.get("graph_traversal").params["edges"].validator(["A-A"]) is not None
    assert registry.get("pendulum").params["angle_degrees"].validator(120) is not None
    assert registry.get("btree_index").params["keys"].validator([1, 2]) is not None
    assert registry.get("database_table").params["columns"].validator(["id"]) is not None
    assert registry.get("chemical_equation").params["equation"].validator("H2 + O2") is not None
    assert registry.get("chemical_equation").params["equation"].validator("2H2 + O2 -> 2H2O") is None


def _cases() -> list:
    return [pytest.param(module, name, id=name) for module, names in PLUGIN_COMPONENTS.items() for name in names]


@pytest.mark.parametrize("module,name", _cases())
def test_component_runs_and_fades_out(module, name):
    if importlib.util.find_spec(module) is None:
        pytest.skip(f"{module} is not installed")
    from manim import FadeOut, Scene, tempconfig
    from manimate.ctx import Ctx

    comp = registry.get(name)
    with tempconfig({"dry_run": True, "disable_caching": True, "verbosity": "ERROR", "progress_bar": "none",
                     "write_to_movie": False}):
        scene = Scene()
        ctx = Ctx(scene, 6.0)
        comp.fn(ctx, **comp.example)
        if ctx.overrun > 0.05:
            import warnings
            warnings.warn(
                f"{comp.name} exceeded its {ctx.duration:.2f}s budget "
                f"by {ctx.overrun:.2f}s",
                RuntimeWarning,
            )
        scene.play(*[FadeOut(m) for m in scene.mobjects], run_time=0.5)  # what storyboard scenes do after a component
