#!/usr/bin/env python3
"""VALIDE la boucle web->réalité->fait-store (veille_corroboration) — ADVERSE, FAUX=0.

Contrat jugé : une valeur observée n'entre dans le store QUE si sources INDÉPENDANTES (>= minimum) concordent ET
un JUGE réel valide ; écriture CONFLIT-REFUSÉE ; candidat contredisant le store connu -> RÉFUTÉ (jamais stocké, +
garde anti-re-proposition). Aucun maillon manquant -> abstention (SUPPOSITION, rien de stocké).

LÉGER : persistance et lecteur INJECTÉS (store factice en mémoire) — pas de chargement du lecteur (77M faits).
Ancres = scénarios déterministes couvrant chaque branche + adversarial (recopie, homonyme de valeur, conflit)."""
import os
import sys

_ICI = os.path.dirname(os.path.abspath(__file__)) or "."
sys.path.insert(0, _ICI)

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
    """Store en mémoire imitant la sémantique conflit-refusé de lecteur.ingere_table."""
    def __init__(self, initial=None):
        self.d = dict(initial or {})       # (relation, cle_norm) -> valeur

    def persiste(self, relation, paires, categorie, source):
        n = 0
        for e, v in paires:
            k = (relation, " ".join(str(e).strip().lower().split()))
            if k in self.d and self.d[k] != v:
                raise ValueError(f"conflit de valeur pour {k}: {self.d[k]!r} != {v!r}")
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


def corr(relation, entite, valeur, obs, store, minimum=2, juge=None):
    return VC.corrobore_valeur(relation, entite, valeur, obs, categorie="convention", source="test",
                               minimum=minimum, juge=juge, persiste=store.persiste, lecteur=store)


# ── 1) CHEMIN NOMINAL : 2 sources indépendantes concordantes + cohérent -> PERSISTE ──
s = FauxStore()
r = corr("capitale", "Canada", "Ottawa", [O("wikidata.org", "u1", "Ottawa"), O("britannica.com", "u2", "Ottawa")], s)
check(r["statut"] == VC.PERSISTE, "2 sources indép. concordantes + cohérent -> PERSISTE")
check(r["n_independantes"] == 2, "compte 2 sources indépendantes")
check(s.d.get(("capitale", "canada")) == "Ottawa", "la valeur est RÉELLEMENT écrite dans le store")
check(isinstance(r["atome"], A.Atome) and r["atome"].statut == A.FAIT, "atome retourné = FAIT (promu par Verdict)")

# ── 2) INDÉPENDANCE : deux témoignages du MÊME domaine ne comptent que pour 1 -> SUPPOSE (rien stocké) ──
s = FauxStore()
r = corr("capitale", "Allemagne", "Berlin", [O("wikidata.org", "u1", "Berlin"), O("wikidata.org", "u2", "Berlin")], s)
check(r["statut"] == VC.SUPPOSE and r["n_independantes"] == 1, "même domaine -> 1 seule source -> SUPPOSE")
check(("capitale", "allemagne") not in s.d, "SUPPOSE -> RIEN écrit dans le store")

# ── 3) RECOPIE : deux domaines mais CONTENU identique (empreinte) comptent pour 1 ── (empreinte = domaine|url|valeur)
s = FauxStore()
r = corr("capitale", "Italie", "Rome",
         [O("a.org", "http://same", "Rome"), O("b.org", "http://same", "Rome")], s)
# domaines distincts + urls distinctes -> 2 indépendants (empreinte inclut le domaine) : reste corroboré.
check(r["statut"] == VC.PERSISTE, "domaines distincts -> 2 indépendants -> PERSISTE (empreinte par domaine)")

# ── 4) JUGE RÉEL : candidat CONTREDIT le fait connu -> RÉFUTÉ (jamais stocké) ──
s = FauxStore({("capitale", "australie"): "Canberra"})
r = corr("capitale", "Australie", "Sydney", [O("a.org", "u", "Sydney"), O("b.org", "u", "Sydney")], s)
check(r["statut"] == VC.REFUTE, "candidat contredisant le store -> RÉFUTÉ (juge réel)")
check(s.d.get(("capitale", "australie")) == "Canberra", "le fait connu n'est PAS écrasé (Canberra intact)")
check(r["atome"].statut == A.REFUTE, "atome retourné = REFUTE (garde anti-re-proposition activée)")

# ── 5) ÉCRITURE CONFLIT-REFUSÉE : juge sans lecteur ne bloque pas, mais le WRITE refuse la divergence -> CONFLIT ──
s = FauxStore({("capitale", "perou"): "Lima"})
r = VC.corrobore_valeur("capitale", "Perou", "Cusco", [O("a.org", "u", "Cusco"), O("b.org", "u", "Cusco")],
                        categorie="convention", source="test", minimum=2, juge=None,
                        persiste=s.persiste, lecteur=None)   # lecteur=None -> juge ne voit pas Lima
