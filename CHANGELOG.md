# Changelog

## 0.7.6: Sande demo and performance test kit

- Show `INTERACTIVE` at the top right using the HUD font. F3 changes foreground; F4 changes background with a following border by default. F5 toggles alternating sequential palette cycling, F6/F7 adjust speed, F8 locks/unlocks a solid-black border, Ctrl+F7 cycles a custom border, and F2 flashes white briefly before restoring defaults. Benchmark idle, default-rate and fastest-rate cycling.
- Keep the bw defaults and add separate HORS-V2 `-color` carts for both Sande models using their original MTL materials. Reproduce with `tools/build_sande_examples.py --source-colors`; include material/picture validation in the Sande and release checks.
- Benchmark both bw and material-colour versions across the full historical renderer matrix and standalone v1/v2 FPS/RAM variants; include high/average/low FPS for each set on the main performance page.
- Credit Sande for the contributed Pretzel and TAC-2 joystick models on the main page and in the separate `examples/demos_sande` set.
- Rename both OBJ/MTL pairs consistently, including their OBJ object names and material-library references. Preserve source topology and material definitions.
- Add reproducible 192-orientation white-on-black standalone carts, plus separately named interactive v2 carts with persistent left/right rotation direction and the colour controls documented above.
- Expose `build --interactive-cart` for standalone HORS-V2 spin CRTs; reject PRG outputs, incompatible renderers and authored scenes.
- Add a Sande v1/v2 FPS/RAM benchmark with full producer-picture and actual-display verification, matching source hashes and a shared PAL observation window.
- Run all 19 historical method/preference combinations for each registered model, retain capacity failures as N/A, and provide `RUN-SANDE-CHECKS.sh` for a shareable log bundle. Preserve per-entry startup allowance and add between-loop screen allowance to the benchmark timeout budget.
- Include Sande results in the generated performance comparison and its freshness checks, and integrate the set into current-example rebuilds and release checks.
- Rebuild current cartridges and refresh release identities and performance evidence for 0.7.6.
- Add the official-source notice, September 2026 HORS-V2 heading and requested project credits to the main README.

## 0.7.5 (2026-09-11): optional legacy cartridge generation

- Add explicit `--legacy-cart` compatibility output for objects, scenes, demo menus, HiFi, Demo Cart 2, colour tests and cartridge smoke tests. Standard generation remains the default; no automatic fallback occurs.
- Restore the preserved pre-0.7.4 boot programs and original scene ROMH packing together. Legacy mode omits EAPI/EF-Name and does not relocate the scene's 1 KiB into bank 2 ROML.
- Warn that the selected method was discontinued since 0.7.4 and may fall outside recommended EasyFlash layout conventions. Retain physical capacity, packet and reset-vector checks.
- Label automatically named compatibility outputs with `-legacy` and record `cart_write_method` in manifests. Keep these outputs out of the current release index.
- Correct the default object/scene bootstraps to initialize the CPU port latch `$01` before direction register `$00`, matching the EasyFlash guide. Historical boot files remain unchanged.
- Verify exact legacy reproduction against the downloaded v0.7.3 release: all 20 control CRTs have equal before/after SHA-256 and zero differing bytes, including headers, with no masking or binary patching. Controls use the published identities, including 0.7.2 for inherited Marbles/HiFi; actual release builds use 0.7.5.
- Rebuild current examples and refresh release validation. See [0.7.5 release notes](docs/RELEASE_0.7.5.md).

## 0.7.4 (2026-09-11): cartridge loading and EasyFlash metadata

