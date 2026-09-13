# v0.7.9: The Golden Dragon & SAKU 2026 — release_final_v4

SAKU starts with the original light starfield enabled: eight single-pixel stars behind the gradient logo. **4** switches to the fuller field and back. **F2** restores the light starting profile. HORS-V3 remains the default renderer.

**RUN/STOP**, or **Esc in the bundled VICE keymaps**, now opens and closes help in all generated HORS-V3 interactive carts. **Shift+H** remains available; **Space** also closes help. Held keys are consumed until release. The v0.7.8 intro layout still waits indefinitely for SPACE, with `press SHIFT+H for help` on its own row above the start prompt. Closing startup help returns to that wait.

## Star-off fix

The old Shift+O outline/gradient and Shift+B white-card handlers enabled stars unconditionally. This revision preserves their on/off state. Native host-key tests reproduced the old failure, then verified the corrected handlers in light and full modes. After a star-off transition, `$d015` stays zero and captured borders are clean. Enabled stars continue to use the displayed frame for masking. No growing allocation or memory leak was demonstrated.

| Key | Action |
| --- | --- |
| RUN/STOP / Esc / Shift+H | Open or close help |
| Space | Start from intro, or close help without starting playback |
| 1 / 2 / 3 | Reset / more / fewer stars in the selected field |
| 4 | Switch light/full, preserving density and on/off state |
| Shift+S | Toggle stars |
| Shift+O / Shift+B | Change outline/gradient or card style, preserving starfield on/off |
| Shift+G | Gradient space preset, explicitly enables stars |
| Shift+T / Shift+W | Solid white-background preset, explicitly disables stars |
| Shift+U | Hide or show all HUD text, including INTERACTIVE |

Future interactive builds include stars disabled unless requested. The new `--starfield-profile light|full` selects the starting and F2-reset profile independently of `--starfield-default enabled|disabled`. Ordinary builds retain full as their profile default; SAKU explicitly selects light. `--no-starfield` excludes both fields while keeping RUN/STOP/Shift+H help and speed controls.

## Performance

Same SAKU cart, default rotation speed and visible HUD, 750 PAL VICE refreshes after warmup. FPS measures displayed-buffer changes, including star work and VIC-II contention.

| Field | Displayed FPS |
| --- | ---: |
| Off | **18.18** |
| Light, 8 points (default) | 15.91 |
| Full, 16 points | 13.70 |

Changing the starting profile adds no per-frame selection work. RUN/STOP reuses the star-density row read and adds **9 CPU cycles per idle input poll**, without a new CIA read. With stars excluded it needs a **34-cycle** poll, including saving/restoring A. Help adds **no raster-IRQ work**. Fixing Shift+O/B removes event-only instructions; it adds no idle work.

The speed/density poll averages 165.47 elapsed VICE cycles over 32 samples. Both starfield off paths remain 32 elapsed cycles. Stopwatch figures include call/return and machine contention, so they differ from opcode-only cycle counts.

**ROM allocated: 440 KiB. Free: 584 KiB.** No extra RAM reservation for these changes. Both starfields remain resident in RAM; switching needs no cartridge reload.

[SAKU keyboard map and previews](../examples/saku_2026/README.md) · [Detailed performance](../examples/saku_2026/PERFORMANCE.md) · [All renderer comparisons](PERFORMANCE_COMPARISON.md)

## Verification and contents

263 unit tests (3 expected skips); 18 cold-boot/SPACE checks; 112 host-key state checks across both VICE keymaps; all SAKU pictures/styles, star masks, density, speed, colours and HUD checks; shared interactive options including no-star help; Pretzel and Dragon measurements; complete uncapped renderer comparison.

Three CRTs changed from final v3: SAKU interactive and both interactive Pretzel variants. The other 63 CRTs are byte-identical. Physical hardware and OS GUI event delivery were not tested. The keymap tests send real host keysyms through the VICE keyboard API and native CIA scanner.

The full ZIP contains the complete project. The incremental ZIP is cumulative against the supplied v0.7.8 baseline. Historical v1–v3 records remain included.
