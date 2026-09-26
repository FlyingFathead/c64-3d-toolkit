# Public renderer comparison: checkpoint 005

PAL VICE 3.10, default machine settings, sound disabled, seed 1. Common V9 normal PLAY ALL; three ten-second visits per case, uncapped. All authored/frozen pictures and colours remain present. These are comparisons between current implementations, not old-release regression measurements.

The canonical twelve-entry corpus shares one cart per method. Each Dragon/SAKU case has its own cart. SAKU uses the standalone 48-frame solid and gradient logo rotations: no starfield, cards, interactive colour controls or exhibition scheduler. Every method has the same static benchmark HUD. Dragon uses all 128 published orientations. Saved byte-clear plans are rebuilt into ordinary geometry cell spans before each backend applies its own lossless encoding; complete bitmap/colour hashes must remain unchanged.

## Average FPS leaders

| Case | Pictures | Fastest measured method / preference | Average FPS | V2 FPS | V4 FPS | V5 FPS |
| --- | ---: | --- | ---: | ---: | ---: | ---: |
| TORUS | 32 | hors-v5-ef / ram | 17.782 | 17.680 | 17.680 | 17.780 |
| TORUS DENSE | 32 | hors-v5-ef / fps | 17.380 | 17.179 | 17.179 | 17.380 |
| CUBE | 36 | yunroll / fps | 30.269 | 30.031 | 30.031 | 30.032 |
| SPHERE | 24 | hors-v5-ef / ram | 17.480 | 17.379 | 17.379 | 17.478 |
| HORSE HEAD | 32 | hors-v5-ef / ram | 29.434 | 29.335 | 29.335 | 29.432 |
| SUNFLOWER TORUS | 28 | hors-v5-ef / ram | 28.931 | 28.730 | 28.730 | 28.927 |
| SUNFLOWER COLOR | 20 | hors-v5-ef / fps | 22.733 | 20.891 | 22.701 | 22.733 |
| SPACE HORSE SPIN | 24 | hors-v5-ef / fps | 19.288 | 19.083 | 19.086 | 19.288 |
| SPACE HORSE CRAWL | 32 | hors-renderer-v3 / ram | 38.278 | 38.275 | 38.273 | 38.271 |
| FALLING CUBES | 18 | hors-v5-ef / ram | 21.397 | 20.892 | 21.295 | 21.396 |
| HORSE HEAD HIFI | 128 | hors-v5-ef / ram | 23.307 | 21.495 | 23.105 | 23.204 |
| SUNFLOWER TORUS HIFI | 128 | hors-v5-ef / fps | 22.804 | 20.394 | 22.702 | 22.804 |
| DRAGON WIREFRAME | 128 | hors-v5-ef / fps | 19.454 | 19.387 | 19.387 | 19.454 |
| DRAGON METALLIC | 128 | hors-v5-ef / fps | 14.366 | 11.452 | 14.265 | 14.366 |
| SAKU SOLID LOGO ONLY | 48 | hors-render-v2 / fps | 38.808 | 38.808 | 32.010 | 32.214 |
| SAKU GRADIENT LOGO ONLY | 48 | hors-render-v2 / fps | 32.013 | 32.013 | 31.209 | 31.335 |

Highest measured average FPS is marked below; small differences may reflect interval/rotation phase. Do not average unlike workloads or mix these uncapped rates with four-refresh native scene contests. High/low values describe observed display intervals, not sustained rates. CRT bytes describe the complete cart, including other corpus entries where applicable. N/A records a confirmed capacity limit; FAIL is a build/verification error.

## TORUS

32 pictures; picture SHA-256 `68c11d497d398ec694254c43e6097b45ad28ae3a2201a69fe5d9889ea658ac8a`.

| Renderer | Preference | High FPS | Average FPS | Low FPS | P95 ms | Worst ms | CRT bytes | Result / reason |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| step | fps | 25.063 | 12.288 | 10.023 | 99.754 | 99.767 | 500,752 | pixels and colours passed |
| bytechunk | fps | 25.065 | 13.862 | 10.023 | 99.748 | 99.767 | 500,752 | pixels and colours passed |
| yunroll | fps | 25.065 | 14.096 | 10.025 | 79.806 | 99.756 | 500,752 | pixels and colours passed |
| yunroll-cart | fps | 25.065 | 14.096 | 10.025 | 79.806 | 99.756 | 500,752 | pixels and colours passed |
| yunroll-cart-v2 | fps | 17.057 | 11.250 | 8.354 | 102.733 | 119.700 | 968,608 | pixels and colours passed |
| yunroll-cart-v3 | fps | 23.696 | 12.054 | 9.838 | 100.134 | 101.652 | 968,608 | pixels and colours passed |
| yunroll-cart-v4 | fps | 23.516 | 12.054 | 9.863 | 99.753 | 101.393 | 968,608 | pixels and colours passed |
| yunroll-cart-v5 | fps | 24.472 | 12.355 | 9.881 | 99.752 | 101.207 | 927,568 | pixels and colours passed |
| yunroll-cart-v6 | fps | 25.871 | 12.757 | 9.678 | 99.755 | 103.325 | 927,568 | pixels and colours passed |
| yunroll-cart-v7 | fps | 27.307 | 13.460 | 9.766 | 99.752 | 102.396 | 804,448 | pixels and colours passed |
| yunroll-cart-v8 | fps | 27.307 | 13.460 | 9.766 | 99.752 | 102.396 | 771,616 | pixels and colours passed |
| yunroll-cart-v9 | fps | 27.064 | 13.460 | 9.722 | 99.752 | 102.859 | 771,616 | pixels and colours passed |
| yunroll-cart-v10 | fps | 27.023 | 16.072 | 12.084 | 79.804 | 82.756 | 985,024 | pixels and colours passed |
| yunroll-cart-v7 | ram | 27.014 | 12.858 | 9.742 | 99.753 | 102.650 | 804,448 | pixels and colours passed |
| yunroll-cart-v8 | ram | 27.014 | 12.858 | 9.742 | 99.753 | 102.650 | 771,616 | pixels and colours passed |
| yunroll-cart-v9 | ram | 26.800 | 12.858 | 9.715 | 99.753 | 102.931 | 771,616 | pixels and colours passed |
| yunroll-cart-v10 | ram | 27.043 | 16.072 | 12.035 | 79.803 | 83.088 | 985,024 | pixels and colours passed |
| hors-render-v2 | fps | 27.179 | 17.680 | 12.087 | 79.801 | 82.734 | 985,024 | pixels and colours passed |
| hors-render-v2 | ram | 27.205 | 17.678 | 12.004 | 79.801 | 83.306 | 985,024 | pixels and colours passed |
| hors-renderer-v3 | fps | 27.179 | 17.680 | 12.087 | 79.801 | 82.734 | 1,009,648 | pixels and colours passed |
| hors-renderer-v3 | ram | 27.205 | 17.678 | 12.004 | 79.801 | 83.306 | 1,009,648 | pixels and colours passed |
| hors-render-v2-beta1 | fps | 27.179 | 17.680 | 12.087 | 79.801 | 82.734 | 985,024 | pixels and colours passed |
| hors-render-v2-beta1 | ram | 27.205 | 17.678 | 12.004 | 79.801 | 83.306 | 985,024 | pixels and colours passed |
| hors-v4-ef | fps | 27.179 | 17.680 | 12.087 | 79.801 | 82.734 | 1,009,648 | pixels and colours passed |
| hors-v4-ef | ram | 27.205 | 17.678 | 12.004 | 79.801 | 83.306 | 1,009,648 | pixels and colours passed |
| hors-v5-ef | fps | 27.205 | 17.780 | 12.529 | 79.800 | 79.812 | 1,001,440 | pixels and colours passed |
| hors-v5-ef | ram | 27.023 | 17.782 | 12.170 | 79.801 | 82.167 | 1,001,440 | **WINNER**; pixels and colours passed |

## TORUS DENSE

32 pictures; picture SHA-256 `209e4c9d1dda249a62c76219812ce66e8c565352728691c7060e75bdbda38f68`.

