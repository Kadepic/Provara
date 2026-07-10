"""
VALIDE proprietes_mecaniques_materiaux.py — held-out ADVERSE.

ANCRES EXTERNES NON CIRCULAIRES (valeurs d'ingénierie universellement tabulées — ASM Handbook,
Ashby (Materials Selection), Eurocodes, MatWeb — écrites EN DUR ici, jamais recalculées par le module) :
  • E(acier) ≈ 200-215 GPa ; E(aluminium 6061) ≈ 68-72 ; E(cuivre) ≈ 110-128 ; E(Ti-6Al-4V) ≈ 110-115 ;
    E(béton) ≈ 20-40 ; E(verre) ≈ 60-75.
  • ρ(acier) ≈ 7800-7900 ; ρ(aluminium) contient 2700 ; ρ(titane) contient 4430 kg/m³ ;
    ρ(verre) contient 2230 (borosilicate Pyrex 7740) ET 2500 (sodocalcique) — conditions('verre')
    annonce couvrir le borosilicate, l'intervalle doit donc le contenir.
  • ORDRE (fait physique) : E(acier) > E(cuivre) > E(titane) ≈ 1,6·E(aluminium) > E(aluminium) > E(béton).
  • Re = ENCADREMENT (min de spec, MAJORANT) : Re(acier doux) = (235, 630) — 235 = ReH min S235
    (EN 10025-2, t ≤ 16 mm) ; 630 = Rm max S355 (EN 10025-2) et Re < Rm, donc aucun acier conforme ne
    dépasse 630. resiste('acier doux', 300) = 'indéterminé' ; resiste(50) = 'oui' ; resiste(900) = 'non'.
  • CONTRE-EXEMPLES D'AUDIT (matière réelle conforme, un 'oui'/'non' serait un FAUX) :
    S235 conforme à Re = 235 plastifie sous 240 -> resiste('acier doux', 240) ≠ 'oui' ;
    6061-T6 de production mesuré 280-325 MPa -> resiste('aluminium 6061', 290) ≠ 'non' ;
    Cu écroui commercial le plus dur ~420 MPa -> resiste('cuivre', 400) ≠ 'non' ;
    Ti-6Al-4V STA réel > 1100 MPa (sections minces ~1170) -> resiste('titane Ti-6Al-4V', 1150) ≠ 'non'.

SOUNDNESS : matériau hors catalogue / non-str / vide, contrainte bool/str/NaN/inf/négative, limite
élastique demandée sur fragile (béton, verre, fonte grise) ou bois -> ValueError. DÉTERMINISME : double appel.
"""
import proprietes_mecaniques_materiaux as M

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


def dans(intervalle, lo, hi):
    """L'intervalle rendu est inclus dans [lo, hi] (ancre tabulée) et bien ordonné."""
    a, b = intervalle
    return lo <= a < b <= hi


# ── 1) ANCRES E — plages d'ingénierie tabulées (GPa), EN DUR ──
check(dans(M.module_young("acier doux"), 200.0, 215.0), "E acier doux ⊂ [200,215] GPa (tables acier)")
check(dans(M.module_young("aluminium 6061"), 68.0, 72.0), "E alu 6061 ⊂ [68,72] GPa (ASM/MatWeb)")
check(dans(M.module_young("cuivre"), 110.0, 128.0), "E cuivre ⊂ [110,128] GPa (tables Cu)")
check(dans(M.module_young("titane Ti-6Al-4V"), 110.0, 115.0), "E Ti-6Al-4V ⊂ [110,115] GPa (~113,8 typique)")
check(dans(M.module_young("béton"), 20.0, 40.0), "E béton ⊂ [20,40] GPa (Eurocode 2, C20/25-C50/60)")
check(dans(M.module_young("verre"), 60.0, 75.0), "E verre ⊂ [60,75] GPa (sodocalcique ~70)")
check(dans(M.module_young("acier inoxydable 304"), 185.0, 205.0), "E inox 304 ⊂ [185,205] GPa (~193-200)")
check(dans(M.module_young("polyéthylène"), 0.05, 1.5), "E PE ⊂ [0,05;1,5] GPa (PEBD-PEHD)")
check(dans(M.module_young("fonte"), 66.0, 170.0), "E fonte grise ⊂ [66,170] GPa (EN-GJL)")
check(dans(M.module_young("magnésium"), 40.0, 48.0), "E magnésium ⊂ [40,48] GPa (~45)")
check(dans(M.module_young("bois de pin"), 6.0, 16.0), "E pin axial ⊂ [6,16] GPa (résineux, 12% humidité)")

