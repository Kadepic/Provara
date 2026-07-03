"""
INGESTION T5 — ŒUVRES CULTURELLES, côté CRÉATEURS / PRODUCTION (Wikidata via QLever).

Couloir T5 du chantier d'ingestion parallèle (cf. BRIEF_T5_OEUVRES.md). On prend le côté
créateurs/production des œuvres ; le côté genre/langue/style/matériau/tonalité/mouvement est DÉJÀ T1.

SOUNDNESS (identique au reste, FAUX=0) : on réutilise la fabrique générique
`ingere_qlever._ingere_x_vers_entite` -> `fonctionnel` (1 valeur/entité, le multi-valeur part en HORS) +
réconciliation amorce (conflits -> datasets/_conflits/) + source citée. Les libellés = Q-ID nu sont rejetés,
les valeurs < 2 caractères aussi (`_paires`). Sanité + ancres vérité-terrain dans `valide_lecteur_t5.py`.

DEUX FAMILLES :
  • ENSEMBLES (quasi-)FERMÉS (scout PROPRE, ratio bas) : société de prod, distributeur, label, éditeur de
    jeu, collection/musée d'une peinture, chaîne de diffusion d'une série. Vocabulaire borné de
    studios/labels/musées/chaînes.
  • VOCAB OUVERT de PERSONNES/STUDIOS (scout « pas un ensemble fermé » MAIS échantillon relu propre +
    `fonctionnel` élevé 94-99 %) : scénariste, interprète d'album, développeur de jeu, auteur/illustrateur
    de livre. La valeur est un NOM (personne ou studio) ; `fonctionnel` rejette les titres homonymes
    multi-valeur -> FAUX=0. Sanité = non vide + ≥2 car. + plausible + ANCRES (œuvres au titre non ambigu).

Catégorie « convention » : la paternité/production d'une œuvre est un fait culturel stable non contesté
(cohérent avec realisateur_film/compositeur_oeuvre déjà ingérés en « convention »).

Usage : python3 ingere_t5.py [domaines...]   (défaut : tous)   puis non-reg OFFLINE.
"""
from __future__ import annotations

import sys

import ingere_qlever as IQ

