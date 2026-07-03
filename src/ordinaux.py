"""ORDINAUX & CARDINAUX — arithmétique EXACTE, FAUX=0 (mission formule/concept).

Posture (identique à `physique`/`chimie`/`maths_discretes`) : le MÉCANISME est exact et l'abstention est
STRUCTURELLE — toute entrée mal formée ou toute question INDÉCIDABLE dans ZFC (ex. ω·n vs 2^ℵ0) lève `ValueError`,
jamais un résultat faux.

ORDINAUX
--------
On représente les ordinaux STRICTEMENT inférieurs à ω^ω en forme normale de Cantor (polynôme en ω) :

    α = ω^{e1}·c1 + ω^{e2}·c2 + … + ω^{ek}·ck    avec  e1 > e2 > … > ek ≥ 0  et  ci ≥ 1 entiers.

En interne : un tuple de paires (exposant, coefficient) en exposants STRICTEMENT décroissants ; () = 0.
Cette classe est CLOSE sous l'addition et la multiplication ordinales (le produit de deux ordinaux < ω^ω reste
< ω^ω), ce qui rend les deux opérations exactes. Elle couvre les ordinaux finis, ω, ω+1, ω·n, ω², ω³, …

L'addition et la multiplication ordinales NE sont PAS commutatives :
    1 + ω = ω        (le fini est absorbé à gauche d'un ordinal limite)   mais   ω + 1 > ω
    2 · ω = ω        (limite : sup des 2·k)                               mais   ω · 2 = ω + ω

CARDINAUX
---------
ℵ_n représenté par la chaîne "aleph_n" ; le continu 2^ℵ0 par "2^aleph_0".
Faits ÉTABLIS exposés : hiérarchie ℵ_m < ℵ_n ⇔ m < n ; ℵ0 < 2^ℵ0 (Cantor) ; 2^ℵ0 ≥ ℵ1 ; CH indécidable dans ZFC
(Gödel-Cohen). Toute comparaison ℵ_n (n≥1) vs 2^ℵ0 dépend de l'hypothèse du continu → ABSTENTION (ValueError),
jamais une réponse inventée.

Vérifié en adverse par `valide_ordinaux.py` (ancres connues + soundness + déterminisme).
"""
from __future__ import annotations


# ──────────────────────────── validation / normalisation ────────────────────────────

def _est_entier(x) -> bool:
    return isinstance(x, int) and not isinstance(x, bool)


def _verifie(a):
    """Valide qu'`a` est une forme normale de Cantor < ω^ω ; renvoie un tuple normalisé de paires (e,c).

    Lève ValueError si : pas une suite de paires, exposant/coeff non entier, exposant < 0, coeff < 1,
    ou exposants non STRICTEMENT décroissants (forme non canonique => ambiguë => refusée).
    """
    if not isinstance(a, (tuple, list)):
        raise ValueError(f"ordinal mal formé (attendu une suite de paires) : {a!r}")
    res = []
    prec = None
    for t in a:
        if not isinstance(t, (tuple, list)) or len(t) != 2:
            raise ValueError(f"terme mal formé (attendu (exposant, coeff)) : {t!r}")
        e, c = t
        if not _est_entier(e) or not _est_entier(c):
            raise ValueError(f"exposant/coefficient non entier : {t!r}")
        if e < 0:
            raise ValueError(f"exposant négatif : {e}")
        if c < 1:
            raise ValueError(f"coefficient < 1 : {c}")
        if prec is not None and e >= prec:
            raise ValueError("exposants non strictement décroissants (forme de Cantor non canonique)")
        prec = e
        res.append((e, c))
    return tuple(res)


def _norm(pairs):
    """Combine les exposants égaux et trie en décroissant ; renvoie une forme de Cantor canonique."""
    d = {}
    for e, c in pairs:
        d[e] = d.get(e, 0) + c
    res = []
    for e in sorted(d, reverse=True):
        c = d[e]
        if c > 0:
            res.append((e, c))
    return tuple(res)


# ──────────────────────────── constructeurs ────────────────────────────

ZERO = ()


