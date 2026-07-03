"""
AUTO-SYNTHÈSE PAR SQUELETTES (2026-06-24, ordre Yohan « lui permettre de construire ses propres briques »).

PROBLÈME résolu : `etend_vocabulaire` instancie des SCHÉMAS D'EXPRESSION (compréhensions, folds courts). Mais dès
qu'une cible exige un PRINCIPE ALGORITHMIQUE (état courant façon Kadane, deux-pointeurs, table DP…), aucune expression
ne suffit et il fallait qu'un HUMAIN code la brique. Ici l'IA CONSTRUIT elle-même la brique : on lui donne une
bibliothèque de SQUELETTES paramétrés (trous remplis par des opérateurs/inits), on ÉNUMÈRE les instanciations, et on
ne garde que celles que la SOURCE DE VÉRITÉ valide (reproduisent exemples + held-out). C'est borné, model-free, sound.

SOUNDNESS (FAUX=0) : une instanciation n'est retenue que si elle reproduit TOUS les exemples ET tout le held-out ;
ambiguïté (plusieurs comportements distincts qui collent) -> on ne tranche pas (None), jamais un faux. Une cible hors
des squelettes -> None honnête. Le COMMENT pas le PLUS : la recherche est petite et guidée, pas une force brute.
"""
from __future__ import annotations

from typing import Optional


def _compile(src: str):
    ns: dict = {}
    try:
        exec(src, ns)
    except Exception:
        return None
    return ns.get("f")


def _reproduit(fn, cas) -> bool:
    """fn reproduit-elle TOUS les (entrée, sortie) ? (crash/écart -> False). Entrée = tuple d'args."""
    if fn is None:
        return False
    for args, attendu in cas:
        try:
            if fn(*args) != attendu:
                return False
        except Exception:
            return False
    return True


# ─────────────────────────── SQUELETTE 1 : balayage linéaire à état courant ───────────────────────────
# def f(xs):
#     s = INIT ; best = s
#     for e in xs[START:]:
#         s = STEP(s, e)
#         best = ACC(best, s)
#     return RET
# Couvre : somme (0,+,_), produit (1,*,_), max-courant (x[0],max,_), Kadane (x[0], max(s+e,e), max best),
# min-sous-tableau, max-préfixe… SANS encoder la cible : ce sont des opérateurs génériques.
_INITS = [("0", 0), ("1", 0), ("_xs[0]", 1)]          # (expr_init, start)
_STEPS = [
    "_s + _e", "_s * _e", "max(_s, _e)", "min(_s, _e)",
    "max(_s + _e, _e)", "min(_s + _e, _e)",            # reset façon Kadane (max/min)
    "_s + _e if _s > 0 else _e",                       # Kadane positif-reset
]
_ACCS = ["max(_best, _s)", "min(_best, _s)", "_best + _s", "_s"]   # dernier état, ou agrégat des états
_RETS = ["_best", "_s"]


def _gen_balayage():
    for init, start in _INITS:
        for step in _STEPS:
            for acc in _ACCS:
                for ret in _RETS:
                    src = (
                        "def f(_xs):\n"
                        f"    _s = {init}\n"
                        "    _best = _s\n"
                        f"    for _e in _xs[{start}:]:\n"
                        f"        _s = {step}\n"
                        f"        _best = {acc}\n"
                        f"    return {ret}\n"
                    )
                    yield src


# ─────────────────────────── SQUELETTE 2 : deux pointeurs convergents ───────────────────────────
# def f(h):
#     l, r = 0, len(h)-1 ; lm = rm = 0 ; acc = 0
#     while l < r:
#         if h[l] CMP h[r]:
#             lm = max(lm, h[l]) ; acc += lm - h[l] ; l += 1
#         else:
#             rm = max(rm, h[r]) ; acc += rm - h[r] ; r -= 1
#     return acc
# Couvre l'eau piégée et la famille « deux bords qui se rapprochent en accumulant un manque ». CMP générique.
_CMPS = ["<", "<=", ">", ">="]


def _gen_deux_pointeurs():
    for cmp in _CMPS:
        src = (
            "def f(_h):\n"
            "    _l, _r = 0, len(_h) - 1\n"
            "    _lm = _rm = 0\n"
            "    _acc = 0\n"
            "    while _l < _r:\n"
            f"        if _h[_l] {cmp} _h[_r]:\n"
            "            _lm = max(_lm, _h[_l])\n            _acc += _lm - _h[_l]\n            _l += 1\n"
            "        else:\n"
            "            _rm = max(_rm, _h[_r])\n            _acc += _rm - _h[_r]\n            _r -= 1\n"
            "    return _acc\n"
        )
        yield src


# ─────────────────────────── SQUELETTE 3 : balayage vers LISTE (état courant -> sortie liste) ───────────────────────────
# def f(xs):
#     out = [xs[0]] ; s = xs[0]
#     for e in xs[1:]:
#         s = STEP(s, e) ; out.append(s)
#     return out
# Couvre prefix_sums (s+e), running_max (max), running_min (min), running_product (s*e). Sortie de longueur len(xs).
_STEPS_LISTE = ["_s + _e", "_s * _e", "max(_s, _e)", "min(_s, _e)"]


def _gen_scan_liste():
    for step in _STEPS_LISTE:
        src = (
            "def f(_xs):\n"
            "    _out = [_xs[0]]\n"
            "    _s = _xs[0]\n"
            "    for _e in _xs[1:]:\n"
            f"        _s = {step}\n"
            "        _out.append(_s)\n"
            "    return _out\n"
        )
        yield src


# ─────────────────────────── SQUELETTE 4 : fenêtre de paires voisines (sortie liste longueur n-1) ───────────────────────────
# def f(xs): return [OP(xs[i+1], xs[i]) for i in range(len(xs)-1)]
# Couvre differences (xs[i+1]-xs[i]), sommes/max/min glissants par 2, écart inverse.
_OPS_PAIRE = ["_xs[_i + 1] - _xs[_i]", "_xs[_i] - _xs[_i + 1]", "_xs[_i + 1] + _xs[_i]",
              "max(_xs[_i + 1], _xs[_i])", "min(_xs[_i + 1], _xs[_i])"]


def _gen_fenetre_paire():
    for op in _OPS_PAIRE:
        src = ("def f(_xs):\n"
               f"    return [{op} for _i in range(len(_xs) - 1)]\n")
        yield src


# ─────────────────────────── SQUELETTE 5 : DP-1D à 2 états (lookback) ───────────────────────────
# def f(xs):
#     a, b = 0, 0
#     for x in xs: a, b = b, OP(b, a + x)
#     return RET
# Couvre house_robber / max(min)-sum-non-adjacent (la famille « choisir sans voisins »). OP/RET génériques.
_OPS_DP = ["max(_b, _a + _x)", "min(_b, _a + _x)", "_b + _a + _x"]
_RETS_DP = ["_b", "max(_a, _b)", "_a"]


def _gen_dp1d():
    for op in _OPS_DP:
        for ret in _RETS_DP:
            src = (
                "def f(_xs):\n"
                "    _a, _b = 0, 0\n"
                "    for _x in _xs:\n"
                f"        _a, _b = _b, {op}\n"
                f"    return {ret}\n"
            )
            yield src


# ─────────────────────────── SQUELETTE 6 : fold à PRÉDICAT (compter/sommer sous condition vs 0) ───────────────────────────
# def f(xs): return AGG(MAP for e in xs if e CMP 0)
_CMPS_PRED = ["> 0", "< 0", ">= 0", "<= 0", "== 0", "!= 0"]
_MAPS_PRED = [("compte", "1"), ("somme", "_e")]


def _gen_fold_predicat():
    for _, mp in _MAPS_PRED:
        for cmp in _CMPS_PRED:
            src = ("def f(_xs):\n"
                   f"    return sum({mp} for _e in _xs if _e {cmp})\n")
            yield src


# ─────────────────────────── SQUELETTE 7 : balayage comparant au PRÉCÉDENT (plus longue série) ───────────────────────────
# def f(xs):
#     best = cur = 1
#     for i in 1..len: cur = cur+1 if xs[i] CMP xs[i-1] else 1 ; best = AGG(best, cur)
#     return best
_CMPS_RUN = ["==", ">", "<", ">=", "<="]


def _gen_run_compare():
    for cmp in _CMPS_RUN:
        src = (
            "def f(_xs):\n"
            "    _best = _cur = 1\n"
            "    for _i in range(1, len(_xs)):\n"
            f"        _cur = _cur + 1 if _xs[_i] {cmp} _xs[_i - 1] else 1\n"
            "        _best = max(_best, _cur)\n"
            "    return _best\n"
        )
        yield src


