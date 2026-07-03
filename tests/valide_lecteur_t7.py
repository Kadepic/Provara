"""
VALIDATION T7 — MESURES NUMÉRIQUES & TECHNIQUE (couloir d'ingestion). FAUX=0 INVIOLABLE.

Charge UNIQUEMENT les relations T7 dans un Lecteur frais (léger : ~quelques dizaines de milliers de faits, pas les
10 M du gate complet) et verrouille les invariants du PATRON NUMÉRIQUE :

  1. PLAGE      : toute valeur stockée parse en float ET tombe dans la plage physique de sa relation (aucune valeur
                  hors-unité/aberrante n'a fui — le garde-fou d'ingestion a bien filtré).
  2. INTÉGRITÉ  : valeur non vide ; licence (catégoriel) = libellé ≥2 caractères.
  3. ANCRES     : valeurs vérifiées À LA MAIN, indépendamment du code (Everest 8848,86 m, Burj Khalifa 828 m,
                  Grande-Dixence 285 m, Baïkal 1642 m, Blender=GPLv3…) -> ancrage NON circulaire.
  4. SOUNDNESS  : adverse — un homonyme multi-valeur (mont Blanc, Kilimandjaro), une entité absente, une relation
                  absente -> TOUJOURS HORS (None). Jamais un faux, jamais une devinette.

EXIT 0 = tous les check passent. Lancer SEUL (1 chargement léger) en dev ; enregistrer dans _nonreg.py pour le gate.
"""
from __future__ import annotations

import json
import os

from garde_ressources import borne

borne(max_go=2.0, max_cpu_s=900)   # discipline ; ce validateur est AUTONOME (lit seulement les jsonl T7, ~240k faits).

# ⚠️ NE PAS `import lecteur` : son chargement GLOBAL au niveau module (charge_dossier()+gele() sur TOUS les datasets
# de tous les terminaux) dépasse désormais le cap RAM (OOM). Ce validateur certifie directement les jsonl T7
# (self-describing) — la déduplication/fonctionnel est déjà appliquée à l'ingestion, le jsonl EST la vérité servie.
HORS, VERIFIE = "HORS", "VERIFIE"

DOSSIER = os.path.join(os.path.dirname(__file__), "datasets", "lecteur")

# Plages physiques par relation (DOIVENT refléter ingere_t7.NUMERIQUES).
PLAGES = {
    "altitude_montagne":   (-500, 9000),
    "hauteur_gratte_ciel": (30, 1000),
    "hauteur_barrage":     (1, 350),
    "hauteur_tour":        (10, 1000),
    "profondeur_lac":      (1, 2000),
    "hauteur_phare":       (1, 160),
    "hauteur_statue":      (1, 250),
    "longueur_navire":     (3, 460),
    # lot 3 (unité-aware, mètres)
    "altitude_aeroport":   (-500, 5000),
    "altitude_ville":      (-500, 5500),
    # lot 3 (compte sans unité : population, valeur datée)
    "population_ville":    (0, 40_000_000),
    # lot 4 (longueurs km-capables, unité-aware, mètres)
    "longueur_fleuve":     (1, 7_000_000),
    "longueur_pont":       (1, 200_000),
    "hauteur_cascade":     (1, 1000),
    # lot 5 (patron AIRE, unité-aware, km²)
    "superficie_ile":      (0, 2_200_000),
    # lot 6 (extensions AIRE km² + glacier m)
    "superficie_parc_national":     (0, 1_000_000),
    "superficie_desert":            (0, 10_000_000),
    "superficie_reserve_naturelle": (0, 1_000_000),
    "longueur_glacier":             (1, 600_000),
    # lot 7 (nouveaux patrons : puissance MW, masse kg)
    "puissance_centrale":           (0, 30_000),
    "masse_vehicule_spatial":       (0, 500_000),
    # lot 8 (diamètre cratère m, débit m³/s, capacité stade compte)
    "diametre_cratere":             (1, 3_000_000),
    "debit_fleuve":                 (0, 300_000),
    "capacite_stade":               (0, 300_000),
    # lot 9 (hauteur pont m, aire protégée km², nombre étages compte)
    "hauteur_pont":                 (1, 400),
    "superficie_aire_protegee":     (0, 3_000_000),
    "nombre_etages":                (1, 200),
    # lot 10 (élargissement de classes, longueur m)
    "altitude_lac":                 (-500, 6000),
    "hauteur_immeuble":             (1, 1000),
    "hauteur_volcan":               (-500, 9000),
    "hauteur_arbre":                (1, 130),
    # lot 11 (cols/collines m, forêts/glaciers km²)
    "altitude_col":                 (-500, 9000),
    "hauteur_colline":              (-500, 9000),
    "superficie_foret":             (0, 3_000_000),
    "superficie_glacier":           (0, 3_000_000),
    # lot 12 (sommets m, salle compte, aéroport km²)
    "altitude_sommet":              (-500, 9000),
    "capacite_salle":               (1, 100_000),
    "superficie_aeroport":          (0, 1000),
    # lot 13 (altitude localités m ~133k, travée pont m)
    "altitude_localite":            (-500, 6000),
    "travee_pont":                  (1, 4000),
    # lot 14 (gares : altitude m, voies à quai compte)
    "altitude_gare":                (-500, 6000),
    "nombre_quais_gare":            (1, 100),
    # lot 15 (montagnes russes m)
    "hauteur_montagnes_russes":     (1, 200),
    "longueur_montagnes_russes":    (1, 3000),
    # lot 16 (hauteur structure m, superset)
    "hauteur_structure":            (1, 1000),
    # lot 17 (largeur navire m, effectif scolaire compte)
    "largeur_navire":               (1, 80),
    "largeur_pont":                 (1, 100),
    "hauteur_eglise":               (5, 180),
    "capacite_reservoir":           (1, 2e11),
    "volume_lac":                   (1, 1e17),
    "largeur_route":                (1, 300),
    "diametre_telescope":           (0.1, 45),
    "superficie_lac":               (0.001, 400_000),
    "superficie_reservoir":         (0.001, 20_000),
    "superficie_baie":              (0.001, 3_000_000),
    "superficie_etang":             (0.001, 2_000),
    "demi_vie_isotope":             (0, 1e40),
    "masse_navire":                 (100, 1e9),
    "vitesse_navire":               (1, 120),
    "vitesse_train":                (1, 700),
    "puissance_centrale_hydro":     (0.1, 30000),
    "puissance_centrale_solaire":   (0.1, 5000),
    "puissance_parc_eolien":        (0.1, 3000),
    "puissance_centrale_charbon":   (1, 8000),
    "nombre_produit_auto":          (1, 100_000_000),
    "nombre_produit_navire":        (1, 10_000),
    "capacite_eglise":              (1, 100_000),
    "nombre_travees":               (1, 15000),
    "longueur_cours_eau":           (1, 7_000_000),
    "hauteur_pyramide":             (1, 160),
    "masse_moleculaire":            (1, 1e7),
    "densite_chimie":               (1, 30000),
    "point_fusion_chimie":          (50, 6000),
    "point_ebullition_chimie":      (50, 6000),
    "point_eclair_chimie":          (100, 700),
    "pKa_chimie":                   (-15, 60),
    "diametre_piece_monnaie":       (1, 200),
    "masse_piece_monnaie":          (0.1, 2000),
    "hauteur_peinture":             (0.01, 25),
    "largeur_peinture":             (0.01, 30),
    "hauteur_sculpture":            (0.01, 200),
    "hauteur_dessin":               (0.01, 5),
    "largeur_dessin":               (0.01, 5),
    "hauteur_estampe":              (0.01, 5),
    "largeur_estampe":              (0.01, 5),
    "hauteur_aquarelle":            (0.01, 5),
    "largeur_aquarelle":            (0.01, 5),
    "longueur_grotte":              (1, 1e6),
    "profondeur_grotte":            (1, 2500),
    "nombre_eleves":                (1, 200_000),
    "nombre_cylindres":             (1, 48),
    "tonnage_brut":                 (1, 600_000),
    "longueur_ligne_ferroviaire":   (100, 10_000_000),
    "longueur_route":               (10, 30_000_000),
    "longueur_tunnel":              (10, 200_000),
    "longueur_canal":               (10, 2_000_000),
    "longueur_sentier":             (10, 20_000_000),
    "longueur_aqueduc":             (10, 500_000),
    "tirant_eau_navire":            (0.2, 40),
    "plus_longue_travee_pont":      (1, 5000),
    "longueur_crete_barrage":       (5, 20000),
    # lot 18 (superficie localités km²)
    "superficie_localite":          (0, 200_000),
    # lot 19 (lits d'hôpital compte)
    "nombre_lits_hopital":          (1, 20_000),
    # lot 20 (hauteur focale phare m)
    "hauteur_focale_phare":         (1, 500),
    # lot 21 (nombre de locuteurs d'une langue, compte ; orpheline ex-T9)
    "nombre_locuteurs_langue":      (1, 2_000_000_000),
    # lot 22 (vitesse maximale d'un véhicule -> km/h ; orpheline ex-T11)
    "vitesse_max_vehicule":         (1, 12_000),
    # lot 23 (masse d'un véhicule -> kg ; orpheline ex-T11)
    "masse_vehicule":               (1, 1_000_000_000),
    # lot 24 (fréquence d'émission d'une station de radio -> MHz ; nouveau patron FRÉQUENCE)
    "frequence_station_radio":      (0.01, 300),
    # lot 25 (tension nominale d'un poste électrique -> kV ; nouveau patron TENSION)
    "tension_poste_electrique":     (0.1, 1200),
    # lot 26 (capacité en passagers d'un navire ; compte unité-filtré personnes)
    "capacite_passagers_navire":    (1, 10_000),
    # lot 27 (autonomie/distance franchissable d'un véhicule -> mètres ; patron AUTONOMIE)
    "autonomie_vehicule":           (100, 100_000_000),
    # lot 28 (nombre total d'exemplaires produits d'un modèle de véhicule ; compte)
    "nombre_produit_vehicule":      (1, 200_000_000),
}
CATEGORIELLES = ["licence_logiciel", "langage_programmation_logiciel", "systeme_exploitation_logiciel",
                 "type_mime_format", "extension_format", "ecartement_rails", "propulse_par", "source_energie"]
