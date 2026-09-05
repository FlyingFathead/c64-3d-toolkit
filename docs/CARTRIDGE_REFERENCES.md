# Cartridge development references

These references informed the cartridge/streaming design work.  They are
reference material, not bundled third-party source code.  Forum posts, blog
articles, and AI-generated/AI-assisted notes are treated as leads and practical
examples; hardware behaviour is checked against primary documentation and the
actual tools/emulator used by the project.

## Primary EasyFlash documentation

- **EasyFlash Programmer's Reference** - the main hardware/programming reference
  for EasyFlash registers, banking, startup state, memory mapping, flash access,
  and cartridge RAM:
  https://skoe.de/easyflash/files/devdocs/EasyFlash-ProgRef.pdf

## VICE / cartconv

- **VICE project** - emulator and cartridge-tool implementation used for
  behavioural cross-checking and testing:
  https://vice-emu.sourceforge.io/
- **VICE source mirror** - useful when checking EasyFlash emulation and
  `cartconv` implementation details:
  https://github.com/VICE-Team/svn-mirror

The project tests against the actual `x64sc` and `cartconv` binaries available
in its configured toolchain rather than assuming remembered command-line
syntax.

## C64 technical documentation

- **C64-Wiki: Cartridge** - overview of cartridge types, cartridge boot-up, and
  expansion-port mapping:
  https://www.c64-wiki.com/wiki/Cartridge
- **C64-Wiki: EasyFlash** - EasyFlash overview and practical background:
  https://www.c64-wiki.com/wiki/EasyFlash

## Practical implementations / discussions

These are useful for implementation patterns, failure modes, and historical
context, but should not override the hardware reference.

- **Lemon64: cartridge creation discussion**:
  https://www.lemon64.com/forum/viewtopic.php?t=6643
- **Lemon64: cartridge-related development discussion**:
  https://www.lemon64.com/forum/viewtopic.php?t=78108
- **Lemon64: creating cartridge files / practical CRT discussion**:
  https://www.lemon64.com/forum/viewtopic.php?t=72351
- **hackup.net: Turn a BASIC Program into a Cartridge for the C64** - clear
  walk-through of the `CBM80` signature, reset vector, an 8 KiB cartridge
  bootloader, raw binary layout, and a `cartconv` example:
  https://www.hackup.net/2019/04/turn-a-basic-program-into-a-cartridge-for-the-c64/
- **IEEE Spectrum: Build Your Own Commodore 64 Cartridge** - useful modern
  physical-cartridge account, including a real-hardware mapping mistake that
  did not appear during the author's VICE development loop:
  https://spectrum.ieee.org/commodore-64-cartridge
- **Retrocomputing Stack Exchange: Help understanding the Commodore 64
  cartridge memory use and lifecycle** - useful historical context on
  cartridges that can become transparent after startup, with the accepted
  answer tracing the technique to Michael R. Mossman's 1987 *Transactor*
  article. This is not an EasyFlash programming recipe; it is background on
  expansion-port lifecycle/mapping techniques:
  https://retrocomputing.stackexchange.com/questions/32020/help-understanding-the-commodore-64-cartridge-memory-use-and-lifecycle
- **Retrocomputing Stack Exchange: Behaviour of $D000-$D3FF on the C64 during
  bankswitching** - supplementary PLA/memory-map discussion useful for
  visualizing how `/GAME`, `/EXROM`, and the 6510 `$01` control bits interact.
  EasyFlash-specific behaviour is still taken from the Programmer's Reference:
  https://retrocomputing.stackexchange.com/questions/5714/behaviour-of-d000-d3ff-section-on-the-c64-during-bankswitching

## Additional community / AI-assisted research material

- **Boris Schneider-Johne: C64 Programming with AI** - EasyFlash conversion,
  debugging, VICE automation, and filesystem experience, plus a separately
  published C64 knowledge pack offered for community use:
  https://www.dreisechzig.net/c64-programming-with-ai.html
- **Claude C64 Knowledge June 2026** - the knowledge package described above is
  available from Boris Schneider-Johne's web page at the link above. It was
  reviewed locally as supplementary human-readable notes and tooling. It is not
  redistributed by this project, and no third-party code should be copied into
  c64-3d-toolkit unless its license and provenance are explicitly compatible.

## Reference policy

When references disagree or an old web example is ambiguous:

1. prefer the EasyFlash Programmer's Reference for mapper/hardware behaviour;
2. compare against VICE's current EasyFlash implementation and `cartconv`;
3. test the exact generated CRT under the configured VICE version;
4. keep emulator-only success distinct from real-hardware validation;
5. treat forum/blog/AI material as a hypothesis to test, not an authority.
