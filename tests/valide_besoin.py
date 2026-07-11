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

# ── 10) CINQUIÈME DOMAINE : capter le CO₂ (loi L3 GÉNÉRALISÉE au gaz dilué : R·T·ln(1/x)) ──
dc = B.decompose("capter le co2")
check(dc["statut"] == "decompose", "besoin capture CO₂ connu -> decompose")
check("dilu" in dc["objectif_reel"].lower() and "source" in dc["objectif_reel"].lower(),
      "objectif réel CO₂ = la dilution est l'ennemi + capter à la source concentrée")
check("fraction_co2_air" in dc, "extras propres : fraction CO₂ de l'air")
co2_canaux = {c.canal for c in dc["canaux"]}
check(co2_canaux == {"absorption chimique", "adsorption solide", "membrane", "mineralisation"},
      f"4 canaux de capture ({co2_canaux})")
prc = B.principes("capter le co2")
check(prc["statut"] == "principes", "principes pour la capture CO₂")
pc = {e["nom"]: e for e in prc["liste"]}
# l'IMPOSSIBLE (sous R·T·ln(1/x)) est RÉFUTÉ
sous_air = pc["DAC « à 10 kJ/mol depuis l'air ambiant »"]
check(sous_air["atome"].statut == A.REFUTE, "DAC 10 kJ/mol < plancher ~19,3 (420 ppm) -> RÉFUTÉ")
check(A.est_refute(sous_air["atome"].contenu), "contenu réfuté (DAC 10 kJ/mol) dans la garde")
sans_e = pc["capture du CO₂ de l'air « sans énergie »"]
check(sans_e["atome"].statut == A.REFUTE, "capture CO₂ sans énergie -> RÉFUTÉ (entropie de mélange)")
# les procédés RÉELS restent des SUPPOSITIONS
for nom in ("amines post-combustion (fumées, référence)", "sorbant solide DAC (capture dans l'air)",
            "altération accélérée / minéralisation (olivine, basalte)"):
    e = pc[nom]
    check(e["atome"].statut == A.SUPPOSITION, f"{nom} -> SUPPOSITION (au-dessus du minimum)")
    check(0.0 < e["atome"].confiance < 1.0, f"{nom} confiance dans ]0,1[")
check(all(e["atome"].statut in (A.SUPPOSITION, A.REFUTE) for e in prc["liste"]),
      "aucun principe de capture promu en FAIT")
check("candidat pour capture_co2" in pc["amines post-combustion (fumées, référence)"]["atome"].portee.condition,
      "portée des principes CO₂ nommant capture_co2")
# la loi GÉNÉRALISÉE : le juge réfute le gaz dilué sous R·T·ln(1/x), et jamais un procédé réel
st_air, _, loi_air = COH.juge_dispositif({"type": "separation", "fraction_molaire": 4.2e-4,
                                          "energie_kJ_par_mol": 10, "t_K": 298.15})
check(st_air == COH.VIOLE and loi_air == COH.L3, "juge : DAC 10 kJ/mol (420 ppm) -> VIOLE via L3")
st_real, _, _ = COH.juge_dispositif({"type": "separation", "fraction_molaire": 4.2e-4,
                                     "energie_kJ_par_mol": 230, "t_K": 298.15})
check(st_real == COH.COHERENT_BORNE, "DAC réel (230 kJ/mol) -> COHÉRENT, jamais réfuté")
# capter à la source (x élevé) abaisse le plancher : mêmes 10 kJ/mol seraient cohérents aux fumées
st_fumee, _, _ = COH.juge_dispositif({"type": "separation", "fraction_molaire": 0.12, "energie_kJ_par_mol": 10})
check(st_fumee == COH.COHERENT_BORNE, "10 kJ/mol aux fumées (x=0,12, plancher ~5,3) -> cohérent : la dilution est l'ennemi")
# pistes sous-exploitées (moisture-swing, électrochimique, minéralisation) présentes
noms_c = set(pc)
check(any("moisture-swing" in n for n in noms_c) and any("électrochimique" in n for n in noms_c)
      and any("minéralisation" in n for n in noms_c), "pistes sous-exploitées CO₂ présentes")
# stratégies naturelles propres (photosynthèse/biominéralisation/enzyme)
natc = B.strategies_naturelles("capter le co2")
check(len(natc) >= 4 and any("photosynthèse" in s["exemple"] for s in natc), "stratégies CO₂ propres (photosynthèse)")
check(not any("graisse" in s["exemple"] for s in natc) and not any("mangrove" in s["exemple"] for s in natc),
      "pas de fuite des stratégies stockage/eau vers la capture CO₂")
# les QUATRE domaines précédents restent INTACTS après le 5e (isolation)
check(len(B.principes("rafraichir une piece")["liste"]) == 18
      and B.decompose("chauffer une piece")["production_corps_W"] == 100
      and B.decompose("dessaler l eau de mer")["salinite_mer_g_L"] == 35
      and "rendement_aller_retour" in B.decompose("stocker de l energie"),
      "cooling, chauffage, dessalement et stockage inchangés après l'ajout de la capture CO₂ (isolation)")

# ── 11) SIXIÈME DOMAINE : eau potable de l'air (AWG) — loi séparation RÉUTILISÉE (x = HR, sans étendre le juge) ──
da = B.decompose("produire de l eau de l air")
check(da["statut"] == "decompose", "besoin AWG connu -> decompose")
check("humidit" in da["objectif_reel"].lower() and "diverge" in da["objectif_reel"].lower(),
      "objectif réel AWG = le rendement dépend d'abord de l'humidité (minimum diverge à sec)")
check("humidite_relative_moteur" in da, "extras propres : l'humidité relative est le moteur")
awg_canaux = {c.canal for c in da["canaux"]}
check(awg_canaux == {"refroidissement", "sorption", "interception", "membrane"}, f"4 canaux AWG ({awg_canaux})")
pra = B.principes("produire de l eau de l air")
pa = {e["nom"]: e for e in pra["liste"]}
# l'IMPOSSIBLE (sous R·T·ln(1/HR)) est RÉFUTÉ, et la SÉCHERESSE renchérit (deux réfutations distinctes)
sous_hr = pa["générateur d'eau « à 0,5 kJ/mol par 50 % d'humidité »"]
check(sous_hr["atome"].statut == A.REFUTE, "0,5 kJ/mol à 50 % HR < plancher ~1,72 -> RÉFUTÉ")
sec = pa["eau d'un air TRÈS SEC (5 % HR) « aussi peu cher qu'à 80 % »"]
check(sec["atome"].statut == A.REFUTE, "2 kJ/mol à 5 % HR < plancher ~7,4 -> RÉFUTÉ (la sécheresse renchérit)")
# procédés réels -> SUPPOSITIONS
for nom in ("condensation par refroidissement (référence)", "MOF hygroscopique (récolte d'eau à basse humidité)",
            "filet à brouillard (interception)"):
    e = pa[nom]
    check(e["atome"].statut == A.SUPPOSITION, f"{nom} -> SUPPOSITION")
check(all(e["atome"].statut in (A.SUPPOSITION, A.REFUTE) for e in pra["liste"]), "aucun principe AWG promu en FAIT")
check("candidat pour eau_potable_air" in pa["condensation par refroidissement (référence)"]["atome"].portee.condition,
      "portée des principes AWG nommant eau_potable_air")
# la loi séparation RÉUTILISÉE (x = HR) : plus l'air est sec, plus le plancher monte
st_50, _, _ = COH.juge_dispositif({"type": "separation", "fraction_molaire": 0.5, "energie_kJ_par_mol": 0.5})
st_05, _, _ = COH.juge_dispositif({"type": "separation", "fraction_molaire": 0.05, "energie_kJ_par_mol": 2.0})
check(st_50 == COH.VIOLE and st_05 == COH.VIOLE, "le juge réfute AWG sous plancher, à 50 % ET à 5 % HR")
st_awg_reel, _, _ = COH.juge_dispositif({"type": "separation", "fraction_molaire": 0.6, "energie_kJ_par_mol": 26})
check(st_awg_reel == COH.COHERENT_BORNE, "AWG réel (26 kJ/mol, 60 % HR) -> COHÉRENT, jamais réfuté")
# stratégies naturelles propres (scarabée du Namib, toile d'araignée)
nata = B.strategies_naturelles("produire de l eau de l air")
check(len(nata) >= 4 and any("Namib" in s["exemple"] for s in nata), "stratégies AWG propres (scarabée du Namib)")
check(not any("photosynthèse" in s["exemple"] for s in nata) and not any("mangrove" in s["exemple"] for s in nata),
      "pas de fuite des stratégies CO₂/eau de mer vers l'AWG")
# les CINQ domaines précédents restent INTACTS
check(len(B.principes("rafraichir une piece")["liste"]) == 18
      and B.decompose("chauffer une piece")["production_corps_W"] == 100
      and B.decompose("dessaler l eau de mer")["salinite_mer_g_L"] == 35
      and "rendement_aller_retour" in B.decompose("stocker de l energie")
      and "fraction_co2_air" in B.decompose("capter le co2"),
      "les 5 domaines précédents inchangés après l'ajout de l'AWG (isolation)")

# ── 12) SEPTIÈME DOMAINE : se propulser (nouvelle loi L4 = conservation de la quantité de mouvement) ──
dp = B.decompose("se propulser")
check(dp["statut"] == "decompose", "besoin propulsion connu -> decompose")
check("reaction" in dp["objectif_reel"].lower().replace("é", "e") and "vide" in dp["objectif_reel"].lower(),
      "objectif réel propulsion = choisir la réaction (pousser sur quelque chose ; vide = éjecter)")
check("regle_or" in dp, "extras propres : la règle d'or de la propulsion")
prop_canaux = {c.canal for c in dp["canaux"]}
check(prop_canaux == {"ejection de masse", "milieu fluide", "momentum externe", "appui solide"},
      f"4 canaux de propulsion ({prop_canaux})")
prp = B.principes("se propulser")
pp = {e["nom"]: e for e in prp["liste"]}
# l'IMPOSSIBLE est RÉFUTÉ : moteur sans réaction ET éjection supraluminique
emd = pp["moteur sans réaction (type EmDrive)"]
check(emd["atome"].statut == A.REFUTE, "moteur sans réaction -> RÉFUTÉ (quantité de mouvement)")
check(A.est_refute(emd["atome"].contenu), "contenu réfuté (EmDrive) dans la garde")
supralum = pp["éjection supraluminique"]
check(supralum["atome"].statut == A.REFUTE, "éjection v > c -> RÉFUTÉ (relativité)")
# procédés réels (fusée, ionique, voile) -> SUPPOSITIONS, JAMAIS réfutés
for nom in ("fusée chimique (référence, vide)", "moteur ionique / à plasma", "voile solaire (momentum de la lumière)",
            "fronde gravitationnelle (assistance gravitationnelle)"):
    e = pp[nom]
    check(e["atome"].statut == A.SUPPOSITION, f"{nom} -> SUPPOSITION (jamais réfuté : réaction réelle)")
check(all(e["atome"].statut in (A.SUPPOSITION, A.REFUTE) for e in prp["liste"]), "aucun principe de propulsion promu en FAIT")
check("candidat pour propulsion" in pp["fusée chimique (référence, vide)"]["atome"].portee.condition,
      "portée des principes propulsion nommant propulsion")
# la loi L4 : réactionless réfuté, mais une fusée à photons (v proche de c mais < c) est cohérente
st_emd, _, loi_emd = COH.juge_dispositif({"type": "propulsion", "poussee_nette": 1.0,
                                          "milieu_externe": False, "ejecte_masse_ou_rayonnement": False})
check(st_emd == COH.VIOLE and loi_emd == COH.L4, "juge : moteur sans réaction -> VIOLE via L4")
st_photon, _, _ = COH.juge_dispositif({"type": "propulsion", "poussee_nette": 1e-6,
                                       "ejecte_masse_ou_rayonnement": True, "vitesse_ejection_m_s": 2.99e8})
check(st_photon == COH.COHERENT_BORNE, "fusée à photons (v < c) -> COHÉRENT, jamais réfutée")
# stratégies naturelles propres (calmar/jet, samare)
natp = B.strategies_naturelles("se propulser")
check(len(natp) >= 4 and any("calmar" in s["exemple"] for s in natp), "stratégies propulsion propres (calmar)")
check(not any("Namib" in s["exemple"] for s in natp) and not any("photosynthèse" in s["exemple"] for s in natp),
      "pas de fuite des stratégies AWG/CO₂ vers la propulsion")
