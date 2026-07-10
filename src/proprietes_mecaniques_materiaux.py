"""
PROPRIÉTÉS MÉCANIQUES DE MATÉRIAUX NOMMÉS — catalogue d'INTERVALLES (PARTIE III, B-FAIT).

Même posture FAUX=0 que `physique` / `chimie` (la réalité juge, jamais un faux) :
  • `proprietes_materiaux.py` fournit la loi de Hooke GÉNÉRIQUE sans aucune constante matériau ;
    CE module fournit le CATALOGUE des valeurs pour des matériaux NOMMÉS.
  • Le MÉCANISME anti-faux : les propriétés d'un matériau réel dépendent de l'alliage, du traitement
    thermique/mécanique, de l'humidité, de la température. Une valeur SCALAIRE unique serait donc un FAUX.
    Chaque propriété est un INTERVALLE (min, max) issu des tables d'ingénierie classiques, accompagné de
    ses CONDITIONS de validité — jamais un scalaire présenté comme exact. Toutes les valeurs sont
    APPROCHÉES par nature (dispersion réelle des nuances) et MARQUÉES comme telles par l'intervalle.
  • Re est un ENCADREMENT GARANTI, PAS la plage typique : min = MINIMUM de spécification (toute nuance
    conforme aux conditions fait AU MOINS ça) ; max = MAJORANT (enveloppe haute prouvable : aucune nuance
    conforme aux conditions ne le dépasse). Un max « typique » rendrait le verdict 'non' FALSIFIABLE par
    de la matière réelle conforme (p. ex. du 6061-T6 de production mesure couramment 280-325 MPa quand la
    valeur typique tabulée dit 276) — ce serait un FAUX. Les valeurs typiques restent en commentaire.
  • JUGEMENT resiste(materiau, contrainte_MPa) -> 'oui' | 'non' | 'indéterminé' :
      – contrainte STRICTEMENT sous le min garanti      -> 'oui'  (toute nuance conforme tient) ;
      – contrainte STRICTEMENT au-dessus du MAJORANT    -> 'non'  (aucune nuance conforme n'y arrive) ;
      – contrainte DANS l'encadrement [min, majorant]   -> 'indéterminé' : on ne tranche pas
        ce que l'encadrement ne tranche pas — c'est le cœur du FAUX=0 ici (bornes incluses : conservateur).
  • MATÉRIAUX FRAGILES / SANS LIMITE ÉLASTIQUE CONVENTIONNELLE (béton, verre, fonte grise) et le bois
    (anisotrope, comportement non plastique en traction) : limite_elastique() et resiste() -> ValueError
    (abstention structurelle) plutôt qu'une pseudo-limite inventée.

GARANTIES (vérifiées en adverse par `valide_proprietes_mecaniques_materiaux.py`) :
  - matériau hors catalogue, nom non-str, str vide            -> ValueError ;
  - contrainte non numérique (bool/str/NaN/±inf) ou négative  -> ValueError ;
  - limite élastique demandée sur un matériau fragile/bois    -> ValueError (abstention) ;
  - tout intervalle rendu vérifie 0 < min < max ;
  - fonctions PURES, déterministes ; stdlib uniquement ; aucun état mutable exposé.

SOURCE = "tables d'ingénierie classiques : ASM Handbook vol.1-2, Ashby — Materials Selection in
Mechanical Design (CES), Eurocodes 2/3, MatWeb (plages recoupées, valeurs universellement tabulées)"
"""
from __future__ import annotations

import math

SOURCE = ("tables d'ingénierie classiques : ASM Handbook vol.1-2, Ashby (Materials Selection / CES), "
          "Eurocodes 2/3, MatWeb — plages recoupées, valeurs universellement tabulées")

