"""
MOTEUR DE DÉDUCTION — la mémoire qui RAISONNE (pas seulement qui rappelle). Phase « profondeur » du moteur de
restitution (mandat Yohan 2026-06-24). Model-free, sound : on ne dérive QUE ce qui est logiquement entraîné par
des FAITS vérifiés + des RÈGLES vérifiées ; un fait non entraîné -> HORS (jamais une devinette).

Issu de la recherche profonde 50 sondes :
  • DATALOG SEMI-NAÏF (bottom-up incrémental) : à chaque tour on ne joint que les NOUVEAUX faits (delta) -> pas de
    recalcul, terminaison garantie (Datalog sans symboles de fonction).
  • PROVENANCE (why/how) : chaque fait dérivé porte sa JUSTIFICATION (règle + faits supports) -> explicable + sound.
  • RÉVISION DE CROYANCE (TMS) : rétracter un fait de base invalide proprement tout ce qui en dépendait
    (re-matérialisation depuis la base restante = correct ; DRed incrémental = optimisation future).

Faits = triplets (relation, x, y). Règles = clauses de Horn : tête :- corps. Termes = VARIABLES (Majuscule) ou
constantes. Ex. transitivité : situe(X,Z) :- situe(X,Y), situe(Y,Z).
"""
from __future__ import annotations

import dataclasses


def _est_var(t) -> bool:
    return isinstance(t, str) and t[:1].isupper()


@dataclasses.dataclass(frozen=True)
class Regle:
    tete: tuple                 # (rel, t1, t2)
    corps: tuple                # ((rel, t1, t2), ...)
    nom: str = ""


