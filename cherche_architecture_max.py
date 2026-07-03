"""
RECHERCHE D'ARCHITECTURE — VERSION MAXIMALE (tous les étages, multi-domaine, gros budget, jugée par le RÉEL).

Le placement des briques n'est PAS tranché par l'humain : la RÉALITÉ choisit l'ordre d'escalade qui minimise le
coût (appels au juge) à couverture pleine (held-out). Différences avec cherche_architecture.py (trop étroit) :
  - LES 27 ÉTAGES (pas 11) — y compris map-repli, multipasse, invariant, jointure-profonde, predicat-mesures,
    positionnel, mots, adjacence, imbrique, dict-accu, group-by, serie, generer-tester, comprehension-generale.
  - BATTERIE MULTI-DOMAINE : une tâche par étage, sur entiers / chaînes / listes / imbriqué / paires / dict /
    booléens — chaque test confronté à plusieurs domaines (exigence Yohan).
  - ÉVALUATION PAR `resoudre` (one-shot, atomes riches semés) -> mesure pure du COÛT D'ORDRE, held-out exigé.
  - BUDGET ÉLEVÉ + borne de TEMPS (tourne des heures) + cache + multi-graines.

Garde-fou : held-out exigé (resoudre n'accepte que ce qui généralise) -> aucun ordre ne gagne en sur-apprenant.
La graine humaine n'est qu'un point de départ, libre d'être supplantée. SORTIE : meilleur ordre + verdict honnête.
"""

from __future__ import annotations

import random
import sys
import tempfile
import time
from pathlib import Path

from comprehension import Predicteur
from compounding import resoudre
from generateur import TYPES_RICHES, GenerateurOrchestre
from juge import Limites
from store import Store
from taches import Tache

LIM = Limites(temps_s=1, cpu_s=1)   # timeout serré : les vraies solutions sur petites entrées sont rapides ;
K = 50                              # cap les candidats divergents (while) et borne le coût d'éval
SEEDS = (0, 1)
BUDGET_S = float(sys.argv[1]) if len(sys.argv) > 1 else 21600.0   # borne de temps (défaut 6 h, tourne la nuit)

ETAGES = ["réutilisation", "recombinaison", "fusion", "composition", "jointure", "multi-entrée", "pli",
          "branchement", "boucle", "recurrence", "while", "map-repli", "invariant", "jointure-profonde",
          "predicat-mesures", "positionnel", "mots", "multipasse", "adjacence", "imbrique", "dict-accu",
          "group-by", "serie", "generer-tester", "comprehension-generale", "invention", "substrat"]
HUMAIN = list(ETAGES)

# Atomes riches semés (chaque tâche one-shot solvable par SON étage ; pas de cube -> invention le minte).
PRIMS = [("carre", "def carre(*args, **kwargs):\n    return args[0] * args[0]\n"),
         ("incremente", "def incremente(*args, **kwargs):\n    return args[0] + 1\n"),
         ("double", "def double(*args, **kwargs):\n    return args[0] + args[0]\n"),
         ("inverse_chaine", "def inverse_chaine(*args, **kwargs):\n    return args[0][::-1]\n"),
         ("trie", "def trie(*args, **kwargs):\n    return sorted(args[0])\n"),
         ("moins_un", "def moins_un(*args, **kwargs):\n    return args[0] - 1\n")]
OPS = [("mul", "def mul(*args, **kwargs):\n    return args[0] * args[1]\n"),
       ("add", "def add(*args, **kwargs):\n    return args[0] + args[1]\n"),
       ("sub", "def sub(*args, **kwargs):\n    return args[0] - args[1]\n"),
       ("max2", "def max2(*args, **kwargs):\n    return args[0] if args[0] >= args[1] else args[1]\n"),
       ("min2", "def min2(*args, **kwargs):\n    return args[0] if args[0] <= args[1] else args[1]\n"),
       ("mod", "def mod(*args, **kwargs):\n    return args[0] % args[1]\n")]
PREDS = [("est_positif", "def est_positif(*args, **kwargs):\n    return args[0] > 0\n"),
         ("est_negatif", "def est_negatif(*args, **kwargs):\n    return args[0] < 0\n"),
         ("is_prime", "def is_prime(*args, **kwargs):\n    return args[0] > 1 and all(args[0] % d for d in range(2, args[0]))\n"),
         ("is_pair", "def is_pair(*args, **kwargs):\n    return args[0] % 2 == 0\n")]