| Renderer | Preference | High FPS | Average FPS | Low FPS | P95 ms | Worst ms | CRT bytes | Result / reason |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| step | fps | 25.073 | 10.949 | 8.353 | 119.703 | 119.719 | 500,752 | pixels and colours passed |
| bytechunk | fps | 25.064 | 12.188 | 8.354 | 99.755 | 119.702 | 500,752 | pixels and colours passed |
| yunroll | fps | 25.065 | 12.422 | 10.024 | 99.755 | 99.763 | 500,752 | pixels and colours passed |
| yunroll-cart | fps | 25.065 | 12.422 | 10.024 | 99.755 | 99.763 | 500,752 | pixels and colours passed |
| yunroll-cart-v2 | fps | 16.900 | 9.840 | 8.217 | 119.704 | 121.705 | 968,608 | pixels and colours passed |
| yunroll-cart-v3 | fps | 23.549 | 10.648 | 8.354 | 118.559 | 119.707 | 968,608 | pixels and colours passed |
| yunroll-cart-v4 | fps | 17.170 | 10.748 | 8.354 | 117.886 | 119.703 | 968,608 | pixels and colours passed |
| yunroll-cart-v5 | fps | 16.710 | 10.949 | 8.354 | 118.366 | 119.702 | 927,568 | pixels and colours passed |
| yunroll-cart-v6 | fps | 27.596 | 11.250 | 8.353 | 102.907 | 119.720 | 927,568 | pixels and colours passed |
| yunroll-cart-v7 | fps | 27.214 | 12.154 | 9.708 | 99.756 | 103.006 | 804,448 | pixels and colours passed |
| yunroll-cart-v8 | fps | 27.214 | 12.154 | 9.708 | 99.756 | 103.006 | 771,616 | pixels and colours passed |
| yunroll-cart-v9 | fps | 27.285 | 12.154 | 9.938 | 99.755 | 100.627 | 771,616 | pixels and colours passed |
| yunroll-cart-v10 | fps | 27.044 | 15.771 | 12.202 | 79.804 | 81.951 | 985,024 | pixels and colours passed |
| yunroll-cart-v7 | ram | 26.822 | 11.552 | 8.354 | 101.910 | 119.705 | 804,448 | pixels and colours passed |
| yunroll-cart-v8 | ram | 26.822 | 11.552 | 8.354 | 101.910 | 119.705 | 771,616 | pixels and colours passed |
| yunroll-cart-v9 | ram | 26.727 | 11.552 | 8.354 | 99.758 | 119.703 | 771,616 | pixels and colours passed |
| yunroll-cart-v10 | ram | 26.782 | 15.774 | 12.043 | 79.804 | 83.035 | 985,024 | pixels and colours passed |
| hors-render-v2 | fps | 27.117 | 17.179 | 12.530 | 79.801 | 79.806 | 985,024 | pixels and colours passed |
| hors-render-v2 | ram | 25.538 | 17.178 | 12.530 | 79.803 | 79.805 | 985,024 | pixels and colours passed |
| hors-renderer-v3 | fps | 27.117 | 17.179 | 12.530 | 79.801 | 79.806 | 1,009,648 | pixels and colours passed |
| hors-renderer-v3 | ram | 25.538 | 17.178 | 12.530 | 79.803 | 79.805 | 1,009,648 | pixels and colours passed |
| hors-render-v2-beta1 | fps | 27.117 | 17.179 | 12.530 | 79.801 | 79.806 | 985,024 | pixels and colours passed |
| hors-render-v2-beta1 | ram | 25.538 | 17.178 | 12.530 | 79.803 | 79.805 | 985,024 | pixels and colours passed |
| hors-v4-ef | fps | 27.117 | 17.179 | 12.530 | 79.801 | 79.806 | 1,009,648 | pixels and colours passed |
| hors-v4-ef | ram | 25.538 | 17.178 | 12.530 | 79.803 | 79.805 | 1,009,648 | pixels and colours passed |
| hors-v5-ef | fps | 27.000 | 17.380 | 12.530 | 79.802 | 79.806 | 1,001,440 | **WINNER**; pixels and colours passed |
| hors-v5-ef | ram | 26.581 | 17.377 | 12.530 | 79.801 | 79.805 | 1,001,440 | pixels and colours passed |

## CUBE

36 pictures; picture SHA-256 `e958784c872795c561fba3be38efe033bbf51bf911e0198e16896e4482a65cbb`.

| Renderer | Preference | High FPS | Average FPS | Low FPS | P95 ms | Worst ms | CRT bytes | Result / reason |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| step | fps | 50.137 | 26.452 | 16.707 | 39.905 | 59.855 | 500,752 | pixels and colours passed |
| bytechunk | fps | 50.170 | 29.398 | 25.050 | 39.905 | 39.920 | 500,752 | pixels and colours passed |
| yunroll | fps | 50.163 | 30.269 | 25.052 | 39.905 | 39.917 | 500,752 | **WINNER**; pixels and colours passed |
| yunroll-cart | fps | 50.163 | 30.269 | 25.052 | 39.905 | 39.917 | 500,752 | **WINNER**; pixels and colours passed |
| yunroll-cart-v2 | fps | 46.055 | 23.003 | 16.707 | 59.757 | 59.856 | 968,608 | pixels and colours passed |
| yunroll-cart-v3 | fps | 50.165 | 24.718 | 16.708 | 58.280 | 59.851 | 968,608 | pixels and colours passed |
| yunroll-cart-v4 | fps | 50.127 | 24.718 | 16.704 | 58.587 | 59.866 | 968,608 | pixels and colours passed |
| yunroll-cart-v5 | fps | 50.130 | 25.514 | 16.709 | 42.771 | 59.849 | 927,568 | pixels and colours passed |
| yunroll-cart-v6 | fps | 55.980 | 26.820 | 16.707 | 41.899 | 59.855 | 927,568 | pixels and colours passed |
| yunroll-cart-v7 | fps | 55.554 | 26.820 | 16.708 | 41.712 | 59.852 | 804,448 | pixels and colours passed |
| yunroll-cart-v8 | fps | 55.554 | 26.820 | 16.708 | 41.712 | 59.852 | 771,616 | pixels and colours passed |
| yunroll-cart-v9 | fps | 55.840 | 26.820 | 16.708 | 41.882 | 59.851 | 771,616 | pixels and colours passed |
| yunroll-cart-v10 | fps | 50.817 | 27.423 | 16.642 | 40.872 | 60.087 | 985,024 | pixels and colours passed |
| yunroll-cart-v7 | ram | 53.306 | 24.610 | 16.049 | 59.853 | 62.308 | 804,448 | pixels and colours passed |
| yunroll-cart-v8 | ram | 53.306 | 24.610 | 16.049 | 59.853 | 62.308 | 771,616 | pixels and colours passed |
| yunroll-cart-v9 | ram | 53.398 | 24.610 | 16.175 | 59.854 | 61.823 | 771,616 | pixels and colours passed |
| yunroll-cart-v10 | ram | 50.854 | 27.423 | 16.685 | 41.221 | 59.934 | 985,024 | pixels and colours passed |
| hors-render-v2 | fps | 55.929 | 30.031 | 23.159 | 41.837 | 43.180 | 985,024 | pixels and colours passed |
| hors-render-v2 | ram | 55.544 | 30.037 | 23.129 | 41.470 | 43.236 | 985,024 | pixels and colours passed |
| hors-renderer-v3 | fps | 55.929 | 30.031 | 23.159 | 41.837 | 43.180 | 1,009,648 | pixels and colours passed |
| hors-renderer-v3 | ram | 55.544 | 30.037 | 23.129 | 41.470 | 43.236 | 1,009,648 | pixels and colours passed |
| hors-render-v2-beta1 | fps | 55.929 | 30.031 | 23.159 | 41.837 | 43.180 | 985,024 | pixels and colours passed |
| hors-render-v2-beta1 | ram | 55.544 | 30.037 | 23.129 | 41.470 | 43.236 | 985,024 | pixels and colours passed |
| hors-v4-ef | fps | 55.929 | 30.031 | 23.159 | 41.837 | 43.180 | 1,009,648 | pixels and colours passed |
| hors-v4-ef | ram | 55.544 | 30.037 | 23.129 | 41.470 | 43.236 | 1,009,648 | pixels and colours passed |
| hors-v5-ef | fps | 54.392 | 30.032 | 23.311 | 41.681 | 42.899 | 1,001,440 | pixels and colours passed |
| hors-v5-ef | ram | 54.560 | 30.134 | 24.082 | 41.229 | 41.526 | 1,001,440 | pixels and colours passed |

## SPHERE

24 pictures; picture SHA-256 `d6c8247156af7016e014957ea1cda02136808f5dadddbfc14cce4b2d33ce0eb9`.

