"""Théorie de la calculabilité — MÉCANISME EXACT, FAUX=0.

Fonctions récursives (totales) calculées par leur définition mathématique établie :
  - fonction_ackermann(m,n) : Ackermann–Péter, récursive mais NON primitive récursive
    (croissance non bornée par aucune fonction primitive récursive). Calcul itératif
    par pile explicite (pas de limite de récursion Python). Bornée explicitement pour
    rester un OUTIL sûr : m,n négatifs -> ValueError ; (m>=4 et n>=2) -> ValueError
    (protection annoncée, pas un faux : on s'abstient au lieu d'exploser) ; un budget
    de pas borne tout cas résiduel coûteux -> ValueError.
  - récursion primitive : successeur + schéma h(x,k,f(x,k)) construisent addition,
    multiplication, puissance (chaînage exact, prouvable par identités arithmétiques).
  - church_numeral(n) : encodage de Church (n = f |-> f^n), décodable sans perte.

Tout est PUR / DÉTERMINISTE. Aucune valeur inventée : entrée invalide ou hors borne -> ValueError.
stdlib uniquement.
"""

_BUDGET_ACKERMANN = 10 ** 6  # garde-fou de pas (A(3,3) ne coûte que ~2432 réductions)


def _nat(x, nom="argument"):
    """Renvoie x s'il est un entier naturel (>=0), sinon ValueError. bool rejeté."""
    if isinstance(x, bool) or not isinstance(x, int):
        raise ValueError(f"{nom} doit être un entier (reçu {type(x).__name__})")
    if x < 0:
        raise ValueError(f"{nom} doit être >= 0 (reçu {x})")
    return x


# ───────────────────────── Ackermann–Péter ─────────────────────────
def fonction_ackermann(m, n):
    """Fonction d'Ackermann–Péter A(m,n).

    A(0,n)=n+1 ; A(m,0)=A(m-1,1) ; A(m,n)=A(m-1,A(m,n-1)).
    Calcul itératif par pile (équivalent exact à la récursion, sans RecursionError).
    Bornes : négatifs -> ValueError ; (m>=4 et n>=2) -> ValueError (protection) ;
    dépassement de budget -> ValueError.
    """
    m = _nat(m, "m")
    n = _nat(n, "n")
    if m >= 4 and n >= 2:
        raise ValueError("ackermann: (m>=4 et n>=2) hors borne de sûreté")
    pile = [m]
    pas = 0
    while pile:
        pas += 1
        if pas > _BUDGET_ACKERMANN:
            raise ValueError("ackermann: dépasse le budget de pas (protection)")
        mc = pile.pop()
        if mc == 0:
            n = n + 1
        elif n == 0:
            pile.append(mc - 1)
            n = 1
        else:
            pile.append(mc - 1)
            pile.append(mc)
            n = n - 1
    return n


ackermann = fonction_ackermann  # alias usuel


def est_primitive_recursive_ackermann():
    """FAIT établi : Ackermann est récursive (totale, calculable) mais PAS primitive
    récursive. Renvoie False (= 'n'est pas primitive récursive'), résultat de théorie
    démontré (croît plus vite que toute fonction primitive récursive)."""
    return False


# ───────────────────── récursion primitive ─────────────────────
def successeur(x):
    """Fonction de base S(x) = x + 1."""
    return _nat(x, "x") + 1


def recursion_primitive(g, h, x, n):
    """Schéma de récursion primitive sur le dernier argument :
        f(x,0)   = g(x)
        f(x,k+1) = h(x, k, f(x,k))
    Déroulé itératif (équivalent exact). n doit être un entier naturel."""
    n = _nat(n, "n")
    val = g(x)
    for k in range(n):
        val = h(x, k, val)
    return val


def addition(m, n):
    """m + n par récursion primitive : add(m,0)=m ; add(m,k+1)=S(add(m,k))."""
    m = _nat(m, "m")
    n = _nat(n, "n")
    return recursion_primitive(lambda x: x, lambda x, k, v: successeur(v), m, n)


def multiplication(m, n):
    """m * n par récursion primitive : mul(m,0)=0 ; mul(m,k+1)=add(mul(m,k), m)."""
    m = _nat(m, "m")
    n = _nat(n, "n")
    return recursion_primitive(lambda x: 0, lambda x, k, v: addition(v, x), m, n)


def puissance(m, n):
    """m ** n par récursion primitive : pow(m,0)=1 ; pow(m,k+1)=mul(pow(m,k), m).
    Convention pow(0,0)=1."""
    m = _nat(m, "m")
    n = _nat(n, "n")
    return recursion_primitive(lambda x: 1, lambda x, k, v: multiplication(v, x), m, n)


def primitive_recursive(nom, m, n):
    """Dispatcher nommé : 'addition' | 'multiplication' | 'puissance'."""
    table = {"addition": addition, "multiplication": multiplication, "puissance": puissance}
    if nom not in table:
        raise ValueError(f"fonction primitive récursive inconnue : {nom!r}")
    return table[nom](m, n)


# ───────────────────────── numéraux de Church ─────────────────────────
def church_numeral(n):
    """Encodage de Church de l'entier n : renvoie la fonction n = f |-> (x |-> f^n(x))."""
    n = _nat(n, "n")

    def numeral(f):
        def applique(x):
            r = x
            for _ in range(n):
                r = f(r)
            return r
        return applique

    return numeral


def church_vers_entier(c):
    """Décode un numéral de Church en entier : applique c(succ) à 0 et compte."""
    if not callable(c):
        raise ValueError("numéral de Church attendu (callable)")
    try:
        r = c(lambda x: x + 1)(0)
    except Exception:
        raise ValueError("objet non décodable comme numéral de Church")
    if not isinstance(r, int) or isinstance(r, bool) or r < 0:
        raise ValueError("décodage de Church invalide")
    return r
