"""
PALIER 2 — PHÉNOMÈNE DE WILL ROGERS / MIGRATION DE STADE : conclure « les deux groupes se sont améliorés » est
sur-confiant après reclassification (brique 101, 2026-06-27).

« Quand les Okies ont quitté l'Oklahoma pour la Californie, ils ont élevé le QI moyen des DEUX États. » Si on déplace
d'un groupe A (valeurs hautes) vers un groupe B (valeurs basses) des éléments qui sont SOUS la moyenne de A mais
AU-DESSUS de la moyenne de B, alors :
  • la moyenne de A MONTE (on lui a retiré des éléments sous sa moyenne),
  • la moyenne de B MONTE (on lui a ajouté des éléments au-dessus de sa moyenne).
Les DEUX moyennes augmentent — sans qu'AUCUNE valeur individuelle n'ait changé et sans qu'aucun élément ne soit créé ou
détruit. La moyenne de la POPULATION TOTALE (groupée) est, elle, strictement INVARIANTE.

En médecine c'est la MIGRATION DE STADE : un meilleur diagnostic reclasse des patients « limites » d'un stade précoce
vers un stade avancé ; la survie par stade s'améliore dans CHAQUE stade, sans aucun progrès thérapeutique réel.

LE MODE D'ÉCHEC DÉMASQUÉ : lire une amélioration des moyennes par groupe après reclassification est SUR-CONFIANT — c'est
un artefact ; seule la statistique GROUPÉE (invariante à la reclassification) dit la vérité. Distinct de Simpson (87 :
renversement d'association par un confondeur). ABSTENTION si données insuffisantes. Pur Python.
"""
from __future__ import annotations

ABSTENTION = "abstention"
ANALYSE = "analyse"


def moyenne(xs):
    return sum(xs) / len(xs) if xs else 0.0


def migrants_will_rogers(A, B):
    """Éléments de A strictement entre moyenne(B) et moyenne(A) : leur migration vers B fait monter les DEUX moyennes."""
    mA, mB = moyenne(A), moyenne(B)
    return [x for x in A if mB < x < mA]


def migration(A, B, migrants=None):
    """Déplace `migrants` (par défaut ceux de Will Rogers) de A vers B. Renvoie (A', B', migrants)."""
    if migrants is None:
        migrants = migrants_will_rogers(A, B)
    reste = list(A)
    for x in migrants:
        reste.remove(x)
    return reste, list(B) + list(migrants), migrants


def analyse(A, B):
    """Façade : moyennes par groupe et groupée, avant/après migration de stade.
    (ANALYSE, {avant, apres, migrants, ...}) ou (ABSTENTION, raison)."""
    if len(A) < 2 or len(B) < 2:
        return (ABSTENTION, "groupes trop petits")
    if moyenne(A) <= moyenne(B):
        return (ABSTENTION, "A doit être le groupe de moyenne supérieure")
    migrants = migrants_will_rogers(A, B)
    if not migrants or len(migrants) >= len(A):
        return (ABSTENTION, "aucune migration de Will Rogers possible (ou viderait A)")
    A2, B2, _ = migration(A, B, migrants)
    pool = A + B
    avant = {"mA": moyenne(A), "mB": moyenne(B), "groupe": moyenne(pool)}
    apres = {"mA": moyenne(A2), "mB": moyenne(B2), "groupe": moyenne(A2 + B2)}
    return (ANALYSE, {"avant": avant, "apres": apres, "migrants": migrants,
                      "nA": len(A), "nB": len(B), "n_migrants": len(migrants)})


def formule(res) -> str:
    if res[0] == ABSTENTION:
        return f"Pas d'analyse : {res[1]}."
    i = res[1]
    av, ap = i["avant"], i["apres"]
    return (f"Migration de {i['n_migrants']} éléments : moyenne A {av['mA']:.2f}→{ap['mA']:.2f} (↑) ET moyenne B "
            f"{av['mB']:.2f}→{ap['mB']:.2f} (↑) — les DEUX montent. Mais la moyenne GROUPÉE reste {av['groupe']:.2f}="
            f"{ap['groupe']:.2f}. Conclure à une amélioration serait sur-confiant : artefact de reclassification, rien "
            f"n'a changé dans la population.")


if __name__ == "__main__":
    A = [50, 60, 70, 80, 90]          # groupe « haut »
    B = [10, 20, 30, 40]              # groupe « bas »
    print("=== PHÉNOMÈNE DE WILL ROGERS (migration de stade) ===\n")
    st, info = analyse(A, B)
    print(f"  migrants (sous moy(A)={moyenne(A):.1f}, au-dessus moy(B)={moyenne(B):.1f}) : {info['migrants']}")
    print(" ", formule((st, info)))
