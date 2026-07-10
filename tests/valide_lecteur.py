"""
VALIDATION du LECTEUR GÉNÉRIQUE DE DONNÉES (`lecteur.py`) — le moteur du borné DATA (chantier #3).

Verrouille les invariants de soundness du contrat lookup-ou-HORS, en ADVERSE (FAUX=0) :

  1. INTÉGRITÉ : chaque entrée ingérée porte une valeur non vide, une catégorie connue, une source.
  2. RÉCUPÉRABILITÉ : toute entrée ingérée se retrouve par `cherche/repond` (clé canonique), même valeur.
  3. ANCRAGE NON-CIRCULAIRE : un échantillon de valeurs vérifiées indépendamment (fer Z=26, or Z=79,
     uranium Z=92, février 28 j, avril 30 j…) + COHÉRENCE séquentielle Z=1..36 -> attrape toute faute
     de transcription dans l'amorce (sinon « ça marche » testerait le code contre lui-même).
  4. SOUNDNESS ADVERSE (le cœur) : large batterie d'INCONNUS (entité absente, relation absente) ->
     JAMAIS un faux : toujours (HORS, None) / None.
  5. INGESTION : conflit (valeur divergente) -> ValueError ; ré-ingestion idempotente -> 0 nouveau, pas
     d'exception ; clé/valeur vide -> ignorée (jamais stockée) ; catégorie/source invalide -> ValueError.
  6. NL : `repond_nl` rend le bon fait pour les tables ingérées ET conserve l'amorce base_faits (repli,
     zéro régression) ; un gabarit reconnu mais entité inconnue ne produit jamais un faux.
  7. COMPOSITION : tables ingérées et amorce base_faits coexistent sans collision (relations distinctes).
"""
from __future__ import annotations

# ─── GARDE « BASE COMPLÈTE » (2026-07-12) — SKIP propre sur l'échantillon ───
# Gate de classe BASE RÉELLE (72 M). Sur l'échantillon committé (que _nonreg épingle) sa donnée est
# absente et ses ancres tomberaient en FAUX-échec. Marqueur de base réelle : occupation_personne (2,35 M,
# jamais committé). Base réelle vérifiée par la passe manuelle valide_lecteur* (cf. CHANGELOG). Une gate
# honnête SKIPPE quand sa donnée manque, elle ne tombe pas.
import os as _os, sys as _sys
_bc = _os.environ.get("LECTEUR_DATASETS_DIR")
if _bc and not _os.path.exists(_os.path.join(_bc, "occupation_personne.jsonl")):
    print("=== valide_lecteur : SKIP — base complète requise (occupation_personne absent de ce store) ===")
    _sys.exit(0)
# ──────────────────────────────────────────────────────

from garde_ressources import borne

import lecteur as L
from lecteur import VERIFIE, HORS
import base_faits as BF

borne(max_go=8.0, max_cpu_s=1800)  # 2026-06-26 : lecteur global a grossi (~1,4 Go jsonl / 539 fichiers, pic RSS ~4 Go
# all-lanes) -> cap 4 Go provoquait un OOM SPURIOUS à l'import (diag flotte T7/T8/T12, pas une donnée fausse). 8 Go AS
# (RAM dispo ~30 Go = sûr) + 1800 s CPU (scan intégral plus long sous contention multi-terminaux). FAUX=0 inchangé.
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


CATS = {BF.CAT_PHYSIQUE, BF.CAT_PASSE, BF.CAT_CONVENTION}

# 1) INTÉGRITÉ : chaque entrée ingérée est complète et bien typée.
# 2) RÉCUPÉRABILITÉ : toute entrée ingérée se retrouve via repond (VERIFIE + même valeur).
# ⚠️ AGRÉGÉ (pas 1 check/print PAR FAIT) : à 6,38 M faits, imprimer 12,76 M lignes bufferisait ~1 Go de stdout
# (capture_output du gate) + créait 12,76 M f-strings -> SIGKILL sous le cap RLIMIT_AS. On parcourt TOUJOURS
# TOUTES les entrées (couverture intégrale), mais on ne rapporte qu'UN check par section + le 1er contre-exemple.
_mauvais_integrite = None
_mauvais_recup = None
for rel, t in L.LECTEUR.tables.items():
    for cle, fait in t.items():
        if _mauvais_integrite is None and not (
                isinstance(fait.valeur, str) and fait.valeur.strip() != ""
                and fait.categorie in CATS
                and isinstance(fait.source, str) and fait.source.strip() != ""):
            _mauvais_integrite = (rel, cle)
        if _mauvais_recup is None:
            # EXEMPTION documentée (FAUX=0 2026-07-08) : les nationalités JOINTES « X et Y » du dataset livré
            # sont en QUARANTAINE au lookup (join tronqué par fréquence de corpus -> faux par omission) —
            # délibérément NON récupérables jusqu'à la ré-ingestion (ingere_celebres joinmax P27 = 1).
            if rel == "nationalite_personne" and " et " in fait.valeur:
                st, f = L.repond(rel, cle)
                if st != HORS:
                    _mauvais_recup = (rel, cle)      # la quarantaine doit TENIR (jamais servi)
            else:
                st, f = L.repond(rel, cle)
                if not (st == VERIFIE and f.valeur == fait.valeur):
                    _mauvais_recup = (rel, cle)
check(f"INTÉGRITÉ : tous les faits complets+typés (catégorie∈CATS, valeur/source non vides) "
      f"[contre-ex: {_mauvais_integrite}]", _mauvais_integrite is None)
check(f"RÉCUPÉRABILITÉ : tout fait ingéré se retrouve via repond (VERIFIE+même valeur) "
      f"[contre-ex: {_mauvais_recup}]", _mauvais_recup is None)

