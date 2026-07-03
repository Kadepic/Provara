"""
Les TÂCHES — la matière première que l'on propose au modèle.

Une Tache = un énoncé (le prompt donné au générateur) + des tests CACHÉS
(que seul le juge voit). C'est le contrat standard des datasets de code à
vérificateur automatique (HumanEval, MBPP, ...).

Pour valider la brique 1 (le juge), on part d'un PROBLÈME EXISTANT et connu :
HumanEval/0 — `has_close_elements` (Chen et al., 2021, OpenAI ; dataset public).
On ne l'invente pas : on l'utilise pour prouver que le juge tranche juste.
"""

from __future__ import annotations

import dataclasses


@dataclasses.dataclass(frozen=True)
class Tache:
    """Un problème de code à juge automatique."""
    id: str                 # identifiant stable (ex. "HumanEval/0")
    prompt: str             # l'énoncé + signature donnés au générateur
    point_entree: str = ""  # nom de la fonction à résoudre (cf. 'entry_point' HumanEval) — défini plus bas
    tests: str = ""         # les tests cachés (asserts) — JAMAIS montrés au générateur
    solution_ref: str = ""  # une solution canonique connue (pour valider le juge, pas pour tricher)
    tests_held_out: str = ""  # 2e jeu de tests CACHÉ, inputs DIFFÉRENTS (cf. B5/exploits.py).
                              # Sert de contre-épreuve : une vraie solution passe les deux ;
                              # un hard-coder passe 'tests' mais échoue 'tests_held_out'.
                              # Jamais montré au générateur, ni utilisé pour archiver — uniquement
                              # pour caractériser COMMENT un candidat a passé.
    gen_entrees: str = ""     # Code définissant `_gen(rng) -> tuple` : produit des ARGUMENTS
                              # aléatoires (dont des cas aberrants) pour le FUZZING (cf. B6/fuzz.py).
                              # Le crible compare le candidat à solution_ref sur ces entrées :
                              # crash ou divergence = faille de robustesse, même si les tests passent.
    difficulte: int = 1       # niveau de la tâche (1 = facile). Le curateur (B8) sert les
                              # tâches du facile au dur, au fur et à mesure que le modèle généralise.


# --- HumanEval/0 : has_close_elements (problème existant, public) ------------

_HE0_PROMPT = '''
from typing import List


def has_close_elements(numbers: List[float], threshold: float) -> bool:
    """ Check if in given list of numbers, are any two numbers closer to each
    other than given threshold.
    >>> has_close_elements([1.0, 2.0, 3.0], 0.5)
    False
    >>> has_close_elements([1.0, 2.8, 3.0, 4.0, 5.0, 2.0], 0.3)
    True
    """
'''

# Solution canonique du dataset (référence connue — sert à prouver que le juge
# laisse bien passer le BON code).
_HE0_SOLUTION_REF = _HE0_PROMPT + '''
    for idx, elem in enumerate(numbers):
        for idx2, elem2 in enumerate(numbers):
            if idx != idx2:
                distance = abs(elem - elem2)
                if distance < threshold:
                    return True
    return False
'''

# Tests cachés du dataset (la fonction check officielle, asserts).
_HE0_TESTS = '''
def check(candidate):
    assert candidate([1.0, 2.0, 3.9, 4.0, 5.0, 2.2], 0.3) == True
    assert candidate([1.0, 2.0, 3.9, 4.0, 5.0, 2.2], 0.05) == False
    assert candidate([1.0, 2.0, 5.9, 4.0, 5.0], 0.95) == True
    assert candidate([1.0, 2.0, 5.9, 4.0, 5.0], 0.8) == False
    assert candidate([1.0, 2.0, 3.0, 4.0, 5.0, 2.0], 0.1) == True
    assert candidate([1.1, 2.2, 3.1, 4.1, 5.1], 1.0) == True
    assert candidate([1.1, 2.2, 3.1, 4.1, 5.1], 0.5) == False

check(has_close_elements)
'''

# Tests HELD-OUT : même fonction, INPUTS DIFFÉRENTS de ceux de _HE0_TESTS.
# Une solution qui généralise les passe ; une qui a mémorisé les cas visibles, non.
_HE0_TESTS_HELD_OUT = '''
def check(candidate):
    assert candidate([0.0, 10.0, 20.0], 1.0) == False
    assert candidate([0.0, 0.5, 10.0], 0.6) == True
    assert candidate([5.0], 1.0) == False
    assert candidate([1.0, 1.0], 0.0001) == True       # doublons : distance 0 < seuil
    assert candidate([-1.0, -1.2, 5.0], 0.3) == True   # négatifs
    assert candidate([100.0, 50.0, 0.0], 49.0) == False
    assert candidate([3.0, 3.4, 3.39], 0.02) == True

check(has_close_elements)
'''

# Générateur d'entrées pour le fuzzing : des listes de tailles variées (dont
# VIDE et singleton — les cas aberrants classiques), des valeurs qui peuvent être
# proches (pour créer des paires proches non adjacentes), des seuils variés.
_HE0_GEN_ENTREES = '''
def _gen(rng):
    n = rng.randint(0, 6)                       # inclut listes vides et singletons
    base = rng.uniform(-50, 50)
    xs = []
    for _ in range(n):
        if rng.random() < 0.4:
            xs.append(base + rng.uniform(-0.2, 0.2))   # valeurs proches -> paires proches
        else:
            xs.append(rng.uniform(-100, 100))
    rng.shuffle(xs)                              # proches pas forcément adjacentes
    threshold = rng.choice([rng.uniform(0, 5), 0.0, 1e-9, 0.5])
    return (xs, threshold)
'''

HUMANEVAL_0 = Tache(
    id="HumanEval/0",
    prompt=_HE0_PROMPT.strip(),
    point_entree="has_close_elements",
    tests=_HE0_TESTS.strip(),
    solution_ref=_HE0_SOLUTION_REF.strip(),
    tests_held_out=_HE0_TESTS_HELD_OUT.strip(),
    gen_entrees=_HE0_GEN_ENTREES.strip(),
)


# Registre des tâches connues (grandira ; on branchera un vrai dataset ensuite).
TACHES = {HUMANEVAL_0.id: HUMANEVAL_0}
