"""
INGESTION T10 — SPORT & COMPÉTITIONS  (ONLINE, lancé à la main).

Couloir T10 du palier 1 (le BORNÉ). Lis BRIEF_INGESTION_COMMUN.md + BRIEF_T10_SPORT.md.
Réutilise les fabriques de `ingere_qlever` (NE redéfinit PAS de fabrique). FAUX=0 INVIOLABLE :
`fonctionnel` (1 valeur/entité ; multi-valeur -> HORS) + ancres vérité-terrain dans valide_lecteur_t10.

T6 a CÉDÉ à T10 les faits d'équipes sportives. Les STADES/VILLES (lieux) restent à T1 : une relation
club->stade est annoncée et nommée distinctement, coordonnée via le canal.

Relations RETENUES :
  ENSEMBLE FERMÉ (scout PROPRE, ratio bas, fonctionnel ≥98 %) :
    - sport_competition   P641 / Q13406554      convention  (compétition sportive -> sport ; ~497 disciplines)
  X -> PAYS SOUVERAIN (ratio haut = NORMAL ; valeur ∈ ~196 états souverains Q3624078) :
    - pays_equipe_nationale  P17 / Q6979593      physique    (équipe nationale de foot -> pays souverain actuel)

NOTE soundness : `sport_competition` est fonctionnel (une compétition étiquetée multi-sport part en HORS = sûr) ET
le sport est quasi-définitionnel (« Tour de France 2000 »→cyclisme, « Coupe du monde 1930 »→football). Les ~497
valeurs sont de vraies disciplines/sous-disciplines (« tennis en fauteuil roulant »…), pas un faux ensemble.
`pays_equipe_nationale` via _ingere_x_vers_pays filtre la valeur = état souverain ACTUEL (Q3624078) : une équipe de
nation constitutive (Angleterre, Écosse…) reçoit son ÉTAT souverain (Royaume-Uni) = correct au sens de P17 « pays ».

REJET DOCUMENTÉ — ligue_club (P118 / Q476028, club->ligue). Scout PROPRE (ratio .061, fonctionnel .987) MAIS
soundness VIOLÉE : la clé d'index = libellé FR, et les clubs ont des HOMONYMES. « Real Madrid » a capté un club
portoricain homonyme MONO-valeur (P118 = « Championnat de Porto Rico ») tandis que le vrai Real Madrid espagnol est
absent/multi-valeur -> lookup(« Real Madrid ») renvoie Porto Rico = FAIT FAUX. `fonctionnel` ne protège QUE du
multi-valeur, pas de l'homonyme mono-valeur. Rejeté (FAUX=0). Réintroduction possible plus tard avec une garde
anti-homonyme (ne garder que les libellés portés par UN seul QID club dans Wikidata) — différé.

Usage : python3 ingere_t10.py [relations...]   (défaut : toutes)   puis valide_lecteur_t10.py OFFLINE.
"""
from __future__ import annotations

import re
import sys

import ingere_qlever as IQ

_T10 = {}

# QID nu depuis une URI Wikidata (« http://www.wikidata.org/entity/Q8682 » -> « Q8682 »).
_RX_QID = re.compile(r"Q\d+$")


def _qid(uri: str) -> str:
    m = _RX_QID.search((uri or "").strip())
    return m.group(0) if m else ""


