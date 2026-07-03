# -*- coding: utf-8 -*-
"""LECTEUR DE DOCUMENT LONG — interroger un texte de plusieurs centaines de pages, FAUX=0 (2026-07-03).

POURQUOI (mandat Yohan « l'IA doit lire et comprendre un mémoire de 200 pages ») : lire un long document, ce
n'est pas le paraphraser — c'est RETROUVER le passage exact qui répond à une question. Ce module découpe un
document (pages -> sections -> passages), construit un INDEX INVERSÉ pondéré idf (même principe que le rappel
de conversations, réutilisé via `conversation._tokens`), et répond à « que dit le document sur X ? » par le
PASSAGE VERBATIM + son numéro de page + le titre de section. Il propose aussi un SOMMAIRE (titres détectés).

FAUX=0 — ce que ce module GARANTIT et ce qu'il ne prétend PAS :
  • Il ne rend QUE des passages LITTÉRAUX du document, avec leur page RÉELLE — jamais une synthèse inventée,
    jamais une « réponse » fabriquée. Aucun passage pertinent -> il le DIT (liste vide), pas d'à-peu-près.
  • Le sommaire = titres réellement présents (heuristique conservatrice) ; il n'invente pas de structure.
  • Souverain, offline, stdlib pur, déterministe. Model-free (index idf + heuristiques bornées).
"""
from __future__ import annotations

import math
import re

from conversation import _tokens, _MOTS_VIDES, normalise   # tokenisation DISCRIMINANTE partagée

# Les mots-vides de conversation.py sont ACCENTUÉS (« été », « où ») mais les tokens sont dé-accentués
# (« ete », « ou ») -> ces mots-outils FUYAIENT dans l'index (« été » parasitait le classement). On re-filtre
# ici sur un ensemble DÉ-ACCENTUÉ + les mots interrogatifs (échafaudage de question, non discriminants pour la
# recherche documentaire — même principe que veille_structure._WIKI_STOP). (Note : la fuite existe aussi dans le
# rappel de conversations ; corrigé localement pour ne pas toucher les gates de conversation.py.)
_STOP_DOC = ({normalise(w) for w in _MOTS_VIDES} |
             set("comment pourquoi quand combien quel quelle quels quelles lequel laquelle lesquels lesquelles "
                 "ils elle elles etre avoir cela ceci dont".split()))


def _racine(t: str) -> str:
    """Racinisation CONSERVATRICE pour l'APPARIEMENT (pas d'affichage) : neutralise le pluriel régulier FR
    (chute du « s »/« x » final) pour que « bâtiments » == « bâtiment » et « instrumentés » == « instrumenté ».
    Appliquée identiquement au document ET à la question -> n'invente rien, améliore seulement le rappel."""
    if len(t) > 3 and t[-1] in "sx":
        return t[:-1]
    return t


def _toks_doc(texte: str):
    """Tokens discriminants racinisés pour un DOCUMENT : conversation._tokens, moins les mots-outils dé-accentués
    et les interrogatifs (qui fuyaient), puis racine de pluriel. Sert aux CLÉS d'index et de requête uniquement ;
    le texte rendu reste toujours le passage VERBATIM d'origine."""
    return [_racine(t) for t in _tokens(texte) if t not in _STOP_DOC]

# — Détection de TITRE de section (heuristique bornée, conservatrice) —
_NUM_TITRE = re.compile(r"^\s*(?:\d+(?:[.)]\d+)*[.)]?)\s+\S")          # « 1. », « 2.3 Titre », « 4) »
_MOT_TITRE = re.compile(
    r"^\s*(chapitre|partie|section|annexe|titre|livre|sommaire|introduction|conclusion|"
    r"bibliographie|r[ée]sum[ée]|abstract|remerciements|table des mati[èe]res|avant[- ]propos|"
    r"pr[ée]ambule|glossaire|index|appendice)\b", re.I)


def _est_titre(ligne: str) -> bool:
    """Une ligne est un TITRE si elle est courte ET (numérotée façon plan / mot-clé de section / capitales)."""
    s = ligne.strip()
    if not s or len(s) > 90:
        return False
    if _MOT_TITRE.match(s) or _NUM_TITRE.match(s):
        return True
    lettres = [c for c in s if c.isalpha()]
    # ligne courte, majoritairement en CAPITALES, pas terminée par une ponctuation de phrase -> titre
    if 3 <= len(lettres) <= 60 and sum(c.isupper() for c in lettres) / len(lettres) > 0.7 and s[-1] not in ".!?,;:":
        return True
    return False


