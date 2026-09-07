# c64-3d-toolkit demo cartridges

**v0.6.7 / yunroll-v7, FPS preferred by default:**

- [Play the FPS cartridge](c643d-demo-v0.6.7-yunroll-cart-v7-all.crt)
- [Optional RAM comparison](c643d-demo-v0.6.7-yunroll-cart-v7-all-ram.crt)

Both contain the same twelve animations, colours and samples. Horse and
Sunflower stays a [separate scene cartridge](../cart_horse_and_sunflower/README.md).

```bash
x64sc -pal -cartcrt examples/cart_demos/c643d-demo-v0.6.7-yunroll-cart-v7-all.crt
python tools/build_v7_examples.py
python tools/build_v7_examples.py --prefer ram
```

PLAY ALL is selected above the list at startup. RETURN starts an endless cycle,
10 seconds per animation after its first picture appears. SPACE skips; F1 or
RUN/STOP returns to the menu. Change duration with `--play-all-seconds N` (1..255).
The last demo is followed by a ten-second THANK YOU FOR WATCHING screen, then
the cycle restarts. F1 on that screen returns to the same menu style.

F1 in the menu cycles default, decorative and flashing demoscene/party styles.
Ten entries are visible at once. A `+` on the top or bottom border means more
entries in that direction. Individual demos keep looping until you leave them;
selecting one does not enable a timer. VICE may map Escape to native RUN/STOP.

## Files and measurements

Only the final FPS/RAM cartridges are kept at this level. Their manifests and
maps are in [metadata/](metadata/); final menu checks are in [reports/](reports/).
Historical benchmark evidence is in [docs/benchmarks/cart_demos/](../../docs/benchmarks/cart_demos/).
Old menu cartridges are in the separate oldies ZIP. Use
[the cleanup command](../../docs/UPGRADING_0.6.7.md) after applying an overlay.

Matched PAL VICE tests measured **0.2–14.6% higher throughput than V6**, preserving
pixels, colours and samples. CRT size is **804,448 bytes**, versus V6's 927,568.
`--prefer ram` saves 1,052 resident code bytes in the regular horse comparison,
with a measured FPS cost. See [the V7 guide](../../docs/CARTRIDGE_STREAM_V7.md).

The builder reads checksum-verified original V4 vector records from
`assets/v4-menu-vector-reference.json.gz`. It needs 64tass and cartconv, but no
Blender rebake or archived menu cartridge. `--reference-multi` still accepts an
archived V4 CRT and its matching manifest for explicit comparisons.
