"""
VALIDE systemes_politiques.py — held-out ADVERSE.

ANCRES CONNUES (théorie classique des régimes ; aucune n'est recalculée par le module) :
  • democratie -> souveraineté du « peuple » (dêmos/kratos).
  • monarchie  -> pouvoir d'un seul, à titre « héréditaire ».
  • republique -> fonction de chef de l'État « élective », res publica.
  • oligarchie -> « petit groupe » (oligos/arkhê).
  • theocratie -> autorité émanant de « Dieu ».
  • anarchie   -> « absence » de « gouvernement ».
  • dictature  -> pouvoir « absolu ».
  • Critères : héréditaire+un seul = monarchie ; suffrage universel = démocratie ; petit groupe = oligarchie ;
    un seul non héréditaire sans suffrage = dictature.
  • Montesquieu : 3 pouvoirs = exécutif / législatif / judiciaire.
SOUNDNESS : système/pouvoir/suffrage hors référentiel, type invalide, combinaison non déterminée -> ValueError.
DÉTERMINISME : double appel identique.
"""
import systemes_politiques as M

ok = 0
ko = 0


def check(cond, label):
    global ok, ko
    if cond:
        ok += 1
    else:
        ko += 1
        print(f"  FAIL: {label}")


def leve(fn, *args):
    try:
        fn(*args)
        return False
    except ValueError:
        return True
    except Exception:
        return False


# ── 1) DÉFINITIONS : ancres lexicales établies présentes ──
check("peuple" in M.definition("democratie"), "democratie -> 'peuple'")
check("héréditaire" in M.definition("monarchie"), "monarchie -> 'héréditaire'")
check("une seule personne" in M.definition("monarchie"), "monarchie -> 'une seule personne'")
check("élective" in M.definition("republique"), "republique -> 'élective'")
check("res publica" in M.definition("republique"), "republique -> 'res publica'")
check("petit groupe" in M.definition("oligarchie"), "oligarchie -> 'petit groupe'")
check("Dieu" in M.definition("theocratie"), "theocratie -> 'Dieu'")
check("absence" in M.definition("anarchie") and "gouvernement" in M.definition("anarchie"),
      "anarchie -> 'absence' + 'gouvernement'")
check("absolu" in M.definition("dictature"), "dictature -> 'absolu'")

# ── 2) RÉFÉRENTIEL : les 7 systèmes attendus, déterminisme ──
check(M.systemes() == ("anarchie", "democratie", "dictature", "monarchie", "oligarchie", "republique", "theocratie"),
      "systemes() = les 7 régimes triés")
check(len(M.systemes()) == 7, "7 systèmes au référentiel")
for s in M.systemes():
    check(isinstance(M.definition(s), str) and len(M.definition(s)) > 20, f"définition non vide pour {s}")

# ── 3) ROBUSTESSE accents/casse : lookup insensible ──
check(M.definition("Démocratie") == M.definition("democratie"), "accents/casse : Démocratie = democratie")
check(M.definition("  THÉOCRATIE  ") == M.definition("theocratie"), "espaces+casse+accents : THÉOCRATIE")
check(M.definition("République") == M.definition("republique"), "République = republique")

# ── 4) CLASSIFICATION PAR CRITÈRES — cas établis ──
check(M.classe_par_criteres(1, True, "aucun") == "monarchie", "héréditaire+un seul -> monarchie")
check(M.classe_par_criteres(1, True, "universel") == "monarchie", "monarchie constitutionnelle (héréditaire prioritaire)")
check(M.classe_par_criteres(500, False, "universel") == "democratie", "suffrage universel -> democratie")
check(M.classe_par_criteres(1, False, "universel") == "democratie", "chef élu au suffrage universel -> democratie")
check(M.classe_par_criteres(3, False, "restreint") == "oligarchie", "petit groupe non universel -> oligarchie")
check(M.classe_par_criteres(10, False, "aucun") == "oligarchie", "petit groupe (10) -> oligarchie")
check(M.classe_par_criteres(2, False, "restreint") == "oligarchie", "groupe de 2 -> oligarchie")
check(M.classe_par_criteres(1, False, "aucun") == "dictature", "un seul, non héréditaire, sans suffrage -> dictature")

