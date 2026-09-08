# Frozen scene comparison references

`comparison-scene-vector-reference.json.gz` preserves the exact decoded vector records and manifest metadata used by the renderer comparison. It was recovered from the preserved `c64-3d-toolkit-v0.6.9-final.zip`; Blender was not rerun.

The comparison loader verifies the asset SHA-256 before use. These inputs retain the historical workload and pacing; they do not substitute the newer 16 FPS force-bytes Marbles presentation.

| Scene | Original cartridge | SHA-256 | Frames |
| --- | --- | --- | ---: |
| horse-sunflower | `examples/cart_horse_and_sunflower/horse_and_sunflower-yunroll-cart-v7-scene.crt` | `963668b568625f1f2fcb28f9bb2c2a75ca33e2103c2e768522fd90a691dcd563` | 84 |
| marbles | `examples/cart_marbles/dont_lose_your_marbles-yunroll-cart-v4-scene-clean.crt` | `7ae73a7d069e25f0bbffc87460324429ff67f55446f1e40347aa6a92adfa0125` | 200 |

Each scene stores `frames` (serialized `FrameBuild` records), the original `manifest`, `source_file`, and `source_sha256`. The outer format is `c643d-scene-vector-reference-v1`. Gzip uses a zero timestamp for reproducible bytes.

Run the full comparison using the commands in `docs/PERFORMANCE_COMPARISON.md`. No historical example cartridges or sibling archive directory are needed.
