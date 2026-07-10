"""VALIDE besoin.py — couche objectif/besoin du moteur d'invention. FAUX=0, adverse.

Vérifie : (1) le REFRAMING (le but réel = évacuer les ~100 W du corps, pas refroidir l'air) ; (2) la décomposition
en canaux physiques établis ; (3) l'ASYMÉTRIE contrat d'atome : coherence_physique RÉFUTE l'impossible et ne
promeut JAMAIS en fait (les principes cohérents restent des SUPPOSITIONS) ; (4) le besoin inconnu -> HORS (le manque
visible) ; (5) le transfert inter-domaines (stratégies naturelles réduites à des leviers) ; (6) le pont physique."""
import atome as A
import besoin as B

ok = 0
ko = 0


def check(c, l):
    global ok, ko
    if c:
        ok += 1
    else:
        ko += 1
        print(f"  FAIL: {l}")


# ── 1) REFRAMING + 2) décomposition ──
d = B.decompose("rafraichir une piece")
check(d["statut"] == "decompose", "besoin connu -> decompose")
check("corps" in d["objectif_reel"].lower() and "100" in d["objectif_reel"], "objectif réel = évacuer ~100 W du corps")
check(d["charge_corps_W"] == 100, "charge du corps ~100 W")
canaux = {c.canal for c in d["canaux"]}
check(canaux == {"rayonnement", "conduction", "convection", "evaporation"}, f"4 canaux d'échange du corps ({canaux})")
check(all(c.grandeur == "chaleur" for c in d["canaux"]), "chaque canal nomme la grandeur physique (chaleur)")
# le mouvement d'air (convection) est le seul non silencieux -> cohérent avec l'exigence de silence
conv = [c for c in d["canaux"] if c.canal == "convection"][0]
check(conv.silencieux is False, "convection (mouvement d'air) marquée NON silencieuse (ventilateur = bruit)")
ray = [c for c in d["canaux"] if c.canal == "rayonnement"][0]
check(ray.silencieux is True, "rayonnement (surface froide) silencieux")

# ── 3) ASYMÉTRIE : réfute l'impossible, ne promeut jamais en fait ──
pr = B.principes("rafraichir une piece")
check(pr["statut"] == "principes", "principes pour besoin connu")
par_nom = {e["nom"]: e for e in pr["liste"]}
# les impossibles -> atome RÉFUTÉ
coolzy = par_nom["boîte fermée sans évacuation (type Coolzy)"]
check(coolzy["atome"].statut == A.REFUTE, "boîte fermée sans rejet -> RÉFUTÉ (2nd principe)")
check(A.est_refute(coolzy["atome"].contenu), "contenu réfuté enregistré dans la garde anti-blanchiment")
carnot = par_nom["pompe magique COP 40 (ΔT 10 K)"]
check(carnot["atome"].statut == A.REFUTE, "COP 40 > Carnot -> RÉFUTÉ")
# les cohérents -> SUPPOSITION (JAMAIS FAIT) + confiance dans ]0,1[
for nom in ("échange direct avec l'eau du réseau (~15 °C)", "magnétocalorique (réfrigération magnétique)",
            "compression de vapeur (clim classique)"):
    e = par_nom[nom]
    check(e["atome"].statut == A.SUPPOSITION, f"{nom} -> SUPPOSITION (cohérent ≠ prouvé)")
    check(0.0 < e["atome"].confiance < 1.0, f"{nom} confiance dans ]0,1[")
# INVARIANT CLÉ : coherence_physique ne promeut JAMAIS un principe en FAIT
check(all(e["atome"].statut in (A.SUPPOSITION, A.REFUTE) for e in pr["liste"]),
      "aucun principe promu en FAIT (la cohérence n'est pas une preuve d'efficacité)")
# effets sous-exploités présents (magnéto/élasto/électro caloriques)
noms = set(par_nom)
check(any("magnétocalorique" in n for n in noms) and any("mécanocalorique" in n for n in noms)
      and any("électrocalorique" in n for n in noms), "effets caloriques sous-exploités présents")
# métadonnées silence/solide honnêtes
eau = par_nom["échange direct avec l'eau du réseau (~15 °C)"]
check(eau["silencieux"] is True and eau["solide_sans_gaz"] is True, "échange eau = silencieux + sans gaz")
clim = par_nom["compression de vapeur (clim classique)"]
check(clim["silencieux"] is False, "clim à compression marquée bruyante (référence à dépasser)")

