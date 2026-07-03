"""
VALIDATION du SUBSTRAT-RÉEL (substrat_physique.py).

Cœur = la SOUNDNESS du concept d'invention physique :
  - toute chaîne INVENTION est COHÉRENTE (chaque maillon est un effet réel, les grandeurs s'enchaînent),
    relie bien entrée→sortie, et est NOUVELLE (absente des dispositifs connus) ;
  - un dispositif connu -> EXISTE_DEJA ; une cible inatteignable -> BRIQUE_MANQUANTE ;
  - déterminisme ; jamais une chaîne incohérente présentée comme invention.
"""
from __future__ import annotations

from garde_ressources import borne
import substrat_physique as P

borne()
ok = 0
total = 0


def check(nom, cond):
    global ok, total
    total += 1
    print(f"  [{'OK ' if cond else 'XXX'}] {nom}")
    if cond:
        ok += 1
    else:
        raise AssertionError(nom)


# 1) EXISTE_DEJA — dispositifs connus (1 et 2 maillons)
check("lumière→électricité = EXISTE_DEJA (cellule solaire)", P.examine("lumiere", "electricite").statut == P.EXISTE_DEJA)
check("mouvement→lumière = EXISTE_DEJA (lampe-dynamo)", P.examine("mouvement", "lumiere").statut == P.EXISTE_DEJA)

# 2) INVENTION — chaîne cohérente nouvelle, avec les principes à combiner
v = P.examine("pression", "lumiere")
check("pression→lumière = INVENTION", v.statut == P.INVENTION)
check("pression→lumière : principes = piézo direct + LED", v.chaine == ("piézo direct", "LED"))
check("pression→lumière : transduction pression→electricite→lumiere",
      v.grandeurs == ("pression", "electricite", "lumiere"))
v2 = P.examine("chaleur", "radio")
check("chaleur→radio = INVENTION (Seebeck + antenne)", v2.statut == P.INVENTION and v2.chaine == ("Seebeck", "antenne émission"))

# 3) BRIQUE_MANQUANTE — grandeur-cible sans aucun PRODUCTEUR (aucune arête entrante)
check("son→gravité = BRIQUE_MANQUANTE (on ne synthétise pas la gravité)", P.examine("son", "gravite").statut == P.BRIQUE_MANQUANTE)
check("électricité→gravité = BRIQUE_MANQUANTE", P.examine("electricite", "gravite").statut == P.BRIQUE_MANQUANTE)
check("électricité→nucléaire = BRIQUE_MANQUANTE (nucléaire = source-only)", P.examine("electricite", "nucleaire").statut == P.BRIQUE_MANQUANTE)

# 3-asym) ASYMÉTRIE PHYSIQUE HONNÊTE — gravité & nucléaire SONT des sources (arête sortante) mais ne sont
#         PAS synthétisables (aucune arête entrante). Fait réel, pas un trou de modélisation.
aretes = {(e, s) for _, e, s, _ in P.TRANSDUCTEURS}
check("gravité PRODUIT (gravite→mouvement existe : chute/hydro)", ("gravite", "mouvement") in aretes)
check("gravité non synthétisable (aucune arête → gravite)", not any(s == "gravite" for _, s in aretes))
check("nucléaire non synthétisable (aucune arête → nucleaire)", not any(s == "nucleaire" for _, s in aretes))
check("gravité→électricité = EXISTE_DEJA (barrage hydroélectrique)", P.examine("gravite", "electricite").statut == P.EXISTE_DEJA)

# 3bis) ANTI-FAUSSE-INVENTION — un PRINCIPE UNIQUE avéré (arête directe) est EXISTE_DEJA, jamais INVENTION,
#       même hors DISPOSITIFS_CONNUS : un effet physique réel connu n'est pas une invention.
sl = P.examine("son", "lumiere")  # sonoluminescence : effet réel, arête directe
check("son→lumière (sonoluminescence, principe unique) = EXISTE_DEJA", sl.statut == P.EXISTE_DEJA and len(sl.chaine) == 1)
check("chimie→chaleur (combustion, principe unique) = EXISTE_DEJA", P.examine("chimie", "chaleur").statut == P.EXISTE_DEJA)
check("INVARIANT : aucune INVENTION n'a une chaîne de longueur 1 (combinaison ≥ 2 maillons)",
      all(len(P.examine(e, s).chaine) >= 2
          for e in P.GRANDEURS for s in P.GRANDEURS
          if e != s and P.examine(e, s).statut == P.INVENTION))

# 3ter) DENSIFICATION — un couplage chimie↔lumière nouveau émerge maintenant comme invention multi-maillon.
vc = P.examine("pression", "chimie")  # piézo direct → électrolyse : pression qui déclenche une réaction
check("pression→chimie = INVENTION (combinaison nouvelle ≥2)", vc.statut == P.INVENTION and len(vc.chaine) >= 2)

# 4) DÉTERMINISME
check("déterministe", str(P.examine("pression", "lumiere")) == str(P.examine("pression", "lumiere")))

# 5) INVARIANT DE SOUNDNESS — sur TOUTES les paires de grandeurs, toute INVENTION est :
#    (a) cohérente, (b) connecte entrée→sortie, (c) nouvelle (hors dispositifs connus).
inv_ok = True
n_inv = 0
for e in P.GRANDEURS:
    for s in P.GRANDEURS:
        if e == s:
            continue
        v = P.examine(e, s)
        if v.statut == P.INVENTION:
            n_inv += 1
            coherente = P._coherente(v.grandeurs)
            relie = v.grandeurs and v.grandeurs[0] == e and v.grandeurs[-1] == s
            nouvelle = v.grandeurs not in P._connus()
            if not (coherente and relie and nouvelle):
                inv_ok = False
check(f"INVARIANT : les {n_inv} inventions sont cohérentes + connectées + nouvelles", inv_ok)

# 6) INVARIANT INVERSE — un EXISTE_DEJA correspond bien à une transduction CONNUE
#    (dispositif curé multi-maillon OU principe unique avéré).
ed_ok = True
for e in P.GRANDEURS:
    for s in P.GRANDEURS:
        if e == s:
            continue
        v = P.examine(e, s)
        if v.statut == P.EXISTE_DEJA and v.grandeurs not in P._connus():
            ed_ok = False
check("INVARIANT : tout EXISTE_DEJA est une transduction réellement connue", ed_ok)

# 7) LACUNES PRIORITAIRES — le levier mesuré est EXACT et la liste triée décroissante.
lac = P.lacunes_prioritaires(6)
check("lacunes : liste non vide", len(lac) > 0)
check("lacunes : triée par levier décroissant", all(lac[i][0] >= lac[i + 1][0] for i in range(len(lac) - 1)))
base = P._atteignables()
exact = all(g == len(P._atteignables(extra=(a, b)) - base) for g, a, b in lac)
check("lacunes : le levier rapporté = capacités réellement débloquées (sound)", exact)
check("lacunes : aucune lacune ne porte sur une arête déjà existante",
      all((a, b) not in {(e, s) for _, e, s, _ in P.TRANSDUCTEURS} for _, a, b in lac))
# synthétiser la gravité (ou le nucléaire) = la brique non-synthétisable la plus précieuse → en tête
check("lacunes : synthétiser gravité/nucléaire est en tête (levier max)",
      lac[0][2] in ("gravite", "nucleaire"))

print(f"\nSUBSTRAT_PHYSIQUE VALIDÉ — {ok}/{total}." if ok == total else f"\nÉCHEC {ok}/{total}")
