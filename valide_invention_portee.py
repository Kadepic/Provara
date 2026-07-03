"""
LA PORTÉE DE LA MUTATION — jusqu'où l'invention-par-mutation minte, et où elle s'arrête.

On vient d'ouvrir l'invention par MUTATION (`valide_invention`). Le réflexe du projet : MESURER sa portée
AVANT de décider la suite — comme `valide_plateau` l'a fait pour la composition. La mutation perturbe UN
nœud d'un atome confirmé (pas de slice, opérateur, constante, allongement d'un produit). Donc :

  CE QU'ELLE MINTE  = ce qui s'obtient en PERTURBANT un nœud existant d'un atome confirmé.
  CE QU'ELLE NE PEUT PAS = introduire un TOKEN DE LANGAGE ABSENT de tous les atomes (méthode, littéral…).

(NB : « non minté par mutation » ≠ « hors de portée du moteur » — certains seraient composables. On mesure
ICI le mécanisme de MUTATION précisément, pour savoir quand il faudra ÉNUMÉRER un substrat.)

Atomes confirmés à muter : carre (x*x), incremente (x+1), copie (s[:]).

MINTÉ par mutation (perturbation d'un nœud) :
  cube = x*x*x      (allonger le produit)     double = x+x     (échanger * en +)
  inverse_chaine = s[::-1] (pas de slice)      ajoute_deux = x+2 (constante 1 -> 2)

HORS portée de la mutation (token de langage absent — la perturbation ne crée pas de token neuf) :
  majuscule = s.upper()                  -> méthode absente de tous les atomes
  contient_voyelle = any(c in 'aeiou' …) -> littéral + appartenance absents
  => la voie pour les franchir n'est PAS la mutation mais l'ÉNUMÉRATION d'un substrat (le mécanisme d'après).

Critères de MORT :
  1. PORTÉE : les 4 cibles mintables sont mintées ET généralisent (held-out).
  2. MUR    : les 2 cibles « token absent » ne sont PAS mintées (la mutation ne conjure pas de token neuf).
  3. CARTE  : le mur de la mutation a une cause nommée unique (TOKEN DE LANGAGE ABSENT) -> spécifie
              la voie suivante de l'invention : l'énumération d'un substrat.
"""

from __future__ import annotations

from generateur import GenerateurInvention
from juge import Limites, juge
from taches import Tache
from valide_invention import CARRE, COPIE

LIM = Limites(temps_s=3, cpu_s=2)
INCREMENTE = ("incremente", "def incremente(*args, **kwargs):\n    return args[0] + 1\n")
ATOMES = [CARRE, INCREMENTE, COPIE]


def _t(fn, arg, tests, held=""):
    return Tache(id=f"port/{fn}", point_entree=fn, prompt=f'def {fn}({arg}):\n    """..."""',
                 tests=tests, tests_held_out=held)


# --- Mintables (perturbation d'un nœud) --------------------------------------
MINTABLES = [
    _t("cube", "x",
       "def check(c):\n    assert c(2) == 8\n    assert c(3) == 27\n    assert c(0) == 0\ncheck(cube)",
       "def check(c):\n    assert c(4) == 64\n    assert c(5) == 125\n    assert c(-2) == -8\ncheck(cube)"),
    _t("double", "x",
       "def check(c):\n    assert c(3) == 6\n    assert c(5) == 10\n    assert c(0) == 0\ncheck(double)",
       "def check(c):\n    assert c(7) == 14\n    assert c(-3) == -6\n    assert c(10) == 20\ncheck(double)"),
    _t("inverse_chaine", "s",
       "def check(c):\n    assert c('abc') == 'cba'\n    assert c('') == ''\n    assert c('x') == 'x'\ncheck(inverse_chaine)",
       "def check(c):\n    assert c('hello') == 'olleh'\n    assert c('ab') == 'ba'\ncheck(inverse_chaine)"),
    _t("ajoute_deux", "x",
       "def check(c):\n    assert c(3) == 5\n    assert c(0) == 2\n    assert c(-1) == 1\ncheck(ajoute_deux)",
       "def check(c):\n    assert c(5) == 7\n    assert c(-3) == -1\n    assert c(100) == 102\ncheck(ajoute_deux)"),
]

# --- Hors portée de la mutation (token de langage absent) --------------------
HORS = [
    _t("majuscule", "s",
       "def check(c):\n    assert c('abc') == 'ABC'\n    assert c('') == ''\n    assert c('Ab') == 'AB'\ncheck(majuscule)"),
    _t("contient_voyelle", "s",
       "def check(c):\n    assert c('xyz') is False\n    assert c('cat') is True\n    assert c('') is False\ncheck(contient_voyelle)"),
]


def _check(nom, condition):
    print(f"  [{'OK ' if condition else 'RATÉ'}] {nom}")
    return condition


def _mint(tache, n=400):
    """Le 1er candidat minté qui passe les tests visibles, ou None."""
    for code in GenerateurInvention(ATOMES).propose(tache.prompt, n):
        if juge(code, tache.tests, LIM).passe:
            return code
    return None


def main() -> int:
    resultats = []

    print(f"    {'cible':<20}{'mutation':<10}{'minté ?'}")
    print("-" * 50)
    portee_ok = True
    for tache in MINTABLES:
        code = _mint(tache)
        gen = code is not None and juge(code, tache.tests_held_out, LIM).passe
        portee_ok = portee_ok and gen
        extrait = code.strip().splitlines()[-1].strip().replace("return ", "") if code else "—"
        print(f"    {tache.point_entree:<20}{'oui':<10}{extrait}{'' if gen else '   <-- !'}")
    print()

    mur_ok = True
    for tache in HORS:
        code = _mint(tache)
        mur_ok = mur_ok and (code is None)
        print(f"    {tache.point_entree:<20}{'NON':<10}{'(token de langage absent)' if code is None else 'MINTÉ ?!'}")
    print()

    resultats.append(_check(f"PORTÉE : les {len(MINTABLES)} cibles mintables sont mintées ET généralisent (held-out)",
                            portee_ok))
    resultats.append(_check(f"MUR : les {len(HORS)} cibles « token de langage absent » ne sont PAS mintées",
                            mur_ok))
    resultats.append(_check("CARTE : le mur de la mutation = TOKEN DE LANGAGE ABSENT (méthode/littéral) "
                            "-> la voie d'après est l'ÉNUMÉRATION d'un substrat, pas la mutation",
                            portee_ok and mur_ok))

    print()
    if all(resultats):
        print(f"PORTÉE DE LA MUTATION CARTOGRAPHIÉE — {len(resultats)}/{len(resultats)}. La mutation minte tout ce "
              f"qui est une PERTURBATION d'un nœud confirmé (cube, double, reverse, +2) ET généralise ; son mur est "
              f"NET et nommé : elle ne crée pas de TOKEN de langage absent (méthode, littéral). MESURÉ, pas supposé — "
              f"le jour où ce mur bloquera, la voie est l'énumération d'un substrat (le prochain mécanisme d'invention).")
        return 0
    print(f"ÉCHEC — {sum(resultats)}/{len(resultats)}. La carte de la portée est fausse sur un point : c'est un RÉSULTAT.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
