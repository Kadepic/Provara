"""
INGESTION T6 — PERSONNES (attributs NON-lieu) & ORGANISATIONS  (ONLINE, lancé à la main).

Couloir T6 du palier 1 (le BORNÉ). Lis BRIEF_INGESTION_COMMUN.md + BRIEF_T6_PERSONNES_ORGS.md.
Réutilise les fabriques de `ingere_qlever` (NE redéfinit PAS de fabrique). FAUX=0 INVIOLABLE :
`fonctionnel` (1 valeur/entité ; multi-valeur -> HORS) + ancres vérité-terrain dans valide_lecteur_t6.

Relations (toutes via _ingere_x_vers_entite = entité→valeur-entité fonctionnelle) :
  ENSEMBLES FERMÉS (scout PROPRE, ratio bas) :
    - sexe_personne        P21  / Q5         physique   (set fermé ~qq dizaines)
    - langue_maternelle    P103 / Q5         physique   (set fermé de langues)
    - secteur_entreprise   P452 / Q4830453   convention (set fermé d'industries)
  VOCAB OUVERT (jugé comme un LIEU : fonctionnel + ancres ; ratio haut = NORMAL, pas un set fermé) :
    - fondateur_organisation P112 / Q43229   passe      (org -> fondateur ; multi-fondateurs -> HORS)
    - maison_mere            P749 / Q4830453 physique   (entreprise -> maison-mère)

DÉFÉRÉ : pdg_actuel (P169) = fait DATÉ volatil (le DG change souvent) -> risque FAUX dans le temps. Non pris.
siege_social (P159, un LIEU) -> couloir T1, non pris ici. profession (P106, très multi) -> différé.

Usage : python3 ingere_t6.py [relations...]   (défaut : toutes)   puis valide_lecteur_t6.py OFFLINE.
"""
from __future__ import annotations

import re
import sys
import urllib.parse
import urllib.request

import ingere_qlever as IQ


def _tsv_champ(s: str) -> str:
    """Décode un champ TSV de QLever : littéral RDF « \"texte\"@fr » -> « texte » (déséchappé) ; IRI/QID nu inchangé."""
    s = s.strip()
    if s.startswith('"'):
        fin = s.rfind('"')
        if fin > 0:
            inner = s[1:fin]
            return (inner.replace('\\"', '"').replace('\\\\', '\\')
                    .replace('\\t', '\t').replace('\\n', '\n'))
    return s


def _stream_paires_tsv(query: str, timeout: int = 1200):
    """Streame une requête SPARQL en TSV (ligne-à-ligne) -> yield (entite, valeur) propres. Mémoire ~ O(1)
    côté transport (pas de json.loads géant) : indispensable pour les relations massives (occupation 2,4 M).
    Applique les MÊMES filtres que IQ._paires : entité non vide, valeur >= 2 car., ni l'un ni l'autre un Q-ID nu."""
    url = IQ.ENDPOINT + "?action=tsv_export&query=" + urllib.parse.quote(IQ.PREFIXES + query)
    req = urllib.request.Request(url, headers={"User-Agent": IQ.UA})
    est_qid = re.compile(r"^Q\d+$").match
    with urllib.request.urlopen(req, timeout=timeout) as r:
        premiere = True
        for ligne in r:
            if premiere:  # en-tête ?eLabel\t?vLabel
                premiere = False
                continue
            parts = ligne.decode("utf-8").rstrip("\n").split("\t")
            if len(parts) < 2:
                continue
            e = _tsv_champ(parts[0])
            v = _tsv_champ(parts[1])
            if e and len(v) >= 2 and not est_qid(e) and not est_qid(v):
                yield (e, v)

# ============================================================================================
#  RELATIONS T6 — chacune = 1 appel de fabrique = 1 relation bornée.
# ============================================================================================
_T6 = {}


def _t6(nom):
    def deco(fn):
        _T6[nom] = fn
        return fn
    return deco


# ---- ENSEMBLES FERMÉS (personne / organisation) ----

@_t6("sexe_personne")
def ingere_sexe_personne():
    IQ._ingere_x_vers_entite(
        "sexe_personne", "P21", "physique",
        "Wikidata/QLever — sexe ou genre de la personne P21 (ensemble fermé)",
        classe_qid="Q5")


@_t6("langue_maternelle")
def ingere_langue_maternelle():
    IQ._ingere_x_vers_entite(
        "langue_maternelle", "P103", "physique",
        "Wikidata/QLever — langue maternelle de la personne P103 (ensemble fermé de langues)",
        classe_qid="Q5")


@_t6("secteur_entreprise")
def ingere_secteur_entreprise():
    IQ._ingere_x_vers_entite(
        "secteur_entreprise", "P452", "convention",
        "Wikidata/QLever — secteur d'activité de l'entreprise P452 (ensemble fermé d'industries)",
        classe_qid="Q4830453")


@_t6("occupation_personne")
def ingere_occupation_personne():
    # personne -> occupation (métier). P106 est intrinsèquement MULTI (>10 M lignes brutes) -> fetch JSON plein
    # = risque OOM. SOLUTION : filtre mono-occupation CÔTÉ SERVEUR (GROUP BY ?e HAVING COUNT(DISTINCT ?o)=1)
    # + transport STREAMÉ en TSV (mémoire ~ paires seulement). 2 422 742 humains mono-occupation (sonde COUNT).
    # FAUX=0 : HAVING=1 garantit déjà l'unicité (fonctionnel dans publie = filet) ; valeur = métier nommé.
    q = """SELECT ?eLabel ?vLabel WHERE {
      { SELECT ?e WHERE { ?e wdt:P31 wd:Q5 ; wdt:P106 ?o } GROUP BY ?e HAVING(COUNT(DISTINCT ?o)=1) }
      ?e wdt:P106 ?v .
      ?v rdfs:label ?vLabel . FILTER(lang(?vLabel)="fr")
      ?e rdfs:label ?eLabel . FILTER(lang(?eLabel)="fr")
    }"""
    print("== occupation_personne (Wikidata/QLever P106 mono, TSV streamé) ==")
    paires = list(_stream_paires_tsv(q, timeout=1500))
    print(f"  {len(paires)} paires streamées (mono-occupation, filtrées).")
    IQ.publie("occupation_personne", "convention",
              "Wikidata/QLever — occupation de la personne P106 (mono-occupation HAVING=1 ; multi -> exclu serveur)",
              paires)


@_t6("poste_occupe")
def ingere_poste_occupe():
    # personne -> poste/fonction officielle occupée. P39 est MULTI (carrière) -> filtre mono côté serveur
    # (HAVING=1) + streaming TSV. Scout PROPRE ratio=0.113, fonctionnel=96% (bourgmestre, ministre, ambassadeur,
    # bâtonnier…). Fait PASSÉ. La sanité (fermé/ratio) est re-vérifiée dans valide_lecteur_t6 sur la donnée réelle.
    q = """SELECT ?eLabel ?vLabel WHERE {
      { SELECT ?e WHERE { ?e wdt:P31 wd:Q5 ; wdt:P39 ?o } GROUP BY ?e HAVING(COUNT(DISTINCT ?o)=1) }
      ?e wdt:P39 ?v .
      ?v rdfs:label ?vLabel . FILTER(lang(?vLabel)="fr")
      ?e rdfs:label ?eLabel . FILTER(lang(?eLabel)="fr")
    }"""
    print("== poste_occupe (Wikidata/QLever P39 mono, TSV streamé) ==")
    paires = list(_stream_paires_tsv(q, timeout=1500))
    print(f"  {len(paires)} paires streamées (mono-poste, filtrées).")
    IQ.publie("poste_occupe", "passe",
              "Wikidata/QLever — poste/fonction occupé par la personne P39 (mono ; multi -> exclu serveur)",
              paires)


@_t6("domaine_travail")
def ingere_domaine_travail():
    # personne -> domaine de travail/champ d'activité. Scout PROPRE : ratio=0.023, fonctionnel=100%, ~57 valeurs
    # (bande dessinée, théologie, modélisation géométrique…). Ensemble fermé de domaines. Multi -> HORS.
    IQ._ingere_x_vers_entite(
        "domaine_travail", "P101", "convention",
        "Wikidata/QLever — domaine de travail de la personne P101 (ensemble fermé ; multi -> HORS)",
        classe_qid="Q5")


@_t6("cause_deces")
def ingere_cause_deces():
    # personne -> cause du décès. Scout PROPRE : ratio=0.024, fonctionnel=100%, ~60 valeurs (Alzheimer,
    # Parkinson, néphropathie… ; une cause-événement « 11 septembre 2001 » reste une cause de décès valide).
    # Fait PASSÉ figé. Multi-cause -> HORS.
    IQ._ingere_x_vers_entite(
        "cause_deces", "P509", "passe",
        "Wikidata/QLever — cause du décès de la personne P509 (ensemble fermé ; multi -> HORS)",
        classe_qid="Q5")


# couleur_cheveux (P1884) ABANDONNÉ : set minuscule contaminé (« bonnet », « jaune-brun » ≠ couleur de cheveux)
# = risque FAUX sur faible valeur (redondant avec couleur_yeux). Rejeté « au moindre doute », dataset supprimé.


@_t6("bourse_cotation")
def ingere_bourse_cotation():
    # entreprise -> bourse de cotation. Scout PROPRE : ratio=0.008, fonctionnel=100%, ~15 valeurs (NYSE, OMX,
    # Euronext…). Ensemble fermé de bourses. multi-cotation -> HORS.
    IQ._ingere_x_vers_entite(
        "bourse_cotation", "P414", "convention",
        "Wikidata/QLever — bourse de cotation de l'entreprise P414 (ensemble fermé ; multi -> HORS)",
        classe_qid="Q4830453")


@_t6("instrument_joue")
def ingere_instrument_joue():
    # personne (musicien) -> instrument pratiqué. Scout PROPRE : ratio=0.029, fonctionnel=98%, ~72 valeurs
    # (flûte, piano, orgue Hammond…). Ensemble fermé d'instruments. Multi-instrumentistes -> HORS (sûr).
    IQ._ingere_x_vers_entite(
        "instrument_joue", "P1303", "convention",
        "Wikidata/QLever — instrument pratiqué par la personne P1303 (ensemble fermé ; multi -> HORS)",
        classe_qid="Q5")


@_t6("branche_militaire")
def ingere_branche_militaire():
    # personne (militaire) -> branche/armée servie. Scout PROPRE : ratio=0.026, fonctionnel=100%, ~64 valeurs
    # (Armée de terre française, Royal Marines, Armée impériale russe…). VRAI porteur des noms d'armée
    # (distinct de grade_militaire P410, REJETÉ par T1 car contaminé par ces mêmes noms de branche).
    IQ._ingere_x_vers_entite(
        "branche_militaire", "P241", "convention",
        "Wikidata/QLever — branche militaire servie par la personne P241 (ensemble fermé ; multi -> HORS)",
        classe_qid="Q5")


