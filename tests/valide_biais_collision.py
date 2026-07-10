"""
VALIDE biais_collision.py — held-out ADVERSE.

ANCRE NON CIRCULAIRE — PARADOXE DE BERKSON (1946), contre-intuitif :
  Deux maladies A et B INDÉPENDANTES dans la population générale -> odds ratio A–B = 1 EXACTEMENT.
  Population de 1000 personnes, P(A)=P(B)=1/10, indépendantes (produit des marges) :
      (A,B) = (1,1)->10   (1,0)->90   (0,1)->90   (0,0)->810      [total 1000]
      OR_population = (10·810)/(90·90) = 8100/8100 = 1     ← calculé À LA MAIN, PAS par la formule testée
  L'hospitalisation S est causée par les maladies (collider A→S←B). Probabilité d'hospitalisation :
      h(1,1)=9/10 -> 9 ; h(1,0)=h(0,1)=1/2 -> 45 ; h(0,0)=1/10 -> 81 (baseline non nulle).
  Dans les hospitalisés (S=1) :
      OR_selectionne = (9·81)/(45·45) = 729/2025 = 9/25 = 0.36 < 1   ← association NÉGATIVE CRÉÉE par la sélection.
  Ces deux nombres (1 et 9/25) sont connus indépendamment de biais_berkson : ce sont des produits croisés
  écrits à la main -> validation NON circulaire.

TÉMOIN : si la sélection est INDÉPENDANTE de A et B (même taux dans chaque case), OR_selectionne == OR_population
  (aucun biais), et ce pour un OR quelconque (1 ou 2).

SOUNDNESS : table incomplète (que s=1 / que s=0), case nulle, clé non binaire, bool/float/négatif -> ValueError.
"""
from fractions import Fraction

import biais_collision as BC
from causalite import GrapheCausal

ok = 0
ko = 0


def check(cond, label):
    global ok, ko
    if cond:
        ok += 1
    else:
        ko += 1
        print(f"  FAIL: {label}")


def leve(fn, *a, **k):
    """True ssi fn lève ValueError (abstention structurelle)."""
    try:
        fn(*a, **k)
        return False
    except ValueError:
        return True


# ── ANCRE : table de Berkson en dur (population entière) ──
BERKSON = {
    (1, 1, 1): 9,  (1, 1, 0): 1,     # 10 avec A et B (9 hospitalisés)
    (1, 0, 1): 45, (1, 0, 0): 45,    # 90 A seul (45 hospitalisés)
    (0, 1, 1): 45, (0, 1, 0): 45,    # 90 B seul (45 hospitalisés)
    (0, 0, 1): 81, (0, 0, 0): 729,   # 810 ni l'un ni l'autre (81 hospitalisés)
}

r = BC.biais_berkson(BERKSON)

# 1) OR de population = 1 EXACTEMENT (indépendance A–B) — ancre écrite à la main
check(r["or_population"] == Fraction(1), "Berkson : OR population = 1 (A,B indépendantes)")
check(isinstance(r["or_population"], Fraction), "OR population est une Fraction exacte")
# (10·810)/(90·90) recalculé indépendamment
check(r["or_population"] == Fraction(10 * 810, 90 * 90), "OR population = (10·810)/(90·90)")

# 2) OR sélectionné = 9/25 < 1 (association négative créée) — ancre écrite à la main
check(r["or_selectionne"] == Fraction(9, 25), "Berkson : OR sélectionné = 9/25")
check(r["or_selectionne"] == Fraction(9 * 81, 45 * 45), "OR sélectionné = (9·81)/(45·45)")
check(r["or_selectionne"] < 1, "Berkson : OR sélectionné < 1 (contre-intuitif)")
check(r["or_selectionne"] != r["or_population"], "sélectionné ≠ population")

# 3) biais détecté
check(r["biais_detecte"] is True, "Berkson : biais_detecte = True")

