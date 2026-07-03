"""
PALIER 2 — L'INSTRUMENT DE CALIBRATION (le juge transverse, 2026-06-25).

incertitude.py PRODUIT des probas/intervalles. calibration.py les JUGE. C'est le « mètre-étalon » du non-borné :
comme mesure.py juge l'apprentissage borné, ce module juge l'HONNÊTETÉ de l'incertitude de TOUTE brique P2.

L'INVARIANT (l'équivalent de FAUX=0 pour le P2) = LA CALIBRATION. On ne vérifie JAMAIS qu'une estimation isolée
est juste (impossible). On vérifie que, sur de NOMBREUX cas dont on connaît la vérité (réels ou simulés) :
  - une confiance annoncée « 90 % » s'avère juste ~90 % du temps (forecast calibré) ;
  - un intervalle annoncé « à 90 % » contient la vraie valeur ~90 % du temps (couverture nominale).

═══ INTERFACE CANONIQUE = (confiance, justesse) ═══
La brique P2 produit une RÉPONSE + une CONFIANCE ∈ [0,1] (« je suis sûr à 90 % »). Pour la juger, on collecte des
couples (confiance annoncée, justesse ∈ {0,1} = la réponse était-elle juste ?). Un système calibré a, parmi les cas
où il annonce ~90 %, ~90 % de réponses justes. C'est CETTE sémantique qui rend la sur-confiance NON ANNULABLE :
durcir une proba (la rendre plus extrême) AUGMENTE la confiance sans changer la justesse -> sur-confiance détectée.
(Le piège évité : un écart signé sur la proba brute P(y=1) s'annule entre positifs et négatifs.)

LA LIGNE ROUGE = la SUR-CONFIANCE : confiance annoncée > justesse réelle. Aussi inacceptable qu'un FAUX en P1.
La sous-confiance (confiance < justesse) est seulement prudente : sûre, mais peu informative. On nomme les deux.

Métriques (pures, sans dépendance, model-free) :
  • brier            — score de Brier (erreur quadratique propre) : 0 = parfait.
  • diagramme_fiabilite — reliability diagram : par tranche de confiance, la justesse empirique observée.
  • ece / mce        — Expected / Maximum Calibration Error : écart moyen / max |confiance − justesse|.
  • ecart_signe      — écart SIGNÉ (confiance − justesse) : > 0 = SUR-confiant (DANGER), < 0 = sous-confiant.
  • est_calibre      — VERDICT : CALIBRE / SURCONFIANT / SOUSCONFIANT / ABSTENTION.
  • couverture / verdict_couverture — juge les estimateurs d'INTERVALLE de incertitude.py (couverture nominale).
  • depuis_probas    — convertit un forecast binaire P(y=1) en couples (confiance, justesse).
  • formule          — la parole honnête (« ce niveau de confiance est honnête / trop sûr de lui »).

ABSTENTION : moins de N_MIN_CAL cas -> calibration non estimable honnêtement -> pas de verdict (pas de faux jugement).
"""
from __future__ import annotations

ABSTENTION = "abstention"
CALIBRE = "calibre"
SURCONFIANT = "surconfiant"        # confiance annoncée > justesse réelle -> LIGNE ROUGE (fausse précision)
SOUSCONFIANT = "sousconfiant"      # confiance annoncée < justesse réelle -> prudent (sûr mais peu informatif)

N_MIN_CAL = 30                     # en-dessous : la calibration n'est pas estimable honnêtement -> ABSTENTION


def _paires(confiances, justesses):
    """Nettoie en couples (confiance ∈ [0,1], justesse ∈ {0,1}). Lève si tailles incohérentes ou confiance hors [0,1]."""
    c = [float(v) for v in confiances]
    j = [1 if v else 0 for v in justesses]
    if len(c) != len(j):
        raise ValueError(f"confiances ({len(c)}) et justesses ({len(j)}) de tailles différentes")
    for v in c:
        if not (0.0 <= v <= 1.0):
            raise ValueError(f"confiance hors [0,1] : {v}")
    return c, j


def depuis_probas(probas, issues):
    """Convertit un FORECAST BINAIRE (proba p = P(y=1), issue y ∈ {0,1}) en couples (confiance, justesse) :
    la réponse prédite est « y=1 » si p ≥ 0.5 sinon « y=0 », la confiance est max(p, 1−p), la justesse = la
    prédiction est-elle correcte. Permet de juger un forecast de proba avec la sémantique confiance/justesse."""
    p = [float(v) for v in probas]
    y = [1 if v else 0 for v in issues]
    if len(p) != len(y):
        raise ValueError(f"probas ({len(p)}) et issues ({len(y)}) de tailles différentes")
    conf, just = [], []
    for i in range(len(p)):
        pred = 1 if p[i] >= 0.5 else 0
        conf.append(max(p[i], 1.0 - p[i]))
        just.append(1 if pred == y[i] else 0)
    return conf, just


