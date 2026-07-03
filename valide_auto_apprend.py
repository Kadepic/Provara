"""
VALIDE — AUTO-APPRENTISSAGE AUTONOME (2026-06-22). Verrouille le comportement de `auto_apprend.MoteurAutonome` :
  1) VOCABULAIRE INVENTÉ : le combinateur binaire rend `max−min` représentable (impossible avec compose/map seuls).
  2) ACTIVE LEARNING SÛR : face à des exemples faibles (coïncidence possible), l'IA détecte l'ambiguïté et demande
     l'entrée discriminante ; après réponse de la RÉALITÉ (oracle), elle élimine les coïncidences et converge sur le
     VRAI solveur — OU déclare HORS en découvrant son gap. JAMAIS de faux engagé.
  3) ANTI-COÏNCIDENCE : `deuxieme_elt` (vrai solveur x[1] non représentable) -> HORS honnête (et surtout PAS `min+1`).
SÉQUENTIEL + garde mémoire.
"""
from __future__ import annotations

from auto_apprend import MoteurAutonome
from demande import _asserts
from garde_ressources import borne
from taches import Tache

def _T(pe, vis):
    return Tache(id=pe, point_entree=pe, prompt=f"def {pe}(x):\n  pass",
                 tests=_asserts(pe, [((a,), o) for a, o in vis]), tests_held_out="")


def _boucle(m, pe, vis, oracle, max_q=4):
    """Active learning : tant qu'ambigu, l'IA demande l'entrée discriminante, la réalité répond, elle réessaie."""
    vis = list(vis)
    r = None
    for _ in range(max_q):
        r = m.resoudre_confiant(_T(pe, vis), vis)   # sondes AUTO-forgées depuis les exemples (zéro aide)
        if r["etat"] != "ambigu":
            break
        q = r["question"]
        vis.append((list(q), oracle(list(q))))
    return r


def _check(nom, cond):
    print(f"  [{'OK ' if cond else 'RATÉ'}] {nom}")
    return cond


def _auto(m, pe, vis, oracle):
    return m.resoudre_autonome(lambda ex: _T(pe, ex), vis, oracle)


def main() -> int:
    borne()
    m = MoteurAutonome()
    m.explore_combine(budget=2000)
    res = []

    # 1) max−min : INVENTÉ (combinateur binaire) + convergence active learning vers le VRAI solveur.
    r = _auto(m, "max_moins_min", [([3, 1, 5], 4), ([2, 2], 0)], lambda x: max(x) - min(x))
    res.append(_check(f"max−min INVENTÉ -> {r.get('expr', r['etat'])}",
                      r["etat"] in ("confiant", "tentatif") and "max(x)" in r.get("expr", "") and "min(x)" in r.get("expr", "")))

    # 2) deuxieme_elt : GAP auto-découvert -> l'IA INVENTE x[1] (extension de vocabulaire) -> converge. JAMAIS min+1.
    r = _auto(m, "deuxieme_elt", [([9, 8, 7], 8), ([1, 2, 3], 2)], lambda x: x[1])
    res.append(_check(f"deuxieme_elt : vocabulaire AUTO-INVENTÉ -> {r.get('expr', r['etat'])}",
                      r["etat"] in ("confiant", "tentatif") and r.get("expr") == "x[1]"))

    # 3) troisieme : autre indexation jamais vue -> inventée à la demande.
    r = _auto(m, "troisieme", [([4, 5, 6, 7], 6), ([9, 8, 7, 6, 5], 7)], lambda x: x[2])
    res.append(_check(f"troisieme : x[2] auto-inventé -> {r.get('expr', r['etat'])}",
                      r["etat"] in ("confiant", "tentatif") and r.get("expr") == "x[2]"))

    # 4) produit_liste : GAP fold -> l'IA INVENTE un fold reduce(a*b) (extension de vocabulaire), réalité-jugé.
    r = _auto(m, "produit_liste", [([2, 3, 4], 24), ([5, 2], 10), ([1, 1, 5], 5)],
              lambda x: x[0] * x[1] * (x[2] if len(x) > 2 else 1))
    res.append(_check(f"produit_liste : fold AUTO-INVENTÉ -> {r.get('expr', r['etat'])}",
                      r["etat"] in ("confiant", "tentatif") and "reduce" in r.get("expr", "")))

    # 5) PROFONDEUR (recherche dirigée AGG∘map(f)) : somme_carres + somme_cubes — chaînes 3-profondes construites.
    r = _auto(m, "somme_carres", [([1, 2, 3], 14), ([2, 3], 13), ([1, 1, 1], 3)], lambda x: sum(e * e for e in x))
    res.append(_check(f"somme_carres (dirigé) -> {r.get('expr', r['etat'])}",
                      r["etat"] in ("confiant", "tentatif") and "sum(" in r.get("expr", "")))
    r = _auto(m, "somme_cubes", [([1, 2], 9), ([2, 3], 35), ([1, 1, 1], 3), ([2, 2], 16)], lambda x: sum(e ** 3 for e in x))
    res.append(_check(f"somme_cubes (dirigé, 3-profond) -> {r.get('expr', r['etat'])}",
                      r["etat"] in ("confiant", "tentatif") and "sum(" in r.get("expr", "")))

    # 7) DOMAINE INCONNU (chaînes, AUCUNE primitive seed) : l'IA acquiert les opérations par schéma, réalité-jugé.
    r = _auto(m, "renverse", [("abc", "cba"), ("hello", "olleh"), ("xy", "yx")], lambda s: s[::-1])
    res.append(_check(f"chaînes : renverse acquis -> {r.get('expr', r['etat'])}",
                      r["etat"] in ("confiant", "tentatif") and "[::-1]" in r.get("expr", "")))
    r = _auto(m, "compte_majus", [("AbC", 2), ("abc", 0), ("HEY", 3)], lambda s: sum(c.isupper() for c in s))
    res.append(_check(f"chaînes : compte_majus acquis -> {r.get('expr', r['etat'])}",
                      r["etat"] in ("confiant", "tentatif") and "isupper" in r.get("expr", "")))

    # 8) incohérent : aucune brique ne généralise -> HORS HONNÊTE (jamais de faux).
    r = _auto(m, "incoherent_xyz", [([2, 3, 4], 999)], lambda x: 999)
    res.append(_check(f"incohérent -> {r['etat']} (HORS honnête)", r["etat"] == "hors"))

    # 5) ambiguïté DÉTECTÉE seule (sait qu'elle ne sait pas) sur exemples faibles, AVANT toute extension/question.
    ex0 = [([9, 8, 7], 8), ([1, 2, 3], 2)]
    r0 = m.resoudre_confiant(_T("deuxieme_elt", ex0), ex0)
    res.append(_check("ambiguïté/incertitude détectée seule", r0["etat"] in ("ambigu", "tentatif")))

    n = sum(res)
    print(f"\nAUTO_APPREND {'VALIDÉ' if n == len(res) else 'ÉCHEC'} — {n}/{len(res)}.")
    return 0 if n == len(res) else 1


if __name__ == "__main__":
    raise SystemExit(main())
