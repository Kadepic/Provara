"""
VALIDE reseau_trophique.py — held-out ADVERSE.

ANCRES NON CIRCULAIRES (valeurs connues INDÉPENDAMMENT de la formule testée, écrites EN DUR) :
  • CHAÎNE herbe -> lapin -> renard : niveaux 1, 2, 3 EXACTEMENT (définition de Lindeman, calcul à la main).
  • RÉSEAU (le cas qui distingue réseau et chaîne) : herbe->lapin, herbe->souris, lapin->renard,
    souris->renard, souris->chouette. À la main :
      niveau(lapin) = 1 + moyenne(1) = 2 ; niveau(souris) = 2 ;
      niveau(renard) = 1 + moyenne(2, 2) = 3 ; niveau(chouette) = 1 + moyenne(2) = 3.
  • OMNIVORE, niveau FRACTIONNAIRE (un module qui rendrait un entier serait FAUX) :
      ours mange herbe(1) ET saumon(3) -> 1 + (1+3)/2 = 3.0 ;
      ours mange herbe(1) ET lapin(2) -> 1 + (1+2)/2 = 2.5.
  • RETRAIT de 'herbe' dans le réseau -> lapin et souris deviennent sans ressource (à la main).
  • CYCLE a->b->a -> ValueError (niveau indéfini).

SOUNDNESS : espèce inconnue, type invalide, producteur avec proie, doublon, bool/str vide/None,
mauvaise arité, cycle -> ValueError. DÉTERMINISME : double appel identique.
"""
import reseau_trophique as RT

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


# ── Constructeurs de scénarios ────────────────────────────────────────────────────────────────────
def chaine():
    r = RT.Reseau()
    r.ajoute_espece("herbe", "producteur")
    r.ajoute_espece("lapin", "herbivore")
    r.ajoute_espece("renard", "carnivore")
    r.ajoute_lien("herbe", "lapin")
    r.ajoute_lien("lapin", "renard")
    return r


def reseau():
    r = RT.Reseau()
    r.ajoute_espece("herbe", "producteur")
    r.ajoute_espece("lapin", "herbivore")
    r.ajoute_espece("souris", "herbivore")
    r.ajoute_espece("renard", "carnivore")
    r.ajoute_espece("chouette", "carnivore")
    r.ajoute_lien("herbe", "lapin")
    r.ajoute_lien("herbe", "souris")
    r.ajoute_lien("lapin", "renard")
    r.ajoute_lien("souris", "renard")
    r.ajoute_lien("souris", "chouette")
    return r


# ── 1) ANCRE CHAÎNE : niveaux 1, 2, 3 EXACTEMENT ──
c = chaine()
check(c.niveau_trophique("herbe") == 1.0, "chaîne : niveau(herbe) = 1")
check(c.niveau_trophique("lapin") == 2.0, "chaîne : niveau(lapin) = 2")
check(c.niveau_trophique("renard") == 3.0, "chaîne : niveau(renard) = 3")

# ── 2) ANCRE RÉSEAU : renard et chouette au niveau 3 (moyenne de 2 et 2 ; de 2) ──
r = reseau()
check(r.niveau_trophique("lapin") == 2.0, "réseau : niveau(lapin) = 2")
check(r.niveau_trophique("souris") == 2.0, "réseau : niveau(souris) = 2")
check(r.niveau_trophique("renard") == 3.0, "réseau : niveau(renard) = 1 + moyenne(2,2) = 3")
check(r.niveau_trophique("chouette") == 3.0, "réseau : niveau(chouette) = 1 + moyenne(2) = 3")

