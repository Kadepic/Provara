"""
PALIER 2 — PARADOXE DE LORD (score de changement vs ANCOVA) : croire qu'une donnée pré/post observationnelle livre « l'»
effet d'un groupe est sur-confiant (brique 119, 2026-06-28).

Deux analystes étudient l'effet d'un GROUPE (régime, sexe, traitement) sur une mesure, avec une valeur INITIALE X et une
valeur FINALE Y. Sur les MÊMES données :
  • Analyste 1 — SCORE DE CHANGEMENT : compare le gain moyen Y−X entre groupes. Trouve AUCUNE différence (gains égaux).
  • Analyste 2 — ANCOVA : régresse Y sur X et compare les moyennes AJUSTÉES (coefficient de groupe). Trouve une différence
    SIGNIFICATIVE.
Les deux conclusions s'OPPOSENT — et chacune est correcte dans son modèle. La raison : ils répondent à des questions
DIFFÉRENTES — E[Y−X | groupe] (le changement) vs E[Y | X, groupe] (l'ajusté). Quand la pente intra-groupe b ≠ 1
(régression vers la moyenne), l'écart ANCOVA = écart de gains + (1−b)·(écart des baselines). « L'effet du groupe » n'est
donc PAS défini par les seules données : il dépend du MODÈLE CAUSAL (X est-il un confondeur à ajuster, ou une partie de
la trajectoire ?).

LE MODE D'ÉCHEC DÉMASQUÉ : annoncer « l'effet » sans expliciter le modèle causal est SUR-CONFIANT — deux analyses
légitimes le contredisent. Distinct de Simpson (87, renversement par confondeur) et causal (31, ATE/IPW). ABSTENTION si
données insuffisantes. Pur Python, rng seedé.
"""
from __future__ import annotations

ABSTENTION = "abstention"
ANALYSE = "analyse"


def _moyenne(xs):
    return sum(xs) / len(xs)


def genere_groupe(moyenne_base, b, n, rng, sigma_x=5.0, sigma_e=3.0, gain=0.0):
    """Groupe avec baseline ~ N(moyenne_base, σx) et Y = moyenne_base + gain + b·(X−moyenne_base) + bruit.
    E[Y−X] = gain ; pente intra-groupe de Y sur X = b."""
    out = []
    for _ in range(n):
        x = rng.gauss(moyenne_base, sigma_x)
        y = moyenne_base + gain + b * (x - moyenne_base) + rng.gauss(0, sigma_e)
        out.append((x, y))
    return out


def score_changement(A, B):
    """Différence des gains moyens Y−X entre les deux groupes (analyste 1)."""
    gA = _moyenne([y - x for x, y in A])
    gB = _moyenne([y - x for x, y in B])
    return gA - gB, gA, gB


def _ols3(data):
    """OLS de Y sur [1, X, G] ; renvoie (intercept, pente_X, coef_groupe)."""
    XtX = [[0.0] * 3 for _ in range(3)]
    Xty = [0.0] * 3
    for x, y, g in data:
        row = [1.0, x, g]
        for i in range(3):
            Xty[i] += row[i] * y
            for j in range(3):
                XtX[i][j] += row[i] * row[j]
    M = [XtX[i][:] + [Xty[i]] for i in range(3)]
    for c in range(3):
        p = max(range(c, 3), key=lambda r: abs(M[r][c]))
        M[c], M[p] = M[p], M[c]
        pv = M[c][c]
        M[c] = [v / pv for v in M[c]]
        for r in range(3):
            if r != c:
                f = M[r][c]
                M[r] = [M[r][k] - f * M[c][k] for k in range(4)]
    return M[0][3], M[1][3], M[2][3]


def ancova(A, B):
    """Coefficient de groupe (A vs B) dans la régression Y ~ X + groupe (analyste 2)."""
    data = [(x, y, 1.0) for x, y in A] + [(x, y, 0.0) for x, y in B]
    _, pente_x, coef_groupe = _ols3(data)
    return coef_groupe, pente_x


def analyse(A, B):
    """Façade : score de changement vs ANCOVA. (ANALYSE, {diff_changement, diff_ancova, divergence, pente}) ou
    (ABSTENTION)."""
    if len(A) < 30 or len(B) < 30:
        return (ABSTENTION, "groupes trop petits")
    diff_chg, gA, gB = score_changement(A, B)
    diff_anc, pente = ancova(A, B)
    divergence = abs(diff_chg) < 0.5 and abs(diff_anc) > 1.0
    return (ANALYSE, {"diff_changement": diff_chg, "diff_ancova": diff_anc, "pente_intra": pente,
                      "gain_A": gA, "gain_B": gB, "divergence": divergence})


def formule(res) -> str:
    if res[0] == ABSTENTION:
        return f"Pas d'analyse : {res[1]}."
    i = res[1]
    return (f"Score de changement : différence des gains = {i['diff_changement']:.2f} (≈ aucune). ANCOVA (pente intra "
            f"{i['pente_intra']:.2f}) : coefficient de groupe = {i['diff_ancova']:.2f} (différence SIGNIFICATIVE). Mêmes "
            f"données, conclusions OPPOSÉES. Annoncer « l'effet du groupe » sans modèle causal est sur-confiant.")


if __name__ == "__main__":
    import random
    rng = random.Random(0)
    print("=== PARADOXE DE LORD (score de changement vs ANCOVA) ===\n")
    A = genere_groupe(70, 0.6, 3000, rng)      # baseline 70, pente 0.6, gain 0
    B = genere_groupe(60, 0.6, 3000, rng)      # baseline 60, pente 0.6, gain 0
    st, info = analyse(A, B)
    print(" ", formule((st, info)))
