"""
PALIER 2 — THÉORÈME DE GIBBARD-SATTERTHWAITE (vote stratégique) : croire qu'une règle de vote révèle les VRAIES
préférences est sur-confiant (brique 128, 2026-06-28).

Pour ≥ 3 options, TOUTE règle de vote déterministe, non-dictatoriale et surjective est MANIPULABLE : il existe des
situations où un votant obtient un MEILLEUR résultat (selon ses vraies préférences) en MENTANT sur son classement.
Donc prendre les bulletins pour les préférences sincères est SUR-CONFIANT — le vote stratégique (enterrement d'un rival,
vote utile) est inévitable. C'est le pendant stratégique du théorème d'Arrow.

Exemple (Borda, 4 votants, A/B/C) : sous les vraies préférences, A gagne ; mais un votant qui préfère B≻C≻A peut ENTERRER
A (annoncer C≻B≻A) pour faire gagner C, qu'il préfère à A.

LE MODE D'ÉCHEC DÉMASQUÉ : supposer qu'une règle de vote est « à l'épreuve de la stratégie » (révèle le sincère) est
sur-confiant à ≥3 options. Avec 2 options, la règle de majorité EST non manipulable (l'impossibilité requiert ≥3) —
honnêteté. Distinct de choix_social (83, Condorcet/Arrow = agrégation des préférences). Pur Python (recherche exacte).
"""
from __future__ import annotations

import itertools

ABSTENTION = "abstention"
ANALYSE = "analyse"


def borda(profil, cands):
    score = {c: 0 for c in cands}
    m = len(cands)
    for rang in profil:
        for i, c in enumerate(rang):
            score[c] += (m - 1 - i)
    return max(cands, key=lambda c: (score[c], -ord(c[0])))      # départage : ordre alphabétique


def pluralite(profil, cands):
    score = {c: 0 for c in cands}
    for rang in profil:
        score[rang[0]] += 1
    return max(cands, key=lambda c: (score[c], -ord(c[0])))


def majorite2(profil, cands):
    """Règle de majorité à 2 candidats (le 1ᵉʳ de chaque bulletin)."""
    return pluralite(profil, cands)


def prefere(rang, x, y):
    """x est strictement préféré à y selon le classement sincère rang (meilleur en tête)."""
    return rang.index(x) < rang.index(y)


def trouve_manipulation(regle, vrais, cands):
    """Cherche un votant qui, en mentant, obtient un gagnant qu'il PRÉFÈRE au gagnant sincère.
    Renvoie (votant, faux_classement, gagnant_manip, gagnant_sincere) ou None."""
    sincere = regle(vrais, cands)
    for v in range(len(vrais)):
        for faux in itertools.permutations(cands):
            if list(faux) == list(vrais[v]):
                continue
            p2 = [list(r) for r in vrais]
            p2[v] = list(faux)
            w = regle(p2, cands)
            if prefere(vrais[v], w, sincere):
                return (v, list(faux), w, sincere)
    return None


def taux_manipulables(regle, cands, n_votants, n_profils, rng):
    """Fraction de profils aléatoires manipulables (illustre que la manipulabilité n'est pas un cas isolé)."""
    perms = [list(p) for p in itertools.permutations(cands)]
    manip = 0
    for _ in range(n_profils):
        vrais = [rng.choice(perms) for _ in range(n_votants)]
        if trouve_manipulation(regle, vrais, cands) is not None:
            manip += 1
    return manip / n_profils


def analyse(profil=None, cands=("A", "B", "C")):
    """Façade : sur un profil donné (ou l'exemple par défaut), cherche une manipulation Borda. (ANALYSE, {...}) ou
    (ABSTENTION)."""
    cands = list(cands)
    if profil is None:
        profil = [["B", "C", "A"], ["B", "A", "C"], ["C", "A", "B"], ["A", "C", "B"]]
    if len(cands) < 3:
        return (ABSTENTION, "Gibbard-Satterthwaite requiert ≥ 3 options")
    sincere = borda(profil, cands)
    manip = trouve_manipulation(borda, profil, cands)
    return (ANALYSE, {"gagnant_sincere": sincere, "manipulation": manip, "manipulable": manip is not None,
                      "profil": profil})


def formule(res) -> str:
    if res[0] == ABSTENTION:
        return f"Pas d'analyse : {res[1]}."
    i = res[1]
    if not i["manipulable"]:
        return f"Gagnant sincère {i['gagnant_sincere']} ; aucune manipulation sur ce profil."
    v, faux, w, sinc = i["manipulation"]
    return (f"Gagnant sincère = {sinc}. Le votant {v} (vrai classement {i['profil'][v]}) MENT en annonçant {faux} ⇒ "
            f"gagnant {w}, qu'il PRÉFÈRE à {sinc}. La règle est manipulable : prendre les bulletins pour les vraies "
            f"préférences est sur-confiant (vote stratégique inévitable à ≥3 options).")


if __name__ == "__main__":
    import random
    print("=== GIBBARD-SATTERTHWAITE (vote stratégique) ===\n")
    st, info = analyse()
    print(" ", formule((st, info)))
    rng = random.Random(0)
    print(f"\n  taux de profils manipulables (Borda, 4 votants) = {taux_manipulables(borda, ['A','B','C'], 4, 1000, rng):.2f}")
