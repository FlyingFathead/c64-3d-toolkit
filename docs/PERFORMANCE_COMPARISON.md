# Renderer performance comparison

The [optimizer-profiler](OPTIMIZER_PROFILER.md) searches a scene at fixed pacing.
The historical tables below retain their recorded versions and protocols.

## v0.8.2: HORS-V1 through V5 average FPS

Fresh PAL VICE measurements compare all six family choices against identical
pictures and colours: **192 public combinations: 190 passes, two capacity N/As, zero failures**, with
**21,322 completed-picture checks**. HORS-V1 is `yunroll-cart-v10`; V3 and V4 EF
retain the same picture core. Both FPS and RAM preferences are measured.

The summary below uses **FPS preference**, the uncapped common V9 normal PLAY ALL
controller, three ten-second visits. Compare within each row. Bold marks the
highest measured average; small differences are not a statistical confidence claim.

| Public input | HORS-V1 | HORS-V2 | HORS-V3 | HORS-V4 EF | V5-c1 | V5-c2 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| DRAGON WIREFRAME | N/A | 19.387 | 19.387 | 19.387 | **19.454** | **19.454** |
| DRAGON METALLIC | 11.250 | 11.452 | 14.265 | 14.265 | **14.366** | **14.366** |
| SAKU SOLID LOGO ONLY | 36.966 | **38.808** | 32.010 | 32.010 | 32.214 | 38.773 |
| SAKU GRADIENT LOGO ONLY | 31.107 | 32.013 | 31.209 | 31.209 | 31.335 | **32.109** |

C2 improves the two SAKU logo-only inputs and ties c1 on the other fourteen
public inputs in both preferences. V2 remains about 0.09% faster on solid SAKU.
There is no universal renderer winner. No cross-scene arithmetic average is used
as a release score. [All 16 inputs, both preferences and latency tails](RELEASE_0.8.2_PERFORMANCE.md).

One private validation workload, **Sande's Nightdrive Test**, retains all 120
pictures, four-refresh pacing, one warmup loop and two measured loops. These
native results are separate from the uncapped public table. Draw gap 12 and
batch budget 2048 apply to V2 and later; V1 does not implement those settings.

| Native scene | HORS-V1 | HORS-V2 | HORS-V3 | HORS-V4 EF | V5-c1 | V5-c2 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Sande's Nightdrive Test | 6.312 | 7.716 | 7.039 | 7.039 | 7.477 | **7.796** |

C2 gains **4.28% over c1** and **1.04% over V2** here. All 24 private family/setting
combinations pass, with 5,832 completed-picture checks. Private source assets,
carts, previews, filenames and raw results are not distributed with this release.

V4/EasyFlash stays the default. V5-c1/c2 are opt-in; `hors-v5` still means c1.
Colour mapping and overlap behaviour are unchanged. These tests verify matching
encoded pictures, not absence of source palette/8×8 colour conflicts. PAL VICE
only; physical hardware and NTSC remain unmeasured. Historical tables follow
with their original workload definitions and measurement versions.

## V5-c1 and V5-c2: checkpoint 006

The existing V5 is now named **V5-c1**. Old `hors-v5` / `hors-v5-ef` selectors still
mean c1. **V5-c2 is a separate opt-in candidate**, combining V5 clearing with a
host-selected run/shared colour transport. Default colour mapping and overlap
behaviour are unchanged; V4/EasyFlash remains the default renderer.

[Implementation and build commands](HORS_V5_CANDIDATES.md) ·
[All new candidate rows and tail holds](V5_CANDIDATE_COMPARISON.md).

Fresh public measurements cover **16 inputs × 8 method/preference combinations:
128 passes, 0 capacity N/As, 0 failures**, with **14,560
completed-picture checks**. V2, V4, c1 and c2 are rebuilt at this checkpoint.
These focused measurements supplement the full original-core tables below;
they do not rerank unmeasured older implementations as current-checkpoint results.

Public rows use the uncapped common V9 normal PLAY ALL harness, three ten-second
visits, fixed complete pictures/colours and FPS preference in this summary.
The twelve original corpus entries produce exactly matching c1/c2 measured
FPS. The separate Dragon/SAKU results are:

| Public case | V2 FPS | V4 FPS | V5-c1 FPS | V5-c2 FPS | C2 colour transport |
| --- | ---: | ---: | ---: | ---: | --- |
| DRAGON WIREFRAME | 19.387 | 19.387 | 19.454 | 19.454 | runs |
| DRAGON METALLIC | 11.452 | 14.265 | 14.366 | 14.366 | shared |
| SAKU SOLID LOGO ONLY | 38.808 | 32.010 | 32.214 | 38.773 | runs |
| SAKU GRADIENT LOGO ONLY | 32.013 | 31.209 | 31.335 | 32.109 | runs |

C2 improves both SAKU variants and exactly matches c1 on the other fourteen
public inputs, in both preferences. Solid SAKU gains 20.36% over c1, but V2's
38.808 FPS remains slightly above c2's 38.773 (about 0.09%). The heuristic is
therefore useful on these inputs, not proof that every scene selects its
fastest possible pipeline. Public p95/worst holds remain in the full tables.

### Native Nightdrive Test: separate four-refresh protocol

Both private exports keep all 120 authored samples, the same projection, HUD,
pacing, bitmap and screen-colour bytes. One warmup loop and two measured loops;
243 completed-picture checks per cart. These native rates are not compared with
the uncapped public table. Test A is car-only; Test B includes the road.

| Test | Draw gap | V2 FPS | V5-c1 FPS | V5-c2 FPS | C2 vs c1 |
| --- | ---: | ---: | ---: | ---: | ---: |
| A | 6 | 12.00588 | 12.10251 | 12.10251 | +0.00% |
| A | 12 | 12.27540 | 12.35102 | 12.35102 | +0.00% |
| B | 6 | 7.35773 | 7.13517 | 7.42586 | +4.07% |
| B | 12 | 7.71641 | 7.47663 | 7.79643 | +4.28% |

For Test B/gap 12, c2 is **4.28% faster than c1 and 1.04% faster than V2**.
C2 uses 763,408 CRT bytes, V2 also 763,408, and c1 993,232. P95 is 159.603 ms
and worst hold 159.608 ms for c1/c2. Forcing c2 to shared colour transport
reproduces c1 FPS and stage totals, supporting transport cost as the cause of
this improvement. The car-only c2 result ties c1 at both settings.

| Test B/gap 12: mean elapsed cycles | V2 | V5-c1 | V5-c2 runs |
| --- | ---: | ---: | ---: |
| Recycle bitmap and colours | 47,879.24 | 36,605.69 | 46,836.73 |
| Metadata fetch | 5,626.03 | 13,343.87 | 5,427.73 |
| Apply colours | 11,193.05 | 18,921.03 | 11,183.81 |
| Draw lines | 62,686.57 | 62,642.00 | 62,675.54 |
| Total active render | 127,410.05 | 131,537.38 | 126,148.23 |

C2 spends more than c1 recycling old colour runs, but saves more in colour
metadata fetch and application. Its V5 clear planner then reduces active work
relative to V2. Stage cycles include VIC/IRQ effects and are measured separately
from actual display intervals. All 13 private comparison/transport-control
carts pass (3,159 completed-picture checks). Private artwork, carts, raw reports
and previews remain outside the repository.

These results support c2 as a candidate, not a universal replacement. Neither
candidate changes the 8×8 colour limitation or repairs existing road/car colour
conflicts. Physical C64 and NTSC are unmeasured. The unchanged historical
sections below preserve their original names and measured source versions.
Where they say V5, that implementation is now c1.

The final source differs from the measured fingerprint only by retaining the
old optimizer `--renderers hors-v5-ef` spelling as a c1 alias. The exact change
and both hashes are recorded in `benchmarks/v5-candidates/provenance-audit.json`;
no measured encoder, renderer, timing or verification path changed.

## Public corpus and renderer contest: checkpoint 005

Fresh PAL VICE measurements cover **16 public inputs × 27 method/preference
combinations: 386 passes, 46 capacity N/As, zero failures**, with **38,506
completed-picture checks**. The established twelve-entry corpus is joined by
Dragon wireframe/metallic and separate SAKU solid/gradient logo-only rotations.
SAKU includes no starfield or interactive presentation effects. All original
source samples and colours are retained; no input is simplified to fit a method.

[Full per-renderer tables, p95/worst holds and N/A reasons](PUBLIC_RENDERER_COMPARISON.md)
· [repeatable public command](PUBLIC_BENCHMARKS.md)
· [scene contest CLI/config](OPTIMIZER_PROFILER.md).

The following public rows share the uncapped common V9 normal PLAY ALL protocol;
the twelve-entry menu uses a multi-entry cart, while Dragon/SAKU each use their
own cart. Compare methods within each case. Values are **average displayed FPS**.

| Case | Pictures | Fastest measured method / preference | Average FPS | V2 FPS | V4 FPS | V5 FPS |
| --- | ---: | --- | ---: | ---: | ---: | ---: |
| TORUS | 32 | hors-v5-ef / ram | 17.782 | 17.680 | 17.680 | 17.780 |
| TORUS DENSE | 32 | hors-v5-ef / fps | 17.380 | 17.179 | 17.179 | 17.380 |
| CUBE | 36 | yunroll / fps | 30.269 | 30.031 | 30.031 | 30.032 |
| SPHERE | 24 | hors-v5-ef / ram | 17.480 | 17.379 | 17.379 | 17.478 |
| HORSE HEAD | 32 | hors-v5-ef / ram | 29.434 | 29.335 | 29.335 | 29.432 |
| SUNFLOWER TORUS | 28 | hors-v5-ef / ram | 28.931 | 28.730 | 28.730 | 28.927 |
| SUNFLOWER COLOR | 20 | hors-v5-ef / fps | 22.733 | 20.891 | 22.701 | 22.733 |
| SPACE HORSE SPIN | 24 | hors-v5-ef / fps | 19.288 | 19.083 | 19.086 | 19.288 |
| SPACE HORSE CRAWL | 32 | hors-renderer-v3 / ram | 38.278 | 38.275 | 38.273 | 38.271 |
| FALLING CUBES | 18 | hors-v5-ef / ram | 21.397 | 20.892 | 21.295 | 21.396 |
| HORSE HEAD HIFI | 128 | hors-v5-ef / ram | 23.307 | 21.495 | 23.105 | 23.204 |
| SUNFLOWER TORUS HIFI | 128 | hors-v5-ef / fps | 22.804 | 20.394 | 22.702 | 22.804 |
| DRAGON WIREFRAME | 128 | hors-v5-ef / fps | 19.454 | 19.387 | 19.387 | 19.454 |
| DRAGON METALLIC | 128 | hors-v5-ef / fps | 14.366 | 11.452 | 14.265 | 14.366 |
| SAKU SOLID LOGO ONLY | 48 | hors-render-v2 / fps | 38.808 | 38.808 | 32.010 | 32.214 |
| SAKU GRADIENT LOGO ONLY | 48 | hors-render-v2 / fps | 32.013 | 32.013 | 31.209 | 31.335 |

V5 leads 12 of these 16 cases by measured average, including both Dragon variants.
The resident yunroll wins CUBE; V3/RAM leads SPACE HORSE CRAWL by a tiny interval
phase difference; V2 wins both SAKU logos. These per-case results do not establish
a universal replacement or an old-release regression claim. In particular,
metallic Dragon favours V4/V5's colour path, while solid SAKU favours V2.
Keep all implementations available and compare a candidate with the best older
compatible method, not only the current default.

### Native fixed-picture contest: Nightdrive Test B

This is a **separate protocol**: 120 pictures, four-refresh minimum hold, one
warmup loop and two measured loops. All 23 native candidates pass; original-core
history adds 23 passes and three resident capacity N/As. There are 11,178 completed
picture checks in total. Private artwork, CRTs, previews and raw evidence remain
outside the repository.

| Renderer / draw gap | Average FPS | Meaning |
| --- | ---: | --- |
| V4 EasyFlash / 6 | 6.73566 | Preserved reference |
| V5 EasyFlash / 6 | 7.13517 | Current V5 defaults |
| V2 / 6 | 7.35773 | Older core still faster here |
| V5 EasyFlash / 12 | 7.47663 | Tuned V5 |
| V2 / 12 | **7.71641** | Highest tested average; stable and beta1 tie |

The V2/gap-12 winner uses 763,408 CRT bytes. It is a measured selection for this
scene, not a change to the default renderer. The public colour-cube and
colour-torus exports also pass all 49 native/core candidates each (4,410 checks
combined); their cheap native candidates reach the four-refresh pacing ceiling,
so tiny differences there should not be promoted as a general speed advantage.

The measurement inputs and tools are hashed in the raw reports. Subsequent
checkpoint finalization adds the public runner, CLI configuration validation and
P95 table formatting; no measured renderer/encoder instruction path changed.
The original historical sections below retain their own recorded protocols.

## Full renderer history: Nightdrive Test (2026-09-25)

Fresh v0.8.2-dev4 measurements cover every distinct implementation represented
by the current `--renderer` choices. Aliases are listed in the private report.
The public CUBE / 36 control exercises the original resident methods. Nightdrive
Test A is the private car-only export; Test B is the private car-and-road export,
each with all 120 authored pictures. These exports are distinct from the original
Nightdrive cartridge below. No private artwork or raw private evidence is stored here.

[Repeatable full-history command and protocols](RENDERER_HISTORY_BENCHMARK.md).
All values below are **high / average / low displayed FPS**, measured in PAL VICE 3.10.
Compare within each table: core runs are uncapped PLAY ALL; native scene runs
retain four-refresh pacing. VICE flash writeback is disabled.

### Original cores: common normal PLAY ALL

Three ten-second visits, identical frozen pictures, colours, HUD and order.
V2 and later comparison encoders use gap 3 / budget 2048. Each case gets its
own cartridge. FPS/RAM preferences are measured separately.

