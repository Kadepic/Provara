"""
PALIER 2 — QUARTET D'ANSCOMBE / INSUFFISANCE DES STATISTIQUES RÉSUMÉES : conclure « même relation » de stats résumées
identiques est sur-confiant (brique 115, 2026-06-28).

Quatre jeux de données (Anscombe 1973) ont des STATISTIQUES RÉSUMÉES IDENTIQUES — même moyenne et variance de x et y, même
corrélation (0.816), même droite de régression (y = 3 + 0.5x). Pourtant leurs STRUCTURES sont radicalement différentes :
  • I   : relation linéaire propre.
  • II  : relation COURBE (parabole) — la droite est trompeuse.
  • III : linéaire parfaite SAUF une VALEUR ABERRANTE qui tire la pente.
  • IV  : tous les x identiques sauf UN point à FORT LEVIER qui détermine seul la droite.
Se fier aux seules statistiques résumées (ou à une droite ajustée) sans REGARDER les données / les résidus est
SUR-CONFIANT : des résumés d'ordre faible ne capturent ni la non-linéarité, ni les valeurs aberrantes, ni le levier.

LA CORRECTION : examiner les DIAGNOSTICS — résidu maximal (aberrant), gain d'un terme quadratique (non-linéarité), levier
maximal (point influent). Chacun démasque une pathologie que les stats résumées cachent.

LE MODE D'ÉCHEC DÉMASQUÉ : « stats identiques ⇒ même relation » est sur-confiant. Distinct de regression_moyenne (86) et
ridge (89). ABSTENTION si données insuffisantes. Pur Python (moindres carrés maison).
"""
from __future__ import annotations

ABSTENTION = "abstention"
ANALYSE = "analyse"

_X = [10, 8, 13, 9, 11, 14, 6, 4, 12, 7, 5]
QUARTET = {
    "I": (_X, [8.04, 6.95, 7.58, 8.81, 8.33, 9.96, 7.24, 4.26, 10.84, 4.82, 5.68]),
    "II": (_X, [9.14, 8.14, 8.74, 8.77, 9.26, 8.10, 6.13, 3.10, 9.13, 7.26, 4.74]),
    "III": (_X, [7.46, 6.77, 12.74, 7.11, 7.81, 8.84, 6.08, 5.39, 8.15, 6.42, 5.73]),
    "IV": ([8, 8, 8, 8, 8, 8, 8, 19, 8, 8, 8], [6.58, 5.76, 7.71, 8.84, 8.47, 7.04, 5.25, 12.50, 5.56, 7.91, 6.89]),
}


def _moyenne(xs):
    return sum(xs) / len(xs)


def _variance(xs):
    m = _moyenne(xs)
    return sum((x - m) ** 2 for x in xs) / len(xs)


def regression(xs, ys):
    """Droite des moindres carrés : (intercept a, pente b, corrélation r)."""
    mx, my = _moyenne(xs), _moyenne(ys)
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    sxx = sum((x - mx) ** 2 for x in xs)
    syy = sum((y - my) ** 2 for y in ys)
    b = sxy / sxx
    a = my - b * mx
    r = sxy / (sxx * syy) ** 0.5 if sxx * syy > 0 else 0.0
    return a, b, r


def stats_resumees(xs, ys):
    """(moy_x, var_x, moy_y, var_y, corr, intercept, pente) arrondis — ce que « tout le monde » regarde."""
    a, b, r = regression(xs, ys)
    return (round(_moyenne(xs), 2), round(_variance(xs), 2), round(_moyenne(ys), 2),
            round(_variance(ys), 2), round(r, 2), round(a, 2), round(b, 2))


