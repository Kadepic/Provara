"""VALIDE conjectures_celebres.py — held-out ADVERSE.

ANCRES EXTERNES NON CIRCULAIRES (faits historiques connus INDÉPENDAMMENT du module, écrits EN DUR) :
  • Poincaré = DÉMONTRÉE par Grigori Perelman en 2003 (flot de Ricci avec chirurgie, arXiv 2002-2003 ;
    prix du millénaire Clay 2010, décliné) — et c'est le SEUL des 7 problèmes du millénaire résolu.
  • Fermat = Andrew Wiles, 1995 (Annals of Mathematics 141).
  • Quatre couleurs = Appel & Haken, 1976 (preuve assistée par ordinateur).
  • Kepler = Thomas Hales, 1998 (preuve formelle Flyspeck achevée en 2014).
  • Mertens = RÉFUTÉE (Odlyzko & te Riele, 1985) — PIÈGE : beaucoup la croient vraie.
  • Euler (sommes de puissances) = RÉFUTÉE (Lander & Parkin, 1966 : 27^5+84^5+110^5+133^5 = 144^5,
    identité vérifiable À LA MAIN ci-dessous — second chemin de code indépendant).
  • Riemann, Goldbach, P vs NP, Collatz, premiers jumeaux, Hodge, BSD, Navier-Stokes, Yang-Mills = OUVERTES.
  • Les 7 problèmes du millénaire (Clay, 2000) : Poincaré, Riemann, P vs NP, Hodge, BSD, Navier-Stokes,
    Yang-Mills — exactement 7, exactement 1 résolu.

SOUNDNESS : hors catalogue, auteur/année d'une conjecture OUVERTE, bool, int, None, chaîne vide -> ValueError.
"""
import conjectures_celebres as C

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


# ── 1) ANCRE CENTRALE : Poincaré = DÉMONTRÉE, Perelman, 2003 ──
check(C.statut("poincaré") == "demontree", "Poincaré = démontrée")
check(C.demontree("poincaré") is True, "demontree(Poincaré) = True")
check(C.ouverte("poincaré") is False, "ouverte(Poincaré) = False")
check(C.refutee("poincaré") is False, "refutee(Poincaré) = False")
check(C.auteur_preuve("poincaré") == "Grigori Perelman", "auteur Poincaré = Grigori Perelman")
check(C.annee_preuve("poincaré") == 2003, "année Poincaré = 2003")
check("3-sphère" in C.enonce("poincaré") and "simplement connexe" in C.enonce("poincaré"),
      "énoncé Poincaré : 3-variété simplement connexe homéomorphe à la 3-sphère")
check("Ricci" in C.reference("poincaré"), "référence Poincaré mentionne le flot de Ricci")
check(C.statut("conjecture de Poincaré") == "demontree", "alias 'conjecture de Poincaré' résolu")

# ── 2) PROBLÈMES DU MILLÉNAIRE : exactement 7, exactement 1 résolu (Poincaré) ──
mill = C.problemes_du_millenaire()
check(isinstance(mill, tuple) and len(mill) == 7, "problemes_du_millenaire = exactement 7 entrées")
check(len(set(mill)) == 7, "les 7 problèmes du millénaire sont distincts")
resolus = [m for m in mill if C.demontree(m)]
check(resolus == ["poincare"], "exactement 1 problème du millénaire résolu, et c'est Poincaré")
# Composition exacte connue indépendamment (liste Clay 2000)
attendus_mill = {"poincare", "riemann", "p_vs_np", "hodge", "birch_swinnerton_dyer",
                 "navier_stokes", "yang_mills"}
check(set(mill) == attendus_mill, "composition exacte des 7 problèmes du millénaire (liste Clay 2000)")
check(all(m in C.catalogue() for m in mill), "chaque problème du millénaire est dans le catalogue")

# ── 3) OUVERTES : Riemann, Goldbach, P vs NP, Collatz, jumeaux, Hodge, BSD, Navier-Stokes, Yang-Mills ──
for nom in ("riemann", "goldbach", "p vs np", "collatz", "premiers jumeaux", "hodge",
            "birch et swinnerton-dyer", "navier-stokes", "yang-mills"):
    check(C.statut(nom) == "ouverte", f"{nom} = ouverte")
    check(C.demontree(nom) is False, f"{nom} ne renvoie PAS 'démontrée'")

