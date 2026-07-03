"""VALIDE langages_formels.py — held-out ADVERSE, FAUX=0. Ancres EXTERNES connues (appartenance à des langages
hors-contexte classiques a^n b^n et parenthèses équilibrées, vérifiables à la main) + classification de Chomsky +
SOUNDNESS : grammaire mal formée / non-CNF / entrée invalide -> ValueError (jamais faux) + déterminisme.
"""
import langages_formels as M

ok = 0
ko = 0


def check(cond, label):
    global ok, ko
    if cond:
        ok += 1
    else:
        ko += 1
        print(f"  FAIL: {label}")


def leve(fn, *a):
    try:
        fn(*a)
        return False
    except ValueError:
        return True
    except Exception:
        return False


# ── GRAMMAIRES DE RÉFÉRENCE (CNF) ──
# L1 = { a^n b^n : n >= 1 }  ;  S -> aSb | ab  mis en CNF
G_ANBN = {"S": [("A", "B"), ("A", "C")],
          "A": [("a",)], "B": [("b",)], "C": [("S", "B")]}
# L2 = parenthèses équilibrées non vides (langage de Dyck) ; S -> SS | () | (S)  en CNF
G_PAR = {"S": [("S", "S"), ("L", "R"), ("L", "T")],
         "T": [("S", "R")], "L": [("(",)], "R": [(")",)]}
# grammaire régulière (linéaire-droite) : a* b
G_REG = {"S": [("a", "S"), ("b",)]}
# grammaire linéaire-gauche : b a*
G_GAUCHE = {"S": [("S", "a"), ("b",)]}
# grammaire linéaire MIXTE (droite + gauche) -> non régulière par la forme
G_MIXTE = {"S": [("a", "S"), ("S", "b"), ("c",)]}


# ── CYK : a^n b^n — mots ACCEPTÉS (ancre = langage connu) ──
check(M.appartient(G_ANBN, "ab") is True, "a^n b^n accepte 'ab'")
check(M.appartient(G_ANBN, "aabb") is True, "a^n b^n accepte 'aabb'")
check(M.appartient(G_ANBN, "aaabbb") is True, "a^n b^n accepte 'aaabbb'")
check(M.appartient(G_ANBN, "aaaabbbb") is True, "a^n b^n accepte 'aaaabbbb'")
# ── mots REJETÉS ──
check(M.appartient(G_ANBN, "") is False, "a^n b^n rejette '' (n>=1)")
check(M.appartient(G_ANBN, "a") is False, "a^n b^n rejette 'a'")
check(M.appartient(G_ANBN, "b") is False, "a^n b^n rejette 'b'")
check(M.appartient(G_ANBN, "aab") is False, "a^n b^n rejette 'aab' (déséquilibré)")
check(M.appartient(G_ANBN, "abb") is False, "a^n b^n rejette 'abb' (déséquilibré)")
check(M.appartient(G_ANBN, "ba") is False, "a^n b^n rejette 'ba' (ordre)")
check(M.appartient(G_ANBN, "abab") is False, "a^n b^n rejette 'abab' (entrelacé)")
check(M.appartient(G_ANBN, "aabbb") is False, "a^n b^n rejette 'aabbb'")
check(M.appartient(G_ANBN, "c") is False, "a^n b^n rejette 'c' (terminal inconnu)")

# ── CYK : parenthèses équilibrées — ACCEPTÉS ──
check(M.appartient(G_PAR, "()") is True, "parenthèses accepte '()'")
check(M.appartient(G_PAR, "(())") is True, "parenthèses accepte '(())'")
check(M.appartient(G_PAR, "()()") is True, "parenthèses accepte '()()'")
check(M.appartient(G_PAR, "(()())") is True, "parenthèses accepte '(()())'")
check(M.appartient(G_PAR, "((()))") is True, "parenthèses accepte '((()))'")
# ── REJETÉS ──
check(M.appartient(G_PAR, "(") is False, "parenthèses rejette '('")
check(M.appartient(G_PAR, ")") is False, "parenthèses rejette ')'")
check(M.appartient(G_PAR, ")(") is False, "parenthèses rejette ')('")
check(M.appartient(G_PAR, "(()") is False, "parenthèses rejette '(()'")
check(M.appartient(G_PAR, "())") is False, "parenthèses rejette '())'")
check(M.appartient(G_PAR, "((") is False, "parenthèses rejette '(('")
check(M.appartient(G_PAR, "(())(") is False, "parenthèses rejette '(())('")

