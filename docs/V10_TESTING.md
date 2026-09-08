# hors-render-v1 builds and Blender targets

hors-render-v1 is a production build target based on the V9 drawing engine and the tested byte-first policy. It is the 0.7.0 CLI default. Historical assembly, encoder and cartridge files remain unchanged. Capacity failures stop the build; samples are never silently removed. This is not yet `hors-optimizer-v1` automatic selection.

## Ready-to-run cartridges

- [Menu FPS](../examples/cart_demos/c643d-demo-v0.7.0-hors-render-v1-all.crt)
- [Menu RAM](../examples/cart_demos/c643d-demo-v0.7.0-hors-render-v1-all-ram.crt)
- [Marbles clean, original export pacing](../examples/cart_marbles/history/dont_lose_your_marbles-hors-render-v1-scene-clean.crt)
- [Marbles HUD, original export pacing](../examples/cart_marbles/history/dont_lose_your_marbles-hors-render-v1-scene.crt)
- [Horse and Sunflower](../examples/cart_horse_and_sunflower/horse_and_sunflower-hors-render-v1-scene.crt)

RAM variants of the scenes append `-ram` before `.crt`. Optional max-speed diagnostics go to ignored `comparison-tests/v10-max-diagnostic/`; they are not release examples or denser exports.

Rebuild shipped examples:

```bash
python tools/build_hors_examples.py
python tools/build_hors_examples.py --prefer ram
python perf/build_v10_max.py
python perf/verify_hors_release.py --vice-data /path/to/vice-data
```

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

[The generated chart](PERFORMANCE_COMPARISON.md) measures real menu display flips with the common PLAY ALL controller. The scene profiler reports stage intervals and includes the final hold; those numbers are not the same metric. [Findings](OPTIMIZATION_FINDINGS.md) distinguish authored-pacing tests, max-speed tests and the pending fresh Blender exports. No music coexistence or real-hardware claim is made.

The previous policy experiments remain available via `perf/byte_candidates.py`, `perf/marbles_candidates.py` and their watchers. `perf/v10_test.py` remains an alias for the historical byte-policy sweep, not the production cartridge builder.

## Compatibility names

The canonical public names are `hors-render-v1` and `hors-render-v1-scene`. `yunroll-cart-v10` and `yunroll-cart-v10-scene` remain accepted CLI aliases. Existing V10 assembler filenames and manifest implementation identifiers remain stable for compatibility; these do not denote a different algorithm. Older released methods retain their names and behavior.

## Fractional export times

`--blender-output-fps` now uses nearest integer source frames (half ties round upward), never fractional geometry evaluation. It warns on the console and in the test log with counts of rounded/clamped and repeated samples. Repeats are retained when upsampling so duration does not shrink. For 25-to-20 FPS conversion this selects 800 samples from the 1,000 source frames. No geometry blending or near-plane error suppression is performed. The original sample-step path is unchanged when the option is omitted.
