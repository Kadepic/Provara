"""RELATIONS_LEXIQUE — syn/ant du dictionnaire branchés sur les briques SENS, VÉRIFIÉ sur de VRAIS enregistrements
kaikki (en ligne, sans réseau, reproductible). Prouve §6.2 d : la DONNÉE nourrit synonymie + antonymie à l'échelle.
  EXTRACTION : aretes_syn / paires_ant depuis le lexique converti.   SYNONYMIE : voiture ~ bagnole (non dirigé).
  ANTONYMIE : chaud <-> froid (symétrique).   HONNÊTE : pas de lien -> False."""
from __future__ import annotations
from convertit_kaikki import convertit
from relations_lexique import aretes_syn, paires_ant, raisonneurs

# Enregistrements RÉELS de kaikki.org/frwiktionary (récupérés le 2026-06-18), réduits aux champs utiles.
KAIKKI = [
    '{"word":"voiture","pos":"noun","tags":["feminine"],"senses":[{"glosses":["Véhicule à roues."]}],'
    '"synonyms":[{"word":"auto"},{"word":"automobile"},{"word":"bagnole"}]}',
    '{"word":"chaud","pos":"adj","senses":[{"glosses":["Qui a une température élevée."]}],'
    '"antonyms":[{"word":"froid"},{"word":"frette"}]}',
    '{"word":"rapide","pos":"adj","senses":[{"glosses":["Qui se déplace vite."]}],'
    '"synonyms":[{"word":"prompt"}],"antonyms":[{"word":"lent"}]}',
    '{"word":"joie","pos":"noun","tags":["feminine"],"senses":[{"glosses":["Sentiment de bonheur."]}],'
    '"synonyms":[{"word":"gaieté"},{"word":"allégresse"}],"antonyms":[{"word":"tristesse"}]}',
]


def _check(nom, c):
    print(f"  [{'OK ' if c else 'RATÉ'}] {nom}")
    return c


def main() -> int:
    lex = convertit(KAIKKI)
    syn_e = aretes_syn(lex)
    ant_p = paires_ant(lex)
    R = raisonneurs()
    r = []

    r.append(_check(f"EXTRACTION : {len(syn_e)} arêtes syn + {len(ant_p)} paires ant depuis la donnée réelle",
                    len(syn_e) >= 6 and len(ant_p) >= 4 and R["est_synonyme"] and R["contraire"] and R["sont_contraires"]))

    es = R["est_synonyme"]
    syno = (es(syn_e, "voiture", "bagnole") is True       # voiture ~ {auto, automobile, bagnole}
            and es(syn_e, "voiture", "auto") is True
            and es(syn_e, "voiture", "joie") is False)     # honnêteté : pas synonymes
    r.append(_check("SYNONYMIE : voiture ~ bagnole / auto (non dirigé), voiture !~ joie", syno))

    sc, co = R["sont_contraires"], R["contraire"]
    anto = (sc(ant_p, "chaud", "froid") is True            # symétrique
            and sc(ant_p, "froid", "chaud") is True
            and co(ant_p, "froid") == "chaud"              # contraire renvoie l'opposé
            and sc(ant_p, "chaud", "joie") is False)        # honnêteté
    r.append(_check("ANTONYMIE : chaud <-> froid (symétrique), contraire(froid)=chaud, chaud !<-> joie", anto))

    print()
    print(f"RELATIONS_LEXIQUE VALIDÉ — {len(r)}/{len(r)}." if all(r) else f"ÉCHEC — {sum(r)}/{len(r)}.")
    return 0 if all(r) else 1


if __name__ == "__main__":
    raise SystemExit(main())
