"""
MESURE — « LA STRUCTURE TRANCHE PAR TÂCHE » poussé au max (2026-06-19, mandat Yohan « teste toutes les idées du même
principe que le round-robin de rr2, le plus performant possible ; la réalité tranche »).

rr2 capte 96 % du gain v3a->oracle sur la famille ambiguë (1,list,int) ; le résiduel (136 appels) vit sur 5 tâches où
v3a (profondeur canonique) bat rr2 (gagnant tôt-en-canonique-peu-profond, que le round-robin dilue). On cherche UNE
traversée unique dont l'ORDRE atteint le gagnant de CHAQUE tâche plus vite, SANS choisir de stratégie à la main
(comme rr2). Candidats, tous « structure -> per-tâche » :
  - rr2          : round-robin largeur, stride 1 (référence câblée).
  - rr_stride k  : round-robin, k candidats/étage/tour (k=2,3) -> interpole largeur(1)<->profondeur(inf).
  - topfirst     : profondeur de l'étage le PLUS voté à fond, puis round-robin le reste prédit, puis fallback rr.
  - occam        : aplatit TOUS les candidats prédits, ordre par longueur de code (simplicité d'abord), puis reste.
  - costweight   : round-robin mais étages prédits triés par NB de candidats croissant (les étages bon-marché d'abord).
Plus, plafond du ROUTAGE-DE-STRATÉGIE par clé (LOO) : le choix de stratégie est NEUTRE EN CORRECTION (couverture
identique), donc apprendre par clé la stratégie la moins chère est SÛR par construction. On mesure le plafond LOO.

SÉQUENTIEL (IA_NPROC=1) + garde. Cadrage : aucune assertion (mesure).
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

from compounding import resoudre
from diable import BATTERIE, OPS, PREDS, PRIMS, _moteur, _seede
from garde_ressources import borne
from juge import Limites
from routeur import RouteurZone, cle_tache, resoudre_route, resoudre_route_rr2
from store import Store

LIM = Limites(temps_s=3, cpu_s=2)
K = 550


def _routeur():
    r = RouteurZone()
    for att, t in BATTERIE:
        r.apprendre(t, att)
    return r


def _ctx(orch, tache, r):
    """(par_nom, predits, reste) — réplique EXACTE de la logique de routeur (ordre canonique, prédits confiants)."""
    etages = orch.etages(tache.prompt, K)
    par_nom = {nom: cands for nom, cands in etages}
    predits = [e for e in r.predit(tache) if e in par_nom]
    reste = [nom for nom, _ in etages if nom not in predits]
    return par_nom, predits, reste


def _faire_gagne(tache, juge_fn):
    def gagne(code):
        if not juge_fn(code, tache.tests, LIM).passe:
            return False
        if tache.tests_held_out and not juge_fn(code, tache.tests_held_out, LIM).passe:
            return False
        return True
    return gagne


# --- traverseurs élémentaires (chacun renvoie (nom, code, appels) ; appels = 1 par candidat testé, comme routeur) ---

def _rr(par_nom, noms, gagne, stride=1):
    appels, i, encore = 0, 0, True
    while encore:
        encore = False
        for nom in noms:
            cands = par_nom[nom]
            for s in range(stride):
                idx = i + s
                if idx < len(cands):
                    encore = True
                    appels += 1
                    if gagne(cands[idx]):
                        return nom, cands[idx], appels
        i += stride
    return None, None, appels


def _depth(par_nom, noms, gagne):
    appels = 0
    for nom in noms:
        for code in par_nom[nom]:
            appels += 1
            if gagne(code):
                return nom, code, appels
    return None, None, appels


def _occam(par_nom, noms, gagne):
    plat = [(nom, code) for nom in noms for code in par_nom[nom]]
    plat.sort(key=lambda nc: len(nc[1]))
    appels = 0
    for nom, code in plat:
        appels += 1
        if gagne(code):
            return nom, code, appels
    return None, None, appels


def _deux_phases(par_nom, predits, reste, gagne, runner):
    n, c, a1 = runner(par_nom, predits, gagne)
    if c is not None:
        return n, c, a1
    n, c, a2 = runner(par_nom, reste, gagne)
    return n, c, a1 + a2


# --- stratégies complètes (prédits PUIS fallback) ---

def st_rr2(par_nom, predits, reste, gagne):
    return _deux_phases(par_nom, predits, reste, gagne, lambda p, n, g: _rr(p, n, g, 1))


def st_stride2(par_nom, predits, reste, gagne):
    return _deux_phases(par_nom, predits, reste, gagne, lambda p, n, g: _rr(p, n, g, 2))


def st_stride3(par_nom, predits, reste, gagne):
    return _deux_phases(par_nom, predits, reste, gagne, lambda p, n, g: _rr(p, n, g, 3))


def st_occam(par_nom, predits, reste, gagne):
    return _deux_phases(par_nom, predits, reste, gagne, _occam)


def st_costweight(par_nom, predits, reste, gagne):
    # round-robin mais étages prédits triés par nb de candidats CROISSANT (bon-marché d'abord)
    p = sorted(predits, key=lambda nom: len(par_nom[nom]))
    rr_sorted = sorted(reste, key=lambda nom: len(par_nom[nom]))
    n, c, a1 = _rr(par_nom, p, gagne, 1)
    if c is not None:
        return n, c, a1
    n, c, a2 = _rr(par_nom, rr_sorted, gagne, 1)
    return n, c, a1 + a2


def st_topfirst(par_nom, predits, reste, gagne):
    # profondeur de l'étage le PLUS voté (predits[0]) à fond, puis round-robin le reste prédit, puis fallback rr
    appels = 0
    if predits:
        top = predits[0]
        for code in par_nom[top]:
            appels += 1
            if gagne(code):
                return top, code, appels
        n, c, a = _rr(par_nom, predits[1:], gagne, 1)
        appels += a
        if c is not None:
            return n, c, appels
    n, c, a = _rr(par_nom, reste, gagne, 1)
    appels += a
    return n, c, appels


STRATS = [
    ("rr2", st_rr2), ("stride2", st_stride2), ("stride3", st_stride3),
    ("occam", st_occam), ("costw", st_costweight), ("topfirst", st_topfirst),
]


def _un(i):
    att, tache = BATTERIE[i]
    if cle_tache(tache)[:3] != (1, "list", "int"):
        return None
    from juge import juge
    with tempfile.TemporaryDirectory() as d:
        store = Store(Path(d) / "s.jsonl")
        _seede(store)
        orch = _moteur(store, PRIMS, OPS, PREDS)
        r = _routeur()
        _, a_esc, c_esc, _ = resoudre(orch, tache, LIM, K)
        _, a_v3a, c_v3a, _ = resoudre_route(orch, tache, r, LIM, K)
        par_nom, predits, reste = _ctx(orch, tache, r)
        gagne = _faire_gagne(tache, juge)
        couts, oks = {"v3a": a_v3a}, {"v3a": c_v3a is not None}
        for nom, fn in STRATS:
            _, c, a = fn(par_nom, predits, reste, gagne)
            couts[nom] = a
            oks[nom] = c is not None
    return (tache.point_entree, cle_tache(tache), a_esc, couts, oks)


def main() -> int:
    borne()
    nproc = max(1, int(os.environ.get("IA_NPROC", "1")))
    items = range(len(BATTERIE))
    res = [r for r in (map(_un, items) if nproc == 1 else __import__("garde_ressources").pmap(_un, items)) if r]

    labels = ["v3a"] + [n for n, _ in STRATS]
    print("=== STRUCTURE -> PER-TÂCHE : batterie d'hybrides sur (1,list,int) — appels juge ===\n")
    head = f"  {'tâche':<24}" + "".join(f"{l:>9}" for l in labels) + f"{'oracle':>9}"
    print(head)
    tot = {l: 0 for l in labels}
    couv = {l: 0 for l in labels}
    toracle = 0
    par_cle = {}  # clé -> liste de (couts) pour LOO
    for fn, cle, a_esc, couts, oks in res:
        oracle = min(couts.values())
        toracle += oracle
        for l in labels:
            tot[l] += couts[l]
            couv[l] += int(oks[l])
        par_cle.setdefault(cle, []).append(couts)
        ligne = f"  {fn:<24}" + "".join(f"{couts[l]:>9}" for l in labels) + f"{oracle:>9}"
        print(ligne)
    n = len(res)
    print(f"\n  Couverture (doit être {n}/{n} partout) : " + " | ".join(f"{l} {couv[l]}" for l in labels))
    te = sum(a_esc for _, _, a_esc, _, _ in res)

    def pct(t):
        return f"{t} (-{100*(te-t)/te:.0f}%)" if te else str(t)
    print(f"\n  escalade {te}")
    for l in labels:
        print(f"  {l:<10} {pct(tot[l])}")
    print(f"  ORACLE     {pct(toracle)}")
    best = min(labels, key=lambda l: tot[l])
    print(f"\n  MEILLEUR stratégie unique = {best} ({tot[best]} appels, capte "
          f"{100*(tot['rr2']-tot[best])/(tot['rr2']-toracle) if tot['rr2']>toracle else 0:.0f}% du résiduel rr2->oracle).")

    # --- plafond ROUTAGE-DE-STRATÉGIE par clé (LOO) : neutre en correction -> sûr ---
    # Pour chaque tâche, on choisit la stratégie qui minimise le coût sur les AUTRES tâches de même clé
    # (par défaut rr2 si clé singleton). Somme = plafond du per-key strategy routing (généralisation honnête).
    cand = ["v3a", "rr2", "topfirst", "occam"]
    total_loo = 0
    for cle, liste in par_cle.items():
        for j, couts in enumerate(liste):
            autres = [c for k, c in enumerate(liste) if k != j]
            if not autres:
                choix = "rr2"
            else:
                choix = min(cand, key=lambda s: sum(a[s] for a in autres))
            total_loo += couts[choix]
    print(f"\n  PLAFOND per-key strategy routing (LOO, sûr/neutre-correction) = {pct(total_loo)}")
    print("  Lecture : si une stratégie unique >= rr2 -> on la câble. Si le LOO bat la meilleure unique ->")
    print("  le routage-de-stratégie par clé vaut une brique (le routeur apprend clé->stratégie, pas que clé->étage).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
