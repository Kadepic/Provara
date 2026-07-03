"""
VALIDE rhetorique.py — held-out ADVERSE. Vérifie :
  • CATALOGUE EXACT : les 3 modes d'Aristote (ethos/pathos/logos) et 6 figures établies sont reconnus et
    leur définition porte le bon noyau sémantique (crédibilité / émotion / logique ; répétition en début…).
  • CAS d'identification imposés par la spéc : appel à l'autorité=ethos ; appel à la peur=pathos ;
    argument chiffré=logos ; anaphore=répétition en début.
  • SOUNDNESS (FAUX=0) : tout terme/description hors référentiel -> ValueError (jamais d'invention) ;
    insensibilité casse/accents ; ambiguïté -> ValueError ; déterminisme.
"""
import rhetorique as R

ok = 0
ko = 0


def check(cond, label):
    global ok, ko
    if cond:
        ok += 1
    else:
        ko += 1
        print(f"  FAIL: {label}")


def leve_v(fn, *a, **k):
    try:
        fn(*a, **k)
        return False
    except ValueError:
        return True
    except Exception:
        return False


# ── 1) MODES — reconnus + noyau sémantique correct ──
for m in ("ethos", "pathos", "logos"):
    check(isinstance(R.mode_persuasion(m), str) and len(R.mode_persuasion(m)) > 0, f"mode {m} défini")
def _n(s):  # normalisation identique au module (sans accents, ponctuation -> espace)
    return R._norme(s)


check("credibilite" in _n(R.mode_persuasion("ethos")), "ethos = crédibilité de l'orateur")
check("emotion" in _n(R.mode_persuasion("pathos")), "pathos = émotions")
check("logique" in _n(R.mode_persuasion("logos")) or "raison" in _n(R.mode_persuasion("logos")),
      "logos = logique/raison")
check(R.modes() == ("ethos", "pathos", "logos"), "trois modes canoniques")
# insensibilité casse/accents
check(R.mode_persuasion("ETHOS") == R.mode_persuasion("ethos"), "mode insensible à la casse")
check(R.mode_persuasion("  Pathos ") == R.mode_persuasion("pathos"), "mode insensible aux espaces")

# ── 2) FIGURES — reconnues + noyau sémantique correct ──
for f in ("métaphore", "anaphore", "hyperbole", "litote", "antithèse", "chiasme"):
    check(isinstance(R.figure_style(f), str) and len(R.figure_style(f)) > 0, f"figure {f} définie")
# CAS spéc : anaphore = répétition en début
anap = _n(R.figure_style("anaphore"))
check("repetition" in anap and "debut" in anap, "anaphore = répétition en début")
check("analogie" in _n(R.figure_style("métaphore")) or "compar" in _n(R.figure_style("métaphore")),
      "métaphore = analogie")
check("exager" in _n(R.figure_style("hyperbole")), "hyperbole = exagération")
check("attenuation" in _n(R.figure_style("litote")) or "moins" in _n(R.figure_style("litote")),
      "litote = atténuation")
check("opposition" in _n(R.figure_style("antithèse")) or "contrair" in _n(R.figure_style("antithèse")),
      "antithèse = opposition")
check("croise" in _n(R.figure_style("chiasme")) or "ab" in _n(R.figure_style("chiasme")),
      "chiasme = construction croisée")
# accents : "metaphore" sans accent doit marcher aussi
check(R.figure_style("metaphore") == R.figure_style("métaphore"), "figure insensible aux accents")

# ── 3) IDENTIFICATION — cas imposés par la spéc ──
check(R.identifie_mode("appel à l'autorité") == "ethos", "appel à l'autorité = ethos")
check(R.identifie_mode("appel à la peur") == "pathos", "appel à la peur = pathos")
check(R.identifie_mode("argument chiffré") == "logos", "argument chiffré = logos")
check(R.identifie_mode("il invoque la crédibilité de l'orateur") == "ethos", "crédibilité orateur = ethos")
check(R.identifie_mode("ce discours fait un appel aux émotions") == "pathos", "appel aux émotions = pathos")
check(R.identifie_mode("preuve statistique solide") == "logos", "preuve statistique = logos")

# ── 4) SOUNDNESS — hors catalogue -> ValueError (jamais d'invention) ──
check(leve_v(R.mode_persuasion, "kairos"), "mode hors catalogue (kairos) -> abstention")
check(leve_v(R.mode_persuasion, "logique"), "terme proche non canonique -> abstention")
check(leve_v(R.mode_persuasion, ""), "mode vide -> abstention")
check(leve_v(R.mode_persuasion, 42), "mode non textuel -> abstention")
check(leve_v(R.figure_style, "oxymore"), "figure hors catalogue (oxymore) -> abstention")
check(leve_v(R.figure_style, "metonymie"), "figure hors catalogue (métonymie) -> abstention")
check(leve_v(R.figure_style, "ethos"), "mode n'est pas une figure -> abstention")
check(leve_v(R.identifie_mode, "il parle d'un sujet quelconque"), "description sans marqueur -> abstention")
check(leve_v(R.identifie_mode, ""), "description vide -> abstention")
# ambiguïté : marqueurs de deux modes différents -> abstention
check(leve_v(R.identifie_mode, "appel à l'autorité doublé d'un appel à la peur"),
      "description ambiguë (ethos+pathos) -> abstention")

# ── 5) DÉTERMINISME ──
check(R.mode_persuasion("logos") == R.mode_persuasion("logos"), "mode déterministe")
check(R.identifie_mode("argument chiffré") == R.identifie_mode("argument chiffré"), "identif déterministe")
check(R.figure_style("chiasme") == R.figure_style("chiasme"), "figure déterministe")

print(f"\n=== valide_rhetorique : {ok}/{ok+ko} ===")
import sys; sys.exit(0 if ko == 0 else 1)
