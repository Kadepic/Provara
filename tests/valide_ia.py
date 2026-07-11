"""
VALIDATION du POINT D'ENTRÉE UNIFIÉ (ia.py) — la façade route bien vers chaque sous-système,
en préservant la soundness (vérifié / abstention / HORS / triage d'invention).
"""
from __future__ import annotations

from garde_ressources import borne
import classifieur_domaine as C
import moteur_invention as MI
import ia

borne(max_go=4.0, max_cpu_s=900)   # charge tout le lecteur via ia (~10 M faits) : CPU 120s défaut tuait (SIGXCPU)
ok = 0
total = 0


def check(nom, cond):
    global ok, total
    total += 1
    print(f"  [{'OK ' if cond else 'XXX'}] {nom}")
    if cond:
        ok += 1
    else:
        raise AssertionError(nom)


# demande -> classifieur
check("demande fait -> VÉRIFIÉ Paris", ia.demande("capitale de la France").valeur == "Paris")
check("demande arith -> VÉRIFIÉ 395", ia.demande("combien font 17*23+4 ?").valeur == "395")
check("demande opinion -> ABSTENTION", ia.demande("ton plat préféré ?").statut == C.ABSTENTION)
check("demande fait inconnu -> HORS", ia.demande("capitale de la Mongolie ?").statut == C.HORS)
check("demande spec calculable -> NÉCESSITÉ/VÉRIFIÉ",
      ia.demande(point_entree="somme_carres", signature="xs", exemples=[([1, 2, 3], 14), ([2, 3], 13)],
                 exemples_held=[([5], 25), ([0, 4], 16)]).statut == C.VERIFIE)

# demande -> moteur de RÈGLES (route structurée, intégrée par la porte unique)
check("demande conformité HACCP 3°C -> VÉRIFIÉ/CONFORME",
      ia.demande(scope="secteur alimentaire", ident="Conservation réfrigérée", cas={"temperature": 3}).valeur == "CONFORME")
check("demande conformité HACCP 8°C -> VÉRIFIÉ/NON_CONFORME",
      ia.demande(scope="secteur alimentaire", ident="Conservation réfrigérée", cas={"temperature": 8}).valeur == "NON_CONFORME")
check("demande lettre R413-3 -> VÉRIFIÉ (contenu)",
      "50 km/h" in (ia.demande(scope="FR", ident="Code de la route R413-3").valeur or ""))
check("demande règle d'interprétation -> ABSTENTION",
      ia.demande(scope="UE", ident="RGPD art. 5", cas={}).statut == C.ABSTENTION)
check("demande règle introuvable -> HORS (jamais inventée)",
      ia.demande(scope="FR", ident="Article imaginaire 999", cas={"x": 1}).statut == C.HORS)

# invente -> moteur_invention
v = ia.invente("amplitude", "xs", [([3, 1, 5], 4), ([2, 2], 0), ([10, 0, 3], 10)],
               [([0, 9, 4], 9), ([7], 0), ([5, 5, 1], 4), ([2, 8], 6)])
check("invente amplitude -> INVENTION", v.statut == MI.INVENTION)
v = ia.invente("rle_decode", "x", [([[5, 3], [2, 1]], [5, 5, 5, 2]), ([[7, 1], [8, 2]], [7, 8, 8])],
               [([[1, 2], [3, 1]], [1, 1, 3]), ([[4, 2]], [4, 4])])  # rle-decode résolu 2026-06-24 (après-nuit) via EXPANSION
check("invente rle_decode -> INVENTION", v.statut == MI.INVENTION)
v = ia.invente("flatten_rec", "x", [([1, [2, [3, 4]], 5], [1, 2, 3, 4, 5]), ([[1, 2], [3, [4]]], [1, 2, 3, 4])],
               [([1, [2, [3, [4, 5]]]], [1, 2, 3, 4, 5]), ([[[1]], 2], [1, 2])])  # flatten récursif résolu (récursion par auto-application)
check("invente flatten_rec -> INVENTION", v.statut == MI.INVENTION)
v = ia.invente("deep_reverse", "x", [([1, [2, 3], 4], [4, [3, 2], 1]), ([[1, 2], [3, 4]], [[4, 3], [2, 1]])],
               [([1, [2, [3, 4]]], [[[4, 3], 2], 1]), ([5, [6, 7], 8, 9], [9, 8, [7, 6], 5])])  # NOUVELLE frontière = deep-reverse
check("invente deep_reverse -> BRIQUE_MANQUANTE", v.statut == MI.BRIQUE_MANQUANTE)

# inventaire + apprend
CORPUS = [
    ("somme_carres", "xs", [([1, 2, 3], 14), ([2, 3], 13)], [([5], 25), ([0, 4], 16), ([1, 1], 2)]),
    ("max_carres", "xs", [([-3, 2], 9), ([1, 4], 16), ([-1, -5], 25)], [([0, 3], 9), ([2, -2], 4), ([-6, 1], 36)]),
]
inv = ia.inventaire(CORPUS)
check("inventaire fait émerger l'abstraction « _e * _e »", any(t == "_e * _e" for t, _ in inv.abstractions))
promo, etendue = ia.apprend(CORPUS)
check("apprend promeut une capacité et étend la bibliothèque",
      promo is not None and len(etendue) == len(MI.EXISTANT) + 1)

# substrat-réel via la façade
import substrat_physique as PH
check("invente_physique pression→lumière -> INVENTION (piézo+LED)",
      ia.invente_physique("pression", "lumiere").statut == PH.INVENTION)
check("inventaire_physique non vide (concepts cohérents nouveaux)", len(ia.inventaire_physique()) > 0)

# Phase 2 (les 3 axes) via la façade : routeur multi-domaines + boucle composite sous contrat d'atome
rc = ia.compose_besoin("maison autonome")
check("compose_besoin composite -> 4 domaines sous 4 lois distinctes, complet",
      rc["statut"] == "compose" and rc["complet"] and len(set(rc["lois"])) == 4)
check("compose_besoin besoin simple -> HORS (pas de maillage)", ia.compose_besoin("rafraichir une piece")["statut"] == "hors")
ric = ia.invente_composite("centre de calcul")
check("invente_composite -> blackboard partagé, aucun fait promu, manque visible",
      ric["statut"] == "propose" and ric["n_suppositions"] > 0 and ric["manques"] != []
      and all(ric["blackboard"].faits(s) == [] for s in ric["sujets"]))

print(f"\nIA VALIDÉ — {ok}/{total}." if ok == total else f"\nÉCHEC {ok}/{total}")
