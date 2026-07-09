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

ACTES v1.1 (brique 3 du fil, 2026-07-09 nuit) :
  • « ET SI » : intervention sur UNE grandeur + SIMULATION AVANT dans les mêmes équations (équations
    structurelles) — avant/après montré, fil réel JAMAIS modifié, °C jamais multiplié (échelle non-ratio) ;
  • « POURQUOI » : ordre causal extrait des équations (Iwasaki-Simon), directions q± (Forbus) JAMAIS
    affirmées à la main — PROUVÉES par recalcul à deux points sur les données de l'utilisateur ; prémisse
    fausse CORRIGÉE ; « pourquoi ? » nu -> mécanisme de la dernière réponse du pont (pourquoi_dernier).

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
# Imparfait/conditionnel = les mondes « et si » (« et si le froid sortait à 60 ? »).
_SENS = {"entre": "entre", "entree": "entre", "entrees": "entre", "arrive": "entre",
         "entrait": "entre", "entrerait": "entre", "arrivait": "entre", "arriverait": "entre",
         "sort": "sort", "sortie": "sort", "sorties": "sort", "ressort": "sort",
         "sortait": "sort", "sortirait": "sort", "ressortait": "sort", "ressortirait": "sort"}


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
    # le sens ne se lit JAMAIS dans une hypothèse (« si c'était à contre-courant » ne fixe pas le monde réel)
    reels = [c for c in sit.clauses if not c["hypothese"]]
    contre = any("contre courant" in normalise(c["texte"]) for c in reels)          # normalise ôte le tiret
    co = any(re.search(r"\bco courant", normalise(c["texte"])) for c in reels)
    return slots, manque, ambigu, contre, co


def _dtlm_num(sit, force_sens: str = ""):
    """Cœur NUMÉRIQUE du DTLM (équations structurelles) : {'val', 'dt1', 'dt2', 'contre', températures…} si
    calculable, sinon l'état EXACT de ce qui manque. Sert le texte (_dtlm), la surface (_surface), les mondes
    « et si » (_et_si) et les preuves par recalcul (_pourquoi). `force_sens` (« contre »/« co ») permet de
    comparer les deux sens d'écoulement (« pourquoi le sens compte-t-il ? »)."""
    vals, manque, ambigu, contre, co = _dtlm_operandes(sit)
    if force_sens:
        contre, co = force_sens == "contre", force_sens == "co"
    e = {"val": None, "manque": manque, "ambigu": ambigu, "impossible": None, "contre": bool(contre),
         "sens_manquant": not manque and not ambigu and not contre and not co}
    if manque or ambigu or e["sens_manquant"]:
        return e
    e["tc_in"], e["tc_out"] = vals[("chaud", "entre")]["valeur"], vals[("chaud", "sort")]["valeur"]
    e["tf_in"], e["tf_out"] = vals[("froid", "entre")]["valeur"], vals[("froid", "sort")]["valeur"]
    e["dt1"], e["dt2"] = ((e["tc_in"] - e["tf_out"], e["tc_out"] - e["tf_in"]) if contre
                          else (e["tc_in"] - e["tf_in"], e["tc_out"] - e["tf_out"]))
    if e["dt1"] <= 0 or e["dt2"] <= 0:
        e["impossible"] = (e["dt1"], e["dt2"])
        return e
    e["val"] = e["dt1"] if e["dt1"] == e["dt2"] else (e["dt1"] - e["dt2"]) / math.log(e["dt1"] / e["dt2"])
    return e


def _dtlm(question: str, sit):
    if not _RE_DTLM.search(question):
        return None
    e = _dtlm_num(sit)
    if e["ambigu"]:
        return "Plusieurs valeurs possibles pour %s — reprécise-les et je calcule le DTLM." % " et ".join(e["ambigu"])
    if e["manque"]:
        return ("Je sais calculer le DTLM, mais il me manque %s. Donne-%s-moi et je te le calcule exactement." %
                (" et ".join(e["manque"]), "les" if len(e["manque"]) > 1 else "la"))
    if e["sens_manquant"]:
        return ("J'ai les 4 températures — il me manque le SENS d'écoulement (contre-courant ou co-courant ?), "
                "il change les ΔT aux bornes.")
    if e["impossible"]:
        return ("Avec ces températures, un ΔT aux bornes est nul ou négatif (%s et %s) : l'échangeur décrit "
                "est physiquement impossible — vérifie les valeurs." % (_fmt(e["impossible"][0]), _fmt(e["impossible"][1])))
    contre = e["contre"]
    return ("DTLM ≈ %s degrés (approximation à 4 décimales ; formule (ΔT1−ΔT2)/ln(ΔT1/ΔT2), %s : "
            "ΔT1 = %s−%s = %s ; ΔT2 = %s−%s = %s — d'après TES données)." %
            (_fmt(round(e["val"], 4)), "contre-courant" if contre else "co-courant",
             _fmt(e["tc_in"]), _fmt(e["tf_out"] if contre else e["tf_in"]), _fmt(e["dt1"]),
             _fmt(e["tc_out"]), _fmt(e["tf_in"] if contre else e["tf_out"]), _fmt(e["dt2"])))


# ── SURFACE D'ÉCHANGE A = Q/(U·ΔTlm) ────────────────────────────────────────────────────────────────────────
_RE_SURFACE = re.compile(r"(?:quelle\s+)?surface\s+(?:d['’][ée]change\s+)?(?:me\s+)?(?:faut|fait)[- ]?(?:il)?|"
                         r"surface\s+d['’][ée]change", re.I)


def _q_u(question: str, sit) -> tuple:
    """Q (converti en W) et U, depuis la QUESTION puis le fil — extraction DIRECTE sur la question (le fil,
    lui, exclut les interrogatives : une question n'est pas une assertion)."""
    locales = []
    for mq in _S._RE_GRANDEUR.finditer(question or ""):
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
    return q_w, u


def _surface(question: str, sit):
    if not _RE_SURFACE.search(question):
        return None
    q_w, u = _q_u(question, sit)
    manque = []
    if q_w is None:
        manque.append("la puissance à échanger (en kW)")
    if u is None:
        manque.append("le coefficient global d'échange U (en W/m²K)")
    if manque:
        return "Je sais calculer la surface (A = Q/(U·ΔTlm)), mais il me manque %s." % " et ".join(manque)
    # ΔTlm : calculé depuis les 4 températures du fil (cœur numérique — plus de re-parsing du texte)
    e = _dtlm_num(sit)
    if e["val"] is None:
        return ("J'ai Q = %s W et U = %s W/m²K — il me manque le ΔT moyen logarithmique. %s" %
                (_fmt(q_w), _fmt(u), _dtlm("dtlm", sit) or "Donne-moi les 4 températures (entrée/sortie des "
                                                           "2 fluides) et le sens d'écoulement, et je fais tout le calcul."))
    dtlm_val = round(e["val"], 4)
    a = q_w / (u * dtlm_val)
    return ("Surface ≈ %s m² (approximation ; A = Q/(U·ΔTlm) = %s / (%s × %s) — Q et U de ta demande, "
            "ΔTlm calculé de TES températures)." % (_fmt(round(a, 4)), _fmt(q_w), _fmt(u), _fmt(dtlm_val)))


