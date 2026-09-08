⚠️🐴 Attention! For best quality, please enjoy each animation with `hors-render-v1` or a newer variant.

The v0.7.1 menu cartridges are rebuilt for this release. Standalone object and
authored-scene cartridges are retained byte-for-byte from v0.7.0; their embedded
version labels and manifests remain their original build provenance.

Recommended for quality and FPS: the `hors-render-v1` cartridge linked below.

# 0.7.1 Horse and Sunflower

Current hors-render-v1 cartridges: [FPS preferred](horse_and_sunflower-hors-render-v1-scene.crt) and [RAM preferred](horse_and_sunflower-hors-render-v1-scene-ram.crt).

Both cartridges are 279,136 bytes and retain the 84-sample authored shot.
The FPS/RAM preference changes kernel size, not the source scene or requested
six-PAL-tick pacing. Actual playback depends on renderer cost; the original
V7 scene's timing must not be presented as a current hors-render-v1 measurement.

```bash
# Run from the repository root.
x64sc +easyflashcrtwrite -cartcrt examples/cart_horse_and_sunflower/horse_and_sunflower-hors-render-v1-scene.crt
```

See the [Blender source guide](../blender_horse_and_sunflower/README.md) and
[current scene build command](../../docs/CARTRIDGE_SCENES.md#current-scene-path-in-071).
The old `tools/build_horse_and_sunflower.py` remains a V7 reproduction helper.

Historical cartridges and metadata are outside the checkout. Renderer source and historical build tools remain available. These current cartridges are unchanged by the cleanup.

## Historical outputs removed

Obsolete cartridges and validation captures are outside this checkout in
`../c64-3d-toolkit-history/` (relative to the repository root). They are not
shipped examples. Run `python perf/prune_old_examples.py` to remove leftovers
from earlier patch extractions. Current source assets and renderer code remain.
