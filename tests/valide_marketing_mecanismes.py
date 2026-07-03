"""
VALIDE marketing_mecanismes.py — held-out ADVERSE.

Modèle AIDA (ordre A->I->D->A, rangs et rôles) + 6 principes de Cialdini (définitions sourcées) + SOUNDNESS
(étape/principe inconnu, entrée invalide -> ValueError) + déterminisme. Aucun de ces cas n'est dans __main__
du module.
"""
import marketing_mecanismes as M

ok = 0
ko = 0


def check(cond, label):
    global ok, ko
    if cond:
        ok += 1
    else:
        ko += 1
        print(f"  FAIL: {label}")


def _leve(fn, *a, **k):
    """True ssi fn(*a, **k) lève ValueError (abstention), False sinon."""
    try:
        fn(*a, **k)
        return False
    except ValueError:
        return True
    except Exception:
        return False


# 1) AIDA — les 4 étapes existent et ont les bons rangs (ordre A->I->D->A).
check(M.etape_aida("attention").rang == 1, "attention = rang 1")
check(M.etape_aida("interet").rang == 2, "interet = rang 2")
check(M.etape_aida("desir").rang == 3, "desir = rang 3")
check(M.etape_aida("action").rang == 4, "action = rang 4")

# 2) AIDA — l'ORDRE canonique est exactement A -> I -> D -> A.
check(M.ordre_aida() == ["attention", "interet", "desir", "action"], "ordre AIDA = A->I->D->A")
# rangs strictement croissants dans l'ordre déclaré.
rangs = [M.rang_aida(n) for n in M.ordre_aida()]
check(rangs == [1, 2, 3, 4], "rangs AIDA dans l'ordre = 1,2,3,4")
# les noms d'étapes sont uniques et au nombre de 4.
check(len(set(M.ordre_aida())) == 4, "AIDA = 4 étapes distinctes")

# 3) AIDA — rôles : chaque étape a un rôle non vide et l'action concerne le déclenchement/l'achat.
check(isinstance(M.etape_aida("attention").role, str) and M.etape_aida("attention").role.strip() != "",
      "rôle attention non vide")
check("attention" in M.etape_aida("attention").role.lower(), "rôle attention parle d'attention")
check(("action" in M.etape_aida("action").role.lower())
      or ("achat" in M.etape_aida("action").role.lower()), "rôle action = déclencher l'action/achat")
check("désir" in M.etape_aida("desir").role.lower() or "envie" in M.etape_aida("desir").role.lower(),
      "rôle désir parle de désir/envie")

# 4) AIDA — robustesse de la casse / espaces (normalisation), même résultat.
check(M.etape_aida("  ATTENTION ") == M.etape_aida("attention"), "AIDA insensible casse/espaces")

# 5) CIALDINI — les 6 principes connus renvoient une définition non vide.
for p in ["reciprocite", "engagement_coherence", "preuve_sociale", "autorite", "sympathie", "rarete"]:
    d = M.principe_cialdini(p).definition
    check(isinstance(d, str) and d.strip() != "", f"définition non vide pour {p}")

# 6) CIALDINI — il y a EXACTEMENT 6 principes, distincts.
check(len(M.principes_cialdini()) == 6, "Cialdini = 6 principes")
check(len(set(M.principes_cialdini())) == 6, "Cialdini = 6 principes distincts")

# 7) CAS imposés par la spéc — rareté = « édition limitée », preuve sociale = « des milliers de clients ».
check("limit" in M.definition_cialdini("rarete").lower(), "rareté = édition limitée")
check("milliers de clients" in M.definition_cialdini("preuve_sociale").lower(),
      "preuve sociale = des milliers de clients")
# réciprocité parle bien de rendre/rendre la pareille.
check("rend" in M.definition_cialdini("reciprocite").lower(), "réciprocité = rendre la faveur")
# autorité parle d'expertise/autorité.
check("autorit" in M.definition_cialdini("autorite").lower(), "autorité = figure d'autorité")

# 8) CIALDINI — robustesse casse/espaces.
check(M.principe_cialdini("RARETE") == M.principe_cialdini("rarete"), "Cialdini insensible casse")

# 9) SOUNDNESS AIDA — étape inconnue / invalide -> ValueError (jamais devinée).
check(_leve(M.etape_aida, "memorisation"), "étape AIDA inconnue 'memorisation' -> ValueError")
check(_leve(M.etape_aida, "satisfaction"), "AIDAS étendu 'satisfaction' -> ValueError (hors AIDA)")
check(_leve(M.etape_aida, "conviction"), "AIDCA 'conviction' -> ValueError (hors AIDA strict)")
check(_leve(M.etape_aida, ""), "étape vide -> ValueError")
check(_leve(M.etape_aida, "   "), "étape blancs -> ValueError")
check(_leve(M.etape_aida, 123), "étape non textuelle -> ValueError")
check(_leve(M.etape_aida, None), "étape None -> ValueError")
check(_leve(M.etape_aida, True), "étape booléenne -> ValueError")
check(_leve(M.rang_aida, "inconnue"), "rang_aida inconnu -> ValueError")

# 10) SOUNDNESS CIALDINI — principe inconnu (faux « 7e principe ») / invalide -> ValueError.
check(_leve(M.principe_cialdini, "unite"), "Cialdini 'unite' (7e principe récent) -> ValueError")
check(_leve(M.principe_cialdini, "peur"), "principe inventé 'peur' -> ValueError")
check(_leve(M.principe_cialdini, "consistance"), "synonyme non canonique 'consistance' -> ValueError")
check(_leve(M.principe_cialdini, ""), "principe vide -> ValueError")
check(_leve(M.principe_cialdini, 0), "principe non textuel -> ValueError")
check(_leve(M.principe_cialdini, None), "principe None -> ValueError")
check(_leve(M.definition_cialdini, "inexistant"), "definition_cialdini inconnu -> ValueError")

# 11) DÉTERMINISME.
check(M.etape_aida("desir") == M.etape_aida("desir"), "déterminisme etape_aida")
check(M.principe_cialdini("autorite") == M.principe_cialdini("autorite"), "déterminisme principe_cialdini")
check(M.ordre_aida() == M.ordre_aida(), "déterminisme ordre_aida")

print(f"\n=== valide_marketing_mecanismes : {ok}/{ok+ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
