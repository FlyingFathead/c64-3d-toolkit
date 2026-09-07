# Changelog

## 0.6.7: V7 rendering, PLAY ALL and repository cleanup

- Finalize the tested V5/V6/V7 work from the release candidates. V7 joins exact drawing runs and selects cell/byte clearing; matched PAL VICE tests measured up to 14.6% higher throughput than V6 with the same geometry, colours and samples. The twelve-demo CRT is 804,448 bytes versus V6's 927,568 bytes.
- Keep `--prefer fps` as the preference default, with optional smaller Y kernels via `--prefer ram`. Rebuild FPS/RAM V7 menu and Marbles carts with final `0.6.7` build-screen text.
- Retain all twelve menu entries, the `+` scroll indicators, all three F1 menu styles, configurable PLAY ALL duration and its ten-second THANK YOU FOR WATCHING screen. Horse and Sunflower remains a separate editable Blender scene and V7 scene cart; its measured playback is about 4.3 samples/s.
- Include the Blender camera-coordinate/winding correction from rc5, including mirrored objects and camera scale handling. Original meshes/materials and released comparison vectors are retained.
- Remove `examples/old/`, older V4/V5/V6 and V7 candidate menu bundles and the generated MP4 from the source package. Preserve these bytes in a separate oldies ZIP. Keep only final FPS/RAM menu CRTs in the active folder, metadata/reports in subfolders, and historical benchmark evidence in `docs/benchmarks/cart_demos/`. A 399,186-byte frozen vector reference replaces the old V4 menu CRT as the default rebuild input. Add `tools/clean_release.py` so overlays archive local copies outside the checkout before removal; repeated cleanup is harmless.
- Ignore historical downloads, generated videos, Blender backups, emulator logs and Python caches. Update README, example guides, Windows release labels and the upgrade/publish instructions. Existing Git history is unchanged.

## 0.6.7-rc5: Horse and sunflower scene, camera export and PLAY ALL closing screen

- Preparing v0.6.7; this remains a release candidate, not a published final release.
- Added `horse_and_sunflower`: original coloured HiFi meshes, a fixed close side-view camera, a stationary flower angled toward the camera, and a looping horse approach/two-sniff/withdraw animation. Delivered as an editable Blender scene and a separate V7 C64 test cartridge; multi-demo integration follows review.
- Correct Blender camera-space polygon orientation in the shared exporter. Positive-forward Z conversion reverses handedness; polygon order now accounts for the combined object/camera transform, including mirrored objects. Materials stay attached to their original polygons. Existing prebuilt reference vectors are preserved.
- PLAY ALL now shows THANK YOU FOR WATCHING, the build version, DEMO CART, project URL and F1 TO RETURN TO MENU after its last entry. Hold for 500 PAL ticks (about ten seconds), then launch the first demo; F1 returns to the same menu style. Manual next-demo wrapping remains immediate.
- Verified the closing-screen timeout, text/colours, F1 scanner, style preservation, restart and subsequent launch in default, decorative and flashing party menus. Verified the full timed PLAY ALL round, SPACE skipping and manual-return path in PAL VICE.
- Reopened the Blender scene and checked its original topology/materials, fixed camera/flower and loop seam. Shared export projection matches Blender within 0.00002 pixels, including mirrored transforms. Scene cartridge: all 84 samples match the original compiler oracle across 171 checks and three buffers; about 4.3 samples/s and 19.71 seconds per loop in PAL VICE. This close-up exceeds its requested six-tick cadence and remains a separate test for review.
- All 118 source tests pass. Menu launch regression passes 84 launches and 252 picture comparisons across all styles. New scene CRT headers use the actual scene title; Blender exports honour `c643d_title`.
- Updated README introduction, example guides and Windows setup version metadata. FPS remains the default preference. Ship a flat changed-files ZIP for overlaying the project root and a separate full ZIP.

## 0.6.7-rc4: V7 run joining, selective clearing and PLAY ALL

- Added opt-in V7 ordinary/scene renderers, preserving released V4/V5/V6 carts and assembly. `--prefer fps` is the default; optional `--prefer ram` uses compact Y loops and saves 1,052 resident code bytes in the regular horse comparison.
- Join connected compatible runs using their exact packed step paths, with decoded-pixel and resolved-colour equality checks. Choose tagged byte-clear spans where cheaper without increasing metadata size. Reuse and sample timing are preserved.
- Final PAL VICE menu throughput improves 0.2–14.6% over V6. Menu CRT: 804,448 bytes versus 927,568; Marbles: 353,008 versus 418,672. Clean Marbles: 30.45 seconds versus 31.43, with all 200 samples retained.
- Added fixed PLAY ALL above the scrolling list, selected at startup. Infinite cycle, ten seconds per demo by default, `--play-all-seconds` 1..255, SPACE skip, RUN/STOP/F1 return. Start timing after the first visible picture. F1 still cycles all menu styles; held SPACE is latched across a handoff.
- Supplied FPS/RAM twelve-demo carts and clean/HUD Marbles with rc4 build screens, plus `tools/build_v7_examples.py` for rebuilding from the released vectors without Blender.
- Validation: 118 Python tests; both preferences matched all menu and Marbles samples to frozen V6 oracles; 1,744 kernel/clear cases per preference; holds and directory boundaries; 81 menu states; 84 launch/handoff checks including flashing party mode; timed PLAY ALL/wrap/skip/return at ten seconds and a separate two-second party build; build screens and finite endings.
- Package as flat changed-files overlay against rc3 plus a full ZIP. Reports live in the example folders and the V7 guide; no extra root release-note or validation directory.

