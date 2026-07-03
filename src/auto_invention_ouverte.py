"""
MOTEUR D'AUTO-INVENTION OUVERTE — compositionnel & multi-domaines (2026-06-18, cap project-vision-auto-evolution-verite).

Le moteur précédent (auto_invention) mutait un espace ARITHMÉTIQUE semé par nous. Ici on enlève ce plafond : le
générateur n'est plus un menu d'opérateurs choisis à la main, c'est la COMPOSITION — le combinateur universel. Avec
quelques primitives typées (entiers ↔ listes) et deux opérateurs ouverts (compose f∘g, map f), l'espace atteignable
est SANS PLAFOND imposé (borné seulement par la profondeur/budget). Le moteur :
  - invente à TRAVERS les domaines (int→int, list→int, int→list, list→list),
  - COMPOSE ses propres découvertes (les inventés deviennent matière à composition -> profondeur ouverte),
  - ne GARDE que ce que la RÉALITÉ valide (typé : déterministe, total, comportementalement NOUVEAU, généralise),
  - SANS tâche humaine dans la boucle de découverte.

La valeur se mesure sur une batterie de tâches RÉELLES jamais montrées au moteur : combien deviennent résolubles à
mesure que la frontière s'étend (et certaines exigent une profondeur/composition inatteignable depuis la graine).

Honnête : « tout le possible » est une asymptote non atteignable en un budget fini — mais l'ARCHITECTURE n'a pas de
plafond qu'on impose. Ce qui n'est pas dérivable (hors compose/map/primitives) reste HORS (None), jamais inventé faux.
"""
from __future__ import annotations

import re

from juge import Limites, juge

LIM = Limites(temps_s=3, cpu_s=2)

# Domaines sondés (la réalité teste le comportement). Listes NON VIDES (max/tête sont totales dessus).
INT_P = (0, 1, 2, 3, 5, -1, -2, 7)
INT_H = (4, 9, -4, 11, 6)
LIST_P = ((1,), (2, 1, 3), (5, 5), (1, 2, 3, 4), (-2, 0, 3), (4, 2))
LIST_H = ((7, 7, 7), (9, 1), (0, -1, -2, -3), (3,))

_VAR = re.compile(r"(?<![A-Za-z0-9_])x(?![A-Za-z0-9_])")

# Primitives typées de départ (expr en `x`, type_in, type_out). int/list = les deux domaines.
PRIMITIVES = [
    ("x + 1", "int", "int"), ("x - 1", "int", "int"), ("x * 2", "int", "int"),
    ("x * x", "int", "int"), ("-x", "int", "int"), ("x % 2", "int", "int"),
    ("len(x)", "list", "int"), ("sum(x)", "list", "int"), ("max(x)", "list", "int"),
    ("min(x)", "list", "int"), ("x[0]", "list", "int"), ("x[-1]", "list", "int"),
    ("sorted(x)", "list", "list"), ("x[::-1]", "list", "list"), ("x[1:]", "list", "list"),
    ("list(range(x))", "int", "list"),
]


def _fn(expr: str):
    ns: dict = {}
    try:
        exec(f"def _f(x):\n    return {expr}\n", ns)
    except Exception:
        return None
    return ns.get("_f")


def _sondes(tin):
    return (INT_P, INT_H) if tin == "int" else (LIST_P, LIST_H)


def _norm(v, tout):
    """Normalise une sortie en valeur hashable du bon TYPE, ou None si type faux."""
    if tout == "int":
        return v if isinstance(v, int) and not isinstance(v, bool) else None
    if isinstance(v, list):
        return tuple(v) if all(isinstance(e, int) and not isinstance(e, bool) for e in v) else None
    return None


def _empreinte(expr, tin, tout, entrees):
    """Empreinte typée = sorties normalisées sur `entrees`, ou None si crash / type faux.
    (Les exprs sont PURES par construction — compose/map de primitives sans hasard — donc déterministes.)"""
    fn = _fn(expr)
    if fn is None:
        return None
    out = []
    for x in entrees:
        try:
            nr = _norm(fn(list(x) if tin == "list" else x), tout)
        except Exception:
            return None
        if nr is None:                               # type faux / partiel
            return None
        out.append(nr)
    return tuple(out)


