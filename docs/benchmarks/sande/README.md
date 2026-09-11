# Sande's Models: measured evidence

`summary.json` records the standalone v1/v2 FPS/RAM builds and separate
interactive HORS-V2 builds, including source hashes, cartridge hashes,
display intervals and pixel checks. `controls.json` records reverse/forward
wraparound and the emulated input/palette checks, including F2 white flash,
F5 toggle, F6/F7 speed limits, persistent F8 black border and Ctrl+F7 custom
border. Interactive timings include the INTERACTIVE label, cycling off,
about one colour event per second and the fastest requested event rate.

`summary-color.json` measures the separate original-MTL colour variants
with the same standalone v1/v2 FPS/RAM protocol. `colors.json` verifies
the material palette and two full rotations of each included colour cart.
`methods-color.json` and `historical-color/` retain the corresponding
complete historical renderer comparison. Bw and material colours have
separate tables and share the same rotation recipe.

`methods.json` aggregates the complete historical renderer matrix.
`historical/sande_pretzel/` and `historical/sande_tac2/` retain the original
per-method JSON evidence and source/tool provenance from those runs.
The benchmark's safety cycle limit was subsequently increased to retain
the per-entry startup allowance for larger menus; neither measured windows
nor renderer instructions changed. These provenance files describe the
actual measurement snapshot and have not been relabelled.

All models keep their original topology and the same 192 Y-axis orientations.
Capacity failures are explicit N/A cases. The standalone gap-6 carts and
historical gap-3 PLAY ALL comparison have separate tables and protocols.

See [the performance page](../../PERFORMANCE_COMPARISON.md#sandes-models)
and [the kit instructions](../../../examples/demos_sande/README.md).
Run `bash RUN-SANDE-CHECKS.sh` from the repository root to collect a new
shareable `sande-perf-logs.zip` beside the checkout.
