"""VALIDE pseudosciences.py — catalogue de consensus fermé + abstention hors catalogue (FAUX=0).

Le module rapporte un STATUT DE PREUVE sourcé (aucune/non_demontree), jamais une vérité métaphysique. Contrôle
négatif clé : hors catalogue -> ValueError (pas de verdict inventé) ; aucune pratique n'a de validité démontrée.
"""
import pseudosciences as P

ok = 0
ko = 0


def check(cond, label):
    global ok, ko
    if cond:
        ok += 1
    else:
        ko += 1
        print(f"  FAIL: {label}")


def leve(fn, *a, **k):
    try:
        fn(*a, **k)
        return False
    except ValueError:
        return True
    except Exception:
        return False


# ── 1) Statuts d'ancres (consensus établi) ──
check(P.validite_scientifique("astrologie") == "aucune", "astrologie : validité aucune (Carlson 1985)")
check(P.validite_scientifique("voyance") == "aucune", "voyance : aucune")
check(P.validite_scientifique("numerologie") == "aucune", "numérologie : aucune")
check(P.validite_scientifique("superstitions") == "aucune", "superstitions : aucune")
check(P.validite_scientifique("phenomenes_paranormaux") == "non_demontree", "paranormal : non démontré")

# ── 2) Alias résolus ──
check(P.validite_scientifique("horoscope") == "aucune", "alias horoscope -> astrologie")
check(P.validite_scientifique("paranormal") == "non_demontree", "alias paranormal")
check(P.validite_scientifique("ESP") == "non_demontree", "alias ESP")
check(P.est_catalogue("Astrologie") and not P.est_catalogue("chimie"), "est_catalogue discrimine")

# ── 3) base_consensus non vide + a_validite_demontree toujours False ──
check(len(P.base_consensus("astrologie")) > 10, "base de consensus sourcée")
check(P.a_validite_demontree("astrologie") is False, "aucune validité démontrée sur le catalogue")
check(len(P.pratiques()) >= 10, "catalogue ≥ 10 pratiques")

# ── 4) FAUX=0 : hors catalogue -> ValueError (jamais deviné) ──
check(leve(P.validite_scientifique, "physique_quantique"), "science réelle hors catalogue -> ValueError")
check(leve(P.validite_scientifique, "truc_invente_xyz"), "inconnu -> ValueError")
check(leve(P.a_validite_demontree, "inconnu"), "a_validite_demontree hors catalogue -> ValueError")
check(leve(P.validite_scientifique, 123), "type non-str -> ValueError")

print(f"\n=== valide_pseudosciences : {ok}/{ok + ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
