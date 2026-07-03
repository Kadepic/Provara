@echo off
cd /d "%~dp0"
echo === VERAX : compilation de VERAX.exe ===
where py >nul 2>&1 || ( echo Installe Python 3.10+ ^: https://www.python.org/downloads/ & pause & exit /b 1 )
py -m pip install --upgrade pyinstaller
py -m PyInstaller --onefile --name VERAX ^
  --paths src --paths ingestion --paths interface ^
  --hidden-import _precharge_verax ^
  --hidden-import ia --hidden-import lecteur --hidden-import base_faits ^
  --hidden-import serveur --hidden-import repond --hidden-import conversation ^
  --hidden-import assistant_nl --hidden-import veille_structure --hidden-import fonction_nl ^
  --add-data "src;src" --add-data "ingestion;ingestion" --add-data "interface;interface" ^
  --add-data "datasets;datasets" --add-data "verax_boot.py;." ^
  --hidden-import json --hidden-import csv --hidden-import sqlite3 --hidden-import wave --hidden-import struct ^
  --hidden-import array --hidden-import zlib --hidden-import gzip --hidden-import bz2 --hidden-import lzma ^
  --hidden-import hashlib --hidden-import decimal --hidden-import fractions --hidden-import statistics ^
  --hidden-import unicodedata --hidden-import secrets --hidden-import uuid ^
  --hidden-import "xml.etree.ElementTree" --hidden-import "urllib.request" --hidden-import "urllib.parse" ^
  --hidden-import "http.server" --hidden-import socketserver --hidden-import zipfile --hidden-import tarfile ^
  --hidden-import marshal --hidden-import base64 --hidden-import difflib --hidden-import calendar ^
  lance.py
if errorlevel 1 ( echo ERREUR ^(copie le message^). & pause & exit /b 1 )
echo OK : dist\VERAX.exe
pause
