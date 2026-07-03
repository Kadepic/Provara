"""LANGAGES FORMELS & GRAMMAIRES — primitives EXACTES, déterministes, FAUX=0 (mission formule/concept 2026-06-29).

Posture (identique à `physique`/`maths_discretes`/`automates`) : le MÉCANISME est exact (algorithme CYK classique,
classification de Chomsky par la FORME des productions), et l'abstention est STRUCTURELLE — toute grammaire mal
formée ou entrée invalide lève `ValueError` (jamais un résultat faux).

CONTENU
-------
* `appartient(grammaire, mot)` — algorithme de Cocke-Younger-Kasami (CYK). Décide si `mot` est engendré par une
  grammaire HORS-CONTEXTE donnée en FORME NORMALE DE CHOMSKY (CNF). Programmation dynamique en O(n^3 · |G|),
  table[l][s] = ensemble des non-terminaux dérivant le sous-mot de longueur l débutant en s.
* `est_forme_normale_chomsky(grammaire)` — True ssi toutes les productions sont en CNF.
* `classe_chomsky(grammaire)` — étiquette la grammaire par la FORME de ses productions : 'reguliere' (type 3, si
  toutes les productions sont linéaires-droites OU toutes linéaires-gauches) sinon 'hors_contexte' (type 2).
  C'est une borne SUPÉRIEURE SOUNDE : on ne déclare JAMAIS « reguliere » une grammaire qui ne l'est pas par sa
  forme (décider la régularité du LANGAGE d'une grammaire hors-contexte est indécidable — on classe donc la forme).
* `terminaux` / `non_terminaux` — alphabets dérivés.

REPRÉSENTATION
--------------
grammaire = dict { non-terminal (str) : liste de productions }.
Chaque production est un TUPLE de symboles (str non vides) :
  * ()              = ε (epsilon), autorisée en CNF uniquement pour l'axiome 'S' (mot vide) ;
  * ('a',)          = production terminale  A -> a  (a est un terminal : tout symbole NON-clé du dict) ;
  * ('B','C')       = production binaire     A -> B C (en CNF, B et C sont des non-terminaux définis).
L'axiome est toujours 'S'. Le mot est une chaîne `str` ; chaque caractère est un symbole terminal.

Exemples (vérifiables à la main) :
  a^n b^n (n>=1) :  S->AB|AC ; A->a ; B->b ; C->SB           (accepte ab, aabb, aaabbb ; rejette aab, abab, '')
  parenthèses     :  S->SS|LR|LT ; T->SR ; L->'(' ; R->')'    (accepte (), (()), ()() ; rejette (, )(, '())')

Vérifié en adverse par `valide_langages_formels.py` (ancres de langage connues + soundness : entrée invalide ->
ValueError, jamais faux).
"""
from __future__ import annotations


# ── VALIDATION STRUCTURELLE (générale, hors-contexte) ────────────────────────────────────────────────────────────
def _valide_grammaire(grammaire) -> None:
    """Vérifie la bonne formation d'une grammaire hors-contexte. Lève ValueError sinon (abstention structurelle)."""
    if not isinstance(grammaire, dict) or not grammaire:
        raise ValueError("grammaire doit être un dict non vide")
    if "S" not in grammaire:
        raise ValueError("axiome 'S' absent de la grammaire")
    for A, prods in grammaire.items():
        if not isinstance(A, str) or A == "":
            raise ValueError(f"non-terminal invalide : {A!r}")
        if not isinstance(prods, (list, tuple)):
            raise ValueError(f"les productions de {A!r} doivent être une liste/tuple")
        for p in prods:
            if not isinstance(p, tuple):
                raise ValueError(f"production {p!r} de {A!r} doit être un tuple")
            for sym in p:
                if not isinstance(sym, str) or sym == "":
                    raise ValueError(f"symbole invalide {sym!r} dans la production {p!r} de {A!r}")


def non_terminaux(grammaire) -> frozenset:
    _valide_grammaire(grammaire)
    return frozenset(grammaire.keys())


def terminaux(grammaire) -> frozenset:
    """Symboles apparaissant en partie droite qui ne sont pas des non-terminaux (= terminaux)."""
    _valide_grammaire(grammaire)
    nts = set(grammaire)
    t = set()
    for prods in grammaire.values():
        for p in prods:
            for sym in p:
                if sym not in nts:
                    t.add(sym)
    return frozenset(t)