# ─────────────────────────── SQUELETTE 8 : fréquence / argmax sur comptage (mode) ───────────────────────────
# def f(xs): return AGG(set(xs), key=lambda e: (xs.count(e), TIE))
# Couvre mode (plus fréquent, tie-break déterministe) et anti-mode. Comptage = nouvelle famille (dict implicite).
_AGGS_FREQ = ["max", "min"]
_TIES_FREQ = ["-_e", "_e"]


def _gen_frequence():
    for agg in _AGGS_FREQ:
        for tie in _TIES_FREQ:
            src = ("def f(_xs):\n"
                   f"    return {agg}(set(_xs), key=lambda _e: (_xs.count(_e), {tie}))\n")
            yield src
    # nombre de valeurs distinctes (comptage global).
    yield "def f(_xs):\n    return len(set(_xs))\n"


# ═══════════════════════ FAMILLE MULTI-ARG (entrées à 2 arguments) ═══════════════════════
# ─────────────────────────── SQUELETTE 9 : fenêtre glissante de taille k -> liste d'agrégats ───────────────────────────
# def f(xs, k): return [AGG(xs[i:i+k]) for i in range(len(xs)-k+1)]
_AGGS_WIN = [("sum", "sum"), ("max", "max"), ("min", "min")]


def _gen_fenetre_k_liste():
    for _, agg in _AGGS_WIN:
        src = ("def f(_xs, _k):\n"
               f"    return [{agg}(_xs[_i:_i + _k]) for _i in range(len(_xs) - _k + 1)]\n")
        yield src


# ─────────────────────────── SQUELETTE 10 : meilleure fenêtre de taille k -> scalaire ───────────────────────────
# def f(xs, k): return AGG2([AGG1(xs[i:i+k]) for i in range(len(xs)-k+1)])
def _gen_fenetre_k_scalaire():
    for _, a1 in _AGGS_WIN:
        for a2 in ("max", "min"):
            src = ("def f(_xs, _k):\n"
                   f"    return {a2}([{a1}(_xs[_i:_i + _k]) for _i in range(len(_xs) - _k + 1)])\n")
            yield src


# ─────────────────────────── SQUELETTE 11 : seuil VENANT DE L'ARG (compter/sommer/filtrer vs args[1]) ───────────────────────────
_CMPS_SEUIL = ["> _t", ">= _t", "< _t", "<= _t", "== _t", "!= _t"]


def _gen_seuil_arg():
    for cmp in _CMPS_SEUIL:
        yield f"def f(_xs, _t):\n    return sum(1 for _e in _xs if _e {cmp})\n"        # comptage
        yield f"def f(_xs, _t):\n    return sum(_e for _e in _xs if _e {cmp})\n"        # somme conditionnelle
        yield f"def f(_xs, _t):\n    return [_e for _e in _xs if _e {cmp}]\n"           # filtre -> liste


# ─────────────────────────── SQUELETTE 12 : DEUX LISTES alignées (zip) ───────────────────────────
_OPS_ZIP = ["_x + _y", "_x - _y", "_x * _y", "max(_x, _y)", "min(_x, _y)"]


def _gen_deux_listes():
    for op in _OPS_ZIP:
        yield f"def f(_a, _b):\n    return [{op} for _x, _y in zip(_a, _b)]\n"          # élément par élément -> liste
    yield "def f(_a, _b):\n    return sum(_x * _y for _x, _y in zip(_a, _b))\n"          # produit scalaire -> scalaire


# ─────────────────────────── SQUELETTE 13 : ALGÈBRE D'ENSEMBLES sur deux listes ───────────────────────────
def _gen_ensembles():
    yield "def f(_a, _b):\n    return sorted(set(_a) & set(_b))\n"                       # intersection
    yield "def f(_a, _b):\n    return sorted(set(_a) | set(_b))\n"                       # union
    yield "def f(_a, _b):\n    return sorted(set(_a) - set(_b))\n"                       # différence
    yield "def f(_a, _b):\n    return sorted(set(_a) ^ set(_b))\n"                       # différence symétrique
    # PRÉDICATS ensemblistes (sortie 0/1) : inclusion, sur-ensemble, disjonction, égalité.
    yield "def f(_a, _b):\n    return int(set(_a) <= set(_b))\n"                          # sous-ensemble
    yield "def f(_a, _b):\n    return int(set(_a) >= set(_b))\n"                          # sur-ensemble
    yield "def f(_a, _b):\n    return int(set(_a).isdisjoint(set(_b)))\n"                 # disjoints
    yield "def f(_a, _b):\n    return int(set(_a) == set(_b))\n"                          # égalité ensembliste


# ═══════════════════════ FAMILLE CHAÎNES (entrée = une chaîne) ═══════════════════════
# ─────────────────────────── SQUELETTE 14 : comptage de caractères par prédicat ───────────────────────────
_PREDS_CHAR = ["_c in 'aeiouAEIOU'", "_c.isdigit()", "_c.isupper()", "_c.islower()",
               "_c.isalpha()", "_c.isspace()", "_c in 'bcdfghjklmnpqrstvwxyz'"]


def _gen_char_count():
    for pred in _PREDS_CHAR:
        yield f"def f(_s):\n    return sum(1 for _c in _s if {pred})\n"


# ─────────────────────────── SQUELETTE 15 : transformation globale de chaîne -> chaîne ───────────────────────────
_TRANSFOS_STR = ["_s[::-1]", "_s.upper()", "_s.lower()", "_s.swapcase()",
                 "''.join(sorted(_s))", "''.join(dict.fromkeys(_s))"]


def _gen_transfo_str():
    for t in _TRANSFOS_STR:
        yield f"def f(_s):\n    return {t}\n"


# ─────────────────────────── SQUELETTE 16 : prédicat sur chaîne -> bool ───────────────────────────
def _gen_predicat_str():
    yield "def f(_s):\n    return _s == _s[::-1]\n"                       # palindrome
    yield "def f(_s):\n    return len(set(_s)) == len(_s)\n"              # tous caractères distincts


# ─────────────────────────── SQUELETTE 17 : opérations sur MOTS (split) ───────────────────────────
def _gen_mots():
    yield "def f(_s):\n    return len(_s.split())\n"                                      # nb de mots
    yield "def f(_s):\n    return [len(_w) for _w in _s.split()]\n"                       # longueurs des mots
    yield "def f(_s):\n    return max(_s.split(), key=len)\n"                             # mot le plus long
    yield "def f(_s):\n    return min(_s.split(), key=len)\n"                             # mot le plus court
    yield "def f(_s):\n    return ' '.join(_w[::-1] for _w in _s.split())\n"             # inverse chaque mot
    yield "def f(_s):\n    return ' '.join(_s.split()[::-1])\n"                           # mots en ordre inverse
    yield "def f(_s):\n    return ' '.join(sorted(_s.split()))\n"                         # mots triés


# ═══════════════════════ FAMILLE MATRICES (entrée = liste de listes) ═══════════════════════
# ─────────────────────────── SQUELETTE 18 : matrice -> liste (ligne/colonne/diagonale) ───────────────────────────
def _gen_matrice_liste():
    yield "def f(_m):\n    return [_v for _r in _m for _v in _r]\n"                       # aplatie
    yield "def f(_m):\n    return [sum(_r) for _r in _m]\n"                                # somme par ligne
    yield "def f(_m):\n    return [sum(_c) for _c in zip(*_m)]\n"                          # somme par colonne
    yield "def f(_m):\n    return [max(_r) for _r in _m]\n"                                # max par ligne
    yield "def f(_m):\n    return [min(_r) for _r in _m]\n"                                # min par ligne
    yield "def f(_m):\n    return [_m[_i][_i] for _i in range(len(_m))]\n"                 # diagonale
    yield "def f(_m):\n    return [list(_c) for _c in zip(*_m)]\n"                         # transposée
    yield "def f(_m):\n    return [_r[::-1] for _r in _m]\n"                               # miroir horizontal


# ─────────────────────────── SQUELETTE 19 : matrice -> scalaire (agrégat global) ───────────────────────────
def _gen_matrice_scalaire():
    yield "def f(_m):\n    return sum(sum(_r) for _r in _m)\n"                             # somme totale
    yield "def f(_m):\n    return max(max(_r) for _r in _m)\n"                             # max global
    yield "def f(_m):\n    return min(min(_r) for _r in _m)\n"                             # min global
    yield "def f(_m):\n    return sum(_m[_i][_i] for _i in range(len(_m)))\n"              # trace


