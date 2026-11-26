<!--
Read CONTRIBUTING.md first. This pull request is checked automatically (the "PR policy" and "CI passed" checks) and is not
reviewed until both are green. Delete nothing below: tick the boxes that are true, and fix what you cannot tick.
New component? It must come from a branch named component/<name>, one component per pull request.
-->

## What this changes

<!-- One or two sentences: what, and why. -->

## Checklist (every PR)

- [ ] The title is a Conventional Commit, e.g. `fix(viz): clamp negative widths` or `feat(community): add binary_heap`
- [ ] `python -m pytest` passes locally
- [ ] I ran `python -m manimate.catalog --out catalog.json && python scripts/gen_docs.py` and committed the result
- [ ] This pull request does one thing; unrelated changes are in their own pull request
- [ ] No network, files, processes, `eval`/`exec`; any plugin is MIT (or CC) and listed in `docs/THIRD_PARTY.md`

## New component only

<!-- Not adding a component? Leave this whole section as it is; it is skipped. -->

- **Teaches:** <!-- the one thing the viewer understands afterwards -->
- **Params:** <!-- names, types, ranges, defaults (at most 5) -->
- **Layout:** <!-- what sits where on the stage -->
- **Beats:** <!-- the animation in order, with rough seconds -->
- **Failure cases:** <!-- too many items, empty input, very long labels -->

- [ ] This pull request comes from a branch named `component/<name>` and adds exactly one component
- [ ] I added `tests/community/test_<name>.py` (logic and edge cases: empty, one item, the maximum, long labels)
- [ ] I previewed it with `python -m manimate.preview <name>` and watched the whole video
