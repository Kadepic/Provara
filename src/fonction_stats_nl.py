# -*- coding: utf-8 -*-
"""ROUTEUR STATISTIQUE EN LANGAGE NATUREL — câble la bibliothèque Palier 2 au chat, FAUX=0 (2026-07-03).

POURQUOI (mandat Yohan « tout câbler ») : ia.py expose ~300 fonctions de stats/incertitude/décision calibrées,
toutes injoignables depuis le dialogue (elles attendent des tableaux, pas du langage). Ce module RECONNAÎT une
intention statistique dans une phrase, en EXTRAIT les nombres (une ou deux listes, ou k/n), appelle la bonne
fonction ia.* avec `phrase=True`, et renvoie sa réponse française. Les fonctions gardent leur HONNÊTETÉ : elles
s'abstiennent d'elles-mêmes si l'échantillon est trop petit (calibration) — on relaie tel quel.

FAUX=0 : on ne calcule QUE ce que la fonction rend (ou l'abstention honnête) ; hors intention -> None (le
pipeline continue). Les stats descriptives simples (moyenne/médiane/écart-type/min/max/somme) sont des maths
EXACTES (module `statistics`), jamais une estimation floue.
"""
from __future__ import annotations

import re
import statistics

_NOMBRE = re.compile(r"-?\d+(?:[.,]\d+)?")


def _nombres(texte: str):
    return [float(m.group(0).replace(",", ".")) for m in _NOMBRE.finditer(texte)]


def _deux_listes(texte: str):
    """Sépare deux listes de nombres autour de « et / vs / contre / ; / // ». Renvoie (xs, ys) ou None."""
    parts = re.split(r"\s+(?:et|vs|versus|contre)\s+|\s*;\s*|\s*//\s*", texte, maxsplit=1, flags=re.I)
    if len(parts) != 2:
        return None
    xs, ys = _nombres(parts[0]), _nombres(parts[1])
    if len(xs) >= 2 and len(ys) >= 2:
        return xs, ys
    return None


def _ia():
    import importlib
    return importlib.import_module("ia")


# — table d'intentions : (regex de déclenchement, fonction de traitement) —
def _descr(op, vals):
    if not vals:
        return None
    if op == "moyenne":
        return "Moyenne : %s." % _fmt(statistics.fmean(vals))
    if op == "mediane":
        return "Médiane : %s." % _fmt(statistics.median(vals))
    if op == "ecart":
        if len(vals) < 2:
            return "Écart-type : indéfini (il faut au moins 2 valeurs)."
        return "Écart-type (échantillon) : %s ; variance : %s." % (
            _fmt(statistics.stdev(vals)), _fmt(statistics.variance(vals)))
    if op == "min":
        return "Minimum : %s ; maximum : %s." % (_fmt(min(vals)), _fmt(max(vals)))
    if op == "somme":
        return "Somme : %s (sur %d valeurs)." % (_fmt(sum(vals)), len(vals))
    if op == "etendue":
        return "Étendue : %s (de %s à %s)." % (_fmt(max(vals) - min(vals)), _fmt(min(vals)), _fmt(max(vals)))
    return None


def _fmt(x):
    if isinstance(x, float) and x == int(x):
        return str(int(x))
    return ("%.4g" % x) if isinstance(x, float) else str(x)


