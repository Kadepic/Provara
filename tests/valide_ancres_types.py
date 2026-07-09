# -*- coding: utf-8 -*-
"""ANCRAGE des grandes tables TYPE_* (backlog audit_ancres 2026-07-09 : 98 tables non référencées, top volume).

Classe « BASE COMPLÈTE » (hors suite) : exige LECTEUR_DATASETS_DIR pointé sur le store réel (~72M faits).
Couvre les 5 plus grosses tables du backlog (≈ 3,7M faits) : type_etoile (1,28M), type_subdivision (1,05M),
type_localite (865k), type_galaxie (361k), type_site_archeo (155k).

MÉTHODE FAUX=0 (sonde + ancres, 2026-07-09) : chaque ancre a été SONDÉE dans le store réel PUIS recoupée avec
une connaissance certaine — au moindre doute l'entité est écartée (Véga/Bételgeuse/Proxima absentes du store ->
écartées, jamais forcées). LÉGER : lecture en flux des .jsonl, aucun import du moteur.

PIÈGE DOCUMENTÉ (anti-ancre) : type_localite["Mont-Saint-Michel"] = « municipalité du Québec » — VRAI pour
l'homonyme québécois (la table COALESCE une valeur par nom) ; l'abbaye normande est shadowée. Ne JAMAIS ancrer
un nom mondialement homonyme ici (même leçon que la garde anti-homonyme des villes/T10).

CLIQUET QUALITÉ : type_subdivision contient des entités-débris (fragments de coordonnées, « 0.1035…] ») —
mesurées et BORNÉES : la borne empêche toute dérive silencieuse à la prochaine ingestion.
"""
from __future__ import annotations

import os
import sys

D = os.environ.get("LECTEUR_DATASETS_DIR", "")

ok = ko = 0


def check(c, label):
    global ok, ko
    if c:
        ok += 1
    else:
        ko += 1
        print("  FAIL: " + label)


if not D or not os.path.exists(os.path.join(D, "type_etoile.jsonl")):
    print("valide_ancres_types : LECTEUR_DATASETS_DIR doit pointer sur la BASE COMPLÈTE "
          "(type_etoile.jsonl introuvable) — gate de classe « base complète », à lancer manuellement.")
    sys.exit(1)


def scanne(table: str, ancres: dict, volume_min: int, prefixe_debris: bool = False, compte_valeurs: bool = False):
    """Un SEUL passage en flux sur `table`.jsonl : (trouvées {entité: valeur}, nb lignes, nb valeurs vides,
    nb entités-débris, top valeurs). Ancres cherchées par sous-chaîne exacte (« "entite": "X", ») — léger et
    sans ambiguïté (le format d'export est stable, une ligne par fait)."""
    import collections
    import json as _json
    cibles = {'"entite": "%s", "valeur": "' % e: e for e in ancres}
    trouvees, n, vides, debris = {}, 0, 0, 0
    valeurs = collections.Counter()
    with open(os.path.join(D, table + ".jsonl"), encoding="utf-8") as f:
        for ligne in f:
            if ligne.startswith('{"_relation"'):
                continue
            n += 1
            if '"valeur": ""' in ligne:
                vides += 1
            if prefixe_debris and ('"entite": "-' in ligne or ']", "valeur"' in ligne):
                debris += 1
            if compte_valeurs:
                try:
                    valeurs[_json.loads(ligne)["valeur"]] += 1
                except (ValueError, KeyError):
                    pass
            for motif, ent in cibles.items():
                p = ligne.find(motif)
                if p >= 0:
                    fin = ligne.find('"', p + len(motif))
                    trouvees[ent] = ligne[p + len(motif):fin]
    return trouvees, n, vides, debris, valeurs


# ── type_etoile (1,28M — tête du backlog) ──
t, n, vides, _, _v = scanne("type_etoile", {"Soleil": 0, "Sirius": 0, "Antarès": 0}, 1_200_000)
check(t.get("Soleil") == "naine jaune", "type_etoile : Soleil -> naine jaune (ancre certaine)")
check(t.get("Sirius") == "étoile sélectionnée pour la navigation",
      "type_etoile : Sirius -> étoile de navigation (vrai — 1 des 58 étoiles de navigation)")
