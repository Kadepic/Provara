"""
PALIER 2 — MULTICALIBRATION : calibration PAR SOUS-GROUPE (brique, 2026-06-26).

« Mon modèle est calibré : un “80 %” s'avère juste 80 % du temps. » Vrai GLOBALEMENT — mais cette moyenne peut CACHER
qu'il est SUR-CONFIANT sur un sous-groupe (et sous-confiant sur un autre, les deux s'annulant). Pour une personne du
sous-groupe sur-confiant, le « 80 % » ment systématiquement. La calibration MARGINALE ne suffit donc pas : c'est la
calibration CONDITIONNELLE au groupe qui compte (équité, fiabilité ciblée).

Le remède : MULTICALIBRER — recalibrer DANS chaque groupe (carte bac→fréquence empirique par groupe, apprise sur un jeu
de calibration). INVARIANT (jugé par calibration.py appliqué PAR GROUPE) : après multicalibration, AUCUN groupe n'est
sur-confiant ; le modèle brut, lui, a beau être calibré en moyenne, reste sur-confiant sur le groupe lésé. ABSTENTION si
un groupe a trop peu d'exemples pour estimer sa correction. Pur Python.
"""
from __future__ import annotations

ABSTENTION = "abstention"
ESTIMATION = "estimation"
N_MIN_GROUPE = 50


def _bac(p, n_bins):
    b = int(p * n_bins)
    return min(n_bins - 1, max(0, b))


def ajuste(probs, ys, groupes, n_bins: int = 10):
    """Apprend une carte de recalibration PAR GROUPE : pour chaque (groupe, bac de proba), la fréquence empirique d'issue.
    Renvoie (ESTIMATION, {n_bins, cartes, global}, None) ou (ABSTENTION, None, raison)."""
    par_groupe = {}
    for p, y, g in zip(probs, ys, groupes):
        par_groupe.setdefault(g, []).append((p, y))
    petits = [g for g, v in par_groupe.items() if len(v) < N_MIN_GROUPE]
    if petits:
        return (ABSTENTION, None, f"groupe(s) trop petit(s) pour multicalibrer : {petits}")
    cartes = {}
    for g, v in par_groupe.items():
        somme = [0.0] * n_bins
        compte = [0] * n_bins
        for p, y in v:
            b = _bac(p, n_bins)
            somme[b] += y; compte[b] += 1
        # bac vide -> on garde le centre du bac (pas de correction)
        cartes[g] = [(somme[b] / compte[b] if compte[b] > 0 else (b + 0.5) / n_bins) for b in range(n_bins)]
    return (ESTIMATION, {"n_bins": n_bins, "cartes": cartes}, None)


def applique(modele, p, groupe):
    """Probabilité multicalibrée pour un point de `groupe`. Si le groupe est inconnu, renvoie p inchangé (abstention de
    correction)."""
    carte = modele["cartes"].get(groupe)
    if carte is None:
        return p
    return carte[_bac(p, modele["n_bins"])]


def applique_lot(modele, probs, groupes):
    return [applique(modele, p, g) for p, g in zip(probs, groupes)]


def formule(res) -> str:
    if res[0] == ABSTENTION:
        return f"Je ne peux pas multicalibrer : {res[2]}."
    groupes = list(res[1]["cartes"].keys())
    return (f"Probabilités recalibrées DANS chaque sous-groupe {groupes} : un modèle calibré en moyenne peut rester "
            f"sur-confiant sur un groupe — la multicalibration garantit qu'aucun groupe n'est trompé.")


if __name__ == "__main__":
    import random
    rng = random.Random(0)
    # modèle calibré GLOBALEMENT mais : groupe A sous-confiant (+0.1), groupe B sur-confiant (−0.1)
    probs, ys, grp = [], [], []
    for _ in range(4000):
        g = "A" if rng.random() < 0.5 else "B"
        p = rng.uniform(0.2, 0.8)
        taux = min(1.0, p + 0.1) if g == "A" else max(0.0, p - 0.1)
        probs.append(p); ys.append(1.0 if rng.random() < taux else 0.0); grp.append(g)
    st, modele, _ = ajuste(probs, ys, grp, n_bins=10)
    print("=== MULTICALIBRATION — calibré en moyenne, sur-confiant sur un groupe ===\n")
    print(f"  modèle brut p=0.7 : groupe A reste 0.70, groupe B reste 0.70 (mais B vaut ~0.60)")
    print(f"  multicalibré p=0.7 : A -> {applique(modele, 0.7, 'A'):.2f}, B -> {applique(modele, 0.7, 'B'):.2f}")
    print(" ", formule((st, modele, None)))