# ── 4) besoin INCONNU -> HORS (le manque visible) ──
check(B.decompose("faire pousser des plantes")["statut"] == B.HORS, "besoin inconnu -> HORS (décompose)")
check(B.principes("cuire un gateau")["statut"] == B.HORS, "besoin inconnu -> HORS (principes)")
check(B.HORS in B.objectif_reel("voyager dans le temps"), "objectif d'un besoin inconnu -> HORS")

# ── 5) transfert inter-domaines (stratégies naturelles) ──
nat = B.strategies_naturelles()
check(len(nat) >= 4, "plusieurs stratégies naturelles")
check(any("forêt" in s["exemple"] for s in nat), "la forêt est une stratégie répertoriée")
check(all(s["leviers"] and s["lecon"] for s in nat), "chaque stratégie réduite à des leviers + une leçon")

# ── 6) pont physique vers substrat_physique ──
ch = B.chaines_physiques(sources=("magnetisme", "lumiere"), cible="chaleur")
check(any(c["source"] == "magnetisme" and c["statut"] for c in ch), "pont substrat_physique renvoie un statut")
check(B.chaines_physiques(sources=("grandeur_bidon",), cible="chaleur")[0]["statut"] == B.HORS,
      "grandeur inconnue -> HORS (pas d'invention à l'aveugle)")

# ── déterminisme ──
check(B.decompose("rafraichir une piece")["objectif_reel"] == B.decompose("rafraichir une piece")["objectif_reel"],
      "décomposition déterministe")

# ── 7) DEUXIÈME DOMAINE : chauffage / confort d'hiver (le symétrique, via le registre — mêmes exigences) ──
dh = B.decompose("chauffer une piece")
check(dh["statut"] == "decompose", "besoin chauffage connu -> decompose")
check("corps" in dh["objectif_reel"].lower() and "100" in dh["objectif_reel"] and "source" in dh["objectif_reel"].lower(),
      "objectif réel hiver = le corps est une SOURCE de ~100 W (asymétrie, pas un copier-coller du cooling)")
check(dh["production_corps_W"] == 100, "production du corps ~100 W (extras propres au domaine)")
ch_canaux = {c.canal for c in dh["canaux"]}
check(ch_canaux == {"rayonnement", "conduction", "convection", "evaporation"},
      f"mêmes 4 canaux physiologiques, sens inversé ({ch_canaux})")
check(all(c.silencieux is True for c in dh["canaux"]),
      "réduire une perte est passif -> tous les canaux hiver silencieux (l'asymétrie rend le silence gratuit)")
prh = B.principes("chauffer une piece")
check(prh["statut"] == "principes", "principes pour le chauffage")
ph = {e["nom"]: e for e in prh["liste"]}
# l'impossible est RÉFUTÉ : rendement > 1 (conservation) et COP > Carnot chauffage
r150 = ph["radiateur « à rendement 150 % »"]
check(r150["atome"].statut == A.REFUTE, "rendement 150 % -> RÉFUTÉ (conservation de l'énergie)")
check(A.est_refute(r150["atome"].contenu), "contenu réfuté (150 %) dans la garde anti-blanchiment")
pac40 = ph["PAC magique COP 40 (ΔT 20 K)"]
check(pac40["atome"].statut == A.REFUTE, "COP 40 chauffage > Carnot Th/(Th−Tc) ≈ 14,7 -> RÉFUTÉ")
# le cas LIMITE exact : rendement 1.0 n'est PAS une violation (tout le courant finit en chaleur, jamais plus)
resistif = ph["convecteur résistif (référence basse)"]
check(resistif["atome"].statut == A.SUPPOSITION, "rendement exactement 1.0 -> cohérent (cas limite, pas de faux positif)")
# les cohérents restent des SUPPOSITIONS, confiance dans ]0,1[ — jamais de FAIT
for nom in ("pompe à chaleur air/air (COP 3–4)", "superisolation + chaleur métabolique (igloo / Passivhaus)",
            "solaire passif (vitrage sud + masse, mur Trombe)"):
    e = ph[nom]
    check(e["atome"].statut == A.SUPPOSITION, f"{nom} -> SUPPOSITION (cohérent ≠ prouvé)")
    check(0.0 < e["atome"].confiance < 1.0, f"{nom} confiance dans ]0,1[")
check(all(e["atome"].statut in (A.SUPPOSITION, A.REFUTE) for e in prh["liste"]),
      "aucun principe de chauffage promu en FAIT")
