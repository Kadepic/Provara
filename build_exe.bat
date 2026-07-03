@echo off
REM ==== VERAX : compile VERAX.exe (Windows) ====
REM Utilise le lanceur "py" (pas besoin que "python" soit dans le PATH).
cd /d "%~dp0"
echo ================================================
echo   VERAX - compilation de VERAX.exe
echo ================================================

where py >nul 2>&1
if errorlevel 1 (
  echo.
  echo ERREUR : le lanceur Python "py" est introuvable.
  echo Installe Python 3.10+ depuis https://www.python.org/downloads/
  echo  ^(coche "Add Python to PATH" pendant l'installation^).
  echo.
  pause
  exit /b 1
)

echo.
echo [1/2] Installation de PyInstaller...
py -m pip install --upgrade pyinstaller
if errorlevel 1 (
  echo.
  echo ERREUR pendant l'installation de PyInstaller ^(voir ci-dessus^).
  pause
  exit /b 1
)

echo.
echo [2/2] Compilation ^(quelques minutes, ne ferme pas cette fenetre^)...
py -m PyInstaller --onefile --name VERAX ^
  --add-data "src;src" ^
  --add-data "ingestion;ingestion" ^
  --add-data "interface;interface" ^
  --add-data "datasets;datasets" ^
  --add-data "verax_boot.py;." ^
  --hidden-import json --hidden-import csv --hidden-import sqlite3 ^
  --hidden-import wave --hidden-import struct --hidden-import array ^
  --hidden-import zlib --hidden-import gzip --hidden-import bz2 --hidden-import lzma --hidden-import hashlib ^
  --hidden-import xml.etree.ElementTree --hidden-import urllib.request ^
  --hidden-import http.server --hidden-import socketserver --hidden-import zipfile --hidden-import tarfile --hidden-import marshal ^
  lance.py
if errorlevel 1 (
  echo.
  echo ERREUR pendant la compilation. Copie-colle le message d'erreur ci-dessus et envoie-le.
  pause
  exit /b 1
)

echo.
echo ================================================
echo   OK : VERAX.exe est dans le dossier  dist\
echo ================================================
pause
