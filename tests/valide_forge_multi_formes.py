"""
VALIDATION — FORGE × FORMES HÉTÉROGÈNES : le câblage INTÉGRÉ de ia.forge_brique_multi sur les formes de type
(palier structurel, atome 6) — « vérifier l'intégré, pas l'isolé ».

Défaut d'intégration MESURÉ puis corrigé : la façade passait `existant = registre appris` (semé des bases
SCALAIRES) à examine_cible_multi, ÉCRASANT le registre de FORME — via la façade, une primitive de forme
(a.count(b), d[k]) passait pour « comportement nouveau » (fausse revendication de nouveauté), alors que le
moteur seul la classait EXISTE_DEJA. Correctif = patron mono (store semé du registre complet) : UNION
registre de la forme détectée ∪ appris, l'appris prioritaire par nom.

Prouve : (1) NOUVEAUTÉ HONNÊTE — une primitive liste×scalaire (count) et une dict×scalaire (lookup) restent
EXISTE_DEJA via la façade ; (2) CHAÎNE COMPLÈTE sur forme hétérogène — INVENTION avec rétention (appris),
force_spec (mutation testing sur args non-scalaires) et MATÉRIALISATION dont la gate se re-prouve SEULE ;
(3) SELF-IMPROVING — la brique retenue est ensuite SERVIE (EXISTE_DEJA, code identique) ; (4) SERVABLE —
sortie JSON-sérialisable ; (5) NON-RÉGRESSION — le chemin int×int de la façade ne bouge pas.
"""
from __future__ import annotations

import glob
import json
import os
import subprocess
import sys
import tempfile

from garde_ressources import borne
borne(max_cpu_s=400)
import ia
import invention_multi as IM

ok = total = 0


def check(nom, cond):
    global ok, total
    total += 1
    print(f"  [{'OK ' if cond else 'XXX'}] {nom}")
    if cond:
        ok += 1
    else:
        raise AssertionError(nom)


HB = [(([3, 1, 4, 1, 5], 2), [3, 1]), (([2, 7, 6], 1), [2]), (([9, 8, 5, 3], 3), [9, 8, 5])]
HB_HELD = [(([1, 2, 3, 4, 5, 6], 4), [1, 2, 3, 4])]

# (1) NOUVEAUTÉ HONNÊTE : les primitives des formes restent EXISTE_DEJA via la FAÇADE.
r = ia.forge_brique_multi("compte_occurrences_forge",
                          [(([3, 1, 3, 3], 3), 3), (([2, 7, 6], 7), 1), (([4, 4], 5), 0)],
                          [(([1, 1, 2], 1), 2)])
check("primitive liste×scalaire (count) : EXISTE_DEJA via la façade (pas de fausse nouveauté)",
      r["statut"] == IM.EXISTE_DEJA and r["code"] == "a.count(b)")
r = ia.forge_brique_multi("valeur_de_cle_forge",
                          [(({"a": 3, "b": 1}, "a"), 3), (({"x": 5, "z": 9}, "z"), 9), (({"m": 7}, "m"), 7)],
                          [(({"u": 6, "v": 1}, "v"), 1)])
check("primitive dict×scalaire (lookup) : EXISTE_DEJA via la façade",
      r["statut"] == IM.EXISTE_DEJA and r["code"] == "a[b]")

# (2) CHAÎNE COMPLÈTE sur forme hétérogène : invention + rétention + force_spec + matérialisation auto-prouvée.
with tempfile.TemporaryDirectory() as d:
    r = ia.forge_brique_multi("n_premiers_forge", HB, HB_HELD, dossier=d)
    check("liste×scalaire : INVENTION complète (code + appris + force_spec + matérialisé)",
          r["statut"] == IM.INVENTION and r["code"] == "a[:b]" and r["appris"] is True
          and r["force_spec"] is not None and r["materialise"] is not None)
    gates = glob.glob(os.path.join(d, "valide_*.py"))
    check("matérialisation : .py + gate présents", len(gates) == 1 and os.path.exists(os.path.join(d, "n_premiers_forge.py")))
    p = subprocess.run([sys.executable, gates[0]], capture_output=True, text=True, timeout=120)
    check("la gate matérialisée se RE-PROUVE seule (args liste×scalaire)", p.returncode == 0)

