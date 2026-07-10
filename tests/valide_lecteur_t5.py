"""
VALIDATION T5 — ŒUVRES CULTURELLES (créateurs/production). Verrouille la soundness FAUX=0 des 37 relations
T5 : `ingere_t5.py` (11 batch1 + 6 vague2 + 3 vague3) + `ingere_t5_canon.py` (6 relations CANON modèle :
compositeur opéra/comédie musicale/ballet + librettiste/parolier, comblent le trou Wikidata FR sous-peuplée).
Lance SEUL en dev (1 seul chargement du lecteur) ; intégrable à la non-rég.

Invariants vérifiés :
  1. PRÉSENCE : chacune des 11 relations T5 existe et est non vide.
  2. INTÉGRITÉ + STRUCTURE : chaque fait porte une valeur non vide ≥2 car., catégorie connue, source non
     vide. NOTE FAUX=0 : ces 11 propriétés sont ENTITÉ-VALUÉES (la valeur = libellé d'un item Wikidata),
     donc AUCUNE date ne peut fuir comme dans les lieux P19/P20 -> on n'exige PAS « contient une lettre »
     (des labels/studios légitimes sont numériques : « 2.13.61 » label de Henry Rollins, « 4AD »…).
  3. FERMETÉ RELATIVE (ensembles quasi-fermés) : société/distributeur/label/éditeur/collection/chaîne ont un
     ratio valeurs_distinctes/faits BAS (< 0.20) -> vocabulaire borné partagé (studios, labels, musées,
     chaînes). Une explosion du ratio signalerait une relation devenue open-vocab = à re-juger.
  4. ANCRES VÉRITÉ-TERRAIN (le cœur FAUX=0) : 20 œuvres au titre NON ambigu -> créateur/producteur vérifié
     à la main, indépendamment du code (Abbey Road->The Beatles, Guernica->Reina Sofía, Portal 2->Valve…).
  5. SOUNDNESS ADVERSE : entité absente / relation absente -> JAMAIS un faux : toujours (HORS, None).

FAUX=0 plus en amont : `fonctionnel` (dans publie) a mis tout titre multi-valeur en HORS (rejets_multi
mesurés : 6217 prod, 18605 scénaristes, 22333 auteurs…), conflits_amorce=0 partout.
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
    print("=== valide_lecteur_t5 : SKIP — base complète requise (occupation_personne absent de ce store) ===")
    _sys.exit(0)
# ──────────────────────────────────────────────────────

from garde_ressources import borne

borne(max_go=6.5, max_cpu_s=900)   # charge tout le lecteur : la base a grossi (~20 M faits, multi-lanes) ;
# le pic transitoire de gele() (blob "".join(keys)) dépassait 4 Go -> MemoryError. 5,5 Go reste sûr (30 Go
# libres mesurés, une seule gate lourde à la fois par coordination). LOAD ~60-90 s CPU -> 900 s de marge.

import lecteur as L
from lecteur import VERIFIE, HORS
import base_faits as BF

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

FERMEES = ["societe_production_film", "distributeur_film", "label_album",
           "editeur_jeu", "collection_peinture", "chaine_diffusion",
           "label_chanson"]  # vague 3 : ratio 0.145 (multi-label -> HORS)
OUVERTES = ["scenariste_film", "interprete_album", "developpeur_jeu",
            "auteur_oeuvre_ecrite", "illustrateur_oeuvre_ecrite",
            # — vague 2 (2026-06-26) : open vocab, fonctionnel ≥94 %, ancres ci-dessous —
            "compositeur_musique_film", "directeur_photo_film", "monteur_film",
            "compositeur_jeu", "serie_jeu", "maison_edition_oeuvre_ecrite",
            # — vague 3 (2026-06-26) : open vocab fonc 96 % —
            "costumier_film", "producteur_album",
            # — vague 7 (2026-06-26) : nouveaux sous-domaines ŒUVRES (face créateur), open vocab —
            "architecte_edifice", "sculpteur_oeuvre", "photographe_oeuvre",
            # — vague 8 (2026-06-26) : BD / manga, open vocab —
            "auteur_manga", "dessinateur_bd",
            # — vague 9 (2026-06-26) : estampe (Wikidata open vocab) —
            "graveur_estampe",
            # — vague 10 (2026-06-26) : réalisateur de jeu vidéo (open vocab fonc 94 %) —
            "realisateur_jeu",
            # — vague 11 (2026-06-26) : interprète d'un single (open vocab fonc 95 %) —
            "interprete_single",
            # — vague 12 (2026-06-26) : chef décorateur / production designer (open vocab fonc 98 %) —
            "chef_decorateur_film",
            # — vague 13 (2026-06-26) : dessin (créateur) + coloriste de BD (open vocab fonc 96 %) —
            "dessinateur_dessin", "coloriste_bd",
            # — vague 14 (2026-06-26) : concepteur (game designer, P287) du jeu vidéo (open vocab fonc 94 %) —
            "concepteur_jeu",
            # — vague 15 (2026-06-26) : hymne (Q484692) compositeur/parolier (open vocab fonc 96 %/94 %) —
            "compositeur_hymne", "parolier_hymne",
            # — vague 16 (2026-06-26) : installation d'art contemporain (Q20437094, open vocab fonc 94 %) —
            "createur_installation_art",
            # — vague 17 (2026-06-26) : facture instrumentale (sous-classes HOMOGÈNES, fonc 100 %) —
            "fabricant_guitare", "fabricant_synthetiseur", "fabricant_piano",
            # — CANON modèle (2026-06-26) : Wikidata FR sous-peuplée -> faits canoniques indiscutables —
            "compositeur_opera", "compositeur_comedie_musicale",
            "compositeur_ballet", "librettiste_opera", "parolier_comedie_musicale",
            "auteur_jeu_societe",
            # — CANON v15 (2026-06-26) : créateur de police d'écriture (Wikidata FR = 0 entité) —
            "createur_police_ecriture",
            # — CANON v16 (2026-06-26) : créateur de langage de programmation (créateur unique incontesté) —
            "createur_langage_programmation",
            # — CANON v17 (2026-06-26) : créateur/showrunner de série télévisée (créateur unique incontesté) —
            "createur_serie_television",
            # — CANON v18 (2026-06-26) : créateur de logiciel emblématique non-jeu (créateur unique incontesté) —
            "createur_logiciel",
            # — CANON v19 (2026-06-26) : librettiste (auteur du livret/« book ») de comédie musicale, auteur
            #   unique certain (duos écartés), distinct du parolier_comedie_musicale et du compositeur_ —
            "librettiste_comedie_musicale",
            # — CANON v20 (2026-06-26) : inventeur UNIQUE indiscutable d'un type d'instrument de musique
            #   (disputés/duos écartés), distinct de la facture instrumentale (fabricants, vague17) —
            "inventeur_instrument_musique",
            # — CANON v21 (2026-06-26) : parfumeur (« nez ») unique d'un parfum (histoire de la parfumerie,
            #   attribution établie ; duos écartés ; titres ambigus qualifiés par la maison) —
            "parfumeur_parfum",
            # — CANON v22 (2026-06-26) : auteur unique d'un jeu de rôle sur table (équipes/duos écartés,
            #   homonymes écartés ; distinct de auteur_jeu_societe plateau et concepteur_jeu vidéo) —
            "auteur_jeu_role",
            # — CANON v23 (2026-06-26) : créateur (designer) unique d'un objet de design iconique (mobilier/
            #   luminaire) ; duos écartés ; précédent createur_police (design attribuable) —
            "createur_objet_design",
            # — CANON round10 (run autonome 2026-06-26) : créateur UNIQUE d'une langue construite (conlang) ;
            #   équipes/réformes écartées (Ido/Interlingua/Lojban) ; distinct de createur_langage_programmation —
            "createur_langue_construite",
            # — CANON round11 (run autonome 2026-06-26) : designer UNIQUE d'un logo iconique ;
            #   agences/équipes écartées ; œuvre de design graphique attribuable —
            "createur_logo",
            # — CANON round12 (run autonome 2026-06-26) : chorégraphe UNIQUE d'un ballet-repère ;
            #   duos/revivals écartés ; distinct de compositeur_ballet —
            "choregraphe_ballet",
            # — CANON round13 (run autonome 2026-06-26) : concepteur/paysagiste UNIQUE d'un jardin-repère ;
            #   jardins à intervenants multiples écartés ; distinct de l'architecte —
            "paysagiste_jardin",
            # — CANON round15 (run autonome 2026-06-26) : designer UNIQUE d'un drapeau ; comités/disputes
            #   écartés ; distinct de la donnée géo pays→drapeau (T1) —
            "createur_drapeau",
            # — CANON round19 (run autonome 2026-06-26) : inventeur UNIQUE d'un système d'écriture/script ;
            #   distinct de conlang (langue) et de police (typographie) —
            "createur_systeme_ecriture",
            # — WIKIDATA round21 (run autonome 2026-06-26) : compositeur de la musique d'une série TV
            #   (P86/Q5398426, vocab ouvert ; fonctionnel multi→HORS) ; veine ré-ouverte par re-scout —
            "compositeur_musique_serie",
            # — CANON round25 (run autonome 2026-06-26) : chorégraphe UNIQUE d'une comédie musicale
            #   (production originale) ; distinct de choregraphe_ballet —
            "choregraphe_comedie_musicale",
            # — CANON round26 (run autonome 2026-06-26) : compositeur UNIQUE d'une opérette (genre distinct
            #   de l'opéra) ; titres d'opérette seulement (pas de redondance OPERAS) —
            "compositeur_operette",
            # — CANON round27 (run autonome 2026-06-27) : compositeur UNIQUE d'un oratorio (genre distinct ;
            #   Wikidata ~0 → canon) ; titres d'oratorio seulement —
            "compositeur_oratorio",
            # — CANON round28 (run autonome 2026-06-27) : compositeur UNIQUE d'un requiem (genre distinct ;
            #   titres qualifiés par le compositeur) —
            "compositeur_requiem",
            # — CANON round71 (run autonome 2026-06-27) : compositeur UNIQUE d'une zarzuela (genre espagnol
            #   distinct opéra/opérette) ; duos écartés —
            "compositeur_zarzuela"]
MES_RELATIONS = FERMEES + OUVERTES

# 1) PRÉSENCE
for r in MES_RELATIONS:
    t = L.LECTEUR.tables.get(r)
    check(f"PRÉSENCE : {r} existe et non vide", t is not None and len(t) > 0)

# 2) INTÉGRITÉ + STRUCTURE  ·  3) FERMETÉ RELATIVE
for r in MES_RELATIONS:
    t = L.LECTEUR.tables[r]
    mauvais = None
    valeurs = []
    for cle, fait in t.items():
        v = fait.valeur
        if mauvais is None and not (
                isinstance(v, str) and len(v.strip()) >= 2
                and fait.categorie in CATS
                and isinstance(fait.source, str) and fait.source.strip() != ""):
            mauvais = (r, cle, v)
        valeurs.append(v)
    check(f"STRUCTURE : {r} — tous faits valeur≥2car, cat∈CATS, source [contre-ex: {mauvais}]",
          mauvais is None)
    if r in FERMEES:
        ratio = len(set(valeurs)) / max(1, len(valeurs))
        check(f"FERMETÉ : {r} ratio distinct/faits = {ratio:.3f} < 0.20 "
              f"({len(set(valeurs))} valeurs / {len(valeurs)} faits)", ratio < 0.20)

# 4) ANCRES VÉRITÉ-TERRAIN — vérifiées à la main, indépendamment de la donnée ingérée.
ANCRES = {
    ("developpeur_jeu", "The Witcher 3 : Wild Hunt"): "CD Projekt RED",
    ("developpeur_jeu", "Portal 2"): "Valve Corporation",
    ("editeur_jeu", "Sonic the Hedgehog"): "Sega",
    ("editeur_jeu", "Portal 2"): "Valve Corporation",
    ("interprete_album", "Abbey Road"): "The Beatles",
    ("interprete_album", "Nevermind"): "Nirvana",
    ("interprete_album", "The Dark Side of the Moon"): "Pink Floyd",
    ("label_album", "Abbey Road"): "Apple Records",
    ("label_album", "Nevermind"): "Geffen Records",
    ("collection_peinture", "Guernica"): "musée national centre d'art Reina Sofía",
    ("collection_peinture", "La Jeune Fille à la perle"): "Mauritshuis",
    ("chaine_diffusion", "Breaking Bad"): "AMC",
    ("chaine_diffusion", "Les Soprano"): "HBO",
    ("scenariste_film", "Pulp Fiction"): "Roger Avary",
    ("societe_production_film", "1 001 pattes"): "Pixar Animation Studios",
    ("societe_production_film", "Les Aventures d'André et Wally B."): "Pixar Animation Studios",
    ("distributeur_film", "Le Seigneur des anneaux : La Communauté de l'anneau"): "New Line Cinema",
    ("auteur_oeuvre_ecrite", "Le Seigneur des anneaux"): "J. R. R. Tolkien",
    ("auteur_oeuvre_ecrite", "De la démocratie en Amérique"): "Alexis de Tocqueville",
    ("illustrateur_oeuvre_ecrite", "Astérix chez les Belges"): "Albert Uderzo",
    # — vague 2 (2026-06-26) : ancres vérité-terrain vérifiées à la main —
    ("compositeur_musique_film", "Les Dents de la mer"): "John Williams",
    ("compositeur_musique_film", "Le Parrain"): "Nino Rota",
    ("directeur_photo_film", "Citizen Kane"): "Gregg Toland",
    ("directeur_photo_film", "1917"): "Roger Deakins",
    ("monteur_film", "Pulp Fiction"): "Sally Menke",
    ("monteur_film", "Raging Bull"): "Thelma Schoonmaker",
    ("compositeur_jeu", "NieR: Automata"): "Keiichi Okabe",
    ("compositeur_jeu", "Undertale"): "Toby Fox",
    ("serie_jeu", "Portal 2"): "Portal",
    ("serie_jeu", "The Legend of Zelda: Ocarina of Time"): "The Legend of Zelda",
    ("maison_edition_oeuvre_ecrite", "Le Seigneur des anneaux"): "George Allen & Unwin",
    ("maison_edition_oeuvre_ecrite", "Fondation"): "Gnome Press",
    # — vague 3 (2026-06-26) : titres NON ambigus (cf. piège label_chanson(Yesterday)=Cherry Red, homonyme) —
    ("costumier_film", "Autant en emporte le vent"): "Walter Plunkett",
    ("costumier_film", "Black Panther"): "Ruth E. Carter",
    ("producteur_album", "Nevermind"): "Butch Vig",
    ("producteur_album", "OK Computer"): "Nigel Godrich",
    ("label_chanson", "Haru Haru"): "YG Entertainment",        # BIGBANG, 2008
    ("label_chanson", "10nen Sakura"): "King Records",         # AKB48, 2009
    # — vague 7 (2026-06-26) : architecture / sculpture / photographie (titres non ambigus) —
    ("architecte_edifice", "villa Savoye"): "Le Corbusier",
    ("architecte_edifice", "Sagrada Família"): "Antoni Gaudí",
    ("architecte_edifice", "maison sur la cascade"): "Frank Lloyd Wright",
    ("sculpteur_oeuvre", "Adam (Rodin)"): "Auguste Rodin",
    ("sculpteur_oeuvre", "L'Action enchaînée"): "Aristide Maillol",
    ("photographe_oeuvre", "Forêt de Fontainebleau"): "Gustave Le Gray",
    # — vague 8 (2026-06-26) : BD / manga (titres non ambigus) —
    ("auteur_manga", "Dragon Ball"): "Akira Toriyama",
    ("auteur_manga", "One Piece"): "Eiichirō Oda",
    ("auteur_manga", "Naruto"): "Masashi Kishimoto",
    ("dessinateur_bd", "Les Aventures de Tintin"): "Hergé",
    ("dessinateur_bd", "Largo Winch"): "Philippe Francq",
    # — vague 9 (2026-06-26) : estampe (Wikidata) + jeu de société (canon) —
    ("graveur_estampe", "La Grande Vague de Kanagawa"): "Hokusai",
    ("graveur_estampe", "Melencolia"): "Albrecht Dürer",
    ("auteur_jeu_societe", "Les Colons de Catane"): "Klaus Teuber",
    ("auteur_jeu_societe", "Pandémie"): "Matt Leacock",
    ("auteur_jeu_societe", "7 Wonders"): "Antoine Bauza",
    # — vague 10 (2026-06-26) : réalisateur de jeu vidéo —
    ("realisateur_jeu", "Metal Gear Solid"): "Hideo Kojima",
    ("realisateur_jeu", "Dark Souls"): "Hidetaka Miyazaki",
    ("realisateur_jeu", "Super Mario Bros."): "Shigeru Miyamoto",
    # — vague 11 (2026-06-26) : interprète d'un single (titres non ambigus) —
    ("interprete_single", "Billie Jean"): "Michael Jackson",
    ("interprete_single", "Smells Like Teen Spirit"): "Nirvana",
    # — vague 12 (2026-06-26) : chef décorateur (titres non ambigus) —
    ("chef_decorateur_film", "Blade Runner"): "Lawrence G. Paull",
    ("chef_decorateur_film", "Citizen Kane"): "Van Nest Polglase",
    ("chef_decorateur_film", "Le Parrain"): "Dean Tavoularis",
    # — vague 13 (2026-06-26) : dessin (artistes certains) + coloriste BD (Dave Stewart, Mignola-verse) —
    ("dessinateur_dessin", "Aile de Rollier bleu"): "Albrecht Dürer",
    ("dessinateur_dessin", "Allégorie au miroir solaire"): "Léonard de Vinci",
    ("coloriste_bd", "Abe Sapien"): "Dave Stewart",
    ("coloriste_bd", "Batman et le Moine fou"): "Dave Stewart",
    # — vague 14 (2026-06-26) : concepteur de jeu vidéo (designers uniques incontestés) —
    ("concepteur_jeu", "Populous"): "Peter Molyneux",
    ("concepteur_jeu", "Dragon Quest"): "Yūji Horii",
    ("concepteur_jeu", "Braid"): "Jonathan Blow",
    ("concepteur_jeu", "Katamari Damacy"): "Keita Takahashi",
    ("concepteur_jeu", "Ultima I"): "Richard Garriott",
    # — vague 15 (2026-06-26) : hymne — compositeur (P86) et parolier (P676), attributions indiscutables —
    ("compositeur_hymne", "La Marseillaise"): "Rouget de Lisle",
    ("compositeur_hymne", "A Portuguesa"): "Alfredo Keil",
    ("compositeur_hymne", "Giovinezza"): "Giuseppe Blanc",
    ("parolier_hymne", "A Portuguesa"): "Henrique Lopes de Mendonça",
    ("parolier_hymne", "Kde domov můj"): "Josef Kajetán Tyl",
    ("parolier_hymne", "Mer Hayrenik"): "Michael Nalbandian",
    # — vague 16 (2026-06-26) : installation d'art (artistes indiscutables) —
    ("createur_installation_art", "Comedian"): "Maurizio Cattelan",
    ("createur_installation_art", "The Weather Project"): "Ólafur Elíasson",
    ("createur_installation_art", "The Gates"): "Christo et Jeanne-Claude",
    # — vague 17 (2026-06-26) : facture instrumentale (modèles à fabricant indiscutable) —
    ("fabricant_guitare", "Gibson Nighthawk"): "Gibson Guitar Corporation",
    ("fabricant_guitare", "Gretsch 6128"): "Gretsch",
    ("fabricant_synthetiseur", "Novachord"): "Hammond",
    ("fabricant_synthetiseur", "Oberheim OB-8"): "Oberheim",
    ("fabricant_piano", "Welte-Mignon"): "M. Welte & Söhne",
    # — CANON v15 (2026-06-26) : créateur de police d'écriture (type designers indiscutables) —
    ("createur_police_ecriture", "Futura"): "Paul Renner",
    ("createur_police_ecriture", "Comic Sans"): "Vincent Connare",
    ("createur_police_ecriture", "Gill Sans"): "Eric Gill",
    ("createur_police_ecriture", "Verdana"): "Matthew Carter",
    ("createur_police_ecriture", "Gotham"): "Tobias Frere-Jones",
    # — CANON v16 (2026-06-26) : créateur de langage de programmation (créateurs uniques incontestés) —
    # NB : C / C++ / C# fusionnent en clé "c" via normalise() (ponctuation écrasée) -> multi -> HORS
    # (sound, pas un faux) ; on n'ancre donc PAS de nom ponctué. Ancres sur noms non ambigus :
    ("createur_langage_programmation", "Python"): "Guido van Rossum",
    ("createur_langage_programmation", "Java"): "James Gosling",
    ("createur_langage_programmation", "Ruby"): "Yukihiro Matsumoto",
    ("createur_langage_programmation", "Perl"): "Larry Wall",
    ("createur_langage_programmation", "Rust"): "Graydon Hoare",
    # — CANON v17 (2026-06-26) : créateur/showrunner de série télévisée (créateurs uniques incontestés) —
    ("createur_serie_television", "Breaking Bad"): "Vince Gilligan",
    ("createur_serie_television", "The Wire"): "David Simon",
    ("createur_serie_television", "Les Soprano"): "David Chase",
    ("createur_serie_television", "Mad Men"): "Matthew Weiner",
    ("createur_serie_television", "Les Simpson"): "Matt Groening",
    # — CANON v18 (2026-06-26) : créateur de logiciel emblématique (créateurs uniques incontestés) —
    ("createur_logiciel", "Linux"): "Linus Torvalds",
    ("createur_logiciel", "Git"): "Linus Torvalds",
    ("createur_logiciel", "Vim"): "Bram Moolenaar",
    ("createur_logiciel", "SQLite"): "D. Richard Hipp",
    ("createur_logiciel", "Blender"): "Ton Roosendaal",
    # — CANON modèle (2026-06-26) : attributions indiscutables (titre non ambigu) —
    ("compositeur_opera", "La traviata"): "Giuseppe Verdi",
    ("compositeur_opera", "Carmen"): "Georges Bizet",
    ("compositeur_opera", "La Bohème"): "Giacomo Puccini",
    ("compositeur_opera", "Don Giovanni"): "Wolfgang Amadeus Mozart",
    ("compositeur_opera", "Tristan und Isolde"): "Richard Wagner",
    ("compositeur_comedie_musicale", "West Side Story"): "Leonard Bernstein",
    ("compositeur_comedie_musicale", "The Phantom of the Opera"): "Andrew Lloyd Webber",
    ("compositeur_comedie_musicale", "Les Misérables"): "Claude-Michel Schönberg",
    ("compositeur_comedie_musicale", "Sweeney Todd"): "Stephen Sondheim",
    ("compositeur_ballet", "Le Lac des cygnes"): "Piotr Ilitch Tchaïkovski",
    ("compositeur_ballet", "Le Sacre du printemps"): "Igor Stravinsky",
    ("compositeur_ballet", "Giselle"): "Adolphe Adam",
    ("librettiste_opera", "Don Giovanni"): "Lorenzo Da Ponte",
    ("librettiste_opera", "Otello"): "Arrigo Boito",
    ("librettiste_opera", "Rigoletto"): "Francesco Maria Piave",
    ("parolier_comedie_musicale", "Jesus Christ Superstar"): "Tim Rice",
    ("parolier_comedie_musicale", "Oklahoma!"): "Oscar Hammerstein II",
    ("parolier_comedie_musicale", "Cabaret"): "Fred Ebb",
    # CANON v19 — librettiste (auteur du livret/« book ») : titres NON ambigus, duos écartés
    ("librettiste_comedie_musicale", "Cabaret"): "Joe Masteroff",
    ("librettiste_comedie_musicale", "Fiddler on the Roof"): "Joseph Stein",
    ("librettiste_comedie_musicale", "Wicked"): "Winnie Holzman",
    # CANON v20 — inventeur d'instrument : attributions brevetées/universelles, non ambiguës
    ("inventeur_instrument_musique", "saxophone"): "Adolphe Sax",
    ("inventeur_instrument_musique", "thérémine"): "Léon Theremin",
    ("inventeur_instrument_musique", "ondes Martenot"): "Maurice Martenot",
    # CANON v21 — parfumeur : attributions établies, non ambiguës
    ("parfumeur_parfum", "Chanel N°5"): "Ernest Beaux",
    ("parfumeur_parfum", "Eau Sauvage"): "Edmond Roudnitska",
    ("parfumeur_parfum", "Fracas"): "Germaine Cellier",
    # CANON v22 — jeu de rôle : titres distinctifs, auteur unique certain
    ("auteur_jeu_role", "Vampire: The Masquerade"): "Mark Rein·Hagen",
    ("auteur_jeu_role", "GURPS"): "Steve Jackson",
    ("auteur_jeu_role", "Cyberpunk 2020"): "Mike Pondsmith",
    # CANON v23 — objet de design : pièces iconiques, designer unique certain
    ("createur_objet_design", "Chaise Panton"): "Verner Panton",
    ("createur_objet_design", "Chaise Louis Ghost"): "Philippe Starck",
    ("createur_objet_design", "Lampe Anglepoise"): "George Carwardine",
    # CANON round10 — langue construite (conlang), créateur unique certain
    ("createur_langue_construite", "Espéranto"): "Louis-Lazare Zamenhof",
    ("createur_langue_construite", "Klingon"): "Marc Okrand",
    ("createur_langue_construite", "Na'vi"): "Paul Frommer",
    # CANON round11 — logo iconique, designer unique certain
    ("createur_logo", "logo Nike"): "Carolyn Davidson",
    ("createur_logo", "logo Apple"): "Rob Janoff",
    ("createur_logo", "logo IBM"): "Paul Rand",
    # CANON round12 — chorégraphe d'un ballet-repère, attribution unique certaine
    ("choregraphe_ballet", "Le Sacre du printemps"): "Vaslav Nijinsky",
    ("choregraphe_ballet", "La Belle au bois dormant"): "Marius Petipa",
    ("choregraphe_ballet", "Apollon musagète"): "George Balanchine",
    # CANON round13 — jardin-repère, concepteur/paysagiste unique certain
    ("paysagiste_jardin", "jardins de Versailles"): "André Le Nôtre",
    ("paysagiste_jardin", "Parc Güell"): "Antoni Gaudí",
    ("paysagiste_jardin", "jardin de Giverny"): "Claude Monet",
    # CANON round15 — drapeau, designer unique documenté
    ("createur_drapeau", "drapeau du Canada"): "George F. G. Stanley",
    ("createur_drapeau", "drapeau de l'Inde"): "Pingali Venkayya",
    ("createur_drapeau", "drapeau de la fierté LGBT"): "Gilbert Baker",
    # CANON round19 — système d'écriture, inventeur unique certain
    ("createur_systeme_ecriture", "alphabet braille"): "Louis Braille",
    ("createur_systeme_ecriture", "hangeul"): "Sejong le Grand",
    ("createur_systeme_ecriture", "syllabaire cherokee"): "Sequoyah",
    # WIKIDATA round21 — compositeur musique de série TV (single-composer ; vérifiés à la main)
    ("compositeur_musique_serie", "Moon Knight"): "Hesham Nazih",
    ("compositeur_musique_serie", "Poupée russe"): "Joe Wong",
    ("compositeur_musique_serie", "L'Extravagante Lucy"): "Wilbur Hatch",
    # CANON round25 — chorégraphe de comédie musicale (production originale)
    ("choregraphe_comedie_musicale", "West Side Story"): "Jerome Robbins",
    ("choregraphe_comedie_musicale", "Chicago"): "Bob Fosse",
    ("choregraphe_comedie_musicale", "A Chorus Line"): "Michael Bennett",
    # CANON round26 — compositeur d'opérette
    ("compositeur_operette", "La Chauve-Souris"): "Johann Strauss II",
    ("compositeur_operette", "La Veuve joyeuse"): "Franz Lehár",
    ("compositeur_operette", "The Mikado"): "Arthur Sullivan",
    # CANON round27 — compositeur d'oratorio
    ("compositeur_oratorio", "Le Messie"): "Georg Friedrich Haendel",
    ("compositeur_oratorio", "La Création"): "Joseph Haydn",
    ("compositeur_oratorio", "Elias"): "Felix Mendelssohn",
    # CANON round28 — compositeur de requiem
    ("compositeur_requiem", "Requiem de Mozart"): "Wolfgang Amadeus Mozart",
    ("compositeur_requiem", "Un requiem allemand"): "Johannes Brahms",
    ("compositeur_requiem", "War Requiem"): "Benjamin Britten",
    # CANON round71 — compositeur de zarzuela
    ("compositeur_zarzuela", "La verbena de la Paloma"): "Tomás Bretón",
    ("compositeur_zarzuela", "Doña Francisquita"): "Amadeo Vives",
    ("compositeur_zarzuela", "Luisa Fernanda"): "Federico Moreno Torroba",
}
for (rel, ent), attendu in ANCRES.items():
    st, f = L.repond(rel, ent)
    check(f"ANCRE : {rel}({ent}) = {attendu!r} [obtenu: {st},{getattr(f,'valeur',None)!r}]",
          st == VERIFIE and f is not None and f.valeur == attendu)

# 5) SOUNDNESS ADVERSE — entité absente / relation absente -> (HORS, None), jamais un faux.
INCONNUS = [
    ("developpeur_jeu", "jeu video totalement inexistant qwxyz 999999"),
    ("collection_peinture", "peinture imaginaire absente zzzzz 424242"),
    ("interprete_album", "album fantome inexistant kkkkk 707070"),
    ("auteur_oeuvre_ecrite", "livre qui n existe pas du tout vvvvv 131313"),
    ("relation_t5_inexistante_zzz", "n importe quoi"),
]
for rel, ent in INCONNUS:
    st, f = L.repond(rel, ent)
    check(f"HORS : {rel}({ent}) -> (HORS,None) [obtenu: {st},{f}]", st == HORS and f is None)

print(f"\n=== VALIDE_LECTEUR_T5 : {ok}/{total} ===")
import sys
sys.exit(0 if ok == total else 1)
