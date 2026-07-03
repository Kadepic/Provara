"""VALIDATION fraicheur.py (Vague 8). FAUX=0 : jamais 'frais' par défaut ; atemporel jamais périmé ; a_rafraichir honnête."""
from __future__ import annotations
from fraicheur import FaitDate, a_rafraichir, frais

ok = 0; total = 0
def check(nom, cond):
    global ok, total; total += 1
    print(f"  [{'OK ' if cond else 'XXX'}] {nom}", flush=True)
    if cond: ok += 1
    else: raise AssertionError(nom)

# temps en "années" pour lisibilité ; maintenant = 2026
MAINT = 2026
pop = FaitDate("population_France", 68_000_000, as_of=2020, ttl=3)     # périmé (6 ans > 3)
prix = FaitDate("prix_baguette", 1.1, as_of=2025, ttl=2)              # frais (1 an <= 2)
c = FaitDate("vitesse_lumiere", 299792458, atemporel=True)           # constante -> jamais périmée

check("fait daté au-delà du TTL -> périmé", pop.est_perime(MAINT))
check("fait daté dans le TTL -> frais", not prix.est_perime(MAINT))
check("fait atemporel (constante) -> jamais périmé", not c.est_perime(MAINT))
check("age calculé", pop.age(MAINT) == 6)

# FAUX=0 : jamais 'frais' par défaut si as_of/ttl manquant
inconnu = FaitDate("x", 1)                                            # as_of/ttl None, non atemporel
check("fait daté-inconnu -> périmé (jamais frais par défaut)", inconnu.est_perime(MAINT))

faits = [pop, prix, c, inconnu]
ar = a_rafraichir(faits, MAINT)
check("a_rafraichir liste population + inconnu (périmés)", set(f.cle for f in ar) == {"population_France", "x"})
check("frais liste prix + constante", set(f.cle for f in frais(faits, MAINT)) == {"prix_baguette", "vitesse_lumiere"})

# le temps est explicite (déterministe) : à une date antérieure, la population était encore fraîche
check("déterminisme temporel : en 2022, population encore fraîche (2 ans <= 3)", not pop.est_perime(2022))

print(f"\n=== valide_fraicheur : {ok}/{total} checks OK ===")
if ok != total: raise SystemExit(1)
