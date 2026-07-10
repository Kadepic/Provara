"""GATE ADVERSE — simplification_booleenne (Quine-McCluskey), FAUX=0.

ANCRES NON CIRCULAIRES : chaque attendu est connu INDÉPENDAMMENT de l'algorithme testé —
lois booléennes classiques (absorption, De Morgan, tiers exclu, contradiction), compte de littéraux
fait à la main, et surtout ÉQUIVALENCE vérifiée par `algebre_boole.equivalent` (chemin de code DISTINCT
qui n'utilise pas Quine-McCluskey). Aucun attendu n'est recalculé avec la fonction testée.
"""
from __future__ import annotations

import algebre_boole as ab
import simplification_booleenne as sb

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
    """True ssi fn(*a) lève (ValueError attendue, ou RuntimeError pour la garde FAUX=0)."""
    try:
        fn(*a, **k)
        return False
    except (ValueError, RuntimeError):
        return True
    except Exception:
        return False


# ─────────────────────────────────────────────────────────────────────────────────────────────────
# ANCRE (a) : 'a & b | a & ~b' se minimise en 'a' (l'implicant b disparaît).
#   Vérité (a,b) : vrai ssi a=1 (b1|b0 = 1) -> forme minimale = 'a'. Vérifié aussi par équivalence.
# ─────────────────────────────────────────────────────────────────────────────────────────────────
r = sb.minimise("a & b | a & ~b", ["a", "b"])
check(r == "a", f"(a) 'a&b|a&~b' -> 'a' (obtenu {r!r})")
check(ab.equivalent("a & b | a & ~b", r), "(a) équivalence indépendante")

# ANCRE (b) : absorption 'a | a & b' -> 'a'.
r = sb.minimise("a | a & b", ["a", "b"])
check(r == "a", f"(b) absorption 'a|a&b' -> 'a' (obtenu {r!r})")
check(ab.equivalent("a | a & b", r), "(b) équivalence indépendante")

# ANCRE (c) : De Morgan — minimise('~(a&b)') et minimise('~a|~b') donnent des formes ÉQUIVALENTES.
m1 = sb.minimise("~(a & b)", ["a", "b"])
m2 = sb.minimise("~a | ~b", ["a", "b"])
check(ab.equivalent(m1, m2), f"(c) De Morgan : {m1!r} ~ {m2!r}")
check(ab.equivalent("~(a & b)", m1), "(c) minimise ~ original (gauche)")
check(ab.equivalent("~a | ~b", m2), "(c) minimise ~ original (droite)")

# ANCRE (d) : contradiction 'a & ~a' -> '0'.
r = sb.minimise("a & ~a", ["a"])
check(r == "0", f"(d) contradiction 'a&~a' -> '0' (obtenu {r!r})")

# ANCRE (e) : tiers exclu 'a | ~a' -> '1'.
r = sb.minimise("a | ~a", ["a"])
check(r == "1", f"(e) tautologie 'a|~a' -> '1' (obtenu {r!r})")

# Tautologie/contradiction à plusieurs variables.
check(sb.minimise("(a | ~a) & (b | ~b)", ["a", "b"]) == "1", "(e') tautologie 2 vars -> '1'")
check(sb.minimise("a & ~a | b & ~b", ["a", "b"]) == "0", "(d') contradiction 2 vars -> '0'")

# ─────────────────────────────────────────────────────────────────────────────────────────────────
# ANCRE (f) : cas classique 3 variables — minterms {0,1,2,5,6,7} sur (a,b,c).
#   Somme-de-produits canonique = 6 minterms × 3 littéraux = 18 littéraux (compté à la main).
#   La forme minimale a STRICTEMENT MOINS de 18 littéraux (et couvre exactement les mêmes valuations).
# ─────────────────────────────────────────────────────────────────────────────────────────────────
mt = [0, 1, 2, 5, 6, 7]
# construction indépendante de la SOP canonique (chaque minterm -> produit des 3 littéraux, MSB=a).
noms3 = ["a", "b", "c"]


def _canon(minterm_indices, noms):
    n = len(noms)
    termes = []
    for m in minterm_indices:
        lits = []
        for k in range(n):
            bit = (m >> (n - 1 - k)) & 1
            lits.append(noms[k] if bit == 1 else "~" + noms[k])
        termes.append(" & ".join(lits))
    return " | ".join(termes)


canon = _canon(mt, noms3)
check(sb.nombre_litteraux(canon) == 18, f"(f) canonique = 18 littéraux (obtenu {sb.nombre_litteraux(canon)})")
mini = sb.minimise(canon, noms3)
check(sb.nombre_litteraux(mini) < 18, f"(f) minimale < 18 littéraux (obtenu {sb.nombre_litteraux(mini)})")
check(sb.nombre_litteraux(mini) == 6, f"(f) minimale = 6 littéraux (3 termes de 2) (obtenu {sb.nombre_litteraux(mini)})")
check(ab.equivalent(canon, mini), "(f) minimale ~ canonique (mêmes valuations)")

