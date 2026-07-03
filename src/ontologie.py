"""
ONTOLOGIE / SYSTÈME DE TYPES (subsomption sur les données) — promotion de la brique 🟡 (2026-07-02).

Raisonne sur les hiérarchies EST-UN présentes dans le corpus (ex. `taxon_parent` : felis catus → felis →
felidae → … → animalia) : subsomption transitive, ancêtres, plus proche ancêtre commun. Paresseux sur le
lecteur via `graphe_monde.chaine` — AUCUNE matérialisation de fermeture transitive (la fermeture de
taxon_parent ≈ 4 M × profondeur ~30 exploserait la RAM ; la marche à la demande coûte ≤ profondeur lookups).
Choix frugal documenté : deduction.py (Datalog) reste l'outil des PETITES bases de règles ; ici, le
substrat massif se traverse paresseusement.

INVARIANT FAUX=0, MONDE OUVERT :
  • est_un(x, T) == True  SEULEMENT si un chemin réel de faits parent relie x à T (dérivation exacte) ;
  • False signifie « NON DÉRIVABLE des faits présents » — jamais « faux dans le monde » (monde ouvert) ;
  • jamais d'inférence de type par ressemblance de nom ; entité inconnue -> False honnête ;
  • un cycle dans les données est détecté (coupé par `graphe_monde.chaine`) et signalé par `cycle()`,
    jamais parcouru à l'infini ni utilisé pour « prouver » une subsomption.
"""
from __future__ import annotations

import lecteur
import graphe_monde
from base_faits import normalise

REL_DEFAUT = "taxon_parent"     # la grande hiérarchie est-un du corpus (~4 M de faits, T4)
MAX_PROF = 60


def ancetres(x: str, rel: str = REL_DEFAUT, max_prof: int = MAX_PROF) -> list:
    """Chaîne d'ancêtres de `x` par `rel` (du plus proche au plus lointain), faits réels uniquement."""
    return graphe_monde.chaine(normalise(x), rel, max_prof)


def est_un(x: str, t: str, rel: str = REL_DEFAUT, max_prof: int = MAX_PROF) -> bool:
    """Subsomption transitive : True ssi `t` apparaît dans la chaîne d'ancêtres RÉELS de `x`.
    False = non dérivable (monde ouvert), jamais une affirmation de fausseté."""
    return normalise(t) in ancetres(x, rel, max_prof)


def plus_proche_commun(x: str, y: str, rel: str = REL_DEFAUT, max_prof: int = MAX_PROF) -> str | None:
    """Plus proche ancêtre COMMUN de deux entités (None si aucun sur les faits présents).
    Déterministe : premier ancêtre de x (ordre de proximité) présent dans les ancêtres de y."""
    ax = ancetres(x, rel, max_prof)
    ay = set(ancetres(y, rel, max_prof))
    nx = normalise(x)
    if normalise(y) in ([nx] + ax):          # y est un ancêtre de x (ou identique) -> c'est lui
        return normalise(y)
    if nx in ay:                             # x est un ancêtre de y
        return nx
    for a in ax:
        if a in ay:
            return a
    return None


def cycle(x: str, rel: str = REL_DEFAUT, max_prof: int = MAX_PROF) -> bool:
    """True si la marche depuis `x` retombe sur un maillon déjà vu (cycle RÉEL dans les données —
    violation d'acyclicité à reporter à la purge, cf. _coherence_croisee). Jamais de boucle infinie."""
    t = lecteur.LECTEUR.tables.get(rel)
    if t is None:
        return False
    vus, cur = {normalise(x)}, normalise(x)
    for _ in range(max_prof):
        f = t.get(cur)
        if f is None:
            return False
        v = normalise(str(f.valeur))
        if v in vus:
            return True
        vus.add(v)
        cur = v
    return False
