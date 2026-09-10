# Stable hors-render-v2 patch and complete package

Use the [0.7.2 installation and release guide](docs/RELEASE_0.7.2.md).
The default is now hors-render-v2. Both archives include the VICE batch-launch
fix, all 19 stable example cartridges, replacement metadata, the cleanup script,
release automation, and updated performance documentation.

```bash
cd ~/NeuralNetwork
unzip -o c64-3d-toolkit-0.7.2-hors-v2-overlay.zip -d c64-3d-toolkit
cd c64-3d-toolkit
python3 tools/cleanup_examples.py --apply
```

Old renderer implementations stay selectable. Old prebuilt examples move to
`../c64-3d-toolkit-history/pre-hors-v2/`. No commit, tag or push is performed.