| Renderer | Preference | High FPS | Average FPS | Low FPS | P95 ms | Worst ms | CRT bytes | Result / reason |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| step | fps | 25.051 | 13.628 | 12.528 | 79.805 | 79.819 | 500,752 | pixels and colours passed |
| bytechunk | fps | 25.064 | 15.000 | 12.528 | 79.803 | 79.822 | 500,752 | pixels and colours passed |
| yunroll | fps | 25.062 | 15.503 | 12.530 | 79.802 | 79.806 | 500,752 | pixels and colours passed |
| yunroll-cart | fps | 25.062 | 15.503 | 12.530 | 79.802 | 79.806 | 500,752 | pixels and colours passed |
| yunroll-cart-v2 | fps | 16.710 | 12.255 | 10.025 | 98.078 | 99.753 | 968,608 | pixels and colours passed |
| yunroll-cart-v3 | fps | 16.926 | 13.159 | 10.025 | 81.548 | 99.752 | 968,608 | pixels and colours passed |
| yunroll-cart-v4 | fps | 16.974 | 13.159 | 10.275 | 81.176 | 97.323 | 968,608 | pixels and colours passed |
| yunroll-cart-v5 | fps | 23.916 | 13.661 | 12.041 | 80.010 | 83.051 | 927,568 | pixels and colours passed |
| yunroll-cart-v6 | fps | 25.062 | 14.264 | 11.933 | 82.775 | 83.804 | 927,568 | pixels and colours passed |
| yunroll-cart-v7 | fps | 17.997 | 14.671 | 11.892 | 83.052 | 84.089 | 804,448 | pixels and colours passed |
| yunroll-cart-v8 | fps | 17.997 | 14.671 | 11.892 | 83.052 | 84.089 | 771,616 | pixels and colours passed |
| yunroll-cart-v9 | fps | 18.006 | 14.671 | 11.889 | 82.852 | 84.111 | 771,616 | pixels and colours passed |
| yunroll-cart-v10 | fps | 25.111 | 15.871 | 11.876 | 82.982 | 84.202 | 985,024 | pixels and colours passed |
| yunroll-cart-v7 | ram | 17.900 | 13.460 | 11.907 | 83.204 | 83.985 | 804,448 | pixels and colours passed |
| yunroll-cart-v8 | ram | 17.900 | 13.460 | 11.907 | 83.204 | 83.985 | 771,616 | pixels and colours passed |
| yunroll-cart-v9 | ram | 18.018 | 13.460 | 11.927 | 82.906 | 83.841 | 771,616 | pixels and colours passed |
| yunroll-cart-v10 | ram | 25.165 | 15.871 | 11.868 | 79.819 | 84.258 | 985,024 | pixels and colours passed |
| hors-render-v2 | fps | 28.084 | 17.379 | 15.530 | 63.105 | 64.391 | 985,024 | pixels and colours passed |
| hors-render-v2 | ram | 28.168 | 17.379 | 15.564 | 63.091 | 64.250 | 985,024 | pixels and colours passed |
| hors-renderer-v3 | fps | 28.084 | 17.379 | 15.530 | 63.105 | 64.391 | 1,009,648 | pixels and colours passed |
| hors-renderer-v3 | ram | 28.168 | 17.379 | 15.564 | 63.091 | 64.250 | 1,009,648 | pixels and colours passed |
| hors-render-v2-beta1 | fps | 28.084 | 17.379 | 15.530 | 63.105 | 64.391 | 985,024 | pixels and colours passed |
| hors-render-v2-beta1 | ram | 28.168 | 17.379 | 15.564 | 63.091 | 64.250 | 985,024 | pixels and colours passed |
| hors-v4-ef | fps | 28.084 | 17.379 | 15.530 | 63.105 | 64.391 | 1,009,648 | pixels and colours passed |
| hors-v4-ef | ram | 28.168 | 17.379 | 15.564 | 63.091 | 64.250 | 1,009,648 | pixels and colours passed |
| hors-v5-ef | fps | 28.129 | 17.478 | 15.575 | 62.882 | 64.204 | 1,001,440 | pixels and colours passed |
| hors-v5-ef | ram | 28.140 | 17.480 | 15.572 | 62.607 | 64.216 | 1,001,440 | **WINNER**; pixels and colours passed |

## HORSE HEAD

32 pictures; picture SHA-256 `86eda922e658bf4b49f639ac97891a320e391917b4847718ecc865f42a144d9d`.

| Renderer | Preference | High FPS | Average FPS | Low FPS | P95 ms | Worst ms | CRT bytes | Result / reason |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| step | fps | 16.710 | 12.154 | 10.023 | 99.753 | 99.768 | 500,752 | pixels and colours passed |
| bytechunk | fps | 25.062 | 12.925 | 10.025 | 99.751 | 99.755 | 500,752 | pixels and colours passed |
| yunroll | fps | 25.062 | 13.226 | 10.024 | 99.748 | 99.757 | 500,752 | pixels and colours passed |
| yunroll-cart | fps | 25.062 | 13.226 | 10.024 | 99.748 | 99.757 | 500,752 | pixels and colours passed |
| yunroll-cart-v2 | fps | 16.579 | 10.547 | 8.413 | 116.076 | 118.868 | 968,608 | pixels and colours passed |
| yunroll-cart-v3 | fps | 16.708 | 11.652 | 9.637 | 100.394 | 103.765 | 968,608 | pixels and colours passed |
| yunroll-cart-v4 | fps | 16.708 | 11.753 | 9.935 | 99.753 | 100.658 | 968,608 | pixels and colours passed |
| yunroll-cart-v5 | fps | 17.132 | 12.456 | 9.786 | 99.505 | 102.183 | 927,568 | pixels and colours passed |
| yunroll-cart-v6 | fps | 17.556 | 12.858 | 9.754 | 101.673 | 102.518 | 927,568 | pixels and colours passed |
| yunroll-cart-v7 | fps | 17.755 | 13.762 | 9.867 | 81.873 | 101.349 | 804,448 | pixels and colours passed |
| yunroll-cart-v8 | fps | 17.755 | 13.762 | 9.867 | 81.873 | 101.349 | 771,616 | pixels and colours passed |
| yunroll-cart-v9 | fps | 25.898 | 13.862 | 9.773 | 82.391 | 102.322 | 771,616 | pixels and colours passed |
| yunroll-cart-v10 | fps | 52.457 | 27.422 | 16.549 | 41.979 | 60.425 | 985,024 | pixels and colours passed |
| yunroll-cart-v7 | ram | 25.061 | 12.757 | 9.750 | 100.463 | 102.564 | 804,448 | pixels and colours passed |
| yunroll-cart-v8 | ram | 25.061 | 12.757 | 9.750 | 100.463 | 102.564 | 771,616 | pixels and colours passed |
| yunroll-cart-v9 | ram | 17.511 | 12.757 | 9.615 | 101.090 | 104.003 | 771,616 | pixels and colours passed |
| yunroll-cart-v10 | ram | 52.577 | 27.423 | 16.598 | 42.230 | 60.250 | 985,024 | pixels and colours passed |
| hors-render-v2 | fps | 54.554 | 29.335 | 23.895 | 41.039 | 41.850 | 985,024 | pixels and colours passed |
| hors-render-v2 | ram | 54.760 | 29.330 | 23.660 | 41.155 | 42.266 | 985,024 | pixels and colours passed |
| hors-renderer-v3 | fps | 54.554 | 29.335 | 23.895 | 41.039 | 41.850 | 1,009,648 | pixels and colours passed |
| hors-renderer-v3 | ram | 54.760 | 29.330 | 23.660 | 41.155 | 42.266 | 1,009,648 | pixels and colours passed |
| hors-render-v2-beta1 | fps | 54.554 | 29.335 | 23.895 | 41.039 | 41.850 | 985,024 | pixels and colours passed |
| hors-render-v2-beta1 | ram | 54.760 | 29.330 | 23.660 | 41.155 | 42.266 | 985,024 | pixels and colours passed |
| hors-v4-ef | fps | 54.554 | 29.335 | 23.895 | 41.039 | 41.850 | 1,009,648 | pixels and colours passed |
| hors-v4-ef | ram | 54.760 | 29.330 | 23.660 | 41.155 | 42.266 | 1,009,648 | pixels and colours passed |
| hors-v5-ef | fps | 54.919 | 29.432 | 24.117 | 41.069 | 41.464 | 1,001,440 | pixels and colours passed |
| hors-v5-ef | ram | 54.791 | 29.434 | 24.039 | 41.054 | 41.599 | 1,001,440 | **WINNER**; pixels and colours passed |

## SUNFLOWER TORUS

28 pictures; picture SHA-256 `90f0c907552fd37ec0f19cd9fa2947081e5079803cea682ee5b8edb5bde50170`.

