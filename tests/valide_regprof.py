"""
VALIDE REGPROF — le cliquet de l'axe « normes, réglementation » (réglementation d'accès, part MIX).

CE QU'IL GARDE. Les faux naissent à TROIS endroits :

  • la PARENTHÈSE : « Infirmier(ère) » est un suffixe de genre à déplier ; « Architecte (droits acquis) »
    est un QUALIFICATIF restrictif — le déplier donnerait à « architecte » une entrée à périmètre réduit ;
  • l'ALIGNEMENT : une forme sous deux entrées, ou un métier atteignant deux entrées, doit TOMBER ;
  • le MONDE CLOS INVENTÉ : REGPROF n'est PAS exhaustif (« notaire », réglementé, est hors champ de la
    directive 2005/36/CE) — l'absence ne doit JAMAIS produire un fait « non réglementé ».

ANCRES NON CIRCULAIRES. La fixture est écrite à la main ; « Avocat » figure dans REGPROF France (publié par
la Commission), « notaire » n'y figure pas (exclusion du champ de la directive, considérant 41 de la
directive 2005/36/CE) : les deux sont connus indépendamment du code testé.

CONTRE-ÉPREUVE DE SABOTAGE. Cache absent -> SystemExit qui NOMME la commande de remoissonnage.
Et le POURQUOI du rejet du drapeau ROME est documenté ici : `emploi_reglemente` échouait sur deux ancres en
NÉGATIF (architecte N, boulanger N) avec une définition circulaire — un drapeau au sens inénonçable ne
publie rien, même ses positifs.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "ingestion"))
import ingere_regprof as R

ok = 0
ko = 0


def check(cond, label):
    global ok, ko
    if cond:
        ok += 1
    else:
        ko += 1
        print(f"  FAIL: {label}")


# ── 1) PARENTHÈSE : genre collé déplié, qualificatif espacé JAMAIS ────────────────────────────────────
f = R._formes_regprof("Infirmier(ère)")
check("infirmier" in f, "parenthèse de genre COLLÉE dépliée : « Infirmier(ère) » -> « infirmier »")
check("infirmier(ère)" in f, "la forme entière est conservée")

f = R._formes_regprof("Infirmier(ière) de bloc opératoire")
check("infirmier de bloc opératoire" in f, "genre collé en milieu de libellé déplié")

f = R._formes_regprof("Architecte (droits acquis)")
check(f == {"architecte (droits acquis)"},
      "qualificatif ESPACÉ jamais déplié : « architecte » n'hérite pas d'une entrée à périmètre réduit")

check(R._formes_regprof("") == set(), "libellé vide -> aucune forme")

# ── 2) ALIGNEMENT : gardes d'unicité, et PAS de monde clos ───────────────────────────────────────────
ENTREES = [
    {"name": "Avocat"},
    {"name": "Infirmier(ère)"},
    {"name": "Architecte (droits acquis)"},
    # GARDE 2 : la même forme sous DEUX entrées distinctes
    {"name": "Conseiller(ère)"},
    {"name": "Conseiller"},
]
METIERS = ["avocat", "infirmière ou infirmier", "architecte", "conseiller ou conseillère", "notaire"]
apparie = R.aligne(ENTREES, METIERS)
check(apparie.get("avocat") == "Avocat", "ancre : avocat -> entrée « Avocat » (publiée par la Commission)")
check(apparie.get("infirmière ou infirmier") == "Infirmier(ère)",
      "le doublet métier rejoint l'entrée à parenthèse de genre")
check("architecte" not in apparie,
      "« architecte » ne s'apparie PAS à « Architecte (droits acquis) » (périmètre réduit)")
check("conseiller ou conseillère" not in apparie, "GARDE 2/3 : forme sous deux entrées -> métier rejeté")
check("notaire" not in apparie, "« notaire » hors REGPROF (hors champ de la directive) : non apparié")

# ── 3) LA VALEUR : attribuée, dédoublonnée, régime + niveau ; jamais de négatif ──────────────────────
lignes = [
    {"directive": "General system of recognition - primary application",
     "qualification_level": "Diploma of post-secondary level (3-4 years)", "region": "app.region.none"},
    {"directive": "General system of recognition - primary application",
     "qualification_level": "Diploma of post-secondary level (3-4 years)", "region": None},
]
v = R.valeur_regprof("Avocat", lignes)
check(v.startswith("profession réglementée en France — base REGPROF"),
      "la valeur ATTRIBUE (base REGPROF, directive 2005/36/CE)")
check("entrée « Avocat »" in v, "la valeur cite l'entrée source")
check(v.count("régime") == 1, "les doublons de la source sont dédoublonnés")
check("région" not in v, "région nationale (app.region.none) -> non mentionnée")
v2 = R.valeur_regprof("Guide", [{"directive": "d", "qualification_level": "q", "region": "Savoie"}])
check("région : Savoie" in v2, "une réglementation RÉGIONALE est dite (périmètre honnête)")

# ── 4) SABOTAGE : cache absent -> SystemExit nommant le remède ───────────────────────────────────────
_sauve = R.CACHE
R.CACHE = "/nonexistent/regprof.json"
try:
    R.publie_depuis_cache()
    check(False, "cache absent doit lever SystemExit")
except SystemExit as e:
    check("moissonne" in str(e), "SystemExit NOMME la commande de remoissonnage")
finally:
    R.CACHE = _sauve

print("=== valide_regprof : %d ok, %d ko ===" % (ok, ko))
sys.exit(1 if ko else 0)
