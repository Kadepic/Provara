"""
VALIDE bilan_energetique.py — held-out ADVERSE.

ANCRES EXTERNES NON CIRCULAIRES (valeurs écrites EN DUR, calculées À LA MAIN, jamais recalculées
par le module testé) :
  • Moteur électrique 100 W entrant, 30 W utile (sortant), 70 W pertes : à la main
    100 − 30 − 70 = 0 -> écart 0, conserve True ; rendement = 30/100 = 0.30 (arithmétique élémentaire).
  • Système 100 W entrant / 120 W sortant : 120/100 = 1.2 > 1 -> rendement -> ValueError
    (1er principe de la thermodynamique, Clausius 1850 : on ne crée pas d'énergie).
  • Système 100 entrant / 30 sortant / 50 pertes : à la main 100 − 30 − 50 = +20 -> EXCÉDENT
    non expliqué de 20 W, nommé explicitement (jamais absorbé en silence).
  • flux_manquant : entrant 100, sortant 30, pertes None -> à la main 100 − 30 = 70 W déduits.
  • Ampoule LED 10 W électriques, 2 W lumière, 8 W chaleur (ordre de grandeur réel d'une LED du
    commerce, efficacité ~20 %) : rendement = 2/10 = 0.20, et 10 − 2 − 8 = 0 -> conserve True.
  • Bouilloire 2200 W secteur, 2000 W stockés dans l'eau, 200 W pertes parois : 2200−2000−200 = 0.
  • Déficit : 100 entrant / 150 sortant -> 100 − 150 = −50 -> DÉFICIT non expliqué de 50 W.
  • IEEE754 : 0.3 entrant / 0.1 sortant / 0.2 pertes -> à la main (décimal) 0.3 − 0.1 − 0.2 = 0
    EXACTEMENT ; le résidu binaire (~−5.6e-17, propriété connue du double IEEE754) est du BRUIT,
    pas une anomalie -> écart 0, conserve(0.0) True, bilan_incoherent None. Rendement 0.1/0.3 = 1/3
    ≈ 0.3333333333 (division à la main, 10 chiffres).
  • Déficit RÉEL minuscule : 0.3 − 0.1 − 0.2 − 1e-9 = −1e-9 (à la main) -> DÉFICIT nommé (le
    plancher, ~1e-15 W à cette échelle, ne masque pas une vraie anomalie).
  • Bilan en déficit SOUS-unitaire : 100 entrant / 90 sortant / 50 pertes -> 90+50 = 140 > 100
    (création de 40 W, impossible, 1er principe) -> rendement -> ValueError (jamais η=0.9 plausible).

SOUNDNESS : valeur négative, sens inconnu, système vide, tol < 0, rendement > 1, entrant nul,
nom vide/dupliqué, bool/str/NaN/inf, 0 ou ≥ 2 inconnues, déduction négative, bilan en déficit
(rendement) -> ValueError.
"""
import math
import warnings

import bilan_energetique as B

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


def proche(x, attendu, tol=1e-9):
    return x is not None and abs(x - attendu) <= tol


def systeme(flux=(), pertes=()):
    """Petit constructeur : flux = (nom, valeur, sens)*, pertes = (nom, valeur)*."""
    s = B.Systeme()
    for (n, v, sens) in flux:
        s.ajoute_flux(n, v, sens)
    for (n, v) in pertes:
        s.ajoute_perte(n, v)
    return s


# ── 1) ANCRE : moteur 100 W entrant, 30 W utile, 70 W pertes (100−30−70 = 0 à la main) ──
moteur = systeme([("secteur", 100.0, "entrant"), ("arbre", 30.0, "sortant")], [("chaleur", 70.0)])
b = moteur.bilan()
check(proche(b["entrant"], 100.0), "moteur : entrant = 100 W")
check(proche(b["sortant"], 30.0), "moteur : sortant = 30 W")
check(proche(b["pertes"], 70.0), "moteur : pertes = 70 W")
check(proche(b["stocke"], 0.0), "moteur : stocke = 0 W")
check(proche(b["ecart"], 0.0), "moteur : écart = 100−30−70 = 0 W (calcul à la main)")
check(moteur.conserve(0.0) is True, "moteur : conserve(0) = True")
check(moteur.bilan_incoherent() is None, "moteur : bilan_incoherent = None (bouclé)")
check(proche(moteur.rendement(), 0.30), "moteur : rendement = 30/100 = 0.30 (à la main)")

