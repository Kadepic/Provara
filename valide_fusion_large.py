"""
ÉLARGIR l'étage 1 — jusqu'où la fusion d'EXPRESSIONS porte (avant de monter d'un cran).

On mesure la PORTÉE de la fusion d'expressions sur des cadres VARIÉS, avant de décider de
l'étage 2. Quatre cadres, deux domaines (nombres / chaînes), deux formes (agrégation / liste) :

  cadre (sum,  x, args[0]) : somme_carres ⊕ compte_positifs  -> sum(x*x for x in args[0] if x>0)
  cadre (max,  x, args[0]) : max_carres   ⊕ max_positif       -> max(x*x for x in args[0] if x>0)
  cadre [list, x, args[0]] : liste_carres ⊕ liste_positifs    -> [x*x for x in args[0] if x>0]
  cadre [list, c, args[0]] : majuscules   ⊕ lettres           -> [c.upper() for c in args[0] if c.isalpha()]

On exige :
  1. PORTÉE LARGE : la fusion résout les QUATRE cibles (élément d'un succès + filtre d'un autre,
     même cadre) — agrégations variées ET listes, nombres ET chaînes.
  2. LE MUR EST PARTOUT : la recombinaison (arité un) ne résout AUCUNE des quatre (le mur de
     composition n'est pas propre à un cadre).
  3. HONNÊTETÉ : retirer la pièce-filtre d'un cadre -> sa cible retombe (compose, n'invente pas).
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from generateur import GenerateurFusion, GenerateurRecombinant, TYPES_RICHES
from juge import Limites, juge
from store import Store
from taches import Tache

LIM = Limites(temps_s=3, cpu_s=2)


def _t(fn, tests, held=""):
    return Tache(id=f"fl/{fn}", point_entree=fn, prompt=f'def {fn}(xs):\n    """..."""',
                 tests=tests, tests_held_out=held)


def _sol(fn, corps):
    return f"def {fn}(*args, **kwargs):\n    return {corps}\n"


# Chaque cadre : (élément-pièce, filtre-pièce, cible). Pièces = succès sur d'AUTRES tâches.
CADRES = [
    {
        "nom": "sum  (nombres)",
        "element": (_t("somme_carres", "def check(c):\n assert c([1,2,3])==14\n assert c([])==0\ncheck(somme_carres)"),
                    _sol("somme_carres", "sum(x * x for x in args[0])")),
        "filtre":  (_t("compte_positifs", "def check(c):\n assert c([1,-2,3])==2\n assert c([])==0\ncheck(compte_positifs)"),
                    _sol("compte_positifs", "sum(1 for x in args[0] if x > 0)")),
        # Held-out adverse : sum(x*x for x in xs if x>0). Tue sum sans filtre / count / min+1.
        "cible":   _t("somme_carres_positifs",
                      "def check(c):\n assert c([1,-2,3])==10\n assert c([-1,-2])==0\n assert c([2])==4\ncheck(somme_carres_positifs)",
                      "def check(c):\n assert c([-5,5])==25\n assert c([3,-3,4])==25\n assert c([])==0\n assert c([0,1,-1])==1\n assert c([2,2])==8\ncheck(somme_carres_positifs)"),
    },
    {
        "nom": "max  (nombres)",
        "element": (_t("max_carres", "def check(c):\n assert c([1,2,3])==9\n assert c([-3,2])==9\ncheck(max_carres)"),
                    _sol("max_carres", "max(x * x for x in args[0])")),
        "filtre":  (_t("max_positif", "def check(c):\n assert c([1,5,2])==5\n assert c([-1,3])==3\ncheck(max_positif)"),
                    _sol("max_positif", "max(x for x in args[0] if x > 0)")),
        # Held-out adverse : max(x*x for x in xs if x>0). Tue max(x*x) sans filtre (sur [-10,1] donnerait 100), max sans carré, etc. (pas de vide : max() crasherait aussi la vraie sol).
        "cible":   _t("max_carre_positif",
                      "def check(c):\n assert c([-3,1,2])==4\n assert c([5])==25\n assert c([-1,3])==9\ncheck(max_carre_positif)",
                      "def check(c):\n assert c([-10,1])==1\n assert c([2,-5,3])==9\n assert c([-2,6])==36\n assert c([7])==49\ncheck(max_carre_positif)"),
    },
    {
        "nom": "list (nombres)",
        "element": (_t("liste_carres", "def check(c):\n assert c([1,2,3])==[1,4,9]\n assert c([])==[]\ncheck(liste_carres)"),
                    _sol("liste_carres", "[x * x for x in args[0]]")),
        "filtre":  (_t("liste_positifs", "def check(c):\n assert c([1,-2,3])==[1,3]\n assert c([-1])==[]\ncheck(liste_positifs)"),
                    _sol("liste_positifs", "[x for x in args[0] if x > 0]")),
        # Held-out adverse : [x*x for x in xs if x>0]. Tue liste sans filtre / sans carré / ordre.
        "cible":   _t("liste_carres_positifs",
                      "def check(c):\n assert c([1,-2,3])==[1,9]\n assert c([-1])==[]\n assert c([2])==[4]\ncheck(liste_carres_positifs)",
                      "def check(c):\n assert c([-5,5])==[25]\n assert c([3,-3,4])==[9,16]\n assert c([])==[]\n assert c([0,1,-1])==[1]\n assert c([2,2])==[4,4]\ncheck(liste_carres_positifs)"),
    },
    {
        "nom": "list (chaînes)",
        "element": (_t("majuscules", "def check(c):\n assert c('ab')==['A','B']\n assert c('')==[]\ncheck(majuscules)"),
                    _sol("majuscules", "[c.upper() for c in args[0]]")),
        "filtre":  (_t("lettres", "def check(c):\n assert c('a1b')==['a','b']\n assert c('12')==[]\ncheck(lettres)"),
                    _sol("lettres", "[c for c in args[0] if c.isalpha()]")),
        # Held-out adverse : [c.upper() for c in xs if c.isalpha()]. Tue upper sans filtre / filtre sans upper / oubli des doublons.
        "cible":   _t("lettres_maj",
                      "def check(c):\n assert c('a1B')==['A','B']\n assert c('x')==['X']\n assert c('12')==[]\ncheck(lettres_maj)",
                      "def check(c):\n assert c('!x?')==['X']\n assert c('')==[]\n assert c('123')==[]\n assert c('Zz')==['Z','Z']\ncheck(lettres_maj)"),
    },
]


def _check(nom, condition):
    print(f"  [{'OK ' if condition else 'RATÉ'}] {nom}")
    return condition


def _seme(store, tache, sol):
    v = juge(sol, tache.tests, LIM)
    assert v.passe, f"pré-condition : {tache.id}"
    store.ajoute(tache, sol, v)


def _resout(generateur, tache, n=300):
    for code in generateur.propose(tache.prompt, n):
        if juge(code, tache.tests, LIM).passe and (not tache.tests_held_out or juge(code, tache.tests_held_out, LIM).passe):
            return code
    return None


def main() -> int:
    resultats = []

    with tempfile.TemporaryDirectory() as d:
        store = Store(Path(d) / "s.jsonl")
        for cadre in CADRES:
            _seme(store, *cadre["element"])
            _seme(store, *cadre["filtre"])

        fus = GenerateurFusion(store)
        g5 = GenerateurRecombinant(store, types=TYPES_RICHES)

        print("Fusion d'expressions sur 4 cadres (2 domaines, 2 formes) :\n")
        resolues, mur_partout = 0, True
        for cadre in CADRES:
            cible = cadre["cible"]
            gagnant = _resout(fus, cible)
            recomb = _resout(g5, cible)
            ok = gagnant is not None
            resolues += ok
            mur_partout = mur_partout and (recomb is None)
            corps = gagnant.strip().splitlines()[-1].strip() if gagnant else "—"
            print(f"    {cadre['nom']:<16} fusion={'OK ' if ok else 'NON'}  recombinaison={'NON' if recomb is None else 'OK'}   {corps}")
        print()

        resultats.append(_check("PORTÉE LARGE : la fusion résout les 4 cibles (agrégations + listes, nombres + chaînes)",
                                resolues == len(CADRES)))
        resultats.append(_check("LE MUR EST PARTOUT : la recombinaison (arité un) n'en résout AUCUNE",
                                mur_partout))

    # 3. Honnêteté : sans la pièce-filtre du cadre chaînes, la cible retombe.
    with tempfile.TemporaryDirectory() as d:
        store2 = Store(Path(d) / "s2.jsonl")
        ch = CADRES[3]
        _seme(store2, *ch["element"])   # majuscules seulement, pas le filtre lettres
        fus2 = GenerateurFusion(store2)
        resultats.append(_check("HONNÊTETÉ : sans la pièce-filtre, la cible chaînes retombe (compose, n'invente pas)",
                                _resout(fus2, ch["cible"]) is None))

    print()
    if all(resultats):
        print(f"ÉTAGE 1 ÉLARGI — {len(resultats)}/{len(resultats)}. La fusion d'expressions porte LARGE : "
              f"tout cadre `AGG(elt for v in it if f)` ou `[elt for v in it if f]`, nombres comme chaînes. "
              f"Le mur de composition tombe partout dans ce monde — mais on reste dans l'EXPRESSION unique "
              f"(le multi-étapes attend l'étage 2). Voilà jusqu'où ça porte, mesuré.")
        return 0
    print(f"ÉCHEC — {sum(resultats)}/{len(resultats)}.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