| Renderer | Preference | CUBE / 36 | Nightdrive Test A / 120 | Nightdrive Test B / 120 |
| --- | --- | ---: | ---: | ---: |
| step | fps | 50.173 / 26.452 / 16.707 | N/A¹ | N/A¹ |
| bytechunk | fps | 50.160 / 29.365 / 25.052 | N/A¹ | N/A¹ |
| yunroll | fps | 50.165 / 30.168 / 25.051 | N/A¹ | N/A¹ |
| yunroll-cart-v2 | fps | 44.363 / 23.036 / 16.707 | 3.366 / 2.913 / 2.772 | 2.947 / 2.511 / 2.378 |
| yunroll-cart-v3 | fps | 50.135 / 24.609 / 16.708 | 3.564 / 3.314 / 3.113 | 3.604 / 2.813 / 2.621 |
| yunroll-cart-v4 | fps | 50.127 / 24.610 / 16.707 | 3.598 / 3.315 / 3.143 | 3.349 / 2.813 / 2.618 |
| yunroll-cart-v5 | fps | 50.135 / 25.581 / 16.705 | 4.558 / 3.817 / 3.550 | 3.862 / 3.214 / 2.955 |
| yunroll-cart-v6 | fps | 55.544 / 26.720 / 16.707 | 4.560 / 3.918 / 3.580 | 4.182 / 3.315 / 3.133 |
| yunroll-cart-v7 | fps | 55.818 / 26.854 / 16.707 | 5.582 / 4.520 / 4.177 | 5.074 / 3.918 / 3.580 |
| yunroll-cart-v8 | fps | 55.818 / 26.854 / 16.707 | 16.831 / 4.721 / 4.177 | 5.074 / 3.918 / 3.580 |
| yunroll-cart-v9 | fps | 55.642 / 26.820 / 16.708 | 25.208 / 4.822 / 4.177 | 5.079 / 3.918 / 3.580 |
| HORS-V1 / yunroll-cart-v10 | fps | 51.039 / 27.490 / 16.640 | 25.208 / 10.246 / 8.353 | 10.025 / 6.730 / 5.012 |
| yunroll-cart-v7 | ram | 52.729 / 24.644 / 16.014 | 5.634 / 4.420 / 3.856 | 4.614 / 3.717 / 3.342 |
| yunroll-cart-v8 | ram | 52.729 / 24.644 / 16.014 | 17.477 / 4.621 / 4.177 | 4.614 / 3.717 / 3.342 |
| yunroll-cart-v9 | ram | 53.366 / 24.644 / 16.033 | 25.106 / 4.721 / 4.177 | 4.607 / 3.817 / 3.342 |
| HORS-V1 / yunroll-cart-v10 | ram | 50.778 / 27.422 / 16.673 | 25.106 / 10.246 / 8.354 | 10.065 / 6.730 / 5.012 |
| HORS-V2 | fps | 55.859 / 29.967 / 23.123 | 25.420 / 11.151 / 8.353 | 12.656 / 7.133 / 5.569 |
| HORS-V2 | ram | 55.916 / 30.000 / 23.127 | 25.594 / 11.151 / 8.354 | 10.025 / 7.132 / 5.569 |
| HORS-V3 | fps | 55.859 / 29.967 / 23.123 | 25.420 / 11.151 / 8.353 | 8.466 / 6.630 / 5.569 |
| HORS-V3 | ram | 55.916 / 30.000 / 23.127 | 25.594 / 11.151 / 8.354 | 10.025 / 6.629 / 5.569 |
| HORS-V2 beta1 | fps | 55.859 / 29.967 / 23.123 | 25.420 / 11.151 / 8.353 | 12.656 / 7.133 / 5.569 |
| HORS-V2 beta1 | ram | 55.916 / 30.000 / 23.127 | 25.594 / 11.151 / 8.354 | 10.025 / 7.132 / 5.569 |
| HORS-V4 / EasyFlash | fps | 55.859 / 29.967 / 23.123 | 25.420 / 11.151 / 8.353 | 8.466 / 6.630 / 5.569 |
| HORS-V4 / EasyFlash | ram | 55.916 / 30.000 / 23.127 | 25.594 / 11.151 / 8.354 | 10.025 / 6.629 / 5.569 |
| HORS-V5 / EasyFlash | fps | 56.471 / 30.035 / 23.166 | 25.576 / 11.284 / 8.354 | 8.505 / 6.831 / 5.569 |
| HORS-V5 / EasyFlash | ram | 55.373 / 30.031 / 23.166 | 16.964 / 11.350 / 8.354 | 10.025 / 6.831 / 5.569 |

¹ Exact recorded reason for each resident N/A: **resident record count exceeds 255**
(the eight-bit line-record count per picture). This is a capacity result, not
zero FPS. The same methods pass on CUBE. No pictures or geometry were dropped.

### Native scene backends: four-refresh minimum hold

One complete warmup loop, then two measured loops (240 display intervals).
CLI encoding defaults: gap 6 / budget 2048. Each result passes 243 completed
picture/colour checks across all three buffers against identical input pictures.
GMod3 retains its own HUD/controller; that row compares native backend behavior.

| Renderer | Nightdrive Test A / 120 | Nightdrive Test B / 120 | B worst hold (ms) |
| --- | ---: | ---: | ---: |
| yunroll-cart-v4-scene | 3.619 / 3.241 / 2.928 | 3.160 / 2.375 / 1.667 | 600.011 |
| yunroll-cart-v5-scene | 4.220 / 3.716 / 3.312 | 3.615 / 2.764 / 2.001 | 499.787 |
| yunroll-cart-v6-scene | 4.177 / 3.821 / 3.342 | 3.580 / 2.873 / 2.089 | 478.803 |
| yunroll-cart-v7-scene | 5.013 / 4.405 / 3.856 | 4.177 / 3.357 / 2.506 | 399.010 |
| yunroll-cart-v8-scene | 12.530 / 4.645 / 3.856 | 4.177 / 3.357 / 2.506 | 399.010 |
| yunroll-cart-v9-scene | 12.677 / 4.718 / 3.856 | 4.177 / 3.378 / 2.506 | 399.009 |
| yunroll-cart-v10-scene | 12.630 / 10.552 / 8.354 | 8.354 / 6.312 / 5.012 | 199.506 |
| hors-render-v2-beta1-scene | 12.829 / 12.006 / 10.025 | 10.025 / 7.358 / 5.569 | 179.555 |
| hors-v2-scene | 12.829 / 12.006 / 10.025 | 10.025 / 7.358 / 5.569 | 179.555 |
| hors-v3 | 12.829 / 12.006 / 10.025 | 8.354 / 6.736 / 5.569 | 179.557 |
| HORS-V4 / EasyFlash | 12.829 / 12.006 / 10.025 | 8.354 / 6.736 / 5.569 | 179.557 |
| hors-v4-gmod3 | 12.773 / 12.078 / 10.025 | 8.354 / 6.789 / 5.569 | 179.558 |
| HORS-V5 / EasyFlash | 12.750 / 12.103 / 10.025 | 10.025 / 7.135 / 5.569 | 179.554 |

### What the broader comparison changes

HORS-V5 improves on preserved V4, but HORS-V2 is faster on Test B. Newer is
not universally faster. The stage profile identifies why: V5 saves clearing
work, while V2 has cheaper frame fetch and colour application for this input.
The next optimization candidate is the colour/metadata policy; this checkpoint
does not change rendering or choose a new default.

| Test B stage, mean elapsed cycles | HORS-V2 scene | HORS-V4 EasyFlash | HORS-V5 EasyFlash |
| --- | ---: | ---: | ---: |
| recycle bitmap and colors | 47,857.36 | 45,157.73 | 36,620.17 |
| fetch | 5,647.07 | 12,969.38 | 13,361.26 |
| apply colors | 11,198.34 | 18,880.04 | 18,919.62 |
| draw lines | 68,928.77 | 68,957.16 | 68,951.44 |

98 combinations pass; 6 capacity N/As; 19,446 completed-picture checks. No unexplained build or pixel failures remain.
All 77 original assembly files and the source geometry/colour pipeline are
byte-identical to the supplied v0.8.1 baseline. The public cube raw report is
[here](benchmarks/renderer-history/cube.json); private raw evidence remains external.
This is a fixed-input renderer comparison, not a rerun of every historical
workload, physical C64 hardware or NTSC. Existing historical tables below remain
labelled with their original protocols and dates.

## HORS-V5 preview / EasyFlash: Nightdrive Test (2026-09-25)

HORS-V5 is an opt-in experiment; HORS-V4 / EasyFlash remains the default.
The **Nightdrive Test** row below identifies the unchanged private cartridge.
Its matching scene/build settings are not available, so it has no V5 result.
The two separately exported private scenes are matched V4/V5 comparisons with
identical pictures, colours, order, HUD and pacing. They are not rebuilds of
that original cartridge. Assets, previews, carts and private raw evidence are
kept outside this repository. [Method, tools and limits](HORS_V5_PREVIEW.md).

| Test | HORS-V4 FPS | HORS-V5 FPS | Change | Worst display hold V4 → V5 |
| --- | ---: | ---: | ---: | ---: |
| Nightdrive Test — original private cartridge | 10.143 | — | unmeasured | 119.705 ms → — |
| Private car-only scene / 120 pictures | 12.006 | 12.103 | +0.805% | 99.752 → 99.748 ms |
| Private car-and-road scene / 120 pictures | 6.736 | 7.135 | +5.931% | 179.557 → 179.554 ms |

These are actual display flips in PAL VICE 3.10: one full warmup loop, then
240 intervals (two loops). Both new scenes pass 243 completed-picture checks
against the same host oracle across all three buffers, including bitmap,
colour, border and HUD checks. All 120 samples are retained. The four-refresh
minimum hold gives a roughly 12.531 FPS ceiling; this is the current build
pacing, not the exports' 24 FPS source rate. No original-duration claim is made.
Physical hardware and NTSC are unmeasured.

The car-only CRT shrinks by one 8 KiB ROM bank; the car-and-road CRT grows by
one bank. Mean active render cycles fall from 77,329.26 to 76,337.12 and from
145,988.74 to 137,877.28 respectively. Worst active cycles also improve;
worst visible holds remain effectively unchanged. This is not a universal
speedup or proof of regression freedom in every workload.

### Public regression controls

Same V4 EasyFlash core versus V5, frozen public pictures, normal automatic
playback or interactive idle as labelled. Stars are excluded. Each case uses
one warmup loop and two measured loops; this protocol is separate from the
historical PLAY ALL matrices below. [Raw public results](benchmarks/hors-v5-preview/results.json).

| Workload | V4 average FPS | V5 average FPS | Change | Worst hold V4 → V5 |
| --- | ---: | ---: | ---: | ---: |
| Metallic torus / 48 | 9.840 | 9.881 | +0.411% | 119.705 → 119.707 ms |
| Golden dragon / 128 | 15.132 | 15.186 | +0.355% | 82.402 → 82.425 ms |
| Interactive metallic torus / 48 | 9.605 | 9.702 | +1.008% | 119.706 → 119.705 ms |

All five matched pairs pass the declared 0.5% aggregate regression tolerance
for displayed average, worst display hold, mean and worst active render cycles.
Small individual regressions remain visible above: the dragon's worst hold
increases by 0.023 ms. Per-frame phase/stall differences are not hidden by this
gate. V4 core CRTs are byte-identical when rebuilt after V5 in the same process;
the two private V4 scene CRTs also match their pre-V5 baselines exactly.
Interactive validation covers 242 forward/reverse pictures and 20 input checks.
The new byte-clear kernel passes 1,275 VICE cases (all lengths 1..255 at five
alignments, including page crossings), with guard bytes unchanged.

For the v0.8.1 interactive hotfix, see the [matched v3.0/v3.1 A/B tables](INTERACTIVE_BASELINE_PERFORMANCE.md): all 58 entries, high/average/low FPS, and measured input-service overhead. The v0.8.0 renderer comparison below remains a historical measurement; the benchmark cartridge is unchanged.


Canonical lookup table for comparing methods and toolkit releases. **Historical method matrices use normal PLAY ALL. F5 is an exhibition mode and MUST NOT be used for benchmarking.** The separately labelled Sande standalone tests measure ordinary object playback and interactive idle cost; compare results within each protocol.

Measured on PAL VICE 3.10, 985,248 cycles/s, default machine settings, sound disabled, seed 1; 64tass 1.59.3120. This is emulated C64 time, not host wall time or the HUD FPS counter. Physical C64 and NTSC are not measured.

In the historical PLAY ALL matrices, each cell is actual display flips / elapsed emulated time across 3 normal PLAY ALL visits. Every visit uses the unchanged 10-second setting. Observation starts on the first timer-count IRQ and ends at automatic-next: 499 PAL refresh intervals (about 9.955 s). The first visible picture is outside that window. Rates are rounded to two decimals; **bold** marks the highest reported average FPS for each comparable workload, including ties. Tiny timer-phase differences are not ranked as wins.

<!-- BEGIN HORS-V4 GMOD3 -->
## HORS-V4 / GMod3: v0.8.0 matched comparison

`hors-v4-gmod3` identifies HORS-V4 using its default GMod3 backend. The baseline is `hors-v3` on EasyFlash. Both receive identical pictures, colours, sample order, encoding policy and HUD settings. These are automatic standalone tests: no input polling, stars, exhibition or authored frame-rate cap.

Across 69 matched workloads: **65 GMod3 wins, 4 ties, 0 lower averages**. The observed change ranges from +0.000 to +0.397 FPS. This supports modest throughput gains and the larger collection capacity; it does not support a universal +1 FPS claim.

Each test verifies two complete picture loops plus warm-up in all three buffers, then counts actual displayed-slot transitions for 4,800 PAL refreshes (95.761 seconds). High/low FPS are reciprocals of the shortest/longest observed display hold; they are listed as diagnostics. Only the highest average in each matched pair is bold. Ties are explicit.

The 640-picture Marbles sequence is compared as five matching 128-picture segments, with no dropped pictures; uninterrupted five-page playback is checked separately in the collection. The 192-picture metallic Pretzel uses its released `indexed4` colour policy on both backends to fit the preserved EasyFlash ROML allocator. All other pairs use literal colour bytes. These settings are recorded per case in the raw report.

[Raw matched results](benchmarks/hors-v4-matched/results.json) · [Actual interactive collection results](benchmarks/gmod3-collection/interactive/results.json) · [Bank/copy diagnostics](benchmarks/gmod3-checkpoint1/results.json)

### SAKU presentations

| Scene | Method | High FPS | Average FPS | Low FPS |
| --- | --- | ---: | ---: | ---: |
| SAKU SOLID SPIN / 30 | hors-v3 | 50.125 | 38.053 | 25.062 |
| SAKU SOLID SPIN / 30 | hors-v4-gmod3 | 50.125 | **38.335** | 25.062 |
| SAKU GRADIENT SPIN / 30 | hors-v3 | 50.125 | 33.563 | 25.062 |
| SAKU GRADIENT SPIN / 30 | hors-v4-gmod3 | 50.125 | **33.803** | 25.062 |
| SAKU SOLID CRAWL / 30 | hors-v3 | 50.125 | **50.125 (tie)** | 50.125 |
| SAKU SOLID CRAWL / 30 | hors-v4-gmod3 | 50.125 | **50.125 (tie)** | 50.125 |
| SAKU GRADIENT CRAWL / 30 | hors-v3 | 50.125 | **48.506 (tie)** | 25.062 |
| SAKU GRADIENT CRAWL / 30 | hors-v4-gmod3 | 50.125 | **48.506 (tie)** | 25.062 |
| SAKU CARD SPIN / 30 | hors-v3 | 50.125 | 22.660 | 16.708 |
| SAKU CARD SPIN / 30 | hors-v4-gmod3 | 50.125 | **22.796** | 16.708 |
| SAKU CARD CRAWL / 30 | hors-v3 | 50.125 | **46.992 (tie)** | 25.062 |
| SAKU CARD CRAWL / 30 | hors-v4-gmod3 | 50.125 | **46.992 (tie)** | 25.062 |
| SAKU OUTLINE SPIN / 30 | hors-v3 | 50.125 | 33.427 | 25.062 |
| SAKU OUTLINE SPIN / 30 | hors-v4-gmod3 | 50.125 | **33.657** | 25.062 |
| SAKU OUTLINE CRAWL / 30 | hors-v3 | 50.125 | **48.506 (tie)** | 25.062 |
| SAKU OUTLINE CRAWL / 30 | hors-v4-gmod3 | 50.125 | **48.506 (tie)** | 25.062 |
| SAKU GRADIENT / 48 | hors-v3 | 50.125 | 33.228 | 25.062 |
| SAKU GRADIENT / 48 | hors-v4-gmod3 | 50.125 | **33.458** | 25.062 |
| SAKU SOLID / 48 | hors-v3 | 50.125 | 34.325 | 25.062 |
| SAKU SOLID / 48 | hors-v4-gmod3 | 50.125 | **34.575** | 25.062 |

### Stanford Dragon

| Scene | Method | High FPS | Average FPS | Low FPS |
| --- | --- | ---: | ---: | ---: |
| DRAGON BLUE / 128 | hors-v3 | 25.062 | 15.152 | 12.531 |
| DRAGON BLUE / 128 | hors-v4-gmod3 | 25.062 | **15.246** | 12.531 |
| DRAGON GOLDEN / 128 | hors-v3 | 25.062 | 15.152 | 12.531 |
| DRAGON GOLDEN / 128 | hors-v4-gmod3 | 25.062 | **15.246** | 12.531 |
| DRAGON GREEN / 128 | hors-v3 | 25.062 | 15.142 | 12.531 |
| DRAGON GREEN / 128 | hors-v4-gmod3 | 25.062 | **15.246** | 12.531 |
| DRAGON METALLIC / 128 | hors-v3 | 25.062 | 15.152 | 12.531 |
| DRAGON METALLIC / 128 | hors-v4-gmod3 | 25.062 | **15.246** | 12.531 |
| DRAGON RED / 128 | hors-v3 | 25.062 | 15.121 | 12.531 |
| DRAGON RED / 128 | hors-v4-gmod3 | 25.062 | **15.215** | 12.531 |
| DRAGON WIREFRAME / 128 | hors-v3 | 50.125 | 19.904 | 16.708 |
| DRAGON WIREFRAME / 128 | hors-v4-gmod3 | 50.125 | **20.050** | 16.708 |

