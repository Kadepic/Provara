"""
VALIDE colorimetrie.py — held-out ADVERSE.

ANCRES EXTERNES NON CIRCULAIRES (valeurs connues, PAS recalculées par les formules testées) :
  • Blanc sRGB (255,255,255) -> XYZ = l'ILLUMINANT D65 LUI-MÊME (95.047, 100.0, 108.883) : constante
    CIE mesurée, indépendante de la matrice testée (c'est elle qui a servi à NORMALISER la matrice).
  • Blanc -> Lab (100, 0, 0) et noir -> Lab (0, 0, 0) : définition même de l'échelle L* (le blanc de
    référence vaut 100, le noir 0) — pas un calcul du module.
  • Rouge pur (255,0,0) -> Lab ≈ (53.24, 80.09, 67.20) ±0.05 ; vert (87.73, −86.18, 83.18) ;
    bleu (32.30, 79.19, −107.86) : valeurs UNIVERSELLEMENT TABULÉES (littérature colorimétrique).
  • Rouge pur -> XYZ ≈ (41.246, 21.267, 1.933) : coordonnées tabulées du primaire rouge sRGB.
  • Courbe sRGB : 0.5 -> 0.2140411 et 128/255 -> 0.2158605 (valeurs tabulées de la norme) ;
    0.04045 -> 0.04045/12.92 (division écrite À LA MAIN ici, ancre de la branche linéaire).
  • Luminance WCAG : blanc=1.0, noir=0.0, rouge=0.2126 (le coefficient normatif lui-même, canal
    linéaire = 1 exactement). Contraste noir/blanc = (1+0.05)/(0+0.05) = 21.0 EXACTEMENT (calcul à la
    main, ancre normative WCAG). Rouge sur noir = 0.2626/0.05 = 5.252 (calcul à la main).
  • ΔE*76 : labs (50,0,0) et (50,3,4) -> distance 5.0 (triangle 3-4-5, arithmétique de collège).
  • HSV/HSL : rouge pur -> H=0,S=1,V=1 (définition du modèle) ; gris (128,128,128) -> S=0, V=128/255
    (division écrite à la main) ; jaune H=60, cyan H=180, bleu H=240, magenta H=300 (hexagone HSV).
  • BOUCLE FERMÉE : rgb -> xyz -> lab -> xyz -> rgb < 1e-6 sur 200 couleurs déterministes (l'identité
    est l'ancre : aucune valeur du module n'est comparée à elle-même, mais à l'ENTRÉE d'origine).

SOUNDNESS : bool/str/NaN/inf, composante hors [0,255] ou [0,1], teinte hors [0,360), XYZ/Lab hors
bornes, mauvaise arité, hors gamut sRGB -> ValueError. DÉTERMINISME : double appel identique.
"""
import math

import colorimetrie as C

ok = 0
ko = 0


def check(cond, label):
    global ok, ko
    if cond:
        ok += 1
    else:
        ko += 1
        print(f"  FAIL: {label}")


def leve(fn, *a):
    """True ssi fn(*a) lève ValueError (abstention structurelle)."""
    try:
        fn(*a)
        return False
    except ValueError:
        return True


def proche(x, attendu, tol=1e-6):
    return x is not None and abs(x - attendu) <= tol


def triplet_proche(t, attendu, tol=1e-6):
    return all(abs(a - b) <= tol for a, b in zip(t, attendu))


BLANC = (255, 255, 255)
NOIR = (0, 0, 0)
ROUGE = (255, 0, 0)
VERT = (0, 255, 0)
BLEU = (0, 0, 255)

# ── 1) ANCRE D65 : blanc sRGB -> XYZ = l'illuminant lui-même (95.047, 100.0, 108.883) ──
Xb, Yb, Zb = C.rgb_vers_xyz(BLANC)
check(proche(Xb, 95.047, 1e-3), f"blanc -> X = 95.047 (D65), obtenu {Xb}")
check(proche(Yb, 100.0, 1e-3), f"blanc -> Y = 100.0 (D65), obtenu {Yb}")
check(proche(Zb, 108.883, 1e-3), f"blanc -> Z = 108.883 (D65), obtenu {Zb}")

