"""
VALIDATION de l'EFFET DE CADRAGE (cadrage.py). Vérifie : les deux cadres décrivent des loteries IDENTIQUES (même
espérance, équivalence sauvés/morts) ; l'agent de prospect RENVERSE sa préférence (sûr en gain, risqué en perte) ;
l'agent frame-INVARIANT ne renverse pas ; le renversement est exploitable (money pump) ; une valeur LINÉAIRE/cohérente
ne renverse pas (le renversement vient de la courbure + aversion aux pertes) ; l'ABSTENTION. Pur Python déterministe.
"""
from __future__ import annotations

from garde_ressources import borne
import cadrage as C
from cadrage import ABSTENTION, ANALYSE

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


# ─── 1. Les deux cadres = loteries identiques ───
print("=== Cadres GAIN et PERTE = loteries identiques ===")
e_sur = sum(p * x for p, x in C.SUR)
e_risque = sum(p * x for p, x in C.RISQUE)
print(f"   E[sauvés] : sûr={e_sur:.0f} ; risqué={e_risque:.0f}")
check("le sûr et le risqué ont la même espérance de sauvés (200)", abs(e_sur - e_risque) < 1e-9)
check("« 200 sauvés à coup sûr » ≡ « 400 morts à coup sûr »", C.TOTAL - e_sur == 400)

# ─── 2. L'agent de prospect RENVERSE ───
print("=== L'agent de prospect renverse ===")
st, info = C.analyse()
print(f"   cadre gain → {info['choix_cadre_gain']} ; cadre perte → {info['choix_cadre_perte']}")
check("cadre GAIN : choisit le SÛR (aversion au risque)", info["choix_cadre_gain"] == "sur")
check("cadre PERTE : choisit le RISQUÉ (recherche de risque)", info["choix_cadre_perte"] == "risque")
check("la préférence S'INVERSE sous reformulation (effet de cadrage)", info["renversement"])

# ─── 3. L'agent frame-INVARIANT ne renverse pas ───
print("=== L'agent frame-invariant est cohérent ===")
print(f"   invariant : gain={info['choix_invariant_gain']} ; perte={info['choix_invariant_perte']}")
check("l'agent à utilité frame-invariante fait le même choix dans les deux cadres", info["choix_invariant_gain"] == info["choix_invariant_perte"])

# ─── 4. Exploitabilité : money pump ───
print("=== Exploitabilité (money pump) ===")
print(f"   étapes payantes = {info['etapes_money_pump']}")
check("le renversement rend l'agent exploitable (money pump = 2 étapes)", info["etapes_money_pump"] == 2)
check("formule signale la sur-confiance de la préférence cadrée", "sur-confiant" in C.formule((st, info)))

# ─── 5. Honnêteté : une valeur cohérente (linéaire, sans aversion aux pertes) ne renverse pas ───
print("=== Honnêteté : valeur linéaire cohérente ne renverse pas ===")
cg_lin = C.choix_prospect(0, alpha=1.0, beta=1.0, lam=1.0)
cp_lin = C.choix_prospect(C.TOTAL, alpha=1.0, beta=1.0, lam=1.0)
print(f"   linéaire : gain={cg_lin} ; perte={cp_lin}")
check("sans courbure ni aversion aux pertes, pas de renversement", cg_lin == cp_lin)
check("le money pump disparaît pour la valeur linéaire", C.money_pump(alpha=1.0, beta=1.0, lam=1.0) == 0)

# ─── 6. Le renversement s'accentue avec l'aversion aux pertes ───
print("=== L'aversion aux pertes alimente le renversement ===")
# avec une forte aversion aux pertes le renversement persiste ; en la retirant (lam=1, convexité douce) il peut cesser
check("renversement présent avec λ=2.25 (aversion aux pertes réaliste)", C.money_pump(lam=2.25) == 2)

# ─── 7. ABSTENTION ───
print("=== ABSTENTION & façade ===")
check("cas valide → ANALYSE", st == ANALYSE)
check("la façade expose le renversement", info["renversement"] is True)

print(f"\nRÉSULTAT cadrage : {ok}/{total}")
assert ok == total