check(t.get("Antarès") == "étoile sélectionnée pour la navigation", "type_etoile : Antarès -> étoile de navigation")
check(n >= 1_200_000, "type_etoile : volume ≥ 1,2M (%d)" % n)
check(vides == 0, "type_etoile : zéro valeur vide (%d)" % vides)

# ── type_subdivision (1,05M) + CLIQUET débris ──
t, n, vides, debris, _v = scanne("type_subdivision", {"Bavière": 0}, 1_000_000, prefixe_debris=True)
check(t.get("Bavière") == "Land d'Allemagne", "type_subdivision : Bavière -> Land d'Allemagne (ancre certaine)")
check(n >= 1_000_000, "type_subdivision : volume ≥ 1M (%d)" % n)
check(vides == 0, "type_subdivision : zéro valeur vide (%d)" % vides)
check(debris < n * 0.005,
      "CLIQUET : entités-débris (coordonnées fuitées) bornées < 0,5 %% (%d/%d)" % (debris, n))

# ── type_localite (865k) ──
t, n, vides, _, _v = scanne("type_localite", {"Gruyères": 0, "Positano": 0}, 800_000)
check(t.get("Gruyères") == "petite ville", "type_localite : Gruyères -> petite ville (cité médiévale, certaine)")
check(t.get("Positano") == "siège de la municipalité", "type_localite : Positano -> siège de municipalité (comune)")
check(n >= 800_000, "type_localite : volume ≥ 800k (%d)" % n)
check(vides == 0, "type_localite : zéro valeur vide (%d)" % vides)

# ── type_galaxie (361k) ──
t, n, vides, _, _v = scanne("type_galaxie", {"Voie lactée": 0}, 350_000)
check(t.get("Voie lactée") == "galaxie spirale barrée", "type_galaxie : Voie lactée -> spirale barrée (certaine)")
check(n >= 350_000, "type_galaxie : volume ≥ 350k (%d)" % n)
check(vides == 0, "type_galaxie : zéro valeur vide (%d)" % vides)

# ── type_site_archeo (155k) ──
t, n, vides, _, _v = scanne("type_site_archeo", {"Pompéi": 0, "Stonehenge": 0, "Machu Picchu": 0}, 150_000)
check(t.get("Pompéi") == "ville antique", "type_site_archeo : Pompéi -> ville antique (certaine)")
check(t.get("Stonehenge") == "cromlech", "type_site_archeo : Stonehenge -> cromlech (cercle de pierres, certaine)")
check(t.get("Machu Picchu") == "ville antique", "type_site_archeo : Machu Picchu -> ville antique (certaine)")
check(n >= 150_000, "type_site_archeo : volume ≥ 150k (%d)" % n)
check(vides == 0, "type_site_archeo : zéro valeur vide (%d)" % vides)

# ═══ TRANCHE 2 (2026-07-09 jour) — le top suivant du backlog (≈ 673k faits) ═══
# Pièges FAUX débusqués à la sonde (anti-ancres, ne JAMAIS ancrer) :
#   subdivision_localite["Montmartre"] = « Saskatchewan » — VRAI pour le village canadien homonyme, le
#   quartier parisien est shadowé (COALESCE une valeur par nom) ;
#   etat_conservation["Colisée"] = « démoli ou détruit » — DOUTEUX (partiellement en ruine) -> écarté.

# ── subdivision_localite (149k : localité -> sa subdivision parente) ──
t, n, vides, _, _v = scanne("subdivision_localite", {"Šnipiškės": 0}, 140_000)
check(t.get("Šnipiškės") == "Municipalité de la ville de Vilnius",
      "subdivision_localite : Šnipiškės -> municipalité de Vilnius (seniūnija, certaine)")
