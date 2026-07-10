"""
COLORIMÉTRIE — conversions entre espaces de couleur, chaque espace NOMMÉ avec sa convention.

Même posture FAUX=0 que `physique` / `geometries_non_euclidiennes` (la NORME juge, jamais un faux) :
  • Le MÉCANISME est un ensemble de FORMULES NORMATIVES EXACTES, pas des approximations :
      – sRGB (IEC 61966-2-1), décodage :  c ≤ 0.04045 ? c/12.92 : ((c+0.055)/1.055)^2.4 — la VRAIE courbe
        à deux morceaux, PAS un gamma 2.2 approché ; encodage = branche inverse exacte
        (c ≤ 0.0031308 ? 12.92·c : 1.055·c^(1/2.4) − 0.055). NOTE HONNÊTE : au point de raccord, les
        constantes arrondies de la norme laissent un défaut connu ≈ 2·10⁻⁶ (0.04045/12.92 = 0.00313080495…
        ≠ 0.0031308) ; aucun canal 8 bits (k/255) ne tombe dans cette zone, la boucle fermée reste < 10⁻⁶.
      – sRGB linéaire → XYZ : matrice D65 standard (primaires IEC 61966-2-1, coefficients à 7 décimales,
        dérivation Lindbloom). L'inverse XYZ → linéaire est calculée EXACTEMENT (fractions.Fraction,
        règle de Cramer) à partir de la matrice directe : la boucle fermée est garantie par construction.
      – XYZ → CIE L*a*b* (CIE 15, illuminant D65 : Xn=95.047, Yn=100.0, Zn=108.883) :
        f(t) = t^(1/3) si t > (6/29)³, sinon t/(3·(6/29)²) + 4/29 ; L=116·f(Y/Yn)−16,
        a=500·(f(X/Xn)−f(Y/Yn)), b=200·(f(Y/Yn)−f(Z/Zn)). Inverse analytique exacte.
      – RGB ↔ HSV et RGB ↔ HSL : formules hexagonales exactes (max/min/chroma).
      – ΔE*76 = distance euclidienne dans L*a*b*. LIMITE CONNUE, DITE : CIE76 SOUS-ESTIME les écarts
        perçus dans les BLEUS saturés (non-uniformité perceptuelle de Lab ; CIE94 puis CIEDE2000
        corrigent ce biais). La valeur rendue est la définition CIE76, pas une mesure perceptuelle.
      – WCAG 2.1 : luminance relative L = 0.2126·R + 0.7152·G + 0.0722·B sur canaux LINÉARISÉS
        (seuil 0.04045 ; WCAG 2.0 écrivait 0.03928 — indistinguable sur des canaux 8 bits) ;
        contraste = (Lclair + 0.05) / (Lsombre + 0.05) ∈ [1, 21] ; AA texte normal ⇔ contraste ≥ 4.5.

CONVENTIONS D'API (documentées ici, vérifiées en adverse) :
  - Couleur RGB : triplet (liste/tuple) de réels dans [0, 255] (255 = canal saturé). Hors bornes → ValueError.
  - rgb_vers_lineaire / lineaire_vers_rgb : canal SCALAIRE dans [0, 1] → ValueError sinon.
  - XYZ : échelle « blanc Y=100 » ; bornes de garde X∈[0,300], Y∈[0,100.001], Z∈[0,300] (Y>100 = plus
    lumineux que le blanc de référence → abstention). XYZ hors du gamut sRGB → xyz_vers_rgb ABSTIENT.
  - L*a*b* : L∈[0, 100.001] (tolérance 10⁻³ : la ligne Y de la matrice somme à 1.0000001), a,b∈[−300,300].
  - HSV/HSL : H∈[0, 360) strict, S/V/L∈[0, 1]. Les GRIS (max=min) ont une teinte indéfinie en théorie ;
    CONVENTION documentée : H=0 et S=0.
  - Les sorties flottantes sont ARRONDIES à 12 chiffres significatifs — précision honnête, dite ici
    (entrées flottantes, matrices normatives à 7 décimales : on ne prétend pas à l'exactitude au-delà).

GARANTIES (vérifiées en adverse par `valide_colorimetrie.py`) :
  - blanc (255,255,255) → XYZ = l'illuminant D65 lui-même (95.047, 100.0, 108.883) ; blanc → Lab (100,0,0) ;
    noir → Lab (0,0,0) ; rouge pur → Lab ≈ (53.24, 80.09, 67.20) (valeurs tabulées) ;
  - boucle fermée rgb → xyz → lab → xyz → rgb < 10⁻⁶ sur 200 couleurs déterministes ;
  - noir sur blanc = contraste 21.0 EXACTEMENT ; couleur sur elle-même = 1.0 ;
  - types invalides (bool, str, NaN, ±inf, mauvaise arité, hors bornes) → ValueError ;
  - fonctions PURES et déterministes ; conservateur (abstention tolérée, faux POSITIF interdit).

Le module n'importe que `math` et `fractions` (stdlib).
"""
from __future__ import annotations

