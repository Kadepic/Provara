"""VALIDE invention_atomes.py — le moteur d'invention rend des ATOMES au bon statut (contrat d'atome), FAUX=0.

Test-clé : une invention (dérivable généralisée / générative physique) n'est JAMAIS servable comme fait ; seul le
TÉMOIN d'une instance re-vérifiée est un FAIT (avec Verdict = graphe_monde.verifie_chemin). ⚠ charge le lecteur.
"""
import atome as A
import invention_atomes as IA
import substrat_reel as SR
import substrat_physique as SP

ok = 0
ko = 0


def check(cond, label):
    global ok, ko
    if cond:
        ok += 1
    else:
        ko += 1
        print(f"  FAIL: {label}")


# ── 1) attribut composite DÉRIVABLE du réel -> (supposition dérivable, fait par instance) ──
sup, fait = IA.invente_attribut("pays", "population_ville", budget=200)
check(sup is not None and sup.statut == A.SUPPOSITION and sup.regime == A.DERIVABLE, "généralisation -> SUPPOSITION régime DÉRIVABLE")
check(0.0 < sup.confiance < 1.0, "supposition dérivable : confiance dans ]0,1[ (= couverture)")
check(sup.est_servable_comme_fait() is False, "supposition dérivable JAMAIS servable comme fait")
check("SUPPOSITION" in sup.sert(), "sert() expose le statut supposition")

check(fait is not None and fait.statut == A.FAIT, "témoin d'instance -> FAIT")
check(fait.est_servable_comme_fait() is True, "le témoin re-vérifié EST servable comme fait")
check(any("verifie_chemin" in p for p in fait.provenance), "le fait porte le Verdict du juge (graphe_monde.verifie_chemin)")
check(fait.regime == "", "un fait ne porte pas de régime de supposition")

# ── 2) invention GÉNÉRATIVE physique (substrat_physique) -> SUPPOSITION générative ──
concept = None
for e, s in [("pression", "lumiere"), ("chaleur", "lumiere"), ("son", "mouvement"), ("mouvement", "son")]:
    c = SP.examine(e, s)
    if c.statut == SP.INVENTION:
        concept = c
        break
check(concept is not None, "substrat_physique fournit au moins une INVENTION générative")
gen = IA.atome_generatif(concept)
check(gen.statut == A.SUPPOSITION and gen.regime == A.GENERATIF, "chaîne de transduction nouvelle -> SUPPOSITION régime GÉNÉRATIF")
check(0.0 < gen.confiance < 1.0, "supposition générative : plausibilité dans ]0,1[")
check(gen.est_servable_comme_fait() is False, "invention générative JAMAIS servable comme fait")
check(gen.portee.type == A.DOMAINE, "portée = domaine physique")

# ── 3) cohérence : rien à servir sur EXISTE_DEJA / BRIQUE_MANQUANTE / None ──
check(IA.atome_derivable(None) is None, "atome_derivable(None) -> None")
dej = SR.derive_attribut("pays", "capitale", budget=100)      # attribut direct -> EXISTE_DEJA
check(dej.statut == SR.EXISTE_DEJA and IA.atome_derivable(dej) is None and IA.atome_temoin(dej) is None,
      "EXISTE_DEJA -> pas d'atome d'invention")
connu = SP.examine("son", "lumiere")                           # dispositif connu
check(connu.statut == SP.EXISTE_DEJA and IA.atome_generatif(connu) is None, "dispositif connu -> pas d'atome génératif")

# ── 4) FAUX=0 transverse : une supposition du moteur ne se promeut pas en fait sans Verdict ──
def leve(fn, *a, **k):
    try:
        fn(*a, **k); return False
    except ValueError:
        return True
    except Exception:
        return False
check(leve(A.promeut, gen, True), "supposition générative : promotion par bool nu -> ValueError (Verdict requis)")
promu = A.promeut(gen, A.Verdict("coherence_physique", True, "dispositif jugé cohérent et faisable"))
check(promu.statut == A.FAIT, "supposition générative promue en FAIT SEULEMENT via Verdict d'un juge réel")

print(f"\n=== valide_invention_atomes : {ok}/{ok + ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
