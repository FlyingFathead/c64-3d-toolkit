# Measured scene optimization search

| Candidate | Display FPS | Worst display ms | Prep mean ms | ROM B | Runtime PRG B | Fixed cadence | Verified |
| --- | ---: | ---: | ---: | ---: | ---: | --- | --- |
| hors-render-v2-beta1-ram-optimized-t1-g6-b2048 | 28.566 | 60.086 | - | 2138 | 37521 | False | yes |
| hors-render-v1-scene-ram-optimized-t1 | 25.062 | 59.967 | - | 2093 | 37521 | False | yes |

Selection: hors-render-v2-beta1-ram-optimized-t1-g6-b2048

Actual display changes per emulated PAL time. PRG length is not total used RAM; allocation categories are in results.json. Preparation can be unavailable when the legacy stage profiler cannot follow duplicate-picture shortcuts. Timing ties are recorded in selection.json. Different minimum holds can change authored animation speed. All selected candidates must pass completed-frame and displayed-picture checks; no build is automatically promoted.
