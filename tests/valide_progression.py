"""
VALIDE LE RETOUR DE PROGRESSION — un chargement/màj long ne doit JAMAIS sembler figé.

DÉFAUT UX (2026-07-12, Yohan) : « quand j'ai le message de mise à jour il faudrait 3 points qui défilent
ou une barre ou un %, car on peut penser que c'est bloqué. » Deux écrans muets de plusieurs minutes :
le préchargement de la connaissance (72 M de faits à froid) et le téléchargement de la mise à jour du .exe.

CE QU'IL GARDE (le contrat, pas le pixel) :
  • `lecteur.PROGRES_CHARGE` publie une progression LISIBLE par un poller externe : total, charges
    croissantes, drapeau `fini`. Sans dépendance vers l'interface (respect des couches).
  • le statut serveur porte `pct` (barre déterminée) et `maj_appli` (vue mise à jour), surfacés à l'UI.
  • le front sait rendre une barre pour CHACUN des trois écrans longs (chargement, installation, màj).
"""
import os
import re
import sys

_RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_RACINE, "src"))

ok = 0
ko = 0


def check(cond, label):
    global ok, ko
    if cond:
        ok += 1
    else:
        ko += 1
        print(f"  FAIL: {label}")


# ── 1) lecteur publie une progression exploitable ───────────────────────────────────────────────────
import lecteur as L

check(isinstance(L.PROGRES_CHARGE, dict), "lecteur.PROGRES_CHARGE existe")
for k in ("charges", "total", "relation", "fini"):
    check(k in L.PROGRES_CHARGE, "PROGRES_CHARGE porte la clé « %s »" % k)

# charge_dossier sur un mini-dossier : total = nb de .jsonl, charges monte jusqu'à total, fini passe True.
import json
import tempfile

_d = tempfile.mkdtemp(prefix="verax_prog_")
for i in range(3):
    with open(os.path.join(_d, "t%d.jsonl" % i), "w", encoding="utf-8") as f:
        f.write('{"_relation":"t%d","_categorie":"convention","_source":"s"}\n' % i)
        f.write('{"entite":"e","valeur":"v%d"}\n' % i)
open(os.path.join(_d, "pas_un.txt"), "w").write("ignore")   # non-.jsonl : ne compte pas

_lect = L.Lecteur() if hasattr(L, "Lecteur") else L.LECTEUR.__class__()
L.PROGRES_CHARGE.update(charges=0, total=0, fini=False)
_lect.charge_dossier(_d, utiliser_mmap=False)
check(L.PROGRES_CHARGE["total"] == 3, "total = nombre de .jsonl (le .txt est ignoré) : %d" % L.PROGRES_CHARGE["total"])
check(L.PROGRES_CHARGE["charges"] == 3, "charges atteint le total à la fin")
check(L.PROGRES_CHARGE["fini"] is True, "le drapeau `fini` passe à True en fin de chargement")

# dossier absent -> fini True immédiat, total 0 (pas de division par zéro côté poller)
L.PROGRES_CHARGE.update(charges=0, total=0, fini=False)
_lect.charge_dossier(os.path.join(_d, "inexistant"), utiliser_mmap=False)
check(L.PROGRES_CHARGE["fini"] is True, "dossier absent -> `fini` True (le poller s'arrête proprement)")

# ── 2) le statut serveur porte pct + maj_appli et les surface ────────────────────────────────────────
sys.path.insert(0, os.path.join(_RACINE, "interface"))
os.environ.setdefault("LECTEUR_DATASETS_DIR", os.path.join(_RACINE, "datasets", "lecteur"))
import serveur

for k in ("pct", "maj_appli"):
    check(k in serveur._STATUT, "le statut serveur porte « %s »" % k)
s = serveur.statut_chargement()
check("pct" in s and "maj_appli" in s, "statut_chargement() surface pct + maj_appli à l'UI")

serveur._maj_statut(phase="chargement", pct=42, detail="… 42 %")
check(serveur.statut_chargement()["pct"] == 42, "un pct posé est bien relu (barre déterminée)")
serveur._maj_statut(phase="maj_appli", maj_appli=True, detail="Mise à jour…")
check(serveur.statut_chargement()["maj_appli"] is True, "maj_appli posé est relu (vue mise à jour)")
serveur._maj_statut(phase="", maj_appli=False, pct=None, detail="")     # remise à zéro

# ── 3) le front sait rendre une barre pour les TROIS écrans longs ────────────────────────────────────
html = open(os.path.join(_RACINE, "interface", "index.html"), encoding="utf-8").read()
check("function vueMajApp" in html, "vue « mise à jour de l'app » présente")
# chaque vue longue référence la barre (déterminée `vm-bar` OU animée `vm-bar indet`)
for vue in ("vueChargement", "vueInstallation", "vueMajApp"):
    corps = re.search(vue + r"\(s\)\s*\{(.*?)\n  \}", html, re.S)
    check(corps is not None and "vm-bar" in corps.group(1),
          "%s affiche une barre de progression (plus jamais un écran muet)" % vue)
check("s.maj_appli" in html, "le routeur de vues (tick) dirige vers la vue mise à jour")

print("=== valide_progression : %d ok, %d ko ===" % (ok, ko))
sys.exit(1 if ko else 0)
