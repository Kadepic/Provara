#!/usr/bin/env python3
"""VALIDE le capstone boucle_invention (besoin->assemblage->gap->corroboration->writeback) — ADVERSE, FAUX=0.

Contrat jugé : (1) besoin connu -> PROPOSE avec candidats SUPPOSITIONS (jamais des faits) + trous + faits de
grounding traités ; (2) besoin inconnu -> HORS à l'étape 'objectif' (abstient au 1er maillon, jamais fabriqué) ;
(3) un fait de grounding corroboré+jugé -> PERSISTÉ ; contredisant le store -> RÉFUTÉ (jamais écrit) ; sous-corroboré
-> SUPPOSÉ ; (4) le candidat d'invention reste SUPPOSITION générative — le capstone ne le promeut JAMAIS en fait.

LÉGER : persistance/lecteur INJECTÉS (store factice) — pas de chargement du lecteur (besoin/transfert lisent des
catalogues internes, pas le lecteur des 77M faits)."""
import os
import sys

os.environ.setdefault("LECTEUR_AMORCE_SEULE", "1")
_ICI = os.path.dirname(os.path.abspath(__file__)) or "."
sys.path.insert(0, _ICI)

import boucle_invention as BI
import veille_corroboration as VC
import atome as A

ok = 0
ko = 0


def check(c, l):
    global ok, ko
    if c:
        ok += 1
    else:
        ko += 1
        print(f"  FAIL: {l}")


O = VC.Observation


class FauxStore:
    def __init__(self, initial=None):
        self.d = dict(initial or {})

    def persiste(self, relation, paires, categorie, source):
        n = 0
        for e, v in paires:
            k = (relation, " ".join(str(e).strip().lower().split()))
            if k in self.d and self.d[k] != v:
                raise ValueError(f"conflit {k}")
            self.d[k] = v
            n += 1
        return n

    def cherche(self, relation, entite):
        v = self.d.get((relation, " ".join(str(entite).strip().lower().split())))
        if v is None:
            return None
        class _F:
            valeur = v
        return _F()


# ── 1) BESOIN CONNU -> PROPOSE (candidats = suppositions, jamais des faits) ──
s = FauxStore()
r = BI.boucle("rafraichir une piece", persiste=s.persiste, lecteur=s)
check(r["statut"] == BI.PROPOSE and r["etape"] == "complet", "besoin connu -> PROPOSE complet")
check(bool(r["objectif"]) and "AIR" in r["objectif"].upper(), "objectif reframé (le corps, pas l'air)")
check(len(r["candidats"]) >= 1 and r["meilleur"] is not None, "au moins 1 candidat + meilleur désigné")
check(all(c["statut_atome"] == "supposition" for c in r["candidats"]),
      "TOUS les candidats sont des SUPPOSITIONS (jamais des faits) — cœur FAUX=0 du capstone")
check(all(0.0 < c["confiance"] < 1.0 for c in r["candidats"]), "confiances de supposition dans ]0,1[")
check(isinstance(r["trous"], list) and len(r["trous"]) >= 1, "gap : au moins un trou diagnostiqué")

# ── 2) BESOIN INCONNU -> HORS à l'étape 'objectif' (abstient au 1er maillon) ──
r = BI.boucle("coloniser mars ce weekend")
check(r["statut"] == BI.HORS and r["etape"] == "objectif", "besoin inconnu -> HORS étape objectif (abstention)")
check("candidats" not in r or not r.get("candidats"), "besoin inconnu -> aucun candidat fabriqué")

# ── 3) GROUNDING : fait corroboré + jugé -> PERSISTÉ ; le store reçoit RÉELLEMENT la valeur ──
s = FauxStore()
faits = [{"relation": "effet_calorique_materiau", "entite": "alliage NiTi", "valeur": "elastocalorique",
          "observations": [O("nature.com", "u1", "elastocalorique"), O("science.org", "u2", "elastocalorique")]}]
r = BI.boucle("rafraichir une piece", faits, persiste=s.persiste, lecteur=s)
check(len(r["faits"]["persistes"]) == 1, "fait de grounding corroboré+jugé -> PERSISTÉ")
check(s.d.get(("effet_calorique_materiau", "alliage niti")) == "elastocalorique",
      "la valeur est RÉELLEMENT écrite dans le store (writeback)")

# ── 4) GROUNDING contredisant le store connu -> RÉFUTÉ (jamais écrit) ──
s = FauxStore({("effet_calorique_materiau", "alliage niti"): "magnetocalorique"})
faits = [{"relation": "effet_calorique_materiau", "entite": "alliage NiTi", "valeur": "elastocalorique",
          "observations": [O("a.org", "u", "elastocalorique"), O("b.org", "u", "elastocalorique")]}]
r = BI.boucle("rafraichir une piece", faits, persiste=s.persiste, lecteur=s)
check(len(r["faits"]["refuses"]) == 1 and not r["faits"]["persistes"],
      "grounding contredisant le connu -> RÉFUTÉ, aucun persisté")
check(s.d[("effet_calorique_materiau", "alliage niti")] == "magnetocalorique", "fait connu non écrasé")

# ── 5) GROUNDING sous-corroboré (1 source) -> SUPPOSÉ (jamais persisté) ──
s = FauxStore()
faits = [{"relation": "r", "entite": "e", "valeur": "v", "observations": [O("a.org", "u", "v")]}]
r = BI.boucle("rafraichir une piece", faits, persiste=s.persiste, lecteur=s)
check(len(r["faits"]["supposes"]) == 1 and not s.d, "grounding 1 source -> SUPPOSÉ, store vide")

# ── 6) entrée grounding malformée -> ignorée (jamais devinée), le reste de la boucle fonctionne ──
s = FauxStore()
faits = [{"relation": "r"}, "pas un dict", {"relation": "r2", "entite": "e2", "valeur": "v2",
         "observations": [O("a.org", "u", "v2"), O("b.org", "u", "v2")]}]
r = BI.boucle("rafraichir une piece", faits, persiste=s.persiste, lecteur=s)
check(r["statut"] == BI.PROPOSE and len(r["faits"]["persistes"]) == 1,
      "entrées malformées ignorées, le fait valide est traité")

# ── 7) juge INJECTÉ négatif -> le grounding est réfuté même sans store (mécanisme réel externe) ──
s = FauxStore()
def juge_non(relation, entite, valeur):
    return A.Verdict("test", False, "rejeté par mécanisme externe")
faits = [{"relation": "r", "entite": "e", "valeur": "v",
          "observations": [O("a.org", "u", "v"), O("b.org", "u", "v")]}]
r = BI.boucle("rafraichir une piece", faits, juge=juge_non, persiste=s.persiste, lecteur=s)
check(len(r["faits"]["refuses"]) == 1 and not s.d, "juge externe négatif -> grounding réfuté, rien stocké")

# ── 8) note explicite sur la nature supposition/vérifié (pas de confusion possible) ──
r = BI.boucle("rafraichir une piece")
check("SUPPOSITION" in r["note"] and "survécu" in r["note"], "note = distinction claire supposition/fait vérifié")

print(f"\n=== valide_boucle_invention : {ok}/{ok + ko} ===")
sys.exit(0 if ko == 0 else 1)
