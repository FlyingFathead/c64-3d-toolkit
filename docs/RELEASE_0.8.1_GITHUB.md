Authored Blender scenes can now pass through the camera without crashing conversion. Geometry clips at the near plane and viewport, fully invisible samples remain in the timeline, and objects can reappear without losing frames.

- **Blender colours:** `--blender-color-space linear|srgb`, an INI default and an interactive chooser. `--configure-blender-color-space srgb` saves the setting directly. Standard linear interpretation remains the default; the palette and explicit material indices are unchanged.
- **Demo Cart v3.1:** all 58 selectable entries and 6,474 pictures, improved help and menu return, SPACE/Enter launch, next/previous navigation, and stars disabled at startup/reset.
- **Setup and CLI:** dependency installation/repair, actionable errors, version/author banner, grouped help and `--help-all`.
- **Diagnostics:** one clipping summary, `--ignore-warnings`, an original camera-crossing example, updated documentation and numbered checkpoint archives.

Stale root monitor logs are copied into ignored `logs/` with unique timestamps and verified before removal. VICE logging destinations and tracked-log release cleanup are corrected.

318 tests passed; three optional historical tests skipped. Native PAL VICE checks passed for the camera example on GMod3, EasyFlash and resident PRG output. All 71 original cartridge binaries are preserved. Existing interactive A/B evidence records a median 0.24% average-FPS reduction for the v3.1 input fixes; no general speedup is claimed. Physical hardware, NTSC and Windows execution were not validated during this update.

The source ZIP includes the toolkit and examples. The standalone Demo Cart v3.1 CRT is attached separately for immediate use.

[Full release notes](https://github.com/FlyingFathead/c64-3d-toolkit/blob/v0.8.1/docs/RELEASE_0.8.1.md) · [Camera-crossing example](https://github.com/FlyingFathead/c64-3d-toolkit/tree/v0.8.1/examples/camera_crossing) · [Installation](https://github.com/FlyingFathead/c64-3d-toolkit/blob/v0.8.1/docs/INSTALLATION.md)
