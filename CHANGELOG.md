# Changelog

## 0.6.0

- Fixed static Blender rigid-body exports: stateful scenes are now evaluated through every intervening source frame while `--sample-step` controls only which frames enter the C64 tables. Added an explicit warning when all captured frames are geometrically identical.
- Fixed Blender 4.x scene export by calling `calc_matrix_camera()` on the evaluated camera object instead of its data block. Blender exporter tracebacks now also produce a nonzero process exit code and a truthful build failure.
- Added viewport clipping for authored Blender/interchange scene edges, allowing normal camera compositions with partially offscreen geometry while retaining the classic auto-fit guard for legacy OBJ/SVG/procedural builds.
- Restored Blender preflight to its proper scope: start Blender headlessly, import its bundled `bpy`, and report the version. Removed unreliable `bpy.types.Object` method introspection that produced false failures on Blender 4.0.2; the real scene exporter remains the capability test and reports API failures with a nonzero exit code and traceback. Documented current Blender 5.2 LTS as recommended, with Ubuntu 24.04's Blender 4.0.2 package retained as a supported older fallback and an explicit warning about newer `.blend` files not being backward-compatible.
- Added optional animated Blender scene compilation with `--blend`, frame-range sampling, active Blender camera projection, multiple evaluated mesh objects, stable-topology deformation/rigid-body support, and Blender material colours.
- Added a versioned Blender-neutral `.c643dscene` interchange and direct `--scene` compilation path. Blender runs `tools/blender_export.py` with its own bundled Python; the ordinary toolkit remains dependency-free and never imports `bpy`.
- Added executable discovery plus a real headless `import bpy` preflight. Missing/broken Blender stops only the `--blend` path and prints platform-specific installation instructions, including `sudo apt install blender` for Ubuntu/Debian.
- Blender animations use strict authored-frame semantics: table overflow fails with sampling/range/detail suggestions instead of silently reducing frame count.
- Added `examples/blender/falling_cubes_c64.py`, which generates a six-cube rigid-body demo `.blend` from the command line, plus Harry's deterministic 40-cube `falling_cubes_full.py` and Blender-4.00 `.blend` authoring/stress example.
- Preserved classic procedural/OBJ/SVG behavior and byte-identical generated output in legacy regression comparisons.

## 0.5.1

- Added `setup-windows.cmd` and `setup-windows.ps1` for assisted Windows 11 setup.
- Added WinGet-based detection and installation support for Python 3, Git, and VICE, including explicit keep, upgrade, and same-version reinstall choices for already installed packages.
- Kept 64tass installation deliberately manual on Windows. Setup can locate or accept an existing `64tass.exe`, validate it without executing it, compute SHA-256, and configure the `[windows] tass` path.
- Added common-location and optional whole-drive 64tass search. Whole-drive scans can be stopped with Q or Esc while preserving and presenting valid candidates already found.
- Added explicit confirmation for manually entered or directly pasted 64tass paths after non-executing validation and hash reporting.
- Added safe handling of existing `config/c643d.ini` Windows paths, preserving unrelated settings and requiring confirmation before path changes are written.
- Added `docs/WINDOWS_SETUP.md` with Windows bootstrap, recovery, path configuration, search options, and 64tass trust/provenance guidance.
- No C64 renderer or colour-pipeline changes from v0.5.0.

## 0.5.0

- Added host-side Wavefront MTL `Kd` parsing and per-face material propagation. Source RGB values are mapped to native VIC-II indices before table generation; the bundled sunflower maps to brown centre, yellow petals, and green stem/leaves.
- Upgraded SVG import from one dominant object colour to per-contour stroke/fill colour propagation, including inherited styles and opacity handling.
- Added per-frame hires screen-colour spans. When differently coloured wires occupy one VIC-II 8x8 cell, the host selects the dominant visible line colour for that cell.
- Recycled triple-buffer screen cells are restored before applying the next frame's colour spans, preventing material colours from trailing across frames.
- Single-colour OBJ/SVG sources reuse the original global hires foreground byte and allocate no colour table, avoiding needless runtime or frame-budget cost.
- Kept RGB/palette work off the C64: generated tables carry native 4-bit colour codes as ready-to-store screen-RAM bytes, so the 6510 performs no palette lookup.
- Added `--no-color`, `--no-colors`, and `--ignore-colors` aliases for classic white-on-black output. `--color NAME|0..15` remains a forced monochrome override.
- Builds now announce the selected color path before frame generation, including a named OBJ/MTL or SVG fallback notice when no usable source color layer exists.
- Kept the monochrome renderer path compile-time isolated. Colour code and calls are assembled out, monochrome clear/line tables retain their previous byte layout, and regression tests compare colour-bearing meshes with their colour metadata disabled.
- Coloured default output basenames now gain `_color`; bundled coloured example targets are `sunflower_torus_color.prg`, `space_horse_spin_color.prg`, and `space_horse_crawl_color.prg`.

