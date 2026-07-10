"""
VALIDE BLS OES — le cliquet de l'axe « rémunération médiane » (part États-Unis, MIX).

CE QU'IL GARDE. La chaîne métier -> ISCO -> SOC 2010 -> SOC 2018 -> médiane a QUATRE maillons ; les faux
naissent aux jointures et aux valeurs spéciales :

  • la GRANULARITÉ : la médiane est PAR OCCUPATION SOC, jamais « du métier » — la valeur doit le DIRE et
    lister TOUTES les occupations du groupe (un extrait serait un top-N déguisé) ;
  • « # » d'OEWS = « ≥ 239 200 $/an » (plafond de publication) : un FAIT à encoder, jamais un nombre
    inventé, jamais jeté ; « * » = non publié : écarté ET compté ;
  • un métier dont AUCUNE occupation n'a de médiane publiée (militaires, hors champ OEWS) reste NON
    TRAITÉ — pas de valeur vide, pas de zéro inventé.

ANCRES NON CIRCULAIRES. La fixture est écrite à la main. « Actuaries » (SOC 15-2011) appartient au groupe
ISCO 2120 via le crosswalk BLS — publié par le BLS, connu indépendamment du code testé.

CONTRE-ÉPREUVE DE SABOTAGE. Cache absent -> SystemExit qui NOMME la commande de remoissonnage.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "ingestion"))
import ingere_bls_oes as B

ok = 0
ko = 0


def check(cond, label):
    global ok, ko
    if cond:
        ok += 1
    else:
        ko += 1
        print(f"  FAIL: {label}")


# ── 1) LA VALEUR : granularité dite, exhaustive, plafond encodé ──────────────────────────────────────
MED = {
    "15-2011": ("Actuaries", "125 770 $/an"),
    "15-2021": ("Mathematicians", "121 680 $/an"),
    "29-1215": ("Family Medicine Physicians", B.PLAFOND),
    # 15-2099 volontairement ABSENT : médiane « * » non publiée
}
v, ecartees = B.valeur_oes("2120", ["15-2011", "15-2021", "15-2099"], MED)
check(v.startswith("groupe ISCO-08 2120"), "la valeur commence par le GROUPE : la granularité est dite")
check("PAR OCCUPATION SOC, pas par métier précis" in v, "la valeur dit explicitement le niveau de la médiane")
check("15-2011 « Actuaries » : 125 770 $/an" in v, "ancre : Actuaries dans le groupe 2120 (crosswalk BLS)")
check("15-2021" in v, "AUCUN top-N : toutes les occupations à médiane publiée sont listées")
check("1 occupation(s) du groupe sans médiane publiée" in v, "l'occupation « * » est écartée ET COMPTÉE")
check(ecartees == 1, "le compte d'écartées est rendu (mesuré : %d)" % ecartees)

v2, _ = B.valeur_oes("2211", ["29-1215"], MED)
check("≥ 239 200 $/an (plafond de publication BLS)" in v2,
      "« # » devient le FAIT de plafond, jamais un nombre inventé")

v3, e3 = B.valeur_oes("0110", ["55-1011", "55-1012"], MED)
check(v3 is None and e3 == 2,
      "aucune médiane publiée dans le groupe (militaires) -> None : le métier reste NON TRAITÉ")

# ── 2) LES MAILLONS : parsing sous gardes ────────────────────────────────────────────────────────────
# isco_vers_soc2010 ne garde que les lignes « 4 chiffres » -> « xx-xxxx » : les entêtes et notes tombent.
import csv as _csv
import tempfile

_tmp = tempfile.mkdtemp(prefix="verax_oes_")
_cw = os.path.join(_tmp, "xwalk.csv")
with open(_cw, "w", newline="", encoding="utf-8") as f:
    w = _csv.writer(f)
    w.writerow(["Bureau of Labor Statistics", "", "", "", "", ""])            # bruit d'entête
    w.writerow(["ISCO-08 Code", "ISCO-08 Title EN", "part", "2010 SOC Code", "2010 SOC Title", ""])
    w.writerow(["2120", "Mathematicians, actuaries and statisticians", "*", "15-2011 ", "Actuaries", ""])
    w.writerow(["2120", "Mathematicians, actuaries and statisticians", "*", "15-2021 ", "Mathematicians", ""])
    w.writerow(["notes diverses", "", "", "pas un code", "", ""])             # bruit de queue
_sauve = B.CACHE_XWALK_CSV
B.CACHE_XWALK_CSV = _cw
t = B.isco_vers_soc2010()
B.CACHE_XWALK_CSV = _sauve
check(t == {"2120": {"15-2011", "15-2021"}},
      "le parseur du crosswalk ne retient que code ISCO 4 chiffres -> code SOC xx-xxxx (bruit ignoré)")

# ── 3) SABOTAGE : cache absent -> SystemExit nommant le remède ───────────────────────────────────────
B.CACHE_XWALK_CSV = "/nonexistent/xwalk.csv"
try:
    B.isco_vers_soc2010()
    check(False, "cache absent doit lever SystemExit")
except SystemExit as e:
    check("moissonne" in str(e), "SystemExit NOMME la commande de remoissonnage")
finally:
    B.CACHE_XWALK_CSV = _sauve

print("=== valide_bls_oes : %d ok, %d ko ===" % (ok, ko))
sys.exit(1 if ko else 0)
