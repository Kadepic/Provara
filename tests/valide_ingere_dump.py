"""INGERE_DUMP — streaming + déduplication du dump complet, VÉRIFIÉ sur un mini-dump local (reproductible, sans réseau).
DÉDUP : 1ʳᵉ occurrence par mot, mais un NOM remplace une non-nom déjà vue (taxonomie = noms d'abord).
FORMAT/2-PASSES : réutilise convertit_kaikki (genus + adjectif-tête). ROBUSTE : lignes corrompues ignorées."""
from __future__ import annotations
import tempfile
from pathlib import Path
from ingere_dump import ingere_dump

# Mini-dump local au format kaikki (vrais schémas), avec doublons pour tester la déduplication.
LIGNES = [
    '{"word":"porte","pos":"verb","senses":[{"glosses":["Troisième personne de porter."]}]}',   # verbe d'abord…
    '{"word":"porte","pos":"noun","tags":["feminine"],"senses":[{"glosses":["Ouverture aménagée dans un mur."]}]}',  # …le NOM gagne
    '{"word":"chat","pos":"noun","tags":["masculine"],"senses":[{"glosses":["Mammifère carnivore félin domestiqué."]}]}',
    '{"word":"chat","pos":"noun","senses":[{"glosses":["Autre sens, ignoré (1re occ. gardée)."]}]}',  # 2e chat ignoré
    '{"word":"grand","pos":"adj","senses":[{"glosses":["De dimensions importantes."]}]}',
    '{"word":"lion","pos":"noun","tags":["masculine"],"senses":[{"glosses":["Grand mammifère carnivore."]}]}',  # 2e passe: saute grand
    '{"word":"chaud","pos":"noun","senses":[{"glosses":["Sensation de chaleur."]}]}',                # nom (gardé), sans antonyme
    '{"word":"chaud","pos":"adj","senses":[{"glosses":["À température élevée."]}],"antonyms":[{"word":"froid"}]}',  # adj : antonyme UNIONÉ
    'ligne corrompue pas json',
]


def _check(nom, c):
    print(f"  [{'OK ' if c else 'RATÉ'}] {nom}")
    return c


def main() -> int:
    r = []
    with tempfile.TemporaryDirectory() as d:
        chemin = Path(d) / "mini.jsonl"
        chemin.write_text("\n".join(LIGNES), encoding="utf-8")
        lex = ingere_dump(str(chemin))

    r.append(_check("DÉDUP : le NOM `porte` remplace la forme verbale (taxonomie priorise les noms)",
                    lex.get("porte", {}).get("classe") == "nom"))
    r.append(_check("FORMAT : chat -> {nom, masculin, hyper=mammifère}",
                    lex.get("chat", {}).get("classe") == "nom" and lex["chat"]["genre"] == "masculin"
                    and lex["chat"]["hyper"] == "mammifère"))
    r.append(_check("2ᵉ PASSE : lion -> mammifère (l'adjectif-tête `grand` est sauté)",
                    lex.get("lion", {}).get("hyper") == "mammifère"))
    r.append(_check("UNION syn/ant : `chaud` gardé comme NOM mais antonyme `froid` (du sens adj) unioné",
                    lex.get("chaud", {}).get("classe") == "nom" and lex["chaud"]["ant"] == ["froid"]))
    r.append(_check("ROBUSTE : ligne corrompue ignorée, 5 entrées (porte, chat, grand, lion, chaud)",
                    "chat" in lex and len(lex) == 5))

    print()
    print(f"INGERE_DUMP VALIDÉ — {len(r)}/{len(r)}." if all(r) else f"ÉCHEC — {sum(r)}/{len(r)}.")
    return 0 if all(r) else 1


if __name__ == "__main__":
    raise SystemExit(main())
