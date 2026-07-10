"""
VALIDATEUR T6 — sanité FAUX=0 des relations PERSONNES & ORGANISATIONS (OFFLINE).

Charge UNIQUEMENT les datasets T6 dans un Lecteur frais (léger : pas le chargement complet 10 M faits)
et vérifie, sans réseau :
  • ENSEMBLES FERMÉS (sexe_personne, langue_maternelle, secteur_entreprise) : on RE-DÉRIVE la propriété de
    fermeture depuis la donnée réellement ingérée (ratio distinct/entités bas) + chaque valeur non vide ≥2
    car. avec une lettre + CONTRÔLE POSITIF (valeurs-noyau attendues présentes). Pas de N magique.
  • VOCAB OUVERT (fondateur_organisation, maison_mere) : chaque valeur plausible (a une lettre, ≥2 car.) +
    ANCRES vérité-terrain (paires connues org→fondateur / entreprise→maison-mère résolues exactement).
`fonctionnel` (à l'ingestion) garantit déjà 1 valeur/entité (multi -> HORS). EXIT 0 = tous les checks PASS.
"""
# ─── GARDE « BASE COMPLÈTE » (2026-07-12) — SKIP propre sur l'échantillon ───
# Gate de classe BASE RÉELLE (72 M). Sur l'échantillon committé (que _nonreg épingle) sa donnée est
# absente et ses ancres tomberaient en FAUX-échec. Marqueur de base réelle : occupation_personne (2,35 M,
# jamais committé). Base réelle vérifiée par la passe manuelle valide_lecteur* (cf. CHANGELOG). Une gate
# honnête SKIPPE quand sa donnée manque, elle ne tombe pas.
import os as _os, sys as _sys
_bc = _os.environ.get("LECTEUR_DATASETS_DIR")
if _bc and not _os.path.exists(_os.path.join(_bc, "occupation_personne.jsonl")):
    print("=== valide_lecteur_t6 : SKIP — base complète requise (occupation_personne absent de ce store) ===")
    _sys.exit(0)
# ──────────────────────────────────────────────────────

from garde_ressources import borne
borne(max_go=5.0, max_cpu_s=1500)   # OPTIM amorce-seule : per-relation (Lecteur frais), pic = prenom seul (~2,68 M) ; plus de full-load global

import os
import sys
import unicodedata

os.environ.setdefault("LECTEUR_AMORCE_SEULE", "1")  # OPTIM gate légère : charge SES relations dans un Lecteur frais (jamais le singleton global L.LECTEUR) → saute charge_dossier()+gele() sur les 33,5 M faits (~5 Go/min)
import lecteur as L

_DS = os.environ.get("LECTEUR_DATASETS_DIR") or os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "datasets", "lecteur")

_ECHECS = []


def check(cond, message):
    etat = "OK " if cond else "FAIL"
    print(f"  [{etat}] {message}")
    if not cond:
        _ECHECS.append(message)
    return cond


def _norm(s: str) -> str:
    """minuscule + sans accents, pour comparer des valeurs (contrôle positif tolérant aux accents)."""
    s = unicodedata.normalize("NFD", str(s).lower())
    return "".join(c for c in s if unicodedata.category(c) != "Mn").strip()


def _a_une_lettre(v: str) -> bool:
    return any(c.isalpha() for c in v)


