"""
VALIDE anneaux_corps.py — held-out ADVERSE.

ANCRES EXTERNES NON CIRCULAIRES (faits classiques, PAS recalculés par le module testé) :
  • ℤ/nℤ est un corps ⇔ n premier (théorème classique) : n ∈ {2,3,5,7} -> CORPS ; n ∈ {4,6,8,9} -> PAS corps.
    Les tables (i+j) mod n et (i·j) mod n sont construites ICI par arithmétique modulaire directe,
    indépendamment du module testé.
  • ANCRE DISCRIMINANTE Z/4Z : 2·x mod 4 ∈ {0, 2}, jamais 1 — vérifié À LA MAIN sur la table construite ici ;
    donc 2 n'a pas d'inverse et Z/4Z n'est pas un corps (bien qu'anneau commutatif unitaire).
  • Z/6Z : diviseurs de zéro, 2·3 = 6 ≡ 0 (lu dans la table construite ici) -> pas un corps.
  • Anneau nul {0} : anneau commutatif unitaire mais PAS un corps (0 = 1, exclu par définition).
  • 2ℤ/4ℤ = {0, 2} mod 4 : anneau SANS unité (rng classique : tous les produits valent 0).
  • Anneau des matrices [[x,y],[0,0]] sur F2 (4 éléments) : anneau NON commutatif classique, sans unité.
  • S3 (via groupes.compose_permutations, SECOND chemin de code) comme « addition » : groupe NON abélien
    -> pas un anneau, le diagnostic nomme la commutativité de l'addition.
  • DOUBLE CHEMIN : pour chaque n, (ℤ/nℤ, +) est un groupe vérifié AUSSI par groupes.est_groupe
    sur la matrice d'indices produite par table_en_indices.

SOUNDNESS : elements vide/doublon/bool/float, tables non carrées, entrée hors ensemble, niveau inconnu,
bool comme entrée de table -> ValueError. DÉTERMINISME : deux appels identiques.
"""
import itertools

import anneaux_corps as AC
import groupes

ok = 0
ko = 0


def check(cond, label):
    global ok, ko
    if cond:
        ok += 1
    else:
        ko += 1
        print(f"  FAIL: {label}")


def leve(fn, *a, **kw):
    """True ssi fn(*a) lève ValueError (abstention structurelle)."""
    try:
        fn(*a, **kw)
        return False
    except ValueError:
        return True


def zn(n):
    """Tables de ℤ/nℤ par arithmétique modulaire DIRECTE (ancre indépendante du module testé)."""
    elts = list(range(n))
    add = [[(i + j) % n for j in range(n)] for i in range(n)]
    mul = [[(i * j) % n for j in range(n)] for i in range(n)]
    return elts, add, mul


# ── 1) ANCRE : ℤ/pℤ est un CORPS pour p premier (2, 3, 5, 7) ──
for p in (2, 3, 5, 7):
    e, a, m = zn(p)
    check(AC.est_corps(e, a, m) is True, f"Z/{p}Z est un corps (p premier)")
    check(AC.est_anneau(e, a, m) is True, f"Z/{p}Z est un anneau")
check(AC.diagnostic(*zn(5), niveau="corps") == [], "diagnostic(Z/5Z, corps) = aucune violation")

# ── 2) ANCRE : ℤ/nℤ n'est PAS un corps pour n composé (4, 6, 8, 9), mais anneau commutatif unitaire ──
for n in (4, 6, 8, 9):
    e, a, m = zn(n)
    check(AC.est_anneau(e, a, m) is True, f"Z/{n}Z est un anneau")
    check(AC.est_anneau_unitaire(e, a, m) is True, f"Z/{n}Z est unitaire")
    check(AC.est_anneau_commutatif(e, a, m) is True, f"Z/{n}Z est commutatif")
    check(AC.est_corps(e, a, m) is False, f"Z/{n}Z n'est PAS un corps (n composé)")

# ── 3) ANCRE DISCRIMINANTE FORTE : dans Z/4Z, 2·x ne vaut JAMAIS 1 (lu dans la table brute) ──
e4, a4, m4 = zn(4)
check(all(m4[2][x] != 1 for x in range(4)), "table brute Z/4Z : 2·x mod 4 ∈ {0,2}, jamais 1")
diag4 = AC.diagnostic(e4, a4, m4, niveau="corps")
check(any("inversibilité" in v for v in diag4), "diagnostic(Z/4Z) nomme l'inversibilité des non nuls")
check(all("distributivité" not in v for v in diag4), "diagnostic(Z/4Z) : distributivité NON violée")

# ── 4) ANCRE : Z/6Z a des diviseurs de zéro (2·3 = 6 ≡ 0, lu dans la table brute) ──
e6, a6, m6 = zn(6)
check(m6[2][3] == 0, "table brute Z/6Z : 2·3 ≡ 0 (diviseurs de zéro)")
check(any("inversibilité" in v for v in AC.diagnostic(e6, a6, m6)), "diagnostic(Z/6Z) nomme l'inversibilité")

