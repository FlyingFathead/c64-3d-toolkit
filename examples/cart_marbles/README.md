⚠️🐴 Attention! For best quality, please enjoy each animation with `hors-render-v1` or a newer variant.

Recommended for quality and FPS: the `hors-render-v1` cartridge linked below.

# DON’T LOSE YOUR MARBLES — 0.7.0

Current accepted presentation: [hors-render-v1, 16 FPS, force-bytes](marbles-hors-render-v1-16fps-force-bytes.crt).

640 integer-source samples cover the original 40-second Blender timeline.
PAL VICE measured 41.82 seconds for the scene; most of the extra time occurs
in the final five seconds. All 640 bitmap and colour frames passed verification;
this presentation was visually accepted. This is a documented timing compromise,
not a claim of exact 16 FPS throughout. Intro and ending are included; no HUD.
No equivalent HUD or RAM variant has been validated for this new sampling.

```bash
x64sc -cartcrt examples/cart_marbles/marbles-hors-render-v1-16fps-force-bytes.crt
```

The adjacent `.lbl` and `-manifest.json` are copied unchanged from the accepted
build. Run `python perf/cleanup_070_examples.py` after applying the cleanup patch
to install them from the existing `marbles-realtime-01` run. No Blender run needed.

Older presentation variants, reports and preview images are no longer in this repository.
Historical renderer implementations remain available. General automatic timing
selection remains unfinished; accepting this cart does not relax future builds.

The build screen waits indefinitely for SPACE before starting the intro. Start recording, focus VICE, then press SPACE.

## Historical outputs removed

Obsolete cartridges and validation captures are outside this checkout in
`../c64-3d-toolkit-history/` (relative to the repository root). They are not
shipped examples. Run `python perf/prune_old_examples.py` to remove leftovers
from earlier patch extractions. Current source assets and renderer code remain.