@_t6("type_voix")
def ingere_type_voix():
    # personne (chanteur) -> tessiture/type de voix. Scout PROPRE : ratio=0.004, fonctionnel=100%, ~11 valeurs
    # (mezzo-soprano, Heldentenor, baryton, basse…). Ensemble fermé strict. Attribut physiologique -> physique.
    IQ._ingere_x_vers_entite(
        "type_voix", "P412", "physique",
        "Wikidata/QLever — type de voix/tessiture de la personne P412 (ensemble fermé ; multi -> HORS)",
        classe_qid="Q5")


@_t6("prix_recu_personne")
def ingere_prix_recu_personne():
    # personne -> distinction reçue. Scout : ratio=0.065, fonctionnel=96%. P166 est intrinsèquement MULTI
    # (les personnes très primées ont >1 prix) -> `fonctionnel` les met en HORS (sûr) ; ne restent que les
    # mono-distinction = fait PASSÉ sûr (« X a reçu le prix Y »). Validé en vocab-ouvert (ancres) si le ratio
    # plein dépasse le seuil fermé. FAUX=0 garanti par fonctionnel + valeurs-plausibles + ancres.
    IQ._ingere_x_vers_entite(
        "prix_recu_personne", "P166", "passe",
        "Wikidata/QLever — distinction reçue par la personne P166 (mono-distinction ; multi -> HORS)",
        classe_qid="Q5")


@_t6("langue_ecriture")
def ingere_langue_ecriture():
    # personne (auteur) -> langue d'expression. Scout PROPRE : ratio=0.012, fonctionnel=100%, set fermé de
    # langues (espagnol, latin médiéval, sanskrit…). Relation SŒUR de langue_maternelle -> cat=physique.
    # Distinct de systeme_ecriture_langue (P282, langue->écriture) du couloir T9. Auteurs polyglottes -> HORS.
    IQ._ingere_x_vers_entite(
        "langue_ecriture", "P6886", "physique",
        "Wikidata/QLever — langue d'écriture/d'expression de la personne P6886 (ensemble fermé ; multi -> HORS)",
        classe_qid="Q5")


@_t6("lateralite_personne")
def ingere_lateralite_personne():
    # personne -> latéralité/main dominante (P552). Set fermé STRICT {droitier, gaucher, ambidextre}. Scout
    # PROPRE ratio~0 fonctionnel=100% (le LIMIT n'a vu que « droitier » = sous-échantillonnage, gaucher/
    # ambidextre dans la veine complète). Attribut physique intrinsèque -> physique (comme couleur_yeux).
    # FAUX=0 : `fonctionnel` (une seule main dominante) + ensemble minuscule re-vérifié au validateur.
    IQ._ingere_x_vers_entite(
        "lateralite_personne", "P552", "physique",
        "Wikidata/QLever — latéralité/main dominante de la personne P552 (ensemble fermé strict)",
        classe_qid="Q5")


@_t6("langue_parlee")
def ingere_langue_parlee():
    # personne -> langue parlée/écrite/signée (P1412). Scout PROPRE : ratio=0.04, fonctionnel=98%, 118 langues
    # (sanskrit, breton, zoulou, latin médiéval, galaïco-portugais…). DISTINCT de langue_maternelle (P103,
    # nativité) et langue_ecriture (P6886, langue d'expression écrite) : P1412 = CAPACITÉ linguistique. Ensemble
    # fermé de langues. FAUX=0 : `fonctionnel` écarte les polyglottes (multi-langue -> HORS) ; ne restent que les
    # mono-langue = fait stable. Capacité linguistique intrinsèque -> physique (comme langue_maternelle).
    IQ._ingere_x_vers_entite(
        "langue_parlee", "P1412", "physique",
        "Wikidata/QLever — langue parlée/écrite/signée de la personne P1412 (ensemble fermé ; polyglotte -> HORS)",
        classe_qid="Q5")


@_t6("diplome_universitaire")
def ingere_diplome_universitaire():
    # personne -> diplôme/grade universitaire obtenu (P512). Scout PROPRE : ratio=0.012, fonctionnel=100%,
    # 35 valeurs distinctes (laurea, habilitation à diriger des recherches, baccalauréat ès arts, licence en
    # droit, honours degree…). Ensemble fermé strict de crédentiels académiques. FAUX=0 : `fonctionnel` écarte
    # les personnes à plusieurs diplômes -> HORS (sûr) ; ne restent que les mono-diplôme = fait biographique
    # figé. Crédential institutionnel nommé -> catégorie convention (comme religion_personne P140).
    IQ._ingere_x_vers_entite(
        "diplome_universitaire", "P512", "convention",
        "Wikidata/QLever — diplôme/grade universitaire de la personne P512 (ensemble fermé ; multi -> HORS)",
        classe_qid="Q5")


@_t6("mouvement_personne")
def ingere_mouvement_personne():
    # personne -> mouvement artistique/intellectuel (P135). Vocab SEMI-FERMÉ (impressionnisme, cubisme,
    # surréalisme, romantisme…). Beaucoup d'artistes appartiennent à >1 mouvement -> on filtre mono côté
    # serveur (HAVING=1) + streaming TSV (le scout d'agrégat sur tout Q5 timeoute). multi -> HORS (sûr).
    # Jugé hors-ligne : ratio bas re-dérivé + noyau de mouvements connus + ancres (Monet->impressionnisme).
    q = """SELECT ?eLabel ?vLabel WHERE {
      { SELECT ?e WHERE { ?e wdt:P31 wd:Q5 ; wdt:P135 ?o } GROUP BY ?e HAVING(COUNT(DISTINCT ?o)=1) }
      ?e wdt:P135 ?v .
      ?v rdfs:label ?vLabel . FILTER(lang(?vLabel)="fr")
      ?e rdfs:label ?eLabel . FILTER(lang(?eLabel)="fr")
    }"""
    print("== mouvement_personne (Wikidata/QLever P135 mono, TSV streamé) ==")
    paires = [(e, v) for e, v in _stream_paires_tsv(q, timeout=1500) if _a_une_lettre(v)]
    print(f"  {len(paires)} paires streamées (mono-mouvement, filtrées).")
    IQ.publie("mouvement_personne", "convention",
              "Wikidata/QLever — mouvement artistique/intellectuel de la personne P135 (mono ; multi -> HORS)",
              paires)


@_t6("religion_personne")
def ingere_religion_personne():
    # personne -> religion/confession. Scout PROPRE : ratio=0.037, fonctionnel=99%, 110 valeurs distinctes
    # (calvinisme, adventisme, mennonitisme, scientologie…). Ensemble fermé de confessions.
    # FAUX=0 : `fonctionnel` écarte les personnes à plusieurs religions (conversions -> HORS) ; ne restent
    # que les mono-confession = fait stable fixé par la biographie (majorité = personnages historiques).
    IQ._ingere_x_vers_entite(
        "religion_personne", "P140", "convention",
        "Wikidata/QLever — religion ou confession de la personne P140 (ensemble fermé ; multi/conversion -> HORS)",
        classe_qid="Q5")


# ---- VOCAB OUVERT (org -> personne/org ; jugé par fonctionnel + ancres, comme un lieu) ----

def _a_une_lettre(v: str) -> bool:
    return any(c.isalpha() for c in v)


@_t6("fondateur_organisation")
def ingere_fondateur_organisation():
    # org -> fondateur (personne). Fait PASSÉ (fondation, figée). Les orgs multi-fondateurs (Apple, Google…)
    # ont >1 valeur -> `fonctionnel` les met en HORS (sûr) ; ne restent que les orgs mono-fondateur.
    # FILTRE FAUX=0 (comme _est_lieu_plausible pour les lieux) : une ANNÉE de fondation fuit parfois dans P112
    # (« Feuerwehr Doren »→« 1892 ») ; un fondateur est une PERSONNE -> son libellé a toujours une lettre.
    # On REJETTE toute valeur sans lettre (date fuitée = fait FAUX). Requête identique à _ingere_x_vers_entite ;
    # le snapshot _raw/fondateur_organisation.json est réutilisé OFFLINE (pas de re-fetch).
    relation = "fondateur_organisation"
    q = (f'SELECT ?eLabel ?vLabel WHERE {{\n'
         f'  ?e wdt:P31/wdt:P279* wd:Q43229 ; wdt:P112 ?o .\n'
         f'  ?o rdfs:label ?vLabel . FILTER(lang(?vLabel)="fr")\n'
         f'  ?e rdfs:label ?eLabel . FILTER(lang(?eLabel)="fr")\n}}')
    print(f"== {relation} (Wikidata/QLever P112, filtre valeur-personne) ==")
    rows = IQ._charge_ou_fetch(relation, q)
    paires = [(e, v) for e, v in IQ._paires(rows, "eLabel", "vLabel") if _a_une_lettre(v)]
    print(f"  {len(rows)} lignes brutes -> {len(paires)} paires personne-plausibles (dates/années rejetées).")
    IQ.publie(relation, "passe",
              "Wikidata/QLever — fondateur de l'organisation P112 (mono-fondateur, valeur=personne ; multi/date -> HORS)",
              paires)


@_t6("directeur_these")
def ingere_directeur_these():
    # personne -> directeur de thèse (P184, lignée doctorale). Surtout fonctionnel (1 directeur) ; filtre mono
    # côté serveur (HAVING=1) + streaming TSV par sécurité. VOCAB OUVERT personne->personne, jugé par ancres.
    q = """SELECT ?eLabel ?vLabel WHERE {
      { SELECT ?e WHERE { ?e wdt:P31 wd:Q5 ; wdt:P184 ?o } GROUP BY ?e HAVING(COUNT(DISTINCT ?o)=1) }
      ?e wdt:P184 ?v .
      ?v rdfs:label ?vLabel . FILTER(lang(?vLabel)="fr")
      ?e rdfs:label ?eLabel . FILTER(lang(?eLabel)="fr")
    }"""
    print("== directeur_these (Wikidata/QLever P184 mono, TSV streamé) ==")
    paires = [(e, v) for e, v in _stream_paires_tsv(q, timeout=1500) if _a_une_lettre(v)]
    print(f"  {len(paires)} paires streamées (mono-directeur, filtrées).")
    IQ.publie("directeur_these", "passe",
              "Wikidata/QLever — directeur de thèse de la personne P184 (mono ; multi -> exclu serveur)",
              paires)


