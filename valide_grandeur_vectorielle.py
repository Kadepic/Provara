#!/usr/bin/env python3
"""
VALIDATION de grandeur_vectorielle.py — grandeurs vectorielles dimensionnées. FAUX=0 : addition/soustraction
de dimensions ou arités différentes REFUSÉE ; produit scalaire porte la dimension produit ; norme conserve la
dimension. Léger (stdlib pur, pas de lecteur).
"""
from __future__ import annotations

import sys

import dimensions as D
from grandeur_vectorielle import GrandeurVectorielle as GV


def main() -> int:
    ok, fails = 0, []

    def check(nom, cond):
        nonlocal ok
        if cond:
            ok += 1
            print(f"  [OK ] {nom}")
        else:
            fails.append(nom)
            print(f"  [XX ] {nom}")

    def leve(fn, exc=Exception):
        try:
            fn(); return False
        except exc:
            return True

    v = GV((3.0, 4.0), D.VITESSE)
    w = GV((1.0, 2.0), D.VITESSE)
    f = GV((10.0, 0.0), D.FORCE)

    check("construction : composantes + dimension", v.composantes == (3.0, 4.0) and v.dimension == D.VITESSE)
    check("immuable", leve(lambda: setattr(v, "composantes", (0,)), AttributeError))
    check("addition même dimension", (v + w).composantes == (4.0, 6.0) and (v + w).dimension == D.VITESSE)
    check("soustraction même dimension", (v - w).composantes == (2.0, 2.0))

    # FAUX=0 : dimensions incompatibles refusées
    check("FAUX=0 : addition vitesse + force -> ValueError (dimensions hétérogènes)",
          leve(lambda: v + f, ValueError))
    check("FAUX=0 : soustraction hétérogène -> ValueError", leve(lambda: v - f, ValueError))
    # FAUX=0 : arités différentes refusées
    check("FAUX=0 : arités différentes -> ValueError",
          leve(lambda: v + GV((1.0, 2.0, 3.0), D.VITESSE), ValueError))

    # multiplication par scalaire (pur et dimensionné)
    check("mul_scalaire pur : dimension inchangée", v.mul_scalaire(2.0).composantes == (6.0, 8.0)
          and v.mul_scalaire(2.0).dimension == D.VITESSE)
    dv = v.mul_scalaire(3.0, D.MASSE)         # masse × vitesse = quantité de mouvement
    check("mul_scalaire dimensionné : dimension = dim · dim_scalaire (masse·vitesse = qté mouvement)",
          dv.dimension == D.MASSE * D.VITESSE == D.QUANTITE_MOUVEMENT)

    # produit scalaire : force · déplacement = travail (énergie)
    depl = GV((2.0, 3.0), D.LONGUEUR)
    val, dim = f.produit_scalaire(depl)
    check("produit scalaire : valeur = Σaᵢbᵢ (10·2 + 0·3 = 20)", val == 20.0)
    check("produit scalaire : dimension = force · longueur = énergie", dim == D.ENERGIE)
    check("FAUX=0 : produit scalaire d'arités différentes -> ValueError",
          leve(lambda: f.produit_scalaire(GV((1.0,), D.LONGUEUR)), ValueError))

    # norme : conserve la dimension, √(3²+4²)=5
    n, nd = v.norme()
    check("norme : √(3²+4²) = 5, dimension conservée (vitesse)", n == 5.0 and nd == D.VITESSE)

    # égalité / hachage
    check("égalité : mêmes composantes + dimension", GV((3.0, 4.0), D.VITESSE) == v)
    check("inégalité : même composantes, dimension ≠", GV((3.0, 4.0), D.FORCE) != v)
    check("hachable", len({v, GV((3.0, 4.0), D.VITESSE), w}) == 2)

    # garde-fous de construction
    check("FAUX=0 : vecteur vide refusé", leve(lambda: GV((), D.VITESSE), ValueError))
    check("FAUX=0 : dimension non-Dimension refusée", leve(lambda: GV((1.0,), "m/s"), TypeError))

    # ── CÂBLAGE ia.py ─────────────────────────────────────────────────────────────────────────
    import ia
    check("CÂBLAGE ia.vecteur : construit une GrandeurVectorielle dimensionnée",
          ia.vecteur((3.0, 4.0), D.VITESSE) == v)
    check("CÂBLAGE ia.vecteur : défaut sans dimension", ia.vecteur((1.0, 2.0)).dimension == D.SANS)

    print(f"\n=== valide_grandeur_vectorielle : {ok}/{ok + len(fails)} ===")
    if fails:
        print("ÉCHECS :", ", ".join(fails))
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main())
