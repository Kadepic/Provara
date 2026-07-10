"""
CONFIGURATION ÉLECTRONIQUE — remplissage d'Aufbau (règle de Klechkowski) + catalogue d'exceptions MESURÉES.

Même posture FAUX=0 que `physique` / `chimie` / `geometries_non_euclidiennes` (la réalité juge, jamais un faux) :
  • Le MÉCANISME est double, et la frontière entre les deux est EXPLICITE :
      – RÈGLE de Klechkowski (Madelung) : les sous-couches se remplissent par (n+l) croissant, puis n croissant :
            1s 2s 2p 3s 3p 4s 3d 4p 5s 4d 5p 6s 4f 5d 6p 7s 5f 6d 7p
        avec les capacités s=2, p=6, d=10, f=14. C'est une RÈGLE empirique, pas une loi exacte.
      – CATALOGUE d'exceptions ÉTABLIES : pour 20 éléments (Cr, Cu, Nb, Mo, Ru, Rh, Pd, Ag, La, Ce, Gd, Pt,
        Au, Ac, Th, Pa, U, Np, Cm, Lr), l'état fondamental MESURÉ (spectroscopie, NIST Atomic Spectra Database)
        VIOLE la règle. Ces configurations sont RENDUES depuis le catalogue (fait mesuré), jamais dérivées
        d'Aufbau. `statut(Z)` dit lequel des deux mécanismes a produit la réponse.
  • CONVENTIONS (dites, pas cachées) :
      – `configuration(Z)` : ordre de REMPLISSAGE (ex. '... 4s2 3d6' pour Fe) pour les éléments réguliers ;
        pour une exception : cœur de gaz rare développé (ordre de remplissage) puis queue mesurée triée (n, l).
      – `configuration_condensee(Z)` : '[gaz rare] ...' avec la queue triée par (n, l) — ex. '[Ar] 3d6 4s2'.
        H et He n'ont pas de gaz rare précédent : la forme condensée est la forme complète.
      – `couche_valence(Z)` / `electrons_valence(Z)` : couche EXTERNE = plus grand n occupé, et nombre
        d'électrons dans cette couche (convention « couche externe » ; pour Pd, [Kr]4d10, la couche externe
        est n=4 avec 18 électrons — fait connu, aucune couche n=5 occupée).
      – `bloc(Z)` : sous-couche qui reçoit le Z-ième électron dans l'ordre de Klechkowski PUR (position dans
        le tableau périodique, forme « Lu sous Y » recommandée provisoirement par l'IUPAC 2021 : La et Ac
        sont bloc f, Lu et Lr bloc d). Indépendant des exceptions mesurées, et c'est DIT.
      – Pour Z ≥ 104 (transactinides), aucune configuration n'est mesurée : Aufbau est rendu comme
        CONVENTION de tableau périodique (statut = règle d'Aufbau), pas comme fait spectroscopique.

GARANTIES (vérifiées en adverse par `valide_configuration_electronique.py`) :
  - Z < 1 ou Z > 118 -> ValueError (aucun élément) ;
  - Z non entier (float même entier, str, None, NaN, inf) ou bool -> ValueError (True n'est pas 1) ;
  - INVARIANT : pour tout Z de 1 à 118, la somme des électrons de la configuration rendue vaut exactement Z ;
  - les exceptions du catalogue sont rendues TELLES QUE MESURÉES (Cr 3d5 4s1, Pd 4d10 sans 5s, ...) ;
  - déterministe ; conservateur (faux négatif/abstention toléré, faux POSITIF interdit).

Toutes les fonctions sont PURES et déterministes ; stdlib uniquement (aucun import de dataset, aucun état).
"""
from __future__ import annotations

SOURCE = ("règle de Klechkowski/Madelung (ordre n+l croissant puis n croissant) ; "
          "exceptions = états fondamentaux mesurés, NIST Atomic Spectra Database (spectroscopie)")

Z_MAX = 118  # oganesson : dernier élément reconnu (IUPAC)

# Ordre de Klechkowski : (n, l) par (n+l) croissant puis n croissant — suffit pour Z <= 118.
_ORDRE_KLECHKOWSKI = (
    (1, "s"), (2, "s"), (2, "p"), (3, "s"), (3, "p"), (4, "s"), (3, "d"), (4, "p"),
    (5, "s"), (4, "d"), (5, "p"), (6, "s"), (4, "f"), (5, "d"), (6, "p"), (7, "s"),
    (5, "f"), (6, "d"), (7, "p"),
)

_CAPACITE = {"s": 2, "p": 6, "d": 10, "f": 14}

