"""GRAMMAIRES FORMELLES & AUTOMATES (appartenance) — ce qui MANQUE, FAUX=0 (PARTIE I, B-NEC).

Deux briques voisines existent déjà et NE SONT PAS modifiées ici, seulement importées :
  * `automates.py`         : appartenance à un AFD (simulation exacte de δ) ;
  * `langages_formels.py`  : algorithme CYK, mais SEULEMENT sur une grammaire DÉJÀ en Forme Normale de
                             Chomsky (il VALIDE la CNF, il ne CONVERTIT pas).
Ce module fournit le chaînon absent : la CONVERSION en CNF d'une grammaire hors-contexte quelconque, la
décision d'appartenance générale (via cette conversion), et le passage AFN -> AFD (sous-ensembles).

MÉCANISME (théorèmes exacts, pas des heuristiques)
--------------------------------------------------
1. CONVERSION EN CNF — les cinq étapes canoniques, DANS L'ORDRE (Hopcroft-Ullman / Sipser) :
     START : nouvel axiome S0 -> S  (l'axiome n'apparaît plus en partie droite) ;
     TERM  : chaque terminal isolé dans une règle de longueur >= 2 devient un non-terminal dédié N_a -> a ;
     BIN   : binarisation des règles de longueur >= 3 en chaînes de règles binaires ;
     DEL   : suppression des règles vides (ε), en propageant les non-terminaux ANNULABLES ;
     UNIT  : suppression des règles unitaires A -> B, par fermeture des paires unitaires.
   La grammaire produite engendre EXACTEMENT le même langage. Ce n'est pas une promesse : c'est VÉRIFIÉ.
   INVARIANT DUR (FAUX=0) — sur tous les mots de longueur <= L (L=6 tant que le budget le permet) sur
   l'alphabet, on compare deux CHEMINS DE CODE DISTINCTS :
       (a) reconnaissance de la grammaire ORIGINALE par un analyseur d'Earley (gère ε, unitaires, cycles) ;
       (b) reconnaissance de la grammaire CONVERTIE par CYK (`langages_formels.appartient`).
   Toute divergence -> RuntimeError (on refuse de rendre une conversion non prouvée équivalente).

2. AFN -> AFD — construction des sous-ensembles de Rabin-Scott : un état de l'AFD = un ENSEMBLE d'états de
   l'AFN, δ_AFD(S,a) = ∪_{q∈S} δ_AFN(q,a). L'AFD produit accepte exactement les mêmes mots que l'AFN ;
   VÉRIFIÉ sur tous les mots de longueur <= 6 (self-test, RuntimeError sinon).

POSTURE FAUX=0
--------------
Un verdict d'appartenance exact, ou une abstention explicite (ValueError) — jamais un faux. Le mot VIDE est
le cas particulier de CYK (une table CYK n'a pas de cellule de longueur 0) : il est traité SÉPARÉMENT,
ε ∈ L(G) ssi la CNF contient la production S -> ε.

GARANTIES (vérifiées en adverse par `valide_grammaires_formelles.py`)
  - grammaire non-dict / vide / sans axiome 'S'      -> ValueError ;
  - plus de 30 non-terminaux (explosion combinatoire) -> ValueError (budget dit) ;
  - terminal multi-caractères (incompatible mot=str)   -> ValueError ;
  - mot non-str (bool, int, float NaN/inf), symbole hors alphabet -> ValueError ;
  - AFN mal formé (clé manquante, initial/acceptant/transition hors états, > 20 états) -> ValueError ;
  - bool REFUSÉS partout (True n'est pas 1), déterminisme, pas d'état global mutable, stdlib seule.

Toutes les fonctions publiques sont PURES et déterministes.
"""
from __future__ import annotations

import automates
import langages_formels

SOURCE = ("conversion CNF START/TERM/BIN/DEL/UNIT (Hopcroft-Ullman, Sipser) + construction des "
          "sous-ensembles de Rabin-Scott (AFN->AFD) ; reconnaissance CYK (langages_formels) et Earley")

