# v0.8.2 HORS family performance

Six implementations, 16 fixed public inputs, FPS/RAM preferences. PAL VICE, sound disabled, seed 1; uncapped common V9 normal PLAY ALL controller, three ten-second visits. SAKU contains only the rotating logo. 190 rows pass complete bitmap and screen-colour checks; two HORS-V1 Dragon wireframe rows exceed capacity (10,492-byte frame, 8,192-byte staging buffer). No source samples are dropped.

| Public input | HORS-V1 | HORS-V2 | HORS-V3 | HORS-V4 EF | V5-c1 | V5-c2 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| TORUS | 16.072 | 17.680 | 17.680 | 17.680 | **17.780** | **17.780** |
| TORUS DENSE | 15.771 | 17.179 | 17.179 | 17.179 | **17.380** | **17.380** |
| CUBE | 27.423 | 30.031 | 30.031 | 30.031 | **30.032** | **30.032** |
| SPHERE | 15.871 | 17.379 | 17.379 | 17.379 | **17.478** | **17.478** |
| HORSE HEAD | 27.422 | 29.335 | 29.335 | 29.335 | **29.432** | **29.432** |
| SUNFLOWER TORUS | 27.122 | 28.730 | 28.730 | 28.730 | **28.927** | **28.927** |
| SUNFLOWER COLOR | 19.991 | 20.891 | 22.701 | 22.701 | **22.733** | **22.733** |
| SPACE HORSE SPIN | 17.579 | 19.083 | 19.086 | 19.086 | **19.288** | **19.288** |
| SPACE HORSE CRAWL | 35.559 | **38.275** | 38.273 | 38.273 | 38.271 | 38.271 |
| FALLING CUBES | 19.688 | 20.892 | 21.295 | 21.295 | **21.396** | **21.396** |
| HORSE HEAD HIFI | 20.693 | 21.495 | 23.105 | 23.105 | **23.204** | **23.204** |
| SUNFLOWER TORUS HIFI | 19.889 | 20.394 | 22.702 | 22.702 | **22.804** | **22.804** |
| DRAGON WIREFRAME | N/A | 19.387 | 19.387 | 19.387 | **19.454** | **19.454** |
| DRAGON METALLIC | 11.250 | 11.452 | 14.265 | 14.265 | **14.366** | **14.366** |
| SAKU SOLID LOGO ONLY | 36.966 | **38.808** | 32.010 | 32.010 | 32.214 | 38.773 |
| SAKU GRADIENT LOGO ONLY | 31.107 | 32.013 | 31.209 | 31.209 | 31.335 | **32.109** |

## Full measurements

Average FPS uses observed display flips over measured elapsed C64 time. P95 and worst holds describe display intervals. Tied aliases remain visible; they are not independent speed improvements. CRT bytes include the container. Public comparisons here are core-harness tests, not native authored-scene pacing.

## TORUS

32 pictures.

| Renderer | Preference | Average FPS | P95 ms | Worst ms | CRT bytes | Result |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| yunroll-cart-v10 | fps | 16.07221 | 79.803 | 82.668 | 985,024 | pixels and colours passed |
| yunroll-cart-v10 | ram | 16.07201 | 79.803 | 83.088 | 985,024 | pixels and colours passed |
| hors-render-v2 | fps | 17.67972 | 79.801 | 82.734 | 985,024 | pixels and colours passed |
| hors-render-v2 | ram | 17.67800 | 79.801 | 83.306 | 985,024 | pixels and colours passed |
| hors-renderer-v3 | fps | 17.67972 | 79.801 | 82.734 | 1,009,648 | pixels and colours passed |
| hors-renderer-v3 | ram | 17.67800 | 79.801 | 83.306 | 1,009,648 | pixels and colours passed |
| hors-v4-ef | fps | 17.67972 | 79.801 | 82.734 | 1,009,648 | pixels and colours passed |
| hors-v4-ef | ram | 17.67800 | 79.801 | 83.306 | 1,009,648 | pixels and colours passed |
| hors-v5-c1 | fps | 17.77998 | 79.800 | 79.812 | 1,001,440 | pixels and colours passed |
| hors-v5-c1 | ram | 17.78158 | 79.801 | 82.167 | 1,001,440 | pixels and colours passed |
| hors-v5-c2 | fps | 17.77998 | 79.800 | 79.812 | 1,001,440 | pixels and colours passed |
| hors-v5-c2 | ram | 17.78158 | 79.801 | 82.167 | 1,001,440 | pixels and colours passed |

