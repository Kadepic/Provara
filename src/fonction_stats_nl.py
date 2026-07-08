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


# — MOYENNE PONDÉRÉE : paires (valeur, coefficient) — jamais la moyenne simple de tous les nombres (FAUX=0).
_PAIRE_POND = re.compile(
    r"(-?\d+(?:[.,]\d+)?)\s*\(?\s*(?:coefficients?|coeffs?\.?|coefs?\.?|poids|pond[ée]r[ée]e?\s+(?:par|de))\s*:?\s*"
    r"(-?\d+(?:[.,]\d+)?)\)?", re.I)


def _moyenne_ponderee(texte: str, bas: str, explicite: bool = True):
    """« 12 coefficient 2 et 15 coefficient 3 » -> 13.8 ; « de 12 et 15 avec les poids 2 et 3 » -> 13.8.
    Si l'appariement valeur/coefficient est ambigu : abstention honnête EXPLICITE quand l'intention est sûre
    (« pondérée »/« coefficient ») — surtout pas la moyenne simple ; None quand seul « poids » apparaît
    (des poids PHYSIQUES se moyennent simplement : « moyenne des poids 70, 80, 90 »)."""
    paires = [(float(v.replace(",", ".")), float(w.replace(",", "."))) for v, w in _PAIRE_POND.findall(texte)]
    if not paires:
        # forme « valeurs … poids/coefficients … » : les nombres AVANT le mot-clé sont les valeurs, APRÈS les poids
        parts = re.split(r"\b(?:poids|coefficients?|coeffs?)\b", bas, maxsplit=1)
        if len(parts) == 2:
            vs, ws = _nombres(parts[0]), _nombres(parts[1])
            if vs and len(vs) == len(ws):
                paires = list(zip(vs, ws))
    if paires:
        total = sum(w for _, w in paires)
        if total <= 0:
            return "Moyenne pondérée : indéfinie (la somme des coefficients doit être strictement positive)."
        return "Moyenne pondérée : %s (coefficients %s)." % (
            _fmt(sum(v * w for v, w in paires) / total), ", ".join(_fmt(w) for _, w in paires))
    if not explicite:
        return None
    return ("Je vois une demande de moyenne pondérée, mais je n'arrive pas à associer chaque valeur à son "
            "coefficient. Donne-les sous la forme « 12 coefficient 2, 15 coefficient 3 » et je calcule.")


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
        # GARDE VITESSE MOYENNE (FAUX vécu 2026-07-08) : « vitesse moyenne si je parcours 150 km en 2 heures »
        # servait « Moyenne : 76 » (la moyenne de {150, 2} !). Le motif « X km en Y heures » est une division
        # d/t -> route cinématique (fonction_nl) ; « moyenne des vitesses 30, 40, 50 km/h » (liste) reste ici.
        if re.search(r"km\b.{0,20}?\ben\s+\d+(?:[.,]\d+)?\s*(?:h\d{0,2}\b|heures?)", bas):
            return None                                  # (h\d{0,2} : « en 1h30 » compact, FAUX 43.67 vécu)
        # moyenne PONDÉRÉE : ne JAMAIS servir la moyenne simple de tous les nombres (les coefficients
        # ne sont pas des valeurs — « 12 coeff 2 et 15 coeff 3 » vaut 13.8, pas 8)
        # HARMONIQUE / GÉOMÉTRIQUE nommées (FAUX vécu 2026-07-08 : « moyenne harmonique de 2 et 4 » servait
        # la moyenne ARITHMÉTIQUE 3 au lieu de 2.67). Formule dite ; valeurs non positives -> abstention.
        if ("harmonique" in bas or "geometrique" in bas) and vals:
            if any(v <= 0 for v in vals):                # hors domaine (la stdlib renverrait 0 par convention
                nom = "harmonique" if "harmonique" in bas else "géométrique"
                return ("La moyenne %s exige des valeurs strictement positives — je m'abstiens "
                        "plutôt que de servir la convention limite." % nom)
            import statistics as _st
            try:
                if "harmonique" in bas:
                    return "Moyenne harmonique : %s (n / Σ 1/xᵢ)." % _fmt(round(_st.harmonic_mean(vals), 4))
                return "Moyenne géométrique : %s (ⁿ√ Π xᵢ)." % _fmt(round(_st.geometric_mean(vals), 4))
            except Exception:
                return None
        if re.search(r"\b(pond[ée]r[ée]e?s?|coefficients?|coeffs?|coefs?)\b", bas):
            return _moyenne_ponderee(t, bas) if vals else None
        if re.search(r"\bpoids\b", bas) and vals:
            pond = _moyenne_ponderee(t, bas, explicite=False)
            if pond:
                return pond
        return _descr("moyenne", vals) if vals else None
    if re.search(r"\bmediane?\b", bas):
        return _descr("mediane", vals) if vals else None
    if re.search(r"\b(ecart[- ]?type|variance|dispersion)\b", bas):
        return _descr("ecart", vals) if vals else None
    if re.search(r"\b(minimum|maximum|min et max|plus petit|plus grand)\b", bas) and vals:
        # GARDE FRACTIONS (FAUX vécu 2026-07-08) : « le plus grand : 2/3 ou 3/5 » servait « Minimum : 2 ;
        # maximum : 5 » (les numérateurs/dénominateurs traités comme des valeurs). Une fraction a/b n'est pas
        # deux nombres -> on laisse la main à la route de comparaison exacte de fractions (fonction_nl).
        if re.search(r"\d\s*/\s*\d", t):
            return None
        # GARDE MOT-CLÉ D'AUTRE INTENTION (FAUX vécu 2026-07-08) : « le plus grand DIVISEUR COMMUN de 24 et
        # 36 » servait « Minimum : 24 ; maximum : 36 » (au lieu du PGCD 12) ; « de combien de % 40 est plus
        # grand que 25 » servait min/max. Le « plus grand » de ces phrases qualifie un DIVISEUR/un ÉCART, pas
        # une liste. On laisse la main aux routes dédiées (fonction_nl : PGCD, comparaison en %).
        if re.search(r"\b(diviseur|multiple|commun|pgcd|ppcm|pourcent|pour ?cent)\b", bas) or "%" in t:
            return None
        # GARDE COMPARAISON / TRI / EXTREMUM (FAUX vécu 2026-07-08) : « 8 est plus grand QUE 5 » (comparaison
        # -> Oui/Non), « CLASSE 3,1,2 par ordre » (tri), « le plus grand ENTRE 7 et 12 » (extremum, réponse
        # directe) ne sont pas des questions de min/max descriptif. On laisse la main à fonction_nl.
        if re.search(r"\bplus\s+(?:grand|petit|[ée]lev[ée])\w*\s+(?:a|à|que)\b|\b(?:sup[ée]rieur|inf[ée]rieur)\w*\s+(?:a|à|que)\b"
                     r"|\b(?:classe|range|trie|ordonne|classer|ranger|trier)\b|\bordre\s+(?:croissant|decroissant)\b"
                     r"|\bplus\s+(?:grand|petit)\s+(?:entre|de|parmi)\b|\bdu\s+plus\s+(?:petit|grand)\b", bas):
            return None
        return _descr("min", vals)
    if re.search(r"\bsomme\b", bas) and vals:
        # GARDE SÉRIE (FAUX vécu 2026-07-08) : « somme des entiers de 1 à 100 » servait « Somme : 101 (sur
        # 2 valeurs) » — les BORNES traitées comme la liste ! Une somme « de X à Y » (ou « des N premiers… »)
        # est une série -> route dédiée (fonction_nl) ; la somme de liste (« somme de 3, 7 et 9 ») reste ici.
        if re.search(r"\b(?:entiers?|nombres?)\s+de\s+\d+\s+a\s+\d+\b", bas) \
                or re.search(r"\bdes\s+\d+\s+premiers?\b", bas) \
                or (len(vals) == 2 and re.search(r"\bde\s+\d+\s+a\s+\d+\b", bas)):
            return None
        return _descr("somme", vals)
    if re.search(r"\b[ée]tendue\b", bas) and vals:
        return _descr("etendue", vals)

    ia = _ia()

    # — PROPORTION « k sur n » / « k succès sur n » (AVANT l'IC de moyenne : « intervalle » y figure aussi) —
    m = re.search(r"(\d+)\s*(?:succ[èe]s\s*)?(?:sur|/|parmi)\s*(\d+)", bas)
    # GARDE ARITHMÉTIQUE (FAUX vécu 2026-07-08) : « quel pourcentage REPRÉSENTE 45 sur 60 » servait un
    # intervalle de Wilson (inférence) au lieu du calcul exact 75 %. « représente/fait » = division exacte
    # -> route pourcentage de fonction_nl ; l'inférence (taux de réussite, confiance) reste ici.
    if m and re.search(r"\b(represente|fait)\b", bas):
        m = None
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
    # GARDE CALCUL (FAUX vécu 2026-07-08) : « augmente 50 de 10 % puis de 20 % » partait en détection de
    # tendance (« série trop courte ») — c'est un calcul de pourcentages enchaînés (fonction_nl).
    if re.search(r"augmente[rz]?\s+\d", bas) and "%" in t:
        return None
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
        # GARDE MONNAIE (FAUX vécu 2026-07-08) : « 3 pièces de 2 euros et 2 billets de 5, combien en tout »
        # MULTIPLIAIT tous les nombres (« ~60 » pour 16 !). Pièces/billets/euros = somme EXACTE (fonction_nl).
        if re.search(r"\b(pieces?|billets?|euros?|centimes?)\b", bas):
            return None
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
