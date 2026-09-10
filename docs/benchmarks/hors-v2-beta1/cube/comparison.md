# Measured scene optimization search

| Candidate | Display FPS | Worst display ms | Prep mean ms | ROM B | Runtime PRG B | Fixed cadence | Verified |
| --- | ---: | ---: | ---: | ---: | ---: | --- | --- |
| hors-render-v2-beta1-fps-optimized-t1-g6-b2048 | 35.717 | 42.414 | 27.864 | 15224 | 37649 | False | yes |
| hors-render-v2-beta1-fps-raw-t1-g6-b2048 | 35.521 | 42.509 | 28.032 | 15224 | 37649 | False | yes |
| hors-render-v1-scene-fps-optimized-t1 | 32.516 | 43.751 | 30.554 | 15012 | 37649 | False | yes |
| hors-render-v1-scene-fps-raw-t1 | 32.416 | 43.874 | 30.726 | 15012 | 37649 | False | yes |
| hors-render-v2-beta1-fps-raw-t2-g6-b2048 | 25.114 | 39.905 | 27.635 | 15224 | 37649 | True | yes |
| hors-render-v2-beta1-fps-optimized-t2-g6-b2048 | 25.114 | 39.904 | 27.473 | 15224 | 37649 | True | yes |
| hors-render-v1-scene-fps-optimized-t2 | 25.112 | 39.904 | 30.185 | 15012 | 37649 | True | yes |
| hors-render-v1-scene-fps-raw-t2 | 25.112 | 39.905 | 30.348 | 15012 | 37649 | True | yes |
| hors-render-v1-scene-fps-optimized-t3 | 16.708 | 59.855 | 30.186 | 15012 | 37649 | True | yes |
| hors-render-v2-beta1-fps-optimized-t3-g6-b2048 | 16.708 | 59.854 | 27.474 | 15224 | 37649 | True | yes |
| hors-render-v2-beta1-fps-raw-t3-g6-b2048 | 16.708 | 59.854 | 27.635 | 15224 | 37649 | True | yes |
| hors-render-v1-scene-fps-raw-t3 | 16.708 | 59.855 | 30.351 | 15012 | 37649 | True | yes |
| hors-render-v2-beta1-fps-raw-t4-g6-b2048 | 12.507 | 79.805 | 27.635 | 15224 | 37649 | True | yes |
| hors-render-v2-beta1-fps-optimized-t4-g6-b2048 | 12.507 | 79.804 | 27.473 | 15224 | 37649 | True | yes |
| hors-render-v1-scene-fps-optimized-t4 | 12.506 | 79.805 | 30.186 | 15012 | 37649 | True | yes |
| hors-render-v1-scene-fps-raw-t4 | 12.506 | 79.805 | 30.349 | 15012 | 37649 | True | yes |

Selection: hors-render-v2-beta1-fps-optimized-t1-g6-b2048

Actual display changes per emulated PAL time. PRG length is not total used RAM; allocation categories are in results.json. Preparation can be unavailable when the legacy stage profiler cannot follow duplicate-picture shortcuts. Timing ties are recorded in selection.json. Different minimum holds can change authored animation speed. All selected candidates must pass completed-frame and displayed-picture checks; no build is automatically promoted.