# ── 2) ÉCHELLE L* : blanc -> Lab (100,0,0), noir -> Lab (0,0,0) (définition de l'échelle) ──
Lb, ab, bb = C.rgb_vers_lab(BLANC)
check(proche(Lb, 100.0, 1e-4), f"blanc -> L* = 100, obtenu {Lb}")
check(proche(ab, 0.0, 1e-4), f"blanc -> a* = 0, obtenu {ab}")
check(proche(bb, 0.0, 1e-4), f"blanc -> b* = 0, obtenu {bb}")
Ln, an, bn = C.rgb_vers_lab(NOIR)
check(proche(Ln, 0.0, 1e-9), f"noir -> L* = 0, obtenu {Ln}")
check(proche(an, 0.0, 1e-9), f"noir -> a* = 0, obtenu {an}")
check(proche(bn, 0.0, 1e-9), f"noir -> b* = 0, obtenu {bn}")

# ── 3) VALEURS TABULÉES (littérature) : Lab des primaires sRGB, ±0.05 ──
Lr, ar, br = C.rgb_vers_lab(ROUGE)
check(proche(Lr, 53.24, 0.05), f"rouge -> L* ≈ 53.24, obtenu {Lr}")
check(proche(ar, 80.09, 0.05), f"rouge -> a* ≈ 80.09, obtenu {ar}")
check(proche(br, 67.20, 0.05), f"rouge -> b* ≈ 67.20, obtenu {br}")
Lg, ag, bg = C.rgb_vers_lab(VERT)
check(proche(Lg, 87.73, 0.05), f"vert -> L* ≈ 87.73, obtenu {Lg}")
check(proche(ag, -86.18, 0.05), f"vert -> a* ≈ -86.18, obtenu {ag}")
check(proche(bg, 83.18, 0.05), f"vert -> b* ≈ 83.18, obtenu {bg}")
Lz, az, bz = C.rgb_vers_lab(BLEU)
check(proche(Lz, 32.30, 0.05), f"bleu -> L* ≈ 32.30, obtenu {Lz}")
check(proche(az, 79.19, 0.05), f"bleu -> a* ≈ 79.19, obtenu {az}")
check(proche(bz, -107.86, 0.05), f"bleu -> b* ≈ -107.86, obtenu {bz}")

# XYZ tabulé du primaire rouge sRGB
Xr, Yr, Zr = C.rgb_vers_xyz(ROUGE)
check(proche(Xr, 41.246, 1e-2), f"rouge -> X ≈ 41.246, obtenu {Xr}")
check(proche(Yr, 21.267, 1e-2), f"rouge -> Y ≈ 21.267, obtenu {Yr}")
check(proche(Zr, 1.933, 1e-2), f"rouge -> Z ≈ 1.933, obtenu {Zr}")

# ── 4) COURBE sRGB (IEC 61966-2-1) — ancres tabulées + calculs à la main ──
check(C.rgb_vers_lineaire(0.0) == 0.0, "linéarisation : 0 -> 0")
check(C.rgb_vers_lineaire(1.0) == 1.0, "linéarisation : 1 -> 1")
# 0.04045/12.92 = 0.0031308049535... (division à la main : branche linéaire au seuil exact)
check(proche(C.rgb_vers_lineaire(0.04045), 0.04045 / 12.92, 1e-12), "linéarisation au seuil 0.04045")
# valeur tabulée de la norme : sRGB 0.5 -> linéaire 0.2140411 (PAS 0.5^2.2=0.2176 : gamma 2.2 réfuté)
check(proche(C.rgb_vers_lineaire(0.5), 0.2140411, 1e-6), "linéarisation 0.5 -> 0.2140411 (tabulé)")
check(not proche(C.rgb_vers_lineaire(0.5), 0.5 ** 2.2, 1e-3), "la courbe N'EST PAS le gamma 2.2 approché")
# valeur tabulée : canal 128 (=128/255) -> 0.2158605
check(proche(C.rgb_vers_lineaire(128 / 255), 0.2158605, 1e-5), "linéarisation 128/255 -> 0.2158605 (tabulé)")
# encodage : 12.92 × 0.0031308 = 0.040449936 (multiplication à la main, branche linéaire)
check(proche(C.lineaire_vers_rgb(0.0031308), 12.92 * 0.0031308, 1e-12), "encodage au seuil 0.0031308")
# aller-retour du canal (hors zone de raccord) : décodage puis encodage = identité
check(proche(C.lineaire_vers_rgb(C.rgb_vers_lineaire(0.7)), 0.7, 1e-9), "canal 0.7 : aller-retour identité")
check(proche(C.rgb_vers_lineaire(C.lineaire_vers_rgb(0.3)), 0.3, 1e-9), "canal 0.3 : retour-aller identité")