# ── 2) ANCRE : 100 W entrant / 120 W sortant -> rendement 1.2 > 1 -> ValueError (1er principe) ──
sur_unite = systeme([("in", 100.0, "entrant"), ("out", 120.0, "sortant")])
check(leve(sur_unite.rendement), "rendement 120/100 = 1.2 > 1 -> ValueError (1er principe)")
try:
    sur_unite.rendement()
    check(False, "rendement > 1 doit lever")
except ValueError as e:
    check("1" in str(e) and "principe" in str(e).lower(), "message rendement > 1 cite le 1er principe")

# ── 3) ANCRE : 100 / 30 / 50 -> écart = +20 W, EXCÉDENT nommé et chiffré ──
excedent = systeme([("in", 100.0, "entrant"), ("out", 30.0, "sortant")], [("frottements", 50.0)])
check(proche(excedent.bilan()["ecart"], 20.0), "100−30−50 = +20 W d'écart (à la main)")
check(excedent.conserve(1.0) is False, "écart 20 > tol 1 -> conserve = False")
msg = excedent.bilan_incoherent()
check(isinstance(msg, str) and "EXCÉDENT" in msg, "bilan_incoherent nomme un EXCÉDENT")
check(msg is not None and "20" in msg, "l'excédent est chiffré : 20 W dans le message")
check(excedent.conserve(20.0) is True, "tol = 20 exactement -> |écart| ≤ tol -> True")

# ── 4) ANCRE : déficit 100 entrant / 150 sortant -> −50 W, DÉFICIT nommé ──
deficit = systeme([("in", 100.0, "entrant"), ("out", 150.0, "sortant")])
check(proche(deficit.bilan()["ecart"], -50.0), "100−150 = −50 W d'écart (à la main)")
msg_d = deficit.bilan_incoherent()
check(isinstance(msg_d, str) and "DÉFICIT" in msg_d, "bilan_incoherent nomme un DÉFICIT")
check(msg_d is not None and "50" in msg_d, "le déficit est chiffré : 50 W dans le message")

# ── 5) ANCRE : flux_manquant — entrant 100, sortant 30, pertes None -> 70 W (100−30 à la main) ──
manque = systeme([("in", 100.0, "entrant"), ("out", 30.0, "sortant")], [("pertes", None)])
d = manque.flux_manquant()
check(proche(d["valeur_watt"], 70.0), "pertes déduites = 100−30 = 70 W (à la main)")
check(d["nom"] == "pertes" and d["sens"] == "perte", "la déduction nomme le flux et son sens")

# entrant inconnu : sortant 30 + pertes 70 -> entrant déduit = 100 W (30+70 à la main)
manque_in = systeme([("in", None, "entrant"), ("out", 30.0, "sortant")], [("chaleur", 70.0)])
check(proche(manque_in.flux_manquant()["valeur_watt"], 100.0), "entrant déduit = 30+70 = 100 W")

# stocké inconnu : 2200 entrant, 200 pertes -> stocké déduit = 2000 W (2200−200 à la main)
manque_st = systeme([("secteur", 2200.0, "entrant"), ("eau", None, "stocke")], [("parois", 200.0)])
check(proche(manque_st.flux_manquant()["valeur_watt"], 2000.0), "stocké déduit = 2200−200 = 2000 W")

# ── 6) ANCRE : deux None -> sous-déterminé -> ValueError ──
deux = systeme([("in", 100.0, "entrant"), ("out", None, "sortant")], [("pertes", None)])
check(leve(deux.flux_manquant), "2 inconnues -> ValueError (sous-déterminé)")
try:
    deux.flux_manquant()
    check(False, "2 inconnues doit lever")
except ValueError as e:
    check("sous-déterminé" in str(e) and "2 inconnues" in str(e), "message : 'sous-déterminé : 2 inconnues, 1 équation'")
check(leve(deux.bilan), "bilan avec inconnues -> ValueError (pas de devinette)")
check(leve(deux.conserve, 0.0), "conserve avec inconnues -> ValueError")
check(leve(deux.rendement), "rendement avec inconnues -> ValueError")