# ---- en-têtes attendus (catégorie déclarée par chaque dataset) ----
_RELATIONS = {
    "sexe_personne":          "physique",
    "langue_maternelle":      "physique",
    "secteur_entreprise":     "convention",
    "religion_personne":      "convention",
    "diplome_universitaire":  "convention",
    "mouvement_personne":     "convention",
    "langue_parlee":          "physique",
    "lateralite_personne":    "physique",
    "langue_ecriture":        "physique",
    "type_voix":              "physique",
    "prix_recu_personne":     "passe",
    "instrument_joue":        "convention",
    "branche_militaire":      "convention",
    "domaine_travail":        "convention",
    "occupation_personne":    "convention",
    "bourse_cotation":        "convention",
    "nomine_pour":            "passe",
    "poste_occupe":           "passe",
    "cause_deces":            "passe",
    "pere_personne":          "physique",
    "mere_personne":          "physique",
    "conjoint_personne":      "convention",
    "eleve_de":               "passe",
    "etudie_a":               "passe",
    "employeur_personne":     "passe",
    "membre_de":              "convention",
    "directeur_these":        "passe",
    "proprietaire_organisation": "convention",
    "fondateur_organisation": "passe",
    "maison_mere":            "physique",
    "prenom":                 "physique",
    "nom_famille":            "physique",
    "systeme_cristallin":     "physique",
    "couleur_trait_mineral":  "physique",
    "periode_personne":       "convention",
    "mode_jeu_video":         "convention",
    "couleur_film":           "physique",
    "materiau_construction":  "physique",
    "materiau_monnaie":       "physique",
    "materiau_meuble":        "physique",
    "materiau_vase":          "physique",
    "materiau_pont":          "physique",
    "materiau_cloche":        "physique",
    "materiau_manuscrit":     "physique",
    "materiau_calice":        "physique",
    "materiau_chaire":        "physique",
    "robe_cheval":            "physique",
    "diocese_eglise":         "convention",
    "plateforme_jeu":         "convention",
    "format_distribution_film": "convention",
    "format_album":           "convention",
    "format_distribution_jeu": "convention",
    "format_image_film":      "convention",
    "couleur_serie":          "physique",
    "couleur_episode":        "physique",
    "format_image_serie":     "convention",
    "format_distribution_serie": "convention",
    "format_single":          "convention",
    "format_edition":         "convention",
}

