"""
INGESTION REGPROF — l'axe « normes, réglementation » s'ouvre par la base des professions réglementées de la
Commission européenne (mandat « traiter tout le backlog », suite de la piste « normes » du runbook,
2026-07-12).

POURQUOI REGPROF ET PAS LE DRAPEAU `emploi_reglemente` DE ROME. Sondé d'abord, REJETÉ ensuite — comme P2283 :
la documentation technique de France Travail définit le champ CIRCULAIREMENT (« indication de si l'emploi est
un emploi réglementé », aucun critère, aucune source, tri-état ''/N/O inexpliqué), et il échoue sur deux
ancres en direction NÉGATIVE : `F1101 Architecte = N` (titre protégé, ordre professionnel, loi de 1977) et
`D1102 Boulanger = N` (qualification exigée, loi 96-603). Des positifs sont invraisemblables (« arbitre
assistant », « archiviste » — absents de REGPROF). Un drapeau dont on ne peut pas énoncer le sens ne PUBLIE
rien, même ses positifs. Au doute, HORS.

LA SOURCE. REGPROF (ec.europa.eu/growth/tools-databases/regprof) : la base OFFICIELLE des professions
réglementées déclarées par les États membres au titre de la directive 2005/36/CE — celle-là même que le
drapeau `regulated` d'ESCO référence. API JSON publique (apiUrl dans assets/config.json de l'application).
255 entrées pour la France, libellées en français, avec le RÉGIME de reconnaissance (directive) et le
NIVEAU de qualification exigé.

CE QUE LA TABLE AFFIRME : « ce métier figure dans REGPROF comme profession réglementée en France, sous
l'entrée E, régime R, niveau Q ». POSITIF SEULEMENT — PAS DE MONDE CLOS : le périmètre de REGPROF est la
directive 2005/36/CE ; « notaire » n'y est pas (exclu du champ de la directive) et est pourtant réglementé.
L'ABSENCE de REGPROF n'est donc PAS un fait « non réglementé » — contraste assumé avec le RNCP, répertoire
exhaustif où l'absence est un fait clos.

FAUX=0 — les gardes de l'ALIGNEMENT :
  1. PARENTHÈSE DE GENRE COLLÉE, côté REGPROF seulement : « Infirmier(ère) » -> « infirmier »,
     « Infirmier(ière) de bloc opératoire » -> « infirmier de bloc opératoire ». JAMAIS la parenthèse
     précédée d'une ESPACE : « Architecte (droits acquis) » est un QUALIFICATIF restrictif, l'entrée ne
     s'apparie que par sa forme entière — « architecte » ne doit PAS hériter d'une entrée à périmètre
     réduit. Côté MÉTIER : `ingere_esco._variantes` (une seule définition du doublet de genre).
  2. UNICITÉ CÔTÉ REGPROF : une forme portée par PLUSIEURS entrées de nom distinct est ÉCARTÉE.
  3. UNICITÉ CÔTÉ MÉTIER : un métier atteignant PLUSIEURS entrées distinctes est REJETÉ (ambigu).
     Égalité EXACTE (NFC, minuscules), jamais d'accents pliés, jamais de rapprochement flou.
  4. La valeur reprend les champs de la SOURCE (entrée, régime, niveau, région si non nationale),
     dédoublonnés et triés. Aucune interprétation.

L'axe « normes, réglementation et certifications » reste MIX -> PARTIEL, jamais TRAITÉ : REGPROF couvre la
réglementation d'ACCÈS à la profession ; les normes TECHNIQUES du métier (ISO/AFNOR, dont le contenu est
payant) restent non couvertes.

Le moissonnage est CACHÉ (`datasets/_raw/regprof_fr.json`). Le réseau ne vit que dans `moissonne()`.

Usage :
    python3 ingestion/ingere_regprof.py moissonne     # 1 appel API (~77 Ko)
    python3 ingestion/ingere_regprof.py publie        # hors ligne, depuis le cache
"""
from __future__ import annotations

import collections
import json
import os
import re
import sys
import time
import unicodedata
import urllib.request

from ingere_esco import _variantes as _variantes_metier
from ingere_wikidata import RAW, publie

API = "https://api.tech.ec.europa.eu/regprof20/prodmigration"
UA = "Provara/1.0 (https://github.com/Provara-IA/Provara) offline-knowledge-ingestion"
CACHE = os.path.join(RAW, "regprof_fr.json")
ID_FRANCE = "6"                     # /utility/countries : {"id": "6", "code": "FR"} — revérifié au moissonnage

SRC = ("REGPROF (Commission européenne, base officielle des professions réglementées au titre de la "
       "directive 2005/36/CE, déclarations des États membres) — entrées FRANCE. La valeur affirme que le "
       "métier y figure sous l'entrée citée, avec le régime de reconnaissance et le niveau de qualification "
       "déclarés. POSITIF SEULEMENT : le périmètre de la base est la directive (« notaire », réglementé mais "
       "hors champ, n'y est pas) — l'absence n'est JAMAIS publiée comme « non réglementé ». Alignement par "
       "égalité exacte sous gardes d'unicité bilatérales ; parenthèse de genre collée dépliée "
       "(« Infirmier(ère) »), qualificatif espacé jamais déplié (« Architecte (droits acquis) »).")


def _get_json(url: str, essais: int = 5, timeout: int = 120):
    for k in range(essais):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return json.loads(r.read().decode("utf-8"))
        except (OSError, json.JSONDecodeError):
            if k == essais - 1:
                raise
            time.sleep(4 * (k + 1))


