"""
PALIER 2 — COMBINAISON BAYÉSIENNE D'ÉVIDENCE (brique 2, 2026-06-25).

Agréger PLUSIEURS indices bruités en UNE probabilité postérieure CALIBRÉE, à partir d'un PRIOR HONNÊTE (explicite,
jamais caché). Mécanisme = mise à jour en LOG-ODDS (numériquement stable) :

    logit(posterior) = logit(prior) + Σ ln(rapport de vraisemblance_i)

Chaque indice i est décrit par (p_si_oui = P(observation | H vraie), p_si_non = P(observation | H fausse), observe).
Rapport de vraisemblance (LR) : observe=1 -> p_si_oui/p_si_non ; observe=0 -> (1−p_si_oui)/(1−p_si_non).

CALIBRATION (l'invariant) : SOUS l'hypothèse d'indépendance conditionnelle des indices et de vraisemblances bien
spécifiées, la postérieure est CALIBRÉE — vérifié Monte-Carlo (valide_bayes.py, jugé par calibration.py).

HONNÊTETÉ / ANTI-SUR-CONFIANCE (la ligne rouge) :
  • PRIOR explicite obligatoire (pas d'uniforme caché).
  • On REFUSE les vraisemblances dégénérées (p=0 ou 1) : elles affirment l'impossible -> odds infinis -> fausse
    certitude. -> ABSTENTION plutôt qu'un faux 100 %.
  • CAVEAT documenté + démontré : si les indices sont CORRÉLÉS (pas indépendants), la postérieure devient
    SUR-CONFIANTE. C'est mesuré dans valide_bayes.py (calibration.py le démasque). Combiner des indices redondants
    = mentir sur la certitude. On l'expose, on ne le cache pas.
"""
from __future__ import annotations

import math

ABSTENTION = "abstention"
ESTIMATION = "estimation"
_EPS = 1e-12


def _logit(p):
    return math.log(p / (1.0 - p))


def _sigmoid(x):
    if x >= 0:
        z = math.exp(-x)
        return 1.0 / (1.0 + z)
    z = math.exp(x)
    return z / (1.0 + z)


def maj_log_odds(prior, lrs):
    """Mise à jour bas-niveau : (ESTIMATION, p_post, infos) à partir d'un prior ∈ (0,1) et d'une liste de rapports
    de vraisemblance STRICTEMENT positifs. ABSTENTION si prior dégénéré ou LR ≤ 0 / infini (certitude fabriquée)."""
    if not (0.0 < prior < 1.0):
        return (ABSTENTION, None, f"prior dégénéré ({prior}) : doit être dans (0,1), pas une certitude")
    lrs = list(lrs)
    for lr in lrs:
        if not (lr > 0.0) or math.isinf(lr):
            return (ABSTENTION, None, f"rapport de vraisemblance invalide ({lr}) : 0/∞ = certitude fabriquée -> refus")
    logit = _logit(prior) + sum(math.log(lr) for lr in lrs)
    p = _sigmoid(logit)
    return (ESTIMATION, p, {"prior": prior, "n_indices": len(lrs), "logit": logit})


def lr_indice(p_si_oui, p_si_non, observe):
    """Rapport de vraisemblance d'UN indice. (p_si_oui, p_si_non) ∈ (0,1) strict (sinon None = à refuser)."""
    if not (0.0 < p_si_oui < 1.0) or not (0.0 < p_si_non < 1.0):
        return None
    if observe:
        return p_si_oui / p_si_non
    return (1.0 - p_si_oui) / (1.0 - p_si_non)


def posterior(prior, indices):
    """Probabilité postérieure de H à partir d'un PRIOR explicite et d'une liste d'INDICES bruités, chacun
    (p_si_oui, p_si_non, observe). Renvoie (ESTIMATION, p_post, infos) ou (ABSTENTION, None, raison).
    Suppose l'INDÉPENDANCE CONDITIONNELLE des indices (sinon -> sur-confiance, cf. module docstring)."""
    if not (0.0 < prior < 1.0):
        return (ABSTENTION, None, f"prior dégénéré ({prior}) : doit être dans (0,1)")
    if not indices:
        return (ESTIMATION, prior, {"prior": prior, "n_indices": 0, "note": "aucun indice -> postérieure = prior"})
    lrs = []
    for (po, pn, obs) in indices:
        lr = lr_indice(po, pn, obs)
        if lr is None:
            return (ABSTENTION, None, f"indice à vraisemblance dégénérée (p_si_oui={po}, p_si_non={pn}) : refus")
        lrs.append(lr)
    return maj_log_odds(prior, lrs)


