r"""
FABRIQUE_FRANCAIS — dataset français VÉRIFIÉ, model-free (2026-06-18, idée Yohan « entraîner en français » + saut APPRENDRE).

Premier pas qui DÉ-RISQUE le QLoRA sans rouvrir la boîte noire : on construit un jeu d'entraînement de FORME du
français (morphologie : conjugaison, pluriel, féminin) où CHAQUE paire est vérifiée par DOUBLE source indépendante :

    PROFESSEUR (gold certifié : vocabulaire RÉEL + bonne réponse)  ↔  BRIQUE (reproduit la forme par sa RÈGLE)
                                          \                        /
                                       le JUGE garde l'ACCORD (exécute la règle en sandbox, == gold)

Anti-dérive (comme le Store) : si la brique ne reproduit pas le gold (mot hors-portée — irrégulier, groupe 2…),
la paire est EXCLUE, jamais exportée fausse. Le held-out est intrinsèque : la règle s'applique à du vocabulaire
JAMAIS « vu » (les briques n'ont aucune liste de mots). Sortie = JSONL instruction→réponse, prêt pour QLoRA.

Couvre la FORME (réglée, donc vérifiable). Le SENS ouvert reste le mur : pas de gold mécanique pour lui.
"""
from __future__ import annotations

import json
from pathlib import Path

from generateur import GenerateurConjugaison, GenerateurFeminin, GenerateurPluriel
from juge import Limites, juge
from taches import Tache

LIM = Limites(temps_s=3, cpu_s=2)

_BRIQUES = {"conjugaison": GenerateurConjugaison, "pluriel": GenerateurPluriel, "feminin": GenerateurFeminin}
_POINT = {"conjugaison": "conjugue", "pluriel": "pluriel", "feminin": "feminin"}

_TEMPS_NOM = {"present": "au présent", "imparfait": "à l'imparfait", "futur": "au futur"}
_PERS_NOM = {0: "à la 1re personne du singulier", 1: "à la 2e personne du singulier",
             2: "à la 3e personne du singulier", 3: "à la 1re personne du pluriel",
             4: "à la 2e personne du pluriel", 5: "à la 3e personne du pluriel"}


# ------------------------------------------------------------------------------------------------------------------
# GOLD CERTIFIÉ PAR LE PROFESSEUR (vocabulaire réel, réponses correctes). Item = (brique, params, gold).
# ------------------------------------------------------------------------------------------------------------------
def _conjug_reguliers(infinitifs):
    """Génère le gold de conjugaison pour de VRAIS verbes du 1er groupe (-er réguliers, certifiés par le prof)."""
    P, I, F = (["e", "es", "e", "ons", "ez", "ent"],
               ["ais", "ais", "ait", "ions", "iez", "aient"],
               ["ai", "as", "a", "ons", "ez", "ont"])
    items = []
    for inf in infinitifs:
        rad = inf[:-2]
        items += [("conjugaison", (inf, "present", p), rad + P[p]) for p in range(6)]
        items += [("conjugaison", (inf, "imparfait", p), rad + I[p]) for p in range(6)]
        items += [("conjugaison", (inf, "futur", p), inf + F[p]) for p in range(6)]
    return items


