# Toolchain configuration

`c64-3d-toolkit` can run with no configuration file. Built-in defaults are:

```ini
64tass executable: 64tass
VICE executable:   x64sc
Blender executable: blender (optional; used only by --blend)
VICE arguments:    +VICIIfull
```

`+VICIIfull` tells VICE to disable fullscreen, which is a friendlier default for repeated build/run development cycles.

## Local config

Copy the supplied example:

```bash
cp config/c643d.ini.example config/c643d.ini
```

`config/c643d.ini` is gitignored and is loaded automatically when present. If it does not exist, the built-in defaults are used.

Configuration precedence is:

```text
built-in defaults
    -> [toolchain]
    -> current platform section ([linux], [macos], [windows])
    -> command-line overrides
```

Example:

```ini
[toolchain]
tass = 64tass
vice = x64sc
blender = blender
tass_args =
vice_args = +VICIIfull

[macos]
tass = /opt/homebrew/bin/64tass
vice = /Applications/vice-arm64-gtk3-3.8/bin/x64sc

[windows]
tass = C:\Tools\64tass\64tass.exe
vice = C:\Tools\VICE\bin\x64sc.exe
blender = C:\Program Files\Blender Foundation\Blender 4.0\blender.exe
```

Executable settings can be a command name in `PATH` or a full path. For VICE, a containing distribution directory or a macOS `.app` bundle can also be supplied; the toolkit probes common internal CLI locations.

Extra argument values are parsed as shell-style whitespace-separated arguments. To let VICE use its own saved fullscreen setting instead of forcing windowed mode, clear the default:

```ini
[toolchain]
vice_args =
```

Or explicitly force fullscreen:

```ini
[toolchain]
vice_args = -VICIIfull
```

## Command-line overrides

Existing executable overrides continue to work:

```bash
./build.sh --object horse_head --vice /path/to/x64sc --tass /path/to/64tass --run
```

Extra tool arguments are repeatable. Supplying any CLI tool arguments replaces the corresponding configured argument list:

```bash
./build.sh --shape torus --vice-arg=+VICIIfull --run
```

To suppress configured/built-in arguments for one invocation, without editing the config:

```bash
./build.sh --shape torus --no-vice-default-args --run
```

The matching `--no-tass-default-args` flag is available for 64tass.

Use another config file with:

```bash
./build.sh --config ~/my-c643d.ini --shape torus --run
```

or:

```bash
C643D_CONFIG=~/my-c643d.ini ./build.sh --shape torus --run
```

Ignore all config files for one invocation:

```bash
./build.sh --no-config --shape torus --run
```

## macOS

The simplest command-line installation is currently Homebrew:

```bash
brew install tass64 vice
```

If you download a VICE macOS package directly and move it into `/Applications` as recommended by the package, point the toolkit at the real command-line binary under that package's `bin/` directory. A typical ARM64/GTK3 install looks like:

```ini
[macos]
vice = /Applications/vice-arm64-gtk3-3.8/bin/x64sc
```

The directory name is package-dependent: architecture (ARM64/Intel), frontend (GTK3/SDL2), and VICE version can all change. In other words, treat `vice-arm64-gtk3-3.8` above as an example, not a fixed name.

This direct `bin/x64sc` path is preferred because some downloaded distributions also contain nested `.app` launchers that can be easy to confuse with the CLI executable. With the default `vice = x64sc`, the toolkit also scans common locations such as the `/Applications/vice*/bin/x64sc` pattern automatically. It can additionally accept the containing distribution directory or compatible `.app` paths when needed. For example:

```text
/Applications/vice-arm64-gtk3-3.8/bin/x64sc   # preferred exact CLI path
/Applications/vice-arm64-gtk3-3.8             # containing distribution directory
~/Downloads/vice-arm64-gtk3-3.8                # unpacked/downloaded distribution
```

Run `doctor` after configuring:

```bash
./build.sh doctor
```

It reports the resolved executables, configured arguments, active platform and loaded config file.

64tass and VICE preflight output includes the version reported by each resolved
executable. `doctor` also runs a headless Blender probe and reports
`<version>; bpy OK` when the optional Blender pipeline is usable.

Blender is optional. When `--blend` is selected, the toolkit performs a real
headless `bpy` import probe in addition to executable discovery. Configure an
unusual installation with `blender = ...` or `--blender PATH`. See
[`BLENDER_PIPELINE.md`](BLENDER_PIPELINE.md).

## Windows

`c643d.py` itself is cross-platform Python. On Windows, executable names in `PATH` or full `.exe` paths can be used in the same config. `build.sh` requires a Bash environment such as Git Bash or WSL; without one, invoke the Python frontend directly, for example:

```powershell
python .\c643d.py doctor
python .\c643d.py build --shape torus --run
```

## Render/build defaults (v0.6.2)

Optional output defaults live in a separate `[render_defaults]` section:

```ini
[render_defaults]
text_overlay = true
viewport_height = auto
overwrite_policy = warn
rastertime_profiler = false
```

`text_overlay = true` uses the normal production renderer and an automatic
256x192 drawable viewport, leaving the bottom 8 bitmap scanlines for the HUD/FPS
row. `text_overlay = false` selects a separate no-overlay ASM derivative and
automatically uses the full 256x200 drawable height.

`viewport_height = auto` follows those defaults. An explicit value must be a
multiple of 8 from 8 through 200. Command-line overrides are available as
`--text-overlay`, `--no-text-overlay`, and `--viewport-height LINES`.

`overwrite_policy` controls existing `.prg`, `.lbl`, and `.lst` files:

- `allow`: overwrite silently.
- `warn`: print the exact outputs that already exist, then overwrite them.
- `error`: refuse the build with exit status 2.

`rastertime_profiler = true` selects the derivative yunroll raster-time debug
renderer. It changes the border while the main-loop clear/colour/raster work is
running, making the CPU budget visible in VICE or on a real C64. The production
yunroll source is not conditionally instrumented and therefore pays no code-size
or cycle cost when profiling is disabled.

Command-line options always override `[render_defaults]` for that invocation.
