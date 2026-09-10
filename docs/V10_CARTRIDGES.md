> Historical version documentation. Current builds and prebuilt examples use [hors-render-v2](HORS_RENDER_V2.md); see [0.7.2 release instructions](RELEASE_0.7.2.md). Older preview binaries are in prior release ZIPs or the external local archive.

# hors-render-v1 cartridge inventory — 0.7.1

The v0.7.1 menu cartridges are rebuilt for this release, alongside the new
[HiFi exhibition reel](../examples/cart_hifi/README.md). Standalone object and
authored-scene cartridges are retained byte-for-byte from v0.7.0; their embedded
version labels and manifests remain their original build provenance.

These are the shipped cartridges in the v0.7.1 package. File sizes include CRT
container headers and are not measurements of free flash or free runtime RAM.
The hardware target is EasyFlash with 1 MiB of flash.

| Cartridge | CRT bytes |
| --- | ---: |
| [c643d-hifi-v0.7.1-hors-render-v1.crt](../examples/cart_hifi/c643d-hifi-v0.7.1-hors-render-v1.crt) | 689,536 |
| [falling_cubes_c64-hors-render-v1.crt](../examples/blender_falling_cubes/falling_cubes_c64-hors-render-v1.crt) | 57,520 |
| [falling_cubes_c64_color-hors-render-v1.crt](../examples/blender_falling_cubes/falling_cubes_c64_color-hors-render-v1.crt) | 57,520 |
| [c643d-demo-v0.7.1-hors-render-v1-all-ram.crt](../examples/cart_demos/c643d-demo-v0.7.1-hors-render-v1-all-ram.crt) | 985,024 |
| [c643d-demo-v0.7.1-hors-render-v1-all.crt](../examples/cart_demos/c643d-demo-v0.7.1-hors-render-v1-all.crt) | 985,024 |
| [horse_and_sunflower-hors-render-v1-scene-ram.crt](../examples/cart_horse_and_sunflower/horse_and_sunflower-hors-render-v1-scene-ram.crt) | 279,136 |
| [horse_and_sunflower-hors-render-v1-scene.crt](../examples/cart_horse_and_sunflower/horse_and_sunflower-hors-render-v1-scene.crt) | 279,136 |
| [marbles-hors-render-v1-16fps-force-bytes.crt](../examples/cart_marbles/marbles-hors-render-v1-16fps-force-bytes.crt) | 902,944 |
| [cube-hors-render-v1.crt](../examples/cube/cube-hors-render-v1.crt) | 82,144 |
| [horse_head_hifi-hors-render-v1.crt](../examples/hifi_showcase/horse_head_hifi-hors-render-v1.crt) | 295,552 |
| [horse_head-hors-render-v1.crt](../examples/horse_head/horse_head-hors-render-v1.crt) | 229,888 |
| [space_horse_crawl_color-hors-render-v1.crt](../examples/space_horse_crawl/space_horse_crawl_color-hors-render-v1.crt) | 164,224 |
| [space_horse_spin_color-hors-render-v1.crt](../examples/space_horse_spin/space_horse_spin_color-hors-render-v1.crt) | 353,008 |
| [sphere-hors-render-v1.crt](../examples/sphere/sphere-hors-render-v1.crt) | 197,056 |
| [sunflower_torus-hors-render-v1.crt](../examples/sunflower_torus/sunflower_torus-hors-render-v1.crt) | 254,512 |
| [sunflower_torus_color-hors-render-v1.crt](../examples/sunflower_torus/sunflower_torus_color-hors-render-v1.crt) | 295,552 |
| [torus-hors-render-v1.crt](../examples/torus/torus-hors-render-v1.crt) | 336,592 |
| [torus_dense-hors-render-v1.crt](../examples/torus_dense/torus_dense-hors-render-v1.crt) | 361,216 |

The accepted Marbles presentation is the **902,944-byte, 640-sample, 16 FPS
force-bytes** cartridge. It waits for SPACE before the intro. Its recorded scene
interval is about 41.82 seconds; there is no validated HUD/RAM equivalent for
this sampling. The older 344,800-byte Marbles variants used 200 samples and are
historical outputs, not the current release presentation.

The menu's HiFi entries use 128 samples in the frozen comparison workload; the
standalone HiFi horse has 192 orientations. Their sizes and throughput describe
different workloads. See [builds and verification](V10_TESTING.md),
[Marbles](../examples/cart_marbles/README.md) and
[capacity accounting](CARTRIDGE_CAPACITY.md).
