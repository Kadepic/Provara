"""VALIDE l'ingestion population_pays (Banque mondiale) + le câblage ia.densite_pays — ADVERSE, FAUX=0.

Ancres EXTERNES non circulaires (densités connues, hab/km²) : Monaco/Singapour très denses, Mongolie/Canada très
peu denses, France ~120. Soundness : pays inconnu -> None (HORS) ; toutes les populations = entiers positifs
plausibles ; clés alignées sur superficie (sinon densite_pays serait toujours None)."""
import json
import os

import ia

ok = 0
ko = 0


def check(c, l):
    global ok, ko
    if c:
        ok += 1
    else:
        ko += 1
        print(f"  FAIL: {l}")


# ── ancres externes de DENSITÉ (via le vrai chemin ia.densite_pays) ──
# (borne, min, max) en hab/km² — fourchettes larges, vérifiées indépendamment.
ANCRES = {
    "France": (100, 140), "Monaco": (10000, 30000), "Singapour": (5000, 12000),
    "Bangladesh": (900, 1500), "Mongolie": (1, 5), "Canada": (2, 7), "Inde": (350, 550),
}
for nom, (lo, hi) in ANCRES.items():
    d = ia.densite_pays(nom)
    check(d is not None, f"{nom} : densité calculée (pop et superficie présentes)")
    if d is not None:
        check(lo <= d <= hi, f"{nom} : densité {d:.1f} dans [{lo},{hi}] hab/km²")

# ordre de bon sens : Monaco >> France >> Mongolie
dM, dF, dMn = ia.densite_pays("Monaco"), ia.densite_pays("France"), ia.densite_pays("Mongolie")
check(dM and dF and dMn and dM > dF > dMn, "ordre densités Monaco > France > Mongolie")

# ── SOUNDNESS ──
check(ia.densite_pays("Pays-Qui-N-Existe-Pas-42") is None, "pays inconnu -> None (HORS)")
check(ia.densite_pays("") is None, "nom vide -> None (HORS)")

# ── bulk : table population_pays saine ──
DOSSIER = os.environ.get("LECTEUR_DATASETS_DIR") or os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "datasets", "lecteur")
pop = {}
for ligne in open(os.path.join(DOSSIER, "population_pays.jsonl"), encoding="utf-8"):
    o = json.loads(ligne)
    if "entite" in o:
        pop[o["entite"]] = o["valeur"]
check(len(pop) > 150, f"population_pays peuplée ({len(pop)} pays)")
mauvais = [n for n, v in pop.items() if not (v.isdigit() and int(v) > 0)]
check(not mauvais, f"toutes les populations = entiers positifs (contre-ex : {mauvais[:3]})")
# plausibilité globale : au moins un pays > 1 milliard (Inde/Chine), aucun > 2 milliards
vals = [int(v) for v in pop.values()]
check(max(vals) > 1_000_000_000 and max(vals) < 2_000_000_000, f"population max plausible ({max(vals)})")
# alignement des clés : une bonne part de population_pays a une superficie (sinon densite_pays serait vide)
sup = set()
for ligne in open(os.path.join(DOSSIER, "superficie.jsonl"), encoding="utf-8"):
    o = json.loads(ligne)
    if "entite" in o:
        sup.add(o["entite"])
communs = sum(1 for n in pop if n in sup)
check(communs > 150, f"clés alignées sur superficie ({communs} pays en commun)")

# France : population dans une fourchette sensée (instantané récent)
check("France" in pop and 60_000_000 <= int(pop["France"]) <= 70_000_000, f"population France sensée ({pop.get('France')})")

print(f"\n=== valide_population_pays : {ok}/{ok + ko} ===")
import sys

sys.exit(0 if ko == 0 else 1)