# 3) ANCRAGE NON-CIRCULAIRE — valeurs vérifiées à la main, indépendamment du code.
ANCRES = {
    ("numero_atomique", "hydrogene"): "1", ("numero_atomique", "oxygene"): "8",
    ("numero_atomique", "fer"): "26", ("numero_atomique", "cuivre"): "29",
    ("numero_atomique", "argent"): "47", ("numero_atomique", "or"): "79",
    ("numero_atomique", "mercure"): "80", ("numero_atomique", "plomb"): "82",
    ("numero_atomique", "uranium"): "92",
    ("jours_mois", "janvier"): "31", ("jours_mois", "fevrier"): "28", ("jours_mois", "avril"): "30",
    ("jours_mois", "juin"): "30", ("jours_mois", "decembre"): "31",
    ("mois_nom", "1"): "janvier", ("mois_nom", "12"): "decembre",
    ("jour_semaine", "1"): "lundi", ("jour_semaine", "7"): "dimanche",
    ("prefixe_si", "kilo"): "3", ("prefixe_si", "deci"): "-1", ("prefixe_si", "milli"): "-3",
    ("prefixe_si", "micro"): "-6", ("prefixe_si", "giga"): "9", ("prefixe_si", "mega"): "6",
    # chiffres romains — INCLUT L (50) et D (500) : clés mono-lettre = articles français -> garde du fix `articles`.
    ("chiffre_romain", "I"): "1", ("chiffre_romain", "V"): "5", ("chiffre_romain", "X"): "10",
    ("chiffre_romain", "L"): "50", ("chiffre_romain", "C"): "100", ("chiffre_romain", "D"): "500",
    ("chiffre_romain", "M"): "1000",
    ("rang_lettre_grecque", "alpha"): "1", ("rang_lettre_grecque", "mu"): "12",
    ("rang_lettre_grecque", "pi"): "16", ("rang_lettre_grecque", "oméga"): "24",
    ("rang_planete", "mercure"): "1", ("rang_planete", "terre"): "3", ("rang_planete", "neptune"): "8",
    ("code_iso_pays", "france"): "FR", ("code_iso_pays", "royaume uni"): "GB",
    ("code_iso_pays", "etats unis"): "US", ("code_iso_pays", "japon"): "JP",
    ("code_iso_pays", "suisse"): "CH", ("code_iso_pays", "allemagne"): "DE",
    ("prefixe_binaire", "kibi"): "10", ("prefixe_binaire", "gibi"): "30", ("prefixe_binaire", "tebi"): "40",
    ("durete_mohs", "talc"): "1", ("durete_mohs", "quartz"): "7", ("durete_mohs", "diamant"): "10",
    ("code_devise", "euro"): "EUR", ("code_devise", "dollar americain"): "USD",
    ("code_devise", "livre sterling"): "GBP", ("code_devise", "yen"): "JPY", ("code_devise", "franc suisse"): "CHF",
    ("indicatif_telephonique", "france"): "33", ("indicatif_telephonique", "etats unis"): "1",
    ("indicatif_telephonique", "royaume uni"): "44", ("indicatif_telephonique", "japon"): "81",
    ("symbole_prefixe_si", "kilo"): "k", ("symbole_prefixe_si", "mega"): "M", ("symbole_prefixe_si", "milli"): "m",
    ("continent", "france"): "Europe", ("continent", "japon"): "Asie", ("continent", "bresil"): "Amérique du Sud",
    ("continent", "egypte"): "Afrique", ("continent", "australie"): "Océanie",
    ("superficie", "france"): "551695", ("superficie", "russie"): "17098242", ("superficie", "suisse"): "41284",
    ("sans_littoral", "suisse"): "oui", ("sans_littoral", "france"): "non", ("sans_littoral", "bolivie"): "oui",
    ("domaine_internet", "france"): ".fr", ("domaine_internet", "japon"): ".jp", ("domaine_internet", "suisse"): ".ch",
    ("masse_atomique", "hydrogene"): "1.008", ("masse_atomique", "carbone"): "12.011",
    ("masse_atomique", "oxygene"): "15.999",
    ("electronegativite", "fluor"): "3.98", ("electronegativite", "oxygene"): "3.44",
    ("etat_standard", "mercure"): "liquide", ("etat_standard", "fer"): "solide",
    ("etat_standard", "hydrogene"): "gaz", ("etat_standard", "brome"): "liquide",
    ("periode_element", "fer"): "4", ("periode_element", "or"): "6", ("periode_element", "oxygene"): "2",
    ("groupe_element", "fer"): "8", ("groupe_element", "sodium"): "1", ("groupe_element", "oxygene"): "16",
    ("point_fusion", "fer"): "1811", ("point_fusion", "mercure"): "234.321",
    ("point_ebullition", "fer"): "3134", ("point_ebullition", "or"): "3243",
    ("gentile", "france"): "Français", ("gentile", "japon"): "Japonais", ("gentile", "allemagne"): "Allemand",
    ("configuration_electronique", "fer"): "[Ar] 3d6 4s2", ("configuration_electronique", "helium"): "1s2",
    ("configuration_electronique", "sodium"): "[Ne] 3s1", ("configuration_electronique", "chrome"): "[Ar] 3d5 4s1",
    ("categorie_element", "fer"): "métal de transition", ("categorie_element", "sodium"): "métal alcalin",
    ("categorie_element", "helium"): "gaz noble", ("categorie_element", "silicium"): "métalloïde",
    ("genre_grammatical", "eau"): "féminin", ("genre_grammatical", "soleil"): "masculin",
    ("genre_grammatical", "table"): "féminin", ("genre_grammatical", "chat"): "masculin",
    ("genre_grammatical", "petale"): "masculin", ("genre_grammatical", "ovule"): "masculin",
    ("genre_grammatical", "ecchymose"): "féminin", ("genre_grammatical", "espece"): "féminin",
    ("genre_grammatical", "antre"): "masculin", ("genre_grammatical", "apogee"): "masculin",
    ("point_culminant", "japon"): "mont Fuji", ("point_culminant", "argentine"): "Aconcagua",
    ("point_culminant", "nepal"): "Everest",
    ("pays_de_capitale", "paris"): "France", ("pays_de_capitale", "tokyo"): "Japon",
    ("pays_de_capitale", "berlin"): "Allemagne",
    ("hymne_national", "france"): "La Marseillaise", ("hymne_national", "japon"): "Kimi ga yo",
    ("affinite_electronique", "chlore"): "348.575", ("affinite_electronique", "hydrogene"): "72.769",
    ("energie_ionisation", "hydrogene"): "1312", ("energie_ionisation", "sodium"): "495.8",
    ("capacite_thermique_molaire", "fer"): "25.1",
    ("code_langue", "français"): "fr", ("code_langue", "anglais"): "en", ("code_langue", "allemand"): "de",
    ("code_langue", "russe"): "ru", ("code_langue", "chinois"): "zh", ("code_langue", "arabe"): "ar",
    ("sens_conduite", "france"): "droite", ("sens_conduite", "japon"): "gauche",
    ("sens_conduite", "royaume uni"): "gauche", ("sens_conduite", "etats unis"): "droite",
    ("code_iso_numerique", "france"): "250", ("code_iso_numerique", "japon"): "392",
    ("code_iso_numerique", "allemagne"): "276",
    ("drapeau_emoji", "france"): "🇫🇷", ("drapeau_emoji", "japon"): "🇯🇵",
    ("code_olympique", "france"): "FRA", ("code_olympique", "allemagne"): "GER",
    ("code_olympique", "etats unis"): "USA",
    ("pluriel", "cheval"): "chevaux", ("pluriel", "journal"): "journaux",
    ("pluriel", "chou"): "choux", ("pluriel", "genou"): "genoux",
    ("diametre_moyen_planete", "terre"): "12742", ("diametre_moyen_planete", "jupiter"): "139820",
    ("diametre_moyen_planete", "mars"): "6779",
    ("type_planete", "terre"): "tellurique", ("type_planete", "jupiter"): "géante gazeuse",
    ("anneaux_planete", "saturne"): "oui", ("anneaux_planete", "terre"): "non",
    ("planete_naine", "pluton"): "planète naine", ("planete_naine", "ceres"): "planète naine",
    ("planete_parente", "lune"): "terre", ("planete_parente", "titan"): "saturne",
    ("planete_parente", "io"): "jupiter",
    ("numero_mois", "janvier"): "1", ("numero_mois", "decembre"): "12",
    ("numero_jour_semaine", "lundi"): "1", ("numero_jour_semaine", "dimanche"): "7",
    ("formule_chimique", "eau"): "H2O", ("formule_chimique", "dioxyde de carbone"): "CO2",
    ("formule_chimique", "methane"): "CH4", ("formule_chimique", "glucose"): "C6H12O6",
    ("monnaie", "france"): "euro", ("monnaie", "japon"): "yen", ("monnaie", "etats unis"): "dollar americain",
    ("monnaie", "suisse"): "franc suisse",
    ("langue_officielle", "france"): "français", ("langue_officielle", "bresil"): "portugais",
    ("langue_officielle", "mexique"): "espagnol",
    ("cotes_polygone", "triangle"): "3", ("cotes_polygone", "hexagone"): "6", ("cotes_polygone", "octogone"): "8",
    ("faces_solide", "cube"): "6", ("faces_solide", "tetraedre"): "4", ("faces_solide", "icosaedre"): "20",
    ("nom_polygone", "3"): "triangle", ("nom_polygone", "6"): "hexagone", ("nom_polygone", "8"): "octogone",
    ("grandeur_unite", "metre"): "longueur", ("grandeur_unite", "seconde"): "temps",
    ("grandeur_unite", "watt"): "puissance", ("grandeur_unite", "newton"): "force",
    ("symbole_unite", "metre"): "m", ("symbole_unite", "seconde"): "s", ("symbole_unite", "kilogramme"): "kg",
    ("symbole_unite", "ohm"): "Ω", ("symbole_unite", "watt"): "W",
    # BIOLOGIE — animal -> classe (faits certains, vérifiés indépendamment)
    ("classe_animal", "chien"): "mammifère", ("classe_animal", "baleine"): "mammifère",
    ("classe_animal", "chauve-souris"): "mammifère", ("classe_animal", "aigle"): "oiseau",
    ("classe_animal", "manchot"): "oiseau", ("classe_animal", "requin"): "poisson",
    ("classe_animal", "hippocampe"): "poisson", ("classe_animal", "crocodile"): "reptile",
    ("classe_animal", "tortue"): "reptile", ("classe_animal", "grenouille"): "amphibien",
    ("classe_animal", "salamandre"): "amphibien", ("classe_animal", "fourmi"): "insecte",
    ("classe_animal", "papillon"): "insecte", ("classe_animal", "araignée"): "arachnide",
    ("classe_animal", "scorpion"): "arachnide", ("classe_animal", "crabe"): "crustacé",
    ("classe_animal", "homard"): "crustacé", ("classe_animal", "escargot"): "mollusque",
    ("classe_animal", "poulpe"): "mollusque",
    # CORPS HUMAIN — organe -> système (faits certains)
    ("systeme_organe", "cœur"): "circulatoire", ("systeme_organe", "poumon"): "respiratoire",
    ("systeme_organe", "estomac"): "digestif", ("systeme_organe", "rein"): "urinaire",
    ("systeme_organe", "cerveau"): "nerveux", ("systeme_organe", "fémur"): "squelettique",
    ("systeme_organe", "thyroïde"): "endocrinien", ("systeme_organe", "peau"): "tégumentaire",
    # HISTOIRE — événement -> année (extension certaine, non disputée)
    ("annee", "prise de la bastille"): "1789", ("annee", "couronnement de charlemagne"): "800",
    ("annee", "chute de constantinople"): "1453", ("annee", "débarquement de normandie"): "1944",
    ("annee", "traité de rome"): "1957", ("annee", "abolition de la peine de mort en france"): "1981",
    # GÉO PHYSIQUE — fleuve/montagne -> continent (certain)
    ("continent_fleuve", "nil"): "Afrique", ("continent_fleuve", "amazone"): "Amérique du Sud",
    ("continent_fleuve", "mississippi"): "Amérique du Nord", ("continent_fleuve", "yangtsé"): "Asie",
    ("continent_fleuve", "danube"): "Europe", ("continent_fleuve", "murray"): "Océanie",
    ("continent_montagne", "everest"): "Asie", ("continent_montagne", "mont blanc"): "Europe",
    ("continent_montagne", "kilimandjaro"): "Afrique", ("continent_montagne", "aconcagua"): "Amérique du Sud",
    ("continent_montagne", "denali"): "Amérique du Nord", ("continent_montagne", "mont vinson"): "Antarctique",
    # GÉO PHYSIQUE — île/volcan -> continent (P30, certain)
    ("continent_ile", "majorque"): "Europe", ("continent_ile", "île de baffin"): "Amérique du Nord",
    ("continent_volcan", "laki"): "Europe", ("continent_volcan", "mont aso"): "Asie",
    ("continent_chaine_montagne", "alpes"): "Europe", ("continent_chaine_montagne", "himalaya"): "Asie",
    ("continent_chaine_montagne", "montagnes rocheuses"): "Amérique du Nord",
    ("continent_chaine_montagne", "atlas"): "Afrique",
    ("continent_lac", "lac baïkal"): "Asie", ("continent_lac", "lac tanganyika"): "Afrique",
    ("continent_lac", "réservoir de kakhovka"): "Europe", ("continent_lac", "lac bierstadt"): "Amérique du Nord",
    ("continent_peninsule", "anatolie"): "Asie", ("continent_peninsule", "péninsule ibérique"): "Europe",
    ("continent_peninsule", "péninsule scandinave"): "Europe", ("continent_peninsule", "cap adare"): "Antarctique",
    ("continent_riviere", "volga"): "Europe", ("continent_riviere", "gange"): "Asie",
    ("continent_riviere", "mississippi"): "Amérique du Nord", ("continent_riviere", "congo"): "Afrique",
    ("continent_riviere", "río putumayo"): "Amérique du Sud",
    ("continent_archipel", "fidji"): "Océanie", ("continent_archipel", "îles canaries"): "Afrique",
    ("continent_archipel", "bahamas"): "Amérique du Nord", ("continent_archipel", "indonésie"): "Asie",
    ("continent_archipel", "svalbard"): "Europe", ("continent_archipel", "îles malouines"): "Amérique du Sud",
    ("continent_glacier", "glacier lambert"): "Antarctique",
    ("continent_glacier", "glacier hubbard"): "Amérique du Nord", ("continent_glacier", "öræfajökull"): "Europe",
    ("continent_cap", "cap adare"): "Antarctique", ("continent_cap", "cap alava"): "Amérique du Nord",
    ("continent_cap", "cap des trois-pointes"): "Afrique", ("continent_cap", "cap froward"): "Amérique du Sud",
    ("continent_cap", "cap kamenjak"): "Europe", ("continent_cap", "cap nelson"): "Océanie",
    ("continent_plateau", "altiplano"): "Amérique du Sud", ("continent_plateau", "plateau tibétain"): "Asie",
    ("continent_plateau", "plateau de bié"): "Afrique", ("continent_plateau", "moraine park"): "Amérique du Nord",
    ("continent_plateau", "plan de l'aiguille"): "Europe", ("continent_plateau", "dôme c"): "Antarctique",
    ("continent_vallee", "big bear valley"): "Amérique du Nord", ("continent_vallee", "vallée du gier"): "Europe",
    ("continent_vallee", "cirque de salazie"): "Afrique", ("continent_vallee", "hillary canyon"): "Antarctique",
    ("continent_vallee", "ouadi jib"): "Asie",
    ("continent_foret", "forêt de sambisa"): "Afrique", ("continent_foret", "douglaseraie des farges"): "Europe",
    ("continent_foret", "forêt nationale de coeur d'alene"): "Amérique du Nord",
    ("continent_baie", "baie de prydz"): "Antarctique", ("continent_baie", "baie tomales"): "Amérique du Nord",
    ("continent_baie", "baie de vostok"): "Asie",
    ("continent_chute_eau", "chute nevada"): "Amérique du Nord",
    ("continent_chute_eau", "cascade des aygalades"): "Europe",
    ("continent_chute_eau", "chutes d'aniwaniwa"): "Océanie",
    ("continent_grotte", "carlsbad cavern"): "Amérique du Nord",
    ("continent_grotte", "cueva del guitarrero"): "Amérique du Sud",
    ("continent_grotte", "caverne des hirondelles"): "Afrique",
    ("continent_col", "col des aravis"): "Europe", ("continent_col", "apache pass"): "Amérique du Nord",
    ("continent_col", "col de bellevue"): "Afrique",
    ("ocean_mer", "mer du nord"): "océan Atlantique", ("ocean_mer", "mer d'arabie"): "océan Indien",
    ("ocean_mer", "mer du japon"): "océan Pacifique", ("ocean_mer", "mer de barents"): "océan Arctique",
    ("ocean_mer", "mer de weddell"): "océan Austral",
    ("etoile_hote_exoplanete", "51 pegasi b"): "51 Pegasi",
    ("etoile_hote_exoplanete", "proxima centauri b"): "Proxima Centauri",
    ("etoile_hote_exoplanete", "hd 209458 b"): "HD 209458", ("etoile_hote_exoplanete", "55 cancri e"): "rho01 Cnc",
    ("etoile_hote_exoplanete", "kepler-452 b"): "Kepler-452", ("etoile_hote_exoplanete", "wasp-18b"): "WASP-18",
    # ASTRO — astre -> corps directement orbité (auto-sourcé Claude, système solaire, certain)
    ("corps_parent_astre", "terre"): "Soleil", ("corps_parent_astre", "lune"): "Terre",
    ("corps_parent_astre", "phobos"): "Mars", ("corps_parent_astre", "io"): "Jupiter",
    ("corps_parent_astre", "titan"): "Saturne", ("corps_parent_astre", "triton"): "Neptune",
    ("corps_parent_astre", "charon"): "Pluton",
    # ASTRO — étoile -> classe spectrale (Wikidata P215, borné ; ancres vérité-terrain)
    ("type_spectral_etoile", "soleil"): "G2V", ("type_spectral_etoile", "véga"): "A0Va",
    ("type_spectral_etoile", "rigel"): "B8Ia", ("type_spectral_etoile", "bételgeuse"): "M1-M2Ia-Iab",
    ("type_spectral_etoile", "pollux"): "K0III", ("type_spectral_etoile", "deneb"): "A2Ia",
    ("type_spectral_etoile", "proxima centauri"): "M4.5", ("type_spectral_etoile", "altaïr"): "A7Vn",
    # ASTRO — étoile variable -> type de variabilité (Wikidata P881, borné ; prototypes canoniques)
    ("type_etoile_variable", "algol"): "binaire à éclipses",
    ("type_etoile_variable", "delta cephei"): "céphéide classique",
    ("type_etoile_variable", "t tauri"): "étoile variable de type T Tauri",
    ("type_etoile_variable", "r leonis"): "étoile variable de type Mira",
    ("type_etoile_variable", "beta lyrae"): "binaire à éclipses",
    # ASTRO — astéroïde -> groupe orbital/dynamique (Wikidata P196 ; closed-set groupes, méta exclus)
    ("groupe_orbital_asteroide", "(433) éros"): "astéroïde Amor",
    ("groupe_orbital_asteroide", "(4) vesta"): "ceinture d'astéroïdes",
    ("groupe_orbital_asteroide", "(2) pallas"): "ceinture d'astéroïdes",
    # ASTRO — astéroïde -> lieu de découverte (Wikidata P65, source Minor Planet Center ; ancres historiques)
    ("lieu_decouverte_asteroide", "(1) cérès"): "observatoire astronomique de Palerme",
    ("lieu_decouverte_asteroide", "(4) vesta"): "Brême",
    ("lieu_decouverte_asteroide", "(16) psyché"): "observatoire astronomique de Capodimonte",
    ("lieu_decouverte_asteroide", "(9) métis"): "observatoire Markree",
    # ASTRO — relief de surface -> corps céleste réel (Wikidata P376 ; closed-set anti-fiction)
    ("astre_du_relief", "tycho"): "Lune", ("astre_du_relief", "copernic"): "Lune",
    ("astre_du_relief", "olympus mons"): "Mars", ("astre_du_relief", "valles marineris"): "Mars",
    ("astre_du_relief", "maxwell montes"): "Vénus", ("astre_du_relief", "tirawa"): "Rhéa",
    # ASTRO — galaxie -> type morphologique (Wikidata P223, séquence de Hubble ; ancres vérité-terrain)
    ("galaxie_morpho", "voie lactée"): "SBbc", ("galaxie_morpho", "galaxie d'andromède"): "SA(s)b",
    ("galaxie_morpho", "galaxie du triangle"): "SA(s)cd", ("galaxie_morpho", "galaxie du sombrero"): "Sa",
    ("galaxie_morpho", "grand nuage de magellan"): "SB(s)m",
    # ASTRO — exoplanète -> constellation (Wikidata P59 ; closed-set 88 IAU)
    ("constellation_exoplanete", "51 pegasi b"): "Pégase", ("constellation_exoplanete", "kepler-452 b"): "Cygne",
    ("constellation_exoplanete", "proxima centauri b"): "Centaure",
    ("constellation_exoplanete", "55 cancri e"): "Cancer",
    # ASTRO — constellation d'autres objets célestes (P59 ; closed-set 88 IAU)
    ("constellation_galaxie", "galaxie d'andromède"): "Andromède", ("constellation_galaxie", "m87"): "Vierge",
    ("constellation_galaxie", "m81"): "Grande Ourse", ("constellation_galaxie", "centaurus a"): "Centaure",
    ("constellation_nebuleuse", "nébuleuse d'orion"): "Orion",
    ("constellation_nebuleuse", "nébuleuse du crabe"): "Taureau",
    ("constellation_nebuleuse", "dentelles du cygne"): "Cygne",
    ("constellation_amas", "pléiades"): "Taureau", ("constellation_amas", "m22"): "Sagittaire",
    ("constellation_amas", "m4"): "Scorpion",
    ("constellation_quasar", "apm 08279+5255"): "Lynx", ("constellation_quasar", "cta-102"): "Pégase",
    # GÉO — subdivision administrative -> pays (P17 ; closed-set pays à code ISO)
    ("pays_subdivision", "bavière"): "Allemagne", ("pays_subdivision", "toscane"): "Italie",
    ("pays_subdivision", "californie"): "États-Unis", ("pays_subdivision", "ontario"): "Canada",
    ("pays_subdivision", "queensland"): "Australie", ("pays_subdivision", "bretagne"): "France",
    # GÉO — lieu -> subdivision administrative de 1er niveau (P131 valeur contrainte Q10864048)
    ("subdivision_lac", "lac okeechobee"): "Floride",
    ("subdivision_lac", "grand lac de l'ours"): "Territoires du Nord-Ouest",
    ("subdivision_lac", "lough neagh"): "Irlande du Nord",
    ("subdivision_montagne", "mont kosciuszko"): "Nouvelle-Galles du Sud",
    ("subdivision_montagne", "pizzo della presolana"): "Lombardie",
    ("subdivision_montagne", "djebel ouenza"): "wilaya de Tébessa",
    ("subdivision_riviere", "murrumbidgee"): "Nouvelle-Galles du Sud",
    ("subdivision_riviere", "kahiltna"): "Alaska",
    ("subdivision_riviere", "västerdalälven"): "Dalécarlie",
    ("subdivision_ile", "île boularderie"): "Nouvelle-Écosse",
    ("subdivision_ile", "île manukan"): "Sabah",
    ("subdivision_ile", "footprint island"): "Nunavut",
    ("subdivision_volcan", "kelud"): "Java oriental",
    ("subdivision_volcan", "mont blackburn"): "Alaska",
    ("subdivision_glacier", "glacier alsek"): "Alaska",
    ("subdivision_glacier", "glacier d'helheim"): "Sermersooq",
    ("subdivision_foret", "bois de gâtine"): "Bretagne",
    ("subdivision_chute_eau", "aldeyjarfoss"): "Norðurland eystra",
    ("subdivision_col", "abra del acay"): "Salta",
    ("subdivision_grotte", "actun tunichil muknal"): "Cayo",
    ("subdivision_baie", "abbot cove"): "Terre-Neuve-et-Labrador",
    ("subdivision_peninsule", "angeln"): "Schleswig-Holstein",
    ("subdivision_cap", "bec de l'aigle"): "Provence-Alpes-Côte d'Azur",
    ("subdivision_plage", "75 mile beach"): "Queensland",
    ("subdivision_desert", "désert arabique"): "gouvernorat de la Mer-Rouge",
    ("subdivision_plateau", "auyán tepuy"): "Bolívar",
    ("subdivision_vallee", "adventdalen"): "Svalbard",
    ("subdivision_canyon", "antelope canyon"): "Arizona",
    ("subdivision_source", "a-0 geyser"): "Wyoming",
    ("subdivision_recif", "abaiang"): "îles Gilbert",
    ("subdivision_marecage", "bassin d'atchafalaya"): "Louisiane",
    ("subdivision_delta", "delta de l'indus"): "Sind",
    ("subdivision_colline", "abelov vrh"): "Lika-Senj",
    ("subdivision_phare", "ancien phare de garðskagi"): "Suðurnes",
    ("subdivision_chateau", "altburg"): "Rhénanie-Palatinat",
    ("subdivision_monument", "32nd indiana monument"): "Kentucky",
    ("subdivision_monastere", "abbaye d'abington"): "Limerick",
    ("subdivision_eglise", "abbaye de romsey"): "Angleterre",
    ("subdivision_musee", "1st infantry division museum"): "Kansas",
    ("plan_eau_port", "abaskun"): "mer Caspienne",
    ("plan_eau_ile", "corse"): "mer Méditerranée",
    ("plan_eau_ile", "île de la réunion"): "océan Indien",
    ("plan_eau_plage", "75 mile beach"): "mer de Corail",
    ("plan_eau_peninsule", "akamas"): "mer Méditerranée",
    ("plan_eau_cap", "beachy head"): "Manche",
    ("plan_eau_barrage", "barrage allard"): "rivière Saint-Charles",
    ("plan_eau_phare", "anapa"): "mer Noire",
    ("ville_sur_ile", "coskata"): "Nantucket",
    ("ville_sur_ile", "kefalás"): "Crète",
    ("montagne_chaine", "acatenango"): "Sierra Madre de Chiapas",
    ("montagne_chaine", "abra grande"): "cordillère des Andes",
    ("ile_archipel", "abd al kuri"): "archipel de Socotra",
    ("col_chaine", "ahartzako lepoa"): "Pyrénées",
    ("col_chaine", "abra del acay"): "cordillère des Andes",
    ("glacier_chaine", "bear glacier"): "Montagnes Kenai",
    ("glacier_chaine", "blaueis"): "Alpes",
    ("methode_decouverte_exoplanete", "51 pegasi b"): "méthode des vitesses radiales",
    ("methode_decouverte_exoplanete", "51 eridani b"): "imagerie directe",
    ("methode_decouverte_exoplanete", "kepler-221 c"): "méthode des transits",
    ("exutoire_lac", "gülper see"): "Rhin",
    ("exutoire_lac", "lake repulse"): "Derwent River",
    ("bassin_lac", "achensee"): "bassin du Danube",
    ("point_culminant_massif", "cuillin"): "Sgùrr Alasdair",
    ("planete_parente_lune", "lune"): "Terre",
    ("planete_parente_lune", "io"): "Jupiter",
    ("planete_parente_lune", "titan"): "Saturne",
    ("planete_parente_lune", "charon"): "Pluton",
    ("capitale_subdivision", "cantabrie"): "Santander",
    ("capitale_subdivision", "tessin"): "Pavie",
    ("iso_subdivision", "rabat-salé-kénitra"): "MA-04",
    ("iso_subdivision", "lusaka"): "ZM-09",
    ("categorie_uicn_aire_protegee", "parc national de banff"): "catégorie II : Parc national",
    ("categorie_uicn_aire_protegee", "parc national de la vanoise"): "catégorie II : Parc national",
    ("subdivision_parc_national", "band-e amir"): "Bâmiyân",
    ("subdivision_canal", "a.g. wildervanckkanaal"): "Groningue",
    ("subdivision_mine", "almy (wyoming)"): "Wyoming",
    ("subdivision_site_archeo", "abbir maius"): "Zaghouan",
    ("subdivision_reservoir", "aberdeen lake"): "Mississippi",
    ("subdivision_observatoire", "algonquin radio observatory"): "Ontario",
    ("volcan_chaine", "chimborazo"): "cordillère des Andes",
    ("volcan_sur_ile", "merapi"): "Java",
    ("pays_code_vehicule", "afghanistan"): "AFG",
    ("pays_code_vehicule", "algérie"): "DZ",
    ("pays_point_bas", "grèce"): "Fosse Calypso",
    ("phare_sur_ile", "phare de klein curaçao"): "Klein Curaçao",
    ("montagne_sur_ile", "mauna kea"): "Hawaï",
    ("montagne_sur_ile", "aoraki/mont cook"): "île du Sud",
    ("statut_patrimonial_monument", "arc de triomphe de l'étoile"): "monument historique classé",
    ("fips_subdivision", "abou dabi"): "AE01",
    ("fips_subdivision", "abia"): "NI45",
    ("gestionnaire_aire_protegee", "resting spring range wilderness"): "Bureau of Land Management",
    ("lac_sur_ile", "bear lake"): "île Devon",
    ("lac_sur_ile", "lac waiʻau"): "Hawaï",
    ("barrage_reservoir", "barrage d'itaipu"): "Réservoir d'Itaipu",
    ("nuts_subdivision", "abruzzes"): "ITF1",
    ("nuts_subdivision", "açores"): "PT200",
    ("subdivision_hotel", "1840s carrollton inn"): "Maryland",
    ("subdivision_stade", "al-marzook field at alumni stadium"): "Connecticut",
    ("subdivision_cimetiere", "allée d’honneur"): "Bakou",
    ("subdivision_theatre", "amphithéâtre archéologique"): "Béja",
    ("subdivision_palais", "arnsteinsches gartenpalais"): "Vienne",
    ("subdivision_tour", "bayterek"): "Astana",
    ("subdivision_mosquee", "al-sayyida nafisa"): "gouvernorat du Caire",
    ("subdivision_temple", "abbaye de romsey"): "Angleterre",
    ("subdivision_fortification", "aghurmi"): "Gouvernorat de Matrouh",
    ("subdivision_bibliotheque", "académie roumaine"): "Bucarest",
    ("subdivision_universite", "académie artistique d'état de biélorussie"): "Minsk",
    ("subdivision_hopital", "abbott northwestern hospital"): "Minnesota",
    ("subdivision_prison", "allan b. polunsky unit"): "Texas",
    ("subdivision_gratte_ciel", "1100 peachtree"): "Géorgie",
    ("subdivision_quartier", "13 septembrie"): "Bucarest",
    ("subdivision_rue", "11. novembra krastmala"): "Riga",
    ("subdivision_sculpture", "a sound garden"): "Washington",
    ("subdivision_reserve_naturelle", "ägeriried (rothenthurm) (35000)"): "canton de Schwytz",
    ("subdivision_barrage", "barrage álvaro obregón"): "Sonora",
    ("subdivision_place", "agora des dieux"): "Al Jabal al Akhdar",
    ("subdivision_port", "al shuaiba"): "La Mecque",
    ("subdivision_parc_attraction", "adventuredome"): "Nevada",
    ("subdivision_langue_off", "canton du tessin"): "italien",
    ("subdivision_langue_off", "québec"): "français",
    ("subdivision_langue_off", "bavière"): "allemand standard",
    ("climat_koppen_localite", "moscou"): "climat continental",
    ("climat_koppen_localite", "lima"): "climat désertique",
    ("climat_koppen_localite", "manille"): "climat de mousson tropical",
    # MUSIQUE — instrument -> famille (certain)
    ("famille_instrument", "violon"): "cordes", ("famille_instrument", "saxophone"): "bois",
    ("famille_instrument", "trompette"): "cuivres", ("famille_instrument", "tambour"): "percussions",
    ("famille_instrument", "piano"): "claviers", ("famille_instrument", "flûte"): "bois",
    # LINGUISTIQUE — langue -> famille (certain)
    ("famille_langue", "français"): "romane", ("famille_langue", "anglais"): "germanique",
    ("famille_langue", "russe"): "slave", ("famille_langue", "arabe"): "sémitique",
    ("famille_langue", "hindi"): "indo-aryenne", ("famille_langue", "finnois"): "ouralienne",
    # MYTHOLOGIE — dieu grec -> domaine + équivalent romain (canonique)
    ("domaine_dieu", "poséidon"): "mer", ("domaine_dieu", "arès"): "guerre",
    ("domaine_dieu", "aphrodite"): "amour", ("domaine_dieu", "hadès"): "enfers",
    ("equivalent_romain", "zeus"): "jupiter", ("equivalent_romain", "héra"): "junon",
    ("equivalent_romain", "athéna"): "minerve", ("equivalent_romain", "arès"): "mars",
    # SPORT — joueurs par équipe (règlement)
    ("joueurs_par_equipe", "football"): "11", ("joueurs_par_equipe", "basketball"): "5",
    ("joueurs_par_equipe", "rugby à xv"): "15", ("joueurs_par_equipe", "volley-ball"): "6",
    ("joueurs_par_equipe", "handball"): "7",
    # CHIMIE — élément -> famille (groupes nommés)
    ("famille_chimique", "hélium"): "gaz noble", ("famille_chimique", "chlore"): "halogène",
    ("famille_chimique", "sodium"): "métal alcalin", ("famille_chimique", "calcium"): "métal alcalino-terreux",
    # LITTÉRATURE — œuvre -> auteur (paternité certaine)
    ("auteur_oeuvre", "les misérables"): "Victor Hugo", ("auteur_oeuvre", "germinal"): "Émile Zola",
    ("auteur_oeuvre", "le petit prince"): "Antoine de Saint-Exupéry",
    ("auteur_oeuvre", "1984"): "George Orwell", ("auteur_oeuvre", "l'étranger"): "Albert Camus",
    # PEINTURE — œuvre -> peintre (attribution certaine)
    ("peintre_oeuvre", "la joconde"): "Léonard de Vinci", ("peintre_oeuvre", "guernica"): "Pablo Picasso",
    ("peintre_oeuvre", "le cri"): "Edvard Munch", ("peintre_oeuvre", "la nuit étoilée"): "Vincent van Gogh",
    # CHIMIE — composé -> formule (extension)
    ("formule_chimique", "éthanol"): "C2H6O", ("formule_chimique", "acide sulfurique"): "H2SO4",
    ("formule_chimique", "benzène"): "C6H6", ("formule_chimique", "saccharose"): "C12H22O11",
    # SCIENCES — découverte -> auteur (consensuel)
    ("auteur_decouverte", "gravitation universelle"): "Isaac Newton",
    ("auteur_decouverte", "théorie de l'évolution"): "Charles Darwin",
    ("auteur_decouverte", "relativité"): "Albert Einstein",
    ("auteur_decouverte", "pénicilline"): "Alexander Fleming",
    # RELIGIONS — texte sacré + lieu de culte (canonique)
    ("texte_sacre", "islam"): "Coran", ("texte_sacre", "judaïsme"): "Torah",
    ("texte_sacre", "christianisme"): "Bible",
    ("lieu_culte", "islam"): "mosquée", ("lieu_culte", "judaïsme"): "synagogue",
    # ÉCONOMIE — monnaie -> symbole
    ("symbole_monnaie", "euro"): "€", ("symbole_monnaie", "livre sterling"): "£",
    ("symbole_monnaie", "yen"): "¥", ("symbole_monnaie", "roupie indienne"): "₹",
    # MUSIQUE CLASSIQUE — œuvre -> compositeur
    ("compositeur_oeuvre", "les quatre saisons"): "Antonio Vivaldi",
    ("compositeur_oeuvre", "la flûte enchantée"): "Wolfgang Amadeus Mozart",
    ("compositeur_oeuvre", "le boléro"): "Maurice Ravel",
    ("compositeur_oeuvre", "carmen"): "Georges Bizet",
    # MONUMENTS — monument -> pays/ville
    ("pays_monument", "tour eiffel"): "France", ("pays_monument", "colisée"): "Italie",
    ("pays_monument", "taj mahal"): "Inde", ("ville_monument", "tour eiffel"): "Paris",
    ("ville_monument", "statue de la liberté"): "New York",
    # CINÉMA — film -> réalisateur
    ("realisateur_film", "le parrain"): "Francis Ford Coppola",
    ("realisateur_film", "pulp fiction"): "Quentin Tarantino",
    ("realisateur_film", "titanic"): "James Cameron",
    ("realisateur_film", "inception"): "Christopher Nolan",
    # FÊTES NATIONALES — pays -> date
    ("fete_nationale", "france"): "14 juillet", ("fete_nationale", "états-unis"): "4 juillet",
    ("fete_nationale", "belgique"): "21 juillet", ("fete_nationale", "suisse"): "1er août",
    # CRIS D'ANIMAUX — animal -> cri
    ("cri_animal", "chien"): "aboiement", ("cri_animal", "cheval"): "hennissement",
    ("cri_animal", "loup"): "hurlement", ("cri_animal", "âne"): "braiement",
    # DISCIPLINES — objet d'étude
    ("objet_etude", "cardiologie"): "le cœur", ("objet_etude", "entomologie"): "les insectes",
    ("objet_etude", "volcanologie"): "les volcans", ("objet_etude", "ornithologie"): "les oiseaux",
    # MYTHOLOGIES — domaine (égyptiens/nordiques) + panthéon
    ("domaine_dieu", "râ"): "soleil", ("domaine_dieu", "odin"): "sagesse et guerre",
    ("domaine_dieu", "thor"): "tonnerre", ("domaine_dieu", "anubis"): "momification et morts",
    ("pantheon_dieu", "zeus"): "grec", ("pantheon_dieu", "jupiter"): "romain",
    ("pantheon_dieu", "râ"): "égyptien", ("pantheon_dieu", "odin"): "nordique",
    # INFORMATIQUE — extension -> langage / type
    ("langage_extension", ".py"): "Python", ("langage_extension", ".rs"): "Rust",
    ("langage_extension", ".java"): "Java", ("type_fichier", ".mp3"): "audio",
    ("type_fichier", ".pdf"): "document", ("type_fichier", ".png"): "image",
    # VITAMINES — vitamine -> nom chimique
    ("nom_vitamine", "vitamine c"): "acide ascorbique", ("nom_vitamine", "vitamine d"): "calciférol",
    ("nom_vitamine", "vitamine b12"): "cobalamine", ("nom_vitamine", "vitamine a"): "rétinol",
    # COULEURS — couleur -> hex sRGB
    ("code_hex_couleur", "rouge"): "#FF0000", ("code_hex_couleur", "noir"): "#000000",
    ("code_hex_couleur", "blanc"): "#FFFFFF", ("code_hex_couleur", "bleu"): "#0000FF",
    # ZODIAQUE — signe -> élément
    ("element_zodiaque", "bélier"): "feu", ("element_zodiaque", "taureau"): "terre",
    ("element_zodiaque", "gémeaux"): "air", ("element_zodiaque", "cancer"): "eau",
    # BIOLOGIE — régime alimentaire
    ("regime_alimentaire", "lion"): "carnivore", ("regime_alimentaire", "vache"): "herbivore",
    ("regime_alimentaire", "sanglier"): "omnivore", ("regime_alimentaire", "grand requin blanc"): "carnivore",  # T1: « cochon »/« requin » absents -> ancres sur « sanglier »/« grand requin blanc » (présents)
    # ASTRO+CHIMIE — couleur de flamme + plus grande lune
    ("couleur_flamme", "sodium"): "jaune", ("couleur_flamme", "cuivre"): "vert",
    ("plus_grande_lune", "jupiter"): "Ganymède", ("plus_grande_lune", "saturne"): "Titan",
    ("plus_grande_lune", "terre"): "Lune",
    # SIGLES — sigle -> signification
    ("signification_sigle", "onu"): "Organisation des Nations Unies",
    ("signification_sigle", "adn"): "acide désoxyribonucléique",
    ("signification_sigle", "pib"): "produit intérieur brut",
    ("signification_sigle", "nasa"): "National Aeronautics and Space Administration",
    # CONSTANTES MATH — constante -> valeur
    ("valeur_constante", "pi"): "3.14159265", ("valeur_constante", "e"): "2.71828183",
    ("valeur_constante", "nombre d'or"): "1.61803399",
    ("valeur_constante", "racine carrée de deux"): "1.41421356",
    # FONCTION ORGANE — organe -> fonction
    ("fonction_organe", "cœur"): "pomper le sang",
    ("fonction_organe", "œil"): "permettre la vision",
    # PHOBIES — phobie -> objet
    ("objet_phobie", "arachnophobie"): "les araignées",
    ("objet_phobie", "claustrophobie"): "les espaces clos",
    ("objet_phobie", "acrophobie"): "les hauteurs",
    # PETITS D'ANIMAUX — animal -> petit
    ("petit_animal", "chien"): "chiot", ("petit_animal", "vache"): "veau",
    ("petit_animal", "cheval"): "poulain", ("petit_animal", "sanglier"): "marcassin",
    # ALLIAGES — alliage -> composition
    ("composition_alliage", "bronze"): "cuivre et étain",
    ("composition_alliage", "laiton"): "cuivre et zinc",
    ("composition_alliage", "acier"): "fer et carbone",
    # VILLES — ville -> pays (seed + volume QLever Q486972/pop>=50k, homonymes multi-pays -> HORS)
    ("pays_ville", "new york"): "États-Unis", ("pays_ville", "barcelone"): "Espagne",
    ("pays_ville", "milan"): "Italie", ("pays_ville", "osaka"): "Japon",
    ("pays_ville", "paris"): "France", ("pays_ville", "berlin"): "Allemagne",
    ("pays_ville", "buenos aires"): "Argentine", ("pays_ville", "le caire"): "Égypte",
    ("pays_ville", "lagos"): "Nigeria", ("pays_ville", "karachi"): "Pakistan",
    # MALADIES — maladie -> agent
    ("agent_maladie", "grippe"): "virus", ("agent_maladie", "tuberculose"): "bactérie",
    ("agent_maladie", "paludisme"): "parasite", ("agent_maladie", "candidose"): "champignon",
    # ROCHES — roche -> type
    ("type_roche", "granite"): "magmatique", ("type_roche", "calcaire"): "sédimentaire",
    ("type_roche", "marbre"): "métamorphique",
    # SYMBOLES MATH — concept -> symbole
    ("symbole_math", "addition"): "+", ("symbole_math", "racine carrée"): "√",
    ("symbole_math", "infini"): "∞", ("symbole_math", "somme"): "∑",
    # COULEURS SECONDAIRES — couleur -> mélange
    ("melange_couleur", "orange"): "rouge et jaune", ("melange_couleur", "violet"): "rouge et bleu",
    # FRUITS -> ARBRES
    ("arbre_fruit", "pomme"): "pommier", ("arbre_fruit", "olive"): "olivier",
    ("arbre_fruit", "noix"): "noyer",
    # MYTHOLOGIE HINDOUE
    ("domaine_dieu", "shiva"): "destruction et transformation",
    ("domaine_dieu", "ganesh"): "sagesse et obstacles",
    ("pantheon_dieu", "vishnou"): "hindou", ("pantheon_dieu", "shiva"): "hindou",
    # INSTRUMENTS DE MESURE
    ("mesure_instrument", "thermomètre"): "la température",
    ("mesure_instrument", "baromètre"): "la pression atmosphérique",
    ("mesure_instrument", "sismographe"): "les séismes",
    # DANSES -> PAYS
    ("pays_danse", "tango"): "Argentine", ("pays_danse", "flamenco"): "Espagne",
    ("pays_danse", "samba"): "Brésil",
    # BD / PERSONNAGES / RELIGIONS
    ("auteur_bd", "tintin"): "Hergé", ("auteur_bd", "les schtroumpfs"): "Peyo",
    ("createur_personnage", "sherlock holmes"): "Arthur Conan Doyle",
    ("createur_personnage", "james bond"): "Ian Fleming",
    ("fondateur_religion", "islam"): "Mahomet",
    ("fondateur_religion", "protestantisme"): "Martin Luther",
    # GASTRONOMIE + SALUTATIONS
    ("pays_plat", "pizza"): "Italie", ("pays_plat", "sushi"): "Japon",
    ("pays_plat", "paella"): "Espagne", ("pays_plat", "tacos"): "Mexique",
    ("bonjour_langue", "espagnol"): "hola", ("bonjour_langue", "italien"): "buongiorno",
    ("merci_langue", "allemand"): "danke", ("merci_langue", "japonais"): "arigato",
    # INVENTEURS / PRIX / SENS
    ("inventeur", "dynamite"): "Alfred Nobel", ("inventeur", "braille"): "Louis Braille",
    ("domaine_prix", "palme d'or"): "le cinéma", ("domaine_prix", "ballon d'or"): "le football",
    ("domaine_prix", "médaille fields"): "les mathématiques",
    ("sens_organe", "œil"): "la vue", ("sens_organe", "nez"): "l'odorat",
    # NOTES / COLLECTIFS / VÊTEMENTS
    ("notation_anglaise_note", "do"): "C", ("notation_anglaise_note", "la"): "A",
    ("nom_groupe_animal", "loup"): "une meute", ("nom_groupe_animal", "poisson"): "un banc",
    ("partie_corps_vetement", "gant"): "les mains", ("partie_corps_vetement", "chapeau"): "la tête",
    # GENRES MUSICAUX / LOCUTIONS / JOURS SAINTS
    ("pays_genre_musical", "jazz"): "États-Unis", ("pays_genre_musical", "reggae"): "Jamaïque",
    ("sens_locution_latine", "carpe diem"): "cueille le jour (profite du moment présent)",
    ("sens_locution_latine", "alea jacta est"): "le sort en est jeté",
    ("jour_saint_religion", "islam"): "vendredi",
    # PAYS RENOMMÉS / SUBDIVISIONS / ARBRES
    ("nom_actuel", "perse"): "Iran", ("nom_actuel", "birmanie"): "Myanmar",
    ("nom_actuel", "siam"): "Thaïlande",
    ("subdivision_monnaie", "euro"): "centime", ("subdivision_monnaie", "rouble"): "kopeck",
    ("type_arbre", "chêne"): "feuillu", ("type_arbre", "sapin"): "conifère",
    # SURNOMS / DENTS / RACCOURCIS
    ("surnom_roi", "louis xiv"): "le Roi-Soleil", ("surnom_roi", "philippe iv"): "le Bel",
    ("fonction_dent", "molaire"): "broyer les aliments",
    ("fonction_dent", "incisive"): "couper les aliments",
    ("raccourci_clavier", "copier"): "Ctrl+C", ("raccourci_clavier", "annuler"): "Ctrl+Z",
    # OS / DEVISES / OLYMPISME
    ("region_os", "fémur"): "la cuisse", ("region_os", "crâne"): "la tête",
    ("devise_pays", "france"): "Liberté, Égalité, Fraternité",
    ("saison_olympique", "biathlon"): "hiver", ("saison_olympique", "natation"): "été",
    # BATAILLES / PERSONNAGES / COULEURS COMPLÉMENTAIRES
    ("guerre_bataille", "waterloo"): "les guerres napoléoniennes",
    ("guerre_bataille", "verdun"): "la Première Guerre mondiale",
    ("fonction_personnage", "napoléon bonaparte"): "empereur des Français",
    ("fonction_personnage", "cléopâtre"): "reine d'Égypte",
    ("couleur_complementaire", "rouge"): "vert", ("couleur_complementaire", "bleu"): "orange",
    # CRÉATURES / DÉSERTS / ASTRES
    ("origine_creature", "minotaure"): "grecque", ("origine_creature", "troll"): "nordique",
    ("continent_desert", "sahara"): "Afrique", ("continent_desert", "gobi"): "Asie",
    ("type_astre", "soleil"): "étoile", ("type_astre", "lune"): "satellite naturel",
    ("type_astre", "halley"): "comète",
    # LIEUX SAINTS / DURÉE NOTES / PONCTUATION
    ("lieu_saint_religion", "islam"): "La Mecque", ("lieu_saint_religion", "sikhisme"): "Amritsar",
    ("duree_note", "ronde"): "4 temps", ("duree_note", "noire"): "1 temps",
    ("symbole_ponctuation", "point"): ".", ("symbole_ponctuation", "arobase"): "@",
    # ANIMAUX DIEUX / CARDINAUX / NOMBRES EN LETTRES
    ("animal_dieu", "zeus"): "l'aigle", ("animal_dieu", "athéna"): "la chouette",
    ("oppose_cardinal", "nord"): "sud", ("oppose_cardinal", "est"): "ouest",
    ("oppose_cardinal", "nord-est"): "sud-ouest",
    ("nombre_en_lettres", "7"): "sept", ("nombre_en_lettres", "80"): "quatre-vingts",
    ("nombre_en_lettres", "100"): "cent",
    # IONS / pH / LETTRES GRECQUES
    ("charge_ion", "ion sodium"): "+1", ("charge_ion", "ion sulfate"): "-2",
    ("ph_substance", "citron"): "acide", ("ph_substance", "savon"): "basique",
    ("ph_substance", "eau pure"): "neutre",
    ("symbole_grec", "alpha"): "α", ("symbole_grec", "pi"): "π",
    # ORBITES / DISTANCES / OCÉANS
    ("periode_revolution_planete", "terre"): "365 jours",
    ("periode_revolution_planete", "mars"): "687 jours",
    ("distance_soleil", "terre"): "150", ("distance_soleil", "jupiter"): "778",
    ("rang_ocean", "océan pacifique"): "1", ("rang_ocean", "océan arctique"): "5",
    # ÉCHECS / ARTS MARTIAUX
    ("valeur_piece_echecs", "dame"): "9", ("valeur_piece_echecs", "tour"): "5",
    ("valeur_piece_echecs", "pion"): "1",
    ("pays_art_martial", "judo"): "Japon", ("pays_art_martial", "taekwondo"): "Corée du Sud",
    ("pays_art_martial", "kung-fu"): "Chine",
    # ORDRES — signes chinois / ceintures / arc-en-ciel
    ("ordre_signe_chinois", "rat"): "1", ("ordre_signe_chinois", "cochon"): "12",
    ("ordre_ceinture_judo", "blanche"): "1", ("ordre_ceinture_judo", "noire"): "7",
    ("ordre_arc_en_ciel", "rouge"): "1", ("ordre_arc_en_ciel", "violet"): "7",
    # BLOC ÉLÉMENTS / ANGLES / VENTS
    ("bloc_element", "sodium"): "s", ("bloc_element", "carbone"): "p",
    ("bloc_element", "fer"): "d", ("bloc_element", "uranium"): "f",
    ("mesure_angle", "angle droit"): "90°", ("mesure_angle", "angle plat"): "180°",
    ("origine_vent", "mistral"): "la vallée du Rhône (sud de la France)",
    ("origine_vent", "sirocco"): "le Sahara",
    # AFFIXES / ÉCRITURES
    ("sens_prefixe", "hyper"): "excès, au-dessus", ("sens_prefixe", "anti"): "contre",
    ("sens_suffixe", "-logie"): "étude, science", ("sens_suffixe", "-phobie"): "peur",
    ("ecriture_langue", "russe"): "alphabet cyrillique",
    ("ecriture_langue", "coréen"): "hangeul",
    # MARQUES -> PAYS (auto / tech / luxe)
    ("pays_marque_auto", "renault"): "France", ("pays_marque_auto", "toyota"): "Japon",
    ("pays_marque_auto", "ferrari"): "Italie",
    ("pays_marque_tech", "apple"): "États-Unis", ("pays_marque_tech", "samsung"): "Corée du Sud",
    ("pays_marque_tech", "nokia"): "Finlande",
    ("pays_marque_luxe", "chanel"): "France", ("pays_marque_luxe", "rolex"): "Suisse",
    ("pays_marque_luxe", "gucci"): "Italie",
    # PIERRES / OPTIQUE / NOMBRE ORGANES
    ("couleur_pierre", "rubis"): "rouge", ("couleur_pierre", "émeraude"): "vert",
    ("couleur_pierre", "saphir"): "bleu",
    ("usage_instrument_optique", "microscope"): "observer l'infiniment petit",
    ("usage_instrument_optique", "télescope"): "observer les astres lointains",
    ("nombre_organe", "cœur"): "1", ("nombre_organe", "rein"): "2",
    ("nombre_organe", "poumon"): "2",
    # CHIENS / FROMAGES / CÉPAGES
    ("pays_race_chien", "berger allemand"): "Allemagne", ("pays_race_chien", "labrador"): "Canada",
    ("pays_race_chien", "chihuahua"): "Mexique",
    ("pays_fromage", "camembert"): "France", ("pays_fromage", "mozzarella"): "Italie",
    ("pays_fromage", "gruyère"): "Suisse",
    ("couleur_cepage", "chardonnay"): "blanc", ("couleur_cepage", "merlot"): "rouge",
    # OTAN / MORSE / SYMBOLES ASTRO (d et l inclus -> non régression du piège _sans_articles)
    ("alphabet_otan", "a"): "Alpha", ("alphabet_otan", "d"): "Delta", ("alphabet_otan", "l"): "Lima",
    ("alphabet_otan", "z"): "Zulu",
    ("code_morse", "s"): "...", ("code_morse", "o"): "---", ("code_morse", "d"): "-..",
    ("code_morse", "l"): ".-..",
    ("symbole_astro_planete", "mars"): "♂", ("symbole_astro_planete", "vénus"): "♀",
    # CHATS / UNITÉS IMPÉRIALES / ÉPICES
    ("pays_race_chat", "siamois"): "Thaïlande", ("pays_race_chat", "persan"): "Iran",
    ("pays_race_chat", "chartreux"): "France",
    ("equivalent_metrique", "mile"): "1,609 km", ("equivalent_metrique", "pouce"): "2,54 cm",
    ("origine_epice", "poivre"): "Inde", ("origine_epice", "cannelle"): "Sri Lanka",
    # CORDES / BEAUFORT / BANQUES
    ("nombre_cordes", "violon"): "4", ("nombre_cordes", "guitare"): "6",
    ("beaufort_description", "0"): "calme", ("beaufort_description", "12"): "ouragan",
    ("banque_centrale", "euro"): "Banque centrale européenne",
    ("banque_centrale", "yen"): "Banque du Japon",
    # CARENCES / HORMONES / JO
    ("carence_vitamine", "vitamine c"): "le scorbut", ("carence_vitamine", "vitamine d"): "le rachitisme",
    ("hormone_organe", "pancréas"): "l'insuline", ("hormone_organe", "thyroïde"): "la thyroxine",
    ("ville_jo_ete", "1924"): "Paris", ("ville_jo_ete", "2024"): "Paris",
    ("ville_jo_ete", "2008"): "Pékin", ("ville_jo_ete", "1936"): "Berlin",
    # JO HIVER / DYNASTIES / EMBLÈMES FLORAUX
    ("ville_jo_hiver", "1924"): "Chamonix", ("ville_jo_hiver", "1992"): "Albertville",
    ("ville_jo_hiver", "2022"): "Pékin",
    ("pays_dynastie", "bourbon"): "France", ("pays_dynastie", "romanov"): "Russie",
    ("pays_dynastie", "ming"): "Chine",
    ("embleme_floral", "japon"): "le cerisier", ("embleme_floral", "canada"): "la feuille d'érable",
    # RÉSISTANCES / FUSEAUX / CÔTÉ ORGANES
    ("valeur_couleur_resistance", "noir"): "0", ("valeur_couleur_resistance", "rouge"): "2",
    ("valeur_couleur_resistance", "blanc"): "9",
    ("decalage_fuseau", "heure de paris"): "UTC+1", ("decalage_fuseau", "heure de tokyo"): "UTC+9",
    ("decalage_fuseau", "heure de new york"): "UTC-5",
    ("cote_organe", "foie"): "à droite", ("cote_organe", "rate"): "à gauche",
    # ATMOSPHÈRE / GAMMES / DURÉE MATCH
    ("atmosphere_planete", "mercure"): "non", ("atmosphere_planete", "terre"): "oui",
    ("nombre_notes_gamme", "gamme majeure"): "7", ("nombre_notes_gamme", "gamme chromatique"): "12",
    ("nombre_notes_gamme", "gamme pentatonique"): "5",
    ("duree_match", "football"): "90 minutes", ("duree_match", "rugby à xv"): "80 minutes",
}
for (rel, ent), attendu in ANCRES.items():
    st, f = L.repond(rel, ent)
    check(f"ancre {rel}({ent}) == {attendu}", st == VERIFIE and f.valeur == attendu)

