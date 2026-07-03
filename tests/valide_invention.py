"""
L'INVENTION par MUTATION — minter un atome NEUF, jugé par le réel (le mur d'APRÈS).

La carte du plafond (`valide_plateau.py`) a isolé une cause de blocage que la composition ne peut PAS
lever : l'ATOME absent (il manque une op/constante non dérivable des seeds). Ici on l'attaque par la voie
tranchée avec Yohan : la MUTATION de l'existant — perturber un atome CONFIRMÉ jusqu'à en faire émerger un
neuf, et laisser le juge garder ce qui marche. Interne, borné, sans modèle externe.

Deux atomes mintés, deux domaines, par une A/B falsifiable :
  cube(x) = x**3            — émerge en ALLONGEANT `x*x` (mutation M2), PAS donné.
  inverse_chaine(s) = s[::-1] — émerge en mutant le PAS d'un slice générique `s[:]` (M1), PAS donné.

Critères de MORT :
  1. MUR (cube)        : ni composition, ni jointure, ni pli (sur {carre} + {mul}) ne font x**3.
  2. INVENTION (cube)  : la mutation minte x**3, qui passe les tests ET le HELD-OUT (vrai cube, pas fluke).
  3. MUR (reverse)     : la composition sur {copie} ne renverse pas (copie∘copie = identité).
  4. INVENTION (reverse): la mutation minte s[::-1], tests + held-out.
  5. HONNÊTETÉ         : sans l'atome SOURCE (`carre` retiré), l'invention ne minte PLUS cube — elle
                         perturbe le confirmé, elle ne conjure pas (≠ énumération aveugle, ≠ seeding).
"""

from __future__ import annotations

from generateur import (GenerateurCompose, GenerateurInvention, GenerateurJointure,
                        GenerateurPli)
from juge import Limites, juge
from taches import Tache

LIM = Limites(temps_s=3, cpu_s=2)


def _t(fn, arg, tests, held):
    return Tache(id=f"inv/{fn}", point_entree=fn, prompt=f'def {fn}({arg}):\n    """..."""',
                 tests=tests, tests_held_out=held)


# --- Atomes CONFIRMÉS (la matière à muter) -----------------------------------
CARRE = ("carre", "def carre(*args, **kwargs):\n    return args[0] * args[0]\n")
MUL = ("mul", "def mul(*args, **kwargs):\n    return args[0] * args[1]\n")
COPIE = ("copie", "def copie(*args, **kwargs):\n    return args[0][:]\n")

CUBE = _t("cube", "x",
          "def check(c):\n    assert c(2) == 8\n    assert c(3) == 27\n    assert c(0) == 0\n    assert c(1) == 1\ncheck(cube)",
          "def check(c):\n    assert c(4) == 64\n    assert c(5) == 125\n    assert c(-2) == -8\ncheck(cube)")
REVERSE = _t("inverse_chaine", "s",
             "def check(c):\n    assert c('abc') == 'cba'\n    assert c('') == ''\n    assert c('x') == 'x'\ncheck(inverse_chaine)",
             "def check(c):\n    assert c('hello') == 'olleh'\n    assert c('ab') == 'ba'\n    assert c('abcd') == 'dcba'\ncheck(inverse_chaine)")


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

    # 1. MUR (cube) : composition / jointure / pli ne minte pas x**3.
    mur_cube = (_resout(GenerateurCompose([CARRE]), CUBE) is None
                and _resout(GenerateurJointure([CARRE], [MUL]), CUBE) is None
                and _resout(GenerateurPli([MUL]), CUBE) is None)
    resultats.append(_check("MUR (cube) : ni composition, ni jointure, ni pli ne font x**3 (sur {carre}+{mul})",
                            mur_cube))

    # 2. INVENTION (cube) : la mutation minte x**3, qui GÉNÉRALISE.
    inv = GenerateurInvention([CARRE, MUL])
    g_cube = _resout(inv, CUBE)
    if g_cube:
        print(f"    minté -> {g_cube.strip().splitlines()[-1].strip()}")
    resultats.append(_check("INVENTION (cube) : la mutation minte x**3, qui passe tests ET held-out (vrai cube)",
                            _generalise(g_cube, CUBE)))

    # 3. MUR (reverse) : la composition sur {copie} ne renverse pas.
    resultats.append(_check("MUR (reverse) : composition sur {copie} ne renverse pas (copie∘copie = identité)",
                            _resout(GenerateurCompose([COPIE]), REVERSE) is None))

    # 4. INVENTION (reverse) : la mutation du pas de slice minte s[::-1].
    g_rev = _resout(GenerateurInvention([COPIE]), REVERSE)
    if g_rev:
        print(f"    minté -> {g_rev.strip().splitlines()[-1].strip()}")
    resultats.append(_check("INVENTION (reverse) : la mutation minte s[::-1], tests + held-out",
                            _generalise(g_rev, REVERSE)))

    # 5. HONNÊTETÉ : sans l'atome source `carre`, plus de cube (mute le confirmé, ne conjure pas).
    resultats.append(_check("HONNÊTETÉ : sans `carre` (que `mul`), l'invention ne minte PLUS cube (perturbe, n'invente pas ex nihilo)",
                            _resout(GenerateurInvention([MUL]), CUBE) is None))

    print()
    if all(resultats):
        print(f"INVENTION VALIDÉE — {len(resultats)}/{len(resultats)}. Le moteur MINTE un atome neuf (cube, reverse) "
              f"en mutant le confirmé — la cause 'ATOME absent' du plafond TOMBE, en interne, sans modèle externe, "
              f"jugée par le réel (held-out compris). La maîtrise a précédé l'invention ; l'invention est amorcée.")
        return 0
    print(f"ÉCHEC — {sum(resultats)}/{len(resultats)}. C'est un RÉSULTAT : la mutation ne minte pas (encore) l'atome visé.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