# impliquants premiers de (f) : il y en a exactement 6 (chart cyclique), aucun essentiel.
pis = sb.impliquants_premiers(mt, 3)
check(len(pis) == 6, f"(f) 6 implicants premiers (obtenu {len(pis)})")
cover = sb.couverture_minimale(pis, mt)
check(len(cover) == 3, f"(f) couverture minimale = 3 termes (obtenu {len(cover)})")

# ─────────────────────────────────────────────────────────────────────────────────────────────────
# minterms(table) et depuis_expression : deux chemins vers les MÊMES minterms.
# ─────────────────────────────────────────────────────────────────────────────────────────────────
# table de vérité de 'a & b' sur (a,b) : vraie seulement pour a=1,b=1 -> minterm 3.
check(sb.minterms([0, 0, 0, 1]) == [3], "minterms table 'a&b' -> [3]")
check(sb.depuis_expression("a & b", ["a", "b"]) == [3], "depuis_expression 'a&b' -> [3]")
check(sb.minterms([1, 0, 0, 1]) == [0, 3], "minterms table EQUIV -> [0,3]")
check(sb.depuis_expression("a = b", ["a", "b"]) == [0, 3], "depuis_expression 'a=b' -> [0,3]")
# 'a' seule sur (a,b) : a=1 -> minterms 2 (10) et 3 (11).
check(sb.depuis_expression("a", ["a", "b"]) == [2, 3], "depuis_expression 'a' sur (a,b) -> [2,3]")

# ─────────────────────────────────────────────────────────────────────────────────────────────────
# impliquants_premiers : fusion de base connue à la main.
#   minterms {0,1} sur 1 bit ... prenons 2 bits : {0,1,2,3} (tout) -> un seul implicant premier ('-','-').
# ─────────────────────────────────────────────────────────────────────────────────────────────────
check(sb.impliquants_premiers([0, 1, 2, 3], 2) == [("-", "-")], "PI de {0,1,2,3} = (-,-)")
# {0,1} sur 2 bits -> 00,01 fusionnent en 0- ; un seul PI.
check(sb.impliquants_premiers([0, 1], 2) == [(0, "-")], "PI de {0,1} = (0,-)")
# {1,2} sur 2 bits (01,10) : diffèrent de 2 bits -> pas de fusion -> 2 PI.
check(sorted(sb.impliquants_premiers([1, 2], 2)) == sorted([(0, 1), (1, 0)]), "PI de {1,2} = deux minterms")

# couverture avec essentiel : {0,1} -> le PI (0,-) est essentiel, couverture = lui seul.
check(sb.couverture_minimale([(0, "-")], [0, 1]) == [(0, "-")], "couverture essentielle unique")

# ─────────────────────────────────────────────────────────────────────────────────────────────────
# nombre_litteraux : comptes faits à la main.
# ─────────────────────────────────────────────────────────────────────────────────────────────────
check(sb.nombre_litteraux("a & b | a & ~b") == 4, "littéraux 'a&b|a&~b' = 4")
check(sb.nombre_litteraux("a") == 1, "littéraux 'a' = 1")
check(sb.nombre_litteraux("~a | ~b | ~c") == 3, "littéraux '~a|~b|~c' = 3")
check(sb.nombre_litteraux("1") == 0, "littéraux '1' = 0 (constante)")
check(sb.nombre_litteraux("0") == 0, "littéraux '0' = 0 (constante)")

# ─────────────────────────────────────────────────────────────────────────────────────────────────
# ANCRE (g) : INVARIANT FORT sur 50 expressions déterministes (<= 4 variables).
#   Chaque expression = SOP canonique (littéraux = MAX possible), donc minimise ne peut qu'égaler ou réduire.
#   Pour CHACUNE : (1) minimise équivalent à l'original sur TOUTES les valuations (algebre_boole, 2e chemin),
#                  (2) minimise n'a JAMAIS plus de littéraux que l'original.
# ─────────────────────────────────────────────────────────────────────────────────────────────────
_NOMS = {1: ["a"], 2: ["a", "b"], 3: ["a", "b", "c"], 4: ["a", "b", "c", "d"]}
cas = []
seed = 0
while len(cas) < 50:
    seed += 1
    n = 1 + (seed % 4)  # 1..4 variables
    total = 1 << n
    ss = {m for m in range(total) if (m * 7 + seed * 3 + 1) % 4 != 0}
    if 0 < len(ss) < total:  # ni contradiction ni tautologie -> vraie minimisation
        cas.append((n, sorted(ss)))

inv_equiv = 0
inv_litt = 0
for n, ss in cas:
    noms = _NOMS[n]
    orig = _canon(ss, noms)
    mini = sb.minimise(orig, noms)
    if ab.equivalent(orig, mini):
        inv_equiv += 1
    else:
        print(f"  FAIL(g-equiv): {orig!r} -> {mini!r}")
    if sb.nombre_litteraux(mini) <= sb.nombre_litteraux(orig):
        inv_litt += 1
    else:
        print(f"  FAIL(g-litt): {orig!r}({sb.nombre_litteraux(orig)}) -> {mini!r}({sb.nombre_litteraux(mini)})")