- Route every cartridge `--run` through one VICE launcher: PAL/windowed/non-Warp defaults, explicit user overrides, default-cartridge detachment, CRT write-back disabled and automatic settings saving disabled. Add `run-cart` for existing CRTs and `--vice-clean-settings` for temporary factory defaults.
- Validate CRT header/mapper/reset mode, CHIP lengths/banks/duplicates and reset target directly before launching; verify actual EasyAPI and PETSCII metadata bytes after building.
- Embed the original 768-byte AM/M29F040 V1.4 EasyAPI with source, redistribution notice, pinned provenance and payload checksum. Add the separate 16-character PETSCII EasyFlash menu name. Use object names and the public HORS V2 identity in CRT container titles.
- Introduce shared loader templates with early CIA interrupt/timer shutdown, VIC IRQ acknowledgement and assembly bounds checks. Preserve the frozen historical loader/renderer source files for regression comparisons.
- Move the scene bytes displaced by bank 0 ROMH metadata into the previously unused ROML bank 2 tail. Restore the exact bytes to RAM before entering the renderer; reject overlaps with reset vectors and unexpected occupied relocation space.
- Linux VICE 3.10 validation covers startup, Warp transitions with soft resets, all menu styles and Marbles' complete ending. The reported Windows GUI `$F800` JAM is not yet reproduced or confirmed fixed. See [cartridge loading](docs/CARTRIDGE_LOADING.md).

- Rebuild the current standalone, scene, menu, HiFi and colour-test cartridges with the new loader and 0.7.4 identity. Preserve older versioned cartridges as historical references.
- Refresh the complete renderer comparison and release validation evidence. See [0.7.4 release notes](docs/RELEASE_0.7.4.md).

## 0.7.3 (2026-09-10): independent output colours and COLOR COMBO TEST

- Windows setup r25 asks before a new VICE installation; declining offers an existing path or manual installation later and explains the effect on running/tests and cartridge builds. Clarify the native Python build command and direct use of prebuilt cartridges.
- Add independent foreground, background and border selection to object and authored-scene builds, including resident PRGs and streamed cartridges. Keep `--color` compatible and add `--foreground-color`, `--background-color` and `--border-color` with documented aliases.
- Accept native colour names, decimal/hex/binary palette indices, RGB hex and `rgb(...)`; map RGB inputs to the fixed C64 palette on the host. Apply the same parsing to SVG foreground selection, Blender `c643d_color` properties and the autotuner's `--color-index`.
- Preserve the selected background in initial screen RAM, per-frame source-colour spans and recycled buffers. Restore selected VIC registers after an authored intro. Monochrome inversion changes screen colours without changing geometry.
- Add optional foreground/background/border defaults in `config/c643d.ini`.
- Add `color-combo-test`: four preserved classic animations, automatic ten-second PAL playback per entry, immediate repeat, F3 foreground cycling and F4 background cycling. Only this tester couples the border to the background. SPACE skips; F1 returns to its menu.
- Add F3/F4 monochrome foreground/background, F7 independent border and F8 preset reset during playback in Demo Cart 1 (FPS/RAM) and Demo Cart 2.0. Preserve the menu's F4 HiFi shortcut and F5 exhibition mode. Multicolour entries retain their source palette and support border cycling/reset.
- Reuse the existing IRQ keyboard scan with equal idle CPU cost; no drawing-loop polling or per-frame colour conversion is added. Controls occupy an unused vector-dispatch page in the direct-only v2 integration. `--no-color-controls` produces a build without these controls.
- Include prebuilt test/demo cartridges, reproducible builders, pixel/border/timing/keyboard verifiers and the colour guide. Other 0.7.2 example cartridges retain their bytes and build identities.
- Finalize after user acceptance. PAL VICE regression matches all 93 old/new timing windows exactly; idle keyboard polling remains 82 cycles. All 26 canonical renderer comparison jobs pass. See [release notes](docs/RELEASE_0.7.3.md) and [validation evidence](docs/COLORS_0.7.3_VALIDATION.md).

## 0.7.2: hors-render-v2 default, rebuilt examples and automated releases

- Restore the original README banner, show Demo Cart 2.0 on the main performance page, and exclude the unreleased v2 beta from the public renderer comparison.

- Promote the independently reproduced beta drawing kernel to stable hors-render-v2; preserve beta1 and all older explicit renderer names.
- Add default object/scene/menu integration and rebuild all 19 active cartridges, including the complete Marbles presentation.
- Archive old CRT/PRG previews outside the checkout; retain compact frozen regression inputs and original renderer source.
- Read build identity from root VERSION, including Python and Windows setup. Stamp generated menu copies and verify actual startup/menu/thanks versions with an alternate-version VICE regression.
- Add COMPILE-RELEASE.sh for isolated builds, picture/menu/ending checks, full comparison regeneration, packaging and optional installation.
- Fix the separate ending verifier to acknowledge the native SPACE-start screen through the shared helper; read the HiFi thanks-screen version from its manifest.
- Stable encoding writes metadata directly, avoiding rejection solely because an unused temporary vector representation exceeds 8 KiB.

