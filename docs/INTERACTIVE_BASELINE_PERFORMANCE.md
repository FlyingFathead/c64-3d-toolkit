# Demo Cart v3.1 interactive performance: A/B against v3.0

Toolkit v0.8.1 versus the actual shipped v0.8.0 interactive cartridge. Both were rerun in PAL VICE 3.10 with the same seed, machine settings, scene data, native frame order, default speed, visible HUD and disabled stars/exhibition. This isolates the interactive hotfix from the older EasyFlash/GMod3 backend comparison.

Across 58 entries: 0 higher averages, 3 ties and 55 lower averages. The largest decrease is 0.1462 FPS; the largest relative decrease is 0.393%. Median change: -0.240%. Maximum increase in mean active rendering cycles: 0.366%.

The hotfix has a small measurable cost. RUN/STOP now has priority over held speed keys and is also latched during the raster IRQ; that extra input work accounts for the increase. Help contents, menu navigation and HUD switching run on demand. Picture encoding and drawing addresses are preserved. This is a control-correctness patch, with no claim of a speedup or zero regression.

Each entry verifies two complete picture loops plus warm-up across all three buffers, then counts actual displayed-slot transitions over 2,400 PAL refreshes (47.881 seconds). Startup and help time are excluded. High/low FPS are reciprocals of the shortest/longest display hold; only the highest average in each pair is bold, including exact ties. Quantisation is about 0.0209 FPS per displayed frame in this observation window.

The benchmark cartridge is byte-identical to v0.8.0; it has no added runtime polling. SAKU uses its default gradient presentation here; alternate presentations and both star profiles have separate correctness checks. These measurements cover default interactive playback, not every combination of enabled effects. Physical C64 and NTSC were not tested.

[Old raw observations](benchmarks/release-0.8.1/baseline/results.json) · [Patched raw observations](benchmarks/release-0.8.1/collection/results.json) · [Keyboard verification](benchmarks/release-0.8.1/keyboard/results.json)

Reproduce with `tools/verify_gmod3_collection.py` on each CRT, using `--output docs/benchmarks/release-0.8.1/baseline` or `collection`, then run `python tools/report_interactive_baseline.py`. Supply `--vice` and `--vice-data` for your VICE installation.

## 01. SAKU 2026 INTERACTIVE (240 stored pictures)

| Interactive cart / renderer | High FPS | Average FPS | Low FPS | Mean render cycles |
| --- | ---: | ---: | ---: | ---: |
| v3.0 / hors-v4-gmod3 | 25.0623 | **18.1910** | 16.7082 | 54192.1 |
| v3.1 / hors-v4-gmod3 | 25.0623 | 18.1493 | 16.7082 | 54324.5 |

Change: -0.0418 FPS (-0.230%).

## 02. DRAGON BLUE (128 stored pictures)

| Interactive cart / renderer | High FPS | Average FPS | Low FPS | Mean render cycles |
| --- | ---: | ---: | ---: | ---: |
| v3.0 / hors-v4-gmod3 | 25.0623 | **14.6614** | 12.5311 | 67171.4 |
| v3.1 / hors-v4-gmod3 | 25.0623 | 14.6197 | 12.5311 | 67323.5 |

Change: -0.0418 FPS (-0.285%).

## 03. DRAGON GOLDEN (128 stored pictures)

| Interactive cart / renderer | High FPS | Average FPS | Low FPS | Mean render cycles |
| --- | ---: | ---: | ---: | ---: |
| v3.0 / hors-v4-gmod3 | 25.0623 | **14.6614** | 12.5311 | 67163.0 |
| v3.1 / hors-v4-gmod3 | 25.0623 | 14.6405 | 12.5311 | 67309.2 |

Change: -0.0209 FPS (-0.142%).

## 04. DRAGON GREEN (128 stored pictures)

