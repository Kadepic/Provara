"""
VALIDATION T11 — TRANSPORT, VÉHICULES & INFRASTRUCTURE (couloir d'ingestion). FAUX=0 INVIOLABLE.

Charge UNIQUEMENT les relations T11 dans un Lecteur frais (léger) et verrouille :

  1. INTÉGRITÉ : faits présents (n>0) ; toute valeur = libellé non vide ≥2 caractères (constructeur/exploitant =
                 nom propre d'organisation, jamais un Q-ID nu ni un caractère isolé).
  2. ANCRES    : couples vérifiés À LA MAIN, indépendamment de Wikidata (Titanic -> Harland and Wolff, Bismarck ->
                 Blohm & Voss, TGV -> Alstom, métro de Paris -> RATP…) -> ancrage NON circulaire. Couvre les
                 sous-classes (navire/aéronef/auto/train) pour prouver que constructeur_vehicule les capte toutes.
  3. SOUNDNESS : adverse — un VÉHICULE HOMONYME multi-constructeur (Belle Poule, Viking, Deutschland), une entité
                 absente, la mauvaise relation -> TOUJOURS HORS (None). Jamais un faux, jamais une devinette.

EXIT 0 = tous les check passent. Lancer SEUL (1 chargement léger) en dev ; enregistrer dans _nonreg.py pour le gate.
"""
from __future__ import annotations

import json
import os
import re

# ─── GARDE « BASE COMPLÈTE » (2026-07-12) — SKIP propre sur l'échantillon ───
# Gate de classe BASE RÉELLE (72 M). Sur l'échantillon committé (que _nonreg épingle) sa donnée est
# absente et ses ancres tomberaient en FAUX-échec. Marqueur de base réelle : occupation_personne (2,35 M,
# jamais committé). Base réelle vérifiée par la passe manuelle valide_lecteur* (cf. CHANGELOG). Une gate
# honnête SKIPPE quand sa donnée manque, elle ne tombe pas.
import os as _os, sys as _sys
_bc = _os.environ.get("LECTEUR_DATASETS_DIR")
if _bc and not _os.path.exists(_os.path.join(_bc, "occupation_personne.jsonl")):
    print("=== valide_lecteur_t11 : SKIP — base complète requise (occupation_personne absent de ce store) ===")
    _sys.exit(0)
# ──────────────────────────────────────────────────────

from garde_ressources import borne

borne(max_go=2.0, max_cpu_s=900)   # OPTIM amorce-seule : ne charge QUE les relations T11 (~17 k faits) dans un Lecteur
                                   # frais, plus le full-load global des 33,5 M faits ; 2 Go large.

os.environ.setdefault("LECTEUR_AMORCE_SEULE", "1")  # OPTIM gate légère : charge SES relations dans un Lecteur frais (jamais le singleton global L.LECTEUR) → saute charge_dossier()+gele() sur les 33,5 M faits (~5 Go/min)
import lecteur as L
from lecteur import HORS, VERIFIE

DOSSIER = os.environ.get("LECTEUR_DATASETS_DIR") or os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "datasets", "lecteur")
RELATIONS = ["constructeur_vehicule", "exploitant_metro",
             "exploitant_aeroport", "exploitant_chemin_fer", "exploitant_ligne_ferroviaire",
             "exploitant_tunnel", "exploitant_port", "alliance_compagnie_aerienne",
             "exploitant_gare", "constructeur_moteur_avion", "exploitant_funiculaire",
             "exploitant_telepherique", "exploitant_reseau_tramway", "classe_navire",
             "constructeur_lanceur", "exploitant_satellite", "constructeur_materiel_roulant",
             "exploitant_vehicule", "exploitant_phare", "exploitant_ligne_ferry",
             "constructeur_satellite", "numero_imo_navire", "mmsi_navire",
             "code_iata_compagnie", "code_icao_compagnie", "callsign_compagnie"]

# Relations IDENTIFIANT (valeur = code canonique) : validées STRUCTURELLEMENT (forme du code), pas par
# ancres vérité-terrain (un identifiant canonique n'a pas d'homonymie de label ; cf. codes ISO T9 / ICAO T1).
CODES = {"numero_imo_navire": r"\d{7}",     # numéro IMO = exactement 7 chiffres.
         "mmsi_navire": r"\d{9}",           # MMSI = exactement 9 chiffres.
         "code_iata_compagnie": r"[A-Z0-9]{2}",  # code IATA compagnie = 2 alphanumériques.
         "code_icao_compagnie": r"[A-Z]{3}",      # code ICAO compagnie = 3 lettres.
         "callsign_compagnie": r"[A-Z0-9][A-Z0-9 '\-]*"}  # indicatif radio = mot(s) majuscule.

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


