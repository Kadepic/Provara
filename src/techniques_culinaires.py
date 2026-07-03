"""
TECHNIQUES CULINAIRES — classification BORNÉE par mode de transfert thermique + températures de référence.

Domaine BORNÉ (cat CONVENTION / CLASSIFICATION par critères établis) :
  • La cuisine classique classe les cuissons selon le MODE de transfert thermique et le MILIEU :
      - chaleur HUMIDE  (milieu eau / vapeur)        : bouillir, pocher, cuire à la vapeur, mijoter, blanchir…
      - chaleur SÈCHE   (milieu air, rayonnement)     : rôtir, griller, cuire au four, gratiner…
      - matière GRASSE  (milieu corps gras)           : frire, sauter, rissoler…
      - cuisson MIXTE   (saisie sèche + mouillement)  : braiser, ragoût (méthode « combination »).
    Cette taxonomie (chaleur humide / sèche / mixte) est une CONVENTION établie de la science culinaire.
  • Les TEMPÉRATURES de référence sont des FAITS physico-chimiques sourcés :
      - eau bout à 100 °C (à 1 atm) / gèle à 0 °C ;
      - réaction de Maillard : amorce vers ~140 °C (active ~140-165 °C) ;
      - caramélisation du saccharose : amorce vers ~160 °C ;
      - point de fumée des corps gras : valeur de référence par huile (donnée sourcée, variable selon raffinage).

GARANTIES (vérifiées en adverse par valide_techniques_culinaires.py) :
  - technique / phénomène / huile INCONNU du référentiel  -> ValueError (JAMAIS une réponse inventée) ;
  - entrée non-str ou vide                                 -> ValueError ;
  - déterministe ; le MÉCANISME (normalisation + table) est exact, le CONTENU est une donnée sourcée.

Le point de fumée est une donnée NOTOIREMENT variable (raffinage, source) : on rend une valeur de
référence typique (huile raffinée sauf mention) — précision honnête, jamais un faux exact.
"""
from __future__ import annotations

import unicodedata

# Modes de transfert thermique (taxonomie culinaire établie).
HUMIDE = "humide"
SEC = "sec"
MATIERE_GRASSE = "matiere_grasse"
MIXTE = "mixte"
MODES = frozenset({HUMIDE, SEC, MATIERE_GRASSE, MIXTE})

# Milieux physiques associés.
EAU = "eau"
AIR = "air"
MILIEUX = frozenset({EAU, AIR, MATIERE_GRASSE, MIXTE})

SOURCE = "classification cuisson par transfert thermique (cuisine classique) + constantes physico-chimiques"

# technique canonique -> (mode de cuisson, milieu de transfert)
CANON: dict[str, tuple[str, str]] = {
    # chaleur humide (milieu eau / vapeur d'eau)
    "bouillir":  (HUMIDE, EAU),
    "pocher":    (HUMIDE, EAU),
    "vapeur":    (HUMIDE, EAU),
    "mijoter":   (HUMIDE, EAU),
    "blanchir":  (HUMIDE, EAU),
    "ebouillanter": (HUMIDE, EAU),
    # chaleur sèche (milieu air / rayonnement)
    "rotir":     (SEC, AIR),
    "griller":   (SEC, AIR),
    "four":      (SEC, AIR),
    "gratiner":  (SEC, AIR),
    # matière grasse (milieu corps gras)
    "frire":     (MATIERE_GRASSE, MATIERE_GRASSE),
    "sauter":    (MATIERE_GRASSE, MATIERE_GRASSE),
    "rissoler":  (MATIERE_GRASSE, MATIERE_GRASSE),
    # cuisson mixte (concentration sèche + expansion humide)
    "braiser":   (MIXTE, MIXTE),
    "ragout":    (MIXTE, MIXTE),
}

