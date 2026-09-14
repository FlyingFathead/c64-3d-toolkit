> Historical HORS-V3 / 0.7.9 checkpoint. Current defaults are HORS-V4 / GMod3; see [0.8.0](RELEASE_0.8.0.md).

# HORS-V3: measured results

HORS-V3 was introduced in v0.7.7: **Pretzel Logic - The Great Texture Update**. These measurements were rerun for **v0.7.9: The Golden Dragon & SAKU 2026**. The complete release gates rebuild the examples and repeat the PAL VICE measurements.

The new [Stanford Dragon example](../examples/stanford_dragon/README.md) demonstrates wireframe, metallic (grey), golden, red, green and blue shaded surfaces, with its own measured performance and timed GIFs. Select coloured shading with `--surface-fill metallic --surface-palette red|green|blue`; `--surface-fill grey` aliases metallic.

HORS-V3 is the normal build default. OBJ defaults remain wireframe; SVG defaults preserve mapped fills and strokes. Surface generation and colour compression use V3. The shared CLI selects V3 by default; older renderer implementations retain their functionality. Current example builds carry the new toolkit version; historical versioned cartridges remain available.

## Results

| Workload | Orientations | Displayed FPS | Frame stream bytes | CRT bytes |
| --- | ---: | ---: | ---: | ---: |
| V2 wireframe, white | 128 | 17.96 | 261,277 | 344,800 |
| V3 wireframe, white | 128 | 17.96 | 261,277 | 344,800 |
| V3 MTL flat fill | 128 | 18.26 | 257,470 | 336,592 |
| V3 metallic, B/W dither | 128 | 18.46 | 252,089 | 328,384 |
| V2 kernel, same metallic pictures | 128 | 10.73 | 332,248 | 451,504 |
| V3 metallic, direct colours | 128 | 14.70 | 296,092 | 377,632 |
| V3 MTL image texture | 128 | 14.70 | 296,344 | 377,632 |
| V3 metallic, compact dictionary | 128 | 12.46 | 274,460 | 361,216 |
| V3 metallic, interactive | 128 | 14.16 | 296,092 | 377,632 |
| V3 compact, interactive | 128 | 12.10 | 274,460 | 361,216 |
| V3 metallic, compact / 192 | 192 | 12.46 | 411,701 | 517,168 |

![Measured FPS and frame-stream storage](benchmarks/hors-v3-preview/performance.png)

The direct-colour V3 metallic animation changes displayed throughput by **+37.0%** against identical metallic pictures through V2, with **-10.9%** frame-stream ROM. Compared with the differently rendered white wireframe, its displayed FPS changes by **-18.2%**.

`--compact-color-dictionary` changes metallic frame-stream size by **-7.3%** and displayed throughput by **-15.2%**. Direct bytes remain the speed default. Compact remains an explicit capacity option; no geometry or sample reduction is automatic.

Plain MTL fill is one uniform dark grey and needs no per-frame colour stream. The dither preset uses only black and white. Both happen to be slightly faster than this wireframe because their packed bitmap drawing streams are favourable. This result is specific to this mesh, projection and encoder; it does not establish that filled meshes are generally faster.

The texture row uses a synthetic planar-UV derivative of the original mesh and a four-grey test image. It demonstrates `map_Kd` support, not a texture supplied by Sande. Texture complexity and colour-cell coverage can materially change the storage and playback results.

## Measurement and correctness

All measurements use PAL VICE 3.10, 985,248 CPU cycles/second, FPS preference, an unpaced looping cartridge and a **1,504-refresh observation window** after warm-up. FPS counts actual display-buffer flips. The separate verifier's `average_fps` describes producer completion and is not used in the chart. Instantaneous HUD values in screenshots may differ from the window average.

The 128-orientation comparisons use the same full 1,552-vertex, 1,552-quad mesh, triangulated into 3,104 triangles. Camera distance 110, focal length 180, Y rotation, fit margin 4, maximum fit scale 1.4, actual fit scale 0.9548340649786405, a 256×192 model viewport and the standard bottom HUD. No animation pacing or mesh simplification is introduced.

Every variant passed independent expected-bitmap and colour checks across all three buffers: **259 completed pictures per 128-orientation cartridge**, and **387 for the 192-orientation cartridge**. The display windows also covered every orientation and checked bitmap, colours and HUD. Release measurements are repeated against the rebuilt cartridges and recorded with their SHA-256 hashes.

The public compact CLI was rebuilt end to end and exactly matched the benchmarked CRT SHA256. Focused surface/texture, palette, SVG, speed and compatibility tests are included in the release suite. The complete release suite additionally checks the historical renderers; see `docs/benchmarks/release-0.7.9/`. Real hardware is not tested.

## Interactive metallic cartridges

Both direct and compact metallic variants have separate `-interactive` cartridges. They retain the full precomputed surface colours, use cursor left/right or either joystick port to select persistent rotation direction, and show `INTERACTIVE` at the top right in the HUD font. Both C64 Shift keys work for left. Releasing a direction keeps it; opposed joystick directions leave it unchanged. Input is polled once per produced picture, so a queued picture may display before the new direction takes effect.

F4 cycles the background, F5 toggles automatic background cycling, and F6/F7 decrease/increase its speed. Only original black colour nibbles are replaced; the metallic greys and white remain unchanged. Black pixels inside an imported texture are also replaced. F8 toggles a persistent black border versus following the background; Ctrl+F7 advances an independent border colour. F2 briefly flashes white, resets the background to black, restores border following, stops cycling and restores the default rate. F3 has no action in these original surface carts; the SAKU presentation cart uses it for hue overlays. All new V3 interactive carts add + / - / 0 speed controls and brief SPD feedback; see [controls and RAM](STARFIELD.md). The original V2 controls are unchanged.