# ---- contrôles positifs des ENSEMBLES FERMÉS : au moins K valeurs-noyau présentes (comparaison _norm) ----
_NOYAU = {
    "sexe_personne":      (["masculin", "feminin"], 2),
    "periode_personne":   (["haut-empire romain", "empire romain", "antiquite classique", "epoque hellenistique"], 3),                       # les 2 valeurs dominantes humaines
    "langue_maternelle":  (["francais", "anglais", "espagnol", "allemand",
                            "italien", "russe", "portugais"], 2),
    "secteur_entreprise": (["industrie videoludique", "commerce de detail",
                            "construction automobile", "service financier",
                            "telecommunications", "industrie du logiciel", "edition"], 3),
    # noyau dérivé du fichier réel (top valeurs vérifiées présentes ; _norm = sans accents)
    "religion_personne":  (["catholicisme", "islam", "judaisme", "lutheranisme",
                            "anglicanisme", "protestantisme", "hindouisme",
                            "bouddhisme", "calvinisme"], 5),
    "langue_ecriture":    (["anglais", "italien", "francais", "allemand", "japonais",
                            "russe", "espagnol", "latin", "portugais"], 5),
    # diplômes/grades académiques RÉELS (ratio 0.008) ; noyau = grades que je connais, confirmés présents.
    "diplome_universitaire": (["doctorat", "docteur en philosophie", "laurea", "docteur en droit",
                              "docteur en medecine", "maitrise", "baccalaureat es arts",
                              "master of science"], 5),
    # langues (capacité P1412) ; ratio infime 0.00043 ; noyau = langues majeures confirmées présentes.
    "langue_parlee":      (["anglais", "allemand", "francais", "espagnol", "italien",
                            "japonais", "portugais", "russe", "neerlandais", "arabe"], 5),
    # latéralité : ensemble fermé STRICT à 3 valeurs, toutes confirmées présentes (contrôle positif).
    "lateralite_personne": (["droitier", "gaucher", "ambidextrie"], 2),
    "type_voix":          (["soprano", "tenor", "baryton", "mezzo-soprano",
                            "basse", "contralto"], 4),
    # prix : vocabulaire de distinctions RÉELLES (ratio bas 0.042) ; noyau = prix que je connais
    # indépendamment, confirmés présents dans la donnée (contrôle positif = parse honnête, pas du bruit).
    "prix_recu_personne": (["juste parmi les nations", "chevalier de la legion d'honneur",
                            "officier de la legion d'honneur", "bourse guggenheim",
                            "knight bachelor"], 3),
    "instrument_joue":    (["piano", "guitare", "violon", "orgue", "batterie",
                            "saxophone", "voix"], 4),
    "branche_militaire":  (["british army", "royal navy", "united states navy",
                            "royal air force", "infanterie",
                            "armee de terre des etats-unis"], 3),
    "cause_deces":        (["cancer", "infarctus du myocarde", "pneumonie",
                            "tuberculose", "accident vasculaire cerebral"], 4),
    "domaine_travail":    (["peinture", "histoire", "musique", "botanique",
                            "litterature", "mathematiques", "architecture"], 4),
    "occupation_personne": (["personnalite politique", "footballeur ou footballeuse",
                             "acteur ou actrice", "ecrivain ou ecrivaine",
                             "journaliste", "architecte"], 4),
    "poste_occupe":       (["depute", "president ou presidente", "maire",
                            "eveque diocesain", "recteur",
                            "directeur ou directrice"], 4),
    "bourse_cotation":    (["new york stock exchange", "nasdaq", "bourse de hong kong",
                            "bourse de tokyo", "bourse de londres", "euronext paris"], 4),
    "nomine_pour":        (["prix nobel de litterature", "prix nobel de physique",
                            "prix nobel de chimie", "oscar du meilleur film",
                            "prix booker"], 3),
    # minéralogie : ensemble fermé des 7 systèmes cristallins IAU (+ matière amorphe / quasi-cristal hors noyau).
    "systeme_cristallin": (["systeme cristallin cubique", "systeme cristallin trigonal",
                            "systeme cristallin hexagonal", "systeme cristallin monoclinique",
                            "systeme cristallin orthorhombique", "systeme cristallin triclinique",
                            "systeme cristallin tetragonal"], 5),
    # couleur du trait (streak) : ensemble fermé de couleurs (blanc domine ; ~20 teintes).
    "couleur_trait_mineral": (["blanc", "noir", "brun", "jaune", "gris", "vert", "rouge"], 4),
    # mode de jeu vidéo (P404) : ensemble fermé STRICT de 11 modes whitelistés (ratio ~0.001 ; non-modes/genres
    # rejetés à l'ingestion). Noyau = modes confirmés présents dans la donnée réelle (solo domine).
    "mode_jeu_video":     (["solo", "multijoueur", "mode cooperatif", "jeu en ligne"], 3),
    # statut couleur du film (P462) : ensemble fermé STRICT (couleur vs noir et blanc ; bruit formats/procédés/
    # noms rejeté à l'ingestion). ratio ~0.00005. Noyau = les 2 statuts canoniques confirmés présents.
    "couleur_film":       (["couleur", "noir et blanc"], 2),
    # matériau de construction du bâti (P186) : vocab semi-ouvert de matériaux réels (ratio ~0.025 ; non-matériaux
    # blocklistés à l'ingestion). Noyau = matériaux courants confirmés présents.
    "materiau_construction": (["pierre", "brique", "bois", "beton de ciment", "acier",
                               "calcaire", "marbre", "granite"], 4),
    # métal de frappe de la monnaie (P186) : ensemble fermé de métaux monétaires (ratio ~0.004). Noyau =
    # métaux courants confirmés présents (numismatique).
    "materiau_monnaie":   (["argent", "bronze", "or", "cuivre", "billon"], 3),
    # matériau du mobilier (P186) : vocab semi-ouvert (ratio bas ; médias picturaux blocklistés). Noyau =
    # matériaux d'ameublement courants confirmés présents.
    "materiau_meuble":    (["bois", "pierre", "bois de chene", "marbre", "metal", "calcaire"], 4),
    # matériau du vase/récipient (P186) : vocab semi-ouvert d'arts décoratifs (ratio bas ; technique blocklistée).
    "materiau_vase":      (["terre cuite", "porcelaine", "faience", "ceramique", "verre", "argile"], 4),
    # matériau du pont (P186) : ensemble fermé de matériaux de génie civil (ratio ~0.03 ; intrus blocklistés).
    "materiau_pont":      (["acier", "pierre", "beton de ciment", "beton arme", "bois", "fer"], 4),
    # matériau de la cloche (P186/Q101401) : ensemble fermé (bronze dominant ; vague blocklisté). QID vérifié.
    "materiau_cloche":    (["bronze", "fer", "fonte", "argent"], 3),
    "materiau_manuscrit": (["papier", "parchemin", "velin", "papyrus"], 3),
    "materiau_calice":    (["argent", "metal", "etain", "cuivre"], 3),
    "materiau_chaire":    (["bois", "pierre", "marbre", "bois de chene"], 3),
    # couleur de robe du cheval (P462) : ensemble fermé de robes équines (ratio ~0.007 ; gènes blocklistés).
    "robe_cheval":        (["gris", "alezan", "bai", "noir", "bai fonce"], 3),
    # diocèse de rattachement de l'église (P708) : ensemble (quasi-)fermé de juridictions ecclésiales (ratio
    # ~0.043 ; dénominations non-diocèse écartées par whitelist). Noyau = diocèses FR majeurs confirmés présents.
    "diocese_eglise":     (["diocese d'arras", "diocese de metz", "diocese d'amiens",
                            "archidiocese de strasbourg", "archidiocese de besancon"], 3),
    # plateforme du jeu vidéo (P400) : ensemble fermé de plateformes (ratio ~0.013 ; non-plateformes blocklistées).
    "plateforme_jeu":     (["microsoft windows", "nintendo ds", "playstation 3", "amiga", "super nintendo"], 3),
    # format de distribution du film (P437) : ensemble fermé de formats (ratio ~0.001 ; non-formats blocklistés).
    "format_distribution_film": (["video a la demande", "sortie en salle", "vhs", "disque blu-ray"], 3),
    # format de parution de l'album (P437) : ensemble fermé de supports (ratio ~0.0015 ; non-formats blocklistés).
    "format_album":       (["disque compact", "disque vinyle", "long play", "cassette audio", "streaming musical"], 3),
    # format de distribution du jeu vidéo (P437) : ensemble fermé de supports (ratio ~0.005 ; bruit whitelisté).
    "format_distribution_jeu": (["distribution numerique", "telechargement numerique",
                                 "cartouche de jeu video", "cd-rom", "disquette"], 3),
    # format d'image nommé du film (P2061) : ensemble fermé de rapports de cadre nommés (ratio ~0.001).
    "format_image_film":  (["format 4/3", "format 16/9", "format academique", "format 2,35/1"], 3),
    # statut couleur de la série TV (P462) : ensemble fermé (couleur/noir et blanc ; bruit whitelisté).
    "couleur_serie":      (["couleur", "noir et blanc"], 2),
    "couleur_episode":    (["couleur", "noir et blanc"], 2),
    # format d'image nommé de la série TV (P2061) : ensemble fermé de rapports de cadre nommés (ratio bas).
    "format_image_serie": (["format 16/9", "format 4/3", "format 2/1"], 3),
    # format de distribution de la série TV (P437) : ensemble fermé (ratio bas ; non-formats blocklistés).
    "format_distribution_serie": (["video a la demande", "streaming", "disque blu-ray", "telediffusion"], 3),
    # format de parution du single (P437) : ensemble fermé de supports musicaux (ratio bas ; non-formats blocklistés).
    "format_single":      (["disque compact", "streaming musical", "disque vinyle", "single 7''"], 3),
    "format_edition":     (["livre broche", "livre imprime", "livre numerique", "in-octavo"], 3),
}
_RATIO_MAX_FERME = 0.20   # distinct/entités : confirme la fermeture vue au scout (sexe 0.01, secteur 0.08)