def fini(n):
    """Ordinal fini n (n ≥ 0)."""
    if not _est_entier(n) or n < 0:
        raise ValueError(f"ordinal fini invalide : {n!r}")
    return () if n == 0 else ((0, n),)


def omega_puissance(e):
    """ω^e (e ≥ 0). ω^0 = 1."""
    if not _est_entier(e) or e < 0:
        raise ValueError(f"exposant invalide : {e!r}")
    return ((0, 1),) if e == 0 else ((e, 1),)


# ω lui-même.
OMEGA = ((1, 1),)
UN = ((0, 1),)


# ──────────────────────────── arithmétique ordinale ────────────────────────────

def addition_ordinale(a, b):
    """Somme ordinale α + β (NON commutative). Les termes de α d'exposant < exposant-dominant(β) sont absorbés.

    Exemples : 1+ω = ω ; ω+1 = ω+1 ≠ ω ; ω+ω = ω·2 ; n+ω = ω.
    """
    a = _verifie(a)
    b = _verifie(b)
    if not b:
        return a
    if not a:
        return b
    E = b[0][0]                                   # exposant dominant de β
    tete = [t for t in a if t[0] > E]             # termes de α strictement au-dessus de E (conservés)
    m = 0
    for e, c in a:                                # coeff éventuel de α exactement à l'exposant E
        if e == E:
            m = c
            break
    milieu = [(E, m + b[0][1])]                   # fusion au niveau E
    queue = list(b[1:])                           # reste de β (exposants < E)
    return _norm(tuple(tete) + tuple(milieu) + tuple(queue))


def multiplication_ordinale(a, b):
    """Produit ordinal α · β (NON commutatif), par distributivité À GAUCHE sur les termes de β.

    Règles par terme ω^be·bc de β (α = ω^a1·m1 + reste) :
      be = 0          : α·bc = ω^a1·(m1·bc) + reste            (le « reste » n'apparaît qu'une fois, à la fin)
      be ≥ 1, α fini  : α·ω^be·bc = ω^be·bc                    (fini absorbé : 2·ω = ω)
      be ≥ 1, α infini: α·ω^be·bc = ω^(a1+be)·bc               ((ω+1)·ω = ω², ω·ω = ω²)
    Exemples : ω·2 = ω+ω ; 2·ω = ω ; ω·ω = ω² ; (ω+1)·ω = ω² ; ω·(ω+1) = ω²+ω.
    """
    a = _verifie(a)
    b = _verifie(b)
    if not a or not b:
        return ()
    a1, m1 = a[0]
    reste = a[1:]
    acc = ()
    for be, bc in b:                              # β en exposants décroissants
        if be == 0:
            terme = _norm(((a1, m1 * bc),) + tuple(reste))
        elif a1 == 0:                             # α fini → absorbé par ω^be
            terme = ((be, bc),)
        else:                                     # α infini
            terme = ((a1 + be, bc),)
        acc = addition_ordinale(acc, terme)
    return acc


# alias confort
addition = addition_ordinale
multiplication = multiplication_ordinale


def compare_ordinaux(a, b):
    """Compare deux ordinaux : renvoie -1 si α<β, 0 si α=β, +1 si α>β (ordre des ordinaux, exact)."""
    a = _verifie(a)
    b = _verifie(b)
    na, nb = len(a), len(b)
    for i in range(max(na, nb)):
        if i >= na:                              # α épuisé, β a des termes positifs en plus
            return -1
        if i >= nb:
            return 1
        ea, ca = a[i]
        eb, cb = b[i]
        if ea != eb:
            return 1 if ea > eb else -1
        if ca != cb:
            return 1 if ca > cb else -1
    return 0


# ──────────────────────────── prédicats ordinaux ────────────────────────────

def est_fini(a):
    """True ssi l'ordinal est fini (0 inclus)."""
    a = _verifie(a)
    return all(e == 0 for e, _ in a)


def est_limite(a):
    """True ssi α est un ordinal LIMITE (≠ 0, sans partie finie : pas de terme d'exposant 0)."""
    a = _verifie(a)
    if not a:
        return False
    return a[-1][0] >= 1


