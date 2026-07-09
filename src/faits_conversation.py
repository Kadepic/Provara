# -*- coding: utf-8 -*-
"""MÉMOIRE CONVERSATIONNELLE À EXTRACTION — les faits que l'utilisateur me confie (2026-07-09).

POURQUOI (audit 2026-07-09, item 12) : « le chien s'appelle Rex » n'était rappelé qu'en ÉCHO verbatim, et la
correction « en fait c'est Max » ne remplaçait RIEN (re-demande -> ressort Rex) — contraire au mandat
« les corrections de l'utilisateur font autorité ». Ce module EXTRAIT les faits personnels d'une conversation
(motifs FERMÉS : nom, âge, lieu de vie), y répond, et applique les corrections de l'utilisateur SANS exiger de
source : sur SA vie, l'utilisateur EST la source (≠ des faits-monde, qui gardent leur exigence de source).

MACHINE-NATIF, ZÉRO STOCKAGE NOUVEAU : l'état se REJOUE depuis les tours déjà stockés (conversation.py, ordre
chronologique) — persistance gratuite, RGPD gratuit (purger la conversation purge les faits), corrections
naturellement ordonnées. L'historique des valeurs est GARDÉ (bitemporel) : la réponse dit la correction.

FAUX=0 :
  • Motifs d'extraction FERMÉS, ancrés sur le message ENTIER -> zéro capture d'une phrase complexe.
  • Réponse TOUJOURS attribuée (« c'est toi qui me l'as dit ») — jamais présentée comme un fait du monde.
  • Correction NUE (« en fait c'est Max ») appliquée SEULEMENT sous FOCUS (le tour utilisateur précédent
    portait ce fait — déclaration ou question dessus) ; sinon None (le flux corrections-monde garde sa route).
  • Sujet inconnu -> None (le pipeline normal continue : « comment s'appelle le président » n'est pas capturé).
"""
from __future__ import annotations

import re

from base_faits import normalise

_ART = re.compile(r"^(?:le\s+|la\s+|les\s+|l['’]\s*|mon\s+|ma\s+|mes\s+|notre\s+|nos\s+|du\s+|de\s+la\s+|de\s+l['’]\s*|d['’]\s*)+", re.I)


def _sujet_cle(s: str) -> str:
    """Clé de sujet : articles/possessifs retirés puis normalisé (« mon chien » == « le chien » == « chien »)."""
    return normalise(_ART.sub("", s.strip()))


def _nettoie(v: str) -> str:
    return v.strip(" .!\"'«»\t")


# ── DÉCLARATIONS (motifs FERMÉS, message entier) ─────────────────────────────────────────────────────────────
_D_SUJET = r"((?:le\s+|la\s+|l['’]\s*|mon\s+|ma\s+|mes\s+|notre\s+|nos\s+)?[a-zà-ÿA-ZÀ-Ý][\w'’ -]{1,40}?)"
_DECLARATIONS = [
    ("nom", re.compile(r"^\s*(?:au fait[, ]+)?" + _D_SUJET +
                       r"\s+(?:s['’]appelle|se nomme|se pr[ée]nomme)\s+([\w'’À-Ýà-ÿ -]{1,40}?)\s*[.!]*\s*$", re.I)),
    ("age", re.compile(r"^\s*(?:au fait[, ]+)?" + _D_SUJET + r"\s+a\s+(\d{1,3})\s+ans\s*[.!]*\s*$", re.I)),
    ("lieu", re.compile(r"^\s*(?:au fait[, ]+)?" + _D_SUJET +
                        r"\s+(?:habite|vit)\s+(?:à\s+|en\s+|au\s+|aux\s+)?([\w'’À-Ýà-ÿ -]{1,40}?)\s*[.!]*\s*$", re.I)),
]
_PRONOM = re.compile(r"^\s*(?:il|elle|ça|ca|c['’]est lui|c['’]est elle)\s*$", re.I)

# ── CORRECTIONS ──────────────────────────────────────────────────────────────────────────────────────────────
#   verbale (pronom + verbe du fait) : « en fait il s'appelle Max » -> dernier fait « nom »
_CORR_VERBALE = re.compile(
    r"^\s*(?:non[, ]+|mais non[, ]+|en fait[, ]+|pardon[, ]+)?(?:il|elle)\s+"
    r"(?:s['’]appelle|se nomme|se pr[ée]nomme)\s+([\w'’À-Ýà-ÿ -]{1,40}?)\s*[.!]*\s*$", re.I)
#   nue (« en fait c'est Max », « non, c'est Max ») : SEULEMENT sous focus (garde FAUX=0)
_CORR_NUE = re.compile(
    r"^\s*(?:non|mais non|en fait|je me suis tromp[ée]?e?|pardon|correction)[, :]+\s*c['’]est\s+"
    r"([\w'’À-Ýà-ÿ -]{1,40}?)\s*[.!]*\s*$", re.I)

# ── QUESTIONS (motifs FERMÉS) ────────────────────────────────────────────────────────────────────────────────
_QUESTIONS = [
    ("nom", re.compile(r"^\s*(?:comment\s+(?:s['’]appelle|se nomme)\s+" + _D_SUJET + r"|"
                       r"quel\s+est\s+le\s+(?:nom|pr[ée]nom)\s+(?:du\s+|de\s+la\s+|de\s+l['’]\s*|de\s+mon\s+|de\s+ma\s+|de\s+)?([\w'’à-ÿ -]{1,40}?)|" +
                       _D_SUJET + r"\s+s['’]appelle\s+comment)\s*\??\s*$", re.I)),
    ("age", re.compile(r"^\s*quel\s+[âa]ge\s+a\s+" + _D_SUJET + r"\s*\??\s*$", re.I)),
    ("lieu", re.compile(r"^\s*o[ùu]\s+(?:habite|vit)\s+" + _D_SUJET + r"\s*\??\s*$", re.I)),
]
_LIBELLES = {"nom": "s'appelle", "age": "a %s ans", "lieu": "habite %s"}


