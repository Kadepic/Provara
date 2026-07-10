"""
VALIDE integrale_elementaire.py — held-out ADVERSE.

ANCRES EXTERNES NON CIRCULAIRES (faits mathématiques ÉTABLIS, écrits EN DUR — jamais recalculés
par le module testé) :
  • exp(-x²) NON élémentaire — Liouville 1835 (erf n'est pas élémentaire). Fait classique de la
    théorie de l'intégration en termes finis (Rosenlicht, Amer. Math. Monthly 79, 1972).
  • x·exp(-x²) EST élémentaire — primitive -½·exp(-x²), VÉRIFIABLE À LA MAIN par dérivation :
    d/dx(-e^(-x²)/2) = -(1/2)·(-2x)·e^(-x²) = x·e^(-x²). ANCRE DE DISCRIMINATION FORTE : un module
    qui répondrait « non élémentaire » à cause du facteur exp(-x²) serait FAUX.
  • 1/x élémentaire (ln|x|) ; tan(x) élémentaire (-ln|cos x|) ; ln(x) élémentaire (x·ln x - x) —
    dérivations élémentaires classiques, vérifiables à la main.
  • sin(x)/x NON élémentaire (Si), exp(x)/x NON élémentaire (Ei), 1/ln(x) NON élémentaire (li),
    sin(x²)/cos(x²) NON élémentaires (Fresnel S/C), x^x NON élémentaire — résultats démontrés,
    répertoriés dans tout exposé de l'algorithme de Risch.
  • Une fonction inventée ('foobar') -> ValueError (abstention : Risch complet non implémenté).

SOUNDNESS : hors-catalogue, non-str (bool/int/float/None/liste), str vide -> ValueError.
CARDINALITÉ : >= 10 non-élémentaires et >= 9 élémentaires au catalogue, tous testés un à un.
"""
import integrale_elementaire as I

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
    """True ssi fn(*a) lève ValueError (abstention structurelle)."""
    try:
        fn(*a)
        return False
    except ValueError:
        return True


# ── 1) NON ÉLÉMENTAIRES — chaque attendu est un FAIT DÉMONTRÉ, écrit EN DUR ──
# (source : Liouville 1833-1841 ; Risch 1969 ; Rosenlicht 1972 — PAS le module testé)
NON_ELEMENTAIRES = [
    ("exp(-x^2)", "erf non élémentaire, Liouville 1835"),
    ("sin(x)/x", "Si(x) non élémentaire"),
    ("cos(x)/x", "Ci(x) non élémentaire"),
    ("exp(x)/x", "Ei(x) non élémentaire"),
    ("1/ln(x)", "li(x) non élémentaire"),
    ("sqrt(1-k^2*sin^2(x))", "elliptique 2e espèce E(x|k) non élémentaire"),
    ("exp(x^2)", "erfi non élémentaire"),
    ("sin(x^2)", "Fresnel S non élémentaire"),
    ("cos(x^2)", "Fresnel C non élémentaire"),
    ("x^x", "x^x sans primitive élémentaire"),
    ("ln(ln(x))", "ln(ln x) sans primitive élémentaire"),
]
for nom, pourquoi in NON_ELEMENTAIRES:
    check(I.primitive_elementaire(nom) is False, f"{nom} NON élémentaire ({pourquoi})")

# ── 2) ÉLÉMENTAIRES — contre-exemples, primitives vérifiables à la main (dérivation) ──
ELEMENTAIRES = [
    ("x^n", "règle de puissance, n != -1"),
    ("1/x", "d/dx ln|x| = 1/x"),
    ("exp(x)", "d/dx e^x = e^x"),
    ("sin(x)", "d/dx(-cos x) = sin x"),
    ("cos(x)", "d/dx sin x = cos x"),
    ("x*exp(-x^2)", "d/dx(-e^(-x^2)/2) = x·e^(-x^2)"),
    ("1/(1+x^2)", "d/dx arctan x = 1/(1+x^2)"),
    ("tan(x)", "d/dx(-ln|cos x|) = tan x"),
    ("ln(x)", "d/dx(x·ln x - x) = ln x"),
]
for nom, pourquoi in ELEMENTAIRES:
    check(I.primitive_elementaire(nom) is True, f"{nom} élémentaire ({pourquoi})")