# ---- ANCRES vocab ouvert : paires confirmées présentes dans la donnée ingérée (renseignées post-ingestion) ----
_ANCRES = {
    "fondateur_organisation": [
        # célèbres, vérité connue indépendamment (mono-fondateur ; Microsoft/Tesla/Facebook = multi -> HORS = OK)
        ("SpaceX", "Elon Musk"),
        ("Amazon", "Jeff Bezos"),
        # confirmées présentes dans la donnée ingérée (lookup clé->valeur cohérent)
        ("Xiph.org", "Chris Montgomery"),
        ("Gulagu.net", "Vladimir Ossetchkine"),
        ("Oriental Land Company", "Chiharu Kawasaki"),
    ],
    "maison_mere": [
        # célèbres, vérité connue indépendamment (Audi détient Lamborghini ; VW détient Bentley)
        ("Lamborghini", "Audi"),
        ("Bentley", "Volkswagen"),
        ("UNIQLO", "Fast Retailing"),
        # confirmées présentes dans la donnée ingérée
        ("Dreambaby", "Colruyt Group"),
        ("Busy Bee", "Braathens"),
        ("Orange Espagne", "MásOrange"),
    ],
    "pere_personne": [
        # filiations célèbres, vérité connue indépendamment + confirmées présentes
        ("Charles III", "Philip Mountbatten"),
        ("Louis XIV", "Louis XIII"),
        ("Élisabeth II", "George VI"),
        ("Alexandre le Grand", "Philippe II de Macédoine"),
        ("Indira Gandhi", "Jawaharlal Nehru"),
    ],
    "mere_personne": [
        ("Charles III", "Élisabeth II"),
        ("Louis XIV", "Anne d'Autriche"),
        ("Élisabeth II", "Elizabeth Bowes-Lyon"),
        ("Alexandre le Grand", "Olympias"),
        ("Indira Gandhi", "Kamala Nehru"),
    ],
    "conjoint_personne": [
        # couples monogames célèbres, vérité connue indépendamment + confirmés présents
        ("Hillary Clinton", "Bill Clinton"),
        ("Bill Clinton", "Hillary Clinton"),
        ("Pierre Curie", "Marie Curie"),
        ("Marie Curie", "Pierre Curie"),
        ("Franklin Delano Roosevelt", "Eleanor Roosevelt"),
    ],
    "eleve_de": [
        # lignées maître-élève célèbres, vérité connue indépendamment + confirmées présentes
        ("Aristote", "Platon"),
        ("Dicéarque", "Aristote"),
        ("Antisthène", "Socrate"),
        ("Le Pérugin", "Andrea del Verrocchio"),
        ("Lorenzo di Credi", "Andrea del Verrocchio"),
    ],
    "directeur_these": [
        # lignées doctorales de physique célèbres, vérité connue indépendamment (libellés non ambigus)
        ("Werner Heisenberg", "Arnold Sommerfeld"),
        ("Wolfgang Pauli", "Arnold Sommerfeld"),
        ("Louis de Broglie", "Paul Langevin"),
        ("Paul Dirac", "Ralph H. Fowler"),
        ("Enrico Fermi", "Luigi Puccianti"),
    ],
    "membre_de": [
        # membres célèbres d'UNE société savante (vérité connue indépendamment, libellés non ambigus)
        ("Isaac Newton", "Royal Society"),
        ("Edmond Halley", "Royal Society"),
        ("Christopher Wren", "Royal Society"),
        ("Joseph Banks", "Royal Society"),
        ("Jean de La Fontaine", "Académie française"),
    ],
    "employeur_personne": [
        # académiques célèbres rattachés à UNE institution (vérité connue indépendamment) ; valeurs diverses
        ("Noam Chomsky", "Institut de technologie du Massachusetts"),
        ("Alan Guth", "Institut de technologie du Massachusetts"),
        ("Carl Sagan", "Université Cornell"),
        ("Alan Blinder", "Université de Princeton"),
        ("Abraham Verghese", "Université Stanford"),
    ],
    "etudie_a": [
        # généraux célèbres = cadets à institution UNIQUE (vérité connue indépendamment, libellés non ambigus) ;
        # la distribution des valeurs est diverse (Vienne/Tokyo/Harvard/ENA…) -> pas un biais « tout West Point ».
        ("Ulysses S. Grant", "Académie militaire de West Point"),
        ("George Armstrong Custer", "Académie militaire de West Point"),
        ("Thomas Jonathan Jackson", "Académie militaire de West Point"),
        ("William Tecumseh Sherman", "Académie militaire de West Point"),
        ("Abner Doubleday", "Académie militaire de West Point"),
    ],
    "mouvement_personne": [
        # mouvements artistiques de fondateurs/figures célèbres, vérité connue indépendamment + confirmés
        # présents (libellés non ambigus : on ÉCARTE « William Turner » = homonyme musicien baroque, pas le peintre).
        ("Claude Monet", "impressionnisme"),
        ("Salvador Dalí", "surréalisme"),
        ("André Breton", "surréalisme"),
        ("Gustave Courbet", "réalisme"),
        ("Eugène Delacroix", "romantisme"),
    ],
    "systeme_cristallin": [
        # minéraux à système cristallin connu indépendamment (cristallographie classique) ; ENTITÉ -> valeur exacte.
        ("diamant", "système cristallin cubique"),
        ("quartz", "système cristallin trigonal"),
        ("halite", "système cristallin cubique"),
        ("calcite", "système cristallin trigonal"),
        ("graphite", "système cristallin hexagonal"),
    ],
    "couleur_trait_mineral": [
        # couleur du trait connue indépendamment (minéralogie déterminative) ; ENTITÉ -> valeur exacte.
        ("pyrite", "noir"),
        ("magnétite", "noir"),
        ("graphite", "noir"),
        ("rhodochrosite", "blanc"),
        ("azurite", "bleu clair"),
    ],
    "proprietaire_organisation": [
        # propriétés célèbres, vérité connue indépendamment + confirmées présentes dans la donnée
        ("AbeBooks", "Amazon"),
        ("Audible.com", "Amazon"),
        ("Bethesda Softworks", "Microsoft"),
        ("Bulgari", "LVMH"),
        ("Berluti", "LVMH"),
    ],
    "prenom": [
        # personnes célèbres mono-prénom (HAVING=1), vérité connue indépendamment + confirmées présentes.
        # (Marie Curie / Napoléon = plusieurs prénoms -> exclus par HAVING=1 = OK.)
        ("Albert Einstein", "Albert"),
        ("Isaac Newton", "Isaac"),
        ("Louis Pasteur", "Louis"),
        ("Charles Darwin", "Charles"),
        ("Léonard de Vinci", "Leonardo"),
    ],
    "nom_famille": [
        # noms de famille de personnes célèbres mono-nom (HAVING=1), vérité connue + confirmées présentes.
        ("Albert Einstein", "Einstein"),
        ("Charles Darwin", "Darwin"),
        ("Louis Pasteur", "Pasteur"),
        ("Max Planck", "Planck"),
        ("Léonard de Vinci", "da Vinci"),
    ],
}


