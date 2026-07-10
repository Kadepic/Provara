"""
RÉSEAU TROPHIQUE — le GRAPHE orienté proie -> prédateur d'un écosystème DÉCRIT par l'utilisateur.

Posture FAUX=0 (identique à `geometries_non_euclidiennes` / `galois`) : on ne rend QUE ce que la STRUCTURE
décrite impose exactement, jamais une devinette. Distinct de `ecologie` (qui traite la CHAÎNE linéaire :
règle des 10 % + Lotka-Volterra 2 espèces) : ICI on modélise un RÉSEAU (plusieurs proies/prédateurs par
espèce) et on en déduit des propriétés EXACTES et déterministes.

MÉCANISME (définitions exactes, pas de corrélation) :
  • Niveau trophique : niveau(x) = 1 + moyenne des niveaux de ses PROIES ; une espèce SANS proie vaut 1
    (donc tout producteur vaut 1). La moyenne est calculée en `fractions.Fraction` (exact) puis rendue en
    float — un réseau où un omnivore mange des niveaux hétérogènes donne un niveau FRACTIONNAIRE (p.ex. 2.5),
    jamais arrondi à l'entier.
  • Le calcul des niveaux exige un graphe ACYCLIQUE : un cycle (a mange b qui mange a) rend le niveau
    mathématiquement indéfini -> ValueError explicite 'cycle trophique : niveau indéfini'.
  • Producteurs = espèces de type producteur ; prédateurs sommet = espèces que RIEN ne mange.
  • Chaînes(depuis, vers) = tous les chemins simples proie -> prédateur.
  • Espèces clés = espèce(s) dont le RETRAIT déconnecte le plus d'AUTRES espèces de la base productrice
    (calcul EXACT par retrait effectif et comptage de la connectivité à un producteur, PAS une heuristique).
  • effet_retrait(x) = espèces qui deviennent SANS RESSOURCE (toutes leurs proies retirées) — direct.

INVARIANTS DURS (vérifiés en adverse par `valide_reseau_trophique.py`) :
  - un producteur ne peut PAS avoir de proie -> ValueError ;
  - une espèce inconnue (nom absent) -> ValueError ;
  - un type d'espèce hors {producteur, herbivore, carnivore, omnivore, décomposeur} -> ValueError ;
  - une espèce déjà déclarée -> ValueError (déclaration déterministe, pas d'écrasement) ;
  - un cycle -> ValueError 'cycle trophique : niveau indéfini' (niveaux et longueur de chaîne max) ;
  - types invalides (bool, str vide, None, mauvaise arité) -> ValueError ;
  - fonctions PURES et déterministes (mêmes entrées -> mêmes sorties), aucun aléatoire, aucune horloge.

Stdlib uniquement (`fractions`). Aucune dépendance, aucun import de dataset.
"""
from __future__ import annotations

from fractions import Fraction

SOURCE = "définition classique du niveau trophique (Lindeman 1942 ; niveau = 1 + moyenne des niveaux des proies) + théorie des graphes orientés acycliques"

TYPES_VALIDES = frozenset({"producteur", "herbivore", "carnivore", "omnivore", "décomposeur"})
_MSG_CYCLE = "cycle trophique : niveau indéfini"


def _exige_nom(nom) -> str:
    """Un nom d'espèce est une chaîne non vide (les bool/None/nombres sont REFUSÉS)."""
    if not isinstance(nom, str) or isinstance(nom, bool) or nom == "":
        raise ValueError(f"nom d'espèce invalide : chaîne non vide attendue, reçu {nom!r}")
    return nom


