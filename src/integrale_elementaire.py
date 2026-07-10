"""
INTÉGRALE SANS PRIMITIVE ÉLÉMENTAIRE — catalogue de FAITS DÉMONTRÉS (Liouville / Risch).

Même posture FAUX=0 que `decidabilite` / `classes_complexite` (le théorème juge, jamais un faux) :
  • Le MÉCANISME est un CATALOGUE CLOS de résultats DÉMONTRÉS, pas un algorithme de décision :
      – Théorème de LIOUVILLE (1833–1841) : si f a une primitive élémentaire, alors cette primitive
        s'écrit  F = v₀ + Σ cᵢ·ln(vᵢ)  où les vᵢ vivent dans le corps différentiel engendré par f.
        En particulier (cas f·e^g, f et g rationnelles) : ∫ f·e^g dx est élémentaire ssi il existe une
        fonction RATIONNELLE r telle que  f = r' + r·g'.  Pour exp(−x²) (f=1, g=−x²), l'équation
        1 = r' − 2x·r n'a AUCUNE solution rationnelle : erf n'est pas élémentaire (Liouville 1835).
      – L'algorithme de RISCH (1969) rend cette question DÉCIDABLE pour les fonctions élémentaires ;
        les entrées du catalogue sont les résultats classiques établis par cette théorie.
  • HONNÊTETÉ STRUCTURELLE : l'algorithme de Risch COMPLET n'est PAS implémenté ici. Ce module ne
    DÉCIDE rien par calcul : il RESTITUE des faits prouvés et sourcés, et S'ABSTIENT (ValueError)
    sur toute fonction HORS catalogue. C'est le cœur du FAUX=0 : jamais une réponse devinée.

GARANTIES (vérifiées en adverse par `valide_integrale_elementaire.py`) :
  - fonction HORS catalogue -> ValueError (abstention structurelle, jamais une devinette) ;
  - nom non-str (bool, int, float, None, liste) ou str vide -> ValueError ;
  - chaque entrée porte sa RÉFÉRENCE (théorème/source) ; les élémentaires portent leur primitive ;
  - discrimination FORTE : exp(−x²) NON élémentaire MAIS x·exp(−x²) ÉLÉMENTAIRE (primitive −½·e^(−x²)) —
    le catalogue distingue les deux, aucun « pattern matching » naïf sur le facteur exp(−x²) ;
  - ≥ 10 non-élémentaires prouvés + ≥ 9 élémentaires (contre-exemples indispensables) ;
  - déterministe ; conservateur (faux négatif/abstention toléré, faux POSITIF interdit).

Toutes les fonctions sont PURES et déterministes ; stdlib uniquement (aucun import externe).
"""
from __future__ import annotations

SOURCE = (
    "théorème de Liouville (J. Liouville, Mémoires 1833-1841, dont 1835 pour exp(-x^2)) + "
    "algorithme de Risch (R. Risch, Trans. AMS 139, 1969) ; exposés classiques : "
    "M. Rosenlicht, 'Integration in finite terms', Amer. Math. Monthly 79 (1972)"
)

