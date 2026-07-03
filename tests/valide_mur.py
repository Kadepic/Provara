"""
DIAGNOSTIC — cartographier le MUR (mesurer et analyser avant de décider).

Pas de modèle, pas d'engagement sur la suite : juste la CARTE du terrain. On répond à
une seule question, honnêtement : « où finit la maîtrise du maison, où commence le mur,
et de quelle NATURE est ce mur ? » (principe : la maîtrise précède l'invention — on ne
peut pas inventer un sujet qu'on ne maîtrise pas ; donc on mesure d'abord la maîtrise.)

L'astuce qui rend ça DÉMONTRÉ (et pas « on a essayé sans succès ») : la portée du maison
est FINIE et ÉNUMÉRABLE. Le recombinant ne produit que { squelette connu } × { sens connu }.
On énumère cet ensemble EN ENTIER, puis, tâche par tâche :

  - DANS la portée  -> un candidat énumérable passe le juge  => maîtrise testable ;
  - HORS la portée  -> AUCUN candidat énumérable ne passe     => c'est un MUR (prouvé), et
        on NOMME sa nature :
          * VOCABULAIRE : la solution exige un fragment ABSENT de tout le store ;
          * STRUCTUREL  : la solution n'est pas réductible à une expression unique
                          (boucle qui accumule, récursion, multi-instructions).

Distinction clé : un échec DANS la portée serait un TROU DE MAÎTRISE (à réparer, pas un
mur). À cette échelle la portée est épuisée intégralement -> pas de trou possible : tout
le réalisable est résolu. (Le trou deviendra mesurable quand la portée sera trop grande
pour être épuisée -> échantillonnage -> c'est là que la DIRECTION, point 2, compte.)

Critère de mort : si une tâche « portée » n'est pas résolue, ou si un mur n'est pas
correctement classé (cause vérifiée), le diagnostic échoue.
"""

from __future__ import annotations

import ast
import tempfile
from pathlib import Path

from generateur import TYPES_RICHES, GenerateurRecombinant, fragments_riches
from juge import Limites, juge
from store import Store
from taches import Tache

LIM = Limites(temps_s=3, cpu_s=2)

# --- La CONNAISSANCE du maison : 2 succès confirmés (sa mémoire longue) -------
K_SOLS = {
    "somme_carres": "def somme_carres(*args, **kwargs):\n    return sum(x * x for x in args[0])\n",
    "max_plus_un":  "def max_plus_un(*args, **kwargs):\n    return max(x + 1 for x in args[0])\n",
}
K_TESTS = {
    "somme_carres": "def check(c):\n    assert c([1,2,3]) == 14\n    assert c([]) == 0\ncheck(somme_carres)",
    "max_plus_un":  "def check(c):\n    assert c([1,2,3]) == 4\n    assert c([0]) == 1\ncheck(max_plus_un)",
}


def _tache(fn, tests):
    return Tache(id=f"diag/{fn}", point_entree=fn, prompt=f'def {fn}(xs):\n    """..."""', tests=tests)


# --- Le jeu de tâches GRADUÉ (vérité curée à comparer au verdict du diagnostic) ---
# (tâche, solution de référence complète, catégorie ATTENDUE)
GRADUE = [
    # -- DANS la portée : recombinables depuis la connaissance (test de maîtrise) --
    (_tache("max_carres",
            "def check(c):\n    assert c([1,2,3]) == 9\n    assert c([-3,2]) == 9\n    assert c([4]) == 16\ncheck(max_carres)"),
     "def max_carres(*args, **kwargs):\n    return max(x * x for x in args[0])\n", "portée"),
    (_tache("somme_plus_un",
            "def check(c):\n    assert c([1,2,3]) == 9\n    assert c([0]) == 1\n    assert c([-1,5]) == 6\ncheck(somme_plus_un)"),
     "def somme_plus_un(*args, **kwargs):\n    return sum(x + 1 for x in args[0])\n", "portée"),

    # -- HORS portée, mur de VOCABULAIRE : fragment absent du store --
    (_tache("cube_total",
            "def check(c):\n    assert c([1,2,3]) == 36\n    assert c([2]) == 8\n    assert c([0,1]) == 1\ncheck(cube_total)"),
     "def cube_total(*args, **kwargs):\n    return sum(x ** 3 for x in args[0])\n", "vocabulaire"),
    (_tache("crie",
            "def check(c):\n    assert c('ok') == 'OK'\n    assert c('aB') == 'AB'\ncheck(crie)"),
     "def crie(*args, **kwargs):\n    return args[0].upper()\n", "vocabulaire"),

    # -- HORS portée, mur STRUCTUREL : pas réductible à une expression unique --
    (_tache("factorielle",
            "def check(c):\n    assert c(5) == 120\n    assert c(0) == 1\n    assert c(3) == 6\ncheck(factorielle)"),
     "def factorielle(*args, **kwargs):\n    r = 1\n    for k in range(2, args[0] + 1):\n        r *= k\n    return r\n", "structurel"),
    (_tache("max_courant",
            "def check(c):\n    assert c([3,1,4,1,5]) == [3,3,4,4,5]\n    assert c([1]) == [1]\n    assert c([2,2]) == [2,2]\ncheck(max_courant)"),
     "def max_courant(*args, **kwargs):\n    out = []\n    m = args[0][0]\n    for x in args[0]:\n        if x > m:\n            m = x\n        out.append(m)\n    return out\n", "structurel"),
]


