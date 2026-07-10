"""
INGESTION `est_domaine` — L'ORACLE DE DOMAINE QUI MANQUAIT (miroir d'`est_metier`, mandat « traiter tout
le backlog », 2026-07-12 : avant de traiter l'ANNEXE D, vérifier que ses sujets EXISTENT).

LE FAUX DE MESURE, MÊME FAMILLE QUE LES MÉTIERS DU 2026-07-12. `genere_sujets` prenait CHAQUE valeur
distincte de `domaine_travail` (P101) pour un domaine. Échantillonné : « Friedrich Nietzsche » (une
PERSONNE — le philologue qui l'étudie a P101 = l'item Nietzsche), « Fonds des Nations unies pour
l'enfance » (une ORGANISATION — un mésusage employeur), « France » (une ENTITÉ GÉOGRAPHIQUE). Le sujet
« résultats établis du domaine Friedrich Nietzsche » est MAL FORMÉ : 905 sujets-domaines faux × 2 axes
= un backlog qui ment.

LA GARDE JUGE LES QID RÉELLEMENT UTILISÉS, PAS LES PORTEURS DU LIBELLÉ. Première version essayée :
exclure tout libellé porté par un item de classe exclue — SUR-EXCLUSION mesurée : « peinture » tombait
parce qu'une PAGE D'HOMONYMIE porte aussi ce libellé, alors que les 4 962 peintres pointent Q11629
(peinture, forme d'art). La garde vraie : un libellé est retiré ssi TOUTES les cibles de P101 qui le
portent sont de classe exclue. (Et une garde POSITIVE « disciplines seulement » sous-compterait :
« permaculture » est typée mouvement social, son sujet est pourtant traitable.)

LES CLASSES EXCLUES (chacune PROUVÉE mal formée comme domaine, aucune « au cas où ») :
    Q5 humain · Q101352 patronyme · Q202444 prénom · Q4167410 page d'homonymie ·
    Q43229 organisation (P31/P279*) · Q27096213 entité géographique (P31/P279*)
Un OBJET (« Grillz ») ou un GENRE (« gospel ») restent : des résultats établis à leur sujet existent —
retirer un sujet traitable serait l'autre mesure fausse. Au doute, le sujet RESTE ; c'est le FAIT douteux
qui sort, jamais l'inverse.

UNE RELATION : `est_domaine` — « <libellé fr> » -> le(s) QID non exclus qui le portent (triés).
Un libellé du store sans cible P101 retrouvée n'est PAS attesté (7 mesurés : dérive de libellés entre
moissons) : l'oracle atteste, il ne devine pas.

CE SCRIPT N'EFFACE RIEN : `domaine_travail` garde ses valeurs (les FAITS sont vrais — le philologue
travaille bien sur Nietzsche). C'est la GÉNÉRATION DES SUJETS qui filtre, par lookup.

Usage :
    python3 ingestion/ingere_domaines_attestes.py moissonne    # 2 requêtes QLever (POST)
    python3 ingestion/ingere_domaines_attestes.py publie       # hors ligne, depuis le snapshot
"""
from __future__ import annotations

import collections
import json
import os
import sys
import time
import urllib.request

from base_faits import _sans_articles
from ingere_wikidata import RAW, charge_raw_json, publie, snapshot_brut

ENDPOINT = "https://qlever.dev/api/wikidata"
UA = "Provara/1.0 (https://github.com/Provara-IA/Provara) offline-knowledge-ingestion"
SNAPSHOT = os.path.join(RAW, "domaines_p101.json")
PFX = ("PREFIX wdt: <http://www.wikidata.org/prop/direct/> PREFIX wd: <http://www.wikidata.org/entity/> "
       "PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> ")

_Q_CIBLES = PFX + ('SELECT DISTINCT ?dom ?l WHERE { ?p wdt:P101 ?dom . ?dom rdfs:label ?l . '
                   'FILTER(lang(?l) = "fr") }')
_EXCLUSION = ("{ ?o wdt:P31 wd:Q5 } UNION { ?o wdt:P31 wd:Q101352 } UNION { ?o wdt:P31 wd:Q202444 } "
              "UNION { ?o wdt:P31 wd:Q4167410 } UNION { ?o wdt:P31/wdt:P279* wd:Q43229 } "
              "UNION { ?o wdt:P31/wdt:P279* wd:Q27096213 }")

SRC = ("Wikidata/QLever — cibles RÉELLEMENT utilisées de P101 (domaine de travail), libellés français, "
       "moins les classes prouvées mal formées comme domaine : humain, patronyme, prénom, page "
       "d'homonymie, organisation, entité géographique. Un libellé est retiré ssi TOUTES ses cibles "
       "utilisées sont exclues (juger les porteurs du libellé sur-excluait : « peinture » tombait par sa "
       "page d'homonymie). ORACLE de la question « ce libellé est-il un domaine ? » pour l'ANNEXE D — "
       "les 905 valeurs retirées (« Friedrich Nietzsche », « France », UNICEF…) restent des FAITS vrais "
       "de domaine_travail, elles ne sont plus des SUJETS.")


