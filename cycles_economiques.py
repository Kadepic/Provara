"""
cycles_economiques.py — CATALOGUE établi du cycle économique (cycle des affaires / business cycle).

Faits SOURCÉS / consensus (macroéconomie standard, NBER, Conference Board). AUCUNE valeur conjoncturelle,
estimation ou datation inventée : on restitue UNIQUEMENT la structure établie du cycle et des classifications
d'indicateurs faisant consensus. Toute entrée hors référentiel -> ValueError (abstention, jamais un faux).

1) PHASES DU CYCLE (modèle à 4 phases, consensus) — ordre canonique :
     1. expansion         : croissance du PIB, de l'emploi, de la production et de la consommation.
     2. sommet/pic        : point haut du cycle ; l'activité cesse de croître avant le retournement.
     3. recession         : contraction de l'activité, baisse du PIB, hausse du chômage.
     4. creux/depression  : point bas du cycle ; l'activité cesse de décroître avant la reprise.
   Le cycle BOUCLE : expansion -> sommet/pic -> recession -> creux/depression -> expansion -> ...
   (après le pic vient la récession ; après le creux, l'expansion).

2) DÉFINITION TECHNIQUE de la récession (règle pratique « rule of thumb ») :
     deux trimestres consécutifs de BAISSE du PIB réel.
   NB : c'est la règle TECHNIQUE, distincte de la datation officielle multicritère (NBER aux États-Unis),
   qui considère profondeur, diffusion et durée. On expose les deux faits honnêtement.

3) INDICATEURS conjoncturels — classification de référence (Conference Board : LEI / CEI / LAG) :
     • avancé (leading)    : se retourne AVANT l'économie ; anticipe les retournements
                             (permis de construire, cours des actions, courbe des taux, nouvelles commandes…).
     • coïncident          : évolue EN MÊME TEMPS que le cycle ; mesure l'état courant (PIB, production
                             industrielle, emploi salarié, revenu des ménages…).
     • retardé (lagging)   : se retourne APRÈS l'économie ; confirme une tendance engagée
                             (taux de chômage, inflation, taux préférentiel, coût unitaire du travail…).

GARANTIES (vérifiées en adverse par valide_cycles_economiques.py) :
  - phase / indicateur / type INCONNU -> ValueError (jamais une classification inventée) ;
  - entrée non-str, vide, ambiguë hors catalogue (ex. « taux d'intérêt » seul) -> ValueError ;
  - est_recession_technique : données vides / non numériques / non finies -> ValueError ;
  - fonctions pures, déterministes, stdlib uniquement.
"""

from __future__ import annotations

import math
import re
import unicodedata

__all__ = [
    "phases",
    "phase_cycle",
    "phase_suivante",
    "definition_recession",
    "est_recession_technique",
    "type_indicateur",
    "definition_indicateur",
    "indicateurs",
]

# ── PHASES (catalogue ordonné) ──────────────────────────────────────────────────────────────────────────────────
_PHASES = ("expansion", "sommet/pic", "recession", "creux/depression")

_ORDRE = {nom: i + 1 for i, nom in enumerate(_PHASES)}

_DESCRIPTION_PHASE = {
    "expansion": (
        "Expansion : phase de croissance — hausse du PIB, de l'emploi, de la production et de la "
        "consommation. La reprise (sortie de récession) en est la première partie."
    ),
    "sommet/pic": (
        "Sommet (pic) : point HAUT du cycle. L'activité cesse de croître ; sommet d'activité juste "
        "avant le retournement à la baisse."
    ),
    "recession": (
        "Récession : phase de CONTRACTION — baisse du PIB sur plusieurs trimestres, recul de la "
        "production et de l'emploi, hausse du chômage."
    ),
    "creux/depression": (
        "Creux (point bas, dépression) : point BAS du cycle. L'activité cesse de décroître ; creux "
        "d'activité juste avant la reprise."
    ),
}

# Cycle qui boucle : chaque phase -> suivante (creux -> expansion).
_SUIVANTE = {
    "expansion": "sommet/pic",
    "sommet/pic": "recession",
    "recession": "creux/depression",
    "creux/depression": "expansion",
}