_MAX_NON_TERMINAUX = 30       # budget grammaire : au-delà, explosion combinatoire -> abstention
_MAX_ETATS_AFN = 20           # budget AFN : au-delà, 2^n états potentiels -> abstention
_MAX_ETATS_AFD = 4096         # garde dure sur l'explosion des sous-ensembles
_MAX_LONGUEUR = 6             # longueur maximale des mots du self-test d'équivalence
_BUDGET_MOTS = 3000           # nombre maximal de mots énumérés pour le self-test


# ══════════════════════════════════════════════════════════════════════════════════════════════════════════
#  OUTILS GRAMMAIRE (représentation interne : dict {NT : set de productions-tuples})
# ══════════════════════════════════════════════════════════════════════════════════════════════════════════
def _to_sets(g) -> dict:
    """Copie de travail : chaque liste de productions devient un set (dédoublonnage, indépendance)."""
    return {A: set(prods) for A, prods in g.items()}


def _fresh_name(used: set, hint: str) -> str:
    """Renvoie un nom de non-terminal ABSENT de `used`, dérivé de `hint`, et l'y enregistre (déterministe)."""
    if hint not in used:
        used.add(hint)
        return hint
    k = 0
    while True:
        cand = f"{hint}_{k}"
        if cand not in used:
            used.add(cand)
            return cand
        k += 1


def _nullable(g: dict) -> set:
    """Ensemble des non-terminaux ANNULABLES (A =>* ε), calculé par point fixe. () => A annulable."""
    nul = set()
    change = True
    while change:
        change = False
        for A, prods in g.items():
            if A in nul:
                continue
            for p in prods:
                if all(s in nul for s in p):        # p == () -> all(∅) == True -> A annulable
                    nul.add(A)
                    change = True
                    break
    return nul


# ── ÉTAPE START ─────────────────────────────────────────────────────────────────────────────────────────────
def _step_start(g: dict) -> dict:
    """Nouvel axiome : on renomme l'ancien 'S' en un nom frais, puis on crée 'S' -> (ancien,). 'S' (le nouvel
    axiome) n'apparaît alors sur AUCUNE partie droite — indispensable pour DEL (ajout sûr de S -> ε)."""
    used = set(g.keys())
    ancien = _fresh_name(used, "S0")               # frais, distinct de 'S'
    ren = {"S": ancien}
    g2: dict = {}
    for A in sorted(g):
        A2 = ren.get(A, A)
        cible = g2.setdefault(A2, set())
        for p in sorted(g[A]):
            cible.add(tuple(ren.get(s, s) if s in g else s for s in p))
    g2["S"] = {(ancien,)}
    return g2


# ── ÉTAPE TERM ──────────────────────────────────────────────────────────────────────────────────────────────
def _step_term(g: dict) -> dict:
    """Terminaux isolés : dans toute règle de longueur >= 2, chaque terminal a est remplacé par N_a, avec
    N_a -> a (un seul N_a par terminal, réutilisé)."""
    nts = set(g)
    used = set(nts)
    term_nt: dict = {}
    g2 = {A: set() for A in g}

    def nt_pour(a: str) -> str:
        if a not in term_nt:
            term_nt[a] = _fresh_name(used, f"T_{a}")
        return term_nt[a]

    for A in sorted(g):
        for p in sorted(g[A]):
            if len(p) >= 2:
                g2[A].add(tuple(nt_pour(s) if s not in nts else s for s in p))
            else:
                g2[A].add(p)
    for a in sorted(term_nt):
        g2.setdefault(term_nt[a], set()).add((a,))
    return g2


