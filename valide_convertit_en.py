"""CONVERTIT_KAIKKI multilingue — le MÉCANISME genus est agnostique : seuls les jeux de mots-outils changent.
Vérifie le chemin ANGLAIS (langue='en', hyperonymes structurés) sur de vrais schémas English Wiktionary, sans réseau.
Prouve que le même convertisseur + les mêmes briques (cf. demo_anglais) raisonnent en anglais."""
from __future__ import annotations
from convertit_kaikki import aretes_isa, convertit, genus

KAIKKI_EN = [
    '{"word":"cat","pos":"noun","senses":[{"glosses":["A small domesticated carnivorous mammal."]}],'
    '"hypernyms":[{"word":"animal"},{"word":"feline"}],"synonyms":[{"word":"feline"}]}',
    '{"word":"dog","pos":"noun","senses":[{"glosses":["A mammal of the family Canidae."]}],'
    '"hypernyms":[{"word":"mammal"}]}',
    '{"word":"guitar","pos":"noun","senses":[{"glosses":["A stringed musical instrument."]}],'
    '"hypernyms":[{"word":"chordophone"}]}',
    '{"word":"hello","pos":"intj","senses":[{"glosses":["A greeting."]}]}',     # pos non mappé -> ignoré
]


def _check(nom, c):
    print(f"  [{'OK ' if c else 'RATÉ'}] {nom}")
    return c


def main() -> int:
    r = []

    # Règles genus EN par RÈGLE (pas liste lexicale) : relatif « Which… » -> None ; méta « A kind of Y » -> Y.
    r.append(_check("genus EN : « Which has a backbone » -> None (relatif), « A kind of fruit » -> fruit (méta)",
                    genus("which has a backbone", langue="en") is None
                    and genus("a kind of fruit", langue="en") == "fruit"))

    lex = convertit(KAIKKI_EN, langue="en", hyper_prioritaire=True)
    r.append(_check("conversion EN : cat->animal, dog->mammal, guitar->chordophone (hyperonymes structurés)",
                    lex.get("cat", {}).get("hyper") == "animal" and lex.get("dog", {}).get("hyper") == "mammal"
                    and lex.get("guitar", {}).get("hyper") == "chordophone"))

    r.append(_check("honnête EN : 'hello' (intj) ignoré ; 3 entrées (cat, dog, guitar)",
                    "hello" not in lex and len(lex) == 3))

    r.append(_check("arêtes is-a EN bien formées (mot, hyper)",
                    sorted(aretes_isa(lex)) == [("cat", "animal"), ("dog", "mammal"), ("guitar", "chordophone")]))

    print()
    print(f"CONVERTIT_EN VALIDÉ — {len(r)}/{len(r)}." if all(r) else f"ÉCHEC — {sum(r)}/{len(r)}.")
    return 0 if all(r) else 1


if __name__ == "__main__":
    raise SystemExit(main())
