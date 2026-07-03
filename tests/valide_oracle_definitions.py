"""ORACLE DÉFINITIONS — la définition officielle = vérité -> savoir auto-construit -> domaines nouveaux prouvables.
AUTO-CONSTRUIT : le graphe is-a est dérivé des définitions (genre = 1er mot). NOUVEAU DOMAINE : géographie prouvée
(Paris->capitale->ville) alors qu'avant = « je ne sais pas ». TRANSITIF : 2 sauts. HONNÊTE : pas de pont inter-domaines."""
from __future__ import annotations

from oracle_definitions import Savoir, construit_isa, genre_de


def _check(nom, c):
    print(f"  [{'OK ' if c else 'RATÉ'}] {nom}")
    return c


def main() -> int:
    r = []
    sav = Savoir()

    # AUTO-CONSTRUIT : les arêtes viennent des définitions (genre extrait), pas codées à la main.
    edges = dict(construit_isa())
    r.append(_check(f"AUTO-CONSTRUIT : is-a dérivé des définitions (paris->{edges['paris']}, capitale->{edges['capitale']})",
                    edges["paris"] == "capitale" and edges["capitale"] == "ville" and edges["chat"] == "mammifère"))

    # NOUVEAU DOMAINE (géographie) prouvé par TRANSITIVITÉ depuis les seules définitions.
    r.append(_check("GÉOGRAPHIE (nouveau) : « Paris est-elle une ville ? » -> oui (Paris->capitale->ville)",
                    sav.est_un("Paris", "ville") is True))
    r.append(_check("GÉNÉRALISE : « Lyon est-elle une ville ? » -> oui (autre entrée, même domaine)",
                    sav.est_un("Lyon", "ville") is True))
    r.append(_check("DIRECT : « Paris est-elle une capitale ? » -> oui", sav.est_un("Paris", "capitale") is True))

    # HONNÊTE : pas de pont entre domaines (géographie vs animal).
    r.append(_check("HONNÊTE : « Paris est-il un mammifère ? » -> non (domaines disjoints)",
                    sav.est_un("Paris", "mammifère") is False))

    # le genre s'extrait bien du texte réel.
    r.append(_check("GENRE : extrait le 1er mot de la définition réelle",
                    genre_de("ville où siègent le gouvernement") == "ville"))

    print()
    print(f"ORACLE DÉFINITIONS VALIDÉ — {sum(r)}/{len(r)}." if all(r) else f"ÉCHEC — {sum(r)}/{len(r)}.")
    return 0 if all(r) else 1


if __name__ == "__main__":
    raise SystemExit(main())