@_t6("nomine_pour")
def ingere_nomine_pour():
    # personne -> récompense pour laquelle elle a été NOMMÉE (P1411, distinct de prix_recu=remportée). MULTI ->
    # filtre mono côté serveur (HAVING=1) + streaming TSV. Valeur = récompense (ensemble fermé-ish). Fait PASSÉ.
    q = """SELECT ?eLabel ?vLabel WHERE {
      { SELECT ?e WHERE { ?e wdt:P31 wd:Q5 ; wdt:P1411 ?o } GROUP BY ?e HAVING(COUNT(DISTINCT ?o)=1) }
      ?e wdt:P1411 ?v .
      ?v rdfs:label ?vLabel . FILTER(lang(?vLabel)="fr")
      ?e rdfs:label ?eLabel . FILTER(lang(?eLabel)="fr")
    }"""
    print("== nomine_pour (Wikidata/QLever P1411 mono, TSV streamé) ==")
    paires = [(e, v) for e, v in _stream_paires_tsv(q, timeout=1500) if _a_une_lettre(v)]
    print(f"  {len(paires)} paires streamées (mono-nomination, filtrées).")
    IQ.publie("nomine_pour", "passe",
              "Wikidata/QLever — récompense pour laquelle la personne est nommée P1411 (mono ; multi -> exclu serveur)",
              paires)


@_t6("membre_de")
def ingere_membre_de():
    # personne -> organisation dont elle est membre (P463 : académies, sociétés savantes, ordres…). MULTI ->
    # filtre mono côté serveur (HAVING=1) + streaming TSV. VOCAB OUVERT, jugé par ancres reconnaissables.
    q = """SELECT ?eLabel ?vLabel WHERE {
      { SELECT ?e WHERE { ?e wdt:P31 wd:Q5 ; wdt:P463 ?o } GROUP BY ?e HAVING(COUNT(DISTINCT ?o)=1) }
      ?e wdt:P463 ?v .
      ?v rdfs:label ?vLabel . FILTER(lang(?vLabel)="fr")
      ?e rdfs:label ?eLabel . FILTER(lang(?eLabel)="fr")
    }"""
    print("== membre_de (Wikidata/QLever P463 mono, TSV streamé) ==")
    paires = [(e, v) for e, v in _stream_paires_tsv(q, timeout=1500) if _a_une_lettre(v)]
    print(f"  {len(paires)} paires streamées (mono-appartenance, filtrées).")
    IQ.publie("membre_de", "convention",
              "Wikidata/QLever — organisation dont la personne est membre P463 (mono ; multi -> exclu serveur)",
              paires)


@_t6("employeur_personne")
def ingere_employeur_personne():
    # personne -> employeur (P108, surtout organisation : université/entreprise). MULTI (carrière) -> filtre
    # mono côté serveur (HAVING=1) + streaming TSV. VOCAB OUVERT, jugé par ancres reconnaissables. Fait PASSÉ.
    q = """SELECT ?eLabel ?vLabel WHERE {
      { SELECT ?e WHERE { ?e wdt:P31 wd:Q5 ; wdt:P108 ?o } GROUP BY ?e HAVING(COUNT(DISTINCT ?o)=1) }
      ?e wdt:P108 ?v .
      ?v rdfs:label ?vLabel . FILTER(lang(?vLabel)="fr")
      ?e rdfs:label ?eLabel . FILTER(lang(?eLabel)="fr")
    }"""
    print("== employeur_personne (Wikidata/QLever P108 mono, TSV streamé) ==")
    paires = [(e, v) for e, v in _stream_paires_tsv(q, timeout=1500) if _a_une_lettre(v)]
    print(f"  {len(paires)} paires streamées (mono-employeur, filtrées).")
    IQ.publie("employeur_personne", "passe",
              "Wikidata/QLever — employeur de la personne P108 (mono ; multi -> exclu serveur)",
              paires)


@_t6("etudie_a")
def ingere_etudie_a():
    # personne -> établissement d'études (P69 « educated at »). MULTI (plusieurs écoles) -> filtre mono côté
    # serveur (HAVING=1) + streaming TSV. VOCAB OUVERT (valeur=institution), jugé par ancres reconnaissables.
    # Fait PASSÉ. Valeur=institution -> lettre (pas de fuite date, mais filtre lettre conservé via validateur).
    q = """SELECT ?eLabel ?vLabel WHERE {
      { SELECT ?e WHERE { ?e wdt:P31 wd:Q5 ; wdt:P69 ?o } GROUP BY ?e HAVING(COUNT(DISTINCT ?o)=1) }
      ?e wdt:P69 ?v .
      ?v rdfs:label ?vLabel . FILTER(lang(?vLabel)="fr")
      ?e rdfs:label ?eLabel . FILTER(lang(?eLabel)="fr")
    }"""
    print("== etudie_a (Wikidata/QLever P69 mono, TSV streamé) ==")
    paires = [(e, v) for e, v in _stream_paires_tsv(q, timeout=1500) if _a_une_lettre(v)]
    print(f"  {len(paires)} paires streamées (mono-établissement, filtrées).")
    IQ.publie("etudie_a", "passe",
              "Wikidata/QLever — établissement d'études de la personne P69 (mono ; multi -> exclu serveur)",
              paires)


@_t6("eleve_de")
def ingere_eleve_de():
    # personne (élève) -> maître/professeur (P1066 « élève de »). VOCAB OUVERT personne->personne, jugé par ancres
    # (lignées savantes : Aristote->Platon->Socrate). Filtre mono côté serveur (HAVING=1) + streaming TSV.
    # Distinct de maitre_philosophe (T12 = P1066 restreint occupation=philosophe) : table au nom différent,
    # non-conflictuelle ; léger recouvrement sur les philosophes (mêmes faits vrais, FAUX=0). Fait PASSÉ.
    q = """SELECT ?eLabel ?vLabel WHERE {
      { SELECT ?e WHERE { ?e wdt:P31 wd:Q5 ; wdt:P1066 ?o } GROUP BY ?e HAVING(COUNT(DISTINCT ?o)=1) }
      ?e wdt:P1066 ?v .
      ?v rdfs:label ?vLabel . FILTER(lang(?vLabel)="fr")
      ?e rdfs:label ?eLabel . FILTER(lang(?eLabel)="fr")
    }"""
    print("== eleve_de (Wikidata/QLever P1066 mono, TSV streamé) ==")
    paires = list(_stream_paires_tsv(q, timeout=1500))
    print(f"  {len(paires)} paires streamées (mono-maître, filtrées).")
    IQ.publie("eleve_de", "passe",
              "Wikidata/QLever — maître de la personne P1066 « élève de » (mono ; multi -> exclu serveur)",
              paires)


@_t6("conjoint_personne")
def ingere_conjoint_personne():
    # personne -> conjoint (époux/se). P26 est MULTI (remariages) -> filtre mono côté serveur (HAVING=1) +
    # streaming TSV. VOCAB OUVERT (valeur=personne) jugé par ancres (couples monogames célèbres). Pas de fuite
    # date (valeur=personne -> lettre). Fait social/légal -> convention. Les remariés -> exclus serveur (sûr).
    q = """SELECT ?eLabel ?vLabel WHERE {
      { SELECT ?e WHERE { ?e wdt:P31 wd:Q5 ; wdt:P26 ?o } GROUP BY ?e HAVING(COUNT(DISTINCT ?o)=1) }
      ?e wdt:P26 ?v .
      ?v rdfs:label ?vLabel . FILTER(lang(?vLabel)="fr")
      ?e rdfs:label ?eLabel . FILTER(lang(?eLabel)="fr")
    }"""
    print("== conjoint_personne (Wikidata/QLever P26 mono, TSV streamé) ==")
    paires = list(_stream_paires_tsv(q, timeout=1500))
    print(f"  {len(paires)} paires streamées (mono-conjoint, filtrées).")
    IQ.publie("conjoint_personne", "convention",
              "Wikidata/QLever — conjoint de la personne P26 (mono ; remariages -> exclus serveur)",
              paires)


@_t6("pere_personne")
def ingere_pere_personne():
    # personne -> père (personne). VOCAB OUVERT (jugé comme fondateur : fonctionnel + ancres, pas ratio).
    # Scout : fonctionnel=99% (un père biologique). Valeur = personne -> toujours une lettre (pas de fuite date).
    # Distinct de pere_divinite (T12 = divinités Q22989102). Fait PHYSIQUE (filiation biologique).
    IQ._ingere_x_vers_entite(
        "pere_personne", "P22", "physique",
        "Wikidata/QLever — père de la personne P22 (valeur=personne ; multi -> HORS)",
        classe_qid="Q5")


@_t6("mere_personne")
def ingere_mere_personne():
    # personne -> mère (personne). VOCAB OUVERT (fonctionnel + ancres). Scout fonctionnel=99%.
    # Distinct de mere_divinite (T12). Fait PHYSIQUE (filiation biologique).
    IQ._ingere_x_vers_entite(
        "mere_personne", "P25", "physique",
        "Wikidata/QLever — mère de la personne P25 (valeur=personne ; multi -> HORS)",
        classe_qid="Q5")


@_t6("proprietaire_organisation")
def ingere_proprietaire_organisation():
    # organisation -> propriétaire (P127, plus large que maison_mère P749 : owner = personne/État/holding).
    # VOCAB OUVERT (fonctionnel + ancres). Scout ratio haut = NORMAL. multi-propriétaire -> HORS.
    # FILTRE FAUX=0 (comme fondateur) : une ANNÉE fuit parfois dans P127 (« château de Dio »→« 1203 ») ; un
    # propriétaire a toujours une lettre -> on REJETTE toute valeur sans lettre (date fuitée = fait FAUX).
    relation = "proprietaire_organisation"
    q = (f'SELECT ?eLabel ?vLabel WHERE {{\n'
         f'  ?e wdt:P31/wdt:P279* wd:Q43229 ; wdt:P127 ?o .\n'
         f'  ?o rdfs:label ?vLabel . FILTER(lang(?vLabel)="fr")\n'
         f'  ?e rdfs:label ?eLabel . FILTER(lang(?eLabel)="fr")\n}}')
    print(f"== {relation} (Wikidata/QLever P127, filtre valeur-propriétaire) ==")
    rows = IQ._charge_ou_fetch(relation, q)
    paires = [(e, v) for e, v in IQ._paires(rows, "eLabel", "vLabel") if _a_une_lettre(v)]
    print(f"  {len(rows)} lignes brutes -> {len(paires)} paires propriétaire-plausibles (dates rejetées).")
    IQ.publie(relation, "convention",
              "Wikidata/QLever — propriétaire de l'organisation P127 (valeur=propriétaire ; multi/date -> HORS)",
              paires)


@_t6("maison_mere")
def ingere_maison_mere():
    # entreprise -> maison-mère. Propriété actuelle (révisable) ; les filiales à plusieurs propriétaires
    # historiques+actuels -> `fonctionnel` -> HORS. fonctionnel mesuré 99 % au scout.
    IQ._ingere_x_vers_entite(
        "maison_mere", "P749", "physique",
        "Wikidata/QLever — maison-mère de l'entreprise P749",
        classe_qid="Q4830453")


