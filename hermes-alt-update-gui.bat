@echo off
REM ============================================================
REM  hermes-alt-update-gui launcher (ASCII only - cp866 safe)
REM  1. finds the GUI script (next to this .bat, then Hermes tools dir)
REM  2. finds a Python with Tkinter (Hermes venv first, then PATH / py)
REM  3. optionally installs Python via winget if nothing was found
REM  Pass-through args: --check   (check only)   --lang en|ru   --repo <path>
REM ============================================================
setlocal EnableExtensions
set "HERE=%~dp0"
set "GUI=%HERE%hermes_update_gui.py"
if not exist "%GUI%" set "GUI=%LOCALAPPDATA%\hermes\tools\hermes-alt-update-gui\hermes_update_gui.py"
if not exist "%GUI%" (
  echo [ERROR] hermes_update_gui.py not found next to this launcher
  echo         and not in %%LOCALAPPDATA%%\hermes\tools\hermes-alt-update-gui
  pause
  exit /b 1
)

REM ---- 1. Hermes venv pythonw (the usual case: Hermes is already installed)
set "PYW=%LOCALAPPDATA%\hermes\hermes-agent\venv\Scripts\pythonw.exe"
if exist "%PYW%" goto :run

REM ---- 2. pythonw on PATH
for /f "delims=" %%i in ('where pythonw 2^>nul') do (
  set "PYW=%%i"
  goto :run
)

REM ---- 3. py launcher (pythonw.exe next to the py-managed interpreter)
for /f "delims=" %%i in ('py -3 -c "import sys,os;print(os.path.join(os.path.dirname(sys.executable),'pythonw.exe'))" 2^>nul') do (
  if exist "%%i" (
    set "PYW=%%i"
    goto :run
  )
)

REM ---- 4. nothing found: try winget (Windows 10/11 ships it)
echo Python with Tkinter was not found. Trying: winget install Python.Python.3.12
winget install -e --id Python.Python.3.12 --accept-package-agreements --accept-source-agreements --silent
if errorlevel 1 (
  echo [ERROR] No Python found and winget install failed.
  echo         Install Python 3.10+ ^(with "tcl/tk and IDLE" option^) and run again.
  pause
  exit /b 1
)
for /f "delims=" %%i in ('where pythonw 2^>nul') do (
  set "PYW=%%i"
  goto :run
)
echo [ERROR] Python installed but pythonw.exe still not found. Reopen a new terminal.
pause
exit /b 1

:run
if "%1"=="--dry-run" (
  echo [dry-run] PYW=%PYW%
  echo [dry-run] GUI=%GUI%
  exit /b 0
)
start "" "%PYW%" "%GUI%" %*
exit /b 0