| Renderer | Preference | High FPS | Average FPS | Low FPS | P95 ms | Worst ms | CRT bytes | Result / reason |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| step | fps | 16.710 | 11.016 | 8.354 | 99.756 | 119.707 | 500,752 | pixels and colours passed |
| bytechunk | fps | 16.709 | 11.351 | 10.024 | 99.754 | 99.757 | 500,752 | pixels and colours passed |
| yunroll | fps | 16.710 | 11.552 | 10.023 | 99.755 | 99.770 | 500,752 | pixels and colours passed |
| yunroll-cart | fps | 16.710 | 11.552 | 10.023 | 99.755 | 99.770 | 500,752 | pixels and colours passed |
| yunroll-cart-v2 | fps | 12.606 | 9.442 | 8.173 | 120.165 | 122.357 | 968,608 | pixels and colours passed |
| yunroll-cart-v3 | fps | 16.555 | 10.246 | 8.354 | 117.301 | 119.702 | 968,608 | pixels and colours passed |
| yunroll-cart-v4 | fps | 16.476 | 10.346 | 8.354 | 116.915 | 119.704 | 968,608 | pixels and colours passed |
| yunroll-cart-v5 | fps | 16.708 | 10.949 | 9.956 | 99.756 | 100.438 | 927,568 | pixels and colours passed |
| yunroll-cart-v6 | fps | 25.076 | 11.150 | 9.745 | 101.289 | 102.617 | 927,568 | pixels and colours passed |
| yunroll-cart-v7 | fps | 25.546 | 12.154 | 9.752 | 101.472 | 102.543 | 804,448 | pixels and colours passed |
| yunroll-cart-v8 | fps | 25.546 | 12.154 | 9.752 | 101.472 | 102.543 | 771,616 | pixels and colours passed |
| yunroll-cart-v9 | fps | 25.455 | 12.154 | 9.739 | 101.623 | 102.677 | 771,616 | pixels and colours passed |
| yunroll-cart-v10 | fps | 53.219 | 27.122 | 16.249 | 60.050 | 61.544 | 985,024 | pixels and colours passed |
| yunroll-cart-v7 | ram | 16.895 | 11.150 | 8.309 | 101.859 | 120.359 | 804,448 | pixels and colours passed |
| yunroll-cart-v8 | ram | 16.895 | 11.150 | 8.309 | 101.859 | 120.359 | 771,616 | pixels and colours passed |
| yunroll-cart-v9 | ram | 25.063 | 11.150 | 9.709 | 101.538 | 102.994 | 771,616 | pixels and colours passed |
| yunroll-cart-v10 | ram | 53.277 | 27.122 | 16.349 | 59.934 | 61.167 | 985,024 | pixels and colours passed |
| hors-render-v2 | fps | 54.329 | 28.730 | 16.300 | 41.550 | 61.348 | 985,024 | pixels and colours passed |
| hors-render-v2 | ram | 54.782 | 28.729 | 16.277 | 60.220 | 61.437 | 985,024 | pixels and colours passed |
| hors-renderer-v3 | fps | 54.329 | 28.730 | 16.300 | 41.550 | 61.348 | 1,009,648 | pixels and colours passed |
| hors-renderer-v3 | ram | 54.782 | 28.729 | 16.277 | 60.220 | 61.437 | 1,009,648 | pixels and colours passed |
| hors-render-v2-beta1 | fps | 54.329 | 28.730 | 16.300 | 41.550 | 61.348 | 985,024 | pixels and colours passed |
| hors-render-v2-beta1 | ram | 54.782 | 28.729 | 16.277 | 60.220 | 61.437 | 985,024 | pixels and colours passed |
| hors-v4-ef | fps | 54.329 | 28.730 | 16.300 | 41.550 | 61.348 | 1,009,648 | pixels and colours passed |
| hors-v4-ef | ram | 54.782 | 28.729 | 16.277 | 60.220 | 61.437 | 1,009,648 | pixels and colours passed |
| hors-v5-ef | fps | 54.907 | 28.927 | 16.269 | 59.980 | 61.467 | 1,001,440 | pixels and colours passed |
| hors-v5-ef | ram | 54.833 | 28.931 | 16.242 | 59.906 | 61.567 | 1,001,440 | **WINNER**; pixels and colours passed |

## SUNFLOWER COLOR

20 pictures; picture SHA-256 `953a9b1839033d8507da0038304b14cd9a7ba262247753b733f7dc1bf24881ec`.

| Renderer | Preference | High FPS | Average FPS | Low FPS | P95 ms | Worst ms | CRT bytes | Result / reason |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| step | fps | 16.708 | 9.677 | 8.353 | 119.704 | 119.717 | 500,752 | pixels and colours passed |
| bytechunk | fps | 16.709 | 9.978 | 8.354 | 119.702 | 119.707 | 500,752 | pixels and colours passed |
| yunroll | fps | 16.708 | 10.179 | 8.353 | 119.702 | 119.714 | 500,752 | pixels and colours passed |
| yunroll-cart | fps | 16.708 | 10.179 | 8.353 | 119.702 | 119.714 | 500,752 | pixels and colours passed |
| yunroll-cart-v2 | fps | 10.285 | 8.036 | 6.919 | 140.768 | 144.524 | 968,608 | pixels and colours passed |
| yunroll-cart-v3 | fps | 12.639 | 8.840 | 7.161 | 122.772 | 139.653 | 968,608 | pixels and colours passed |
| yunroll-cart-v4 | fps | 12.531 | 8.940 | 7.322 | 121.704 | 136.566 | 968,608 | pixels and colours passed |
| yunroll-cart-v5 | fps | 16.363 | 9.342 | 8.111 | 121.234 | 123.288 | 927,568 | pixels and colours passed |
| yunroll-cart-v6 | fps | 16.709 | 9.744 | 8.320 | 119.704 | 120.195 | 927,568 | pixels and colours passed |
| yunroll-cart-v7 | fps | 17.603 | 10.447 | 8.354 | 119.701 | 119.707 | 804,448 | pixels and colours passed |
| yunroll-cart-v8 | fps | 17.603 | 10.447 | 8.354 | 119.701 | 119.707 | 771,616 | pixels and colours passed |
| yunroll-cart-v9 | fps | 16.710 | 10.547 | 8.354 | 119.702 | 119.706 | 771,616 | pixels and colours passed |
| yunroll-cart-v10 | fps | 53.036 | 19.991 | 12.531 | 60.048 | 79.801 | 985,024 | pixels and colours passed |
| yunroll-cart-v7 | ram | 17.644 | 9.744 | 8.138 | 119.829 | 122.877 | 804,448 | pixels and colours passed |
| yunroll-cart-v8 | ram | 17.644 | 9.744 | 8.138 | 119.829 | 122.877 | 771,616 | pixels and colours passed |
| yunroll-cart-v9 | ram | 16.709 | 9.744 | 8.177 | 120.994 | 122.292 | 771,616 | pixels and colours passed |
| yunroll-cart-v10 | ram | 52.913 | 19.990 | 12.531 | 59.854 | 79.804 | 985,024 | pixels and colours passed |
| hors-render-v2 | fps | 60.160 | 20.891 | 15.829 | 59.854 | 63.176 | 985,024 | pixels and colours passed |
| hors-render-v2 | ram | 51.254 | 20.894 | 16.147 | 59.855 | 61.930 | 985,024 | pixels and colours passed |
| hors-renderer-v3 | fps | 53.372 | 22.701 | 16.006 | 61.075 | 62.477 | 1,009,648 | pixels and colours passed |
| hors-renderer-v3 | ram | 52.945 | 22.698 | 15.988 | 60.991 | 62.547 | 1,009,648 | pixels and colours passed |
| hors-render-v2-beta1 | fps | 60.160 | 20.891 | 15.829 | 59.854 | 63.176 | 985,024 | pixels and colours passed |
| hors-render-v2-beta1 | ram | 51.254 | 20.894 | 16.147 | 59.855 | 61.930 | 985,024 | pixels and colours passed |
| hors-v4-ef | fps | 53.372 | 22.701 | 16.006 | 61.075 | 62.477 | 1,009,648 | pixels and colours passed |
| hors-v4-ef | ram | 52.945 | 22.698 | 15.988 | 60.991 | 62.547 | 1,009,648 | pixels and colours passed |
| hors-v5-ef | fps | 54.102 | 22.733 | 15.993 | 60.989 | 62.527 | 1,001,440 | **WINNER**; pixels and colours passed |
| hors-v5-ef | ram | 53.601 | 22.702 | 16.011 | 60.952 | 62.456 | 1,001,440 | pixels and colours passed |

## SPACE HORSE SPIN

24 pictures; picture SHA-256 `91d4040c370d3c305752497b72257d473c6083ec0e9a523f865532e650eece8e`.

| Renderer | Preference | High FPS | Average FPS | Low FPS | P95 ms | Worst ms | CRT bytes | Result / reason |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| step | fps | 12.534 | 9.978 | 8.353 | 119.704 | 119.715 | 500,752 | pixels and colours passed |
| bytechunk | fps | 12.532 | 10.547 | 8.354 | 99.756 | 119.705 | 500,752 | pixels and colours passed |
| yunroll | fps | 12.534 | 10.648 | 8.354 | 99.757 | 119.706 | 500,752 | pixels and colours passed |
| yunroll-cart | fps | 12.534 | 10.648 | 8.354 | 99.757 | 119.706 | 500,752 | pixels and colours passed |
| yunroll-cart-v2 | fps | 10.098 | 8.538 | 7.173 | 137.441 | 139.416 | 968,608 | pixels and colours passed |
| yunroll-cart-v3 | fps | 12.456 | 9.342 | 8.167 | 120.853 | 122.438 | 968,608 | pixels and colours passed |
| yunroll-cart-v4 | fps | 12.531 | 9.442 | 8.268 | 120.162 | 120.946 | 968,608 | pixels and colours passed |
| yunroll-cart-v5 | fps | 50.127 | 10.145 | 8.210 | 118.912 | 121.804 | 927,568 | pixels and colours passed |
| yunroll-cart-v6 | fps | 50.140 | 10.547 | 8.224 | 119.703 | 121.595 | 927,568 | pixels and colours passed |
| yunroll-cart-v7 | fps | 50.130 | 10.648 | 8.187 | 119.704 | 122.144 | 804,448 | pixels and colours passed |
| yunroll-cart-v8 | fps | 50.130 | 10.648 | 8.187 | 119.704 | 122.144 | 771,616 | pixels and colours passed |
| yunroll-cart-v9 | fps | 52.800 | 10.748 | 8.227 | 119.701 | 121.545 | 771,616 | pixels and colours passed |
| yunroll-cart-v10 | fps | 52.055 | 17.579 | 12.165 | 79.803 | 82.202 | 985,024 | pixels and colours passed |
| yunroll-cart-v7 | ram | 50.125 | 9.945 | 8.353 | 119.704 | 119.716 | 804,448 | pixels and colours passed |
| yunroll-cart-v8 | ram | 50.125 | 9.945 | 8.353 | 119.704 | 119.716 | 771,616 | pixels and colours passed |
| yunroll-cart-v9 | ram | 50.484 | 10.045 | 8.215 | 119.705 | 121.732 | 771,616 | pixels and colours passed |
| yunroll-cart-v10 | ram | 50.132 | 17.578 | 12.525 | 79.803 | 79.842 | 985,024 | pixels and colours passed |
| hors-render-v2 | fps | 50.132 | 19.083 | 12.530 | 79.801 | 79.806 | 985,024 | pixels and colours passed |
| hors-render-v2 | ram | 51.638 | 19.086 | 12.209 | 79.801 | 81.904 | 985,024 | pixels and colours passed |
| hors-renderer-v3 | fps | 53.537 | 19.086 | 12.531 | 79.800 | 79.803 | 1,009,648 | pixels and colours passed |
| hors-renderer-v3 | ram | 50.137 | 19.086 | 12.528 | 79.801 | 79.819 | 1,009,648 | pixels and colours passed |
| hors-render-v2-beta1 | fps | 50.132 | 19.083 | 12.530 | 79.801 | 79.806 | 985,024 | pixels and colours passed |
| hors-render-v2-beta1 | ram | 51.638 | 19.086 | 12.209 | 79.801 | 81.904 | 985,024 | pixels and colours passed |
| hors-v4-ef | fps | 53.537 | 19.086 | 12.531 | 79.800 | 79.803 | 1,009,648 | pixels and colours passed |
| hors-v4-ef | ram | 50.137 | 19.086 | 12.528 | 79.801 | 79.819 | 1,009,648 | pixels and colours passed |
| hors-v5-ef | fps | 53.257 | 19.288 | 12.530 | 79.799 | 79.805 | 1,001,440 | **WINNER**; pixels and colours passed |
| hors-v5-ef | ram | 52.262 | 19.288 | 12.530 | 79.796 | 79.805 | 1,001,440 | pixels and colours passed |

