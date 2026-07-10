"""
VALIDE classification_roches.py — held-out ADVERSE.

ANCRES EXTERNES NON CIRCULAIRES (pétrologie classique — valeurs écrites EN DUR, connues indépendamment
du module, jamais recalculées par lui) :
  • granite = magmatique PLUTONIQUE (refroidissement LENT en profondeur, gros cristaux) ;
    basalte = magmatique VOLCANIQUE (refroidissement RAPIDE en surface, microlithique).
    Même chimie possible, textures différentes -> ANCRE DISCRIMINANTE : un module classant le basalte
    'plutonique' serait FAUX (testé explicitement).
  • marbre = métamorphique, protolithe = CALCAIRE ; quartzite = métamorphique, protolithe = GRÈS ;
    ardoise = métamorphique, protolithe = ARGILITE ; amphibolite : protolithe = BASALTE (méta-basite).
  • calcaire = sédimentaire BIOCHIMIQUE (PAS métamorphique) ; obsidienne = VOLCANIQUE (verre de trempe).
  • protolithe('granite') -> ValueError : le granite n'est PAS métamorphique.
  (Source : classification génétique classique, Foucault & Raoult / manuels de géologie générale.)

SOUNDNESS : hors catalogue, minéral (quartz ≠ roche), types non-str (bool/int/float/None/list/NaN),
protolithe de roche non métamorphique, ambiguïtés (schiste/gneiss/amphibolite) -> ValueError.
"""
import math

import classification_roches as C

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


# ── 1) ANCRE DISCRIMINANTE : granite plutonique vs basalte volcanique ──
check(C.famille("granite") == "magmatique", "granite = magmatique")
check(C.sous_type("granite") == "plutonique", "granite = plutonique (refroidissement lent en profondeur)")
check(C.famille("basalte") == "magmatique", "basalte = magmatique")
check(C.sous_type("basalte") == "volcanique", "basalte = volcanique (refroidissement rapide)")
check(C.sous_type("basalte") != "plutonique", "DISCRIMINANT : basalte ≠ plutonique (sinon module FAUX)")
check(C.sous_type("granite") != C.sous_type("basalte"),
      "granite/basalte : même famille magmatique mais textures/sous-types DIFFÉRENTS")

# ── 2) ANCRES protolithes (métamorphisme classique) ──
check(C.famille("marbre") == "métamorphique", "marbre = métamorphique")
check(C.protolithe("marbre") == "calcaire", "protolithe(marbre) = calcaire")
check(C.famille("quartzite") == "métamorphique", "quartzite = métamorphique")
check(C.protolithe("quartzite") == "grès", "protolithe(quartzite) = grès")
check(C.famille("ardoise") == "métamorphique", "ardoise = métamorphique")
check(C.protolithe("ardoise") == "argilite", "protolithe(ardoise) = argilite")
check(C.protolithe("amphibolite") == "basalte", "protolithe(amphibolite) = basalte (méta-basite)")
# Cohérence génétique : chaque protolithe rendu est lui-même une roche NON métamorphique du catalogue.
for meta in ("marbre", "quartzite", "ardoise", "amphibolite"):
    p = C.protolithe(meta)
    check(p in C.catalogue() and C.famille(p) != "métamorphique",
          f"protolithe({meta}) = {p} : roche du catalogue, non métamorphique")

# ── 3) ANCRE : calcaire = sédimentaire biochimique (PAS métamorphique) ──
check(C.famille("calcaire") == "sédimentaire", "calcaire = sédimentaire")
check(C.famille("calcaire") != "métamorphique", "calcaire PAS métamorphique (c'est le marbre qui l'est)")
check(C.sous_type("calcaire") == "biochimique", "calcaire = biochimique")

# ── 4) ANCRE : obsidienne = volcanique (verre de trempe) ──
check(C.famille("obsidienne") == "magmatique", "obsidienne = magmatique")
check(C.sous_type("obsidienne") == "volcanique", "obsidienne = volcanique (verre)")

