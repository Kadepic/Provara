"""VALIDE le pont moteur_invention (capacités) -> contrat d'atome (Phase 2 axe ① : atome universel), FAUX=0.

Test-clé : une INVENTION de capacité n'est JAMAIS servable comme fait (la revendication générale reste une
SUPPOSITION générative) ; seul le fait BORNÉ au spec (« la réalisation reproduit les n paires vérifiées ») est
attesté, avec le Verdict du juge réel (exécution + held-out). AMBIGU/BRIQUE_MANQUANTE/INCOHERENT -> abstention.
Autonome (pas de lecteur) : le juge est l'EXÉCUTEUR — la gate tourne dans la suite, elle ne dort pas.
"""
import atome as A
import invention_atomes as IA
import moteur_invention as MI

ok = 0
ko = 0


def check(cond, label):
    global ok, ko
    if cond:
        ok += 1
    else:
        ko += 1
        print(f"  FAIL: {label}")


# ── 1) INVENTION réelle (amplitude = max-min) -> (supposition générative, fait borné au spec) ──
EX = [([3, 1, 5], 4), ([2, 2], 0), ([10, 0, 3], 10)]
HELD = [([0, 9, 4], 9), ([7], 0), ([5, 5, 1], 4), ([2, 8], 6)]
verdict, sup, fait = IA.invente_capacite("amplitude", "xs", EX, HELD)
check(verdict.statut == MI.INVENTION, "amplitude -> INVENTION (précondition du test)")
check(sup is not None and sup.statut == A.SUPPOSITION and sup.regime == A.GENERATIF,
      "revendication générale -> SUPPOSITION régime GÉNÉRATIF")
n = len(EX) + len(HELD)
check(sup is not None and abs(sup.confiance - (n + 1.0) / (n + 2.0)) < 1e-9,
      "confiance = règle de succession (n+1)/(n+2) sur les n paires vérifiées")
check(sup is not None and sup.est_servable_comme_fait() is False,
      "l'invention générale n'est JAMAIS servable comme fait")
check(sup is not None and "SUPPOSITION" in sup.sert(), "sert() expose le statut supposition")

check(fait is not None and fait.statut == A.FAIT, "revendication bornée au spec -> FAIT")
check(fait is not None and fait.est_servable_comme_fait() is True, "le fait borné (spec vérifié) EST servable")
check(fait is not None and any("moteur_invention" in p for p in fait.provenance),
      "le fait porte le Verdict du juge réel (moteur_invention)")
check(fait is not None and fait.regime == "", "un fait ne porte pas de régime de supposition")
check(fait is not None and fait.portee.type == A.EPISTEMIQUE, "le fait est borné à son spec (portée épistémique)")
check(fait is not None and fait.est_servable_comme_fait({"portee": "un autre contexte"}) is False,
      "hors de sa portée-spec, le fait borné n'est PAS servable (fait hors portée = pas un fait ici)")

# ── 2) EXISTE_DEJA (somme) -> pas de supposition (rien de nouveau), fait borné attesté ──
verdict2, sup2, fait2 = IA.invente_capacite("somme_totale", "xs", [([1, 2, 3], 6), ([5], 5)],
                                            [([0, 4], 4), ([2, 2], 4)])
check(verdict2.statut == MI.EXISTE_DEJA, "somme_totale -> EXISTE_DEJA (précondition du test)")
check(sup2 is None, "EXISTE_DEJA : aucune supposition (rien de nouveau à inventer)")
check(fait2 is not None and fait2.statut == A.FAIT and fait2.est_servable_comme_fait() is True,
      "EXISTE_DEJA : le fait borné (la capacité existante reproduit le spec) est attesté")

# ── 3) INCOHERENT réel -> abstention totale ──
verdict3, sup3, fait3 = IA.invente_capacite("absurde", "xs", [([1, 2], 5)], [([1, 2], 9)])
check(verdict3.statut == MI.INCOHERENT, "spec contradictoire -> INCOHERENT (précondition)")
check(sup3 is None and fait3 is None, "INCOHERENT : (None, None) — jamais d'atome sur un spec contradictoire")

# ── 4) AMBIGU / BRIQUE_MANQUANTE (unitaires sur le pont) -> abstention ; la sonde reste dans le verdict ──
va = MI.Verdict(MI.AMBIGU, "cible_x", sonde=[1, 2], justification="≥2 réalisations distinctes")
check(IA.atome_capacite(va, EX, HELD) == (None, None), "AMBIGU : abstention (committer serait un faux)")
vb = MI.Verdict(MI.BRIQUE_MANQUANTE, "cible_y", justification="aucune recombinaison connue")
check(IA.atome_capacite(vb, EX, HELD) == (None, None), "BRIQUE_MANQUANTE : abstention (rien de vérifié)")
check(IA.atome_capacite(None, EX, HELD) == (None, None), "verdict None : abstention propre")

# ── 5) durci : spec VIDE -> rien d'attestable, même sur un verdict INVENTION fabriqué ──
vi = MI.Verdict(MI.INVENTION, "cible_z", par="max(x)-min(x)", justification="fabriqué pour le test")
check(IA.atome_capacite(vi, [], []) == (None, None), "0 paire vérifiée : aucun fait borné possible (abstention)")
check(IA.atome_capacite(vi, [], None) == (None, None), "held None + exemples vides : abstention propre")

print(f"\n=== valide_capacite_atomes : {ok}/{ok + ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