# ── CATALOGUE CLOS ──────────────────────────────────────────────────────────────────────────────────────────────
# Chaque entrée est un FAIT DÉMONTRÉ de la théorie de Liouville/Risch.
#   'elementaire' : la fonction admet-elle une primitive élémentaire (True/False, PROUVÉ) ;
#   'primitive'   : la primitive si élémentaire (str), None sinon ;
#   'reference'   : le théorème / la source du fait.
_CATALOGUE: dict[str, dict] = {
    # ── NON ÉLÉMENTAIRES (primitive prouvée inexistante dans les fonctions élémentaires) ──
    "exp(-x^2)": {
        "elementaire": False, "primitive": None,
        "reference": "Liouville 1835 : 1 = r' - 2x·r sans solution rationnelle ; primitive = (√π/2)·erf(x), "
                     "erf n'est pas élémentaire",
    },
    "sin(x)/x": {
        "elementaire": False, "primitive": None,
        "reference": "théorie de Liouville : primitive = Si(x) (sinus intégral), non élémentaire",
    },
    "cos(x)/x": {
        "elementaire": False, "primitive": None,
        "reference": "théorie de Liouville : primitive = Ci(x) (cosinus intégral), non élémentaire",
    },
    "exp(x)/x": {
        "elementaire": False, "primitive": None,
        "reference": "Liouville : 1/x = r' + r sans solution rationnelle ; primitive = Ei(x) "
                     "(exponentielle intégrale), non élémentaire",
    },
    "1/ln(x)": {
        "elementaire": False, "primitive": None,
        "reference": "théorie de Liouville : primitive = li(x) (logarithme intégral), non élémentaire "
                     "(équivalent à Ei via x = e^t)",
    },
    "sqrt(1-k^2*sin^2(x))": {
        "elementaire": False, "primitive": None,
        "reference": "intégrale ELLIPTIQUE de 2e espèce E(x|k), 0<k<1 : non élémentaire "
                     "(Liouville 1834, intégrales elliptiques)",
    },
    "exp(x^2)": {
        "elementaire": False, "primitive": None,
        "reference": "Liouville : 1 = r' + 2x·r sans solution rationnelle ; primitive = (√π/2)·erfi(x), "
                     "non élémentaire",
    },
    "sin(x^2)": {
        "elementaire": False, "primitive": None,
        "reference": "primitive = intégrale de FRESNEL S(x), non élémentaire (théorie de Liouville)",
    },
    "cos(x^2)": {
        "elementaire": False, "primitive": None,
        "reference": "primitive = intégrale de FRESNEL C(x), non élémentaire (théorie de Liouville)",
    },
    "x^x": {
        "elementaire": False, "primitive": None,
        "reference": "x^x = e^(x·ln x) : pas de primitive élémentaire (théorie de Liouville/Risch)",
    },
    "ln(ln(x))": {
        "elementaire": False, "primitive": None,
        "reference": "pas de primitive élémentaire (théorie de Liouville ; liée à li(ln x))",
    },
    # ── ÉLÉMENTAIRES (contre-exemples : le catalogue DISCRIMINE, il ne bannit pas un motif) ──
    "x^n": {
        "elementaire": True, "primitive": "x^(n+1)/(n+1)  (pour n ≠ -1)",
        "reference": "primitive polynomiale classique (règle de puissance), n ≠ -1",
    },
    "1/x": {
        "elementaire": True, "primitive": "ln|x|",
        "reference": "primitive classique : d/dx ln|x| = 1/x",
    },
    "exp(x)": {
        "elementaire": True, "primitive": "exp(x)",
        "reference": "primitive classique : d/dx e^x = e^x",
    },
    "sin(x)": {
        "elementaire": True, "primitive": "-cos(x)",
        "reference": "primitive classique : d/dx (-cos x) = sin x",
    },
    "cos(x)": {
        "elementaire": True, "primitive": "sin(x)",
        "reference": "primitive classique : d/dx sin x = cos x",
    },
    "x*exp(-x^2)": {
        "elementaire": True, "primitive": "-exp(-x^2)/2",
        "reference": "substitution u = -x² : d/dx (-e^(-x²)/2) = x·e^(-x²) — ÉLÉMENTAIRE malgré le "
                     "facteur exp(-x²) (discrimination forte vs ∫exp(-x²))",
    },
    "1/(1+x^2)": {
        "elementaire": True, "primitive": "arctan(x)",
        "reference": "primitive classique : d/dx arctan x = 1/(1+x²)",
    },
    "tan(x)": {
        "elementaire": True, "primitive": "-ln|cos(x)|",
        "reference": "primitive classique : d/dx (-ln|cos x|) = sin x / cos x = tan x",
    },
    "ln(x)": {
        "elementaire": True, "primitive": "x*ln(x) - x",
        "reference": "intégration par parties : d/dx (x·ln x - x) = ln x",
    },
}