| Interactive cart / renderer | High FPS | Average FPS | Low FPS | Mean render cycles |
| --- | ---: | ---: | ---: | ---: |
| v3.0 / hors-v4-gmod3 | 25.0623 | **14.6614** | 12.5311 | 67173.1 |
| v3.1 / hors-v4-gmod3 | 25.0623 | 14.6197 | 12.5311 | 67328.8 |

Change: -0.0418 FPS (-0.285%).

## 05. DRAGON METALLIC (128 stored pictures)

| Interactive cart / renderer | High FPS | Average FPS | Low FPS | Mean render cycles |
| --- | ---: | ---: | ---: | ---: |
| v3.0 / hors-v4-gmod3 | 25.0623 | **14.6614** | 12.5311 | 67161.4 |
| v3.1 / hors-v4-gmod3 | 25.0623 | 14.6405 | 12.5311 | 67313.7 |

Change: -0.0209 FPS (-0.142%).

## 06. DRAGON RED (128 stored pictures)

| Interactive cart / renderer | High FPS | Average FPS | Low FPS | Mean render cycles |
| --- | ---: | ---: | ---: | ---: |
| v3.0 / hors-v4-gmod3 | 25.0623 | **14.6405** | 12.5311 | 67301.5 |
| v3.1 / hors-v4-gmod3 | 25.0623 | 14.5988 | 12.5311 | 67455.4 |

Change: -0.0418 FPS (-0.285%).

## 07. DRAGON WIREFRAME (128 stored pictures)

| Interactive cart / renderer | High FPS | Average FPS | Low FPS | Mean render cycles |
| --- | ---: | ---: | ---: | ---: |
| v3.0 / hors-v4-gmod3 | 50.1245 | **19.1726** | 12.5311 | 51340.7 |
| v3.1 / hors-v4-gmod3 | 50.1245 | 19.1100 | 12.5311 | 51470.2 |

Change: -0.0627 FPS (-0.327%).

## 08. FALLING CUBES (18 stored pictures)

| Interactive cart / renderer | High FPS | Average FPS | Low FPS | Mean render cycles |
| --- | ---: | ---: | ---: | ---: |
| v3.0 / hors-v4-gmod3 | 50.1245 | **27.4223** | 16.7082 | 34977.1 |
| v3.1 / hors-v4-gmod3 | 50.1245 | 27.3388 | 16.7082 | 35067.9 |

Change: -0.0835 FPS (-0.305%).

## 09. FALLING CUBES (18 stored pictures)

| Interactive cart / renderer | High FPS | Average FPS | Low FPS | Mean render cycles |
| --- | ---: | ---: | ---: | ---: |
| v3.0 / hors-v4-gmod3 | 25.0623 | **20.8017** | 16.7082 | 46401.9 |
| v3.1 / hors-v4-gmod3 | 25.0623 | 20.7599 | 16.7082 | 46517.4 |

Change: -0.0418 FPS (-0.201%).

## 10. BLENDER TRACKING TEST (16 stored pictures)

| Interactive cart / renderer | High FPS | Average FPS | Low FPS | Mean render cycles |
| --- | ---: | ---: | ---: | ---: |
| v3.0 / hors-v4-gmod3 | 8.3541 | **7.8111** | 7.1606 | 124992.1 |
| v3.1 / hors-v4-gmod3 | 8.3541 | 7.7902 | 7.1606 | 125257.3 |

Change: -0.0209 FPS (-0.267%).

## 11. BLENDER VIEWPORT TEST (16 stored pictures)

| Interactive cart / renderer | High FPS | Average FPS | Low FPS | Mean render cycles |
| --- | ---: | ---: | ---: | ---: |
| v3.0 / hors-v4-gmod3 | 10.0249 | **7.9364** | 6.2656 | 124575.4 |
| v3.1 / hors-v4-gmod3 | 10.0249 | 7.9155 | 6.2656 | 124844.0 |

Change: -0.0209 FPS (-0.263%).

## 12. TORUS (32 stored pictures)