def brier(confiances, justesses) -> float:
    """SCORE DE BRIER : moyenne de (confiance − justesse)². Règle de score PROPRE (minimisée par la vraie
    probabilité de justesse) : récompense justesse ET calibration. 0 = parfait, 0.25 = confiance constante 0.5."""
    c, j = _paires(confiances, justesses)
    if not c:
        raise ValueError("aucune donnée")
    return sum((c[i] - j[i]) ** 2 for i in range(len(c))) / len(c)


def diagramme_fiabilite(confiances, justesses, n_bins: int = 10):
    """RELIABILITY DIAGRAM : range les cas par tranche de confiance et renvoie, pour chaque tranche NON VIDE, un
    dict {bas, haut, n, conf (confiance moyenne annoncée), just (justesse empirique observée)}. Calibré -> conf ≈ just."""
    c, j = _paires(confiances, justesses)
    seaux = [[] for _ in range(n_bins)]
    for i in range(len(c)):
        b = min(n_bins - 1, int(c[i] * n_bins))     # confiance=1.0 -> dernière tranche
        seaux[b].append(i)
    diag = []
    for k in range(n_bins):
        idx = seaux[k]
        if not idx:
            continue
        conf = sum(c[i] for i in idx) / len(idx)
        just = sum(j[i] for i in idx) / len(idx)
        diag.append({"bas": k / n_bins, "haut": (k + 1) / n_bins, "n": len(idx), "conf": conf, "just": just})
    return diag


def ece(confiances, justesses, n_bins: int = 10) -> float:
    """EXPECTED CALIBRATION ERROR : écart moyen |confiance − justesse|, pondéré par l'effectif de chaque tranche.
    0 = calibration parfaite. Mesure d'infidélité GLOBALE (non signée)."""
    diag = diagramme_fiabilite(confiances, justesses, n_bins)
    n = sum(s["n"] for s in diag)
    if n == 0:
        raise ValueError("aucune donnée")
    return sum(s["n"] * abs(s["conf"] - s["just"]) for s in diag) / n


def mce(confiances, justesses, n_bins: int = 10) -> float:
    """MAXIMUM CALIBRATION ERROR : pire écart |confiance − justesse| sur les tranches (le point le plus malhonnête)."""
    diag = diagramme_fiabilite(confiances, justesses, n_bins)
    if not diag:
        raise ValueError("aucune donnée")
    return max(abs(s["conf"] - s["just"]) for s in diag)


def ecart_signe(confiances, justesses, n_bins: int = 10) -> float:
    """ÉCART SIGNÉ moyen (confiance − justesse), pondéré. > 0 = SUR-confiant (annonce plus de certitude que la
    réalité = DANGER), < 0 = sous-confiant (prudent). Distingue le mensonge (sur-confiance) de la prudence."""
    diag = diagramme_fiabilite(confiances, justesses, n_bins)
    n = sum(s["n"] for s in diag)
    if n == 0:
        raise ValueError("aucune donnée")
    return sum(s["n"] * (s["conf"] - s["just"]) for s in diag) / n


def est_calibre(confiances, justesses, n_bins: int = 10, tol: float = 0.05):
    """VERDICT de calibration d'un lot de couples (confiance annoncée, justesse 0/1).
    Renvoie (verdict, infos) avec verdict ∈ {CALIBRE, SURCONFIANT, SOUSCONFIANT, ABSTENTION} et
    infos = {n, ece, mce, brier, ecart_signe}. La SUR-confiance est prioritaire (ligne rouge).
    ABSTENTION si moins de N_MIN_CAL cas (calibration non jugeable honnêtement)."""
    c, j = _paires(confiances, justesses)
    n = len(c)
    if n < N_MIN_CAL:
        return (ABSTENTION, {"n": n, "raison": f"trop peu de cas (n={n} < {N_MIN_CAL}) : calibration non jugeable"})
    infos = {"n": n, "ece": ece(c, j, n_bins), "mce": mce(c, j, n_bins),
             "brier": brier(c, j), "ecart_signe": ecart_signe(c, j, n_bins)}
    es = infos["ecart_signe"]
    if es > tol:
        verdict = SURCONFIANT
    elif es < -tol:
        verdict = SOUSCONFIANT
    else:
        verdict = CALIBRE
    return (verdict, infos)


# ───────────────────────── COUVERTURE D'INTERVALLES (juge incertitude.py) ─────────────────────────

def couverture(intervalles, verites):
    """Fraction d'intervalles (bas, haut) qui CONTIENNENT la vérité associée. Le test direct des estimateurs
    d'intervalle (estime_moyenne, predit_intervalle, estime_proportion…) de incertitude.py. Renvoie (frac, n)."""
    inter = list(intervalles)
    ver = [float(v) for v in verites]
    if len(inter) != len(ver):
        raise ValueError(f"intervalles ({len(inter)}) et verites ({len(ver)}) de tailles différentes")
    if not inter:
        raise ValueError("aucune donnée")
    couvre = sum(1 for i in range(len(inter)) if inter[i][0] <= ver[i] <= inter[i][1])
    return (couvre / len(inter), len(inter))


