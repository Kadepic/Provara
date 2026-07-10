"""
VALIDE compression_sans_perte.py — held-out ADVERSE.

ANCRES EXTERNES NON CIRCULAIRES (valeurs connues, PAS recalculées par la fonction testée) :
  • KRAFT [1,2,3,3] : 1/2 + 1/4 + 1/8 + 1/8 = 1 EXACTEMENT (calcul à la main, refait ici en Fraction
    par simple addition — second chemin indépendant de kraft_somme) -> satisfaite.
    [1,1,2] : 1/2 + 1/2 + 1/4 = 5/4 > 1 -> NON satisfaite (aucun code préfixe n'existe : théorème de Kraft).
  • HUFFMAN classique {a:0.4, b:0.35, c:0.2, d:0.05} : fusion à la main d+c=0.25, puis 0.25+b=0.6, puis
    0.6+a=1 -> longueurs {a:1, b:2, c:3, d:3} ; L = 0.4·1 + 0.35·2 + 0.2·3 + 0.05·3
    = 0.4 + 0.7 + 0.6 + 0.15 = 1.85 bits (arithmétique à la main, écrite EN DUR).
  • ENTROPIE H(0.4,0.35,0.2,0.05) = 1.739353... bits : calculée par information_calcul.entropie (module
    RÉSERVÉ, chemin de code indépendant) ET confrontée à la valeur 1.7394 posée EN DUR (table de log₂
    à la main : 0.528771 + 0.530100 + 0.464386 + 0.216096 ≈ 1.739353). Encadrement 1.7394 ≤ 1.85 < 2.7394.
  • SOURCE UNIFORME sur 4 symboles : Huffman = 2 bits/symbole = H exactement (dé à 4 faces = 2 bits,
    ancre classique d'information_calcul) — cas d'ÉGALITÉ de l'encadrement.
  • TIROIRS n=3 : 8 messages de 3 bits, mais 1+2+4 = 7 chaînes strictement plus courtes (longueurs 0,1,2,
    comptées à la main) -> au moins un message NE RACCOURCIT PAS (longueur de sortie ≥ n). La clé
    « grossit strictement » serait FAUSSE : contre-modèle IDENTITÉ énuméré ICI exhaustivement sur les
    8 messages de 3 bits (sans perte, aucune sortie plus longue que l'entrée) — la gate vérifie que le
    module ne rend PLUS l'ancienne clé sur-affirmante `au_moins_un_message_grossit`.
  • DÉCODAGE : code manuel {a:'0', b:'10', c:'110', d:'111'} ; '0'+'110'+'111' = '0110111' -> [a,c,d]
    (concaténation faite à la main). Boucle fermée : 200 messages pseudo-aléatoires DÉTERMINISTES (LCG à
    graine fixe) encodés puis décodés redonnent l'original.

SOUNDNESS : bool, str, NaN, inf, longueurs non entières/<1, fréquence ≤ 0, un seul symbole, dict vide,
mauvaise structure, flux ambigu/inachevé/non binaire, symboles non ordonnables -> ValueError.
DÉTERMINISME : chaque fonction appelée deux fois rend l'identique (y compris Huffman avec ex æquo).
"""
from fractions import Fraction

import information_calcul
import compression_sans_perte as C

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


def proche(x, attendu, tol=1e-9):
    return x is not None and abs(x - attendu) <= tol


# ── 1) KRAFT : ancres calculées À LA MAIN (Fraction = second chemin, simple addition) ──
main_1233 = Fraction(1, 2) + Fraction(1, 4) + Fraction(1, 8) + Fraction(1, 8)   # = 1 à la main
check(main_1233 == Fraction(1), "vérif à la main : 1/2+1/4+1/8+1/8 = 1")
check(C.kraft_somme([1, 2, 3, 3]) == Fraction(1), "kraft_somme([1,2,3,3]) = 1 exactement")
check(C.kraft_somme([1, 2, 3, 3]) == main_1233, "kraft_somme = addition manuelle (2e chemin)")
check(C.kraft_satisfaite([1, 2, 3, 3]) is True, "Kraft satisfaite pour [1,2,3,3] (code préfixe existe)")

main_112 = Fraction(1, 2) + Fraction(1, 2) + Fraction(1, 4)                     # = 5/4 à la main
check(C.kraft_somme([1, 1, 2]) == Fraction(5, 4), "kraft_somme([1,1,2]) = 5/4 > 1")
check(C.kraft_somme([1, 1, 2]) == main_112, "kraft_somme([1,1,2]) = addition manuelle")
check(C.kraft_satisfaite([1, 1, 2]) is False, "Kraft NON satisfaite pour [1,1,2] : aucun code préfixe")

