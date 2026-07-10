"""
ÉQUATIONS POLYNOMIALES — résolution EFFECTIVE des degrés 1 à 4, FAUX=0 (sujet B-NEC, PARTIE I).

Distinct de `galois` (qui CLASSIFIE la résolubilité par radicaux sans calculer aucune racine) : ici on
RÉSOUT, et chaque réponse est PROUVÉE, jamais un flottant plausible déguisé en vérité.

  • Racines RATIONNELLES : rendues EXACTEMENT (`Fraction`) par le théorème des racines rationnelles +
    déflation, et chacune est CERTIFIÉE par l'évaluation exacte  p(r) == 0  (arithmétique rationnelle,
    zéro arrondi). Les multiplicités sont exactes (décomposition sans carré de Yun). RÉSERVE : si un
    coefficient entier (après mise à l'échelle) dépasse 10¹², la recherche rationnelle RENONCE (coût
    d'énumération des diviseurs) — elle est alors INCOMPLÈTE et le dit
    ('exactitude_rationnelle_complete': False) ; voir 'reelles_non_classees' ci-dessous.

  • Racines réelles IRRATIONNELLES : jamais inventées. Une racine n'entre dans 'reelles_irrationnelles'
    QUE si son irrationalité est PROUVÉE : la recherche rationnelle a été EXHAUSTIVE sur le facteur
    (tous les candidats p/q du théorème des racines rationnelles essayés et rejetés), donc le reste n'a
    AUCUNE racine rationnelle. On rend un INTERVALLE RATIONNEL [lo, hi] PROUVÉ contenir exactement une
    racine (suites de STURM + dichotomie, arithmétique exacte), de largeur ≤ tol, PLUS un flottant
    explicitement MARQUÉ « approché » (clé 'approche': True). L'intervalle exact reste la vérité ; le
    flottant n'est qu'un confort de lecture.

  • Racines réelles NON CLASSÉES : quand la recherche rationnelle a renoncé (coefficients > 10¹²),
    l'irrationalité des racines restantes n'est PAS prouvée — elles pourraient être rationnelles. Elles
    vont alors dans 'reelles_non_classees' (même certificat d'intervalle par Sturm, même flottant marqué
    approché), chaque entrée portant 'rationalite_indeterminee': True. JAMAIS dans
    'reelles_irrationnelles' : affirmer une catégorie non prouvée serait un faux positif.

  • Racines COMPLEXES non réelles : on en donne le NOMBRE exact (degré − racines réelles, avec
    multiplicité), sans les énumérer — abstention structurelle, jamais un faux.

  • `cardan` (degré 3) croise DEUX chemins indépendants : le signe du DISCRIMINANT
        Δ = 18abcd − 4b³d + b²c² − 4ac³ − 27a²d²
    (Δ > 0 ⇔ 3 racines réelles distinctes ; Δ = 0 ⇔ racine multiple, toutes réelles ;
     Δ < 0 ⇔ 1 réelle et 2 complexes conjuguées — classification classique de la cubique réelle)
    contre le comptage de Sturm. Toute divergence -> RuntimeError (invariant violé), jamais un résultat.

Les briques polynomiales exactes (_p_eval, _p_divmod, _sans_carre, _racines_rationnelles,
_racines_reelles/Sturm) sont RÉUTILISÉES depuis `valeurs_propres` (pas de duplication).

GARANTIES (vérifiées en adverse par `valide_equations_polynomiales.py`) :
  - degré > 4                         -> ValueError ('insoluble par radicaux en général,
                                         cf. galois.resoluble_par_radicaux') ;
  - coefficient dominant nul          -> ValueError (le degré annoncé serait un mensonge) ;
  - degré < 1 (constante / vide)      -> ValueError (rien à résoudre) ;
  - entrée flottante / bool / str / complexe / NaN / inf -> ValueError (int ou Fraction exigé :
    0.1 n'est pas un rationnel exact, True n'est pas 1) ;
  - tol non rationnel ou ≤ 0          -> ValueError ;
  - recherche rationnelle bornée (coefficient > 10¹²) -> les racines réelles restantes sont rendues
    dans 'reelles_non_classees' (rationalité INDÉTERMINÉE, marquée sur chaque entrée), JAMAIS affirmées
    irrationnelles ; 'reelles_irrationnelles' ne contient QUE des irrationalités prouvées ;
  - INVARIANT dur : Σ multiplicités (rationnelles + réelles irrationnelles + non classées + complexes)
    = degré,
    sinon RuntimeError — jamais une résolution silencieusement incomplète ;
  - déterministe ; conservateur (abstention tolérée, faux POSITIF interdit).

Le module n'importe que la stdlib (`fractions`) et les helpers exacts de `valeurs_propres`.
"""
from __future__ import annotations