# 3bis) COHÉRENCE SÉQUENTIELLE : les 36 premiers éléments DOIVENT être Z=1..36 dans l'ordre (anti-typo fort).
prem36 = L._NUMERO_ATOMIQUE[:36]
check("Z séquentiel 1..36 sans trou", [z for _, z in prem36] == list(range(1, 37)))
check("12 mois ingérés, jours ∈ {28,30,31}", len(L._JOURS_MOIS) == 12
      and all(j in (28, 30, 31) for _, j in L._JOURS_MOIS)
      and sum(j for _, j in L._JOURS_MOIS) == 365)   # année non bissextile = 365
check("alphabet grec = 24 lettres rang 1..24", [r for _, r in L._RANG_LETTRE_GRECQUE] == list(range(1, 25)))
check("planètes = 8 rang 1..8 (Pluton exclue)", [r for _, r in L._RANG_PLANETE] == list(range(1, 9))
      and "pluton" not in {n for n, _ in L._RANG_PLANETE})
check("préfixes SI : exposants distincts, kilo=3 milli=-3", len({e for _, e in L._PREFIXE_SI}) == len(L._PREFIXE_SI)
      and dict(L._PREFIXE_SI)["kilo"] == 3 and dict(L._PREFIXE_SI)["milli"] == -3)
