# DON'T LOSE YOUR MARBLES

**0.6.8 / V8:** separate [clean FPS](dont_lose_your_marbles-yunroll-cart-v8-scene-clean.crt), [HUD FPS](dont_lose_your_marbles-yunroll-cart-v8-scene.crt), [clean RAM](dont_lose_your_marbles-yunroll-cart-v8-scene-clean-ram.crt) and [HUD RAM](dont_lose_your_marbles-yunroll-cart-v8-scene-ram.crt) carts. All 200 samples and older carts are preserved. [Measured changes](../../docs/CARTRIDGE_STREAM_V8.md).

**0.6.7 / V7, FPS preferred by default:**
[clean presentation](dont_lose_your_marbles-yunroll-cart-v7-scene-clean.crt) and
[HUD build](dont_lose_your_marbles-yunroll-cart-v7-scene.crt).
Optional RAM comparisons: [clean](dont_lose_your_marbles-yunroll-cart-v7-scene-clean-ram.crt)
and [HUD](dont_lose_your_marbles-yunroll-cart-v7-scene-ram.crt).

V7 preserves all 200 original samples, colours, seven-tick pacing, intro and
ending. Clean scene duration falls to **30.45 seconds from V6's 31.43**, while
each CRT shrinks to **353,008 bytes from 418,672**. Every frame matches the
frozen V6 oracle. The build screen shows `0.6.7` / `yunroll-v7` for about
three seconds or SPACE to skip. RAM builds identify `yunroll-v7 (ram)`.
See the [V7 guide](../../docs/CARTRIDGE_STREAM_V7.md) for timings and validation.

```bash
x64sc -cartcrt examples/cart_marbles/dont_lose_your_marbles-yunroll-cart-v7-scene-clean.crt
python tools/build_v7_examples.py
```

PLAY ALL belongs to the separate multi-demo menu; Marbles retains its finite story.

## Preserved V6 comparison

**0.6.7-rc3 / V6 candidate:**
[clean presentation](dont_lose_your_marbles-yunroll-cart-v6-scene-clean.crt) and
[HUD build](dont_lose_your_marbles-yunroll-cart-v6-scene.crt).
The white-on-black build screen shows `0.6.7-rc3` and `yunroll-v6` for about
three seconds, or SPACE skips immediately into the original native intro.

V6 uses the same 200 samples and seven-raster-tick cadence as V5. In matched
PAL VICE profiling, the clean vector scene takes **31.43 seconds versus V5's
32.07**, with exact bitmap/colour matches on every frame. Both CRTs occupy
418,672 bytes, the same as V5. The V4 and V5 releases are preserved below and
alongside these files. See [the V6 guide](../../docs/CARTRIDGE_STREAM_V6.md)
for the changes, comparisons and validation.

From the repository root:

```bash
x64sc -cartcrt examples/cart_marbles/dont_lose_your_marbles-yunroll-cart-v6-scene-clean.crt
python tools/build_v6_examples.py
```

## Original V4 release

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

The earlier looping build is preserved in the separate oldies ZIP as an [early concept tryout](../../docs/UPGRADING_0.6.7.md#what-cleanup-does).