# ── 3) ANCRE OMNIVORE : niveau FRACTIONNAIRE (jamais un entier arrondi) ──
o = RT.Reseau()
o.ajoute_espece("herbe", "producteur")
o.ajoute_espece("saumon", "carnivore")
o.ajoute_espece("truite", "herbivore")   # herbe -> truite -> saumon => saumon niveau 3
o.ajoute_espece("ours", "omnivore")
o.ajoute_lien("herbe", "truite")
o.ajoute_lien("truite", "saumon")
o.ajoute_lien("herbe", "ours")
o.ajoute_lien("saumon", "ours")
check(o.niveau_trophique("saumon") == 3.0, "omnivore : niveau(saumon) = 3 (préalable)")
check(o.niveau_trophique("ours") == 3.0, "omnivore : ours(herbe1, saumon3) = 1 + (1+3)/2 = 3.0")

o2 = RT.Reseau()
o2.ajoute_espece("herbe", "producteur")
o2.ajoute_espece("lapin", "herbivore")
o2.ajoute_espece("ours", "omnivore")
o2.ajoute_lien("herbe", "lapin")
o2.ajoute_lien("herbe", "ours")
o2.ajoute_lien("lapin", "ours")
check(o2.niveau_trophique("ours") == 2.5, "omnivore : ours(herbe1, lapin2) = 1 + (1+2)/2 = 2.5 (FRACTIONNAIRE)")
check(isinstance(o2.niveau_trophique("ours"), float), "niveau est un float")

# ── 4) PRODUCTEURS / PRÉDATEURS SOMMET ──
check(r.producteurs() == ["herbe"], "réseau : producteurs = [herbe]")
check(r.predateurs_sommet() == ["chouette", "renard"], "réseau : sommets = chouette, renard (rien ne les mange)")
check(c.producteurs() == ["herbe"], "chaîne : producteurs = [herbe]")
check(c.predateurs_sommet() == ["renard"], "chaîne : sommet = renard")

# ── 5) CHAÎNES (chemins simples) ──
ch = r.chaines("herbe", "renard")
check(len(ch) == 2, "réseau : 2 chemins herbe -> renard")
check(("herbe", "lapin", "renard") in ch, "chemin herbe->lapin->renard présent")
check(("herbe", "souris", "renard") in ch, "chemin herbe->souris->renard présent")
check(r.chaines("herbe", "chouette") == [("herbe", "souris", "chouette")], "unique chemin herbe->chouette")
check(r.chaines("renard", "herbe") == [], "aucun chemin à contre-courant renard->herbe")
check(c.chaines("herbe", "renard") == [("herbe", "lapin", "renard")], "chaîne : unique chemin")

# ── 6) LONGUEUR DE CHAÎNE MAX (nombre d'espèces) ──
check(c.longueur_chaine_max() == 3, "chaîne : longueur max = 3 espèces")
check(r.longueur_chaine_max() == 3, "réseau : longueur max = 3 espèces")
vide = RT.Reseau()
check(vide.longueur_chaine_max() == 0, "réseau vide : longueur max = 0")
solo = RT.Reseau()
solo.ajoute_espece("algue", "producteur")
check(solo.longueur_chaine_max() == 1, "une espèce isolée : longueur max = 1")

# ── 7) EFFET DE RETRAIT (sans ressource, direct) — ANCRE 'herbe' -> {lapin, souris} ──
check(r.effet_retrait("herbe") == ["lapin", "souris"], "retrait herbe -> lapin et souris sans ressource")
check(r.effet_retrait("souris") == ["chouette"], "retrait souris -> chouette sans ressource (renard garde lapin)")
check(r.effet_retrait("lapin") == [], "retrait lapin -> personne privé (renard garde souris)")
check(c.effet_retrait("herbe") == ["lapin"], "chaîne : retrait herbe -> lapin sans ressource")

# ── 8) ESPÈCES CLÉS (retrait effectif + comptage, EXACT) ──
check(r.especes_cles() == ["herbe"], "réseau : espèce clé = herbe (déconnecte les 4 autres)")
check(c.especes_cles() == ["herbe"], "chaîne : espèce clé = herbe")