# les SIX domaines précédents restent INTACTS
check(len(B.principes("rafraichir une piece")["liste"]) == 18
      and B.decompose("dessaler l eau de mer")["salinite_mer_g_L"] == 35
      and "fraction_co2_air" in B.decompose("capter le co2")
      and "humidite_relative_moteur" in B.decompose("produire de l eau de l air"),
      "les 6 domaines précédents inchangés après l'ajout de la propulsion (isolation)")

# ── 13) HUITIÈME DOMAINE : éclairer (nouvelle loi L5 = efficacité lumineuse ≤ 683 lm/W) ──
dl = B.decompose("eclairer une piece")
check(dl["statut"] == "decompose", "besoin éclairage connu -> decompose")
check("oeil" in dl["objectif_reel"].lower().replace("œ", "oe") and "683" in dl["objectif_reel"],
      "objectif réel éclairage = lumens vus par l'œil, plafond 683 lm/W")
check("plafond_lm_par_W" in dl, "extras propres : le plafond lm/W")
ecl_canaux = {c.canal for c in dl["canaux"]}
check(ecl_canaux == {"efficacite spectrale", "direction", "couleur adaptee", "lumiere naturelle"},
      f"4 canaux d'éclairage ({ecl_canaux})")
prl = B.principes("eclairer une piece")
pl = {e["nom"]: e for e in prl["liste"]}
# l'IMPOSSIBLE (> 683 lm/W) est RÉFUTÉ
led800 = pl["LED « à 800 lm/W »"]
check(led800["atome"].statut == A.REFUTE, "LED 800 lm/W > 683 -> RÉFUTÉ")
check(A.est_refute(led800["atome"].contenu), "contenu réfuté (800 lm/W) dans la garde")
amp1000 = pl["ampoule « à 1000 lm/W »"]
check(amp1000["atome"].statut == A.REFUTE, "ampoule 1000 lm/W -> RÉFUTÉ")
# procédés réels (dont la lumière du jour, sans efficacité déclarée) -> SUPPOSITIONS
for nom in ("LED blanche (référence)", "sodium basse pression (monochromatique)",
            "lumière du jour guidée (puits de lumière, fibres optiques)"):
    e = pl[nom]
    check(e["atome"].statut == A.SUPPOSITION, f"{nom} -> SUPPOSITION")
check(all(e["atome"].statut in (A.SUPPOSITION, A.REFUTE) for e in prl["liste"]), "aucun principe d'éclairage promu en FAIT")
check("candidat pour eclairage" in pl["LED blanche (référence)"]["atome"].portee.condition,
      "portée des principes éclairage nommant eclairage")
# la loi L5 : > 683 réfuté, AU plafond 683 cohérent (cas limite), record labo 330 cohérent
st_800, _, loi_800 = COH.juge_dispositif({"type": "eclairage", "efficacite_lm_par_W": 800})
check(st_800 == COH.VIOLE and loi_800 == COH.L5, "juge : 800 lm/W -> VIOLE via L5")
check(COH.juge_dispositif({"type": "eclairage", "efficacite_lm_par_W": 683})[0] == COH.COHERENT_BORNE,
      "683 lm/W (AU plafond) -> cohérent, pas de faux positif")
# stratégies naturelles propres (luciole, tapetum)
natl = B.strategies_naturelles("eclairer une piece")
check(len(natl) >= 4 and any("luciole" in s["exemple"] for s in natl), "stratégies éclairage propres (luciole)")
check(not any("calmar" in s["exemple"] for s in natl) and not any("Namib" in s["exemple"] for s in natl),
      "pas de fuite des stratégies propulsion/AWG vers l'éclairage")
# les SEPT domaines précédents restent INTACTS
check(len(B.principes("rafraichir une piece")["liste"]) == 18
      and B.decompose("dessaler l eau de mer")["salinite_mer_g_L"] == 35
      and "regle_or" in B.decompose("se propulser")
      and "humidite_relative_moteur" in B.decompose("produire de l eau de l air"),
      "les 7 domaines précédents inchangés après l'ajout de l'éclairage (isolation)")

# ── 14) NEUVIÈME DOMAINE : calculer à basse énergie (nouvelle loi L6 = limite de Landauer) ──
dk = B.decompose("calculer efficacement")
check(dk["statut"] == "decompose", "besoin calcul connu -> decompose")
check("joule" in dk["objectif_reel"].lower() and "landauer" in dk["objectif_reel"].lower(),
      "objectif réel calcul = calcul par joule, plancher Landauer")
check("limite_landauer_J_bit" in dk, "extras propres : la limite de Landauer")
cal_canaux = {c.canal for c in dk["canaux"]}
check(cal_canaux == {"ne pas effacer", "ne pas deplacer", "moins d operations", "basse temperature"},
      f"4 canaux de calcul ({cal_canaux})")
prk = B.principes("calculer efficacement")
pk = {e["nom"]: e for e in prk["liste"]}
# l'IMPOSSIBLE (sous Landauer) est RÉFUTÉ
sous_land = pk["effacement de bit « à 1e-23 J » (300 K)"]
check(sous_land["atome"].statut == A.REFUTE, "1e-23 J/bit < Landauer ~2,87e-21 -> RÉFUTÉ")
check(A.est_refute(sous_land["atome"].contenu), "contenu réfuté (1e-23 J/bit) dans la garde")
nul = pk["calcul irréversible « à énergie nulle »"]
check(nul["atome"].statut == A.REFUTE, "effacement à énergie nulle -> RÉFUTÉ")
# procédés réels (dont le réversible, TRÈS bas mais > 0) -> SUPPOSITIONS
for nom in ("CMOS numérique actuel (référence)", "calcul réversible / adiabatique", "calcul in-memory (près de la mémoire)"):
    e = pk[nom]
    check(e["atome"].statut == A.SUPPOSITION, f"{nom} -> SUPPOSITION")
check(all(e["atome"].statut in (A.SUPPOSITION, A.REFUTE) for e in prk["liste"]), "aucun principe de calcul promu en FAIT")
check("candidat pour calcul" in pk["CMOS numérique actuel (référence)"]["atome"].portee.condition,
      "portée des principes calcul nommant calcul")
# la loi L6 : sous Landauer réfuté, juste au-dessus cohérent (le réversible n'efface pas → jamais réfuté)
st_land, _, loi_land = COH.juge_dispositif({"type": "calcul", "energie_par_bit_efface_J": 1e-23, "t_K": 300})
check(st_land == COH.VIOLE and loi_land == COH.L6, "juge : 1e-23 J/bit -> VIOLE via L6")
check(COH.juge_dispositif({"type": "calcul", "energie_par_bit_efface_J": 2.9e-21, "t_K": 300})[0] == COH.COHERENT_BORNE,
      "2,9e-21 J/bit (juste au-dessus de Landauer) -> cohérent")
# stratégies naturelles propres (cerveau, rétine)
natk = B.strategies_naturelles("calculer efficacement")
check(len(natk) >= 4 and any("cerveau" in s["exemple"] for s in natk), "stratégies calcul propres (cerveau)")
check(not any("luciole" in s["exemple"] for s in natk) and not any("calmar" in s["exemple"] for s in natk),
      "pas de fuite des stratégies éclairage/propulsion vers le calcul")
# les HUIT domaines précédents restent INTACTS
check(len(B.principes("rafraichir une piece")["liste"]) == 18
      and B.decompose("dessaler l eau de mer")["salinite_mer_g_L"] == 35
      and "regle_or" in B.decompose("se propulser")
      and "plafond_lm_par_W" in B.decompose("eclairer une piece"),
      "les 8 domaines précédents inchangés après l'ajout du calcul (isolation)")

# ── 15) DIXIÈME DOMAINE : communiquer (nouvelle loi L7 = limite de Shannon, débit ≤ B·log₂(1+S/N)) ──
dco = B.decompose("transmettre de l information")
check(dco["statut"] == "decompose", "besoin communication connu -> decompose")
check("bande" in dco["objectif_reel"].lower() and "shannon" in dco["objectif_reel"].lower(),
      "objectif réel communication = élargir la bande (Shannon), pas crier plus fort")
check("capacite_shannon" in dco, "extras propres : la capacité de Shannon")
com_canaux = {c.canal for c in dco["canaux"]}
check(com_canaux == {"bande passante", "rapport signal sur bruit", "codage", "energie par bit"},
      f"4 canaux de communication ({com_canaux})")
prco = B.principes("transmettre de l information")
pco = {e["nom"]: e for e in prco["liste"]}
# l'IMPOSSIBLE (au-dessus de la capacité) est RÉFUTÉ
sur_cap = pco["liaison « 20 Mbit/s sur 1 MHz à 30 dB »"]
check(sur_cap["atome"].statut == A.REFUTE, "20 Mbit/s > capacité ~9,97 -> RÉFUTÉ (Shannon)")
check(A.est_refute(sur_cap["atome"].contenu), "contenu réfuté (20 Mbit/s) dans la garde")
sans_b = pco["transmission « sans bande passante »"]
check(sans_b["atome"].statut == A.REFUTE, "débit > 0 sans bande passante -> RÉFUTÉ")
# procédés réels -> SUPPOSITIONS
for nom in ("radio numérique moderne (5G, référence)", "étalement de spectre / ultra-large bande (UWB)",
            "rétrodiffusion ambiante (backscatter, RFID passif)"):
    e = pco[nom]
    check(e["atome"].statut == A.SUPPOSITION, f"{nom} -> SUPPOSITION")
check(all(e["atome"].statut in (A.SUPPOSITION, A.REFUTE) for e in prco["liste"]), "aucun principe de communication promu en FAIT")
check("candidat pour communication" in pco["radio numérique moderne (5G, référence)"]["atome"].portee.condition,
      "portée des principes communication nommant communication")
# la loi L7 : au-dessus de la capacité réfuté, en dessous cohérent
st_sur, _, loi_sur = COH.juge_dispositif({"type": "communication", "debit_bits_par_s": 2e7,
                                          "bande_passante_Hz": 1e6, "rapport_signal_bruit": 1000})
check(st_sur == COH.VIOLE and loi_sur == COH.L7, "juge : 20 Mbit/s -> VIOLE via L7")
st_sous, _, _ = COH.juge_dispositif({"type": "communication", "debit_bits_par_s": 8e6,
                                     "bande_passante_Hz": 1e6, "rapport_signal_bruit": 1000})
check(st_sous == COH.COHERENT_BORNE, "8 Mbit/s (< capacité) -> COHÉRENT, jamais réfuté")
# stratégies naturelles propres (baleine, fourmi)
natco = B.strategies_naturelles("transmettre de l information")
check(len(natco) >= 4 and any("baleine" in s["exemple"] for s in natco), "stratégies communication propres (baleine)")
check(not any("cerveau" in s["exemple"] for s in natco) and not any("luciole" in s["exemple"] for s in natco),
      "pas de fuite des stratégies calcul/éclairage vers la communication")
# les NEUF domaines précédents restent INTACTS
check(len(B.principes("rafraichir une piece")["liste"]) == 18
      and B.decompose("dessaler l eau de mer")["salinite_mer_g_L"] == 35
      and "regle_or" in B.decompose("se propulser")
      and "limite_landauer_J_bit" in B.decompose("calculer efficacement"),
      "les 9 domaines précédents inchangés après l'ajout de la communication (isolation)")

# ── 17) ONZIÈME DOMAINE : capter l'énergie solaire (nouvelle loi L8 = Shockley-Queisser / plafond thermodynamique) ──
dso = B.decompose("capter l energie solaire")
check(dso["statut"] == "decompose", "besoin captation solaire connu -> decompose")
check("photon" in dso["objectif_reel"].lower() and "shockley" in dso["objectif_reel"].lower(),
      "objectif réel solaire = convertir chaque photon, plafond Shockley-Queisser")
check("plafond_shockley_queisser" in dso, "extras propres : le plafond de Shockley-Queisser")
sol_canaux = {c.canal for c in dso["canaux"]}
check(sol_canaux == {"spectre", "concentration", "thermalisation", "recombinaison"},
      f"4 canaux du solaire ({sol_canaux})")
