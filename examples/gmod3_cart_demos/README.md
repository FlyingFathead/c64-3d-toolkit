# Demo Cart v3.1: GMod3 All-in-One

Interactive v3.1 is built with HORS-V4 in toolkit v0.8.1. The automatic benchmark
edition remains the unchanged v3.0 image from v0.8.0. The
complete released picture inventory fits in a standard 16 MiB GMod3 image.

| Cartridge | Entries | Stored pictures | Used | Free |
| --- | ---: | ---: | ---: | ---: |
| [Interactive v3.1](demo-cart-v3.1-gmod3-all-in-one.crt) | 58 | 6,474 | 13,448 KiB | 2,936 KiB |
| [Benchmark](demo-cart-v3.0-gmod3-all-in-one-benchmark.crt) | 65 | 6,474 | 13,416 KiB | 2,968 KiB |

Includes the original twelve-demo collection, Demo Cart 2.0 scenes, all 640
Marbles pictures, SAKU 2026 presentations, six Stanford Dragon shading/wire
variants, Sande's Pretzel and TAC-2 variants, HiFi models, colour-combination
tests and Blender examples. Duplicate source cartridges with identical
pictures and pacing share entries. Different sample counts remain visible.
The manifests list every source cartridge and its SHA-256 provenance.

Use CURSOR to select an entry and SPACE or RETURN (Enter) to start.
Shift+H opens help directly from the menu; SPACE or Shift+H closes it without
launching a demo. Shift+CURSOR selects the
previous entry. The menu scrolls across four pages automatically. The bottom
two rows identify GMod3 and centre the allocated/free flash space. Stars start
**off**, including after a presentation reset.

| Key | Action |
| --- | --- |
| RUN/STOP (Esc in VICE) or F1 | Return to the collection menu |
| N / P | Next / previous demo |
| C | Next Dragon shade; wireframe is included in the cycle |
| CURSOR left/right or joystick 1/2 left/right | Change playback direction |
| + / − / 0 | Faster / slower / normal speed |
| F2 | Reset presentation; stars off |
| F3 / F4 | Foreground hue / background colour |
| F5 / F6 / F7 | Background colour cycle on/off / slower / faster |
| F8 / Ctrl+F7 | Black/follow border / independent border colour |
| Shift+H | Help; SPACE or Shift+H closes it; RUN/STOP returns to menu |
| Shift+S | Toggle stars |
| 1 / 2 / 3 / 4 | Reset / more / fewer stars / light-or-full star profile |
| Shift+I / Shift+F / Shift+U | Model information / FPS+speed / all HUD text |
| 5 / 6 / 7 / 8 | Exhibition / sequential-or-random / shorter-or-longer interval |
| SAKU: Shift+T or Shift+W | Solid on white, stars off |
| SAKU: Shift+G / Shift+R | Gradient with stars / spin-or-crawl |
| SAKU: Shift+B / Shift+O | White card / outline variants |

Even F-keys use Shift plus the preceding odd F-key on a C64 keyboard. Help has
two pages selected with left/right. Exhibition hides HUD/stars and restores
their previous state on exit; it is not the performance benchmark mode.

The benchmark CRT starts from the same SPACE menu, then automatically plays
every picture of each entry before advancing. It has no runtime input polling
or starfield. The last picture is displayed for its normal hold before loading
the next entry. SAKU's eight modes appear as eight individual benchmark entries.

```sh
python examples/gmod3_cart_demos/build.py --tass 64tass --cartconv cartconv
python c643d.py run-cart --cart-type gmod3 examples/gmod3_cart_demos/demo-cart-v3.1-gmod3-all-in-one.crt
```

The default builds only the v3.1 interactive image. Pass `--variant benchmark`
explicitly to rebuild the historical automatic image, or `--variant both` for both.
`--refresh-inventory` regenerates the read-only inventory from released source
manifests/oracles. Default tool paths can be absolute, including on Windows.
Keep the existing examples tree: it supplies the rebuild inputs. Generated
individual runtime files live under ignored `build/`, not this examples tree.

[Implementation and specifications](../../docs/GMOD3.md) ·
[Per-scene performance comparisons](../../docs/PERFORMANCE_COMPARISON.md)

[Complete shared interactive baseline](../../docs/INTERACTIVE_CART_BASELINE.md) ·
[Measured v3.0/v3.1 A/B performance](../../docs/INTERACTIVE_BASELINE_PERFORMANCE.md).
The [original v3.0 interactive image](demo-cart-v3.0-gmod3-all-in-one.crt) remains available for reproduction.
