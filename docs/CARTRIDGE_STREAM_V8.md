> Historical version documentation. Current builds and prebuilt examples use [hors-render-v2](HORS_RENDER_V2.md); see [0.7.2 release instructions](RELEASE_0.7.2.md). Older preview binaries are in prior release ZIPs or the external local archive.

# V8 adaptive byte spans — toolkit 0.6.8

> Historical renderer guide. Release labels, defaults, measurements and
> reproduction commands below refer to this generation, not the v0.7.0 defaults.
> v0.7.0 uses hors-render-v1 / hors-render-v1-scene; see
> [current builds](V10_TESTING.md) and the [matched comparison](PERFORMANCE_COMPARISON.md).
> Superseded generated outputs live in the optional sibling
> `../c64-3d-toolkit-history/` archive. Old paths in the historical examples
> may require that archive or the corresponding release checkout.

V8 is a separate opt-in renderer. All prior renderer sources and shipped CRT/PRG
files are retained byte-for-byte. The default PRG renderer remains `yunroll`;
`cart-demos` still defaults to V4. Select `yunroll-cart-v8` or
`yunroll-cart-v8-scene` explicitly. FPS remains the default preference.

The final release keeps rc1's renderer/encoder code and all eight frame streams
identical. Version text and V8 menu/build screens identify 0.6.8. A V8-only
F5 internal demo mode extends the two HiFi holds for exhibitions; normal
PLAY ALL remains unchanged at 10 seconds per demo. The original
rc1 reports remain under [benchmarks/v8/rc1/](benchmarks/v8/rc1/); current report
links below refer to checks of the final artifacts.

## What changes

V8 adds **host-rasterized sparse bitmap byte spans** alongside the existing V7
vector format. It is a hybrid renderer: qualifying pictures are reproduced by
copying literal bitmap bytes, while the others are rasterized from vector runs
on the C64. This is a distinct rendering method, not a faster vector kernel.
Projection, visibility, geometry, colours, samples and sample order are unchanged.

The compiler first applies the unchanged V5/V7 lossless vector optimizers and
selective clearing. It then builds an alternative sparse byte representation
of each complete picture. Adjacent occupied bytes may share a span across up
to two zero bytes, with a maximum span length of 255. A byte representation is
selected only when it is **strictly smaller** than that picture's V7 payload.
Otherwise the exact V7 vector payload is used. No frame becomes larger, and
no animation samples are removed to meet cartridge capacity.

This conservative size rule is not a universal execution-time cost model.
The measured gains below establish its benefit on the supplied examples.

## Runtime and format

Metadata and its per-slot cache stay unchanged. After metadata, the little-endian
16-bit record count has two meanings:

- Bit 15 clear: the existing V7 vector-record stream.
- Bit 15 set: the lower 15 bits count byte spans. Each span is
  `(bitmap_offset_low, bitmap_offset_high, length, literal_bytes...)`.
  Length is 1–255, and the offset is relative to the current bitmap slot.

An 8 KiB block cannot contain enough legal V7 vector records to use bit 15,
so the distinction is unambiguous. V8 streams must be consumed by V8. Existing
V2–V7 encoders and decoders keep their original wire formats.

The target slot is recycled with the original clearing and colour-reset path
before either representation is drawn. Byte spans contain complete desired
values and need no previous-picture reference. Triple buffering, duplicate
picture reuse, directory paging, playback holds and bank-copy critical sections
are inherited. This release does **not** implement buffer-dependent region deltas.

The new byte-copy routine occupies previously unused space below `$4300` in the
existing helper allocation. No new bitmap, cache, lookup table or staging buffer
is allocated. When an entire animation contains no byte-mode pictures, both
byte-mode dispatch and its helper are compiled out. `--prefer ram` retains
V7's compact Y loops; byte-mode pictures use the same copy routine in either
preference. RAM mode is deliberately slower on vector-heavy content.

Manifests identify `wire_format`, `byte_span_frames` and each directory entry's
`encoding`. The legacy `runs` field still counts the source vector records;
for byte pictures, the span count is encoded in the actual stream header.

## PLAY ALL timing and comparison rules

Normal PLAY ALL retains **10 seconds for every demo**, including both HiFi
entries, matching previous releases and V8 rc1.

Press **F5 at the V8 menu** to start a separate exhibition loop, intended for
a real C64 on display. HiFi horse head and HiFi sunflower torus run for
15 seconds each; the other demos stay at 10. SPACE skips, F1/RUN-STOP exits,
and the closing thank-you screen still leads into the next loop. Returning
to the menu or launching normal PLAY ALL clears exhibition mode.

Use normal PLAY ALL for matched showcase timing comparisons. Exhibition adds
10 seconds per full cycle and is not a benchmark mode. The previously collected tables below are isolated per-entry renderer profiles
with autoplay inactive, not PLAY ALL benchmark scores.
An explicit non-default `--play-all-seconds N` uses N seconds uniformly in both
modes. The manifest records exhibition durations separately from normal timing.

## Matched PAL VICE results

VICE 3.10 x64sc, 64tass 1.59.3120, PAL at 985,248 cycles/s. The comparison uses
the original shipped V7 CRTs and original pixel/colour oracles, across all three
slots. Menu throughput excludes startup and covers two loops plus three samples.
The new release strings alter startup/IRQ phase slightly; differences below
0.01% in fallback-only demos are timing alignment, not a material speed gain.

