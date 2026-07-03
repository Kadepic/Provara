"""
EXPORTE_DATASET — le maillon APPRENDRE, sans GPU (2026-06-17, « rendre l'IA prête à apprendre »).

Le STORE accumule des paires (prompt -> solution) VÉRIFIÉES par le juge (rien de faux n'y entre). Cette brique le
transforme en JEU D'ENTRAÎNEMENT de fine-tuning, propre et standard. Le jour où un GPU est dispo, on entraîne sur
ce fichier — il ne manque QUE le GPU. Tout y est correct par construction (le store refuse le non-vérifié) et
dédupliqué.

Formats :
  - "chat"       : {"messages":[{"role":"user",...},{"role":"assistant", "content": solution}]}  (modèles de chat)
  - "completion" : {"prompt": ..., "completion": ...}                                              (modèles complétion)
"""

from __future__ import annotations

import json
from pathlib import Path

from store import Store

INSTRUCTION = "Écris une fonction Python qui satisfait cette signature, en code correct et général :"


def _exemple(prompt: str, solution: str, format: str) -> dict:
    if format == "completion":
        return {"prompt": f"{INSTRUCTION}\n{prompt}\n", "completion": " " + solution.strip()}
    # chat (défaut)
    return {"messages": [
        {"role": "user", "content": f"{INSTRUCTION}\n{prompt}"},
        {"role": "assistant", "content": solution.strip()},
    ]}


def exporte(chemin_store, chemin_sortie, format: str = "chat") -> dict:
    """Store -> JSONL de fine-tuning. Renvoie un résumé (n exemples, n dédupliqués, longueurs)."""
    store = Store(chemin_store)
    vus = set()
    n, doublons, total_chars = 0, 0, 0
    Path(chemin_sortie).parent.mkdir(parents=True, exist_ok=True)
    with open(chemin_sortie, "w", encoding="utf-8") as f:
        for s in store:
            cle = (s.prompt.strip(), s.solution.strip())
            if cle in vus:                       # dédup supplémentaire (au cas où) (prompt, solution)
                doublons += 1
                continue
            vus.add(cle)
            ex = _exemple(s.prompt, s.solution, format)
            f.write(json.dumps(ex, ensure_ascii=False) + "\n")
            n += 1
            total_chars += len(s.solution)
    return {"exemples": n, "doublons_evites": doublons, "format": format,
            "chemin": str(chemin_sortie), "chars_moyen": (total_chars // n) if n else 0}


def resume(chemin_sortie) -> dict:
    """Relit le JSONL exporté et vérifie qu'il est BIEN FORMÉ (chaque ligne = JSON valide avec prompt+solution
    non vides). Renvoie {lignes, valides, mal_formees, taches_distinctes-approx}."""
    lignes = valides = mal = 0
    solutions = set()
    with open(chemin_sortie, encoding="utf-8") as f:
        for ligne in f:
            ligne = ligne.strip()
            if not ligne:
                continue
            lignes += 1
            try:
                ex = json.loads(ligne)
                if "messages" in ex:
                    u = ex["messages"][0]["content"]
                    a = ex["messages"][1]["content"]
                else:
                    u, a = ex["prompt"], ex["completion"]
                if u.strip() and a.strip() and "def " in a:
                    valides += 1
                    solutions.add(a.strip())
                else:
                    mal += 1
            except Exception:
                mal += 1
    return {"lignes": lignes, "valides": valides, "mal_formees": mal, "solutions_distinctes": len(solutions)}


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        print("usage: python3 exporte_dataset.py <store.jsonl> <sortie.jsonl> [chat|completion]")
        raise SystemExit(2)
    fmt = sys.argv[3] if len(sys.argv) > 3 else "chat"
    r = exporte(sys.argv[1], sys.argv[2], fmt)
    print("Export :", r)
    print("Vérif  :", resume(sys.argv[2]))
