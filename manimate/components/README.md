# Component roadmap: the 50 essential components

This is the build list for the next wave of components. They were picked because an explainer video keeps reaching
for them: a way to show change over time, a way to compare, a way to walk through a process, and the one or two
visuals each subject cannot do without. Each one fills a gap in the current catalog (44 components) and is
parametrised, so the planner can use it for many topics.

Work in order. Tier 1 unlocks the most videos, so it goes first. Each component ships as **its own pull request**:
code, tests, regenerated catalog, and a one-line status tick in this file.

Status key: `[ ]` not started, `[~]` PR open, `[x]` merged.

## Design rules (every component follows these)

1. **One idea per component.** If the description needs the word "and" twice, split it.
2. **Computed, not drawn.** Any algorithm, formula or layout is a plain Python function (`binary_search_steps` in
   `algorithms.py` is the model). The scene only plays those results back, so the video is always correct and the
   function can be unit-tested without Manim.
3. **Fade in as a whole.** The finished picture appears together with one `FadeIn` (about 1.2 to 1.5 s, `smooth`),
   then the parts that carry the meaning animate. No part-by-part build of the static frame. (See the
   `synchronous_motor` entrance.)
4. **Fill the narration time.** The last animation uses `ctx.remaining`. Use `Ctx.beat()` to share time between reveals.
5. **Stay on the stage.** About 12.4 x 5.8 units; the caption owns the bottom. Use `ctx.fit()`; wrap text with `label()`.
6. **Theme colours only** (`theme.py`). One accent colour per component to mark "look here", and never rely on
   colour alone: pair it with a label, a position or a shape.
7. **Few, forgiving params.** At most 5. Every param has a default or is clearly required, a range check with a
   plain-English error, and clamps instead of crashing on odd input.
8. **Example = test.** The `example` passed to `@component` must render. Each component has a pure-logic test plus a
   dry-run against a real `Scene`, like `tests/test_algorithms.py`.
9. **No jargon in labels.** On-screen text is short (under 28 characters where possible), in plain words.
10. **Regenerate the catalog**: `python -m manimate.catalog --out ../worker/src/catalog.json` (CI diffs it), and copy
    to `web/lib/catalog.json`.

## Per-component design template

Each PR description answers these five questions, so the design is reviewed before the code:

- **Teaches:** the one thing the viewer understands afterwards.
- **Params:** names, types, ranges, defaults.
- **Layout:** what sits where on the stage.
- **Beats:** the animation in order, with rough seconds (static frame fades in; then what moves).
- **Failure cases:** what happens with too many items, empty input, very long labels.

---

## Tier 1: general-purpose (build first; useful for every topic)

| # | Name | Teaches | Key params | Status |
|---|------|---------|-----------|--------|
| 1 | `timeline` | Events in order and their spacing in time | `events[]` (`year: label`), `title` | [~] |
| 2 | `data_table` | Values compared across rows and columns, one cell highlighted at a time | `headers[]`, `rows[][]`, `highlight` | [ ] |
| 3 | `line_chart` | How one or more quantities change | `x[]`, `series{name: y[]}`, `title`, `unit` | [ ] |
| 4 | `pie_chart` | Parts of a whole | `labels[]`, `values[]`, `title` | [ ] |
| 5 | `venn_diagram` | What two or three things share and where they differ | `sets[]`, `overlaps[]` | [ ] |
| 6 | `cycle_diagram` | A process that loops (water cycle, feedback loop) | `steps[]`, `title` | [ ] |
| 7 | `concept_map` | How a central idea connects to related ideas | `center`, `branches[]` | [~] |
| 8 | `hierarchy_tree` | Parent and child structure (org chart, taxonomy) | `root`, `children{}` | [~] |
| 9 | `quiz_question` | Active recall: question, options, then the answer revealed | `question`, `options[]`, `answer` | [ ] |
| 10 | `definition_card` | A term, its plain meaning and one example | `term`, `meaning`, `example` | [ ] |
| 11 | `before_after` | The same thing before and after a change | `before`, `after`, `change` | [ ] |
| 12 | `number_line` | Where numbers sit, and jumps between them | `min`, `max`, `points[]`, `jumps[]` | [ ] |

## Tier 2: mathematics