## TORUS DENSE

32 pictures.

| Renderer | Preference | Average FPS | P95 ms | Worst ms | CRT bytes | Result |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| yunroll-cart-v10 | fps | 15.77050 | 79.804 | 81.951 | 985,024 | pixels and colours passed |
| yunroll-cart-v10 | ram | 15.77397 | 79.804 | 83.035 | 985,024 | pixels and colours passed |
| hors-render-v2 | fps | 17.17877 | 79.801 | 79.806 | 985,024 | pixels and colours passed |
| hors-render-v2 | ram | 17.17778 | 79.803 | 79.805 | 985,024 | pixels and colours passed |
| hors-renderer-v3 | fps | 17.17877 | 79.801 | 79.806 | 1,009,648 | pixels and colours passed |
| hors-renderer-v3 | ram | 17.17778 | 79.803 | 79.805 | 1,009,648 | pixels and colours passed |
| hors-v4-ef | fps | 17.17877 | 79.801 | 79.806 | 1,009,648 | pixels and colours passed |
| hors-v4-ef | ram | 17.17778 | 79.803 | 79.805 | 1,009,648 | pixels and colours passed |
| hors-v5-c1 | fps | 17.38025 | 79.802 | 79.806 | 1,001,440 | pixels and colours passed |
| hors-v5-c1 | ram | 17.37716 | 79.801 | 79.805 | 1,001,440 | pixels and colours passed |
| hors-v5-c2 | fps | 17.38025 | 79.802 | 79.806 | 1,001,440 | pixels and colours passed |
| hors-v5-c2 | ram | 17.37716 | 79.801 | 79.805 | 1,001,440 | pixels and colours passed |

## CUBE

36 pictures.

| Renderer | Preference | Average FPS | P95 ms | Worst ms | CRT bytes | Result |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| yunroll-cart-v10 | fps | 27.42273 | 40.872 | 60.087 | 985,024 | pixels and colours passed |
| yunroll-cart-v10 | ram | 27.42278 | 41.221 | 59.934 | 985,024 | pixels and colours passed |
| hors-render-v2 | fps | 30.03055 | 41.837 | 43.180 | 985,024 | pixels and colours passed |
| hors-render-v2 | ram | 30.03722 | 41.470 | 43.236 | 985,024 | pixels and colours passed |
| hors-renderer-v3 | fps | 30.03055 | 41.837 | 43.180 | 1,009,648 | pixels and colours passed |
| hors-renderer-v3 | ram | 30.03722 | 41.470 | 43.236 | 1,009,648 | pixels and colours passed |
| hors-v4-ef | fps | 30.03055 | 41.837 | 43.180 | 1,009,648 | pixels and colours passed |
| hors-v4-ef | ram | 30.03722 | 41.470 | 43.236 | 1,009,648 | pixels and colours passed |
| hors-v5-c1 | fps | 30.03204 | 41.681 | 42.899 | 1,001,440 | pixels and colours passed |
| hors-v5-c1 | ram | 30.13382 | 41.229 | 41.526 | 1,001,440 | pixels and colours passed |
| hors-v5-c2 | fps | 30.03204 | 41.681 | 42.899 | 1,001,440 | pixels and colours passed |
| hors-v5-c2 | ram | 30.13382 | 41.229 | 41.526 | 1,001,440 | pixels and colours passed |

## SPHERE

24 pictures.