# ── ÉTAPE BIN ───────────────────────────────────────────────────────────────────────────────────────────────
def _step_bin(g: dict) -> dict:
    """Binarisation : A -> X1 X2 ... Xn (n >= 3) devient A -> X1 A1, A1 -> X2 A2, ..., A(n-2) -> X(n-1) Xn."""
    used = set(g)
    g2 = {A: set() for A in g}
    for A in sorted(g):
        for p in sorted(g[A]):
            if len(p) <= 2:
                g2[A].add(p)
            else:
                syms = list(p)
                gauche = A
                for i in range(len(syms) - 2):
                    frais = _fresh_name(used, f"{A}bin")
                    g2.setdefault(gauche, set()).add((syms[i], frais))
                    g2.setdefault(frais, set())
                    gauche = frais
                g2.setdefault(gauche, set()).add((syms[-2], syms[-1]))
    return g2


# ── ÉTAPE DEL ───────────────────────────────────────────────────────────────────────────────────────────────
def _step_del(g: dict, axiome: str = "S") -> dict:
    """Suppression des ε-règles. Pour chaque règle, on génère toutes les variantes obtenues en RETIRANT des
    occurrences de non-terminaux annulables (jamais la règle vide). Puis on rajoute S -> ε ssi S annulable."""
    nul = _nullable(g)
    g2 = {A: set() for A in g}
    for A in sorted(g):
        for p in sorted(g[A]):
            idxs = [i for i, s in enumerate(p) if s in nul]
            for masque in range(1 << len(idxs)):
                retire = {idxs[j] for j in range(len(idxs)) if (masque >> j) & 1}
                newp = tuple(s for i, s in enumerate(p) if i not in retire)
                if newp:                            # jamais la production vide ici
                    g2[A].add(newp)
    if axiome in nul:                               # ε ∈ L(G) : on le préserve sur l'axiome uniquement
        g2[axiome].add(())
    return g2


# ── ÉTAPE UNIT ──────────────────────────────────────────────────────────────────────────────────────────────
def _step_unit(g: dict) -> dict:
    """Suppression des règles unitaires A -> B (B non-terminal). Pour chaque paire unitaire (A,B) atteignable,
    on copie dans A toutes les productions NON unitaires de B."""
    nts = set(g)
    g2 = {A: set() for A in g}
    for A in sorted(g):
        atteint = {A}
        pile = [A]
        while pile:
            B = pile.pop()
            for p in g[B]:
                if len(p) == 1 and p[0] in nts:
                    C = p[0]
                    if C not in atteint:
                        atteint.add(C)
                        pile.append(C)
        for B in sorted(atteint):
            for p in g[B]:
                if not (len(p) == 1 and p[0] in nts):
                    g2[A].add(p)
    return g2


# ── NETTOYAGE (non-terminaux stériles) ──────────────────────────────────────────────────────────────────────
def _cleanup(g: dict, axiome: str = "S") -> dict:
    """Retire les non-terminaux sans production (langage vide) et les productions qui les référencent, par
    point fixe. L'axiome est toujours conservé (au besoin avec une liste de productions vide = langage vide)."""
    g = {A: set(prods) for A, prods in g.items()}
    nts = set(g)
    change = True
    while change:
        change = False
        vivants = {A for A in g if g[A]}
        for A in list(g):
            neuf = set()
            for p in g[A]:
                if all((s not in nts) or (s in vivants) for s in p):
                    neuf.add(p)
            if neuf != g[A]:
                g[A] = neuf
                change = True
    resultat = {A: prods for A, prods in g.items() if prods or A == axiome}
    resultat.setdefault(axiome, set())
    return resultat


def _finalize(g: dict) -> dict:
    """Sérialise en la représentation de `langages_formels` : dict {NT : liste TRIÉE de tuples} (déterministe)."""
    return {A: sorted(g[A]) for A in sorted(g)}