### Original demos and HiFi variants

| Scene | Method | High FPS | Average FPS | Low FPS |
| --- | --- | ---: | ---: | ---: |
| FALLING CUBES (mono) / 18 | hors-v3 | 50.125 | 28.999 | 16.708 |
| FALLING CUBES (mono) / 18 | hors-v4-gmod3 | 50.125 | **29.250** | 16.708 |
| FALLING CUBES (colour) / 18 | hors-v3 | 50.125 | 21.846 | 16.708 |
| FALLING CUBES (colour) / 18 | hors-v4-gmod3 | 50.125 | **22.003** | 16.708 |
| TORUS / 32 | hors-v3 | 25.062 | 18.421 | 12.531 |
| TORUS / 32 | hors-v4-gmod3 | 25.062 | **18.567** | 12.531 |
| TORUS DENSE / 32 | hors-v3 | 25.062 | 18.024 | 12.531 |
| TORUS DENSE / 32 | hors-v4-gmod3 | 25.062 | **18.170** | 12.531 |
| CUBE / 36 | hors-v3 | 50.125 | 30.795 | 25.062 |
| CUBE / 36 | hors-v4-gmod3 | 50.125 | **31.067** | 25.062 |
| SPHERE / 24 | hors-v3 | 25.062 | 17.867 | 16.708 |
| SPHERE / 24 | hors-v4-gmod3 | 25.062 | **18.014** | 16.708 |
| HORSE HEAD / 32 | hors-v3 | 50.125 | 30.837 | 25.062 |
| HORSE HEAD / 32 | hors-v4-gmod3 | 50.125 | **31.119** | 25.062 |
| SUNFLOWER TORUS / 28 | hors-v3 | 50.125 | 30.064 | 16.708 |
| SUNFLOWER TORUS / 28 | hors-v4-gmod3 | 50.125 | **30.336** | 16.708 |
| SUNFLOWER COLOR / 20 | hors-v3 | 50.125 | 23.485 | 16.708 |
| SUNFLOWER COLOR / 20 | hors-v4-gmod3 | 50.125 | **23.663** | 16.708 |
| SPACE HORSE SPIN / 24 | hors-v3 | 50.125 | 20.227 | 12.531 |
| SPACE HORSE SPIN / 24 | hors-v4-gmod3 | 50.125 | **20.405** | 12.531 |
| SPACE HORSE CRAWL / 32 | hors-v3 | 50.125 | 42.178 | 25.062 |
| SPACE HORSE CRAWL / 32 | hors-v4-gmod3 | 50.125 | **42.188** | 25.062 |
| HORSE HEAD HIFI / 128 | hors-v3 | 50.125 | 23.934 | 16.708 |
| HORSE HEAD HIFI / 128 | hors-v4-gmod3 | 50.125 | **24.112** | 16.708 |
| SUNFLOWER TORUS HIFI / 128 | hors-v3 | 50.125 | 23.590 | 16.708 |
| SUNFLOWER TORUS HIFI / 128 | hors-v4-gmod3 | 50.125 | **23.799** | 16.708 |
| TORUS BLACK ON WHITE / 32 | hors-v3 | 25.062 | 18.421 | 12.531 |
| TORUS BLACK ON WHITE / 32 | hors-v4-gmod3 | 25.062 | **18.567** | 12.531 |
| DENSE TORUS CYAN ON BLUE / 32 | hors-v3 | 25.062 | 18.024 | 12.531 |
| DENSE TORUS CYAN ON BLUE / 32 | hors-v4-gmod3 | 25.062 | **18.170** | 12.531 |
| SPHERE LIGHT GREEN ON BLACK / 24 | hors-v3 | 25.062 | 17.867 | 16.708 |
| SPHERE LIGHT GREEN ON BLACK / 24 | hors-v4-gmod3 | 25.062 | **18.014** | 16.708 |
| CUBE WHITE ON PURPLE / 36 | hors-v3 | 50.125 | 30.795 | 25.062 |
| CUBE WHITE ON PURPLE / 36 | hors-v4-gmod3 | 50.125 | **31.077** | 25.062 |
| CUBE / 192 | hors-v3 | 50.125 | 30.733 | 25.062 |
| CUBE / 192 | hors-v4-gmod3 | 50.125 | **30.994** | 25.062 |
| HORSE HEAD HIFI / 192 | hors-v3 | 50.125 | 23.924 | 16.708 |
| HORSE HEAD HIFI / 192 | hors-v4-gmod3 | 50.125 | **24.102** | 16.708 |
| HORSE HEAD / 192 | hors-v3 | 50.125 | 30.670 | 16.708 |
| HORSE HEAD / 192 | hors-v4-gmod3 | 50.125 | **31.025** | 16.708 |
| SPACE HORSE CRAWL / 192 | hors-v3 | 50.125 | 41.593 | 16.708 |
| SPACE HORSE CRAWL / 192 | hors-v4-gmod3 | 50.125 | **41.812** | 16.708 |
| SPACE HORSE / 192 | hors-v3 | 50.125 | 19.914 | 12.531 |
| SPACE HORSE / 192 | hors-v4-gmod3 | 50.125 | **20.050** | 12.531 |
| SPHERE / 192 | hors-v3 | 25.062 | 17.857 | 16.708 |
| SPHERE / 192 | hors-v4-gmod3 | 25.062 | **18.003** | 16.708 |
| SUNFLOWER TORUS (mono) / 192 | hors-v3 | 50.125 | 30.002 | 16.708 |
| SUNFLOWER TORUS (mono) / 192 | hors-v4-gmod3 | 50.125 | **30.221** | 16.708 |
| SUNFLOWER TORUS (colour) / 192 | hors-v3 | 50.125 | 23.256 | 16.708 |
| SUNFLOWER TORUS (colour) / 192 | hors-v4-gmod3 | 50.125 | **23.444** | 16.708 |
| TORUS / 192 | hors-v3 | 25.062 | 18.337 | 12.531 |
| TORUS / 192 | hors-v4-gmod3 | 25.062 | **18.515** | 12.531 |
| DENSE TORUS / 192 | hors-v3 | 50.125 | 18.014 | 12.531 |
| DENSE TORUS / 192 | hors-v4-gmod3 | 50.125 | **18.139** | 12.531 |

### Blender scenes

| Scene | Method | High FPS | Average FPS | Low FPS |
| --- | --- | ---: | ---: | ---: |
| BLENDER TRACKING TEST / 16 | hors-v3 | 8.354 | 7.968 | 7.161 |
| BLENDER TRACKING TEST / 16 | hors-v4-gmod3 | 10.025 | **8.030** | 7.161 |
| BLENDER VIEWPORT TEST / 16 | hors-v3 | 12.531 | 8.083 | 6.266 |
| BLENDER VIEWPORT TEST / 16 | hors-v4-gmod3 | 12.531 | **8.156** | 6.266 |
| HORSE AND SUNFLOWER (HiFi reel) / 84 | hors-v3 | 10.025 | 8.740 | 8.354 |
| HORSE AND SUNFLOWER (HiFi reel) / 84 | hors-v4-gmod3 | 10.025 | **8.803** | 8.354 |
| HORSE AND SUNFLOWER (authored scene) / 84 | hors-v3 | 10.025 | 8.740 | 8.354 |
| HORSE AND SUNFLOWER (authored scene) / 84 | hors-v4-gmod3 | 10.025 | **8.803** | 8.354 |

### Demo Cart 2.0

| Scene | Method | High FPS | Average FPS | Low FPS |
| --- | --- | ---: | ---: | ---: |
| COLOUR CUBE 24 / 24 | hors-v3 | 50.125 | 38.053 | 25.062 |
| COLOUR CUBE 24 / 24 | hors-v4-gmod3 | 50.125 | **38.335** | 25.062 |
| COLOUR TORUS 18 / 18 | hors-v3 | 50.125 | 23.559 | 16.708 |
| COLOUR TORUS 18 / 18 | hors-v4-gmod3 | 50.125 | **23.736** | 16.708 |
| TWIST TUNNEL / 48 | hors-v3 | 12.531 | 12.134 | 10.025 |
| TWIST TUNNEL / 48 | hors-v4-gmod3 | 12.531 | **12.228** | 10.025 |
| RIBBON DANCE / 48 | hors-v3 | 50.125 | 47.545 | 25.062 |
| RIBBON DANCE / 48 | hors-v4-gmod3 | 50.125 | **47.942** | 25.062 |
| ORBITAL CUBES / 48 | hors-v3 | 50.125 | 35.045 | 25.062 |
| ORBITAL CUBES / 48 | hors-v4-gmod3 | 50.125 | **35.317** | 25.062 |
| WAVE LATTICE / 48 | hors-v3 | 50.125 | 28.989 | 16.708 |
| WAVE LATTICE / 48 | hors-v4-gmod3 | 50.125 | **29.198** | 16.708 |
| RIPPLES LITE / 100 | hors-v3 | 25.062 | 15.768 | 12.531 |
| RIPPLES LITE / 100 | hors-v4-gmod3 | 25.062 | **15.915** | 12.531 |

### Marbles: all five segments

| Scene | Method | High FPS | Average FPS | Low FPS |
| --- | --- | ---: | ---: | ---: |
| DON'T LOSE YOUR MARBLES [1..128] / 128 | hors-v3 | 50.125 | 19.998 | 16.708 |
| DON'T LOSE YOUR MARBLES [1..128] / 128 | hors-v4-gmod3 | 50.125 | **20.154** | 16.708 |
| DON'T LOSE YOUR MARBLES [129..256] / 128 | hors-v3 | 25.062 | 19.194 | 16.708 |
| DON'T LOSE YOUR MARBLES [129..256] / 128 | hors-v4-gmod3 | 25.062 | **19.329** | 16.708 |
| DON'T LOSE YOUR MARBLES [257..384] / 128 | hors-v3 | 25.062 | 18.557 | 16.708 |
| DON'T LOSE YOUR MARBLES [257..384] / 128 | hors-v4-gmod3 | 25.062 | **18.682** | 16.708 |
| DON'T LOSE YOUR MARBLES [385..512] / 128 | hors-v3 | 25.062 | 18.828 | 16.708 |
| DON'T LOSE YOUR MARBLES [385..512] / 128 | hors-v4-gmod3 | 25.062 | **18.953** | 16.708 |
| DON'T LOSE YOUR MARBLES [513..640] / 128 | hors-v3 | 50.125 | 14.390 | 8.354 |
| DON'T LOSE YOUR MARBLES [513..640] / 128 | hors-v4-gmod3 | 50.125 | **14.505** | 8.354 |

### Sande's Pretzel

| Scene | Method | High FPS | Average FPS | Low FPS |
| --- | --- | ---: | ---: | ---: |
| PRETZEL WIRE-COLOR / 192 | hors-v3 | 25.062 | 17.961 | 12.531 |
| PRETZEL WIRE-COLOR / 192 | hors-v4-gmod3 | 25.062 | **18.097** | 12.531 |
| PRETZEL WIRE-INTERACTIVE / 192 | hors-v3 | 25.062 | 17.961 | 12.531 |
| PRETZEL WIRE-INTERACTIVE / 192 | hors-v4-gmod3 | 25.062 | **18.097** | 12.531 |
| PRETZEL DITHER / 128 | hors-v3 | 25.062 | 18.452 | 12.531 |
| PRETZEL DITHER / 128 | hors-v4-gmod3 | 25.062 | **18.609** | 16.708 |
| PRETZEL MATERIAL / 128 | hors-v3 | 25.062 | 18.222 | 12.531 |
| PRETZEL MATERIAL / 128 | hors-v4-gmod3 | 25.062 | **18.389** | 12.531 |
| PRETZEL METALLIC / 128 | hors-v3 | 16.708 | 14.682 | 12.531 |
| PRETZEL METALLIC / 128 | hors-v4-gmod3 | 25.062 | **14.787** | 12.531 |
| PRETZEL METALLIC / 192 / indexed4 | hors-v3 | 16.708 | 12.448 | 10.025 |
| PRETZEL METALLIC / 192 / indexed4 | hors-v4-gmod3 | 16.708 | **12.531** | 10.025 |
| PRETZEL TEXTURED / 128 | hors-v3 | 16.708 | 14.703 | 12.531 |
| PRETZEL TEXTURED / 128 | hors-v4-gmod3 | 16.708 | **14.808** | 12.531 |
| PRETZEL WIRE-BW / 128 | hors-v3 | 25.062 | 17.972 | 12.531 |
| PRETZEL WIRE-BW / 128 | hors-v4-gmod3 | 25.062 | **18.118** | 12.531 |

### Sande's TAC-2 joystick

| Scene | Method | High FPS | Average FPS | Low FPS |
| --- | --- | ---: | ---: | ---: |
| TAC-2 COLOUR / 192 | hors-v3 | 25.062 | 20.551 | 16.708 |
| TAC-2 COLOUR / 192 | hors-v4-gmod3 | 25.062 | **20.708** | 16.708 |
| TAC-2 WIRE / 192 | hors-v3 | 50.125 | 24.582 | 16.708 |
| TAC-2 WIRE / 192 | hors-v4-gmod3 | 50.125 | **24.801** | 16.708 |

### Actual All-in-One interactive defaults

Historical v0.8.0 / Demo Cart v3.0 measurements. For the v0.8.1 / v3.1 interactive hotfix, see [the fresh A/B tables](INTERACTIVE_BASELINE_PERFORMANCE.md).

These figures include the collection navigation, the complete interactive runtime, HUD and disabled-but-available starfield. Authored pacing remains enabled where supplied. They are not mixed into the automatic A/B ranking above. Each entry is individually checked with the final cartridge hash; SAKU starts in gradient-spin mode with stars off.

