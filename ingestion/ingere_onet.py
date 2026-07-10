"""
INGESTION O*NET — l'axe « outils, machines et logiciels » s'ouvre par sa part CODIFIÉE US (mandat « traiter
tout le backlog », 2026-07-12). L'axe était à « aucun » depuis le rejet de P2283 (« soliste -> solo ») ;
la carte notait déjà « source réelle = ESCO/ROME » — c'est finalement O*NET, ESCO ne typant pas ses
compétences en « outil ».

LA SOURCE. O*NET 30.0 (US Department of Labor, licence CC BY 4.0) : fichiers « Tools Used » (41 662 lignes)
et « Technology Skills » (32 681) par occupation O*NET-SOC. NOTE DE VERSION : la 30.3 ne porte PLUS ces
fichiers (T2 sorti du produit principal) — on épingle db_30_0, dernière version du produit complet.
Le code O*NET-SOC « xx-xxxx.yy » se tronque à « xx-xxxx » = SOC 2018 (taxonomie O*NET-SOC 2019 = SOC 2018
détaillé, correspondance documentée par l'O*NET Center).

LA CHAÎNE — la même que `ingere_bls_oes` (maillons RÉUTILISÉS, pas recopiés) :
  métier -> groupe ISCO-08 (ESCO, store) -> SOC 2010 (crosswalk BLS) -> SOC 2018 (crosswalk BLS/SOCPC)
  -> catégories d'outils et technologies O*NET.

CE QUE LA TABLE AFFIRME : les CATÉGORIES UNSPSC (champ « Commodity Title ») recensées par O*NET pour les
occupations SOC associées au GROUPE ISCO du métier — granularité dite, dédoublonnage à l'échelle du groupe,
liste EXHAUSTIVE à cette granularité (jamais un top-N). On publie la CATÉGORIE (« Desktop calculator »)
et non chaque exemple commercial (« 10-key calculators ») : le niveau catégorie est complet et stable là
où les exemples sont une liste ouverte de marques — publier un niveau COMPLET plutôt qu'un extrait d'un
niveau plus fin, c'est le même choix que geste_metier (part codifiée).

Le sujet reste MIX -> PARTIEL, jamais TRAITÉ : O*NET codifie l'outillage du marché du travail AMÉRICAIN
contemporain ; l'outillage réel d'un métier n'est borné par aucun référentiel unique.

CACHE : `datasets/_raw/onet_tools_used.xlsx` + `onet_technology_skills.xlsx` (stdlib pur en lecture).

Usage :
    python3 ingestion/ingere_onet.py moissonne     # 2 fichiers O*NET (~2,3 Mo)
    python3 ingestion/ingere_onet.py publie        # hors ligne, depuis le cache
"""
from __future__ import annotations

import collections
import os
import re
import sys

from ingere_bls_oes import (RAW, _isco_du_store, _telecharge, isco_vers_soc2010, lit_xlsx,
                            soc2010_vers_2018)
from ingere_wikidata import publie

URL_OUTILS = "https://www.onetcenter.org/dl_files/database/db_30_0_excel/Tools%20Used.xlsx"
URL_TECHS = "https://www.onetcenter.org/dl_files/database/db_30_0_excel/Technology%20Skills.xlsx"
CACHE_OUTILS = os.path.join(RAW, "onet_tools_used.xlsx")
CACHE_TECHS = os.path.join(RAW, "onet_technology_skills.xlsx")

SRC = ("O*NET 30.0 (US Department of Labor, CC BY 4.0 — db_30_0 épinglé : la 30.3 ne porte plus Tools "
       "Used/Technology Skills) × crosswalks BLS (ISCO-08→SOC 2010→SOC 2018) × `code_isco_metier` (ESCO). "
       "La valeur affirme : le métier relève du groupe ISCO-08 indiqué ; les catégories listées (UNSPSC, "
       "« Commodity Title ») sont celles qu'O*NET recense pour les occupations SOC de ce GROUPE (pas le "
       "métier précis — granularité dite). Dédoublonnées, triées, EXHAUSTIVES à cette granularité ; le "
       "niveau catégorie est publié parce qu'il est COMPLET, là où les exemples commerciaux sont une liste "
       "ouverte. Part CODIFIÉE US seulement : le sujet reste MIX.")