# ══════════════════════════════════════════════════════════════════════════════════════════════════════════
#  ANALYSEUR D'EARLEY (grammaire hors-contexte QUELCONQUE) — chemin de code INDÉPENDANT de CYK
# ══════════════════════════════════════════════════════════════════════════════════════════════════════════
def _earley(grammaire: dict, mot: str) -> bool:
    """True ssi `mot` est engendré par la grammaire (axiome 'S'), par l'algorithme d'Earley. Gère ε, règles
    unitaires et cycles (prédiction des annulables à la Aycock-Horspool ; chaque ensemble d'Earley est saturé
    jusqu'au point fixe). Sert de SECONDE reconnaissance, distincte de CYK, pour prouver l'équivalence CNF."""
    nts = set(grammaire)
    nul = _nullable(_to_sets(grammaire))
    n = len(mot)
    charts = [set() for _ in range(n + 1)]
    for p in grammaire["S"]:
        charts[0].add(("S", tuple(p), 0, 0))
    for i in range(n + 1):
        change = True
        while change:                                   # saturation de l'ensemble d'Earley i
            change = False
            for item in list(charts[i]):
                A, rhs, dot, j = item
                if dot < len(rhs):
                    X = rhs[dot]
                    if X in nts:                        # PRÉDICTION
                        for p in grammaire[X]:
                            it = (X, tuple(p), 0, i)
                            if it not in charts[i]:
                                charts[i].add(it); change = True
                        if X in nul:                    # annulable : on avance le point
                            it = (A, rhs, dot + 1, j)
                            if it not in charts[i]:
                                charts[i].add(it); change = True
                else:                                   # COMPLÉTION
                    for (B, rhs2, dot2, k) in list(charts[j]):
                        if dot2 < len(rhs2) and rhs2[dot2] == A:
                            it = (B, rhs2, dot2 + 1, k)
                            if it not in charts[i]:
                                charts[i].add(it); change = True
        if i < n:                                       # SCAN vers l'ensemble suivant
            for (A, rhs, dot, j) in list(charts[i]):
                if dot < len(rhs):
                    X = rhs[dot]
                    if X not in nts and len(X) == 1 and mot[i] == X:
                        charts[i + 1].add((A, rhs, dot + 1, j))
    for (A, rhs, dot, j) in charts[n]:
        if A == "S" and dot == len(rhs) and j == 0:
            return True
    return False


# ══════════════════════════════════════════════════════════════════════════════════════════════════════════
#  ÉNUMÉRATION BORNÉE DES MOTS (self-tests) — commune grammaire/AFN
# ══════════════════════════════════════════════════════════════════════════════════════════════════════════
def _mots_bornes(alphabet, max_len: int = _MAX_LONGUEUR, budget: int = _BUDGET_MOTS):
    """Renvoie (liste des mots de longueur <= L, L) où L <= max_len est la plus grande longueur telle que le
    nombre total de mots reste sous `budget` (honnêteté : on ne prétend pas tester plus loin que le budget)."""
    alpha = sorted(alphabet)
    total = 0
    L = 0
    for k in range(max_len + 1):
        total += len(alpha) ** k if alpha else (1 if k == 0 else 0)
        if total > budget:
            break
        L = k
    mots = [""]
    courant = [""]
    for _ in range(L):
        courant = [w + c for w in courant for c in alpha]
        mots += courant
    return mots, L


def _verifie_equivalence(orig: dict, cnf: dict) -> None:
    """INVARIANT DUR de vers_cnf : Earley(orig) == CYK(cnf) sur tous les mots testés. Sinon RuntimeError."""
    alpha = sorted(langages_formels.terminaux(orig))
    mots, _ = _mots_bornes(alpha)
    for w in mots:
        a = _earley(orig, w)
        b = (() in cnf["S"]) if w == "" else langages_formels.appartient(cnf, w)
        if a != b:
            raise RuntimeError(f"conversion CNF NON équivalente sur {w!r} : origine={a}, cnf={b}")


