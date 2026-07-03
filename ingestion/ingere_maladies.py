"""
INGESTION SANTÉ — maladie -> type d'agent pathogène  -> datasets/lecteur/agent_maladie.jsonl (OFFLINE).

SOURCE : microbiologie/médecine de référence. Faits STABLES et CERTAINS (agent causal établi).

FAUX=0 — discipline : UNIQUEMENT les maladies à agent NON CONTESTÉ. Valeurs ∈ {virus, bactérie,
parasite, champignon}. maladie -> UN type d'agent = fonctionnel. Clés = noms FR minuscules.

Usage : python3 ingere_maladies.py    (puis non-reg OFFLINE).
"""
from __future__ import annotations

from ingere_wikidata import publie

_PAR_AGENT = {
    "virus": ["grippe", "rage", "rougeole", "varicelle", "oreillons", "hépatite b", "covid-19",
              "sida", "ebola", "dengue", "poliomyélite", "variole", "herpès", "zona"],
    "bactérie": ["tuberculose", "choléra", "tétanos", "peste", "syphilis", "salmonellose",
                 "diphtérie", "coqueluche", "lèpre", "botulisme", "angine bactérienne"],
    "parasite": ["paludisme", "toxoplasmose", "leishmaniose", "amibiase", "gale", "téniase"],
    "champignon": ["candidose", "teigne", "mycose", "aspergillose"],
}

SRC = "microbiologie de référence (maladie -> type d'agent pathogène)"


def ingere():
    paires = [(m, ag) for ag, mals in _PAR_AGENT.items() for m in mals]
    print(f"== MALADIES — maladie -> agent ({len(paires)}) ==")
    publie("agent_maladie", "convention", SRC, paires)


if __name__ == "__main__":
    ingere()