class MoteurOuvert:
    """Répertoire typé qui s'étend par COMPOSITION ouverte, jugé par l'exécution. Pas de plafond d'opérateurs."""

    def __init__(self, primitives=PRIMITIVES, seed: int = 0):
        self.atomes = []                  # (expr, tin, tout)
        self.empreintes = {}              # (tin, fp) -> expr   (nouveauté comportementale)
        self.inventes = []
        self._cout = 0                    # nb de tentatives d'insertion (= execs sur sondes) — budget HONNÊTE
        for e, ti, to in primitives:
            self._ajoute(e, ti, to)
        self._cout = 0                    # le coût ne compte QUE l'exploration (la graine est gratuite, identique partout)

    def _ajoute(self, expr, tin, tout, invente=False):
        self._cout += 1                   # chaque tentative = un exec sur sondes+held : c'est LE coût réel
        p, h = _sondes(tin)
        fp_all = _empreinte(expr, tin, tout, p + h)   # un seul exec : sondes + held-out d'un coup
        if fp_all is None:                            # invalide (crash/type) ou ne généralise pas (held-out)
            return False
        cle = (tin, fp_all[:len(p)])                  # nouveauté = empreinte sur les sondes
        if cle in self.empreintes:                                  # déjà connu comportementalement
            return False
        self.empreintes[cle] = expr
        self.atomes.append((expr, tin, tout))
        if invente:
            self.inventes.append((expr, tin, tout))
        return True

    @staticmethod
    def _compose(f, g):
        """f∘g : f(g(x)). Type : g.tin -> f.tout, exige g.tout == f.tin. Substitution textuelle de x."""
        fe, fi, fo = f
        ge, gi, go = g
        if go != fi:
            return None
        expr = _VAR.sub(f"({ge})", fe)
        return (expr, gi, fo)

    @staticmethod
    def _map(f):
        """map f sur une liste : (int->int) -> (list->list). [f(e) for e in x]."""
        fe, fi, fo = f
        if fi != "int" or fo != "int":
            return None
        corps = _VAR.sub("e", fe)
        return (f"[{corps} for e in x]", "list", "list")

    def explore(self, rounds: int = 4, cap: int = 170, budget: int | None = None):
        """LARGEUR aveugle : compose le répertoire courant round par round (et map les int->int) ; garde le NOUVEAU
        validé. `budget` (optionnel) borne le nb de tentatives d'insertion (coût réel) pour comparer à exploration égale."""
        a_sec = 0
        for _ in range(rounds):
            base = list(self.atomes)
            neuf = 0
            for f in base:
                if budget is not None and self._cout >= budget:
                    return self.inventes
                m = self._map(f)
                if m and self._ajoute(*m, invente=True):
                    neuf += 1
                for g in base:
                    if budget is not None and self._cout >= budget:
                        return self.inventes
                    c = self._compose(f, g)
                    if c and len(c[0]) <= 120 and self._ajoute(*c, invente=True):
                        neuf += 1
                        if len(self.atomes) >= cap:
                            return self.inventes
            a_sec = a_sec + 1 if neuf == 0 else 0
            if a_sec >= 2:
                break
        return self.inventes

    def explore_dirige(self, budget: int = 400, cap: int = 4000):
        """NOUVEAUTÉ DIRIGÉE (best-first) : au lieu de finir toute la profondeur-1 avant la 2 (barrière de round de la
        largeur), on dépense le budget sur les atomes les plus PROMETTEURS d'abord. Curiosité = productivité estimée du
        type de sortie (territoire fécond) − pénalité de longueur (rester compact/réutilisable). Un atome fraîchement
        inventé et fécond (ex. map(x*x) : list->list) est ainsi RE-COMPOSÉ tôt → la profondeur UTILE est atteinte sous
        un budget où la largeur aveugle n'a encore produit que du peu profond. Autonome : aucune tâche humaine dans la
        boucle, la réalité (juge typé + held-out à l'insertion) filtre comme toujours.
        Coût mesuré = mêmes tentatives d'insertion que `explore(budget=...)` → comparaison à exploration ÉGALE."""
        import heapq
        prod = {}                          # type de sortie -> productivité observée (a priori 1.0) : signal de nouveauté
        deja = set()                       # exprs déjà développées (chaque atome développé au plus une fois)
        ordre = 0                          # départage stable du tas (pas de Math.random) -> déterministe

        def score(atome):
            e, _, to = atome
            return prod.get(to, 1.0) - 0.03 * len(e)

        tas = []
        for a in list(self.atomes):
            ordre += 1
            heapq.heappush(tas, (-score(a), ordre, a))

        while tas and self._cout < budget and len(self.atomes) < cap:
            f = heapq.heappop(tas)[2]
            if f[0] in deja:
                continue
            deja.add(f[0])
            produit = 0
            enfants = []
            m = self._map(f)
            if m and self._cout < budget and self._ajoute(*m, invente=True):
                produit += 1
                enfants.append(m)
            for g in list(self.atomes):
                if self._cout >= budget:
                    break
                for c in (self._compose(f, g), self._compose(g, f)):
                    if c and len(c[0]) <= 120 and self._cout < budget and self._ajoute(*c, invente=True):
                        produit += 1
                        enfants.append(c)
            if produit:                    # crédit de fécondité au type de sortie développé -> ce territoire remonte
                prod[f[2]] = prod.get(f[2], 1.0) + produit
            for c in enfants:
                ordre += 1
                heapq.heappush(tas, (-score(c), ordre, c))
        return self.inventes

    def explore_basis(self, budget: int = 400, cap: int = 100000):
        """COMPOSITION SUR BASE FIXE (le « comment » : fan-out LINÉAIRE au lieu du produit croisé quadratique de la
        largeur). On ne compose pas atome×atome (quadratique, qui noie le budget dans la largeur-1) : on développe une
        frontière en composant chaque atome avec la BASE des 16 primitives seulement (+ map). compose étant associatif,
        composer une chaîne avec une primitive à GAUCHE ou à DROITE atteint TOUTES les chaînes -> base complète, mais à
        coût ~33/atome (linéaire) au lieu de ~|atomes| -> la profondeur UTILE est atteinte sous un budget où la largeur
        n'a pas fini la profondeur-1. BFS = grimpe la profondeur uniformément. Autonome, réalité-jugée comme toujours."""
        from collections import deque
        base = [a for a in self.atomes]          # les 16 primitives = la BASE (toutes comportementalement distinctes)
        file = deque(self.atomes)
        while file and self._cout < budget and len(self.atomes) < cap:
            f = file.popleft()
            m = self._map(f)
            if m and self._cout < budget and self._ajoute(*m, invente=True):
                file.append(m)
            for p in base:
                if self._cout >= budget:
                    break
                for c in (self._compose(f, p), self._compose(p, f)):
                    if c and len(c[0]) <= 120 and self._cout < budget and self._ajoute(*c, invente=True):
                        file.append(c)
        return self.inventes

    def resoudre(self, tache):
        """Le répertoire (graine + inventé) résout-il une tâche RÉELLE jamais montrée ? (juge visible + held-out)."""
        for expr, _, _ in self.atomes:
            code = f"def {tache.point_entree}(x):\n    return {expr}\n"
            if juge(code, tache.tests, LIM).passe and (
                    not tache.tests_held_out or juge(code, tache.tests_held_out, LIM).passe):
                return code
        return None


if __name__ == "__main__":
    from garde_ressources import borne
    borne()  # filet kernel dur : explore() est combinatoire (|base|² execs/round) -> MemoryError rattrapable AVANT que WSL/Windows ne tombe.
    m = MoteurOuvert()
    g = len(m.atomes)
    try:
        inv = m.explore()
    except MemoryError:
        raise SystemExit("explore() a atteint le plafond mémoire (garde 2 Go) -> arrêt honnête, WSL préservé. "
                         "Passe un budget explicite (m.explore(budget=N)) pour borner le coût.")
    print(f"Exploration OUVERTE (compose + map, multi-domaines) : graine {g} -> {len(m.atomes)} atomes "
          f"({len(inv)} inventés), sans tâche humaine.")
    par_type = {}
    for e, ti, to in m.atomes:
        par_type[(ti, to)] = par_type.get((ti, to), 0) + 1
    print("Répartition par type (in->out) :", {f"{a}->{b}": n for (a, b), n in sorted(par_type.items())})
    print("\nÉchantillon d'atomes auto-inventés (compositions de découvertes) :")
    for e, ti, to in inv[:18]:
        print(f"    [{ti}->{to}] {e}")