class Reseau:
    """Graphe orienté proie -> prédateur d'un écosystème décrit. Toutes les requêtes sont exactes."""

    def __init__(self) -> None:
        self._type: dict[str, str] = {}          # nom -> type
        self._liens: set[tuple[str, str]] = set()  # (proie, predateur)

    # ── CONSTRUCTION ─────────────────────────────────────────────────────────────────────────────
    def ajoute_espece(self, nom: str, type: str) -> None:
        """Déclare une espèce. Type hors ensemble -> ValueError ; espèce déjà déclarée -> ValueError."""
        nom = _exige_nom(nom)
        if not isinstance(type, str) or isinstance(type, bool) or type not in TYPES_VALIDES:
            raise ValueError(
                f"type d'espèce invalide : {type!r} ; attendu l'un de {sorted(TYPES_VALIDES)}"
            )
        if nom in self._type:
            raise ValueError(f"espèce déjà déclarée : {nom!r}")
        self._type[nom] = type

    def ajoute_lien(self, proie: str, predateur: str) -> None:
        """Ajoute l'arc proie -> prédateur (le prédateur mange la proie).

        Espèce inconnue -> ValueError ; un producteur ne peut PAS avoir de proie -> ValueError."""
        proie = _exige_nom(proie)
        predateur = _exige_nom(predateur)
        self._exige_connue(proie)
        self._exige_connue(predateur)
        if self._type[predateur] == "producteur":
            raise ValueError(
                f"un producteur ne peut pas avoir de proie : {predateur!r} est producteur"
            )
        self._liens.add((proie, predateur))

    # ── HELPERS ──────────────────────────────────────────────────────────────────────────────────
    def _exige_connue(self, nom: str) -> None:
        if nom not in self._type:
            raise ValueError(f"espèce inconnue : {nom!r}")

    def _proies(self, x: str) -> set[str]:
        """Proies de x = espèces p telles que (p, x) est un arc (p mangé par x)."""
        return {p for (p, pred) in self._liens if pred == x}

    def _predateurs(self, x: str) -> set[str]:
        """Prédateurs de x = espèces q telles que (x, q) est un arc (x mangé par q)."""
        return {q for (p, q) in self._liens if p == x}

    # ── NIVEAU TROPHIQUE ─────────────────────────────────────────────────────────────────────────
    def niveau_trophique(self, espece: str) -> float:
        """niveau(x) = 1 + moyenne des niveaux des proies ; sans proie -> 1. Cycle -> ValueError."""
        espece = _exige_nom(espece)
        self._exige_connue(espece)
        memo: dict[str, Fraction] = {}
        pile: set[str] = set()

        def rec(x: str) -> Fraction:
            if x in memo:
                return memo[x]
            if x in pile:
                raise ValueError(_MSG_CYCLE)
            pile.add(x)
            proies = self._proies(x)
            if not proies:
                val = Fraction(1)
            else:
                total = sum((rec(p) for p in sorted(proies)), Fraction(0))
                val = Fraction(1) + total / Fraction(len(proies))
            pile.discard(x)
            memo[x] = val
            return val

        return float(rec(espece))

    # ── DESCRIPTEURS DE STRUCTURE ────────────────────────────────────────────────────────────────
    def producteurs(self) -> list[str]:
        """Espèces de type producteur (base du réseau), triées."""
        return sorted(n for n, t in self._type.items() if t == "producteur")

    def predateurs_sommet(self) -> list[str]:
        """Prédateurs au sommet : espèces déclarées que RIEN ne mange (aucun prédateur), triées."""
        return sorted(n for n in self._type if not self._predateurs(n))

    def chaines(self, depuis: str, vers: str) -> list[tuple[str, ...]]:
        """Tous les chemins simples proie -> prédateur de `depuis` vers `vers` (déterministe, triés)."""
        depuis = _exige_nom(depuis)
        vers = _exige_nom(vers)
        self._exige_connue(depuis)
        self._exige_connue(vers)
        resultats: list[tuple[str, ...]] = []

        def dfs(noeud: str, chemin: list[str]) -> None:
            if noeud == vers:
                resultats.append(tuple(chemin))
                return
            for suiv in sorted(self._predateurs(noeud)):
                if suiv not in chemin:
                    dfs(suiv, chemin + [suiv])

        dfs(depuis, [depuis])
        return resultats

    def longueur_chaine_max(self) -> int:
        """Nombre d'espèces du plus long chemin simple du réseau. Cycle -> ValueError. Vide -> 0."""
        memo: dict[str, int] = {}
        pile: set[str] = set()

        def lp(x: str) -> int:
            if x in memo:
                return memo[x]
            if x in pile:
                raise ValueError(_MSG_CYCLE)
            pile.add(x)
            succ = self._predateurs(x)
            best = 1 + max((lp(s) for s in succ), default=0)
            pile.discard(x)
            memo[x] = best
            return best

        return max((lp(x) for x in self._type), default=0)

    # ── ANALYSE DE RETRAIT ───────────────────────────────────────────────────────────────────────
    def _supportees(self, exclus: frozenset[str]) -> set[str]:
        """Espèces (hors `exclus`) reliées à un producteur via une chaîne de proies présentes."""
        memo: dict[str, bool] = {}
        pile: set[str] = set()

        def sup(x: str) -> bool:
            if x in exclus:
                return False
            if x in memo:
                return memo[x]
            if self._type[x] == "producteur":
                memo[x] = True
                return True
            if x in pile:
                return False  # arête d'un cycle : ne fournit pas de support fondé
            pile.add(x)
            r = any(sup(p) for p in self._proies(x))
            pile.discard(x)
            memo[x] = r
            return r

        return {x for x in self._type if x not in exclus and sup(x)}

    def effet_retrait(self, espece: str) -> list[str]:
        """Espèces qui deviennent SANS RESSOURCE si `espece` est retirée (toutes leurs proies parties)."""
        espece = _exige_nom(espece)
        self._exige_connue(espece)
        res = []
        for x in self._type:
            if x == espece:
                continue
            proies = self._proies(x)
            if proies and not (proies - {espece}):
                res.append(x)
        return sorted(res)

    def especes_cles(self) -> list[str]:
        """Espèce(s) dont le retrait déconnecte le PLUS d'autres espèces de la base productrice.

        Calcul EXACT : pour chaque espèce, on la retire réellement et on compte combien d'AUTRES
        espèces perdent toute connexion à un producteur. On renvoie celles au maximum (liste triée,
        vide si aucun retrait ne déconnecte quoi que ce soit)."""
        base = self._supportees(frozenset())
        meilleur = 0
        comptes: dict[str, int] = {}
        for c in self._type:
            apres = self._supportees(frozenset({c}))
            deconnectees = (base - {c}) - apres
            n = len(deconnectees)
            comptes[c] = n
            if n > meilleur:
                meilleur = n
        if meilleur == 0:
            return []
        return sorted(c for c, n in comptes.items() if n == meilleur)
