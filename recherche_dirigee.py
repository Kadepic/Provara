"""
RECHERCHE DIRIGÉE — dompter l'explosion combinatoire de l'invention ouverte (2026-06-18, cap auto-évolution).

L'auto-invention ouverte (auto_invention_ouverte) ÉNUMÈRE en largeur jusqu'à un cap, puis cherche dans le sac. Ici on
DIRIGE : énumération BOTTOM-UP par taille croissante (les programmes courts d'abord = rasoir d'Occam), élaguée par
ÉQUIVALENCE OBSERVATIONNELLE — deux programmes qui se comportent pareil sur les sondes sont FUSIONNÉS (on garde le
plus court). C'est la réalité qui juge l'identité, pas la syntaxe. Effet : l'espace effectif s'effondre, on atteint
des profondeurs inaccessibles à l'énumération naïve, et on S'ARRÊTE dès qu'une cible est résolue (visible + held-out).

C'est le mécanisme de référence de la synthèse de programmes (enumeration + observational equivalence), ici greffé
sur le moteur ouvert. Honnête : hors de l'espace (compose/map/primitives), aucune solution -> None, jamais de faux.
"""
from __future__ import annotations

from auto_invention_ouverte import PRIMITIVES, _empreinte, _sondes
from auto_invention_ouverte import MoteurOuvert as _M

_compose = _M._compose
_map = _M._map


def _fp_sondes(expr, tin, tout):
    """Empreinte sur les SONDES (pour l'équivalence observationnelle). None si invalide."""
    p, _ = _sondes(tin)
    return _empreinte(expr, tin, tout, p)


class Banque:
    """Banque de programmes indexée par taille et par type, dédupliquée par ÉQUIVALENCE OBSERVATIONNELLE."""

    def __init__(self):
        self.par_taille = {}                 # taille -> list[(expr, tin, tout)]
        self.vus = set()                     # (tin, tout, fp_sondes) déjà représentés (le plus court gagne)
        self.generes = 0                     # candidats FORMÉS (avant élagage) = mesure de l'explosion brute
        self.distincts = 0                   # comportements distincts retenus = espace EFFECTIF

    def ajoute(self, expr, tin, tout):
        """Tente d'insérer un programme ; rejeté si invalide ou comportement déjà connu. Renvoie l'empreinte ou None."""
        self.generes += 1
        fp = _fp_sondes(expr, tin, tout)
        if fp is None:
            return None
        cle = (tin, tout, fp)
        if cle in self.vus:                  # équivalence observationnelle : déjà représenté par plus court
            return None
        self.vus.add(cle)
        self.distincts += 1
        return fp

    def pose(self, taille, expr, tin, tout):
        self.par_taille.setdefault(taille, []).append((expr, tin, tout))

    def de_taille(self, t):
        return self.par_taille.get(t, [])


