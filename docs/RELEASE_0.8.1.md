# v0.8.1: Camera crossings, Blender colours and Demo Cart v3.1

Authored scenes can now cross the camera near plane without aborting conversion.
Visible edge segments and occluding surfaces are clipped, invisible samples stay
in the animation, and objects can reappear without losing timeline frames.

Blender material interpretation is selectable with `--blender-color-space
linear|srgb`. `linear` remains the default; use `srgb` for imports whose material
numbers already represent sRGB. Save the default directly with
`--configure-blender-color-space srgb`, or omit the value for the chooser.
The shared palette, perceptual matching and explicit C64 indices are unchanged.

This release also includes Demo Cart v3.1 interactive fixes, full dependency
setup and repair, grouped versioned CLI help, and numbered checkpoint archives.
Default conversion remains automatic HORS-V4/GMod3 playback. Existing cartridge
binaries are preserved.

## Camera, colour and configuration validation

- 321 Python tests completed: 318 passed, three optional historical tests skipped.
- The original camera-crossing road retains all 17 frames, including nine
  consecutive invisible samples. GMod3, EasyFlash and resident PRG output each
  pass 54 native bitmap/colour checks across all three buffers.
- A 300-refresh PAL display check verifies every road sample in order with the
  intended two-refresh holds. The measured complete loop is about 0.6783 seconds.
- Four existing scenes retain identical sampled frame records in monochrome
  and colour. Blender 4.0.2 retains all 96 calibration material indices in the
  default linear mode and passes reflected/scaled/shifted camera checks.
- All 71 original CRTs and all C64 assembly sources match the supplied baseline.
- One clipping summary replaces repeated diagnostics; `--ignore-warnings`
  suppresses toolkit scene/export warnings. Scene exports honour `--output-dir`.