# ═══════════════════════ FAMILLE INTERVALLES (entrée = liste de paires [début, fin]) — TRI-PUIS-BALAYAGE ═══════════════════════
# ─────────────────────────── SQUELETTE 20 : fusion d'intervalles -> liste d'intervalles ───────────────────────────
def _gen_intervalles():
    yield ("def f(_iv):\n    _out = []\n    for _a, _b in sorted(_iv):\n"
           "        if _out and _a <= _out[-1][1]:\n            _out[-1][1] = max(_out[-1][1], _b)\n"
           "        else:\n            _out.append([_a, _b])\n    return _out\n")                   # fusion (merge)
    yield ("def f(_iv):\n    _cnt = 0\n    _end = None\n"
           "    for _a, _b in sorted(_iv, key=lambda _p: _p[1]):\n"
           "        if _end is None or _a >= _end:\n            _cnt += 1\n            _end = _b\n    return _cnt\n")  # activité max
    yield ("def f(_iv):\n    _tot = 0\n    _cs = _ce = None\n    for _a, _b in sorted(_iv):\n"
           "        if _cs is None:\n            _cs, _ce = _a, _b\n        elif _a <= _ce:\n            _ce = max(_ce, _b)\n"
           "        else:\n            _tot += _ce - _cs\n            _cs, _ce = _a, _b\n"
           "    return _tot + (_ce - _cs if _cs is not None else 0)\n")                             # longueur couverte
    yield ("def f(_iv):\n    return max(_b for _a, _b in _iv) - min(_a for _a, _b in _iv)\n")       # étendue totale


# ═══════════════════════ FAMILLE GRAPHES (entrée = n sommets + liste d'arêtes [u,v]) ═══════════════════════
_UF = ("    _p = list(range(_n))\n    def _find(_x):\n        while _p[_x] != _x:\n"
       "            _p[_x] = _p[_p[_x]]\n            _x = _p[_x]\n        return _x\n")


def _gen_graphe():
    # degrés de chaque sommet -> liste.
    yield ("def f(_n, _e):\n    _d = [0] * _n\n    for _u, _v in _e:\n        _d[_u] += 1\n        _d[_v] += 1\n    return _d\n")
    # nombre de composantes connexes (union-find).
    yield ("def f(_n, _e):\n" + _UF + "    for _u, _v in _e:\n        _p[_find(_u)] = _find(_v)\n"
           "    return len({_find(_i) for _i in range(_n)})\n")
    # cycle non orienté ? (une arête relie deux sommets déjà unis) -> bool.
    yield ("def f(_n, _e):\n" + _UF + "    for _u, _v in _e:\n        _ru, _rv = _find(_u), _find(_v)\n"
           "        if _ru == _rv:\n            return True\n        _p[_ru] = _rv\n    return False\n")
    # connexe ? (une seule composante).
    yield ("def f(_n, _e):\n" + _UF + "    for _u, _v in _e:\n        _p[_find(_u)] = _find(_v)\n"
           "    return len({_find(_i) for _i in range(_n)}) == 1\n")


# ═══════════════════════ FAMILLE DP-2D (entrée = deux chaînes) — tables de programmation dynamique ═══════════════════════
def _gen_dp2d():
    # distance d'édition (Levenshtein).
    yield ("def f(_a, _b):\n    _m, _n = len(_a), len(_b)\n    _dp = [[0] * (_n + 1) for _ in range(_m + 1)]\n"
           "    for _i in range(_m + 1):\n        _dp[_i][0] = _i\n    for _j in range(_n + 1):\n        _dp[0][_j] = _j\n"
           "    for _i in range(1, _m + 1):\n        for _j in range(1, _n + 1):\n"
           "            _dp[_i][_j] = min(_dp[_i-1][_j] + 1, _dp[_i][_j-1] + 1,\n"
           "                              _dp[_i-1][_j-1] + (_a[_i-1] != _b[_j-1]))\n    return _dp[_m][_n]\n")
    # plus longue sous-séquence commune (longueur).
    yield ("def f(_a, _b):\n    _m, _n = len(_a), len(_b)\n    _dp = [[0] * (_n + 1) for _ in range(_m + 1)]\n"
           "    for _i in range(1, _m + 1):\n        for _j in range(1, _n + 1):\n"
           "            if _a[_i-1] == _b[_j-1]:\n                _dp[_i][_j] = _dp[_i-1][_j-1] + 1\n"
           "            else:\n                _dp[_i][_j] = max(_dp[_i-1][_j], _dp[_i][_j-1])\n    return _dp[_m][_n]\n")
    # plus longue sous-chaîne commune CONTIGUË (longueur).
    yield ("def f(_a, _b):\n    _m, _n = len(_a), len(_b)\n    _dp = [[0] * (_n + 1) for _ in range(_m + 1)]\n    _best = 0\n"
           "    for _i in range(1, _m + 1):\n        for _j in range(1, _n + 1):\n"
           "            if _a[_i-1] == _b[_j-1]:\n                _dp[_i][_j] = _dp[_i-1][_j-1] + 1\n"
           "                _best = max(_best, _dp[_i][_j])\n    return _best\n")


# ═══════════════════════ FAMILLE PILE / PARENTHÈSES (entrée = chaîne de crochets) ═══════════════════════
def _gen_pile():
    # équilibrage MULTI-délimiteurs (), [], {} par appariement de pile -> bool.
    yield ("def f(_s):\n    _st = []\n    _m = {')': '(', ']': '[', '}': '{'}\n    for _c in _s:\n"
           "        if _c in '([{':\n            _st.append(_c)\n        elif _c in _m:\n"
           "            if not _st or _st.pop() != _m[_c]:\n                return False\n    return not _st\n")
    # profondeur d'imbrication MAX (un seul type) -> entier.
    yield ("def f(_s):\n    _d = _best = 0\n    for _c in _s:\n        if _c in '([{':\n            _d += 1\n"
           "            _best = max(_best, _d)\n        elif _c in ')]}':\n            _d -= 1\n    return _best\n")
    # nombre d'ouvrants non appariés (déficit) -> entier.
    yield ("def f(_s):\n    _open = _add = 0\n    for _c in _s:\n        if _c in '([{':\n            _open += 1\n"
           "        elif _c in ')]}':\n            if _open > 0:\n                _open -= 1\n            else:\n                _add += 1\n"
           "    return _add + _open\n")


# ─────────────────────────── FAMILLE ARITHMÉTIQUE SCALAIRE (théorie des nombres / logique / géométrie) ──
# Toute la branche B-NEC « scalaire » manquait : les squelettes ci-dessus opèrent sur des SÉQUENCES, jamais
# sur un entier nu. Ces 4 générateurs couvrent le socle calculable de la Partie I de la taxonomie (sciences
# formelles) : réduction sur un intervalle [a..b] dérivé de n, réduction sur les chiffres/bits de n,
# expression binaire sur (a,b) (+ Euclide), expression unaire sur n. Bornés/sound : l'anti-coïncidence par
# sondes fraîches (régime entiers-purs, voir _sonde_inputs) tranche, et l'oracle désambiguïse activement.

def _gen_arith_intervalle():
    # def f(n): acc=INIT ; for d in range(LO, HI): [if n%d==0:] acc = STEP ; return acc
    # Couvre : factorielle (∏ 1..n), nb_diviseurs, somme_diviseurs, somme/produit 1..n.
    for init in ("0", "1"):
        for lo in ("1", "2"):
            for hi in ("_n + 1", "_n"):
                for pred in ("", "if _n % _d == 0: "):
                    for terme in ("_d", "1", "_d * _d"):       # _d*_d : somme/produit des carrés sur l'intervalle
                        for op in ("+", "*"):
                            yield (
                                "def f(_n):\n"
                                f"    _acc = {init}\n"
                                f"    for _d in range({lo}, {hi}):\n"
                                f"        {pred}_acc = _acc {op} {terme}\n"
                                "    return _acc\n"
                            )
    # Primalité : aucun diviseur dans [2, n) et n >= 2 -> 1/0 (variantes de borne supérieure équivalentes).
    for hi in ("_n", "int(_n ** 0.5) + 1"):
        yield (
            "def f(_n):\n"
            "    if _n < 2:\n        return 0\n"
            f"    for _d in range(2, {hi}):\n"
            "        if _n % _d == 0:\n            return 0\n"
            "    return 1\n"
        )


