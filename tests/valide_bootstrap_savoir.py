"""BOOTSTRAP_SAVOIR — l'IA construit SEULE une taxonomie multi-niveaux en remontant les définitions.
MULTI-NIVEAUX : chaînes auto-dérivées (Paris->capitale->ville->agglomération, 3 niveaux). FRONTIÈRE : sait quoi aller
chercher ensuite. PROFOND : raisonnement transitif sur 3 sauts. HONNÊTE : pas de pont inter-domaines."""
from __future__ import annotations

from bootstrap_savoir import Savoir, chaine, frontiere


def _check(nom, c):
    print(f"  [{'OK ' if c else 'RATÉ'}] {nom}")
    return c


def main() -> int:
    r = []
    sav = Savoir()

    cp = chaine("paris", sav.edges)
    r.append(_check(f"MULTI-NIVEAUX : chaîne auto-construite paris = {cp}",
                    cp == ["paris", "capitale", "ville", "agglomération"]))

    cc = chaine("chat", sav.edges)
    r.append(_check(f"AUTRE CHAÎNE : chat = {cc}", cc == ["chat", "mammifère", "animal"]))

    fr = frontiere()
    r.append(_check(f"FRONTIÈRE : genres non encore définis à aller chercher = {fr}",
                    "animal" in fr and "agglomération" in fr))

    r.append(_check("PROFOND : « Paris est-elle une agglomération ? » -> oui (3 niveaux)",
                    sav.est_un("Paris", "agglomération") is True))
    r.append(_check("PROFOND 2 : « chat est-il un animal ? » -> oui (2 niveaux)",
                    sav.est_un("chat", "animal") is True))

    r.append(_check("HONNÊTE : « chat est-il une ville ? » -> non (domaines disjoints)",
                    sav.est_un("chat", "ville") is False))

    print()
    print(f"BOOTSTRAP SAVOIR VALIDÉ — {sum(r)}/{len(r)}." if all(r) else f"ÉCHEC — {sum(r)}/{len(r)}.")
    return 0 if all(r) else 1


if __name__ == "__main__":
    raise SystemExit(main())