# l numérique pour le tri (n, l) de la notation condensée / des queues d'exceptions.
_L_NUM = {"s": 0, "p": 1, "d": 2, "f": 3}

# Gaz rares (couche p pleine, sauf He) : Z croissant. Utilisés comme cœurs de la notation condensée.
_GAZ_RARES = ((2, "He"), (10, "Ne"), (18, "Ar"), (36, "Kr"), (54, "Xe"), (86, "Rn"))

# ── CATALOGUE D'EXCEPTIONS MESURÉES (NIST ASD, états fondamentaux) ─────────────────────────────────────────────
# Queue AU-DELÀ du gaz rare précédent, triée par (n, l). Ce sont des FAITS de spectroscopie, pas des règles.
# NB : Lr (Z=103, [Rn] 5f14 7s2 7p1, terme ²P°1/2) est ajouté au catalogue : Aufbau donnerait 6d1 7s2,
# la mesure/analyse NIST donne 7s2 7p1 — le rendre par Aufbau serait un FAUX.
_EXCEPTIONS = {
    24:  ((3, "d", 5), (4, "s", 1)),                            # Cr  [Ar] 3d5 4s1
    29:  ((3, "d", 10), (4, "s", 1)),                           # Cu  [Ar] 3d10 4s1
    41:  ((4, "d", 4), (5, "s", 1)),                            # Nb  [Kr] 4d4 5s1
    42:  ((4, "d", 5), (5, "s", 1)),                            # Mo  [Kr] 4d5 5s1
    44:  ((4, "d", 7), (5, "s", 1)),                            # Ru  [Kr] 4d7 5s1
    45:  ((4, "d", 8), (5, "s", 1)),                            # Rh  [Kr] 4d8 5s1
    46:  ((4, "d", 10),),                                       # Pd  [Kr] 4d10  (couche 5 VIDE)
    47:  ((4, "d", 10), (5, "s", 1)),                           # Ag  [Kr] 4d10 5s1
    57:  ((5, "d", 1), (6, "s", 2)),                            # La  [Xe] 5d1 6s2
    58:  ((4, "f", 1), (5, "d", 1), (6, "s", 2)),               # Ce  [Xe] 4f1 5d1 6s2
    64:  ((4, "f", 7), (5, "d", 1), (6, "s", 2)),               # Gd  [Xe] 4f7 5d1 6s2
    78:  ((4, "f", 14), (5, "d", 9), (6, "s", 1)),              # Pt  [Xe] 4f14 5d9 6s1
    79:  ((4, "f", 14), (5, "d", 10), (6, "s", 1)),             # Au  [Xe] 4f14 5d10 6s1
    89:  ((6, "d", 1), (7, "s", 2)),                            # Ac  [Rn] 6d1 7s2 (NIST ASD, ²D3/2 ;
                                                                #     analogue de La — Aufbau donnerait 5f1)
    90:  ((6, "d", 2), (7, "s", 2)),                            # Th  [Rn] 6d2 7s2  (aucun 5f !)
    91:  ((5, "f", 2), (6, "d", 1), (7, "s", 2)),               # Pa  [Rn] 5f2 6d1 7s2
    92:  ((5, "f", 3), (6, "d", 1), (7, "s", 2)),               # U   [Rn] 5f3 6d1 7s2
    93:  ((5, "f", 4), (6, "d", 1), (7, "s", 2)),               # Np  [Rn] 5f4 6d1 7s2
    96:  ((5, "f", 7), (6, "d", 1), (7, "s", 2)),               # Cm  [Rn] 5f7 6d1 7s2
    103: ((5, "f", 14), (7, "s", 2), (7, "p", 1)),              # Lr  [Rn] 5f14 7s2 7p1
}


# ── VALIDATION D'ENTRÉE ────────────────────────────────────────────────────────────────────────────────────────
def _exige_Z(Z) -> int:
    """Numéro atomique valide : un int (pas bool, pas float, pas str) entre 1 et 118 inclus."""
    if isinstance(Z, bool) or not isinstance(Z, int):
        raise ValueError("Z invalide : un entier Python (int) est requis (bool/float/str/None refusés)")
    if not (1 <= Z <= Z_MAX):
        raise ValueError(f"Z hors domaine : 1 <= Z <= {Z_MAX} (éléments reconnus) ; Z={Z} refusé")
    return Z


