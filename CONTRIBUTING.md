# Contributing

Thank you for helping. The most valuable thing you can add is a **new component**: one reusable animation that explains
one idea. There are three ways to contribute, from "I have an idea" to "I am a developer".

| You are... | Do this |
|---|---|
| Not a programmer, with an idea for an animation | Follow [docs/GENERATE_WITH_AN_LLM.md](docs/GENERATE_WITH_AN_LLM.md), then open the **New component (from an LLM)** issue. A bot turns it into a pull request for you, and maintainers help from there. |
| Comfortable with Python | Fork, push **one component** to a branch named `component/<name>`, open a pull request. See below. |
| Someone who found a bug or a gap | Open an issue: **Bug report** or **Component request**. |

AI-assisted contributions are welcome. You are responsible for what you submit: run it, look at the video, and read
the rules below before you send it.

## The rules (enforced by CI)

This repository is used by services that render videos for other people, so contributions are checked strictly and
automatically. A pull request is not reviewed until **both required checks are green**: **CI passed** and **PR policy**.

1. **A new component always goes on its own branch named `component/<name>`**, where `<name>` is the component's
   snake_case name (`component/binary_heap` for `binary_heap.py`). Branch from an up-to-date `main`.
2. **One component per pull request.** The branch carries that component, its test, and the regenerated catalog and
   docs, and nothing else. Fixes, refactors and other components go in separate pull requests (use `fix/<topic>`,
   `docs/<topic>`, and so on for those; the `component/` prefix is reserved for new components).
3. **The title is a Conventional Commit**: `type(scope): summary`. Types: `feat`, `fix`, `docs`, `chore`, `test`, `ci`,
   `refactor`, `build`, `perf`, `revert`. A new component is `feat(community): add <name> ...`.
4. **A new component comes with tests**: `tests/community/test_<name>.py`, covering the plain-Python logic and the edge
   cases (empty, one item, the maximum, long labels).
5. **Fill in the pull request description.** The template asks the five design questions and has a checklist. Every box
   must be ticked (once it is true) before the check passes.
6. **No generated files left behind.** Run `python -m manimate.catalog --out catalog.json` and `python scripts/gen_docs.py`
   and commit the result. CI regenerates both and fails on any difference.
7. **No binaries, media, secrets or files over 1 MB.** Previews are rendered by CI; do not commit videos. Images for the
   README go in `assets/`.
8. **Only what the safety check allows**: no network, files, processes, `eval`/`exec`, no loading images or SVGs, and
   only the allowed imports (see `manimate/components/community/_safety.py`).

Maintainers can waive a rule for a specific pull request with the `policy-override` label; contributors cannot, so
if a rule is wrong for your change, say so in the description.

## Add a component as a developer

```bash
# 1. Fork on GitHub, then:
git clone https://github.com/<you>/manimater-components && cd manimater-components
git remote add -f upstream https://github.com/Manimater/manimater-components   # -f fetches it, so upstream/main exists
git switch -c component/my_component upstream/main      # the branch name is the rule: component/<name>

# 2. Set up
pip install -e ".[dev]"            # needs ffmpeg, Cairo and Pango for Manim
./scripts/install_plugins.sh       # optional: only if your component wraps a community plugin

# 3. Write it
cp manimate/components/community/_template.py manimate/components/community/my_component.py
cp ...                             # and write tests/community/test_my_component.py
manimate-preview my_component      # watch it: previews/my_component.mp4

# 4. Check it exactly as CI will
python scripts/check_community.py  # fast static rules, nothing is run
python -m pytest                   # includes a dry run of every component
manimate-catalog --out catalog.json && python scripts/gen_docs.py

# 5. Push the component branch and open the pull request
git add manimate/components/community/my_component.py tests/community/test_my_component.py catalog.json docs skills
git commit -m "feat(community): add my_component"
git push -u origin component/my_component
```

