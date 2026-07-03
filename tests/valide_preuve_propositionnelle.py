"""Validateur ADVERSARIAL de preuve_propositionnelle — ancres logiques connues + oracle indépendant
(est_tautologie de algebre_boole) + soundness (mal formé -> ValueError) + déterminisme. FAUX=0."""
from __future__ import annotations

import preuve_propositionnelle as M
import algebre_boole as B

ok = ko = 0


def check(cond, label):
    global ok, ko
    if cond:
        ok += 1
    else:
        ko += 1
        print("KO:", label)


def leve(fn, *a):
    try:
        fn(*a)
        return False
    except ValueError:
        return True
    except Exception:
        return False


def oracle(premisses, conclusion):
    """Vérité-terrain indépendante : (∧premisses) -> conclusion est-elle une tautologie ? (via algebre_boole)."""
    conj = " & ".join(f"({p})" for p in premisses) if premisses else "1"
    return B.est_tautologie(f"({conj}) -> ({conclusion})")


# ---------- 1. Les quatre CAS imposés par la spécification ----------
check(M.inference_valide(["p", "p -> q"], "q") is True, "modus ponens valide")
check(M.inference_valide(["p -> q", "~q"], "~p") is True, "modus tollens valide")
check(M.inference_valide(["p -> q", "q"], "p") is False, "affirmation du conséquent INVALIDE")
check(M.inference_valide(["p"], "q") is False, "non-séquence INVALIDE")

# ---------- 2. Inférences VALIDES classiques (ancres de théorie de la démonstration) ----------
valides = [
    (["p -> q", "q -> r"], "p -> r"),        # syllogisme hypothétique
    (["p | q", "~p"], "q"),                   # syllogisme disjonctif
    (["p -> q", "r -> s", "p | r"], "q | s"),  # dilemme constructif
    (["p & q"], "p"),                        # simplification
    (["p", "q"], "p & q"),                   # conjonction
    (["p"], "p | q"),                        # addition
    (["p | q", "~p | r"], "q | r"),          # résolution
    (["p", "~p"], "q"),                      # ex falso quodlibet (prémisses contradictoires)
    (["~(p & q)"], "~p | ~q"),               # De Morgan (sens 1)
    (["~p | ~q"], "~(p & q)"),               # De Morgan (sens 2)
    (["p <-> q", "p"], "q"),                 # biconditionnel
    (["p <-> q", "q"], "p"),
    ([], "p | ~p"),                          # tiers exclu, sans prémisse
    (["a -> b", "b -> c", "c -> d", "a"], "d"),
]
for prem, concl in valides:
    check(M.inference_valide(prem, concl) is True, f"VALIDE: {prem} |- {concl}")

# ---------- 3. Inférences INVALIDES classiques (sophismes) ----------
invalides = [
    (["p -> q", "~p"], "~q"),                # négation de l'antécédent
    (["p -> q", "q"], "p"),                  # affirmation du conséquent
    (["p | q"], "p & q"),                    # disjonction n'entraîne pas conjonction
    ([], "p"),                               # une variable seule n'est pas tautologie
    (["p -> q"], "q -> p"),                  # converse
    (["p"], "p & q"),
]
for prem, concl in invalides:
    check(M.inference_valide(prem, concl) is False, f"INVALIDE: {prem} |- {concl}")

# ---------- 4. Croisement avec l'oracle indépendant (est_tautologie) ----------
for prem, concl in valides + invalides + [(["p", "p -> q"], "q"), (["p -> q", "q"], "p")]:
    check(M.inference_valide(prem, concl) == oracle(prem, concl), f"oracle accord: {prem} |- {concl}")

# ---------- 5. Règles de déduction (applications syntaxiques exactes) ----------
check(M.regle_modus_ponens("p -> q", "p") == "q", "MP p->q,p => q")
check(M.regle_modus_ponens("(a & b) -> c", "a & b") == "c", "MP (a&b)->c, a&b => c")
check(B.equivalent(M.regle_modus_ponens("p -> (q & r)", "p"), "q & r"), "MP conséquent composé")
check(M.regle_modus_ponens("p -> q", "(p)") == "q", "MP robuste aux parenthèses sur l'antécédent")
check(M.regle_modus_tollens("p -> q", "~q") == "~p", "MT p->q,~q => ~p")
check(B.equivalent(M.regle_modus_tollens("a -> (b | c)", "~(b | c)"), "~a"), "MT antécédent simple")

# soundness sémantique des règles : l'inférence dérivée est valide
check(M.inference_valide(["p -> q", "p"], M.regle_modus_ponens("p -> q", "p")) is True, "MP dérive du valide")
check(M.inference_valide(["p -> q", "~q"], M.regle_modus_tollens("p -> q", "~q")) is True, "MT dérive du valide")

# ---------- 6. SOUNDNESS : entrées mal formées / formes non respectées -> ValueError ----------
check(leve(M.inference_valide, ["p &"], "q"), "prémisse mal formée -> ValueError")
check(leve(M.inference_valide, ["p"], "q ->"), "conclusion mal formée -> ValueError")
check(leve(M.inference_valide, ["p"], ""), "conclusion vide -> ValueError")
check(leve(M.inference_valide, "p", "q"), "premisses chaîne (non liste) -> ValueError")
check(leve(M.inference_valide, ["p"], 123), "conclusion non-chaîne -> ValueError")
check(leve(M.inference_valide, [5], "q"), "prémisse non-chaîne -> ValueError")
check(leve(M.inference_valide, ["p ) ("], "q"), "parenthèses déséquilibrées -> ValueError")
check(leve(M.inference_valide, ["p @ q"], "q"), "caractère invalide -> ValueError")
check(leve(M.regle_modus_ponens, "p & q", "p"), "MP sur non-implication -> ValueError")
check(leve(M.regle_modus_ponens, "p -> q", "r"), "MP antécédent non concordant -> ValueError")
check(leve(M.regle_modus_ponens, "p ->", "p"), "MP implication mal formée -> ValueError")
check(leve(M.regle_modus_tollens, "p -> q", "q"), "MT seconde prémisse non négative -> ValueError")
check(leve(M.regle_modus_tollens, "p -> q", "~r"), "MT négation du mauvais terme -> ValueError")
check(leve(M.regle_modus_tollens, "p & q", "~q"), "MT sur non-implication -> ValueError")

# borne d'abstention 2ⁿ (trop de variables)
trop = " | ".join(chr(ord("a") + i) for i in range(M._MAX_VARS + 1))
check(leve(M.inference_valide, [], trop), f"{M._MAX_VARS + 1} variables -> abstention ValueError")

# ---------- 7. Déterminisme ----------
check(M.inference_valide(["p", "p -> q"], "q") == M.inference_valide(["p", "p -> q"], "q"), "déterminisme inférence")
check(M.regle_modus_ponens("p -> q", "p") == M.regle_modus_ponens("p -> q", "p"), "déterminisme règle MP")

print(f"\n=== valide_preuve_propositionnelle : {ok}/{ok+ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
