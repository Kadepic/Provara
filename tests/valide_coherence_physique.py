"""
VALIDE coherence_physique.py — held-out ADVERSE. Soundness : on ne déclare VIOLE que sur une contradiction
CERTAINE de la spec ; un dispositif RÉEL/légal ne doit JAMAIS être déclaré impossible (faux positif INTERDIT).
On n'affirme jamais « ça marche » (COHERENT_BORNE = pas une preuve). Aucun cas ici n'est dans le __main__.
"""
import coherence_physique as P

ok = 0
ko = 0


def check(cond, label):
    global ok, ko
    if cond:
        ok += 1
    else:
        ko += 1
        print(f"  FAIL: {label}")


def statut(spec):
    return P.juge_dispositif(spec)[0]


def loi(spec):
    return P.juge_dispositif(spec)[2]


# 1) VIOLATIONS CERTAINES -> VIOLE (avec la bonne loi).
# 1er principe : over-unity.
check(statut({"type": "conversion", "rendement": 1.2}) == P.VIOLE, "conversion rendement>1")
check(loi({"type": "conversion", "rendement": 1.2}) == P.L1, "over-unity = 1er principe")
check(statut({"type": "conversion", "puissance_entree": 100, "puissance_utile": 150}) == P.VIOLE,
      "utile>entree")
check(statut({"type": "moteur_thermique", "rendement": 1.5}) == P.VIOLE, "moteur rendement>1")
check(statut({"type": "conversion", "mouvement_perpetuel": True}) == P.VIOLE, "mouvement perpétuel")
check(statut({"type": "conversion", "energie_libre": True}) == P.VIOLE, "énergie libre")

# 2nd principe : système fermé qui « refroidit » (cas Coolzy).
check(statut({"type": "refroidissement", "systeme_ferme": True, "puissance_entree": 45}) == P.VIOLE,
      "Coolzy : refroidissement système fermé")
check(loi({"type": "refroidissement", "systeme_ferme": True}) == P.L2, "Coolzy = 2nd principe")
check(statut({"type": "refroidissement", "rejette_chaleur_exterieur": False}) == P.VIOLE,
      "refroidissement sans rejet extérieur")

# 2nd principe : Carnot moteur.
check(statut({"type": "moteur_thermique", "rendement": 0.70, "t_chaud_K": 800, "t_froid_K": 300}) == P.VIOLE,
      "rendement 0.70 > Carnot 0.625")
check(loi({"type": "moteur_thermique", "rendement": 0.70, "t_chaud_K": 800, "t_froid_K": 300}) == P.L2,
      "Carnot = 2nd principe")
check(statut({"type": "moteur_thermique", "t_chaud_K": 300, "t_froid_K": 300}) == P.VIOLE,
      "Tc>=Th : aucun travail")
# 2nd principe : COP de Carnot pompe à chaleur.
check(statut({"type": "pompe_chaleur", "cop": 25, "t_chaud_K": 293, "t_froid_K": 278}) == P.VIOLE,
      "COP 25 > COP Carnot ~19.5")
# 2nd principe : dessalement SOUS le travail minimal de séparation (π ≈ 27 bar → ~0.75 kWh/m³ pour l'eau de mer).
check(statut({"type": "dessalement", "energie_kWh_par_m3": 0.3, "osmose_pression_bar": 27}) == P.VIOLE,
      "dessalement 0.3 kWh/m³ < plancher 0.75 (π 27 bar)")
check(loi({"type": "dessalement", "energie_kWh_par_m3": 0.3, "osmose_pression_bar": 27}) == P.L3,
      "travail minimal de séparation = 2nd principe (L3)")
check(statut({"type": "dessalement", "energie_kWh_par_m3": 0.0, "osmose_pression_bar": 27}) == P.VIOLE,
      "dessalement à énergie NULLE d'une saumure : impossible")
# plancher calculé depuis la concentration (i·C·R·T) : c=0.6 mol/L, i=2, 298 K → π ≈ 29.7 bar → ~0.83 kWh/m³.
check(statut({"type": "dessalement", "energie_kWh_par_m3": 0.5, "concentration_mol_par_L": 0.6,
              "facteur_vant_hoff": 2, "t_K": 298.15}) == P.VIOLE,
      "dessalement 0.5 kWh/m³ < plancher calculé ~0.83 (van 't Hoff)")