@_t6("prenom")
def ingere_prenom():
    # personne -> prénom (P735, valeur = item « prénom »). MULTI possible (plusieurs prénoms) -> filtre mono
    # CÔTÉ SERVEUR (HAVING COUNT(DISTINCT)=1) + streaming TSV (veine massive, millions de lignes brutes -> pas
    # de JSON plein, pas d'OOM ; débloquée par RAM libre + validateur per-relation). FAUX=0 : HAVING=1 garantit
    # l'unicité ; valeur = prénom nommé. Scout ratio=0.077, fonctionnel=100% (Albin/Franziska/Bud...).
    # Ancres triviales (Albert Einstein -> Albert). Filtre lettre = filet (un prénom a toujours une lettre).
    q = """SELECT ?eLabel ?vLabel WHERE {
      { SELECT ?e WHERE { ?e wdt:P31 wd:Q5 ; wdt:P735 ?o } GROUP BY ?e HAVING(COUNT(DISTINCT ?o)=1) }
      ?e wdt:P735 ?v .
      ?v rdfs:label ?vLabel . FILTER(lang(?vLabel)="fr")
      ?e rdfs:label ?eLabel . FILTER(lang(?eLabel)="fr")
    }"""
    print("== prenom (Wikidata/QLever P735 mono, TSV streamé) ==")
    paires = [(e, v) for e, v in _stream_paires_tsv(q, timeout=1800) if _a_une_lettre(v)]
    print(f"  {len(paires)} paires streamées (mono-prénom, filtrées).")
    IQ.publie("prenom", "physique",
              "Wikidata/QLever — prénom de la personne P735 (mono HAVING=1 ; multi -> exclu serveur)",
              paires)


@_t6("nom_famille")
def ingere_nom_famille():
    # personne -> nom de famille (P734, valeur = item « nom de famille »). MULTI possible -> filtre mono
    # CÔTÉ SERVEUR (HAVING=1) + streaming TSV. Même schéma que prenom. FAUX=0 : HAVING=1 + valeur nommée.
    # Ancres triviales (Albert Einstein -> Einstein). Filtre lettre = filet.
    q = """SELECT ?eLabel ?vLabel WHERE {
      { SELECT ?e WHERE { ?e wdt:P31 wd:Q5 ; wdt:P734 ?o } GROUP BY ?e HAVING(COUNT(DISTINCT ?o)=1) }
      ?e wdt:P734 ?v .
      ?v rdfs:label ?vLabel . FILTER(lang(?vLabel)="fr")
      ?e rdfs:label ?eLabel . FILTER(lang(?eLabel)="fr")
    }"""
    print("== nom_famille (Wikidata/QLever P734 mono, TSV streamé) ==")
    paires = [(e, v) for e, v in _stream_paires_tsv(q, timeout=1800) if _a_une_lettre(v)]
    print(f"  {len(paires)} paires streamées (mono-nom, filtrées).")
    IQ.publie("nom_famille", "physique",
              "Wikidata/QLever — nom de famille de la personne P734 (mono HAVING=1 ; multi -> exclu serveur)",
              paires)


@_t6("systeme_cristallin")
def ingere_systeme_cristallin():
    # PIVOT minéralogie (PERSONNES/ORGS saturé) : espèce minérale -> système cristallin (P556). Ensemble FERMÉ
    # (7 systèmes cristallins IAU + matière amorphe) : scout ratio=0.008, fonctionnel=100%. Propriété PHYSIQUE
    # (la réalité fixe la structure). classe Q12089225 = espèce minérale. fonctionnel -> minéraux dimorphes (>1
    # système) en HORS = FAUX=0. Ancres diamant->cubique, quartz->trigonal, halite->cubique.
    IQ._ingere_x_vers_entite(
        "systeme_cristallin", "P556", "physique",
        "Wikidata/QLever — système cristallin de l'espèce minérale P556 (ensemble fermé ; dimorphes -> HORS)",
        classe_qid="Q12089225")


@_t6("couleur_trait_mineral")
def ingere_couleur_trait_mineral():
    # minéralogie : espèce minérale -> couleur du trait (P534, streak = couleur de la poudre, DISTINCTE de la
    # couleur visible du minéral). Ensemble FERMÉ de couleurs : scout ratio=0.048, fonctionnel=100% (~20 couleurs).
    # Propriété PHYSIQUE (déterminée par essai du trait). fonctionnel -> minéraux à trait variable en HORS.
    # Ancres hématite->rouge, pyrite->noir, soufre->blanc/jaune (vérifiées sur la donnée réelle).
    IQ._ingere_x_vers_entite(
        "couleur_trait_mineral", "P534", "physique",
        "Wikidata/QLever — couleur du trait de l'espèce minérale P534 (ensemble fermé de couleurs ; streak)",
        classe_qid="Q12089225")


# NON-matériaux à exclure de materiau_construction (P186/Q41176) : débusqués atome par atome sur le _raw.
# Bâtiments mal classés (centrales -> fuel/réacteur), surfaces de stade, arbres bruts (le matériau = « bois de
# X », pas l'espèce), technique picturale. Le reste des 178 valeurs = matériaux réels (pierre/brique/béton/…).
_NON_MATERIAUX_BATI = frozenset({
    "réacteur à eau pressurisée", "gaz naturel", "sel alimentaire",
    "AstroTurf", "Desso GrassMaster", "pelouse artificielle",
    "Sequoia sempervirens", "cyprès", "arbre", "tronc", "Mätas", "fresque",
})


# NON-matériaux à exclure de materiau_meuble (P186/Q14745) : débusqués atome par atome sur le _raw. Médias
# picturaux (tableaux mal classés en meuble), genres d'arbres bruts, divers. Reste des 122 valeurs = matériaux
# d'ameublement réels (bois/pierre/métaux/textiles cuir-soie-laine/céramiques).
_NON_MATERIAUX_MEUBLE = frozenset({
    "peinture à l'huile", "tempera", "fresque", "estampe", "techniques mixtes",
    "Jacaranda", "Castanea", "canette d'aluminium",
})


# REJET materiau_statue (P186/Q179700) : overlap 95,4 % avec materiau_objet_art (T5, Q860861 sculpture inclut
# les statues) -> quasi-doublon, non ingéré. LEÇON : mesurer l'overlap par ENTITÉ avant de certifier.


# Mots-clés de TYPE de juridiction ecclésiale (whitelist FAUX=0 pour diocese_eglise). P708 mélange de vraies
# juridictions territoriales (diocèses/archidiocèses/éparchies/préfectures apostoliques…) ET des DÉNOMINATIONS
# qui ne sont PAS des diocèses (« Église orthodoxe russe », « Saint-Siège », « Église protestante… ») -> on ne
# garde QUE les valeurs nommant une juridiction de type diocèse (vérifié atome par atome sur le _raw).
_TYPES_JURIDICTION_DIOCESE = (
    "diocèse", "archidiocèse", "éparchie", "archéparchie", "évêché", "archevêché", "métropole",
    "exarchat", "ordinariat", "prélature", "vicariat apostolique", "préfecture apostolique",
    "administration apostolique", "patriarcat", "abbaye territoriale", "mission sui iuris",
)


def _est_juridiction_diocese(v: str) -> bool:
    vl = v.lower()
    return any(k in vl for k in _TYPES_JURIDICTION_DIOCESE)


# NON-plateformes à exclure de plateforme_jeu (P400/Q7889), débusquées atome par atome : méta-valeurs, CPU/
# langages/VM bruts, protocoles web, un mode, et un jeu (Psycho Soldier). On GARDE les catégories-plateformes
# légitimes (arcade/navigateur web/téléphone mobile/ordinateur personnel/mainframe) et les cartes d'arcade.
_NON_PLATEFORMES_JEU = frozenset({
    "multiplateforme", "jeu vidéo", "en ligne et hors-ligne", "Open Graph Protocol",
    "moteur de rendu HTML", "Java", "machine virtuelle Java", "Zilog Z80", "Intel 8080",
    "PowerPC 620", "X64", "GNU Emacs", "Psycho Soldier",
})


# NON-formats à exclure de format_distribution_film (P437/Q11424), débusqués atome par atome : distributeurs/
# réseaux (≠ format), formats MUSIQUE, divers (livre/durée/résolution). Reste = vrais formats de distribution.
_NON_FORMATS_FILM = frozenset({
    "CBS", "Colmax", "Voltage Pictures", "Warner Bros.", "Télévision Algérienne", "Universidad del Cine",
    "Amazon Prime Video", "Manga Films", "streaming musical", "téléchargement de musique", "cassette audio",
    "livre cartonné", "moyen métrage", "4K",
})


# Mots-clés de SUPPORT de distribution de jeu (whitelist FAUX=0). P437/Q7889 est très bruité (plateformes,
# services, unités de données, modes, sociétés, termes ciné) -> on ne garde QUE les valeurs nommant un support
# physique/numérique. Vérifié atome par atome sur le _raw. + petit blocklist d'une valeur-musique parasite.
_FMT_SUPPORT_KW = (
    "cartouche", "disque", "disquette", "rom", "dvd", "cd", "carte", "card", "cassette", "pak",
    "umd", "media disc", "téléchargement", "numérique", "mémoire", "flash", "solid-state",
    "blu-ray", "laserdisc", "bande magnétique", "disk",
)
_FMT_JEU_BLOQUE = frozenset({"téléchargement de musique"})


def _est_support_jeu(v: str) -> bool:
    if v in _FMT_JEU_BLOQUE:
        return False
    vl = v.lower()
    return any(k in vl for k in _FMT_SUPPORT_KW)


@_t6("format_distribution_jeu")
def ingere_format_distribution_jeu():
    # jeu vidéo -> format/support de distribution (P437). DISTINCT de plateforme_jeu (P400 = console). ratio
    # 0.022, fonctionnel 96%. FAUX=0 : (1) multi→HORS via publie ; (2) WHITELIST `_est_support_jeu` ne garde que
    # les supports (cartouche/disque/CD-ROM/cartes/téléchargement/numérique/mémoire…), écarte plateformes/
    # services/unités/modes/sociétés/termes ciné. classe Q7889. _raw réutilisé offline.
    relation = "format_distribution_jeu"
    q = (f'SELECT ?eLabel ?vLabel WHERE {{\n'
         f'  ?e wdt:P31/wdt:P279* wd:Q7889 ; wdt:P437 ?o .\n'
         f'  ?o rdfs:label ?vLabel . FILTER(lang(?vLabel)="fr")\n'
         f'  ?e rdfs:label ?eLabel . FILTER(lang(?eLabel)="fr")\n}}')
    print(f"== {relation} (Wikidata/QLever P437, whitelist supports) ==")
    rows = IQ._charge_ou_fetch(relation, q)
    paires = [(e, v) for e, v in IQ._paires(rows, "eLabel", "vLabel") if _est_support_jeu(v)]
    print(f"  {len(rows)} lignes brutes -> {len(paires)} paires (supports ; bruit rejeté).")
    IQ.publie(relation, "convention",
              "Wikidata/QLever — format de distribution du jeu vidéo P437 (support ; multi/non-support -> HORS)",
              paires)