# ── 5) ANCRE : anneau nul {0} — anneau commutatif unitaire, PAS un corps (0 = 1 exclu) ──
e1, a1, m1 = zn(1)
check(AC.est_anneau(e1, a1, m1) is True, "anneau nul : est un anneau")
check(AC.est_anneau_unitaire(e1, a1, m1) is True, "anneau nul : unitaire (0 = 1)")
check(AC.est_anneau_commutatif(e1, a1, m1) is True, "anneau nul : commutatif")
check(AC.est_corps(e1, a1, m1) is False, "anneau nul : PAS un corps (corps trivial exclu)")
check(any("corps trivial" in v for v in AC.diagnostic(e1, a1, m1)), "diagnostic(anneau nul) nomme 0 = 1")

# ── 6) ANCRE : 2ℤ/4ℤ = {0, 2} mod 4 — anneau SANS unité (rng classique, tous produits nuls) ──
e22 = [0, 2]
a22 = [[0, 2], [2, 0]]          # 0+0=0, 0+2=2, 2+2=4≡0 (mod 4), à la main
m22 = [[0, 0], [0, 0]]          # 0·0=0, 0·2=0, 2·2=4≡0 (mod 4), à la main
check(AC.est_anneau(e22, a22, m22) is True, "2Z/4Z est un anneau")
check(AC.est_anneau_unitaire(e22, a22, m22) is False, "2Z/4Z n'a PAS d'unité")
check(any("neutre (multiplication)" in v for v in AC.diagnostic(e22, a22, m22, niveau="anneau_unitaire")),
      "diagnostic(2Z/4Z, unitaire) nomme le neutre multiplicatif")
check(AC.est_corps(e22, a22, m22) is False, "2Z/4Z n'est pas un corps")

# ── 7) DISTRIBUTIVITÉ CASSÉE : ({0,1}, xor, mul ≡ 1) — a·(b+c)=1 mais a·b+a·c=1+1=0 ──
eD = [0, 1]
aD = [[0, 1], [1, 0]]           # xor = addition de F2, à la main
mD = [[1, 1], [1, 1]]           # produit constant 1 : associatif, mais PAS distributif
check(AC.est_anneau(eD, aD, mD) is False, "mul constante 1 sur F2-additif : PAS un anneau")
diagD = AC.diagnostic(eD, aD, mD, niveau="anneau")
check(any("distributivité" in v for v in diagD), "diagnostic nomme la distributivité")
check("distributivité (gauche)" in diagD and "distributivité (droite)" in diagD,
      "distributivité violée des DEUX côtés")

# ── 8) MULTIPLICATION NON ASSOCIATIVE : soustraction mod 3 comme « produit » ──
eS = [0, 1, 2]
aS = [[(i + j) % 3 for j in range(3)] for i in range(3)]
mS = [[(i - j) % 3 for j in range(3)] for i in range(3)]   # (1−1)−1 = 2 ≠ 1 = 1−(1−1)
check(((1 - 1) - 1) % 3 != (1 - (1 - 1)) % 3, "ancre à la main : la soustraction n'est pas associative")
check(AC.est_anneau(eS, aS, mS) is False, "produit = soustraction mod 3 : PAS un anneau")
check(any("associativité (multiplication)" in v for v in AC.diagnostic(eS, aS, mS, niveau="anneau")),
      "diagnostic nomme l'associativité de la multiplication")

# ── 9) ADDITION NON ABÉLIENNE : S3 (bâti par groupes.compose_permutations, second chemin) ──
perms = list(itertools.permutations(range(3)))             # perms[0] = identité
ip = {p: i for i, p in enumerate(perms)}
eG = list(range(6))
aG = [[ip[groupes.compose_permutations(perms[i], perms[j])] for j in range(6)] for i in range(6)]
mG = [[0] * 6 for _ in range(6)]                           # produit constant = neutre additif (identité)
check(groupes.est_groupe(aG) is True, "S3 est bien un groupe (second chemin groupes.est_groupe)")
check(any(aG[i][j] != aG[j][i] for i in range(6) for j in range(6)),
      "ancre à la main : la table de S3 n'est pas symétrique (non abélien)")
check(AC.est_anneau(eG, aG, mG) is False, "addition = S3 : PAS un anneau (groupe non abélien)")
check(any("commutativité (addition)" in v for v in AC.diagnostic(eG, aG, mG, niveau="anneau")),
      "diagnostic nomme la commutativité de l'addition")

