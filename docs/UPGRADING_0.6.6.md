# Updating to v0.6.6

This package adds the early beta of Don't Lose Your Marbles as separate Blender
and cartridge examples. The existing v0.6.5 twelve-demo menu cart stays intact.
The full ZIP contains the complete source tree; the incremental ZIP contains
changed/new files relative to the uploaded v0.6.5 source. Either also updates
the earlier Marbles beta. Both extract under `c64-3d-toolkit/`.

For downloads saved in `~/NeuralNetwork/`, apply **one** source package:

```bash
cd ~/NeuralNetwork
unzip -o c64-3d-toolkit-v0.6.6-changed.zip
cd c64-3d-toolkit
python3 c643d.py --version
x64sc -cartcrt examples/cart_marbles/dont_lose_your_marbles-yunroll-cart-v4-scene-clean.crt
```

For a full source copy, substitute `c64-3d-toolkit-v0.6.6-full.zip` in the unzip
command. Your local `config/c643d.ini` is omitted from both packages. The demo-only
ZIP contains the ready-to-run HUD and clean CRTs, reports and screenshots.

The `*-v4-scene` assembly files are updated extension files. The baseline V4
renderer and original menu cartridge are unchanged; see the exact explanation
in [CARTRIDGE_SCENES.md](CARTRIDGE_SCENES.md). The changed-file list and validation
summary are in `examples/cart_marbles/package-notes.json`.

The demo is finite: roughly 58 seconds through the final typed ghost message,
then an idle cursor. The BASIC screen is staged. Audio has not been added yet.
This package prepares version 0.6.6 locally; publishing/tagging on GitHub is a
separate step.

The prior looping Marbles beta is archived under
`examples/old/cart_marbles/early-test-v0.6.5/`, labelled **early concept tryout**.
The update includes those original bytes before replacing the active Marbles files.
