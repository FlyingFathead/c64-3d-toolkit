# Scene optimizer-profiler

`tools/optimizer_profiler.py` searches measured, lossless build choices for an
exported scene. It includes every original core (step, bytechunk, yunroll and all
streamed/HORS generations), native scene backends, and a separate GMod3 row.
The EasyFlash scene winner is selected only from matching native scene builds. It complements `autotune_scene.py`, whose historical
search also varies pacing and frame plans; those timing results are a different
protocol.

```sh
python3 tools/optimizer_profiler.py /path/to/input.c643dscene \
  --out /path/to/new-private-optimization-run \
  --vice-data /usr/local/share/vice --workers 3 --capture
```

The output directory must be new and outside the checkout. It holds a private
input snapshot, frozen pictures, candidate CRTs, manifests, pixel checks, stage
profiles, comparison.md, results.json and selection.json. Capture is optional.
No candidate is installed and no configuration is changed.

## Build CLI and configuration

```sh
python3 c643d.py build --scene /path/to/input.c643dscene \
  --renderer-selection best-fps --contest-out /path/to/new-contest \
  --contest-vice-data /usr/local/share/vice --contest-capture
```

`--renderer-contest` is an alias for `--renderer-selection best-fps`.
In `[render_defaults]`, `renderer_selection = best-fps` enables this workflow;
`manual` is the built-in default. The CLI overrides config. The selected cart is copied byte-for-byte
into `winner/<scene>-WINNER-<renderer>-g<gap>-b<budget>.crt`, alongside labels and
a manifest. Every contender remains available. The ranked report marks WINNER;
the final output prints the cart path and reusable renderer/encoding flags. No global default is changed.

This first build entry point accepts exported scenes with default playback.
It rejects unsupported appearance/pacing/output overrides rather than measuring
a different build silently. Export `.blend` first, using the intended colour
interpretation. Object/SVG builds and GMod3 require `manual` selection for now.
Use the standalone tool for an explicit candidate/gap/budget search.

## Search and verification

The default search includes all native scene implementations. It tries draw gaps
3, 6 and 12 with batch budget 2048 for the HORS-V2 beta/stable, V3, V4, V5-c1 and V5-c2
encoders; earlier backends retain their native settings. GMod3 is measured but
excluded from the EasyFlash winner. A separate full original-core chart uses
the historical uncapped common PLAY ALL harness, including FPS/RAM variants.
Those rates are not ranked against paced native carts. The standard V4/gap-6/budget-2048 reference is always included.
V5-c2 selects its colour transport with a host cost estimate inside each build;
the contest measures the resulting cartridge. It is an experimental contender,
not an automatic replacement for c1. Original `hors-v5` builds still select c1.
Use `--renderers`, `--gaps` and `--budgets` to bound the search. Aliases do not count
as additional candidates. Independent worker processes isolate build hooks.
The former `--renderers hors-v5-ef` spelling remains accepted as c1.

All candidates retain the same complete picture bytes, colours and order,
source projection and picture order. Eligible native EasyFlash builds share the
HUD and four-refresh minimum hold; GMod3 retains its own controller/HUD, and the
original-core chart uses its separately labelled common-controller protocol. Before measuring, each
candidate's oracle must match the frozen input hash and pass completed-picture
checks in VICE. Measurement uses one full warmup loop and two measured loops.
All source samples remain present. Source, input and tool hashes are recorded.

Results include average displayed FPS, p95/worst display hold, active cycles,
clear/reset, fetch, colour and drawing stages, cart size and per-frame details.
A confirmed capacity limit is N/A with its reason; other errors remain FAIL and
cause a nonzero final exit status, even if another candidate succeeds.

The **highest verified average FPS wins** among eligible native EasyFlash carts.
Exact FPS ties prefer the smaller CRT, then lower active work. Close contenders
within 0.5% are listed without pretending the difference is a universal speed
advantage. P95/worst holds more than 0.5% above V4 are explicitly flagged; a
slower cart is not relabelled as the FPS winner. `--tolerance-percent` controls
these informational comparisons. The terminal prints ranked tables, with bold
green WINNER on supporting terminals and a plain WINNER marker when redirected
or `NO_COLOR` is set. Each protocol has its own FPS leader.