| Renderer | Preference | Average FPS | P95 ms | Worst ms | CRT bytes | Result |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| yunroll-cart-v10 | fps | 15.87107 | 82.982 | 84.202 | 985,024 | pixels and colours passed |
| yunroll-cart-v10 | ram | 15.87105 | 79.819 | 84.258 | 985,024 | pixels and colours passed |
| hors-render-v2 | fps | 17.37914 | 63.105 | 64.391 | 985,024 | pixels and colours passed |
| hors-render-v2 | ram | 17.37851 | 63.091 | 64.250 | 985,024 | pixels and colours passed |
| hors-renderer-v3 | fps | 17.37914 | 63.105 | 64.391 | 1,009,648 | pixels and colours passed |
| hors-renderer-v3 | ram | 17.37851 | 63.091 | 64.250 | 1,009,648 | pixels and colours passed |
| hors-v4-ef | fps | 17.37914 | 63.105 | 64.391 | 1,009,648 | pixels and colours passed |
| hors-v4-ef | ram | 17.37851 | 63.091 | 64.250 | 1,009,648 | pixels and colours passed |
| hors-v5-c1 | fps | 17.47823 | 62.882 | 64.204 | 1,001,440 | pixels and colours passed |
| hors-v5-c1 | ram | 17.47951 | 62.607 | 64.216 | 1,001,440 | pixels and colours passed |
| hors-v5-c2 | fps | 17.47823 | 62.882 | 64.204 | 1,001,440 | pixels and colours passed |
| hors-v5-c2 | ram | 17.47951 | 62.607 | 64.216 | 1,001,440 | pixels and colours passed |

## HORSE HEAD

32 pictures.

| Renderer | Preference | Average FPS | P95 ms | Worst ms | CRT bytes | Result |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| yunroll-cart-v10 | fps | 27.42236 | 41.979 | 60.425 | 985,024 | pixels and colours passed |
| yunroll-cart-v10 | ram | 27.42286 | 42.230 | 60.250 | 985,024 | pixels and colours passed |
| hors-render-v2 | fps | 29.33514 | 41.039 | 41.850 | 985,024 | pixels and colours passed |
| hors-render-v2 | ram | 29.33001 | 41.155 | 42.266 | 985,024 | pixels and colours passed |
| hors-renderer-v3 | fps | 29.33514 | 41.039 | 41.850 | 1,009,648 | pixels and colours passed |
| hors-renderer-v3 | ram | 29.33001 | 41.155 | 42.266 | 1,009,648 | pixels and colours passed |
| hors-v4-ef | fps | 29.33514 | 41.039 | 41.850 | 1,009,648 | pixels and colours passed |
| hors-v4-ef | ram | 29.33001 | 41.155 | 42.266 | 1,009,648 | pixels and colours passed |
| hors-v5-c1 | fps | 29.43246 | 41.069 | 41.464 | 1,001,440 | pixels and colours passed |
| hors-v5-c1 | ram | 29.43351 | 41.054 | 41.599 | 1,001,440 | pixels and colours passed |
| hors-v5-c2 | fps | 29.43246 | 41.069 | 41.464 | 1,001,440 | pixels and colours passed |
| hors-v5-c2 | ram | 29.43351 | 41.054 | 41.599 | 1,001,440 | pixels and colours passed |

## SUNFLOWER TORUS

28 pictures.

| Renderer | Preference | Average FPS | P95 ms | Worst ms | CRT bytes | Result |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| yunroll-cart-v10 | fps | 27.12165 | 60.050 | 61.544 | 985,024 | pixels and colours passed |
| yunroll-cart-v10 | ram | 27.12163 | 59.934 | 61.167 | 985,024 | pixels and colours passed |
| hors-render-v2 | fps | 28.72975 | 41.550 | 61.348 | 985,024 | pixels and colours passed |
| hors-render-v2 | ram | 28.72945 | 60.220 | 61.437 | 985,024 | pixels and colours passed |
| hors-renderer-v3 | fps | 28.72975 | 41.550 | 61.348 | 1,009,648 | pixels and colours passed |
| hors-renderer-v3 | ram | 28.72945 | 60.220 | 61.437 | 1,009,648 | pixels and colours passed |
| hors-v4-ef | fps | 28.72975 | 41.550 | 61.348 | 1,009,648 | pixels and colours passed |
| hors-v4-ef | ram | 28.72945 | 60.220 | 61.437 | 1,009,648 | pixels and colours passed |
| hors-v5-c1 | fps | 28.92669 | 59.980 | 61.467 | 1,001,440 | pixels and colours passed |
| hors-v5-c1 | ram | 28.93080 | 59.906 | 61.567 | 1,001,440 | pixels and colours passed |
| hors-v5-c2 | fps | 28.92669 | 59.980 | 61.467 | 1,001,440 | pixels and colours passed |
| hors-v5-c2 | ram | 28.93080 | 59.906 | 61.567 | 1,001,440 | pixels and colours passed |

