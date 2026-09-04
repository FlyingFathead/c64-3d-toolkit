<#
 c64-3d-toolkit Windows installer / configuration assistant
 Installer revision: r24 (2026-09-02)
 Target toolkit release: v0.6.2

 Security model:
 - Python, Git, VICE and optional Blender are checked against exact package IDs in Microsoft's
   WinGet `winget` source before any new WinGet install is attempted.
 - Existing WinGet packages are kept by default; the user may explicitly request
   an upgrade or same-version force-reinstall/repair attempt through WinGet.
 - If WinGet package-status lookup fails, setup treats the status as UNKNOWN and
   does not assume the component is absent or install a duplicate solely on that basis.
 - 64tass is NEVER downloaded or installed automatically by this script.
 - No MSYS2, pacman, Scoop, Chocolatey or other third-party package manager is
   installed or invoked automatically.
 - No proactive Internet connectivity probes are made. Network access occurs
   only if WinGet actually needs to install Python, Git, VICE or user-approved Blender.
 - User-supplied/configured .exe paths are validated without execution: the expected
   filename must exist and the file must have a recognizable Windows PE executable header. This
   does not prove publisher identity, authenticity or runtime correctness.
 - VICE and 64tass are not executed during setup.
 - c643d.py doctor/build is not executed during setup.
 - Existing config/c643d.ini content is preserved; only confirmed `tass` and
   `vice` values in [windows] are merged/updated.
#>

[CmdletBinding()]
param(
    [Alias('h')][switch]$Help,
    [string]$VicePath,
    [string]$TassPath,
    [switch]$FindTass
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$InstallerRevision = 'r24'
$TargetRelease = '0.6.2'
$ToolkitRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$ConfigDir = Join-Path $ToolkitRoot 'config'
$ConfigPath = Join-Path $ConfigDir 'c643d.ini'

# Keep package IDs, executable names, official locations and other external
# trust/dependency metadata together so release review and future updates have
# one obvious place to inspect.
$KnownLocations = @{
    WinGet = @{
        Download = 'https://aka.ms/getwinget'
    }
    Python = @{
        WingetId = 'Python.Python.3.13'
        Download = 'https://www.python.org/downloads/windows/'
    }
    Git = @{
        WingetId = 'Git.Git'
        Download = 'https://git-scm.com/download/win'
    }
    Blender = @{
        WingetId = 'BlenderFoundation.Blender'
        Download = 'https://www.blender.org/download/'
        ExeName = 'blender.exe'
    }
    VICE = @{
        PreferredWingetId = 'VICE-Team.VICE.GTK3'
        WingetIds = @(
            'VICE-Team.VICE.GTK3',
            'VICE-Team.VICE.SDL2'
        )
        Download = 'https://vice-emu.sourceforge.io/'
        ExeName = 'x64sc.exe'
    }
    Tass = @{
        Project = 'https://sourceforge.net/projects/tass64/'
        Binaries = 'https://sourceforge.net/projects/tass64/files/binaries/'
        Source = 'https://sourceforge.net/projects/tass64/files/source/'
        Manual = 'https://tass64.sourceforge.net/'
        KnownVersion = '1.60.3243'
        ExeName = '64tass.exe'
        # Reference hashes recorded during v0.5.1 preparation from the manually
        # downloaded 64tass 1.60.3243 SourceForge Windows package. A hash match
        # identifies identical bytes; it is not a general safety guarantee.
        KnownExeSha256 = '46920377fde73464068556b1a60f6e3794707966f31d45936741e618f78384b5'
        KnownZipSha256 = '04bf54b7e975c13485f991a59a54e3cb909f9c439aab8288c4927951bdcce781'
    }
}

function Write-Section([string]$Name) {
    Write-Host ''
    Write-Host "== $Name =="
}

function Write-FallbackHeader([string]$Label) {
    Write-Host ''
    Write-Host "--- Manual fallback: $Label ---" -ForegroundColor Yellow
}

function Refresh-ProcessPath {
    $machine = [Environment]::GetEnvironmentVariable('Path', 'Machine')
    $user = [Environment]::GetEnvironmentVariable('Path', 'User')
    $parts = @($machine, $user) | Where-Object { $_ }
    $env:Path = $parts -join ';'
}

function Strip-PathQuotes([string]$Value) {
    if ($null -eq $Value) { return $null }
    $v = [Environment]::ExpandEnvironmentVariables($Value.Trim())
    if ($v.Length -ge 2) {
        if (($v.StartsWith('"') -and $v.EndsWith('"')) -or
            ($v.StartsWith("'") -and $v.EndsWith("'"))) {
            $v = $v.Substring(1, $v.Length - 2).Trim()
        }
    }
    return $v
}

function Find-Executable {
    param(
        [Parameter(Mandatory=$true)][string[]]$Names,
        [string[]]$ExtraPaths = @()
    )

    foreach ($path in $ExtraPaths) {
        if (-not $path) { continue }
        $resolved = Resolve-ExecutableInput -InputPath $path -ExpectedNames $Names
        if ($resolved) { return $resolved }
    }

    foreach ($name in $Names) {
        $cmd = Get-Command $name -CommandType Application -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($cmd) { return $cmd.Source }
    }

    return $null
}

function Test-WindowsExecutableHeader {
    param([Parameter(Mandatory=$true)][string]$Path)

    try {
        $stream = [System.IO.File]::Open(
            $Path,
            [System.IO.FileMode]::Open,
            [System.IO.FileAccess]::Read,
            [System.IO.FileShare]::ReadWrite
        )
        try {
            if ($stream.Length -lt 64) { return $false }

            if (($stream.ReadByte() -ne 0x4D) -or ($stream.ReadByte() -ne 0x5A)) {
                return $false
            }

            # DOS header e_lfanew at offset 0x3c points at the PE signature.
            [void]$stream.Seek(0x3C, [System.IO.SeekOrigin]::Begin)
            $offsetBytes = New-Object byte[] 4
            if ($stream.Read($offsetBytes, 0, 4) -ne 4) { return $false }
            $peOffset = [BitConverter]::ToInt32($offsetBytes, 0)
            if (($peOffset -lt 64) -or (($peOffset + 4) -gt $stream.Length)) { return $false }

            [void]$stream.Seek($peOffset, [System.IO.SeekOrigin]::Begin)
            $p0 = $stream.ReadByte()
            $p1 = $stream.ReadByte()
            $p2 = $stream.ReadByte()
            $p3 = $stream.ReadByte()
            return (($p0 -eq 0x50) -and ($p1 -eq 0x45) -and ($p2 -eq 0x00) -and ($p3 -eq 0x00))
        }
        finally {
            $stream.Dispose()
        }
    }
    catch {
        return $false
    }
}

function Test-ExecutableCandidate {
    param(
        [Parameter(Mandatory=$true)][string]$Path,
        [Parameter(Mandatory=$true)][string[]]$ExpectedNames
    )

    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        return $false
    }

    $leaf = [System.IO.Path]::GetFileName($Path)
    $expected = $false
    foreach ($name in $ExpectedNames) {
        if ($leaf -ieq $name) {
            $expected = $true
            break
        }
    }
    if (-not $expected) {
        return $false
    }

    if ([System.IO.Path]::GetExtension($leaf) -ieq '.exe') {
        return (Test-WindowsExecutableHeader -Path $Path)
    }

    return $true
}

function Resolve-ExecutableInput {
    param(
        [string]$InputPath,
        [Parameter(Mandatory=$true)][string[]]$ExpectedNames,
        [string[]]$DirectoryRelatives = @()
    )

    $value = Strip-PathQuotes $InputPath
    if (-not $value) { return $null }

    # Allow a command name such as `64tass.exe` or `x64sc.exe` when it is in PATH.
    if (($value -notmatch '[\\/]') -and ($value -notmatch '^[A-Za-z]:')) {
        $cmd = Get-Command $value -CommandType Application -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($cmd -and (Test-ExecutableCandidate -Path $cmd.Source -ExpectedNames $ExpectedNames)) {
            return $cmd.Source
        }
    }

    if (Test-Path -LiteralPath $value -PathType Leaf) {
        $resolvedLeaf = (Resolve-Path -LiteralPath $value).Path
        if (Test-ExecutableCandidate -Path $resolvedLeaf -ExpectedNames $ExpectedNames) {
            return $resolvedLeaf
        }
        return $null
    }

    if (Test-Path -LiteralPath $value -PathType Container) {
        $relatives = New-Object System.Collections.Generic.List[string]
        foreach ($name in $ExpectedNames) { [void]$relatives.Add($name) }
        foreach ($rel in $DirectoryRelatives) { [void]$relatives.Add($rel) }

        foreach ($relative in $relatives) {
            $candidate = Join-Path $value $relative
            if (Test-Path -LiteralPath $candidate -PathType Leaf) {
                $resolvedCandidate = (Resolve-Path -LiteralPath $candidate).Path
                if (Test-ExecutableCandidate -Path $resolvedCandidate -ExpectedNames $ExpectedNames) {
                    return $resolvedCandidate
                }
            }
        }
    }

    return $null
}

function Find-WinGet {
    return Find-Executable -Names @('winget.exe')
}

function Get-WindowsConfigState {
    $state = [PSCustomObject]@{
        SectionFound = $false
        tass = $null
        vice = $null
    }

    if (-not (Test-Path -LiteralPath $ConfigPath -PathType Leaf)) {
        return $state
    }

    $inWindows = $false
    foreach ($line in Get-Content -LiteralPath $ConfigPath) {
        if ($line -match '^\s*\[([^]]+)\]\s*$') {
            $inWindows = ($Matches[1] -ieq 'windows')
            if ($inWindows) { $state.SectionFound = $true }
            continue
        }
        if (-not $inWindows) { continue }
        if ($line -match '^\s*(tass|vice)\s*=\s*(.*?)\s*$') {
            $key = $Matches[1].ToLowerInvariant()
            $value = $Matches[2]
            if ($value -and ($value -notmatch '^\s*[#;]')) {
                if ($key -eq 'tass') { $state.tass = Strip-PathQuotes $value } else { $state.vice = Strip-PathQuotes $value }
            }
        }
    }

    return $state
}

function Get-ConfiguredExecutableStatus {
    param(
        [string]$ConfiguredPath,
        [Parameter(Mandatory=$true)][string[]]$ExpectedNames,
        [string[]]$DirectoryRelatives = @()
    )

    if (-not $ConfiguredPath) {
        return [PSCustomObject]@{ Present = $false; Valid = $false; Path = $null }
    }

    $resolved = Resolve-ExecutableInput -InputPath $ConfiguredPath -ExpectedNames $ExpectedNames -DirectoryRelatives $DirectoryRelatives
    return [PSCustomObject]@{
        Present = $true
        Valid = [bool]$resolved
        Path = $resolved
    }
}

function Request-ExistingWindowsConfigMode {
    param(
        [Parameter(Mandatory=$true)]$ConfigState,
        [Parameter(Mandatory=$true)]$ViceStatus,
        [Parameter(Mandatory=$true)]$TassStatus
    )

    Write-Host ''
    Write-Host 'Existing [windows] configuration found:' -ForegroundColor Cyan
    if ($ConfigState.vice) {
        $status = if ($ViceStatus.Valid) { 'VALID' } else { 'NOT FOUND' }
        Write-Host "  vice = $($ConfigState.vice) [$status]"
    }
    else {
        Write-Host '  vice = <not set>'
    }
    if ($ConfigState.tass) {
        $status = if ($TassStatus.Valid) { 'VALID' } else { 'NOT FOUND' }
        Write-Host "  tass = $($ConfigState.tass) [$status]"
    }
    else {
        Write-Host '  tass = <not set>'
    }

    while ($true) {
        Write-Host ''
        Write-Host 'How should setup handle the existing Windows configuration?'
        Write-Host '  K / KEEP   = keep valid existing paths; only repair/fill missing or invalid entries'
        Write-Host '  M / MODIFY = allow setup to search/select replacement paths'
        Write-Host '  Q / QUIT   = show the session summary, then quit'
        $answer = Read-Host 'Choice [K]'
        if ($null -eq $answer) { $answer = '' }
        $answer = $answer.Trim()

        if (($answer -eq '') -or ($answer -ieq 'k') -or ($answer -ieq 'keep')) { return 'Keep' }
        if (($answer -ieq 'm') -or ($answer -ieq 'modify') -or ($answer -ieq 'change')) { return 'Modify' }
        if (($answer -ieq 'q') -or ($answer -ieq 'quit') -or ($answer -ieq 'cancel') -or ($answer -ieq 'exit')) { return 'Quit' }
        Write-Host 'Please enter K, M or Q.' -ForegroundColor Yellow
    }
}

