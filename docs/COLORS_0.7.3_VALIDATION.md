# 0.7.3 colour controls: validation

No idle playback slowdown was measured against the uploaded 0.7.2 cartridges.
The complete sampled timing records are identical, including every observed
render-cycle cost and display interval, not just rounded FPS.

PAL VICE 3.10, fixed defaults/seed, normal PLAY ALL, three ten-second visits per
entry. Each old cartridge was rebuilt and matched the uploaded CRT's SHA-256
exactly before it was used as a baseline.

| Cartridge | Entries | Matched windows | Old displayed frames | New displayed frames | Timing records |
| --- | ---: | ---: | ---: | ---: | --- |
| demo1-fps | 12 | 36 | 8403 | 8403 | identical |
| demo1-ram | 12 | 36 | 8406 | 8406 | identical |
| demo2 | 7 | 21 | 5139 | 5139 | identical |

The two Demo Cart 1 preferences and Demo Cart 2.0 cover 31 animation/preference
rows and 93 observation windows per build. All source oracle bytes match.
Menu tests passed in all three styles; 2,897 completed pictures per build
matched their bitmap and colour references across every demo entry.

The idle/manual IRQ keyboard path measured 82 cycles before and after in 12
consecutive interrupt samples. The new scanner reuses the existing keyboard
reads: a two-cycle CMP replaces the two cycles saved by using the RUN/STOP
read's sign flag directly. No rendering-loop poll was added. The handler uses
the dead high-byte vector dispatch table in the direct-only v2 integration.
The machine code outside that unused page is unchanged in the renderer.

A longer experimental menu hint shifted startup phase and some measured
intervals, despite equal scanner cost. It was removed; the delivered menus
retain the original text/timing, with colour-key instructions in the guide.
The final comparisons below all use the corrected, shipped bytes.

## Colour behaviour

- CLI/config parsing and integration: 199 tests run, 3 skipped because optional
  historical archives are absent; all remaining tests passed.
- Dedicated COLOR COMBO TEST: 260 completed pictures, two automatic rounds,
  four presets, 96 key/hold/release checks, both shift keys, all three screen
  buffers and border-follow behaviour passed.
- Demo Cart 1 and Demo Cart 2.0: 416 key/hold checks across monochrome and
  multicolour entries. F3/F4 affect monochrome graphics only; F7 changes the
  border independently; F8 restores presets. Multicolour screen data is
  unchanged by these keys. Both shift keys and held-key handling passed.
- Independent CLI border: black-on-white cube with red border passed 19 frame
  checks. A source-coloured authored cube on light_gray with light_blue border
  passed 51 frame checks, covering all three buffers. A resident yunroll PRG
  also assembled with yellow foreground, blue background and purple border.

Applying a colour after an actual keypress takes a one-time screen update.
The idle comparison excludes keypresses. Measurements are from PAL emulation;
physical hardware and NTSC were not measured.

## Per-animation timing

Every old/new pair below has equal raw timing records. Display counts refer to
three visits; FPS uses the exact observed timer window.

| Cartridge | Animation | Old frames | New frames | Old FPS | New FPS | Worst display interval ms, both |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| demo1-fps | TORUS | 528 | 528 | 17.679555 | 17.679555 | 79.806303 |
| demo1-fps | TORUS DENSE | 513 | 513 | 17.179314 | 17.179314 | 79.806303 |
| demo1-fps | CUBE | 897 | 897 | 30.038919 | 30.038919 | 43.038910 |
| demo1-fps | SPHERE | 519 | 519 | 17.375998 | 17.375998 | 63.892543 |
| demo1-fps | HORSE HEAD | 876 | 876 | 29.331521 | 29.331521 | 42.608561 |
| demo1-fps | SUNFLOWER TORUS | 858 | 858 | 28.728704 | 28.728704 | 61.299287 |
| demo1-fps | SUNFLOWER COLOR | 624 | 624 | 20.892907 | 20.892907 | 63.105939 |
| demo1-fps | SPACE HORSE SPIN | 570 | 570 | 19.085086 | 19.085086 | 79.805288 |
| demo1-fps | SPACE HORSE CRAWL | 1143 | 1143 | 38.276431 | 38.276431 | 60.544147 |
| demo1-fps | FALLING CUBES | 624 | 624 | 20.891032 | 20.891032 | 61.967139 |
| demo1-fps | HORSE HEAD HIFI | 642 | 642 | 21.496253 | 21.496253 | 64.116852 |
| demo1-fps | SUNFLOWER TORUS HIFI | 609 | 609 | 20.393513 | 20.393513 | 62.080816 |
| demo1-ram | TORUS | 528 | 528 | 17.681906 | 17.681906 | 79.805288 |
| demo1-ram | TORUS DENSE | 513 | 513 | 17.176130 | 17.176130 | 79.806303 |
| demo1-ram | CUBE | 897 | 897 | 30.033777 | 30.033777 | 43.241905 |
| demo1-ram | SPHERE | 519 | 519 | 17.379823 | 17.379823 | 64.078283 |
| demo1-ram | HORSE HEAD | 876 | 876 | 29.332322 | 29.332322 | 42.307115 |
| demo1-ram | SUNFLOWER TORUS | 861 | 861 | 28.829833 | 28.829833 | 61.526641 |
| demo1-ram | SUNFLOWER COLOR | 624 | 624 | 20.892025 | 20.892025 | 62.827836 |
| demo1-ram | SPACE HORSE SPIN | 570 | 570 | 19.086019 | 19.086019 | 79.804273 |
| demo1-ram | SPACE HORSE CRAWL | 1143 | 1143 | 38.272923 | 38.272923 | 41.544870 |
| demo1-ram | FALLING CUBES | 624 | 624 | 20.893778 | 20.893778 | 62.335574 |
| demo1-ram | HORSE HEAD HIFI | 642 | 642 | 21.495045 | 21.495045 | 63.788001 |
| demo1-ram | SUNFLOWER TORUS HIFI | 609 | 609 | 20.391295 | 20.391295 | 62.221897 |
| demo2 | COLOUR CUBE 24 | 1062 | 1062 | 35.558209 | 35.558209 | 42.788212 |
| demo2 | COLOUR TORUS 18 | 597 | 597 | 19.991641 | 19.991641 | 62.587288 |
| demo2 | TWIST TUNNEL | 297 | 297 | 9.944161 | 9.944161 | 119.702857 |
| demo2 | RIBBON DANCE | 999 | 999 | 33.449759 | 33.449759 | 44.424348 |
| demo2 | ORBITAL CUBES | 939 | 939 | 31.447309 | 31.447309 | 44.086362 |
| demo2 | WAVE LATTICE | 741 | 741 | 24.809821 | 24.809821 | 63.071430 |
| demo2 | RIPPLES LITE | 504 | 504 | 16.877110 | 16.877110 | 79.803258 |

Raw reports, exact cart hashes, key checks and the cycle measurements are in [benchmarks/colors/](benchmarks/colors/).

The final full renderer comparison also passed all 26 jobs. The regenerated performance chart passes `python tools/compare_renderers.py --check`.