prso = B.principes("capter l energie solaire")
pso = {e["nom"]: e for e in prso["liste"]}
# l'IMPOSSIBLE est RÉFUTÉ : mono-jonction standard > SQ, et 100 % > plafond thermo
mono50 = pso["panneau mono-jonction « à 50 % » (1 soleil)"]
check(mono50["atome"].statut == A.REFUTE, "50 % mono-jonction standard > SQ 33,7 -> RÉFUTÉ")
check(A.est_refute(mono50["atome"].contenu), "contenu réfuté (50 % mono-jonction) dans la garde")
cent = pso["panneau solaire « 100 % efficace »"]
check(cent["atome"].statut == A.REFUTE, "100 % > plafond thermodynamique -> RÉFUTÉ")
# procédés réels (dont MEG qui dépasse SQ légitimement hors régime standard) -> SUPPOSITIONS
for nom in ("cellule silicium mono-jonction (référence)", "tandem pérovskite/silicium (multi-jonction)",
            "multi-jonction III-V sous concentration (CPV)", "génération multi-excitons (points quantiques)"):
    e = pso[nom]
    check(e["atome"].statut == A.SUPPOSITION, f"{nom} -> SUPPOSITION")
check(all(e["atome"].statut in (A.SUPPOSITION, A.REFUTE) for e in prso["liste"]), "aucun principe solaire promu en FAIT")
check("candidat pour captation_solaire" in pso["cellule silicium mono-jonction (référence)"]["atome"].portee.condition,
      "portée des principes solaires nommant captation_solaire")
# la loi L8 : mono-jonction standard > SQ réfuté, AU plafond SQ cohérent
st_50, _, loi_50 = COH.juge_dispositif({"type": "captation_solaire", "rendement": 0.50, "nb_jonctions": 1,
                                        "concentration_solaire": 1, "bilan_detaille_standard": True})
check(st_50 == COH.VIOLE and loi_50 == COH.L8, "juge : 50 % mono-jonction standard -> VIOLE via L8")
check(COH.juge_dispositif({"type": "captation_solaire", "rendement": 0.337, "nb_jonctions": 1,
                           "concentration_solaire": 1, "bilan_detaille_standard": True})[0] == COH.COHERENT_BORNE,
      "AU plafond SQ (33,7 %) -> cohérent, pas de faux positif")
# stratégies naturelles propres (photosynthèse, mite)
natso = B.strategies_naturelles("capter l energie solaire")
check(len(natso) >= 4 and any("photosynth" in s["exemple"].lower() for s in natso), "stratégies solaires propres (photosynthèse)")
check(not any("baleine" in s["exemple"] for s in natso) and not any("cerveau" in s["exemple"] for s in natso),
      "pas de fuite des stratégies communication/calcul vers le solaire")
# les DIX domaines précédents restent INTACTS
check(len(B.principes("rafraichir une piece")["liste"]) == 18
      and "capacite_shannon" in B.decompose("transmettre de l information")
      and "limite_landauer_J_bit" in B.decompose("calculer efficacement"),
      "les 10 domaines précédents inchangés après l'ajout du solaire (isolation)")

# ── 18) DOUZIÈME DOMAINE : produire de l'hydrogène (nouvelle loi L9 = électrolyse, tension ≥ E_rev, énergie ≥ ΔH) ──
dh2 = B.decompose("produire de l hydrogene")
check(dh2["statut"] == "decompose", "besoin production hydrogène connu -> decompose")
check("surtension" in dh2["objectif_reel"].lower() and "gibbs" in dh2["objectif_reel"].lower(),
      "objectif réel H₂ = approcher ΔG (Gibbs) contre la surtension")
check("tension_reversible_V" in dh2, "extras propres : la tension réversible ~1,23 V")
h2_canaux = {c.canal for c in dh2["canaux"]}
check(h2_canaux == {"surtension", "temperature", "catalyseur", "anode"}, f"4 canaux de l'électrolyse ({h2_canaux})")
prh2 = B.principes("produire de l hydrogene")
ph2 = {e["nom"]: e for e in prh2["liste"]}
# l'IMPOSSIBLE est RÉFUTÉ : 0,9 V (anode standard) < E_rev, et 150 kJ/mol < PCS
sous_erev = ph2["électrolyseur « à 0,9 V » (anode standard, ambiant)"]
check(sous_erev["atome"].statut == A.REFUTE, "0,9 V anode standard < E_rev 1,23 -> RÉFUTÉ")
check(A.est_refute(sous_erev["atome"].contenu), "contenu réfuté (0,9 V) dans la garde")
sous_pcs = ph2["hydrogène « à 150 kJ/mol » (sous le PCS)"]
check(sous_pcs["atome"].statut == A.REFUTE, "150 kJ/mol < PCS 285,8 -> RÉFUTÉ")
# procédés réels (dont l'électrolyse assistée qui descend sous 1,23 V légitimement) -> SUPPOSITIONS
for nom in ("électrolyse alcaline (référence)", "électrolyse à oxyde solide (SOEC, haute température)",
            "électrolyse assistée (oxydation sacrificielle à l'anode)"):
    e = ph2[nom]
    check(e["atome"].statut == A.SUPPOSITION, f"{nom} -> SUPPOSITION")
check(all(e["atome"].statut in (A.SUPPOSITION, A.REFUTE) for e in prh2["liste"]), "aucun principe d'électrolyse promu en FAIT")
check("candidat pour production_hydrogene" in ph2["électrolyse alcaline (référence)"]["atome"].portee.condition,
      "portée des principes H₂ nommant production_hydrogene")
# la loi L9 : tension sous E_rev (anode standard) réfutée, SOEC haute T cohérente
st_09, _, loi_09 = COH.juge_dispositif({"type": "electrolyse", "tension_cellule_V": 0.9, "t_K": 298.15,
                                        "reaction_anodique_standard": True})
check(st_09 == COH.VIOLE and loi_09 == COH.L9, "juge : 0,9 V anode standard -> VIOLE via L9")
check(COH.juge_dispositif({"type": "electrolyse", "tension_cellule_V": 1.3, "t_K": 1073,
                           "reaction_anodique_standard": True})[0] == COH.COHERENT_BORNE,
      "SOEC 1,3 V à haute température -> cohérent (E_rev abaissée), pas de faux positif")
# stratégies naturelles propres (hydrogénase, photosystème II)
nath2 = B.strategies_naturelles("produire de l hydrogene")
check(len(nath2) >= 4 and any("hydrogénase" in s["exemple"].lower() for s in nath2), "stratégies H₂ propres (hydrogénase)")
check(not any("tournesol" in s["exemple"] for s in nath2) and not any("baleine" in s["exemple"] for s in nath2),
      "pas de fuite des stratégies solaire/communication vers l'hydrogène")
# les ONZE domaines précédents restent INTACTS
check(len(B.principes("rafraichir une piece")["liste"]) == 18
      and "plafond_shockley_queisser" in B.decompose("capter l energie solaire")
      and "capacite_shannon" in B.decompose("transmettre de l information"),
      "les 11 domaines précédents inchangés après l'ajout de l'hydrogène (isolation)")

# ── 19) TREIZIÈME DOMAINE : voler sur place / vol stationnaire (nouvelle loi L10 = puissance induite idéale) ──
dvo = B.decompose("vol stationnaire")
check(dvo["statut"] == "decompose", "besoin vol stationnaire connu -> decompose")
check("disque" in dvo["objectif_reel"].lower() and "induite" in dvo["objectif_reel"].lower(),
      "objectif réel vol = charge du disque, puissance induite")
check("puissance_induite_ideale" in dvo, "extras propres : la puissance induite idéale")
vol_canaux = {c.canal for c in dvo["canaux"]}
check(vol_canaux == {"aire du disque", "charge du disque", "masse", "portance statique / effet de sol"},
      f"4 canaux du vol stationnaire ({vol_canaux})")
prvo = B.principes("vol stationnaire")
pvo = {e["nom"]: e for e in prvo["liste"]}
# l'IMPOSSIBLE est RÉFUTÉ : puissances sous le plancher induit
drone5 = pvo["drone 2 kg « qui plane à 5 W » (hélice 0,05 m²)"]
check(drone5["atome"].statut == A.REFUTE, "drone 2 kg à 5 W < P induite -> RÉFUTÉ")
check(A.est_refute(drone5["atome"].contenu), "contenu réfuté (5 W) dans la garde")
plat = pvo["plateforme 100 kg « qui plane à 50 W » (disque 0,1 m²)"]
check(plat["atome"].statut == A.REFUTE, "plateforme 100 kg à 50 W -> RÉFUTÉ")
# procédés réels (dont l'aérostat à portance statique) -> SUPPOSITIONS
for nom in ("hélicoptère à grand rotor (référence)", "drone à grand disque lent (rotor surdimensionné)",
            "aérostat (portance statique, Archimède)"):
    e = pvo[nom]
    check(e["atome"].statut == A.SUPPOSITION, f"{nom} -> SUPPOSITION")
check(all(e["atome"].statut in (A.SUPPOSITION, A.REFUTE) for e in prvo["liste"]), "aucun principe de vol promu en FAIT")
check("candidat pour sustentation" in pvo["hélicoptère à grand rotor (référence)"]["atome"].portee.condition,
      "portée des principes de vol nommant sustentation")
# la loi L10 : puissance sous le plancher réfutée, grand disque lent cohérent
st_vo, _, loi_vo = COH.juge_dispositif({"type": "sustentation", "masse_kg": 2, "aire_rotor_m2": 0.05, "puissance_W": 5})
check(st_vo == COH.VIOLE and loi_vo == COH.L10, "juge : drone 5 W -> VIOLE via L10")
check(COH.juge_dispositif({"type": "sustentation", "masse_kg": 2, "aire_rotor_m2": 0.5, "puissance_W": 100})[0]
      == COH.COHERENT_BORNE, "grand disque lent 100 W -> cohérent, pas de faux positif")
# stratégies naturelles propres (colibri, samare)
natvo = B.strategies_naturelles("vol stationnaire")
check(len(natvo) >= 4 and any("colibri" in s["exemple"].lower() for s in natvo), "stratégies vol propres (colibri)")
check(not any("hydrogénase" in s["exemple"] for s in natvo) and not any("tournesol" in s["exemple"] for s in natvo),
      "pas de fuite des stratégies hydrogène/solaire vers le vol")
# les DOUZE domaines précédents restent INTACTS
check(len(B.principes("rafraichir une piece")["liste"]) == 18
      and "tension_reversible_V" in B.decompose("produire de l hydrogene")
      and "plafond_shockley_queisser" in B.decompose("capter l energie solaire"),
      "les 12 domaines précédents inchangés après l'ajout du vol (isolation)")

# ── 20) QUATORZIÈME DOMAINE : voir plus petit / résolution optique (nouvelle loi L11 = limite de diffraction d'Abbe) ──
dop = B.decompose("voir plus petit")
check(dop["statut"] == "decompose", "besoin résolution optique connu -> decompose")
check("diffraction" in dop["objectif_reel"].lower() and "abbe" in dop["objectif_reel"].lower(),
      "objectif réel optique = limite de diffraction d'Abbe")
check("limite_abbe" in dop, "extras propres : la limite d'Abbe")
opt_canaux = {c.canal for c in dop["canaux"]}
check(opt_canaux == {"longueur d onde", "ouverture numerique", "champ proche", "localisation / commutation"},
      f"4 canaux de la résolution optique ({opt_canaux})")
prop = B.principes("voir plus petit")
pop = {e["nom"]: e for e in prop["liste"]}
# l'IMPOSSIBLE est RÉFUTÉ : sous Abbe (conventionnel) et NA > n
sous_abbe = pop["microscope conventionnel « résolvant 50 nm » (λ=550, NA=1,4)"]
check(sous_abbe["atome"].statut == A.REFUTE, "50 nm conventionnel < Abbe -> RÉFUTÉ")
check(A.est_refute(sous_abbe["atome"].contenu), "contenu réfuté (50 nm) dans la garde")
na_sup = pop["objectif « à NA 1,7 dans l'air »"]
check(na_sup["atome"].statut == A.REFUTE, "NA 1,7 dans l'air (n=1) -> RÉFUTÉ")
# procédés réels (dont la super-résolution, exemptée) -> SUPPOSITIONS
for nom in ("immersion à huile (NA élevé)", "STED (déplétion par émission stimulée)",
            "PALM / STORM (localisation de molécules uniques)"):
    e = pop[nom]
    check(e["atome"].statut == A.SUPPOSITION, f"{nom} -> SUPPOSITION")