# ── 5) ANCRE ValueError imposée : protolithe('granite') ──
check(leve(C.protolithe, "granite"), "protolithe(granite) -> ValueError (pas métamorphique)")

# ── 6) Reste du catalogue magmatique ──
check(C.sous_type("gabbro") == "plutonique", "gabbro = plutonique")
check(C.sous_type("rhyolite") == "volcanique", "rhyolite = volcanique (équivalent volcanique du granite)")
check(C.sous_type("andésite") == "volcanique", "andésite = volcanique")
check(C.sous_type("pierre ponce") == "volcanique", "pierre ponce = volcanique")
check(C.famille("gabbro") == "magmatique" and C.famille("rhyolite") == "magmatique",
      "gabbro et rhyolite = magmatiques")

# ── 7) Sédimentaires : détritique / chimique / biochimique ──
check(C.famille("grès") == "sédimentaire" and C.sous_type("grès") == "détritique", "grès = sédim. détritique")
check(C.famille("argilite") == "sédimentaire" and C.sous_type("argilite") == "détritique",
      "argilite = sédim. détritique")
check(C.sous_type("conglomérat") == "détritique", "conglomérat = détritique (galets cimentés)")
check(C.famille("sel gemme") == "sédimentaire" and C.sous_type("sel gemme") == "chimique",
      "sel gemme = sédim. chimique (évaporite)")
check(C.sous_type("gypse") == "chimique", "gypse = chimique (évaporite)")
check(C.famille("charbon") == "sédimentaire" and C.sous_type("charbon") == "biochimique",
      "charbon = sédim. biochimique (végétaux accumulés)")

# ── 8) Métamorphiques foliées ──
check(C.famille("schiste") == "métamorphique" and C.sous_type("schiste") == "foliée",
      "schiste = métamorphique foliée")
check(C.famille("gneiss") == "métamorphique" and C.sous_type("gneiss") == "foliée",
      "gneiss = métamorphique foliée")
check(C.famille("amphibolite") == "métamorphique", "amphibolite = métamorphique")
check(C.sous_type("marbre") == "non foliée" and C.sous_type("quartzite") == "non foliée",
      "marbre et quartzite = non foliées")
check(C.sous_type("ardoise") == "foliée", "ardoise = foliée (plans de clivage)")

# ── 9) ORIGINE = le critère génétique (mode de formation) ──
check("magma" in C.origine("granite"), "origine(granite) mentionne le magma")
check("magma" in C.origine("basalte"), "origine(basalte) mentionne le magma")
check("diagen" in C.origine("calcaire"), "origine(calcaire) mentionne la diagenèse")
check("état solide" in C.origine("marbre"), "origine(marbre) = transformation à l'état solide")
check(C.origine("granite") == C.origine("obsidienne"), "même origine pour toute la famille magmatique")
check(C.origine("grès") != C.origine("gneiss"), "origines sédimentaire ≠ métamorphique")

# ── 10) CATALOGUE : closed-set complet et cohérent ──
cat = C.catalogue()
check(isinstance(cat, tuple) and len(cat) == 20, f"catalogue = 20 roches (obtenu {len(cat)})")
for attendu in ("granite", "basalte", "gabbro", "rhyolite", "andésite", "obsidienne", "pierre ponce",
                "grès", "argilite", "conglomérat", "calcaire", "sel gemme", "gypse", "charbon",
                "marbre", "quartzite", "ardoise", "schiste", "gneiss", "amphibolite"):
    check(attendu in cat, f"{attendu} présent au catalogue")
check(all(C.famille(r) in ("magmatique", "sédimentaire", "métamorphique") for r in cat),
      "toute roche du catalogue a une famille parmi les 3")
check(sorted(cat) == list(cat), "catalogue trié (déterministe)")
# Comptes par famille écrits EN DUR (7 magmatiques + 7 sédimentaires + 6 métamorphiques = 20).
check(sum(1 for r in cat if C.famille(r) == "magmatique") == 7, "7 roches magmatiques")
check(sum(1 for r in cat if C.famille(r) == "sédimentaire") == 7, "7 roches sédimentaires")
check(sum(1 for r in cat if C.famille(r) == "métamorphique") == 6, "6 roches métamorphiques")

