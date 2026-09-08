# Cartridge capacity and optimization budgets

The current toolkit targets EasyFlash: **1 MiB (1,048,576 bytes) of flash total**, shared by boot code, renderer, menus, metadata and animation payloads. Music and other additions must also fit. This is a hardware-target limit, not a universal C64 cartridge limit.

EasyFlash has 64 banks with two 8 KiB regions per bank. The current builder allocates frame data within available regions and rejects overflow without reducing animation samples. Individual frame blocks must fit its 8 KiB window.

CRT disk size includes container headers. Empty regions can be omitted; included regions can contain padding. File-size subtraction therefore does not measure usable free flash. Report packed payload, allocated banks, padding and reserved areas separately when choosing candidates.

## Larger targets

| Target | Documented flash | Toolkit status |
| --- | --- | --- |
| EasyFlash | 1 MiB | Current supported target |
| GMod3 | 2–16 MB depending on version | Not supported; manufacturer says it was not mass produced and was superseded by GMod4 |
| GMod4 | 8 MB | Potential future backend; not implemented or validated here |

Larger flash is accessed through cartridge-specific banking. A larger target needs matching image format, allocator, boot code, bank switching, runtime memory-map handling and hardware/emulator validation. Increasing a constant in the EasyFlash builder is insufficient. Larger storage does not itself increase CPU speed or internal RAM.

GMod4 provides banked ROM windows and a different register layout; its 8 MB capacity uses an additional switch between 4 MB regions. This warrants a separate backend experiment rather than changing preserved EasyFlash implementations.

## Optimization decision

Keep EasyFlash as the existing compatibility target. Evaluate speed against explicit ROM and RAM budgets, retaining room for future content. A larger backend could permit more precomputed pictures, but resulting speed must still be measured. No music coexistence or extra free RAM is claimed by the current byte-policy experiment.

The byte-policy confirmation bundle passed its supplied SHA-256 check and reports all four candidates completed. Raw results remain outside tracked documentation. Capacity figures must not be confused with whole-menu CRT sizes or per-demo costs.

## Primary references

- [EasyFlash programmer guide](https://skoe.de/easyflash/files/devdocs/EasyFlash-ProgRef.pdf)
- [GMod3 hardware documentation](https://wiki.icomp.de/wiki/GMod3)
- [GMod4 hardware documentation](https://wiki.icomp.de/wiki/GMod4)

## hors-render-v1 delivered examples

The hors-render-v1 twelve-demo menu is 985,024 CRT bytes in either preference.
Horse/Sunflower is 279,136 bytes in either preference. The accepted 640-sample
Marbles cart is **902,944 bytes**; no HUD/RAM counterpart is validated for that
sampling. The earlier 344,800-byte Marbles figures describe the historical
200-sample export. All current cartridges fit EasyFlash individually; this does
not establish that they fit together. Fresh 1,000/800-sample exports have no fit
guarantee. See [inventory](V10_CARTRIDGES.md) and [build targets](V10_TESTING.md).
