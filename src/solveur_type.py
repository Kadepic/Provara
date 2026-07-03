"""SOLVEUR DIRIGÉ PAR LES TYPES (means-end) — « le comment » contre « le plus » (2026-06-19).

Constat mesuré (`mesure_exploration_dirigee.py`) : l'exploration EN AVANT (largeur quadratique OU base linéaire) noie son
budget à couvrir la profondeur-1 et n'atteint PAS les cibles `map∘reduce` (sum∘map(x²)…) même à 600 tentatives. Le coût
vient de l'ÉNUMÉRATION aveugle — produire BEAUCOUP en espérant tomber sur la cible.

Ici on renverse : on part DU BUT et on remonte (recherche arrière dirigée par les types), comme un humain résout. Pour
fabriquer une cible (tin→tout) de comportement `vise` :
  1. un atome de base la fait-il directement ?            (coût : ~|base de ce type|)
  2. sinon target = f ∘ g : on CHOISIT g (tin→mid) dans la base, on calcule les valeurs intermédiaires g(entrées), puis
     on RÉSOUT récursivement f (mid→tout) pour que f(intermédiaires)=vise. La récursion porte le but, pas l'énumération.
Mémoïsé par (tin, tout, vise). Le coût = nb d'évaluations de comportement (execs) = la « puissance » dépensée.

Même garde-fou : la RÉALITÉ juge (held-out adversaire dans les probes ; reconfirmation sandbox par le vrai juge en fin).
Honnête : hors de l'espace compose/map/primitives → None (jamais de faux). Borné en profondeur.
"""
from __future__ import annotations

from auto_invention_ouverte import PRIMITIVES, MoteurOuvert, _empreinte, _norm

_compose = MoteurOuvert._compose
_map = MoteurOuvert._map


# Prédicats int→bool pour le filter (sélection). filter_p(x) = [e for e in x if p(e)] : list→list.
_PREDICATS = ("e > 0", "e < 0", "e % 2 == 0", "e % 2 == 1")


def _base_etendue(filtres: bool = False):
    """Base de candidats g : les 16 primitives + le map de chaque primitive int→int (ouvre map(x*x), map(x+1)…).
    Ordre = qualité : réducteurs/arith/map d'abord, puis les transforms QUI NE CHANGENT RIEN aux fonctions invariantes
    (sorted, reverse) en DERNIER -> on préfère `sum∘map(x²)` à `sum∘map(x²)∘sorted∘reverse` (solution propre, moins chère).
    `filtres=True` ajoute les filter par prédicat (list→list) -> ouvre « somme des pairs », « combien de positifs »…
    (togglable : on MESURE son gain avant de l'adopter par défaut — excellence par brique)."""
    reordonne = {"sorted(x)", "x[::-1]"}
    atomes = list(PRIMITIVES) + [m for p in PRIMITIVES if (m := _map(p))]
    if filtres:
        atomes += [(f"[e for e in x if {p}]", "list", "list") for p in _PREDICATS]
    atomes.sort(key=lambda a: 1 if a[0] in reordonne else 0)   # tri stable : rearrangers à la fin
    return atomes


BASE = _base_etendue()