SEED = (
    _conjug_reguliers(["parler", "donner", "chanter", "aimer", "jouer", "travailler", "regarder", "écouter"])
    # pluriel — gold INDÉPENDANT (connaissance du prof) : réguliers + familles -al/-eau/-eu.
    + [("pluriel", ("chat",), "chats"), ("pluriel", ("table",), "tables"), ("pluriel", ("ami",), "amis"),
       ("pluriel", ("mur",), "murs"), ("pluriel", ("livre",), "livres"),
       ("pluriel", ("journal",), "journaux"), ("pluriel", ("cheval",), "chevaux"),
       ("pluriel", ("animal",), "animaux"), ("pluriel", ("général",), "généraux"),
       ("pluriel", ("bateau",), "bateaux"), ("pluriel", ("gâteau",), "gâteaux"),
       ("pluriel", ("château",), "châteaux"), ("pluriel", ("cheveu",), "cheveux"),
       ("pluriel", ("jeu",), "jeux"), ("pluriel", ("feu",), "feux")]
    # féminin — gold INDÉPENDANT : réguliers + invariants -e + familles -eux/-er/-f.
    + [("feminin", ("grand",), "grande"), ("feminin", ("petit",), "petite"), ("feminin", ("joli",), "jolie"),
       ("feminin", ("vert",), "verte"), ("feminin", ("bleu",), "bleue"),
       ("feminin", ("rouge",), "rouge"), ("feminin", ("jaune",), "jaune"),
       ("feminin", ("heureux",), "heureuse"), ("feminin", ("joyeux",), "joyeuse"),
       ("feminin", ("courageux",), "courageuse"), ("feminin", ("léger",), "légère"),
       ("feminin", ("premier",), "première"), ("feminin", ("fier",), "fière"),
       ("feminin", ("actif",), "active"), ("feminin", ("sportif",), "sportive"), ("feminin", ("neuf",), "neuve")]
)


def instruction(item) -> str:
    """Consigne en français naturel pour une paire d'entraînement."""
    brique, params, _ = item
    if brique == "conjugaison":
        inf, t, p = params
        return f"Conjugue le verbe « {inf} » {_TEMPS_NOM[t]}, {_PERS_NOM[p]}."
    if brique == "pluriel":
        return f"Donne le pluriel du nom « {params[0]} »."
    return f"Donne le féminin de l'adjectif « {params[0]} »."


def _tache(item) -> Tache:
    brique, params, gold = item
    pe = _POINT[brique]
    appel = ", ".join(repr(a) for a in params)
    tests = f"def check(c):\n    assert c({appel}) == {gold!r}\ncheck({pe})"
    return Tache(id=f"fr/{pe}/{appel}", point_entree=pe, prompt=f'def {pe}(*a):\n    """..."""',
                 tests=tests, tests_held_out="")


def _reproduit(item, n: int = 8) -> bool:
    """La BRIQUE reproduit-elle le gold du prof ? (règle exécutée en sandbox par le juge). True = paire VÉRIFIÉE."""
    brique = item[0]
    gen = _BRIQUES[brique]()
    t = _tache(item)
    return any(juge(code, t.tests, LIM).passe for code in gen.propose(t.prompt, n))


def fabrique(items, chemin_sortie) -> dict:
    """Construit le dataset : n'exporte QUE les paires où prof et brique sont D'ACCORD. Renvoie un résumé."""
    exportes, exclus = [], []
    for item in items:
        (exportes if _reproduit(item) else exclus).append(item)
    Path(chemin_sortie).parent.mkdir(parents=True, exist_ok=True)
    vus = set()
    with open(chemin_sortie, "w", encoding="utf-8") as f:
        for item in exportes:
            consigne, gold = instruction(item), item[2]
            if consigne in vus:
                continue
            vus.add(consigne)
            f.write(json.dumps({"instruction": consigne, "reponse": gold}, ensure_ascii=False) + "\n")
    return {"vus": len(items), "exportes": len(exportes), "exclus": len(exclus),
            "lignes": len(vus), "chemin": str(chemin_sortie),
            "mots_exclus": [it[1][0] for it in exclus]}


def resume(chemin_sortie) -> dict:
    """Relit le JSONL et vérifie qu'il est BIEN FORMÉ (chaque ligne = JSON avec instruction + réponse non vides)."""
    lignes = valides = mal = 0
    with open(chemin_sortie, encoding="utf-8") as fh:
        for ligne in fh:
            ligne = ligne.strip()
            if not ligne:
                continue
            lignes += 1
            try:
                ex = json.loads(ligne)
                if ex.get("instruction", "").strip() and ex.get("reponse", "").strip():
                    valides += 1
                else:
                    mal += 1
            except Exception:
                mal += 1
    return {"lignes": lignes, "valides": valides, "mal_formees": mal}


if __name__ == "__main__":
    import sys
    sortie = sys.argv[1] if len(sys.argv) > 1 else "datasets/francais_forme.jsonl"
    r = fabrique(SEED, sortie)
    print("Fabrique :", r)
    print("Vérif    :", resume(sortie))