# ── ROUES DE DÉFINITIONS — moteur GÉNÉRIQUE (généralisation du ②bis, 2026-07-09 jour) ──────────────────────
# Une ROUE = quelques grandeurs liées par des DÉFINITIONS exactes, fermée par SATURATION depuis les grandeurs
# ÉNONCÉES (chaque pas de dérivation NOTÉ et montré). L'électrique (U = R·I / P = U·I) et l'hydraulique
# (Q = S·v : débit volumique = section × vitesse) sont deux INSTANCES du même moteur — mêmes comportements-clés
# partout : dernière valeur fait foi, hypothèses jamais opérandes, manquant DEMANDÉ NOMMÉMENT, et-si simulé
# avant, pourquoi q± prouvé par recalcul. FAUX=0 : chaque relation est une DÉFINITION, jamais un modèle à
# hypothèses cachées (P = Q·Δp hydraulique ÉCARTÉ : une « pression » énoncée n'est pas forcément une
# DIFFÉRENCE de pression) ; les unités sont FILTRÉES par table (un débit MASSIQUE kg/s n'entre jamais dans
# Q = S·v — même dimension « débit » dans le fil, mais pas la même grandeur).
_ROUE_ELEC = {
    "nom": "électrique",
    "dims": ("tension", "courant", "résistance", "puissance"),
    "unites": {"tension": "V", "courant": "A", "résistance": "Ω", "puissance": "W"},
    "fil_dims": {"tension": "tension", "courant": "courant", "résistance": "résistance",
                 "puissance": "puissance"},
    "conv": {"tension": {"v": 1.0, "volt": 1.0, "volts": 1.0, "kv": 1e3},
             "courant": {"ampere": 1.0, "amperes": 1.0, "ampère": 1.0, "ampères": 1.0},
             "résistance": {"ohm": 1.0, "ohms": 1.0},
             "puissance": _W_FACT},
    "ancres": ("tension", "courant", "résistance"),
    "articles": {"tension": "la tension", "courant": "le courant", "résistance": "la résistance",
                 "puissance": "la puissance"},
    "noms": {"tension": "la tension (en volts)", "courant": "le courant (en ampères)",
             "résistance": "la résistance (en ohms)", "puissance": "la puissance (en watts)"},
    "relations": (("tension", ("résistance", "courant"), lambda r, i: r * i, "U = R×I"),
                  ("tension", ("puissance", "courant"), lambda p, i: p / i if i else None, "U = P/I"),
                  ("courant", ("tension", "résistance"), lambda u, r: u / r if r else None, "I = U/R"),
                  ("courant", ("puissance", "tension"), lambda p, u: p / u if u else None, "I = P/U"),
                  ("résistance", ("tension", "courant"), lambda u, i: u / i if i else None, "R = U/I"),
                  ("puissance", ("tension", "courant"), lambda u, i: u * i, "P = U×I")),
    "cible_re": re.compile(
        r"\b(puissance|tension|courant|intensit[ée]|r[ée]sistance)\b.{0,40}\??\s*$|"
        r"^\s*(?:quelle?\s+(?:est\s+)?(?:la\s+|le\s+|l['’])?)?(puissance|tension|courant|intensit[ée]|r[ée]sistance)\b",
        re.I),
    "q_re": re.compile(r"\b(puissance|tension|courant|intensit[ée]|r[ée]sistance)\b", re.I),
    "alias": {"intensite": "courant", "resistance": "résistance"},
    "cible_defaut": "puissance",
    "devise": "roue U = R·I, P = U·I",
    "deps": {
        "puissance": "P = U·I (énergie par seconde = tension × débit de charges) ; et comme U = R·I "
                     "(loi d'Ohm), elle s'écrit aussi P = R·I² ou P = U²/R",
        "tension": "U = R·I (loi d'Ohm) — ou U = P/I depuis la puissance",
        "courant": "I = U/R (loi d'Ohm) — ou I = P/U depuis la puissance",
        "résistance": "R = U/I (loi d'Ohm : la résistance est le rapport tension/courant)",
    },
    "paire_exemple": "la puissance ou la résistance",
}

_ROUE_HYDRO = {
    "nom": "hydraulique",
    "dims": ("débit", "section", "vitesse"),
    "unites": {"débit": "m³/s", "section": "m²", "vitesse": "m/s"},
    "fil_dims": {"débit": "débit", "aire": "section", "vitesse": "vitesse"},
    "conv": {"débit": {"m3/s": 1.0, "m³/s": 1.0, "m3/h": 1.0 / 3600, "m³/h": 1.0 / 3600,
                       "l/s": 1e-3, "l/min": 1.0 / 60000, "l/h": 1.0 / 3.6e6},
             "section": {"m2": 1.0, "m²": 1.0, "metre carre": 1.0, "metres carres": 1.0,
                         "cm2": 1e-4, "cm²": 1e-4, "centimetre carre": 1e-4, "centimetres carres": 1e-4,
                         "mm2": 1e-6, "mm²": 1e-6},
             "vitesse": {"m/s": 1.0, "m s": 1.0, "metre par seconde": 1.0, "metres par seconde": 1.0,
                         "km/h": 1.0 / 3.6, "km h": 1.0 / 3.6, "kmh": 1.0 / 3.6,
                         "kilometre heure": 1.0 / 3.6, "kilometres heure": 1.0 / 3.6,
                         "kilometre par heure": 1.0 / 3.6, "kilometres par heure": 1.0 / 3.6}},
    "ancres": ("débit", "section"),                       # la vitesse SEULE n'ancre pas (une voiture roule aussi)
    "articles": {"débit": "le débit", "section": "la section", "vitesse": "la vitesse"},
    "noms": {"débit": "le débit (en m³/s ou l/s)", "section": "la section (en m² ou cm²)",
             "vitesse": "la vitesse d'écoulement (en m/s)"},
    "relations": (("débit", ("section", "vitesse"), lambda s, v: s * v, "Q = S×v"),
                  ("section", ("débit", "vitesse"), lambda q, v: q / v if v else None, "S = Q/v"),
                  ("vitesse", ("débit", "section"), lambda q, s: q / s if s else None, "v = Q/S")),
    "cible_re": re.compile(
        r"\b(d[ée]bit|section|vitesse)\b.{0,40}\??\s*$|"
        r"^\s*(?:quel(?:le)?\s+(?:est\s+)?(?:la\s+|le\s+|l['’])?)?(d[ée]bit|section|vitesse)\b", re.I),
    "q_re": re.compile(r"\b(d[ée]bit|section|vitesse)\b", re.I),
    "alias": {"debit": "débit"},
    "cible_defaut": "débit",
    "devise": "roue Q = S·v",
    "deps": {
        "débit": "Q = S·v (le débit volumique est, par définition, la section de passage × la vitesse "
                 "d'écoulement)",
        "section": "S = Q/v (la section de passage est le rapport débit/vitesse)",
        "vitesse": "v = Q/S (la vitesse d'écoulement est le rapport débit/section)",
    },
    "paire_exemple": "le débit",
}

