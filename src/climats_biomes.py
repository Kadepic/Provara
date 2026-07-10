"""
CLIMATS & BIOMES — classification de KÖPPEN-GEIGER (convention publiée, B-CONV).

Même posture FAUX=0 que `galois`/`geometries_non_euclidiennes` : on n'expose QUE une CONVENTION
publiée et un arbre de décision DÉTERMINISTE, jamais une devinette.

  • Le MÉCANISME est une CLASSIFICATION conventionnelle (Köppen-Geiger, telle qu'enseignée) calculée
    depuis des données climatiques normales : 12 températures mensuelles moyennes (°C) et 12
    précipitations mensuelles (mm), plus l'hémisphère (qui fixe quels mois sont l'« été » et l'« hiver »).
  • L'arbre de décision est appliqué DANS CET ORDRE (choix de convention, déterministe) :
      1. E (polaire) si le mois le plus chaud T_max < 10 °C   ->  ET si 0 ≤ T_max < 10, EF si T_max < 0 ;
      2. B (aride)  si P_annuelle < seuil de sécheresse, avec
             seuil = 20·T_moyenne + 280  si ≥ 70 % des pluies tombent en été,
                   = 20·T_moyenne + 140  si réparties,
                   = 20·T_moyenne + 0    si ≥ 70 % en hiver ;
             BW si P_annuelle < seuil/2, BS sinon ; 3e lettre h si T_moyenne ≥ 18 °C sinon k ;
      3. A (tropical) si le mois le plus froid T_min ≥ 18 °C  ->  Af si P_min ≥ 60 mm,
             Am si P_min ≥ 100 − P_annuelle/25, Aw sinon ;
      4. C (tempéré) si −3 °C < T_min < 18 °C ;
      5. D (continental) si T_min ≤ −3 °C.
    Pour C et D : 2e lettre saisonnière s/w/f (été sec / hiver sec / sans saison sèche) puis 3e lettre
    a/b/c/d selon T_max et le nombre de mois > 10 °C (d pour D si T_min < −38 °C).

  • ATTENTION aux PIÈGES DE NOM du dépôt : `meteo` est un client d'API TEMPS RÉEL et `environnement`
    un portfolio de compilateurs — AUCUN rapport, non importés. Ici : pure classification hors-ligne.
  • La classification est DISCRÈTE (un code, ex. 'Cfb') : pas d'arrondi, pas de flottant en sortie.
    Les entrées sont des flottants (normales climatiques) : la sortie est un code exact, pas une mesure.

GARANTIES (vérifiées en adverse par `valide_climats_biomes.py`) :
  - liste de longueur ≠ 12 (températures ou précipitations) -> ValueError ;
  - valeur non numérique / bool / NaN / ±inf -> ValueError ; précipitation négative -> ValueError ;
  - hémisphère hors {nord, sud} -> ValueError ;
  - code inconnu passé à `libelle`/`biome_associe` -> ValueError (abstention, jamais un biome deviné) ;
  - déterministe ; conservateur (faux négatif toléré, faux POSITIF interdit).

Ancres non circulaires : classifications de villes universellement publiées (Paris Cfb, Singapour Af,
Le Caire BWh, Moscou Dfb, Reykjavik Cfc/ET, Utqiaġvik ET, Perth Csa) — cf. la gate.

Toutes les fonctions sont PURES et déterministes ; le module n'importe que `math` (stdlib).
"""
from __future__ import annotations

import math

SOURCE = "classification climatique de Köppen-Geiger (convention publiée ; cf. Peel, Finlayson & McMahon 2007)"


# ── VALIDATION ──────────────────────────────────────────────────────────────────────────────────────────────────
def _est_reel(x) -> bool:
    """True ssi x est un réel fini (les bool sont REFUSÉS : True n'est pas une mesure)."""
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x)


def _exige_serie(serie, nom: str, mini=None) -> list:
    """Exige une liste/tuple de 12 réels finis ; `mini` borne inférieure optionnelle (ex. pluie ≥ 0)."""
    if not isinstance(serie, (list, tuple)) or len(serie) != 12:
        raise ValueError(f"{nom} : exactement 12 valeurs mensuelles (liste/tuple) sont requises")
    out = []
    for v in serie:
        if not _est_reel(v):
            raise ValueError(f"{nom} : valeur non numérique / bool / NaN / inf refusée ({v!r})")
        if mini is not None and v < mini:
            raise ValueError(f"{nom} : valeur < {mini} refusée ({v!r})")
        out.append(float(v))
    return out


# NH : été = avril..septembre (indices 0-based 3..8), hiver = octobre..mars ; hémisphère sud = symétrique.
_ETE_NORD = (3, 4, 5, 6, 7, 8)
_HIVER_NORD = (9, 10, 11, 0, 1, 2)


