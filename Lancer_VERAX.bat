@echo off
REM VERAX - double-cliquez pour lancer l'IA (necessite Python 3.10+ installe).
cd /d "%~dp0"
python lance.py
if errorlevel 1 (
  echo.
  echo Python 3.10+ est requis. Installez-le depuis https://www.python.org/downloads/
  echo A l'installation, cochez "Add Python to PATH".
  pause
)
