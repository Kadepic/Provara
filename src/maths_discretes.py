"""MATHS DISCRÈTES — primitives EXACTES (entiers), directement appelables, FAUX=0 (mission formule/concept 2026-06-29).

Posture (identique à `physique`/`chimie`) : le MÉCANISME est exact (algorithmes classiques, arithmétique entière
sans flottant), et l'abstention est STRUCTURELLE — toute entrée invalide lève `ValueError` (jamais un résultat faux).
Couvre les sujets bornés : combinatoire (dénombrement), théorie des graphes, récurrences linéaires, géométrie
analytique (coordonnées entières), structures de données (pile / RPN / équilibrage).

Ces capacités existent aussi dans le moteur génératif `generateur.py` (via Predicteur/juge) ; ici elles sont
EXPOSÉES en appel direct, léger et exact — utilisables par l'IA et vérifiables sur des cas à réponse connue.
Vérifié en adverse par `valide_maths_discretes.py` (ancres + soundness : entrée invalide -> ValueError, jamais faux).
"""
from __future__ import annotations

import collections
import heapq


def _entier_pos(*xs):
    for x in xs:
        if not isinstance(x, int) or isinstance(x, bool) or x < 0:
            raise ValueError(f"entier ≥ 0 attendu, reçu {x!r}")


# ── COMBINATOIRE (dénombrement exact) ───────────────────────────────────────────────────────────────────────────
def factorielle(n: int) -> int:
    _entier_pos(n)
    r = 1
    for k in range(2, n + 1):
        r *= k
    return r


def binomial(n: int, k: int) -> int:
    """Coefficient binomial C(n,k) exact. 0 si k>n ou k<0 (convention de dénombrement)."""
    _entier_pos(n)
    if not isinstance(k, int) or isinstance(k, bool):
        raise ValueError("k entier attendu")
    if k < 0 or k > n:
        return 0
    k = min(k, n - k)
    num = 1
    for i in range(k):
        num = num * (n - i) // (i + 1)
    return num


def catalan(n: int) -> int:
    """n-ième nombre de Catalan = C(2n,n)/(n+1) (parenthésages, chemins de Dyck, arbres binaires)."""
    _entier_pos(n)
    return binomial(2 * n, n) // (n + 1)


def derangements(n: int) -> int:
    """Nombre de permutations sans point fixe : D(0)=1, D(1)=0, D(k)=(k-1)(D(k-1)+D(k-2))."""
    _entier_pos(n)
    a, b = 1, 0           # D(0), D(1)
    if n == 0:
        return 1
    for k in range(2, n + 1):
        a, b = b, (k - 1) * (a + b)
    return b


def partitions(n: int) -> int:
    """Nombre de partitions de l'entier n (DP type pièces : 1..n)."""
    _entier_pos(n)
    dp = [1] + [0] * n
    for piece in range(1, n + 1):
        for s in range(piece, n + 1):
            dp[s] += dp[s - piece]
    return dp[n]


# ── RÉCURRENCES LINÉAIRES (exactes, bornées) ─────────────────────────────────────────────────────────────────────
def suite_recurrente(x0: int, x1: int, p: int, q: int, n: int) -> int:
    """Terme n d'une récurrence linéaire d'ordre 2 : x_k = p·x_{k-1} + q·x_{k-2}, x_0=x0, x_1=x1. Entiers exacts."""
    _entier_pos(n)
    for v in (x0, x1, p, q):
        if not isinstance(v, int) or isinstance(v, bool):
            raise ValueError("coefficients entiers attendus")
    if n == 0:
        return x0
    if n == 1:
        return x1
    a, b = x0, x1
    for _ in range(2, n + 1):
        a, b = b, p * b + q * a
    return b


def fibonacci(n: int) -> int:
    """F(0)=0, F(1)=1, F(k)=F(k-1)+F(k-2)."""
    return suite_recurrente(0, 1, 1, 1, n)


def lucas(n: int) -> int:
    """L(0)=2, L(1)=1, même récurrence que Fibonacci."""
    return suite_recurrente(2, 1, 1, 1, n)


# ── GRAPHES (sommets 0..n-1, arêtes = liste de (u,v)) ────────────────────────────────────────────────────────────
def _valide_graphe(n, aretes):
    if not isinstance(n, int) or isinstance(n, bool) or n < 0:
        raise ValueError("n (nb sommets) entier ≥ 0 attendu")
    for e in aretes:
        if len(e) != 2:
            raise ValueError(f"arête mal formée: {e!r}")
        u, v = e
        if not (0 <= u < n and 0 <= v < n):
            raise ValueError(f"sommet hors plage dans l'arête {e!r}")