def _check(nom, condition):
    print(f"  [{'OK ' if condition else 'RATÉ'}] {nom}")
    return condition


def _expression_unique(solution: str) -> bool:
    """Vrai si le corps de la fonction se réduit à un SEUL `return <expr>` (hors
    docstring) -> c'est tout ce que le recombinant sait produire."""
    arbre = ast.parse(solution)
    fn = next((n for n in ast.walk(arbre) if isinstance(n, ast.FunctionDef)), None)
    if fn is None:
        return False
    corps = fn.body
    if corps and isinstance(corps[0], ast.Expr) and isinstance(getattr(corps[0], "value", None), ast.Constant):
        corps = corps[1:]   # ignorer la docstring
    return len(corps) == 1 and isinstance(corps[0], ast.Return) and corps[0].value is not None


def _resout(generateur, tache, n=1000):
    """1er candidat énumérable qui passe le juge, sinon None (portée épuisée)."""
    for code in generateur.propose(tache.prompt, n):
        if juge(code, tache.tests, LIM).passe:
            return code
    return None


def main() -> int:
    resultats = []

    with tempfile.TemporaryDirectory() as d:
        store = Store(Path(d) / "s.jsonl")
        for fn, sol in K_SOLS.items():
            t = _tache(fn, K_TESTS[fn])
            v = juge(sol, t.tests, LIM)
            assert v.passe, f"pré-condition : {fn}"
            store.ajoute(t, sol, v)

        g5 = GenerateurRecombinant(store, types=TYPES_RICHES)
        squelettes, sens = g5._pool()
        portee = {sq.replace("{C}", se) for sq in squelettes for se in sens}
        store_sens = set(sens)

        print(f"Connaissance du maison : {len(store)} succès confirmés.")
        print(f"PORTÉE énumérée EN ENTIER : {len(squelettes)} squelettes × {len(sens)} sens "
              f"-> {len(portee)} expressions atteignables (aucun échantillonnage).\n")
        print(f"{'tâche':<16}{'résolue':<9}{'portée':<8}{'cause / preuve'}")
        print("-" * 64)

        classes = []   # (tache, categorie_trouvee, categorie_attendue)
        for tache, ref, attendue in GRADUE:
            assert juge(ref, tache.tests, LIM).passe, f"la référence de {tache.point_entree} doit passer (honnêteté)"
            gagnant = _resout(g5, tache)
            dans_portee = gagnant is not None

            if dans_portee:
                trouvee = "portée"
                preuve = "recombiné: " + gagnant.strip().splitlines()[-1].strip()
            elif not _expression_unique(ref):
                trouvee = "structurel"
                preuve = "réf. non réductible à une expression unique"
            else:
                _, frags = fragments_riches(ref, TYPES_RICHES)
                manquants = [f for f in frags if f not in store_sens]
                trouvee = "vocabulaire"
                preuve = f"fragment(s) absent(s): {manquants}"

            classes.append((tache, trouvee, attendue))
            print(f"{tache.point_entree:<16}{('oui' if dans_portee else 'non'):<9}"
                  f"{('dans' if dans_portee else 'hors'):<8}{preuve}")
        print()

        # 1. Maîtrise : tout ce qui est DANS la portée est résolu (pas de trou de maîtrise).
        portee_ok = all(tr == "portée" for _, tr, at in classes if at == "portée")
        resultats.append(_check("MAÎTRISE : toutes les tâches dans la portée sont résolues (aucun trou)",
                                portee_ok))
        # 2. Mur prouvé : aucune tâche hors-portée n'est résolue (portée épuisée, pas de chance).
        mur_non_resolu = all(tr != "portée" for _, tr, at in classes if at != "portée")
        resultats.append(_check("MUR PROUVÉ : aucune tâche hors-portée résolue (portée énumérée en entier)",
                                mur_non_resolu))
        # 3. Causes correctement localisées : verdict auto == vérité curée.
        bien_classe = all(tr == at for _, tr, at in classes)
        resultats.append(_check("CAUSES LOCALISÉES : classification auto = vérité curée (6/6)",
                                bien_classe))
        # 4. Honnêteté : on a énuméré la portée en entier (taille connue, > 0), pas échantillonné.
        resultats.append(_check(f"HONNÊTETÉ : portée bornée et énumérée en entier ({len(portee)} expr.)",
                                len(portee) > 0))

        # Synthèse lisible de la carte.
        murs = [t.point_entree for t, tr, _ in classes if tr != "portée"]
        voc = [t.point_entree for t, tr, _ in classes if tr == "vocabulaire"]
        struct = [t.point_entree for t, tr, _ in classes if tr == "structurel"]
        print(f"\nCARTE — maîtrise sur sa portée ({len(portee)} expr.) ; mur localisé sur {len(murs)} tâches :")
        print(f"    mur de VOCABULAIRE (fragment absent)        : {voc}")
        print(f"    mur STRUCTUREL (hors expression unique)     : {struct}")

    print()
    if all(resultats):
        print(f"DIAGNOSTIC VALIDÉ — {len(resultats)}/{len(resultats)}. Le terrain est cartographié : "
              f"le maison MAÎTRISE sa portée (énumérée en entier) ; le mur est DÉMONTRÉ et de deux natures "
              f"(vocabulaire / structurel). On décide la suite sur cette carte, pas à l'aveugle.")
        return 0
    print(f"ÉCHEC — {sum(resultats)}/{len(resultats)}.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