| Interactive cart / renderer | High FPS | Average FPS | Low FPS | Mean render cycles |
| --- | ---: | ---: | ---: | ---: |
| v3.0 / hors-v4-gmod3 | 25.0623 | **17.7733** | 12.5311 | 55820.7 |
| v3.1 / hors-v4-gmod3 | 25.0623 | 17.7316 | 12.5311 | 55955.7 |

Change: -0.0418 FPS (-0.235%).

## 13. TORUS DENSE (32 stored pictures)

| Interactive cart / renderer | High FPS | Average FPS | Low FPS | Mean render cycles |
| --- | ---: | ---: | ---: | ---: |
| v3.0 / hors-v4-gmod3 | 25.0623 | **17.3974** | 12.5311 | 57088.7 |
| v3.1 / hors-v4-gmod3 | 25.0623 | 17.3765 | 12.5311 | 57232.5 |

Change: -0.0209 FPS (-0.120%).

## 14. CUBE (36 stored pictures)

| Interactive cart / renderer | High FPS | Average FPS | Low FPS | Mean render cycles |
| --- | ---: | ---: | ---: | ---: |
| v3.0 / hors-v4-gmod3 | 50.1245 | **29.0305** | 25.0623 | 33489.5 |
| v3.1 / hors-v4-gmod3 | 50.1245 | 28.9469 | 25.0623 | 33577.6 |

Change: -0.0835 FPS (-0.288%).

## 15. SPHERE (24 stored pictures)

| Interactive cart / renderer | High FPS | Average FPS | Low FPS | Mean render cycles |
| --- | ---: | ---: | ---: | ---: |
| v3.0 / hors-v4-gmod3 | 25.0623 | **17.2721** | 16.7082 | 56770.7 |
| v3.1 / hors-v4-gmod3 | 25.0623 | 17.2303 | 16.7082 | 56897.1 |

Change: -0.0418 FPS (-0.242%).

## 16. HORSE HEAD (32 stored pictures)

| Interactive cart / renderer | High FPS | Average FPS | Low FPS | Mean render cycles |
| --- | ---: | ---: | ---: | ---: |
| v3.0 / hors-v4-gmod3 | 50.1245 | **29.0931** | 16.7082 | 33889.9 |
| v3.1 / hors-v4-gmod3 | 50.1245 | 28.9887 | 16.7082 | 33985.4 |

Change: -0.1044 FPS (-0.359%).

## 17. SUNFLOWER TORUS (28 stored pictures)

| Interactive cart / renderer | High FPS | Average FPS | Low FPS | Mean render cycles |
| --- | ---: | ---: | ---: | ---: |
| v3.0 / hors-v4-gmod3 | 50.1245 | **28.3830** | 16.7082 | 35301.5 |
| v3.1 / hors-v4-gmod3 | 50.1245 | 28.2995 | 16.7082 | 35387.2 |

Change: -0.0835 FPS (-0.294%).

## 18. SUNFLOWER COLOR (20 stored pictures)

| Interactive cart / renderer | High FPS | Average FPS | Low FPS | Mean render cycles |
| --- | ---: | ---: | ---: | ---: |
| v3.0 / hors-v4-gmod3 | 50.1245 | **22.3472** | 16.7082 | 44745.1 |
| v3.1 / hors-v4-gmod3 | 50.1245 | 22.2845 | 16.7082 | 44845.3 |

Change: -0.0627 FPS (-0.280%).

## 19. SPACE HORSE SPIN (24 stored pictures)

| Interactive cart / renderer | High FPS | Average FPS | Low FPS | Mean render cycles |
| --- | ---: | ---: | ---: | ---: |
| v3.0 / hors-v4-gmod3 | 50.1245 | **19.4650** | 12.5311 | 51621.8 |
| v3.1 / hors-v4-gmod3 | 50.1245 | 19.4441 | 12.5311 | 51764.0 |

Change: -0.0209 FPS (-0.107%).

## 20. SPACE HORSE CRAWL (32 stored pictures)