_ROUES = (_ROUE_ELEC, _ROUE_HYDRO)


def _liste_ou(noms: list) -> str:
    """« a, b ou c » — l'énumération des demandes nommées."""
    return noms[0] if len(noms) == 1 else ", ".join(noms[:-1]) + " ou " + noms[-1]


def _vals_roue(sit, roue: dict, question: str = "") -> dict:
    """Les grandeurs de la roue UTILISABLES (fil sûr + question), dernière valeur par dimension fait foi,
    converties en unité SI de la roue. FILTRE PAR TABLE D'UNITÉS : une unité hors table (kg/s massique pour
    l'hydraulique, hectare pour une section de conduite) n'entre JAMAIS comme opérande."""
    locales = []
    for mq in _S._RE_GRANDEUR.finditer(question or ""):
        try:
            val = float(mq.group(1).replace(",", "."))
        except ValueError:
            continue
        unite = mq.group(2).lower()
        locales.append({"valeur": val, "unite": unite,
                        "dim": _S._DIMS.get(_S._TOUTES_UNITES.get(unite, ""), "")})
    vals = {}
    for g in _grandeurs_sures(sit) + locales:
        rdim = roue["fil_dims"].get(g["dim"])
        if not rdim:
            continue
        f = roue["conv"][rdim].get(g["unite"])
        if f is None:
            continue
        vals[rdim] = g["valeur"] * f
    return vals


def _roue_resout(vals: dict, roue: dict) -> tuple:
    """Ferme la roue par SATURATION (divisions par zéro écartées par les relations). -> (valeurs, chemins)."""
    v, chemins = dict(vals), []
    for _ in range(max(1, len(roue["dims"]) - 1)):
        for cible, ops, fn, label in roue["relations"]:
            if cible in v or not all(o in v for o in ops):
                continue
            r = fn(*[v[o] for o in ops])
            if r is None:
                continue
            v[cible] = r
            chemins.append(label)
    return v, chemins


def _roue_repond(question: str, sit, roue: dict):
    """Calcul de roue depuis les grandeurs ÉNONCÉES. Ne s'engage que si une grandeur d'ANCRAGE du domaine est
    énoncée (« quelle puissance passe dans l'échangeur ? » n'est pas pour l'électrique ; « à quelle vitesse
    roule le TGV ? » n'est pas pour l'hydraulique). Opérande manquant -> demandé NOMMÉMENT."""
    m = roue["cible_re"].search(question)
    if not m:
        return None
    cible = normalise(m.group(1) or m.group(2) or "")
    cible = roue["alias"].get(cible, cible)
    if cible not in roue["dims"]:
        return None
    vals = _vals_roue(sit, roue, question)
    if not any(d in vals for d in roue["ancres"]):
        return None                                       # aucun ancrage du domaine : pas pour moi
    ferme, chemins = _roue_resout(vals, roue)
    if cible not in ferme:
        manque = [d for d in roue["dims"] if d not in ferme and d != cible]
        return ("Je sais calculer %s (%s), mais il me manque une donnée : donne-moi %s "
                "et je calcule exactement." % (roue["articles"][cible], roue["devise"],
                                               " ou ".join(roue["noms"][d] for d in manque[:2])))
    donnees = ", ".join("%s = %s %s" % (d, _fmt(vals[d]), roue["unites"][d]) for d in roue["dims"] if d in vals)
    deriv = " ; ".join(chemins) if chemins else "donnée énoncée telle quelle"
    return ("%s ≈ %s %s (%s — d'après ce que tu m'as donné : %s)." %
            (cible[:1].upper() + cible[1:], _fmt(round(ferme[cible], 4)), roue["unites"][cible], deriv, donnees))


def _electrique(question: str, sit):
    """La roue électrique (instance du moteur générique — signature conservée)."""
    return _roue_repond(question, sit, _ROUE_ELEC)


def _hydraulique(question: str, sit):
    """La roue hydraulique Q = S·v (instance du moteur générique)."""
    return _roue_repond(question, sit, _ROUE_HYDRO)


# ── « ET SI » : monde contrefactuel = intervention + SIMULATION AVANT (brique 3 du fil) ────────────────────
# Théorie (recherche 2026-07-09) : un contrefactuel = intervenir sur UNE variable puis re-propager dans les
# MÊMES équations (équations structurelles, Pearl) — le registre fermé du pont (DTLM ← 4 temp + sens ;
# A ← Q, U, ΔTlm) est déjà un modèle causal structurel. FAUX=0 : le fil RÉEL n'est jamais modifié (le monde
# hypothétique est JETÉ après la réponse), la réponse est étiquetée « dans ton hypothèse », l'avant/après est
# montré dès que les deux mondes sont calculables.
_RE_ETSI = re.compile(r"^\s*(?:et|mais)\s+si\s+(.+)$", re.I | re.S)
_RE_QUE_DEVIENT = re.compile(r"^\s*que\s+devien(?:t|drait)\s+(.+?)\s+si\s+(.+?)\s*\??\s*$", re.I | re.S)
_RE_MULT_PCT = re.compile(
    r"(augmentait|montait|grimpait|baissait|diminuait|chutait|r[ée]duisait)\s+de\s+(\d+(?:[.,]\d+)?)\s*%", re.I)
_MULTS = [(re.compile(r"\bdoubl", re.I), 2.0), (re.compile(r"\btripl", re.I), 3.0),
          (re.compile(r"\bquadrupl", re.I), 4.0),
          (re.compile(r"moiti[ée]|divis\w+\s+par\s+(?:2\b|deux\b)", re.I), 0.5)]


def _cible_de(txt: str):
    """La grandeur-CIBLE nommée dans un bout de question (registre fermé) — None si aucune."""
    if not (txt or "").strip():
        return None
    if _RE_DTLM.search(txt):
        return "dtlm"
    t = normalise(txt)
    if "surface" in t:
        return "surface"
    if "ecart" in t or "difference" in t:
        return "ecart"
    return None


def _monde_hypothetique(sit, clause: str):
    """Le monde « et si » : les clauses réelles + la clause hypothétique AFFIRMÉE (dans ce monde-là, elle est
    vraie). JETÉ après la réponse — le fil réel n'est jamais modifié (une hypothèse n'est pas promue)."""
    cf = _S.Situation()
    cf.clauses = list(sit.clauses)                                   # partagé en lecture : on ne fait qu'ajouter
    seq = max([c["seq"] for c in sit.clauses], default=0) + 1
    n = cf.apprend(seq, clause)
    for c in cf.clauses[len(sit.clauses):]:
        c["hypothese"] = False
    return cf, n


