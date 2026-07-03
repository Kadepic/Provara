"""
SAVOIR_MASSIF — branche le LEXIQUE MASSIF (1,9 M entrées du dump frwiktionary) comme ressource des briques SENS
(§6.2 b, 2026-06-18). L'IA raisonne sur TOUT le dictionnaire, pas seulement la synonymie.

Le graphe is-a massif (1,87 M arêtes) est cyclique et trop gros pour une clôture directe. Stratégie : charger une
fois, puis pour CHAQUE question extraire le SOUS-GRAPHE pertinent — les chaînes d'ascendance des mots concernés
(remontée garde-anti-cycle) — et le passer à la brique VIVANTE (est_un dirigé, ancêtre commun, chemin, distance,
intrus). Sûr + rapide à l'échelle du dico. Synonymes/antonymes lus directement des champs syn/ant.

  sav = SavoirMassif()                 # charge datasets/lexique_kaikki_full.jsonl
  sav.est_un("chat", "animal")  -> True
  sav.ancetre_commun("chat", "chien")  -> "mammifère"
  sav.chemin("voiture", "objet")       -> ["voiture", "véhicule", …, "objet"]
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

from charge_lexique import charge
from comprehension import Predicteur
from compounding import resoudre
from generateur import GenerateurOrchestre, TYPES_RICHES
from juge import Limites
from store import Store
from taches import Tache

LIM = Limites(temps_s=3, cpu_s=2)
FULL = "datasets/lexique_kaikki_full.jsonl"

# Tests-pince : chaque point d'entrée doit ÊTRE la bonne brique. `est_un` épinglé DIRIGÉ (a->c oui, c->a non) ;
# `distance` épinglé NON DIRIGÉ (a->b<-c, distance 2 ; le `distance` dirigé du chemin rendrait None) pour ne pas
# le confondre avec l'étage chemin.
_PINS = {
    "est_un": ("aretes, x, y",
               "def check(c):\n    E=[('a','b'),('b','c')]\n    assert c(E,'a','c')==True\n"
               "    assert c(E,'c','a')==False\ncheck(est_un)"),
    "ancetre_commun": ("aretes, x, y",
                       "def check(c):\n    E=[('chat','félin'),('félin','mammifère'),('chien','canidé'),"
                       "('canidé','mammifère')]\n    assert c(E,'chat','chien')=='mammifère'\ncheck(ancetre_commun)"),
    "intrus": ("aretes, mots",
               "def check(c):\n    E=[('chat','félin'),('félin','mammifère'),('chien','canidé'),"
               "('canidé','mammifère'),('voiture','engin')]\n"
               "    assert c(E,['chat','chien','voiture'])=='voiture'\ncheck(intrus)"),
    "chemin": ("aretes, x, y",
               "def check(c):\n    E=[('a','b'),('b','c')]\n    assert c(E,'a','c')==['a','b','c']\ncheck(chemin)"),
    "distance": ("aretes, x, y",
                 "def check(c):\n    E=[('a','b'),('c','b')]\n    assert c(E,'a','c')==2\ncheck(distance)"),
}


def _resoudre_briques():
    st = Store(Path(tempfile.mkdtemp()) / "s.jsonl")
    orch = GenerateurOrchestre(st, predicteur=Predicteur(st, types=TYPES_RICHES),
                               relation_lexicale=True, ancetre_commun=True, intrus=True,
                               chemin=True, distance_semantique=True)
    out = {}
    for point, (sig, tests) in _PINS.items():
        t = Tache(id=f"sm/{point}", point_entree=point, prompt=f'def {point}({sig}):\n    """..."""',
                  tests=tests, tests_held_out="")
        _, _, code, _ = resoudre(orch, t, LIM)
        ns: dict = {}
        if code:
            exec(code, ns)
        out[point] = ns.get(point)
    return out


class SavoirMassif:
    """Le dictionnaire entier comme ressource is-a/syn/ant des briques SENS vivantes."""

    def __init__(self, source=FULL):
        lex = charge(source) if isinstance(source, str) else source
        self.suiv = {m: d["hyper"] for m, d in lex.items() if d.get("hyper")}
        self.syn = {m: (d.get("syn") or []) for m, d in lex.items()}
        self.ant = {m: (d.get("ant") or []) for m, d in lex.items()}
        self.n = len(lex)
        self._b = _resoudre_briques()

    def ancetres(self, mot):
        """Chaîne is-a remontée (garde anti-cycle pour le graphe massif cyclique)."""
        out, cur, vus = [mot], mot, {mot}
        while cur in self.suiv and self.suiv[cur] not in vus:
            cur = self.suiv[cur]
            out.append(cur)
            vus.add(cur)
        return out

    def _sous_graphe(self, mots):
        """Arêtes des chaînes d'ascendance des mots = sous-graphe minimal pour la requête."""
        e = []
        for m in mots:
            ch = self.ancetres(m)
            e += list(zip(ch, ch[1:]))
        return list(dict.fromkeys(e))

    def est_un(self, x, y):
        return self._b["est_un"](self._sous_graphe([x, y]), x, y)

    def ancetre_commun(self, x, y):
        return self._b["ancetre_commun"](self._sous_graphe([x, y]), x, y)

    def chemin(self, x, y):
        return self._b["chemin"](self._sous_graphe([x, y]), x, y)

    def distance(self, x, y):
        return self._b["distance"](self._sous_graphe([x, y]), x, y)

    def intrus(self, mots):
        return self._b["intrus"](self._sous_graphe(mots), mots)

    def synonymes(self, mot):
        return self.syn.get(mot, [])

    def contraires(self, mot):
        return self.ant.get(mot, [])


def main(argv) -> int:
    sav = SavoirMassif()
    print(f"SavoirMassif : {sav.n} entrées | {len(sav.suiv)} arêtes is-a chargées.\n")
    print("Raisonnement SENS sur tout le dictionnaire (briques vivantes, sous-graphe par requête) :")
    for x, y in [("chat", "animal"), ("voiture", "objet"), ("guitare", "instrument"), ("chat", "voiture")]:
        print(f"  est_un({x}, {y}) -> {sav.est_un(x, y)}")
    for x, y in [("chat", "chien"), ("voiture", "guitare")]:
        print(f"  ancetre_commun({x}, {y}) -> {sav.ancetre_commun(x, y)}")
    print(f"  chemin(voiture, objet) -> {sav.chemin('voiture', 'objet')}")
    print(f"  intrus([chat, chien, voiture]) -> {sav.intrus(['chat', 'chien', 'voiture'])}")
    print(f"  synonymes(voiture) -> {sav.synonymes('voiture')[:5]}")
    print(f"  contraires(chaud) -> {sav.contraires('chaud')[:5]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