def _gen_arith_chiffres():
    # def f(n): acc=INIT ; for c in SRC: acc = STEP ; return acc — réduction sur chiffres OU bits.
    # Couvre : somme_chiffres, produit_chiffres, nb_chiffres, popcount, longueur binaire.
    for src in ("str(_n)", "bin(_n)[2:]"):
        for init in ("0", "1"):
            for terme in ("int(_c)", "1", "(_c == '1')"):
                for op in ("+", "*"):
                    yield (
                        "def f(_n):\n"
                        f"    _acc = {init}\n"
                        f"    for _c in {src}:\n"
                        f"        _acc = _acc {op} {terme}\n"
                        "    return _acc\n"
                    )


def _gen_arith_binaire():
    # def f(a, b): return EXPR — expressions binaires bornées (logique, géométrie, arithmétique modulaire).
    exprs = [
        "int(bool(_a) ^ bool(_b))", "int((not _a) or _b)", "int(bool(_a) and bool(_b))",
        "int(bool(_a) or _b)", "_a * _a + _b * _b", "_a % _b", "_a // _b", "_a + _b",
        "_a * _b", "abs(_a - _b)", "max(_a, _b)", "min(_a, _b)", "_a ** _b",
        "int(not (_a and _b))", "int(not (_a or _b))", "int(bool(_a) == bool(_b))",   # nand, nor, equiv
        "_a ^ _b", "_a & _b", "_a | _b", "bin(_a ^ _b).count('1')",                   # bitops + distance Hamming
    ]
    for e in exprs:
        yield f"def f(_a, _b):\n    return {e}\n"
    # Euclide (PGCD) : algorithme à condition, schéma figé (le COMMENT, pas le PLUS).
    yield "def f(_a, _b):\n    while _b:\n        _a, _b = _b, _a % _b\n    return _a\n"


def _gen_arith_unaire():
    # def f(n): return EXPR — expressions unaires bornées (racine entière, parité, carré, inversion, bits…).
    for e in ("int(_n ** 0.5)", "_n * _n", "abs(_n)", "_n % 2", "_n // 2", "-_n", "_n + 1", "_n - 1",
              "int(str(_n)[::-1])", "int(_n > 0 and (_n & (_n - 1)) == 0)", "bin(_n).count('1')",
              "2 ** _n", "_n * (_n + 1) // 2", "_n * (_n - 1) // 2"):     # cardinal des parties (2^n), nombres triangulaires
        yield f"def f(_n):\n    return {e}\n"


def _gen_arith_recurrence2():
    # def f(n): a,b=I0,I1 ; for _ in range(n): a,b = b, OP(a,b) ; return RET — récurrence 2 états (Fibonacci, Lucas).
    for i0, i1 in (("0", "1"), ("2", "1"), ("1", "1"), ("1", "3")):
        for op in ("_a + _b", "_a + _b + 1", "2 * _b + _a"):
            for ret in ("_a", "_b"):
                yield (
                    "def f(_n):\n"
                    f"    _a, _b = {i0}, {i1}\n"
                    "    for _ in range(_n):\n"
                    f"        _a, _b = _b, {op}\n"
                    f"    return {ret}\n"
                )


def _gen_arith_while():
    # def f(n): c=0 ; for _ in range(GARDE): if not COND: break ; n=TRANSFORM ; c+=1 ; return RET
    # Itération jusqu'à condition (Collatz, racine numérique, retrait de chiffres). La GARDE range() BORNE
    # structurellement les itérations -> jamais de boucle infinie en in-process (un cas non-terminant atteint la
    # garde, diverge de l'oracle, et est rejeté par la vérif finale -> None, jamais un faux ni un hang).
    transforms = (
        "_n // 2 if _n % 2 == 0 else 3 * _n + 1",         # Collatz
        "sum(int(_c) for _c in str(_n))",                  # somme des chiffres -> racine numérique
        "_n // 10",                                         # retrait du dernier chiffre
    )
    conds = ("_n != 1", "_n > 9", "_n > 1", "_n != 0")
    for t in transforms:
        for cond in conds:
            for ret in ("_c", "_n"):
                yield (
                    "def f(_n):\n    _c = 0\n"
                    "    for _ in range(200):\n"                # GARDE : borne le coût + interdit le hang in-process
                    f"        if not ({cond}):\n            break\n"
                    f"        _n = {t}\n        _c += 1\n"
                    f"    return {ret}\n"
                )


def _gen_arith_compose1():
    # def f(n): composition de primitives bornées sur UN entier — parfait/abondant/déficient, Catalan, totient.
    fact = "_F = lambda _k: 1 if _k < 2 else _k * _F(_k - 1)\n"
    pgcd = "def _g(_x, _y):\n        while _y:\n            _x, _y = _y, _x % _y\n        return _x\n"
    for cmp in ("==", ">", "<"):                            # parfait / abondant / déficient (gardé n>0)
        yield (f"def f(_n):\n    return int(_n > 0 and "
               f"sum(_d for _d in range(1, _n) if _n % _d == 0) {cmp} _n)\n")
    yield "def f(_n):\n    " + fact + "    return _F(2 * _n) // (_F(_n + 1) * _F(_n))\n"   # Catalan
    yield ("def f(_n):\n    " + pgcd
           + "    return sum(1 for _k in range(1, _n + 1) if _g(_k, _n) == 1)\n")           # totient d'Euler
    # composition avec un test de PRIMALITÉ embarqué : nb de premiers ≤ n (π(n)), somme des premiers ≤ n.
    prime = "_p = lambda _k: _k > 1 and all(_k % _d for _d in range(2, int(_k ** 0.5) + 1))\n"
    yield ("def f(_n):\n    " + prime + "    return sum(1 for _k in range(2, _n + 1) if _p(_k))\n")
    yield ("def f(_n):\n    " + prime + "    return sum(_k for _k in range(2, _n + 1) if _p(_k))\n")
    # agrégat CUMULÉ d'une mesure sur [0..n] : somme des bits posés jusqu'à n, somme des diviseurs-compte, etc.
    yield "def f(_n):\n    return sum(bin(_i).count('1') for _i in range(_n + 1))\n"           # cumul des bits posés
    yield "def f(_n):\n    return sum(int(_c) for _k in range(_n + 1) for _c in str(_k))\n"     # cumul des chiffres


def _gen_arith_reduction2():
    # def f(n, r): acc=INIT ; for i in range(r): acc = acc OP TERM(n, i) ; return acc — réduction 2-arg.
    # Couvre : arrangements nPr (∏_{i<r}(n-i)), produit/somme de suites dérivées des deux args.
    for init in ("0", "1"):
        for terme in ("_n - _i", "_n + _i", "_i", "_n"):
            for op in ("+", "*"):
                yield (
                    "def f(_n, _r):\n"
                    f"    _acc = {init}\n"
                    "    for _i in range(_r):\n"
                    f"        _acc = _acc {op} ({terme})\n"
                    "    return _acc\n"
                )


def _gen_arith_compose2():
    # def f(a, b): return EXPR composant des PRIMITIVES bornées (factorielle, pgcd) — couvre nCr, ppcm.
    # Primitives locales définies dans le corps (sound : re-vérifiées par le juge comme tout le reste).
    fact = "_F = lambda _k: 1 if _k < 2 else _k * _F(_k - 1)\n"
    pgcd = "def _g(_x, _y):\n        while _y:\n            _x, _y = _y, _x % _y\n        return _x\n"
    # nCr / nPr GARDÉS sur leur domaine : 0 si _b > _a ou _b < 0 (sinon la factorielle d'un négatif ment).
    yield ("def f(_a, _b):\n    " + fact
           + "    return 0 if _b < 0 or _b > _a else _F(_a) // (_F(_b) * _F(_a - _b))\n")   # nCr
    yield ("def f(_a, _b):\n    " + fact
           + "    return 0 if _b < 0 or _b > _a else _F(_a) // _F(_a - _b)\n")               # nPr
    yield ("def f(_a, _b):\n    " + pgcd
           + "    return 0 if not _a or not _b else _a * _b // _g(_a, _b)\n")                  # ppcm (0 si un arg nul)
    yield "def f(_a, _b):\n    " + pgcd + "    return _g(_a, _b)\n"                            # pgcd (redondant, sûr)


def _gen_arith_ternaire():
    # def f(a, b, c): return EXPR — 3 entiers (arithmétique modulaire, combinaisons linéaires bornées).
    for e in ("pow(_a, _b, _c)", "(_a + _b) % _c", "(_a * _b) % _c", "_a * _b + _c",
              "_a + _b + _c", "(_a ** _b) % _c", "_a % _b % _c",
              "int(_a * _a + _b * _b == _c * _c)",            # triplet pythagoricien
              "int((_a + _b + _c) >= 2)", "max(_a, _b, _c)", "min(_a, _b, _c)"):  # majorité bits, extrema
        yield f"def f(_a, _b, _c):\n    return {e}\n"