check(all(e["atome"].statut in (A.SUPPOSITION, A.REFUTE) for e in prop["liste"]), "aucun principe optique promu en FAIT")
check("candidat pour resolution_optique" in pop["immersion à huile (NA élevé)"]["atome"].portee.condition,
      "portée des principes optiques nommant resolution_optique")
# la loi L11 : sous Abbe (conventionnel) réfuté, super-résolution cohérente
st_op, _, loi_op = COH.juge_dispositif({"type": "imagerie_optique", "longueur_onde_nm": 550,
                                        "ouverture_numerique": 1.4, "resolution_nm": 50})
check(st_op == COH.VIOLE and loi_op == COH.L11, "juge : 50 nm conventionnel -> VIOLE via L11")
check(COH.juge_dispositif({"type": "imagerie_optique", "longueur_onde_nm": 550, "ouverture_numerique": 1.4,
                           "indice_milieu": 1.5, "resolution_nm": 30, "super_resolution": True})[0]
      == COH.COHERENT_BORNE, "STED 30 nm super-résolu -> cohérent, pas de faux positif")
# stratégies naturelles propres (aigle, diatomée)
natop = B.strategies_naturelles("voir plus petit")
check(len(natop) >= 4 and any("aigle" in s["exemple"].lower() for s in natop), "stratégies optiques propres (aigle)")
check(not any("colibri" in s["exemple"] for s in natop) and not any("tournesol" in s["exemple"] for s in natop),
      "pas de fuite des stratégies vol/solaire vers l'optique")
# les TREIZE domaines précédents restent INTACTS
check(len(B.principes("rafraichir une piece")["liste"]) == 18
      and "puissance_induite_ideale" in B.decompose("vol stationnaire")
      and "tension_reversible_V" in B.decompose("produire de l hydrogene"),
      "les 13 domaines précédents inchangés après l'ajout de l'optique (isolation)")

# ── 21) QUINZIÈME DOMAINE : capter l'énergie du vent (nouvelle loi L12 = limite de Betz, Cp ≤ 16/27) ──
dve = B.decompose("capter l energie du vent")
check(dve["statut"] == "decompose", "besoin énergie éolienne connu -> decompose")
check("betz" in dve["objectif_reel"].lower() and "vent" in dve["objectif_reel"].lower(),
      "objectif réel éolien = limite de Betz sur la puissance du vent")
check("limite_betz" in dve, "extras propres : la limite de Betz")
vent_canaux = {c.canal for c in dve["canaux"]}
check(vent_canaux == {"aire balayee", "vitesse du site", "approche de Betz", "carenage"},
      f"4 canaux de l'éolien ({vent_canaux})")
prve = B.principes("capter l energie du vent")
pve = {e["nom"]: e for e in prve["liste"]}
# l'IMPOSSIBLE est RÉFUTÉ : Cp et puissance au-dessus de Betz (rotor ouvert)
cp07 = pve["éolienne « à Cp 0,7 » (rotor ouvert)"]
check(cp07["atome"].statut == A.REFUTE, "Cp 0,7 rotor ouvert > Betz -> RÉFUTÉ")
check(A.est_refute(cp07["atome"].contenu), "contenu réfuté (Cp 0,7) dans la garde")
p50 = pve["éolienne « 50 kW sur 100 m² à 10 m/s »"]
check(p50["atome"].statut == A.REFUTE, "50 kW > Betz ~36 kW -> RÉFUTÉ")
# procédés réels (dont la carénée à diffuseur, exemptée) -> SUPPOSITIONS
for nom in ("éolienne tripale à axe horizontal (référence)", "éolienne carénée à diffuseur",
            "éolien aéroporté (cerf-volant / aile captive)"):
    e = pve[nom]
    check(e["atome"].statut == A.SUPPOSITION, f"{nom} -> SUPPOSITION")
check(all(e["atome"].statut in (A.SUPPOSITION, A.REFUTE) for e in prve["liste"]), "aucun principe éolien promu en FAIT")
check("candidat pour energie_eolienne" in pve["éolienne tripale à axe horizontal (référence)"]["atome"].portee.condition,
      "portée des principes éoliens nommant energie_eolienne")
# la loi L12 : Cp au-dessus de Betz réfuté, carénée (diffuseur) cohérente
st_ve, _, loi_ve = COH.juge_dispositif({"type": "eolienne", "coefficient_puissance": 0.7})
check(st_ve == COH.VIOLE and loi_ve == COH.L12, "juge : Cp 0,7 rotor ouvert -> VIOLE via L12")
check(COH.juge_dispositif({"type": "eolienne", "coefficient_puissance": 0.7, "avec_diffuseur": True})[0]
      == COH.COHERENT_BORNE, "carénée à diffuseur Cp 0,7 -> cohérent (par aire de rotor), pas de faux positif")
# stratégies naturelles propres (pissenlit, arbre flexible)
natve = B.strategies_naturelles("capter l energie du vent")
check(len(natve) >= 4 and any("pissenlit" in s["exemple"].lower() for s in natve), "stratégies éoliennes propres (pissenlit)")
check(not any("colibri" in s["exemple"] for s in natve) and not any("aigle" in s["exemple"] for s in natve),
      "pas de fuite des stratégies vol/optique vers l'éolien")
# les QUATORZE domaines précédents restent INTACTS
check(len(B.principes("rafraichir une piece")["liste"]) == 18
      and "limite_abbe" in B.decompose("voir plus petit")
      and "puissance_induite_ideale" in B.decompose("vol stationnaire"),
      "les 14 domaines précédents inchangés après l'ajout de l'éolien (isolation)")

# ── 22) SEIZIÈME DOMAINE : propulsion spatiale (nouvelle loi L13 = équation de Tsiolkovski, Δv ≤ ve·ln(m₀/mf)) ──
dfu = B.decompose("propulsion spatiale")
check(dfu["statut"] == "decompose", "besoin propulsion spatiale connu -> decompose")
check("tsiolkov" in dfu["objectif_reel"].lower() and "logarithm" in dfu["objectif_reel"].lower(),
      "objectif réel fusée = Tsiolkovski, gain logarithmique")
check("tsiolkovski" in dfu, "extras propres : l'équation de Tsiolkovski")
fu_canaux = {c.canal for c in dfu["canaux"]}
check(fu_canaux == {"vitesse d ejection", "etagement", "masse a vide", "momentum externe"},
      f"4 canaux de la propulsion spatiale ({fu_canaux})")
prfu = B.principes("propulsion spatiale")
pfu = {e["nom"]: e for e in prfu["liste"]}
# l'IMPOSSIBLE est RÉFUTÉ : Δv au-dessus de Tsiolkovski, et Δv sans ergols
dv30 = pfu["fusée chimique « à 30 km/s » (ve 4,5 km/s, rapport 20)"]
check(dv30["atome"].statut == A.REFUTE, "30 km/s > Tsiolkovski -> RÉFUTÉ")
check(A.est_refute(dv30["atome"].contenu), "contenu réfuté (30 km/s) dans la garde")
sans_erg = pfu["fusée « qui accélère sans consommer d'ergols » (rapport de masse 1)"]
check(sans_erg["atome"].statut == A.REFUTE, "Δv > 0 sans ergols (rapport 1) -> RÉFUTÉ")
# procédés réels (dont la voile solaire à momentum externe) -> SUPPOSITIONS
for nom in ("fusée chimique (référence)", "propulsion électrique / ionique (Isp élevé)",
            "voile solaire (momentum externe)"):
    e = pfu[nom]
    check(e["atome"].statut == A.SUPPOSITION, f"{nom} -> SUPPOSITION")
check(all(e["atome"].statut in (A.SUPPOSITION, A.REFUTE) for e in prfu["liste"]), "aucun principe de fusée promu en FAIT")
check("candidat pour propulsion_spatiale" in pfu["fusée chimique (référence)"]["atome"].portee.condition,
      "portée des principes de fusée nommant propulsion_spatiale")
# la loi L13 : Δv au-dessus de Tsiolkovski réfuté, chimique réaliste cohérent
st_fu, _, loi_fu = COH.juge_dispositif({"type": "fusee", "delta_v_m_s": 30000, "vitesse_ejection_m_s": 4500,
                                        "rapport_masse": 20})
check(st_fu == COH.VIOLE and loi_fu == COH.L13, "juge : 30 km/s chimique -> VIOLE via L13")
check(COH.juge_dispositif({"type": "fusee", "delta_v_m_s": 13000, "vitesse_ejection_m_s": 4500,
                           "rapport_masse": 20})[0] == COH.COHERENT_BORNE,
      "chimique 13 km/s (< Tsiolkovski) -> cohérent, pas de faux positif")
# stratégies naturelles propres (salpe, raie manta)
natfu = B.strategies_naturelles("propulsion spatiale")
check(len(natfu) >= 4 and any("salpe" in s["exemple"].lower() for s in natfu), "stratégies fusée propres (salpe)")
check(not any("calmar" in s["exemple"] for s in natfu) and not any("pissenlit" in s["exemple"] for s in natfu),
      "pas de fuite des stratégies propulsion/éolien vers la fusée")
# les QUINZE domaines précédents restent INTACTS
check(len(B.principes("rafraichir une piece")["liste"]) == 18
      and "limite_betz" in B.decompose("capter l energie du vent")
      and "limite_abbe" in B.decompose("voir plus petit"),
      "les 15 domaines précédents inchangés après l'ajout de la fusée (isolation)")

# ── 23) DIX-SEPTIÈME DOMAINE : nourrir / cultiver (nouvelle loi L14 = plafond de rendement photosynthétique) ──
dno = B.decompose("cultiver")
check(dno["statut"] == "decompose", "besoin production alimentaire connu -> decompose")
check("photosynth" in dno["objectif_reel"].lower() and "biomasse" in dno["objectif_reel"].lower(),
      "objectif réel nourrir = plafond photosynthétique, calories par surface")
check("rendement_photo_max" in dno, "extras propres : le plafond photosynthétique")
no_canaux = {c.canal for c in dno["canaux"]}
check(no_canaux == {"rendement photosynthetique", "decouplage", "niveau trophique", "indice de recolte"},
      f"4 canaux de la production alimentaire ({no_canaux})")
prno = B.principes("cultiver")
pno = {e["nom"]: e for e in prno["liste"]}
# l'IMPOSSIBLE est RÉFUTÉ : au-dessus du plafond et over-unity
c25 = pno["culture « à 25 % de rendement solaire »"]
check(c25["atome"].statut == A.REFUTE, "25 % solaire→biomasse > plafond -> RÉFUTÉ")
check(A.est_refute(c25["atome"].contenu), "contenu réfuté (25 %) dans la garde")
ou = pno["biomasse « produisant plus d'énergie que le soleil reçu »"]
check(ou["atome"].statut == A.REFUTE, "biomasse over-unity -> RÉFUTÉ")
# procédés réels (dont la fermentation gazeuse découplée) -> SUPPOSITIONS
for nom in ("grande culture C3 en plein champ (référence)", "plante en C4 (maïs, canne, sorgho)",
            "fermentation gazeuse (H₂/CO₂ → protéine microbienne)"):
    e = pno[nom]
    check(e["atome"].statut == A.SUPPOSITION, f"{nom} -> SUPPOSITION")
check(all(e["atome"].statut in (A.SUPPOSITION, A.REFUTE) for e in prno["liste"]), "aucun principe alimentaire promu en FAIT")
check("candidat pour production_alimentaire" in pno["grande culture C3 en plein champ (référence)"]["atome"].portee.condition,
      "portée des principes alimentaires nommant production_alimentaire")
# la loi L14 : rendement au-dessus du plafond réfuté, C4 réaliste cohérent
st_no, _, loi_no = COH.juge_dispositif({"type": "photosynthese", "rendement_solaire_biomasse": 0.25})
check(st_no == COH.VIOLE and loi_no == COH.L14, "juge : 25 % solaire→biomasse -> VIOLE via L14")
check(COH.juge_dispositif({"type": "photosynthese", "rendement_solaire_biomasse": 0.06})[0] == COH.COHERENT_BORNE,
      "C4/algue 6 % (< plafond) -> cohérent, pas de faux positif")
