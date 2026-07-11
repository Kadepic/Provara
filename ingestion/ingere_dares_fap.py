"""
INGESTION DARES×FAP — l'axe « rémunération médiane » s'ouvre par sa part FRANCE
(mandat « traiter tout le backlog », piste §4 du runbook « DARES×FAP via le pont ROME », sondée le 2026-07-12).

POURQUOI LA DARES ET PAS EUROSTAT. `earn_ses18_25` (écarté au runbook) est une MOYENNE par grand groupe
ISCO à 1 chiffre. La série « salaire médian » des Portraits statistiques des métiers (Dares) publie la vraie
MÉDIANE, par famille professionnelle FINE (FAP-2009, niveau 225), d'après l'enquête Emploi (Insee). La
définition documentée de la série (édition 1982-2011, p. « présentation ») : « le salaire mensuel net
médian des salariés à temps complet (hors apprentis et stagiaires) ».

LA CHAÎNE, ET CE QUE CHAQUE MAILLON AFFIRME (aucun maillon n'est de nous) :
  1. métier -> code ROME v4        — `code_rome_metier` du store (France Travail v4.61, gardes amont) ;
  2. code ROME -> FAP-2009 fine    — table de passage OFFICIELLE Dares ($FAP9RSQ), part DIRECTE seulement :
                                     les codes dont l'affectation exige la QUALIFICATION de la personne
                                     ($FAP9RAQ) sont écartés et comptés — la qualification d'un MÉTIER
                                     n'existe pas, seule celle d'un poste existe ;
  3. GARDE DE STABILITÉ v3/v4      — la table de passage est écrite pour ROME **v3** ; le store parle ROME
                                     **v4** (piège de millésime documenté : tatoueur D1208 v3 / D1244 v4).
                                     On n'accepte un code QUE si les DEUX affectations Dares — FAP-2009
                                     (côté v3) et FAP-2021 (côté V4, table explicitement « version V4 ») —
                                     tombent dans une famille au MÊME intitulé (égalité normalisée, ou
                                     inclusion d'un intitulé dans l'autre). Un code dont la famille a changé
                                     d'intitulé entre les deux nomenclatures est ÉCARTÉ et compté : on ne
                                     peut plus certifier que le code v4 porte la sémantique v3. Au doute,
                                     HORS. (154 codes-métiers écartés ainsi à la sonde — surtout des
                                     familles RENOMMÉES, on ne cherche pas à les « sauver ».)
  4. FAP-2009 -> médiane           — fichier « salaire médian (3 niveaux) » du portail 2022 des Portraits
                                     statistiques des métiers, période la plus récente (2017-2019).
PERSONNE n'affirme « la médiane du métier M est X » : la médiane est PAR FAMILLE de métiers, et la valeur
le DIT — le nom de la table porte « fap » pour la même raison (leçon Eurostat : nommer honnêtement).

UNE RELATION : `salaire_median_fap_fr_metier` — MIX -> PARTIEL, jamais TRAITÉ : seule la part FRANCE
(une période, un pays) est fermée. Elle complète la part États-Unis (`salaire_median_soc_us_metier`).

FAUX=0 :
  • Médiane exigée NUMÉRIQUE et plausible (800..15000 €/mois) — une valeur hors plage fait TOUT échouer
    (un fichier corrompu ne publie rien).
  • Liste des écartés COMPTÉE à chaque maillon (RAQ, code absent v3, famille instable, pas de médiane).
  • Gardes de volume à chaque maillon : un référentiel tronqué ne publie rien.

CACHE (`datasets/_raw/`) — les quatre fichiers Dares sont servis par la Wayback Machine (le site Dares est
derrière un challenge anti-robot F5/TSPD depuis ~2024 ; ces fichiers sont STATIQUES et leurs captures sont
épinglées par horodatage — suffixe `id_` = octets d'origine, sans réécriture archive) :
  • `dares_passage_fap2009_romev3.txt`   (capture 20231014103614) — table $FAP9RSQ/$FAP9RAQ (SAS) ;
  • `dares_intitules_fap2009.xlsx`       (capture 20231014111847) — 225 intitulés FAP-2009 fins ;
  • `dares_fap2021_passage_rome.xlsx`    (capture 20231014123745) — FAP-2021 <- ROME « version V4 » ;
  • `dares_psm_salaire_median.csv`       (capture 20220404094600) — médianes par FAP-2009, 3 niveaux.

Usage :
    python3 ingestion/ingere_dares_fap.py moissonne     # 4 fichiers (~0,2 Mo)
    python3 ingestion/ingere_dares_fap.py publie        # hors ligne, depuis le cache
"""
from __future__ import annotations

