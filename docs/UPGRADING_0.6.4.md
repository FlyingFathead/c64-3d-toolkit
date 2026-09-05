# 0.6.4 package notes

The changed-files ZIP contains paths relative to the repository root. Extract
it into your existing `c64-3d-toolkit/` checkout. The full ZIP contains one
`c64-3d-toolkit/` directory. Neither archive contains the external tool bundle,
local tool configuration, generated build workspaces, or Git metadata.

Changes include both HiFi OBJ/MTL/JSON presets; the separate yunroll-cart-v2
renderer; its builder, boot and copy helpers; previews and real VICE framebuffer
captures; standalone 192-orientation CRTs; and the 0.6.4 twelve-demo menu CRT
with 128 orientations per HiFi entry. `c643d-demo.crt` and
`c643d-demo-v0.6.4.crt` are byte-identical aliases. All original model assets and
standalone example PRGs are preserved.

`python3 c643d.py --version` reports 0.6.4. The on-screen cartridge menus show
0.6.4 in all three styles. The menu retains cursors/RETURN, F1 style cycling,
F1/RUNSTOP return and SPACE-next controls for both old and new entries.

Verification: 98 host tests; 387 consecutive exact bitmap/colour comparisons
per standalone stream; 259 per menu stream; all twelve loader payload checksums;
three menu styles; return, next and wrap-to-first control paths in VICE 3.10.
Control-path tests enter existing handlers through the monitor; keyboard matrix
scanning is unchanged. Physical EasyFlash hardware was not available.

Final standalone PAL VICE throughput: horse 7.20 FPS; sunflower 4.94 FPS.
The meshes use culling and surface depth occlusion, static native wire colours,
and actual 3D geometry. The C64 does not fill or shade polygons dynamically.

See README.md, docs/CARTRIDGE_STREAM_V2.md and examples/hifi_showcase/README.md
for operation, reproducible builds and limits. This package does not publish
or modify the remote GitHub repository.