# (3) SELF-IMPROVING : la brique retenue est SERVIE au prochain besoin identique.
r2 = ia.forge_brique_multi("n_premiers_rappel", HB, HB_HELD)
check("rappel : la brique apprise est servie (EXISTE_DEJA, code identique)",
      r2["statut"] == IM.EXISTE_DEJA and r2["code"] == "a[:b]")

# (4) SERVABLE + chaîne dict×scalaire.
D = [(({"a": 3, "b": 1}, "a"), {"b": 1}), (({"x": 5, "y": 2, "z": 9}, "z"), {"x": 5, "y": 2}),
     (({"m": 7, "n": 4}, "n"), {"m": 7})]
D_HELD = [(({"u": 6, "v": 1, "w": 3}, "v"), {"u": 6, "w": 3})]
r3 = ia.forge_brique_multi("retire_cle_forge", D, D_HELD)
check("dict×scalaire : INVENTION retenue via la façade",
      r3["statut"] == IM.INVENTION and r3["appris"] is True)
check("sortie JSON-sérialisable (servable inter-moteurs)", json.dumps(r3) is not None)

# (5) ARITÉ 3 HÉTÉROGÈNE de bout en bout (atome 19) : invention retenue + matérialisée + rappelée ;
# la primitive du registre de forme reste EXISTE_DEJA via la façade.
RI = [(("le chat dort", "chien", "chat"), "le chien dort"), (("aaa", "b", "a"), "bbb"), (("xyz", "", "y"), "xz")]
RIH = [(("bord de mer", "lac", "mer"), "bord de lac")]
with tempfile.TemporaryDirectory() as d:
    r5 = ia.forge_brique_multi("remplace_inverse_forge", RI, RIH, dossier=d)
    check("arité 3 hét. : INVENTION complète (a.replace(c, b), appris + matérialisé)",
          r5["statut"] == IM.INVENTION and r5["code"] == "a.replace(c, b)"
          and r5["appris"] is True and r5["materialise"] is not None)
    gates3 = glob.glob(os.path.join(d, "valide_*.py"))
    p = subprocess.run([sys.executable, gates3[0]], capture_output=True, text=True, timeout=120)
    check("arité 3 hét. : la gate matérialisée se re-prouve seule", p.returncode == 0)
r6 = ia.forge_brique_multi("remplace_inverse_rappel", RI, RIH)
check("arité 3 hét. : rappel self-improving (EXISTE_DEJA, code identique)",
      r6["statut"] == IM.EXISTE_DEJA and r6["code"] == "a.replace(c, b)")
r7 = ia.forge_brique_multi("remplace_forge",
                           [(("le chat dort", "chat", "chien"), "le chien dort"), (("aaa", "a", "b"), "bbb"),
                            (("xyz", "y", ""), "xz")],
                           [(("bord de mer", "mer", "lac"), "bord de lac")])
check("arité 3 hét. : la primitive (a.replace(b, c)) reste EXISTE_DEJA via la façade",
      r7["statut"] == IM.EXISTE_DEJA and r7["code"] == "a.replace(b, c)")

# (6) NON-RÉGRESSION : le chemin int×int de la façade ne bouge pas.
r4 = ia.forge_brique_multi("difference_forge", [((7, 2), 5), ((9, 4), 5), ((3, 1), 2)], [((10, 6), 4)])
check("int×int : difference reste EXISTE_DEJA via la façade", r4["statut"] == IM.EXISTE_DEJA and r4["code"] == "a - b")

print(f"\nvalide_forge_multi_formes : {ok}/{total}")
assert ok == total
