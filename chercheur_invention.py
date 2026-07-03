"""
CHERCHEUR D'INVENTIONS AUTONOME — couche au-dessus de `moteur_invention` vers l'OBJECTIF FINAL
(cf. [[project-ia-objectif-final-inventions]]).

Le moteur d'invention tranche UNE cible. Ici on raisonne sur un CORPUS de cibles (« tout ce qu'on
voudrait pouvoir faire ») et on répond aux deux questions de Yohan :
  1) QU'EST-CE QUI MANQUE ?  -> inventaire : EXISTE_DEJA / INVENTION / AMBIGU / BRIQUE_MANQUANTE.
  2) QUOI CONSTRUIRE EN PRIORITÉ ? -> la VALEUR d'une invention se MESURE par sa RÉUTILISATION : un
     composant (transformation) qui revient dans la solution de PLUSIEURS cibles distinctes est une
     ABSTRACTION à ajouter à la bibliothèque (principe DreamCoder : compression = valeur). Signal
     mesurable, pas une opinion -> sound.

Anti-LLM, « sûr avant rapide » : on ne RANGE en invention que ce que `moteur_invention` a vérifié
(unique sous le spec + held-out + nouveau). Les composants réutilisés sont EXTRAITS de solutions
VÉRIFIÉES (jamais inventés à la volée). Une cible ambiguë/non réalisable n'entre pas dans le compte.
"""
from __future__ import annotations

import ast
import dataclasses

import moteur_invention as MI


@dataclasses.dataclass
class Inventaire:
    par_statut: dict          # statut -> [noms de cibles]
    inventions: dict          # nom -> code (les éléments à construire)
    abstractions: list        # [(transform, [noms réutilisateurs])] trié par réutilisation décroissante

    def rapport(self) -> str:
        L = []
        for st in (MI.INVENTION, MI.AMBIGU, MI.BRIQUE_MANQUANTE, MI.EXISTE_DEJA, MI.INCOHERENT):
            noms = self.par_statut.get(st, [])
            if noms:
                L.append(f"  {st:16s}: {', '.join(noms)}")
        L.append("\n  INVENTIONS (éléments à construire) :")
        for nom, code in self.inventions.items():
            L.append(f"    • {nom}: {code}")
        L.append("\n  ABSTRACTIONS À CONSTRUIRE EN PRIORITÉ (réutilisation mesurée) :")
        if self.abstractions:
            for t, users in self.abstractions:
                L.append(f"    ★ « {t} » réutilisée par {len(users)} cibles : {', '.join(users)}")
        else:
            L.append("    (aucun composant réutilisé sur ≥2 cibles dans ce corpus)")
        return "\n".join(L)


def _transform_core(expr: str):
    """Extrait la TRANSFORMATION réutilisable d'une solution. Pour AGG(F for _e in x) -> 'F' (le cœur
    appliqué à chaque élément). Sinon -> None (pas de composant élémentaire isolable de façon sûre)."""
    try:
        arbre = ast.parse(expr, mode="eval").body
    except SyntaxError:
        return None
    # forme AGG(<gen>) : un appel dont le 1er argument est une compréhension/générateur
    if isinstance(arbre, ast.Call) and arbre.args and isinstance(arbre.args[0], (ast.GeneratorExp, ast.ListComp)):
        elt = arbre.args[0].elt
        try:
            return ast.unparse(elt)
        except Exception:
            return None
    return None


def inventorie(corpus, budget: int = 2000) -> Inventaire:
    """`corpus` = [(nom, signature, exemples, held), …]. Inventorie + mesure la réutilisation des composants."""
    par_statut: dict = {}
    inventions: dict = {}
    cores: dict = {}                       # transform -> set(noms de cibles qui la réutilisent)
    for nom, sig, ex, held in corpus:
        v = MI.examine_cible(nom, sig, ex, held, budget=budget)
        par_statut.setdefault(v.statut, []).append(nom)
        if v.statut == MI.INVENTION:
            inventions[nom] = v.par
            core = _transform_core(v.par)
            if core and core != "_e":      # '_e' = identité, pas une abstraction
                cores.setdefault(core, set()).add(nom)
    abstractions = sorted(((t, sorted(u)) for t, u in cores.items() if len(u) >= 2),
                          key=lambda p: (-len(p[1]), p[0]))
    return Inventaire(par_statut, inventions, abstractions)


if __name__ == "__main__":
    from garde_ressources import borne
    borne()
    print("=== CHERCHEUR D'INVENTIONS AUTONOME (qu'est-ce qui manque ? quoi construire d'abord ?) ===\n")
    # Corpus où le composant « carré » (_e*_e) revient -> doit émerger comme abstraction prioritaire.
    CORPUS = [
        ("somme_totale", "xs", [([1, 2, 3], 6), ([5], 5)], [([0, 4], 4), ([2, 2], 4)]),                  # existe déjà
        ("somme_carres", "xs", [([1, 2, 3], 14), ([2, 3], 13)], [([5], 25), ([0, 4], 16), ([1, 1], 2)]),  # invention (carré)
        ("max_carres", "xs", [([-3, 2], 9), ([1, 4], 16), ([-1, -5], 25)],
         [([0, 3], 9), ([2, -2], 4), ([-6, 1], 36)]),                                                      # invention (carré, négatifs)
        ("amplitude", "xs", [([3, 1, 5], 4), ([2, 2], 0), ([10, 0, 3], 10)],
         [([0, 9, 4], 9), ([7], 0), ([5, 5, 1], 4), ([2, 8], 6)]),                                         # invention (max-min)
        ("produit_cumulatif", "x", [([1, 2, 3], [1, 2, 6]), ([2, 2], [2, 4])],
         [([3, 1, 4], [3, 3, 12]), ([5], [5])]),                                                          # brique manquante (frontière)
    ]
    inv = inventorie(CORPUS)
    print(inv.rapport())
