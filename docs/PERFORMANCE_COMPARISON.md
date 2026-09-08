# Renderer performance comparison

Canonical lookup table for comparing methods and toolkit releases. **ONLY use normal PLAY ALL for comparative FPS. F5 is an exhibition mode and MUST NOT be used for benchmarking.**

Measured on PAL VICE 3.10, 985,248 cycles/s, default machine settings, sound disabled, seed 1; 64tass 1.59.3120. This is emulated C64 time, not host wall time or the HUD FPS counter. Physical C64 and NTSC are not measured.

Each cell is actual display flips / elapsed emulated time across 3 normal PLAY ALL visits. Every visit uses the unchanged 10-second setting. Observation starts on the first timer-count IRQ and ends at automatic-next: 499 PAL refresh intervals (about 9.955 s). The first visible picture is outside that window. Rates are rounded to two decimals; **bold** marks the highest displayed-frame count among FPS-preferred methods for that animation, including ties. Tiny timer-phase differences are not ranked as wins.

## Best method for each animation

| Animation | Source samples | Best method(s), FPS preference | Display FPS | V9 vs V8 displayed frames |
| --- | ---: | --- | ---: | ---: |
| TORUS | 32 | hors-render-v1 | 16.07 | +0.00% |
| TORUS DENSE | 32 | hors-render-v1 | 15.77 | +0.00% |
| CUBE | 36 | yunroll, cart scaffold | 30.27 | +0.00% |
| SPHERE | 24 | hors-render-v1 | 15.87 | +0.00% |
| HORSE HEAD | 32 | hors-render-v1 | 27.42 | +0.73% |
| SUNFLOWER TORUS | 28 | hors-render-v1 | 27.12 | +0.00% |
| SUNFLOWER COLOR | 20 | hors-render-v1 | 19.99 | +0.96% |
| SPACE HORSE SPIN | 24 | hors-render-v1 | 17.58 | +0.94% |
| SPACE HORSE CRAWL | 32 | hors-render-v1 | 35.56 | +2.63% |
| FALLING CUBES | 18 | hors-render-v1 | 19.69 | +0.00% |
| HORSE HEAD HIFI | 128 | hors-render-v1 | 20.69 | +0.99% |
| SUNFLOWER TORUS HIFI | 128 | hors-render-v1 | 19.89 | +16.13% |

## Per-animation lookup

High/low are 985,248 divided by the shortest/longest **actual display-flip interval within a normal PLAY ALL window**, including VIC and IRQ stalls. Average is total displayed frames / measured time, not an arithmetic average of instantaneous FPS. Window edges are excluded from interval extrema. High FPS can include a brief queued-frame burst; it does not describe sustained throughput. Bold average marks the best frame-count result across FPS-preferred methods. RAM variants are listed separately. All values are FPS unless the header says bytes.

### TORUS

| Method | High | Average | Low | Resident frame-table RAM (B) | Frame data ROM (B) | Runtime PRG (B) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| step | 25.06 | 12.29 | 10.02 | 18,760 | 0 | 43,546 |
| bytechunk | 25.07 | 13.86 | 10.02 | 18,760 | 0 | 43,546 |
| yunroll | 25.07 | 14.10 | 10.02 | 18,760 | 0 | 43,546 |
| cart scaffold | 25.07 | 14.10 | 10.02 | 18,760 | 0 | 43,546 |
| V2 | 17.06 | 11.25 | 8.35 | 0 | 18,664 | 16,609 |
| V3 | 23.70 | 12.05 | 9.84 | 0 | 18,664 | 18,433 |
| V4 | 23.52 | 12.05 | 9.86 | 0 | 18,664 | 18,433 |
| V5 | 24.47 | 12.36 | 9.88 | 0 | 18,500 | 21,777 |
| V6 | 25.87 | 12.76 | 9.68 | 0 | 18,500 | 21,777 |
| V7 | 27.31 | 13.46 | 9.77 | 0 | 16,505 | 21,777 |
| V8 | 27.31 | 13.46 | 9.77 | 0 | 16,505 | 21,777 |
| V9 | 27.06 | 13.46 | 9.72 | 0 | 16,505 | 21,777 |
| hors-render-v1 | 27.00 | **16.07** | 12.10 | 0 | 46,217 | 21,777 |
| V7-ram | 27.01 | 12.86 | 9.74 | 0 | 16,505 | 18,433 |
| V8-ram | 27.01 | 12.86 | 9.74 | 0 | 16,505 | 18,433 |
| V9-ram | 26.80 | 12.86 | 9.72 | 0 | 16,505 | 18,433 |
| hors-render-v1-ram | 27.04 | 16.07 | 12.04 | 0 | 46,217 | 18,433 |

