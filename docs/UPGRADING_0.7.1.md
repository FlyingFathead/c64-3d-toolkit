> Historical version documentation. Current builds and prebuilt examples use [hors-render-v2](HORS_RENDER_V2.md); see [0.7.2 release instructions](RELEASE_0.7.2.md). Older preview binaries are in prior release ZIPs or the external local archive.

# Upgrade to 0.7.1

This release adds a [separate HiFi exhibition reel](../examples/cart_hifi/README.md)
and updates menu presentation and release identity while retaining the
hors-render-v1 drawing implementation and original scene/object cartridge bytes.
Normal PLAY ALL and F5 keep their existing schedules. Current menus are:

- [FPS preference](../examples/cart_demos/c643d-demo-v0.7.1-hors-render-v1-all.crt)
- [RAM preference](../examples/cart_demos/c643d-demo-v0.7.1-hors-render-v1-all-ram.crt)

## Apply the package

Save `c64-3d-toolkit-v0.7.1.zip` in `~/c64-work/`, then extract from that
parent directory. The ZIP contains the `c64-3d-toolkit/` tree and includes the
previous documentation fix. Preserve any later local source edits before overlaying.

```bash
(
set -euo pipefail
cd ~/c64-work
unzip -oq c64-3d-toolkit-v0.7.1.zip
cd c64-3d-toolkit
python perf/prune_old_examples.py
python c643d.py --version
python tools/compare_renderers.py --check
python -m unittest discover -s tests
git diff --check
git status --short
)
```

The cleanup moves superseded v0.7.0 menu outputs into the external sibling
archive and retains the new menus. Existing standalone/scene carts retain their
original labels and manifests; they were not rerendered or renamed for this
presentation update. VERSION and the Python/Windows setup identity become 0.7.1.

The saved comparison is regenerated for the v0.7.1 source fingerprint. It still
uses the common normal PLAY ALL comparison controller, not an exhibition mode.
Release menu-control validation is separate from that matched renderer chart.

## Commit, tag, push and release

After reviewing the changes and checks, commit on `main`, create a new annotated
`v0.7.1` tag, and publish that tag with a source archive from the same commit.
Keep the existing `v0.7.0` tag unchanged. Applying this ZIP does not commit or
publish anything. See CHANGELOG.md for the release notes.

Run these commands from the project directory after reviewing `git diff`:

```bash
(
set -euo pipefail
test "$(git branch --show-current)" = main
test "$(cat VERSION)" = 0.7.1
python tools/compare_renderers.py --check
python -m unittest discover -s tests
git diff --check
if git rev-parse --verify --quiet refs/tags/v0.7.1 >/dev/null; then
  echo 'v0.7.1 already exists; inspect it before continuing.' >&2
  exit 1
fi
git add -A -- README.md CHANGELOG.md VERSION setup-windows.cmd setup-windows.ps1 c64 tools tests perf docs assets examples objects
git diff --cached --check
git diff --cached --stat
git commit -m "Release v0.7.1: HiFi presentations and documentation"
git tag -a v0.7.1 -m "c64-3d-toolkit v0.7.1"
git archive --format=zip --prefix=c64-3d-toolkit/ \
  -o ../c64-3d-toolkit-v0.7.1-release.zip v0.7.1
git push origin main
git push origin v0.7.1
)
```

With GitHub CLI installed and authenticated, publish the tagged archive:

```bash
(
set -euo pipefail
c64_release_notes=$(mktemp)
trap 'rm -f "$c64_release_notes"' EXIT
awk '/^## 0\.7\.1:/{copy=1;next} copy && /^## /{exit} copy{print}' \
  CHANGELOG.md > "$c64_release_notes"
gh release create v0.7.1 ../c64-3d-toolkit-v0.7.1-release.zip \
  --verify-tag --title "c64-3d-toolkit v0.7.1" --notes-file "$c64_release_notes"
)
```