# ── CATALOGUE ─────────────────────────────────────────────────────────────────────────────────────────────────
# Par matériau : E [GPa] (min, max) ; Re limite élastique [MPa] = ENCADREMENT (min de spec, MAJORANT) ou
# None (abstention : fragile / pas de limite conventionnelle) ; rho [kg/m³] (min, max) ; conditions (str).
_CATALOGUE: dict[str, dict] = {
    "acier doux": {
        "E": (200.0, 215.0),          # valeur d'ingénierie universelle ~200-215 GPa
        "Re": (235.0, 630.0),         # min : ReH min S235 = 235 MPa (EN 10025-2, t ≤ 16 mm) ; MAJORANT :
                                      # Re < Rm et Rm max S355 = 630 MPa (EN 10025-2) — les valeurs
                                      # TYPIQUES (235-460) restent strictement dans cet encadrement
        "rho": (7800.0, 7900.0),      # ~7850 kg/m³ typique
        "conditions": "acier au carbone non allié (type S235-S355, EN 10025-2), état laminé, "
                      "épaisseur ≤ 16 mm, 20 °C",
    },
    "acier inoxydable 304": {
        "E": (190.0, 203.0),          # austénitique 18-8, ~193-200 GPa tabulé
        "Re": (205.0, 690.0),         # min : Rp0,2 min recuit 205 MPa (ASTM A240) ; MAJORANT approché :
                                      # Re < Rm, et la dureté plafonnée du recuit (≤ 92 HRB / 201 HBW,
                                      # A240) borne Rm à ≈ 690 MPa (conversion A370) ; typique 205-350
        "rho": (7900.0, 8060.0),      # ~8000 kg/m³ typique
        "conditions": "austénitique 18Cr-8Ni (AISI 304), état recuit (hypertrempé, conforme ASTM A240 ; "
                      "l'écroui, même léger, est hors de cette entrée), 20 °C",
    },
    "aluminium 6061": {
        "E": (68.0, 72.0),            # ~68,9 GPa typique, plage tabulée 68-72
        "Re": (55.0, 350.0),          # min : état O ~55 MPa (ASM) ; MAJORANT : le T6 de production mesure
                                      # 280-325 MPa (dispersion ASM/MMPDS, aucune donnée tabulée O→T6
                                      # au-delà de ~325) -> majorant 350 ; la TYPIQUE T6 (276) n'est pas
                                      # une enveloppe et ne doit jamais servir au verdict 'non'
        "rho": (2690.0, 2710.0),      # ~2700 kg/m³
        "conditions": "alliage Al-Mg-Si 6061, du recuit (O) au revenu T6, 20 °C",
    },
    "cuivre": {
        "E": (110.0, 128.0),          # cuivre pur, ~110-128 GPa tabulé
        "Re": (33.0, 450.0),          # min : recuit ~33 MPa (ASM C11000) ; MAJORANT : l'écroui commercial
                                      # le plus dur (fil tréfilé / ressort extra-dur) plafonne Rp0,2 vers
                                      # ~420 MPa (ASM) -> majorant 450 ; l'« écroui dur » typique (~365)
                                      # n'est pas une enveloppe
        "rho": (8920.0, 8960.0),      # ~8940 kg/m³
        "conditions": "cuivre pur (Cu-ETP/OF), du recuit à l'écroui dur, 20 °C",
    },
    "titane ti-6al-4v": {
        "E": (110.0, 115.0),          # ~113,8 GPa typique
        "Re": (828.0, 1250.0),        # min : recuit 828 MPa (AMS 4911) ; MAJORANT : le STA réel atteint
                                      # ~1170 MPa en sections minces (ASM) -> majorant 1250 ; la TYPIQUE
                                      # STA (~1100) n'est pas une enveloppe
        "rho": (4420.0, 4450.0),      # ~4430 kg/m³
        "conditions": "alliage Ti-6Al-4V (grade 5), état recuit à STA, 20 °C",
    },
    "béton": {
        "E": (20.0, 40.0),            # module sécant, béton courant C20/25 à C50/60 (Eurocode 2)
        "Re": None,                   # fragile : pas de limite élastique — abstention structurelle
        "rho": (2200.0, 2500.0),      # béton non armé ~2200-2400, armé ~2500
        "conditions": "béton courant durci (C20/25 à C50/60), module sécant en compression, 28 jours ; "
                      "FRAGILE : pas de limite élastique définie (résistance ≠ plasticité)",
    },
    "bois de pin": {
        "E": (7.0, 14.0),             # SENS DES FIBRES (axial), bois résineux sec à 12 % d'humidité
        "Re": None,                   # anisotrope, pas de limite élastique conventionnelle — abstention
        "rho": (350.0, 600.0),        # pins courants secs à l'air
        "conditions": "bois de pin, sollicitation PARALLÈLE AU SENS DES FIBRES (axial), sec à ~12 % "
                      "d'humidité, 20 °C ; anisotrope : transverse aux fibres E est ~10-20× plus faible ; "
                      "pas de limite élastique conventionnelle (abstention)",
    },
    "verre": {
        "E": (60.0, 75.0),            # sodocalcique ~70, borosilicate ~64, plage verres courants 60-75
        "Re": None,                   # fragile : rupture sans plasticité — abstention structurelle
        "rho": (2200.0, 2800.0),      # borosilicate (Pyrex 7740) ≈ 2230, sodocalcique ≈ 2500 : le min
                                      # doit couvrir le borosilicate annoncé dans les conditions
        "conditions": "verre silicaté courant (sodocalcique, borosilicate), 20 °C ; FRAGILE : rupture "
                      "sans plasticité, pas de limite élastique (abstention)",
    },
    "polyéthylène": {
        "E": (0.1, 1.4),              # PEBD ~0,1-0,3 GPa à PEHD ~0,6-1,4 GPa
        "Re": (8.0, 45.0),            # min : seuil PEBD ~8 MPa ; MAJORANT : le PEHD homopolymère plafonne
                                      # vers ~38 MPa tabulé -> majorant 45 ; typiques PEBD 8-14, PEHD 20-33
        "rho": (910.0, 970.0),        # PEBD 910-925, PEHD 940-970
        "conditions": "polyéthylène PEBD à PEHD, 23 °C, sollicitation quasi statique (fort effet "
                      "vitesse/température : hors de ces conditions les valeurs ne tiennent pas)",
    },
    "fonte": {
        "E": (80.0, 150.0),           # fonte grise à graphite lamellaire, selon classe EN-GJL
        "Re": None,                   # grise : pas de limite élastique nette — abstention structurelle
        "rho": (6900.0, 7400.0),      # ~7100-7200 typique
        "conditions": "fonte GRISE à graphite lamellaire (EN-GJL-150 à 350), 20 °C ; pas de limite "
                      "élastique nette (courbe non linéaire dès l'origine) : abstention ; la fonte GS "
                      "(ductile) est un autre matériau, hors de cette entrée",
    },
    "magnésium": {
        "E": (44.0, 46.0),            # ~45 GPa (pur et alliages courants)
        "Re": (21.0, 300.0),          # min : pur recuit ~21 MPa ; MAJORANT : les corroyés couverts
                                      # plafonnent à ~275 MPa (AZ80A-T5, ASM) -> majorant 300
        "rho": (1738.0, 1850.0),      # pur 1738, alliages courants jusqu'à ~1850
        "conditions": "magnésium pur à alliages courants (AZ31/AZ61/AZ80), 20 °C",
    },
}

