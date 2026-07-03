"""
RAPPORT D'INVENTION UNIFIÉ — la surface « produit » de l'objectif de Yohan : par rapport à ce qui
existe, QU'EST-CE QUI MANQUE, et QUELS SONT LES ÉLÉMENTS pour le construire (cf.
[[project-ia-objectif-final-inventions]]).

Synthétise, sur les DEUX substrats, en sections actionnables et SOUND (tout est jugé par la réalité) :
  A. INVENTIONS RÉALISABLES MAINTENANT — recombinaisons vérifiées + LES ÉLÉMENTS à construire.
  B. À PRÉCISER — cibles ambiguës : ce que la réalité doit trancher (sonde discriminante).
  C. FRONTIÈRES — ce qu'aucune recombinaison connue ne réalise = là où un PRINCIPE NEUF est requis,
     classé par LEVIER (combien de capacités il débloquerait) pour le substrat physique.

Ne contient AUCUNE logique de vérité propre : il agrège `moteur_invention`, `chercheur_invention` et
`substrat_physique` (tous validés). Honnêteté maintenue : aucune invention non vérifiée, efficacité
physique non jugée (« concept à évaluer »).
"""
from __future__ import annotations

import chercheur_invention as _CH
import moteur_invention as _MI
import substrat_physique as _PH


def rapport(corpus_code=None, paires_physiques=None, k_lacunes: int = 5) -> dict:
    """Renvoie un dict structuré : {realisables, a_preciser, frontieres, abstractions, principes_manquants}.
    `corpus_code` = [(nom, signature, exemples, held)] ; `paires_physiques` = [(grandeur_in, grandeur_out)]."""
    realisables, a_preciser, frontieres = [], [], []
    abstractions = []

    if corpus_code:
        inv = _CH.inventorie(corpus_code)
        for nom, code in inv.inventions.items():
            realisables.append(("code", nom, code))
        for nom in inv.par_statut.get(_MI.AMBIGU, []):
            a_preciser.append(("code", nom))
        for nom in inv.par_statut.get(_MI.BRIQUE_MANQUANTE, []):
            frontieres.append(("code", nom, "aucune recombinaison connue — primitive de code neuve requise"))
        abstractions = inv.abstractions

    if paires_physiques:
        for e, s in paires_physiques:
            v = _PH.examine(e, s)
            if v.statut == _PH.INVENTION:
                realisables.append(("physique", f"{e}→{s}", " + ".join(v.chaine)))
            elif v.statut == _PH.BRIQUE_MANQUANTE:
                frontieres.append(("physique", f"{e}→{s}", "aucune chaîne de transduction — principe physique neuf requis"))

    principes_manquants = _PH.lacunes_prioritaires(k_lacunes)
    return {"realisables": realisables, "a_preciser": a_preciser, "frontieres": frontieres,
            "abstractions": abstractions, "principes_manquants": principes_manquants}


def texte(rap: dict) -> str:
    L = ["=" * 78, "RAPPORT D'INVENTION — ce qui manque vs ce qui existe (réalité-jugé, sound)", "=" * 78]
    L.append("\nA. INVENTIONS RÉALISABLES MAINTENANT (+ éléments à construire) :")
    if rap["realisables"]:
        for substrat, nom, comment in rap["realisables"]:
            L.append(f"   ✔ [{substrat:8s}] {nom}\n        éléments : {comment}")
    else:
        L.append("   (aucune)")
    if rap["abstractions"]:
        L.append("\n   → abstractions de VALEUR (réutilisées, à construire d'abord) :")
        for t, users in rap["abstractions"]:
            L.append(f"        ★ « {t} » (réutilisée par {len(users)} cibles : {', '.join(users)})")
    L.append("\nB. À PRÉCISER (la réalité doit trancher — fournir plus d'exemples) :")
    L.append("   " + (", ".join(f"[{s}] {n}" for s, n in rap["a_preciser"]) if rap["a_preciser"] else "(aucune)"))
    L.append("\nC. FRONTIÈRES (un principe/atome NEUF est requis) :")
    if rap["frontieres"]:
        for substrat, nom, comment in rap["frontieres"]:
            L.append(f"   ✗ [{substrat:8s}] {nom} — {comment}")
    else:
        L.append("   (aucune)")
    L.append("\n   → principes physiques manquants les plus PRÉCIEUX (levier = capacités débloquées) :")
    for gain, a, b in rap["principes_manquants"]:
        L.append(f"        ☆ {a} → {b}  (+{gain} transductions)")
    return "\n".join(L)


if __name__ == "__main__":
    from garde_ressources import borne
    borne()
    CORPUS = [
        ("somme_totale", "xs", [([1, 2, 3], 6), ([5], 5)], [([0, 4], 4), ([2, 2], 4)]),
        ("somme_carres", "xs", [([1, 2, 3], 14), ([2, 3], 13)], [([5], 25), ([0, 4], 16), ([1, 1], 2)]),
        ("max_carres", "xs", [([-3, 2], 9), ([1, 4], 16), ([-1, -5], 25)], [([0, 3], 9), ([2, -2], 4), ([-6, 1], 36)]),
        ("amp_faible", "x", [([3, 1, 5], 4), ([2, 2], 0)], [([0, 9, 4], 9)]),
        ("produit_cumulatif", "x", [([1, 2, 3], [1, 2, 6]), ([2, 2], [2, 4])], [([3, 1, 4], [3, 3, 12]), ([5], [5])]),
    ]
    PHYS = [("lumiere", "electricite"), ("pression", "lumiere"), ("chaleur", "radio"), ("son", "gravite")]
    print(texte(rapport(CORPUS, PHYS)))
