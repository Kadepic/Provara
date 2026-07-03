"""
VALIDATION ADVERSARIALE des EXTERNALITÉS (externalites.py). Vérifie : les ancres connues (pollution=négative,
vaccination/abeilles=positive, coût social=privé+externe, taxe Pigou=coût externe marginal, sens de la défaillance) ;
la cohérence du signe pour l'impact numérique ; la SOUNDNESS (coûts négatifs, type/exemple inconnu, impact nul, non-numérique
⇒ ValueError) ; le DÉTERMINISME (mêmes entrées ⇒ mêmes sorties). Pur Python.
"""
from __future__ import annotations

from garde_ressources import borne
import externalites as M

borne()
ok = 0
ko = 0


def check(cond, label):
    global ok, ko
    if cond:
        ok += 1
        print(f"  [OK ] {label}")
    else:
        ko += 1
        print(f"  [XXX] {label}")


def leve_valueerror(fn, *a, **k):
    try:
        fn(*a, **k)
        return False
    except ValueError:
        return True
    except Exception:
        return False


# ─── 1. Ancres CATALOGUE (exemples canoniques sourcés) ───
print("=== Ancres : type d'externalité (catalogue) ===")
check(M.type_externalite("pollution") == "negative", "pollution = externalité négative")
check(M.type_externalite("Pollution") == "negative", "casse/espaces tolérés (normalisation)")
check(M.type_externalite("tabagisme passif") == "negative", "tabagisme passif = négative")
check(M.type_externalite("congestion routiere") == "negative", "congestion routière = négative")
check(M.type_externalite("vaccination") == "positive", "vaccination = externalité positive")
check(M.type_externalite("abeilles") == "positive", "abeilles (pollinisation) = positive")
check(M.type_externalite("pollinisation") == "positive", "pollinisation = positive")
check(M.type_externalite("education") == "positive", "éducation = positive")

# ─── 2. Signe de l'impact numérique sur les tiers ───
print("=== Type d'après le signe de l'impact tiers ===")
check(M.type_externalite(-5.0) == "negative", "impact tiers négatif (coût) ⇒ négative")
check(M.type_externalite(3.0) == "positive", "impact tiers positif (bénéfice) ⇒ positive")
check(M.type_externalite(0.5) == "positive", "petit bénéfice ⇒ positive")
check(M.type_externalite(-1) == "negative", "coût entier ⇒ négative")

# ─── 3. Coût social = privé + externe ───
print("=== Coût social ===")
check(M.cout_social(10.0, 4.0) == 14.0, "coût social privé 10 + externe 4 = 14")
check(M.cout_social(0.0, 0.0) == 0.0, "aucun coût ⇒ 0")
check(M.cout_social(7, 0) == 7.0, "sans externalité, coût social = coût privé")
check(M.cout_social(2.5, 1.25) == 3.75, "additivité exacte (flottants)")
check(M.cout_social(100.0, 30.0) >= M.cout_social(100.0, 0.0), "coût externe ≥ 0 ⇒ coût social ≥ coût privé")

# ─── 4. Taxe pigouvienne = coût externe marginal ───
print("=== Taxe de Pigou ===")
check(M.taxe_pigou(4.0) == 4.0, "taxe Pigou = coût externe marginal (4)")
check(M.taxe_pigou(0.0) == 0.0, "coût externe marginal nul ⇒ taxe nulle")
# la taxe pigouvienne aligne le coût privé sur le coût social
ce = 6.0
check(M.cout_social(12.0, ce) == 12.0 + M.taxe_pigou(ce), "taxe Pigou internalise exactement le coût externe")

# ─── 5. Défaillance de marché (sens) ───
print("=== Défaillance de marché ===")
check(M.defaillance_marche("negative") == "surproduction", "externalité négative non internalisée ⇒ surproduction")
check(M.defaillance_marche("positive") == "sous-production", "externalité positive non internalisée ⇒ sous-production")
check(M.defaillance_marche(M.type_externalite("pollution")) == "surproduction", "chaîne pollution ⇒ surproduction")
check(M.defaillance_marche(M.type_externalite("vaccination")) == "sous-production", "chaîne vaccination ⇒ sous-production")

# ─── 6. Internalisation (pédagogique) ───
print("=== Internalisation ===")
check(M.internalisee(10.0, 4.0, True) == 14.0, "internalisée ⇒ agent supporte privé + externe")
check(M.internalisee(10.0, 4.0, False) == 10.0, "non internalisée ⇒ agent ne supporte que le privé")

# ─── 7. SOUNDNESS : abstention (ValueError) ───
print("=== Soundness : abstention ===")
check(leve_valueerror(M.cout_social, -1.0, 4.0), "coût privé négatif ⇒ ValueError")
check(leve_valueerror(M.cout_social, 4.0, -1.0), "coût externe négatif ⇒ ValueError")
check(leve_valueerror(M.taxe_pigou, -1.0), "coût externe marginal négatif ⇒ ValueError")
check(leve_valueerror(M.defaillance_marche, "neutre"), "type d'externalité inconnu ⇒ ValueError")
check(leve_valueerror(M.defaillance_marche, "POSITIVE"), "type mal casé non deviné ⇒ ValueError")
check(leve_valueerror(M.type_externalite, "subvention_xyz"), "exemple hors catalogue ⇒ ValueError")
check(leve_valueerror(M.type_externalite, 0), "impact tiers nul ⇒ ValueError")
check(leve_valueerror(M.type_externalite, 0.0), "impact tiers nul (float) ⇒ ValueError")
check(leve_valueerror(M.type_externalite, True), "booléen non numérique ⇒ ValueError")
check(leve_valueerror(M.cout_social, "10", 4.0), "coût non numérique ⇒ ValueError")
check(leve_valueerror(M.internalisee, 10.0, 4.0, "oui"), "prise_en_compte non booléenne ⇒ ValueError")

# ─── 8. DÉTERMINISME ───
print("=== Déterminisme ===")
det = all(M.type_externalite("pollution") == "negative" for _ in range(50))
det &= all(M.cout_social(10.0, 4.0) == 14.0 for _ in range(50))
det &= all(M.taxe_pigou(4.0) == 4.0 for _ in range(50))
det &= all(M.defaillance_marche("positive") == "sous-production" for _ in range(50))
check(det, "sorties identiques sur 50 répétitions (déterminisme)")

print(f"\n=== valide_externalites : {ok}/{ok+ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
