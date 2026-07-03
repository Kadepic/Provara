"""
RELATIONS_LEXIQUE — exploite syn/ant du lexique converti (§6.2 d, 2026-06-18). convertit_kaikki extrait déjà les
synonymes et antonymes structurés du Wiktionnaire ; ici on les branche sur les briques SENS pour raisonner à
l'échelle du dictionnaire : synonymie (relation-lexicale, non dirigée) et antonymie (antonyme, symétrique).

  aretes_syn(lex) -> arêtes (mot, synonyme) non dirigées      -> est_synonyme : voiture ~ auto ~ bagnole
  paires_ant(lex) -> paires (mot, antonyme) symétriques       -> contraire / sont_contraires : chaud <-> froid

Les raisonneurs sont les MÊMES briques vivantes (orchestrateur), appliquées aux relations issues de la DONNÉE réelle.
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


def aretes_syn(lex: dict):
    """Arêtes de synonymie (mot, synonyme) depuis le lexique converti."""
    return [(m, s) for m, d in lex.items() for s in (d.get("syn") or [])]


def paires_ant(lex: dict):
    """Paires d'antonymie (mot, antonyme) depuis le lexique converti."""
    return [(m, a) for m, d in lex.items() for a in (d.get("ant") or [])]


def _resout(orch, point, sig, tests):
    t = Tache(id=f"rx/{point}", point_entree=point, prompt=f'def {point}({sig}):\n    """..."""',
              tests=tests, tests_held_out="")
    _, _, code, _ = resoudre(orch, t, LIM)
    if code is None:
        return None
    ns: dict = {}
    exec(code, ns)
    return ns[point]


def raisonneurs():
    """Récupère est_synonyme / contraire / sont_contraires des briques VIVANTES (relation-lexicale + antonyme)."""
    st = Store(Path(tempfile.mkdtemp()) / "s.jsonl")
    orch = GenerateurOrchestre(st, predicteur=Predicteur(st, types=TYPES_RICHES),
                               relation_lexicale=True, antonyme=True)
    syn = _resout(orch, "est_synonyme", "aretes, x, y",
                  "def check(c):\n    S=[('a','b'),('b','c')]\n    assert c(S,'a','c') == True\n"
                  "    assert c(S,'c','a') == True\ncheck(est_synonyme)")            # non dirigé
    contr = _resout(orch, "contraire", "antonymes, mot",
                    "def check(c):\n    A=[('grand','petit')]\n    assert c(A,'grand') == 'petit'\n"
                    "    assert c(A,'petit') == 'grand'\ncheck(contraire)")           # symétrique
    sont = _resout(orch, "sont_contraires", "antonymes, x, y",
                   "def check(c):\n    A=[('grand','petit')]\n    assert c(A,'grand','petit') == True\n"
                   "    assert c(A,'grand','grand') == False\ncheck(sont_contraires)")
    return {"est_synonyme": syn, "contraire": contr, "sont_contraires": sont}


if __name__ == "__main__":      # démo LIVE (réseau) : exploite syn/ant du vrai dictionnaire
    import sys
    from convertit_kaikki import convertit
    from ingere_kaikki import telecharge
    mots = [m.strip() for m in (sys.argv[1] if len(sys.argv) > 1 else "voiture,chaud,rapide,joie,grand").split(",")]
    lex = convertit(telecharge(mots))
    syn_e, ant_p, R = aretes_syn(lex), paires_ant(lex), raisonneurs()
    print(f"Depuis kaikki : {len(syn_e)} arêtes de synonymie, {len(ant_p)} paires d'antonymie.\n")
    print("SYNONYMIE (la réalité juge) :")
    for x, y in [("voiture", "bagnole"), ("voiture", "joie")]:
        print(f"  « {x} et {y} sont-ils synonymes ? » -> {'oui' if R['est_synonyme'](syn_e, x, y) else 'non'}")
    print("\nANTONYMIE :")
    for mot in [m for m in ("chaud", "rapide", "grand") if any(a == m for a, _ in ant_p)]:
        print(f"  « contraire de {mot} ? » -> {R['contraire'](ant_p, mot)}")
