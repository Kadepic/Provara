"""
TEST DU DIABLE — « tout sert, dans le TOUT » (2026-06-17). Consigne Yohan : un test où le diable tremblerait,
activant ABSOLUMENT TOUS les étages, isolés ET plusieurs à la fois, pour être SÛR que chaque brique sert.

UN SEUL moteur, TOUS les flags ON (tous les étages en compétition simultanée). Trois parties :

  (A) CHAQUE BRIQUE SERT DANS LE TOUT — une tâche dure dédiée par étage, avec held-out ADVERSE. On exige que
      l'orchestrateur la résolve À SON ÉTAGE EXACT *alors que tous les autres sont en lice*. Un étage MASQUÉ par
      un moins cher (sa tâche résolue ailleurs) = poids mort RÉEL dans l'assemblage (≠ A/B isolé). C'est la
      vérification de l'INTÉGRÉ (cf. la leçon « validé en A/B ≠ actif dans la boucle vivante »).

  (B) PLUSIEURS BRIQUES À LA FOIS — composites vivants (montée/compounding) qui EXIGENT plusieurs étages chaînés
      en UNE session. A/B : sans rétroaction le composite tombe (émergence : le tout > la somme).

  (C) OPTIMISABLE — coût mesuré : candidats par générateur (proxy ressource) + appels juge par tâche (réel).
      Pointe les étages les plus chers (à durcir/alléger).

Sortie : pass/fail sur (A) et (B) ; (C) est un cadrage chiffré.
"""

from __future__ import annotations

import os
import tempfile
from multiprocessing import Pool
from pathlib import Path

from comprehension import Predicteur
from compounding import franchies, montee, resoudre
from curateur import CurateurGradue
from generateur import TYPES_RICHES, GenerateurOrchestre
from juge import Limites, juge
from store import Store
from taches import Tache

LIM = Limites(temps_s=3, cpu_s=2)


def _d(nom, corps):
    return (nom, f"def {nom}(*args, **kwargs):\n    return {corps}\n")


PRIMS = [_d("carre", "args[0] * args[0]"), _d("cube", "args[0] ** 3"), _d("incremente", "args[0] + 1"),
         _d("double", "args[0] + args[0]"), _d("inverse_chaine", "args[0][::-1]"), _d("trie", "sorted(args[0])"),
         _d("avant_dernier", "args[0][-2]"), _d("premier", "args[0][0]"), _d("dernier", "args[0][-1]")]
OPS = [_d("mul", "args[0] * args[1]"), _d("add", "args[0] + args[1]"), _d("sub", "args[0] - args[1]"),
       _d("mod", "args[0] % args[1]"), _d("max2", "args[0] if args[0] > args[1] else args[1]"),
       _d("min2", "args[0] if args[0] < args[1] else args[1]")]
PREDS = [_d("est_positif", "args[0] > 0"), _d("est_negatif", "args[0] < 0"),
         ("is_prime", "def is_prime(*args, **kwargs):\n    return args[0] > 1 and all(args[0] % i != 0 for i in range(2, args[0]))\n"),
         ("is_pair", "def is_pair(*args, **kwargs):\n    return args[0] % 2 == 0\n")]
# prompt EXACT de la tâche réutilisation (l'étage réutilisation matche par `s.prompt == prompt`) -> le seed doit
# porter ce prompt pour que la réutilisation (étage 0) le reprenne, au lieu que recombinaison le re-dérive.
_PROMPT_REUTIL = 'def somme_carres(xs):\n    """..."""'
STORE_SEEDS = {
    "tous_pairs": ("", "def tous_pairs(*args, **kwargs):\n    return all(x % 2 == 0 for x in args[0])\n",
                   "def check(c):\n    assert c([2,4]) is True\ncheck(tous_pairs)"),
    "compte_positifs": ("", "def compte_positifs(*args, **kwargs):\n    return sum(1 for x in args[0] if x > 0)\n",
                        "def check(c):\n    assert c([1,-2,3]) == 2\ncheck(compte_positifs)"),
    "somme_carres": (_PROMPT_REUTIL, "def somme_carres(*args, **kwargs):\n    return sum(x * x for x in args[0])\n",
                     "def check(c):\n    assert c([1,2,3]) == 14\ncheck(somme_carres)"),
}


def _t(fn, sig, tests, held):
    return Tache(id=f"diable/{fn}", point_entree=fn, prompt=f'def {fn}({sig}):\n    """..."""',
                 tests=tests, tests_held_out=held)


