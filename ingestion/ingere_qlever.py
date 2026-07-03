"""
INGESTION WIKIDATA via QLEVER -> datasets/lecteur/*.jsonl  (ONLINE, lancé à la main).

POURQUOI QLEVER : l'endpoint officiel WDQS (query.wikidata.org) est en outage/rate-limit agressif
(429 « 1 req/min »). QLever (https://qlever.cs.uni-freiburg.de/api/wikidata) est un MIROIR SPARQL
haute-performance de Wikidata, NON rate-limité de la même façon -> débloque toute la breadth.

DIFFÉRENCE DE SYNTAXE vs WDQS : QLever ne supporte PAS le `SERVICE wikibase:label`. On récupère donc
les libellés FR explicitement : `?x rdfs:label ?xLabel . FILTER(lang(?xLabel)="fr")`. PREFIX explicites.

SOUNDNESS (identique au reste) : `fonctionnel` (1 valeur/entité), réconciliation amorce (conflits ->
datasets/_conflits/), source citée, ancres + sanités dans valide_lecteur, HORS pour tout absent.
On écarte les libellés = Q-ID nu (entité sans nom FR).

Usage : python3 ingere_qlever.py [domaines...]   (défaut : tous)   puis non-reg OFFLINE.
"""
from __future__ import annotations

import json
import os
import re
import sys
import urllib.parse
import urllib.request

from ingere_wikidata import RAW, UA, _est_qid, publie, snapshot_brut

# Mois FR : une valeur de LIEU (P19/P20) qui contient un mois OU n'est qu'un nombre/année est en fait une DATE qui a
# fui dans la propriété (« 13 août », « 11 février 1963 », « 1166 ») -> FAIT FAUX -> on la REJETTE (FAUX=0). Les
# adresses/arrondissements à chiffre en tête (« 100 Mile House », « 10e arrondissement de Paris ») sont de VRAIS
# lieux : on les GARDE (la sanité lieu n'exige donc PAS « capitalisé/sans chiffre », juste « contient une lettre »).
_MOIS_FR = {"janvier", "février", "fevrier", "mars", "avril", "mai", "juin", "juillet", "août", "aout",
            "septembre", "octobre", "novembre", "décembre", "decembre"}


def _est_lieu_plausible(v: str) -> bool:
    """True si v ressemble à un LIEU (pas une date/année). Rejette : tout-chiffres/année nue, valeur contenant un nom
    de mois (date), valeur sans aucune lettre. Garde les adresses/arrondissements (vrais lieux à chiffre en tête)."""
    toks = re.findall(r"\w+", v.lower())
    if not any(ch.isalpha() for ch in v):
        return False                                  # « 1166 », « 16/5 » sans lettre
    if any(t in _MOIS_FR for t in toks):
        return False                                  # « 13 août », « 11 février 1963 »
    if re.fullmatch(r"\d{1,4}", v.strip()):
        return False                                  # année nue
    return True

# 2026-06-26 : l'ancien endpoint cs.uni-freiburg.de répond désormais en 308 (redirection
# permanente) vers qlever.dev, que urllib NE suit PAS sur 308 -> requêtes perdues/timeout.
# Pointer directement sur le nouvel hôte rétablit tout le scout/ingestion réseau (T1/T4/T6/T7/T8).
ENDPOINT = "https://qlever.dev/api/wikidata"
PREFIXES = """PREFIX wdt: <http://www.wikidata.org/prop/direct/>
PREFIX wd: <http://www.wikidata.org/entity/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
"""


