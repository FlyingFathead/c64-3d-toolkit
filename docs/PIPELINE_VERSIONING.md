# Incremental pipeline versions and comparable evidence

Project rule reaffirmed by the user on 10 September 2026:

**Every new pipeline is an additional selectable version. Preserve the old
implementations so each new result can be compared with its predecessors.**

1. Keep earlier renderer assembly, encoders, formats, entry points and fixtures.
   Add new implementations and explicit names. Do not silently redefine an old
   renderer name to mean the new algorithm. After a beta is shared, algorithm
   changes also need a new beta identifier and retained prior evidence.
2. Pair the encoder and decoder under an explicit format/version. Build-time
   parameters and per-scene policies belong in the manifest. A faster path may
   only reclaim memory after proving its ownership conditions.
3. Compare identical source pictures, colours, HUD, sample counts/order,
   machine settings, timing policy and observation windows. Freeze input
   hashes; reject unsupported combinations explicitly. Do not remove geometry
   or frames to force a result.
4. Add new method rows to the full comparison; retain every old method row,
   including slower methods and N/A results. Report gains, ties and regressions.
   A newest version is not automatically the best method for every scene.
5. Normal PLAY ALL is the comparative menu protocol. F5 exhibition, standalone
   optimization probes, and authored paced scenes are separate results. Keep
   renderer work, waiting, actual display throughput and animation tempo clear.
6. Save source/tool/cartridge/oracle identities, raw measurements, failures,
   ROM/RAM allocation components and correctness results. Treat timer-phase
   noise as a tie rather than a claimed optimization.
7. Update documentation and regenerate the full chart from completed tests
   before pushing a release. Run the provenance check after installing the
   generated chart. A stale chart or failed candidate is not a passing gate.

The initial 0.7.2 work added hors-render-v2-beta1. Existing C64 assembly and encoder
implementations remain intact. The v2 decoder is constructed in an isolated
assembly tree; its named per-scene encoder hook defaults to the original
encoder when unused. Archived original example CRTs keep their bytes and
version labels outside the checkout. New Demo Cart 2.0 has a separate folder and dataset.

The canonical 12-entry v2 comparison uses gap 3 / batch 2048 so its literal
payload sizes fit the same full-cart allocation as v1. The separate seven-entry
showcase has room for measured per-scene choices (including Ripples Lite gap
10). Both policies are recorded, rather than silently treating them as the
same benchmark build.

## Stable v2 adoption

On 10 September 2026 the user independently reproduced the measurements,
reviewed the video and authorized hors-render-v2 as the default. Stable v2
retains the beta drawing kernel, adds object/menu/intro integration, and avoids
constructing an unused vector stream in the host encoder. Beta1 remains
selectable and its historical evidence retains its actual beta identity.

All 67 existing C64 assembly files and older encoders remain intact. Old
prebuilt examples are archived outside the checkout; they are not active
release outputs. The complete comparison adds stable rows alongside beta1
and every older method. Publication requires a current passing chart.
