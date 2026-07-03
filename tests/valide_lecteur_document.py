# -*- coding: utf-8 -*-
"""VALIDE lecteur_document : interroger un long document, FAUX=0.

On fabrique un document multi-pages / multi-sections, on l'interroge, et on vérifie : passage VERBATIM correct,
page RÉELLE, section rattachée, sommaire des titres, abstention honnête sur un sujet absent, round-trip PDF."""
from __future__ import annotations

import os
import sys

_ICI = os.path.dirname(os.path.abspath(__file__)) or "."
sys.path.insert(0, os.path.join(os.path.dirname(_ICI), "src"))

os.environ.setdefault("LECTEUR_AMORCE_SEULE", "1")

import lecteur_document as LD

ok = ko = 0


def check(c, label):
    global ok, ko
    if c:
        ok += 1
    else:
        ko += 1
        print("  FAIL: " + label)


# — Document fabriqué : 3 pages, sections détectables, paragraphes distincts —
pages = [
    # page 1
    "Introduction\n"
    "Ce mémoire porte sur la sobriété énergétique des bâtiments tertiaires.\n"
    "\n"
    "1. Contexte\n"
    "La consommation de chauffage représente la part dominante des dépenses.",
    # page 2
    "2. Méthodologie\n"
    "Nous avons instrumenté douze bâtiments avec des capteurs de température.\n"
    "\n"
    "Les mesures ont été relevées toutes les quinze minutes pendant un an.",
    # page 3
    "3. Résultats\n"
    "L'isolation des combles réduit la facture de chauffage de quarante-trois pour cent.\n"
    "\n"
    "CONCLUSION\n"
    "La rénovation thermique est rentable en moins de sept ans.",
]
doc = LD.Document(pages, titre_document="Mémoire sobriété")

check(doc.n >= 6, "document découpé en plusieurs passages (%d)" % doc.n)

# (1) interrogation -> bon passage, bonne page
r = doc.repond("quel est le pourcentage de réduction de la facture de chauffage ?")
check(r is not None and "quarante-trois" in r["reponse"], "trouve le passage des résultats VERBATIM")
check(r is not None and r["page"] == 3, "attribue la BONNE page (3)")
check(r is not None and r["section"] and "Résultats" in r["section"], "rattache la section « Résultats »")

# (2) autre requête -> autre page
r = doc.repond("comment les bâtiments ont-ils été instrumentés ?")
check(r is not None and "capteurs" in r["reponse"] and r["page"] == 2, "méthodologie -> page 2, capteurs")

# (3) requête sur la conclusion
r = doc.repond("la rénovation est-elle rentable ?")
check(r is not None and "sept ans" in r["reponse"], "conclusion retrouvée")

# (4) sujet ABSENT -> abstention honnête (pas d'invention)
r = doc.repond("quelle est la vitesse de la lumière dans le vide ?")
check(r is None, "sujet absent du document -> None (aucune invention)")

# (5) interroge renvoie plusieurs passages classés
hits = doc.interroge("chauffage", k=3)
check(len(hits) >= 2, "un terme fréquent renvoie plusieurs passages")
check(all("texte" in h and "page" in h for h in hits), "chaque hit porte texte + page")
check(hits == sorted(hits, key=lambda h: -h["score"]), "passages classés par score décroissant")

# (6) sommaire = titres détectés dans l'ordre avec page
som = doc.sommaire()
titres = [s["titre"] for s in som]
check(any("Introduction" in t for t in titres), "sommaire : Introduction détectée")
check(any(t.startswith("2.") for t in titres), "sommaire : titre numéroté « 2. Méthodologie »")
check(any("CONCLUSION" in t for t in titres), "sommaire : CONCLUSION (capitales) détectée")
check([s["page"] for s in som] == sorted(s["page"] for s in som), "sommaire ordonné par page")

# (7) infos cohérentes
inf = doc.infos()
check(inf["pages"] == 3 and inf["passages"] == doc.n, "infos : 3 pages, passages comptés")

# (8) round-trip PDF : écrire un PDF puis le lire comme document
import document_pdf as DP
d = DP.Document()
p = d.page(); p.texte(72, 800, "Chapitre 1", taille=14); p.texte(72, 770, "Le budget alloue trois millions d'euros.", taille=12)
p2 = d.page(); p2.texte(72, 800, "Chapitre 2", taille=14); p2.texte(72, 770, "Le calendrier prevoit une livraison en juin.", taille=12)
docpdf = LD.depuis_pdf(DP.encode(d))
r = docpdf.repond("quel est le budget alloué ?")
check(r is not None and "trois millions" in r["reponse"] and r["page"] == 1, "PDF -> question budget -> page 1")
r = docpdf.repond("quand est prévue la livraison ?")
check(r is not None and "juin" in r["reponse"] and r["page"] == 2, "PDF -> question livraison -> page 2")

# (9) document vide -> pas de crash, abstention
vide = LD.Document([""])
check(vide.interroge("quoi que ce soit") == [], "document vide -> aucune réponse (robuste)")

print("=== valide_lecteur_document : %d/%d ===" % (ok, ok + ko))
sys.exit(0 if ko == 0 else 1)