# Alias d'écriture (normalisés) -> nom canonique. AUCUNE heuristique au-delà : hors liste -> ValueError.
_ALIAS: dict[str, str] = {
    "e^(-x^2)": "exp(-x^2)",
    "e^(x^2)": "exp(x^2)",
    "e^x": "exp(x)",
    "e^x/x": "exp(x)/x",
    "x*e^(-x^2)": "x*exp(-x^2)",
    "1/log(x)": "1/ln(x)",
    "log(x)": "ln(x)",
    "log(log(x))": "ln(ln(x))",
    "sqrt(1-k^2*sin(x)^2)": "sqrt(1-k^2*sin^2(x))",
    "sqrt(1-k^2*sin^2x)": "sqrt(1-k^2*sin^2(x))",
    "sinc(x)": "sin(x)/x",
}


def _normalise(nom) -> str:
    """Nom canonique du catalogue, ou ValueError (abstention) si inconnu.

    Normalisation PUREMENT typographique (espaces, casse, ², **, ·) — jamais sémantique."""
    if not isinstance(nom, str):
        raise ValueError("nom invalide : une chaîne (str) est requise")
    s = nom.strip().lower()
    if not s:
        raise ValueError("nom invalide : chaîne vide")
    s = s.replace(" ", "").replace("²", "^2").replace("**", "^").replace("·", "*").replace("×", "*")
    s = _ALIAS.get(s, s)
    if s not in _CATALOGUE:
        raise ValueError(
            f"fonction hors catalogue : {nom!r} — l'algorithme de Risch complet n'est pas implémenté, "
            "ce module ne restitue que des faits démontrés (abstention plutôt qu'une devinette)"
        )
    return s


# ── API ─────────────────────────────────────────────────────────────────────────────────────────────────────────
def primitive_elementaire(nom: str) -> bool:
    """True ssi la fonction (du catalogue) admet une primitive élémentaire — fait DÉMONTRÉ.

    Fonction hors catalogue -> ValueError (abstention structurelle)."""
    return _CATALOGUE[_normalise(nom)]["elementaire"]


def statut(nom: str) -> dict:
    """Statut complet : {'elementaire': bool, 'reference': str, 'primitive': str|None}.

    Fonction hors catalogue -> ValueError. Le dict rendu est une COPIE (pas d'état mutable partagé)."""
    e = _CATALOGUE[_normalise(nom)]
    return {"elementaire": e["elementaire"], "reference": e["reference"], "primitive": e["primitive"]}


def catalogue() -> dict:
    """Copie du catalogue complet : {nom_canonique: {'elementaire', 'reference', 'primitive'}}."""
    return {nom: dict(e) for nom, e in _CATALOGUE.items()}


def critere_liouville() -> str:
    """Énoncé du critère de Liouville (cas ∫ f·e^g, f et g rationnelles) — le théorème qui fonde le catalogue."""
    return (
        "Critère de Liouville (1833-1841) : si f possède une primitive élémentaire, elle s'écrit "
        "F = v0 + Σ ci·ln(vi) avec les vi dans le corps différentiel engendré par f. "
        "Cas ∫ f·e^g dx (f, g rationnelles, g non constante) : la primitive est élémentaire SI ET SEULEMENT SI "
        "il existe une fonction RATIONNELLE r telle que f = r' + r·g'. "
        "Exemple : pour exp(-x^2) (f=1, g=-x^2), l'équation 1 = r' - 2x·r n'a aucune solution rationnelle "
        "(comparaison des degrés aux pôles), donc erf n'est pas élémentaire (Liouville 1835). "
        "L'algorithme de Risch (1969) rend cette question décidable ; il n'est PAS implémenté ici : "
        "le module restitue des faits démontrés et s'abstient hors catalogue."
    )
