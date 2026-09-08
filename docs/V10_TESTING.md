# hors-render-v1 builds and Blender targets

The v0.7.1 menu cartridges are rebuilt for this release, alongside the new
[HiFi exhibition reel](../examples/cart_hifi/README.md). Standalone object and
authored-scene cartridges are retained byte-for-byte from v0.7.0; their embedded
version labels and manifests remain their original build provenance.

hors-render-v1 is a production build target based on the V9 drawing engine and the tested byte-first policy. It is the 0.7.1 CLI default. Historical assembly, encoder and cartridge files remain unchanged. Capacity failures stop the build; samples are never silently removed. This is not yet `hors-optimizer-v1` automatic selection.

## Ready-to-run cartridges

- [Menu FPS](../examples/cart_demos/c643d-demo-v0.7.1-hors-render-v1-all.crt)
- [Menu RAM](../examples/cart_demos/c643d-demo-v0.7.1-hors-render-v1-all-ram.crt)
- [Accepted 640-sample Marbles](../examples/cart_marbles/marbles-hors-render-v1-16fps-force-bytes.crt)
- [Horse and Sunflower FPS](../examples/cart_horse_and_sunflower/horse_and_sunflower-hors-render-v1-scene.crt)
- [Horse and Sunflower RAM](../examples/cart_horse_and_sunflower/horse_and_sunflower-hors-render-v1-scene-ram.crt)
- [Standalone HiFi horse, 192 orientations](../examples/hifi_showcase/horse_head_hifi-hors-render-v1.crt)

See the [complete inventory](V10_CARTRIDGES.md). Marbles has no validated HUD or
RAM counterpart for its accepted 640-sample presentation. Its startup waits for
SPACE, followed by the native intro, scene and ending.

## Build current menu and standalone examples

From the repository root, with 64tass and cartconv available:

```bash
./build.sh cart-demos
./build.sh cart-demos --prefer ram
python tools/build_current_examples.py
```

The standalone builder uses bundled models and frozen falling-cubes vectors;
it does not require Blender or the external history archive. The menu builder
uses the current named-demo registry; the performance comparison deliberately
uses frozen matched inputs. Rebuilt outputs should be verified before replacing
release assets. For a fresh Horse/Sunflower export, use the
[scene command](CARTRIDGE_SCENES.md#current-scene-path-in-071).

## Accepted Marbles reproduction boundary

The shipped cart is the accepted 16 FPS force-bytes candidate from the local
recovery workflow: 640 samples, about 41.82 seconds of measured scene playback.
Keep its supplied CRT, labels and manifest together. A generic
`--blender-output-fps 16` build is not a byte-exact rebuild recipe: recovery
used an existing 1,000-sample compiled checkpoint and experimental whole-frame
packing. Those ignored local run artifacts are not bundled in a fresh clone.
See [recovery prerequisites and results](MARBLES_RECOVERY.md).

`tools/build_hors_examples.py` is a **historical preserved-sample builder**. It
requires archived V4 Marbles and V7 Horse/Sunflower references from the optional
`../c64-3d-toolkit-history/` tree and generates the old 200-sample Marbles
variants. It is not the command to recreate the accepted 640-sample cart.
`perf/build_v10_max.py` likewise builds historical max-speed diagnostics, not
release presentations. These remain available for deliberate reproduction.

## Verify the supplied release inputs

```bash
python tools/compare_renderers.py --check
python -m unittest discover -s tests
python perf/verify_hors_release.py --vice-data /path/to/vice-data
```

The last command runs VICE pixel/profile/ending and menu-control checks and
writes reports under `logs/hors-release/`; it needs a working emulator and ROM
data. Automated scene verifiers acknowledge the SPACE startup screen. This
documentation update does not claim a new emulator run. `--check` validates the
saved chart's fingerprint; it does not benchmark or regenerate the chart.

## Fresh Blender export at 25 or 20 FPS

```bash
python perf/blender_targets.py --id marbles-blender-01 --fps 25 20 --vice-data /path/to/vice-data
```

This runner creates separate fresh candidates, captures build diagnostics, verifies successful builds, measures their stages and bundles the results under `logs/`. A capacity failure is recorded as failed, never ranked as a passing result. It does not touch existing examples. Blender must be installed on the executing machine.

Equivalent direct build for 25 FPS:

```bash
python c643d.py build --no-config --renderer hors-render-v1-scene   --blend examples/blender_marbles/dont_lose_your_marbles.blend   --blender-output-fps 25 --intro --ending --no-text-overlay   --output marbles-v10-blender-25fps --output-dir comparison-tests/marbles-25fps
```

`--blender-output-fps` is opt-in, V10-only and requires baked animation with `--sample-step 1`. It samples source time at the requested rate without editing the blend or retiming the animation. For Marbles the Blender source is 1,000 frames at 25 FPS: a 40-second source interval, giving 1,000 samples at 25 FPS or 800 at 20 FPS. The old 200-sample cartridge's 28-second target was its playback pacing, not the Blender source duration.

25 FPS uses two PAL refreshes per sample. 20 FPS alternates two and three refreshes. Actual throughput may be lower when drawing misses those intervals. The fractional profile's scalar budget counter currently uses the shorter interval; use stage costs and measured intervals instead of interpreting that counter as exact deadline misses.

Do not combine this option with a non-default sample step. The output-FPS option sets cartridge pacing; use it instead of manually setting frame ticks. Omit it to retain the existing export mechanics. All prior methods reject the option.

## Measurement interpretation

[The generated chart](PERFORMANCE_COMPARISON.md) measures real menu display flips with the common PLAY ALL controller. The scene profiler reports stage intervals and includes the final hold; those numbers are not the same metric. [Findings](OPTIMIZATION_FINDINGS.md) distinguish authored-pacing tests, max-speed tests and the dense Blender export/recovery results. No music coexistence or real-hardware claim is made.

The previous policy experiments remain available via `perf/byte_candidates.py`, `perf/marbles_candidates.py` and their watchers. `perf/v10_test.py` remains an alias for the historical byte-policy sweep, not the production cartridge builder.

## Compatibility names

The canonical public names are `hors-render-v1` and `hors-render-v1-scene`. `yunroll-cart-v10` and `yunroll-cart-v10-scene` remain accepted CLI aliases. Existing V10 assembler filenames and manifest implementation identifiers remain stable for compatibility; these do not denote a different algorithm. Older released methods retain their names and behavior.

## Fractional export times

`--blender-output-fps` now uses nearest integer source frames (half ties round upward), never fractional geometry evaluation. It warns on the console and in the test log with counts of rounded/clamped and repeated samples. Repeats are retained when upsampling so duration does not shrink. For 25-to-20 FPS conversion this selects 800 samples from the 1,000 source frames. No geometry blending or near-plane error suppression is performed. The original sample-step path is unchanged when the option is omitted.

## v0.7.1 presentation validation

Build the independent reel with `python tools/build_hifi_cart.py`. It uses bundled
scene/menu vector references and needs no Blender installation or external archive.
See [cart_hifi](../examples/cart_hifi/README.md) for playback and verification.

The [release validation report](benchmarks/release-071/cartridge-validation.json)
records PAL VICE execution of both menu variants and the separate reel, including
normal PLAY ALL, F5, presentation transitions, looping, and pixel/color comparison
of all 84 scene samples and both 128-orientation spinners. Exhibition timings are
separate from the matched-method renderer comparison.
