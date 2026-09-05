# DON'T LOSE YOUR MARBLES

**DON'T LOSE YOUR MARBLES — early beta.** This build is silent. SID music and
possible digi playback are future experiments; audio integration has not yet
been implemented or validated.

A standalone EasyFlash cartridge experiment built on the V4 scene extension.

- `dont_lose_your_marbles-yunroll-cart-v4-scene.crt`: intro, scene, title and FPS HUD.
- `dont_lose_your_marbles-yunroll-cart-v4-scene-clean.crt`: same intro and scene, with no HUD.

Attach either CRT to VICE as an EasyFlash cartridge. For example:

```bash
x64sc -cartcrt dont_lose_your_marbles-yunroll-cart-v4-scene.crt
```

The intro fades in **FlyingFathead**, then **presents**, fades to white,
slams in **DON'T / LOSE / YOUR / MARBLES** one word at a time, then shows
**A COMMODORE 64 / CARTRIDGE DEMO** on white and flashes into the scene.
The scene loops; reset the cartridge to replay the introduction.

The 60-second Blender scene has 86 objects across ten alternating cube/marble
pours and a full camera orbit. The C64 plays all 750 samples, with colours and
hidden-line removal. Objects bounce, slide and fall off the table and screen.
Blender computes the physics; the C64 rasterises streamed vectors in real time.

Measured in PAL VICE 3.10:

| Build | Scene loop | Overall FPS | Verified frames |
|---|---:|---:|---:|
| Title / FPS HUD | 72.819 s | 10.31 | 1,503 |
| Clean | 72.779 s | 10.32 | 1,503 |

The intro adds startup time. Busy pours drop below the nominal 12.5 FPS target;
no samples are skipped. Both variants match the host oracle exactly in bitmap
pixels and colours across all three buffers, both ROM chips and loop wrap.
The clean HUD row is checked blank. See the accompanying validation reports.
Physical EasyFlash hardware and NTSC have not been tested here.

The stream occupies 698,536 vector bytes before bank-packing gaps. Complete
frames stay inside 8 KiB banks. The active RAM directory is fixed at 1,792 bytes;
16-bit indexing and ROM directory pages lift the original 255-frame limit.

The original V4 renderer, twelve-demo cartridge and falling-cubes example are
preserved byte-for-byte. This is an unreleased experiment on the v0.6.5 source
baseline, not a replacement release of that baseline.

In the full source package, see `docs/CARTRIDGE_SCENES.md` for build commands,
architecture and limitations, and `examples/blender_marbles/` for the generator,
live-physics `.blend`, and baked `.blend` ready for export. The neutral scene
export and verification oracle are recreated under `build/` during compilation.
