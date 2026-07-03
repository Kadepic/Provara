"""
VALIDATION du PROBLÈME DE PASCAL (pascal_mugging.py). Vérifie : l'agent EU NAÏF paie dès que la promesse est assez grande
et reste exploitable sans borne (pour toute demande D, un M assez grand le fait payer) ; l'utilité BORNÉE plafonne
l'espérance et fait refuser les promesses géantes ; la PÉNALITÉ DE LEVIER borne l'espérance (P·M ≤ c) ; HONNÊTETÉ : un
pari modéré et calibré reste accepté ; l'ABSTENTION. Pur Python déterministe.
"""
from __future__ import annotations

from garde_ressources import borne
import pascal_mugging as PM
from pascal_mugging import ABSTENTION, ANALYSE

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


eps, D = 1e-9, 5.0

# ─── 1. L'agent naïf est exploitable sans borne ───
print("=== L'agent EU naïf est exploitable sans borne ===")
st, info = PM.analyse(eps=eps, D=D)
check("le naïf paie la promesse la plus colossale", info["naif_paie_la_plus_grande"])
# pour toute demande D, un M assez grand le fait payer
check("pour D=1000, une promesse assez grande fait payer le naïf", PM.paye_naif(1e20, eps, 1000.0))
check("une fois qu'il paie, il paie pour TOUTE promesse plus grande (monotone)",
      all(PM.paye_naif(M, eps, D) for M in (1e15, 1e30, 1e100)))

# ─── 2. Utilité bornée : refuse les promesses géantes ───
print("=== Utilité bornée plafonne l'exploitation ===")
check("l'agent à utilité bornée refuse la promesse colossale", not info["borne_paie_la_plus_grande"])
check("son espérance est plafonnée à ε·U_max", PM.paye_borne(1e100, eps, 1e6, D) == (eps * 1e6 > D))

# ─── 3. Pénalité de levier : espérance bornée ───
print("=== Pénalité de levier borne l'espérance ===")
print(f"   EV levier max sur les promesses = {info['ev_levier_max']:.2f} (plafond c)")
check("l'agent à pénalité de levier refuse la promesse colossale", not info["levier_paie_la_plus_grande"])
check("l'espérance sous pénalité de levier est bornée (P·M ≤ c)", all(PM.proba_levier(M, eps, 1.0) * M <= 1.0 + 1e-9 for M in (1e9, 1e15, 1e30, 1e100)))
# l'EV plateaue à c pour M grand
check("l'EV de levier plafonne à c pour les grandes promesses", abs(PM.proba_levier(1e30, eps, 1.0) * 1e30 - 1.0) < 1e-6)

# ─── 4. Honnêteté : un pari modéré et calibré reste accepté ───
print("=== Honnêteté : pari modéré calibré ===")
# promesse vérifiable : ε=0.5 (calibrée), M=20, D=5 → ε·M=10 > 5 → payer est raisonnable
check("un pari calibré à espérance positive est accepté (pas de refus systématique)", PM.paye_naif(20, 0.5, 5.0))
check("le même pari sous utilité bornée reste accepté (M sous le plafond)", PM.paye_borne(20, 0.5, 1e6, 5.0))
check("formule signale la sur-confiance de l'EU à gains non bornés", "sur-confiant" in PM.formule((st, info)))

# ─── 5. ABSTENTION ───
print("=== ABSTENTION ===")
check("ε hors ]0,1[ → ABSTENTION", PM.analyse(eps=1.5)[0] == ABSTENTION)
check("D ≤ 0 → ABSTENTION", PM.analyse(D=-1.0)[0] == ABSTENTION)
check("cas valide → ANALYSE", st == ANALYSE)

print(f"\nRÉSULTAT pascal_mugging : {ok}/{total}")
assert ok == total