def verdict_couverture(intervalles, verites, nominal: float, tol: float = 0.05):
    """VERDICT sur un estimateur d'INTERVALLE : la couverture empirique tient-elle la promesse `nominal` (ex 0.90) ?
    Renvoie (verdict, infos). SUR-confiant = SOUS-couvre (intervalle trop étroit -> contient la vérité MOINS souvent
    que promis = ligne rouge). Sous-confiant = SUR-couvre (intervalle trop large, prudent). ABSTENTION si trop peu."""
    n = len(list(intervalles))
    if n < N_MIN_CAL:
        return (ABSTENTION, {"n": n, "raison": f"trop peu de cas (n={n} < {N_MIN_CAL})"})
    frac, _ = couverture(intervalles, verites)
    ecart = frac - nominal                       # < 0 -> sous-couvre -> sur-confiant
    infos = {"n": n, "couverture": frac, "nominal": nominal, "ecart": ecart}
    if ecart < -tol:
        verdict = SURCONFIANT
    elif ecart > tol:
        verdict = SOUSCONFIANT
    else:
        verdict = CALIBRE
    return (verdict, infos)


# ───────────────────────────────────── LA PAROLE DU JUGE ─────────────────────────────────────

def formule(verdict_infos, quoi: str = "forecast") -> str:
    """Traduit un verdict (est_calibre / verdict_couverture) en phrase HONNÊTE. `quoi` ∈ {forecast, couverture}."""
    verdict, infos = verdict_infos
    if verdict == ABSTENTION:
        return f"Je ne peux pas juger la calibration : {infos.get('raison', 'trop peu de cas')}."
    if quoi == "couverture":
        pct_n = round(infos["nominal"] * 100)
        pct_r = round(infos["couverture"] * 100)
        if verdict == CALIBRE:
            return (f"Cet intervalle est honnête : annoncé à {pct_n}%, il contient la vérité {pct_r}% du temps "
                    "(promesse tenue).")
        if verdict == SURCONFIANT:
            return (f"⚠ Cet intervalle est TROP SÛR DE LUI : annoncé à {pct_n}%, il ne contient la vérité que "
                    f"{pct_r}% du temps — trop étroit, il ment sur sa précision.")
        return (f"Cet intervalle est trop PRUDENT : annoncé à {pct_n}%, il contient la vérité {pct_r}% du temps "
                "(plus large que nécessaire — sûr, mais peu informatif).")
    # forecast
    ec = round(infos["ece"] * 100, 1)
    if verdict == CALIBRE:
        return f"Ces confiances sont honnêtes (écart de calibration ≈ {ec}%) : un « X% » annoncé s'avère juste ~X% du temps."
    if verdict == SURCONFIANT:
        return (f"⚠ Ces confiances sont TROP SÛRES D'ELLES (sur-confiance ≈ {round(infos['ecart_signe']*100,1)}%, "
                f"écart ≈ {ec}%) : la confiance annoncée dépasse la justesse réelle — c'est de la fausse précision.")
    return (f"Ces confiances sont trop PRUDENTES (sous-confiance ≈ {round(-infos['ecart_signe']*100,1)}%) : "
            "elles ne mentent jamais en sur-promettant, mais pourraient affirmer davantage.")


if __name__ == "__main__":
    print("=== INSTRUMENT DE CALIBRATION (le juge du Palier 2) ===\n")
    import random
    rng = random.Random(0)
    # forecaster calibré : annonce une confiance c, la réponse est juste à Bernoulli(c) (c ∈ [0.5,1])
    C = [0.5 + 0.5 * rng.random() for _ in range(3000)]
    J_cal = [1 if rng.random() < c else 0 for c in C]
    print(" calibré   :", formule(est_calibre(C, J_cal), "forecast"))
    # forecaster sur-confiant : annonce TROP de confiance (durci vers 1) pour la même justesse réelle
    C_sur = [min(1.0, c + 0.5 * (1 - c)) for c in C]      # remonte chaque confiance vers 1
    print(" sur-conf  :", formule(est_calibre(C_sur, J_cal), "forecast"))
    # forecaster sous-confiant : annonce trop peu de confiance
    C_sous = [0.5 + 0.5 * (c - 0.5) for c in C]
    print(" sous-conf :", formule(est_calibre(C_sous, J_cal), "forecast"))
    # intervalles : nominal 90% mais en réalité ~72%
    inter = [(0, 1) if rng.random() < 0.72 else (2, 3) for _ in range(500)]
    print(" couverture:", formule(verdict_couverture(inter, [0.5] * 500, 0.90), "couverture"))
