"""
VEILLE / ACCÈS WEB — recherche SOUVERAINE, FAUX=0 (roadmap #11 : « si mon IA veut approfondir un sujet, recherche
sur internet »).

DISCIPLINE STRICTE (non négociable) :
  • Toute info du web = SUPPOSITION régime RAPPORTÉ (atome A.RAPPORTE), JAMAIS un fait. Elle porte sa PROVENANCE
    (URL + domaine + empreinte) et une confiance basse.
  • Promotion RAPPORTÉ -> FAIT SEULEMENT si (a) CORROBORATION de sources INDÉPENDANTES (domaines distincts ET
    contenu non recopié — « 3 sources qui se recopient ≠ corroboration ») ET (b) un JUGE RÉEL (A.Verdict d'un
    mécanisme fourni par l'appelant : coherence_physique, un test, une falsification…). Jamais l'un sans l'autre.
  • SOUVERAIN : urllib (stdlib) seul ; http/https uniquement ; taille bornée ; UA explicite.
  • DÉGRADATION GRACIEUSE : pas de réseau / erreur / statut d'erreur / oversize -> HORS, JAMAIS une info fabriquée.
  • On APPROFONDIT dans le REGISTRE de sources de confiance (sources.py), pas dans une fouille web non maîtrisée.

HONNÊTETÉ ASSUMÉE : l'EXTRACTION de faits précis depuis du HTML libre est un risque d'hallucination — ce module ne
la fait PAS automatiquement. Il fournit la RÉCUPÉRATION + le TYPAGE rapporté + la PROVENANCE + la CORROBORATION.
Les faits fiables viennent des sources STRUCTURÉES du registre (SPARQL/API), où l'extraction est déterministe.

Testable OFFLINE : recupere() accepte un `transport` injectable (les tests fournissent un faux transport).
"""
from __future__ import annotations

import hashlib
import urllib.parse
import urllib.request
from collections import namedtuple

import atome as A
import sources as SRC

HORS = "hors"
OK = "recupere"
_TAILLE_MAX = 2_000_000            # 2 Mo — borne dure
_SCHEMES_OK = ("http", "https")
UA = "verax-veille/1.0 (souverain; urllib)"

Temoignage = namedtuple("Temoignage", ["url", "domaine", "enonce", "empreinte"])


def _domaine(url: str) -> str:
    net = urllib.parse.urlparse(url).netloc.lower()
    return net[4:] if net.startswith("www.") else net


def _valide_url(url) -> bool:
    if not isinstance(url, str) or not url.strip():
        return False
    p = urllib.parse.urlparse(url)
    return p.scheme in _SCHEMES_OK and bool(p.netloc)


def _urllib_transport(url: str, timeout: int = 15):
    """Transport SOUVERAIN par défaut : GET urllib. Renvoie (statut_http, octets)."""
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        statut = getattr(r, "status", None) or r.getcode()
        return statut, r.read(_TAILLE_MAX + 1)


def recupere(url: str, *, timeout: int = 15, transport=None):
    """Récupère une URL. Renvoie (OK, texte, meta) ou (HORS, None, meta). Dégradation gracieuse : TOUTE erreur -> HORS
    (jamais d'exception qui fuit, jamais d'info fabriquée). `transport(url, timeout) -> (statut, octets)` injectable."""
    meta = {"url": url}
    if not _valide_url(url):
        return (HORS, None, {**meta, "raison": "URL invalide ou schéma non http(s)"})
    t = transport or _urllib_transport
    try:
        statut, octets = t(url, timeout=timeout)
    except Exception as e:
        return (HORS, None, {**meta, "raison": f"réseau/erreur : {type(e).__name__}"})
    if not isinstance(octets, (bytes, bytearray)) or len(octets) == 0:
        return (HORS, None, {**meta, "raison": "réponse vide ou non binaire"})
    if len(octets) > _TAILLE_MAX:
        return (HORS, None, {**meta, "raison": "réponse au-delà de la borne de taille"})
    if statut is not None and int(statut) >= 400:
        return (HORS, None, {**meta, "statut_http": int(statut), "raison": "statut HTTP d'erreur"})
    texte = bytes(octets).decode("utf-8", errors="replace")
    return (OK, texte, {**meta, "domaine": _domaine(url), "taille": len(octets),
                        "empreinte": hashlib.sha256(bytes(octets)).hexdigest()})


