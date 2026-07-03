"""
BOOTSTRAP_SAVOIR — l'IA construit SEULE une taxonomie multi-niveaux en lisant les définitions (2026-06-18).

Cascade : une définition donne son GENRE (1er mot) ; le genre a lui-même une définition ; en remontant, l'IA bâtit
un graphe is-a PROFOND, puis raisonne sur tous les niveaux. Elle sait aussi quoi aller chercher ensuite (la FRONTIÈRE
= genres cités mais pas encore définis -> prochains WebFetch). Boucle d'auto-extension du savoir, vérifiable à chaque arête.

Définitions = extraits RÉELS du Wiktionnaire (fr.wiktionary.org), nettoyés. Chaînes obtenues :
  chat -> mammifère -> animal           |   Paris -> capitale -> ville -> agglomération
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

DEFINITIONS = {
    "chat": "mammifère carnivore félin de taille moyenne au museau court domestiqué",
    "mammifère": "animal qui porte des mamelles pour allaiter ses petits",
    "paris": "capitale de la france chef-lieu de la région île-de-france",
    "capitale": "ville où siègent le gouvernement et le pouvoir législatif de l'état",
    "lyon": "ville française préfecture de la région auvergne-rhône-alpes",
    "ville": "agglomération ordonnée d'un nombre considérable de maisons disposées par rues",
}


def genus(definition):
    return definition.split()[0]


def graphe(defs=DEFINITIONS):
    """is-a auto-construit : (mot -> son genre) pour chaque définition."""
    return [(mot, genus(d)) for mot, d in defs.items()]


def chaine(mot, edges):
    """Remonte la chaîne is-a complète depuis un mot (avec garde anti-cycle)."""
    suiv = dict(edges)
    out, cur, vus = [mot], mot, {mot}
    while cur in suiv and suiv[cur] not in vus:
        cur = suiv[cur]
        out.append(cur)
        vus.add(cur)
    return out


def frontiere(defs=DEFINITIONS):
    """Genres CITÉS mais pas encore définis = ce que l'IA doit aller chercher pour creuser (prochains fetch)."""
    genres = {genus(d) for d in defs.values()}
    return sorted(g for g in genres if g not in defs)


def _est_un(orch):
    t = Tache(id="bs/est_un", point_entree="est_un", prompt='def est_un(e,x,y):\n    """..."""',
              tests="def check(c):\n    assert c([('a','b'),('b','c')],'a','c') == True\ncheck(est_un)", tests_held_out="")
    _, _, code, _ = resoudre(orch, t, LIM)
    ns: dict = {}
    exec(code, ns)
    return ns["est_un"]


class Savoir:
    def __init__(self, defs=DEFINITIONS):
        self.edges = graphe(defs)
        orch = GenerateurOrchestre(Store(Path(tempfile.mkdtemp()) / "s.jsonl"),
                                   predicteur=Predicteur(Store(Path(tempfile.mkdtemp()) / "s2.jsonl"),
                                                         types=TYPES_RICHES),
                                   relation_lexicale=True)
        self._est_un = _est_un(orch)

    def est_un(self, x, y):
        return self._est_un(self.edges, x.lower(), y.lower())


if __name__ == "__main__":
    sav = Savoir()
    print("Taxonomie AUTO-CONSTRUITE par cascade de définitions :")
    for mot in ("chat", "paris", "lyon"):
        print(f"    {mot} : {' -> '.join(chaine(mot, sav.edges))}")
    print(f"\nFRONTIÈRE (à aller chercher pour creuser) : {frontiere()}")
    print("\nRaisonnement PROFOND (multi-niveaux, la réalité juge) :")
    for x, y in [("chat", "animal"), ("Paris", "ville"), ("Paris", "agglomération"), ("Lyon", "agglomération"),
                 ("chat", "ville")]:
        n = len(chaine(x.lower(), sav.edges)) - 1
        print(f"  « {x} est-il/elle un(e) {y} ? » -> {'oui' if sav.est_un(x, y) else 'non'}")
    print("\n-> L'IA lit le dictionnaire et bâtit SEULE sa taxonomie ; Paris->agglomération = 3 niveaux, "
          "tout dérivé des seules définitions officielles.")
