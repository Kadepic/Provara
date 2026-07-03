"""
EXTRACTION DEPUIS SOURCES SALES (texte -> triplets) — brique Vague 8. La veille sans injecter de faux.

POURQUOI : la veille lit du TEXTE (articles, brevets). En tirer des faits (sujet, relation, objet) est indispensable,
mais c'est le point où le faux entre le plus facilement. Discipline : extraction DÉTERMINISTE par motifs exacts, chaque
candidat avec une CONFIANCE et une PROVENANCE ; on n'ASSERTE que le sûr, le reste reste CANDIDAT (jamais injecté seul).

MODÈLE : une liste de motifs (regex français) -> (relation, ordre des groupes, confiance). `extrait(texte)` renvoie
tous les candidats (triplet, confiance, motif) ; `extrait_surs(texte, seuil)` ne garde que le haut de confiance.

FAUX=0 :
  • Aucune extraction hors motif : une phrase qui ne matche aucun motif -> RIEN (abstention, pas de triplet deviné).
  • Chaque candidat porte sa confiance ET la provenance (le motif + le texte source) -> traçable, filtrable.
  • `extrait_surs` n'asserte QUE ce qui dépasse le seuil ; le reste demeure candidat, à corroborer ailleurs (ancres).
Stdlib pur (re), déterministe, souverain.
"""
from __future__ import annotations

import re

# Chaque motif : (regex, relation, (idx_sujet, idx_objet) parmi les groupes, confiance). Motifs FR exacts.
_MOTIFS = [
    (re.compile(r"^(.+?) est la capitale (?:de la |de l'|de l’|des |du |de |d'|d’)(.+?)\.?$", re.I), "capitale", (2, 1), 0.95),
    (re.compile(r"^(.+?) a été inventé(?:e)? par (.+?)\.?$", re.I), "inventeur", (1, 2), 0.9),
    (re.compile(r"^(.+?) a été découvert(?:e)? par (.+?)\.?$", re.I), "decouvreur", (1, 2), 0.9),
    (re.compile(r"^(.+?) est né(?:e)? (?:à|en) (.+?)\.?$", re.I), "lieu_naissance", (1, 2), 0.85),
    (re.compile(r"^(.+?) est un(?:e)? (.+?)\.?$", re.I), "est_un", (1, 2), 0.7),
]


def extrait(texte: str, source: str = "texte"):
    """Tous les triplets CANDIDATS d'un texte : liste de dicts {triplet:(sujet,relation,objet), confiance, motif,
    source}. Une phrase par ligne ou séparée par points. Aucune extraction hors motif (abstention)."""
    out = []
    phrases = re.split(r"(?<=\.)\s+|\n+", texte.strip())
    for ph in phrases:
        ph = ph.strip()
        if not ph:
            continue
        for regex, relation, (isuj, iobj), conf in _MOTIFS:
            m = regex.match(ph)
            if m:
                sujet = m.group(isuj).strip()
                objet = m.group(iobj).strip()
                out.append({"triplet": (sujet, relation, objet), "confiance": conf,
                            "motif": relation, "source": source})
                break                            # un motif par phrase (le plus spécifique d'abord)
    return out


def extrait_surs(texte: str, seuil: float = 0.9, source: str = "texte"):
    """Seulement les triplets dont la confiance ≥ seuil (assertables) ; le reste reste candidat, non retourné ici."""
    return [c for c in extrait(texte, source) if c["confiance"] >= seuil]
