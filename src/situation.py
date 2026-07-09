# -*- coding: utf-8 -*-
"""SITUATION DE CONVERSATION — « tenir le fil », machine-natif (2026-07-09, chantier compréhension).

POURQUOI (sonde du 09/07 au soir : conversation d'ingénieur sur un échangeur thermique) : ce que l'utilisateur
ÉNONCE (grandeurs, entités, hypothèses) n'alimentait AUCUN état — « reprends ce que je t'ai dit sur le fluide
chaud » s'auto-citait, « résume notre conversation » rendait le repli, et les grandeurs données restaient
inertes. Cette brique tient LE FIL : tout ce que l'utilisateur affirme, tenu, typé, indexé, restituable.

PENSÉE MACHINE (constitution SPEC_TRONC §1 — à REBOURS de l'humain) :
  • NE JAMAIS compresser ni oublier : chaque clause utilisateur est tenue VERBATIM, avec son tour d'origine.
    Le « résumé » n'est pas stocké : il se CALCULE à la demande depuis l'ancré.
  • Pas de slots prédéfinis (≠ dialogue-state-tracking classique) : référents OUVERTS — l'index inversé par
    tokens de contenu remplace la grille figée ; les GRANDEURS (nombre + unité fermée) sont typées par
    dimension et attachées à leur clause.
  • FAUX=0 PAR CONSTRUCTION : toute restitution CITE sa clause source (« tour N ») — même si l'indexation
    était imparfaite, on ne restitue que du verbatim réellement dit, jamais une reformulation inventée.
  • Une clause « si … » est étiquetée HYPOTHÈSE et restituée comme telle (jamais promue en fait).

REJOUABLE : l'état se reconstruit des tours stockés (persistance/RGPD gratuits — même principe que
faits_conversation). Zéro stockage nouveau.
"""
from __future__ import annotations

import re

from base_faits import normalise
from fonction_nl import _CONV_UNITS

# unités RECONNUES (pas converties ici) : la table fermée de conversion + les grandeurs de travail courantes
# (température/pression/puissance/débit — absentes de _CONV_UNITS car non linéaires ou composées).
_DIMS = {"L": "longueur", "M": "masse", "T": "temps", "V": "volume", "A": "aire", "S": "vitesse", "D": "données",
         "TEMP": "température", "P": "pression", "W": "puissance", "E": "énergie", "F": "débit", "PC": "proportion",
         "U": "coefficient d'échange", "EUR": "montant"}
_UNITES_LOCALES = {
    "°c": "TEMP", "degre": "TEMP", "degres": "TEMP", "degré": "TEMP", "degrés": "TEMP", "kelvin": "TEMP", "k": "TEMP",
    "bar": "P", "bars": "P", "pa": "P", "kpa": "P", "mpa": "P", "hpa": "P",
    "w": "W", "kw": "W", "mw": "W", "watt": "W", "watts": "W", "kilowatt": "W", "kilowatts": "W",
    "j": "E", "kj": "E", "mj": "E", "kwh": "E", "wh": "E",
    "kg/s": "F", "kg/h": "F", "l/s": "F", "l/min": "F", "l/h": "F", "m3/h": "F", "m3/s": "F",
    "w/m2k": "U", "w/m2.k": "U", "w/m²k": "U",
    "%": "PC", "€": "EUR", "euro": "EUR", "euros": "EUR",
}
_TOUTES_UNITES = {u: dim for u, (dim, _) in _CONV_UNITS.items()} | _UNITES_LOCALES
# les unités multi-caractères d'abord (w/m2k avant w ; km/h avant km) ; échappées pour le motif.
_UNITE_ALT = "|".join(re.escape(u) for u in sorted(_TOUTES_UNITES, key=len, reverse=True))
_RE_GRANDEUR = re.compile(r"(-?\d+(?:[.,]\d+)?)\s*(" + _UNITE_ALT + r")(?![a-z0-9])", re.I)

