# v0.7.9: The Golden Dragon & SAKU 2026 — release_final_v5

Shared HORS-V3 interactive cartridges now include paged help and exhibition controls. The original introduction still waits indefinitely for SPACE; its separate `press SHIFT+H for help` row is retained. SAKU starts normally with gradient spin and light stars. Ordinary interactive carts keep stars disabled unless the user enables them through the CLI.

| Key | Action |
| --- | --- |
| RUN/STOP / Esc / Shift+H | Open/close help; Space also closes |
| Left / right in help | Page 1 / page 2 |
| 5 | Exhibition on/off |
| 6 | Sequential/random style order |
| 7 / 8 | Interval -/+5 seconds, from 5 to 60 |
| Shift+S | Stars on/off, including during exhibition |
| 1 / 2 / 3 | Reset/more/fewer stars |
| 4 | Light/full starfield |
| Shift+U | Show/hide all HUD text, including INTERACTIVE |

Exhibition defaults to a five-second sequential interval. SAKU cycles its solid outlined, gradient and rounded white-card styles, retaining spin/crawl. Random avoids immediate repeats. HUD and stars switch off once on entry; subsequent scene changes retain manual star/HUD choices. Exit restores the entry HUD visibility and star on/off state while retaining selected starfield profile/densities. Interval adjustments show a brief bottom-row message. Help pauses the timer; F2 ends exhibition and restores configured order/interval plus the usual presentation defaults.

The shared CLI adds `--exhibition-default enabled|disabled`, `--exhibition-order sequential|random`, and `--exhibition-interval SECONDS`. Exhibition startup is opt-in and still follows the SPACE intro. Generic single-animation carts retain that animation; only compiled presentation styles can be cycled. Starfield exclusion and fixed HUD builds remain supported. [Full behavior and CLI reference](EXHIBITION.md).

## Full-width Blender export and input flips

New `.blend` conversions draw across 320×192; `--viewport-width 256` retains the old width. Clear spans are split on the host to avoid the runtime's 8-bit Y wrap beyond 32 cells. Camera projection, clipping, colours, loop clearing and unchanged HUD pass native checks. Existing interchange files retain their recorded width (256 when absent); re-export the .blend for new full-width camera framing.

[Editable zoom/tracking test cards](../examples/blender_viewport_test/README.md) include two new carts, .blend/.c643dscene sources, VICE screenshots/GIFs and detailed results. Each cart passes 51 bitmap/colour checks over three loops/all buffers. Projection matches Blender within 0.00005 pixels. Uncapped calibration zoom: 8.74 FPS at 256 width; 8.09 at 320, which draws more pixels. The wider path adds no per-pixel branches or fixed buffer allocation.

[Input flips](INPUT_FLIPS.md): `--flip-input-horizontal` / `--flip-input-vertical`, aliases `--flip-horizontal` / `--flip-vertical` and `--mirror-horizontal` / `--mirror-vertical`. Default off, both directions composable, host-only artwork reflection. Seven conversion/interactive cases pass exact-reflection and native HUD/bitmap/colour checks. Sande confirmed his mirroring happened inside Blender, before export.

[Blender FAQ](BLENDER_FAQ.md) explains the 256-pixel cutoff, matching preview sizes, old-scene migration and orientation checks.

## Measured cost

Same gradient spin, default speed, HUD and stars hidden; PAL VICE 3.10, 750 refreshes after warmup. FPS counts displayed-buffer changes.

| Scheduler | Displayed FPS |
| --- | ---: |
| Inactive | **18.65** |
| Active; 60-second interval, no change in this window | 18.58 |

The matched active-scheduler difference is **-0.36%**. The separate five-second exhibition tour measures 17.23 FPS across three styles; its workload differs and is not an overhead estimate.

Normal SAKU gradient playback, HUD visible: **15.91 FPS light**, 13.70 FPS full, 18.11 FPS stars off. [All density, style and historical results](../examples/saku_2026/PERFORMANCE.md).

Inactive exhibition adds **no raster IRQ instructions**. Keys 5–8 add **67 CPU cycles per idle input poll**. The main/event code fits existing reserved RAM; packed help adds **1 KiB at $c000–$c3ff**. SAKU still allocates **440 KiB ROM**, leaving **584 KiB free**. No new animation frame streams are required.

## Verification and package

272 unit tests (3 expected skips); 18 V3 cold-boot/SPACE checks; 112 existing host-key checks plus 106 exhibition/page checks across both VICE keymaps. SAKU's native checks cover all eight presentations, three buffers, speed/HUD/density controls, star masking, both help pages, interval limits, random non-repetition, timer pause and retained star settings. Notification expiry restores white as well as black backgrounds. The exhibition GIF comes from actual VICE screenshots with displayed bitmap/colour and sprite-enable checks.

The three CLI startup combinations (ordinary default, enabled/random/60 seconds, enabled with stars and manual HUD keys excluded) passed native boot-state checks. The generic interactive option matrix, both interactive Pretzel variants, all Dragon variants, and the complete uncapped renderer comparison have fresh or explicitly verified unchanged-cartridge evidence. Physical hardware and OS GUI event delivery were not tested.

Three CRTs changed from final v4: SAKU interactive and the two interactive Pretzel variants. The other 63 prior CRTs are byte-identical. Two new Blender calibration CRTs are included. Full source and cumulative incremental ZIPs are supplied; the latter overlays the supplied v0.7.8 baseline. Historical results remain included.

[SAKU GIFs and keyboard map](../examples/saku_2026/README.md) · [All performance comparisons](PERFORMANCE_COMPARISON.md) · [Validation](benchmarks/release-final-v5/validation.json)
