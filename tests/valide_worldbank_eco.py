"""VALIDE l'ingestion éco/social Banque mondiale (6 relations) + les ponts ia.* — ADVERSE, FAUX=0.

Relations jugées : pib_pays, pib_par_habitant_pays, taux_chomage_pays, taux_inflation_pays, esperance_vie_pays,
indice_gini_pays. Ancres EXTERNES non circulaires en FOURCHETTES LARGES (valeurs volatiles, millésime tracé dans
la source) : France/Japon/Inde/Afrique du Sud, ordres de bon sens (USA > France en PIB, Japon < France en chômage,
Afrique du Sud = Gini le plus élevé). COHÉRENCE CROISÉE : PIB/hab dérivé (pib.py sur pib/population) ≈ PIB/hab
direct (tolérance large : millésimes différents). Soundness : pays inconnu -> None (HORS), jamais deviné."""
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


# ── ancres externes en fourchettes larges (via les vrais chemins ia.*) ──
ANCRES = {
    # relation -> {pays: (min, max)}
    "pib_pays": {"France": (2.2e12, 4.0e12), "Etats-Unis": (2.0e13, 4.0e13), "Inde": (2.5e12, 6.5e12)},
    "pib_par_habitant_pays": {"France": (30_000, 65_000), "Inde": (1_500, 5_000), "Japon": (25_000, 55_000)},
    "taux_chomage_pays": {"France": (4.5, 13.0), "Japon": (1.0, 5.0)},
    "taux_inflation_pays": {"France": (-2.0, 9.0), "Japon": (-2.5, 9.0)},
    "esperance_vie_pays": {"France": (80.0, 87.0), "Japon": (82.0, 89.0), "Nigeria": (48.0, 66.0)},
    # NB Gini : la Banque mondiale a RÉVISÉ la série (ZAF 63,0/2014 -> 54,1/2022, nouvelle méthodologie) — l'ancre
    # suit la source vivante ; l'invariant stable = Afrique du Sud parmi les plus hauts du monde et > France.
    "indice_gini_pays": {"France": (25.0, 38.0), "Afrique du Sud": (45.0, 70.0)},
}
PONTS = {
    "pib_pays": ia.pib_pays, "pib_par_habitant_pays": ia.pib_par_habitant_pays,
    "taux_chomage_pays": ia.taux_chomage_pays, "taux_inflation_pays": ia.taux_inflation_pays,
    "esperance_vie_pays": ia.esperance_vie_pays, "indice_gini_pays": ia.indice_gini_pays,
}
for rel, ancres in ANCRES.items():
    pont = PONTS[rel]
    for nom, (lo, hi) in ancres.items():
        v = pont(nom)
        check(v is not None, f"{rel} : {nom} présent (pont ia)")
        if v is not None:
            check(lo <= v <= hi, f"{rel} : {nom} = {v} dans [{lo}, {hi}]")

# ── ordres de bon sens (stables depuis des décennies) ──
_maroc = ia.pib_pays("Maroc")
if _maroc is not None:
    check((ia.pib_pays("Etats-Unis") or 0) > (ia.pib_pays("France") or 0) > _maroc,
          "ordre PIB : Etats-Unis > France > Maroc")
else:
    check((ia.pib_pays("Etats-Unis") or 0) > (ia.pib_pays("France") or 0), "ordre PIB : Etats-Unis > France")
check((ia.taux_chomage_pays("France") or 0) > (ia.taux_chomage_pays("Japon") or 99),
      "ordre chômage : France > Japon")
check((ia.esperance_vie_pays("Japon") or 0) > (ia.esperance_vie_pays("Nigeria") or 999),
      "ordre espérance de vie : Japon > Nigeria")
check((ia.indice_gini_pays("Afrique du Sud") or 0) > (ia.indice_gini_pays("France") or 999),
      "ordre Gini : Afrique du Sud > France")
check((ia.pib_par_habitant_pays("France") or 0) > (ia.pib_par_habitant_pays("Inde") or 1e9),
      "ordre PIB/hab : France > Inde")

# ── COHÉRENCE CROISÉE : moteur pib.py RÉVEILLÉ — dérivé ≈ direct (millésimes différents -> tolérance 35 %) ──
for nom in ("France", "Japon", "Inde"):
    direct = ia.pib_par_habitant_pays(nom)
    derive = ia.pib_par_habitant_calcule(nom)
    check(derive is not None, f"PIB/hab DÉRIVÉ (pib.py sur pib/population) calculable pour {nom}")
    if direct and derive:
        check(abs(derive - direct) / direct < 0.35,
              f"cohérence croisée {nom} : dérivé {derive:.0f} ≈ direct {direct:.0f} (<35 %)")

# ── SOUNDNESS : inconnu -> None (HORS), jamais deviné ──
for rel, pont in PONTS.items():
    check(pont("Pays-Qui-N-Existe-Pas-42") is None, f"{rel} : pays inconnu -> None (HORS)")
check(ia.pib_pays("") is None, "nom vide -> None (HORS)")
check(ia.pib_par_habitant_calcule("Pays-Qui-N-Existe-Pas-42") is None, "dérivé : pays inconnu -> None")

# ── bulk : les 6 tables saines (relues directement, indépendamment des ponts) ──
DOSSIER = os.path.join(os.path.dirname(__file__), "datasets", "lecteur")
BORNES_BULK = {
    "pib_pays": (150, 1e6, 5e13),                      # (min pays, val min, val max) — Tuvalu ~6e7… borne basse laxiste
    "pib_par_habitant_pays": (150, 100, 300_000),      # Burundi ~230 ; Monaco/Liechtenstein ~200k
    "taux_chomage_pays": (150, 0.0, 45.0),
    "taux_inflation_pays": (140, -30.0, 1500.0),       # déflations & hyperinflations réelles
    "esperance_vie_pays": (180, 45.0, 90.0),
    "indice_gini_pays": (100, 20.0, 70.0),
}
pop_keys = set()
for ligne in open(os.path.join(DOSSIER, "population_pays.jsonl"), encoding="utf-8"):
    o = json.loads(ligne)
    if "entite" in o:
        pop_keys.add(o["entite"])
for rel, (nmin, vmin, vmax) in BORNES_BULK.items():
    table = {}
    for ligne in open(os.path.join(DOSSIER, rel + ".jsonl"), encoding="utf-8"):
        o = json.loads(ligne)
        if "entite" in o:
            table[o["entite"]] = o["valeur"]
    check(len(table) >= nmin, f"{rel} peuplée ({len(table)} pays >= {nmin})")
    try:
        vals = [float(v) for v in table.values()]
        check(all(vmin <= v <= vmax for v in vals),
              f"{rel} : toutes les valeurs dans [{vmin}, {vmax}] "
              f"(contre-ex : {[v for v in vals if not (vmin <= v <= vmax)][:3]})")
    except ValueError:
        check(False, f"{rel} : toutes les valeurs sont des nombres")
    communs = sum(1 for n in table if n in pop_keys)
    check(communs >= min(nmin, len(table)) * 0.8, f"{rel} : clés alignées sur population_pays ({communs} communs)")

print(f"\n=== valide_worldbank_eco : {ok}/{ok + ko} ===")
import sys

sys.exit(0 if ko == 0 else 1)