def _etsi_thermique(sit, cf, hyp: str, cible_txt: str, cible, implicite: bool):
    """Hypothèse sur une TEMPÉRATURE de slot -> DTLM re-propagé (+ surface si Q et U connus), avant/après."""
    avant, apres = _dtlm_num(sit), _dtlm_num(cf)
    etiquette = "Dans ton hypothèse (%s%s)" % (hyp, " — degrés implicites" if implicite else "")
    if cible == "ecart" and _RE_ECART.search(cible_txt):
        r = _ecart(cible_txt, cf)
        return "%s : %s" % (etiquette, r) if r else None
    if apres["impossible"]:
        return ("%s, un ΔT aux bornes devient nul ou négatif (%s et %s) : cet échangeur serait physiquement "
                "impossible — l'hypothèse ne tient pas." %
                (etiquette, _fmt(apres["impossible"][0]), _fmt(apres["impossible"][1])))
    if apres["val"] is None:
        if apres["sens_manquant"]:
            return ("%s, j'aurais les 4 températures — mais il me manque toujours le SENS d'écoulement "
                    "(contre-courant ou co-courant ?)." % etiquette)
        return ("%s, il me manquerait encore %s. Donne-%s-moi et je simule." %
                (etiquette, " et ".join(apres["manque"]), "les" if len(apres["manque"]) > 1 else "la"))
    lignes = ["DTLM ≈ %s degrés%s (%s : ΔT1 = %s ; ΔT2 = %s)" % (
        _fmt(round(apres["val"], 4)),
        (" au lieu de %s avec tes données réelles" % _fmt(round(avant["val"], 4)))
        if avant["val"] is not None and abs(avant["val"] - apres["val"]) > 1e-9 else "",
        "contre-courant" if apres["contre"] else "co-courant", _fmt(apres["dt1"]), _fmt(apres["dt2"]))]
    q_w, u = _q_u(cible_txt, sit)
    if q_w is not None and u is not None:
        a1 = q_w / (u * apres["val"])
        aussi = ""
        if avant["val"] is not None and abs(avant["val"] - apres["val"]) > 1e-9:
            aussi = " au lieu de %s m²" % _fmt(round(q_w / (u * avant["val"]), 4))
        lignes.append("Surface ≈ %s m²%s (A = Q/(U·ΔTlm), Q = %s W, U = %s W/m²K)" %
                      (_fmt(round(a1, 4)), aussi, _fmt(q_w), _fmt(u)))
    elif cible == "surface":
        manque = ([] if q_w is not None else ["la puissance à échanger (en kW)"]) + \
                 ([] if u is not None else ["le coefficient global d'échange U (en W/m²K)"])
        lignes.append("pour la surface, il me manque %s" % " et ".join(manque))
    note = (" Ton fil réel, lui, n'a pas cette donnée — affirme-la sans « si » et je la retiens."
            if avant["val"] is None else
            " Le fil réel reste inchangé (une hypothèse n'est jamais promue) — affirme-la si tu veux que je la retienne.")
    return "%s : %s.%s" % (etiquette, " ; ".join(lignes), note)


def _etsi_surface(sit, hyp: str, cible_txt: str, q_val=None, u_val=None, d_val=None,
                  q_fact=None, u_fact=None, d_fact=None):
    """Hypothèse sur Q, U ou ΔTlm (valeur cible ou multiplicateur) -> surface re-propagée, avant/après.
    Les valeurs RÉELLES viennent du fil (+ de la partie question HORS hypothèse) ; la modification, de l'hypothèse seule."""
    q0, u0 = _q_u(cible_txt, sit)
    d0 = _dtlm_num(sit)["val"]
    etiquette = "Dans ton hypothèse (%s)" % hyp
    if q_fact is not None and q0 is None:
        return ("%s : il me manque la puissance RÉELLE à multiplier — donne-la (« la puissance est de "
                "100 kW ») et je simule." % etiquette)
    if u_fact is not None and u0 is None:
        return "%s : il me manque le coefficient d'échange RÉEL à multiplier — donne-le et je simule." % etiquette
    if d_fact is not None and d0 is None:
        return ("%s : je ne connais pas le ΔTlm réel à multiplier — donne-moi les 4 températures et le sens "
                "d'écoulement, et je simule." % etiquette)
    q1 = q_val if q_val is not None else (q0 * q_fact if q_fact is not None else q0)
    u1 = u_val if u_val is not None else (u0 * u_fact if u_fact is not None else u0)
    d1 = d_val if d_val is not None else (d0 * d_fact if d_fact is not None else d0)
    manque = ([] if q1 is not None else ["la puissance à échanger (en kW)"]) + \
             ([] if u1 is not None else ["le coefficient global d'échange U (en W/m²K)"]) + \
             ([] if d1 is not None else ["le ΔT moyen logarithmique (ou les 4 températures + le sens d'écoulement)"])
    if manque:
        return "%s : je sais simuler la surface (A = Q/(U·ΔTlm)), mais il me manque %s." % (etiquette, " et ".join(manque))
    if d1 <= 0:
        return "%s : un ΔTlm nul ou négatif n'a pas de sens physique — la surface n'est pas définie." % etiquette
    a1 = q1 / (u1 * d1)
    avant = ""
    if None not in (q0, u0, d0):
        a0 = q0 / (u0 * d0)
        if abs(a0 - a1) > 1e-9:
            avant = " au lieu de %s m² avec tes données réelles" % _fmt(round(a0, 4))
    return ("%s : surface ≈ %s m²%s (A = Q/(U·ΔTlm) = %s / (%s × %s)). Le fil réel reste inchangé — affirme "
            "la nouvelle valeur si tu veux que je la retienne." %
            (etiquette, _fmt(round(a1, 4)), avant, _fmt(q1), _fmt(u1), _fmt(round(d1, 4))))


def _etsi_roue(sit, hyp: str, cible_txt: str, roue: dict):
    """Hypothèse sur une grandeur de roue -> la roue re-fermée dans le monde hypothétique, avant/après montré.
    None sans ancrage du domaine dans le monde hypothétique (« et si la voiture roulait à 3 m/s » n'est pas
    pour l'hydraulique)."""
    cf, n = _monde_hypothetique(sit, hyp)
    if not n:
        return None
    m = roue["cible_re"].search(cible_txt or "")
    cible = normalise((m.group(1) or m.group(2)) if m else roue["cible_defaut"])
    cible = roue["alias"].get(cible, cible)
    if cible not in roue["dims"]:
        cible = roue["cible_defaut"]
    ap_vals = _vals_roue(cf, roue)
    if not any(d in ap_vals for d in roue["ancres"]):
        return None
    av, _ = _roue_resout(_vals_roue(sit, roue), roue)
    ap, chemins = _roue_resout(ap_vals, roue)
    etiquette = "Dans ton hypothèse (%s)" % hyp
    if cible not in ap:
        return ("%s, il me manque encore de quoi fermer le calcul — donne-moi %s." %
                (etiquette, _liste_ou([roue["noms"][d] for d in roue["ancres"]])))
    lieu = (" au lieu de %s %s avec tes données réelles" % (_fmt(round(av[cible], 4)), roue["unites"][cible])) \
        if cible in av and abs(av[cible] - ap[cible]) > 1e-9 else ""
    return ("%s : %s ≈ %s %s%s (%s). Le fil réel reste inchangé — affirme la nouvelle valeur si tu veux "
            "que je la retienne." % (etiquette, cible[:1].upper() + cible[1:], _fmt(round(ap[cible], 4)),
                                     roue["unites"][cible], lieu, " ; ".join(chemins) or "donnée énoncée"))


