"""GATE ADVERSE — grammaires_formelles : conversion CNF, appartenance, AFN->AFD.

Preuve par ANCRES NON CIRCULAIRES (langages classiques connus à la main, prédicats indépendants), SOUNDNESS
(abstention sur bool/str/NaN/inf/hors-domaine/mauvaise arité) et DÉTERMINISME. Aucune valeur attendue n'est
recalculée avec la fonction testée.
"""
from __future__ import annotations

import itertools

import automates
import langages_formels
import grammaires_formelles as gf

ok = 0
ko = 0


def check(cond, label):
    global ok, ko
    if cond:
        ok += 1
    else:
        ko += 1
        print(f"  FAIL: {label}")


def leve(fn, *a, **k) -> bool:
    """True ssi fn(*a) lève ValueError (abstention attendue)."""
    try:
        fn(*a, **k)
        return False
    except ValueError:
        return True


NAN = float("nan")
INF = float("inf")

# ── Grammaires ancres (langages connus INDÉPENDAMMENT) ──────────────────────────────────────────────────────
G_ANBN = {"S": [("a", "S", "b"), ()]}                       # {a^n b^n | n>=0}  (ε inclus)
G_PAR = {"S": [("S", "S"), ("(", "S", ")"), ()]}            # parenthèses bien formées (ε inclus)
G_ASTAR = {"S": [("A",)], "A": [("a", "A"), ()]}            # a*  (avec règle unitaire S->A et ε)


# ════════════════════════════════════════════════════════════════════════════════════════════════════════════
# ANCRE 1 : {a^n b^n} après conversion CNF — appartenance décidée par CYK sur la CNF produite.
#   Vérité indépendante : un mot est dans {a^n b^n} ssi c'est a répété n fois puis b répété n fois.
# ════════════════════════════════════════════════════════════════════════════════════════════════════════════
for m in ["", "ab", "aabb", "aaabbb"]:                      # DOIVENT être acceptés (a^n b^n, n=0,1,2,3)
    check(gf.appartient(G_ANBN, m) is True, f"a^n b^n accepte {m!r}")
for m in ["a", "ba", "aab", "abb", "abab", "b", "aaabb"]:   # DOIVENT être refusés
    check(gf.appartient(G_ANBN, m) is False, f"a^n b^n refuse {m!r}")

# La CNF produite est réellement en Forme Normale de Chomsky (vérifié par le module voisin, non par nous).
check(langages_formels.est_forme_normale_chomsky(gf.vers_cnf(G_ANBN)) is True, "vers_cnf(a^n b^n) est en CNF")
check(langages_formels.est_forme_normale_chomsky(gf.vers_cnf(G_PAR)) is True, "vers_cnf(paren) est en CNF")
check(langages_formels.est_forme_normale_chomsky(gf.vers_cnf(G_ASTAR)) is True, "vers_cnf(a*) est en CNF")

# ════════════════════════════════════════════════════════════════════════════════════════════════════════════
# ANCRE 2 : parenthèses bien formées après conversion CNF.
# ════════════════════════════════════════════════════════════════════════════════════════════════════════════
for m in ["", "()", "(())", "()()", "(()())", "((()))"]:    # DOIVENT être acceptés
    check(gf.appartient(G_PAR, m) is True, f"paren accepte {m!r}")
for m in ["(", ")(", "(()", "((", "())", ")", "()("]:       # DOIVENT être refusés
    check(gf.appartient(G_PAR, m) is False, f"paren refuse {m!r}")

# ════════════════════════════════════════════════════════════════════════════════════════════════════════════
# ANCRE 3 : AFN "mots finissant par 'a'" sur {a,b} ; sa déterminisation accepte EXACTEMENT les mêmes mots.
#   Vérité indépendante : mot accepté ssi non vide et dernier caractère == 'a'.
#   Vérifié sur TOUS les mots de longueur <= 6 (127 mots), à la fois pour l'AFN et pour l'AFD produit.
# ════════════════════════════════════════════════════════════════════════════════════════════════════════════
AFN_FIN_A = {
    "etats": {"q0", "q1"},
    "alphabet": {"a", "b"},
    "transitions": {("q0", "a"): {"q0", "q1"}, ("q0", "b"): {"q0"}},   # q1 : puits acceptant (pas de sortie)
    "initial": "q0",
    "acceptants": {"q1"},
}
DFA_FIN_A = gf.determinise(AFN_FIN_A)
# L'AFD produit est bien formé au sens de `automates` (δ totale, etc.) : automates.accepte ne lève pas.
_nb_mots = 0
for L in range(7):                                          # longueurs 0..6
    for tup in itertools.product("ab", repeat=L):
        w = "".join(tup)
        _nb_mots += 1
        attendu = (w != "" and w[-1] == "a")               # prédicat INDÉPENDANT
        check(gf.accepte_afn(AFN_FIN_A, w) is attendu, f"AFN fin-a {w!r}")
        check(automates.accepte(DFA_FIN_A, w) is attendu, f"AFD fin-a {w!r}")