## SUNFLOWER COLOR

20 pictures.

| Renderer | Preference | Average FPS | P95 ms | Worst ms | CRT bytes | Result |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| yunroll-cart-v10 | fps | 19.99089 | 60.048 | 79.801 | 985,024 | pixels and colours passed |
| yunroll-cart-v10 | ram | 19.98982 | 59.854 | 79.804 | 985,024 | pixels and colours passed |
| hors-render-v2 | fps | 20.89136 | 59.854 | 63.176 | 985,024 | pixels and colours passed |
| hors-render-v2 | ram | 20.89354 | 59.855 | 61.930 | 985,024 | pixels and colours passed |
| hors-renderer-v3 | fps | 22.70070 | 61.075 | 62.477 | 1,009,648 | pixels and colours passed |
| hors-renderer-v3 | ram | 22.69844 | 60.991 | 62.547 | 1,009,648 | pixels and colours passed |
| hors-v4-ef | fps | 22.70070 | 61.075 | 62.477 | 1,009,648 | pixels and colours passed |
| hors-v4-ef | ram | 22.69844 | 60.991 | 62.547 | 1,009,648 | pixels and colours passed |
| hors-v5-c1 | fps | 22.73306 | 60.989 | 62.527 | 1,001,440 | pixels and colours passed |
| hors-v5-c1 | ram | 22.70164 | 60.952 | 62.456 | 1,001,440 | pixels and colours passed |
| hors-v5-c2 | fps | 22.73306 | 60.989 | 62.527 | 1,001,440 | pixels and colours passed |
| hors-v5-c2 | ram | 22.70164 | 60.952 | 62.456 | 1,001,440 | pixels and colours passed |

## SPACE HORSE SPIN

24 pictures.

| Renderer | Preference | Average FPS | P95 ms | Worst ms | CRT bytes | Result |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| yunroll-cart-v10 | fps | 17.57871 | 79.803 | 82.202 | 985,024 | pixels and colours passed |
| yunroll-cart-v10 | ram | 17.57849 | 79.803 | 79.842 | 985,024 | pixels and colours passed |
| hors-render-v2 | fps | 19.08280 | 79.801 | 79.806 | 985,024 | pixels and colours passed |
| hors-render-v2 | ram | 19.08605 | 79.801 | 81.904 | 985,024 | pixels and colours passed |
| hors-renderer-v3 | fps | 19.08558 | 79.800 | 79.803 | 1,009,648 | pixels and colours passed |
| hors-renderer-v3 | ram | 19.08625 | 79.801 | 79.819 | 1,009,648 | pixels and colours passed |
| hors-v4-ef | fps | 19.08558 | 79.800 | 79.803 | 1,009,648 | pixels and colours passed |
| hors-v4-ef | ram | 19.08625 | 79.801 | 79.819 | 1,009,648 | pixels and colours passed |
| hors-v5-c1 | fps | 19.28795 | 79.799 | 79.805 | 1,001,440 | pixels and colours passed |
| hors-v5-c1 | ram | 19.28794 | 79.796 | 79.805 | 1,001,440 | pixels and colours passed |
| hors-v5-c2 | fps | 19.28795 | 79.799 | 79.805 | 1,001,440 | pixels and colours passed |
| hors-v5-c2 | ram | 19.28794 | 79.796 | 79.805 | 1,001,440 | pixels and colours passed |

## SPACE HORSE CRAWL

32 pictures.

| Renderer | Preference | Average FPS | P95 ms | Worst ms | CRT bytes | Result |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| yunroll-cart-v10 | fps | 35.55910 | 40.248 | 60.225 | 985,024 | pixels and colours passed |
| yunroll-cart-v10 | ram | 35.65986 | 40.186 | 60.225 | 985,024 | pixels and colours passed |
| hors-render-v2 | fps | 38.27451 | 40.980 | 41.545 | 985,024 | pixels and colours passed |
| hors-render-v2 | ram | 38.27160 | 40.976 | 41.545 | 985,024 | pixels and colours passed |
| hors-renderer-v3 | fps | 38.27324 | 40.978 | 41.539 | 1,009,648 | pixels and colours passed |
| hors-renderer-v3 | ram | 38.27757 | 40.978 | 41.539 | 1,009,648 | pixels and colours passed |
| hors-v4-ef | fps | 38.27324 | 40.978 | 41.539 | 1,009,648 | pixels and colours passed |
| hors-v4-ef | ram | 38.27757 | 40.978 | 41.539 | 1,009,648 | pixels and colours passed |
| hors-v5-c1 | fps | 38.27057 | 41.261 | 41.573 | 1,001,440 | pixels and colours passed |
| hors-v5-c1 | ram | 38.27668 | 41.261 | 41.573 | 1,001,440 | pixels and colours passed |
| hors-v5-c2 | fps | 38.27057 | 41.261 | 41.573 | 1,001,440 | pixels and colours passed |
| hors-v5-c2 | ram | 38.27668 | 41.261 | 41.573 | 1,001,440 | pixels and colours passed |