# ── 5) BOUCLE FERMÉE rgb -> xyz -> lab -> xyz -> rgb sur 200 couleurs déterministes ──
couleurs = [((i * 37) % 256, (i * 73 + 11) % 256, (i * 97 + 5) % 256) for i in range(200)]
err_max = 0.0
echecs = 0
for rgb in couleurs:
    try:
        xyz = C.rgb_vers_xyz(rgb)
        lab = C.xyz_vers_lab(xyz)
        xyz2 = C.lab_vers_xyz(lab)
        rgb2 = C.xyz_vers_rgb(xyz2)
        err_max = max(err_max, max(abs(u - v) for u, v in zip(rgb, rgb2)))
    except ValueError:
        echecs += 1
check(echecs == 0, f"boucle fermée : aucune abstention indue sur 200 couleurs ({echecs} échecs)")
check(err_max <= 1e-6, f"boucle fermée rgb->xyz->lab->xyz->rgb < 1e-6 (err_max={err_max:.3e})")

# ── 6) HSV — ancres de définition du modèle hexagonal ──
h, s, v = C.rgb_vers_hsv(ROUGE)
check(h == 0.0 and proche(s, 1.0, 1e-12) and proche(v, 1.0, 1e-12), f"rouge -> HSV (0,1,1), obtenu {(h, s, v)}")
hg, sg, vg = C.rgb_vers_hsv((128, 128, 128))
check(sg == 0.0, f"gris 128 -> S = 0, obtenu {sg}")
check(hg == 0.0, f"gris 128 -> H = 0 (convention documentée), obtenu {hg}")
check(proche(vg, 128 / 255, 1e-9), f"gris 128 -> V = 128/255, obtenu {vg}")
check(proche(C.rgb_vers_hsv((255, 255, 0))[0], 60.0, 1e-9), "jaune -> H = 60")
check(proche(C.rgb_vers_hsv((0, 255, 255))[0], 180.0, 1e-9), "cyan -> H = 180")
check(proche(C.rgb_vers_hsv(BLEU)[0], 240.0, 1e-9), "bleu -> H = 240")
check(proche(C.rgb_vers_hsv((255, 0, 255))[0], 300.0, 1e-9), "magenta -> H = 300")
check(triplet_proche(C.hsv_vers_rgb((0.0, 1.0, 1.0)), (255.0, 0.0, 0.0), 1e-9), "HSV (0,1,1) -> rouge pur")
check(triplet_proche(C.hsv_vers_rgb((240.0, 1.0, 1.0)), (0.0, 0.0, 255.0), 1e-9), "HSV (240,1,1) -> bleu pur")
# boucle fermée HSV sur les 200 couleurs
err_hsv = max(max(abs(u - v) for u, v in zip(rgb, C.hsv_vers_rgb(C.rgb_vers_hsv(rgb))))
              for rgb in couleurs)
check(err_hsv <= 1e-6, f"boucle fermée rgb->hsv->rgb < 1e-6 (err_max={err_hsv:.3e})")

# ── 7) HSL — ancres de définition ──
hl, sl, ll = C.rgb_vers_hsl(ROUGE)
check(hl == 0.0 and proche(sl, 1.0, 1e-12) and proche(ll, 0.5, 1e-12), f"rouge -> HSL (0,1,0.5), obtenu {(hl, sl, ll)}")
hb2, sb2, lb2 = C.rgb_vers_hsl(BLANC)
check(sb2 == 0.0 and proche(lb2, 1.0, 1e-12), f"blanc -> HSL S=0, L=1, obtenu {(sb2, lb2)}")
check(C.rgb_vers_hsl(NOIR)[2] == 0.0, "noir -> HSL L = 0")
check(triplet_proche(C.hsl_vers_rgb((0.0, 1.0, 0.5)), (255.0, 0.0, 0.0), 1e-9), "HSL (0,1,0.5) -> rouge pur")
err_hsl = max(max(abs(u - v) for u, v in zip(rgb, C.hsl_vers_rgb(C.rgb_vers_hsl(rgb))))
              for rgb in couleurs)
check(err_hsl <= 1e-6, f"boucle fermée rgb->hsl->rgb < 1e-6 (err_max={err_hsl:.3e})")