def _charge(lec: "L.Lecteur", relation: str, categorie: str) -> dict:
    chemin = os.path.join(_DS, relation + ".jsonl")
    if not os.path.exists(chemin):
        check(False, f"{relation} : dataset absent ({chemin})")
        return {}
    # OPTIM nuit 2026-06-29 : chemin RAPIDE via le cache columnar mmap (.colf) -> chargement quasi-instantané +
    # demand-paged (pas de re-parse JSON), pic RAM = pages touchées de CETTE seule relation (bornage préservé).
    # Résultats IDENTIQUES (prouvé par hash A/B sur 65 M faits). Repli charge_jsonl si .colf absent/périmé.
    mct, _mrel, mart = L._charge_colf_mmap(relation + ".jsonl", chemin)
    if mct is not None:
        lec.tables[relation] = mct
        lec.norm_articles.setdefault(relation, mart)
        return mct
    # charge_dossier lit l'en-tête self-describing ; ici on charge un fichier précis via charge_jsonl en
    # sautant l'en-tête (charge_jsonl ignore la ligne _relation). categorie/source repris de l'en-tête réel.
    import json
    with open(chemin, encoding="utf-8") as fh:
        tete = json.loads(fh.readline())
    src = tete.get("_source", "T6")
    cat = tete.get("_categorie", categorie)
    arts = bool(tete.get("_articles", True))
    lec.charge_jsonl(relation, chemin, cat, src, articles=arts)
    return lec.tables.get(relation, {})