| Interactive cart / renderer | High FPS | Average FPS | Low FPS | Mean render cycles |
| --- | ---: | ---: | ---: | ---: |
| v3.0 / hors-v4-gmod3 | 50.1245 | **41.0812** | 25.0623 | 22909.1 |
| v3.1 / hors-v4-gmod3 | 50.1245 | **41.0812** | 16.7082 | 22992.9 |

Change: +0.0000 FPS (+0.000%).

## 21. HORSE HEAD HIFI (128 stored pictures)

| Interactive cart / renderer | High FPS | Average FPS | Low FPS | Mean render cycles |
| --- | ---: | ---: | ---: | ---: |
| v3.0 / hors-v4-gmod3 | 50.1245 | **22.8067** | 16.7082 | 43084.9 |
| v3.1 / hors-v4-gmod3 | 50.1245 | 22.7649 | 16.7082 | 43195.7 |

Change: -0.0418 FPS (-0.183%).

## 22. SUNFLOWER TORUS HIFI (128 stored pictures)

| Interactive cart / renderer | High FPS | Average FPS | Low FPS | Mean render cycles |
| --- | ---: | ---: | ---: | ---: |
| v3.0 / hors-v4-gmod3 | 50.1245 | **22.4725** | 16.7082 | 43808.8 |
| v3.1 / hors-v4-gmod3 | 50.1245 | 22.4307 | 16.7082 | 43914.6 |

Change: -0.0418 FPS (-0.186%).

## 23. COLOUR CUBE 24 (24 stored pictures)

| Interactive cart / renderer | High FPS | Average FPS | Low FPS | Mean render cycles |
| --- | ---: | ---: | ---: | ---: |
| v3.0 / hors-v4-gmod3 | 50.1245 | **34.9828** | 25.0623 | 27906.9 |
| v3.1 / hors-v4-gmod3 | 50.1245 | 34.8783 | 25.0623 | 27991.5 |

Change: -0.1044 FPS (-0.299%).

## 24. COLOUR TORUS 18 (18 stored pictures)

| Interactive cart / renderer | High FPS | Average FPS | Low FPS | Mean render cycles |
| --- | ---: | ---: | ---: | ---: |
| v3.0 / hors-v4-gmod3 | 25.0623 | **22.4307** | 16.7082 | 44189.3 |
| v3.1 / hors-v4-gmod3 | 25.0623 | 22.3681 | 16.7082 | 44300.6 |

Change: -0.0627 FPS (-0.279%).

## 25. TWIST TUNNEL (48 stored pictures)

| Interactive cart / renderer | High FPS | Average FPS | Low FPS | Mean render cycles |
| --- | ---: | ---: | ---: | ---: |
| v3.0 / hors-v4-gmod3 | 12.5311 | **11.8210** | 10.0249 | 83036.1 |
| v3.1 / hors-v4-gmod3 | 12.5311 | 11.8002 | 10.0249 | 83217.6 |

Change: -0.0209 FPS (-0.177%).

## 26. RIBBON DANCE (48 stored pictures)

| Interactive cart / renderer | High FPS | Average FPS | Low FPS | Mean render cycles |
| --- | ---: | ---: | ---: | ---: |
| v3.0 / hors-v4-gmod3 | 50.1245 | **43.2951** | 25.0623 | 22545.8 |
| v3.1 / hors-v4-gmod3 | 50.1245 | 43.1489 | 25.0623 | 22619.5 |

Change: -0.1462 FPS (-0.338%).

## 27. ORBITAL CUBES (48 stored pictures)

| Interactive cart / renderer | High FPS | Average FPS | Low FPS | Mean render cycles |
| --- | ---: | ---: | ---: | ---: |
| v3.0 / hors-v4-gmod3 | 50.1245 | **32.6018** | 25.0623 | 29984.7 |
| v3.1 / hors-v4-gmod3 | 50.1245 | 32.5183 | 25.0623 | 30071.1 |