# ── 5) SÉPARATION DES POUVOIRS (Montesquieu) — 3 pouvoirs ──
check(M.separation_pouvoirs() == ("executif", "legislatif", "judiciaire"), "3 pouvoirs ordonnés (Montesquieu)")
check(len(M.separation_pouvoirs()) == 3, "exactement 3 pouvoirs")
check(len(set(M.separation_pouvoirs())) == 3, "3 pouvoirs distincts")
check("lois" in M.attribution_pouvoir("legislatif"), "législatif -> vote des lois")
check("exécuter" in M.attribution_pouvoir("executif"), "exécutif -> exécution des lois")
check("litiges" in M.attribution_pouvoir("judiciaire"), "judiciaire -> tranche les litiges")
check(M.attribution_pouvoir("Législatif") == M.attribution_pouvoir("legislatif"), "attribution accents/casse")

# ── 6) SOUNDNESS — definition hors référentiel / type invalide ──
check(leve(M.definition, "feodalisme"), "feodalisme hors référentiel -> ValueError")
check(leve(M.definition, "ploutocratie"), "ploutocratie hors référentiel -> ValueError")
check(leve(M.definition, "aristocratie"), "aristocratie hors référentiel -> ValueError")
check(leve(M.definition, ""), "chaîne vide -> ValueError")
check(leve(M.definition, "   "), "espaces seuls -> ValueError")
check(leve(M.definition, 123), "definition(int) -> ValueError")
check(leve(M.definition, None), "definition(None) -> ValueError")

# ── 7) SOUNDNESS — classe_par_criteres : types/valeurs invalides ──
check(leve(M.classe_par_criteres, 0, False, "universel"), "nb=0 -> ValueError")
check(leve(M.classe_par_criteres, -3, False, "universel"), "nb<0 -> ValueError")
check(leve(M.classe_par_criteres, True, False, "universel"), "nb booléen -> ValueError")
check(leve(M.classe_par_criteres, 1.0, False, "universel"), "nb float -> ValueError")
check(leve(M.classe_par_criteres, "1", False, "universel"), "nb str -> ValueError")
check(leve(M.classe_par_criteres, 1, 1, "universel"), "est_hereditaire non booléen -> ValueError")
check(leve(M.classe_par_criteres, 1, "oui", "universel"), "est_hereditaire str -> ValueError")
check(leve(M.classe_par_criteres, 3, False, "censitaire"), "suffrage hors référentiel -> ValueError")
check(leve(M.classe_par_criteres, 3, False, None), "suffrage None -> ValueError")

# ── 8) SOUNDNESS — combinaisons NON déterminées par les critères -> ValueError (jamais inventer) ──
check(leve(M.classe_par_criteres, 1, False, "restreint"), "un seul non héréd. + suffrage restreint -> indéterminé")
check(leve(M.classe_par_criteres, 5, True, "aucun"), "groupe héréditaire -> indéterminé")
check(leve(M.classe_par_criteres, 1000, False, "aucun"), "corps nombreux non universel -> indéterminé")
check(leve(M.classe_par_criteres, 100, False, "restreint"), "au-delà du petit groupe, non universel -> indéterminé")

# ── 9) SOUNDNESS — attribution_pouvoir hors référentiel ──
check(leve(M.attribution_pouvoir, "militaire"), "pouvoir 'militaire' hors référentiel -> ValueError")
check(leve(M.attribution_pouvoir, "mediatique"), "pouvoir 'mediatique' hors référentiel -> ValueError")
check(leve(M.attribution_pouvoir, 5), "attribution_pouvoir(int) -> ValueError")
check(leve(M.attribution_pouvoir, ""), "attribution_pouvoir('') -> ValueError")

# ── 10) DÉTERMINISME ──
check(M.definition("monarchie") == M.definition("monarchie"), "definition déterministe")
check(M.classe_par_criteres(3, False, "restreint") == M.classe_par_criteres(3, False, "restreint"),
      "classe_par_criteres déterministe")
check(M.separation_pouvoirs() == M.separation_pouvoirs(), "separation_pouvoirs déterministe")

print(f'\n=== valide_systemes_politiques : {ok}/{ok+ko} ===')
import sys
sys.exit(0 if ko == 0 else 1)
