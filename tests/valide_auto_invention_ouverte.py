"""MOTEUR D'AUTO-INVENTION OUVERTE — composition universelle, multi-domaines, jugé par la réalité (cap auto-évolution).
L'espace n'est plus un menu d'opérateurs semé par nous : c'est la COMPOSITION (combinateur universel) + map, sur des
primitives typées (entiers ↔ listes). L'architecture n'a donc PAS de plafond qu'on impose.
  OUVERT      : graine 16 -> des centaines d'atomes sur 4 signatures de type, SANS tâche humaine.
  RÉALITÉ     : tout atome gardé est typé, total, et d'empreinte UNIQUE (zéro déchet ; la vérité filtre, held-out inclus).
  FRONTIÈRE   : des tâches RÉELLES jamais montrées, inatteignables depuis la graine (0/2), deviennent résolues (2/2).
  PROFONDEUR/COMPOUNDING : la solution de « somme des carrés » est sum ∘ map(carré) — composée sur un atome INVENTÉ.
  HONNÊTE     : « produit » (aucun fold-produit dans l'espace) -> None ; held-out ADVERSAIRE tue les coïncidences."""
from __future__ import annotations
from auto_invention_ouverte import MoteurOuvert
from taches import Tache


def _t(fn, tests, held):
    return Tache(id=f"aio/{fn}", point_entree=fn, prompt=f'def {fn}(x):\n    """..."""', tests=tests, tests_held_out=held)


# held-out ADVERSAIRE (négatifs) -> force le VRAI atome compositionnel, rejette les coïncidences.
SOMME_CARRES = _t("f", "def check(c):\n    assert c([1,2,3])==14\n    assert c([2,3])==13\ncheck(f)",
                  "def check(c):\n    assert c([-2,3])==13\n    assert c([-1,-4])==17\ncheck(f)")          # sum ∘ map(carré)
TRIANGULAIRE = _t("f", "def check(c):\n    assert c(4)==6\n    assert c(5)==10\ncheck(f)",
                  "def check(c):\n    assert c(1)==0\n    assert c(6)==15\ncheck(f)")                       # sum ∘ range
PRODUIT = _t("f", "def check(c):\n    assert c([1,2,3,4])==24\n    assert c([2,3])==6\ncheck(f)",
             "def check(c):\n    assert c([5,2])==10\ncheck(f)")                                            # hors espace -> None


def _check(nom, c):
    print(f"  [{'OK ' if c else 'RATÉ'}] {nom}")
    return c


def main() -> int:
    moteur = MoteurOuvert()
    n_graine = len(moteur.atomes)
    moteur.explore(rounds=3, cap=800)
    r = []

    types = {(ti, to) for _, ti, to in moteur.atomes}
    r.append(_check(f"OUVERT MULTI-DOMAINE : graine {n_graine} -> {len(moteur.atomes)} atomes sur {len(types)} "
                    f"signatures {sorted(types)}, sans tâche humaine",
                    n_graine == 16 and len(moteur.atomes) >= 400 and len(types) >= 4))

    r.append(_check("RÉALITÉ : empreintes toutes UNIQUES (zéro doublon comportemental ; held-out validé à l'insertion)",
                    len(moteur.empreintes) == len(moteur.atomes)))

    graine = MoteurOuvert()                                   # graine seule, PAS d'exploration
    f_graine = sum(1 for tk in (SOMME_CARRES, TRIANGULAIRE) if graine.resoudre(tk))
    f_apres = sum(1 for tk in (SOMME_CARRES, TRIANGULAIRE) if moteur.resoudre(tk))
    r.append(_check(f"FRONTIÈRE S'ÉTEND SEULE : tâches profondes résolues {f_graine}/2 (graine) -> {f_apres}/2 (exploré)",
                    f_graine == 0 and f_apres == 2))

    sol = moteur.resoudre(SOMME_CARRES)
    r.append(_check("PROFONDEUR/COMPOUNDING : « somme des carrés » = sum ∘ map(carré) (composé sur un atome INVENTÉ)",
                    sol is not None and "for e in x" in sol))

    r.append(_check("HONNÊTE : « produit » (aucun fold-produit dans l'espace) -> None, jamais de faux",
                    moteur.resoudre(PRODUIT) is None))

    print()
    print(f"AUTO_INVENTION_OUVERTE VALIDÉ — {len(r)}/{len(r)}." if all(r) else f"ÉCHEC — {sum(r)}/{len(r)}.")
    return 0 if all(r) else 1


if __name__ == "__main__":
    raise SystemExit(main())