- Add batched direct-byte mapping with guarded vector-page reuse and independent pictures.
- Add a measured multi-pass scene search with correctness gates, pacing/preferences/encoding choices, and CLI/Markdown/JSON/CSV reports.
- Add Demo Cart 2.0, a separate seven-entry preview with new geometry and selected Ripples Lite source; archive superseded demo artifacts.
- Add source-hash-guarded per-scene encoder selection and an independent three-worker local performance runner.
- Fix benchmark SPACE startup handling, verifier menu-style symbols, dynamic menu-entry counts, and failure diagnostics.
- Bump VERSION, Python and setup labels to 0.7.2; make hors-render-v2 the default.
- Extend the canonical tester with stable v2 FPS/RAM rows alongside all older released methods. The release pipeline regenerates the complete 26-job matrix before packaging.
- Include a Linux all-checks script and both overlay/complete packages. Stable adoption follows independent beta results and the user’s visual review.

## 0.7.1: HiFi exhibition cartridge and presentation update

- Correct the default demo-menu header to use the release version and HORS-V1 label.

- Add a separate `examples/cart_hifi/` reel: complete horse-sniffing animation, captioned HiFi sunflower and horse spinners, and a ten-second closing screen. SPACE starts the repeating presentation.
- Update menu exhibition playback with native closing and opening screens, timed repetition and keyboard controls.
- Preserve normal PLAY ALL and F5 schedules and the hors-render-v1 drawing algorithm.
- Rebuild FPS/RAM menu cartridges with v0.7.1 identity; keep existing standalone and authored-scene cartridge bytes and original build provenance.
- Include the documentation consistency corrections prepared after v0.7.0; refresh current menu links and release instructions.
- Advance VERSION, Python package and Windows setup release labels together.
- Verify optional historical binaries that are available and explicitly skip missing reference coverage when the external archive is partial.


## 0.7.0: hors-render-v1 byte-first rendering and performance tools

### Documentation correction

- Update current architecture, build/configuration, scene and example guides for hors-render-v1.
- Distinguish current 640-sample Marbles from historical 200-sample builds and record actual shipped cartridge sizes.
- Correct cleanup/reproduction prerequisites and broken historical report links; label older renderer and upgrade guides as historical.
- Add a documentation index and cumulative documentation fix-pack instructions.
- Documentation only: no version, renderer, cartridge, sample, manifest or performance-measurement changes.


### Release changes

- Repair comparison reproduction after example cleanup: bundle the original V4 Marbles/V7 Horse & Sunflower vectors as a frozen, hash-checked reference asset. Remove the broken external-history dependency, acknowledge the V10 SPACE startup screen in automated scene verification/profiling, and clarify how to regenerate a stale chart.

- Add optional authored Marbles clean/HUD, FPS/RAM policy benchmarking with mandatory pixel checks and optional ending validation.
- Integrate repeatable candidate runs, recoverable summaries, ignored logs, result bundles and terminal viewers.
- Add independent hors-render-v1/hors-render-v1-scene targets and make hors-render-v1 the default. Prefer byte spans that fit an 8 KiB arena; preserve V9 explicitly.
- Ship hors-render-v1 menu and Horse/Sunflower cartridges in FPS/RAM variants, plus current standalone object cartridges. The accepted Marbles presentation uses 640 samples targeting 16 FPS, with SPACE to start; its recorded scene duration is 41.82 seconds. Historical 200-sample HUD/RAM Marbles variants are not the current shipped presentation.
- Add opt-in `--blender-output-fps` for baked Blender exports with hors-render-v1 playback targets and explicit console reporting; 20 FPS uses alternating PAL holds.
- Fresh Blender 25/20 FPS builds remain local test candidates, not guaranteed sustained rates. Music testing remains pending.
- Record confirmed three-loop byte-policy speed/size comparisons and EasyFlash capacity accounting.
- Document GMod3/GMod4 backend plans, source links and emulator limitations; neither backend is implemented yet.
- Retain historical renderer assembly and resident PRG references byte-for-byte. Superseded generated cartridges move to the optional external sibling archive; their original version labels and bytes remain historical.
- Use new run IDs after upgrade; older experimental results remain preserved.

