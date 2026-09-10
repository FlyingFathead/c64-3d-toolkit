# 0.7.2 test launcher fix 1

The first Linux run passed 180 unit tests, the 264-sample beta boundary test
(531 checked pictures), and six v1 showcase scenes. VICE then terminated with
SIGTRAP while creating a GTK style context during the v1 Ripples Lite check.
That log does not identify what triggered the GTK error; a CPU JAM or another
emulator error could be hidden by a dialog failure in console mode.

The picture verifier inherited saved VICE resources, unlike the canonical
comparison and PLAY ALL benchmark. This launcher makes every test start with
factory defaults, disables saving settings, and sets CPU JAM action to quit.
It retains stdout/stderr for every process. CPU JAM is explicitly treated as
a failure even if VICE returns status zero. No assertion or frame check is
skipped, and the benchmark still uses emulated C64 cycles.

This patch changes only the test launcher and all-checks shell script. It does
not change renderer/encoder code, scene inputs, CRT bytes, or prior charts.
The actual VICE executable version/hash and launcher hash are saved together;
the canonical tester's tool hash will now identify the launcher.

Extract this small ZIP over the existing 0.7.2 checkout:

```bash
cd ~/NeuralNetwork
unzip -o c64-3d-toolkit-0.7.2-vice-launch-fix1.zip -d c64-3d-toolkit
cd c64-3d-toolkit
JOBS=3 VICE_DATA=/usr/local/share/vice bash RUN-0.7.2-CHECKS.sh \
  ../c64-072-local-tests-retry1
```

Use a new results directory to keep the original failed run intact. The checks
rerun from the start. If another failure occurs, the tail of the console output
and `c64-072-local-tests-retry1/vice-logs/` retain the emulator evidence.
The saved desktop VICE configuration is not modified. VICE 3.10 is supported;
the small allocation warnings printed by `--version` are not the SIGTRAP shown
in the failed test log.

For individual Python test commands, use `--vice "$PWD/VICE-BATCH.sh"`. The
launcher finds `x64sc` on PATH, or accepts the actual executable through
`C64_VICE_REAL`. `C64_VICE_LOG_DIR` selects its persistent log directory. The
all-checks script sets both automatically. Do not use this test launcher for
your normal interactive VICE session: it deliberately restores defaults.

VICE resource-file behavior is documented in the official
[settings manual](https://vice-emu.sourceforge.io/vice_6.html). The launcher
options and JAM action numbers were checked against VICE 3.10's local CLI help.