# ── TÉMOIN 1 : sélection indépendante (50 % de chaque case), OR population = 1 -> pas de biais ──
TEMOIN1 = {
    (1, 1, 1): 5,   (1, 1, 0): 5,    # 10, moitié sélectionnée
    (1, 0, 1): 45,  (1, 0, 0): 45,   # 90
    (0, 1, 1): 45,  (0, 1, 0): 45,   # 90
    (0, 0, 1): 405, (0, 0, 0): 405,  # 810
}
t1 = BC.biais_berkson(TEMOIN1)
check(t1["or_population"] == Fraction(1), "témoin1 : OR population = 1")
check(t1["or_selectionne"] == Fraction(1), "témoin1 : OR sélectionné = 1 (sélection indépendante)")
check(t1["or_selectionne"] == t1["or_population"], "témoin1 : sélectionné == population")
check(t1["biais_detecte"] is False, "témoin1 : biais_detecte = False")

# ── TÉMOIN 2 : sélection indépendante préserve un OR ≠ 1 (ici OR = 2) ──
# population (1,1)=20 (1,0)=10 (0,1)=10 (0,0)=10 -> OR = (20·10)/(10·10) = 2 ; 50 % sélectionné dans chaque case
TEMOIN2 = {
    (1, 1, 1): 10, (1, 1, 0): 10,
    (1, 0, 1): 5,  (1, 0, 0): 5,
    (0, 1, 1): 5,  (0, 1, 0): 5,
    (0, 0, 1): 5,  (0, 0, 0): 5,
}
t2 = BC.biais_berkson(TEMOIN2)
check(t2["or_population"] == Fraction(2), "témoin2 : OR population = 2 (calculé à la main)")
check(t2["or_selectionne"] == Fraction(2), "témoin2 : OR sélectionné = 2 (sélection indépendante préserve l'OR)")
check(t2["biais_detecte"] is False, "témoin2 : biais_detecte = False")

# ── (c) DÉMONSTRATION CHIFFRÉE : conditionner sur un collider crée une association ──
demo = BC.conditionner_sur_collider_cree_association()
check(demo["or_population"] == Fraction(1), "démo : OR population = 1")
check(demo["or_conditionne"] == Fraction(9, 25), "démo : OR conditionné = 9/25")
check(demo["association_creee"] is True, "démo : association créée (True)")
check(demo["or_conditionne"] < demo["or_population"], "démo : conditionné < population")

# ── (b) est_collider via causalite.GrapheCausal ──
g = GrapheCausal()
g.ajoute_cause("A", "S")   # A → S
g.ajoute_cause("B", "S")   # B → S   (S = effet commun = collider)
check(BC.est_collider(g, "S", "A", "B") is True, "collider : S effet commun de A et B")
check(BC.est_collider(g, "S", "B", "A") is True, "collider : symétrique (B,A)")
check(BC.est_collider(g, "S", "A", "Z") is False, "non-collider : Z n'est pas parent de S")

# chaîne A → M → S : A n'est PAS parent direct de S -> pas un collider de (A,B)
g2 = GrapheCausal()
g2.ajoute_cause("A", "M")
g2.ajoute_cause("M", "S")
g2.ajoute_cause("B", "S")
check(BC.est_collider(g2, "S", "A", "B") is False, "non-collider : A cause indirecte (chaîne), pas parent")
check(BC.est_collider(g2, "S", "M", "B") is True, "collider : M et B parents directs de S")

# un seul parent -> pas de collider
g3 = GrapheCausal()
g3.ajoute_cause("A", "S")
check(BC.est_collider(g3, "S", "A", "B") is False, "non-collider : S n'a qu'un parent")

# ── (d) catalogue des biais ──
cat = BC.catalogue_biais()
noms = {e["nom"] for e in cat}
check(len(cat) == 6, "catalogue : 6 mécanismes nommés")
check("Berkson (collision)" in noms, "catalogue contient Berkson")
check(any("survie" == e["nom"] for e in cat), "catalogue contient survie")
check(all({"nom", "mecanisme", "remede", "module"} <= set(e) for e in cat), "chaque entrée a nom/mecanisme/remede/module")
# les modules DÉDIÉS cités sont les vrais noms de modules du dépôt (non modifiés)
mods = {e["module"] for e in cat}
check("biais_survie" in mods, "catalogue cite le module biais_survie")
check("biais_publication" in mods, "catalogue cite le module biais_publication")
check("biais_longueur" in mods, "catalogue cite le module biais_longueur")
check(None in mods, "non-réponse / auto-sélection : pas de module dédié (None)")
# tous les modules cités non-None existent et sont importables
import importlib
for e in cat:
    if e["module"] is not None:
        check(importlib.import_module(e["module"]) is not None, f"module {e['module']} importable")

