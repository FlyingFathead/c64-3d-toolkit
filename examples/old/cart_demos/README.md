# Archived demo cartridges

This folder preserves superseded menu carts and their original reports,
including the 0.6.4 V3/V4 comparison bundles. Released binaries are kept
byte-for-byte and may retain bugs fixed by later releases, including the
0.6.4 animated-menu launch bug. Paths inside historical reports describe the
original build locations.

Use `../../cart_demos/c643d-demo-v0.6.5-yunroll-cart-v4-all.crt` for the current
fixed demo. The normal `cart-demos` command builds V4 in that active folder.
Explicit V2/V3 builds default to this archive folder, with current menu source;
use a custom `--output` name if you want to preserve a previous comparison.

Run `python tools/archive_old_carts.py` after overlaying an update ZIP to move
the known old filenames out of the active folder. Local edits are preserved
with a content-hash suffix. The command is safe to repeat.
