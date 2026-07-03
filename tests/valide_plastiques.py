"""
VALIDE plastiques.py — held-out ADVERSE. Conventions de code de recyclage (ASTM D7611), classe thermique
(thermoplastique vs thermodurcissable), Tg sourcées + SOUNDNESS (plastique/code inconnu -> ValueError) +
déterminisme. Aucun de ces cas n'est dans le module ; les ancres sont des faits/conventions externes.
"""
import plastiques as P

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


# 1) CODE DE RECYCLAGE — convention exacte (held-out : valeurs de référence ASTM D7611).
REF_CODE = {"PET": 1, "PEHD": 2, "PVC": 3, "PEBD": 4, "PP": 5, "PS": 6}
for nom, c in REF_CODE.items():
    check(P.code_recyclage(nom) == c, f"code({nom}) == {c}")

# Cas requis par la spéc.
check(P.code_recyclage("PET") == 1, "CAS: PET = code 1")
check(P.code_recyclage("PP") == 5, "CAS: PP = code 5")

# Alias et casse/accents tolérés.
check(P.code_recyclage("HDPE") == 2, "alias HDPE -> 2")
check(P.code_recyclage("LDPE") == 4, "alias LDPE -> 4")
check(P.code_recyclage("pet") == 1, "casse: pet -> 1")
check(P.code_recyclage("polypropylène") == 5, "nom complet polypropylène -> 5")
check(P.code_recyclage("polystyrène") == 6, "nom complet polystyrène -> 6")
check(P.code_recyclage("V") == 3, "marquage V -> PVC -> 3")
# Plastiques techniques -> catégorie 7.
for autre in ["PC", "ABS", "PMMA", "PA", "PLA", "PTFE", "polycarbonate", "nylon", "teflon", "autres"]:
    check(P.code_recyclage(autre) == 7, f"{autre} -> code 7 (autres)")

# 2) nom_depuis_code — inverse exact.
REF_NOM = {1: "PET", 2: "PEHD", 3: "PVC", 4: "PEBD", 5: "PP", 6: "PS", 7: "autres"}
for c, nom in REF_NOM.items():
    check(P.nom_depuis_code(c) == nom, f"nom_depuis_code({c}) == {nom}")
# Bijection 1..6 : code -> nom -> code.
for nom in REF_CODE:
    check(P.code_recyclage(P.nom_depuis_code(P.code_recyclage(nom))) == P.code_recyclage(nom),
          f"aller-retour code/nom cohérent pour {nom}")

# 3) CLASSE THERMIQUE — thermoplastiques (refondables) vs thermodurcissables (réticulés).
for tp in ["PET", "PP", "PE", "PS", "PVC", "PEHD", "PEBD", "PC", "ABS", "PMMA", "PA", "PLA", "PTFE"]:
    check(P.est_thermoplastique(tp) is True, f"{tp} thermoplastique")
    check(P.est_thermodurcissable(tp) is False, f"{tp} non thermodurcissable")
    check(P.classe_thermique(tp) == "thermoplastique", f"classe({tp}) thermoplastique")
for td in ["bakélite", "époxy", "mélamine", "phénoplaste", "polyester insaturé"]:
    check(P.est_thermodurcissable(td) is True, f"{td} thermodurcissable")
    check(P.est_thermoplastique(td) is False, f"{td} non thermoplastique")
    check(P.classe_thermique(td) == "thermodurcissable", f"classe({td}) thermodurcissable")

# Cas requis par la spéc.
check(P.est_thermoplastique("PP") is True, "CAS: PP thermoplastique")
check(P.est_thermodurcissable("bakélite") is True, "CAS: bakélite thermodurcissable")

# 4) Tg — données sourcées (held-out ; tolérance = variabilité littérature).
REF_TG = {"PS": 100.0, "PET": 70.0, "PVC": 80.0, "PMMA": 105.0, "PC": 147.0, "PLA": 60.0}
for nom, tg in REF_TG.items():
    v = P.temperature_transition_vitreuse(nom)
    check(abs(v - tg) < 10.0, f"Tg({nom}) ~ {tg} (obtenu {v})")