check("romain : symboles canoniques I V X L C D M", [s for s, _ in L._CHIFFRE_ROMAIN] == list("IVXLCDM"))

# 3ter) SANITÉS STRUCTURELLES SUR LES TABLES CHARGÉES — scalent à l'ingestion à grande échelle.
# Ces invariants tiennent pour l'amorce ET pour tout dataset ingéré (datasets/lecteur/*.jsonl) -> ils
# attrapent une donnée structurellement aberrante (code mal formé, Z hors plage, doublon de code unique).
def _vals(rel):
    return [f.valeur for f in L.LECTEUR.tables.get(rel, {}).values()]

if "code_iso_pays" in L.LECTEUR.tables:
    v = _vals("code_iso_pays")
    check("STRUCT code_iso_pays : 2 lettres MAJ, codes uniques",
          all(len(c) == 2 and c.isascii() and c.isupper() for c in v) and len(set(v)) == len(v))
if "code_iso3_pays" in L.LECTEUR.tables:
    v = _vals("code_iso3_pays")
    check("STRUCT code_iso3_pays : 3 lettres MAJ, codes uniques",
          all(len(c) == 3 and c.isascii() and c.isupper() for c in v) and len(set(v)) == len(v))
if "numero_atomique" in L.LECTEUR.tables:
    v = _vals("numero_atomique")
    check("STRUCT numero_atomique : entiers 1..118, distincts",
          all(c.isdigit() and 1 <= int(c) <= 118 for c in v) and len(set(v)) == len(v))
if "symbole_chimique" in L.LECTEUR.tables:
    v = _vals("symbole_chimique")
    check("STRUCT symbole_chimique : 1-3 car. commençant par une MAJ, distincts",
          all(1 <= len(c) <= 3 and c[0].isupper() for c in v) and len(set(v)) == len(v))
if "indicatif_telephonique" in L.LECTEUR.tables:
    check("STRUCT indicatif_telephonique : chiffres uniquement",
          all(c.isdigit() for c in _vals("indicatif_telephonique")))
if "code_devise" in L.LECTEUR.tables:
    check("STRUCT code_devise : 3 lettres MAJ",
          all(len(c) == 3 and c.isascii() and c.isupper() for c in _vals("code_devise")))
if "genre_grammatical" in L.LECTEUR.tables:
    check("STRUCT genre_grammatical : valeurs ∈ {masculin, féminin}",
          set(_vals("genre_grammatical")) <= {"masculin", "féminin"})
if "etat_standard" in L.LECTEUR.tables:
    check("STRUCT etat_standard : valeurs ∈ {gaz, solide, liquide}",
          set(_vals("etat_standard")) <= {"gaz", "solide", "liquide"})
if "sans_littoral" in L.LECTEUR.tables:
    check("STRUCT sans_littoral : valeurs ∈ {oui, non}",
          set(_vals("sans_littoral")) <= {"oui", "non"})
if "periode_element" in L.LECTEUR.tables:
    check("STRUCT periode_element : entiers 1..7",
          all(c.isdigit() and 1 <= int(c) <= 7 for c in _vals("periode_element")))
if "groupe_element" in L.LECTEUR.tables:
    check("STRUCT groupe_element : entiers 1..18",
          all(c.isdigit() and 1 <= int(c) <= 18 for c in _vals("groupe_element")))
if "domaine_internet" in L.LECTEUR.tables:
    check("STRUCT domaine_internet : commence par un point",
          all(c.startswith(".") and len(c) >= 3 for c in _vals("domaine_internet")))
if "genre_grammatical" in L.LECTEUR.tables:  # (déjà couvert plus haut ; gardé groupé)
    pass
if "definition_nom" in L.LECTEUR.tables:
    _dn = L.LECTEUR.tables["definition_nom"]
    def _def(m):
        f = _dn.get(L.LECTEUR._cle("definition_nom", m))
        return (f.valeur if f else "").lower()
    # ancres par MOT-CLÉ (exact-string trop fragile pour de la prose) — sens vérifié indépendamment.
    check("definition_nom chat ~ félin/mammifère", "félin" in _def("chat") or "mammifère" in _def("chat"))
    check("definition_nom volcan ~ magma", "magma" in _def("volcan"))
    check("definition_nom démocratie ~ peuple/pouvoir", "peuple" in _def("démocratie") and "pouvoir" in _def("démocratie"))
    check("definition_nom photosynthèse ~ lumière/chlorophylle", "lumi" in _def("photosynthèse") or "chloro" in _def("photosynthèse") or "organism" in _def("photosynthèse"))
    # définitions courtes par SYNONYME légitimes (aminche->« ami. », bb->« bébé. ») -> seuil bas non-trivial.
    check("STRUCT definition_nom : définitions non triviales (>=2 car.)",
          all(len(v.strip()) >= 2 for v in _vals("definition_nom")))
if "code_langue" in L.LECTEUR.tables:
    v = _vals("code_langue")
    check("STRUCT code_langue : 2 lettres minuscules, codes uniques",
          all(len(c) == 2 and c.isascii() and c.islower() for c in v) and len(set(v)) == len(v))
if "sens_conduite" in L.LECTEUR.tables:
    check("STRUCT sens_conduite : valeurs ∈ {droite, gauche}",
          set(_vals("sens_conduite")) <= {"droite", "gauche"})
if "code_olympique" in L.LECTEUR.tables:
    v = _vals("code_olympique")
    check("STRUCT code_olympique : 3 lettres MAJ, codes uniques",
          all(len(c) == 3 and c.isascii() and c.isupper() for c in v) and len(set(v)) == len(v))
if "pluriel" in L.LECTEUR.tables:
    check("STRUCT pluriel : formes non triviales (>=2 car.)",
          all(len(c.strip()) >= 2 for c in _vals("pluriel")))
# NOTE T1 2026-06-26 : RÉCONCILIATION type_planete (collision T1↔T7). type_planete est une CATÉGORIE (couloir
# astro T1) -> vocabulaire SCIENTIFIQUE 3-valeurs {tellurique, géante gazeuse, géante de glace} (Neptune = géante
# de GLACE, pas « gazeuse »). Le check closed-set canonique est plus bas. Ancre alignée (jupiter -> géante gazeuse).
if "anneaux_planete" in L.LECTEUR.tables:
    check("STRUCT anneaux_planete : valeurs ∈ {oui, non}",
          set(_vals("anneaux_planete")) <= {"oui", "non"})
if "diametre_moyen_planete" in L.LECTEUR.tables:
    check("STRUCT diametre_moyen_planete : entiers positifs",
          all(c.isdigit() and int(c) > 0 for c in _vals("diametre_moyen_planete")))
if "planete_naine" in L.LECTEUR.tables:
    check("STRUCT planete_naine : valeur = « planète naine »",
          set(_vals("planete_naine")) <= {"planète naine"})
if "planete_parente" in L.LECTEUR.tables:
    check("STRUCT planete_parente : valeurs ∈ 8 planètes",
          set(_vals("planete_parente")) <= {"mercure", "vénus", "terre", "mars", "jupiter", "saturne", "uranus", "neptune"})
if "classe_animal" in L.LECTEUR.tables:
    check("STRUCT classe_animal : valeurs ∈ 9 classes zoologiques",
          set(_vals("classe_animal")) <= {"mammifère", "oiseau", "poisson", "reptile", "amphibien",
                                          "insecte", "arachnide", "crustacé", "mollusque"})
if "systeme_organe" in L.LECTEUR.tables:
    check("STRUCT systeme_organe : valeurs ∈ systèmes/appareils anatomiques",
          set(_vals("systeme_organe")) <= {"circulatoire", "respiratoire", "digestif", "urinaire",
                                           "nerveux", "musculaire", "squelettique", "reproducteur",
                                           "endocrinien", "tégumentaire"})
if "annee" in L.LECTEUR.tables:
    check("STRUCT annee : années entières (>= -10000), éventuellement négatives (av. J.-C.)",
          all(c.lstrip("-").isdigit() and -10000 <= int(c) <= 2100 for c in _vals("annee")))
_CONTINENTS = {"Afrique", "Asie", "Europe", "Amérique du Nord", "Amérique du Sud", "Océanie", "Antarctique"}
if "continent_fleuve" in L.LECTEUR.tables:
    check("STRUCT continent_fleuve : valeurs ∈ 7 continents",
          set(_vals("continent_fleuve")) <= _CONTINENTS)
if "continent_montagne" in L.LECTEUR.tables:
    check("STRUCT continent_montagne : valeurs ∈ 7 continents",
          set(_vals("continent_montagne")) <= _CONTINENTS)
if "continent_ile" in L.LECTEUR.tables:
    check("STRUCT continent_ile : valeurs ∈ 7 continents",
          set(_vals("continent_ile")) <= _CONTINENTS)
if "continent_volcan" in L.LECTEUR.tables:
    check("STRUCT continent_volcan : valeurs ∈ 7 continents",
          set(_vals("continent_volcan")) <= _CONTINENTS)
if "corps_parent_astre" in L.LECTEUR.tables:
    check("STRUCT corps_parent_astre : valeurs ∈ corps-parents du système solaire",
          set(_vals("corps_parent_astre")) <=
          {"Soleil", "Terre", "Mars", "Jupiter", "Saturne", "Uranus", "Neptune", "Pluton"})
if "type_planete" in L.LECTEUR.tables:
    check("STRUCT type_planete : valeurs ∈ {tellurique, géante gazeuse, géante de glace}",
          set(_vals("type_planete")) <= {"tellurique", "géante gazeuse", "géante de glace"})
if "climat_koppen_localite" in L.LECTEUR.tables:
    check("STRUCT climat_koppen_localite : valeurs ∈ types de climat de Köppen (closed-set)",
          set(_vals("climat_koppen_localite")) <= {
              "climat équatorial", "climat tropical", "climat de mousson tropical", "climat océanique",
              "climat méditerranéen avec été chaud", "climat subtropical humide", "climat continental humide",
              "climat tropical de savane", "climat continental", "climat méditerranéen", "climat désertique",
              "climat supra-méditerranéen", "climat de tundra", "toundra", "climat semi-aride",
              "climat subarctique", "climat tempéré"})
if "continent_chaine_montagne" in L.LECTEUR.tables:
    check("STRUCT continent_chaine_montagne : valeurs ∈ 7 continents",
          set(_vals("continent_chaine_montagne")) <= _CONTINENTS)
if "continent_lac" in L.LECTEUR.tables:
    check("STRUCT continent_lac : valeurs ∈ 7 continents",
          set(_vals("continent_lac")) <= _CONTINENTS)
if "continent_peninsule" in L.LECTEUR.tables:
    check("STRUCT continent_peninsule : valeurs ∈ 7 continents",
          set(_vals("continent_peninsule")) <= _CONTINENTS)
if "continent_riviere" in L.LECTEUR.tables:
    check("STRUCT continent_riviere : valeurs ∈ 7 continents",
          set(_vals("continent_riviere")) <= _CONTINENTS)
if "continent_archipel" in L.LECTEUR.tables:
    check("STRUCT continent_archipel : valeurs ∈ 7 continents",
          set(_vals("continent_archipel")) <= _CONTINENTS)
if "continent_glacier" in L.LECTEUR.tables:
    check("STRUCT continent_glacier : valeurs ∈ 7 continents",
          set(_vals("continent_glacier")) <= _CONTINENTS)
