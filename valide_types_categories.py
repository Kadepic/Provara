"""VALIDE types_categories.py — ADVERSE, FAUX=0.

Ancres CONNUES : règles de typage du lambda-calcul simplement typé (application f:A->B sur x:A donne B, abstraction
λx:A.x : A->A) + lois de catégorie (composition A->B->C donne A->C, identité neutre, associativité). SOUNDNESS :
type/morphisme incompatible -> ValueError (jamais un verdict faux). DÉTERMINISME : mêmes entrées -> mêmes sorties.
"""
import types_categories as M

ok = 0
ko = 0


def check(c, l):
    global ok, ko
    if c:
        ok += 1
    else:
        ko += 1
        print(f"  FAIL: {l}")


def leve(fn, *a):
    try:
        fn(*a)
        return False
    except ValueError:
        return True
    except Exception:
        return False


# ───────────────────────── (1) LAMBDA SIMPLEMENT TYPÉ ─────────────────────────
ctx = {"f": "A->B", "x": "A", "y": "C", "g": "B->C"}

# variables
check(M.type_de(M.var("x"), ctx) == "A", "var x : A")
check(M.type_de(M.var("f"), ctx) == "A->B", "var f : A->B")

# application bien typée : (f:A->B)(x:A) : B
check(M.type_de(M.app(M.var("f"), M.var("x")), ctx) == "B", "(f x) : B")

# composition fonctionnelle (g:B->C)((f:A->B)(x:A)) : C
check(M.type_de(M.app(M.var("g"), M.app(M.var("f"), M.var("x"))), ctx) == "C", "(g (f x)) : C")

# abstraction : λx:A. x  :  A->A  (identité)
check(M.type_de(M.lam("x", "A", M.var("x")), {}) == "A->A", "λx:A.x : A->A")

# abstraction d'ordre supérieur : λf:A->B. λx:A. (f x)  :  (A->B)->A->B
ho = M.lam("f", "A->B", M.lam("x", "A", M.app(M.var("f"), M.var("x"))))
check(M.type_de(ho, {}) == "(A->B)->A->B", "λf:A->B.λx:A.(f x) : (A->B)->A->B")

# composition λg:B->C. λf:A->B. λx:A. g (f x)  :  (B->C)->(A->B)->A->C
comp = M.lam("g", "B->C", M.lam("f", "A->B", M.lam("x", "A",
            M.app(M.var("g"), M.app(M.var("f"), M.var("x"))))))
check(M.type_de(comp, {}) == "(B->C)->(A->B)->A->C", "combinateur de composition typé")

# normalisation des types : '->' associatif à droite, parenthésage minimal
check(M.parse_type("A->B->C") == "A->B->C", "A->B->C reste A->B->C (assoc droite)")
check(M.parse_type("(A->B)->C") == "(A->B)->C", "(A->B)->C garde ses parenthèses")
check(M.parse_type("A->(B->C)") == "A->B->C", "A->(B->C) = A->B->C")
check(M.parse_type("(A)") == "A", "parenthèses superflues réduites")

# bien_type
check(M.bien_type(M.app(M.var("f"), M.var("x")), ctx), "bien_type (f x) True")
check(not M.bien_type(M.app(M.var("f"), M.var("y")), ctx), "bien_type (f y) False")

# SOUNDNESS typage
check(leve(M.type_de, M.app(M.var("f"), M.var("y")), ctx), "(f:A->B)(y:C) -> ValueError")     # arg incompatible
check(leve(M.type_de, M.app(M.var("x"), M.var("y")), ctx), "(x:A) appliqué -> ValueError")     # tête non-fonction
check(leve(M.type_de, M.var("z"), ctx), "variable libre z -> ValueError")
check(leve(M.type_de, M.var("x"), {}), "x hors contexte -> ValueError")
check(leve(M.type_de, ("oops", 1), ctx), "constructeur inconnu -> ValueError")
check(leve(M.type_de, 42, ctx), "terme non-tuple -> ValueError")
check(leve(M.type_de, M.var("x"), "pas un dict"), "contexte non-dict -> ValueError")
check(leve(M.parse_type, "A->"), "type 'A->' incomplet -> ValueError")
check(leve(M.parse_type, "(A->B"), "type parenthèse non fermée -> ValueError")
check(leve(M.parse_type, ""), "type vide -> ValueError")
check(leve(M.parse_type, "A B"), "type 'A B' jetons résiduels -> ValueError")
check(leve(M.parse_type, "A->#"), "type caractère invalide -> ValueError")