Direct metallic interactive measures **14.16 FPS** versus **14.70 FPS** automatic (-3.6%). Compact interactive measures **12.10 FPS** versus **12.46 FPS** (-2.9%). Controls add no frame-stream payload. Background remapping uses a 256-byte lookup at $0200; shared speed controls use RAM at $9000. Border/background registers follow the displayed buffer, including queued pictures.

Each interactive variant additionally passed **562 completed pictures** with reverse traversal, forward/reverse wraparound and repeated direction changes, plus **20 direction input-path checks**, **47 background-control input checks** and **272 palette-changing pictures**. Every palette colour, all 256 lookup values, the bottom HUD background, persistent border modes and the five-tick reset flash were checked. Bitmap and colour data were checked in all three buffers. Input tests inject CIA read results in the VICE monitor; physical controllers and host key mappings were not tested.


### Background controls and performance

| Background mode | Direct FPS | Compact FPS |
| --- | ---: | ---: |
| Black, cycling off | 14.16 | 12.10 |
| Blue, cycling off | 13.70 | 12.10 |
| Automatic, 50 ticks | 13.43 | 11.86 |
| Automatic, 1 tick | 12.40 | 11.03 |

![Background-control performance](benchmarks/hors-v3-preview/background-performance.png)

The default cycle interval is 50 PAL ticks; the fastest setting requests one tick but performs at most one event per produced sample. Raw background reports record the observed periods. Every sampled displayed picture is checked against the original bitmap and its black-only colour remap.

Current interactive results include help, shared + / - / 0 speed controls at normal speed, HUD switches, and the included-but-disabled starfield. Shift+I / Shift+F / Shift+U toggle the name/counts, FPS/speed messages, or both; `--hide-hud` selects a hidden startup and `--no-hud-toggle` omits switches. Historical results remain in their release records; the table above comes from the current rebuilt carts.

## What the colour dictionary does

The metallic animation needs only ten distinct **colour-pair bytes**. One byte normally holds a cell's two C64 colour nibbles. The optional dictionary maps a four-bit index to that complete byte: two cells' indices fit in one byte, with a ten-byte shared dictionary.

V3 identifies the union of cells whose colour can differ from the global base. This example has **338 cells** in **22 address runs**. Addresses are shared across the animation in a 66-byte table. Direct mode sends 338 ready-to-store colour bytes per picture; compact sends 169 bytes of indices. Both write the complete union, including values that return to the base, so the renderer never depends on which old picture occupied a reused buffer. The old colour erase pass can be omitted.

The noninteractive colour codec reuses the vector dispatch allocation. Interactive builds reserve a 256-byte colour lookup, 2 KiB for speed controls, and 2 KiB for help code/text plus 1 KiB at $c000–$c3ff for the packed help pages. Exhibition reuses spare HUD/help code space. The included starfield reuses $1700–$1fff and adds 192 sprite-pattern bytes; it starts disabled unless explicitly enabled. --no-starfield excludes it. Existing frame/cache RAM is 11,264 bytes, plus seven directory bytes per orientation. CRT size includes bootstrap code and bank padding. See [the complete memory map and controls](STARFIELD.md).

Indexed mode requires at most 16 distinct pair bytes and a fitting shared address plan. It rejects inputs which exceed those limits. Direct mode has an absolute-colour-run fallback when a shared address plan will not fit. These are picture-independent absolute encodings, not temporal delta compression.

## Materials, shading and image limits

Sande's original Pretzel binds opaque `Default` material to its faces. The last of the repeated definitions supplies `Kd 0.2 0.2 0.2`, which the existing importer maps to dark grey. It has no OBJ UV coordinates and no image map. MTL describes face materials; it does not ask a renderer to fill or wireframe them.

`material` fills faces with their imported Kd colours. `metallic` is a new stylised flat-lighting preset using dark grey, grey, light grey and white; it is not a physically based metal shader. `textured` samples OBJ UVs and MTL `map_Kd`, multiplies RGB by Kd, and uses the existing nearest-C64-colour mapper. It supports nearest sampling, repeat/clamp, `-s` scale, `-o` offset and quoted filenames. Perspective correction, visibility and lighting are baked on the host; the C64 draws precomputed bitmap streams, not live triangles or image samples.

The native hires mode can show only **two colours per 8×8 cell**. The host chooses a best-fitting pair and preserves black at silhouette cells, so fine texture or shade boundaries can exhibit colour clash. Metallic `--surface-encoding dither` avoids per-cell colour updates using an ordered black/white pattern. Textures require faces with UVs; opaque diffuse image maps are supported, while alpha, bump/normal/displacement maps and PBR materials are not.

## Reproduce and inspect

- [Build commands and preset list](../examples/hors_v3_preview/README.md)
- [Exact settings and hashes](benchmarks/hors-v3-preview/summary.json)
- [Capacity check](benchmarks/hors-v3-preview/capacity-192.json)
- [Raw VICE results](benchmarks/hors-v3-preview/results/)
- [Independent source picture oracles](benchmarks/hors-v3-preview/oracles/)
- [Exportable SVG chart](benchmarks/hors-v3-preview/performance.svg)

```sh
python tools/run_hors_v3_perfs.py --check
python tools/build_hors_v3_examples.py --tass /path/to/64tass --cartconv /path/to/cartconv
python tools/run_hors_v3_perfs.py --run --vice /path/to/x64sc --vice-data /path/to/vice-data --cartridge-dir build/hors-v3-preview
```

The release runner integrates these measurements into `compare_renderers.py` before running the complete canonical matrix. Both `python tools/compare_renderers.py --check` and `python tools/run_hors_v3_perfs.py --check` must pass for the shipped release.
