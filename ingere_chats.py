"""
INGESTION FÉLINOLOGIE — race de chat -> pays d'origine  -> datasets/lecteur/pays_race_chat.jsonl (OFFLINE).

SOURCE : standards félins de référence. Faits STABLES et CERTAINS pour les origines NON CONTESTÉES.
FAUX=0 : on ÉCARTE les origines disputées (abyssin). Fonctionnel. Clés FR minuscules.
"""
from __future__ import annotations
from ingere_wikidata import publie

_PAR_PAYS = {
    "Thaïlande": ["siamois", "korat"],
    "Iran": ["persan"],
    "États-Unis": ["maine coon", "bengal", "ragdoll"],
    "France": ["chartreux"],
    "Canada": ["sphynx"],
    "Royaume-Uni": ["british shorthair"],
    "Russie": ["sibérien", "bleu russe"],
    "Turquie": ["angora turc", "van turc"],
    "Birmanie": ["sacré de birmanie"],
    "Norvège": ["norvégien"],
    "Somalie": ["somali"],
    "Singapour": ["singapura"],
}

def ingere():
    paires = [(r, p) for p, races in _PAR_PAYS.items() for r in races]
    print(f"== RACES DE CHATS -> PAYS ({len(paires)}) ==")
    publie("pays_race_chat", "convention", "félinologie de référence (race -> pays d'origine)", paires)

if __name__ == "__main__":
    ingere()