| Entry | Scene / stored samples | High FPS | Average FPS | Low FPS | Allocated KiB |
| ---: | --- | ---: | ---: | ---: | ---: |
| 1 | SAKU 2026 INTERACTIVE / 240 | 25.062 | 18.191 | 16.708 | 432 |
| 2 | DRAGON BLUE / 128 | 25.062 | 14.661 | 12.531 | 344 |
| 3 | DRAGON GOLDEN / 128 | 25.062 | 14.661 | 12.531 | 344 |
| 4 | DRAGON GREEN / 128 | 25.062 | 14.661 | 12.531 | 344 |
| 5 | DRAGON METALLIC / 128 | 25.062 | 14.661 | 12.531 | 344 |
| 6 | DRAGON RED / 128 | 25.062 | 14.641 | 12.531 | 336 |
| 7 | DRAGON WIREFRAME / 128 | 50.125 | 19.173 | 12.531 | 288 |
| 8 | FALLING CUBES / 18 | 50.125 | 27.422 | 16.708 | 48 |
| 9 | FALLING CUBES / 18 | 25.062 | 20.802 | 16.708 | 48 |
| 10 | BLENDER TRACKING TEST / 16 | 8.354 | 7.811 | 7.161 | 88 |
| 11 | BLENDER VIEWPORT TEST / 16 | 10.025 | 7.936 | 6.266 | 96 |
| 12 | TORUS / 32 | 25.062 | 17.773 | 12.531 | 80 |
| 13 | TORUS DENSE / 32 | 25.062 | 17.397 | 12.531 | 80 |
| 14 | CUBE / 36 | 50.125 | 29.030 | 25.062 | 56 |
| 15 | SPHERE / 24 | 25.062 | 17.272 | 16.708 | 64 |
| 16 | HORSE HEAD / 32 | 50.125 | 29.093 | 16.708 | 56 |
| 17 | SUNFLOWER TORUS / 28 | 50.125 | 28.383 | 16.708 | 56 |
| 18 | SUNFLOWER COLOR / 20 | 50.125 | 22.347 | 16.708 | 56 |
| 19 | SPACE HORSE SPIN / 24 | 50.125 | 19.465 | 12.531 | 64 |
| 20 | SPACE HORSE CRAWL / 32 | 50.125 | 41.081 | 25.062 | 48 |
| 21 | HORSE HEAD HIFI / 128 | 50.125 | 22.807 | 16.708 | 208 |
| 22 | SUNFLOWER TORUS HIFI / 128 | 50.125 | 22.473 | 16.708 | 200 |
| 23 | COLOUR CUBE 24 / 24 | 50.125 | 34.983 | 25.062 | 40 |
| 24 | COLOUR TORUS 18 / 18 | 25.062 | 22.431 | 16.708 | 48 |
| 25 | TWIST TUNNEL / 48 | 12.531 | 11.821 | 10.025 | 152 |
| 26 | RIBBON DANCE / 48 | 50.125 | 43.295 | 25.062 | 56 |
| 27 | ORBITAL CUBES / 48 | 50.125 | 32.602 | 25.062 | 64 |
| 28 | WAVE LATTICE / 48 | 50.125 | 27.297 | 16.708 | 80 |
| 29 | RIPPLES LITE / 100 | 16.708 | 15.330 | 12.531 | 224 |
| 30 | HORSE AND SUNFLOWER / 84 | 10.025 | 8.563 | 7.161 | 360 |
| 31 | HORSE AND SUNFLOWER / 84 | 10.025 | 8.354 | 8.354 | 360 |
| 32 | DON'T LOSE YOUR MARBLES / 640 | 25.062 | 15.100 | 8.354 | 1384 |
| 33 | TORUS BLACK ON WHITE / 32 | 25.062 | 17.752 | 12.531 | 80 |
| 34 | DENSE TORUS CYAN ON BLUE / 32 | 25.062 | 17.377 | 12.531 | 80 |
| 35 | SPHERE LIGHT GREEN ON BLACK / 24 | 25.062 | 17.272 | 16.708 | 64 |
| 36 | CUBE WHITE ON PURPLE / 36 | 50.125 | 28.947 | 25.062 | 56 |
| 37 | CUBE / 192 | 50.125 | 28.947 | 25.062 | 200 |
| 38 | PRETZEL WIRE-COLOR / 192 | 25.062 | 17.377 | 12.531 | 480 |
| 39 | PRETZEL WIRE-INTERACTIVE / 192 | 25.062 | 17.377 | 12.531 | 480 |
| 40 | TAC-2 COLOUR / 192 | 25.062 | 19.695 | 16.708 | 336 |
| 41 | TAC-2 WIRE / 192 | 25.062 | 23.454 | 16.708 | 280 |
| 42 | HORSE HEAD HIFI / 192 | 50.125 | 22.828 | 16.708 | 304 |
| 43 | PRETZEL DITHER / 128 | 25.062 | 17.794 | 12.531 | 312 |
| 44 | PRETZEL MATERIAL / 128 | 25.062 | 17.585 | 12.531 | 320 |
| 45 | PRETZEL METALLIC / 128 | 16.708 | 14.244 | 12.531 | 360 |
| 46 | PRETZEL METALLIC / 192 | 16.708 | 14.223 | 12.531 | 528 |
| 47 | PRETZEL TEXTURED / 128 | 16.708 | 14.265 | 12.531 | 360 |
| 48 | PRETZEL WIRE-BW / 128 | 25.062 | 17.356 | 12.531 | 328 |
| 49 | HORSE HEAD / 192 | 50.125 | 28.905 | 16.708 | 224 |
| 50 | SAKU GRADIENT / 48 | 50.125 | 30.994 | 25.062 | 72 |
| 51 | SAKU SOLID / 48 | 50.125 | 31.892 | 25.062 | 72 |
| 52 | SPACE HORSE CRAWL / 192 | 50.125 | 40.100 | 16.708 | 160 |
| 53 | SPACE HORSE / 192 | 50.125 | 19.277 | 12.531 | 344 |
| 54 | SPHERE / 192 | 25.062 | 17.251 | 16.708 | 336 |
| 55 | SUNFLOWER TORUS / 192 | 50.125 | 28.320 | 16.708 | 240 |
| 56 | SUNFLOWER TORUS / 192 | 50.125 | 22.138 | 16.708 | 288 |
| 57 | TORUS / 192 | 25.062 | 17.732 | 12.531 | 336 |
| 58 | DENSE TORUS / 192 | 25.062 | 17.418 | 12.531 | 352 |

There is one method in this inventory table, so no cross-scene “winner” is highlighted. Different scenes contain different work. The interactive cart uses 13,448 KiB and leaves 2,936 KiB free; its automatic companion uses 13,416 KiB and leaves 2,968 KiB.

### Reproduce these results

```sh
# These historical interactive measurements use the preserved v3.0 CRT.
python tools/compare_gmod3_catalog.py --tass 64tass --cartconv cartconv --vice x64sc --vice-data /path/to/vice/data
python tools/verify_gmod3_collection.py examples/gmod3_cart_demos/demo-cart-v3.0-gmod3-all-in-one.crt --vice x64sc --vice-data /path/to/vice/data --output docs/benchmarks/gmod3-collection/interactive
python tools/report_gmod3_performance.py
python tools/report_gmod3_performance.py --check
```

Historical matrices elsewhere on this page retain their original protocols and measured cartridge versions. Their figures are not relabelled as new HORS-V4 measurements.
<!-- hors-v4-results-sha256: 4982a4d3a215ea04920b8b8be6030f3ff45f00d151cf1f3a96651d4e9998bc38 -->
<!-- END HORS-V4 GMOD3 -->


## Best method for each animation (historical PLAY ALL)

| Animation | Source samples | Best method(s), FPS preference | Display FPS | V9 vs V8 displayed frames | HORS v2 vs v1 displayed frames |
| --- | ---: | --- | ---: | ---: | ---: |
| TORUS | 32 | hors-v2, hors-v3 | **17.68** | +0.00% | +10.00% |
| TORUS DENSE | 32 | hors-v2, hors-v3 | **17.18** | +0.00% | +8.92% |
| CUBE | 36 | yunroll, cart scaffold | **30.27** | +0.00% | +9.52% |
| SPHERE | 24 | hors-v2, hors-v3 | **17.38** | +0.00% | +9.49% |
| HORSE HEAD | 32 | hors-v2, hors-v3 | **29.34** | +0.73% | +6.96% |
| SUNFLOWER TORUS | 28 | hors-v2, hors-v3 | **28.73** | +0.00% | +5.93% |
| SUNFLOWER COLOR | 20 | hors-v3 | **22.70** | +0.96% | +4.52% |
| SPACE HORSE SPIN | 24 | hors-v2, hors-v3 | **19.08** | +0.94% | +8.57% |
| SPACE HORSE CRAWL | 32 | hors-v2, hors-v3 | **38.27** | +2.63% | +7.63% |
| FALLING CUBES | 18 | hors-v3 | **21.30** | +0.00% | +6.12% |
| HORSE HEAD HIFI | 128 | hors-v3 | **23.10** | +0.99% | +3.88% |
| SUNFLOWER TORUS HIFI | 128 | hors-v3 | **22.70** | +16.13% | +2.53% |

**Bold FPS values** mark the highest value within each comparable row or workload group, using average FPS only. **(tie)** marks equal values at the displayed precision. Storage sizes are not ranked as FPS wins. The best-method summary uses actual displayed-frame counts; brief peak bursts do not establish sustained speed.


## Demo Cart 2.0

The seven-scene showcase has its own **hors-v1 vs hors-v2** comparison. Both methods use identical complete source pictures, colours and sample order. PAL VICE, FPS preference, normal PLAY ALL, three ten-second visits per entry. F5 is excluded.

These are the measured shipped showcase cartridges, with their per-scene encoding policy. This is a separate workload from the original twelve-animation matrix; the COLOUR CUBE 24 here is not its CUBE or FALLING CUBES entry. Gains rank displayed-frame counts rather than tiny timer-phase differences.

| Scene | Samples | v1 FPS | v2 FPS | Gain | v1 worst display ms | v2 worst display ms |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| COLOUR CUBE 24 | 24 | 32.45 | **35.56** | +9.60% | 43.90 | 42.71 |
| COLOUR TORUS 18 | 18 | 18.38 | **19.99** | +8.74% | 79.80 | 62.59 |
| TWIST TUNNEL | 48 | 9.14 | **9.94** | +8.79% | 119.72 | 119.70 |
| RIBBON DANCE | 48 | 31.64 | **33.45** | +5.71% | 44.34 | 44.42 |
| ORBITAL CUBES | 48 | 28.73 | **31.45** | +9.44% | 44.07 | 44.09 |
| WAVE LATTICE | 48 | 22.00 | **24.81** | +12.79% | 64.27 | 63.07 |
| RIPPLES LITE | 100 | 12.46 | **16.88** | +35.48% | 99.75 | 79.80 |

All seven entries passed bitmap and colour checks for both methods. Worst intervals describe the observed window; a higher average FPS does not guarantee a lower worst interval.

[Demo Cart 2.0 and source scenes](../examples/cart_demos_v2/README.md) · [v1 raw results](benchmarks/hors-v2/showcase/v1/play-all.json) · [v2 raw results](benchmarks/hors-v2/showcase/v2/play-all.json) · [Release and HiFi results](HORS_RENDER_V2_RESULTS.md)

The chart fingerprint includes both reports and the shipped v2 CRT; generation verifies their cartridge hash and matching picture oracles. The release/check runner refreshes the showcase evidence before generating this page.


## Sande's Models

Models contributed by **Sande**: **Sande's Pretzel** and **Sande's TAC-2 joystick**. This is a separate workload from the original twelve animations and Demo Cart 2.0.

Each standalone cart uses the complete OBJ topology, white-on-black output, 192 Y-axis orientations, automatic surface visibility, the normal HUD and uncapped playback. V1/V2 and FPS/RAM builds use identical picture oracles. PAL VICE measures actual display-slot changes after each raster IRQ; every observed bitmap, colour matrix and Sande HUD is checked. The initial full-loop warmup is excluded.


#### Sande's Pretzel

| V / E | Renderer | Preference | High FPS | Average FPS | Low FPS | CRT bytes | Frame data ROM bytes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1552 / 3104 | hors-v1 | fps | 25.82 | 17.30 | 12.53 | 492,544 | 389,676 |
| 1552 / 3104 | hors-v1 | ram | 25.82 | 17.30 | 12.53 | 492,544 | 389,676 |
| 1552 / 3104 | hors-v2 | fps | 25.71 | **18.00 (tie)** | 12.53 | 500,752 | 392,010 |
| 1552 / 3104 | hors-v2 | ram | 25.71 | **18.00 (tie)** | 12.53 | 500,752 | 392,010 |

#### Sande's TAC-2 joystick

| V / E | Renderer | Preference | High FPS | Average FPS | Low FPS | CRT bytes | Frame data ROM bytes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 178 / 344 | hors-v1 | fps | 26.50 | 21.86 | 16.13 | 287,344 | 235,981 |
| 178 / 344 | hors-v1 | ram | 26.50 | 21.86 | 16.13 | 287,344 | 235,981 |
| 178 / 344 | hors-v2 | fps | 54.49 | **24.60 (tie)** | 16.29 | 295,552 | 240,004 |
| 178 / 344 | hors-v2 | ram | 54.49 | **24.60 (tie)** | 16.29 | 295,552 | 240,004 |


### Interactive path, no input

The separate interactive v2/FPS builds poll the keyboard and both joystick ports once per produced sample. These rows include the top-right INTERACTIVE label and measure their cost with no control held, using the same source pictures and observation window. The label is checked separately over the model oracle.


#### Sande's Pretzel

| Automatic FPS | Interactive idle FPS | Change |
| --- | --- | --- |
| **18.00** | 17.50 | -2.77% |

#### Sande's TAC-2 joystick

| Automatic FPS | Interactive idle FPS | Change |
| --- | --- | --- |
| **24.60** | 23.73 | -3.53% |


### Interactive palette cycling

F5 toggles sequential colour changes, alternating foreground and background. F6 slows the rate; F7 speeds it up. F8 toggles a persistent black border or background-follow mode (the default); Ctrl+F7 selects an independent border colour. F2 flashes white briefly and resets. Cycling uses the existing PAL tick counter; palette writes run only on a change event. The fastest setting requests one change per PAL tick but is limited to one event per produced frame.


#### Sande's Pretzel

| Cycle setting | High FPS | Average FPS | Low FPS | Change versus interactive idle |
| --- | --- | --- | --- | --- |
| Default: about 1 s per change | 26.20 | **17.14** | 10.02 | -2.07% |
| Fastest: at most once per produced frame | 20.18 | 13.26 | 10.48 | -24.21% |

#### Sande's TAC-2 joystick

| Cycle setting | High FPS | Average FPS | Low FPS | Change versus interactive idle |
| --- | --- | --- | --- | --- |
| Default: about 1 s per change | 26.48 | **23.30** | 12.37 | -1.79% |
| Fastest: at most once per produced frame | 25.06 | 16.60 | 12.53 | -30.03% |


All cases use 1,504 PAL refresh intervals per observation window (approximately 30.01 seconds). Average FPS is displayed frames divided by emulated elapsed time. High/low are interval extrema, not sustained rates. A difference below one flip per window is within measurement granularity.

**V/E are source-mesh totals, not runtime transformations or a count of visible lines drawn each frame.** Projection and visibility are computed offline; hors-v2 draws precomputed bitmap spans. No mesh simplification or orientation reduction is used. These are emulator measurements, not physical-hardware results.

[Sande models, carts and reproduction](../examples/demos_sande/README.md) · [Raw Sande measurements](benchmarks/sande/summary.json)

```bash
python tools/run_sande_perfs.py --workspace ../c64-sande-perfs --vice-data /usr/local/share/vice
```

The Sande benchmark is also part of `RUN-CHECKS.sh`. Its checked report, source hashes and shipped cart hashes are verified when this page is generated and by `--check`.

### Standalone material-colour variants

These separate `-color` carts use the original MTL diffuse colours with the same 192 Y-axis orientations, visibility and gap-6 encoding recipe as the bw defaults. Pretzel maps to dark grey; TAC-2 retains red, white and greys. The measurements use the same PAL display-slot and complete-picture checks as the bw table.


#### Sande's Pretzel

| Renderer | Preference | High FPS | Average FPS | Low FPS | CRT bytes | Frame data ROM bytes |
| --- | --- | --- | --- | --- | --- | --- |
| hors-v1 | fps | 25.82 | 17.30 | 12.53 | 492,544 | 389,676 |
| hors-v1 | ram | 25.82 | 17.30 | 12.53 | 492,544 | 389,676 |
| hors-v2 | fps | 25.71 | **18.00 (tie)** | 12.53 | 500,752 | 392,010 |
| hors-v2 | ram | 25.71 | **18.00 (tie)** | 12.53 | 500,752 | 392,010 |

#### Sande's TAC-2 joystick

| Renderer | Preference | High FPS | Average FPS | Low FPS | CRT bytes | Frame data ROM bytes |
| --- | --- | --- | --- | --- | --- | --- |
| hors-v1 | fps | 28.19 | 16.93 | 12.53 | 328,384 | 270,153 |
| hors-v1 | ram | 28.19 | 16.93 | 12.53 | 328,384 | 270,153 |
| hors-v2 | fps | 28.02 | **18.53 (tie)** | 15.61 | 336,592 | 274,176 |
| hors-v2 | ram | 28.02 | **18.53 (tie)** | 15.61 | 336,592 | 274,176 |


Shared colour-test window: 1,504 PAL refresh intervals; high/low are interval extrema, not sustained rates.

[Raw material-colour measurements](benchmarks/sande/summary-color.json)

```bash
python tools/run_sande_perfs.py --source-colors --workspace ../c64-sande-color-perfs --vice-data /usr/local/share/vice
```


### Sande bw models across renderer methods

This matrix uses the same isolated **normal PLAY ALL** harness as the original renderer comparison: three ten-second visits per model, all 192 orientations, no controls and no FPS cap. Each model gets its own comparison cart so another model cannot consume its cartridge budget. V2 uses the canonical comparison encoder settings (gap 3, batch budget 2048); the standalone carts above use gap 6. Menu/controller cost and encoding settings mean these rates should be compared within this matrix.

