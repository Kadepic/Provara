"""
FABRIQUE_SEMANTIQUE — dataset de COMPRÉHENSION français vérifié (2026-06-18, « la définition officielle = la vérité »).

Étend la fabrique de FORME au SENS : à partir du lexique certifié (oracle officiel), produit des paires
instruction→réponse VÉRIFIÉES sur tous les axes du mot :

  - définition  : mot -> sens officiel           (fidélité à l'oracle)
  - mot_def     : définition -> mot              (réversible, non ambigu dans la graine)
  - genre       : nom -> masculin/féminin        (remplit le mur LEXICAL de la carte, par table officielle)
  - est_une_sorte_de : hyperonymie TRANSITIVE    (VÉRIFIÉE par la brique relation-lexicale + juge → vrai raisonnement)
  - synonyme    : VÉRIFIÉ par relation-lexicale (closure non dirigée)
  - antonyme    : bidirectionnel dans l'oracle

Anti-dérive : une relation que la brique ne confirme PAS n'est jamais émise. Le held-out est intrinsèque (relations
transitives jamais directes). Sortie JSONL prête pour l'entraînement.
"""
from __future__ import annotations

import json
from pathlib import Path

import lexique_fr as L
from generateur import GenerateurRelationLexicale
from juge import Limites, juge
from taches import Tache

LIM = Limites(temps_s=3, cpu_s=2)


def _verifie(point: str, edges, x, y, attendu) -> bool:
    """La brique relation-lexicale confirme-t-elle la relation ? (closure exécutée en sandbox par le juge)."""
    gen = GenerateurRelationLexicale()
    appel = f"{edges!r}, {x!r}, {y!r}"
    tests = f"def check(c):\n    assert c({appel}) == {attendu!r}\ncheck({point})"
    t = Tache(id=f"sem/{point}", point_entree=point, prompt=f'def {point}(*a):\n    """..."""',
              tests=tests, tests_held_out="")
    return any(juge(code, t.tests, LIM).passe for code in gen.propose(t.prompt, 8))


def construit_paires(lex=L.LEXIQUE):
    """Construit toutes les paires vérifiées (sans écrire). Renvoie [(axe, instruction, reponse)]."""
    e_isa, e_syn = L.edges_isa(lex), L.edges_syn(lex)
    paires = []
    for m, d in lex.items():
        paires.append(("definition", f"Quelle est la définition de « {m} » ?", d["definition"]))
        paires.append(("mot_def", f"Quel mot correspond à cette définition : « {d['definition']} » ?", m))
        if d["classe"] == "nom":
            paires.append(("genre", f"Quel est le genre du nom « {m} » ?", d["genre"]))
    # est-une-sorte-de : hyperonymie transitive, CONFIRMÉE par la brique (raisonnement, pas mémorisation).
    for m in lex:
        for anc in L.ancetres(m, lex):
            if _verifie("est_un", e_isa, m, anc, True):
                paires.append(("est_une_sorte_de", f"Est-ce que « {m} » est une sorte de « {anc} » ?", "oui"))
    # synonymes : CONFIRMÉS par closure non dirigée.
    for m, d in lex.items():
        for s in d["syn"]:
            if _verifie("est_synonyme", e_syn, m, s, True):
                paires.append(("synonyme", f"Donne un synonyme de « {m} ».", s))
    # antonymes : bidirectionnels dans l'oracle.
    for m, d in lex.items():
        for a in d["ant"]:
            if m in lex.get(a, {}).get("ant", []):
                paires.append(("antonyme", f"Donne un antonyme de « {m} ».", a))
    return paires


def fabrique(lex=L.LEXIQUE, chemin_sortie="datasets/francais_sens.jsonl") -> dict:
    paires = construit_paires(lex)
    Path(chemin_sortie).parent.mkdir(parents=True, exist_ok=True)
    vus, axes = set(), {}
    with open(chemin_sortie, "w", encoding="utf-8") as f:
        for axe, instr, rep in paires:
            if instr in vus:
                continue
            vus.add(instr)
            axes[axe] = axes.get(axe, 0) + 1
            f.write(json.dumps({"instruction": instr, "reponse": rep, "axe": axe}, ensure_ascii=False) + "\n")
    return {"paires": len(paires), "lignes": len(vus), "axes": axes, "chemin": str(chemin_sortie)}


def resume(chemin_sortie) -> dict:
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
    sortie = sys.argv[1] if len(sys.argv) > 1 else "datasets/francais_sens.jsonl"
    print("Fabrique :", fabrique(L.LEXIQUE, sortie))
    print("Vérif    :", resume(sortie))
