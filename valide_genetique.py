"""
VALIDE genetique.py — held-out ADVERSE. Exactitude (code génétique standard) + soundness : base invalide /
longueur non multiple de 3 / codon inconnu -> HORS (jamais deviné). Aucun cas ici n'est dans __main__.
"""
import genetique as G

ok = 0
ko = 0


def check(cond, label):
    global ok, ko
    if cond:
        ok += 1
    else:
        ko += 1
        print(f"  FAIL: {label}")


# 1) COMPLÉMENT ADN (A↔T, G↔C) — held-out.
check(G.complement_adn("GGCCAATT") == (G.VERIFIE, "CCGGTTAA"), "complément GGCCAATT")
check(G.complement_adn("A") == (G.VERIFIE, "T"), "complément A->T")
check(G.complement_adn("atgc") == (G.VERIFIE, "TACG"), "complément casse minuscule")
check(G.complement_inverse("ATGC") == (G.VERIFIE, "GCAT"), "complément inverse ATGC")

# 2) TRANSCRIPTION ADN codant -> ARNm (T->U).
check(G.transcrit("ATGGCC") == (G.VERIFIE, "AUGGCC"), "transcription ATGGCC")
check(G.transcrit("TTTT") == (G.VERIFIE, "UUUU"), "transcription TTTT")

# 3) CODON -> ACIDE AMINÉ (table standard ; ADN ou ARN). Held-out couvrant des cas variés.
ATTENDU_CODON = {"AUG": "M", "ATG": "M", "UGG": "W", "UAA": "*", "UAG": "*", "UGA": "*",
                 "GGU": "G", "CCC": "P", "AAA": "K", "GAA": "E", "UAU": "Y", "CGU": "R",
                 "AGA": "R", "AGU": "S", "CAU": "H", "GUC": "V"}
for codon, aa in ATTENDU_CODON.items():
    check(G.codon_vers_aa(codon) == (G.VERIFIE, aa), f"codon {codon} -> {aa}")

# 4) TRADUCTION (ARN ou ADN) -> protéine, arrêt au STOP.
check(G.traduit("AUGUUUUAA") == (G.VERIFIE, "MF"), "traduit AUGUUUUAA -> MF (stop)")
check(G.traduit("ATGGGATAA") == (G.VERIFIE, "MG"), "traduit ADN ATGGGATAA -> MG")
check(G.traduit("AUGAAAUUUGGGUAA") == (G.VERIFIE, "MKFG"), "traduit plus long -> MKFG")
check(G.traduit("AUGUAAUUU") == (G.VERIFIE, "M"), "stop au milieu coupe -> M")
check(G.traduit("AUGUAAUUU", arret_au_stop=False)[1] == "M*F", "sans arrêt -> M*F")

# 5) SOUNDNESS — base invalide -> HORS (jamais deviné).
for bad in ["ATBX", "AUGN", "XYZ", "AT GC!", "123", "U" * 0]:
    check(G.complement_adn(bad)[0] == G.HORS, f"complément base invalide {bad!r} -> HORS")
check(G.transcrit("ATGX")[0] == G.HORS, "transcription base invalide -> HORS")
check(G.codon_vers_aa("ATB")[0] == G.HORS, "codon base invalide -> HORS")
check(G.codon_vers_aa("AT")[0] == G.HORS, "codon longueur != 3 -> HORS")

# 6) SOUNDNESS — longueur non multiple de 3 pour traduction -> HORS (pas de codon tronqué).
for s in ["AUGU", "AUGUU", "A", "ATGGC"]:
    check(G.traduit(s)[0] == G.HORS, f"traduction longueur {len(s)} -> HORS")

# 7) Entrées non-str -> HORS.
for bad in [None, 123, ["ATGC"]]:
    check(G.complement_adn(bad)[0] == G.HORS, f"non-str complément {bad!r} -> HORS")
    check(G.traduit(bad)[0] == G.HORS, f"non-str traduit {bad!r} -> HORS")

# 8) NL SOUND : extraction VALIDÉE (séquence invalide -> HORS, pas de fragment deviné).
quoi, st, v = G.repond_nl("Quel est le complément ADN de ATGC ?")
check(quoi == "complement" and st == G.VERIFIE and v == "TACG", f"NL complément ATGC (obtenu {v})")
quoi, st, v = G.repond_nl("complément de GGCC")
check(st == G.VERIFIE and v == "CCGG", "NL complément sans 'ADN'")
quoi, st, v = G.repond_nl("traduis l'ARN AUGUUUUAA")
check(quoi == "traduction" and st == G.VERIFIE and v == "MF", f"NL traduction (obtenu {v})")
check(G.repond_nl("quelle heure est-il ?")[1] == G.HORS, "NL hors gabarit -> HORS")
check(G.repond_nl(None)[1] == G.HORS, "NL non-str -> HORS")

# 9) Intégrité de la table : 64 codons, exactement 3 STOP, 20 acides aminés distincts.
check(len(G.CODE) == 64, "table = 64 codons")
check(sum(1 for v in G.CODE.values() if v == "*") == 3, "3 codons STOP")
check(len({v for v in G.CODE.values() if v != "*"}) == 20, "20 acides aminés")

# 10) DÉTERMINISME.
check(G.traduit("AUGAAAUUUGGGUAA") == G.traduit("AUGAAAUUUGGGUAA"), "déterminisme")

print(f"\n=== valide_genetique : {ok}/{ok+ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
