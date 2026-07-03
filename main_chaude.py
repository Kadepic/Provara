"""
PALIER 2 — SOPHISME DU JOUEUR & MAIN CHAUDE (biais de Miller-Sanjurjo) : DEUX sur-confiances opposées (brique 107, 2026-06-27).

(a) SOPHISME DU JOUEUR : après une série de Piles, croire que Face « est dû ». SUR-CONFIANT : des tirages INDÉPENDANTS
n'ont pas de mémoire — P(Face | k Piles) = 0.5, point. La « force de rappel vers la moyenne » sur le PROCHAIN tirage
n'existe pas.

(b) DÉBUNKAGE NAÏF DE LA « MAIN CHAUDE » : pour tester si un joueur réussit plus après un succès, on estime
P(succès | succès précédent) en moyennant, sur une séquence FINIE, les tirages suivant un succès. Miller & Sanjurjo (2018)
ont montré que cet estimateur est BIAISÉ SOUS 0.5 même pour une pièce parfaitement équitable : sélectionner les positions
qui suivent un succès sur une séquence finie crée un biais vers le « renversement ». Donc conclure « pas de main chaude »
depuis cet estimateur naïf est AUSSI sur-confiant — le biais doit être corrigé. (Le célèbre « hot hand fallacy » était
lui-même une erreur statistique.)

L'unificateur : une subtilité de CONDITIONNEMENT/SÉLECTION miscalibre dans les DEUX sens. La probabilité conditionnelle
VRAIE est 0.5 (indépendance) ; mais l'estimateur naïf sur séquence finie tend vers < 0.5. Le biais → 0 quand la séquence
s'allonge ; pour DÉTECTER une vraie main chaude il faut comparer à la BASELINE BIAISÉE, pas à 0.5.

LE MODE D'ÉCHEC DÉMASQUÉ : sur-confiance du joueur (renversement attendu) ET sur-confiance du débunkeur (biais ignoré).
Distinct de regression_moyenne (86 : régression d'une mesure extrême vers la moyenne). ABSTENTION si données insuffisantes.
Pur Python, rng seedé.
"""
from __future__ import annotations

ABSTENTION = "abstention"
ANALYSE = "analyse"


def estimateur_naif(sequence):
    """P̂(succès | succès au tirage précédent) sur UNE séquence finie (0/1). None si aucun succès non-terminal."""
    num = den = 0
    for i in range(1, len(sequence)):
        if sequence[i - 1] == 1:
            den += 1
            num += sequence[i]
    return num / den if den else None


def conditionnelle_flux_long(p, n, rng):
    """Estime P(succès | succès précédent) sur UN flux LONG (indépendance ⇒ ≈ p). Réfute le sophisme du joueur."""
    prev = 1 if rng.random() < p else 0
    num = den = 0
    for _ in range(n):
        x = 1 if rng.random() < p else 0
        if prev == 1:
            den += 1
            num += x
        prev = x
    return num / den if den else None


def biais_miller_sanjurjo(p, n, reps, rng):
    """Espérance de l'estimateur naïf sur des séquences de longueur n (E[p̂]). < p pour n fini (biais de sélection)."""
    vals = [estimateur_naif([1 if rng.random() < p else 0 for _ in range(n)]) for _ in range(reps)]
    vals = [v for v in vals if v is not None]
    return sum(vals) / len(vals)


def detecte_main_chaude(p_apres_succes, baseline_biaisee, p_naif_observe):
    """Une vraie main chaude n'est détectée que si p̂ observé dépasse la BASELINE BIAISÉE (pas 0.5)."""
    return p_naif_observe > baseline_biaisee


def analyse(p=0.5, n=4, reps=200000, rng=None):
    """Façade : conditionnelle vraie (flux long) vs estimateur naïf biaisé (séquences finies).
    (ANALYSE, {cond_vraie, biais_naif, n, ...}) ou (ABSTENTION, raison)."""
    if rng is None or n < 3 or not (0 < p < 1):
        return (ABSTENTION, "rng requis / n<3 / p hors ]0,1[")
    cond = conditionnelle_flux_long(p, max(reps, 200000), rng)
    biais = biais_miller_sanjurjo(p, n, reps, rng)
    return (ANALYSE, {"cond_vraie": cond, "biais_naif": biais, "n": n, "p": p, "ampleur_biais": p - biais})


def formule(res) -> str:
    if res[0] == ABSTENTION:
        return f"Pas d'analyse : {res[1]}."
    i = res[1]
    return (f"Indépendance : P(succès|succès précédent) = {i['cond_vraie']:.3f} ≈ {i['p']} (le sophisme du joueur, qui "
            f"attend un renversement, est sur-confiant). MAIS l'estimateur naïf sur séquences de n={i['n']} vaut "
            f"{i['biais_naif']:.3f} < {i['p']} (biais de Miller-Sanjurjo) : conclure « pas de main chaude » depuis ce "
            f"chiffre serait AUSSI sur-confiant — il faut corriger le biais de sélection.")


if __name__ == "__main__":
    import random
    rng = random.Random(0)
    print("=== SOPHISME DU JOUEUR & MAIN CHAUDE (Miller-Sanjurjo) ===\n")
    st, info = analyse(0.5, 4, 200000, rng)
    print(" ", formule((st, info)))
    print("\n  biais selon la longueur de séquence :")
    for n in (4, 10, 50, 200):
        print(f"    n={n:4d} : E[p̂]={biais_miller_sanjurjo(0.5, n, 120000, random.Random(n)):.4f}")
