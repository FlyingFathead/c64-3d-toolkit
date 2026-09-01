# Windows setup

`c64-3d-toolkit` v0.5.1 adds a Windows 11 setup helper.

## First-time bootstrap on Windows 11

If Git is not already installed, install **Git for Windows first** from Microsoft's WinGet `winget` source:

```powershell
winget install --id Git.Git -e --source winget
```

Then clone the toolkit and enter its directory:

```powershell
git clone https://github.com/FlyingFathead/c64-3d-toolkit.git
cd c64-3d-toolkit
```

Now run the setup helper:

```powershell
.\setup-windows.cmd
```

If you already obtained the toolkit another way (for example, a GitHub release ZIP or a copy from another machine), you can run `setup-windows.cmd` directly from the toolkit root. The installer **still checks for Git** and can install it through WinGet if it is missing.

The batch file launches `setup-windows.ps1` from the toolkit root.

## What the installer does

The installer first detects existing tools. When Python, Git, or VICE is missing, it may install the missing component through Microsoft's WinGet `winget` source:

- Python: `Python.Python.3.13`
- Git: `Git.Git`
- VICE (preferred): `VICE-Team.VICE.GTK3`
- VICE (also recognized): `VICE-Team.VICE.SDL2`

The installer does **not** proactively probe Internet hosts. WinGet may contact only its configured `winget` source for exact package-state queries and install/upgrade/reinstall operations. The local preflight reports whether `winget.exe` and Windows `curl.exe` exist; `curl.exe` is informational only and is not used by this installer revision.

The installer does **not** run `64tass`, `c643d.py doctor`, a build, or VICE during setup.


### Existing Windows config behavior

If `config/c643d.ini` already has a `[windows]` section with `tass` and/or `vice`, setup reports each current value as `VALID` or `NOT FOUND` without executing it. You can then:

- `K` / `KEEP` (default): keep valid existing paths and only fill/repair missing or invalid entries.
- `M` / `MODIFY`: allow setup to search/select replacement paths.
- `Q` / `QUIT`: show a summary of what setup has done so far, then save or discard any valid pending tool-path changes before quitting. WinGet package changes are not rolled back.

If setup ends up with a path different from what is currently stored, it shows the exact `current` and `new` values and asks again before writing them. `N` leaves the INI unchanged.

## 64tass on Windows

64tass is deliberately **detect/configure only**. The installer will not automatically download it and will not install MSYS2, pacman, Scoop, Chocolatey, or another third-party package manager.

If 64tass is already in `PATH`, setup will use it. You can also specify the exact executable:

```powershell
.\setup-windows.cmd -TassPath "C:\path\to\64tass.exe"
```

Official upstream locations:

- Project: https://sourceforge.net/projects/tass64/
- Windows binaries: https://sourceforge.net/projects/tass64/files/binaries/
- Source archives: https://sourceforge.net/projects/tass64/files/source/
- Project/manual site: https://tass64.sourceforge.net/

During v0.5.1 release preparation on 2026-08-31, the current upstream Windows binary was `64tass-1.60.3243.zip`.

The 64tass project has a documented history of antivirus false positives affecting MinGW-built Windows binaries. A prebuilt binary being official upstream establishes provenance, not an absolute safety guarantee. Review and verify executables according to your own security policy before running them.

Manual choices include:

1. Download the official SourceForge Windows binary yourself.
2. Build 64tass yourself from the official source archive.
3. Deliberately use the official MSYS2 64tass package yourself if you already use/want MSYS2. The toolkit installer will not install MSYS2 or invoke `pacman` automatically.

After installing a copy you trust, rerun `setup-windows.cmd`, pass `-TassPath` explicitly, or use the local search option:

```powershell
.\setup-windows.cmd -FindTass
```

At the interactive 64tass prompt, `F` / `FIND` does the same thing. It searches only common local locations (toolkit directory, Downloads, Desktop, `%LOCALAPPDATA%\Programs`, `C:\Tools`, and Program Files); it does **not** perform an unrestricted whole-drive scan.

## VICE path override

If VICE is installed but `x64sc.exe` is not detected automatically:

```powershell
.\setup-windows.cmd -VicePath "C:\path\to\VICE\bin\x64sc.exe"
```

The official VICE site is:

https://vice-emu.sourceforge.io/

## Configuration

Before changing an existing Windows configuration, setup inspects `config/c643d.ini`. If a `[windows]` section already contains `tass` and/or `vice`, setup shows the paths and whether they still exist, then asks whether to keep valid existing values or review/modify them.

Before writing any actual difference, setup prints the proposed old -> new values and asks for confirmation. Declining leaves the INI unchanged.

When changes are approved, the installer updates only confirmed `tass`/`vice` values in the `[windows]` section of `config/c643d.ini`, preserving other sections and unrelated settings:

