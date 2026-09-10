# hors-render-v2 release results

Stable v2, PAL VICE, normal PLAY ALL: three ten-second visits per entry. Changes rank displayed-frame counts; all methods use matching complete pictures and colours. Peak interval FPS is not sustained throughput. F5 is excluded.

| New menu scene | v1 FPS | v2 FPS | Change |
| --- | ---: | ---: | ---: |
| COLOUR CUBE 24 | 32.45 | 35.56 | +9.60% |
| COLOUR TORUS 18 | 18.38 | 19.99 | +8.74% |
| TWIST TUNNEL | 9.14 | 9.94 | +8.79% |
| RIBBON DANCE | 31.64 | 33.45 | +5.71% |
| ORBITAL CUBES | 28.73 | 31.45 | +9.44% |
| WAVE LATTICE | 22.00 | 24.81 | +12.79% |
| RIPPLES LITE | 12.46 | 16.88 | +35.48% |

Normal PLAY ALL, three visits at ten seconds each. New Demo Cart 2.0 material; not the original release matrix. Change uses display counts to avoid ranking timer-phase noise.

## HiFi comparison against hors-render-v1

Same 128 source samples, FPS preference, three normal PLAY ALL visits per animation. Gains are based on displayed-frame counts; tiny timer-phase differences are not ranked.

| Animation | v1 FPS | v2 FPS | Gain | v1 worst display interval | v2 worst display interval |
| --- | ---: | ---: | ---: | ---: | ---: |
| HORSE HEAD HIFI | 20.69 | 21.50 | +3.88% | 63.81 ms | 63.95 ms |
| SUNFLOWER TORUS HIFI | 19.89 | 20.39 | +2.53% | 79.80 ms | 62.58 ms |

Horse Head displayed 618 → 642 pictures and Sunflower Torus 594 → 609 across roughly 29.86 measured seconds each. All picture/colour checks passed. Sunflower Torus also had a shorter worst observed display interval; Horse Head’s worst interval was essentially unchanged. These extrema describe this measured window, not a guarantee for arbitrary scenes.

The alternate-VERSION gate also passed: temporary v1/v2 carts showed the manifest version on their startup screens, all menu styles and thanks screens. Root VERSION supplies Python and Windows setup identity.

The [main performance page](PERFORMANCE_COMPARISON.md) compares released renderer generations, including stable v2 FPS/RAM rows, and displays [Demo Cart 2.0 in its own section](PERFORMANCE_COMPARISON.md#demo-cart-20). CUBE can still favour the resident yunroll renderer.

Release examples: **19 cartridges**, **49 picture checks**, **8,429 completed pictures**. Native Marbles ending, menu states and HiFi reel transitions also passed. The ending verifier acknowledges the SPACE build screen after reaching intro_start, before waiting for frame_begin.

The independent Linux beta run reproduced the earlier raw measurements and cartridge hashes. Stable results above are a new run after promotion, using the preserved beta drawing kernel. These checks measure emulated C64 time; physical C64 and NTSC are not measured.

V2 adds no reserved RAM to the drawing helper. Fixed graphics storage is 27,000 bytes and staging/metadata caches reserve 11,264 bytes. These components are not a total free-RAM figure. ROM and runtime sizes for each historical row are in the full chart.

Reproduce with `JOBS=3 bash COMPILE-RELEASE.sh --workspace ../c64-072-release-build`. Detailed JSON evidence is in `docs/benchmarks/hors-v2/`; full monitor traces remain in the external release workspace.