# ── MÉCANIQUE INTERNE ──────────────────────────────────────────────────────────────────────────────────────────
def _aufbau(Z: int):
    """Sous-couches (n, l, nb_electrons) par remplissage de Klechkowski pur, dans l'ordre de remplissage."""
    restant = Z
    parts = []
    for (n, l) in _ORDRE_KLECHKOWSKI:
        if restant == 0:
            break
        c = min(restant, _CAPACITE[l])
        parts.append((n, l, c))
        restant -= c
    return parts


def _gaz_rare_precedent(Z: int):
    """(Z_gaz, symbole) du plus grand gaz rare STRICTEMENT inférieur à Z, ou None (H, He)."""
    prec = None
    for (zg, sym) in _GAZ_RARES:
        if zg < Z:
            prec = (zg, sym)
    return prec


def _occupation(Z: int):
    """État fondamental réel : (n, l, nb) — exception mesurée si cataloguée, sinon Aufbau.

    Pour une exception : cœur du gaz rare précédent (ordre de remplissage) + queue mesurée (triée (n, l))."""
    if Z in _EXCEPTIONS:
        zg, _sym = _gaz_rare_precedent(Z)  # toute exception cataloguée a un gaz rare précédent
        return _aufbau(zg) + [tuple(t) for t in _EXCEPTIONS[Z]]
    return _aufbau(Z)


def _texte(parts) -> str:
    return " ".join(f"{n}{l}{c}" for (n, l, c) in parts)


# ── API PUBLIQUE ───────────────────────────────────────────────────────────────────────────────────────────────
def configuration(Z) -> str:
    """Configuration électronique complète de l'état fondamental, ex. '1s2 2s2 2p6 3s2 3p6 4s2 3d6' (Z=26).

    Régulier : ordre de remplissage (Klechkowski). Exception cataloguée : cœur développé + queue mesurée.
    Z hors [1, 118] ou non-int -> ValueError."""
    Z = _exige_Z(Z)
    return _texte(_occupation(Z))


def configuration_condensee(Z) -> str:
    """Notation gaz rare, ex. '[Ar] 3d6 4s2' (Z=26) ; queue triée par (n, l) croissant.

    H (Z=1) et He (Z=2) n'ont pas de gaz rare précédent : renvoie la configuration complète."""
    Z = _exige_Z(Z)
    prec = _gaz_rare_precedent(Z)
    if prec is None:
        return configuration(Z)
    zg, sym = prec
    if Z in _EXCEPTIONS:
        queue = list(_EXCEPTIONS[Z])
    else:
        # Les gaz rares tombent exactement sur des frontières de sous-couches de l'ordre de Klechkowski :
        # le cœur est un préfixe strict, la queue est le reste, ensuite triée par (n, l).
        queue = _aufbau(Z)[len(_aufbau(zg)):]
    queue = sorted(queue, key=lambda t: (t[0], _L_NUM[t[1]]))
    return f"[{sym}] " + _texte(queue)


def couche_valence(Z) -> int:
    """Numéro n de la couche EXTERNE (plus grand n occupé) de l'état fondamental réel."""
    Z = _exige_Z(Z)
    return max(n for (n, _l, _c) in _occupation(Z))


def electrons_valence(Z) -> int:
    """Nombre d'électrons de la couche EXTERNE (plus grand n occupé) — convention « couche externe ».

    Ex. Fe (Z=26) -> 2 (4s2) ; Pd (Z=46, [Kr]4d10) -> 18 (couche n=4 : 4s2 4p6 4d10, aucune couche 5)."""
    Z = _exige_Z(Z)
    occ = _occupation(Z)
    n_max = max(n for (n, _l, _c) in occ)
    return sum(c for (n, _l, c) in occ if n == n_max)


def bloc(Z) -> str:
    """Bloc du tableau périodique : 's' | 'p' | 'd' | 'f'.

    Convention : sous-couche recevant le Z-ième électron dans l'ordre de Klechkowski PUR (position dans le
    tableau, forme « Lu sous Y », IUPAC 2021 provisoire : La/Ac bloc f, Lu/Lr bloc d). Indépendant des
    exceptions mesurées (Cr, Cu, Pd... restent bloc d ; He reste bloc s)."""
    Z = _exige_Z(Z)
    cumul = 0
    for (n, l) in _ORDRE_KLECHKOWSKI:
        cumul += _CAPACITE[l]
        if cumul >= Z:
            return l
    raise ValueError("inatteignable : Z <= 118 est couvert par l'ordre de Klechkowski")  # garde-fou


def statut(Z) -> str:
    """Provenance de la configuration : 'exception mesurée' (catalogue spectroscopique) ou "règle d'Aufbau"."""
    Z = _exige_Z(Z)
    return "exception mesurée" if Z in _EXCEPTIONS else "règle d'Aufbau"
