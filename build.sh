#!/usr/bin/env bash
set -euo pipefail
HERE="$(cd -- "$(dirname -- "$0")" && pwd)"
cd "$HERE"

if ! command -v python3 >/dev/null 2>&1; then
  echo "error: python3 not found; c64-3d-toolkit requires Python 3." >&2
  exit 2
fi

# Shortcuts:
#   ./build.sh --shape torus --run       -> build command
#   ./build.sh run --shape torus         -> build + --run
#   ./build.sh --generate-examples       -> compile reference PRGs into examples/
#   ./build.sh doctor                    -> check 64tass/VICE availability
#   ./build.sh inspect ...               -> direct CLI subcommand
#   ./build.sh import-obj ...            -> direct CLI subcommand
case "${1:-}" in
  run)
    shift
    exec python3 ./c643d.py build --run "$@"
    ;;
  --generate-examples)
    shift
    exec python3 ./c643d.py generate-examples "$@"
    ;;
  build|inspect|import-obj|generate-examples|doctor|list-shapes|list-objects)
    exec python3 ./c643d.py "$@"
    ;;
  *)
    exec python3 ./c643d.py build "$@"
    ;;
esac