# 2) DISPOSITIFS RÉELS / LÉGAUX -> JAMAIS VIOLE (cœur soundness : pas de faux positif).
reels = [
    {"type": "refroidissement", "rejette_chaleur_exterieur": True, "puissance_entree": 800, "cop": 3},  # clim normale
    {"type": "moteur_thermique", "rendement": 0.40, "t_chaud_K": 800, "t_froid_K": 300},  # < Carnot 0.625
    {"type": "moteur_thermique", "rendement": 0.625, "t_chaud_K": 800, "t_froid_K": 300},  # = Carnot (limite, ok)
    {"type": "conversion", "rendement": 0.95},                                              # rendement < 1
    {"type": "conversion", "rendement": 1.0},                                               # = 1 (limite idéale)
    {"type": "conversion", "puissance_entree": 100, "puissance_utile": 90},                 # pertes normales
    {"type": "pompe_chaleur", "cop": 5, "t_chaud_K": 293, "t_froid_K": 278},                # COP réaliste < Carnot
    {"type": "pompe_chaleur", "cop": 12, "t_chaud_K": 293, "t_froid_K": 278},               # élevé mais < Carnot ~19.5
    # source externe DÉCLARÉE : utile > mesuré n'est plus une création nette.
    {"type": "conversion", "rendement": 3.0, "source_energie_externe": True},
    # dessalements RÉELS : au-DESSUS du plancher thermodynamique (osmose inverse, distillation).
    {"type": "dessalement", "energie_kWh_par_m3": 3.5, "osmose_pression_bar": 27},   # osmose inverse mer réelle
    {"type": "dessalement", "energie_kWh_par_m3": 10.0, "osmose_pression_bar": 27},  # distillation thermique
    {"type": "dessalement", "energie_kWh_par_m3": 0.75, "osmose_pression_bar": 27},  # AU plancher (limite, ok)
    {"type": "dessalement", "energie_kWh_par_m3": 1.0, "concentration_mol_par_L": 0.6,
     "facteur_vant_hoff": 2, "t_K": 298.15},                                          # > plancher calculé ~0.83
    {"type": "dessalement", "energie_kWh_par_m3": 2.0},                               # sans base π : indéterminé, PAS un faux positif
]
for sp in reels:
    check(statut(sp) != P.VIOLE, f"dispositif réel NON déclaré impossible: {sp}")
    check(statut(sp) == P.COHERENT_BORNE, f"dispositif réel -> COHERENT_BORNE: {sp}")

# 3) COHERENT_BORNE n'est PAS une preuve de fonctionnement (message honnête).
st, r, _ = P.juge_dispositif({"type": "conversion", "rendement": 0.5})
check(st == P.COHERENT_BORNE and "PAS une preuve" in r, "COHERENT_BORNE dit : pas une preuve")

# 4) Spec insuffisante / type inconnu -> HORS (jamais un jugement deviné).
check(statut({"type": "teleportation"}) == P.HORS, "type inconnu -> HORS")
check(statut({}) == P.HORS, "spec vide -> HORS")
check(statut("Coolzy") == P.HORS, "spec non-dict -> HORS")
check(statut(None) == P.HORS, "None -> HORS")
# refroidissement sans info de rejet -> on ne peut PAS trancher la violation -> pas VIOLE.
check(statut({"type": "refroidissement", "puissance_entree": 45}) != P.VIOLE,
      "refroidissement sans info rejet -> pas de faux positif")

# 5) Carnot : booléens ne sont pas des nombres (robustesse de _nb).
check(P._nb(True) is False and P._nb(5) is True, "_nb rejette les booléens")

# 6) DÉTERMINISME.
sp = {"type": "moteur_thermique", "rendement": 0.70, "t_chaud_K": 800, "t_froid_K": 300}
check(P.juge_dispositif(sp) == P.juge_dispositif(sp), "déterminisme")

# 7) explique() lisible pour les 3 statuts.
check("IMPOSSIBLE" in P.explique(P.VIOLE, "x", P.L1), "explique VIOLE")
check("COHÉRENT" in P.explique(P.COHERENT_BORNE, "x", None), "explique COHERENT")
check("[HORS]" in P.explique(P.HORS, "x", None), "explique HORS")

print(f"\n=== valide_coherence_physique : {ok}/{ok+ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