# (A) UNE tâche par étage — held-out ADVERSE. (étage attendu, tâche).
BATTERIE = [
    ("réutilisation", _t("somme_carres", "xs", "def check(c):\n    assert c([1,2,3]) == 14\ncheck(somme_carres)",
                         "def check(c):\n    assert c([2,3]) == 13\n    assert c([0]) == 0\ncheck(somme_carres)")),
    ("recombinaison", _t("compte_pairs", "xs", "def check(c):\n    assert c([1,2,3,4]) == 2\n    assert c([2,4,6]) == 3\ncheck(compte_pairs)",
                         "def check(c):\n    assert c([1,3,5]) == 0\n    assert c([2]) == 1\ncheck(compte_pairs)")),
    ("fusion", _t("somme_carres_positifs", "xs", "def check(c):\n    assert c([1,-2,3]) == 10\n    assert c([2]) == 4\ncheck(somme_carres_positifs)",
                  "def check(c):\n    assert c([-1,-2]) == 0\n    assert c([3,-3,4]) == 25\ncheck(somme_carres_positifs)")),
    ("composition", _t("deuxieme_plus_grand", "xs", "def check(c):\n    assert c([3,1,2]) == 2\n    assert c([5,1,4,2]) == 4\ncheck(deuxieme_plus_grand)",
                       "def check(c):\n    assert c([1,2]) == 1\n    assert c([9,7,8]) == 8\ncheck(deuxieme_plus_grand)")),
    ("jointure", _t("produit_premier_dernier", "xs", "def check(c):\n    assert c([2,3,4]) == 8\n    assert c([5,1]) == 5\ncheck(produit_premier_dernier)",
                    "def check(c):\n    assert c([3,3]) == 9\n    assert c([2,9,9,2]) == 4\ncheck(produit_premier_dernier)")),
    ("multi-entrée", _t("clamp", "x, lo, hi", "def check(c):\n    assert c(5,0,10) == 5\n    assert c(-3,0,10) == 0\n    assert c(20,0,10) == 10\ncheck(clamp)",
                       "def check(c):\n    assert c(7,1,5) == 5\n    assert c(0,2,8) == 2\ncheck(clamp)")),
    ("pli", _t("factorielle", "n", "def check(c):\n    assert c(5) == 120\n    assert c(3) == 6\n    assert c(0) == 1\ncheck(factorielle)",
              "def check(c):\n    assert c(4) == 24\n    assert c(1) == 1\ncheck(factorielle)")),
    ("branchement", _t("signe", "x", "def check(c):\n    assert c(5) == 1\n    assert c(-3) == -1\n    assert c(0) == 0\ncheck(signe)",
                       "def check(c):\n    assert c(100) == 1\n    assert c(-1) == -1\ncheck(signe)")),
    ("boucle", _t("somme_jusqua_neg", "xs", "def check(c):\n    assert c([1,2,-1,5]) == 3\n    assert c([3,4]) == 7\ncheck(somme_jusqua_neg)",
                  "def check(c):\n    assert c([-1,5]) == 0\n    assert c([2,2,2]) == 6\ncheck(somme_jusqua_neg)")),
    ("recurrence", _t("fibonacci", "n", "def check(c):\n    assert c(6) == 8\n    assert c(1) == 1\n    assert c(0) == 0\ncheck(fibonacci)",
                      "def check(c):\n    assert c(7) == 13\n    assert c(2) == 1\ncheck(fibonacci)")),
    ("while", _t("gcd", "a, b", "def check(c):\n    assert c(12,8) == 4\n    assert c(7,3) == 1\ncheck(gcd)",
                "def check(c):\n    assert c(100,60) == 20\n    assert c(17,5) == 1\ncheck(gcd)")),
    ("map-repli", _t("somme_cubes", "xs", "def check(c):\n    assert c([1,2]) == 9\n    assert c([2,3]) == 35\ncheck(somme_cubes)",
                     "def check(c):\n    assert c([3]) == 27\n    assert c([1,1,1]) == 3\ncheck(somme_cubes)")),
    ("invariant", _t("is_palindrome", "s", "def check(c):\n    assert c('aba') is True\n    assert c('ab') is False\ncheck(is_palindrome)",
                     "def check(c):\n    assert c('aa') is True\n    assert c('abc') is False\ncheck(is_palindrome)")),
    ("jointure-profonde", _t("max_minus_min", "xs", "def check(c):\n    assert c([3,1,2]) == 2\n    assert c([5,5]) == 0\ncheck(max_minus_min)",
                            "def check(c):\n    assert c([10,1,7]) == 9\n    assert c([4]) == 0\n    assert c([1,2,3,4,5]) == 4\n    assert c([1,3,5,7,9]) == 8\ncheck(max_minus_min)")),
    ("predicat-mesures", _t("all_unique", "xs", "def check(c):\n    assert c([1,2,3]) is True\n    assert c([1,1]) is False\ncheck(all_unique)",
                           "def check(c):\n    assert c([1,2,1]) is False\n    assert c([5]) is True\n    assert c([1,2,3,1]) is False\n    assert c([3,1,2]) is True\n    assert c([5,2,8,1]) is True\n    assert c([1,2,2,3]) is False\n    assert c([2,2,2]) is False\ncheck(all_unique)")),
    ("positionnel", _t("alternating_sum", "xs", "def check(c):\n    assert c([1,2,3]) == 2\n    assert c([5]) == 5\n    assert c([1,1,1,1]) == 0\ncheck(alternating_sum)",
                       "def check(c):\n    assert c([10,1,2,3]) == 8\n    assert c([4,4]) == 0\ncheck(alternating_sum)")),
    ("mots", _t("reverse_words", "s", "def check(c):\n    assert c('a b c') == 'c b a'\n    assert c('x') == 'x'\ncheck(reverse_words)",
                "def check(c):\n    assert c('un deux trois') == 'trois deux un'\ncheck(reverse_words)")),
    ("multipasse", _t("au_dessus_moyenne", "xs", "def check(c):\n    assert c([1,2,3,4]) == 2\n    assert c([10,0,0]) == 1\ncheck(au_dessus_moyenne)",
                      "def check(c):\n    assert c([5,5,5]) == 0\n    assert c([1,2,3]) == 1\ncheck(au_dessus_moyenne)")),
    ("adjacence", _t("compte_montees", "xs", "def check(c):\n    assert c([1,3,2,4]) == 2\n    assert c([5,4,3]) == 0\ncheck(compte_montees)",
                     "def check(c):\n    assert c([1,2,3]) == 2\n    assert c([7]) == 0\ncheck(compte_montees)")),
    ("imbrique", _t("somme_imbrique", "xss", "def check(c):\n    assert c([[1,2],[3]]) == 6\n    assert c([[5]]) == 5\ncheck(somme_imbrique)",
                    "def check(c):\n    assert c([[1],[2,3],[4]]) == 10\n    assert c([[10]]) == 10\ncheck(somme_imbrique)")),
    ("dict-accu", _t("word_count", "mots", "def check(c):\n    assert c(['a','b','a']) == {'a':2,'b':1}\n    assert c(['x']) == {'x':1}\ncheck(word_count)",
                     "def check(c):\n    assert c(['z','z','z']) == {'z':3}\ncheck(word_count)")),
    ("group-by", _t("max_par_cle", "paires", "def check(c):\n    assert c([('a',1),('b',5),('a',3)]) == {'a':3,'b':5}\ncheck(max_par_cle)",
                    "def check(c):\n    assert c([('x',2),('x',9)]) == {'x':9}\n    assert c([('y',1)]) == {'y':1}\ncheck(max_par_cle)")),
    ("serie", _t("plus_longue_serie", "xs", "def check(c):\n    assert c([1,1,2,2,2,3]) == 3\n    assert c([5]) == 1\ncheck(plus_longue_serie)",
                 "def check(c):\n    assert c([4,4,4,4,1]) == 4\n    assert c([1,2,3]) == 1\ncheck(plus_longue_serie)")),
    ("generer-tester", _t("nieme_premier", "n", "def check(c):\n    assert c(1) == 2\n    assert c(3) == 5\ncheck(nieme_premier)",
                         "def check(c):\n    assert c(2) == 3\n    assert c(4) == 7\ncheck(nieme_premier)")),
    ("comprehension-generale", _t("somme_cubes_au_dessus_moyenne", "xs", "def check(c):\n    assert c([1,2,3,4]) == 91\n    assert c([2,2,2]) == 0\ncheck(somme_cubes_au_dessus_moyenne)",
                                  "def check(c):\n    assert c([1,2,3]) == 27\ncheck(somme_cubes_au_dessus_moyenne)")),
    ("fenetre", _t("max_window", "xs, k", "def check(c):\n    assert c([1,2,3,4],2) == 7\n    assert c([5,1,1,5],2) == 6\ncheck(max_window)",
                   "def check(c):\n    assert c([1,2,3,4],3) == 9\n    assert c([4,1,1,1],1) == 4\n    assert c([-3,-1,-2],2) == -3\ncheck(max_window)")),
    ("matrice", _t("transpose", "m", "def check(c):\n    assert c([[1,2],[3,4]]) == [[1,3],[2,4]]\n    assert c([[1,2,3]]) == [[1],[2],[3]]\ncheck(transpose)",
                   "def check(c):\n    assert c([[1],[2],[3]]) == [[1,2,3]]\ncheck(transpose)")),
    ("repetition", _t("power", "a, b", "def check(c):\n    assert c(2,3) == 8\n    assert c(5,0) == 1\ncheck(power)",
                      "def check(c):\n    assert c(-2,3) == -8\n    assert c(2,5) == 32\ncheck(power)")),
    ("index-ordonne", _t("kth_largest", "xs, k", "def check(c):\n    assert c([3,1,2],1) == 3\n    assert c([3,1,2],2) == 2\ncheck(kth_largest)",
                         "def check(c):\n    assert c([5,4,3,2,1],5) == 1\n    assert c([10,10,20],1) == 20\ncheck(kth_largest)")),
    ("sous-suite", _t("longest_increasing", "xs", "def check(c):\n    assert c([1,3,2,4]) == 3\n    assert c([5,4,3]) == 1\ncheck(longest_increasing)",
                      "def check(c):\n    assert c([2,2,2]) == 1\n    assert c([]) == 0\ncheck(longest_increasing)")),
    ("paires", _t("two_sum_exists", "xs, t", "def check(c):\n    assert c([1,2,3],5) is True\n    assert c([1,2,3],10) is False\ncheck(two_sum_exists)",
                  "def check(c):\n    assert c([5],5) is False\n    assert c([1,2],4) is False\ncheck(two_sum_exists)")),
    ("run-length", _t("compress", "s", "def check(c):\n    assert c('aaabb') == 'a3b2'\n    assert c('x') == 'x1'\ncheck(compress)",
                      "def check(c):\n    assert c('') == ''\n    assert c('abab') == 'a1b1a1b1'\ncheck(compress)")),
    ("dict-transform", _t("invert_dict", "d", "def check(c):\n    assert c({'a':1,'b':2}) == {1:'a',2:'b'}\ncheck(invert_dict)",
                         "def check(c):\n    assert c({}) == {}\n    assert c({'x':5}) == {5:'x'}\ncheck(invert_dict)")),
    ("invention", _t("caracteres_pairs", "s", "def check(c):\n    assert c('abcdef') == 'ace'\n    assert c('a') == 'a'\ncheck(caracteres_pairs)",
                     "def check(c):\n    assert c('ab') == 'a'\n    assert c('abcde') == 'ace'\ncheck(caracteres_pairs)")),
    ("substrat", _t("majuscule", "s", "def check(c):\n    assert c('abc') == 'ABC'\n    assert c('') == ''\ncheck(majuscule)",
                    "def check(c):\n    assert c('xyz') == 'XYZ'\ncheck(majuscule)")),
    # --- 7 BRIQUES PUISSANTES (front 2026-06-17) — une tâche dure dédiée chacune, held-out ADVERSE ---
    ("profond", _t("somme_profonde", "xss", "def check(c):\n    assert c([[1,2],[3,[4,5]]]) == 15\n    assert c([1,[2,[3]]]) == 6\ncheck(somme_profonde)",
                   "def check(c):\n    assert c([[[1]]]) == 1\n    assert c([10,[20],[[30]]]) == 60\ncheck(somme_profonde)")),
    ("filtre-seuil", _t("count_above", "xs, t", "def check(c):\n    assert c([1,5,3,8],4) == 2\n    assert c([1,2,3],0) == 3\ncheck(count_above)",
                        "def check(c):\n    assert c([5,5,5],5) == 0\n    assert c([-1,-2,3],-1) == 1\ncheck(count_above)")),
    ("matrice-reduce", _t("max_row_sum", "m", "def check(c):\n    assert c([[1,2],[3,4]]) == 7\n    assert c([[5],[1],[2]]) == 5\ncheck(max_row_sum)",
                          "def check(c):\n    assert c([[1,9],[9,1]]) == 10\n    assert c([[0,0],[0,0]]) == 0\ncheck(max_row_sum)")),
    ("dedup", _t("dedup_preserve", "xs", "def check(c):\n    assert c([1,2,1,3,2]) == [1,2,3]\n    assert c([5,5,5]) == [5]\ncheck(dedup_preserve)",
                 "def check(c):\n    assert c([3,1,2,1,3]) == [3,1,2]\n    assert c([]) == []\ncheck(dedup_preserve)")),
    ("prefixe-commun", _t("lcp", "strs", "def check(c):\n    assert c(['flower','flow','flight']) == 'fl'\n    assert c(['abc','abd']) == 'ab'\ncheck(lcp)",
                          "def check(c):\n    assert c(['x','y']) == ''\n    assert c(['same','same']) == 'same'\ncheck(lcp)")),
    ("monnaie", _t("coin_change", "coins, m", "def check(c):\n    assert c([1,2,5],11) == 3\n    assert c([2],3) == -1\ncheck(coin_change)",
                   "def check(c):\n    assert c([1,3,4],6) == 2\n    assert c([5],3) == -1\ncheck(coin_change)")),
    ("cesar", _t("caesar", "s, k", "def check(c):\n    assert c('abc',1) == 'bcd'\n    assert c('xyz',3) == 'abc'\ncheck(caesar)",
                 "def check(c):\n    assert c('hello',0) == 'hello'\n    assert c('az',1) == 'ba'\ncheck(caesar)")),
    # --- front GÉNÉRATIF (record à complétude graduable) ---
    ("record", _t("resume", "xs", "def check(c):\n    assert c([1,2,3]) == {'somme': 6, 'n': 3, 'max': 3, 'min': 1}\ncheck(resume)",
                  "def check(c):\n    assert c([4,1,4]) == {'somme': 9, 'n': 3, 'max': 4, 'min': 1}\ncheck(resume)")),
    # --- briques COGNITIVES cross-domaines ---
    ("anticipation", _t("suite_ari", "xs", "def check(c):\n    assert c([1,2,3]) == 4\n    assert c([10,20,30]) == 40\ncheck(suite_ari)",
                        "def check(c):\n    assert c([5,7,9]) == 11\n    assert c([2,4,6]) == 8\ncheck(suite_ari)")),
    ("optimisation", _t("plus_long_mot", "mots", "def check(c):\n    assert c(['a','bbb','cc']) == 'bbb'\n    assert c(['x','yy']) == 'yy'\ncheck(plus_long_mot)",
                        "def check(c):\n    assert c(['aaa','b']) == 'aaa'\n    assert c(['z','zzzz','zz']) == 'zzzz'\ncheck(plus_long_mot)")),
    ("ranking", _t("trie_par_longueur", "mots", "def check(c):\n    assert c(['bbb','a','cc']) == ['a','cc','bbb']\n    assert c(['xy','x']) == ['x','xy']\ncheck(trie_par_longueur)",
                   "def check(c):\n    assert c(['xyz','x','xy']) == ['x','xy','xyz']\n    assert c(['aa','b','ccc']) == ['b','aa','ccc']\ncheck(trie_par_longueur)")),
    # --- domaines vérifiables élargis (bits / logique / ensembles) ---
    ("bits", _t("bit_xor", "a, b", "def check(c):\n    assert c(5,3) == 6\n    assert c(12,10) == 6\ncheck(bit_xor)",
                "def check(c):\n    assert c(7,1) == 6\n    assert c(255,128) == 127\ncheck(bit_xor)")),
    ("logique", _t("exactement_un", "bools", "def check(c):\n    assert c([True,False,False]) == True\n    assert c([True,True,False]) == False\ncheck(exactement_un)",
                   "def check(c):\n    assert c([False,False]) == False\n    assert c([True]) == True\n    assert c([True,True,True]) == False\n    assert c([False,True,True]) == False\ncheck(exactement_un)")),
    ("ensembles", _t("intersection", "a, b", "def check(c):\n    assert c([1,2,3],[2,3,4]) == [2,3]\n    assert c([1,2],[3,4]) == []\ncheck(intersection)",
                     "def check(c):\n    assert c([1,1,2],[2,2,3]) == [2]\n    assert c([5],[5,6]) == [5]\ncheck(intersection)")),
    # --- briques de capacité ajoutées (analyse/retranscription/calcul/graphe/combinatoire) ---
    ("statistiques", _t("mediane", "xs", "def check(c):\n    assert c([3,1,2]) == 2\n    assert c([5,1,4,2,3]) == 3\ncheck(mediane)",
                        "def check(c):\n    assert c([10,20,30]) == 20\n    assert c([100,5,50]) == 50\n    assert c([1,2]) == 2\n    assert c([1,5,9]) == 5\n    assert c([2,4,6,8,10]) == 6\ncheck(mediane)")),
    ("conversion", _t("vers_binaire", "n", "def check(c):\n    assert c(5) == '101'\n    assert c(8) == '1000'\ncheck(vers_binaire)",
                      "def check(c):\n    assert c(0) == '0'\n    assert c(255) == '11111111'\ncheck(vers_binaire)")),
    ("parsing", _t("paires_kv", "s", "def check(c):\n    assert c('a=1,b=2') == {'a':'1','b':'2'}\n    assert c('x=5') == {'x':'5'}\ncheck(paires_kv)",
                   "def check(c):\n    assert c('k=v') == {'k':'v'}\n    assert c('p=1,q=2,r=3') == {'p':'1','q':'2','r':'3'}\ncheck(paires_kv)")),
    ("math-avance", _t("isqrt", "n", "def check(c):\n    assert c(9) == 3\n    assert c(16) == 4\ncheck(isqrt)",
                       "def check(c):\n    assert c(0) == 0\n    assert c(99) == 9\n    assert c(1) == 1\ncheck(isqrt)")),
    ("chiffres", _t("somme_chiffres", "n", "def check(c):\n    assert c(123) == 6\n    assert c(45) == 9\ncheck(somme_chiffres)",
                    "def check(c):\n    assert c(0) == 0\n    assert c(999) == 27\n    assert c(10) == 1\ncheck(somme_chiffres)")),
    ("liste-transforms", _t("rotation", "xs, k", "def check(c):\n    assert c([1,2,3,4],1) == [2,3,4,1]\n    assert c([1,2,3],2) == [3,1,2]\ncheck(rotation)",
                            "def check(c):\n    assert c([5,6],1) == [6,5]\n    assert c([1,2,3,4,5],0) == [1,2,3,4,5]\ncheck(rotation)")),
    ("chaines-avancees", _t("anagramme", "a, b", "def check(c):\n    assert c('abc','cba') is True\n    assert c('abc','abd') is False\ncheck(anagramme)",
                           "def check(c):\n    assert c('aab','aba') is True\n    assert c('a','b') is False\n    assert c('ab','abc') is False\n    assert c('abc','ab') is False\ncheck(anagramme)")),
    ("diviseurs", _t("diviseurs", "n", "def check(c):\n    assert c(6) == [1,2,3,6]\n    assert c(12) == [1,2,3,4,6,12]\ncheck(diviseurs)",
                     "def check(c):\n    assert c(1) == [1]\n    assert c(7) == [1,7]\ncheck(diviseurs)")),
    ("graphe", _t("voisins", "edges, n", "def check(c):\n    assert c([(1,2),(1,3),(2,3)],1) == [2,3]\n    assert c([(0,1),(2,1)],2) == [1]\ncheck(voisins)",
                  "def check(c):\n    assert c([(1,2)],1) == [2]\n    assert c([(1,2),(1,3)],5) == []\ncheck(voisins)")),
    ("combinatoire", _t("permutations", "xs", "def check(c):\n    assert c([1,2]) == [[1,2],[2,1]]\n    assert c([1]) == [[1]]\ncheck(permutations)",
                       "def check(c):\n    assert c([]) == [[]]\n    assert c([1,2,3]) == [[1,2,3],[1,3,2],[2,1,3],[2,3,1],[3,1,2],[3,2,1]]\ncheck(permutations)")),
]


