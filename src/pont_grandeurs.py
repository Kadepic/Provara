# -*- coding: utf-8 -*-
"""PONT SITUATION→MOTEURS — les grandeurs ÉNONCÉES deviennent des OPÉRANDES (brique 2 du fil, 2026-07-09).

POURQUOI (sonde échangeur) : « quel est l'écart de température moyen logarithmique ? » partait au web et
« quelle surface pour 100 kW avec 500 W/m²K ? » recevait « c'est subjectif » — alors que les données étaient
DANS la conversation. Ce module apparie les grandeurs du fil (situation.grandeurs_de, typées + rôles) aux
besoins de CALCULS FERMÉS et répond EXACT, formule montrée.

LE COMPORTEMENT-CLÉ (perfection FAUX=0) : opérande MANQUANT -> l'IA le DEMANDE NOMMÉMENT (« il me manque la
température de sortie du fluide froid — donne-la-moi et je calcule »). Jamais une valeur devinée, jamais un
« je ne sais pas » aveugle : l'abstention est ACTIONNABLE.

CALCULS v1 (registre fermé) :
  • ÉCART entre deux grandeurs du fil (« l'écart entre l'entrée et la sortie du fluide chaud ») ;
  • DTLM (échangeur : ΔT moyen logarithmique) — exige les 4 températures ET le sens (contre/co-courant) ;
  • SURFACE D'ÉCHANGE A = Q / (U · ΔTlm) — les grandeurs peuvent venir du fil OU de la question elle-même.

FAUX=0 : motifs fermés (mots-clés exigés) ; ambiguïté d'appariement -> candidats LISTÉS, jamais tranchés en
silence ; hypothèses (« si… ») jamais utilisées comme opérandes ; arrondi TOUJOURS marqué (valeur exacte à
côté) ; hors périmètre -> None (le pipeline continue).
"""
from __future__ import annotations

import math
import re

from base_faits import normalise
import situation as _S

_W_FACT = {"w": 1.0, "watt": 1.0, "watts": 1.0, "kw": 1e3, "kilowatt": 1e3, "kilowatts": 1e3, "mw": 1e6}


def _fmt(v: float) -> str:
    if v == int(v):
        return str(int(v))
    return ("%.4f" % v).rstrip("0").rstrip(".").replace(".", ",")


def _grandeurs_sures(sit) -> list:
    """Les grandeurs UTILISABLES comme opérandes : jamais celles d'une hypothèse (« si je double… »)."""
    return [g for g in sit.grandeurs_de() if not g.get("hypothese")]


def _cherche(sit, mots: str, dim: str = ""):
    """Grandeurs du fil dont rôle∪clause couvre les tokens de `mots` (et la dimension si donnée)."""
    vise = _S._toks(mots)
    out = []
    for g in _grandeurs_sures(sit):
        if dim and g["dim"] != dim:
            continue
        contexte = set(g.get("role") or set()) | _S._toks(g["clause"])
        if vise <= contexte:
            out.append(g)
    return out


# normalisation des rôles thermiques : le nom (« l'entrée ») et le verbe (« entre ») désignent le même slot.
_SENS = {"entre": "entre", "entree": "entre", "entrees": "entre", "arrive": "entre",
         "sort": "sort", "sortie": "sort", "sorties": "sort", "ressort": "sort"}


def _slots_temperature(sit) -> tuple:
    """MACHINE À ÉTATS sur les grandeurs de température du fil (ordre du texte) : le FLUIDE COURANT
    (chaud/froid) se propage de segment en segment (« le fluide chaud entre à 90 et sort à 50 » : le 50 hérite
    de « chaud »), le SENS vient du segment de la grandeur. -> ({(fluide, sens): grandeur}, {slots ambigus})."""
    slots, conflits = {}, set()
    fluide = None
    for g in _grandeurs_sures(sit):
        if g["dim"] != "température":
            continue
        role = set(g.get("role") or set())
        if "chaud" in role:
            fluide = "chaud"
        elif "froid" in role:
            fluide = "froid"
        sens = next((_SENS[t] for t in role if t in _SENS), None)
        if fluide is None or sens is None:
            continue
        # ré-énoncé -> la DERNIÈRE valeur fait foi (même principe que les corrections : l'utilisateur est
        # l'autorité sur SES données ; l'historique reste dans le fil, citable).
        slots[(fluide, sens)] = g
    return slots, conflits


# ── ÉCART entre deux grandeurs ───────────────────────────────────────────────────────────────────────────────
_RE_ECART = re.compile(
    r"(?:[ée]cart|diff[ée]rence)\s+(?:de\s+(\w+)\s+)?entre\s+(.+?)\s+et\s+(?:celle\s+de\s+|celui\s+de\s+)?(.+?)\s*\??\s*$", re.I)
