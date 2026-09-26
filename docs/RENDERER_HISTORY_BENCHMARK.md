# Full renderer history benchmark

`tools/benchmark_renderer_history.py` covers the original `step`, `bytechunk`
and `yunroll` cores; `yunroll-cart-v2` through `v10`; HORS-V2 beta/stable;
HORS-V3; preserved HORS-V4 EasyFlash; experimental HORS-V5; and the native
scene backends, including HORS-V4 GMod3. Accepted CLI aliases are accounted
for in the report rather than counted as independent speedups.

The default also runs the original public CUBE / 36-picture control. This
allows the resident renderers to be measured even when a private scene is too
large for their tables. It does not replace or simplify the private scene.
The complete original twelve-animation results remain in
[PERFORMANCE_COMPARISON.md](PERFORMANCE_COMPARISON.md); this new control is
not a claim that every historical workload has been rerun.

## Run

Python, 64tass, cartconv, PAL VICE and its data files are required. Pillow is
needed for optional `--capture`. Run from the checkout; use a new external
output directory. Each scene is compiled once and frozen for every method.
The input files and repository are never modified.

```bash
benchmark_run=$(date +%Y%m%d-%H%M%S)
python3 tools/benchmark_renderer_history.py \
  --scene ../private-scenes/car-only.c643dscene \
  --scene ../private-scenes/car-and-road.c643dscene \
  --out "../private-renderer-history-${benchmark_run}" \
  --name 'Nightdrive Test' \
  --vice-data /usr/local/share/vice \
  --workers 3 --capture
```

Omit `--scene` to run just the public cube control. `--core-only` is a labelled
subset that omits native scene builds. `--loops` changes the PLAY ALL visit
count (default 3), not the two complete native-scene measurement loops.
The V4/V5-only `benchmark_scene_pair.py` remains available for quick checks.

Outputs include `comparison.md`, `comparison.json`, selector coverage, source
and tool hashes, CRTs, logs, frame oracles, stage profiles and native previews.
All private inputs and derived evidence stay outside the checkout. A nonzero
exit indicates an incomplete or failed run. Read the failed rows and logs;
do not treat a partially populated report as a passing comparison.

## Two measurement protocols

- **Original cores:** unchanged renderer instructions inside the existing
  common V9 normal-PLAY-ALL controller; three ten-second visits, no FPS cap.
  FPS and supported RAM preferences are measured separately. The stable V2
  and V3/V4/V5 comparison encoders use gap 3 / batch budget 2048. All methods
  receive the same complete pictures, colours, order and HUD. The test-only
  controller relocates its timer away from resident frame data and shortens
  long development-version menu captions. Each version owns its build path.
- **Native scenes:** ordinary automatic playback of every authored sample,
  four PAL refreshes minimum hold, one complete warmup loop and two measured
  loops. Native CLI defaults retain gap 6 / batch budget 2048. GMod3 retains
  its own HUD and controller; its row is a native backend comparison, not
  an isolated bank-copy cost. VICE flash writeback is explicitly disabled.

Both use PAL VICE defaults, sound disabled, seed 1. FPS counts actual displayed
pictures in emulated C64 time. High/low values describe shortest/longest
observed display holds; they are not sustained throughput. Pixel checks cover
two loops plus three pictures across all three buffers. Input picture hashes
must match each built oracle, including colours and order.

Compare rates within a table. Do not merge the uncapped core rates with the
paced native scene rates or the earlier standalone V4/V5 pair. Differences in
encoding, controller work and pacing affect the result.

## N/A and failures

A confirmed capacity failure has an **N/A** score and the exact reason, such
as an eight-bit record counter, frame-pointer arena, metadata cache, staging
buffer or cartridge allocation. No source samples, geometry or colours are
removed to force a result. Unknown build errors, assembler failures and pixel
mismatches are **FAIL**, never N/A. Missing reports are also failures.

This compares generations on fixed inputs. It is not by itself an old-release
versus new-release regression test. Preserve the separate V4 byte-preservation
and V4/V5 matched gates. Physical C64 hardware and NTSC remain unmeasured.