def _gen_arith_base2():
    # def f(n, b): réduction sur les CHIFFRES de n en base b (b>=2) — famille « représentation en base paramétrée ».
    # Couvre : somme_chiffres_base, produit_chiffres_base, longueur_base (nb de chiffres). GARDE range() = pas de hang
    # même si une sonde donne b<2 (n//1 boucle, n//0 lève) : ces entrées sont rejetées par l'oracle, jamais un faux.
    for init in ("0", "1"):
        for terme in ("_n % _b", "1"):
            for op in ("+", "*"):
                yield (
                    "def f(_n, _b):\n"
                    f"    _acc = {init}\n"
                    "    for _ in range(200):\n"
                    "        if _n <= 0:\n            break\n"
                    f"        _acc = _acc {op} ({terme})\n"
                    "        _n //= _b\n"
                    "    return _acc\n"
                )
    # longueur_base : nb de chiffres, avec le cas n==0 -> 1 chiffre (le compteur seul rendrait 0).
    yield (
        "def f(_n, _b):\n"
        "    _c = 1 if _n == 0 else 0\n"
        "    for _ in range(200):\n"
        "        if _n <= 0:\n            break\n"
        "        _c += 1\n        _n //= _b\n"
        "    return _c\n"
    )


def _gen_arith_fold_liste_scalaire():
    # def f(xs, x): _acc=INIT ; for _c in xs: _acc = EXPR(_acc, _x, _c) ; return _acc — fold d'une LISTE avec un SCALAIRE.
    # Couvre : Horner (évaluation polynomiale acc*x+c), évaluations/accumulations dépendant d'un paramètre scalaire.
    for init in ("0", "1"):
        for body in ("_acc * _x + _c", "_acc + _c * _x", "_acc + _c", "_acc * _x"):
            yield (
                "def f(_xs, _x):\n"
                f"    _acc = {init}\n"
                "    for _c in _xs:\n"
                f"        _acc = {body}\n"
                "    return _acc\n"
            )


def _gen_arith_determinant():
    # def f(m): déterminant d'une matrice carrée (développement de Laplace récursif) — générique n×n (couvre 2×2, 3×3…).
    yield (
        "def f(_m):\n"
        "    def _det(_M):\n"
        "        _k = len(_M)\n"
        "        if _k == 1:\n            return _M[0][0]\n"
        "        _t = 0\n"
        "        for _j in range(_k):\n"
        "            _sub = [[_M[_i][_c] for _c in range(_k) if _c != _j] for _i in range(1, _k)]\n"
        "            _t += ((-1) ** _j) * _M[0][_j] * _det(_sub)\n"
        "        return _t\n"
        "    return _det(_m)\n"
    )


def _gen_arith_predicat_chiffres():
    # def f(n): prédicat comparant n à un AGRÉGAT de ses chiffres — famille « nombres spéciaux digit-agrégat ».
    # Couvre : Harshad (n % somme_chiffres == 0), Armstrong (somme des d**k == n), divisibilité par nb de chiffres.
    for agg in ("sum(int(_c) for _c in str(_n))", "len(str(_n))"):
        yield (f"def f(_n):\n    _t = {agg}\n    return int(_n > 0 and _t != 0 and _n % _t == 0)\n")
    for p in ("len(str(_n))", "3", "2"):
        yield (f"def f(_n):\n    return int(sum(int(_c) ** ({p}) for _c in str(_n)) == _n)\n")


def _gen_arith_factorisation():
    # def f(n): décomposition par DIVISIONS SUCCESSIVES (schéma figé reconnu, comme Euclide) — la boucle `_d*_d<=_m`
    # TERMINE structurellement. Couvre : factorisation en premiers (avec multiplicité), facteurs premiers DISTINCTS.
    yield (
        "def f(_n):\n    _out = []\n    _m = _n\n    _d = 2\n"
        "    while _d * _d <= _m:\n"
        "        while _m % _d == 0:\n            _out.append(_d)\n            _m //= _d\n"
        "        _d += 1\n"
        "    if _m > 1:\n        _out.append(_m)\n    return _out\n"
    )
    yield (
        "def f(_n):\n    _out = []\n    _m = _n\n    _d = 2\n"
        "    while _d * _d <= _m:\n"
        "        if _m % _d == 0:\n            _out.append(_d)\n"
        "            while _m % _d == 0:\n                _m //= _d\n"
        "        _d += 1\n"
        "    if _m > 1:\n        _out.append(_m)\n    return _out\n"
    )


def _gen_arith_reduit_fraction():
    # def f(a, b): réduit une paire (a, b) par leur PGCD -> (a//g, b//g). Tuple de sortie (fraction irréductible).
    pgcd = "def _g(_x, _y):\n        while _y:\n            _x, _y = _y, _x % _y\n        return _x\n"
    yield ("def f(_a, _b):\n    " + pgcd
           + "    _k = _g(_a, _b)\n    if _k == 0:\n        return (_a, _b)\n    return (_a // _k, _b // _k)\n")


def _gen_arith_serie3():
    # def f(a, r, n): accumulation de n termes d'une suite paramétrée par (a, r) — série GÉOMÉTRIQUE ou ARITHMÉTIQUE.
    for upd in ("_t = _t * _r", "_t = _t + _r"):       # géométrique (×r) / arithmétique (+r)
        yield (
            "def f(_a, _r, _n):\n    _s = 0\n    _t = _a\n"
            "    for _ in range(_n):\n        _s = _s + _t\n"
            f"        {upd}\n"
            "    return _s\n"
        )


def _gen_liste_indexee():
    # def f(xs): transformation d'une LISTE dépendant de l'INDICE et de la longueur — sortie LISTE.
    # Couvre : dérivée d'un polynôme (coeffs poids-fort->faible : c[i]*(n-1-i)), mise à l'échelle par l'indice.
    yield ("def f(_xs):\n    _n = len(_xs)\n"
           "    return [_xs[_i] * (_n - 1 - _i) for _i in range(_n - 1)]\n")     # dérivée polynomiale
    yield ("def f(_xs):\n    return [_xs[_i] * _i for _i in range(len(_xs))]\n")  # échelle par indice
    yield ("def f(_xs):\n    return [_xs[_i] + _i for _i in range(len(_xs))]\n")  # décalage par indice


def _gen_arith_base_liste():
    # def f(n, b): CHIFFRES de n en base b sous forme de LISTE (poids fort -> faible). GARDE range() = pas de hang.
    yield (
        "def f(_n, _b):\n    if _n == 0:\n        return [0]\n    _out = []\n"
        "    for _ in range(200):\n"
        "        if _n <= 0:\n            break\n"
        "        _out.append(_n % _b)\n        _n //= _b\n"
        "    return _out[::-1]\n"
    )


def _gen_liste_mode_freq():
    # def f(xs): valeur de fréquence EXTRÊME — mode (la plus fréquente, départage par la plus petite) / la moins fréquente.
    yield "def f(_xs):\n    return min(set(_xs), key=lambda _v: (-_xs.count(_v), _v))\n"      # mode
    yield "def f(_xs):\n    return min(set(_xs), key=lambda _v: (_xs.count(_v), _v))\n"        # moins fréquente


def _gen_compte_fenetre3():
    # def f(xs): comptage par FENÊTRE glissante de 3 — pics locaux (sommets) / creux locaux (vallées).
    yield ("def f(_xs):\n    return sum(1 for _i in range(1, len(_xs) - 1) "
           "if _xs[_i] > _xs[_i - 1] and _xs[_i] > _xs[_i + 1])\n")
    yield ("def f(_xs):\n    return sum(1 for _i in range(1, len(_xs) - 1) "
           "if _xs[_i] < _xs[_i - 1] and _xs[_i] < _xs[_i + 1])\n")


def _gen_liste_rotation():
    # def f(xs): rotation circulaire d'un cran (gauche / droite).
    yield "def f(_xs):\n    return _xs[1:] + _xs[:1]\n"        # gauche
    yield "def f(_xs):\n    return _xs[-1:] + _xs[:-1]\n"      # droite


