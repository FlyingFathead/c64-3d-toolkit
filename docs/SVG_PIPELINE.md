# SVG artwork in HORS-V3

`build --svg artwork.svg` uses HORS-V3 by default. It preserves the painted
fills **and strokes**, holes, proportions and local transforms, fits the whole
rotation inside the viewport, and maps source paint to the nearest C64 colour.
Painted canvas rectangles are retained; transparent page margins are cropped.
No geometry or animation samples are silently reduced to make a cart fit.

```bash
python c643d.py build --svg artwork.svg
python c643d.py build --svg artwork.svg --fill-style gradient
python c643d.py build --svg artwork.svg --svg-outlines-only
python c643d.py build --svg artwork.svg --svg-no-colors
python c643d.py build --svg artwork.svg --svg-override-with-color cyan
python c643d.py build --svg artwork.svg --svg-override-with-color yellow --fill-style gradient
```

| Option | Behaviour |
| --- | --- |
| Default / `--fill-style solid` | Preserve mapped source fills and strokes |
| `--fill-style gradient` | Nearest source colour selects its Dragon-style lighting ramp |
| `--svg-outlines-only` | Ignore fills, retain mapped strokes; fill-only shapes receive white one-unit contours |
| `--svg-no-colors` | Solid white artwork on black, including outlines; holes remain transparent |
| `--svg-override-with-color COLOR` | One flat colour for all paint; combine with an explicit gradient style to shade that hue |
| `--fill-style wireframe` | Historical simplified vector/extrusion importer |
| `--fill-style textured --surface-texture IMAGE` | Map an image over the SVG silhouette |
| `--fill-style metallic --surface-palette gold` | Use one lighting family throughout the artwork |
| `--surface-ramp brown,orange,yellow,white` | Custom dark-to-light metallic ramp; use with metallic style |
| `--include-svg-background-color true` | Keep painted canvas rectangles (default); accepts true/false, yes/no, on/off, 1/0 |
| `--include-svg-background-color false` / `--svg-drop-background` | Remove direct, untransformed full-canvas rectangles, including 100% width/height; no guesswork on arbitrary background shapes |
| `--svg-depth 0` | Flat, two-sided artwork; default depth is 5 toolkit units |
| `--svg-texture-size 1024` | Host paint resolution, longest side; default 512, range 16–2048 |
| `--svg-alpha-threshold 128` | Binary geometry coverage threshold, 1–255 |
| `--margin 4` | Viewport fitting margin; `--max-fit-scale` optionally caps enlargement |

`--no-svg-color-mapping` aliases `--svg-no-colors`.
`--override-svg-color` aliases `--svg-override-with-color`.
Colours accept C64 names/indices and the usual RGB notation. RGB overrides are
also mapped to the fixed palette. Black source paint stays black in solid mode;
choose a contrasting background when necessary. The black family's gradient
uses neutral grey shades, making it visible against black space.

The gradient style uses the same flat lighting model and hue ramps as the
[Stanford Dragon](../examples/stanford_dragon/README.md). It changes the lighting
of each source colour; it does not replace all source colours with one hue.
SVG-authored gradients/patterns are painted before palette reduction, so they
also work with solid style. Source and final cell mapping use the same weighted
CIELAB distance (half-weighted squared L, plus squared a and b).

## Host dependencies and fidelity

```bash
python -m pip install -r requirements-svg.txt
```

CairoSVG requires the Cairo library. On Ubuntu, install `libcairo2`; on Windows,
install a Cairo runtime as described by [CairoSVG](https://cairosvg.org/documentation/)
and make its DLLs available to Python. The wireframe importer does not need
CairoSVG. PyMuPDF is needed only to reproduce the supplied SAKU PDF extraction.

The host paints SVG through CairoSVG, then builds disjoint rectangles and
boundary walls from the alpha mask. This preserves concave shapes and holes
without filling them with triangle fans. Source vector art remains included;
the cartridge itself receives precomputed bitmap and colour spans.

This is a C64 interpretation, with explicit limits: 256×192 model viewport,
16 palette colours, two colours per 8×8 hires cell, and binary transparency.
Partial opacity is composited on black before matching. Features smaller than a
screen pixel can disappear as they rotate. A larger host texture can improve
sampling but cannot remove these VIC-II limits. Antialiasing at paint boundaries
can introduce intermediate mapped colours.

CairoSVG handles common SVG paths, CSS paint, strokes, gradients, clips, and
local/embedded images. It has [documented SVG support limits](https://cairosvg.org/svg_support/).
Filters, scripts, foreignObject and animation are rejected by this static
importer. Outline-only mode requires vector shapes. Text uses installed fonts;
convert lettering to paths for portable results. Remote resources must first be
downloaded or embedded. Missing resources fail the build. Resource hashes,
paint resolution, warnings, crop, palette histogram and geometry counts are
recorded in `*-surface.json`.

## Interactive logo presentations

```bash
python c643d.py build --svg artwork.svg --fill-style gradient \
  --frames 48 --interactive-cart --svg-presentation-modes \
  --background-effect starfield-forward
```

This packs solid-spin, gradient-spin, solid-crawl and gradient-crawl into one
cart, starting with gradient spin. There are 1–63 samples per mode; ROM capacity
is checked without silently dropping samples. `--svg-background-card card.svg` adds a solid white-card spin/crawl pair, and `--svg-outline-variant outlined.svg` supplies the gradient artwork plus a solid outlined spin/crawl pair. Six modes allow up to 42 samples each; eight allow 31. SAKU explicitly uses 30, with all eight looks in one cart. Card sources retain their painted backgrounds, and only the transparent outlined source receives white contours. Shift+B selects the card and Shift+O selects solid outlines; Shift+R preserves the selected look while changing motion.

See the complete
[SAKU keyboard map](../examples/saku_2026/README.md) and
[starfield implementation](STARFIELD.md). The SAKU source has transparent page
space already removed, original black/red paint, and eight genuine vector paths.

Every new HORS-V3 interactive build waits for SPACE at the original intro,
shows a separate `press SHIFT+H for help` row above the start prompt, and offers
**RUN/STOP (Esc in VICE) or Shift+H** pause/help. `+`, `-` and `0` control angular speed. The starfield is
included but disabled initially unless `--starfield-default enabled` is set;
`--no-starfield` (alias `--no-include-starfield`) excludes its code/data and key
binding entirely. These controls also apply to ordinary OBJ interactive builds.

Source-colour gradients keep red paint in the red family: native red for the
two darkest levels, then light red and white. The VIC-II palette has no separate
dark red. Explicit metallic overlays retain their established ramps, including
the golden Dragon's yellow/orange/brown highlights and shadows.
