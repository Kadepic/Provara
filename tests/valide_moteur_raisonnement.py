"""
VALIDATION du CÂBLAGE end-to-end (moteur_raisonnement.py) — les briques dialoguent vraiment.

Scénario fil rouge = le refroidissement (COP réel vs Carnot), déroulé de bout en bout par les briques câblées :
fait → loi (Carnot) → écart (limite) → vérification → verdict (abstention) → trace vérifiable.
Plus : chemin CONTRADICTION (arbitre) et chemin IMPOSSIBLE (borne violée -> HORS).
FAUX=0 : rien d'inventé ; abstention/HORS au doute ; trace re-vérifiable.
"""
from __future__ import annotations

import dimensions as D
from grandeur import Grandeur
from loi import Loi
from limite import Limite
from moteur_raisonnement import MoteurRaisonnement
from abstention import VERIFIE, ABSTENTION, HORS

ok = 0; total = 0
def check(nom, cond):
    global ok, total; total += 1
    print(f"  [{'OK ' if cond else 'XXX'}] {nom}", flush=True)
    if cond: ok += 1
    else: raise AssertionError(nom)

# Loi et limite de Carnot (réutilisées de la brique limite).
carnot = Loi("COP_Carnot",
             variables={"COP": D.SANS, "T_froid": D.TEMPERATURE, "T_chaud": D.TEMPERATURE},
             solveurs={"COP": lambda T_froid, T_chaud: T_froid / (T_chaud - T_froid) if T_chaud > T_froid else None})
lim = Limite("COP_Carnot", carnot, cible="COP", sens="max")

# ── CHAÎNE COMPLÈTE (cas nominal) ────────────────────────────────────────────────────────
m = MoteurRaisonnement()
m.observe("T_froid", Grandeur.depuis(295, "K"), source="capteur_interieur", confiance=0.95)
m.observe("T_chaud", Grandeur.depuis(310, "K"), source="capteur_exterieur", confiance=0.95)
m.observe("COP_reel", Grandeur(3.5, D.SANS), source="fiche_produit", confiance=0.9)
# dérive la borne théorique via la loi
borne = m.derive("COP_max", carnot, "COP", {"T_froid": "T_froid", "T_chaud": "T_chaud"})
check("chaîne: la borne de Carnot est dérivée (~19.67)", borne is not None and abs(borne.valeur - 295/15) < 1e-9)
# écart au théorique
r = m.marge("analyse_COP", lim, "COP_reel", {"T_froid": "T_froid", "T_chaud": "T_chaud"}, borne_sujet="COP_max")
check("chaîne: écart calculé, réel respecte la borne", r is not None and r["respecte"])
check("chaîne: marge d'invention ≈ ×5.6", abs(r["facteur_marge"] - (295/15)/3.5) < 1e-9)
# verdict + trace
v = m.verdict("analyse_COP", seuil=0.5)
check("chaîne: verdict VERIFIE (preuve + confiance + pas d'impossibilité)", v == VERIFIE)
check("chaîne: la trace menant à l'analyse est VÉRIFIABLE de bout en bout", m.trace_verifie("analyse_COP"))
check("chaîne: la sous-trace remonte aux 3 faits observés",
      {"T_froid", "T_chaud", "COP_reel", "COP_max", "analyse_COP"} <= set(m.tr.remonte("analyse_COP")))

# ── CHEMIN IMPOSSIBLE : un COP réel qui VIOLE Carnot -> HORS ──────────────────────────────
m2 = MoteurRaisonnement()
m2.observe("T_froid", Grandeur.depuis(295, "K"), source="s", confiance=0.9)
m2.observe("T_chaud", Grandeur.depuis(310, "K"), source="s", confiance=0.9)
m2.observe("COP_reel", Grandeur(25.0, D.SANS), source="pub_douteuse", confiance=0.9)  # 25 > 19.67 = impossible
r2 = m2.marge("analyse", lim, "COP_reel", {"T_froid": "T_froid", "T_chaud": "T_chaud"})
check("impossible: la brique limite flague le réel > borne", r2["impossible"])
check("impossible: le moteur tranche HORS (jamais accepté comme marge)", m2.verdict("analyse") == HORS)
check("impossible: la trace de l'analyse NE se vérifie PAS (étape impossible)", not m2.trace_verifie("analyse"))

# ── CHEMIN CONTRADICTION : deux sources sur COP_reel -> arbitre ───────────────────────────
m3 = MoteurRaisonnement()
m3.observe("COP_reel", Grandeur(3.5, D.SANS), source="labo_accredite")
m3.observe("COP_reel", Grandeur(9.0, D.SANS), source="forum")
statut, val = m3.resout_conflit("COP_reel", {"labo_accredite": 0.95, "forum": 0.2})
check("contradiction: arbitre tranche pour la source fiable (labo -> 3.5)", val is not None and val.valeur == 3.5)
# contradiction indécidable -> pas de valeur -> verdict abstient/HORS
m4 = MoteurRaisonnement()
m4.observe("x", Grandeur(1.0, D.SANS), source="a")
m4.observe("x", Grandeur(2.0, D.SANS), source="b")
st4, val4 = m4.resout_conflit("x", {"a": 0.5, "b": 0.5})   # égalité -> abstention
check("contradiction indécidable -> pas de valeur imposée", val4 is None)
check("verdict avec contradiction non résolue -> HORS", m4.verdict("x", contradiction_non_resolue=True) == HORS)

# ── FAUX=0 : une dérivation impossible (params manquants) ne fabrique rien ────────────────
m5 = MoteurRaisonnement()
m5.observe("T_froid", Grandeur.depuis(295, "K"), source="s")
check("dérivation avec paramètre manquant -> None (rien posé)",
      m5.derive("COP_max", carnot, "COP", {"T_froid": "T_froid", "T_chaud": "T_chaud"}) is None)
check("verdict sans preuve -> ABSTENTION", m5.verdict("COP_max") == ABSTENTION)

print(f"\n=== valide_moteur_raisonnement : {ok}/{total} checks OK ===")
if ok != total:
    raise SystemExit(1)
