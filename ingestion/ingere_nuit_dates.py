"""Ingestion NUIT 2026-06-29 : année de NAISSANCE (P569) et de DÉCÈS (P570) des personnes (Q5).
Veine FONCTIONNELLE massive non encore faite (lieu P19/P20 l'était, pas la DATE). Streaming TSV (O(1) mémoire
transport) + extraction d'année via ingere_t8._annee (vérifiée sur Einstein/Napoléon/Platon…). FAUX=0 : la clé
est le LIBELLÉ normalisé -> les homonymes (même nom, années différentes) partent en HORS via `fonctionnel` de
publie ; une personne à dates multiples divergentes -> HORS aussi. categorie=passe (fait historique daté)."""
import os
os.environ.setdefault("LECTEUR_AMORCE_SEULE", "1")
import sys

import ingere_qlever as IQ
import ingere_t6 as T6   # _stream_paires_tsv (transport massif streamé)
import ingere_t8 as T8   # _annee (extraction d'année, signe BCE conservé)


def ingere_date(relation, prop, source, classe_qid="Q5", lo=-4000, hi=2026, sous_classes=False):
    if classe_qid:
        chemin = "wdt:P31/wdt:P279*" if sous_classes else "wdt:P31"
        filtre = f"?e {chemin} wd:{classe_qid} ; wdt:{prop} ?v ."
    else:
        filtre = f"?e wdt:{prop} ?v ."
    q = f"""SELECT ?eLabel ?v WHERE {{
      {filtre}
      ?e rdfs:label ?eLabel . FILTER(lang(?eLabel)="fr")
    }}"""
    print(f"== {relation} (Wikidata/QLever {prop}, classe={classe_qid}, TSV streamé) ==", flush=True)
    paires, brut, sans_annee, hors_plage = [], 0, 0, 0
    for e, d in T6._stream_paires_tsv(q, timeout=3000):
        brut += 1
        an = T8._annee(d)
        if an is None:
            sans_annee += 1
            continue
        try:
            y = int(an)
        except ValueError:
            sans_annee += 1
            continue
        if not (lo <= y <= hi):        # plage plausible : hors = erreur Wikidata / mistypé -> REJET (FAUX=0)
            hors_plage += 1
            continue
        paires.append((e, an))
    print(f"  {brut} brutes -> {len(paires)} paires ; {sans_annee} sans année, "
          f"{hors_plage} hors plage [{lo},{hi}] rejetées.", flush=True)
    IQ.publie(relation, "passe", source, paires)


# Registre des veines DATE (extensible) : nom -> (relation, prop, source, classe_qid, an_min, an_max, sous_classes)
_CIBLES = {
    "naissance": ("annee_naissance_personne", "P569",
                  "Wikidata/QLever — année de naissance P569 (humains ; homonymes/dates divergentes -> HORS)",
                  "Q5", -4000, 2026, False),
    "deces": ("annee_deces_personne", "P570",
              "Wikidata/QLever — année de décès P570 (humains ; homonymes/dates divergentes -> HORS)",
              "Q5", -4000, 2026, False),
    "publication": ("annee_publication_oeuvre", "P577",
                    "Wikidata/QLever — année de publication P577 (œuvres fr ; multi-date/homonymes -> HORS)",
                    None, -3000, 2026, False),
    "construction": ("annee_construction_edifice", "P571",
                     "Wikidata/QLever — année de construction/inception P571 (structures Q811979 ; multi/homonymes -> HORS)",
                     "Q811979", -4000, 2026, True),
    "ouverture": ("annee_ouverture_edifice", "P1619",
                  "Wikidata/QLever — année d'ouverture officielle P1619 (structures Q811979 ; multi/homonymes -> HORS)",
                  "Q811979", -4000, 2026, True),
    "astre": ("annee_decouverte_astre", "P575",
              "Wikidata/QLever — année de découverte P575 (planètes mineures Q3863 ; multi/homonymes -> HORS)",
              "Q3863", -4000, 2026, False),
    "art": ("annee_creation_oeuvre_art", "P571",
            "Wikidata/QLever — année de création P571 (œuvres d'art Q838948 ; multi/homonymes -> HORS)",
            "Q838948", -4000, 2026, True),
    "logiciel": ("annee_creation_logiciel", "P571",
                 "Wikidata/QLever — année de création P571 (logiciels Q7397 ; multi/homonymes -> HORS)",
                 "Q7397", -4000, 2026, True),
}

if __name__ == "__main__":
    cibles = sys.argv[1:] or ["naissance", "deces"]
    if "both" in cibles:
        cibles = ["naissance", "deces"]
    for c in cibles:
        if c not in _CIBLES:
            print(f"cible inconnue : {c} (dispo : {list(_CIBLES)})", flush=True)
            continue
        rel, prop, src, cls, lo, hi, sc = _CIBLES[c]
        ingere_date(rel, prop, src, classe_qid=cls, lo=lo, hi=hi, sous_classes=sc)
    print("FINI.", flush=True)
