"""VALIDE raisonnement_defaut.py — exception prime, défaut sur membre connu, abstention sur inconnu, FAUX=0.

Scénario canonique (oiseaux volent, sauf manchot/autruche) + conflit d'exceptions. Prouve la non-monotonie SOUND :
révision par le cas particulier, jamais de conclusion sur un individu d'appartenance inconnue.
"""
import raisonnement_defaut as RD

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


# ── Scénario : normalement, un oiseau vole ──
r = RD.RegleDefaut("oiseau", "vole", True)
r.ajoute_membre("moineau").ajoute_membre("aigle")
r.sauf("manchot", False).sauf("autruche", False)

# ── 1) Défaut sur membre connu non-exceptionnel ──
st, v, _ = r.conclut("moineau")
check(st == RD.DEFAUT and v is True, "moineau (oiseau connu) -> défaut vole=True")

# ── 2) Exception prime le défaut (non-monotonie SOUND) ──
st, v, _ = r.conclut("manchot")
check(st == RD.EXCEPTION and v is False, "manchot (exception) -> vole=False, prime le défaut")
st, v, _ = r.conclut("autruche")
check(st == RD.EXCEPTION and v is False, "autruche (exception) -> vole=False")

# ── 3) Abstention sur individu d'appartenance inconnue (FAUX=0 : jamais deviné) ──
st, v, raison = r.conclut("wandering_xyz")
check(st == RD.ABSTIENT and v is None, "individu inconnu -> ABSTIENT (pas de conclusion)")
check("abstention" in raison.lower(), "abstention tracée")

# ── 4) est_exception / vaut_en_general / exceptions ──
check(r.est_exception("manchot") is True and r.est_exception("moineau") is False, "est_exception discrimine")
check(r.vaut_en_general() is True, "cas général = défaut True")
check(r.exceptions() == {"manchot": False, "autruche": False}, "table des exceptions")

# ── 5) Un membre ajouté APRÈS reste sound ──
r.ajoute_membre("colibri")
check(r.conclut("colibri")[0] == RD.DEFAUT, "nouveau membre -> défaut")

# ── 6) Révision : déclarer une exception sur un ex-membre défaut le fait basculer ──
r2 = RD.RegleDefaut("metal", "solide_20C", True)
r2.ajoute_membre("fer")
check(r2.conclut("fer")[0] == RD.DEFAUT, "fer -> défaut solide")
r2.sauf("mercure", False)
check(r2.conclut("mercure") == (RD.EXCEPTION, False, r2.conclut("mercure")[2]), "mercure exception -> liquide")

# ── 7) FAUX=0 : conflits et entrées invalides -> ValueError ──
check(leve(r.sauf, "manchot", True), "exception contradictoire (manchot False puis True) -> ValueError")
check(leve(RD.RegleDefaut, "", "p", True), "classe vide -> ValueError")
check(leve(RD.RegleDefaut, "c", "p", None), "valeur défaut None -> ValueError")
check(leve(r.sauf, "x", None), "valeur d'exception None -> ValueError")
check(leve(r.ajoute_membre, None), "membre None -> ValueError")
# idempotence : re-déclarer la MÊME exception (même valeur) est OK
r.sauf("manchot", False)
check(r.conclut("manchot")[1] is False, "re-déclaration identique d'exception tolérée")

print(f"\n=== valide_raisonnement_defaut : {ok}/{ok + ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
