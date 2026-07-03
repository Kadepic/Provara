"""VALIDE godel.py — held-out ADVERSE, FAUX=0.

Ancres : valeurs de numérotation calculées À LA MAIN (∏ p_i^{code}) + bijection encode/decode (aller-retour) +
injectivité (suites distinctes -> numéros distincts) + énoncés de référence des théorèmes.
SOUNDNESS : suite vide / symbole hors alphabet / numéro ≤ 1 / non entier / trou de premier / code hors alphabet /
n de théorème hors {1,2} -> ValueError (jamais une réponse inventée). + déterminisme.
"""
import godel as M

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


# ── NUMÉROTATION — valeurs calculées à la main ──
# code('0')=1, code('S')=2 ; p_0=2, p_1=3, p_2=5, p_3=7
check(M.godel_numero(['0']) == 2, "['0'] -> 2^1 = 2")
check(M.godel_numero(['0', '0']) == 6, "['0','0'] -> 2^1·3^1 = 6")
check(M.godel_numero(['S', '0']) == 12, "['S','0'] -> 2^2·3^1 = 12")
check(M.godel_numero(['0', 'S']) == 18, "['0','S'] -> 2^1·3^2 = 18")
check(M.godel_numero(['x', 'y']) == 2 ** 16 * 3 ** 17, "['x','y'] -> 2^16·3^17")
check(M.code_symbole('S') == 2 and M.code_symbole('0') == 1 and M.code_symbole('z') == 18, "codes alphabet")

# ── BIJECTION — aller-retour sur plusieurs suites ──
for suite in (['0'], ['S', '0'], ['0', 'S'], ['∀', 'x', '=', '0'],
              ['∀', 'x', '(', 'S', '0', ')'], ['¬', '∃', 'y', '∧', 'x', '=', 'z']):
    check(M.decode_godel(M.godel_numero(suite)) == suite, f"aller-retour {suite}")
check(M.decode_godel(12) == ['S', '0'], "decode(12) = ['S','0']")
check(M.decode_godel(6) == ['0', '0'], "decode(6) = ['0','0']")
# couverture de tout l'alphabet en aller-retour (chaque symbole exactement)
for s in M.ALPHABET:
    check(M.decode_godel(M.godel_numero([s])) == [s], f"aller-retour symbole {s!r}")

# ── INJECTIVITÉ — suites distinctes -> numéros distincts ──
check(M.godel_numero(['S', '0']) != M.godel_numero(['0', 'S']), "ordre distinct -> numéro distinct")
check(M.godel_numero(['x', 'y']) != M.godel_numero(['y', 'x']), "['x','y'] != ['y','x']")
nums = [M.godel_numero(['0']), M.godel_numero(['0', '0']), M.godel_numero(['S']),
        M.godel_numero(['S', '0']), M.godel_numero(['0', 'S', '0'])]
check(len(set(nums)) == len(nums), "5 suites -> 5 numéros distincts")

# ── THÉORÈMES — faits de référence (Gödel 1931) ──
check('incomplet' in M.theoreme(1) and 'démontrable' in M.theoreme(1), "1er théorème : énoncé d'incomplétude")
check('cohérence' in M.theoreme(2) and 'Coh(T)' in M.theoreme(2), "2nd théorème : non-démontrabilité de Coh(T)")
check(M.theoreme() == M.theoreme(1), "theoreme() par défaut = 1er")

# ── SOUNDNESS — abstention stricte (jamais de faux positif) ──
check(leve(M.godel_numero, []), "suite vide -> ValueError")
check(leve(M.godel_numero, ['@']), "symbole hors alphabet -> ValueError")
check(leve(M.godel_numero, ['0', 'Q']), "symbole inconnu en 2e position -> ValueError")
check(leve(M.godel_numero, '0S'), "chaîne (pas liste/tuple) -> ValueError")
check(leve(M.code_symbole, '@'), "code_symbole hors alphabet -> ValueError")
check(leve(M.decode_godel, 1), "decode(1) (suite vide) -> ValueError")
check(leve(M.decode_godel, 0), "decode(0) -> ValueError")
check(leve(M.decode_godel, -12), "decode(négatif) -> ValueError")
check(leve(M.decode_godel, 3), "decode(3) : manque le premier 2 -> ValueError")
check(leve(M.decode_godel, 10), "decode(10=2·5) : trou (pas de 3) -> ValueError")
check(leve(M.decode_godel, 13), "decode(13) : premier isolé -> ValueError")
check(leve(M.decode_godel, 2 ** 19), "decode(2^19) : exposant 19 hors alphabet -> ValueError")
check(leve(M.decode_godel, 2.0), "decode(float) -> ValueError")
check(leve(M.decode_godel, True), "decode(bool) -> ValueError")
check(leve(M.theoreme, 3), "théorème n=3 hors catalogue -> ValueError")
check(leve(M.theoreme, 0), "théorème n=0 -> ValueError")
check(leve(M.theoreme, 1.0), "théorème n float -> ValueError")

# ── DÉTERMINISME ──
check(M.godel_numero(['S', 'S', '0']) == M.godel_numero(['S', 'S', '0']), "déterminisme encode")
check(M.decode_godel(360) == M.decode_godel(360), "déterminisme decode")

print(f"\n=== valide_godel : {ok}/{ok+ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
