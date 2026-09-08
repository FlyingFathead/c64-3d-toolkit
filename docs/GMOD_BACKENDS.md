# GMod cartridge backend plan

Status: design only. No GMod renderer or production target is implemented by this documentation change.

## Targets and validation

EasyFlash supports 1 MiB; GMod3 documents 2–16 MB variants; GMod4 documents 8 MB. GMod3 was not mass-produced and was superseded by GMod4. The VICE manual lists GMod3. This does not establish GMod4 support or revision compatibility in the installed emulator; inspect and test those before promising support.

## Implementation boundaries

Separate cartridge hardware from picture encoding. Keep preserved EasyFlash assemblers, layouts and binaries intact; add new target-specific files. The host can reuse source pictures and encoding policies while a backend supplies allocation, image format, boot and bank access.

GMod3 uses an 8 KiB window at $8000 and an 11-bit bank selection scheme. Existing V9 accesses to both ROML and ROMH therefore need a new reader; changing the CRT type alone cannot work. Account for IRQ vectors and RAM visibility explicitly.

GMod4 has distinct banking/control registers and selectable ROM windows. Its extra capacity bit changes entire 4 MB regions, including normally fixed ROM content. Place or duplicate required boot/trampoline content accordingly. Do not assume optional or revision-specific hardware features are available.

## Milestones

1. Confirm exact toolchain support and target hardware revision. Add capacity and bank-address unit tests plus image round-trip checks.
2. Build a minimal boot cartridge. Read known signatures from every bank, especially beyond 1 MiB and across GMod4's 4 MB boundary. Verify reset and RAM visibility.
3. Implement independent stream helpers and directories with sufficiently wide bank addressing. Audit register ownership and IRQ-safe bank restoration.
4. Integrate one source-identical demo, verifying bitmap and colour references. Compare emulated-cycle timing with EasyFlash.
5. Expand to all menu entries, FPS/RAM preferences, authored scenes, handoffs and endings. Include crossing-boundary and near-capacity synthetic cases.
6. Test music coexistence with explicit RAM/IRQ budgets and actual physical hardware. Publish supported revisions and remaining limitations.

Use ignored comparison-tests/ and logs/ for generated images and traces. Record measured results and decisions in tracked documentation. Never infer speed gains merely from increased capacity, and never silently discard frames to meet a budget.

## Sources