### TORUS DENSE

| Method | High | Average | Low | Resident frame-table RAM (B) | Frame data ROM (B) | Runtime PRG (B) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| step | 25.07 | 10.95 | 8.35 | 22,081 | 0 | 47,017 |
| bytechunk | 25.06 | 12.19 | 8.35 | 22,081 | 0 | 47,017 |
| yunroll | 25.06 | 12.42 | 10.02 | 22,081 | 0 | 47,017 |
| cart scaffold | 25.06 | 12.42 | 10.02 | 22,081 | 0 | 47,017 |
| V2 | 16.90 | 9.84 | 8.22 | 0 | 21,985 | 16,609 |
| V3 | 23.55 | 10.65 | 8.35 | 0 | 21,985 | 18,433 |
| V4 | 17.17 | 10.75 | 8.35 | 0 | 21,985 | 18,433 |
| V5 | 16.71 | 10.95 | 8.35 | 0 | 21,767 | 21,777 |
| V6 | 27.60 | 11.25 | 8.35 | 0 | 21,767 | 21,777 |
| V7 | 27.21 | 12.15 | 9.71 | 0 | 18,302 | 21,777 |
| V8 | 27.21 | 12.15 | 9.71 | 0 | 18,302 | 21,777 |
| V9 | 27.29 | 12.15 | 9.94 | 0 | 18,302 | 21,777 |
| hors-render-v1 | 27.04 | **15.77** | 12.20 | 0 | 48,568 | 21,777 |
| V7-ram | 26.82 | 11.55 | 8.35 | 0 | 18,302 | 18,433 |
| V8-ram | 26.82 | 11.55 | 8.35 | 0 | 18,302 | 18,433 |
| V9-ram | 26.73 | 11.55 | 8.35 | 0 | 18,302 | 18,433 |
| hors-render-v1-ram | 26.78 | 15.77 | 12.04 | 0 | 48,568 | 18,433 |

### CUBE

| Method | High | Average | Low | Resident frame-table RAM (B) | Frame data ROM (B) | Runtime PRG (B) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| step | 50.14 | 26.45 | 16.71 | 10,264 | 0 | 35,381 |
| bytechunk | 50.17 | 29.40 | 25.05 | 10,264 | 0 | 35,381 |
| yunroll | 50.16 | **30.27** | 25.05 | 10,264 | 0 | 35,381 |
| cart scaffold | 50.16 | **30.27** | 25.05 | 10,264 | 0 | 35,381 |
| V2 | 46.05 | 23.00 | 16.71 | 0 | 10,156 | 16,637 |
| V3 | 50.17 | 24.72 | 16.71 | 0 | 10,156 | 18,433 |
| V4 | 50.13 | 24.72 | 16.70 | 0 | 10,156 | 18,433 |
| V5 | 50.13 | 25.51 | 16.71 | 0 | 2,539 | 21,919 |
| V6 | 55.98 | 26.82 | 16.71 | 0 | 2,539 | 21,919 |
| V7 | 55.55 | 26.82 | 16.71 | 0 | 2,539 | 21,919 |
| V8 | 55.55 | 26.82 | 16.71 | 0 | 2,539 | 21,919 |
| V9 | 55.84 | 26.82 | 16.71 | 0 | 2,539 | 21,919 |
| hors-render-v1 | 50.82 | 27.42 | 16.64 | 0 | 7,824 | 21,919 |
| V7-ram | 53.31 | 24.61 | 16.05 | 0 | 2,539 | 21,647 |
| V8-ram | 53.31 | 24.61 | 16.05 | 0 | 2,539 | 21,647 |
| V9-ram | 53.40 | 24.61 | 16.18 | 0 | 2,539 | 21,647 |
| hors-render-v1-ram | 50.85 | 27.42 | 16.68 | 0 | 7,824 | 21,647 |

### SPHERE

