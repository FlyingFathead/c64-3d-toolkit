# Examples: toolkit 0.8.0

[Demo Cart v3.0: GMod3 All-in-One](gmod3_cart_demos/README.md) combines all 58 distinct released entries in one interactive 16 MiB cartridge, with an automatic benchmark companion.


The 26 preserved HORS-V2 and colour-test cartridges were rebuilt for 0.7.9 with the new loader, real EAPI
and PETSCII name metadata. The 0.7.3 colour controls remain available in Demo
Cart 1, Demo Cart 2.0 and [COLOR COMBO TEST](color_combo_test/README.md).
Older versioned menu and HiFi CRTs remain unchanged as historical references;
use the current links below for the updated builds.

HORS-V4 / GMod3 is the conversion default; the comparison/menu builder retains V2. The additional [HORS-V3 collection](hors_v3_preview/README.md) contains 11 surface, texture, interactive and comparison cartridges. Historical versioned menu and HiFi cartridges, original renderer code and frozen test inputs remain available.

The [Stanford Dragon example](stanford_dragon/README.md) adds six standalone HORS-V3 cartridges: wireframe, metallic (grey), golden, red, green and blue, with PAL-timed GIFs, performance results and a reproducible source mesh. It uses the HORS-V3 surface palette options introduced in 0.7.8.

The [SAKU 2026 example](saku_2026/README.md) includes the original vector logo,
solid and gradient carts, and all eight spin/crawl looks in one interactive
starfield cart, with help, speed and HUD controls.

| Folder | Stable cartridges |
| --- | ---: |
| [saku_2026](saku_2026/README.md) | 3 |
| [stanford_dragon](stanford_dragon/README.md) | 6 |
| [hors_v3_preview](hors_v3_preview/README.md) | 11 |
| [demos_sande](demos_sande/README.md) | 6 |
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

Sources remain in the Blender and autotune folders. Use [COMPILE-RELEASE.sh](../COMPILE-RELEASE.sh) to rebuild and verify the complete release; see the [release guide](../docs/RELEASE_0.7.9.md).

`examples.json` remains the explicit resident regression recipe used by `generate-examples` / `test-examples`. For current v2 artifacts use `tools/build_current_examples.py` or the complete release compiler above.

[SAKU 2026 SVG presentations and keyboard map](saku_2026/README.md) · [SAKU](https://suomenamigakayttajat.fi/) · [Saku magazine](https://sakulehti.fi/)