[Camera-crossing example and evidence](../examples/camera_crossing/README.md) ·
[Colour-space FAQ](BLENDER_FAQ.md#why-can-red-become-orange) ·
[Complete recovery verification](RECOVERY_CHECKPOINT.md).

The checks below describe the existing interactive hotfix evidence. That
record was checked again against the unchanged cartridges; its entire native
performance/keymap suite was not rerun during the camera/colour update.

## Interactive collection

The [shared SAKU baseline](INTERACTIVE_CART_BASELINE.md) composes the existing
HUD, speed, effects, help and exhibition implementations. The two help pages
now expose all controls, with HUD/star controls on the first page. Main-menu
Shift+H works; closing help returns to the same selection. SPACE **or Enter**
starts that selection. RUN/STOP (Esc in VICE) or F1 returns to the menu from
playback, help, exhibition and slow playback, including held speed keys.
Stars start off and remain off after reset. SAKU's explicit gradient-with-stars
shortcut still enables them when requested.

Input return receives priority before speed-key polling. A raster IRQ latch
catches STOP across delayed playback while the foreground performs the actual
menu reload. The key must be observed during an input/IRQ sample; the native
keyboard tests include a roughly 50 ms press/release during slow playback.

[Download v3.1](../examples/gmod3_cart_demos/demo-cart-v3.1-gmod3-all-in-one.crt) ·
[All commands and original v3.0 images](../examples/gmod3_cart_demos/README.md).
The automatic benchmark image is unchanged. Its menu has SPACE launch and
no interactive help/Enter binding; all five menu pages and 65 selections were
verified through both native VICE keymaps.

## Performance and correctness

The [58-entry matched A/B](INTERACTIVE_BASELINE_PERFORMANCE.md) reruns the old
and new interactive CRTs with identical pictures, PAL VICE 3.10 settings,
seed, speed and HUD, with stars/exhibition off. It measures actual displayed
frame transitions over 2,400 PAL refreshes per entry after warm-up.
Median average-FPS reduction is 0.240%; the largest relative reduction is
0.393%, and the largest absolute reduction is 0.1462 FPS. Three entries tie.
Maximum mean active render-cycle increase is 0.366%. High/average/low FPS are
listed; only the winning averages are bold. This is a small measured input
service cost, not a claim of zero regression or extra FPS.

- All 58 rebuilt runtimes pass complete picture/colour loops across three buffers.
- 1,842 state checks and 5,992 native VICE key events cover symbolic and
  positional layouts, help, HUD removal/restoration, stars, speed, exhibition
  and menu return. Host desktop GUI event injection was not tested.
- The independent SAKU picture, colour, HUD/speed, light/full-star and exhibition
  checks pass on the final CRT. Marbles passes all five pages, reverse and wrap.
- The earlier interactive checkpoint ran 291 Python tests: 288 passed, three
  optional checks skipped; the final source suite has 321 tests as listed above.
- Linux setup was executed through a separate environment with the full
  packages already available; pip and a fresh import check succeeded. Missing,
  outdated and broken-native-library cases are covered separately. Windows
  installer changes were reviewed but not executed on Windows in this environment.
- Blender 4.0.2 creates and exports the 96-material calibration card: all
  exported face indices agree with recorded material results.

[Release audit](benchmarks/release-0.8.1/release-audit.json) ·
[Keyboard checks](benchmarks/release-0.8.1/keyboard/results.json) ·
[Picture loops](benchmarks/release-0.8.1/collection/results.json) ·
[Effects and SAKU](benchmarks/release-0.8.1/features/results.json) ·
[Paging](benchmarks/release-0.8.1/paging/results.json) ·
[Benchmark menu](benchmarks/release-0.8.1/benchmark-menu/results.json).
Physical C64/GMod3 hardware and NTSC were not tested.

## Installation, help and colour diagnostics

[Windows/Linux installation](INSTALLATION.md) uses the complete Python build
requirements by default: NumPy, Pillow, CairoSVG and defusedxml, with transitive
packages installed by pip. Native Cairo is checked as well. Missing or
unloadable libraries produce a concise error with an installer command for
the exact interpreter, plus individual pip instructions. `setup-python.py
--repair` reinstalls packages; `setup-linux.sh` creates/reuses a local venv.

Top-level `--help` now lists every build option and correct HORS-V4/GMod3
and non-interactive defaults. `--help-all` includes other commands. All help
works without Python build dependencies. [CLI guide](CLI.md).

The [editable Blender colour card](../examples/blender_color_calibration/README.md)
compares toolkit, Pepto PAL and Colodore values and explicit C64 indices.
It identifies cross-palette mismatches without changing the global mapper.
The recovery update makes material-number interpretation explicit: `linear`
remains the default; `srgb` handles imports already storing sRGB values.
`#98352D` directly maps to red, while interpreting those numbers as linear
converts them to `#CB7E75`, mapping to orange. The palette and matcher remain
unchanged. Use `--configure-blender-color-space srgb` to save a default, or
omit the value for the chooser.

Authored camera crossings now clip edges and occluding surfaces. Entirely
invisible samples remain in order, and `--ignore-warnings` suppresses the single
clipping summary. See [camera-crossing diagnostics](../examples/camera_crossing/README.md),
[recovery verification](RECOVERY_CHECKPOINT.md) and [checkpointing](CHECKPOINTING.md).

## Monitor log maintenance

CLI startup copies a stale root `monitor.log` into `logs/` under a unique UTC
filename, verifies the copy, then removes the original. VICE launchers select
monitor filenames before enabling logging, preventing accidental root output.
The external publisher also archives and untracks generated monitor logs from
older checkouts. See [maintenance](MAINTENANCE.md).

## Install and reproduce

The release source ZIP extracts under `c64-3d-toolkit/`. For an existing checkout,
apply the cumulative release-preparation ZIP from the parent directory:

```sh
unzip -o c64-3d-toolkit-v0.8.1-release-prep-cp007-incremental.zip
cd c64-3d-toolkit
python3 -m unittest discover -s tests
python3 tools/verify_gmod3_release.py
```

Fresh installations can use `bash setup-linux.sh` or `setup-windows.cmd`.
See [installation and repair](INSTALLATION.md) for toolchain requirements.
The [camera diagnostic](../examples/camera_crossing/README.md#reproduce) includes
native rebuild/verification commands; interactive hotfix reproduction details
remain in [the collection guide](../examples/gmod3_cart_demos/README.md).

## Publish from your checkout

The publisher is delivered beside `c64-3d-toolkit/`, outside the repository.
From the checkout, run:

```sh
bash ../RELEASE-v0.8.1-cp007.sh .
```

It first moves any obsolete checkpoint-005 publisher out of the checkout,
preserving its local and staged contents in the external release directory,
and removes that publisher from Git's index. It also runs repository maintenance
to archive and untrack generated `monitor.log` files, including old benchmark logs. The publisher is excluded from
the reviewed source inventory, source packages and published release assets.

The script requires `main`, verifies VERSION, GitHub authentication, origin/main
ancestry and tag/release availability, runs the unit suite and saved release
audit, then stages the reviewed source paths in `docs/RELEASE_0.8.1_FILES.txt`.
It checks for staged files outside that list. Unlisted files are never staged.
Known source/media files are staged by exact filename, including the reviewed
showreel covered by the broad video ignore rule. Untracked diagnostic logs and
generated intermediates are excluded. Unknown tracked or staged files cause a
clear stop for review, and missing required release files stop publication.

It commits the changes, creates the annotated `v0.8.1` tag, creates the source
ZIP from that exact tag, writes its SHA-256 file, pushes `main` and the tag
atomically, then creates the GitHub release with the source ZIP, checksum and
Demo Cart v3.1 CRT attached. The GitHub body is
[the dedicated release announcement](RELEASE_0.8.1_GITHUB.md).

The script refuses an existing tag or release and uses no force push or tag
replacement. If interrupted after a push, inspect the remote state before
retrying; it intentionally does not replace an existing release.