if "continent_cap" in L.LECTEUR.tables:
    check("STRUCT continent_cap : valeurs ∈ 7 continents",
          set(_vals("continent_cap")) <= _CONTINENTS)
if "continent_plateau" in L.LECTEUR.tables:
    check("STRUCT continent_plateau : valeurs ∈ 7 continents",
          set(_vals("continent_plateau")) <= _CONTINENTS)
if "continent_vallee" in L.LECTEUR.tables:
    check("STRUCT continent_vallee : valeurs ∈ 7 continents",
          set(_vals("continent_vallee")) <= _CONTINENTS)
if "continent_foret" in L.LECTEUR.tables:
    check("STRUCT continent_foret : valeurs ∈ 7 continents",
          set(_vals("continent_foret")) <= _CONTINENTS)
if "continent_baie" in L.LECTEUR.tables:
    check("STRUCT continent_baie : valeurs ∈ 7 continents",
          set(_vals("continent_baie")) <= _CONTINENTS)
if "continent_chute_eau" in L.LECTEUR.tables:
    check("STRUCT continent_chute_eau : valeurs ∈ 7 continents",
          set(_vals("continent_chute_eau")) <= _CONTINENTS)
if "continent_grotte" in L.LECTEUR.tables:
    check("STRUCT continent_grotte : valeurs ∈ 7 continents",
          set(_vals("continent_grotte")) <= _CONTINENTS)
if "continent_col" in L.LECTEUR.tables:
    check("STRUCT continent_col : valeurs ∈ 7 continents",
          set(_vals("continent_col")) <= _CONTINENTS)
if "ocean_mer" in L.LECTEUR.tables:
    check("STRUCT ocean_mer : valeurs ∈ 5 océans",
          set(_vals("ocean_mer")) <=
          {"océan Atlantique", "océan Pacifique", "océan Indien", "océan Arctique", "océan Austral"})
if "type_spectral_etoile" in L.LECTEUR.tables:
    import re as _re_spec
    _SPEC = _re_spec.compile(r'^(sd|esd|d|g|c|w|k|h|m)*[OBAFGKMLTYWCSRND]')
    check("STRUCT type_spectral_etoile : toutes valeurs ∈ grammaire spectrale (≤40 car.)",
          all(_SPEC.match(v) and len(v) <= 40 for v in _vals("type_spectral_etoile")))
if "astre_du_relief" in L.LECTEUR.tables:
    _CORPS_REELS = {"Mercure", "Vénus", "Terre", "Mars", "Jupiter", "Saturne", "Uranus", "Neptune",
        "Lune", "Pluton", "Charon", "Phobos", "Déimos", "Io", "Europe", "Ganymède", "Callisto", "Amalthée",
        "Titan", "Rhéa", "Dioné", "Japet", "Encelade", "Téthys", "Mimas", "Phœbé", "Janus", "Épiméthée",
        "Hypérion", "Ariel", "Miranda", "Umbriel", "Obéron", "Titania", "Puck", "Triton", "Protée",
        "(1) Cérès", "(4) Vesta", "(433) Éros", "(21) Lutèce", "(951) Gaspra", "(243) Ida", "(2867) Šteins",
        "(253) Mathilde", "(25143) Itokawa", "(65803) Didymos", "(162173) Ryugu", "Dactyle",
        "67P/Tchourioumov-Guerassimenko"}
    check("STRUCT astre_du_relief : valeurs ∈ corps réels (anti-fiction)",
          set(_vals("astre_du_relief")) <= _CORPS_REELS)
if "galaxie_morpho" in L.LECTEUR.tables:
    import re as _re_hub
    _HUB = _re_hub.compile(r'^(cD|BCD|dSph|d?E\d?|d?(S0|SB0|SA0|SAB0)(-a|/a)?|'
                           r'd?S(AB|A|B)?(\((rs|r|s)\))?[abcdm]{0,3}|d?I(AB|A|B)?m?|Irr|Sm|Im|d[GI]|E[-/]S0)$')
    check("STRUCT galaxie_morpho : valeurs ∈ grammaire Hubble/de Vaucouleurs",
          all(_HUB.match(v) and "..." not in v for v in _vals("galaxie_morpho")))
if "constellation_exoplanete" in L.LECTEUR.tables:
    check("STRUCT constellation_exoplanete : <=88 constellations distinctes (ensemble fermé IAU)",
          len(set(_vals("constellation_exoplanete"))) <= 88)
    check("STRUCT constellation_exoplanete : noms capitalisés sans chiffre",
          all(v[:1].isupper() and not any(c.isdigit() for c in v) for v in _vals("constellation_exoplanete")))
for _ct in ("constellation_galaxie", "constellation_nebuleuse", "constellation_amas", "constellation_quasar"):
    if _ct in L.LECTEUR.tables:
        check(f"STRUCT {_ct} : <=88 constellations distinctes (ensemble fermé IAU)",
              len(set(_vals(_ct))) <= 88)
        check(f"STRUCT {_ct} : noms capitalisés sans chiffre",
              all(v[:1].isupper() and not any(c.isdigit() for c in v) for v in _vals(_ct)))
if "pays_subdivision" in L.LECTEUR.tables:
    _vp = _vals("pays_subdivision")
    check("STRUCT pays_subdivision : valeurs = pays plausibles (≥1 majuscule, sans chiffre, >=3 car.)",
          all(any(c.isupper() for c in v) and not any(c.isdigit() for c in v) and len(v) >= 3 for v in _vp))
    check("STRUCT pays_subdivision : <=260 pays distincts (ensemble borné)", len(set(_vp)) <= 260)
# NB : une subdivision réelle peut avoir un label FR en minuscules (« district nord », « division occidentale »)
# -> sanité = a une lettre + ≥2 car. (la garantie FAUX=0 vient de la contrainte SPARQL valeur=subdivision niveau1).
if "subdivision_lac" in L.LECTEUR.tables:
    _vsl = _vals("subdivision_lac")
    check("STRUCT subdivision_lac : valeurs = subdivisions plausibles (lettre, >=2 car.)",
          all(any(c.isalpha() for c in v) and len(v) >= 2 for v in _vsl))
if "subdivision_montagne" in L.LECTEUR.tables:
    _vsm = _vals("subdivision_montagne")
    check("STRUCT subdivision_montagne : valeurs = subdivisions plausibles (lettre, >=2 car.)",
          all(any(c.isalpha() for c in v) and len(v) >= 2 for v in _vsm))
if "subdivision_riviere" in L.LECTEUR.tables:
    _vsr = _vals("subdivision_riviere")
    check("STRUCT subdivision_riviere : valeurs = subdivisions plausibles (lettre, >=2 car.)",
          all(any(c.isalpha() for c in v) and len(v) >= 2 for v in _vsr))
if "subdivision_ile" in L.LECTEUR.tables:
    _vsi = _vals("subdivision_ile")
    check("STRUCT subdivision_ile : valeurs = subdivisions plausibles (lettre, >=2 car.)",
          all(any(c.isalpha() for c in v) and len(v) >= 2 for v in _vsi))
for _sdrel in ("subdivision_volcan", "subdivision_glacier", "subdivision_foret", "subdivision_chute_eau",
               "subdivision_col", "subdivision_grotte", "subdivision_baie", "subdivision_peninsule",
               "subdivision_cap", "subdivision_plage", "subdivision_desert", "subdivision_plateau",
               "subdivision_vallee", "subdivision_canyon",
               "subdivision_source", "subdivision_recif", "subdivision_marecage",
               "subdivision_delta", "subdivision_colline",
               "subdivision_phare", "subdivision_chateau", "subdivision_monument", "subdivision_monastere",
               "subdivision_eglise", "subdivision_musee", "subdivision_parc_national",
               "subdivision_canal", "subdivision_mine", "subdivision_site_archeo", "subdivision_reservoir",
               "subdivision_observatoire", "subdivision_hotel", "subdivision_stade", "subdivision_cimetiere",
               "subdivision_theatre", "subdivision_palais", "subdivision_tour",
               "subdivision_mosquee", "subdivision_temple", "subdivision_cathedrale", "subdivision_fortification",
               "subdivision_bibliotheque", "subdivision_universite", "subdivision_hopital", "subdivision_prison",
               "subdivision_gratte_ciel", "subdivision_quartier", "subdivision_rue", "subdivision_sculpture",
               "subdivision_reserve_naturelle", "subdivision_barrage", "subdivision_place", "subdivision_port",
               "subdivision_parc_attraction"):
    if _sdrel in L.LECTEUR.tables:
        _vsd = _vals(_sdrel)
        check("STRUCT %s : valeurs = subdivisions plausibles (lettre, >=2 car.)" % _sdrel,
              all(any(c.isalpha() for c in v) and len(v) >= 2 for v in _vsd))
for _perel in ("plan_eau_port", "plan_eau_ile", "plan_eau_plage", "plan_eau_peninsule", "plan_eau_cap",
               "plan_eau_barrage", "plan_eau_phare"):
    if _perel in L.LECTEUR.tables:
        _vpe = _vals(_perel)
        check("STRUCT %s : valeurs = plans d'eau plausibles (lettre, >=2 car.)" % _perel,
              all(any(c.isalpha() for c in v) and len(v) >= 2 for v in _vpe))
for _aprel in ("ville_sur_ile", "montagne_chaine", "ile_archipel", "col_chaine", "glacier_chaine",
               "exutoire_lac", "bassin_lac", "point_culminant_massif", "planete_parente_lune",
               "capitale_subdivision", "volcan_chaine", "volcan_sur_ile",
               "pays_point_bas", "phare_sur_ile", "montagne_sur_ile",
               "gestionnaire_aire_protegee", "lac_sur_ile", "barrage_reservoir", "subdivision_langue_off"):
    if _aprel in L.LECTEUR.tables:
        _vap = _vals(_aprel)
        check("STRUCT %s : valeurs = objets géographiques plausibles (lettre, >=2 car.)" % _aprel,
              all(any(c.isalpha() for c in v) and len(v) >= 2 for v in _vap))
if "methode_decouverte_exoplanete" in L.LECTEUR.tables:
    _METHODES_EXO = {"méthode des vitesses radiales", "méthode des transits", "microlentille gravitationnelle",
                     "imagerie directe", "astrométrie", "variation du moment de transit", "chronométrage",
                     "variation de la durée de transit", "disque circumstellaire", "perturbation orbitale"}
    check("STRUCT methode_decouverte_exoplanete : valeurs ∈ méthodes de détection connues (closed-set)",
          set(_vals("methode_decouverte_exoplanete")) <= _METHODES_EXO)
if "iso_subdivision" in L.LECTEUR.tables:
    import re as _re_iso
    _RX_ISO = _re_iso.compile(r"^[A-Z]{2}-[A-Z0-9]{1,3}$")
    check("STRUCT iso_subdivision : valeurs = codes ISO 3166-2 (^[A-Z]{2}-[A-Z0-9]{1,3}$)",
          all(_RX_ISO.match(v) for v in _vals("iso_subdivision")))
if "pays_code_vehicule" in L.LECTEUR.tables:
    import re as _re_veh
    _RX_VEH = _re_veh.compile(r"^[A-Z]{1,3}$")
    check("STRUCT pays_code_vehicule : valeurs = codes distinctifs véhicule (^[A-Z]{1,3}$)",
          all(_RX_VEH.match(v) for v in _vals("pays_code_vehicule")))
if "fips_subdivision" in L.LECTEUR.tables:
    import re as _re_fips
    _RX_FIPS = _re_fips.compile(r"^[A-Z]{2}[A-Z0-9]{1,4}$")
    check("STRUCT fips_subdivision : valeurs = codes FIPS 10-4 (^[A-Z]{2}[A-Z0-9]{1,4}$)",
          all(_RX_FIPS.match(v) for v in _vals("fips_subdivision")))
if "nuts_subdivision" in L.LECTEUR.tables:
    import re as _re_nuts
    _RX_NUTS = _re_nuts.compile(r"^[A-Z]{2}[0-9A-Z]{1,4}$")
    check("STRUCT nuts_subdivision : valeurs = codes NUTS (^[A-Z]{2}[0-9A-Z]{1,4}$)",
          all(_RX_NUTS.match(v) for v in _vals("nuts_subdivision")))
if "statut_patrimonial_monument" in L.LECTEUR.tables:
    check("STRUCT statut_patrimonial_monument : valeurs = statuts patrimoniaux plausibles (lettre, >=3 car.)",
          all(any(c.isalpha() for c in v) and len(v) >= 3 for v in _vals("statut_patrimonial_monument")))
if "categorie_uicn_aire_protegee" in L.LECTEUR.tables:
    _CATS_UICN = {"catégorie Ia : Réserve naturelle intégrale", "catégorie Ib : Zone de nature sauvage",
                  "catégorie II : Parc national", "catégorie III : Monument ou élément naturel",
                  "catégorie IV : Aire de gestion des habitats ou des espèces",
                  "catégorie V : Paysage terrestre ou marin protégé",
                  "catégorie VI : Aire protégée avec utilisation durable des ressources naturelles"}
    check("STRUCT categorie_uicn_aire_protegee : valeurs ∈ catégories UICN Ia-VI (closed-set)",
          set(_vals("categorie_uicn_aire_protegee")) <= _CATS_UICN)
if "famille_instrument" in L.LECTEUR.tables:
    check("STRUCT famille_instrument : valeurs ∈ 5 familles",
          set(_vals("famille_instrument")) <= {"cordes", "bois", "cuivres", "percussions", "claviers"})
if "famille_langue" in L.LECTEUR.tables:
    check("STRUCT famille_langue : valeurs ∈ familles linguistiques établies",
          set(_vals("famille_langue")) <= {"romane", "germanique", "slave", "celtique", "hellénique",
                                           "indo-aryenne", "iranienne", "baltique", "sémitique",
                                           "turcique", "sino-tibétaine", "ouralienne", "dravidienne",
                                           "austronésienne"})
if "joueurs_par_equipe" in L.LECTEUR.tables:
    check("STRUCT joueurs_par_equipe : entiers 1..20",
          all(c.isdigit() and 1 <= int(c) <= 20 for c in _vals("joueurs_par_equipe")))
if "famille_chimique" in L.LECTEUR.tables:
    check("STRUCT famille_chimique : valeurs ∈ 4 groupes nommés",
          set(_vals("famille_chimique")) <= {"gaz noble", "halogène", "métal alcalin",
                                             "métal alcalino-terreux"})
if "equivalent_romain" in L.LECTEUR.tables:
    check("STRUCT equivalent_romain : valeurs non triviales (>=3 car.)",
          all(len(c.strip()) >= 3 for c in _vals("equivalent_romain")))
if "auteur_oeuvre" in L.LECTEUR.tables:
    check("STRUCT auteur_oeuvre : noms d'auteur non triviaux (>=4 car., une majuscule)",
          all(len(c.strip()) >= 4 and any(x.isupper() for x in c) for c in _vals("auteur_oeuvre")))
if "peintre_oeuvre" in L.LECTEUR.tables:
    check("STRUCT peintre_oeuvre : noms de peintre non triviaux (>=4 car., une majuscule)",
          all(len(c.strip()) >= 4 and any(x.isupper() for x in c) for c in _vals("peintre_oeuvre")))
if "formule_chimique" in L.LECTEUR.tables:
    import re as _re
    check("STRUCT formule_chimique : commence par une MAJ, lettres+chiffres uniquement",
          all(c[0].isupper() and _re.fullmatch(r"[A-Za-z0-9()]+", c) for c in _vals("formule_chimique")))
if "auteur_decouverte" in L.LECTEUR.tables:
    check("STRUCT auteur_decouverte : noms non triviaux (>=4 car., une majuscule)",
          all(len(c.strip()) >= 4 and any(x.isupper() for x in c) for c in _vals("auteur_decouverte")))
if "texte_sacre" in L.LECTEUR.tables:
    check("STRUCT texte_sacre : valeurs non triviales (>=3 car.)",
          all(len(c.strip()) >= 3 for c in _vals("texte_sacre")))
if "lieu_culte" in L.LECTEUR.tables:
    check("STRUCT lieu_culte : valeurs ∈ lieux de culte connus",
          set(_vals("lieu_culte")) <= {"église", "temple", "mosquée", "synagogue", "gurdwara",
                                       "temple du feu", "pagode"})
if "symbole_monnaie" in L.LECTEUR.tables:
    check("STRUCT symbole_monnaie : symboles courts (1-3 car.)",
          all(1 <= len(c) <= 3 for c in _vals("symbole_monnaie")))
for _rel in ("compositeur_oeuvre", "realisateur_film", "pays_monument", "ville_monument"):
    if _rel in L.LECTEUR.tables:
        check(f"STRUCT {_rel} : valeurs non triviales (>=3 car., une majuscule)",
              all(len(c.strip()) >= 3 and any(x.isupper() for x in c) for c in _vals(_rel)))
if "fete_nationale" in L.LECTEUR.tables:
    _MOIS_FR = ("janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août",
                "septembre", "octobre", "novembre", "décembre")
    check("STRUCT fete_nationale : date « jour mois » avec un mois FR valide",
          all(any(m in c for m in _MOIS_FR) for c in _vals("fete_nationale")))
if "cri_animal" in L.LECTEUR.tables:
    check("STRUCT cri_animal : noms de cri non triviaux (>=4 car.)",
          all(len(c.strip()) >= 4 for c in _vals("cri_animal")))
if "objet_etude" in L.LECTEUR.tables:
    check("STRUCT objet_etude : valeurs non triviales (>=3 car.)",
          all(len(c.strip()) >= 3 for c in _vals("objet_etude")))
if "pantheon_dieu" in L.LECTEUR.tables:
    check("STRUCT pantheon_dieu : valeurs ∈ 5 panthéons",
          set(_vals("pantheon_dieu")) <= {"grec", "romain", "égyptien", "nordique", "hindou"})
if "langage_extension" in L.LECTEUR.tables:
    check("STRUCT langage_extension : noms de langage non triviaux (>=1 car., une majuscule)",
          all(len(c.strip()) >= 1 and any(x.isupper() for x in c) for c in _vals("langage_extension")))
if "type_fichier" in L.LECTEUR.tables:
    check("STRUCT type_fichier : catégories connues",
          set(_vals("type_fichier")) <= {"image", "audio", "vidéo", "document", "texte", "tableur",
                                         "présentation", "archive", "page web", "feuille de style",
                                         "données", "données tabulaires"})
if "nom_vitamine" in L.LECTEUR.tables:
    check("STRUCT nom_vitamine : noms chimiques non triviaux (>=5 car.)",
          all(len(c.strip()) >= 5 for c in _vals("nom_vitamine")))