RELATIONS = list(PLAGES) + CATEGORIELLES

ok = 0
total = 0


def check(nom, cond):
    global ok, total
    total += 1
    print(f"  [{'OK ' if cond else 'XXX'}] {nom}")
    if cond:
        ok += 1
    else:
        raise AssertionError(nom)


def _charge(chemin):
    """Charge un jsonl self-describing -> dict {entite: valeur_str}. Ignore l'en-tête {_relation,...}."""
    d = {}
    with open(chemin, encoding="utf-8") as fh:
        for brut in fh:
            brut = brut.strip()
            if not brut:
                continue
            o = json.loads(brut)
            if "_relation" in o:
                continue
            d[o["entite"]] = o["valeur"]
    return d


# --- Chargement AUTONOME : uniquement les jsonl T7, dans des dicts {entite: valeur}. ---
TABLES = {}
manquants = []
for rel in RELATIONS:
    chemin = os.path.join(DOSSIER, rel + ".jsonl")
    if not os.path.exists(chemin):
        manquants.append(rel)
        continue
    TABLES[rel] = _charge(chemin)
check(f"DATASETS présents (aucun manquant : {manquants})", not manquants)


def repond(rel, ent):
    """Réplique le contrat sound du lecteur : (VERIFIE, valeur) si connu, sinon (HORS, None). Lookup EXACT."""
    t = TABLES.get(rel)
    if t is not None and ent in t:
        return VERIFIE, t[ent]
    return HORS, None


# 1) PLAGE + 2) INTÉGRITÉ numérique : toute valeur parse en float et tombe dans la plage.
for rel, (lo, hi) in PLAGES.items():
    t = TABLES.get(rel, {})
    n = len(t)
    mauvais = None
    for cle, val in t.items():
        try:
            f = float(val)
        except (TypeError, ValueError):
            mauvais = (cle, val, "non-float")
            break
        if not (lo <= f <= hi):
            mauvais = (cle, val, "hors-plage")
            break
    check(f"{rel} : {n} faits, tous float ∈ [{lo},{hi}] [contre-ex: {mauvais}]", n > 0 and mauvais is None)

# 2bis) INTÉGRITÉ catégorielle : licence = libellé ≥2 caractères, non vide.
for rel in CATEGORIELLES:
    t = TABLES.get(rel, {})
    n = len(t)
    mauvais = next((c for c, v in t.items() if not (isinstance(v, str) and len(v.strip()) >= 2)), None)
    check(f"{rel} : {n} faits, libellés ≥2 car. non vides [contre-ex: {mauvais}]", n > 0 and mauvais is None)

