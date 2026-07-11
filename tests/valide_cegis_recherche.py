"""
VALIDATION — BOUCLE CEGIS CÔTÉ RECHERCHE (chantier FORGE atome 3, Solar-Lezama 2006).

Le trou mesuré : les familles etend_* sont DIRIGÉES par les exemples (seuils/constantes synthétisés depuis
les données visibles). Quand la constante décisive ne vit QUE dans le held-out, la recherche conclut
BRIQUE_MANQUANTE alors qu'un candidat PARTIEL (reproduit les exemples, tué par le held-out) prouve qu'un
contre-exemple existe. La boucle CEGIS (opt-in `tours_cegis`) promeut ce contre-exemple au spec et RELANCE.

Prouve : (1) GAIN MESURÉ — une cible réelle bascule BRIQUE_MANQUANTE (défaut) -> INVENTION (CEGIS), et la
réalisation est RE-VÉRIFIÉE ici même sur TOUTES les paires (indépendamment du moteur) ; (2) OPT-IN — le
défaut (tours_cegis=0) est le flux inchangé (verdicts historiques intacts) ; (3) PROVENANCE — la promotion
est tracée dans la justification (paire promue lisible) ; (4) GARDE held-jamais-vidé — un held-out d'une
seule paire n'est JAMAIS consommé (le juge final à froid survit toujours) ; (5) SOUNDNESS inchangée —
INCOHERENT reste INCOHERENT, une vraie frontière (aucun partiel) reste BRIQUE_MANQUANTE sans promotion ;
(6) DÉTERMINISME — deux passes rendent le même verdict et la même paire promue ; (7) SERVABLE — le câblage
ia.forge_brique(tours_cegis=) rend la sortie de première classe complète (code + fait borné + appris).
"""
from __future__ import annotations

import json

from garde_ressources import borne
borne(max_cpu_s=400)
import ia
import moteur_invention as MI

ok = total = 0


def check(nom, cond):
    global ok, total
    total += 1
    print(f"  [{'OK ' if cond else 'XXX'}] {nom}")
    if cond:
        ok += 1
    else:
        raise AssertionError(nom)


def _reproduit_tout(expr, paires):
    """Re-vérification INDÉPENDANTE du moteur : la réalisation reproduit chaque paire (type-exact sur bool)."""
    ns: dict = {}
    exec(f"def _f(x):\n    return {expr}\n", ns)
    for a, o in paires:
        r = ns["_f"](a)
        if r != o or isinstance(r, bool) != isinstance(o, bool):
            return False
    return True


# La cible-basculement : somme des éléments > 5. Le seuil 5 n'est PAS dérivable des exemples (valeurs
# {1, 2, 12} -> seuils synthétisés {1, 2, 7, 12}) ; il ne l'est QUE d'une paire du held-out (valeurs 5 et 6
# encadrent la coupure). Sans CEGIS la recherche est aveugle ; avec, le contre-exemple la redirige.
NOM = "somme_sup_seuil"
EX = [([1, 12], 12), ([2, 12, 1], 12)]
HELD = [([5, 6, 1], 6), ([5, 6, 7], 13), ([1, 2, 3], 0)]

# ── (2) OPT-IN : le défaut est le flux inchangé ──────────────────────────────────────────────────────────
v0 = MI.examine_cible(NOM, "x", EX, HELD)
check("défaut (tours_cegis=0) : la cible-basculement reste BRIQUE_MANQUANTE", v0.statut == MI.BRIQUE_MANQUANTE)
check("défaut : aucune promotion tracée", "CEGIS" not in v0.justification)
for nom, ex, held, attendu in [
    ("somme_totale", [([1, 2, 3], 6), ([5], 5)], [([0, 4], 4), ([2, 2], 4)], MI.EXISTE_DEJA),
    ("amplitude", [([3, 1, 5], 4), ([2, 2], 0), ([10, 0, 3], 10)],
     [([0, 9, 4], 9), ([7], 0), ([5, 5, 1], 4), ([2, 8], 6)], MI.INVENTION),
    ("absurde", [([1, 2], 5)], [([1, 2], 9)], MI.INCOHERENT),
]:
    check(f"défaut : verdict historique intact ({nom} -> {attendu})",
          MI.examine_cible(nom, "x", ex, held).statut == attendu)

