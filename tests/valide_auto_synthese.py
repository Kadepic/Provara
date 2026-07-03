"""
AUTO-SYNTHÈSE PAR SQUELETTES (2026-06-24) — l'IA CONSTRUIT ses propres briques à partir de squelettes génériques +
la source de vérité, SANS qu'un humain code la brique. Validé : sound (FAUX=0), honnête (None si sous-déterminé),
utile (reconstruit des algos non triviaux : Kadane, eau piégée, folds).

Critères de MORT (5) :
  1. RECONSTRUCTION : Kadane (max_subarray) + eau piégée (deux-pointeurs) synthétisés et GÉNÉRALISENT (vérité fraîche).
  2. FOLDS : somme/produit/max/min synthétisés (spec discriminante) et généralisent.
  3. SOUNDNESS FAUX=0 : sur un lot de cibles-fold aléatoires, AUCUNE brique synthétisée ne généralise faux.
  4. HONNÊTETÉ : spec AMBIGUË (sum vs max-préfixe non distinguées) -> None ; cible HORS squelette (tri) -> None.
  5. DÉTERMINISME : deux appels sur la même spec rendent le même code (reproductible).

Pur en-process (pas de subprocess), rapide. SÉQUENTIEL + garde.
"""
from __future__ import annotations

import functools
import math
import random

from auto_synthese import synthetise, _compile
from garde_ressources import borne


def _check(nom, ok):
    print(f"  [{'OK ' if ok else 'RATÉ'}] {nom}", flush=True)
    return ok


def _kadane(xs):
    b = best = xs[0]
    for v in xs[1:]:
        b = max(v, b + v)
        best = max(best, b)
    return best


def _trap(h):
    l, r = 0, len(h) - 1
    lm = rm = t = 0
    while l < r:
        if h[l] < h[r]:
            lm = max(lm, h[l]); t += lm - h[l]; l += 1
        else:
            rm = max(rm, h[r]); t += rm - h[r]; r -= 1
    return t


def _prod(xs):
    p = 1
    for v in xs:
        p *= v
    return p


def _house_robber(xs):
    a = b = 0
    for x in xs:
        a, b = b, max(b, a + x)
    return b


def _longest_run(xs):
    best = cur = 1
    for i in range(1, len(xs)):
        cur = cur + 1 if xs[i] == xs[i - 1] else 1
        best = max(best, cur)
    return best


def _gen_comme(fn, rng, lo=-9, hi=9):
    return [rng.randint(lo, hi) for _ in range(rng.randint(1, 7))]


def _generalise(g, fn, rng, n=200, lo=-9, hi=9):
    for _ in range(n):
        zs = [rng.randint(lo, hi) for _ in range(rng.randint(1, 8))]
        try:
            if g(zs) != fn(zs):
                return False
        except Exception:
            return False
    return True