# Synonymes (déjà NORMALISÉS : minuscules, sans accents) -> nom canonique de phase.
_SYN_PHASE = {
    "expansion": "expansion",
    "expansion economique": "expansion",
    "phase d'expansion": "expansion",
    "sommet/pic": "sommet/pic",
    "sommet": "sommet/pic",
    "pic": "sommet/pic",
    "pic conjoncturel": "sommet/pic",
    "peak": "sommet/pic",
    "recession": "recession",
    "contraction": "recession",
    "creux/depression": "creux/depression",
    "creux": "creux/depression",
    "depression": "creux/depression",
    "point bas": "creux/depression",
    "trough": "creux/depression",
}

# ── INDICATEURS (catalogue de classification consensuel — Conference Board) ──────────────────────────────────────
_IND = {
    "avance": [
        "cours des actions", "prix des actions", "indice boursier", "bourse",
        "permis de construire", "mises en chantier", "permis de batir",
        "nouvelles commandes", "carnet de commandes", "commandes a l'industrie",
        "masse monetaire", "masse monetaire m2", "m2",
        "courbe des taux", "ecart de taux", "spread de taux", "pente de la courbe des taux",
        "confiance des consommateurs", "anticipations des consommateurs",
        "climat de confiance des consommateurs",
        "inscriptions au chomage", "inscriptions hebdomadaires au chomage",
        "nouvelles demandes d'allocation chomage", "initial jobless claims",
        "duree hebdomadaire du travail", "heures hebdomadaires moyennes",
    ],
    "coincident": [
        "pib", "produit interieur brut",
        "production industrielle",
        "emploi salarie non agricole", "emplois non agricoles", "emploi salarie", "payrolls",
        "revenu des menages", "revenu personnel", "revenus personnels",
        "ventes manufacturieres et commerciales", "ventes du commerce et de l'industrie",
    ],
    "retarde": [
        "taux de chomage",
        "duree moyenne du chomage", "duree du chomage",
        "cout unitaire du travail", "cout du travail par unite produite",
        "encours de credit commercial et industriel", "credits commerciaux et industriels",
        "taux preferentiel", "prime rate", "taux de base bancaire",
        "inflation", "indice des prix a la consommation", "ipc",
        "ratio stocks/ventes", "ratio stocks sur ventes",
    ],
}

# Carte plate synonyme -> type. Sanité : aucun synonyme ne doit appartenir à deux types (sinon catalogue incohérent).
_SYN_IND: dict[str, str] = {}
for _t, _noms in _IND.items():
    for _n in _noms:
        if _n in _SYN_IND and _SYN_IND[_n] != _t:
            raise AssertionError(f"indicateur ambigu dans le catalogue : {_n!r}")
        _SYN_IND[_n] = _t

_DESCRIPTION_TYPE = {
    "avance": (
        "Indicateur avancé (leading) : se retourne AVANT l'économie ; anticipe les points de "
        "retournement du cycle (ex. permis de construire, cours des actions, courbe des taux)."
    ),
    "coincident": (
        "Indicateur coïncident : évolue EN MÊME TEMPS que le cycle ; mesure l'état courant de "
        "l'activité (ex. PIB, production industrielle, emploi salarié)."
    ),
    "retarde": (
        "Indicateur retardé (lagging) : se retourne APRÈS l'économie ; confirme une tendance déjà "
        "engagée (ex. taux de chômage, inflation, taux préférentiel)."
    ),
}


# ── NORMALISATION (stricte : lookup exact après normalisation, pas de fuzzy) ─────────────────────────────────────
def _norm(s) -> str:
    """Minuscule, sans accents, apostrophes droites, espaces compactés. Non-str / vide -> ValueError."""
    if not isinstance(s, str):
        raise ValueError(f"libellé non textuel : {s!r}")
    t = s.strip()
    if not t:
        raise ValueError("libellé vide")
    for apo in ("’", "‘", "ʼ", "´", "`"):
        t = t.replace(apo, "'")
    t = unicodedata.normalize("NFKD", t)
    t = "".join(c for c in t if not unicodedata.combining(c))
    t = re.sub(r"\s+", " ", t).lower()
    return t


