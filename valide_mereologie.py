"""
VALIDATION de la MÉRÉOLOGIE (mereologie.py) — Vague 1.
FAUX=0 : irréflexivité (X pas partie de X), acyclicité (cycle refusé), transitivité SOUND (jamais de partie inventée).
"""
from __future__ import annotations

from mereologie import Assemblage, CycleMereologique

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


# ── Un artefact = assemblage de parties (ex. climatiseur) ────────────────────────────────
a = Assemblage()
for p, role in [("compresseur", "compression"), ("condenseur", "rejet_chaleur"),
                ("détendeur", "détente"), ("évaporateur", "absorption_chaleur")]:
    a.ajoute_partie(p, "climatiseur", role=role)
a.ajoute_partie("moteur", "compresseur", role="entraînement")     # sous-partie
check("parties directes du climatiseur = 4", len(a.parties_directes("climatiseur")) == 4)
check("transitivité : le moteur est (indirectement) une partie du climatiseur",
      a.contient("climatiseur", "moteur"))
check("clôture transitive complète (5 parties)", len(a.parties("climatiseur")) == 5)
check("rôle d'une partie récupérable", a.role_de("condenseur", "climatiseur")[0] == "rejet_chaleur")
check("racine = climatiseur (partie de rien)", a.racines() == {"climatiseur"})
check("feuilles atomiques incluent le moteur/condenseur/détendeur/évaporateur",
      "moteur" in a.feuilles() and "condenseur" in a.feuilles())
check("montée : les touts contenant le moteur incluent compresseur ET climatiseur",
      a.touts("moteur") == {"compresseur", "climatiseur"})

# ── FAUX=0 : irréflexivité ───────────────────────────────────────────────────────────────
check("REJET : X partie de X (irréflexif)",
      leve(lambda: a.ajoute_partie("pièce", "pièce"), CycleMereologique))

# ── FAUX=0 : acyclicité ──────────────────────────────────────────────────────────────────
b = Assemblage()
b.ajoute_partie("roue", "voiture")
b.ajoute_partie("voiture", "convoi")
check("REJET : arête qui fermerait un cycle (convoi partie de roue)",
      leve(lambda: b.ajoute_partie("convoi", "roue"), CycleMereologique))
check("après rejet du cycle, la structure reste saine",
      b.contient("convoi", "roue") and not b.contient("roue", "convoi"))

# ── FAUX=0 : pas de partie inventée ──────────────────────────────────────────────────────
check("contient() faux pour une relation jamais posée", not a.contient("climatiseur", "réacteur nucléaire"))
check("parties() ne renvoie que des parties réelles",
      all(x in {"compresseur", "condenseur", "détendeur", "évaporateur", "moteur"}
          for x in a.parties("climatiseur")))

print(f"\n=== valide_mereologie : {ok}/{total} checks OK ===")
if ok != total:
    raise SystemExit(1)