def _ingere_club_vers_entite_garde(relation, propriete, categorie, source, classe_qid="Q476028"):
    """Fabrique « club -> valeur » AVEC GARDE ANTI-HOMONYME (FAUX=0).

    PROBLÈME (leçon T10) : la clé d'index du lecteur = libellé FR. La classe club Q476028 est INFECTÉE par
    les homonymes (« Real Madrid » = club espagnol RÉEL + club portoricain homonyme). `fonctionnel` ne protège
    QUE du multi-valeur d'un même libellé ; il NE voit PAS le cas où le vrai club est ABSENT de la propriété et
    un homonyme mono-valeur capte la clé -> FAIT FAUX (Real Madrid -> Porto Rico).

    GARDE : on récupère, pour TOUTE la classe (qu'elle porte ou non la propriété), la carte libellé -> {QID}.
    On ne garde un fait que si son eLabel est porté par UN SEUL QID dans la classe (libellé non ambigu). Tout
    libellé homonyme (>=2 QID) part en HORS -> aucun homonyme ne peut subsister. Agressif = SÛR (FAUX=0)."""
    print(f"== {relation} (Wikidata/QLever {propriete}, classe {classe_qid}) + GARDE ANTI-HOMONYME ==")
    # (1) faits candidats : club portant la propriété -> valeur (avec le QID du club).
    q_rel = f"""SELECT ?e ?eLabel ?vLabel WHERE {{
      ?e wdt:P31/wdt:P279* wd:{classe_qid} ; wdt:{propriete} ?o .
      ?o rdfs:label ?vLabel . FILTER(lang(?vLabel)="fr")
      ?e rdfs:label ?eLabel . FILTER(lang(?eLabel)="fr")
    }}"""
    rows = IQ._charge_ou_fetch(relation, q_rel)
    print(f"  {len(rows)} lignes brutes (relation).")
    # (2) carte d'ambiguïté : libellé FR -> nombre de QID distincts dans TOUTE la classe.
    q_amb = f"""SELECT ?e ?eLabel WHERE {{
      ?e wdt:P31/wdt:P279* wd:{classe_qid} .
      ?e rdfs:label ?eLabel . FILTER(lang(?eLabel)="fr")
    }}"""
    # snapshot AMBIG nommé par CLASSE (pas par relation) -> ligue_club et stade_club partagent UN seul fetch.
    rows_amb = IQ._charge_ou_fetch(f"_ambig_classe_{classe_qid}", q_amb)
    qids_par_label: dict[str, set] = {}
    for r in rows_amb:
        lab = IQ.val(r, "eLabel")
        qid = _qid(IQ.val(r, "e"))
        if lab and qid:
            qids_par_label.setdefault(lab, set()).add(qid)
    n_total = len(qids_par_label)
    n_ambigu = sum(1 for s in qids_par_label.values() if len(s) >= 2)
    print(f"  carte d'ambiguïté : {n_total} libellés, {n_ambigu} homonymes (>=2 QID) -> écartés.")
    # (3) ne garder que les paires dont l'eLabel est porté par EXACTEMENT un QID.
    paires_brutes = IQ._paires(rows, "eLabel", "vLabel")
    avant = len(paires_brutes)
    paires = [(e, v) for (e, v) in paires_brutes if len(qids_par_label.get(e, set())) == 1]
    print(f"  garde anti-homonyme : {avant} -> {len(paires)} paires (libellés mono-QID).")
    IQ.publie(relation, categorie, source, paires)


def _t10(nom):
    def deco(fn):
        _T10[nom] = fn
        return fn
    return deco


# ---- ENSEMBLE FERMÉ (entité sport -> valeur d'un set fermé) ----
# NB : ligue_club (P118) a été REJETÉ pour FAUX=0 (homonymes de clubs) — voir docstring du module.

@_t10("sport_competition")
def ingere_sport_competition():
    # compétition/édition/SAISON sportive -> sport pratiqué (ensemble fermé ~497 sports). Quasi définitionnel ;
    # fonctionnel rejette les rares étiquetées multi-sport -> HORS. UNION de la classe compétition (Q13406554) ET
    # saison sportive (Q27020041) : ~27 % des saisons ne sont PAS sous-classe de compétition -> +~48k éditions
    # datées neuves (« championnats des Balkans d'athlétisme en salle 2013 »). Chevauchement réconcilié idempotent.
    q = """SELECT ?eLabel ?vLabel WHERE {
      { ?e wdt:P31/wdt:P279* wd:Q13406554 } UNION { ?e wdt:P31/wdt:P279* wd:Q27020041 }
      ?e wdt:P641 ?o .
      ?o rdfs:label ?vLabel . FILTER(lang(?vLabel)="fr")
      ?e rdfs:label ?eLabel . FILTER(lang(?eLabel)="fr")
    }"""
    rows = IQ._charge_ou_fetch("sport_competition_union", q)
    print(f"  {len(rows)} lignes brutes (compétition ∪ saison).")
    IQ.publie("sport_competition", "convention",
              "Wikidata/QLever — sport de la compétition/saison P641 (union Q13406554 ∪ Q27020041 ; ensemble fermé)",
              IQ._paires(rows, "eLabel", "vLabel"))