import collections
import json
import os
import re
import sys
import time
import urllib.request

from ingere_wikidata import RAW, publie
from ingere_bls_oes import lit_xlsx

UA = "Mozilla/5.0 (compatible; Provara/1.0; offline-knowledge-ingestion; contact yohan.fauck@gmail.com)"
_WB = "https://web.archive.org/web/%sid_/%s"
SOURCES = (
    ("dares_passage_fap2009_romev3.txt", "20231014103614",
     "https://dares.travail-emploi.gouv.fr/sites/default/files/123f646dfb8646b139d78a04079699c9/passage_fap2009_romev3.txt"),
    ("dares_intitules_fap2009.xlsx", "20231014111847",
     "https://dares.travail-emploi.gouv.fr/sites/default/files/762dab9e16b56b9ba49d9649ca638791/Intitul%C3%A9s_FAP2009.xlsx"),
    ("dares_fap2021_passage_rome.xlsx", "20231014123745",
     "https://dares.travail-emploi.gouv.fr/sites/default/files/f83237de4f41868cb73b0e1aafe4800c/Dares_FAP2021_Table_passage_ROME.xlsx"),
    ("dares_psm_salaire_median.csv", "20220404094600",
     "https://dares.travail-emploi.gouv.fr/sites/default/files/950ac3fe527f83f45c362509f657a62c/"
     "Dares_portraits_statistiques_m%C3%A9tiers_salaire_m%C3%A9dian_3niveaux.csv"),
)
PERIODE = "2017-2019"

SRC = ("Dares, Portraits statistiques des métiers (série « salaire médian », d'après l'enquête Emploi "
       "Insee ; définition documentée de la série : salaire mensuel net médian des salariés à temps complet, "
       "hors apprentis et stagiaires), période %s × table de passage OFFICIELLE Dares ROME v3 -> FAP-2009 "
       "(part directe $FAP9RSQ seulement) × `code_rome_metier` (France Travail v4.61). Couture de millésime "
       "ROME v3/v4 fermée par une GARDE DE STABILITÉ : le code n'est accepté que si ses affectations Dares "
       "FAP-2009 et FAP-2021 (table « version V4 ») portent le même intitulé de famille. La valeur affirme : "
       "le métier relève de la famille FAP-2009 indiquée (affectation Dares de son code ROME) ; la médiane "
       "est celle de la FAMILLE entière (granularité dite), jamais du métier précis. Part FRANCE seulement. "
       "Fichiers Dares statiques servis par la Wayback Machine (site Dares derrière un anti-robot F5/TSPD), "
       "captures épinglées par horodatage." % PERIODE)

C_PASSAGE = os.path.join(RAW, "dares_passage_fap2009_romev3.txt")
C_INTITULES = os.path.join(RAW, "dares_intitules_fap2009.xlsx")
C_FAP2021 = os.path.join(RAW, "dares_fap2021_passage_rome.xlsx")
C_SALAIRES = os.path.join(RAW, "dares_psm_salaire_median.csv")


# ============================================================================================
#  MOISSONNAGE (le réseau ne vit qu'ici)
# ============================================================================================
def _telecharge(url: str, chemin: str, essais: int = 5, timeout: int = 120) -> None:
    for k in range(essais):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                brut = r.read()
            if brut.lstrip()[:9].lower() == b"<!doctype":
                raise OSError("la capture renvoie du HTML (page de challenge ?) : " + url)
            tmp = chemin + ".tmp"
            with open(tmp, "wb") as fh:
                fh.write(brut)
            os.replace(tmp, chemin)
            return
        except OSError:
            if k == essais - 1:
                raise
            time.sleep(4 * (k + 1))


def moissonne() -> None:
    os.makedirs(RAW, exist_ok=True)
    print("== MOISSONNAGE DARES×FAP (4 fichiers via Wayback, captures épinglées) ==")
    for nom, ts, url in SOURCES:
        chemin = os.path.join(RAW, nom)
        _telecharge(_WB % (ts, url), chemin)
        print("  %s (%.0f Ko)" % (nom, os.path.getsize(chemin) / 1e3))