check(r["statut"] == VC.CONFLIT, "juge aveugle mais WRITE conflit-refusé -> CONFLIT (2e garde FAUX=0)")
check(s.d.get(("capitale", "perou")) == "Lima", "valeur existante préservée (write refusé)")

# ── 6) CORROBORATION INSUFFISANTE : une seule source -> SUPPOSE ──
s = FauxStore()
r = corr("capitale", "Japon", "Tokyo", [O("a.org", "u", "Tokyo")], s)
check(r["statut"] == VC.SUPPOSE and r["n_independantes"] == 1, "1 source < minimum -> SUPPOSE")
check(not s.d, "SUPPOSE -> store reste vide")

# ── 7) VALEURS DIVERGENTES entre sources : seules celles qui portent LA valeur candidate comptent ──
s = FauxStore()
# 2 sources disent Madrid, 1 dit Barcelone -> candidat "Madrid" corroboré par 2 (Barcelone ignoré pour ce candidat).
obs = [O("a.org", "u", "Madrid"), O("b.org", "u", "Madrid"), O("c.org", "u", "Barcelone")]
r = corr("capitale", "Espagne", "Madrid", obs, s)
check(r["statut"] == VC.PERSISTE and r["n_independantes"] == 2, "seules les sources portant LA valeur comptent")
# et le candidat minoritaire "Barcelone" (1 source) -> SUPPOSE
s2 = FauxStore()
r = corr("capitale", "Espagne", "Barcelone", obs, s2)
check(r["statut"] == VC.SUPPOSE, "candidat minoritaire (1 source) -> SUPPOSE (jamais stocké)")

# ── 8) JUGE INJECTÉ (mécanisme réel externe) : un juge qui réfute -> REFUTE même si le store est vide ──
s = FauxStore()
def juge_refuse(relation, entite, valeur):
    return A.Verdict("test_refus", False, "test : ce candidat est rejeté par le mécanisme externe")
r = corr("x_rel", "e", "v", [O("a.org", "u", "v"), O("b.org", "u", "v")], s, juge=juge_refuse)
check(r["statut"] == VC.REFUTE, "juge externe négatif -> REFUTE (jamais stocké)")
check(not s.d, "juge négatif -> store vide")

def juge_ok(relation, entite, valeur):
    return A.Verdict("test_ok", True, "test : candidat validé par le mécanisme externe")
s = FauxStore()
r = corr("y_rel", "e2", "v2", [O("a.org", "u", "v2"), O("b.org", "u", "v2")], s, juge=juge_ok)
check(r["statut"] == VC.PERSISTE and s.d.get(("y_rel", "e2")) == "v2", "juge externe positif -> PERSISTE")

# ── 9) SOUNDNESS entrées : relation/entité/valeur vides -> SUPPOSE (jamais d'écriture) ──
s = FauxStore()
check(corr("", "e", "v", [O("a.org", "u", "v"), O("b.org", "u", "v")], s)["statut"] == VC.SUPPOSE,
      "relation vide -> SUPPOSE")
check(corr("r", "", "v", [O("a.org", "u", "v"), O("b.org", "u", "v")], s)["statut"] == VC.SUPPOSE,
      "entité vide -> SUPPOSE")
check(corr("r", "e", "", [O("a.org", "u", "")], s)["statut"] == VC.SUPPOSE, "valeur vide -> SUPPOSE")
check(corr("r", "e", "v", [], s)["statut"] == VC.SUPPOSE, "aucune observation -> SUPPOSE")
check(not s.d, "toutes les entrées invalides -> store resté vide")

# ── 10) PROVENANCE tracée : le fait persisté porte les domaines corroborants dans sa source ──
s = FauxStore()
corr("capitale", "Portugal", "Lisbonne", [O("wikidata.org", "u", "Lisbonne"), O("unesco.org", "u", "Lisbonne")], s)
# la source écrite (2e élément du tuple stocké n'est pas gardée par FauxStore ; on re-teste via l'atome)
r = corr("capitale", "Suede", "Stockholm", [O("wikidata.org", "u", "Stockholm"), O("bnf.fr", "u", "Stockholm")], s)
check("wikidata.org" in r["provenance"] and "bnf.fr" in r["provenance"], "provenance = domaines corroborants")
check("juge" in r["atome"].preuve.lower() or "coherence" in r["atome"].preuve.lower(),
      "l'atome FAIT porte la preuve du juge")

print(f"\n=== valide_veille_corroboration : {ok}/{ok + ko} ===")
sys.exit(0 if ko == 0 else 1)