_MOTS_VIDES_SIT = set(normalise(
    "le la les l un une des de du d et ou mais donc or ni car a à au aux en dans sur sous vers chez pour par "
    "avec sans que qui quoi dont je tu il elle on nous vous ils elles ce cet cette ces mon ma mes ton ta tes "
    "son sa ses notre votre leur nos vos est sont etait suis es sera c s y ne pas plus tres si alors quand "
    "comme aussi encore deja tout tous toute toutes rien quel quelle quels quelles").split())
# NB : « entre » n'est PAS un mot vide ici — c'est le VERBE porteur des rôles thermiques (« entre à 90 ») ;
# son usage prépositionnel n'ajoute qu'un token de bruit inoffensif pour l'appariement par sur-ensemble.


# interjections/sociales (carte fermée) : une clause faite UNIQUEMENT de ces tokens n'est pas un fil à tenir.
_INTERJECTIONS = set(normalise(
    "ok oui non merci super parfait genial bravo cool top nickel bonjour bonsoir salut hello coucou daccord "
    "d'accord entendu compris bien noté note ca marche impeccable excellent chouette ah oh hum euh voila").split())


def _toks(texte: str) -> set:
    """Tokens de CONTENU racinisés (pluriel régulier neutralisé) — l'index du fil."""
    out = set()
    for t in normalise(texte).split():
        if t and t not in _MOTS_VIDES_SIT and not t.isdigit():
            out.add(t[:-1] if len(t) > 3 and t[-1] in "sx" else t)
    return out


_RE_INTERROGATIVE = re.compile(
    r"^\s*(?:quel(?:le)?s?\b|comment\b|pourquoi\b|combien\b|qui\b|que\b|qu['’]|quand\b|o[ùu]\b|est[- ]ce\b|"
    r"peux[- ]tu\b|dis[- ]moi\b|donne[- ]moi\b|"
    # DEMANDES impératives (vécu e2e : « reprends ce que je t'ai dit… » entrait LUI-MÊME dans le fil)
    r"reprends?\b|rappelle\b|redis\b|r[ée]sume\b|r[ée]capitule\b|montre\b|explique\b|calcule\b|cherche\b|"
    r"donne\b|liste\b|trace\b|compare\b|v[ée]rifie\b|prouve\b|fais\b)", re.I)


def _clauses(texte: str) -> list:
    """Découpe conservatrice d'un tour en (clause verbatim, est_question). Une clause est une QUESTION si elle
    porte un « ? » propre, ouvre par un interrogatif, ou est la dernière d'un tour finissant par « ? »."""
    brut = texte.strip()
    finit_question = brut.endswith("?")
    morceaux = [m.strip(" ,") for m in re.split(r"\s*[;.!]\s+|\s*[;.!]$", brut) if m and m.strip(" ,")]
    out = []
    for i, m in enumerate(morceaux):
        est_q = ("?" in m or bool(_RE_INTERROGATIVE.match(m))
                 or (finit_question and i == len(morceaux) - 1))
        out.append((m.rstrip(" ?"), est_q))
    return out