# synonymes / variantes normalisés -> clé canonique
SYN: dict[str, str] = {
    "faire_bouillir": "bouillir", "ebullition": "bouillir", "bouilli": "bouillir",
    "pochage": "pocher", "poche": "pocher",
    "cuisson_vapeur": "vapeur", "cuire_vapeur": "vapeur", "a_la_vapeur": "vapeur",
    "cuisson_a_la_vapeur": "vapeur", "cuire_a_la_vapeur": "vapeur", "cuiseur_vapeur": "vapeur",
    "mitonner": "mijoter", "fremir": "mijoter", "fremissement": "mijoter",
    "blanchiment": "blanchir",
    "roti": "rotir", "rotissage": "rotir", "rotie": "rotir",
    "grillade": "griller", "grille": "griller", "grilling": "griller", "barbecue": "griller",
    "cuire_au_four": "four", "cuisson_au_four": "four", "au_four": "four",
    "cuisson_four": "four", "enfourner": "four", "cuire_four": "four",
    "gratin": "gratiner",
    "friture": "frire", "faire_frire": "frire", "frit": "frire",
    "saute": "sauter", "faire_sauter": "sauter", "sautee": "sauter",
    "braisage": "braiser", "braise": "braiser", "braisee": "braiser",
    "ragouter": "ragout", "en_ragout": "ragout", "ragout_de": "ragout",
}

# Phénomènes thermiques de référence -> température d'amorce / point fixe (°C, à 1 atm).
PHENOMENES: dict[str, float] = {
    "ebullition_eau":   100.0,   # eau bout à 100 °C (1 atm)
    "congelation_eau":    0.0,   # eau gèle à 0 °C
    "maillard":         140.0,   # amorce de la réaction de Maillard (~140 °C ; active 140-165)
    "caramelisation":   160.0,   # amorce caramélisation du saccharose (~160 °C)
}
PHENOM_SYN: dict[str, str] = {
    "ebullition": "ebullition_eau", "point_ebullition_eau": "ebullition_eau",
    "eau_bout": "ebullition_eau", "point_d_ebullition_de_l_eau": "ebullition_eau",
    "congelation": "congelation_eau", "gel_eau": "congelation_eau", "point_congelation_eau": "congelation_eau",
    "reaction_de_maillard": "maillard", "reaction_maillard": "maillard", "brunissement": "maillard",
    "caramel": "caramelisation", "caramelisation_sucre": "caramelisation",
    "caramelisation_du_sucre": "caramelisation", "caramelisation_saccharose": "caramelisation",
}

# Plage couramment citée de la réaction de Maillard (active).
_PLAGE_MAILLARD = (140.0, 165.0)

# Points de fumée de référence (°C) — valeurs typiques, huile RAFFINÉE sauf mention.
# Donnée sourcée et VARIABLE (raffinage/source) : on rend une valeur de référence, pas un exact universel.
POINTS_FUMEE: dict[str, float] = {
    "beurre":                   150.0,   # beurre non clarifié (bas, brûle vite)
    "beurre_clarifie":          250.0,   # ghee / beurre clarifié (élevé)
    "huile_olive_vierge_extra": 191.0,   # ~190 °C
    "huile_olive":              210.0,   # huile d'olive raffinée
    "huile_tournesol":          225.0,   # tournesol raffiné
    "huile_arachide":           230.0,   # arachide raffinée
    "huile_colza":              205.0,   # colza/canola raffiné
    "huile_pepins_raisin":      216.0,   # pépins de raisin
}
FUMEE_SYN: dict[str, str] = {
    "ghee": "beurre_clarifie",
    "huile_d_olive_vierge_extra": "huile_olive_vierge_extra",
    "olive_vierge_extra": "huile_olive_vierge_extra",
    "huile_d_olive": "huile_olive", "olive": "huile_olive",
    "tournesol": "huile_tournesol", "huile_de_tournesol": "huile_tournesol",
    "arachide": "huile_arachide", "huile_d_arachide": "huile_arachide", "cacahuete": "huile_arachide",
    "colza": "huile_colza", "huile_de_colza": "huile_colza", "canola": "huile_colza",
    "pepins_de_raisin": "huile_pepins_raisin", "huile_de_pepins_de_raisin": "huile_pepins_raisin",
}