## FALLING CUBES

18 pictures.

| Renderer | Preference | Average FPS | P95 ms | Worst ms | CRT bytes | Result |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| yunroll-cart-v10 | fps | 19.68817 | 60.745 | 81.445 | 985,024 | pixels and colours passed |
| yunroll-cart-v10 | ram | 19.58739 | 61.321 | 82.426 | 985,024 | pixels and colours passed |
| hors-render-v2 | fps | 20.89210 | 61.301 | 62.576 | 985,024 | pixels and colours passed |
| hors-render-v2 | ram | 20.89366 | 60.616 | 62.595 | 985,024 | pixels and colours passed |
| hors-renderer-v3 | fps | 21.29535 | 61.667 | 62.576 | 1,009,648 | pixels and colours passed |
| hors-renderer-v3 | ram | 21.29738 | 61.486 | 62.389 | 1,009,648 | pixels and colours passed |
| hors-v4-ef | fps | 21.29535 | 61.667 | 62.576 | 1,009,648 | pixels and colours passed |
| hors-v4-ef | ram | 21.29738 | 61.486 | 62.389 | 1,009,648 | pixels and colours passed |
| hors-v5-c1 | fps | 21.39579 | 61.488 | 62.530 | 1,001,440 | pixels and colours passed |
| hors-v5-c1 | ram | 21.39680 | 61.516 | 62.560 | 1,001,440 | pixels and colours passed |
| hors-v5-c2 | fps | 21.39579 | 61.488 | 62.530 | 1,001,440 | pixels and colours passed |
| hors-v5-c2 | ram | 21.39680 | 61.516 | 62.560 | 1,001,440 | pixels and colours passed |

## HORSE HEAD HIFI

128 pictures.

| Renderer | Preference | Average FPS | P95 ms | Worst ms | CRT bytes | Result |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| yunroll-cart-v10 | fps | 20.69308 | 62.097 | 63.808 | 985,024 | pixels and colours passed |
| yunroll-cart-v10 | ram | 20.79254 | 62.199 | 63.629 | 985,024 | pixels and colours passed |
| hors-render-v2 | fps | 21.49514 | 62.269 | 63.954 | 985,024 | pixels and colours passed |
| hors-render-v2 | ram | 21.59796 | 62.387 | 64.257 | 985,024 | pixels and colours passed |
| hors-renderer-v3 | fps | 23.10472 | 60.706 | 62.370 | 1,009,648 | pixels and colours passed |
| hors-renderer-v3 | ram | 23.20544 | 60.618 | 62.388 | 1,009,648 | pixels and colours passed |
| hors-v4-ef | fps | 23.10472 | 60.706 | 62.370 | 1,009,648 | pixels and colours passed |
| hors-v4-ef | ram | 23.20544 | 60.618 | 62.388 | 1,009,648 | pixels and colours passed |
| hors-v5-c1 | fps | 23.20439 | 60.195 | 62.094 | 1,001,440 | pixels and colours passed |
| hors-v5-c1 | ram | 23.30673 | 60.715 | 62.497 | 1,001,440 | pixels and colours passed |
| hors-v5-c2 | fps | 23.20439 | 60.195 | 62.094 | 1,001,440 | pixels and colours passed |
| hors-v5-c2 | ram | 23.30673 | 60.715 | 62.497 | 1,001,440 | pixels and colours passed |

## SUNFLOWER TORUS HIFI

128 pictures.

