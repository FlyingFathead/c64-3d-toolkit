# Don't Lose Your Marbles: Blender example

A separate early-beta example derived from the original falling-cubes scene.
The original asset is unchanged. The source timeline is 1,000 frames at 25 FPS
(40 seconds); the cartridge's complete story runs for about 58 seconds.

- `dont_lose_your_marbles.blend`: baked transforms, including the orbit and finale;
  ready to scrub or export without a physics cache.
- `dont_lose_your_marbles_physics.blend`: live rigid-body pours. Play sequentially
  from frame 1. The authored fracture/constellation finale is added by the
  generator after evaluating physics and appears in the baked file.
- `dont_lose_your_marbles.py`: deterministic generator (seed 6502), with optional
  `--seed` and `--output`. Run using Blender 4.x.
- `dont_lose_your_marbles.json`: schedule, colours and simulation audit.

Six alternating waves release 15 cubes and 30 marbles. Releases are centred
above the level tabletop, with heavier marbles and enough bounce to disturb the
cube pile. Queued objects use a separate collision collection until release;
otherwise moving a waiting object into the inlet can kick live bodies sideways.
All 45 bodies enter the tabletop/pile volume in this build. The audit measures
proximity, not an exact collision-contact count.

At source frame 851, the tabletop becomes 32 triangular-prism fragments.
Nearby bodies and fragments scatter, float outward and shrink into a camera-
tracked constellation. This finale is authored animation following the rigid-
body simulation. Fixed mesh topology is preserved throughout.

The original yellow/cyan/light-red/light-blue/gray palette is retained. Marbles
use 8-segment, 4-ring meshes. The camera completes one continuous 360-degree orbit.
Sampling every five source frames produces 200 cartridge samples; PAL playback
pacing and renderer load determine the actual running time.

The exporter recognises optional integer object properties `c643d_visible_start`
and `c643d_visible_end` (inclusive source frames). Outside that window, it keeps
the object's topology but parks its vertices off-screen in front of the camera
plane. This only hides waiting emitters and the exchanged table mesh; released
marbles have no timed removal and remain present until they leave the view or
are obscured by other geometry.

```bash
blender --background --python examples/blender_marbles/dont_lose_your_marbles.py
```

See [the scene cartridge guide](../../docs/CARTRIDGE_SCENES.md) for builds,
memory limits, timing, the native introduction and the finite ending.
