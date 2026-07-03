#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VERAX — lanceur. Démarre l'interface web locale et ouvre le navigateur.

  • Sources :  python3 lance.py   (VERAX_FULL=1 pour installer la base complète)
  • .exe (Windows) : double-clic — installe la base complète au 1er lancement, puis instantané.

Localhost uniquement : les données ne quittent jamais la machine. Aucun GPU, aucune dépendance.
"""
import os
import sys
import threading
import time
import webbrowser

if getattr(sys, "frozen", False):
    _ROOT = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(sys.executable)))
else:
    _ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _ROOT)
import verax_boot  # noqa: F401,E402  -- chemins + choix des données

# .exe (ou VERAX_FULL=1) : installe la base complète (73M faits) une fois, puis bascule dessus.
if getattr(sys, "frozen", False) or os.environ.get("VERAX_FULL") == "1":
    try:
        import telecharge_donnees  # noqa: E402
        if telecharge_donnees.assure_base_complete():
            os.environ["LECTEUR_DATASETS_DIR"] = telecharge_donnees.dossier_donnees()
    except Exception as _e:
        print("  (base complète non installée : %s)" % _e)

import glob as _glob
_dd = os.environ.get("LECTEUR_DATASETS_DIR", "")
_nrel = len(_glob.glob(os.path.join(_dd, "*.jsonl"))) if _dd and os.path.isdir(_dd) else 0
print("  donnees : %d relation(s) chargeables  [%s]" % (_nrel, _dd))
os.environ.setdefault("IA_PLEINE", "1")
os.environ.setdefault("IA_WEB", "1")  # recherche structurée en secours (source fiable, attribuée)
_PORT = int(os.environ.get("PORT", "8765"))
_URL = "http://127.0.0.1:%d" % _PORT


def _ouvre_navigateur():
    time.sleep(2.0)
    try:
        webbrowser.open(_URL)
    except Exception:
        pass


print("=" * 58)
print("  VERAX — ouvre  %s" % _URL)
print("  localhost uniquement · aucun GPU · Ctrl+C pour arrêter")
print("=" * 58)
threading.Thread(target=_ouvre_navigateur, daemon=True).start()

sys.path.insert(0, os.path.join(_ROOT, "interface"))
import serveur  # noqa: E402  -- interface/serveur.py
serveur.main()