from fractions import Fraction

from valeurs_propres import (
    _p_deg,
    _p_eval,
    _p_norm,
    _racines_rationnelles,
    _racines_reelles,
    _sans_carre,
)

SOURCE = ("théorème des racines rationnelles + déflation (racines exactes) · suites de Sturm "
          "(isolation certifiée des racines réelles) · décomposition sans carré de Yun (multiplicités) · "
          "discriminant de la cubique Δ = 18abcd − 4b³d + b²c² − 4ac³ − 27a²d² (classification classique) · "
          "Cardan/Ferrari : degrés 3 et 4 résolubles, degré ≥ 5 non résoluble en général (Abel–Ruffini, "
          "cf. galois.resoluble_par_radicaux)")

_DEGRE_MAX = 4
_TOL_DEFAUT = Fraction(1, 10 ** 12)

# natures de la cubique (classification par le discriminant — chaînes stables, testées en adverse)
NATURE_3_REELLES_DISTINCTES = "3 réelles distinctes"
NATURE_RACINE_MULTIPLE = "racine multiple (toutes réelles)"
NATURE_1_REELLE_2_COMPLEXES = "1 réelle, 2 complexes conjuguées"


# ── VALIDATION DES ENTRÉES ─────────────────────────────────────────────────────────────────────────────────────
def _exige_coeff(x) -> Fraction:
    """Coefficient : int ou Fraction UNIQUEMENT. bool/float/str/complexe/NaN/inf -> ValueError."""
    if isinstance(x, bool):
        raise ValueError("coefficient invalide : un booléen n'est pas un nombre (True n'est pas 1)")
    if isinstance(x, int):
        return Fraction(x)
    if isinstance(x, Fraction):
        return x
    raise ValueError(
        "coefficient invalide : int ou Fraction exigé (le flottant est refusé — 0.1 n'est pas un rationnel "
        "exact ; utiliser Fraction(1, 10))")


def _exige_coeffs(coeffs):
    """Coefficients du degré le plus HAUT au plus BAS. Renvoie le polynôme interne (indice = degré)."""
    if not isinstance(coeffs, (list, tuple)) or len(coeffs) == 0:
        raise ValueError("coefficients invalides : une séquence non vide (haut -> bas) est requise")
    if len(coeffs) > _DEGRE_MAX + 1:
        raise ValueError("degré %d : insoluble par radicaux en général, cf. galois.resoluble_par_radicaux "
                         "(Abel–Ruffini) — ce module résout les degrés 1 à 4" % (len(coeffs) - 1))
    exacts = [_exige_coeff(c) for c in coeffs]
    if exacts[0] == 0:
        raise ValueError("coefficient dominant nul : le degré annoncé est faux (retirer les zéros de tête)")
    if len(exacts) < 2:
        raise ValueError("degré 0 (constante) : aucune inconnue, rien à résoudre")
    return list(reversed(exacts))                      # représentation interne : indice = degré


def _exige_tol(tol) -> Fraction:
    if isinstance(tol, bool) or not isinstance(tol, (int, Fraction)):
        raise ValueError("tol invalide : int ou Fraction exigé (exactitude requise)")
    tol = Fraction(tol)
    if tol <= 0:
        raise ValueError("tol invalide : un rationnel strictement positif est requis")
    return tol