## 0.6.9: V9 direct ROM byte spans

- Add independent `yunroll-cart-v9` and `yunroll-cart-v9-scene` renderers. Selected V8 byte pictures draw directly from cartridge ROM into the recycled bitmap, eliminating intermediate staging. Keep V8's encoder, payloads, geometry, colours and animation cadence unchanged.
- Optimize the shared page copier for aligned destinations and backwards four-lane traversal. Preserve vector drawing, FPS/RAM preferences, buffer allocations, previous renderer implementations.
- Measure native-release-cartridge A/B throughput ONLY through normal PLAY ALL, with 10 seconds per demo and three loops. FPS preference displays 5,181 → 5,274 frames (+1.8% overall); HiFi sunflower +16.9%, Crawl +2.6%, smaller gains elsewhere. Six entries have identical counts; no entry loses a displayed frame. RAM preference gains 1.8% overall. These are scene-dependent results, not a universal 17% gain.
- Keep F5 internal demo mode for exhibitions only, including the 15-second HiFi holds. It MUST NOT be used for benchmarking. Add a reusable normal PLAY ALL benchmark that traces actual display flips, records source-oracle hashes and ignores host wall time.
- Keep all eight cartridge sizes and frame payloads unchanged from V8. Guard the direct copier's helper regions so the existing Marbles ending remains intact. No additional fixed buffers or reclaimed staging RAM are claimed.
- Validate all examples and both preferences in PAL VICE, 337 mixed/boundary cases plus 257 ROML/ROMH-directory cases per preference, menu handoffs, normal controls, F5 and native endings. All 139 Python tests pass; 118 historical source/executable hashes match. Pristine rebuilds reproduce 108 older runtimes and nine frame images exactly.
- Update README, version identity, detailed measurements, build/verification tools and additive 0.6.8-to-0.6.9 upgrade instructions. Previous release files remain in place; no V8 cleanup is required.

- Add `tools/compare_renderers.py` and the linked per-animation performance lookup chart: high/average/low displayed FPS, best-method ties, size and RAM components. Generated test carts, traces and raw data stay in ignored `comparison-tests/` or an external workspace. A source fingerprint detects a stale chart before release.
- Make V9 the default for build/cart-stream/cart-demos and V9-scene for authored inputs. Old renderers remain explicitly selectable and byte-exact; default selection is an intentional CLI change.
- Add opt-in `--max-fps` and two-pass `--lock-to-min-fps` to the comparison builder for paced test reels. Both default off, announce their state on the console, and leave shipped cartridge timing and integer HUD displays unchanged.

## 0.6.8: Independent V8 adaptive vector/byte-span renderer