| Method | High | Average | Low | Resident frame-table RAM (B) | Frame data ROM (B) | Runtime PRG (B) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| step | 25.05 | 13.63 | 12.53 | 12,710 | 0 | 37,749 |
| bytechunk | 25.06 | 15.00 | 12.53 | 12,710 | 0 | 37,749 |
| yunroll | 25.06 | 15.50 | 12.53 | 12,710 | 0 | 37,749 |
| cart scaffold | 25.06 | 15.50 | 12.53 | 12,710 | 0 | 37,749 |
| V2 | 16.71 | 12.25 | 10.02 | 0 | 12,638 | 16,553 |
| V3 | 16.93 | 13.16 | 10.02 | 0 | 12,638 | 18,433 |
| V4 | 16.97 | 13.16 | 10.28 | 0 | 12,638 | 18,433 |
| V5 | 23.92 | 13.66 | 12.04 | 0 | 6,314 | 21,919 |
| V6 | 25.06 | 14.26 | 11.93 | 0 | 6,314 | 21,919 |
| V7 | 18.00 | 14.67 | 11.89 | 0 | 5,824 | 21,919 |
| V8 | 18.00 | 14.67 | 11.89 | 0 | 5,824 | 21,919 |
| V9 | 18.01 | 14.67 | 11.89 | 0 | 5,824 | 21,919 |
| hors-render-v1 | 25.11 | **15.87** | 11.88 | 0 | 18,108 | 21,919 |
| V7-ram | 17.90 | 13.46 | 11.91 | 0 | 5,824 | 21,647 |
| V8-ram | 17.90 | 13.46 | 11.91 | 0 | 5,824 | 21,647 |
| V9-ram | 18.02 | 13.46 | 11.93 | 0 | 5,824 | 21,647 |
| hors-render-v1-ram | 25.16 | 15.87 | 11.87 | 0 | 18,108 | 21,647 |

### HORSE HEAD

| Method | High | Average | Low | Resident frame-table RAM (B) | Frame data ROM (B) | Runtime PRG (B) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| step | 16.71 | 12.15 | 10.02 | 22,658 | 0 | 49,076 |
| bytechunk | 25.06 | 12.92 | 10.02 | 22,658 | 0 | 49,076 |
| yunroll | 25.06 | 13.23 | 10.02 | 22,658 | 0 | 49,076 |
| cart scaffold | 25.06 | 13.23 | 10.02 | 22,658 | 0 | 49,076 |
| V2 | 16.58 | 10.55 | 8.41 | 0 | 22,562 | 16,609 |
| V3 | 16.71 | 11.65 | 9.64 | 0 | 22,562 | 18,433 |
| V4 | 16.71 | 11.75 | 9.93 | 0 | 22,562 | 18,433 |
| V5 | 17.13 | 12.46 | 9.79 | 0 | 21,447 | 21,777 |
| V6 | 17.56 | 12.86 | 9.75 | 0 | 21,447 | 21,777 |
| V7 | 17.75 | 13.76 | 9.87 | 0 | 18,245 | 21,777 |
| V8 | 17.75 | 13.76 | 9.87 | 0 | 18,245 | 21,777 |
| V9 | 25.90 | 13.86 | 9.77 | 0 | 18,245 | 21,777 |
| hors-render-v1 | 52.46 | **27.42** | 16.55 | 0 | 30,840 | 21,777 |
| V7-ram | 25.06 | 12.76 | 9.75 | 0 | 18,245 | 18,433 |
| V8-ram | 25.06 | 12.76 | 9.75 | 0 | 18,245 | 18,433 |
| V9-ram | 17.51 | 12.76 | 9.62 | 0 | 18,245 | 18,433 |
| hors-render-v1-ram | 52.58 | 27.42 | 16.60 | 0 | 30,840 | 18,433 |

### SUNFLOWER TORUS

| Method | High | Average | Low | Resident frame-table RAM (B) | Frame data ROM (B) | Runtime PRG (B) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| step | 16.71 | 11.02 | 8.35 | 21,752 | 0 | 48,971 |
| bytechunk | 16.71 | 11.35 | 10.02 | 21,752 | 0 | 48,971 |
| yunroll | 16.71 | 11.55 | 10.02 | 21,752 | 0 | 48,971 |
| cart scaffold | 16.71 | 11.55 | 10.02 | 21,752 | 0 | 48,971 |
| V2 | 12.61 | 9.44 | 8.17 | 0 | 21,668 | 16,581 |
| V3 | 16.55 | 10.25 | 8.35 | 0 | 21,668 | 18,433 |
| V4 | 16.48 | 10.35 | 8.35 | 0 | 21,668 | 18,433 |
| V5 | 16.71 | 10.95 | 9.96 | 0 | 20,777 | 21,777 |
| V6 | 25.08 | 11.15 | 9.74 | 0 | 20,777 | 21,777 |
| V7 | 25.55 | 12.15 | 9.75 | 0 | 17,168 | 21,777 |
| V8 | 25.55 | 12.15 | 9.75 | 0 | 17,168 | 21,777 |
| V9 | 25.46 | 12.15 | 9.74 | 0 | 17,168 | 21,777 |
| hors-render-v1 | 53.22 | **27.12** | 16.25 | 0 | 29,308 | 21,777 |
| V7-ram | 16.89 | 11.15 | 8.31 | 0 | 17,168 | 18,433 |
| V8-ram | 16.89 | 11.15 | 8.31 | 0 | 17,168 | 18,433 |
| V9-ram | 25.06 | 11.15 | 9.71 | 0 | 17,168 | 18,433 |
| hors-render-v1-ram | 53.28 | 27.12 | 16.35 | 0 | 29,308 | 18,433 |

