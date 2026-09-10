# Measured scene optimization search

| Candidate | Display FPS | Worst display ms | Prep mean ms | ROM B | Runtime PRG B | Fixed cadence | Verified |
| --- | ---: | ---: | ---: | ---: | ---: | --- | --- |
| hors-render-v2-beta1-fps-optimized-t1-g6-b2048 | 20.111 | 62.517 | 49.549 | 22455 | 37649 | False | yes |
| hors-render-v2-beta1-ram-optimized-t1-g6-b2048 | 20.111 | 62.517 | 49.549 | 22455 | 21620 | False | yes |
| hors-render-v1-scene-fps-optimized-t1 | 18.409 | 79.803 | 54.149 | 22085 | 37649 | False | yes |
| hors-render-v1-scene-ram-optimized-t1 | 18.409 | 79.803 | 54.149 | 22085 | 21620 | False | yes |
| hors-render-v1-scene-fps-optimized-t4 | 12.506 | 79.805 | 53.873 | 22085 | 37649 | True | yes |
| hors-render-v1-scene-ram-optimized-t4 | 12.506 | 79.805 | 53.873 | 22085 | 21620 | True | yes |
| hors-render-v2-beta1-fps-optimized-t4-g6-b2048 | 12.505 | 79.805 | 49.204 | 22455 | 37649 | True | yes |
| hors-render-v2-beta1-ram-optimized-t4-g6-b2048 | 12.505 | 79.805 | 49.204 | 22455 | 21620 | True | yes |

Selection: hors-render-v2-beta1-fps-optimized-t1-g6-b2048

Actual display changes per emulated PAL time. PRG length is not total used RAM; allocation categories are in results.json. Preparation can be unavailable when the legacy stage profiler cannot follow duplicate-picture shortcuts. Timing ties are recorded in selection.json. Different minimum holds can change authored animation speed. All selected candidates must pass completed-frame and displayed-picture checks; no build is automatically promoted.
