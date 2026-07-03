"""
energies_comparees.py — Comparaison énergétique fossiles vs renouvelables.

Mécanismes EXACTS / établis (définitions d'ingénierie énergétique conventionnelles) :

  • facteur_charge(E, P, heures=8760) = E / (P · heures)
      Facteur de charge (capacity factor) : énergie réellement produite rapportée à
      l'énergie que la puissance nominale aurait fournie en fonctionnant en continu sur
      la période. Grandeur SANS dimension dans [0, 1] (E et P·heures en unités cohérentes,
      ex. MWh et MW·h). heures=8760 = nombre d'heures d'une année non bissextile (365·24).
      Ordres de grandeur (IRENA/EIA) : solaire PV ≈ 0.15, éolien terrestre ≈ 0.25–0.35,
      nucléaire ≈ 0.9.

  • contenu_energetique(masse_kg, pci_MJ_kg) = masse · PCI
      Énergie chimique libérable par combustion = masse (kg) × pouvoir calorifique
      inférieur PCI (MJ/kg). Renvoie des mégajoules (MJ). Définition exacte (produit).

  • retour_energetique(E_produite, E_investie) = E_produite / E_investie   [alias eroi]
      Taux de retour énergétique EROI/EROEI : énergie produite sur le cycle de vie
      divisée par l'énergie investie pour la produire. Sans dimension. > 1 = source
      énergétiquement viable (rend plus qu'elle ne coûte).

  • emissions_co2(energie_kWh, facteur_g_kWh) = energie · facteur
      Émissions de CO2 = énergie (kWh) × facteur d'émission (gCO2eq/kWh). Renvoie des
      grammes de CO2 équivalent. Définition exacte (produit).

  • facteur_co2_reference(source) : facteur d'émission médian cycle de vie (gCO2eq/kWh)
      pour une source nommée, d'après le GIEC AR5, WG III, Annexe III (2014, Table A.III.2,
      valeurs médianes). Source inconnue -> ValueError (abstention).

CONSTANTES SOURCÉES (GIEC AR5 2014, médianes cycle de vie, gCO2eq/kWh) :
  charbon 820 · gaz 490 · solaire_pv 48 · biomasse 230 · geothermie 38 · hydraulique 24 ·
  nucleaire 12 · eolien 11.

ABSTENTION STRUCTURELLE (faux positif INTERDIT — ValueError) :
  • puissance nominale <= 0, heures <= 0, énergie produite < 0 -> ValueError.
  • facteur de charge calculé > 1 (physiquement impossible) -> ValueError.
  • PCI <= 0, masse < 0 -> ValueError.
  • énergie investie <= 0, énergie produite < 0 -> ValueError.
  • énergie < 0, facteur d'émission < 0 -> ValueError.
  • toute valeur non finie, source inconnue -> ValueError.

Fonctions pures déterministes, sorties arrondies à 6 décimales. stdlib uniquement.
"""

import math

__all__ = [
    "facteur_charge",
    "contenu_energetique",
    "retour_energetique",
    "eroi",
    "emissions_co2",
    "facteur_co2_reference",
    "FACTEUR_CO2_REF",
]

# Facteurs d'émission médians cycle de vie — GIEC AR5, WG III (2014), Annexe III,
# Table A.III.2 (gCO2eq/kWh). Valeurs médianes de la littérature.
FACTEUR_CO2_REF = {
    "charbon": 820.0,
    "gaz": 490.0,
    "biomasse": 230.0,
    "solaire_pv": 48.0,
    "geothermie": 38.0,
    "hydraulique": 24.0,
    "nucleaire": 12.0,
    "eolien": 11.0,
}

_NDEC = 6


def _reel_fini(x, nom):
    """Convertit en float fini, sinon ValueError."""
    try:
        v = float(x)
    except (TypeError, ValueError):
        raise ValueError(f"{nom} non numérique : {x!r}")
    if not math.isfinite(v):
        raise ValueError(f"{nom} non fini : {x!r}")
    return v


def _arr(x):
    """Arrondi déterministe à 6 décimales."""
    return round(x, _NDEC)