## 0.4.2

- Clarified macOS VICE setup based on tester feedback: for downloaded VICE distributions moved into `/Applications`, documentation now points first to the actual package CLI, e.g. `/Applications/vice-arm64-gtk3-3.8/bin/x64sc`.
- Documented that the package directory varies by architecture, frontend and VICE version (ARM64/Intel, GTK3/SDL2, etc.), while distribution-directory and `.app` probing remain supported fallbacks.
- Updated macOS preflight hints and added a regression test ensuring a downloaded VICE distribution prefers `bin/x64sc` over a sibling launcher path.

## 0.4.1

- Added optional `config/c643d.ini` toolchain configuration with built-in fallbacks and per-platform `[linux]`, `[macos]`, and `[windows]` overrides.
- Added configurable 64tass/VICE executable names or full paths plus extra command-line arguments; CLI `--tass`/`--vice` overrides remain available and `--tass-arg`/`--vice-arg` were added.
- VICE now defaults to `+VICIIfull` for development runs so `--run` opens windowed rather than inheriting a saved fullscreen preference; this can be changed or cleared in config.
- Added cross-platform tool discovery fallbacks. On macOS, VICE distribution directories and `.app` bundles are understood and the resolver prefers the real CLI `x64sc` binary over launcher wrappers when possible.
- Added `config/c643d.ini.example`, `C643D_CONFIG`, `--config`/`--no-config`, one-shot default-argument suppression flags, expanded `doctor` reporting, and toolchain configuration regression tests.

## 0.4.0

- Added dependency-free SVG import with `import-svg` and one-off `--svg` builds. Common SVG paths/primitives are flattened to polylines and simplified into explicit wire edges, avoiding fake filled triangulation through glyph holes.
- Added optional shallow SVG wire extrusion via `--svg-depth` and sparse front/back connectors via `--svg-connector-stride`.
- Added SVG artwork colour inference and nearest C64 palette mapping; generated hires demos can now select a foreground colour with `--color`.
- Generalized the host frame transform beyond rotation: `spin`, front-facing `recede`, and tilted-plane `crawl` animation modes are now available.
- Added the bundled `space_horse.svg` demo asset plus spinner and horizon-crawl presets.
- Added SVG pipeline documentation and regression tests; the suite now covers SVG parsing, colour mapping, preset import, explicit wire edges, and crawl frame generation.

## 0.3.3-wip

- Restored the v0.3.1 `surface_features` semantics so ordinary back-facing manifold edges are culled before Z testing again; this removes the sunflower workload/FPS regression introduced in 0.3.2.
- Added `surface_creases` as the explicit crease-aware mode containing the heavier 0.3.2 behavior, while `horse_head` remains on full `surface` visibility.
- Fixed HUD source corruption from the 0.3.2 memory-map change: frame pointer tables now live at `$1600-$16ff` instead of `$1500-$16ff`, avoiding overlap with the tail of long generated HUD strings such as `SUNFLOWER TORUS ... E:142`.
- Strengthened assembler sanity checks so renderer + worst-case HUD growth is rejected before it can enter the pointer arena.
- Added regression coverage for the sunflower v0.3.1 workload, separated crease mode, and generated-memory-map overlap.

## 0.3.2-wip

- Fixed intermittent horse muzzle/snout line loss: the bundled horse now defaults to full `surface` Z-buffer visibility, so unreliable face normals on its open/non-manifold topology cannot pre-cull legitimate edges.
- Kept `surface_features` as an optional crease-aware mode with `--feature-angle`; boundary, non-manifold and sharp crease edges are preserved before Z testing.
- Added segmented generated-line packing: whole orientation blocks can spill into otherwise-unused RAM below bitmap #2, allowing the full 64-vertex horse to keep 36 sampled orientations in `surface` mode.
- Moved generated frame pointer tables to `$1500-$16ff`; this later proved unsafe for long generated HUD strings and was corrected in 0.3.3.
- Build diagnostics now print boundary/non-manifold topology counts when present.
- Added regression tests for horse full-surface visibility, crease edges, and segmented table packing.

