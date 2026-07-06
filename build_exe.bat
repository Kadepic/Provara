@echo off
cd /d "%~dp0"
echo === Provara : compilation de Provara.exe ===
where py >nul 2>&1 || ( echo Installe Python 3.10+ ^: https://www.python.org/downloads/ & pause & exit /b 1 )
rem Tampon de version : le .exe sait de quel commit il vient (affiché au démarrage + « diagnostic »).
set "VERAX_SHA="
for /f %%i in ('git rev-parse --short=12 HEAD 2^>nul') do set "VERAX_SHA=%%i"
if not defined VERAX_SHA set "VERAX_SHA=build-local"
> VERSION_BUILD.txt echo %VERAX_SHA%
py -m pip install --upgrade pyinstaller
rem Mode FENÊTRÉ par défaut (pas de console noire au lancement ; les messages vont dans ~/.verax/verax.log
rem et l'interface web affiche une modale de chargement). Pour rétablir la console : VERAX_CONSOLE=1.
set "WINFLAG=--noconsole"
if "%VERAX_CONSOLE%"=="1" set "WINFLAG="
rem ONEDIR (remede antivirus, builds 49 et suivants) : VERAX_ONEDIR=1 produit dist\Provara\ (exe + _internal,
rem extrait UNE fois -- plus de re-extraction %%TEMP%% scannee par l'AV a chaque lancement). Defaut : --onefile.
set "PACKFLAG=--onefile"
if "%VERAX_ONEDIR%"=="1" set "PACKFLAG=--onedir"
py -m PyInstaller %PACKFLAG% --name Provara %WINFLAG% ^
  --paths src --paths ingestion --paths interface ^
  --hidden-import _precharge_verax ^
  --hidden-import ia --hidden-import lecteur --hidden-import base_faits ^
  --hidden-import serveur --hidden-import repond --hidden-import conversation ^
  --hidden-import assistant_nl --hidden-import veille_structure --hidden-import fonction_nl ^
  --hidden-import correction_ortho --hidden-import synonymes --hidden-import formulation ^
  --hidden-import est_un --hidden-import ontologie --hidden-import classifieur_bornage --hidden-import resolution ^
  --hidden-import realisation_fr --hidden-import deduction --hidden-import induction_horn --hidden-import maj ^
  --add-data "src;src" --add-data "ingestion;ingestion" --add-data "interface;interface" ^
  --add-data "datasets/lecteur;datasets/lecteur" --add-data "verax_boot.py;." --add-data "VERSION_BUILD.txt;." ^
  --hidden-import json --hidden-import csv --hidden-import sqlite3 --hidden-import wave --hidden-import struct ^
  --hidden-import array --hidden-import zlib --hidden-import gzip --hidden-import bz2 --hidden-import lzma ^
  --hidden-import hashlib --hidden-import decimal --hidden-import fractions --hidden-import statistics ^
  --hidden-import unicodedata --hidden-import secrets --hidden-import uuid ^
  --hidden-import "xml.etree.ElementTree" --hidden-import "urllib.request" --hidden-import "urllib.parse" ^
  --hidden-import "http.server" --hidden-import socketserver --hidden-import zipfile --hidden-import tarfile ^
  --hidden-import marshal --hidden-import base64 --hidden-import difflib --hidden-import calendar ^
  lance.py
if errorlevel 1 ( echo ERREUR ^(copie le message^). & pause & exit /b 1 )
echo OK : dist\Provara.exe
pause
