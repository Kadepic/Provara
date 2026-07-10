"""
VALIDE temps_geologiques.py — held-out ADVERSE.

ANCRES NON CIRCULAIRES (faits conventionnels ICS, connus INDÉPENDAMMENT du module) :
  • limite Crétacé/Paléogène (extinction des dinosaures non-aviens) = 66.0 Ma ;
  • limite Permien/Trias (plus grande extinction) = 251.902 Ma ;
  • base du Cambrien (début de la vie complexe abondante) = 538.8 Ma ;
  • base de l'Holocène = 11 700 ans = 0.0117 Ma ;
  • periode_a(70) = 'Crétacé' ; periode_a(60) = 'Paléogène' ;
  • ere_a(100) = 'Mésozoïque' ; eon_a(3000) = 'Archéen' ;
  • PAVAGE : somme des durées des périodes du Phanérozoïque = 538.8 Ma exactement, additionnée ici par
    un CHEMIN DE CODE INDÉPENDANT (boucle qui somme duree() des 12 périodes), à comparer à Fraction('538.8').

SOUNDNESS : nom hors charte, âge < 0, âge > 4567, bool/str/NaN/inf, mauvaise arité -> ValueError.
DÉTERMINISME : double appel, égalité exigée.
"""
from fractions import Fraction

import temps_geologiques as T

ok = 0
ko = 0


def check(cond, label):
    global ok, ko
    if cond:
        ok += 1
    else:
        ko += 1
        print(f"  FAIL: {label}")


def leve(fn, *a):
    """True ssi fn(*a) lève ValueError (abstention structurelle)."""
    try:
        fn(*a)
        return False
    except ValueError:
        return True


F = Fraction

# ── 1) ANCRES : bornes conventionnelles ICS écrites EN DUR ──
# limite K/Pg = 66.0 : c'est la fin du Crétacé ET le début du Paléogène
deb_cret, fin_cret = T.intervalle("Crétacé")
check(fin_cret == F("66.0"), "fin Crétacé = 66.0 Ma (limite K/Pg)")
deb_pal, fin_pal = T.intervalle("Paléogène")
check(deb_pal == F("66.0"), "début Paléogène = 66.0 Ma (limite K/Pg)")
# limite P/T = 251.902 : fin Permien = début Trias
check(T.intervalle("Permien")[1] == F("251.902"), "fin Permien = 251.902 Ma (limite P/T)")
check(T.intervalle("Trias")[0] == F("251.902"), "début Trias = 251.902 Ma (limite P/T)")
# base du Cambrien = 538.8
check(T.intervalle("Cambrien")[0] == F("538.8"), "début Cambrien = 538.8 Ma")
# base de l'Holocène = 0.0117 Ma (11 700 ans)
check(T.intervalle("Holocène")[0] == F("0.0117"), "début Holocène = 0.0117 Ma (11 700 ans)")
check(T.intervalle("Holocène")[1] == F("0"), "fin Holocène = 0 (présent)")
# éons — bornes du contenu minimal
check(T.intervalle("Hadéen") == (F("4567"), F("4031")), "Hadéen 4567-4031")
check(T.intervalle("Archéen") == (F("4031"), F("2500")), "Archéen 4031-2500")
check(T.intervalle("Protérozoïque") == (F("2500"), F("538.8")), "Protérozoïque 2500-538.8")
check(T.intervalle("Phanérozoïque") == (F("538.8"), F("0")), "Phanérozoïque 538.8-0")

# ── 2) ROUTAGE D'ÂGE (ancres directes) ──
check(T.periode_a(70) == "Crétacé", "periode_a(70) = Crétacé")
check(T.periode_a(60) == "Paléogène", "periode_a(60) = Paléogène")
check(T.ere_a(100) == "Mésozoïque", "ere_a(100) = Mésozoïque")
check(T.eon_a(3000) == "Archéen", "eon_a(3000) = Archéen")
# routages supplémentaires connus
check(T.eon_a(0) == "Phanérozoïque", "eon_a(0) = Phanérozoïque")
check(T.eon_a(4500) == "Hadéen", "eon_a(4500) = Hadéen")
check(T.ere_a(300) == "Paléozoïque", "ere_a(300) = Paléozoïque")
check(T.ere_a(30) == "Cénozoïque", "ere_a(30) = Cénozoïque")
check(T.periode_a(500) == "Cambrien", "periode_a(500) = Cambrien")
check(T.periode_a(0) == "Quaternaire", "periode_a(0) = Quaternaire")
check(T.periode_a(1) == "Quaternaire", "periode_a(1) = Quaternaire")
# convention de borne : 66.0 exactement -> Crétacé (borne vieille exclue du Paléogène)
check(T.periode_a(66.0) == "Crétacé", "periode_a(66.0) = Crétacé (borne jeune incluse)")

# ── 3) PAVAGE : somme des durées des 12 périodes du Phanérozoïque = 538.8 (chemin indépendant) ──
periodes = ("Cambrien", "Ordovicien", "Silurien", "Dévonien", "Carbonifère", "Permien",
            "Trias", "Jurassique", "Crétacé",
            "Paléogène", "Néogène", "Quaternaire")