| Renderer | Preference | Average FPS | P95 ms | Worst ms | CRT bytes | Result |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| yunroll-cart-v10 | fps | 19.88874 | 59.856 | 79.803 | 985,024 | pixels and colours passed |
| yunroll-cart-v10 | ram | 19.89087 | 60.392 | 79.801 | 985,024 | pixels and colours passed |
| hors-render-v2 | fps | 20.39390 | 59.856 | 62.582 | 985,024 | pixels and colours passed |
| hors-render-v2 | ram | 20.39130 | 59.856 | 62.594 | 985,024 | pixels and colours passed |
| hors-renderer-v3 | fps | 22.70164 | 61.208 | 62.023 | 1,009,648 | pixels and colours passed |
| hors-renderer-v3 | ram | 22.70165 | 61.152 | 62.558 | 1,009,648 | pixels and colours passed |
| hors-v4-ef | fps | 22.70164 | 61.208 | 62.023 | 1,009,648 | pixels and colours passed |
| hors-v4-ef | ram | 22.70165 | 61.152 | 62.558 | 1,009,648 | pixels and colours passed |
| hors-v5-c1 | fps | 22.80432 | 60.791 | 62.377 | 1,001,440 | pixels and colours passed |
| hors-v5-c1 | ram | 22.70163 | 61.165 | 62.506 | 1,001,440 | pixels and colours passed |
| hors-v5-c2 | fps | 22.80432 | 60.791 | 62.377 | 1,001,440 | pixels and colours passed |
| hors-v5-c2 | ram | 22.70163 | 61.165 | 62.506 | 1,001,440 | pixels and colours passed |

## DRAGON WIREFRAME

128 pictures.

| Renderer | Preference | Average FPS | P95 ms | Worst ms | CRT bytes | Result |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| yunroll-cart-v10 | fps | N/A | N/A | N/A | N/A | frame block 10492 exceeds 8192-byte staging buffer |
| yunroll-cart-v10 | ram | N/A | N/A | N/A | N/A | frame block 10492 exceeds 8192-byte staging buffer |
| hors-render-v2 | fps | 19.38737 | 59.856 | 79.798 | 328,384 | pixels and colours passed |
| hors-render-v2 | ram | 19.38807 | 59.856 | 79.802 | 328,384 | pixels and colours passed |
| hors-renderer-v3 | fps | 19.38737 | 59.856 | 79.798 | 328,384 | pixels and colours passed |
| hors-renderer-v3 | ram | 19.38807 | 59.856 | 79.802 | 328,384 | pixels and colours passed |
| hors-v4-ef | fps | 19.38737 | 59.856 | 79.798 | 328,384 | pixels and colours passed |
| hors-v4-ef | ram | 19.38807 | 59.856 | 79.802 | 328,384 | pixels and colours passed |
| hors-v5-c1 | fps | 19.45435 | 59.856 | 79.805 | 328,384 | pixels and colours passed |
| hors-v5-c1 | ram | 19.38702 | 60.157 | 79.804 | 328,384 | pixels and colours passed |
| hors-v5-c2 | fps | 19.45435 | 59.856 | 79.805 | 328,384 | pixels and colours passed |
| hors-v5-c2 | ram | 19.38702 | 60.157 | 79.804 | 328,384 | pixels and colours passed |

## DRAGON METALLIC

128 pictures.

| Renderer | Preference | Average FPS | P95 ms | Worst ms | CRT bytes | Result |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| yunroll-cart-v10 | fps | 11.25039 | 119.700 | 119.706 | 385,840 | pixels and colours passed |
| yunroll-cart-v10 | ram | 11.25042 | 119.698 | 119.706 | 385,840 | pixels and colours passed |
| hors-render-v2 | fps | 11.45249 | 99.757 | 119.704 | 385,840 | pixels and colours passed |
| hors-render-v2 | ram | 11.45193 | 119.697 | 119.705 | 385,840 | pixels and colours passed |
| hors-renderer-v3 | fps | 14.26455 | 80.827 | 84.056 | 377,632 | pixels and colours passed |
| hors-renderer-v3 | ram | 14.26297 | 80.885 | 82.728 | 377,632 | pixels and colours passed |
| hors-v4-ef | fps | 14.26455 | 80.827 | 84.056 | 377,632 | pixels and colours passed |
| hors-v4-ef | ram | 14.26297 | 80.885 | 82.728 | 377,632 | pixels and colours passed |
| hors-v5-c1 | fps | 14.36595 | 79.805 | 82.523 | 377,632 | pixels and colours passed |
| hors-v5-c1 | ram | 14.36198 | 79.805 | 82.503 | 377,632 | pixels and colours passed |
| hors-v5-c2 | fps | 14.36595 | 79.805 | 82.523 | 377,632 | pixels and colours passed |
| hors-v5-c2 | ram | 14.36198 | 79.805 | 82.503 | 377,632 | pixels and colours passed |

