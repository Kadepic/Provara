"""
RAFFINEMENTS SOTA DU ROUTAGE (2026-07-02) — Smith's rule / SUNNY / presolve SATzilla / auto-config AutoFolio.

Tous passent par le canal SÛR existant : le registre de stratégies per-clé (couverture identique par
construction — mêmes candidats, autre ordre ; le juge reste l'arbitre) + l'auto-config est contrainte à
couverture ≥ référence. Jugé au RÉSULTAT (coût mesuré + couverture), jamais à la catégorie.

Critères de MORT (4) :
  1. COUVERTURE IDENTIQUE : sur un lot, smith/sunny/presolve résolvent EXACTEMENT le même ensemble que rr2,
     et chaque code rendu passe le held-out (aucun masquage, aucun faux).
  2. PRESOLVE UTILE : routeur EMPOISONNÉ (votes vers un étage profond) sur une tâche triviale -> presolve
     résout STRICTEMENT moins cher que rr2 empoisonné (il attrape le trivial en tête d'escalade).
  3. JAMAIS PIRE À CHAUD : clé réchauffée par apprendre_toutes (nouvelles stratégies incluses) -> le méta-routeur
     route au coût ≤ rr2 (rr2 est dans le registre -> le min ne peut pas faire pire).
  4. AUTO-CONFIG SOUND : auto_configure rend une config à couverture COMPLÈTE (≥ référence) et de coût ≤ la
     config à-la-main (seuil=8, k=400) si celle-ci est valide ; roundtrip sauve/charge OK.

SÉQUENTIEL + garde.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from diable import BATTERIE, OPS, PREDS, PRIMS, _moteur, _seede
from garde_ressources import borne
from juge import Limites, juge
from routeur import RouteurZone, auto_configure, charge_config, sauve_config
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
    par_nom, predits, reste = _ctx(orch, tache, rz, K)
    gagne = _faire_gagne(tache, LIM)
    _, code, appels = STRATEGIES[strat](par_nom, predits, reste, gagne, votes=rz.votes_confiants(tache))
    return code, appels


def _check(nom, ok):
    print(f"  [{'OK ' if ok else 'RATÉ'}] {nom}", flush=True)
    return ok


def main() -> int:
    borne()
    r = []
    lot = ["somme_carres", "max_minus_min", "compte_pairs", "mediane", "clamp",
           "fibonacci", "somme_cubes", "alternating_sum", "gcd", "produit_premier_dernier"]

    # 1. COUVERTURE IDENTIQUE + held-out (aucun masquage, aucun faux).
    with tempfile.TemporaryDirectory() as d:
        orch = _moteur_neuf(d)
        rz = _zone()
        couverture_ok, held_ok = True, True
        for nom in lot:
            t = PAR_NOM[nom]
            codes = {s: _cout_strat(orch, t, rz, s)[0] for s in ("rr2", "smith", "sunny", "presolve")}
            resolus = {s: c is not None for s, c in codes.items()}
            if len(set(resolus.values())) != 1:
                couverture_ok = False
            for c in codes.values():
                if c is not None and t.tests_held_out and not (
                        juge(c, t.tests, LIM).passe and juge(c, t.tests_held_out, LIM).passe):
                    held_ok = False
        r.append(_check(f"COUVERTURE IDENTIQUE : smith/sunny/presolve == rr2 sur {len(lot)} tâches "
                        f"({couverture_ok}), held-out OK ({held_ok})", couverture_ok and held_ok))

    # 2. PRESOLVE UTILE : routeur empoisonné (votes -> étage profond) sur une tâche triviale.
    with tempfile.TemporaryDirectory() as d:
        orch = _moteur_neuf(d)
        t = PAR_NOM["somme_carres"]
        poison = RouteurZone()
        for _ in range(3):
            poison.apprendre(t, "monnaie")                     # prédiction FAUSSE vers un étage profond
        code_p, a_p = _cout_strat(orch, t, poison, "presolve")
        code_r, a_r = _cout_strat(orch, t, poison, "rr2")
        r.append(_check(f"PRESOLVE UTILE : empoisonné, presolve résout en {a_p} appels < rr2 {a_r} "
                        f"(résolu={code_p is not None})",
                        code_p is not None and code_r is not None and a_p < a_r))

    # 3. JAMAIS PIRE À CHAUD : registre étendu, le méta-routeur route au coût ≤ rr2.
    with tempfile.TemporaryDirectory() as d:
        orch = _moteur_neuf(d)
        rz = _zone()
        rs = RouteurStrategie()
        pire = []
        for nom in ("max_minus_min", "somme_carres", "mediane"):
            t = PAR_NOM[nom]
            couts = apprendre_toutes(orch, t, rz, rs, LIM, K)
            routed = resoudre_route_strategie(orch, t, rz, rs, LIM, K)
            if routed[2] is None or routed[1] > couts["rr2"]:
                pire.append((nom, routed[1], couts["rr2"]))
        r.append(_check(f"JAMAIS PIRE À CHAUD : routé ≤ rr2 sur 3 clés réchauffées (écarts={pire})", not pire))

    # 4. AUTO-CONFIG SOUND (mini-batterie pour rester borné) + roundtrip persistance.
    with tempfile.TemporaryDirectory() as d:
        orch = _moteur_neuf(d)
        mini = [PAR_NOM[n] for n in lot[:6]]
        best, mesures = auto_configure(orch, mini, seuils=(4, 8), ks=(400, 550), limites=LIM)
        main_cfg = next((m for m in mesures if m["seuil"] == 8 and m["k"] == 400), None)
        ok_best = best is not None and best["couverture_ok"]
        ok_vs_main = (main_cfg is None or not main_cfg["couverture_ok"]
                      or (best is not None and best["appels"] <= main_cfg["appels"]))
        chemin = Path(d) / "cfg.json"
        if best is not None:
            sauve_config(best, chemin)
        relu = charge_config(chemin) if best is not None else None
        ok_rt = best is None or (relu is not None and relu["seuil"] == best["seuil"] and relu["k"] == best["k"])
        r.append(_check(f"AUTO-CONFIG : best={best and {k: best[k] for k in ('seuil', 'k', 'appels')}} "
                        f"couverture OK ({ok_best}), ≤ config manuelle ({ok_vs_main}), roundtrip ({ok_rt})",
                        ok_best and ok_vs_main and ok_rt))

    print()
    print("ROUTAGE SOTA VALIDÉ — 4/4." if all(r) else f"ÉCHEC — {sum(r)}/4.")
    return 0 if all(r) else 1


if __name__ == "__main__":
    raise SystemExit(main())
