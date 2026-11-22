# Contributing

Thank you for helping. The most valuable thing you can add is a **new component**: one reusable animation that explains
one idea. There are three ways to contribute, from "I have an idea" to "I am a developer".

| You are... | Do this |
|---|---|
| Not a programmer, with an idea for an animation | Follow [docs/GENERATE_WITH_AN_LLM.md](docs/GENERATE_WITH_AN_LLM.md), then open the **New component (from an LLM)** issue. A bot turns it into a pull request for you, and maintainers help from there. |
| Comfortable with Python | Fork, add one file to `manimate/components/community/`, open a pull request. See below. |
| Someone who found a bug or a gap | Open an issue: **Bug report** or **Component request**. |

AI-assisted contributions are welcome. You are responsible for what you submit: run it, look at the video, and read
the checklist below before you send it.

## Add a component as a developer

```bash
git clone https://github.com/<you>/manimater-components && cd manimater-components
pip install -e ".[dev]"            # needs ffmpeg, Cairo and Pango for Manim
./scripts/install_plugins.sh       # optional: only if your component wraps a community plugin

cp manimate/components/community/_template.py manimate/components/community/my_component.py
# edit it, then:
manimate-preview my_component                 # watch it: previews/my_component.mp4
python -m pytest                               # includes a dry run of every component
manimate-catalog > catalog.json                # regenerate the catalog (CI checks it)
```

The short commands are installed by `pip install`. You can also use
`python -m manimate.preview` and `python -m manimate.catalog`, including in CI.

Then open a pull request. A good pull request answers five questions in its description (the template asks them):

1. **Teaches**: the one thing the viewer understands afterwards.
2. **Params**: names, types, ranges, defaults.
3. **Layout**: what sits where on the stage.
4. **Beats**: the animation in order, with rough seconds.
5. **Failure cases**: what happens with too many items, empty input, very long labels.

### The checklist

- [ ] One idea per component. If the description needs the word "and" twice, split it.
- [ ] At most 5 parameters, each with a default or clearly required, and a plain-English error for bad values.
- [ ] `example` renders (preview it) and the dry-run test passes.
- [ ] Only `theme` colours; text stays on the stage (`ctx.fit`) and is short and plain.
- [ ] The animation uses the time it is given (`ctx.remaining`, `Ctx.beat`) and fades in as a whole.
- [ ] Any algorithm, formula or layout is a plain Python function with a unit test, not buried in drawing code.
- [ ] No network, files, processes, or `eval`/`exec`. If you wrap a Manim plugin, it must be MIT (or CC) licensed and
      you add it to `manimate/plugins.py`, `scripts/install_plugins.sh` and `docs/THIRD_PARTY.md`.
- [ ] `catalog.json` regenerated.

Full guide: [docs/WRITING_A_COMPONENT.md](docs/WRITING_A_COMPONENT.md). The design rules in
[manimate/components/README.md](manimate/components/README.md) apply to every component.

## Contribute without coding

1. Open [docs/GENERATE_WITH_AN_LLM.md](docs/GENERATE_WITH_AN_LLM.md) and copy the prompt into Claude, ChatGPT, Gemini
   or any LLM. Describe the animation you want in plain words.
2. The LLM gives you one block of Python code. Optionally, run the preview command it gives you.
3. Open the **New component (from an LLM)** issue form and paste the code in. That's it.

A bot checks your code (it never runs it), opens a pull request, and CI renders and tests it. A maintainer reviews it and
may ask you, or the LLM, for changes. You keep credit: your GitHub name is on the commit.

## How your contribution reaches Manimater

When a pull request is merged here, CI opens a pull request in [Manimater](https://github.com/bishnt/manimater) with the
same change, so the app and this library never drift.

## Licence

By contributing you agree your work is released under the [MIT licence](LICENSE).