# ── 7) ANCRE : LED 10 W, 2 W lumière, 8 W chaleur -> rendement 0.20, conserve True ──
led = systeme([("electrique", 10.0, "entrant"), ("lumiere", 2.0, "sortant")], [("chaleur", 8.0)])
check(proche(led.rendement(), 0.20), "LED : rendement = 2/10 = 0.20 (à la main)")
check(led.conserve(0.0) is True, "LED : 10−2−8 = 0 -> conserve True")

# ── 8) ANCRE : bouilloire — le flux 'stocke' compte dans le bilan ──
bouilloire = systeme([("secteur", 2200.0, "entrant"), ("eau", 2000.0, "stocke")], [("parois", 200.0)])
check(proche(bouilloire.bilan()["ecart"], 0.0), "bouilloire : 2200−0−200−2000 = 0 (à la main)")
check(proche(bouilloire.bilan()["stocke"], 2000.0), "bouilloire : stocke = 2000 W")

# ── 9) AVERTISSEMENT : rendement sans perte déclarée -> UserWarning ; avec pertes -> silence ──
sans_perte = systeme([("in", 100.0, "entrant"), ("out", 80.0, "sortant")])
with warnings.catch_warnings(record=True) as w:
    warnings.simplefilter("always")
    r = sans_perte.rendement()
    check(proche(r, 0.80), "rendement sans perte = 80/100 = 0.80 (à la main)")
    check(len(w) == 1 and issubclass(w[0].category, UserWarning), "aucune perte déclarée -> UserWarning émis")
with warnings.catch_warnings(record=True) as w:
    warnings.simplefilter("always")
    led.rendement()
    check(len(w) == 0, "pertes déclarées -> aucun avertissement")

# ── 10) SANKEY TEXTUEL : contient les noms, les valeurs et l'écart ; aucune dépendance graphique ──
sk = moteur.diagramme_sankey_texte()
check(isinstance(sk, str) and "secteur" in sk and "arbre" in sk and "chaleur" in sk,
      "sankey : les trois flux nommés apparaissent")
check("100" in sk and "30" in sk and "70" in sk, "sankey : les valeurs 100/30/70 apparaissent")
check("ecart=0" in sk, "sankey : l'écart (0) est affiché")
check("█" in sk, "sankey : barres proportionnelles présentes")
check(leve(moteur.diagramme_sankey_texte, 0), "sankey : largeur 0 -> ValueError")
check(leve(moteur.diagramme_sankey_texte, True), "sankey : largeur bool -> ValueError")

# ── 11) SOUNDNESS — valeurs et sens invalides ──
s = B.Systeme()
check(leve(s.ajoute_flux, "in", -5.0, "entrant"), "flux entrant négatif -> ValueError")
check(leve(s.ajoute_flux, "out", -1.0, "sortant"), "flux sortant négatif -> ValueError")
check(leve(s.ajoute_perte, "p", -0.1), "perte négative -> ValueError")
check(leve(s.ajoute_flux, "in", 10.0, "lateral"), "sens inconnu 'lateral' -> ValueError")
check(leve(s.ajoute_flux, "in", 10.0, 3), "sens non-str -> ValueError")
check(leve(s.ajoute_flux, "in", True, "entrant"), "valeur bool -> ValueError (True n'est pas 1 W)")
check(leve(s.ajoute_flux, "in", "10", "entrant"), "valeur str -> ValueError")
check(leve(s.ajoute_flux, "in", float("nan"), "entrant"), "valeur NaN -> ValueError")
check(leve(s.ajoute_flux, "in", float("inf"), "entrant"), "valeur inf -> ValueError")
check(leve(s.ajoute_flux, "", 10.0, "entrant"), "nom vide -> ValueError")
check(leve(s.ajoute_flux, 42, 10.0, "entrant"), "nom non-str -> ValueError")
s.ajoute_flux("unique", 10.0, "entrant")
check(leve(s.ajoute_flux, "unique", 5.0, "sortant"), "nom dupliqué -> ValueError (ambiguïté)")
check(leve(s.ajoute_perte, "unique", 5.0), "nom de perte dupliqué avec un flux -> ValueError")

