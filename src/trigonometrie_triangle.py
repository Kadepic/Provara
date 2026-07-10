"""
TRIGONOMÉTRIE DU TRIANGLE — résolution COMPLÈTE d'un triangle quelconque, FAUX=0.

Ce module PROLONGE `trigonometrie.py` (qui fournit sin/cos/tan en degrés, la LOI DES COSINUS et l'angle
par les côtés) SANS le modifier : il l'importe et le réutilise. `trigonometrie` annonce la loi des SINUS
dans sa docstring mais ne l'implémente PAS — c'est fait ici, avec la résolution des cinq cas classiques.

MÉCANISME (théorèmes EXACTS, jamais une corrélation) :
  • LOI DES SINUS :  a/sin A = b/sin B = c/sin C  ⟹  loi_sinus(a, A, B) = a·sin B / sin A  (côté opposé à B).
  • RÉSOLUTION DES CAS classiques (donnees['cas']) :
      – 'CCC' (SSS, trois côtés) : angles par la loi des cosinus inverse ;
      – 'CAC' (SAS, côté-angle-côté) : troisième côté par la loi des cosinus, puis les angles ;
      – 'ACA' (ASA, angle-côté-angle) : troisième angle = 180−A−C, puis les côtés par la loi des sinus ;
      – 'AAC' (AAS, angle-angle-côté) : idem, côté connu non inclus ;
      – 'CCA' (SSA, côté-côté-angle) : LE CAS AMBIGU — 0, 1 ou 2 triangles.
  • CAS AMBIGU SSA (cœur FAUX=0) : soit a le côté opposé à l'angle connu A, b l'autre côté connu,
    h = b·sin A (hauteur). Pour A aigu :  a < h → 0 solution ;  a = h → 1 (rectangle) ;
    h < a < b → 2 solutions ;  a ≥ b → 1 solution. Pour A ≥ 90° : 1 solution ssi a > b, sinon 0.
    `resout_triangle` rend TOUJOURS la LISTE des triangles solutions (0, 1 ou 2) — JAMAIS un unique
    triangle choisi au hasard.
  • AIRE par DEUX chemins qui doivent COÏNCIDER : aire_heron(a,b,c) = √(s(s−a)(s−b)(s−c)) et
    aire_sinus(a,b,C) = ½·a·b·sin C.
  • VALEURS EXACTES : sin_exact(angle) rend une expression EXACTE pour 0/30/45/60/90° (Fraction pour un
    rationnel, couple (num, radicande, den) = num·√radicande/den pour un radical) ; tout autre angle est
    APPROCHÉ et MARQUÉ tel : couple (valeur_flottante, 'approchee').

PRÉCISION HONNÊTE : les résolutions numériques sont arrondies à 12 décimales (comme `trigonometrie`) ; les
angles remarquables retombent exacts (angle opposé à l'hypoténuse 3-4-5 = 90.0). Ce qui est approché est dit.

GARANTIES (vérifiées en adverse par `valide_trigonometrie_triangle.py`) :
  - inégalité triangulaire violée (a+b ≤ c, …) -> ValueError ;
  - côté ≤ 0 -> ValueError ; angle ≤ 0 ou ≥ 180 -> ValueError ; somme des angles ≥ 180 -> ValueError ;
  - cas inconnu / clés manquantes dans `donnees` -> ValueError (on ne devine jamais le cas) ;
  - types invalides (bool, str, NaN, ±inf, mauvaise arité) -> ValueError ;
  - PUR, déterministe ; conservateur (faux négatif toléré, faux POSITIF interdit).

Toutes les fonctions sont PURES et déterministes. stdlib UNIQUEMENT (math, fractions) + `trigonometrie`.
"""
from __future__ import annotations

import math
from fractions import Fraction

import trigonometrie as T

SOURCE = "loi des sinus / loi des cosinus / formule de Héron (trigonométrie euclidienne classique)"

_DEC = 12          # mêmes 12 décimales que trigonometrie (précision honnête)
_EPS = 1e-9        # tolérance pour le cas a == h (rectangle) du cas ambigu SSA


# ── helpers internes ─────────────────────────────────────────────────────────────────────────────────────────────
def _reel(x) -> float:
    """Réel fini. bool REFUSÉS (True n'est pas 1) ; str/complexe REFUSÉS ; NaN/inf REFUSÉS."""
    if isinstance(x, bool) or not isinstance(x, (int, float)):
        raise ValueError(f"nombre réel attendu, reçu {x!r}")
    x = float(x)
    if not math.isfinite(x):
        raise ValueError("valeur non finie (NaN/inf) refusée")
    return x


def _cote(x) -> float:
    """Longueur d'un côté : réel STRICTEMENT positif."""
    x = _reel(x)
    if x <= 0:
        raise ValueError(f"côté > 0 requis, reçu {x}")
    return x


def _angle(x) -> float:
    """Angle d'un triangle en degrés : réel dans ]0, 180[ (strict)."""
    x = _reel(x)
    if not (0.0 < x < 180.0):
        raise ValueError(f"angle dans ]0, 180[ degrés requis, reçu {x}")
    return x