# ============================================================================================
#  LES QUATRE MAILLONS
# ============================================================================================
def _exige(chemin: str) -> str:
    if not os.path.exists(chemin):
        raise SystemExit("cache absent : %s — lancer : python3 ingestion/ingere_dares_fap.py moissonne"
                         % chemin)
    return chemin


def _normalise(s: str) -> str:
    """Normalisation LOCALE pour comparer deux intitulés Dares (pas une clé du store) : minuscules,
    accents pliés, ponctuation -> espace."""
    s = s.lower().replace("œ", "oe").replace("’", "'")
    for accents, plat in (("àâä", "a"), ("éèêë", "e"), ("îï", "i"), ("ôö", "o"), ("ûüù", "u"), ("ç", "c")):
        s = re.sub("[" + accents + "]", plat, s)
    return re.sub(r"[^a-z0-9]+", " ", s).strip()


def passage_rsq() -> dict:
    """code ROME v3 -> code FAP-2009 fin, part DIRECTE ($FAP9RSQ) seulement. Le bloc s'arrête à son
    `Other = "ZZZZZ"` : la table $FAP9RAQ (affectation PAR QUALIFICATION, clés à 6 caractères) n'entre
    jamais ici — la qualification d'un métier n'est pas connaissable."""
    txt = open(_exige(C_PASSAGE), encoding="latin1").read()
    m = re.search(r"value\s+\$FAP9RSQ(.*?)Other", txt, re.S)
    if not m:
        raise ValueError("bloc $FAP9RSQ introuvable dans %s — format Dares changé, refus de deviner"
                         % C_PASSAGE)
    table = {}
    for codes, fap in re.findall(r'((?:"[A-Z]\d{4}"\s*,?\s*)+)=\s*"([A-Z]\d[A-Z]\d{2})"', m.group(1)):
        for c in re.findall(r'"([A-Z]\d{4})"', codes):
            table[c] = fap
    return table


def intitules_fap2009() -> dict:
    """code FAP-2009 fin (A0Z40) -> intitulé, depuis le fichier officiel des intitulés."""
    table = {}
    for r in lit_xlsx(_exige(C_INTITULES)):
        vals = list(r.values())
        for i, v in enumerate(vals):
            if re.fullmatch(r"[A-Z]\d[A-Z]\d{2}", (v or "").strip()) and i + 1 < len(vals):
                table[v.strip()] = (vals[i + 1] or "").strip()
    return table


def familles_fap2021() -> dict:
    """code ROME **V4** -> [intitulés des familles FAP-2021 qui le portent] (table Dares « version V4 »).
    Sert UNIQUEMENT de contre-affectation pour la garde de stabilité v3/v4."""
    table = collections.defaultdict(list)
    for r in lit_xlsx(_exige(C_FAP2021), feuille=2)[1:]:
        rome, lab = (r.get("C") or "").strip(), (r.get("B") or "").strip()
        if re.fullmatch(r"[A-Z]\d{4}", rome) and lab:
            table[rome].append(lab)
    return table


def medianes_fap(periode: str = PERIODE) -> dict:
    """code FAP-2009 fin -> médiane (€/mois, str du fichier) pour la période demandée. Le fichier du
    portail 2022 met CHAQUE LIGNE entière entre guillemets (guillemets internes doublés) : on déplie
    avant de découper. Une médiane non numérique ou hors 800..15000 €/mois fait TOUT échouer."""
    table = {}
    for ligne in open(_exige(C_SALAIRES), encoding="utf-8"):
        l = ligne.strip().strip('"').replace('""', '"')
        parts = [p.strip('"') for p in l.split(",")]
        if len(parts) < 3 or parts[0] == "Fap3" or parts[1] != periode:
            continue
        if not re.fullmatch(r"[A-Z]\d[A-Z]\d{2}", parts[0]):
            continue                                    # niveaux 22/87/ensemble : hors granularité fine
        med = float(parts[2])                           # ValueError = fichier corrompu, on NE publie PAS
        if not 800 <= med <= 15000:
            raise ValueError("médiane implausible %s €/mois pour %s — fichier suspect, refus de publier"
                             % (parts[2], parts[0]))
        table[parts[0]] = parts[2]
    return table