def _moteur(store, primitives, ops, predicats):
    return GenerateurOrchestre(
        store, primitives=primitives, ops=ops, predicats=predicats,
        predicteur=Predicteur(store, types=TYPES_RICHES),
        inventer=True, substrat=True, profondeur_compo=2, recurrence=True, boucle_while=True,
        map_repli=True, invariant=True, jointure_profonde=True, predicat_mesures=True,
        positionnel=True, mots=True, multipasse=True, adjacence=True, imbrique=True,
        dict_accu=True, group_by=True, serie=True, generer_tester=True, comprehension_generale=True,
        fenetre=True, matrice=True, repetition=True, index_ordonne=True, sous_suite=True,
        paires=True, run_length=True, dict_transform=True,
        profond=True, filtre_seuil=True, matrice_reduce=True, dedup=True,
        prefixe_commun=True, monnaie=True, cesar=True, record=True,
        anticipation=True, optimisation=True, ranking=True,
        bits=True, logique=True, ensembles=True,
        statistiques=True, conversion=True, parsing=True, math_avance=True, chiffres=True,
        liste_transforms=True, chaines_avancees=True, diviseurs=True, graphe=True, combinatoire=True)


def _moteur_complet(store):
    return GenerateurOrchestre(
        store, primitives=PRIMS, ops=OPS, predicats=PREDS,
        predicteur=Predicteur(store, types=TYPES_RICHES),
        inventer=True, substrat=True, profondeur_compo=2, recurrence=True, boucle_while=True,
        map_repli=True, invariant=True, jointure_profonde=True, predicat_mesures=True,
        positionnel=True, mots=True, multipasse=True, adjacence=True, imbrique=True,
        dict_accu=True, group_by=True, serie=True, generer_tester=True, comprehension_generale=True,
        fenetre=True, matrice=True, repetition=True, index_ordonne=True, sous_suite=True,
        paires=True, run_length=True, dict_transform=True,
        profond=True, filtre_seuil=True, matrice_reduce=True, dedup=True,
        prefixe_commun=True, monnaie=True, cesar=True, record=True,
        anticipation=True, optimisation=True, ranking=True,
        bits=True, logique=True, ensembles=True,
        statistiques=True, conversion=True, parsing=True, math_avance=True, chiffres=True,
        liste_transforms=True, chaines_avancees=True, diviseurs=True, graphe=True, combinatoire=True)