# REJET format_episode_podcast (P437/Q61855877) : le filtre label-entité-FR effondre la veine à 48 faits mono
# « balado » (épisodes podcast rarement labellés FR ; balado vidéo disparaît) -> sparse+mono, gate FAIL. LEÇON :
# vérifier le compte APRÈS le filtre label-FR de l'ingestion (le compte direct sans ce filtre peut être trompeur).


@_t6("format_edition")
def ingere_format_edition():
    # édition/version/traduction d'œuvre -> format (P437). QID Q3331189 (découverte top-P437, 108k). ⚠️ overlap à
    # mesurer vs format_album/single/film (éditions musicales/ciné = versions). FAUX=0 : multi→HORS via publie.
    # Valeurs vérifiées atome par atome. classe Q3331189. Convention.
    relation = "format_edition"
    bloque = frozenset({"streaming musical"})  # format musical parasite dans une relation d'éditions (livres)
    q = (f'SELECT ?eLabel ?vLabel WHERE {{\n'
         f'  ?e wdt:P31/wdt:P279* wd:Q3331189 ; wdt:P437 ?o .\n'
         f'  ?o rdfs:label ?vLabel . FILTER(lang(?vLabel)="fr")\n'
         f'  ?e rdfs:label ?eLabel . FILTER(lang(?eLabel)="fr")\n}}')
    print(f"== {relation} (Wikidata/QLever P437 Q3331189, blocklist musical) ==")
    rows = IQ._charge_ou_fetch(relation, q)
    paires = [(e, v) for e, v in IQ._paires(rows, "eLabel", "vLabel") if v not in bloque]
    print(f"  {len(rows)} lignes brutes -> {len(paires)} paires (formats d'édition).")
    IQ.publie(relation, "convention",
              "Wikidata/QLever — format de l'édition/version P437 (mono ; multi/format-musical -> HORS)",
              paires)


@_t6("format_single")
def ingere_format_single():
    # single musical -> format de parution (P437). Classe Q134556 (overlap mesuré 3,9% vs format_album = disjoint,
    # PAS un doublon). ratio 0.003, fonctionnel 98%. FAUX=0 : (1) multi→HORS via publie ; (2) BLOCKLIST 5 intrus
    # (terme ciné/mode radio/podcast/type-de-release), vérifiés atome par atome. _raw réutilisé offline.
    relation = "format_single"
    bloque = frozenset({"direct-to-video", "airplay", "vidéo à la demande", "balado", "enregistrement promotionnel"})
    q = (f'SELECT ?eLabel ?vLabel WHERE {{\n'
         f'  ?e wdt:P31/wdt:P279* wd:Q134556 ; wdt:P437 ?o .\n'
         f'  ?o rdfs:label ?vLabel . FILTER(lang(?vLabel)="fr")\n'
         f'  ?e rdfs:label ?eLabel . FILTER(lang(?eLabel)="fr")\n}}')
    print(f"== {relation} (Wikidata/QLever P437, blocklist non-formats) ==")
    rows = IQ._charge_ou_fetch(relation, q)
    paires = [(e, v) for e, v in IQ._paires(rows, "eLabel", "vLabel") if v not in bloque]
    print(f"  {len(rows)} lignes brutes -> {len(paires)} paires (formats ; non-formats rejetés).")
    IQ.publie(relation, "convention",
              "Wikidata/QLever — format de parution du single P437 (mono ; multi/non-format -> HORS)",
              paires)


@_t6("format_album")
def ingere_format_album():
    # album musical -> format de parution (P437). DISTINCT de format_distribution_film (classe album ≠ film).
    # ratio 0.007, fonctionnel 100% (~56 formats : CD/vinyle/LP/cassette/configs multi-disques/streaming/
    # téléchargement + formats vidéo-albums VHS/DVD/Laserdisc). FAUX=0 : (1) multi→HORS via publie ; (2) BLOCKLIST
    # `direct-to-video` (terme de sortie ciné, pas un medium) / `livre audio` / `balado` (podcast). Vérifié atome
    # par atome sur le _raw. classe Q482994 = album. _raw réutilisé offline.
    relation = "format_album"
    bloque = frozenset({"direct-to-video", "livre audio", "balado"})
    q = (f'SELECT ?eLabel ?vLabel WHERE {{\n'
         f'  ?e wdt:P31/wdt:P279* wd:Q482994 ; wdt:P437 ?o .\n'
         f'  ?o rdfs:label ?vLabel . FILTER(lang(?vLabel)="fr")\n'
         f'  ?e rdfs:label ?eLabel . FILTER(lang(?eLabel)="fr")\n}}')
    print(f"== {relation} (Wikidata/QLever P437, blocklist non-formats) ==")
    rows = IQ._charge_ou_fetch(relation, q)
    paires = [(e, v) for e, v in IQ._paires(rows, "eLabel", "vLabel") if v not in bloque]
    print(f"  {len(rows)} lignes brutes -> {len(paires)} paires (formats ; non-formats rejetés).")
    IQ.publie(relation, "convention",
              "Wikidata/QLever — format de parution de l'album P437 (mono ; multi/non-format -> HORS)",
              paires)


@_t6("format_distribution_film")
def ingere_format_distribution_film():
    # film -> format/mode de distribution (P437). ATTRIBUT distinct du canon T5. ratio 0.025, fonctionnel 93%
    # (sortie en salle/VOD/VHS/Blu-ray/téléchargement…). FAUX=0 : (1) multi-format→HORS via publie ; (2) BLOCKLIST
    # `_NON_FORMATS_FILM` (distributeurs/formats musique/divers). classe Q11424. _raw réutilisé offline.
    relation = "format_distribution_film"
    q = (f'SELECT ?eLabel ?vLabel WHERE {{\n'
         f'  ?e wdt:P31/wdt:P279* wd:Q11424 ; wdt:P437 ?o .\n'
         f'  ?o rdfs:label ?vLabel . FILTER(lang(?vLabel)="fr")\n'
         f'  ?e rdfs:label ?eLabel . FILTER(lang(?eLabel)="fr")\n}}')
    print(f"== {relation} (Wikidata/QLever P437, blocklist non-formats) ==")
    rows = IQ._charge_ou_fetch(relation, q)
    paires = [(e, v) for e, v in IQ._paires(rows, "eLabel", "vLabel") if v not in _NON_FORMATS_FILM]
    print(f"  {len(rows)} lignes brutes -> {len(paires)} paires (formats ; non-formats rejetés).")
    IQ.publie(relation, "convention",
              "Wikidata/QLever — format de distribution du film P437 (mono ; multi/non-format -> HORS)",
              paires)


@_t6("plateforme_jeu")
def ingere_plateforme_jeu():
    # jeu vidéo -> plateforme (P400). ATTRIBUT distinct de mode_jeu_video (P404) et de genre (T5). ratio 0.02,
    # fonctionnel 94%, plateformes (PlayStation/Amiga/Neo-Geo/PC-Engine/CD-i…). FAUX=0 : (1) jeu multi-plateforme
    # →HORS via publie (mono = exclusivités/rétro = fait figé) ; (2) BLOCKLIST `_NON_PLATEFORMES_JEU` (méta/CPU/
    # langages/protocoles/jeu). classe Q7889. _raw réutilisé offline.
    relation = "plateforme_jeu"
    q = (f'SELECT ?eLabel ?vLabel WHERE {{\n'
         f'  ?e wdt:P31/wdt:P279* wd:Q7889 ; wdt:P400 ?o .\n'
         f'  ?o rdfs:label ?vLabel . FILTER(lang(?vLabel)="fr")\n'
         f'  ?e rdfs:label ?eLabel . FILTER(lang(?eLabel)="fr")\n}}')
    print(f"== {relation} (Wikidata/QLever P400, blocklist non-plateformes) ==")
    rows = IQ._charge_ou_fetch(relation, q)
    paires = [(e, v) for e, v in IQ._paires(rows, "eLabel", "vLabel") if v not in _NON_PLATEFORMES_JEU]
    print(f"  {len(rows)} lignes brutes -> {len(paires)} paires (plateformes ; non-plateformes rejetées).")
    IQ.publie(relation, "convention",
              "Wikidata/QLever — plateforme du jeu vidéo P400 (mono-plateforme ; multi/non-plateforme -> HORS)",
              paires)


@_t6("diocese_eglise")
def ingere_diocese_eglise():
    # église (bâtiment) -> diocèse de rattachement (P708). DISTINCT de diocese_personne (personne→diocèse).
    # Inventaire dense (Palissy/églises). ratio 0.067, fonctionnel 99%. Fait administratif stable (une église
    # rattachée à UN diocèse). FAUX=0 en DEUX gardes : (1) multi→HORS via publie ; (2) WHITELIST
    # `_est_juridiction_diocese` : ne publie QUE les valeurs nommant une juridiction de type diocèse (écarte les
    # dénominations « Église orthodoxe/protestante… », « Saint-Siège », noms nus). classe Q16970. _raw offline.
    relation = "diocese_eglise"
    q = (f'SELECT ?eLabel ?vLabel WHERE {{\n'
         f'  ?e wdt:P31/wdt:P279* wd:Q16970 ; wdt:P708 ?o .\n'
         f'  ?o rdfs:label ?vLabel . FILTER(lang(?vLabel)="fr")\n'
         f'  ?e rdfs:label ?eLabel . FILTER(lang(?eLabel)="fr")\n}}')
    print(f"== {relation} (Wikidata/QLever P708, whitelist juridiction-diocèse) ==")
    rows = IQ._charge_ou_fetch(relation, q)
    paires = [(e, v) for e, v in IQ._paires(rows, "eLabel", "vLabel") if _est_juridiction_diocese(v)]
    print(f"  {len(rows)} lignes brutes -> {len(paires)} paires (juridictions-diocèse ; dénominations rejetées).")
    IQ.publie(relation, "convention",
              "Wikidata/QLever — diocèse de rattachement de l'église P708 (juridiction-diocèse ; multi/dénomination -> HORS)",
              paires)


