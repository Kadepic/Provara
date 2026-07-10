"""
VALIDE O*NET Interests — le cliquet de l'axe « profil d'intérêt dominant (RIASEC) » (part US, MIX).

CE QU'IL GARDE — le point sensible est l'ARGMAX (pas un seuil) :
  • le dominant est le high-point = argmax des 6 scores RIASEC ; DÉTERMINISTE, jamais un seuil arbitraire ;
  • les EX-AEQUO sont tous listés, triés (aucun choix arbitraire entre deux maxima) ;
  • seul le scale OI (Occupational Interests) est lu ; les autres scales sont ignorées ;
  • la troncature O*NET-SOC ; granularité dite ; None si aucun profil (métier NON TRAITÉ, pas de vide).

ANCRE NON CIRCULAIRE : un métier de bibliothèque a pour intérêt dominant « Conventional » (données O*NET,
connu indépendamment). Sabotages nommant le remède.
"""
import os
import sys
import tempfile
import zipfile

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "ingestion"))
import ingere_onet_interets as I

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


_tmp = tempfile.mkdtemp(prefix="verax_int_")

# ── 1) L'ARGMAX : dominant = high-point, ex-aequo listés, autres scales ignorées ─────────────────────
_f = os.path.join(_tmp, "int.xlsx")
_H = ["O*NET-SOC Code", "Title", "Element ID", "Element Name", "Scale ID", "Scale Name", "Data Value"]
_rows = [_H]
# SOC 15-2011 : Investigative max (5.0) -> dominant unique
for el, sc in [("Realistic", "2.0"), ("Investigative", "5.0"), ("Artistic", "1.0"),
               ("Social", "3.0"), ("Enterprising", "4.0"), ("Conventional", "4.5")]:
    _rows.append(["15-2011.00", "Actuaries", "x", el, "OI", "Occupational Interests", sc])
# une ligne AUTRE scale (à ignorer, valeur haute qui piégerait un parseur naïf)
_rows.append(["15-2011.00", "Actuaries", "x", "Investigative", "IH", "Interest High-Point", "99"])
# SOC 43-4121 : ex-aequo Conventional & Enterprising (tous deux 6.0)
for el, sc in [("Realistic", "1.0"), ("Investigative", "2.0"), ("Artistic", "1.0"),
               ("Social", "3.0"), ("Enterprising", "6.0"), ("Conventional", "6.0")]:
    _rows.append(["43-4121.00", "Library clerks", "x", el, "OI", "Occupational Interests", sc])
# code non conforme -> écarté
_rows.append(["All", "bruit", "x", "Social", "OI", "Occupational Interests", "9"])
_xlsx(_f, _rows)
dom = I.dominant_par_soc(_f)
check(dom.get("15-2011") == ("Investigative",),
      "argmax unique : Investigative (5.0) ; le scale IH=99 est IGNORÉ (mesuré : %r)" % (dom.get("15-2011"),))
check(dom.get("43-4121") == ("Conventional", "Enterprising"),
      "ex-aequo (6.0/6.0) : les DEUX listés, triés (mesuré : %r)" % (dom.get("43-4121"),))
check("All" not in dom and len(dom) == 2, "code non conforme écarté")

# ── 2) LA VALEUR : granularité dite, None si vide ────────────────────────────────────────────────────
v = I.valeur_interet("2120", ["15-2011", "43-4121"], dom)
check(v.startswith("groupe ISCO-08 2120"), "la valeur commence par le GROUPE : granularité dite")
check("argmax déterministe des scores, sans seuil" in v, "la valeur DIT que c'est l'argmax, pas un seuil")
check("15-2011 → Investigative" in v and "43-4121 → Conventional, Enterprising" in v,
      "chaque SOC du groupe → son/ses intérêt(s) dominant(s)")
check(I.valeur_interet("0110", ["55-1011"], dom) is None,
      "aucun profil dans le groupe -> None : le métier reste NON TRAITÉ")

# ── 3) SABOTAGE ──────────────────────────────────────────────────────────────────────────────────────
try:
    I.dominant_par_soc("/nonexistent/int.xlsx")
    check(False, "cache absent doit lever SystemExit")
except SystemExit as e:
    check("moissonne" in str(e), "SystemExit NOMME la commande de remoissonnage")

_bad = os.path.join(_tmp, "bad.xlsx")
_xlsx(_bad, [["Colonne inconnue", "Autre"], ["a", "b"]])
try:
    I.dominant_par_soc(_bad)
    check(False, "colonnes renommées doivent lever SystemExit")
except SystemExit as e:
    check("format O*NET" in str(e), "SystemExit dit que le format a changé")

print("=== valide_onet_interets : %d ok, %d ko ===" % (ok, ko))
sys.exit(1 if ko else 0)
