"""
RÉPONDEUR IA — questions/réponses unifiées, model-free (2026-06-18, « voir ce que l'IA peut faire sans modèle »).

L'IA lit le dictionnaire-oracle + des faits, et répond à une VARIÉTÉ de questions naturelles en ROUTANT chaque
question vers la bonne capacité (toutes bâties model-free, vérifiées) :

  - « qu'est-ce qu'un X ? »                 -> définition (oracle)
  - « quel est le contraire de X ? »        -> antonyme (oracle)
  - « X est-il un Y ? »                     -> inférence (oui/non/inconnu) — brique assemblée
  - « qu'ont en commun X et Y ? »           -> ancêtre commun — brique assemblée
  - « combien de A, B, C sont des Y ? »     -> comptage — brique assemblée
  - « qui <verbe> Y ? »                     -> rôle SVO sur les faits

Démonstration de l'étendue atteinte SANS modèle. Tout est ancré (oracle) ou calculé par une brique vérifiée ;
hors de portée -> « je ne sais pas » (honnête).
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

# verbes d'action (le lexique-oracle ne porte que noms/adjectifs ; les verbes du discours sont listés ici).
VERBES = {"mange", "chasse", "voit", "dort", "mord", "suit", "regarde", "écoute"}
DET_MOTS = {"le", "la", "les", "un", "une", "l'"}


def _fn(orch, point, sig, appel, attendu):
    t = Tache(id=f"q/{point}", point_entree=point, prompt=f'def {point}({sig}):\n    """..."""',
              tests=f"def check(c):\n    assert c({appel}) == {attendu!r}\ncheck({point})", tests_held_out="")
    _, _, code, _ = resoudre(orch, t, LIM)
    ns: dict = {}
    exec(code, ns)
    return ns[point]


class RepondeurIA:
    def __init__(self, faits=()):
        self.lex = L.LEXIQUE
        self.edges = L.edges_isa()
        self.premisses = [(m, "est", h) for m, h in self.edges]
        self.svo, self.location, self.avant, self.events = [], {}, [], set()
        for f in faits:
            toks = f.split()
            if "avant" in toks:                                # « X avant Y » -> relation temporelle
                ai = toks.index("avant")
                g = [t for t in toks[:ai] if t not in DET_MOTS]
                d = [t for t in toks[ai + 1:] if t not in DET_MOTS]
                if g and d:
                    self.avant.append((g[-1], d[-1]))
                    self.events.update({g[-1], d[-1]})
                continue
            if "dans" in toks:                                 # « X est dans Y » -> localisation
                di = toks.index("dans")
                sujet = self._noms(toks[:di])
                if sujet and toks[di + 1:]:
                    self.location[sujet[-1]] = toks[-1]
                continue
            cls = [self._cls(t) for t in toks]
            if "verbe" in cls:
                vi = cls.index("verbe")
                s = self._noms(toks[:vi])
                o = self._noms(toks[vi + 1:])
                if s and o:
                    self.svo.append((s[-1], toks[vi], o[-1]))
        # capacités de RAISONNEMENT depuis le moteur assemblé
        orch = GenerateurOrchestre(Store(Path(tempfile.mkdtemp()) / "s.jsonl"),
                                   predicteur=Predicteur(Store(Path(tempfile.mkdtemp()) / "s2.jsonl"),
                                                         types=TYPES_RICHES),
                                   inference=True, ancetre_commun=True, comptage=True, chemin=True,
                                   relation_lexicale=True, temporel=True)
        self._deduit = _fn(orch, "deduit", "p,x,y", "[('a','est','b'),('b','est','c')],'a','c'", "oui")
        self._est_un = _fn(orch, "est_un", "e,x,y", "[('a','b')],'a','b'", True)
        self._premier = _fn(orch, "premier", "r,e", "[('a','b')],['b','a']", "a")
        self._commun = _fn(orch, "ancetre_commun", "e,x,y",
                           "[('a','b'),('c','b')],'a','c'", "b")
        self._combien = _fn(orch, "combien", "e,m,c",
                            "[('a','b')],['a'],'b'", 1)
        self._chemin = _fn(orch, "chemin", "e,x,y",
                           "[('a','b'),('b','c')],'a','c'", ["a", "b", "c"])

    def _cls(self, t):
        return "verbe" if t in VERBES else self.lex.get(t, {}).get("classe")

    def _noms(self, toks):
        return [t for t in toks if self.lex.get(t, {}).get("classe") == "nom"]

    def _sing(self, w):
        """Singularise une catégorie au pluriel pour la retrouver dans le lexique (animaux -> animal)."""
        if w in self.lex:
            return w
        if w.endswith("aux"):
            return w[:-3] + "al"
        if w.endswith(("s", "x")):
            return w[:-1]
        return w

    def repond(self, q):
        toks = q.lower().rstrip("?").replace("-", " ").replace(",", " ").split()
        S = set(toks)

        if "premier" in S or "d'abord" in S:                   # qu'est-ce qui vient en premier
            return self._premier(self.avant, sorted(self.events)) if self.events else "je ne sais pas"

        if "avant" in S:                                       # X est-il avant Y (ordre temporel transitif)
            evs = [t for t in toks if t in self.events]
            if len(evs) >= 2:
                return "oui" if self._est_un(self.avant, evs[0], evs[1]) else "non"
            return "je ne sais pas"

        if "pourquoi" in S:                                    # pourquoi X est-il un Y -> la chaîne (explication)
            ns = self._noms(toks)
            apres = [self._sing(t) for t in toks if self.lex.get(t, {}).get("classe") != "determinant"]
            if ns:
                ch = self._chemin(self.edges, ns[0], self._sing(ns[-1]) if len(ns) > 1 else (apres[-1] if apres else ""))
                if ch and len(ch) > 1:
                    return "parce que " + " → ".join(ch)
            return "je ne sais pas"

        if "où" in S or "ou" in S:                             # où est X -> localisation
            for t in toks:
                if t in self.location:
                    return self.location[t]
            return "je ne sais pas"

        if "contraire" in S:                                   # contraire de X
            for t in toks:
                ants = self.lex.get(t, {}).get("ant")
                if ants:
                    return ants[0]
            return "je ne sais pas"

        if "définition" in S or "definition" in S or ("qu'est" in q.lower() and "ce" in S):
            for t in toks:                                     # définition de X
                if t in self.lex:
                    return self.lex[t]["definition"]
            return "je ne sais pas"

        if "combien" in S:                                     # combien de A,B,C sont des Y
            cat = self._sing(toks[toks.index("des") + 1]) if "des" in toks else self._noms(toks)[-1]
            membres = [t for t in self._noms(toks) if t != cat]
            return self._combien(self.edges, membres, cat)

        if "commun" in S:                                      # qu'ont en commun X et Y
            ns = self._noms(toks)
            return self._commun(self.edges, ns[0], ns[-1]) if len(ns) >= 2 else "je ne sais pas"

        if "qui" in S and any(self._cls(t) == "verbe" for t in toks):
            cls = [self._cls(t) for t in toks]
            vi = cls.index("verbe")
            objet = self._noms(toks[vi + 1:])
            for s, v, o in self.svo:
                if v == toks[vi] and objet and o == objet[-1]:
                    return s
            return "je ne sais pas"

        if "est" in S:                                         # X est-il un Y
            i = toks.index("est")
            avant = self._noms(toks[:i])
            if not avant:                                      # pas de sujet connu -> hors de portée
                return "je ne sais pas"
            sujet = avant[-1]
            apres = [self._sing(t) for t in toks[i + 1:] if self.lex.get(t, {}).get("classe") != "determinant"
                     and t not in ("il", "elle", "ce")]
            objet = apres[-1] if apres else ""
            return self._deduit(self.premisses, sujet, objet)

        return "je ne sais pas"


FAITS = ["le chat mange la souris", "le chien chasse le chat", "le chat est dans le jardin",
         "le lever avant le repas", "le repas avant le travail"]
DEMO = ["qu'est-ce qu'un chat ?", "quel est le contraire de grand ?", "le chat est-il un mammifère ?",
        "le chat est-il un véhicule ?", "pourquoi le chat est-il un animal ?", "où est le chat ?",
        "qu'ont en commun le chat et le chien ?", "combien de chat, chien et voiture sont des animaux ?",
        "qui mange la souris ?", "qui chasse le chat ?", "qu'est-ce qui vient en premier ?",
        "le lever est-il avant le travail ?", "quelle est la capitale de la France ?"]


if __name__ == "__main__":
    ia = RepondeurIA(FAITS)
    for q in DEMO:
        print(f"  Q: {q:<48} R: {ia.repond(q)}")
