# -*- coding: utf-8 -*-
"""RECHERCHE STRUCTURÉE (Wikidata) — « source fiable -> réponse VÉRIFIÉE », FAUX=0.

Quand Provara n'a pas un fait en base, il peut l'aller chercher sur une SOURCE STRUCTURÉE de confiance
(Wikidata via le miroir QLever) et en extraire la valeur de façon DÉTERMINISTE. Aucun scraping de texte
libre ici : une requête SPARQL exacte -> une valeur exacte, ou rien (abstention). L'entité doit se résoudre
en UN SEUL QID portant la propriété (sinon ambiguïté -> None, jamais un choix arbitraire).

stdlib pure (urllib), souverain. Réseau requis (opt-in côté appelant). Dégradation gracieuse : toute erreur
réseau/parse -> None.
"""
from __future__ import annotations

import html as _html
import json
import re
import time as _time
import urllib.parse
import urllib.request

import https_confiance                     # urlopen à repli épinglé (magasin Windows parfois pollué -> faux « expired »)
from base_faits import normalise as _normalise

ENDPOINT = "https://qlever.dev/api/wikidata"
_PREFIXES = ("PREFIX wdt: <http://www.wikidata.org/prop/direct/> "
             "PREFIX wd: <http://www.wikidata.org/entity/> "
             "PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> "
             "PREFIX wikibase: <http://wikiba.se/ontology#> ")
_UA = "Provara/1.0 (https://github.com/Provara-IA/Provara) recherche-structuree"

_SIGNALEES: set = set()   # échecs réseau déjà affichés (un par message distinct : pas de spam en mode hors-ligne)


def _signale(ou: str, e: Exception) -> None:
    """Rend un échec RÉSEAU visible en console (dans le .exe c'est le seul canal de diagnostic) — la dégradation
    reste gracieuse (l'appelant reçoit None comme avant), mais plus JAMAIS silencieuse."""
    msg = "%s : %r" % (ou, e)
    if msg in _SIGNALEES:
        return
    _SIGNALEES.add(msg)
    try:
        print("  [Provara] recherche web en échec — %s" % msg, flush=True)
    except Exception:
        pass

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
    with https_confiance.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())["results"]["bindings"]


def _echappe(s: str) -> str:
    return s.replace("\\", "").replace('"', "").strip()


def interroge(attribut: str, entite: str, timeout: int = 20):
    """(attribut, entité) -> (valeur, "Wikidata") ou None. L'entité (label FR exact, casse+accents préservés) est
    résolue vers l'entité HOMONYME LA PLUS NOTOIRE (plus de liens Wikipédia) — désambiguïsation défendable et
    TRANSPARENTE (la réponse est attribuée à Wikidata, jamais présentée comme une vérité absolue de Provara)."""
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
    except Exception as e:
        _signale("Wikidata (qlever.dev)", e)
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
    "quoi ou comment combien pourquoi donne moi dis peux tu me ce cette a plus grand grande grands moins "
    # mots de DISCOURS (pas de contenu) : sans eux, « quelle boisson serait vraiment rafraîchissante » exigeait
    # « serait » et « vraiment » sur les pages -> tout était rejeté et la recherche restait muette
    "serait seraient serais sera vraiment tres assez trop plutot bien dire savoir voudrais aimerais faudrait".split())


_WIKI_PREFIXES = re.compile(
    r"^\s*(?:s['e ]?il\s+te\s+pla[iî]t\s+)?"
    r"(?:quel(?:le)?s?\s+(?:est|sont|était|etait|étaient|etaient)|qui\s+(?:est|sont|a|ont)|"
    r"qu['e ]?\s*est[- ]?ce\s+que|c['e ]?\s*est\s+quoi|c['e ]?\s*est\s+qui|donne(?:s|z)?[- ]?moi|"
    r"dis[- ]?moi|peux[- ]?tu(?:\s+me)?|sais[- ]?tu|connais[- ]?tu|montre(?:s|z)?[- ]?moi|"
    r"explique(?:s|z)?[- ]?moi|parle[- ]?moi\s+de|quel(?:le)?s?|comment|combien|pourquoi|o[uù]|quand|"
    # INTENTIONS (« je voudrais construire X » = le sujet est X, pas la phrase entière -> sans ça, la recherche
    # plein-texte matchait n'importe quoi : « je voudrais construire un moteur à eau » rapportait le Concorde).
    r"je\s+(?:voudrais|veux|souhaite(?:rais)?|aimerais|cherche\s+[aà]?|dois|peux|pourrais)|j['e ]?\s*aimerais|"
    r"puis[- ]?je|il\s+me\s+faut|aide[- ]?moi\s+[aà]|dans|pays)\s+",
    re.I)