_DIM_MOTS = {"temperature": "température", "températures": "température", "temperatures": "température",
             "debit": "débit", "débit": "débit", "pression": "pression", "puissance": "puissance"}


def _ecart(question: str, sit):
    m = _RE_ECART.search(question)
    if not m:
        return None
    gauche, droite = m.group(2), m.group(3)
    # « l'entrée et la sortie du fluide chaud » : le COMPLÉMENT commun (après « du/de la ») s'applique aux deux.
    commun = ""
    mc = re.search(r"^(.*?)\s+(?:du|de\s+la|de\s+l['’])\s+(.+)$", droite)
    if mc:
        droite, commun = mc.group(1), mc.group(2)

    def _resout(cote: str):
        toks = {_SENS.get(t, t) for t in _S._toks(cote + " " + commun)}
        # slot thermique (entrée/sortie × chaud/froid) via la machine à états
        slots, _ = _slots_temperature(sit)
        fl = "chaud" if "chaud" in toks else ("froid" if "froid" in toks else None)
        sens = next((t for t in toks if t in ("entre", "sort")), None)
        if fl and sens and (fl, sens) in slots:
            return slots[(fl, sens)]
        # sinon appariement générique par rôle∪clause
        cands = _cherche(sit, (cote + " " + commun).strip())
        return cands[0] if len(cands) == 1 else ("ambigu" if len(cands) > 1 else None)

    a, b = _resout(gauche), _resout(droite)
    if a in (None, "ambigu") or b in (None, "ambigu"):
        if a == "ambigu" or b == "ambigu":
            return "Plusieurs grandeurs du fil correspondent — précise (entrée/sortie, chaud/froid…)."
        return None
    if a["dim"] != b["dim"]:
        return "Je ne soustrais pas des grandeurs de dimensions différentes (%s vs %s)." % (a["dim"], b["dim"])
    d = abs(a["valeur"] - b["valeur"])
    unite = a["unite"] if a["unite"] not in ("degres", "degrés", "degre", "degré") else "degrés"
    return ("Écart = %s − %s = %s %s  (d'après ce que tu m'as donné : « %s », tour %d%s)." %
            (_fmt(max(a["valeur"], b["valeur"])), _fmt(min(a["valeur"], b["valeur"])), _fmt(d), unite,
             a["clause"][:60], a["seq"],
             "" if a["clause"] == b["clause"] else " ; « %s », tour %d" % (b["clause"][:60], b["seq"])))


# ── DTLM (échangeur) ─────────────────────────────────────────────────────────────────────────────────────────
_RE_DTLM = re.compile(r"dtlm|lmtd|(?:[ée]cart|diff[ée]rence)\s+(?:de\s+temp[ée]rature\s+)?moyen(?:ne)?\s+"
                      r"logarithmique|Δt\s*lm|deltat\s*lm", re.I)


_LIBELLES_SLOT = {("chaud", "entre"): "la température d'ENTRÉE du fluide chaud",
                  ("chaud", "sort"): "la température de SORTIE du fluide chaud",
                  ("froid", "entre"): "la température d'ENTRÉE du fluide froid",
                  ("froid", "sort"): "la température de SORTIE du fluide froid"}


def _dtlm_operandes(sit):
    """Les 4 températures + le sens d'écoulement, ou la LISTE de ce qui manque (demande actionnable)."""
    slots, conflits = _slots_temperature(sit)
    manque = [lib for cle, lib in _LIBELLES_SLOT.items() if cle not in slots]
    ambigu = [_LIBELLES_SLOT[cle] for cle in conflits]
    contre = any("contre courant" in normalise(c["texte"]) for c in sit.clauses)   # normalise ôte le tiret
    co = any(re.search(r"\bco courant", normalise(c["texte"])) for c in sit.clauses)
    return slots, manque, ambigu, contre, co


