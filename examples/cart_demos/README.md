# c64-3d-toolkit 0.6.5 demo cartridge

The current cart is `c643d-demo-v0.6.5-yunroll-cart-v4-all.crt`.
All twelve demos use V4, including the horse head and sunflower HiFi models.

```bash
x64sc -cartcrt examples/cart_demos/c643d-demo-v0.6.5-yunroll-cart-v4-all.crt
./build.sh cart-demos --run
```

Cursor keys select; RETURN launches. Ten visible rows scroll between fixed
horizontal borders. A `+` at a border means more entries in that direction.
F1 cycles default/decorative/demoscene. During demos, F1 or RUN/STOP returns to
the menu; SPACE launches the next demo and wraps after the last entry.

0.6.5 fixes the CPU jam when launching from the animated-colour demoscene menu.
The loader disables the menu IRQ and restores the cartridge ROM mapping before
copying the animation. Renderer code, culling, colours and samples are unchanged.

`menu-launch-v4-validation.json` records the CRT hash and 84 VICE launch checks:
every demo from every style across two cycles, plus next-demo and wrap checks.
It verifies complete loaded payloads, the control shim and three rendered frames
per launch. `scroll-menu-validation.json` covers 75 navigation states. Physical
hardware has not been tested here.

Older menu carts and their historical reports are in `../old/cart_demos/`.
After applying the changed-files ZIP, run `python tools/archive_old_carts.py`
to move obsolete copies out of this folder. The command is repeatable and
preserves local edits. Explicit V2/V3 builds default to the archive folder;
`--output-dir` can override that for deliberate comparisons.

See [the V4 guide](../../docs/CARTRIDGE_STREAM_V4.md) and
[upgrade instructions](../../docs/UPGRADING_0.6.5.md).
