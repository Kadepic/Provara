"""
COMPRÉHENSION INTÉGRÉE — l'IA lit UNE phrase et la comprend de bout en bout (2026-06-18, mandat nuit Yohan).

« Vérifier l'intégré, pas l'isolé » : un SEUL moteur (toutes les briques compréhension allumées) résout, sur la même
phrase « le chat voit le chien » + le dictionnaire officiel, la chaîne complète :

  structure (analyse)  ->  rôles qui-fait-quoi (sujet/action/objet)  ->  sens des mots (est-une-sorte-de, catégorie
  commune)  ->  compréhension de la définition (genre)  ->  LOGIQUE (déduction).

Chaque maillon est RÉSOLU par le moteur assemblé (routé vers son étage), exécuté, et les sorties se RECOUPENT
(ex. la catégorie commune chat/chien == le genre tiré de la définition de « chat »). C'est la compréhension réelle,
au niveau vérifiable.
"""
from __future__ import annotations

import tempfile
from pathlib import Path

import lexique_fr as L
from comprehension import Predicteur
from compounding import resoudre
from generateur import GenerateurOrchestre, TYPES_RICHES
from juge import Limites
from store import Store
from taches import Tache

LIM = Limites(temps_s=3, cpu_s=2)

PHRASE = "le chat voit le chien"
# table de classes = noms/adjectifs officiels du lexique + mots-outils de la phrase.
CLASSES = {m: d["classe"] for m, d in L.LEXIQUE.items()}
CLASSES.update({"le": "determinant", "la": "determinant", "voit": "verbe", "mange": "verbe", "dort": "verbe"})
EDGES = L.edges_isa()
DEF_CHAT = L.LEXIQUE["chat"]["definition"]
PREMISSES = [("chat", "est", "félin"), ("félin", "est", "mammifère"), ("mammifère", "est", "animal")]


def _tache(point, sig, appel, attendu):
    tests = f"def check(c):\n    assert c({appel}) == {attendu!r}\ncheck({point})"
    return Tache(id=f"int/{point}", point_entree=point, prompt=f'def {point}({sig}):\n    """..."""',
                 tests=tests, tests_held_out="")


def _resoudre_exec(orch, tache):
    """Résout via le moteur ASSEMBLÉ, exécute le code produit, renvoie (étage, fonction)."""
    e, _, code, _ = resoudre(orch, tache, LIM)
    if code is None:
        return e, None
    ns: dict = {}
    exec(code, ns)
    return e, ns[tache.point_entree]


def comprend():
    """Lance la chaîne complète sur le moteur assemblé. Renvoie {réponses, étages}."""
    with tempfile.TemporaryDirectory() as d:
        st = Store(Path(d) / "s.jsonl")
        orch = GenerateurOrchestre(st, predicteur=Predicteur(st, types=TYPES_RICHES),
                                   analyse_phrase=True, comprehension_phrase=True, relation_lexicale=True,
                                   ancetre_commun=True, comprehension_definition=True, inference=True)
        maillons = {
            "structure": _tache("analyse", "classes, phrase", f"{CLASSES!r}, {PHRASE!r}",
                                 ["determinant", "nom", "verbe", "determinant", "nom"]),
            "sujet": _tache("sujet", "classes, phrase", f"{CLASSES!r}, {PHRASE!r}", "le chat"),
            "objet": _tache("objet", "classes, phrase", f"{CLASSES!r}, {PHRASE!r}", "le chien"),
            "est_animal": _tache("est_un", "aretes, x, y", f"{EDGES!r}, 'chat', 'animal'", True),
            "categorie_commune": _tache("ancetre_commun", "aretes, x, y", f"{EDGES!r}, 'chat', 'chien'", "mammifère"),
            "genre_def": _tache("genus", "classes, definition", f"{CLASSES!r}, {DEF_CHAT!r}", "mammifère"),
            "deduction": _tache("deduit", "premisses, x, y", f"{PREMISSES!r}, 'chat', 'animal'", "oui"),
        }
        reponses, etages = {}, {}
        for cle, t in maillons.items():
            e, fn = _resoudre_exec(orch, t)
            etages[cle] = e
            reponses[cle] = None if fn is None else fn(*_args(cle))
    return {"reponses": reponses, "etages": etages}


def _args(cle):
    return {
        "structure": (CLASSES, PHRASE), "sujet": (CLASSES, PHRASE), "objet": (CLASSES, PHRASE),
        "est_animal": (EDGES, "chat", "animal"), "categorie_commune": (EDGES, "chat", "chien"),
        "genre_def": (CLASSES, DEF_CHAT), "deduction": (PREMISSES, "chat", "animal"),
    }[cle]


if __name__ == "__main__":
    r = comprend()
    print(f"Phrase : « {PHRASE} »\n")
    print("Compréhension intégrée (moteur assemblé) :")
    for cle, rep in r["reponses"].items():
        print(f"  {cle:<20} -> {rep!r:<45} [étage: {r['etages'][cle]}]")
    print(f"\nRecoupement : catégorie commune chat/chien == genre de la définition de « chat » ? "
          f"{r['reponses']['categorie_commune'] == r['reponses']['genre_def']}")
