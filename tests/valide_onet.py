"""
VALIDE O*NET — le cliquet de l'axe « outils, machines et logiciels » (part codifiée US, MIX).

CE QU'IL GARDE. L'axe avait déjà produit UN faux (P2283, « soliste -> solo », table supprimée). Les faux
de cette chaîne naissent à :

  • la TRONCATURE : « 11-1011.00 » -> « 11-1011 » (SOC 2018) ; un code non conforme ne doit JAMAIS être
    deviné ;
  • la GRANULARITÉ : les catégories sont celles du GROUPE ISCO (via ses occupations SOC), pas du métier —
    la valeur doit le DIRE ;
  • l'EXHAUSTIVITÉ à granularité dite : catégories dédoublonnées, JAMAIS un extrait ; un groupe sans
    recensement O*NET rend None (le métier reste NON TRAITÉ, pas de valeur vide).

ANCRES NON CIRCULAIRES : la fixture est écrite à la main ; les maillons ISCO->SOC sont ceux
d'`ingere_bls_oes`, gardés par `valide_bls_oes` (une seule définition de la chaîne dans le projet).

CONTRE-ÉPREUVE DE SABOTAGE. Cache absent -> SystemExit qui NOMME la commande de remoissonnage ;
colonnes renommées par O*NET -> SystemExit qui nomme le fichier.
"""
import os
import sys
import tempfile
import zipfile

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "ingestion"))
import ingere_onet as O

ok = 0
ko = 0


def check(cond, label):
    global ok, ko
    if cond:
        ok += 1
    else:
        ko += 1
        print(f"  FAIL: {label}")


# ── 1) LA VALEUR : granularité dite, dédoublonnée, None si vide ──────────────────────────────────────
OUTILS = {"15-2011": {"Desktop calculator", "Personal computers"},
          "15-2021": {"Personal computers", "Interactive whiteboard"}}
TECHS = {"15-2011": {"Financial analysis software"}}
v = O.valeur_onet("2120", ["15-2011", "15-2021"], OUTILS, TECHS)
check(v.startswith("groupe ISCO-08 2120"), "la valeur commence par le GROUPE : granularité dite")
check("pas le métier précis" in v, "la valeur dit explicitement que ce n'est pas le métier précis")
check(v.count("Personal computers") == 1, "dédoublonnage à l'échelle du groupe")
check("Interactive whiteboard" in v and "Desktop calculator" in v,
      "EXHAUSTIF à granularité dite : les catégories des DEUX occupations sont là")
check("OUTILS :" in v and "TECHNOLOGIES :" in v, "outils et technologies distingués")
check(O.valeur_onet("0110", ["55-1011"], OUTILS, TECHS) is None,
      "groupe sans recensement -> None : le métier reste NON TRAITÉ")

# ── 2) LA TRONCATURE : codes O*NET-SOC -> SOC 2018, bruit jamais deviné ──────────────────────────────
def _xlsx(chemin, lignes):
    """Écrit un xlsx MINIMAL (inline strings) lisible par lit_xlsx — fixture autoportante."""
    feuille = ['<?xml version="1.0"?><worksheet xmlns='
               '"http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData>']
    for i, cells in enumerate(lignes, 1):
        feuille.append("<row r='%d'>" % i)
        for j, val in enumerate(cells):
            feuille.append("<c r='%s%d' t='inlineStr'><is><t>%s</t></is></c>" % (chr(65 + j), i, val))
        feuille.append("</row>")
    feuille.append("</sheetData></worksheet>")
    with zipfile.ZipFile(chemin, "w") as z:
        z.writestr("xl/worksheets/sheet1.xml", "".join(feuille))

_tmp = tempfile.mkdtemp(prefix="verax_onet_")
_fx = os.path.join(_tmp, "tools.xlsx")
_xlsx(_fx, [
    ["O*NET-SOC Code", "Title", "Example", "Commodity Code", "Commodity Title"],
    ["15-2011.00", "Actuaries", "10-key calculators", "44101809", "Desktop calculator"],
    ["15-2011.01", "Variante détaillée", "x", "1", "Notebook computers"],   # .01 -> même SOC 15-2011
    ["All occupations", "bruit", "y", "2", "Pas un code"],                  # ne se tronque pas -> tombe
    ["15-2021.00", "Mathematicians", "z", "3", ""],                        # catégorie vide -> tombe
])
t = O.categories_par_soc(_fx)
check(t == {"15-2011": {"Desktop calculator", "Notebook computers"}},
      "troncature .yy -> SOC 6 chiffres, variantes détaillées fusionnées, bruit et vides écartés")

# ── 3) SABOTAGE ──────────────────────────────────────────────────────────────────────────────────────
try:
    O.categories_par_soc("/nonexistent/onet.xlsx")
    check(False, "cache absent doit lever SystemExit")
except SystemExit as e:
    check("moissonne" in str(e), "SystemExit NOMME la commande de remoissonnage")

_fx2 = os.path.join(_tmp, "renomme.xlsx")
_xlsx(_fx2, [["Colonne inconnue", "Autre"], ["a", "b"]])
try:
    O.categories_par_soc(_fx2)
    check(False, "colonnes renommées doivent lever SystemExit")
except SystemExit as e:
    check("format O*NET a changé" in str(e), "SystemExit dit que le format a changé")

print("=== valide_onet : %d ok, %d ko ===" % (ok, ko))
sys.exit(1 if ko else 0)