## 0.3.1-wip

- Added bundled `sunflower_torus.obj` + `sunflower_torus.mtl` and a reusable object preset.
- Added `sunflower_torus.prg` to `--generate-examples`.
- Fixed intermittent OBJ edge self-occlusion: the host Z-buffer now records the winning face ID, so a wire edge is never hidden by one of its own adjacent faces.
- Edge depth is now interpolated at the same screen-space pixel centres used by the surface Z-buffer, reducing steep-line/self-depth drift.
- `horse_head` keeps `surface_features` visibility and now preserves the muzzle/snout outline more robustly through rotation.
- `import-obj` now preserves directly referenced Wavefront MTL files and rewrites flattened `mtllib` references when needed.
- Added/updated regression tests for the horse visibility preset, sunflower asset, examples manifest, and OBJ+MTL import.
- Reworded normal table-RAM auto-fit retries as informational notes: topology is preserved while sampled rotation orientations are reduced.

## 0.3.0-wip

- Added `generate-examples` plus the `--generate-examples` shortcut; reference PRGs are copied into `examples/`.
- Added an example manifest containing torus, dense torus, cube, sphere, and `horse_head`.
- Added `doctor` and early dependency preflight. Missing `64tass` is an error when assembly is requested; missing VICE is a warning for build-only and an error for `--run`.
- Added `--visibility auto|surface|frontface` and `--z-tolerance`.
- OBJ presets default to robust winding-independent `surface` Z-buffer visibility; procedural closed shapes retain the faster historical `frontface` mode under `auto`.
- Set `horse_head` to `surface` visibility with a slightly relaxed edge-depth tolerance to avoid intermittent snout/muzzle edges disappearing on the open/non-manifold reference mesh.
- Clarified that orientation auto-fit warnings preserve mesh topology and only reduce sampled rotation frames to fit C64 table RAM.
- Kept higher-density torus generation available through `--vertices`, `--polycount`, or explicit segment counts.

## 0.2.0-wip

- Bundled the canonical `objects/horse_head.obj` reference mesh (64 vertices / 124 edges / 65 faces).
- Added persistent object presets via `objects/<name>.json`.
- Added `import-obj` and `list-objects` CLI/build-script commands.
- Added `--object NAME` for compiling repository OBJ presets.
- Added OBJ topology diagnostics (face-size mix, boundary edges, non-manifold edges, isolated vertices).
- Added `--vertices N` as an approximate procedural detail target alongside `--polycount N`.
- Added selectable `--spin-axis x|y|z` and per-object preferred spin-axis metadata.
- Generalized projection/fit/hidden-line generation to spin about X, Y, or Z.
- Updated the README with a short command-first Quickstart.
- Documented the planned topology-aware OBJ simplification/preview pipeline.
- Updated measured `yunroll` torus performance to roughly 15-18 FPS on stock PAL timing in VICE.

## 0.1.2-wip

- Fixed a concave-mesh winding regression that removed the visible inner wall/hole of the torus.
- Replaced per-face centre-vector winding guesses with topology-propagated consistent winding plus signed-volume orientation for closed components.
- Added a torus regression test that verifies all tube normals, including the inner ring, point outward.
- No torus topology reduction: the default remains 10x5 = 50 vertices, 100 edges, 50 quad faces.

## 0.1.1-wip

- Fixed generated include paths in `build/main.asm`; 64tass resolves includes relative to the copied assembler source, so `generated/*.inc` must be referenced as `../generated/*.inc`.
- This fixes the undefined `frame_*`, `xchunk_*`, and HUD symbols reported by 64tass.

## 0.1.0-wip

- Generalized rotating torus generator into `c64-3d-toolkit`.
- Added procedural torus, sphere and cube.
- Added Wavefront OBJ import.
- Added `horse_head` preset convention and automatic adoption of `lowpoly_horse_head_zup*.obj` as `objects/horse_head.obj`.
- Added fallback horse-head mesh for pipeline testing when the original asset is unavailable.
- Added topology/detail CLI flags including `--polycount`.
- Retained v0.7-style `step` and v0.8 `bytechunk` renderers.
- Added experimental `yunroll` renderer with unrolled Y-major phases.
- Added generated lower-left topology HUD plus lower-right FPS display.
- Added automatic reduction of orientation-table count when a higher-detail mesh would exceed the current C64 table RAM layout.
- Added source-level assembler sanity checks for relative-branch range and the $1700 LUT boundary before invoking 64tass.
