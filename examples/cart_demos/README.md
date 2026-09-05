# Cartridge demos

This directory contains runnable cartridge-image examples produced by the
experimental cartridge backend.

Build the current EasyFlash multi-animation demo with:

```bash
./build.sh cart-demos
```

The matching convenience flag is also available:

```bash
./build.sh --generate-cart-demos
```

Run it directly in VICE with:

```bash
./build.sh cart-demos --run
```

The final `.crt`, cartridge map, and manifest are written here by default.
Temporary assembler outputs, the raw 1 MiB EasyFlash image, and generated
includes stay under `build/`.

## `c643d-demo.crt`

The initial 0.6.3 demo cartridge is a deliberately simple integration bridge.
It packs the canonical toolkit PRG animations into EasyFlash ROM and boots a
small menu. Use the cursor keys to select an animation (up/left = previous,
down/right = next), RETURN to launch it, and F1 to cycle the live menu style
through `default` -> `decorative` -> `demoscene` -> `default`. While a demo is
running, F1 or RUN/STOP returns to the cartridge menu and SPACE launches the
next demo, wrapping back to the first entry after the last. The highlighted
entry and selected menu style survive the switch/return path. The ordinary
shipped PRGs are not modified; only their copies packed into this CRT receive
the cart-control IRQ shim.

This proves cartridge boot, bank switching, payload copying, and multi-demo
packaging. It is **not** yet the continuous `yunroll-cart` frame/table streaming
backend. That work is tracked in `docs/CARTRIDGE_ROADMAP.md`.

## Menu styles

Every demo CRT contains all three menu presentations. `--menu-style` chooses
which one appears at startup; F1 cycles them live without rebuilding the cart:

```bash
./build.sh cart-demos --menu-style default
./build.sh cart-demos --menu-style decorative --output c643d-demo-decorative
./build.sh cart-demos --menu-style demoscene --output c643d-demo-demoscene
```

`default` is the plain/readable utility menu. `decorative` adds a static frame,
colour treatment, and a menu-only compact 5x7 character set derived from the
toolkit HUD font. `demoscene` adds a small raster IRQ which slowly cycles the
header, footer, and border colours. The `--menu-style` flag therefore controls
only the initial presentation. All styles include:

```text
by FlyingFathead, 2026

github: flyingfathead/c64-3d-toolkit
```

Use `--output` when keeping differently configured/startup-style CRTs side by
side. Because every CRT contains all three styles, separate files are not
required merely to try the menu presentations.
