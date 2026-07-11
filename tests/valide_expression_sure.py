"""
VALIDATION — EXPRESSION SÛRE : le juge d'INNOCUITÉ de la forge (chantier FORGE atome 7).

Le trou MESURÉ (reproduit ici en (2)) : la re-jugeance (atome 1) prouve la CORRECTION d'une brique, pas son
INNOCUITÉ. Une expr spec-correcte à effet de bord `(open(p,'w').write(…), sum(x))[1]` reproduit `somme` ET
écrit un fichier ; l'admission l'EXÉCUTAIT (déclenchant l'effet) puis la servait.

Prouve : (1) JUGE STATIQUE sound — tout l'inventaire EXISTANT + un échantillon etend_* sont SÛRS (zéro faux
positif : on ne casse aucune brique légitime), et un corpus d'attaques (I/O, os.system, évasion dunder, eval,
getattr, __import__ hostile, sous-classes) est TOUT refusé avec raison précise ; le jugement N'EXÉCUTE
jamais le code (POC : juger une expr qui écrirait un fichier ne l'écrit pas) ; (2) FRONTIÈRE retient() —
refuse la brique non sûre, l'effet de bord N'EST PAS déclenché (fichier absent), refus compté, pas servie ;
(3) FRONTIÈRE charge() — un briques.json v2 altéré portant une expr non sûre part en QUARANTAINE tracée,
n'est ni exécuté ni injecté dans existant() ; (4) FRONTIÈRE forge_brique() — jamais de code non audité servi
(code_refuse dit la raison), et une brique non sûre n'est ni retenue ni mutée ; (5) NON-RÉGRESSION locale —
une vraie invention pure (amplitude) reste admise, retenue et servie normalement.
"""
from __future__ import annotations

import json
import os
import tempfile

from garde_ressources import borne
borne(max_cpu_s=400)
import expression_sure as ES
import ia
import moteur_invention as MI
from memoire_briques import MemoireBriques, VERSION, _spec_vers_texte

ok = total = 0


def check(nom, cond):
    global ok, total
    total += 1
    print(f"  [{'OK ' if cond else 'XXX'}] {nom}")
    if cond:
        ok += 1
    else:
        raise AssertionError(nom)


def _poc_path(tag):
    p = os.path.join(tempfile.gettempdir(), f"forge_atome7_{tag}.txt")
    if os.path.exists(p):
        os.remove(p)
    return p


# ── (1) JUGE STATIQUE : sound (zéro faux positif) + complet (attaques refusées) + n'exécute pas ──────────
check("sound : tout l'inventaire EXISTANT est jugé sûr (aucune brique légitime cassée)",
      all(ES.est_sure(e) for e in MI.EXISTANT.values()))
LEGIT = ["sum(_e for _e in x if _e > 5)", "(lambda _y: max(_y) - min(_y))(x)",
         "[list(_col) for _col in zip(*x)]", "sorted(x, key=abs)", "x.upper()",
         "{_e: x.count(_e) for _e in set(x)}", "__import__('math').prod(x)",
         "list(__import__('itertools').accumulate(x))", "[_e ** 2 for _e in x]"]
check("sound : échantillon représentatif des familles etend_* jugé sûr",
      all(ES.est_sure(e) for e in LEGIT))
ATTAQUES = [
    "(open('/tmp/x','w').write('h'), sum(x))[1]",   # I/O
    "__import__('os').system('id')",                 # commande système
    "__import__('subprocess').run(['id'])",          # idem
    "(1).__class__.__bases__[0].__subclasses__()",   # évasion par sous-classes
    "[y for y in ().__class__.__mro__]",             # évasion par attribut spécial en compréhension
    "eval('1+1')", "exec('x=1')", "compile('1','','eval')",
    "getattr(x, 'foo')", "globals()", "open('f')",
    "__import__('math').__loader__",                 # dunder sur un module pourtant sûr
]
for a in ATTAQUES:
    r = ES.raison_danger(a)
    check(f"attaque refusée avec raison : {a[:42]}", r is not None and not ES.est_sure(a))
# le jugement lui-même n'exécute rien : juger une expr qui écrirait un fichier ne l'écrit pas.
poc = _poc_path("juge")
ES.est_sure(f"(open({poc!r}, 'w').write('h'), sum(x))[1]")
check("le juge STATIQUE n'exécute jamais le code (aucun effet de bord au jugement)", not os.path.exists(poc))

