"""
INGERE_KAIKKI — CLI (réseau/fichier) : dump kaikki.org/frwiktionary -> lexique noyau vérifié (§6.2, 2026-06-18).

Tout l'aval (convertir -> contrôler la cohérence -> exporter au format charge_lexique) est ici ; la logique pure
de conversion vit dans `convertit_kaikki` (testée hors réseau par valide_convertit_kaikki). Deux modes :

  python3 ingere_kaikki.py dump.jsonl                      # convertit un dump kaikki local (passage à l'échelle)
  python3 ingere_kaikki.py --mots chat,lion,ville,capitale # télécharge ces entrées depuis kaikki (réseau), démo

Sortie : exporte datasets/lexique_kaikki.jsonl, imprime le rapport de cohérence + le graphe is-a auto-construit.
"""
from __future__ import annotations

import sys
import urllib.parse
import urllib.request

from charge_lexique import coherence, ecris
from convertit_kaikki import aretes_isa, convertit

BASE = "https://kaikki.org/frwiktionary/Fran%C3%A7ais/meaning"


def _url(mot: str) -> str:
    p1 = urllib.parse.quote(mot[:1])
    p2 = urllib.parse.quote(mot[:2])
    return f"{BASE}/{p1}/{p2}/{urllib.parse.quote(mot)}.jsonl"


def telecharge(mots, timeout=20):
    """Récupère les lignes JSONL kaikki pour une liste de mots (réseau). Échecs silencieusement ignorés."""
    lignes = []
    for mot in mots:
        try:
            with urllib.request.urlopen(_url(mot), timeout=timeout) as r:
                texte = r.read().decode("utf-8")
            premiere = next((ln for ln in texte.splitlines() if ln.strip()), None)
            if premiere:
                lignes.append(premiere)
        except Exception as e:  # réseau/404 : on continue, jamais d'invention
            print(f"  ! {mot} : {type(e).__name__}", file=sys.stderr)
    return lignes


def ingere(lignes, sortie="datasets/lexique_kaikki.jsonl"):
    """Convertit des lignes JSONL kaikki -> lexique, contrôle, exporte. Renvoie (lex, rapport)."""
    lex = convertit(lignes)
    rapport = coherence(lex)
    if lex:
        ecris(lex, sortie)
    return lex, rapport


def main(argv) -> int:
    if not argv:
        print(__doc__)
        return 1
    if argv[0] == "--mots":
        mots = [m.strip() for m in argv[1].split(",")] if len(argv) > 1 else []
        lignes = telecharge(mots)
    else:
        with open(argv[0], encoding="utf-8") as f:
            lignes = f.readlines()

    lex, rapport = ingere(lignes)
    print(f"Lexique converti : {rapport['entrees']} entrées | acyclique={rapport['acyclique']} | "
          f"orphelins(frontière)={len(rapport['hyperonymes_orphelins'])}")
    print("\nGraphe is-a AUTO-CONSTRUIT (mot --est-une-sorte-de--> genus de la définition) :")
    for a, b in aretes_isa(lex):
        print(f"    {a} --> {b}")
    if rapport["entrees"]:
        print(f"\n-> Exporté vers datasets/lexique_kaikki.jsonl (prêt pour fabrique_semantique). "
              f"Le mur lexical recule par la DONNÉE, pas par la règle.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