# stratégies naturelles propres (C4, rhizobium)
natno = B.strategies_naturelles("cultiver")
check(len(natno) >= 4 and any("c4" in s["exemple"].lower() for s in natno), "stratégies alimentaires propres (C4)")
check(not any("diatomée" in s["exemple"] for s in natno) and not any("salpe" in s["exemple"] for s in natno),
      "pas de fuite des stratégies optique/fusée vers l'alimentaire")
# les SEIZE domaines précédents restent INTACTS
check(len(B.principes("rafraichir une piece")["liste"]) == 18
      and "tsiolkovski" in B.decompose("propulsion spatiale")
      and "limite_betz" in B.decompose("capter l energie du vent"),
      "les 16 domaines précédents inchangés après l'ajout de l'alimentaire (isolation)")

# ── 24) DIX-HUITIÈME DOMAINE : compresser l'information (nouvelle loi L15 = borne d'entropie, codage de source) ──
dco2 = B.decompose("compresser des donnees")
check(dco2["statut"] == "decompose", "besoin compression connu -> decompose")
check("entropie" in dco2["objectif_reel"].lower() and "shannon" in dco2["objectif_reel"].lower(),
      "objectif réel compression = borne d'entropie de Shannon")
check("borne_entropie" in dco2, "extras propres : la borne d'entropie")
comp_canaux = {c.canal for c in dco2["canaux"]}
check(comp_canaux == {"modele de source", "redondance", "perte controlee", "transformation"},
      f"4 canaux de la compression ({comp_canaux})")
prco2 = B.principes("compresser des donnees")
pco2 = {e["nom"]: e for e in prco2["liste"]}
# l'IMPOSSIBLE est RÉFUTÉ : sous l'entropie, et universel
sous_h = pco2["compresseur sans perte « à 1 bit/symbole » (source d'entropie 4)"]
check(sous_h["atome"].statut == A.REFUTE, "1 bit sur entropie 4 sans perte -> RÉFUTÉ")
check(A.est_refute(sous_h["atome"].contenu), "contenu réfuté (1 bit/symbole) dans la garde")
univ = pco2["compresseur sans perte « universel » (réduit tout fichier)"]
check(univ["atome"].statut == A.REFUTE, "compresseur sans perte universel -> RÉFUTÉ")
# procédés réels (dont la compression avec perte) -> SUPPOSITIONS
for nom in ("codage entropique (Huffman / arithmétique)", "dictionnaire / déduplication (LZ)",
            "codage perceptuel (MP3, JPEG)"):
    e = pco2[nom]
    check(e["atome"].statut == A.SUPPOSITION, f"{nom} -> SUPPOSITION")
check(all(e["atome"].statut in (A.SUPPOSITION, A.REFUTE) for e in prco2["liste"]), "aucun principe de compression promu en FAIT")
check("candidat pour compression_information" in pco2["codage entropique (Huffman / arithmétique)"]["atome"].portee.condition,
      "portée des principes de compression nommant compression_information")
# la loi L15 : sous l'entropie (sans perte) réfuté, avec perte cohérent
st_co, _, loi_co = COH.juge_dispositif({"type": "compression", "sans_perte": True,
                                        "entropie_bits_par_symbole": 4.0, "bits_par_symbole": 1.0})
check(st_co == COH.VIOLE and loi_co == COH.L15, "juge : 1 bit sur entropie 4 sans perte -> VIOLE via L15")
check(COH.juge_dispositif({"type": "compression", "sans_perte": False, "entropie_bits_par_symbole": 8.0,
                           "bits_par_symbole": 0.5})[0] == COH.COHERENT_BORNE,
      "compression AVEC PERTE sous H -> cohérent, pas de faux positif")
# stratégies naturelles propres (fractale, cristal)
natco = B.strategies_naturelles("compresser des donnees")
check(len(natco) >= 4 and any("fractale" in s["exemple"].lower() for s in natco), "stratégies compression propres (fractale)")
check(not any("phytoplancton" in s["exemple"] for s in natco) and not any("salpe" in s["exemple"] for s in natco),
      "pas de fuite des stratégies alimentaire/fusée vers la compression")
# les DIX-SEPT domaines précédents restent INTACTS
check(len(B.principes("rafraichir une piece")["liste"]) == 18
      and "rendement_photo_max" in B.decompose("cultiver")
      and "tsiolkovski" in B.decompose("propulsion spatiale"),
      "les 17 domaines précédents inchangés après l'ajout de la compression (isolation)")

# ── 25) DIX-NEUVIÈME DOMAINE : isoler thermiquement (nouvelle loi L16 = plancher radiatif de Stefan-Boltzmann) ──
dis = B.decompose("isoler thermiquement")
check(dis["statut"] == "decompose", "besoin isolation thermique connu -> decompose")
check("rayonnement" in dis["objectif_reel"].lower() and "stefan" in dis["objectif_reel"].lower(),
      "objectif réel isolation = plancher radiatif de Stefan-Boltzmann")
check("plancher_radiatif" in dis, "extras propres : le plancher radiatif")
iso_canaux = {c.canal for c in dis["canaux"]}
check(iso_canaux == {"conduction convection", "emissivite", "aire gradient", "masse thermique"},
      f"4 canaux de l'isolation ({iso_canaux})")
pris = B.principes("isoler thermiquement")
pis = {e["nom"]: e for e in pris["liste"]}
# l'IMPOSSIBLE est RÉFUTÉ : zéro perte, et émissivité nulle
zero = pis["isolation « parfaite » (zéro perte à 373 K vers 293 K)"]
check(zero["atome"].statut == A.REFUTE, "zéro perte < plancher radiatif -> RÉFUTÉ")
check(A.est_refute(zero["atome"].contenu), "contenu réfuté (zéro perte) dans la garde")
eps0 = pis["matériau « à émissivité nulle »"]
check(eps0["atome"].statut == A.REFUTE, "émissivité nulle -> RÉFUTÉ")
# procédés réels -> SUPPOSITIONS
for nom in ("bouteille isotherme (vide + argenture)", "isolant multicouche (MLI, spatial)",
            "panneau isolant sous vide (VIP)"):
    e = pis[nom]
    check(e["atome"].statut == A.SUPPOSITION, f"{nom} -> SUPPOSITION")
check(all(e["atome"].statut in (A.SUPPOSITION, A.REFUTE) for e in pris["liste"]), "aucun principe d'isolation promu en FAIT")
check("candidat pour isolation_thermique" in pis["bouteille isotherme (vide + argenture)"]["atome"].portee.condition,
      "portée des principes d'isolation nommant isolation_thermique")
# la loi L16 : zéro perte réfuté, thermos réel cohérent
st_is, _, loi_is = COH.juge_dispositif({"type": "isolation_thermique", "emissivite": 0.5, "aire_m2": 1,
                                        "t_objet_K": 373, "t_env_K": 293, "puissance_perdue_W": 0})
check(st_is == COH.VIOLE and loi_is == COH.L16, "juge : zéro perte -> VIOLE via L16")
check(COH.juge_dispositif({"type": "isolation_thermique", "emissivite": 0.05, "aire_m2": 0.1, "t_objet_K": 363,
                           "t_env_K": 293, "puissance_perdue_W": 5})[0] == COH.COHERENT_BORNE,
      "thermos 5 W (> plancher) -> cohérent, pas de faux positif")
# stratégies naturelles propres (ours polaire, phoque)
natis = B.strategies_naturelles("isoler thermiquement")
check(len(natis) >= 4 and any("ours polaire" in s["exemple"].lower() for s in natis), "stratégies isolation propres (ours polaire)")
check(not any("fractale" in s["exemple"] for s in natis) and not any("phytoplancton" in s["exemple"] for s in natis),
      "pas de fuite des stratégies compression/alimentaire vers l'isolation")
# les DIX-HUIT domaines précédents restent INTACTS
check(len(B.principes("rafraichir une piece")["liste"]) == 18
      and "borne_entropie" in B.decompose("compresser des donnees")
      and "rendement_photo_max" in B.decompose("cultiver"),
      "les 18 domaines précédents inchangés après l'ajout de l'isolation (isolation)")

# ── 26) VINGTIÈME DOMAINE : chiffrer / garder un secret (nouvelle loi L17 = secret parfait de Shannon) ──
dcr = B.decompose("chiffrer un message")
check(dcr["statut"] == "decompose", "besoin confidentialité connu -> decompose")
check("secret" in dcr["objectif_reel"].lower() and "shannon" in dcr["objectif_reel"].lower(),
      "objectif réel chiffrement = secret parfait de Shannon")
check("secret_parfait" in dcr, "extras propres : le secret parfait H(clé) >= H(message)")
cr_canaux = {c.canal for c in dcr["canaux"]}
check(cr_canaux == {"longueur de cle", "hypothese calculatoire", "entropie du message", "distribution de cle"},
      f"4 canaux de la confidentialité ({cr_canaux})")
prcr = B.principes("chiffrer un message")
pcr = {e["nom"]: e for e in prcr["liste"]}
# l'IMPOSSIBLE est RÉFUTÉ : clé trop courte pour un secret parfait, et clé réutilisée
cle128 = pcr["secret « parfait » avec clé de 128 bits pour 1 Mo"]
check(cle128["atome"].statut == A.REFUTE, "clé 128 bits < message, secret parfait -> RÉFUTÉ")
check(A.est_refute(cle128["atome"].contenu), "contenu réfuté (clé 128) dans la garde")
ttp = pcr["masque jetable réutilisé (two-time pad)"]
check(ttp["atome"].statut == A.REFUTE, "masque jetable réutilisé -> RÉFUTÉ")
# procédés réels (dont AES calculatoire, non réfuté) -> SUPPOSITIONS
for nom in ("masque jetable (OTP)", "chiffrement symétrique (AES)",
            "chiffrement asymétrique (RSA / courbes elliptiques)"):
    e = pcr[nom]
    check(e["atome"].statut == A.SUPPOSITION, f"{nom} -> SUPPOSITION")
check(all(e["atome"].statut in (A.SUPPOSITION, A.REFUTE) for e in prcr["liste"]), "aucun principe de chiffrement promu en FAIT")
check("candidat pour confidentialite_information" in pcr["masque jetable (OTP)"]["atome"].portee.condition,
      "portée des principes de chiffrement nommant confidentialite_information")
# la loi L17 : clé sous l'entropie du message (secret parfait) réfutée, AES calculatoire cohérent
st_cr, _, loi_cr = COH.juge_dispositif({"type": "chiffrement", "securite_parfaite": True,
                                        "entropie_cle_bits": 128, "entropie_message_bits": 8e6})
check(st_cr == COH.VIOLE and loi_cr == COH.L17, "juge : clé 128 secret parfait -> VIOLE via L17")
check(COH.juge_dispositif({"type": "chiffrement", "securite_parfaite": False, "entropie_cle_bits": 256,
                           "entropie_message_bits": 8e6})[0] == COH.COHERENT_BORNE,
      "AES calculatoire (pas parfait) -> cohérent, pas de faux positif")
# stratégies naturelles propres (seiche, gymnote)
natcr = B.strategies_naturelles("chiffrer un message")
check(len(natcr) >= 4 and any("seiche" in s["exemple"].lower() for s in natcr), "stratégies chiffrement propres (seiche)")
check(not any("ours polaire" in s["exemple"] for s in natcr) and not any("fractale" in s["exemple"] for s in natcr),
      "pas de fuite des stratégies isolation/compression vers le chiffrement")
# les DIX-NEUF domaines précédents restent INTACTS
check(len(B.principes("rafraichir une piece")["liste"]) == 18
      and "plancher_radiatif" in B.decompose("isoler thermiquement")
      and "borne_entropie" in B.decompose("compresser des donnees"),
      "les 19 domaines précédents inchangés après l'ajout du chiffrement (isolation)")

# ── 27) VINGT-ET-UNIÈME DOMAINE : voler loin / croisière (nouvelle loi L18 = traînée induite minimale) ──
dcro = B.decompose("voler loin")
check(dcro["statut"] == "decompose", "besoin vol de croisière connu -> decompose")
check("envergure" in dcro["objectif_reel"].lower() and "induite" in dcro["objectif_reel"].lower(),
      "objectif réel croisière = envergure, traînée induite")
check("trainee_induite_min" in dcro, "extras propres : la traînée induite minimale")
cro_canaux = {c.canal for c in dcro["canaux"]}
check(cro_canaux == {"envergure", "finesse", "altitude vitesse", "fraction de carburant"},
      f"4 canaux de la croisière ({cro_canaux})")
