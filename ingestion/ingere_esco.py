"""
INGESTION ESCO — les axes MÉTIER que Wikidata ne sait pas fermer (mandat « traiter tout le backlog », nuit
du 2026-07-10).

SOURCE : ESCO v1 (European Skills, Competences, Qualifications and Occupations), API publique de la
Commission européenne — https://ec.europa.eu/esco/api. Référentiel officiel, multilingue, versionné.

POURQUOI ESCO ET PAS WIKIDATA. Mesuré : Wikidata ne porte ni compétences, ni savoirs, ni référentiel de
formation par métier, et sa propriété « uses » (P2283) est sémantiquement trop lâche pour l'axe « outils »
(elle donne « soliste -> solo »). ESCO, lui, distingue formellement, pour chaque occupation :
  • une DESCRIPTION rédigée (axe « définition et périmètre ») ;
  • un code ISCO-08 (axe taxonomique) ;
  • des compétences essentielles typées `skill-type/skill`      -> axe « gestes et savoir-faire techniques » ;
  • des compétences essentielles typées `skill-type/knowledge`  -> les SAVOIRS mobilisés.

TROIS RELATIONS PUBLIÉES :
  • `definition_esco_metier` — la description ESCO du métier ;
  • `geste_metier`           — les gestes/compétences CODIFIÉS (liste triée) ;
  • `savoir_metier`          — les savoirs essentiels (liste triée) ;
  • `code_isco_metier`       — le code ISCO-08 de l'occupation ;
  • `reglementation_metier`  — les professions SECTORIELLES à reconnaissance automatique (directive
                               2005/36/CE). ATTENTION : le drapeau `unregulated` d'ESCO signifie « consultez
                               la base des professions réglementées », pas « non réglementée ». Une première
                               version publiait « avocat : non réglementée » — un FAUX. On ne publie que les
                               professions effectivement marquées `regulated` (15 sur 2 938).

DESCENTE COMPLÈTE DE L'ARBRE (bug corrigé le 2026-07-11) : une occupation ESCO peut avoir des occupations
FILLES (`narrowerOccupation` : « employé de bureau » -> « assistant d'ingénieur »). La première version
s'arrêtait à la première occupation rencontrée et n'a ramené que 1 699 des ~3 000 occupations — un tiers du
référentiel manquait, sans qu'aucun signal ne le dise. Rien n'était FAUX, mais la couverture était
silencieusement amputée : c'est le genre de manque qu'aucune gate ne voit.

HONNÊTETÉ SUR L'AXE « GESTES ». ESCO codifie la part TRANSMISSIBLE PAR TEXTE du savoir-faire. Le TOUR DE MAIN
tacite (le geste qu'on apprend par imitation et répétition) n'est PAS dans ESCO et ne peut pas l'être : la
carte des sujets le classe MIX pour cette raison. Fermer `geste_metier` ferme la part codifiée, PAS le métier
entier. `couverture_borne` doit le dire, et le sujet reste MIX. On ne prétend rien de plus.

FAUX=0 — les gardes de l'ALIGNEMENT (c'est là que les faux naissent : donner à un métier les gestes d'un
autre) :

  1. VARIANTES CONTRÔLÉES. Un métier du store s'écrit « boulanger ou boulangère » ; ESCO écrit
     « boulanger/boulangère » et liste « boulanger », « boulangère » en libellés alternatifs. On génère donc,
     pour chaque côté, l'ensemble des variantes en découpant sur « ou » et « / », en minuscules. Aucune
     normalisation d'accents (« côte » ≠ « cote »), aucun rapprochement flou : égalité EXACTE de chaîne.

  2. UNICITÉ CÔTÉ ESCO. Une variante portée par PLUSIEURS occupations ESCO distinctes est ÉCARTÉE du
     dictionnaire d'alignement. On ne devine jamais de quel métier on parle.

  3. UNICITÉ CÔTÉ MÉTIER. Un métier dont les variantes atteignent PLUSIEURS occupations ESCO distinctes est
     REJETÉ (ambigu). Un métier sans aucune correspondance reste NON TRAITÉ, et le dit.

  4. FONCTIONNALITÉ (héritée de `publie`) : une entité, une valeur ; les listes sont triées et jointes —
     représentation fidèle de l'ensemble, jamais un choix arbitraire.

Le moissonnage est CACHÉ sur disque (`datasets/_raw/esco_occupations.json`) : rejouer l'ingestion ne
re-télécharge pas. Le réseau ne vit que dans ce script.

Usage :
    python3 ingestion/ingere_esco.py moissonne     # ~3 000 appels, cache sur disque
    python3 ingestion/ingere_esco.py publie        # hors ligne, depuis le cache
"""
from __future__ import annotations

