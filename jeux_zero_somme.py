"""
PALIER 2 — JEUX À SOMME NULLE & STRATÉGIE DE SÉCURITÉ (maximin, théorème minimax de von Neumann) (brique 70,
2026-06-27).

Face à un adversaire STRATÉGIQUE (jeu à somme nulle, matrice de gains A pour le joueur-ligne), supposer qu'il jouera
une stratégie PRÉCISE et y répondre au mieux (best-response à une croyance ponctuelle) est SUR-CONFIANT : si
l'adversaire dévie pour exploiter, le gain peut tomber bien EN DESSOUS de la valeur du jeu. La stratégie de SÉCURITÉ
(maximin) maximise le pire-cas et GARANTIT la valeur du jeu v contre N'IMPORTE QUEL adversaire :
    v = max_x min_j (xᵀA)_j = min_y max_i (Ay)_i        (théorème minimax : maximin = minimax = v).

On calcule v et les stratégies optimales par JEU FICTIF (Brown-Robinson) : chaque joueur réplique au mieux à
l'historique empirique de l'autre ; les stratégies moyennes convergent vers l'optimum et fournissent un ENCADREMENT
L ≤ v ≤ U qui se resserre.

LE MODE D'ÉCHEC DÉMASQUÉ : le best-response à un adversaire présumé est EXPLOITABLE (pire-cas < v) ; la stratégie
maximin garantit ≥ v quoi qu'il arrive. ABSTENTION si matrice vide/mal formée. Pur Python.
"""
from __future__ import annotations

ABSTENTION = "abstention"
JEU = "jeu"


def _dims(A):
    return len(A), len(A[0])


def securite_ligne(A, x):
    """Gain GARANTI de la stratégie-ligne x = min_j (xᵀA)_j (pire colonne adverse)."""
    m, n = _dims(A)
    return min(sum(x[i] * A[i][j] for i in range(m)) for j in range(n))


def plafond_colonne(A, y):
    """Plafond de la stratégie-colonne y = max_i (Ay)_i (meilleure ligne)."""
    m, n = _dims(A)
    return max(sum(A[i][j] * y[j] for j in range(n)) for i in range(m))


def meilleure_reponse_ligne(A, y):
    """Meilleure réponse pure de la ligne à une colonne y : argmax_i (Ay)_i."""
    m, n = _dims(A)
    vals = [sum(A[i][j] * y[j] for j in range(n)) for i in range(m)]
    return max(range(m), key=lambda i: vals[i])


def jeu_fictif(A, iters=5000):
    """Jeu fictif (Brown-Robinson) : renvoie (valeur, x_moy, y_moy, (L, U)). Converge vers l'optimum (zéro-somme)."""
    m, n = _dims(A)
    rc = [0] * m; cc = [0] * n
    colvec = [0.0] * m      # gain-ligne cumulé selon l'historique des colonnes
    rowvec = [0.0] * n      # gain-ligne cumulé selon l'historique des lignes
    cc[0] = 0
    for k in range(m):
        colvec[k] += A[k][0]
    cc[0] = 1
    for _ in range(iters):
        i = max(range(m), key=lambda r: colvec[r])      # ligne best-responds à l'historique colonne
        rc[i] += 1
        for j in range(n):
            rowvec[j] += A[i][j]
        j = min(range(n), key=lambda c: rowvec[c])       # colonne best-responds (minimise) à l'historique ligne
        cc[j] += 1
        for k in range(m):
            colvec[k] += A[k][j]
    tot_r, tot_c = sum(rc), sum(cc)
    x = [c / tot_r for c in rc]
    y = [c / tot_c for c in cc]
    L, U = securite_ligne(A, x), plafond_colonne(A, y)
    return ((L + U) / 2, x, y, (L, U))


def analyse(A, iters=5000):
    """Façade : (JEU, {valeur, x, y, encadrement}) ou (ABSTENTION, raison)."""
    if not A or not A[0] or any(len(r) != len(A[0]) for r in A):
        return (ABSTENTION, "matrice vide ou mal formée")
    v, x, y, bornes = jeu_fictif(A, iters)
    return (JEU, {"valeur": v, "x": x, "y": y, "encadrement": bornes})


def formule(res) -> str:
    if res[0] == ABSTENTION:
        return f"Jeu non résolu : {res[1]}."
    info = res[1]
    return (f"Valeur du jeu ≈ {info['valeur']:.3f} ; la stratégie de SÉCURITÉ (maximin) garantit ce gain contre tout "
            f"adversaire. Répondre au mieux à un adversaire présumé serait sur-confiant (exploitable).")


if __name__ == "__main__":
    print("=== JEUX À SOMME NULLE — sécurité maximin ===\n")
    pennies = [[1, -1], [-1, 1]]          # matching pennies : valeur 0, optimal (0.5,0.5)
    st, info = analyse(pennies)
    print(f"  Matching pennies : valeur≈{info['valeur']:.3f}, x_moy={[round(v,2) for v in info['x']]}, "
          f"encadrement={tuple(round(v,3) for v in info['encadrement'])}")
    i0 = meilleure_reponse_ligne(pennies, [0.5, 0.5])
    print(f"   best-response pur à (0.5,0.5) = ligne {i0}, pire-cas = {min(pennies[i0])} (EXPLOITABLE < valeur 0)")
    print(f"   sécurité de la stratégie maximin = {securite_ligne(pennies, info['x']):.3f} (≥ valeur, garanti)")
    jeu = [[3, -1, 2], [-2, 4, -1], [1, -1, 0]]
    st2, info2 = analyse(jeu)
    print(f"\n  Jeu 3×3 : valeur≈{info2['valeur']:.3f}, encadrement={tuple(round(v,3) for v in info2['encadrement'])}")
    print(" ", formule(analyse(jeu)))
