"""
VALIDATION — MATÉRIALISATION D'UNE BRIQUE : la sortie de première classe DURABLE (chantier FORGE, piste (a)).

Le mandat de Yohan : la forge doit servir « aux autres moteurs » et à l'utilisateur. Matérialiser grave une
brique apprise en artefact réutilisable HORS processus : un module `.py` importable + sa gate auto-écrite qui
RE-EXÉCUTE le spec (le FAIT borné se re-prouve seul, sans rien du moteur).

Prouve : (1) GRAVE — une invention pure produit un module + une gate sur disque, avec un identifiant valide
dérivé d'un nom parlant ; (2) IMPORTABLE & CORRECT — le module gravé s'importe et sa fonction reproduit TOUT
le spec (exécuté hors moteur) ; (3) AUTO-PORTANT — la gate auto-écrite, lancée en SUBPROCESS sans le moteur
sur le PYTHONPATH, passe (exit 0) : le FAIT se prouve seul ; (4) INNOCUITÉ (atome 7) — jamais graver du code
non sûr : un expr hostile est refusé, AUCUN fichier écrit, effet de bord jamais déclenché ; (5) CORRECTION
(atome 1) — une expr qui ne reproduit pas son spec est refusée, rien gravé ; (6) SERVABLE — le câblage
ia.materialise_brique produit une brique importable de bout en bout ; (7) IDENTIFIANT — noms exotiques (mot-clé,
chiffre initial, ponctuation) donnent des identifiants Python valides et déterministes.
"""
from __future__ import annotations

import os
import subprocess
import sys
import tempfile

from garde_ressources import borne
borne(max_cpu_s=400)
import ia
import materialise as MAT
import moteur_invention as MI

ok = total = 0


def check(nom, cond):
    global ok, total
    total += 1
    print(f"  [{'OK ' if cond else 'XXX'}] {nom}")
    if cond:
        ok += 1
    else:
        raise AssertionError(nom)


SRC = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src")
AEX = [([3, 1, 5], 4), ([2, 2], 0), ([10, 0, 3], 10)]
AHELD = [([0, 9, 4], 9), ([7], 0), ([5, 5, 1], 4)]

# ── (1) GRAVE + (2) IMPORTABLE & CORRECT ─────────────────────────────────────────────────────────────────
d = tempfile.mkdtemp(prefix="forge_mat_")
r = MAT.materialise_brique("amplitude", "max(x) - min(x)", AEX, AHELD, d, origine="amplitude")
check("grave : renvoie un artefact (pas de refus)", r and r.get("refus") is None)
check("grave : le module .py et la gate existent sur disque",
      os.path.exists(r["module"]) and os.path.exists(r["gate"]))
check("grave : identifiant valide", r["ident"].isidentifier())
# import du module gravé (isolé) et exécution de la fonction hors moteur.
sys.path.insert(0, d)
try:
    mod = __import__(r["ident"])
    f = getattr(mod, r["ident"])
    check("importable & correct : la fonction gravée reproduit TOUT le spec (hors moteur)",
          all(f(list(a)) == o for a, o in AEX + AHELD))
finally:
    sys.path.remove(d)
    sys.modules.pop(r["ident"], None)

# ── (3) AUTO-PORTANT : la gate auto-écrite passe en SUBPROCESS SANS le moteur sur le PYTHONPATH ──────────
env = dict(os.environ)
env["PYTHONPATH"] = d                       # UNIQUEMENT le dossier gravé : la gate ne dépend d'aucun module du moteur
p = subprocess.run([sys.executable, r["gate"]], capture_output=True, text=True, env=env, cwd=d, timeout=60)
check("auto-portant : la gate auto-écrite passe seule (exit 0, sans le moteur)", p.returncode == 0)
check("auto-portant : la gate re-prouve toutes les paires", "6/6 paires reproduites" in p.stdout)

# ── (4) INNOCUITÉ : jamais graver du code non sûr, aucun effet de bord ───────────────────────────────────
poc = os.path.join(tempfile.gettempdir(), "forge_mat_poc.txt")
if os.path.exists(poc):
    os.remove(poc)
d2 = tempfile.mkdtemp(prefix="forge_mat_mal_")
mal = f"(open({poc!r}, 'w').write('x'), max(x) - min(x))[1]"
rm = MAT.materialise_brique("piegee", mal, AEX, AHELD, d2, origine="piegee")
check("innocuité : expr hostile REFUSÉE (refus dit, rien gravé)",
      rm.get("refus") and "non sûre" in rm["refus"])
check("innocuité : aucun fichier .py écrit dans le dossier", not os.listdir(d2))
check("innocuité : l'effet de bord n'a PAS été déclenché (jugé avant exécution)", not os.path.exists(poc))

# ── (5) CORRECTION : une expr qui ne reproduit pas son spec est refusée ──────────────────────────────────
d3 = tempfile.mkdtemp(prefix="forge_mat_faux_")
rf = MAT.materialise_brique("faux", "sum(x)", AEX, AHELD, d3)   # sum != amplitude
check("correction : expr ne reproduisant pas le spec REFUSÉE", rf.get("refus") and "reproduit pas" in rf["refus"])
check("correction : rien gravé", not os.listdir(d3))

# ── (6) SERVABLE : câblage ia.materialise_brique de bout en bout ─────────────────────────────────────────
d4 = tempfile.mkdtemp(prefix="forge_mat_ia_")
sortie = ia.materialise_brique("amplitude", "x", AEX, AHELD, dossier=d4)
check("servable : ia.materialise_brique grave une invention",
      sortie["statut"] == MI.INVENTION and sortie["materialise"] and sortie["materialise"]["refus"] is None)
pe = subprocess.run([sys.executable, sortie["materialise"]["gate"]],
                    capture_output=True, text=True, env={**os.environ, "PYTHONPATH": d4}, cwd=d4, timeout=60)
check("servable : la gate de la brique ia-matérialisée passe seule", pe.returncode == 0)

# ── (7) IDENTIFIANT : noms exotiques -> identifiants valides et déterministes ────────────────────────────
for src_nom, attendu_ok in [("class", True), ("2eme-mesure", True), ("mon calcul!", True)]:
    idt = MAT._identifiant(src_nom)
    check(f"identifiant : « {src_nom} » -> « {idt} » valide", idt.isidentifier() and not (idt in __import__("keyword").kwlist))
check("identifiant : déterministe (même entrée -> même sortie)", MAT._identifiant("a b") == MAT._identifiant("a b"))

print(f"\n== VALIDE_MATERIALISE : {ok}/{total} ==")
assert ok == total
