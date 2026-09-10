> Current default: **hors-render-v2**. [Release build and example migration](RELEASE_0.7.2.md).

# Marbles recording start — 0.7.0

The shipped `examples/cart_marbles/marbles-hors-render-v2-16fps-force-bytes.crt`
already waits indefinitely for SPACE. Start recording in VICE, focus its window,
then press SPACE to begin the native intro. The scene follows, then the ending.
See [the presentation guide](../examples/cart_marbles/README.md).

No cleanup or startup patch is required for this release. New hors-render-v2
scene builds with the native intro also wait for SPACE. Historical renderer
build screens retain their original behaviour. Automated playback verifiers
must acknowledge the startup screen.

## Historical startup patch

`perf/marbles_wait_for_space.py` remains an idempotent compatibility utility for
the earlier accepted cart with an automatic timeout. It changes the startup
DEX/BNE sequence to CLC/BCC without changing animation addresses or payloads.
It checks for the expected accepted cart, backs up an automatic-start copy in
the external sibling archive, and leaves an already-patched cart alone.