# ── 2) ANCRES ρ (kg/m³) — valeurs de référence EN DUR ──
check(dans(M.masse_volumique("acier doux"), 7800.0, 7900.0), "ρ acier ⊂ [7800,7900] (7850 typique)")
rho_al = M.masse_volumique("aluminium 6061")
check(rho_al[0] <= 2700.0 <= rho_al[1], "ρ alu contient 2700 (référence Al)")
rho_ti = M.masse_volumique("titane Ti-6Al-4V")
check(rho_ti[0] <= 4430.0 <= rho_ti[1], "ρ titane contient 4430 (référence Ti-6Al-4V)")
rho_cu = M.masse_volumique("cuivre")
check(rho_cu[0] <= 8940.0 <= rho_cu[1], "ρ cuivre contient 8940 (référence Cu)")
rho_mg = M.masse_volumique("magnésium")
check(rho_mg[0] <= 1740.0 <= rho_mg[1], "ρ magnésium contient 1740 (Mg pur 1738)")
check(dans(M.masse_volumique("polyéthylène"), 900.0, 980.0), "ρ PE ⊂ [900,980] (flotte sur l'eau : <1000)")
check(M.masse_volumique("bois de pin")[1] < 1000.0, "ρ pin < 1000 (le pin sec flotte)")
rho_verre = M.masse_volumique("verre")
check(rho_verre[0] <= 2230.0 <= rho_verre[1], "ρ verre contient 2230 (borosilicate Pyrex 7740, 2,23 g/cm³)")
check(rho_verre[0] <= 2500.0 <= rho_verre[1], "ρ verre contient 2500 (sodocalcique ~2,5 g/cm³)")
check(dans(rho_verre, 2100.0, 2900.0), "ρ verre ⊂ [2100,2900] (verres silicatés courants)")
check("borosilicate" in M.conditions("verre").lower(),
      "conditions(verre) annoncent le borosilicate — l'intervalle ρ ci-dessus DOIT donc le couvrir")

# ── 3) ORDRE DES MODULES (fait physique, indépendant du catalogue) ──
def milieu(iv):
    return (iv[0] + iv[1]) / 2.0

e_acier = milieu(M.module_young("acier doux"))
e_cu = milieu(M.module_young("cuivre"))
e_ti = milieu(M.module_young("titane Ti-6Al-4V"))
e_al = milieu(M.module_young("aluminium 6061"))
e_beton = milieu(M.module_young("béton"))
check(e_acier > e_cu, "ORDRE : E(acier) > E(cuivre)")
check(e_cu > e_ti, "ORDRE : E(cuivre) > E(titane)")
check(e_ti > e_al, "ORDRE : E(titane) > E(aluminium)")
check(e_al > e_beton, "ORDRE : E(aluminium) > E(béton)")
check(abs(e_ti - 1.6 * e_al) / e_ti < 0.05, "ORDRE : E(titane) ≈ 1,6 × E(aluminium) (à 5 %)")
# séparation stricte des intervalles (pas seulement des milieux) là où les tables séparent
check(M.module_young("acier doux")[0] > M.module_young("cuivre")[1], "intervalles acier et cuivre disjoints")
check(M.module_young("cuivre")[1] > M.module_young("béton")[1] * 2, "E cuivre >> E béton")

# ── 4) ANCRES resiste() — Re(acier doux) = (235, 630) : min EN 10025-2 S235 t≤16mm, majorant Rm max S355 ──
check(M.resiste("acier doux", 300) == "indéterminé",
      "resiste(acier doux, 300 MPa) = 'indéterminé' (300 DANS [235,630] : on ne tranche pas)")
check(M.resiste("acier doux", 50) == "oui", "resiste(acier doux, 50 MPa) = 'oui' (50 < 235)")
check(M.resiste("acier doux", 900) == "non",
      "resiste(acier doux, 900 MPa) = 'non' (900 > 630 = Rm max S355 EN 10025-2, et Re < Rm)")
re_acier = M.limite_elastique("acier doux")
check(re_acier == (235.0, 630.0),
      "Re acier doux = (235, 630) : ReH min S235 t≤16mm (EN 10025-2) / majorant = Rm max S355 (630)")