# ── 3) ANCRE DE DISCRIMINATION FORTE : exp(-x²) vs x·exp(-x²) ──
# Même facteur exp(-x²), verdicts OPPOSÉS (Liouville 1835 vs dérivation à la main).
check(I.primitive_elementaire("exp(-x^2)") is False and I.primitive_elementaire("x*exp(-x^2)") is True,
      "discrimination : exp(-x^2) NON élémentaire MAIS x*exp(-x^2) élémentaire")
s_gauss = I.statut("x*exp(-x^2)")
check(s_gauss["elementaire"] is True, "statut x*exp(-x^2) : elementaire=True")
check(isinstance(s_gauss["primitive"], str) and "exp(-x^2)" in s_gauss["primitive"].replace(" ", "")
      and "-" in s_gauss["primitive"] and "/2" in s_gauss["primitive"],
      "statut x*exp(-x^2) : primitive = -exp(-x^2)/2 (vérifiable par dérivation)")

# ── 4) STATUT — structure et contenu (références sourcées, primitive=None ssi non élémentaire) ──
s_erf = I.statut("exp(-x^2)")
check(set(s_erf.keys()) == {"elementaire", "reference", "primitive"}, "statut : clés exactes")
check(s_erf["elementaire"] is False, "statut exp(-x^2) : elementaire=False")
check(s_erf["primitive"] is None, "statut exp(-x^2) : primitive=None (aucune primitive élémentaire)")
check(isinstance(s_erf["reference"], str) and "1835" in s_erf["reference"],
      "statut exp(-x^2) : référence cite Liouville 1835")
check("erf" in s_erf["reference"], "statut exp(-x^2) : référence nomme erf")

s_inv = I.statut("1/x")
check(s_inv["elementaire"] is True and s_inv["primitive"] == "ln|x|",
      "statut 1/x : primitive = ln|x| (classique)")
s_tan = I.statut("tan(x)")
check(s_tan["elementaire"] is True and "ln|cos" in s_tan["primitive"].replace(" ", ""),
      "statut tan(x) : primitive = -ln|cos(x)|")
s_li = I.statut("1/ln(x)")
check(s_li["elementaire"] is False and s_li["primitive"] is None and "li" in s_li["reference"],
      "statut 1/ln(x) : non élémentaire, référence nomme li")
s_si = I.statut("sin(x)/x")
check(s_si["elementaire"] is False and "Si" in s_si["reference"],
      "statut sin(x)/x : référence nomme Si")
s_fresnel = I.statut("sin(x^2)")
check(s_fresnel["elementaire"] is False and "fresnel" in s_fresnel["reference"].lower(),
      "statut sin(x^2) : référence nomme Fresnel")
s_ell = I.statut("sqrt(1-k^2*sin^2(x))")
check(s_ell["elementaire"] is False and ("lliptique" in s_ell["reference"] or "lliptic" in s_ell["reference"]),
      "statut elliptique : référence nomme l'intégrale elliptique")

# Toute entrée non élémentaire a primitive=None ; toute élémentaire a une primitive str non vide.
cat = I.catalogue()
check(all((e["primitive"] is None) == (e["elementaire"] is False) for e in cat.values()),
      "catalogue : primitive=None <=> non élémentaire")
check(all(isinstance(e["primitive"], str) and e["primitive"] for e in cat.values() if e["elementaire"]),
      "catalogue : chaque élémentaire porte sa primitive (str non vide)")
check(all(isinstance(e["reference"], str) and e["reference"] for e in cat.values()),
      "catalogue : chaque entrée porte une référence non vide")

# ── 5) CARDINALITÉ DU CATALOGUE (>= 10 non-élémentaires, >= 9 élémentaires) ──
n_non = sum(1 for e in cat.values() if e["elementaire"] is False)
n_oui = sum(1 for e in cat.values() if e["elementaire"] is True)
check(n_non >= 10, f"catalogue : >= 10 non-élémentaires (trouvés : {n_non})")
check(n_oui >= 9, f"catalogue : >= 9 élémentaires (trouvés : {n_oui})")
check(len(cat) == n_non + n_oui, "catalogue : chaque entrée a un verdict booléen")