# ---- X -> PAYS SOUVERAIN ACTUEL (valeur ∈ ensemble fermé des ~190 pays) ----

@_t10("pays_equipe_nationale")
def ingere_pays_equipe_nationale():
    IQ._ingere_x_vers_pays(
        "pays_equipe_nationale", "Q6979593", "PAYS DE L'ÉQUIPE NATIONALE")


# ---- VOCAB OUVERT (clé = édition datée UNIQUE -> pas de piège homonyme ; valeur = vainqueur) ----

@_t10("vainqueur_competition")
def ingere_vainqueur_competition():
    # édition de saison sportive (Q27020041, libellé daté UNIQUE « championnat d'Angleterre 1965-1966 ») -> vainqueur
    # (équipe/club/personne). Fait PASSÉ figé (un palmarès ne change jamais). La clé étant l'édition datée, il n'y a
    # PAS de collision d'homonymes (≠ ligue_club/stade_club dont la clé est le club). `fonctionnel` rejette les
    # éditions ambiguës à plusieurs vainqueurs (compétition récurrente sans édition précise) -> HORS (sûr).
    IQ._ingere_x_vers_entite(
        "vainqueur_competition", "P1346", "passe",
        "Wikidata/QLever — vainqueur de l'édition de compétition P1346 (clé=édition datée unique ; multi -> HORS)",
        classe_qid="Q27020041")


# ---- CLUB -> X via GARDE ANTI-HOMONYME (récupère ligue_club + stade_club proprement, FAUX=0) ----
# La classe club Q476028 est infectée par les homonymes (Real Madrid espagnol vs portoricain). La garde ne
# conserve QUE les libellés mono-QID -> tout homonyme part en HORS. Voir _ingere_club_vers_entite_garde.

@_t10("ligue_club")
def ingere_ligue_club():
    # club -> ligue/championnat où il évolue (P118). Vocab ouvert (championnats nommés), clé = club (homonymes)
    # -> GARDE obligatoire. fonctionnel (dans publie) écarte en plus les clubs multi-ligue.
    _ingere_club_vers_entite_garde(
        "ligue_club", "P118", "convention",
        "Wikidata/QLever — ligue du club P118 (garde anti-homonyme : libellés clubs mono-QID)")


@_t10("stade_club")
def ingere_stade_club():
    # club -> stade qu'il occupe (P115). Le stade est un LIEU -> annoncer DONE à T1. Même garde anti-homonyme.
    _ingere_club_vers_entite_garde(
        "stade_club", "P115", "physique",
        "Wikidata/QLever — stade du club P115 (garde anti-homonyme : libellés clubs mono-QID)")


# ---- X -> PAYS SOUVERAIN (compétition -> pays P17) : pas de garde homonyme nécessaire (valeur ∈ ~196 pays,
# sanité structurelle forte ; clé = compétition à libellé souvent daté/unique ; fonctionnel rejette les multi-pays).

@_t10("pays_competition")
def ingere_pays_competition():
    # compétition sportive (Q13406554) -> pays P17 (organisateur / d'appartenance). _ingere_x_vers_pays filtre la
    # valeur = état souverain ACTUEL (Q3624078) et fonctionnel rejette les compétitions multi-pays -> HORS (sûr).
    IQ._ingere_x_vers_pays(
        "pays_competition", "Q13406554", "PAYS DE LA COMPÉTITION")


# ---- ÉQUIPE SPORTIVE -> SPORT (set fermé) AVEC GARDE ANTI-HOMONYME (clé = équipe, même risque que les clubs).

@_t10("sport_equipe")
def ingere_sport_equipe():
    # équipe sportive (Q12973014) -> sport pratiqué P641 (ensemble fermé de disciplines). Une équipe multi-sport
    # (« MTV Braunschweig » -> hockey | fistball) part en HORS via fonctionnel ; la garde écarte les homonymes.
    _ingere_club_vers_entite_garde(
        "sport_equipe", "P641", "convention",
        "Wikidata/QLever — sport de l'équipe P641 (set fermé ; garde anti-homonyme : libellés équipes mono-QID)",
        classe_qid="Q12973014")


# ---- COMPÉTITION -> FÉDÉRATION ORGANISATRICE (vocab ouvert ; clé = compétition à libellé unique/daté = pas
# d'infection homonyme ; valeur = organisme stable). fonctionnel rejette les compétitions multi-organisateur.