## SPACE HORSE CRAWL

32 pictures; picture SHA-256 `a74f5a64d3a5faa6a4d7818cd932cbb6784b62da07abc8bb768621e01ad65740`.

| Renderer | Preference | High FPS | Average FPS | Low FPS | P95 ms | Worst ms | CRT bytes | Result / reason |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| step | fps | 25.070 | 15.134 | 10.025 | 79.804 | 99.756 | 500,752 | pixels and colours passed |
| bytechunk | fps | 25.065 | 16.608 | 12.529 | 79.803 | 79.816 | 500,752 | pixels and colours passed |
| yunroll | fps | 25.066 | 16.608 | 12.529 | 79.803 | 79.815 | 500,752 | pixels and colours passed |
| yunroll-cart | fps | 25.066 | 16.608 | 12.529 | 79.803 | 79.815 | 500,752 | pixels and colours passed |
| yunroll-cart-v2 | fps | 17.588 | 12.858 | 9.811 | 98.982 | 101.923 | 968,608 | pixels and colours passed |
| yunroll-cart-v3 | fps | 23.659 | 14.063 | 10.025 | 83.402 | 99.753 | 968,608 | pixels and colours passed |
| yunroll-cart-v4 | fps | 24.954 | 14.264 | 10.083 | 82.814 | 99.174 | 968,608 | pixels and colours passed |
| yunroll-cart-v5 | fps | 25.062 | 14.666 | 10.042 | 97.219 | 99.581 | 927,568 | pixels and colours passed |
| yunroll-cart-v6 | fps | 25.954 | 15.469 | 9.689 | 81.947 | 103.210 | 927,568 | pixels and colours passed |
| yunroll-cart-v7 | fps | 26.928 | 16.574 | 10.012 | 81.179 | 99.883 | 804,448 | pixels and colours passed |
| yunroll-cart-v8 | fps | 59.029 | 22.903 | 12.129 | 81.304 | 82.450 | 771,616 | pixels and colours passed |
| yunroll-cart-v9 | fps | 52.415 | 23.505 | 12.184 | 80.955 | 82.074 | 771,616 | pixels and colours passed |
| yunroll-cart-v10 | fps | 52.440 | 35.559 | 16.604 | 40.248 | 60.225 | 985,024 | pixels and colours passed |
| yunroll-cart-v7 | ram | 25.651 | 16.273 | 12.196 | 81.261 | 81.993 | 804,448 | pixels and colours passed |
| yunroll-cart-v8 | ram | 58.382 | 22.702 | 12.120 | 80.485 | 82.511 | 771,616 | pixels and colours passed |
| yunroll-cart-v9 | ram | 53.288 | 23.304 | 12.130 | 80.135 | 82.437 | 771,616 | pixels and colours passed |
| yunroll-cart-v10 | ram | 54.090 | 35.660 | 16.604 | 40.186 | 60.225 | 985,024 | pixels and colours passed |
| hors-render-v2 | fps | 54.669 | 38.275 | 24.070 | 40.980 | 41.545 | 985,024 | pixels and colours passed |
| hors-render-v2 | ram | 54.669 | 38.272 | 24.070 | 40.976 | 41.545 | 985,024 | pixels and colours passed |
| hors-renderer-v3 | fps | 54.690 | 38.273 | 24.074 | 40.978 | 41.539 | 1,009,648 | pixels and colours passed |
| hors-renderer-v3 | ram | 54.730 | 38.278 | 24.074 | 40.978 | 41.539 | 1,009,648 | **WINNER**; pixels and colours passed |
| hors-render-v2-beta1 | fps | 54.669 | 38.275 | 24.070 | 40.980 | 41.545 | 985,024 | pixels and colours passed |
| hors-render-v2-beta1 | ram | 54.669 | 38.272 | 24.070 | 40.976 | 41.545 | 985,024 | pixels and colours passed |
| hors-v4-ef | fps | 54.690 | 38.273 | 24.074 | 40.978 | 41.539 | 1,009,648 | pixels and colours passed |
| hors-v4-ef | ram | 54.730 | 38.278 | 24.074 | 40.978 | 41.539 | 1,009,648 | **WINNER**; pixels and colours passed |
| hors-v5-ef | fps | 54.928 | 38.271 | 24.054 | 41.261 | 41.573 | 1,001,440 | pixels and colours passed |
| hors-v5-ef | ram | 54.712 | 38.277 | 24.054 | 41.261 | 41.573 | 1,001,440 | pixels and colours passed |

## FALLING CUBES

18 pictures; picture SHA-256 `5a7187e82950a18e70c4ed0713acc7ba4fcb119af1f71ceb3e6096851223552a`.

| Renderer | Preference | High FPS | Average FPS | Low FPS | P95 ms | Worst ms | CRT bytes | Result / reason |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| step | fps | 25.065 | 13.561 | 10.024 | 99.752 | 99.765 | 500,752 | pixels and colours passed |
| bytechunk | fps | 50.125 | 14.800 | 10.025 | 79.806 | 99.756 | 500,752 | pixels and colours passed |
| yunroll | fps | 50.127 | 14.900 | 10.024 | 79.805 | 99.764 | 500,752 | pixels and colours passed |
| yunroll-cart | fps | 50.127 | 14.900 | 10.024 | 79.805 | 99.764 | 500,752 | pixels and colours passed |
| yunroll-cart-v2 | fps | 25.061 | 11.552 | 8.290 | 116.195 | 120.626 | 968,608 | pixels and colours passed |
| yunroll-cart-v3 | fps | 24.984 | 12.456 | 9.816 | 99.782 | 101.877 | 968,608 | pixels and colours passed |
| yunroll-cart-v4 | fps | 25.064 | 12.659 | 9.738 | 99.752 | 102.693 | 968,608 | pixels and colours passed |
| yunroll-cart-v5 | fps | 25.065 | 13.159 | 9.930 | 99.605 | 100.702 | 927,568 | pixels and colours passed |
| yunroll-cart-v6 | fps | 27.753 | 13.661 | 9.742 | 99.755 | 102.644 | 927,568 | pixels and colours passed |
| yunroll-cart-v7 | fps | 26.965 | 13.862 | 9.809 | 99.752 | 101.946 | 804,448 | pixels and colours passed |
| yunroll-cart-v8 | fps | 27.064 | 13.862 | 9.835 | 99.753 | 101.678 | 771,616 | pixels and colours passed |
| yunroll-cart-v9 | fps | 28.149 | 13.862 | 9.830 | 99.754 | 101.728 | 771,616 | pixels and colours passed |
| yunroll-cart-v10 | fps | 50.150 | 19.688 | 12.278 | 60.745 | 81.445 | 985,024 | pixels and colours passed |
| yunroll-cart-v7 | ram | 26.825 | 13.460 | 9.760 | 99.765 | 102.455 | 804,448 | pixels and colours passed |
| yunroll-cart-v8 | ram | 26.683 | 13.460 | 9.757 | 99.757 | 102.494 | 771,616 | pixels and colours passed |
| yunroll-cart-v9 | ram | 27.264 | 13.561 | 9.784 | 100.767 | 102.210 | 771,616 | pixels and colours passed |
| yunroll-cart-v10 | ram | 27.460 | 19.587 | 12.132 | 61.321 | 82.426 | 985,024 | pixels and colours passed |
| hors-render-v2 | fps | 50.130 | 20.892 | 15.981 | 61.301 | 62.576 | 985,024 | pixels and colours passed |
| hors-render-v2 | ram | 50.127 | 20.894 | 15.976 | 60.616 | 62.595 | 985,024 | pixels and colours passed |
| hors-renderer-v3 | fps | 50.127 | 21.295 | 15.981 | 61.667 | 62.576 | 1,009,648 | pixels and colours passed |
| hors-renderer-v3 | ram | 50.119 | 21.297 | 16.028 | 61.486 | 62.389 | 1,009,648 | pixels and colours passed |
| hors-render-v2-beta1 | fps | 50.130 | 20.892 | 15.981 | 61.301 | 62.576 | 985,024 | pixels and colours passed |
| hors-render-v2-beta1 | ram | 50.127 | 20.894 | 15.976 | 60.616 | 62.595 | 985,024 | pixels and colours passed |
| hors-v4-ef | fps | 50.127 | 21.295 | 15.981 | 61.667 | 62.576 | 1,009,648 | pixels and colours passed |
| hors-v4-ef | ram | 50.119 | 21.297 | 16.028 | 61.486 | 62.389 | 1,009,648 | pixels and colours passed |
| hors-v5-ef | fps | 50.122 | 21.396 | 15.992 | 61.488 | 62.530 | 1,001,440 | pixels and colours passed |
| hors-v5-ef | ram | 26.887 | 21.397 | 15.985 | 61.516 | 62.560 | 1,001,440 | **WINNER**; pixels and colours passed |