def _saisons(hemisphere: str):
    """Renvoie (indices_ete, indices_hiver) selon l'hémisphère. Hémisphère invalide -> ValueError."""
    if not isinstance(hemisphere, str):
        raise ValueError(f"hémisphère (chaîne 'nord'/'sud') attendu, reçu {hemisphere!r}")
    h = hemisphere.strip().lower()
    if h in ("nord", "n", "north", "boreal", "boréal"):
        return _ETE_NORD, _HIVER_NORD
    if h in ("sud", "s", "south", "austral"):
        return _HIVER_NORD, _ETE_NORD  # les saisons sont inversées dans l'hémisphère sud
    raise ValueError(f"hémisphère inconnu (abstention) : {hemisphere!r} — attendu 'nord' ou 'sud'")


# ── SEUIL DE SÉCHERESSE (aride B) ───────────────────────────────────────────────────────────────────────────────
def seuil_secheresse(temperatures_mensuelles, precipitations_mensuelles, hemisphere: str) -> float:
    """Seuil de sécheresse de Köppen (mm) = 20·T_moyenne + {280 été | 140 réparti | 0 hiver}.

    Le régime saisonnier des pluies (≥70 % en été / en hiver / réparties) fixe le terme additif."""
    t = _exige_serie(temperatures_mensuelles, "températures")
    p = _exige_serie(precipitations_mensuelles, "précipitations", mini=0.0)
    idx_ete, idx_hiver = _saisons(hemisphere)
    t_moy = sum(t) / 12.0
    p_ann = sum(p)
    p_ete = sum(p[i] for i in idx_ete)
    p_hiver = sum(p[i] for i in idx_hiver)
    if p_ann <= 0.0:
        add = 140.0  # sans pluie, le régime saisonnier est indéfini ; terme neutre (n'affecte pas B : P=0 < seuil)
    elif p_ete >= 0.70 * p_ann:
        add = 280.0
    elif p_hiver >= 0.70 * p_ann:
        add = 0.0
    else:
        add = 140.0
    return 20.0 * t_moy + add


# ── ARBRE DE DÉCISION KÖPPEN ────────────────────────────────────────────────────────────────────────────────────
def _troisieme_lettre_cd(groupe: str, t_max: float, t_min: float, n_chauds: int) -> str:
    """3e lettre a/b/c/d pour C et D. a: T_max≥22 ; b: <22 et ≥4 mois >10°C ; c: sinon ; d (D): T_min<−38."""
    if groupe == "D" and t_min < -38.0:
        return "d"
    if t_max >= 22.0:
        return "a"
    if n_chauds >= 4:
        return "b"
    return "c"


def _deuxieme_lettre_cd(p, idx_ete, idx_hiver) -> str:
    """2e lettre s/w/f pour C et D (saison sèche).

    s (été sec méditerranéen) : mois d'été le plus sec < 40 mm ET < (mois d'hiver le plus humide)/3 ;
    w (hiver sec)             : mois d'hiver le plus sec < (mois d'été le plus humide)/10 ;
    f                         : sinon (pas de saison sèche marquée). s est testé avant w (convention)."""
    p_ete = [p[i] for i in idx_ete]
    p_hiver = [p[i] for i in idx_hiver]
    ete_sec = min(p_ete)
    ete_humide = max(p_ete)
    hiver_sec = min(p_hiver)
    hiver_humide = max(p_hiver)
    if ete_sec < 40.0 and ete_sec < hiver_humide / 3.0:
        return "s"
    if hiver_sec < ete_humide / 10.0:
        return "w"
    return "f"


def koppen(temperatures_mensuelles, precipitations_mensuelles, hemisphere: str) -> str:
    """Code de Köppen-Geiger (ex. 'Cfb', 'BWh', 'Af', 'Dfb', 'ET') depuis 12 T (°C) + 12 P (mm) + hémisphère.

    Arbre déterministe dans l'ordre E -> B -> A -> C -> D. Entrées invalides -> ValueError (abstention)."""
    t = _exige_serie(temperatures_mensuelles, "températures")
    p = _exige_serie(precipitations_mensuelles, "précipitations", mini=0.0)
    idx_ete, idx_hiver = _saisons(hemisphere)

    t_max = max(t)
    t_min = min(t)
    t_moy = sum(t) / 12.0
    p_ann = sum(p)
    p_min = min(p)
    n_chauds = sum(1 for x in t if x > 10.0)

    # 1. E — polaire : le mois le plus chaud reste sous 10 °C.
    if t_max < 10.0:
        return "ET" if t_max >= 0.0 else "EF"

    # 2. B — aride : précipitation annuelle sous le seuil de sécheresse.
    seuil = seuil_secheresse(t, p, hemisphere)
    if p_ann < seuil:
        w_ou_s = "W" if p_ann < seuil / 2.0 else "S"
        chaleur = "h" if t_moy >= 18.0 else "k"
        return "B" + w_ou_s + chaleur

    # 3. A — tropical : le mois le plus froid reste au-dessus de 18 °C.
    if t_min >= 18.0:
        if p_min >= 60.0:
            return "Af"
        if p_min >= 100.0 - p_ann / 25.0:
            return "Am"
        return "Aw"

    # 4/5. C (tempéré, −3 < T_min < 18) ou D (continental, T_min ≤ −3).
    groupe = "C" if t_min > -3.0 else "D"
    l2 = _deuxieme_lettre_cd(p, idx_ete, idx_hiver)
    l3 = _troisieme_lettre_cd(groupe, t_max, t_min, n_chauds)
    return groupe + l2 + l3


