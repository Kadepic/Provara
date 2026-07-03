"""urgence_medicale.py — Scores d'urgence cliniques établis. FAUX=0.

Échelles de gravité CONSENSUS, mécanisme EXACT et déterministe (catalogue sourcé) :

1) ÉCHELLE DE GLASGOW (Glasgow Coma Scale, Teasdale & Jennett, Lancet 1974) — état de
   conscience. Somme de trois sous-scores, chacun dans une plage FIXE :
     - ouverture des yeux  (ouverture_yeux)  : 1..4
     - réponse verbale     (reponse_verbale) : 1..5
     - réponse motrice     (reponse_motrice) : 1..6
   Total = 3..15. Classification établie :
     - 13..15 = atteinte légère
     -  9..12 = atteinte modérée
     -  3..8  = atteinte grave (coma) ; seuil ≤ 8 = coma grave (indication d'intubation).

2) SCORE D'APGAR (Virginia Apgar, 1952) — vitalité du NOUVEAU-NÉ (1 et 5 min de vie).
   Cinq critères, CHACUN coté 0..2, somme = 0..10 :
     - coloration (apparence cutanée)
     - fréquence cardiaque (pouls)
     - réflexes (réactivité / grimace)
     - tonus (tonus musculaire / activité)
     - respiration (effort respiratoire)
   Classification établie : 7..10 = normal (rassurant) ; 4..6 = modérément anormal ;
   0..3 = critique (bas).

3) INDICE DE CHOC (shock index, Allgöwer & Burri, 1967) = fréquence cardiaque / pression
   artérielle systolique (FC / PAS). Valeur normale ≈ 0,5..0,7 ; > 0,9 = choc
   (instabilité hémodynamique).

SOUNDNESS : un sous-score hors de SA plage -> ValueError ; entrée non entière pour un
sous-score -> ValueError ; PAS ≤ 0 ou FC ≤ 0 (impossible physiologiquement) -> ValueError ;
valeur non numérique / non finie -> ValueError. Aucune valeur n'est inventée : hors
référentiel -> abstention (ValueError).
"""
import math

# Plages canoniques des sous-scores (valeurs établies, non modifiables).
GLASGOW_YEUX = (1, 4)
GLASGOW_VERBAL = (1, 5)
GLASGOW_MOTEUR = (1, 6)
GLASGOW_TOTAL = (3, 15)
GLASGOW_SEUIL_COMA = 8          # total ≤ 8 = coma grave

APGAR_CRITERE = (0, 2)          # chaque critère
APGAR_TOTAL = (0, 10)

INDICE_CHOC_SEUIL = 0.9         # indice > 0,9 = choc


def _entier_dans(x, lo, hi, nom):
    """Valide que x est un entier (pas un bool) dans [lo, hi] inclus, sinon ValueError."""
    if isinstance(x, bool) or not isinstance(x, int):
        raise ValueError(f"{nom} doit être un entier, reçu {type(x).__name__}")
    if x < lo or x > hi:
        raise ValueError(f"{nom} hors plage : {x} attendu dans [{lo}, {hi}]")
    return x


def _nombre_fini(x, nom):
    """Valide que x est un nombre réel fini (rejette bool, str, NaN, inf), sinon ValueError."""
    if isinstance(x, bool) or not isinstance(x, (int, float)):
        raise ValueError(f"{nom} doit être un nombre, reçu {type(x).__name__}")
    if not math.isfinite(x):
        raise ValueError(f"{nom} doit être fini, reçu {x}")
    return float(x)


# ============================ ÉCHELLE DE GLASGOW ============================

def score_glasgow(ouverture_yeux, reponse_verbale, reponse_motrice):
    """Score de Glasgow total = somme des trois sous-scores (entier 3..15).

    ouverture_yeux 1..4, reponse_verbale 1..5, reponse_motrice 1..6.
    Sous-score hors plage / non entier -> ValueError."""
    y = _entier_dans(ouverture_yeux, *GLASGOW_YEUX, "ouverture_yeux")
    v = _entier_dans(reponse_verbale, *GLASGOW_VERBAL, "reponse_verbale")
    m = _entier_dans(reponse_motrice, *GLASGOW_MOTEUR, "reponse_motrice")
    return y + v + m


def est_coma_grave(ouverture_yeux, reponse_verbale, reponse_motrice):
    """True ssi score de Glasgow ≤ 8 (coma grave). Mêmes validations que score_glasgow."""
    return score_glasgow(ouverture_yeux, reponse_verbale, reponse_motrice) <= GLASGOW_SEUIL_COMA


def gravite_glasgow(ouverture_yeux, reponse_verbale, reponse_motrice):
    """Classe la gravité d'après le total de Glasgow (catalogue exact) :
    'grave' (3..8), 'modere' (9..12), 'leger' (13..15)."""
    t = score_glasgow(ouverture_yeux, reponse_verbale, reponse_motrice)
    if t <= 8:
        return "grave"
    if t <= 12:
        return "modere"
    return "leger"


# ============================== SCORE D'APGAR ==============================

def score_apgar(coloration, frequence_cardiaque, reflexes, tonus, respiration):
    """Score d'Apgar total = somme des cinq critères (entier 0..10).

    Chaque critère est coté 0, 1 ou 2. Critère hors plage / non entier -> ValueError."""
    c = _entier_dans(coloration, *APGAR_CRITERE, "coloration")
    f = _entier_dans(frequence_cardiaque, *APGAR_CRITERE, "frequence_cardiaque")
    r = _entier_dans(reflexes, *APGAR_CRITERE, "reflexes")
    to = _entier_dans(tonus, *APGAR_CRITERE, "tonus")
    re = _entier_dans(respiration, *APGAR_CRITERE, "respiration")
    return c + f + r + to + re


def interpretation_apgar(coloration, frequence_cardiaque, reflexes, tonus, respiration):
    """Classe la vitalité d'après le total d'Apgar (catalogue exact) :
    'normal' (7..10), 'modere' (4..6), 'critique' (0..3)."""
    t = score_apgar(coloration, frequence_cardiaque, reflexes, tonus, respiration)
    if t >= 7:
        return "normal"
    if t >= 4:
        return "modere"
    return "critique"


# ============================== INDICE DE CHOC ==============================

def indice_choc(fc, pression_systolique):
    """Indice de choc = FC / PAS (float). Valeur normale ≈ 0,5..0,7 ; > 0,9 = choc.

    FC ≤ 0 ou PAS ≤ 0 (impossible physiologiquement) -> ValueError ;
    valeur non numérique / non finie -> ValueError."""
    f = _nombre_fini(fc, "fc")
    p = _nombre_fini(pression_systolique, "pression_systolique")
    if f <= 0:
        raise ValueError("fc doit être > 0")
    if p <= 0:
        raise ValueError("pression_systolique doit être > 0")
    return f / p


def est_choc(fc, pression_systolique):
    """True ssi l'indice de choc est STRICTEMENT > 0,9 (instabilité hémodynamique)."""
    return indice_choc(fc, pression_systolique) > INDICE_CHOC_SEUIL