### SUNFLOWER COLOR

| Method | High | Average | Low | Resident frame-table RAM (B) | Frame data ROM (B) | Runtime PRG (B) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| step | 16.71 | 9.68 | 8.35 | 19,385 | 0 | 44,450 |
| bytechunk | 16.71 | 9.98 | 8.35 | 19,385 | 0 | 44,450 |
| yunroll | 16.71 | 10.18 | 8.35 | 19,385 | 0 | 44,450 |
| cart scaffold | 16.71 | 10.18 | 8.35 | 19,385 | 0 | 44,450 |
| V2 | 10.28 | 8.04 | 6.92 | 0 | 19,325 | 16,525 |
| V3 | 12.64 | 8.84 | 7.16 | 0 | 19,325 | 18,433 |
| V4 | 12.53 | 8.94 | 7.32 | 0 | 19,325 | 18,433 |
| V5 | 16.36 | 9.34 | 8.11 | 0 | 18,597 | 21,777 |
| V6 | 16.71 | 9.74 | 8.32 | 0 | 18,597 | 21,777 |
| V7 | 17.60 | 10.45 | 8.35 | 0 | 16,028 | 21,777 |
| V8 | 17.60 | 10.45 | 8.35 | 0 | 16,028 | 21,777 |
| V9 | 16.71 | 10.55 | 8.35 | 0 | 16,028 | 21,777 |
| hors-render-v1 | 53.04 | **19.99** | 12.53 | 0 | 24,790 | 21,777 |
| V7-ram | 17.64 | 9.74 | 8.14 | 0 | 16,028 | 18,433 |
| V8-ram | 17.64 | 9.74 | 8.14 | 0 | 16,028 | 18,433 |
| V9-ram | 16.71 | 9.74 | 8.18 | 0 | 16,028 | 18,433 |
| hors-render-v1-ram | 52.91 | 19.99 | 12.53 | 0 | 24,790 | 18,433 |

### SPACE HORSE SPIN

| Method | High | Average | Low | Resident frame-table RAM (B) | Frame data ROM (B) | Runtime PRG (B) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| step | 12.53 | 9.98 | 8.35 | 21,930 | 0 | 48,828 |
| bytechunk | 12.53 | 10.55 | 8.35 | 21,930 | 0 | 48,828 |
| yunroll | 12.53 | 10.65 | 8.35 | 21,930 | 0 | 48,828 |
| cart scaffold | 12.53 | 10.65 | 8.35 | 21,930 | 0 | 48,828 |
| V2 | 10.10 | 8.54 | 7.17 | 0 | 21,858 | 16,553 |
| V3 | 12.46 | 9.34 | 8.17 | 0 | 21,858 | 18,433 |
| V4 | 12.53 | 9.44 | 8.27 | 0 | 21,858 | 18,433 |
| V5 | 50.13 | 10.15 | 8.21 | 0 | 20,489 | 21,777 |
| V6 | 50.14 | 10.55 | 8.22 | 0 | 20,489 | 21,777 |
| V7 | 50.13 | 10.65 | 8.19 | 0 | 20,119 | 21,777 |
| V8 | 50.13 | 10.65 | 8.19 | 0 | 20,119 | 21,777 |
| V9 | 52.80 | 10.75 | 8.23 | 0 | 20,119 | 21,777 |
| hors-render-v1 | 52.06 | **17.58** | 12.17 | 0 | 34,107 | 21,777 |
| V7-ram | 50.12 | 9.94 | 8.35 | 0 | 20,119 | 18,433 |
| V8-ram | 50.12 | 9.94 | 8.35 | 0 | 20,119 | 18,433 |
| V9-ram | 50.48 | 10.04 | 8.21 | 0 | 20,119 | 18,433 |
| hors-render-v1-ram | 50.13 | 17.58 | 12.52 | 0 | 34,107 | 18,433 |

### SPACE HORSE CRAWL

