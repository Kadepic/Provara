"""VERAX — bootstrap de chemins (à importer EN PREMIER depuis un point d'entrée).

Rend l'espace de noms « à plat » (import lecteur, import chimie, ...) utilisable alors que les modules
sont rangés dans src/, ingestion/, tests/, interface/. Conscient du mode « frozen » (.exe PyInstaller).
Données : la base COMPLÈTE téléchargée (~/.verax) prime sur l'échantillon embarqué. stdlib pure.
"""
import os
import sys

if getattr(sys, "frozen", False):
    _ROOT = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(sys.executable)))
else:
    _ROOT = os.path.dirname(os.path.abspath(__file__))
os.environ.setdefault("VERAX_ROOT", _ROOT)


def _a_des_donnees(d):
    try:
        return os.path.isdir(d) and any(f.endswith(".jsonl") for f in os.listdir(d))
    except OSError:
        return False


_home = os.environ.get("VERAX_DATA_HOME") or os.path.join(os.path.expanduser("~"), ".verax")
_complet = os.path.join(_home, "datasets", "lecteur")     # base complète téléchargée
_echantillon = os.path.join(_ROOT, "datasets", "lecteur")  # échantillon embarqué
if "LECTEUR_DATASETS_DIR" not in os.environ:
    if _a_des_donnees(_complet):
        os.environ["LECTEUR_DATASETS_DIR"] = _complet
    elif os.path.isdir(_echantillon):
        os.environ["LECTEUR_DATASETS_DIR"] = _echantillon

for _sub in ("src", "ingestion", "tests", "interface"):
    _p = os.path.join(_ROOT, _sub)
    if os.path.isdir(_p) and _p not in sys.path:
        sys.path.insert(0, _p)
