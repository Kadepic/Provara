"""
INGESTION LANGUES — langue -> « bonjour » et langue -> « merci »  (OFFLINE).

SOURCE : lexique multilingue de référence. Faits STABLES et CERTAINS (formes standard).
FAUX=0 : forme standard NON CONTESTÉE (transcription latine usuelle). langue -> UNE forme = fonctionnel.
"""
from __future__ import annotations
from ingere_wikidata import publie

# (langue, bonjour, merci)
_LANGUES = [
    ("anglais", "hello", "thank you"),
    ("espagnol", "hola", "gracias"),
    ("italien", "buongiorno", "grazie"),
    ("allemand", "guten Tag", "danke"),
    ("portugais", "olá", "obrigado"),
    ("néerlandais", "hallo", "dank je"),
    ("japonais", "konnichiwa", "arigato"),
    ("chinois", "ni hao", "xie xie"),
    ("russe", "zdravstvouïtié", "spassiba"),
    ("arabe", "marhaba", "choukran"),
    ("hindi", "namaste", "dhanyavad"),
    ("grec", "yassou", "efcharisto"),
    ("turc", "merhaba", "teşekkür"),
    ("polonais", "dzień dobry", "dziękuję"),
    ("suédois", "hej", "tack"),
    ("hawaïen", "aloha", "mahalo"),
    ("coréen", "annyeong", "kamsahamnida"),
    ("swahili", "jambo", "asante"),
]

def ingere():
    print(f"== SALUTATIONS — bonjour + merci par langue ({len(_LANGUES)}) ==")
    publie("bonjour_langue", "convention", "lexique multilingue (langue -> bonjour)",
           [(lg, b) for lg, b, _ in _LANGUES])
    publie("merci_langue", "convention", "lexique multilingue (langue -> merci)",
           [(lg, m) for lg, _, m in _LANGUES])

if __name__ == "__main__":
    ingere()
