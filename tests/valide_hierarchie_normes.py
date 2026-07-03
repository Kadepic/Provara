"""
VALIDE hierarchie_normes.py — held-out ADVERSE. Ancres de droit français CONNUES (constitution > loi >
décret ; traité > loi par l'art. 55 ; décret > arrêté ; un décret doit respecter la loi) + SOUNDNESS
(type hors pyramide -> ValueError, jamais un rang inventé) + DÉTERMINISME (mêmes entrées -> mêmes sorties).
"""
import hierarchie_normes as H

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


# ── 1) RANGS ÉTABLIS — la constitution au sommet, l'acte individuel à la base ──
check(H.rang("constitution") == 1, "constitution = rang 1 (sommet)")
check(H.rang("traite_international") == 2, "traité international = rang 2")
check(H.rang("loi") == 3, "loi = rang 3")
check(H.rang("decret") == 4, "décret = rang 4")
check(H.rang("reglement") == 4, "règlement = rang 4 (= décret)")
check(H.rang("arrete") == 5, "arrêté = rang 5")
check(H.rang("contrat") == 6, "contrat = rang 6 (base)")
check(H.rang("acte_individuel") == 6, "acte individuel = rang 6 (base)")
# casse / espaces tolérés (normalisation)
check(H.rang("  LOI ") == 3, "normalisation casse/espaces : '  LOI ' = rang 3")

# ── 2) PRIMAUTÉ — constitution > loi > décret ; traité > loi (art. 55) ; décret > arrêté ──
check(H.superieur("constitution", "loi") is True, "constitution prime la loi")
check(H.superieur("loi", "decret") is True, "loi prime le décret")
check(H.superieur("constitution", "decret") is True, "constitution prime le décret (transitif)")
check(H.superieur("traite_international", "loi") is True, "traité > loi en France (art. 55 C.)")
check(H.superieur("decret", "arrete") is True, "décret > arrêté")
check(H.superieur("loi", "constitution") is False, "la loi NE prime PAS la constitution")
check(H.superieur("loi", "traite_international") is False, "la loi NE prime PAS le traité")
check(H.superieur("loi", "loi") is False, "même rang -> pas de primauté stricte")

# ── 3) SUBORDINATION / MÊME RANG ──
check(H.inferieur("decret", "loi") is True, "le décret est subordonné à la loi")
check(H.inferieur("loi", "decret") is False, "la loi n'est pas subordonnée au décret")
check(H.meme_rang("loi", "loi_organique") is True, "loi et loi organique = même étage législatif")
check(H.meme_rang("decret", "reglement") is True, "décret et règlement = même étage réglementaire")
check(H.meme_rang("loi", "decret") is False, "loi et décret = étages distincts")

# ── 4) CONFORMITÉ — une norme doit respecter les normes de rang supérieur ──
check(H.conforme("decret", "loi") is True, "un décret doit respecter la loi")
check(H.conforme("loi", "constitution") is True, "une loi doit respecter la constitution")
check(H.conforme("arrete", "decret") is True, "un arrêté doit respecter le décret")
check(H.conforme("loi", "traite_international") is True, "une loi doit respecter le traité (art. 55)")
check(H.conforme("loi", "decret") is False, "la loi NE se conforme PAS à un décret (rang inférieur)")
check(H.conforme("constitution", "loi") is False, "la constitution NE se conforme PAS à la loi")
check(H.conforme("loi", "loi_organique") is True, "même rang : conformité requise (>=)")

# ── 5) DOMINATION / PYRAMIDE CANONIQUE ──
check(H.domine("constitution")[0] == "traite_international", "la constitution domine le traité juste en dessous")
check("loi" in H.domine("constitution"), "la constitution domine la loi")
check(H.domine("acte_individuel") == [], "rien n'est subordonné à la base (acte individuel)")
hp = H.hierarchie()
check(hp[0] == (1, "constitution") and hp[-1] == (6, "acte_individuel"), "pyramide : sommet=constitution, base=acte")
check([r for r, _ in hp] == [1, 2, 3, 4, 5, 6], "pyramide ordonnée 1..6 sans trou")

# ── 6) SOUNDNESS — type HORS pyramide -> ValueError (jamais un rang inventé) ──
check(leve(H.rang, "circulaire"), "circulaire (norme infra-décrétale non cataloguée) -> ValueError")
check(leve(H.rang, "jurisprudence"), "jurisprudence (statut débattu, hors catalogue) -> ValueError")
check(leve(H.rang, "coutume"), "coutume -> ValueError")
check(leve(H.rang, ""), "chaîne vide -> ValueError")
check(leve(H.rang, "norme_inconnue_xyz"), "type inventé -> ValueError")
check(leve(H.rang, 42), "type non-str (int) -> ValueError")
check(leve(H.superieur, "loi", "fantaisie"), "superieur avec type inconnu -> ValueError")
check(leve(H.conforme, "blabla", "loi"), "conforme avec type inconnu -> ValueError")
check(leve(H.domine, "inexistant"), "domine avec type inconnu -> ValueError")

# ── 7) DÉTERMINISME — mêmes entrées -> mêmes sorties ──
check(all(H.rang("decret") == 4 for _ in range(5)), "rang déterministe")
check(H.hierarchie() == H.hierarchie(), "hierarchie() déterministe")
check(H.domine("loi") == H.domine("loi"), "domine() déterministe")

# ── 8) COHÉRENCE STRUCTURELLE — antisymétrie & transitivité de la primauté ──
check(not (H.superieur("loi", "decret") and H.superieur("decret", "loi")), "antisymétrie primauté")
check(H.superieur("constitution", "loi") and H.superieur("loi", "arrete")
      and H.superieur("constitution", "arrete"), "transitivité de la primauté")

print(f"\n=== valide_hierarchie_normes : {ok}/{ok+ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