def _seede(store):
    for fn, (prompt, src, tests) in STORE_SEEDS.items():
        v = juge(src, tests, LIM)
        assert v.passe, f"seed {fn}"
        store.ajoute(Tache(id=f"seed/{fn}", point_entree=fn, prompt=prompt, tests=tests), src, v)


def _resoudre_tache(item):
    """Worker (1 process) : moteur COMPLET + une tâche -> (fn, attendu, appels, etage, résolu)."""
    attendu, tache = item
    with tempfile.TemporaryDirectory() as d:
        store = Store(Path(d) / "s.jsonl")
        _seede(store)
        orch = _moteur_complet(store)
        etage, appels, code, _ = resoudre(orch, tache, LIM, k=1000)   # k ≥ max candidats/étage (jointure-profonde=636) -> aucune troncature
    return (tache.point_entree, attendu, appels, etage, code is not None)


def partie_A():
    print("=== (A) CHAQUE BRIQUE SERT DANS LE TOUT (tous les étages en lice, held-out adverse) ===", flush=True)
    # SÉQUENTIEL par défaut (DIABLE_NPROC=1) — respecte « un seul process lourd à la fois » (un autre projet tourne).
    # Bump DIABLE_NPROC pour paralléliser quand la machine est libre.
    nproc = max(1, int(os.environ.get("DIABLE_NPROC", "1")))
    if nproc == 1:
        res = [_resoudre_tache(item) for item in BATTERIE]
    else:
        with Pool(processes=nproc) as pool:
            res = pool.map(_resoudre_tache, BATTERIE)
    ok, mauvais, hors, couts = 0, [], [], []
    attendu_par_fn = {t.point_entree: att for att, t in BATTERIE}
    for fn, attendu, appels, etage, resolu in res:
        couts.append((fn, attendu, appels, etage))
        if not resolu:
            hors.append((attendu, fn))
            marque = "HORS-PORTÉE !!"
        elif etage == attendu:
            ok += 1
            marque = "OK"
        else:
            mauvais.append((attendu, etage, fn))
            marque = f"MASQUÉ par `{etage}`"
        print(f"  [{marque:<22}] {attendu:<24} {fn:<28} ({appels} appels)", flush=True)
    return ok, mauvais, hors, couts


