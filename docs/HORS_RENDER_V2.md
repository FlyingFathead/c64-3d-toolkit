# hors-render-v2 — stable default in 0.7.2

Stable v2 uses the independently reproduced beta1 drawing kernel. `build`,
`cart-stream` and `cart-demos` select it by default. Object/OBJ/SVG spins,
authored `.c643dscene` / Blender inputs, menu carts, the HiFi reel and native
scene intros/endings are supported by the stable integration. Explicit v1,
beta1 and older names remain available with their original implementations.

Every frame uses independent literal bitmap spans and absolute colour metadata.
The compiler marks batch boundaries so the renderer can keep cartridge mapping
enabled across adjacent spans. It releases mapping at each marked boundary and
at the end of a picture. The former vector-dispatch page `$4F00–$4FFF` holds the
helper only when every frame uses this direct path. The helper adds no reserved
RAM allocation; this does not mean total RAM use is zero.

The stable encoder writes metadata without constructing an unused vector stream.
This extends host input handling without changing encoded bytes for beta-supported
pictures. It rejects metadata above 1 KiB, literal pictures above one 8 KiB bank,
and cartridges that exceed available EasyFlash capacity. It never drops samples,
geometry or colours. V1's vector fallback remains available through its explicit
name; stable v2 does not silently switch algorithms under its name.

## Default policies

| Build | Gap / batch budget | Purpose |
| --- | --- | --- |
| Normal object / authored-scene CLI | 6 / 2048 | General default, configurable with `--v2-draw-gap` / `--v2-batch-budget` |
| Twelve-demo comparison/menu | 3 / 2048 | Keep the original dataset within its cartridge allocation |
| Migrated standalone release examples | 3 / 2048 | Preserve complete shipped pictures and fit their existing capacity |
| Demo Cart 2.0 | Per-scene policy | Gap 6 on six scenes, gap 10 on Ripples Lite; budget 2048 |

The budget is a host cycle estimate, not a guaranteed interrupt-latency bound.
Pacing remains an explicit authored choice. Lowering a hold can increase display
rate and animation speed; reports distinguish this from faster rendering.

`tools/autotune_scene.py` freezes geometry, builds independent candidates and
measures actual display changes plus active stage costs. It prints a comparison
table and saves JSON, CSV, Markdown and logs. Only verified candidates are ranked.
No finite search proves the maximum possible performance on every input.

[Performance comparison](PERFORMANCE_COMPARISON.md) ·
[Showcase results](HORS_RENDER_V2_RESULTS.md) ·
[Compile a release](RELEASE_0.7.2.md)
