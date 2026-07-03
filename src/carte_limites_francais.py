"""
CARTE_LIMITES_FRANCAIS — jusqu'où le model-free monte en français, et où est le mur (2026-06-18, Yohan « déterminer
les limites que je peux atteindre »).

Méthode (la réalité juge) : une ÉCHELLE de phénomènes français de difficulté croissante. Chaque barreau est SONDÉ
sur le moteur model-free ASSEMBLÉ (toutes les briques FORME allumées) via `resoudre` — ATTEINT si une brique le
résout, MUR sinon. On classe chaque mur par NATURE :

  REGLE       — dérivable par une règle finie  -> ATTEINT, cœur du model-free.
  LEXICAL     — info ARBITRAIRE à mémoriser (genre d'un nom, groupe d'un verbe) : model-free possible SEULEMENT via
                une TABLE finie = de la DONNÉE, plus une règle. Frontière : faisable mais c'est là qu'un modèle
                compresse mieux.
  STRUCTUREL  — composition de règles (accord propagé dans une phrase) : COMBLABLE par une brique pas encore écrite.
  SENS        — pas de juge mécanique (pertinence, répondre à une question ouverte) : MUR DUR, hors model-free ET
                hors vérifiable.

Verdict : le plafond model-free = tout REGLE + ce qu'on accepte d'encoder en TABLE (LEXICAL) ; le mur DUR = SENS.
"""
from __future__ import annotations

import tempfile
from pathlib import Path

from comprehension import Predicteur
from compounding import resoudre
from generateur import GenerateurOrchestre, TYPES_RICHES
from juge import Limites
from store import Store
from taches import Tache

LIM = Limites(temps_s=3, cpu_s=2)


def _tache(pe, appel, gold):
    tests = f"def check(c):\n    assert c({appel}) == {gold!r}\ncheck({pe})"
    return Tache(id=f"lim/{pe}/{appel}", point_entree=pe, prompt=f'def {pe}(*a):\n    """..."""',
                 tests=tests, tests_held_out="")


# Échelle : (n, nom, catégorie, comblable, tâche-sonde) ; tâche=None pour SENS (aucun juge ne peut l'exprimer).
RUNGS = [
    (1, "Conjugaison -er, présent", "REGLE", True, _tache("conjugue", "'parler','present',2", "parle")),
    (2, "Conjugaison -er, imparfait/futur", "REGLE", True, _tache("conjugue", "'donner','futur',0", "donnerai")),
    (3, "Conjugaison -er, irréguliers fréquents", "REGLE", True, _tache("conjugue", "'être','present',0", "suis")),
    (4, "Pluriel (réguliers + familles -al/-eau/-eu)", "REGLE", True, _tache("pluriel", "'cheval'", "chevaux")),
    (5, "Féminin (réguliers + familles -eux/-er/-f)", "REGLE", True, _tache("feminin", "'heureux'", "heureuse")),
    (6, "Conjugaison -ir, 2ᵉ groupe (-iss-)", "REGLE", True, _tache("conjugue", "'finir','present',3", "finissons")),
    (7, "Conjugaison -ir, 3ᵉ groupe (partir)", "LEXICAL", True, _tache("conjugue", "'partir','present',0", "pars")),
    (8, "Genre d'un nom (le/la)", "LEXICAL", True, _tache("genre", "'table'", "la")),
    (9, "Accord dans le groupe nominal", "STRUCTUREL", True, _tache("accord", "'le chat noir'", "les chats noirs")),
    (10, "Phrase qui a du SENS / question ouverte", "SENS", False, None),
]


def carte():
    """Sonde chaque barreau sur le moteur assemblé. Renvoie la liste des barreaux avec `atteint` (bool)."""
    out = []
    with tempfile.TemporaryDirectory() as d:
        st = Store(Path(d) / "s.jsonl")
        orch = GenerateurOrchestre(st, predicteur=Predicteur(st, types=TYPES_RICHES),
                                   conjugaison=True, conjugaison2=True, pluriel=True, feminin=True)
        for n, nom, cat, comblable, tache in RUNGS:
            if tache is None:
                atteint = False
            else:
                _, _, code, _ = resoudre(orch, tache, LIM)
                atteint = code is not None
            out.append({"n": n, "nom": nom, "categorie": cat, "comblable": comblable, "atteint": atteint})
    return out


def verdict(c):
    regle_atteints = [r for r in c if r["categorie"] == "REGLE" and r["atteint"]]
    murs = [r for r in c if not r["atteint"]]
    dur = [r for r in murs if not r["comblable"]]
    return {
        "plafond_regle": max((r["n"] for r in regle_atteints), default=0),
        "premier_mur": min((r["n"] for r in murs), default=None),
        "murs_comblables": [r["n"] for r in murs if r["comblable"]],
        "mur_dur": [r["n"] for r in dur],
    }


def main() -> int:
    c = carte()
    print("CARTE DES LIMITES — FRANÇAIS MODEL-FREE\n")
    for r in c:
        etat = "✅ ATTEINT" if r["atteint"] else f"⛔ MUR ({r['categorie']}{'—comblable' if r['comblable'] else '—DUR'})"
        print(f"  {r['n']:>2}. {r['nom']:<46} {etat}")
    v = verdict(c)
    print()
    print(f"  Plafond REGLE atteint      : barreau {v['plafond_regle']} (tout le réglé est couvert)")
    print(f"  1er mur                    : barreau {v['premier_mur']} (frontière LEXICAL = donnée, pas règle)")
    print(f"  Murs COMBLABLES (table/brique) : {v['murs_comblables']}")
    print(f"  Mur DUR (sans juge = SENS)     : {v['mur_dur']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
