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
# 2nd principe GÉNÉRALISÉ : séparation d'un composant dilué sous R·T·ln(1/x) (capture du CO₂ : x ≈ 4.2e-4 → ~19.3 kJ/mol).
check(statut({"type": "separation", "fraction_molaire": 4.2e-4, "energie_kJ_par_mol": 10, "t_K": 298.15}) == P.VIOLE,
      "capture CO₂ air 10 kJ/mol < plancher ~19.3 (x=420 ppm)")
check(loi({"type": "separation", "fraction_molaire": 4.2e-4, "energie_kJ_par_mol": 10, "t_K": 298.15}) == P.L3,
      "séparation diluée = travail minimal (L3)")
check(statut({"type": "separation", "fraction_molaire": 4.2e-4, "energie_kJ_par_mol": 0.0}) == P.VIOLE,
      "capture CO₂ à énergie NULLE depuis l'air : impossible")
# conservation de la QUANTITÉ DE MOUVEMENT : moteur sans réaction (EmDrive) et éjection supraluminique.
check(statut({"type": "propulsion", "poussee_nette": 1.0, "milieu_externe": False,
              "ejecte_masse_ou_rayonnement": False}) == P.VIOLE,
      "moteur sans réaction (poussée sans milieu ni éjection) -> VIOLE")
check(loi({"type": "propulsion", "poussee_nette": 1.0, "milieu_externe": False,
           "ejecte_masse_ou_rayonnement": False}) == P.L4, "réactionless = conservation de la quantité de mouvement (L4)")
check(statut({"type": "propulsion", "poussee_nette": 1.0, "ejecte_masse_ou_rayonnement": True,
              "vitesse_ejection_m_s": 3.0e8}) == P.VIOLE,
      "éjection à v > c -> VIOLE")
# efficacité lumineuse > 683 lm/W (maximum spectral à 555 nm).
check(statut({"type": "eclairage", "efficacite_lm_par_W": 800}) == P.VIOLE, "800 lm/W > 683 -> VIOLE")
check(loi({"type": "eclairage", "efficacite_lm_par_W": 800}) == P.L5, "efficacité lumineuse = L5")
# limite de Landauer : effacer un bit sous k·T·ln2 (~2.87e-21 J à 300 K).
check(statut({"type": "calcul", "energie_par_bit_efface_J": 1e-23, "t_K": 300}) == P.VIOLE,
      "1e-23 J/bit < Landauer ~2.87e-21 -> VIOLE")
check(loi({"type": "calcul", "energie_par_bit_efface_J": 1e-23, "t_K": 300}) == P.L6, "Landauer = L6")
check(statut({"type": "calcul", "energie_par_bit_efface_J": 0.0}) == P.VIOLE, "effacer un bit à énergie nulle -> VIOLE")
# limite de Shannon : débit > B·log2(1+S/N) (B=1 MHz, S/N=1000 -> capacité ~9.97 Mbit/s).
check(statut({"type": "communication", "debit_bits_par_s": 20e6, "bande_passante_Hz": 1e6,
              "rapport_signal_bruit": 1000}) == P.VIOLE, "20 Mbit/s > capacité ~9.97 -> VIOLE")
check(loi({"type": "communication", "debit_bits_par_s": 20e6, "bande_passante_Hz": 1e6,
           "rapport_signal_bruit": 1000}) == P.L7, "capacité de canal = Shannon (L7)")
check(statut({"type": "communication", "debit_bits_par_s": 1e6, "bande_passante_Hz": 0,
              "rapport_signal_bruit": 1000}) == P.VIOLE, "débit > 0 à bande passante NULLE -> VIOLE")
# limite de Shockley-Queisser : jonction simple STANDARD sous 1 soleil > 33,7 %.
check(statut({"type": "captation_solaire", "rendement": 0.50, "nb_jonctions": 1, "concentration_solaire": 1,
              "bilan_detaille_standard": True}) == P.VIOLE, "PV 50% mono-jonction standard 1 soleil > SQ -> VIOLE")
check(loi({"type": "captation_solaire", "rendement": 0.50, "nb_jonctions": 1, "concentration_solaire": 1,
           "bilan_detaille_standard": True}) == P.L8, "Shockley-Queisser = L8")
# plafond ABSOLU (exergie du rayonnement) : > Carnot solaire (~94,8 %) quelle que soit l'architecture.
check(statut({"type": "captation_solaire", "rendement": 1.0}) == P.VIOLE, "PV 100% > plafond thermo -> VIOLE")
check(loi({"type": "captation_solaire", "rendement": 1.0}) == P.L8, "plafond thermo solaire = L8")
# électrolyse : tension SOUS E_rev (anode standard) + énergie totale SOUS le PCS de H₂.
check(statut({"type": "electrolyse", "tension_cellule_V": 0.9, "t_K": 298.15,
              "reaction_anodique_standard": True}) == P.VIOLE, "cellule 0,9 V (anode std, 25 °C) < E_rev 1,23 -> VIOLE")
