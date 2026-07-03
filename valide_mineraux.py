"""
VALIDE mineraux.py — held-out ADVERSE. Échelle de Mohs (faits établis) :
exactitude des degrés + relation de rayure + soundness (hors catalogue -> ValueError) + déterminisme.
"""
import mineraux as M

ok = 0
ko = 0


def check(cond, label):
    global ok, ko
    if cond:
        ok += 1
    else:
        ko += 1
        print(f"  FAIL: {label}")


def leve_v(fn, *a):
    try:
        fn(*a)
        return False
    except ValueError:
        return True
    except Exception:
        return False


# 1) EXACTITUDE — les dix degrés de référence de l'échelle de Mohs.
REF = {
    "talc": 1, "gypse": 2, "calcite": 3, "fluorine": 4, "apatite": 5,
    "orthose": 6, "quartz": 7, "topaze": 8, "corindon": 9, "diamant": 10,
}
for nom, deg in REF.items():
    check(M.durete_mohs(nom) == deg, f"durete {nom} = {deg}")

# 2) NORMALISATION (casse / espaces) — même fait.
check(M.durete_mohs("DIAMANT") == 10, "casse insensible")
check(M.durete_mohs("  Quartz ") == 7, "espaces ignorés")

# 3) CAS DEMANDÉS — rayure.
check(M.raye("diamant", "quartz") is True, "diamant raye quartz")
check(M.durete_mohs("quartz") > M.durete_mohs("calcite"), "quartz(7) > calcite(3)")
check(M.raye("quartz", "calcite") is True, "quartz raye calcite")
check(M.raye("calcite", "quartz") is False, "calcite ne raye pas quartz")

# 4) TALC = le plus tendre (rien ne lui est inférieur, tout le raye).
plus_tendre = min(REF, key=REF.get)
check(plus_tendre == "talc", "talc est le plus tendre")
for nom in REF:
    if nom != "talc":
        check(M.raye(nom, "talc") is True, f"{nom} raye talc")
        check(M.raye("talc", nom) is False, f"talc ne raye pas {nom}")

# 5) DIAMANT = le plus dur (raye tout, rien ne le raye).
plus_dur_ref = max(REF, key=REF.get)
check(plus_dur_ref == "diamant", "diamant est le plus dur")
for nom in REF:
    if nom != "diamant":
        check(M.raye("diamant", nom) is True, f"diamant raye {nom}")
        check(M.raye(nom, "diamant") is False, f"{nom} ne raye pas diamant")

# 6) plus_dur(m1, m2).
check(M.plus_dur("quartz", "calcite") == "quartz", "plus_dur quartz/calcite")
check(M.plus_dur("calcite", "quartz") == "quartz", "plus_dur calcite/quartz (commutatif)")
check(M.plus_dur("diamant", "talc") == "diamant", "plus_dur diamant/talc")
check(M.plus_dur("apatite", "orthose") == "orthose", "plus_dur apatite/orthose")

# 7) Égalité -> pas de rayure, plus_dur abstient.
check(M.raye("quartz", "quartz") is False, "même minéral ne se raye pas")
check(leve_v(M.plus_dur, "quartz", "quartz"), "plus_dur égalité -> ValueError")

# 8) SOUNDNESS — hors catalogue -> ValueError (jamais une dureté inventée).
for faux in ["or", "fer", "émeraude", "graphite", "saphir", "rubis", "obsidienne", "verre", "", "feldspath"]:
    check(leve_v(M.durete_mohs, faux), f"durete hors catalogue {faux!r} -> ValueError")
check(leve_v(M.raye, "diamant", "or"), "raye avec inconnu -> ValueError")
check(leve_v(M.plus_dur, "topaze", "platine"), "plus_dur avec inconnu -> ValueError")
check(leve_v(M.durete_mohs, None), "None -> ValueError")
check(leve_v(M.durete_mohs, 7), "entier -> ValueError")

# 9) DÉTERMINISME.
check(M.durete_mohs("topaze") == M.durete_mohs("topaze"), "déterminisme durete")
check(M.plus_dur("topaze", "apatite") == M.plus_dur("topaze", "apatite"), "déterminisme plus_dur")

# 10) Ordre monotone complet : pour tout couple, raye <=> degré strictement supérieur.
noms = list(REF)
for a in noms:
    for b in noms:
        attendu = REF[a] > REF[b]
        check(M.raye(a, b) is attendu, f"raye {a}/{b} == ({REF[a]}>{REF[b]})")

# 11) catalogue() expose les 10 étalons sans muter l'état interne.
cat = M.catalogue()
check(cat == REF, "catalogue complet et exact")
cat["talc"] = 99
check(M.durete_mohs("talc") == 1, "catalogue() est une copie (pas de fuite d'état)")

print(f"\n=== valide_mineraux : {ok}/{ok+ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