def _resol3(A, y):
    """Résout un système 3×3 par élimination de Gauss."""
    M = [row[:] + [y[i]] for i, row in enumerate(A)]
    for c in range(3):
        p = max(range(c, 3), key=lambda r: abs(M[r][c]))
        M[c], M[p] = M[p], M[c]
        piv = M[c][c]
        M[c] = [v / piv for v in M[c]]
        for r in range(3):
            if r != c:
                f = M[r][c]
                M[r] = [M[r][k] - f * M[c][k] for k in range(4)]
    return [M[r][3] for r in range(3)]


def diagnostics(xs, ys):
    """Diagnostics qui DISTINGUENT des jeux à stats résumées identiques."""
    n = len(xs)
    a, b, _ = regression(xs, ys)
    residus = [ys[i] - (a + b * xs[i]) for i in range(n)]
    rss_lin = sum(e * e for e in residus)
    # ajustement quadratique y = c0 + c1 x + c2 x²
    Sx = sum(xs); Sx2 = sum(x * x for x in xs); Sx3 = sum(x ** 3 for x in xs); Sx4 = sum(x ** 4 for x in xs)
    Sy = sum(ys); Sxy = sum(x * y for x, y in zip(xs, ys)); Sx2y = sum(x * x * y for x, y in zip(xs, ys))
    try:
        c0, c1, c2 = _resol3([[n, Sx, Sx2], [Sx, Sx2, Sx3], [Sx2, Sx3, Sx4]], [Sy, Sxy, Sx2y])
        rss_quad = sum((ys[i] - (c0 + c1 * xs[i] + c2 * xs[i] ** 2)) ** 2 for i in range(n))
        gain_quad = 1 - rss_quad / rss_lin if rss_lin > 0 else 0.0
    except (ZeroDivisionError, ValueError):
        gain_quad = 0.0
    # levier max : h_i = 1/n + (x_i − x̄)²/Sxx
    mx = _moyenne(xs); Sxx = sum((x - mx) ** 2 for x in xs)
    levier_max = max(1 / n + (x - mx) ** 2 / Sxx for x in xs) if Sxx > 0 else 1.0
    return {"residu_max": max(abs(e) for e in residus), "gain_quadratique": gain_quad, "levier_max": levier_max}


def analyse(jeux=None):
    """Façade : stats résumées (identiques) vs diagnostics (différents) sur le quartet. (ANALYSE, {...}) ou (ABSTENTION)."""
    jeux = jeux or QUARTET
    if any(len(xs) < 4 for xs, _ in jeux.values()):
        return (ABSTENTION, "jeux trop petits")
    stats = {k: stats_resumees(xs, ys) for k, (xs, ys) in jeux.items()}
    diags = {k: diagnostics(xs, ys) for k, (xs, ys) in jeux.items()}
    identiques = len({s for s in stats.values()}) == 1
    return (ANALYSE, {"stats": stats, "diagnostics": diags, "stats_identiques": identiques})


def formule(res) -> str:
    if res[0] == ABSTENTION:
        return f"Pas d'analyse : {res[1]}."
    i = res[1]
    d = i["diagnostics"]
    return (f"Les 4 jeux ont {'des stats résumées IDENTIQUES' if i['stats_identiques'] else 'des stats proches'} "
            f"(corr 0.816, y=3+0.5x). Mais : II gain quadratique {d['II']['gain_quadratique']:.2f} (courbe), III résidu "
            f"max {d['III']['residu_max']:.1f} (aberrant), IV levier max {d['IV']['levier_max']:.2f} (point influent). "
            f"Conclure « même relation » des seules stats résumées est sur-confiant — il faut regarder les résidus.")


if __name__ == "__main__":
    print("=== QUARTET D'ANSCOMBE ===\n")
    st, info = analyse()
    for k in ("I", "II", "III", "IV"):
        d = info["diagnostics"][k]
        print(f"  {k:3s}: stats={info['stats'][k]}  | résidu_max={d['residu_max']:.2f} "
              f"gain_quad={d['gain_quadratique']:.2f} levier_max={d['levier_max']:.2f}")
    print("\n ", formule((st, info)))
