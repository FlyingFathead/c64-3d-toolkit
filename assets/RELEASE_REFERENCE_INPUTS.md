# Frozen release and regression inputs

`released-example-pictures-v1.json.gz` contains the complete bitmap pictures,
resolved colour spans, sample order, static HUD bytes and presentation settings
from the 15 previously shipped standalone v1 examples. Each source cartridge
and each reconstructed picture has a SHA-256 identity. The v2 release builder
validates these pictures before encoding; it does not rebake Blender physics
or reduce the sample count. Original source geometry remains in the source
example folders where available.

`resident-regression-inputs.json.gz` contains 43 exact resident PRG regression
inputs, compressed with their original relative paths and hashes. They are
materialized into ignored `build/reference-prgs/` only when needed by the
preserved comparison/test paths. This lets old methods remain reproducible
without keeping legacy runnable previews in the active examples tree.

These fixtures do not supply new performance measurements. The canonical
menu workload remains `v4-menu-vector-reference.json.gz`; authored comparison
scenes remain `comparison-scene-vector-reference.json.gz`.

`legacy-example-files.json` is the explicit 103-file archive list. Cleanup first
checks every new artifact against `examples/release-index.json`, then preserves
old local files outside the checkout. Unknown custom files are not selected.