# ── VÉRIFICATION / INÉGALITÉ TRIANGULAIRE ────────────────────────────────────────────────────────────────────────
def verifie_triangle(a, b, c) -> bool:
    """Vrai si (a, b, c) forment un triangle non dégénéré (inégalité triangulaire STRICTE).

    Côté ≤ 0 ou inégalité violée (a+b ≤ c, a+c ≤ b, b+c ≤ a) -> ValueError (abstention, jamais un faux)."""
    a, b, c = _cote(a), _cote(b), _cote(c)
    if a + b <= c or a + c <= b or b + c <= a:
        raise ValueError(f"inégalité triangulaire violée pour ({a}, {b}, {c})")
    return True


# ── LOI DES SINUS ────────────────────────────────────────────────────────────────────────────────────────────────
def loi_sinus(a, A, B) -> float:
    """Côté opposé à l'angle B, connaissant le côté a opposé à A :  b = a·sin B / sin A.

    a > 0 ; A, B dans ]0, 180[ degrés (sin A ≠ 0 alors garanti). Résultat arrondi à 12 décimales."""
    a = _cote(a)
    A = _angle(A)
    B = _angle(B)
    sinA = T.sin_deg(A)
    if sinA == 0.0:                      # impossible dans ]0,180[, garde défensive
        raise ValueError("sin A = 0 : loi des sinus non applicable")
    return round(a * T.sin_deg(B) / sinA, _DEC)


# ── AIRE (DEUX CHEMINS INDÉPENDANTS) ─────────────────────────────────────────────────────────────────────────────
def aire_heron(a, b, c) -> float:
    """Aire par la formule de Héron : A = √(s(s−a)(s−b)(s−c)), s = (a+b+c)/2. Triangle valide requis."""
    verifie_triangle(a, b, c)
    a, b, c = float(a), float(b), float(c)
    s = (a + b + c) / 2.0
    prod = s * (s - a) * (s - b) * (s - c)
    if prod < 0:                          # ne peut arriver que par erreur d'arrondi extrême
        raise ValueError("produit de Héron négatif (triangle dégénéré)")
    return round(math.sqrt(prod), _DEC)


def aire_sinus(a, b, C) -> float:
    """Aire par deux côtés et l'angle inclus : A = ½·a·b·sin C. a,b > 0 ; C dans ]0,180[ degrés."""
    a = _cote(a)
    b = _cote(b)
    C = _angle(C)
    return round(0.5 * a * b * T.sin_deg(C), _DEC)


# ── COMPLÉTION D'UN TRIANGLE À PARTIR DES TROIS CÔTÉS ─────────────────────────────────────────────────────────────
def _complet(a: float, b: float, c: float) -> dict:
    """Triangle complet (côtés + angles opposés en degrés) à partir des trois côtés. Valide l'inégalité."""
    verifie_triangle(a, b, c)
    A = T.angle_par_cotes(b, c, a)        # angle opposé à a
    B = T.angle_par_cotes(a, c, b)        # angle opposé à b
    C = T.angle_par_cotes(a, b, c)        # angle opposé à c
    return {
        "a": round(float(a), _DEC), "b": round(float(b), _DEC), "c": round(float(c), _DEC),
        "A": A, "B": B, "C": C,
    }


def _cle(donnees: dict, nom: str):
    if nom not in donnees:
        raise ValueError(f"clé '{nom}' manquante dans donnees")
    return donnees[nom]


# ── CAS AMBIGU SSA (côté-côté-angle) ─────────────────────────────────────────────────────────────────────────────
def _resout_ssa(a: float, b: float, A: float) -> list:
    """Cas ambigu : a côté opposé à l'angle connu A, b l'autre côté connu. Rend 0, 1 ou 2 triangles."""
    a = _cote(a)
    b = _cote(b)
    A = _angle(A)
    sinA = T.sin_deg(A)
    h = b * sinA                          # hauteur issue du sommet opposé à b

    if A >= 90.0:
        # Angle connu droit/obtus : le côté opposé DOIT être le plus grand -> au plus 1 solution.
        nb = 1 if a > b + _EPS else 0
    else:
        if a < h - _EPS:
            nb = 0                        # a < h : le côté n'atteint pas la base
        elif abs(a - h) <= _EPS:
            nb = 1                        # a = h : triangle RECTANGLE (B = 90°)
        elif a < b - _EPS:
            nb = 2                        # h < a < b : DEUX triangles
        else:
            nb = 1                        # a ≥ b : un seul

    if nb == 0:
        return []

    ratio = max(-1.0, min(1.0, b * sinA / a))
    B1 = math.degrees(math.asin(ratio))   # solution aiguë
    angles_B = [B1] if nb == 1 else [B1, 180.0 - B1]

    triangles = []
    for B in angles_B:
        C = 180.0 - A - B
        if C <= _EPS:                     # garde : troisième angle non positif -> pas un triangle
            continue
        c = loi_sinus(a, A, C)            # côté opposé à C par la loi des sinus
        triangles.append(_complet(a, b, c))
    return triangles


