# -*- coding: utf-8 -*-
"""VALIDE veille_structure.py — OFFLINE (transport factice, zéro réseau), FAUX=0.

Régressions vécues 2026-07-06 (« A Brives » -> infobox {{…}} illisible servie comme extrait) :
  1. _BALISE_RE naïve (<[^>]+>) coupait les balises MediaWiki au premier `>` D'UN ATTRIBUT (data-mw="{…JSON…}")
     -> le JSON Parsoid fuyait dans le « texte » de la page.
  2. Les articles Wikipédia sont désormais lus via l'API TextExtracts (texte brut servi par la source),
     jamais scrapés (coordonnées/bandeaux/infobox = champ de mines).
Plus les gardes existantes : _termes_wiki (dépouillage des préfixes), _pertinent (rejet du hors-sujet),
extrait_contextuel (fenêtre de mots pleins, préférence prose)."""
import io
import json as _json
import sys

import veille_structure as VS

ok = 0
ko = 0


def check(c, l):
    global ok, ko
    if c:
        ok += 1
    else:
        ko += 1
        print(f"  FAIL: {l}")


# ————— (1) _BALISE_RE : attributs quotés contenant `>` (JSON Parsoid data-mw) entièrement retirés —————
html = ('avant <a data-mw=\'{"parts":[{"template":{"target":{"wt":"Infobox commune"},"params":'
        '{"statut":{"wt":"<small>([[sous-préfecture]])</small>"}}}}]}\' href="/wiki/X">Lien</a> après')
texte = VS._BALISE_RE.sub(" ", html)
check("wt" not in texte and "Infobox" not in texte and "sous-préfecture" not in texte,
      "JSON d'attribut (data-mw avec `>` internes) JAMAIS fui dans le texte")
check("avant" in texte and "Lien" in texte and "après" in texte, "le vrai texte survit au dépouillage")
check(VS._BALISE_RE.sub(" ", "<p class=\"a\">x</p>") == " x ", "balise simple avec attribut quoté retirée")
check(VS._BALISE_RE.sub(" ", "2 < 3 dans la prose") == "2 < 3 dans la prose",
      "un `<` de prose (jamais refermé) est GARDÉ")

# ————— (2) _texte_page : article Wikipédia -> API TextExtracts (texte brut), jamais le HTML scrapé —————
_reqs = []


class _Rep:
    def __init__(self, corps, ctype="text/html; charset=utf-8"):
        self._c = corps
        self.headers = {"Content-Type": ctype}

    def read(self, cap=None):
        return self._c[:cap] if cap else self._c


class _FauxHttps:
    @staticmethod
    def urlopen(req, timeout=0):
        url = req.full_url if hasattr(req, "full_url") else str(req)
        _reqs.append(url)
        if "api.php" in url and "extracts" in url:
            corps = _json.dumps({"query": {"pages": {"42": {
                "extract": "Brive-la-Gaillarde est une commune française, sous-préfecture de la Corrèze."}}}})
            return _Rep(corps.encode("utf-8"), "application/json")
        return _Rep(b"<html><body><p>page brute</p></body></html>")


_https_reel = VS.https_confiance
VS.https_confiance = _FauxHttps
try:
    t = VS._texte_page("https://fr.wikipedia.org/wiki/Brive-la-Gaillarde")
    check("commune fran" in t and "sous-pr" in t, "article Wikipédia lu via TextExtracts (texte brut de la source)")
    check(any("api.php" in u for u in _reqs), "la page wiki n'est PAS scrapée : l'API est interrogée")
    t2 = VS._texte_page("https://exemple.org/page")
    check(t2 == "page brute", "page non-wiki : scraping HTML dépouillé inchangé")
finally:
    VS.https_confiance = _https_reel

# ————— (3) extrait_contextuel : fenêtre de mots pleins sur texte INJECTÉ (pas de réseau) —————
_texte_page_reel = VS._texte_page
VS._texte_page = lambda url, timeout=6, cap=400_000: (
    "Menu Accueil Contact " * 10
    + "La tour Eiffel est une tour de fer puddlé construite par Gustave Eiffel à Paris pour l'exposition "
      "universelle de 1889 et elle attire des millions de visiteurs chaque année. " + "Pied de page " * 30)