check(n >= 140_000, "subdivision_localite : volume ≥ 140k (%d)" % n)
check(vides == 0, "subdivision_localite : zéro valeur vide (%d)" % vides)

# ── statut_patrimonial_site_archeo (118k) ──
t, n, vides, _, _v = scanne("statut_patrimonial_site_archeo",
                            {"site archéologique de Delphes": 0, "Machu Picchu": 0}, 110_000)
check(t.get("site archéologique de Delphes") == "Site archéologique de Grèce",
      "statut_patrimonial : Delphes -> site archéologique de Grèce (désignation officielle, certaine)")
check(t.get("Machu Picchu") == "Historic Civil Engineering Landmark",
      "statut_patrimonial : Machu Picchu -> Historic Civil Engineering Landmark (désignation ASCE, réelle)")
check(n >= 110_000, "statut_patrimonial_site_archeo : volume ≥ 110k (%d)" % n)
check(vides == 0, "statut_patrimonial_site_archeo : zéro valeur vide (%d)" % vides)

# ── type_cimetiere (81k) ──
t, n, vides, _, _v = scanne("type_cimetiere", {"cimetière de Passy": 0}, 75_000)
check(t.get("cimetière de Passy") == "cimetière parisien", "type_cimetiere : Passy -> cimetière parisien (certaine)")
check(n >= 75_000, "type_cimetiere : volume ≥ 75k (%d)" % n)
check(vides == 0, "type_cimetiere : zéro valeur vide (%d)" % vides)

# ── type_aire_protegee (80k) ──
t, n, vides, _, _v = scanne("type_aire_protegee",
                            {"parc national de la Vanoise": 0, "parc national des Écrins": 0}, 75_000)
check(t.get("parc national de la Vanoise") == "parc national", "type_aire_protegee : Vanoise -> parc national")
check(t.get("parc national des Écrins") == "parc national", "type_aire_protegee : Écrins -> parc national")
check(n >= 75_000, "type_aire_protegee : volume ≥ 75k (%d)" % n)
check(vides == 0, "type_aire_protegee : zéro valeur vide (%d)" % vides)

# ── type_eglise (77k) — aucune église célèbre dans la table (elles vivent ailleurs) : pas d'ancre d'entité
#    sans doute -> contrôle de DISTRIBUTION (les valeurs dominantes DOIVENT être des types d'églises réels,
#    vocabulaire fermé — certitude linguistique, pas devinette d'entité) ──
_VOCAB_EGLISE = {"chapelle", "église paroissiale", "église orthodoxe", "église catholique", "chapelle funéraire",
                 "temple protestant", "église de succursale", "ermitage", "église paroissiale catholique",
                 "cathédrale catholique", "cathédrale", "église en bois", "basilique", "collégiale", "oratoire",
                 "église fortifiée", "abbatiale", "temple maçonnique", "église ronde", "chapelle de cimetière"}
t, n, vides, _, vals = scanne("type_eglise", {}, 70_000, compte_valeurs=True)
_top10 = [v for v, _c in vals.most_common(10)]
check(all(v in _VOCAB_EGLISE for v in _top10),
      "type_eglise : top-10 des valeurs ⊆ vocabulaire fermé des types d'églises (%s)" %
      ", ".join(v for v in _top10 if v not in _VOCAB_EGLISE))
check(n >= 70_000, "type_eglise : volume ≥ 70k (%d)" % n)
check(vides == 0, "type_eglise : zéro valeur vide (%d)" % vides)

# ── type_quartier (59k) — même approche distribution (quartiers célèbres absents de la table) ──
_VOCAB_QUARTIER = {"mahalle", "communauté de quartier", "section de municipalité en Tchéquie", "arrondissement",
                   "dong de Corée du Sud", "district du Brésil", "ghetto dans l'Europe occupée par les nazis",
                   "Quartier prioritaire de la politique de la ville", "grand ensemble", "secteur résidentiel",
                   "quartier", "faubourg", "barrio", "quartier historique", "îlot urbain"}