## 0.6.7-rc3: V6 partial-byte drawing and direct metadata loading

- Added opt-in `yunroll-cart-v6` and `yunroll-cart-v6-scene`, preserving the released V4/V5 cartridges and their renderer sources. V4 remains the default menu build; V5 retains its existing lossless stream optimizations.
- Accumulate partial X-major head/tail bits before writing each bitmap byte. Keep the existing aligned eight-pixel chunk path and both line directions.
- Recycle the old bitmap/colour slot before fetching; copy incoming metadata directly into that slot's cache and stage line records separately. Removed the second metadata copy, retaining bounded cartridge-copy bursts and interrupt-safe mapping restoration.
- Matched PAL VICE checks against frozen V5 oracles measured 1.2–5.4% higher completed-frame throughput across all twelve menu demos. Clean Marbles' mean render cost fell 3.63%; its unchanged 200 samples / seven-raster-tick cadence took 31.43 seconds versus 32.07, with 93 rather than 107 frames above the render budget. No geometry, colours, samples or playback deadlines were reduced.
- Net resident code/data change is +90 bytes in the regular horse comparison (+115 main/HUD, -25 copy helper); lookup tables and buffer allocations are unchanged. V6 vector payloads and shipped CRT sizes equal V5's.
- Built the V6 twelve-demo menu and both Marbles variants with the `0.6.7-rc3` / `yunroll-v6` build screen. Added `tools/build_v6_examples.py` to reproduce these from the released vector samples without a Blender rebake.
- Profiling follows explicit labels in the new recycle/fetch order and omits the removed cache stage. The bitmap verifier explicitly selects PAL. Verified all twelve menu demos, all 200 frames of both Marbles builds, 1,152 X-kernel cases, 270 reuse/hold samples including colour-only changes, stream boundaries, 75 menu states, build-screen timeout/SPACE scan and the finite ending. All 111 Python tests pass. Reports and limits are linked from `docs/CARTRIDGE_STREAM_V6.md`.
- Added the main README variant and cartridge-size tables. Planned compact, balanced and speed-focused profiles independently of demo/game use; these are not new runtime modes in rc3.

## 0.6.7-rc2: Clean merge of the V5 release candidate

- Merged rc1 into the latest local source snapshot, preserving the removed `0.6.4-local` cartridge and the original executable permissions. Kept release information in this changelog; omitted the extra root release-notes file, monitor log and validation directory.
- Retained rc1's opt-in `yunroll-cart-v5` and `yunroll-cart-v5-scene`: redundant-run removal after colour resolution, exact-picture ROM sharing and resident-buffer reuse, four-section page copies, eight-pixel Y-major blocks, cached host DDA selection and explicit profiling stages.
- Rebuilt the twelve-demo V5 cartridge and both V5 Don't Lose Your Marbles cartridges with `0.6.7-rc2` version text. Their black-and-white build screens wait about three seconds or accept SPACE. V5 rendering and sample data are unchanged from rc1; V4 remains the default renderer.
- Playback follow-up: the user reported smooth V5 playback on Windows 11 after seeing twitches with NVIDIA on Linux/Wayland. Host presentation is suspected; no renderer or driver defect is established. The regular horse head and both regular sunflower variants have no duplicate pictures and disable whole-frame reuse; redundant-line removal remains active.

## 0.6.6: Don't Lose Your Marbles early beta

- Added separate Blender and EasyFlash examples: targeted alternating cube/marble pours, a continuous orbit and a 32-piece tabletop fracture that drifts into a constellation. Isolated waiting emitters from active collisions; all 45 released bodies enter the table/pile volume.
- Added the opt-in `yunroll-cart-v4-scene` extension: unchanged V4 drawing kernels, 16-bit scene indices, paged ROM directories, dual-chip frame packing, PAL pacing and custom/clean HUD variants.
- Added a native title introduction and finite `--ending`: backspacing demoscene greeting, animated thank-you credits and a staged BASIC boot with the self-typing ghost message. The complete HUD build ends at 58.151 seconds; the vector scene takes 36.370 seconds.
- Verified all 200 scene frames in both carts, the intro and ending, and 514 unobscured tabletop-marble regions. All 105 source tests pass. The stream uses 405,972 vector bytes. Music/digi playback remains unimplemented.
- Documented cartridge examples in `examples/README.md`, added the scene guide and corrected GIF timing. Kept the original V4 files, falling-cubes example and v0.6.5 twelve-demo menu cart byte-identical.
- Bumped toolkit and Windows setup metadata to 0.6.6. This package prepares the next patch version; it does not publish a GitHub release.

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
