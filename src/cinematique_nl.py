# -*- coding: utf-8 -*-
"""CINÉMATIQUE NL — problèmes à étapes du mouvement uniforme, EXACTS (audit 2026-07-09, item 7).

POURQUOI : « deux trains distants de 300 km partent l'un vers l'autre à 80 et 70 km/h : quand se croisent-
ils ? » n'avait aucune route — le dernier item du pont vocabulaire→moteurs. La physique est BORNÉE (mouvement
rectiligne uniforme, 2 lois fermées) : la réponse est un CALCUL exact, pas une supposition.

DEUX PATRONS FERMÉS (v1) :
  • RENCONTRE (sens opposés)  : t = D / (v1 + v2) ; point de croisement à v1·t du premier.
  • POURSUITE (même sens)     : t = D / (v1 − v2) si v1 > v2, sinon IMPOSSIBLE dit (jamais un temps négatif).

FAUX=0 :
  • Fractions EXACTES de bout en bout (2 h 24 = 12/5 h, jamais 2.3999…) ; affichage h + min exactes.
  • Motifs FERMÉS : il faut la distance, LES DEUX vitesses ET le mot-clé (se croisent / rencontrent /
    rattrape) — sinon None, le pipeline continue (zéro capture d'une question sur « les trains »).
  • Unités contrôlées : km + km/h (ou m + m/s). Unités mélangées -> None (pas de conversion devinée).
  • La DÉRIVATION est montrée (vitesse de rapprochement, division exacte) — re-vérifiable à la main.
"""
from __future__ import annotations

import re
from fractions import Fraction

_NUM = r"(\d+(?:[.,]\d+)?)"
# vitesses : « à 80 et 70 km/h », « à 80 km/h et (l'autre à) 70 km/h »
_V2 = (r"[àa]\s+" + _NUM + r"\s*(?:km/?h|kilom[èe]tres?[ /-]heure)?\s*(?:et|,)\s*(?:l['’]autre\s+)?(?:[àa]\s+)?"
       + _NUM + r"\s*(km/?h|kilom[èe]tres?[ /-]heure|m/s)")
_D_KM = _NUM + r"\s*(km|kilom[èe]tres?|m[èe]tres?|m)\b"

_RE_RENCONTRE = re.compile(
    r"(?:deux|2)\s+(?:trains?|voitures?|v[ée]los?|cyclistes?|coureurs?|mobiles?|bateaux?|camions?)\b.*?"
    r"(?:distants?\s+de|s[ée]par[ée]s?\s+de|[ée]loign[ée]s?\s+de|[àa])\s+" + _D_KM +
    r".*?l['’]un\s+vers\s+l['’]autre.*?" + _V2 + r"|"
    r"(?:deux|2)\s+(?:trains?|voitures?|v[ée]los?|cyclistes?|coureurs?|mobiles?|bateaux?|camions?)\b.*?"
    r"l['’]un\s+vers\s+l['’]autre.*?(?:distants?\s+de|s[ée]par[ée]s?\s+de|[àa])\s+" + _D_KM + r".*?" + _V2,
    re.I | re.S)
_RE_CROISE = re.compile(r"se\s+(?:croisent|rencontrent|croiseront|rencontreront)|croisement|rencontre", re.I)
_RE_POURSUITE = re.compile(
    r"(?:rattrape|rattrapera|rejoint|rejoindra|(?:[àa]\s+la\s+)?poursuite)", re.I)
_RE_POURSUITE_DATA = re.compile(
    r"(?:avance|retard|[ée]cart|distance)\s+d[e'’]\s*" + _D_KM + r".*?" + _V2 + r"|" +
    _V2 + r".*?(?:avance|retard|[ée]cart|distance)\s+d[e'’]\s*" + _D_KM, re.I | re.S)


def _f(s: str) -> Fraction:
    return Fraction(s.replace(",", "."))


def _fmt_duree(t: Fraction) -> str:
    """Durée exacte en h/min (2,4 h -> « 2 h 24 min ») ; minutes non entières -> fraction dite."""
    h = int(t)
    mn = (t - h) * 60
    if mn == 0:
        return "%d h" % h
    if mn.denominator == 1:
        return ("%d h %d min" % (h, mn)) if h else ("%d min" % mn)
    return ("%d h %s min (exactement)" % (h, mn)) if h else ("%s min (exactement)" % mn)


def _fmt_km(x: Fraction, unite: str) -> str:
    if x.denominator == 1:
        return "%d %s" % (x, unite)
    return "%s %s (= %s)" % (x, unite, round(float(x), 3))


def resout(question: str):
    """Réponse EXACTE (str, dérivation montrée) ou None (hors des 2 patrons fermés — le pipeline continue)."""
    q = str(question or "")
    m = _RE_RENCONTRE.search(q)
    if m and _RE_CROISE.search(q):
        g = [x for x in m.groups() if x is not None]
        if len(g) != 5:
            return None
        d, u_d, v1, v2, u_v = _f(g[0]), g[1], _f(g[2]), _f(g[3]), g[4]
        if u_d.startswith("m") and "km" not in u_d and not u_v.startswith("m/s"):
            return None                                              # mètres avec km/h -> pas de conversion devinée
        if v1 + v2 == 0:
            return None
        t = d / (v1 + v2)
        p1 = v1 * t
        u_len = "km" if "km" in u_d else "m"
        return ("Ils se croisent au bout de %s : vitesse de rapprochement = %s + %s = %s %s ; temps = %s ÷ %s "
                "= %s. Le croisement a lieu à %s du premier (et %s du second)." %
                (_fmt_duree(t), g[2].replace(",", "."), g[3].replace(",", "."), v1 + v2, u_v, g[0].replace(",", "."),
                 v1 + v2, _fmt_duree(t), _fmt_km(p1, u_len), _fmt_km(d - p1, u_len)))
    if _RE_POURSUITE.search(q):
        m = _RE_POURSUITE_DATA.search(q)
        if not m:
            return None
        g = [x for x in m.groups() if x is not None]
        if len(g) != 5:
            return None
        if g[1] in ("km", "m") or g[1].startswith(("kilom", "mètre", "metre")):   # ordre : distance d'abord
            d, u_d, va, vb, u_v = _f(g[0]), g[1], _f(g[2]), _f(g[3]), g[4]
        else:                                                                     # ordre : vitesses d'abord
            va, vb, u_v, d, u_d = _f(g[0]), _f(g[1]), g[2], _f(g[3]), g[4]
        v_pours, v_fuit = max(va, vb), min(va, vb)                    # le poursuivant est le plus rapide
        if v_pours == v_fuit:
            return ("À vitesses égales (%s %s), l'écart de %s %s ne se referme jamais : il ne le rattrape pas." %
                    (v_pours, u_v, d, u_d))
        t = d / (v_pours - v_fuit)
        return ("Il le rattrape au bout de %s : vitesse de rapprochement = %s − %s = %s %s ; temps = %s ÷ %s "
                "= %s." % (_fmt_duree(t), v_pours, v_fuit, v_pours - v_fuit, u_v,
                           d, v_pours - v_fuit, _fmt_duree(t)))
    return None
