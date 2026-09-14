# Interactive cartridge baseline: SAKU 2026

The released [SAKU 2026 interactive cartridge](../examples/saku_2026/README.md)
defines the shared controls. `tools/c643d/interactive_cart_baseline.py` composes
its existing control, speed, HUD, help, exhibition and starfield modules.
Demo Cart v3.1 uses that baseline with collection navigation. The previous
EasyFlash modules and cartridges are preserved.

Stars are included but **disabled by default**, including after F2 reset in
the collection. The original SAKU cartridge explicitly starts its light stars
and remains unchanged as an historical example. Shift+G explicitly enables
stars as part of SAKU's gradient presentation.

## Collection menu and help

Use CURSOR to select a demo, then **SPACE or RETURN (Enter)** to start it.
Shift+H opens two-page help directly from the menu. Left/right changes help
pages; SPACE or Shift+H closes help and returns to the same selection without
starting a demo. HUD and star controls are on the first page.

During playback, **RUN/STOP (Esc in VICE) or F1 returns to the collection menu**,
including from help, exhibition, hidden HUD and slow playback. STOP takes
priority over held speed keys. Shift+H opens/closes help; closing restores
all three buffers and their prior HUD state. The benchmark v3.0 front door
retains SPACE launch and automatic playback; it has no interactive help.

## Complete command map

| Key | Action |
| --- | --- |
| Shift+I | Toggle name and vertex/edge counts |
| Shift+F | Toggle FPS and speed text; speed controls still work |
| Shift+U | Hide all HUD text, including INTERACTIVE, or restore all |
| Shift+S | Toggle stars |
| 1 / 2 / 3 | Reset star density / more / fewer |
| 4 | Switch light/full star profiles; preserve each density and on/off state |
| + / − / 0 | Increase / decrease / reset playback speed |
| CURSOR or joystick 1/2 left/right | Playback direction |
| F2 | Reset presentation; stars off in the collection |
| F3 | Foreground/source palette |
| F4 | Background colour |
| F5 / F6 / F7 | Background colour cycle on/off / slower / faster |
| F8 / Ctrl+F7 | Black/follow border / independent border colour |
| 5 | Exhibition on/off |
| 6 | Sequential/random exhibition style order |
| 7 / 8 | Shorter/longer exhibition interval, 5–60 seconds |
| Shift+H | Open/close help |
| Left/right in help | Previous/next help page |
| SPACE in help | Close help |
| RUN/STOP (Esc in VICE), F1 | Collection menu |
| N / P | Next/previous collection demo |
| C | Cycle Dragon shade/wireframe |
| SAKU: Shift+T / Shift+W | Solid white presentation, stars off |
| SAKU: Shift+G | Gradient on black, stars on |
| SAKU: Shift+R | Spin/crawl |
| SAKU: Shift+B | White card/gradient |
| SAKU: Shift+O | Outline/gradient |

Even F-keys are Shift plus the preceding odd F-key on a C64 keyboard. SAKU's
presentation shortcuts require its authored presentation pictures; they do not
create absent variants for unrelated meshes. Exhibition starts with HUD/stars
off and preserves manual star choices across style changes.

## Build options

These CLI options already control standalone interactive builds:

```sh
python c643d.py build --shape torus --interactive-cart --starfield-default disabled
python c643d.py build --shape torus --interactive-cart --hide-hud --allow-hud-toggle
python c643d.py build --shape torus --interactive-cart --starfield-default enabled --starfield-profile light
python c643d.py build --shape torus --interactive-cart --no-starfield
```

`--starfield-default disabled` is the default; `--no-starfield` removes its code
and data. `--hide-hud` starts hidden; `--no-hud-toggle` fixes the chosen visibility.
The supplied v3.1 collection deliberately includes every baseline control and
starts with a visible HUD and disabled stars. Rebuild it with
`python examples/gmod3_cart_demos/build.py --variant interactive`.

## Runtime cost and verification

HUD visibility uses key-event clear/restore and patches drawing entry points
to RTS; it adds no visibility branch to the drawing loop. Help runs only when
opened. A small resident STOP check runs before speed-key handling, and the
raster IRQ latches STOP for foreground dispatch while preserving CIA column
selection. The IRQ never reloads the cartridge itself.

[A/B results for all 58 entries](INTERACTIVE_BASELINE_PERFORMANCE.md) quantify
the small input-service cost. Native VICE symbolic and positional keyboard
tests cover menu/help launch and close, HUD in all buffers, stars, speed,
exhibition and menu exit. The benchmark image remains byte-identical.

[Star implementation/options](STARFIELD.md) · [Exhibition](EXHIBITION.md) ·
[GMod3 details](GMOD3.md) · [v0.8.1 release](RELEASE_0.8.1.md)