`hors-v1` is the public name for `yunroll-cart-v10`. N/A is a recorded capacity failure with the original data, never a simplified substitute.

#### Sande's Pretzel

| Method | Preference | High FPS | Average FPS | Low FPS | Frame-table RAM (B) | Frame data ROM (B) |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| step | fps | N/A | N/A | N/A | N/A | N/A |
| bytechunk | fps | N/A | N/A | N/A | N/A | N/A |
| yunroll | fps | N/A | N/A | N/A | N/A | N/A |
| yunroll-cart | fps | N/A | N/A | N/A | N/A | N/A |
| yunroll-cart-v2 | fps | N/A | N/A | N/A | N/A | N/A |
| yunroll-cart-v3 | fps | N/A | N/A | N/A | N/A | N/A |
| yunroll-cart-v4 | fps | N/A | N/A | N/A | N/A | N/A |
| yunroll-cart-v5 | fps | N/A | N/A | N/A | N/A | N/A |
| yunroll-cart-v6 | fps | N/A | N/A | N/A | N/A | N/A |
| yunroll-cart-v7 | fps | 3.15 | 2.91 | 2.78 | 0 | 504,239 |
| yunroll-cart-v8 | fps | 17.53 | 10.95 | 9.76 | 0 | 389,676 |
| yunroll-cart-v9 | fps | 26.26 | 17.38 | 12.53 | 0 | 389,676 |
| hors-v1 (v10) | fps | 26.26 | 17.38 | 12.53 | 0 | 389,676 |
| yunroll-cart-v7 | ram | 2.96 | 2.71 | 2.64 | 0 | 504,239 |
| yunroll-cart-v8 | ram | 17.53 | 10.95 | 9.91 | 0 | 389,676 |
| yunroll-cart-v9 | ram | 25.79 | 17.38 | 12.53 | 0 | 389,676 |
| hors-v1 (v10) | ram | 25.79 | 17.38 | 12.53 | 0 | 389,676 |
| hors-v2 | fps | 26.02 | **17.58 (tie)** | 12.53 | 0 | 389,676 |
| hors-v2 | ram | 25.74 | 17.48 | 12.53 | 0 | 389,676 |
| hors-v3 | fps | 26.02 | **17.58 (tie)** | 12.53 | 0 | 389,676 |
| hors-v3 | ram | 25.74 | 17.48 | 12.53 | 0 | 389,676 |

Recorded capacity limits:

- `step` (fps): resident record count exceeds 255
- `bytechunk` (fps): resident record count exceeds 255
- `yunroll` (fps): resident record count exceeds 255
- `yunroll-cart` (fps): resident record count exceeds 255
- `yunroll-cart-v2` (fps): frame block 8654 exceeds 8192-byte staging buffer
- `yunroll-cart-v3` (fps): frame block 8654 exceeds 8192-byte staging buffer
- `yunroll-cart-v4` (fps): frame block 8654 exceeds 8192-byte staging buffer
- `yunroll-cart-v5` (fps): uniform demo frames exceed EasyFlash capacity; samples were not reduced
- `yunroll-cart-v6` (fps): uniform demo frames exceed EasyFlash capacity; samples were not reduced

#### Sande's TAC-2 joystick

| Method | Preference | High FPS | Average FPS | Low FPS | Frame-table RAM (B) | Frame data ROM (B) |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| step | fps | N/A | N/A | N/A | N/A | N/A |
| bytechunk | fps | N/A | N/A | N/A | N/A | N/A |
| yunroll | fps | N/A | N/A | N/A | N/A | N/A |
| yunroll-cart | fps | N/A | N/A | N/A | N/A | N/A |
| yunroll-cart-v2 | fps | 6.25 | 5.42 | 4.93 | 0 | 315,789 |
| yunroll-cart-v3 | fps | 7.23 | 6.13 | 5.48 | 0 | 315,789 |
| yunroll-cart-v4 | fps | 7.24 | 6.23 | 5.49 | 0 | 315,789 |
| yunroll-cart-v5 | fps | 8.61 | 7.33 | 6.24 | 0 | 253,516 |
| yunroll-cart-v6 | fps | 8.56 | 7.60 | 7.02 | 0 | 253,516 |
| yunroll-cart-v7 | fps | 10.32 | 9.04 | 8.16 | 0 | 180,514 |
| yunroll-cart-v8 | fps | 10.32 | 9.04 | 8.16 | 0 | 180,514 |
| yunroll-cart-v9 | fps | 10.31 | 9.14 | 8.17 | 0 | 180,514 |
| hors-v1 (v10) | fps | 51.63 | 21.69 | 16.14 | 0 | 235,981 |
| yunroll-cart-v7 | ram | 10.31 | 8.54 | 7.06 | 0 | 180,514 |
| yunroll-cart-v8 | ram | 10.31 | 8.54 | 7.06 | 0 | 180,514 |
| yunroll-cart-v9 | ram | 10.30 | 8.54 | 7.05 | 0 | 180,514 |
| hors-v1 (v10) | ram | 50.32 | 21.63 | 16.17 | 0 | 235,981 |
| hors-v2 | fps | 54.44 | **23.20 (tie)** | 16.16 | 0 | 235,981 |
| hors-v2 | ram | 50.85 | **23.20 (tie)** | 16.15 | 0 | 235,981 |
| hors-v3 | fps | 54.44 | **23.20 (tie)** | 16.16 | 0 | 235,981 |
| hors-v3 | ram | 50.85 | **23.20 (tie)** | 16.15 | 0 | 235,981 |

Recorded capacity limits:

- `step` (fps): resident record count exceeds 255
- `bytechunk` (fps): resident record count exceeds 255
- `yunroll` (fps): resident record count exceeds 255
- `yunroll-cart` (fps): resident record count exceeds 255

[Raw historical Sande method results](benchmarks/sande/methods.json)

```bash
python tools/run_sande_methods.py --workspace ../c64-sande-methods --vice-data /usr/local/share/vice
```


### Sande material colours across renderer methods

This matrix uses the same isolated **normal PLAY ALL** harness as the original renderer comparison: three ten-second visits per model, all 192 orientations, no controls and no FPS cap. Each model gets its own comparison cart so another model cannot consume its cartridge budget. V2 uses the canonical comparison encoder settings (gap 3, batch budget 2048); the standalone carts above use gap 6. Menu/controller cost and encoding settings mean these rates should be compared within this matrix.

`hors-v1` is the public name for `yunroll-cart-v10`. N/A is a recorded capacity failure with the original data, never a simplified substitute.

#### Sande's Pretzel

| Method | Preference | High FPS | Average FPS | Low FPS | Frame-table RAM (B) | Frame data ROM (B) |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| step | fps | N/A | N/A | N/A | N/A | N/A |
| bytechunk | fps | N/A | N/A | N/A | N/A | N/A |
| yunroll | fps | N/A | N/A | N/A | N/A | N/A |
| yunroll-cart | fps | N/A | N/A | N/A | N/A | N/A |
| yunroll-cart-v2 | fps | N/A | N/A | N/A | N/A | N/A |
| yunroll-cart-v3 | fps | N/A | N/A | N/A | N/A | N/A |
| yunroll-cart-v4 | fps | N/A | N/A | N/A | N/A | N/A |
| yunroll-cart-v5 | fps | N/A | N/A | N/A | N/A | N/A |
| yunroll-cart-v6 | fps | N/A | N/A | N/A | N/A | N/A |
| yunroll-cart-v7 | fps | 3.15 | 2.91 | 2.78 | 0 | 504,239 |
| yunroll-cart-v8 | fps | 17.53 | 10.95 | 9.76 | 0 | 389,676 |
| yunroll-cart-v9 | fps | 26.26 | 17.38 | 12.53 | 0 | 389,676 |
| hors-v1 (v10) | fps | 26.26 | 17.38 | 12.53 | 0 | 389,676 |
| yunroll-cart-v7 | ram | 2.96 | 2.71 | 2.64 | 0 | 504,239 |
| yunroll-cart-v8 | ram | 17.53 | 10.95 | 9.91 | 0 | 389,676 |
| yunroll-cart-v9 | ram | 25.79 | 17.38 | 12.53 | 0 | 389,676 |
| hors-v1 (v10) | ram | 25.79 | 17.38 | 12.53 | 0 | 389,676 |
| hors-v2 | fps | 26.02 | **17.58 (tie)** | 12.53 | 0 | 389,676 |
| hors-v2 | ram | 25.74 | 17.48 | 12.53 | 0 | 389,676 |
| hors-v3 | fps | 26.02 | **17.58 (tie)** | 12.53 | 0 | 389,676 |
| hors-v3 | ram | 25.74 | 17.48 | 12.53 | 0 | 389,676 |

Recorded capacity limits:

- `step` (fps): resident record count exceeds 255
- `bytechunk` (fps): resident record count exceeds 255
- `yunroll` (fps): resident record count exceeds 255
- `yunroll-cart` (fps): resident record count exceeds 255
- `yunroll-cart-v2` (fps): frame block 8654 exceeds 8192-byte staging buffer
- `yunroll-cart-v3` (fps): frame block 8654 exceeds 8192-byte staging buffer
- `yunroll-cart-v4` (fps): frame block 8654 exceeds 8192-byte staging buffer
- `yunroll-cart-v5` (fps): uniform demo frames exceed EasyFlash capacity; samples were not reduced
- `yunroll-cart-v6` (fps): uniform demo frames exceed EasyFlash capacity; samples were not reduced

#### Sande's TAC-2 joystick

| Method | Preference | High FPS | Average FPS | Low FPS | Frame-table RAM (B) | Frame data ROM (B) |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| step | fps | N/A | N/A | N/A | N/A | N/A |
| bytechunk | fps | N/A | N/A | N/A | N/A | N/A |
| yunroll | fps | N/A | N/A | N/A | N/A | N/A |
| yunroll-cart | fps | N/A | N/A | N/A | N/A | N/A |
| yunroll-cart-v2 | fps | 5.68 | 4.92 | 4.51 | 0 | 349,961 |
| yunroll-cart-v3 | fps | 6.34 | 5.52 | 4.96 | 0 | 349,961 |
| yunroll-cart-v4 | fps | 6.32 | 5.63 | 4.95 | 0 | 349,961 |
| yunroll-cart-v5 | fps | 8.21 | 6.63 | 5.59 | 0 | 287,688 |
| yunroll-cart-v6 | fps | 8.54 | 6.93 | 6.12 | 0 | 287,688 |
| yunroll-cart-v7 | fps | 10.03 | 8.04 | 6.96 | 0 | 214,686 |
| yunroll-cart-v8 | fps | 10.03 | 8.04 | 6.96 | 0 | 214,686 |
| yunroll-cart-v9 | fps | 10.44 | 8.14 | 6.96 | 0 | 214,686 |
| hors-v1 (v10) | fps | 27.69 | 16.88 | 12.53 | 0 | 270,153 |
| yunroll-cart-v7 | ram | 8.64 | 7.63 | 6.97 | 0 | 214,686 |
| yunroll-cart-v8 | ram | 8.64 | 7.63 | 6.97 | 0 | 214,686 |
| yunroll-cart-v9 | ram | 8.65 | 7.63 | 6.96 | 0 | 214,686 |
| hors-v1 (v10) | ram | 27.83 | 16.88 | 12.53 | 0 | 270,153 |
| hors-v2 | fps | 50.14 | 17.78 | 15.66 | 0 | 270,153 |
| hors-v2 | ram | 27.29 | 17.78 | 15.84 | 0 | 270,153 |
| hors-v3 | fps | 50.27 | **19.59 (tie)** | 15.97 | 0 | 278,221 |
| hors-v3 | ram | 26.90 | **19.59 (tie)** | 15.98 | 0 | 278,221 |

Recorded capacity limits:

- `step` (fps): resident record count exceeds 255
- `bytechunk` (fps): resident record count exceeds 255
- `yunroll` (fps): resident record count exceeds 255
- `yunroll-cart` (fps): resident record count exceeds 255

[Raw historical Sande method results](benchmarks/sande/methods-color.json)

```bash
python tools/run_sande_methods.py --source-colors --workspace ../c64-sande-methods --vice-data /usr/local/share/vice
```


## HORS-V3 surfaces and textures

Sande’s complete Pretzel mesh, PAL VICE 3.10, 1,504-refresh windows. FPS counts actual display-buffer flips. These standalone workloads are separate from normal PLAY ALL. The V2 metallic row replays identical filled pictures through the unchanged V2 kernel as a comparison harness; V2 does not gain a surface-fill CLI.

| Workload | Orientations | Displayed FPS | Frame stream bytes | CRT bytes |
| --- | ---: | ---: | ---: | ---: |
| V2 wireframe, white | 128 | 17.96 | 261,277 | 344,800 |
| V3 wireframe, white | 128 | 17.96 | 261,277 | 344,800 |
| V3 MTL flat fill | 128 | 18.26 | 257,470 | 336,592 |
| V3 metallic, B/W dither | 128 | **18.46** | 252,089 | 328,384 |
| V2 kernel, same metallic pictures | 128 | 10.73 | 332,248 | 451,504 |
| V3 metallic, direct colours | 128 | 14.70 | 296,092 | 377,632 |
| V3 MTL image texture | 128 | 14.70 | 296,344 | 377,632 |
| V3 metallic, compact dictionary | 128 | 12.46 | 274,460 | 361,216 |
| V3 metallic, interactive | 128 | 14.16 | 296,092 | 377,632 |
| V3 compact, interactive | 128 | 12.10 | 274,460 | 361,216 |
| V3 metallic, compact / 192 | 192 | 12.46 | 411,701 | 517,168 |

![HORS-V3 FPS and ROM comparison](benchmarks/hors-v3-preview/performance.png)

Direct colour bytes remain the speed default. Compact dictionary encoding is optional: smaller streams, additional decoding cost. [Method, limitations and raw evidence](HORS_RENDER_V3_RESULTS.md).

### Background controls and performance

| Background mode | Direct FPS | Compact FPS |
| --- | ---: | ---: |
| Black, cycling off | **14.16** | 12.10 |
| Blue, cycling off | **13.70** | 12.10 |
| Automatic, 50 ticks | **13.43** | 11.86 |
| Automatic, 1 tick | **12.40** | 11.03 |

![Background-control performance](benchmarks/hors-v3-preview/background-performance.png)

Interactive controls replace originally black pixels only; other metallic shades are preserved. Default cycling requests 50 PAL ticks between changes; the fastest setting requests one tick but performs at most one change per produced picture. The displayed border follows its buffer’s background unless locked or independently selected.


## Stanford Dragon: HORS-V3 palettes

The official Stanford res4 mesh: 5,205 vertices, 15,796 edges and 11,102 triangles; 128 orientations. PAL VICE, FPS preference, 1,504-refresh display windows after warmup. Projection, visibility and surface lighting are precomputed on the host.

| Surface | Average displayed FPS | Longest display hold (ms) | Frame stream bytes | CRT bytes |
| --- | ---: | ---: | ---: | ---: |
| wireframe | **20.00** | 59.85 | 233,306 | 303,760 |
| metallic (grey) | 15.13 | 79.80 | 279,935 | 361,216 |
| red | 15.10 | 79.80 | 277,791 | 353,008 |
| green | 15.13 | 79.80 | 279,215 | 361,216 |
| blue | 15.13 | 79.80 | 280,945 | 361,216 |
| golden | 15.13 | 79.80 | 280,195 | 361,216 |

[Cartridges, correctly timed GIFs, source credits and full results](../examples/stanford_dragon/README.md).


## SAKU 2026: SVG paint, interactive controls and starfield

30 samples per presentation, 8 presentations on one HORS-V3 cart. PAL VICE; actual displayed-buffer transitions after warmup. Star motion runs independently at PAL refresh rate. Fast/slow controls change angular tempo, not CPU clock.