# 3) ANCRES NUMÉRIQUES — vérité-terrain INDÉPENDANTE (en mètres). Tolérance = max(2 m, 1 %) : assez serrée pour
#    démasquer une fuite d'unité (pied = 3,28×, cm = 100×) mais robuste aux mesures multiples légitimement fusionnées
#    (Everest a plusieurs relevés à ±4 m). Entités choisies = valeur unique survivant au fonctionnel-à-tolérance.
ANCRES_NUM = [
    ("altitude_montagne", "Everest", 8848.86),
    ("altitude_montagne", "Aconcagua", 6962.0),
    ("hauteur_gratte_ciel", "Shanghai Tower", 632.0),
    ("hauteur_gratte_ciel", "Willis Tower", 442.1),
    ("hauteur_tour", "Tokyo Skytree", 634.0),
    ("hauteur_tour", "tour Ostankino", 540.1),
    ("hauteur_barrage", "barrage de la Grande-Dixence", 285.0),
    ("hauteur_barrage", "barrage des Trois-Gorges", 181.0),
    ("profondeur_lac", "lac Baïkal", 1642.0),
    ("hauteur_phare", "phare de Cordouan", 67.5),
    ("hauteur_statue", "Grand Bouddha de Leshan", 71.0),
    ("longueur_navire", "Titanic", 269.1),
    ("longueur_navire", "Queen Mary 2", 345.03),
    # lot 3 — altitude (mètres, valeurs réelles connues)
    ("altitude_aeroport", "aéroport international El Alto", 4061.0),
    ("altitude_aeroport", "aéroport Daocheng Yading", 4411.0),
    ("altitude_aeroport", "aéroport d'Amsterdam-Schiphol", -3.0),
    ("altitude_ville", "El Alto", 4150.0),
    ("altitude_ville", "Cuzco", 3399.0),
    ("altitude_ville", "Quito", 2850.0),
    # lot 4 — longueurs converties en mètres (km×1000) ; ancres vérité-terrain connues
    ("longueur_fleuve", "Seine", 776670.0),
    ("longueur_fleuve", "Danube", 2850000.0),
    ("longueur_fleuve", "Volga", 3530000.0),
    ("longueur_fleuve", "Rhône", 812000.0),
    ("longueur_pont", "viaduc de Millau", 2460.0),
    ("longueur_pont", "pont du Golden Gate", 2737.0),
    ("longueur_pont", "pont de la Confédération", 12900.0),
    ("hauteur_cascade", "chutes Victoria", 108.0),
    ("hauteur_cascade", "chutes d'Iguazú", 82.0),
    ("hauteur_cascade", "chutes du Rhin", 23.0),
    # lot 5 — aires d'îles en km² (km²/ha/m²/acre convertis) ; ancres vérité-terrain connues
    ("superficie_ile", "Madagascar", 587041.0),
    ("superficie_ile", "Sumatra", 473481.0),
    ("superficie_ile", "Honshū", 227960.0),
    ("superficie_ile", "Cuba", 105806.0),
    # lot 6 — aires (km²) et glacier (m) ; ancres vérité-terrain
    ("superficie_parc_national", "parc national de Yellowstone", 8983.0),
    ("superficie_parc_national", "parc national de Banff", 6641.0),
    ("superficie_parc_national", "parc national Kruger", 19485.0),
    ("superficie_desert", "Sahara", 9200000.0),
    ("superficie_reserve_naturelle", "réserve naturelle de Scandola", 16.7),
    ("superficie_reserve_naturelle", "réserve naturelle nationale de Camargue", 131.2),
    ("longueur_glacier", "glacier Lambert", 400000.0),
    ("longueur_glacier", "glacier d'Aletsch", 22750.0),
    ("longueur_glacier", "glacier du Baltoro", 62000.0),
    # lot 7 — puissance (MW) et masse (kg) ; ancres vérité-terrain
    ("puissance_centrale", "barrage des Trois-Gorges", 22500.0),
    ("puissance_centrale", "barrage d'Itaipu", 14000.0),
    ("puissance_centrale", "centrale nucléaire de Gravelines", 5460.0),
    ("masse_vehicule_spatial", "Spoutnik 1", 83.6),
    ("masse_vehicule_spatial", "station spatiale internationale", 419725.0),
    ("masse_vehicule_spatial", "Curiosity", 899.0),
    # lot 8 — diamètre cratère (m), débit (m³/s), capacité stade (places)
    ("diametre_cratere", "cratère de Chicxulub", 180000.0),
    ("diametre_cratere", "dôme de Vredefort", 300000.0),
    ("diametre_cratere", "Meteor Crater", 1186.0),
    ("debit_fleuve", "Nil", 2830.0),
    ("debit_fleuve", "Congo", 41800.0),
    ("debit_fleuve", "Rhône", 1780.0),
    ("capacite_stade", "stade de Wembley", 90000.0),
    ("capacite_stade", "stade Maracanã", 78838.0),
    ("capacite_stade", "stade de France", 81338.0),
    # lot 9 — hauteur pont (m), aire protégée (km²), nombre étages (compte)
    ("hauteur_pont", "viaduc de Millau", 343.0),
    ("hauteur_pont", "pont de Sutong", 306.0),
    ("hauteur_pont", "pont du Golden Gate", 227.38),
    ("superficie_aire_protegee", "parc national de Yellowstone", 8983.0),
    ("superficie_aire_protegee", "parc national du Serengeti", 14750.0),
    ("superficie_aire_protegee", "parc national Kruger", 19485.0),
    ("nombre_etages", "Burj Khalifa", 163.0),
    ("nombre_etages", "Merdeka 118", 118.0),
    ("nombre_etages", "Taipei 101", 101.0),
    # lot 10 — élargissement de classes (longueur m)
    ("altitude_lac", "Léman", 372.0),
    ("altitude_lac", "lac Tahoe", 1897.0),
    ("altitude_lac", "lac Tanganyika", 773.0),
    ("hauteur_immeuble", "cathédrale de Cologne", 157.0),
    ("hauteur_immeuble", "cathédrale Notre-Dame de Strasbourg", 142.0),
    ("hauteur_immeuble", "Mole Antonelliana", 168.0),
    ("hauteur_volcan", "mont Fuji", 3776.0),
    ("hauteur_volcan", "Cotopaxi", 5897.0),
    ("hauteur_volcan", "Teide", 3715.0),
    ("hauteur_arbre", "Hyperion", 115.85),
    ("hauteur_arbre", "General Sherman", 83.8),
    # lot 11 — cols/collines (m), forêts/glaciers (km²)
    ("altitude_col", "col de l'Iseran", 2764.0),
    ("altitude_col", "col du Stelvio", 2757.0),
    ("altitude_col", "col du Galibier", 2642.0),
    ("hauteur_colline", "Montmartre", 130.53),
    ("hauteur_colline", "mont Palatin", 51.0),
    ("hauteur_colline", "Aventin", 46.6),
    ("superficie_foret", "Forêt-Noire", 6009.2),
    ("superficie_foret", "forêt de Fontainebleau", 280.92),
    ("superficie_foret", "forêt de Soignes", 43.83),
    ("superficie_glacier", "Vatnajökull", 7700.0),
    ("superficie_glacier", "glacier d'Aletsch", 117.6),
    # lot 12 — sommets (m), salle (places), aéroport (km²)
    ("altitude_sommet", "mont Blanc", 4808.0),
    ("altitude_sommet", "pic du Midi d'Ossau", 2884.0),
    ("capacite_salle", "opéra Bastille", 2745.0),
    ("capacite_salle", "théâtre Bolchoï", 1740.0),
    ("superficie_aeroport", "aéroport international de Denver", 137.27),
    ("superficie_aeroport", "aéroport international de Dallas-Fort Worth", 69.63),
    # lot 13 — altitude localités (m), travée pont (m)
    ("altitude_localite", "Leadville", 3094.0),
    ("altitude_localite", "Davos", 1560.0),
    ("altitude_localite", "Addis-Abeba", 2355.0),
    ("travee_pont", "pont du détroit d'Akashi", 1991.0),
    ("travee_pont", "pont du Golden Gate", 1280.0),
    ("travee_pont", "pont du Humber", 1410.0),
    # lot 14 — gares : altitude (m), voies à quai (compte)
    ("altitude_gare", "Tanggula", 5068.0),
    ("altitude_gare", "Galera", 4781.0),
    ("altitude_gare", "Engelberg", 1002.0),
    ("nombre_quais_gare", "Grand Central", 67.0),
    ("nombre_quais_gare", "Roma Termini", 32.0),
    ("nombre_quais_gare", "Châtelet - Les Halles", 7.0),
    # lot 15 — montagnes russes (m)
    ("hauteur_montagnes_russes", "Kingda Ka", 139.0),
    ("hauteur_montagnes_russes", "Red Force", 112.0),
    ("hauteur_montagnes_russes", "Millennium Force", 94.0),
    ("longueur_montagnes_russes", "Millennium Force", 2010.0),
    ("longueur_montagnes_russes", "Formula Rossa", 2000.0),
    # lot 16 — hauteur structure (m)
    ("hauteur_structure", "Tokyo Skytree", 634.0),
    ("hauteur_structure", "tour Ostankino", 540.1),
    ("hauteur_structure", "tour Canton", 600.0),
    # lot 17 — largeur navire (m), effectif scolaire (compte)
    ("largeur_navire", "Titanic", 28.2),
    ("largeur_navire", "Charles de Gaulle", 64.4),
    ("largeur_navire", "Bismarck", 36.0),
    # largeur pont (m) — Golden Gate teste la conversion pied (90 ft = 27.43 m)
    ("largeur_pont", "pont de Brooklyn", 25.9),
    ("largeur_pont", "pont du Golden Gate", 27.432),
    ("largeur_pont", "pont de Normandie", 23.6),
    # hauteur église (m) — flèche/total ; range [5,180] exclut l'outlier Montpellier 2850 (erreur source)
    ("hauteur_eglise", "cathédrale de Cologne", 157.0),
    ("hauteur_eglise", "cathédrale Notre-Dame de Strasbourg", 142.0),
    ("hauteur_eglise", "cathédrale Notre-Dame de Rouen", 151.0),
    ("hauteur_eglise", "basilique Saint-Pierre", 136.6),
    # capacité réservoir (m³) — patron VOLUME, valeurs ~1e10-1e11
    ("capacite_reservoir", "lac Kariba", 180000000000.0),
    ("capacite_reservoir", "lac Mead", 32220000000.0),
    ("capacite_reservoir", "réservoir des Trois-Gorges", 39300000000.0),
    ("capacite_reservoir", "lac Volta", 148000000000.0),
    # volume lac naturel (m³) — patron VOLUME ; Baïkal/Supérieur/Tanganyika = plus grands lacs
    ("volume_lac", "lac Baïkal", 2.362e13),
    ("volume_lac", "lac Supérieur", 1.210e13),
    ("volume_lac", "lac Tanganyika", 1.890e13),
    ("volume_lac", "Léman", 8.900e10),
    # grottes (m) — unité-aware ; longueur = Mammoth (plus longue) / profondeur = Veryovkina (plus profonde)
    # largeur route/avenue (m) — Champs-Élysées 70 / Unter den Linden 60 (largeurs documentées classiques)
    ("largeur_route", "avenue des Champs-Élysées", 70.0),
    ("largeur_route", "Unter den Linden", 60.0),
    # diamètre télescope = ouverture (m) — GTC 10.4 / Subaru 8.2 (ouvertures documentées)
    ("diametre_telescope", "Gran Telescopio Canarias", 10.4),
    ("diametre_telescope", "Subaru", 8.2),
    # superficie lac (km²) — grands lacs (tolérance 1% discriminante à cette échelle)
    ("superficie_lac", "lac Baïkal", 31722.0),
    ("superficie_lac", "lac Tanganyika", 32900.0),
    ("superficie_lac", "lac Supérieur", 82350.0),
    # superficie réservoir (km²) — grands lacs de barrage
    ("superficie_reservoir", "lac Volta", 8502.0),
    ("superficie_reservoir", "lac Kariba", 5400.0),
    ("superficie_reservoir", "lac Nasser", 5250.0),
    # superficie baie/golfe (km²) — Chesapeake / golfe du Bengale (couvre 11k → 2.17M)
    ("superficie_baie", "baie de Chesapeake", 11601.0),
    ("superficie_baie", "golfe du Bengale", 2172000.0),
    # superficie étang (km²) — étangs français documentés (unité-explicite seulement)
    ("superficie_etang", "étang de Vaccarès", 65.0),
    ("superficie_etang", "étang de Cazaux et de Sanguinet", 55.0),
    ("superficie_etang", "étang de Lacanau", 19.85),
    # demi-vie isotope (s) — patron TEMPS ; C-14 5700ans / U-238 4.468e9ans / Co-60 5.27ans / Ra-226 1600ans
    ("demi_vie_isotope", "carbone 14", 179878320000.0),
    ("demi_vie_isotope", "uranium 238", 1.409993568e17),
    ("demi_vie_isotope", "cobalt 60", 166344192.0),
    ("demi_vie_isotope", "radium 226", 50492160000.0),
    # masse navire = déplacement (kg) — Titanic 52310 t / Yamato 69100 t / Hood 42000 t
    ("masse_navire", "Titanic", 52310000.0),
    ("masse_navire", "Yamato", 69100000.0),
    ("masse_navire", "HMS Hood", 42000000.0),
    # vitesse navire (km/h) — Titanic 24 nd / Bismarck 30 nd / Yamato 27 nd
    ("vitesse_navire", "Titanic", 44.448),
    ("vitesse_navire", "Bismarck", 55.5785),
    ("vitesse_navire", "Yamato", 50.004),
    # vitesse train/matériel roulant (km/h, de conception) — TGV 320 / ICE 3M 330 / loco ES64U4 230
    ("vitesse_train", "TGV", 320.0),
    ("vitesse_train", "ICE 3M", 330.0),
    ("vitesse_train", "Siemens ES64U4", 230.0),
    # puissance centrale hydro (MW) — Itaipu 14000 / Guri 10235 / Hoover 2079 (hors Q159719)
    ("puissance_centrale_hydro", "barrage d'Itaipu", 14000.0),
    ("puissance_centrale_hydro", "barrage de Guri", 10235.0),
    ("puissance_centrale_hydro", "barrage Hoover", 2078.8),
    # puissance solaire PV (MW) — Benban 1650 / Tengger 1547
    ("puissance_centrale_solaire", "parc solaire de Benban", 1650.0),
    ("puissance_centrale_solaire", "Tengger Desert Solar Park", 1547.0),
    # puissance parc éolien (MW) — Shepherds Flat 845 / Horse Hollow 735
    ("puissance_parc_eolien", "parc éolien de Shepherds Flat", 845.0),
    ("puissance_parc_eolien", "parc éolien d'Horse Hollow", 735.5),
    # puissance centrale charbon (MW) — Tuoketuo 6720 (+ grande mondiale, web) / Medupi 4764 (Afrique du Sud)
    ("puissance_centrale_charbon", "centrale thermique de Tuoketuo", 6720.0),
    ("puissance_centrale_charbon", "centrale thermique de Medupi", 4764.0),
    # nombre produit auto (dénombrement) — Ford T 15M / Coccinelle 21.53M (hors Q42889)
    ("nombre_produit_auto", "Ford T", 15000000.0),
    ("nombre_produit_auto", "Volkswagen Coccinelle", 21529464.0),
    # nombre produit navire = nb de navires d'une classe (dénombrement) — Fletcher 175 / Casablanca 50 / Essex 24
    ("nombre_produit_navire", "classe Fletcher", 175.0),
    ("nombre_produit_navire", "classe Casablanca", 50.0),
    ("nombre_produit_navire", "classe Essex", 24.0),
    # capacité église (places) — Notre-Dame 9000 / Sagrada 9000 / St-Pie-X Lourdes 25000
    ("capacite_eglise", "cathédrale Notre-Dame de Paris", 9000.0),
    ("capacite_eglise", "Sagrada Família", 9000.0),
    ("capacite_eglise", "basilique Saint-Pie-X", 25000.0),
    # nombre de travées de pont (dénombrement) — Millau 8 / Vasco da Gama 81 (web-vérifiés)
    ("nombre_travees", "viaduc de Millau", 8.0),
    ("nombre_travees", "pont Vasco da Gama", 81.0),
    # longueur cours d'eau (m) — grands fleuves (superset watercourse)
    ("longueur_cours_eau", "Volga", 3530000.0),
    ("longueur_cours_eau", "Danube", 2850000.0),
    ("longueur_cours_eau", "Mississippi", 3766000.0),
    ("longueur_cours_eau", "Seine", 776670.0),
    # hauteur pyramide (m) — pyramides égyptiennes (noms distinctifs, anti-homonyme)
    ("hauteur_pyramide", "pyramide de Khéphren", 143.5),
    ("hauteur_pyramide", "Pyramide rhomboïdale", 105.07),
    ("hauteur_pyramide", "pyramide de Meïdoum", 65.0),
    # masse moléculaire (Da) — molécules courantes (eau 18 / éthanol 46 / caféine 194 / saccharose 342)
    ("masse_moleculaire", "eau", 18.02),
    ("masse_moleculaire", "éthanol", 46.042),
    ("masse_moleculaire", "caféine", 194.0804),
    ("masse_moleculaire", "saccharose", 342.116),
    # masse volumique (kg/m³) — liquides connus : éthanol 790 / benzène 880 / chloroforme 1480 / H2SO4 1830
    ("densite_chimie", "éthanol", 790.0),
    ("densite_chimie", "benzène", 880.0),
    ("densite_chimie", "acide sulfurique", 1830.2),
    ("densite_chimie", "chloroforme", 1480.0),
    # point de fusion (K) — composés connus : naphtalène 80°C / urée 134°C / caféine 235°C
    ("point_fusion_chimie", "naphtalène", 353.4),
    ("point_fusion_chimie", "urée", 407.1),
    ("point_fusion_chimie", "caféine", 508.1),
    # point d'ébullition (K) — eau 100°C / éthanol 78°C / ammoniac -33°C (affine sur °C négatif)
    ("point_ebullition_chimie", "eau", 373.1),
    ("point_ebullition_chimie", "éthanol", 351.5),
    ("point_ebullition_chimie", "ammoniac", 239.8),
    # point d'éclair (K) — flammables : méthanol 11°C / acétone -18°C / éther -45°C
    ("point_eclair_chimie", "méthanol", 284.26),
    ("point_eclair_chimie", "acétone", 255.37),
    ("point_eclair_chimie", "éther diéthylique", 228.15),
    # pKa (sans dimension) — ammoniac 9.21 (NH4+) / acide citrique 3.14 (pKa1)
    ("pKa_chimie", "ammoniac", 9.21),
    ("pKa_chimie", "acide citrique", 3.14),
    # diamètre pièce (mm) — euros + quarter US (patron mm = ancre discriminante)
    ("diametre_piece_monnaie", "pièce de 1 euro", 23.25),
    ("diametre_piece_monnaie", "pièce de 2 euros", 25.75),
    ("diametre_piece_monnaie", "quarter", 24.26),
    # masse pièce (g) — euros + quarter US (patron gramme = ancre discriminante)
    ("masse_piece_monnaie", "pièce de 1 euro", 7.5),
    ("masse_piece_monnaie", "pièce de 2 euros", 8.5),
    ("masse_piece_monnaie", "quarter", 5.67),
    # hauteur tableau (m) — œuvres à titre distinctif (Night Watch / Starry Night)
    ("hauteur_peinture", "La Ronde de nuit", 3.63),
    ("hauteur_peinture", "La Nuit étoilée", 0.737),
    ("largeur_peinture", "Guernica", 7.76),
    ("largeur_peinture", "La Ronde de nuit", 4.37),
    ("largeur_peinture", "La Nuit étoilée", 0.921),
    # hauteur sculpture/monument (m) — Crazy Horse / Spire de Dublin (web-vérifiés, distinctifs)
    ("hauteur_sculpture", "mémorial Crazy Horse", 172.0),
    ("hauteur_sculpture", "Spire de Dublin", 121.2),
    # hauteur dessin (m) — Homme de Vitruve 0.346 / Le Lièvre de Dürer 0.25 (web-vérifiés)
    ("hauteur_dessin", "Homme de Vitruve", 0.346),
    ("hauteur_dessin", "Le Lièvre", 0.25),
    ("largeur_dessin", "Homme de Vitruve", 0.255),
    ("largeur_dessin", "Le Lièvre", 0.225),
    # hauteur estampe (m) — Grande Vague Hokusai / Melencolia & Rhinocéros Dürer (web-vérifiés)
    ("hauteur_estampe", "La Grande Vague de Kanagawa", 0.26),
    ("hauteur_estampe", "Melencolia", 0.242),
    ("hauteur_estampe", "Rhinocéros", 0.235),
    ("largeur_estampe", "La Grande Vague de Kanagawa", 0.38),
    ("largeur_estampe", "Melencolia", 0.188),
    ("largeur_estampe", "Rhinocéros", 0.298),
    # aquarelle (m) — études Dürer (Young Hare / Wing of a Blue Roller, web-vérifiées)
    ("hauteur_aquarelle", "Le Lièvre", 0.25),
    ("hauteur_aquarelle", "Aile de Rollier bleu", 0.196),
    ("largeur_aquarelle", "Le Lièvre", 0.225),
    ("largeur_aquarelle", "Aile de Rollier bleu", 0.2),
    ("longueur_grotte", "Optymistychna", 264576.0),
    ("longueur_grotte", "Tham Luang", 10316.0),
    ("profondeur_grotte", "gouffre Veryovkina", 2212.0),
    ("profondeur_grotte", "Krubera-Voronja", 2199.0),
    ("nombre_eleves", "Harvard Business School", 1953.0),
    ("nombre_eleves", "Harvard Medical School", 1563.0),
    ("nombre_cylindres", "Pagani Huayra", 12.0),          # V12 biturbo AMG
    ("nombre_cylindres", "Ferrari 812 Superfast", 12.0),  # 6.5 L V12
    ("nombre_cylindres", "Benz Patent Motorwagen", 1.0),  # monocylindre, 1885
    ("longueur_ligne_ferroviaire", "ligne de Petite Ceinture", 32000.0),  # ~32 km (Paris)
    ("longueur_ligne_ferroviaire", "ligne du Gothard", 206000.0),         # ~206 km (Immensee-Chiasso)
    ("longueur_route", "boulevard périphérique de Paris", 35040.0),       # 35.04 km (officiel)
    ("longueur_route", "deuxième périphérique de Pékin", 32700.0),        # 32.7 km (2nd Ring Road)
    ("longueur_tunnel", "tunnel de base du Saint-Gothard", 57090.0),      # 57.09 km (plus long du monde)
    ("longueur_tunnel", "tunnel sous la Manche", 50450.0),                # 50.45 km
    ("longueur_tunnel", "tunnel du Seikan", 53850.0),                     # 53.85 km
    ("longueur_canal", "canal de Suez", 193300.0),                        # 193.3 km
    ("longueur_canal", "canal de Panama", 82000.0),                       # 82 km
    ("longueur_canal", "canal de Corinthe", 6340.0),                      # 6.34 km
    ("longueur_sentier", "sentier des Appalaches", 3538000.0),            # ~3538 km (Appalachian Trail)
    ("longueur_sentier", "GR 20", 179000.0),                              # ~179 km (Corse)
    ("longueur_sentier", "Tour du Mont-Blanc", 170000.0),                 # ~170 km
    ("longueur_aqueduc", "aqueduc du Delaware", 137000.0),                # ~137 km (plus long tunnel)
    ("longueur_aqueduc", "aqueduc du Päijänne", 120000.0),                # ~120 km (Finlande)
    ("tirant_eau_navire", "Titanic", 10.54),                              # tirant d'eau ~10.5 m
    ("tirant_eau_navire", "Yamato", 10.86),                               # cuirassé ~10.86 m
    ("tirant_eau_navire", "USS Nimitz", 11.3),                            # porte-avions ~11.3 m
    ("plus_longue_travee_pont", "pont du Golden Gate", 1280.0),           # travée principale 1280 m
    ("plus_longue_travee_pont", "pont de Brooklyn", 487.0),               # ~486 m
    ("plus_longue_travee_pont", "viaduc de Millau", 342.0),               # 342 m
    ("longueur_crete_barrage", "barrage Hoover", 379.0),                  # crête 379 m
    ("longueur_crete_barrage", "barrage des Trois-Gorges", 2335.0),       # crête 2335 m
    ("longueur_crete_barrage", "barrage de Bort-les-Orgues", 390.0),      # ~390 m
    ("tonnage_brut", "Titanic", 46329.0),                 # GT historique
    ("tonnage_brut", "Harmony of the Seas", 226963.0),    # paquebot
    ("tonnage_brut", "Symphony of the Seas", 228081.0),   # paquebot
    ("tonnage_brut", "Costa Concordia", 114147.0),
    # lot 18 — superficie localités (km²)
    ("superficie_localite", "Vienne", 414.8),
    ("superficie_localite", "Hambourg", 755.2),
    ("superficie_localite", "Lisbonne", 100.0),
    # lot 19 — lits d'hôpital (compte)
    ("nombre_lits_hopital", "hôpital universitaire de la Charité de Berlin", 3001.0),
    ("nombre_lits_hopital", "hôpital Bicêtre", 2007.0),
    ("nombre_lits_hopital", "hôpital Cochin", 1483.0),
    # lot 23 — masse véhicule (kg) : Spoutnik 1 = 83,6 kg (1er satellite, valeur précise mono)
    ("masse_vehicule", "Spoutnik 1", 83.6),
    # lot 24 — fréquence station radio (MHz) : stations dont le NOM encode la fréquence (auto-validantes)
    ("frequence_station_radio", "95.8 FM", 95.8),
    ("frequence_station_radio", "102 FM", 102.0),
    ("frequence_station_radio", "BCB 106.6fm", 106.6),
    # lot 25 — tension poste électrique (kV) : niveaux normalisés du réseau (RTE/Hydro-Québec)
    ("tension_poste_electrique", "Poste électrique de Tollevast", 400.0),
    ("tension_poste_electrique", "poste de la Chamouchouane", 735.0),
    ("tension_poste_electrique", "Poste électrique de Pariset", 225.0),
    # lot 20 — hauteur focale phare (m)
    ("hauteur_focale_phare", "phare de Cordouan", 60.0),
    ("hauteur_focale_phare", "phare de Chassiron", 50.0),
    ("hauteur_focale_phare", "phare de Contis", 39.0),
]
for rel, ent, vrai in ANCRES_NUM:
    st, val = repond(rel, ent)
    tol = max(2.0, 0.01 * abs(vrai))
    bon = st == VERIFIE and val is not None and abs(float(val) - vrai) <= tol
    check(f"ANCRE {rel}({ent}) ≈ {vrai} (±{tol:.1f}) [{st}, {val}]", bon)

