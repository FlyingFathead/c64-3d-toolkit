> Archived beta1 documentation and measurements. **hors-render-v2 is the stable 0.7.2 default**; see [current integration](HORS_RENDER_V2.md) and [stable results](HORS_RENDER_V2_RESULTS.md). Older release ZIPs preserve the tools used for this beta evidence.

> Historical version documentation. Current builds and prebuilt examples use [hors-render-v2](HORS_RENDER_V2.md); see [0.7.2 release instructions](RELEASE_0.7.2.md). Older preview binaries are in prior release ZIPs or the external local archive.

# hors-render-v2 beta 1 — measured results

Measured 10 September 2026 on PAL VICE 3.10, seed 1, sound disabled, 985,248 emulated cycles/s; 64tass 1.59.3120. Host wall time and the HUD counter are not used.

The menu and Ripples runs below were repeated successfully after the toolkit
version bump to 0.7.2. Earlier standalone cube/torus diagnostic values are
retained separately with their original evidence.

## Canonical 0.7.2 comparison: preserved 12-animation dataset

The complete uncapped matrix passed all **26 jobs**: 19 menu method/preference
combinations plus seven historical authored-scene jobs. Bitmap and colour
verification covered **22,901 completed pictures**. Every earlier method remains
in `docs/PERFORMANCE_COMPARISON.md`; its source-provenance check passes.

| Original animation | v1 FPS | v2 beta FPS | Display-count gain |
| --- | ---: | ---: | ---: |
| TORUS | 16.07 | 17.68 | +10.00% |
| TORUS DENSE | 15.77 | 17.18 | +8.92% |
| CUBE | 27.42 | 30.03 | +9.52% |
| SPHERE | 15.87 | 17.38 | +9.49% |
| HORSE HEAD | 27.42 | 29.34 | +6.96% |
| SUNFLOWER TORUS | 27.12 | 28.73 | +5.93% |
| SUNFLOWER COLOR | 19.99 | 20.89 | +4.52% |
| SPACE HORSE SPIN | 17.58 | 19.08 | +8.57% |
| SPACE HORSE CRAWL | 35.56 | 38.27 | +7.63% |
| FALLING CUBES | 19.69 | 20.89 | +6.12% |
| HORSE HEAD HIFI | 20.69 | 21.50 | +3.88% |
| SUNFLOWER TORUS HIFI | 19.89 | 20.39 | +2.53% |

Both sides use the frozen released vector reference, matching colours, HUD,
samples and the same normal PLAY ALL wrapper. The canonical beta uses gap 3 /
batch 2048 so all 12 entries fit the existing cartridge layout; encoded literal
payload sizes match v1. This is a different packing policy from the seven-entry
showcase below. V2 beats v1 on these 12 inputs; the resident `yunroll` and cart
scaffold still win CUBE overall at 30.27 FPS. Earlier rows and authored-scene
results are retained, including methods that are slower or unsupported.

The authored intro/ending diagnostic remains V4–V10; beta1 does not claim support
for that path. The performance gate has passed for this source snapshot. This
is still a beta awaiting independent user tests and visual-output review.

## New Demo Cart 2.0: normal PLAY ALL

These are seven newly assembled menu entries, not the frozen 12-animation release matrix. Each result counts actual display flips over three normal PLAY ALL visits with the unchanged ten-second setting (499 PAL refresh intervals per visit). The first visible picture is outside each observation window. F5 was not used.

| New menu scene | Samples | v1 display FPS | v2 beta display FPS | Display-count gain | v2 worst interval ms |
| --- | ---: | ---: | ---: | ---: | ---: |
| COLOUR CUBE 24 | 24 | 32.45 | 35.56 | +9.60% | 42.79 |
| COLOUR TORUS 18 | 18 | 18.38 | 19.99 | +8.74% | 62.59 |
| TWIST TUNNEL | 48 | 9.14 | 9.94 | +8.79% | 119.70 |
| RIBBON DANCE | 48 | 31.64 | 33.45 | +5.71% | 44.42 |
| ORBITAL CUBES | 48 | 28.73 | 31.45 | +9.44% | 44.09 |
| WAVE LATTICE | 48 | 22.00 | 24.81 | +12.79% | 63.07 |
| RIPPLES LITE | 100 | 12.46 | 16.88 | +35.48% | 79.80 |

**COLOUR CUBE 24 is a new rotating coloured-face cube. It is neither the released CUBE (36 samples) nor FALLING CUBES (18 samples).** COLOUR TORUS 18 is also a new fixture. These are separate results from the canonical `PERFORMANCE_COMPARISON.md`.

All source sample counts, geometry, colours and sample order match between the A/B menu builds. Both use the same caption/HUD and one-refresh minimum hold. V2 uses gap 6 / batch 2048 for the first six scenes, and the measured gap 10 / batch 2048 choice for Ripples Lite. Higher throughput changes loop speed. No fixed cadence or universal FPS guarantee is claimed.

The JSON reports also retain interval high/low FPS and p95, raw display intervals, completed-render costs, per-visit display counts, oracle hashes and cartridge hashes. A brief queued-frame burst can yield interval high FPS above the PAL refresh rate; that is not sustained throughput.

## Cartridge and memory trade-off

