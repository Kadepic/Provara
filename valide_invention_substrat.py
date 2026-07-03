"""
INVENTION par ÉNUMÉRATION D'UN SUBSTRAT — franchir le mur de la mutation (token de langage absent).

`valide_invention_portee` a MESURÉ que la mutation ne crée pas de TOKEN absent du confirmé : `majuscule`
(s.upper(), méthode absente) et `contient_voyelle` (any(c in 'aeiou' …), littéral + appartenance absents)
restent HORS-PORTÉE de la mutation. La voie tranchée = ÉNUMÉRER un petit substrat. `GenerateurSubstrat`
énumère un vocabulaire FIXE de gabarits (méthodes unaires, appartenance à des littéraux) ; le juge garde.

A/B au niveau générateur, mécanisme contre mécanisme (la mutation est le CONTRÔLE) :
    MUTATION    (`GenerateurInvention`) : perturbe le confirmé -> ne crée pas le token -> HORS-PORTÉE.
    ÉNUMÉRATION (`GenerateurSubstrat`)  : énumère le substrat -> minte l'atome -> RÉSOLU + généralise.

Critères de MORT :
  1. MUR (mutation)    : `majuscule` ET `contient_voyelle` NON mintés par la mutation (re-confirme le mur).
  2. SUBSTRAT (méthode): l'énumération minte `majuscule = s.upper()` ET ça GÉNÉRALISE (held-out).
  3. SUBSTRAT (littéral): l'énumération minte `contient_voyelle = any(c in 'aeiou' …)` ET généralise.
  4. BORNÉ/HONNÊTE     : une cible dont le token est HORS substrat (`.replace`) reste HORS-PORTÉE — l'énumération
                         couvre un vocabulaire CHOISI, elle ne conjure pas un token arbitraire.
  5. ROUTAGE           : `majuscule` (unaire, rend une chaîne) est rangé en 'primitive' -> composable.
"""

from __future__ import annotations

from compounding import route
from generateur import GenerateurInvention, GenerateurSubstrat
from juge import Limites, juge
from taches import Tache

LIM = Limites(temps_s=3, cpu_s=2)

# Atomes confirmés à muter (le CONTRÔLE = mutation), comme dans valide_invention_portee.
ATOMES = [
    ("carre", "def carre(*args, **kwargs):\n    return args[0] * args[0]\n"),
    ("incremente", "def incremente(*args, **kwargs):\n    return args[0] + 1\n"),
    ("copie", "def copie(*args, **kwargs):\n    return args[0][:]\n"),
]


def _t(fn, tests, held=""):
    return Tache(id=f"sub/{fn}", point_entree=fn, prompt=f'def {fn}(s):\n    """..."""',
                 tests=tests, tests_held_out=held)


# Cibles : token de langage absent du confirmé (le mur de la mutation).
MAJUSCULE = _t("majuscule",
    "def check(c):\n    assert c('abc') == 'ABC'\n    assert c('') == ''\n    assert c('Ab') == 'AB'\ncheck(majuscule)",
    "def check(c):\n    assert c('xyz') == 'XYZ'\n    assert c('aB') == 'AB'\n    assert c('hi!') == 'HI!'\ncheck(majuscule)")
VOYELLE = _t("contient_voyelle",
    "def check(c):\n    assert c('xyz') is False\n    assert c('cat') is True\n    assert c('') is False\ncheck(contient_voyelle)",
    "def check(c):\n    assert c('bcd') is False\n    assert c('aei') is True\n    assert c('sky') is False\ncheck(contient_voyelle)")
# Hors substrat (token `.replace` + argument) : reste hors-portée même par énumération.
SANS_ESPACES = _t("sans_espaces",
    "def check(c):\n    assert c('a b') == 'ab'\n    assert c('  ') == ''\n    assert c('x') == 'x'\ncheck(sans_espaces)")


def _check(nom, condition):
    print(f"  [{'OK ' if condition else 'RATÉ'}] {nom}")
    return condition


def _resout(generateur, tache, n=400):
    for code in generateur.propose(tache.prompt, n):
        if juge(code, tache.tests, LIM).passe:
            return code
    return None


def _generalise(code, tache):
    return code is not None and juge(code, tache.tests_held_out, LIM).passe


def main() -> int:
    resultats = []
    mutation = GenerateurInvention(ATOMES)
    substrat = GenerateurSubstrat()

    # 1. MUR (mutation) : les deux cibles restent hors-portée de la mutation.
    resultats.append(_check(
        "MUR (mutation) : `majuscule` ET `contient_voyelle` NON mintés par la mutation (token absent)",
        _resout(mutation, MAJUSCULE) is None and _resout(mutation, VOYELLE) is None))

    # 2. SUBSTRAT (méthode) : l'énumération minte majuscule + généralise.
    g_maj = _resout(substrat, MAJUSCULE)
    if g_maj:
        print(f"    minté (substrat) -> {g_maj.strip().splitlines()[-1].strip()}")
    resultats.append(_check(
        "SUBSTRAT (méthode) : l'énumération minte `majuscule = s.upper()` ET passe le HELD-OUT",
        _generalise(g_maj, MAJUSCULE)))

    # 3. SUBSTRAT (littéral) : l'énumération minte contient_voyelle + généralise.
    g_voy = _resout(substrat, VOYELLE)
    if g_voy:
        print(f"    minté (substrat) -> {g_voy.strip().splitlines()[-1].strip()}")
    resultats.append(_check(
        "SUBSTRAT (littéral) : l'énumération minte `contient_voyelle = any(c in 'aeiou' …)` ET généralise",
        _generalise(g_voy, VOYELLE)))

    # 4. BORNÉ/HONNÊTE : un token hors substrat reste hors-portée.
    resultats.append(_check(
        "BORNÉ : une cible hors substrat (`.replace`) reste HORS-PORTÉE — l'énumération couvre un "
        "vocabulaire choisi, elle ne conjure pas un token arbitraire",
        _resout(substrat, SANS_ESPACES) is None))

    # 5. ROUTAGE : majuscule (unaire, rend une chaîne) -> primitive (composable).
    r = route(g_maj, "majuscule", LIM) if g_maj else None
    print(f"    routage : majuscule -> {r}")
    resultats.append(_check("ROUTAGE : `majuscule` rangé en 'primitive' (unaire, rend une chaîne) -> composable",
                            r == "primitive"))

    print()
    if all(resultats):
        print(f"INVENTION PAR SUBSTRAT VALIDÉE — {len(resultats)}/{len(resultats)}. Le mur de la mutation (token de "
              f"langage absent) est franchi par la voie tranchée : ÉNUMÉRER un petit substrat de gabarits (méthodes, "
              f"littéraux+appartenance). Le moteur minte `s.upper()` et `any(c in 'aeiou' …)` — hors-portée de toute "
              f"mutation — et ça généralise. Borné et honnête : hors substrat (`.replace`), rien. Un atome minté est "
              f"routé (primitive) -> composable. La couche d'invention d'après est posée, sans modèle externe. "
              f"(Caveat base-froide : le substrat est un vocabulaire choisi, il s'élargira comme TYPES_RICHES.)")
        return 0
    print(f"ÉCHEC — {sum(resultats)}/{len(resultats)}. L'énumération ne franchit pas (encore) le mur : c'est un RÉSULTAT.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
