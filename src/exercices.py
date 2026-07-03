"""
LE LOT D'EXERCICES CURÉS — la matière première, fournie de l'EXTÉRIEUR.

Des problèmes écrits à la main, GRADUÉS en difficulté (1 = facile), du calcul
simple vers la sécurité (l'angle VERAX). Chacun est complet : énoncé + tests
cachés + held-out + générateur d'entrées (fuzz) + solution de référence.

IMPORTANT (le garde-fou sur le curateur) : chaque exercice ici doit s'AUTO-VALIDER
— sa solution de référence passe ses propres tests ET survit au fuzz — sinon le
curateur (B8) le rejette. Le juge garde le modèle honnête ET le curateur honnête.
"""

from __future__ import annotations

from taches import Tache


def _tache(id, difficulte, prompt, point_entree, corps_ref, tests, held_out, gen):
    """Petit constructeur : assemble la référence = prompt + corps."""
    return Tache(
        id=id, difficulte=difficulte, prompt=prompt.strip(), point_entree=point_entree,
        tests=tests.strip(), solution_ref=(prompt.strip() + "\n" + corps_ref),
        tests_held_out=held_out.strip(), gen_entrees=gen.strip(),
    )


# --- Difficulté 1 : compter les pairs ---------------------------------------

COMPTE_PAIRS = _tache(
    id="exo/compte_pairs", difficulte=1, point_entree="compte_pairs",
    prompt='''
from typing import List


def compte_pairs(nombres: List[int]) -> int:
    """Compte combien d'entiers de la liste sont pairs.
    >>> compte_pairs([1, 2, 3, 4])
    2
    """''',
    corps_ref="    return sum(1 for n in nombres if n % 2 == 0)\n",
    tests='''
def check(candidate):
    assert candidate([1, 2, 3, 4]) == 2
    assert candidate([]) == 0
    assert candidate([2, 4, 6]) == 3
    assert candidate([1, 3, 5]) == 0

check(compte_pairs)
''',
    held_out='''
def check(candidate):
    assert candidate([0]) == 1
    assert candidate([-2, -4, -5]) == 2
    assert candidate([7]) == 0
    assert candidate([10, 11, 12, 13, 14]) == 3

check(compte_pairs)
''',
    gen='''
def _gen(rng):
    n = rng.randint(0, 8)
    return ([rng.randint(-50, 50) for _ in range(n)],)
''',
)


# --- Difficulté 2 : inverser l'ordre des mots --------------------------------

INVERSER_MOTS = _tache(
    id="exo/inverser_mots", difficulte=2, point_entree="inverser_mots",
    prompt='''
def inverser_mots(phrase: str) -> str:
    """Inverse l'ordre des mots d'une phrase (mots séparés par des espaces simples).
    >>> inverser_mots("le chat dort")
    'dort chat le'
    """''',
    corps_ref="    return ' '.join(phrase.split(' ')[::-1])\n",
    tests='''
def check(candidate):
    assert candidate("le chat dort") == "dort chat le"
    assert candidate("a b c d") == "d c b a"
    assert candidate("seul") == "seul"

check(inverser_mots)
''',
    held_out='''
def check(candidate):
    assert candidate("un deux") == "deux un"
    assert candidate("x y z w v") == "v w z y x"
    assert candidate("bonjour le monde") == "monde le bonjour"

check(inverser_mots)
''',
    gen='''
def _gen(rng):
    mots = [rng.choice(["a", "le", "chat", "x", "code", "bonjour", "z"])
            for _ in range(rng.randint(1, 6))]
    return (" ".join(mots),)
''',
)


# --- Difficulté 3 : robustesse d'un mot de passe (sécurité) ------------------

MDP_ROBUSTE = _tache(
    id="exo/mdp_robuste", difficulte=3, point_entree="est_mdp_robuste",
    prompt='''
def est_mdp_robuste(mdp: str) -> bool:
    """Vrai si le mot de passe a au moins 8 caractères ET contient au moins
    un chiffre, une minuscule et une majuscule.
    >>> est_mdp_robuste("abcDEF12")
    True
    >>> est_mdp_robuste("court1A")
    False
    """''',
    corps_ref=(
        "    return (len(mdp) >= 8\n"
        "            and any(c.isdigit() for c in mdp)\n"
        "            and any(c.islower() for c in mdp)\n"
        "            and any(c.isupper() for c in mdp))\n"
    ),
    tests='''
def check(candidate):
    assert candidate("abcDEF12") is True
    assert candidate("court1A") is False          # trop court
    assert candidate("abcdefg1") is False         # pas de majuscule
    assert candidate("ABCDEFG1") is False         # pas de minuscule
    assert candidate("abcDEFGH") is False         # pas de chiffre

check(est_mdp_robuste)
''',
    held_out='''
def check(candidate):
    assert candidate("Passw0rd") is True
    assert candidate("12345678") is False
    assert candidate("aB3xY9zQ") is True
    assert candidate("") is False
    assert candidate("aaaaaaaa") is False

check(est_mdp_robuste)
''',
    gen='''
def _gen(rng):
    alpha = "abcXYZ123!@ "
    n = rng.randint(0, 12)
    return ("".join(rng.choice(alpha) for _ in range(n)),)
''',
)


# --- Difficulté 4 : échapper du HTML (sécurité, l'ORDRE compte) --------------

ECHAPPE_HTML = _tache(
    id="exo/echappe_html", difficulte=4, point_entree="echappe_html",
    prompt='''
def echappe_html(texte: str) -> str:
    """Échappe les caractères dangereux pour du HTML : & devient &amp;,
    < devient &lt;, > devient &gt;. L'esperluette doit être traitée EN PREMIER.
    >>> echappe_html("a < b & c")
    'a &lt; b &amp; c'
    """''',
    corps_ref=(
        "    return texte.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')\n"
    ),
    tests='''
def check(candidate):
    assert candidate("a < b & c") == "a &lt; b &amp; c"
    assert candidate("<script>") == "&lt;script&gt;"
    assert candidate("sans danger") == "sans danger"
    assert candidate("&") == "&amp;"

check(echappe_html)
''',
    held_out='''
def check(candidate):
    assert candidate("x > y") == "x &gt; y"
    assert candidate("&<>") == "&amp;&lt;&gt;"
    assert candidate("a&&b") == "a&amp;&amp;b"
    assert candidate("") == ""

check(echappe_html)
''',
    gen='''
def _gen(rng):
    chars = "abc <>&\\"'/"
    n = rng.randint(0, 10)
    return ("".join(rng.choice(chars) for _ in range(n)),)
''',
)


# Le catalogue curé, ordonné par difficulté.
CATALOGUE = [COMPTE_PAIRS, INVERSER_MOTS, MDP_ROBUSTE, ECHAPPE_HTML]