import math
from fractions import Fraction

SOURCE = ("IEC 61966-2-1 (courbe et primaires sRGB) ; CIE 15 (XYZ, L*a*b*, ΔE*76) ; "
          "illuminant D65 Xn=95.047 Yn=100.0 Zn=108.883 (CIE, observateur 2°) ; "
          "WCAG 2.1 §relative luminance / contrast ratio (W3C)")

# Blanc de référence D65 (CIE, observateur 2°) — constantes NORMATIVES, pas calculées ici.
XN = 95.047
YN = 100.0
ZN = 108.883

_CHIFFRES_SIGNIFICATIFS = 12   # précision honnête des sorties flottantes (dit dans la docstring)
_EPS_NUM = 1e-9                # tolérance numérique de raccord (clamp documenté, jamais au-delà)
_DELTA = 6.0 / 29.0            # constante de la fonction f de CIELAB (CIE 15)

# Matrice sRGB linéaire (D65) -> XYZ, coefficients standards à 7 décimales (dérivation Lindbloom des
# primaires IEC 61966-2-1). Texte -> Fraction pour inverser EXACTEMENT (règle de Cramer).
_M_TXT = (("0.4124564", "0.3575761", "0.1804375"),
          ("0.2126729", "0.7151522", "0.0721750"),
          ("0.0193339", "0.1191920", "0.9503041"))

# Coefficients de luminance relative WCAG (normatifs, cités tels quels par WCAG 2.x).
_WCAG_R, _WCAG_G, _WCAG_B = 0.2126, 0.7152, 0.0722


def _inverse_exacte_3x3(M):
    """Inverse EXACTE (Fraction) d'une matrice 3×3 par la règle de Cramer."""
    a, b, c = M[0]
    d, e, f = M[1]
    g, h, i = M[2]
    det = a * (e * i - f * h) - b * (d * i - f * g) + c * (d * h - e * g)
    if det == 0:
        raise ValueError("matrice non inversible")
    adj = ((e * i - f * h, c * h - b * i, b * f - c * e),
           (f * g - d * i, a * i - c * g, c * d - a * f),
           (d * h - e * g, b * g - a * h, a * e - b * d))
    return tuple(tuple(x / det for x in ligne) for ligne in adj)


_M_FRAC = tuple(tuple(Fraction(x) for x in ligne) for ligne in _M_TXT)
_M = tuple(tuple(float(x) for x in ligne) for ligne in _M_FRAC)
_M_INV = tuple(tuple(float(x) for x in ligne) for ligne in _inverse_exacte_3x3(_M_FRAC))


def _sig(x: float, n: int = _CHIFFRES_SIGNIFICATIFS) -> float:
    """Arrondit à n chiffres significatifs (précision honnête, indépendante de la magnitude)."""
    if x == 0:
        return 0.0
    return float(f"{x:.{n}g}")


def _est_reel(x) -> bool:
    """True ssi x est un réel fini (les bool sont REFUSÉS : True n'est pas une mesure)."""
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x)


def _exige_triplet(t, nom: str):
    if not isinstance(t, (list, tuple)) or len(t) != 3:
        raise ValueError(f"{nom} invalide : un triplet (liste/tuple de 3 réels) est requis")
    return t


def _exige_rgb(rgb):
    """Triplet RGB : réels dans [0, 255]. bool/str/NaN/inf/hors bornes -> ValueError."""
    t = _exige_triplet(rgb, "rgb")
    for c in t:
        if not _est_reel(c) or not (0.0 <= c <= 255.0):
            raise ValueError("composante RGB invalide : un réel dans [0, 255] est requis")
    return tuple(float(c) for c in t)


def _exige_xyz(xyz):
    """Triplet XYZ (échelle blanc Y=100) : X∈[0,300], Y∈[0,100.001], Z∈[0,300] (bornes de garde)."""
    t = _exige_triplet(xyz, "xyz")
    X, Y, Z = t
    for v in t:
        if not _est_reel(v):
            raise ValueError("composante XYZ invalide : un réel fini est requis")
    if not (0.0 <= X <= 300.0) or not (0.0 <= Z <= 300.0):
        raise ValueError("composante XYZ hors bornes de garde : X et Z doivent être dans [0, 300]")
    if not (0.0 <= Y <= 100.0 + 1e-3):
        raise ValueError("Y hors [0, 100] : luminance au-delà du blanc de référence -> abstention")
    return float(X), float(Y), float(Z)