@_t6("robe_cheval")
def ingere_robe_cheval():
    # cheval -> couleur de robe (P462). Domaine no-lane (distinct de la bio T4). ratio 0.008, fonctionnel 97%,
    # ~19 robes nettes (gris/alezan/bai/noir/bai foncé/pie/aubère/isabelle/palomino/Tobiano…) = ensemble FERMÉ.
    # Fait physique figé (un cheval A une robe). FAUX=0 : (1) multi→HORS via publie ; (2) BLOCKLIST des 2 valeurs
    # qui nomment un GÈNE et non une robe (vérifiées atome par atome sur le _raw). classe Q726. _raw offline.
    relation = "robe_cheval"
    bloque = frozenset({"Gène rouan du cheval", "gène crème du cheval"})
    q = (f'SELECT ?eLabel ?vLabel WHERE {{\n'
         f'  ?e wdt:P31/wdt:P279* wd:Q726 ; wdt:P462 ?o .\n'
         f'  ?o rdfs:label ?vLabel . FILTER(lang(?vLabel)="fr")\n'
         f'  ?e rdfs:label ?eLabel . FILTER(lang(?eLabel)="fr")\n}}')
    print(f"== {relation} (Wikidata/QLever P462, blocklist gènes) ==")
    rows = IQ._charge_ou_fetch(relation, q)
    paires = [(e, v) for e, v in IQ._paires(rows, "eLabel", "vLabel") if v not in bloque]
    print(f"  {len(rows)} lignes brutes -> {len(paires)} paires (robes ; gènes rejetés).")
    IQ.publie(relation, "physique",
              "Wikidata/QLever — couleur de robe du cheval P462 (ensemble fermé ; multi/gène -> HORS)",
              paires)


@_t6("materiau_vase")
def ingere_materiau_vase():
    # vase/récipient -> matériau (P186). Domaine arts décoratifs (sans lane). ratio 0.096, fonctionnel 82%
    # (~55 valeurs : terre cuite/porcelaine/faïence/céramique/verre/argile/bronze/albâtre…). Fait physique.
    # FAUX=0 : (1) multi-matériau→HORS via publie ; (2) BLOCKLIST `émaillage du verre` (technique, pas matériau ;
    # seul intrus débusqué atome par atome — boue/bitume/chlorites sont des matériaux réels, gardés). classe
    # Q191851 = vase (P31/P279*). _raw réutilisé offline.
    relation = "materiau_vase"
    bloque = frozenset({"émaillage du verre"})
    q = (f'SELECT ?eLabel ?vLabel WHERE {{\n'
         f'  ?e wdt:P31/wdt:P279* wd:Q191851 ; wdt:P186 ?o .\n'
         f'  ?o rdfs:label ?vLabel . FILTER(lang(?vLabel)="fr")\n'
         f'  ?e rdfs:label ?eLabel . FILTER(lang(?eLabel)="fr")\n}}')
    print(f"== {relation} (Wikidata/QLever P186, blocklist technique) ==")
    rows = IQ._charge_ou_fetch(relation, q)
    paires = [(e, v) for e, v in IQ._paires(rows, "eLabel", "vLabel") if v not in bloque]
    print(f"  {len(rows)} lignes brutes -> {len(paires)} paires (matériaux ; technique rejetée).")
    IQ.publie(relation, "physique",
              "Wikidata/QLever — matériau du vase/récipient P186 (mono-matériau ; multi/technique -> HORS)",
              paires)


@_t6("materiau_meuble")
def ingere_materiau_meuble():
    # meuble/mobilier -> matériau (P186). Vocab SEMI-OUVERT (bois de chêne/pin/frêne/ébène, métal, étain, verre,
    # textiles d'ameublement…). Fait physique du mobilier. FAUX=0 en DEUX gardes : (1) multi-matériau→HORS via
    # publie ; (2) BLOCKLIST `_NON_MATERIAUX_MEUBLE` retire les médias picturaux (tableaux mal classés) + arbres
    # bruts, vérifiés sur le _raw. classe Q14745 = meuble (P31/P279*). _raw réutilisé offline.
    relation = "materiau_meuble"
    q = (f'SELECT ?eLabel ?vLabel WHERE {{\n'
         f'  ?e wdt:P31/wdt:P279* wd:Q14745 ; wdt:P186 ?o .\n'
         f'  ?o rdfs:label ?vLabel . FILTER(lang(?vLabel)="fr")\n'
         f'  ?e rdfs:label ?eLabel . FILTER(lang(?eLabel)="fr")\n}}')
    print(f"== {relation} (Wikidata/QLever P186, blocklist non-matériaux) ==")
    rows = IQ._charge_ou_fetch(relation, q)
    paires = [(e, v) for e, v in IQ._paires(rows, "eLabel", "vLabel") if v not in _NON_MATERIAUX_MEUBLE]
    print(f"  {len(rows)} lignes brutes -> {len(paires)} paires (matériaux ; non-matériaux rejetés).")
    IQ.publie(relation, "physique",
              "Wikidata/QLever — matériau du meuble P186 (mono-matériau ; multi/non-matériau -> HORS)",
              paires)


# REJET materiau_fontaine (P186/Q483453) : overlap 87 % avec materiau_construction (Q483453 fontaine ⊂ Q41176
# bâtiment) -> quasi-doublon, non ingéré. Idem materiau_porte (Q36794) probablement (portes de bâtiments).


# REJET format_episode_tv (P437/Q21191270) : après filtre fonctionnel (multi→HORS), s'effondre à mono VOD (945)
# — les épisodes à variété (VOD+VHS) sont multi-format → rejetés, ne restent que mono-VOD. ── PIPELINE P437
# CONCLU : 1 atome frais (format_edition Q3331189) ; classes album/single/film/jeu/série DONE ; épisodes-TV/podcast
# s'effondrent (mono/FR-label). LEÇON : variété apparente en MULTI-valeur ≠ variété après filtre fonctionnel.


@_t6("format_distribution_serie")
def ingere_format_distribution_serie():
    # série TV -> format/mode de distribution (P437). Classe Q5398426 (entités disjointes des films). ratio 0.01,
    # fonctionnel 96% (VOD/télévision/streaming/Blu-ray/télédiffusion…). FAUX=0 : (1) multi→HORS via publie ;
    # (2) BLOCKLIST du bruit (podcast/musique/genre/société/résolution/protocole), vérifié atome par atome.
    relation = "format_distribution_serie"
    bloque = frozenset({"direct-to-video", "balado", "balado vidéo", "streaming musical", "telenarconovela",
                        "Red Book", "Warner Bros.", "série télévisée", "site web", "4K", "BitTorrent"})
    q = (f'SELECT ?eLabel ?vLabel WHERE {{\n'
         f'  ?e wdt:P31/wdt:P279* wd:Q5398426 ; wdt:P437 ?o .\n'
         f'  ?o rdfs:label ?vLabel . FILTER(lang(?vLabel)="fr")\n'
         f'  ?e rdfs:label ?eLabel . FILTER(lang(?eLabel)="fr")\n}}')
    print(f"== {relation} (Wikidata/QLever P437, blocklist non-formats) ==")
    rows = IQ._charge_ou_fetch(relation, q)
    paires = [(e, v) for e, v in IQ._paires(rows, "eLabel", "vLabel") if v not in bloque]
    print(f"  {len(rows)} lignes brutes -> {len(paires)} paires (formats ; non-formats rejetés).")
    IQ.publie(relation, "convention",
              "Wikidata/QLever — format de distribution de la série TV P437 (mono ; multi/non-format -> HORS)",
              paires)


# REJET couleur_court_metrage (P462/Q24862) : overlap 95% couleur_film (court-métrage ⊂ film). Idem prévisible
# pour téléfilm/film-animation/film-muet/mini-série (⊂ Q11424). Seules classes P462 FRAÎCHES = non-film/non-série.


# REJET couleur_clip (P462/Q193977) : 108 faits (sparse) + overlap 91% couleur_film. ── PIPELINE P462 CONCLU :
# 1 atome frais (couleur_episode Q21191270) ; reste = sous-classes de film (overlap quasi-total) ou sparse.


@_t6("couleur_episode")
def ingere_couleur_episode():
    # épisode de série TV -> statut couleur (P462). classe Q21191270 (découverte top-P462, 7454 ent), DISTINCTE
    # des séries (Q5398426) ET des films (Q11424) -> entités fraîches. Whitelist statuts couleur (comme
    # couleur_serie). FAUX=0 : (1) multi→HORS via publie ; (2) WHITELIST. overlap mesuré vs couleur_film/serie.
    relation = "couleur_episode"
    garde = frozenset({"couleur", "noir et blanc", "télévision couleur", "cinéma en noir et blanc"})
    q = (f'SELECT ?eLabel ?vLabel WHERE {{\n'
         f'  ?e wdt:P31/wdt:P279* wd:Q21191270 ; wdt:P462 ?o .\n'
         f'  ?o rdfs:label ?vLabel . FILTER(lang(?vLabel)="fr")\n'
         f'  ?e rdfs:label ?eLabel . FILTER(lang(?eLabel)="fr")\n}}')
    print(f"== {relation} (Wikidata/QLever P462, whitelist statuts) ==")
    rows = IQ._charge_ou_fetch(relation, q)
    paires = [(e, v) for e, v in IQ._paires(rows, "eLabel", "vLabel") if v in garde]
    print(f"  {len(rows)} lignes brutes -> {len(paires)} paires (statuts couleur ; bruit rejeté).")
    IQ.publie(relation, "physique",
              "Wikidata/QLever — statut couleur de l'épisode TV P462 (couleur vs N&B ; multi/bruit -> HORS)",
              paires)


@_t6("couleur_serie")
def ingere_couleur_serie():
    # série TV -> statut couleur (P462). Comme couleur_film mais classe Q5398426 (série, entités DISJOINTES des
    # films). Scout PROPRE ratio 0.005, fonctionnel 98%. FAUX=0 : (1) multi→HORS via publie ; (2) WHITELIST des
    # statuts couleur réels (écarte « peinture »/« vermillon » = bruit). Fait borné (une série EST en couleur/N&B).
    relation = "couleur_serie"
    garde = frozenset({"couleur", "noir et blanc", "télévision couleur", "cinéma en noir et blanc"})
    q = (f'SELECT ?eLabel ?vLabel WHERE {{\n'
         f'  ?e wdt:P31/wdt:P279* wd:Q5398426 ; wdt:P462 ?o .\n'
         f'  ?o rdfs:label ?vLabel . FILTER(lang(?vLabel)="fr")\n'
         f'  ?e rdfs:label ?eLabel . FILTER(lang(?eLabel)="fr")\n}}')
    print(f"== {relation} (Wikidata/QLever P462, whitelist statuts couleur) ==")
    rows = IQ._charge_ou_fetch(relation, q)
    paires = [(e, v) for e, v in IQ._paires(rows, "eLabel", "vLabel") if v in garde]
    print(f"  {len(rows)} lignes brutes -> {len(paires)} paires (statuts couleur ; bruit rejeté).")
    IQ.publie(relation, "physique",
              "Wikidata/QLever — statut couleur de la série TV P462 (couleur vs N&B ; multi/bruit -> HORS)",
              paires)


