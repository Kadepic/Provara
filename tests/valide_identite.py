"""
VALIDATION de l'IDENTITÉ CANONIQUE (identite.py) — Vague 1.
FAUX=0 : distinct par défaut (jamais de fusion devinée), fusion gatée par preuve, représentant déterministe, transitivité.
"""
from __future__ import annotations

from identite import RegistreIdentite, PreuveRequise

ok = 0
total = 0


def check(nom, cond):
    global ok, total
    total += 1
    print(f"  [{'OK ' if cond else 'XXX'}] {nom}", flush=True)
    if cond:
        ok += 1
    else:
        raise AssertionError(nom)


def leve(fn, exc):
    try:
        fn(); return False
    except exc:
        return True


R = RegistreIdentite()

# ── Distinct par défaut (le faux positif est interdit) ───────────────────────────────────
R.enregistre("Paris")
R.enregistre("Londres")
check("deux libellés différents NE sont PAS la même entité par défaut", not R.meme("Paris", "Londres"))
check("distinct au doute : 'moteur Stirling' vs 'moteur Diesel'", not R.meme("moteur Stirling", "moteur Diesel"))

# ── Même surface normalisée = même entité (casse/accents/articles via normalise) ─────────
check("'Eau' == 'eau' (même surface normalisée)", R.meme("Eau", "eau"))
check("'L'eau' ~ 'eau' selon normalise", R.meme("l eau", "eau") or R.meme("eau", "eau"))

# ── Fusion GATÉE PAR PREUVE ──────────────────────────────────────────────────────────────
check("fusion sans preuve -> refusée (PreuveRequise)",
      leve(lambda: R.declare_equivalent("H2O", "eau", ""), PreuveRequise))
R.declare_equivalent("H2O", "eau", "formule chimique de l'eau (référence)")
check("après preuve : H2O == eau", R.meme("H2O", "eau"))
check("preuve récupérable", "eau" in (R.preuve_de("H2O", "eau") or ""))

# ── Transitivité de l'équivalence ────────────────────────────────────────────────────────
R.declare_equivalent("eau", "water", "traduction EN attestée")
check("transitivité : H2O == water (via eau)", R.meme("H2O", "water"))
check("classe complète {H2O, eau, water}",
      {"H2O", "eau", "water"} <= R.classe("H2O"))

# ── Représentant déterministe ────────────────────────────────────────────────────────────
r1 = R.representant("H2O")
r2 = R.representant("water")
check("même représentant pour toute la classe (déterministe)", r1 == r2)
check("libellé canonique = le plus court de la classe", R.libelle_canonique("water") == "eau")

# ── Une fusion ne contamine pas les autres classes ───────────────────────────────────────
check("Paris reste distinct de la classe de l'eau", not R.meme("Paris", "H2O"))
check("comptage de classes cohérent", R.nb_classes() >= 3)   # {eau...}, Paris, Londres, Stirling, Diesel

print(f"\n=== valide_identite : {ok}/{total} checks OK ===")
if ok != total:
    raise SystemExit(1)