# ── 12) SOUNDNESS — système vide, tolérance, entrant nul, aucune inconnue ──
vide = B.Systeme()
check(leve(vide.bilan), "système vide : bilan -> ValueError")
check(leve(vide.conserve, 0.0), "système vide : conserve -> ValueError")
check(leve(vide.rendement), "système vide : rendement -> ValueError")
check(leve(vide.diagramme_sankey_texte), "système vide : sankey -> ValueError")
check(leve(vide.flux_manquant), "système vide : flux_manquant -> ValueError")
check(leve(moteur.conserve, -0.1), "tol < 0 -> ValueError")
check(leve(moteur.conserve, True), "tol bool -> ValueError")
check(leve(moteur.conserve, float("nan")), "tol NaN -> ValueError")
check(leve(moteur.bilan_incoherent, -1.0), "bilan_incoherent(tol<0) -> ValueError")
sans_entree = systeme([("out", 10.0, "sortant")])
check(leve(sans_entree.rendement), "entrant = 0 W : rendement -> ValueError (division refusée)")
check(leve(moteur.flux_manquant), "0 inconnue : flux_manquant -> ValueError (rien à déduire)")

# ── 13) SOUNDNESS — déduction négative refusée (flux déclarés incohérents) ──
impossible = systeme([("in", 100.0, "entrant"), ("out", 150.0, "sortant")], [("pertes", None)])
check(leve(impossible.flux_manquant), "pertes déduites = 100−150 = −50 W -> ValueError (incohérent)")

# ── 14) DÉTERMINISME ──
check(moteur.bilan() == moteur.bilan(), "déterminisme : bilan")
check(moteur.diagramme_sankey_texte() == moteur.diagramme_sankey_texte(), "déterminisme : sankey")
check(moteur.rendement() == moteur.rendement(), "déterminisme : rendement")
m2 = systeme([("secteur", 100.0, "entrant"), ("arbre", 30.0, "sortant")], [("chaleur", 70.0)])
check(m2.bilan() == moteur.bilan(), "déterminisme : deux systèmes identiques, même bilan")

# ── 15) flux_manquant ne MUTE pas le système (fonction de lecture) ──
avant = len(manque._inconnues())
manque.flux_manquant()
check(len(manque._inconnues()) == avant, "flux_manquant ne modifie pas le système")

# ── 16) ANCRE IEEE754 : 0.3 entrant / 0.1 sortant / 0.2 pertes — à la main 0.3−0.1−0.2 = 0 ──
# En binaire double, 0.3 − 0.1 − 0.2 laisse un résidu ~−5.6e-17 (propriété connue d'IEEE754) :
# c'est du BRUIT de représentation, pas de la physique. L'affirmer comme anomalie = FAUX POSITIF.
bruit = systeme([("in", 0.3, "entrant"), ("out", 0.1, "sortant")], [("chaleur", 0.2)])
check(bruit.bilan()["ecart"] == 0.0, "0.3−0.1−0.2 : écart rapporté = 0.0 (résidu binaire = bruit)")
check(bruit.conserve(0.0) is True, "0.3/0.1/0.2 : conserve(0.0) = True (pas de faux positif IEEE754)")
check(bruit.bilan_incoherent() is None, "0.3/0.1/0.2 : bilan_incoherent() = None (bouclé)")
check(bruit.bilan_incoherent(0.0) is None, "0.3/0.1/0.2 : bilan_incoherent(0.0) = None")
check(proche(bruit.rendement(), 0.3333333333, 1e-9),
      "0.3/0.1/0.2 : rendement = 0.1/0.3 = 1/3 ≈ 0.3333333333 (division à la main, 10 chiffres)")
check(bruit.bilan() == bruit.bilan(), "déterminisme : bilan sur valeurs non dyadiques")

# ── 17) ANCRE IEEE754 (cas adverse exact) : 0.3 entrant / 0.1 et 0.2 sortant ──
# à la main : 0.1 + 0.2 = 0.3 sortent, 0.3 entre -> bouclé, rendement = 0.3/0.3 = 1 exactement.
bruit2 = systeme([("in", 0.3, "entrant"), ("a", 0.1, "sortant"), ("b", 0.2, "sortant")])
check(bruit2.bilan_incoherent() is None, "0.3 in / 0.1+0.2 out : bilan_incoherent = None")
check(bruit2.conserve(0.0) is True, "0.3 in / 0.1+0.2 out : conserve(0.0) = True")
with warnings.catch_warnings(record=True) as w:
    warnings.simplefilter("always")
    r2 = bruit2.rendement()
