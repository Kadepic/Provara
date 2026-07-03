"""
PALIER 2 — TRANSFERABLE BELIEF MODEL (TBM, Smets) : croyances à MONDE OUVERT + niveau de décision pignistique
(brique 59, 2026-06-26).

Raffinement de Dempster-Shafer [[croyance_dempster_shafer]] qui sépare DEUX niveaux :
  • niveau CRÉDAL (raisonnement) : des masses, mais à MONDE OUVERT — m(∅) > 0 est AUTORISÉ et signifie « la vérité
    est peut-être HORS du cadre Θ » (aucune hypothèse listée n'est correcte). C'est la différence clé avec le monde
    fermé de Shafer (qui force m(∅)=0 par normalisation).
  • niveau PIGNISTIQUE (décision) : pour parier/décider, on transforme la masse en probabilité BetP en répartissant
    chaque masse m(A) ÉQUITABLEMENT sur les éléments de A : BetP(ω) = Σ_{A∋ω} m(A)/(|A|·(1−m(∅))).

RÈGLE CONJONCTIVE (⊕, NON normalisée) : m₁₂(A) = Σ_{B∩C=A} m₁(B)m₂(C). Le conflit s'ACCUMULE sur ∅ au lieu d'être
redistribué. Fermer le monde (renormaliser par 1−m(∅)) redonne EXACTEMENT la règle de Dempster.

LE MODE D'ÉCHEC DÉMASQUÉ : la masse de conflit m(∅) est un AVERTISSEMENT honnête (« mes évidences se contredisent
tant que mon cadre est peut-être faux »). Le monde fermé (Dempster) la JETTE par normalisation → sur-confiance : sur
le paradoxe de Zadeh, le TBM met m(∅)≈0.9999 (alarme) là où Dempster affirme une certitude absurde. Et BetP, point de
décision, vit DANS le crédal [Bel, Pl] : l'annoncer comme la vraie probabilité écrase l'imprécision (sur-confiant).
ABSTENTION si m(∅)=1 (conflit total : impossible de parier). Pur Python.
"""
from __future__ import annotations

import croyance_dempster_shafer as _DS

ABSTENTION = "abstention"
PIGNISTIQUE = "pignistique"
_TOL = 1e-12


def _masse(m):
    """Normalise les clés en frozenset, AUTORISE ∅ (monde ouvert), vérifie masses ≥ 0 et somme ≈ 1."""
    out = {}
    for k, v in m.items():
        fk = frozenset(k)
        if v < -1e-9:
            raise ValueError(f"masse négative sur {set(fk)}")
        out[fk] = out.get(fk, 0.0) + float(v)
    s = sum(out.values())
    if abs(s - 1.0) > 1e-6:
        raise ValueError(f"masses ne somment pas à 1 (somme={s:.6f})")
    return out


def masse_vide(m):
    """m(∅) : degré de conflit / « hors cadre » (monde ouvert)."""
    return _masse(m).get(frozenset(), 0.0)


def belief(m, A):
    """Bel(A) = Σ_{∅≠B⊆A} m(B) (monde ouvert : ∅ exclu)."""
    m = _masse(m); A = frozenset(A)
    return sum(v for B, v in m.items() if B and B <= A)


def plausibilite(m, A):
    """Pl(A) = Σ_{B∩A≠∅} m(B)."""
    m = _masse(m); A = frozenset(A)
    return sum(v for B, v in m.items() if B & A)


def conjonctive(m1, m2):
    """Règle conjonctive ⊕ (NON normalisée) : le conflit s'accumule sur ∅. Renvoie une masse à monde ouvert."""
    m1, m2 = _masse(m1), _masse(m2)
    out = {}
    for B, v1 in m1.items():
        for C, v2 in m2.items():
            inter = B & C
            out[inter] = out.get(inter, 0.0) + v1 * v2
    return out


def ferme_le_monde(m):
    """Ferme le monde : renormalise par 1−m(∅) et jette ∅ → masse de Shafer. Sur ⊕, redonne la règle de Dempster."""
    m = _masse(m)
    vide = m.get(frozenset(), 0.0)
    if vide >= 1.0 - _TOL:
        return None
    return {A: v / (1.0 - vide) for A, v in m.items() if A}


def pignistique(m, omega):
    """Transformation pignistique BetP(ω) = Σ_{A∋ω} m(A)/(|A|·(1−m(∅))) : probabilité de DÉCISION (équirépartition)."""
    m = _masse(m)
    vide = m.get(frozenset(), 0.0)
    if vide >= 1.0 - _TOL:
        return None
    denom = 1.0 - vide
    return {w: sum(v / len(A) for A, v in m.items() if A and w in A) / denom for w in omega}


def betp_evenement(betp, A):
    return sum(betp[w] for w in A)


def decide(m, omega, utilites):
    """Décision d'utilité espérée maximale au niveau pignistique. `utilites` = dict action→(dict état→utilité).
    Renvoie (PIGNISTIQUE, action*, BetP) ou (ABSTENTION, None, raison)."""
    betp = pignistique(m, omega)
    if betp is None:
        return (ABSTENTION, None, "m(∅)=1 : conflit total, impossible de parier")
    eu = {a: sum(betp[w] * u[w] for w in omega) for a, u in utilites.items()}
    best = max(eu, key=eu.get)
    return (PIGNISTIQUE, best, betp)


def formule(m, omega) -> str:
    vide = masse_vide(m)
    betp = pignistique(m, omega)
    if betp is None:
        return "Conflit total (m(∅)=1) : aucune décision possible, le cadre est probablement faux."
    alerte = f" ⚠ conflit/hors-cadre m(∅)={vide:.3f}" if vide > 0.05 else ""
    pari = ", ".join(f"{w}:{betp[w]:.2f}" for w in omega)
    return f"Probabilité pignistique (pour décider) : {pari}.{alerte} (au niveau crédal, garder [Bel,Pl] ; BetP n'est qu'un point de pari)."


if __name__ == "__main__":
    print("=== TRANSFERABLE BELIEF MODEL (Smets) — monde ouvert & pignistique ===\n")
    m1 = {("M",): 0.99, ("T",): 0.01}
    m2 = {("C",): 0.99, ("T",): 0.01}
    comb = conjonctive(m1, m2)
    print(f"  Zadeh (2 médecins) — conjonctive ⊕ :")
    print(f"   m(∅) = {comb.get(frozenset(),0):.4f}  (ALARME : conflit énorme, cadre suspect)")
    print(f"   vs Dempster (monde fermé) Bel(T) = {_DS.belief(_DS.combine_dempster(m1,m2),('T',)):.3f}  (certitude absurde, alarme JETÉE)\n")
    m = {("a",): 0.5, ("a", "b", "c"): 0.3, (): 0.2}   # monde ouvert
    print(f"  masse monde ouvert m = {{a:0.5, abc:0.3, ∅:0.2}}")
    print("  BetP =", {k: round(v, 3) for k, v in pignistique(m, ["a", "b", "c"]).items()})
    print(" ", formule(m, ["a", "b", "c"]))