| Method | High | Average | Low | Resident frame-table RAM (B) | Frame data ROM (B) | Runtime PRG (B) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| step | 25.07 | 15.13 | 10.02 | 23,680 | 0 | 49,153 |
| bytechunk | 25.07 | 16.61 | 12.53 | 23,680 | 0 | 49,153 |
| yunroll | 25.07 | 16.61 | 12.53 | 23,680 | 0 | 49,153 |
| cart scaffold | 25.07 | 16.61 | 12.53 | 23,680 | 0 | 49,153 |
| V2 | 17.59 | 12.86 | 9.81 | 0 | 23,584 | 16,609 |
| V3 | 23.66 | 14.06 | 10.02 | 0 | 23,584 | 18,433 |
| V4 | 24.95 | 14.26 | 10.08 | 0 | 23,584 | 18,433 |
| V5 | 25.06 | 14.67 | 10.04 | 0 | 22,981 | 21,777 |
| V6 | 25.95 | 15.47 | 9.69 | 0 | 22,981 | 21,777 |
| V7 | 26.93 | 16.57 | 10.01 | 0 | 20,603 | 21,777 |
| V8 | 59.03 | 22.90 | 12.13 | 0 | 17,765 | 21,777 |
| V9 | 52.42 | 23.51 | 12.18 | 0 | 17,765 | 21,777 |
| hors-render-v1 | 52.44 | **35.56** | 16.60 | 0 | 20,292 | 21,777 |
| V7-ram | 25.65 | 16.27 | 12.20 | 0 | 20,603 | 18,433 |
| V8-ram | 58.38 | 22.70 | 12.12 | 0 | 17,765 | 18,433 |
| V9-ram | 53.29 | 23.30 | 12.13 | 0 | 17,765 | 18,433 |
| hors-render-v1-ram | 54.09 | 35.66 | 16.60 | 0 | 20,292 | 18,433 |

### FALLING CUBES

| Method | High | Average | Low | Resident frame-table RAM (B) | Frame data ROM (B) | Runtime PRG (B) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| step | 25.07 | 13.56 | 10.02 | 12,804 | 0 | 38,586 |
| bytechunk | 50.12 | 14.80 | 10.02 | 12,804 | 0 | 38,586 |
| yunroll | 50.13 | 14.90 | 10.02 | 12,804 | 0 | 38,586 |
| cart scaffold | 50.13 | 14.90 | 10.02 | 12,804 | 0 | 38,586 |
| V2 | 25.06 | 11.55 | 8.29 | 0 | 12,750 | 16,511 |
| V3 | 24.98 | 12.46 | 9.82 | 0 | 12,750 | 18,433 |
| V4 | 25.06 | 12.66 | 9.74 | 0 | 12,750 | 18,433 |
| V5 | 25.06 | 13.16 | 9.93 | 0 | 12,542 | 21,777 |
| V6 | 27.75 | 13.66 | 9.74 | 0 | 12,542 | 21,777 |
| V7 | 26.97 | 13.86 | 9.81 | 0 | 12,007 | 21,777 |
| V8 | 27.06 | 13.86 | 9.83 | 0 | 12,007 | 21,777 |
| V9 | 28.15 | 13.86 | 9.83 | 0 | 12,007 | 21,777 |
| hors-render-v1 | 50.15 | **19.69** | 12.28 | 0 | 19,518 | 21,777 |
| V7-ram | 26.82 | 13.46 | 9.76 | 0 | 12,007 | 18,433 |
| V8-ram | 26.68 | 13.46 | 9.76 | 0 | 12,007 | 18,433 |
| V9-ram | 27.26 | 13.56 | 9.78 | 0 | 12,007 | 18,433 |
| hors-render-v1-ram | 27.46 | 19.59 | 12.13 | 0 | 19,518 | 18,433 |

### HORSE HEAD HIFI

| Method | High | Average | Low | Resident frame-table RAM (B) | Frame data ROM (B) | Runtime PRG (B) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| step | N/A¹ | N/A¹ | N/A¹ | N/A | N/A | N/A |
| bytechunk | N/A¹ | N/A¹ | N/A¹ | N/A | N/A | N/A |
| yunroll | N/A¹ | N/A¹ | N/A¹ | N/A | N/A | N/A |
| cart scaffold | N/A¹ | N/A¹ | N/A¹ | N/A | N/A | N/A |
| V2 | 8.69 | 7.03 | 6.16 | 0 | 147,346 | 17,281 |
| V3 | 10.15 | 7.84 | 7.00 | 0 | 147,346 | 18,433 |
| V4 | 10.03 | 7.94 | 7.03 | 0 | 147,346 | 18,433 |
| V5 | 10.22 | 8.34 | 7.00 | 0 | 141,625 | 21,777 |
| V6 | 12.53 | 8.64 | 7.00 | 0 | 141,625 | 21,777 |
| V7 | 13.00 | 10.14 | 8.11 | 0 | 105,831 | 21,777 |
| V8 | 25.06 | 10.15 | 8.10 | 0 | 105,759 | 21,777 |
| V9 | 50.17 | 10.25 | 8.08 | 0 | 105,759 | 21,777 |
| hors-render-v1 | 51.01 | **20.69** | 15.67 | 0 | 158,181 | 21,777 |
| V7-ram | 12.98 | 9.34 | 8.09 | 0 | 105,831 | 18,433 |
| V8-ram | 27.19 | 9.44 | 8.07 | 0 | 105,759 | 18,433 |
| V9-ram | 50.13 | 9.54 | 8.10 | 0 | 105,759 | 18,433 |
| hors-render-v1-ram | 51.33 | 20.79 | 15.72 | 0 | 158,181 | 18,433 |

