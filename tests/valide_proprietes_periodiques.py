"""
VALIDE proprietes_periodiques.py — held-out ADVERSE.

ANCRES EXTERNES NON CIRCULAIRES (valeurs NIST/CRC largement tabulées, PAS recalculées par le module ;
écrites EN DUR ci-dessous, tolérance ±3 %) :
  • E_ionisation : H = 1312 kJ/mol ; He = 2372 (le plus élevé de TOUS les éléments) ; Li = 520 ;
    Ne = 2081 ; Na = 496 ; Ar = 1521 ; K = 419 (le plus bas de la période 4).
  • TENDANCES (faits) : E_ionisation CROÎT le long d'une période, DÉCROÎT le long d'un groupe ;
    le rayon DÉCROÎT le long d'une période, CROÎT le long d'un groupe.
  • Groupe 18 : E(He) > E(Ne) > E(Ar) > E(Kr) (décroissance dans le groupe).
  • ANCRE PIÈGE : Li -> Ne n'est PAS monotone — anomalies réelles B < Be et O < N (appariement 2p) ;
    le module ne doit PAS prétendre une monotonie stricte (sa chaîne de tendance doit le dire).
  • Rayons covalents de liaison simple : valeurs classiques de Pauling écrites en dur, Cl ≈ 99 pm et
    C ≈ 77 pm (tolérance ±6 % : définitions covalentes voisines) ; ordres classiques r(K) > r(Na) > r(Li),
    r(Br) > r(Cl) > r(F), r(Li) > r(Be) > r(B) > r(C) > r(N) > r(O) ; K = le plus grand rayon de Z=1..36.

SOUNDNESS : 'Xx', casse fautive, str vide, int, bool, None, NaN(float), prop inconnue, comparaison
dégénérée, égalité de table -> ValueError.
"""
import proprietes_periodiques as P

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
    """True ssi fn(*a) lève ValueError (abstention structurelle)."""
    try:
        fn(*a)
        return False
    except ValueError:
        return True


def pct(x, attendu, tol=0.03):
    """|x − attendu| ≤ tol·attendu (tolérance relative)."""
    return abs(x - attendu) <= tol * attendu


E = P.energie_premiere_ionisation
R = P.rayon_atomique

# ── 1) ANCRES IONISATION (kJ/mol, NIST/CRC en dur, ±3 %) ──
check(pct(E("H"), 1312.0), "E(H) ≈ 1312 kJ/mol (NIST)")
check(pct(E("He"), 2372.0), "E(He) ≈ 2372 kJ/mol (NIST)")
check(pct(E("Li"), 520.0), "E(Li) ≈ 520 kJ/mol (NIST)")
check(pct(E("Ne"), 2081.0), "E(Ne) ≈ 2081 kJ/mol (NIST)")
check(pct(E("Na"), 496.0), "E(Na) ≈ 496 kJ/mol (NIST)")
check(pct(E("Ar"), 1521.0), "E(Ar) ≈ 1521 kJ/mol (NIST)")
check(pct(E("K"), 419.0), "E(K) ≈ 419 kJ/mol (NIST)")

# ── 2) He = maximum ABSOLU du catalogue ; K = minimum de la période 4 ──
TOUS = ["H", "He", "Li", "Be", "B", "C", "N", "O", "F", "Ne",
        "Na", "Mg", "Al", "Si", "P", "S", "Cl", "Ar",
        "K", "Ca", "Sc", "Ti", "V", "Cr", "Mn", "Fe", "Co", "Ni",
        "Cu", "Zn", "Ga", "Ge", "As", "Se", "Br", "Kr"]
PERIODE_4 = TOUS[18:]  # K..Kr
check(all(E("He") >= E(s) for s in TOUS), "E(He) = le plus élevé de tous (fait NIST)")
check(all(E("K") <= E(s) for s in PERIODE_4), "E(K) = le plus bas de la période 4 (fait NIST)")

