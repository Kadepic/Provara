"""
VALIDE medecines_alternatives.py — held-out ADVERSE.

Ancres = niveaux de preuve issus du CONSENSUS établi (méta-analyses / Cochrane / rapports d'agences),
posés à la main (non re-dérivés par le module) :
  • homéopathie = aucune preuve (ne dépasse PAS le placebo) — cas-pivot du sujet ;
  • acupuncture = preuve faible ; ostéopathie/chiropraxie = preuve limitée ;
  • reiki/chakras/soins énergétiques/magnétothérapie/lithothérapie/réflexologie = aucune preuve ;
  • phytothérapie = variable (verdict placebo non agrégeable -> abstention) ;
  • méditation pleine conscience = preuve modérée (dépasse le placebo).
+ INVARIANTS de soundness :
  - tout niveau renvoyé ∈ NIVEAUX ;
  - depasse_placebo ne renvoie JAMAIS True pour une pratique 'aucune_preuve' (faux positif interdit) ;
  - depasse_placebo cohérent avec le niveau ('variable'/'faible'/'limitee' -> abstention) ;
  - hors catalogue / non tranché / non-str -> ValueError (jamais un verdict inventé) ;
+ normalisation (accents, casse, synonymes) ; + DÉTERMINISME.
"""
import medecines_alternatives as A

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


# ── 1) ANCRES NIVEAU DE PREUVE — consensus établi, posées à la main ──
ANCRES = {
    "homeopathie": "aucune_preuve",
    "reiki": "aucune_preuve",
    "chakras": "aucune_preuve",
    "soins_energetiques": "aucune_preuve",
    "magnetotherapie": "aucune_preuve",
    "lithotherapie": "aucune_preuve",
    "reflexologie": "aucune_preuve",
    "acupuncture": "preuve_faible",
    "osteopathie": "preuve_limitee",
    "chiropraxie": "preuve_limitee",
    "phytotherapie": "variable",
    "meditation_pleine_conscience": "preuve_moderee",
}
for p, attendu in ANCRES.items():
    check(A.niveau_preuve(p) == attendu, f"niveau_preuve({p}) = {attendu}")

# ── 2) CAS-PIVOTS du sujet ──
check(A.niveau_preuve("homeopathie") == "aucune_preuve", "homéopathie = aucune preuve (pivot)")
check(A.depasse_placebo("homeopathie") is False, "homéopathie NE dépasse PAS le placebo (pivot)")
check(A.niveau_preuve("phytotherapie") == "variable", "phytothérapie = variable (pivot)")
check(_leve_v(A.depasse_placebo, "phytotherapie"), "phytothérapie : verdict placebo non tranché -> abstention")

# ── 3) DEPASSE_PLACEBO — verdicts tranchés (True/False stricts) ──
for p in ("homeopathie", "reiki", "chakras", "soins_energetiques",
          "magnetotherapie", "lithotherapie", "reflexologie"):
    check(A.depasse_placebo(p) is False, f"depasse_placebo({p}) is False")
check(A.depasse_placebo("meditation_pleine_conscience") is True,
      "depasse_placebo(méditation pleine conscience) is True")

# ── 4) DEPASSE_PLACEBO — non tranché -> abstention (jamais True/False deviné) ──
for p in ("acupuncture", "osteopathie", "chiropraxie", "phytotherapie"):
    check(_leve_v(A.depasse_placebo, p), f"depasse_placebo({p}) non tranché -> ValueError")

# ── 5) NORMALISATION — accents / casse / espaces / synonymes ──
check(A.niveau_preuve("Homéopathie") == "aucune_preuve", "accent + casse : Homéopathie")
check(A.niveau_preuve("  ACUPUNCTURE  ") == "preuve_faible", "casse + espaces : ACUPUNCTURE")
check(A.niveau_preuve("méditation pleine conscience") == "preuve_moderee", "espaces : méditation pleine conscience")
check(A.niveau_preuve("mindfulness") == "preuve_moderee", "synonyme EN : mindfulness")
check(A.niveau_preuve("homeopathy") == "aucune_preuve", "synonyme EN : homeopathy")
check(A.niveau_preuve("chiropractic") == "preuve_limitee", "synonyme EN : chiropractic")
check(A.niveau_preuve("crystal healing") == "aucune_preuve", "synonyme EN : crystal healing -> lithothérapie")
check(A.niveau_preuve("soin énergétique") == "aucune_preuve", "synonyme : soin énergétique (singulier)")
check(A.depasse_placebo("Homéopathie") is False, "depasse_placebo normalisé : Homéopathie")