### SUNFLOWER TORUS HIFI

| Method | High | Average | Low | Resident frame-table RAM (B) | Frame data ROM (B) | Runtime PRG (B) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| step | N/A¹ | N/A¹ | N/A¹ | N/A | N/A | N/A |
| bytechunk | N/A¹ | N/A¹ | N/A¹ | N/A | N/A | N/A |
| yunroll | N/A¹ | N/A¹ | N/A¹ | N/A | N/A | N/A |
| cart scaffold | N/A¹ | N/A¹ | N/A¹ | N/A | N/A | N/A |
| V2 | 9.83 | 4.72 | 3.60 | 0 | 247,481 | 17,281 |
| V3 | 10.30 | 5.42 | 4.16 | 0 | 247,481 | 18,433 |
| V4 | 10.17 | 5.42 | 4.13 | 0 | 247,481 | 18,433 |
| V5 | 12.36 | 5.83 | 4.51 | 0 | 230,752 | 21,777 |
| V6 | 12.97 | 6.03 | 4.56 | 0 | 230,752 | 21,777 |
| V7 | 16.85 | 6.83 | 5.01 | 0 | 181,152 | 21,777 |
| V8 | 50.16 | 12.46 | 6.27 | 0 | 160,415 | 21,777 |
| V9 | 56.34 | 14.46 | 6.27 | 0 | 160,415 | 21,777 |
| hors-render-v1 | 57.46 | **19.89** | 12.53 | 0 | 163,780 | 21,777 |
| V7-ram | 12.84 | 6.43 | 5.01 | 0 | 181,152 | 18,433 |
| V8-ram | 60.30 | 12.05 | 6.27 | 0 | 160,415 | 18,433 |
| V9-ram | 56.71 | 14.06 | 6.19 | 0 | 160,415 | 18,433 |
| hors-render-v1-ram | 60.62 | 19.89 | 12.53 | 0 | 163,780 | 18,433 |


## Storage and fixed RAM allocations

| Method | Comparison CRT bytes | Entries | Runtime PRG size range, bytes | Fixed bitmap + screen storage | Stream staging + metadata caches |
| --- | ---: | ---: | ---: | ---: | ---: |
| step | 500,752 | 10 | 35,381–49,153 | 27,000 B | 0 B |
| bytechunk | 500,752 | 10 | 35,381–49,153 | 27,000 B | 0 B |
| yunroll | 500,752 | 10 | 35,381–49,153 | 27,000 B | 0 B |
| cart scaffold | 500,752 | 10 | 35,381–49,153 | 27,000 B | 0 B |
| V2 | 968,608 | 12 | 16,511–17,281 | 27,000 B | 11,264 B |
| V3 | 968,608 | 12 | 18,433–18,433 | 27,000 B | 11,264 B |
| V4 | 968,608 | 12 | 18,433–18,433 | 27,000 B | 11,264 B |
| V5 | 927,568 | 12 | 21,777–21,919 | 27,000 B | 11,264 B |
| V6 | 927,568 | 12 | 21,777–21,919 | 27,000 B | 11,264 B |
| V7 | 804,448 | 12 | 21,777–21,919 | 27,000 B | 11,264 B |
| V8 | 771,616 | 12 | 21,777–21,919 | 27,000 B | 11,264 B |
| V9 | 771,616 | 12 | 21,777–21,919 | 27,000 B | 11,264 B |
| hors-render-v1 | 985,024 | 12 | 21,777–21,919 | 27,000 B | 11,264 B |
| V7-ram | 804,448 | 12 | 18,433–21,647 | 27,000 B | 11,264 B |
| V8-ram | 771,616 | 12 | 18,433–21,647 | 27,000 B | 11,264 B |
| V9-ram | 771,616 | 12 | 18,433–21,647 | 27,000 B | 11,264 B |
| hors-render-v1-ram | 985,024 | 12 | 18,433–21,647 | 27,000 B | 11,264 B |

Fixed graphics storage counts three 8,000-byte bitmaps and three 1,000-byte screen-colour matrices. Streamed methods also reserve 8,192 bytes staging and three 1,024-byte metadata caches. These are allocation components, **not total used or free RAM**: renderer code, LUTs, state, directories, menu/control storage and padding also occupy address space. RAM preference saves code but does not reclaim those fixed buffers. PRG length includes load address and gaps; it must not be added to these figures as if it were a disjoint allocation. The resident comparison CRT has fewer entries because HiFi does not fit, so its whole-cart size is not directly comparable to twelve-entry streamed carts.

