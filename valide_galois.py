"""VALIDE galois.py — held-out ADVERSE, FAUX=0. Ancres = théorèmes/valeurs de référence (Abel-Ruffini, résolubilité
de Sₙ/Aₙ, φ(n) connus, groupes de Galois catalogués) + SOUNDNESS (entrée invalide/inconnue -> ValueError) +
déterminisme. On ne recalcule PAS une ancre par la formule testée : valeurs de référence externes connues.
"""
import galois as G

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
    try:
        fn(*a)
        return False
    except ValueError:
        return True
    except Exception:
        return False


# ── RÉSOLUBILITÉ PAR RADICAUX (polynôme général) — Abel-Ruffini / Cardan / Ferrari ────────────────────────────────
for d in (1, 2, 3, 4):
    check(G.resoluble_par_radicaux(d) is True, f"degré {d} général résoluble (Cardan/Ferrari)")
for d in (5, 6, 7, 10, 100):
    check(G.resoluble_par_radicaux(d) is False, f"degré {d} général NON résoluble (Abel-Ruffini)")

# ── RÉSOLUBILITÉ DE Sₙ — résoluble ssi n ≤ 4 ─────────────────────────────────────────────────────────────────────
for n in (1, 2, 3, 4):
    check(G.groupe_resoluble(n) is True, f"S{n} résoluble")
    check(G.groupe_symetrique_resoluble(n) is True, f"S{n} résoluble (alias)")
for n in (5, 6, 7):
    check(G.groupe_resoluble(n) is False, f"S{n} NON résoluble")
check(G.groupe_resoluble(4) is True and G.groupe_resoluble(5) is False, "frontière S4/S5 (cas central)")

# ── RÉSOLUBILITÉ DE Aₙ — résoluble ssi n ≤ 4 (A5 simple non abélien) ──────────────────────────────────────────────
for n in (1, 2, 3, 4):
    check(G.groupe_alterne_resoluble(n) is True, f"A{n} résoluble")
for n in (5, 6, 7):
    check(G.groupe_alterne_resoluble(n) is False, f"A{n} NON résoluble")

# ── ORDRES |Sₙ|=n!, |Aₙ|=n!/2 (références externes) ───────────────────────────────────────────────────────────────
for n, val in [(0, 1), (1, 1), (2, 2), (3, 6), (4, 24), (5, 120), (6, 720)]:
    check(G.ordre_groupe_symetrique(n) == val, f"|S{n}| = {val}")
for n, val in [(0, 1), (1, 1), (2, 1), (3, 3), (4, 12), (5, 60), (6, 360)]:
    check(G.ordre_groupe_alterne(n) == val, f"|A{n}| = {val}")

# ── ORDRE DU GROUPE DE GALOIS — cyclotomique φ(n) (table de référence externe) ────────────────────────────────────
PHI = {1: 1, 2: 1, 3: 2, 4: 2, 5: 4, 6: 2, 7: 6, 8: 4, 9: 6, 10: 4, 12: 4, 15: 8, 100: 40}
for n, val in PHI.items():
    check(G.indicatrice_euler(n) == val, f"φ({n}) = {val}")
    check(G.ordre_groupe_galois_cyclotomique(n) == val, f"|Gal(Q(ζ{n})/Q)| = φ({n}) = {val}")
    check(G.ordre_groupe_galois("cyclotomique", n) == val, f"dispatcher cyclotomique n={n} -> {val}")

# ── ORDRE DU GROUPE DE GALOIS — quadratique = 2 ──────────────────────────────────────────────────────────────────
check(G.ordre_groupe_galois_quadratique() == 2, "|Gal(Q(√d)/Q)| = 2")
check(G.ordre_groupe_galois("quadratique") == 2, "dispatcher quadratique -> 2")
check(G.ordre_groupe_galois_quadratique(2) == 2, "Q(√2) ordre 2")
check(G.ordre_groupe_galois_quadratique(-1) == 2, "Q(i) (√-1) ordre 2")
check(G.ordre_groupe_galois_quadratique(8) == 2, "Q(√8)=Q(√2) non carré ordre 2")

