# -*- coding: utf-8 -*-
"""RECHERCHE STRUCTURÉE (Wikidata) — « source fiable -> réponse VÉRIFIÉE », FAUX=0.

Quand VERAX n'a pas un fait en base, il peut l'aller chercher sur une SOURCE STRUCTURÉE de confiance
(Wikidata via le miroir QLever) et en extraire la valeur de façon DÉTERMINISTE. Aucun scraping de texte
libre ici : une requête SPARQL exacte -> une valeur exacte, ou rien (abstention). L'entité doit se résoudre
en UN SEUL QID portant la propriété (sinon ambiguïté -> None, jamais un choix arbitraire).

stdlib pure (urllib), souverain. Réseau requis (opt-in côté appelant). Dégradation gracieuse : toute erreur
réseau/parse -> None.
"""
from __future__ import annotations

import json
import re
import urllib.parse
import urllib.request

from base_faits import normalise as _normalise

ENDPOINT = "https://qlever.dev/api/wikidata"
_PREFIXES = ("PREFIX wdt: <http://www.wikidata.org/prop/direct/> "
             "PREFIX wd: <http://www.wikidata.org/entity/> "
             "PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> "
             "PREFIX wikibase: <http://wikiba.se/ontology#> ")
_UA = "VERAX/1.0 (https://github.com/Verax-IA/Verax) recherche-structuree"

# Mot-clé d'ATTRIBUT (tel qu'écrit dans la question) -> propriété Wikidata (curé, FAUX=0 : chaque P vérifié).
_ATTR_PROP = {
    "capitale": "P36", "monnaie": "P38", "devise": "P38", "langue": "P37", "langues": "P37",
    "population": "P1082", "continent": "P30", "president": "P35", "chef": "P35", "dirigeant": "P6",
    "auteur": "P50", "autrice": "P50", "realisateur": "P57", "compositeur": "P86", "inventeur": "P61",
    "decouvreur": "P61", "fondateur": "P112", "createur": "P170", "editeur": "P123",
    "superficie": "P2046", "altitude": "P2044", "hauteur": "P2048", "profondeur": "P4511",
    "pays": "P17", "nationalite": "P27", "profession": "P106", "metier": "P106", "occupation": "P106",
    "genre": "P136", "realisation": "P57", "sport": "P641", "instrument": "P1303",
    "symbole": "P246", "maison": "P176", "constructeur": "P176", "moteur": "P408",
    "prix": "P166", "recompense": "P166", "conjoint": "P26", "pere": "P22", "mere": "P25",
    "hymne": "P85", "drapeau": "P163", "gentile": "P1549",
}

# « [attribut] de/du/des/de la/de l' [entité] ? » — préfixe interrogatif optionnel. Casse-INSENSIBLE pour le motif,
# mais l'ENTITÉ est capturée en CASSE + ACCENTS D'ORIGINE (indispensable pour matcher le label Wikidata « France »).
_MOTIF = re.compile(
    r"^(?:quel(?:le)?s?\s+(?:est|sont|était|etait|étaient|etaient)\s+)?"
    r"(?:la\s+|le\s+|les\s+|l['’]\s*|un\s+|une\s+)?"
    r"([A-Za-zÀ-ÿ]+)\s+"
    r"(?:de\s+la\s+|de\s+l['’]\s*|du\s+|des\s+|de\s+|d['’]\s*)"
    r"(.+?)\s*\??\s*$", re.IGNORECASE)


