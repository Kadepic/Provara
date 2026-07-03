"""
VALIDE scrutin.py — held-out ADVERSE.

Ancres CONNUES (vérifiées À LA MAIN, pas recalculées par la même expression) :
  • D'Hondt A=100,B=80,C=30 / 5 sièges -> A=3,B=2,C=0 (quotients 100,80,50,40,100/3).
  • Sainte-Laguë même scrutin -> A=2,B=2,C=1 (quotients 100,80,100/3,30,80/3) : les DEUX méthodes diffèrent,
    donc ce n'est pas la même formule renommée.
  • majorité absolue = strictement > 50 %.
SOUNDNESS : siège <= 0, voix négative/flottante/booléenne, dict vide, total <= 0, voix > total, et surtout
ÉGALITÉ de quotient au seuil entre partis distincts -> ValueError (jamais un siège inventé). Aucun de ces cas
n'est codé en dur dans scrutin.py : le mécanisme les produit.
"""
import scrutin as S

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
    try:
        fn(*a, **k)
        return False
    except ValueError:
        return True
    except Exception:
        return False


# ── 1) ANCRE D'HONDT (énoncé, vérifiée à la main) ──
check(S.dhondt({"A": 100, "B": 80, "C": 30}, 5) == {"A": 3, "B": 2, "C": 0}, "D'Hondt 100/80/30·5 -> 3/2/0")
check(sum(S.dhondt({"A": 100, "B": 80, "C": 30}, 5).values()) == 5, "D'Hondt conserve 5 sièges")

# ── 2) ANCRE SAINTE-LAGUË (diffère de D'Hondt) ──
check(S.sainte_lague({"A": 100, "B": 80, "C": 30}, 5) == {"A": 2, "B": 2, "C": 1}, "Sainte-Laguë -> 2/2/1")
check(S.dhondt({"A": 100, "B": 80, "C": 30}, 5) != S.sainte_lague({"A": 100, "B": 80, "C": 30}, 5),
      "les deux méthodes diffèrent réellement")

# ── 3) AUTRES répartitions hand-checkables ──
check(S.dhondt({"A": 100}, 3) == {"A": 3}, "parti unique prend tous les sièges")
check(S.dhondt({"A": 10, "B": 4}, 2) == {"A": 2, "B": 0},
      "D'Hondt 10/4·2 : quotients 10,5(A),4(B) -> 2/0")
check(S.sainte_lague({"A": 10, "B": 4}, 2) == {"A": 1, "B": 1},
      "Sainte-Laguë 10/4·2 : quotients 10,4,3.33 -> 1/1")
check(S.dhondt({"A": 100, "B": 0}, 3) == {"A": 3, "B": 0}, "parti à 0 voix n'a aucun siège")
check(sum(S.dhondt({"P1": 47, "P2": 33, "P3": 12, "P4": 8}, 11).values()) == 11, "11 sièges conservés")

# ── 4) QUOTIENT DE HARE & MAJORITÉ ABSOLUE ──
check(S.quotient_hare(1000, 10) == 100.0, "Hare 1000/10 = 100")
check(S.quotient_hare(600, 4) == 150.0, "Hare 600/4 = 150")
check(S.majorite_absolue(60, 100) is True, "60/100 = majorité absolue")
check(S.majorite_absolue(51, 100) is True, "51/100 = majorité absolue")
check(S.majorite_absolue(50, 100) is False, "50/100 (pile la moitié) -> PAS majorité absolue")
check(S.majorite_absolue(51, 101) is True, "51/101 > 50.5 -> majorité")
check(S.majorite_absolue(50, 101) is False, "50/101 < 50.5 -> pas majorité")

# ── 5) SOUNDNESS — répartition ──
check(leve(S.dhondt, {"A": 1}, 0), "n_sieges=0 -> ValueError")
check(leve(S.dhondt, {"A": 1}, -3), "n_sieges<0 -> ValueError")
check(leve(S.dhondt, {}, 5), "dict de voix vide -> ValueError")
check(leve(S.dhondt, {"A": -1}, 5), "voix négative -> ValueError")
check(leve(S.dhondt, {"A": 10.5}, 5), "voix flottante -> ValueError")
check(leve(S.dhondt, {"A": True}, 5), "voix booléenne -> ValueError")
check(leve(S.dhondt, {"A": 10}, True), "n_sieges booléen -> ValueError")
check(leve(S.sainte_lague, {"A": -1}, 5), "Sainte-Laguë voix négative -> ValueError")

# ── 6) SOUNDNESS — ÉGALITÉ non mécanique au seuil (le mécanisme refuse d'inventer) ──
check(leve(S.dhondt, {"A": 100, "B": 100}, 1), "ex æquo 100/100 pour 1 siège -> ValueError (départage)")
check(leve(S.sainte_lague, {"A": 100, "B": 100}, 1), "ex æquo Sainte-Laguë 1 siège -> ValueError")
check(leve(S.dhondt, {"A": 100, "B": 50}, 2),
      "ex æquo 2e siège (A:50 vs B:50) -> ValueError (départage)")
# … mais ex æquo de partis distincts sans contestation (assez de sièges) ne lève PAS :
check(S.dhondt({"A": 100, "B": 100}, 2) == {"A": 1, "B": 1}, "2 partis 100/100·2 sièges -> 1/1 (non contesté)")

# ── 7) SOUNDNESS — quotient / majorité ──
check(leve(S.quotient_hare, 1000, 0), "Hare n_sieges=0 -> ValueError")
check(leve(S.quotient_hare, -1, 10), "Hare total négatif -> ValueError")
check(leve(S.majorite_absolue, -1, 100), "majorité voix négative -> ValueError")
check(leve(S.majorite_absolue, 10, 0), "majorité total=0 -> ValueError")
check(leve(S.majorite_absolue, 10, -5), "majorité total négatif -> ValueError")
check(leve(S.majorite_absolue, 101, 100), "voix > total -> ValueError")

# ── 8) DÉTERMINISME ──
check(S.dhondt({"A": 100, "B": 80, "C": 30}, 5) == S.dhondt({"A": 100, "B": 80, "C": 30}, 5),
      "D'Hondt déterministe")
check(S.sainte_lague({"X": 7, "Y": 3}, 4) == S.sainte_lague({"X": 7, "Y": 3}, 4), "Sainte-Laguë déterministe")

print(f"\n=== valide_scrutin : {ok}/{ok+ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
