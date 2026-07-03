"""
PALIER 2 — CRITÈRE DE KELLY (pari proportionnel, croissance logarithmique) : miser plus que Kelly par sur-confiance
mène à la RUINE malgré une espérance positive (brique 79, 2026-06-27).

Pari favorable répété : probabilité p de gagner b fois la mise (sinon on perd la mise). Combien miser, fraction f de la
fortune, à chaque coup ? L'espérance de fortune (1+f·(pb−q), q=1−p) est maximisée en misant TOUT (f=1) — mais c'est
SUR-CONFIANT : une seule défaite ruine. Le critère de KELLY maximise le TAUX DE CROISSANCE LOGARITHMIQUE
    G(f) = p·ln(1+b·f) + q·ln(1−f),   maximisé en   f* = (p·b − q)/b,
qui maximise la fortune TYPIQUE (médiane/géométrique) à long terme.

LE MODE D'ÉCHEC DÉMASQUÉ : sur-miser (f > f*, par sur-confiance dans son avantage) FAIT BAISSER la croissance ; au-delà
de ≈ 2·f* la croissance devient NÉGATIVE (on s'appauvrit en moyenne géométrique malgré chaque pari à espérance
positive), et miser tout (f=1) ruine presque sûrement. Maximiser l'ESPÉRANCE de fortune (au lieu de l'espérance du LOG)
est l'erreur : la moyenne est gonflée par des trajectoires improbables, la trajectoire TYPIQUE va à zéro. Si l'avantage
est négatif (pb ≤ q), f* ≤ 0 : ne pas parier. ABSTENTION si p∉(0,1) ou b≤0. Pur Python.
"""
from __future__ import annotations

import math

ABSTENTION = "abstention"
KELLY = "kelly"


def fraction_kelly(p, b):
    """Fraction optimale de Kelly f* = (p·b − (1−p))/b (≤ 0 si pas d'avantage → ne pas parier)."""
    return (p * b - (1 - p)) / b


def croissance(f, p, b):
    """Taux de croissance log G(f) = p·ln(1+bf) + q·ln(1−f). −∞ si f mène à une fortune nulle possible."""
    if f >= 1 or 1 + b * f <= 0:
        return float("-inf") if (f >= 1 or 1 + b * f <= 0) else 0.0
    q = 1 - p
    t1 = p * math.log(1 + b * f)
    t2 = q * math.log(1 - f) if f < 1 else float("-inf")
    return t1 + t2


def fortune_finale(f, p, b, T, rng, w0=1.0):
    """Simule T paris en misant la fraction f ; renvoie la fortune finale (multiplicative)."""
    w = w0
    for _ in range(T):
        if rng.random() < p:
            w *= (1 + b * f)
        else:
            w *= (1 - f)
        if w <= 0:
            return 0.0
    return w


def conseille(p, b):
    """Façade : (KELLY, {f_kelly, croissance, espere}) ou (ABSTENTION, raison). f_kelly borné à [0,1)."""
    if not (0 < p < 1) or b <= 0:
        return (ABSTENTION, "p∉(0,1) ou b≤0")
    fk = fraction_kelly(p, b)
    fk_borne = max(0.0, min(0.999, fk))
    return (KELLY, {"f_kelly": fk, "f_applique": fk_borne, "croissance": croissance(fk_borne, p, b),
                    "avantage": p * b - (1 - p)})


def formule(res) -> str:
    if res[0] == ABSTENTION:
        return f"Pas de conseil : {res[1]}."
    i = res[1]
    if i["f_kelly"] <= 0:
        return f"Avantage négatif ({i['avantage']:.3f}) : NE PAS parier (Kelly f*={i['f_kelly']:.3f} ≤ 0)."
    return (f"Miser f*={i['f_kelly']:.3f} de la fortune (Kelly) : croissance log {i['croissance']:.4f}/coup. "
            f"Sur-miser par sur-confiance ferait baisser puis ruinerait la fortune typique malgré l'espérance positive.")


if __name__ == "__main__":
    import random, statistics
    rng = random.Random(0)
    p, b = 0.55, 1.0
    fk = fraction_kelly(p, b)
    print("=== CRITÈRE DE KELLY ===\n")
    print(f"  p={p}, b={b} → Kelly f*={fk:.3f} ; avantage={p*b-(1-p):.3f}\n")
    print("  croissance log G(f) :")
    for f in (0.05, fk, 2 * fk, 0.30, 0.5):
        print(f"   f={f:.2f} : G={croissance(f, p, b):+.4f}{'  ← Kelly (max)' if abs(f-fk)<1e-9 else ''}")
    print("\n  Fortune médiane après 200 coups (5000 trajectoires) :")
    for f, lab in [(fk, "Kelly f*"), (2 * fk, "2× Kelly (sur-mise)"), (0.5, "agressif"), (1.0, "tout-in (espérance max)")]:
        ws = sorted(fortune_finale(f, p, b, 200, rng) for _ in range(5000))
        print(f"   {lab:24s} (f={f:.2f}): médiane={ws[len(ws)//2]:.3g}  moyenne={statistics.mean(ws):.3g}")
