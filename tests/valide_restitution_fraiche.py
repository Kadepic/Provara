#!/usr/bin/env python3
"""
VALIDATION de restitution_fraiche.py — gate de fraîcheur. FAUX=0 : fait périmé -> HORS (jamais servi comme courant) ;
atemporel -> toujours servi ; le plus frais choisi ; maintenant explicite (déterministe). Léger (stdlib pur).
"""
from __future__ import annotations

import sys

import restitution_fraiche as R
from fraicheur import FaitDate


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

    # as_of/ttl en années ; maintenant = 2026
    frais = FaitDate("population_paris", "2 100 000", as_of=2025, ttl=2)   # valide jusqu'en 2027
    perime = FaitDate("population_lyon", "500 000", as_of=2010, ttl=2)     # périmé depuis 2012
    inconnu = FaitDate("prix_x", "10", as_of=None, ttl=None)               # daté-inconnu
    atemporel = FaitDate("numero_atomique_fer", "26", atemporel=True)

    # ── Fait FRAIS -> servi ───────────────────────────────────────────────────────────────────
    r = R.sert_ou_hors(frais, 2026)
    check("FRAIS : population récente servie (VERIFIE)", r["statut"] == R.VERIFIE and r["valeur"] == "2 100 000")

    # ── FAUX=0 : fait PÉRIMÉ -> HORS (jamais servi comme courant) ──────────────────────────────
    r2 = R.sert_ou_hors(perime, 2026)
    check("FAUX=0 : population périmée -> HORS (pas servie comme courante)",
          r2["statut"] == R.HORS and r2["valeur"] is None)

    # ── FAUX=0 : daté-inconnu -> HORS (jamais réputé frais) ────────────────────────────────────
    r3 = R.sert_ou_hors(inconnu, 2026)
    check("FAUX=0 : daté-inconnu (as_of/ttl manquant) -> HORS", r3["statut"] == R.HORS)

    # ── Atemporel -> toujours servi ───────────────────────────────────────────────────────────
    r4 = R.sert_ou_hors(atemporel, 2026)
    check("ATEMPOREL : constante (numéro atomique) toujours servie", r4["statut"] == R.VERIFIE and r4["valeur"] == "26")
    # même très loin dans le futur, l'atemporel reste servi
    check("ATEMPOREL : servie même en 3000", R.sert_ou_hors(atemporel, 3000)["statut"] == R.VERIFIE)

    # ── Plusieurs versions : sert la plus récente NON périmée ─────────────────────────────────
    versions = [
        FaitDate("pop", "1M", as_of=2010, ttl=2),     # périmé
        FaitDate("pop", "2M", as_of=2024, ttl=5),     # frais (récent)
        FaitDate("pop", "1.5M", as_of=2018, ttl=3),   # périmé
    ]
    rv = R.sert_le_plus_frais(versions, 2026)
    check("VERSIONS : sert la plus récente non périmée (2M, as_of=2024)",
          rv["statut"] == R.VERIFIE and rv["valeur"] == "2M")
    # toutes périmées -> HORS
    toutes_perimees = [FaitDate("pop", "1M", as_of=2000, ttl=2), FaitDate("pop", "1.2M", as_of=2005, ttl=2)]
    check("VERSIONS FAUX=0 : toutes périmées -> HORS", R.sert_le_plus_frais(toutes_perimees, 2026)["statut"] == R.HORS)

    # ── a_rafraichir : liste les clés à re-fetcher ────────────────────────────────────────────
    cles = R.a_rafraichir([frais, perime, inconnu, atemporel], 2026)
    check("A_RAFRAICHIR : liste les périmés (lyon, prix_x) mais pas les frais/atemporels",
          "population_lyon" in cles and "prix_x" in cles and "population_paris" not in cles
          and "numero_atomique_fer" not in cles)

    # ── Déterminisme : maintenant explicite ───────────────────────────────────────────────────
    check("DÉTERMINISTE : même (fait, maintenant) -> même verdict", R.sert_ou_hors(perime, 2026) == r2)

    # ── CÂBLAGE ia.py ─────────────────────────────────────────────────────────────────────────
    import ia
    check("CÂBLAGE ia.sert_frais : fait frais servi, périmé -> HORS",
          ia.sert_frais(frais, 2026)["statut"] == R.VERIFIE and ia.sert_frais(perime, 2026)["statut"] == R.HORS)

    print(f"\n=== valide_restitution_fraiche : {ok}/{ok + len(fails)} ===")
    if fails:
        print("ÉCHECS :", ", ".join(fails))
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main())