# ── ÉPUISEMENT DES RACINES RATIONNELLES ────────────────────────────────────────────────────────────────────────
def _racines_rationnelles_epuisees(f):
    """Épuise les racines rationnelles de f (sans carré) en itérant `_racines_rationnelles` jusqu'au
    point fixe.

    NÉCESSAIRE (constaté en adverse, pas supposé) : le helper réutilisé s'arrête sur le PREMIER signe
    gagnant pour un couple (p, q) donné — ex. sur x⁴ − 5x² + 4 il trouve +1 et +2 mais laisse −1 et −2
    dans le reste. Le rappeler sur le reste converge (chaque passe qui trouve au moins une racine fait
    strictement baisser le degré). Renvoie (racines, reste, complet)."""
    racines = []
    complet = True
    while True:
        rs, f, ok = _racines_rationnelles(f)
        complet = complet and ok
        racines.extend(rs)
        if not rs or _p_deg(f) < 1:
            return racines, f, complet


# ── RÉSOLUTION EFFECTIVE (degrés 1 à 4) ────────────────────────────────────────────────────────────────────────
def resout(coeffs, tol=_TOL_DEFAUT) -> dict:
    """Résout p(x) = 0 pour p de degré 1 à 4, coefficients du degré le plus HAUT au plus BAS.

    Renvoie un dict :
      'degre'                    : degré (1..4) ;
      'rationnelles'             : [(Fraction r, multiplicité)] — EXACTES, chacune CERTIFIÉE p(r) == 0 ;
      'reelles_irrationnelles'   : [{'intervalle': (lo, hi) Fractions PROUVÉ (Sturm) encadrer exactement
                                     une racine, largeur ≤ tol, 'approx': float, 'approche': True,
                                     'multiplicite': m}] — irrationalité PROUVÉE (recherche rationnelle
                                     EXHAUSTIVE sur le facteur, aucun candidat p/q restant) ;
      'reelles_non_classees'     : mêmes entrées + 'rationalite_indeterminee': True — racines réelles
                                   dont la rationalité est INCONNUE parce que la recherche rationnelle a
                                   renoncé (coefficient > 10¹²) ; l'intervalle Sturm reste PROUVÉ, mais
                                   aucune catégorie n'est affirmée (FAUX=0) ;
      'nb_reelles'               : nombre de racines réelles, AVEC multiplicité ;
      'nb_complexes_non_reelles' : nombre EXACT de racines non réelles, avec multiplicité ;
      'exactitude_rationnelle_complete' : False si la recherche rationnelle a été bornée (coefficients
                                          géants) — honnêteté, pas un faux.

    INVARIANT : Σ multiplicités = degré, sinon RuntimeError (jamais une résolution silencieusement
    incomplète)."""
    p = _exige_coeffs(coeffs)
    tol = _exige_tol(tol)
    degre = _p_deg(p)

    rationnelles = {}
    irrationnelles = []
    non_classees = []
    complexes = 0
    complet = True

    for facteur, mult in _sans_carre(p):
        rats, reste, ok = _racines_rationnelles_epuisees(facteur)
        complet = complet and ok
        for r in rats:
            rationnelles[r] = rationnelles.get(r, 0) + mult
        if _p_deg(reste) >= 1:
            brackets = _racines_reelles(reste, tol)
            for lo, hi in brackets:
                if lo == hi:                            # racine rationnelle attrapée par le milieu exact
                    rationnelles[lo] = rationnelles.get(lo, 0) + mult
                elif ok:
                    # recherche rationnelle EXHAUSTIVE sur ce facteur : le reste n'a AUCUNE racine
                    # rationnelle, donc la racine encadrée est PROUVÉE irrationnelle
                    irrationnelles.append({"intervalle": (lo, hi),
                                           "approx": float((lo + hi) / 2),
                                           "approche": True,
                                           "multiplicite": mult})
                else:
                    # recherche rationnelle BORNÉE (coefficient > 10¹²) : la racine encadrée pourrait
                    # être rationnelle — catégorie NON affirmée, entrée MARQUÉE indéterminée (FAUX=0)
                    non_classees.append({"intervalle": (lo, hi),
                                         "approx": float((lo + hi) / 2),
                                         "approche": True,
                                         "multiplicite": mult,
                                         "rationalite_indeterminee": True})
            complexes += (_p_deg(reste) - len(brackets)) * mult

    # CERTIFICATION : chaque racine rationnelle annulée EXACTEMENT sur le polynôme d'ORIGINE
    for r in rationnelles:
        if _p_eval(p, r) != 0:
            raise RuntimeError("racine rationnelle non certifiée : p(r) ≠ 0 (invariant violé)")
    nb_reelles = (sum(rationnelles.values()) + sum(d["multiplicite"] for d in irrationnelles)
                  + sum(d["multiplicite"] for d in non_classees))
    if nb_reelles + complexes != degre:
        raise RuntimeError("résolution incomplète : Σ multiplicités = %d ≠ degré = %d (invariant violé)"
                           % (nb_reelles + complexes, degre))

    return {
        "degre": degre,
        "rationnelles": sorted(rationnelles.items()),
        "reelles_irrationnelles": sorted(irrationnelles, key=lambda d: d["intervalle"][0]),
        "reelles_non_classees": sorted(non_classees, key=lambda d: d["intervalle"][0]),
        "nb_reelles": nb_reelles,
        "nb_complexes_non_reelles": complexes,
        "exactitude_rationnelle_complete": complet,
    }


