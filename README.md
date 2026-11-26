<p align="center">
  <a href="https://github.com/bishnt/manimater">
    <img src="assets/banner.svg" alt="manimater-components: the open source component library" width="100%">
  </a>
</p>

<p align="center">
  <b>Open-source, tested, reusable animation components for <a href="https://www.manim.community/">Manim</a>.</b><br>
  The <b>open source library</b> behind <a href="https://github.com/bishnt/manimater">Manimater</a>, and the part we want the world to build on.
</p>

<p align="center">
  <a href="LICENSE"><img alt="License: MIT" src="https://img.shields.io/badge/license-MIT-000000?style=flat-square&labelColor=000000"></a>
  <a href="CONTRIBUTING.md"><img alt="Contributions welcome" src="https://img.shields.io/badge/contributions-welcome-ffffff?style=flat-square&labelColor=000000&color=ffffff"></a>
</p>

<p align="center">
  <a href="#quick-start">Quick start</a> ·
  <a href="CONTRIBUTING.md">Contribute</a> ·
  <a href="docs/WRITING_A_COMPONENT.md">Write a component</a> ·
  <a href="catalog.json">Catalog</a> ·
  <a href="https://github.com/bishnt/manimater">Manimater</a>
</p>

---

# manimater-components

Components across many subjects: electrical and power systems, control and signals, microelectronics, machine learning,
computer science, finance, physics, chemistry, databases and more. Each is written once, tested, and driven by plain JSON.

Manimater turns a prompt into a narrated explainer video. This library is what makes that possible, and it is open source
(MIT) so that anyone can use it, extend it and ship their own videos with it.

```jsonc
// A component is a name plus parameters. No animation code.
{ "component": "synchronous_motor", "params": { "poles": 2, "frequency_hz": 50 } }
```

<table>
  <tr>
    <td width="33%" align="center"><img src="assets/gifs/synchronous_motor.gif" alt="synchronous motor component" width="100%"><br><sub><code>synchronous_motor</code><br>electrical</sub></td>
    <td width="33%" align="center"><img src="assets/gifs/cpu_pipeline.gif" alt="cpu pipeline component" width="100%"><br><sub><code>cpu_pipeline</code><br>microelectronics</sub></td>
    <td width="33%" align="center"><img src="assets/gifs/neural_network.gif" alt="neural network component" width="100%"><br><sub><code>neural_network</code><br>machine learning</sub></td>
  </tr>
  <tr>
    <td width="33%" align="center"><img src="assets/gifs/pid_response.gif" alt="pid response component" width="100%"><br><sub><code>pid_response</code><br>control systems</sub></td>
    <td width="33%" align="center"><img src="assets/gifs/binary_search_tree.gif" alt="binary search tree component" width="100%"><br><sub><code>binary_search_tree</code><br>computer science</sub></td>
    <td width="33%" align="center"><img src="assets/gifs/order_book_matching.gif" alt="order book matching component" width="100%"><br><sub><code>order_book_matching</code><br>finance</sub></td>
  </tr>
</table>

<p align="center"><sub>Six of the components, rendered from their own <code>example</code> parameters with <code>python -m manimate.preview</code>.</sub></p>

## Why components

- **No generated code.** An LLM (or you) only picks a component and fills in its parameters as JSON. `manimate.storyboard`
  validates every value against the catalog before anything runs, so nothing arbitrary is executed.
- **Tested.** Every component has an `example` that must render, and CI dry-runs all of them against a real Manim scene.
- **Reusable.** Written once, used in every video. Adding a component makes every project that uses the library better.
- **Built on the community.** 27 components draw with open-source Manim plugins, all credited in
  [docs/THIRD_PARTY.md](docs/THIRD_PARTY.md).

## Quick start

```bash
git clone https://github.com/Manimater/manimater-components && cd manimater-components
# Manim needs ffmpeg, Cairo and Pango (https://docs.manim.community/en/stable/installation.html).
pip install -e ".[dev]"
./scripts/install_plugins.sh          # the community Manim packages some components wrap (optional)

manimate-preview --list              # every component
manimate-preview callout             # renders previews/callout.mp4 from the component's own example
manimate-catalog --out catalog.json      # export the component catalog
```

The commands are installed by `pip install`. The module forms
`python -m manimate.preview` and `python -m manimate.catalog` also work.

Use it from Python:

```python
from manimate import registry
from manimate.components import load_all
from manimate.storyboard import validate

load_all()
comp = registry.get("bar_chart")
print(comp.example)                                  # parameters that are known to render

storyboard, errors = validate({"title": "Demo", "scenes": [
    {"component": "bar_chart", "params": comp.example, "narration": "Synchronous speed by pole count."}]})
```

`catalog.json` is the machine-readable list of every component (name, domain, description, parameters, example). Hand it
to an LLM as the menu it picks from.

## Use it with Claude

This repo ships a Claude skill, [`skills/manimater-components`](skills/manimater-components/SKILL.md). It teaches Claude to
pick components from the catalog, write valid storyboards, preview them, and write new components that follow the rules.
In Claude Code it is picked up automatically when you open this repo (`.claude/skills/`). In claude.ai, upload the folder
under Settings, Capabilities, Skills.

## Contribute

New components are the best way to help, and you do not have to code.

- **Developer:** copy [`_template.py`](manimate/components/community/_template.py) into `manimate/components/community/`
  on a branch named `component/<name>` (one component per pull request), see [CONTRIBUTING.md](CONTRIBUTING.md) and
  [docs/WRITING_A_COMPONENT.md](docs/WRITING_A_COMPONENT.md).
- **Not a developer:** describe the animation you want to any LLM, paste the result into a form, and we turn it into a pull
  request for you. Start with [docs/GENERATE_WITH_AN_LLM.md](docs/GENERATE_WITH_AN_LLM.md).

## Layout

| Path | What |
|---|---|
| `manimate/components/` | Component packs (one module per subject). Registers itself with the registry. |
| `manimate/components/community/` | **Your contribution goes here**: one file per component, auto-loaded. |
| `manimate/viz/` | Lower-level 3Blue1Brown-style building blocks: `core`, `ml_advanced`, `microelectronics`, `signals`, `power`, `finance`. |
| `manimate/registry.py`, `ctx.py`, `theme.py` | The `@component` decorator, the per-scene time budget and layout helpers, the colours. |
| `manimate/storyboard.py`, `catalog.py` | Validate JSON against the library; export `catalog.json`. |
| `manimate/preview.py` | Render one component to MP4. |
| `skills/manimater-components/` | The Claude skill. |
| `tests/` | Fast tests plus a dry run of every component. |

## Relationship to Manimater

[Manimater](https://github.com/bishnt/manimater) uses this library to render videos, and the two copies are kept in sync by
CI: a change merged here is proposed to the app as a pull request. A component change made in the app is brought here by hand.
The synced paths and the setup are in [docs/SYNC.md](docs/SYNC.md).

## License

MIT. Each community plugin keeps its own licence: see [docs/THIRD_PARTY.md](docs/THIRD_PARTY.md).

---

<p align="center">
  <a href="https://github.com/bishnt/manimater"><img src="assets/logo.svg" alt="Manimater" width="40"></a><br>
  <sub>Manimater is built on this open source library. The logo and banner in <a href="assets/"><code>assets/</code></a> are the Manimater marks.</sub>
</p>
