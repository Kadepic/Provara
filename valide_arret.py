"""VALIDE arret.py — ADVERSE, FAUX=0.

Ancres : arrêt borné mécanique (boucles finies -> ('arrete', n) EXACT ; boucle infinie -> timeout ;
programme vide -> arrete,0 ; bornes de budget). Théorème de Turing : arret_general_decidable()=False
(fait établi) et argument_diagonal()=True (preuve par l'absurde constructive, H se trompe toujours).
SOUNDNESS : budget <= 0 / non entier -> ValueError ; programme non appelable / non itérable -> ValueError ;
décideur non appelable / verdict invalide -> ValueError. DÉTERMINISME : mêmes entrées -> mêmes sorties.
"""
import arret as M

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


# ---- programmes-machines de test (générateurs d'étapes) ----
def fini(n):
    def prog(e):
        for _ in range(n):
            yield
    return prog


def vide(e):
    return
    yield            # générateur qui ne produit aucune étape


def infini(e):
    while True:
        yield


def jusqua_arret(seuil):
    # s'arrête après `seuil` pas : modèle d'un calcul borné
    def prog(e):
        i = 0
        while i < seuil:
            i += 1
            yield
    return prog


# ---- ARRÊT BORNÉ : boucles finies -> ('arrete', n) EXACT ----
check(M.sarrete_dans(fini(3), None, 100) == ('arrete', 3), "boucle finie 3 pas -> arrete,3")
check(M.sarrete_dans(fini(0), None, 100) == ('arrete', 0), "boucle finie 0 pas -> arrete,0")
check(M.sarrete_dans(fini(10), None, 100) == ('arrete', 10), "boucle finie 10 pas -> arrete,10")
check(M.sarrete_dans(vide, None, 5) == ('arrete', 0), "programme vide -> arrete,0")
check(M.sarrete_dans(jusqua_arret(7), "x", 1000) == ('arrete', 7), "calcul borné 7 pas -> arrete,7")

# ---- BOUCLE INFINIE -> timeout au budget ----
check(M.sarrete_dans(infini, None, 50) == ('timeout',), "boucle infinie -> timeout")
check(M.sarrete_dans(infini, None, 1) == ('timeout',), "boucle infinie budget 1 -> timeout")
check(len(M.sarrete_dans(infini, None, 50)) == 1, "timeout est un 1-uplet")

# ---- BORNES DE BUDGET (il faut n+1 avancées pour CONFIRMER l'arrêt d'un programme à n pas) ----
check(M.sarrete_dans(fini(3), None, 4) == ('arrete', 3), "n=3 pas, budget 4 -> arrete,3 (limite)")
check(M.sarrete_dans(fini(3), None, 3) == ('timeout',), "n=3 pas, budget 3 -> timeout (pas confirmé)")
check(M.sarrete_dans(fini(3), None, 2) == ('timeout',), "n=3 pas, budget 2 -> timeout")

# timeout est SOUND : ne se transforme jamais en faux « arrete » sous budget insuffisant
for b in range(1, 4):
    check(M.sarrete_dans(fini(5), None, b) == ('timeout',), f"5 pas, budget {b} -> timeout (jamais faux arrete)")

# ---- THÉORÈME DE TURING (faits établis) ----
check(M.arret_general_decidable() is False, "arret général indécidable -> False (Turing 1936)")
check(M.argument_diagonal() is True, "argument diagonal -> True (preuve par l'absurde)")
check(isinstance(M.THEOREME_TURING, str) and "arrêt" in M.THEOREME_TURING, "énoncé du théorème présent")

# ---- DIAGONALISATION CONSTRUCTIVE : tout décideur prétendu se trompe sur (D,D) ----
H_dit_arrete = lambda p, x: 'arrete'
H_dit_boucle = lambda p, x: 'boucle'
D1 = M.programme_diagonal(H_dit_arrete)
D2 = M.programme_diagonal(H_dit_boucle)
# H dit 'arrete' -> D boucle réellement -> timeout : H A TORT
check(M.sarrete_dans(D1, "D", 64) == ('timeout',), "H='arrete' -> D boucle (H a tort)")
# H dit 'boucle' -> D s'arrête réellement -> arrete,0 : H A TORT
check(M.sarrete_dans(D2, "D", 64) == ('arrete', 0), "H='boucle' -> D s'arrête (H a tort)")
# avec ces décideurs concrets, l'argument confirme la contradiction
check(M.argument_diagonal(H_dit_arrete) is True, "diagonal réfute H='arrete'")
check(M.argument_diagonal(H_dit_boucle) is True, "diagonal réfute H='boucle'")

# ---- DÉTERMINISME ----
check(M.sarrete_dans(fini(4), None, 100) == M.sarrete_dans(fini(4), None, 100), "déterminisme arrete")
check(M.sarrete_dans(infini, None, 20) == M.sarrete_dans(infini, None, 20), "déterminisme timeout")
check(M.argument_diagonal() == M.argument_diagonal(), "déterminisme argument_diagonal")

# ---- SOUNDNESS : abstention stricte ----
check(leve(M.sarrete_dans, infini, None, 0), "budget 0 -> ValueError")
check(leve(M.sarrete_dans, infini, None, -5), "budget négatif -> ValueError")
check(leve(M.sarrete_dans, infini, None, 3.5), "budget non entier -> ValueError")
check(leve(M.sarrete_dans, infini, None, True), "budget booléen -> ValueError")
check(leve(M.sarrete_dans, 42, None, 10), "programme non appelable (int) -> ValueError")
check(leve(M.sarrete_dans, "abc", None, 10), "programme non appelable (str) -> ValueError")
check(leve(M.sarrete_dans, (lambda e: 99), None, 10), "programme non itérable (renvoie int) -> ValueError")
check(leve(M.programme_diagonal, 42), "programme_diagonal décideur non appelable -> ValueError")
check(leve(M.argument_diagonal, 42), "argument_diagonal décideur non appelable -> ValueError")
check(leve(M.argument_diagonal, (lambda p, x: 'peut-etre')), "verdict invalide -> ValueError")

print(f"\n=== valide_arret : {ok}/{ok + ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
