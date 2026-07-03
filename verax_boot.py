"""VERAX — bootstrap de chemins (à importer EN PREMIER depuis un point d'entrée).

Rend l'espace de noms « à plat » (import lecteur, import chimie, ...) utilisable alors que les modules
sont rangés dans src/, ingestion/, tests/, interface/. Conscient du mode « frozen » (.exe PyInstaller) :
localise robustement le dossier des données, même si PyInstaller l'a rangé ailleurs. stdlib pure.
Données : base COMPLÈTE téléchargée (~/.verax) > échantillon embarqué.
"""
import os
import sys

if getattr(sys, "frozen", False):
    _ROOT = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(sys.executable)))
else:
    _ROOT = os.path.dirname(os.path.abspath(__file__))
os.environ.setdefault("VERAX_ROOT", _ROOT)


def _a_des_jsonl(d):
    try:
        return os.path.isdir(d) and any(f.endswith(".jsonl") for f in os.listdir(d))
    except OSError:
        return False


def _trouve_donnees():
    _home = os.environ.get("VERAX_DATA_HOME") or os.path.join(os.path.expanduser("~"), ".verax")
    _complet = os.path.join(_home, "datasets", "lecteur")     # base complète téléchargée
    if _a_des_jsonl(_complet):
        return _complet
    _ech = os.path.join(_ROOT, "datasets", "lecteur")          # échantillon (chemin attendu)
    if _a_des_jsonl(_ech):
        return _ech
    # .exe : le layout PyInstaller peut différer -> localise l'échantillon par un fichier connu
    import glob
    for motif in ("capitale.jsonl", "*.jsonl"):
        hits = glob.glob(os.path.join(_ROOT, "**", motif), recursive=True)
        if hits:
            return os.path.dirname(hits[0])
    return _ech


if "LECTEUR_DATASETS_DIR" not in os.environ:
    os.environ["LECTEUR_DATASETS_DIR"] = _trouve_donnees()

for _sub in ("src", "ingestion", "tests", "interface"):
    _p = os.path.join(_ROOT, _sub)
    if os.path.isdir(_p) and _p not in sys.path:
        sys.path.insert(0, _p)