def main() -> int:
    borne()
    r = []
    rng = random.Random(20260624)

    # 1) RECONSTRUCTION d'algos non triviaux.
    ks = synthetise([(([-2, 1, -3, 4, -1, 2, 1, -5, 4],), 6), (([1, 2, 3],), 6)],
                    [(([-1, -2, -3],), -1), (([5, -2, 3],), 6), (([8, -19, 5, -4, 20],), 21)])
    ts = synthetise([(([0, 1, 0, 2, 1, 0, 1, 3, 2, 1, 2, 1],), 6), (([4, 2, 0, 3, 2, 5],), 9)],
                    [(([1, 0, 1],), 1), (([3, 3, 3],), 0), (([5, 4, 1, 2],), 1)])
    ok1 = ks is not None and _generalise(_compile(ks), _kadane, rng) \
        and ts is not None and _generalise(_compile(ts), _trap, rng, lo=0, hi=9)
    r.append(_check("RECONSTRUCTION Kadane + eau piégée synthétisés et généralisent", ok1))

    # 2) FOLDS via ORACLE (mode prévu « donnée + source de vérité ») : somme/produit/max/min bâtis et généralisent.
    #    (Sans oracle, max/min deviennent ambigus vs la coïncidence FRÉQUENCE quand la spec est faible -> None honnête ;
    #     l'oracle tranche. C'est le bon design : la source de vérité construit la brique.)
    def _b(fn, base, held_in):
        ex = [((base,), fn(base))]
        held = [((h,), fn(h)) for h in held_in]
        src = synthetise(ex, held, oracle=lambda xs, _f=fn: _f(xs))
        return src is not None and _generalise(_compile(src), fn, rng)
    ok2 = (_b(sum, [1, 2, 3], [[5, 5], [0], [-1, 4]])
           and _b(_prod, [1, 2, 3, 4], [[5], [10, 0, 2], [2, 2, 2]])
           and _b(max, [3, 1, 5, 2], [[1, 1, 5], [7, 7], [0, 0, -4]])
           and _b(min, [3, 1, 5, 2], [[2, 2, 5], [7, 7], [5, 5, 1]]))
    r.append(_check("FOLDS somme/produit/max/min bâtis via oracle et généralisent", bool(ok2)))

    # 3) SOUNDNESS FAUX=0 sur un lot aléatoire (toute brique synthétisée DOIT généraliser juste).
    cibles = {"sum": sum, "prod": _prod, "max": max, "min": min, "kadane": _kadane}
    faux = 0; synth = 0
    rs = random.Random(424242)
    for name, fn in cibles.items():
        for _ in range(40):
            base = _gen_comme(fn, rs)
            ex = [((base,), fn(base))]
            held = []
            for _ in range(5):
                ys = _gen_comme(fn, rs)
                held.append(((ys,), fn(ys)))
            src = synthetise(ex, held)
            if src is None:
                continue
            synth += 1
            if not _generalise(_compile(src), fn, rs, n=60):
                faux += 1
    r.append(_check(f"SOUNDNESS FAUX=0 (synthétisées={synth}, FAUX={faux})", faux == 0))

    # 4) HONNÊTETÉ : ambigu -> None ; hors squelette -> None.
    amb = synthetise([(([1, 2, 3],), 6), (([5, 5],), 10)], [(([0],), 0), (([-1, 4],), 3), (([2, 2, 2],), 6)])
    tri = synthetise([(([3, 1, 2],), [1, 2, 3])], [(([5, 4],), [4, 5]), (([2, 1, 3],), [1, 2, 3])])
    r.append(_check(f"HONNÊTETÉ ambigu->None ({amb is None}) | hors-squelette tri->None ({tri is None})",
                    amb is None and tri is None))

    # 5) DÉTERMINISME.
    a = synthetise([(([1, 2, 3],), 6), (([3, -2],), 1)], [(([2, -5, 1],), -2), (([0],), 0)])
    b = synthetise([(([1, 2, 3],), 6), (([3, -2],), 1)], [(([2, -5, 1],), -2), (([0],), 0)])
    r.append(_check("DÉTERMINISME : même spec -> même code", a == b and a is not None))

    # 6) ORACLE (désambiguïsation active) : avec la source de vérité, robuste ET sound (FAUX=0) même sur spec faible.
    cibles_o = {"sum": sum, "kadane": _kadane, "house_robber": _house_robber, "longest_run": _longest_run}
    ro = random.Random(99887766)
    faux_o = 0; synth_o = 0; bati_o = 0
    for name, fn in cibles_o.items():
        for _ in range(25):
            base = [ro.randint(-9, 9) for _ in range(ro.randint(1, 7))]
            ex = [((base,), fn(base))]               # spec MINIMALE (1 exemple) : l'oracle doit suffire
            held = [(([ro.randint(-9, 9) for _ in range(ro.randint(1, 7))],), None) for _ in range(2)]
            held = [((a2[0],), fn(a2[0])) for a2, _ in held]
            src = synthetise(ex, held, oracle=lambda xs, _f=fn: _f(xs))
            if src is None:
                continue
            synth_o += 1
            if _generalise(_compile(src), fn, ro, n=80):
                bati_o += 1
            else:
                faux_o += 1
    r.append(_check(f"ORACLE robuste+sound (bâti={bati_o}/{synth_o}, FAUX={faux_o})", faux_o == 0 and bati_o >= 80))

    # 7) MULTI-ARG (fenêtre-k, seuil-arg, deux-listes, ensembles) : bâtis via oracle, généralisent, FAUX=0.
    rm = random.Random(31415926)

    def _Lk():
        xs = [rm.randint(-6, 9) for _ in range(rm.randint(2, 7))]
        return (xs, rm.randint(1, len(xs)))

    def _Lt():
        return ([rm.randint(-6, 9) for _ in range(rm.randint(2, 7))], rm.randint(-3, 5))

    def _LL():
        n = rm.randint(2, 6); pool = [rm.randint(-5, 5) for _ in range(5)]
        return ([rm.choice(pool) for _ in range(n)], [rm.choice(pool) for _ in range(n)])

    multi = [
        ("max_window_sum_k", lambda xs, k: max(sum(xs[i:i + k]) for i in range(len(xs) - k + 1)), _Lk),
        ("count_gt_t", lambda xs, t: sum(1 for e in xs if e > t), _Lt),
        ("dot_product", lambda a, b: sum(x * y for x, y in zip(a, b)), _LL),
        ("intersection", lambda a, b: sorted(set(a) & set(b)), _LL),
        ("elementwise_sum", lambda a, b: [x + y for x, y in zip(a, b)], _LL),
        ("sym_diff", lambda a, b: sorted(set(a) ^ set(b)), _LL),
    ]
    faux_m = 0; bati_m = 0
    for name, fn, gen_in in multi:
        ex = [(lambda a: (a, fn(*a)))(gen_in()) for _ in range(3)]
        held = [(lambda a: (a, fn(*a)))(gen_in()) for _ in range(6)]
        src = synthetise(ex, held, oracle=lambda *a, _f=fn: _f(*a))
        if src is None:
            continue
        g = _compile(src)
        ok = True
        for _ in range(120):
            a = gen_in()
            try:
                if g(*a) != fn(*a):
                    ok = False; break
            except Exception:
                ok = False; break
        if ok:
            bati_m += 1
        else:
            faux_m += 1
    r.append(_check(f"MULTI-ARG bâtis via oracle (bâti={bati_m}/{len(multi)}, FAUX={faux_m})",
                    faux_m == 0 and bati_m == len(multi)))

    # 8) CHAÎNES (comptage de caractères, transformation, palindrome, mots) : bâties via oracle, FAUX=0.
    #    Le check de généralisation IGNORE les entrées où la VÉRITÉ est indéfinie (ex. longest_word sur "   ").
    rstr_rng = random.Random(27182818)

    def _rstr():
        if rstr_rng.random() < 0.4:
            return " ".join("".join(rstr_rng.choice("aeiouxyzBCD") for _ in range(rstr_rng.randint(1, 4)))
                            for _ in range(rstr_rng.randint(1, 4)))
        return "".join(rstr_rng.choice("aeiouxyzBCD 12") for _ in range(rstr_rng.randint(1, 8)))

    def _gen_str_ok(g, fn, n=200):
        for _ in range(n):
            s = _rstr()
            try:
                v = fn(s)                         # vérité définie ?
            except Exception:
                continue                          # hors domaine de la vérité -> ignoré
            try:
                gv = g(s)
            except Exception:
                return False                      # la brique crashe là où la vérité est définie -> faux
            if gv != v:
                return False
        return True

    strs = [
        ("count_vowels", lambda s: sum(1 for c in s if c in "aeiouAEIOU")),
        ("reverse", lambda s: s[::-1]),
        ("swapcase", lambda s: s.swapcase()),
        ("is_palindrome", lambda s: s == s[::-1]),
        ("num_words", lambda s: len(s.split())),
        ("longest_word", lambda s: max(s.split(), key=len)),
        ("reverse_words", lambda s: " ".join(s.split()[::-1])),
    ]
    faux_s = 0; bati_s = 0
    for name, fn in strs:
        ex, held = [], []
        while len(ex) < 4:
            s = _rstr()
            try: ex.append(((s,), fn(s)))
            except Exception: pass
        while len(held) < 8:
            s = _rstr()
            try: held.append(((s,), fn(s)))
            except Exception: pass
        src = synthetise(ex, held, oracle=lambda s, _f=fn: _f(s))
        if src is None:
            continue
        if _gen_str_ok(_compile(src), fn):
            bati_s += 1
        else:
            faux_s += 1
    r.append(_check(f"CHAÎNES bâties via oracle (bâti={bati_s}/{len(strs)}, FAUX={faux_s})",
                    faux_s == 0 and bati_s == len(strs)))

    # 9) MATRICES (liste de listes) : aplatie/sommes/diagonale/transposée/trace/max-global bâties via oracle, FAUX=0.
    rmx = random.Random(16180339)

    def _rmat():
        R, C = rmx.randint(1, 4), rmx.randint(1, 4)
        return [[rmx.randint(-6, 9) for _ in range(C)] for _ in range(R)]

    def _gen_mat_ok(g, fn, n=150):
        for _ in range(n):
            m = _rmat()
            try:
                v = fn(m)
            except Exception:
                continue
            try:
                if g(m) != v:
                    return False
            except Exception:
                return False
        return True

    mats = [
        ("flatten", lambda m: [v for row in m for v in row]),
        ("row_sums", lambda m: [sum(row) for row in m]),
        ("col_sums", lambda m: [sum(c) for c in zip(*m)]),
        ("diagonal", lambda m: [m[i][i] for i in range(len(m))]),
        ("transpose", lambda m: [list(c) for c in zip(*m)]),
        ("total", lambda m: sum(sum(row) for row in m)),
        ("trace", lambda m: sum(m[i][i] for i in range(len(m)))),
    ]
    faux_x = 0; bati_x = 0
    for name, fn in mats:
        ex, held = [], []
        while len(ex) < 4:
            m = _rmat()
            try: ex.append(((m,), fn(m)))
            except Exception: pass
        while len(held) < 8:
            m = _rmat()
            try: held.append(((m,), fn(m)))
            except Exception: pass
        src = synthetise(ex, held, oracle=lambda m, _f=fn: _f(m))
        if src is None:
            continue
        if _gen_mat_ok(_compile(src), fn):
            bati_x += 1
        else:
            faux_x += 1
    r.append(_check(f"MATRICES bâties via oracle (bâti={bati_x}/{len(mats)}, FAUX={faux_x})",
                    faux_x == 0 and bati_x == len(mats)))

    # 10) INTERVALLES (liste de paires [a,b], tri-puis-balayage) : fusion/activité-max/couverture bâties, FAUX=0.
    riv_rng = random.Random(14142135)

    def _riv():
        out = []
        for _ in range(riv_rng.randint(1, 6)):
            a, b = riv_rng.randint(-6, 8), riv_rng.randint(-6, 8)
            out.append([min(a, b), max(a, b)])
        return out

    def _merge(iv):
        out = []
        for a, b in sorted(iv):
            if out and a <= out[-1][1]:
                out[-1][1] = max(out[-1][1], b)
            else:
                out.append([a, b])
        return out

    def _activity(iv):
        cnt = 0; end = None
        for a, b in sorted(iv, key=lambda p: p[1]):
            if end is None or a >= end:
                cnt += 1; end = b
        return cnt

    def _covered(iv):
        tot = 0; cs = ce = None
        for a, b in sorted(iv):
            if cs is None:
                cs, ce = a, b
            elif a <= ce:
                ce = max(ce, b)
            else:
                tot += ce - cs; cs, ce = a, b
        return tot + (ce - cs if cs is not None else 0)

    ivs = [("merge", _merge), ("activity_max", _activity), ("covered_len", _covered),
           ("total_extent", lambda iv: max(b for a, b in iv) - min(a for a, b in iv))]
    faux_i = 0; bati_i = 0
    for name, fn in ivs:
        ex = [(lambda iv: ((iv,), fn(iv)))(_riv()) for _ in range(4)]
        held = [(lambda iv: ((iv,), fn(iv)))(_riv()) for _ in range(8)]
        src = synthetise(ex, held, oracle=lambda iv, _f=fn: _f(iv))
        if src is None:
            continue
        g = _compile(src); ok = True
        for _ in range(150):
            iv = _riv()
            try:
                if g(iv) != fn(iv):
                    ok = False; break
            except Exception:
                ok = False; break
        bati_i += 1 if ok else 0
        faux_i += 0 if ok else 1
    r.append(_check(f"INTERVALLES bâtis via oracle (bâti={bati_i}/{len(ivs)}, FAUX={faux_i})",
                    faux_i == 0 and bati_i == len(ivs)))

    # 11) GRAPHES (n, arêtes) : degrés / composantes / cycle / connexe via union-find, bâtis par oracle, FAUX=0.
    rg_rng = random.Random(57721566)

    def _rg():
        n = rg_rng.randint(1, 6)
        e = [[rg_rng.randint(0, n - 1), rg_rng.randint(0, n - 1)] for _ in range(rg_rng.randint(0, 7))]
        return (n, e)

    def _degrees(n, e):
        d = [0] * n
        for u, v in e:
            d[u] += 1; d[v] += 1
        return d

    def _comps(n, e):
        p = list(range(n))
        def fnd(x):
            while p[x] != x:
                p[x] = p[p[x]]; x = p[x]
            return x
        for u, v in e:
            p[fnd(u)] = fnd(v)
        return len({fnd(i) for i in range(n)})

    def _cycle(n, e):
        p = list(range(n))
        def fnd(x):
            while p[x] != x:
                p[x] = p[p[x]]; x = p[x]
            return x
        for u, v in e:
            ru, rv = fnd(u), fnd(v)
            if ru == rv:
                return True
            p[ru] = rv
        return False

    graphs = [("degrees", _degrees), ("num_components", _comps), ("has_cycle", _cycle),
              ("is_connected", lambda n, e: _comps(n, e) == 1)]
    faux_g = 0; bati_g = 0
    for name, fn in graphs:
        ex = [(lambda g: (g, fn(*g)))(_rg()) for _ in range(5)]
        held = [(lambda g: (g, fn(*g)))(_rg()) for _ in range(8)]
        src = synthetise(ex, held, oracle=lambda *g, _f=fn: _f(*g))
        if src is None:
            continue
        gg = _compile(src); ok = True
        for _ in range(150):
            g = _rg()
            try:
                if gg(*g) != fn(*g):
                    ok = False; break
            except Exception:
                ok = False; break
        bati_g += 1 if ok else 0
        faux_g += 0 if ok else 1
    r.append(_check(f"GRAPHES bâtis via oracle (bâti={bati_g}/{len(graphs)}, FAUX={faux_g})",
                    faux_g == 0 and bati_g == len(graphs)))

    # 12) DP-2D (deux chaînes) : edit_distance / LCS / sous-chaîne commune via table DP, bâtis par oracle, FAUX=0.
    rd_rng = random.Random(26535897)

    def _rds():
        return "".join(rd_rng.choice("abcd") for _ in range(rd_rng.randint(0, 6)))

    def _edit(a, b):
        m, n = len(a), len(b)
        dp = [[0] * (n + 1) for _ in range(m + 1)]
        for i in range(m + 1):
            dp[i][0] = i
        for j in range(n + 1):
            dp[0][j] = j
        for i in range(1, m + 1):
            for j in range(1, n + 1):
                dp[i][j] = min(dp[i-1][j] + 1, dp[i][j-1] + 1, dp[i-1][j-1] + (a[i-1] != b[j-1]))
        return dp[m][n]

    def _lcs(a, b):
        m, n = len(a), len(b)
        dp = [[0] * (n + 1) for _ in range(m + 1)]
        for i in range(1, m + 1):
            for j in range(1, n + 1):
                dp[i][j] = dp[i-1][j-1] + 1 if a[i-1] == b[j-1] else max(dp[i-1][j], dp[i][j-1])
        return dp[m][n]

    dps = [("edit_distance", _edit), ("lcs_len", _lcs)]
    faux_d = 0; bati_d = 0
    for name, fn in dps:
        ex = [(lambda a, b: ((a, b), fn(a, b)))(_rds(), _rds()) for _ in range(5)]
        held = [(lambda a, b: ((a, b), fn(a, b)))(_rds(), _rds()) for _ in range(8)]
        src = synthetise(ex, held, oracle=lambda a, b, _f=fn: _f(a, b))
        if src is None:
            continue
        g = _compile(src); ok = True
        for _ in range(200):
            a, b = _rds(), _rds()
            try:
                if g(a, b) != fn(a, b):
                    ok = False; break
            except Exception:
                ok = False; break
        bati_d += 1 if ok else 0
        faux_d += 0 if ok else 1
    r.append(_check(f"DP-2D bâtis via oracle (bâti={bati_d}/{len(dps)}, FAUX={faux_d})",
                    faux_d == 0 and bati_d == len(dps)))

    # 13) PILE / PARENTHÈSES (chaîne de crochets) : équilibrage / profondeur / déficit, bâtis par oracle, FAUX=0.
    rp_rng = random.Random(31830988)

    def _rb():
        return "".join(rp_rng.choice("()[]{}") for _ in range(rp_rng.randint(0, 8)))

    def _balanced(s):
        st = []; m = {")": "(", "]": "[", "}": "{"}
        for c in s:
            if c in "([{":
                st.append(c)
            elif c in m:
                if not st or st.pop() != m[c]:
                    return False
        return not st

    def _maxdepth(s):
        d = best = 0
        for c in s:
            if c in "([{":
                d += 1; best = max(best, d)
            elif c in ")]}":
                d -= 1
        return best

    piles = [("balanced", _balanced), ("max_depth", _maxdepth)]
    faux_p = 0; bati_p = 0
    for name, fn in piles:
        ex = [((s,), fn(s)) for s in (_rb() for _ in range(5))]
        held = [((s,), fn(s)) for s in (_rb() for _ in range(8))]
        src = synthetise(ex, held, oracle=lambda s, _f=fn: _f(s))
        if src is None:
            continue
        g = _compile(src); ok = True
        for _ in range(200):
            s = _rb()
            try:
                if g(s) != fn(s):
                    ok = False; break
            except Exception:
                ok = False; break
        bati_p += 1 if ok else 0
        faux_p += 0 if ok else 1
    r.append(_check(f"PILE/PARENTHÈSES bâtis via oracle (bâti={bati_p}/{len(piles)}, FAUX={faux_p})",
                    faux_p == 0 and bati_p == len(piles)))

    # 14) SCALAIRE (théorie des nombres / logique / géométrie) : entier(s) -> entier. Bâtis par oracle, FAUX=0.
    #     Régime ENTIERS POSITIFS (range/diviseurs/chiffres) ; le check ignore les entrées hors-domaine (div par 0).
    rsc = random.Random(86420864)

    def _isprime(n):
        return int(n > 1 and all(n % d for d in range(2, int(n ** 0.5) + 1)))

    def _ndiv(n):
        return sum(1 for d in range(1, n + 1) if n % d == 0)

    def _dsum(n):
        return sum(int(c) for c in str(n))

    def _pc(n):
        return bin(n).count("1")

    def _fib(n):
        a, b = 0, 1
        for _ in range(n):
            a, b = b, a + b
        return a

    def _collatz(n):
        if n < 1:                      # indéfini pour n<1 (bouclerait) -> l'oracle lève => sonde ignorée
            raise ValueError
        c = 0
        while n != 1:
            n = n // 2 if n % 2 == 0 else 3 * n + 1
            c += 1
        return c

    def _totient(n):
        return sum(1 for k in range(1, n + 1) if math.gcd(k, n) == 1)

    def _est_parfait(n):
        return int(n > 0 and sum(d for d in range(1, n) if n % d == 0) == n)

    def _pos(arity):
        return tuple(rsc.choice([0, 1, 2, 3] + [rsc.randint(2, 24)]) for _ in range(arity))

    def _gen_scal_ok(g, fn, arity, n=200):
        for _ in range(n):
            a = tuple(rsc.choice([0, 1, 2, 3] + [rsc.randint(2, 30)]) for _ in range(arity))
            try:
                v = fn(*a)                       # vérité définie ? (sinon div par 0, etc. -> ignoré)
            except Exception:
                continue
            try:
                if g(*a) != v:
                    return False
            except Exception:
                return False
        return True

    scals = [
        ("factorielle", math.factorial, 1), ("est_premier", _isprime, 1), ("nb_diviseurs", _ndiv, 1),
        ("somme_chiffres", _dsum, 1), ("popcount", _pc, 1), ("racine_entiere", lambda n: int(n ** 0.5), 1),
        ("pgcd", math.gcd, 2), ("xor", lambda a, b: int(bool(a) ^ bool(b)), 2),
        ("implique", lambda a, b: int((not a) or b), 2), ("hypotenuse_carre", lambda a, b: a * a + b * b, 2),
        # compositionnels (réduction 2-arg / composition de primitives / ternaire) — domaines à BORDS (k>n, m=0).
        ("combinaisons_nCr", math.comb, 2), ("arrangements_nPr", math.perm, 2), ("ppcm", math.lcm, 2),
        ("puissance_mod", lambda b, e, m: pow(b, e, m), 3),
        # vague 2 : récurrence (Fibonacci), while-borné (Collatz), composition (parfait/totient/Catalan), portes/bits.
        ("fibonacci", _fib, 1), ("collatz", _collatz, 1), ("totient", _totient, 1), ("est_parfait", _est_parfait, 1),
        ("inverse_entier", lambda n: int(str(n)[::-1]), 1),
        ("puiss_de_2", lambda n: int(n > 0 and (n & (n - 1)) == 0), 1),
        ("catalan", lambda n: math.comb(2 * n, n) // (n + 1), 1),
        ("nand", lambda a, b: int(not (a and b)), 2), ("equiv", lambda a, b: int(bool(a) == bool(b)), 2),
        ("hamming", lambda a, b: bin(a ^ b).count("1"), 2), ("manhattan", lambda a, b: abs(a) + abs(b), 2),
        ("majorite3", lambda a, b, c: int((a + b + c) >= 2), 3),
        ("triplet_pyth", lambda a, b, c: int(a * a + b * b == c * c), 3),
    ]
    faux_sc = 0; bati_sc = 0
    for name, fn, arity in scals:
        ex, held = [], []
        while len(ex) < 4:
            a = _pos(arity)
            try: ex.append((a, fn(*a)))
            except Exception: pass
        while len(held) < 8:
            a = _pos(arity)
            try: held.append((a, fn(*a)))
            except Exception: pass
        src = synthetise(ex, held, oracle=lambda *a, _f=fn: _f(*a))
        if src is None:
            continue
        if _gen_scal_ok(_compile(src), fn, arity):
            bati_sc += 1
        else:
            faux_sc += 1
    r.append(_check(f"SCALAIRE bâtis via oracle (bâti={bati_sc}/{len(scals)}, FAUX={faux_sc})",
                    faux_sc == 0 and bati_sc == len(scals)))

    # 14bis) SCALAIRE FAUX=0 SANS oracle (anti-coïncidence stricte) : aucune brique scalaire fausse, même sans vérité.
    faux_sn = 0; synth_sn = 0
    for name, fn, arity in scals:
        for _ in range(20):
            base = _pos(arity)
            try:
                exs = [(base, fn(*base))]
            except Exception:
                continue
            held = []
            while len(held) < 5:
                a = _pos(arity)
                try: held.append((a, fn(*a)))
                except Exception: pass
            src = synthetise(exs, held)
            if src is None:
                continue
            synth_sn += 1
            if not _gen_scal_ok(_compile(src), fn, arity, n=60):
                faux_sn += 1
    r.append(_check(f"SCALAIRE FAUX=0 sans oracle (synthétisées={synth_sn}, FAUX={faux_sn})", faux_sn == 0))

    # 15) VAGUE-3 (base paramétrée n,b / Horner liste+scalaire / déterminant matrice / prédicats digit-agrégat) :
    #     formes hétérogènes hors du harnais scalaire pur -> harnais dédié. Bâtis par oracle ET FAUX=0 sur lot frais.
    rv3 = random.Random(31337)

    def _scb(n, b):
        if b < 2:
            raise ValueError
        s = 0
        while n > 0:
            s += n % b; n //= b
        return s

    def _lenb(n, b):
        if b < 2:
            raise ValueError
        if n == 0:
            return 1
        c = 0
        while n > 0:
            c += 1; n //= b
        return c

    def _horner(xs, x):
        acc = 0
        for c in xs:
            acc = acc * x + c
        return acc

    def _det2(m):
        (a, b), (c, d) = m
        return a * d - b * c

    def _armstrong(n):
        s = str(n); k = len(s)
        return int(sum(int(c) ** k for c in s) == n)

    def _harshad(n):
        if n <= 0:
            raise ValueError
        return int(n % sum(int(c) for c in str(n)) == 0)

    def _smp_nb():
        return (rv3.randint(0, 60), rv3.randint(2, 16))

    def _smp_horner():
        return ([rv3.randint(-5, 5) for _ in range(rv3.randint(1, 5))], rv3.randint(-4, 6))

    def _smp_mat():
        return ([[rv3.randint(-9, 9) for _ in range(2)] for _ in range(2)],)

    def _smp_n(): return (rv3.randint(0, 400),)
    def _smp_npos(): return (rv3.randint(1, 400),)
    # années REPRÉSENTATIVES : pool incluant des bornes de siècle (×100, ×400) pour que les exemples DISCRIMINENT
    # la règle grégorienne complète de la simple « divisible par 4 » (sinon spec sous-déterminée -> honnêtement n%4).
    _ans = [1900, 2000, 2100, 2200, 2300, 2400, 1600, 1700, 1800, 2800] + list(range(1990, 2030))
    def _smp_an(): return (rv3.choice(_ans),)

    def _bissextile(y):
        return int(y % 4 == 0 and (y % 100 != 0 or y % 400 == 0))

    def _facto(n):
        if n < 2:
            raise ValueError
        out, d, m = [], 2, n
        while d * d <= m:
            while m % d == 0:
                out.append(d); m //= d
            d += 1
        if m > 1:
            out.append(m)
        return out

    def _redfrac(a, b):
        if b == 0:
            raise ValueError
        g = math.gcd(a, b)
        return (a // g, b // g)

    def _deriv(c):
        n = len(c)
        return [c[i] * (n - 1 - i) for i in range(n - 1)]

    def _geo(a, r, n):
        s, t = 0, a
        for _ in range(n):
            s += t; t *= r
        return s

    def _npi(n):
        return sum(1 for k in range(2, n + 1) if all(k % d for d in range(2, int(k ** 0.5) + 1)))

    def _digb(n, b):
        if b < 2:
            raise ValueError
        if n == 0:
            return [0]
        out = []
        while n > 0:
            out.append(n % b); n //= b
        return out[::-1]

    def _smp_facto(): return (rv3.randint(2, 600),)
    def _smp_frac(): return (rv3.randint(1, 99), rv3.randint(1, 99))
    def _smp_pset(): return (rv3.randint(0, 40),)
    def _smp_poly(): return ([rv3.randint(-5, 5) for _ in range(rv3.randint(1, 6))],)
    def _smp_geo(): return (rv3.randint(0, 9), rv3.randint(0, 5), rv3.randint(0, 8))
    def _smp_dot(): n = rv3.randint(1, 5); return ([rv3.randint(-6, 6) for _ in range(n)], [rv3.randint(-6, 6) for _ in range(n)])
    def _smp_pi(): return (rv3.randint(0, 300),)
    def _smp_digb(): return (rv3.randint(0, 600), rv3.randint(2, 16))

    def _pmul(p, q):
        out = [0] * (len(p) + len(q) - 1)
        for i in range(len(p)):
            for j in range(len(q)):
                out[i + j] += p[i] * q[j]
        return out

    def _madd(A, B):
        return [[A[i][j] + B[i][j] for j in range(len(A[0]))] for i in range(len(A))]

    def _mmul(A, B):
        return [[sum(A[i][t] * B[t][j] for t in range(len(B))) for j in range(len(B[0]))]
                for i in range(len(A))]

    def _part(n):
        dp = [1] + [0] * n
        for k in range(1, n + 1):
            for j in range(k, n + 1):
                dp[j] += dp[j - k]
        return dp[n]

    def _stir2(n, k):
        dp = [[0] * (k + 1) for _ in range(n + 1)]
        dp[0][0] = 1
        for i in range(1, n + 1):
            for j in range(1, k + 1):
                dp[i][j] = j * dp[i - 1][j] + dp[i - 1][j - 1]
        return dp[n][k]

    def _minv(a, m):
        if m <= 0:
            raise ValueError
        a %= m
        for x in range(m):
            if (a * x) % m == 1:
                return x
        return 0

    def _gcdl(xs): return functools.reduce(math.gcd, xs, 0)
    def _lcml(xs): return functools.reduce(math.lcm, xs, 1)

    def _maxcol(n):
        if n < 1:
            raise ValueError
        m = n
        while n != 1:
            n = n // 2 if n % 2 == 0 else 3 * n + 1
            m = max(m, n)
        return m

    def _issq(n):
        if n < 0:
            raise ValueError
        r = int(n ** 0.5)
        return int(r * r == n or (r + 1) ** 2 == n)

    def _fibm(n, m):
        if m <= 0:
            raise ValueError
        a, b = 0, 1
        for _ in range(n):
            a, b = b, (a + b) % m
        return a % m

    def _smp_gcdl(): return ([rv3.randint(-12, 12) for _ in range(rv3.randint(1, 6))],)
    def _smp_lcml(): return ([rv3.randint(1, 12) for _ in range(rv3.randint(1, 4))],)
    def _smp_col(): return (rv3.randint(1, 200),)
    def _smp_sq(): return (rv3.randint(0, 2000),)
    def _smp_fibm(): return (rv3.randint(0, 30), rv3.randint(1, 30))

    def _bell(n):
        if n == 0:
            return 1
        row = [1]
        for _ in range(1, n + 1):
            nr = [row[-1]]
            for x in row:
                nr.append(nr[-1] + x)
            row = nr
        return row[0]

    def _caesar(s, k):
        return "".join(chr((ord(c) - 97 + k) % 26 + 97) if "a" <= c <= "z" else c for c in s)

    def _cumbits(n):
        return sum(bin(i).count("1") for i in range(n + 1))

    def _mode(xs): return min(set(xs), key=lambda v: (-xs.count(v), v))
    def _peaks(xs): return sum(1 for i in range(1, len(xs) - 1) if xs[i] > xs[i - 1] and xs[i] > xs[i + 1])
    def _rot1(xs): return xs[1:] + xs[:1]
    def _varsc(xs):
        n = len(xs); s = sum(xs)
        return sum((n * x - s) ** 2 for x in xs)
    def _smp_lst(): return ([rv3.randint(0, 6) for _ in range(rv3.randint(1, 7))],)
    def _smp_lst2(): return ([rv3.randint(-5, 9) for _ in range(rv3.randint(1, 7))],)

    def _sumsq(n): return sum(i * i for i in range(1, n + 1))

    def _pxor(xs):
        out, x = [], 0
        for v in xs:
            x ^= v
            out.append(x)
        return out

    def _cinv(xs):
        return sum(1 for i in range(len(xs)) for j in range(i + 1, len(xs)) if xs[i] > xs[j])

    def _hap(n):
        seen = set()
        while n != 1 and n not in seen:
            seen.add(n)
            n = sum(int(c) ** 2 for c in str(n))
        return int(n == 1)

    def _smp_sumsq(): return (rv3.randint(0, 60),)
    def _smp_pxor(): return ([rv3.randint(0, 15) for _ in range(rv3.randint(1, 7))],)
    def _smp_cinv(): return ([rv3.randint(-9, 12) for _ in range(rv3.randint(1, 7))],)
    def _smp_hap(): return (rv3.randint(1, 200),)

    def _smp_bell(): return (rv3.randint(0, 15),)
    def _smp_cumbits(): return (rv3.randint(0, 300),)
    def _smp_caesar():
        s = "".join(rv3.choice("abcdefghij xyzAB12") for _ in range(rv3.randint(0, 8)))
        return (s, rv3.randint(-10, 30))

    def _smp_part(): return (rv3.randint(0, 45),)
    def _smp_stir(): return (rv3.randint(0, 12), rv3.randint(0, 12))
    def _smp_minv(): return (rv3.randint(0, 30), rv3.randint(1, 30))
    def _smp_sub():
        pool = list(range(0, 8))
        return ([rv3.choice(pool) for _ in range(rv3.randint(0, 4))],
                [rv3.choice(pool) for _ in range(rv3.randint(0, 5))])

    def _rmat(n): return [[rv3.randint(-9, 9) for _ in range(n)] for _ in range(n)]
    def _smp_pmul(): return ([rv3.randint(-5, 5) for _ in range(rv3.randint(1, 5))],
                             [rv3.randint(-5, 5) for _ in range(rv3.randint(1, 5))])
    def _smp_mat2(): n = rv3.randint(1, 3); return (_rmat(n), _rmat(n))

    v3 = [
        ("somme_chiffres_base", _scb, _smp_nb), ("longueur_base", _lenb, _smp_nb),
        ("horner", _horner, _smp_horner), ("determinant_2x2", _det2, _smp_mat),
        ("armstrong", _armstrong, _smp_n), ("harshad", _harshad, _smp_npos),
        ("annee_bissextile", _bissextile, _smp_an),
        # vague 5 : opérations calculables exactes (sortie int / liste / tuple)
        ("factorisation", _facto, _smp_facto), ("reduire_fraction", _redfrac, _smp_frac),
        ("cardinal_parties", lambda n: 2 ** n, _smp_pset), ("derivee_poly", _deriv, _smp_poly),
        ("somme_serie_geometrique", _geo, _smp_geo),
        ("produit_scalaire", lambda u, v: sum(x * y for x, y in zip(u, v)), _smp_dot),
        ("nb_premiers_jusqua", _npi, _smp_pi), ("chiffres_en_base", _digb, _smp_digb),
        # vague 6 : algèbre polynômes & matrices (sortie liste / matrice)
        ("poly_mult", _pmul, _smp_pmul), ("mat_add", _madd, _smp_mat2), ("mat_mult", _mmul, _smp_mat2),
        # vague 7 : prédicat ensembliste, combinatoire avancée, inverse modulaire
        ("sous_ensemble", lambda a, b: int(set(a) <= set(b)), _smp_sub),
        ("partitions", _part, _smp_part), ("stirling2", _stir2, _smp_stir), ("mod_inverse", _minv, _smp_minv),
        # vague 8 : PGCD/PPCM de liste, récurrence modulaire, racine entière, extremum de trajectoire
        ("gcd_list", _gcdl, _smp_gcdl), ("lcm_list", _lcml, _smp_lcml), ("max_collatz", _maxcol, _smp_col),
        ("carre_parfait", _issq, _smp_sq), ("fibonacci_mod", _fibm, _smp_fibm),
        # vague 9 : Bell, César, agrégat cumulé
        ("bell", _bell, _smp_bell), ("caesar_shift", _caesar, _smp_caesar), ("cumul_bits", _cumbits, _smp_cumbits),
        # vague 10 : somme des carrés, scan→liste, comptage de paires, itération-cycle
        ("somme_carres", _sumsq, _smp_sumsq), ("prefix_xor", _pxor, _smp_pxor),
        ("count_inversions", _cinv, _smp_cinv), ("nombre_heureux", _hap, _smp_hap),
        # vague 11 : statistiques exactes + transformations de liste
        ("mode", _mode, _smp_lst), ("variance_scaled", _varsc, _smp_lst2),
        ("pics_locaux", _peaks, _smp_lst), ("rotation_gauche", _rot1, _smp_lst2),
    ]
    faux_v3 = 0; bati_v3 = 0
    for name, fn, smp in v3:
        ex, held = [], []
        while len(ex) < 5:
            a = smp()
            try: ex.append((a, fn(*a)))
            except Exception: pass
        while len(held) < 6:
            a = smp()
            try: held.append((a, fn(*a)))
            except Exception: pass
        src = synthetise(ex, held, oracle=lambda *a, _f=fn: _f(*a))
        if src is None:
            continue
        g = _compile(src)
        ok = True
        for _ in range(800):
            a = smp()
            try: truth = fn(*a)
            except Exception: continue
            try: val = g(*a)
            except Exception: val = "__ERR__"
            if val != truth:
                ok = False; break
        if ok:
            bati_v3 += 1
        else:
            faux_v3 += 1
    r.append(_check(f"VAGUE-3 bâtis via oracle (bâti={bati_v3}/{len(v3)}, FAUX={faux_v3})",
                    faux_v3 == 0 and bati_v3 == len(v3)))

    print()
    print(f"AUTO-SYNTHÈSE VALIDÉE — {len(r)}/{len(r)}." if all(r) else f"ÉCHEC — {sum(r)}/{len(r)}.")
    return 0 if all(r) else 1


if __name__ == "__main__":
    raise SystemExit(main())