## HORSE HEAD HIFI

128 pictures; picture SHA-256 `6f72273f6b4303f26047376cd61f522fc11ac196c9b2ee5f400e7bb9c7090a57`.

| Renderer | Preference | High FPS | Average FPS | Low FPS | P95 ms | Worst ms | CRT bytes | Result / reason |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| step | fps | N/A | N/A | N/A | — | — | — | frame pointer tables reach $1800, limit $1700; reduce --frames |
| bytechunk | fps | N/A | N/A | N/A | — | — | — | frame pointer tables reach $1800, limit $1700; reduce --frames |
| yunroll | fps | N/A | N/A | N/A | — | — | — | frame pointer tables reach $1800, limit $1700; reduce --frames |
| yunroll-cart | fps | N/A | N/A | N/A | — | — | — | frame pointer tables reach $1800, limit $1700; reduce --frames |
| yunroll-cart-v2 | fps | 8.689 | 7.031 | 6.162 | 161.608 | 162.283 | 968,608 | pixels and colours passed |
| yunroll-cart-v3 | fps | 10.151 | 7.835 | 7.004 | 140.796 | 142.777 | 968,608 | pixels and colours passed |
| yunroll-cart-v4 | fps | 10.025 | 7.936 | 7.035 | 141.680 | 142.155 | 968,608 | pixels and colours passed |
| yunroll-cart-v5 | fps | 10.220 | 8.337 | 6.995 | 139.881 | 142.954 | 927,568 | pixels and colours passed |
| yunroll-cart-v6 | fps | 12.531 | 8.639 | 7.002 | 139.655 | 142.820 | 927,568 | pixels and colours passed |
| yunroll-cart-v7 | fps | 13.000 | 10.143 | 8.109 | 119.706 | 123.314 | 804,448 | pixels and colours passed |
| yunroll-cart-v8 | fps | 25.061 | 10.145 | 8.098 | 120.597 | 123.487 | 771,616 | pixels and colours passed |
| yunroll-cart-v9 | fps | 50.165 | 10.246 | 8.076 | 119.713 | 123.828 | 771,616 | pixels and colours passed |
| yunroll-cart-v10 | fps | 51.015 | 20.693 | 15.672 | 62.097 | 63.808 | 985,024 | pixels and colours passed |
| yunroll-cart-v7 | ram | 12.977 | 9.342 | 8.090 | 121.731 | 123.614 | 804,448 | pixels and colours passed |
| yunroll-cart-v8 | ram | 27.188 | 9.442 | 8.071 | 122.972 | 123.902 | 771,616 | pixels and colours passed |
| yunroll-cart-v9 | ram | 50.127 | 9.543 | 8.103 | 121.496 | 123.411 | 771,616 | pixels and colours passed |
| yunroll-cart-v10 | ram | 51.334 | 20.793 | 15.716 | 62.199 | 63.629 | 985,024 | pixels and colours passed |
| hors-render-v2 | fps | 50.158 | 21.495 | 15.636 | 62.269 | 63.954 | 985,024 | pixels and colours passed |
| hors-render-v2 | ram | 56.725 | 21.598 | 15.563 | 62.387 | 64.257 | 985,024 | pixels and colours passed |
| hors-renderer-v3 | fps | 53.596 | 23.105 | 16.033 | 60.706 | 62.370 | 1,009,648 | pixels and colours passed |
| hors-renderer-v3 | ram | 51.850 | 23.205 | 16.029 | 60.618 | 62.388 | 1,009,648 | pixels and colours passed |
| hors-render-v2-beta1 | fps | 50.158 | 21.495 | 15.636 | 62.269 | 63.954 | 985,024 | pixels and colours passed |
| hors-render-v2-beta1 | ram | 56.725 | 21.598 | 15.563 | 62.387 | 64.257 | 985,024 | pixels and colours passed |
| hors-v4-ef | fps | 53.596 | 23.105 | 16.033 | 60.706 | 62.370 | 1,009,648 | pixels and colours passed |
| hors-v4-ef | ram | 51.850 | 23.205 | 16.029 | 60.618 | 62.388 | 1,009,648 | pixels and colours passed |
| hors-v5-ef | fps | 50.135 | 23.204 | 16.105 | 60.195 | 62.094 | 1,001,440 | pixels and colours passed |
| hors-v5-ef | ram | 52.842 | 23.307 | 16.001 | 60.715 | 62.497 | 1,001,440 | **WINNER**; pixels and colours passed |

## SUNFLOWER TORUS HIFI

128 pictures; picture SHA-256 `d9bd18e351f1f88ce30fa93397393b59f77f4143e532767ffb6e1c388a75b102`.

| Renderer | Preference | High FPS | Average FPS | Low FPS | P95 ms | Worst ms | CRT bytes | Result / reason |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| step | fps | N/A | N/A | N/A | — | — | — | resident record count exceeds 255 |
| bytechunk | fps | N/A | N/A | N/A | — | — | — | resident record count exceeds 255 |
| yunroll | fps | N/A | N/A | N/A | — | — | — | resident record count exceeds 255 |
| yunroll-cart | fps | N/A | N/A | N/A | — | — | — | resident record count exceeds 255 |
| yunroll-cart-v2 | fps | 9.829 | 4.721 | 3.601 | 260.733 | 277.730 | 968,608 | pixels and colours passed |
| yunroll-cart-v3 | fps | 10.299 | 5.424 | 4.157 | 239.613 | 240.540 | 968,608 | pixels and colours passed |
| yunroll-cart-v4 | fps | 10.169 | 5.423 | 4.130 | 240.022 | 242.124 | 968,608 | pixels and colours passed |
| yunroll-cart-v5 | fps | 12.363 | 5.826 | 4.511 | 220.455 | 221.660 | 927,568 | pixels and colours passed |
| yunroll-cart-v6 | fps | 12.974 | 6.027 | 4.557 | 219.456 | 219.466 | 927,568 | pixels and colours passed |
| yunroll-cart-v7 | fps | 16.847 | 6.831 | 5.012 | 199.500 | 199.505 | 804,448 | pixels and colours passed |
| yunroll-cart-v8 | fps | 50.155 | 12.456 | 6.265 | 139.657 | 159.606 | 771,616 | pixels and colours passed |
| yunroll-cart-v9 | fps | 56.342 | 14.465 | 6.265 | 139.654 | 159.608 | 771,616 | pixels and colours passed |
| yunroll-cart-v10 | fps | 57.462 | 19.889 | 12.531 | 59.856 | 79.803 | 985,024 | pixels and colours passed |
| yunroll-cart-v7 | ram | 12.837 | 6.429 | 5.012 | 199.504 | 199.507 | 804,448 | pixels and colours passed |
| yunroll-cart-v8 | ram | 60.304 | 12.054 | 6.265 | 159.602 | 159.607 | 771,616 | pixels and colours passed |
| yunroll-cart-v9 | ram | 56.715 | 14.064 | 6.188 | 159.601 | 161.599 | 771,616 | pixels and colours passed |
| yunroll-cart-v10 | ram | 60.619 | 19.891 | 12.531 | 60.392 | 79.801 | 985,024 | pixels and colours passed |
| hors-render-v2 | fps | 58.796 | 20.394 | 15.979 | 59.856 | 62.582 | 985,024 | pixels and colours passed |
| hors-render-v2 | ram | 59.999 | 20.391 | 15.976 | 59.856 | 62.594 | 985,024 | pixels and colours passed |
| hors-renderer-v3 | fps | 53.237 | 22.702 | 16.123 | 61.208 | 62.023 | 1,009,648 | pixels and colours passed |
| hors-renderer-v3 | ram | 52.939 | 22.702 | 15.985 | 61.152 | 62.558 | 1,009,648 | pixels and colours passed |
| hors-render-v2-beta1 | fps | 58.796 | 20.394 | 15.979 | 59.856 | 62.582 | 985,024 | pixels and colours passed |
| hors-render-v2-beta1 | ram | 59.999 | 20.391 | 15.976 | 59.856 | 62.594 | 985,024 | pixels and colours passed |
| hors-v4-ef | fps | 53.237 | 22.702 | 16.123 | 61.208 | 62.023 | 1,009,648 | pixels and colours passed |
| hors-v4-ef | ram | 52.939 | 22.702 | 15.985 | 61.152 | 62.558 | 1,009,648 | pixels and colours passed |
| hors-v5-ef | fps | 52.690 | 22.804 | 16.032 | 60.791 | 62.377 | 1,001,440 | **WINNER**; pixels and colours passed |
| hors-v5-ef | ram | 54.069 | 22.702 | 15.998 | 61.165 | 62.506 | 1,001,440 | pixels and colours passed |