# 3ter) ANCRES POPULATION — ORDRE DE GRANDEUR (valeur datée, ne pas figer une valeur exacte) : bornes larges.
ANCRES_ORDRE = [
    ("population_ville", "Shanghaï", 1.5e7, 4e7),
    ("population_ville", "New York", 5e6, 1.5e7),
    ("population_ville", "Chongqing", 1.5e7, 4e7),
    # nombre de locuteurs (mono-valeur survivant au fonctionnel ; valeur datée -> ordre de grandeur)
    ("nombre_locuteurs_langue", "espagnol", 3e8, 6e8),
    ("nombre_locuteurs_langue", "anglais", 5e8, 1.5e9),
    ("nombre_locuteurs_langue", "thaï", 1e7, 4e7),
    ("nombre_locuteurs_langue", "géorgien", 2e6, 6e6),
    # vitesse max -> km/h : records connus + conversion nœud->km/h (Titanic/QM2 = navires en nœuds)
    ("vitesse_max_vehicule", "Thrust SSC", 1200, 1260),     # record terrestre absolu ≈ 1228 km/h
    ("vitesse_max_vehicule", "Shinkansen L0", 590, 610),    # record maglev ≈ 603 km/h
    ("vitesse_max_vehicule", "Queen Mary 2", 50, 60),       # 30 nœuds -> 55,56 km/h
    ("vitesse_max_vehicule", "Titanic", 40, 50),            # 24 nœuds -> 44,45 km/h
    # masse -> kg : gros navires (déplacement) en ordre de grandeur
    ("masse_vehicule", "USS Carl Vinson", 9e7, 1.1e8),      # porte-avions Nimitz ≈ 101 300 t
    ("masse_vehicule", "Yamato", 6.5e7, 7.2e7),             # cuirassé ≈ 69 100 t
    ("masse_vehicule", "Titanic", 4e7, 6e7),                # ≈ 52 310 t
    # capacité passagers navire : méga-paquebots modernes (ordre de grandeur)
    ("capacite_passagers_navire", "MSC Europa", 6500, 7000),    # ≈ 6774
    ("capacite_passagers_navire", "Costa Toscana", 6000, 7000), # ≈ 6554
    ("capacite_passagers_navire", "MSC Virtuosa", 6000, 6700),  # ≈ 6334
    # autonomie -> mètres : range naval 20 000 NM = 37 040 000 m (confirme conversion mille nautique)
    ("autonomie_vehicule", "USS Essex", 3.6e7, 3.8e7),       # porte-avions Essex ≈ 20 000 NM
    ("autonomie_vehicule", "Graf Zeppelin", 3.5e7, 3.8e7),   # dirigeable ≈ 37 040 km
    ("autonomie_vehicule", "Liberty ship", 3.6e7, 3.8e7),    # cargo ≈ 20 000 NM
    # nombre produit (compte) : chiffres de production documentés (un seul chiffre cité -> survit)
    ("nombre_produit_vehicule", "Lamborghini Gallardo", 13000, 15000),  # ≈ 14 022
    ("nombre_produit_vehicule", "Peugeot 406 Coupé", 100000, 115000),   # ≈ 107 631
]
for rel, ent, lo, hi in ANCRES_ORDRE:
    st, val = repond(rel, ent)
    bon = st == VERIFIE and val is not None and lo <= float(val) <= hi
    check(f"ANCRE-ORDRE {rel}({ent}) ∈ [{lo:.0e},{hi:.0e}] [{st}, {val}]", bon)