def facteur_charge(energie_produite_reelle, puissance_nominale, heures=8760):
    """
    Facteur de charge = énergie_produite / (puissance_nominale · heures).

    energie_produite_reelle : énergie effectivement produite (ex. MWh), >= 0.
    puissance_nominale : puissance nominale installée (ex. MW), > 0.
    heures : durée de la période en heures, > 0 (défaut 8760 = 1 an non bissextile).
    Renvoie un réel sans dimension dans [0, 1].
    puissance <= 0, heures <= 0, énergie < 0, ou résultat > 1 -> ValueError.
    """
    e = _reel_fini(energie_produite_reelle, "énergie produite")
    p = _reel_fini(puissance_nominale, "puissance nominale")
    h = _reel_fini(heures, "heures")
    if p <= 0.0:
        raise ValueError(f"puissance nominale non strictement positive : {p}")
    if h <= 0.0:
        raise ValueError(f"heures non strictement positives : {h}")
    if e < 0.0:
        raise ValueError(f"énergie produite négative : {e}")
    cf = e / (p * h)
    if cf > 1.0 + 1e-12:
        raise ValueError(
            f"facteur de charge > 1 physiquement impossible : {cf} "
            f"(énergie produite > puissance·heures)"
        )
    if cf > 1.0:
        cf = 1.0
    return _arr(cf)


def contenu_energetique(masse_kg, pci_MJ_kg):
    """
    Contenu énergétique = masse · PCI (mégajoules).

    masse_kg : masse de combustible en kg, >= 0.
    pci_MJ_kg : pouvoir calorifique inférieur en MJ/kg, > 0.
    Renvoie l'énergie libérable en MJ.
    masse < 0 ou PCI <= 0 -> ValueError.
    """
    m = _reel_fini(masse_kg, "masse")
    pci = _reel_fini(pci_MJ_kg, "PCI")
    if m < 0.0:
        raise ValueError(f"masse négative : {m}")
    if pci <= 0.0:
        raise ValueError(f"PCI non strictement positif : {pci}")
    return _arr(m * pci)


def retour_energetique(energie_produite, energie_investie):
    """
    Taux de retour énergétique EROI = énergie_produite / énergie_investie.

    energie_produite : énergie produite sur le cycle de vie (mêmes unités), >= 0.
    energie_investie : énergie investie pour la produire, > 0.
    Renvoie un réel sans dimension. > 1 = source viable.
    énergie investie <= 0 ou énergie produite < 0 -> ValueError.
    """
    out = _reel_fini(energie_produite, "énergie produite")
    inv = _reel_fini(energie_investie, "énergie investie")
    if inv <= 0.0:
        raise ValueError(f"énergie investie non strictement positive : {inv}")
    if out < 0.0:
        raise ValueError(f"énergie produite négative : {out}")
    return _arr(out / inv)


# Alias conventionnel.
eroi = retour_energetique


def emissions_co2(energie_kWh, facteur_g_kWh):
    """
    Émissions de CO2 = énergie · facteur d'émission (grammes de CO2 équivalent).

    energie_kWh : énergie consommée/produite en kWh, >= 0.
    facteur_g_kWh : facteur d'émission en gCO2eq/kWh, >= 0.
    Renvoie les émissions en gCO2eq.
    énergie < 0 ou facteur < 0 -> ValueError.
    """
    e = _reel_fini(energie_kWh, "énergie")
    f = _reel_fini(facteur_g_kWh, "facteur d'émission")
    if e < 0.0:
        raise ValueError(f"énergie négative : {e}")
    if f < 0.0:
        raise ValueError(f"facteur d'émission négatif : {f}")
    return _arr(e * f)


def facteur_co2_reference(source):
    """
    Facteur d'émission médian cycle de vie (gCO2eq/kWh) d'une source nommée.

    Source connue (GIEC AR5 2014, Annexe III) -> valeur ; sinon -> ValueError.
    """
    if not isinstance(source, str):
        raise ValueError(f"source non textuelle : {source!r}")
    cle = source.strip().lower()
    if cle not in FACTEUR_CO2_REF:
        raise ValueError(
            f"source inconnue : {source!r} (connues : {sorted(FACTEUR_CO2_REF)})"
        )
    return FACTEUR_CO2_REF[cle]
