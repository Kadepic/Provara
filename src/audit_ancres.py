"""
AUDIT DES ANCRES — quelles relations du lecteur ont une assertion de vérité EXTERNE (non circulaire) ?

Le store (datasets/lecteur/*.jsonl) contient des faits ingérés. La SOUNDNESS FAUX=0 exige que les plus grosses
tables soient testées par un validateur portant des ANCRES EXTERNES (valeurs de référence codées à la main,
vérifiées indépendamment de la source d'ingestion — ex. « Paris capitale de la France », « fer = numéro 26 »).
Ce module DIAGNOSTIQUE la couverture : quelles relations sont référencées par un validateur, lesquelles ne le
sont PAS (candidates prioritaires à ancrer, par volume de faits décroissant).

MÉTHODE (sur-approximation SOUND de la couverture) : une relation est dite « référencée » si son nom exact apparaît
(délimité) dans le source d'un `valide_*.py`. C'est un PROXY : un validateur peut mentionner une relation sans
l'ancrer vraiment -> le vrai taux d'ancrage est ≤ celui-ci. Mais l'inverse est FIABLE : une relation JAMAIS
mentionnée n'est certainement PAS ancrée. Donc la liste des NON-référencées est un sous-ensemble sûr des
non-ancrées : un point de départ sans faux « non-ancré ». Read-only, souverain, stdlib pur.

Usage : python3 audit_ancres.py            (rapport) ; importable : audit() -> dict.
"""
from __future__ import annotations

import os
import re

# RACINE = le REPO (ce fichier vit dans src/) — l'ancien dirname(__file__) cherchait src/datasets/lecteur
# (inexistant : inventaire vide/partiel, cause du dossier « 6/22 » de l'audit 2026-07-09). Le store audité
# honore LECTEUR_DATASETS_DIR (la base réelle) avant le chemin embarqué.
_ICI = (os.environ.get("VERAX_ROOT") or os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_LECT = os.environ.get("LECTEUR_DATASETS_DIR") or os.path.join(_ICI, "datasets", "lecteur")


def _relations_et_tailles() -> dict:
    """{relation: nb_faits} en comptant les lignes de chaque .jsonl moins l'en-tête (_relation). Comptage rapide
    par blocs (newlines), sans parser le JSON."""
    out = {}
    if not os.path.isdir(_LECT):
        return out
    for f in os.listdir(_LECT):
        if not f.endswith(".jsonl"):
            continue
        rel = f[:-6]
        chemin = os.path.join(_LECT, f)
        n = 0
        try:
            with open(chemin, "rb") as fh:
                while True:
                    bloc = fh.read(1 << 20)
                    if not bloc:
                        break
                    n += bloc.count(b"\n")
        except OSError:
            continue
        out[rel] = max(0, n - 1)                    # -1 = ligne d'en-tête self-describing
    return out


def _relations_referencees(relations) -> set:
    """Sous-ensemble des `relations` dont le nom EXACT (délimité par des non-alphanum) apparaît dans un valide_*.py.
    Un seul balayage de chaque validateur ; matching par regex de mots pour éviter les sous-chaînes accidentelles."""
    if not relations:
        return set()
    # motif unique : (rel1|rel2|…) entre délimiteurs non-[a-z0-9_]. Les noms de relation sont en snake_case.
    motif = re.compile(r"(?<![a-z0-9_])(" + "|".join(re.escape(r) for r in sorted(relations, key=len, reverse=True))
                       + r")(?![a-z0-9_])")
    refs = set()
    # ⚠ cause racine du « classe mal » (audit 2026-07-09) : on listait tests/ mais on OUVRAIT depuis la racine
    # (_ICI/f) -> aucun validateur jamais lu (OSError silencieux), tout partait en « non référencé ».
    dossier_tests = os.path.join(_ICI, "tests")
    if not os.path.isdir(dossier_tests):
        return set()
    for f in os.listdir(dossier_tests):
        if not (f.startswith("valide_") and f.endswith(".py")):
            continue
        try:
            with open(os.path.join(dossier_tests, f), encoding="utf-8") as fh:
                txt = fh.read()
        except OSError:
            continue
        for m in motif.finditer(txt):
            refs.add(m.group(1))
    return refs


def audit(details: bool = False) -> dict:
    """Rapport de couverture d'ancrage (UN seul scan du store). Renvoie {total_relations, total_faits, referencees,
    non_referencees, faits_non_references, top_non_references:[(rel, n), …]}. `details=True` ajoute `tailles` (dict
    relation->n) et `referencees_set` (set) pour éviter aux appelants de re-scanner (coûteux : ~4 Go d'octets)."""
    tailles = _relations_et_tailles()
    refs = _relations_referencees(set(tailles))
    non_ref = {r: n for r, n in tailles.items() if r not in refs}
    top = sorted(non_ref.items(), key=lambda kv: -kv[1])
    out = {
        "total_relations": len(tailles),
        "total_faits": sum(tailles.values()),
        "referencees": len(refs),
        "non_referencees": len(non_ref),
        "faits_non_references": sum(non_ref.values()),
        "top_non_references": top,
    }
    if details:
        out["tailles"] = tailles
        out["referencees_set"] = refs
    return out


if __name__ == "__main__":
    r = audit()
    print(f"=== AUDIT DES ANCRES ({r['total_relations']} relations / {r['total_faits']:,} faits) ===")
    print(f"  référencées par un validateur : {r['referencees']} "
          f"({100 * r['referencees'] / max(1, r['total_relations']):.0f} %)")
    print(f"  NON référencées               : {r['non_referencees']} "
          f"({r['faits_non_references']:,} faits non couverts par une ancre)")
    print(f"\n  Top 30 des plus grosses tables NON référencées (candidates prioritaires à ancrer) :")
    for rel, n in r["top_non_references"][:30]:
        print(f"    {n:>9,}  {rel}")