@_t6("format_image_serie")
def ingere_format_image_serie():
    # série TV -> format d'image (P2061). Comme format_image_film mais classe Q5398426 (entités disjointes).
    # Scout PROPRE ratio 0.01, fonctionnel 98%. FAUX=0 : (1) multi→HORS via publie ; (2) FILTRE LETTRE garde les
    # formats NOMMÉS (T6), laisse les ratios nus à T7. classe Q5398426 = série TV. _raw réutilisé offline.
    relation = "format_image_serie"
    q = (f'SELECT ?eLabel ?vLabel WHERE {{\n'
         f'  ?e wdt:P31/wdt:P279* wd:Q5398426 ; wdt:P2061 ?o .\n'
         f'  ?o rdfs:label ?vLabel . FILTER(lang(?vLabel)="fr")\n'
         f'  ?e rdfs:label ?eLabel . FILTER(lang(?eLabel)="fr")\n}}')
    print(f"== {relation} (Wikidata/QLever P2061, formats nommés) ==")
    rows = IQ._charge_ou_fetch(relation, q)
    paires = [(e, v) for e, v in IQ._paires(rows, "eLabel", "vLabel") if _a_une_lettre(v)]
    print(f"  {len(rows)} lignes brutes -> {len(paires)} paires (formats nommés ; ratios nus -> T7).")
    IQ.publie(relation, "convention",
              "Wikidata/QLever — format d'image nommé de la série TV P2061 (mono ; multi/ratio-nu -> HORS)",
              paires)


@_t6("format_image_film")
def ingere_format_image_film():
    # film -> format d'image / rapport de cadre (P2061). Scout PROPRE : ratio 0.003, fonctionnel 99%, ~9 valeurs
    # (format 16/9, format 4/3, format académique, VistaVision…). FAUX=0 : (1) multi→HORS via publie ;
    # (2) FILTRE LETTRE : on ne garde QUE les formats NOMMÉS (avec lettre) = territoire T6 ; les ratios nus
    # (« 2.55:1 ») = numérique pur -> laissés à T7 (frontière). classe Q11424 = film. _raw réutilisé offline.
    relation = "format_image_film"
    q = (f'SELECT ?eLabel ?vLabel WHERE {{\n'
         f'  ?e wdt:P31/wdt:P279* wd:Q11424 ; wdt:P2061 ?o .\n'
         f'  ?o rdfs:label ?vLabel . FILTER(lang(?vLabel)="fr")\n'
         f'  ?e rdfs:label ?eLabel . FILTER(lang(?eLabel)="fr")\n}}')
    print(f"== {relation} (Wikidata/QLever P2061, formats nommés) ==")
    rows = IQ._charge_ou_fetch(relation, q)
    paires = [(e, v) for e, v in IQ._paires(rows, "eLabel", "vLabel") if _a_une_lettre(v)]
    print(f"  {len(rows)} lignes brutes -> {len(paires)} paires (formats nommés ; ratios nus -> T7).")
    IQ.publie(relation, "convention",
              "Wikidata/QLever — format d'image nommé du film P2061 (mono ; multi/ratio-nu -> HORS)",
              paires)


# REJET materiau_artefact_archeo (P186/Q220659) : overlap 44% avec materiau_objet_art (classe très hétérogène,
# beaucoup d'artefacts = objets d'art). Substantiel + redondant -> non ingéré.


# REJET materiau_verriere (P186/Q21061279) : effectivement MONO-valué (~tout = « verre ») -> trivial, pas un
# ensemble catégoriel à variété. QUALITÉ : un attribut doit avoir une vraie variété, pas être une constante.


# REJET materiau_dalle_funeraire (P186/Q11832720) : overlap 99,9% avec materiau_objet_art (dalles = sculptures).
# PATTERN : les classes « sculpture/objet d'art » (statue/dalle/figurine…) overlappent objet_art ; cloche/
# manuscrit/calice/chaire (PAS des sculptures) = 0%. Toujours mesurer l'overlap objet_art AVANT.


# REJET materiau_plaque_commemorative (P186/Q721747) : overlap 100% materiau_objet_art (plaques = objets d'art).


# REJET materiau_figurine (P186/Q1066288) : overlap 93% materiau_objet_art (figurines = sculptures).
# ── PIPELINE MATÉRIAU P186 CONCLU : classes sculpture-type (statue/dalle/plaque/figurine) overlappent objet_art
#    (T5) ; classes non-sculpture FRAÎCHES toutes prises (cloche/manuscrit/calice/chaire + construction/monnaie/
#    meuble/vase/pont). Seul reste materiau_peinture (Q3305213, 676k) = EN ATTENTE réponse T5 (son turf).


@_t6("materiau_chaire")
def ingere_materiau_chaire():
    # chaire à prêcher -> matériau (P186). QID Q211775 (découverte top-P186, 2875 ent). Bois/pierre/marbre =
    # variété attendue. ⚠️ overlap à mesurer vs materiau_construction (chaires d'église) AVANT certif. FAUX=0 :
    # multi→HORS via publie. classe Q211775. Catégorie physique.
    IQ._ingere_x_vers_entite(
        "materiau_chaire", "P186", "physique",
        "Wikidata/QLever — matériau de la chaire à prêcher P186 (mono-matériau ; multi -> HORS)",
        classe_qid="Q211775")


@_t6("materiau_calice")
def ingere_materiau_calice():
    # calice (objet liturgique) -> matériau (P186). QID Q210723 (découverte top-P186, 2466 ent). Argent/or/bronze
    # dominants. ⚠️ overlap à mesurer vs materiau_objet_art AVANT certif. FAUX=0 : multi→HORS via publie. classe
    # Q210723. Catégorie physique.
    IQ._ingere_x_vers_entite(
        "materiau_calice", "P186", "physique",
        "Wikidata/QLever — matériau du calice P186 (mono-matériau ; multi -> HORS)",
        classe_qid="Q210723")


@_t6("materiau_manuscrit")
def ingere_materiau_manuscrit():
    # manuscrit -> matériau (P186). QID Q87167 (vérifié, dense ~26k via découverte top-P186). Supports (papier/
    # parchemin/vélin/papyrus/soie) + médias d'enluminure (encre/or/argent/pigment/tempera) = matériaux réels.
    # FAUX=0 : multi→HORS via publie. Valeurs vérifiées atome par atome + overlap mesuré vs materiau_objet_art.
    # classe Q87167 = manuscrit. Catégorie physique.
    relation = "materiau_manuscrit"
    bloque = frozenset({"manuscrit"})  # valeur circulaire (1-2 faits) débusquée atome par atome
    q = (f'SELECT ?eLabel ?vLabel WHERE {{\n'
         f'  ?e wdt:P31/wdt:P279* wd:Q87167 ; wdt:P186 ?o .\n'
         f'  ?o rdfs:label ?vLabel . FILTER(lang(?vLabel)="fr")\n'
         f'  ?e rdfs:label ?eLabel . FILTER(lang(?eLabel)="fr")\n}}')
    print(f"== {relation} (Wikidata/QLever P186 Q87167, blocklist circulaire) ==")
    rows = IQ._charge_ou_fetch(relation, q)
    paires = [(e, v) for e, v in IQ._paires(rows, "eLabel", "vLabel") if v not in bloque]
    print(f"  {len(rows)} lignes brutes -> {len(paires)} paires (matériaux ; circulaire rejeté).")
    IQ.publie(relation, "physique",
              "Wikidata/QLever — matériau du manuscrit P186 (mono-matériau ; multi/circulaire -> HORS)",
              paires)


@_t6("materiau_cloche")
def ingere_materiau_cloche():
    # cloche -> matériau (P186). QID VÉRIFIÉ Q101401 (le faux Q101017 donnait 0 ; leçon T1 = vérifier le QID par
    # label). Veine DENSE (~6000 faits) : bronze dominant (cloches d'église), + fer/bois/fonte/cuivre/argent/acier.
    # FAUX=0 : multi→HORS via publie. Valeurs vérifiées atome par atome + overlap mesuré vs materiau_objet_art/
    # construction (cloche ⊄ bâtiment/sculpture attendu). classe Q101401 = cloche. Catégorie physique.
    relation = "materiau_cloche"
    bloque = frozenset({"matériel végétal"})  # vague non-matériau (1 fait) débusqué atome par atome
    q = (f'SELECT ?eLabel ?vLabel WHERE {{\n'
         f'  ?e wdt:P31/wdt:P279* wd:Q101401 ; wdt:P186 ?o .\n'
         f'  ?o rdfs:label ?vLabel . FILTER(lang(?vLabel)="fr")\n'
         f'  ?e rdfs:label ?eLabel . FILTER(lang(?eLabel)="fr")\n}}')
    print(f"== {relation} (Wikidata/QLever P186 Q101401, blocklist vague) ==")
    rows = IQ._charge_ou_fetch(relation, q)
    paires = [(e, v) for e, v in IQ._paires(rows, "eLabel", "vLabel") if v not in bloque]
    print(f"  {len(rows)} lignes brutes -> {len(paires)} paires (matériaux ; vague rejeté).")
    IQ.publie(relation, "physique",
              "Wikidata/QLever — matériau de la cloche P186 (mono-matériau ; multi/vague -> HORS)",
              paires)


@_t6("materiau_pont")
def ingere_materiau_pont():
    # pont -> matériau (P186). DISTINCT des mesures numériques T7 (largeur/longueur). Offert à T11 sans objection.
    # ratio 0.032, fonctionnel 90%, ~47 matériaux (acier/pierre/béton armé/bois/fonte/bambou/glace…). FAUX=0 :
    # (1) multi-matériau→HORS via publie ; (2) BLOCKLIST 4 intrus vérifiés atome par atome (taxon d'arbre brut,
    # une REVUE académique, 2 types-de-pont non-matériaux). classe Q12280 = pont (P31/P279*). _raw offline.
    relation = "materiau_pont"
    bloque = frozenset({"Sequoioideae", "Steel & Composite Structures", "pont en béton armé", "pont en maçonnerie"})
    q = (f'SELECT ?eLabel ?vLabel WHERE {{\n'
         f'  ?e wdt:P31/wdt:P279* wd:Q12280 ; wdt:P186 ?o .\n'
         f'  ?o rdfs:label ?vLabel . FILTER(lang(?vLabel)="fr")\n'
         f'  ?e rdfs:label ?eLabel . FILTER(lang(?eLabel)="fr")\n}}')
    print(f"== {relation} (Wikidata/QLever P186, blocklist non-matériaux) ==")
    rows = IQ._charge_ou_fetch(relation, q)
    paires = [(e, v) for e, v in IQ._paires(rows, "eLabel", "vLabel") if v not in bloque]
    print(f"  {len(rows)} lignes brutes -> {len(paires)} paires (matériaux ; intrus rejetés).")
    IQ.publie(relation, "physique",
              "Wikidata/QLever — matériau du pont P186 (mono-matériau ; multi/non-matériau -> HORS)",
              paires)


