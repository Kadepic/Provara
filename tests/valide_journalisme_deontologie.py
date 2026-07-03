"""
VALIDE journalisme_deontologie.py — held-out ADVERSE.

Ancres = devoirs établis des chartes (Munich 1971 / SPJ Code of Ethics), posés À LA MAIN :
  • les 7 principes sont reconnus et décrits ; tout nom hors charte -> ValueError ;
  • verdicts non ambigus des CAS de référence (vérifier/publier-sans-vérifier, séparation faits/opinions,
    protection des sources, droit de réponse, présomption d'innocence, indépendance, rectification) ;
  • robustesse de surface (accents, casse, espaces) sans accepter d'inconnu ;
  • SOUNDNESS : pratique hors catalogue / principe hors charte / non-str -> ValueError ;
  • DÉTERMINISME.
"""
import journalisme_deontologie as J

ok = 0
ko = 0


def check(cond, label):
    global ok, ko
    if cond:
        ok += 1
    else:
        ko += 1
        print(f"  FAIL: {label}")


def _leve_v(fn, *a, **k) -> bool:
    """True ssi fn(*a, **k) lève ValueError (abstention), False sinon."""
    try:
        fn(*a, **k)
        return False
    except ValueError:
        return True
    except Exception:
        return False


PRINCIPES = ("verification/exactitude", "separation_faits_opinions", "protection_sources",
             "droit_de_reponse", "presomption_innocence", "independance", "rectification")

# ── 1) PRINCIPES — closed-set de 7, chacun décrit ──
check(J.liste_principes() == PRINCIPES, "liste_principes = les 7 devoirs canoniques")
for p in PRINCIPES:
    d = J.principe(p)
    check(isinstance(d, str) and len(d) > 20, f"principe({p!r}) décrit (str non vide)")
# contenu des descriptions = bon devoir
check("verit" in J._strip_accents(J.principe("verification/exactitude")).lower()
      and "verifier" in J._strip_accents(J.principe("verification/exactitude")).lower(),
      "verification/exactitude parle de vérité + vérifier")
check("commentaire" in J.principe("separation_faits_opinions").lower()
      or "opinion" in J.principe("separation_faits_opinions").lower(),
      "separation_faits_opinions parle de commentaire/opinion")
check("source" in J.principe("protection_sources").lower(), "protection_sources parle de source")
check("reponse" in J._strip_accents(J.principe("droit_de_reponse")).lower(), "droit_de_reponse parle de réponse")
check("innocence" in J.principe("presomption_innocence").lower(), "presomption_innocence parle d'innocence")
check("independance" in J._strip_accents(J.principe("independance")).lower(), "independance parle d'indépendance")
check("rectif" in J.principe("rectification").lower() or "corrig" in J.principe("rectification").lower(),
      "rectification parle de rectifier/corriger")
# déterminisme de la description
check(J.principe("protection_sources") == J.principe("protection_sources"), "principe déterministe")

# ── 2) CAS de référence (énoncé) — verdicts ──
check(J.respecte_deontologie("publier sans vérifier") == "violation", "publier sans vérifier -> violation")
check(J.respecte_deontologie("protéger une source") == "conforme", "protéger une source -> conforme")
check(J.respecte_deontologie("vérifier avant publier") == "conforme", "vérifier avant publier -> conforme")
check(J.respecte_deontologie("vérifier avant de publier") == "conforme", "vérifier avant de publier -> conforme")
check(J.respecte_deontologie("séparer faits et commentaires") == "conforme",
      "séparer faits et commentaires -> conforme")
check(J.respecte_deontologie("révéler une source confidentielle") == "violation",
      "révéler une source confidentielle -> violation")

# ── 3) Principe concerné par chaque pratique (CAS : « = principe d'exactitude », « = principe ») ──
check(J.principe_concerne("vérifier avant publier") == "verification/exactitude",
      "vérifier avant publier -> principe verification/exactitude")
check(J.principe_concerne("publier sans vérifier") == "verification/exactitude",
      "publier sans vérifier -> principe verification/exactitude")
check(J.principe_concerne("séparer faits et commentaires") == "separation_faits_opinions",
      "séparer faits et commentaires -> principe separation_faits_opinions")
check(J.principe_concerne("protéger une source") == "protection_sources",
      "protéger une source -> principe protection_sources")
check(J.principe_concerne("révéler une source confidentielle") == "protection_sources",
      "révéler une source confidentielle -> principe protection_sources")
# evalue = (statut, principe)
check(J.evalue("publier sans vérifier") == ("violation", "verification/exactitude"),
      "evalue(publier sans vérifier) = (violation, verification/exactitude)")
check(J.evalue("protéger une source") == ("conforme", "protection_sources"),
      "evalue(protéger une source) = (conforme, protection_sources)")
# est_conforme cohérent avec respecte_deontologie
check(J.est_conforme("protéger une source") is True, "est_conforme protéger une source = True")
check(J.est_conforme("publier sans vérifier") is False, "est_conforme publier sans vérifier = False")