@_t10("organisateur_competition")
def ingere_organisateur_competition():
    # compétition (Q13406554) -> organisateur P664 (fédération/organisme). Clé = compétition (libellé souvent
    # unique/daté, PAS la classe club infectée) -> pas de garde homonyme. fonctionnel écarte les multi-organisateur.
    # FILTRE ANTI-SELF : on écarte les paires (entite==valeur) — une compétition ne s'organise pas elle-même (fait
    # circulaire vacuant) ; rare (≈3) mais faux -> HORS (FAUX=0). Réutilise le snapshot brut offline.
    q = """SELECT ?eLabel ?vLabel WHERE {
      ?e wdt:P31/wdt:P279* wd:Q13406554 ; wdt:P664 ?o .
      ?o rdfs:label ?vLabel . FILTER(lang(?vLabel)="fr")
      ?e rdfs:label ?eLabel . FILTER(lang(?eLabel)="fr")
    }"""
    rows = IQ._charge_ou_fetch("organisateur_competition", q)
    print(f"  {len(rows)} lignes brutes.")
    paires = IQ._paires(rows, "eLabel", "vLabel")
    avant = len(paires)
    paires = [(e, v) for (e, v) in paires if e.strip().lower() != v.strip().lower()]
    print(f"  filtre anti-self (entite==valeur) : {avant} -> {len(paires)}")
    IQ.publie("organisateur_competition", "convention",
              "Wikidata/QLever — organisateur de la compétition P664 (anti-self ; multi -> HORS)", paires)


# ---- CLUB -> VILLE-SIÈGE (P159) AVEC GARDE ANTI-HOMONYME (clé = club infecté). Valeur = LIEU -> annoncer à T1.

@_t10("siege_club")
def ingere_siege_club():
    # club (Q476028) -> ville du siège P159. Valeur = lieu (vocab ouvert). Même garde anti-homonyme que ligue/stade
    # (« Real Madrid » ambigu écarté). fonctionnel écarte les clubs multi-siège.
    _ingere_club_vers_entite_garde(
        "siege_club", "P159", "physique",
        "Wikidata/QLever — ville du siège du club P159 (garde anti-homonyme : libellés clubs mono-QID)")


# ---- ÉPREUVE SPORTIVE -> SPORT (set fermé). Clé = épreuve à libellé ULTRA-unique (« VTT cross-country masculin
# aux Jeux olympiques d'été de 2016 ») -> pas de garde. fonctionnel écarte les rares épreuves multi-sport.

@_t10("epreuve_sport")
def ingere_epreuve_sport():
    IQ._ingere_x_vers_entite(
        "epreuve_sport", "P641", "convention",
        "Wikidata/QLever — sport de l'épreuve P641 (set fermé ; clé=épreuve datée unique ; multi -> HORS)",
        classe_qid="Q18536594")


# ---- ÉQUIPE SPORTIVE -> VILLE-SIÈGE (P159) AVEC GARDE ANTI-HOMONYME (clé = équipe). Valeur = LIEU -> info T1.

@_t10("ville_equipe")
def ingere_ville_equipe():
    _ingere_club_vers_entite_garde(
        "ville_equipe", "P159", "physique",
        "Wikidata/QLever — ville du siège de l'équipe P159 (garde anti-homonyme : libellés équipes mono-QID)",
        classe_qid="Q12973014")


# ---- ÉQUIPE SPORTIVE -> PAYS SOUVERAIN, combo GARDE ANTI-HOMONYME + filtre valeur=état souverain (FAUX=0).
# Double protection : (1) clé d'équipe mono-QID (écarte les homonymes d'équipes) ; (2) valeur ∈ états souverains
# actuels (Q3624078) imposée dans la requête (sanité structurelle forte + normalise Angleterre/Écosse hors -> HORS).

