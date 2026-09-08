⚠️🐴 Attention! For best quality, please enjoy the `hors-renderer` version of each animation.

Recommended for quality and FPS: the `hors-render-v1` cartridge linked below.

# HiFi horse head — hors-render-v1

Example #3 for 0.7.0: the coloured HiFi horse head, compiled from
`objects/horse_head_hifi.obj` and its material/preset files into 192 orientations.

```bash
x64sc +easyflashcrtwrite -cartcrt examples/hifi_showcase/horse_head_hifi-hors-render-v1.crt
```

Rebuild from the repository root:

```bash
python c643d.py build --object horse_head_hifi --renderer hors-render-v1 --frames 192 --strict-frames --viewport-height 192 --text-overlay --output horse_head_hifi-hors-render-v1 --output-dir examples/hifi_showcase --no-config --overwrite-policy allow
```

Only this current cartridge and its matching labels and manifest are shipped here.
V2/V3 outputs remain outside the checkout. The cleanup script retains this example.