# ── 4) DÉMONTRÉES : Fermat (Wiles 1995), quatre couleurs (Appel-Haken 1976), Kepler (Hales 1998) ──
check(C.statut("fermat") == "demontree", "Fermat = démontré")
check(C.auteur_preuve("fermat") == "Andrew Wiles", "auteur Fermat = Andrew Wiles")
check(C.annee_preuve("fermat") == 1995, "année Fermat = 1995")
check(C.statut("quatre couleurs") == "demontree", "quatre couleurs = démontré")
check("Appel" in C.auteur_preuve("quatre couleurs") and "Haken" in C.auteur_preuve("quatre couleurs"),
      "auteurs quatre couleurs = Appel & Haken")
check(C.annee_preuve("quatre couleurs") == 1976, "année quatre couleurs = 1976")
check("ordinateur" in C.reference("quatre couleurs"), "quatre couleurs : preuve assistée par ordinateur (dit)")
check(C.statut("kepler") == "demontree", "Kepler = démontrée")
check(C.auteur_preuve("kepler") == "Thomas Hales", "auteur Kepler = Thomas Hales")
check(C.annee_preuve("kepler") == 1998, "année Kepler = 1998")
check("Flyspeck" in C.reference("kepler") and "2014" in C.reference("kepler"),
      "Kepler : preuve formelle Flyspeck 2014 mentionnée")

# ── 5) RÉFUTÉES : Mertens (piège !) et Euler sommes de puissances ──
check(C.statut("mertens") == "refutee", "Mertens = RÉFUTÉE (piège : souvent crue vraie)")
check(C.demontree("mertens") is False, "Mertens ne renvoie PAS 'démontrée'")
check(C.ouverte("mertens") is False, "Mertens ne renvoie PAS 'ouverte'")
check(C.refutee("mertens") is True, "refutee(Mertens) = True")
check("Odlyzko" in C.auteur_preuve("mertens") and "te Riele" in C.auteur_preuve("mertens"),
      "réfutation Mertens = Odlyzko & te Riele")
check(C.annee_preuve("mertens") == 1985, "année réfutation Mertens = 1985")
check(C.refutee("conjecture d'Euler") is True, "Euler (puissances) = réfutée")
check("Lander" in C.auteur_preuve("conjecture d'Euler") and "Parkin" in C.auteur_preuve("conjecture d'Euler"),
      "réfutation Euler = Lander & Parkin")
check(C.annee_preuve("conjecture d'Euler") == 1966, "année réfutation Euler = 1966")
# SECOND CHEMIN INDÉPENDANT : le contre-exemple de Lander & Parkin se vérifie par arithmétique entière
check(27**5 + 84**5 + 110**5 + 133**5 == 144**5,
      "contre-exemple Lander-Parkin vérifié à la main : 27^5+84^5+110^5+133^5 = 144^5")

# ── 6) ABSTENTION : conjecture OUVERTE -> ni auteur ni année (JAMAIS inventés) ──
for nom in ("riemann", "goldbach", "p vs np", "collatz", "premiers jumeaux", "hodge",
            "birch et swinnerton-dyer", "navier-stokes", "yang-mills"):
    check(leve(C.auteur_preuve, nom), f"auteur_preuve({nom}) ouverte -> ValueError")
    check(leve(C.annee_preuve, nom), f"annee_preuve({nom}) ouverte -> ValueError")
# BALAYAGE : aucune entrée du catalogue marquée ouverte n'expose auteur/année
for nom in C.catalogue():
    if C.ouverte(nom):
        check(leve(C.auteur_preuve, nom) and leve(C.annee_preuve, nom),
              f"balayage catalogue : {nom} ouverte n'expose ni auteur ni année")