# ── 6) ABSTENTION — hors catalogue : pratiques plausibles mais NON répertoriées -> ValueError ──
HORS = [
    "naturopathie", "kinesiologie", "biorésonance", "bioresonance", "fleurs de bach",
    "auriculotherapie", "ventouses", "iridologie", "fasciatherapie", "sophrologie",
    "ostéothérapie", "medecine", "plante", "aimant", "yoga", "hypnose", "diététique",
    "vaccin", "chimiothérapie", "antibiotique", "placebo", "acuponcteur", "homeo",
]
for p in HORS:
    check(_leve_v(A.niveau_preuve, p), f"hors catalogue {p!r} -> niveau ValueError")
    check(_leve_v(A.depasse_placebo, p), f"hors catalogue {p!r} -> placebo ValueError")
    check(A.est_catalogue(p) is False, f"est_catalogue({p!r}) is False")

# ── 7) ABSTENTION — entrées invalides (non-str / vide) -> ValueError ──
for bad in [None, 123, 3.14, ["homeopathie"], {"x": 1}, b"reiki", True, "", "   ", "  -- "]:
    check(_leve_v(A.niveau_preuve, bad), f"invalide {bad!r} -> niveau ValueError")
    check(_leve_v(A.depasse_placebo, bad), f"invalide {bad!r} -> placebo ValueError")
check(A.est_catalogue(None) is False, "est_catalogue(None) is False (ne lève pas)")
check(A.est_catalogue(123) is False, "est_catalogue(123) is False (ne lève pas)")

# ── 8) INVARIANTS de soundness sur TOUT le catalogue ──
cat = A.pratiques()
check(len(cat) == len(set(cat)) == 12, "catalogue = 12 pratiques distinctes")
for p in cat:
    n = A.niveau_preuve(p)
    # (a) tout niveau renvoyé appartient à l'ensemble fermé NIVEAUX
    check(n in A.NIVEAUX, f"niveau({p})={n!r} ∈ NIVEAUX")
    # (b) depasse_placebo : soit un bool strict, soit une abstention — jamais autre chose
    try:
        d = A.depasse_placebo(p)
        check(d in (True, False), f"depasse_placebo({p}) est un bool strict")
        # (c) FAUX POSITIF INTERDIT : une pratique 'aucune_preuve' ne dépasse JAMAIS le placebo
        if n == "aucune_preuve":
            check(d is False, f"aucune_preuve -> depasse_placebo({p}) is False (pas de faux positif)")
        # (d) un True n'est possible que pour un niveau modéré/fort
        if d is True:
            check(n in ("preuve_moderee", "preuve_forte"), f"depasse_placebo True ⇒ niveau fort ({p})")
    except ValueError:
        # abstention légitime uniquement pour les niveaux non tranchés
        check(n in ("preuve_faible", "preuve_limitee", "variable"),
              f"abstention placebo légitime seulement si non tranché ({p}={n})")

# Invariant inverse : aucune pratique 'aucune_preuve' ne renvoie True
for p in cat:
    if A.niveau_preuve(p) == "aucune_preuve":
        check(A.depasse_placebo(p) is False, f"INVARIANT aucune_preuve∧placebo=False ({p})")

# ── 9) DÉTERMINISME — fonctions pures ──
check(A.niveau_preuve("acupuncture") == A.niveau_preuve("acupuncture"), "niveau déterministe")
check([A.niveau_preuve("homeopathie") for _ in range(5)] == ["aucune_preuve"] * 5, "niveau 5 appels identiques")
check(A.depasse_placebo("reiki") == A.depasse_placebo("reiki"), "placebo déterministe")
check(A.pratiques() == A.pratiques(), "pratiques() déterministe")

# ── 10) PREUVE auto-portée intégrée ──
check(A._p_medecines_alternatives() is True, "_p_medecines_alternatives() == True")

print(f"\n=== valide_medecines_alternatives : {ok}/{ok+ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
