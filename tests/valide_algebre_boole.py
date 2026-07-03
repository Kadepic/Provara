"""VALIDE algebre_boole.py — ADVERSE, FAUX=0. Lois logiques CONNUES (De Morgan, tiers exclu, distributivité, modus
ponens, contraposition…) + équivalences + SOUNDNESS (expression mal formée -> ValueError ; un non-théorème n'est
JAMAIS déclaré tautologie)."""
import algebre_boole as B

ok = 0
ko = 0


def check(c, l):
    global ok, ko
    if c:
        ok += 1
    else:
        ko += 1
        print(f"  FAIL: {l}")


def leve(fn, *a):
    try:
        fn(*a)
        return False
    except ValueError:
        return True
    except Exception:
        return False


# TAUTOLOGIES connues
for taut in ["a | ~a", "~(a & ~a)", "~(a & b) <-> (~a | ~b)", "~(a | b) <-> (~a & ~b)",
             "a & (b | c) <-> (a & b) | (a & c)", "a | (b & c) <-> (a | b) & (a | c)",
             "((a -> b) & a) -> b", "((a -> b) & ~b) -> ~a", "(a -> b) <-> (~b -> ~a)",
             "a <-> ~~a", "(a -> b) <-> (~a | b)", "(a & b) -> a", "a -> (a | b)",
             "((a -> b) & (b -> c)) -> (a -> c)"]:
    check(B.est_tautologie(taut), f"tautologie : {taut}")

# NON-tautologies (un théorème factice ne doit PAS passer)
for non in ["a", "a & b", "a -> b", "a | b", "a <-> b", "(a | b) -> (a & b)"]:
    check(not B.est_tautologie(non), f"NON-tautologie : {non}")

# CONTRADICTIONS / SATISFIABILITÉ
check(B.est_contradiction("a & ~a"), "a & ~a contradiction")
check(B.est_contradiction("(a -> b) & a & ~b"), "modus ponens nié = contradiction")
check(not B.est_contradiction("a"), "a n'est pas une contradiction")
check(B.est_satisfiable("a -> b") and B.est_satisfiable("a & b") and not B.est_satisfiable("a & ~a"),
      "satisfiabilité")

# ÉQUIVALENCES
check(B.equivalent("a -> b", "~a | b"), "implication ≡ ~a|b")
check(B.equivalent("a <-> b", "(a & b) | (~a & ~b)"), "équivalence ≡ (a&b)|(~a&~b)")
check(B.equivalent("a ^ b", "(a | b) & ~(a & b)"), "XOR ≡ ou exclusif")
check(B.equivalent("a & b", "b & a"), "commutativité")
check(not B.equivalent("a -> b", "b -> a"), "implication non symétrique")

# ÉVALUATION ponctuelle
check(B.evalue("a & b", {"a": True, "b": False}) is False, "T&F = F")
check(B.evalue("a -> b", {"a": True, "b": False}) is False, "T->F = F")
check(B.evalue("a -> b", {"a": False, "b": False}) is True, "F->F = T")
check(B.evalue("~a | b", {"a": True, "b": True}) is True, "~T|T = T")
check(sorted(B.variables("a & (b | c) -> d")) == ["a", "b", "c", "d"], "extraction des variables")
check(len(B.table_verite("a & b")) == 4, "table de vérité 2 variables = 4 lignes")

# SOUNDNESS
check(leve(B.evalue, "a &", {"a": True}), "expression incomplète -> ValueError")
check(leve(B.est_tautologie, "(a & b"), "parenthèse non fermée -> ValueError")
check(leve(B.est_tautologie, ""), "expression vide -> ValueError")
check(leve(B.est_tautologie, "a # b"), "opérateur invalide -> ValueError")
check(leve(B.evalue, "a & b", {"a": True}), "variable non affectée -> ValueError")

print(f"\n=== valide_algebre_boole : {ok}/{ok + ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
