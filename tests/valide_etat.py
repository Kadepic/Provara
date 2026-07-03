"""
VALIDATION des ÉTATS & VARIABLES (etat.py) — Vague 1.
FAUX=0 : valeur hors domaine/dimension refusée, variable inconnue refusée, immuabilité (transition = nouvel état).
"""
from __future__ import annotations

import dimensions as D
from grandeur import Grandeur
from etat import EspaceEtats, ValeurHorsDomaine

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


# Espace mixte : une variable à domaine fini (phase) + une variable continue (température).
E = EspaceEtats()
E.variable("phase", domaine={"solide", "liquide", "gaz"})
E.variable("temperature", dimension=D.TEMPERATURE)

s0 = E.etat(phase="liquide", temperature=Grandeur.depuis(20, "°C"))
check("état valide construit", s0.valeur("phase") == "liquide")
check("variable non affectée -> None", E.etat(phase="solide").valeur("temperature") is None)
check("état complet détecté", s0.complet() and not E.etat(phase="gaz").complet())

# ── Transition = nouvel état (immuabilité) ───────────────────────────────────────────────
s1 = s0.avec(phase="gaz", temperature=Grandeur.depuis(120, "°C"))
check("transition produit un nouvel état", s1.valeur("phase") == "gaz")
check("l'état d'origine est INCHANGÉ (immuable)", s0.valeur("phase") == "liquide")
check("deux états différents ne sont pas égaux", s0 != s1)
check("états hachables (utilisables en set)", len({s0, s1, s0}) == 2)

# ── FAUX=0 : valeur hors domaine fini refusée ────────────────────────────────────────────
check("valeur hors domaine fini -> ValeurHorsDomaine",
      leve(lambda: E.etat(phase="plasma", temperature=Grandeur.depuis(0, "K")), ValeurHorsDomaine))

# ── FAUX=0 : mauvaise dimension pour une variable continue ───────────────────────────────
check("valeur de mauvaise dimension (énergie au lieu de température) -> refus",
      leve(lambda: E.etat(phase="gaz", temperature=Grandeur.depuis(5, "J")), ValeurHorsDomaine))
check("valeur nue (pas une Grandeur) sur variable continue -> refus",
      leve(lambda: E.etat(phase="gaz", temperature=300), ValeurHorsDomaine))

# ── FAUX=0 : variable inconnue refusée ───────────────────────────────────────────────────
check("variable inconnue -> refus", leve(lambda: E.etat(couleur="rouge"), ValeurHorsDomaine))

# ── Déclaration de variable : exactement un type ─────────────────────────────────────────
check("variable sans domaine NI dimension -> refus", leve(lambda: EspaceEtats().variable("x"), ValueError))
check("variable avec domaine ET dimension -> refus",
      leve(lambda: EspaceEtats().variable("x", domaine={1}, dimension=D.MASSE), ValueError))
check("transition vers une valeur invalide -> refus (re-validation)",
      leve(lambda: s0.avec(phase="plasma"), ValeurHorsDomaine))

print(f"\n=== valide_etat : {ok}/{total} checks OK ===")
if ok != total:
    raise SystemExit(1)
