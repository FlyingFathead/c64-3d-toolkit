# Toolchain configuration

`c64-3d-toolkit` can run with no configuration file. Built-in defaults are:

```ini
64tass executable: 64tass
VICE executable:   x64sc
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
tass_args =
vice_args = +VICIIfull

[macos]
tass = /opt/homebrew/bin/64tass
vice = /Applications/VICE.app

[windows]
tass = C:\Tools\64tass\64tass.exe
vice = C:\Tools\VICE\bin\x64sc.exe
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

Downloaded VICE packages can have a less obvious layout. Depending on the package/version, `x64sc.app` may be a launcher while the usable command-line launcher/binary lives in a sibling `tools/x64sc`, `bin/x64sc`, or inside `VICE.app/Contents/Resources/bin/x64sc`. The toolkit probes those layouts automatically when possible.

For example, any of these can be used as `vice = ...` if they match the local installation:

```text
/Applications/VICE.app
/Applications/vice-arm64-gtk3-3.8/VICE.app
~/Downloads/vice-arm64-gtk3-3.8
```

Run `doctor` after configuring:

```bash
./build.sh doctor
```

It reports the resolved executables, configured arguments, active platform and loaded config file.

## Windows

`c643d.py` itself is cross-platform Python. On Windows, executable names in `PATH` or full `.exe` paths can be used in the same config. `build.sh` requires a Bash environment such as Git Bash or WSL; without one, invoke the Python frontend directly, for example:

```powershell
python .\c643d.py doctor
python .\c643d.py build --shape torus --run
```