# catalogue() rend une COPIE : la muter ne change pas le module.
cat["exp(-x^2)"]["elementaire"] = True
check(I.primitive_elementaire("exp(-x^2)") is False, "catalogue() est une copie (mutation sans effet)")
s_mut = I.statut("1/x")
s_mut["elementaire"] = False
check(I.statut("1/x")["elementaire"] is True, "statut() est une copie (mutation sans effet)")

# ── 6) NORMALISATION TYPOGRAPHIQUE (², espaces, casse, **) — jamais sémantique ──
check(I.primitive_elementaire("exp(-x²)") is False, "alias unicode : exp(-x²) reconnu")
check(I.primitive_elementaire("x·exp(-x²)") is True, "alias unicode : x·exp(-x²) reconnu")
check(I.primitive_elementaire("EXP(-X^2)") is False, "casse ignorée : EXP(-X^2)")
check(I.primitive_elementaire(" sin(x)/x ") is False, "espaces ignorés : ' sin(x)/x '")
check(I.primitive_elementaire("x**x") is False, "alias ** : x**x reconnu")
check(I.primitive_elementaire("e^(-x^2)") is False, "alias e^ : e^(-x^2) reconnu")
check(I.primitive_elementaire("sqrt(1-k²·sin²(x))") is False, "alias unicode elliptique reconnu")

# ── 7) CRITÈRE DE LIOUVILLE — énoncé non vide, cite le théorème et l'honnêteté structurelle ──
crit = I.critere_liouville()
check(isinstance(crit, str) and len(crit) > 100, "critère : texte substantiel")
check("Liouville" in crit, "critère : cite Liouville")
check("r' + r" in crit.replace("·", "").replace(" ", "").replace("'+r", "' + r".replace(" ", ""))
      or "r'+r" in crit.replace(" ", ""), "critère : énonce f = r' + r·g'")
check("Risch" in crit and ("PAS implémenté" in crit or "pas implémenté" in crit),
      "critère : dit que Risch complet n'est PAS implémenté")

# ── 8) SOUNDNESS — ABSTENTION hors catalogue (le cœur du FAUX=0) ──
check(leve(I.primitive_elementaire, "foobar"), "'foobar' -> ValueError (abstention)")
check(leve(I.primitive_elementaire, "exp(-x^3)"), "exp(-x^3) hors catalogue -> ValueError (pas de devinette)")
check(leve(I.primitive_elementaire, "sin(x)*cos(x)"), "sin(x)*cos(x) hors catalogue -> ValueError")
check(leve(I.primitive_elementaire, "1/ln(ln(x))"), "1/ln(ln(x)) hors catalogue -> ValueError")
check(leve(I.statut, "foobar"), "statut('foobar') -> ValueError")
check(leve(I.statut, "gamma(x)"), "statut('gamma(x)') hors catalogue -> ValueError")

# ── 9) SOUNDNESS — types invalides ──
check(leve(I.primitive_elementaire, True), "bool -> ValueError (True n'est pas un nom)")
check(leve(I.primitive_elementaire, False), "bool False -> ValueError")
check(leve(I.primitive_elementaire, 1), "int -> ValueError")
check(leve(I.primitive_elementaire, 1.5), "float -> ValueError")
check(leve(I.primitive_elementaire, None), "None -> ValueError")
check(leve(I.primitive_elementaire, ["exp(-x^2)"]), "liste -> ValueError")
check(leve(I.primitive_elementaire, ""), "str vide -> ValueError")
check(leve(I.primitive_elementaire, "   "), "str blanche -> ValueError")
check(leve(I.statut, 3), "statut(int) -> ValueError")
check(leve(I.statut, ""), "statut('') -> ValueError")

# ── 10) DÉTERMINISME ──
check(I.primitive_elementaire("exp(-x^2)") == I.primitive_elementaire("exp(-x^2)"),
      "déterminisme primitive_elementaire")
check(I.statut("tan(x)") == I.statut("tan(x)"), "déterminisme statut")
check(I.catalogue() == I.catalogue(), "déterminisme catalogue")
check(I.critere_liouville() == I.critere_liouville(), "déterminisme critère")

print(f"\n=== valide_integrale_elementaire : {ok}/{ok+ko} ===")
import sys; sys.exit(0 if ko == 0 else 1)
