# V9 direct cartridge byte spans — toolkit 0.6.9

**ONLY use normal PLAY ALL for A/B comparisons between rendering methods and
versions. F5 is an internal demo mode for exhibitions and MUST NOT be used for
benchmarking.** Normal PLAY ALL remains 10 seconds per entry. F5 retains its
15-second HiFi horse/sunflower holds; all other entries stay at 10 seconds.

## What V9 changes

V9 uses exactly V8's source pictures, vector optimization, byte-span selection,
colour metadata, frame payloads and sample cadence. It adds two runtime changes:

1. Selected byte pictures stream **directly from cartridge ROM to the recycled
   render bitmap**. V8 first copied those bytes into the $a000 staging buffer
   and then copied them again into bitmap RAM. V9 eliminates that intermediate
   transfer, and copies literal bytes eight at a time. Metadata is still cached.
2. The shared metadata/vector/directory page copier exploits its page-aligned
   destinations. It patches only destination high bytes and runs four 64-byte
   lanes backwards, removing the per-iteration CPY. Unaligned ROM sources retain
   their independent address carries; partial pages keep their bounded tail copy.

Vector pictures still use the existing V8 vector kernels and staging buffer.
All-vector animations compile out direct-byte dispatch entirely. No animation
samples, orientations, edges, colours or HUD data were removed. No regional
patches or dependencies on the previous displayed picture were introduced.

V9 is the default: `yunroll-cart-v9` / `yunroll-cart-v9-scene`. Resident PRG rendering
is available explicitly as `--renderer yunroll`; `build`, `cart-stream` and
`cart-demos` now default to V9 (authored inputs use V9-scene). FPS/RAM preferences
remain separate, and V8 and all older rendering methods remain selectable.

## Normal PLAY ALL A/B results

These are the original **native release-cartridge** measurements. The canonical
[cross-method lookup chart](PERFORMANCE_COMPARISON.md) uses one adapted PLAY ALL
controller for every generation, including resident methods. Its V9 FPS total
is 5,271 versus the native cart's 5,274: launch/timer phase can move a frame across
the observation boundary. The V9 renderer and shipped cartridge bytes have not
changed. Do not mix the two harnesses when calculating gains.

Measured in supplied **VICE 3.10 x64sc**, PAL, emulator defaults, fixed seed 1,
sound disabled, cartridge writeback disabled. Each preference was compared
against the corresponding **published V8 cartridge**, over **three normal
PLAY ALL loops**. The cartridges were not patched by the benchmark.

The monitor counts actual VIC bitmap-bank flips separately from logical sample
publications. Each observation window starts at the first timer-count IRQ and
ends at the automatic-next handler: approximately 499 PAL raster ticks for the
10-second setting. The initial visible picture precedes this window and is not
counted. Startup, loading and closing screens are excluded. FPS uses measured
emulated cycles, not host wall time or the on-screen integer FPS counter.
The reports record matching frame counts and original-oracle SHA-256 hashes.

### FPS preference

| Demo | V8 displayed FPS | V9 displayed FPS | Display flips across three windows |
| --- | ---: | ---: | ---: |
| TORUS | 13.460 | 13.460 | 402 → 402 |
| TORUS DENSE | 12.154 | 12.154 | 363 → 363 |
| CUBE | 26.820 | 26.820 | 801 → 801 |
| SPHERE | 14.666 | 14.666 | 438 → 438 |
| HORSE HEAD | 13.762 | 13.862 | 411 → 414 |
| SUNFLOWER TORUS | 12.154 | 12.154 | 363 → 363 |
| SUNFLOWER COLOR | 10.447 | 10.547 | 312 → 315 |
| SPACE HORSE SPIN | 10.648 | 10.746 | 318 → 321 |
| SPACE HORSE CRAWL | 22.903 | 23.505 | 684 → 702 |
| FALLING CUBES | 13.862 | 13.862 | 414 → 414 |
| HORSE HEAD HIFI | 10.145 | 10.246 | 303 → 306 |
| SUNFLOWER TORUS HIFI | 12.456 | 14.563 | 372 → 435 |

Total displayed frames: **5,181 → 5,274 (+1.8%)** across the twelve matching
windows repeated three times. HiFi sunflower gains **16.9%**, Space Horse Crawl
**2.6%**, and several vector demos gain approximately **0.7–1.0%**. Six entries
have the same displayed-frame count. No entry loses a displayed frame in this
measurement. Very small normalized FPS differences can remain because bounded
ROM-copy sections slightly shift the last timer IRQ.

These are workload-dependent gains, not a universal 17% improvement. The small
gains are often one additional displayed frame per ten-second entry. Repeating
the same reel improves reproducibility but does not turn it into coverage of
all possible future assets. Compare the whole reel and each entry, not only the
best case.

### RAM preference

Total displayed frames: **4,890 → 4,977 (+1.8%)**. HiFi sunflower improves from
**12.054 to 14.063 displayed FPS (+16.7%)**; Crawl gains **2.7%**. No entry loses
a displayed frame. Compare FPS with FPS and RAM with RAM.

Raw results: [V8 FPS](benchmarks/v9/play-all-v8-fps.json),
[V9 FPS](benchmarks/v9/play-all-v9-fps.json),
[V8 RAM](benchmarks/v9/play-all-v8-ram.json),
[V9 RAM](benchmarks/v9/play-all-v9-ram.json).

## Isolated diagnostics, not PLAY ALL benchmark scores

The [stage profiles](benchmarks/v9/ui-and-stages.json) explain the change:
HiFi sunflower's mean fetch stage drops from **17,759 to 7,776 cycles**.
The combined vector/byte draw stage remains near 38,550 cycles; the largest
saving is the transfer that is no longer needed.

