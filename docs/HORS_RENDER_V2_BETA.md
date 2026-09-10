> Archived beta1 documentation and measurements. **hors-render-v2 is the stable 0.7.2 default**; see [current integration](HORS_RENDER_V2.md) and [stable results](HORS_RENDER_V2_RESULTS.md). Older release ZIPs preserve the tools used for this beta evidence.

> Historical version documentation. Current builds and prebuilt examples use [hors-render-v2](HORS_RENDER_V2.md); see [0.7.2 release instructions](RELEASE_0.7.2.md). Older preview binaries are in prior release ZIPs or the external local archive.

# hors-render-v2 beta 1

An opt-in experiment based on the uploaded 0.7.1 workstation snapshot, with
the toolkit working version advanced to **0.7.2** at the user's request. The
default renderer and preserved examples remain v1. No release tag is made.

## What is implemented

- A byte-span encoder that tries different zero-gap bridges and groups spans
  into cartridge-mapping batches. Colour metadata remains independent.
- A matching decoder with explicit ownership of the former vector-dispatch
  page at `$4F00–$4FFF`. Every picture must use direct byte spans. A picture
  that needs vector fallback or exceeds an 8 KiB bank is rejected.
- Standalone looping scene builds through `c643d.py build --scene ...
  --renderer hors-render-v2-beta1`, plus the separate Demo Cart 2.0 builder.
- A measured multi-pass scene search. Compile geometry once; build each
  encoding/preference/hold candidate in isolation; verify against the same
  oracle; measure actual display changes; save CLI, Markdown, JSON and CSV
  results; rank only passing candidates under the selected objective.
- Correct handling of the selected menu style in the verifier, retained VICE
  error diagnostics, and SPACE-start handling in the PLAY ALL benchmark.
  These fix test-harness problems exposed by the preview integration.

Each frame remains a complete independent picture. Production-specific
buffer-relative delta encoding is **not** included in this generic beta.
General per-frame mixing of codecs is future work, not a shipped feature.

## Use the beta directly

```bash
python c643d.py build \
  --scene examples/autotune/colour-cube.c643dscene \
  --renderer hors-render-v2-beta1 --prefer fps --frame-ticks 1 \
  --v2-draw-gap 6 --v2-batch-budget 2048 --no-text-overlay \
  --output colour-cube-v2-beta --output-dir ../hors-v2-direct
```

Beta 1 supports looping authored scenes. Intro/ending integration is rejected
explicitly. The existing Blender export path feeds the same scene backend,
but the beta validation supplied here uses `.c643dscene` inputs, not a new
Blender export. The regular `cart-demos` command remains on stable backends;
use `tools/build_demo_cart_v2.py` for the beta menu showcase.

## Multi-pass optimization

```bash
python tools/autotune_scene.py examples/autotune/colour-cube.c643dscene \
  --out ../hors-v2-cube-search --jobs 4 \
  --preferences fps ram --ticks 1 2 3 4 \
  --plans optimized raw --gaps 3 6 10 --batches 1024 2048 \
  --tass 64tass --cartconv cartconv --vice x64sc \
  --vice-data /usr/local/share/vice
```

This is a bounded search over the requested candidate matrix, not a proof of
the maximum possible FPS. Default objective `fps` selects the best measured
throughput. `--objective steady` requires observed holds to equal the chosen
fixed interval. Differences smaller than one display update per measurement
window are treated as ties. Ties prefer a longer minimum hold, then lower
measured stage cost, then smaller frame payload. The fastest, slowest and
smallest eligible choices are retained in `selection.json`.

Use a new `--out` directory for each run. Workers are separate Python
processes, allowing independent VICE instances. Failed builds have logs and
failure rows; they are never assigned invented FPS. If no candidate meets
the constraints the command fails. Source frames are never removed to force
a speed or capacity result. The initial analysis records source identity,
tool paths, frame counts, geometry and per-frame drawing/metadata counts.

`--width 320` enables full-width exported scenes. The default 256 preserves
the normal toolkit scene framing. Use `--mono` for monochrome source tests.
Minimum holds can change animation tempo; the search does not resample the
animation or preserve authored duration automatically. `--prefer fps` alone
still selects kernels; it does not silently launch a benchmark search.

## Measurements and memory

Standalone diagnostics measure real display-slot changes after VIC register
updates, over at least ten emulated seconds and two source cycles, following
warm-up. Every observed bitmap and visible colour is checked, and complete
unique-picture coverage is required. Separately, the existing verifier checks
all bitmap bytes and all 960 colour cells in completed pictures. Duplicate
picture shortcuts are tested; the legacy stage profiler is explicitly marked
unavailable for such inputs rather than giving misleading stage timings.

The stage-cost field includes elapsed emulated cycles in the measured stages,
with VIC/IRQ interference. It is not an isolated instruction-cycle count.
Reports include worst/p95 display intervals, observed hold distributions,
ROM payload/banks, PRG length and individual RAM allocation components.
PRG length includes gaps. Neither its length nor the sum of overlapping
allocation categories is a total used/free RAM measurement.

The beta reserves no additional RAM; its helper occupies part of a reclaimed
256-byte vector-only page. The 8 KiB staging allocation is still reserved.
The batch-budget parameter is a host cost model, **not a measured hard IRQ
latency bound**; a single long span may exceed it. Physical C64, NTSC, SID
playback and arbitrary production interrupt integrations are not validated by
these tests. The normal geometry compiler continues to reject wholly invisible
scene samples; compiler-level blank-picture handling is separately verified.

## Reproduce boundary checks

```bash
python tools/verify_hors_v2.py --help
```

The test builds 264 frames, a blank picture, directory paging beyond frame
255, and ROMH-only frame payloads. It checks 531 completed pictures and
explicit oversized-payload rejection. See the saved results for exact scope.

## Release gate

The full canonical matrix has been regenerated for 0.7.2, preserving all old
rows and adding v2 beta FPS/RAM rows. All 26 jobs and the
`compare_renderers.py --check` gate passed. See the results document for both
canonical and new-showcase tables. Rerun this gate after input changes.
Stable v2 adoption still depends on independent results and clean visual
output. No GitHub push, tag or publication is included.
