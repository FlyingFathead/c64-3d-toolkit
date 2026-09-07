# Updating to v0.6.7

The final V7 release keeps the twelve-demo menu, all three F1 styles, the `+`
scroll indicators, PLAY ALL and its ten-second closing screen. Horse and
Sunflower stays a separate scene cartridge. FPS is the default preference.

## Apply the overlay and clean the checkout

Save `c64-3d-toolkit-v0.6.7-overlay.zip` beside your existing project:

```bash
cd ~/NeuralNetwork/c64-3d-toolkit
unzip -o ../c64-3d-toolkit-v0.6.7-overlay.zip
python tools/clean_release.py
python c643d.py --version
x64sc -pal -cartcrt examples/cart_demos/c643d-demo-v0.6.7-yunroll-cart-v7-all.crt
```

The overlay is flat: paths start at `README.md`, `tools/`, `examples/`, etc.
It contains only changed/new files relative to the uploaded rc5 snapshot
`c64-3d-toolkit-2026-09-08_022024.zip`. An overlay cannot delete old files;
the cleanup command handles that step.

`c64-3d-toolkit-v0.6.7-full.zip` is a clean source copy with an enclosing
`c64-3d-toolkit-v0.6.7/` folder. It already has the obsolete files removed.
Keep using the overlay for your existing Git checkout.

## What cleanup does

`tools/clean_release.py` archives these files outside the project:

- Everything under `examples/old/`, including the early Marbles scene.
- Older V4/V5/V6 and superseded V7 candidate menu carts with matching manifests/maps.
- Old flat menu reports, whose retained evidence is now in `docs/benchmarks/cart_demos/`.
- Older obsolete menu filenames recognized by the existing archive helper.
- Generated videos and numbered Blender backups under `examples/` or at the root.

The default destination is `../c64-3d-toolkit-legacy-pre-0.6.7.zip`. Each
archived file is verified against its original before removal. An existing
archive is preserved and the new archive gets a unique filename. Locally edited
copies are saved as they are, so cleanup does not discard local work.

Use `python tools/clean_release.py --dry-run` to list candidates, or
`--archive /path/outside/the/project/legacy.zip` to choose the destination.
Running it again with no new obsolete files makes no changes.

The final menu directory contains only the current FPS/RAM CRTs and README,
plus `metadata/` and `reports/`. Historical menu benchmark evidence lives under
`docs/benchmarks/cart_demos/`. A compact, checksum-verified original V4 vector
reference in `assets/` keeps V5/V6/V7 builds independent of archived menu CRTs.
Editable `.blend` scenes, source assets, PRGs and the separate Marbles/Horse
cartridges remain. Small README stills/GIFs remain; generated videos are ignored
by Git. The supplied oldies ZIP also preserves the removed MP4 preview.

For historical docs that refer to `examples/old/...`, extract the legacy ZIP
into a separate directory and read those original paths there. Extracting it
into the project deliberately restores the old files into an ignored directory.

`.gitignore` only prevents new tracking. Existing tracked files are removed
from the next commit when you stage the cleanup below. This reduces the current
source tree; it does not remove old blobs from Git history or shrink an existing
`.git` directory. No history rewrite or force push is part of this release.

## Commit, tag and push from your checkout

Run these after applying the overlay, running cleanup and reviewing the result:

```bash
git status --short
git diff --stat
git add -A
git diff --cached --stat
git commit -m "Release v0.6.7: V7 rendering, PLAY ALL and repository cleanup"
git tag -a v0.6.7 -m "c64-3d-toolkit v0.6.7"
git push
git push origin v0.6.7
```

`git add -A` records the removed tracked legacy files as well as the source
update; ignored MP4s/archives are not re-added. Review your local changes before
the commit. `git push` uses your current branch's configured upstream. Do not
replace an existing `v0.6.7` tag if Git reports one already exists.

Create the GitHub release from that tag and attach the final source ZIPs,
legacy ZIP and runnable cartridges as release assets. Keep the ZIPs outside
the repository. The top entry in [CHANGELOG.md](../CHANGELOG.md) supplies the
release notes. Publishing is performed from your machine.

## Validation and performance

The renderer, samples and menu logic are unchanged from rc5. Final rebuilds
update version text. The release checks cover Python tests, menu launches
through all three styles, PLAY ALL sequencing and its closing screen.
Reports are under `examples/cart_demos/`; the matched renderer benchmarks
remain documented in [the V7 guide](CARTRIDGE_STREAM_V7.md).

The separate Horse and Sunflower scene uses V7 with FPS preference. Its large
two-mesh close-up still takes about 19.71 seconds for 84 samples in PAL VICE,
about 4.3 samples/s. This release does not claim a new speed improvement for it.