function Get-ProposedWindowsConfigChanges {
    param(
        [Parameter(Mandatory=$true)]$ConfigState,
        [string]$ViceExe,
        [string]$TassExe
    )

    # Plain arrays avoid a Windows PowerShell 5.1 generic-list return edge case.
    $changes = @()
    foreach ($item in @(
        @{ Key = 'tass'; NewValue = $TassExe },
        @{ Key = 'vice'; NewValue = $ViceExe }
    )) {
        if (-not $item.NewValue) { continue }
        $oldValue = if ($item.Key -eq 'tass') { $ConfigState.tass } else { $ConfigState.vice }
        if ($oldValue -ne $item.NewValue) {
            $changes += [PSCustomObject]@{
                Key = $item.Key
                OldValue = $oldValue
                NewValue = $item.NewValue
            }
        }
    }
    return $changes
}

function Confirm-WindowsConfigChanges {
    param([Parameter(Mandatory=$true)][object[]]$Changes)

    if ($Changes.Count -eq 0) { return 'NoChanges' }

    Write-Host ''
    Write-Host 'Proposed changes to config\c643d.ini [windows]:' -ForegroundColor Cyan
    foreach ($change in $Changes) {
        $old = if ($change.OldValue) { $change.OldValue } else { '<not set>' }
        Write-Host "  $($change.Key):"
        Write-Host "    current: $old"
        Write-Host "    new:     $($change.NewValue)"
    }

    while ($true) {
        Write-Host ''
        Write-Host 'Apply these [windows] configuration changes?'
        Write-Host '  Y / YES = write the changes'
        Write-Host '  N / NO  = leave c643d.ini unchanged'
        Write-Host '  Q / QUIT = show the session summary, then quit'
        $answer = Read-Host 'Choice [Y]'
        if ($null -eq $answer) { $answer = '' }
        $answer = $answer.Trim()

        if (($answer -eq '') -or ($answer -ieq 'y') -or ($answer -ieq 'yes')) { return 'Apply' }
        if (($answer -ieq 'n') -or ($answer -ieq 'no')) { return 'Leave' }
        if (($answer -ieq 'q') -or ($answer -ieq 'quit') -or ($answer -ieq 'cancel') -or ($answer -ieq 'exit')) { return 'Quit' }
        Write-Host 'Please enter Y, N or Q.' -ForegroundColor Yellow
    }
}

function Write-SetupSessionSummary {
    param(
        [string]$PythonExe,
        [string]$GitExe,
        [string]$ViceExe,
        [string]$TassExe,
        [string]$PythonAction = 'not processed',
        [string]$GitAction = 'not processed',
        [string]$ViceAction = 'not processed',
        [string]$TassAction = 'not processed',
        [Parameter(Mandatory=$true)]$OriginalConfig
    )

    Write-Section 'Setup changes so far'

    Write-Host 'Python 3'
    Write-Host "  Action: $PythonAction"
    if ($PythonExe) { Write-Host "  Path:   $PythonExe" } else { Write-Host '  Path:   <not selected/found>' }

    Write-Host ''
    Write-Host 'Git'
    Write-Host "  Action: $GitAction"
    if ($GitExe) { Write-Host "  Path:   $GitExe" } else { Write-Host '  Path:   <not selected/found>' }

    Write-Host ''
    Write-Host 'Blender (optional, highly recommended)'
    Write-Host "  Action: $blenderAction"
    if ($blender) { Write-Host "  Path:   $blender" } else { Write-Host '  Path:   <not installed/found>' }

    Write-Host ''
    Write-Host 'VICE'
    Write-Host "  Action: $ViceAction"
    if ($ViceExe) { Write-Host "  Path:   $ViceExe" } else { Write-Host '  Path:   <not selected/found>' }

    Write-Host ''
    Write-Host '64tass'
    Write-Host "  Action: $TassAction"
    if ($TassExe) { Write-Host "  Path:   $TassExe" } else { Write-Host '  Path:   <not selected/found>' }

    Write-Host ''
    Write-Host 'Configuration file'
    Write-Host "  Path: $ConfigPath"
    if (Test-Path -LiteralPath $ConfigPath -PathType Leaf) {
        Write-Host '  Current state: exists'
    }
    else {
        Write-Host '  Current state: not created'
    }

    # Pending means not yet reflected in the actual INI at the moment the
    # summary is printed. This keeps success/error summaries truthful even if
    # configuration has already been written earlier in the run.
    $currentConfig = Get-WindowsConfigState
    $pending = @(Get-ProposedWindowsConfigChanges -ConfigState $currentConfig -ViceExe $ViceExe -TassExe $TassExe)
    if ($pending.Count -gt 0) {
        Write-Host ''
        Write-Host 'Pending valid [windows] configuration discovered during this run:' -ForegroundColor Cyan
        foreach ($change in $pending) {
            $old = if ($change.OldValue) { $change.OldValue } else { '<not set>' }
            Write-Host "  $($change.Key):"
            Write-Host "    current: $old"
            Write-Host "    new:     $($change.NewValue)"
        }
    }
    else {
        Write-Host '  Pending changes: none'
    }

    return $pending
}

