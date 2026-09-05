# Changelog

## 0.6.5: Animated-menu launch fix and V4-only active cart

- Fixed `JAM at $0008` when launching from the demoscene (animated colour) menu. The loader now disables and acknowledges the menu raster IRQ and restores `$01=$37` before reading cartridge ROM. The animated menu had left `$01=$35`, causing payload and control-shim copies to read RAM instead.
- Rebuilt the current V4 demo cart as `c643d-demo-v0.6.5-yunroll-cart-v4-all.crt`; renderer code, vector data and frame allocation are unchanged. Added a VICE regression that launches all twelve demos from all three styles across two style cycles, including menu returns and next-demo wrapping.

- Moved both 0.6.4 comparison bundles and their historical reports under `examples/old/cart_demos/`. The cleanup command handles ZIP overlays and preserves local edits. Explicit V2/V3 builds now default to the archive folder; V4 remains the normal build/run choice.
- Bumped CLI, package, Windows setup labels, current documentation and all generated menu styles to 0.6.5.
- Corrected ZIP update timestamps so Python invalidates cached bytecode after same-length source edits.

## 0.6.4: HiFi assets and cartridge streaming variants

- Added separate `yunroll-cart-v4` with inline line dispatch and direct kernel continuation; modest further gains over V3 with identical vector data.
- `cart-demos` now uses one selected renderer for all twelve entries (default V4). Shipped V3-all and V4-all cartridges preserve original samples, colours and visibility for matched A/B comparisons.
- Added a ten-row scrolling menu with fixed horizontal borders and buffered character/colour updates in all three styles; navigation no longer clears the screen.
- Archived superseded mixed-method carts under `examples/old/cart_demos/`; added an idempotent cleanup command for ZIP updates which preserves local modifications.
- Verified all twelve entries for both renderers in PAL VICE, all three menu styles, control paths and V4 RAM/count boundaries.

- Added opt-in `yunroll-cart-v3`, with direct line dispatch, cheaper run counting, vertical-loop fall-through, faster page copying and constant-time metadata skips. The vector format and frame/cache capacities match V2. PAL VICE HiFi throughput improves by approximately 12–13% with exact pixel/colour matches.
- Added separate V3 standalone and twelve-entry demo cartridges, a stage profiler and VICE boundary checks. Use `cart-demos --stream-renderer yunroll-cart-v3`; standalone defaults are retained; superseded menu carts are archived below `examples/old/cart_demos/`.

- Added title-art-inspired `horse_head_hifi` and `sunflower_torus_hifi` OBJ/MTL presets; originals unchanged.
- Added separate `yunroll-cart-v2` renderer and `cart-stream` command: banked EasyFlash frame data, fixed RAM staging, per-buffer metadata caches and 16-bit visible-run counts.
- Added two 192-orientation CRT demos, pixel/colour verification in VICE, and cartridge support in the README introduction.
- The 0.6.4 menu cartridge includes all ten original demos plus both 128-orientation HiFi streams in ROMH, with versioned CRT aliases. Original PRG renderers and the `yunroll-cart` scaffold are retained.

## 0.6.3

- Finalize the v0.6.3 EasyFlash milestone and ship a ready-to-run ten-animation demo cartridge at `examples/cart_demos/c643d-demo.crt`, alongside its cartridge map and JSON manifest.
- Preserve the cartridge menu style state across control-shim reinstalls, fixing F1 style cycling that previously only redrew the default menu.

