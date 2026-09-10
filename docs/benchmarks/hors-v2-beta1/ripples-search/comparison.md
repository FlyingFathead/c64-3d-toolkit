# Measured scene optimization search

| Candidate | Display FPS | Worst display ms | Active stages ms | ROM B | Runtime PRG B | Fixed cadence | Verified |
| --- | ---: | ---: | ---: | ---: | ---: | --- | --- |
| hors-render-v2-beta1-fps-optimized-t1-g10-b2048 | 16.792 | 79.804 | 59.409 | 214548 | 37649 | False | yes |
| hors-render-v2-beta1-fps-optimized-t1-g10-b1024 | 16.625 | 79.806 | 60.007 | 214548 | 37649 | False | yes |
| hors-render-v2-beta1-fps-optimized-t1-g6-b2048 | 15.713 | 79.806 | 63.460 | 176592 | 37649 | False | yes |
| hors-render-v2-beta1-fps-optimized-t1-g6-b1024 | 15.305 | 79.806 | 65.172 | 176592 | 37649 | False | yes |
| hors-render-v2-beta1-fps-optimized-t1-g3-b2048 | 13.885 | 79.807 | 71.901 | 167420 | 37649 | False | yes |
| hors-render-v2-beta1-fps-optimized-t1-g3-b1024 | 13.474 | 79.807 | 74.034 | 167420 | 37649 | False | yes |
| hors-render-v1-scene-fps-optimized-t1 | 12.392 | 99.756 | 80.577 | 167420 | 37649 | False | yes |

Selection: hors-render-v2-beta1-fps-optimized-t1-g10-b2048

Actual display changes per emulated PAL time. PRG length is not total used RAM; allocation categories are in results.json. Preparation can be unavailable when the legacy stage profiler cannot follow duplicate-picture shortcuts. Timing ties are recorded in selection.json. Different minimum holds can change authored animation speed. All selected candidates must pass completed-frame and displayed-picture checks; no build is automatically promoted.