def _t(fn, sig, tests, held):
    return Tache(id=f"am/{fn}", point_entree=fn, prompt=f'def {fn}({sig}):\n    """..."""',
                 tests=tests, tests_held_out=held)


# Batterie MULTI-DOMAINE : une tâche par étage, plusieurs domaines (int, str, list, nested, pairs, dict, bool).
TACHES = [
    _t("somme_carres", "xs", "def check(c):\n assert c([1,2])==5\n assert c([3])==9\ncheck(somme_carres)",
       "def check(c):\n assert c([1,2,3])==14\n assert c([-2,4])==20\ncheck(somme_carres)"),                       # map-repli
    _t("au_dessus_moyenne", "xs", "def check(c):\n assert c([1,2,3,4])==2\n assert c([5,5,5,5])==0\ncheck(au_dessus_moyenne)",
       "def check(c):\n assert c([1,2,3,10])==1\n assert c([-1,-2,-3])==1\ncheck(au_dessus_moyenne)"),             # multipasse
    _t("somme_carres_sup_moy", "xs", "def check(c):\n assert c([1,2,3,4])==25\n assert c([2,2,2])==0\ncheck(somme_carres_sup_moy)",
       "def check(c):\n assert c([1,5])==25\n assert c([0,0,0,8])==64\ncheck(somme_carres_sup_moy)"),              # comprehension-generale
    _t("produit_premier_dernier", "xs", "def check(c):\n assert c([2,3,4])==8\n assert c([5,1])==5\ncheck(produit_premier_dernier)",
       "def check(c):\n assert c([3])==9\n assert c([2,5])==10\ncheck(produit_premier_dernier)"),                 # jointure
    _t("max_minus_min", "xs", "def check(c):\n assert c([3,1,2])==2\n assert c([5,5])==0\ncheck(max_minus_min)",
       "def check(c):\n assert c([1,9])==8\n assert c([0,10,5])==10\ncheck(max_minus_min)"),                      # jointure-profonde
    _t("factorielle", "n", "def check(c):\n assert c(5)==120\n assert c(0)==1\ncheck(factorielle)",
       "def check(c):\n assert c(3)==6\n assert c(4)==24\ncheck(factorielle)"),                                   # pli
    _t("signe", "x", "def check(c):\n assert c(5)==1\n assert c(-3)==-1\n assert c(0)==0\ncheck(signe)",
       "def check(c):\n assert c(2)==1\n assert c(-7)==-1\ncheck(signe)"),                                        # branchement
    _t("somme_jusqua_neg", "xs", "def check(c):\n assert c([1,2,-1,5])==3\n assert c([3,4])==7\ncheck(somme_jusqua_neg)",
       "def check(c):\n assert c([-1,9])==0\n assert c([5,5,-1])==10\ncheck(somme_jusqua_neg)"),                  # boucle
    _t("fibonacci", "n", "def check(c):\n assert c(6)==8\n assert c(1)==1\n assert c(0)==0\ncheck(fibonacci)",
       "def check(c):\n assert c(8)==21\n assert c(10)==55\ncheck(fibonacci)"),                                   # recurrence
    _t("gcd", "a, b", "def check(c):\n assert c(12,8)==4\n assert c(7,3)==1\ncheck(gcd)",
       "def check(c):\n assert c(48,18)==6\n assert c(10,5)==5\ncheck(gcd)"),                                     # while
    _t("is_palindrome", "s", "def check(c):\n assert c('aba') is True\n assert c('ab') is False\ncheck(is_palindrome)",
       "def check(c):\n assert c('abcba') is True\n assert c('abc') is False\ncheck(is_palindrome)"),             # invariant (chaîne)
    _t("all_unique", "xs", "def check(c):\n assert c([1,2,3]) is True\n assert c([1,1]) is False\ncheck(all_unique)",
       "def check(c):\n assert c([1,2,3,4]) is True\n assert c([5,5,5]) is False\ncheck(all_unique)"),            # predicat-mesures
    _t("alternating_sum", "xs", "def check(c):\n assert c([1,2,3])==2\n assert c([10,1])==9\ncheck(alternating_sum)",
       "def check(c):\n assert c([2,3,4])==3\n assert c([1,2,3,4])==-2\ncheck(alternating_sum)"),                 # positionnel
    _t("reverse_words", "s", "def check(c):\n assert c('a b c')=='c b a'\n assert c('x')=='x'\ncheck(reverse_words)",
       "def check(c):\n assert c('one two three')=='three two one'\ncheck(reverse_words)"),                       # mots (chaîne)
    _t("count_transitions", "xs", "def check(c):\n assert c([1,1,2,3,3])==2\n assert c([1,1,1])==0\ncheck(count_transitions)",
       "def check(c):\n assert c([1,2,2,3])==2\n assert c([1,2,1,2])==3\ncheck(count_transitions)"),              # adjacence
    _t("flatten", "xss", "def check(c):\n assert c([[1,2],[3]])==[1,2,3]\n assert c([[5]])==[5]\ncheck(flatten)",
       "def check(c):\n assert c([[1],[2],[3]])==[1,2,3]\n assert c([[7,8]])==[7,8]\ncheck(flatten)"),            # imbrique (nested)
    _t("word_count", "xs", "def check(c):\n assert c(['a','b','a'])=={'a':2,'b':1}\n assert c(['x'])=={'x':1}\ncheck(word_count)",
       "def check(c):\n assert c(['a','a','b','b'])=={'a':2,'b':2}\n assert c([])=={}\ncheck(word_count)"),       # dict-accu (dict)
    _t("max_par_cle", "pairs", "def check(c):\n assert c([('a',1),('b',5),('a',3)])=={'a':3,'b':5}\ncheck(max_par_cle)",
       "def check(c):\n assert c([('a',1),('a',2),('b',9)])=={'a':2,'b':9}\ncheck(max_par_cle)"),                 # group-by (pairs->dict)
    _t("plus_longue_serie", "xs", "def check(c):\n assert c([1,1,2,2,2,3])==3\n assert c([5])==1\ncheck(plus_longue_serie)",
       "def check(c):\n assert c([4,4,4,4,1])==4\n assert c([7,7,1,1])==2\ncheck(plus_longue_serie)"),            # serie
    _t("nieme_premier", "n", "def check(c):\n assert c(1)==2\n assert c(2)==3\n assert c(3)==5\ncheck(nieme_premier)",
       "def check(c):\n assert c(4)==7\n assert c(5)==11\ncheck(nieme_premier)"),                                 # generer-tester
    _t("majuscule", "s", "def check(c):\n assert c('abc')=='ABC'\n assert c('')==''\ncheck(majuscule)",
       "def check(c):\n assert c('xy')=='XY'\n assert c('Hi!')=='HI!'\ncheck(majuscule)"),                        # substrat (chaîne)
    _t("cube", "x", "def check(c):\n assert c(2)==8\n assert c(3)==27\n assert c(0)==0\ncheck(cube)",
       "def check(c):\n assert c(4)==64\n assert c(-2)==-8\ncheck(cube)"),                                        # invention (mute carre)
    _t("double_carre", "x", "def check(c):\n assert c(2)==16\n assert c(1)==4\ncheck(double_carre)",
       "def check(c):\n assert c(3)==36\n assert c(0)==0\ncheck(double_carre)"),                                  # composition carre∘double
    _t("somme_deux", "a, b", "def check(c):\n assert c(2,3)==5\n assert c(0,0)==0\ncheck(somme_deux)",
       "def check(c):\n assert c(-1,4)==3\n assert c(10,5)==15\ncheck(somme_deux)"),                              # multi-entrée
]


