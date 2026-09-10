@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>nul
if not errorlevel 1 (
  py -3 scripts\run_local.py
  goto done
)
where python >nul 2>nul
if not errorlevel 1 (
  python scripts\run_local.py
  goto done
)
if exist "%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" (
  "%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" scripts\run_local.py
  goto done
)
echo Python 3.11 or newer is required. Install Python and try again.
:done
if errorlevel 1 pause
endlocal
