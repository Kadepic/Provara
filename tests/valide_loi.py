"""
VALIDATION des LOIS MANIPULABLES (loi.py) — Vague 2. Dépend de dimensions.py + grandeur.py.

FAUX=0 :
  • Inversabilité SOUND : une loi (E=½mv², U=RI) se résout pour N'IMPORTE quelle variable, résultat typé correct.
  • Round-trip cohérent (verifie_coherence) : les solveurs d'une loi sont mutuellement sains.
  • Entrée de mauvaise dimension / manquante / cible non inversable -> HORS (None), jamais un nombre faux.
  • Solveur numérique par bisection : racine encadrée -> trouvée ; non encadrée -> HORS.
"""
from __future__ import annotations

import math

import dimensions as D
from grandeur import Grandeur
from loi import Loi, solveur_numerique

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


# ── Loi 1 : énergie cinétique E = ½·m·v², inversable pour E, m, v ────────────────────────
Ec = Loi("énergie_cinétique",
         variables={"E": D.ENERGIE, "m": D.MASSE, "v": D.VITESSE},
         solveurs={
             "E": lambda m, v: 0.5 * m * v * v,
             "m": lambda E, v: 2 * E / (v * v) if v else None,
             "v": lambda E, m: math.sqrt(2 * E / m) if m > 0 and E >= 0 else None,
         })
gE = Ec.resout("E", m=Grandeur.depuis(2, "kg"), v=Grandeur.depuis(3, "m/s"))
check("E depuis m,v : ½·2·9 = 9 J (dimension énergie)", gE.dim == D.ENERGIE and abs(gE.en("J") - 9) < 1e-9)
gv = Ec.resout("v", E=Grandeur.depuis(9, "J"), m=Grandeur.depuis(2, "kg"))
check("INVERSION : v depuis E,m = 3 m/s (dimension vitesse)", gv.dim == D.VITESSE and abs(gv.en("m/s") - 3) < 1e-9)
gm = Ec.resout("m", E=Grandeur.depuis(9, "J"), v=Grandeur.depuis(3, "m/s"))
check("INVERSION : m depuis E,v = 2 kg", gm.dim == D.MASSE and abs(gm.en("kg") - 2) < 1e-9)
check("round-trip cohérent des 3 solveurs (verifie_coherence)",
      Ec.verifie_coherence({"E": Grandeur.depuis(9, "J"), "m": Grandeur.depuis(2, "kg"), "v": Grandeur.depuis(3, "m/s")}))

# ── FAUX=0 : mauvaise dimension, cible fournie, manquant, non inversable -> HORS ──────────
check("REJET : v de mauvaise dimension (temps au lieu de vitesse) -> HORS",
      Ec.resout("E", m=Grandeur.depuis(2, "kg"), v=Grandeur.depuis(3, "s")) is None)
check("REJET : entrée manquante -> HORS", Ec.resout("E", m=Grandeur.depuis(2, "kg")) is None)
check("REJET : cible aussi fournie -> HORS",
      Ec.resout("E", E=Grandeur.depuis(1, "J"), m=Grandeur.depuis(2, "kg"), v=Grandeur.depuis(3, "m/s")) is None)
check("REJET : entrée nue (pas une Grandeur) -> HORS", Ec.resout("E", m=2, v=3) is None)

# ── Loi 2 : loi d'Ohm U = R·I ────────────────────────────────────────────────────────────
Ohm = Loi("loi_d_Ohm",
          variables={"U": D.TENSION, "R": D.RESISTANCE, "I": D.COURANT},
          solveurs={"U": lambda R, I: R * I, "R": lambda U, I: U / I if I else None,
                    "I": lambda U, R: U / R if R else None})
gU = Ohm.resout("U", R=Grandeur.depuis(10, "Ω"), I=Grandeur(2, D.COURANT))
check("Ohm : U = 10 Ω × 2 A = 20 V", gU.dim == D.TENSION and abs(gU.en("V") - 20) < 1e-9)
gI = Ohm.resout("I", U=Grandeur.depuis(20, "V"), R=Grandeur.depuis(10, "Ω"))
check("Ohm inversé : I = 20 V / 10 Ω = 2 A", gI.dim == D.COURANT and abs(gI.valeur - 2) < 1e-9)