def _orch(d, idx, ordre, seed):
    store = Store(Path(d) / f"s_{idx}_{seed}.jsonl")
    return GenerateurOrchestre(store, primitives=PRIMS, ops=OPS, predicats=PREDS,
                               predicteur=Predicteur(store, types=TYPES_RICHES), ordre_etages=ordre, seed=seed)


def evalue1(ordre, d, idx, seed):
    orch = _orch(d, idx, ordre, seed)
    cov, cost = 0, 0
    for t in TACHES:
        _, appels, code, _ = resoudre(orch, t, LIM, k=K)
        cost += appels
        if code is not None:
            cov += 1
    return cov, cost


def main() -> int:
    rng = random.Random(7)
    cache = {}
    t0 = time.time()

    def fit(ordre):
        cle = tuple(ordre)
        if cle not in cache:
            with tempfile.TemporaryDirectory() as d:
                rs = [evalue1(ordre, d, abs(hash(cle)) % 99999, s) for s in SEEDS]
            cache[cle] = (sum(r[0] for r in rs) / len(rs), sum(r[1] for r in rs) / len(rs))
        return cache[cle]

    def mieux(a, b):
        (ca, ka), (cb, kb) = a, b
        return (ca > cb + 1e-9) or (abs(ca - cb) < 1e-9 and ka < kb)

    def mute(ordre):
        o = list(ordre); g = rng.random()
        if g < 0.30 and len(o) > 1:
            o.insert(0, o.pop(rng.randrange(len(o))))
        elif g < 0.55 and len(o) > 1:
            i, j = rng.randrange(len(o)), rng.randrange(len(o)); o[i], o[j] = o[j], o[i]
        elif g < 0.72 and len(o) > 3:
            o.pop(rng.randrange(len(o)))
        else:
            manq = [e for e in ETAGES if e not in o]
            if manq:
                o.insert(rng.randrange(len(o) + 1), rng.choice(manq))
        return o

    cov_h, cost_h = fit(HUMAIN)
    print(f"GRAINE HUMAINE : couverture={cov_h:.1f}/{len(TACHES)}, coût={cost_h:.0f} appels (moy/{len(SEEDS)}) "
          f"[{time.time()-t0:.0f}s]", flush=True)
    if cov_h < len(TACHES):
        manques = [t.point_entree for t in TACHES
                   if resoudre(_orch(tempfile.mkdtemp(), 0, HUMAIN, 0), t, LIM, k=K)[2] is None]
        print(f"  ATTENTION : l'ordre humain ne couvre pas tout — non résolus : {manques}", flush=True)

    POP = 12
    best, score = HUMAIN, (cov_h, cost_h)
    gen = 0
    pop = [HUMAIN]
    while len(pop) < POP:
        o = list(ETAGES); rng.shuffle(o)
        pop.append(o)
    while time.time() - t0 < BUDGET_S:
        pop.sort(key=lambda o: (fit(o)[0], -fit(o)[1]), reverse=True)
        top = pop[: max(4, POP // 2)]
        if mieux(fit(top[0]), score):
            best, score = list(top[0]), fit(top[0])
        cb, kb = fit(top[0])
        print(f"  gén {gen}: best_courant couverture={cb:.1f}, coût={kb:.0f} | global={score[0]:.1f}/{score[1]:.0f} "
              f"| {len(cache)} archis | [{time.time()-t0:.0f}s]", flush=True)
        pop = list(top)
        while len(pop) < POP:
            pop.append(mute(rng.choice(top)))
        gen += 1

    cov_m, cost_m = score
    print(f"\n=== VERDICT DU RÉEL — {time.time()-t0:.0f}s, {len(cache)} architectures évaluées, {gen} générations ===", flush=True)
    print(f"  GRAINE HUMAINE  : couverture={cov_h:.1f}/{len(TACHES)}, coût={cost_h:.0f}")
    print(f"  MEILLEUR TROUVÉ : couverture={cov_m:.1f}/{len(TACHES)}, coût={cost_m:.0f}")
    print(f"  ordre trouvé    : {best}")
    if mieux((cov_m, cost_m), (cov_h, cost_h)):
        gain = 100 * (cost_h - cost_m) / cost_h if cost_h else 0
        cov = "à couverture égale" if abs(cov_m - cov_h) < 1e-9 else f"ET couverture {cov_h:.1f}->{cov_m:.1f}"
        print(f"  -> LE RÉEL SUPPLANTE L'HUMAIN : {cov}, coût {cost_h:.0f}->{cost_m:.0f} ({gain:.0f}% d'appels en moins).")
    else:
        print(f"  -> l'ordre humain TIENT (rien de strictement mieux sur l'espace fouillé). Résultat honnête.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