def _tc(fn, sig, vis, hel, ref, diff):
    asserts = lambda L: "def check(c):\n" + "".join(f"    assert {a}\n" for a in L) + f"check({fn})"
    return Tache(id=f"diableB/{fn}", point_entree=fn, prompt=f'def {fn}({sig}):\n    """..."""',
                 tests=asserts(vis), tests_held_out=asserts(hel),
                 solution_ref=f"def {fn}(*args, **kwargs):\n    return {ref}\n", difficulte=diff)


# Curriculum (B) : chaîne d'ÉMERGENCE (cube inventé -> somme_cubes map-repli -> somme_cubes_plus_un composé) +
# tâches de briques NEUVES (terminales) glissées dans la MÊME montée -> prouve que tout coexiste/chaîne en vivant.
TACHES_B = [
    _tc("cube", "x", ["c(2) == 8", "c(3) == 27", "c(0) == 0", "c(-2) == -8", "c(1) == 1"],
        ["c(4) == 64", "c(-3) == -27", "c(5) == 125"], "args[0] ** 3", 1),
    _tc("max_window", "xs, k", ["c([1,2,3,4],2) == 7", "c([5,1,1,5],2) == 6"],
        ["c([1,2,3,4],3) == 9", "c([-3,-1,-2],2) == -3", "c([4,1,1,1],1) == 4"],
        "max(sum(args[0][i:i+args[1]]) for i in range(len(args[0]) - args[1] + 1))", 1),
    _tc("transpose", "m", ["c([[1,2],[3,4]]) == [[1,3],[2,4]]", "c([[1,2,3]]) == [[1],[2],[3]]"],
        ["c([[1],[2],[3]]) == [[1,2,3]]"], "[list(_l) for _l in zip(*args[0])]", 1),
    _tc("somme_cubes", "xs", ["c([1,2]) == 9", "c([2,3]) == 35", "c([3]) == 27", "c([]) == 0"],
        ["c([1,2,3]) == 36", "c([-2]) == -8", "c([4]) == 64"], "sum(x ** 3 for x in args[0])", 2),
    _tc("somme_cubes_plus_un", "xs", ["c([1,2]) == 10", "c([2,3]) == 36", "c([3]) == 28", "c([]) == 1"],
        ["c([1,2,3]) == 37", "c([4]) == 65", "c([-2]) == -7"], "sum(x ** 3 for x in args[0]) + 1", 3),
]


