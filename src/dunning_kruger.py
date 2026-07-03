"""
PALIER 2 — EFFET DUNNING-KRUGER COMME ARTEFACT STATISTIQUE : attribuer le graphe DK à « l'incompétence rend confiant »
est sur-confiant (brique 130, 2026-06-28).

Le graphe canonique de Dunning-Kruger — les MOINS compétents SUR-estiment leur rang, les PLUS compétents le SOUS-estiment —
est en grande partie un ARTEFACT statistique. Il émerge AUTOMATIQUEMENT dès qu'on trace (auto-évaluation − compétence
réelle) en fonction de la compétence, même si l'auto-évaluation est du PUR BRUIT sans aucune information : par régression
vers la moyenne, l'auto-évaluation moyenne par quartile reste vers le centre (~50), si bien que le quartile du BAS paraît
se surestimer et celui du HAUT se sous-estimer. La compétence apparaît des DEUX côtés de l'axe (une fois comme abscisse,
une fois soustraite), ce qui force une pente négative.

Conclure « les incompétents ne savent pas qu'ils le sont » à partir de ce graphe est donc SUR-CONFIANT : on ne peut pas
distinguer un vrai effet psychologique d'un simple bruit d'auto-évaluation + régression. Avec une connaissance de soi
PARFAITE, le motif DISPARAÎT ; un vrai effet s'ajouterait par-dessus l'artefact, mais le graphe naïf attribue TOUT à
l'incompétence.

LE MODE D'ÉCHEC DÉMASQUÉ : lire le graphe DK comme une preuve d'« incompétence sur-confiante » est sur-confiant — c'est
en grande partie une régression vers la moyenne. Distinct de regression_moyenne (86, générique) : ici la structure
spécifique self − réel et l'émergence à information NULLE. ABSTENTION si données insuffisantes. rng seedé.
"""
from __future__ import annotations

ABSTENTION = "abstention"
ANALYSE = "analyse"


def _moyenne(xs):
    return sum(xs) / len(xs)


def simule(n, info, rng):
    """n personnes. compétence réelle = percentile uniforme. auto-évaluation = info·réel + (1−info)·bruit_uniforme
    (info=0 ⇒ pur bruit indépendant ; info=1 ⇒ parfaite). Renvoie (réels, autos)."""
    reels = [rng.uniform(0, 100) for _ in range(n)]
    autos = [info * r + (1 - info) * rng.uniform(0, 100) for r in reels]
    return reels, autos


def moyennes_par_quartile(reels, autos):
    """Pour chaque quartile de compétence RÉELLE : (réel moyen, auto-éval moyenne, sur/sous-estimation)."""
    pairs = sorted(zip(reels, autos))
    q = len(pairs) // 4
    out = []
    for i in range(4):
        seg = pairs[i * q:(i + 1) * q] if i < 3 else pairs[i * q:]
        mr = _moyenne([r for r, a in seg])
        ma = _moyenne([a for r, a in seg])
        out.append((mr, ma, ma - mr))
    return out


def pente_ecart_competence(reels, autos):
    """Pente de la régression (auto − réel) sur réel. Fortement négative = motif DK (même à info=0)."""
    ecarts = [a - r for r, a in zip(reels, autos)]
    mr = _moyenne(reels)
    me = _moyenne(ecarts)
    sxx = sum((r - mr) ** 2 for r in reels)
    sxy = sum((r - mr) * (e - me) for r, e in zip(reels, ecarts))
    return sxy / sxx if sxx else 0.0


def analyse(info=0.0, n=20000, rng=None):
    """Façade : motif DK pour un niveau d'information donné. (ANALYSE, {quartiles, pente, ...}) ou (ABSTENTION)."""
    if rng is None or n < 400:
        return (ABSTENTION, "rng requis / n trop petit")
    reels, autos = simule(n, info, rng)
    quart = moyennes_par_quartile(reels, autos)
    return (ANALYSE, {"info": info, "quartiles": quart, "surestim_bas": quart[0][2], "surestim_haut": quart[-1][2],
                      "pente": pente_ecart_competence(reels, autos)})


def formule(res) -> str:
    if res[0] == ABSTENTION:
        return f"Pas d'analyse : {res[1]}."
    i = res[1]
    src = "PUR BRUIT (aucune information)" if i["info"] == 0 else f"information={i['info']}"
    return (f"Auto-évaluation = {src}. Quartile du BAS : surestimation {i['surestim_bas']:+.0f} ; quartile du HAUT : "
            f"{i['surestim_haut']:+.0f} (pente écart/compétence {i['pente']:+.2f}). Le motif Dunning-Kruger émerge même "
            f"sans aucune information — l'attribuer à « l'incompétence rend confiant » est sur-confiant (artefact de "
            f"régression).")


if __name__ == "__main__":
    import random
    print("=== EFFET DUNNING-KRUGER (artefact statistique) ===\n")
    for info in (0.0, 0.5, 1.0):
        st, inf = analyse(info, rng=random.Random(0))
        qs = " ".join(f"Q{k+1}:{d:+.0f}" for k, (_, _, d) in enumerate(inf["quartiles"]))
        print(f"  info={info}: {qs}  (pente {inf['pente']:+.2f})")
    print("\n ", formule(analyse(0.0, rng=random.Random(0))))
