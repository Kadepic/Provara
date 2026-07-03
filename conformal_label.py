"""
PALIER 2 — CONFORME LABEL-CONDITIONAL (Mondrian par classe, brique 22, 2026-06-25).

Le conforme de classification marginal (conformal.ensemble_conforme) garantit que le vrai label est dans l'ensemble
~1−α EN MOYENNE. Mais sous DÉSÉQUILIBRE de classes, il peut SOUS-couvrir les classes RARES (et sur-couvrir les
fréquentes) : marginalement honnête, injuste par classe. Le conforme LABEL-CONDITIONAL calibre un seuil SÉPARÉ par
VRAIE classe :

  pour chaque classe c :  q_c = quantile (1−α) des scores {1 − p(c)} sur les exemples de calibration dont y = c
  ensemble test = { c : 1 − p_test(c) ≤ q_c }  =  { c : p_test(c) ≥ 1 − q_c }

GARANTIE (distribution-free, par classe) : P(c ∈ ensemble | vrai label = c) ≥ 1−α POUR CHAQUE c. Plus fort que le
marginal : couverture ÉQUITABLE même pour les classes rares. ABSTENTION (classe non calibrée) si trop peu d'exemples.
"""
from __future__ import annotations

import math

N_MIN_CLASSE = 10


def ajuste_label(probas_cal, labels_cal, alpha=0.1):
    """Apprend un seuil q_c par classe. `probas_cal` = liste de dict {classe: proba} ; `labels_cal` = vraie classe.
    Renvoie dict {classe: q_c} (classes avec trop peu d'exemples -> absentes = on inclura toujours, prudent)."""
    par_classe = {}
    for probas, y in zip(probas_cal, labels_cal):
        par_classe.setdefault(y, []).append(1.0 - float(probas.get(y, 0.0)))
    seuils = {}
    for c, scores in par_classe.items():
        n = len(scores)
        if n < N_MIN_CLASSE:
            continue
        s = sorted(scores)
        k = math.ceil((1.0 - alpha) * (n + 1))
        seuils[c] = s[k - 1] if k <= n else float("inf")     # +inf -> classe toujours incluse (prudent)
    return seuils


def ensemble_label(seuils_q, probas_test):
    """Ensemble de prédiction label-conditional : {c : 1 − p_test(c) ≤ q_c}. Une classe sans seuil (non calibrée)
    est INCLUSE (prudence : on ne l'exclut pas faute d'évidence)."""
    ens = set()
    for c, p in probas_test.items():
        q = seuils_q.get(c)
        if q is None or (1.0 - float(p)) <= q:
            ens.add(c)
    return ens


def formule(ensemble, conf=0.90) -> str:
    pct = round(conf * 100)
    if not ensemble:
        return f"Aucune classe ne passe mon seuil ({pct}% par classe) — incertitude forte, je m'abstiens."
    if len(ensemble) == 1:
        return f"La réponse est {next(iter(ensemble))} (couverture garantie {pct}% pour CHAQUE classe)."
    return (f"Je n'arrive pas à trancher : la réponse est dans {{{', '.join(map(str, sorted(map(str, ensemble))))}}} "
            f"(garantie {pct}% par classe, même les rares).")


if __name__ == "__main__":
    print("=== CONFORME LABEL-CONDITIONAL ===\n")
    import random
    rng = random.Random(0)
    # 3 classes déséquilibrées ; proba de la vraie classe ~ U(0.3,0.9)
    classes = ["frequent", "moyen", "rare"]
    poids = [0.8, 0.15, 0.05]
    probas_cal, labels = [], []
    for _ in range(2000):
        u = rng.random(); cum = 0; y = classes[-1]
        for c, w in zip(classes, poids):
            cum += w
            if u < cum:
                y = c; break
        pv = 0.3 + 0.6 * rng.random()
        reste = 1 - pv
        d = {c: 0.0 for c in classes}
        d[y] = pv
        autres = [c for c in classes if c != y]
        d[autres[0]] = reste * rng.random()
        d[autres[1]] = reste - d[autres[0]]
        probas_cal.append(d); labels.append(y)
    seuils = ajuste_label(probas_cal, labels, 0.1)
    print("  seuils q_c :", {c: round(q, 2) for c, q in seuils.items()})
    print(" ", formule(ensemble_label(seuils, {"frequent": 0.2, "moyen": 0.3, "rare": 0.5})))