t, n, vides, _, vals = scanne("type_quartier", {}, 55_000, compte_valeurs=True)
_top10 = [v for v, _c in vals.most_common(10)]
check(all(v in _VOCAB_QUARTIER for v in _top10),
      "type_quartier : top-10 des valeurs ⊆ vocabulaire fermé des types de quartiers (%s)" %
      ", ".join(v for v in _top10 if v not in _VOCAB_QUARTIER))
check(n >= 55_000, "type_quartier : volume ≥ 55k (%d)" % n)
check(vides == 0, "type_quartier : zéro valeur vide (%d)" % vides)

# ── type_fortification (58k) ──
t, n, vides, _, _v = scanne("type_fortification", {"château de Vincennes": 0, "tour de Londres": 0}, 55_000)
check(t.get("château de Vincennes") == "château fort", "type_fortification : Vincennes -> château fort (certaine)")
check(t.get("tour de Londres") == "château fort", "type_fortification : tour de Londres -> château fort (certaine)")
check(n >= 55_000, "type_fortification : volume ≥ 55k (%d)" % n)
check(vides == 0, "type_fortification : zéro valeur vide (%d)" % vides)

# ── etat_conservation (50k) ──
t, n, vides, _, _v = scanne("etat_conservation", {"phare d'Alexandrie": 0, "temple d'Artémis": 0}, 48_000)
check(t.get("phare d'Alexandrie") == "démoli ou détruit",
      "etat_conservation : phare d'Alexandrie -> démoli ou détruit (séismes, disparu — certaine)")
check(t.get("temple d'Artémis") == "en ruine", "etat_conservation : temple d'Artémis -> en ruine (certaine)")
check(n >= 48_000, "etat_conservation : volume ≥ 48k (%d)" % n)
check(vides == 0, "etat_conservation : zéro valeur vide (%d)" % vides)

# ═══ TRANCHE 3 (2026-07-09 jour) — top suivant (≈ 247k faits) ═══

# ── type_riviere (50k) ──
t, n, vides, _, _v = scanne("type_riviere", {"Loire": 0, "Danube": 0}, 48_000)
check(t.get("Loire") == "fleuve", "type_riviere : Loire -> fleuve (certaine)")
check(t.get("Danube") == "cours d'eau transfrontalier", "type_riviere : Danube -> transfrontalier (10 pays, certaine)")
check(n >= 48_000, "type_riviere : volume ≥ 48k (%d)" % n)
check(vides == 0, "type_riviere : zéro valeur vide (%d)" % vides)

# ── type_ile (45k) — Honshū, l'île du fait réinjecté du LOT 1 (audit total), désormais ANCRÉE ici aussi ──
t, n, vides, _, _v = scanne("type_ile", {"Honshū": 0}, 42_000)
check(t.get("Honshū") == "île du Japon", "type_ile : Honshū -> île du Japon (certaine)")
check(n >= 42_000, "type_ile : volume ≥ 42k (%d)" % n)
check(vides == 0, "type_ile : zéro valeur vide (%d)" % vides)

# ── type_bibliotheque (44k) ──
t, n, vides, _, _v = scanne("type_bibliotheque",
                            {"Bibliothèque nationale de France": 0, "bibliothèque Bodléienne": 0}, 42_000)
check(t.get("Bibliothèque nationale de France") == "bibliothèque nationale",
      "type_bibliotheque : BnF -> bibliothèque nationale (certaine)")
check(t.get("bibliothèque Bodléienne") == "bibliothèque universitaire",
      "type_bibliotheque : Bodléienne -> bibliothèque universitaire (Oxford, certaine)")
check(n >= 42_000, "type_bibliotheque : volume ≥ 42k (%d)" % n)
check(vides == 0, "type_bibliotheque : zéro valeur vide (%d)" % vides)