# scénario de départage : deux producteurs, un pont unique
pont = RT.Reseau()
pont.ajoute_espece("a", "producteur")
pont.ajoute_espece("b", "herbivore")
pont.ajoute_espece("c", "carnivore")
pont.ajoute_lien("a", "b")
pont.ajoute_lien("b", "c")
# retrait de 'a' déconnecte b et c (2) ; retrait de 'b' déconnecte c (1) ; a est donc clé
check(pont.especes_cles() == ["a"], "pont : clé = a (déconnecte b et c)")

# ── 9) INVARIANT CYCLE -> ValueError 'cycle trophique : niveau indéfini' ──
cyc = RT.Reseau()
cyc.ajoute_espece("a", "carnivore")
cyc.ajoute_espece("b", "carnivore")
cyc.ajoute_lien("a", "b")
cyc.ajoute_lien("b", "a")
check(leve(cyc.niveau_trophique, "a"), "cycle a<->b : niveau -> ValueError")
check(leve(cyc.longueur_chaine_max), "cycle : longueur_chaine_max -> ValueError")
try:
    cyc.niveau_trophique("a")
    msg_ok = False
except ValueError as e:
    msg_ok = "cycle trophique" in str(e)
check(msg_ok, "message de cycle explicite")

# ── 10) INVARIANT producteur sans proie ──
p = RT.Reseau()
p.ajoute_espece("soleil", "producteur")
p.ajoute_espece("algue", "producteur")
check(leve(p.ajoute_lien, "algue", "soleil"), "producteur prédateur -> ValueError (pas de proie)")

# ── 11) SOUNDNESS — espèce inconnue ──
check(leve(r.niveau_trophique, "dragon"), "niveau espèce inconnue -> ValueError")
check(leve(r.effet_retrait, "dragon"), "effet_retrait inconnue -> ValueError")
check(leve(r.chaines, "dragon", "renard"), "chaines depuis inconnue -> ValueError")
check(leve(r.chaines, "herbe", "dragon"), "chaines vers inconnue -> ValueError")
check(leve(r.ajoute_lien, "herbe", "dragon"), "lien vers inconnue -> ValueError")
check(leve(r.ajoute_lien, "dragon", "renard"), "lien depuis inconnue -> ValueError")

# ── 12) SOUNDNESS — type invalide / doublon ──
z = RT.Reseau()
check(leve(z.ajoute_espece, "x", "super-predateur"), "type invalide -> ValueError")
check(leve(z.ajoute_espece, "x", "PRODUCTEUR"), "type casse différente -> ValueError")
z.ajoute_espece("x", "herbivore")
check(leve(z.ajoute_espece, "x", "carnivore"), "espèce déjà déclarée -> ValueError")

# ── 13) SOUNDNESS — types de nom invalides (bool / str vide / None / nombre) ──
check(leve(z.ajoute_espece, True, "herbivore"), "nom bool -> ValueError")
check(leve(z.ajoute_espece, "", "herbivore"), "nom vide -> ValueError")
check(leve(z.ajoute_espece, None, "herbivore"), "nom None -> ValueError")
check(leve(z.ajoute_espece, 3, "herbivore"), "nom numérique -> ValueError")
check(leve(z.ajoute_espece, "y", True), "type bool -> ValueError")
check(leve(z.niveau_trophique, True), "niveau nom bool -> ValueError")
check(leve(z.chaines, "", "x"), "chaines nom vide -> ValueError")

# ── 14) DÉTERMINISME ──
check(r.niveau_trophique("renard") == r.niveau_trophique("renard"), "déterminisme niveau")
check(r.chaines("herbe", "renard") == r.chaines("herbe", "renard"), "déterminisme chaines")
check(r.especes_cles() == r.especes_cles(), "déterminisme especes_cles")
check(r.effet_retrait("herbe") == r.effet_retrait("herbe"), "déterminisme effet_retrait")
check(r.longueur_chaine_max() == r.longueur_chaine_max(), "déterminisme longueur_chaine_max")

print(f"\n=== valide_reseau_trophique : {ok}/{ok+ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