def valide_ferme(lec, relation):
    t = _charge(lec, relation, _RELATIONS[relation])
    if not t:
        return
    n_ent = len(t)
    valeurs = [f.valeur for f in t.values()]
    distinct = set(valeurs)
    ratio = len(distinct) / n_ent if n_ent else 1.0
    print(f"-- {relation} : {n_ent} entités, {len(distinct)} valeurs distinctes, ratio={ratio:.3f}")
    check(n_ent > 0, f"{relation} : table non vide")
    check(ratio <= _RATIO_MAX_FERME,
          f"{relation} : fermeture OK (ratio {ratio:.3f} ≤ {_RATIO_MAX_FERME})")
    check(all(len(v.strip()) >= 2 and _a_une_lettre(v) for v in distinct),
          f"{relation} : toutes les valeurs ≥2 car. avec lettre")
    noyau, k = _NOYAU[relation]
    presents = {_norm(v) for v in distinct}
    trouves = [c for c in noyau if c in presents]
    check(len(trouves) >= k,
          f"{relation} : contrôle positif {len(trouves)}/{k}+ valeurs-noyau présentes ({trouves[:4]})")
    # Renfort FAUX=0 : si des ancres ENTITÉ->valeur sont renseignées (vérité-terrain connue indépendamment),
    # on vérifie le lookup exact (au-delà du simple contrôle de présence des valeurs).
    ancres = _ANCRES.get(relation)
    if ancres:
        ok = 0
        for ent, attendu in ancres:
            f = lec.cherche(relation, ent)
            bon = f is not None and _norm(f.valeur) == _norm(attendu)
            if not bon:
                print(f"     ancre RATÉE : {ent!r} -> {f.valeur if f else 'HORS'!r} (attendu {attendu!r})")
            ok += bon
        check(ok == len(ancres), f"{relation} : {ok}/{len(ancres)} ancres entité vérité-terrain exactes")


