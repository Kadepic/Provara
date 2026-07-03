"""ETEND_SAVOIR — l'IA étend SEULE sa taxonomie par fermeture transitive (fetcher INJECTÉ, hors réseau, reproductible).
CLOSURE : d'une seule graine `chat`, découvre mammifère puis animal via la frontière. CHAÎNE : chat->mammifère->animal.
VIVANT : relation-lexicale raisonne en profondeur sur le graphe crawlé. BORNÉ : termine sur frontière épuisée."""
from __future__ import annotations
from charge_lexique import coherence
from convertit_kaikki import aretes_isa
from etend_savoir import acyclise, chaine, etend, frontiere, raisonneur

# Faux « dictionnaire » kaikki (enregistrements réalistes), pour tester la LOGIQUE de fermeture sans réseau.
CORPUS = {
    "chat": '{"word":"chat","pos":"noun","tags":["masculine"],'
            '"senses":[{"glosses":["Mammifère carnivore félin de taille moyenne, domestiqué."]}]}',
    "mammifère": '{"word":"mammifère","pos":"noun",'
                 '"senses":[{"glosses":["Animal qui porte des mamelles pour allaiter ses petits."]}]}',
    "animal": '{"word":"animal","pos":"noun","tags":["masculine"],'
              '"senses":[{"glosses":["Métazoaire ; être organisé, doué de sensibilité et de mouvement."]}]}',
}


def faux_telecharge(mots):
    return [CORPUS[m] for m in mots if m in CORPUS]


def _check(nom, c):
    print(f"  [{'OK ' if c else 'RATÉ'}] {nom}")
    return c


def main() -> int:
    lex, trace = etend(["chat"], rounds=5, max_mots=50, telecharge_fn=faux_telecharge)
    edges = aretes_isa(lex)
    r = []

    r.append(_check(f"CLOSURE : d'une seule graine `chat`, auto-découvre mammifère + animal (entrées 1→{len(lex)}) ; trace={trace}",
                    "mammifère" in lex and "animal" in lex and len(lex) == 3))

    ch = chaine("chat", edges)
    r.append(_check(f"CHAÎNE : {' -> '.join(ch)}", ch[:3] == ["chat", "mammifère", "animal"]))

    r.append(_check(f"BORNÉ : frontière finale = {frontiere(lex)} (métazoaire orphelin -> termine)",
                    frontiere(lex) == ["métazoaire"]))

    eu = raisonneur(edges)
    vivant = (eu("chat", "animal") is True and eu("chat", "métazoaire") is True
              and eu("animal", "chat") is False)
    r.append(_check("VIVANT : relation-lexicale prouve chat->animal (2 niveaux) + direction (animal !-> chat)", vivant))

    # DAG : de vraies définitions circulaires existent -> acyclise garantit une taxonomie sans cycle.
    def _e(h):
        return {"classe": "nom", "genre": None, "definition": "", "hyper": h, "syn": [], "ant": []}
    dag, coupes = acyclise({"a": _e("b"), "b": _e("a")})
    r.append(_check(f"DAG : cycle a<->b cassé ({len(coupes)} arête coupée) -> acyclique",
                    coherence(dag)["acyclique"] is True and len(coupes) == 1))

    print()
    print(f"ETEND_SAVOIR VALIDÉ — {len(r)}/{len(r)}." if all(r) else f"ÉCHEC — {sum(r)}/{len(r)}.")
    return 0 if all(r) else 1


if __name__ == "__main__":
    raise SystemExit(main())
