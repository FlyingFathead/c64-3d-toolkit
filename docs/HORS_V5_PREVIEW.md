# HORS-V5-c1 clear optimizer preview

Since checkpoint 006, this implementation is explicitly named **V5-c1**.
`hors-v5` and `hors-v5-ef` retain this renderer. The separate
[V5-c2 candidate](HORS_V5_CANDIDATES.md) adds colour-transport selection without
replacing c1 or changing the default colour-overlap policy. The measurements
below describe the original c1 checkpoints.

HORS-V5 is an explicit development choice in 0.8.2-dev3. HORS-V4 remains the
default; EasyFlash is the default cartridge. GMod3 remains a V4 option and
GMod4 remains on the roadmap. V5 currently builds EasyFlash only.

```sh
python c643d.py build --scene scene.c643dscene --renderer hors-v5 --cart-type easyflash
python c643d.py build --shape torus --renderer hors-v5 --interactive-cart
```

V5 searches a bounded set of byte-clear plans per picture, using the metadata
space left by the existing colour plan. It keeps the existing cell-clear plan
as a candidate and clears eight bytes per unrolled group. The CPU cost model
only ranks plans; elapsed VICE measurements include fetch, IRQ and VIC costs.
It does not change source geometry, pixels, colours, order, samples or pacing.
The existing independent-picture format and three buffers are retained.
Clear metadata belongs to the picture actually stored in each recycled slot;
it does not assume forward-only playback or an adjacent source frame.

The implementation patches an isolated build staging tree. It does not edit
the V4/V3 assembly files. Hooks are restored after success or failure. No new
bitmap buffers or lookup-table RAM are allocated; the byte-clear routine is
larger. The assembler still enforces the existing memory layout. ROM usage can
rise or fall because clear metadata affects packing.

## Repeat a private scene comparison

Use an exported `.c643dscene` file. This command builds both versions from one
shared host frame set and keeps generated assembly, oracles, CRTs, reports and
previews outside the checkout. It uses the ordinary wireframe build defaults,
including source colours and the four-refresh minimum scene hold. It ignores
local config so both builds have a reproducible starting point.

```sh
python tools/benchmark_scene_pair.py ../c64-private-benchmarks/scene.c643dscene \
  --out ../c64-private-benchmarks/scene-comparison-001 \
  --name "Nightdrive Test" --capture \
  --tass 64tass --cartconv cartconv --vice x64sc
```

Add `--vice-data /path/to/vice-data` if the VICE installation needs it. Output
must be a new directory, so previous evidence is preserved. The report is
`comparison/comparison.md`; raw data and GIFs are beside it. GIFs reconstruct
completed VICE pictures and approximate their timing. Display FPS is measured
separately at the actual raster-IRQ display-slot update, not from the HUD.

For two already built looping EasyFlash cartridges with matching `.lbl`,
manifest, `runtime.prg` and `oracle.json` files:

```sh
python tools/compare_cart_stream.py path/to/baseline.crt path/to/candidate.crt \
  --baseline-root path/to/baseline-build-root \
  --candidate-root path/to/candidate-build-root \
  --out ../c64-private-benchmarks/comparison-002 --capture --vice x64sc
```

Build roots default to the toolkit checkout. The tool rejects mismatched
pictures, colours, order, frame count and the checked pacing/HUD settings.
It records CRT hashes/sizes, stage cycles, actual displayed high/average/low
FPS, mean/p95/worst holds, and bitmap/colour/border/HUD oracle checks. VICE uses
PAL defaults, seed 1 and sound off. One full display loop warms up, then two
loops are measured. The stage profiler separately samples a full loop after
three warmup pictures. Pixel checks cover two loops plus three pictures.

Exit status is nonzero if any check fails or aggregate performance regresses
beyond `--tolerance-percent` (default 0.5). The aggregate gate covers displayed
average, worst display hold, and mean/worst active render cycles. It does not
claim every individual picture got faster. Use `--tolerance-percent 0` for a
strict aggregate gate; small IRQ-phase differences can then fail a pair.
Finite endings, menu collections, exhibition playback and GMod3 are outside
this comparison command's current scope.

## Evidence and remaining work

The [Nightdrive Test and public control tables](PERFORMANCE_COMPARISON.md)
separate the original private cartridge from matched exported-scene pairs.
The original cartridge's V5 result remains unmeasured: it needs the matching
source export and build parameters. The supplied exports contain different
content, so their gains cannot be applied to that cartridge.

The current measured gain is modest: about 0.8% for the car-only scene and
5.9% for the car-and-road scene. Bitmap drawing remains the largest stage.
The later [full-history comparison](RENDERER_HISTORY_BENCHMARK.md) includes
the original cores and scene variants. V2 outperforms V5 on the car-and-road
input: the V4/V5 speedup does not make V5 the fastest available method.
Its colour/metadata policy is another concrete optimization target.
Next candidates are draw-span/batch tuning and reducing clear-then-overwrite
work, always with the same complete-picture oracle and display measurement.
The cost search does not yet automatically benchmark and choose among whole
pipeline configurations, nor optimize frame pacing or authored duration.

Checkpoint 003's full unit suite passed 331 tests with eight existing skips. Public pixel
and input checks supplement it, but do not exhaust every feature combination.
In particular this checkpoint does not revalidate every collection entry,
starfield/exhibition combination, physical cartridge or NTSC timing.
