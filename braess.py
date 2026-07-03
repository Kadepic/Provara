"""
PALIER 2 — PARADOXE DE BRAESS : « ajouter une route/une option ne peut qu'aider » est sur-confiant (brique 106, 2026-06-27).

Intuition de MONOTONIE : donner plus de capacité, d'options, de connexions à un système ne peut qu'améliorer (ou laisser
inchangé) sa performance. C'est SUR-CONFIANT dès qu'il y a routage ÉGOÏSTE (chaque agent optimise pour lui, équilibre de
Nash) : ajouter une route peut AUGMENTER le temps de trajet de TOUT LE MONDE.

Réseau canonique (N conducteurs de S à T) :
  • Route HAUTE : S→A (latence = x/100, congestionnée) puis A→T (latence = 45, fixe).
  • Route BASSE : S→B (latence = 45, fixe) puis B→T (latence = x/100, congestionnée).
  Sans raccourci, l'équilibre répartit 50/50 → temps = N/200 + 45 (= 65 pour N=4000).
  • On AJOUTE un raccourci gratuit A→B (latence 0). La route en zigzag S→A→B→T devient dominante pour chacun → tout le
    monde la prend → temps = N/100 + N/100 = N/50 (= 80 pour N=4000). PIRE pour tous, alors qu'on a ajouté une option.

L'équilibre égoïste (Nash) est sous-optimal : l'optimum SOCIAL n'utilise pas le raccourci et garde 65. L'écart = « prix
de l'anarchie ».

LE MODE D'ÉCHEC DÉMASQUÉ : conclure qu'élargir l'offre améliore toujours est sur-confiant — en système stratégique il
faut calculer le nouvel ÉQUILIBRE, pas supposer la monotonie. Distinct de jeux_zero_somme (70) et choix_social (83).
ABSTENTION si réseau dégénéré. Pur Python (meilleure réponse asynchrone = Nash pur des jeux de congestion).
"""
from __future__ import annotations

ABSTENTION = "abstention"
ANALYSE = "analyse"

# latences des arêtes : (constante) ou ('flux', coef) pour coef·x
RESEAU = {
    "SA": ("flux", 1 / 100), "BT": ("flux", 1 / 100),
    "AT": ("const", 45.0), "SB": ("const", 45.0), "AB": ("const", 0.0),
}
SANS_PONT = [["SA", "AT"], ["SB", "BT"]]
AVEC_PONT = [["SA", "AT"], ["SB", "BT"], ["SA", "AB", "BT"]]


def _flux_aretes(assign, chemins):
    flux = {}
    for p in assign:
        for e in chemins[p]:
            flux[e] = flux.get(e, 0) + 1
    return flux


def _latence_arete(e, x, reseau):
    typ, c = reseau[e]
    return c if typ == "const" else c * x


def _latence_chemin(chemin, flux, reseau):
    return sum(_latence_arete(e, flux.get(e, 0), reseau) for e in chemin)


def equilibre_nash(n, chemins, reseau=RESEAU, max_sweeps=200):
    """Équilibre de Nash pur par meilleure réponse asynchrone (flux maintenu incrémentalement). Renvoie
    (temps_moyen, assignation)."""
    assign = [i % len(chemins) for i in range(n)]          # répartition initiale équilibrée
    flux = _flux_aretes(assign, chemins)                   # flux courant, mis à jour à chaque changement
    for _ in range(max_sweeps):
        change = False
        for i in range(n):
            cur = assign[i]
            best, best_lat = cur, None
            for p in range(len(chemins)):
                lat = 0.0
                for e in chemins[p]:
                    x = flux.get(e, 0) + (0 if e in chemins[cur] else 1)   # i déjà compté sur son chemin actuel
                    lat += _latence_arete(e, x, reseau)
                if best_lat is None or lat < best_lat - 1e-12:
                    best_lat, best = lat, p
            if best != cur:
                for e in chemins[cur]:
                    flux[e] -= 1
                for e in chemins[best]:
                    flux[e] = flux.get(e, 0) + 1
                assign[i] = best
                change = True
        if not change:
            break
    temps = sum(_latence_chemin(chemins[p], flux, reseau) for p in assign) / n
    return temps, assign


def optimum_social(n, chemins, reseau=RESEAU):
    """Temps moyen à l'optimum social (réparti pour minimiser le temps moyen) — borne le mieux atteignable."""
    # pour le réseau canonique, l'optimum n'utilise pas le pont : on évalue la meilleure répartition 50/50 haut/bas.
    meilleurs = [c for c in chemins if "AB" not in c]
    assign = [i % len(meilleurs) for i in range(n)]
    flux = _flux_aretes(assign, meilleurs)
    return sum(_latence_chemin(meilleurs[p], flux, reseau) for p in assign) / n


def analyse(n=4000):
    """Façade : équilibre sans pont vs avec pont. (ANALYSE, {temps_sans, temps_avec, ...}) ou (ABSTENTION)."""
    if n < 100:
        return (ABSTENTION, "réseau trop petit pour un équilibre de congestion")
    t_sans, _ = equilibre_nash(n, SANS_PONT)
    t_avec, _ = equilibre_nash(n, AVEC_PONT)
    opt = optimum_social(n, AVEC_PONT)
    return (ANALYSE, {"temps_sans_pont": t_sans, "temps_avec_pont": t_avec, "optimum_social": opt,
                      "braess": t_avec > t_sans, "prix_anarchie": t_avec / opt})


def formule(res) -> str:
    if res[0] == ABSTENTION:
        return f"Pas d'analyse : {res[1]}."
    i = res[1]
    return (f"Temps de trajet à l'équilibre : sans raccourci = {i['temps_sans_pont']:.1f} ; AVEC raccourci = "
            f"{i['temps_avec_pont']:.1f} ({'PIRE' if i['braess'] else 'mieux'}). Optimum social = {i['optimum_social']:.1f} "
            f"(prix de l'anarchie {i['prix_anarchie']:.2f}). Croire qu'ajouter une route aide toujours serait "
            f"sur-confiant — l'équilibre égoïste peut empirer pour tous.")


if __name__ == "__main__":
    print("=== PARADOXE DE BRAESS ===\n")
    st, info = analyse(4000)
    print(" ", formule((st, info)))