# ── 10) ANCRE : anneau NON commutatif à 4 éléments — matrices [[x,y],[0,0]] sur F2 ──
#     (x1,y1)·(x2,y2) = (x1·x2, x1·y2) mod 2 ; addition composante par composante mod 2 (à la main).
eM = ["00", "10", "01", "11"]   # "xy" = matrice [[x, y], [0, 0]]
paires = [(0, 0), (1, 0), (0, 1), (1, 1)]
im = {p: eM[i] for i, p in enumerate(paires)}
aM = [[im[((x1 + x2) % 2, (y1 + y2) % 2)] for (x2, y2) in paires] for (x1, y1) in paires]
mM = [[im[((x1 * x2) % 2, (x1 * y2) % 2)] for (x2, y2) in paires] for (x1, y1) in paires]
check(im[(1, 0)] == "10" and mM[1][3] != mM[3][1], "ancre à la main : (1,0)·(1,1) ≠ (1,1)·(1,0)")
check(AC.est_anneau(eM, aM, mM) is True, "matrices [[x,y],[0,0]] sur F2 : anneau")
check(AC.est_anneau_commutatif(eM, aM, mM) is False, "matrices [[x,y],[0,0]] : NON commutatif")
check(any("commutativité (multiplication)" in v
          for v in AC.diagnostic(eM, aM, mM, niveau="anneau_commutatif")),
      "diagnostic nomme la commutativité de la multiplication")
check(AC.est_corps(eM, aM, mM) is False, "matrices [[x,y],[0,0]] : pas un corps")

# ── 11) DOUBLE CHEMIN : (ℤ/nℤ, +) est un groupe AUSSI selon groupes.est_groupe ──
for n in range(2, 10):
    e, a, _ = zn(n)
    check(groupes.est_groupe(AC.table_en_indices(e, a)) is True,
          f"(Z/{n}Z, +) est un groupe selon groupes.est_groupe (second chemin)")

# ── 12) GÉNÉRICITÉ : F2 avec des étiquettes str ("z" = 0, "u" = 1) reste un corps ──
eF = ["z", "u"]
aF = [["z", "u"], ["u", "z"]]
mF = [["z", "z"], ["z", "u"]]
check(AC.est_corps(eF, aF, mF) is True, "F2 étiqueté en str : corps")

# ── 13) SOUNDNESS — elements mal formés -> ValueError ──
e2, a2, m2 = zn(2)
check(leve(AC.est_anneau, [], [], []), "elements vide -> ValueError")
check(leve(AC.est_anneau, [0, 0], a2, m2), "elements avec doublon -> ValueError")
check(leve(AC.est_anneau, [True, 1], a2, m2), "élément bool -> ValueError")
check(leve(AC.est_anneau, [0.0, 1.0], a2, m2), "éléments float -> ValueError")
check(leve(AC.est_anneau, "01", a2, m2), "elements = str (pas liste) -> ValueError")
check(leve(AC.est_anneau, [None, 1], a2, m2), "élément None -> ValueError")

# ── 14) SOUNDNESS — tables mal formées -> ValueError ──
check(leve(AC.est_anneau, e2, [[0, 1]], m2), "table_add non carrée (1 ligne) -> ValueError")
check(leve(AC.est_anneau, e2, [[0, 1], [1]], m2), "ligne trop courte -> ValueError")
check(leve(AC.est_anneau, e2, [[0, 1, 0], [1, 0, 1]], m2), "lignes trop longues -> ValueError")
check(leve(AC.est_anneau, e2, [[0, 7], [1, 0]], m2), "entrée 7 hors ensemble -> ValueError")
check(leve(AC.est_anneau, e2, a2, [[0, True], [0, 1]]), "entrée bool (True≡1) -> ValueError")
check(leve(AC.est_anneau, e2, 5, m2), "table_add = int -> ValueError")
check(leve(AC.est_anneau, e2, a2, [[0, 0], "01"]), "ligne = str -> ValueError")
check(leve(AC.est_corps, e2, a2, [[0, 0], [0, 2]]), "table_mul hors ensemble -> ValueError")
check(leve(AC.table_en_indices, e2, [[0, 1], [1, 2]]), "table_en_indices hors ensemble -> ValueError")

# ── 15) SOUNDNESS — niveau de diagnostic inconnu -> ValueError ──
check(leve(AC.diagnostic, e2, a2, m2, niveau="groupe"), "niveau inconnu -> ValueError")
check(leve(AC.diagnostic, e2, a2, m2, niveau=""), "niveau vide -> ValueError")

# ── 16) DÉTERMINISME ──
check(AC.est_corps(*zn(7)) == AC.est_corps(*zn(7)), "déterminisme est_corps")
check(AC.diagnostic(*zn(4)) == AC.diagnostic(*zn(4)), "déterminisme diagnostic")
check(AC.est_anneau(eG, aG, mG) == AC.est_anneau(eG, aG, mG), "déterminisme est_anneau (S3)")

print(f"\n=== valide_anneaux_corps : {ok}/{ok+ko} ===")
import sys; sys.exit(0 if ko == 0 else 1)