# ── type_nebuleuse (37k) — entités-catalogue (SIMBAD), pas de nom célèbre : distribution (types de sources
#    astronomiques RÉELS — certitude de vocabulaire, pas devinette d'entité) ──
_VOCAB_ASTRO = {"source submillimétrique", "radiogalaxie", "source radio millimétrique", "source de raie HI",
                "maser astronomique", "source radio centimétrique", "étoile à émission OH/IR",
                "sursaut radio rapide", "nébuleuse en émission", "nébuleuse obscure", "nébuleuse planétaire",
                "rémanent de supernova", "région HII", "nuage moléculaire"}
t, n, vides, _, vals = scanne("type_nebuleuse", {}, 35_000, compte_valeurs=True)
_top8 = [v for v, _c in vals.most_common(8)]
check(all(v in _VOCAB_ASTRO for v in _top8),
      "type_nebuleuse : top-8 ⊆ types de sources astronomiques réels (%s)" %
      ", ".join(v for v in _top8 if v not in _VOCAB_ASTRO))
check(n >= 35_000, "type_nebuleuse : volume ≥ 35k (%d)" % n)
check(vides == 0, "type_nebuleuse : zéro valeur vide (%d)" % vides)

# ── subdivision_aire_protegee (37k) — valeurs = subdivisions RÉELLES (états australiens, cantons suisses…) ──
_VOCAB_SUBDIV = {"Victoria", "Nouvelle-Galles du Sud", "Australie-Méridionale", "Australie-Occidentale",
                 "Tasmanie", "Queensland", "canton des Grisons", "canton de Berne", "canton du Valais",
                 "canton de Vaud", "Territoire du Nord", "oblast de Ternopil", "Jeju"}
t, n, vides, _, vals = scanne("subdivision_aire_protegee", {}, 34_000, compte_valeurs=True)
_top8 = [v for v, _c in vals.most_common(8)]
check(all(v in _VOCAB_SUBDIV for v in _top8),
      "subdivision_aire_protegee : top-8 ⊆ subdivisions réelles (%s)" %
      ", ".join(v for v in _top8 if v not in _VOCAB_SUBDIV))
check(n >= 34_000, "subdivision_aire_protegee : volume ≥ 34k (%d)" % n)
check(vides == 0, "subdivision_aire_protegee : zéro valeur vide (%d)" % vides)

# ── etoile_galaxie (34k : étoile cataloguée -> galaxie hôte) — valeurs = galaxies RÉELLES ──
_VOCAB_GALAXIES = {"Grand Nuage de Magellan", "Petit Nuage de Magellan", "galaxie naine de la Carène",
                   "galaxie naine du Fourneau", "galaxie naine du Sculpteur", "M101", "galaxie du Triangle",
                   "Andromeda VII", "galaxie d'Andromède", "Voie lactée", "M33", "NGC 6822"}
t, n, vides, _, vals = scanne("etoile_galaxie", {}, 32_000, compte_valeurs=True)
_top8 = [v for v, _c in vals.most_common(8)]
check(all(v in _VOCAB_GALAXIES for v in _top8),
      "etoile_galaxie : top-8 ⊆ galaxies réelles (%s)" % ", ".join(v for v in _top8 if v not in _VOCAB_GALAXIES))
check(n >= 32_000, "etoile_galaxie : volume ≥ 32k (%d)" % n)
check(vides == 0, "etoile_galaxie : zéro valeur vide (%d)" % vides)

# ═══ TRANCHE 4 (2026-07-09 jour) — top suivant (≈ 159k faits) ═══

# ── type_zone_humide (30k) ──
t, n, vides, _, _v = scanne("type_zone_humide", {"Everglades": 0}, 29_000)
check(t.get("Everglades") == "prairies et savanes inondées",
      "type_zone_humide : Everglades -> prairies et savanes inondées (biome réel, certaine)")
check(n >= 29_000, "type_zone_humide : volume ≥ 29k (%d)" % n)
check(vides == 0, "type_zone_humide : zéro valeur vide (%d)" % vides)