# ── 11) SOUNDNESS : hors catalogue -> ValueError ──
check(leve(C.famille, "kryptonite"), "roche imaginaire -> ValueError")
check(leve(C.famille, "quartz"), "quartz = MINÉRAL pas roche -> ValueError")
check(leve(C.famille, "diamant"), "diamant = minéral -> ValueError")
check(leve(C.sous_type, "pouzzolane"), "roche hors catalogue (sous_type) -> ValueError")
check(leve(C.origine, "météorite"), "hors catalogue (origine) -> ValueError")
check(leve(C.protolithe, "migmatite"), "hors catalogue (protolithe) -> ValueError")
check(leve(C.famille, ""), "chaîne vide -> ValueError")
check(leve(C.famille, "   "), "espaces seuls -> ValueError")

# ── 12) SOUNDNESS : protolithe d'une roche non métamorphique -> ValueError ──
check(leve(C.protolithe, "basalte"), "protolithe(basalte) -> ValueError (magmatique)")
check(leve(C.protolithe, "calcaire"), "protolithe(calcaire) -> ValueError (sédimentaire)")
check(leve(C.protolithe, "grès"), "protolithe(grès) -> ValueError (sédimentaire)")
check(leve(C.protolithe, "obsidienne"), "protolithe(obsidienne) -> ValueError (magmatique)")

# ── 13) SOUNDNESS : ambiguïtés documentées -> abstention (jamais un choix arbitraire) ──
check(leve(C.protolithe, "schiste"), "protolithe(schiste) ambigu (pélite/basalte) -> ValueError")
check(leve(C.protolithe, "gneiss"), "protolithe(gneiss) ambigu (ortho/paragneiss) -> ValueError")
check(leve(C.sous_type, "amphibolite"), "sous_type(amphibolite) foliation ambiguë -> ValueError")

# ── 14) SOUNDNESS : types invalides (bool/int/float/None/list/NaN) -> ValueError ──
check(leve(C.famille, True), "bool -> ValueError")
check(leve(C.famille, 42), "int -> ValueError")
check(leve(C.famille, 3.14), "float -> ValueError")
check(leve(C.famille, float("nan")), "NaN -> ValueError")
check(leve(C.famille, None), "None -> ValueError")
check(leve(C.famille, ["granite"]), "list -> ValueError")
check(leve(C.sous_type, False), "sous_type(bool) -> ValueError")
check(leve(C.protolithe, 0), "protolithe(int) -> ValueError")
check(leve(C.origine, math.inf), "origine(inf) -> ValueError")

# ── 15) Tolérance de graphie STRICTE (casse/espaces/alias sans accent connus) ──
check(C.famille("GRANITE") == "magmatique", "casse insensible (GRANITE)")
check(C.famille("  basalte  ") == "magmatique", "espaces péri. tolérés")
check(C.sous_type("gres") == "détritique", "alias sans accent 'gres' -> grès")
check(C.sous_type("andesite") == "volcanique", "alias sans accent 'andesite'")
check(C.sous_type("conglomerat") == "détritique", "alias sans accent 'conglomerat'")
check(C.famille("Pierre  Ponce") == "magmatique", "espaces internes normalisés")

# ── 16) DÉTERMINISME ──
check(C.famille("granite") == C.famille("granite"), "déterminisme famille")
check(C.sous_type("basalte") == C.sous_type("basalte"), "déterminisme sous_type")
check(C.protolithe("marbre") == C.protolithe("marbre"), "déterminisme protolithe")
check(C.catalogue() == C.catalogue(), "déterminisme catalogue")

print(f"\n=== valide_classification_roches : {ok}/{ok+ko} ===")
import sys; sys.exit(0 if ko == 0 else 1)