def _rome_du_store() -> dict:
    """metier -> code ROME v4 (`code_rome_metier`, gardes d'unicité amont — cf. ingere_rome_rncp)."""
    dossier = os.environ.get("LECTEUR_DATASETS_DIR",
                             os.path.join(os.path.expanduser("~"), ".verax", "datasets", "lecteur"))
    chemin = os.path.join(dossier, "code_rome_metier.jsonl")
    if not os.path.exists(chemin):
        raise SystemExit("table `code_rome_metier` absente du store — lancer d'abord ingere_rome_rncp.py")
    table = {}
    with open(chemin, encoding="utf-8") as fh:
        for ligne in fh:
            if ligne.startswith('{"_relation"'):
                continue
            o = json.loads(ligne)
            m = re.search(r"[A-Z]\d{4}", o["valeur"])
            if m:
                table[o["entite"]] = m.group(0)
    return table


def stable_v3_v4(intitule_2009: str, intitules_2021: list) -> bool:
    """La garde de stabilité : le code est stable si l'intitulé de sa famille FAP-2009 se retrouve dans
    l'une de ses familles FAP-2021 (égalité normalisée, ou inclusion d'un intitulé dans l'autre —
    « Aides-soignants » ⊂ « Aides-soignants et professions assimilées »). Intitulé vide = jamais stable."""
    n9 = _normalise(intitule_2009)
    if not n9:
        return False
    for lab in intitules_2021:
        n21 = _normalise(lab)
        if n9 == n21 or n9 in n21 or n21 in n9:
            return True
    return False


def valeur_fap(fap: str, intitule: str, rome: str, mediane: str) -> str:
    """La valeur publiée : granularité DITE (médiane de la FAMILLE, pas du métier), période et champ dits."""
    return ("famille professionnelle FAP-2009 %s « %s » (affectation Dares du code ROME %s, stable entre "
            "FAP-2009 et FAP-2021) ; salaire mensuel net MÉDIAN de la famille, France, période %s : "
            "%s €/mois (Dares, Portraits statistiques des métiers, d'après l'enquête Emploi Insee ; champ "
            "de la série : salariés à temps complet hors apprentis et stagiaires ; médiane PAR FAMILLE de "
            "métiers, pas par métier précis)" % (fap, intitule, rome, PERIODE, mediane))


def publie_depuis_cache() -> None:
    print("== DARES×FAP — axe « rémunération médiane » (part France, MIX) ==")
    rsq = passage_rsq()
    labs = intitules_fap2009()
    f21 = familles_fap2021()
    med = medianes_fap()
    if len(rsq) < 300 or len(labs) != 225 or len(f21) < 500 or len(med) < 200:
        raise ValueError("maillon tronqué : %d codes RSQ, %d intitulés FAP-2009 (attendu 225), %d codes "
                         "ROME V4, %d médianes %s — refus de publier"
                         % (len(rsq), len(labs), len(f21), len(med), PERIODE))
    print("  maillons : %d codes ROME v3 directs · %d intitulés · %d codes V4 contre-affectés · "
          "%d médianes %s" % (len(rsq), len(labs), len(f21), len(med), PERIODE))

    rome_m = _rome_du_store()
    print("  univers : %d métiers de la carte avec code ROME" % len(rome_m))

    paires, ecartes = [], collections.Counter()
    for metier, code in sorted(rome_m.items()):
        fap = rsq.get(code)
        if not fap:
            ecartes["affectation par qualification ($FAP9RAQ) ou code absent de la table v3"] += 1
            continue
        if fap not in med:
            ecartes["pas de médiane %s publiée pour la famille" % PERIODE] += 1
            continue
        intitule = labs.get(fap, "")
        if code not in f21 or not stable_v3_v4(intitule, f21[code]):
            ecartes["famille instable entre FAP-2009 et FAP-2021 (couture v3/v4 non certifiable)"] += 1
            continue
        paires.append((metier, valeur_fap(fap, intitule, code, med[fap])))
    for raison, n in ecartes.most_common():
        print("  écartés — %s : %d" % (raison, n))
    if len(paires) < 100:
        raise ValueError("chaîne suspecte : %d métiers seulement — maillons à réauditer" % len(paires))
    print("  métiers publiés : %d" % len(paires))
    publie("salaire_median_fap_fr_metier", "convention", SRC, paires)


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "publie"
    if mode == "moissonne":
        moissonne()
    elif mode == "publie":
        publie_depuis_cache()
    else:
        raise SystemExit("usage : ingere_dares_fap.py [moissonne|publie]")