def synthetise(visible, held, tin, tout, taille_max=6, budget=50000):
    """Recherche dirigée bottom-up d'un programme `tin->tout` satisfaisant `visible` (et `held`).
    Renvoie {sol, taille, generes, distincts, teste}. sol=None si rien dans le budget/taille (honnête).

    budget borne le NOMBRE de candidats générés. Comme chaque candidat = un exec/compile (coût mémoire
    réel non vu par tracemalloc : code-objects + fragmentation CPython), la mémoire est ~proportionnelle
    au budget. Les cibles solubles ici se résolvent en <600 candidats ; le défaut 50000 garde donc 80×
    de marge tout en plafonnant la mémoire d'une cible SANS solution (qui épuise tout le budget) bien
    en-deçà de la zone qui faisait tomber WSL. Un MemoryError éventuel est rattrapé -> None honnête."""
    b = Banque()
    teste = [0]

    def _verifie(expr, ti, to):
        if ti != tin or to != tout:
            return False
        teste[0] += 1
        fn_ns: dict = {}
        try:
            exec(f"def _f(x):\n    return {expr}\n", fn_ns)
            f = fn_ns["_f"]
            for ex, att in visible + held:
                if f(list(ex) if tin == "list" else ex) != att:
                    return False
        except Exception:
            return False
        return True

    def _hors():
        return {"sol": None, "taille": None, "generes": b.generes,
                "distincts": b.distincts, "teste": teste[0]}

    # taille 1 : primitives.
    for expr, ti, to in PRIMITIVES:
        if b.ajoute(expr, ti, to) is not None:
            b.pose(1, expr, ti, to)
            if _verifie(expr, ti, to):
                return {"sol": expr, "taille": 1, "generes": b.generes, "distincts": b.distincts, "teste": teste[0]}

    # tailles croissantes : map (f int->int) et compose (f∘g, taille f + taille g).
    # GÉNÉRÉ-ET-TESTÉ EN FLUX : on n'accumule JAMAIS la liste des produits (qui montait à plusieurs Go
    # sur les cibles sans solution -> explosion mémoire qui faisait tomber WSL). Chaque candidat est
    # inséré+testé immédiatement, donc `b.generes` croît en direct et le budget MORD tout de suite.
    # L'ordre d'énumération est inchangé (maps de taille t-1, puis composes par a croissant ; on ne POSE
    # qu'à la taille courante et on ne LIT que des tailles < taille), donc les solutions trouvées sont
    # identiques ; seul l'épuisement de budget est désormais borné en mémoire ET en temps.
    # FILET DUR : si malgré tout la mémoire atteint le plafond setrlimit (cf. garde_ressources), le
    # MemoryError est rattrapé et converti en None honnête -> jamais de crash, jamais de faux skill.
    try:
        for taille in range(2, taille_max + 1):
            for expr, ti, to in b.de_taille(taille - 1):
                m = _map((expr, ti, to))
                if m and b.ajoute(*m) is not None:
                    b.pose(taille, *m)
                    if _verifie(*m):
                        return {"sol": m[0], "taille": taille, "generes": b.generes,
                                "distincts": b.distincts, "teste": teste[0]}
                if b.generes > budget:
                    return _hors()
            for a in range(1, taille):
                for fe, fi, fo in b.de_taille(a):
                    for ge, gi, go in b.de_taille(taille - a):
                        c = _compose((fe, fi, fo), (ge, gi, go))
                        if c and len(c[0]) <= 200 and b.ajoute(*c) is not None:
                            b.pose(taille, *c)
                            if _verifie(*c):
                                return {"sol": c[0], "taille": taille, "generes": b.generes,
                                        "distincts": b.distincts, "teste": teste[0]}
                        if b.generes > budget:
                            return _hors()
    except MemoryError:
        return _hors()
    return _hors()


if __name__ == "__main__":
    from garde_ressources import borne
    print("[garde] plafond appliqué ->", borne(max_go=2.0, max_cpu_s=180), flush=True)
    CIBLES = {
        "somme_carres (list->int)": ([((1, 2, 3), 14), ((2, 3), 13)], [((-2, 3), 13), ((-1, -4), 17)], "list", "int"),
        "triangulaire (int->int)": ([(4, 6), (5, 10)], [(1, 0), (6, 15)], "int", "int"),
        "max_carre (list->int)": ([((1, 2, 3), 9), ((4, 1), 16)], [((-5, 3), 25), ((-1, -4, 2), 16)], "list", "int"),
        "longueur_doublee (list->int)": ([((1, 2), 4), ((5,), 2)], [((1, 1, 1), 6), ((9, 8), 4)], "list", "int"),
        "produit_HORS (list->int)": ([((1, 2, 3, 4), 24), ((2, 3), 6)], [((5, 2), 10)], "list", "int"),
    }
    for nom, (vis, hel, ti, to) in CIBLES.items():
        r = synthetise(vis, hel, ti, to)
        sol = r["sol"]
        print(f"  {nom:30} -> {('« '+sol+' » (taille '+str(r['taille'])+')') if sol else 'None (hors espace)':45} "
              f"| générés {r['generes']:6} -> distincts {r['distincts']:4} (élagage ×{r['generes']//max(1,r['distincts'])}) "
              f"| testés {r['teste']}")
