# 0.7.6: Sande demo and performance test kit

This release adds models contributed by **Sande** in the separate
[`examples/demos_sande`](../examples/demos_sande/README.md) collection:
Sande's Pretzel and Sande's TAC-2 joystick. It is based on the 0.7.5 workdir.

Both renamed OBJ/MTL pairs, pinned build recipes, automatic playback carts
and separate interactive carts are included. These defaults start white on black.
Two additional automatic `-color` carts use the supplied MTL materials:
grey for Pretzel; red, white and greys for TAC-2. Both use HORS-V2.
The main CLI's `--interactive-cart` flag enables cursor/joystick rotation
direction and F-key palette controls for standalone v2 spin CRTs.
It rejects incompatible renderers and non-CRT outputs before compilation.
Interactive carts show `INTERACTIVE` at the top right using the HUD font.
F4 changes background with a following border by default; F3 changes only the foreground.
F5 toggles alternating sequential palette cycling, F6/F7 adjust its rate,
and F8 locks/unlocks a persistent black border. Ctrl+F7 cycles a custom border. F2 briefly flashes white
and then restores colours, default speed and border-follow mode, with cycling off.

The [performance page](PERFORMANCE_COMPARISON.md#sandes-models) includes a
separate Sande workload across historical renderer methods, standalone
v1/v2 FPS/RAM measurements in bw and material colours, plus the idle cost
of the bw interactive path.
Capacity failures are reported with complete sources, without lowering
detail or dropping orientations. Sande's registry is extensible.

## Measured performance and validation

Standalone PAL VICE display rates, with the pinned 192-sample Y rotation:

| Model | HORS-V2 bw average FPS | HORS-V2 material-colour average FPS |
| --- | ---: | ---: |
| Sande's Pretzel | 18.00 | 18.00 |
| Sande's TAC-2 | 24.60 | 18.53 |

Pretzel uses a single grey foreground. TAC-2's per-cell material colours
add runtime work. The separate interactive measurements include input
polling and repainting the top-right label.
| Model | Interactive idle FPS | Default cycling FPS | Fastest cycling FPS |
| --- | ---: | ---: | ---: |
| Sande's Pretzel | 17.50 | 17.14 | 13.26 |
| Sande's TAC-2 | 23.73 | 23.30 | 16.60 |

Default cycling costs about 2% versus interactive idle; the fastest setting
costs about 24–30%. These rows include the top-right label and normal input
polling. Palette updates do not modify the precomputed geometry.

High/low interval rates, v1/v2 FPS/RAM variants and all 19 historical
method/preference combinations per model are on the
[performance page](PERFORMANCE_COMPARISON.md#sandes-models). Thirteen of
the 38 historical bw model/method cases exceed an older renderer's capacity;
their exact failure reasons are retained as N/A. The other 25 passed.
The colour matrix also has 25 passing and 13 capacity-limited cases:
76 cases in total across both modes, with 50 passing and 26 recorded N/A.
The screenshot's rounded Pretzel HUD reading is a separate observation,
not the average of this reproducible test.

The unit suite completed 216 tests (three skipped) with no failures.
The current release evidence covers 10,751 completed-picture checks across
25 named v2 carts and separate Color Combo Test validation. The two added
material-colour carts account for 774 of those checks and also passed source-
palette verification. The current index contains 26 cartridges.
The original automatic bw carts retain their exact bytes; interactive carts
are rebuilt for the new label and complete palette controls.
Interactive tests checked 450
produced pictures per Sande model, including both loop boundaries and
repeated direction changes, plus palette cycling, debounce, both Shift
keys and both joystick paths. Each model also passed 193 input-state checks
and 180 timed palette events across slow, default, fast, black-border and
custom-border modes, plus 500 stopped-frame checks. These input tests inject values at the CIA
read points; physical joysticks and host keyboard mapping were not tested.
The alternate-version test, native endings, menu states, HiFi transitions
and both existing demo carts' colour controls also passed.
The full original comparison passed all 26 jobs and 22,901 completed-picture
checks. Its regenerated page passes the current-source freshness gate.

Evidence: [Sande timing](benchmarks/sande/summary.json),
[historical methods](benchmarks/sande/methods.json),
[interactive checks](benchmarks/sande/controls.json),
[material colours](benchmarks/sande/colors.json),
[colour timing](benchmarks/sande/summary-color.json),
[historical colour methods](benchmarks/sande/methods-color.json),
[release picture checks](benchmarks/release-0.7.6/examples.json) and
[alternate-version checks](benchmarks/release-0.7.6/version.json).
Timings measure the emulated PAL C64; no physical C64 or NTSC claim is made.

## Install

The download contains a top-level `c64-3d-toolkit/` directory. Extract it
from the parent of the existing checkout:

```bash
unzip -o c64-3d-toolkit-v0.7.6.zip
cd c64-3d-toolkit
python c643d.py --version
```

The archive contains no Git metadata or local configuration. Review changes
in your existing checkout before committing. Older versioned carts remain
historical files; current links and the release index select 0.7.6 builds.

## Rebuild

```bash
python tools/build_current_examples.py
python tools/build_demo_cart_v2.py
python c643d.py color-combo-test --overwrite-policy allow
python tools/index_release_examples.py
bash RUN-CHECKS.sh ../c64-076-checks
```

For the complete isolated release compiler:

```bash
JOBS=3 bash COMPILE-RELEASE.sh --workspace ../c64-076-release-build
```

For Sande's models and a shareable log ZIP only:

```bash
bash RUN-SANDE-CHECKS.sh ../c64-sande-checks
```

To rebuild just the added colour carts:

```bash
python tools/build_sande_examples.py --source-colors
```

The standard EasyFlash metadata, real EasyAPI, protected VICE launching and
explicit legacy compatibility option from 0.7.5 remain available. See
[cartridge loading](CARTRIDGE_LOADING.md).
