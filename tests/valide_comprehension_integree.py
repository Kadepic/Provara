"""COMPRÉHENSION INTÉGRÉE — le moteur ASSEMBLÉ comprend une phrase de bout en bout (vérifier l'intégré, pas l'isolé).
CORRECT : chaque maillon (structure→rôles→sens→genre→logique) donne la bonne réponse. ROUTAGE : chaque maillon part
sur son étage DISTINCT (zéro masquage). RECOUPEMENT : les couches se croisent (catégorie commune == genre de la
définition). COMPLET : aucun maillon non résolu."""
from __future__ import annotations

from comprehension_integree import comprend


def _check(nom, c):
    print(f"  [{'OK ' if c else 'RATÉ'}] {nom}")
    return c


def main() -> int:
    r = []
    res = comprend()
    rep, eta = res["reponses"], res["etages"]

    attendu = {
        "structure": ["determinant", "nom", "verbe", "determinant", "nom"],
        "sujet": "le chat", "objet": "le chien", "est_animal": True,
        "categorie_commune": "mammifère", "genre_def": "mammifère", "deduction": "oui",
    }
    r.append(_check(f"CORRECT : les 7 maillons donnent la bonne réponse {list(rep.values())}",
                    all(rep[k] == attendu[k] for k in attendu)))

    etages_attendus = {
        "structure": "analyse-phrase", "sujet": "comprehension-phrase", "objet": "comprehension-phrase",
        "est_animal": "relation-lexicale", "categorie_commune": "ancetre-commun",
        "genre_def": "comprehension-definition", "deduction": "inference",
    }
    r.append(_check("ROUTAGE : chaque maillon routé vers son étage attendu (zéro masquage)",
                    all(eta[k] == etages_attendus[k] for k in etages_attendus)))

    distincts = {eta[k] for k in ("structure", "sujet", "est_animal", "categorie_commune", "genre_def", "deduction")}
    r.append(_check(f"DISTINCTS : {len(distincts)} étages différents mobilisés (≥6)", len(distincts) >= 6))

    r.append(_check("RECOUPEMENT : catégorie commune chat/chien == genre tiré de la définition de « chat »",
                    rep["categorie_commune"] == rep["genre_def"] == "mammifère"))

    r.append(_check("COMPLET : aucun maillon non résolu", all(v is not None for v in rep.values())))

    print()
    print("COMPRÉHENSION INTÉGRÉE VALIDÉE — 5/5." if all(r) else f"ÉCHEC — {sum(r)}/5.")
    return 0 if all(r) else 1


if __name__ == "__main__":
    raise SystemExit(main())
