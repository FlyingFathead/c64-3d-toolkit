# c64-3d-toolkit 0.7.4

Cartridge loading update, prepared 2026-09-11 against 0.7.3 commit
`78b197d38b3ffd6adf06f92d007a9487dd0050d5`. The supplied working-directory
snapshot matched that commit byte for byte.

## Changes

- One VICE launcher for cartridge build commands and the new `run-cart` command.
  It disables CRT write-back and automatic settings saving. PAL, windowed and
  Warp-off defaults can be overridden for diagnostics.
- `--vice-clean-settings` temporarily uses VICE defaults without rewriting the
  user's saved settings.
- Genuine AM/M29F040 V1.4 EasyAPI and a PETSCII cartridge-name structure in the
  standard bank 0 ROMH positions. The original driver source and license are
  included in `tools/c643d/data/easyapi/`.
- Guarded metadata placement and scene-content relocation preserve the scene's
  runtime data, graphics and frame-bank addresses.
- Reset code shuts down CIA interrupt/timer sources and acknowledges VIC IRQs
  before copying the loader. Historical renderer kernels remain unchanged.
- Direct CRT byte validation checks container identity, CHIP packets and reset
  vectors. New builds also require the real EAPI and name metadata.
- Current examples are rebuilt with 0.7.4 identity. Demo Cart 2 and the HiFi reel
  have their own descriptive container names.

This is a patch release. The default renderer remains `hors-render-v2` and the
colour controls introduced in 0.7.3 remain available.

## Install

Save `c64-3d-toolkit-v0.7.4.zip` in the parent of your existing checkout.
Run these commands from that parent:

```bash
unzip -o c64-3d-toolkit-v0.7.4.zip
cd c64-3d-toolkit
cat VERSION
python tools/compare_renderers.py --check
python -m unittest discover -s tests -q
```

`VERSION` should print `0.7.4`. The archive contains a top-level
`c64-3d-toolkit/` directory and does not contain Git metadata. No rebuild is
needed to try the supplied cartridges. Existing older versioned menu and HiFi
cartridges are retained unchanged as historical references.

```bash
python c643d.py run-cart examples/cart_demos/c643d-demo-v0.7.4-hors-render-v2-all.crt
python c643d.py run-cart examples/cart_demos_v2/demo-cart-2-preview-hors-v2.crt
```

Add `--vice-clean-settings` for temporary factory settings. See
[cartridge loading](CARTRIDGE_LOADING.md) for standalone VICE commands and the
memory layout. [The release index](../examples/release-index.json) lists the
current verified cartridge and metadata checksums.

## Validation and limits

The initial loading patch passed 208 Python tests with three optional skips,
all 26 canonical renderer comparison jobs, Warp on/off startup checks, menu
states, scene playback and the complete Marbles ending. The comparison's FPS
tables matched 0.7.3; one historical scene's maximum interval was two CPU cycles
shorter. Marbles' scene duration and ending images matched exactly.

The final 0.7.4 build and comparison results are recorded in
[cartridge-loading validation](CARTRIDGE_LOADING_VALIDATION.md).

Tests use PAL Linux VICE 3.10. The reported VICE 3.10 Win64 GUI sequence that
produced `Main CPU: JAM at $F800` after toggling Warp has not been reproduced
here. This release fixes confirmed loading gaps; it does not establish that
specific failure's cause. Physical EasyFlash hardware has not been tested.

## Rebuild

From the repository root, with 64tass and VICE/cartconv installed:

```bash
JOBS=3 VICE_DATA=/usr/local/share/vice bash COMPILE-RELEASE.sh \
  --workspace ../c64-074-release-build
```

Choose a new external workspace. This rebuilds and verifies examples, picture
output, endings, menus, colour controls, version labels, renderer boundaries and
the complete performance comparison. It never commits, tags or pushes.