# Verbes d'ACTION de tête (après les préfixes) : « construire un moteur à eau » -> « un moteur à eau ».
# Infinitifs seulement (jamais « construit » : « qui a construit la tour Eiffel » garde son participe).
# Verbes d'EXPOSÉ avec leur « de » (« peux-tu me PARLER DE Brive » : vécu 2026-07-06 — le terme partait
# pollué et la recherche plein-texte servait « RAFLE de Brive-la-Gaillarde » au lieu de la ville).
_WIKI_VERBES = re.compile(
    r"^(?:(?:me\s+|nous\s+)?(?:parler|pr[ée]senter|d[ée]crire|exposer)\s+(?:de\s+|d['’]\s*)?|"
    r"(?:construire|fabriquer|cr[ée]er|faire|acheter|trouver|obtenir|installer|r[ée]parer|utiliser|"
    r"dire|savoir|conna[iî]tre|conseiller|recommander|proposer|sugg[ée]rer)\s+)", re.I)


def _termes_wiki(question: str) -> str:
    """Sujet de recherche = la question MOINS ses préfixes interrogatifs/commandes/intentions de tête (on GARDE
    le sujet intact, articles compris : « le roi de la pop » reste tel quel -> trouve Michael Jackson)."""
    q = (question or "").strip().rstrip("?.! ").strip()
    prev = None
    while q and q != prev:
        prev = q
        q = _WIKI_PREFIXES.sub("", q).strip()
        q = _WIKI_VERBES.sub("", q).strip()
    return q


# Balises AVEC attributs quotés : les pages MediaWiki modernes embarquent du JSON Parsoid dans data-mw="{…}"
# qui contient des `>` — la regex naïve <[^>]+> coupait la balise au premier `>` et le JSON fuyait dans le
# « texte » (vécu 2026-07-06 : « A Brives » servait l'infobox {{…}} illisible comme extrait).
_BALISE_RE = re.compile(r"<[^>\"']*(?:\"[^\"]*\"[^>\"']*|'[^']*'[^>\"']*)*>")