check(loi({"type": "electrolyse", "tension_cellule_V": 0.9, "t_K": 298.15,
           "reaction_anodique_standard": True}) == P.L9, "électrolyse (tension < E_rev) = L9")
check(statut({"type": "electrolyse", "energie_kJ_par_mol_H2": 150}) == P.VIOLE, "150 kJ/mol H₂ < PCS 285,8 -> VIOLE")
check(loi({"type": "electrolyse", "energie_kJ_par_mol_H2": 150}) == P.L9, "sous le PCS de H₂ = L9")
# vol stationnaire : puissance sous la puissance induite idéale (théorie de la quantité de mouvement).
check(statut({"type": "sustentation", "masse_kg": 2, "aire_rotor_m2": 0.05, "puissance_W": 5}) == P.VIOLE,
      "drone 2 kg 0,05 m² à 5 W < P induite (~248 W) -> VIOLE")
check(loi({"type": "sustentation", "masse_kg": 2, "aire_rotor_m2": 0.05, "puissance_W": 5}) == P.L10,
      "vol stationnaire = L10")
check(statut({"type": "sustentation", "poussee_N": 981, "aire_rotor_m2": 0.1, "puissance_W": 50}) == P.VIOLE,
      "plateforme 100 kg 0,1 m² à 50 W < P induite (~62 kW) -> VIOLE")
# limite de diffraction d'Abbe : résolution sous λ/2NA (conventionnel) + NA > n.
check(statut({"type": "imagerie_optique", "longueur_onde_nm": 550, "ouverture_numerique": 1.4,
              "resolution_nm": 50}) == P.VIOLE, "50 nm < Abbe ~196 (champ lointain conventionnel) -> VIOLE")
check(loi({"type": "imagerie_optique", "longueur_onde_nm": 550, "ouverture_numerique": 1.4,
           "resolution_nm": 50}) == P.L11, "diffraction d'Abbe = L11")
check(statut({"type": "imagerie_optique", "ouverture_numerique": 1.7, "indice_milieu": 1.0,
              "longueur_onde_nm": 550, "resolution_nm": 300}) == P.VIOLE, "NA 1,7 dans l'air (n=1) -> VIOLE")
check(loi({"type": "imagerie_optique", "ouverture_numerique": 1.7, "indice_milieu": 1.0}) == P.L11, "NA > n = L11")
# limite de Betz : coefficient de puissance ou puissance extraite au-dessus de 16/27 (rotor ouvert).
check(statut({"type": "eolienne", "coefficient_puissance": 0.7}) == P.VIOLE, "Cp 0,7 > Betz 0,593 -> VIOLE")
check(loi({"type": "eolienne", "coefficient_puissance": 0.7}) == P.L12, "limite de Betz = L12")
check(statut({"type": "eolienne", "puissance_W": 50000, "aire_balayee_m2": 100,
              "vitesse_vent_m_s": 10}) == P.VIOLE, "50 kW > Betz ~36,3 kW (100 m², 10 m/s) -> VIOLE")
# équation de Tsiolkovski : Δv au-dessus de ve·ln(rapport de masse).
check(statut({"type": "fusee", "delta_v_m_s": 30000, "vitesse_ejection_m_s": 4500,
              "rapport_masse": 20}) == P.VIOLE, "30 km/s > Tsiolkovski ~13,5 km/s -> VIOLE")
check(loi({"type": "fusee", "delta_v_m_s": 30000, "vitesse_ejection_m_s": 4500,
           "rapport_masse": 20}) == P.L13, "Tsiolkovski = L13")
