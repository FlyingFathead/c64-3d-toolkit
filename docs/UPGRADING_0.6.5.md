# Upgrading to 0.6.5

This fixes `JAM at $0008` when launching an animation from the flashing
`demoscene` menu. It also makes V4 the only active demo cartridge and moves
older bundles and reports under `examples/old/cart_demos/`.

For an existing checkout, download the changed-files ZIP to `~/NeuralNetwork/`:

```bash
cd ~/NeuralNetwork/c64-3d-toolkit
unzip -o ../c64-3d-toolkit-v0.6.5-corrected-changed-files.zip
python tools/archive_old_carts.py
python c643d.py --version
x64sc -cartcrt examples/cart_demos/c643d-demo-v0.6.5-yunroll-cart-v4-all.crt
```

The version command prints `0.6.5`. Start the newly named CRT in VICE; an
already-running emulator still has the old cart loaded. No rebuild is required.
The full-repo ZIP contains a `c64-3d-toolkit/` directory with the cleaned layout.
Neither ZIP contains Git metadata, external tools or temporary build outputs.

The cleanup step matters: ZIP overlays do not remove obsolete paths. It moves
only known old bundle names and historical reports, preserves differing local
copies with a content-hash suffix, and is safe to repeat. Use `--dry-run` to
preview it. Existing 0.6.4 release assets remain preserved in the archive.

The V4 renderer and animation data are unchanged. The fix disables the menu
raster IRQ and restores `$01=$37` before copying cartridge ROM. The menu had
left `$01=$35`, making the loader read RAM instead of the intended ROM data.
Both menu loader sources are fixed; the current 0.6.5 V4 cart is rebuilt.

Verification includes every demo launched from all three styles across two
style cycles, next-demo wrapping, exact program/shim copies, and bitmap/colour
checks across all three buffers. The animated IRQ is allowed to run before
launch. The monitor enters real handler paths; it does not inject host keys.
See [the V4 guide](CARTRIDGE_STREAM_V4.md) and the shipped JSON reports.

## Corrected ZIP timestamps

The first 0.6.5 ZIP preserved old timestamps on modified files. Python could
reuse 0.6.4 bytecode when a source file kept the same byte length and timestamp.
The corrected ZIPs use fresh timestamps for modified files; unchanged files
retain their original timestamps. The CLI source, CRT and manifest were already
0.6.5; this corrects extraction over an existing Python cache.

If you already applied the first ZIP and see the stale CLI version, run:

```bash
find tools -type f -name '*.pyc' -delete
python c643d.py --version
```

The corrected package also updates Windows setup release labels and current
configuration/HiFi documentation to 0.6.5. Archived binaries, historical
changelog entries and PRG reference versions retain their original labels.
