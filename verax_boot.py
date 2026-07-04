"""VERAX — bootstrap de chemins (à importer EN PREMIER depuis un point d'entrée).

Rend l'espace de noms « à plat » (import lecteur, import chimie, ...) utilisable alors que les modules
sont rangés dans src/, ingestion/, tests/, interface/. Conscient du mode « frozen » (.exe PyInstaller) :
localise robustement le dossier des données, même si PyInstaller l'a rangé ailleurs. stdlib pure.
Données : base COMPLÈTE téléchargée (~/.verax) > échantillon embarqué.
"""
import os
import sys

# Sorties TOLÉRANTES. Deux cas à couvrir pour ne JAMAIS planter sur un print :
#  1) console présente : l'encodage peut retomber sur cp1252 (« ✓ », « — » -> UnicodeEncodeError) -> errors="replace".
#  2) .exe FENÊTRÉ (--noconsole, pas de console) : sys.stdout/stderr valent None -> tout print() lèverait une erreur.
#     -> on les redirige vers un fichier journal (~/.verax/verax.log), utile aussi pour diagnostiquer sans console.
_verax_log = None
for _n in ("stdout", "stderr"):
    _flux = getattr(sys, _n, None)
    if _flux is None:
        if _verax_log is None:
            try:
                _home = os.environ.get("VERAX_DATA_HOME") or os.path.join(os.path.expanduser("~"), ".verax")
                os.makedirs(_home, exist_ok=True)
                _verax_log = open(os.path.join(_home, "verax.log"), "a", encoding="utf-8", errors="replace")
            except Exception:
                _verax_log = open(os.devnull, "w")
        setattr(sys, _n, _verax_log)
    else:
        try:
            _flux.reconfigure(errors="replace")
        except Exception:
            pass

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


def _trouve_cache_livre():
    """Cache `.colf` PRÉ-CONSTRUIT livré avec la base complète (Release) : évite le build d'index au TOUT premier
    lancement (sinon pic RAM/temps une fois). Cherché à côté des données (`~/.verax/cache`) puis dans le bundle.
    Renvoie le dossier s'il contient des `.colf`, sinon None."""
    _home = os.environ.get("VERAX_DATA_HOME") or os.path.join(os.path.expanduser("~"), ".verax")
    for _c in (os.path.join(_home, "cache"), os.path.join(_ROOT, "cache")):
        try:
            if os.path.isdir(_c) and any(f.endswith(".colf") for f in os.listdir(_c)):
                return _c
        except OSError:
            pass
    return None


# Cache livré -> on le pointe + mode PORTABLE (le mtime des jsonl change à l'extraction ; on se fie à la taille).
# Sans cache livré, comportement inchangé : le lecteur construit son index au 1er lancement (dans ~/.cache).
if "LECTEUR_CACHE_DIR" not in os.environ:
    _cache_livre = _trouve_cache_livre()
    if _cache_livre:
        os.environ["LECTEUR_CACHE_DIR"] = _cache_livre
        os.environ.setdefault("LECTEUR_CACHE_PORTABLE", "1")

for _sub in ("src", "ingestion", "tests", "interface"):
    _p = os.path.join(_ROOT, _sub)
    if os.path.isdir(_p) and _p not in sys.path:
        sys.path.insert(0, _p)