function Invoke-QuitWithSummary {
    param(
        [string]$PythonExe,
        [string]$GitExe,
        [string]$ViceExe,
        [string]$TassExe,
        [string]$PythonAction,
        [string]$GitAction,
        [string]$ViceAction,
        [string]$TassAction,
        [Parameter(Mandatory=$true)]$OriginalConfig
    )

    $pending = @(Write-SetupSessionSummary `
        -PythonExe $PythonExe -GitExe $GitExe -ViceExe $ViceExe -TassExe $TassExe `
        -PythonAction $PythonAction -GitAction $GitAction -ViceAction $ViceAction -TassAction $TassAction `
        -OriginalConfig $OriginalConfig)

    Write-Host ''
    Write-Host 'NOTE: software already installed/upgraded/reinstalled by WinGet will NOT be undone by leaving setup.' -ForegroundColor Yellow
    Write-Host 'The choice below controls only whether valid discovered VICE/64tass paths are written to config\c643d.ini.'

    if ($pending.Count -gt 0) {
        while ($true) {
            Write-Host ''
            Write-Host 'Save the valid configuration discovered so far before leaving setup?'
            Write-Host '  Y / SAVE    = write the pending [windows] tass/vice paths'
            Write-Host '  N / DISCARD = leave c643d.ini unchanged'
            $answer = Read-Host 'Choice [N]'
            if ($null -eq $answer) { $answer = '' }
            $answer = $answer.Trim()

            if (($answer -ieq 'y') -or ($answer -ieq 'yes') -or ($answer -ieq 'save')) {
                [void](Update-WindowsConfig -ViceExe $ViceExe -TassExe $TassExe)
                Write-Host 'Valid discovered configuration was saved before leaving setup.'
                return
            }
            if (($answer -eq '') -or ($answer -ieq 'n') -or ($answer -ieq 'no') -or ($answer -ieq 'discard')) {
                Write-Host 'Configuration was not changed.' -ForegroundColor Yellow
                return
            }
            Write-Host 'Please enter Y/SAVE or N/DISCARD.' -ForegroundColor Yellow
        }
    }

    Write-Host 'There are no pending valid tool-path changes to save.'
}

function Write-SetupHelpHint {
    Write-Host 'Setup help:'
    Write-Host '  .\setup-windows.cmd -Help'
}

function Show-InstallerHelp {
    Write-Host 'c64-3d-toolkit Windows setup help'
    Write-Host "target release: v$TargetRelease"
    Write-Host "installer revision: $InstallerRevision"
    Write-Host ''
    Write-Host 'Usage:'
    Write-Host '  .\setup-windows.cmd'
    Write-Host '  .\setup-windows.cmd -Help'
    Write-Host '  .\setup-windows.cmd -VicePath "C:\path\to\VICE\bin\x64sc.exe"'
    Write-Host '  .\setup-windows.cmd -TassPath "C:\path\to\64tass.exe"'
    Write-Host '  .\setup-windows.cmd -TassPath "C:\path\to\64tass-directory"'
    Write-Host '  .\setup-windows.cmd -FindTass'
    Write-Host ''
    Write-Host 'What setup manages:'
    Write-Host '  - Python 3, Git and VICE: exact WinGet package detection plus install/upgrade/reinstall support.'
    Write-Host '  - Blender: optional but highly recommended; if absent, setup asks before installing BlenderFoundation.Blender.'
    Write-Host '  - 64tass: manual acquisition only; setup never downloads or executes it.'
    Write-Host '    64tass is REQUIRED to assemble generated data into a runnable .prg; only --no-assemble works without it.'
    Write-Host '    Existing valid 64tass config gets its own K/KEEP, C/CHANGE or Q/QUIT prompt.'
    Write-Host '    E/ENTER accepts either 64tass.exe itself or the directory containing it.'
    Write-Host '    Manual/direct paths are validated and hashed first, then require Y/YES confirmation before use.'
    Write-Host '    F/FIND or -FindTass searches common local locations only.'
    Write-Host '    D/DRIVE scans one chosen drive. At the drive prompt, any drive letter is valid; blank Enter returns.'
    Write-Host '    Once a drive scan has started, Q or Esc stops it; any results found so far are shown for selection.'
    Write-Host '  - config\c643d.ini: only confirmed tass/vice values in [windows] are merged.'
    Write-Host '  - Q/QUIT prints a session summary; pending valid tass/vice paths can be saved or discarded before exit.'
    Write-Host '  - Fatal setup errors also attempt the same summary + save/discard prompt before returning exit code 1.'
    Write-Host ''
    Write-Host 'Adding 64tass later:'
    Write-Host '  1. Download/build and extract a 64tass.exe that you have chosen to trust.'
    Write-Host "     Official Windows binaries: $($KnownLocations.Tass.Binaries)"
    Write-Host '  2. Rerun setup with the executable OR its containing directory:'
    Write-Host '       .\setup-windows.cmd -TassPath "C:\Tools\64tass\64tass.exe"'
    Write-Host '       .\setup-windows.cmd -TassPath "C:\Tools\64tass"'
    Write-Host '     or simply run .\setup-windows.cmd and use E/ENTER at the 64tass prompt.'
    Write-Host '  3. Setup checks that the expected 64tass.exe exists and has a recognizable Windows PE header.'
    Write-Host '     It does NOT execute the file and cannot prove its publisher/authenticity or runtime behavior.'
    Write-Host '     Setup also computes SHA-256. A KNOWN HASH MATCH identifies byte-for-byte equality with the'
    Write-Host "     64tass $($KnownLocations.Tass.KnownVersion) Windows executable reference recorded during v0.5.1 preparation."
    Write-Host '  4. Setup shows the proposed config change and asks before writing it. The resulting entry is:'
    Write-Host '       [windows]'
    Write-Host '       tass = C:\Tools\64tass\64tass.exe'
    Write-Host ''
    Write-Host 'VICE can be added/repaired later the same way with -VicePath.'
    Write-Host ''
    Write-Host 'Clean cancellation:'
    Write-Host '  Use Q / QUIT if you want the setup session summary and save/discard prompt.'
    Write-Host '  Ctrl+C is handled by the surrounding shell and may terminate the batch wrapper immediately.'
    Write-Host ''
    Write-Host 'Optional manual toolkit validation after configuration (executes the toolchain):'
    Write-Host '  py -3 .\c643d.py doctor'
}

function Show-WinGetFallback {
    Write-FallbackHeader 'WinGet / App Installer'
    Write-Host 'WinGet is provided by Microsoft App Installer on current Windows 11 systems.'
    Write-Host 'Official Microsoft installer/update route:'
    Write-Host "  $($KnownLocations.WinGet.Download)"
    Write-Host 'After installing/updating App Installer, open a new PowerShell window and rerun:'
    Write-Host '  .\setup-windows.cmd'
    Write-SetupHelpHint
}

function Show-WinGetOperationFallback {
    param(
        [Parameter(Mandatory=$true)][string]$Component,
        [Parameter(Mandatory=$true)][string]$Operation,
        [Parameter(Mandatory=$true)][string]$PackageId
    )

    Write-FallbackHeader "$Component / WinGet"
    Write-Host "WinGet could not complete the requested $Operation for:"
    Write-Host "  $PackageId"
    Write-Host 'This can mean the WinGet source is unavailable/blocked, the package ID is unavailable,'
    Write-Host 'or the vendor installer itself failed. Setup will not silently switch package sources.'
    Write-Host 'Check the WinGet output above and your firewall/proxy/VPN policy before retrying.'
    Write-SetupHelpHint
}

function Get-WinGetPackageState {
    param(
        [Parameter(Mandatory=$true)][string]$Id
    )

    $state = [PSCustomObject]@{
        Id = $Id
        Status = 'Unknown'
        Installed = $false
        InstalledVersion = $null
        AvailableVersion = $null
        QueryExitCode = $null
        QueryOutput = $null
    }

    $winget = Find-WinGet
    if (-not $winget) {
        return $state
    }

    $lines = @(& $winget list --exact --id $Id --source winget --accept-source-agreements 2>&1)
    $exitCode = $LASTEXITCODE
    $output = ($lines | ForEach-Object { "$_" }) -join [Environment]::NewLine
    $state.QueryExitCode = $exitCode
    $state.QueryOutput = $output

    if ($output -match '(?i)No installed package found matching input criteria') {
        $state.Status = 'NotInstalled'
        return $state
    }

    foreach ($line in $lines) {
        $text = "$line"

        # Strip common ANSI terminal sequences before parsing the WinGet table.
        $clean = [Regex]::Replace($text, "$([char]27)\[[0-9;?]*[ -/]*[@-~]", '')

        $idIndex = $clean.IndexOf($Id, [System.StringComparison]::OrdinalIgnoreCase)
        if ($idIndex -lt 0) {
            continue
        }

        $afterId = $clean.Substring($idIndex + $Id.Length).Trim()
        if (-not $afterId) {
            continue
        }

        $tokens = @($afterId -split '\s+' | Where-Object { $_ })
        if ($tokens.Count -lt 1) {
            continue
        }

        # The exact-ID row begins with the installed version after the package ID.
        # Depending on terminal width/WinGet version, the Available and Source
        # columns may be omitted. Do not require the trailing `winget` token.
        if ($tokens[0] -match '^\d[0-9A-Za-z._+-]*$') {
            $state.Status = 'Installed'
            $state.Installed = $true
            $state.InstalledVersion = $tokens[0]
            if (($tokens.Count -ge 2) -and ($tokens[1] -match '^\d[0-9A-Za-z._+-]*$')) {
                $state.AvailableVersion = $tokens[1]
            }
            return $state
        }
    }

    if (($exitCode -eq 0) -and ($output -match [Regex]::Escape($Id))) {
        # Exact package appears to be registered, but the human-readable table
        # format was not recognized. Never downgrade this to "missing".
        $state.Status = 'Installed'
        $state.Installed = $true
        return $state
    }

    return $state
}

function Write-WinGetPackageState {
    param(
        [Parameter(Mandatory=$true)][string]$Label,
        [Parameter(Mandatory=$true)]$State
    )

    if ($State.Status -eq 'Installed') {
        $version = if ($State.InstalledVersion) { $State.InstalledVersion } else { '<version not parsed>' }
        Write-Host "WinGet package: $($State.Id) [INSTALLED $version]"
        if ($State.AvailableVersion) {
            Write-Host "WinGet reports an available version: $($State.AvailableVersion)"
        }
        return
    }

    if ($State.Status -eq 'NotInstalled') {
        Write-Host "WinGet package: $($State.Id) [not installed]"
        return
    }

    Write-Host "WinGet package: $($State.Id) [STATUS UNKNOWN]" -ForegroundColor Yellow
    Write-Host 'WinGet package-state lookup could not be completed. Setup will not infer that the package is missing.'
}

function Request-WinGetInstalledAction {
    param(
        [Parameter(Mandatory=$true)][string]$Label,
        [Parameter(Mandatory=$true)]$State
    )

    while ($true) {
        Write-Host ''
        Write-Host "$Label is registered as an installed WinGet package:"
        Write-Host "  $($State.Id)"
        if ($State.InstalledVersion) {
            Write-Host "  installed: $($State.InstalledVersion)"
        }
        if ($State.AvailableVersion) {
            Write-Host "  available: $($State.AvailableVersion)"
        }
        Write-Host ''
        Write-Host 'What should setup do?'
        Write-Host '  K / KEEP      = leave the installed package alone (default)'
        Write-Host '  U / UPGRADE   = ask WinGet to upgrade this exact package if an upgrade is available'
        if ($State.InstalledVersion) {
            Write-Host '  R / REINSTALL = force-reinstall the same installed version through this exact package ID'
        }
        else {
            Write-Host '  R / REINSTALL = force-reinstall via this exact package ID (version could not be parsed)'
        }
        Write-Host '  Q / QUIT      = show the session summary, then quit'
        $answer = Read-Host 'Choice [K]'
        if ($null -eq $answer) { $answer = '' }
        $answer = $answer.Trim()

        if (($answer -eq '') -or ($answer -ieq 'k') -or ($answer -ieq 'keep')) { return 'Keep' }
        if (($answer -ieq 'u') -or ($answer -ieq 'upgrade') -or ($answer -ieq 'update')) { return 'Upgrade' }
        if (($answer -ieq 'r') -or ($answer -ieq 'reinstall') -or ($answer -ieq 'repair')) { return 'Reinstall' }
        if (($answer -ieq 'q') -or ($answer -ieq 'quit') -or ($answer -ieq 'cancel') -or ($answer -ieq 'exit')) { return 'Quit' }

        Write-Host 'Please enter K, U, R or Q.' -ForegroundColor Yellow
    }
}

function Invoke-WinGetPackageOperation {
    param(
        [Parameter(Mandatory=$true)][ValidateSet('Install','Upgrade','Reinstall')][string]$Operation,
        [Parameter(Mandatory=$true)][string]$Id,
        [Parameter(Mandatory=$true)][string]$Label,
        [string]$Version
    )

    $winget = Find-WinGet
    if (-not $winget) {
        Show-WinGetFallback
        throw "WinGet is required for the requested $Label operation."
    }

    switch ($Operation) {
        'Install' {
            Write-Host "Installing $Label ($Id) with WinGet..."
            & $winget install --exact --id $Id --source winget --accept-package-agreements --accept-source-agreements
        }
        'Upgrade' {
            Write-Host "Checking/upgrading $Label ($Id) with WinGet..."
            & $winget upgrade --exact --id $Id --source winget --accept-package-agreements --accept-source-agreements
        }
        'Reinstall' {
            if ($Version) {
                Write-Host "Force-reinstalling $Label ($Id), version $Version, with WinGet..."
                & $winget install --exact --id $Id --version $Version --source winget --accept-package-agreements --accept-source-agreements --force
            }
            else {
                Write-Host "Force-reinstalling $Label ($Id) with WinGet; installed version was not parsed..."
                & $winget install --exact --id $Id --source winget --accept-package-agreements --accept-source-agreements --force
            }
        }
    }

    $exitCode = $LASTEXITCODE
    if ($exitCode -ne 0) {
        Show-WinGetOperationFallback -Component $Label -Operation $Operation.ToLowerInvariant() -PackageId $Id
        throw "WinGet $Operation failed for $Label (exit code $exitCode)."
    }

    Refresh-ProcessPath
}

function Invoke-WinGetInstalledMaintenance {
    param(
        [Parameter(Mandatory=$true)][string]$Label,
        [Parameter(Mandatory=$true)]$State
    )

    $action = Request-WinGetInstalledAction -Label $Label -State $State
    if ($action -eq 'Quit') {
        return 'Quit'
    }
    if ($action -eq 'Keep') {
        return 'Keep'
    }

    try {
        if ($action -eq 'Reinstall') {
            Invoke-WinGetPackageOperation -Operation Reinstall -Id $State.Id -Label $Label -Version $State.InstalledVersion
        }
        else {
            Invoke-WinGetPackageOperation -Operation Upgrade -Id $State.Id -Label $Label
        }
        return $action
    }
    catch {
        Write-Host "$Label WinGet $action failed: $($_.Exception.Message)" -ForegroundColor Yellow
        Write-Host 'The existing installation/configuration will be preserved where possible.'
        return 'Failed'
    }
}

function Install-WinGetPackage {
    param(
        [Parameter(Mandatory=$true)][string]$Id,
        [Parameter(Mandatory=$true)][string]$Label
    )

    Invoke-WinGetPackageOperation -Operation Install -Id $Id -Label $Label
}

function Show-PythonFallback {
    Write-FallbackHeader 'Python 3'
    Write-Host 'Official Python for Windows:'
    Write-Host "  $($KnownLocations.Python.Download)"
    Write-Host 'Install Python 3, then rerun:'
    Write-Host '  .\setup-windows.cmd'
    Write-SetupHelpHint
}

function Show-GitFallback {
    Write-FallbackHeader 'Git'
    Write-Host 'Official Git for Windows:'
    Write-Host "  $($KnownLocations.Git.Download)"
    Write-Host 'Install Git, then rerun:'
    Write-Host '  .\setup-windows.cmd'
    Write-SetupHelpHint
}

function Show-BlenderFallback {
    Write-FallbackHeader 'Blender (optional, highly recommended)'
    Write-Host 'Blender is required only for animated .blend scene builds; classic OBJ/SVG/procedural builds still work without it.'
    Write-Host 'Official Blender download:'
    Write-Host "  $($KnownLocations.Blender.Download)"
    Write-Host 'Preferred Windows install command:'
    Write-Host "  winget install --exact --id $($KnownLocations.Blender.WingetId) --source winget"
}

function Request-BlenderInstall {
    while ($true) {
        Write-Host ''
        Write-Host 'Blender was not found. Installing it is HIGHLY RECOMMENDED for the authored 3-D scene/camera pipeline.' -ForegroundColor Cyan
        Write-Host 'Blender remains optional for the existing OBJ, SVG and procedural workflows.'
        Write-Host 'Install Blender now through the exact WinGet package BlenderFoundation.Blender?'
        Write-Host '  Y / YES = install Blender (default)'
        Write-Host '  N / NO  = skip Blender and continue setup'
        $answer = Read-Host 'Choice [Y]'
        if ($null -eq $answer) { $answer = '' }
        $answer = $answer.Trim()
        if (($answer -eq '') -or ($answer -ieq 'y') -or ($answer -ieq 'yes')) { return $true }
        if (($answer -ieq 'n') -or ($answer -ieq 'no') -or ($answer -ieq 'skip')) { return $false }
        Write-Host 'Please enter Y or N.' -ForegroundColor Yellow
    }
}

function Show-ViceFallback {
    Write-FallbackHeader 'VICE'
    Write-Host 'Official VICE project/downloads:'
    Write-Host "  $($KnownLocations.VICE.Download)"
    Write-Host 'If you already have VICE installed or extracted, enter its x64sc.exe path below.'
    Write-Host 'You may enter either the full x64sc.exe path or the VICE directory.'
    Write-Host 'Command-line override for later runs:'
    Write-Host '  .\setup-windows.cmd -VicePath "C:\path\to\VICE\bin\x64sc.exe"'
    Write-SetupHelpHint
}

function Show-64tassFallback {
    Write-FallbackHeader '64tass'
    Write-Host '64tass was not found. This installer deliberately does NOT download or install it automatically.' -ForegroundColor Yellow
    Write-Host '64tass is REQUIRED to assemble a runnable .prg. You may skip it temporarily, but normal builds cannot finish until it is configured.' -ForegroundColor Yellow
    Write-Host 'Only table/source generation with --no-assemble can run without 64tass.'
    Write-Host ''
    Write-Host 'Easiest Windows option:'
    Write-Host '  1. Download the current Windows binary yourself from:'
    Write-Host "     $($KnownLocations.Tass.Binaries)"
    Write-Host '  2. Extract it somewhere you control.'
    Write-Host '  3. Use E/ENTER to enter the .exe or its directory, F/FIND for common locations,'
    Write-Host '     or D/DRIVE to choose one whole drive. Blank returns before scanning; Q/Esc cancels once scanning.'
    Write-Host '     You can also skip it now and add it later:'
    Write-Host '       .\setup-windows.cmd -TassPath "C:\Tools\64tass\64tass.exe"'
    Write-Host '       .\setup-windows.cmd -TassPath "C:\Tools\64tass"'
    Write-Host ''
    Write-Host 'Official upstream locations:'
    Write-Host "  Project:          $($KnownLocations.Tass.Project)"
    Write-Host "  Windows binaries: $($KnownLocations.Tass.Binaries)"
    Write-Host "  Source archives:  $($KnownLocations.Tass.Source)"
    Write-Host "  Manual/homepage:  $($KnownLocations.Tass.Manual)"
    Write-Host ''
    Write-Host "Current upstream release recorded for v0.5.1 preparation: $($KnownLocations.Tass.KnownVersion)"
    Write-Host 'The project has a documented history of antivirus false positives on MinGW-built Windows binaries.'
    Write-Host 'Review/verify any prebuilt executable according to your own security policy before running it.'
    Write-Host ''
    Write-Host 'Setup validation is deliberately non-executing:'
    Write-Host '  - expected filename must be 64tass.exe'
    Write-Host '  - the file must exist and have a recognizable Windows PE executable header'
    Write-Host '  - SHA-256 is computed; a known hash match identifies identical bytes to the recorded reference'
    Write-Host '  - a hash match does NOT by itself prove publisher identity/safety or runtime correctness'
    Write-Host ''
    Write-Host 'Manual alternatives:'
    Write-Host '  - Build 64tass yourself from the official source archive.'
    Write-Host '  - If you intentionally use MSYS2, its official 64tass package is another manual route.'
    Write-Host '    This installer will NOT install MSYS2 or invoke pacman.'
    Write-Host ''
    Write-Host 'When a valid path is selected, setup shows the proposed [windows] tass change and asks before writing config\c643d.ini.'
    Write-SetupHelpHint
}

function Get-Sha256String {
    param([Parameter(Mandatory=$true)][string]$Path)
    try {
        return (Get-FileHash -LiteralPath $Path -Algorithm SHA256 -ErrorAction Stop).Hash.ToLowerInvariant()
    }
    catch {
        return $null
    }
}

function Get-64tassHashInfo {
    param([Parameter(Mandatory=$true)][string]$Path)

    $hash = Get-Sha256String -Path $Path
    $known = $false
    if ($hash -and ($hash -ieq $KnownLocations.Tass.KnownExeSha256)) {
        $known = $true
    }

    return [PSCustomObject]@{
        Path = $Path
        Sha256 = $hash
        KnownMatch = $known
    }
}

function Write-64tassHashInfo {
    param([Parameter(Mandatory=$true)][string]$Path)

    $info = Get-64tassHashInfo -Path $Path
    Write-Host '64tass SHA-256:'
    if ($info.Sha256) {
        Write-Host "  $($info.Sha256)"
    }
    else {
        Write-Host '  <could not calculate>' -ForegroundColor Yellow
        return
    }

    if ($info.KnownMatch) {
        Write-Host "KNOWN HASH MATCH: byte-for-byte match with the 64tass $($KnownLocations.Tass.KnownVersion)"
        Write-Host 'Windows executable reference recorded from the manually obtained SourceForge package during v0.5.1 preparation.'
        Write-Host 'This hash match identifies identical bytes; it is not a general safety/authenticity guarantee.'
    }
    else {
        Write-Host 'UNKNOWN HASH: the file does not match the single 64tass Windows executable reference known to this installer.' -ForegroundColor Yellow
        Write-Host 'That does not mean the file is malicious; it may be another release or a locally built executable.'
    }
}

function Find-64tassCandidatesInRoots {
    param(
        [Parameter(Mandatory=$true)][string[]]$Roots,
        [Parameter(Mandatory=$true)][string]$SearchDescription,
        [switch]$Force
    )

    Write-Host ''
    Write-Host $SearchDescription

    $seenRoots = @{}
    $seenFiles = @{}
    $results = @()

    foreach ($root in $Roots) {
        if (-not $root) { continue }
        $expandedRoot = [Environment]::ExpandEnvironmentVariables($root)
        $rootKey = $expandedRoot.ToLowerInvariant()
        if ($seenRoots.ContainsKey($rootKey)) { continue }
        $seenRoots[$rootKey] = $true

        if (-not (Test-Path -LiteralPath $expandedRoot -PathType Container)) {
            continue
        }

        Write-Host "  searching: $expandedRoot"

        if ($Force) {
            $files = @(Get-ChildItem -LiteralPath $expandedRoot -Filter $KnownLocations.Tass.ExeName -File -Recurse -Force -ErrorAction SilentlyContinue)
        }
        else {
            $files = @(Get-ChildItem -LiteralPath $expandedRoot -Filter $KnownLocations.Tass.ExeName -File -Recurse -ErrorAction SilentlyContinue)
        }

        foreach ($file in $files) {
            $resolved = $file.FullName
            $key = $resolved.ToLowerInvariant()
            if ($seenFiles.ContainsKey($key)) { continue }
            $seenFiles[$key] = $true

            if (-not (Test-ExecutableCandidate -Path $resolved -ExpectedNames @($KnownLocations.Tass.ExeName))) {
                continue
            }

            $results += (Get-64tassHashInfo -Path $resolved)
        }
    }

    return $results
}

function Find-64tassCandidates {
    $programFilesX86 = [Environment]::GetEnvironmentVariable('ProgramFiles(x86)')
    $roots = @(
        $ToolkitRoot,
        (Join-Path $env:USERPROFILE 'Downloads'),
        (Join-Path $env:USERPROFILE 'Desktop'),
        (Join-Path $env:LOCALAPPDATA 'Programs'),
        'C:\Tools',
        $env:ProgramFiles,
        $programFilesX86
    )

    return @(Find-64tassCandidatesInRoots `
        -Roots $roots `
        -SearchDescription 'Searching common local locations for 64tass.exe (no whole-drive scan)...')
}

function Select-64tassFromCandidateList {
    param(
        [AllowNull()]
        [AllowEmptyCollection()]
        [object[]]$Candidates = @(),
        [Parameter(Mandatory=$true)][string]$NoResultsMessage
    )

    $Candidates = @($Candidates)
    if ($Candidates.Count -eq 0) {
        Write-Host $NoResultsMessage -ForegroundColor Yellow
        return $null
    }

    Write-Host ''
    Write-Host "Found $($Candidates.Count) candidate(s):"
    for ($i = 0; $i -lt $Candidates.Count; $i++) {
        $candidate = $Candidates[$i]
        Write-Host "  [$($i + 1)] $($candidate.Path)"
        if ($candidate.Sha256) {
            Write-Host "      SHA-256: $($candidate.Sha256)"
        }
        if ($candidate.KnownMatch) {
            Write-Host "      KNOWN HASH MATCH: 64tass $($KnownLocations.Tass.KnownVersion) reference" -ForegroundColor Cyan
        }
        else {
            Write-Host '      hash: unknown to this installer' -ForegroundColor Yellow
        }
    }

    while ($true) {
        Write-Host ''
        Write-Host 'Select a candidate number, or R / RETURN to go back.'
        $answer = Read-Host 'Choice'
        if ($null -eq $answer) { $answer = '' }
        $answer = $answer.Trim()

        if (($answer -eq '') -or ($answer -ieq 'r') -or ($answer -ieq 'return')) {
            return $null
        }

        $number = 0
        if ([int]::TryParse($answer, [ref]$number)) {
            if (($number -ge 1) -and ($number -le $Candidates.Count)) {
                return $Candidates[$number - 1].Path
            }
        }

        Write-Host 'Please enter one of the displayed numbers, or R to return.' -ForegroundColor Yellow
    }
}

function Select-64tassCandidate {
    $candidates = @(Find-64tassCandidates)
    return (Select-64tassFromCandidateList `
        -Candidates $candidates `
        -NoResultsMessage 'No structurally valid 64tass.exe was found in the common search locations.')
}

function Resolve-64tassUserPath {
    param([Parameter(Mandatory=$true)][string]$InputPath)

    $value = Strip-PathQuotes $InputPath
    if (-not $value) {
        return $null
    }

    # Allow the bare command name if it is already resolvable from PATH.
    if (($value -notmatch '[\\/]') -and ($value -notmatch '^[A-Za-z]:')) {
        $cmd = Get-Command $value -CommandType Application -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($cmd) {
            if (([System.IO.Path]::GetFileName($cmd.Source) -ine $KnownLocations.Tass.ExeName)) {
                Write-Host "WRONG EXECUTABLE NAME: $($cmd.Source)" -ForegroundColor Yellow
                Write-Host "Expected: $($KnownLocations.Tass.ExeName)"
                return $null
            }
            if (-not (Test-WindowsExecutableHeader -Path $cmd.Source)) {
                Write-Host "EXECUTABLE HEADER NOT RECOGNIZED: $($cmd.Source)" -ForegroundColor Yellow
                return $null
            }
            return $cmd.Source
        }
    }

    if (Test-Path -LiteralPath $value -PathType Leaf) {
        $resolvedLeaf = (Resolve-Path -LiteralPath $value).Path
        $leaf = [System.IO.Path]::GetFileName($resolvedLeaf)

        if ($leaf -ine $KnownLocations.Tass.ExeName) {
            Write-Host "WRONG EXECUTABLE NAME: $resolvedLeaf" -ForegroundColor Yellow
            Write-Host "Expected: $($KnownLocations.Tass.ExeName)"
            return $null
        }

        if (-not (Test-WindowsExecutableHeader -Path $resolvedLeaf)) {
            Write-Host "EXECUTABLE HEADER NOT RECOGNIZED: $resolvedLeaf" -ForegroundColor Yellow
            Write-Host 'The file exists but does not have the Windows PE structure expected by setup.'
            return $null
        }

        return $resolvedLeaf
    }

    if (Test-Path -LiteralPath $value -PathType Container) {
        $resolvedDir = (Resolve-Path -LiteralPath $value).Path
        Write-Host "Directory found: $resolvedDir"
        $candidate = Join-Path $resolvedDir $KnownLocations.Tass.ExeName

        if (-not (Test-Path -LiteralPath $candidate -PathType Leaf)) {
            Write-Host "64tass.exe NOT FOUND IN DIRECTORY:" -ForegroundColor Yellow
            Write-Host "  $resolvedDir"
            Write-Host 'Returning to 64tass selection.'
            return $null
        }

        $resolvedCandidate = (Resolve-Path -LiteralPath $candidate).Path
        if (-not (Test-WindowsExecutableHeader -Path $resolvedCandidate)) {
            Write-Host "EXECUTABLE HEADER NOT RECOGNIZED: $resolvedCandidate" -ForegroundColor Yellow
            Write-Host 'Returning to 64tass selection.'
            return $null
        }

        return $resolvedCandidate
    }

    Write-Host "PATH NOT FOUND:" -ForegroundColor Yellow
    Write-Host "  $value"
    Write-Host 'Returning to 64tass selection.'
    return $null
}

function Request-64tassManualPath {
    Write-Host ''
    Write-Host 'Enter either:'
    Write-Host '  - the full path to 64tass.exe'
    Write-Host '  - the directory that directly contains 64tass.exe'
    Write-Host 'Setup will validate/hash the resolved executable and ask before using it.'
    Write-Host ''
    Write-Host 'You can also add/change it later with:'
    Write-Host '  .\setup-windows.cmd -TassPath "C:\path\to\64tass.exe"'
    Write-Host '  .\setup-windows.cmd -TassPath "C:\path\to\64tass-directory"'
    $answer = Read-Host 'Path (blank = return)'
    if ($null -eq $answer) { $answer = '' }
    $trimmed = $answer.Trim()

    if ($trimmed -eq '') {
        return $null
    }

    $resolved = Resolve-64tassUserPath -InputPath $trimmed
    if ($resolved) {
        Write-Host "Found 64tass.exe: $resolved"
        Write-Host '64tass.exe passed non-executing path/name/PE-header validation; it was NOT executed.'
        return $resolved
    }

    return $null
}

function Request-64tassManualCandidateConfirmation {
    param(
        [Parameter(Mandatory=$true)][string]$Path
    )

    Write-Host ''
    Write-Host 'Manual 64tass candidate validated:'
    Write-Host "  $Path"
    Write-64tassHashInfo -Path $Path
    Write-Host '64tass was NOT executed by this setup script.'

    while ($true) {
        Write-Host ''
        Write-Host 'Use this 64tass executable?'
        Write-Host '  Y / YES  = use this path (default)'
        Write-Host '  N / NO   = return to 64tass selection'
        Write-Host '  Q / QUIT = show the session summary, then quit'
        $answer = Read-Host 'Choice [Y]'
        if ($null -eq $answer) { $answer = '' }
        $answer = $answer.Trim()

        if (($answer -eq '') -or ($answer -ieq 'y') -or ($answer -ieq 'yes')) {
            return 'Use'
        }

        if (($answer -ieq 'n') -or ($answer -ieq 'no') -or ($answer -ieq 'return') -or ($answer -ieq 'back')) {
            return 'Return'
        }

        if (($answer -ieq 'q') -or ($answer -ieq 'quit') -or ($answer -ieq 'cancel') -or ($answer -ieq 'exit')) {
            return 'Quit'
        }

        Write-Host 'Please enter Y, N or Q.' -ForegroundColor Yellow
    }
}

function Resolve-RequestedDriveRoot {
    param([Parameter(Mandatory=$true)][string]$InputDrive)

    $value = Strip-PathQuotes $InputDrive
    if (-not $value) { return $null }

    if ($value -notmatch '^([A-Za-z])(?::(?:\\)?)?$') {
        Write-Host 'INVALID DRIVE. Enter a single drive letter such as C, D, D: or D:\.' -ForegroundColor Yellow
        return $null
    }

    $letter = $Matches[1].ToUpperInvariant()
    $root = ('{0}:\' -f $letter)

    if (-not (Test-Path -LiteralPath $root -PathType Container)) {
        Write-Host "DRIVE NOT FOUND: $root" -ForegroundColor Yellow
        return $null
    }

    return $root
}

function Test-64tassDriveScanCancelRequested {
    try {
        while ([Console]::KeyAvailable) {
            $key = [Console]::ReadKey($true)
            if (($key.Key -eq [ConsoleKey]::Q) -or ($key.Key -eq [ConsoleKey]::Escape)) {
                return $true
            }
        }
    }
    catch {
        # KeyAvailable can fail when input is redirected or there is no normal
        # interactive console. In that case the scan continues normally.
        return $false
    }

    return $false
}

function Find-64tassCandidatesOnDrive {
    param(
        [Parameter(Mandatory=$true)][string]$Root
    )

    $stack = New-Object System.Collections.Stack
    $stack.Push($Root)

    $seenDirectories = @{}
    $seenFiles = @{}
    $results = @()
    $directoriesScanned = 0

    Write-Host ''
    Write-Host "Scanning entire drive $Root for 64tass.exe..."
    Write-Host 'Press Q or Esc at any time to stop this scan; results found so far will still be shown.'
    Write-Host 'Protected/inaccessible directories and filesystem reparse points are skipped.'
    Write-Host 'No discovered executable is run.'

    while ($stack.Count -gt 0) {
        if (Test-64tassDriveScanCancelRequested) {
            Write-Progress -Activity "Scanning $Root for 64tass.exe" -Completed
            Write-Host ''
            Write-Host "Drive scan cancelled by user after $directoriesScanned director$(if ($directoriesScanned -eq 1) { 'y' } else { 'ies' })." -ForegroundColor Yellow
            Write-Host 'No files were changed or executed by the scan.'
            if ($results.Count -gt 0) {
                Write-Host "Preserving $($results.Count) candidate(s) found before cancellation."
            }
            else {
                Write-Host 'No candidates were found before cancellation.'
                Write-Host 'Returning to 64tass selection.'
            }
            return [PSCustomObject]@{
                Cancelled = $true
                Candidates = @($results)
                DirectoriesScanned = $directoriesScanned
            }
        }

        $directory = [string]$stack.Pop()
        if (-not $directory) {
            continue
        }

        $directoryKey = $directory.TrimEnd('\').ToLowerInvariant()
        if ($seenDirectories.ContainsKey($directoryKey)) {
            continue
        }
        $seenDirectories[$directoryKey] = $true
        $directoriesScanned++

        if (($directoriesScanned -eq 1) -or (($directoriesScanned % 100) -eq 0)) {
            Write-Progress `
                -Activity "Scanning $Root for 64tass.exe" `
                -Status "Directories scanned: $directoriesScanned; candidates: $($results.Count). Press Q or Esc to cancel."
        }

        # Because the target filename is known, check the exact path in each
        # directory rather than enumerating every file on the drive.
        $candidatePath = Join-Path $directory $KnownLocations.Tass.ExeName
        if (Test-Path -LiteralPath $candidatePath -PathType Leaf -ErrorAction SilentlyContinue) {
            try {
                $resolved = (Resolve-Path -LiteralPath $candidatePath -ErrorAction Stop).Path
                $fileKey = $resolved.ToLowerInvariant()

                if (-not $seenFiles.ContainsKey($fileKey)) {
                    $seenFiles[$fileKey] = $true
                    if (Test-ExecutableCandidate -Path $resolved -ExpectedNames @($KnownLocations.Tass.ExeName)) {
                        $results += (Get-64tassHashInfo -Path $resolved)
                    }
                }
            }
            catch {
                # Ignore a candidate that disappears or becomes inaccessible
                # between the existence check and validation.
            }
        }

        if (Test-64tassDriveScanCancelRequested) {
            Write-Progress -Activity "Scanning $Root for 64tass.exe" -Completed
            Write-Host ''
            Write-Host "Drive scan cancelled by user after $directoriesScanned director$(if ($directoriesScanned -eq 1) { 'y' } else { 'ies' })." -ForegroundColor Yellow
            Write-Host 'No files were changed or executed by the scan.'
            if ($results.Count -gt 0) {
                Write-Host "Preserving $($results.Count) candidate(s) found before cancellation."
            }
            else {
                Write-Host 'No candidates were found before cancellation.'
                Write-Host 'Returning to 64tass selection.'
            }
            return [PSCustomObject]@{
                Cancelled = $true
                Candidates = @($results)
                DirectoriesScanned = $directoriesScanned
            }
        }

        # Enumerate only immediate child directories so cancellation can be
        # checked between directories instead of blocking on one whole-drive
        # Get-ChildItem -Recurse operation.
        $children = @(
            Get-ChildItem `
                -LiteralPath $directory `
                -Directory `
                -Force `
                -ErrorAction SilentlyContinue
        )

        foreach ($child in $children) {
            if (Test-64tassDriveScanCancelRequested) {
                Write-Progress -Activity "Scanning $Root for 64tass.exe" -Completed
                Write-Host ''
                Write-Host "Drive scan cancelled by user after $directoriesScanned director$(if ($directoriesScanned -eq 1) { 'y' } else { 'ies' })." -ForegroundColor Yellow
                Write-Host 'No files were changed or executed by the scan.'
                if ($results.Count -gt 0) {
                    Write-Host "Preserving $($results.Count) candidate(s) found before cancellation."
                }
                else {
                    Write-Host 'No candidates were found before cancellation.'
                    Write-Host 'Returning to 64tass selection.'
                }
                return [PSCustomObject]@{
                    Cancelled = $true
                    Candidates = @($results)
                    DirectoriesScanned = $directoriesScanned
                }
            }

            # Do not traverse junctions/symlinks/reparse points. Besides being
            # unnecessary for a local executable search, they can create loops
            # or unexpectedly cross filesystem boundaries.
            if (($child.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0) {
                continue
            }

            $stack.Push($child.FullName)
        }
    }

    Write-Progress -Activity "Scanning $Root for 64tass.exe" -Completed
    Write-Host ''
    Write-Host "Drive scan completed: $directoriesScanned director$(if ($directoriesScanned -eq 1) { 'y' } else { 'ies' }) scanned; $($results.Count) structurally valid candidate(s) found."

    return [PSCustomObject]@{
        Cancelled = $false
        Candidates = @($results)
        DirectoriesScanned = $directoriesScanned
    }
}

function Request-64tassDriveSearch {
    Write-Host ''
    Write-Host 'Whole-drive scan'
    Write-Host '  This walks one drive directory-by-directory and may take a while.'
    Write-Host '  Press Q or Esc during the scan to stop it; any results found so far will still be shown.'
    Write-Host '  Protected/inaccessible directories and filesystem reparse points are skipped.'
    Write-Host '  No files found by the scan are executed.'
    Write-Host ''
    Write-Host 'At the drive-letter prompt, every drive letter is treated literally (including Q: or R:).'
    Write-Host 'Press Enter on a blank line to return to the 64tass menu.'
    Write-Host 'For a clean exit from SETUP with summary/save options, return to the 64tass menu first and use Q there.'
    Write-Host ''
    $driveInput = Read-Host 'Drive letter to scan (for example C, D: or E:\)'
    if ($null -eq $driveInput) { $driveInput = '' }
    if ($driveInput.Trim() -eq '') {
        Write-Host 'Returning to 64tass selection.'
        return $null
    }

    $root = Resolve-RequestedDriveRoot -InputDrive $driveInput
    if (-not $root) {
        Write-Host 'Returning to 64tass selection.'
        return $null
    }

    $scan = Find-64tassCandidatesOnDrive -Root $root
    $candidates = @($scan.Candidates)

    if ($scan.Cancelled -and ($candidates.Count -eq 0)) {
        return $null
    }

    if ($scan.Cancelled -and ($candidates.Count -gt 0)) {
        Write-Host ''
        if ($candidates.Count -eq 1) {
            Write-Host 'Search was cancelled, but 1 candidate was found before cancellation.' -ForegroundColor Cyan
        }
        else {
            Write-Host "Search was cancelled, but $($candidates.Count) candidates were found before cancellation." -ForegroundColor Cyan
        }
        Write-Host 'Showing the results found so far. Select one, or return without changing the current 64tass path.'
    }

    return (Select-64tassFromCandidateList `
        -Candidates $candidates `
        -NoResultsMessage "No structurally valid 64tass.exe was found on drive $root.")
}

function Request-Existing64tassAction {
    param(
        [Parameter(Mandatory=$true)][string]$Path
    )

    Write-Host ''
    Write-Host 'Existing valid 64tass configuration:'
    Write-Host "  $Path"

    while ($true) {
        Write-Host ''
        Write-Host 'What should setup do?'
        Write-Host '  K / KEEP   = keep this 64tass path (default)'
        Write-Host '  C / CHANGE = choose/search for a different 64tass executable or directory'
        Write-Host '  Q / QUIT   = show the session summary, then quit'
        $answer = Read-Host 'Choice [K]'
        if ($null -eq $answer) { $answer = '' }
        $answer = $answer.Trim()

        if (($answer -eq '') -or ($answer -ieq 'k') -or ($answer -ieq 'keep')) {
            return 'Keep'
        }
        if (($answer -ieq 'c') -or ($answer -ieq 'change') -or ($answer -ieq 'modify')) {
            return 'Change'
        }
        if (($answer -ieq 'q') -or ($answer -ieq 'quit') -or ($answer -ieq 'cancel') -or ($answer -ieq 'exit')) {
            return 'Quit'
        }

        Write-Host 'Please enter K, C or Q.' -ForegroundColor Yellow
    }
}

function Request-64tassPath {
    while ($true) {
        Write-Host ''
        Write-Host '64tass selection:'
        Write-Host '  E / ENTER  = enter a 64tass.exe path or the directory containing it'
        Write-Host '  F / FIND   = search common local locations for 64tass.exe'
        Write-Host '  D / DRIVE  = scan one drive (blank returns; Q/Esc stops scan and shows results found so far)'
        Write-Host '  S / SKIP   = skip this component for now'
        Write-Host '  Q / QUIT / CANCEL = show the session summary, then quit'
        Write-Host '  <path>     = you may also paste a path directly here'
        Write-Host ''
        Write-Host 'You can skip it now and add/change it later with:'
        Write-Host '  .\setup-windows.cmd -TassPath "C:\path\to\64tass.exe"'
        Write-Host '  .\setup-windows.cmd -TassPath "C:\path\to\64tass-directory"'
        Write-Host 'Use Q / QUIT rather than Ctrl+C if you want the session summary and save/discard prompt.'

        $answer = Read-Host 'Choice or path'
        if ($null -eq $answer) { $answer = '' }
        $trimmed = $answer.Trim()

        if (($trimmed -eq '') -or ($trimmed -ieq 's') -or ($trimmed -ieq 'skip')) {
            return [PSCustomObject]@{ Action = 'Skip'; Path = $null; Source = 'Skip' }
        }

        if (($trimmed -ieq 'q') -or ($trimmed -ieq 'quit') -or ($trimmed -ieq 'cancel') -or ($trimmed -ieq 'exit')) {
            return [PSCustomObject]@{ Action = 'Quit'; Path = $null; Source = 'Quit' }
        }

        if (($trimmed -ieq 'e') -or ($trimmed -ieq 'enter')) {
            $manual = Request-64tassManualPath
            if ($manual) {
                $decision = Request-64tassManualCandidateConfirmation -Path $manual
                if ($decision -eq 'Use') {
                    return [PSCustomObject]@{ Action = 'Use'; Path = $manual; Source = 'Manual' }
                }
                if ($decision -eq 'Quit') {
                    return [PSCustomObject]@{ Action = 'Quit'; Path = $null; Source = 'Quit' }
                }
            }
            continue
        }

        if (($trimmed -ieq 'f') -or ($trimmed -ieq 'find') -or ($trimmed -ieq 'search')) {
            $found = Select-64tassCandidate
            if ($found) {
                return [PSCustomObject]@{ Action = 'Use'; Path = $found; Source = 'Find' }
            }
            continue
        }

        if (($trimmed -ieq 'd') -or ($trimmed -ieq 'drive')) {
            $found = Request-64tassDriveSearch
            if ($found) {
                return [PSCustomObject]@{ Action = 'Use'; Path = $found; Source = 'Drive' }
            }
            continue
        }

        $resolved = Resolve-64tassUserPath -InputPath $trimmed
        if ($resolved) {
            Write-Host "Found 64tass.exe: $resolved"
            Write-Host '64tass.exe passed non-executing path/name/PE-header validation; it was NOT executed.'
            $decision = Request-64tassManualCandidateConfirmation -Path $resolved
            if ($decision -eq 'Use') {
                return [PSCustomObject]@{ Action = 'Use'; Path = $resolved; Source = 'Manual' }
            }
            if ($decision -eq 'Quit') {
                return [PSCustomObject]@{ Action = 'Quit'; Path = $null; Source = 'Quit' }
            }
            continue
        }

        Write-SetupHelpHint
    }
}

function Request-ExecutablePath {
    param(
        [Parameter(Mandatory=$true)][string]$Label,
        [Parameter(Mandatory=$true)][string[]]$ExpectedNames,
        [string[]]$DirectoryRelatives = @()
    )

    while ($true) {
        Write-Host ''
        Write-Host "Enter the path for $Label."
        Write-Host '  You may enter the executable itself or its containing/install directory.'
        Write-Host '  S / SKIP   = skip this component for now'
        Write-Host '  Q / QUIT / CANCEL = show the session summary, then quit'
        $answer = Read-Host 'Path'

        if ($null -eq $answer) { $answer = '' }
        $trimmed = $answer.Trim()

        if (($trimmed -eq '') -or ($trimmed -ieq 's') -or ($trimmed -ieq 'skip')) {
            return [PSCustomObject]@{ Action = 'Skip'; Path = $null }
        }
        if (($trimmed -ieq 'q') -or ($trimmed -ieq 'quit') -or ($trimmed -ieq 'cancel') -or ($trimmed -ieq 'exit')) {
            return [PSCustomObject]@{ Action = 'Quit'; Path = $null }
        }

        $resolved = Resolve-ExecutableInput -InputPath $trimmed -ExpectedNames $ExpectedNames -DirectoryRelatives $DirectoryRelatives
        if ($resolved) {
            Write-Host "Found ${Label}: $resolved"
            Write-Host "$Label passed non-executing path/name/PE-header validation; it was NOT executed."
            return [PSCustomObject]@{ Action = 'Use'; Path = $resolved }
        }

        Write-Host ''
        Write-Host "Not found, wrong filename, or not a recognizable Windows PE executable: $trimmed" -ForegroundColor Yellow
        Write-Host "Expected: $($ExpectedNames -join ' or ')"
        Write-Host 'Please try again, or enter S to skip / Q to quit.'
        Write-SetupHelpHint
    }
}

function Find-Python {
    $candidates = @(
        (Join-Path $env:LOCALAPPDATA 'Programs\Python\Launcher\py.exe'),
        (Join-Path $env:LOCALAPPDATA 'Programs\Python\Python313\python.exe'),
        (Join-Path $env:LOCALAPPDATA 'Programs\Python\Python312\python.exe'),
        (Join-Path $env:LOCALAPPDATA 'Programs\Python\Python311\python.exe')
    )
    return Find-Executable -Names @('py.exe', 'python.exe', 'python3.exe') -ExtraPaths $candidates
}

function Find-Git {
    $candidates = @((Join-Path $env:ProgramFiles 'Git\cmd\git.exe'))
    if (${env:ProgramFiles(x86)}) {
        $candidates += (Join-Path ${env:ProgramFiles(x86)} 'Git\cmd\git.exe')
    }
    return Find-Executable -Names @('git.exe') -ExtraPaths $candidates
}

function Find-Blender {
    $found = Find-Executable -Names @($KnownLocations.Blender.ExeName, 'blender')
    if ($found) { return $found }

    $wingetPackageRoot = Join-Path $env:LOCALAPPDATA 'Microsoft\WinGet\Packages'
    if (Test-Path -LiteralPath $wingetPackageRoot -PathType Container) {
        $packageDirs = Get-ChildItem -LiteralPath $wingetPackageRoot -Directory -ErrorAction SilentlyContinue |
            Where-Object { $_.Name -like "$($KnownLocations.Blender.WingetId)*" }
        foreach ($packageDir in $packageDirs) {
            $candidate = Get-ChildItem -LiteralPath $packageDir.FullName -Filter $KnownLocations.Blender.ExeName -File -Recurse -ErrorAction SilentlyContinue |
                Select-Object -First 1
            if ($candidate -and (Test-WindowsExecutableHeader -Path $candidate.FullName)) {
                return $candidate.FullName
            }
        }
    }

    $roots = @(
        (Join-Path $env:ProgramFiles 'Blender Foundation'),
        (Join-Path $env:LOCALAPPDATA 'Programs')
    )
    if (${env:ProgramFiles(x86)}) {
        $roots += (Join-Path ${env:ProgramFiles(x86)} 'Blender Foundation')
    }
    $roots = @($roots | Where-Object { $_ -and (Test-Path -LiteralPath $_ -PathType Container) })
    foreach ($root in $roots) {
        $candidate = Get-ChildItem -LiteralPath $root -Filter $KnownLocations.Blender.ExeName -File -Recurse -ErrorAction SilentlyContinue |
            Sort-Object FullName -Descending |
            Select-Object -First 1
        if ($candidate -and (Test-WindowsExecutableHeader -Path $candidate.FullName)) {
            return $candidate.FullName
        }
    }
    return $null
}

function Find-Vice {
    param([string]$ConfiguredPath)

    $expected = @($KnownLocations.VICE.ExeName)
    $relatives = @('bin\x64sc.exe')

    if ($VicePath) {
        $resolved = Resolve-ExecutableInput -InputPath $VicePath -ExpectedNames $expected -DirectoryRelatives $relatives
        if ($resolved) { return $resolved }
        Write-Host "VICE override was not valid: $VicePath" -ForegroundColor Yellow
    }

    if ($ConfiguredPath) {
        $resolved = Resolve-ExecutableInput -InputPath $ConfiguredPath -ExpectedNames $expected -DirectoryRelatives $relatives
        if ($resolved) {
            Write-Host "Using VICE from existing config: $resolved"
            return $resolved
        }
        Write-Host "Configured VICE path is currently unavailable: $ConfiguredPath" -ForegroundColor Yellow
    }

    $found = Find-Executable -Names @('x64sc.exe', 'x64sc')
    if ($found) { return $found }

    # VICE installed by WinGet may live under WinGet's managed package tree
    # rather than PATH or Program Files. Search only the two known VICE package
    # IDs; do not recurse across unrelated WinGet packages.
    $wingetPackageRoot = Join-Path $env:LOCALAPPDATA 'Microsoft\WinGet\Packages'
    if (Test-Path -LiteralPath $wingetPackageRoot -PathType Container) {
        foreach ($packageId in $KnownLocations.VICE.WingetIds) {
            $packageDirs = Get-ChildItem -LiteralPath $wingetPackageRoot -Directory -ErrorAction SilentlyContinue |
                Where-Object { $_.Name -like "$packageId*" }

            foreach ($packageDir in $packageDirs) {
                $candidate = Get-ChildItem -LiteralPath $packageDir.FullName -Filter $KnownLocations.VICE.ExeName -File -Recurse -ErrorAction SilentlyContinue |
                    Select-Object -First 1
                if ($candidate) {
                    return $candidate.FullName
                }
            }
        }
    }

    $toolkitCandidates = @(
        (Join-Path $ToolkitRoot 'tools\VICE\bin\x64sc.exe'),
        (Join-Path $ToolkitRoot 'tools\VICE\x64sc.exe')
    )
    foreach ($candidate in $toolkitCandidates) {
        if (Test-Path -LiteralPath $candidate -PathType Leaf) {
            return (Resolve-Path -LiteralPath $candidate).Path
        }
    }

    $roots = @(
        $env:ProgramFiles,
        ${env:ProgramFiles(x86)},
        (Join-Path $env:LOCALAPPDATA 'Programs')
    ) | Where-Object { $_ -and (Test-Path -LiteralPath $_ -PathType Container) }

    foreach ($root in $roots) {
        $dirs = Get-ChildItem -LiteralPath $root -Directory -Filter 'VICE*' -ErrorAction SilentlyContinue
        foreach ($dir in $dirs) {
            foreach ($relative in @('bin\x64sc.exe', 'x64sc.exe')) {
                $candidate = Join-Path $dir.FullName $relative
                if (Test-Path -LiteralPath $candidate -PathType Leaf) {
                    return (Resolve-Path -LiteralPath $candidate).Path
                }
            }
        }
    }

    return $null
}

function Get-ViceWinGetStates {
    # Use a normal PowerShell array here. Windows PowerShell 5.1 can throw
    # "Argument types do not match" when a generic List[object] is returned
    # through an array subexpression.
    $states = @()
    foreach ($id in $KnownLocations.VICE.WingetIds) {
        $state = Get-WinGetPackageState -Id $id
        if ($null -ne $state) {
            $states += $state
        }
    }
    return $states
}

function Select-ViceWinGetState {
    param(
        [Parameter(Mandatory=$true)][object[]]$States,
        [string]$ViceExe
    )

    $installed = @($States | Where-Object { $_.Status -eq 'Installed' })
    if ($installed.Count -eq 0) { return $null }

    if ($ViceExe) {
        foreach ($state in $installed) {
            if ($ViceExe -like "*$($state.Id)*") {
                return $state
            }
        }
    }

    $preferred = $installed | Where-Object { $_.Id -eq $KnownLocations.VICE.PreferredWingetId } | Select-Object -First 1
    if ($preferred) { return $preferred }

    return ($installed | Select-Object -First 1)
}

function Find-64tass {
    param([string]$ConfiguredPath)

    $expected = @($KnownLocations.Tass.ExeName)

    if ($TassPath) {
        $resolved = Resolve-ExecutableInput -InputPath $TassPath -ExpectedNames $expected
        if ($resolved) { return $resolved }
        Write-Host "64tass -TassPath override was not usable: $TassPath" -ForegroundColor Yellow
        Write-Host 'The value may be either 64tass.exe itself or the directory that directly contains it.'
        Write-SetupHelpHint
    }

    if ($ConfiguredPath) {
        $resolved = Resolve-ExecutableInput -InputPath $ConfiguredPath -ExpectedNames $expected
        if ($resolved) {
            Write-Host "Using 64tass from existing config: $resolved"
            return $resolved
        }
        Write-Host "Configured 64tass path is currently unavailable: $ConfiguredPath" -ForegroundColor Yellow
    }

    $candidates = @(
        (Join-Path $ToolkitRoot 'tools\64tass\64tass.exe'),
        (Join-Path $ToolkitRoot 'tools\64tass.exe'),
        'C:\Tools\64tass\64tass.exe',
        (Join-Path $env:LOCALAPPDATA 'Programs\64tass\64tass.exe')
    )
    return Find-Executable -Names @('64tass.exe', '64tass') -ExtraPaths $candidates
}

function Update-WindowsConfig {
    param(
        [string]$ViceExe,
        [string]$TassExe
    )

    $updates = @{}
    if ($TassExe) { $updates['tass'] = $TassExe }
    if ($ViceExe) { $updates['vice'] = $ViceExe }

    if ($updates.Count -eq 0) {
        Write-Host 'No confirmed Windows tool paths to write; config was left unchanged.' -ForegroundColor Yellow
        return $false
    }

    if (-not (Test-Path -LiteralPath $ConfigDir -PathType Container)) {
        Write-Host "Creating config directory: $ConfigDir"
        New-Item -ItemType Directory -Force -Path $ConfigDir | Out-Null
    }

    $lines = @()
    if (Test-Path -LiteralPath $ConfigPath -PathType Leaf) {
        $lines = @(Get-Content -LiteralPath $ConfigPath)
    }

    $result = New-Object System.Collections.Generic.List[string]
    $inWindows = $false
    $foundWindows = $false
    $written = @{}

    function Add-MissingWindowsUpdates {
        param(
            [System.Collections.Generic.List[string]]$Target,
            [hashtable]$UpdateMap,
            [hashtable]$WrittenMap
        )
        foreach ($key in @('tass', 'vice')) {
            if ($UpdateMap.ContainsKey($key) -and -not $WrittenMap.ContainsKey($key)) {
                [void]$Target.Add("$key = $($UpdateMap[$key])")
                $WrittenMap[$key] = $true
            }
        }
    }

    foreach ($line in $lines) {
        if ($line -match '^\s*\[([^]]+)\]\s*$') {
            if ($inWindows) {
                Add-MissingWindowsUpdates -Target $result -UpdateMap $updates -WrittenMap $written
                $inWindows = $false
            }

            if ($Matches[1] -ieq 'windows') {
                $foundWindows = $true
                $inWindows = $true
            }

            [void]$result.Add($line)
            continue
        }

        if ($inWindows -and $line -match '^\s*(tass|vice)\s*=') {
            $key = $Matches[1].ToLowerInvariant()
            if ($updates.ContainsKey($key)) {
                if (-not $written.ContainsKey($key)) {
                    [void]$result.Add("$key = $($updates[$key])")
                    $written[$key] = $true
                }
                # Drop duplicate copies of a key we are actively updating.
                continue
            }
        }

        [void]$result.Add($line)
    }

    if ($inWindows) {
        Add-MissingWindowsUpdates -Target $result -UpdateMap $updates -WrittenMap $written
    }

    if (-not $foundWindows) {
        if ($result.Count -gt 0 -and $result[$result.Count - 1] -ne '') {
            [void]$result.Add('')
        }
        [void]$result.Add('[windows]')
        Add-MissingWindowsUpdates -Target $result -UpdateMap $updates -WrittenMap $written
    }

    $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
    $tempPath = Join-Path $ConfigDir ('.c643d.ini.setup-' + [Guid]::NewGuid().ToString('N') + '.tmp')
    try {
        [System.IO.File]::WriteAllLines($tempPath, [string[]]$result, $utf8NoBom)
        Move-Item -LiteralPath $tempPath -Destination $ConfigPath -Force
    }
    finally {
        if (Test-Path -LiteralPath $tempPath -PathType Leaf) {
            Remove-Item -LiteralPath $tempPath -Force -ErrorAction SilentlyContinue
        }
    }

    Write-Host "Updated Windows tool configuration: $ConfigPath"
    return $true
}

if ($Help) {
    Show-InstallerHelp
    exit 0
}

# Session state is initialized before the main try block so an error or explicit
# quit can still report exactly what setup discovered/changed up to that point.
$python = $null
$git = $null
$blender = $null
$vice = $null
$tass = $null
$pythonAction = 'not processed'
$gitAction = 'not processed'
$blenderAction = 'not processed'
$viceAction = 'not processed'
$tassAction = 'not processed'
$existingConfig = Get-WindowsConfigState
$configChanged = $false

try {
    Write-Host 'c64-3d-toolkit Windows setup'
    Write-Host "target release: v$TargetRelease"
    Write-Host "installer revision: $InstallerRevision"
    Write-Host "toolkit: $ToolkitRoot"

    Write-Section 'Local preflight'

    if (Test-Path -LiteralPath $ConfigDir -PathType Container) {
        Write-Host "Config directory: found ($ConfigDir)"
    }
    else {
        Write-Host "Config directory: not found ($ConfigDir) [will be created only when a confirmed path is written]"
    }

    if (Test-Path -LiteralPath $ConfigPath -PathType Leaf) {
        Write-Host "Config file: found ($ConfigPath)"
    }
    else {
        Write-Host "Config file: not found ($ConfigPath) [will be created when needed]"
    }

    $existingConfig = Get-WindowsConfigState
    if ($existingConfig.SectionFound) {
        Write-Host 'Config [windows] section: found'
    }
    else {
        Write-Host 'Config [windows] section: not found'
    }

    $viceConfigStatus = Get-ConfiguredExecutableStatus -ConfiguredPath $existingConfig.vice -ExpectedNames @($KnownLocations.VICE.ExeName) -DirectoryRelatives @('bin\x64sc.exe')
    $tassConfigStatus = Get-ConfiguredExecutableStatus -ConfiguredPath $existingConfig.tass -ExpectedNames @($KnownLocations.Tass.ExeName)

    $configMode = 'Keep'
    if ($existingConfig.SectionFound -and ($existingConfig.vice -or $existingConfig.tass)) {
        $configMode = Request-ExistingWindowsConfigMode -ConfigState $existingConfig -ViceStatus $viceConfigStatus -TassStatus $tassConfigStatus
        if ($configMode -eq 'Quit') {
            Invoke-QuitWithSummary -PythonExe $python -GitExe $git -ViceExe $vice -TassExe $tass `
                -PythonAction $pythonAction -GitAction $gitAction -ViceAction $viceAction -TassAction $tassAction `
                -OriginalConfig $existingConfig
            exit 3
        }
    }

    $winget = Find-WinGet
    if ($winget) {
        Write-Host "WinGet: found ($winget)"
    }
    else {
        Write-Host 'WinGet: NOT FOUND (automatic Python/Git/VICE and optional Blender installation unavailable)' -ForegroundColor Yellow
        Show-WinGetFallback
    }

    $curl = Join-Path $env:SystemRoot 'System32\curl.exe'
    if (Test-Path -LiteralPath $curl -PathType Leaf) {
        Write-Host "curl.exe: found ($curl) [informational; this installer does not use it]"
    }
    else {
        Write-Host 'curl.exe: not found [informational; not required by this installer]'
    }
    Write-Host 'Internet: not proactively probed. WinGet may contact only its configured `winget` source for exact package-state/install/upgrade/reinstall operations.'

    Write-Section 'Python 3'
    $python = Find-Python
    $pythonAction = if ($python) { 'existing executable found' } else { 'not found yet' }
    $pythonPkg = if ($winget) { Get-WinGetPackageState -Id $KnownLocations.Python.WingetId } else { $null }

    if ($pythonPkg) {
        Write-WinGetPackageState -Label 'Python 3.13' -State $pythonPkg
    }

    if ($pythonPkg -and ($pythonPkg.Status -eq 'Installed')) {
        $action = Invoke-WinGetInstalledMaintenance -Label 'Python 3.13' -State $pythonPkg
        if ($action -eq 'Quit') {
            Invoke-QuitWithSummary -PythonExe $python -GitExe $git -ViceExe $vice -TassExe $tass `
                -PythonAction $pythonAction -GitAction $gitAction -ViceAction $viceAction -TassAction $tassAction `
                -OriginalConfig $existingConfig
            exit 3
        }
        if ($action -eq 'Keep') { $pythonAction = 'existing WinGet package kept unchanged' }
        elseif ($action -eq 'Upgrade') { $pythonAction = 'WinGet upgrade completed/requested'; $python = Find-Python }
        elseif ($action -eq 'Reinstall') { $pythonAction = 'WinGet same-version reinstall completed/requested'; $python = Find-Python }
        elseif ($action -eq 'Failed') { $pythonAction = 'existing package preserved; requested WinGet maintenance failed' }
    }
    elseif (-not $python) {
        if ($pythonPkg -and ($pythonPkg.Status -eq 'Unknown')) {
            $pythonAction = 'not found; WinGet state unknown, automatic install skipped'
            Write-Host 'Python executable was not found, but WinGet package state is unknown; automatic install is skipped to avoid a duplicate.' -ForegroundColor Yellow
        }
        else {
            try {
                Install-WinGetPackage -Id $KnownLocations.Python.WingetId -Label 'Python 3.13'
                $pythonAction = 'installed through WinGet'
                $python = Find-Python
            }
            catch {
                $pythonAction = 'automatic WinGet install failed'
                Show-PythonFallback
                Write-Host "Python automatic installation failed: $($_.Exception.Message)" -ForegroundColor Yellow
            }
        }
    }

    if ($python) {
        Write-Host "Found Python 3: $python"
    }
    else {
        Show-PythonFallback
        Write-Host 'Python 3 is still missing. Setup will continue so tool paths can still be configured.' -ForegroundColor Yellow
    }

    Write-Section 'Git'
    $git = Find-Git
    $gitAction = if ($git) { 'existing executable found' } else { 'not found yet' }
    $gitPkg = if ($winget) { Get-WinGetPackageState -Id $KnownLocations.Git.WingetId } else { $null }

    if ($gitPkg) {
        Write-WinGetPackageState -Label 'Git' -State $gitPkg
    }

    if ($gitPkg -and ($gitPkg.Status -eq 'Installed')) {
        $action = Invoke-WinGetInstalledMaintenance -Label 'Git' -State $gitPkg
        if ($action -eq 'Quit') {
            Invoke-QuitWithSummary -PythonExe $python -GitExe $git -ViceExe $vice -TassExe $tass `
                -PythonAction $pythonAction -GitAction $gitAction -ViceAction $viceAction -TassAction $tassAction `
                -OriginalConfig $existingConfig
            exit 3
        }
        if ($action -eq 'Keep') { $gitAction = 'existing WinGet package kept unchanged' }
        elseif ($action -eq 'Upgrade') { $gitAction = 'WinGet upgrade completed/requested'; $git = Find-Git }
        elseif ($action -eq 'Reinstall') { $gitAction = 'WinGet same-version reinstall completed/requested'; $git = Find-Git }
        elseif ($action -eq 'Failed') { $gitAction = 'existing package preserved; requested WinGet maintenance failed' }
    }
    elseif (-not $git) {
        if ($gitPkg -and ($gitPkg.Status -eq 'Unknown')) {
            $gitAction = 'not found; WinGet state unknown, automatic install skipped'
            Write-Host 'Git executable was not found, but WinGet package state is unknown; automatic install is skipped to avoid a duplicate.' -ForegroundColor Yellow
        }
        else {
            try {
                Install-WinGetPackage -Id $KnownLocations.Git.WingetId -Label 'Git'
                $gitAction = 'installed through WinGet'
                $git = Find-Git
            }
            catch {
                $gitAction = 'automatic WinGet install failed'
                Show-GitFallback
                Write-Host "Git automatic installation failed: $($_.Exception.Message)" -ForegroundColor Yellow
            }
        }
    }

    if ($git) {
        Write-Host "Found Git: $git"
    }
    else {
        Show-GitFallback
        Write-Host 'Git is still missing. Setup will continue so tool paths can still be configured.' -ForegroundColor Yellow
    }

    Write-Section 'Blender (optional, highly recommended)'
    $blender = Find-Blender
    $blenderAction = if ($blender) { 'existing executable found; not executed by setup' } else { 'not found yet' }
    if ($blender) {
        Write-Host "Found Blender: $blender"
        Write-Host 'Blender was NOT executed by setup. The first --blend build performs the real headless bpy probe.'
    }
    else {
        $blenderPkg = if ($winget) { Get-WinGetPackageState -Id $KnownLocations.Blender.WingetId } else { $null }
        if ($blenderPkg) {
            Write-WinGetPackageState -Label 'Blender' -State $blenderPkg
        }
        if ($blenderPkg -and ($blenderPkg.Status -eq 'Installed')) {
            $blenderAction = 'WinGet package installed, but blender.exe was not discovered'
            Write-Host 'WinGet reports Blender installed, but blender.exe was not found in PATH or normal installation locations.' -ForegroundColor Yellow
            Write-Host 'Open a new terminal and rerun setup; an unusual install can later be selected with --blender PATH.'
        }
        elseif ($blenderPkg -and ($blenderPkg.Status -eq 'Unknown')) {
            $blenderAction = 'not found; WinGet state unknown, install not offered'
            Write-Host 'Blender was not found, but WinGet package state is UNKNOWN; setup will not risk a duplicate install.' -ForegroundColor Yellow
            Show-BlenderFallback
        }
        elseif (-not $winget) {
            $blenderAction = 'not found; WinGet unavailable'
            Show-BlenderFallback
        }
        elseif (Request-BlenderInstall) {
            try {
                Install-WinGetPackage -Id $KnownLocations.Blender.WingetId -Label 'Blender'
                $blenderAction = 'installed through WinGet'
                $blender = Find-Blender
                if ($blender) {
                    Write-Host "Blender selected: $blender"
                }
                else {
                    $blenderAction = 'installed through WinGet; executable discovery pending new shell'
                    Write-Host 'WinGet completed, but blender.exe is not visible to this process yet.' -ForegroundColor Yellow
                    Write-Host 'Open a new PowerShell/CMD window before using --blend.'
                }
            }
            catch {
                $blenderAction = 'user-approved WinGet install failed'
                Show-BlenderFallback
                Write-Host "Blender automatic installation failed: $($_.Exception.Message)" -ForegroundColor Yellow
            }
        }
        else {
            $blenderAction = 'user declined optional installation'
            Write-Host 'Blender skipped. Existing OBJ/SVG/procedural workflows remain available.' -ForegroundColor Yellow
        }
    }

    Write-Section 'VICE'
    $viceConfiguredCandidate = if ($configMode -eq 'Keep') { $existingConfig.vice } else { $null }
    $vice = Find-Vice -ConfiguredPath $viceConfiguredCandidate
    $viceAction = if ($vice) { 'existing executable found' } else { 'not found yet' }

    $vicePkgStates = @()
    if ($winget) {
        $vicePkgStates = @(Get-ViceWinGetStates)
        foreach ($state in $vicePkgStates) {
            Write-WinGetPackageState -Label 'VICE' -State $state
        }
    }

    $viceInstalledPkg = if ($vicePkgStates.Count -gt 0) {
        Select-ViceWinGetState -States $vicePkgStates -ViceExe $vice
    }
    else {
        $null
    }

    if ($viceInstalledPkg) {
        $installedViceStates = @($vicePkgStates | Where-Object { $_.Status -eq 'Installed' })
        if ($installedViceStates.Count -gt 1) {
            Write-Host "Multiple official VICE WinGet variants are installed; setup will manage: $($viceInstalledPkg.Id)" -ForegroundColor Yellow
        }

        $action = Invoke-WinGetInstalledMaintenance -Label 'VICE' -State $viceInstalledPkg
        if ($action -eq 'Quit') {
            Invoke-QuitWithSummary -PythonExe $python -GitExe $git -ViceExe $vice -TassExe $tass `
                -PythonAction $pythonAction -GitAction $gitAction -ViceAction $viceAction -TassAction $tassAction `
                -OriginalConfig $existingConfig
            exit 3
        }
        if ($action -eq 'Keep') { $viceAction = 'existing WinGet package kept unchanged' }
        elseif ($action -eq 'Upgrade') { $viceAction = 'WinGet upgrade completed/requested'; $vice = Find-Vice -ConfiguredPath $viceConfiguredCandidate }
        elseif ($action -eq 'Reinstall') { $viceAction = 'WinGet same-version reinstall completed/requested'; $vice = Find-Vice -ConfiguredPath $viceConfiguredCandidate }
        elseif ($action -eq 'Failed') { $viceAction = 'existing package preserved; requested WinGet maintenance failed' }
    }
    elseif (-not $vice) {
        $viceUnknown = @($vicePkgStates | Where-Object { $_.Status -eq 'Unknown' })
        if ($viceUnknown.Count -gt 0) {
            $viceAction = 'not found; WinGet state unknown, automatic install skipped'
            Write-Host 'VICE was not found on disk, but at least one VICE WinGet package-state lookup is UNKNOWN.' -ForegroundColor Yellow
            Write-Host 'Automatic VICE installation is skipped to avoid installing a duplicate when WinGet/source access may simply be blocked.'
        }
        else {
            try {
                Install-WinGetPackage -Id $KnownLocations.VICE.PreferredWingetId -Label 'VICE GTK3'
                $viceAction = 'installed through WinGet'
                $vice = Find-Vice -ConfiguredPath $viceConfiguredCandidate
            }
            catch {
                $viceAction = 'automatic WinGet install failed'
                Write-Host "VICE automatic installation failed: $($_.Exception.Message)" -ForegroundColor Yellow
            }
        }
    }

    if (-not $vice) {
        Show-ViceFallback
        $choice = Request-ExecutablePath -Label 'VICE x64sc.exe' -ExpectedNames @($KnownLocations.VICE.ExeName) -DirectoryRelatives @('bin\x64sc.exe')
        if ($choice.Action -eq 'Quit') {
            Invoke-QuitWithSummary -PythonExe $python -GitExe $git -ViceExe $vice -TassExe $tass `
                -PythonAction $pythonAction -GitAction $gitAction -ViceAction $viceAction -TassAction $tassAction `
                -OriginalConfig $existingConfig
            exit 3
        }
        if ($choice.Action -eq 'Use') { $vice = $choice.Path; $viceAction = 'manual/existing path selected' }
        elseif ($choice.Action -eq 'Skip') { $viceAction = 'skipped / not configured' }
    }

    if ($vice) {
        Write-Host "VICE selected: $vice"
        Write-Host 'VICE was NOT executed by this setup script.'
    }
    else {
        Write-Host 'VICE skipped for now.' -ForegroundColor Yellow
    }

    Write-Section '64tass'
    $tassConfiguredCandidate = if ($configMode -eq 'Keep') { $existingConfig.tass } else { $null }
    $configuredTassResolved = $null
    if ($tassConfiguredCandidate) {
        $configuredTassResolved = Resolve-ExecutableInput `
            -InputPath $tassConfiguredCandidate `
            -ExpectedNames @($KnownLocations.Tass.ExeName)
    }

    $tass = Find-64tass -ConfiguredPath $tassConfiguredCandidate
    $tassAction = if ($tass) { 'existing executable found' } else { 'not found yet' }
    $tassChangeRequested = $false
    $previousConfiguredTass = $null

    # If setup is keeping the existing Windows config and the selected executable
    # is that configured tass path, give 64tass its own explicit keep/change choice.
    # A command-line -TassPath override remains an explicit selection and bypasses
    # this prompt.
    if ($tass -and $configuredTassResolved -and (-not $TassPath) -and
        ($tass -ieq $configuredTassResolved)) {

        $tassDecision = Request-Existing64tassAction -Path $tass
        if ($tassDecision -eq 'Quit') {
            $tassAction = 'existing configured path preserved; user quit at 64tass prompt'
            Invoke-QuitWithSummary -PythonExe $python -GitExe $git -ViceExe $vice -TassExe $tass `
                -PythonAction $pythonAction -GitAction $gitAction -ViceAction $viceAction -TassAction $tassAction `
                -OriginalConfig $existingConfig
            exit 3
        }

        if ($tassDecision -eq 'Keep') {
            $tassAction = 'existing configured path kept unchanged'
        }
        elseif ($tassDecision -eq 'Change') {
            $previousConfiguredTass = $tass
            $tass = $null
            $tassChangeRequested = $true
            $tassAction = 'change requested; existing configured path retained until a replacement is selected'
        }
    }

    if ((-not $tass) -and $FindTass) {
        $foundTass = Select-64tassCandidate
        if ($foundTass) {
            $tass = $foundTass
            $tassAction = 'selected by -FindTass local search'
        }
    }

    if (-not $tass) {
        if ($tassChangeRequested) {
            Write-Host ''
            Write-Host 'Select a replacement 64tass path.' -ForegroundColor Cyan
            Write-Host "Current configured path will remain unchanged unless you select and confirm a replacement:"
            Write-Host "  $previousConfiguredTass"
        }
        else {
            Show-64tassFallback
        }

        $choice = Request-64tassPath

        if ($choice.Action -eq 'Quit') {
            if ($tassChangeRequested -and $previousConfiguredTass) {
                $tass = $previousConfiguredTass
                $tassAction = 'change cancelled by quit; existing configured path kept'
            }
            Invoke-QuitWithSummary -PythonExe $python -GitExe $git -ViceExe $vice -TassExe $tass `
                -PythonAction $pythonAction -GitAction $gitAction -ViceAction $viceAction -TassAction $tassAction `
                -OriginalConfig $existingConfig
            exit 3
        }

        if ($choice.Action -eq 'Use') {
            $tass = $choice.Path
            if ($choice.Source -eq 'Find') { $tassAction = 'replacement selected by F/FIND common-location search' }
            elseif ($choice.Source -eq 'Drive') { $tassAction = 'replacement selected by D/DRIVE whole-drive search' }
            else { $tassAction = 'replacement manual path/directory selected' }
        }
        elseif ($choice.Action -eq 'Skip') {
            if ($tassChangeRequested -and $previousConfiguredTass) {
                $tass = $previousConfiguredTass
                $tassAction = 'change cancelled; existing configured path kept'
                Write-Host 'No replacement selected; keeping the existing configured 64tass path.' -ForegroundColor Yellow
            }
            else {
                $tassAction = 'skipped / not configured'
            }
        }
    }

    if ($tass) {
        Write-Host "64tass selected: $tass"
        Write-64tassHashInfo -Path $tass
        Write-Host '64tass was NOT executed by this setup script.'
    }
    else {
        Write-Host '64tass skipped for now.' -ForegroundColor Yellow
        Write-Host 'Assembly is unavailable until 64tass is configured; use --no-assemble only for host-side generation.' -ForegroundColor Yellow
    }

    Write-Section 'Configuration'
    $changes = @(Get-ProposedWindowsConfigChanges -ConfigState $existingConfig -ViceExe $vice -TassExe $tass)
    $configChanged = $false
    if ($changes.Count -eq 0) {
        Write-Host 'No changes to the existing [windows] configuration are required.'
    }
    else {
        $decision = Confirm-WindowsConfigChanges -Changes $changes
        if ($decision -eq 'Quit') {
            Invoke-QuitWithSummary -PythonExe $python -GitExe $git -ViceExe $vice -TassExe $tass `
                -PythonAction $pythonAction -GitAction $gitAction -ViceAction $viceAction -TassAction $tassAction `
                -OriginalConfig $existingConfig
            exit 3
        }
        elseif ($decision -eq 'Apply') {
            $configChanged = Update-WindowsConfig -ViceExe $vice -TassExe $tass
        }
        else {
            Write-Host 'Configuration changes were declined; c643d.ini was left unchanged.' -ForegroundColor Yellow
        }
    }

    [void](Write-SetupSessionSummary `
        -PythonExe $python -GitExe $git -ViceExe $vice -TassExe $tass `
        -PythonAction $pythonAction -GitAction $gitAction -ViceAction $viceAction -TassAction $tassAction `
        -OriginalConfig $existingConfig)

    Write-Section 'Final configuration'
    $finalConfig = Get-WindowsConfigState
    if ($finalConfig.vice) { Write-Host "Config [windows] vice: $($finalConfig.vice)" } else { Write-Host 'Config [windows] vice: NOT SET' -ForegroundColor Yellow }
    if ($finalConfig.tass) { Write-Host "Config [windows] tass: $($finalConfig.tass)" } else { Write-Host 'Config [windows] tass: NOT SET' -ForegroundColor Yellow }

    if ($configChanged) {
        Write-Host "Config: updated ($ConfigPath)"
    }
    elseif (Test-Path -LiteralPath $ConfigPath -PathType Leaf) {
        Write-Host "Config: unchanged ($ConfigPath)"
    }
    else {
        Write-Host 'Config: not created'
    }

    Write-Host ''
    if (-not $python -or -not $tass) {
        Write-Host 'Setup finished, but the build toolchain is not complete yet.' -ForegroundColor Yellow
        Write-Host 'Install/configure the missing component(s) and rerun:'
        Write-Host '  .\setup-windows.cmd'
        Write-SetupHelpHint
        if (-not $tass) {
            Write-Host 'Reminder: 64tass is required for assembly and runnable .prg output.' -ForegroundColor Yellow
        }
    }
    else {
        Write-Host 'c64-3d-toolkit Windows setup/configuration complete.'
    }

    Write-Host 'No configured third-party tool was executed, and doctor/build was not run automatically.'
    Write-Host ''
    Write-Host 'Optional manual validation (this WILL execute the configured toolchain):'
    Write-Host '  py -3 .\c643d.py doctor'
    exit 0
}
catch {
    Write-Host ''
    Write-Host "error: $($_.Exception.Message)" -ForegroundColor Red
    try {
        Invoke-QuitWithSummary `
            -PythonExe $python -GitExe $git -ViceExe $vice -TassExe $tass `
            -PythonAction $pythonAction -GitAction $gitAction -ViceAction $viceAction -TassAction $tassAction `
            -OriginalConfig $existingConfig
    }
    catch {
        Write-Host 'Session summary/save prompt could not be completed after the error.' -ForegroundColor Yellow
    }
    Write-Host ''
    Write-Host 'Setup is still considered failed; saving valid discovered paths does not change the failure exit status.' -ForegroundColor Yellow
    Write-SetupHelpHint
    exit 1
}