def _entete(chemin):
    with open(chemin, encoding="utf-8") as fh:
        for brut in fh:
            brut = brut.strip()
            if brut:
                t = json.loads(brut)
                return t["_categorie"], t["_source"]
    raise ValueError(f"{chemin} : en-tête manquant")


# --- Chargement léger : seules les relations T11 dans un Lecteur frais. ---
lec = L.Lecteur()
manquants = []
for rel in RELATIONS:
    chemin = os.path.join(DOSSIER, rel + ".jsonl")
    if not os.path.exists(chemin):
        manquants.append(rel)
        continue
    cat, src = _entete(chemin)
    lec.charge_jsonl(rel, chemin, cat, src)
check(f"DATASETS présents (aucun manquant : {manquants})", not manquants)

# 1) INTÉGRITÉ : n>0 et toute valeur = libellé non vide ≥2 caractères.
for rel in RELATIONS:
    t = lec.tables.get(rel, {})
    n = len(t)
    mauvais = next((c for c, f in t.items()
                    if not (isinstance(f.valeur, str) and len(f.valeur.strip()) >= 2)), None)
    check(f"{rel} : {n} faits, libellés ≥2 car. non vides [contre-ex: {mauvais}]", n > 0 and mauvais is None)

# 1bis) STRUCTURE des relations IDENTIFIANT : toute valeur conforme au format canonique du code.
for rel, motif in CODES.items():
    t = lec.tables.get(rel, {})
    non_conf = next((f.valeur for f in t.values() if not re.fullmatch(motif, f.valeur)), None)
    check(f"{rel} : {len(t)} codes, tous conformes à /{motif}/ [contre-ex: {non_conf}]",
          len(t) > 0 and non_conf is None)