check(_nb_mots == 127, "126+1 mots de longueur <= 6 énumérés")   # 2^0+...+2^6 = 127

# ════════════════════════════════════════════════════════════════════════════════════════════════════════════
# ANCRE D'INVARIANT : pour 3 grammaires, {mots acceptés, |w|<=5} est IDENTIQUE avant/après conversion CNF.
#   Chemin 1 (AVANT) : dérivation exhaustive de la grammaire ORIGINALE (BFS bornée, gauche d'abord) — code
#                      écrit ci-dessous, TOTALEMENT indépendant du module.
#   Chemin 2 (APRÈS) : CYK sur la CNF (via gf.appartient, qui convertit puis délègue à langages_formels).
# ════════════════════════════════════════════════════════════════════════════════════════════════════════════
def langue_par_derivation(g, alphabet, maxlen):
    """Ensemble des mots de longueur <= maxlen engendrés par g, par expansion BFS du non-terminal le plus à
    gauche (dérivations gauches), avec bornes de terminaison. INDÉPENDANT de CYK et d'Earley."""
    nts = set(g)
    accepte = set()
    vus = {("S",)}
    file = [("S",)]
    cap = maxlen + 6
    while file:
        forme = file.pop(0)
        if all(sym not in nts for sym in forme):           # forme entièrement terminale
            w = "".join(forme)
            if len(w) <= maxlen:
                accepte.add(w)
            continue
        if sum(1 for sym in forme if sym not in nts) > maxlen:
            continue                                        # déjà trop de terminaux
        if len(forme) > cap:
            continue
        for i, sym in enumerate(forme):
            if sym in nts:                                  # non-terminal le plus à gauche
                for p in g[sym]:
                    neuf = forme[:i] + tuple(p) + forme[i + 1:]
                    if len(neuf) <= cap and neuf not in vus:
                        vus.add(neuf)
                        file.append(neuf)
                break
    return accepte


def tous_les_mots(alphabet, maxlen):
    res = [""]
    cur = [""]
    for _ in range(maxlen):
        cur = [w + c for w in cur for c in alphabet]
        res += cur
    return res


for G, alpha, nom in [(G_ANBN, "ab", "a^n b^n"), (G_PAR, "()", "paren"), (G_ASTAR, "a", "a*")]:
    avant = langue_par_derivation(G, alpha, 5)                                  # dérivation exhaustive
    apres = {w for w in tous_les_mots(alpha, 5) if gf.appartient(G, w)}         # CYK sur la CNF
    check(avant == apres, f"invariant CNF (dériv vs CYK) : {nom}")
# Contrôle de sanité : les langues calculées ne sont pas vides et contiennent des jalons connus.
check("aabb" in langue_par_derivation(G_ANBN, "ab", 5), "dérivation a^n b^n contient aabb")
check("()()" in langue_par_derivation(G_PAR, "()", 5), "dérivation paren contient ()()")
check(langue_par_derivation(G_ASTAR, "a", 5) == {"", "a", "aa", "aaa", "aaaa", "aaaaa"}, "dérivation a* = {a^k, k<=5}")

# ════════════════════════════════════════════════════════════════════════════════════════════════════════════
# classe_chomsky (délégué) : ancres de FORME connues.
# ════════════════════════════════════════════════════════════════════════════════════════════════════════════
check(gf.classe_chomsky({"S": [("a", "S"), ()]}) == "reguliere", "classe droite-linéaire = reguliere")
check(gf.classe_chomsky({"S": [("S", "a"), ()]}) == "reguliere", "classe gauche-linéaire = reguliere")
check(gf.classe_chomsky(G_PAR) == "hors_contexte", "classe parenthèses = hors_contexte")

# ════════════════════════════════════════════════════════════════════════════════════════════════════════════
# SOUNDNESS — abstention structurelle (ValueError), jamais un faux.
# ════════════════════════════════════════════════════════════════════════════════════════════════════════════
# vers_cnf
check(leve(gf.vers_cnf, True), "vers_cnf(bool) -> ValueError")
check(leve(gf.vers_cnf, "abc"), "vers_cnf(str) -> ValueError")
check(leve(gf.vers_cnf, 3.14), "vers_cnf(float) -> ValueError")
check(leve(gf.vers_cnf, {}), "vers_cnf({}) -> ValueError")
check(leve(gf.vers_cnf, {"A": [("a",)]}), "vers_cnf(sans axiome S) -> ValueError")
check(leve(gf.vers_cnf, {"S": [("ab",)]}), "vers_cnf(terminal multi-car) -> ValueError")
check(leve(gf.vers_cnf, {"S": ["a"]}), "vers_cnf(production non-tuple) -> ValueError")
_gros = {"S": [tuple(f"N{i}" for i in range(2))]}
for i in range(32):
    _gros[f"N{i}"] = [("a",)]
