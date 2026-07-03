"""
VALIDATION du THÉORÈME NO FREE LUNCH (no_free_lunch.py). Vérifie : moyennés sur TOUTES les fonctions cibles, tous les
apprenants ont EXACTEMENT la même erreur hors-échantillon (0.5) ; sur une classe STRUCTURÉE (constantes) un biais adapté
est parfait alors que d'autres non ; l'avantage sur une classe est EXACTEMENT compensé sur le complément ; l'opposé du
bon apprenant est le pire sur cette classe ; l'ABSTENTION. Pur Python (énumération exacte, déterministe).
"""
from __future__ import annotations

import itertools

from garde_ressources import borne
import no_free_lunch as NFL
from no_free_lunch import ABSTENTION, ANALYSE

borne()
ok = 0
total = 0


def check(nom, cond):
    global ok, total
    total += 1
    print(f"  [{'OK ' if cond else 'XXX'}] {nom}", flush=True)
    if cond:
        ok += 1
    else:
        raise AssertionError(nom)


N, train, test = 5, [0, 1], [2, 3, 4]
st, info = NFL.analyse(N, tuple(train), tuple(test))

# ─── 1. Tous les apprenants ont la même erreur moyenne (0.5) sur toutes les fonctions ───
print("=== No Free Lunch : égalité sur toutes les fonctions ===")
moy = info["moyennes"]
print(f"   erreurs moyennes : {({k: round(v,3) for k,v in moy.items()})}")
check("tous les apprenants ont une erreur moyenne de 0.5 (NFL)", all(abs(v - 0.5) < 1e-12 for v in moy.values()))
check("aucun apprenant ne bat les autres en moyenne sur toutes les fonctions", len(set(round(v, 9) for v in moy.values())) == 1)

# ─── 2. Sur une classe structurée, un biais adapté gagne ───
print("=== Sur une classe structurée (constantes) ===")
sc = info["sur_constantes"]
print(f"   sur constantes : {({k: round(v,3) for k,v in sc.items()})}")
check("« majorité » est parfait sur les fonctions constantes", abs(sc["majorité"]) < 1e-12)
check("« constant0 » n'est pas parfait sur les constantes", sc["constant0"] > 0.4)
check("« opposé_majorité » est le PIRE sur les constantes (miroir)", abs(sc["opposé_majorité"] - 1.0) < 1e-12)

# ─── 3. L'avantage sur les constantes est EXACTEMENT compensé sur le complément ───
print("=== Compensation exacte sur le complément ===")
constantes = [tuple([v] * N) for v in (0, 1)]
non_const = [f for f in itertools.product([0, 1], repeat=N) if f not in constantes]
err_maj_complement = NFL.erreur_sur_classe(NFL.APPRENANTS["majorité"], non_const, train, test)
print(f"   « majorité » : sur constantes={sc['majorité']:.3f} ; sur non-constantes={err_maj_complement:.3f}")
check("« majorité » fait PIRE que 0.5 sur le complément (compense son avantage)", err_maj_complement > 0.5)
# vérif de la moyenne pondérée = 0.5
moy_reconstituee = (sc["majorité"] * len(constantes) + err_maj_complement * len(non_const)) / (2 ** N)
check("la moyenne pondérée (constantes + complément) redonne 0.5", abs(moy_reconstituee - 0.5) < 1e-9)

# ─── 4. Honnêteté & formule ───
print("=== Honnêteté : un biais adapté aide sur un monde structuré ===")
check("sur un monde structuré (constantes), l'apprentissage est possible (majorité parfait)", sc["majorité"] < sc["constant0"])
check("formule signale la sur-confiance de la supériorité universelle", "sur-confiant" in NFL.formule((st, info)))

# ─── 5. ABSTENTION ───
print("=== ABSTENTION ===")
check("domaine trop petit → ABSTENTION", NFL.analyse(N=2)[0] == ABSTENTION)
check("partition invalide → ABSTENTION", NFL.analyse(N=5, train=(0, 9))[0] == ABSTENTION)
check("cas valide → ANALYSE", st == ANALYSE)

print(f"\nRÉSULTAT no_free_lunch : {ok}/{total}")
assert ok == total
