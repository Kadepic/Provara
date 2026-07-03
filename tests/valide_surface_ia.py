"""
VALIDATION DE LA SURFACE DE ia.py — gate statique quasi-gratuite (AST, aucun chargement du lecteur).

MOTIVATION (audit 2026-07-01) : les validateurs P2 importent les BRIQUES directement (`import survie as S`),
jamais les WRAPPERS de ia.py. Une collision d'alias au niveau module (`import survie as _SUR` puis
`import surapprentissage as _SUR`) casse des wrappers (AttributeError / mauvais module) SANS qu'aucune gate ne
le voie : ~430 checks verts avec 5 wrappers cassés. Cette gate ferme le trou.

DEUX vérifications, sans exécuter ia.py (parse AST + import LÉGER des modules aliasés sous amorce-seule) :
  1. ALIAS UNIQUES : aucun alias `import X as A` ne doit être lié à DEUX modules différents (shadowing silencieux).
  2. SURFACE RÉSOLUE : tout accès `A.attr` de ia.py (A = alias importé) doit résoudre (hasattr(module, attr)).
     -> un wrapper qui appelle une fonction absente du (mauvais) module FAIL ici, immédiatement.

FAUX=0 : cette gate protège la couche API P2 (disponibilité/exactitude des façades) contre la régression.
EXIT 0 = tout résout ; EXIT non-nul = au moins un alias dupliqué ou un attribut non résolu.
"""
from __future__ import annotations

import ast
import importlib
import os

os.environ.setdefault("LECTEUR_AMORCE_SEULE", "1")   # ne jamais déclencher un full-load depuis cette gate

HARN = os.path.dirname(os.path.abspath(__file__))
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


src = open(os.path.join(os.environ.get("VERAX_ROOT") or HARN, "src", "ia.py"), encoding="utf-8").read()
arbre = ast.parse(src)

# 1) Collecte des imports de module au niveau du MODULE : `import X as A` / `import X`.
alias2mod: dict[str, str] = {}      # dernier binding (comme Python)
doublons: dict[str, set] = {}       # alias -> ensemble des modules distincts qui l'ont porté
for noeud in arbre.body:            # seulement le top-level (les imports de ia.py sont au module)
    if isinstance(noeud, ast.Import):
        for al in noeud.names:
            nom_local = al.asname or al.name.split(".")[0]
            module = al.name
            doublons.setdefault(nom_local, set()).add(module)
            alias2mod[nom_local] = module

# 2) LINT alias dupliqué : un alias lié à ≥2 modules DIFFÉRENTS = collision silencieuse (le bug _SUR/_KAL).
collisions = {a: sorted(m) for a, m in doublons.items() if len(m) >= 2}
check(f"aucun alias d'import dupliqué dans ia.py (collisions={collisions})", not collisions)

# 3) Surface : tout `A.attr` où A est un alias importé doit résoudre sur le module.
#    On importe chaque module aliasé une fois (léger, amorce-seule). Un import qui échoue = FAIL explicite.
mods: dict[str, object] = {}
manquants_import = []
for alias, module in sorted(alias2mod.items()):
    try:
        mods[alias] = importlib.import_module(module)
    except Exception as e:                       # noqa: BLE001 — on veut le diagnostic exact
        manquants_import.append(f"{alias}={module} ({type(e).__name__}: {e})")
check(f"tous les modules aliasés par ia.py s'importent (échecs={manquants_import})", not manquants_import)

# Accès attribut `A.attr` sur un alias importé -> (alias, attr) uniques.
acces: set = set()
for noeud in ast.walk(arbre):
    if (isinstance(noeud, ast.Attribute) and isinstance(noeud.value, ast.Name)
            and noeud.value.id in alias2mod):
        acces.add((noeud.value.id, noeud.attr))

non_resolus = []
for alias, attr in sorted(acces):
    mod = mods.get(alias)
    if mod is not None and not hasattr(mod, attr):
        non_resolus.append(f"{alias}({alias2mod[alias]}).{attr}")
check(f"tout accès alias.attr de ia.py résout ({len(acces)} accès, non résolus={non_resolus})",
      not non_resolus)

print(f"\n=== valide_surface_ia : {ok}/{total} checks OK "
      f"({len(alias2mod)} alias, {len(acces)} accès attribut vérifiés) ===")
if ok != total:
    raise SystemExit(1)
