# Installation and dependency repair

Install from the toolkit root after cloning or extracting the complete release.
The installers read `requirements.txt`: NumPy, Pillow, CairoSVG and defusedxml,
plus dependencies resolved by pip. Python libraries must be installed in the
same interpreter used to run `c643d.py`. Installing Python alone does not install
these libraries. Builds check their Python dependencies before conversion and
exit with code 2 and repair instructions if a library is missing, too old or
unable to load. Help, version and listing commands remain usable.

## Windows

```powershell
.\setup-windows.cmd
py -3 .\c643d.py dependencies
py -3 .\c643d.py doctor
py -3 .\c643d.py build --shape cube
```

Windows setup checks the full Python requirement set after configuring the C64
tools and offers to install missing libraries with pip. It runs pip through
the same Python executable/launcher it checked. It reports incomplete setup
if the libraries cannot load; it does not run Blender, 64tass or VICE.
[External tool installation and config preservation](WINDOWS_SETUP.md).

To install or repair just the Python packages, without reconfiguring tools:

```powershell
py -3 .\setup-python.py
py -3 .\setup-python.py --repair
```

`--repair` forces package reinstallation without using pip's cache. Use it for
a broken installation; a missing package usually needs only the first command.
For the specific `No module named 'numpy'` error, `py -3 -m pip install numpy`
is also sufficient to install that package. The installer covers the whole set.
If using a virtual environment, run its `python` instead of `py -3` for both
installation and builds. The error message prints an exact installer command
for the interpreter that failed.

CairoSVG also needs the native Cairo runtime. pip installs the Python packages,
but cannot guarantee that a system Cairo DLL exists. If that check fails,
follow the [CairoSVG Windows runtime instructions](https://cairosvg.org/documentation/),
make the runtime visible to the same Python process, then rerun
`py -3 .\setup-python.py --check`. Setup does not download arbitrary DLLs or
silently report full success with Cairo missing. `--core` explicitly selects
NumPy/Pillow only when SVG conversion is not needed.

## Linux

```sh
bash setup-linux.sh
source .venv/bin/activate
python c643d.py dependencies
python c643d.py doctor
python c643d.py build --shape cube
```

The root script creates/reuses `.venv` and installs the full Python requirement
set there. It preserves system Python and `config/c643d.ini`. On Debian/Ubuntu,
this explicit option also installs Python venv/pip, 64tass, VICE and native Cairo
through apt (administrator access is required):

```sh
bash setup-linux.sh --system-deps
```

Other distributions should install their equivalent packages first. Blender is
an external optional tool needed for `.blend` input; install it through your
distribution or configure an existing Blender path. VICE ROM availability
depends on its installation. `doctor` reports external tool paths and runs
their version/probe commands; it does not install them.

Repair or check the environment without changing tool paths:

```sh
bash setup-linux.sh --repair
bash setup-linux.sh --check
```

`--python PATH` chooses the Python used to create the environment; `--venv PATH`
chooses its location. `--core` explicitly omits SVG packages. For an existing
activated environment, `python setup-python.py` installs the full requirements
there, and `python setup-python.py --repair` repairs them. No `sudo pip` or
system-Python protection override is used.

## Dependency inventory

| Component | Used for | Installation |
| --- | --- | --- |
| NumPy, Pillow | Surface, texture and image conversion | `requirements.txt` via the installers |
| CairoSVG, defusedxml | Filled SVG paint and safe XML parsing | Included in the full Python installation |
| Cairo native runtime | CairoSVG rendering | apt option on Debian/Ubuntu; host runtime on Windows |
| 64tass | C64 assembly | Windows tool setup or system packages |
| VICE/cartconv | CRT creation and emulator playback | Windows tool setup or system packages |
| Blender | `.blend` scene export | Optional external installation; its `bpy` belongs to Blender |
| PyMuPDF | Reproducing the original SAKU PDF extraction | Optional authoring helper, not needed to build/play its supplied SVG/cart |

`requirements-core.txt` is the explicit minimal profile. `requirements-svg.txt`
remains a compatibility include for the full requirement set. New mandatory
Python imports must be added to the requirement files and the import mapping
in `tools/c643d/dependencies.py` so installation and checks stay aligned.

`python setup-python.py --check` and `python c643d.py dependencies` check only
Python imports/versions (including Cairo loading), with no installation or
external C64 tool execution. `python c643d.py dependencies --core` checks the
minimal profile. If pip itself is unavailable, restore pip in that Python or
recreate its virtual environment before retrying; pip's error remains visible.
