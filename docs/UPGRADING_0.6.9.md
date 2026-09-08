# Apply v0.6.9 / V9 to your published v0.6.8 checkout

Download the changes ZIP and checksum file to `~/NeuralNetwork/`.
The changes ZIP contains paths relative to `c64-3d-toolkit/`; the full ZIP has
its own `c64-3d-toolkit-v0.6.9/` top-level directory for a fresh unpack.

The overlay adds V9 and updates shared builders, version identity, tests and
documentation. It preserves every shipped V8-and-earlier assembly and CRT/PRG
file. No V8 examples are removed, and no cleanup step is needed for this release.
The existing `clean_release.py` remains unchanged and retains its narrow rc1
archive behaviour if you choose to run it separately.

Back up the local checkout before overlaying shared files. This also preserves
any local edits to files that the overlay updates:

```bash
(
set -euo pipefail
cd ~/NeuralNetwork
sha256sum --ignore-missing -c c64-3d-toolkit-v0.6.9-final-SHA256SUMS.txt

tar -czf "c64-3d-toolkit-before-v0.6.9-$(date +%Y%m%d-%H%M%S).tar.gz" \
  c64-3d-toolkit
unzip -o c64-3d-toolkit-v0.6.9-changes-final.zip -d c64-3d-toolkit
cd c64-3d-toolkit

test "$(cat VERSION)" = "0.6.9"
python -m unittest discover -s tests
python tools/compare_renderers.py --check
git diff --check
git status --short
)

x64sc -pal +easyflashcrtwrite -cartcrt \
  ~/NeuralNetwork/c64-3d-toolkit/examples/cart_demos/history/c643d-demo-v0.6.9-yunroll-cart-v9-all.crt
```

**ONLY use normal PLAY ALL for A/B comparisons between rendering methods and
versions. F5 is an internal demo mode for exhibitions and MUST NOT be used for
benchmarking.** Compare matching FPS/RAM preferences and PAL settings.
Normal PLAY ALL keeps 10 seconds per demo. F5 keeps the two HiFi entries at
15 seconds and all others at 10 seconds. F1/RUN-STOP exits; SPACE skips.

The old comparison cartridge stays at:

```bash
x64sc -pal +easyflashcrtwrite -cartcrt \
  ~/NeuralNetwork/c64-3d-toolkit/examples/cart_demos/history/c643d-demo-v0.6.8-yunroll-cart-v8-all.crt
```

The [V9 guide](CARTRIDGE_STREAM_V9.md) includes measurements, limits and
reproducible normal PLAY ALL benchmarking commands. The 139 unit tests include
118 frozen historical source/executable hashes. If you intentionally edited
one of those files locally, inspect the named mismatch against your backup.

## Commit, tag, archive and publish after reviewing locally

The delivered package does not push or publish automatically. Once satisfied:

```bash
(
set -euo pipefail
cd ~/NeuralNetwork/c64-3d-toolkit
test "$(cat VERSION)" = "0.6.9"
test "$(git branch --show-current)" = "main"
gh auth status
git fetch origin
git merge-base --is-ancestor origin/main HEAD
if git rev-parse --verify refs/tags/v0.6.9 >/dev/null 2>&1; then
  echo "Tag v0.6.9 already exists; stopping."
  exit 1
fi
c64_release_notes=$(mktemp)
trap 'rm -f "$c64_release_notes"' EXIT
awk '
  /^## 0\.6\.9([ :]|$)/ { section=1; next }
  section && /^## / { exit }
  section { print }
' CHANGELOG.md > "$c64_release_notes"
test -s "$c64_release_notes"
git add -A
git diff --cached --check
git diff --cached --stat
git commit -m "Release v0.6.9: V9 direct ROM byte spans"
git tag -a v0.6.9 -m "c64-3d-toolkit v0.6.9"
git archive --format=zip --prefix=c64-3d-toolkit-v0.6.9/ \
  --output=../c64-3d-toolkit-v0.6.9.zip v0.6.9
(
  cd ..
  sha256sum c64-3d-toolkit-v0.6.9.zip > c64-3d-toolkit-v0.6.9.zip.sha256
)
git push --atomic origin main refs/tags/v0.6.9
gh release create v0.6.9 --repo FlyingFathead/c64-3d-toolkit \
  --verify-tag --title "v0.6.9 — V9 direct ROM byte spans" \
  --notes-file "$c64_release_notes" \
  ../c64-3d-toolkit-v0.6.9.zip ../c64-3d-toolkit-v0.6.9.zip.sha256 \
  examples/cart_demos/history/c643d-demo-v0.6.9-yunroll-cart-v9-all.crt \
  examples/cart_demos/history/c643d-demo-v0.6.9-yunroll-cart-v9-all-ram.crt
git status --short
gh release view v0.6.9 --repo FlyingFathead/c64-3d-toolkit
)
```

V9 is now the default for `build`, `cart-stream` and `cart-demos`; authored inputs
use V9-scene. For the historical resident PRG path, specify `--renderer yunroll`.
All old renderer assembly and shipped PRG/CRT bytes remain preserved.

[See comparison chart for details on performance differences](PERFORMANCE_COMPARISON.md).
The new comparison tester writes only to ignored `comparison-tests/` or an external
workspace. All FPS locking is off by default; optional paced test reels do not
change the normal shipped cartridges.