# ── RÉSOLUTION GÉNÉRALE ──────────────────────────────────────────────────────────────────────────────────────────
def resout_triangle(donnees) -> list:
    """Résout un triangle. `donnees` = dict nommant le cas et ses données. Rend TOUJOURS une LISTE de
    triangles (dict côtés+angles). Cas déterministes -> 1 élément ; cas ambigu 'CCA' -> 0, 1 ou 2.

    Cas & clés attendus :
      'CCC' : a, b, c                     (trois côtés)
      'CAC' : b, c, A                     (deux côtés b,c et l'angle inclus A, opposé à a)
      'ACA' : A, C, b                     (deux angles A,C et le côté inclus b, opposé à B)
      'AAC' : A, B, a                     (deux angles A,B et le côté a opposé à A)
      'CCA' : a, b, A                     (a opposé à A, b l'autre côté ; cas AMBIGU)
    Cas inconnu / clé manquante -> ValueError (on ne devine jamais)."""
    if not isinstance(donnees, dict):
        raise ValueError("donnees doit être un dict nommant le cas")
    cas = donnees.get("cas")
    if not isinstance(cas, str):
        raise ValueError("donnees['cas'] (str) requis")
    cas = cas.upper()

    if cas == "CCC":
        a, b, c = _cle(donnees, "a"), _cle(donnees, "b"), _cle(donnees, "c")
        return [_complet(_cote(a), _cote(b), _cote(c))]

    if cas == "CAC":
        b, c, A = _cote(_cle(donnees, "b")), _cote(_cle(donnees, "c")), _angle(_cle(donnees, "A"))
        a = T.loi_cosinus(b, c, A)        # côté opposé à l'angle inclus A
        return [_complet(a, b, c)]

    if cas == "ACA":
        A, C, b = _angle(_cle(donnees, "A")), _angle(_cle(donnees, "C")), _cote(_cle(donnees, "b"))
        B = 180.0 - A - C
        if B <= 0.0:
            raise ValueError("somme des angles ≥ 180° : triangle impossible")
        a = loi_sinus(b, B, A)            # b opposé à B -> côté opposé à A
        c = loi_sinus(b, B, C)
        return [_complet(a, b, c)]

    if cas == "AAC":
        A, B, a = _angle(_cle(donnees, "A")), _angle(_cle(donnees, "B")), _cote(_cle(donnees, "a"))
        C = 180.0 - A - B
        if C <= 0.0:
            raise ValueError("somme des angles ≥ 180° : triangle impossible")
        b = loi_sinus(a, A, B)            # a opposé à A -> côté opposé à B
        c = loi_sinus(a, A, C)
        return [_complet(a, b, c)]

    if cas == "CCA":
        a, b, A = _cle(donnees, "a"), _cle(donnees, "b"), _cle(donnees, "A")
        return _resout_ssa(a, b, A)

    raise ValueError(f"cas inconnu : {cas!r} (attendu CCC/CAC/ACA/AAC/CCA)")


# ── VALEURS EXACTES DES ANGLES REMARQUABLES ──────────────────────────────────────────────────────────────────────
# sin des angles remarquables : Fraction pour un rationnel, (num, radicande, den) = num·√radicande/den pour un radical.
_SIN_EXACT = {
    0: Fraction(0, 1),        # sin 0  = 0
    30: Fraction(1, 2),       # sin 30 = 1/2                          (EXACT)
    45: (1, 2, 2),            # sin 45 = √2/2 = 1·√2/2                (EXACT)
    60: (1, 3, 2),            # sin 60 = √3/2 = 1·√3/2                (EXACT)
    90: Fraction(1, 1),       # sin 90 = 1                            (EXACT)
}


def sin_exact(angle_deg):
    """Valeur EXACTE de sin(angle_deg) pour 0/30/45/60/90° ; sinon valeur APPROCHÉE MARQUÉE.

    Rend :
      • une Fraction  (angle rationnel : 0, 30, 90) ;
      • un couple (num, radicande, den) signifiant num·√radicande/den  (45, 60) ;
      • pour tout autre angle : le couple (valeur_flottante, 'approchee') — APPROCHÉ, jamais présenté exact.
    Angle non numérique / bool / NaN / inf -> ValueError."""
    x = _reel(angle_deg)
    if x == int(x) and int(x) in _SIN_EXACT:
        return _SIN_EXACT[int(x)]
    return (T.sin_deg(x), "approchee")


if __name__ == "__main__":
    print("3-4-5 :", resout_triangle({"cas": "CCC", "a": 3, "b": 4, "c": 5}))
    print("loi_sinus(10,30,45) :", loi_sinus(10, 30, 45))
    print("SSA a=6,b=8,A=30 ->", len(resout_triangle({"cas": "CCA", "a": 6, "b": 8, "A": 30})), "solutions")
    print("aire Héron 3-4-5 :", aire_heron(3, 4, 5), "| aire sinus 3,4,90 :", aire_sinus(3, 4, 90))
    print("sin30 :", sin_exact(30), "| sin45 :", sin_exact(45), "| sin37 :", sin_exact(37))