prcro = B.principes("voler loin")
pcro = {e["nom"]: e for e in prcro["liste"]}
# l'IMPOSSIBLE est RÉFUTÉ : traînée induite nulle, et e > 1
di0 = pcro["aile « à traînée induite nulle » en portance"]
check(di0["atome"].statut == A.REFUTE, "traînée induite nulle en portance -> RÉFUTÉ")
check(A.est_refute(di0["atome"].contenu), "contenu réfuté (traînée nulle) dans la garde")
e15 = pcro["aile « à efficacité d'envergure 1,5 »"]
check(e15["atome"].statut == A.REFUTE, "efficacité d'envergure 1,5 -> RÉFUTÉ")
# procédés réels (dont le dirigeable à portance statique) -> SUPPOSITIONS
for nom in ("aile longue et fine (grande envergure)", "winglet / dispositif de bout d'aile",
            "dirigeable / portance statique"):
    e = pcro[nom]
    check(e["atome"].statut == A.SUPPOSITION, f"{nom} -> SUPPOSITION")
check(all(e["atome"].statut in (A.SUPPOSITION, A.REFUTE) for e in prcro["liste"]), "aucun principe de croisière promu en FAIT")
check("candidat pour vol_croisiere" in pcro["aile longue et fine (grande envergure)"]["atome"].portee.condition,
      "portée des principes de croisière nommant vol_croisiere")
# la loi L18 : traînée induite nulle réfutée, planeur réaliste cohérent
st_cro, _, loi_cro = COH.juge_dispositif({"type": "vol_croisiere", "portance_N": 686000, "envergure_m": 60,
                                          "vitesse_m_s": 250, "rho_air": 0.4, "trainee_induite_N": 0})
check(st_cro == COH.VIOLE and loi_cro == COH.L18, "juge : traînée induite nulle -> VIOLE via L18")
check(COH.juge_dispositif({"type": "vol_croisiere", "portance_N": 5000, "envergure_m": 20, "vitesse_m_s": 30,
                           "rho_air": 1.0, "trainee_induite_N": 60, "efficacite_envergure": 0.9})[0]
      == COH.COHERENT_BORNE, "planeur (> plancher) -> cohérent, pas de faux positif")
# stratégies naturelles propres (frégate, martinet)
natcro = B.strategies_naturelles("voler loin")
check(len(natcro) >= 4 and any("frégate" in s["exemple"].lower() for s in natcro), "stratégies croisière propres (frégate)")
check(not any("albatros" in s["exemple"] for s in natcro) and not any("seiche" in s["exemple"] for s in natcro),
      "pas de fuite des stratégies vol stationnaire/chiffrement vers la croisière")
# les VINGT domaines précédents restent INTACTS
check(len(B.principes("rafraichir une piece")["liste"]) == 18
      and "secret_parfait" in B.decompose("chiffrer un message")
      and "plancher_radiatif" in B.decompose("isoler thermiquement"),
      "les 20 domaines précédents inchangés après l'ajout de la croisière (isolation)")

# ── 28) VINGT-DEUXIÈME DOMAINE : détecter un signal faible (nouvelle loi L19 = bruit de grenaille, SNR ≤ √N) ──
dde = B.decompose("detecter un signal faible")
check(dde["statut"] == "decompose", "besoin détection connu -> decompose")
check("grenaille" in dde["objectif_reel"].lower() and "photons" in dde["objectif_reel"].lower(),
      "objectif réel détection = bruit de grenaille, photons")
check("bruit_grenaille" in dde, "extras propres : le bruit de grenaille")
de_canaux = {c.canal for c in dde["canaux"]}
check(de_canaux == {"flux de photons", "autres bruits", "rendement quantique", "lumiere comprimee"},
      f"4 canaux de la détection ({de_canaux})")
prde = B.principes("detecter un signal faible")
pde = {e["nom"]: e for e in prde["liste"]}
# l'IMPOSSIBLE est RÉFUTÉ : SNR au-dessus de √N, et QE > 1
snr100 = pde["capteur « à SNR 100 sur 100 photons »"]
check(snr100["atome"].statut == A.REFUTE, "SNR 100 sur 100 photons -> RÉFUTÉ")
check(A.est_refute(snr100["atome"].contenu), "contenu réfuté (SNR 100) dans la garde")
qe12 = pde["capteur « à rendement quantique 1,2 »"]
check(qe12["atome"].statut == A.REFUTE, "rendement quantique 1,2 -> RÉFUTÉ")
# procédés réels (dont la lumière comprimée, exemptée) -> SUPPOSITIONS
for nom in ("grande ouverture / télescope (collecter plus de photons)", "comptage de photons (SPAD / PMT)",
            "lumière comprimée (squeezed, interférométrie)"):
    e = pde[nom]
    check(e["atome"].statut == A.SUPPOSITION, f"{nom} -> SUPPOSITION")
check(all(e["atome"].statut in (A.SUPPOSITION, A.REFUTE) for e in prde["liste"]), "aucun principe de détection promu en FAIT")
check("candidat pour detection_signal" in pde["comptage de photons (SPAD / PMT)"]["atome"].portee.condition,
      "portée des principes de détection nommant detection_signal")
# la loi L19 : SNR au-dessus de √N réfuté, capteur réel cohérent
st_de, _, loi_de = COH.juge_dispositif({"type": "detection", "nb_photons": 100, "rapport_signal_bruit": 100})
check(st_de == COH.VIOLE and loi_de == COH.L19, "juge : SNR 100 sur 100 photons -> VIOLE via L19")
check(COH.juge_dispositif({"type": "detection", "nb_photons": 10000, "rapport_signal_bruit": 80})[0]
      == COH.COHERENT_BORNE, "SNR 80 sur 10000 photons (< √N) -> cohérent, pas de faux positif")
# stratégies naturelles propres (bâtonnet, tapetum)
natde = B.strategies_naturelles("detecter un signal faible")
check(len(natde) >= 4 and any("bâtonnet" in s["exemple"].lower() for s in natde), "stratégies détection propres (bâtonnet)")
check(not any("aigle" in s["exemple"] for s in natde) and not any("frégate" in s["exemple"] for s in natde),
      "pas de fuite des stratégies optique/croisière vers la détection")
# les VINGT-ET-UN domaines précédents restent INTACTS
check(len(B.principes("rafraichir une piece")["liste"]) == 18
      and "trainee_induite_min" in B.decompose("voler loin")
      and "secret_parfait" in B.decompose("chiffrer un message"),
      "les 21 domaines précédents inchangés après l'ajout de la détection (isolation)")

# ── 29) VINGT-TROISIÈME DOMAINE : amplifier un signal (nouvelle loi L20 = facteur de bruit ≥ 1, pas d'amélioration du SNR) ──
dam = B.decompose("amplifier un signal")
check(dam["statut"] == "decompose", "besoin amplification connu -> decompose")
check("bruit" in dam["objectif_reel"].lower() and "snr" in dam["objectif_reel"].lower(),
      "objectif réel amplification = facteur de bruit, SNR préservé")
check("facteur_de_bruit_min" in dam, "extras propres : le facteur de bruit minimal")
am_canaux = {c.canal for c in dam["canaux"]}
check(am_canaux == {"premier etage", "temperature", "position", "phase sensible"},
      f"4 canaux de l'amplification ({am_canaux})")
pram = B.principes("amplifier un signal")
pam = {e["nom"]: e for e in pram["liste"]}
# l'IMPOSSIBLE est RÉFUTÉ : F < 1 et NF < 0 dB
f05 = pam["amplificateur « à facteur de bruit 0,5 »"]
check(f05["atome"].statut == A.REFUTE, "facteur de bruit 0,5 < 1 -> RÉFUTÉ")
check(A.est_refute(f05["atome"].contenu), "contenu réfuté (F 0,5) dans la garde")
nfm1 = pam["amplificateur « qui améliore le SNR » (NF −1 dB)"]
check(nfm1["atome"].statut == A.REFUTE, "NF -1 dB -> RÉFUTÉ")
# procédés réels (dont paramétrique à 0 dB) -> SUPPOSITIONS
for nom in ("amplificateur faible bruit en tête (LNA, Friis)", "amplificateur cryogénique (refroidi)",
            "amplificateur paramétrique / phase-sensible"):
    e = pam[nom]
    check(e["atome"].statut == A.SUPPOSITION, f"{nom} -> SUPPOSITION")
check(all(e["atome"].statut in (A.SUPPOSITION, A.REFUTE) for e in pram["liste"]), "aucun principe d'amplification promu en FAIT")
check("candidat pour amplification_signal" in pam["amplificateur faible bruit en tête (LNA, Friis)"]["atome"].portee.condition,
      "portée des principes d'amplification nommant amplification_signal")
# la loi L20 : F < 1 réfuté, LNA réaliste cohérent
st_am, _, loi_am = COH.juge_dispositif({"type": "amplification", "facteur_de_bruit": 0.5})
check(st_am == COH.VIOLE and loi_am == COH.L20, "juge : facteur de bruit 0,5 -> VIOLE via L20")
check(COH.juge_dispositif({"type": "amplification", "facteur_de_bruit_dB": 0.5})[0] == COH.COHERENT_BORNE,
      "LNA NF 0,5 dB (> 0) -> cohérent, pas de faux positif")
# stratégies naturelles propres (cochlée, osselets)
natam = B.strategies_naturelles("amplifier un signal")
check(len(natam) >= 4 and any("cochlée" in s["exemple"].lower() for s in natam), "stratégies amplification propres (cochlée)")
check(not any("bâtonnet" in s["exemple"] for s in natam) and not any("frégate" in s["exemple"] for s in natam),
      "pas de fuite des stratégies détection/croisière vers l'amplification")
# les VINGT-DEUX domaines précédents restent INTACTS
check(len(B.principes("rafraichir une piece")["liste"]) == 18
      and "bruit_grenaille" in B.decompose("detecter un signal faible")
      and "trainee_induite_min" in B.decompose("voler loin"),
      "les 22 domaines précédents inchangés après l'ajout de l'amplification (isolation)")

# ── 30) VINGT-QUATRIÈME DOMAINE : numériser / échantillonner (nouvelle loi L21 = Nyquist-Shannon, fs ≥ 2B) ──
dech = B.decompose("numeriser un signal")
check(dech["statut"] == "decompose", "besoin numérisation connu -> decompose")
check("nyquist" in dech["objectif_reel"].lower() and "bande" in dech["objectif_reel"].lower(),
      "objectif réel numérisation = Nyquist, couvrir la bande")
check("nyquist" in dech, "extras propres : la fréquence de Nyquist")
ech_canaux = {c.canal for c in dech["canaux"]}
check(ech_canaux == {"frequence d echantillonnage", "filtre anti-repliement", "parcimonie", "passe bande"},
      f"4 canaux de la numérisation ({ech_canaux})")
prech = B.principes("numeriser un signal")
pech = {e["nom"]: e for e in prech["liste"]}
# l'IMPOSSIBLE est RÉFUTÉ : sous 2B (reconstruction parfaite non parcimonieuse)
sous2b = pech["reconstruction parfaite « d'un 20 kHz échantillonné à 30 kHz »"]
check(sous2b["atome"].statut == A.REFUTE, "30k < 2*20k reconstruction parfaite -> RÉFUTÉ")
check(A.est_refute(sous2b["atome"].contenu), "contenu réfuté (30 kHz) dans la garde")
fseqb = pech["numériser « sans perte à la fréquence de la bande » (fs = B)"]
check(fseqb["atome"].statut == A.REFUTE, "fs = B < 2B -> RÉFUTÉ")
# procédés réels (dont l'acquisition comprimée parcimonieuse, exemptée) -> SUPPOSITIONS
for nom in ("échantillonnage à la fréquence de Nyquist (2B)", "acquisition comprimée (parcimonie)",
            "échantillonnage passe-bande (sous-échantillonnage)"):
    e = pech[nom]
    check(e["atome"].statut == A.SUPPOSITION, f"{nom} -> SUPPOSITION")
check(all(e["atome"].statut in (A.SUPPOSITION, A.REFUTE) for e in prech["liste"]), "aucun principe de numérisation promu en FAIT")
check("candidat pour numerisation_signal" in pech["échantillonnage à la fréquence de Nyquist (2B)"]["atome"].portee.condition,
      "portée des principes de numérisation nommant numerisation_signal")
