# Changelog

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
