#!/usr/bin/env python3
"""VALIDE le MÉCANISME d'audit des ancres (audit_ancres.py) — FAUX=0 sur le diagnostic lui-même.

On ne teste PAS que la couverture d'ancrage est de 100 % (ce serait un gate rouge à perpétuité) : on teste que
l'OUTIL de mesure est SOUND — partition exacte référencées/non-référencées, tri décroissant, relations à validateur
dédié classées « référencées », et la propriété de sur-approximation (le proxy ne produit pas de faux « non-ancré »
sur une relation manifestement ancrée). LÉGER : audit_ancres ne charge pas le lecteur (listdir + comptage d'octets).
"""
import os
import sys

_ICI = os.path.dirname(os.path.abspath(__file__)) or "."
sys.path.insert(0, _ICI)

import audit_ancres as AA

ok = 0
ko = 0


def check(c, l):
    global ok, ko
    if c:
        ok += 1
    else:
        ko += 1
        print(f"  FAIL: {l}")


r = AA.audit(details=True)          # UN seul scan du store (~4 Go d'octets) ; on réutilise tout ci-dessous
tailles = r["tailles"]
refs = r["referencees_set"]

# ── cohérence structurelle ──
check(r["total_relations"] > 1000, f"inventaire non trivial ({r['total_relations']} relations)")
check(r["referencees"] + r["non_referencees"] == r["total_relations"],
      "partition EXACTE : référencées + non-référencées == total (aucune relation perdue/comptée deux fois)")
check(r["total_faits"] > 10_000_000, f"volume de faits plausible ({r['total_faits']:,})")
check(0 <= r["faits_non_references"] <= r["total_faits"], "faits non couverts dans [0, total]")

# ── tri décroissant du top ──
top = r["top_non_references"]
check(all(top[i][1] >= top[i + 1][1] for i in range(len(top) - 1)), "top non-références trié par volume décroissant")
check(len(top) == r["non_referencees"], "le top liste TOUTES les non-référencées (pas une troncature silencieuse)")

# ── relations à VALIDATEUR DÉDIÉ -> forcément « référencées » (sinon le proxy a un faux « non-ancré ») ──
ANCREES_SURES = ["capitale", "numero_atomique", "pib_pays", "population_pays", "latitude_capitale",
                 "esperance_vie_pays", "indice_gini_pays"]
noms_top = {rel for rel, _ in top}
for rel in ANCREES_SURES:
    if rel in tailles:                          # on ne teste que celles présentes sur disque
        check(rel in refs, f"« {rel} » (validateur dédié) classée référencée")
        check(rel not in noms_top, f"« {rel} » absente de la liste des non-ancrées (pas de faux non-ancré)")

# ── propriété de sur-approximation : une relation non-référencée n'apparaît dans AUCUN valide_*.py ──
# (échantillon : la plus grosse non-référencée ne doit pas figurer, délimitée, dans un validateur)
if top:
    grosse = top[0][0]
    import re
    motif = re.compile(r"(?<![a-z0-9_])" + re.escape(grosse) + r"(?![a-z0-9_])")
    trouve = False
    for f in os.listdir(_ICI):
        if f.startswith("valide_") and f.endswith(".py"):
            with open(os.path.join(_ICI, f), encoding="utf-8") as fh:
                if motif.search(fh.read()):
                    trouve = True
                    break
    check(not trouve, f"cohérence proxy : la non-référencée « {grosse} » n'apparaît dans aucun validateur")

# ── déterminisme : le classement des références est stable (sans re-scanner les 4 Go d'octets) ──
refs2 = AA._relations_referencees(set(tailles))
check(refs2 == refs, "audit déterministe (même store -> même ensemble de relations référencées)")

print(f"\n=== valide_audit_ancres : {ok}/{ok + ko} ===")
sys.exit(0 if ko == 0 else 1)