try:
    p = VS.extrait_contextuel("https://exemple.org/x", "tour eiffel")
    check(p and "Gustave" in p, "le passage VERBATIM pertinent est trouvé dans la page")
    p2 = VS.extrait_contextuel("https://exemple.org/x", "population du wakanda")
    check(p2 == "", "page lue mais MUETTE sur le sujet -> '' (source rejetée, garde FAUX=0)")
finally:
    VS._texte_page = _texte_page_reel


def _leve(url, terme):
    def _boom(u, timeout=6, cap=400_000):
        raise OSError("réseau coupé")
    VS._texte_page = _boom
    try:
        return VS.extrait_contextuel(url, terme)
    finally:
        VS._texte_page = _texte_page_reel


check(_leve("https://exemple.org/x", "tour eiffel") is None,
      "page INACCESSIBLE -> None (on ne peut pas juger, distinct de « muette »)")

# ————— (4) apercu_site : visite d'un site NOMMÉ (vécu « regarde yohanfauck.fr » -> clarification générique) —————
class _FauxSite:
    @staticmethod
    def urlopen(req, timeout=0):
        url = req.full_url if hasattr(req, "full_url") else str(req)
        _reqs.append(url)
        if url.startswith("https://casse.example"):
            raise OSError("pas de HTTPS ici")
        corps = ("<html><head><title>Yohan Fauck — Portfolio</title></head><body>"
                 "<nav>Accueil Projets Contact CV Blog Liens</nav>"
                 "<p>Je suis un développeur passionné par les moteurs de raisonnement et je construis des "
                 "outils qui vérifient les faits avant de les affirmer, parce que la confiance se gagne.</p>"
                 "</body></html>")
        return _Rep(corps.encode("utf-8"))


VS.https_confiance = _FauxSite
try:
    _reqs.clear()
    ap = VS.apercu_site("yohanfauck.fr")
    check(ap is not None and ap[0] == "Yohan Fauck — Portfolio", "titre de la page extrait (balise <title>)")
    check(ap and "développeur" in ap[1] and "raisonnement" in ap[1],
          "l'extrait choisi est la PROSE (fenêtre à mots-outils), pas le menu de navigation")
    check(_reqs and _reqs[0].startswith("https://"), "HTTPS tenté d'abord")
    _reqs.clear()
    ap2 = VS.apercu_site("casse.example.com")
    check(ap2 is not None and ap2[2].startswith("http://"), "repli HTTP quand le site n'a pas de HTTPS")
    check(VS.apercu_site("localhost") is None and VS.apercu_site("127.0.0.1") is None
          and VS.apercu_site("192.168.1.10") is None, "adresses locales/IP JAMAIS visitées")
    check(VS.apercu_site("motsanspoint") is None, "pas un domaine -> None")
finally:
    VS.https_confiance = _https_reel

# ————— (5) gardes existantes : _termes_wiki + _pertinent —————
check(VS._termes_wiki("quelle est la capitale du Japon ?") == "la capitale du Japon",
      "préfixes interrogatifs dépouillés, sujet INTACT (articles compris)")
check(VS._termes_wiki("je voudrais construire un moteur à eau") == "un moteur à eau",
      "intention + verbe d'action de tête dépouillés")
check(VS._termes_wiki("peux-tu me parler de Brive-la-Gaillarde ?") == "Brive-la-Gaillarde",
      "verbe d'exposé + « de » dépouillés (vécu : « parler de Brive » servait la RAFLE de Brive, pas la ville)")
check(VS._termes_wiki("qui a construit la tour Eiffel ?") == "construit la tour Eiffel",
      "participe « construit » jamais confondu avec l'infinitif (il reste dans le terme de recherche)")
check(VS._pertinent("tour eiffel", "Tour Eiffel", "monument parisien de Gustave Eiffel") is True,
      "résultat qui parle du sujet -> pertinent")
check(VS._pertinent("capitale du wakanda", "Gentilés d'ailleurs", "liste d'habitants") is False,
      "résultat hors-sujet -> rejeté (garde FAUX=0)")

print(f"valide_veille_structure : {ok} OK, {ko} KO")
sys.exit(1 if ko else 0)