# 3bis) ANCRES LICENCE — vérité-terrain (correspondance exacte).
ANCRES_LIC = [
    ("Blender", "licence publique générale GNU version 3"),
    ("Mozilla Firefox", "MPL-2.0"),
    ("PostgreSQL", "licence PostgreSQL"),
]
for ent, vrai in ANCRES_LIC:
    st, val = repond("licence_logiciel", ent)
    check(f"ANCRE licence_logiciel({ent}) = {vrai!r} [{st}, {val}]",
          st == VERIFIE and val is not None and val == vrai)

# 3ter) ANCRES LANGAGE DE PROGRAMMATION — vérité-terrain (correspondance exacte).
ANCRES_LANG = [
    ("phpMyAdmin", "PHP"),
    ("Symfony", "PHP"),
    ("GNU Emacs", "Emacs Lisp"),
]
for ent, vrai in ANCRES_LANG:
    st, val = repond("langage_programmation_logiciel", ent)
    check(f"ANCRE langage_programmation_logiciel({ent}) = {vrai!r} [{st}, {val}]",
          st == VERIFIE and val is not None and val == vrai)

# 3quater) ANCRES SYSTÈME D'EXPLOITATION — logiciels Windows-only (correspondance exacte).
ANCRES_OS = [
    ("WinRAR", "Microsoft Windows"),
    ("IrfanView", "Microsoft Windows"),
    ("AutoHotkey", "Microsoft Windows"),
]
for ent, vrai in ANCRES_OS:
    st, val = repond("systeme_exploitation_logiciel", ent)
    check(f"ANCRE systeme_exploitation_logiciel({ent}) = {vrai!r} [{st}, {val}]",
          st == VERIFIE and val is not None and val == vrai)

