"""CONVERTIT_KAIKKI — pont dump Wiktionnaire -> lexique noyau, VÉRIFIÉ sur de VRAIS enregistrements kaikki (en ligne,
sans réseau, reproductible). Prouve §6.2 : la DONNÉE franchit le mur lexical par le genus des définitions françaises.
  FORMAT : conversion exacte vers {classe, genre, hyper, …}.   COHÉRENCE : graphe is-a auto-construit ACYCLIQUE.
  VIVANT : relation-lexicale RAISONNE en transitif sur la donnée réelle (chat -> animal).   HONNÊTE : pos non mappé ignoré."""
from __future__ import annotations
import tempfile
from pathlib import Path
from comprehension import Predicteur
from compounding import resoudre
from convertit_kaikki import convertit, aretes_isa
from charge_lexique import coherence
from generateur import GenerateurOrchestre, TYPES_RICHES
from juge import Limites
from store import Store
from taches import Tache

LIM = Limites(temps_s=3, cpu_s=2)

# Enregistrements RÉELS de kaikki.org/frwiktionary (récupérés le 2026-06-18), réduits aux champs utiles.
KAIKKI = [
    '{"word":"chat","pos":"noun","lang":"Français","tags":["masculine"],"sounds":[{"ipa":"/ʃa/"}],'
    '"senses":[{"glosses":["Mammifère carnivore félin de taille moyenne, au museau court et arrondi, domestiqué."]}],'
    '"hypernyms":[{"word":"félidés"}],"synonyms":[{"word":"matou"},{"word":"minet"}]}',
    '{"word":"mammifère","pos":"noun","tags":["feminine","masculine"],'
    '"senses":[{"glosses":["Animal qui porte des mamelles pour allaiter ses petits."]}]}',
    '{"word":"animal","pos":"noun","tags":["masculine"],'
    '"senses":[{"glosses":["Métazoaire ; être organisé, doué de sensibilité et de mouvement."]}]}',
    '{"word":"ville","pos":"noun","tags":["feminine"],'
    '"senses":[{"glosses":["Assemblage ordonné d\'un nombre assez considérable de maisons disposées en rues."]}]}',
    '{"word":"capitale","pos":"noun","tags":["feminine"],'
    '"senses":[{"glosses":["Ville où siègent le gouvernement et le pouvoir législatif de l\'État."]}]}',
    # lion + grand : la définition « Grand félin… » commence par un ADJECTIF -> la 2ᵉ passe le saute -> genus = félin.
    '{"word":"lion","pos":"noun","tags":["masculine"],'
    '"senses":[{"glosses":["Grand félin carnivore, (Panthera leo), autrefois répandu des Balkans au sous-continent."]}]}',
    '{"word":"grand","pos":"adj","senses":[{"glosses":["De dimensions importantes."]}]}',
    '{"word":"bonjour","pos":"intj","senses":[{"glosses":["Formule de salutation."]}]}',  # pos non mappé -> ignoré
    'ligne corrompue { pas du json',                                                       # robustesse -> ignorée
]


def _check(nom, c):
    print(f"  [{'OK ' if c else 'RATÉ'}] {nom}")
    return c


def _est_un(edges):
    """Récupère la fonction est_un de l'orchestrateur VIVANT (relation-lexicale) et l'applique au graphe converti."""
    st = Store(Path(tempfile.mkdtemp()) / "s.jsonl")
    orch = GenerateurOrchestre(st, predicteur=Predicteur(st, types=TYPES_RICHES), relation_lexicale=True)
    t = Tache(id="kk/est_un", point_entree="est_un", prompt='def est_un(e,x,y):\n    """..."""',
              tests="def check(c):\n    assert c([('a','b'),('b','c')],'a','c') == True\ncheck(est_un)", tests_held_out="")
    _, _, code, _ = resoudre(orch, t, LIM)
    ns: dict = {}
    exec(code, ns)
    f = ns["est_un"]
    return lambda x, y: f(edges, x, y)


def main() -> int:
    lex = convertit(KAIKKI)
    r = []

    fmt = (lex.get("chat", {}).get("classe") == "nom" and lex["chat"]["genre"] == "masculin"
           and lex["chat"]["hyper"] == "mammifère" and "matou" in lex["chat"]["syn"]
           and lex.get("ville", {}).get("genre") == "féminin" and lex.get("capitale", {}).get("hyper") == "ville"
           and lex.get("mammifère", {}).get("genre") is None        # épicène -> None (honnête)
           and lex.get("lion", {}).get("hyper") == "félin")          # 2ᵉ passe : saute l'adjectif-tête « grand »
    r.append(_check("FORMAT : chat->{nom,masculin,mammifère,syn=matou}, ville féminin, épicène->None, lion->félin (2ᵉ passe)", fmt))

    h = coherence(lex)
    r.append(_check(f"COHÉRENCE : {h['entrees']} entrées, graphe is-a ACYCLIQUE ({h['acyclique']}), "
                    f"orphelins frontière={h['hyperonymes_orphelins'][:3]}…",
                    h["entrees"] == 7 and h["acyclique"] is True))

    honnete = "bonjour" not in lex and len(lex) == 7
    r.append(_check("HONNÊTE : entrée pos non mappé (intj) + ligne corrompue ignorées (pas de faux)", honnete))

    eu = _est_un(aretes_isa(lex))
    vivant = (eu("chat", "animal") is True            # transitif chat->mammifère->animal
              and eu("capitale", "ville") is True      # direct (genus de la définition)
              and eu("capitale", "assemblage") is True # transitif capitale->ville->assemblage
              and eu("chat", "ville") is False)         # honnêteté : pas de lien
    r.append(_check("VIVANT : relation-lexicale prouve la transitivité sur la DONNÉE RÉELLE (chat->animal) + honnêteté", vivant))

    print()
    print("CONVERTIT_KAIKKI VALIDÉ — 4/4." if all(r) else f"ÉCHEC — {sum(r)}/4.")
    return 0 if all(r) else 1


if __name__ == "__main__":
    raise SystemExit(main())