def _dtlm(question: str, sit):
    if not _RE_DTLM.search(question):
        return None
    vals, manque, ambigu, contre, co = _dtlm_operandes(sit)
    if ambigu:
        return "Plusieurs valeurs possibles pour %s — reprécise-les et je calcule le DTLM." % " et ".join(ambigu)
    if manque:
        return ("Je sais calculer le DTLM, mais il me manque %s. Donne-%s-moi et je te le calcule exactement." %
                (" et ".join(manque), "les" if len(manque) > 1 else "la"))
    if not contre and not co:
        return ("J'ai les 4 températures — il me manque le SENS d'écoulement (contre-courant ou co-courant ?), "
                "il change les ΔT aux bornes.")
    tc_in, tc_out = vals[("chaud", "entre")]["valeur"], vals[("chaud", "sort")]["valeur"]
    tf_in, tf_out = vals[("froid", "entre")]["valeur"], vals[("froid", "sort")]["valeur"]
    dt1, dt2 = (tc_in - tf_out, tc_out - tf_in) if contre else (tc_in - tf_in, tc_out - tf_out)
    if dt1 <= 0 or dt2 <= 0:
        return ("Avec ces températures, un ΔT aux bornes est nul ou négatif (%s et %s) : l'échangeur décrit "
                "est physiquement impossible — vérifie les valeurs." % (_fmt(dt1), _fmt(dt2)))
    dtlm = dt1 if dt1 == dt2 else (dt1 - dt2) / math.log(dt1 / dt2)
    return ("DTLM ≈ %s degrés (approximation à 4 décimales ; formule (ΔT1−ΔT2)/ln(ΔT1/ΔT2), %s : "
            "ΔT1 = %s−%s = %s ; ΔT2 = %s−%s = %s — d'après TES données)." %
            (_fmt(round(dtlm, 4)), "contre-courant" if contre else "co-courant",
             _fmt(tc_in), _fmt(tf_out if contre else tf_in), _fmt(dt1),
             _fmt(tc_out), _fmt(tf_in if contre else tf_out), _fmt(dt2)))


# ── SURFACE D'ÉCHANGE A = Q/(U·ΔTlm) ────────────────────────────────────────────────────────────────────────
_RE_SURFACE = re.compile(r"(?:quelle\s+)?surface\s+(?:d['’][ée]change\s+)?(?:me\s+)?(?:faut|fait)[- ]?(?:il)?|"
                         r"surface\s+d['’][ée]change", re.I)


def _surface(question: str, sit):
    if not _RE_SURFACE.search(question):
        return None
    # les grandeurs de la QUESTION elle-même comptent (« pour 100 kW avec un coefficient de 500 W/m2K ») —
    # extraction DIRECTE (le fil, lui, exclut les interrogatives : une question n'est pas une assertion).
    locales = []
    for mq in _S._RE_GRANDEUR.finditer(question):
        try:
            val = float(mq.group(1).replace(",", "."))
        except ValueError:
            continue
        unite = mq.group(2).lower()
        locales.append({"valeur": val, "unite": unite,
                        "dim": _S._DIMS.get(_S._TOUTES_UNITES.get(unite, ""), "")})
    q_w = next((g["valeur"] * _W_FACT[g["unite"]] for g in locales + _grandeurs_sures(sit)
                if g["dim"] == "puissance"), None)
    u = next((g["valeur"] for g in locales + _grandeurs_sures(sit) if g["dim"] == "coefficient d'échange"), None)
    manque = []
    if q_w is None:
        manque.append("la puissance à échanger (en kW)")
    if u is None:
        manque.append("le coefficient global d'échange U (en W/m²K)")
    # ΔTlm : donné directement… ou calculable depuis les 4 températures du fil
    dtlm_txt = _dtlm("dtlm", sit) if not manque else None
    dtlm_val = None
    if dtlm_txt and dtlm_txt.startswith("DTLM"):
        dtlm_val = float(dtlm_txt.split("≈")[1].split("degrés")[0].strip().replace(",", "."))
    if not manque and dtlm_val is None:
        return ("J'ai Q = %s W et U = %s W/m²K — il me manque le ΔT moyen logarithmique. %s" %
                (_fmt(q_w), _fmt(u), dtlm_txt or "Donne-moi les 4 températures (entrée/sortie des 2 fluides) "
                                                 "et le sens d'écoulement, et je fais tout le calcul."))
    if manque:
        return "Je sais calculer la surface (A = Q/(U·ΔTlm)), mais il me manque %s." % " et ".join(manque)
    a = q_w / (u * dtlm_val)
    return ("Surface ≈ %s m² (approximation ; A = Q/(U·ΔTlm) = %s / (%s × %s) — Q et U de ta demande, "
            "ΔTlm calculé de TES températures)." % (_fmt(round(a, 4)), _fmt(q_w), _fmt(u), _fmt(dtlm_val)))


def repond(question: str, sit):
    """Point d'entrée du PONT : calcul exact depuis les grandeurs énoncées, demande NOMMÉE de l'opérande
    manquant, ou None (hors périmètre — le pipeline continue)."""
    if sit is None:
        return None
    q = str(question or "")
    if not q.strip():
        return None
    for resolveur in (_dtlm, _surface, _ecart):
        try:
            r = resolveur(q, sit)
        except Exception:
            r = None
        if r:
            return r
    return None