## DRAGON WIREFRAME

128 pictures; picture SHA-256 `665e70fac756b5bf5751e5e44cebea7e0d462cf189ed9aef3d1208385983396b`.

| Renderer | Preference | High FPS | Average FPS | Low FPS | P95 ms | Worst ms | CRT bytes | Result / reason |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| step | fps | N/A | N/A | N/A | — | — | — | resident record count exceeds 255 |
| bytechunk | fps | N/A | N/A | N/A | — | — | — | resident record count exceeds 255 |
| yunroll | fps | N/A | N/A | N/A | — | — | — | resident record count exceeds 255 |
| yunroll-cart | fps | N/A | N/A | N/A | — | — | — | resident record count exceeds 255 |
| yunroll-cart-v2 | fps | N/A | N/A | N/A | — | — | — | frame block 10492 exceeds 8192-byte staging buffer |
| yunroll-cart-v3 | fps | N/A | N/A | N/A | — | — | — | frame block 10492 exceeds 8192-byte staging buffer |
| yunroll-cart-v4 | fps | N/A | N/A | N/A | — | — | — | frame block 10492 exceeds 8192-byte staging buffer |
| yunroll-cart-v5 | fps | N/A | N/A | N/A | — | — | — | frame block 10492 exceeds 8192-byte staging buffer |
| yunroll-cart-v6 | fps | N/A | N/A | N/A | — | — | — | frame block 10492 exceeds 8192-byte staging buffer |
| yunroll-cart-v7 | fps | N/A | N/A | N/A | — | — | — | frame block 10492 exceeds 8192-byte staging buffer |
| yunroll-cart-v8 | fps | N/A | N/A | N/A | — | — | — | frame block 10492 exceeds 8192-byte staging buffer |
| yunroll-cart-v9 | fps | N/A | N/A | N/A | — | — | — | frame block 10492 exceeds 8192-byte staging buffer |
| yunroll-cart-v10 | fps | N/A | N/A | N/A | — | — | — | frame block 10492 exceeds 8192-byte staging buffer |
| yunroll-cart-v7 | ram | N/A | N/A | N/A | — | — | — | frame block 10492 exceeds 8192-byte staging buffer |
| yunroll-cart-v8 | ram | N/A | N/A | N/A | — | — | — | frame block 10492 exceeds 8192-byte staging buffer |
| yunroll-cart-v9 | ram | N/A | N/A | N/A | — | — | — | frame block 10492 exceeds 8192-byte staging buffer |
| yunroll-cart-v10 | ram | N/A | N/A | N/A | — | — | — | frame block 10492 exceeds 8192-byte staging buffer |
| hors-render-v2 | fps | 53.774 | 19.387 | 12.532 | 59.856 | 79.798 | 328,384 | pixels and colours passed |
| hors-render-v2 | ram | 53.056 | 19.388 | 12.531 | 59.856 | 79.802 | 328,384 | pixels and colours passed |
| hors-renderer-v3 | fps | 53.774 | 19.387 | 12.532 | 59.856 | 79.798 | 328,384 | pixels and colours passed |
| hors-renderer-v3 | ram | 53.056 | 19.388 | 12.531 | 59.856 | 79.802 | 328,384 | pixels and colours passed |
| hors-render-v2-beta1 | fps | N/A | N/A | N/A | — | — | — | frame block 10492 exceeds 8192-byte staging buffer |
| hors-render-v2-beta1 | ram | N/A | N/A | N/A | — | — | — | frame block 10492 exceeds 8192-byte staging buffer |
| hors-v4-ef | fps | 53.774 | 19.387 | 12.532 | 59.856 | 79.798 | 328,384 | pixels and colours passed |
| hors-v4-ef | ram | 53.056 | 19.388 | 12.531 | 59.856 | 79.802 | 328,384 | pixels and colours passed |
| hors-v5-ef | fps | 53.692 | 19.454 | 12.530 | 59.856 | 79.805 | 328,384 | **WINNER**; pixels and colours passed |
| hors-v5-ef | ram | 53.898 | 19.387 | 12.531 | 60.157 | 79.804 | 328,384 | pixels and colours passed |

## DRAGON METALLIC

128 pictures; picture SHA-256 `d3b0b9ed42874c0dbaf0d6189f7e96f34181feb1b35341a3e476120044e1a4e9`.

| Renderer | Preference | High FPS | Average FPS | Low FPS | P95 ms | Worst ms | CRT bytes | Result / reason |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| step | fps | N/A | N/A | N/A | — | — | — | resident record count exceeds 255 |
| bytechunk | fps | N/A | N/A | N/A | — | — | — | resident record count exceeds 255 |
| yunroll | fps | N/A | N/A | N/A | — | — | — | resident record count exceeds 255 |
| yunroll-cart | fps | N/A | N/A | N/A | — | — | — | resident record count exceeds 255 |
| yunroll-cart-v2 | fps | N/A | N/A | N/A | — | — | — | uniform demo frames exceed EasyFlash capacity; samples were not reduced |
| yunroll-cart-v3 | fps | N/A | N/A | N/A | — | — | — | uniform demo frames exceed EasyFlash capacity; samples were not reduced |
| yunroll-cart-v4 | fps | N/A | N/A | N/A | — | — | — | uniform demo frames exceed EasyFlash capacity; samples were not reduced |
| yunroll-cart-v5 | fps | N/A | N/A | N/A | — | — | — | uniform demo frames exceed EasyFlash capacity; samples were not reduced |
| yunroll-cart-v6 | fps | N/A | N/A | N/A | — | — | — | uniform demo frames exceed EasyFlash capacity; samples were not reduced |
| yunroll-cart-v7 | fps | N/A | N/A | N/A | — | — | — | uniform demo frames exceed EasyFlash capacity; samples were not reduced |
| yunroll-cart-v8 | fps | 16.708 | 8.940 | 7.160 | 139.654 | 139.657 | 385,840 | pixels and colours passed |
| yunroll-cart-v9 | fps | 16.711 | 11.250 | 8.354 | 119.700 | 119.706 | 385,840 | pixels and colours passed |
| yunroll-cart-v10 | fps | 16.711 | 11.250 | 8.354 | 119.700 | 119.706 | 385,840 | pixels and colours passed |
| yunroll-cart-v7 | ram | N/A | N/A | N/A | — | — | — | uniform demo frames exceed EasyFlash capacity; samples were not reduced |
| yunroll-cart-v8 | ram | 12.677 | 8.940 | 7.160 | 139.653 | 139.658 | 385,840 | pixels and colours passed |
| yunroll-cart-v9 | ram | 16.713 | 11.250 | 8.354 | 119.698 | 119.706 | 385,840 | pixels and colours passed |
| yunroll-cart-v10 | ram | 16.713 | 11.250 | 8.354 | 119.698 | 119.706 | 385,840 | pixels and colours passed |
| hors-render-v2 | fps | 16.918 | 11.452 | 8.354 | 99.757 | 119.704 | 385,840 | pixels and colours passed |
| hors-render-v2 | ram | 17.952 | 11.452 | 8.354 | 119.697 | 119.705 | 385,840 | pixels and colours passed |
| hors-renderer-v3 | fps | 27.760 | 14.265 | 11.897 | 80.827 | 84.056 | 377,632 | pixels and colours passed |
| hors-renderer-v3 | ram | 26.502 | 14.263 | 12.088 | 80.885 | 82.728 | 377,632 | pixels and colours passed |
| hors-render-v2-beta1 | fps | 16.918 | 11.452 | 8.354 | 99.757 | 119.704 | 385,840 | pixels and colours passed |
| hors-render-v2-beta1 | ram | 17.952 | 11.452 | 8.354 | 119.697 | 119.705 | 385,840 | pixels and colours passed |
| hors-v4-ef | fps | 27.760 | 14.265 | 11.897 | 80.827 | 84.056 | 377,632 | pixels and colours passed |
| hors-v4-ef | ram | 26.502 | 14.263 | 12.088 | 80.885 | 82.728 | 377,632 | pixels and colours passed |
| hors-v5-ef | fps | 27.732 | 14.366 | 12.118 | 79.805 | 82.523 | 377,632 | **WINNER**; pixels and colours passed |
| hors-v5-ef | ram | 27.254 | 14.362 | 12.121 | 79.805 | 82.503 | 377,632 | pixels and colours passed |