# Cas requis : PS Tg ~ 100 °C.
check(abs(P.temperature_transition_vitreuse("PS") - 100.0) < 1e-9, "CAS: PS Tg ~ 100 °C")

# 5) nom_complet — nomenclature.
check(P.nom_complet("PET") == "polyéthylène téréphtalate", "nom_complet PET")
check(P.nom_complet("PP") == "polypropylène", "nom_complet PP")
check(P.nom_complet("bakélite").lower().startswith("résine") or "phénol" in P.nom_complet("bakélite").lower(),
      "nom_complet bakélite = résine phénol-formaldéhyde")

# 6) SOUNDNESS — entrée HORS référentiel -> ValueError (jamais une réponse inventée).
for bad in ["kryptonite", "PVCX", "", "polyester", "PE3", "adamantium", "metal"]:
    check(leve(P.code_recyclage, bad), f"code_recyclage({bad!r}) -> ValueError")
    check(leve(P.est_thermoplastique, bad), f"est_thermoplastique({bad!r}) -> ValueError")
    check(leve(P.temperature_transition_vitreuse, bad), f"Tg({bad!r}) -> ValueError")
    check(leve(P.nom_complet, bad), f"nom_complet({bad!r}) -> ValueError")
# "polyester" seul est ambigu (PET est un polyester thermoplastique) -> refusé.
check(leve(P.code_recyclage, "polyester"), "polyester seul (ambigu) -> ValueError")

# PE générique : thermoplastique connu MAIS pas de code unique (PEHD=2 ou PEBD=4) -> ValueError sur le code.
check(P.est_thermoplastique("PE") is True, "PE générique reconnu thermoplastique")
check(leve(P.code_recyclage, "PE"), "PE générique sans code unique -> ValueError")

# Thermodurcissables : pas de code de recyclage standard -> ValueError.
check(leve(P.code_recyclage, "bakélite"), "bakélite sans code de recyclage -> ValueError")
check(leve(P.code_recyclage, "époxy"), "époxy sans code de recyclage -> ValueError")

# "autres" : code 7 défini, mais PAS de classe thermique propre ni de Tg.
check(P.code_recyclage("autres") == 7, "autres -> code 7")
check(leve(P.classe_thermique, "autres"), "autres sans classe thermique -> ValueError")
check(leve(P.est_thermoplastique, "autres"), "est_thermoplastique(autres) -> ValueError")

# Tg non répertoriée pour un polymère pourtant connu -> ValueError (jamais inventée).
check(leve(P.temperature_transition_vitreuse, "PP"), "Tg(PP) non répertoriée -> ValueError")
check(leve(P.temperature_transition_vitreuse, "PEHD"), "Tg(PEHD) non répertoriée -> ValueError")

# nom_depuis_code — soundness : hors plage / mauvais type -> ValueError.
for bad in [0, 8, -1, 100, 1.0, "1", None, True, [1]]:
    check(leve(P.nom_depuis_code, bad), f"nom_depuis_code({bad!r}) -> ValueError")

# code_recyclage / Tg sur non-str -> ValueError.
for bad in [None, 1, 3.14, ["PET"], {"x": 1}]:
    check(leve(P.code_recyclage, bad), f"code_recyclage({bad!r}) non-str -> ValueError")
    check(leve(P.est_thermoplastique, bad), f"est_thermoplastique({bad!r}) non-str -> ValueError")

# 7) DÉTERMINISME.
check(P.code_recyclage("PET") == P.code_recyclage("PET"), "déterminisme code")
check(P.est_thermoplastique("PP") == P.est_thermoplastique("PP"), "déterminisme classe")
check(P.temperature_transition_vitreuse("PS") == P.temperature_transition_vitreuse("PS"), "déterminisme Tg")

print(f"\n=== valide_plastiques : {ok}/{ok+ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
