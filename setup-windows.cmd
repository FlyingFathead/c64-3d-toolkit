@echo off
rem c64-3d-toolkit Windows installer / configuration assistant
rem Installer revision: r24 (2026-09-02)
rem Target toolkit release: v0.6.5

setlocal
set "SCRIPT_DIR=%~dp0"
set "PS1=%SCRIPT_DIR%setup-windows.ps1"
set "RC=0"

if not exist "%PS1%" (
    echo error: setup-windows.ps1 was not found next to setup-windows.cmd.
    echo Keep setup-windows.cmd and setup-windows.ps1 in the toolkit root.
    echo Setup help normally: .\setup-windows.cmd -Help
    set "RC=1"
    goto :finish
)

powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%PS1%" %*
set "RC=%ERRORLEVEL%"

if not "%RC%"=="0" (
    echo.
    if "%RC%"=="3" (
        echo c64-3d-toolkit setup was cancelled by the user.
    ) else (
        echo c64-3d-toolkit setup did not complete ^(exit code %RC%^).
        echo Read the instructions printed above, fix/install the missing component, and rerun:
        echo   .\setup-windows.cmd
        echo For setup/recovery options:
        echo   .\setup-windows.cmd -Help
    )
)

:finish
echo.
echo NOTE: If setup installed or updated any tools, close this terminal and open a new
echo PowerShell/Command Prompt before using them so PATH and command-alias changes are picked up.
echo.
exit /b %RC%
