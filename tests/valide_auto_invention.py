"""MOTEUR D'AUTO-INVENTION — l'IA étend SEULE son répertoire, jugée par la réalité (cf. project-vision-auto-evolution-verite).
  AUTONOME  : d'une graine de 3 atomes, mint des dizaines d'atomes NOUVEAUX sans tâche humaine.
  RÉALITÉ   : tout atome gardé est déterministe + total + comportementalement DISTINCT (zéro déchet ; la vérité filtre).
  PAYOFF    : une tâche INATTEIGNABLE depuis la graine (cube=x³) devient résolue APRÈS exploration — on n'a JAMAIS nommé `cube`.
  COMPOUNDING : des atomes naissent en mutant des atomes EUX-MÊMES inventés (x⁴ depuis cube) -> le répertoire bâtit sur lui-même.
  HONNÊTE   : une tâche hors de l'espace exploré (valeur absolue) -> None, jamais de faux."""
from __future__ import annotations
from auto_invention import HELD_OUT, SONDES, MoteurAutoInvention, _empreinte
from taches import Tache


def _t(fn, tests, held):
    return Tache(id=f"ai/{fn}", point_entree=fn, prompt=f'def {fn}(x):\n    """..."""', tests=tests, tests_held_out=held)


CUBE = _t("cube",
          "def check(c):\n    assert c(2)==8\n    assert c(3)==27\n    assert c(0)==0\n    assert c(1)==1\ncheck(cube)",
          "def check(c):\n    assert c(4)==64\n    assert c(5)==125\n    assert c(-2)==-8\ncheck(cube)")
# valeur absolue : aucune expression ARITHMÉTIQUE simple (sans condition) ne l'égale sur les deux signes -> hors espace.
ABS = _t("vabs",
         "def check(c):\n    assert c(3)==3\n    assert c(-3)==3\n    assert c(5)==5\n    assert c(-5)==5\n    assert c(0)==0\ncheck(vabs)",
         "def check(c):\n    assert c(7)==7\n    assert c(-7)==7\n    assert c(9)==9\ncheck(vabs)")


def _check(nom, c):
    print(f"  [{'OK ' if c else 'RATÉ'}] {nom}")
    return c


def main() -> int:
    r = []

    graine = MoteurAutoInvention()
    n_graine = len(graine.exprs)
    mintes = graine.explore()

    r.append(_check(f"AUTONOME : graine={n_graine} atomes -> {len(mintes)} atomes mintés SANS tâche humaine",
                    n_graine == 3 and len(mintes) >= 20))

    # RÉALITÉ : tout atome gardé reste total/déterministe sur des entrées HELD-OUT, et toutes les empreintes distinctes.
    tous_valides = all(_empreinte(e, SONDES + HELD_OUT) is not None for e in mintes)
    distinctes = len(graine.empreintes) == n_graine + len(mintes)
    r.append(_check("RÉALITÉ : 100% des atomes gardés sont totaux/déterministes (held-out) ET d'empreinte unique (zéro déchet)",
                    tous_valides and distinctes))

    avant = MoteurAutoInvention().resoudre(CUBE)            # graine seule, PAS d'exploration
    apres = graine.resoudre(CUBE)                           # répertoire auto-étendu
    r.append(_check("PAYOFF : cube (x³) INATTEIGNABLE depuis la graine, RÉSOLU après exploration (jamais nommé `cube`)",
                    avant is None and apres is not None))

    profonds = [e for e in mintes if e.count("*") >= 3]    # >=3 produits : au-delà de carré(1) et cube(2) -> muté de l'inventé
    r.append(_check(f"COMPOUNDING : {len(profonds)} atomes nés en mutant un atome DÉJÀ inventé (ex. x⁴ depuis cube)",
                    len(profonds) >= 1))

    r.append(_check("HONNÊTE : valeur absolue (hors espace arithmétique exploré) -> None, jamais de faux",
                    graine.resoudre(ABS) is None))

    print()
    print(f"AUTO_INVENTION VALIDÉ — {len(r)}/{len(r)}." if all(r) else f"ÉCHEC — {sum(r)}/{len(r)}.")
    return 0 if all(r) else 1


if __name__ == "__main__":
    raise SystemExit(main())