| Presentation / setting | Displayed FPS | Longest hold (ms) | Stars / density | HUD | Speed level |
| --- | ---: | ---: | --- | --- | ---: |
| gradient-stars | 13.70 | 82.59 | full / 16 | shown | 3 |
| gradient-no-stars | 18.11 | 63.54 | off | shown | 3 |
| solid-no-stars | 18.44 | 64.07 | off | shown | 3 |
| solid-stars | 14.37 | 83.49 | full / 16 | shown | 3 |
| gradient-crawl-stars | 16.24 | 83.81 | full / 16 | shown | 3 |
| solid-crawl | **21.99** | 63.36 | off | shown | 3 |
| gradient-stars-cycle | 9.69 | 142.33 | full / 16 | shown | 3 |
| gradient-stars-hue | 12.30 | 102.83 | full / 16 | shown | 3 |
| card-spin | 11.36 | 121.37 | full / 16 | shown | 3 |
| card-crawl | 14.10 | 101.83 | full / 16 | shown | 3 |
| outline-spin | 13.70 | 102.70 | full / 16 | shown | 3 |
| outline-crawl | 15.31 | 104.18 | full / 16 | shown | 3 |
| gradient-light-stars | 15.91 | 82.45 | light / 8 | shown | 3 |
| card-light-stars | 12.97 | 102.24 | light / 8 | shown | 3 |
| crawl-light-stars | 19.05 | 81.20 | light / 8 | shown | 3 |
| outline-light-stars | 16.24 | 82.57 | light / 8 | shown | 3 |
| outline-crawl-light-stars | 18.92 | 79.84 | light / 8 | shown | 3 |
| slowest | 2.03 | 618.82 | full / 16 | shown | 0 |
| fastest | 13.43 | 100.32 | full / 16 | shown | 10 |
| gradient-stars-hud-hidden | 14.04 | 83.86 | full / 16 | hidden | 3 |
| gradient-no-stars-hud-hidden | 18.65 | 63.33 | off | hidden | 3 |
| gradient-exhibition-active | 18.58 | 63.72 | off | hidden | 3 |
| exhibition-tour | 17.23 | 82.49 | off | hidden | 3 |
| gradient-stars-density-2 | 17.31 | 83.36 | full / 2 | shown | 3 |
| gradient-stars-density-8 | 14.91 | 83.14 | full / 8 | shown | 3 |
| gradient-stars-density-32 | 12.10 | 103.46 | full / 32 | shown | 3 |

### Light versus full starfield

| Same gradient spin, HUD shown | Displayed FPS |
| --- | ---: |
| Stars off | **18.11** |
| Original light, 8 points (SAKU default) | 15.91 |
| Full, 16 points | 13.70 |

`4` switches the two resident kernels. Light improves throughput by **16.10%** over full on this cart. Both are measured in the same binary; original light is not zero-cost. `1` resets the selected density; `2`/`3` increase/decrease it. Each mode remembers its density, and switching preserves whether stars are enabled.

Light trajectories reserve another 1 KiB at $8000–$83ff. Its kernel fits the existing $9c00–$9fff density reservation. Changing the IRQ call operand only on key events adds zero per-refresh dispatch instructions. The 4 key adds 13 CPU cycles per idle input poll, reusing an existing CIA row read.


Starfield difference on this cart: **-24.35%** displayed throughput. This includes sprite setup and VIC-II DMA. Default speed is level 3; source/style, input, hue and background controls remain enabled in both rows.

Speed and HUD controls share a 2,048-byte reservation at $9000–$97ff. HUD switches use its second KiB without additional reserved RAM; hidden glyph rendering returns immediately. The starfield reuses the literal-only vector LUT allocation at $1700–$1fff and uses 384 bytes of sprite patterns when interactive (192 bytes for automatic stars). Interactive density controls reserve 1 KiB at $9c00–$9fff and retain separate light (8 points by default) and full (16 points by default) densities. SAKU starts light; --starfield-profile selects the initial/F2-reset profile for future interactive builds. Use 1 = reset, 2 = more, 3 = less, 4 = light/full. Extra points are checked against filled cells and opaque masks; unsafe groups are suppressed. Opaque SAKU variants reserve another 2 KiB at $8800–$8fff for bounding-box masks and relocated star paths. Toggling an already included mode/effect adds no frame-stream ROM; additional precomputed presentations do consume ROM. See the manifests for actual code extents and total cartridge capacity.

[Source, CRTs, keyboard map, GIF and raw measurements](../examples/saku_2026/README.md).

| Routine / state | Mean cycles | Minimum cycles | Maximum cycles |
| --- | ---: | ---: | ---: |
| stars-on | 3936.88 | 3686 | 4219 |
| stars-off | 32.00 | 32 | 32 |
| light-stars-on | 1818.94 | 1796 | 1841 |
| light-stars-off | 32.00 | 32 | 32 |
| speed-poll-idle | 243.16 | 218 | 424 |
| effects-poll-idle | 86.03 | 82 | 125 |

VICE stopwatch, 32 calls per routine, including call/return; elapsed machine cycles. RUN/STOP (Esc in the bundled VICE keymaps) and Shift+H open/close help. RUN/STOP reuses the density row with nine extra CPU cycles per idle input poll and no extra CIA read; without stars, its short scan adds 34 cycles per poll. The HUD key-release latch adds six CPU cycles per ordinary unshifted poll when effects are included (three without them); no per-frame visibility branch is added to drawing. Paged help uses a 1 KiB text screen, 1 KiB code reservation and 1 KiB packed text reservation at $c000–$c3ff; it pauses the producer/IRQ while open, and restores all three picture buffers and presentation state. The startup screen is excluded from these measurements.

HUD hidden versus shown, gradient-stars: **+2.44%** displayed throughput, same cartridge and default speed.

HUD hidden versus shown, gradient-no-stars: **+2.95%** displayed throughput, same cartridge and default speed.

### Exhibition scheduler: matched gradient, HUD and stars hidden

| Scheduler | Displayed FPS |
| --- | ---: |
| Inactive | **18.65** |
| Active (60-second interval, no switch in measurement window) | 18.58 |

Measured scheduler-only throughput difference: **-0.36%**. The separate exhibition-tour row cycles the three styles every five seconds; its mixed workload is not a scheduler-overhead comparison.

`5` toggles exhibition, `6` selects ordered/random, `7`/`8` adjust the interval by five seconds (5–60). Entry hides HUD and stars; manual star selections persist across scene changes. Ordinary interactive builds still start with stars disabled unless explicitly enabled. Inactive exhibition adds no IRQ instructions; its key scan adds 67 CPU cycles per idle input poll. Help expands packed text only on opening or page changes. [Shared controls and CLI settings](EXHIBITION.md).

### Optional starfield: matched ordinary interactive builds

48-sample metallic torus; identical geometry and host pictures. 1504 PAL refreshes after warmup; actual display transitions; help/startup excluded.

| Starfield build / startup | Displayed FPS | Frame stream bytes |
| --- | ---: | ---: |
| excluded | **9.60** | 170,815 |
| included-disabled | 9.56 | 170,815 |
| included-enabled | 7.47 | 170,815 |

Excluded builds retain help and speed controls but contain no starfield IRQ routine, paths or sprite setup. The included-disabled build allows Shift+S; the enabled build starts with stars. All model picture oracles are identical. The separate indexed4 and no-stars SVG presentation builds also pass native pixel/control checks.


## Per-animation lookup

High/low are 985,248 divided by the shortest/longest **actual display-flip interval within a normal PLAY ALL window**, including VIC and IRQ stalls. Average is total displayed frames / measured time, not an arithmetic average of instantaneous FPS. Window edges are excluded from interval extrema. High FPS can include a brief queued-frame burst; it does not describe sustained throughput. Only the highest average FPS is bolded, including ties, across the shown FPS/RAM variants. The best-method summary above uses frame counts among FPS-preferred methods. All values are FPS unless the header says bytes.

### TORUS

| Method | High | Average | Low | Resident frame-table RAM (B) | Frame data ROM (B) | Runtime PRG (B) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| step | 25.06 | 12.29 | 10.02 | 18,760 | 0 | 43,546 |
| bytechunk | 25.07 | 13.86 | 10.02 | 18,760 | 0 | 43,546 |
| yunroll | 25.07 | 14.10 | 10.02 | 18,760 | 0 | 43,546 |
| cart scaffold | 25.07 | 14.10 | 10.02 | 18,760 | 0 | 43,546 |
| V2 | 17.06 | 11.25 | 8.35 | 0 | 18,664 | 16,609 |
| V3 | 23.70 | 12.05 | 9.84 | 0 | 18,664 | 18,433 |
| V4 | 23.52 | 12.05 | 9.86 | 0 | 18,664 | 18,433 |
| V5 | 24.47 | 12.36 | 9.88 | 0 | 18,500 | 21,777 |
| V6 | 25.87 | 12.76 | 9.68 | 0 | 18,500 | 21,777 |
| V7 | 27.31 | 13.46 | 9.77 | 0 | 16,505 | 21,777 |
| V8 | 27.31 | 13.46 | 9.77 | 0 | 16,505 | 21,777 |
| V9 | 27.06 | 13.46 | 9.72 | 0 | 16,505 | 21,777 |
| hors-v1 | 27.00 | 16.07 | 12.10 | 0 | 46,217 | 21,777 |
| V7-ram | 27.01 | 12.86 | 9.74 | 0 | 16,505 | 18,433 |
| V8-ram | 27.01 | 12.86 | 9.74 | 0 | 16,505 | 18,433 |
| V9-ram | 26.80 | 12.86 | 9.72 | 0 | 16,505 | 18,433 |
| hors-v1-ram | 27.04 | 16.07 | 12.04 | 0 | 46,217 | 18,433 |
| hors-v2 | 27.18 | **17.68 (tie)** | 12.09 | 0 | 46,217 | 21,777 |
| hors-v2-ram | 27.20 | **17.68 (tie)** | 12.00 | 0 | 46,217 | 18,203 |
| hors-v3 | 27.18 | **17.68 (tie)** | 12.09 | 0 | 46,217 | 21,777 |
| hors-v3-ram | 27.20 | **17.68 (tie)** | 12.00 | 0 | 46,217 | 18,203 |

### TORUS DENSE

| Method | High | Average | Low | Resident frame-table RAM (B) | Frame data ROM (B) | Runtime PRG (B) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| step | 25.07 | 10.95 | 8.35 | 22,081 | 0 | 47,017 |
| bytechunk | 25.06 | 12.19 | 8.35 | 22,081 | 0 | 47,017 |
| yunroll | 25.06 | 12.42 | 10.02 | 22,081 | 0 | 47,017 |
| cart scaffold | 25.06 | 12.42 | 10.02 | 22,081 | 0 | 47,017 |
| V2 | 16.90 | 9.84 | 8.22 | 0 | 21,985 | 16,609 |
| V3 | 23.55 | 10.65 | 8.35 | 0 | 21,985 | 18,433 |
| V4 | 17.17 | 10.75 | 8.35 | 0 | 21,985 | 18,433 |
| V5 | 16.71 | 10.95 | 8.35 | 0 | 21,767 | 21,777 |
| V6 | 27.60 | 11.25 | 8.35 | 0 | 21,767 | 21,777 |
| V7 | 27.21 | 12.15 | 9.71 | 0 | 18,302 | 21,777 |
| V8 | 27.21 | 12.15 | 9.71 | 0 | 18,302 | 21,777 |
| V9 | 27.29 | 12.15 | 9.94 | 0 | 18,302 | 21,777 |
| hors-v1 | 27.04 | 15.77 | 12.20 | 0 | 48,568 | 21,777 |
| V7-ram | 26.82 | 11.55 | 8.35 | 0 | 18,302 | 18,433 |
| V8-ram | 26.82 | 11.55 | 8.35 | 0 | 18,302 | 18,433 |
| V9-ram | 26.73 | 11.55 | 8.35 | 0 | 18,302 | 18,433 |
| hors-v1-ram | 26.78 | 15.77 | 12.04 | 0 | 48,568 | 18,433 |
| hors-v2 | 27.12 | **17.18 (tie)** | 12.53 | 0 | 48,568 | 21,777 |
| hors-v2-ram | 25.54 | **17.18 (tie)** | 12.53 | 0 | 48,568 | 18,203 |
| hors-v3 | 27.12 | **17.18 (tie)** | 12.53 | 0 | 48,568 | 21,777 |
| hors-v3-ram | 25.54 | **17.18 (tie)** | 12.53 | 0 | 48,568 | 18,203 |

### CUBE

| Method | High | Average | Low | Resident frame-table RAM (B) | Frame data ROM (B) | Runtime PRG (B) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| step | 50.14 | 26.45 | 16.71 | 10,264 | 0 | 35,381 |
| bytechunk | 50.17 | 29.40 | 25.05 | 10,264 | 0 | 35,381 |
| yunroll | 50.16 | **30.27 (tie)** | 25.05 | 10,264 | 0 | 35,381 |
| cart scaffold | 50.16 | **30.27 (tie)** | 25.05 | 10,264 | 0 | 35,381 |
| V2 | 46.05 | 23.00 | 16.71 | 0 | 10,156 | 16,637 |
| V3 | 50.17 | 24.72 | 16.71 | 0 | 10,156 | 18,433 |
| V4 | 50.13 | 24.72 | 16.70 | 0 | 10,156 | 18,433 |
| V5 | 50.13 | 25.51 | 16.71 | 0 | 2,539 | 21,919 |
| V6 | 55.98 | 26.82 | 16.71 | 0 | 2,539 | 21,919 |
| V7 | 55.55 | 26.82 | 16.71 | 0 | 2,539 | 21,919 |
| V8 | 55.55 | 26.82 | 16.71 | 0 | 2,539 | 21,919 |
| V9 | 55.84 | 26.82 | 16.71 | 0 | 2,539 | 21,919 |
| hors-v1 | 50.82 | 27.42 | 16.64 | 0 | 7,824 | 21,919 |
| V7-ram | 53.31 | 24.61 | 16.05 | 0 | 2,539 | 21,647 |
| V8-ram | 53.31 | 24.61 | 16.05 | 0 | 2,539 | 21,647 |
| V9-ram | 53.40 | 24.61 | 16.18 | 0 | 2,539 | 21,647 |
| hors-v1-ram | 50.85 | 27.42 | 16.68 | 0 | 7,824 | 21,647 |
| hors-v2 | 55.93 | 30.03 | 23.16 | 0 | 7,824 | 21,919 |
| hors-v2-ram | 55.54 | 30.04 | 23.13 | 0 | 7,824 | 21,647 |
| hors-v3 | 55.93 | 30.03 | 23.16 | 0 | 7,824 | 21,919 |
| hors-v3-ram | 55.54 | 30.04 | 23.13 | 0 | 7,824 | 21,647 |

### SPHERE

| Method | High | Average | Low | Resident frame-table RAM (B) | Frame data ROM (B) | Runtime PRG (B) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| step | 25.05 | 13.63 | 12.53 | 12,710 | 0 | 37,749 |
| bytechunk | 25.06 | 15.00 | 12.53 | 12,710 | 0 | 37,749 |
| yunroll | 25.06 | 15.50 | 12.53 | 12,710 | 0 | 37,749 |
| cart scaffold | 25.06 | 15.50 | 12.53 | 12,710 | 0 | 37,749 |
| V2 | 16.71 | 12.25 | 10.02 | 0 | 12,638 | 16,553 |
| V3 | 16.93 | 13.16 | 10.02 | 0 | 12,638 | 18,433 |
| V4 | 16.97 | 13.16 | 10.28 | 0 | 12,638 | 18,433 |
| V5 | 23.92 | 13.66 | 12.04 | 0 | 6,314 | 21,919 |
| V6 | 25.06 | 14.26 | 11.93 | 0 | 6,314 | 21,919 |
| V7 | 18.00 | 14.67 | 11.89 | 0 | 5,824 | 21,919 |
| V8 | 18.00 | 14.67 | 11.89 | 0 | 5,824 | 21,919 |
| V9 | 18.01 | 14.67 | 11.89 | 0 | 5,824 | 21,919 |
| hors-v1 | 25.11 | 15.87 | 11.88 | 0 | 18,108 | 21,919 |
| V7-ram | 17.90 | 13.46 | 11.91 | 0 | 5,824 | 21,647 |
| V8-ram | 17.90 | 13.46 | 11.91 | 0 | 5,824 | 21,647 |
| V9-ram | 18.02 | 13.46 | 11.93 | 0 | 5,824 | 21,647 |
| hors-v1-ram | 25.16 | 15.87 | 11.87 | 0 | 18,108 | 21,647 |
| hors-v2 | 28.08 | **17.38 (tie)** | 15.53 | 0 | 18,108 | 21,919 |
| hors-v2-ram | 28.17 | **17.38 (tie)** | 15.56 | 0 | 18,108 | 21,647 |
| hors-v3 | 28.08 | **17.38 (tie)** | 15.53 | 0 | 18,108 | 21,919 |
| hors-v3-ram | 28.17 | **17.38 (tie)** | 15.56 | 0 | 18,108 | 21,647 |