def repond_stats(texte: str):
    """Renvoie une réponse statistique (str) si la phrase EST une demande statistique reconnue, sinon None."""
    t = texte.strip()
    bas = _normalise(t)
    vals = _nombres(t)

    # — stats DESCRIPTIVES exactes (maths) —
    if re.search(r"\b(moyenne|moyen)\b", bas) and "confiance" not in bas and "intervalle" not in bas:
        return _descr("moyenne", vals) if vals else None
    if re.search(r"\bmediane?\b", bas):
        return _descr("mediane", vals) if vals else None
    if re.search(r"\b(ecart[- ]?type|variance|dispersion)\b", bas):
        return _descr("ecart", vals) if vals else None
    if re.search(r"\b(minimum|maximum|min et max|plus petit|plus grand)\b", bas) and vals:
        return _descr("min", vals)
    if re.search(r"\bsomme\b", bas) and vals:
        return _descr("somme", vals)
    if re.search(r"\b[ée]tendue\b", bas) and vals:
        return _descr("etendue", vals)

    ia = _ia()

    # — PROPORTION « k sur n » / « k succès sur n » (AVANT l'IC de moyenne : « intervalle » y figure aussi) —
    m = re.search(r"(\d+)\s*(?:succ[èe]s\s*)?(?:sur|/|parmi)\s*(\d+)", bas)
    if m and re.search(r"\b(proportion|pourcentage|taux de r[ée]ussite|intervalle|confiance|succ[èe]s|fiab)\b", bas):
        k, n = int(m.group(1)), int(m.group(2))
        if 0 <= k <= n and n > 0:
            try:
                return ia.intervalle_proportion(k, n, phrase=True)
            except Exception:
                return None

    # — INTERVALLE DE CONFIANCE de la moyenne d'un échantillon —
    if re.search(r"\b(intervalle de confiance|à quel point|est[- ]?elle? s[ûu]re|marge d'erreur)\b", bas) and len(vals) >= 3:
        try:
            return ia.incertitude(vals, quoi="moyenne", phrase=True)
        except Exception:
            return None

    # — TENDANCE (série qui monte/baisse) —
    if re.search(r"\b(tendance|en hausse|en baisse|monte|augmente|diminue|d[ée]cro[iî]t|[ée]volue)\b", bas) and len(vals) >= 3:
        try:
            return ia.tendance(vals, phrase=True)
        except Exception:
            return None

    # — PRÉVISION de la prochaine valeur —
    if re.search(r"\b(pr[ée]vois|pr[ée]vision|proch(?:aine|ain)\s+valeur|pr[ée]dis la suite)\b", bas) and len(vals) >= 3:
        try:
            return ia.prevoit(vals, phrase=True)
        except Exception:
            return None

    # — RUPTURE / CHANGEMENT de régime dans une série —
    if re.search(r"\b(rupture|changement de r[ée]gime|a[- ]?t[- ]?(?:il|elle) chang[ée]|point de bascule|cassure)\b", bas) and len(vals) >= 3:
        try:
            return ia.detecte_changement(vals, phrase=True)
        except Exception:
            return None

    # — FERMI (ordre de grandeur d'un produit de facteurs) —
    if re.search(r"\b(fermi|ordre de grandeur|estime.*produit|combien.*en tout|estimation approximative)\b", bas) and len(vals) >= 2:
        try:
            return ia.estime_fermi([(v, v) for v in vals], phrase=True)
        except Exception:
            return None

    # — BENFORD (fraude / premiers chiffres) —
    if re.search(r"\bbenford\b", bas) and len(vals) >= 5:
        try:
            return ia.test_benford([int(abs(v)) for v in vals if v], phrase=True)
        except Exception:
            return None

    # — TAUX (Poisson) « k événements en n / sur n » —
    m = re.search(r"(\d+)\s*(?:[ée]v[ée]nements?|pannes?|appels?|cas|fois)\s*(?:en|sur|par|pendant)\s*(\d+(?:[.,]\d+)?)", bas)
    if m and re.search(r"\b(taux|fr[ée]quence|poisson)\b", bas):
        k = int(m.group(1)); expo = float(m.group(2).replace(",", "."))
        try:
            return ia.estime_taux(k, expo, phrase=True)
        except Exception:
            return None

    # — KELLY (mise optimale) : une proba (<1 ou en %) + une cote (>1). On lit les nombres du texte ORIGINAL. —
    if re.search(r"\b(kelly|combien parier|quelle mise|fraction .* parier)\b", bas):
        mpct = re.search(r"(\d+(?:[.,]\d+)?)\s*%", t)
        proba = float(mpct.group(1).replace(",", ".")) / 100 if mpct else next((v for v in vals if 0 < v < 1), None)
        cote = next((v for v in vals if v > 1), None)
        if proba is not None and cote is not None:
            try:
                return ia.mise_kelly(proba, cote, phrase=True)
            except Exception:
                return None

    # — ANOMALIE : « X est-il anormal par rapport à … » (1 valeur + 1 liste) —
    if re.search(r"\b(anormale?|aberrante?|hors norme|valeur[- ]?ab[ée]rrante|outlier)\b", bas) and len(vals) >= 3:
        return _anomalie(ia, vals)

    # — RISQUE EXTRÊME / VaR —
    if re.search(r"\b(risque extr[êe]me|valeur[- ]?[àa][- ]?risque|\bvar\b|pire des cas|perte extr[êe]me)\b", bas) and len(vals) >= 5:
        try:
            return ia.risque_extreme(vals, 0.99, phrase=True)
        except Exception:
            return None

    # — DEUX LISTES : corrélation/pente, comparaison, effet causal, méta-analyse —
    duo = _deux_listes(t)
    if duo:
        xs, ys = duo
        if re.search(r"\b(corr[ée]lation|pente|r[ée]gression|relation entre|lien entre)\b", bas) and len(xs) == len(ys):
            try:
                return ia.pente_robuste(xs, ys, phrase=True)
            except Exception:
                return None
        if re.search(r"\b(effet causal|traitement|caus\w+)\b", bas):
            try:
                return ia.effet_causal(xs, ys, phrase=True)
            except Exception:
                return None
        if re.search(r"\b(m[ée]ta[- ]?analyse|combine .* [ée]tudes)\b", bas) and len(xs) == len(ys):
            try:
                return ia.meta_analyse(xs, ys, phrase=True)
            except Exception:
                return None
        if re.search(r"\b(compare|diff[éè]re|diff[ée]rence|significatif|groupe)\b", bas):
            try:
                return ia.compare(xs, ys, phrase=True)
            except Exception:
                return None

    return None


def _anomalie(ia, vals):
    """« 87 est-il anormal par rapport à 12, 15, 14 » : la 1re valeur est le candidat, le reste la référence."""
    if len(vals) < 3:
        return None
    candidat, reference = vals[0], vals[1:]
    try:
        return ia.anomalie(candidat, reference, phrase=True)
    except Exception:
        return None


def _normalise(s):
    try:
        from base_faits import normalise as _n
        return _n(s)
    except Exception:
        import unicodedata
        s = unicodedata.normalize("NFD", str(s).lower())
        return "".join(c for c in s if unicodedata.category(c) != "Mn")