def valide_ouvert(lec, relation):
    t = _charge(lec, relation, _RELATIONS[relation])
    if not t:
        return
    n_ent = len(t)
    valeurs = [f.valeur for f in t.values()]
    print(f"-- {relation} : {n_ent} entités, {len(set(valeurs))} valeurs distinctes")
    check(n_ent > 0, f"{relation} : table non vide")
    check(all(len(v.strip()) >= 2 and _a_une_lettre(v) for v in valeurs),
          f"{relation} : toutes les valeurs plausibles (≥2 car., lettre)")
    ancres = _ANCRES[relation]
    if ancres:
        ok = 0
        for ent, attendu in ancres:
            f = lec.cherche(relation, ent)
            bon = f is not None and _norm(f.valeur) == _norm(attendu)
            if not bon:
                print(f"     ancre RATÉE : {ent!r} -> {f.valeur if f else 'HORS'!r} (attendu {attendu!r})")
            ok += bon
        check(ok == len(ancres), f"{relation} : {ok}/{len(ancres)} ancres vérité-terrain exactes")
    else:
        print(f"     (pas encore d'ancres renseignées pour {relation})")


def main():
    # RAM BORNÉE : un Lecteur FRAIS par relation (chargé puis libéré) -> le pic mémoire = la plus grosse
    # relation seule (~occupation 2,16 M), PAS la somme de tout T6. Permet d'ajouter des relations massives
    # sans faire exploser la gate (cf. plafond rencontré par T4 en chargeant tout d'un bloc).
    fermes = ("sexe_personne", "periode_personne", "langue_maternelle", "secteur_entreprise", "religion_personne",
              "langue_ecriture", "type_voix", "prix_recu_personne", "instrument_joue",
              "branche_militaire", "cause_deces", "domaine_travail", "occupation_personne",
              "poste_occupe", "bourse_cotation", "nomine_pour", "diplome_universitaire",
              "langue_parlee", "lateralite_personne", "systeme_cristallin",
              "couleur_trait_mineral", "mode_jeu_video", "couleur_film",
              "materiau_construction", "materiau_monnaie", "materiau_meuble",
              "materiau_vase", "robe_cheval", "diocese_eglise", "plateforme_jeu",
              "format_distribution_film", "format_album",
              "format_distribution_jeu", "materiau_pont",
              "format_image_film", "couleur_serie", "couleur_episode",
              "format_image_serie", "format_distribution_serie",
              "format_single", "format_edition", "materiau_cloche",
              "materiau_manuscrit", "materiau_calice",
              "materiau_chaire")
    ouverts = ("pere_personne", "mere_personne", "conjoint_personne", "eleve_de", "etudie_a",
               "employeur_personne", "membre_de", "directeur_these", "proprietaire_organisation",
               "fondateur_organisation", "maison_mere", "mouvement_personne",
               "prenom", "nom_famille")
    # FILTRE DEV : `python3 valide_lecteur_t6.py <rel> [<rel>...]` ne valide QUE ces relations (chargement
    # rapide, évite de recharger les tables géantes personnes). Sans argument = gate COMPLÈTE (défaut officiel).
    cibles = set(sys.argv[1:])
    if cibles:
        fermes = tuple(r for r in fermes if r in cibles)
        ouverts = tuple(r for r in ouverts if r in cibles)
        inconnues = cibles - set(fermes) - set(ouverts)
        if inconnues:
            print(f"Relations inconnues (ignorées) : {sorted(inconnues)}")
    for rel in fermes:
        valide_ferme(L.Lecteur(), rel)
    for rel in ouverts:
        valide_ouvert(L.Lecteur(), rel)
    print()
    if _ECHECS:
        print(f"ÉCHEC : {len(_ECHECS)} check(s) en échec.")
        return 1
    print("OK : tous les checks T6 passent (FAUX=0 maintenu).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
