# yunroll-cart-v6: partial-byte drawing and direct metadata loading

> Historical renderer guide. Release labels, defaults, measurements and
> reproduction commands below refer to this generation, not the v0.7.0 defaults.
> v0.7.0 uses hors-render-v1 / hors-render-v1-scene; see
> [current builds](V10_TESTING.md) and the [matched comparison](PERFORMANCE_COMPARISON.md).
> Superseded generated outputs live in the optional sibling
> `../c64-3d-toolkit-history/` archive. Old paths in the historical examples
> may require that archive or the corresponding release checkout.

> Historical menu cartridges and the former `examples/old/` paths are now in the
> separate oldies ZIP. See [v0.6.7 cleanup and archive access](UPGRADING_0.6.7.md).

Toolkit **0.6.7-rc3** adds opt-in `yunroll-cart-v6` and
`yunroll-cart-v6-scene`. The released V5/V4 cartridges and renderer sources are
preserved. V4 remains the default menu renderer, and V2 the standalone
`cart-stream` default. The [README variant table](../README.md#renderers)
explains each generation and V5's cartridge-size savings.

## What changes on the C64

1. **Partial X-major byte accumulation.** Heads and tails accumulate adjacent
   bits in A and update bitmap memory at row changes, cell boundaries or line
   completion. Both directions retain the original DDA decisions. Full aligned
   eight-pixel chunks keep their existing lookup-table path.
2. **Direct metadata loading.** Recycle the destination slot using its old
   metadata first. Fetch the incoming clear/colour metadata directly into that
   slot's cache, then fetch the line count and records into staging RAM. This
   removes the subsequent staging-to-cache copy.

For a picture already resident in a bitmap slot, V5's reuse path still bypasses
recycle/fetch/colour/drawing and retains logical sample timing. A colour change
is part of picture identity. No new stream format, sample reduction, mesh
reduction, prerendered bitmap playback or shorter presentation delay is involved.

The metadata destinations remain `$5000`, `$5400`, `$5800`, with 1 KiB per
slot. Only line count/records now start at `$a000`; the allocated staging region
remains 8 KiB. The source advances by the exact metadata length, including a
partial-page tail. Full pages retain V5's four-section copy loop. Each critical
section copies at most 256 bytes, restoring cartridge-off / `$01=$35` before
allowing interrupts. Existing ROM bank boundaries and frame-size guards remain.

The profiler follows explicit labels in their execution order: directory/lookup
when present, recycle, fetch, colour, drawing, then publication and advance.
V6 has no `profile_cache` stage; V5's labelled cache stage remains supported.
Elapsed stage costs include VIC stalls and IRQ work.

## Matched PAL VICE results

Measured with VICE 3.10 `x64sc`, PAL, and 64tass 1.59.3120. The menu runs two
complete cycles plus three frames per entry. Each completed bitmap and all 960
geometry colour cells are checked against the frozen V5 build's original,
pre-optimization oracle, across all three bitmap slots. Those oracle files also
match the original samples recovered from the released V4 cartridge byte for
byte. Startup is excluded. Emulator warp changes host execution speed, not the
emulated cycle counts used here.

These menu FPS values are **completed-frame throughput**. The longest interval
columns include queue/IRQ costs; they are not isolated drawing costs or a
measurement of host display smoothness. No physical C64 or NTSC result is claimed.

| Demo | Samples | V5 FPS | V6 FPS | Gain | V5 longest interval, cycles | V6 longest interval, cycles |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| TORUS | 32 | 12.370 | 12.771 | 3.24% | 92,856 | 90,183 |
| TORUS DENSE | 32 | 10.950 | 11.298 | 3.18% | 105,734 | 102,422 |
| CUBE | 36 | 25.809 | 27.092 | 4.97% | 42,644 | 40,908 |
| SPHERE | 24 | 13.727 | 14.423 | 5.07% | 77,278 | 75,046 |
| HORSE HEAD | 32 | 12.501 | 12.949 | 3.58% | 93,133 | 89,986 |
| SUNFLOWER TORUS | 28 | 11.007 | 11.144 | 1.24% | 100,730 | 99,380 |
| SUNFLOWER COLOR | 20 | 9.434 | 9.786 | 3.73% | 117,087 | 113,706 |
| SPACE HORSE SPIN | 24 | 10.196 | 10.573 | 3.70% | 110,349 | 106,362 |
| SPACE HORSE CRAWL | 32 | 14.829 | 15.534 | 4.76% | 86,453 | 84,502 |
| FALLING CUBES | 18 | 13.344 | 14.063 | 5.39% | 95,706 | 89,529 |
| HORSE HEAD HIFI | 128 | 8.448 | 8.742 | 3.48% | 130,775 | 127,186 |
| SUNFLOWER TORUS HIFI | 128 | 5.947 | 6.139 | 3.23% | 216,697 | 211,811 |

The partial-X change alone improved the five initial comparison entries by
0.42–1.87%. The table above includes both accepted changes. These modest gains
are measured, and do not imply that additional unrolling is always worthwhile.
Full measurements, CRT hashes, baseline oracle hashes and verification results
are in [v5-v6-validation.json](benchmarks/cart_demos/v5-v6-validation.json).

## Marbles: rendering versus its presentation cadence

Both candidates use the exact same 200 samples, seven PAL raster ticks per
sample and finite ending. The following comparison is the **clean build**;
intro/credits are excluded, while the final scene display hold is included.

| Measurement | V5 | V6 |
| --- | ---: | ---: |
| Mean render cycles | 142,996.55 | 137,811.51 |
| Worst render cycles | 304,457 | 297,383 |
| Frames over the 137,592-cycle render budget | 107 | 93 |
| Scene seconds | 32.06692 | 31.42851 |
| Scene samples per second | 6.23696 | 6.36365 |

Mean rendering cost falls **3.63%**, while scene throughput rises **2.03%**.
Faster frames wait for the existing presentation cadence, so the two gains are
different. The render-budget count measures work above the deadline; queueing
and publication mean it is not an exact count of visibly late frames.

| Mean elapsed stage cycles | V5 | V6 |
| --- | ---: | ---: |
| Directory | 133.87 | 133.44 |
| Recycle bitmap and colours | 18,392.25 | 18,322.10 |
| Fetch | 21,426.57 | 22,193.75 |
| Cache metadata | 4,367.53 | Removed |
| Apply colours | 5,909.91 | 5,964.95 |
| Draw lines | 92,766.43 | 91,197.27 |
| Publish wait | 13,486.11 | 15,526.31 |

Fetch by itself is slightly more expensive because the destinations are split;
fetch plus metadata caching is cheaper overall. Drawing is also cheaper. More
publish waiting is expected when rendering finishes earlier. The full per-frame
stage reports and both HUD/clean output checks are in
the Marbles report (historical report, external archive required; original path: `../examples/cart_marbles/history/v5-v6-validation.json`).

## RAM and cartridge size

The following assembled regions are from the matched **regular horse** menu
payload. Totals include startup/runtime data and HUD in the first region; this
is not the whole C64 memory map.

| Region / allocation | V5 bytes | V6 bytes | Change |
| --- | ---: | ---: | ---: |
| Main runtime and HUD (`$0801` onward) | 3,455 | 3,570 | +115 |
| Copy helper (`$4100` onward) | 394 | 369 | -25 |
| Net of these resident regions | 3,849 | 3,939 | **+90** |
| Three bitmap allocations | 24,576 | 24,576 | 0 |
| Three screen allocations | 3,072 | 3,072 | 0 |
| Line staging allocation | 8,192 | 8,192 | 0 |
| Three metadata caches | 3,072 | 3,072 | 0 |

Lookup tables and the inherited Y-block/picture-reuse code are unchanged.
The partial-X region grows 118 bytes; removal of the cache call and smaller
helper reduce the net cost. The fixed allocations are not reclaimed by this
candidate, even where less staging data is used.

| Released cartridge | V5 CRT bytes | V6 CRT bytes | Vector bytes in each |
| --- | ---: | ---: | ---: |
| Twelve-demo menu | 927,568 | 927,568 | 538,330 |
| Marbles, clean | 418,672 | 418,672 | 323,159 |
| Marbles, HUD | 418,672 | 418,672 | 323,159 |

The new code fits within the already stored cartridge chips. V5's stream
reduction is inherited; V6 introduces no additional ROM data compression.
Compact/balanced/speed-focused profiles remain
[future work](ROADMAP.md#memory-and-cpu-profiles-independent-of-the-application).
They should be useful to demos as well as games, with sequence/input handling
separate from shared drawing and explicit memory ownership.

## Run and rebuild

From the repository root:

```bash
x64sc -cartcrt examples/cart_demos/c643d-demo-v0.6.7-rc3-yunroll-cart-v6-all.crt
x64sc -cartcrt examples/cart_marbles/history/dont_lose_your_marbles-yunroll-cart-v6-scene-clean.crt
x64sc -cartcrt examples/cart_marbles/history/dont_lose_your_marbles-yunroll-cart-v6-scene.crt

# All three shipped V6 examples, from exact released vector samples:
python tools/build_v6_examples.py --tass 64tass --cartconv cartconv

# Ordinary build commands also support V6:
./build.sh cart-demos --stream-renderer yunroll-cart-v6
python c643d.py cart-stream --renderer yunroll-cart-v6 --object horse_head
```

`build_v6_examples.py` reads the supplied V4 menu and clean Marbles cartridges,
validates their frame blocks against the manifests, applies the inherited V5
lossless optimization, and assembles V6. It needs 64tass and VICE's `cartconv`,
but no Blender installation or physics rebake. Rebuild products stay in `build/`;
final carts and manifests go into the existing example folders. The native
build screen displays `0.6.7-rc3` / `yunroll-v6` on white-on-black, waits about
three seconds or accepts SPACE, then enters the menu or authored Marbles intro.

For verification after building, adjust tool paths and `--vice-data` to the
installed VICE data directory as needed:

```bash
python -m unittest discover -s tests
python tools/verify_cart_stream.py   examples/cart_demos/c643d-demo-v0.6.7-rc3-yunroll-cart-v6-all.crt --menu-entry 4
python tools/verify_cart_stream.py   examples/cart_marbles/history/dont_lose_your_marbles-yunroll-cart-v6-scene-clean.crt
python tools/profile_cart_stream.py   examples/cart_marbles/history/dont_lose_your_marbles-yunroll-cart-v6-scene-clean.crt   --report build/v6-marbles-profile.json
python tools/verify_cart_stream_edges.py --renderer yunroll-cart-v6
python tools/verify_v6_kernels.py --vice-data /path/to/vice-data
```

The example builders preserve pre-optimization oracles for these menu/scene
checks. The included matched report was additionally checked using the frozen
V5 oracles through `--oracle`, rather than using only the new builder's output.
Do that again when changing the compiler or optimizer itself.

## Verification coverage and limits

- All twelve menu entries: two loops plus three frames each, original geometry,
  colours, sample order, all three slots and wraparound.
- Both Marbles builds: all 200 frames against the original oracle; the clean
  build's complete finite ending also checks the greeting correction, BASIC
  banner, ghost message and stable idle cursor.
- 1,152 synthetic X-major cases, 2,307 completed frames: both directions,
  every X/Y phase pair, short heads, full chunks, tails and row transitions.
- A 270-sample scene with 231 resident reuses, consecutive holds, colour-only
  changes, cache misses and a directory-page transition. Its 16.186-second
  measured duration is within 0.1 second of the 16.160-second PAL hold budget.
- Zero, one, 255, 256, 257 and 512 runs; 255 clear spans; 1,024-byte metadata;
  a 255-frame ordinary directory; monochrome and colour paths.
- 75 menu navigation states covering all three styles, both directions,
  scrolling, wraparound, markers and stable headers/footers.
- All three build screens: approximately three-second timeout and immediate
  SPACE scan. The SPACE test drives the CIA column from the monitor; it does
  not test the host's keyboard event handling.
- 111 Python tests passed. PAL VICE validates the guest pipeline; physical
  EasyFlash, NTSC and audio coexistence remain untested.

The earlier V5 twitching was reported on NVIDIA/Linux/Wayland and absent on the
user's Windows 11 system. Host presentation is suspected, without a confirmed
driver or renderer diagnosis. This candidate changes measured guest work; it
contains no speculative host-stutter fix.

## Applying rc3

The changed-files ZIP is flat. With it saved next to the user's main project:

```bash
cd ~/NeuralNetwork/c64-3d-toolkit
unzip -o ../c64-3d-toolkit-v0.6.7-rc3-overlay.zip
```

It adds/replaces only the included paths and does not delete local-only files.
The separate all-in-one ZIP contains `c64-3d-toolkit-v0.6.7-rc3/` for a fresh
extraction. Both exclude build outputs, caches, logs and the previously deleted
hash-named cartridge. Existing historical assets in the supplied baseline are
preserved; the overlay does not recopy unchanged archive files.