# ── LIBELLÉS & BIOMES (catalogue de convention) ─────────────────────────────────────────────────────────────────
_LIBELLES = {
    "Af": "climat équatorial (tropical humide sans saison sèche)",
    "Am": "climat tropical de mousson",
    "Aw": "climat tropical de savane (hiver sec)",
    "As": "climat tropical de savane (été sec)",
    "BWh": "climat désertique chaud",
    "BWk": "climat désertique froid",
    "BSh": "climat de steppe chaud (semi-aride)",
    "BSk": "climat de steppe froid (semi-aride)",
    "Cfa": "climat subtropical humide (tempéré sans saison sèche, été chaud)",
    "Cfb": "climat océanique tempéré (sans saison sèche, été doux)",
    "Cfc": "climat océanique frais (subpolaire océanique)",
    "Csa": "climat méditerranéen à été chaud",
    "Csb": "climat méditerranéen à été doux",
    "Csc": "climat méditerranéen frais",
    "Cwa": "climat subtropical humide à hiver sec",
    "Cwb": "climat subtropical d'altitude à hiver sec",
    "Cwc": "climat subpolaire d'altitude à hiver sec",
    "Dfa": "climat continental humide à été chaud",
    "Dfb": "climat continental humide à été tempéré",
    "Dfc": "climat continental subarctique (sans saison sèche)",
    "Dfd": "climat continental subarctique à hiver très froid",
    "Dsa": "climat continental à été chaud et sec",
    "Dsb": "climat continental à été doux et sec",
    "Dsc": "climat continental subarctique à été sec",
    "Dsd": "climat continental subarctique à hiver très froid et été sec",
    "Dwa": "climat continental humide à hiver sec, été chaud",
    "Dwb": "climat continental humide à hiver sec, été tempéré",
    "Dwc": "climat continental subarctique à hiver sec",
    "Dwd": "climat continental subarctique à hiver sec très froid",
    "ET": "climat de toundra (polaire)",
    "EF": "climat de calotte glaciaire (inlandsis)",
}

_BIOMES = {
    "Af": "forêt tropicale humide",
    "Am": "forêt tropicale humide",
    "Aw": "savane",
    "As": "savane",
    "BWh": "désert chaud",
    "BWk": "désert froid",
    "BSh": "steppe chaude",
    "BSk": "steppe froide",
    "Cfa": "forêt subtropicale humide",
    "Cfb": "forêt tempérée",
    "Cfc": "forêt tempérée océanique",
    "Csa": "forêt et maquis méditerranéens",
    "Csb": "forêt et maquis méditerranéens",
    "Csc": "forêt et maquis méditerranéens",
    "Cwa": "forêt subtropicale humide",
    "Cwb": "forêt subtropicale d'altitude",
    "Cwc": "prairie d'altitude",
    "Dfa": "forêt tempérée mixte",
    "Dfb": "forêt tempérée mixte",
    "Dfc": "taïga (forêt boréale)",
    "Dfd": "taïga (forêt boréale)",
    "Dsa": "forêt tempérée continentale",
    "Dsb": "forêt tempérée continentale",
    "Dsc": "taïga (forêt boréale)",
    "Dsd": "taïga (forêt boréale)",
    "Dwa": "forêt tempérée continentale",
    "Dwb": "forêt tempérée continentale",
    "Dwc": "taïga (forêt boréale)",
    "Dwd": "taïga (forêt boréale)",
    "ET": "toundra",
    "EF": "désert glacé (inlandsis)",
}


# index de recherche insensible à la casse : la forme majuscule du code -> code canonique catalogué.
_INDEX = {k.upper(): k for k in _LIBELLES}


def _norm_code(code: str) -> str:
    """Renvoie le code canonique (ex. 'cfb'->'Cfb', 'et'->'ET'), sans deviner : code inconnu -> ValueError."""
    if not isinstance(code, str):
        raise ValueError(f"code de Köppen (chaîne) attendu, reçu {code!r}")
    cle = code.strip().upper()
    if cle not in _INDEX:
        raise ValueError(f"code de Köppen inconnu (abstention) : {code!r}")
    return _INDEX[cle]


def libelle(code: str) -> str:
    """Description française d'un code de Köppen. Code inconnu -> ValueError (abstention)."""
    c = _norm_code(code)
    if c not in _LIBELLES:
        raise ValueError(f"code de Köppen inconnu (abstention) : {code!r}")
    return _LIBELLES[c]


def biome_associe(code: str) -> str:
    """Biome dominant associé à un code de Köppen. Code inconnu -> ValueError (abstention)."""
    c = _norm_code(code)
    if c not in _BIOMES:
        raise ValueError(f"code de Köppen inconnu (abstention) : {code!r}")
    return _BIOMES[c]


def codes_connus() -> tuple:
    """Liste triée des codes de Köppen catalogués (libellé + biome)."""
    return tuple(sorted(_LIBELLES))