@_t6("materiau_monnaie")
def ingere_materiau_monnaie():
    # monnaie/pièce -> métal de frappe (P186). Domaine NUMISMATIQUE (sans lane). Scout PROPRE : ratio 0.003,
    # fonctionnel 99%, ~8 valeurs (argent/bronze/électrum/métal argenté/placage à l'or…) = ensemble FERMÉ de
    # métaux monétaires. Fait physique figé (une pièce EST frappée dans un métal). FAUX=0 : multi-métal→HORS via
    # publie. Valeurs vérifiées atome par atome sur le jsonl produit (offline) ; blocklist si bruit. classe
    # Q41207 = pièce de monnaie (P31/P279*). Catégorie physique.
    IQ._ingere_x_vers_entite(
        "materiau_monnaie", "P186", "physique",
        "Wikidata/QLever — métal de frappe de la pièce de monnaie P186 (ensemble fermé ; multi -> HORS)",
        classe_qid="Q41207")


@_t6("materiau_construction")
def ingere_materiau_construction():
    # bâtiment -> matériau de construction (P186). Vocab SEMI-OUVERT de matériaux (béton/acier/grès/bois/ardoise/
    # pierre de taille/verre/brique…). Fait physique du bâti. FAUX=0 en DEUX gardes : (1) `_paires`/`publie`
    # mettent en HORS tout bâtiment multi-matériau (conflit) ; (2) BLOCKLIST `_NON_MATERIAUX_BATI` retire le
    # bruit non-matériau vérifié sur le _raw. classe Q41176 = bâtiment (P31/P279*). _raw réutilisé offline.
    relation = "materiau_construction"
    q = (f'SELECT ?eLabel ?vLabel WHERE {{\n'
         f'  ?e wdt:P31/wdt:P279* wd:Q41176 ; wdt:P186 ?o .\n'
         f'  ?o rdfs:label ?vLabel . FILTER(lang(?vLabel)="fr")\n'
         f'  ?e rdfs:label ?eLabel . FILTER(lang(?eLabel)="fr")\n}}')
    print(f"== {relation} (Wikidata/QLever P186, blocklist non-matériaux) ==")
    rows = IQ._charge_ou_fetch(relation, q)
    paires = [(e, v) for e, v in IQ._paires(rows, "eLabel", "vLabel") if v not in _NON_MATERIAUX_BATI]
    print(f"  {len(rows)} lignes brutes -> {len(paires)} paires (matériaux ; non-matériaux rejetés).")
    IQ.publie(relation, "physique",
              "Wikidata/QLever — matériau de construction du bâtiment P186 (mono-matériau ; multi/non-matériau -> HORS)",
              paires)


# Ensemble FERMÉ des modes de jeu LÉGITIMES (whitelist FAUX=0, vérifiés atome par atome sur le _raw P404/Q7889).
# La queue de P404 contient du bruit non-mode (genres « jeu de rôle »/« jeu vidéo d'arcade », service « Xbox
# Network », « combat », « tournoi », libellé vide) -> EXCLU. On ne laisse passer QUE des modes confirmés.
_MODES_JEU_VALIDES = frozenset({
    "solo", "multijoueur", "mode coopératif", "en ligne et hors-ligne", "jeu en ligne",
    "joueur contre joueur", "jeu en ligne multijoueur", "jeu pour 2 joueurs", "jeu à zéro joueur",
    "multijoueur en écran divisé / partagé", "Match à mort",
})


@_t6("periode_personne")
def ingere_periode_personne():
    # personne -> période historique (P2348). DISTINCT de periode_oeuvre (rejeté par T1 = muddy ères+saisons-
    # théâtre) : le filtre Q5 (humains) ne garde que des ères historiques propres (Empire romain, époque
    # hellénistique, Égypte antique, siècles…). Attribut biographique (comme religion/occupation). Scout : ratio
    # ~0.026, 342 ères, 13 280 faits post-FR. FAUX=0 : multi (ères imbriquées)→HORS via publie. Valeurs vérifiées
    # atome par atome (offline) ; blocklist si bruit. classe Q5. Convention (classification en ères nommées).
    # BLOCKLIST des valeurs P2348 qui ne sont PAS des périodes (débusquées atome par atome) : années nues +
    # événements (guerres/révolutions/conquête) + groupe de martyrs. GARDÉS : siècles av. J.-C. + après-guerre/
    # entre-deux-guerres (vraies périodes).
    bloque = frozenset({
        "1998", "2020", "32", "340 av. J.-C.", "450", "48", "Martyrs espagnols du XXe siècle",
        "Révolution française", "Seconde Guerre mondiale", "conquête de l'empire inca",
        "guerre civile du Salvador", "guerre d'Espagne", "guerre d'indépendance du Pérou",
        "guerre de Trịnh–Nguyễn", "guerre du Biafra", "guerres révolutionnaires yorubas",
        "occupation de la France par l'Allemagne pendant la Seconde Guerre mondiale",
        "révolution américaine", "révolution libératrice",
    })
    q = ('SELECT ?eLabel ?vLabel WHERE {\n'
         '  ?e wdt:P31 wd:Q5 ; wdt:P2348 ?o .\n'
         '  ?o rdfs:label ?vLabel . FILTER(lang(?vLabel)="fr")\n'
         '  ?e rdfs:label ?eLabel . FILTER(lang(?eLabel)="fr")\n}')
    print("== periode_personne (Wikidata/QLever P2348 Q5, blocklist non-périodes) ==")
    rows = IQ._charge_ou_fetch("periode_personne", q)
    paires = [(e, v) for e, v in IQ._paires(rows, "eLabel", "vLabel") if v not in bloque]
    print(f"  {len(rows)} lignes brutes -> {len(paires)} paires (ères ; années/événements rejetés).")
    IQ.publie("periode_personne", "convention",
              "Wikidata/QLever — période historique de la personne P2348 (ères nommées ; multi/événement/année -> HORS)",
              paires)


@_t6("mode_jeu_video")
def ingere_mode_jeu_video():
    # jeu vidéo -> mode de jeu (P404). Scout PROPRE : ratio=0.006, fonctionnel ~94%. ATTRIBUT « mode » de design,
    # DISTINCT de genre_jeu_video (P136, T5 ; coordination postée sur le canal). FAUX=0 en DEUX gardes :
    #   (1) `_paires`/`publie` refusent tout jeu multi-mode (conflit) -> HORS ; ne restent que les mono-mode.
    #   (2) WHITELIST `_MODES_JEU_VALIDES` : la queue P404 mélange des genres/services/vide non-modes -> on ne
    #       publie QUE les valeurs confirmées comme de vrais modes (vérifiées atome par atome sur le _raw).
    # Attribut de design nommé -> catégorie convention. classe Q7889 = jeu vidéo (P31/P279*). _raw réutilisé offline.
    relation = "mode_jeu_video"
    q = (f'SELECT ?eLabel ?vLabel WHERE {{\n'
         f'  ?e wdt:P31/wdt:P279* wd:Q7889 ; wdt:P404 ?o .\n'
         f'  ?o rdfs:label ?vLabel . FILTER(lang(?vLabel)="fr")\n'
         f'  ?e rdfs:label ?eLabel . FILTER(lang(?eLabel)="fr")\n}}')
    print(f"== {relation} (Wikidata/QLever P404, whitelist modes) ==")
    rows = IQ._charge_ou_fetch(relation, q)
    paires = [(e, v) for e, v in IQ._paires(rows, "eLabel", "vLabel") if v in _MODES_JEU_VALIDES]
    print(f"  {len(rows)} lignes brutes -> {len(paires)} paires (modes whitelistés ; non-modes rejetés).")
    IQ.publie(relation, "convention",
              "Wikidata/QLever — mode de jeu du jeu vidéo P404 (ensemble fermé ; multi-mode + non-modes -> HORS)",
              paires)


# Statuts couleur CANONIQUES d'un film (whitelist FAUX=0). P462/Q11424 est très contaminé (noms d'acteurs
# mal liés, formats CinemaScope/4K/Betacam, procédés-marques DeLuxe/Gevacolor, teintes bleu/rouge/sépia,
# techniques encre de Chine/peinture) -> on ne garde QUE le statut binaire réel couleur vs noir et blanc.
_STATUTS_COULEUR_FILM = frozenset({"couleur", "cinéma en noir et blanc", "noir et blanc"})


@_t6("couleur_film")
def ingere_couleur_film():
    # film -> statut couleur (P462). Fait BORNÉ : un film EST en couleur ou en noir et blanc (figé à la
    # production). FAUX=0 en DEUX gardes : (1) `_paires`/`publie` -> film multi-valeur (N&B + couleur) en HORS ;
    # (2) WHITELIST `_STATUTS_COULEUR_FILM` : P462 mélange formats/procédés/teintes/noms de personnes -> on ne
    # publie QUE les 2 statuts canoniques (vérifiés sur le _raw). Propriété physique observable -> physique.
    # classe Q11424 = film (P31/P279*). _raw réutilisé offline.
    relation = "couleur_film"
    q = (f'SELECT ?eLabel ?vLabel WHERE {{\n'
         f'  ?e wdt:P31/wdt:P279* wd:Q11424 ; wdt:P462 ?o .\n'
         f'  ?o rdfs:label ?vLabel . FILTER(lang(?vLabel)="fr")\n'
         f'  ?e rdfs:label ?eLabel . FILTER(lang(?eLabel)="fr")\n}}')
    print(f"== {relation} (Wikidata/QLever P462, whitelist statuts couleur) ==")
    rows = IQ._charge_ou_fetch(relation, q)
    paires = [(e, v) for e, v in IQ._paires(rows, "eLabel", "vLabel") if v in _STATUTS_COULEUR_FILM]
    print(f"  {len(rows)} lignes brutes -> {len(paires)} paires (statuts couleur ; bruit rejeté).")
    IQ.publie(relation, "physique",
              "Wikidata/QLever — statut couleur du film P462 (couleur vs noir et blanc ; formats/procédés/noms -> HORS)",
              paires)


def main(argv):
    cibles = argv[1:] if len(argv) > 1 else list(_T6)
    inconnues = [c for c in cibles if c not in _T6]
    if inconnues:
        print(f"Relations inconnues : {inconnues}\nDisponibles : {list(_T6)}")
        return 1
    for nom in cibles:
        print(f"\n########## {nom} ##########")
        _T6[nom]()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