def partie_B():
    print("\n=== (B) PLUSIEURS BRIQUES À LA FOIS — montée vivante, moteur COMPLET, A/B émergence ===", flush=True)
    # prims MINIMALES (cube ABSENT -> doit être inventé) ; tous les étages ON.
    prims = [_d("carre", "args[0] * args[0]"), _d("incremente", "args[0] + 1")]
    ops = [_d("add", "args[0] + args[1]"), _d("mul", "args[0] * args[1]"), _d("sub", "args[0] - args[1]"),
           _d("max2", "args[0] if args[0] > args[1] else args[1]"), _d("min2", "args[0] if args[0] < args[1] else args[1]")]
    preds = [_d("est_positif", "args[0] > 0")]
    cibles = [t.point_entree for t in TACHES_B]

    def run(retro, suffixe):
        with tempfile.TemporaryDirectory() as d:
            store = Store(Path(d) / f"b_{suffixe}.jsonl")
            orch = _moteur(store, prims, ops, preds)
            cur = CurateurGradue(TACHES_B, seuil=0.7, limites=LIM)
            assert not cur.rejetees, f"curriculum rejeté : {cur.rejetees}"
            journal = montee(orch, cur, store, limites=LIM, retroaction=retro, routage=True, k=400)
        return franchies(journal), journal

    f_avec, journal = run(True, "avec")
    for p in journal:
        print("   ", p.resume(), flush=True)
    f_sans, _ = run(False, "sans")
    print(f"    AVEC compounding : {sorted(f_avec)}")
    print(f"    SANS compounding : {sorted(f_sans)}")

    composites = ["somme_cubes", "somme_cubes_plus_un"]
    tout_resolu = all(c in f_avec for c in cibles)
    emergence = all(c in f_avec for c in composites) and all(c not in f_sans for c in composites)
    neuves_vivantes = "max_window" in f_avec and "transpose" in f_avec
    print(f"  [{'OK ' if tout_resolu else 'RATÉ'}] CHAÎNE+NEUVES : tout le curriculum résolu en une montée (manquants : "
          f"{[c for c in cibles if c not in f_avec]})")
    print(f"  [{'OK ' if neuves_vivantes else 'RATÉ'}] BRIQUES NEUVES VIVANTES : max_window ET transpose résolus dans la même session")
    print(f"  [{'OK ' if emergence else 'RATÉ'}] ÉMERGENCE : composites {composites} résolus AVEC, hors-portée SANS (le tout > la somme)")
    return tout_resolu and emergence and neuves_vivantes


