#!/usr/bin/env bash
# VERAX — lance l'interface web locale (Linux/Mac). Windows : utilise VERAX.exe.
cd "$(dirname "$0")"
exec python3 lance.py
