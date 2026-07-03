"""
PALIER 2 — FONCTIONS DE CROYANCE (Dempster-Shafer) : combiner des évidences EN CONFLIT sans fabriquer de fausse
certitude (brique 50, 2026-06-26).

Paradigme « hors-calibration » (probabilité IMPRÉCISE) : au lieu d'une proba ponctuelle p(A), une fonction de masse
m attribue du poids à des SOUS-ENSEMBLES d'hypothèses ; l'ignorance vit explicitement sur Θ tout entier. À toute
hypothèse A on associe un INTERVALLE [Bel(A), Pl(A)] (croyance = preuve POUR ; plausibilité = 1 − preuve CONTRE).
Bel ≤ Pl ; l'écart Pl−Bel = l'ignorance assumée. Une proba ponctuelle écrase cet écart → c'est précisément la fausse
précision que l'invariant T2 interdit.

LE MODE D'ÉCHEC DÉMASQUÉ (paradoxe de Zadeh) : la règle de combinaison de DEMPSTER NORMALISE par (1−K) où K est la
masse de conflit. Sur deux sources fortement en désaccord, K→1 et la normalisation AMPLIFIE une hypothèse marginale
jusqu'à la CERTITUDE absurde. Ex. : médecin 1 = {méningite 0.99, tumeur 0.01}, médecin 2 = {commotion 0.99,
tumeur 0.01} → Dempster conclut tumeur avec Bel=1.0, alors que les DEUX la jugeaient la MOINS probable. C'est de la
sur-confiance manufacturée à partir d'un désaccord.

LA RÉPARATION (règle de YAGER) : ne pas normaliser ; REVERSER la masse de conflit K sur Θ (ignorance). La même
évidence conflictuelle donne alors Bel(tumeur) minuscule et Pl(tumeur)=1 → l'intervalle [≈0, 1] dit honnêtement
« je ne sais pas » au lieu d'affirmer. Sur des évidences CONCORDANTES (K petit) Dempster et Yager coïncident et
resserrent correctement la croyance. Pur Python (ensembles de sous-ensembles, frozenset).
"""
from __future__ import annotations

ABSTENTION = "abstention"
COMBINAISON = "combinaison"
_TOL = 1e-9


def _norme(m):
    """Normalise les clés en frozenset et vérifie une fonction de masse valide (m(∅)=0, masses≥0, somme≈1)."""
    out = {}
    for k, v in m.items():
        fk = frozenset(k)
        if not fk:
            if v > _TOL:
                raise ValueError("masse sur l'ensemble vide ∅ interdite")
            continue
        if v < -_TOL:
            raise ValueError(f"masse négative sur {set(fk)}")
        out[fk] = out.get(fk, 0.0) + float(v)
    s = sum(out.values())
    if abs(s - 1.0) > 1e-6:
        raise ValueError(f"les masses ne somment pas à 1 (somme={s:.6f})")
    return out


def cadre(*masses):
    """Cadre de discernement Θ = union de tous les éléments apparaissant dans les fonctions de masse."""
    theta = set()
    for m in masses:
        for k in m:
            theta |= set(k)
    return frozenset(theta)


def belief(m, A):
    """Bel(A) = Σ_{B ⊆ A} m(B) : la masse ENTIÈREMENT engagée en faveur de A (preuve POUR, sans le bénéfice du doute)."""
    m = _norme(m)
    A = frozenset(A)
    return sum(v for B, v in m.items() if B <= A)


def plausibility(m, A):
    """Pl(A) = Σ_{B ∩ A ≠ ∅} m(B) : tout ce qui n'EXCLUT pas A (preuve POUR + part de doute compatible). Pl ≥ Bel."""
    m = _norme(m)
    A = frozenset(A)
    return sum(v for B, v in m.items() if B & A)


def intervalle_croyance(m, A):
    """Intervalle épistémique [Bel(A), Pl(A)]. Sa LARGEUR = l'ignorance assumée sur A (0 = proba ponctuelle nette)."""
    return (belief(m, A), plausibility(m, A))


def conflit(m1, m2):
    """Masse de CONFLIT K = Σ_{B ∩ C = ∅} m1(B)·m2(C) entre deux évidences. K→1 = désaccord quasi total."""
    m1, m2 = _norme(m1), _norme(m2)
    return sum(v1 * v2 for B, v1 in m1.items() for C, v2 in m2.items() if not (B & C))


