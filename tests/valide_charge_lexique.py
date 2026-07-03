"""CHARGE_LEXIQUE — ingesteur de lexique scalable (voie Wiktionnaire) — la cohérence est vérifiée, pas supposée.
ROUND-TRIP : ecris(seed) puis charge -> identique. COHÉRENCE : la graine certifiée est acyclique, sans champ manquant.
CYCLE : un dump avec boucle is-a est DÉTECTÉ. ÉCHELLE : fabrique_semantique sur un lexique chargé produit des paires
vérifiées (dont des transitives held-out sur les nouveaux domaines)."""
from __future__ import annotations
import tempfile
from pathlib import Path

import lexique_fr as L
from charge_lexique import charge, coherence, ecris
from fabrique_semantique import construit_paires, _verifie


def _check(nom, c):
    print(f"  [{'OK ' if c else 'RATÉ'}] {nom}")
    return c


def main() -> int:
    r = []
    with tempfile.TemporaryDirectory() as d:
        chemin = Path(d) / "lexique.jsonl"
        n = ecris(L.LEXIQUE, chemin)
        relu = charge(chemin)
        r.append(_check(f"ROUND-TRIP : {n} entrées écrites puis relues à l'identique", relu == L.LEXIQUE))

        co = coherence(relu)
        r.append(_check(f"COHÉRENCE : graine certifiée acyclique={co['acyclique']}, "
                        f"champs_manquants={co['champs_manquants']}",
                        co["acyclique"] and not co["champs_manquants"]))

        # CYCLE : on fabrique un dump fautif (a est une sorte de b, b une sorte de a) -> doit être détecté.
        mauvais = {"a": {"classe": "nom", "genre": "masculin", "definition": "x", "hyper": "b", "syn": [], "ant": []},
                   "b": {"classe": "nom", "genre": "masculin", "definition": "y", "hyper": "a", "syn": [], "ant": []}}
        r.append(_check("CYCLE : une boucle is-a (a->b->a) est détectée (acyclique=False)",
                        not coherence(mauvais)["acyclique"]))

        # ÉCHELLE : le lexique relu (élargi) nourrit la fabrique ; transitive held-out sur un NOUVEAU domaine.
        paires = construit_paires(relu)
        isa = {(i, rep) for i, rep in [(p[1], p[2]) for p in paires if p[0] == "est_une_sorte_de"]}
        e_isa = L.edges_isa(relu)
        lion_animal = _verifie("est_un", e_isa, "lion", "animal", True)   # lion->félin->mammifère->animal
        rose_plante = _verifie("est_un", e_isa, "rose", "plante", True)   # rose->fleur->plante
        r.append(_check(f"ÉCHELLE : {len(paires)} paires sémantiques ; transitives held-out nouveaux domaines "
                        f"(lion→animal={lion_animal}, rose→plante={rose_plante})",
                        len(paires) > 80 and lion_animal and rose_plante))

    print()
    print(f"CHARGE_LEXIQUE VALIDÉE — {sum(r)}/{len(r)}." if all(r) else f"ÉCHEC — {sum(r)}/{len(r)}.")
    return 0 if all(r) else 1


if __name__ == "__main__":
    raise SystemExit(main())