## SAKU SOLID LOGO ONLY

48 pictures.

| Renderer | Preference | Average FPS | P95 ms | Worst ms | CRT bytes | Result |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| yunroll-cart-v10 | fps | 36.96574 | 40.461 | 41.162 | 90,352 | pixels and colours passed |
| yunroll-cart-v10 | ram | 36.96550 | 40.461 | 41.093 | 90,352 | pixels and colours passed |
| hors-render-v2 | fps | 38.80824 | 41.211 | 41.504 | 90,352 | pixels and colours passed |
| hors-render-v2 | ram | 38.77784 | 41.196 | 41.485 | 90,352 | pixels and colours passed |
| hors-renderer-v3 | fps | 32.01002 | 41.498 | 42.593 | 106,768 | pixels and colours passed |
| hors-renderer-v3 | ram | 31.94796 | 41.283 | 42.644 | 106,768 | pixels and colours passed |
| hors-v4-ef | fps | 32.01002 | 41.498 | 42.593 | 106,768 | pixels and colours passed |
| hors-v4-ef | ram | 31.94796 | 41.283 | 42.644 | 106,768 | pixels and colours passed |
| hors-v5-c1 | fps | 32.21358 | 41.216 | 42.563 | 106,768 | pixels and colours passed |
| hors-v5-c1 | ram | 32.14516 | 41.254 | 42.613 | 106,768 | pixels and colours passed |
| hors-v5-c2 | fps | 38.77259 | 41.142 | 41.685 | 90,352 | pixels and colours passed |
| hors-v5-c2 | ram | 38.77524 | 41.142 | 41.685 | 90,352 | pixels and colours passed |

## SAKU GRADIENT LOGO ONLY

48 pictures.

| Renderer | Preference | Average FPS | P95 ms | Worst ms | CRT bytes | Result |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| yunroll-cart-v10 | fps | 31.10677 | 40.646 | 43.451 | 98,560 | pixels and colours passed |
| yunroll-cart-v10 | ram | 31.13813 | 40.728 | 42.724 | 98,560 | pixels and colours passed |
| hors-render-v2 | fps | 32.01272 | 41.319 | 44.248 | 98,560 | pixels and colours passed |
| hors-render-v2 | ram | 31.94015 | 42.048 | 42.687 | 98,560 | pixels and colours passed |
| hors-renderer-v3 | fps | 31.20856 | 41.168 | 42.650 | 106,768 | pixels and colours passed |
| hors-renderer-v3 | ram | 31.14104 | 41.484 | 42.606 | 106,768 | pixels and colours passed |
| hors-v4-ef | fps | 31.20856 | 41.168 | 42.650 | 106,768 | pixels and colours passed |
| hors-v4-ef | ram | 31.14104 | 41.484 | 42.606 | 106,768 | pixels and colours passed |
| hors-v5-c1 | fps | 31.33467 | 41.527 | 42.638 | 106,768 | pixels and colours passed |
| hors-v5-c1 | ram | 31.24000 | 41.499 | 42.621 | 106,768 | pixels and colours passed |
| hors-v5-c2 | fps | 32.10927 | 41.314 | 42.379 | 98,560 | pixels and colours passed |
| hors-v5-c2 | ram | 32.03902 | 41.323 | 42.159 | 98,560 | pixels and colours passed |

[Raw public evidence](benchmarks/release-0.8.2/public-family.json) · [Reproduce](PUBLIC_BENCHMARKS.md) · [Full original renderer history](PUBLIC_RENDERER_COMPARISON.md)

The full historical chart remains separate and includes step, bytechunk, yunroll and every streamed generation. Capacity failures there remain N/A with reasons. Two fresh family rows also exceed capacity and remain visible above; older renderers are retained in the historical comparison.