# ── API ─────────────────────────────────────────────────────────────────────────────────────────────────────────
def phases() -> tuple:
    """Les 4 phases du cycle, dans l'ordre canonique (tuple immuable)."""
    return _PHASES


def phase_cycle(nom):
    """
    Catalogue d'une phase : dict {nom (canonique), ordre (1..4), description}.
    Phase inconnue / non-str / vide -> ValueError (abstention).
    """
    cle = _norm(nom)
    if cle not in _SYN_PHASE:
        raise ValueError(f"phase inconnue : {nom!r} (attendu : {', '.join(_PHASES)})")
    canon = _SYN_PHASE[cle]
    return {"nom": canon, "ordre": _ORDRE[canon], "description": _DESCRIPTION_PHASE[canon]}


def phase_suivante(phase):
    """
    Phase qui SUIT dans le cycle (nom canonique). Le cycle boucle :
    expansion -> sommet/pic -> recession -> creux/depression -> expansion.
    Phase inconnue -> ValueError.
    """
    cle = _norm(phase)
    if cle not in _SYN_PHASE:
        raise ValueError(f"phase inconnue : {phase!r}")
    return _SUIVANTE[_SYN_PHASE[cle]]


def definition_recession() -> dict:
    """
    Règle TECHNIQUE de la récession (consensus « rule of thumb ») :
    deux trimestres consécutifs de baisse du PIB réel.
    """
    return {
        "nombre_trimestres": 2,
        "critere": "baisse du PIB réel",
        "consecutifs": True,
        "regle": "Récession technique : deux trimestres consécutifs de baisse du PIB réel.",
        "source": "règle technique (rule of thumb), distincte de la datation officielle multicritère (NBER).",
    }


def est_recession_technique(variations_pib_trimestrielles) -> bool:
    """
    Applique la règle technique à une séquence de variations TRIMESTRIELLES du PIB réel
    (taux de croissance, en % ou en points — seul le SIGNE compte).
    Renvoie True s'il existe AU MOINS deux trimestres CONSÉCUTIFS de baisse (variations < 0).

    Données vides / chaîne / élément non numérique / booléen / non fini -> ValueError (abstention).
    """
    if isinstance(variations_pib_trimestrielles, (str, bytes)) or isinstance(
        variations_pib_trimestrielles, dict
    ):
        raise ValueError("séquence de variations attendue (liste/tuple de nombres)")
    try:
        seq = list(variations_pib_trimestrielles)
    except TypeError:
        raise ValueError("argument non itérable")
    if not seq:
        raise ValueError("séquence vide : pas de données trimestrielles")
    vals = []
    for x in seq:
        if isinstance(x, bool):
            raise ValueError(f"valeur booléenne refusée : {x!r}")
        if not isinstance(x, (int, float)):
            raise ValueError(f"variation non numérique : {x!r}")
        xf = float(x)
        if not math.isfinite(xf):
            raise ValueError(f"variation non finie : {x!r}")
        vals.append(xf)
    for i in range(len(vals) - 1):
        if vals[i] < 0 and vals[i + 1] < 0:
            return True
    return False


def type_indicateur(nom) -> str:
    """
    Type conjoncturel d'un indicateur : 'avance' | 'coincident' | 'retarde'.
    Indicateur hors catalogue / ambigu (ex. « taux d'intérêt » seul) / non-str -> ValueError (abstention).
    """
    cle = _norm(nom)
    if cle not in _SYN_IND:
        raise ValueError(f"indicateur hors catalogue : {nom!r}")
    return _SYN_IND[cle]


def definition_indicateur(type_) -> str:
    """Description du type d'indicateur ('avance' | 'coincident' | 'retarde'). Type inconnu -> ValueError."""
    cle = _norm(type_)
    if cle not in _DESCRIPTION_TYPE:
        raise ValueError(f"type d'indicateur inconnu : {type_!r} (attendu : avance, coincident, retarde)")
    return _DESCRIPTION_TYPE[cle]


def indicateurs(type_) -> tuple:
    """Libellés canoniques connus pour un type donné (tuple trié). Type inconnu -> ValueError."""
    cle = _norm(type_)
    if cle not in _IND:
        raise ValueError(f"type d'indicateur inconnu : {type_!r}")
    return tuple(sorted(_IND[cle]))