# la portée nomme SON domaine (pas de fuite du cooling)
check("candidat pour chauffage_confort" in resistif["atome"].portee.condition,
      "portée des principes chauffage nommant chauffage_confort")
# pistes sous-exploitées présentes (miroirs hiver : caloriques, thermochimique, chaleur fatale)
noms_h = set(ph)
check(any("calorique" in n for n in noms_h) and any("thermochimique" in n for n in noms_h)
      and any("chaleur fatale" in n for n in noms_h), "pistes sous-exploitées hiver présentes")
# libellé nu ambigu -> HORS honnête (« chauffage » seul peut viser l'industriel, l'eau sanitaire…)
check(B.decompose("chauffage")["statut"] == B.HORS, "« chauffage » nu (ambigu) -> HORS")
# stratégies naturelles PROPRES au domaine (pas celles du cooling)
nath = B.strategies_naturelles("chauffer une piece")
check(len(nath) >= 4, "plusieurs stratégies naturelles hiver")
check(any("manchot" in s["exemple"] for s in nath), "les manchots (mutualisation) sont répertoriés")
check(not any("forêt" in s["exemple"] for s in nath), "pas de fuite des stratégies été vers l'hiver")
check(all(s["leviers"] and s["lecon"] for s in nath), "chaque stratégie hiver réduite à des leviers + une leçon")
# le cooling est INTACT après l'ajout du chauffage (isolation entre domaines réels)
check(B.decompose("rafraichir une piece")["charge_corps_W"] == 100
      and len(B.principes("rafraichir une piece")["liste"]) == 18,
      "le cooling est inchangé après l'ajout du domaine chauffage")

# ── 8) TROISIÈME DOMAINE : dessaler / purifier l'eau (loi DURE = travail minimal de séparation) ──
de = B.decompose("dessaler l eau de mer")
check(de["statut"] == "decompose", "besoin dessalement connu -> decompose")
check("minimal" in de["objectif_reel"].lower() and "salinite" in de["objectif_reel"].lower().replace("é", "e"),
      "objectif réel dessalement = payer au-dessus du travail minimal + apparier à la salinité")
check(de["salinite_mer_g_L"] == 35, "extras propres : salinité mer 35 g/L")
eau_canaux = {c.canal for c in de["canaux"]}
check(eau_canaux == {"pression", "changement de phase", "champ electrique", "affinite selective"},
      f"4 canaux de séparation ({eau_canaux})")
pre = B.principes("dessaler l eau de mer")
check(pre["statut"] == "principes", "principes pour le dessalement")
pe = {e["nom"]: e for e in pre["liste"]}
# l'IMPOSSIBLE est RÉFUTÉ par le travail minimal de séparation (pas une simple supposition)
sous = pe["osmose inverse « à 0,3 kWh/m³ pour l'eau de mer »"]
check(sous["atome"].statut == A.REFUTE, "0,3 kWh/m³ < plancher ~0,76 -> RÉFUTÉ (travail minimal)")
check(A.est_refute(sous["atome"].contenu), "contenu réfuté (0,3 kWh/m³) dans la garde anti-blanchiment")
passif = pe["dessalement passif « sans énergie »"]
check(passif["atome"].statut == A.REFUTE, "dessalement sans énergie -> RÉFUTÉ (entropie de mélange)")
# les procédés RÉELS au-dessus du plancher restent des SUPPOSITIONS (jamais des faits)
for nom in ("osmose inverse eau de mer (SWRO, référence)", "distillation multi-effet / MSF (thermique)",
            "électrodialyse (ED / EDR)", "membranes biomimétiques (aquaporines / graphène)"):
    e = pe[nom]
    check(e["atome"].statut == A.SUPPOSITION, f"{nom} -> SUPPOSITION (au-dessus du minimum, non prouvé efficace)")
    check(0.0 < e["atome"].confiance < 1.0, f"{nom} confiance dans ]0,1[")
check(all(e["atome"].statut in (A.SUPPOSITION, A.REFUTE) for e in pre["liste"]),
      "aucun principe de dessalement promu en FAIT")
# la portée nomme SON domaine
check("candidat pour dessalement_eau" in pe["osmose inverse eau de mer (SWRO, référence)"]["atome"].portee.condition,
      "portée des principes dessalement nommant dessalement_eau")
