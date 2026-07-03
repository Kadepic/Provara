"""posologie.py — Calculs de POSOLOGIE / DOSAGE (exacts, déterministes). FAUX=0.

Mécanismes établis de pharmacologie clinique. Chaque fonction est une formule
EXACTE, sans valeur inventée ; sortie arrondie ; abstention (ValueError) sur
toute entrée invalide plutôt qu'un résultat faux.

  dose_totale(dose_par_kg, masse_kg)
      = dose_par_kg · masse_kg                         [mg]
      Dose totale d'un médicament prescrit par kg de masse corporelle.
      Ex. 10 mg/kg · 70 kg = 700 mg.

  debit_perfusion(volume_ml, duree_h)
      = volume_ml / duree_h                            [ml/h]
      Débit d'une perfusion continue.
      Ex. 1000 ml en 8 h = 125 ml/h.

  debit_gouttes(volume_ml, duree_min, facteur=20)
      = volume_ml · facteur / duree_min                [gouttes/min]
      Débit en gouttes/min ; `facteur` = facteur de calibration du
      perfuseur (gouttes/ml) : 20 (macrogouttes) ou 60 (microgouttes).

  surface_corporelle_mosteller(taille_cm, masse_kg)
      = sqrt(taille_cm · masse_kg / 3600)              [m²]
      Surface corporelle (BSA), formule de Mosteller (NEJM 1987).
      Ex. Mosteller(170, 70) = sqrt(170·70/3600) ≈ 1.8181 m².

  dose_pediatrique(dose_adulte, masse_enfant_kg, masse_adulte_kg=70.0)
      = dose_adulte · masse_enfant_kg / masse_adulte_kg
      Règle de Clark (proportion à la masse corporelle).
      Ex. 500 mg · 35/70 = 250 mg.

  dose_pediatrique_bsa(dose_adulte, bsa_enfant, bsa_adulte=1.73)
      = dose_adulte · bsa_enfant / bsa_adulte
      Ajustement pédiatrique par surface corporelle (BSA adulte de
      référence = 1.73 m²).
      Ex. 500 mg · 0.865/1.73 = 250 mg.

SOUNDNESS : entrées non numériques / non finies (bool, str, NaN, inf) -> ValueError ;
masse ≤ 0, durée ≤ 0, taille ≤ 0, facteur ≤ 0, masse/bsa de référence ≤ 0 -> ValueError ;
dose / volume négatif -> ValueError.
"""
import math

# Précision de sortie (décimales). Déterministe.
_DEC = 4


def _nombre_fini(x, nom):
    """Nombre réel fini (rejette bool, str, NaN, inf) ou ValueError."""
    if isinstance(x, bool) or not isinstance(x, (int, float)):
        raise ValueError(f"{nom} doit être un nombre, reçu {type(x).__name__}")
    if not math.isfinite(x):
        raise ValueError(f"{nom} doit être fini, reçu {x}")
    return float(x)


def _positif(x, nom):
    """Nombre fini strictement positif (diviseur / grandeur physique) ou ValueError."""
    v = _nombre_fini(x, nom)
    if v <= 0.0:
        raise ValueError(f"{nom} doit être strictement positif, reçu {v}")
    return v


def _non_negatif(x, nom):
    """Nombre fini ≥ 0 (dose, volume) ou ValueError."""
    v = _nombre_fini(x, nom)
    if v < 0.0:
        raise ValueError(f"{nom} doit être ≥ 0, reçu {v}")
    return v


def dose_totale(dose_par_kg, masse_kg):
    """Dose totale [mg] = dose_par_kg [mg/kg] · masse_kg [kg]."""
    d = _non_negatif(dose_par_kg, "dose_par_kg")
    m = _positif(masse_kg, "masse_kg")
    return round(d * m, _DEC)


def debit_perfusion(volume_ml, duree_h):
    """Débit de perfusion [ml/h] = volume_ml / duree_h."""
    v = _non_negatif(volume_ml, "volume_ml")
    t = _positif(duree_h, "duree_h")
    return round(v / t, _DEC)


def debit_gouttes(volume_ml, duree_min, facteur=20):
    """Débit [gouttes/min] = volume_ml · facteur / duree_min."""
    v = _non_negatif(volume_ml, "volume_ml")
    t = _positif(duree_min, "duree_min")
    f = _positif(facteur, "facteur")
    return round(v * f / t, _DEC)


def surface_corporelle_mosteller(taille_cm, masse_kg):
    """Surface corporelle [m²] = sqrt(taille_cm · masse_kg / 3600) (Mosteller)."""
    h = _positif(taille_cm, "taille_cm")
    m = _positif(masse_kg, "masse_kg")
    return round(math.sqrt(h * m / 3600.0), _DEC)


def dose_pediatrique(dose_adulte, masse_enfant_kg, masse_adulte_kg=70.0):
    """Dose pédiatrique (règle de Clark) = dose_adulte · masse_enfant / masse_adulte."""
    d = _non_negatif(dose_adulte, "dose_adulte")
    me = _positif(masse_enfant_kg, "masse_enfant_kg")
    ma = _positif(masse_adulte_kg, "masse_adulte_kg")
    return round(d * me / ma, _DEC)


def dose_pediatrique_bsa(dose_adulte, bsa_enfant, bsa_adulte=1.73):
    """Dose pédiatrique par surface corporelle = dose_adulte · bsa_enfant / bsa_adulte."""
    d = _non_negatif(dose_adulte, "dose_adulte")
    be = _positif(bsa_enfant, "bsa_enfant")
    ba = _positif(bsa_adulte, "bsa_adulte")
    return round(d * be / ba, _DEC)