# Chaque entrée : (clé domaine, relation, classe_qid, propriété, libellé source).
_T5 = [
    # — ENSEMBLES (quasi-)FERMÉS (scout PROPRE) —
    ("societe_prod",   "societe_production_film", "Q11424",   "P272",
     "société de production du film"),
    ("distributeur",   "distributeur_film",       "Q11424",   "P750",
     "distributeur du film"),
    ("label_album",    "label_album",             "Q482994",  "P264",
     "label discographique de l'album"),
    ("editeur_jeu",    "editeur_jeu",             "Q7889",    "P123",
     "éditeur du jeu vidéo"),
    ("collection",     "collection_peinture",     "Q3305213", "P195",
     "collection/musée de la peinture"),
    ("chaine",         "chaine_diffusion",        "Q5398426", "P449",
     "chaîne de diffusion d'origine de la série TV"),
    # — VOCAB OUVERT de PERSONNES/STUDIOS (fonctionnel élevé, échantillon relu propre, ancres) —
    ("scenariste",     "scenariste_film",         "Q11424",   "P58",
     "scénariste du film"),
    ("interprete",     "interprete_album",        "Q482994",  "P175",
     "artiste interprète de l'album"),
    ("developpeur",    "developpeur_jeu",         "Q7889",    "P178",
     "studio développeur du jeu vidéo"),
    # Q7725634 = « œuvre écrite » (livre MAIS AUSSI article/publication) -> nom HONNÊTE « œuvre écrite »
    # (le fait reste vrai ; renommé pour ne pas mentir sur le périmètre, cf. piège materiau_objet_art).
    ("auteur_oeuvre_ecrite", "auteur_oeuvre_ecrite", "Q7725634", "P50",
     "auteur de l'œuvre écrite (livre/article/publication)"),
    ("illustrateur_oeuvre_ecrite", "illustrateur_oeuvre_ecrite", "Q7725634", "P110",
     "illustrateur de l'œuvre écrite"),
    # — VAGUE 2 (2026-06-26) : open vocab, scout fonctionnel ≥94 % + échantillon relu propre —
    # (producteur_film P162 fonc 92 % et librettiste_oeuvre P87 fonc 86 % REJETÉS : sous le seuil.)
    ("compositeur_musique_film", "compositeur_musique_film", "Q11424", "P86",
     "compositeur de la musique du film"),
    ("directeur_photo_film", "directeur_photo_film", "Q11424", "P344",
     "directeur de la photographie du film"),
    ("monteur_film", "monteur_film", "Q11424", "P1040",
     "monteur du film"),
    ("compositeur_jeu", "compositeur_jeu", "Q7889", "P86",
     "compositeur de la musique du jeu vidéo"),
    # serie_jeu = franchise dont le jeu fait partie (œuvre->œuvre, fonctionnel = 1 série principale).
    ("serie_jeu", "serie_jeu", "Q7889", "P179",
     "série/franchise dont le jeu vidéo fait partie"),
    ("maison_edition_oeuvre_ecrite", "maison_edition_oeuvre_ecrite", "Q7725634", "P123",
     "maison d'édition de l'œuvre écrite"),
    # — VAGUE 3 (2026-06-26) —
    # FERMÉE : label de la chanson (vocabulaire borné de labels, ratio 0.145 ; multi-label->HORS).
    ("label_chanson", "label_chanson", "Q7366", "P264",
     "label discographique de la chanson"),
    # OPEN VOCAB (fonc ≥96 %, échantillon relu propre) : costumier de film, producteur d'album.
    # (REJETÉS vague3 : societe_production_serie 80 %, distributeur_serie 80 %, compositeur_serie 93 %,
    #  scenariste_jeu 82 %/207 ent., directeur_artistique_jeu 28 ent.)
    ("costumier_film", "costumier_film", "Q11424", "P2515",
     "costumier (création des costumes) du film"),
    ("producteur_album", "producteur_album", "Q482994", "P162",
     "producteur de l'album"),
    # — VAGUE 7 (2026-06-26) : NOUVEAUX sous-domaines ŒUVRES côté créateurs (collision=0, open vocab) —
    # T1 a la géo/style/usage de ces œuvres, PAS le créateur -> côté production = T5.
    ("architecte_edifice", "architecte_edifice", "Q41176", "P84",
     "architecte de l'édifice"),
    ("sculpteur_oeuvre", "sculpteur_oeuvre", "Q860861", "P170",
     "sculpteur (créateur) de la sculpture"),
    ("photographe_oeuvre", "photographe_oeuvre", "Q125191", "P170",
     "photographe (créateur) de la photographie"),
    # — VAGUE 8 (2026-06-26) : BD / manga (open vocab) — auteur_bd T1 = petite amorce distincte.
    # On prend le mangaka (P50) + le dessinateur de BD (P110) ; dessinateur_manga ÉCARTÉ (redondant : même
    # personne que l'auteur via P50/P110) ; scenariste_bd ÉCARTÉ (fonc 84 % < seuil).
    ("auteur_manga", "auteur_manga", "Q21198342", "P50",
     "auteur (mangaka) de la série manga"),
    ("dessinateur_bd", "dessinateur_bd", "Q1004", "P110",
     "dessinateur de la bande dessinée"),
    # — VAGUE 9 (2026-06-26) : graveur d'estampe (open vocab fonc 97 %) —
    ("graveur_estampe", "graveur_estampe", "Q11835431", "P170",
     "graveur (créateur) de l'estampe"),
    # — VAGUE 10 (2026-06-26) : réalisateur de jeu vidéo (open vocab fonc 94 %, sémantique « director ») —
    ("realisateur_jeu", "realisateur_jeu", "Q7889", "P57",
     "réalisateur (game director) du jeu vidéo"),
    # — VAGUE 11 (2026-06-26) : interprète d'un single (Q134556, distinct de l'album ; open vocab fonc 95 %) —
    ("interprete_single", "interprete_single", "Q134556", "P175",
     "artiste interprète du single"),
    # — VAGUE 12 (2026-06-26) : chef décorateur / production designer du film (open vocab fonc 98 %) —
    ("chef_decorateur_film", "chef_decorateur_film", "Q11424", "P2554",
     "chef décorateur (production designer) du film"),
    # — VAGUE 13 (2026-06-26) : dessin (créateur) + coloriste de BD (open vocab fonc 96 %) —
    ("dessinateur_dessin", "dessinateur_dessin", "Q93184", "P170",
     "dessinateur (créateur) du dessin"),
    ("coloriste_bd", "coloriste_bd", "Q1004", "P6338",
     "coloriste de la bande dessinée"),
    # — VAGUE 14 (2026-06-26) : concepteur (game designer, P287 « designed by ») du jeu vidéo —
    #   open vocab fonc 94 % (= seuil, comme realisateur_jeu vague 10). DISTINCT de developpeur_jeu(P178,
    #   studio)/realisateur_jeu(P57, director)/compositeur_jeu(P86). Le designer est une PERSONNE
    #   (Will Wright, Peter Molyneux, Yūji Horii, Sid Meier…). Multi-designer -> HORS.
    ("concepteur_jeu", "concepteur_jeu", "Q7889", "P287",
     "concepteur (game designer) du jeu vidéo"),
    # — VAGUE 15 (2026-06-26) : hymne (Q484692) — compositeur (P86) + parolier (P676) ; open vocab
    #   fonc 96 %/94 %, échantillons relus propres (A Portuguesa→Keil/Mendonça, Marseillaise→Rouget de Lisle,
    #   Mer Hayrenik→Nalbandian). Œuvre hymne = couloir T5 (créateur) ; signalé board (T1 = musique générique).
    ("compositeur_hymne", "compositeur_hymne", "Q484692", "P86",
     "compositeur de l'hymne"),
    ("parolier_hymne", "parolier_hymne", "Q484692", "P676",
     "parolier (auteur des paroles) de l'hymne"),
    # — VAGUE 16 (2026-06-26) : installation d'art contemporain (Q20437094) -> créateur (P170) ; open vocab
    #   fonc 94 %, échantillon propre (Comedian→Cattelan, Bruce Nauman, Lawrence Weiner). ≠ peinture(T1)/sculpture.
    ("createur_installation_art", "createur_installation_art", "Q20437094", "P170",
     "créateur (artiste) de l'installation d'art"),
    # — VAGUE 17 (2026-06-26) : facture instrumentale via SOUS-CLASSES HOMOGÈNES (la classe parent
    #   instrument Q34379 est BRUITÉE : Beyblade/sonars CAPTAS·USHUS/écouteurs/micros/consoles -> FAUX rejeté).
    #   Sous-classes propres seulement : guitare électrique, synthétiseur, piano -> fabricant (P176).
    ("fabricant_guitare", "fabricant_guitare", "Q78987", "P176",
     "fabricant de la guitare électrique"),
    ("fabricant_synthetiseur", "fabricant_synthetiseur", "Q163829", "P176",
     "fabricant du synthétiseur"),
    ("fabricant_piano", "fabricant_piano", "Q5994", "P176",
     "fabricant du piano"),
    # — VAGUE 18 ⛔ REJETÉE FAUX=0 (2026-06-26, reprise post-/clear) : lieu_conservation via P276 ABANDONNÉE.
    #   La prémisse « sous-classe peinture = que des musées » était basée sur le TOP30 seulement = FAUSSE.
    #   La relire COMPLÈTE du snapshot (127 928 lignes) révèle du bruit en QUEUE non rattrapable par `fonctionnel` :
    #   « salle 709/710/903… » (numéros de salle = sous-localisation, pas une institution identifiable),
    #   « réserves »/« stockage »/« Réserve des miniatures » (descripteurs de rangement), « Paris »/villes nues
    #   (géographique), « inconnu », et côté dessin (Q93184) « Petit/Grand format ». P276 = propriété
    #   « localisation » qui MÉLANGE les granularités (institution/salle/ville/réserve) -> inassainissable sans
    #   filtre fragile sur 8544 valeurs ouvertes. DE PLUS redondant avec `collection_peinture` (P195, 61 963 faits
    #   déjà ingérés, valeurs institutionnelles PROPRES). LEÇON (re)confirmée : relire la LISTE COMPLÈTE, pas le top.
    #   Q838948 (œuvre parent) déjà rejeté avant (Stolpersteine). Le côté institutionnel propre est DÉJÀ couvert.
]

_SRC = "Wikidata/QLever — {} {} (fonctionnel, multi-valeur -> HORS)"


def _fait(relation, classe, prop, libelle):
    IQ._ingere_x_vers_entite(relation, prop, "convention",
                             _SRC.format(libelle, prop), classe_qid=classe)


def main(argv):
    choisis = set(argv) if argv else None
    for cle, relation, classe, prop, libelle in _T5:
        if choisis and cle not in choisis and relation not in choisis:
            continue
        _fait(relation, classe, prop, libelle)


if __name__ == "__main__":
    main(sys.argv[1:])
