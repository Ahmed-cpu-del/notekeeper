@echo off
setlocal
cd /d "%~dp0"

if exist "%LOCALAPPDATA%\Python\bin\python.exe" (
    "%LOCALAPPDATA%\Python\bin\python.exe" notekeeper\main.py %*
) else (
    python notekeeper\main.py %*
)