# Alias d'écriture sans ambiguïté (accents/casse) -> clé canonique. AUCUN alias approximatif.
_ALIAS = {
    "beton": "béton",
    "polyethylene": "polyéthylène",
    "magnesium": "magnésium",
    "titane ti6al4v": "titane ti-6al-4v",
}


def _cle(materiau) -> str:
    """Normalise le nom (casse/espaces) et exige sa présence au catalogue -> sinon ValueError."""
    if isinstance(materiau, bool) or not isinstance(materiau, str):
        raise ValueError("matériau invalide : un nom (str) est requis")
    nom = " ".join(materiau.strip().lower().split())
    nom = _ALIAS.get(nom, nom)
    if nom not in _CATALOGUE:
        raise ValueError(f"matériau hors catalogue : {materiau!r} (voir catalogue()) — abstention")
    return nom


def _num_positif_ou_nul(x, nom: str) -> float:
    """Exige un réel fini ≥ 0 (bool/str/NaN/±inf refusés) -> sinon ValueError."""
    if isinstance(x, bool) or not isinstance(x, (int, float)):
        raise ValueError(f"{nom} invalide : un nombre réel est requis")
    f = float(x)
    if not math.isfinite(f):
        raise ValueError(f"{nom} invalide : NaN/inf refusés")
    if f < 0:
        raise ValueError(f"{nom} invalide : une contrainte de traction est ≥ 0 (MPa)")
    return f