# CONTRE-EXEMPLE D'AUDIT : un S235 conforme à Re=235 plastifie sous 240 -> 'oui' serait un FAUX POSITIF
check(M.resiste("acier doux", 240) == "indéterminé",
      "resiste(acier doux, 240) = 'indéterminé' — un S235 conforme à Re=235 plastifie sous 240 (audit)")
check(M.resiste("acier doux", 234) == "oui", "resiste(acier doux, 234) = 'oui' (234 < 235 garanti EN 10025-2)")
# bornes de l'encadrement : incluses -> indéterminé (conservateur)
check(M.resiste("acier doux", re_acier[0]) == "indéterminé", "contrainte = min(Re) -> 'indéterminé'")
check(M.resiste("acier doux", re_acier[1]) == "indéterminé", "contrainte = majorant(Re) -> 'indéterminé'")
check(M.resiste("acier doux", 0) == "oui", "contrainte nulle -> 'oui'")
# Ti-6Al-4V : Re ≥ 828 MPa (AMS 4911) -> 500 MPa tient partout ; 1500 > majorant 1250 -> aucune nuance
check(M.resiste("titane Ti-6Al-4V", 500) == "oui", "resiste(Ti-6Al-4V, 500) = 'oui' (Re min ~828)")
check(M.resiste("titane Ti-6Al-4V", 1500) == "non", "resiste(Ti-6Al-4V, 1500) = 'non' (1500 > majorant 1250)")
# CONTRE-EXEMPLE D'AUDIT : du STA réel dépasse 1100 (sections minces ~1170) -> 'non' à 1150 serait un FAUX
check(M.resiste("titane Ti-6Al-4V", 1150) == "indéterminé",
      "resiste(Ti-6Al-4V, 1150) = 'indéterminé' — du STA réel mesure ~1170 (audit)")
check(M.resiste("polyéthylène", 100) == "non", "resiste(PE, 100 MPa) = 'non' (100 > majorant 45)")
check(M.resiste("polyéthylène", 5) == "oui", "resiste(PE, 5 MPa) = 'oui' (5 < 8, seuil PEBD min)")
# CONTRE-EXEMPLE D'AUDIT : le Cu écroui commercial le plus dur atteint ~420 -> 'non' à 400 serait un FAUX
check(M.resiste("cuivre", 400) == "indéterminé",
      "resiste(cuivre, 400) = 'indéterminé' — écroui extra-dur réel ~420 MPa (audit)")
check(M.resiste("cuivre", 500) == "non", "resiste(cuivre, 500) = 'non' (500 > majorant 450)")
check(M.resiste("cuivre", 100) == "indéterminé", "resiste(cuivre, 100) = 'indéterminé' (recuit 33, écroui ~420)")
# CONTRE-EXEMPLE D'AUDIT : du 6061-T6 de production mesure 280-325 MPa -> 'non' à 290 serait un FAUX
check(M.resiste("aluminium 6061", 290) == "indéterminé",
      "resiste(alu 6061, 290) = 'indéterminé' — T6 de production mesuré 280-325 MPa (audit)")
check(M.resiste("aluminium 6061", 400) == "non",
      "resiste(alu 6061, 400) = 'non' (400 > majorant 350 ; aucun 6061 O→T6 tabulé au-delà de ~325)")
check(M.resiste("aluminium 6061", 50) == "oui", "resiste(alu 6061, 50) = 'oui' (50 < 55, état O)")
# inox 304 : min 205 (ASTM A240 recuit) ; majorant 690 (dureté plafonnée A240 -> Rm ≲ 690, Re < Rm)
check(M.limite_elastique("acier inoxydable 304")[0] == 205.0, "Re min inox 304 recuit = 205 MPa (ASTM A240)")
check(M.resiste("acier inoxydable 304", 200) == "oui", "resiste(304, 200) = 'oui' (200 < 205 A240)")
check(M.resiste("acier inoxydable 304", 800) == "non", "resiste(304, 800) = 'non' (800 > majorant 690)")
check(M.resiste("acier inoxydable 304", 350) == "indéterminé", "resiste(304, 350) = 'indéterminé'")

