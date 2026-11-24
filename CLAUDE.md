# manimater-components

Open-source Manim component library (MIT). Start with `skills/manimater-components/SKILL.md` (also available as
`.claude/skills/manimater-components`): it covers using, previewing and adding components.

- Components live in `manimate/components/` (and `manimate/viz/`); contributions go in `manimate/components/community/`, one file each.
- A new component always goes on its own branch `component/<name>`, one component per pull request, title `feat(community): add <name>` (see CONTRIBUTING.md; `scripts/check_pr_policy.py` enforces it). Never commit straight to `main`.
- After changing components run `python -m manimate.catalog --out catalog.json` and `python scripts/gen_docs.py`; CI checks both. Also run `python scripts/check_community.py`.
- Tests: `python -m pytest` (a dry run of every component). Preview: `python -m manimate.preview <name>`.
- Several files are mirrored with the Manimater app by CI; see `docs/SYNC.md` before moving or renaming them.