```ini
[windows]
tass = C:\path\to\64tass.exe
vice = C:\path\to\x64sc.exe
```

The correct configuration key is `tass`, not `64tass`.

## Manual validation

Setup does not automatically execute the configured toolchain. After reviewing the paths, validation is explicitly opt-in:

```powershell
py -3 .\c643d.py doctor
```

That command will execute the configured dependency binaries.

## Installer help and adding 64tass later

Run:

```powershell
.\setup-windows.cmd -Help
```

The help output summarizes setup behavior, recovery commands, tool-path overrides, and the 64tass trust boundary.

64tass is intentionally not downloaded or executed by setup. After downloading/building and extracting a `64tass.exe` you trust, add it later with:

```powershell
.\setup-windows.cmd -TassPath "C:\Tools\64tass\64tass.exe"
```

A containing directory is also accepted. Setup validates the expected filename, file existence, and a recognizable Windows PE signature without running the executable. It also computes SHA-256. If the executable hash is `46920377fde73464068556b1a60f6e3794707966f31d45936741e618f78384b5`, setup reports a **KNOWN HASH MATCH** against the 64tass 1.60.3243 Windows executable reference recorded during v0.5.1 release preparation. The corresponding manually downloaded ZIP was recorded as SHA-256 `04bf54b7e975c13485f991a59a54e3cb909f9c439aab8288c4927951bdcce781`. A hash match means identical bytes to that recorded reference; it does not independently prove safety, publisher identity, or runtime correctness. Setup then shows the proposed `[windows]` configuration diff and asks before writing/merging:

```ini
[windows]
tass = C:\Tools\64tass\64tass.exe
```

Existing unrelated INI sections and keys are preserved.

If setup installed or updated a tool through WinGet, close the current terminal and open a new PowerShell/Command Prompt before testing commands; PATH and WinGet command aliases may not appear in a shell that was already open.

## Quitting part-way through setup

Selecting `Q` / `QUIT` no longer silently discards the setup state. The helper prints a summary of what it has discovered or changed so far, including existing/installed package actions, selected paths, and any pending `[windows]` `tass`/`vice` values. If valid tool paths are pending, you can save those configuration changes before quitting or discard them.

This is **not** a rollback mechanism: a Python/Git/VICE install, upgrade, or reinstall already performed by WinGet remains installed even if you choose to quit and discard the INI changes.

### 64tass path/search options

For `E` / `ENTER` and directly pasted 64tass paths, setup first resolves the executable, performs the non-executing path/name/PE-header validation, computes SHA-256, and shows whether it matches the recorded 1.60.3243 reference. Only then does setup ask `Y` / `YES`, `N` / `NO`, or `Q` / `QUIT`. `F` / `FIND` and `D` / `DRIVE` already confirm through their numbered candidate selection, while an explicit `-TassPath` command-line override remains authoritative.

When `[windows] tass` already points to a valid `64tass.exe` and existing configuration is being kept, setup gives 64tass its own `K` / `KEEP`, `C` / `CHANGE`, `Q` / `QUIT` prompt. `CHANGE` opens the normal E/F/D selector. If the replacement flow is skipped without selecting another executable, the previous valid 64tass path remains configured.

At the 64tass prompt, `E` / `ENTER` accepts either the full `64tass.exe` path or the directory that directly contains it. `F` / `FIND` searches common local locations. `D` / `DRIVE` asks for a drive letter and scans only that explicitly selected drive. At the drive-letter prompt, any drive letter is treated literally (for example `C`, `D:`, or `E:\`); a blank Enter is the only way to return to the 64tass menu before scanning. Once the scan has actually started, `Q` or `Esc` stops the scan. Any structurally valid candidates already found are immediately shown for selection; if none were found, setup returns directly to the 64tass menu. Filesystem reparse points and inaccessible directories are skipped, and nonexistent/invalid drives are rejected. You can also paste a path directly at the menu.

You may skip 64tass and configure it later with either form:

```powershell
.\setup-windows.cmd -TassPath "C:\Tools\64tass\64tass.exe"
.\setup-windows.cmd -TassPath "C:\Tools\64tass"
```

For a clean cancellation with the session summary and save/discard prompt, use `Q` / `QUIT`. Ctrl+C is handled by the surrounding shell and may terminate the batch wrapper before setup can offer its normal quit flow.

### Partial configuration after an error

If setup encounters a fatal error after discovering valid VICE and/or 64tass paths, it attempts to show the same session summary used by `Q` / `QUIT` and asks whether those valid pending paths should be saved to `config\c643d.ini`. Software already installed or updated by WinGet is not rolled back. Saving valid partial configuration does not change the failed run's exit status: setup still returns exit code 1.