def _et_si(question: str, sit):
    """Acte « et si … » : intervention sur une grandeur + re-propagation. None si la modification n'est pas
    du registre (jamais de capture des « et si on allait à la plage ? »)."""
    q = str(question or "").strip()
    m = _RE_QUE_DEVIENT.match(q)
    if m:
        cible_txt, hyp = m.group(1).strip(), m.group(2).strip()
    else:
        m = _RE_ETSI.match(q)
        if not m:
            return None
        reste = m.group(1).rstrip(" ?").strip()
        parts = re.split(r"\s*[,;:—]\s*|\s+(?=quel(?:le)?s?\b|combien\b|que\s+devien)", reste, maxsplit=1)
        hyp = parts[0].strip()
        cible_txt = parts[1].strip() if len(parts) > 1 else ""
    cible = _cible_de(cible_txt)
    hyp_n = normalise(hyp)
    # 1) MULTIPLICATEUR (« doublait la puissance », « baissait de 20 % ») — registre fermé
    fact = None
    mp = _RE_MULT_PCT.search(hyp)
    if mp:
        pct = float(mp.group(2).replace(",", "."))
        fact = 1 + pct / 100 if normalise(mp.group(1)).startswith(("augment", "mont", "grimp")) else 1 - pct / 100
    else:
        fact = next((f for rx, f in _MULTS if rx.search(hyp)), None)
    if fact is not None:
        if "puissance" in hyp_n:
            return _etsi_surface(sit, hyp, cible_txt, q_fact=fact)
        if "coefficient" in hyp_n:
            return _etsi_surface(sit, hyp, cible_txt, u_fact=fact)
        if _RE_DTLM.search(hyp):
            return _etsi_surface(sit, hyp, cible_txt, d_fact=fact)
        if "debit" in hyp_n:
            return ("Le débit n'entre dans aucun de mes calculs fermés (DTLM, surface d'échange) — je ne "
                    "simule pas un effet que je ne sais pas calculer exactement.")
        if "temperature" in hyp_n or "degre" in hyp_n or re.search(r"\b(?:chaud|froid)\b", hyp_n):
            return ("Multiplier une température en degrés n'a pas de sens physique (échelle non-ratio : "
                    "40 °C n'est pas « deux fois plus chaud » que 20 °C). Donne-moi la valeur cible "
                    "(« et si le fluide chaud entrait à 95 degrés ») et je re-calcule.")
        return None                                                   # « et si on doublait la mise ? » : pas pour moi
    # 2) REMPLACEMENT DE VALEUR — il faut un nombre ET un ancrage du registre
    if not re.search(r"\d", hyp):
        return None
    grs = []
    for mg in _S._RE_GRANDEUR.finditer(hyp):
        try:
            val = float(mg.group(1).replace(",", "."))
        except ValueError:
            continue
        unite = mg.group(2).lower()
        grs.append((val, unite, _S._DIMS.get(_S._TOUTES_UNITES.get(unite, ""), "")))
    dims = {d for _, _, d in grs}
    slot_thermique = bool(re.search(r"\b(?:chaud|froid)\b", hyp_n)) and any(t in _SENS for t in _S._toks(hyp))
    if slot_thermique and ("température" in dims or not dims):
        implicite = "température" not in dims
        clause = hyp if not implicite else re.sub(r"(-?\d+(?:[.,]\d+)?)(?![\w%€])(?![.,]\d)", r"\1 degrés", hyp)
        cf, n = _monde_hypothetique(sit, clause)
        if not n:
            return None
        return _etsi_thermique(sit, cf, hyp, cible_txt, cible, implicite)
    if _RE_DTLM.search(hyp):                                          # « et si le DTLM était de 30 »
        mv = re.search(r"(-?\d+(?:[.,]\d+)?)", hyp)
        return _etsi_surface(sit, hyp, cible_txt, d_val=float(mv.group(1).replace(",", ".")))
    if "puissance" in dims:
        q_val = next(v * _W_FACT[u] for v, u, d in grs if d == "puissance")
        return _etsi_surface(sit, hyp, cible_txt, q_val=q_val)
    if "coefficient d'échange" in dims:
        return _etsi_surface(sit, hyp, cible_txt,
                             u_val=next(v for v, u, d in grs if d == "coefficient d'échange"))
    if dims & {"tension", "courant", "résistance"}:       # ②bis : et-si électrique (même simulation avant)
        return _etsi_roue(sit, hyp, cible_txt, _ROUE_ELEC)
    if dims & {"débit", "aire", "vitesse"}:               # et-si hydraulique (Q = S·v) — ancrage vérifié dedans
        return _etsi_roue(sit, hyp, cible_txt, _ROUE_HYDRO)
    return None


# ── « POURQUOI » : explication CAUSALE depuis les équations fermées (brique 3 du fil) ──────────────────────
# Théorie : l'ordre causal s'EXTRAIT de la structure des équations (Iwasaki-Simon 1986) ; la direction d'une
# influence est une proportionnalité qualitative q± (Forbus, qualitative process theory) — avec le twist
# machine : la direction n'est JAMAIS affirmée à la main, elle est PROUVÉE PAR RECALCUL à deux points sur les
# données de l'utilisateur (valeurs montrées). Prémisse fausse -> CORRIGÉE, jamais validée.
_RE_PQ_DEP = re.compile(
    r"^\s*de\s+quoi\s+d[ée]pend(?:ent)?\s+(.+?)\s*\??\s*$|"
    r"^\s*(?:mais\s+)?pourquoi\s+(.+?)\s+d[ée]pend(?:[- ](?:elle|il|t[- ](?:elle|il)))?\s+(?:de|du|des)\s+.+$", re.I)
_RE_PQ_SENS = re.compile(r"^\s*(?:mais\s+)?pourquoi\b.{0,60}\b(?:sens\b|contre[- ]courant|co[- ]courant)", re.I)
_RE_PQ_DIR = re.compile(
    r"^\s*(?:mais\s+)?pourquoi\s+(?:est[- ]ce\s+que\s+)?(.+?)\s+(?:quand|lorsque|si|alors\s+que)\s+(.+?)\s*\??\s*$", re.I)
_MONTE = ("augmente", "monte", "grandit", "grimpe")
_DESCEND = ("baisse", "diminue", "chute", "descend")
_SIGNE_SURFACE = {"dtlm": -1, "puissance": 1, "coefficient": -1}     # q± lus dans A = Q/(U·ΔTlm)