class _UnionFind:
    def __init__(self, n):
        self.p = list(range(n))

    def trouve(self, x):
        while self.p[x] != x:
            self.p[x] = self.p[self.p[x]]
            x = self.p[x]
        return x

    def unit(self, a, b):
        ra, rb = self.trouve(a), self.trouve(b)
        if ra == rb:
            return False
        self.p[ra] = rb
        return True


def composantes_connexes(n: int, aretes) -> int:
    """Nombre de composantes connexes (union-find, graphe non orienté)."""
    _valide_graphe(n, aretes)
    uf = _UnionFind(n)
    for u, v in aretes:
        uf.unit(u, v)
    return len({uf.trouve(i) for i in range(n)})


def a_cycle(n: int, aretes) -> bool:
    """Vrai s'il existe un cycle (non orienté, sans arête multiple/boucle implicite : 2 arêtes égales = cycle)."""
    _valide_graphe(n, aretes)
    uf = _UnionFind(n)
    for u, v in aretes:
        if u == v:
            return True
        if not uf.unit(u, v):
            return True
    return False


def distance_bfs(n: int, aretes, src: int, dst: int) -> int:
    """Plus court chemin en nombre d'arêtes (non pondéré). -1 si dst inatteignable."""
    _valide_graphe(n, aretes)
    if not (0 <= src < n and 0 <= dst < n):
        raise ValueError("src/dst hors plage")
    adj = collections.defaultdict(list)
    for u, v in aretes:
        adj[u].append(v)
        adj[v].append(u)
    vus = {src: 0}
    file = collections.deque([src])
    while file:
        x = file.popleft()
        if x == dst:
            return vus[x]
        for y in adj[x]:
            if y not in vus:
                vus[y] = vus[x] + 1
                file.append(y)
    return -1


def est_arbre(n: int, aretes) -> bool:
    """Vrai ssi le graphe est un arbre : connexe ET exactement n-1 arêtes ET sans cycle."""
    _valide_graphe(n, aretes)
    if n == 0:
        return False
    return len(aretes) == n - 1 and composantes_connexes(n, aretes) == 1 and not a_cycle(n, aretes)


def est_biparti(n: int, aretes) -> bool:
    """Vrai ssi le graphe est biparti (2-coloration BFS sans conflit)."""
    _valide_graphe(n, aretes)
    adj = collections.defaultdict(list)
    for u, v in aretes:
        adj[u].append(v)
        adj[v].append(u)
    couleur = {}
    for depart in range(n):
        if depart in couleur:
            continue
        couleur[depart] = 0
        file = collections.deque([depart])
        while file:
            x = file.popleft()
            for y in adj[x]:
                if y not in couleur:
                    couleur[y] = 1 - couleur[x]
                    file.append(y)
                elif couleur[y] == couleur[x]:
                    return False
    return True


def dijkstra(n: int, aretes_ponderees, src: int, dst: int) -> int:
    """Plus court chemin pondéré (poids ≥ 0). -1 si inatteignable. aretes_ponderees = liste de (u,v,poids)."""
    if not isinstance(n, int) or isinstance(n, bool) or n < 0:
        raise ValueError("n entier ≥ 0 attendu")
    adj = collections.defaultdict(list)
    for e in aretes_ponderees:
        if len(e) != 3:
            raise ValueError(f"arête pondérée mal formée: {e!r}")
        u, v, w = e
        if not (0 <= u < n and 0 <= v < n):
            raise ValueError(f"sommet hors plage: {e!r}")
        if w < 0:
            raise ValueError("poids négatif interdit (Dijkstra)")
        adj[u].append((v, w))
        adj[v].append((u, w))
    if not (0 <= src < n and 0 <= dst < n):
        raise ValueError("src/dst hors plage")
    dist = {src: 0}
    tas = [(0, src)]
    while tas:
        d, x = heapq.heappop(tas)
        if x == dst:
            return d
        if d > dist.get(x, float("inf")):
            continue
        for y, w in adj[x]:
            nd = d + w
            if nd < dist.get(y, float("inf")):
                dist[y] = nd
                heapq.heappush(tas, (nd, y))
    return -1