# ══════════════════════════════════════════════════════════════════════════════════════════════════════════
#  API PUBLIQUE — GRAMMAIRES
# ══════════════════════════════════════════════════════════════════════════════════════════════════════════
def vers_cnf(grammaire) -> dict:
    """Convertit une grammaire hors-contexte quelconque en Forme Normale de Chomsky ÉQUIVALENTE (même langage).

    Étapes canoniques dans l'ordre START, TERM, BIN, DEL, UNIT, puis nettoyage des non-terminaux stériles.
    Le résultat est prouvé équivalent (self-test Earley vs CYK, RuntimeError sinon) et respecte la CNF de
    `langages_formels`. Abstention (ValueError) : grammaire mal formée / sans axiome, > 30 non-terminaux,
    terminal multi-caractères."""
    nts = langages_formels.non_terminaux(grammaire)          # valide la grammaire ET compte les NT
    if len(nts) > _MAX_NON_TERMINAUX:
        raise ValueError(f"budget dépassé : {len(nts)} non-terminaux > {_MAX_NON_TERMINAUX} (explosion) ; abstention")
    for t in langages_formels.terminaux(grammaire):
        if len(t) != 1:
            raise ValueError(f"terminal multi-caractères non supporté : {t!r} (un mot = une suite de caractères)")

    g = _to_sets(grammaire)
    g = _step_start(g)
    g = _step_term(g)
    g = _step_bin(g)
    g = _step_del(g)
    g = _step_unit(g)
    g = _cleanup(g)
    cnf = _finalize(g)

    if not langages_formels.est_forme_normale_chomsky(cnf):   # garde interne : bug de conversion
        raise RuntimeError("conversion interne : la grammaire produite n'est pas en CNF")
    _verifie_equivalence(grammaire, cnf)                      # INVARIANT DUR d'équivalence de langage
    return cnf


def appartient(grammaire, mot) -> bool:
    """True ssi `mot` (str) est engendré par la grammaire hors-contexte `grammaire` (axiome 'S').

    Convertit en CNF puis délègue à CYK (`langages_formels.appartient`). Le mot VIDE est traité séparément
    (ε ∈ L(G) ssi la CNF contient S -> ε). Abstention : grammaire mal formée, mot non-str, symbole du mot
    hors de l'alphabet terminal de la grammaire."""
    langages_formels.non_terminaux(grammaire)                # valide la grammaire (lève ValueError sinon)
    if not isinstance(mot, str):
        raise ValueError("le mot doit être une chaîne (str)")
    terms = langages_formels.terminaux(grammaire)
    for ch in mot:
        if ch not in terms:
            raise ValueError(f"symbole hors alphabet : {ch!r}")
    cnf = vers_cnf(grammaire)
    if mot == "":
        return () in cnf["S"]
    return langages_formels.appartient(cnf, mot)


def classe_chomsky(grammaire) -> str:
    """Classification de Chomsky par la FORME des productions (délégué à `langages_formels`) :
    'reguliere' (type 3) ou 'hors_contexte' (type 2). Borne supérieure sounde, jamais de faux 'reguliere'."""
    return langages_formels.classe_chomsky(grammaire)


# ══════════════════════════════════════════════════════════════════════════════════════════════════════════
#  API PUBLIQUE — AUTOMATES FINIS NON DÉTERMINISTES (AFN)
# ══════════════════════════════════════════════════════════════════════════════════════════════════════════
#  Représentation AFN : dict {
#     "etats"      : ensemble d'états (hashables),
#     "alphabet"   : ensemble de symboles,
#     "transitions": dict {(etat, symbole) : itérable d'états}  (clé ABSENTE = ensemble vide : δ partielle OK),
#     "initial"    : état initial,
#     "acceptants" : ensemble d'états acceptants }.
#  Pas d'ε-transition (documenté) : chaque transition consomme un symbole de l'alphabet.
def _valide_afn(afn):
    if not isinstance(afn, dict):
        raise ValueError("AFN doit être un dict")
    for cle in ("etats", "alphabet", "transitions", "initial", "acceptants"):
        if cle not in afn:
            raise ValueError(f"AFN : clé manquante {cle!r}")
    etats = set(afn["etats"])
    alpha = set(afn["alphabet"])
    delta = afn["transitions"]
    if not isinstance(delta, dict):
        raise ValueError("AFN : 'transitions' doit être un dict {(etat,symbole): itérable d'états}")
    if len(etats) > _MAX_ETATS_AFN:
        raise ValueError(f"budget dépassé : {len(etats)} états > {_MAX_ETATS_AFN} (déterminisation exponentielle) ; abstention")
    if afn["initial"] not in etats:
        raise ValueError("état initial hors des états")
    if not set(afn["acceptants"]) <= etats:
        raise ValueError("états acceptants hors des états")
    for cle, val in delta.items():
        if not (isinstance(cle, tuple) and len(cle) == 2):
            raise ValueError(f"clé de transition invalide : {cle!r} (attendu (etat, symbole))")
        e, s = cle
        if e not in etats:
            raise ValueError(f"transition depuis un état inconnu : {e!r}")
        if s not in alpha:
            raise ValueError(f"transition sur un symbole hors alphabet : {s!r}")
        if not isinstance(val, (set, frozenset, list, tuple)):
            raise ValueError(f"cible de transition {cle!r} doit être un itérable d'états")
        for f in val:
            if f not in etats:
                raise ValueError(f"transition vers un état inconnu : {f!r}")
    return etats, alpha, delta


