"""
CHARGE_LEXIQUE — ingesteur de lexique scalable (2026-06-18, « étendre le lexique → gros dataset vérifié »).

La voie Wiktionnaire : n'importe quel dump converti au format JSONL
  {"mot":..., "classe":..., "genre":..., "definition":..., "hyper":..., "syn":[...], "ant":[...]}
est INGÉRÉ ici, puis CONTRÔLÉ (cohérence) avant de nourrir `fabrique_semantique`. La graine certifiée
(`lexique_fr.LEXIQUE`) en est un cas particulier : `ecris` l'exporte au format, `charge` le relit (round-trip).

Cohérence vérifiée (pré-requis pour un dataset SAIN) :
  - champs requis présents ;
  - graphe is-a (mot -> hyper) ACYCLIQUE (une boucle « X est une sorte de X » casserait la closure) ;
  - hyperonymes signalés s'ils ne sont pas eux-mêmes des entrées (orphelins -> à compléter).

Convertir le wikitext brut de Wiktionnaire vers ce format JSONL est une étape data séparée ; tout l'aval
(ingestion → cohérence → dataset vérifié) est ici, prêt à passer à l'échelle.
"""
from __future__ import annotations

import json
from pathlib import Path

CHAMPS = ("classe", "genre", "definition", "hyper", "syn", "ant")


def ecris(lex, chemin) -> int:
    """Exporte un lexique (dict mot->attrs) en JSONL. Renvoie le nombre d'entrées écrites."""
    Path(chemin).parent.mkdir(parents=True, exist_ok=True)
    n = 0
    with open(chemin, "w", encoding="utf-8") as f:
        for mot, d in lex.items():
            f.write(json.dumps({"mot": mot, **{k: d.get(k) for k in CHAMPS}}, ensure_ascii=False) + "\n")
            n += 1
    return n


def charge(chemin) -> dict:
    """Lit un dump JSONL -> dict mot->attrs (mêmes clés que lexique_fr.LEXIQUE)."""
    lex = {}
    with open(chemin, encoding="utf-8") as f:
        for ligne in f:
            ligne = ligne.strip()
            if not ligne:
                continue
            e = json.loads(ligne)
            mot = e["mot"]
            lex[mot] = {k: e.get(k, [] if k in ("syn", "ant") else None) for k in CHAMPS}
    return lex


def _cycle(lex):
    """Détecte un cycle dans le graphe is-a (mot -> hyper). Renvoie le 1er cycle trouvé ou None."""
    couleur = {}  # 0=en cours, 1=fini

    def visite(n, pile):
        if couleur.get(n) == 1:
            return None
        if couleur.get(n) == 0:
            return pile[pile.index(n):] + [n]
        couleur[n] = 0
        h = lex.get(n, {}).get("hyper")
        if h:
            c = visite(h, pile + [n])
            if c:
                return c
        couleur[n] = 1
        return None

    for mot in lex:
        c = visite(mot, [])
        if c:
            return c
    return None


def coherence(lex) -> dict:
    """Contrôle de santé du lexique avant fabrication du dataset."""
    champs_manquants = [m for m, d in lex.items() if any(k not in d for k in CHAMPS)]
    cyc = _cycle(lex)
    hypers = {d["hyper"] for d in lex.values() if d.get("hyper")}
    orphelins = sorted(h for h in hypers if h not in lex)
    return {"entrees": len(lex), "acyclique": cyc is None, "cycle": cyc,
            "champs_manquants": champs_manquants, "hyperonymes_orphelins": orphelins}


if __name__ == "__main__":
    import sys
    import lexique_fr as L
    chemin = sys.argv[1] if len(sys.argv) > 1 else "datasets/lexique.jsonl"
    n = ecris(L.LEXIQUE, chemin)
    relu = charge(chemin)
    print(f"Round-trip : {n} entrées écrites, {len(relu)} relues, identiques={relu == L.LEXIQUE}")
    print("Cohérence  :", coherence(relu))
