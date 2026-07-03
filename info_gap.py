"""
PALIER 2 — DÉCISION INFO-GAP (Ben-Haim) : robustesse face à une incertitude SÉVÈRE, sans probabilités ni pire-cas
connu (brique 53, 2026-06-26).

Parfois on n'a NI distribution de probabilité NI borne d'erreur : juste une estimation nominale ũ et la conscience
qu'elle peut être fausse d'un montant INCONNU et non borné. L'info-gap modélise cet écart par une famille
d'ensembles d'incertitude EMBOÎTÉS U(α, ũ) qui grossissent avec l'« horizon » α ≥ 0 (U(0)={ũ}, α inconnu/illimité).

Deux fonctions d'immunité :
  • ROBUSTESSE  α̂(q, r_c) = le PLUS GRAND horizon α auquel la décision q garantit ENCORE une récompense ≥ r_c
    (= min sur U(α) de la récompense ≥ r_c). Grand α̂ = supporte beaucoup d'erreur de modèle avant de casser.
  • OPPORTUNITÉ β̂(q, r_w) = le PLUS PETIT horizon α auquel un résultat EXCEPTIONNEL (≥ r_w) devient possible.

LE THÉORÈME DE PRÉFÉRENCE (Ben-Haim) : la décision la plus robuste n'est PAS celle de meilleure performance NOMINALE.
La robustesse s'ACHÈTE en sacrifiant la performance prédite optimale ; les courbes α̂(r_c) des décisions se CROISENT
→ le classement DÉPEND de l'exigence r_c.

LE MODE D'ÉCHEC DÉMASQUÉ : choisir la décision de meilleure performance NOMINALE = SUR-CONFIANT (suppose
implicitement que le modèle ũ est exact, α=0). Quand la réalité dévie (α>0) cette décision casse l'exigence r_c plus
tôt qu'une décision plus robuste. La réponse honnête maximise α̂ pour le r_c requis, pas la performance prédite.
α̂(q, r_c) est une GARANTIE EXACTE : ∀u∈U(α̂), récompense ≥ r_c (vérifié, 0 violation). ABSTENTION si même le nominal
échoue r_c (α̂=0). Pur Python (scalaire ; U(α)=[ũ−α·s, ũ+α·s]).
"""
from __future__ import annotations

ROBUSTE = "robuste"
ABSTENTION = "abstention"


def pire_cas(recompense, u_nom, alpha, s=1.0, n=201):
    """min de `recompense` sur U(α)=[ũ−α·s, ũ+α·s] (grille). À α=0 : récompense(ũ)."""
    if alpha <= 0:
        return recompense(u_nom)
    lo, hi = u_nom - alpha * s, u_nom + alpha * s
    return min(recompense(lo + (hi - lo) * i / (n - 1)) for i in range(n))


def meilleur_cas(recompense, u_nom, alpha, s=1.0, n=201):
    """max de `recompense` sur U(α) (pour l'opportunité)."""
    if alpha <= 0:
        return recompense(u_nom)
    lo, hi = u_nom - alpha * s, u_nom + alpha * s
    return max(recompense(lo + (hi - lo) * i / (n - 1)) for i in range(n))


def robustesse(recompense, u_nom, r_c, s=1.0, alpha_max=10.0, n_alpha=4000, n_grid=201):
    """α̂(q, r_c) : plus grand horizon α tel que min_{u∈U(α)} récompense ≥ r_c. La récompense pire-cas est
    NON-CROISSANTE en α (ensembles emboîtés) → on scanne jusqu'à la 1ʳᵉ rupture. 0 si le nominal échoue déjà ;
    alpha_max si jamais rompu (renvoyé comme borne)."""
    if recompense(u_nom) < r_c:
        return 0.0
    best = 0.0
    for k in range(1, n_alpha + 1):
        a = alpha_max * k / n_alpha
        if pire_cas(recompense, u_nom, a, s, n_grid) >= r_c:
            best = a
        else:
            break
    return best


def opportunite(recompense, u_nom, r_w, s=1.0, alpha_max=10.0, n_alpha=4000, n_grid=201):
    """β̂(q, r_w) : plus petit horizon α tel que max_{u∈U(α)} récompense ≥ r_w (un coup de chance devient possible).
    Le meilleur-cas est NON-DÉCROISSANT en α. 0 si le nominal atteint déjà r_w ; alpha_max si jamais atteint."""
    if recompense(u_nom) >= r_w:
        return 0.0
    for k in range(1, n_alpha + 1):
        a = alpha_max * k / n_alpha
        if meilleur_cas(recompense, u_nom, a, s, n_grid) >= r_w:
            return a
    return alpha_max


def choisis(decisions, u_nom, r_c, s=1.0, **kw):
    """Choisit la décision la PLUS ROBUSTE pour l'exigence r_c. `decisions` = dict nom→fonction récompense(u).
    Renvoie (ROBUSTE, nom*, {nom: (α̂, récompense_nominale)}) ou (ABSTENTION, None, table) si aucune ne garantit r_c."""
    table = {nom: (robustesse(f, u_nom, r_c, s, **kw), f(u_nom)) for nom, f in decisions.items()}
    faisables = {nom: v for nom, v in table.items() if v[0] > 0}
    if not faisables:
        return (ABSTENTION, None, table)
    gagnant = max(faisables, key=lambda nom: faisables[nom][0])
    return (ROBUSTE, gagnant, table)


def formule(res, r_c) -> str:
    if res[0] == ABSTENTION:
        return f"Aucune décision ne garantit r_c={r_c} même au nominal : incertitude trop sévère (α̂=0)."
    gagnant, table = res[1], res[2]
    a, nom_perf = table[gagnant]
    nominal_best = max(table, key=lambda n: table[n][1])
    note = "" if gagnant == nominal_best else (
        f" — PAS la meilleure performance nominale ({nominal_best}={table[nominal_best][1]:g}), "
        f"mais la plus immunisée contre l'erreur de modèle (la choisir serait sur-confiant).")
    return (f"Décision la plus robuste : « {gagnant} » (α̂={a:.3f} : garantit récompense ≥ {r_c} tant que l'erreur "
            f"sur le modèle reste ≤ {a:.3f}·s).{note}")


if __name__ == "__main__":
    print("=== DÉCISION INFO-GAP — robustesse > performance nominale ===\n")
    R_A = lambda u: 100 * u          # agressif : meilleur nominal, fragile
    R_B = lambda u: 40 + 30 * u      # conservateur : plancher, dégrade lentement
    u_nom = 1.0
    print(f"  Nominal (ũ=1) : A={R_A(1):g}  B={R_B(1):g}  (A meilleur prédit)")
    for r_c in (50, 65):
        aA = robustesse(R_A, u_nom, r_c)
        aB = robustesse(R_B, u_nom, r_c)
        gagne = "B" if aB > aA else "A"
        print(f"  r_c={r_c} : α̂_A={aA:.3f}  α̂_B={aB:.3f}  -> le plus robuste = {gagne}")
    print()
    print(" ", formule(choisis({"A": R_A, "B": R_B}, u_nom, 50), 50))
    print("  Opportunité (windfall r_w=120) : β̂_A =", round(opportunite(R_A, u_nom, 120), 3),
          " β̂_B =", round(opportunite(R_B, u_nom, 120), 3), "(A plus opportun)")