- Finalize the V8 release as 0.6.8; rebuild V8 title/closing screens with the final version. Renderer algorithms, source pictures and scene sample cadence are unchanged from rc1.
- Normal PLAY ALL remains 10 seconds per demo for comparison with earlier releases. F5 in the V8 menu starts a separate exhibition loop with 15-second HiFi horse and sunflower entries; other entries remain 10 seconds. ONLY use normal PLAY ALL for A/B comparisons between methods and versions; F5 MUST NOT be used for benchmarking.
- Update `tools/clean_release.py` for local pre-push use: default scope archives and verifies only 0.6.8-rc1 V8 menu carts/metadata before removing them from examples. Earlier methods and final cartridges are retained; the historical broader cleanup is explicit opt-in with `--scope legacy-0.6.7`.
- Add opt-in `yunroll-cart-v8` and `yunroll-cart-v8-scene`. Preserve all existing renderer assembly, shipped CRT/PRG files, older builders and build defaults. Add frozen SHA-256 checks for 102 historical source/binary files.
- Select host-rasterized sparse bitmap-byte spans only when strictly smaller than the unchanged V7 vector payload; otherwise retain vector drawing. This is a new hybrid method, not a claim that V7 vector kernels became 78% faster. No geometry, colour or animation samples are removed.
- Fit the byte copier in unused space in the existing helper region. Keep triple buffering, metadata caches, bank-copy critical sections, duplicate-picture reuse and scene pacing. Compile out byte dispatch for animations that use only vectors. Retain separate FPS/RAM preferences.
- Matched PAL VICE: HiFi sunflower 6.989 to 12.469 FPS (+78.4%), Space Horse Crawl 16.623 to 22.793 (+37.1%), HiFi horse +0.7%; other menu demos essentially unchanged (less than 0.01% timing differences). Clean Marbles mean render cost drops 33.4%, over-budget samples fall 47 to 8/200, scene duration 30.451 to 28.975 seconds. Worst Marbles frame and Horse & Sunflower remain essentially unchanged.
- Menu CRT shrinks from 804,448 to 771,616 bytes; clean/HUD Marbles from 353,008 to 303,760. Supply eight separate V8 cartridges: FPS/RAM menu, Marbles clean/HUD, and Horse & Sunflower. Pre-V8 cartridges remain intact; rc1 menu artifacts are archived by the local cleanup.
- Preserve the existing menu source; add a V8 menu source carrying the new version. Verify 84 launch/handoff paths with 252 picture comparisons across all three styles, timed PLAY ALL, native skip/return, six closing-screen cases, six build screens and both clean Marbles endings.
- Disable VICE EasyFlash CRT writeback in verification/profiling tools; this prevents emulator exit from rewriting reference cartridge title headers. No historical CRT changes are shipped.
- Verify both preferences against original bitmap/colour references, all 12 menu entries and all scene samples; add 337 synthetic cases per preference (677 completed pictures each), including byte/page/count boundaries, mixed formats, empty frames, colour changes, resident reuse and directory crossing. Rebuild V2–V7 for comparison with pristine 0.6.7.
- All 130 Python tests pass; all 102 historical assembly/CRT/PRG checksums match.
- Update README, renderer guide, Windows setup identity and additive upgrade instructions. Deliver a flat changes ZIP and a full source ZIP. The documented local cleanup removes only archived rc1 menu artifacts; Git publication remains a separate step.

## 0.6.7: V7 rendering, PLAY ALL and repository cleanup

- Finalize the tested V5/V6/V7 work from the releases. V7 joins exact drawing runs and selects cell/byte clearing; matched PAL VICE tests measured up to 14.6% higher throughput than V6 with the same geometry, colours and samples. The twelve-demo CRT is 804,448 bytes versus V6's 927,568 bytes.
- Keep `--prefer fps` as the preference default, with optional smaller Y kernels via `--prefer ram`. Rebuild FPS/RAM V7 menu and Marbles carts with final `0.6.7` build-screen text.
- Retain all twelve menu entries, the `+` scroll indicators, all three F1 menu styles, configurable PLAY ALL duration and its ten-second THANK YOU FOR WATCHING screen. Horse and Sunflower remains a separate editable Blender scene and V7 scene cart; its measured playback is about 4.3 samples/s.
- Include the Blender camera-coordinate/winding correction from rc5, including mirrored objects and camera scale handling. Original meshes/materials and released comparison vectors are retained.
- Remove `examples/old/`, older V4/V5/V6 and V7 candidate menu bundles and the generated MP4 from the source package. Preserve these bytes in a separate oldies ZIP. Keep only final FPS/RAM menu CRTs in the active folder, metadata/reports in subfolders, and historical benchmark evidence in `docs/benchmarks/cart_demos/`. A 399,186-byte frozen vector reference replaces the old V4 menu CRT as the default rebuild input. Add `tools/clean_release.py` so overlays archive local copies outside the checkout before removal; repeated cleanup is harmless.
- Ignore historical downloads, generated videos, Blender backups, emulator logs and Python caches. Update README, example guides, Windows release labels and the upgrade/publish instructions. Existing Git history is unchanged.

## 0.6.7-rc5: Horse and sunflower scene, camera export and PLAY ALL closing screen

- Preparing v0.6.7; this remains a release, not a published final release.
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

## 0.6.7-rc2: Clean merge of the V5 release

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

### 0.7.0 example selection follow-up

- Select the visually accepted 640-sample, 16 FPS force-bytes Marbles presentation (41.82-second scene).
- Move superseded cartridge outputs into history subdirectories; preserve legacy renderer code and regression inputs.
- Provide checksum-guarded local promotion without rerendering.