def _exige_lab(lab):
    """Triplet L*a*b* : L∈[0, 100.001] (tolérance documentée), a et b réels dans [−300, 300]."""
    t = _exige_triplet(lab, "lab")
    L, a, b = t
    for v in t:
        if not _est_reel(v):
            raise ValueError("composante Lab invalide : un réel fini est requis")
    if not (0.0 <= L <= 100.0 + 1e-3):
        raise ValueError("L* hors [0, 100] : clarté CIELAB mal posée -> abstention")
    if not (-300.0 <= a <= 300.0) or not (-300.0 <= b <= 300.0):
        raise ValueError("a*/b* hors [-300, 300] (borne de garde, le gamut réel est bien plus étroit)")
    return float(L), float(a), float(b)


def _exige_01(x, nom: str) -> float:
    if not _est_reel(x) or not (0.0 <= x <= 1.0):
        raise ValueError(f"{nom} invalide : un réel dans [0, 1] est requis")
    return float(x)


def _exige_teinte(h) -> float:
    """Teinte H : réel dans [0, 360) STRICT (360 exclu : la teinte est circulaire, 360 ≡ 0)."""
    if not _est_reel(h) or not (0.0 <= h < 360.0):
        raise ValueError("teinte invalide : un réel dans [0, 360) est requis (360 est exclu)")
    return float(h)


# ── COURBE sRGB (IEC 61966-2-1) — les deux branches EXACTES, pas un gamma 2.2 ─────────────────────────────────
def _lin(c: float) -> float:
    """Décodage sRGB -> linéaire, canal dans [0,1], SANS arrondi (usage interne)."""
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def _delin(c: float) -> float:
    """Encodage linéaire -> sRGB, canal dans [0,1], SANS arrondi (usage interne)."""
    return 12.92 * c if c <= 0.0031308 else 1.055 * c ** (1.0 / 2.4) - 0.055


def rgb_vers_lineaire(c: float) -> float:
    """Décodage sRGB (IEC 61966-2-1) : canal encodé c∈[0,1] -> canal linéaire.

    c ≤ 0.04045 ? c/12.92 : ((c+0.055)/1.055)^2.4 — la vraie courbe, PAS un gamma 2.2 approché."""
    return _sig(_lin(_exige_01(c, "canal sRGB")))


def lineaire_vers_rgb(c: float) -> float:
    """Encodage sRGB (IEC 61966-2-1) : canal linéaire c∈[0,1] -> canal encodé.

    c ≤ 0.0031308 ? 12.92·c : 1.055·c^(1/2.4) − 0.055 (branche inverse exacte)."""
    return _sig(_delin(_exige_01(c, "canal linéaire")))


# ── sRGB <-> XYZ (matrice D65 standard, inverse EXACTE par Cramer) ────────────────────────────────────────────
def rgb_vers_xyz(rgb):
    """sRGB (triplet [0,255]) -> XYZ D65 (échelle blanc Y=100). Blanc -> (95.047, 100.0, 108.883)."""
    r, g, b = (_lin(c / 255.0) for c in _exige_rgb(rgb))
    X = (_M[0][0] * r + _M[0][1] * g + _M[0][2] * b) * 100.0
    Y = (_M[1][0] * r + _M[1][1] * g + _M[1][2] * b) * 100.0
    Z = (_M[2][0] * r + _M[2][1] * g + _M[2][2] * b) * 100.0
    return (_sig(X), _sig(Y), _sig(Z))


def xyz_vers_rgb(xyz):
    """XYZ D65 (échelle blanc Y=100) -> sRGB (triplet [0,255]).

    ABSTENTION (ValueError) si la couleur est HORS GAMUT sRGB : composante linéaire hors [0,1] au-delà
    de la tolérance numérique 1e-9 (clamp documenté). Jamais un écrêtage silencieux."""
    X, Y, Z = _exige_xyz(xyz)
    x, y, z = X / 100.0, Y / 100.0, Z / 100.0
    sortie = []
    for ligne in _M_INV:
        v = ligne[0] * x + ligne[1] * y + ligne[2] * z
        if -_EPS_NUM <= v < 0.0:
            v = 0.0
        elif 1.0 < v <= 1.0 + _EPS_NUM:
            v = 1.0
        if not (0.0 <= v <= 1.0):
            raise ValueError("couleur hors gamut sRGB : composante linéaire hors [0,1] -> abstention")
        sortie.append(_sig(255.0 * _delin(v)))
    return tuple(sortie)


