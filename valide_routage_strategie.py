"""
ROUTAGE DE STRATÉGIE PAR CLÉ (2026-06-19, idée Yohan) — l'IA apprend, par clé, la stratégie de traversée la MOINS
chère et y route les tâches de même clé. SÛR : toutes les stratégies ont la MÊME couverture -> neutre en correction
(jamais de faux), seulement moins d'appels. Mesuré : per-clé LOO honnête −24 %, hindsight −32 %, oracle −38 % vs rr2.

Critères de MORT (4) :
  1. SÛR À FROID : routeur vide -> predit == rr2 -> coût et résolution IDENTIQUES à rr2 pur (zéro régression).
  2. APPREND + MOINS CHER À CHAUD : sur max_minus_min, apprendre_toutes apprend rr_occam (39) << rr2 (518) ->
     un re-run routé y va et coûte BIEN moins, en résolvant.
  3. GÉNÉRALISE PAR CLÉ (held-out) : routeur réchauffé sur max_minus_min route alternating_sum (MÊME clé (1,list,int,
     F,F,F,F), JAMAIS vue) vers rr_occam -> résout, coût <= rr2 (le signal vit dans la clé, pas le cas).
  4. NEUTRE EN CORRECTION : sur un lot de tâches, le routage chaud résout EXACTEMENT les mêmes que rr2 (couverture
     identique) et chaque code rendu passe le held-out -> aucun masquage, aucun faux.

SÉQUENTIEL + garde.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from diable import BATTERIE, OPS, PREDS, PRIMS, _moteur, _seede
from garde_ressources import borne
from juge import Limites
from routeur import RouteurZone, cle_tache
from store import Store
from strategies import STRATEGIES, RouteurStrategie, _ctx, _faire_gagne, apprendre_toutes, resoudre_route_strategie

LIM = Limites(temps_s=3, cpu_s=2)
K = 550
PAR_NOM = {t.point_entree: t for _, t in BATTERIE}


def _zone():
    r = RouteurZone()
    for att, t in BATTERIE:
        r.apprendre(t, att)
    return r


def _moteur_neuf(d):
    store = Store(Path(d) / "s.jsonl")
    _seede(store)
    return _moteur(store, PRIMS, OPS, PREDS)


def _cout_strat(orch, tache, rz, strat):
    """Coût d'UNE stratégie nommée sur une tâche (sans routeur), pour comparer."""
    par_nom, predits, reste = _ctx(orch, tache, rz, K)
    gagne = _faire_gagne(tache, LIM)
    _, code, appels = STRATEGIES[strat](par_nom, predits, reste, gagne)
    return code is not None, appels


def _check(nom, ok):
    print(f"  [{'OK ' if ok else 'RATÉ'}] {nom}", flush=True)
    return ok


def main() -> int:
    borne()
    r = []

    # 1. SÛR À FROID : routeur vide -> rr2.
    with tempfile.TemporaryDirectory() as d:
        orch = _moteur_neuf(d)
        rz = _zone()
        rs = RouteurStrategie()
        t = PAR_NOM["max_minus_min"]
        froid = resoudre_route_strategie(orch, t, rz, rs, LIM, K)
        ok_rr2, a_rr2 = _cout_strat(orch, t, rz, "rr2")
        r.append(_check(f"SÛR À FROID : predit={rs.predit(t)!r}, routé en {froid[1]} appels == rr2 {a_rr2} (résolu={froid[2] is not None})",
                        rs.predit(t) == "rr2" and froid[2] is not None and froid[1] == a_rr2 and ok_rr2))

    # 2. APPREND + MOINS CHER À CHAUD : max_minus_min.
    with tempfile.TemporaryDirectory() as d:
        orch = _moteur_neuf(d)
        rz = _zone()
        rs = RouteurStrategie()
        t = PAR_NOM["max_minus_min"]
        couts = apprendre_toutes(orch, t, rz, rs, LIM, K)
        chaud = resoudre_route_strategie(orch, t, rz, rs, LIM, K)
        meilleur = rs.predit(t)
        r.append(_check(f"MOINS CHER À CHAUD : appris {couts}, predit={meilleur!r} -> routé {chaud[1]} appels "
                        f"(<< rr2 {couts['rr2']}), résolu={chaud[2] is not None}",
                        chaud[2] is not None and meilleur != "rr2" and chaud[1] * 2 < couts["rr2"]))

    # 3. GÉNÉRALISE PAR CLÉ (held-out) : réchauffé sur max_minus_min, route alternating_sum (même clé, jamais vue).
    with tempfile.TemporaryDirectory() as d:
        orch = _moteur_neuf(d)
        rz = _zone()
        rs = RouteurStrategie()
        seed, cible = PAR_NOM["max_minus_min"], PAR_NOM["alternating_sum"]
        meme_cle = cle_tache(seed) == cle_tache(cible)
        apprendre_toutes(orch, seed, rz, rs, LIM, K)         # n'apprend QUE sur le seed
        routed = resoudre_route_strategie(orch, cible, rz, rs, LIM, K)
        _, a_rr2 = _cout_strat(orch, cible, rz, "rr2")
        r.append(_check(f"GÉNÉRALISE PAR CLÉ : alternating_sum (même clé={meme_cle}) routé via {rs.predit(cible)!r} en "
                        f"{routed[1]} appels (rr2={a_rr2}), résolu={routed[2] is not None}",
                        meme_cle and routed[2] is not None and routed[1] <= a_rr2))

    # 4. NEUTRE EN CORRECTION : couverture identique à rr2 sur un lot, chaque code passe le held-out.
    lot = ["somme_carres", "max_minus_min", "alternating_sum", "compte_pairs", "produit_premier_dernier",
           "mediane", "clamp", "fibonacci", "suite_ari", "somme_cubes"]
    couverture_ok = True
    held_ok = True
    with tempfile.TemporaryDirectory() as d:
        orch = _moteur_neuf(d)
        rz = _zone()
        rs = RouteurStrategie()
        for nom in lot:                                       # réchauffe sur tout le lot (chaud)
            apprendre_toutes(orch, PAR_NOM[nom], rz, rs, LIM, K)
        for nom in lot:
            t = PAR_NOM[nom]
            routed = resoudre_route_strategie(orch, t, rz, rs, LIM, K)
            ok_rr2, _ = _cout_strat(orch, t, rz, "rr2")
            if (routed[2] is not None) != ok_rr2:
                couverture_ok = False
            # le code routé doit re-passer visible+held (neutre en correction)
            if routed[2] is not None and t.tests_held_out:
                from juge import juge
                if not (juge(routed[2], t.tests, LIM).passe and juge(routed[2], t.tests_held_out, LIM).passe):
                    held_ok = False
    r.append(_check(f"NEUTRE EN CORRECTION : couverture == rr2 sur {len(lot)} tâches ({couverture_ok}), held-out OK ({held_ok})",
                    couverture_ok and held_ok))

    print()
    print("ROUTAGE DE STRATÉGIE VALIDÉ — 4/4." if all(r) else f"ÉCHEC — {sum(r)}/4.")
    return 0 if all(r) else 1


if __name__ == "__main__":
    raise SystemExit(main())