| Demo | V7 FPS | V8 FPS | Change |
| --- | ---: | ---: | ---: |
| Torus | 13.505 | 13.505 | essentially unchanged |
| Torus dense | 12.105 | 12.105 | essentially unchanged |
| Cube | 27.136 | 27.136 | essentially unchanged |
| Sphere | 14.787 | 14.787 | essentially unchanged |
| Horse head | 13.874 | 13.874 | essentially unchanged |
| Sunflower torus | 12.122 | 12.122 | essentially unchanged |
| Sunflower colour | 10.522 | 10.523 | essentially unchanged |
| Space Horse Spin | 10.669 | 10.669 | essentially unchanged |
| Space Horse Crawl | 16.623 | 22.793 | +37.1% |
| Falling cubes | 14.275 | 14.275 | essentially unchanged |
| HiFi horse head | 10.018 | 10.087 | +0.7% |
| HiFi sunflower torus | 6.989 | 12.469 | +78.4% |

Byte spans are selected for 19/32 Crawl pictures, 2/128 HiFi horse pictures,
and 97/128 HiFi sunflower pictures. Other menu entries keep vector drawing.

| Clean Marbles | V7 FPS preference | V8 FPS preference |
| --- | ---: | ---: |
| Mean render cycles | 125,940.87 | 83,821.83 |
| Worst render cycles | 282,700 | 282,735 |
| Samples exceeding render budget | 47/200 | 8/200 |
| Scene duration, excluding intro/ending | 30.45095 s | 28.97462 s |
| Scene samples/s | 6.56794 | 6.90259 |

Mean rendering cost drops **33.4%**; scene throughput rises **5.1%** because
samples retain their seven-PAL-tick minimum holds. The worst frame stays
essentially unchanged, including a small dispatch/IRQ timing difference.
116/200 Marbles samples use byte spans. All 200 samples, the intro, credits
and BASIC epilogue are preserved.

**Horse & Sunflower is unchanged at about 4.28 samples/s.** None of its byte
alternatives passes the size rule, so it retains vector rendering and still
misses its requested six-tick cadence. V8 is not a fix for this scene yet.
Its RAM comparison is about 4.08 samples/s, the expected compact-kernel trade-off.

| Cartridge | V7 bytes | V8 bytes |
| --- | ---: | ---: |
| Twelve-demo menu | 804,448 | 771,616 |
| Marbles, clean or HUD | 353,008 | 303,760 |

Physical C64 hardware, NTSC timing, host display smoothness and audio have not
been validated in this pass. No audio implementation is added.

## Build and verify

```bash
# Rebuild four FPS examples from the preserved V4/V7 references; no Blender:
python tools/build_v8_examples.py
# The four RAM comparisons have separate -ram names:
python tools/build_v8_examples.py --prefer ram

# Ordinary compiler entry points:
./build.sh cart-demos --stream-renderer yunroll-cart-v8
python c643d.py cart-stream --renderer yunroll-cart-v8 --object horse_head

python -m unittest discover -s tests
python tools/verify_v8_kernels.py --vice-data /path/to/vice-data
python tools/verify_v8_examples.py --vice-data /path/to/vice-data
python tools/verify_v8_ui.py --vice-data /path/to/vice-data
```

The examples/kernel verification tools accept `--tass`, `--cartconv` and `--vice` paths.
The examples verifier rebuilds V7 symbols with its original 0.6.7 build identity
in `build/`, checks its payload against the shipped cartridge, and never rewrites
that shipped cartridge. Builders do not change older renderer sources or samples.

[Full comparison](benchmarks/v8/validation.json) includes both preferences,
all twelve menu demos, all 200 Marbles samples in clean/HUD variants, the 84
Horse & Sunflower samples, 84 menu launches/252 pictures across three styles,
and the timed PLAY ALL cycle/skip/return paths.
[F5 internal-demo checks](benchmarks/v8/play-all-exhibition.json) and
[RAM checks](benchmarks/v8/play-all-exhibition-ram.json) verify the F5 matrix
sample, menu dispatch, all durations, wrap, skip and return to normal playback.
These are functional checks, not performance benchmarks. The keyboard test
injects the CIA row sample through the VICE monitor; real hardware key input
has not been tested.
[Byte-kernel checks](benchmarks/v8/kernels.json) exercise 337 cases per
preference: byte lengths, source/destination page crossings, 255/256/257 span
counts, mixed vector/byte pictures, empty frames, colour-only changes, resident
reuse and a scene-directory page crossing. Each preference checks 677 completed
pictures. [UI and stage checks](benchmarks/v8/ui-and-stages.json) cover six
build screens, both clean Marbles endings, six closing-screen cases and fresh
V7/V8 HiFi sunflower stage profiles.

See [installing the overlay](UPGRADING_0.6.8.md). The default cleanup archives only superseded 0.6.8-rc1 V8 menu carts and metadata
outside the checkout, verifies the archive, then removes those rc1 example files.
Earlier renderer comparisons and final V8 artifacts remain intact.

## Historical preservation

The [pristine-build comparison](benchmarks/v8/legacy-preservation.json) confirms
72 V2–V7 runtimes and six complete frame-data images match pristine 0.6.7.
All **130 Python tests pass**. The source tests independently check SHA-256 hashes of 102 historical assembly
and CRT/PRG files. The original `step`, `bytechunk` and `yunroll` code and shared
projection/rasterization compiler remain unchanged.

VICE enables EasyFlash cartridge writeback by default in the supplied build;
it can rewrite a CRT title header even in a read-only playback test. The
verification commands now pass `+easyflashcrtwrite` so reference files cannot
be rewritten on emulator exit. No original CRT changes are shipped.

**ONLY use normal PLAY ALL for A/B comparisons between rendering methods and
versions. F5 is an internal demo mode for exhibitions and MUST NOT be used for
benchmarking.**