def _norm(s: str) -> str:
    """Minuscule, sans accents, séparateurs -> '_'. Lève ValueError si non-str ou vide."""
    if not isinstance(s, str):
        raise ValueError("entrée non textuelle")
    t = s.strip().lower()
    if not t:
        raise ValueError("entrée vide")
    # supprime les diacritiques
    t = "".join(c for c in unicodedata.normalize("NFD", t)
                if unicodedata.category(c) != "Mn")
    # tout caractère non [a-z0-9] -> '_'
    out = []
    for c in t:
        out.append(c if (c.isalnum() and c.isascii()) else "_")
    t = "".join(out)
    # compacte les '_'
    while "__" in t:
        t = t.replace("__", "_")
    t = t.strip("_")
    if not t:
        raise ValueError("entrée vide après normalisation")
    return t


def _resoudre(valeur: str, canon: dict, syn: dict, quoi: str) -> str:
    """Retourne la clé canonique pour `valeur` (canon directe ou via synonymes) ; ValueError sinon."""
    n = _norm(valeur)
    if n in canon:
        return n
    if n in syn:
        return syn[n]
    raise ValueError(f"{quoi} inconnu(e) du référentiel : {valeur!r}")


def mode_cuisson(technique: str) -> str:
    """Mode de transfert thermique d'une technique : 'humide' | 'sec' | 'matiere_grasse' | 'mixte'.

    Ex. : bouillir/pocher/vapeur -> 'humide' ; rôtir/griller/four -> 'sec' ;
          frire/sauter -> 'matiere_grasse' ; braiser -> 'mixte'.
    Technique inconnue -> ValueError (jamais de réponse inventée)."""
    return CANON[_resoudre(technique, CANON, SYN, "technique")][0]


def milieu_cuisson(technique: str) -> str:
    """Milieu physique de transfert : 'eau' | 'air' | 'matiere_grasse' | 'mixte'.
    Technique inconnue -> ValueError."""
    return CANON[_resoudre(technique, CANON, SYN, "technique")][1]


def decrit(technique: str) -> dict:
    """Fiche {technique_canonique, mode, milieu}. Technique inconnue -> ValueError."""
    cle = _resoudre(technique, CANON, SYN, "technique")
    mode, milieu = CANON[cle]
    return {"technique": cle, "mode": mode, "milieu": milieu}


def techniques_du_mode(mode: str) -> tuple[str, ...]:
    """Liste triée des techniques canoniques d'un mode donné. Mode inconnu -> ValueError."""
    if mode not in MODES:
        raise ValueError(f"mode inconnu : {mode!r}")
    return tuple(sorted(t for t, (m, _) in CANON.items() if m == mode))


def temperature_reference(phenomene: str) -> float:
    """Température de référence (°C, 1 atm) d'un phénomène thermique culinaire.

    Ex. : 'ebullition_eau' -> 100.0 ; 'maillard' -> 140.0 (amorce) ; 'caramelisation' -> 160.0.
    Phénomène inconnu -> ValueError."""
    return PHENOMENES[_resoudre(phenomene, PHENOMENES, PHENOM_SYN, "phenomene")]


def plage_maillard() -> tuple[float, float]:
    """Plage (°C) couramment citée de la réaction de Maillard active : (140.0, 165.0)."""
    return _PLAGE_MAILLARD


def point_de_fumee(huile: str) -> float:
    """Point de fumée de référence (°C) d'un corps gras (valeur typique, huile raffinée sauf mention).
    Donnée sourcée variable. Corps gras inconnu -> ValueError."""
    return POINTS_FUMEE[_resoudre(huile, POINTS_FUMEE, FUMEE_SYN, "corps gras")]


def convient_friture(huile: str, temperature: float = 180.0) -> bool:
    """True si le point de fumée du corps gras est >= température de friture visée (défaut 180 °C).
    Corps gras inconnu -> ValueError ; température non-numérique/négative -> ValueError."""
    if isinstance(temperature, bool) or not isinstance(temperature, (int, float)):
        raise ValueError("température non numérique")
    if temperature <= 0:
        raise ValueError("température invalide")
    return point_de_fumee(huile) >= float(temperature)
