# c64-3d-toolkit 0.6.4 comparison cartridges

Both cartridges contain the same twelve demos, using one renderer throughout:

- `c643d-demo-v0.6.4-yunroll-cart-v4-all.crt`: current default, all V4.
- `c643d-demo-v0.6.4-yunroll-cart-v3-all.crt`: comparison baseline, all V3.

```bash
x64sc -cartcrt examples/cart_demos/c643d-demo-v0.6.4-yunroll-cart-v4-all.crt
./build.sh cart-demos
./build.sh cart-demos --stream-renderer yunroll-cart-v3
```

Cursor keys select; RETURN launches. Ten visible rows scroll between fixed
horizontal borders. A `+` at a border means more entries in that direction.
F1 cycles default/decorative/demoscene. During demos, F1 or RUN/STOP returns to
the menu; SPACE launches the next demo and wraps after the last entry.

The ten canonical PRGs retain their original samples through exact vector-table
extraction. Each HiFi model uses 128 orientations. Both carts use the same frame
bytes and ROM allocation. All entries passed pixel/colour comparisons in PAL
VICE over more than two complete rotations. The JSON reports record per-demo
FPS, scrolling, controls and boundary checks. Physical C64 testing remains open.

See [the V4 guide](../../docs/CARTRIDGE_STREAM_V4.md) for measurements, layout and
verification commands. Standalone 192-frame HiFi carts remain in `../hifi_showcase/`.

Superseded mixed-method carts are in `../old/cart_demos/`. After applying the
changed-files ZIP, run `python tools/archive_old_carts.py` from the repo to move
old copies out of this folder. `--dry-run` previews the moves. Modified local
files get a content-hash suffix; custom cart names are untouched.
