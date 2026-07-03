"""
PALIER 2 — THÉORÈME NO FREE LUNCH (Wolpert-Macready) : prétendre qu'un apprenant/optimiseur est universellement meilleur
est sur-confiant (brique 127, 2026-06-28).

Un algorithme d'apprentissage (ou d'optimisation) ne peut pas être le meilleur sur TOUS les problèmes. MOYENNÉ sur TOUTES
les fonctions cibles possibles, TOUS les apprenants ont EXACTEMENT la même erreur hors-échantillon (50 % en binaire) : ce
qu'un biais inductif gagne sur une classe de problèmes, il le perd EXACTEMENT sur la classe complémentaire. Aucun
apprentissage n'est possible SANS biais inductif, et aucun biais n'est universellement bon.

Démonstration exacte (domaine fini) : on énumère les 2^N fonctions cibles binaires, on apprend sur un sous-ensemble et on
mesure l'erreur sur les points HORS apprentissage. Tout apprenant — « prédire la majorité du train », « prédire 0 »,
« prédire l'opposé » — a la MÊME erreur moyenne 0.5. Sur une classe STRUCTURÉE (fonctions constantes), un apprenant au
biais ADAPTÉ (majorité) est parfait ; mais cet avantage est compensé exactement ailleurs.

LE MODE D'ÉCHEC DÉMASQUÉ : affirmer « mon modèle est le meilleur » sans spécifier la CLASSE de problèmes est SUR-CONFIANT.
Le monde réel a une structure ⇒ un biais adapté aide vraiment (honnêteté) — mais c'est une hypothèse, pas une garantie
universelle. Distinct des bornes de généralisation (PAC 63, Rademacher 66, stabilité 74). Pur Python (énumération exacte).
"""
from __future__ import annotations

import itertools

ABSTENTION = "abstention"
ANALYSE = "analyse"


def majorite_train(f, train):
    s = sum(f[i] for i in train)
    return 1 if s * 2 >= len(train) else 0      # égalité → 1


APPRENANTS = {
    "majorité": lambda f, x, train: majorite_train(f, train),
    "constant0": lambda f, x, train: 0,
    "opposé_majorité": lambda f, x, train: 1 - majorite_train(f, train),
    "parité": lambda f, x, train: sum(f[i] for i in train) % 2,
}


def erreur_hors_echantillon(apprenant, f, train, test):
    """Fraction d'erreurs de l'apprenant sur les points HORS apprentissage."""
    return sum(apprenant(f, x, train) != f[x] for x in test) / len(test)


def erreur_moyenne(apprenant, N, train, test):
    """Erreur hors-échantillon moyennée sur TOUTES les 2^N fonctions cibles binaires."""
    tot = 0.0
    nb = 0
    for f in itertools.product([0, 1], repeat=N):
        tot += erreur_hors_echantillon(apprenant, f, train, test)
        nb += 1
    return tot / nb


def erreur_sur_classe(apprenant, fonctions, train, test):
    """Erreur moyenne sur une CLASSE donnée de fonctions."""
    return sum(erreur_hors_echantillon(apprenant, f, train, test) for f in fonctions) / len(fonctions)


def analyse(N=5, train=(0, 1), test=(2, 3, 4)):
    """Façade : erreur moyenne de chaque apprenant sur TOUTES les fonctions, et sur la classe constante.
    (ANALYSE, {moyennes, sur_constantes}) ou (ABSTENTION)."""
    if N < 3 or not train or not test or any(i >= N for i in list(train) + list(test)):
        return (ABSTENTION, "domaine/partition invalide")
    moyennes = {nom: erreur_moyenne(app, N, list(train), list(test)) for nom, app in APPRENANTS.items()}
    constantes = [tuple([v] * N) for v in (0, 1)]
    sur_const = {nom: erreur_sur_classe(app, constantes, list(train), list(test)) for nom, app in APPRENANTS.items()}
    return (ANALYSE, {"moyennes": moyennes, "sur_constantes": sur_const})


def formule(res) -> str:
    if res[0] == ABSTENTION:
        return f"Pas d'analyse : {res[1]}."
    i = res[1]
    vals = list(i["moyennes"].values())
    return (f"Moyennés sur TOUTES les fonctions cibles, les apprenants ont la MÊME erreur hors-échantillon "
            f"({min(vals):.3f}=...={max(vals):.3f}). Sur les fonctions CONSTANTES, « majorité » est parfait "
            f"({i['sur_constantes']['majorité']:.3f}) mais « constant0 » non ({i['sur_constantes']['constant0']:.3f}). "
            f"Prétendre qu'un apprenant est universellement meilleur est sur-confiant — le biais inductif est nécessaire "
            f"et propre à la classe de problèmes.")


if __name__ == "__main__":
    print("=== THÉORÈME NO FREE LUNCH ===\n")
    st, info = analyse()
    for nom, e in info["moyennes"].items():
        print(f"  {nom:18s}: erreur moyenne (toutes fonctions)={e:.3f}  | sur constantes={info['sur_constantes'][nom]:.3f}")
    print("\n ", formule((st, info)))