@_t10("pays_equipe_sport")
def ingere_pays_equipe_sport():
    q_rel = """SELECT ?e ?eLabel ?vLabel WHERE {
      ?e wdt:P31/wdt:P279* wd:Q12973014 ; wdt:P17 ?p .
      ?p wdt:P31 wd:Q3624078 .
      ?p rdfs:label ?vLabel . FILTER(lang(?vLabel)="fr")
      ?e rdfs:label ?eLabel . FILTER(lang(?eLabel)="fr")
    }"""
    rows = IQ._charge_ou_fetch("pays_equipe_sport", q_rel)
    print(f"  {len(rows)} lignes brutes (équipe -> pays souverain).")
    # carte d'ambiguïté de la classe équipe (réutilise le snapshot partagé _ambig_classe_Q12973014).
    q_amb = """SELECT ?e ?eLabel WHERE {
      ?e wdt:P31/wdt:P279* wd:Q12973014 .
      ?e rdfs:label ?eLabel . FILTER(lang(?eLabel)="fr")
    }"""
    rows_amb = IQ._charge_ou_fetch("_ambig_classe_Q12973014", q_amb)
    qids_par_label = {}
    for r in rows_amb:
        lab = IQ.val(r, "eLabel"); qid = _qid(IQ.val(r, "e"))
        if lab and qid:
            qids_par_label.setdefault(lab, set()).add(qid)
    n_amb = sum(1 for s in qids_par_label.values() if len(s) >= 2)
    print(f"  carte ambiguïté équipe : {len(qids_par_label)} libellés, {n_amb} homonymes (>=2 QID) -> écartés.")
    paires = IQ._paires(rows, "eLabel", "vLabel")
    avant = len(paires)
    paires = [(e, v) for (e, v) in paires if len(qids_par_label.get(e, set())) == 1]
    print(f"  garde anti-homonyme : {avant} -> {len(paires)} (libellés équipe mono-QID).")
    IQ.publie("pays_equipe_sport", "physique",
              "Wikidata/QLever — pays souverain de l'équipe P17 (Q3624078 ; garde anti-homonyme mono-QID)", paires)


# ---- helper local : entité -> valeur (vocab ouvert) AVEC filtre anti-self (entite==valeur -> HORS, FAUX=0).
def _ingere_nonself(relation, propriete, categorie, source, classe_qid):
    print(f"== {relation} (Wikidata/QLever {propriete}, classe {classe_qid}) + anti-self ==")
    q = f"""SELECT ?eLabel ?vLabel WHERE {{
      ?e wdt:P31/wdt:P279* wd:{classe_qid} ; wdt:{propriete} ?o .
      ?o rdfs:label ?vLabel . FILTER(lang(?vLabel)="fr")
      ?e rdfs:label ?eLabel . FILTER(lang(?eLabel)="fr")
    }}"""
    rows = IQ._charge_ou_fetch(relation, q)
    paires = IQ._paires(rows, "eLabel", "vLabel")
    avant = len(paires)
    paires = [(e, v) for (e, v) in paires if e.strip().lower() != v.strip().lower()]
    print(f"  {len(rows)} lignes brutes ; anti-self {avant} -> {len(paires)}.")
    IQ.publie(relation, categorie, source, paires)


# ---- SAISON SPORTIVE -> COMPÉTITION/LIGUE PARENTE (P3450). Clé = saison datée UNIQUE (pas d'homonyme) ;
# valeur = ligue parente (vocab ouvert). fonctionnel + anti-self. « Formule 3 Euro Series 2012 -> Formule 3 Euro Series ».

@_t10("ligue_parente_saison")
def ingere_ligue_parente_saison():
    _ingere_nonself(
        "ligue_parente_saison", "P3450", "convention",
        "Wikidata/QLever — ligue/compétition parente de la saison P3450 (clé=saison datée unique ; anti-self)",
        classe_qid="Q13406554")


