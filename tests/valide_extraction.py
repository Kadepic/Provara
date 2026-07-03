"""VALIDATION extraction.py (Vague 8). FAUX=0 : hors motif -> rien ; candidats avec confiance+provenance ; sûrs filtrés."""
from __future__ import annotations
from extraction import extrait, extrait_surs

ok = 0; total = 0
def check(nom, cond):
    global ok, total; total += 1
    print(f"  [{'OK ' if cond else 'XXX'}] {nom}", flush=True)
    if cond: ok += 1
    else: raise AssertionError(nom)

c = extrait("Paris est la capitale de la France.")
check("motif 'capitale' extrait le bon triplet (France, capitale, Paris)",
      len(c) == 1 and c[0]["triplet"] == ("France", "capitale", "Paris"))
check("confiance élevée pour un motif spécifique", c[0]["confiance"] >= 0.9)
check("provenance conservée", c[0]["source"] == "texte")

c2 = extrait("La pénicilline a été découverte par Alexander Fleming.")
check("motif 'découvreur' -> (pénicilline, decouvreur, Fleming)",
      c2 and c2[0]["triplet"][1] == "decouvreur" and "Fleming" in c2[0]["triplet"][2])

# FAUX=0 : phrase hors motif -> aucune extraction (abstention, pas de triplet deviné)
check("phrase sans motif connu -> rien extrait", extrait("Le ciel est parfois nuageux au printemps quand.") == [])

# extrait_surs filtre par seuil : 'est un' (0.7) sous 0.9 -> pas asserté
faible = extrait("Le chat est un animal.")
check("motif faible 'est_un' présent en candidat", faible and faible[0]["motif"] == "est_un")
check("extrait_surs(0.9) écarte le motif faible (reste candidat, non asserté)",
      extrait_surs("Le chat est un animal.", seuil=0.9) == [])
check("extrait_surs garde le motif fort (capitale)",
      len(extrait_surs("Paris est la capitale de la France.", seuil=0.9)) == 1)

# Plusieurs phrases
multi = extrait("Paris est la capitale de la France. Rome est la capitale de l'Italie.")
check("extraction multi-phrases (2 triplets)", len(multi) == 2)

print(f"\n=== valide_extraction : {ok}/{total} checks OK ===")
if ok != total: raise SystemExit(1)