# ── XYZ <-> CIE L*a*b* (illuminant D65, CIE 15) ───────────────────────────────────────────────────────────────
def _f_lab(t: float) -> float:
    """f(t) de CIELAB : t^(1/3) si t > (6/29)³, sinon t/(3·(6/29)²) + 4/29."""
    return t ** (1.0 / 3.0) if t > _DELTA ** 3 else t / (3.0 * _DELTA * _DELTA) + 4.0 / 29.0


def _f_lab_inv(u: float) -> float:
    """Inverse analytique exacte de f : u³ si u > 6/29, sinon 3·(6/29)²·(u − 4/29)."""
    return u ** 3 if u > _DELTA else 3.0 * _DELTA * _DELTA * (u - 4.0 / 29.0)


def xyz_vers_lab(xyz):
    """XYZ D65 (blanc Y=100) -> CIE L*a*b* (Xn=95.047, Yn=100.0, Zn=108.883)."""
    X, Y, Z = _exige_xyz(xyz)
    fx, fy, fz = _f_lab(X / XN), _f_lab(Y / YN), _f_lab(Z / ZN)
    L = 116.0 * fy - 16.0
    if -_EPS_NUM < L < 0.0:   # noir : 116·(4/29)−16 peut rendre −1 ulp, clamp numérique documenté
        L = 0.0
    return (_sig(L), _sig(500.0 * (fx - fy)), _sig(200.0 * (fy - fz)))


def lab_vers_xyz(lab):
    """CIE L*a*b* -> XYZ D65 (blanc Y=100), inverse analytique exacte.

    ABSTENTION si le Lab demandé sort du domaine physique (composante XYZ négative)."""
    L, a, b = _exige_lab(lab)
    fy = (L + 16.0) / 116.0
    fx = fy + a / 500.0
    fz = fy - b / 200.0
    sortie = []
    for u, n in ((fx, XN), (fy, YN), (fz, ZN)):
        v = _f_lab_inv(u) * n
        if -_EPS_NUM <= v < 0.0:
            v = 0.0
        if v < 0.0:
            raise ValueError("Lab hors du domaine physique : composante XYZ négative -> abstention")
        sortie.append(_sig(v))
    return tuple(sortie)


def rgb_vers_lab(rgb):
    """sRGB (triplet [0,255]) -> CIE L*a*b* D65 (composition rgb->xyz->lab)."""
    return xyz_vers_lab(rgb_vers_xyz(rgb))


def lab_vers_rgb(lab):
    """CIE L*a*b* D65 -> sRGB (triplet [0,255]). Hors gamut sRGB -> ValueError (abstention)."""
    return xyz_vers_rgb(lab_vers_xyz(lab))


# ── RGB <-> HSV et RGB <-> HSL (formules hexagonales exactes) ─────────────────────────────────────────────────
def _teinte_hexagonale(r: float, g: float, b: float, mx: float, d: float) -> float:
    """Teinte H∈[0,360) du modèle hexagonal. CONVENTION documentée : H=0 pour les gris (d=0)."""
    if d == 0.0:
        return 0.0
    if mx == r:
        h = 60.0 * (((g - b) / d) % 6.0)
    elif mx == g:
        h = 60.0 * ((b - r) / d + 2.0)
    else:
        h = 60.0 * ((r - g) / d + 4.0)
    h = _sig(h)
    return 0.0 if h >= 360.0 else h   # 360 ≡ 0 (teinte circulaire) : jamais de sortie hors [0,360)