# ---- federation_internationale_sport : sport -> FÉDÉRATION MONDIALE. SOURCE = SAVOIR CLAUDE (vérifié), car
# Wikidata est CONTAMINÉ par les organes continentaux (FIBA Afrique, Badminton Asia…) et `fonctionnel` ne protège
# pas quand un organe régional est le seul survivant -> FAUX possible (cf. scouts _scout_fed*.py). Directive Yohan :
# « être la source si besoin ». FAUX=0 : uniquement les sports dont je connais l'organe mondial avec CERTITUDE
# ABSOLUE et son nom actuel ; ABSTENTION sur les sports à gouvernance contestée/multiple (ex. boxe = IBA vs World
# Boxing en litige -> EXCLU). Faits stables (institutionnels). Chaque paire = « la fédération MONDIALE de X est Y ».
_FEDERATION_SPORT = [
    ("football", "Fédération internationale de football association"),
    ("basket-ball", "Fédération internationale de basket-ball"),
    ("volley-ball", "Fédération internationale de volleyball"),
    ("beach-volley", "Fédération internationale de volleyball"),
    ("tennis", "Fédération internationale de tennis"),
    ("tennis de table", "Fédération internationale de tennis de table"),
    ("badminton", "Fédération mondiale de badminton"),
    ("handball", "Fédération internationale de handball"),
    ("rugby à XV", "World Rugby"),
    ("cricket", "Conseil international du cricket"),
    ("hockey sur glace", "Fédération internationale de hockey sur glace"),
    ("hockey sur gazon", "Fédération internationale de hockey"),
    ("natation", "World Aquatics"),
    ("water-polo", "World Aquatics"),
    ("athlétisme", "World Athletics"),
    ("cyclisme", "Union cycliste internationale"),
    ("gymnastique", "Fédération internationale de gymnastique"),
    ("escrime", "Fédération internationale d'escrime"),
    ("judo", "Fédération internationale de judo"),
    ("taekwondo", "World Taekwondo"),
    ("aviron", "World Rowing"),
    ("voile", "World Sailing"),
    ("canoë-kayak", "Fédération internationale de canoë"),
    ("tir à l'arc", "World Archery"),
    ("haltérophilie", "Fédération internationale d'haltérophilie"),
    ("triathlon", "World Triathlon"),
    ("équitation", "Fédération équestre internationale"),
    ("golf", "Fédération internationale de golf"),
    ("ski", "Fédération internationale de ski"),
    ("biathlon", "Union internationale de biathlon"),
    ("patinage", "Union internationale de patinage"),
    ("escalade", "Fédération internationale d'escalade sportive"),
    ("lutte", "United World Wrestling"),
    ("baseball", "Confédération mondiale de baseball et softball"),
    ("softball", "Confédération mondiale de baseball et softball"),
    ("curling", "Fédération mondiale de curling"),
    ("pentathlon moderne", "Union internationale de pentathlon moderne"),
    ("tir sportif", "Fédération internationale de tir sportif"),
]


@_t10("federation_internationale_sport")
def ingere_federation_internationale_sport():
    print("== federation_internationale_sport (SOURCE = savoir Claude vérifié ; Wikidata contaminé continental) ==")
    IQ.publie(
        "federation_internationale_sport", "convention",
        "Savoir Claude vérifié — fédération sportive MONDIALE par sport (hors Wikidata : données contaminées par "
        "les organes continentaux ; uniquement organes mondiaux à gouvernance non contestée)",
        _FEDERATION_SPORT)


# ---- AUTO-SOURCÉ (savoir Claude vérifié) : taxonomies sportives CANONIQUES non contaminées et sans flou.
# categorie_epreuve_athletisme : épreuve d'athlétisme -> famille (taxonomie standard World Athletics, non débattue).
_CATEGORIE_ATHLE = [
    ("100 mètres", "course"), ("200 mètres", "course"), ("400 mètres", "course"),
    ("800 mètres", "course"), ("1 500 mètres", "course"), ("5 000 mètres", "course"),
    ("10 000 mètres", "course"), ("marathon", "course"), ("110 mètres haies", "course"),
    ("100 mètres haies", "course"), ("400 mètres haies", "course"), ("3 000 mètres steeple", "course"),
    ("relais 4 × 100 mètres", "course"), ("relais 4 × 400 mètres", "course"),
    ("saut en longueur", "saut"), ("saut en hauteur", "saut"), ("triple saut", "saut"),
    ("saut à la perche", "saut"),
    ("lancer du poids", "lancer"), ("lancer du disque", "lancer"), ("lancer du javelot", "lancer"),
    ("lancer du marteau", "lancer"),
    ("20 kilomètres marche", "marche"), ("50 kilomètres marche", "marche"),
    ("décathlon", "épreuve combinée"), ("heptathlon", "épreuve combinée"),
]


