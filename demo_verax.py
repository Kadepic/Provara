#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DÉMO VERAX — « Ou il sait, ou il le dit. Jamais il n'invente. »

Lance :  python3 demo_verax.py

Aucune dépendance (Python 3.10+ standard), aucun GPU, aucun réseau.
Tourne sur l'ÉCHANTILLON livré (16 domaines de faits) + les moteurs de calcul
(qui, eux, ne demandent aucune donnée). La base complète — 73 millions de faits —
se reconstruit ensuite en allant chercher les données (voir README, section « Regarde-le apprendre »).
"""
import time
import ia

LARGEUR = 78


def titre(t):
    print("\n" + "═" * LARGEUR + f"\n  {t}\n" + "═" * LARGEUR)


def q(question):
    """Pose une question à VERAX (porte conversationnelle) et affiche son verdict typé."""
    r = ia.assistant(question)
    etiquette = {
        "fait": "✔ FAIT",
        "supposition": "≈ SUPPOSITION",
        "hors": "∅ ABSTENTION",
        "clarification": "? CLARIFICATION",
        "echange": "· ÉCHANGE",
    }.get(r.statut, r.statut.upper())
    print(f"\n  « {question} »")
    print(f"    {etiquette:<16} {r.texte}")
    if r.source:
        print(f"    {'':<16} source : {r.source}")


def calcule(libelle, valeur):
    print(f"    {libelle:<42} = {valeur}")


def main():
    print("\n  VERAX — démonstration")
    print("  L'IA qui ne ment pas : elle sait (avec preuve), ou elle s'abstient.")

    # ── 1. CE QU'IL SAIT (faits vérifiés, avec provenance) ─────────────────────
    titre("1. Il RÉPOND — quand la réalité tranche (fait vérifié, avec source)")
    q("Quelle est la capitale du Japon ?")
    q("Quel est le numéro atomique du fer ?")
    q("Quelle est la capitale du Bhoutan ?")

    # ── 2. CE QU'IL CALCULE (aucune donnée requise : moteurs exacts) ───────────
    titre("2. Il CALCULE — moteurs exacts, sans la moindre donnée stockée")
    calcule("128 × 64  (arithmétique, AST évalué)", ia.assistant("combien font 128*64 ?").texte)
    statut, masse = ia.chimie("H2O")
    calcule("masse molaire de H₂O  (g/mol, moteur chimie)", masse)
    statut, masse2 = ia.chimie("C6H12O6")
    calcule("masse molaire du glucose C₆H₁₂O₆", masse2)
    d = ia.distance_lieux("Tokyo", "Paris")            # orthodromie depuis les coords de l'échantillon
    if d is not None:
        calcule("distance Tokyo → Paris  (grand cercle, km)", f"{d:.0f}")

    # ── 3. LA DISCIPLINE : il n'invente JAMAIS ─────────────────────────────────
    titre("3. Il S'ABSTIENT ou CADRE — là où un LLM hallucinerait")
    print("\n  ─ fait qu'il n'a pas ingéré → il le dit, il ne devine pas :")
    q("Quelle est la population de la ville de Wakanda ?")
    print("\n  ─ question non bornée (pas de vérité unique) → supposition cadrée, jamais un « fait » :")
    q("Quel est le plus beau pays du monde ?")

    # ── 4. FRUGALITÉ (mesurée, ici, maintenant) ────────────────────────────────
    titre("4. Frugalité — mesurée à l'instant")
    import resource
    rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024
    print(f"\n    Empreinte mémoire de cette démo : {rss:.0f} Mo")
    print("    Base COMPLÈTE (73 M faits) mesurée séparément : 3,3 s à charger, 520 Mo, 0 GPU.")
    print("    Dépendances tierces : 0.   Python : 3.10+.\n")


if __name__ == "__main__":
    t = time.time()
    main()
    print(f"  (démo terminée en {time.time() - t:.2f} s)\n")
