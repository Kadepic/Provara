"""VALIDE heraldique.py — catalogue fermé + règle de contrariété exacte + FAUX=0 (abstention hors catalogue)."""
import heraldique as H

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


# ── 1) Catégories ──
check(H.categorie("or") == "metal" and H.categorie("argent") == "metal", "métaux")
check(H.categorie("gueules") == "couleur" and H.categorie("azur") == "couleur", "couleurs")
check(H.categorie("hermine") == "fourrure" and H.categorie("vair") == "fourrure", "fourrures")
check(H.categorie("OR") == "metal", "casse insensible")

# ── 2) Règle de contrariété (rule of tincture) ──
check(H.contraste_valide("or", "gueules") is True, "métal sur couleur -> valide")
check(H.contraste_valide("azur", "argent") is True, "couleur sur métal -> valide")
check(H.contraste_valide("or", "argent") is False, "métal sur métal -> VIOLE la règle")
check(H.contraste_valide("gueules", "azur") is False, "couleur sur couleur -> VIOLE la règle")
check(H.contraste_valide("gueules", "sinople") is False, "couleur sur couleur (2) -> viole")
check(H.contraste_valide("hermine", "gueules") is True, "fourrure neutre -> valide avec couleur")
check(H.contraste_valide("or", "hermine") is True, "fourrure neutre -> valide avec métal")

# ── 3) Teintes modernes + catalogue ──
check(H.teintes_modernes("gueules") == "rouge" and H.teintes_modernes("azur") == "bleu", "teintes modernes")
cat = H.teintures()
check(cat["metaux"] == ["argent", "or"] and len(cat["couleurs"]) == 5, "catalogue fermé")

# ── 4) FAUX=0 ──
check(leve(H.categorie, "turquoise"), "teinture hors catalogue -> ValueError")
check(leve(H.contraste_valide, "or", "rose"), "figure hors catalogue -> ValueError")
check(leve(H.teintes_modernes, "hermine"), "pas de teinte moderne pour fourrure -> ValueError")
check(leve(H.categorie, 42), "type non-str -> ValueError")

print(f"\n=== valide_heraldique : {ok}/{ok + ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