class Solveur:
    def __init__(self, profondeur_max: int = 4, budget: int | None = None, base=None):
        self.profondeur_max = profondeur_max
        self.budget = budget    # borne dure de puissance (opt-in) : stoppe au-delà -> None honnête, jamais de faux
        self.cout = 0           # nb d'évaluations de comportement = la PUISSANCE dépensée
        self.base = base if base is not None else BASE
        self._memo = {}

    def _emp(self, expr, tin, tout, entrees):
        self.cout += 1
        return _empreinte(expr, tin, tout, entrees)

    def resoudre(self, cible, tin, tout, entrees):
        """Renvoie l'expr qui reproduit `cible` sur `entrees` (held-out inclus), ou None. entrees = inputs de type tin."""
        vise = []
        for x in entrees:
            v = _norm(cible(list(x) if tin == "list" else x), tout)
            if v is None:
                return None
            vise.append(v)
        return self._cherche(tin, tout, tuple(entrees), tuple(vise), self.profondeur_max)

    def _cherche(self, tin, tout, entrees, vise, prof):
        if self.budget is not None and self.cout >= self.budget:    # budget épuisé -> abandon honnête (pas de memo poison)
            return None
        cle = (tin, tout, entrees, vise, prof)   # entrees INCLUS : un même `vise` sur des entrées différentes = un autre problème
        if cle in self._memo:
            return self._memo[cle]
        res = None
        # 1. un atome de base de ce type fait-il directement le job ?
        for expr, ti, to in self.base:
            if ti == tin and to == tout and self._emp(expr, tin, tout, entrees) == vise:
                res = expr
                break
        # 2. sinon, remonter : target = f ∘ g, on choisit g (tin→mid), on résout f (mid→tout) sur g(entrées)
        if res is None and prof > 0:
            for gexpr, gi, go in self.base:
                if gi != tin:
                    continue
                inter = self._emp(gexpr, gi, go, entrees)      # valeurs intermédiaires = nouvelles "entrées" pour f
                if inter is None:
                    continue
                if go == tin and inter == entrees:             # g ne change RIEN ici (ex. sorted∘sorted) -> détour stérile
                    continue
                sous = self._cherche(go, tout, inter, vise, prof - 1)
                if sous is not None:
                    c = _compose((sous, go, tout), (gexpr, gi, go))   # f ∘ g
                    if c and len(c[0]) <= 200:
                        res = c[0]
                        break
        self._memo[cle] = res
        return res

    # --- IDDFS À MEMO D'ÉTAT PARTAGÉ (2026-06-19, question Yohan « réduire le HORS comme pour v3a/v3b ») ---
    # L'approfondissement itératif naïf (un Solveur._memo NEUF par passe) RE-EXPLORE les profondeurs basses à chaque
    # passe -> mesuré : produit (HORS) coûte 43300 évals en itératif vs 25391 en passe unique (~18000 gaspillées).
    # Ici un SEUL memo, keyé par ÉTAT (sans prof) : memo[etat] = (prof_recherché, sol|None, prof_sol). La passe d+1
    # réutilise « état déjà cherché à profondeur >= p, rien trouvé » -> élague les sous-arbres déjà prouvés stériles.
    # SOUND uniquement SANS budget (un budget tronque la recherche -> un None mémoïsé serait faux). Minimalité préservée
    # (IDDFS top-level : la 1ʳᵉ profondeur qui réussit donne la solution de profondeur minimale).
    def cherche_iddfs(self, tin, tout, entrees, vise, prof_max):
        for d in range(1, prof_max + 1):
            r = self._cherche_m(tin, tout, entrees, vise, d)
            if r is not None:
                return r
        return None

    def _cherche_m(self, tin, tout, entrees, vise, prof):
        etat = (tin, tout, entrees, vise)
        c = self._memo.get(etat)
        if c is not None:
            sd, sol, sp = c
            if sol is not None and sp <= prof:     # solution connue assez peu profonde
                return sol
            if sol is None and sd >= prof:          # déjà cherché aussi profond, rien d'atteignable à <= prof
                return None
        sol = None
        for expr, ti, to in self.base:              # profondeur 0 : un atome direct ?
            if ti == tin and to == tout and self._emp(expr, tin, tout, entrees) == vise:
                sol = expr
                break
        if sol is None and prof > 0:                # profondeur > 0 : target = f ∘ g
            for gexpr, gi, go in self.base:
                if gi != tin:
                    continue
                inter = self._emp(gexpr, gi, go, entrees)
                if inter is None:
                    continue
                if go == tin and inter == entrees:  # g ne change rien -> détour stérile
                    continue
                sous = self._cherche_m(go, tout, inter, vise, prof - 1)
                if sous is not None:
                    comp = _compose((sous, go, tout), (gexpr, gi, go))
                    if comp and len(comp[0]) <= 200:
                        sol = comp[0]
                        break
        prev = self._memo.get(etat)
        sd_prev = prev[0] if prev else -1
        # sp = `prof` (borne sup. conservatrice de la profondeur de la solution) -> réutilisation sûre (jamais de faux).
        self._memo[etat] = (max(sd_prev, prof), sol, prof if sol is not None else None)
        return sol


def _type_de(v):
    """Type means-end d'une valeur : 'int' (scalaire) | 'list' (liste/tuple d'entiers) | None (hors espace : str, float…)."""
    if isinstance(v, bool):
        return None
    if isinstance(v, int):
        return "int"
    if isinstance(v, (list, tuple)):
        return "list" if v and all(isinstance(e, int) and not isinstance(e, bool) for e in v) else None
    return None


