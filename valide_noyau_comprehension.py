"""
NOYAU DE COMPRÉHENSION — laisser le RÉEL décider du PÉRIMÈTRE de la déduplication, EXHAUSTIVEMENT (idée de Yohan :
comme on a laissé l'IA choisir l'ordre des étages, on lui laisse choisir QUELLES briques fusionnent — l'aboutissement
= le plus grand noyau que le juge accorde). On teste TOUTES les briques, énumération COMPLÈTE, sans raccourci.

Exigence Yohan (excellence chirurgicale, tous les plans) : on ne se contente JAMAIS de « ça marche ». Une brique
n'est ABSORBÉE que si le général G est, sur ses cibles : (1) CORRECT au held-out [inclusion] ET (2) au COÛT
maîtrisé [gradient : résolu hors du tier le plus cher] — et on MESURE chaque plan (générateurs, étages, candidats,
rang G vs standalone). Sinon SÉPARÉE — un refus HONNÊTE dessine la frontière mesurée + la FEUILLE DE ROUTE de
croissance (briques « de forme compréhension » refusées seulement faute d'une SOURCE/FORME → cibles d'extension).

Le test est lui-même FALSIFIABLE : le verdict mesuré de CHAQUE brique doit coller à l'attendu (il identifie les
absorptions ET tous les refus — s'il tamponnait, il casserait sur les 20 refuseurs).
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from comprehension import Predicteur
from compounding import resoudre
from generateur import (TYPES_RICHES, GenerateurComprehensionGenerale, GenerateurMapRepli,
                        GenerateurMultiPasse, GenerateurOrchestre)
from juge import Limites, juge
from store import Store
from taches import Tache

LIM = Limites(temps_s=3, cpu_s=2)

CARRE = ("carre", "def carre(*args, **kwargs):\n    return args[0] * args[0]\n")
CUBE = ("cube", "def cube(*args, **kwargs):\n    return args[0] ** 3\n")
ADD = ("add", "def add(*args, **kwargs):\n    return args[0] + args[1]\n")
MUL = ("mul", "def mul(*args, **kwargs):\n    return args[0] * args[1]\n")
EST_POS = ("est_positif", "def est_positif(*args, **kwargs):\n    return args[0] > 0\n")
EST_NEG = ("est_negatif", "def est_negatif(*args, **kwargs):\n    return args[0] < 0\n")

N_ENUM = 100000   # énumération COMPLÈTE (au-delà de tout espace de G) — aucun raccourci


def _t(fn, tests, held=""):
    return Tache(id=f"noyau/{fn}", point_entree=fn, prompt=f'def {fn}(*a):\n    """..."""',
                 tests=tests, tests_held_out=held)


# --- TEST D'ENFER : held-out EXTRÊMES (négatifs massifs, annulations, moyenne flottante, valeurs géantes) ------
# « ça marche en enfer », pas « ça marche sur un test difficile ». Le noyau doit résoudre CES cibles DANS la
# montée vivante avec TOUS les autres étages allumés en compétition (map-repli/multipasse ÉTEINTS).
ENFER = {
    "somme_cubes": _t("somme_cubes",
        "def check(c):\n    assert c([1,2]) == 9\n    assert c([2,3]) == 35\ncheck(somme_cubes)",
        "def check(c):\n    assert c([-100,100]) == 0\n    assert c([10,-10,5]) == 125\n    assert c([3,-3,3,-3]) == 0\n    assert c([-2,-2,-2]) == -24\n    assert c([50,50]) == 250000\n    assert c([0,0,0]) == 0\ncheck(somme_cubes)"),
    "au_dessus_moyenne": _t("au_dessus_moyenne",
        "def check(c):\n    assert c([1,2,3,4]) == 2\n    assert c([5,5,5,5]) == 0\ncheck(au_dessus_moyenne)",
        "def check(c):\n    assert c([1,2,3,4,5,6,7,8,9,10]) == 5\n    assert c([100,1,1,1]) == 1\n    assert c([-10,-20,-30]) == 1\n    assert c([1000000,0]) == 1\n    assert c([3,3,3,3]) == 0\n    assert c([5,5,5,5,5,6]) == 1\ncheck(au_dessus_moyenne)"),
}


# --- Cibles canoniques de CHAQUE brique (reprises verbatim de leurs valide_*.py) ------------------------------
TACHES = {
    "map-repli": [
        # held-out ADVERSE : négatifs (le SIGNE du cube compte), zéro -> distingue cube de carre, pas de coïncidence.
        _t("somme_cubes",
           "def check(c):\n    assert c([1,2]) == 9\n    assert c([2,3]) == 35\n    assert c([0,1]) == 1\ncheck(somme_cubes)",
           "def check(c):\n    assert c([1,2,3]) == 36\n    assert c([3]) == 27\n    assert c([-1,2]) == 7\n    assert c([-2,-3]) == -35\n    assert c([0]) == 0\ncheck(somme_cubes)"),
        _t("max_carres",
           "def check(c):\n    assert c([1,3,2]) == 9\n    assert c([2,2]) == 4\n    assert c([5,1]) == 25\ncheck(max_carres)",
           "def check(c):\n    assert c([4,3]) == 16\n    assert c([6]) == 36\n    assert c([-5,1]) == 25\n    assert c([-3,-4]) == 16\ncheck(max_carres)")],
    "multipasse": [
        # held-out ADVERSE : négatifs (moyenne négative), doublons, moyenne flottante -> pas de coïncidence.
        _t("au_dessus_moyenne",
           "def check(c):\n    assert c([1,2,3,4]) == 2\n    assert c([10,0,0]) == 1\n    assert c([5,5,5,5]) == 0\ncheck(au_dessus_moyenne)",
           "def check(c):\n    assert c([1,2,3,10]) == 1\n    assert c([0,0,0,4]) == 1\n    assert c([2,4,6]) == 1\n    assert c([-1,-2,-3]) == 1\n    assert c([-5,5]) == 1\n    assert c([2,2,2,8]) == 1\ncheck(au_dessus_moyenne)"),
        _t("somme_au_dessus_moyenne",
           "def check(c):\n    assert c([1,2,3,4]) == 7\n    assert c([10,0,0]) == 10\n    assert c([5,5]) == 0\ncheck(somme_au_dessus_moyenne)",
           "def check(c):\n    assert c([1,2,3,10]) == 10\n    assert c([2,4,6]) == 6\n    assert c([-1,-2,-3]) == -1\n    assert c([1,1,1,5]) == 5\ncheck(somme_au_dessus_moyenne)")],
    "composition": [
        # COUVERTURE COMPLÈTE + held-out DURCI (leçon « tests faibles = faux positifs ») : sémantique canonique
        # = sorted(xs)[-2]. Sur doublons-du-max le noyau `max(x if x<max(xs))` se trompe -> démasqué. Et `trie`
        # (sorted) est hors de toute compréhension -> défense en profondeur (composition refusée même sans la ruse).
        _t("deuxieme_plus_grand",
           "def check(c):\n    assert c([3,1,2]) == 2\n    assert c([5,1,4,2]) == 4\n    assert c([1,2]) == 1\ncheck(deuxieme_plus_grand)",
           "def check(c):\n    assert c([2,1,2]) == 2\n    assert c([5,5,4]) == 5\n    assert c([3,3,3]) == 3\ncheck(deuxieme_plus_grand)"),
        _t("trie",
           "def check(c):\n    assert c([3,1,2]) == [1,2,3]\n    assert c([]) == []\ncheck(trie)",
           "def check(c):\n    assert c([2,2,1]) == [1,2,2]\n    assert c([5,3,4]) == [3,4,5]\ncheck(trie)")],
    "jointure": [
        _t("produit_premier_dernier",
           "def check(c):\n    assert c([2,3,4]) == 8\n    assert c([5,1]) == 5\n    assert c([3]) == 9\ncheck(produit_premier_dernier)")],
    "multi-entrée": [
        _t("somme_deux",
           "def check(c):\n    assert c(2,3) == 5\n    assert c(0,0) == 0\n    assert c(-1,4) == 3\ncheck(somme_deux)")],
    "pli": [
        _t("factorielle",
           "def check(c):\n    assert c(5) == 120\n    assert c(0) == 1\n    assert c(3) == 6\ncheck(factorielle)")],
    "branchement": [
        _t("signe",
           "def check(c):\n    assert c(5) == 1\n    assert c(-3) == -1\n    assert c(0) == 0\n    assert c(2) == 1\ncheck(signe)")],
    "boucle": [
        _t("somme_jusqua_neg",
           "def check(c):\n    assert c([1,2,-1,5]) == 3\n    assert c([3,4]) == 7\n    assert c([-1,9]) == 0\n    assert c([]) == 0\ncheck(somme_jusqua_neg)")],
    "recurrence": [
        _t("fibonacci",
           "def check(c):\n    assert c(6) == 8\n    assert c(1) == 1\n    assert c(0) == 0\ncheck(fibonacci)",
           "def check(c):\n    assert c(8) == 21\n    assert c(10) == 55\n    assert c(2) == 1\ncheck(fibonacci)")],
    "while": [
        _t("gcd",
           "def check(c):\n    assert c(12,8) == 4\n    assert c(7,3) == 1\n    assert c(10,5) == 5\ncheck(gcd)",
           "def check(c):\n    assert c(48,18) == 6\n    assert c(100,75) == 25\n    assert c(9,6) == 3\ncheck(gcd)")],
    "invariant": [
        _t("is_palindrome",
           "def check(c):\n    assert c('aba') is True\n    assert c('ab') is False\n    assert c('') is True\ncheck(is_palindrome)",
           "def check(c):\n    assert c('abcba') is True\n    assert c('abc') is False\n    assert c('xx') is True\ncheck(is_palindrome)")],
    "jointure-profonde": [
        _t("max_minus_min",
           "def check(c):\n    assert c([3,1,2]) == 2\n    assert c([5,5]) == 0\n    assert c([1,9]) == 8\ncheck(max_minus_min)",
           "def check(c):\n    assert c([0,10,5]) == 10\n    assert c([7]) == 0\ncheck(max_minus_min)")],
    "comptage-membre": [
        _t("count_vowels",
           "def check(c):\n    assert c('chat') == 1\n    assert c('aeiou') == 5\n    assert c('xyz') == 0\ncheck(count_vowels)",
           "def check(c):\n    assert c('hello') == 2\n    assert c('sky') == 0\n    assert c('aaa') == 3\ncheck(count_vowels)")],
    "predicat-mesures": [
        _t("all_unique",
           "def check(c):\n    assert c([1,2,3]) is True\n    assert c([1,1]) is False\n    assert c([1,2,2]) is False\ncheck(all_unique)",
           "def check(c):\n    assert c([1,2,3,4]) is True\n    assert c([5,5,5]) is False\n    assert c([7]) is True\ncheck(all_unique)")],
    "positionnel": [
        _t("alternating_sum",
           "def check(c):\n    assert c([1,2,3]) == 2\n    assert c([5]) == 5\n    assert c([1,1,1,1]) == 0\n    assert c([10,1]) == 9\ncheck(alternating_sum)",
           "def check(c):\n    assert c([2,3,4]) == 3\n    assert c([1,2,3,4]) == -2\n    assert c([]) == 0\ncheck(alternating_sum)")],
    "mots": [
        _t("reverse_words",
           "def check(c):\n    assert c('a b c') == 'c b a'\n    assert c('hi yo') == 'yo hi'\n    assert c('x') == 'x'\ncheck(reverse_words)",
           "def check(c):\n    assert c('one two three') == 'three two one'\n    assert c('w x y z') == 'z y x w'\ncheck(reverse_words)")],
    "adjacence": [
        _t("count_transitions",
           "def check(c):\n    assert c([1,1,2,3,3]) == 2\n    assert c([1,1,1]) == 0\n    assert c([1,2,3]) == 2\n    assert c([5]) == 0\ncheck(count_transitions)",
           "def check(c):\n    assert c([1,2,2,3]) == 2\n    assert c([4,4]) == 0\n    assert c([1,2,1,2]) == 3\ncheck(count_transitions)")],
    "imbrique": [
        _t("flatten",
           "def check(c):\n    assert c([[1,2],[3]]) == [1,2,3]\n    assert c([[1],[2,3],[4]]) == [1,2,3,4]\n    assert c([[5]]) == [5]\ncheck(flatten)",
           "def check(c):\n    assert c([[1],[2],[3]]) == [1,2,3]\n    assert c([[7,8]]) == [7,8]\ncheck(flatten)")],
    "dict-accu": [
        _t("word_count",
           "def check(c):\n    assert c(['a','b','a']) == {'a':2,'b':1}\n    assert c(['x']) == {'x':1}\n    assert c(['z','z','z']) == {'z':3}\ncheck(word_count)",
           "def check(c):\n    assert c(['a','a','b','b']) == {'a':2,'b':2}\n    assert c([]) == {}\ncheck(word_count)")],
    "group-by": [
        _t("max_par_cle",
           "def check(c):\n    assert c([('a',1),('b',5),('a',3)]) == {'a':3,'b':5}\n    assert c([('x',2)]) == {'x':2}\ncheck(max_par_cle)",
           "def check(c):\n    assert c([('a',1),('a',2),('b',9)]) == {'a':2,'b':9}\n    assert c([('p',7),('q',7)]) == {'p':7,'q':7}\ncheck(max_par_cle)")],
    "serie": [
        _t("plus_longue_serie",
           "def check(c):\n    assert c([1,1,2,2,2,3]) == 3\n    assert c([5]) == 1\n    assert c([1,2,3]) == 1\ncheck(plus_longue_serie)",
           "def check(c):\n    assert c([4,4,4,4,1]) == 4\n    assert c([7,7,1,1]) == 2\ncheck(plus_longue_serie)")],
    "generer-tester": [
        _t("nieme_premier",
           "def check(c):\n    assert c(1) == 2\n    assert c(2) == 3\n    assert c(3) == 5\ncheck(nieme_premier)",
           "def check(c):\n    assert c(4) == 7\n    assert c(5) == 11\ncheck(nieme_premier)")],
}

# Registre exhaustif : prims données à G (équité d'inclusion), verdict attendu, et tag d'EXTENSIBILITÉ (forme de
# compréhension refusée seulement faute d'une source/forme -> feuille de route vers le plus grand noyau).
# raison = pourquoi séparée (la frontière mesurée).
BRIQUES = [
    ("map-repli",        [CARRE, CUBE], "ABSORBÉE", False, "transform+reduce (sous-cas direct)"),
    ("multipasse",       [],            "ABSORBÉE", False, "filtre-agrégat+reduce (sous-cas direct)"),
    ("comptage-membre",  [],            "SÉPARÉE",  True,  "filtre par APPARTENANCE (c in litt.) — EXTENSION filtre"),
    ("adjacence",        [],            "SÉPARÉE",  True,  "source = VOISINS (xs[i],xs[i-1]) — EXTENSION source"),
    ("imbrique",         [],            "SÉPARÉE",  True,  "source = 2 NIVEAUX (for x for y) — EXTENSION source"),
    ("positionnel",      [],            "SÉPARÉE",  True,  "source = PARITÉ de position (xs[::2]) — EXTENSION source"),
    ("composition",      [],            "SÉPARÉE",  False, "pipeline SCALAIRE (pas une compréhension)"),
    ("jointure",         [],            "SÉPARÉE",  False, "joint 2 sous-résultats (op binaire)"),
    ("jointure-profonde",[],            "SÉPARÉE",  False, "joint 2 agrégats/pipelines"),
    ("multi-entrée",     [],            "SÉPARÉE",  False, "arité ≥ 2 (plusieurs args)"),
    ("pli",              [],            "SÉPARÉE",  False, "état/accumulateur (reduce)"),
    ("branchement",      [],            "SÉPARÉE",  False, "contrôle (ternaire)"),
    ("boucle",           [],            "SÉPARÉE",  False, "boucle bornée (arrêt anticipé)"),
    ("recurrence",       [],            "SÉPARÉE",  False, "état à 2 variables"),
    ("while",            [],            "SÉPARÉE",  False, "boucle conditionnelle"),
    ("invariant",        [],            "SÉPARÉE",  False, "égalité structurelle x == prim(x)"),
    ("predicat-mesures", [],            "SÉPARÉE",  False, "compare 2 mesures globales (bool)"),
    ("mots",             [],            "SÉPARÉE",  False, "liste de mots -> string (join)"),
    ("dict-accu",        [],            "SÉPARÉE",  False, "sortie DICT {clé: mesure}"),
    ("group-by",         [],            "SÉPARÉE",  False, "sortie DICT groupée par clé"),
    ("serie",            [],            "SÉPARÉE",  False, "état run-length (best/cur)"),
    ("generer-tester",   [],            "SÉPARÉE",  False, "génère-et-teste (while count<n)"),
]

STANDALONE = {"map-repli": GenerateurMapRepli([CARRE, CUBE]), "multipasse": GenerateurMultiPasse()}


def _est_t3(code: str) -> bool:
    """Candidat du tier le plus cher de G : transform ET filtre simultanés."""
    return " if x " in code and "(x) for x in args[0]" in code


def _resout_rang(gen, tache, n=N_ENUM):
    cands = gen.propose(tache.prompt, n)
    for i, code in enumerate(cands):
        if juge(code, tache.tests, LIM).passe and (not tache.tests_held_out or juge(code, tache.tests_held_out, LIM).passe):
            return code, i, len(cands)
    return None, -1, len(cands)


def _check(nom, condition):
    print(f"  [{'OK ' if condition else 'RATÉ'}] {nom}")
    return condition


def main() -> int:
    resultats = []
    absorbees, extensibles = [], []
    print(f"BALAYAGE EXHAUSTIF — {len(BRIQUES)} briques, énumération complète (n={N_ENUM}), jugé par le réel :\n")
    for nom, prims, attendu, extensible, raison in BRIQUES:
        G = GenerateurComprehensionGenerale(prims)
        inclus, couts_ok, n_cands = True, True, 0
        lignes = []
        for tache in TACHES[nom]:
            code, rg, n_cands = _resout_rang(G, tache)
            if code is None:
                inclus = False
                lignes.append(f"{tache.point_entree}: HORS-PORTÉE")
                continue
            t3 = _est_t3(code)
            couts_ok = couts_ok and not t3
            extra = ""
            if nom in STANDALONE:
                _, rb, nb = _resout_rang(STANDALONE[nom], tache)
                extra = f"  | standalone rang={rb}/{nb}"
            lignes.append(f"{tache.point_entree}: rang G={rg}/{n_cands}{' [T3!]' if t3 else ''}{extra}")
        verdict = "ABSORBÉE" if (inclus and couts_ok) else "SÉPARÉE"
        ok = verdict == attendu
        if verdict == "ABSORBÉE":
            absorbees.append(nom)
        elif extensible:
            extensibles.append((nom, raison))
        tag = "" if verdict == "ABSORBÉE" else (f"  ~EXTENSIBLE: {raison}" if extensible else f"  ({raison})")
        print(f"  {'✓' if ok else '✗'} {nom:<18} {verdict:<9} (attendu {attendu}){tag}")
        for l in lignes:
            print(f"        {l}")
        resultats.append(ok)

    # --- TEST D'ENFER : montée vivante, TOUS les étages en compétition, map-repli/multipasse ÉTEINTS ----------
    print("\n  ENFER (montée vivante, tous les étages allumés, map-repli/multipasse ÉTEINTS) :")
    for nom_brique, (prims, tache) in {"map-repli": ([CARRE, CUBE], ENFER["somme_cubes"]),
                                       "multipasse": ([CARRE, CUBE], ENFER["au_dessus_moyenne"])}.items():
        with tempfile.TemporaryDirectory() as d:
            store = Store(Path(d) / "s.jsonl")
            orch = GenerateurOrchestre(
                store, primitives=prims, ops=[ADD, MUL], predicats=[EST_POS, EST_NEG],
                predicteur=Predicteur(store, types=TYPES_RICHES),
                recurrence=True, boucle_while=True, invariant=True, jointure_profonde=True,
                predicat_mesures=True, positionnel=True, mots=True, adjacence=True, imbrique=True,
                dict_accu=True, group_by=True, serie=True, generer_tester=True,
                comprehension_generale=True, inventer=True, substrat=True,
                map_repli=False, multipasse=False)   # les deux absorbées sont ÉTEINTES : le noyau doit les porter
            etage, appels, code, _ = resoudre(orch, tache, LIM)
        bon = code is not None and etage == "comprehension-generale"
        print(f"        {tache.point_entree:<22} -> étage `{etage}` en {appels} appels (held-out enfer)")
        resultats.append(_check(f"ENFER : le noyau porte `{tache.point_entree}` (ex-{nom_brique}) à l'étage "
                                f"`comprehension-generale` malgré toute la compétition", bon))

    print()
    print(f"  CARTE DE CAPACITÉ (ce que le noyau PEUT faire — PAS un plan de consolidation) :")
    print(f"    - le noyau SUBSUME {absorbees} en capacité (il sait les résoudre).")
    print(f"    - MAIS la consolidation (retirer les spécialistes, mettre le noyau à leur place) est RÉFUTÉE par le")
    print(f"      réel : `mesure_cout_systeme.py` mesure +9% d'appels au juge (un gros étage général est CHER À")
    print(f"      ÉCHOUER pour toute tâche résolue plus loin). -> on GARDE les spécialistes rapides + le noyau en")
    print(f"      FALLBACK (dernier étage) pour le NEUF (transform+filtre). La dédup élégante perdait sur le coût.")
    print()
    if all(resultats):
        print(f"NOYAU — CARTE DE CAPACITÉ VALIDÉE {sum(resultats)}/{len(resultats)}. Le noyau PEUT résoudre {absorbees} "
              f"(capacité, prouvée au held-out + en enfer) ; FRONTIÈRE MESURÉE : {len(BRIQUES) - len(absorbees)} briques "
              f"refusées, dont {len(extensibles)} de FORME compréhension (feuille de route de CROISSANCE du noyau, "
              f"source/forme à ajouter) : {[n for n, _ in extensibles]}. Le test DISCRIMINE (capacité ET refus). "
              f"VERDICT DU RÉEL : NE PAS consolider (coût) ; le noyau reste un étage FALLBACK additif pour le neuf.")
        return 0
    print(f"ÉCHEC — {sum(resultats)}/{len(resultats)}. La carte ne colle pas au réel : RÉSULTAT (donnée, pas drame).")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