@_t10("categorie_epreuve_athletisme")
def ingere_categorie_epreuve_athletisme():
    print("== categorie_epreuve_athletisme (SOURCE = savoir Claude ; taxonomie World Athletics) ==")
    IQ.publie("categorie_epreuve_athletisme", "convention",
              "Savoir Claude vérifié — famille de l'épreuve d'athlétisme (taxonomie standard course/saut/lancer/"
              "marche/combiné, non débattue)", _CATEGORIE_ATHLE)


# surface_tournoi_tennis : tournoi du Grand Chelem -> surface (fait canonique stable, non débattu).
_SURFACE_TENNIS = [
    ("Roland-Garros", "terre battue"),                  # tennis-unambigu
    ("Tournoi de Wimbledon", "gazon"),                  # tennis-unambigu
    ("US Open de tennis", "dur"),                        # désambiguïsé (US Open de golf existe)
    ("Open d'Australie de tennis", "dur"),              # désambiguïsé
]


@_t10("surface_tournoi_tennis")
def ingere_surface_tournoi_tennis():
    print("== surface_tournoi_tennis (SOURCE = savoir Claude ; Grand Chelem) ==")
    IQ.publie("surface_tournoi_tennis", "convention",
              "Savoir Claude vérifié — surface du tournoi du Grand Chelem de tennis (canonique stable)",
              _SURFACE_TENNIS)


# ---- ATHLÈTE -> PAYS SPORTIF (P1532, « country for sport »), combo GARDE ANTI-HOMONYME + filtre souverain.
# La nationalité sportive est définitionnelle (bornée). Clé = nom d'athlète (HOMONYMES fréquents) -> garde mono-QID
# sur l'univers des humains portant P1532. Valeur ∈ état souverain Q3624078 (sanité + naturalisés multi -> HORS).

@_t10("pays_sportif_athlete")
def ingere_pays_sportif_athlete():
    print("== pays_sportif_athlete (Wikidata/QLever Q5 P1532 -> souverain) + GARDE ANTI-HOMONYME ==")
    q_rel = """SELECT ?e ?eLabel ?vLabel WHERE {
      ?e wdt:P31 wd:Q5 ; wdt:P1532 ?p .
      ?p wdt:P31 wd:Q3624078 .
      ?p rdfs:label ?vLabel . FILTER(lang(?vLabel)="fr")
      ?e rdfs:label ?eLabel . FILTER(lang(?eLabel)="fr")
    }"""
    rows = IQ._charge_ou_fetch("pays_sportif_athlete", q_rel)
    print(f"  {len(rows)} lignes brutes (athlète -> pays souverain).")
    # univers d'ambiguïté = humains portant P1532 (la nationalité sportive) -> carte libellé->{QID}.
    q_amb = """SELECT ?e ?eLabel WHERE {
      ?e wdt:P31 wd:Q5 ; wdt:P1532 ?x .
      ?e rdfs:label ?eLabel . FILTER(lang(?eLabel)="fr")
    }"""
    rows_amb = IQ._charge_ou_fetch("_ambig_athlete_P1532", q_amb)
    qids_par_label = {}
    for r in rows_amb:
        lab = IQ.val(r, "eLabel"); qid = _qid(IQ.val(r, "e"))
        if lab and qid:
            qids_par_label.setdefault(lab, set()).add(qid)
    n_amb = sum(1 for s in qids_par_label.values() if len(s) >= 2)
    print(f"  carte ambiguïté athlète : {len(qids_par_label)} libellés, {n_amb} homonymes (>=2 QID) -> écartés.")
    paires = IQ._paires(rows, "eLabel", "vLabel")
    avant = len(paires)
    paires = [(e, v) for (e, v) in paires if len(qids_par_label.get(e, set())) == 1]
    print(f"  garde anti-homonyme : {avant} -> {len(paires)} (athlètes mono-QID).")
    IQ.publie("pays_sportif_athlete", "physique",
              "Wikidata/QLever — pays sportif de l'athlète P1532 (Q3624078 ; garde anti-homonyme mono-QID)", paires)


def main(argv):
    cibles = argv[1:] if len(argv) > 1 else list(_T10)
    inconnues = [c for c in cibles if c not in _T10]
    if inconnues:
        print(f"Relations inconnues : {inconnues}\nDisponibles : {list(_T10)}")
        return 1
    for nom in cibles:
        print(f"\n########## {nom} ##########")
        _T10[nom]()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