# ── 3) GROUPE 18 : décroissance He > Ne > Ar > Kr ──
check(E("He") > E("Ne"), "E(He) > E(Ne) (groupe 18 décroît)")
check(E("Ne") > E("Ar"), "E(Ne) > E(Ar) (groupe 18 décroît)")
check(E("Ar") > E("Kr"), "E(Ar) > E(Kr) (groupe 18 décroît)")
# Groupe 1 : décroissance H > Li > Na > K
check(E("H") > E("Li") > E("Na") > E("K"), "groupe 1 : E décroît H > Li > Na > K")

# ── 4) ANCRE PIÈGE : période 2 NON strictement monotone (anomalies réelles) ──
check(E("B") < E("Be"), "anomalie B < Be (sous-couche 2p entamée) — fait NIST")
check(E("O") < E("N"), "anomalie O < N (appariement 2p) — fait NIST")
croissante_stricte = all(E(a) < E(b) for a, b in
                         zip(["Li", "Be", "B", "C", "N", "O", "F"],
                             ["Be", "B", "C", "N", "O", "F", "Ne"]))
check(not croissante_stricte, "Li->Ne n'est PAS strictement croissante (piège)")
# ... mais la tendance de FOND est bien là : les extrémités de période
check(E("Li") < E("Ne"), "tendance de fond période 2 : E(Li) < E(Ne)")
check(E("Na") < E("Ar"), "tendance de fond période 3 : E(Na) < E(Ar)")
check(E("K") < E("Kr"), "tendance de fond période 4 : E(K) < E(Kr)")

# ── 5) Le module NE PRÉTEND PAS de monotonie stricte (chaînes de tendance honnêtes) ──
tp_ion = P.tendance_periode("ionisation")
check("CROÎT" in tp_ion or "croît" in tp_ion, "tendance période ionisation = croît")
check("strictement" in tp_ion and "NON" in tp_ion.upper(),
      "la tendance ionisation/période DIT 'non strictement monotone' (piège)")
check("Be" in tp_ion and "N" in tp_ion, "les anomalies Be->B et N->O sont NOMMÉES")
tg_ion = P.tendance_groupe("ionisation")
check("DÉCROÎT" in tg_ion or "décroît" in tg_ion, "tendance groupe ionisation = décroît")
tp_ray = P.tendance_periode("rayon")
check("DÉCROÎT" in tp_ray or "décroît" in tp_ray, "tendance période rayon = décroît")
tg_ray = P.tendance_groupe("rayon")
check("CROÎT" in tg_ray or "croît" in tg_ray, "tendance groupe rayon = croît")

# ── 6) ANCRES RAYON (pm ; classiques de Pauling en dur, ±6 %) ──
check(abs(R("Cl") - 99.0) <= 0.06 * 99.0, "r(Cl) ≈ 99 pm (valeur covalente classique)")
check(abs(R("C") - 77.0) <= 0.06 * 77.0, "r(C) ≈ 77 pm (valeur covalente classique)")
# Ordres classiques (faits, indépendants de la table choisie)
check(R("K") > R("Na") > R("Li"), "groupe 1 : rayon croît Li < Na < K")
check(R("Br") > R("Cl") > R("F"), "groupe 17 : rayon croît F < Cl < Br")
check(R("Li") > R("Be") > R("B") > R("C") > R("N") > R("O"),
      "période 2 : rayon décroît Li > Be > B > C > N > O")
check(R("Na") > R("Mg") > R("Al") > R("Si") > R("P") > R("S") > R("Cl"),
      "période 3 : rayon décroît Na > ... > Cl")
check(all(R("K") >= R(s) for s in TOUS), "r(K) = le plus grand de Z=1..36")
check(R("H") < R("Li"), "r(H) < r(Li) (H = le plus petit des métaux-non, fait classique)")
# La définition publiée est NOMMÉE (covalent, pas van der Waals)
check("covalent" in P.RAYON_DEFINITION, "la définition du rayon est nommée : covalent")
check("covalent" in P.SOURCE and ("NIST" in P.SOURCE or "CRC" in P.SOURCE),
      "SOURCE cite la table de rayons ET la source NIST/CRC des ionisations")