_DEP_SURFACE = ("La surface d'échange se déduit de la définition du coefficient U : Q = U·A·ΔTlm, donc "
                "A = Q/(U·ΔTlm). Elle dépend de trois grandeurs : la puissance Q à faire passer "
                "(proportionnelle — Q au numérateur), le coefficient d'échange U (inverse — U au dénominateur) "
                "et l'écart moyen logarithmique ΔTlm (inverse aussi). ΔTlm dépend lui-même des 4 températures "
                "d'entrée/sortie des deux fluides ET du sens d'écoulement — c'est l'ordre causal complet.")
_DEP_DTLM = ("Le DTLM dépend des 4 températures (entrée/sortie des deux fluides) et du SENS d'écoulement : "
             "contre-courant -> ΔT1 = Tc,entrée − Tf,sortie et ΔT2 = Tc,sortie − Tf,entrée ; co-courant -> "
             "ΔT1 = Tc,entrée − Tf,entrée et ΔT2 = Tc,sortie − Tf,sortie ; puis (ΔT1−ΔT2)/ln(ΔT1/ΔT2).")
_EXPL_SURFACE = {
    "dtlm": "le ΔTlm est au DÉNOMINATEUR de A = Q/(U·ΔTlm) : chaque m² transfère U·ΔTlm watts — un écart "
            "moyen plus faible fait passer moins par m², il faut donc plus de surface pour la même puissance",
    "puissance": "Q est au NUMÉRATEUR de A = Q/(U·ΔTlm) : à U et ΔTlm fixés, la surface est strictement "
                 "proportionnelle à la puissance à faire passer",
    "coefficient": "U est au DÉNOMINATEUR de A = Q/(U·ΔTlm) : un meilleur coefficient d'échange fait passer "
                   "plus de watts par m², donc moins de surface pour la même puissance",
}


def _dir_de(txt: str) -> int:
    t = normalise(txt)
    if any(w in t for w in _MONTE):
        return 1
    if any(w in t for w in _DESCEND):
        return -1
    return 0


def _var_de(txt: str):
    """La variable-INFLUENCE nommée (registre fermé de A = Q/(U·ΔTlm))."""
    if _RE_DTLM.search(txt):
        return "dtlm"
    t = normalise(txt)
    if "puissance" in t:
        return "puissance"
    if "coefficient" in t:
        return "coefficient"
    return None


def _preuve_surface(sit, var: str, dir_v: int) -> str:
    """Preuve PAR RECALCUL de l'effet de `var` sur la surface, aux données de l'utilisateur (deux points)."""
    q_w, u = _q_u("", sit)
    d = _dtlm_num(sit)["val"]
    if None in (q_w, u, d):
        return " (Donne-moi Q, U et les 4 températures + le sens, et je te le prouve par recalcul sur TES chiffres.)"
    a0 = q_w / (u * d)
    f = 1.2 if dir_v > 0 else 0.8
    q1, u1, d1 = (q_w * f if var == "puissance" else q_w), (u * f if var == "coefficient" else u), \
                 (d * f if var == "dtlm" else d)
    a1 = q1 / (u1 * d1)
    nom = {"dtlm": "ΔTlm", "puissance": "Q", "coefficient": "U"}[var]
    v0 = {"dtlm": d, "puissance": q_w, "coefficient": u}[var]
    return (" Preuve par recalcul sur TES données : %s = %s -> A ≈ %s m² ; %s = %s -> A ≈ %s m²." %
            (nom, _fmt(round(v0, 4)), _fmt(round(a0, 4)), nom, _fmt(round(v0 * f, 4)), _fmt(round(a1, 4))))


def _pourquoi_dtlm_slot(sit, v_part: str, dir_v: int):
    """Effet d'une température de slot sur le DTLM : MESURÉ par perturbation (±5°) et recalcul — jamais une
    tendance affirmée sans preuve."""
    t = {_SENS.get(x, x) for x in _S._toks(v_part)}
    fl = "chaud" if "chaud" in t else ("froid" if "froid" in t else None)
    sens = next((x for x in t if x in ("entre", "sort")), None)
    if not fl or not sens:
        return None
    e0 = _dtlm_num(sit)
    if e0["val"] is None:
        return ("Je ne fais pas d'affirmation de tendance sans preuve : donne-moi les 4 températures et le "
                "sens d'écoulement, et je te montre l'effet de %s par recalcul sur TES chiffres." %
                _LIBELLES_SLOT[(fl, sens)])
    delta = 5.0 if (dir_v or 1) > 0 else -5.0
    v0 = {"chaud": {"entre": e0["tc_in"], "sort": e0["tc_out"]},
          "froid": {"entre": e0["tf_in"], "sort": e0["tf_out"]}}[fl][sens]
    cf, _ = _monde_hypothetique(sit, "le fluide %s %s à %s degrés" %
                                (fl, "entre" if sens == "entre" else "sort", repr(v0 + delta)))
    e1 = _dtlm_num(cf)
    if e1["impossible"]:
        return ("Effet mesuré sur TES données : %s = %s -> DTLM ≈ %s degrés ; à %s, un ΔT de borne devient "
                "nul ou négatif — l'échangeur cesserait d'être physiquement possible." %
                (_LIBELLES_SLOT[(fl, sens)], _fmt(v0), _fmt(round(e0["val"], 4)), _fmt(v0 + delta)))
    if e1["val"] is None:
        return None
    monte = e1["val"] > e0["val"] + 1e-12
    return ("Effet PROUVÉ par recalcul sur TES données (je ne déclare pas une tendance, je la mesure) : "
            "%s = %s -> DTLM ≈ %s degrés ; à %s -> DTLM ≈ %s degrés : il %s. Mécanisme : cette température "
            "entre dans un ΔT de borne de la formule (ΔT1−ΔT2)/ln(ΔT1/ΔT2)." %
            (_LIBELLES_SLOT[(fl, sens)], _fmt(v0), _fmt(round(e0["val"], 4)),
             _fmt(v0 + delta), _fmt(round(e1["val"], 4)), "monte" if monte else "baisse"))


# ── POURQUOI-ROUE contentful (q± générique — né électrique, 2026-07-09) ────────────────────────────────────
# Théorie (de Kleer, confluences) : sur une roue de définitions, une direction q± N'EXISTE PAS dans l'absolu —
# elle dépend de CE QUI EST TENU CONSTANT. Le twist machine FAUX=0 : les constantes ne sont jamais choisies par
# heuristique, ce sont les données ÉNONCÉES par l'utilisateur (ordre causal d'Iwasaki-Simon : l'exogène = le
# donné). Même question « pourquoi I baisse quand U monte ? » -> réponses OPPOSÉES selon que le fil porte (U, I)
# (deux données indépendantes) ou (P, U) (I = P/U, prouvé par recalcul 2 points).
def _var_roue_de(txt: str, roue: dict):
    """La grandeur de la roue nommée dans un bout de question (registre fermé) — None si aucune."""
    m = roue["q_re"].search(txt or "")
    if not m:
        return None
    v = normalise(m.group(1))
    return roue["alias"].get(v, v)