Change: -0.0835 FPS (-0.256%).

## 28. WAVE LATTICE (48 stored pictures)

| Interactive cart / renderer | High FPS | Average FPS | Low FPS | Mean render cycles |
| --- | ---: | ---: | ---: | ---: |
| v3.0 / hors-v4-gmod3 | 50.1245 | **27.2970** | 16.7082 | 35756.8 |
| v3.1 / hors-v4-gmod3 | 50.1245 | 27.2552 | 16.7082 | 35855.1 |

Change: -0.0418 FPS (-0.153%).

## 29. RIPPLES LITE (100 stored pictures)

| Interactive cart / renderer | High FPS | Average FPS | Low FPS | Mean render cycles |
| --- | ---: | ---: | ---: | ---: |
| v3.0 / hors-v4-gmod3 | 16.7082 | **15.3298** | 12.5311 | 64094.2 |
| v3.1 / hors-v4-gmod3 | 16.7082 | 15.3089 | 12.5311 | 64232.1 |

Change: -0.0209 FPS (-0.136%).

## 30. HORSE AND SUNFLOWER (84 stored pictures)

| Interactive cart / renderer | High FPS | Average FPS | Low FPS | Mean render cycles |
| --- | ---: | ---: | ---: | ---: |
| v3.0 / hors-v4-gmod3 | 10.0249 | **8.5629** | 7.1606 | 114442.9 |
| v3.1 / hors-v4-gmod3 | 10.0249 | 8.5421 | 7.1606 | 114680.5 |

Change: -0.0209 FPS (-0.244%).

## 31. HORSE AND SUNFLOWER (84 stored pictures)

| Interactive cart / renderer | High FPS | Average FPS | Low FPS | Mean render cycles |
| --- | ---: | ---: | ---: | ---: |
| v3.0 / hors-v4-gmod3 | 10.0249 | **8.3541** | 8.3541 | 114436.8 |
| v3.1 / hors-v4-gmod3 | 10.0249 | **8.3541** | 8.3541 | 114678.1 |

Change: +0.0000 FPS (+0.000%).

## 32. DON'T LOSE YOUR MARBLES (640 stored pictures)

| Interactive cart / renderer | High FPS | Average FPS | Low FPS | Mean render cycles |
| --- | ---: | ---: | ---: | ---: |
| v3.0 / hors-v4-gmod3 | 25.0623 | **15.1000** | 8.3541 | 64457.0 |
| v3.1 / hors-v4-gmod3 | 25.0623 | 15.0791 | 8.3541 | 64609.5 |

Change: -0.0209 FPS (-0.138%).

## 33. TORUS BLACK ON WHITE (32 stored pictures)

| Interactive cart / renderer | High FPS | Average FPS | Low FPS | Mean render cycles |
| --- | ---: | ---: | ---: | ---: |
| v3.0 / hors-v4-gmod3 | 25.0623 | **17.7524** | 12.5311 | 55918.0 |
| v3.1 / hors-v4-gmod3 | 25.0623 | 17.6898 | 12.5311 | 56035.1 |

Change: -0.0627 FPS (-0.353%).

## 34. DENSE TORUS CYAN ON BLUE (32 stored pictures)

| Interactive cart / renderer | High FPS | Average FPS | Low FPS | Mean render cycles |
| --- | ---: | ---: | ---: | ---: |
| v3.0 / hors-v4-gmod3 | 25.0623 | **17.3765** | 12.5311 | 57171.5 |
| v3.1 / hors-v4-gmod3 | 25.0623 | 17.3347 | 12.5311 | 57316.9 |

Change: -0.0418 FPS (-0.240%).

## 35. SPHERE LIGHT GREEN ON BLACK (24 stored pictures)

| Interactive cart / renderer | High FPS | Average FPS | Low FPS | Mean render cycles |
| --- | ---: | ---: | ---: | ---: |
| v3.0 / hors-v4-gmod3 | 25.0623 | **17.2721** | 16.7082 | 56768.8 |
| v3.1 / hors-v4-gmod3 | 25.0623 | 17.2303 | 16.7082 | 56888.3 |