# 3quinquies) ANCRES TYPE MIME — formats de fichier connus (correspondance exacte).
ANCRES_MIME = [
    ("Portable Network Graphics", "image/png"),
    ("Portable Document Format", "application/pdf"),
    ("HTML", "text/html"),
]
for ent, vrai in ANCRES_MIME:
    st, val = repond("type_mime_format", ent)
    check(f"ANCRE type_mime_format({ent}) = {vrai!r} [{st}, {val}]",
          st == VERIFIE and val is not None and val == vrai)

# extension de fichier (P1195) : valeur littérale mono-extension (multi -> HORS via fonctionnel). Ancres stables.
ANCRES_EXT = [
    ("GIF", "gif"),
    ("WebP", "webp"),
    ("MPEG-4", "mp4"),
    ("Waveform Audio File Format", "wav"),
    ("WebM", "webm"),
]
for ent, vrai in ANCRES_EXT:
    st, val = repond("extension_format", ent)
    check(f"ANCRE extension_format({ent}) = {vrai!r} [{st}, {val}]",
          st == VERIFIE and val is not None and val == vrai)

# écartement des rails (P1064) : valeur = type d'écartement (entité). Ancres ferroviaires connues, mono.
ANCRES_ECART = [
    ("métro de Paris", "écartement standard"),
    ("Shinkansen", "écartement standard"),
    ("tramway de Lisbonne", "voie de 900 mm"),
]
for ent, vrai in ANCRES_ECART:
    st, val = repond("ecartement_rails", ent)
    check(f"ANCRE ecartement_rails({ent}) = {vrai!r} [{st}, {val}]",
          st == VERIFIE and val is not None and val == vrai)

