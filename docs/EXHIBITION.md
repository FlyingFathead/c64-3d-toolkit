# Interactive exhibition mode

HORS-V4 / GMod3 retains these V3 controls. The [All-in-One collection](../examples/gmod3_cart_demos/README.md) starts with stars off and adds F1 menu, N/P entry selection and C Dragon shading. Older EasyFlash cartridges retain their original keymaps.


HORS-V3 interactive cartridges include two-page help and exhibition controls. Use RUN/STOP (Esc in the supplied VICE keymaps) or Shift+H to open help. Cursor right selects page 2; cursor left selects page 1. On a C64, left is Shift+cursor-right. The top-right page indicator shows the available direction. Help pauses playback and the exhibition timer; closing it restores the display. Opening help from the original intro returns to the intro, which still requires SPACE to start.

| Key | Action |
| --- | --- |
| 5 | Exhibition on/off |
| 6 | Sequential/random selection; restart the current interval |
| 7 | Decrease interval by 5 seconds, minimum 5 |
| 8 | Increase interval by 5 seconds, maximum 60 |
| Shift+S | Toggle stars while exhibition continues |
| 1 / 2 / 3 | Reset/increase/decrease the selected starfield density |
| 4 | Select light/full stars, retaining their separate densities |
| Shift+U | Show/hide all HUD text, including INTERACTIVE |
| F2 | Leave exhibition and restore the cart's presentation defaults |

Exhibition is initially disabled. Turning it on hides HUD and stars once. Subsequent scene changes preserve manual star on/off, profile and density choices, and any manual HUD choice. Turning it off restores the HUD visibility and star on/off states from entry; the selected profile and densities remain. Existing explicit presentation presets retain their normal actions: Shift+G enables stars, while Shift+T/W disables them.

Sequential is the default order, with one change every **5 seconds**. Random selects another compiled style without immediately repeating the current one. It uses a small 8-bit LFSR; the distribution is not guaranteed uniform. Interval changes display `AUTO TIME INCREASED/DECREASED TO NN SECS` briefly above the bottom HUD, even when that HUD is hidden. F2 restores the CLI-selected interval and order and leaves exhibition off.

SAKU cycles **solid outlined**, **gradient**, and **rounded white-card** styles. The first change advances from the current style; the normal gradient startup therefore advances to the white card. Axis spin or crawl stays selected across changes. Original colours and background choices are restored for each selected style. The underlying eight SAKU presentations remain accessible through their original keys.

A cart can cycle only styles actually compiled into it. A generic cart containing one animation continues that animation; exhibition does not synthesize extra scenes or silently add frame streams. Multi-style SVG carts use their compiled solid/gradient and optional card/outline variants. The same shared controls apply when stars are excluded.

## CLI

```bash
# Normal interactive startup: HUD shown, stars off, exhibition off.
python c643d.py build --shape cube --interactive-cart

# Exhibition after the normal SPACE intro, in random order every ten seconds.
python c643d.py build --svg artwork.svg --interactive-cart \
  --exhibition-default enabled --exhibition-order random --exhibition-interval 10

# Ordinary interactive startup with light stars enabled explicitly.
python c643d.py build --shape cube --interactive-cart \
  --starfield-default enabled --starfield-profile light

# Remove starfield code/data; help, exhibition and speed controls remain.
python c643d.py build --shape cube --interactive-cart --no-starfield
```

| Option | Values | Default |
| --- | --- | --- |
| `--exhibition-default` | enabled / disabled | disabled |
| `--exhibition-order` | sequential / random | sequential |
| `--exhibition-interval` | 5, 10, …, 60 seconds | 5 |
| `--starfield-default` | enabled / disabled | disabled |
| `--starfield-profile` | light / full | full |
| `--show-hud` / `--hide-hud` | initial visibility | shown |
| `--hud-default` | enabled / disabled | initial visibility above |
| `--allow-hud-toggle` / `--no-hud-toggle` | include/omit manual HUD shortcuts | included |

`--default-info-text-mode` aliases `--hud-default`; `--no-include-starfield` aliases `--no-starfield`. Exhibition options require a standalone HORS-V3 interactive build. Selecting exhibition startup overrides HUD/star startup visibility to off, while retaining those values for exhibition exit. SAKU's recipe explicitly enables the light field for ordinary startup; other carts remain off unless the user enables them.

## Cost and memory

The inactive scheduler uses the original raster routine's RTS: **zero additional inactive IRQ instructions**. Two CIA rows for keys 5–8 add **67 CPU cycles per idle input poll**, not per pixel or edge. Active exhibition uses byte-sized raster-tick/second counters; a pending change is serviced only at the producer's safe input boundary. This can delay the visible switch until the next finished frame. Help pauses the clock. Intervals use 50 PAL refreshes per nominal second, independent of renderer FPS and rotation speed.

The event handlers and scheduler occupy spare space in the existing speed/HUD and help reservations. Packed two-page text adds **1,024 bytes at $c000–$c3ff**; the existing $8400–$87ff text screen is expanded only on help entry or a page change. Exhibition adds no animation frames. SAKU still allocates **440 KiB ROM with 584 KiB free**. Manifest fields and assembler bounds checks record and protect the actual layout.

See [SAKU's measured scheduler and starfield results](../examples/saku_2026/PERFORMANCE.md), [all renderer comparisons](PERFORMANCE_COMPARISON.md), and the [starfield RAM map](STARFIELD.md). Measurements use PAL VICE, not physical hardware.