def resoudre_demande(point_entree, exemples, exemples_held=None, budget=None, profondeur_max=4, filtres=True):
    """Chemin RAPIDE dirigé par le but pour une DEMANDE par l'exemple. N'APPLIQUE QUE le mono-entrée int/list (sinon
    rend (None, 0) -> le moteur lourd prend le relais, intact). Reconfirme au VRAI juge sur visible+held avant de rendre.
    Renvoie (code | None, cout). Honnête : hors espace / non trouvé -> None (jamais de faux)."""
    tous = list(exemples) + list(exemples_held or [])
    if not tous or any(len(args) != 1 for args, _ in tous):       # uniquement les fonctions à UN argument
        return None, 0
    tin = _type_de(exemples[0][0][0])
    tout = _type_de(exemples[0][1])
    if tin is None or tout is None:
        return None, 0
    if any(_type_de(args[0]) != tin or _type_de(out) != tout for args, out in tous):   # types homogènes
        return None, 0
    h = lambda v: tuple(v) if isinstance(v, (list, tuple)) else v
    entrees = tuple(h(args[0]) for args, _ in tous)               # visible + held : le held-out CONTRAINT la recherche
    vise = tuple(_norm(out, tout) for _, out in tous)             # (anti-coïncidence pendant la recherche, pas après)
    if any(v is None for v in vise):
        return None, 0
    # APPROFONDISSEMENT ITÉRATIF : on cherche d'abord en profondeur 1, puis 2… -> la PREMIÈRE solution est de profondeur
    # MINIMALE (la plus propre et la moins chère). Coût cumulé borné par `budget` (opt-in).
    base = _base_etendue(filtres) if filtres else None
    # GARDE MÉMOIRE (2026-06-20) : means-end exécute ~50k exprs EN-PROCESS via `_empreinte` ; une expr type `x * énorme`
    # (ex. sur daily_temperatures list->list) matérialise ~1,5 Go avant que MemoryError ne tombe au plafond ulimit -v,
    # faisant flaker les vagues lourdes (16/25). On cape la recherche à VMS+512 Mo (= borne sandbox juge) : SOUND (toute
    # expr dépassant échoue AUSSI en sandbox -> aucune perte de couverture), MemoryError rattrapé par `_empreinte`
    # (except Exception -> None), pic RSS ~600 Mo. UN seul setrlimit pour toute la recherche (pas par-éval). Cf. REPRISE.
    from prefiltre import _limite_memoire
    with _limite_memoire():
        if budget is None:
            # SANS budget : IDDFS à memo d'état partagé (sound ici) -> profondeur minimale ET zéro re-exploration entre passes.
            s = Solveur(profondeur_max=profondeur_max, base=base)
            expr = s.cherche_iddfs(tin, tout, entrees, vise, profondeur_max)
            cout_total = s.cout
        else:
            # AVEC budget : passe-par-passe (memo neuf, prof-keyé) -> la troncature par budget reste sound (jamais de faux None).
            cout_total = 0
            expr = None
            for d in range(1, profondeur_max + 1):
                reste = budget - cout_total
                if reste <= 0:
                    break
                s = Solveur(profondeur_max=d, budget=reste, base=base)
                expr = s._cherche(tin, tout, entrees, vise, d)
                cout_total += s.cout
                if expr is not None:
                    break
    if expr is None:
        return None, cout_total
    code = f"def {point_entree}(*args, **kwargs):\n    x = args[0]\n    return {expr}\n"
    # RÉALITÉ tranche : reconfirmation sandbox sur TOUS les exemples (visible + held-out).
    from juge import Limites, juge
    lignes = [f"    assert c({args[0]!r}) == {out!r}" for args, out in tous]
    tests = "def check(c):\n" + "\n".join(lignes) + f"\ncheck({point_entree})\n"
    if juge(code, tests, Limites(temps_s=3, cpu_s=2)).passe:
        return code, cout_total
    return None, cout_total


# --- batterie identique à mesure_exploration_dirigee (dont les profondeur-3 que l'avant ne résout pas) ---
BATTERIE = [
    ("somme_carres",        lambda x: sum(e * e for e in x),          "list", "int", [(1, 2, 3), (2, 3), (-2, 3), (-1, -4)]),
    ("triangulaire",        lambda x: sum(range(x)),                  "int",  "int", [4, 5, 1, 6, 0]),
    ("somme_doublee",       lambda x: sum(x) * 2,                     "list", "int", [(1, 2, 3), (2, 3), (-2, 3), (4,)]),
    ("carre_longueur",      lambda x: len(x) * len(x),                "list", "int", [(1, 2, 3), (5, 5), (1, 2, 3, 4), (7,)]),
    ("max_plus_un",         lambda x: max(x) + 1,                     "list", "int", [(1, 2, 3), (5, 5), (-2, 0, 3), (4, 2)]),
    ("somme_plus_un",       lambda x: sum(e + 1 for e in x),          "list", "int", [(1, 2, 3), (2, 3), (-2, 3), (0, 0, 0)]),
    ("carres_range_somme",  lambda x: sum(e * e for e in range(x)),   "int",  "int", [3, 4, 1, 5, 2]),                       # depth-3
    ("longueur_doublee",    lambda x: len(x) * 2,                     "list", "int", [(1, 2, 3), (5, 5), (7,), (1, 2, 3, 4)]),
    ("max_carres",          lambda x: max(e * e for e in x),          "list", "int", [(1, 2, 3), (-2, 1), (0, -3), (5, 5)]),
    ("neg_somme",           lambda x: -sum(x),                        "list", "int", [(1, 2, 3), (2, 3), (-2, 3), (4,)]),
    ("somme_carres_x2",     lambda x: sum(e * e for e in x) * 2,      "list", "int", [(1, 2, 3), (2, 3), (-2, 3), (1,)]),     # depth-3
    ("triangulaire_carre",  lambda x: sum(range(x)) ** 2,             "int",  "int", [3, 4, 2, 5]),                          # depth-3
    # HONNÊTE : hors de l'espace compose/map/primitives -> doit renvoyer None (jamais de faux)
    ("produit",             lambda x: __import__("math").prod(x),     "list", "int", [(1, 2, 3, 4), (2, 3), (5, 2)]),
]