## SAKU SOLID LOGO ONLY

48 pictures; picture SHA-256 `fac1512538ccd349b31eab93fc85492a0d83688a9f4ebeab609f51c974232e67`.

| Renderer | Preference | High FPS | Average FPS | Low FPS | P95 ms | Worst ms | CRT bytes | Result / reason |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| step | fps | N/A | N/A | N/A | — | — | — | resident record count exceeds 255 |
| bytechunk | fps | N/A | N/A | N/A | — | — | — | resident record count exceeds 255 |
| yunroll | fps | N/A | N/A | N/A | — | — | — | resident record count exceeds 255 |
| yunroll-cart | fps | N/A | N/A | N/A | — | — | — | resident record count exceeds 255 |
| yunroll-cart-v2 | fps | 25.064 | 8.135 | 5.528 | 161.583 | 180.907 | 131,392 | pixels and colours passed |
| yunroll-cart-v3 | fps | 50.125 | 9.342 | 6.173 | 157.747 | 161.984 | 131,392 | pixels and colours passed |
| yunroll-cart-v4 | fps | 50.125 | 9.442 | 6.150 | 142.070 | 162.612 | 131,392 | pixels and colours passed |
| yunroll-cart-v5 | fps | 50.130 | 9.543 | 6.260 | 140.955 | 159.756 | 131,392 | pixels and colours passed |
| yunroll-cart-v6 | fps | 53.669 | 10.246 | 7.042 | 139.858 | 142.005 | 131,392 | pixels and colours passed |
| yunroll-cart-v7 | fps | 45.881 | 10.279 | 7.020 | 140.082 | 142.442 | 123,184 | pixels and colours passed |
| yunroll-cart-v8 | fps | 59.156 | 30.068 | 23.510 | 41.633 | 42.535 | 90,352 | pixels and colours passed |
| yunroll-cart-v9 | fps | 53.044 | 36.966 | 24.294 | 40.461 | 41.162 | 90,352 | pixels and colours passed |
| yunroll-cart-v10 | fps | 53.044 | 36.966 | 24.294 | 40.461 | 41.162 | 90,352 | pixels and colours passed |
| yunroll-cart-v7 | ram | 50.127 | 10.245 | 7.018 | 139.929 | 142.482 | 123,184 | pixels and colours passed |
| yunroll-cart-v8 | ram | 58.092 | 30.034 | 23.416 | 41.634 | 42.706 | 90,352 | pixels and colours passed |
| yunroll-cart-v9 | ram | 53.044 | 36.965 | 24.352 | 40.461 | 41.064 | 90,352 | pixels and colours passed |
| yunroll-cart-v10 | ram | 53.044 | 36.965 | 24.352 | 40.461 | 41.064 | 90,352 | pixels and colours passed |
| hors-render-v2 | fps | 54.506 | 38.808 | 24.094 | 41.211 | 41.504 | 90,352 | **WINNER**; pixels and colours passed |
| hors-render-v2 | ram | 54.437 | 38.778 | 24.105 | 41.196 | 41.485 | 90,352 | pixels and colours passed |
| hors-renderer-v3 | fps | 57.976 | 32.010 | 23.478 | 41.498 | 42.593 | 106,768 | pixels and colours passed |
| hors-renderer-v3 | ram | 55.202 | 31.948 | 23.450 | 41.283 | 42.644 | 106,768 | pixels and colours passed |
| hors-render-v2-beta1 | fps | 54.506 | 38.808 | 24.094 | 41.211 | 41.504 | 90,352 | **WINNER**; pixels and colours passed |
| hors-render-v2-beta1 | ram | 54.437 | 38.778 | 24.105 | 41.196 | 41.485 | 90,352 | pixels and colours passed |
| hors-v4-ef | fps | 57.976 | 32.010 | 23.478 | 41.498 | 42.593 | 106,768 | pixels and colours passed |
| hors-v4-ef | ram | 55.202 | 31.948 | 23.450 | 41.283 | 42.644 | 106,768 | pixels and colours passed |
| hors-v5-ef | fps | 58.038 | 32.214 | 23.495 | 41.216 | 42.563 | 106,768 | pixels and colours passed |
| hors-v5-ef | ram | 58.168 | 32.145 | 23.467 | 41.254 | 42.613 | 106,768 | pixels and colours passed |

## SAKU GRADIENT LOGO ONLY

48 pictures; picture SHA-256 `0fc821e0a75767e2d6a5f3f6ff552e00875403af7f40d1c984d026d0cb70fd3b`.

| Renderer | Preference | High FPS | Average FPS | Low FPS | P95 ms | Worst ms | CRT bytes | Result / reason |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| step | fps | N/A | N/A | N/A | — | — | — | resident record count exceeds 255 |
| bytechunk | fps | N/A | N/A | N/A | — | — | — | resident record count exceeds 255 |
| yunroll | fps | N/A | N/A | N/A | — | — | — | resident record count exceeds 255 |
| yunroll-cart | fps | N/A | N/A | N/A | — | — | — | resident record count exceeds 255 |
| yunroll-cart-v2 | fps | 24.605 | 6.025 | 4.938 | 200.571 | 202.504 | 164,224 | pixels and colours passed |
| yunroll-cart-v3 | fps | 24.765 | 6.730 | 5.469 | 181.106 | 182.847 | 164,224 | pixels and colours passed |
| yunroll-cart-v4 | fps | 25.842 | 6.831 | 5.529 | 179.923 | 180.858 | 164,224 | pixels and colours passed |
| yunroll-cart-v5 | fps | 50.132 | 6.931 | 5.523 | 180.493 | 181.062 | 164,224 | pixels and colours passed |
| yunroll-cart-v6 | fps | 50.125 | 7.532 | 6.129 | 161.283 | 163.170 | 164,224 | pixels and colours passed |
| yunroll-cart-v7 | fps | 50.275 | 7.734 | 6.157 | 161.354 | 162.428 | 164,224 | pixels and colours passed |
| yunroll-cart-v8 | fps | 58.541 | 24.307 | 15.564 | 62.315 | 64.249 | 98,560 | pixels and colours passed |
| yunroll-cart-v9 | fps | 55.354 | 31.107 | 23.014 | 40.646 | 43.451 | 98,560 | pixels and colours passed |
| yunroll-cart-v10 | fps | 55.354 | 31.107 | 23.014 | 40.646 | 43.451 | 98,560 | pixels and colours passed |
| yunroll-cart-v7 | ram | 50.127 | 7.733 | 6.158 | 161.308 | 162.401 | 164,224 | pixels and colours passed |
| yunroll-cart-v8 | ram | 58.541 | 24.304 | 15.937 | 62.023 | 62.747 | 98,560 | pixels and colours passed |
| yunroll-cart-v9 | ram | 52.329 | 31.138 | 23.406 | 40.728 | 42.724 | 98,560 | pixels and colours passed |
| yunroll-cart-v10 | ram | 52.329 | 31.138 | 23.406 | 40.728 | 42.724 | 98,560 | pixels and colours passed |
| hors-render-v2 | fps | 56.226 | 32.013 | 22.600 | 41.319 | 44.248 | 98,560 | **WINNER**; pixels and colours passed |
| hors-render-v2 | ram | 56.226 | 31.940 | 23.426 | 42.048 | 42.687 | 98,560 | pixels and colours passed |
| hors-renderer-v3 | fps | 57.519 | 31.209 | 23.447 | 41.168 | 42.650 | 106,768 | pixels and colours passed |
| hors-renderer-v3 | ram | 56.974 | 31.141 | 23.471 | 41.484 | 42.606 | 106,768 | pixels and colours passed |
| hors-render-v2-beta1 | fps | 56.226 | 32.013 | 22.600 | 41.319 | 44.248 | 98,560 | **WINNER**; pixels and colours passed |
| hors-render-v2-beta1 | ram | 56.226 | 31.940 | 23.426 | 42.048 | 42.687 | 98,560 | pixels and colours passed |
| hors-v4-ef | fps | 57.519 | 31.209 | 23.447 | 41.168 | 42.650 | 106,768 | pixels and colours passed |
| hors-v4-ef | ram | 56.974 | 31.141 | 23.471 | 41.484 | 42.606 | 106,768 | pixels and colours passed |
| hors-v5-ef | fps | 56.819 | 31.335 | 23.453 | 41.527 | 42.638 | 106,768 | pixels and colours passed |
| hors-v5-ef | ram | 57.570 | 31.242 | 23.463 | 41.450 | 42.621 | 106,768 | pixels and colours passed |

## Verification

386 passed combinations; 46 capacity N/As; 0 failures. 38,506 completed-picture checks. Physical C64 and NTSC are unmeasured.

See [public-results.json](benchmarks/optimizer-public/public-results.json) for source/tool/input hashes and per-row measurements.
Reproduce with [the public benchmark command](PUBLIC_BENCHMARKS.md). The external benchmark workspace retains playable CRTs, raw traces, labels and oracles.