check(C.kraft_somme([2, 2, 2, 2]) == Fraction(1), "4 mots de 2 bits : 4·(1/4) = 1")
check(C.kraft_somme([3]) == Fraction(1, 8), "un mot de 3 bits : 1/8")
check(C.kraft_satisfaite([1, 2, 3]) is True, "7/8 < 1 : satisfaite (inégalité stricte, code incomplet)")

# ── 2) EST_PREFIXE : exemples jugés à la main ──
check(C.est_prefixe({"a": "0", "b": "10", "c": "11"}) is True, "{0,10,11} est préfixe")
check(C.est_prefixe(["0", "01"]) is False, "'0' est préfixe de '01' -> False")
check(C.est_prefixe(["0", "10", "110", "111"]) is True, "{0,10,110,111} (longueurs 1,2,3,3) est préfixe")
check(C.est_prefixe(["01", "01"]) is False, "deux mots identiques -> pas préfixe")
check(C.est_prefixe(["0", "1"]) is True, "{0,1} est préfixe")
check(C.est_prefixe(["10", "1"]) is False, "'1' préfixe de '10' (ordre inversé aussi détecté)")

# ── 3) HUFFMAN classique : fusion faite À LA MAIN -> longueurs {a:1,b:2,c:3,d:3} ──
FREQS = {"a": 0.4, "b": 0.35, "c": 0.2, "d": 0.05}
codes = C.huffman(FREQS)
check(len(codes["a"]) == 1, "Huffman : |code(a)| = 1 (fusion manuelle d+c=0.25, +b=0.6, +a=1)")
check(len(codes["b"]) == 2, "Huffman : |code(b)| = 2")
check(len(codes["c"]) == 3, "Huffman : |code(c)| = 3")
check(len(codes["d"]) == 3, "Huffman : |code(d)| = 3")
check(C.est_prefixe(codes) is True, "le code de Huffman est préfixe")
check(C.kraft_satisfaite([len(m) for m in codes.values()]) is True, "les longueurs Huffman satisfont Kraft")

L = C.longueur_moyenne(codes, FREQS)
check(proche(L, 1.85), "L = 0.4+0.7+0.6+0.15 = 1.85 bits (arithmétique à la main)")

# ── 4) ENTROPIE (chemin indépendant) + ENCADREMENT DE SHANNON ──
H_ic = information_calcul.entropie([0.4, 0.35, 0.2, 0.05])      # module réservé, chemin indépendant
check(proche(H_ic, 1.7394, tol=5e-4), "H(0.4,0.35,0.2,0.05) = 1.7394 (table log2 à la main, EN DUR)")
check(1.7394 <= 1.85 < 1.7394 + 1.0, "encadrement posé en dur : 1.7394 <= 1.85 < 2.7394")

H, L2 = C.encadre_huffman(FREQS)
check(proche(H, H_ic), "encadre_huffman rend H = information_calcul.entropie (même borne)")
check(proche(L2, 1.85), "encadre_huffman rend L = 1.85")
check(H <= L2 < H + 1.0, "H <= L < H+1 vérifié sur le cas classique")

# ── 5) CAS D'ÉGALITÉ : uniforme sur 4 symboles -> L = H = 2 bits exactement ──
UNIF = {"w": 0.25, "x": 0.25, "y": 0.25, "z": 0.25}
codes_u = C.huffman(UNIF)
check(all(len(m) == 2 for m in codes_u.values()), "uniforme/4 : tous les mots font 2 bits")
Lu = C.longueur_moyenne(codes_u, UNIF)
check(Lu == 2.0, "uniforme/4 : L = 2.0 bits exactement")
check(information_calcul.entropie([0.25] * 4) == 2.0, "dé à 4 faces : H = 2 bits (ancre classique)")
Hu, Lu2 = C.encadre_huffman(UNIF)
check(Hu == 2.0 and Lu2 == 2.0, "cas d'égalité L = H = 2.0 : encadrement tenu (pas de RuntimeError)")

# Uniforme sur 2 symboles : pièce équilibrée, H = 1 bit, Huffman = {0,1} -> L = 1
Hp, Lp = C.encadre_huffman({"pile": 1, "face": 1})
check(Hp == 1.0 and Lp == 1.0, "pièce équilibrée : H = L = 1 bit (fréquences entières acceptées)")

# ── 6) TIROIRS : comptage à la main pour n=3 ──
d3 = C.compression_universelle_impossible(3)
check(d3["messages_de_n_bits"] == 8, "n=3 : 2^3 = 8 messages")
check(d3["messages_strictement_plus_courts"] == 7, "n=3 : 7 chaînes plus courtes")
check(d3["messages_strictement_plus_courts"] == 1 + 2 + 4,
      "comptage à la main : longueurs 0,1,2 -> 1+2+4 = 7 chaînes")