def _gen_stat_exacte():
    # def f(xs): STATISTIQUE EXACTE en entiers (évite les flottants) — somme des écarts au carré ÉCHELLÉE par n :
    # Σ(n*x - Σx)² = n³·variance (entier). Permet de traiter variance/dispersion de façon exacte et vérifiable.
    yield ("def f(_xs):\n    _n = len(_xs)\n    _s = sum(_xs)\n"
           "    return sum((_n * _x - _s) ** 2 for _x in _xs)\n")
    # amplitude (étendue) = max - min, exacte.
    yield "def f(_xs):\n    return max(_xs) - min(_xs)\n"


def _gen_scan_accumule_liste():
    # def f(xs): SCAN à accumulateur -> liste des préfixes (somme/produit/xor cumulés, max/min courant).
    for ini, op in (("0", "+"), ("1", "*"), ("0", "^"), ("0", "|"), ("-1", "&")):
        yield (
            "def f(_xs):\n    _acc = " + ini + "\n    _out = []\n"
            "    for _x in _xs:\n        _acc = _acc " + op + " _x\n        _out.append(_acc)\n"
            "    return _out\n"
        )
    for agg in ("max", "min"):
        yield (
            "def f(_xs):\n    _out = []\n"
            "    for _i in range(len(_xs)):\n"
            f"        _out.append(_xs[_i] if _i == 0 else {agg}(_out[-1], _xs[_i]))\n"
            "    return _out\n"
        )


def _gen_compte_paires():
    # def f(xs): nombre de PAIRES (i<j) vérifiant une relation entre xs[i] et xs[j] — inversions, paires égales, etc.
    for rel in (">", "<", "==", "!="):
        yield (
            "def f(_xs):\n    return sum(1 for _i in range(len(_xs)) "
            f"for _j in range(_i + 1, len(_xs)) if _xs[_i] {rel} _xs[_j])\n"
        )


def _gen_iter_cycle():
    # def f(n): itération d'une transformation digit-agrégat avec DÉTECTION DE CYCLE -> atteint 1 ? (nombre heureux).
    # GARDE range + l'ensemble `_seen` bornent le coût ; un cycle ≠ 1 termine via `_n in _seen`.
    for t in ("sum(int(_c) ** 2 for _c in str(_n))", "sum(int(_c) for _c in str(_n))"):
        yield (
            "def f(_n):\n    _seen = set()\n"
            "    for _ in range(1000):\n"
            "        if _n == 1 or _n in _seen:\n            break\n"
            f"        _seen.add(_n)\n        _n = {t}\n"
            "    return int(_n == 1)\n"
        )


def _gen_arith_bell():
    # def f(n): nombre de Bell B(n) (partitions d'un n-ensemble) — triangle de Bell. Primitive combinatoire reconnue.
    yield (
        "def f(_n):\n    if _n == 0:\n        return 1\n    _row = [1]\n"
        "    for _i in range(1, _n + 1):\n        _nr = [_row[-1]]\n"
        "        for _x in _row:\n            _nr.append(_nr[-1] + _x)\n        _row = _nr\n"
        "    return _row[0]\n"
    )


def _gen_chaine_decalee():
    # def f(s, k): chiffrement par DÉCALAGE (César) des lettres minuscules a-z modulo 26 ; autres caractères inchangés.
    yield ("def f(_s, _k):\n    return ''.join("
           "chr((ord(_c) - 97 + _k) % 26 + 97) if 'a' <= _c <= 'z' else _c for _c in _s)\n")


def _gen_fold_arith_liste():
    # def f(xs): réduction d'une LISTE par un opérateur de théorie des nombres — PGCD / PPCM de la liste (abs : conforme
    # à math.gcd/lcm). Couvre « PGCD/PPCM d'un ensemble de nombres ».
    g = "def _g(_x, _y):\n        while _y:\n            _x, _y = _y, _x % _y\n        return _x\n"
    yield ("def f(_xs):\n    " + g
           + "    _r = 0\n    for _v in _xs:\n        _r = _g(abs(_r), abs(_v))\n    return _r\n")     # PGCD liste
    yield ("def f(_xs):\n    " + g
           + "    _r = 1\n    for _v in _xs:\n        _r = _r * abs(_v) // _g(_r, abs(_v)) if _v else 0\n"
           "    return _r\n")                                                                            # PPCM liste


def _gen_arith_recurrence_mod():
    # def f(n, m): n-ième terme d'une récurrence 2 états RÉDUITE modulo m (Fibonacci mod m, Lucas mod m…). m>0.
    for i0, i1 in (("0", "1"), ("2", "1")):
        yield (
            "def f(_n, _m):\n"
            f"    _a, _b = {i0}, {i1}\n"
            "    for _ in range(_n):\n        _a, _b = _b, (_a + _b) % _m\n"
            "    return _a % _m\n"
        )


def _gen_arith_racine_predicat():
    # def f(n): prédicats/valeurs liés à la RACINE entière — carré parfait, cube parfait (n>=0).
    yield ("def f(_n):\n    _r = int(_n ** 0.5)\n"
           "    return int(_r * _r == _n or (_r + 1) * (_r + 1) == _n)\n")              # carré parfait
    yield ("def f(_n):\n    _r = round(_n ** (1.0 / 3))\n"
           "    return int(_r ** 3 == _n or (_r + 1) ** 3 == _n or (_r - 1) ** 3 == _n)\n")  # cube parfait


def _gen_arith_while_extremum():
    # def f(n): valeur EXTRÊME atteinte le long d'une trajectoire bornée (max/min d'une orbite de Collatz). GARDE range.
    for agg in ("max", "min"):
        yield (
            "def f(_n):\n    _m = _n\n"
            "    for _ in range(500):\n"
            "        if _n == 1:\n            break\n"
            "        _n = _n // 2 if _n % 2 == 0 else 3 * _n + 1\n"
            f"        _m = {agg}(_m, _n)\n"
            "    return _m\n"
        )


def _gen_arith_partitions():
    # def f(n): nombre de PARTITIONS d'entier p(n) — DP « monnaie » (parts 1..n). Primitive combinatoire reconnue.
    yield (
        "def f(_n):\n    _dp = [1] + [0] * _n\n"
        "    for _k in range(1, _n + 1):\n"
        "        for _j in range(_k, _n + 1):\n            _dp[_j] += _dp[_j - _k]\n"
        "    return _dp[_n]\n"
    )


def _gen_arith_stirling2():
    # def f(n, k): nombres de Stirling de 2e espèce S(n,k) (partitions d'un n-ensemble en k blocs) — DP par récurrence
    # S(n,k) = k*S(n-1,k) + S(n-1,k-1). Couvre aussi Stirling-like via la même table.
    yield (
        "def f(_n, _k):\n    _dp = [[0] * (_k + 1) for _ in range(_n + 1)]\n"
        "    _dp[0][0] = 1\n"
        "    for _i in range(1, _n + 1):\n"
        "        for _j in range(1, _k + 1):\n"
        "            _dp[_i][_j] = _j * _dp[_i - 1][_j] + _dp[_i - 1][_j - 1]\n"
        "    return _dp[_n][_k]\n"
    )


def _gen_arith_mod_inverse():
    # def f(a, m): inverse modulaire de a mod m par recherche bornée [0, m) ; 0 si aucun (a non inversible). m>0.
    yield (
        "def f(_a, _m):\n    if _m <= 0:\n        return 0\n    _a %= _m\n"
        "    for _x in range(_m):\n        if (_a * _x) % _m == 1:\n            return _x\n"
        "    return 0\n"
    )


def _gen_poly_mult():
    # def f(p, q): produit de deux polynômes (CONVOLUTION des coefficients) -> liste de longueur len(p)+len(q)-1.
    yield (
        "def f(_p, _q):\n    _out = [0] * (len(_p) + len(_q) - 1)\n"
        "    for _i in range(len(_p)):\n        for _j in range(len(_q)):\n"
        "            _out[_i + _j] += _p[_i] * _q[_j]\n"
        "    return _out\n"
    )


def _gen_matrice_binaire():
    # def f(A, B): opérations sur DEUX matrices de même forme — addition/soustraction/Hadamard (élémentaires) + PRODUIT.
    for op in ("+", "-", "*"):
        yield (f"def f(_A, _B):\n"
               f"    return [[_A[_i][_j] {op} _B[_i][_j] for _j in range(len(_A[0]))] "
               f"for _i in range(len(_A))]\n")
    yield (
        "def f(_A, _B):\n"
        "    return [[sum(_A[_i][_t] * _B[_t][_j] for _t in range(len(_B))) "
        "for _j in range(len(_B[0]))] for _i in range(len(_A))]\n"
    )