# ── 8) ΔE*76 — ancre arithmétique (triangle 3-4-5) + propriétés métriques ──
check(C.delta_e_76((50.0, 0.0, 0.0), (50.0, 0.0, 0.0)) == 0.0, "ΔE(identiques) = 0")
check(proche(C.delta_e_76((50.0, 0.0, 0.0), (50.0, 3.0, 4.0)), 5.0, 1e-12), "ΔE 3-4-5 = 5 (Pythagore à la main)")
check(C.delta_e_76((50.0, 0.0, 0.0), (50.0, 3.0, 4.0))
      == C.delta_e_76((50.0, 3.0, 4.0), (50.0, 0.0, 0.0)), "ΔE symétrique")
# ΔE blanc-noir = 100 exactement (seul L diffère : 100-0)
check(proche(C.delta_e_76(C.rgb_vers_lab(BLANC), C.rgb_vers_lab(NOIR)), 100.0, 1e-3), "ΔE(blanc, noir) = 100")

# ── 9) WCAG — luminance relative (coefficients normatifs comme ancres) ──
check(C.luminance_relative(BLANC) == 1.0, "luminance blanc = 1.0")
check(C.luminance_relative(NOIR) == 0.0, "luminance noir = 0.0")
check(proche(C.luminance_relative(ROUGE), 0.2126, 1e-12), "luminance rouge = 0.2126 (coefficient normatif)")
check(proche(C.luminance_relative(VERT), 0.7152, 1e-12), "luminance vert = 0.7152 (coefficient normatif)")
check(proche(C.luminance_relative(BLEU), 0.0722, 1e-12), "luminance bleu = 0.0722 (coefficient normatif)")

# ── 10) WCAG — contraste : noir sur blanc = 21.0 EXACTEMENT (ancre normative, (1+0.05)/(0+0.05)) ──
check(C.contraste_wcag(NOIR, BLANC) == 21.0, f"contraste noir/blanc = 21.0 EXACT, obtenu {C.contraste_wcag(NOIR, BLANC)}")
check(C.contraste_wcag(BLANC, NOIR) == 21.0, "contraste symétrique (ordre trié)")
check(C.contraste_wcag(ROUGE, ROUGE) == 1.0, "contraste d'une couleur avec elle-même = 1.0")
# rouge sur noir : (0.2126+0.05)/0.05 = 0.2626/0.05 = 5.252 (division à la main)
check(proche(C.contraste_wcag(ROUGE, NOIR), 5.252, 1e-9), "contraste rouge/noir = 5.252 (main)")
check(C.conforme_wcag_aa(21.0) is True, "AA : 21 conforme")
check(C.conforme_wcag_aa(4.5) is True, "AA : 4.5 conforme (seuil inclus)")
check(C.conforme_wcag_aa(4.499) is False, "AA : 4.499 non conforme")
check(C.conforme_wcag_aa(1.0) is False, "AA : 1.0 non conforme")

# ── 11) SOUNDNESS — RGB hors bornes / types ──
check(leve(C.rgb_vers_xyz, (256, 0, 0)), "rgb 256 -> ValueError")
check(leve(C.rgb_vers_xyz, (-1, 0, 0)), "rgb -1 -> ValueError")
check(leve(C.rgb_vers_xyz, (True, 0, 0)), "rgb bool -> ValueError")
check(leve(C.rgb_vers_xyz, ("255", 0, 0)), "rgb str -> ValueError")
check(leve(C.rgb_vers_xyz, (float("nan"), 0, 0)), "rgb NaN -> ValueError")
check(leve(C.rgb_vers_xyz, (float("inf"), 0, 0)), "rgb inf -> ValueError")
check(leve(C.rgb_vers_xyz, (0, 0)), "rgb arité 2 -> ValueError")
check(leve(C.rgb_vers_xyz, (0, 0, 0, 0)), "rgb arité 4 -> ValueError")
check(leve(C.rgb_vers_xyz, 128), "rgb non-triplet -> ValueError")
check(leve(C.luminance_relative, (0, 0, 300)), "luminance rgb hors bornes -> ValueError")
check(leve(C.contraste_wcag, (0, 0, 0), (0, 0, "x")), "contraste rgb str -> ValueError")

# ── 12) SOUNDNESS — canal scalaire hors [0,1] / types ──
check(leve(C.rgb_vers_lineaire, 1.5), "canal 1.5 -> ValueError")
check(leve(C.rgb_vers_lineaire, -0.1), "canal -0.1 -> ValueError")
check(leve(C.rgb_vers_lineaire, True), "canal bool -> ValueError")
check(leve(C.rgb_vers_lineaire, "0.5"), "canal str -> ValueError")
check(leve(C.rgb_vers_lineaire, float("nan")), "canal NaN -> ValueError")
check(leve(C.lineaire_vers_rgb, float("inf")), "canal inf -> ValueError")
check(leve(C.lineaire_vers_rgb, 255), "canal 255 (échelle [0,1] documentée) -> ValueError")