check(d3["deficit"] == 1, "n=3 : déficit = 1 (le tiroir manquant)")
check(d3["au_moins_un_message_ne_raccourcit_pas"] is True,
      "n=3 : au moins un message ne raccourcit pas (exactement ce que prouve le comptage)")
check("au_moins_un_message_grossit" not in d3,
      "l'ancienne clé sur-affirmante 'au_moins_un_message_grossit' a DISPARU (faux positif tué)")

# CONTRE-MODÈLE (énuméré ICI, chemin totalement indépendant du module) : le compresseur IDENTITÉ sur
# les 8 messages de 3 bits est SANS PERTE (injectif : 8 sorties distinctes) et ne fait GROSSIR aucun
# message (chaque sortie a exactement la longueur de l'entrée). Donc « au moins un message grossit »
# était un énoncé FAUX ; seul « au moins un ne raccourcit pas » est prouvé par les tiroirs.
_messages_3bits = [format(i, "03b") for i in range(8)]          # '000'..'111', énumération à la main
_identite = {m: m for m in _messages_3bits}
check(len(set(_identite.values())) == 8, "contre-modèle : l'identité est injective (sans perte, 8 sorties)")
check(all(len(_identite[m]) == len(m) for m in _messages_3bits),
      "contre-modèle : l'identité ne fait grossir AUCUN message (longueurs égales)")
check(all(len(_identite[m]) >= 3 for m in _messages_3bits),
      "contre-modèle compatible avec le théorème : aucune sortie plus courte que n=3")
d1 = C.compression_universelle_impossible(1)
check(d1["messages_de_n_bits"] == 2 and d1["messages_strictement_plus_courts"] == 1,
      "n=1 : 2 messages, 1 seule chaîne plus courte (la vide)")
d10 = C.compression_universelle_impossible(10)
check(d10["messages_de_n_bits"] - d10["messages_strictement_plus_courts"] == 1,
      "n=10 : le déficit reste 1 (1024 vs 1023)")

# ── 7) DÉCODAGE : code manuel, flux concaténé À LA MAIN ──
CODE_MANUEL = {"a": "0", "b": "10", "c": "110", "d": "111"}
check(C.decode(CODE_MANUEL, "0110111") == ["a", "c", "d"],
      "decode('0'+'110'+'111') = [a,c,d] (concaténation manuelle)")
check(C.decode(CODE_MANUEL, "") == [], "flux vide -> message vide")
check(C.encode(CODE_MANUEL, ["a", "c", "d"]) == "0110111", "encode([a,c,d]) = '0110111' (à la main)")
check(C.encode(CODE_MANUEL, "abba") == "010100",
      "encode('abba') = '0'+'10'+'10'+'0' = '010100' (concaténation manuelle)")

# Boucle fermée : 200 messages pseudo-aléatoires DÉTERMINISTES (LCG graine fixe, aucun module random)
graine = 123456789
syms = sorted(CODE_MANUEL.keys())
reussites = 0
for _ in range(200):
    message = []
    for _ in range(1 + graine % 17):
        graine = (1103515245 * graine + 12345) % (2 ** 31)
        message.append(syms[graine % 4])
    if C.decode(CODE_MANUEL, C.encode(CODE_MANUEL, message)) == message:
        reussites += 1
    graine = (1103515245 * graine + 12345) % (2 ** 31)
check(reussites == 200, "boucle fermée : 200/200 messages encodés puis décodés = originaux")

# Boucle fermée aussi avec le code HUFFMAN construit (pas seulement le code manuel)
msg_h = ["a", "b", "a", "c", "d", "a", "b", "b", "c", "a"]
check(C.decode(codes, C.encode(codes, msg_h)) == msg_h, "boucle fermée sur le code Huffman construit")

# ── 8) DÉCODAGE : abstentions ──
check(leve(C.decode, {"a": "0", "b": "01"}, "001"), "code non préfixe -> ValueError (ambigu)")
check(leve(C.decode, CODE_MANUEL, "11"), "flux inachevé ('11' n'est pas un mot complet) -> ValueError")
check(leve(C.decode, CODE_MANUEL, "01121"), "caractère '2' dans le flux -> ValueError")
check(leve(C.decode, CODE_MANUEL, 5), "flux non-chaîne -> ValueError")
check(leve(C.encode, CODE_MANUEL, ["a", "z"]), "symbole inconnu à l'encodage -> ValueError")