def moissonne() -> None:
    os.makedirs(RAW, exist_ok=True)
    print("== MOISSONNAGE O*NET 30.0 (Tools Used + Technology Skills) ==")
    for url, chemin in ((URL_OUTILS, CACHE_OUTILS), (URL_TECHS, CACHE_TECHS)):
        _telecharge(url, chemin)
        print("  %s (%.0f Ko)" % (os.path.basename(chemin), os.path.getsize(chemin) / 1e3))


def _exige(chemin: str) -> str:
    if not os.path.exists(chemin):
        raise SystemExit("cache absent : %s — lancer : python3 ingestion/ingere_onet.py moissonne" % chemin)
    return chemin


def categories_par_soc(chemin: str) -> dict:
    """code SOC 2018 (6 chiffres, tronqué de l'O*NET-SOC 8 chiffres) -> {catégories UNSPSC}. Les lignes
    dont le code ne se tronque pas en « xx-xxxx » ou sans catégorie tombent — jamais devinées."""
    lignes = lit_xlsx(_exige(chemin))
    col = {v: k for k, v in lignes[0].items()}
    if "O*NET-SOC Code" not in col or "Commodity Title" not in col:
        raise SystemExit("colonnes attendues absentes de %s — le format O*NET a changé" % chemin)
    table = collections.defaultdict(set)
    for r in lignes[1:]:
        code = (r.get(col["O*NET-SOC Code"]) or "")[:7]
        cat = (r.get(col["Commodity Title"]) or "").strip()
        if re.fullmatch(r"\d{2}-\d{4}", code) and cat:
            table[code].add(cat)
    return table


def valeur_onet(groupe: str, socs: list, outils: dict, techs: dict):
    """La valeur du métier, ou None si AUCUNE occupation du groupe n'est recensée par O*NET."""
    o = sorted(set().union(*[outils.get(s, set()) for s in socs])) if socs else []
    t = sorted(set().union(*[techs.get(s, set()) for s in socs])) if socs else []
    if not o and not t:
        return None
    tete = ("groupe ISCO-08 %s ; catégories d'outils et de technologies recensées par O*NET 30.0 (US DOL, "
            "CC BY 4.0) pour les occupations SOC 2018 que les crosswalks BLS associent à ce groupe "
            "(granularité : occupation SOC, catégories UNSPSC dédoublonnées — pas le métier précis)"
            % groupe)
    parts = []
    if o:
        parts.append("OUTILS : %s" % " ; ".join(o))
    if t:
        parts.append("TECHNOLOGIES : %s" % " ; ".join(t))
    return "%s — %s" % (tete, " — ".join(parts))


def publie_depuis_cache() -> None:
    print("== O*NET — axe « outils, machines et logiciels » (part codifiée US, MIX) ==")
    outils = categories_par_soc(CACHE_OUTILS)
    techs = categories_par_soc(CACHE_TECHS)
    if len(outils) < 600 or len(techs) < 600:
        raise ValueError("O*NET tronqué : %d SOC avec outils, %d avec technologies — refus de publier"
                         % (len(outils), len(techs)))
    print("  O*NET : %d SOC avec outils · %d avec technologies" % (len(outils), len(techs)))

    i2s, s18, isco = isco_vers_soc2010(), soc2010_vers_2018(), _isco_du_store()
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "outils"))
    from genere_sujets import metiers_de_la_carte
    metiers, _, _ = metiers_de_la_carte()

    paires, sans = [], 0
    for m in metiers:
        g = isco.get(m)
        if not g:
            continue
        socs = sorted({b for a in i2s.get(g, ()) for b in s18.get(a, ())})
        v = valeur_onet(g, socs, outils, techs)
        if v is None:
            sans += 1
            continue
        paires.append((m, v))
    if len(paires) < 300:
        raise ValueError("chaîne suspecte : %d métiers seulement — maillons à réauditer" % len(paires))
    print("  métiers publiés : %d | groupe sans recensement O*NET (restent non traités) : %d"
          % (len(paires), sans))
    publie("outil_technologie_soc_metier", "convention", SRC, sorted(paires))


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "publie"
    if mode == "moissonne":
        moissonne()
    elif mode == "publie":
        publie_depuis_cache()
    else:
        raise SystemExit("usage : ingere_onet.py [moissonne|publie]")