def _pourquoi_roue_dep(sit, cible, roue: dict):
    """« De quoi dépend la puissance ? » en contexte de roue : les définitions + l'ordre causal RÉEL du fil
    (les données énoncées sont les racines — c'est d'elles que tout dérive, chemins montrés)."""
    if cible not in roue["deps"]:
        return None
    vals = _vals_roue(sit, roue)
    if not any(d in vals for d in roue["ancres"]):
        return None                                           # aucun ancrage du domaine : pas pour moi
    ferme, chemins = _roue_resout({k: v for k, v in vals.items() if k != cible}, roue)
    art = roue["articles"]
    donnees = ", ".join("%s = %s %s" % (d, _fmt(vals[d]), roue["unites"][d]) for d in roue["dims"]
                        if d in vals and d != cible)
    reponse = "%s se déduit de la roue des définitions : %s." % (
        art[cible][:1].upper() + art[cible][1:], roue["deps"][cible])
    if cible in ferme and donnees:
        via = " ; ".join(chemins) if chemins else "donnée énoncée telle quelle"
        reponse += (" Dans TES données, les racines causales sont ce que tu m'as donné (%s) : c'est de là que "
                    "tout dérive — ici %s ≈ %s %s via %s." %
                    (donnees, art[cible], _fmt(round(ferme[cible], 4)), roue["unites"][cible], via))
    elif cible in vals:                                       # la cible est LEUR donnée : une racine, pas une dérivée
        reponse += (" Dans TES données, %s est justement une RACINE causale : tu me l'as donné%s directement "
                    "(%s %s) — rien ne le dérive ici, c'est de lui que le reste peut dériver." %
                    (art[cible], "e" if art[cible].startswith("la ") else "",
                     _fmt(vals[cible]), roue["unites"][cible]))
    elif donnees:
        reponse += (" Avec tes données (%s), je ne peux pas encore la fermer — donne-moi une grandeur de plus "
                    "de la roue et je te montre la dérivation exacte." % donnees)
    return reponse


def _pourquoi_roue_dir(sit, c_part: str, v_part: str, roue: dict):
    """Direction d'influence sur la roue, PROUVÉE par recalcul 2 points sur les données énoncées — les autres
    données de l'utilisateur tenues constantes (et DITES constantes). Prémisse fausse -> corrigée. Grandeur
    d'influence DÉRIVÉE (pas énoncée) -> dit honnêtement + demande laquelle des données change."""
    cible, var = _var_roue_de(c_part, roue), _var_roue_de(v_part, roue)
    if not cible or not var or cible == var or cible not in roue["dims"] or var not in roue["dims"]:
        return None
    vals = _vals_roue(sit, roue)
    if not any(d in vals for d in roue["ancres"]):
        return None
    art, unites = roue["articles"], roue["unites"]
    dir_c, dir_v = _dir_de(c_part), _dir_de(v_part)
    if not dir_v:
        return None
    if var not in vals:                                       # influence non énoncée : dérivée ou absente
        ferme, chemins = _roue_resout(vals, roue)
        if var in ferme:
            return ("Cette grandeur (%s), tu ne me l'as pas donnée : je l'ai DÉRIVÉE de tes données "
                    "(%s ≈ %s %s, via %s). La faire varier, c'est changer une de TES données — dis-moi "
                    "laquelle bouge (%s) et je mesure l'effet par recalcul." %
                    (art[var], art[var], _fmt(round(ferme[var], 4)), unites[var],
                     " ; ".join(chemins) or "donnée énoncée",
                     " ou ".join(art[d] for d in vals if d in roue["dims"])))
        return ("Je ne connais pas %s de ton installation — donne-la-moi (ou donne-moi de quoi la dériver) et "
                "je te prouve l'effet par recalcul sur TES chiffres." % art[var])
    base = {k: v for k, v in vals.items() if k != cible}
    f0, _ch0 = _roue_resout(base, roue)
    if cible not in f0:
        if cible in vals:                                     # la cible est LEUR donnée : indépendante chez eux
            return ("Dans TES données, %s ne dépend PAS de %s : tu m'as donné les deux séparément (%s = %s %s), "
                    "ce sont deux données indépendantes de ton énoncé. %s dépendrait de %s si tu me donnais "
                    "plutôt une autre paire de la roue (par exemple %s)." %
                    (art[cible], art[var], cible, _fmt(vals[cible]), unites[cible],
                     art[cible][:1].upper() + art[cible][1:], art[var], roue["paire_exemple"]))
        return ("Je sais prouver ce genre d'effet par recalcul, mais il me manque de quoi fermer %s depuis "
                "tes données — donne-moi une grandeur de plus de la roue (%s)." %
                (art[cible], ", ".join(roue["dims"])))
    f = 1.2 if dir_v > 0 else 0.8
    base1 = dict(base)
    base1[var] = base[var] * f
    f1, ch1 = _roue_resout(base1, roue)
    if cible not in f1:
        return None
    v0, v1 = f0[cible], f1[cible]
    attendu = 0 if abs(v1 - v0) < 1e-12 else (1 if v1 > v0 else -1)
    tenus = [d for d in base if d != var]
    constantes = (" — à %s constante%s (tes autres données)" %
                  (" et ".join(art[d] for d in tenus), "s" if len(tenus) > 1 else "")) if tenus else ""
    preuve = ("%s = %s %s -> %s ≈ %s %s ; %s = %s %s -> %s ≈ %s %s" %
              (var, _fmt(base[var]), unites[var], cible, _fmt(round(v0, 4)), unites[cible],
               var, _fmt(round(base1[var], 4)), unites[var], cible, _fmt(round(v1, 4)), unites[cible]))
    mecanisme = " ; ".join(ch1) if ch1 else "donnée énoncée"
    if attendu == 0:
        return ("Effet mesuré sur TES données%s : %s — %s ne bouge pas. Mécanisme : %s." %
                (constantes, preuve, art[cible], mecanisme))
    verbe = "AUGMENTE" if attendu > 0 else "DIMINUE"
    if dir_c and dir_c != attendu:                            # prémisse FAUSSE -> corrigée, jamais validée
        return ("Ce n'est pas ce qui se passe : quand %s %s%s, %s %s. Preuve par recalcul sur TES données : "
                "%s. Mécanisme : %s." %
                (art[var], "augmente" if dir_v > 0 else "baisse", constantes, art[cible], verbe,
                 preuve, mecanisme))
    return ("Effet PROUVÉ par recalcul sur TES données (je ne déclare pas une tendance, je la mesure)%s : "
            "%s — %s %s. Mécanisme : %s." % (constantes, preuve, art[cible], verbe, mecanisme))