somme = F(0)
for p in periodes:
    somme += T.duree(p)          # addition INDÉPENDANTE (pas la formule interne de pavage)
check(somme == F("538.8"), f"pavage : Σ durées périodes = 538.8 (obtenu {somme})")
check(len(periodes) == 12, "12 périodes couvrent le Phanérozoïque")

# durée exacte d'un intervalle
check(T.duree("Crétacé") == F("145.0") - F("66.0"), "durée Crétacé = 145.0-66.0 = 79.0")
check(T.duree("Quaternaire") == F("2.58"), "durée Quaternaire = 2.58-0")

# ── 4) HIÉRARCHIE parent / enfants ──
check(T.parent("Crétacé") == "Mésozoïque", "parent Crétacé = Mésozoïque")
check(T.parent("Mésozoïque") == "Phanérozoïque", "parent Mésozoïque = Phanérozoïque")
check(T.parent("Phanérozoïque") is None, "parent d'un éon = None")
check(T.parent("Holocène") == "Quaternaire", "parent Holocène = Quaternaire")
check(T.enfants("Cénozoïque") == ("Paléogène", "Néogène", "Quaternaire"),
      "enfants Cénozoïque = Paléogène,Néogène,Quaternaire (vieux->jeune)")
check(T.enfants("Quaternaire") == ("Pléistocène", "Holocène"), "enfants Quaternaire = Pléistocène,Holocène")
check(T.enfants("Phanérozoïque") == ("Paléozoïque", "Mésozoïque", "Cénozoïque"),
      "enfants Phanérozoïque = 3 ères")
check(T.enfants("Hadéen") == (), "enfants Hadéen = () (feuille : pas d'ère définie)")
check(T.enfants("Holocène") == (), "enfants Holocène = () (feuille)")

# cohérence enfants pavent parent (vérif indépendante côté gate)
for parent_nom in ("Phanérozoïque", "Paléozoïque", "Mésozoïque", "Cénozoïque", "Quaternaire"):
    fils = T.enfants(parent_nom)
    dp, fp = T.intervalle(parent_nom)
    check(T.intervalle(fils[0])[0] == dp, f"pavage[{parent_nom}] : 1er enfant commence au début")
    check(T.intervalle(fils[-1])[1] == fp, f"pavage[{parent_nom}] : dernier enfant finit à la fin")

# ── 5) CATALOGUE déterministe et complet ──
cat = T.catalogue()
check(cat == T.catalogue(), "catalogue déterministe")
check(len(cat) == 21, f"catalogue = 21 unités (4 éons + 3 ères + 12 périodes + 2 époques)")
check(cat[0] == "Hadéen", "catalogue trié : plus vieux début = Hadéen")
for essentiel in ("Phanérozoïque", "Cénozoïque", "Quaternaire", "Holocène", "Cambrien"):
    check(essentiel in cat, f"{essentiel} présent au catalogue")

# ── 6) SOUNDNESS — nom hors charte ──
check(leve(T.intervalle, "Anthropocène"), "nom hors charte -> ValueError")
check(leve(T.intervalle, "cambrien"), "casse différente (cambrien) hors charte -> ValueError")
check(leve(T.duree, "Jurassic"), "nom anglais hors charte -> ValueError")
check(leve(T.parent, ""), "nom vide -> ValueError")
check(leve(T.enfants, "Précambrien"), "Précambrien (non catalogué) -> ValueError")
check(leve(T.intervalle, 42), "nom non-str -> ValueError")

# ── 7) SOUNDNESS — âge hors domaine ──
check(leve(T.eon_a, -1), "âge < 0 -> ValueError")
check(leve(T.eon_a, 4568), "âge > 4567 -> ValueError")
check(leve(T.eon_a, 10000), "âge très grand -> ValueError")
check(leve(T.periode_a, 3000), "periode_a(3000) : pas de période au Protérozoïque -> ValueError")
check(leve(T.ere_a, 1000), "ere_a(1000) : pas d'ère au Protérozoïque -> ValueError")

# ── 8) SOUNDNESS — types invalides ──
check(leve(T.eon_a, True), "âge bool -> ValueError")
check(leve(T.eon_a, "100"), "âge str -> ValueError")
check(leve(T.eon_a, float("nan")), "âge NaN -> ValueError")
check(leve(T.eon_a, float("inf")), "âge inf -> ValueError")
check(leve(T.eon_a, float("-inf")), "âge -inf -> ValueError")
check(leve(T.periode_a, None), "âge None -> ValueError")
check(leve(T.periode_a, 1 + 2j), "âge complexe -> ValueError")

# ── 9) DÉTERMINISME ──
check(T.periode_a(70) == T.periode_a(70), "déterminisme periode_a")
check(T.intervalle("Crétacé") == T.intervalle("Crétacé"), "déterminisme intervalle")
check(T.enfants("Cénozoïque") == T.enfants("Cénozoïque"), "déterminisme enfants")

print(f"\n=== valide_temps_geologiques : {ok}/{ok+ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
