"""
VALIDATION — FORGE_BRIQUE : la SORTIE DE PREMIÈRE CLASSE de la forge (ia.forge_brique, chantier FORGE atome 5).

Le mandat : « le générateur de briques doit servir le moteur d'invention EN SORTIE à l'utilisateur et aux
autres moteurs — rendre tout ça parfait ». Cette façade COMBINE, en une porte, ce que la forge sait dire
d'une brique, CHAQUE affirmation étiquetée par son statut épistémique.

Prouve : (1) une INVENTION rend une sortie COMPLÈTE (code + FAIT borné + SUPPOSITION cadrée + force du spec +
appris) ; (2) SOUNDNESS — le FAIT est certain (confiance 1.0) mais la SUPPOSITION n'est JAMAIS servie comme
un fait (statut SUPPOSITION, confiance < 1) ; (3) EXISTE_DEJA rend le code + le fait, sans supposition ni
mutation ; (4) SELF-IMPROVING — la rétention est idempotente (re-forger la même brique -> appris False, et
elle est désormais reconnue) ; (5) la solidité du besoin est mesurée (force_spec cohérent : score 1.0 <=>
0 survivant <=> pas de besoin_a_renforcer) ; (6) SERVABLE — toute la sortie est JSON-sérialisable (utilisable
par l'utilisateur et par un autre moteur) ; (7) ABSTENTION — un spec incohérent ne rend NI code NI atomes.
"""
from __future__ import annotations

import json
import os

from garde_ressources import borne
borne(max_cpu_s=400)
import ia
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


# ── (1) INVENTION : sortie complète de première classe ──────────────────────────────────────────────────
AMP = ("amplitude", "x", [([3, 1, 5], 4), ([2, 2], 0), ([10, 0, 3], 10)], [([0, 9, 4], 9), ([7], 0), ([5, 5, 1], 4)])
r = ia.forge_brique(*AMP)
check("INVENTION : statut invention", r["statut"] == MI.INVENTION)
check("INVENTION : code = la réalisation", r["code"] and "max(x) - min(x)" in r["code"])
check("INVENTION : FAIT borné rendu (ce qui est CERTAIN)", r["fait_borne"] and r["fait_borne"].startswith("[FAIT]"))
check("INVENTION : SUPPOSITION générative rendue (ce qui est SUPPOSÉ)",
      r["supposition"] and r["supposition"].startswith("[SUPPOSITION(generatif"))
check("INVENTION : force du spec mesurée", isinstance(r["force_spec"], dict) and "score" in r["force_spec"])
check("INVENTION : retenue en mémoire (self-improving)", r["appris"] is True)

# ── (2) SOUNDNESS : le FAIT est certain, la SUPPOSITION ne l'est JAMAIS ──────────────────────────────────
check("le FAIT borné ne porte pas de doute (statut FAIT)", "[FAIT]" in r["fait_borne"])
check("la SUPPOSITION est servie AVEC son statut et une confiance < 1 (jamais comme un fait)",
      "SUPPOSITION" in r["supposition"] and "conf=" in r["supposition"] and "[FAIT]" not in r["supposition"])

# ── (3) EXISTE_DEJA : code + fait, pas de supposition, pas de mutation ───────────────────────────────────
red = ia.forge_brique("somme_simple", "x", [([1, 2, 3], 6), ([5], 5)], [([0, 4], 4), ([2, 2], 4)])
check("EXISTE_DEJA : statut existe_deja", red["statut"] == MI.EXISTE_DEJA)
check("EXISTE_DEJA : code présent + FAIT borné, PAS de supposition (rien de neuf à supposer)",
      red["code"] and red["fait_borne"] and red["supposition"] is None)
check("EXISTE_DEJA : pas de mesure de mutation (on ne mute pas une capacité existante)", red["force_spec"] is None)

# ── (4) SELF-IMPROVING : rétention idempotente + reconnaissance ──────────────────────────────────────────
r2 = ia.forge_brique("amplitude_bis", "x", AMP[2], AMP[3])
check("re-forger une brique déjà apprise -> reconnue EXISTE_DEJA (mémoire persistante en-process)",
      r2["statut"] == MI.EXISTE_DEJA and r2["appris"] is False)

# ── (5) SOLIDITÉ DU BESOIN : force_spec cohérent avec besoin_a_renforcer ─────────────────────────────────
fs = r["force_spec"]
check("cohérence : score 1.0 <=> 0 survivant <=> aucun besoin à renforcer",
      (fs["score"] == 1.0) == (fs["survivants"] == 0) and (r["besoin_a_renforcer"] is None) == (fs["survivants"] == 0))

# ── (6) SERVABLE : toute la sortie est JSON-sérialisable (utilisable par l'utilisateur ET un autre moteur) ─
try:
    json.dumps(r)
    json.dumps(red)
    check("sortie entièrement JSON-sérialisable (première classe, inter-moteurs)", True)
except (TypeError, ValueError):
    check("sortie entièrement JSON-sérialisable (première classe, inter-moteurs)", False)
check("la sortie contient exactement les champs de première classe attendus",
      set(r) == {"statut", "code", "code_refuse", "fait_borne", "supposition",
                 "force_spec", "besoin_a_renforcer", "appris"})
# atome 7 : frontière de service — le code d'une invention pure est audité sûr (code_refuse None).
check("le code servi est audité sûr (code_refuse None pour une invention pure)", r["code_refuse"] is None)

# ── (7) ABSTENTION : un spec incohérent ne rend NI code NI atomes (FAUX=0) ───────────────────────────────
inc = ia.forge_brique("absurde", "x", [([1, 2], 5)], [([1, 2], 9)])
check("INCOHERENT : abstention totale (ni code, ni fait, ni supposition)",
      inc["statut"] == MI.INCOHERENT and inc["code"] is None and inc["fait_borne"] is None and inc["supposition"] is None)

print(f"\nFORGE_BRIQUE VALIDÉ — {ok}/{total}." if ok == total else f"\nÉCHEC {ok}/{total}")