# 2) ANCRES — vérité-terrain indépendante (correspondance exacte du libellé stocké).
ANCRES = [
    # constructeur_vehicule : couvre NAVIRE / AÉRONEF / AUTO / TRAIN -> prouve la couverture des sous-classes.
    ("constructeur_vehicule", "Titanic", "Harland and Wolff"),               # paquebot
    ("constructeur_vehicule", "Bismarck", "Blohm & Voss"),                   # cuirassé
    ("constructeur_vehicule", "Queen Mary 2", "Chantiers de l'Atlantique"),  # paquebot
    ("constructeur_vehicule", "Airbus A320", "Airbus Commercial Aircraft"),  # avion
    ("constructeur_vehicule", "TGV Rame 4401", "Alstom"),                    # train
    ("constructeur_vehicule", "Triumph Spitfire 1500", "Triumph"),          # automobile
    # exploitant_metro : réseaux -> exploitant.
    ("exploitant_metro", "métro de Paris", "Régie autonome des transports parisiens"),
    ("exploitant_metro", "métro de Lyon", "Transports en commun lyonnais"),
    ("exploitant_metro", "métro de Montréal", "Société de transport de Montréal"),
    ("exploitant_metro", "métro de New York", "New York City Transit Authority"),
    ("exploitant_metro", "Mass Transit Railway", "MTR Corporation"),
    # exploitant_aeroport : aéroport -> organisation exploitante.
    ("exploitant_aeroport", "aéroport de Paris-Orly", "Groupe ADP"),
    ("exploitant_aeroport", "aéroport international de Barcelone-El Prat", "Aena"),
    ("exploitant_aeroport", "aéroport international Franz-Josef-Strauss de Munich", "Flughafen München GmbH"),
    # exploitant_chemin_fer : chemin de fer -> exploitant.
    ("exploitant_chemin_fer", "Brockenbahn", "Harzer Schmalspurbahnen"),
    ("exploitant_chemin_fer", "ligne de la Jungfrau", "Jungfraubahn AG"),
    # exploitant_ligne_ferroviaire : ligne -> exploitant.
    ("exploitant_ligne_ferroviaire", "ligne de Paris à Granville", "SNCF"),
    ("exploitant_ligne_ferroviaire", "ligne de Lyon à Bordeaux", "SNCF"),
    ("exploitant_ligne_ferroviaire", "ligne de Séville à Huelva", "Renfe Operadora"),
    # exploitant_tunnel : tunnel -> gestionnaire (ferroviaire/routier).
    ("exploitant_tunnel", "tunnel sous la Manche", "Getlink"),
    ("exploitant_tunnel", "tunnel du Mont-Blanc", "Autoroutes et tunnel du Mont-Blanc"),
    ("exploitant_tunnel", "tunnel de base du Saint-Gothard", "Chemins de fer fédéraux suisses"),
    ("exploitant_tunnel", "tunnel du Simplon", "Chemins de fer fédéraux suisses"),
    ("exploitant_tunnel", "Holland Tunnel", "Port Authority of New York and New Jersey"),
    # exploitant_port : port -> autorité portuaire / exploitant.
    ("exploitant_port", "port de Rotterdam", "Autorité portuaire de Rotterdam"),
    ("exploitant_port", "port de Hambourg", "Hamburg Port Authority"),
    ("exploitant_port", "port de Barcelone", "Autorité portuaire de Barcelone"),
    ("exploitant_port", "port de Shanghai", "Shanghai International Port Group"),
    ("exploitant_port", "port du Havre", "HAROPA PORT"),
    # alliance_compagnie_aerienne : compagnie -> alliance (closed set Star Alliance/Oneworld/Skyteam…).
    ("alliance_compagnie_aerienne", "Lufthansa", "Star Alliance"),
    ("alliance_compagnie_aerienne", "United Airlines", "Star Alliance"),
    ("alliance_compagnie_aerienne", "Singapore Airlines", "Star Alliance"),
    ("alliance_compagnie_aerienne", "Air France", "Skyteam"),
    ("alliance_compagnie_aerienne", "Delta Air Lines", "Skyteam"),
    ("alliance_compagnie_aerienne", "American Airlines", "Oneworld"),
    ("alliance_compagnie_aerienne", "British Airways", "Oneworld"),
    ("alliance_compagnie_aerienne", "Qatar Airways", "Oneworld"),
    # exploitant_gare : gare -> exploitant ferroviaire / régie transit (couvre rail longue distance ET métro).
    ("exploitant_gare", "Lyon-Part-Dieu", "SNCF"),
    ("exploitant_gare", "Marseille-Saint-Charles", "SNCF"),
    ("exploitant_gare", "Atocha-Cercanías", "Renfe Operadora"),
    ("exploitant_gare", "Bruxelles-Midi", "Société nationale des chemins de fer belges"),
    ("exploitant_gare", "116th Street – Columbia University", "New York City Transit Authority"),
    ("exploitant_gare", "Grand Central Madison", "Metropolitan Transportation Authority"),
    ("exploitant_gare", "Gare de Lyon", "Régie autonome des transports parisiens"),
    # constructeur_moteur_avion : moteur -> motoriste (complète constructeur, distinct du véhicule).
    ("constructeur_moteur_avion", "Pratt & Whitney JT3D-3", "Pratt & Whitney"),
    ("constructeur_moteur_avion", "General Electric GEnx", "GE Aerospace"),
    ("constructeur_moteur_avion", "Aviadvigatel PS-90", "Aviadvigatel"),
    # exploitant_reseau_tramway : réseau -> exploitant.
    ("exploitant_reseau_tramway", "tramway de La Haye", "HTM Personenvervoer NV"),
    ("exploitant_reseau_tramway", "tramway de Lyon", "Transports en commun lyonnais"),
    ("exploitant_reseau_tramway", "tramway de Montpellier", "Transports de l’Agglomération de Montpellier"),
    # exploitant_funiculaire : funiculaire -> exploitant.
    ("exploitant_funiculaire", "funiculaire de Bica", "Carris"),
    ("exploitant_funiculaire", "funiculaire de Glória", "Carris"),
    ("exploitant_funiculaire", "funiculaire de Fourvière", "Transports en commun lyonnais"),
    # exploitant_telepherique : téléphérique -> exploitant.
    ("exploitant_telepherique", "téléphérique de la Flégère", "Compagnie du Mont-Blanc"),
    ("exploitant_telepherique", "Téléphérique de Lognan", "Compagnie du Mont-Blanc"),
    ("exploitant_telepherique", "Ngong Ping 360", "Ngong Ping 360 Limited"),
    # classe_navire : navire -> sa classe de conception (attribut, couvre cuirassés/porte-avions/paquebots).
    ("classe_navire", "Yamato", "classe Yamato"),
    ("classe_navire", "Bismarck", "classe Bismarck"),
    ("classe_navire", "Britannic", "classe Olympic"),
    ("classe_navire", "HMS Belfast", "classe Town"),
    ("classe_navire", "HMS Queen Elizabeth", "classe Queen Elizabeth"),
    ("classe_navire", "HMS Warspite", "classe Queen Elizabeth"),
    # constructeur_lanceur : lanceur spatial -> constructeur (complète la famille constructeur).
    ("constructeur_lanceur", "Delta IV Heavy", "United Launch Alliance"),
    ("constructeur_lanceur", "B1060", "SpaceX"),
    ("constructeur_lanceur", "Falcon 9 booster B1021", "SpaceX"),
    ("constructeur_lanceur", "Saturn INT-21", "Boeing"),
    ("constructeur_lanceur", "McDonnell Douglas DC-X", "McDonnell Douglas"),
    ("constructeur_lanceur", "Maia (fusée)", "MaiaSpace"),
    # exploitant_satellite : satellite -> opérateur (agences + opérateurs commerciaux).
    ("exploitant_satellite", "Sentinel-2A", "Agence spatiale européenne"),
    ("exploitant_satellite", "SMART-1", "Agence spatiale européenne"),
    ("exploitant_satellite", "Galaxy Evolution Explorer", "National Aeronautics and Space Administration"),
    ("exploitant_satellite", "Nilesat 201", "Nilesat"),
    ("exploitant_satellite", "Telstar 14R", "Telesat"),
    ("exploitant_satellite", "Hipparcos", "Agence spatiale européenne"),
    # constructeur_materiel_roulant : classe de train -> constructeur (mono-constructeur ; multi co-fab -> HORS).
    ("constructeur_materiel_roulant", "EMD F3", "Electro-Motive Diesel"),
    ("constructeur_materiel_roulant", "Bombardier Talent 3", "Bombardier"),
    ("constructeur_materiel_roulant", "Shinkansen série 0", "Hitachi"),
    ("constructeur_materiel_roulant", "ALCO RS-1", "American Locomotive Company"),
    ("constructeur_materiel_roulant", "1995 Stock", "Alstom"),
    # exploitant_vehicule : véhicule individuel -> opérateur (marines, compagnies ferroviaires).
    ("exploitant_vehicule", "HMS Victory", "Royal Navy"),
    ("exploitant_vehicule", "USS Constitution", "United States Navy"),
    ("exploitant_vehicule", "USS S-4", "United States Navy"),
    ("exploitant_vehicule", "Bismarck", "Kriegsmarine"),
    ("exploitant_vehicule", "Unterseeboot 96", "Kriegsmarine"),
    ("exploitant_vehicule", "030 TU 13", "SNCF"),
    # exploitant_phare : phare -> autorité maritime (aide à la navigation).
    ("exploitant_phare", "Nab Tower", "Trinity House"),
    ("exploitant_phare", "phare d'Eddystone", "Trinity House"),
    ("exploitant_phare", "phare de Deauville", "Service des phares et balises"),
    ("exploitant_phare", "phare d'Ailsa Craig", "Northern Lighthouse Board"),
    ("exploitant_phare", "phare arrière de Baker Shoal", "United States Coast Guard"),
    ("exploitant_phare", "phare avant de Murray Harbour", "Garde côtière canadienne"),
    # exploitant_ligne_ferry : liaison par ferry -> compagnie de traversiers.
    ("exploitant_ligne_ferry", "Copenhague-Oslo", "DFDS Seaways"),
    ("exploitant_ligne_ferry", "ferry de Staten Island", "New York City Department of Transportation"),
    ("exploitant_ligne_ferry", "Alaska Marine Highway", "département des Transports et de l'Équipement de l'Alaska"),
    ("exploitant_ligne_ferry", "90 Tórshavn - Nólsoy", "Strandfaraskip Landsins"),
    # constructeur_satellite : satellite -> constructeur (mono ; co-fabrication multi -> HORS ; distinct de l'exploitant).
    ("constructeur_satellite", "ENVISAT", "Astrium"),
    ("constructeur_satellite", "Hipparcos", "Matra Marconi Space"),
    ("constructeur_satellite", "Planck", "Alcatel Space"),
    ("constructeur_satellite", "Spoutnik 1", "RKK Energia"),
    ("constructeur_satellite", "Vanguard 1", "Naval Research Laboratory"),
]
for rel, ent, vrai in ANCRES:
    st, f = lec.repond(rel, ent)
    bon = st == VERIFIE and f is not None and f.valeur == vrai
    check(f"ANCRE {rel}({ent}) = {vrai!r} [{st}, {f.valeur if f else None}]", bon)