if "code_hex_couleur" in L.LECTEUR.tables:
    import re as _re2
    check("STRUCT code_hex_couleur : format #RRGGBB hexadécimal",
          all(_re2.fullmatch(r"#[0-9A-F]{6}", c) for c in _vals("code_hex_couleur")))
if "element_zodiaque" in L.LECTEUR.tables:
    check("STRUCT element_zodiaque : valeurs ∈ 4 éléments, 12 signes",
          set(_vals("element_zodiaque")) <= {"feu", "terre", "air", "eau"}
          and len(L.LECTEUR.tables["element_zodiaque"]) == 12)
if "regime_alimentaire" in L.LECTEUR.tables:
    check("STRUCT regime_alimentaire : valeurs ∈ {carnivore, herbivore, omnivore, insectivore}",
          set(_vals("regime_alimentaire")) <= {"carnivore", "herbivore", "omnivore", "insectivore"})  # T1: +insectivore (présent dans la donnée, correct)
if "plus_grande_lune" in L.LECTEUR.tables:
    check("STRUCT plus_grande_lune : noms de lune capitalisés (>=3 car.)",
          all(len(c) >= 3 and c[0].isupper() for c in _vals("plus_grande_lune")))
if "couleur_flamme" in L.LECTEUR.tables:
    check("STRUCT couleur_flamme : couleurs non triviales (>=3 car.)",
          all(len(c.strip()) >= 3 for c in _vals("couleur_flamme")))
if "signification_sigle" in L.LECTEUR.tables:
    check("STRUCT signification_sigle : développements non triviaux (>=4 car., un espace ou majuscule)",
          all(len(c.strip()) >= 4 for c in _vals("signification_sigle")))
if "valeur_constante" in L.LECTEUR.tables:
    import re as _re3
    check("STRUCT valeur_constante : nombres décimaux",
          all(_re3.fullmatch(r"-?\d+\.\d+", c) for c in _vals("valeur_constante")))
if "fonction_organe" in L.LECTEUR.tables:
    check("STRUCT fonction_organe : fonctions non triviales (>=5 car.)",
          all(len(c.strip()) >= 5 for c in _vals("fonction_organe")))
for _rel in ("objet_phobie", "petit_animal", "composition_alliage"):
    if _rel in L.LECTEUR.tables:
        check(f"STRUCT {_rel} : valeurs non triviales (>=3 car.)",
              all(len(c.strip()) >= 3 for c in _vals(_rel)))
if "pays_ville" in L.LECTEUR.tables:
    check("STRUCT pays_ville : noms de pays capitalisés (>=3 car.)",
          all(len(c) >= 3 and c[0].isupper() for c in _vals("pays_ville")))
    check("STRUCT pays_ville : valeurs ⊆ pays plausibles (pas de chiffre, capitalisé)",
          all(c[0].isupper() and not any(ch.isdigit() for ch in c) for c in _vals("pays_ville")))
    # FAUX=0 : les libellés homonymes multi-pays doivent être HORS (rejetés par fonctionnel).
    check("FAUX=0 pays_ville : homonymes multi-pays -> HORS",
          all(L.cherche("pays_ville", v) is None for v in ("toledo", "valencia", "santiago", "melbourne")))
# « X -> pays » (aéroport / université / lac) — MÊME recette FAUX=0 que villes : valeur ∈ pays.
for _rel in ("pays_aeroport", "pays_universite", "pays_lac", "pays_gare", "pays_musee",
             "pays_stade", "pays_pont", "pays_chateau", "pays_parc_national",
             "pays_ile", "pays_phare", "pays_volcan", "pays_film",
             "pays_journal", "pays_club_foot", "pays_entreprise", "pays_barrage",
             "pays_bibliotheque", "pays_centrale_electrique", "pays_grotte",
             "pays_gratte_ciel", "pays_monastere", "pays_theatre", "pays_hopital",
             "pays_mine", "pays_cathedrale", "pays_mosquee", "pays_cascade",
             "pays_glacier", "pays_canal", "pays_cimetiere", "pays_palais", "pays_prison",
             "pays_temple", "pays_tunnel", "pays_raffinerie", "pays_fontaine", "pays_abbaye",
             "pays_synagogue", "pays_observatoire", "pays_opera", "pays_zoo", "pays_jardin_botanique",
             "pays_fort", "pays_brasserie", "pays_chantier_naval", "pays_marche",
             "pays_gare_routiere", "pays_centrale_nucleaire",
             "pays_col", "pays_metro", "pays_cinema", "pays_centre_commercial",
             "pays_site_archeologique", "pays_parc_attraction", "pays_casino",
             "pays_moulin", "pays_hotel",
             "pays_aqueduc", "pays_place", "pays_reservoir", "pays_tour", "pays_mairie",
             "pays_reserve_naturelle", "pays_monument_historique", "pays_statue", "pays_ecluse",
             "pays_quartier", "pays_gare_metro", "pays_peninsule", "pays_desert",
             "pays_eglise", "pays_chapelle", "pays_sculpture", "pays_puits", "pays_etang",
             "pays_riviere", "pays_foret", "pays_plage", "pays_source", "pays_rue", "pays_place_forte",
             "pays_archipel", "pays_baie", "pays_cap", "pays_massif", "pays_route",
             "pays_ecole", "pays_groupe_musique", "pays_serie_tv", "pays_parti_politique",
             "pays_localite", "pays_montagne", "pays_colline", "pays_vallee",
             "pays_plateau", "pays_marais", "pays_source_thermale",
             "pays_plaine", "pays_detroit", "pays_fjord", "pays_estuaire",
             "pays_lagune", "pays_dune",
             "pays_canyon", "pays_anse", "pays_banc", "pays_crique",
             "pays_promontoire", "pays_recif",
             "pays_chenal", "pays_bras_de_mer", "pays_torrent",
             "pays_zone_humide", "pays_tourbiere", "pays_prairie", "pays_cratere",
             "pays_aire_protegee", "pays_geotope", "pays_reserve_biosphere",
             "pays_carriere", "pays_viaduc",
             "pays_affleurement", "pays_escarpement", "pays_faille", "pays_karst", "pays_doline",
             "pays_crete",
             "pays_bassin_sedimentaire"):
    if _rel in L.LECTEUR.tables:
        _v = _vals(_rel)
        # « capitalisé » = contient une MAJUSCULE (nom propre), pas forcément en tête : les noms d'États français
        # commencent par une minuscule (« république de Chine », « protectorat français au Maroc ») = légitimes.
        check(f"STRUCT {_rel} : valeurs = pays plausibles (≥1 majuscule, sans chiffre, >=3 car.)",
              all(len(c) >= 3 and any(ch.isupper() for ch in c) and not any(ch.isdigit() for ch in c) for c in _v))
        # cap = ensemble borné « pays » (sanité anti-explosion homonymes) ; 260 couvre pays actuels + États
        # historiques (ROC, Sud-Vietnam, URSS, protectorats…) sans laisser passer une explosion (villes captées…).
        check(f"STRUCT {_rel} : <=260 pays distincts (ensemble borné)", len(set(_v)) <= 260)
# NATIONALITÉ (P27) : la valeur n'est PAS un « pays actuel » — la citoyenneté couvre les polities HISTORIQUES
# aux libellés Wikidata fidèles : minuscules légitimes en français (« califat abbasside », « royaume séleucide »),
# désambiguïsation par années (« royaume de Norvège (872-1397) »). Le check « pays plausibles » (majuscule
# requise, zéro chiffre, ≤260) était une SPEC FAUSSE pour cette relation — vécu 2026-07-08 : 12 valeurs
# légitimes le cassaient. Invariants VRAIS : ≥3 car., chiffres UNIQUEMENT dans une parenthèse d'années, pas
# d'explosion (≤2000 distinctes : ~1244 aujourd'hui). NB : les valeurs JOINTES « X et Y » restantes dans le
# dataset livré sont mises en QUARANTAINE au lookup (join tronqué par fréquence de corpus = faux par omission).
if "nationalite_personne" in L.LECTEUR.tables:
    import re as _re_nat
    _v = _vals("nationalite_personne")
    _sans_annees = [_re_nat.sub(r"\(\d{1,4}[–-]\d{1,4}\)", "", c) for c in set(_v)]
    check("STRUCT nationalite_personne : >=3 car., chiffres seulement en parenthèse d'années",
          all(len(c) >= 3 for c in _v) and not any(any(ch.isdigit() for ch in c) for c in _sans_annees))
    check("STRUCT nationalite_personne : <=2000 polities distinctes (anti-explosion)", len(set(_v)) <= 2000)

# VEINES GÉNÉRALISÉES « X -> valeur d'un ENSEMBLE FERMÉ » (scout généralisé) : valeur non vide, ensemble borné.
for _rel, _maxd in (("genre_film", 600), ("style_batiment", 600), ("langue_oeuvre", 200), ("tonalite_oeuvre", 64),
                    ("moteur_jeu_video", 2000), ("systeme_exploitation_logiciel", 400),
                    ("genre_jeu_video", 600), ("materiau_objet_art", 3000),
                    ("mouvement_peinture", 700), ("forme_juridique_entreprise", 500),
                    ("genre_album", 1500), ("genre_groupe_musique", 1500),
                    ("mode_distribution_jeu", 200), ("ordre_religieux_monastere", 400),
                    ("culture_artefact", 400), ("langue_film", 300),
                    ("lieu_action_oeuvre", 3000), ("genre_emission_tv", 600),
                    ("couleur_yeux", 60), ("usage_batiment", 1500)):
    if _rel in L.LECTEUR.tables:
        _v = _vals(_rel)
        check(f"STRUCT {_rel} : valeurs non vides, >=2 car.", all(isinstance(c, str) and len(c) >= 2 for c in _v))
        check(f"STRUCT {_rel} : <= {_maxd} valeurs distinctes (ensemble fermé)", len(set(_v)) <= _maxd)
# PERSONNE -> LIEU DE NAISSANCE/DÉCÈS (P19/P20) : valeur = LIEU plausible (PAS un ensemble fermé borné → pas de borne
# ≤N) + ancres vérité-terrain (Wikidata, vérifiées). FAUX=0 : homonymes multi-lieu -> HORS via `fonctionnel`.
for _rel in ("lieu_naissance", "lieu_deces", "lieu_inhumation", "lieu_travail", "division_admin_ville",
             "bassin_fleuve", "chaine_montagne", "embouchure_fleuve", "origine_fleuve"):
    if _rel in L.LECTEUR.tables:
        _v = _vals(_rel)
        # un VRAI lieu peut commencer par un chiffre (« 100 Mile House », « 10e arrondissement de Paris ») -> on
        # n'exige PAS « capitalisé/sans chiffre ». FAUX=0 vient du filtre `_est_lieu_plausible` à l'ingestion (rejette
        # dates/années nues). Sanité ici = contient au moins une lettre + pas une date résiduelle : la valeur ENTIÈRE
        # a la FORME d'une date (« 12 mai 1994 », « mai 1994 », année nue) — un token de mois DANS un toponyme est
        # légitime (« Chiang Mai » cassait l'ancien détecteur par tokens, vécu 2026-07-08).
        import re as _re_dat
        _DATE_RESIDUELLE = _re_dat.compile(
            r"^\s*(?:\d{1,2}(?:er)?\s+)?(?:janvier|f[ée]vrier|mars|avril|mai|juin|juillet|ao[ûu]t"
            r"|septembre|octobre|novembre|d[ée]cembre)(?:\s+\d{1,4})?\s*$|^\s*\d+\s*$", _re_dat.I)
        check(f"STRUCT {_rel} : valeurs = lieux (>=2 car., contient une lettre)",
              all(len(c) >= 2 and any(ch.isalpha() for ch in c) for c in _v))
        check(f"STRUCT {_rel} : 0 date/année résiduelle (FAUX=0)",
              not any(_DATE_RESIDUELLE.match(c) for c in _v))
# NB : ancres = personnes au label FR NON ambigu (« charles de gaulle » écarté : homonyme porte-avions/aéroport/
# petit-fils -> multi-valeur -> HORS = comportement FAUX=0 CORRECT, mais inutilisable comme ancre).
if "lieu_naissance" in L.LECTEUR.tables:
    check("ANCRES lieu_naissance : personnes connues -> bon lieu",
          L.cherche("lieu_naissance", "napoléon ier") and
          L.cherche("lieu_naissance", "napoléon ier").valeur == "Ajaccio" and
          L.cherche("lieu_naissance", "albert einstein").valeur == "Ulm" and
          L.cherche("lieu_naissance", "louis pasteur").valeur == "Dole" and
          L.cherche("lieu_naissance", "marie curie").valeur == "Varsovie" and
          L.cherche("lieu_naissance", "wolfgang amadeus mozart").valeur == "Salzbourg" and
          L.cherche("lieu_naissance", "emmanuel macron").valeur == "Amiens")
if "lieu_deces" in L.LECTEUR.tables:
    check("ANCRES lieu_deces : personnes connues -> bon lieu",
          L.cherche("lieu_deces", "napoléon ier") and
          L.cherche("lieu_deces", "napoléon ier").valeur == "Longwood House" and
          L.cherche("lieu_deces", "albert einstein").valeur == "Princeton" and
          L.cherche("lieu_deces", "wolfgang amadeus mozart").valeur == "Vienne" and
          L.cherche("lieu_deces", "marie curie").valeur == "sanatorium de Sancellemoz")
# BATCH 6 — ancres vérité-terrain des veines « X -> LIEU » (vérifiées contre le lecteur ; lieu_travail &
# division_admin_ville = SANS ancre car libellés homonymes -> sanité structurelle seule, FAUX=0 via filtre+fonctionnel).
if "lieu_inhumation" in L.LECTEUR.tables:
    check("ANCRES lieu_inhumation : personnes connues -> bon lieu",
          L.cherche("lieu_inhumation", "marie curie") and
          L.cherche("lieu_inhumation", "marie curie").valeur == "Panthéon" and
          L.cherche("lieu_inhumation", "wolfgang amadeus mozart").valeur == "cimetière Saint-Marx")
if "embouchure_fleuve" in L.LECTEUR.tables:
    check("ANCRES embouchure_fleuve : fleuves connus -> bon exutoire",
          L.cherche("embouchure_fleuve", "seine") and
          L.cherche("embouchure_fleuve", "seine").valeur == "Manche" and
          L.cherche("embouchure_fleuve", "amazone").valeur == "océan Atlantique")
if "bassin_fleuve" in L.LECTEUR.tables:
    check("ANCRES bassin_fleuve : fleuves connus -> bon bassin",
          L.cherche("bassin_fleuve", "seine") and
          L.cherche("bassin_fleuve", "seine").valeur == "bassin de la Seine" and
          L.cherche("bassin_fleuve", "amazone").valeur == "bassin amazonien")
if "chaine_montagne" in L.LECTEUR.tables:
    check("ANCRES chaine_montagne : sommets connus -> bonne chaîne",
          L.cherche("chaine_montagne", "cervin") and
          L.cherche("chaine_montagne", "cervin").valeur == "Alpes pennines" and
          L.cherche("chaine_montagne", "grandes jorasses").valeur == "massif du Mont-Blanc")
if "origine_fleuve" in L.LECTEUR.tables:
    check("ANCRES origine_fleuve : Rhône -> glacier du Rhône",
          L.cherche("origine_fleuve", "rhône") and
          L.cherche("origine_fleuve", "rhône").valeur == "glacier du Rhône")
# PERSONNE -> NATIONALITÉ (P27) : ancres personnes connues + rejet des multi-nationalités (FAUX=0).
if "nationalite_personne" in L.LECTEUR.tables:
    check("ANCRES nationalite_personne : personnes connues -> bon pays",
          L.cherche("nationalite_personne", "emmanuel macron") and
          L.cherche("nationalite_personne", "emmanuel macron").valeur == "France" and
          L.cherche("nationalite_personne", "cristiano ronaldo").valeur == "Portugal" and
          L.cherche("nationalite_personne", "pelé").valeur == "Brésil" and
          L.cherche("nationalite_personne", "nelson mandela").valeur == "Afrique du Sud")
    check("FAUX=0 nationalite_personne : multi-nationalités/historiques -> HORS",
          L.cherche("nationalite_personne", "lionel messi") is None and
          L.cherche("nationalite_personne", "albert einstein") is None)
# ATHLÈTE -> SPORT (P641) : valeur ∈ ENSEMBLE FERMÉ des sports (~872 distincts), ancres connues, sans chiffre.
if "sport_athlete" in L.LECTEUR.tables:
    _vs = _vals("sport_athlete")
    check("STRUCT sport_athlete : <=2000 sports distincts (ensemble fermé)", len(set(_vs)) <= 2000)
    # NB : pas de contrainte « sans chiffre » — des sports en contiennent légitimement (100 mètres, Formule 1,
    # rugby à 7, Twenty20, DotA 2…). La sûreté FAUX=0 vient du set fermé + ancres + rejet des multi-sport.
    check("STRUCT sport_athlete : noms de sport non triviaux (>=2 car.)",
          all(len(c.strip()) >= 2 for c in _vs))
    check("ANCRES sport_athlete : athlètes connus -> bon sport",
          L.cherche("sport_athlete", "roger federer") and
          L.cherche("sport_athlete", "roger federer").valeur == "tennis" and
          L.cherche("sport_athlete", "usain bolt").valeur == "athlétisme" and
          L.cherche("sport_athlete", "teddy riner").valeur == "judo" and
          L.cherche("sport_athlete", "kylian mbappé").valeur == "football")
    check("FAUX=0 sport_athlete : polyvalents/homonymes multi-sport -> HORS",
          L.cherche("sport_athlete", "michael jordan") is None and
          L.cherche("sport_athlete", "tom brady") is None)
# ASTRE -> CONSTELLATION : valeur ∈ ensemble fermé des 88 constellations IAU.
if "constellation_astre" in L.LECTEUR.tables:
    _vc = _vals("constellation_astre")
    check("STRUCT constellation_astre : <=88 constellations distinctes (ensemble fermé IAU)",
          len(set(_vc)) <= 88)
    check("STRUCT constellation_astre : noms capitalisés sans chiffre",
          all(c and c[0].isupper() and not any(ch.isdigit() for ch in c) for c in _vc))
    check("ANCRES constellation_astre : étoiles connues",
          L.cherche("constellation_astre", "bételgeuse") and
          L.cherche("constellation_astre", "bételgeuse").valeur == "Orion" and
          L.cherche("constellation_astre", "sirius").valeur == "Grand Chien" and
          L.cherche("constellation_astre", "véga").valeur == "Lyre")