| Build | CRT file bytes | Frame payload bytes | Used 8 KiB frame slots | Runtime PRG sizes |
| --- | ---: | ---: | ---: | --- |
| hors-v1 | 705,952 | 445,502 | 61 | 21777 |
| hors-v2-beta1 | 771,616 | 496,854 | 69 | 21777 |

The seven-entry layout provides 103 frame-data slots (843,776 bytes), after fixed runtime/menu reservations. The selected beta uses 69 of them, leaving **34 whole frame-data slots (278,528 bytes)** plus unused space inside occupied slots. This cart fits EasyFlash; GMod3 is not required for this preview.

Both streamed implementations retain three 8,000-byte bitmap buffers, three 1,000-byte screens, three 1,024-byte metadata caches and an 8,192-byte staging reservation. V2 reuses a vector-only 256-byte dispatch page; its added helper code/state occupies 26 bytes. It does not allocate another RAM buffer. PRG lengths contain address gaps and are not total used RAM. These allocation components must not be summed with PRG size as disjoint memory.

## Multi-pass Ripples Lite search

Independent standalone diagnostic: full 320-by-192 source, all 100 samples, monochrome, no HUD, one-refresh minimum hold. The measurement window expands to at least two complete source loops. This is a separate measurement protocol from the menu table above.

| Candidate | Display FPS | Worst display ms | Frame payload bytes | Passed |
| --- | ---: | ---: | ---: | --- |
| hors-render-v2-beta1-fps-optimized-t1-g10-b2048 | 16.792 | 79.804 | 214,548 | passed |
| hors-render-v2-beta1-fps-optimized-t1-g10-b1024 | 16.625 | 79.806 | 214,548 | passed |
| hors-render-v2-beta1-fps-optimized-t1-g6-b2048 | 15.713 | 79.806 | 176,592 | passed |
| hors-render-v2-beta1-fps-optimized-t1-g6-b1024 | 15.305 | 79.806 | 176,592 | passed |
| hors-render-v2-beta1-fps-optimized-t1-g3-b2048 | 13.885 | 79.807 | 167,420 | passed |
| hors-render-v2-beta1-fps-optimized-t1-g3-b1024 | 13.474 | 79.807 | 167,420 | passed |
| hors-render-v1-scene-fps-optimized-t1 | 12.392 | 99.756 | 167,420 | passed |

The wider runs win here despite writing more literal bytes, because they reduce per-run overhead. This is why a measured search is useful: smallest ROM and highest throughput are different objectives. The selected policy stores the source hash and is subsequently checked in the real menu cart. Other inputs may prefer other settings.

## Earlier standalone beta fixtures

| New fixture | v1 display FPS | v2 beta display FPS | Protocol |
| --- | ---: | ---: | --- |
| Colour cube, 24 samples | 32.52 | 35.72 | Standalone, same minimum hold, no HUD |
| Colour torus, 18 samples | 18.41 | 20.11 | Standalone, same minimum hold, no HUD |

These earlier values explain the initial progress update. They are not substituted into the menu results or the canonical release chart.

## Validation and limits

- Menu A/B: **1,378 completed pictures** checked against identical oracles across all three buffers; bitmap and all 960 screen-colour cells matched.
- Menu UI: 51 states across default, decorative and demoscene styles, including up/down wraparound, PLAY ALL selection, marker colours and stable header/footer.
- Standalone matrices: 16 cube, 8 torus, 2 repeated-hold and 7 Ripples Lite candidates passed. Each includes completed-picture and displayed-picture verification.
- Boundary test: 264 samples including a blank picture, frame-directory paging beyond 255, all-ROMH payloads, and 531 verified completed pictures; oversized payload rejection passed.
- Standard beta build CLI verified 51 pictures. The unchanged v1 standalone cube build was byte-identical to the same build from the original snapshot (SHA-256 `d36d1f568ec970e1a231170e113d59466491b231a20c51ba70ea5e1b78ce6549`).
- The batch budget is an estimate used for planning, not a hard measured interrupt-latency guarantee. No physical C64, NTSC, SID soundtrack or private production integration is claimed.
- Liquid Floor and Cross Swell are optional approved source alternatives, not measured rows in the default menu comparison. The Cross Swell bug report was withdrawn by the user.
- The complete canonical 0.7.2 matrix and provenance gate passed. The unit suite ran 180 tests, with three optional external historical-archive checks skipped and no failures. Rerun after changes to fingerprinted inputs. No public release, tag or push was performed.
- Adoption also requires clean video in the user's interactive run. Oracle equality does not establish absence of every scanline/transition artifact.

Raw evidence is under `docs/benchmarks/hors-v2-beta1/`. Configuration files retain original run paths for provenance; use the relative commands below to reproduce on another machine.

## One-command local check

From the toolkit root, with up to three VICE workers:

```bash
python tools/run_hors_v2_perfs.py \
  --workspace ../hors-v2-local-perfs --jobs 3 \
  --tass 64tass --cartconv cartconv --vice x64sc \
  --vice-data /usr/local/share/vice
```

Add `--extended-search` to test all four minimum holds and both optimized/raw plans (56 scene candidates). The workspace must be new. The command builds into that workspace, checks both menu carts, runs the scene search, prints/saves `COMPARISON.md`, and writes logs, JSON and SHA256SUMS together. Matching compiler symbols are also retained in the toolkit's ignored `build/` directory.
