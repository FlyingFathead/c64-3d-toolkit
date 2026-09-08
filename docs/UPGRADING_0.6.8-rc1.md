# Apply 0.6.8-rc1 to an existing 0.6.7 checkout

> Historical upgrade instructions for the version named above. They are not
> the v0.7.0 installation or release procedure. Use [Upgrading to 0.7.0](UPGRADING_0.7.0.md)
> for the current package. Old generated paths below describe their original
> release layout; superseded outputs are now outside the checkout in
> `../c64-3d-toolkit-history/`, when that optional archive is available.

Download `c64-3d-toolkit-v0.6.8-rc1-changes.zip` and the checksum file into
`~/NeuralNetwork/`. The changes ZIP has flat paths relative to the project root.
It contains additions and updates only: no deletion list and no cleanup step.
Every existing renderer and shipped CRT/PRG is preserved. The full ZIP contains
a separate `c64-3d-toolkit-v0.6.8-rc1/` top-level directory for a fresh checkout.

The following backs up the complete local checkout, including local edits,
before applying updated shared Python files and documentation. Existing local
files with those same names are overwritten by unzip, but remain in the backup.
Files not present in the overlay, including older local comparison carts, stay
where they are. Do not run `clean_release.py` as part of this update.

```bash
(
set -euo pipefail
cd ~/NeuralNetwork
sha256sum --ignore-missing -c c64-3d-toolkit-v0.6.8-rc1-SHA256SUMS.txt

tar -czf "c64-3d-toolkit-before-v0.6.8-rc1-$(date +%Y%m%d-%H%M%S).tar.gz" \
  c64-3d-toolkit
unzip -o c64-3d-toolkit-v0.6.8-rc1-changes.zip -d c64-3d-toolkit
cd c64-3d-toolkit

test "$(cat VERSION)" = "0.6.8-rc1"
python -m unittest discover -s tests
git diff --check
git status --short
)

x64sc -pal +easyflashcrtwrite -cartcrt \
  ~/NeuralNetwork/c64-3d-toolkit/examples/cart_demos/c643d-demo-v0.6.8-rc1-yunroll-cart-v8-all.crt
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

No automatic Git commit, tag, push or release publication is included. The
version is a release candidate so you can review V8 locally first.