def _dist2(a: str, b: str) -> int:
    """Distance d'édition bornée (>2 d'écart de longueur -> 3 : « pas proche »). Pour tolérer une FAUTE."""
    if abs(len(a) - len(b)) > 2:
        return 3
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def _pertinent(terme: str, titre: str, snippet: str) -> bool:
    """GARDE DE PERTINENCE (FAUX=0) : le résultat doit PARLER du sujet demandé. La recherche plein-texte de
    Wikipédia renvoie TOUJOURS quelque chose — sans ce garde, un sujet absent rapportait un article sans rapport
    comme s'il répondait. Exigence : les mots PLEINS du sujet se retrouvent dans le titre ou l'extrait de
    correspondance (TOUS si ≤3 mots, ≥60 % sinon), à une faute près pour les mots ≥5 lettres (distance ≤2 :
    « parmezzan » -> « parmesan » passe). Ce garde ne peut que REJETER un rapport, jamais en fabriquer."""
    mots = [m for m in _normalise(terme).split() if len(m) >= 3 and m not in _WIKI_STOP]
    if not mots:
        return False
    cible = set(_normalise(_BALISE_RE.sub(" ", "%s %s" % (titre, snippet))).split())
    trouves = 0
    for m in mots:
        if m in cible or (len(m) >= 5 and any(_dist2(m, c) <= 2 for c in cible)):
            trouves += 1
    requis = len(mots) if len(mots) <= 3 else max(3, -(-len(mots) * 3 // 5))   # plafond arrondi sup de 60 %
    return trouves >= requis


def cherche_web_libre(question: str, timeout: int = 15):
    """WEB LIBRE (Wikipédia, recherche plein-texte) : renvoie (extrait VERBATIM, titre, url) ou None.
    FAUX=0 : l'extrait est RAPPORTÉ tel quel et ATTRIBUÉ ; jamais présenté comme une vérité vérifiée de Provara
    (design Yohan : « d'après [source]… »). Réseau requis (opt-in). Dégradation gracieuse -> None."""
    terme = _termes_wiki(question)
    if not terme:
        return None
    try:
        u = ("https://fr.wikipedia.org/w/api.php?action=query&list=search&srlimit=3&format=json&srsearch="
             + urllib.parse.quote(terme))
        hits = json.loads(https_confiance.urlopen(
            urllib.request.Request(u, headers={"User-Agent": _UA}), timeout=timeout).read()
        ).get("query", {}).get("search", [])
        # premier résultat PERTINENT (garde FAUX=0) ; aucun -> abstention honnête plutôt qu'un hors-sujet.
        hit = next((h for h in hits if _pertinent(terme, h.get("title", ""), h.get("snippet", ""))), None)
        if hit is None:
            return None
        titre = hit["title"]
        u2 = "https://fr.wikipedia.org/api/rest_v1/page/summary/" + urllib.parse.quote(titre.replace(" ", "_"))
        s = json.loads(https_confiance.urlopen(
            urllib.request.Request(u2, headers={"User-Agent": _UA}), timeout=timeout).read())
        extrait = (s.get("extract") or "").strip()
        url = (((s.get("content_urls") or {}).get("desktop") or {}).get("page")
               or "https://fr.wikipedia.org/wiki/" + urllib.parse.quote(titre.replace(" ", "_")))
        return (extrait, titre, url) if extrait else None
    except Exception as e:
        _signale("Wikipédia (fr.wikipedia.org)", e)
        return None


# ———————————————— MULTI-SOURCES : l'index du web ENTIER par mots-clés + vérification DE CONTEXTE sur site ————————————————
# Réponse au principe « une encyclopédie communautaire seule ne suffit pas » : on interroge un INDEX DU WEB
# (millions de sites spécialisés) par mots-clés, puis on VA SUR chaque site candidat vérifier qu'il parle
# VRAIMENT du sujet (garde de contexte) avant de le rapporter — passage VERBATIM + attribué + lié.
# La promotion « N sources concordent -> fait » reste au système de confiance (veille_corroboration) ; ici on
# RAPPORTE honnêtement qui parle du sujet. Dégradation gracieuse : bloqué/inaccessible -> liste vide.
# Index primaire = Bing RSS (flux prévu pour la consommation programmatique, accepte notre UA honnête) ;
# repli = DuckDuckGo lite (⚠ vécu 2026-07-03 : sert un CAPTCHA « anomaly » aux UA non-navigateur -> 0 résultat).
_DDG_URL = "https://lite.duckduckgo.com/lite/?q=%s&kl=fr-fr"
_DDG_UA = "Mozilla/5.0 (compatible; Provara/1.0; +https://github.com/Provara-IA/Provara)"
_DDG_LINK_RE = re.compile(r"<a\s+([^>]*result-link[^>]*)>(.*?)</a>", re.S | re.I)
_DDG_HREF_RE = re.compile(r"href\s*=\s*[\"']([^\"']+)[\"']", re.I)
_DDG_SNIP_RE = re.compile(r"<td[^>]*result-snippet[^>]*>(.*?)</td>", re.S | re.I)
_BING_RSS_URL = "https://www.bing.com/search?q=%s&format=rss&setmkt=fr-FR"
_MOJEEK_URL = "https://www.mojeek.com/search?q=%s"
_MOJEEK_TITRE_RE = re.compile(r"<h2><a class=\"title\"[^>]*href=\"([^\"]+)\"[^>]*>(.*?)</a>", re.S)
_MOJEEK_SNIP_RE = re.compile(r"<p class=\"s\">(.*?)</p>", re.S)
_INDEX_CACHE: dict = {}   # (index, requête) -> (monotonic, candidats) : absorbe rafales et redemandes
_INDEX_TTL = 900.0        # 15 min — les limites anti-rafale des index (403/CAPTCHA) ne s'accumulent plus


def _url_reelle(href: str) -> str:
    """DDG enveloppe ses liens (…/l/?uddg=<url-encodée>&rut=…) -> URL réelle de la source."""
    if "uddg=" in href:
        cible = (urllib.parse.parse_qs(urllib.parse.urlparse(href).query).get("uddg") or [""])[0]
        if cible:
            return cible
    return "https:" + href if href.startswith("//") else href


def _domaine_de(url: str) -> str:
    net = urllib.parse.urlparse(url).netloc.lower()
    return net[4:] if net.startswith("www.") else net


def _mots_cles(terme: str) -> str:
    """REQUÊTE PAR MOTS-CLÉS : le sujet réduit à ses mots PLEINS (« un moteur à eau » -> « moteur eau »).
    Les articles/mots-outils polluent les index (« UN » matchait les Nations Unies sur Bing)."""
    pleins = [m for m in terme.split() if len(_normalise(m)) >= 3 and _normalise(m) not in _WIKI_STOP]
    return " ".join(pleins) or terme


def _resultats_mojeek(terme: str, timeout: int) -> list:
    """INDEX PRIMAIRE (Mojeek, crawler indépendant) : mots-clés -> candidats [(titre, extrait, url)].
    Accepte notre UA honnête ; résultats = sites SPÉCIALISÉS du web entier (pas de pages d'accueil SEO)."""
    req = urllib.request.Request(_MOJEEK_URL % urllib.parse.quote_plus(terme), headers={"User-Agent": _DDG_UA})
    page = https_confiance.urlopen(req, timeout=timeout).read().decode("utf-8", "ignore")
    out = []
    for bloc in page.split("<!--rs-->")[1:]:              # un bloc = un résultat (marqueurs de la page)
        m = _MOJEEK_TITRE_RE.search(bloc)
        if not m:
            continue
        url = _html.unescape(m.group(1))
        titre = " ".join(_html.unescape(_BALISE_RE.sub(" ", m.group(2))).split())
        ms = _MOJEEK_SNIP_RE.search(bloc)
        extrait = " ".join(_html.unescape(_BALISE_RE.sub(" ", ms.group(1))).split()) if ms else ""
        if titre and url.startswith("http"):
            out.append((titre, extrait, url))
    return out


def _resultats_bing_rss(terme: str, timeout: int) -> list:
    """INDEX PRIMAIRE (Bing RSS) : mots-clés -> candidats [(titre, extrait, url)] de tout le web.
    Flux XML prévu pour être consommé par des programmes (pas de CAPTCHA, UA honnête accepté)."""
    import xml.etree.ElementTree as ET
    req = urllib.request.Request(_BING_RSS_URL % urllib.parse.quote_plus(terme), headers={"User-Agent": _DDG_UA})
    brut = https_confiance.urlopen(req, timeout=timeout).read()
    out = []
    for it in ET.fromstring(brut).iter("item"):
        titre = " ".join(_html.unescape(_BALISE_RE.sub(" ", it.findtext("title") or "")).split())
        url = (it.findtext("link") or "").strip()
        extrait = " ".join(_html.unescape(_BALISE_RE.sub(" ", it.findtext("description") or "")).split())
        if titre and url.startswith("http"):
            out.append((titre, extrait, url))
    return out


def _resultats_ddg_lite(terme: str, timeout: int) -> list:
    """REPLI (DuckDuckGo lite) : même contrat que _resultats_bing_rss. ⚠ sert parfois un CAPTCHA -> []."""
    req = urllib.request.Request(_DDG_URL % urllib.parse.quote_plus(terme), headers={"User-Agent": _DDG_UA})
    page = https_confiance.urlopen(req, timeout=timeout).read().decode("utf-8", "ignore")
    liens = _DDG_LINK_RE.findall(page)
    snippets = [" ".join(_html.unescape(_BALISE_RE.sub(" ", s)).split()) for s in _DDG_SNIP_RE.findall(page)]
    out = []
    for i, (attrs, titre_html) in enumerate(liens):
        m = _DDG_HREF_RE.search(attrs)
        if not m:
            continue
        url = _url_reelle(_html.unescape(m.group(1)))
        titre = " ".join(_html.unescape(_BALISE_RE.sub(" ", titre_html)).split())
        if titre and url.startswith("http"):
            out.append((titre, snippets[i] if i < len(snippets) else "", url))
    return out


# ——— VÉRIFICATION DE CONTEXTE SUR LE SITE : on ne rapporte pas un site sur la foi du moteur, on Y VA ———
_SCRIPT_RE = re.compile(r"<(script|style|noscript|svg|head)[^>]*>.*?</\1>", re.S | re.I)
_CHARSET_RE = re.compile(r"charset=[\"']?([a-zA-Z0-9_-]+)", re.I)


_WIKI_ARTICLE_RE = re.compile(r"https?://([a-z]{2,3})\.(?:m\.)?wikipedia\.org/wiki/([^?#]+)", re.I)


def _texte_page(url: str, timeout: int = 6, cap: int = 400_000) -> str:
    """Télécharge une page (bornée à `cap` octets) et la réduit à son TEXTE (balises/scripts retirés).
    '' si le contenu n'est pas du texte/HTML. Les exceptions réseau remontent (l'appelant distingue
    « inaccessible » de « lue mais hors-sujet »)."""
    # Article Wikipédia -> API TextExtracts (texte BRUT servi par la source elle-même : pas de coordonnées,
    # de bandeaux d'homonymie ni de JSON d'infobox — le scraping HTML de MediaWiki est un champ de mines).
    mw = _WIKI_ARTICLE_RE.match(url)
    if mw:
        u = ("https://%s.wikipedia.org/w/api.php?action=query&prop=extracts&explaintext=1&redirects=1"
             "&format=json&titles=%s" % (mw.group(1).lower(), mw.group(2)))
        brut = https_confiance.urlopen(
            urllib.request.Request(u, headers={"User-Agent": _DDG_UA}), timeout=timeout).read(cap)
        try:
            pages = json.loads(brut.decode("utf-8", "replace")).get("query", {}).get("pages", {}) or {}
            texte = " ".join((next(iter(pages.values()), {}).get("extract") or "").split())
        except Exception:
            texte = ""
        if texte:
            return texte[:cap]                            # repli scraping si l'API est muette (page spéciale…)
    rep = https_confiance.urlopen(urllib.request.Request(url, headers={"User-Agent": _DDG_UA}), timeout=timeout)
    ctype = rep.headers.get("Content-Type", "") or ""
    if "html" not in ctype and "text" not in ctype:
        return ""
    brut = rep.read(cap)
    return " ".join(_html.unescape(_BALISE_RE.sub(" ", _SCRIPT_RE.sub(" ", _decode_page(brut, ctype)))).split())


def _decode_page(brut: bytes, ctype: str) -> str:
    """Décodage tolérant d'une page (charset déclaré dans l'en-tête ou le début du HTML, repli utf-8)."""
    m = _CHARSET_RE.search(ctype) or _CHARSET_RE.search(brut[:4096].decode("ascii", "ignore"))
    try:
        return brut.decode(m.group(1) if m else "utf-8", "replace")
    except LookupError:                                   # charset exotique déclaré -> utf-8 tolérant
        return brut.decode("utf-8", "replace")


# ———————————— VISITE D'UN SITE EXPLICITEMENT NOMMÉ (« regarde yohanfauck.fr ») ————————————
_TITRE_RE = re.compile(r"<title[^>]*>(.*?)</title>", re.S | re.I)


def _fenetre_prose(texte: str, fen: int = 60, pas: int = 30) -> str:
    """La fenêtre la plus « PROSE » d'un texte de page : max de mots-outils FR — les menus de navigation et
    les listes de rubriques n'en ont presque pas. Bornée à ~360 caractères (extrait, pas la page entière)."""
    mots = texte.split()
    if len(mots) <= fen:
        seg = " ".join(mots)
    else:
        seg, meilleur_n = "", -1
        for i in range(0, len(mots) - pas, pas):
            cand = " ".join(mots[i:i + fen])
            n = sum(1 for m in _normalise(cand).split() if m in _WIKI_STOP)
            if n > meilleur_n:
                seg, meilleur_n = cand, n
    if len(seg) > 360:
        seg = seg[:360].rsplit(" ", 1)[0] + "…"
    return seg


def apercu_site(hote_ou_url: str, timeout: int = 8):
    """VISITE le site que l'utilisateur NOMME (vécu 2026-07-06 : « regarde yohanfauck.fr » tombait dans la
    clarification générique). Renvoie (titre, extrait PROSE, url) ou None (injoignable/vide/non-HTML).
    FAUX=0 : contenu RAPPORTÉ verbatim et attribué — jamais un jugement. Jamais d'adresse locale ni d'IP
    (seul le web PUBLIC explicitement demandé est visité). HTTPS d'abord, repli HTTP (petits sites)."""
    u = (hote_ou_url or "").strip().rstrip(".,;!?»«")
    if not re.match(r"^https?://", u, re.I):
        u = "https://" + u
    hote = (urllib.parse.urlparse(u).hostname or "").lower()
    if not hote or "." not in hote or hote == "localhost" or re.fullmatch(r"[0-9.:]+", hote):
        return None
    brut, ctype, u_finale = b"", "", u
    for essai in (u, "http://" + hote):
        try:
            rep = https_confiance.urlopen(urllib.request.Request(essai, headers={"User-Agent": _DDG_UA}),
                                          timeout=timeout)
            ctype = rep.headers.get("Content-Type", "") or ""
            if "html" not in ctype and "text" not in ctype:
                return None
            brut, u_finale = rep.read(400_000), essai
            break
        except Exception as e:
            if essai.startswith("http://"):               # les deux voies ont échoué -> signalé, None
                _signale(hote, e)
    if not brut:
        return None
    page = _decode_page(brut, ctype)
    mt = _TITRE_RE.search(page)
    titre = " ".join(_html.unescape(mt.group(1)).split())[:120] if mt else ""
    texte = " ".join(_html.unescape(_BALISE_RE.sub(" ", _SCRIPT_RE.sub(" ", page))).split())
    if len(texte) < 40:                                   # page quasi vide -> rien d'honnête à rapporter
        return None
    return (titre, _fenetre_prose(texte), u_finale)


def extrait_contextuel(url: str, terme: str, timeout: int = 6):
    """VA SUR le site et VÉRIFIE LE CONTEXTE : la page parle-t-elle vraiment du sujet ? Fenêtre glissante de
    ~70 mots ; la meilleure doit contenir les mots PLEINS du sujet (tous si ≤3, ≥60 % sinon — mêmes exigences
    que _pertinent). Renvoie le passage VERBATIM (≤360 car.), '' si la page est LUE mais ne confirme pas le
    sujet (-> rejeter la source), None si la page est INACCESSIBLE (-> on ne peut pas juger)."""
    try:
        texte = _texte_page(url, timeout)
    except Exception:
        return None
    mots = [m for m in _normalise(terme).split() if len(m) >= 3 and m not in _WIKI_STOP]
    if len(texte) < 80 or not mots:
        return "" if mots else None
    mots_page = texte.split()
    phrase = _normalise(terme) if len(mots) >= 2 else ""  # la phrase EXACTE (« roi de la pop ») vaut plus que
    fen, pas = 70, 35                                     # ses mots épars (« ROI » marketing + « pop-up »…)
    meilleur, meilleur_cle = "", (0, 0, 0)
    for i in range(0, max(1, len(mots_page) - pas), pas):
        seg = " ".join(mots_page[i:i + fen])
        seg_norm = _normalise(seg)
        cible = set(seg_norm.split())
        score = sum(1 for m in mots if m in cible)        # exact après normalisation (pages longues : pas de fuzzy)
        # départage : 1) mots du sujet 2) phrase exacte présente 3) PROSE (les menus de navigation contiennent
        # les mots-clés mais presque aucun mot-outil : on préfère une vraie phrase à une liste de rubriques)
        cle = (score, 1 if phrase and phrase in seg_norm else 0,
               sum(1 for m in seg_norm.split() if m in _WIKI_STOP))
        if cle > meilleur_cle:
            meilleur, meilleur_cle = seg, cle
    requis = len(mots) if len(mots) <= 3 else max(3, -(-len(mots) * 3 // 5))   # arrondi sup de 60 %
    if meilleur_cle[0] < requis:
        return ""                                         # page lue, sujet ABSENT en contexte -> source rejetée
    if len(meilleur) > 360:
        meilleur = meilleur[:360].rsplit(" ", 1)[0] + "…"
    return meilleur


def cherche_web_domaines(question: str, timeout: int = 12, k: int = 3, verifie_sur_site: bool = True) -> list:
    """RECHERCHE PAR MOTS-CLÉS sur l'index du web entier -> jusqu'à k sites de DOMAINES DISTINCTS dont le
    CONTEXTE est vérifié SUR PLACE : [(titre, extrait, url, domaine)]. FAUX=0 en 3 étages :
    1) garde de pertinence sur titre+snippet du moteur (rejette le hors-sujet évident) ;
    2) VISITE du site : le sujet doit s'y retrouver en contexte (fenêtre de mots pleins) -> l'extrait rapporté
       est le PASSAGE VERBATIM de la page, pas le snippet du moteur ; page lue mais muette -> source REJETÉE ;
    3) page inaccessible (bot bloqué, timeout) -> on garde le snippet VERBATIM du moteur (attribué « à vérifier »).
    Un seul résultat par domaine (indépendance). [] si l'index est bloqué ou muet."""
    terme = _termes_wiki(question)
    if not terme:
        return []
    cles = _mots_cles(terme)
    # PHRASE EXACTE d'abord (précision : « "roi de la pop" » ne remonte jamais les sites « ROI » marketing),
    # MOTS-CLÉS en repli (rappel : la phrase exacte peut être trop stricte pour les sujets peu écrits tels quels).
    variantes = ['"%s"' % terme, cles] if " " in cles else [cles]
    assez = max(k + 1, 4)                                 # marge pour les rejets sur site SANS doubler les requêtes
                                                          # d'index (les rafales déclenchent leurs limites : 403/CAPTCHA)
    # Étage 1 : AGRÉGATION D'INDEX (chacun couvre le web entier ; on s'arrête dès qu'on a assez de candidats
    # PERTINENTS) + dédoublonnage par domaine + garde de pertinence sur ce que dit L'INDEX.
    retenus, domaines_vus = [], set()
    for requete in variantes:
        # Ordre 2026-07-06 : Mojeek RÉTROGRADÉ en dernier — son quota serré renvoyait 403 dès la 1re requête
        # (observé au challenge web), ajoutant erreur + latence à CHAQUE recherche alors que Bing RSS et DDG
        # lite répondent fiablement. Le repli existant absorbe les échecs ; on met le fiable DEVANT.
        for backend, nom in ((_resultats_bing_rss, "Bing RSS (www.bing.com)"),
                             (_resultats_ddg_lite, "DuckDuckGo (lite.duckduckgo.com)"),
                             (_resultats_mojeek, "Mojeek (www.mojeek.com)")):
            en_cache = _INDEX_CACHE.get((nom, requete))
            if en_cache and _time.monotonic() - en_cache[0] < _INDEX_TTL:
                candidats = en_cache[1]                   # redemande/rafale absorbée SANS toucher l'index
            else:
                # QUOTA Mojeek serré (~4 req/min observé) : au 2ᵉ tour (mots-clés), on ne le re-sollicite que
                # si le tour « phrase » n'a RIEN donné (sinon Bing/DDG suffisent pour compléter).
                if backend is _resultats_mojeek and requete != variantes[0] and retenus:
                    continue
                try:
                    candidats = backend(requete, timeout)
                except Exception as e:
                    _signale(nom, e)
                    continue
                if len(_INDEX_CACHE) > 200:               # borne mémoire (usage mono-utilisateur)
                    _INDEX_CACHE.clear()
                _INDEX_CACHE[(nom, requete)] = (_time.monotonic(), candidats)
            for titre, extrait, url in candidats:
                dom = _domaine_de(url)
                if not dom or dom in domaines_vus or dom.endswith("duckduckgo.com"):
                    continue                              # un seul résultat par domaine (indépendance des sources)
                try:                                      # source BANNIE par l'utilisateur (« oublie ce site ») -> jamais rapportée
                    import confiance
                    if confiance.est_bannie(dom):
                        continue
                except Exception:
                    pass
                if not _pertinent(terme, titre, extrait):
                    continue                              # hors-sujet -> jamais rapporté (garde FAUX=0)
                domaines_vus.add(dom)
                retenus.append((titre, extrait, url, dom))
            if len(retenus) >= assez:
                break
        if len(retenus) >= k:                             # k sources dès le tour « phrase » -> pas de 2ᵉ tour
            break                                         # (chaque tour re-consomme du quota d'index)
    retenus = retenus[:assez]
    if not verifie_sur_site:
        return [(t, e[:300], u, d) for t, e, u, d in retenus[:k]]
    # Étage 2 : VISITES EN PARALLÈLE (borne le temps de réponse) puis assemblage dans l'ordre de l'index.
    import concurrent.futures
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        passages = list(pool.map(lambda r: extrait_contextuel(r[2], terme), retenus))
    resultats = []
    for (titre, extrait, url, dom), passage in zip(retenus, passages):
        if passage == "":
            continue                                      # visitée et MUETTE sur le sujet -> source rejetée
        resultats.append((titre, (passage or extrait)[:360], url, dom))
        if len(resultats) >= k:
            break
    return resultats
