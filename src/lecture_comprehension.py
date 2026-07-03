"""
LECTURE & COMPRÉHENSION — l'IA lit des phrases-faits et répond à des questions par LOGIQUE (2026-06-18, capstone nuit).

Le sommet du mandat : « comprendre les phrases […] avec une logique derrière ». L'IA reçoit des FAITS en français
(« le chat est un félin », « le chat mange la souris »), les COMPREND (parse sujet/relation/objet via les classes
officielles), et RÉPOND à des questions :

  - « X est-il un Z ? »  -> déduction transitive 3 valeurs (oui / non / inconnu), via l'étage `inference` du moteur
                            ASSEMBLÉ (intégré, pas isolé).
  - « qui <verbe> Y ? »  -> retrouve le SUJET du fait correspondant (compréhension SVO).

Tout est vérifiable et honnête : ce qui n'est pas dérivable -> « inconnu » (jamais d'invention).
"""
from __future__ import annotations

import tempfile
from pathlib import Path

import lexique_fr as L
from comprehension import Predicteur
from compounding import resoudre
from generateur import GenerateurOrchestre, TYPES_RICHES
from juge import Limites
from store import Store
from taches import Tache

LIM = Limites(temps_s=3, cpu_s=2)

CLASSES = {m: d["classe"] for m, d in L.LEXIQUE.items()}
CLASSES.update({"le": "determinant", "la": "determinant", "un": "determinant", "une": "determinant",
                "souris": "nom", "fromage": "nom", "est": "copule",
                "mange": "verbe", "voit": "verbe", "dort": "verbe", "chasse": "verbe"})


def _noms(toks):
    return [t for t in toks if CLASSES.get(t) == "nom"]


def _terme(toks):
    """Le terme principal d'un fragment : nom connu en priorité, sinon dernier mot hors déterminant (catégorie
    possiblement hors lexique, ex. « reptile »)."""
    noms = _noms(toks)
    if noms:
        return noms[-1]
    cand = [t for t in toks if CLASSES.get(t) != "determinant"]
    return cand[-1] if cand else (toks[-1] if toks else "")


def _parse(phrase, est_neg, enleve):
    """Comprend une phrase-fait, NÉGATION comprise (« X n'est pas un Y » -> isa négatif).
    ('isa', sujet, relation, objet) avec relation ∈ {est, nest_pas} ; ('svo', sujet, verbe, objet, negatif) sinon."""
    neg = est_neg(phrase)
    noyau = enleve(phrase) if neg else phrase
    toks = noyau.split()
    if "est" in toks:
        i = toks.index("est")
        return ("isa", _terme(toks[:i]), "nest_pas" if neg else "est", _terme(toks[i + 1:]))
    cls = [CLASSES.get(t) for t in toks]
    vi = cls.index("verbe")
    return ("svo", _terme(toks[:vi]), toks[vi], _terme(toks[vi + 1:]), neg)


def _moteur():
    """Récupère déduction + négation depuis le MÊME moteur assemblé (étages `inference` + `negation`)."""
    with tempfile.TemporaryDirectory() as d:
        st = Store(Path(d) / "s.jsonl")
        orch = GenerateurOrchestre(st, predicteur=Predicteur(st, types=TYPES_RICHES),
                                   inference=True, negation=True)

        def _res(point, sig, appel, attendu):
            t = Tache(id=f"lc/{point}", point_entree=point, prompt=f'def {point}({sig}):\n    """..."""',
                      tests=f"def check(c):\n    assert c({appel}) == {attendu!r}\ncheck({point})", tests_held_out="")
            e, _, code, _ = resoudre(orch, t, LIM)
            ns: dict = {}
            exec(code, ns)
            return e, ns[point]

        e1, deduit = _res("deduit", "p, x, y", "[('a','est','b'),('b','est','c')], 'a', 'c'", "oui")
        _, est_neg = _res("est_negative", "phrase", "'le chat ne dort pas'", True)
        _, enleve = _res("enleve_negation", "phrase", "'le chat ne dort pas'", "le chat dort")
        return e1, deduit, est_neg, enleve


class Lecteur:
    """Lit des faits (affirmatifs ET négatifs), répond à des questions. Déduction + négation via le moteur assemblé."""

    def __init__(self, faits):
        self._etage, self._deduit, self._est_neg, self._enleve = _moteur()
        self.premisses, self.svo = [], []
        for f in faits:
            p = _parse(f, self._est_neg, self._enleve)
            if p[0] == "isa":
                self.premisses.append((p[1], p[2], p[3]))
            else:
                self.svo.append((p[1], p[2], p[3], p[4]))

    def repond(self, question):
        toks = question.rstrip("?").replace("-", " ").split()
        cop = [k for k, t in enumerate(toks) if t == "est"]   # « est », « est il », « est elle »
        if cop:                                 # « X est-il un Z ? » (Z peut être hors lexique -> inconnu honnête)
            i = cop[0]
            avant = toks[:i]
            apres = [t for t in toks[i + 1:] if CLASSES.get(t) != "determinant" and t not in ("il", "elle")]
            sujet = (_noms(avant) or avant)[-1]
            objet = apres[-1] if apres else ""
            return self._deduit(self.premisses, sujet, objet)
        if toks and toks[0] == "qui":           # « qui <verbe> Y ? »
            cls = [CLASSES.get(t) for t in toks]
            vi = cls.index("verbe")
            verbe, objet = toks[vi], _noms(toks[vi + 1:])[-1]
            for s, v, o, neg in self.svo:
                if v == verbe and o == objet and not neg:   # un fait NIÉ ne répond pas « qui fait l'action »
                    return s
            return "inconnu"
        return "inconnu"


FAITS = ["le chat est un félin", "le félin est un mammifère", "le mammifère est un animal",
         "le félin n'est pas un reptile", "le chat mange la souris", "le chien ne mange pas la souris"]


if __name__ == "__main__":
    lec = Lecteur(FAITS)
    print("Faits lus :")
    for f in FAITS:
        print(f"  - {f}")
    print(f"\n(déduction + négation via l'étage assemblé : {lec._etage})\n")
    for q in ["le chat est-il un mammifère ?", "le chat est-il un animal ?", "le chat est-il un reptile ?",
              "le chat est-il un oiseau ?", "qui mange la souris ?"]:
        print(f"  Q: {q:<34} R: {lec.repond(q)}")