def accepte_afn(afn, mot) -> bool:
    """True ssi l'AFN accepte `mot` (str), par simulation directe de l'ensemble des états courants.
    AFN mal formé -> ValueError ; mot non-str -> ValueError ; symbole hors alphabet -> ValueError."""
    _, alpha, delta = _valide_afn(afn)
    if not isinstance(mot, str):
        raise ValueError("le mot doit être une chaîne (str)")
    courant = {afn["initial"]}
    for sym in mot:
        if sym not in alpha:
            raise ValueError(f"symbole hors alphabet : {sym!r}")
        suivant = set()
        for e in courant:
            for f in delta.get((e, sym), ()):
                suivant.add(f)
        courant = suivant
    return bool(courant & set(afn["acceptants"]))


def _verifie_afn_afd(afn, dfa) -> None:
    """INVARIANT : l'AFD accepte exactement comme l'AFN sur tous les mots testés. Sinon RuntimeError."""
    mots, _ = _mots_bornes(afn["alphabet"])
    for w in mots:
        if automates.accepte(dfa, w) != accepte_afn(afn, w):
            raise RuntimeError(f"déterminisation NON équivalente sur {w!r}")


def determinise(afn) -> dict:
    """Construit un AFD (représentation de `automates`) équivalent à l'AFN, par construction des sous-ensembles
    de Rabin-Scott. Chaque état de l'AFD est un frozenset d'états de l'AFN ; δ est TOTALE (état-puits =
    frozenset vide inclus si atteint). Équivalence VÉRIFIÉE (self-test, RuntimeError sinon).
    AFN mal formé -> ValueError ; explosion (> budget d'états) -> ValueError."""
    _, alpha, delta = _valide_afn(afn)
    alpha_l = sorted(alpha)
    depart = frozenset({afn["initial"]})
    dfa_etats = {depart}
    trans: dict = {}
    pile = [depart]
    while pile:
        S = pile.pop()
        for a in alpha_l:
            T = frozenset(f for e in S for f in delta.get((e, a), ()))
            trans[(S, a)] = T
            if T not in dfa_etats:
                if len(dfa_etats) >= _MAX_ETATS_AFD:
                    raise ValueError(f"budget dépassé : plus de {_MAX_ETATS_AFD} sous-ensembles ; abstention")
                dfa_etats.add(T)
                pile.append(T)
    acc_afn = set(afn["acceptants"])
    dfa = {
        "etats": dfa_etats,
        "alphabet": set(alpha),
        "transitions": trans,
        "initial": depart,
        "acceptants": {S for S in dfa_etats if S & acc_afn},
    }
    _verifie_afn_afd(afn, dfa)
    return dfa


if __name__ == "__main__":
    G = {"S": [("a", "S", "b"), ()]}                 # {a^n b^n}
    for m in ["", "ab", "aabb", "aaabbb", "a", "ba", "aab"]:
        print(f"  a^n b^n « {m or 'ε'} » -> {appartient(G, m)}")
