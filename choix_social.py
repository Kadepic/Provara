"""
PALIER 2 — CHOIX SOCIAL (paradoxe de Condorcet, théorème d'Arrow) : il n'existe pas toujours de « meilleur » choix
collectif (brique 83, 2026-06-27).

Agréger des préférences individuelles en UN classement collectif « rationnel » semble anodin. Mais :
  • PARADOXE DE CONDORCET : la règle de majorité par PAIRES peut CYCLER (A bat B, B bat C, C bat A) — il n'y a alors
    AUCUN gagnant de Condorcet. Déclarer un vainqueur définitif est SUR-CONFIANT.
  • Les méthodes (pluralité, Borda, Condorcet) donnent des vainqueurs DIFFÉRENTS sur le MÊME profil → « le » gagnant
    dépend de la règle (arbitraire). La pluralité peut élire un candidat battu par TOUS en face-à-face.
  • EFFET SPOILER (violation de l'indépendance aux options non pertinentes) : retirer un perdant peut CHANGER le
    vainqueur.
  • Théorème d'ARROW : pour ≥3 options, AUCUNE règle ne satisfait simultanément unanimité + IIA + non-dictature.

LE MODE D'ÉCHEC DÉMASQUÉ : prétendre qu'un agrégat fournit « le » choix collectif objectif est sur-confiant quand il y
a un cycle ou que les méthodes divergent. L'attitude honnête : DÉTECTER l'ambiguïté (cycle / désaccord) et la
SIGNALER plutôt que sur-affirmer. ABSTENTION si profil/candidats vides. Pur Python.
"""
from __future__ import annotations

import itertools

ABSTENTION = "abstention"
CLAIR = "clair"
AMBIGU = "ambigu"


def matrice_majorite(profil, candidats):
    """M[a][b] = nombre d'électeurs préférant a à b."""
    M = {a: {b: 0 for b in candidats} for a in candidats}
    for rang in profil:
        pos = {c: i for i, c in enumerate(rang)}
        for a in candidats:
            for b in candidats:
                if a != b and pos[a] < pos[b]:
                    M[a][b] += 1
    return M


def bat(M, a, b):
    return M[a][b] > M[b][a]


def gagnant_condorcet(profil, candidats):
    """Candidat qui bat TOUS les autres en face-à-face, ou None (cycle / pas de gagnant)."""
    M = matrice_majorite(profil, candidats)
    for a in candidats:
        if all(bat(M, a, b) for b in candidats if b != a):
            return a
    return None


def cycle_condorcet(profil, candidats):
    """Y a-t-il un cycle de majorité (a bat b, b bat c, c bat a) ?"""
    M = matrice_majorite(profil, candidats)
    for a, b, c in itertools.permutations(candidats, 3):
        if bat(M, a, b) and bat(M, b, c) and bat(M, c, a):
            return True
    return False


def gagnant_pluralite(profil, candidats):
    """Plus de premières places (départage : ordre des candidats)."""
    cnt = {c: 0 for c in candidats}
    for rang in profil:
        cnt[rang[0]] += 1
    return max(candidats, key=lambda c: (cnt[c], -list(candidats).index(c)))


def gagnant_borda(profil, candidats):
    """Score de Borda (rang i sur K → K−1−i points)."""
    K = len(candidats)
    sc = {c: 0 for c in candidats}
    for rang in profil:
        for i, c in enumerate(rang):
            sc[c] += K - 1 - i
    return max(candidats, key=lambda c: (sc[c], -list(candidats).index(c)))


def analyse(profil, candidats):
    """Façade : (CLAIR/AMBIGU, {condorcet, pluralite, borda, cycle, accord}) ou (ABSTENTION, raison).
    CLAIR = gagnant de Condorcet existe ET les 3 méthodes s'accordent ; AMBIGU sinon."""
    if not profil or len(candidats) < 2:
        return (ABSTENTION, "profil ou candidats insuffisants")
    cond = gagnant_condorcet(profil, candidats)
    plur = gagnant_pluralite(profil, candidats)
    bord = gagnant_borda(profil, candidats)
    cyc = cycle_condorcet(profil, candidats)
    accord = (cond is not None and cond == plur == bord)
    info = {"condorcet": cond, "pluralite": plur, "borda": bord, "cycle": cyc, "accord": accord}
    return (CLAIR if accord else AMBIGU, info)


def formule(res) -> str:
    if res[0] == ABSTENTION:
        return f"Pas d'agrégation : {res[1]}."
    i = res[1]
    if res[0] == CLAIR:
        return f"Gagnant collectif NET : {i['condorcet']} (Condorcet = pluralité = Borda)."
    if i["cycle"]:
        return "AMBIGU : cycle de Condorcet (A>B>C>A) — AUCUN gagnant objectif. Affirmer un vainqueur serait sur-confiant."
    return (f"AMBIGU : les méthodes DIVERGENT (Condorcet={i['condorcet']}, pluralité={i['pluralite']}, Borda={i['borda']}) "
            f"— « le » gagnant dépend de la règle. Sur-affirmer serait sur-confiant.")


if __name__ == "__main__":
    print("=== CHOIX SOCIAL (Condorcet / Arrow) ===\n")
    # Pluralité élit A, mais A est battu par B ET C en face-à-face
    profil = [("A", "B", "C")] * 5 + [("B", "C", "A")] * 4 + [("C", "B", "A")] * 2
    print("  Profil 5×(A>B>C), 4×(B>C>A), 2×(C>B>A) :")
    print("  ", formule(analyse(profil, ["A", "B", "C"])))
    # Paradoxe de Condorcet (cycle)
    cyc = [("A", "B", "C"), ("B", "C", "A"), ("C", "A", "B")]
    print("\n  Profil cyclique (A>B>C, B>C>A, C>A>B) :")
    print("  ", formule(analyse(cyc, ["A", "B", "C"])))
