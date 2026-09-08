⚠️🐴 Attention! For best quality, please enjoy each animation with `hors-render-v1` or a newer variant.

Recommended for quality and FPS: the `hors-render-v1` cartridge linked below.

# 0.7.1 demo menu

Current hors-render-v1 cartridges: [FPS preferred](c643d-demo-v0.7.1-hors-render-v1-all.crt) and [RAM preferred](c643d-demo-v0.7.1-hors-render-v1-all-ram.crt).

Each cart contains twelve animations rendered with hors-render-v1. Normal
PLAY ALL runs each for ten seconds by default. F5 is an exhibition mode with a
different schedule and must not be used for comparative FPS measurements.

```bash
# Run from the repository root.
x64sc +easyflashcrtwrite -cartcrt examples/cart_demos/c643d-demo-v0.7.1-hors-render-v1-all.crt

# Rebuild the menu with the current renderer.
./build.sh cart-demos
./build.sh cart-demos --prefer ram
```

| Context | Key | Action |
| --- | --- | --- |
| Menu | Cursor keys / RETURN | Select and launch an entry or PLAY ALL |
| Menu | F1 | Cycle menu style |
| Menu | F5 | Start exhibition playback |
| Animation | SPACE | Next demo |
| Animation | RUN/STOP or F1 | Return to menu |

Use [the performance chart](../../docs/PERFORMANCE_COMPARISON.md) for matched
results and [the build guide](../../docs/V10_TESTING.md) for validation.

Historical cartridges and metadata are outside the checkout. Renderer source and historical build tools remain available. These current cartridges are unchanged by the cleanup.

## Historical outputs removed

Obsolete cartridges and validation captures are outside this checkout in
`../c64-3d-toolkit-history/` (relative to the repository root). They are not
shipped examples. Run `python perf/prune_old_examples.py` to remove leftovers
from earlier patch extractions. Current source assets and renderer code remain.
