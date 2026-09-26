# Public renderer benchmark corpus

Run the established twelve-entry performance corpus, two Stanford Dragon
variants and two independent SAKU logo rotations against every original core:

```sh
python3 tools/benchmark_repo_examples.py \
  --out ../public-renderer-benchmarks-new \
  --vice-data /usr/local/share/vice --workers 3
```

To run only the separate logo and Dragon versions:

```sh
python3 tools/benchmark_repo_examples.py \
  --cases saku-solid saku-gradient dragon-wireframe dragon-metallic \
  --out ../logo-dragon-benchmarks-new \
  --vice-data /usr/local/share/vice --workers 3
```

The output must be new and outside the checkout. It contains one workspace per
selected group, playable comparison CRTs, complete timing/pixel evidence,
`public-results.json` and `PUBLIC_RENDERER_COMPARISON.md`. The terminal prints a
ranked table per input with the highest verified average FPS marked WINNER.
A capacity limit is N/A with its reason; other failures remain FAIL and produce
a nonzero exit status. No frames are removed to make an old method fit.

Checkpoint 006 adds V5-c1 and V5-c2. For a focused candidate comparison across
the same complete public corpus, add:

```sh
--methods hors-render-v2 hors-v4-ef hors-v5-c1 hors-v5-c2
```

Omitting `--methods` retains all original cores. A subset's winner is the
fastest of that subset; it must not be described as beating every older core.
[The candidate comparison](HORS_V5_CANDIDATES.md) keeps the full checkpoint-005
historical chart alongside its new measurements.

## Inputs

| Group | Frozen inputs | Pictures |
| --- | --- | ---: |
| menu | TORUS, TORUS DENSE, CUBE, SPHERE, HORSE HEAD, SUNFLOWER TORUS, SUNFLOWER COLOR, SPACE HORSE SPIN, SPACE HORSE CRAWL, FALLING CUBES, HORSE HEAD HIFI, SUNFLOWER TORUS HIFI | Original 18–128 per entry |
| dragon-wireframe | Published Stanford Dragon wireframe oracle | 128 |
| dragon-metallic | Published Stanford Dragon metallic oracle | 128 |
| saku-solid | Standalone solid SAKU rotation | 48 |
| saku-gradient | Standalone gradient SAKU rotation | 48 |

SAKU benchmarks use the repository's standalone logo rotations. The interactive
demo, starfield, background cards, presentation switching, hue controls and
exhibition scheduler are absent. Each renderer receives the same geometry,
colours, order and static benchmark HUD. These are separate comparison versions;
the original playable examples remain unchanged.

Published oracles may contain mixed byte/cell clear instructions from a newer
backend. The adapter reconstructs ordinary geometry-cell clear spans before
running each historical encoder. It checks complete bitmap and colour hashes
before and after normalization. This changes clearing metadata, not artwork.
Original material RGB, projection and mesh processing are not rerun in this
fixed-picture playback test.

## Protocol and interpretation

All original cores use the existing common V9 normal PLAY ALL harness, uncapped,
with three ten-second visits. FPS/RAM preferences are separate rows. Accepted
spelling aliases do not count as separate implementations. This includes the
original resident cores, legacy yunroll-cart, streamed v2–v10, HORS-V2 beta/stable,
V3, preserved V4 EasyFlash, V5-c1 and V5-c2. HORS-V1 aliases v10. GMod3 has its own native
scene comparison in the [optimizer-profiler](OPTIMIZER_PROFILER.md), because this
common controller is EasyFlash-specific.

The twelve-entry corpus uses one multi-entry cartridge per method. Dragon and
SAKU each use a separate cartridge per method. Reported CRT sizes include the
whole cartridge; compare within the corresponding group. Native scene contest
rates retain four-refresh pacing and are not mixed into this chart.

Inspect each case and the strongest older compatible method before proposing a
replacement. Average FPS, p95/worst holds, ROM capacity and completed-picture
verification answer different questions. Tiny differences can reflect display
interval/rotation phase. A single average across unrelated inputs hides losses.
These are current-implementation comparisons, not a claim that every old release
has been rerun or that every repository example has been covered.

[Measured checkpoint-005 tables](PUBLIC_RENDERER_COMPARISON.md) and
[the main performance chart](PERFORMANCE_COMPARISON.md).