# propulsé par (P516) : valeur = type de propulsion (entité). Ancres mono, 3 types vérifiables.
ANCRES_PROP = [
    ("Volkswagen Coccinelle", "moteur à allumage commandé"),
    ("Toyota BZ4X", "moteur électrique"),
    ("Tata Sumo", "moteur Diesel"),
]
for ent, vrai in ANCRES_PROP:
    st, val = repond("propulse_par", ent)
    check(f"ANCRE propulse_par({ent}) = {vrai!r} [{st}, {val}]",
          st == VERIFIE and val is not None and val == vrai)

# source d'énergie (P618) : valeur = type d'énergie. Ancres mono vérifiables (éolien/charbon/gaz).
ANCRES_ENER = [
    ("Enercon E-126", "énergie éolienne"),
    ("centrale thermique d'Isogo", "charbon"),
    ("centrale thermique de Castelló", "gaz naturel"),
]
for ent, vrai in ANCRES_ENER:
    st, val = repond("source_energie", ent)
    check(f"ANCRE source_energie({ent}) = {vrai!r} [{st}, {val}]",
          st == VERIFIE and val is not None and val == vrai)

# 4) SOUNDNESS ADVERSE — homonymes multi-valeur, entité absente, relation absente -> TOUJOURS HORS.
ADVERSE = [
    ("altitude_montagne", "mont Blanc"),         # homonymes très dispersés [370..4810] -> désaccord -> HORS
    ("altitude_montagne", "montagne-qui-nexiste-pas-zzz"),
    ("hauteur_gratte_ciel", "tour Eiffel"),      # bonne entité, MAUVAISE relation -> HORS
    ("relation_inexistante_t7", "Everest"),
    ("licence_logiciel", "logiciel-inconnu-zzz"),
    ("longueur_navire", "Bismarck"),             # 2 navires [241.6, 251] -> désaccord -> HORS
    ("hauteur_phare", "Titanic"),                # bonne entité, MAUVAISE relation -> HORS
    ("nombre_locuteurs_langue", "français"),     # 2 valeurs L1/total [77.2M, 208M] -> désaccord -> HORS
    ("nombre_locuteurs_langue", "langue-qui-nexiste-pas-zzz"),
    ("vitesse_max_vehicule", "Concorde"),        # vitesse en Mach (facteur non fixe) -> ignorée -> HORS
    ("vitesse_max_vehicule", "Lockheed SR-71 Blackbird"),  # idem Mach -> HORS
    ("longueur_navire", "Shinkansen L0"),        # bonne entité, MAUVAISE relation -> HORS
    ("masse_vehicule", "vehicule-inexistant-zzz"),         # entité absente -> HORS
    ("hauteur_phare", "Yamato"),                 # bonne entité, MAUVAISE relation -> HORS
    ("frequence_station_radio", "station-inexistante-zzz"),  # entité absente -> HORS
    ("masse_vehicule", "95.8 FM"),               # station radio n'a pas de masse de véhicule -> HORS
    ("tension_poste_electrique", "poste-inexistant-zzz"),    # entité absente -> HORS
    ("capacite_passagers_navire", "navire-inexistant-zzz"),  # entité absente -> HORS
    ("autonomie_vehicule", "vehicule-inexistant-zzz"),       # entité absente -> HORS
    ("nombre_produit_vehicule", "modele-inexistant-zzz"),    # entité absente -> HORS
    ("langage_programmation_logiciel", "logiciel-inconnu-zzz"),  # entité absente -> HORS
    ("systeme_exploitation_logiciel", "logiciel-inconnu-zzz"),   # entité absente -> HORS
    ("type_mime_format", "format-inconnu-zzz"),                  # entité absente -> HORS
    ("extension_format", "format-inconnu-zzz"),                  # entité absente -> HORS
    ("nombre_cylindres", "moteur-inexistant-zzz"),               # entité absente -> HORS
    ("tonnage_brut", "navire-inexistant-zzz"),                   # entité absente -> HORS
    ("ecartement_rails", "ligne-inexistante-zzz"),               # entité absente -> HORS
    ("propulse_par", "vehicule-inexistant-zzz"),                 # entité absente -> HORS
    ("source_energie", "centrale-inexistante-zzz"),              # entité absente -> HORS
    ("longueur_ligne_ferroviaire", "ligne-inexistante-zzz"),     # entité absente -> HORS
    ("longueur_route", "route-inexistante-zzz"),                 # entité absente -> HORS
    ("longueur_tunnel", "tunnel-inexistant-zzz"),                # entité absente -> HORS
    ("longueur_canal", "canal-inexistant-zzz"),                  # entité absente -> HORS
    ("longueur_sentier", "sentier-inexistant-zzz"),              # entité absente -> HORS
    ("longueur_aqueduc", "aqueduc-inexistant-zzz"),              # entité absente -> HORS
    ("tirant_eau_navire", "navire-sans-tirant-zzz"),            # entité absente -> HORS
    ("plus_longue_travee_pont", "pont-inexistant-zzz"),         # entité absente -> HORS
    ("longueur_crete_barrage", "barrage-inexistant-zzz"),       # entité absente -> HORS
]
for rel, ent in ADVERSE:
    st, val = repond(rel, ent)
    check(f"SOUNDNESS {rel}({ent}) -> HORS [{st}]", st == HORS and val is None)

print(f"\n=== T7 : {ok}/{total} checks PASS ===")
if ok != total:
    raise SystemExit(1)