import collections
import http.client
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

from ingere_wikidata import publie as _publie

API = "https://ec.europa.eu/esco/api"
UA = "Provara/1.0 (https://github.com/Provara-IA/Provara) offline-knowledge-ingestion"
SCHEME = "http://data.europa.eu/esco/concept-scheme/occupations"
TYPE_GESTE = "http://data.europa.eu/esco/skill-type/skill"
TYPE_SAVOIR = "http://data.europa.eu/esco/skill-type/knowledge"

SRC_DEF = "ESCO v1 (Commission européenne) — description de l'occupation, alignement par libellé exact et unique"
SRC_GESTE = ("ESCO v1 (Commission européenne) — compétences essentielles de type `skill` : la part CODIFIÉE du "
             "savoir-faire. Le tour de main tacite n'y est pas et ne peut pas y être (le sujet reste MIX).")
SRC_SAVOIR = "ESCO v1 (Commission européenne) — savoirs essentiels de l'occupation (skill-type/knowledge)"
SRC_ISCO = "ESCO v1 (Commission européenne) — code ISCO-08 (OIT) de l'occupation"
SRC_REGL = ("ESCO v1 (Commission européenne) — professions SECTORIELLES à reconnaissance automatique au "
            "titre de la directive 2005/36/CE (médecin, infirmier, dentiste, sage-femme, pharmacien, "
            "vétérinaire, architecte et leurs spécialités). L'absence d'un métier de cette table ne signifie "
            "PAS qu'il n'est pas réglementé : ESCO ne le dit pas, et on ne l'invente pas. Ce statut ne ferme "
            "donc JAMAIS l'axe « normes, réglementation et certifications ».")


def _get(url: str, essais: int = 6, timeout: int = 30):
    """GET JSON avec retry. Le filet doit être LARGE.

    Vécu le 2026-07-11 : après ~30 minutes de moissonnage, une réponse tronquée a levé
    `http.client.IncompleteRead` — que ce retry ne connaissait pas (il n'attrapait que HTTPError, URLError
    et TimeoutError). Tout le travail a été perdu. Sur 3 600 requêtes, un aléa réseau est CERTAIN : le retry
    doit couvrir la lecture tronquée, la connexion coupée, le socket cassé. On ne laisse remonter que ce qui
    n'est pas réessayable (un 404, un 400)."""
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    for k in range(essais):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503, 504):
                time.sleep(2 * (k + 1))
                continue
            raise
        except (urllib.error.URLError, TimeoutError, ConnectionError, http.client.HTTPException,
                json.JSONDecodeError, OSError):
            time.sleep(2 * (k + 1))
    raise RuntimeError("ESCO injoignable après %d essais : %s" % (essais, url[:90]))


def _concept(uri: str) -> dict:
    return _get(API + "/resource/concept?uri=" + urllib.parse.quote(uri, safe="") + "&language=fr")


def _occupation(uri: str) -> dict:
    return _get(API + "/resource/occupation?uri=" + urllib.parse.quote(uri, safe="") + "&language=fr")


def _uris_occupations() -> list:
    """Descend l'arbre ISCO depuis les 10 grands groupes et collecte toutes les URI d'occupations."""
    racine = _get(API + "/resource/taxonomy?uri=" + urllib.parse.quote(SCHEME, safe="") + "&language=fr")
    file_ = [t["uri"] for t in racine["_links"]["hasTopConcept"]]
    vus, occupations = set(), []
    while file_:
        uri = file_.pop()
        if uri in vus:
            continue
        vus.add(uri)
        if "/occupation/" in uri:
            occupations.append(uri)
            # NE PAS S'ARRÊTER ICI. Une occupation ESCO peut avoir des occupations FILLES
            # (« employé de bureau » -> « assistant d'ingénieur »), reliées par `narrowerOccupation`.
            # Une première version coupait la descente sur la première occupation rencontrée et n'a
            # ramené que 1 699 des ~3 000 occupations : un tiers du référentiel était invisible, sans
            # que rien ne le signale. On continue donc à descendre.
        try:
            n = _concept(uri)
        except RuntimeError:
            continue
        liens = n.get("_links", {})
        for cle in ("narrowerConcept", "narrowerOccupation"):
            for enfant in liens.get(cle, []):
                if enfant["uri"] not in vus:
                    file_.append(enfant["uri"])
        if len(vus) % 200 == 0:
            print("    ... %d concepts visités, %d occupations" % (len(vus), len(occupations)))
    return sorted(occupations)