# ── 5) ABSTENTION fragiles / bois : pas de limite élastique -> ValueError ──
check(leve(M.limite_elastique, "béton"), "limite_elastique(béton) -> ValueError (fragile)")
check(leve(M.limite_elastique, "verre"), "limite_elastique(verre) -> ValueError (fragile)")
check(leve(M.limite_elastique, "fonte"), "limite_elastique(fonte grise) -> ValueError (pas de limite nette)")
check(leve(M.limite_elastique, "bois de pin"), "limite_elastique(bois de pin) -> ValueError (anisotrope)")
check(leve(M.resiste, "béton", 10), "resiste(béton, 10) -> ValueError (abstention, pas 'oui'/'non')")
check(leve(M.resiste, "verre", 10), "resiste(verre, 10) -> ValueError (abstention)")

# ── 6) CONDITIONS — le sens des fibres du bois est DIT ; conditions non vides partout ──
cond_pin = M.conditions("bois de pin")
check(isinstance(cond_pin, str) and "fibres" in cond_pin.lower(), "conditions(pin) mentionnent le SENS DES FIBRES")
check("fragile" in M.conditions("verre").lower(), "conditions(verre) disent FRAGILE")
check(all(isinstance(M.conditions(m), str) and len(M.conditions(m)) > 10 for m in M.catalogue()),
      "conditions non vides pour tout le catalogue")

# ── 7) CATALOGUE — 11 matériaux, intervalles tous bien formés (0 < min < max) ──
noms = M.catalogue()
check(isinstance(noms, tuple) and len(noms) == 11, "catalogue = 11 matériaux (tuple)")
check("acier doux" in noms and "titane ti-6al-4v" in noms and "béton" in noms, "noms canoniques présents")
check(all(0 < M.module_young(m)[0] < M.module_young(m)[1] for m in noms), "tous les E : 0 < min < max")
check(all(0 < M.masse_volumique(m)[0] < M.masse_volumique(m)[1] for m in noms), "tous les ρ : 0 < min < max")
# normalisation casse/espaces/accents non ambigus
check(M.module_young("  ACIER   DOUX ") == M.module_young("acier doux"), "normalisation casse/espaces")
check(M.module_young("beton") == M.module_young("béton"), "alias sans accent -> même entrée")

# ── 8) SOUNDNESS — matériau ──
check(leve(M.module_young, "kryptonite"), "matériau hors catalogue -> ValueError")
check(leve(M.module_young, "acier"), "'acier' seul (ambigu, hors catalogue) -> ValueError")
check(leve(M.masse_volumique, "adamantium"), "masse_volumique hors catalogue -> ValueError")
check(leve(M.limite_elastique, "unobtainium"), "limite_elastique hors catalogue -> ValueError")
check(leve(M.conditions, "bois"), "'bois' seul -> ValueError (le sens des fibres impose l'entrée précise)")
check(leve(M.resiste, "granite", 10), "resiste hors catalogue -> ValueError")
check(leve(M.module_young, ""), "nom vide -> ValueError")
check(leve(M.module_young, True), "matériau bool -> ValueError")
check(leve(M.module_young, 42), "matériau int -> ValueError")
check(leve(M.module_young, None), "matériau None -> ValueError")

# ── 9) SOUNDNESS — contrainte ──
check(leve(M.resiste, "acier doux", True), "contrainte bool -> ValueError")
check(leve(M.resiste, "acier doux", "300"), "contrainte str -> ValueError")
check(leve(M.resiste, "acier doux", float("nan")), "contrainte NaN -> ValueError")
check(leve(M.resiste, "acier doux", float("inf")), "contrainte inf -> ValueError")
check(leve(M.resiste, "acier doux", float("-inf")), "contrainte -inf -> ValueError")
check(leve(M.resiste, "acier doux", -10), "contrainte négative -> ValueError")
check(leve(M.resiste, "acier doux", None), "contrainte None -> ValueError")

# ── 10) DÉTERMINISME ──
check(M.module_young("cuivre") == M.module_young("cuivre"), "déterminisme module_young")
check(M.resiste("acier doux", 300) == M.resiste("acier doux", 300), "déterminisme resiste")
check(M.catalogue() == M.catalogue(), "déterminisme catalogue")
check(M.masse_volumique("verre") == M.masse_volumique("verre"), "déterminisme masse_volumique")

print(f"\n=== valide_proprietes_mecaniques_materiaux : {ok}/{ok+ko} ===")
import sys; sys.exit(0 if ko == 0 else 1)