def _secteur_vers_rgb01(h: float, c: float, x: float):
    """(c,x) -> triplet RGB [0,1] sans décalage m, selon le secteur hexagonal de H."""
    return ((c, x, 0.0), (x, c, 0.0), (0.0, c, x),
            (0.0, x, c), (x, 0.0, c), (c, 0.0, x))[int(h // 60.0)]


def rgb_vers_hsv(rgb):
    """sRGB (triplet [0,255]) -> HSV : H∈[0,360), S∈[0,1], V∈[0,1]. Gris -> H=0, S=0 (convention)."""
    r, g, b = (c / 255.0 for c in _exige_rgb(rgb))
    mx, mn = max(r, g, b), min(r, g, b)
    d = mx - mn
    h = _teinte_hexagonale(r, g, b, mx, d)
    s = 0.0 if mx == 0.0 else d / mx
    return (h, _sig(s), _sig(mx))


def hsv_vers_rgb(hsv):
    """HSV (H∈[0,360), S,V∈[0,1]) -> sRGB (triplet [0,255])."""
    t = _exige_triplet(hsv, "hsv")
    h = _exige_teinte(t[0])
    s = _exige_01(t[1], "saturation")
    v = _exige_01(t[2], "valeur")
    c = v * s
    x = c * (1.0 - abs((h / 60.0) % 2.0 - 1.0))
    m = v - c
    return tuple(_sig(255.0 * (u + m)) for u in _secteur_vers_rgb01(h, c, x))


def rgb_vers_hsl(rgb):
    """sRGB (triplet [0,255]) -> HSL : H∈[0,360), S∈[0,1], L∈[0,1]. Gris -> H=0, S=0 (convention)."""
    r, g, b = (c / 255.0 for c in _exige_rgb(rgb))
    mx, mn = max(r, g, b), min(r, g, b)
    d = mx - mn
    h = _teinte_hexagonale(r, g, b, mx, d)
    l = (mx + mn) / 2.0
    s = 0.0 if d == 0.0 else min(d / (1.0 - abs(2.0 * l - 1.0)), 1.0)   # min() : garde numérique (s ≤ 1)
    return (h, _sig(s), _sig(l))


def hsl_vers_rgb(hsl):
    """HSL (H∈[0,360), S,L∈[0,1]) -> sRGB (triplet [0,255])."""
    t = _exige_triplet(hsl, "hsl")
    h = _exige_teinte(t[0])
    s = _exige_01(t[1], "saturation")
    l = _exige_01(t[2], "clarté")
    c = (1.0 - abs(2.0 * l - 1.0)) * s
    x = c * (1.0 - abs((h / 60.0) % 2.0 - 1.0))
    m = l - c / 2.0
    return tuple(_sig(255.0 * (u + m)) for u in _secteur_vers_rgb01(h, c, x))


# ── ÉCART DE COULEUR ΔE*76 ────────────────────────────────────────────────────────────────────────────────────
def delta_e_76(lab1, lab2) -> float:
    """ΔE*76 = distance euclidienne dans CIE L*a*b* (CIE 1976).

    LIMITE CONNUE (dite, pas cachée) : CIE76 SOUS-ESTIME les écarts perçus dans les BLEUS saturés
    (Lab n'est pas parfaitement uniforme perceptuellement ; CIE94/CIEDE2000 corrigent). La valeur
    rendue est la définition CIE76 exacte, pas une mesure perceptuelle."""
    L1, a1, b1 = _exige_lab(lab1)
    L2, a2, b2 = _exige_lab(lab2)
    return _sig(math.sqrt((L1 - L2) ** 2 + (a1 - a2) ** 2 + (b1 - b2) ** 2))


# ── WCAG 2.1 : luminance relative, contraste, seuil AA ────────────────────────────────────────────────────────
def luminance_relative(rgb) -> float:
    """Luminance relative WCAG 2.1 : L = 0.2126·R + 0.7152·G + 0.0722·B sur canaux linéarisés.

    Blanc -> 1.0, noir -> 0.0. Seuil de linéarisation 0.04045 (WCAG 2.1/IEC ; le 0.03928 de WCAG 2.0
    est indistinguable sur des canaux 8 bits)."""
    r, g, b = (_lin(c / 255.0) for c in _exige_rgb(rgb))
    return _sig(_WCAG_R * r + _WCAG_G * g + _WCAG_B * b)


def contraste_wcag(rgb1, rgb2) -> float:
    """Contraste WCAG = (Lclair + 0.05) / (Lsombre + 0.05) ∈ [1, 21] (symétrique : l'ordre est trié).

    Noir sur blanc = 21.0 exactement ; une couleur avec elle-même = 1.0."""
    l1 = luminance_relative(rgb1)
    l2 = luminance_relative(rgb2)
    clair, sombre = max(l1, l2), min(l1, l2)
    return _sig((clair + 0.05) / (sombre + 0.05))


def conforme_wcag_aa(contraste) -> bool:
    """True ssi le contraste satisfait WCAG AA texte normal : contraste ≥ 4.5.

    `contraste` = ratio WCAG, réel dans [1, 21] (domaine du contraste) -> ValueError sinon."""
    if not _est_reel(contraste) or not (1.0 <= contraste <= 21.0):
        raise ValueError("contraste invalide : un réel dans [1, 21] est requis (ratio WCAG)")
    return float(contraste) >= 4.5
