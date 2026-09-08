# HiFi exhibition cartridge — v0.7.1

[Download the HiFi cart](c643d-hifi-v0.7.1-hors-render-v1.crt).

Press SPACE on the opening screen to begin. The reel then repeats:

1. The complete Horse and Sunflower animation: the horse sniffs the flower and withdraws its head. All 84 authored samples play once, with the original six-PAL-tick minimum pacing. This takes approximately 11.6 seconds in PAL VICE; the animation completes before the next section starts.
2. Rotating HiFi sunflower torus, with its caption: 10 seconds.
3. Rotating HiFi horse head, with its caption: 10 seconds.
4. Native THANK YOU FOR WATCHING screen with v0.7.1 identification: 10 seconds.

The next cycle starts with the sniffing scene. The opening SPACE wait appears
only at startup or after exiting the reel. During animation, SPACE skips to the
next section; F1 or RUN/STOP returns to the opening screen. F1 also exits the
thank-you screen.

The spinners use the same 128-orientation sources and captions as the multi-demo
cart. The first section uses the frozen vector reference for
`horse_and_sunflower-hors-render-v1-scene.crt`; it is rebuilt into the shared reel
runtime, so this cartridge does not concatenate or launch the original CRT files.

## Build and verify

From the repository root, with 64tass, cartconv and VICE installed:

```bash
python tools/build_hifi_cart.py
python tools/verify_hifi_reel.py \
  examples/cart_hifi/c643d-hifi-v0.7.1-hors-render-v1.crt \
  --vice-data /usr/local/share/vice
```

Blender and the external historical archive are not needed. The bundled vector
references retain the original scene sampling. Timing is specified for PAL.