The short commands are installed by `pip install`. You can also use `python -m manimate.preview` and
`python -m manimate.catalog`, including in CI.

A good pull request answers five questions in its description (the template asks them, and the check requires them):

1. **Teaches**: the one thing the viewer understands afterwards.
2. **Params**: names, types, ranges, defaults.
3. **Layout**: what sits where on the stage.
4. **Beats**: the animation in order, with rough seconds.
5. **Failure cases**: what happens with too many items, empty input, very long labels.

### What CI runs on your pull request

| Check | What it does |
|---|---|
| **Static checks** | Seconds, nothing installed or run: the safety rules, file layout and naming, one `@component` named like its file, docstring, lint. |
| **Workflow lint** | Validates the workflow files and that every action is pinned to a commit. |
| **Tests (3.11, 3.12)** | The whole test suite, a dry run of every component, and that `catalog.json` and the generated docs are up to date. |
| **Render new and changed components** | Renders a real video of every component you add or change and attaches it to the run (Artifacts, `component-previews`) so reviewers can watch it. |
| **Package builds and installs** | Builds the wheel and imports it from a clean environment. |
| **PR policy** | Branch name, title, description, one component per pull request, file hygiene. |
| **CI passed** | One summary check that is green only when all of the above are. |

If a pull request from a first-time contributor shows "Workflow awaiting approval", a maintainer has to approve the run
once; that is a GitHub safeguard, not a problem with your change.

### The checklist

- [ ] One idea per component. If the description needs the word "and" twice, split it.
- [ ] At most 5 parameters, each with a default or clearly required, and a plain-English error for bad values.
- [ ] `example` renders (preview it) and the dry-run test passes.
- [ ] Only `theme` colours; text stays on the stage (`ctx.fit`) and is short and plain.
- [ ] The animation uses the time it is given (`ctx.remaining`, `Ctx.beat`) and fades in as a whole.
- [ ] Any algorithm, formula or layout is a plain Python function with a unit test, not buried in drawing code.
- [ ] No network, files, processes, or `eval`/`exec`. If you wrap a Manim plugin, it must be MIT (or CC) licensed and
      you add it to `manimate/plugins.py`, `scripts/install_plugins.sh` and `docs/THIRD_PARTY.md`.
- [ ] `catalog.json` and the generated docs regenerated and committed.

Full guide: [docs/WRITING_A_COMPONENT.md](docs/WRITING_A_COMPONENT.md). The design rules in
[manimate/components/README.md](manimate/components/README.md) apply to every component.

## Contribute without coding

1. Open [docs/GENERATE_WITH_AN_LLM.md](docs/GENERATE_WITH_AN_LLM.md) and copy the prompt into Claude, ChatGPT, Gemini
   or any LLM. Describe the animation you want in plain words.
2. The LLM gives you one block of Python code. Optionally, run the preview command it gives you.
3. Open the **New component (from an LLM)** issue form and paste the code in. That's it.

A bot checks your code (it never runs it) and opens a pull request from a `component/` branch. A maintainer reads it,
runs the checks, and may ask you, or the LLM, for changes. You keep credit: your GitHub name is on the commit.

## Other changes (fixes, docs, tooling)

Use a branch named `fix/<topic>`, `docs/<topic>`, `chore/<topic>` and so on, keep the pull request to one change, and
follow rules 3, 5 and 6 above. Changes to `.github/`, `scripts/`, the safety check or packaging always need a
maintainer's review.

## How your contribution reaches Manimater

When a pull request is merged here, the **Sync to app** workflow opens a pull request in [Manimater](https://github.com/bishnt/manimater) with the
same change, so the app and this library do not drift (see [docs/SYNC.md](docs/SYNC.md)).

## Security

Never put tokens or keys in a commit, an issue or a pull request. Report vulnerabilities privately, see
[SECURITY.md](SECURITY.md).

## Licence

By contributing you agree your work is released under the [MIT licence](LICENSE).
