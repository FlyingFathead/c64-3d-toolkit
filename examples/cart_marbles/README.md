# DON'T LOSE YOUR MARBLES

**Early beta, included with toolkit v0.6.6.** A silent standalone EasyFlash demo.
Music and digi playback remain future experiments.

- `dont_lose_your_marbles-yunroll-cart-v4-scene-clean.crt`: presentation build,
  with no title/FPS HUD. Recommended for watching the complete demo.
- `dont_lose_your_marbles-yunroll-cart-v4-scene.crt`: development build,
  with `DON'T LOSE YOUR MARBLES` and the right-hand FPS counter.

Attach either CRT in VICE as an EasyFlash cartridge:

```bash
x64sc -cartcrt dont_lose_your_marbles-yunroll-cart-v4-scene-clean.crt
```

The native intro fades in FlyingFathead and presents, slams in the title one
word at a time, then shows A COMMODORE 64 / CARTRIDGE DEMO on white.
The orbiting scene pours cubes, marbles, more cubes and more marbles onto a table.
The table fractures into 32 pieces which drift into a constellation.

After a brief star-field hold and flash, the machine types
`GREETINGS TO ALL OLD DEMOSCENE WANKE`, pauses, backspaces the last five letters,
and corrects itself to `WANDERERS`. Animated THANK YOU / FOR WATCHING and
`github.com/FlyingFathead` follow on white. The credits fade away into a staged
BASIC boot screen. After a pause at READY., the machine types:

```text
HEY... DON'T LOSE YOUR MARBLES. :-)
```

The cursor then blinks indefinitely. This is a scripted boot-screen illusion,
not an actual reset or interactive BASIC session. The demo does not loop;
reset the cartridge to replay it.

Measured PAL VICE timing: approximately **58.15 seconds from reset through the
completed ghost message**, including **36.37 seconds of vector scene playback**.
The source is a 40-second Blender timeline sampled into 200 frames. Overall
scene throughput is about 5.5 FPS; busy collisions/fracture exceed the nominal
7.14 FPS target. Every exported sample is drawn, without runtime frame dropping.

Both builds pass exact bitmap/colour checks for all 200 frames across three
buffers. The ending verifier checks the greeting correction, BASIC banner,
message and stable idle loop. A separate visibility audit checks 514 unobscured
marble-on-table samples for pixels within their projected bounds, with no empty
regions found. This does not identify the exact frame of the earlier reported
disappearance, but this build has no timed disposal of released marbles.

The stream uses 405,972 vector bytes before bank-packing gaps. See
`validation.json`, `validation-clean.json`, `ending-validation.json`,
`ending-clean-validation.json`, `marble-visibility-audit.json`, and the intro/
ending screenshots. PAL VICE is verified; physical EasyFlash and NTSC are untested.

The original V4 renderer, falling-cubes assets and twelve-demo menu cart are
unchanged. This standalone example ships alongside that menu cartridge.
See [the scene guide](../../docs/CARTRIDGE_SCENES.md) for rebuild commands and the
specific assembly changes.

The earlier looping build is preserved as an [early concept tryout](../old/cart_marbles/early-test-v0.6.5/README.md).