This is a measured choice among tested candidates, not a global optimum.

RAM layouts, video standard, pacing and geometry are fixed rather than searched.
PRG length is not a measure of RAM consumption. Physical C64 and NTSC performance
remain unmeasured. Profiles include VIC stalls and interrupt work; these are not
bare instruction-cycle estimates.

## Mapping and colour conflict are separate

The report includes the recorded Blender colour-space choice, exported face
palette counts and conflicting 8×8 cells. A conflict means visible edges request
more than one foreground colour in the same cell. Existing wireframe output
chooses one foreground plus the background, so it cannot represent black, red
and blue simultaneously in that cell.

`blender_color_space = linear` interprets standard Blender material values as
linear light before palette matching. `srgb` interprets them as already encoded
sRGB. This controls material-to-palette conversion during Blender export; it
cannot reinterpret palette indices already stored in a `.c643dscene`. Re-export
from `.blend` to compare it. A material custom property `c643d_color` selects an
explicit C64 index/name independently of that conversion.

The interchange file does not retain original material RGB or shader-node values.
The profiler therefore reports that information as unavailable; it does not infer
whether linear or sRGB was artistically intended from the resulting palette.

Lossless optimization must preserve the current pictures, including their colour
clashes. A depth-priority colour policy or suppression of conflicting background
fragments is a separate visual experiment with a new reference, side-by-side
previews and an explicit count of changed colours or omitted pixels. It must not
be ranked as a free speed improvement over unchanged artwork.

## Next optimization targets

Use the stage breakdown to choose the next code change. If colour application
and metadata fetch dominate, test alternative colour encoding before adding
more line-drawing unrolling. If clearing dominates, compare bounded clear plans.
Keep V2, V4 and V5 available: a newer generation is not automatically faster.

For the established public corpus, Dragon and effect-free SAKU logo versions,
use [the public benchmark runner](PUBLIC_BENCHMARKS.md).

## Learning from the older renderers

The contest chooses an available build; the replacement-development loop must
also explain the winners. Keep the original implementations as controls rather
than removing them after a new version appears. The checkpoint-004 measurements
in PERFORMANCE_COMPARISON.md establish these workload-specific observations:

| Family | Observed strength | Observed limitation / next test |
| --- | --- | --- |
| Resident step / bytechunk / yunroll | Strong small-CUBE throughput; yunroll averaged 30.168 FPS in the common controller | Both private large scenes exceed the 255-record resident limit; capacity is N/A, not low FPS |
| Streamed v2 through v9 | Handle scenes that do not fit resident tables; smaller carts in several cases | Fetch/draw overhead leaves the tested large scenes far below later methods; retain as capacity/size controls |
| v10 / HORS-V1 | Large throughput improvement over earlier streamed generations on these scenes | HORS-V2 remains faster on both measured native scenes |
| HORS-V2 | Cheaper fetch and colour application on the multicolour scene | More clear/reset work than V5; tune span gaps and retain ROM-size accounting |
| HORS-V3 / preserved V4 | Shared absolute colour-address strategy removes old per-picture colour reset dependency | On the multicolour test, fetch and colour application cost more than V2; test whether encoding should be selected per scene |
| HORS-V5 | Lower clearing cost and higher average FPS than V4 on both private scenes | Default V5 still loses to V2 on the multicolour test; clearing alone is not a better overall replacement |

These are measured cases, not universal claims about each algorithm. Public CUBE,
monochrome scene and multicolour scene belong in the minimum comparison set.
Add sparse/dense coverage, colour-boundary stress, high record counts, clipping,
and repeated pictures as distinct controls when the relevant code changes.

A replacement candidate should keep bitmap/colour/sample equality, report each
case separately, and compare against the strongest compatible older method as
well as the current default. Show p95/worst latency, ROM capacity and visual
checks beside average FPS. A single combined average must not hide a regressing
case. Treat a new visual colour policy as a separate experiment with explicit
image differences, not as a lossless renderer speed gain.

The next concrete runtime hypothesis is to combine V5's bounded clearing with
V2's cheaper colour/metadata path, then measure the complete scene again. A
component's estimated cycle saving does not guarantee an end-to-end win.