# AÉROPORT -> CODE IATA : code exact = 3 lettres majuscules (définitionnel).
if "code_iata_aeroport" in L.LECTEUR.tables:
    check("STRUCT code_iata_aeroport : tous = 3 lettres majuscules",
          all(len(c) == 3 and c.isalpha() and c.isupper() for c in _vals("code_iata_aeroport")))
    check("ANCRES code_iata_aeroport : CDG/LHR connus",
          L.cherche("code_iata_aeroport", "aéroport paris-charles-de-gaulle") and
          L.cherche("code_iata_aeroport", "aéroport paris-charles-de-gaulle").valeur == "CDG" and
          L.cherche("code_iata_aeroport", "aéroport de londres heathrow").valeur == "LHR")
if "code_icao_aeroport" in L.LECTEUR.tables:
    check("STRUCT code_icao_aeroport : tous = 4 lettres majuscules",
          all(len(c) == 4 and c.isalpha() and c.isupper() for c in _vals("code_icao_aeroport")))
    check("ANCRES code_icao_aeroport : LFPG/EGLL connus",
          L.cherche("code_icao_aeroport", "aéroport paris-charles-de-gaulle") and
          L.cherche("code_icao_aeroport", "aéroport paris-charles-de-gaulle").valeur == "LFPG" and
          L.cherche("code_icao_aeroport", "aéroport de londres heathrow").valeur == "EGLL")
# PAYS -> CODES ISO 3166-1 (alpha-2 / alpha-3) + indicatif téléphonique : codes exacts définitionnels, ancres sûres.
# (codes ISO alpha-2/alpha-3 + indicatif déjà validés plus haut via les tables mledoze code_iso_pays /
#  code_iso3_pays / indicatif_telephonique — pas de doublon QLever.)
# LIEU DE CULTE -> RELIGION : valeurs = dénominations religieuses (ensemble large mais propre, pas de junk).
if "religion_lieu_culte" in L.LECTEUR.tables:
    _vr = _vals("religion_lieu_culte")
    check("STRUCT religion_lieu_culte : dénominations sans chiffre, >=3 car.",
          all(len(c) >= 3 and not any(ch.isdigit() for ch in c) for c in _vr))
    check("STRUCT religion_lieu_culte : <=300 dénominations distinctes", len(set(_vr)) <= 300)
if "agent_maladie" in L.LECTEUR.tables:
    check("STRUCT agent_maladie : valeurs ∈ {virus, bactérie, parasite, champignon}",
          set(_vals("agent_maladie")) <= {"virus", "bactérie", "parasite", "champignon"})
if "type_roche" in L.LECTEUR.tables:
    check("STRUCT type_roche : valeurs ∈ {magmatique, sédimentaire, métamorphique}",
          set(_vals("type_roche")) <= {"magmatique", "sédimentaire", "métamorphique"})
if "symbole_math" in L.LECTEUR.tables:
    check("STRUCT symbole_math : symboles courts (1-2 car.), valeurs distinctes",
          all(1 <= len(c) <= 2 for c in _vals("symbole_math"))
          and len(set(_vals("symbole_math"))) == len(_vals("symbole_math")))
if "arbre_fruit" in L.LECTEUR.tables:
    check("STRUCT arbre_fruit : noms d'arbre non triviaux (>=4 car.)",
          all(len(c.strip()) >= 4 for c in _vals("arbre_fruit")))
if "melange_couleur" in L.LECTEUR.tables:
    check("STRUCT melange_couleur : mélanges « X et Y »",
          all(" et " in c for c in _vals("melange_couleur")))
if "mesure_instrument" in L.LECTEUR.tables:
    check("STRUCT mesure_instrument : grandeurs non triviales (>=4 car.)",
          all(len(c.strip()) >= 4 for c in _vals("mesure_instrument")))
if "pays_danse" in L.LECTEUR.tables:
    check("STRUCT pays_danse : noms de pays capitalisés (>=4 car.)",
          all(len(c) >= 4 and c[0].isupper() for c in _vals("pays_danse")))
for _rel in ("auteur_bd", "createur_personnage", "fondateur_religion"):
    if _rel in L.LECTEUR.tables:
        check(f"STRUCT {_rel} : noms non triviaux (>=3 car., une majuscule)",
              all(len(c.strip()) >= 3 and any(x.isupper() for x in c) for c in _vals(_rel)))
if "pays_plat" in L.LECTEUR.tables:
    check("STRUCT pays_plat : noms de pays capitalisés (>=4 car.)",
          all(len(c) >= 4 and c[0].isupper() for c in _vals("pays_plat")))
for _rel in ("bonjour_langue", "merci_langue"):
    if _rel in L.LECTEUR.tables:
        check(f"STRUCT {_rel} : formes non triviales (>=2 car.)",
              all(len(c.strip()) >= 2 for c in _vals(_rel)))
if "inventeur" in L.LECTEUR.tables:
    check("STRUCT inventeur : noms non triviaux (>=4 car., une majuscule)",
          all(len(c.strip()) >= 4 and any(x.isupper() for x in c) for c in _vals("inventeur")))
for _rel in ("domaine_prix", "sens_organe"):
    if _rel in L.LECTEUR.tables:
        check(f"STRUCT {_rel} : valeurs non triviales (>=4 car.)",
              all(len(c.strip()) >= 4 for c in _vals(_rel)))
if "notation_anglaise_note" in L.LECTEUR.tables:
    check("STRUCT notation_anglaise_note : lettres ∈ A..G",
          set(_vals("notation_anglaise_note")) <= set("ABCDEFG"))
for _rel in ("nom_groupe_animal", "partie_corps_vetement"):
    if _rel in L.LECTEUR.tables:
        check(f"STRUCT {_rel} : valeurs non triviales (>=3 car.)",
              all(len(c.strip()) >= 3 for c in _vals(_rel)))
if "pays_genre_musical" in L.LECTEUR.tables:
    check("STRUCT pays_genre_musical : noms de pays capitalisés (>=4 car.)",
          all(len(c) >= 4 and c[0].isupper() for c in _vals("pays_genre_musical")))
if "sens_locution_latine" in L.LECTEUR.tables:
    check("STRUCT sens_locution_latine : traductions non triviales (>=5 car.)",
          all(len(c.strip()) >= 5 for c in _vals("sens_locution_latine")))
if "jour_saint_religion" in L.LECTEUR.tables:
    check("STRUCT jour_saint_religion : mentionne un jour de la semaine",
          all(any(j in c for j in ("lundi","mardi","mercredi","jeudi","vendredi","samedi","dimanche"))
              for c in _vals("jour_saint_religion")))
if "nom_actuel" in L.LECTEUR.tables:
    check("STRUCT nom_actuel : noms de pays capitalisés (>=3 car.)",
          all(len(c) >= 3 and c[0].isupper() for c in _vals("nom_actuel")))
if "subdivision_monnaie" in L.LECTEUR.tables:
    check("STRUCT subdivision_monnaie : noms non triviaux (>=3 car.)",
          all(len(c.strip()) >= 3 for c in _vals("subdivision_monnaie")))
if "type_arbre" in L.LECTEUR.tables:
    check("STRUCT type_arbre : valeurs ∈ {feuillu, conifère}",
          set(_vals("type_arbre")) <= {"feuillu", "conifère"})
if "surnom_roi" in L.LECTEUR.tables:
    check("STRUCT surnom_roi : surnoms non triviaux (>=2 car., une majuscule)",
          all(len(c.strip()) >= 2 and any(x.isupper() for x in c) for c in _vals("surnom_roi")))
if "fonction_dent" in L.LECTEUR.tables:
    check("STRUCT fonction_dent : fonctions non triviales (>=5 car.)",
          all(len(c.strip()) >= 5 for c in _vals("fonction_dent")))
if "raccourci_clavier" in L.LECTEUR.tables:
    check("STRUCT raccourci_clavier : raccourcis contenant une touche modificatrice",
          all(any(m in c for m in ("Ctrl", "Alt", "Maj", "Shift")) for c in _vals("raccourci_clavier")))
if "region_os" in L.LECTEUR.tables:
    check("STRUCT region_os : régions non triviales (>=4 car.)",
          all(len(c.strip()) >= 4 for c in _vals("region_os")))
if "devise_pays" in L.LECTEUR.tables:
    check("STRUCT devise_pays : devises non triviales (>=6 car., une majuscule)",
          all(len(c.strip()) >= 6 and any(x.isupper() for x in c) for c in _vals("devise_pays")))
if "saison_olympique" in L.LECTEUR.tables:
    check("STRUCT saison_olympique : valeurs ∈ {été, hiver}",
          set(_vals("saison_olympique")) <= {"été", "hiver"})
for _rel in ("guerre_bataille", "fonction_personnage"):
    if _rel in L.LECTEUR.tables:
        check(f"STRUCT {_rel} : valeurs non triviales (>=5 car.)",
              all(len(c.strip()) >= 5 for c in _vals(_rel)))
if "couleur_complementaire" in L.LECTEUR.tables:
    check("STRUCT couleur_complementaire : valeurs ∈ 6 couleurs RYB",
          set(_vals("couleur_complementaire")) <= {"rouge", "vert", "bleu", "orange", "jaune", "violet"})
if "origine_creature" in L.LECTEUR.tables:
    check("STRUCT origine_creature : origines non triviales (>=5 car.)",
          all(len(c.strip()) >= 5 for c in _vals("origine_creature")))
if "continent_desert" in L.LECTEUR.tables:
    check("STRUCT continent_desert : valeurs ∈ 7 continents",
          set(_vals("continent_desert")) <= _CONTINENTS)
if "type_astre" in L.LECTEUR.tables:
    check("STRUCT type_astre : valeurs ∈ types astronomiques connus",
          set(_vals("type_astre")) <= {"étoile", "planète", "planète naine", "satellite naturel",
                                       "comète", "astéroïde", "galaxie"})
if "lieu_saint_religion" in L.LECTEUR.tables:
    check("STRUCT lieu_saint_religion : lieux non triviaux (>=5 car., une majuscule)",
          all(len(c.strip()) >= 5 and any(x.isupper() for x in c) for c in _vals("lieu_saint_religion")))
if "duree_note" in L.LECTEUR.tables:
    check("STRUCT duree_note : durées non triviales (>=5 car.)",
          all(len(c.strip()) >= 5 for c in _vals("duree_note")))
if "symbole_ponctuation" in L.LECTEUR.tables:
    check("STRUCT symbole_ponctuation : symboles courts (1 car.)",
          all(len(c) == 1 for c in _vals("symbole_ponctuation")))
if "animal_dieu" in L.LECTEUR.tables:
    check("STRUCT animal_dieu : valeurs non triviales (>=4 car.)",
          all(len(c.strip()) >= 4 for c in _vals("animal_dieu")))
if "oppose_cardinal" in L.LECTEUR.tables:
    check("STRUCT oppose_cardinal : valeurs ∈ 8 directions",
          set(_vals("oppose_cardinal")) <= {"nord","sud","est","ouest","nord-est","sud-ouest",
                                            "nord-ouest","sud-est"})
if "nombre_en_lettres" in L.LECTEUR.tables:
    check("STRUCT nombre_en_lettres : écritures non triviales (>=2 car.)",
          all(len(c.strip()) >= 2 for c in _vals("nombre_en_lettres")))
if "charge_ion" in L.LECTEUR.tables:
    import re as _re4
    check("STRUCT charge_ion : signe + chiffre (±1..3)",
          all(_re4.fullmatch(r"[+-][123]", c) for c in _vals("charge_ion")))
if "ph_substance" in L.LECTEUR.tables:
    check("STRUCT ph_substance : valeurs ∈ {acide, basique, neutre}",
          set(_vals("ph_substance")) <= {"acide", "basique", "neutre"})
if "symbole_grec" in L.LECTEUR.tables:
    check("STRUCT symbole_grec : symboles 1 caractère, distincts",
          all(len(c) == 1 for c in _vals("symbole_grec"))
          and len(set(_vals("symbole_grec"))) == len(_vals("symbole_grec")))
if "periode_revolution_planete" in L.LECTEUR.tables:
    check("STRUCT periode_revolution_planete : mentionne « jours » ou « ans »",
          all(("jour" in c or "an" in c) for c in _vals("periode_revolution_planete")))
if "distance_soleil" in L.LECTEUR.tables:
    check("STRUCT distance_soleil : entiers positifs (millions de km)",
          all(c.isdigit() and int(c) > 0 for c in _vals("distance_soleil")))
if "rang_ocean" in L.LECTEUR.tables:
    check("STRUCT rang_ocean : rangs 1..5 distincts, 5 océans",
          sorted(_vals("rang_ocean")) == ["1", "2", "3", "4", "5"])
if "valeur_piece_echecs" in L.LECTEUR.tables:
    check("STRUCT valeur_piece_echecs : entiers 0..9",
          all(c.isdigit() and 0 <= int(c) <= 9 for c in _vals("valeur_piece_echecs")))
if "deplacement_piece" in L.LECTEUR.tables:
    check("STRUCT deplacement_piece : descriptions non triviales (>=6 car.)",
          all(len(c.strip()) >= 6 for c in _vals("deplacement_piece")))
if "pays_art_martial" in L.LECTEUR.tables:
    check("STRUCT pays_art_martial : noms de pays capitalisés (>=4 car.)",
          all(len(c) >= 4 and c[0].isupper() for c in _vals("pays_art_martial")))
if "ordre_signe_chinois" in L.LECTEUR.tables:
    check("STRUCT ordre_signe_chinois : rangs 1..12 distincts",
          sorted(int(c) for c in _vals("ordre_signe_chinois")) == list(range(1, 13)))
if "ordre_ceinture_judo" in L.LECTEUR.tables:
    check("STRUCT ordre_ceinture_judo : rangs 1..7 distincts",
          sorted(int(c) for c in _vals("ordre_ceinture_judo")) == list(range(1, 8)))
if "ordre_arc_en_ciel" in L.LECTEUR.tables:
    check("STRUCT ordre_arc_en_ciel : rangs 1..7 distincts",
          sorted(int(c) for c in _vals("ordre_arc_en_ciel")) == list(range(1, 8)))
if "bloc_element" in L.LECTEUR.tables:
    check("STRUCT bloc_element : valeurs ∈ {s, p, d, f}",
          set(_vals("bloc_element")) <= {"s", "p", "d", "f"})
if "mesure_angle" in L.LECTEUR.tables:
    check("STRUCT mesure_angle : mesures en degrés (finissent par °)",
          all(c.endswith("°") for c in _vals("mesure_angle")))
if "origine_vent" in L.LECTEUR.tables:
    check("STRUCT origine_vent : origines non triviales (>=5 car.)",
          all(len(c.strip()) >= 5 for c in _vals("origine_vent")))
for _rel in ("sens_prefixe", "sens_suffixe", "ecriture_langue"):
    if _rel in L.LECTEUR.tables:
        check(f"STRUCT {_rel} : valeurs non triviales (>=3 car.)",
              all(len(c.strip()) >= 3 for c in _vals(_rel)))
for _rel in ("pays_marque_auto", "pays_marque_tech", "pays_marque_luxe"):
    if _rel in L.LECTEUR.tables:
        check(f"STRUCT {_rel} : noms de pays capitalisés (>=4 car.)",
              all(len(c) >= 4 and c[0].isupper() for c in _vals(_rel)))
if "couleur_pierre" in L.LECTEUR.tables:
    check("STRUCT couleur_pierre : couleurs non triviales (>=3 car.)",
          all(len(c.strip()) >= 3 for c in _vals("couleur_pierre")))
if "usage_instrument_optique" in L.LECTEUR.tables:
    check("STRUCT usage_instrument_optique : usages non triviaux (>=6 car.)",
          all(len(c.strip()) >= 6 for c in _vals("usage_instrument_optique")))
if "nombre_organe" in L.LECTEUR.tables:
    check("STRUCT nombre_organe : valeurs ∈ {1, 2}",
          set(_vals("nombre_organe")) <= {"1", "2"})
for _rel in ("pays_race_chien", "pays_fromage"):
    if _rel in L.LECTEUR.tables:
        check(f"STRUCT {_rel} : noms de pays capitalisés (>=4 car.)",
              all(len(c) >= 4 and c[0].isupper() for c in _vals(_rel)))
if "couleur_cepage" in L.LECTEUR.tables:
    check("STRUCT couleur_cepage : valeurs ∈ {blanc, rouge}",
          set(_vals("couleur_cepage")) <= {"blanc", "rouge"})
if "alphabet_otan" in L.LECTEUR.tables:
    check("STRUCT alphabet_otan : 26 lettres, mots capitalisés (d et l présents)",
          len(L.LECTEUR.tables["alphabet_otan"]) == 26
          and all(c[0].isupper() for c in _vals("alphabet_otan")))
if "code_morse" in L.LECTEUR.tables:
    check("STRUCT code_morse : 36 caractères, codes en points/tirets uniquement",
          len(L.LECTEUR.tables["code_morse"]) == 36
          and all(set(c) <= {".", "-"} and c for c in _vals("code_morse")))
if "symbole_astro_planete" in L.LECTEUR.tables:
    check("STRUCT symbole_astro_planete : symboles 1 caractère",
          all(len(c) == 1 for c in _vals("symbole_astro_planete")))
if "pays_race_chat" in L.LECTEUR.tables:
    check("STRUCT pays_race_chat : noms de pays capitalisés (>=4 car.)",
          all(len(c) >= 4 and c[0].isupper() for c in _vals("pays_race_chat")))
if "equivalent_metrique" in L.LECTEUR.tables:
    check("STRUCT equivalent_metrique : contient un chiffre et une unité métrique",
          all(any(ch.isdigit() for ch in c) and any(u in c for u in ("m", "g", "L", "h"))
              for c in _vals("equivalent_metrique")))
if "origine_epice" in L.LECTEUR.tables:
    check("STRUCT origine_epice : noms de pays capitalisés (>=4 car.)",
          all(len(c) >= 4 and c[0].isupper() for c in _vals("origine_epice")))
if "nombre_cordes" in L.LECTEUR.tables:
    check("STRUCT nombre_cordes : entiers 3..12",
          all(c.isdigit() and 3 <= int(c) <= 12 for c in _vals("nombre_cordes")))
if "beaufort_description" in L.LECTEUR.tables:
    check("STRUCT beaufort_description : 13 degrés (0..12), appellations non triviales",
          len(L.LECTEUR.tables["beaufort_description"]) == 13
          and all(len(c.strip()) >= 4 for c in _vals("beaufort_description")))
if "banque_centrale" in L.LECTEUR.tables:
    check("STRUCT banque_centrale : noms contenant « Banque » ou « Réserve »",
          all(("Banque" in c or "Réserve" in c) for c in _vals("banque_centrale")))
for _rel in ("carence_vitamine", "hormone_organe"):
    if _rel in L.LECTEUR.tables:
        check(f"STRUCT {_rel} : valeurs non triviales (>=5 car.)",
              all(len(c.strip()) >= 5 for c in _vals(_rel)))
if "ville_jo_ete" in L.LECTEUR.tables:
    check("STRUCT ville_jo_ete : villes capitalisées (>=4 car.)",
          all(len(c) >= 4 and c[0].isupper() for c in _vals("ville_jo_ete")))