- Began the separate experimental `yunroll-cart` cartridge backend without changing the production `yunroll` PRG renderer.
- Added a minimal native EasyFlash bank-switch smoke build that assembles an 8 KiB ROMH bootstrap, packs a 1 MiB raw EasyFlash image, converts it to `.crt` with `cartconv`, and emits a human-readable bank map plus JSON manifest.
- Added optional `cartconv` discovery/configuration and `--cartconv` overrides. `doctor` reports it as optional; cartridge output fails with targeted setup guidance when it is missing, while normal `.prg` builds remain unaffected.
- Added cartridge development roadmap and reference documentation. The implementation policy starts with simple measurable bank/stream tests before introducing direct ROM consumption, caching, compression, or long-form animation optimizations.
- Set the release version to 0.6.3 while preserving the v0.6.2 PRG golden-output baseline.
- Added `cart-demos` (with `cartridge-demo` compatibility alias), a menu-driven EasyFlash integration cartridge that packs the ten canonical toolkit animations into banked ROML storage. Menu controls use natural four-way cursor semantics (up/left previous, down/right next) and RETURN launches an animation.
- Added a cart-only `$0200` raster-IRQ control shim: F1 or RUN/STOP returns from a running animation to the cartridge menu, while SPACE launches the next animation and wraps at the end. Only the copies packed into the CRT are IRQ-patched; the canonical `.prg` files remain untouched.
- Added a RAM-resident cartridge demo loader at `$C800-$CFFF` plus a `$DF00` EasyFlash-RAM trampoline. Existing PRGs are copied through 256-byte staging pages so destination RAM hidden beneath `$8000-$9FFF` is handled explicitly rather than relying on write-under-ROM behaviour.
- Added host-generated per-entry bank/load/length/checksum metadata and a VICE debug-cart validation path that loads and checksums every packed PRG before reporting success.
- Verified an existing production torus PRG launches and renders from the generated EasyFlash CRT; this demo launcher is deliberately separate from the upcoming true `yunroll-cart` frame/table streamer.
- Added `--generate-cart-demos` as a convenience counterpart to `cart-demos`; final demo artifacts live under `examples/cart_demos/` while temporary assembler/raw-ROM files remain under `build/`.
- Keep generated demo manifests portable by recording repository-relative source PRG paths rather than machine-specific absolute build paths.
- Added selectable cartridge-menu presentation with `--menu-style default|decorative|demoscene`. `default` keeps the simple utility menu, `decorative` adds a static framed/colour layout with a menu-only compact 5x7 charset derived from the existing HUD font, and `demoscene` adds a lightweight raster-IRQ colour-gradient animation.
- Every demo CRT now carries all three menu runtimes. `--menu-style` selects the startup presentation, while F1 in the menu cycles live through `default` -> `decorative` -> `demoscene` -> `default`; the highlighted entry is preserved across style swaps and the selected style is preserved when returning from an animation.
- Added a common cartridge-menu footer to every style: `by FlyingFathead, 2026` plus `github: flyingfathead/c64-3d-toolkit`. The custom lowercase glyphs are menu-only and do not alter the production HUD font or ordinary PRGs.
- Updated the README with a new try-it-first/getting-started path that points directly to the shipped PRG examples and ready-to-run `examples/cart_demos/c643d-demo.crt`, while documenting the current cartridge capabilities, limitations, and the next measured-streaming milestone consistently.

## 0.6.2