check(len(cas) == 50, f"(g) 50 cas générés (obtenu {len(cas)})")
check(inv_equiv == 50, f"(g) 50/50 minimise équivalent à l'original (obtenu {inv_equiv})")
check(inv_litt == 50, f"(g) 50/50 minimise sans surcoût de littéraux (obtenu {inv_litt})")

# ─────────────────────────────────────────────────────────────────────────────────────────────────
# SOUNDNESS — abstentions structurelles (ValueError / RuntimeError).
# ─────────────────────────────────────────────────────────────────────────────────────────────────
# n_vars > 8 : budget dépassé.
check(leve(sb.impliquants_premiers, [0], 9), "abstention n_vars=9")
check(leve(sb.minimise, "a", ["a"] + [f"x{i}" for i in range(8)]), "abstention 9 variables")
check(leve(sb.depuis_expression, "a", ["v" + str(i) for i in range(9)]), "abstention depuis_expression 9 vars")

# n_vars : bool / str / float refusés.
check(leve(sb.impliquants_premiers, [0], True), "n_vars bool refusé")
check(leve(sb.impliquants_premiers, [0], "2"), "n_vars str refusé")
check(leve(sb.impliquants_premiers, [0], 2.0), "n_vars float refusé")
check(leve(sb.impliquants_premiers, [0], -1), "n_vars négatif refusé")

# minterm : bool / str / float / hors domaine refusés.
check(leve(sb.impliquants_premiers, [True], 2), "minterm bool refusé")
check(leve(sb.impliquants_premiers, ["0"], 2), "minterm str refusé")
check(leve(sb.impliquants_premiers, [1.0], 2), "minterm float refusé")
check(leve(sb.impliquants_premiers, [4], 2), "minterm hors [0,4) refusé")
check(leve(sb.impliquants_premiers, [-1], 2), "minterm négatif refusé")

# table : longueur non-puissance-de-2, entrée hors {0,1}, bool refusé.
check(leve(sb.minterms, [0, 1, 0]), "table longueur 3 refusée (non 2^n)")
check(leve(sb.minterms, []), "table vide refusée")
check(leve(sb.minterms, [0, 2]), "table entrée '2' refusée")
check(leve(sb.minterms, [0, True]), "table entrée bool refusée")
check(leve(sb.minterms, "01"), "table str refusée")

# variables : inconnue dans l'expression, doublon, mauvais type.
check(leve(sb.minimise, "a & z", ["a", "b"]), "variable inconnue 'z' refusée")
check(leve(sb.depuis_expression, "a & c", ["a", "b"]), "depuis_expression variable inconnue refusée")
check(leve(sb.minimise, "a", ["a", "a"]), "variables dupliquées refusées")
check(leve(sb.minimise, "a", [1]), "nom de variable non-str refusé")
check(leve(sb.minimise, "a", "a"), "variables str (non liste) refusé")
check(leve(sb.minimise, "a & (", ["a"]), "expression mal formée refusée")
check(leve(sb.nombre_litteraux, "a & ("), "nombre_litteraux mal formé refusé")

# couverture impossible : minterm non couvert par les implicants -> RuntimeError.
check(leve(sb.couverture_minimale, [(0, 0)], [0, 3]), "couverture impossible -> abstention")
check(leve(sb.couverture_minimale, [], [0]), "aucun implicant mais minterm -> abstention")
check(sb.couverture_minimale([], []) == [], "aucun implicant, aucun minterm -> []")

# ─────────────────────────────────────────────────────────────────────────────────────────────────
# DÉTERMINISME — deux appels identiques donnent le même résultat.
# ─────────────────────────────────────────────────────────────────────────────────────────────────
check(sb.minimise(canon, noms3) == sb.minimise(canon, noms3), "déterminisme minimise")
check(sb.impliquants_premiers(mt, 3) == sb.impliquants_premiers(mt, 3), "déterminisme impliquants_premiers")
check(sb.couverture_minimale(pis, mt) == sb.couverture_minimale(pis, mt), "déterminisme couverture_minimale")
check(sb.minterms([0, 1, 1, 0]) == sb.minterms([0, 1, 1, 0]), "déterminisme minterms")

# ─────────────────────────────────────────────────────────────────────────────────────────────────
# GARDE FAUX=0 : la vérification interne est réellement active (le résultat est équivalent à l'entrée).
#   On le prouve sur une famille : XOR à 3 variables (non représentable en moins que sa SOP complète).
# ─────────────────────────────────────────────────────────────────────────────────────────────────
r = sb.minimise("a ^ b ^ c", ["a", "b", "c"])
check(ab.equivalent("a ^ b ^ c", r), "XOR3 minimise équivalent (garde active)")
check(sb.nombre_litteraux(r) <= 12, f"XOR3 minimise <= 12 littéraux canoniques (obtenu {sb.nombre_litteraux(r)})")

print(f"\n=== valide_simplification_booleenne : {ok}/{ok+ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