# ── FORME NORMALE DE CHOMSKY ─────────────────────────────────────────────────────────────────────────────────────
def _exige_cnf(grammaire) -> None:
    """Lève ValueError si la grammaire (déjà validée) n'est pas en CNF."""
    nts = set(grammaire)
    for A, prods in grammaire.items():
        for p in prods:
            if len(p) == 0:                                   # ε : seulement pour l'axiome
                if A != "S":
                    raise ValueError(f"ε-production interdite hors axiome : {A}->ε")
            elif len(p) == 1:                                 # A -> a : a doit être un terminal
                if p[0] in nts:
                    raise ValueError(f"production unitaire interdite en CNF : {A}->{p[0]}")
            elif len(p) == 2:                                 # A -> B C : B,C non-terminaux définis
                if p[0] not in nts or p[1] not in nts:
                    raise ValueError(f"production binaire {A}->{p} doit lier deux non-terminaux définis")
            else:
                raise ValueError(f"production {A}->{p} de longueur > 2 : hors CNF")


def est_forme_normale_chomsky(grammaire) -> bool:
    """True ssi la grammaire (bien formée) est en Forme Normale de Chomsky. Grammaire mal formée -> ValueError."""
    _valide_grammaire(grammaire)
    try:
        _exige_cnf(grammaire)
        return True
    except ValueError:
        return False


# ── CLASSIFICATION DE CHOMSKY (par la forme des productions) ─────────────────────────────────────────────────────
def classe_chomsky(grammaire) -> str:
    """'reguliere' (type 3) si toutes les productions sont linéaires-droites OU toutes linéaires-gauches,
    sinon 'hors_contexte' (type 2). Borne SUPÉRIEURE sounde : jamais de faux 'reguliere'."""
    _valide_grammaire(grammaire)
    nts = set(grammaire)

    def est_terminal(sym: str) -> bool:
        return sym not in nts

    droite = True   # linéaire à droite : A -> ε | a | a B  (a terminal, B non-terminal)
    gauche = True   # linéaire à gauche : A -> ε | a | B a
    for prods in grammaire.values():
        for p in prods:
            if len(p) == 0:
                continue                                      # ε convient aux deux
            elif len(p) == 1:
                if not est_terminal(p[0]):                    # production unitaire : ni droite ni gauche
                    droite = gauche = False
            elif len(p) == 2:
                a, b = p
                if not (est_terminal(a) and not est_terminal(b)):
                    droite = False
                if not (not est_terminal(a) and est_terminal(b)):
                    gauche = False
            else:
                droite = gauche = False                       # production longue : pas linéaire (reste type 2)
    return "reguliere" if (droite or gauche) else "hors_contexte"


# ── ALGORITHME CYK ───────────────────────────────────────────────────────────────────────────────────────────────
def appartient(grammaire, mot) -> bool:
    """CYK : True ssi `mot` (str) est engendré par `grammaire` en CNF (axiome 'S'). Sinon False.
    Grammaire mal formée / non-CNF, ou `mot` non-str -> ValueError (abstention, jamais faux)."""
    _valide_grammaire(grammaire)
    _exige_cnf(grammaire)
    if not isinstance(mot, str):
        raise ValueError("le mot doit être une chaîne (str)")

    n = len(mot)
    if n == 0:
        return () in grammaire["S"]                           # ε engendré ssi S->ε existe

    # table[l][s] = ensemble des non-terminaux dérivant mot[s : s+l]
    table = [[set() for _ in range(n)] for _ in range(n + 1)]

    # base : sous-mots de longueur 1
    for s in range(n):
        ch = mot[s]
        for A, prods in grammaire.items():
            for p in prods:
                if len(p) == 1 and p[0] == ch:
                    table[1][s].add(A)

    # récurrence : longueurs croissantes, sur tous les découpages
    for l in range(2, n + 1):
        for s in range(0, n - l + 1):
            cellule = table[l][s]
            for coupe in range(1, l):
                gauche = table[coupe][s]
                droite = table[l - coupe][s + coupe]
                if not gauche or not droite:
                    continue
                for A, prods in grammaire.items():
                    if A in cellule:
                        continue
                    for p in prods:
                        if len(p) == 2 and p[0] in gauche and p[1] in droite:
                            cellule.add(A)
                            break

    return "S" in table[n][0]