| Animation | Resident frame tables (RAM bytes) | V2–V4 vectors (ROM bytes) | V5 | V6 | V7 | V8 | V9 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| TORUS | 18,760 | 18,664 | 18,500 | 18,500 | 16,505 | 16,505 | 16,505 |
| TORUS DENSE | 22,081 | 21,985 | 21,767 | 21,767 | 18,302 | 18,302 | 18,302 |
| CUBE | 10,264 | 10,156 | 2,539 | 2,539 | 2,539 | 2,539 | 2,539 |
| SPHERE | 12,710 | 12,638 | 6,314 | 6,314 | 5,824 | 5,824 | 5,824 |
| HORSE HEAD | 22,658 | 22,562 | 21,447 | 21,447 | 18,245 | 18,245 | 18,245 |
| SUNFLOWER TORUS | 21,752 | 21,668 | 20,777 | 20,777 | 17,168 | 17,168 | 17,168 |
| SUNFLOWER COLOR | 19,385 | 19,325 | 18,597 | 18,597 | 16,028 | 16,028 | 16,028 |
| SPACE HORSE SPIN | 21,930 | 21,858 | 20,489 | 20,489 | 20,119 | 20,119 | 20,119 |
| SPACE HORSE CRAWL | 23,680 | 23,584 | 22,981 | 22,981 | 20,603 | 17,765 | 17,765 |
| FALLING CUBES | 12,804 | 12,750 | 12,542 | 12,542 | 12,007 | 12,007 | 12,007 |
| HORSE HEAD HIFI | N/A | 147,346 | 141,625 | 141,625 | 105,831 | 105,759 | 105,759 |
| SUNFLOWER TORUS HIFI | N/A | 247,481 | 230,752 | 230,752 | 181,152 | 160,415 | 160,415 |

Resident table bytes count pointer, clear/colour and line records, excluding renderer code/LUTs. ROM bytes count unique encoded frame blocks, excluding menu/runtime/CHIP headers and unused bank space. These figures explain capacity tradeoffs; they do not pretend to be a free-RAM measurement.

¹ N/A means the complete dataset does not fit that preserved resident implementation. In the shipped dataset, 128 HiFi orientations exceed the 64-entry pointer arena, and HiFi sunflower also exceeds the 8-bit run-count limit. Exact per-method rejection reasons are in the external `*-unsupported.json` files. No frames, geometry or colours were removed to force a result. `yunroll-cart` is the initial resident scaffold, not V2 streaming.

## Authored scenes: separate paced diagnostics

These are **not PLAY ALL A/B FPS results** and must not be mixed into the menu tables or used to rank renderer throughput. The unchanged authored sequence runs with its original pacing and intro/ending behavior. Samples/s includes waits; mean active render cycles shows rendering cost. Clean/HUD Marbles and Horse & Sunflower use matching full source samples across V4–V10, frozen in `assets/comparison-scene-vector-reference.json.gz` from the original V4/V7 cartridges. No external history directory is required. For V10, the monitor acknowledges the indefinite SPACE build screen through its normal exit before running the authored intro; no cartridge bytes or measured renderer instructions are changed. Earlier generations do not provide the authored scene backend.

| Scene | Method | Samples/s (paced) | Mean render cycles | Worst render cycles | Over-budget samples |
| --- | --- | ---: | ---: | ---: | ---: |
| marbles-clean | V4-scene | 5.504 | 168,769 | 329,444 | 134 / 200 |
| marbles-clean | V5-scene | 6.237 | 142,997 | 304,457 | 107 / 200 |
| marbles-clean | V6-scene | 6.364 | 137,812 | 297,383 | 93 / 200 |
| marbles-clean | V7-scene | 6.568 | 125,941 | 282,700 | 47 / 200 |
| marbles-clean | V8-scene | 6.903 | 83,822 | 282,735 | 8 / 200 |
| marbles-clean | V9-scene | 6.903 | 78,073 | 280,843 | 8 / 200 |
| marbles-clean | V10-scene | 7.149 | 57,446 | 106,461 | 0 / 200 |
| marbles-hud | V4-scene | 5.499 | 168,959 | 329,882 | 135 / 200 |
| marbles-hud | V5-scene | 6.227 | 143,252 | 304,859 | 107 / 200 |
| marbles-hud | V6-scene | 6.357 | 137,957 | 297,677 | 93 / 200 |
| marbles-hud | V7-scene | 6.569 | 126,052 | 282,842 | 47 / 200 |
| marbles-hud | V8-scene | 6.899 | 83,970 | 283,024 | 8 / 200 |
| marbles-hud | V9-scene | 6.904 | 78,212 | 281,085 | 8 / 200 |
| marbles-hud | V10-scene | 7.145 | 57,590 | 106,810 | 0 / 200 |
| horse-sunflower | V4-scene | 3.350 | 293,992 | 301,458 | 84 / 84 |
| horse-sunflower | V5-scene | 4.132 | 203,307 | 296,295 | 59 / 84 |
| horse-sunflower | V6-scene | 4.275 | 195,348 | 284,084 | 59 / 84 |
| horse-sunflower | V7-scene | 4.279 | 195,116 | 283,624 | 59 / 84 |
| horse-sunflower | V8-scene | 4.279 | 195,116 | 283,624 | 59 / 84 |
| horse-sunflower | V9-scene | 4.301 | 193,946 | 282,090 | 59 / 84 |
| horse-sunflower | V10-scene | 7.335 | 99,173 | 146,290 | 57 / 84 |

