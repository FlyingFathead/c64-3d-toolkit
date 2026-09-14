#!/usr/bin/env bash
# Local virtual-environment setup; optional Debian/Ubuntu package installation.
set -euo pipefail
c643d_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
c643d_python=python3
c643d_venv="$c643d_root/.venv"
c643d_system=0
c643d_check=0
c643d_svg=1
c643d_args=()
while (($#)); do
    case "$1" in
        --python|--venv)
            if (($# < 2)); then echo "error: $1 needs a value" >&2; exit 2; fi
            if [[ "$1" == --python ]]; then c643d_python="$2"; else c643d_venv="$2"; fi
            shift 2 ;;
        --system-deps) c643d_system=1; shift ;;
        --check) c643d_check=1; c643d_args+=(--check); shift ;;
        --repair) c643d_args+=(--repair); shift ;;
        --svg) c643d_svg=1; c643d_args+=(--svg); shift ;;
        --core) c643d_svg=0; c643d_args+=(--core); shift ;;
        -h|--help)
            echo 'Usage: bash setup-linux.sh [--system-deps] [--core] [--repair|--check] [--python PATH] [--venv PATH]'
            echo 'Default: create/reuse .venv and install ALL host Python requirements, including SVG.'
            echo '--system-deps explicitly installs Debian/Ubuntu Python venv, 64tass and VICE packages.'
            echo 'Blender is optional and installed/configured separately. Existing config is preserved.'
            exit 0 ;;
        *) echo "error: unknown option: $1" >&2; exit 2 ;;
    esac
done
if ((c643d_check && c643d_system)); then
    echo 'error: --check cannot install --system-deps' >&2; exit 2
fi
if ((c643d_system)); then
    if ! command -v apt-get >/dev/null; then
        echo 'error: --system-deps supports apt-based Debian/Ubuntu; install your distro packages separately.' >&2
        exit 2
    fi
    c643d_packages=(python3 python3-venv python3-pip 64tass vice)
    if ((c643d_svg)); then c643d_packages+=(libcairo2); fi
    if ((EUID == 0)); then
        apt-get install "${c643d_packages[@]}"
    else
        sudo apt-get install "${c643d_packages[@]}"
    fi
fi
if ! command -v "$c643d_python" >/dev/null; then
    echo "error: Python not found: $c643d_python. Install Python 3 or pass --python PATH." >&2; exit 2
fi
if [[ ! -x "$c643d_venv/bin/python" ]]; then
    if ((c643d_check)); then
        echo "error: no environment at $c643d_venv. Run bash setup-linux.sh first." >&2; exit 2
    fi
    if ! "$c643d_python" -m venv "$c643d_venv"; then
        echo 'error: could not create the environment. On Debian/Ubuntu install python3-venv, or use --system-deps.' >&2
        exit 2
    fi
fi
"$c643d_venv/bin/python" "$c643d_root/setup-python.py" "${c643d_args[@]}"
echo 'Python requirements are ready. Activate this environment before building:'
printf '  source %q/bin/activate\n' "$c643d_venv"
echo 'Then run: python c643d.py doctor'
echo 'doctor checks configured 64tass/VICE/cartconv and optional Blender; setup preserves config/c643d.ini.'