# ── 7) COMPARAISONS ──
check(P.compare_rayon("K", "Li") == "K", "compare_rayon(K,Li) = K")
check(P.compare_rayon("F", "Cl") == "Cl", "compare_rayon(F,Cl) = Cl")
check(P.compare_ionisation("He", "H") == "He", "compare_ionisation(He,H) = He")
check(P.compare_ionisation("N", "O") == "N", "compare_ionisation(N,O) = N (anomalie)")
check(P.compare_ionisation("Be", "B") == "Be", "compare_ionisation(Be,B) = Be (anomalie)")
check(P.compare_ionisation("Na", "Cl") == "Cl", "compare_ionisation(Na,Cl) = Cl (période)")

# ── 8) SOUNDNESS — élément hors catalogue / casse / types ──
check(leve(E, "Xx"), "élément inventé 'Xx' -> ValueError")
check(leve(R, "Xx"), "rayon 'Xx' -> ValueError")
check(leve(E, "Rb"), "Rb (Z=37, hors catalogue) -> ValueError (pas d'extrapolation)")
check(leve(R, "Uuo"), "'Uuo' -> ValueError")
check(leve(E, "he"), "casse fautive 'he' -> ValueError")
check(leve(R, "CL"), "casse fautive 'CL' -> ValueError")
check(leve(E, ""), "chaîne vide -> ValueError")
check(leve(E, 1), "int -> ValueError")
check(leve(R, 26), "Z numérique -> ValueError (le symbole est requis)")
check(leve(E, True), "bool -> ValueError")
check(leve(R, None), "None -> ValueError")
check(leve(E, float("nan")), "NaN -> ValueError")
check(leve(E, ["H"]), "liste -> ValueError")

# ── 9) SOUNDNESS — tendances : propriété inconnue ──
check(leve(P.tendance_periode, "masse"), "tendance_periode('masse') -> ValueError")
check(leve(P.tendance_groupe, "électronégativité"), "prop hors périmètre -> ValueError")
check(leve(P.tendance_periode, True), "tendance_periode(bool) -> ValueError")
check(leve(P.tendance_groupe, 3), "tendance_groupe(int) -> ValueError")
check(leve(P.tendance_periode, None), "tendance_periode(None) -> ValueError")

# ── 10) SOUNDNESS — comparaisons dégénérées / égalités de table ──
check(leve(P.compare_rayon, "H", "H"), "compare_rayon(H,H) -> ValueError")
check(leve(P.compare_ionisation, "Fe", "Fe"), "compare_ionisation(Fe,Fe) -> ValueError")
check(leve(P.compare_rayon, "Ge", "As"),
      "compare_rayon(Ge,As) : rayons catalogués ÉGAUX (121 pm Pyykkö) -> ValueError (abstention)")
check(leve(P.compare_rayon, "Xx", "H"), "compare_rayon(Xx,H) -> ValueError")
check(leve(P.compare_ionisation, "H", "Og"), "compare_ionisation(H,Og) -> ValueError")
check(leve(P.compare_rayon, 1, 2), "compare_rayon(int,int) -> ValueError")

# ── 11) COMPLÉTUDE du catalogue Z=1..36 (les 36 répondent, aucune abstention indue) ──
check(all(isinstance(E(s), float) and E(s) > 0 for s in TOUS), "les 36 énergies répondent (> 0)")
check(all(isinstance(R(s), float) and R(s) > 0 for s in TOUS), "les 36 rayons répondent (> 0)")

# ── 12) DÉTERMINISME ──
check(E("Fe") == E("Fe"), "déterminisme énergie")
check(R("Fe") == R("Fe"), "déterminisme rayon")
check(P.tendance_periode("rayon") == P.tendance_periode("rayon"), "déterminisme tendance")
check(P.compare_ionisation("He", "H") == P.compare_ionisation("He", "H"), "déterminisme comparaison")

print(f"\n=== valide_proprietes_periodiques : {ok}/{ok+ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