class FaitsConversation:
    """Faits personnels d'UNE conversation, rejoués depuis ses tours utilisateur. Voir docstring module."""

    def __init__(self):
        self._faits: dict = {}      # (attribut, sujet_cle) -> {"sujet": affiché, "valeurs": [v1, v2, …]}
        self._focus = None          # (attribut, sujet_cle) posé par le DERNIER tour (déclaration/question/correction)

    # — apprentissage —
    def apprend(self, texte: str):
        """Traite un tour utilisateur. Renvoie ("appris", fait) | ("corrige", fait, ancienne) | None.
        `fait` = {"sujet", "attribut", "valeur"}. Met à jour le focus (et le PERD sur tout autre message)."""
        t = str(texte or "").strip()
        for attribut, motif in _DECLARATIONS:
            m = motif.match(t)
            if m:
                sujet, valeur = m.group(1).strip(), _nettoie(m.group(2))
                if _PRONOM.match(sujet) or not valeur:
                    break                                            # pronom -> voie correction, pas déclaration
                cle = (attribut, _sujet_cle(sujet))
                if not cle[1]:
                    break
                ent = self._faits.setdefault(cle, {"sujet": sujet.strip(), "valeurs": []})
                self._focus = cle
                if ent["valeurs"] and normalise(ent["valeurs"][-1]) == normalise(valeur):
                    return None                                      # redite exacte : rien de neuf
                ancienne = ent["valeurs"][-1] if ent["valeurs"] else None
                ent["valeurs"].append(valeur)
                fait = {"sujet": ent["sujet"], "attribut": attribut, "valeur": valeur}
                return ("corrige", fait, ancienne) if ancienne else ("appris", fait)
        m = _CORR_VERBALE.match(t)
        if m:
            return self._corrige("nom", _nettoie(m.group(1)))
        m = _CORR_NUE.match(t)
        if m and self._focus:
            return self._corrige(self._focus[0], _nettoie(m.group(1)), cle=self._focus)
        # question sur un fait connu -> garde le focus ; tout autre message le PERD (correction nue = fermée)
        q = self._question_cle(t)
        if q:
            self._focus = q if q in self._faits else None
        else:
            self._focus = None
        return None

    def _corrige(self, attribut: str, valeur: str, cle=None):
        """Applique une correction au fait ciblé (focus, ou dernier fait de cet attribut). L'utilisateur fait
        autorité sur SES faits : remplacement immédiat, historique gardé."""
        if not valeur:
            return None
        if cle is None:                                              # dernier fait de cet attribut (correction verbale)
            candidats = [c for c in self._faits if c[0] == attribut]
            if len(candidats) != 1 and self._focus in candidats:
                candidats = [self._focus]
            if len(candidats) != 1:
                return None                                          # ambigu -> on ne devine pas
            cle = candidats[0]
        ent = self._faits.get(cle)
        if not ent or not ent["valeurs"]:
            return None
        ancienne = ent["valeurs"][-1]
        if normalise(ancienne) == normalise(valeur):
            return None
        ent["valeurs"].append(valeur)
        self._focus = cle
        return ("corrige", {"sujet": ent["sujet"], "attribut": cle[0], "valeur": valeur}, ancienne)

    # — restitution —
    def _question_cle(self, texte: str):
        for attribut, motif in _QUESTIONS:
            m = motif.match(str(texte or "").strip())
            if m:
                sujet = next((g for g in m.groups() if g), "")
                ck = _sujet_cle(sujet)
                if ck:
                    return (attribut, ck)
        return None

    def repond(self, question: str):
        """Réponse ATTRIBUÉE depuis les faits confiés, ou None (sujet inconnu -> le pipeline continue)."""
        cle = self._question_cle(question)
        if not cle:
            return None
        ent = self._faits.get(cle)
        if not ent or not ent["valeurs"]:
            return None
        self._focus = cle
        val = ent["valeurs"][-1]
        aff = ("%s ans" % val) if cle[0] == "age" else val
        if len(ent["valeurs"]) > 1:
            return ("%s. (C'est toi qui me l'as dit — tu avais d'abord dit « %s », ta correction fait "
                    "autorité.)" % (aff, ent["valeurs"][0]))
        return "%s. (C'est toi qui me l'as dit dans cette conversation.)" % aff

    def accuse(self, resultat) -> str:
        """Accusé de réception SPÉCIFIQUE (remplace le « C'est noté » générique quand on a VRAIMENT extrait)."""
        if not resultat:
            return ""
        genre, fait = resultat[0], resultat[1]
        desc = {"nom": "%s s'appelle %s" % (fait["sujet"], fait["valeur"]),
                "age": "%s a %s ans" % (fait["sujet"], fait["valeur"]),
                "lieu": "%s habite %s" % (fait["sujet"], fait["valeur"])}[fait["attribut"]]
        if genre == "corrige":
            return ("Corrigé : %s (j'avais « %s » — ta correction fait autorité). Tu peux me le "
                    "redemander." % (desc, resultat[2]))
        return "Noté : %s. Tu peux me le redemander dans cette conversation." % desc


def depuis_tours(tours) -> FaitsConversation:
    """Rejoue les tours UTILISATEUR d'une conversation (dicts {role, texte}, ordre chronologique) -> état."""
    fc = FaitsConversation()
    for t in tours or []:
        if isinstance(t, dict) and t.get("role") == "user":
            fc.apprend(t.get("texte") or "")
    return fc