- Expand the default overlay-enabled drawable viewport from 256x144 to 256x192 while preserving explicit `_legacy144.prg` performance/reference builds; no-overlay builds use the full 256x200 bitmap height.
- Document the viewport/performance tradeoff explicitly: 144-line legacy builds preserve the older performance profile, while 192/200-line builds intentionally do more drawing/clearing work and may report lower FPS on complex scenes.
- Add `--no-text-overlay` using separate no-overlay ASM derivatives for `step`, `bytechunk`, and `yunroll`, so production renderers pay no code-size or cycle cost for the alternate path.
- Add a separate `yunroll` raster-time debug renderer that marks actual main-loop render work with the border without instrumenting the production renderer.
- Add `[render_defaults]` configuration for text overlay, viewport height, overwrite policy, and raster-time profiling; command-line options remain highest precedence.
- Add `--overwrite-policy allow|warn|error`, warn before replacing existing build outputs by default, and fix output directories outside the repository root.
- Add deterministic PRG checksum regression manifests and `test-examples` reporting `MATCHING`, `CHANGED`, or `ABSENT` per generated PRG plus totals. Historical v0.6.0/v0.6.1 hashes remain available for byte-exact compatibility checks.
- Reorganize generated/reference artifacts into per-example directories under `examples/`; Blender falling-cubes sources and PRGs now live under `examples/blender_falling_cubes/`.
- Add a safe one-time `tools/migrate_examples_layout.py` helper for upgrading older flat example layouts without overwriting locally modified files.
- Remove redundant byte-identical `space_horse_spin.prg` / `space_horse_crawl.prg` aliases from the shipped example tree while retaining their historical hashes.
- Extend standard example generation/testing to four lanes: 192-line normal, 144-line legacy/performance, 200-line no-overlay, and 192-line raster-profiler builds.
- Add the Blender-only falling-cubes regression matrix with authored-colour and forced-monochrome current builds plus the original 144-line / sample-step-3 colour PRG as `falling_cubes_c64_color-yunroll_legacy144.prg`.
- Use sample-step 4 for current 192/200-line falling-cubes builds so the expanded viewport remains within the fixed C64 table-RAM budget; retain sample-step 3 for the byte-exact legacy144 reference.
- Clean manifest variant overrides so historical Blender builds replace `--sample-step 4` with `--sample-step 3` instead of emitting both options on the command line.
- Improve Blender table-RAM overflow diagnostics with scene/sample/viewport context, overflow/headroom information where available, an explicit note that host RAM is not the problem, and actionable sampling/range/detail suggestions.
- Harden Blender `.blend` imports by passing `--disable-autoexec` before opening the scene, and apply the same policy to the Blender/`bpy` preflight.
- Make plain `pytest -q` work from the repository root via `tests/conftest.py` and expand regression coverage for the new release paths.
- Final 0.6.2 PRG golden outputs are byte-identical to the verified 0.6.2-rc3 set; finalization changes release metadata/docs and the duplicate-option cleanup only.

## 0.6.0

- Fixed static Blender rigid-body exports: stateful scenes are now evaluated through every intervening source frame while `--sample-step` controls only which frames enter the C64 tables. Added an explicit warning when all captured frames are geometrically identical.
- Fixed Blender 4.x scene export by calling `calc_matrix_camera()` on the evaluated camera object instead of its data block. Blender exporter tracebacks now also produce a nonzero process exit code and a truthful build failure.
- Added viewport clipping for authored Blender/interchange scene edges, allowing normal camera compositions with partially offscreen geometry while retaining the classic auto-fit guard for legacy OBJ/SVG/procedural builds.
- Restored Blender preflight to its proper scope: start Blender headlessly, import its bundled `bpy`, and report the version. Removed unreliable `bpy.types.Object` method introspection that produced false failures on Blender 4.0.2; the real scene exporter remains the capability test and reports API failures with a nonzero exit code and traceback. Documented current Blender 5.2 LTS as recommended, with Ubuntu 24.04's Blender 4.0.2 package retained as a supported older fallback and an explicit warning about newer `.blend` files not being backward-compatible.
- Added optional animated Blender scene compilation with `--blend`, frame-range sampling, active Blender camera projection, multiple evaluated mesh objects, stable-topology deformation/rigid-body support, and Blender material colours.
- Added a versioned Blender-neutral `.c643dscene` interchange and direct `--scene` compilation path. Blender runs `tools/blender_export.py` with its own bundled Python; the ordinary toolkit remains dependency-free and never imports `bpy`.
- Added executable discovery plus a real headless `import bpy` preflight. Missing/broken Blender stops only the `--blend` path and prints platform-specific installation instructions, including `sudo apt install blender` for Ubuntu/Debian.
- Blender animations use strict authored-frame semantics: table overflow fails with sampling/range/detail suggestions instead of silently reducing frame count.
- Added `examples/blender_falling_cubes/falling_cubes_c64.py`, which generates a six-cube rigid-body demo `.blend` from the command line, plus Harry's deterministic 40-cube `falling_cubes_full.py` and Blender-4.00 `.blend` authoring/stress example.
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