# la MÊME loi dure réfute la revendication sous-plancher, quelle que soit la base π (bar direct ou concentration)
import coherence_physique as COH
st_bar, _, loi_bar = COH.juge_dispositif({"type": "dessalement", "energie_kWh_par_m3": 0.3, "osmose_pression_bar": 27})
check(st_bar == COH.VIOLE and loi_bar == COH.L3, "juge : 0,3 kWh/m³ (π 27 bar) -> VIOLE via L3")
st_c, _, _ = COH.juge_dispositif({"type": "dessalement", "energie_kWh_par_m3": 0.5,
                                  "concentration_mol_par_L": 0.6, "facteur_vant_hoff": 2, "t_K": 298.15})
check(st_c == COH.VIOLE, "juge : plancher calculé depuis la concentration (van 't Hoff) réfute aussi")
# un procédé réel n'est JAMAIS réfuté (soundness : pas de faux positif)
st_ro, _, _ = COH.juge_dispositif({"type": "dessalement", "energie_kWh_par_m3": 3.0, "osmose_pression_bar": 27})
check(st_ro == COH.COHERENT_BORNE, "osmose inverse réelle (3 kWh/m³) -> COHÉRENT, jamais réfutée")
# pistes sous-exploitées présentes (congélation, chaleur fatale, biomimétique)
noms_e = set(pe)
check(any("congélation" in n for n in noms_e) and any("membranaire" in n for n in noms_e)
      and any("biomimétiques" in n for n in noms_e), "pistes sous-exploitées dessalement présentes")
# libellé ambigu (« purifier l'eau » = bactéries/turbidité) écarté du dessalement
check(B.decompose("purifier l eau")["statut"] == B.HORS, "« purifier l'eau » nu (ambigu) -> HORS")
# stratégies naturelles propres au domaine
nate = B.strategies_naturelles("dessaler l eau de mer")
check(len(nate) >= 4 and any("mangrove" in s["exemple"] for s in nate), "stratégies dessalement propres (mangrove)")
check(not any("forêt" in s["exemple"] for s in nate) and not any("manchot" in s["exemple"] for s in nate),
      "pas de fuite des stratégies froid/chaud vers l'eau")
# cooling ET chauffage restent INTACTS après le 3e domaine
check(B.decompose("rafraichir une piece")["charge_corps_W"] == 100
      and len(B.principes("rafraichir une piece")["liste"]) == 18
      and B.decompose("chauffer une piece")["production_corps_W"] == 100,
      "cooling et chauffage inchangés après l'ajout du dessalement (isolation)")

# ── 9) QUATRIÈME DOMAINE : stocker l'énergie (loi DÉJÀ jugeable — rendement aller-retour ≤ 1, SANS étendre le juge) ──
dg = B.decompose("stocker de l energie")
check(dg["statut"] == "decompose", "besoin stockage connu -> decompose")
check("temps" in dg["objectif_reel"].lower() and "conversion" in dg["objectif_reel"].lower(),
      "objectif réel stockage = décaler dans le TEMPS + minimiser les conversions")
check("rendement_aller_retour" in dg, "extras propres : rendement aller-retour")
en_canaux = {c.canal for c in dg["canaux"]}
check(en_canaux == {"chimique", "mecanique", "thermique", "electrostatique"},
      f"4 canaux = 4 formes de stockage ({en_canaux})")
prg = B.principes("stocker de l energie")
check(prg["statut"] == "principes", "principes pour le stockage")
pg = {e["nom"]: e for e in prg["liste"]}
# l'IMPOSSIBLE est RÉFUTÉ par la conservation (type `conversion` existant, PAS d'extension du juge)
over = pg["stockage « à rendement aller-retour 115 % »"]
check(over["atome"].statut == A.REFUTE, "rendement aller-retour 1,15 > 1 -> RÉFUTÉ (conservation)")
check(A.est_refute(over["atome"].contenu), "contenu réfuté (115 %) dans la garde anti-blanchiment")
perp = pg["batterie « auto-rechargeante » perpétuelle"]
check(perp["atome"].statut == A.REFUTE, "batterie auto-rechargeante -> RÉFUTÉ (mouvement perpétuel)")
# les technos RÉELLES (rendement < 1) restent des SUPPOSITIONS
for nom in ("batterie lithium-ion (référence)", "pompage-turbinage (STEP)",
            "hydrogène (électrolyse → pile/combustion)", "thermochimique saisonnier (hydrates de sels)"):
    e = pg[nom]
    check(e["atome"].statut == A.SUPPOSITION, f"{nom} -> SUPPOSITION (rendement < 1, non prouvé optimal)")
    check(0.0 < e["atome"].confiance < 1.0, f"{nom} confiance dans ]0,1[")
