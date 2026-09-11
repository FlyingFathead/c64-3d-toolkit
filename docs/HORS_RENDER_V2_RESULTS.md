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

The alternate-VERSION gate also passed: temporary v1/v2 carts showed the manifest version on their startup screens, all menu styles and thanks screens. Root VERSION supplies Python and Windows setup identity.

The [main performance page](PERFORMANCE_COMPARISON.md) compares released renderer generations, including stable v2 FPS/RAM rows, and displays Demo Cart 2.0 in its own section. CUBE can still favour the resident yunroll renderer.

Release examples: **19 cartridges**, **49 picture checks**, **8,429 completed pictures**. Native Marbles ending, menu states and HiFi reel transitions also passed. The ending verifier acknowledges the SPACE build screen after reaching intro_start, before waiting for frame_begin.

The independent Linux beta run reproduced the earlier raw measurements and cartridge hashes. Stable results above are a new run after promotion, using the preserved beta drawing kernel. These checks measure emulated C64 time; physical C64 and NTSC are not measured.

V2 adds no reserved RAM to the drawing helper. Fixed graphics storage is 27,000 bytes and staging/metadata caches reserve 11,264 bytes. These components are not a total free-RAM figure. ROM and runtime sizes for each historical row are in the full chart.

Reproduce with `JOBS=3 bash COMPILE-RELEASE.sh --workspace ../c64-075-release-build`. Detailed JSON evidence is in `docs/benchmarks/hors-v2/`; full monitor traces remain in the external release workspace.