### HORSE HEAD

| Method | High | Average | Low | Resident frame-table RAM (B) | Frame data ROM (B) | Runtime PRG (B) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| step | 16.71 | 12.15 | 10.02 | 22,658 | 0 | 49,076 |
| bytechunk | 25.06 | 12.92 | 10.02 | 22,658 | 0 | 49,076 |
| yunroll | 25.06 | 13.23 | 10.02 | 22,658 | 0 | 49,076 |
| cart scaffold | 25.06 | 13.23 | 10.02 | 22,658 | 0 | 49,076 |
| V2 | 16.58 | 10.55 | 8.41 | 0 | 22,562 | 16,609 |
| V3 | 16.71 | 11.65 | 9.64 | 0 | 22,562 | 18,433 |
| V4 | 16.71 | 11.75 | 9.93 | 0 | 22,562 | 18,433 |
| V5 | 17.13 | 12.46 | 9.79 | 0 | 21,447 | 21,777 |
| V6 | 17.56 | 12.86 | 9.75 | 0 | 21,447 | 21,777 |
| V7 | 17.75 | 13.76 | 9.87 | 0 | 18,245 | 21,777 |
| V8 | 17.75 | 13.76 | 9.87 | 0 | 18,245 | 21,777 |
| V9 | 25.90 | 13.86 | 9.77 | 0 | 18,245 | 21,777 |
| hors-v1 | 52.46 | 27.42 | 16.55 | 0 | 30,840 | 21,777 |
| V7-ram | 25.06 | 12.76 | 9.75 | 0 | 18,245 | 18,433 |
| V8-ram | 25.06 | 12.76 | 9.75 | 0 | 18,245 | 18,433 |
| V9-ram | 17.51 | 12.76 | 9.62 | 0 | 18,245 | 18,433 |
| hors-v1-ram | 52.58 | 27.42 | 16.60 | 0 | 30,840 | 18,433 |
| hors-v2 | 54.55 | **29.34 (tie)** | 23.89 | 0 | 30,840 | 21,777 |
| hors-v2-ram | 54.76 | 29.33 | 23.66 | 0 | 30,840 | 18,203 |
| hors-v3 | 54.55 | **29.34 (tie)** | 23.89 | 0 | 30,840 | 21,777 |
| hors-v3-ram | 54.76 | 29.33 | 23.66 | 0 | 30,840 | 18,203 |

### SUNFLOWER TORUS

| Method | High | Average | Low | Resident frame-table RAM (B) | Frame data ROM (B) | Runtime PRG (B) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| step | 16.71 | 11.02 | 8.35 | 21,752 | 0 | 48,971 |
| bytechunk | 16.71 | 11.35 | 10.02 | 21,752 | 0 | 48,971 |
| yunroll | 16.71 | 11.55 | 10.02 | 21,752 | 0 | 48,971 |
| cart scaffold | 16.71 | 11.55 | 10.02 | 21,752 | 0 | 48,971 |
| V2 | 12.61 | 9.44 | 8.17 | 0 | 21,668 | 16,581 |
| V3 | 16.55 | 10.25 | 8.35 | 0 | 21,668 | 18,433 |
| V4 | 16.48 | 10.35 | 8.35 | 0 | 21,668 | 18,433 |
| V5 | 16.71 | 10.95 | 9.96 | 0 | 20,777 | 21,777 |
| V6 | 25.08 | 11.15 | 9.74 | 0 | 20,777 | 21,777 |
| V7 | 25.55 | 12.15 | 9.75 | 0 | 17,168 | 21,777 |
| V8 | 25.55 | 12.15 | 9.75 | 0 | 17,168 | 21,777 |
| V9 | 25.46 | 12.15 | 9.74 | 0 | 17,168 | 21,777 |
| hors-v1 | 53.22 | 27.12 | 16.25 | 0 | 29,308 | 21,777 |
| V7-ram | 16.89 | 11.15 | 8.31 | 0 | 17,168 | 18,433 |
| V8-ram | 16.89 | 11.15 | 8.31 | 0 | 17,168 | 18,433 |
| V9-ram | 25.06 | 11.15 | 9.71 | 0 | 17,168 | 18,433 |
| hors-v1-ram | 53.28 | 27.12 | 16.35 | 0 | 29,308 | 18,433 |
| hors-v2 | 54.33 | **28.73 (tie)** | 16.30 | 0 | 29,308 | 21,777 |
| hors-v2-ram | 54.78 | **28.73 (tie)** | 16.28 | 0 | 29,308 | 18,203 |
| hors-v3 | 54.33 | **28.73 (tie)** | 16.30 | 0 | 29,308 | 21,777 |
| hors-v3-ram | 54.78 | **28.73 (tie)** | 16.28 | 0 | 29,308 | 18,203 |

### SUNFLOWER COLOR

| Method | High | Average | Low | Resident frame-table RAM (B) | Frame data ROM (B) | Runtime PRG (B) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| step | 16.71 | 9.68 | 8.35 | 19,385 | 0 | 44,450 |
| bytechunk | 16.71 | 9.98 | 8.35 | 19,385 | 0 | 44,450 |
| yunroll | 16.71 | 10.18 | 8.35 | 19,385 | 0 | 44,450 |
| cart scaffold | 16.71 | 10.18 | 8.35 | 19,385 | 0 | 44,450 |
| V2 | 10.28 | 8.04 | 6.92 | 0 | 19,325 | 16,525 |
| V3 | 12.64 | 8.84 | 7.16 | 0 | 19,325 | 18,433 |
| V4 | 12.53 | 8.94 | 7.32 | 0 | 19,325 | 18,433 |
| V5 | 16.36 | 9.34 | 8.11 | 0 | 18,597 | 21,777 |
| V6 | 16.71 | 9.74 | 8.32 | 0 | 18,597 | 21,777 |
| V7 | 17.60 | 10.45 | 8.35 | 0 | 16,028 | 21,777 |
| V8 | 17.60 | 10.45 | 8.35 | 0 | 16,028 | 21,777 |
| V9 | 16.71 | 10.55 | 8.35 | 0 | 16,028 | 21,777 |
| hors-v1 | 53.04 | 19.99 | 12.53 | 0 | 24,790 | 21,777 |
| V7-ram | 17.64 | 9.74 | 8.14 | 0 | 16,028 | 18,433 |
| V8-ram | 17.64 | 9.74 | 8.14 | 0 | 16,028 | 18,433 |
| V9-ram | 16.71 | 9.74 | 8.18 | 0 | 16,028 | 18,433 |
| hors-v1-ram | 52.91 | 19.99 | 12.53 | 0 | 24,790 | 18,433 |
| hors-v2 | 60.16 | 20.89 | 15.83 | 0 | 24,790 | 21,777 |
| hors-v2-ram | 51.25 | 20.89 | 16.15 | 0 | 24,790 | 18,203 |
| hors-v3 | 53.37 | **22.70 (tie)** | 16.01 | 0 | 25,898 | 21,777 |
| hors-v3-ram | 52.94 | **22.70 (tie)** | 15.99 | 0 | 25,898 | 18,203 |

### SPACE HORSE SPIN

| Method | High | Average | Low | Resident frame-table RAM (B) | Frame data ROM (B) | Runtime PRG (B) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| step | 12.53 | 9.98 | 8.35 | 21,930 | 0 | 48,828 |
| bytechunk | 12.53 | 10.55 | 8.35 | 21,930 | 0 | 48,828 |
| yunroll | 12.53 | 10.65 | 8.35 | 21,930 | 0 | 48,828 |
| cart scaffold | 12.53 | 10.65 | 8.35 | 21,930 | 0 | 48,828 |
| V2 | 10.10 | 8.54 | 7.17 | 0 | 21,858 | 16,553 |
| V3 | 12.46 | 9.34 | 8.17 | 0 | 21,858 | 18,433 |
| V4 | 12.53 | 9.44 | 8.27 | 0 | 21,858 | 18,433 |
| V5 | 50.13 | 10.15 | 8.21 | 0 | 20,489 | 21,777 |
| V6 | 50.14 | 10.55 | 8.22 | 0 | 20,489 | 21,777 |
| V7 | 50.13 | 10.65 | 8.19 | 0 | 20,119 | 21,777 |
| V8 | 50.13 | 10.65 | 8.19 | 0 | 20,119 | 21,777 |
| V9 | 52.80 | 10.75 | 8.23 | 0 | 20,119 | 21,777 |
| hors-v1 | 52.06 | 17.58 | 12.17 | 0 | 34,107 | 21,777 |
| V7-ram | 50.12 | 9.94 | 8.35 | 0 | 20,119 | 18,433 |
| V8-ram | 50.12 | 9.94 | 8.35 | 0 | 20,119 | 18,433 |
| V9-ram | 50.48 | 10.04 | 8.21 | 0 | 20,119 | 18,433 |
| hors-v1-ram | 50.13 | 17.58 | 12.52 | 0 | 34,107 | 18,433 |
| hors-v2 | 50.13 | 19.08 | 12.53 | 0 | 34,107 | 21,777 |
| hors-v2-ram | 51.64 | **19.09 (tie)** | 12.21 | 0 | 34,107 | 18,203 |
| hors-v3 | 53.54 | **19.09 (tie)** | 12.53 | 0 | 34,107 | 21,777 |
| hors-v3-ram | 50.14 | **19.09 (tie)** | 12.53 | 0 | 34,107 | 18,203 |

### SPACE HORSE CRAWL

| Method | High | Average | Low | Resident frame-table RAM (B) | Frame data ROM (B) | Runtime PRG (B) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| step | 25.07 | 15.13 | 10.02 | 23,680 | 0 | 49,153 |
| bytechunk | 25.07 | 16.61 | 12.53 | 23,680 | 0 | 49,153 |
| yunroll | 25.07 | 16.61 | 12.53 | 23,680 | 0 | 49,153 |
| cart scaffold | 25.07 | 16.61 | 12.53 | 23,680 | 0 | 49,153 |
| V2 | 17.59 | 12.86 | 9.81 | 0 | 23,584 | 16,609 |
| V3 | 23.66 | 14.06 | 10.02 | 0 | 23,584 | 18,433 |
| V4 | 24.95 | 14.26 | 10.08 | 0 | 23,584 | 18,433 |
| V5 | 25.06 | 14.67 | 10.04 | 0 | 22,981 | 21,777 |
| V6 | 25.95 | 15.47 | 9.69 | 0 | 22,981 | 21,777 |
| V7 | 26.93 | 16.57 | 10.01 | 0 | 20,603 | 21,777 |
| V8 | 59.03 | 22.90 | 12.13 | 0 | 17,765 | 21,777 |
| V9 | 52.42 | 23.51 | 12.18 | 0 | 17,765 | 21,777 |
| hors-v1 | 52.44 | 35.56 | 16.60 | 0 | 20,292 | 21,777 |
| V7-ram | 25.65 | 16.27 | 12.20 | 0 | 20,603 | 18,433 |
| V8-ram | 58.38 | 22.70 | 12.12 | 0 | 17,765 | 18,433 |
| V9-ram | 53.29 | 23.30 | 12.13 | 0 | 17,765 | 18,433 |
| hors-v1-ram | 54.09 | 35.66 | 16.60 | 0 | 20,292 | 18,433 |
| hors-v2 | 54.67 | 38.27 | 24.07 | 0 | 20,292 | 21,777 |
| hors-v2-ram | 54.67 | 38.27 | 24.07 | 0 | 20,292 | 18,203 |
| hors-v3 | 54.69 | 38.27 | 24.07 | 0 | 20,292 | 21,777 |
| hors-v3-ram | 54.73 | **38.28** | 24.07 | 0 | 20,292 | 18,203 |

### FALLING CUBES

| Method | High | Average | Low | Resident frame-table RAM (B) | Frame data ROM (B) | Runtime PRG (B) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| step | 25.07 | 13.56 | 10.02 | 12,804 | 0 | 38,586 |
| bytechunk | 50.12 | 14.80 | 10.02 | 12,804 | 0 | 38,586 |
| yunroll | 50.13 | 14.90 | 10.02 | 12,804 | 0 | 38,586 |
| cart scaffold | 50.13 | 14.90 | 10.02 | 12,804 | 0 | 38,586 |
| V2 | 25.06 | 11.55 | 8.29 | 0 | 12,750 | 16,511 |
| V3 | 24.98 | 12.46 | 9.82 | 0 | 12,750 | 18,433 |
| V4 | 25.06 | 12.66 | 9.74 | 0 | 12,750 | 18,433 |
| V5 | 25.06 | 13.16 | 9.93 | 0 | 12,542 | 21,777 |
| V6 | 27.75 | 13.66 | 9.74 | 0 | 12,542 | 21,777 |
| V7 | 26.97 | 13.86 | 9.81 | 0 | 12,007 | 21,777 |
| V8 | 27.06 | 13.86 | 9.83 | 0 | 12,007 | 21,777 |
| V9 | 28.15 | 13.86 | 9.83 | 0 | 12,007 | 21,777 |
| hors-v1 | 50.15 | 19.69 | 12.28 | 0 | 19,518 | 21,777 |
| V7-ram | 26.82 | 13.46 | 9.76 | 0 | 12,007 | 18,433 |
| V8-ram | 26.68 | 13.46 | 9.76 | 0 | 12,007 | 18,433 |
| V9-ram | 27.26 | 13.56 | 9.78 | 0 | 12,007 | 18,433 |
| hors-v1-ram | 27.46 | 19.59 | 12.13 | 0 | 19,518 | 18,433 |
| hors-v2 | 50.13 | 20.89 | 15.98 | 0 | 19,518 | 21,777 |
| hors-v2-ram | 50.13 | 20.89 | 15.98 | 0 | 19,518 | 18,203 |
| hors-v3 | 50.13 | **21.30 (tie)** | 15.98 | 0 | 21,374 | 21,777 |
| hors-v3-ram | 50.12 | **21.30 (tie)** | 16.03 | 0 | 21,374 | 18,203 |

### HORSE HEAD HIFI

| Method | High | Average | Low | Resident frame-table RAM (B) | Frame data ROM (B) | Runtime PRG (B) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| step | N/A¹ | N/A¹ | N/A¹ | N/A | N/A | N/A |
| bytechunk | N/A¹ | N/A¹ | N/A¹ | N/A | N/A | N/A |
| yunroll | N/A¹ | N/A¹ | N/A¹ | N/A | N/A | N/A |
| cart scaffold | N/A¹ | N/A¹ | N/A¹ | N/A | N/A | N/A |
| V2 | 8.69 | 7.03 | 6.16 | 0 | 147,346 | 17,281 |
| V3 | 10.15 | 7.84 | 7.00 | 0 | 147,346 | 18,433 |
| V4 | 10.03 | 7.94 | 7.03 | 0 | 147,346 | 18,433 |
| V5 | 10.22 | 8.34 | 7.00 | 0 | 141,625 | 21,777 |
| V6 | 12.53 | 8.64 | 7.00 | 0 | 141,625 | 21,777 |
| V7 | 13.00 | 10.14 | 8.11 | 0 | 105,831 | 21,777 |
| V8 | 25.06 | 10.15 | 8.10 | 0 | 105,759 | 21,777 |
| V9 | 50.17 | 10.25 | 8.08 | 0 | 105,759 | 21,777 |
| hors-v1 | 51.01 | 20.69 | 15.67 | 0 | 158,181 | 21,777 |
| V7-ram | 12.98 | 9.34 | 8.09 | 0 | 105,831 | 18,433 |
| V8-ram | 27.19 | 9.44 | 8.07 | 0 | 105,759 | 18,433 |
| V9-ram | 50.13 | 9.54 | 8.10 | 0 | 105,759 | 18,433 |
| hors-v1-ram | 51.33 | 20.79 | 15.72 | 0 | 158,181 | 18,433 |
| hors-v2 | 50.16 | 21.50 | 15.64 | 0 | 158,181 | 21,777 |
| hors-v2-ram | 56.72 | 21.60 | 15.56 | 0 | 158,181 | 18,203 |
| hors-v3 | 53.60 | 23.10 | 16.03 | 0 | 168,425 | 21,777 |
| hors-v3-ram | 51.85 | **23.21** | 16.03 | 0 | 168,425 | 18,203 |