# la loi L21 : reconstruction parfaite sous 2B réfutée, acquisition comprimée cohérente
st_ech, _, loi_ech = COH.juge_dispositif({"type": "echantillonnage", "bande_passante_Hz": 20000,
                                          "frequence_echantillonnage_Hz": 30000, "reconstruction_parfaite": True})
check(st_ech == COH.VIOLE and loi_ech == COH.L21, "juge : 30 kHz pour 20 kHz -> VIOLE via L21")
check(COH.juge_dispositif({"type": "echantillonnage", "bande_passante_Hz": 1000000,
                           "frequence_echantillonnage_Hz": 500000, "reconstruction_parfaite": True,
                           "signal_parcimonieux": True})[0] == COH.COHERENT_BORNE,
      "acquisition comprimée (parcimonieux) sous Nyquist -> cohérent, pas de faux positif")
# stratégies naturelles propres (vision, fovéa)
natech = B.strategies_naturelles("numeriser un signal")
check(len(natech) >= 4 and any("fovéa" in s["exemple"].lower() for s in natech), "stratégies numérisation propres (fovéa)")
check(not any("cochlée" in s["exemple"] for s in natech) and not any("bâtonnet" in s["exemple"] for s in natech),
      "pas de fuite des stratégies amplification/détection vers la numérisation")
# les VINGT-TROIS domaines précédents restent INTACTS
check(len(B.principes("rafraichir une piece")["liste"]) == 18
      and "facteur_de_bruit_min" in B.decompose("amplifier un signal")
      and "bruit_grenaille" in B.decompose("detecter un signal faible"),
      "les 23 domaines précédents inchangés après l'ajout de la numérisation (isolation)")

# ── 31) VINGT-CINQUIÈME DOMAINE : trier des données (nouvelle loi L22 = borne du tri par comparaison, ≥ log₂(n!)) ──
dtr = B.decompose("trier des donnees")
check(dtr["statut"] == "decompose", "besoin tri connu -> decompose")
check("comparaison" in dtr["objectif_reel"].lower() and "log" in dtr["objectif_reel"].lower(),
      "objectif réel tri = borne log₂(n!) du tri par comparaison")
check("borne_tri" in dtr, "extras propres : la borne du tri")
tr_canaux = {c.canal for c in dtr["canaux"]}
check(tr_canaux == {"algorithme optimal", "structure des cles", "tri partiel", "ordre preexistant"},
      f"4 canaux du tri ({tr_canaux})")
prtr = B.principes("trier des donnees")
ptr = {e["nom"]: e for e in prtr["liste"]}
# l'IMPOSSIBLE est RÉFUTÉ : tri par comparaison arbitraire sous log₂(n!)
tr1m = ptr["tri par comparaison « d'un million d'éléments en un million de comparaisons »"]
check(tr1m["atome"].statut == A.REFUTE, "1e6 comparaisons < log2(1e6!) -> RÉFUTÉ")
check(A.est_refute(tr1m["atome"].contenu), "contenu réfuté (1e6 comparaisons) dans la garde")
tr8 = ptr["tri par comparaison « de 8 éléments en 10 comparaisons »"]
check(tr8["atome"].statut == A.REFUTE, "8 éléments en 10 comparaisons -> RÉFUTÉ")
# procédés réels (dont radix non comparatif et adaptatif, exemptés) -> SUPPOSITIONS
for nom in ("tri par fusion / par tas (n·log n optimal)", "tri par base (radix, non comparatif)",
            "tri adaptatif (Timsort, exploite l'ordre préexistant)"):
    e = ptr[nom]
    check(e["atome"].statut == A.SUPPOSITION, f"{nom} -> SUPPOSITION")
check(all(e["atome"].statut in (A.SUPPOSITION, A.REFUTE) for e in prtr["liste"]), "aucun principe de tri promu en FAIT")
check("candidat pour tri_donnees" in ptr["tri par fusion / par tas (n·log n optimal)"]["atome"].portee.condition,
      "portée des principes de tri nommant tri_donnees")
# la loi L22 : tri par comparaison arbitraire sous la borne réfuté, radix cohérent
st_tr, _, loi_tr = COH.juge_dispositif({"type": "tri", "tri_par_comparaison": True, "entree_arbitraire": True,
                                        "nb_elements": 1000000, "nb_comparaisons": 1000000})
check(st_tr == COH.VIOLE and loi_tr == COH.L22, "juge : 1e6 comparaisons arbitraire -> VIOLE via L22")
check(COH.juge_dispositif({"type": "tri", "tri_par_comparaison": False, "nb_elements": 1000000,
                           "nb_comparaisons": 1000000})[0] == COH.COHERENT_BORNE,
      "radix (non comparatif) O(n) -> cohérent, pas de faux positif")
# stratégies naturelles propres (rivière, sédimentation)
nattr = B.strategies_naturelles("trier des donnees")
check(len(nattr) >= 4 and any("rivière" in s["exemple"].lower() for s in nattr), "stratégies tri propres (rivière)")
check(not any("fovéa" in s["exemple"] for s in nattr) and not any("cochlée" in s["exemple"] for s in nattr),
      "pas de fuite des stratégies numérisation/amplification vers le tri")
# les VINGT-QUATRE domaines précédents restent INTACTS
check(len(B.principes("rafraichir une piece")["liste"]) == 18
      and "nyquist" in B.decompose("numeriser un signal")
      and "facteur_de_bruit_min" in B.decompose("amplifier un signal"),
      "les 24 domaines précédents inchangés après l'ajout du tri (isolation)")

# ── 32) VINGT-SIXIÈME DOMAINE : rechercher dans des données (nouvelle loi L23 = borne de la recherche, ≥ n/2) ──
dre = B.decompose("rechercher un element")
check(dre["statut"] == "decompose", "besoin recherche connu -> decompose")
check("index" in dre["objectif_reel"].lower() and "structur" in dre["objectif_reel"].lower(),
      "objectif réel recherche = pré-structurer / indexer")
check("borne_recherche" in dre, "extras propres : la borne de la recherche")
re_canaux = {c.canal for c in dre["canaux"]}
check(re_canaux == {"index", "hachage", "filtre probabiliste", "quantique"}, f"4 canaux de la recherche ({re_canaux})")
prre = B.principes("rechercher un element")
pre = {e["nom"]: e for e in prre["liste"]}
# l'IMPOSSIBLE est RÉFUTÉ : recherche non indexée sous n/2
re20 = pre["recherche « dans un million de non indexés en 20 examens »"]
check(re20["atome"].statut == A.REFUTE, "20 examens < n/2 non indexé -> RÉFUTÉ")
check(A.est_refute(re20["atome"].contenu), "contenu réfuté (20 examens) dans la garde")
re100 = pre["recherche « dans un milliard de non indexés en 100 examens »"]
check(re100["atome"].statut == A.REFUTE, "100 examens << n/2 -> RÉFUTÉ")
# procédés réels (dont indexés et quantique, exemptés) -> SUPPOSITIONS
for nom in ("parcours linéaire (sans structure)", "table de hachage (O(1))", "recherche quantique (Grover)"):
    e = pre[nom]
    check(e["atome"].statut == A.SUPPOSITION, f"{nom} -> SUPPOSITION")
check(all(e["atome"].statut in (A.SUPPOSITION, A.REFUTE) for e in prre["liste"]), "aucun principe de recherche promu en FAIT")
check("candidat pour recherche_donnees" in pre["parcours linéaire (sans structure)"]["atome"].portee.condition,
      "portée des principes de recherche nommant recherche_donnees")
# la loi L23 : recherche non indexée sous n/2 réfutée, table de hachage cohérente
st_re, _, loi_re = COH.juge_dispositif({"type": "recherche", "nb_elements": 1000000, "nb_requetes_moyennes": 20})
check(st_re == COH.VIOLE and loi_re == COH.L23, "juge : 20 examens non indexé -> VIOLE via L23")
check(COH.juge_dispositif({"type": "recherche", "nb_elements": 1000000, "nb_requetes_moyennes": 1,
                           "donnees_indexees": True})[0] == COH.COHERENT_BORNE,
      "hachage O(1) (indexé) -> cohérent, pas de faux positif")
# stratégies naturelles propres (chien pisteur, pigeon)
natre = B.strategies_naturelles("rechercher un element")
check(len(natre) >= 4 and any("pisteur" in s["exemple"].lower() for s in natre), "stratégies recherche propres (chien pisteur)")
check(not any("rivière" in s["exemple"] for s in natre) and not any("fovéa" in s["exemple"] for s in natre),
      "pas de fuite des stratégies tri/numérisation vers la recherche")
# les VINGT-CINQ domaines précédents restent INTACTS
check(len(B.principes("rafraichir une piece")["liste"]) == 18
      and "borne_tri" in B.decompose("trier des donnees")
      and "nyquist" in B.decompose("numeriser un signal"),
      "les 25 domaines précédents inchangés après l'ajout de la recherche (isolation)")

# ── 33) VINGT-SEPTIÈME DOMAINE : paralléliser un calcul (nouvelle loi L24 = loi d'Amdahl, accélération ≤ 1/s) ──
dpa = B.decompose("accelerer un calcul")
check(dpa["statut"] == "decompose", "besoin parallélisation connu -> decompose")
check("amdahl" in dpa["objectif_reel"].lower() and "fraction" in dpa["objectif_reel"].lower(),
      "objectif réel parallélisation = loi d'Amdahl, fraction série")
check("amdahl" in dpa, "extras propres : la loi d'Amdahl")
pa_canaux = {c.canal for c in dpa["canaux"]}
check(pa_canaux == {"fraction serie", "agrandir le probleme", "communication", "equilibrage"},
      f"4 canaux de la parallélisation ({pa_canaux})")
prpa = B.principes("accelerer un calcul")
ppa = {e["nom"]: e for e in prpa["liste"]}
# l'IMPOSSIBLE est RÉFUTÉ : accélération au-dessus de la borne d'Amdahl
acc20 = ppa["accélération « ×20 » avec 10 % de série"]
check(acc20["atome"].statut == A.REFUTE, "×20 avec 10% série (> 1/s=10) -> RÉFUTÉ")
check(A.est_refute(acc20["atome"].contenu), "contenu réfuté (×20) dans la garde")
acclin = ppa["accélération LINÉAIRE (×100 sur 100 cœurs) avec 5 % de série"]
check(acclin["atome"].statut == A.REFUTE, "×100 linéaire avec 5% série -> RÉFUTÉ")
# procédés réels (dont Gustafson problème agrandi, exempté) -> SUPPOSITIONS
for nom in ("réduction de la fraction série (algorithme)", "parallélisme massif (GPU, milliers de cœurs)",
            "problème agrandi (loi de Gustafson, weak scaling)"):
    e = ppa[nom]
    check(e["atome"].statut == A.SUPPOSITION, f"{nom} -> SUPPOSITION")
check(all(e["atome"].statut in (A.SUPPOSITION, A.REFUTE) for e in prpa["liste"]), "aucun principe de parallélisation promu en FAIT")
check("candidat pour parallelisation_calcul" in ppa["réduction de la fraction série (algorithme)"]["atome"].portee.condition,
      "portée des principes de parallélisation nommant parallelisation_calcul")
# la loi L24 : accélération au-dessus d'Amdahl réfutée, sous la borne cohérente
st_pa, _, loi_pa = COH.juge_dispositif({"type": "parallelisation", "fraction_serie": 0.1, "nb_processeurs": 1000,
                                        "acceleration": 20})
check(st_pa == COH.VIOLE and loi_pa == COH.L24, "juge : ×20 avec s=0,1 -> VIOLE via L24")
check(COH.juge_dispositif({"type": "parallelisation", "fraction_serie": 0.05, "nb_processeurs": 16,
                           "acceleration": 9})[0] == COH.COHERENT_BORNE,
      "×9 avec s=0,05 sur 16 cœurs (< Amdahl) -> cohérent, pas de faux positif")
# stratégies naturelles propres (étourneaux, corail)
natpa = B.strategies_naturelles("accelerer un calcul")
check(len(natpa) >= 4 and any("étourneaux" in s["exemple"].lower() for s in natpa), "stratégies parallélisation propres (étourneaux)")
check(not any("pisteur" in s["exemple"] for s in natpa) and not any("rivière" in s["exemple"] for s in natpa),
      "pas de fuite des stratégies recherche/tri vers la parallélisation")