| # | Name | Teaches | Key params | Status |
|---|------|---------|-----------|--------|
| 13 | `vector_addition` | Adding vectors tip to tail and by components | `a`, `b` | [ ] |
| 14 | `unit_circle` | Sine and cosine as the coordinates of a point on a circle | `angle_deg` | [ ] |
| 15 | `derivative_tangent` | The derivative as the slope of a tangent that slides along a curve | `expr`, `x_range` | [ ] |
| 16 | `riemann_sum` | The integral as the area of thinner and thinner rectangles | `expr`, `a`, `b`, `n` | [ ] |
| 17 | `linear_transformation` | What a 2x2 matrix does to the grid | `matrix` | [ ] |
| 18 | `probability_tree` | Chances multiplying along branches | `branches[]` | [ ] |
| 19 | `normal_distribution` | The bell curve, the mean and the 68/95/99.7 rule | `mean`, `std` | [ ] |
| 20 | `scatter_regression` | A line fitted to points, with the residuals shown | `points[]` | [ ] |
| 21 | `fraction_bar` | Fractions as parts of a bar, and equal fractions | `numerator`, `denominator`, `compare` | [ ] |
| 22 | `pythagoras_proof` | a squared plus b squared equals c squared, shown with areas | `a`, `b` | [ ] |

## Tier 3: physics and engineering

| # | Name | Teaches | Key params | Status |
|---|------|---------|-----------|--------|
| 23 | `projectile_motion` | A path from independent horizontal and vertical motion | `speed`, `angle_deg` | [ ] |
| 24 | `free_body_diagram` | Forces on an object adding to a net force | `forces[]` | [ ] |
| 25 | `inclined_plane` | Splitting weight into parallel and perpendicular parts | `angle_deg`, `friction` | [ ] |
| 26 | `spring_mass` | Simple harmonic motion and its energy swap | `k`, `mass` | [ ] |
| 27 | `wave_interference` | Two waves adding, constructive and destructive | `wavelength`, `phase` | [ ] |
| 28 | `snell_refraction` | Light bending at a boundary | `n1`, `n2`, `angle_deg` | [ ] |
| 29 | `orbit_kepler` | Orbits, and why speed changes along an ellipse | `eccentricity` | [ ] |
| 30 | `logic_gates` | AND, OR, NOT and the truth table, with signal flow | `gate`, `inputs[]` | [ ] |
| 31 | `rc_charging_curve` | A capacitor charging and the time constant | `r`, `c` | [ ] |
| 32 | `bode_plot` | Gain and phase against frequency | `poles[]`, `zeros[]` | [ ] |

## Tier 4: chemistry and biology

| # | Name | Teaches | Key params | Status |
|---|------|---------|-----------|--------|
| 33 | `periodic_table_highlight` | Where elements sit and what a group or period shares | `highlight[]`, `mode` | [ ] |
| 34 | `reaction_energy_diagram` | Activation energy, and exothermic against endothermic | `reactants`, `products`, `delta_h` | [ ] |
| 35 | `titration_curve` | pH against volume and the equivalence point | `acid`, `base` | [ ] |
| 36 | `cell_diagram` | The parts of a cell and what each does | `kind` | [ ] |
| 37 | `dna_replication` | Unzipping and the pairing rule A-T, C-G | `sequence` | [ ] |
| 38 | `food_web` | Who eats whom and how energy moves up | `organisms[]`, `eats[]` | [ ] |

## Tier 5: computer science and AI

| # | Name | Teaches | Key params | Status |
|---|------|---------|-----------|--------|
| 39 | `queue_operations` | First in, first out: enqueue and dequeue | `ops[]` | [ ] |
| 40 | `heap_operations` | The heap rule, insertion and extract-min | `values[]`, `op` | [ ] |
| 41 | `dijkstra` | Shortest paths found by always taking the closest unvisited node | `edges[]`, `start` | [ ] |
| 42 | `merge_sort` | Divide, sort the halves and merge | `values[]` | [ ] |
| 43 | `tcp_handshake` | How a connection opens: SYN, SYN-ACK, ACK | `client`, `server` | [ ] |
| 44 | `osi_layers` | Data wrapped layer by layer on its way down | `layers[]` | [ ] |
| 45 | `state_machine` | States, transitions and an input that walks through them | `states[]`, `transitions[]`, `input` | [ ] |
| 46 | `gradient_descent` | Going downhill on a loss surface, and what the learning rate does | `learning_rate`, `start` | [ ] |
| 47 | `k_means` | Points, centres, assign, move, repeat | `points[]`, `k` | [ ] |
| 48 | `confusion_matrix` | True and false positives and negatives, and precision against recall | `tp`, `fp`, `fn`, `tn` | [ ] |
| 49 | `convolution_filter` | A small filter sliding over an image to make a feature map | `image`, `kernel` | [ ] |
| 50 | `attention_heatmap` | Which words a model looks at when reading another word | `tokens[]`, `weights[][]` | [ ] |

---

## Definition of done (per component)

- [ ] Design questions answered in the PR description
- [ ] Pure-logic function with unit tests
- [ ] `@component` with params, ranges and a rendering `example`
- [ ] Dry-run test against a real `Scene` plus the storyboard fade-out
- [ ] One rendered frame or clip checked by eye (text on stage, nothing clipped)
- [ ] `worker/src/catalog.json` and `web/lib/catalog.json` regenerated
- [ ] Status ticked in this file
