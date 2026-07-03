"""VALIDE paradoxes.py — held-out ADVERSE, FAUX=0.

Ancres = faits logiques ÉTABLIS (paradoxe de Russell / barbier / menteur /
Grelling contradictoires par argument diagonal ; détection d'auto-référence
sur cas non ambigus ; catalogue de paradoxes connus) + SOUNDNESS (entrée
invalide/inconnue -> ValueError, jamais de faux positif) + DÉTERMINISME.
"""
import paradoxes as M

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


# ── ARGUMENT DIAGONAL — contradictions ÉTABLIES (toutes prouvées True) ──
check(M.ensemble_russell_paradoxal() is True, "Russell {x:x∉x} paradoxal")
check(M.barbier_paradoxal() is True, "barbier de Russell paradoxal")
check(M.menteur_paradoxal() is True, "menteur paradoxal")
check(M.grelling_paradoxal() is True, "Grelling paradoxal")

# ── DÉTECTION D'AUTO-RÉFÉRENCE — cas non ambigus ──
check(M.est_autoreferentiel("Cette phrase est fausse", "L") is True,
      "menteur : 'cette phrase' -> auto-référentiel")
check(M.est_autoreferentiel("This sentence is false", "S") is True,
      "marqueur anglais 'this sentence'")
check(M.est_autoreferentiel("G n'est pas démontrable", "G") is True,
      "auto-référence par nom (jeton 'G')")
check(M.est_autoreferentiel("Il pleut aujourd'hui à Paris", "P") is False,
      "phrase ordinaire -> non auto-référentielle")
check(M.est_autoreferentiel("Paris est une ville", "P") is False,
      "nom 'P' NON jeton autonome ('Paris') -> False")
check(M.est_autoreferentiel("Socrate est mortel") is False,
      "sans nom et sans marqueur -> False")

# ── GRELLING — règle hétérologique exacte (hét. ssi ne se décrit pas) ──
check(M.est_heterologique("long", False) is True,
      "'long' ne se décrit pas -> hétérologique")
check(M.est_heterologique("français", True) is False,
      "'français' se décrit (mot français) -> autologique")

# ── CATALOGUE — faits établis ──
check(M.catalogue("menteur")["auto_referentiel"] is True, "menteur auto-réf.")
check(M.catalogue("menteur")["famille"] == "sémantique", "menteur sémantique")
check("fausse" in M.catalogue("menteur")["enonce"], "énoncé menteur")
check(M.catalogue("russell")["famille"] == "théorie des ensembles",
      "Russell = théorie des ensembles")
check(M.catalogue("barbier")["famille"] == "théorie des ensembles",
      "barbier = théorie des ensembles")
check(M.catalogue("berry")["famille"] == "définissabilité",
      "Berry = définissabilité")
check(M.catalogue("grelling")["famille"] == "sémantique", "Grelling sémantique")
check(M.catalogue("RUSSELL")["nom"] == "Paradoxe de Russell",
      "catalogue insensible à la casse")
check(all(M.catalogue(n)["paradoxal"] is True
          for n in ("menteur", "russell", "barbier", "berry", "grelling")),
      "tous les paradoxes catalogués sont paradoxaux")

# ── SOUNDNESS — abstention sur entrée invalide/inconnue (FAUX=0) ──
check(leve(M.catalogue, "inexistant"), "paradoxe inconnu -> ValueError")
check(leve(M.catalogue, "zenon"), "Zénon non catalogué -> ValueError")
check(leve(M.catalogue, 42), "nom non-chaîne -> ValueError")
check(leve(M.est_autoreferentiel, 123, "P"), "phrase non-chaîne -> ValueError")
check(leve(M.est_autoreferentiel, "", "P"), "phrase vide -> ValueError")
check(leve(M.est_autoreferentiel, "Il pleut", 42), "nom non-chaîne -> ValueError")
check(leve(M.est_heterologique, "heterologique", False),
      "mot 'hétérologique' lui-même -> abstention paradoxale")
check(leve(M.est_heterologique, "hétérologique", True),
      "'hétérologique' accentué -> abstention")
check(leve(M.est_heterologique, "", False), "adjectif vide -> ValueError")
check(leve(M.est_heterologique, "long", "non-bool"),
      "se_decrit non-booléen -> ValueError")

# ── DÉTERMINISME ──
check(M.ensemble_russell_paradoxal() == M.ensemble_russell_paradoxal(),
      "déterminisme Russell")
check(M.est_autoreferentiel("Cette phrase est fausse", "L")
      == M.est_autoreferentiel("Cette phrase est fausse", "L"),
      "déterminisme détection")
check(M.catalogue("russell") == M.catalogue("russell"), "déterminisme catalogue")

print(f"\n=== valide_paradoxes : {ok}/{ok + ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