check(r2 == 1.0, "0.3 in / 0.3 out : rendement = 1.0 exactement (l'excès binaire >1 est du bruit)")
check("ecart=0" in bruit2.diagramme_sankey_texte(), "sankey : écart affiché 0 sur système non dyadique")

# ── 18) Le plancher ne masque PAS un vrai écart : déficit réel de 1e-9 W ──
# à la main : 0.3 − 0.1 − 0.2 − 1e-9 = −1e-9, très au-dessus du plancher (~1e-15 à cette échelle).
petit_deficit = systeme([("in", 0.3, "entrant"), ("a", 0.1, "sortant"), ("b", 0.2, "sortant")],
                        [("fuite", 1e-9)])
check(petit_deficit.conserve(0.0) is False, "déficit réel 1e-9 W : conserve(0.0) = False (non masqué)")
msg_p = petit_deficit.bilan_incoherent()
check(isinstance(msg_p, str) and "DÉFICIT" in msg_p, "déficit réel 1e-9 W : DÉFICIT nommé")
check(petit_deficit.conserve(1e-8) is True, "tol 1e-8 > déficit 1e-9 : conserve = True")
check(petit_deficit.conserve(1e-12) is False, "tol 1e-12 < déficit 1e-9 : conserve = False")
check(leve(petit_deficit.rendement), "rendement sur déficit réel (même minuscule) -> ValueError")

# ── 19) ANCRE (défaut adverse) : 100 in / 90 out / 50 pertes -> déficit 40 W -> rendement REFUSE ──
# à la main : 90 + 50 = 140 > 100 -> le système CRÉE 40 W (impossible, 1er principe). η = 0.9 serait
# plausible mais FAUX : l'abstention est exigée.
cree = systeme([("in", 100.0, "entrant"), ("out", 90.0, "sortant")], [("chaleur", 50.0)])
check(leve(cree.rendement), "100/90/50 : sortant+pertes = 140 > entrant = 100 -> rendement -> ValueError")
try:
    cree.rendement()
    check(False, "rendement sur bilan en déficit doit lever")
except ValueError as e:
    check("principe" in str(e).lower(), "message : cite le premier principe")
    check("40" in str(e), "message : chiffre le déficit (40 W)")
check("DÉFICIT" in (cree.bilan_incoherent() or ""), "bilan_incoherent nomme le même DÉFICIT")
# déficit via le stockage : 100 in / 150 stockés -> −50 W ; η = 0/100 = 0 mais système impossible
stock_impossible = systeme([("in", 100.0, "entrant"), ("batterie", 150.0, "stocke")])
check(leve(stock_impossible.rendement), "100 in / 150 stockés : déficit -> rendement -> ValueError")
# l'EXCÉDENT (pertes non déclarées), lui, reste toléré : η = utile/entrant n'en dépend pas
check(proche(excedent.rendement(), 0.30), "excédent 20 W : rendement = 30/100 = 0.30 rendu (pas une violation)")

# ── 20) flux_manquant : la déduction sous le plancher est NULLE, pas 'incohérente' ──
# à la main : 0.3 − 0.1 − 0.2 = 0 -> la perte manquante vaut 0 W (le résidu −5.6e-17 est du bruit,
# le refuser comme 'flux incohérents' serait un faux positif).
manque_bruit = systeme([("in", 0.3, "entrant"), ("a", 0.1, "sortant"), ("b", 0.2, "sortant")],
                       [("p", None)])
dz = manque_bruit.flux_manquant()
check(dz["valeur_watt"] == 0.0, "déduction 0.3−0.3 : 0.0 W exactement (bruit clampé)")
check(dz["nom"] == "p" and dz["sens"] == "perte", "la déduction nulle nomme bien le flux")
check(leve(impossible.flux_manquant), "déduction −50 W réelle : toujours ValueError (clamp inoffensif)")

print(f"\n=== valide_bilan_energetique : {ok}/{ok+ko} ===")
import sys; sys.exit(0 if ko == 0 else 1)