# ── 4) Couverture des 7 principes par au moins une pratique conforme ET une violation ──
for p in PRINCIPES:
    confs = [c for c, (s, pr) in J._PRATIQUES.items() if pr == p and s == "conforme"]
    viols = [c for c, (s, pr) in J._PRATIQUES.items() if pr == p and s == "violation"]
    check(len(confs) >= 1 and len(viols) >= 1, f"principe {p}: ≥1 conforme et ≥1 violation catalogués")
# tout principe référencé par une pratique appartient bien à la charte
check(all(pr in PRINCIPES for (s, pr) in J._PRATIQUES.values()), "tout principe catalogué ∈ charte")
check(all(s in ("conforme", "violation") for (s, pr) in J._PRATIQUES.values()), "statuts ∈ {conforme,violation}")

# ── 5) Autres cas non ambigus du catalogue ──
check(J.respecte_deontologie("accorder un droit de réponse") == "conforme", "droit de réponse accordé -> conforme")
check(J.respecte_deontologie("refuser un droit de réponse") == "violation", "droit de réponse refusé -> violation")
check(J.respecte_deontologie("respecter la présomption d'innocence") == "conforme",
      "présomption respectée -> conforme")
check(J.respecte_deontologie("désigner un coupable avant jugement") == "violation",
      "désigner coupable avant jugement -> violation")
check(J.respecte_deontologie("refuser la pression d'un annonceur") == "conforme",
      "refuser pression annonceur -> conforme")
check(J.respecte_deontologie("publier un publireportage déguisé") == "violation",
      "publireportage déguisé -> violation")
check(J.respecte_deontologie("rectifier une information inexacte") == "conforme",
      "rectifier info inexacte -> conforme")
check(J.respecte_deontologie("refuser de rectifier") == "violation", "refuser de rectifier -> violation")
check(J.respecte_deontologie("mêler faits et opinions") == "violation", "mêler faits et opinions -> violation")

# ── 6) ROBUSTESSE de surface (accents/casse/espaces) — sans accepter d'inconnu ──
check(J.respecte_deontologie("PROTÉGER UNE SOURCE") == "conforme", "casse haute tolérée")
check(J.respecte_deontologie("  protéger   une  source  ") == "conforme", "espaces multiples tolérés")
check(J.respecte_deontologie("proteger une source") == "conforme", "sans accent toléré")
check(J.respecte_deontologie("proteger une source") == J.respecte_deontologie("Protéger une source"),
      "normalisation stable accents/casse")

# ── 7) SOUNDNESS — abstention (ValueError), JAMAIS un faux verdict ──
# principe hors charte
check(_leve_v(J.principe, "objectivite_totale"), "principe inconnu -> ValueError")
check(_leve_v(J.principe, "neutralite"), "principe 'neutralite' (hors set) -> ValueError")
check(_leve_v(J.principe, "verification"), "clé partielle 'verification' -> ValueError (pas la clé exacte)")
check(_leve_v(J.principe, ""), "principe vide -> ValueError")
check(_leve_v(J.principe, True), "principe booléen -> ValueError")
check(_leve_v(J.principe, None), "principe None -> ValueError")
check(_leve_v(J.principe, 3), "principe int -> ValueError")
# pratique hors catalogue / ambiguë -> abstention
check(_leve_v(J.respecte_deontologie, "faire un scoop"), "pratique inconnue 'faire un scoop' -> ValueError")
check(_leve_v(J.respecte_deontologie, "interviewer un témoin"), "pratique inconnue -> ValueError")
check(_leve_v(J.respecte_deontologie, "publier"), "pratique trop vague 'publier' -> ValueError")
check(_leve_v(J.respecte_deontologie, ""), "pratique vide -> ValueError")
check(_leve_v(J.respecte_deontologie, True), "pratique booléenne -> ValueError")
check(_leve_v(J.respecte_deontologie, None), "pratique None -> ValueError")
check(_leve_v(J.respecte_deontologie, 42), "pratique int -> ValueError")
check(_leve_v(J.principe_concerne, "faire un scoop"), "principe_concerne inconnu -> ValueError")
check(_leve_v(J.evalue, "faire un scoop"), "evalue inconnu -> ValueError")
check(_leve_v(J.est_conforme, "faire un scoop"), "est_conforme inconnu -> ValueError")

# ── 8) DÉTERMINISME ──
check(J.respecte_deontologie("protéger une source") == J.respecte_deontologie("protéger une source"),
      "respecte_deontologie déterministe")
check([J.respecte_deontologie("publier sans vérifier") for _ in range(5)] == ["violation"] * 5,
      "5 appels identiques -> 'violation'")
check(J.evalue("publier sans vérifier") == J.evalue("publier sans vérifier"), "evalue déterministe")
check(J.liste_principes() == J.liste_principes(), "liste_principes déterministe")

print(f"\n=== valide_journalisme_deontologie : {ok}/{ok+ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