def formule(res) -> str:
    """Parole honnête d'une combinaison bayésienne."""
    statut = res[0]
    if statut == ABSTENTION:
        return f"Je préfère ne pas conclure : {res[2]}."
    p = res[1]
    pct = round(p * 100)
    prior = res[2].get("prior")
    sens = "renforcé" if p > prior else ("affaibli" if p < prior else "inchangé")
    return (f"En combinant les indices, j'estime la probabilité à ~{pct}% (départ {round(prior*100)}%, {sens}). "
            "C'est une probabilité calibrée si les indices sont indépendants — pas une certitude.")


def posterior_correle(prior, indices, rho: float = 0.0):
    """Combinaison bayésienne pour indices CORRÉLÉS (corrige le caveat de `posterior`). On ESCOMPTE l'évidence par la
    TAILLE D'ÉCHANTILLON EFFECTIVE : k indices de corrélation moyenne ρ valent n_eff = k/(1+(k−1)ρ) indices
    indépendants. Le log-rapport total est multiplié par n_eff/k = 1/(1+(k−1)ρ). Renvoie (ESTIMATION, p, infos) ou
    ABSTENTION. Propriétés EXACTES : ρ=0 -> identique à `posterior` (indépendant) ; ρ=1 sur m DOUBLONS identiques ->
    compte UNE seule fois (plus de sur-confiance). Monotone : plus ρ est grand, plus la postérieure reste proche du prior."""
    if not (0.0 <= rho <= 1.0):
        return (ABSTENTION, None, f"corrélation invalide (ρ={rho}) : attendu dans [0,1]")
    if not (0.0 < prior < 1.0):
        return (ABSTENTION, None, f"prior dégénéré ({prior}) : doit être dans (0,1)")
    if not indices:
        return (ESTIMATION, prior, {"prior": prior, "n_indices": 0, "rho": rho, "n_eff": 0.0})
    lrs = []
    for (po, pn, obs) in indices:
        lr = lr_indice(po, pn, obs)
        if lr is None:
            return (ABSTENTION, None, f"indice à vraisemblance dégénérée (p_si_oui={po}, p_si_non={pn}) : refus")
        lrs.append(lr)
    k = len(lrs)
    facteur = 1.0 / (1.0 + (k - 1) * rho)              # = n_eff / k
    logit = _logit(prior) + facteur * sum(math.log(lr) for lr in lrs)
    p = _sigmoid(logit)
    return (ESTIMATION, p, {"prior": prior, "n_indices": k, "rho": rho, "n_eff": k * facteur})


def rho_empirique(signaux_par_cas):
    """Estime la corrélation moyenne entre indices à partir de l'historique : `signaux_par_cas` = liste, un par cas
    observé, d'un vecteur de signaux binaires (0/1) — un par indice, MÊME ordre. Renvoie la corrélation de Pearson
    moyenne sur toutes les paires d'indices (clampée à [0,1]), utilisable comme ρ dans `posterior_correle`."""
    cas = [[1.0 if v else 0.0 for v in vecteur] for vecteur in signaux_par_cas]
    if len(cas) < 2 or not cas[0]:
        return 0.0
    k = len(cas[0])
    n = len(cas)
    moy = [sum(cas[t][i] for t in range(n)) / n for i in range(k)]
    var = [sum((cas[t][i] - moy[i]) ** 2 for t in range(n)) for i in range(k)]
    cors, npaires = 0.0, 0
    for i in range(k):
        for j in range(i + 1, k):
            if var[i] <= 0 or var[j] <= 0:
                continue
            cov = sum((cas[t][i] - moy[i]) * (cas[t][j] - moy[j]) for t in range(n))
            cors += cov / math.sqrt(var[i] * var[j])
            npaires += 1
    if npaires == 0:
        return 0.0
    return max(0.0, min(1.0, cors / npaires))


if __name__ == "__main__":
    print("=== COMBINAISON BAYÉSIENNE D'ÉVIDENCE ===\n")
    # prior 10% ; deux tests assez fiables qui pointent « oui »
    r = posterior(0.10, [(0.9, 0.2, 1), (0.8, 0.3, 1)])
    print(" ", formule(r))
    # un indice « non » fait redescendre
    r2 = posterior(0.10, [(0.9, 0.2, 1), (0.85, 0.25, 0)])
    print(" ", formule(r2))
    # prior dégénéré -> abstention
    print(" ", formule(posterior(1.0, [(0.9, 0.2, 1)])))
    # vraisemblance dégénérée -> abstention (refus de fabriquer une certitude)
    print(" ", formule(posterior(0.3, [(1.0, 0.2, 1)])))