def _post(requete: str, timeout: int = 600, essais: int = 5) -> dict:
    for k in range(essais):
        try:
            req = urllib.request.Request(ENDPOINT, data=requete.encode(), method="POST",
                                         headers={"User-Agent": UA,
                                                  "Accept": "application/qlever-results+json",
                                                  "Content-Type": "application/sparql-query"})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return json.loads(r.read().decode("utf-8"))
        except (OSError, json.JSONDecodeError):
            if k == essais - 1:
                raise
            time.sleep(4 * (k + 1))
    return {}


def _qid(cellule: str) -> str:
    return cellule.rsplit("/", 1)[-1].strip("<>")


def _texte(cellule: str) -> str:
    if cellule.startswith('"'):
        i = cellule.rfind('"')
        return cellule[1:i] if i > 0 else cellule
    return cellule


def moissonne() -> None:
    print("== MOISSONNAGE cibles P101 + classes exclues ==")
    d = _post(_Q_CIBLES)
    cibles = [(_qid(r[0]), _texte(r[1])) for r in d.get("res", []) if len(r) >= 2 and r[0] and r[1]]
    if len(cibles) < 20000:
        raise ValueError("cibles P101 suspectes : %d lignes (≈35 000 attendues) — refus de cacher un "
                         "résultat tronqué" % len(cibles))
    print("  %d couples (QID, libellé fr) cibles de P101" % len(cibles))

    qids = sorted({q for q, _ in cibles})
    valeurs = " ".join("wd:%s" % q for q in qids)
    d2 = _post(PFX + "SELECT DISTINCT ?o WHERE { VALUES ?o { %s } %s }" % (valeurs, _EXCLUSION))
    exclus = sorted({_qid(r[0]) for r in d2.get("res", []) if r and r[0]})
    if not exclus or len(exclus) > len(qids) // 2:
        raise ValueError("classes exclues suspectes : %d/%d QID — la garde exclurait trop ou rien"
                         % (len(exclus), len(qids)))
    print("  %d QID de classe exclue sur %d" % (len(exclus), len(qids)))
    snapshot_brut("domaines_p101", [{"cibles": cibles, "exclus": exclus}])


def oracle(cibles: list, exclus: set) -> list:
    """[(libellé, 'QID, QID…')] : les libellés dont AU MOINS UNE cible utilisée n'est pas exclue —
    seules les cibles non exclues sont publiées comme attestation.

    GROUPEMENT PAR LA CLÉ DE `fonctionnel` (`_sans_articles`) : « physique » et « Physique » sont deux
    surfaces d'une même clé ; émises séparément elles se rejetaient mutuellement en multivalué et le
    domaine SORTAIT de l'oracle en silence (139 rejets mesurés, dont « physique »). On unionne les QID
    sous la clé et on émet UNE surface déterministe (la plus courte puis lexicographique) — le lookup du
    générateur passe par la même clé."""
    par_cle = collections.defaultdict(set)
    surfaces = collections.defaultdict(list)
    for q, lab in cibles:
        if "::" in lab:
            continue
        cle = _sans_articles(lab)
        if not cle:
            continue
        par_cle[cle].add(q)
        surfaces[cle].append(lab)
    gardes = []
    for cle, qs in par_cle.items():
        vivants = sorted(qs - exclus)
        if vivants:
            surface = sorted(surfaces[cle], key=lambda s: (len(s), s))[0]
            gardes.append((surface, ", ".join(vivants)))
    return sorted(gardes)


def publie_depuis_cache() -> None:
    print("== ORACLE DE DOMAINE — libellés attestés (cibles P101 non exclues) ==")
    brut = charge_raw_json(SNAPSHOT)
    if not brut:
        raise SystemExit("snapshot absent : %s — lancer : python3 ingestion/ingere_domaines_attestes.py "
                         "moissonne" % SNAPSHOT)
    cibles = [tuple(c) for c in brut[0]["cibles"]]
    exclus = set(brut[0]["exclus"])
    paires = oracle(cibles, exclus)
    print("  libellés attestés domaine : %d (sur %d cibles distinctes)" % (len(paires), len({l for _, l in cibles})))
    if len(paires) < 10000:
        raise ValueError("oracle suspect : %d libellés — refus de publier une table tronquée qui "
                         "déclarerait « non-domaine » des domaines réels" % len(paires))
    publie("est_domaine", "convention", SRC, paires)


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "publie"
    if mode == "moissonne":
        moissonne()
    elif mode == "publie":
        publie_depuis_cache()
    else:
        raise SystemExit("usage : ingere_domaines_attestes.py [moissonne|publie]")