def combine_dempster(m1, m2):
    """Règle de DEMPSTER (normalisée par 1−K). Renvoie la fonction de masse combinée, ou None si conflit TOTAL (K≈1).
    ⚠️ Sur fort conflit, la normalisation FABRIQUE de la certitude (paradoxe de Zadeh) — démasqué par le validateur."""
    m1, m2 = _norme(m1), _norme(m2)
    brut, K = {}, 0.0
    for B, v1 in m1.items():
        for C, v2 in m2.items():
            inter = B & C
            if inter:
                brut[inter] = brut.get(inter, 0.0) + v1 * v2
            else:
                K += v1 * v2
    if K > 1.0 - 1e-12:
        return None  # conflit total : combinaison indéfinie -> ABSTENTION
    return {A: v / (1.0 - K) for A, v in brut.items()}


def combine_yager(m1, m2, theta=None):
    """Règle de YAGER : NE normalise pas ; reverse le conflit K sur Θ (ignorance). Honnête sous fort conflit :
    [Bel, Pl] s'élargit au lieu d'affirmer. Coïncide avec Dempster quand K≈0."""
    m1, m2 = _norme(m1), _norme(m2)
    if theta is None:
        theta = cadre(m1, m2)
    theta = frozenset(theta)
    brut, K = {}, 0.0
    for B, v1 in m1.items():
        for C, v2 in m2.items():
            inter = B & C
            if inter:
                brut[inter] = brut.get(inter, 0.0) + v1 * v2
            else:
                K += v1 * v2
    brut[theta] = brut.get(theta, 0.0) + K  # le conflit devient de l'ignorance, pas de la certitude
    return brut


def combine(m1, m2, regle="yager", theta=None):
    """Façade : combine deux évidences. Défaut = YAGER (robuste au conflit). Renvoie
    (COMBINAISON, masse, infos) ou (ABSTENTION, None, raison). infos porte K (conflit) — un K élevé est un signal."""
    try:
        m1n, m2n = _norme(m1), _norme(m2)
    except ValueError as e:
        return (ABSTENTION, None, str(e))
    K = conflit(m1n, m2n)
    if regle == "dempster":
        res = combine_dempster(m1n, m2n)
        if res is None:
            return (ABSTENTION, None, f"conflit total (K≈{K:.4f}) : Dempster indéfini")
        return (COMBINAISON, res, {"conflit": K, "regle": "dempster"})
    if regle == "yager":
        return (COMBINAISON, combine_yager(m1n, m2n, theta), {"conflit": K, "regle": "yager"})
    return (ABSTENTION, None, f"règle inconnue : {regle}")


def formule(res, focal=None) -> str:
    """Parole honnête. Si `focal` (une hypothèse) est donné, rapporte son intervalle [Bel, Pl]."""
    statut = res[0]
    if statut == ABSTENTION:
        return f"Je ne peux pas combiner ces évidences : {res[2]}."
    m, infos = res[1], res[2]
    base = f"Évidences combinées (règle {infos['regle']}, conflit K={infos['conflit']:.3f})"
    if focal is not None:
        bel, pl = belief(m, focal), plausibility(m, focal)
        gap = pl - bel
        nom = "/".join(sorted(focal)) if not isinstance(focal, str) else focal
        return (f"{base}. Pour « {nom} » : croyance {bel:.3f}, plausibilité {pl:.3f} "
                f"(je ne peux pas être plus précis qu'à ±{gap/2:.3f} — c'est mon ignorance assumée, pas une certitude).")
    return base + "."


if __name__ == "__main__":
    print("=== FONCTIONS DE CROYANCE (Dempster-Shafer) — le paradoxe de Zadeh ===\n")
    m1 = {("meningite",): 0.99, ("tumeur",): 0.01}
    m2 = {("commotion",): 0.99, ("tumeur",): 0.01}
    print(f"  Médecin 1 : {m1}")
    print(f"  Médecin 2 : {m2}")
    print(f"  Conflit K = {conflit(m1, m2):.4f}\n")
    d = combine_dempster(m1, m2)
    print(f"  DEMPSTER  -> Bel(tumeur)={belief(d, ('tumeur',)):.3f}  (CERTITUDE ABSURDE : tous deux la jugeaient improbable)")
    y = combine_yager(m1, m2)
    bel, pl = intervalle_croyance(y, ("tumeur",))
    print(f"  YAGER     -> tumeur ∈ [Bel={bel:.3f}, Pl={pl:.3f}]  (honnête : « je ne sais pas », vu le désaccord)\n")
    print("  Évidences CONCORDANTES (K petit) : Dempster et Yager s'accordent et resserrent —")
    a = {("M",): 0.8, ("M", "C"): 0.2}
    b = {("M",): 0.7, ("M", "C"): 0.3}
    print(f"   K={conflit(a, b):.3f} ; Dempster Bel(M)={belief(combine_dempster(a, b), ('M',)):.3f}")
    print(" ", formule(combine(m1, m2, "yager"), focal=("tumeur",)))