# ── 7) ABSTENTION : hors catalogue -> ValueError (jamais un statut deviné) ──
check(leve(C.statut, "conjecture abc"), "conjecture abc (hors catalogue, statut contesté) -> ValueError")
check(leve(C.statut, "grande conjecture de machin"), "conjecture inconnue -> ValueError")
check(leve(C.demontree, "beal"), "demontree(hors catalogue) -> ValueError")
check(leve(C.ouverte, "erdos-strauss"), "ouverte(hors catalogue) -> ValueError")
check(leve(C.refutee, "legendre"), "refutee(hors catalogue) -> ValueError")
check(leve(C.auteur_preuve, "abc"), "auteur_preuve(hors catalogue) -> ValueError")
check(leve(C.annee_preuve, "abc"), "annee_preuve(hors catalogue) -> ValueError")
check(leve(C.enonce, "xyz"), "enonce(hors catalogue) -> ValueError")

# ── 8) SOUNDNESS — types invalides ──
check(leve(C.statut, True), "statut(bool) -> ValueError")
check(leve(C.statut, 1), "statut(int) -> ValueError")
check(leve(C.statut, None), "statut(None) -> ValueError")
check(leve(C.statut, ""), "statut('') -> ValueError")
check(leve(C.statut, "   "), "statut(espaces) -> ValueError")
check(leve(C.statut, 3.14), "statut(float) -> ValueError")
check(leve(C.statut, ["poincare"]), "statut(liste) -> ValueError")
check(leve(C.auteur_preuve, False), "auteur_preuve(bool) -> ValueError")
check(leve(C.annee_preuve, 2003), "annee_preuve(int) -> ValueError")
check(leve(C.enonce, None), "enonce(None) -> ValueError")

# ── 9) ALIAS EXPLICITES (jamais flous) ──
check(C.statut("syracuse") == "ouverte", "alias 'syracuse' -> Collatz (ouverte)")
check(C.statut("Syracuse") == C.statut("collatz"), "syracuse et collatz = même statut")
check(C.statut("BSD") == "ouverte", "alias 'BSD' -> Birch et Swinnerton-Dyer")
check(C.statut("dernier théorème de Fermat") == "demontree", "alias 'dernier théorème de Fermat'")
check(C.statut("hypothèse de Riemann") == "ouverte", "alias 'hypothèse de Riemann'")
check(C.statut("P = NP") == "ouverte", "alias 'P = NP'")
check(C.statut("3n+1") == "ouverte", "alias '3n+1' -> Collatz")

# ── 10) CATALOGUE : 15 entrées, statuts tous licites, comptes exacts ──
cat = C.catalogue()
check(isinstance(cat, tuple) and len(cat) == 15, "catalogue = 15 entrées (tuple)")
check(len(set(cat)) == 15, "catalogue sans doublon")
check(all(C.statut(n) in ("demontree", "refutee", "ouverte") for n in cat), "statuts tous licites")
# Comptes connus indépendamment : 4 démontrées, 2 réfutées, 9 ouvertes
check(sum(1 for n in cat if C.demontree(n)) == 4, "exactement 4 démontrées (Poincaré/Fermat/4coul/Kepler)")
check(sum(1 for n in cat if C.refutee(n)) == 2, "exactement 2 réfutées (Mertens/Euler)")
check(sum(1 for n in cat if C.ouverte(n)) == 9, "exactement 9 ouvertes")
# Toute démontrée/réfutée expose un auteur non vide et une année plausible (1 seul statut vrai à la fois)
for n in cat:
    check((C.demontree(n) + C.refutee(n) + C.ouverte(n)) == 1, f"{n} : exactement un statut vrai")
    if not C.ouverte(n):
        check(isinstance(C.auteur_preuve(n), str) and C.auteur_preuve(n) != ""
              and isinstance(C.annee_preuve(n), int) and 1900 <= C.annee_preuve(n) <= 2026,
              f"{n} : auteur non vide + année dans [1900, 2026]")

# ── 11) DÉTERMINISME ──
check(C.statut("poincaré") == C.statut("poincaré"), "déterminisme statut")
check(C.problemes_du_millenaire() == C.problemes_du_millenaire(), "déterminisme problèmes du millénaire")
check(C.catalogue() == C.catalogue(), "déterminisme catalogue")
check(C.auteur_preuve("fermat") == C.auteur_preuve("fermat"), "déterminisme auteur")

print(f"\n=== valide_conjectures_celebres : {ok}/{ok+ko} ===")
import sys; sys.exit(0 if ko == 0 else 1)