check(leve(gf.vers_cnf, _gros), "vers_cnf(>30 non-terminaux) -> ValueError (budget)")

# appartient
check(leve(gf.appartient, G_ANBN, 123), "appartient(mot int) -> ValueError")
check(leve(gf.appartient, G_ANBN, True), "appartient(mot bool) -> ValueError")
check(leve(gf.appartient, G_ANBN, NAN), "appartient(mot NaN) -> ValueError")
check(leve(gf.appartient, G_ANBN, INF), "appartient(mot inf) -> ValueError")
check(leve(gf.appartient, G_ANBN, "c"), "appartient(symbole hors alphabet) -> ValueError")
check(leve(gf.appartient, G_ANBN, "aXb"), "appartient(symbole X hors alphabet) -> ValueError")
check(leve(gf.appartient, {}, "ab"), "appartient(grammaire vide) -> ValueError")
check(leve(gf.appartient, True, "ab"), "appartient(grammaire bool) -> ValueError")

# accepte_afn
check(leve(gf.accepte_afn, AFN_FIN_A, 5), "accepte_afn(mot int) -> ValueError")
check(leve(gf.accepte_afn, AFN_FIN_A, True), "accepte_afn(mot bool) -> ValueError")
check(leve(gf.accepte_afn, AFN_FIN_A, NAN), "accepte_afn(mot NaN) -> ValueError")
check(leve(gf.accepte_afn, AFN_FIN_A, "aca"), "accepte_afn(symbole hors alphabet) -> ValueError")
check(leve(gf.accepte_afn, True, "a"), "accepte_afn(afn bool) -> ValueError")
check(leve(gf.accepte_afn, {"etats": {"q0"}}, "a"), "accepte_afn(afn clés manquantes) -> ValueError")

# determinise
check(leve(gf.determinise, True), "determinise(bool) -> ValueError")
check(leve(gf.determinise, {"etats": {"q0"}}), "determinise(clés manquantes) -> ValueError")
check(leve(gf.determinise, {"etats": {"q0"}, "alphabet": {"a"}, "transitions": {},
                            "initial": "qX", "acceptants": set()}), "determinise(initial hors états) -> ValueError")
check(leve(gf.determinise, {"etats": {"q0"}, "alphabet": {"a"}, "transitions": {},
                            "initial": "q0", "acceptants": {"qZ"}}), "determinise(acceptant hors états) -> ValueError")
check(leve(gf.determinise, {"etats": {"q0"}, "alphabet": {"a"}, "transitions": {("q0", "a"): {"qZ"}},
                            "initial": "q0", "acceptants": set()}), "determinise(cible hors états) -> ValueError")
check(leve(gf.determinise, {"etats": {"q0"}, "alphabet": {"a"}, "transitions": {("q0", "b"): {"q0"}},
                            "initial": "q0", "acceptants": set()}), "determinise(symbole hors alphabet) -> ValueError")
_gros_afn = {"etats": {f"q{i}" for i in range(21)}, "alphabet": {"a"}, "transitions": {},
             "initial": "q0", "acceptants": set()}
check(leve(gf.determinise, _gros_afn), "determinise(>20 états) -> ValueError (budget)")

# classe_chomsky
check(leve(gf.classe_chomsky, {}), "classe_chomsky({}) -> ValueError")
check(leve(gf.classe_chomsky, True), "classe_chomsky(bool) -> ValueError")

# ════════════════════════════════════════════════════════════════════════════════════════════════════════════
# DÉTERMINISME — deux appels, résultat identique.
# ════════════════════════════════════════════════════════════════════════════════════════════════════════════
check(gf.vers_cnf(G_ANBN) == gf.vers_cnf(G_ANBN), "vers_cnf déterministe")
check(gf.vers_cnf(G_PAR) == gf.vers_cnf(G_PAR), "vers_cnf(paren) déterministe")
check(gf.appartient(G_ANBN, "aabb") == gf.appartient(G_ANBN, "aabb"), "appartient déterministe")
check(gf.determinise(AFN_FIN_A) == gf.determinise(AFN_FIN_A), "determinise déterministe")
check(gf.accepte_afn(AFN_FIN_A, "aba") == gf.accepte_afn(AFN_FIN_A, "aba"), "accepte_afn déterministe")

# Cohérence croisée : appartient (empty word) == présence de S->() dans la CNF.
check(gf.appartient(G_ANBN, "") == (() in gf.vers_cnf(G_ANBN)["S"]), "mot vide cohérent avec S->ε")
check(gf.appartient({"S": [("a",)]}, "") is False, "grammaire sans ε refuse le mot vide")
check(gf.appartient({"S": [("a",)]}, "a") is True, "grammaire S->a accepte 'a'")

print(f"\n=== valide_grammaires_formelles : {ok}/{ok+ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
