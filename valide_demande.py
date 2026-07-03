"""
DEMANDE — l'interface de requête « la parole » (2026-06-17). On prouve qu'on peut DEMANDER du code à l'IA par
l'exemple, et qu'elle répond du VÉRIFIÉ ou un HORS honnête (jamais du faux).

Critères de MORT (4) :
  1. DEMANDABLE        : une demande dans le périmètre (somme_carres par l'exemple) -> code RÉSOLU et GÉNÉRALISE
                         (held-out vérifié) -> on peut lui demander des choses.
  2. HONNÊTE / HORS    : des exemples CONTRADICTOIRES (même entrée, deux sorties) -> HORS (ok=False), jamais un faux.
  3. BUDGET            : sous budget serré, la recherche est BORNÉE (appels <= budget) et toute réponse reste SOUND.
                         (gcd se résout désormais via la famille scalaire de l'auto-synthèse — montée de capacité ;
                          le test ne dépend plus d'une cible « qui reste HORS », contraire au but du projet.)
  4. PLUSIEURS DOMAINES : nombres (somme_carres) ET chaînes (compress) résolus par la MÊME interface -> agnostique.
"""

from __future__ import annotations

from demande import demande


def _check(nom, ok):
    print(f"  [{'OK ' if ok else 'RATÉ'}] {nom}", flush=True)
    return ok


def main() -> int:
    r = []

    # 1. DEMANDABLE + GÉNÉRALISE. exemples = [(args_tuple, sortie)] ; args_tuple = (xs,) pour 1 argument liste.
    rep = demande("somme_carres", "xs", [(([1, 2, 3],), 14), (([2, 3],), 13)], [(([5],), 25), (([0, 4],), 16)])
    r.append(_check(f"DEMANDABLE : somme_carres demandé par l'exemple -> {('résolu via `'+str(rep.etage)+'`, généralise='+str(rep.generalise)) if rep.ok else 'HORS'}",
                    rep.ok and rep.generalise))

    # 2. HONNÊTE / HORS sur des exemples contradictoires (impossible) -> jamais du faux.
    rep_h = demande("impossible", "xs", [(([1],), 5), (([1],), 6)], [(([2],), 9)])
    r.append(_check(f"HONNÊTE/HORS : exemples contradictoires -> {'HORS (aucun faux)' if not rep_h.ok else 'A RENDU DU CODE (faux !)'}",
                    not rep_h.ok and rep_h.code is None))

    # 3. BUDGET : la borne de puissance est RESPECTÉE par la recherche (appels <= budget) et la réponse est SOUND.
    #    gcd se résout maintenant (auto-synthèse a ouvert la famille scalaire) -> on teste la BORNE, pas un HORS figé.
    rep_b = demande("gcd", "a, b", [((12, 8), 4), ((7, 3), 1)], [((100, 60), 20)], budget=30)
    etat_b = ("résolu via `" + str(rep_b.etage) + "`") if rep_b.ok else "HORS"
    r.append(_check(f"BUDGET : gcd budget=30 -> {etat_b} en {rep_b.appels} appels (<=30), sound",
                    rep_b.appels <= 30 and ((not rep_b.ok) or rep_b.generalise)))

    # 4. PLUSIEURS DOMAINES : chaînes (compress) par la même interface.
    rep_c = demande("compress", "s", [(("aaabb",), "a3b2"), (("x",), "x1")], [(("",), ""), (("abab",), "a1b1a1b1")])
    r.append(_check(f"PLUSIEURS DOMAINES : compress (chaînes) -> {('résolu via `'+str(rep_c.etage)+'`') if rep_c.ok else 'HORS'}",
                    rep_c.ok and rep_c.generalise))

    print()
    print("DEMANDE (« la parole ») VALIDÉE — 4/4." if all(r) else f"ÉCHEC — {sum(r)}/4.")
    return 0 if all(r) else 1


if __name__ == "__main__":
    raise SystemExit(main())