[Standalone scene diagnostics](benchmarks/v9/validation.json) retain their
original cadence and all samples. Clean Marbles' mean active render cost falls
from **83,822 to 78,073 cycles (6.9%)**, but its approximately **28.975-second**
scene duration is unchanged at displayed precision. It still has **8/200**
frames over its render budget. Horse & Sunflower's all-vector FPS-preference
profile changes from approximately 4.279 to 4.301 samples/s, a modest saving.
These measurements diagnose renderer stages and scene pacing; use normal
PLAY ALL, not these isolated runs or F5, for the release's A/B benchmark.

## Memory and wire format

Frame payloads and packing locations are byte-for-byte identical to V8. Only
V9 directory entries change: bit 15 of the **frame byte length** marks a direct
byte picture. The true length is `length & 0x7fff`. The original payload's
record-count bit 15 remains V8's byte-span marker. V8 directories never receive
the new length flag. Scene-directory pages and picture aliases propagate it.
A whole frame still fits in one 8 KiB ROM chip; no span can cross that chip's end.

| Region | V9 use |
| --- | --- |
| $4000–$406f | Existing colour-reset helper |
| $4080–$40ff | Direct ROM mapping/pointer helpers when byte pictures exist |
| $4100–$42ff | Fetch/page-copy helpers and direct-span decoder |
| $4300–$43ff | Existing vector dispatch table, unchanged |
| $5000–$5bff | Existing three 1 KiB metadata caches |
| $a000–$bfff | Existing vector staging buffer, still allocated |

The largest menu helper ends at $42ff; assembly guards reject overlaps at
$4080, $4100 and $4300. No buffer allocation grew. Scene ending code at
$5c80–$5fff is preserved. An initial prototype placed the direct decoder at
$5e00; ending verification caught that conflict, and the release uses the guarded
helper gaps instead. The failing prototype is not included in shipped carts.

Each ROM-mapped critical section handles at most one 255-byte literal span.
It restores cartridge-off and RAM IRQ vectors before CLI/NOP. Writes beneath
KERNAL ROM reach the third bitmap's RAM. Interrupts can run between spans.
The IRQ handlers, presentation cadence and three-buffer ownership protocol are
unchanged. Metadata/vector copies remain bounded to 256 bytes per section.

The menu CRT remains **771,616 bytes**; Marbles clean/HUD remain **303,760 bytes**;
Horse & Sunflower remains **197,056 bytes**. V9 does not claim a smaller cartridge
or reclaimed staging RAM. This is a runtime throughput improvement.

## Build and verify

From the repository root, with 64tass, cartconv and x64sc on PATH:

```bash
python tools/build_v9_examples.py
python tools/build_v9_examples.py --prefer ram
python -m unittest discover -s tests
python tools/verify_v9_kernels.py --vice-data /path/to/vice-data
python tools/verify_v9_examples.py --vice-data /path/to/vice-data
python tools/verify_v9_ui.py --vice-data /path/to/vice-data
python tools/verify_v9_preservation.py --tass /absolute/path/to/64tass

python tools/benchmark_play_all.py   examples/cart_demos/history/c643d-demo-v0.6.8-yunroll-cart-v8-all.crt   --vice-data /path/to/vice-data --report build/benchmark-v8.json
python tools/benchmark_play_all.py   examples/cart_demos/history/c643d-demo-v0.6.9-yunroll-cart-v9-all.crt   --vice-data /path/to/vice-data --report build/benchmark-v9.json
```

The example verifier rebuilds matching V8 FPS and RAM symbols outside `examples`
with the original 0.6.8 identity before comparison. For RAM benchmarking, use
the two `-ram.crt` files with distinct report paths.
Builders/verifiers accept explicit tool paths. The preservation verifier requires
a Git checkout containing commit `5025172`; source ZIP users can run the frozen
hash tests and the emulator checks without Git history.

[Kernel tests](benchmarks/v9/kernels.json) cover **337 mixed/boundary cases per
preference (677 completed pictures each)**, plus **257 additional cases per
preference (517 pictures each)** spanning ROML bank 63 to ROMH and the 256-entry
scene-directory boundary. Cases exercise maximum-length spans, page alignments,
empty/vector/byte switches, resident reuse, colours, and all bitmap slots.
The [example checks](benchmarks/v9/validation.json) cover all twelve entries,
all standalone scene samples, 84 menu handoffs/252 pictures across three styles,
and normal PLAY ALL controls. [UI checks](benchmarks/v9/ui-and-stages.json) cover
build screens, both Marbles endings and closing screens. F5 is checked separately
for [FPS](benchmarks/v9/exhibition-fps.json) and [RAM](benchmarks/v9/exhibition-ram.json);
these are functional tests only. Its key test injects a CIA matrix sample through
the monitor, then runs the production scanner and handler.

**139 Python tests pass.** All **118 historical assembly/CRT/PRG files** match
published v0.6.8. [Pristine rebuilds](benchmarks/v9/legacy-preservation.json)
confirm **108 V2–V8 FPS/RAM runtimes and nine frame-data images** remain identical.
All eight V9 cartridges preserve their corresponding V8 frame-payload hashes.
Tests use PAL VICE, not physical C64 hardware; NTSC timing has not been validated.

See [applying the release overlay](UPGRADING_0.6.9.md).

[See comparison chart for details on performance differences](PERFORMANCE_COMPARISON.md).

## Cartridge capacity

EasyFlash has 1 MiB of flash shared by code and data. See [cartridge capacity and optimization budgets](CARTRIDGE_CAPACITY.md) for file-size accounting and larger hardware targets.