def partie_C():
    print("\n=== (C) OPTIMISABLE — candidats par étage (proxy énergie : ce que coûte ESSAYER chaque zone) ===", flush=True)
    with tempfile.TemporaryDirectory() as d:
        store = Store(Path(d) / "s.jsonl")
        _seede(store)
        orch = _moteur_complet(store)
        cat = orch._catalogue()
        prompt = 'def f(a, b, c):\n    """..."""'
        comptes = []
        for nom, gen in cat.items():
            try:
                comptes.append((nom, len(gen.propose(prompt, 100000))))
            except Exception as e:
                comptes.append((nom, -1))
    comptes.sort(key=lambda c: -c[1])
    total = sum(c for _, c in comptes if c > 0)
    print(f"    Total candidats (somme des étages) : {total}")
    for nom, c in comptes:
        barre = "█" * min(40, c // 15)
        print(f"     {c:>5}  {nom:<22} {barre}")
    print("    -> les plus gros = les + chers à ESSAYER quand un étage tardif est requis (cible d'un routage/allègement).")
    return True


def main() -> int:
    import sys
    parts = sys.argv[1] if len(sys.argv) > 1 else "ABC"
    okA = True
    if "A" in parts:
        ok, mauvais, hors, couts = partie_A_rapport()
        okA = (ok == len(BATTERIE))
    okB = partie_B() if "B" in parts else True
    okC = partie_C() if "C" in parts else True
    print()
    if okA and okB and okC:
        print("TEST DU DIABLE VALIDÉ — chaque brique sert dans le TOUT (A), plusieurs chaînent en vivant (B), coût cartographié (C).")
        return 0
    print("TEST DU DIABLE — voir les RATÉ ci-dessus.")
    return 1


def partie_A_rapport():
    ok, mauvais, hors, couts = partie_A()
    total = len(BATTERIE)
    print(f"\n  Bilan (A) : {ok}/{total} étages résolus À LEUR étage.")
    if hors:
        print("  HORS-PORTÉE (l'étage ne résout même pas sa tâche dédiée) :")
        for att, fn in hors:
            print(f"     • {att} ({fn})")
    if mauvais:
        print("  MASQUÉS (tâche résolue par un étage moins cher -> held-out trop faible OU étage redondant) :")
        for att, eta, fn in mauvais:
            print(f"     • {att} masqué par `{eta}` ({fn})")
    print("\n  Coût par tâche (appels juge), trié décroissant :")
    for fn, att, appels, eta in sorted(couts, key=lambda c: -c[2])[:12]:
        print(f"     {appels:>5}  {att:<24} {fn} -> {eta}")

    if ok == total:
        print(f"PARTIE A VALIDÉE — {ok}/{total}. Chaque étage est l'UNIQUE résolveur de sa tâche dans le moteur complet.")
    else:
        print(f"PARTIE A — {ok}/{total}. Analyser les MASQUÉS/HORS ci-dessus (durcir la tâche ou conclure redondance).")
    return ok, mauvais, hors, couts


if __name__ == "__main__":
    raise SystemExit(main())