# 3) SOUNDNESS ADVERSE — homonymes multi-constructeur (rejetés par fonctionnel), entité/relation absente -> HORS.
ADVERSE = [
    ("constructeur_vehicule", "Belle Poule"),     # 3 constructeurs distincts -> HORS
    ("constructeur_vehicule", "Viking"),          # 2 constructeurs distincts -> HORS
    ("constructeur_vehicule", "Deutschland"),     # 8 constructeurs distincts -> HORS
    ("constructeur_vehicule", "vehicule-qui-nexiste-pas-zzz"),
    ("constructeur_vehicule", "métro de Paris"),  # bonne entité d'une AUTRE relation -> HORS
    ("exploitant_metro", "Titanic"),              # navire, pas un métro -> HORS
    ("exploitant_metro", "metro-inconnu-zzz"),
    ("relation_inexistante_t11", "Titanic"),
    # lot 2 : lignes multi-exploitant (2 gestionnaires d'infra distincts) rejetées par fonctionnel -> HORS.
    ("exploitant_ligne_ferroviaire", "ligne de Ljubiana à Zagreb"),   # {HŽ Infrastruktura, SŽ-Infrastruktura}
    ("exploitant_ligne_ferroviaire", "ligne de Pivka à Rijeka"),
    ("exploitant_aeroport", "Titanic"),           # navire -> mauvaise relation -> HORS
    ("exploitant_chemin_fer", "aeroport-inconnu-zzz"),
    # lot 3 : tunnels/ports multi-exploitant réels (2-3 gestionnaires distincts) rejetés par fonctionnel -> HORS.
    ("exploitant_tunnel", "tunnel du Seikan"),     # {Hokkaido Railway, Japan Freight Railway} -> HORS
    ("exploitant_tunnel", "Moffat Tunnel"),        # 3 compagnies distinctes -> HORS
    ("exploitant_port", "base navale de Rota"),    # {Armada espagnole, United States Navy} -> HORS
    ("exploitant_port", "base navale de Mers El-Kébir"),  # {Marine nationale, Marine nationale algérienne} -> HORS
    ("exploitant_tunnel", "port de Rotterdam"),    # bonne entité d'une AUTRE relation -> HORS
    ("exploitant_port", "tunnel sous la Manche"),  # bonne entité d'une AUTRE relation -> HORS
    # lot 4 : compagnies ayant CHANGÉ d'alliance (vérité datée, multi-valeur) rejetées par fonctionnel -> HORS.
    ("alliance_compagnie_aerienne", "US Airways"),        # {Oneworld, Star Alliance} -> HORS
    ("alliance_compagnie_aerienne", "Continental Airlines"),  # {Skyteam, Star Alliance} -> HORS
    ("alliance_compagnie_aerienne", "Titanic"),    # navire -> mauvaise relation -> HORS
    ("exploitant_port", "Lufthansa"),              # compagnie aérienne -> mauvaise relation -> HORS
    # lot 5 : gares multi-exploitant réelles (2-3 compagnies distinctes) rejetées par fonctionnel -> HORS.
    ("exploitant_gare", "Foggia"),                 # {Ferrovie del Gargano, Italo, Trenitalia} -> HORS
    ("exploitant_gare", "Butte"),                  # {Burlington Northern, Northern Pacific, Union Pacific} -> HORS
    ("exploitant_gare", "Titanic"),                # navire -> mauvaise relation -> HORS
    ("exploitant_tunnel", "Lyon-Part-Dieu"),       # gare d'une AUTRE relation -> HORS
    # lot 6 : remontées/tramways multi-exploitant réels rejetés par fonctionnel -> HORS.
    ("exploitant_funiculaire", "Funiculaire da Graça"),   # {Carris, EMEL Lisboa} -> HORS
    ("exploitant_telepherique", "téléphérique du Salève"),  # 4 exploitants distincts -> HORS
    ("exploitant_reseau_tramway", "tramway d'Helsinki"),  # 2 exploitants distincts -> HORS
    ("constructeur_moteur_avion", "Titanic"),      # navire -> mauvaise relation -> HORS
    ("exploitant_telepherique", "tramway de Lyon"),  # tramway d'une AUTRE relation -> HORS
    # lot 7 : navire multi-classe (reclassé) rejeté par fonctionnel -> HORS + cross-relation.
    ("classe_navire", "HMS Kempenfelt"),           # {classe C et D, classe River} -> HORS
    ("classe_navire", "métro de Paris"),           # pas un navire -> mauvaise relation -> HORS
    ("exploitant_gare", "Yamato"),                 # cuirassé -> mauvaise relation -> HORS
    # lot 8 : cross-relation -> HORS (pas de multi : fonctionnel 100%).
    ("constructeur_lanceur", "Titanic"),           # navire -> mauvaise relation -> HORS
    ("constructeur_lanceur", "métro de Paris"),    # métro -> mauvaise relation -> HORS
    ("exploitant_port", "Delta IV Heavy"),         # lanceur -> mauvaise relation -> HORS
    # lot 9 : satellite multi-opérateur réel rejeté par fonctionnel -> HORS + cross-relation.
    ("exploitant_satellite", "SPOT-7"),            # {Airbus DS Geo, Azercosmos} -> HORS
    ("exploitant_satellite", "Titanic"),           # navire -> mauvaise relation -> HORS
    ("exploitant_satellite", "métro de Paris"),    # métro -> mauvaise relation -> HORS
    # lot 10 : classe de train multi-constructeur (co-fabrication) rejetée par fonctionnel -> HORS + cross-relation.
    ("constructeur_materiel_roulant", "Série Tobu 8000"),  # plusieurs constructeurs -> HORS
    ("constructeur_materiel_roulant", "Titanic"),  # navire -> mauvaise relation -> HORS
    ("exploitant_gare", "EMD F3"),                 # locomotive -> mauvaise relation -> HORS
    # lot 11 : véhicule multi-opérateur réel rejeté par fonctionnel -> HORS + cross-relation.
    ("exploitant_vehicule", "PS Waverley"),        # plusieurs opérateurs successifs -> HORS
    ("exploitant_vehicule", "métro de Paris"),     # réseau (infra) -> mauvaise relation -> HORS
    ("exploitant_satellite", "HMS Victory"),       # navire -> mauvaise relation -> HORS
    # lot 12 : phare multi-exploitant réel rejeté par fonctionnel -> HORS + cross-relation.
    ("exploitant_phare", "phare de Plymouth"),     # {MoD UK, Trinity House} -> HORS
    ("exploitant_phare", "Titanic"),               # navire -> mauvaise relation -> HORS
    ("exploitant_vehicule", "Nab Tower"),          # phare (structure) -> mauvaise relation -> HORS
    # lot 13 : liaison ferry multi-exploitant réelle rejetée par fonctionnel -> HORS + cross-relation.
    ("exploitant_ligne_ferry", "Traverse Rivière-du-Loup–Saint-Siméon"),  # {Clarke Inc., STQ} -> HORS
    ("exploitant_ligne_ferry", "Titanic"),         # navire -> mauvaise relation -> HORS
    ("exploitant_phare", "Copenhague-Oslo"),       # ligne de ferry -> mauvaise relation -> HORS
    # lot 14 : satellite multi-constructeur (co-fabrication) rejeté par fonctionnel -> HORS + cross-relation.
    ("constructeur_satellite", "Landsat 8"),       # plusieurs constructeurs -> HORS
    ("constructeur_satellite", "Titanic"),         # navire -> mauvaise relation -> HORS
    ("exploitant_phare", "Hipparcos"),             # satellite -> mauvaise relation -> HORS
    # lot 15 (identifiant) : entité/relation absente -> HORS (pas d'homonymie pour un code canonique).
    ("numero_imo_navire", "métro de Paris"),       # pas un navire -> mauvaise relation -> HORS
    ("numero_imo_navire", "navire-inexistant-zzz"),
    ("classe_navire", "9241061"),                  # un code IMO n'est pas une entité navire -> HORS
    ("mmsi_navire", "métro de Paris"),             # pas un navire -> mauvaise relation -> HORS
    ("mmsi_navire", "navire-inexistant-zzz"),
    ("code_iata_compagnie", "Titanic"),            # navire, pas une compagnie -> HORS
    ("code_iata_compagnie", "compagnie-inexistante-zzz"),
    ("code_icao_compagnie", "Titanic"),            # navire, pas une compagnie -> HORS
    ("code_icao_compagnie", "compagnie-inexistante-zzz"),
    ("callsign_compagnie", "Titanic"),             # navire, pas une compagnie -> HORS
    ("callsign_compagnie", "compagnie-inexistante-zzz"),
]
for rel, ent in ADVERSE:
    st, f = lec.repond(rel, ent)
    check(f"SOUNDNESS {rel}({ent}) -> HORS [{st}]", st == HORS and f is None)

print(f"\n=== T11 : {ok}/{total} checks PASS ===")
if ok != total:
    raise SystemExit(1)