def rapporte(enonce: str, url: str, *, confiance: float = 0.3):
    """Info web -> SUPPOSITION régime RAPPORTÉ (JAMAIS un fait) portant sa provenance. Confiance basse par défaut."""
    if not isinstance(enonce, str) or not enonce.strip():
        raise ValueError("énoncé rapporté requis")
    dom = _domaine(url) if _valide_url(url) else "?"
    return A.suppose(enonce, A.RAPPORTE,
                     A.Portee(A.DOMAINE, f"rapporté du web ({dom}) ; à corroborer par sources indépendantes"),
                     confiance, base=f"source rapportée : {url}")


def independantes(temoignages):
    """Filtre l'INDÉPENDANCE : un seul témoignage par DOMAINE, et empreintes de contenu DISTINCTES (deux domaines
    au contenu identique = recopie = NON indépendants). Renvoie la sous-liste indépendante."""
    vus_dom, vues_emp, out = set(), set(), []
    for t in temoignages:
        if t.domaine in vus_dom or t.empreinte in vues_emp:
            continue
        vus_dom.add(t.domaine)
        vues_emp.add(t.empreinte)
        out.append(t)
    return out


def corrobore(enonce: str, temoignages, *, minimum: int = 2, juge=None):
    """Tente de promouvoir un énoncé RAPPORTÉ en FAIT. EXIGE (a) >= `minimum` témoignages INDÉPENDANTS qui
    l'affirment ET (b) un JUGE RÉEL `juge(enonce, temoignages_indep) -> A.Verdict`. Sinon RESTE une SUPPOSITION
    (confiance révisée selon le nombre de sources indépendantes, bornée < 1). Renvoie un atome."""
    indep = independantes([t for t in temoignages if t.enonce == enonce])
    n = len(indep)
    detail = ", ".join(t.domaine for t in indep) if indep else "aucune"
    conf = min(0.9, 0.2 + 0.2 * n) if n else 0.1
    at = A.suppose(enonce, A.RAPPORTE,
                   A.Portee(A.DOMAINE, f"corroboration web ; {n} source(s) indépendante(s) : {detail}"),
                   conf, base=f"corroboration : {n} indépendante(s) [{detail}]")
    if n >= minimum and callable(juge):
        v = juge(enonce, indep)
        if isinstance(v, A.Verdict) and v.verdict:
            return A.promeut(at, v, quand="veille")     # RAPPORTÉ -> FAIT : indépendance ET juge réel réunis
    return at                                            # sinon : reste SUPPOSITION (jamais un fait par défaut)


def approfondit(sujet: str, urls=None, *, domaine: str = None, transport=None):
    """APPROFONDIR un sujet : récupère des sources (URLs fournies, sinon sources de confiance du registre pour
    `domaine`, sinon toutes les sources actives) et renvoie des TÉMOIGNAGES + des atomes RAPPORTÉS (suppositions à
    corroborer, JAMAIS des faits). Pas de réseau / rien récupéré -> HORS (gracieux)."""
    if not isinstance(sujet, str) or not sujet.strip():
        return {"statut": HORS, "sujet": sujet, "raison": "sujet requis"}
    if urls is None:
        src = SRC.pour_domaine(domaine) if domaine else SRC.toutes(actives_seulement=True)
        urls = [s.get("url") for s in src if s.get("url")]
    temoignages = []
    for u in urls:
        statut, _texte, meta = recupere(u, transport=transport)
        if statut != OK:
            continue                                    # dégradation gracieuse : on saute la source KO
        temoignages.append(Temoignage(u, meta["domaine"], sujet, meta["empreinte"]))
    return {"statut": OK if temoignages else HORS, "sujet": sujet, "temoignages": temoignages,
            "atomes": [rapporte(sujet, t.url) for t in temoignages]}