# ── API ───────────────────────────────────────────────────────────────────────────────────────────────────────
def catalogue() -> tuple:
    """Noms canoniques des matériaux couverts (tuple trié, immuable)."""
    return tuple(sorted(_CATALOGUE))


def module_young(materiau: str) -> tuple:
    """Module de Young E : intervalle APPROCHÉ (min_GPa, max_GPa). Hors catalogue -> ValueError."""
    e = _CATALOGUE[_cle(materiau)]["E"]
    return (e[0], e[1])


def limite_elastique(materiau: str) -> tuple:
    """Limite élastique Re : ENCADREMENT APPROCHÉ (min_MPa, majorant_MPa).

    min = minimum de spécification (toute nuance conforme fait au moins ça) ; max = MAJORANT (enveloppe
    haute prouvable), PAS une valeur typique : la vraie valeur d'une nuance donnée est quelque part DANS
    cet encadrement. Matériau fragile ou sans limite conventionnelle (béton, verre, fonte grise, bois)
    -> ValueError (abstention : une pseudo-limite serait un FAUX)."""
    fiche = _CATALOGUE[_cle(materiau)]
    if fiche["Re"] is None:
        raise ValueError(f"pas de limite élastique définie pour {materiau!r} "
                         "(matériau fragile ou sans limite conventionnelle) — abstention")
    re = fiche["Re"]
    return (re[0], re[1])


def masse_volumique(materiau: str) -> tuple:
    """Masse volumique ρ : intervalle APPROCHÉ (min, max) en kg/m³. Hors catalogue -> ValueError."""
    r = _CATALOGUE[_cle(materiau)]["rho"]
    return (r[0], r[1])


def conditions(materiau: str) -> str:
    """Conditions de validité des intervalles (alliage/traitement/température). Hors catalogue -> ValueError."""
    return _CATALOGUE[_cle(materiau)]["conditions"]


def resiste(materiau: str, contrainte_MPa) -> str:
    """La contrainte (MPa, traction quasi statique) reste-t-elle sous la limite élastique ?

    'oui' si contrainte < min garanti (toute nuance conforme tient) ; 'non' si contrainte > MAJORANT
    (aucune nuance conforme n'y arrive — le majorant est une enveloppe prouvable, jamais une typique) ;
    'indéterminé' si la contrainte tombe DANS [min, majorant] : l'encadrement ne tranche pas, on ne
    tranche pas. Matériau sans limite élastique définie -> ValueError (abstention)."""
    fiche = _CATALOGUE[_cle(materiau)]
    sigma = _num_positif_ou_nul(contrainte_MPa, "contrainte")
    if fiche["Re"] is None:
        raise ValueError(f"pas de limite élastique définie pour {materiau!r} — resiste() s'abstient")
    re_min, re_max = fiche["Re"]
    if sigma < re_min:
        return "oui"
    if sigma > re_max:
        return "non"
    return "indéterminé"
