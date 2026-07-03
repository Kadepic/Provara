"""
PALIER 2 — CALIBRATION DE SÉQUENCE (confiance d'une génération multi-étapes, type LLM, brique 47, 2026-06-26).

« Un modèle génère une RÉPONSE en plusieurs étapes (tokens, étapes de raisonnement, sous-décisions). Quelle confiance
honnête accorder à la séquence ENTIÈRE ? » La séquence n'est correcte que si TOUTES les étapes le sont → la confiance
de séquence = PRODUIT des confiances par étape. Deux pièges très « LLM » :
  • la sur-confiance par étape se COMPOSE : un modèle un peu trop sûr à chaque token devient massivement trop sûr sur
    la séquence (le produit amplifie le biais) → SUR-CONFIANCE.
  • prendre la confiance d'UNE étape (la 1ʳᵉ, ou le max) pour la séquence ignore que tout doit être juste → idem.

Remède : RECALIBRER la confiance PAR ÉTAPE (isotonique, hors-échantillon) pour qu'elle reflète la vraie probabilité de
justesse de l'étape, PUIS multiplier. INVARIANT (jugé par calibration.py) : la confiance de séquence recalibrée vérifie
P(séquence entièrement correcte) ≈ confiance annoncée, là où le produit BRUT (sur-confiant par étape) sur-couvre.
ABSTENTION si jeu de calibration trop petit. Pur Python (réutilise l'isotonique de classif_calibree).
"""
from __future__ import annotations

import classif_calibree as _CC

ABSTENTION = "abstention"
ESTIMATION = "estimation"


def confiance_sequence(confiances):
    """Confiance de la séquence ENTIÈRE = produit des confiances par étape (toutes les étapes doivent être justes)."""
    p = 1.0
    for c in confiances:
        p *= c
    return p


def ajuste_par_etape(confiances_plates, justesses_plates):
    """Apprend un recalibrateur ISOTONIQUE par étape sur des couples (confiance_étape, étape_juste∈{0,1}) agrégés sur
    toutes les positions. Renvoie un Calibrateur ou None (jeu trop petit)."""
    return _CC.ajuste_isotonique(confiances_plates, justesses_plates)


def confiance_sequence_calibree(calibrateur, confiances):
    """Confiance de séquence APRÈS recalibration par étape : produit des probabilités d'étape calibrées. Renvoie
    (ESTIMATION, proba) ou (ABSTENTION, None) si pas de calibrateur."""
    if calibrateur is None:
        return (ABSTENTION, None)
    p = 1.0
    for c in confiances:
        p *= calibrateur.applique(c)
    return (ESTIMATION, p)


def formule(res) -> str:
    if res[0] == ABSTENTION:
        return "Je ne peux pas donner de confiance de séquence honnête : pas assez de données pour calibrer les étapes."
    p = res[1]
    return (f"Confiance que la réponse ENTIÈRE soit correcte ≈ {round(p*100)}% (étapes recalibrées puis combinées). "
            f"Le produit des confiances brutes, lui, surestimerait — la sur-confiance par étape se compose.")


if __name__ == "__main__":
    import random
    print("=== CALIBRATION DE SÉQUENCE (type LLM) ===\n")
    rng = random.Random(0)
    L = 5                       # 5 étapes par séquence
    T_OVER = 0.45               # le modèle rapporte c = q**T_OVER  (>q) -> sur-confiant par étape

    def fabrique(n):
        seqs = []
        for _ in range(n):
            confs, justes = [], []
            for _ in range(L):
                q = rng.uniform(0.6, 0.98)            # vraie proba de justesse de l'étape
                c = q ** T_OVER                        # confiance RAPPORTÉE (sur-confiante)
                juste = 1 if rng.random() < q else 0
                confs.append(c); justes.append(juste)
            seqs.append((confs, justes))
        return seqs

    calib = fabrique(400)
    plates_c = [c for confs, _ in calib for c in confs]
    plates_j = [j for _, justes in calib for j in justes]
    cal = ajuste_par_etape(plates_c, plates_j)
    test = fabrique(2000)
    # calibration au niveau séquence : brut vs recalibré
    import calibration as CAL
    cb, jb, ck, jk = [], [], [], []
    for confs, justes in test:
        seq_ok = 1.0 if all(justes) else 0.0
        cb.append(confiance_sequence(confs)); jb.append(seq_ok)
        ck.append(confiance_sequence_calibree(cal, confs)[1]); jk.append(seq_ok)
    print("  BRUT     :", CAL.formule(CAL.est_calibre(cb, jb), "forecast"))
    print("  RECALIBRÉ:", CAL.formule(CAL.est_calibre(ck, jk), "forecast"))