# les VINGT-SIX domaines précédents restent INTACTS
check(len(B.principes("rafraichir une piece")["liste"]) == 18
      and "borne_recherche" in B.decompose("rechercher un element")
      and "borne_tri" in B.decompose("trier des donnees"),
      "les 26 domaines précédents inchangés après l'ajout de la parallélisation (isolation)")

# ── 34) VINGT-HUITIÈME DOMAINE : cryogénie / zéro absolu (nouvelle loi L25 = troisième principe, 0 K inatteignable) ──
dcy = B.decompose("refroidir vers le zero absolu")
check(dcy["statut"] == "decompose", "besoin cryogénie connu -> decompose")
check("absolu" in dcy["objectif_reel"].lower() and "entropie" in dcy["objectif_reel"].lower(),
      "objectif réel cryogénie = zéro absolu inatteignable, entropie")
check("zero_absolu" in dcy, "extras propres : le zéro absolu inatteignable")
cy_canaux = {c.canal for c in dcy["canaux"]}
check(cy_canaux == {"etagement", "desaimantation", "refroidissement optique", "detente de gaz"},
      f"4 canaux de la cryogénie ({cy_canaux})")
prcy = B.principes("refroidir vers le zero absolu")
pcy = {e["nom"]: e for e in prcy["liste"]}
# l'IMPOSSIBLE est RÉFUTÉ : atteindre 0 K, refroidir sous 0
z0 = pcy["atteinte du zéro absolu (0 K)"]
check(z0["atome"].statut == A.REFUTE, "atteindre 0 K -> RÉFUTÉ")
check(A.est_refute(z0["atome"].contenu), "contenu réfuté (0 K) dans la garde")
tm1 = pcy["refroidissement « à −1 K »"]
check(tm1["atome"].statut == A.REFUTE, "-1 K -> RÉFUTÉ")
# procédés réels -> SUPPOSITIONS
for nom in ("réfrigérateur à dilution (He³/He⁴)", "refroidissement évaporatif (condensat de Bose-Einstein)",
            "étagement en cascade complet"):
    e = pcy[nom]
    check(e["atome"].statut == A.SUPPOSITION, f"{nom} -> SUPPOSITION")
check(all(e["atome"].statut in (A.SUPPOSITION, A.REFUTE) for e in prcy["liste"]), "aucun principe de cryogénie promu en FAIT")
check("candidat pour refroidissement_cryogenique" in pcy["réfrigérateur à dilution (He³/He⁴)"]["atome"].portee.condition,
      "portée des principes de cryogénie nommant refroidissement_cryogenique")
# la loi L25 : atteindre 0 K réfuté, nK réel cohérent
st_cy, _, loi_cy = COH.juge_dispositif({"type": "cryogenie", "atteint_zero_absolu": True})
check(st_cy == COH.VIOLE and loi_cy == COH.L25, "juge : atteindre 0 K -> VIOLE via L25")
check(COH.juge_dispositif({"type": "cryogenie", "temperature_atteinte_K": 1e-9})[0] == COH.COHERENT_BORNE,
      "1 nK (> 0) -> cohérent, pas de faux positif")
# stratégies naturelles propres (nébuleuse du Boomerang, fond cosmologique)
natcy = B.strategies_naturelles("refroidir vers le zero absolu")
check(len(natcy) >= 4 and any("boomerang" in s["exemple"].lower() for s in natcy), "stratégies cryogénie propres (Boomerang)")
check(not any("étourneaux" in s["exemple"] for s in natcy) and not any("forêt" in s["exemple"] for s in natcy),
      "pas de fuite des stratégies parallélisation/cooling vers la cryogénie")
# les VINGT-SEPT domaines précédents restent INTACTS
check(len(B.principes("rafraichir une piece")["liste"]) == 18
      and "amdahl" in B.decompose("accelerer un calcul")
      and "borne_recherche" in B.decompose("rechercher un element"),
      "les 27 domaines précédents inchangés après l'ajout de la cryogénie (isolation)")

# ── 35) VINGT-NEUVIÈME DOMAINE : mesurer le temps (nouvelle loi L26 = limite quantique standard d'une horloge) ──
dho = B.decompose("mesurer le temps")
check(dho["statut"] == "decompose", "besoin mesure du temps connu -> decompose")
check("atomes" in dho["objectif_reel"].lower() and "quantique" in dho["objectif_reel"].lower(),
      "objectif réel horloge = N atomes, bruit quantique")
check("limite_quantique_standard" in dho, "extras propres : la limite quantique standard")
ho_canaux = {c.canal for c in dho["canaux"]}
check(ho_canaux == {"frequence", "nombre d atomes", "interrogation", "intrication"},
      f"4 canaux de l'horloge ({ho_canaux})")
prho = B.principes("mesurer le temps")
pho = {e["nom"]: e for e in prho["liste"]}
# l'IMPOSSIBLE est RÉFUTÉ : stabilité sous la LQS (non intriquée)
h19 = pho["horloge « à 1e-19 » non intriquée (10⁴ atomes optiques)"]
check(h19["atome"].statut == A.REFUTE, "1e-19 non intriquée < LQS -> RÉFUTÉ")
check(A.est_refute(h19["atome"].contenu), "contenu réfuté (1e-19) dans la garde")
cs16 = pho["césium « à 1e-16 » non intriqué"]
check(cs16["atome"].statut == A.REFUTE, "césium 1e-16 < LQS -> RÉFUTÉ")
# procédés réels (dont horloge intriquée, exemptée) -> SUPPOSITIONS
for nom in ("horloge optique (fréquence plus haute)", "horloge à réseau optique (nombreux atomes)",
            "horloge intriquée (spin squeezing)"):
    e = pho[nom]
    check(e["atome"].statut == A.SUPPOSITION, f"{nom} -> SUPPOSITION")
check(all(e["atome"].statut in (A.SUPPOSITION, A.REFUTE) for e in prho["liste"]), "aucun principe d'horloge promu en FAIT")
check("candidat pour mesure_temps" in pho["horloge optique (fréquence plus haute)"]["atome"].portee.condition,
      "portée des principes d'horloge nommant mesure_temps")
# la loi L26 : stabilité sous la LQS réfutée, horloge optique réelle cohérente
st_ho, _, loi_ho = COH.juge_dispositif({"type": "horloge", "frequence_Hz": 5e14, "temps_s": 1,
                                        "nb_atomes": 10000, "stabilite": 1e-19})
check(st_ho == COH.VIOLE and loi_ho == COH.L26, "juge : 1e-19 non intriquée -> VIOLE via L26")
check(COH.juge_dispositif({"type": "horloge", "frequence_Hz": 5e14, "temps_s": 1, "nb_atomes": 10000,
                           "stabilite": 1e-16})[0] == COH.COHERENT_BORNE,
      "horloge optique 1e-16 (> LQS) -> cohérent, pas de faux positif")
# stratégies naturelles propres (circadienne, cigale)
natho = B.strategies_naturelles("mesurer le temps")
check(len(natho) >= 4 and any("circadienne" in s["exemple"].lower() for s in natho), "stratégies horloge propres (circadienne)")
check(not any("boomerang" in s["exemple"].lower() for s in natho) and not any("étourneaux" in s["exemple"] for s in natho),
      "pas de fuite des stratégies cryogénie/parallélisation vers l'horloge")
# les VINGT-HUIT domaines précédents restent INTACTS
check(len(B.principes("rafraichir une piece")["liste"]) == 18
      and "zero_absolu" in B.decompose("refroidir vers le zero absolu")
      and "amdahl" in B.decompose("accelerer un calcul"),
      "les 28 domaines précédents inchangés après l'ajout de l'horloge (isolation)")

# ── 36) TRENTIÈME DOMAINE : calculer vite (nouvelle loi L27 = limite de Margolus-Levitin, ops/s ≤ 2E/πℏ) ──
dvc = B.decompose("calculer vite")
check(dvc["statut"] == "decompose", "besoin vitesse de calcul connu -> decompose")
check("margolus" in dvc["objectif_reel"].lower() and "seconde" in dvc["objectif_reel"].lower(),
      "objectif réel vitesse de calcul = Margolus-Levitin, opérations par seconde")
check("margolus_levitin" in dvc, "extras propres : la limite de Margolus-Levitin")
vc_canaux = {c.canal for c in dvc["canaux"]}
check(vc_canaux == {"energie", "moins d operations", "parallelisme", "substrat physique"},
      f"4 canaux de la vitesse de calcul ({vc_canaux})")
prvc = B.principes("calculer vite")
pvc = {e["nom"]: e for e in prvc["liste"]}
# l'IMPOSSIBLE est RÉFUTÉ : ops/s au-dessus de 2E/πℏ
op40 = pvc["processeur « à 1e40 opérations/s avec 1 J »"]
check(op40["atome"].statut == A.REFUTE, "1e40 ops/s avec 1 J > ML -> RÉFUTÉ")
check(A.est_refute(op40["atome"].contenu), "contenu réfuté (1e40 ops) dans la garde")
op60 = pvc["calculateur « à 1e60 opérations/s avec 1 MJ »"]
check(op60["atome"].statut == A.REFUTE, "1e60 ops/s avec 1 MJ > ML -> RÉFUTÉ")
# procédés réels (dont l'ordinateur ultime de Lloyd, à la borne) -> SUPPOSITIONS
for nom in ("processeur classique (référence)", "ordinateur ultime de Lloyd (1 kg à la borne)",
            "réduction algorithmique (moins de calcul)"):
    e = pvc[nom]
    check(e["atome"].statut == A.SUPPOSITION, f"{nom} -> SUPPOSITION")
check(all(e["atome"].statut in (A.SUPPOSITION, A.REFUTE) for e in prvc["liste"]), "aucun principe de vitesse de calcul promu en FAIT")
check("candidat pour vitesse_calcul" in pvc["processeur classique (référence)"]["atome"].portee.condition,
      "portée des principes de vitesse de calcul nommant vitesse_calcul")
# la loi L27 : ops/s au-dessus de ML réfutée, supercalculateur cohérent
st_vc, _, loi_vc = COH.juge_dispositif({"type": "vitesse_calcul", "operations_par_seconde": 1e40, "energie_J": 1})
check(st_vc == COH.VIOLE and loi_vc == COH.L27, "juge : 1e40 ops/s avec 1 J -> VIOLE via L27")
check(COH.juge_dispositif({"type": "vitesse_calcul", "operations_par_seconde": 1e18, "energie_J": 1000})[0]
      == COH.COHERENT_BORNE, "supercalculateur 1e18 ops/s (<< ML) -> cohérent, pas de faux positif")
# stratégies naturelles propres (ATP synthase, ribosome)
natvc = B.strategies_naturelles("calculer vite")
check(len(natvc) >= 4 and any("atp synthase" in s["exemple"].lower() for s in natvc), "stratégies vitesse de calcul propres (ATP synthase)")
check(not any("circadienne" in s["exemple"] for s in natvc) and not any("boomerang" in s["exemple"].lower() for s in natvc),
      "pas de fuite des stratégies horloge/cryogénie vers la vitesse de calcul")
# les VINGT-NEUF domaines précédents restent INTACTS
check(len(B.principes("rafraichir une piece")["liste"]) == 18
      and "limite_quantique_standard" in B.decompose("mesurer le temps")
      and "zero_absolu" in B.decompose("refroidir vers le zero absolu"),
      "les 29 domaines précédents inchangés après l'ajout de la vitesse de calcul (isolation)")

# ── 16) REGISTRE DE DOMAINES (généralisation 2026-07-12) : ajouter un domaine = l'enregistrer, RIEN d'autre ──
check(B.domaines_connus() == ["rafraichissement_confort", "chauffage_confort", "dessalement_eau",
                              "stockage_energie", "capture_co2", "eau_potable_air", "propulsion", "eclairage",
                              "calcul", "communication", "captation_solaire", "production_hydrogene",
                              "sustentation", "resolution_optique", "energie_eolienne", "propulsion_spatiale",
                              "production_alimentaire", "compression_information", "isolation_thermique",
                              "confidentialite_information", "vol_croisiere", "detection_signal",
                              "amplification_signal", "numerisation_signal", "tri_donnees", "recherche_donnees",
                              "parallelisation_calcul", "refroidissement_cryogenique", "mesure_temps",
                              "vitesse_calcul"],
      "trente domaines modélisés, dans l'ordre d'enregistrement")
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