# ── (e) HONNÊTETÉ ──
h = BC.pourquoi_le_mecanisme_est_requis()
check(isinstance(h, str) and "MÉCANISME" in h, "honnêteté : mécanisme de sélection requis (déclaré)")

# ── SOUNDNESS : table incomplète ──
check(leve(BC.biais_berkson, {(1, 1, 1): 9, (1, 0, 1): 45, (0, 1, 1): 45, (0, 0, 1): 81}),
      "que des s=1 (échantillon sélectionné seul) -> ValueError")
check(leve(BC.biais_berkson, {(1, 1, 0): 9, (1, 0, 0): 45, (0, 1, 0): 45, (0, 0, 0): 81}),
      "que des s=0 (personne sélectionné) -> ValueError")
check(leve(BC.biais_berkson, {}), "dict vide -> ValueError")
check(leve(BC.biais_berkson, [(1, 1, 1)]), "non-dict -> ValueError")

# ── SOUNDNESS : case nulle ──
# population : (0,0) absent -> case population nulle
check(leve(BC.biais_berkson, {(1, 1, 1): 9, (1, 1, 0): 1, (1, 0, 1): 45, (1, 0, 0): 45,
                              (0, 1, 1): 45, (0, 1, 0): 45}),
      "case population (0,0) nulle -> ValueError")
# selected : (0,0) jamais sélectionné -> case échantillon nulle
check(leve(BC.biais_berkson, {(1, 1, 1): 9, (1, 1, 0): 1, (1, 0, 1): 45, (1, 0, 0): 45,
                              (0, 1, 1): 45, (0, 1, 0): 45, (0, 0, 0): 810}),
      "case échantillon (0,0) nulle -> ValueError")

# ── SOUNDNESS : clés / effectifs invalides ──
check(leve(BC.biais_berkson, {(2, 0, 1): 5, (0, 0, 0): 5}), "variable non binaire (2) -> ValueError")
check(leve(BC.biais_berkson, {(True, 0, 1): 5, (0, 0, 0): 5}), "clé bool -> ValueError")
check(leve(BC.biais_berkson, {(1, 0, 1): True, (0, 0, 0): 5}), "effectif bool -> ValueError")
check(leve(BC.biais_berkson, {(1, 0, 1): 1.5, (0, 0, 0): 5}), "effectif float -> ValueError")
check(leve(BC.biais_berkson, {(1, 0, 1): -3, (0, 0, 0): 5}), "effectif négatif -> ValueError")
check(leve(BC.biais_berkson, {(1, 0): 5, (0, 0, 0): 5}), "clé longueur 2 -> ValueError")
check(leve(BC.biais_berkson, {"ab": 5, (0, 0, 0): 5}), "clé non-tuple -> ValueError")
check(leve(BC.biais_berkson, {(1, 0, 1): "5", (0, 0, 0): 5}), "effectif str -> ValueError")

# ── SOUNDNESS : est_collider ──
check(leve(BC.est_collider, {"A": ["S"]}, "S", "A", "B"), "est_collider dag non-GrapheCausal -> ValueError")
check(leve(BC.est_collider, 42, "S", "A", "B"), "est_collider dag int -> ValueError")
check(leve(BC.est_collider, g, "S", "A", "A"), "est_collider a==b -> ValueError")
check(leve(BC.est_collider, g, "A", "A", "B"), "est_collider variable==a -> ValueError")
check(leve(BC.est_collider, g, "B", "A", "B"), "est_collider variable==b -> ValueError")

# ── DÉTERMINISME ──
check(BC.biais_berkson(BERKSON) == BC.biais_berkson(BERKSON), "déterminisme biais_berkson")
check(BC.conditionner_sur_collider_cree_association() == BC.conditionner_sur_collider_cree_association(),
      "déterminisme démonstration")
check(BC.catalogue_biais() == BC.catalogue_biais(), "déterminisme catalogue")
check(BC.est_collider(g, "S", "A", "B") == BC.est_collider(g, "S", "A", "B"), "déterminisme est_collider")

print(f"\n=== valide_biais_collision : {ok}/{ok+ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