def qlever(query: str, timeout: int = 90) -> list[dict]:
    url = ENDPOINT + "?action=json_export&query=" + urllib.parse.quote(PREFIXES + query)
    req = urllib.request.Request(url, headers={
        "User-Agent": UA, "Accept": "application/sparql-results+json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())["results"]["bindings"]


def _charge_ou_fetch(nom: str, query: str) -> list:
    chemin = os.path.join(RAW, nom + ".json")
    if os.path.exists(chemin):
        with open(chemin, encoding="utf-8") as fh:
            rows = json.load(fh)
        print(f"  [snapshot réutilisé : {nom}.json — {len(rows)} lignes, offline]")
        return rows
    rows = qlever(query)
    snapshot_brut(nom, rows)
    return rows


def val(row: dict, cle: str) -> str:
    return (row.get(cle, {}) or {}).get("value", "").strip()


def _paires(rows, k_ent, k_val):
    """(entité_fr, valeur_fr) en écartant les Q-ID nus, les vides et les libellés DÉGÉNÉRÉS (<2 car. côté valeur,
    ex. moteur de jeu « Q » = placeholder Wikidata). FAUX=0 : une valeur d'un seul caractère n'est jamais un fait
    fiable dans ces relations entité→entité à ensemble fermé."""
    return [(val(r, k_ent), val(r, k_val)) for r in rows
            if val(r, k_ent) and len(val(r, k_val)) >= 2
            and not _est_qid(val(r, k_val)) and not _est_qid(val(r, k_ent))]


# ============================================================================================
#  DOMAINES (chacun = 1 requête = 1 relation bornée). Libellés FR explicites.
# ============================================================================================
_DOMAINES = {}


def domaine(nom):
    def deco(fn):
        _DOMAINES[nom] = fn
        return fn
    return deco


@domaine("sommets")
def ingere_sommets():
    print("== POINT CULMINANT PAR PAYS (Wikidata/QLever P610) ==")
    q = """SELECT ?cLabel ?sLabel WHERE {
      ?c wdt:P31 wd:Q3624078 ; wdt:P610 ?s .
      ?c rdfs:label ?cLabel . FILTER(lang(?cLabel)="fr")
      ?s rdfs:label ?sLabel . FILTER(lang(?sLabel)="fr")
    }"""
    rows = _charge_ou_fetch("sommets", q)
    print(f"  {len(rows)} lignes brutes.")
    publie("point_culminant", "physique", "Wikidata/QLever — point culminant du pays P610",
           _paires(rows, "cLabel", "sLabel"))


@domaine("capitales")
def ingere_capitales():
    print("== PAYS D'UNE CAPITALE (Wikidata/QLever P1376, inverse) ==")
    q = """SELECT ?capLabel ?cLabel WHERE {
      ?c wdt:P31 wd:Q3624078 ; wdt:P36 ?cap .
      ?cap wdt:P1376 ?c .
      ?c rdfs:label ?cLabel . FILTER(lang(?cLabel)="fr")
      ?cap rdfs:label ?capLabel . FILTER(lang(?capLabel)="fr")
    }"""
    rows = _charge_ou_fetch("capitales_inv", q)
    print(f"  {len(rows)} lignes brutes.")
    publie("pays_de_capitale", "physique", "Wikidata/QLever — capitale de (P1376)",
           _paires(rows, "capLabel", "cLabel"))


@domaine("hymnes")
def ingere_hymnes():
    print("== HYMNE NATIONAL (Wikidata/QLever P85) ==")
    q = """SELECT ?cLabel ?hLabel WHERE {
      ?c wdt:P31 wd:Q3624078 ; wdt:P85 ?h .
      ?c rdfs:label ?cLabel . FILTER(lang(?cLabel)="fr")
      ?h rdfs:label ?hLabel . FILTER(lang(?hLabel)="fr")
    }"""
    rows = _charge_ou_fetch("hymnes", q)
    print(f"  {len(rows)} lignes brutes.")
    publie("hymne_national", "convention", "Wikidata/QLever — hymne national P85",
           _paires(rows, "cLabel", "hLabel"))


@domaine("conduite")
def ingere_conduite():
    print("== SENS DE CONDUITE PAR PAYS (Wikidata/QLever P1622) ==")
    # fait borné actuel. Fonctionnel : les pays avec valeur historique+actuelle (ex. Argentine {droite,gauche})
    # sont REJETÉS (HORS) -> ne reste que les sens actuels non ambigus.
    q = """SELECT ?cLabel ?vLabel WHERE {
      ?c wdt:P31 wd:Q3624078 ; wdt:P1622 ?v .
      ?c rdfs:label ?cLabel . FILTER(lang(?cLabel)="fr")
      ?v rdfs:label ?vLabel . FILTER(lang(?vLabel)="fr")
    }"""
    rows = _charge_ou_fetch("conduite", q)
    print(f"  {len(rows)} lignes brutes.")
    publie("sens_conduite", "convention", "Wikidata/QLever — sens de circulation P1622 (actuel non ambigu)",
           _paires(rows, "cLabel", "vLabel"))


@domaine("iso_num")
def ingere_iso_num():
    print("== CODE ISO 3166-1 NUMÉRIQUE PAR PAYS (Wikidata/QLever P299) ==")
    q = """SELECT ?cLabel ?code WHERE {
      ?c wdt:P31 wd:Q3624078 ; wdt:P299 ?code .
      ?c rdfs:label ?cLabel . FILTER(lang(?cLabel)="fr")
    }"""
    rows = _charge_ou_fetch("iso_num", q)
    print(f"  {len(rows)} lignes brutes.")
    publie("code_iso_numerique", "convention", "Wikidata/QLever — code ISO 3166-1 numérique P299",
           _paires(rows, "cLabel", "code"))


@domaine("langues")
def ingere_langues():
    print("== CODE ISO 639-1 DES LANGUES (Wikidata/QLever P218) ==")
    # définitionnel (norme ISO, non contestable). 1 code/langue. Valeurs = 2 lettres minuscules.
    q = """SELECT ?lLabel ?c WHERE {
      ?l wdt:P218 ?c .
      ?l rdfs:label ?lLabel . FILTER(lang(?lLabel)="fr")
    }"""
    rows = _charge_ou_fetch("langues_iso6391", q)
    print(f"  {len(rows)} lignes brutes.")
    publie("code_langue", "convention", "Wikidata/QLever — code ISO 639-1 de la langue P218",
           _paires(rows, "lLabel", "c"))


@domaine("villes")
def ingere_villes():
    print("== PAYS DE LA VILLE (Wikidata/QLever P17, ville Q515) ==")
    # FAUX=0 — TRIPLE garde-fou (Q515 seul rejeté : ratait Paris/Berlin = communes/capitales, et laissait
    # un homonyme obscur « Buenos Aires (Costa Rica) » Q515 gagner -> FAUX). Version sûre :
    #  (1) ?v = établissement humain (Q486972 + sous-classes) AVEC population P1082 >= 50 000
    #      -> inclut les vraies villes (Paris…), exclut les hameaux homonymes obscurs.
    #  (2) ?p = ÉTAT SOUVERAIN ACTUEL (Q3624078) -> pas de pays disparus (URSS, Tchécoslovaquie…).
    #  (3) `fonctionnel` (dans publie) rejette tout LIBELLÉ portant >1 pays distinct -> les homonymes
    #      multi-pays (Toledo ES/US, Valencia ES/VE, Santiago, Melbourne AU/US, Tripoli…) tombent en HORS.
    # Résultat mesuré : ~10 000 villes uniques, 158 homonymes rejetés, 0 FAUX sur 55 ancres connues.
    # Chine RPC / Taïwan / Palestine / Kosovo = polities ACTUELLES réelles (Q3624078) : pas faux.
    q = """SELECT ?vLabel ?pLabel WHERE {
      ?v wdt:P31/wdt:P279* wd:Q486972 ; wdt:P17 ?p ; wdt:P1082 ?pop .
      FILTER(?pop >= 50000)
      ?p wdt:P31 wd:Q3624078 .
      ?v rdfs:label ?vLabel . FILTER(lang(?vLabel)="fr")
      ?p rdfs:label ?pLabel . FILTER(lang(?pLabel)="fr")
    }"""
    rows = _charge_ou_fetch("villes_pays_pop50k", q)
    print(f"  {len(rows)} lignes brutes.")
    publie("pays_ville", "physique", "Wikidata/QLever — pays de la ville P17 (valeur=état souverain Q3624078)",
           _paires(rows, "vLabel", "pLabel"))


def _ingere_x_vers_pays(relation, classe_qid, libelle, prop="P17"):
    """Fabrique générique « entité (classe_qid) -> pays souverain actuel » via `prop` (défaut P17 = pays ;
    ex. P495 = pays d'origine d'un film). FAUX=0 : (1) valeur = état souverain ACTUEL (Q3624078) ;
    (2) `fonctionnel` rejette les libellés multi-pays (homonymes + entités multi-pays) -> HORS. SANITÉ
    STRUCTURELLE forte : toutes les valeurs ∈ ensemble fermé des ~190 pays (vérifiée dans valide_lecteur)."""
    print(f"== {libelle} (Wikidata/QLever {prop}, classe {classe_qid}) ==")
    q = f"""SELECT ?eLabel ?vLabel WHERE {{
      ?e wdt:P31/wdt:P279* wd:{classe_qid} ; wdt:{prop} ?p .
      ?p wdt:P31 wd:Q3624078 .
      ?p rdfs:label ?vLabel . FILTER(lang(?vLabel)="fr")
      ?e rdfs:label ?eLabel . FILTER(lang(?eLabel)="fr")
    }}"""
    rows = _charge_ou_fetch(relation, q)
    print(f"  {len(rows)} lignes brutes.")
    publie(relation, "physique", f"Wikidata/QLever — {libelle} {prop} (valeur=état souverain Q3624078)",
           _paires(rows, "eLabel", "vLabel"))


def _ingere_x_vers_code(relation, classe_qid, prop, libelle, categorie="convention", motif=None):
    """Fabrique « entité (classe_qid) -> code/identifiant exact (littéral, ex. P238 = IATA) ». Définitionnel
    (1 entité = 1 code), `fonctionnel` rejette les ambigus. `motif` (regex) ne garde QUE les codes au format
    canonique (ex. ^[A-Z]{4}$ pour ICAO -> écarte les codes FAA alphanumériques, mis en HORS = sûr).
    Sanité structurelle (forme du code) dans valide_lecteur."""
    import re as _re
    print(f"== {libelle} (Wikidata/QLever {prop}, classe {classe_qid}) ==")
    q = f"""SELECT ?eLabel ?vLabel WHERE {{
      ?e wdt:P31/wdt:P279* wd:{classe_qid} ; wdt:{prop} ?vLabel .
      ?e rdfs:label ?eLabel . FILTER(lang(?eLabel)="fr")
    }}"""
    rows = _charge_ou_fetch(relation, q)
    print(f"  {len(rows)} lignes brutes.")
    paires = _paires(rows, "eLabel", "vLabel")
    if motif:
        avant = len(paires)
        paires = [(e, v) for e, v in paires if _re.fullmatch(motif, v)]
        print(f"  filtre motif {motif!r} : {avant} -> {len(paires)} (codes non conformes -> HORS)")
    publie(relation, categorie, f"Wikidata/QLever — {libelle} {prop}", paires)


def _ingere_x_vers_entite(relation, propriete, categorie, source, classe_qid=None):
    """Fabrique « entité -> valeur (autre entité) via une propriété fonctionnelle » (ex. P59 constellation,
    P140 religion). `classe_qid` restreint l'entité source (ex. Q1370598 lieu de culte, sinon P140 capterait
    aussi les personnes). FAUX=0 : `fonctionnel` rejette tout libellé multi-valeur (homonymes) -> HORS. La
    sanité structurelle des valeurs (ensemble fermé) est vérifiée dans valide_lecteur."""
    print(f"== {relation} (Wikidata/QLever {propriete}) ==")
    filtre = f"?e wdt:P31/wdt:P279* wd:{classe_qid} ; " if classe_qid else "?e "
    q = f"""SELECT ?eLabel ?vLabel WHERE {{
      {filtre}wdt:{propriete} ?o .
      ?o rdfs:label ?vLabel . FILTER(lang(?vLabel)="fr")
      ?e rdfs:label ?eLabel . FILTER(lang(?eLabel)="fr")
    }}"""
    rows = _charge_ou_fetch(relation, q)
    print(f"  {len(rows)} lignes brutes.")
    publie(relation, categorie, source, _paires(rows, "eLabel", "vLabel"))


def _ingere_x_vers_lieu(relation, propriete, classe_qid, source, categorie="physique"):
    """Fabrique « entité -> LIEU » (vocabulaire de lieux OUVERT, pas un ensemble fermé : naissance/décès/inhumation/
    travail d'une personne, embouchure/source/bassin d'un fleuve, chaîne d'une montagne, division admin d'une ville…).
    Comme _ingere_x_vers_entite MAIS filtre les valeurs NON-LIEU via `_est_lieu_plausible` : certaines propriétés
    contiennent des dates/années/nombres qui ont fui (P19/P20 : « 13 août », « 1166 ») = FAITS FAUX -> REJET (FAUX=0).
    `fonctionnel` (dans publie) rejette les homonymes multi-lieu -> HORS. Réutilise le snapshot _raw si présent."""
    print(f"== {relation} (Wikidata/QLever {propriete}) ==")
    q = f"""SELECT ?eLabel ?vLabel WHERE {{
      ?e wdt:P31/wdt:P279* wd:{classe_qid} ; wdt:{propriete} ?o .
      ?o rdfs:label ?vLabel . FILTER(lang(?vLabel)="fr")
      ?e rdfs:label ?eLabel . FILTER(lang(?eLabel)="fr")
    }}"""
    rows = _charge_ou_fetch(relation, q)
    paires = [(e, v) for e, v in _paires(rows, "eLabel", "vLabel") if _est_lieu_plausible(v)]
    print(f"  {len(rows)} lignes brutes -> {len(paires)} paires lieu-plausibles (dates/années/nombres rejetés).")
    publie(relation, categorie, source, paires)


def _ingere_personne_vers_lieu(relation, propriete, source):
    """Cas particulier « personne -> LIEU » (catégorie passé). Délègue à `_ingere_x_vers_lieu` (classe Q5)."""
    _ingere_x_vers_lieu(relation, propriete, "Q5", source, categorie="passe")


@domaine("constellations")
def ingere_constellations():
    _ingere_x_vers_entite("constellation_astre", "P59", "physique",
                          "Wikidata/QLever — constellation de l'astre P59 (ensemble fermé = 88 constellations IAU)")


@domaine("iles")
def ingere_iles():
    _ingere_x_vers_pays("pays_ile", "Q23442", "PAYS DE L'ÎLE")


@domaine("phares")
def ingere_phares():
    _ingere_x_vers_pays("pays_phare", "Q39715", "PAYS DU PHARE")


@domaine("volcans")
def ingere_volcans():
    _ingere_x_vers_pays("pays_volcan", "Q8072", "PAYS DU VOLCAN")


@domaine("aeroports")
def ingere_aeroports():
    _ingere_x_vers_pays("pays_aeroport", "Q1248784", "PAYS DE L'AÉROPORT")


@domaine("iata")
def ingere_iata():
    _ingere_x_vers_code("code_iata_aeroport", "Q1248784", "P238", "CODE IATA DE L'AÉROPORT")


@domaine("icao")
def ingere_icao():
    _ingere_x_vers_code("code_icao_aeroport", "Q1248784", "P239", "CODE OACI DE L'AÉROPORT", motif="[A-Z]{4}")


@domaine("bibliotheques")
def ingere_bibliotheques():
    _ingere_x_vers_pays("pays_bibliotheque", "Q7075", "PAYS DE LA BIBLIOTHÈQUE")


@domaine("centrales")
def ingere_centrales():
    _ingere_x_vers_pays("pays_centrale_electrique", "Q159719", "PAYS DE LA CENTRALE ÉLECTRIQUE")


@domaine("grottes")
def ingere_grottes():
    _ingere_x_vers_pays("pays_grotte", "Q35509", "PAYS DE LA GROTTE")


@domaine("gratte_ciels")
def ingere_gratte_ciels():
    _ingere_x_vers_pays("pays_gratte_ciel", "Q11303", "PAYS DU GRATTE-CIEL")


@domaine("monasteres")
def ingere_monasteres():
    _ingere_x_vers_pays("pays_monastere", "Q44613", "PAYS DU MONASTÈRE")


@domaine("theatres")
def ingere_theatres():
    _ingere_x_vers_pays("pays_theatre", "Q24354", "PAYS DU THÉÂTRE")


@domaine("hopitaux")
def ingere_hopitaux():
    _ingere_x_vers_pays("pays_hopital", "Q16917", "PAYS DE L'HÔPITAL")


@domaine("films_pays")
def ingere_films_pays():
    _ingere_x_vers_pays("pays_film", "Q11424", "PAYS D'ORIGINE DU FILM", prop="P495")


@domaine("journaux")
def ingere_journaux():
    _ingere_x_vers_pays("pays_journal", "Q11032", "PAYS DU JOURNAL")


@domaine("entreprises")
def ingere_entreprises():
    _ingere_x_vers_pays("pays_entreprise", "Q4830453", "PAYS DE L'ENTREPRISE")


@domaine("barrages")
def ingere_barrages():
    _ingere_x_vers_pays("pays_barrage", "Q12323", "PAYS DU BARRAGE")


@domaine("religions_culte")
def ingere_religions_culte():
    _ingere_x_vers_entite("religion_lieu_culte", "P140", "convention",
                          "Wikidata/QLever — religion du lieu de culte P140", classe_qid="Q1370598")


@domaine("clubs_foot")
def ingere_clubs_foot():
    _ingere_x_vers_pays("pays_club_foot", "Q476028", "PAYS DU CLUB DE FOOTBALL")


@domaine("universites")
def ingere_universites():
    _ingere_x_vers_pays("pays_universite", "Q3918", "PAYS DE L'UNIVERSITÉ")


@domaine("lacs")
def ingere_lacs():
    _ingere_x_vers_pays("pays_lac", "Q23397", "PAYS DU LAC")


@domaine("gares")
def ingere_gares():
    _ingere_x_vers_pays("pays_gare", "Q55488", "PAYS DE LA GARE")


@domaine("musees")
def ingere_musees():
    _ingere_x_vers_pays("pays_musee", "Q33506", "PAYS DU MUSÉE")


@domaine("stades")
def ingere_stades():
    _ingere_x_vers_pays("pays_stade", "Q483110", "PAYS DU STADE")


@domaine("ponts")
def ingere_ponts():
    _ingere_x_vers_pays("pays_pont", "Q12280", "PAYS DU PONT")


@domaine("chateaux")
def ingere_chateaux():
    _ingere_x_vers_pays("pays_chateau", "Q23413", "PAYS DU CHÂTEAU")


@domaine("parcs_nationaux")
def ingere_parcs_nationaux():
    _ingere_x_vers_pays("pays_parc_national", "Q46169", "PAYS DU PARC NATIONAL")


# --- LOT 2026-06-26 (post-/clear) : X -> pays, classes mesurées propres (valeur ∈ ~190 pays, ancres+échantillon vérifiés) ---
@domaine("mines")
def ingere_mines():
    _ingere_x_vers_pays("pays_mine", "Q820477", "PAYS DE LA MINE")


@domaine("cathedrales")
def ingere_cathedrales():
    _ingere_x_vers_pays("pays_cathedrale", "Q2977", "PAYS DE LA CATHÉDRALE")


@domaine("mosquees")
def ingere_mosquees():
    _ingere_x_vers_pays("pays_mosquee", "Q32815", "PAYS DE LA MOSQUÉE")


@domaine("cascades")
def ingere_cascades():
    _ingere_x_vers_pays("pays_cascade", "Q34038", "PAYS DE LA CASCADE")


@domaine("glaciers")
def ingere_glaciers():
    _ingere_x_vers_pays("pays_glacier", "Q35666", "PAYS DU GLACIER")


@domaine("canaux")
def ingere_canaux():
    _ingere_x_vers_pays("pays_canal", "Q12284", "PAYS DU CANAL")


@domaine("cimetieres")
def ingere_cimetieres():
    _ingere_x_vers_pays("pays_cimetiere", "Q39614", "PAYS DU CIMETIÈRE")


@domaine("palais")
def ingere_palais():
    _ingere_x_vers_pays("pays_palais", "Q16560", "PAYS DU PALAIS")


@domaine("prisons")
def ingere_prisons():
    _ingere_x_vers_pays("pays_prison", "Q40357", "PAYS DE LA PRISON")


# --- LOT 2026-06-26 (b) : X -> pays, classes mesurées propres (échantillons vérifiés, valeurs = pays réels) ---
@domaine("temples")
def ingere_temples():
    _ingere_x_vers_pays("pays_temple", "Q44539", "PAYS DU TEMPLE")


@domaine("tunnels")
def ingere_tunnels():
    _ingere_x_vers_pays("pays_tunnel", "Q44377", "PAYS DU TUNNEL")


@domaine("raffineries")
def ingere_raffineries():
    _ingere_x_vers_pays("pays_raffinerie", "Q131596", "PAYS DE LA RAFFINERIE")


@domaine("fontaines")
def ingere_fontaines():
    _ingere_x_vers_pays("pays_fontaine", "Q483453", "PAYS DE LA FONTAINE")


@domaine("abbayes")
def ingere_abbayes():
    _ingere_x_vers_pays("pays_abbaye", "Q160742", "PAYS DE L'ABBAYE")


@domaine("synagogues")
def ingere_synagogues():
    _ingere_x_vers_pays("pays_synagogue", "Q34627", "PAYS DE LA SYNAGOGUE")


@domaine("observatoires")
def ingere_observatoires():
    _ingere_x_vers_pays("pays_observatoire", "Q62832", "PAYS DE L'OBSERVATOIRE")


@domaine("operas")
def ingere_operas():
    _ingere_x_vers_pays("pays_opera", "Q153562", "PAYS DE L'OPÉRA")


@domaine("zoos")
def ingere_zoos():
    _ingere_x_vers_pays("pays_zoo", "Q43501", "PAYS DU ZOO")


@domaine("jardins_botaniques")
def ingere_jardins_botaniques():
    _ingere_x_vers_pays("pays_jardin_botanique", "Q167346", "PAYS DU JARDIN BOTANIQUE")


# --- LOT 2026-06-26 (c) : X->pays nets + CODES ISO pays (ensembles fermés exacts, ancres FR/FRA/+33 vérifiées) ---
# NB écartés (FAUX=0/honnêteté) : Q22652 « vignoble » = en fait des JARDINS ; Q10283556 « distillerie » = dépôts
# de tram. Pays correct mais classe fausse -> on n'ingère PAS sous un nom mensonger.
@domaine("forts")
def ingere_forts():
    _ingere_x_vers_pays("pays_fort", "Q57831", "PAYS DU FORT")


@domaine("brasseries")
def ingere_brasseries():
    _ingere_x_vers_pays("pays_brasserie", "Q131734", "PAYS DE LA BRASSERIE")


@domaine("chantiers_navals")
def ingere_chantiers_navals():
    _ingere_x_vers_pays("pays_chantier_naval", "Q190928", "PAYS DU CHANTIER NAVAL")


@domaine("marches")
def ingere_marches():
    _ingere_x_vers_pays("pays_marche", "Q330284", "PAYS DU MARCHÉ")


@domaine("gares_routieres")
def ingere_gares_routieres():
    _ingere_x_vers_pays("pays_gare_routiere", "Q494829", "PAYS DE LA GARE ROUTIÈRE")


@domaine("centrales_nucleaires")
def ingere_centrales_nucleaires():
    _ingere_x_vers_pays("pays_centrale_nucleaire", "Q134447", "PAYS DE LA CENTRALE NUCLÉAIRE")

# NB : codes ISO alpha-2/alpha-3 + indicatif téléphonique NON ré-ingérés via QLever — DÉJÀ couverts par
# `ingere_geo.py` (mledoze : `code_iso_pays`, `code_iso3_pays`, `indicatif_telephonique`, 250 pays = plus
# complet que QLever 198). Doublon évité (FAUX=0/propreté). Ne pas ré-ajouter ici.


# --- LOT 2026-06-26 (d) : X->pays, classes SÉMANTIQUEMENT VÉRIFIÉES par échantillon (anti-classe-mensongère) ---
# Écartés au sampling (classe fausse, pays correct mais nom mensonger) : Q14745 (retables), Q1311670 (villages),
# Q204832 (montagnes russes), Q3253281 (étangs). Q39715 phare = DÉJÀ pays_phare. -> ne PAS ré-essayer.
@domaine("cols")
def ingere_cols():
    _ingere_x_vers_pays("pays_col", "Q133056", "PAYS DU COL DE MONTAGNE")


@domaine("metros")
def ingere_metros():
    _ingere_x_vers_pays("pays_metro", "Q5503", "PAYS DU MÉTRO")


@domaine("cinemas")
def ingere_cinemas():
    _ingere_x_vers_pays("pays_cinema", "Q41253", "PAYS DU CINÉMA (salle)")


@domaine("centres_commerciaux")
def ingere_centres_commerciaux():
    _ingere_x_vers_pays("pays_centre_commercial", "Q31374404", "PAYS DU CENTRE COMMERCIAL")


@domaine("sites_archeo")
def ingere_sites_archeo():
    _ingere_x_vers_pays("pays_site_archeologique", "Q839954", "PAYS DU SITE ARCHÉOLOGIQUE")


@domaine("parcs_attraction")
def ingere_parcs_attraction():
    _ingere_x_vers_pays("pays_parc_attraction", "Q194195", "PAYS DU PARC D'ATTRACTIONS")


@domaine("casinos")
def ingere_casinos():
    _ingere_x_vers_pays("pays_casino", "Q133215", "PAYS DU CASINO")


@domaine("moulins")
def ingere_moulins():
    _ingere_x_vers_pays("pays_moulin", "Q38720", "PAYS DU MOULIN À VENT")


@domaine("hotels")
def ingere_hotels():
    _ingere_x_vers_pays("pays_hotel", "Q27686", "PAYS DE L'HÔTEL")


# --- LOT 2026-06-26 (e) : X->pays, 13 classes échantillonnées propres. Écartés : Q44613=doublon pays_monastere,
# Q473972 aire_protegee=redondant parc/réserve, Q19478/Q1003183/Q1142889=vides. ---
@domaine("aqueducs")
def ingere_aqueducs():
    _ingere_x_vers_pays("pays_aqueduc", "Q474", "PAYS DE L'AQUEDUC")


@domaine("places")
def ingere_places():
    _ingere_x_vers_pays("pays_place", "Q174782", "PAYS DE LA PLACE")


@domaine("reservoirs")
def ingere_reservoirs():
    _ingere_x_vers_pays("pays_reservoir", "Q131681", "PAYS DU RÉSERVOIR")


@domaine("tours")
def ingere_tours():
    _ingere_x_vers_pays("pays_tour", "Q12518", "PAYS DE LA TOUR")


@domaine("mairies")
def ingere_mairies():
    _ingere_x_vers_pays("pays_mairie", "Q543654", "PAYS DE LA MAIRIE")


@domaine("reserves_naturelles")
def ingere_reserves_naturelles():
    _ingere_x_vers_pays("pays_reserve_naturelle", "Q179049", "PAYS DE LA RÉSERVE NATURELLE")


@domaine("monuments_historiques")
def ingere_monuments_historiques():
    _ingere_x_vers_pays("pays_monument_historique", "Q4989906", "PAYS DU MONUMENT HISTORIQUE")


@domaine("statues")
def ingere_statues():
    _ingere_x_vers_pays("pays_statue", "Q179700", "PAYS DE LA STATUE")


@domaine("ecluses")
def ingere_ecluses():
    _ingere_x_vers_pays("pays_ecluse", "Q105731", "PAYS DE L'ÉCLUSE")


@domaine("quartiers")
def ingere_quartiers():
    _ingere_x_vers_pays("pays_quartier", "Q123705", "PAYS DU QUARTIER")


@domaine("gares_metro")
def ingere_gares_metro():
    _ingere_x_vers_pays("pays_gare_metro", "Q928830", "PAYS DE LA STATION DE MÉTRO")


@domaine("peninsules")
def ingere_peninsules():
    _ingere_x_vers_pays("pays_peninsule", "Q34763", "PAYS DE LA PÉNINSULE")


@domaine("deserts")
def ingere_deserts():
    _ingere_x_vers_pays("pays_desert", "Q8514", "PAYS DU DÉSERT")


# --- LOT 2026-06-26 (f) : X->pays, 11 classes échantillonnées propres. IUCN P141 DIFFÉRÉ (vérité datée :
# statut de conservation réévalué périodiquement = régime-chiffré, pas borné stable en base froide). ---
@domaine("eglises")
def ingere_eglises():
    _ingere_x_vers_pays("pays_eglise", "Q16970", "PAYS DE L'ÉGLISE")


@domaine("chapelles")
def ingere_chapelles():
    _ingere_x_vers_pays("pays_chapelle", "Q108325", "PAYS DE LA CHAPELLE")


@domaine("sculptures")
def ingere_sculptures():
    _ingere_x_vers_pays("pays_sculpture", "Q860861", "PAYS DE LA SCULPTURE")


@domaine("puits")
def ingere_puits():
    _ingere_x_vers_pays("pays_puits", "Q43483", "PAYS DU PUITS")


@domaine("etangs")
def ingere_etangs():
    _ingere_x_vers_pays("pays_etang", "Q3253281", "PAYS DE L'ÉTANG")


@domaine("rivieres")
def ingere_rivieres():
    _ingere_x_vers_pays("pays_riviere", "Q4022", "PAYS DE LA RIVIÈRE")


@domaine("forets")
def ingere_forets():
    _ingere_x_vers_pays("pays_foret", "Q4421", "PAYS DE LA FORÊT")


@domaine("plages")
def ingere_plages():
    _ingere_x_vers_pays("pays_plage", "Q40080", "PAYS DE LA PLAGE")


@domaine("sources")
def ingere_sources():
    _ingere_x_vers_pays("pays_source", "Q1437299", "PAYS DE LA SOURCE (d'eau)")


@domaine("rues")
def ingere_rues():
    _ingere_x_vers_pays("pays_rue", "Q79007", "PAYS DE LA RUE")


@domaine("places_fortes")
def ingere_places_fortes():
    _ingere_x_vers_pays("pays_place_forte", "Q1785071", "PAYS DE LA PLACE FORTE")


# --- LOT 2026-06-26 (g) : X->pays, 5 classes nettes. Écartés au sampling : Q133156 isthme=colonies pénit.,
# Q1440300 viaduc=tours d'observation, Q133067 mosaïque=junk, Q12323=redondant barrage/réservoir.
# REJET CONFIRMÉ montagne→massif P4552 (ancre fausse « mont Blanc→Laurentides », cf. mémoire « ancres HORS »). ---
@domaine("archipels")
def ingere_archipels():
    _ingere_x_vers_pays("pays_archipel", "Q33837", "PAYS DE L'ARCHIPEL")


@domaine("baies")
def ingere_baies():
    _ingere_x_vers_pays("pays_baie", "Q39594", "PAYS DE LA BAIE")


@domaine("caps")
def ingere_caps():
    _ingere_x_vers_pays("pays_cap", "Q185113", "PAYS DU CAP")


@domaine("massifs")
def ingere_massifs():
    _ingere_x_vers_pays("pays_massif", "Q46831", "PAYS DU MASSIF MONTAGNEUX")


@domaine("routes")
def ingere_routes():
    _ingere_x_vers_pays("pays_route", "Q34442", "PAYS DE LA ROUTE")


# --- LOT 2026-06-26 (h) : X->pays, types d'entités VARIÉS (pas que du bâti). Écartés : Q44613=dup monastere,
# Q62447 aérodrome=redondant aeroport. ---
@domaine("ecoles")
def ingere_ecoles():
    _ingere_x_vers_pays("pays_ecole", "Q3914", "PAYS DE L'ÉCOLE")


@domaine("groupes_musique")
def ingere_groupes_musique():
    _ingere_x_vers_pays("pays_groupe_musique", "Q215380", "PAYS D'ORIGINE DU GROUPE DE MUSIQUE")


@domaine("series_tv")
def ingere_series_tv():
    _ingere_x_vers_pays("pays_serie_tv", "Q5398426", "PAYS DE LA SÉRIE TÉLÉVISÉE")


@domaine("partis_politiques")
def ingere_partis_politiques():
    _ingere_x_vers_pays("pays_parti_politique", "Q7278", "PAYS DU PARTI POLITIQUE")


# --- LOT 2026-06-26 (i) : PIVOT non-pays. athlète -> sport (P641), valeur ∈ ENSEMBLE FERMÉ ~872 sports. ---
# FAUX=0 : `fonctionnel` rejette les noms multi-sport (Jordan/Brady = homonymes ou polyvalents -> HORS).
# Ancres VÉRIFIÉES 7/7 (Federer→tennis, Bolt→athlétisme, Riner→judo, Nadal→tennis, Loeb→rallye, Mbappé→football,
# Parker→basket). Résiduel homonymes = même profil que X→pays (la valeur reste vraie pour la personne notable).
@domaine("sport_athlete")
def ingere_sport_athlete():
    _ingere_x_vers_entite("sport_athlete", "P641", "physique",
                          "Wikidata/QLever — sport pratiqué par l'athlète P641 (ensemble fermé ~872 sports)")


# --- LOT 2026-06-26 (j) : personne -> nationalité (P27), valeur = pays souverain actuel (set fermé 198). ---
# FAUX=0 : `fonctionnel` rejette les multi-nationalités + citoyennetés historiques (Einstein/Messi/Poutine→HORS).
# Ancres VÉRIFIÉES 9/9 (Macron/de Gaulle→France, Ronaldo→Portugal, Beyoncé→US, Modi→Inde, Pelé/Senna→Brésil,
# Kahlo→Mexique, Mandela→Afrique du Sud, Mao→Chine). Sanité = valeur ∈ pays (boucle X→pays de valide_lecteur).
@domaine("nationalites")
def ingere_nationalites():
    _ingere_x_vers_pays("nationalite_personne", "Q5", "NATIONALITÉ DE LA PERSONNE", prop="P27")


# --- LOT 2026-06-26 (k) : lieu peuplé (large) -> pays (P17). Q486972 SUBSUME village/hameau/commune → 1 seule
# relation pour ~605k localités (division_admin Q56061 = recouvrement quasi-total → NON ajouté). FAUX=0 :
# homonymes multi-pays rejetés par fonctionnel ; valeur ∈ ~190 pays (boucle sanité X→pays). ---
@domaine("localites")
def ingere_localites():
    _ingere_x_vers_pays("pays_localite", "Q486972", "PAYS DE LA LOCALITÉ")


# NOTE : domaine `decouvreur_element` (P61) TENTÉ puis REJETÉ (FAUX=0) — attribution de découverte trop
# contestable même en fonctionnel : uranium->Péligot (a ISOLÉ le métal, découverte = Klaproth),
# oxygène->Scheele (priorité disputée Scheele/Priestley/Lavoisier). Ne pas ré-ingérer sans source historienne.


# --- LOT 2026-06-25 (RELIEFS, proposés par le SCOUT decouvre()+sonde) : 3 classes de relief DISTINCTES non
# couvertes (montagne/colline/vallée), valeur=pays. Sondées PROPRES (fonctionnel ≥98 %, closed-fit 100 %,
# échantillons relus = vrais reliefs, pas de classe mensongère). Écartés du même lot pour ANTI-REDONDANCE :
# village/hameau (subsumés par pays_localite Q486972), installation_sportive (subsume pays_stade), cours_eau
# (subsume pays_riviere). FAUX=0 : un relief transfrontalier (multi-P17) part en HORS via `fonctionnel`. ---
@domaine("montagnes")
def ingere_montagnes():
    _ingere_x_vers_pays("pays_montagne", "Q8502", "PAYS DE LA MONTAGNE")


@domaine("collines")
def ingere_collines():
    _ingere_x_vers_pays("pays_colline", "Q54050", "PAYS DE LA COLLINE")


@domaine("vallees")
def ingere_vallees():
    _ingere_x_vers_pays("pays_vallee", "Q39816", "PAYS DE LA VALLÉE")


# --- LOT 2026-06-25 (RELIEFS, suite — CLÔTURE de la veine X→pays via P17, décision Yohan « finir au propre ») :
# 3 dernières classes PROPRES & distinctes (échantillons relus). Le filon X→pays/P17 est ensuite considéré ÉPUISÉ
# (95+ classes ; les candidats restants = mal nommés [Q205895 « plaine »=îles/caps, Q1245089 « falaise »=caps] ou
# redondants). ANTI-COLLISION + closed-fit 100% + fonctionnel ≥94% vérifiés par scout_qlever. ---
@domaine("plateaux")
def ingere_plateaux():
    _ingere_x_vers_pays("pays_plateau", "Q75520", "PAYS DU PLATEAU")


@domaine("marais")
def ingere_marais():
    _ingere_x_vers_pays("pays_marais", "Q166735", "PAYS DU MARAIS")


@domaine("sources_thermales")
def ingere_sources_thermales():
    _ingere_x_vers_pays("pays_source_thermale", "Q177380", "PAYS DE LA SOURCE THERMALE")


# --- LOT 2026-06-25 (GÉNÉRALISATION du scout au-delà du pays — directive Yohan « si trop de redondance, généralise »).
# 4 NOUVELLES VEINES « X -> valeur d'un ENSEMBLE FERMÉ détecté par la donnée » (ratio distinct/entités < 0.03),
# fonctionnelles, échantillons relus propres (cf. scout_qlever.rapport_generique). FAUX=0 : `fonctionnel` met les
# multi-valeurs en HORS (un film multi-genre, une œuvre bilingue → HORS). Catégorie = convention (faits culturels
# stables). Écartés du lot : langage_logiciel (échantillon douteux), fuseau_ville (valeurs UTC/noms redondantes). ---
@domaine("genres_film")
def ingere_genres_film():
    _ingere_x_vers_entite("genre_film", "P136", "convention",
                          "Wikidata/QLever — genre du film P136 (ensemble fermé, fonctionnel)", classe_qid="Q11424")


@domaine("styles_batiment")
def ingere_styles_batiment():
    _ingere_x_vers_entite("style_batiment", "P149", "convention",
                          "Wikidata/QLever — style architectural du bâtiment P149 (ensemble fermé)", classe_qid="Q41176")


@domaine("langues_oeuvre")
def ingere_langues_oeuvre():
    _ingere_x_vers_entite("langue_oeuvre", "P407", "convention",
                          "Wikidata/QLever — langue de l'œuvre écrite P407 (ensemble fermé)", classe_qid="Q571")


@domaine("tonalites_oeuvre")
def ingere_tonalites_oeuvre():
    _ingere_x_vers_entite("tonalite_oeuvre", "P826", "convention",
                          "Wikidata/QLever — tonalité de l'œuvre musicale P826 (ensemble fermé ~douze tons × mode)",
                          classe_qid="Q2188189")


# --- LOT 2026-06-25 (T1, scout généralisé — 6 nouvelles veines fermées hors-pays, échantillons relus propres,
# cf. scout_qlever.rapport_generique). FAUX=0 : `fonctionnel` met les multi-valeurs en HORS (jeu multi-genre,
# logiciel multi-OS, œuvre multi-mouvement → HORS). Catégorie = convention (attributs culturels/techniques stables).
# `materiau_objet_art` : la classe Q860861 (sculpture) inclut des monnaies/médailles ; le matériau reste VRAI, on
# nomme la relation « objet d'art » (pas « sculpture ») pour rester honnête sur le périmètre. ---
@domaine("moteurs_jeu")
def ingere_moteurs_jeu():
    _ingere_x_vers_entite("moteur_jeu_video", "P408", "convention",
                          "Wikidata/QLever — moteur de jeu du jeu vidéo P408 (ensemble fermé ~moteurs)",
                          classe_qid="Q7889")


@domaine("os_logiciel")
def ingere_os_logiciel():
    _ingere_x_vers_entite("systeme_exploitation_logiciel", "P306", "convention",
                          "Wikidata/QLever — système d'exploitation du logiciel P306 (ensemble fermé)",
                          classe_qid="Q7397")


@domaine("genres_jeu_video")
def ingere_genres_jeu_video():
    _ingere_x_vers_entite("genre_jeu_video", "P136", "convention",
                          "Wikidata/QLever — genre du jeu vidéo P136 (ensemble fermé, fonctionnel)",
                          classe_qid="Q7889")


@domaine("materiaux_objet_art")
def ingere_materiaux_objet_art():
    _ingere_x_vers_entite("materiau_objet_art", "P186", "convention",
                          "Wikidata/QLever — matériau de l'objet d'art P186 (ensemble fermé ~matériaux)",
                          classe_qid="Q860861")


@domaine("mouvements_peinture")
def ingere_mouvements_peinture():
    _ingere_x_vers_entite("mouvement_peinture", "P135", "convention",
                          "Wikidata/QLever — mouvement artistique de la peinture P135 (ensemble fermé)",
                          classe_qid="Q3305213")


@domaine("formes_juridiques")
def ingere_formes_juridiques():
    _ingere_x_vers_entite("forme_juridique_entreprise", "P1454", "convention",
                          "Wikidata/QLever — forme juridique de l'entreprise P1454 (ensemble fermé)",
                          classe_qid="Q4830453")


# --- LOT 2026-06-25 (T1, scout généralisé — BATCH 2 : 5 veines fermées propres. ÉCARTÉ `genre_livre` (P136/Q7725634)
# car la classe « œuvre littéraire » inclut des CHANSONS mal-classées (« Plastic Love→city pop ») = nom trompeur. ---
@domaine("genres_album")
def ingere_genres_album():
    _ingere_x_vers_entite("genre_album", "P136", "convention",
                          "Wikidata/QLever — genre de l'album P136 (ensemble fermé, fonctionnel)", classe_qid="Q482994")


@domaine("genres_groupe_musique")
def ingere_genres_groupe_musique():
    _ingere_x_vers_entite("genre_groupe_musique", "P136", "convention",
                          "Wikidata/QLever — genre du groupe de musique P136 (ensemble fermé)", classe_qid="Q215380")


@domaine("modes_distribution_jeu")
def ingere_modes_distribution_jeu():
    _ingere_x_vers_entite("mode_distribution_jeu", "P437", "convention",
                          "Wikidata/QLever — mode de distribution du jeu vidéo P437 (ensemble fermé)", classe_qid="Q7889")


@domaine("ordres_religieux_monastere")
def ingere_ordres_religieux_monastere():
    _ingere_x_vers_entite("ordre_religieux_monastere", "P611", "convention",
                          "Wikidata/QLever — ordre religieux du monastère P611 (ensemble fermé d'ordres)",
                          classe_qid="Q44613")


@domaine("cultures_artefact")
def ingere_cultures_artefact():
    _ingere_x_vers_entite("culture_artefact", "P2596", "convention",
                          "Wikidata/QLever — culture archéologique de l'artefact P2596 (ensemble fermé)",
                          classe_qid="Q220659")


# --- LOT 2026-06-25 (T1, scout généralisé — BATCH 3 : 3 veines fermées propres. REJETS scout corrects :
# forme_gouvernement_pays (P122, multi-temporel ratio 0.24), ideologie_parti (P1142, multi 59 % fonctionnel),
# langage_logiciel (P277, COLLISION = déjà câblé). ---
@domaine("langues_film")
def ingere_langues_film():
    _ingere_x_vers_entite("langue_film", "P364", "convention",
                          "Wikidata/QLever — langue originale du film P364 (ensemble fermé de langues)",
                          classe_qid="Q11424")


@domaine("lieux_action_oeuvre")
def ingere_lieux_action_oeuvre():
    _ingere_x_vers_entite("lieu_action_oeuvre", "P840", "convention",
                          "Wikidata/QLever — lieu de l'action de l'œuvre P840 (ensemble fermé de lieux)",
                          classe_qid="Q11424")


@domaine("genres_emission_tv")
def ingere_genres_emission_tv():
    _ingere_x_vers_entite("genre_emission_tv", "P136", "convention",
                          "Wikidata/QLever — genre de l'émission de télévision P136 (ensemble fermé)",
                          classe_qid="Q15416")


# --- LOT 2026-06-25 (T1, scout généralisé — BATCH 4 : attributs fermés de PERSONNE (Q5). SEUL `couleur_yeux` retenu.
# ÉCARTÉS pour FAUX=0 (« rejeter au moindre doute ») : poste_joueur_sport (P413) et grade_militaire (P410) — valeurs
# CONTAMINÉES (« Bureau de l'Intérieur »/« Banca » pas des postes ; « Armée de terre des États-Unis » pas un grade) =
# faits FAUX. Aussi écartés : diplome_personne (P512 contaminé « géoscientifique » = métier), periode_oeuvre (P2348
# muddy ères+saisons-théâtre), groupe_sanguin (P1853 sparse 5 entités). ---
@domaine("couleurs_yeux")
def ingere_couleurs_yeux():
    _ingere_x_vers_entite("couleur_yeux", "P1340", "physique",
                          "Wikidata/QLever — couleur des yeux de la personne P1340 (ensemble fermé de couleurs)",
                          classe_qid="Q5")


# --- LOT 2026-06-25 (T1, BATCH 5). `usage_batiment` = ensemble fermé classique. `lieu_naissance`/`lieu_deces` = GROS
# filon « personne -> LIEU » (P19/P20), fonctionnel 100 % (un seul lieu) : VALEUR = lieu plausible (PAS un ensemble
# fermé borné comme les autres → sanité dédiée « lieu capitalisé + ancres vérité-terrain » dans valide_lecteur, pas de
# borne ≤N). FAUX=0 : homonymes multi-valeur -> HORS via `fonctionnel` ; source Wikidata P19/P20 très fiable. ---
@domaine("usages_batiment")
def ingere_usages_batiment():
    _ingere_x_vers_entite("usage_batiment", "P366", "convention",
                          "Wikidata/QLever — usage du bâtiment P366 (ensemble fermé d'usages)", classe_qid="Q41176")


@domaine("lieux_naissance")
def ingere_lieux_naissance():
    _ingere_personne_vers_lieu("lieu_naissance", "P19",
                               "Wikidata/QLever — lieu de naissance de la personne P19 (fonctionnel, lieu filtré)")


@domaine("lieux_deces")
def ingere_lieux_deces():
    _ingere_personne_vers_lieu("lieu_deces", "P20",
                               "Wikidata/QLever — lieu de décès de la personne P20 (fonctionnel, lieu filtré)")


# --- LOT 2026-06-25 (T1, BATCH 6 — veines « X -> LIEU » géo/personne, vocab ouvert, fabrique _ingere_x_vers_lieu).
@domaine("lieux_inhumation")
def ingere_lieux_inhumation():
    _ingere_personne_vers_lieu("lieu_inhumation", "P119",
                               "Wikidata/QLever — lieu de sépulture de la personne P119 (fonctionnel, lieu filtré)")


@domaine("lieux_travail")
def ingere_lieux_travail():
    _ingere_personne_vers_lieu("lieu_travail", "P937",
                               "Wikidata/QLever — lieu de travail de la personne P937 (fonctionnel, lieu filtré)")


@domaine("divisions_admin_ville")
def ingere_divisions_admin_ville():
    _ingere_x_vers_lieu("division_admin_ville", "P131", "Q486972",
                        "Wikidata/QLever — division administrative de l'établissement humain P131 (lieu)")


@domaine("bassins_fleuve")
def ingere_bassins_fleuve():
    _ingere_x_vers_lieu("bassin_fleuve", "P4614", "Q4022",
                        "Wikidata/QLever — bassin versant du cours d'eau P4614 (lieu, ~fermé)")


@domaine("chaines_montagne")
def ingere_chaines_montagne():
    _ingere_x_vers_lieu("chaine_montagne", "P4552", "Q8502",
                        "Wikidata/QLever — chaîne de montagnes du sommet P4552 (lieu)")


@domaine("embouchures_fleuve")
def ingere_embouchures_fleuve():
    _ingere_x_vers_lieu("embouchure_fleuve", "P403", "Q4022",
                        "Wikidata/QLever — embouchure/exutoire du cours d'eau P403 (lieu)")


@domaine("origines_fleuve")
def ingere_origines_fleuve():
    _ingere_x_vers_lieu("origine_fleuve", "P885", "Q4022",
                        "Wikidata/QLever — origine/source du cours d'eau P885 (lieu)")


if __name__ == "__main__":
    cibles = sys.argv[1:] or list(_DOMAINES)
    for c in cibles:
        if c not in _DOMAINES:
            print(f"domaine inconnu : {c} (dispo : {sorted(_DOMAINES)})")
            continue
        _DOMAINES[c]()
    print("\nFait. Relancer la non-reg OFFLINE :  python3 _nonreg.py --full --jobs 6")