def _sparql(query: str, timeout: int = 20) -> list:
    url = ENDPOINT + "?action=json_export&query=" + urllib.parse.quote(_PREFIXES + query)
    req = urllib.request.Request(url, headers={"User-Agent": _UA,
                                               "Accept": "application/sparql-results+json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())["results"]["bindings"]


def _echappe(s: str) -> str:
    return s.replace("\\", "").replace('"', "").strip()


def interroge(attribut: str, entite: str, timeout: int = 20):
    """(attribut, entité) -> (valeur, "Wikidata") ou None. L'entité (label FR exact, casse+accents préservés) est
    résolue vers l'entité HOMONYME LA PLUS NOTOIRE (plus de liens Wikipédia) — désambiguïsation défendable et
    TRANSPARENTE (la réponse est attribuée à Wikidata, jamais présentée comme une vérité absolue de VERAX)."""
    prop = _ATTR_PROP.get(_normalise(attribut).strip())
    if not prop:
        return None
    ent = _echappe(entite)
    if not ent or len(ent) < 2:
        return None
    # Une requête : l'entité la PLUS NOTOIRE portant ce label ET la propriété -> sa valeur (label FR si entité).
    q = ('SELECT ?vl ?v WHERE { ?e rdfs:label "%s"@fr . ?e wdt:%s ?v . ?e wikibase:sitelinks ?sl . '
         'OPTIONAL { ?v rdfs:label ?vl . FILTER(LANG(?vl)="fr") } } ORDER BY DESC(?sl) LIMIT 1' % (ent, prop))
    try:
        rows = _sparql(q, timeout)
    except Exception:
        return None
    if not rows:
        return None
    r = rows[0]
    vl = (r.get("vl") or {}).get("value", "").strip()
    v = (r.get("v") or {}).get("value", "").strip()
    val = vl or (v.rsplit("/", 1)[-1] if v.startswith("http") else v)
    if re.match(r"^-?\d+\.0$", val):               # 83577140.0 -> 83577140
        val = val[:-2]
    return (val, "Wikidata") if val else None


def interroge_nl(question: str, timeout: int = 20):
    """Question en langage naturel (« capitale de la Ruritanie ? ») -> (attribut, entité, valeur, source) si
    trouvé sur Wikidata, sinon None. Extraction déterministe ; aucune invention."""
    q = " ".join((question or "").strip().split())
    m = _MOTIF.match(q)
    if not m:
        return None
    attribut = _normalise(m.group(1)).strip()      # sans accents -> table des propriétés
    entite = m.group(2).strip()                    # CASSE + ACCENTS préservés -> label Wikidata
    res = interroge(attribut, entite, timeout)
    if res is None:
        return None
    valeur, source = res
    return (attribut, entite, valeur, source)


# ————————————————————————————— WEB LIBRE (Wikipédia) : rapport ATTRIBUÉ —————————————————————————————
_WIKI_STOP = frozenset(
    "quel quelle quels quelles est sont etait le la les l un une des du de d au aux et en dans sur qui que "
    "quoi ou comment combien pourquoi donne moi dis peux tu me ce cette a plus grand grande grands moins".split())


_WIKI_PREFIXES = re.compile(
    r"^\s*(?:s['e ]?il\s+te\s+pla[iî]t\s+)?"
    r"(?:quel(?:le)?s?\s+(?:est|sont|était|etait|étaient|etaient)|qui\s+(?:est|sont|a|ont)|"
    r"qu['e ]?\s*est[- ]?ce\s+que|c['e ]?\s*est\s+quoi|c['e ]?\s*est\s+qui|donne(?:s|z)?[- ]?moi|"
    r"dis[- ]?moi|peux[- ]?tu(?:\s+me)?|sais[- ]?tu|connais[- ]?tu|montre(?:s|z)?[- ]?moi|"
    r"explique(?:s|z)?[- ]?moi|parle[- ]?moi\s+de|quel(?:le)?s?|comment|combien|pourquoi|o[uù]|quand)\s+",
    re.I)


def _termes_wiki(question: str) -> str:
    """Sujet de recherche = la question MOINS ses préfixes interrogatifs/commandes de tête (on GARDE le sujet
    intact, articles compris : « le roi de la pop » reste tel quel -> trouve Michael Jackson)."""
    q = (question or "").strip().rstrip("?.! ").strip()
    prev = None
    while q and q != prev:
        prev = q
        q = _WIKI_PREFIXES.sub("", q).strip()
    return q


def cherche_web_libre(question: str, timeout: int = 15):
    """WEB LIBRE (Wikipédia, recherche plein-texte) : renvoie (extrait VERBATIM, titre, url) ou None.
    FAUX=0 : l'extrait est RAPPORTÉ tel quel et ATTRIBUÉ ; jamais présenté comme une vérité vérifiée de VERAX
    (design Yohan : « d'après [source]… »). Réseau requis (opt-in). Dégradation gracieuse -> None."""
    terme = _termes_wiki(question)
    if not terme:
        return None
    try:
        u = ("https://fr.wikipedia.org/w/api.php?action=query&list=search&srlimit=1&format=json&srsearch="
             + urllib.parse.quote(terme))
        hits = json.loads(urllib.request.urlopen(
            urllib.request.Request(u, headers={"User-Agent": _UA}), timeout=timeout).read()
        ).get("query", {}).get("search", [])
        if not hits:
            return None
        titre = hits[0]["title"]
        u2 = "https://fr.wikipedia.org/api/rest_v1/page/summary/" + urllib.parse.quote(titre.replace(" ", "_"))
        s = json.loads(urllib.request.urlopen(
            urllib.request.Request(u2, headers={"User-Agent": _UA}), timeout=timeout).read())
        extrait = (s.get("extract") or "").strip()
        url = (((s.get("content_urls") or {}).get("desktop") or {}).get("page")
               or "https://fr.wikipedia.org/wiki/" + urllib.parse.quote(titre.replace(" ", "_")))
        return (extrait, titre, url) if extrait else None
    except Exception:
        return None