# ── 13) SOUNDNESS — teinte hors [0,360) et S/V/L hors [0,1] ──
check(leve(C.hsv_vers_rgb, (360.0, 1.0, 1.0)), "teinte 360 (exclue) -> ValueError")
check(leve(C.hsv_vers_rgb, (-1.0, 1.0, 1.0)), "teinte -1 -> ValueError")
check(leve(C.hsv_vers_rgb, (0.0, 1.1, 1.0)), "saturation 1.1 -> ValueError")
check(leve(C.hsv_vers_rgb, (0.0, 1.0, -0.1)), "valeur -0.1 -> ValueError")
check(leve(C.hsv_vers_rgb, (float("nan"), 1.0, 1.0)), "teinte NaN -> ValueError")
check(leve(C.hsv_vers_rgb, (True, 1.0, 1.0)), "teinte bool -> ValueError")
check(leve(C.hsl_vers_rgb, (400.0, 0.5, 0.5)), "HSL teinte 400 -> ValueError")
check(leve(C.hsl_vers_rgb, (0.0, 0.5, 2.0)), "HSL clarté 2 -> ValueError")
check(leve(C.hsl_vers_rgb, (0.0, 0.5)), "HSL arité 2 -> ValueError")

# ── 14) SOUNDNESS — XYZ / Lab hors bornes, hors gamut ──
check(leve(C.xyz_vers_lab, (-1.0, 50.0, 50.0)), "X négatif -> ValueError")
check(leve(C.xyz_vers_lab, (50.0, 150.0, 50.0)), "Y > 100 -> ValueError (abstention)")
check(leve(C.xyz_vers_rgb, (float("inf"), 50.0, 50.0)), "XYZ inf -> ValueError")
check(leve(C.xyz_vers_rgb, (0.0, 100.0, 0.0)), "XYZ hors gamut sRGB -> ValueError (abstention)")
check(leve(C.lab_vers_xyz, (-1.0, 0.0, 0.0)), "L* négatif -> ValueError")
check(leve(C.lab_vers_xyz, (101.0, 0.0, 0.0)), "L* > 100 -> ValueError")
check(leve(C.lab_vers_xyz, (50.0, 400.0, 0.0)), "a* hors garde -> ValueError")
check(leve(C.lab_vers_rgb, (50.0, -100.0, 60.0)), "Lab hors gamut sRGB -> ValueError (abstention)")
check(leve(C.delta_e_76, (50.0, 0.0, 0.0), (50.0, 0.0)), "ΔE arité 2 -> ValueError")
check(leve(C.delta_e_76, (50.0, 0.0, 0.0), (50.0, float("nan"), 0.0)), "ΔE NaN -> ValueError")
check(leve(C.delta_e_76, (True, 0.0, 0.0), (50.0, 0.0, 0.0)), "ΔE bool -> ValueError")

# ── 15) SOUNDNESS — conformité AA (domaine [1,21]) ──
check(leve(C.conforme_wcag_aa, 0.5), "contraste 0.5 (<1 impossible) -> ValueError")
check(leve(C.conforme_wcag_aa, 22.0), "contraste 22 (>21 impossible) -> ValueError")
check(leve(C.conforme_wcag_aa, True), "contraste bool -> ValueError")
check(leve(C.conforme_wcag_aa, "4.5"), "contraste str -> ValueError")
check(leve(C.conforme_wcag_aa, float("nan")), "contraste NaN -> ValueError")

# ── 16) DÉTERMINISME — double appel strictement identique ──
check(C.rgb_vers_lab((12, 200, 99)) == C.rgb_vers_lab((12, 200, 99)), "déterminisme rgb_vers_lab")
check(C.rgb_vers_hsv((12, 200, 99)) == C.rgb_vers_hsv((12, 200, 99)), "déterminisme rgb_vers_hsv")
check(C.contraste_wcag((12, 200, 99), (0, 0, 0)) == C.contraste_wcag((12, 200, 99), (0, 0, 0)),
      "déterminisme contraste_wcag")
check(C.rgb_vers_lineaire(0.33) == C.rgb_vers_lineaire(0.33), "déterminisme rgb_vers_lineaire")

print(f"\n=== valide_colorimetrie : {ok}/{ok+ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