## Workload and interpretation

- All menu builds use the exact released V4 vector reference (`assets/v4-menu-vector-reference.json.gz`), including colours, HUD and animation sample order. Native method-specific lossless encoding is retained.
- This table compares preserved renderer implementations under one **external comparison PLAY ALL wrapper**, not the exact historical release cartridges. The V9 normal PLAY ALL controller is used for every method. Its identical timer instructions live at `$0334` instead of `$c700`, because resident data occupies `$c700`; launch metadata is cached before loading and shared menu data restored between entries. Renderer code is unchanged apart from the existing cartridge IRQ-vector redirection. All these wrapper adaptations are generated outside the repo.
- Resident and streamed methods have different memory/ROM costs. A faster resident method does not imply it can hold the larger HiFi datasets. Compare the same named animation and sample count.
- A frame count tie is reported as a tie; a few extra samples over roughly 30 seconds are a small gain. Compare individual animations before quoting a suite total.
- Full bitmap and colour verification covered **20,693 completed pictures**. Raw traces, cartridge hashes, per-entry oracle hashes, unsupported-build reasons and individual results remain in the external workspace.
- These measurements do not establish a universal performance floor or guarantee behavior for untested inputs.

## Reproduce and keep this chart current

Run from the repository root. The tool defaults to ignored `comparison-tests/`; an external `--workspace` is also supported. It creates an isolated source snapshot and never writes old test cartridges into `examples` or `build` in this checkout. Python, 64tass, cartconv and PAL VICE with its data files are required.

```bash
python tools/compare_renderers.py \
  --workspace ../c64-renderer-comparison \
  --tass 64tass --cartconv cartconv --vice x64sc \
  --vice-data /usr/local/share/vice

# Only after the complete run succeeds:
cp ../c64-renderer-comparison/PERFORMANCE_COMPARISON.md docs/PERFORMANCE_COMPARISON.md
python tools/compare_renderers.py --check
```

Future demos: `--current-demos` compiles the current registry once and tests every resulting named entry across methods. Alternatively pass `--reference-json dataset.json.gz` in the `c643d-vector-reference-v1` format. Dataset files are saved outside tracked source and frozen for all methods. RAM-limited resident combinations are reported as N/A without dropping frames; bank capacity/build failures stop the comparison rather than silently simplify it. New renderer generations must be added to `METHODS` and the supported builders; chart rows themselves come from the data, not a twelve-row constant.

Optional pacing: `--max-fps 10` creates separate paced comparison carts after the uncapped pass. Integer rates 1–50 are supported; 10 FPS holds five PAL refreshes, while 12 FPS alternates four/five. `--lock-to-min-fps` measures two complete uncapped animation cycles, chooses a fixed per-demo refresh interval from the worst frame plus one refresh guard, then builds and verifies the paced copy. These options are mutually exclusive and **off by default** (`fps locking: not set`). A fixed cap cannot make an overloaded renderer meet a deadline; reports include observed hold intervals and missed deadlines. Pacing applies to these experimental menu reels, not the unchanged authored-scene timing or normal shipped cartridges. Paced/subset runs do not generate the release chart.

Use `--resume` only with the same source/tool fingerprint and options. Logs and JSON reports stay outside the repo. Archive that workspace with the release if long-term raw evidence is needed.

**Release gate:** run `--check` before publishing. If renderer code, builders, input assets, examples, version or this tester changes, rerun the complete uncapped matrix and replace this chart before tagging. Preserve old method rows; add new generations to the tester and regenerate. Never silently copy old numbers into a changed workload. Capped runs are separate experiments and must not replace this uncapped baseline.

<!-- comparison-input-sha256: 35d598ce28519fcc95da2d38b9386c85053dec3c013e9eb7055086f46696cf2d -->
<!-- comparison-source-version: 0.7.1 -->