# ── (1) GAIN MESURÉ : le basculement BRIQUE_MANQUANTE -> INVENTION ───────────────────────────────────────
v1 = MI.examine_cible(NOM, "x", EX, HELD, tours_cegis=2)
check("CEGIS : la frontière bascule en INVENTION", v1.statut == MI.INVENTION)
check("CEGIS : la réalisation reproduit TOUTES les paires (re-vérifié ici, hors moteur)",
      v1.par is not None and _reproduit_tout(v1.par, EX + HELD))
# ── (3) PROVENANCE : la promotion est tracée, et UNE seule a suffi (convergence en un tour) ──────────────
check("CEGIS : promotion tracée dans la justification", "CEGIS : contre-exemple" in v1.justification)
check("CEGIS : un seul contre-exemple promu (convergence en un tour)", v1.justification.count("CEGIS") == 1)
check("CEGIS : la paire promue est lisible et vient du held-out",
      any(repr(p) in v1.justification for p in HELD))

# ── (6) DÉTERMINISME : deux passes, même verdict, même paire promue ──────────────────────────────────────
v1bis = MI.examine_cible(NOM, "x", EX, HELD, tours_cegis=2)
check("déterminisme : deux passes rendent le même verdict et la même trace",
      (v1bis.statut, v1bis.par, v1bis.justification) == (v1.statut, v1.par, v1.justification))

# ── (4) GARDE : le held-out n'est JAMAIS vidé (le dernier juge à froid survit) ───────────────────────────
v2 = MI.examine_cible(NOM, "x", EX, [([5, 6, 7], 13)], tours_cegis=2)
check("garde : un held-out d'UNE paire n'est jamais consommé (reste BRIQUE_MANQUANTE)",
      v2.statut == MI.BRIQUE_MANQUANTE and "CEGIS" not in v2.justification)
v3 = MI.examine_cible(NOM, "x", EX, [([5, 6, 1], 6), ([5, 6, 7], 13)], tours_cegis=5)
check("garde : held-out de 2 paires -> 1 consommée, 1 reste juge final (INVENTION vérifiée)",
      v3.statut == MI.INVENTION and v3.justification.count("CEGIS") == 1
      and _reproduit_tout(v3.par, EX + [([5, 6, 1], 6), ([5, 6, 7], 13)]))

# ── (5) SOUNDNESS inchangée sous CEGIS ───────────────────────────────────────────────────────────────────
vi = MI.examine_cible("absurde", "x", [([1, 2], 5)], [([1, 2], 9), ([3], 3)], tours_cegis=2)
check("soundness : INCOHERENT reste INCOHERENT sous tours_cegis", vi.statut == MI.INCOHERENT)
# Vraie frontière : aucun atome ne reproduit ces sorties (grands entiers sans rapport) -> aucun partiel,
# donc aucun contre-exemple à promouvoir : BRIQUE_MANQUANTE honnête, sans trace CEGIS.
vf = MI.examine_cible("hors_portee", "x", [([1, 2, 3], 999983), ([4], 424243)],
                      [([9], 111119), ([2, 7], 777777)], tours_cegis=2)
check("soundness : vraie frontière (aucun partiel) -> BRIQUE_MANQUANTE sans promotion",
      vf.statut == MI.BRIQUE_MANQUANTE and "CEGIS" not in vf.justification)

# ── (7) SERVABLE : câblage ia.forge_brique(tours_cegis=) ─────────────────────────────────────────────────
f0 = ia.forge_brique(NOM, "x", EX, HELD)
check("forge_brique défaut : la cible-basculement reste brique_manquante", f0["statut"] == MI.BRIQUE_MANQUANTE)
f1 = ia.forge_brique(NOM, "x", EX, HELD, tours_cegis=2)
check("forge_brique CEGIS : invention servie avec code", f1["statut"] == MI.INVENTION and f1["code"])
check("forge_brique CEGIS : fait borné rendu (le CERTAIN) + brique retenue (self-improving)",
      f1["fait_borne"] is not None and f1["appris"] is True)
check("forge_brique CEGIS : sortie JSON-sérialisable (servable inter-moteurs)",
      isinstance(json.dumps(f1, ensure_ascii=False), str))

print(f"\n== VALIDE_CEGIS_RECHERCHE : {ok}/{total} ==")
assert ok == total
