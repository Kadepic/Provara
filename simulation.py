"""
SIMULATION / FORWARD-MODEL — brique Vague 3. Dépend de etat.py (+ loi.py pour les règles physiques).

POURQUOI : pour valider une invention, il faut PRÉDIRE le comportement d'un design — faire évoluer son état dans le
temps selon des règles. C'est le maillon loi→limite→écart→design : on mesure l'écart d'un système réel ET on vérifie
qu'un design proposé se comporte comme prévu (ou le falsifie). Sans modèle exécutable du monde, « inventer » reste du
récit.

MODÈLE : un `Simulateur` = un EspaceEtats + des RÈGLES de transition (chaque règle : `fn(etat) -> {var: nouvelle
valeur}` ou None). `pas` applique toutes les règles pour produire l'état suivant ; `simule` déroule une trajectoire ;
`point_fixe` cherche un équilibre.

FAUX=0 :
  • DÉTERMINISTE : règles appliquées dans l'ordre ; même entrée -> même trajectoire.
  • Chaque état produit est VALIDÉ par l'espace (via etat.avec) -> jamais un état hors domaine/dimension.
  • CONFLIT de règles (deux règles imposent des valeurs DIFFÉRENTES à la même variable) -> `ConflitDeRegles`
    (jamais un choix silencieux).
  • TERMINANT : `simule(n)` borne les pas ; `point_fixe` a un budget et renvoie HONNÊTEMENT « non convergé » sinon
    (jamais une convergence fabriquée).
Stdlib pur, souverain. L'intégration numérique continue (EDO) est une extension ultérieure ; ici, pas discrets.
"""
from __future__ import annotations


class ConflitDeRegles(Exception):
    """Deux règles imposent des valeurs différentes à la même variable au même pas — rejet FAUX=0 (pas de choix caché)."""


class Simulateur:
    __slots__ = ("espace", "regles")

    def __init__(self, espace, regles):
        self.espace = espace
        self.regles = list(regles)               # [fn(etat) -> dict|None]

    def pas(self, etat):
        """Un pas de simulation : applique toutes les règles, fusionne les changements (conflit -> erreur),
        renvoie l'état suivant VALIDÉ."""
        changements = {}
        for r in self.regles:
            d = r(etat) or {}
            for var, val in d.items():
                if var in changements and changements[var] != val:
                    raise ConflitDeRegles(f"règles en conflit sur {var!r} : {changements[var]!r} vs {val!r}")
                changements[var] = val
        return etat.avec(**changements)          # re-validation par l'espace (FAUX=0)

    def simule(self, etat0, n: int, arret_point_fixe: bool = True) -> list:
        """Trajectoire [etat0, etat1, …] sur au plus `n` pas. S'arrête tôt si point fixe (état inchangé)."""
        traj = [etat0]
        cur = etat0
        for _ in range(n):
            suiv = self.pas(cur)
            traj.append(suiv)
            if arret_point_fixe and suiv == cur:
                break
            cur = suiv
        return traj

    def point_fixe(self, etat0, max_pas: int = 1000):
        """(état d'équilibre, converge: bool). converge=False = budget épuisé sans point fixe (honnête, pas fabriqué)."""
        cur = etat0
        for _ in range(max_pas):
            suiv = self.pas(cur)
            if suiv == cur:
                return cur, True
            cur = suiv
        return cur, False