# ── CATALOGUE de polynômes concrets (faits établis) ──────────────────────────────────────────────────────────────
check(G.resoluble_polynome("x^5 - x - 1") is False, "x^5-x-1 : groupe S5, NON résoluble")
check(G.groupe_galois_polynome("x^5 - x - 1") == "S5", "x^5-x-1 : groupe = S5")
check(G.ordre_galois_polynome("x^5 - x - 1") == 120, "x^5-x-1 : |groupe| = 120")
check(G.resoluble_polynome("x^2 - 2") is True, "x^2-2 résoluble (Z/2Z)")
check(G.ordre_galois_polynome("x^2 - 2") == 2, "x^2-2 : ordre 2")
check(G.resoluble_polynome("x^3 - 2") is True, "x^3-2 résoluble (S3)")
check(G.ordre_galois_polynome("x^3 - 2") == 6, "x^3-2 : ordre 6 (S3)")
check(G.resoluble_polynome("x^4 - 2") is True, "x^4-2 résoluble (D4)")
check(G.ordre_galois_polynome("x^4 - 2") == 8, "x^4-2 : ordre 8 (D4)")
check(G.resoluble_polynome("x^5 - 2") is True, "x^5-2 résoluble (F20 métacyclique)")
check(G.ordre_galois_polynome("x^5 - 2") == 20, "x^5-2 : ordre 20")
check(G.groupe_galois_polynome("X^5-X-1") == "S5", "normalisation casse/espaces")
check(len(G.catalogue_polynomes()) == 5, "catalogue = 5 polynômes")

# ── DÉTERMINISME ─────────────────────────────────────────────────────────────────────────────────────────────────
check(G.resoluble_par_radicaux(5) == G.resoluble_par_radicaux(5), "déterminisme resoluble_par_radicaux")
check(G.indicatrice_euler(100) == G.indicatrice_euler(100), "déterminisme φ")
check(G.ordre_galois_polynome("x^5-x-1") == G.ordre_galois_polynome("x^5 - x - 1"), "déterminisme catalogue")

# ── SOUNDNESS — entrée invalide/inconnue -> ValueError (faux positif INTERDIT) ────────────────────────────────────
check(leve(G.resoluble_par_radicaux, 0), "degré 0 -> ValueError")
check(leve(G.resoluble_par_radicaux, -3), "degré négatif -> ValueError")
check(leve(G.resoluble_par_radicaux, 2.0), "degré flottant -> ValueError")
check(leve(G.resoluble_par_radicaux, True), "degré bool -> ValueError")
check(leve(G.groupe_resoluble, 0), "S0 demandé (n<1) -> ValueError")
check(leve(G.groupe_alterne_resoluble, 0), "A0 demandé (n<1) -> ValueError")
check(leve(G.indicatrice_euler, 0), "φ(0) -> ValueError")
check(leve(G.indicatrice_euler, -5), "φ(négatif) -> ValueError")
check(leve(G.ordre_groupe_symetrique, -1), "|S(-1)| -> ValueError")
check(leve(G.ordre_groupe_galois_cyclotomique, 0), "Gal cyclotomique n=0 -> ValueError")
check(leve(G.ordre_groupe_galois, "cyclotomique"), "cyclotomique sans n -> ValueError")
check(leve(G.ordre_groupe_galois, "cubique", 3), "famille inconnue -> ValueError")
check(leve(G.ordre_groupe_galois, 7), "famille non-chaîne -> ValueError")
check(leve(G.ordre_groupe_galois_quadratique, 4), "radicande carré parfait -> ValueError (Q(√4)=Q)")
check(leve(G.ordre_groupe_galois_quadratique, 0), "radicande 0 -> ValueError")
check(leve(G.ordre_groupe_galois_quadratique, 1), "radicande 1 (carré) -> ValueError")
check(leve(G.resoluble_polynome, "x^6 - 7"), "polynôme hors catalogue -> ValueError (abstention)")
check(leve(G.resoluble_polynome, "x^5 + x + 1"), "x^5+x+1 (≠ catalogué) -> ValueError")
check(leve(G.groupe_galois_polynome, ""), "polynôme vide -> ValueError")
check(leve(G.ordre_galois_polynome, 42), "polynôme non-chaîne -> ValueError")

print(f"\n=== valide_galois : {ok}/{ok + ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
