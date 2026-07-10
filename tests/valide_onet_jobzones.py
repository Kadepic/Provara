"""
VALIDE O*NET Job Zones — le cliquet de l'axe « niveau de préparation requise » (part US, MIX).

CE QU'IL GARDE :
  • la TRONCATURE O*NET-SOC (« 11-1011.00 » -> « 11-1011 ») ; un code non conforme n'est jamais deviné ;
  • le référentiel des 5 niveaux (1 peu → 5 extensive) : exactement 5, libellés nettoyés du préfixe ;
  • la GRANULARITÉ dite (groupe ISCO, pas le métier), niveaux dédoublonnés et triés, JAMAIS un top-N ;
  • None si aucune occupation du groupe n'a de Job Zone (le métier reste NON TRAITÉ, pas de valeur vide).

ANCRE NON CIRCULAIRE : « actuaire » (groupe 2120) requiert une préparation de niveau 4-5 (considérable à
extensive) — cohérent avec le métier, connu indépendamment du code testé. Maillons ISCO→SOC gardés par
`valide_bls_oes`. Sabotages nommant le remède.
"""
import os
import sys
import tempfile
import zipfile

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "ingestion"))
import ingere_onet_jobzones as J

ok = 0
ko = 0


def check(cond, label):
    global ok, ko
    if cond:
        ok += 1
    else:
        ko += 1
        print(f"  FAIL: {label}")


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


_tmp = tempfile.mkdtemp(prefix="verax_jz_")

# ── 1) LE RÉFÉRENTIEL : 5 niveaux, préfixe nettoyé ───────────────────────────────────────────────────
_ref = os.path.join(_tmp, "ref.xlsx")
_xlsx(_ref, [["Job Zone", "Name", "Experience"],
             ["1", "Job Zone One: Little or No Preparation Needed", "x"],
             ["2", "Job Zone Two: Some Preparation Needed", "x"],
             ["3", "Job Zone Three: Medium Preparation Needed", "x"],
             ["4", "Job Zone Four: Considerable Preparation Needed", "x"],
             ["5", "Job Zone Five: Extensive Preparation Needed", "x"]])
_saveref = J.CACHE_JZREF
J.CACHE_JZREF = _ref
ref = J.reference()
J.CACHE_JZREF = _saveref
check(len(ref) == 5, "le référentiel porte exactement 5 niveaux")
check(ref["1"] == "Little or No Preparation Needed", "le préfixe « Job Zone One: » est retiré")
check(ref["5"] == "Extensive Preparation Needed", "niveau 5 = préparation extensive")

# ── 2) LE PARSE : troncature O*NET-SOC, valeurs hors 1-5 écartées ────────────────────────────────────
_jz = os.path.join(_tmp, "jz.xlsx")
_xlsx(_jz, [["O*NET-SOC Code", "Title", "Job Zone", "Date", "Domain Source"],
            ["15-2011.00", "Actuaries", "4", "08/2023", "Analyst"],
            ["15-2011.03", "Variante détaillée", "5", "08/2023", "Analyst"],   # .03 -> même SOC, autre zone
            ["15-2011.00", "Actuaries", "9", "x", "x"],                        # 9 hors 1-5 -> écarté
            ["All occ", "bruit", "3", "x", "x"]])                              # code non conforme -> écarté
t = J.zones_par_soc(_jz)
check(t == {"15-2011": {"4", "5"}}, "troncature .yy -> SOC, zones 1-5 seulement, bruit écarté (mesuré : %r)" % (t,))

# ── 3) LA VALEUR : granularité dite, dédoublonnée, None si vide ──────────────────────────────────────
v = J.valeur_jobzone("2120", ["15-2011"], {"15-2011": {"4", "5"}}, ref)
check(v.startswith("groupe ISCO-08 2120"), "la valeur commence par le GROUPE : granularité dite")
check("pas le métier précis" in v, "la valeur dit explicitement que ce n'est pas le métier précis")
check("niveau 4 (Considerable Preparation Needed)" in v and "niveau 5 (Extensive Preparation Needed)" in v,
      "ANCRE : actuaire (2120) -> niveaux 4 et 5, avec libellé du référentiel")
check(v.index("niveau 4") < v.index("niveau 5"), "niveaux triés")
check(J.valeur_jobzone("0110", ["55-1011"], {}, ref) is None,
      "aucune Job Zone dans le groupe -> None : le métier reste NON TRAITÉ")

# ── 4) SABOTAGE ──────────────────────────────────────────────────────────────────────────────────────
try:
    J.zones_par_soc("/nonexistent/jz.xlsx")
    check(False, "cache absent doit lever SystemExit")
except SystemExit as e:
    check("moissonne" in str(e), "SystemExit NOMME la commande de remoissonnage")

_bad = os.path.join(_tmp, "bad.xlsx")
_xlsx(_bad, [["Colonne inconnue", "Autre"], ["a", "b"]])
try:
    J.zones_par_soc(_bad)
    check(False, "colonnes renommées doivent lever SystemExit")
except SystemExit as e:
    check("format O*NET" in str(e), "SystemExit dit que le format a changé")

print("=== valide_onet_jobzones : %d ok, %d ko ===" % (ok, ko))
sys.exit(1 if ko else 0)