def _passages_d_une_page(texte_page: str):
    """Découpe le texte d'une page en (titre_courant, passage). Un passage = un paragraphe (bloc de lignes
    séparé par une ligne vide, ou une ligne isolée). Les titres sont retenus et rattachés aux passages suivants."""
    lignes = texte_page.split("\n")
    titre = None
    buf = []
    out = []

    def vide():
        nonlocal buf
        if buf:
            passage = " ".join(l.strip() for l in buf if l.strip()).strip()
            if passage:
                out.append((titre, passage))
        buf = []

    for ligne in lignes:
        if not ligne.strip():
            vide(); continue
        if _est_titre(ligne):
            vide(); titre = ligne.strip(); continue
        buf.append(ligne)
    vide()
    return out


class Document:
    """Document indexé : liste de passages (page, section, texte) + index inversé idf pour l'interrogation."""

    def __init__(self, pages, titre_document: str | None = None):
        """`pages` = liste de str (une par page ; cf. extrait_pdf.pages) OU un seul str (document mono-bloc)."""
        if isinstance(pages, str):
            pages = [pages]
        self.titre = titre_document
        self.passages = []                    # [ {page, section, texte, tokens(set)} ]
        self._index = {}                      # token -> [id_passage, ...]
        self._df = {}                         # token -> nb de passages le contenant (pour l'idf)
        for i, txt in enumerate(pages):
            for section, passage in _passages_d_une_page(txt or ""):
                pid = len(self.passages)
                toks = _toks_doc(passage)
                self.passages.append({"page": i + 1, "section": section, "texte": passage,
                                      "tokens": toks, "tf": _compte(toks)})
                vus = set()
                for t in toks:
                    self._index.setdefault(t, []).append(pid)
                    if t not in vus:
                        self._df[t] = self._df.get(t, 0) + 1
                        vus.add(t)
        self.n = len(self.passages)

    # — interrogation —
    def interroge(self, question: str, k: int = 3, min_score: float = 0.0):
        """Passages les PLUS pertinents pour la question, pondérés idf : [{page, section, texte, score}].
        FAUX=0 : uniquement des passages littéraux ; [] si rien ne correspond (jamais d'invention)."""
        qtoks = set(_toks_doc(question))
        if not qtoks or self.n == 0:
            return []
        scores = {}
        for t in qtoks:
            postings = self._index.get(t)
            if not postings:
                continue
            idf = math.log(1.0 + self.n / (self._df.get(t, 0) or 1))     # idf lissé (>0 pour un terme présent)
            for pid in postings:
                tf = self.passages[pid]["tf"].get(t, 0)
                if tf <= 0:
                    continue
                # tf saturé (log) : un passage qui répète un mot ne l'emporte pas sur un passage qui couvre PLUS
                # de mots distincts de la question.
                scores[pid] = scores.get(pid, 0.0) + idf * (1.0 + math.log(tf))
        classes = sorted(scores.items(), key=lambda kv: (-kv[1], kv[0]))
        out = []
        for pid, sc in classes[:k]:
            if sc <= min_score:
                break
            p = self.passages[pid]
            out.append({"page": p["page"], "section": p["section"], "texte": p["texte"], "score": round(sc, 4)})
        return out

    def repond(self, question: str, max_chars: int = 500):
        """Réponse ATTRIBUÉE prête à afficher : le meilleur passage verbatim + page/section, ou None (honnête)."""
        hits = self.interroge(question, k=1)
        if not hits:
            return None
        h = hits[0]
        extrait = h["texte"]
        if len(extrait) > max_chars:
            extrait = extrait[:max_chars].rsplit(" ", 1)[0] + "…"
        loc = "page %d" % h["page"]
        if h["section"]:
            loc += ", section « %s »" % h["section"]
        return {"reponse": extrait, "page": h["page"], "section": h["section"], "localisation": loc}

    # — vue d'ensemble —
    def sommaire(self, max_titres: int = 40):
        """Titres de section détectés, dans l'ordre, avec leur page (uniques successifs). Vide si aucun titre."""
        out, dernier = [], None
        for p in self.passages:
            s = p["section"]
            if s and s != dernier:
                out.append({"titre": s, "page": p["page"]})
                dernier = s
            if len(out) >= max_titres:
                break
        return out

    def infos(self):
        pages = max((p["page"] for p in self.passages), default=0)
        return {"pages": pages, "passages": self.n, "sections": len(self.sommaire(10_000)),
                "mots_indexes": len(self._index)}


def _compte(tokens):
    d = {}
    for t in tokens:
        d[t] = d.get(t, 0) + 1
    return d


def depuis_pdf(octets: bytes, titre: str | None = None) -> "Document":
    """Construit un Document interrogeable directement depuis les octets d'un PDF (couche texte)."""
    import extrait_pdf
    return Document(extrait_pdf.pages(octets), titre_document=titre)