- [EasyFlash programmer guide](https://skoe.de/easyflash/files/devdocs/EasyFlash-ProgRef.pdf)
- [GMod3 manufacturer documentation](https://wiki.icomp.de/wiki/GMod3)
- [GMod4 manufacturer documentation](https://wiki.icomp.de/wiki/GMod4)
- [VICE cartridge support](https://vice-emu.sourceforge.io/vice_7.html)

## August 2026 specification: implementation checks

The supplied manufacturer page revision (20 August 2026, oldid 10536) links a [preliminary VICE patch](https://sourceforge.net/p/vice-emu/patches/368/) and [example repository](https://gitlab.icomp.de/icomp-oem/gmod4). Their presence provides an emulator-development route; neither patch compatibility nor its match to the August 2026 hardware has yet been verified here.

- Target the 2026 register layout explicitly. Initialize both contexts before enabling banking; retain control bit 6 on later writes that should keep banking active.
- Resolve a documentation inconsistency before implementation: the register table assigns context B to $DE08–$DE0B and control mirrors to $DE0C–$DE0F, while the context-switching prose says $DE0C–$DE0F selects B. Cross-check implementation and hardware; do not silently choose the contradictory prose.
- Context A and B expose different $DE00 read pages. Any trampoline/interrupt code using that page must account for its changing immediately on a context switch.
- Switching the upper 4 MB region also changes fixed ROM/vector/trampoline contents. Ensure execution and interrupt handling remain valid across this transition.
- First implement ordinary banked reads with AGR and intrusive mode disabled. Intrusive mode is not a standard retail feature; AGR has documented machine-compatibility restrictions.
- Bank contexts might reduce interrupt bank-save/restore work, but music coexistence remains an untested integration hypothesis. A dual context does not itself make nested IRQ/NMI handling safe.
- Keep example-code licensing distinct from the GPL emulator patch. Review applicable terms before incorporating manufacturer code; the page describes other code as restricted to use with their hardware.

This is a prototype plan, not a claim of shipping GMod4 support. Finish the current EasyFlash byte-policy evaluation independently so larger hardware support cannot invalidate its measurements.

## GMod3 implementation reference

Source: [GMod3 specification, revision 10320](https://wiki.icomp.de/w/index.php?title=GMod3&oldid=10320), supplied for this design review. The page is marked work in progress; verify behavior against the chosen emulator and hardware before treating this backend as supported.

GMod3 presents one 8 KiB ROM window at $8000. Its address-selected bank-high bits and written bank-low byte form a single 11-bit bank number, not eight independent bank contexts.

| Flash capacity | Valid bank numbers | Bank-select write addresses |
| --- | --- | --- |
| 2 MiB | 0–255 | $DE00 |
| 4 MiB | 0–511 | $DE00–$DE01 |
| 8 MiB | 0–1023 | $DE00–$DE03 |
| 16 MiB | 0–2047 | $DE00–$DE07 |

Select bank N by writing its low eight bits to $DE00 + (N >> 8). These write addresses are fully decoded and have no mirrors. In normal mode, read $DE00 for the low bank byte and $DE08 for the upper three bits; the upper-bit read is mirrored through $DE0F. Bank selection resets to zero.

### Control register and interrupt ownership

Writes to $DE08 set control state. Reads at the same address return bank-high bits, not control state; retain a software shadow if required.

| Control bit | Meaning when set | Backend consideration |
| --- | --- | --- |
| 7 | SPI bitbang mode | Normal ROM access and bank readback cease; keep disabled for streaming |
| 6 | Disable 8K cartridge mode | Audit $01 mapping and RAM visibility alongside this setting |
| 5 | Override interrupt/vector region | Reserve and initialize zero-page handlers before enabling |
| 4–0 | Unused | Write zero |

The optional vector override covers $FFF8–$FFFF independently of $01 and directs NMI to $0008, IRQ to $000C and the reset vector to $800C. Normal reset clears the override, but a factory option can change that assumption. A backend must explicitly document its supported reset configuration and audit zero-page ownership before using these addresses. This is not a drop-in replacement for the existing EasyFlash interrupt layout.

### Flash writes are a separate future feature

For initial rendering support, leave bitbang mode off. If a writer is later implemented, execute it from RAM, save the bank before entering, and restore the mapping afterward. The specification recommends selecting bank 255 before entry. $DE00 bits 6, 5 and 4 drive chip-select, clock and data-in; chip-select is active-low. Read serial data-out in bit 7, with $DE10 the example repository's chosen read address. Use the flash device's erase/program protocol rather than assuming arbitrary single-byte overwrites.

### Required GMod3 probes

- Read unique signatures from every supported bank, including 255/256, 511/512 and 1023/1024 boundaries where capacity permits.
- Test bank readback, reset, ROM hiding and RAM visibility with the actual $01 configurations used by the renderer.
- Validate interrupt entry and bank restoration while streaming; test vector override separately if enabled.
- Translate the current two-window EasyFlash frame addressing into the single GMod3 ROM window using a new backend. Preserve all historical runtime files.

## Hardware and implementation links

- [GMod3 hardware documentation](https://wiki.icomp.de/wiki/GMod3)
- [GMod3 example repository](https://gitlab.icomp.de/icomp-oem/gmod3)
- [GMod4 hardware documentation](https://wiki.icomp.de/wiki/GMod4)
- [GMod4 example repository](https://gitlab.icomp.de/icomp-oem/gmod4)
- [Preliminary GMod4 VICE patch](https://sourceforge.net/p/vice-emu/patches/368/)

The linked repositories and patch are implementation references to inspect, not code already incorporated or validated by this project. Review their respective licenses before reuse.

## Inspected toolchain and reference revision

The GMod4 reference repository was inspected at commit `d36b978fcd70e9c269f6c8468d5145d775540067`. Its README explicitly targets the 2026 prototype. `include/gmod4.inc` defines context B at $DE08 and B bank registers at $DE09–$DE0B, agreeing with the specification table rather than the conflicting prose. This is source corroboration, not physical-hardware verification.

The supplied VICE tool bundle's `cartconv --types` lists GMod3 as CRT type 62 and does not list GMod4. Its x64sc binary contains GMod3 emulation symbols/options. No GMod4 support was established in that supplied build; no GMod3 functional cartridge probe has yet been run here.

The reference repository supplies `vice/gmod4-r46196.diff`. Its accompanying readme reports missing snapshot support, nonworking AGR, incomplete intrusive-mode behavior and unverified C128 behavior. Treat it as a separate experimental emulator build, with an exact recorded patch revision. Do not replace the existing benchmark emulator or assume feature completeness. Some patch comments also differ from the register include; audit executable register decoding before testing.