# ── type_lac (29k) ──
t, n, vides, _, _v = scanne("type_lac", {"lac Titicaca": 0}, 28_000)
check(t.get("lac Titicaca") == "lac monomictique",
      "type_lac : Titicaca -> lac monomictique (limnologie, certaine)")
check(n >= 28_000, "type_lac : volume ≥ 28k (%d)" % n)
check(vides == 0, "type_lac : zéro valeur vide (%d)" % vides)

# ── type_gare (26k) — gares célèbres absentes : distribution (types de gares réels) ──
_VOCAB_GARE = {"station de métro", "ancienne gare ferroviaire", "gare de marchandise", "station surélevée",
               "station de RER", "Bahnhof", "gare frontière ou poste frontière ferroviaire", "gare technique",
               "gare ferroviaire", "halte ferroviaire", "gare souterraine", "gare de triage"}
t, n, vides, _, vals = scanne("type_gare", {}, 25_000, compte_valeurs=True)
_top8 = [v for v, _c in vals.most_common(8)]
check(all(v in _VOCAB_GARE for v in _top8),
      "type_gare : top-8 ⊆ types de gares réels (%s)" % ", ".join(v for v in _top8 if v not in _VOCAB_GARE))
check(n >= 25_000, "type_gare : volume ≥ 25k (%d)" % n)
check(vides == 0, "type_gare : zéro valeur vide (%d)" % vides)

# ── type_parc (26k) ──
t, n, vides, _, _v = scanne("type_parc", {"jardin du Luxembourg": 0}, 24_000)
check(t.get("jardin du Luxembourg") == "jardin public", "type_parc : jardin du Luxembourg -> jardin public (certaine)")
check(n >= 24_000, "type_parc : volume ≥ 24k (%d)" % n)
check(vides == 0, "type_parc : zéro valeur vide (%d)" % vides)

# ── lieu_dans_aire_protegee (26k : lieu -> aire protégée contenante) — valeurs = aires protégées RÉELLES ──
_VOCAB_AIRES = {"parc national de Fiordland", "parc national du mont Aspiring", "réserve faunique La Vérendrye",
                "parc national d'Aigüestortes et lac Saint-Maurice", "zec du Gros-Brochet",
                "parc national des Tatras", "parc national de Te Urewera", "parc national du Nord-Est du Groenland",
                "parc national du Loch Lomond et des Trossachs", "parc national des volcans d'Hawaï"}
t, n, vides, _, vals = scanne("lieu_dans_aire_protegee", {}, 24_000, compte_valeurs=True)
_top8 = [v for v, _c in vals.most_common(8)]
check(all(v in _VOCAB_AIRES for v in _top8),
      "lieu_dans_aire_protegee : top-8 ⊆ aires protégées réelles (%s)" %
      ", ".join(v for v in _top8 if v not in _VOCAB_AIRES))
check(n >= 24_000, "lieu_dans_aire_protegee : volume ≥ 24k (%d)" % n)
check(vides == 0, "lieu_dans_aire_protegee : zéro valeur vide (%d)" % vides)

# ── type_musee (22k) — distribution (types de musées réels) ──
_VOCAB_MUSEE = {"musée d'art", "musée d'histoire locale", "maison-musée", "musée militaire", "musée historique",
                "musée archéologique", "musée en plein air", "musée ferroviaire", "musée des sciences",
                "musée ethnographique", "musée maritime", "écomusée"}
t, n, vides, _, vals = scanne("type_musee", {}, 20_000, compte_valeurs=True)
_top8 = [v for v, _c in vals.most_common(8)]
check(all(v in _VOCAB_MUSEE for v in _top8),
      "type_musee : top-8 ⊆ types de musées réels (%s)" % ", ".join(v for v in _top8 if v not in _VOCAB_MUSEE))
check(n >= 20_000, "type_musee : volume ≥ 20k (%d)" % n)
check(vides == 0, "type_musee : zéro valeur vide (%d)" % vides)

print("=== valide_ancres_types : %d/%d ===" % (ok, ok + ko))
sys.exit(1 if ko else 0)