def _gen_arith_predicat_modulaire():
    # def f(n): prédicat de DIVISIBILITÉ par des modules constants — famille « règles modulaires ». La STRUCTURE est
    # générique (divisibilité simple, ET de deux modules, règle imbriquée a|n ET (¬b|n OU c|n)) ; les CONSTANTES sont
    # choisies par la recherche + désambiguïsées par l'oracle (comme nCr émerge de la famille factorielle). Couvre :
    # divisibilité, FizzBuzz-prédicat, et l'ANNÉE BISSEXTILE grégorienne = instance (4, 100, 400) de la règle imbriquée.
    mods = (2, 3, 4, 5, 7, 9, 10, 100, 400)
    for a in mods:
        yield f"def f(_n):\n    return int(_n % {a} == 0)\n"
    for a, b in ((3, 5), (2, 3), (4, 6)):
        yield f"def f(_n):\n    return int(_n % {a} == 0 and _n % {b} == 0)\n"
    # règle imbriquée « grégorienne » : a | n ET (¬(b | n) OU c | n). Grille de triplets ; l'oracle élit le bon.
    for a, b, c in ((4, 100, 400), (2, 4, 8), (3, 9, 27)):
        yield (f"def f(_n):\n    return int(_n % {a} == 0 and "
               f"(_n % {b} != 0 or _n % {c} == 0))\n")


_SQUELETTES = [_gen_balayage, _gen_deux_pointeurs, _gen_scan_liste, _gen_fenetre_paire,
               _gen_dp1d, _gen_fold_predicat, _gen_run_compare, _gen_frequence,
               _gen_fenetre_k_liste, _gen_fenetre_k_scalaire, _gen_seuil_arg,
               _gen_deux_listes, _gen_ensembles,
               _gen_char_count, _gen_transfo_str, _gen_predicat_str, _gen_mots,
               _gen_matrice_liste, _gen_matrice_scalaire, _gen_intervalles, _gen_graphe, _gen_dp2d, _gen_pile,
               _gen_arith_intervalle, _gen_arith_chiffres, _gen_arith_binaire, _gen_arith_unaire,
               _gen_arith_reduction2, _gen_arith_compose2, _gen_arith_ternaire,
               _gen_arith_recurrence2, _gen_arith_while, _gen_arith_compose1,
               _gen_arith_base2, _gen_arith_fold_liste_scalaire, _gen_arith_determinant,
               _gen_arith_predicat_chiffres, _gen_arith_predicat_modulaire,
               _gen_arith_factorisation, _gen_arith_reduit_fraction, _gen_arith_serie3,
               _gen_liste_indexee, _gen_arith_base_liste, _gen_poly_mult, _gen_matrice_binaire,
               _gen_arith_partitions, _gen_arith_stirling2, _gen_arith_mod_inverse,
               _gen_fold_arith_liste, _gen_arith_recurrence_mod, _gen_arith_racine_predicat,
               _gen_arith_while_extremum, _gen_arith_bell, _gen_chaine_decalee,
               _gen_scan_accumule_liste, _gen_compte_paires, _gen_iter_cycle,
               _gen_liste_mode_freq, _gen_compte_fenetre3, _gen_liste_rotation, _gen_stat_exacte]


def _sonde_inputs(exemples, rng):
    """Génère des ENTRÉES fraîches de même FORME que les exemples (mutation + aléatoire), pour discriminer les
    survivants par leur comportement (anti-coïncidence). Ne dépend PAS de la sortie : juste la structure des args.

    CONSCIENT DES CONTRAINTES MULTI-ARG : un int à côté d'une liste est parfois généré comme une TAILLE/INDICE VALIDE
    [1..len] (fenêtre k, seuil) ; deux listes partagent une longueur et un POOL de valeurs (pour que zip s'aligne et
    que les ensembles se recoupent). Sinon les sondes crasheraient (k>len) ou seraient dégénérées (intersection vide)."""
    bornes = (-9, 12)

    def _rand_list(n=None, pool=None):
        if n is None:
            n = rng.randint(1, 7)
        if pool is not None:
            return [rng.choice(pool) for _ in range(n)]
        return [rng.randint(*bornes) for _ in range(n)]

    def _rand_args(modele):
        types = [type(a) for a in modele]
        # cas ENTIERS PURS (1 ou 2 ints, aucune liste/chaîne) : régime THÉORIE DES NOMBRES. Petits entiers
        # POSITIFS (range/diviseurs/chiffres ont besoin de n>0 pour discriminer) + 0/1 (cas logique/limite).
        # Sûr : AUCUN squelette pré-existant ne prend un modèle tout-entier -> n'altère pas leurs sondes.
        if 1 <= len(modele) <= 3 and all(t is int for t in types):
            def _pos():
                return rng.choice([0, 1, 2, 3] + [rng.randint(2, 20)])
            return tuple(_pos() for _ in modele)
        # cas DEUX MATRICES : matrices CARRÉES n×n de même taille (addition/Hadamard ET produit matriciel tous valides).
        if (len(modele) == 2 and types == [list, list]
                and modele[0] and isinstance(modele[0][0], list)
                and modele[1] and isinstance(modele[1][0], list)):
            n = max(1, len(modele[0]))
            return ([[rng.randint(*bornes) for _ in range(n)] for _ in range(n)],
                    [[rng.randint(*bornes) for _ in range(n)] for _ in range(n)])
        # cas DEUX LISTES : longueur partagée + pool de valeurs commun (alignement zip + recouvrement d'ensembles).
        if len(modele) == 2 and types == [list, list]:
            n = rng.randint(1, 7)
            pool = [rng.randint(-6, 6) for _ in range(rng.randint(3, 7))]
            return (_rand_list(n, pool), _rand_list(n, pool))
        # cas DEUX CHAÎNES : alphabet PARTAGÉ et petit (sinon LCS toujours 0 / edit = longueur max -> indiscriminant).
        if len(modele) == 2 and types == [str, str]:
            alpha = "abcd"
            def _s():
                return "".join(rng.choice(alpha) for _ in range(rng.randint(0, 6)))
            return (_s(), _s())
        # cas (INT, ARÊTES) : graphe = n sommets + liste d'arêtes [u,v] avec 0<=u,v<n (références valides).
        if len(modele) == 2 and types == [int, list]:
            n = rng.randint(1, 6)
            e = [[rng.randint(0, n - 1), rng.randint(0, n - 1)] for _ in range(rng.randint(0, 7))]
            return (n, e)
        # cas (LISTE, INT) : l'int est SOIT une valeur, SOIT une taille/indice valide [1..len] (fenêtre k, seuil).
        if len(modele) == 2 and types == [list, int]:
            xs = _rand_list()
            if rng.random() < 0.6:
                k = rng.randint(1, len(xs))                  # taille/indice valide
            else:
                k = rng.randint(*bornes)                     # valeur libre (seuil)
            return (xs, k)
        # défaut : chaque arg indépendamment.
        def _rand_brackets():
            return "".join(rng.choice("()[]{}") for _ in range(rng.randint(0, 8)))

        def _rand_str():
            # alphabet RICHE (voyelles/consonnes/chiffres/MAJ/espace) pour discriminer les prédicats de caractères ;
            # parfois une chaîne MULTI-MOTS (espaces) pour les opérations sur mots ; parfois un palindrome.
            alpha = "aeiouxyzBCD 123"
            if rng.random() < 0.35:                          # multi-mots
                mots = ["".join(rng.choice("aeiouxyzBCD") for _ in range(rng.randint(1, 4)))
                        for _ in range(rng.randint(1, 4))]
                return " ".join(mots)
            s = "".join(rng.choice(alpha) for _ in range(rng.randint(1, 8)))
            if rng.random() < 0.2:                           # palindrome occasionnel
                s = s + s[::-1]
            return s

        def _rand_comme(val):
            if isinstance(val, bool):
                return rng.choice([True, False])
            if isinstance(val, int):
                return rng.randint(*bornes)
            if isinstance(val, str):
                if val and all(_c in "()[]{}" for _c in val):   # chaîne de PARENTHÈSES -> sondes à crochets
                    return _rand_brackets()
                return _rand_str()
            if isinstance(val, list):
                if (val and isinstance(val[0], list) and len(val) == len(val[0]) >= 2
                        and all(isinstance(_r, list) and len(_r) == len(val)
                                and all(isinstance(_z, int) for _z in _r) for _r in val)):
                    # MATRICE CARRÉE n×n (déterminant…) : valeurs libres, même n que l'exemple (priorité sur intervalles
                    # car un intervalle [a,b] exige a<=b ; une matrice non).
                    _n = len(val)
                    return [[rng.randint(*bornes) for _ in range(_n)] for _ in range(_n)]
                if (val and isinstance(val[0], list) and len(val[0]) == 2
                        and all(isinstance(_z, int) for _z in val[0])):   # LISTE DE PAIRES / INTERVALLES [a,b], a<=b
                    out = []
                    for _ in range(rng.randint(1, 6)):
                        _a, _b = rng.randint(-6, 8), rng.randint(-6, 8)
                        out.append([min(_a, _b), max(_a, _b)])
                    return out
                if val and isinstance(val[0], list):     # MATRICE : liste de lignes de MÊME largeur (transpose/zip OK)
                    R, C = rng.randint(1, 4), rng.randint(1, 4)
                    return [[rng.randint(*bornes) for _ in range(C)] for _ in range(R)]
                return _rand_list()
            return val
        return tuple(_rand_comme(a) for a in modele)

    def _adversarialise(args):
        """Variante ADVERSAIRE PRÉSERVANT LES LONGUEURS (pour exposer mode-vs-min, fréquence-vs-valeur, ordre…) :
        duplication EN PLACE, tout-pareil, tri. Préserver la longueur est crucial en multi-arg (alignement zip,
        validité de k). On n'altère qu'UNE liste par tuple (évite de désaligner deux listes corrélées)."""
        out = list(args)
        idxs = [i for i, a in enumerate(out) if isinstance(a, list) and a]
        if idxs:
            i = idxs[0]                                  # une seule liste touchée
            a = list(out[i])
            forme = rng.random()
            if forme < 0.30:                             # duplication EN PLACE (doublons sans changer la longueur)
                a[rng.randrange(len(a))] = rng.choice(a)
            elif forme < 0.45:                           # tout-pareil
                a = [rng.choice(a)] * len(a)
            elif forme < 0.60:                           # trié / inversé
                a = sorted(a, reverse=rng.random() < 0.5)
            out[i] = a
        return tuple(out)

    sondes = []
    gabarits = [args for args, _ in exemples]
    for _ in range(60):
        modele = rng.choice(gabarits)
        sondes.append(_adversarialise(_rand_args(modele)))
    # PROBES STRUCTURÉS pour cibles ENTIÈRES : balayage DENSE des petits entiers (1..40). Discrimine les prédicats
    # SPARSES (est_parfait, nombre_heureux, carré parfait… dont les cas positifs 6/28/496 sont rares) qu'un échantillon
    # uniforme rate -> un candidat CONSTANT (ex. `_acc*1`->0) ne survit plus. Avec oracle : la bonne réponse gagne ;
    # sans oracle : désaccord détecté -> None honnête, JAMAIS un faux. Sound + déterministe (couvre 6, 28).
    for modele in {tuple(type(a) for a in g): g for g in gabarits}.values():
        if 1 <= len(modele) <= 3 and all(t is int for t in (type(a) for a in modele)):
            if len(modele) == 1:
                sondes.extend((i,) for i in range(1, 41))
            else:
                base = [0, 1, 2, 3, 4, 5, 6, 7, 9, 12, 28]
                sondes.extend(tuple(v for _ in modele) for v in base)
    return sondes