# ── FORME NORMALE DE CHOMSKY ──
check(M.est_forme_normale_chomsky(G_ANBN) is True, "G_ANBN est en CNF")
check(M.est_forme_normale_chomsky(G_PAR) is True, "G_PAR est en CNF")
check(M.est_forme_normale_chomsky(G_REG) is False, "G_REG (a,S) terminal en slot binaire -> pas CNF")
# unitaire S->A interdite en CNF
check(M.est_forme_normale_chomsky({"S": [("A",)], "A": [("a",)]}) is False, "production unitaire -> pas CNF")

# ── CLASSIFICATION DE CHOMSKY (par la forme) ──
check(M.classe_chomsky(G_ANBN) == "hors_contexte", "a^n b^n : grammaire hors-contexte")
check(M.classe_chomsky(G_PAR) == "hors_contexte", "parenthèses : grammaire hors-contexte")
check(M.classe_chomsky(G_REG) == "reguliere", "a* b : linéaire-droite -> reguliere")
check(M.classe_chomsky(G_GAUCHE) == "reguliere", "b a* : linéaire-gauche -> reguliere")
check(M.classe_chomsky(G_MIXTE) == "hors_contexte", "linéaire mixte -> non régulière par la forme")
check(M.classe_chomsky({"S": [("a",), ("b",)]}) == "reguliere", "S->a|b fini -> reguliere")

# ── ALPHABETS ──
check(M.terminaux(G_ANBN) == frozenset({"a", "b"}), "terminaux a^n b^n = {a,b}")
check(M.non_terminaux(G_ANBN) == frozenset({"S", "A", "B", "C"}), "non-terminaux a^n b^n")

# ── SOUNDNESS : abstention sur entrée invalide -> ValueError ──
check(leve(M.appartient, G_REG, "ab"), "appartient sur grammaire non-CNF -> ValueError")
check(leve(M.appartient, G_ANBN, 123), "mot non-str -> ValueError")
check(leve(M.appartient, G_ANBN, ["a", "b"]), "mot liste (non-str) -> ValueError")
check(leve(M.appartient, {}, "ab"), "grammaire vide -> ValueError")
check(leve(M.appartient, [("S", "AB")], "ab"), "grammaire non-dict -> ValueError")
check(leve(M.appartient, {"A": [("a",)]}, "a"), "axiome 'S' absent -> ValueError")
check(leve(M.appartient, {"S": ["ab"]}, "ab"), "production non-tuple -> ValueError")
check(leve(M.appartient, {"S": [("",)]}, "a"), "symbole vide -> ValueError")
check(leve(M.appartient, {"S": [("A", "B")], "A": [("a",)]}, "ab"),
      "production binaire référant un non-terminal non défini -> ValueError")
check(leve(M.appartient, {"S": [("A",)], "A": [("a",)]}, "a"), "production unitaire (non-CNF) -> ValueError")
check(leve(M.appartient, {"S": [("a", "b", "c")]}, "abc"), "production de longueur 3 (non-CNF) -> ValueError")
check(leve(M.classe_chomsky, {"X": [("a",)]}), "classe_chomsky sans axiome 'S' -> ValueError")
check(leve(M.est_forme_normale_chomsky, 42), "est_forme_normale_chomsky sur non-dict -> ValueError")
check(leve(M.terminaux, {"S": [("a", 5)]}), "symbole non-str -> ValueError")

# ── DÉTERMINISME ──
check(M.appartient(G_ANBN, "aaabbb") == M.appartient(G_ANBN, "aaabbb"), "déterminisme CYK")
check(M.classe_chomsky(G_REG) == M.classe_chomsky(G_REG), "déterminisme classe_chomsky")

print(f"\n=== valide_langages_formels : {ok}/{ok + ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