for _rel in ("ville_jo_hiver", "pays_dynastie"):
    if _rel in L.LECTEUR.tables:
        check(f"STRUCT {_rel} : valeurs capitalisées (>=4 car.)",
              all(len(c) >= 4 and c[0].isupper() for c in _vals(_rel)))
if "embleme_floral" in L.LECTEUR.tables:
    check("STRUCT embleme_floral : valeurs non triviales (>=4 car.)",
          all(len(c.strip()) >= 4 for c in _vals("embleme_floral")))
if "valeur_couleur_resistance" in L.LECTEUR.tables:
    check("STRUCT valeur_couleur_resistance : chiffres 0..9 distincts (10 couleurs)",
          sorted(_vals("valeur_couleur_resistance")) == [str(i) for i in range(10)])
if "decalage_fuseau" in L.LECTEUR.tables:
    check("STRUCT decalage_fuseau : format UTC±…",
          all(c.startswith("UTC+") or c.startswith("UTC-") for c in _vals("decalage_fuseau")))
if "cote_organe" in L.LECTEUR.tables:
    check("STRUCT cote_organe : valeurs ∈ {à droite, à gauche}",
          set(_vals("cote_organe")) <= {"à droite", "à gauche"})
if "atmosphere_planete" in L.LECTEUR.tables:
    check("STRUCT atmosphere_planete : valeurs ∈ {oui, non}",
          set(_vals("atmosphere_planete")) <= {"oui", "non"})
if "nombre_notes_gamme" in L.LECTEUR.tables:
    check("STRUCT nombre_notes_gamme : entiers 5..12",
          all(c.isdigit() and 5 <= int(c) <= 12 for c in _vals("nombre_notes_gamme")))
if "duree_match" in L.LECTEUR.tables:
    check("STRUCT duree_match : durées en minutes",
          all(c.endswith("minutes") for c in _vals("duree_match")))
if "code_iso_numerique" in L.LECTEUR.tables:
    v = _vals("code_iso_numerique")
    check("STRUCT code_iso_numerique : chiffres, codes uniques",
          all(c.isdigit() for c in v) and len(set(v)) == len(v))
if "definition_adverbe" in L.LECTEUR.tables:
    _dadv = L.LECTEUR.tables["definition_adverbe"]
    def _defadv(m):
        f = _dadv.get(L.LECTEUR._cle("definition_adverbe", m))
        return (f.valeur if f else "").lower()
    check("definition_adverbe souvent ~ fréquence/fois", "fréquen" in _defadv("souvent") or "fois" in _defadv("souvent"))
    check("STRUCT definition_adverbe : non triviales (>=2 car.)",
          all(len(v.strip()) >= 2 for v in _vals("definition_adverbe")))
if "definition_verbe" in L.LECTEUR.tables:
    _dv = L.LECTEUR.tables["definition_verbe"]
    def _defv(m):
        f = _dv.get(L.LECTEUR._cle("definition_verbe", m))
        return (f.valeur if f else "").lower()
    check("definition_verbe aimer ~ sentiment/attirance", "sentiment" in _defv("aimer") or "attir" in _defv("aimer"))
    check("definition_verbe voler ~ air/ailes", "air" in _defv("voler") or "aile" in _defv("voler"))
    check("STRUCT definition_verbe : non triviales (>=2 car.)",
          all(len(v.strip()) >= 2 for v in _vals("definition_verbe")))
if "definition_adjectif" in L.LECTEUR.tables:
    _da = L.LECTEUR.tables["definition_adjectif"]
    def _defa(m):
        f = _da.get(L.LECTEUR._cle("definition_adjectif", m))
        return (f.valeur if f else "").lower()
    check("definition_adjectif alphabétique ~ alphabet", "alphabet" in _defa("alphabétique"))
    check("definition_adjectif rare ~ nombre/difficile", "nombre" in _defa("rare") or "difficile" in _defa("rare"))
    check("STRUCT definition_adjectif : non triviales (>=2 car.)",
          all(len(v.strip()) >= 2 for v in _vals("definition_adjectif")))

# 4) SOUNDNESS ADVERSE — inconnus -> JAMAIS un faux.
INCONNUS = [
    ("numero_atomique", "kryptonite"), ("numero_atomique", "vibranium"), ("numero_atomique", ""),
    ("numero_atomique", "123"), ("numero_atomique", "fer fer"),
    ("jours_mois", "septembrrr"), ("jours_mois", "13"), ("jours_mois", "lundi"),
    ("mois_nom", "0"), ("mois_nom", "13"), ("mois_nom", "janvier"),
    ("jour_semaine", "0"), ("jour_semaine", "8"), ("jour_semaine", "lundi"),
    ("relation_inexistante", "fer"), ("", "fer"), ("capitale", "atlantide"),
    ("prefixe_si", "zillion"), ("prefixe_si", "kilometre"), ("chiffre_romain", "A"), ("chiffre_romain", "W"),
    ("rang_lettre_grecque", "aleph"), ("rang_planete", "pluton"), ("rang_planete", "lune"),
    ("code_iso_pays", "atlantide"), ("code_iso_pays", "wakanda"), ("code_iso_pays", "fr"),
    ("prefixe_binaire", "kilo"), ("durete_mohs", "plastique"), ("durete_mohs", "11"),
    ("code_devise", "credit"), ("code_devise", "galleon"),
    ("indicatif_telephonique", "narnia"), ("symbole_prefixe_si", "zillion"), ("continent", "atlantide"),
    ("numero_mois", "smarch"), ("numero_mois", "13"), ("numero_jour_semaine", "funday"),
    ("formule_chimique", "kryptonite"), ("formule_chimique", "amour"),
    ("monnaie", "atlantide"), ("langue_officielle", "wakanda"), ("cotes_polygone", "cercle"),
    ("cotes_polygone", "patatoide"), ("faces_solide", "sphere"),
    ("nom_polygone", "2"), ("nom_polygone", "100"), ("grandeur_unite", "parsec"), ("symbole_unite", "lieue"),
]
# nom_polygone = inverse exact de cotes_polygone.
check("nom_polygone inverse de cotes_polygone",
      all(L.repond("nom_polygone", str(n))[1].valeur == nom for nom, n in L._COTES_POLYGONE))
check("grandeur_unite et symbole_unite couvrent le noyau SI (mètre/seconde/kg/ampère/kelvin/mole/candela)",
      all(L.repond("grandeur_unite", u)[0] == VERIFIE and L.repond("symbole_unite", u)[0] == VERIFIE
          for u in ("metre", "seconde", "kilogramme", "ampere", "kelvin", "mole", "candela")))
# Polygones/solides : valeurs cohérentes (côtés ≥ 3 ; faces ≥ 4). Monnaie zone euro = 'euro' partout.
check("polygones : côtés ≥ 3", all(int(c) >= 3 for _, c in L._COTES_POLYGONE))
check("solides de Platon : faces ∈ {4,6,8,12,20}", all(f in (4, 6, 8, 12, 20) for _, f in L._FACES_SOLIDE))
check("zone euro cohérente (France/Allemagne/Italie = euro)",
      all(L.repond("monnaie", p)[1].valeur == "euro" for p in ("france", "allemagne", "italie")))
# Inverses cohérents avec les tables directes : numero_mois ∘ mois_nom = identité ; idem jour_semaine.
check("numero_mois inverse de mois_nom",
      all(L.repond("numero_mois", nom)[1].valeur == num for num, nom in L._MOIS_NOM))
check("numero_jour_semaine inverse de jour_semaine",
      all(L.repond("numero_jour_semaine", j)[1].valeur == num for num, j in L._JOUR_SEMAINE))
check("symbole_prefixe_si couvre les mêmes noms que prefixe_si",
      {n for n, _ in L._SYMBOLE_PREFIXE_SI} == {n for n, _ in L._PREFIXE_SI})
check("formules chimiques non vides, alphanumériques",
      all(f and any(c.isdigit() or c.isupper() for c in f) for _, f in L._FORMULE_CHIMIQUE))
# ISO 3166 : tout code ingéré = 2 lettres MAJUSCULES, et les codes sont DISTINCTS (pas de doublon).
check("codes ISO = 2 lettres MAJ, distincts",
      all(isinstance(c, str) and len(c) == 2 and c.isupper() for _, c in L._CODE_ISO_PAYS)
      and len({c for _, c in L._CODE_ISO_PAYS}) == len(L._CODE_ISO_PAYS))
# ISO 4217 : codes = 3 lettres MAJ distincts. Mohs : échelle DÉFINITIONNELLE = exactement 1..10.
check("codes devise = 3 lettres MAJ distincts",
      all(isinstance(c, str) and len(c) == 3 and c.isupper() for _, c in L._CODE_DEVISE)
      and len({c for _, c in L._CODE_DEVISE}) == len(L._CODE_DEVISE))
check("échelle de Mohs = 10 minéraux dureté 1..10", [d for _, d in L._DURETE_MOHS] == list(range(1, 11)))
check("préfixes binaires = exposants de 2 (10,20,…,80)", [e for _, e in L._PREFIXE_BINAIRE] == list(range(10, 81, 10)))
for rel, ent in INCONNUS:
    st, f = L.repond(rel, ent)
    check(f"adverse {rel}({ent!r}) -> HORS", st == HORS and f is None and L.cherche(rel, ent) is None)

# 5) INGESTION — intégrité d'une source autoritative.
lec = L.Lecteur()
n = lec.ingere_table("densite", [("eau", 1000), ("mercure", 13534)], BF.CAT_PHYSIQUE, "CRC Handbook")
check("ingere_table renvoie nb nouvelles entrées", n == 2 and len(lec) == 2)
check("relecture après ingestion fraîche", lec.repond("densite", "eau")[1].valeur == "1000")
# idempotent : même valeur -> 0 nouveau, pas d'exception
check("ré-ingestion idempotente (même valeur)", lec.ingere_table("densite", [("eau", 1000)], BF.CAT_PHYSIQUE, "CRC") == 0)
# conflit : valeur divergente -> ValueError
try:
    lec.ingere_table("densite", [("eau", 9999)], BF.CAT_PHYSIQUE, "source fausse")
    check("conflit divergent -> ValueError", False)
except ValueError:
    check("conflit divergent -> ValueError", True)
# garde-fous : clé/valeur vide ignorée ; catégorie/source invalide -> ValueError
check("clé/valeur vide ignorée", lec.ingere_table("densite", [("", 5), ("plomb", "")], BF.CAT_PHYSIQUE, "x") == 0)
for bad in (lambda: lec.ingere_table("x", [("a", 1)], "categorie_bidon", "s"),
            lambda: lec.ingere_table("x", [("a", 1)], BF.CAT_PHYSIQUE, ""),
            lambda: lec.ingere_table("", [("a", 1)], BF.CAT_PHYSIQUE, "s")):
    try:
        bad(); check("garde-fou ingestion -> ValueError", False)
    except ValueError:
        check("garde-fou ingestion -> ValueError", True)

# 6) NL — tables ingérées + repli amorce base_faits (zéro régression).
NL_OK = [
    ("Quel est le numéro atomique du cuivre ?", "29"),
    ("numéro atomique de l'or", "79"),
    ("Combien de jours en février ?", "28"),
    ("Quelle est la capitale de la France ?", "Paris"),   # repli base_faits
    ("Quel est le pluriel de cheval ?", "chevaux"),       # repli base_faits
    ("Quel est le préfixe kilo ?", "3"),
    ("code ISO du Japon", "JP"),
    ("dureté du quartz", "7"),
    ("indicatif téléphonique de la France", "33"),
    ("formule chimique de l'eau", "H2O"),
    ("Sur quel continent se trouve le Japon ?", "Asie"),
    ("Quelle position occupe la Terre ?", "3"),
    ("Quelle est la monnaie du Japon ?", "yen"),
    ("Quelle est la langue officielle du Brésil ?", "portugais"),
    ("Combien de côtés a un hexagone ?", "6"),
    ("Combien de faces a un cube ?", "6"),
]
for q, attendu in NL_OK:
    st, f = L.repond_nl(q)
    check(f"NL « {q} » -> {attendu}", st == VERIFIE and f.valeur == attendu)
# NL adverse : gabarit reconnu, entité inconnue -> jamais un faux (HORS, et pas une valeur inventée).
for q in ("numéro atomique du vibranium", "Combien de jours en smarch ?", "Quel est ton plat préféré ?",
          "code ISO du Wakanda", "dureté du plastique", "formule chimique de l'amour",
          "Sur quel continent se trouve l'Atlantide ?", "préfixe zillion",
          "Quelle est la monnaie de l'Atlantide ?", "Combien de côtés a un cercle ?",
          "Combien de faces a une sphère ?",
          # FAUX=0 vécu 2026-07-08 : un INTERVALLE de dates n'est pas la durée d'un mois (« 31 » servi à tort)
          "Combien de jours entre le 1er janvier et le 15 mars ?",
          "Combien de jours du 1er janvier au 15 mars ?",
          # ni un COMPTE À REBOURS vers une date datée (« dans combien de jours le 25 décembre » -> 31 à tort)
          "dans combien de jours le 25 décembre ?",
          "combien de jours jusqu'au 25 décembre ?"):
    st, f = L.repond_nl(q)
    check(f"NL adverse « {q} » -> HORS", st == HORS and f is None)

# 6bis) POLITIQUE D'ARTICLES — table de symboles (articles=False) + cohérence imposée.
lec2 = L.Lecteur()
lec2.ingere_table("sym", [("L", 50), ("D", 500)], BF.CAT_CONVENTION, "s", articles=False)
check("articles=False : clé mono-lettre 'L' préservée", lec2.repond("sym", "L")[1].valeur == "50")
try:
    lec2.ingere_table("sym", [("M", 1000)], BF.CAT_CONVENTION, "s", articles=True)
    check("politique d'articles incohérente -> ValueError", False)
except ValueError:
    check("politique d'articles incohérente -> ValueError", True)

# 7) COMPOSITION — une relation PARTAGÉE entre le lecteur (datasets réconciliés) et base_faits est
#    autorisée SSI elle ÉTEND l'amorce sans JAMAIS la contredire (cherche() = dataset puis repli base_faits ;
#    la réconciliation a mis en quarantaine toute divergence -> 0 entité où les deux valeurs s'opposent).
#    Invariant de soundness plus fort que l'ancienne disjonction : c'est la NON-CONTRADICTION qui garantit
#    FAUX=0, pas l'absence de recouvrement (ex. capitale 74->191, symbole_chimique 55->118 via Wikidata).
_partagees = set(L.LECTEUR.tables) & {rel for rel, _ in BF.FAITS}
_incoherences = [(rel, ent, L.LECTEUR.tables[rel][L.LECTEUR._cle(rel, ent)].valeur, f_bf.valeur)
                 for (rel, ent), f_bf in BF.FAITS.items()
                 if rel in _partagees
                 and L.LECTEUR.tables[rel].get(L.LECTEUR._cle(rel, ent)) is not None
                 and L.LECTEUR.tables[rel][L.LECTEUR._cle(rel, ent)].valeur != f_bf.valeur]
check("relations partagées lecteur/base_faits : extension sans contradiction (FAUX=0)",
      not _incoherences)

# 8) CHARGEMENT JSONL OFFLINE (étape 0 ingestion) — charge_jsonl / charge_dossier, mêmes garde-fous.
import os, json, tempfile
_tmp = tempfile.mkdtemp(prefix="valide_lecteur_")
# 8a) charge_dossier : fichier self-describing (en-tête + faits) -> chargé, récupérable.
with open(os.path.join(_tmp, "densite_demo.jsonl"), "w", encoding="utf-8") as fh:
    fh.write(json.dumps({"_relation": "densite_demo", "_categorie": "physique", "_source": "test"}) + "\n")
    fh.write(json.dumps({"entite": "eau", "valeur": "1000"}) + "\n")
    fh.write(json.dumps({"entite": "fer", "valeur": "7874"}) + "\n")
lec_j = L.Lecteur()
charges = lec_j.charge_dossier(_tmp)
check("charge_dossier : 2 faits chargés", charges == {"densite_demo": 2} and len(lec_j) == 2)
check("charge_dossier : récupérable + source/catégorie portées",
      lec_j.repond("densite_demo", "eau")[1].valeur == "1000"
      and lec_j.cherche("densite_demo", "fer").source == "test")
# 8b) charge_dossier sur dossier absent -> no-op (l'amorce reste le socle).
check("charge_dossier : dossier absent -> {}", lec_j.charge_dossier(os.path.join(_tmp, "nexistepas")) == {})
# 8c) en-tête manquant -> ValueError (refus, pas de chargement silencieux).
with open(os.path.join(_tmp, "sans_entete.jsonl"), "w", encoding="utf-8") as fh:
    fh.write(json.dumps({"entite": "x", "valeur": "1"}) + "\n")
try:
    L.Lecteur().charge_dossier(_tmp); check("en-tête manquant -> ValueError", False)
except ValueError:
    check("en-tête manquant -> ValueError", True)
os.remove(os.path.join(_tmp, "sans_entete.jsonl"))
# 8d) charge_jsonl (fichier de faits, métadonnées passées par l'appelant) + conflit divergent -> ValueError.
with open(os.path.join(_tmp, "data.jsonl"), "w", encoding="utf-8") as fh:
    fh.write(json.dumps({"entite": "or", "valeur": "19300"}) + "\n")
    fh.write(json.dumps({"entite": "or", "valeur": "99999"}) + "\n")   # divergent -> doit lever
lec_k = L.Lecteur()
try:
    lec_k.charge_jsonl("densite_demo", os.path.join(_tmp, "data.jsonl"), "physique", "test")
    check("charge_jsonl : conflit divergent -> ValueError", False)
except ValueError:
    check("charge_jsonl : conflit divergent -> ValueError", True)
# 8e) charge_jsonl avec en-tête éventuel ignoré + idempotence.
with open(os.path.join(_tmp, "data2.jsonl"), "w", encoding="utf-8") as fh:
    fh.write(json.dumps({"_relation": "x"}) + "\n")                    # en-tête ignoré par charge_jsonl
    fh.write(json.dumps({"entite": "plomb", "valeur": "11340"}) + "\n")
lec_m = L.Lecteur()
n1 = lec_m.charge_jsonl("densite_demo", os.path.join(_tmp, "data2.jsonl"), "physique", "test")
n2 = lec_m.charge_jsonl("densite_demo", os.path.join(_tmp, "data2.jsonl"), "physique", "test")
check("charge_jsonl : en-tête ignoré + idempotent (1 puis 0)", n1 == 1 and n2 == 0)
import shutil
shutil.rmtree(_tmp, ignore_errors=True)

print(f"\n=== valide_lecteur : {ok}/{total} ===")
assert ok == total