def _cache_chemin() -> str:
    import lecteur as L
    brut = os.path.join(os.path.dirname(L._DOSSIER_DATASETS), "_raw")
    os.makedirs(brut, exist_ok=True)
    return os.path.join(brut, "esco_occupations.json")


def moissonne() -> None:
    """Phase RÉSEAU : descend l'arbre, lit chaque occupation, écrit le cache brut."""
    print("== ESCO — moissonnage (réseau) ==")
    uris = _uris_occupations()
    print("  occupations trouvées : %d" % len(uris))
    # POINT DE REPRISE : 3 000 appels réseau ne doivent pas s'évaporer sur un aléa. On sauve tous les 200,
    # et on repart de ce qui est déjà lu. Le fichier partiel est remplacé par le cache final à la fin.
    partiel = _cache_chemin() + ".encours"
    out, deja = [], set()
    if os.path.exists(partiel):
        with open(partiel, encoding="utf-8") as f:
            out = json.load(f)
        deja = {o["uri"] for o in out}
        print("  reprise : %d occupations déjà lues" % len(deja))
    for i, uri in enumerate(uris, 1):
        if uri in deja:
            continue
        try:
            o = _occupation(uri)
        except RuntimeError as e:
            print("    ! %s" % e)
            continue
        liens = o.get("_links", {})
        essentielles = liens.get("hasEssentialSkill", [])
        # STATUT réglementé — fait VRAI (directive 2005/36/CE) mais qui ne donne PAS le contenu des normes :
        # il ne fermera donc JAMAIS l'axe « normes, réglementation et certifications ». On le capture parce
        # qu'il est vrai et utile, pas parce qu'il suffirait.
        note = (liens.get("regulatedProfessionNote") or {})
        uri_note = note.get("uri", "") if isinstance(note, dict) else ""
        out.append({
            "uri": uri,
            "prefere": (o.get("preferredLabel") or {}).get("fr", ""),
            "alternatifs": (o.get("alternativeLabel") or {}).get("fr", []) or [],
            "description": ((o.get("description") or {}).get("fr") or {}).get("literal", ""),
            "code_isco": o.get("code", ""),
            # NE PAS écrire « non réglementée » quand ESCO dit `unregulated`. Le texte associé à ce drapeau
            # dit littéralement : « pour vérifier si cette profession est réglementée dans les États membres,
            # veuillez consulter la base de données des professions réglementées ». C'est une ABSENCE
            # D'INFORMATION, pas un fait. Vécu : la table affirmait « avocat : non réglementée », ce qui est
            # FAUX. Le drapeau `regulated` ne marque que les professions SECTORIELLES à reconnaissance
            # automatique (médecin, infirmier, dentiste, sage-femme, pharmacien, vétérinaire, architecte) :
            # 15 sur 2 938. On ne publie QUE celles-là, et on nomme exactement ce qu'elles sont.
            "reglementee": ("profession sectorielle à reconnaissance automatique "
                            "(directive 2005/36/CE, titre III chapitre III)"
                            if uri_note.endswith("/regulated") else ""),
            "gestes": sorted({s["title"] for s in essentielles if s.get("skillType") == TYPE_GESTE}),
            "savoirs": sorted({s["title"] for s in essentielles if s.get("skillType") == TYPE_SAVOIR}),
        })
        if i % 100 == 0:
            print("    ... %d/%d occupations lues" % (i, len(uris)))
        if len(out) % 200 == 0:
            with open(partiel, "w", encoding="utf-8") as f:
                json.dump(out, f, ensure_ascii=False)
        time.sleep(0.05)
    chemin = _cache_chemin()
    with open(chemin, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False)
    if os.path.exists(partiel):
        os.remove(partiel)
    print("  cache écrit : %s (%d occupations)" % (chemin, len(out)))