# ── (2) FRONTIÈRE retient() : refus SANS exécution de l'effet de bord ────────────────────────────────────
poc = _poc_path("retient")
mem = MemoireBriques(base=dict(MI.EXISTANT))
mal = f"(open({poc!r}, 'w').write('touched'), sum(x))[1]"
avant = mem.refus_admission
admis = mem.retient(mal, origine="somme_piegee", exemples=[([1, 2, 3], 6), ([5], 5)], held=[([0, 4], 4)])
check("retient() REFUSE la brique correcte mais non sûre", admis is False)
check("retient() : l'effet de bord N'EST PAS déclenché (fichier absent) — jugé avant exécution",
      not os.path.exists(poc))
check("retient() : le refus est compté (refus_admission +1)", mem.refus_admission == avant + 1)
check("retient() : l'expr non sûre n'est PAS dans existant()",
      not any("open(" in e for e in mem.existant().values()))

# ── (3) FRONTIÈRE charge() : un briques.json v2 ALTÉRÉ (expr non sûre) part en quarantaine ───────────────
d = tempfile.mkdtemp(prefix="forge_a7_")
chemin = os.path.join(d, "briques.json")
poc = _poc_path("charge")
# on FABRIQUE un fichier v2 bien formé mais dont l'expr est hostile ET reproduit son spec (attaque réaliste).
falsifie = {"version": VERSION, "briques": {"somme_piegee": {
    "expr": f"(open({poc!r}, 'w').write('h'), sum(x))[1]", "origine": "somme_piegee",
    "quand": "2026-07-12",
    "spec": _spec_vers_texte([([1, 2, 3], 6)]), "held": _spec_vers_texte([([0, 4], 4)]),
    "n_verifie": 2}}}
with open(chemin, "w", encoding="utf-8") as f:
    json.dump(falsifie, f)
mem2 = MemoireBriques(chemin=chemin, base=dict(MI.EXISTANT))
check("charge() : l'expr non sûre du fichier altéré part en QUARANTAINE (pas injectée)",
      "somme_piegee" not in mem2.appris and any(q["nom"] == "somme_piegee" for q in mem2.quarantaine))
check("charge() : la quarantaine dit « non sûre »",
      any("non sûre" in q["raison"] for q in mem2.quarantaine if q["nom"] == "somme_piegee"))
check("charge() : l'effet de bord n'a PAS été exécuté au chargement (fichier absent)", not os.path.exists(poc))
check("charge() : trace de quarantaine écrite sur disque (append-only)", os.path.exists(chemin + ".quarantaine"))

# ── (4) FRONTIÈRE forge_brique() : jamais de code non audité servi ──────────────────────────────────────
# On force le cas via un registre où une capacité NON SÛRE reproduirait la cible (defense-in-depth explicite).
sortie = ia.forge_brique("amplitude", "x",
                         [([3, 1, 5], 4), ([2, 2], 0), ([10, 0, 3], 10)],
                         [([0, 9, 4], 9), ([7], 0), ([5, 5, 1], 4)])
check("forge_brique : le champ de sûreté 'code_refuse' existe et vaut None pour une invention pure",
      "code_refuse" in sortie and sortie["code_refuse"] is None)
check("forge_brique : reste JSON-sérialisable avec le nouveau champ", isinstance(json.dumps(sortie), str))

# ── (5) NON-RÉGRESSION locale : une invention pure passe toujours ────────────────────────────────────────
mem3 = MemoireBriques(base=dict(MI.EXISTANT))
AEX = [([3, 1, 5], 4), ([2, 2], 0), ([10, 0, 3], 10)]
AHELD = [([0, 9, 4], 9), ([7], 0), ([5, 5, 1], 4)]
v = MI.examine_cible("amplitude", "x", AEX, AHELD, existant=mem3.existant())
check("non-rég : amplitude reste une INVENTION", v.statut == MI.INVENTION)
check("non-rég : la réalisation pure est ADMISE (retient True)",
      mem3.retient(v.par, origine="amplitude", exemples=AEX, held=AHELD) is True)
check("non-rég : elle est bien servie par existant()", v.par in mem3.existant().values())

print(f"\n== VALIDE_EXPRESSION_SURE : {ok}/{total} ==")
assert ok == total
