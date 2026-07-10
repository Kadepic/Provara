"""
VALIDE BLS SOII — le cliquet de l'axe « risques professionnels » (part mesurée US, MIX).

CE QU'IL GARDE. Les faux de cette table naissent à :

  • les EN-TÊTES à deux étages : les colonnes « Total » de chaque famille d'événements sont DÉRIVÉES des
    deux rangées, jamais des lettres codées en dur (le BLS peut insérer une colonne) ;
  • les AGRÉGATS : « 11-0000 » (groupe majeur) n'est pas une occupation — publier son taux pour un métier
    serait une moyenne déguisée ; seuls les codes détaillés (dernier chiffre non nul) passent ;
  • le TYPE DE CAS : DAFW (arrêt de travail) est publié et DIT ; DART/DJTR tombent ;
  • les FLOTTANTS xlsx : « 4.0999999999999996 » EST le « 4.1 » publié — reformé, jamais renchéri ;
    « - » (non publié) reste VERBATIM.

ANCRES NON CIRCULAIRES. Fixture écrite à la main ; granularité groupe ISCO dite dans la valeur.
CONTRE-ÉPREUVE DE SABOTAGE. Cache absent / titre inattendu -> SystemExit nommant le remède.
"""
import os
import sys
import tempfile
import zipfile

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "ingestion"))
import ingere_bls_soii as R

ok = 0
ko = 0


def check(cond, label):
    global ok, ko
    if cond:
        ok += 1
    else:
        ko += 1
        print(f"  FAIL: {label}")


# ── 1) LES TAUX : flottant binaire reformé, non publié verbatim ──────────────────────────────────────
check(R._taux("4.0999999999999996") == "4.1", "flottant xlsx reformé au dixième publié")
check(R._taux("86.6") == "86.6", "taux propre inchangé")
check(R._taux("-") == "-", "« - » (non publié) reste verbatim")
check(R._taux("") == "", "vide reste vide")

# ── 2) LES COLONNES DE FAMILLES : dérivées des deux rangées d'en-tête ────────────────────────────────
r1 = {"A": "Occupation(1)", "B": "Occupation code(2)", "C": "Case type(3)", "D": "Total rate",
      "E": "Contact incidents", "F": "Contact incidents", "G": "Falls, slips, trips",
      "H": "Falls, slips, trips", "I": "Explosions and fires", "J": "Violent acts",
      "K": "All other events or exposures(4)"}
r2 = {"A": "", "B": "", "C": "", "D": "Total rate", "E": "Total", "F": "Struck by…",
      "G": "Total", "H": "Fall to lower level", "I": "Explosions and fires", "J": "Violent acts",
      "K": "All other events or exposures(4)"}
cols = R.colonnes_familles(r1, r2)
check(cols == [("D", "Total rate"), ("E", "Contact incidents"), ("G", "Falls, slips, trips"),
               ("I", "Explosions and fires"), ("J", "Violent acts"),
               ("K", "All other events or exposures(4)")],
      "les « Total » de chaque famille + les familles mono-colonne, jamais les sous-détails (mesuré : %r)"
      % (cols,))

# ── 3) LE PARSEUR : agrégats et autres types de cas tombent ──────────────────────────────────────────
def _xlsx(chemin, lignes):
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

_tmp = tempfile.mkdtemp(prefix="verax_soii_")
_fx = os.path.join(_tmp, "r100.xlsx")
_xlsx(_fx, [
    ["TABLE R100. Annualized incidence rates…", "", "", "", "", "", "", "", "", "", ""],
    list(r1[c] for c in "ABCDEFGHIJK"),
    list(r2[c] for c in "ABCDEFGHIJK"),
    ["All occupations", "", "DAFW", "86.6", "23.6", "1.9", "22.6", "4.1", "0.1", "2.6", "0.9"],   # sans code
    ["Management occupations", "11-0000", "DAFW", "19.8", "2.7", "0.5", "6", "1", "0", "1", "0"],  # agrégat
    ["Bakers", "51-3011", "DAFW", "105.3", "30.4", "2", "22.0999999999999996", "4", "-", "1.2", "0.3"],
    ["Bakers", "51-3011", "DART", "150.1", "40", "3", "30", "5", "0", "2", "1"],                  # DART
])
taux, titre = R.taux_par_soc(_fx)
check(list(taux) == ["51-3011"], "seuls les codes DÉTAILLÉS en DAFW passent (agrégats, sans-code, DART tombent)")
check(taux["51-3011"][0] == "Bakers", "le titre de l'occupation est repris")
check(("Falls, slips, trips", "22.1") in taux["51-3011"][1], "sous-flottant reformé DANS la ligne")
check(("Explosions and fires", "-") in taux["51-3011"][1], "« - » conservé dans la ligne")

# ── 4) LA VALEUR : granularité dite, None si groupe absent ───────────────────────────────────────────
v = R.valeur_soii("7512", ["51-3011"], taux)
check(v.startswith("groupe ISCO-08 7512"), "la valeur commence par le GROUPE : granularité dite")
check("cas avec arrêt de travail — DAFW" in v, "le type de cas publié est DIT")
check("51-3011 « Bakers » : Total rate 105.3" in v, "ancre : Bakers et son taux total")
check(R.valeur_soii("0110", ["55-1011"], taux) is None,
      "groupe absent de R100 -> None : le métier reste NON TRAITÉ")

# ── 5) SABOTAGE ──────────────────────────────────────────────────────────────────────────────────────
try:
    R.taux_par_soc("/nonexistent/r100.xlsx")
    check(False, "cache absent doit lever SystemExit")
except SystemExit as e:
    check("moissonne" in str(e), "SystemExit NOMME la commande de remoissonnage")

_fx2 = os.path.join(_tmp, "autre.xlsx")
_xlsx(_fx2, [["TABLE R42. Autre chose", "", ""], ["a", "b", "c"], ["d", "e", "f"]])
try:
    R.taux_par_soc(_fx2)
    check(False, "titre inattendu doit lever SystemExit")
except SystemExit as e:
    check("format SOII a changé" in str(e), "SystemExit dit que le format a changé")

print("=== valide_bls_soii : %d ok, %d ko ===" % (ok, ko))
sys.exit(1 if ko else 0)