def _variantes(libelle: str) -> set:
    """« boulanger ou boulangère » et « boulanger/boulangère » -> {boulanger, boulangère} + la forme entière.

    ON NE DÉCOUPE QUE LE DOUBLET DE GENRE PUR : deux MOTS SIMPLES, sans virgule, sans qualificatif.
    Mesuré (2026-07-10), deux fausses attributions successives :
      • « écrivain ou écrivaine, militaire » -> variante « écrivain » -> vole les gestes de l'occupation
        ESCO « écrivain/écrivaine » ; or un écrivain militaire est une occupation DISTINCTE ;
      • « écrivain ou écrivaine politique » -> même vol, la virgule ne suffisait donc pas à s'en protéger.
    D'où la règle finale : les deux parts doivent être des mots simples (« boulanger », « boulangère »).
    Tout libellé qualifié ne s'apparie que par sa forme ENTIÈRE, et reste NON TRAITÉ à défaut d'homologue.

    Égalité EXACTE ensuite : aucune normalisation d'accents, aucun rapprochement flou."""
    base = libelle.strip().lower()
    morceaux = {base}
    if "," in base:                                   # qualificatif -> occupation distincte, on ne scinde pas
        return morceaux
    for sep in (" ou ", "/"):
        if sep in base:
            parts = [m.strip() for m in base.split(sep)]
            if (len(parts) == 2 and all(len(m) >= 3 and " " not in m for m in parts)):
                morceaux.update(parts)
            break
    return morceaux


def _metiers_attestes(dossier: str) -> set:
    chemin = os.path.join(dossier, "occupation_personne.jsonl")
    vus = set()
    with open(chemin, encoding="utf-8") as f:
        for ligne in f:
            if ligne.startswith('{"_relation"'):
                continue
            try:
                v = json.loads(ligne)["valeur"]
            except (ValueError, KeyError):
                continue
            if v and "::" not in v and 2 <= len(v) <= 90:
                vus.add(v)
    return vus


def aligne(occupations: list, metiers: set):
    """Alignement sous gardes 1-3. Renvoie (metier -> occupation, comptes)."""
    par_variante = collections.defaultdict(set)
    for o in occupations:
        for lab in [o["prefere"]] + list(o["alternatifs"]):
            for v in _variantes(lab):
                par_variante[v].add(o["uri"])
    ambigues = {v for v, u in par_variante.items() if len(u) > 1}     # GARDE 2
    index = {v: next(iter(u)) for v, u in par_variante.items() if len(u) == 1}
    par_uri = {o["uri"]: o for o in occupations}

    apparie, ambigus, absents = {}, 0, 0
    for m in metiers:
        cibles = {index[v] for v in _variantes(m) if v in index}
        if len(cibles) == 1:                                          # GARDE 3
            apparie[m] = par_uri[next(iter(cibles))]
        elif len(cibles) > 1:
            ambigus += 1
        else:
            absents += 1
    print("  variantes ESCO : %d (dont %d ambiguës, écartées)" % (len(par_variante), len(ambigues)))
    print("  métiers appariés : %d | ambigus rejetés : %d | sans correspondance : %d"
          % (len(apparie), ambigus, absents))
    return apparie


def publie_depuis_cache() -> None:
    """Phase HORS LIGNE : aligne le cache sur les métiers attestés et publie les tables."""
    import lecteur as L
    chemin = _cache_chemin()
    if not os.path.exists(chemin):
        raise SystemExit("cache absent : lance d'abord `python3 ingestion/ingere_esco.py moissonne`")
    with open(chemin, encoding="utf-8") as f:
        occupations = json.load(f)
    print("== ESCO — publication (hors ligne, %d occupations en cache) ==" % len(occupations))
    metiers = _metiers_attestes(L._DOSSIER_DATASETS)
    print("  métiers attestés : %d" % len(metiers))
    apparie = aligne(occupations, metiers)

    defs = [(m, o["description"]) for m, o in sorted(apparie.items()) if o["description"].strip()]
    gestes = [(m, ", ".join(o["gestes"])) for m, o in sorted(apparie.items()) if o["gestes"]]
    savoirs = [(m, ", ".join(o["savoirs"])) for m, o in sorted(apparie.items()) if o["savoirs"]]
    iscos = [(m, o["code_isco"]) for m, o in sorted(apparie.items()) if o["code_isco"]]
    regl = [(m, o["reglementee"]) for m, o in sorted(apparie.items()) if o.get("reglementee")]

    _publie("definition_esco_metier", "convention", SRC_DEF, defs)
    _publie("geste_metier", "convention", SRC_GESTE, gestes)
    _publie("savoir_metier", "convention", SRC_SAVOIR, savoirs)
    _publie("code_isco_metier", "convention", SRC_ISCO, iscos)
    _publie("reglementation_metier", "convention", SRC_REGL, regl)


if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 else "publie"
    if action == "moissonne":
        moissonne()
    else:
        publie_depuis_cache()