# ───────────────────────── (2) LOIS DE CATÉGORIE ─────────────────────────
f = M.morphisme("f", "A", "B")
g = M.morphisme("g", "B", "C")
h = M.morphisme("h", "C", "D")

# composition A->B->C donne A->C
gf = M.compose(g, f)
check(gf.dom == "A" and gf.cod == "C", "compose(g,f) : A -> C")
check(gf.fleches == ("f", "g"), "compose(g,f) chemin = (f, g)  (g après f)")

# composition triple A->B->C->D donne A->D
hgf = M.compose(h, M.compose(g, f))
check(hgf.dom == "A" and hgf.cod == "D" and hgf.fleches == ("f", "g", "h"), "h∘g∘f : A -> D")

# identité neutre : id(B) ∘ f = f  et  f ∘ id(A) = f
idA = M.identite("A")
idB = M.identite("B")
check(idA.dom == "A" and idA.cod == "A" and idA.fleches == (), "id(A) : A -> A chemin vide")
check(M.compose(idB, f) == f, "id(cod f) ∘ f = f")
check(M.compose(f, idA) == f, "f ∘ id(dom f) = f")
check(M.verifie_identite(f), "verifie_identite(f) True")
check(M.verifie_identite(h), "verifie_identite(h) True")

# associativité (h∘g)∘f = h∘(g∘f)
check(M.compose(M.compose(h, g), f) == M.compose(h, M.compose(g, f)), "(h∘g)∘f = h∘(g∘f) égalité")
check(M.verifie_associativite(h, g, f), "verifie_associativite(h,g,f) True")

# l'égalité de morphismes n'est PAS triviale : deux composites différents diffèrent
k = M.morphisme("k", "A", "B")
check(M.compose(g, f) != M.compose(g, k), "g∘f ≠ g∘k (chemins distincts)")
check(f != M.morphisme("f2", "A", "B"), "morphismes de même type mais noms ≠ sont distincts")

# SOUNDNESS catégorie : composition incompatible -> ValueError
check(leve(M.compose, g, M.morphisme("u", "A", "X")), "compose dom(g)=B ≠ cod=X -> ValueError")
check(leve(M.compose, f, g), "compose(f,g) avec cod g=C ≠ dom f=A -> ValueError")
check(leve(M.verifie_associativite, h, g, M.morphisme("u", "A", "X")), "assoc non composable -> ValueError")
check(leve(M.compose, g, "pas un morphisme"), "compose argument non-morphisme -> ValueError")
check(leve(M.verifie_identite, 7), "verifie_identite non-morphisme -> ValueError")
check(leve(M.morphisme, "f", "", "B"), "morphisme objet vide -> ValueError")
check(leve(M.morphisme, "", "A", "B"), "morphisme nom vide -> ValueError")
check(leve(M.identite, ""), "identite objet vide -> ValueError")

# ───────────────────────── DÉTERMINISME ─────────────────────────
check(M.type_de(M.app(M.var("f"), M.var("x")), ctx) == M.type_de(M.app(M.var("f"), M.var("x")), ctx),
      "type_de déterministe")
check(M.compose(g, f) == M.compose(g, f), "compose déterministe")
check(M.parse_type("A->B->C") == M.parse_type("A->B->C"), "parse_type déterministe")

print(f"\n=== valide_types_categories : {ok}/{ok + ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