check(all(e["atome"].statut in (A.SUPPOSITION, A.REFUTE) for e in prg["liste"]),
      "aucun principe de stockage promu en FAIT")
check("candidat pour stockage_energie" in pg["batterie lithium-ion (référence)"]["atome"].portee.condition,
      "portée des principes stockage nommant stockage_energie")
# le cas limite rendement aller-retour = 1.0 (idéal, sans perte) n'est PAS une violation
import coherence_physique as COH
check(COH.juge_dispositif({"type": "conversion", "rendement": 1.0})[0] == COH.COHERENT_BORNE,
      "rendement aller-retour 1.0 (idéal) -> cohérent, pas réfuté")
# le levier « minimiser les conversions » présent + techno saisonnière (hydrogène/thermochimique)
noms_g = set(pg)
check(any("hydrogène" in n for n in noms_g) and any("thermochimique" in n for n in noms_g)
      and any("supercondensateur" in n for n in noms_g), "technos couvrant durée courte→saisonnière présentes")
# stratégies naturelles propres au domaine (graisse/ATP/graine/tendon)
natg = B.strategies_naturelles("stocker de l energie")
check(len(natg) >= 4 and any("graisse" in s["exemple"] for s in natg), "stratégies stockage propres (graisse)")
check(not any("mangrove" in s["exemple"] for s in natg) and not any("forêt" in s["exemple"] for s in natg),
      "pas de fuite des stratégies eau/froid vers le stockage")
# les TROIS domaines précédents restent INTACTS après le 4e (isolation)
check(len(B.principes("rafraichir une piece")["liste"]) == 18
      and B.decompose("chauffer une piece")["production_corps_W"] == 100
      and B.decompose("dessaler l eau de mer")["salinite_mer_g_L"] == 35,
      "cooling, chauffage et dessalement inchangés après l'ajout du stockage (isolation)")

# ── 10) REGISTRE DE DOMAINES (généralisation 2026-07-12) : ajouter un domaine = l'enregistrer, RIEN d'autre ──
check(B.domaines_connus() == ["rafraichissement_confort", "chauffage_confort", "dessalement_eau", "stockage_energie"],
      "quatre domaines modélisés (cooling, chauffage, dessalement, stockage), dans l'ordre d'enregistrement")
# on enregistre un domaine de TEST et on vérifie que TOUTES les fonctions publiques dispatchent vers lui
_TESTP = B._P("principe bidon", "faire X : mécanisme Y", {"type": "refroidissement", "cop": 2}, True, True,
              "puits", "test", 0.5, "base test")
_TESTC = B.Canal("canal_test", "chaleur", "levier test", True, "note test")
_TESTN = B._Nature("exemple test", ["levier a", "levier b"], "leçon test")
B.enregistre(B.Domaine(nom="besoin_test_xyz", aliases=frozenset({"besoin de test xyz"}),
                       objectif="objectif reel du test", canaux=[_TESTC], principes=[_TESTP],
                       strategies=[_TESTN], loi="loi test", extras={"param_test": 42}))
check("besoin_test_xyz" in B.domaines_connus(), "un domaine enregistré apparaît dans domaines_connus()")
dt = B.decompose("besoin de test xyz")
check(dt["statut"] == "decompose" and dt["objectif_reel"] == "objectif reel du test" and dt["param_test"] == 42,
      "decompose dispatche vers le nouveau domaine (objectif + extras propres)")
check(dt["loi"] == "loi test" and len(dt["canaux"]) == 1, "canaux et loi du nouveau domaine servis")
pt = B.principes("besoin de test xyz")
check(pt["statut"] == "principes" and len(pt["liste"]) == 1
      and "candidat pour besoin_test_xyz" in pt["liste"][0]["atome"].portee.condition,
      "principes dispatche vers le nouveau domaine (portée nommant SON domaine)")
check(len(B.strategies_naturelles("besoin de test xyz")) == 1, "strategies dispatche vers le nouveau domaine")
# le cooling reste INTACT après l'ajout (pas de fuite entre domaines)
check(B.decompose("rafraichir une piece")["charge_corps_W"] == 100 and len(B.principes("rafraichir une piece")["liste"]) == 18,
      "le cooling est inchangé après l'ajout d'un domaine (isolation)")
# un besoin toujours inconnu reste HORS
check(B.decompose("teleporter un objet")["statut"] == B.HORS, "besoin hors registre -> HORS (inchangé)")

print(f"\n=== valide_besoin : {ok}/{ok + ko} ===")
import sys

sys.exit(0 if ko == 0 else 1)
