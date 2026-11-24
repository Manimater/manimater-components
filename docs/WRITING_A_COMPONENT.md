# Writing a component

A component is a Python function `fn(ctx, **params)` that draws one animation, registered with `@component(...)`. The
registry turns the declaration into validation, the catalog, and docs. Start from
[`_template.py`](../manimate/components/community/_template.py); read a finished one such as `callout` in
`manimate/components/general.py`.

## Anatomy

```python
@component(
    "step_chain",                                  # name: snake_case, unique in the whole library
    "A row of 2-6 labelled steps that light up one after another.",   # what it shows and when to use it (one sentence)
    {                                               # params, at most 5
        "steps": P("string[]", "The step names, in order", required=True, validator=...),
        "title": P("string", "Optional heading", default=""),
    },
    {"steps": ["Plan", "Build", "Test", "Ship"], "title": "A release"},   # example: must render
    domain="general",                               # subject area
)
def step_chain(ctx: Ctx, steps: list[str], title: str = "") -> None:
    ...
```

Parameter types: `string`, `number`, `integer`, `boolean`, `string[]`, `number[]`, `object[]`. Strings are capped at 300
characters and lists at 8 items by the registry. Add a `choices=[...]` list or a `validator` that returns an error message
(or `None`) to be stricter. Describe every parameter well: **an LLM reads these descriptions to decide what to put in them.**

## The `Ctx` object

| Member | Use |
|---|---|
| `ctx.play(*anims, run_time=)` / `ctx.wait(s)` | Play animations and track the time spent. Always use these instead of `scene.play`. |
| `ctx.remaining` | Seconds left in this scene. Spend them: the narration is that long. |
| `Ctx.beat(remaining, n)` | Seconds per reveal when `n` reveals share the remaining time. |
| `ctx.fit(mob)` | Scale down to fit the stage and centre it. Stage is about 12.4 x 5.8 units; the bottom is for the caption. |
| `ctx.heading(text)` | A standard heading. |
| `label(text, size, color, width=)` | Text with word wrap. |

Colours come from `manimate.theme` (`FG`, `MUTED`, `PANEL`, `ACCENT`, `GOOD`, `WARN`, `DANGER`, `YELLOW`, `PURPLE`).
Never write hex colours.

## Rules

1. **One idea per component**, and a description a planner can match to a topic.
2. **Computed, not drawn.** Algorithms, formulas and layouts are plain functions you can unit-test without Manim
   (`binary_search_steps` in `algorithms.py` is the model). The scene only plays the result.
3. **Fade in as a whole.** The finished picture appears with one `FadeIn` (1.2 to 1.5 s), then the parts that carry the meaning animate.
4. **Fill the time** you are given; do not run over it.
5. **Forgiving parameters.** Clamp and trim instead of crashing. Empty lists, huge numbers and very long labels must not break it.
6. **Plain labels**, under 28 characters where possible.
7. **Pure drawing code.** No network, files, subprocesses, `eval` or `exec`.

## Wrapping a Manim plugin

Only MIT (or Creative Commons) licensed plugins. Import the plugin **inside** the function through
`from ._plugin import require` so the library still imports without it, declare it in `manimate/plugins.py`, pin it in
`scripts/install_plugins.sh`, and add a row to [THIRD_PARTY.md](THIRD_PARTY.md). See `physics.py` for an example.

## Branch and pull request

A new component goes on its own branch named `component/<name>` (the same name as the file and the `@component`), one
component per pull request, with the title `feat(community): add <name>`. The branch carries the component, its test
and the regenerated `catalog.json` and docs, and nothing else. CI enforces this; see [CONTRIBUTING.md](../CONTRIBUTING.md).

## Test it

```bash
python -m manimate.preview my_component         # look at it
python -m manimate.preview my_component --params '{"steps": ["a"]}'     # try awkward input
python scripts/check_community.py              # fast static rules (what CI runs first)
python -m pytest tests/community                # generic checks run on every community component
python -m manimate.catalog --out catalog.json && python scripts/gen_docs.py   # CI fails if these are stale
```

Put the logic tests in `tests/community/test_my_component.py`. Test edge cases: empty, one item, the maximum, long labels.