def _hashable(v):
    """Convertit RÉCURSIVEMENT listes/dicts en structures hashables (matrices = listes de listes incluses)."""
    if isinstance(v, list):
        return tuple(_hashable(_e) for _e in v)
    if isinstance(v, dict):
        return tuple(sorted((k, _hashable(val)) for k, val in v.items()))
    return v


def _sig(fn, sondes):
    """Signature comportementale = sorties sur les sondes (marqueur si crash), rendue hashable (récursivement)."""
    out = []
    for args in sondes:
        try:
            out.append(_hashable(fn(*args)))
        except Exception:
            out.append(("__ERR__",))
    return tuple(out)


# PERF : les squelettes sont STATIQUES -> on les compile UNE FOIS pour tout le process (cache module-level), au lieu de
# recompiler ~800 sources à CHAQUE appel de synthetise (gain majeur pour le validateur et la prod qui appellent souvent).
_CACHE_COMPILE: list | None = None


def _squelettes_compiles():
    global _CACHE_COMPILE
    if _CACHE_COMPILE is None:
        compiles = []
        for gen in _SQUELETTES:
            for src in gen():
                fn = _compile(src)
                if fn is not None:
                    compiles.append((src, fn))
        _CACHE_COMPILE = compiles
    return _CACHE_COMPILE


def synthetise(exemples, held=None, oracle=None, _seed: int = 0) -> Optional[str]:
    """Construit une brique pour la cible décrite par `exemples` (+ `held`), via les squelettes.

    Retourne le CODE SOURCE d'une fonction `f(*args)` VÉRIFIÉE, ou None si rien de sound. exemples/held = liste de
    (args_tuple, sortie). `oracle` (optionnel) = la SOURCE DE VÉRITÉ appelable `oracle(*args) -> sortie` : si fournie,
    on DÉSAMBIGUÏSE ACTIVEMENT (on génère un exemple discriminant, on demande la vérité, on élimine les mauvais
    candidats) jusqu'à comportement unique — c'est « la donnée ET la source de vérité » qui construisent la brique.

    SOUNDNESS (FAUX=0) : 1) on ne garde que les instanciations reproduisant exemples ET held ; 2) ANTI-COÏNCIDENCE par
    SONDES FRAÎCHES : on ne rend une brique que si les survivants se comportent de façon IDENTIQUE sur des entrées
    fraîches. Sans oracle, une divergence -> None honnête. Avec oracle, la divergence est TRANCHÉE par la vérité (et si
    le bon comportement n'est pas dans les squelettes, les survivants s'épuisent -> None). Jamais un faux."""
    import random
    tous = list(exemples) + list(held or [])
    # PERF : squelettes compilés UNE FOIS (cache module-level) ; on ne garde ici que ceux qui reproduisent exemples+held.
    survivants = [(src, fn) for src, fn in _squelettes_compiles() if _reproduit(fn, tous)]
    if not survivants:
        return None
    rng = random.Random(f"{_seed}|{len(survivants)}|{len(tous)}")

    if oracle is not None:
        # DÉSAMBIGUÏSATION ACTIVE : tant que des survivants divergent sur une sonde, demander la vérité et filtrer.
        # (8 tours suffisent : le FILTRE FINAL PAR L'ORACLE ci-dessous est l'arbitre robuste, pas ces tours.)
        for _tour in range(8):
            sondes = _sonde_inputs(exemples, rng)
            disc = None
            for s in sondes:                                   # cherche une sonde DISCRIMINANTE
                if len({_sig(fn, [s]) for _src, fn in survivants}) > 1:
                    disc = s
                    break
            if disc is None:
                break                                          # tous les survivants coïncident -> déterminé
            try:
                verite = oracle(*disc)
            except Exception:
                continue                                       # oracle indéfini ici -> on ignore cette sonde
            verite_h = _hashable(verite)
            survivants = [(src, fn) for src, fn in survivants if _sig(fn, [disc]) == (verite_h,)]
            if not survivants:
                return None                                    # le bon comportement n'est dans aucun squelette
        # FILTRE FINAL PAR L'ORACLE (FAUX=0) : la VÉRITÉ tranche, pas l'unanimité entre survivants. On garde TOUT
        # survivant qui reproduit l'oracle sur un GRAND lot frais (entrées hors-domaine de l'oracle ignorées), puis on
        # rend le plus court. Robuste même si la désambiguïsation a laissé une ambiguïté résiduelle (malchance de
        # sonde) : le bon candidat n'est jamais jeté à cause d'un autre, et un candidat faux n'est jamais rendu.
        lot = _sonde_inputs(exemples, rng) + _sonde_inputs(exemples, rng)
        bons = []
        for src, fn in survivants:
            ok = True
            for s in lot:
                try:
                    verite = oracle(*s)
                except Exception:
                    continue                                   # oracle indéfini ici -> ignoré
                try:
                    if _sig(fn, [s]) != (_hashable(verite),):
                        ok = False
                        break
                except Exception:
                    ok = False
                    break
            if ok:
                bons.append(src)
        if not bons:
            return None
        return min(bons, key=len)

    # SANS oracle : anti-coïncidence stricte (None si sous-déterminé).
    sondes = _sonde_inputs(exemples, rng)
    sigs = {_sig(fn, sondes) for _src, fn in survivants}
    if len(sigs) > 1:
        return None
    return min((src for src, _fn in survivants), key=len)
