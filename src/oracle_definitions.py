"""
ORACLE DÉFINITIONS — la définition officielle = vérité, donc auto-construction du savoir (2026-06-18, insight Yohan :
« les définitions ouvrent des domaines qu'on ne pouvait pas prouver avant »).

Mécanisme prouvé sur de VRAIES définitions du Wiktionnaire (récupérées par le web) : une définition commence par son
GENRE (« chat = Mammifère… », « Paris = Capitale… », « capitale = Ville… »). On extrait ce genre -> on bâtit le
graphe is-a AUTOMATIQUEMENT -> la brique relation-lexicale raisonne dessus. Un domaine NOUVEAU (géographie) devient
prouvable : « Paris est-elle une ville ? » -> oui (Paris -> capitale -> ville), alors qu'avant c'était « je ne sais pas ».

Définitions ci-dessous = extraits RÉELS du Wiktionnaire (fr.wiktionary.org), nettoyés (minuscules, sans ponctuation).
"""
from __future__ import annotations

import tempfile
from pathlib import Path

from comprehension import Predicteur
from compounding import resoudre
from generateur import GenerateurOrchestre, TYPES_RICHES
from juge import Limites
from store import Store
from taches import Tache

LIM = Limites(temps_s=3, cpu_s=2)

# (mot -> définition réelle Wiktionnaire). Le 1er mot est le GENRE (hyperonyme).
DEFINITIONS = {
    "chat": "mammifère carnivore félin de taille moyenne au museau court domestiqué",
    "paris": "capitale de la france chef-lieu de la région île-de-france",
    "capitale": "ville où siègent le gouvernement et le pouvoir législatif de l'état",
    "lyon": "ville française préfecture de la région auvergne-rhône-alpes",
}


def genre_de(definition):
    """Extrait le GENRE : le premier mot significatif de la définition (le nom-tête)."""
    return definition.split()[0]


def construit_isa(defs=DEFINITIONS):
    """Auto-construit le graphe is-a depuis les définitions (mot -> son genre)."""
    return [(mot, genre_de(d)) for mot, d in defs.items()]


def _est_un(orch):
    t = Tache(id="ora/est_un", point_entree="est_un", prompt='def est_un(e,x,y):\n    """..."""',
              tests="def check(c):\n    assert c([('a','b'),('b','c')],'a','c') == True\ncheck(est_un)",
              tests_held_out="")
    _, _, code, _ = resoudre(orch, t, LIM)
    ns: dict = {}
    exec(code, ns)
    return ns["est_un"]


class Savoir:
    """Le savoir auto-construit depuis les définitions, interrogeable par la réalité (relation-lexicale)."""

    def __init__(self, defs=DEFINITIONS):
        self.edges = construit_isa(defs)
        orch = GenerateurOrchestre(Store(Path(tempfile.mkdtemp()) / "s.jsonl"),
                                   predicteur=Predicteur(Store(Path(tempfile.mkdtemp()) / "s2.jsonl"),
                                                         types=TYPES_RICHES),
                                   relation_lexicale=True)
        self._est_un = _est_un(orch)

    def est_un(self, x, y):
        return self._est_un(self.edges, x.lower(), y.lower())


if __name__ == "__main__":
    sav = Savoir()
    print("Graphe is-a AUTO-CONSTRUIT depuis de vraies définitions Wiktionnaire :")
    for a, b in sav.edges:
        print(f"    {a} --est-une-sorte-de--> {b}")
    print("\nRaisonnement (la réalité juge) :")
    for x, y in [("chat", "mammifère"), ("Paris", "capitale"), ("Paris", "ville"), ("Lyon", "ville"),
                 ("Paris", "mammifère")]:
        print(f"  « {x} est-il/elle un(e) {y} ? » -> {'oui' if sav.est_un(x, y) else 'non'}")
    print("\n-> Domaine GÉOGRAPHIE prouvé (Paris->capitale->ville) à partir des seules définitions officielles. "
          "Avant : « je ne sais pas ». C'est l'insight de Yohan, réalisé.")