# ── DISCRIMINANT DE LA CUBIQUE (exact) ─────────────────────────────────────────────────────────────────────────
def discriminant_cubique(a, b, c, d) -> Fraction:
    """Δ = 18abcd − 4b³d + b²c² − 4ac³ − 27a²d²  pour  ax³ + bx² + cx + d  (a ≠ 0), EXACT.

    Δ > 0 ⇔ 3 racines réelles distinctes ; Δ = 0 ⇔ racine multiple (toutes réelles) ;
    Δ < 0 ⇔ 1 racine réelle et 2 complexes conjuguées."""
    a, b, c, d = (_exige_coeff(x) for x in (a, b, c, d))
    if a == 0:
        raise ValueError("coefficient dominant nul : pas une cubique (a ≠ 0 requis)")
    return 18 * a * b * c * d - 4 * b ** 3 * d + b ** 2 * c ** 2 - 4 * a * c ** 3 - 27 * a ** 2 * d ** 2


# ── CARDAN (degré 3) : résolution + classification CROISÉE discriminant/Sturm ──────────────────────────────────
def cardan(a, b, c, d, tol=_TOL_DEFAUT) -> dict:
    """Résout ax³ + bx² + cx + d = 0 (a ≠ 0). Renvoie le dict de `resout` enrichi de :
      'discriminant' : Δ exact (Fraction) ;
      'nature'       : classification par Δ, VÉRIFIÉE contre le comptage de Sturm (RuntimeError si
                       divergence — deux chemins indépendants doivent coïncider, sinon on s'abstient)."""
    res = resout([a, b, c, d], tol)                    # valide aussi les entrées (a == 0 -> ValueError)
    disc = discriminant_cubique(a, b, c, d)
    mults = ([m for _, m in res["rationnelles"]]
             + [e["multiplicite"] for e in res["reelles_irrationnelles"]]
             + [e["multiplicite"] for e in res["reelles_non_classees"]])
    if disc > 0:
        nature = NATURE_3_REELLES_DISTINCTES
        attendu_ok = (res["nb_reelles"] == 3 and res["nb_complexes_non_reelles"] == 0
                      and all(m == 1 for m in mults))
    elif disc == 0:
        nature = NATURE_RACINE_MULTIPLE
        attendu_ok = (res["nb_reelles"] == 3 and res["nb_complexes_non_reelles"] == 0
                      and any(m >= 2 for m in mults))
    else:
        nature = NATURE_1_REELLE_2_COMPLEXES
        attendu_ok = (res["nb_reelles"] == 1 and res["nb_complexes_non_reelles"] == 2)
    if not attendu_ok:
        raise RuntimeError("cubique : le discriminant et le comptage de Sturm divergent (invariant violé)")
    res["discriminant"] = disc
    res["nature"] = nature
    return res


# ── FERRARI (degré 4) : résolution effective de la quartique ───────────────────────────────────────────────────
def ferrari(a, b, c, d, e, tol=_TOL_DEFAUT) -> dict:
    """Résout ax⁴ + bx³ + cx² + dx + e = 0 (a ≠ 0) : dict de `resout` (racines rationnelles exactes,
    réelles irrationnelles encadrées par Sturm, nombre exact de complexes)."""
    coeffs = [a, b, c, d, e]
    for x in coeffs:
        _exige_coeff(x)
    if _exige_coeff(a) == 0:
        raise ValueError("coefficient dominant nul : pas une quartique (a ≠ 0 requis)")
    return resout(coeffs, tol)