class MoteurDeduction:
    """Datalog semi-naïf sur triplets, avec provenance et rétraction sound (TMS). FAUX=0 par construction."""

    def __init__(self):
        self.base: dict[tuple, str] = {}          # faits de base : triplet -> source
        self.regles: list[Regle] = []
        self.faits: set[tuple] = set()            # tous les faits (base + dérivés) après matérialisation
        self.prov: dict[tuple, list] = {}         # triplet -> justification (("base",source) | (nom_regle, [supports]))

    # — construction (chaque mutation INVALIDE la matérialisation : sinon un fait de base ajouté après une
    #   première requête serait servi « hors » à tort — faux négatif — tant que rien ne re-matérialise) —
    def ajoute_fait(self, rel, x, y, source="donné"):
        self.base[(rel, x, y)] = source
        self.faits = set()

    def ajoute_regle(self, tete, corps, nom=""):
        if nom == "base":
            # « base » est le SENTINEL de provenance des faits de base (cf. materialise) : une règle portant ce
            # nom ferait passer ses dérivations pour des faits de base (trou FAUX=0 prouvé par attaque 2026-07-02).
            raise ValueError("nom de règle réservé : 'base' (sentinel de provenance)")
        self.regles.append(Regle(tete, tuple(corps), nom or f"r{len(self.regles)}"))
        self.faits = set()

    # — jointure d'un atome de corps contre les faits courants, étend les bindings —
    def _match(self, atome, faits, binding):
        rel, t1, t2 = atome
        for (fr, fx, fy) in faits:
            if fr != rel:
                continue
            b = dict(binding)
            ok = True
            for terme, val in ((t1, fx), (t2, fy)):
                if _est_var(terme):
                    if terme in b and b[terme] != val:
                        ok = False; break
                    b[terme] = val
                elif terme != val:
                    ok = False; break
            if ok:
                yield b, (fr, fx, fy)

    def _evalue_corps(self, corps, faits):
        """Renvoie les (binding, [faits_supports]) qui satisfont tout le corps (jointure naïve, bornée Datalog)."""
        partiels = [({}, [])]
        for atome in corps:
            suiv = []
            for binding, sup in partiels:
                for b2, fait in self._match(atome, faits, binding):
                    suiv.append((b2, sup + [fait]))
            partiels = suiv
            if not partiels:
                break
        return partiels

    def _ground(self, terme, binding):
        return binding[terme] if _est_var(terme) else terme

    # — matérialisation SEMI-NAÏVE (delta) —
    def materialise(self):
        self.faits = set(self.base)
        self.prov = {t: [("base", s)] for t, s in self.base.items()}
        delta = set(self.faits)
        while delta:
            nouveaux = set()
            for regle in self.regles:
                # semi-naïf : au moins un atome du corps doit matcher un fait du delta -> on évalue le corps sur
                # TOUS les faits mais on ne garde une dérivation que si elle UTILISE au moins un fait du delta.
                for binding, supports in self._evalue_corps(regle.corps, self.faits):
                    if not any(s in delta for s in supports):
                        continue
                    rel, t1, t2 = regle.tete
                    tete = (rel, self._ground(t1, binding), self._ground(t2, binding))
                    if tete not in self.faits and tete not in nouveaux:
                        nouveaux.add(tete)
                        self.prov[tete] = [(regle.nom, list(supports))]
            self.faits |= nouveaux
            delta = nouveaux
        return self.faits

    # — interrogation : dérivable ? (base OU dérivé) avec provenance ; sinon HORS —
    def interroge(self, rel, x, y):
        if not self.faits:
            self.materialise()
        t = (rel, x, y)
        if t in self.faits:
            return "verifie", self.prov.get(t)
        return "hors", None

    def reponses(self, rel, x):
        """Requête à VARIABLE : tous les y tels que (rel, x, y) est dérivable, avec provenance. Pour 'capitale de
        France ?' -> [(Paris, justif)]. Sound : ne renvoie que des faits entraînés."""
        if not self.faits:
            self.materialise()
        return [(fy, self.prov.get((fr, fx, fy))) for (fr, fx, fy) in self.faits if fr == rel and fx == x]

    def explique(self, rel, x, y, _prof=0):
        """Arbre de justification lisible (why-provenance) d'un fait dérivé."""
        if not self.faits:                         # même paresse que interroge/reponses (sinon état périmé)
            self.materialise()
        t = (rel, x, y)
        if t not in self.faits:
            return f"{'  ' * _prof}{t} : HORS"
        j = self.prov[t][0]
        if j[0] == "base":
            return f"{'  ' * _prof}{t}  [base: {j[1]}]"
        lignes = [f"{'  ' * _prof}{t}  [{j[0]}]"]
        for s in j[1]:
            lignes.append(self.explique(*s, _prof=_prof + 1))
        return "\n".join(lignes)

    # — RÉTRACTION (TMS) : retire un fait de base + invalide proprement les dérivés dépendants —
    def retracte(self, rel, x, y):
        self.base.pop((rel, x, y), None)
        self.faits = set()                         # re-matérialisation depuis la base restante (sound)
        self.materialise()


if __name__ == "__main__":
    from garde_ressources import borne
    borne(max_cpu_s=120)
    print("=== DÉMO : la mémoire qui RAISONNE (Datalog semi-naïf + provenance + TMS) ===")
    m = MoteurDeduction()
    for a, b in [("Paris", "IleDeFrance"), ("IleDeFrance", "France"), ("France", "Europe")]:
        m.ajoute_fait("situe", a, b, "géo")
    m.ajoute_regle(("situe", "X", "Z"), [("situe", "X", "Y"), ("situe", "Y", "Z")], "transitivite")
    m.materialise()
    print("  Paris situé en Europe ? ->", m.interroge("situe", "Paris", "Europe")[0])
    print("  justification :"); print(m.explique("situe", "Paris", "Europe"))
    print("  Paris situé en Asie ? ->", m.interroge("situe", "Paris", "Asie")[0], "(HORS honnête)")
    m.retracte("situe", "IleDeFrance", "France")
    print("  après rétraction (IleDeFrance->France) : Paris en Europe ? ->",
          m.interroge("situe", "Paris", "Europe")[0], "(invalidé par TMS)")