check(statut({"type": "fusee", "delta_v_m_s": 5000, "vitesse_ejection_m_s": 4500,
              "rapport_masse": 1}) == P.VIOLE, "Δv > 0 sans ergols (rapport de masse 1) -> VIOLE")

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
    # séparations RÉELLES au-dessus du plancher R·T·ln(1/x).
    {"type": "separation", "fraction_molaire": 4.2e-4, "energie_kJ_par_mol": 230, "t_K": 298.15},  # DAC solide réel (air)
    {"type": "separation", "fraction_molaire": 0.12, "energie_kJ_par_mol": 120, "t_K": 298.15},    # amines aux fumées (x élevé)
    {"type": "separation", "fraction_molaire": 4.2e-4, "energie_kJ_par_mol": 25, "t_K": 298.15},   # juste au-dessus du plancher ~19.3
    {"type": "separation", "fraction_molaire": 4.2e-4},                                # sans énergie déclarée : indéterminé, PAS un faux positif
    # propulsions RÉELLES : toujours un milieu OU une éjection -> jamais réactionless.
    {"type": "propulsion", "poussee_nette": 1e5, "ejecte_masse_ou_rayonnement": True,
     "vitesse_ejection_m_s": 4500},                                                    # fusée chimique (éjecte masse)
    {"type": "propulsion", "poussee_nette": 0.1, "ejecte_masse_ou_rayonnement": True,
     "vitesse_ejection_m_s": 30000},                                                   # moteur ionique (Isp élevé)
    {"type": "propulsion", "poussee_nette": 0.01, "milieu_externe": True},             # voile solaire (rayonnement externe)
    {"type": "propulsion", "poussee_nette": 5e4, "milieu_externe": True},              # turboréacteur (pousse l'air)
    {"type": "propulsion", "poussee_nette": 1e-6, "ejecte_masse_ou_rayonnement": True,
     "vitesse_ejection_m_s": 2.99e8},                                                  # fusée à photons (v proche de c, < c)
    {"type": "propulsion"},                                                            # spec insuffisante : PAS un faux positif
    # éclairages RÉELS : sous le plafond de 683 lm/W.
    {"type": "eclairage", "efficacite_lm_par_W": 150},                                 # LED blanche courante
    {"type": "eclairage", "efficacite_lm_par_W": 330},                                 # LED de labo (record) < 683
    {"type": "eclairage", "efficacite_lm_par_W": 683},                                 # AU plafond (limite, ok)
    {"type": "eclairage", "efficacite_lm_par_W": 15},                                  # incandescence
    {"type": "eclairage"},                                                             # sans efficacité : PAS un faux positif
    # calculs RÉELS : bien AU-DESSUS de la limite de Landauer.
    {"type": "calcul", "energie_par_bit_efface_J": 1e-17, "t_K": 300},                 # CMOS actuel (~10^4× Landauer)
    {"type": "calcul", "energie_par_bit_efface_J": 1e-18, "t_K": 300},                 # sous-seuil / basse tension
    {"type": "calcul", "energie_par_bit_efface_J": 2.9e-21, "t_K": 300},               # juste au-dessus de Landauer
    {"type": "calcul"},                                                                # sans énergie déclarée : PAS un faux positif
    # communications RÉELLES : sous la capacité de Shannon.
    {"type": "communication", "debit_bits_par_s": 8e6, "bande_passante_Hz": 1e6, "rapport_signal_bruit": 1000},  # sous capacité
    {"type": "communication", "debit_bits_par_s": 9.9e6, "bande_passante_Hz": 1e6, "rapport_signal_bruit": 1000}, # proche capacité
    {"type": "communication", "debit_bits_par_s": 1e6},                                # sans B/SNR : indéterminé, PAS un faux positif
    # captations solaires RÉELLES : sous les limites.
    {"type": "captation_solaire", "rendement": 0.27, "nb_jonctions": 1, "concentration_solaire": 1,
     "bilan_detaille_standard": True},                                                 # silicium mono record (< SQ 33,7)
    {"type": "captation_solaire", "rendement": 0.337, "nb_jonctions": 1, "concentration_solaire": 1,
     "bilan_detaille_standard": True},                                                 # AU plafond SQ (limite, ok)
    {"type": "captation_solaire", "rendement": 0.47, "nb_jonctions": 3, "concentration_solaire": 500},  # multi-jonction concentrée (record ~47%)
    {"type": "captation_solaire", "rendement": 0.42, "nb_jonctions": 1, "concentration_solaire": 1},    # MEG mono-jonction (dépasse SQ légitimement : pas de flag standard) -> PAS un faux positif
    {"type": "captation_solaire", "rendement": 0.40, "nb_jonctions": 1, "concentration_solaire": 1000},  # mono-jonction CONCENTRÉE (SQ relevée) -> PAS un faux positif
    {"type": "captation_solaire", "rendement": 0.86},                                  # solaire idéal (< plafond absolu) -> PAS un faux positif
    {"type": "captation_solaire"},                                                     # sans rendement : indéterminé, PAS un faux positif
    # électrolyses RÉELLES : au-dessus des planchers.
    {"type": "electrolyse", "tension_cellule_V": 1.9, "t_K": 353, "reaction_anodique_standard": True},   # alcaline (surtension normale)
    {"type": "electrolyse", "tension_cellule_V": 1.8, "t_K": 343, "reaction_anodique_standard": True},    # PEM
    {"type": "electrolyse", "tension_cellule_V": 1.3, "t_K": 1073, "reaction_anodique_standard": True},   # SOEC haute T (E_rev abaissée)
    {"type": "electrolyse", "tension_cellule_V": 0.8, "t_K": 298.15},                  # assistée sacrificielle (pas d'anode std) -> PAS un faux positif
    {"type": "electrolyse", "energie_kJ_par_mol_H2": 400},                             # thermochimique (> ΔH)
    {"type": "electrolyse", "energie_kJ_par_mol_H2": 285.8},                           # AU plancher ΔH (limite, ok)
    {"type": "electrolyse"},                                                           # spec insuffisante -> PAS un faux positif
    # sustentations RÉELLES : au-dessus de la puissance induite idéale.
    {"type": "sustentation", "masse_kg": 2000, "aire_rotor_m2": 113, "puissance_W": 180000},  # hélico grand rotor (P_ideal ~165 kW)
    {"type": "sustentation", "masse_kg": 2, "aire_rotor_m2": 0.05, "puissance_W": 300},        # drone petit disque (inefficace mais réel)
    {"type": "sustentation", "masse_kg": 2, "aire_rotor_m2": 0.5, "puissance_W": 100},         # drone grand disque lent (levier aire)
    {"type": "sustentation", "poussee_N": 19613, "aire_rotor_m2": 113, "puissance_W": 170000}, # au-dessus de P_ideal (poussée donnée)
    {"type": "sustentation", "masse_kg": 2},                                                   # sans P/A : indéterminé -> PAS un faux positif
    {"type": "sustentation"},                                                                  # vide -> PAS un faux positif
    # imageries optiques RÉELLES : au-dessus de la limite d'Abbe, ou super-résolues (exemptées), NA ≤ n.
    {"type": "imagerie_optique", "longueur_onde_nm": 550, "ouverture_numerique": 1.4, "indice_milieu": 1.5, "resolution_nm": 200},  # optique standard (> Abbe ~196)
    {"type": "imagerie_optique", "longueur_onde_nm": 550, "ouverture_numerique": 1.4, "indice_milieu": 1.5, "resolution_nm": 197},  # AU Abbe ~196,4 (limite, ok)
    {"type": "imagerie_optique", "longueur_onde_nm": 250, "ouverture_numerique": 1.0, "indice_milieu": 1.0, "resolution_nm": 130},  # UV (λ court), Abbe ~125
    {"type": "imagerie_optique", "longueur_onde_nm": 550, "ouverture_numerique": 1.4, "indice_milieu": 1.5, "resolution_nm": 30, "super_resolution": True},   # STED (exempté)
    {"type": "imagerie_optique", "longueur_onde_nm": 550, "ouverture_numerique": 1.4, "indice_milieu": 1.5, "resolution_nm": 20, "super_resolution": True},   # PALM/STORM (exempté)
    {"type": "imagerie_optique", "longueur_onde_nm": 550, "ouverture_numerique": 0.9, "resolution_nm": 50, "super_resolution": True},   # NSOM champ proche (exempté)
    {"type": "imagerie_optique", "ouverture_numerique": 1.4, "indice_milieu": 1.5},   # NA < n, sans résolution : PAS un faux positif
    {"type": "imagerie_optique"},                                                     # vide -> PAS un faux positif
    # éoliennes RÉELLES : sous la limite de Betz (ou carénée, exemptée).
    {"type": "eolienne", "coefficient_puissance": 0.45},                              # turbine moderne (< Betz)
    {"type": "eolienne", "coefficient_puissance": 0.592},                             # juste SOUS Betz (16/27 ~0,5926) (limite, ok)
    {"type": "eolienne", "puissance_W": 27000, "aire_balayee_m2": 100, "vitesse_vent_m_s": 10},  # Cp ~0,44 (< Betz ~36,3 kW)
    {"type": "eolienne", "coefficient_puissance": 0.7, "avec_diffuseur": True},       # carénée : Cp>Betz par aire rotor -> PAS un faux positif
    {"type": "eolienne"},                                                             # vide -> PAS un faux positif
    # propulsions spatiales RÉELLES : sous le Δv de Tsiolkovski (ou momentum externe non jugé).
    {"type": "fusee", "delta_v_m_s": 13000, "vitesse_ejection_m_s": 4500, "rapport_masse": 20},   # chimique (max ~13481)
    {"type": "fusee", "delta_v_m_s": 12000, "vitesse_ejection_m_s": 30000, "rapport_masse": 1.5}, # ionique (max ~12164)
    {"type": "fusee", "delta_v_m_s": 18000, "vitesse_ejection_m_s": 4500, "rapport_masse": 60},   # étagé (max ~18424)
    {"type": "fusee", "delta_v_m_s": 13480, "vitesse_ejection_m_s": 4500, "rapport_masse": 20},   # AU max ~13480,8 (limite, ok)
    {"type": "fusee", "vitesse_ejection_m_s": 9000},                                  # sans Δv/rapport : PAS un faux positif
    {"type": "fusee"},                                                                # vide (voile solaire, momentum externe) -> PAS un faux positif
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