# ── Solveur numérique (bisection) sur une loi non inversée analytiquement ─────────────────
# x tel que x² = aire (racine carrée numérique), aire donnée -> côté. Résidu = x² - aire.
carre = Loi("côté_d_un_carré",
            variables={"cote": D.LONGUEUR, "aire": D.AIRE},
            solveurs={"cote": solveur_numerique(lambda x, aire: x * x - aire, 0.0, 1e6),
                      "aire": lambda cote: cote * cote})
gc = carre.resout("cote", aire=Grandeur.depuis(9, "m") * Grandeur.depuis(1, "m"))  # 9 m²
check("bisection : côté d'un carré de 9 m² = 3 m", abs(gc.en("m") - 3) < 1e-4 and gc.dim == D.LONGUEUR)
check("bisection racine non encadrée -> HORS",
      solveur_numerique(lambda x, aire: x * x + aire, 1.0, 2.0)(aire=1.0) is None)

# ── verifie_coherence détecte une loi mal inversée ───────────────────────────────────────
faux = Loi("loi_incohérente",
           variables={"a": D.LONGUEUR, "b": D.LONGUEUR},
           solveurs={"a": lambda b: b, "b": lambda a: a * 2})   # a=b mais b=2a : incohérent
check("verifie_coherence FAUX sur solveurs incohérents",
      not faux.verifie_coherence({"a": Grandeur.depuis(5, "m"), "b": Grandeur.depuis(5, "m")}))

# ── DOMAINE DE VALIDITÉ (durcissement 2026-07-02) : une loi hors de son champ physique -> HORS ──────────
# COP de Carnot d'une pompe à chaleur : COP = Tc/(Tc - Tf), valide seulement si Tc > Tf > 0. Hors de ce champ,
# la formule rend un nombre ABSURDE (COP négatif ou infini) — le domaine doit faire abstenir (FAUX=0).
cop = Loi("cop_carnot",
          variables={"cop": D.SANS, "Tc": D.TEMPERATURE, "Tf": D.TEMPERATURE},
          solveurs={"cop": lambda Tc, Tf: Tc / (Tc - Tf) if Tc != Tf else None},
          domaine=lambda cop, Tc, Tf: Tc > Tf > 0)
gcop = cop.resout("cop", Tc=Grandeur(300, D.TEMPERATURE), Tf=Grandeur(270, D.TEMPERATURE))
check("DOMAINE : COP Carnot dans le champ (Tc>Tf>0) -> résultat (300/30=10)",
      gcop is not None and abs(gcop.valeur - 10.0) < 1e-9)
check("DOMAINE FAUX=0 : Tf>Tc (hors champ) -> HORS (pas de COP négatif absurde)",
      cop.resout("cop", Tc=Grandeur(270, D.TEMPERATURE), Tf=Grandeur(300, D.TEMPERATURE)) is None)
check("DOMAINE FAUX=0 : Tf=0 K (hors champ) -> HORS",
      cop.resout("cop", Tc=Grandeur(300, D.TEMPERATURE), Tf=Grandeur(0, D.TEMPERATURE)) is None)
check("DOMAINE : dans_domaine() explicite (Tc>Tf>0)",
      cop.dans_domaine(cop=10.0, Tc=300.0, Tf=270.0) and not cop.dans_domaine(cop=-9.0, Tc=270.0, Tf=300.0))
# backward-compat : une loi SANS domaine se comporte exactement comme avant (aucune contrainte).
libre = Loi("aire_rectangle", variables={"aire": D.AIRE, "L": D.LONGUEUR, "l": D.LONGUEUR},
            solveurs={"aire": lambda L, l: L * l})
check("BACKWARD-COMPAT : loi sans domaine -> comportement inchangé",
      libre.resout("aire", L=Grandeur(3, D.LONGUEUR), l=Grandeur(4, D.LONGUEUR)) is not None
      and libre.dans_domaine(aire=12.0, L=3.0, l=4.0))
check("DOMAINE FAUX=0 : domaine qui lève une exception -> traité comme NON satisfait (conservateur)",
      not Loi("x", {"a": D.LONGUEUR}, {}, domaine=lambda **k: 1 / 0).dans_domaine(a=1.0))

print(f"\n=== valide_loi : {ok}/{total} checks OK ===")
if ok != total:
    raise SystemExit(1)