def moissonne() -> None:
    os.makedirs(RAW, exist_ok=True)
    print("== MOISSONNAGE REGPROF (France) ==")
    pays = _get_json(API + "/utility/countries?language=en")
    fr = [c for c in pays if c.get("code") == "FR"]
    if len(fr) != 1 or fr[0]["id"] != ID_FRANCE:
        raise ValueError("REGPROF : l'id de la France a changé (%r) — mettre ID_FRANCE à jour" % fr)
    charge = _get_json(API + "/regprofs?id_country=%s&language=en&maxrows=3000&pagenum=1" % ID_FRANCE)
    n, lst = charge.get("count"), charge.get("list", [])
    if not lst or len(lst) != n:
        raise ValueError("REGPROF : %s entrées annoncées, %d reçues — pagination à revoir, refus de cacher "
                         "un export partiel" % (n, len(lst)))
    tmp = CACHE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(charge, fh, ensure_ascii=False)
    os.replace(tmp, CACHE)
    print("  %d professions réglementées (France) -> %s" % (len(lst), CACHE))


def _nfc_bas(s: str) -> str:
    return unicodedata.normalize("NFC", (s or "").strip()).lower()


# parenthèse COLLÉE au mot (pas d'espace avant), contenu court : un suffixe de genre, jamais un qualificatif.
_PAREN_GENRE = re.compile(r"(?<=\w)\([\w’']{1,7}\)")


def _formes_regprof(nom: str) -> set:
    """Formes d'une entrée REGPROF : la forme entière (+ doublet de genre ESCO) et, si une parenthèse de
    genre COLLÉE existe, la forme dépliée. « Architecte (droits acquis) » (espace avant la parenthèse)
    ne se déplie JAMAIS : le qualificatif restreint le périmètre de l'entrée."""
    lab = _nfc_bas(nom)
    if not lab:
        return set()
    formes = set(_variantes_metier(lab))
    sans = _PAREN_GENRE.sub("", lab)
    if sans != lab and "(" not in sans:
        formes |= _variantes_metier(re.sub(r"\s+", " ", sans).strip())
    return formes


def aligne(entrees: list, metiers: list):
    """metier -> nom d'entrée REGPROF, sous les gardes 2-3."""
    par_forme = collections.defaultdict(set)
    for x in entrees:
        for f in _formes_regprof(x["name"]):
            par_forme[f].add(x["name"])
    ambigues = {f for f, ns in par_forme.items() if len(ns) > 1}                     # GARDE 2
    index = {f: next(iter(ns)) for f, ns in par_forme.items() if len(ns) == 1}

    apparie, ambigus, absents = {}, 0, 0
    for m in metiers:
        cibles = {index[v] for v in _variantes_metier(_nfc_bas(m)) if v in index}
        if len(cibles) == 1:                                                         # GARDE 3
            apparie[m] = next(iter(cibles))
        elif len(cibles) > 1:
            ambigus += 1
        else:
            absents += 1
    print("  formes REGPROF : %d (dont %d ambiguës, écartées)" % (len(par_forme), len(ambigues)))
    print("  métiers appariés : %d | ambigus rejetés : %d | hors REGPROF : %d (PAS « non réglementés »)"
          % (len(apparie), ambigus, absents))
    return apparie


def valeur_regprof(nom: str, lignes: list) -> str:
    """La valeur reprend la SOURCE, dédoublonnée et triée : entrée, régime(s), niveau(x), région si non
    nationale. Aucune interprétation, aucun résumé."""
    details = sorted({(l.get("directive") or "?", l.get("qualification_level") or "?",
                       "" if (l.get("region") in (None, "", "app.region.none"))
                       else " ; région : %s" % l["region"]) for l in lignes})
    corps = " | ".join("régime « %s », niveau de qualification « %s »%s" % d for d in details)
    return ("profession réglementée en France — base REGPROF (Commission européenne, directive 2005/36/CE), "
            "entrée « %s » : %s") % (nom, corps)


def publie_depuis_cache() -> None:
    print("== REGPROF — axe « normes, réglementation » (réglementation d'accès, part MIX) ==")
    if not os.path.exists(CACHE):
        raise SystemExit("cache absent : %s — lancer : python3 ingestion/ingere_regprof.py moissonne" % CACHE)
    with open(CACHE, encoding="utf-8") as fh:
        entrees = json.load(fh).get("list", [])
    if len(entrees) < 200:
        raise ValueError("REGPROF suspect : %d entrées France (255 attendues à ±20 %%) — refus de publier "
                         "depuis un export tronqué" % len(entrees))
    print("  %d entrées France" % len(entrees))

    sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "outils"))
    from genere_sujets import metiers_de_la_carte
    metiers, n_oracle, _ = metiers_de_la_carte()
    print("  univers : %d métiers de la carte (oracle %d)" % (len(metiers), n_oracle))

    apparie = aligne(entrees, metiers)
    if len(apparie) < 20:
        raise ValueError("alignement suspect : %d métiers seulement — gardes ou format à réauditer"
                         % len(apparie))
    par_nom = collections.defaultdict(list)
    for x in entrees:
        par_nom[x["name"]].append(x)
    paires = sorted((m, valeur_regprof(nom, par_nom[nom])) for m, nom in apparie.items())
    publie("profession_reglementee_metier", "convention", SRC, paires)


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "publie"
    if mode == "moissonne":
        moissonne()
    elif mode == "publie":
        publie_depuis_cache()
    else:
        raise SystemExit("usage : ingere_regprof.py [moissonne|publie]")
