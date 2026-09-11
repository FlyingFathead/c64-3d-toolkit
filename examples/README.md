# Examples: hors-render-v2 / toolkit 0.7.4

All 20 current cartridges are rebuilt for 0.7.4 with the new loader, real EAPI
and PETSCII name metadata. The 0.7.3 colour controls remain available in Demo
Cart 1, Demo Cart 2.0 and [COLOR COMBO TEST](color_combo_test/README.md).
Older versioned menu and HiFi CRTs remain unchanged as historical references;
use the current links below for the updated builds.

All active prebuilt cartridges use **hors-render-v2**. Older CRT and PRG previews are archived outside this checkout; original renderer code and frozen test inputs remain available.

| Folder | Stable cartridges |
| --- | ---: |
| [color_combo_test](color_combo_test/README.md) | 1 |
| [blender_falling_cubes](blender_falling_cubes/README.md) | 2 |
| [cart_demos](cart_demos/README.md) | 2 |
| [cart_demos_v2](cart_demos_v2/README.md) | 1 |
| [cart_hifi](cart_hifi/README.md) | 1 |
| [cart_horse_and_sunflower](cart_horse_and_sunflower/README.md) | 2 |
| [cart_marbles](cart_marbles/README.md) | 1 |
| [cube](cube/README.md) | 1 |
| [hifi_showcase](hifi_showcase/README.md) | 1 |
| [horse_head](horse_head/README.md) | 1 |
| [space_horse_crawl](space_horse_crawl/README.md) | 1 |
| [space_horse_spin](space_horse_spin/README.md) | 1 |
| [sphere](sphere/README.md) | 1 |
| [sunflower_torus](sunflower_torus/README.md) | 2 |
| [torus](torus/README.md) | 1 |
| [torus_dense](torus_dense/README.md) | 1 |

Sources remain in the Blender and autotune folders. Use [COMPILE-RELEASE.sh](../docs/RELEASE_0.7.4.md#rebuild) to rebuild and verify the complete release.

`examples.json` remains the explicit resident regression recipe used by `generate-examples` / `test-examples`. For current v2 artifacts use `tools/build_current_examples.py` or the complete release compiler above.