# ── 9) SOUNDNESS Kraft ──
check(leve(C.kraft_somme, []), "liste vide -> ValueError")
check(leve(C.kraft_somme, [1.5, 2]), "longueur non entière -> ValueError")
check(leve(C.kraft_somme, [True, 2]), "bool comme longueur -> ValueError")
check(leve(C.kraft_somme, [0, 2]), "longueur 0 -> ValueError")
check(leve(C.kraft_somme, [-1]), "longueur négative -> ValueError")
check(leve(C.kraft_somme, "12"), "chaîne au lieu d'une liste -> ValueError")
check(leve(C.kraft_somme, [float("nan")]), "NaN -> ValueError")
check(leve(C.kraft_somme, [float("inf")]), "inf -> ValueError")

# ── 10) SOUNDNESS est_prefixe ──
check(leve(C.est_prefixe, []), "liste vide -> ValueError")
check(leve(C.est_prefixe, ["0", "2"]), "caractère hors {0,1} -> ValueError")
check(leve(C.est_prefixe, ["0", ""]), "mot vide -> ValueError")
check(leve(C.est_prefixe, 42), "entier au lieu de codes -> ValueError")
check(leve(C.est_prefixe, ["0", 10]), "mot non-chaîne -> ValueError")

# ── 11) SOUNDNESS Huffman / longueur_moyenne / encadre ──
check(leve(C.huffman, {}), "dict vide -> ValueError")
check(leve(C.huffman, {"a": 1}), "UN SEUL symbole -> ValueError explicite (mot de longueur 0)")
check(leve(C.huffman, {"a": 0.5, "b": 0}), "fréquence nulle -> ValueError")
check(leve(C.huffman, {"a": 0.5, "b": -1}), "fréquence négative -> ValueError")
check(leve(C.huffman, {"a": 0.5, "b": True}), "fréquence bool -> ValueError")
check(leve(C.huffman, {"a": float("nan"), "b": 1}), "fréquence NaN -> ValueError")
check(leve(C.huffman, {"a": float("inf"), "b": 1}), "fréquence inf -> ValueError")
check(leve(C.huffman, {"a": "x", "b": 1}), "fréquence chaîne -> ValueError")
check(leve(C.huffman, [1, 2]), "liste au lieu d'un dict -> ValueError")
check(leve(C.huffman, {"a": 1, 7: 1}), "symboles non ordonnables entre eux -> ValueError (ordre stable)")
check(leve(C.longueur_moyenne, CODE_MANUEL, {"a": 1, "b": 1}), "clés codes/fréquences différentes -> ValueError")
check(leve(C.longueur_moyenne, CODE_MANUEL, {"a": 1, "b": 1, "c": 1, "d": 0}), "fréquence nulle -> ValueError")
check(leve(C.longueur_moyenne, {"a": ""}, {"a": 1}), "mot de code vide -> ValueError")
check(leve(C.encadre_huffman, {"a": 1}), "encadre_huffman sur un seul symbole -> ValueError")
check(leve(C.encadre_huffman, {}), "encadre_huffman sur dict vide -> ValueError")

# ── 12) SOUNDNESS tiroirs ──
check(leve(C.compression_universelle_impossible, 0), "n=0 -> ValueError")
check(leve(C.compression_universelle_impossible, -3), "n négatif -> ValueError")
check(leve(C.compression_universelle_impossible, True), "n bool -> ValueError")
check(leve(C.compression_universelle_impossible, 2.0), "n flottant -> ValueError")
check(leve(C.compression_universelle_impossible, 10001), "n > garde-fou -> ValueError")

# ── 13) DÉTERMINISME (y compris ex æquo Huffman) ──
check(C.huffman(FREQS) == C.huffman(FREQS), "déterminisme Huffman (cas classique)")
check(C.huffman(UNIF) == C.huffman(UNIF), "déterminisme Huffman (4 ex æquo)")
check(C.huffman({"a": 1, "b": 1, "c": 1}) == C.huffman({"a": 1, "b": 1, "c": 1}),
      "déterminisme Huffman (3 ex æquo, arbre asymétrique)")
check(C.kraft_somme([1, 2, 3, 3]) == C.kraft_somme([1, 2, 3, 3]), "déterminisme kraft_somme")
check(C.decode(CODE_MANUEL, "0110111") == C.decode(CODE_MANUEL, "0110111"), "déterminisme decode")
check(C.encadre_huffman(FREQS) == C.encadre_huffman(FREQS), "déterminisme encadre_huffman")

# Cohérence interne du code Huffman 3 ex æquo : longueurs {1,2,2} (fusion manuelle : deux 1 -> 2, puis 2+1)
codes3 = C.huffman({"a": 1, "b": 1, "c": 1})
check(sorted(len(m) for m in codes3.values()) == [1, 2, 2],
      "3 symboles équiprobables : longueurs {1,2,2} (fusion à la main)")
check(C.est_prefixe(codes3) is True, "code 3 ex æquo : préfixe")

print(f"\n=== valide_compression_sans_perte : {ok}/{ok+ko} ===")
import sys; sys.exit(0 if ko == 0 else 1)