Change: -0.0418 FPS (-0.242%).

## 36. CUBE WHITE ON PURPLE (36 stored pictures)

| Interactive cart / renderer | High FPS | Average FPS | Low FPS | Mean render cycles |
| --- | ---: | ---: | ---: | ---: |
| v3.0 / hors-v4-gmod3 | 50.1245 | **28.9469** | 25.0623 | 33575.4 |
| v3.1 / hors-v4-gmod3 | 50.1245 | 28.8634 | 25.0623 | 33671.4 |

Change: -0.0835 FPS (-0.289%).

## 37. CUBE (192 stored pictures)

| Interactive cart / renderer | High FPS | Average FPS | Low FPS | Mean render cycles |
| --- | ---: | ---: | ---: | ---: |
| v3.0 / hors-v4-gmod3 | 50.1245 | **28.9469** | 25.0623 | 33690.0 |
| v3.1 / hors-v4-gmod3 | 50.1245 | 28.8634 | 16.7082 | 33785.3 |

Change: -0.0835 FPS (-0.289%).

## 38. PRETZEL WIRE-COLOR (192 stored pictures)

| Interactive cart / renderer | High FPS | Average FPS | Low FPS | Mean render cycles |
| --- | ---: | ---: | ---: | ---: |
| v3.0 / hors-v4-gmod3 | 25.0623 | **17.3765** | 12.5311 | 56591.1 |
| v3.1 / hors-v4-gmod3 | 25.0623 | 17.3347 | 12.5311 | 56724.8 |

Change: -0.0418 FPS (-0.240%).

## 39. PRETZEL WIRE-INTERACTIVE (192 stored pictures)

| Interactive cart / renderer | High FPS | Average FPS | Low FPS | Mean render cycles |
| --- | ---: | ---: | ---: | ---: |
| v3.0 / hors-v4-gmod3 | 25.0623 | **17.3765** | 12.5311 | 56591.1 |
| v3.1 / hors-v4-gmod3 | 25.0623 | 17.3347 | 12.5311 | 56724.8 |

Change: -0.0418 FPS (-0.240%).

## 40. TAC-2 COLOUR (192 stored pictures)

| Interactive cart / renderer | High FPS | Average FPS | Low FPS | Mean render cycles |
| --- | ---: | ---: | ---: | ---: |
| v3.0 / hors-v4-gmod3 | 25.0623 | **19.6948** | 16.7082 | 49744.3 |
| v3.1 / hors-v4-gmod3 | 25.0623 | 19.6321 | 16.7082 | 49863.3 |

Change: -0.0627 FPS (-0.318%).

## 41. TAC-2 WIRE (192 stored pictures)

| Interactive cart / renderer | High FPS | Average FPS | Low FPS | Mean render cycles |
| --- | ---: | ---: | ---: | ---: |
| v3.0 / hors-v4-gmod3 | 25.0623 | **23.4541** | 16.7082 | 41729.3 |
| v3.1 / hors-v4-gmod3 | 25.0623 | 23.3915 | 16.7082 | 41834.5 |

Change: -0.0627 FPS (-0.267%).

## 42. HORSE HEAD HIFI (192 stored pictures)

| Interactive cart / renderer | High FPS | Average FPS | Low FPS | Mean render cycles |
| --- | ---: | ---: | ---: | ---: |
| v3.0 / hors-v4-gmod3 | 50.1245 | **22.8276** | 16.7082 | 43082.7 |
| v3.1 / hors-v4-gmod3 | 50.1245 | 22.7858 | 16.7082 | 43197.9 |

Change: -0.0418 FPS (-0.183%).

## 43. PRETZEL DITHER (128 stored pictures)