# ── GÉOMÉTRIE ANALYTIQUE (coordonnées entières, aires ×2 exactes) ────────────────────────────────────────────────
def _point(p):
    if len(p) != 2 or not all(isinstance(c, int) and not isinstance(c, bool) for c in p):
        raise ValueError(f"point entier (x,y) attendu, reçu {p!r}")
    return p[0], p[1]


def aire_triangle_x2(a, b, c) -> int:
    """DEUX fois l'aire du triangle (produit vectoriel, exact, entier ≥ 0). 0 = points colinéaires."""
    ax, ay = _point(a); bx, by = _point(b); cx, cy = _point(c)
    return abs((bx - ax) * (cy - ay) - (by - ay) * (cx - ax))


def orientation(a, b, c) -> int:
    """Signe du produit vectoriel (a->b->c) : +1 trigonométrique (gauche), -1 horaire (droite), 0 colinéaire."""
    ax, ay = _point(a); bx, by = _point(b); cx, cy = _point(c)
    d = (bx - ax) * (cy - ay) - (by - ay) * (cx - ax)
    return (d > 0) - (d < 0)


def aire_polygone_x2(points) -> int:
    """DEUX fois l'aire d'un polygone simple (lacet/shoelace, exact). Sommets en ordre, ≥ 3 points."""
    pts = [_point(p) for p in points]
    if len(pts) < 3:
        raise ValueError("polygone : au moins 3 sommets")
    s = 0
    for i in range(len(pts)):
        x1, y1 = pts[i]
        x2, y2 = pts[(i + 1) % len(pts)]
        s += x1 * y2 - x2 * y1
    return abs(s)


def distance_manhattan(a, b) -> int:
    ax, ay = _point(a); bx, by = _point(b)
    return abs(ax - bx) + abs(ay - by)


# ── STRUCTURES DE DONNÉES (pile : RPN entier exact, équilibrage) ─────────────────────────────────────────────────
def eval_rpn(tokens) -> int:
    """Évalue une expression en notation polonaise inverse (machine à pile), arithmétique ENTIÈRE exacte.
    Division SEULEMENT si exacte (sinon ValueError, jamais d'arrondi). Opérateurs : + - * //."""
    pile = []
    for t in tokens:
        if t in ("+", "-", "*", "//"):
            if len(pile) < 2:
                raise ValueError("RPN : opérandes manquants")
            b = pile.pop(); a = pile.pop()
            if t == "+":
                pile.append(a + b)
            elif t == "-":
                pile.append(a - b)
            elif t == "*":
                pile.append(a * b)
            else:
                if b == 0 or a % b != 0:
                    raise ValueError("RPN : division non exacte ou par zéro")
                pile.append(a // b)
        else:
            iv = int(t)               # lève ValueError si pas un entier
            if isinstance(t, str) and t.strip() != str(iv):
                raise ValueError(f"jeton invalide: {t!r}")
            pile.append(iv)
    if len(pile) != 1:
        raise ValueError("RPN : expression mal formée")
    return pile[0]


def equilibre(chaine: str) -> bool:
    """Vrai ssi les parenthèses/crochets/accolades de `chaine` sont correctement appariés (machine à pile)."""
    if not isinstance(chaine, str):
        raise ValueError("chaîne attendue")
    paires = {")": "(", "]": "[", "}": "{"}
    ouvrants = set(paires.values())
    pile = []
    for ch in chaine:
        if ch in ouvrants:
            pile.append(ch)
        elif ch in paires:
            if not pile or pile.pop() != paires[ch]:
                return False
    return not pile


if __name__ == "__main__":
    print("catalan 0..8 :", [catalan(i) for i in range(9)])
    print("derangements(5) :", derangements(5), "| partitions(6) :", partitions(6))
    print("fib(10) :", fibonacci(10), "| lucas(6) :", lucas(6))
    print("composantes(4,[(0,1),(2,3)]) :", composantes_connexes(4, [(0, 1), (2, 3)]))
    print("cycle triangle :", a_cycle(3, [(0, 1), (1, 2), (2, 0)]))
    print("dijkstra :", dijkstra(4, [(0, 1, 1), (1, 3, 1), (0, 2, 5), (2, 3, 1)], 0, 3))
    print("aire_triangle_x2 (3-4-5) :", aire_triangle_x2((0, 0), (4, 0), (0, 3)))
    print("eval_rpn 2 3 + 4 * :", eval_rpn(["2", "3", "+", "4", "*"]))
    print("equilibre (()[]) :", equilibre("(()[])"), "| (( :", equilibre("(("))