class Situation:
    """Le FIL d'une conversation : clauses utilisateur verbatim + grandeurs typées + index inversé."""

    def __init__(self):
        self.clauses: list = []          # {seq, texte, toks, grandeurs:[{brut, valeur, unite, dim}], hypothese}

    # — apprentissage (chaque tour UTILISATEUR) —
    def apprend(self, seq: int, texte: str) -> int:
        """Tient les clauses ASSERTIVES du tour (les questions sont des demandes, pas des déclarations).
        Renvoie le nombre de clauses tenues. ELLIPSE D'UNITÉ (« entre à 90 degrés et sort à 50 ») : un nombre
        NU coordonné après une grandeur typée hérite de sa dimension en SUPPOSITION ÉTIQUETÉE (unite_implicite),
        restituée comme telle — jamais affirmée (constitution : non tranché = supposition, jamais un faux)."""
        n = 0
        for cl, est_question in _clauses(str(texte or "")):
            if est_question or len(cl) < 3:
                continue
            grandeurs, fin_prec = [], 0
            for m in _RE_GRANDEUR.finditer(cl):
                brut, unite = m.group(1), m.group(2).lower()
                try:
                    val = float(brut.replace(",", "."))
                except ValueError:
                    continue
                # rôle = les tokens du SEGMENT depuis la grandeur précédente (« et sort à » pour le 2ᵉ nombre) —
                # une fenêtre fixe mélangeait les rôles de grandeurs voisines (vécu pont : chaud/froid confondus).
                grandeurs.append({"brut": m.group(0), "valeur": val, "unite": unite,
                                  "dim": _DIMS.get(_TOUTES_UNITES.get(unite, ""), ""),
                                  "implicite": False, "pos": m.start(),
                                  "role": _toks(cl[fin_prec:m.start()])})
                fin_prec = m.end()
            if grandeurs:
                # ellipse : nombres NUS après la 1ʳᵉ grandeur typée (« et sort à 50 ») -> même dimension, SUPPOSÉE
                couverts = [(g["pos"], g["pos"] + len(g["brut"])) for g in grandeurs]
                ref = grandeurs[0]
                for m in re.finditer(r"(?<![\w,.])(-?\d+(?:[.,]\d+)?)(?![\w%€])(?![.,]\d)", cl):
                    if any(a <= m.start() < b for a, b in couverts) or m.start() < ref["pos"]:
                        continue
                    try:
                        val = float(m.group(1).replace(",", "."))
                    except ValueError:
                        continue
                    prec = max([b for a, b in couverts if b <= m.start()], default=0)
                    grandeurs.append({"brut": "%s (%s implicite)" % (m.group(1), ref["unite"]),
                                      "valeur": val, "unite": ref["unite"], "dim": ref["dim"],
                                      "implicite": True, "pos": m.start(),
                                      "role": _toks(cl[prec:m.start()])})
                grandeurs.sort(key=lambda g: g["pos"])
            toks = _toks(cl)
            if not grandeurs and (len(toks) < 2 or toks <= _INTERJECTIONS):
                continue                                             # interjection / bruit : pas un fil
            self.clauses.append({"seq": seq, "texte": cl, "toks": toks, "grandeurs": grandeurs,
                                 "hypothese": bool(re.match(r"\s*(?:et\s+)?si\b", cl, re.I))})
            n += 1
        return n

    # — restitutions (toujours ANCRÉES : clause verbatim + tour) —
    def _cite(self, c) -> str:
        pfx = "[hypothèse] " if c["hypothese"] else ""
        return "%s« %s » (tour %d)" % (pfx, c["texte"], c["seq"])

    def reprends(self, sujet: str):
        """Rappel FILTRÉ : les clauses dont l'index couvre les tokens du sujet. None si rien (jamais d'à-côté)."""
        vise = _toks(sujet)
        if not vise:
            return None
        hits = [c for c in self.clauses if vise <= c["toks"]]
        if not hits:
            return None
        return "Voici ce que tu m'as dit là-dessus :\n" + "\n".join("· " + self._cite(c) for c in hits[:12])

    def resume(self):
        """Résumé CALCULÉ depuis l'ancré (jamais stocké, jamais réécrit) : les clauses tenues + les grandeurs."""
        if not self.clauses:
            return None
        lignes = ["· " + self._cite(c) for c in self.clauses[:15]]
        gr = [(g["brut"], g["dim"]) for c in self.clauses for g in c["grandeurs"]]
        rec = ("\nGrandeurs relevées : " + ", ".join("%s%s" % (b, " (%s)" % d if d else "") for b, d in gr[:20])) \
            if gr else ""
        plus = "\n(+%d autres clauses tenues)" % (len(self.clauses) - 15) if len(self.clauses) > 15 else ""
        return "Le fil de cette conversation — ce que tu m'as dit, verbatim :\n" + "\n".join(lignes) + plus + rec

    def accuse_tour(self, seq: int):
        """Accusé de réception du FIL pour un tour à GRANDEURS (« C'est noté, je tiens : 90 degrés… ») —
        remplace le lookup fragmenté « pas en mémoire » sur une déclaration technique. None si le tour n'a
        apporté aucune grandeur (les affirmations simples gardent leurs flux existants : mémo, patrons…)."""
        gr = [g for c in self.clauses if c["seq"] == seq for g in c["grandeurs"]]
        if not gr:
            return None
        return ("C'est noté, je tiens le fil : %s. Tu peux me les redemander (« quelles données je t'ai "
                "données ? »), me demander « résume notre conversation », ou continuer." %
                ", ".join(g["brut"] for g in gr[:10]))

    def grandeurs_de(self, sujet: str = "") -> list:
        """Les grandeurs typées (toutes, ou filtrées par sujet) — l'interface du PONT vers les moteurs."""
        vise = _toks(sujet)
        out = []
        for c in self.clauses:
            if vise and not vise <= c["toks"]:
                continue
            for g in c["grandeurs"]:
                out.append({**g, "clause": c["texte"], "seq": c["seq"], "hypothese": c["hypothese"]})
        return out

    # — routeur de QUESTIONS sur le fil (motifs fermés ; None = pas pour moi, le pipeline continue) —
    _RE_RESUME = re.compile(
        r"^\s*(?:fais[- ]?(?:moi\s+)?(?:le\s+|un\s+)?(?:point|r[ée]sum[ée])|r[ée]sume(?:[- ]?(?:moi|nous))?)\s*"
        r"(?:notre|la|cette)?\s*(?:conversation|discussion|[ée]change|fil)?\s*\??\s*$|"
        r"^\s*o[ùu] en (?:est[- ]on|sommes[- ]nous)\s*\??\s*$", re.I)
    _RE_REPREND = re.compile(
        r"^\s*(?:reprends?|rappelle(?:[- ]?(?:moi|nous))?|redis(?:[- ]?moi)?|r[ée]capitule)\s+"
        r"(?:ce que je t['’]ai dit|ce qu['’]on a dit|mes donn[ée]es)?\s*(?:sur|de|à propos de|concernant)?\s*(.*?)\s*\??\s*$|"
        r"^\s*qu['’]est[- ]ce que je t['’]ai dit\s+(?:sur|de|à propos de|concernant)\s+(.+?)\s*\??\s*$", re.I)
    _RE_DONNEES = re.compile(
        r"^\s*quelles?\s+(?:donn[ée]es|grandeurs|valeurs)\s+(?:je\s+t['’]ai|t['’]ai[- ]je)\s+donn[ée]e?s?\s*\??\s*$", re.I)

    def repond(self, question: str):
        q = str(question or "").strip()
        if self._RE_RESUME.match(q):
            return self.resume()
        m = self._RE_DONNEES.match(q)
        if m:
            gr = self.grandeurs_de()
            if not gr:
                return "Tu ne m'as encore donné aucune grandeur chiffrée dans cette conversation."
            return "Les grandeurs que tu m'as données :\n" + "\n".join(
                "· %s%s — « %s » (tour %d)" % (g["brut"], " (%s)" % g["dim"] if g["dim"] else "",
                                               g["clause"], g["seq"]) for g in gr[:15])
        m = self._RE_REPREND.match(q)
        if m:
            sujet = next((g for g in m.groups() if g), "").strip()
            if sujet:
                return self.reprends(sujet)
            return self.resume()                                     # « reprends » nu = tout le fil
        return None


def depuis_tours(tours) -> Situation:
    """Rejoue les tours UTILISATEUR ({role, texte, seq?}) -> Situation (ordre chronologique)."""
    s = Situation()
    for i, t in enumerate(tours or []):
        if isinstance(t, dict) and t.get("role") == "user":
            s.apprend(int(t.get("seq", i)), t.get("texte") or "")
    return s