| Interactive cart / renderer | High FPS | Average FPS | Low FPS | Mean render cycles |
| --- | ---: | ---: | ---: | ---: |
| v3.0 / hors-v4-gmod3 | 25.0623 | **17.7942** | 12.5311 | 55171.2 |
| v3.1 / hors-v4-gmod3 | 25.0623 | 17.7316 | 12.5311 | 55299.3 |

Change: -0.0627 FPS (-0.352%).

## 44. PRETZEL MATERIAL (128 stored pictures)

| Interactive cart / renderer | High FPS | Average FPS | Low FPS | Mean render cycles |
| --- | ---: | ---: | ---: | ---: |
| v3.0 / hors-v4-gmod3 | 25.0623 | **17.5854** | 12.5311 | 55794.5 |
| v3.1 / hors-v4-gmod3 | 25.0623 | 17.5436 | 12.5311 | 55929.0 |

Change: -0.0418 FPS (-0.238%).

## 45. PRETZEL METALLIC (128 stored pictures)

| Interactive cart / renderer | High FPS | Average FPS | Low FPS | Mean render cycles |
| --- | ---: | ---: | ---: | ---: |
| v3.0 / hors-v4-gmod3 | 16.7082 | **14.2437** | 12.5311 | 69035.7 |
| v3.1 / hors-v4-gmod3 | 16.7082 | 14.2228 | 12.5311 | 69191.5 |

Change: -0.0209 FPS (-0.147%).

## 46. PRETZEL METALLIC (192 stored pictures)

| Interactive cart / renderer | High FPS | Average FPS | Low FPS | Mean render cycles |
| --- | ---: | ---: | ---: | ---: |
| v3.0 / hors-v4-gmod3 | 16.7082 | **14.2228** | 12.5311 | 68949.8 |
| v3.1 / hors-v4-gmod3 | 16.7082 | 14.2020 | 12.5311 | 69105.0 |

Change: -0.0209 FPS (-0.147%).

## 47. PRETZEL TEXTURED (128 stored pictures)

| Interactive cart / renderer | High FPS | Average FPS | Low FPS | Mean render cycles |
| --- | ---: | ---: | ---: | ---: |
| v3.0 / hors-v4-gmod3 | 16.7082 | **14.2646** | 12.5311 | 68944.4 |
| v3.1 / hors-v4-gmod3 | 16.7082 | 14.2228 | 12.5311 | 69100.5 |

Change: -0.0418 FPS (-0.293%).

## 48. PRETZEL WIRE-BW (128 stored pictures)

| Interactive cart / renderer | High FPS | Average FPS | Low FPS | Mean render cycles |
| --- | ---: | ---: | ---: | ---: |
| v3.0 / hors-v4-gmod3 | 25.0623 | **17.3556** | 12.5311 | 56578.8 |
| v3.1 / hors-v4-gmod3 | 25.0623 | 17.3347 | 12.5311 | 56711.1 |

Change: -0.0209 FPS (-0.120%).

## 49. HORSE HEAD (192 stored pictures)

| Interactive cart / renderer | High FPS | Average FPS | Low FPS | Mean render cycles |
| --- | ---: | ---: | ---: | ---: |
| v3.0 / hors-v4-gmod3 | 50.1245 | **28.9052** | 16.7082 | 33683.4 |
| v3.1 / hors-v4-gmod3 | 50.1245 | 28.8425 | 16.7082 | 33776.2 |

Change: -0.0627 FPS (-0.217%).

## 50. SAKU GRADIENT (48 stored pictures)

| Interactive cart / renderer | High FPS | Average FPS | Low FPS | Mean render cycles |
| --- | ---: | ---: | ---: | ---: |
| v3.0 / hors-v4-gmod3 | 50.1245 | **30.9937** | 25.0623 | 31770.4 |
| v3.1 / hors-v4-gmod3 | 50.1245 | 30.9101 | 25.0623 | 31858.2 |

Change: -0.0835 FPS (-0.270%).

## 51. SAKU SOLID (48 stored pictures)

