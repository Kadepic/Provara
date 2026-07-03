"""VALIDATION abstention.py (Vague 7). FAUX=0 : défaut ABSTENTION ; HORS domine ; confiance None ne franchit pas le seuil."""
from __future__ import annotations
from abstention import decide, affirme_ou_abstient, VERIFIE, ABSTENTION, HORS

ok = 0; total = 0
def check(nom, cond):
    global ok, total; total += 1
    print(f"  [{'OK ' if cond else 'XXX'}] {nom}", flush=True)
    if cond: ok += 1
    else: raise AssertionError(nom)

check("preuve + confiance haute -> VERIFIE", decide(preuve=True, confiance=0.9, seuil=0.5) == VERIFIE)
check("pas de preuve -> ABSTENTION (défaut)", decide(preuve=False) == ABSTENTION)
check("confiance sous le seuil -> ABSTENTION", decide(preuve=True, confiance=0.3, seuil=0.5) == ABSTENTION)
check("confiance None -> ABSTENTION (ignorance != confiance)", decide(preuve=True, confiance=None, seuil=0.5) == ABSTENTION)
check("contradiction -> HORS (domine)", decide(preuve=True, confiance=0.99, contradiction=True) == HORS)
check("impossible -> HORS (domine, même avec preuve+confiance)", decide(preuve=True, confiance=1.0, impossible=True) == HORS)
check("HORS l'emporte sur l'abstention (impossible sans preuve)", decide(preuve=False, impossible=True) == HORS)
check("défaut absolu (aucun argument) -> ABSTENTION", decide() == ABSTENTION)

# affirme_ou_abstient
check("affirme la réponse si VERIFIE", affirme_ou_abstient("Paris", preuve=True, confiance=0.8) == "Paris")
check("renvoie ABSTENTION si preuve insuffisante", affirme_ou_abstient("Paris", preuve=False) == ABSTENTION)
check("renvoie HORS si impossible (jamais la réponse)", affirme_ou_abstient("Paris", preuve=True, confiance=1.0, impossible=True) == HORS)

print(f"\n=== valide_abstention : {ok}/{total} checks OK ===")
if ok != total: raise SystemExit(1)