### SUNFLOWER TORUS HIFI

| Method | High | Average | Low | Resident frame-table RAM (B) | Frame data ROM (B) | Runtime PRG (B) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| step | N/A¹ | N/A¹ | N/A¹ | N/A | N/A | N/A |
| bytechunk | N/A¹ | N/A¹ | N/A¹ | N/A | N/A | N/A |
| yunroll | N/A¹ | N/A¹ | N/A¹ | N/A | N/A | N/A |
| cart scaffold | N/A¹ | N/A¹ | N/A¹ | N/A | N/A | N/A |
| V2 | 9.83 | 4.72 | 3.60 | 0 | 247,481 | 17,281 |
| V3 | 10.30 | 5.42 | 4.16 | 0 | 247,481 | 18,433 |
| V4 | 10.17 | 5.42 | 4.13 | 0 | 247,481 | 18,433 |
| V5 | 12.36 | 5.83 | 4.51 | 0 | 230,752 | 21,777 |
| V6 | 12.97 | 6.03 | 4.56 | 0 | 230,752 | 21,777 |
| V7 | 16.85 | 6.83 | 5.01 | 0 | 181,152 | 21,777 |
| V8 | 50.16 | 12.46 | 6.27 | 0 | 160,415 | 21,777 |
| V9 | 56.34 | 14.46 | 6.27 | 0 | 160,415 | 21,777 |
| hors-v1 | 57.46 | 19.89 | 12.53 | 0 | 163,780 | 21,777 |
| V7-ram | 12.84 | 6.43 | 5.01 | 0 | 181,152 | 18,433 |
| V8-ram | 60.30 | 12.05 | 6.27 | 0 | 160,415 | 18,433 |
| V9-ram | 56.71 | 14.06 | 6.19 | 0 | 160,415 | 18,433 |
| hors-v1-ram | 60.62 | 19.89 | 12.53 | 0 | 163,780 | 18,433 |
| hors-v2 | 58.80 | 20.39 | 15.98 | 0 | 163,780 | 21,777 |
| hors-v2-ram | 60.00 | 20.39 | 15.98 | 0 | 163,780 | 18,203 |
| hors-v3 | 53.24 | **22.70 (tie)** | 16.12 | 0 | 168,484 | 21,777 |
| hors-v3-ram | 52.94 | **22.70 (tie)** | 15.99 | 0 | 168,484 | 18,203 |


## Storage and fixed RAM allocations

| Method | Comparison CRT bytes | Entries | Runtime PRG size range, bytes | Fixed bitmap + screen storage | Stream staging + metadata caches |
| --- | ---: | ---: | ---: | ---: | ---: |
| step | 500,752 | 10 | 35,381–49,153 | 27,000 B | 0 B |
| bytechunk | 500,752 | 10 | 35,381–49,153 | 27,000 B | 0 B |
| yunroll | 500,752 | 10 | 35,381–49,153 | 27,000 B | 0 B |
| cart scaffold | 500,752 | 10 | 35,381–49,153 | 27,000 B | 0 B |
| V2 | 968,608 | 12 | 16,511–17,281 | 27,000 B | 11,264 B |
| V3 | 968,608 | 12 | 18,433–18,433 | 27,000 B | 11,264 B |
| V4 | 968,608 | 12 | 18,433–18,433 | 27,000 B | 11,264 B |
| V5 | 927,568 | 12 | 21,777–21,919 | 27,000 B | 11,264 B |
| V6 | 927,568 | 12 | 21,777–21,919 | 27,000 B | 11,264 B |
| V7 | 804,448 | 12 | 21,777–21,919 | 27,000 B | 11,264 B |
| V8 | 771,616 | 12 | 21,777–21,919 | 27,000 B | 11,264 B |
| V9 | 771,616 | 12 | 21,777–21,919 | 27,000 B | 11,264 B |
| hors-v1 | 985,024 | 12 | 21,777–21,919 | 27,000 B | 11,264 B |
| V7-ram | 804,448 | 12 | 18,433–21,647 | 27,000 B | 11,264 B |
| V8-ram | 771,616 | 12 | 18,433–21,647 | 27,000 B | 11,264 B |
| V9-ram | 771,616 | 12 | 18,433–21,647 | 27,000 B | 11,264 B |
| hors-v1-ram | 985,024 | 12 | 18,433–21,647 | 27,000 B | 11,264 B |
| hors-v2 | 985,024 | 12 | 21,777–21,919 | 27,000 B | 11,264 B |
| hors-v2-ram | 985,024 | 12 | 18,203–21,647 | 27,000 B | 11,264 B |
| hors-v3 | 1,009,648 | 12 | 21,777–21,919 | 27,000 B | 11,264 B |
| hors-v3-ram | 1,009,648 | 12 | 18,203–21,647 | 27,000 B | 11,264 B |

Fixed graphics storage counts three 8,000-byte bitmaps and three 1,000-byte screen-colour matrices. Streamed methods also reserve 8,192 bytes staging and three 1,024-byte metadata caches. These are allocation components, **not total used or free RAM**: renderer code, LUTs, state, directories, menu/control storage and padding also occupy address space. RAM preference saves code but does not reclaim those fixed buffers. PRG length includes load address and gaps; it must not be added to these figures as if it were a disjoint allocation. The resident comparison CRT has fewer entries because HiFi does not fit, so its whole-cart size is not directly comparable to twelve-entry streamed carts.

| Animation | Resident frame tables (RAM bytes) | V2–V4 vectors (ROM bytes) | V5 | V6 | V7 | V8 | V9 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| TORUS | 18,760 | 18,664 | 18,500 | 18,500 | 16,505 | 16,505 | 16,505 |
| TORUS DENSE | 22,081 | 21,985 | 21,767 | 21,767 | 18,302 | 18,302 | 18,302 |
| CUBE | 10,264 | 10,156 | 2,539 | 2,539 | 2,539 | 2,539 | 2,539 |
| SPHERE | 12,710 | 12,638 | 6,314 | 6,314 | 5,824 | 5,824 | 5,824 |
| HORSE HEAD | 22,658 | 22,562 | 21,447 | 21,447 | 18,245 | 18,245 | 18,245 |
| SUNFLOWER TORUS | 21,752 | 21,668 | 20,777 | 20,777 | 17,168 | 17,168 | 17,168 |
| SUNFLOWER COLOR | 19,385 | 19,325 | 18,597 | 18,597 | 16,028 | 16,028 | 16,028 |
| SPACE HORSE SPIN | 21,930 | 21,858 | 20,489 | 20,489 | 20,119 | 20,119 | 20,119 |
| SPACE HORSE CRAWL | 23,680 | 23,584 | 22,981 | 22,981 | 20,603 | 17,765 | 17,765 |
| FALLING CUBES | 12,804 | 12,750 | 12,542 | 12,542 | 12,007 | 12,007 | 12,007 |
| HORSE HEAD HIFI | N/A | 147,346 | 141,625 | 141,625 | 105,831 | 105,759 | 105,759 |
| SUNFLOWER TORUS HIFI | N/A | 247,481 | 230,752 | 230,752 | 181,152 | 160,415 | 160,415 |

Resident table bytes count pointer, clear/colour and line records, excluding renderer code/LUTs. ROM bytes count unique encoded frame blocks, excluding menu/runtime/CHIP headers and unused bank space. These figures explain capacity tradeoffs; they do not pretend to be a free-RAM measurement.

¹ N/A means the complete dataset does not fit that preserved resident implementation. In the shipped dataset, 128 HiFi orientations exceed the 64-entry pointer arena, and HiFi sunflower also exceeds the 8-bit run-count limit. Exact per-method rejection reasons are in the external `*-unsupported.json` files. No frames, geometry or colours were removed to force a result. `yunroll-cart` is the initial resident scaffold, not V2 streaming.

## Authored scenes: separate paced diagnostics

These are **not PLAY ALL A/B FPS results** and must not be mixed into the menu tables or used to rank renderer throughput. The unchanged authored sequence runs with its original pacing and intro/ending behavior. Samples/s includes waits; mean active render cycles shows rendering cost. Clean/HUD Marbles and Horse & Sunflower use matching full source samples across V4–V10, frozen in `assets/comparison-scene-vector-reference.json.gz` from the original V4/V7 cartridges. No external history directory is required. For V10, the monitor acknowledges the indefinite SPACE build screen through its normal exit before running the authored intro; no cartridge bytes or measured renderer instructions are changed. Earlier generations do not provide the authored scene backend.

| Scene | Method | Samples/s (paced) | Mean render cycles | Worst render cycles | Over-budget samples |
| --- | --- | ---: | ---: | ---: | ---: |
| marbles-clean | V4-scene | 5.504 | 168,769 | 329,444 | 134 / 200 |
| marbles-clean | V5-scene | 6.237 | 142,997 | 304,457 | 107 / 200 |
| marbles-clean | V6-scene | 6.364 | 137,812 | 297,383 | 93 / 200 |
| marbles-clean | V7-scene | 6.568 | 125,941 | 282,700 | 47 / 200 |
| marbles-clean | V8-scene | 6.903 | 83,822 | 282,735 | 8 / 200 |
| marbles-clean | V9-scene | 6.903 | 78,073 | 280,843 | 8 / 200 |
| marbles-clean | V10-scene | **7.149** | 57,446 | 106,461 | 0 / 200 |
| marbles-hud | V4-scene | 5.499 | 168,959 | 329,882 | 135 / 200 |
| marbles-hud | V5-scene | 6.227 | 143,252 | 304,859 | 107 / 200 |
| marbles-hud | V6-scene | 6.357 | 137,957 | 297,677 | 93 / 200 |
| marbles-hud | V7-scene | 6.569 | 126,052 | 282,842 | 47 / 200 |
| marbles-hud | V8-scene | 6.899 | 83,970 | 283,024 | 8 / 200 |
| marbles-hud | V9-scene | 6.904 | 78,212 | 281,085 | 8 / 200 |
| marbles-hud | V10-scene | **7.145** | 57,590 | 106,810 | 0 / 200 |
| horse-sunflower | V4-scene | 3.350 | 293,992 | 301,456 | 84 / 84 |
| horse-sunflower | V5-scene | 4.132 | 203,307 | 296,295 | 59 / 84 |
| horse-sunflower | V6-scene | 4.275 | 195,348 | 284,084 | 59 / 84 |
| horse-sunflower | V7-scene | 4.279 | 195,116 | 283,624 | 59 / 84 |
| horse-sunflower | V8-scene | 4.279 | 195,116 | 283,624 | 59 / 84 |
| horse-sunflower | V9-scene | 4.301 | 193,946 | 282,090 | 59 / 84 |
| horse-sunflower | V10-scene | **7.335** | 99,173 | 146,290 | 57 / 84 |

## Workload and interpretation

- All menu builds use the exact released V4 vector reference (`assets/v4-menu-vector-reference.json.gz`), including colours, HUD and animation sample order. Native method-specific lossless encoding is retained.
- The explicit hors-v3 comparison rows run the V3 literal colour pipeline inside the same external PLAY ALL wrapper and frozen inputs. The public menu default remains V2. V3 FPS/RAM rows are measured independently; no V2 number is relabelled.
- hors-v2 uses gap 3 / batch budget 2048 in this canonical twelve-entry cart, retaining the v1 byte-span payload sizes to fit the same cartridge budget. Its independent pictures and guarded vector-page reuse are built in a private assembly tree. The seven-entry Demo Cart 2.0 uses separate measured encoding choices and is reported in its own section above.
- The public matrix compares released renderer generations. The authored-scene diagnostic rows preserve the unchanged V4–V10 productions.
- This table compares preserved renderer implementations under one **external comparison PLAY ALL wrapper**, not the exact historical release cartridges. The V9 normal PLAY ALL controller is used for every method. Its identical timer instructions live at `$0334` instead of `$c700`, because resident data occupies `$c700`; launch metadata is cached before loading and shared menu data restored between entries. Renderer code is unchanged apart from the existing cartridge IRQ-vector redirection. All these wrapper adaptations are generated outside the repo.
- Resident and streamed methods have different memory/ROM costs. A faster resident method does not imply it can hold the larger HiFi datasets. Compare the same named animation and sample count.
- A frame count tie is reported as a tie; a few extra samples over roughly 30 seconds are a small gain. Compare individual animations before quoting a suite total.
- Full bitmap and colour verification covered **25,109 completed pictures**. Raw traces, cartridge hashes, per-entry oracle hashes, unsupported-build reasons and individual results remain in the external workspace.
- These measurements do not establish a universal performance floor or guarantee behavior for untested inputs.

## Reproduce the historical renderer matrix

Run from the repository root. The tool defaults to ignored `comparison-tests/`; an external `--workspace` is also supported. It creates an isolated source snapshot and never writes old test cartridges into `examples` or `build` in this checkout. Python, 64tass, cartconv and PAL VICE with its data files are required.

```bash
python tools/compare_renderers.py \
  --workspace ../c64-renderer-comparison \
  --tass 64tass --cartconv cartconv --vice x64sc \
  --vice-data /usr/local/share/vice

# Only after the complete run succeeds:
cp ../c64-renderer-comparison/PERFORMANCE_COMPARISON.md docs/PERFORMANCE_COMPARISON.md
python tools/compare_renderers.py --check
```

Future demos: `--current-demos` compiles the current registry once and tests every resulting named entry across methods. Alternatively pass `--reference-json dataset.json.gz` in the `c643d-vector-reference-v1` format. Dataset files are saved outside tracked source and frozen for all methods. RAM-limited resident combinations are reported as N/A without dropping frames; bank capacity/build failures stop the comparison rather than silently simplify it. New renderer generations must be added to `METHODS` and the supported builders; chart rows themselves come from the data, not a twelve-row constant.

Optional pacing: `--max-fps 10` creates separate paced comparison carts after the uncapped pass. Integer rates 1–50 are supported; 10 FPS holds five PAL refreshes, while 12 FPS alternates four/five. `--lock-to-min-fps` measures two complete uncapped animation cycles, chooses a fixed per-demo refresh interval from the worst frame plus one refresh guard, then builds and verifies the paced copy. These options are mutually exclusive and **off by default** (`fps locking: not set`). A fixed cap cannot make an overloaded renderer meet a deadline; reports include observed hold intervals and missed deadlines. Pacing applies to these experimental menu reels, not the unchanged authored-scene timing or normal shipped cartridges. Paced/subset runs do not generate the release chart.

Use `--resume` only with the same source/tool fingerprint and options. Logs and JSON reports stay outside the repo. Archive that workspace with the release if long-term raw evidence is needed.

**Historical matrix gate:** the following fingerprint belongs to the recorded matrix version. Use `report_gmod3_performance.py --check` for the current HORS-V4 section. To replace the historical matrix with a fresh run, run its `--check` before publishing. If renderer code, builders, input assets, examples, version or this tester changes, rerun the complete uncapped matrix and replace this chart before tagging. Preserve old method rows; add new generations to the tester and regenerate. Never silently copy old numbers into a changed workload. Capped runs are separate experiments and must not replace this uncapped baseline.

<!-- comparison-input-sha256: 6dde2d3bf99a5197c2a33e645196a06976974c494963aab655a52dedd94cb5c1 -->
<!-- comparison-source-version: 0.7.9 -->