def _pourquoi(question: str, sit):
    """Acte « pourquoi » : ordre causal, effet du sens d'écoulement, ou direction d'influence PROUVÉE.
    None dès que la question sort du registre (« pourquoi le ciel est bleu ? » n'est pas pour moi)."""
    q = str(question or "").strip()
    m = _RE_PQ_DEP.match(q)
    if m:
        cible = _cible_de(m.group(1) or m.group(2) or "")
        if cible == "surface":
            return _DEP_SURFACE
        if cible == "dtlm":
            return _DEP_DTLM
        for roue in _ROUES:
            r = _pourquoi_roue_dep(sit, _var_roue_de(m.group(1) or m.group(2) or "", roue), roue)
            if r:
                return r
        return None
    if _RE_PQ_SENS.match(q) and re.search(
            r"\b(?:compte|importe|change|demandes?|besoin|sert|utile|influe)\b|dtlm|r[ée]sultat", q, re.I):
        e_contre, e_co = _dtlm_num(sit, force_sens="contre"), _dtlm_num(sit, force_sens="co")
        preuve = ""
        if e_contre["val"] is not None and e_co["val"] is not None:
            preuve = (" Sur TES données : contre-courant -> DTLM ≈ %s degrés ; co-courant -> DTLM ≈ %s degrés." %
                      (_fmt(round(e_contre["val"], 4)), _fmt(round(e_co["val"], 4))))
        elif e_contre["impossible"] or e_co["impossible"]:
            preuve = (" Sur TES données, l'un des deux sens donne même un ΔT de borne nul ou négatif "
                      "(physiquement impossible) — preuve que le sens n'est pas un détail.")
        return ("Parce que le sens d'écoulement change les ΔT AUX BORNES : contre-courant -> ΔT1 = Tc,entrée − "
                "Tf,sortie et ΔT2 = Tc,sortie − Tf,entrée ; co-courant -> ΔT1 = Tc,entrée − Tf,entrée et "
                "ΔT2 = Tc,sortie − Tf,sortie. Mêmes 4 températures, bornes différentes, DTLM différent.%s" % preuve)
    m = _RE_PQ_DIR.match(q)
    if m:
        c_part, v_part = m.group(1), m.group(2)
        cible, var = _cible_de(c_part), _var_de(v_part)
        dir_c, dir_v = _dir_de(c_part), _dir_de(v_part)
        if cible == "surface" and var in _EXPL_SURFACE and dir_v:
            attendu = _SIGNE_SURFACE[var] * dir_v                     # direction RÉELLE de la surface
            preuve = _preuve_surface(sit, var, dir_v)
            if dir_c and dir_c != attendu:                            # prémisse FAUSSE -> corrigée, jamais validée
                return ("Ce n'est pas ce qui se passe : quand %s %s, la surface %s — %s.%s" %
                        ("le ΔTlm" if var == "dtlm" else "la " + var if var == "puissance" else "le coefficient U",
                         "augmente" if dir_v > 0 else "baisse",
                         "AUGMENTE" if attendu > 0 else "DIMINUE", _EXPL_SURFACE[var], preuve))
            return "Parce que %s.%s" % (_EXPL_SURFACE[var], preuve)
        if cible == "dtlm":
            return _pourquoi_dtlm_slot(sit, v_part, dir_v)
        for roue in _ROUES:
            r = _pourquoi_roue_dir(sit, c_part, v_part, roue)
            if r:
                return r
    return None


_RE_PQ_NU = re.compile(r"^\s*(?:mais\s+)?pourquoi(?:\s+(?:ça|ca|donc))?\s*\??\s*$|"
                       r"^\s*explique(?:[- ]moi)?(?:\s+(?:ça|ca|ce\s+calcul|ce\s+r[ée]sultat))?\s*\??\s*$", re.I)


def pourquoi_dernier(texte: str, derniere_reponse, sit):
    """« Pourquoi ? » NU -> le MÉCANISME de la dernière réponse si elle vient du pont (câblé serveur, qui
    seul connaît la dernière réponse). None sinon — le pipeline continue."""
    if not derniere_reponse or not _RE_PQ_NU.match(str(texte or "").strip()):
        return None
    r = str(derniere_reponse)
    if r.startswith("DTLM"):
        return ("Parce que l'écart de température n'est pas constant le long de l'échangeur : il varie "
                "exponentiellement entre les deux bornes (sous les hypothèses standard — U et débits "
                "constants), et la moyenne EXACTE de cet écart est la moyenne logarithmique "
                "(ΔT1−ΔT2)/ln(ΔT1/ΔT2) ; une moyenne arithmétique la surestimerait. " + _DEP_DTLM)
    if r.startswith("Surface"):
        return "Parce que " + _DEP_SURFACE[0].lower() + _DEP_SURFACE[1:]
    if r.startswith("Écart"):
        return ("Simple soustraction des deux grandeurs que TU m'as données (citées dans ma réponse avec leur "
                "tour d'origine) : je n'ai rien ajouté, j'ai soustrait tes valeurs.")
    if r.startswith(("Tension ≈", "Courant ≈", "Résistance ≈", "Puissance ≈")):
        return ("Parce que ces quatre grandeurs sont liées par DEUX définitions : la loi d'Ohm U = R·I (la "
                "résistance est le rapport tension/courant) et la puissance électrique P = U·I (énergie par "
                "seconde = tension × débit de charges). Deux valeurs suffisent donc à fermer les quatre — j'ai "
                "montré dans ma réponse le chemin exact suivi depuis TES données.")
    if r.startswith(("Débit ≈", "Section ≈", "Vitesse ≈")):
        return ("Parce que le débit volumique est, PAR DÉFINITION, le volume qui traverse la section chaque "
                "seconde : Q = S·v (section de passage × vitesse d'écoulement). Deux de ces trois grandeurs "
                "suffisent donc à fermer la troisième — j'ai montré dans ma réponse le chemin exact suivi "
                "depuis TES données.")
    if r.startswith("Dans ton hypothèse"):
        return ("Parce que j'ai re-propagé TA modification dans les mêmes équations fermées (simulation "
                "avant) : mêmes formules, un seul opérande changé — c'est pour ça que je montre l'avant/après.")
    if "il me manque" in r and re.search(r"DTLM|surface|temp[ée]rature|sens d['’][ée]coulement", r):
        return ("Parce que la formule exige chacun de ses opérandes : sans celui-là, il faudrait DEVINER une "
                "valeur — et je ne devine jamais (règle FAUX=0 : calcul exact, ou demande nommée de ce qui "
                "manque). Donne la valeur demandée et je calcule.")
    return None


def repond(question: str, sit):
    """Point d'entrée du PONT : calcul exact depuis les grandeurs énoncées, monde « et si » re-propagé,
    explication causale prouvée, demande NOMMÉE de l'opérande manquant, ou None (hors périmètre — le
    pipeline continue)."""
    if sit is None:
        return None
    q = str(question or "")
    if not q.strip():
        return None
    for resolveur in (_et_si, _pourquoi, _dtlm, _surface, _electrique, _hydraulique, _ecart):
        try:
            r = resolveur(q, sit)
        except Exception:
            r = None
        if r:
            return r
    return None
