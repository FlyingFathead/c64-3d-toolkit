> Historical version documentation. Current builds and prebuilt examples use [hors-render-v2](HORS_RENDER_V2.md); see [0.7.2 release instructions](RELEASE_0.7.2.md). Older preview binaries are in prior release ZIPs or the external local archive.

# Apply 0.6.8 to an existing 0.6.7 or 0.6.8-rc1 checkout

> Historical upgrade instructions for the version named above. They are not
> the v0.7.0 installation or release procedure. Use [Upgrading to 0.7.0](UPGRADING_0.7.0.md)
> for the current package. Old generated paths below describe their original
> release layout; superseded outputs are now outside the checkout in
> `../c64-3d-toolkit-history/`, when that optional archive is available.

Download `c64-3d-toolkit-v0.6.8-changes.zip` and the checksum file into
`~/NeuralNetwork/`. The changes ZIP has flat paths relative to the project root.
It contains additions and updates. After extraction, run the updated cleanup
script below to archive and remove superseded 0.6.8-rc1 V8 menu examples.
Earlier rendering methods and pre-V8 comparison CRT/PRG files are preserved.
V8 scene filenames stay the same and receive the final build identity; the
backup below retains your rc1 copies before extraction. The full ZIP contains
a separate `c64-3d-toolkit-v0.6.8/` top-level directory for a fresh checkout.

The following backs up the complete local checkout, including local edits,
before applying updated shared Python files and documentation. Existing local
files with those same names are overwritten by unzip, but remain in the backup.
Files not present in the overlay, including older local comparison carts, stay
where they are. The default `clean_release.py` scope touches only rc1 V8 menu artifacts;
older renderer comparisons remain intact. The archive is written to
`~/NeuralNetwork/c64-3d-toolkit-v0.6.8-rc1-oldies.zip` (an existing archive
is never overwritten).

```bash
(
set -euo pipefail
cd ~/NeuralNetwork
sha256sum --ignore-missing -c c64-3d-toolkit-v0.6.8-SHA256SUMS.txt

tar -czf "c64-3d-toolkit-before-v0.6.8-$(date +%Y%m%d-%H%M%S).tar.gz" \
  c64-3d-toolkit
unzip -o c64-3d-toolkit-v0.6.8-changes.zip -d c64-3d-toolkit
cd c64-3d-toolkit

test "$(cat VERSION)" = "0.6.8"
python tools/clean_release.py
python -m unittest discover -s tests
git diff --check
git status --short
)

x64sc -pal +easyflashcrtwrite -cartcrt \
  ~/NeuralNetwork/c64-3d-toolkit/examples/cart_demos/history/c643d-demo-v0.6.8-yunroll-cart-v8-all.crt
```

The packaged unit tests include byte-for-byte preservation checks against the
102 historical source/binary files from Git commit `718e6c3`. If you intentionally
modified one of those files locally, keep the backup and inspect that test's
named file rather than replacing your work blindly.

For direct comparison, the old cart stays at:

```bash
x64sc -pal +easyflashcrtwrite -cartcrt \
  ~/NeuralNetwork/c64-3d-toolkit/examples/cart_demos/history/c643d-demo-v0.6.7-yunroll-cart-v7-all.crt
```

No automatic Git commit, tag, push or release publication is included. The package prepares the final 0.6.8 release locally; GitHub publication is a separate step.

Normal **PLAY ALL** remains the reference for A/B testing, at 10 seconds per
demo. **F5** from the V8 menu is an **internal demo mode for exhibitions, NOT
for benchmarking**; only its HiFi horse and sunflower holds extend to 15 seconds.

**ONLY use normal PLAY ALL for A/B comparisons between rendering methods and
versions. F5 is an internal demo mode for exhibitions and MUST NOT be used for
benchmarking.**