def main() -> int:
    from garde_ressources import borne
    borne()
    print("SOLVEUR DIRIGÉ PAR LES TYPES (recherche arrière) — coût = nb d'évaluations (la « puissance »).\n")
    print(f"{'tâche':>20} | résolu | coût | atome")
    print("-" * 78)
    n_ok = 0
    couts = []
    sols = {}
    for nom, cible, tin, tout, probes in BATTERIE:
        s = Solveur()
        expr = s.resoudre(cible, tin, tout, probes)
        attendu_none = nom == "produit"
        bon = (expr is None) if attendu_none else (expr is not None)
        if bon and not attendu_none:
            n_ok += 1
            couts.append(s.cout)
        sols[nom] = (expr, s.cout)
        montre = "—(HORS ok)" if attendu_none and expr is None else (expr[:34] + "…" if expr and len(expr) > 35 else expr)
        print(f"{nom:>20} | {'OK ' if bon else 'RATÉ':>6} | {s.cout:>4} | {montre}")

    # Reconfirmation sandbox (vrai juge) sur les 3 cibles profondeur-3 que l'exploration EN AVANT n'atteint pas à 600.
    print("\nReconfirmation sandbox (vrai juge) des cibles profondeur-3 (que la largeur/base ne résolvent pas à 600) :")
    from juge import Limites, juge
    LIM = Limites(temps_s=3, cpu_s=2)
    profond = {
        "carres_range_somme": ("int", "def check(c):\n assert c(3)==5\n assert c(4)==14\ncheck(f)",
                               "def check(c):\n assert c(1)==0\n assert c(5)==30\n assert c(6)==55\ncheck(f)"),
        "somme_carres_x2":    ("list", "def check(c):\n assert c([1,2,3])==28\n assert c([2,3])==26\ncheck(f)",
                               "def check(c):\n assert c([-2,3])==26\n assert c([4])==32\ncheck(f)"),
        "triangulaire_carre": ("int", "def check(c):\n assert c(3)==9\n assert c(4)==36\ncheck(f)",
                               "def check(c):\n assert c(2)==1\n assert c(5)==100\ncheck(f)"),
    }
    tous_ok = True
    for nom, (_, tests, held) in profond.items():
        expr = sols[nom][0]
        if not expr:
            tous_ok = False
            print(f"  [RATÉ] {nom} : non résolu")
            continue
        code = f"def f(x):\n    return {expr}\n"
        ok = juge(code, tests, LIM).passe and juge(code, held, LIM).passe
        tous_ok = tous_ok and ok
        print(f"  [{'OK ' if ok else 'RATÉ'}] {nom} = {expr}  (coût {sols[nom][1]} évals)")

    print("\n=== VERDICT ===")
    moy = sum(couts) / len(couts) if couts else 0
    print(f"  tâches résolues (hors la piège 'produit') : {n_ok}/{len(BATTERIE) - 1}")
    print(f"  coût moyen : {moy:.0f} évals/tâche   (l'exploration EN AVANT échoue 4 de celles-ci à 600 tentatives)")
    print(f"  cibles profondeur-3 confirmées par le vrai juge : {tous_ok}")
    print(f"  honnête : 'produit' (hors espace) -> {sols['produit'][0]!r}")
    gagne = n_ok >= 11 and tous_ok and sols["produit"][0] is None
    print(f"  → {'MEANS-END = le bon levier : MIEUX (résout les profondes) à puissance MOINDRE.' if gagne else 'résultat mitigé — voir détail.'}")
    return 0 if gagne else 1


if __name__ == "__main__":
    raise SystemExit(main())
