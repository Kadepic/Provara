"""
INGESTION SIGLES — sigle/acronyme -> signification  -> datasets/lecteur/signification_sigle.jsonl (OFFLINE).

SOURCE : nomenclatures officielles de référence. Faits STABLES et CERTAINS (développements officiels).

FAUX=0 — discipline : développements OFFICIELS non contestés. Acronymes étrangers gardés dans leur langue
officielle (NASA = anglais). sigle -> UNE signification = fonctionnel. Clés = sigles (normalisés au load).

Usage : python3 ingere_sigles.py    (puis non-reg OFFLINE).
"""
from __future__ import annotations

from ingere_wikidata import publie

_SIGLES = [
    ("ONU", "Organisation des Nations Unies"),
    ("OTAN", "Organisation du traité de l'Atlantique Nord"),
    ("UE", "Union européenne"),
    ("OMS", "Organisation mondiale de la santé"),
    ("FMI", "Fonds monétaire international"),
    ("OMC", "Organisation mondiale du commerce"),
    ("UNESCO", "United Nations Educational, Scientific and Cultural Organization"),
    ("UNICEF", "United Nations International Children's Emergency Fund"),
    ("NASA", "National Aeronautics and Space Administration"),
    ("ADN", "acide désoxyribonucléique"),
    ("ARN", "acide ribonucléique"),
    ("PIB", "produit intérieur brut"),
    ("TVA", "taxe sur la valeur ajoutée"),
    ("SIDA", "syndrome d'immunodéficience acquise"),
    ("OVNI", "objet volant non identifié"),
    ("GPS", "Global Positioning System"),
    ("HTML", "HyperText Markup Language"),
    ("PDF", "Portable Document Format"),
    ("USB", "Universal Serial Bus"),
    ("CPU", "Central Processing Unit"),
    ("RAM", "Random Access Memory"),
    ("LASER", "Light Amplification by Stimulated Emission of Radiation"),
    ("RADAR", "Radio Detection And Ranging"),
    ("SMIC", "salaire minimum interprofessionnel de croissance"),
    ("RATP", "Régie autonome des transports parisiens"),
    ("SNCF", "Société nationale des chemins de fer français"),
    ("CERN", "Conseil européen pour la recherche nucléaire"),
    ("BCE", "Banque centrale européenne"),
    ("PME", "petite et moyenne entreprise"),
    ("QI", "quotient intellectuel"),
]

SRC = "nomenclatures officielles de référence (sigle -> signification)"


def ingere():
    print(f"== SIGLES — sigle -> signification ({len(_SIGLES)}) ==")
    publie("signification_sigle", "convention", SRC, _SIGLES)


if __name__ == "__main__":
    ingere()
