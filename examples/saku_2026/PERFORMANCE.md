# SAKU 2026 performance — release_final_v5

Measured in this exact interactive cart in PAL VICE 3.10: 750 refreshes after warmup, normal rotation speed, HUD shown. FPS counts displayed-buffer changes, including sprite work and VIC-II DMA.

| Starfield | Displayed FPS | Average visible points |
| --- | ---: | ---: |
| Stars off | **18.11** | 0.00 |
| Original light, 8 points (SAKU default) | 15.91 | 4.04 |
| Full, 16 points | 13.70 | 10.99 |

Light is **16.1% faster than full** on this animation. Relative to stars off, light costs 12.2% of displayed throughput; full costs 24.3%. Neither field is free.

Configured counts differ from visible counts because points outside the viewport or behind the logo are suppressed. `1/2/3` resets/increases/decreases density and `4` switches resident light/full kernels without a ROM reload.

## Exhibition scheduler

| Same gradient spin, HUD/stars hidden | Displayed FPS |
| --- | ---: |
| Exhibition inactive | **18.65** |
| Exhibition active, 60-second interval | 18.58 |

The active scheduler changes displayed throughput by **-0.36%** in this 15-second window with no scene switch. This isolates timer/service overhead. The five-second three-style tour averages **17.23 FPS** over 800 refreshes; it draws different styles and is not an overhead comparison.

Inactive exhibition adds no raster IRQ instructions. The 5–8 key scan adds 67 CPU cycles per idle input poll. Scene selection is deferred to a safe producer/input boundary. The two tested sequential intervals were 4,950,027 and 4,882,089 machine cycles, approximately five PAL seconds; the next displayed frame can follow slightly later. Help pauses the timer. The notification expires and restores the row background in all three picture buffers, including white backgrounds.

## Density in the full field

| Configured points | Displayed FPS |
| --- | ---: |
| off | **18.11** |
| 2 | 17.31 |
| 8 | 14.91 |
| 16 (default) | 13.70 |
| 32 | 12.10 |

## Matching presentations

| Presentation, HUD shown | Full FPS | Light FPS |
| --- | ---: | ---: |
| Gradient spin | 13.70 | **15.91** |
| Rounded white-card spin | 11.36 | **12.97** |
| Gradient crawl | 16.24 | **19.05** |
| Solid outlined spin | 13.70 | **16.24** |
| Solid outlined crawl | 15.31 | **18.92** |

Bold marks the faster result within each matching presentation.

## Routine cost

| Routine / state | Mean elapsed cycles | Minimum | Maximum |
| --- | ---: | ---: | ---: |
| stars-on | 3936.88 | 3686 | 4219 |
| stars-off | 32.00 | 32 | 32 |
| light-stars-on | 1818.94 | 1796 | 1841 |
| light-stars-off | 32.00 | 32 | 32 |
| speed-poll-idle | 243.16 | 218 | 424 |
| effects-poll-idle | 86.03 | 82 | 125 |

VICE stopwatch across 32 calls, including call/return and contention; these are not pure opcode CPU totals. The speed-poll result includes the complete density, RUN/STOP and new exhibition scan. Starfield off paths remain 32 elapsed cycles.

## RAM and ROM

Both star kernels and coordinate sets load once. Light paths occupy $8000–$83ff; the light kernel fits the existing density reservation at $9c00–$9fff. The 4 key changes the IRQ call operand only on events, adding no per-refresh dispatch branch. `--no-starfield` excludes these regions and code.

Exhibition adds 19 mutable state bytes, a 6-byte SAKU style table, and 96 bytes of precomputed decimal/replacement glyphs inside already reserved HUD/help space. Its main block occupies $9540–$9770; notifications and their template occupy $99f5–$9bc4. Two help pages add **1,024 reserved bytes at $c000–$c3ff** (1,018 bytes used for the default SAKU help). Text expands into the existing $8400–$87ff screen only on opening/page changes. No extra animation frames are stored.

**440 KiB ROM allocated; 584 KiB free**, unchanged from final v4: 80 KiB free ROML plus 504 KiB free ROMH. CRT headers/container bytes are separate. [Shared memory map](../../docs/STARFIELD.md) · [Exhibition design and CLI](../../docs/EXHIBITION.md).

## Historical SAKU results

| Build / selected field | Stars FPS | Off FPS |
| --- | ---: | ---: |
| First saved v0.7.9, original eight-point field | **15.97** | **18.25** |
| release_final_v1, 16-point field | 14.77 | **18.25** |
| release_final_v2, full with wider near stars | 13.70 | 18.18 |
| release_final_v3, light selected | 15.91 | 18.18 |
| release_final_v3, full selected | 13.70 | 18.18 |
| release_final_v4, light default | 15.91 | 18.18 |
| release_final_v4, full selected | 13.70 | 18.18 |
| release_final_v5, light default | 15.91 | 18.11 |
| release_final_v5, full selected | 13.70 | 18.11 |

Historical rows include artwork and control changes. Bold marks the highest rounded historical FPS, including ties. Use matched current-binary rows above for comparisons. [v4 evidence](../../docs/benchmarks/release-final-v4/saku.json) · [v5 evidence](../../docs/benchmarks/release-final-v5/saku.json).

## Reproduce

```bash
python examples/saku_2026/build.py --variants interactive
python examples/saku_2026/verify.py --vice x64sc --vice-data /usr/share/vice --install
python tools/verify_exhibition.py examples/saku_2026/cartridges/saku_2026-interactive.crt \
  --vice x64sc --vice-data /usr/share/vice --out /tmp/saku-exhibition
```

All eight presentations pass bitmap/colour checks. The exhibition GIF checks each displayed buffer against its source style and confirms sprites stay disabled. Native host-key tests cover both VICE symbolic/positional mappings, held keys, help pause, no random repeats, limits, reset and manual star/HUD persistence. These use VICE keyboard API events and its CIA matrix, not OS GUI event delivery. Physical hardware testing is not claimed.
