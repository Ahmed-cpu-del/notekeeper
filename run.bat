@echo off
setlocal
rem Always navigate to the root directory where run.bat resides
cd /d "%~dp0"

set "PY_EXE="
if exist "%LOCALAPPDATA%\Python\bin\python.exe" (
    set "PY_EXE=%LOCALAPPDATA%\Python\bin\python.exe"
) else (
    set "PY_EXE=python"
)

"%PY_EXE%" notekeeper\main.py %*