| Interactive cart / renderer | High FPS | Average FPS | Low FPS | Mean render cycles |
| --- | ---: | ---: | ---: | ---: |
| v3.0 / hors-v4-gmod3 | 50.1245 | **31.8917** | 25.0623 | 30933.2 |
| v3.1 / hors-v4-gmod3 | 50.1245 | 31.7664 | 25.0623 | 31025.0 |

Change: -0.1253 FPS (-0.393%).

## 52. SPACE HORSE CRAWL (192 stored pictures)

| Interactive cart / renderer | High FPS | Average FPS | Low FPS | Mean render cycles |
| --- | ---: | ---: | ---: | ---: |
| v3.0 / hors-v4-gmod3 | 50.1245 | **40.0996** | 16.7082 | 22003.9 |
| v3.1 / hors-v4-gmod3 | 50.1245 | **40.0996** | 16.7082 | 22067.4 |

Change: +0.0000 FPS (+0.000%).

## 53. SPACE HORSE (192 stored pictures)

| Interactive cart / renderer | High FPS | Average FPS | Low FPS | Mean render cycles |
| --- | ---: | ---: | ---: | ---: |
| v3.0 / hors-v4-gmod3 | 50.1245 | **19.2771** | 12.5311 | 51246.0 |
| v3.1 / hors-v4-gmod3 | 50.1245 | 19.2353 | 12.5311 | 51373.4 |

Change: -0.0418 FPS (-0.217%).

## 54. SPHERE (192 stored pictures)

| Interactive cart / renderer | High FPS | Average FPS | Low FPS | Mean render cycles |
| --- | ---: | ---: | ---: | ---: |
| v3.0 / hors-v4-gmod3 | 25.0623 | **17.2512** | 16.7082 | 56823.2 |
| v3.1 / hors-v4-gmod3 | 25.0623 | 17.2303 | 16.7082 | 56953.6 |

Change: -0.0209 FPS (-0.121%).

## 55. SUNFLOWER TORUS (192 stored pictures)

| Interactive cart / renderer | High FPS | Average FPS | Low FPS | Mean render cycles |
| --- | ---: | ---: | ---: | ---: |
| v3.0 / hors-v4-gmod3 | 50.1245 | **28.3204** | 16.7082 | 34603.4 |
| v3.1 / hors-v4-gmod3 | 50.1245 | 28.2577 | 16.7082 | 34694.1 |

Change: -0.0627 FPS (-0.221%).

## 56. SUNFLOWER TORUS (192 stored pictures)

| Interactive cart / renderer | High FPS | Average FPS | Low FPS | Mean render cycles |
| --- | ---: | ---: | ---: | ---: |
| v3.0 / hors-v4-gmod3 | 50.1245 | **22.1383** | 16.7082 | 44330.8 |
| v3.1 / hors-v4-gmod3 | 50.1245 | 22.0966 | 16.7082 | 44440.5 |

Change: -0.0418 FPS (-0.189%).

## 57. TORUS (192 stored pictures)

| Interactive cart / renderer | High FPS | Average FPS | Low FPS | Mean render cycles |
| --- | ---: | ---: | ---: | ---: |
| v3.0 / hors-v4-gmod3 | 25.0623 | **17.7316** | 12.5311 | 55350.2 |
| v3.1 / hors-v4-gmod3 | 25.0623 | 17.6898 | 12.5311 | 55482.7 |

Change: -0.0418 FPS (-0.236%).

## 58. DENSE TORUS (192 stored pictures)

| Interactive cart / renderer | High FPS | Average FPS | Low FPS | Mean render cycles |
| --- | ---: | ---: | ---: | ---: |
| v3.0 / hors-v4-gmod3 | 25.0623 | **17.4183** | 12.5311 | 56527.8 |
| v3.1 / hors-v4-gmod3 | 25.0623 | 17.3765 | 12.5311 | 56661.1 |

Change: -0.0418 FPS (-0.240%).