def est_successeur(a):
    """True ssi α est un ordinal SUCCESSEUR (a une partie finie > 0 : terme d'exposant 0)."""
    a = _verifie(a)
    return bool(a) and a[-1][0] == 0


def est_denombrable(a):
    """True : tout ordinal représentable ici (< ω^ω, donc < ω₁) est DÉNOMBRABLE.

    Fait établi : ω, ω+1, ω·2, ω² … sont tous dénombrables (le premier ordinal indénombrable est ω₁).
    """
    _verifie(a)
    return True


def ecrit(a):
    """Écriture lisible d'un ordinal en forme de Cantor."""
    a = _verifie(a)
    if not a:
        return "0"
    parts = []
    for e, c in a:
        if e == 0:
            parts.append(str(c))
        elif e == 1:
            parts.append("ω" if c == 1 else f"ω·{c}")
        else:
            parts.append(f"ω^{e}" if c == 1 else f"ω^{e}·{c}")
    return " + ".join(parts)


# ──────────────────────────── cardinaux ────────────────────────────

def cardinal_aleph(n):
    """Le n-ième cardinal infini ℵ_n, représenté par la chaîne 'aleph_n' (n ≥ 0)."""
    if not _est_entier(n) or n < 0:
        raise ValueError(f"indice de aleph invalide : {n!r}")
    return f"aleph_{n}"


def cardinal_continu():
    """Le continu 2^ℵ0 = |ℝ|, représenté par la chaîne '2^aleph_0'."""
    return "2^aleph_0"


def _parse_card(s):
    if not isinstance(s, str):
        raise ValueError(f"cardinal non reconnu : {s!r}")
    if s == "2^aleph_0":
        return ("continu", None)
    if s.startswith("aleph_"):
        suf = s[len("aleph_"):]
        if suf.isdigit():
            return ("aleph", int(suf))
    raise ValueError(f"cardinal non reconnu : {s!r}")


def compare_cardinaux(a, b):
    """Compare deux cardinaux (-1/0/+1) sur le sous-ensemble ÉTABLI dans ZFC.

      ℵ_m vs ℵ_n      : signe(m-n)            (hiérarchie des aleph)
      ℵ0 vs 2^ℵ0      : -1                    (théorème de Cantor : ℵ0 < 2^ℵ0)
      ℵ_n (n≥1) vs 2^ℵ0 : ABSTENTION         (dépend de l'hypothèse du continu, indécidable dans ZFC) -> ValueError
    """
    ta = _parse_card(a)
    tb = _parse_card(b)
    if ta[0] == "aleph" and tb[0] == "aleph":
        return (ta[1] > tb[1]) - (ta[1] < tb[1])
    if ta[0] == "continu" and tb[0] == "continu":
        return 0
    if ta[0] == "aleph" and tb[0] == "continu":
        if ta[1] == 0:
            return -1                            # Cantor
        raise ValueError("ℵ_n (n≥1) vs 2^ℵ0 dépend de CH — indécidable dans ZFC (abstention)")
    if ta[0] == "continu" and tb[0] == "aleph":
        if tb[1] == 0:
            return 1                             # Cantor
        raise ValueError("2^ℵ0 vs ℵ_n (n≥1) dépend de CH — indécidable dans ZFC (abstention)")
    raise ValueError("comparaison de cardinaux non reconnue")


def cardinal_est_denombrable(c):
    """True ssi le cardinal est dénombrable : ℵ0 oui ; ℵ_n (n≥1) et 2^ℵ0 non."""
    t = _parse_card(c)
    if t[0] == "aleph":
        return t[1] == 0
    return False                                 # 2^ℵ0 indénombrable (Cantor)


def continu_au_moins_aleph1():
    """Fait établi (ZFC) : 2^ℵ0 ≥ ℵ1 (ℵ1 est le plus petit cardinal indénombrable)."""
    return True


def hypothese_du_continu_independante():
    """Fait méta-mathématique établi (Gödel 1940 + Cohen 1963) : CH (2^ℵ0 = ℵ1) est indécidable dans ZFC."""
    return True
