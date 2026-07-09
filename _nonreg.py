#!/usr/bin/env python3
"""
NON-RÉGRESSION INCRÉMENTALE + PARALLÈLE (le runner standard, rapide ET sound).

Idée (façon build-system / Bazel) : un validateur est DÉTERMINISTE pour un code donné. On hash le CONTENU de
sa CLÔTURE D'IMPORTS (lui + tous les modules-projet qu'il importe, transitivement). Si ce fingerprint n'a pas
changé depuis le dernier PASS mémorisé -> on REJOUE le verdict depuis le cache, INSTANTANÉMENT. Sinon on relance.
Les validateurs réellement impactés par un fichier modifié re-tournent ; les autres sont gratuits.

SOUNDNESS : le fingerprint couvre TOUTE la clôture d'imports statique (import / from import). Tout changement
d'un fichier de la clôture change le hash -> re-run. Garde-fou : si un validateur fait un import DYNAMIQUE local
non résolu, il est marqué "toujours relancer" (jamais de faux cache). Un cache n'est posé que pour un PASS (un
FAIL n'est jamais mémorisé -> toujours re-tenté).

Parallélisme borné (défaut 8, ulimit 1,5 Go/process), ordre LONGEST-FIRST (profil de durées) pour minimiser la
traîne. Usage : python3 _nonreg.py [--jobs N] [--full] [--no-cache]
"""
from __future__ import annotations

import ast
import concurrent.futures as cf
import hashlib
import json
import os
import subprocess
import sys
import time

HARN = os.path.dirname(os.path.abspath(__file__))
# PORTAGE Provara : les validateurs vivent dans tests/ (et interface/valide_interface.py dans interface/), pas à
# la racine comme dans le repo d'origine. `_chemin()` résout un nom de validateur vers son chemin réel relatif
# à HARN ; `TESTS` est le dossier des `valide_*.py`. Le pipeline importe depuis src/ + interface/ + ingestion/.
TESTS = os.path.join(HARN, "tests")
# tests/ EN TÊTE : les validateurs importent leur helper `valide_commun` et parfois un validateur frère
# (valide_invention…) comme module — tous dans tests/. Puis les modules du pipeline (src/interface/ingestion).
_SRCPATH = os.pathsep.join(os.path.join(HARN, d) for d in ("tests", "src", "interface", "ingestion"))


def _chemin(f):
    """Chemin d'un validateur RELATIF à HARN : 'interface/valide_interface.py' tel quel, sinon 'tests/<f>'."""
    if "/" in f or os.sep in f:
        return f                                   # déjà un chemin (ex. interface/valide_interface.py)
    cand = os.path.join("tests", f)
    return cand if os.path.exists(os.path.join(HARN, cand)) else f


def _env_pipeline(base=None):
    """Env avec le PYTHONPATH du pipeline (src+interface+ingestion) — sinon les validateurs de tests/ ne trouvent
    pas repond/conversation/ia. Préserve un PYTHONPATH éventuel existant."""
    e = dict(base if base is not None else os.environ)
    e["PYTHONPATH"] = _SRCPATH + (os.pathsep + e["PYTHONPATH"] if e.get("PYTHONPATH") else "")
    e.setdefault("VERAX_ROOT", HARN)            # validateurs qui cherchent src/ia.py etc. relatif à la racine
    return e


CACHE = os.path.join(HARN, ".nonreg_cache.json")
DUREES = "/tmp/nrp_durees.txt"
TIMEOUT = 1500   # valide_meta ~428s SOLO mais le démarrage (chargement de ~227 tables lecteur + préchauffe 59
                 # familles) GRANDIT à chaque lot d'ingestion -> sous contention 6-jobs il a dépassé 1000s au lot 4
                 # (faux TIMEOUT, valide_meta passe 4/4 solo). Marge portée à 1500s. NB scaling : si ça redéborde,
                 # rendre le chargement du lecteur paresseux plutôt que de monter indéfiniment ce mou.
UNIVERSELS = ("garde_ressources",)   # deps de fait inclus partout par prudence


def liste_validateurs():
    vagues = [f"valide_vague{v}.py" for v in range(4, 52)]
    extras = ["valide_routage_strategie.py", "valide_meta.py", "valide_completude.py",
              "valide_consolidation.py", "valide_mesure.py", "valide_assistant.py",
              "valide_budget.py", "valide_demande.py", "valide_auto_synthese.py",
              "valide_surface_ia.py",                    # gate statique : surface P2 de ia.py (alias + attributs)
              "valide_audit_ancres.py"]                  # méta : couverture d'ancrage du store (diagnostic sound)
    invention = ["valide_invention_gap.py", "valide_chercheur_invention.py",
                 "valide_bibliotheque_invention.py", "valide_rapport_invention.py"]
    domaines = ["valide_audit_code.py", "valide_chimie.py", "valide_coherence_physique.py",
                "valide_besoin.py",
                "valide_transfert.py",
                "valide_veille.py",
                "valide_veille_corroboration.py",
                "valide_boucle_invention.py",
                "valide_population_pays.py",
                "valide_worldbank_eco.py",
                "valide_physique.py", "valide_capacites.py",
                "valide_scrutin.py",
                "valide_strategie_jeux.py",
                "valide_jeux_appliques.py",
                "valide_budget_personnel.py",
                "valide_biostatistique.py",
                "valide_psychometrie.py",
                "valide_hierarchie_normes.py",
                "valide_conjugaison.py",
                "valide_cartographie.py",
                "valide_mesures_sociales.py",
                "valide_citoyennete.py",
                "valide_conservation_aliments.py",
                "valide_retraite.py",
                "valide_externalites.py",
                "valide_cycles_economiques.py",
                "valide_commerce_international.py",
                "valide_rhetorique.py",
                "valide_journalisme_deontologie.py",
                "valide_marketing_mecanismes.py",
                "valide_propagande.py",
                "valide_bibliotheconomie.py",
                "valide_cardiologie.py",
                "valide_urgence_medicale.py",
                "valide_medecines_alternatives.py",
                "valide_maths_financieres.py",
                "valide_gestion_risque.py",
                "valide_comptabilite.py",
                "valide_inflation.py",
                "valide_pib.py",
                "valide_chomage.py",
                "valide_posologie.py",
                "valide_essais_cliniques.py",
                "valide_biomecanique.py",
                "valide_entrainement.py",
                "valide_demographie.py",
                "valide_audiologie.py",
                "valide_croissance_bacterienne.py",
                "valide_transport_membranaire.py",
                "valide_aerodynamique.py",
                "valide_maritime.py",
                "valide_automobile.py",
                "valide_logistique.py",
                "valide_toxicologie.py",
                "valide_topographie_arpentage.py",
                "valide_navigation.py",
                "valide_coordonnees.py",
                "valide_villes_coordonnees.py",
                "valide_assistant_nl.py",
                "valide_editeur.py",
                "valide_hydrologie.py",
                "valide_glaciologie.py",
                "valide_pedologie.py",
                "valide_teledetection.py",
                "valide_energies_comparees.py",
                "valide_marketing_metrics.py",
                "valide_big_bang.py",
                "valide_asteroides.py",
                "valide_alliages.py",
                "valide_mecanismes_machines.py",
                "valide_immunite.py",
                "valide_mutations.py",
                "valide_neurone_biologique.py",
                "valide_cycles_biogeochimiques.py",
                "valide_homeostasie.py",
                "valide_chronobiologie.py",
                "valide_proteines.py",
                "valide_cryobiologie.py",
                "valide_petrochimie.py",
                "valide_preuve_propositionnelle.py",
                "valide_sophismes.py",
                "valide_paradoxes.py",
                "valide_ordinaux.py",
                "valide_types_categories.py",
                "valide_galois.py",
                "valide_classification_surfaces.py",
                "valide_calculabilite.py",
                "valide_arret.py",
                "valide_algo_analyse.py",
                "valide_decidabilite.py",
                "valide_godel.py",
                "valide_intrication.py",
                "valide_coordination.py",
                "valide_nomenclature_chimique.py",
                "valide_pharmacochimie.py",
                "valide_mecanismes_reactionnels.py",
                "valide_eclipses.py",
                "valide_industrie40.py",
                "valide_stereochimie.py",
                "valide_procedes_industriels.py",
                "valide_classes_complexite.py",
                "valide_bioingenierie.py",
                "valide_nucleosynthese.py",
                "valide_impression_3d.py",
                "valide_usinage.py",
                "valide_procedes_fabrication.py",
                "valide_mineraux.py",
                "valide_systemes_politiques.py",
                "valide_recettes.py",
                "valide_techniques_culinaires.py",
                "valide_ceramiques.py",
                "valide_plastiques.py",                     # manifeste capacités formule/concept (voie REGISTRE)
                "valide_maths_discretes.py",                                     # primitives maths discrètes exactes (REGISTRE)
                "valide_algebre_calcul.py",                                      # équations linéaires/polynomiales exactes (REGISTRE)
                "valide_arithmetique_modulaire.py",                             # crypto math : Euclide/inverse mod/Miller-Rabin/RSA (REGISTRE)
                "valide_information_calcul.py", "valide_algebre_boole.py",       # Shannon + algèbre de Boole (REGISTRE)
                "valide_automates.py", "valide_turing.py", "valide_groupes.py",   # automates DFA + machines de Turing + groupes (REGISTRE)
                "valide_stoechiometrie.py",                                      # équilibrage d'équations chimiques (REGISTRE)
                "valide_trigonometrie.py", "valide_calcul_infinitesimal.py",   # trigo + limites/dérivation/intégration (REGISTRE)
                "valide_series_calcul.py",                                       # séries & convergence (REGISTRE)
                "valide_mecanique.py",                                           # mécanique : frottements/oscillateurs/fluides (REGISTRE)
                "valide_chimie_quantitative.py",                                 # solutions/thermochimie/électrochimie (REGISTRE)
                "valide_electronique.py", "valide_statique.py",                 # circuits électroniques + statique des structures (REGISTRE)
                "valide_robotique.py", "valide_controle.py",                   # robotique cinématique + automatique/contrôle (REGISTRE)
                "valide_equilibre_chimique.py", "valide_hydraulique.py",         # équilibres chimiques + hydraulique (REGISTRE)
                "valide_reseaux_ip.py", "valide_architecture.py",               # réseaux IPv4 + architecture (complément à 2) (REGISTRE)
                "valide_bases_donnees.py", "valide_theorie_reseaux.py",         # algèbre relationnelle + métriques de réseaux (REGISTRE)
                "valide_telecom.py", "valide_reseaux_neurones.py",             # télécoms (Shannon) + réseaux de neurones (REGISTRE)
                "valide_blockchain.py", "valide_etats_matiere.py",             # blockchain (SHA-256) + états de la matière (REGISTRE)
                "valide_cryptographie_appliquee.py", "valide_microprocesseurs.py",  # crypto symétrique + microprocesseurs/ALU (REGISTRE)
                "valide_cloud_distribue.py", "valide_big_data.py",             # cloud/distribué + big data (REGISTRE)
                "valide_web.py", "valide_geometrie_projective.py",           # web (HTML/CSS) + géométrie projective (REGISTRE)
                "valide_geotechnique.py", "valide_genie_chimique.py",
                "valide_nombres_complexes.py",
                "valide_liaisons_chimiques.py",
                "valide_analyse_fonctionnelle.py",
                "valide_equa_diff.py",
                "valide_relativite_restreinte.py",
                "valide_relativite_generale.py",
                "valide_quantique.py",
                "valide_semiconducteurs.py",
                "valide_entropie_thermo.py",
                "valide_maxwell.py",
                "valide_geometries_non_euclidiennes.py",
                "valide_geometrie_differentielle.py",
                "valide_topologie.py",
                "valide_fractales.py",
                "valide_complexite.py",
                "valide_langages_formels.py",
                "valide_cardinalite.py",
                "valide_astronautique.py",
                "valide_cosmologie.py",
                "valide_rayonnement_thermique.py",
                "valide_habitabilite.py",
                "valide_drake.py",
                "valide_mecanismes.py",
                "valide_structures_genie.py",
                "valide_batteries.py",
                "valide_composites.py",
                "valide_proprietes_materiaux.py",
                "valide_controle_qualite.py",
                "valide_cybernetique.py",
                "valide_chaos.py",
                "valide_bifurcations.py",
                "valide_ecologie.py",
                "valide_bioinfo.py",
                "valide_redox.py",
                "valide_polymeres.py",
                "valide_analyse_chimique.py",   # VAGUE PARALLÈLE 36 sujets (REGISTRE)         # géotechnique + génie chimique réacteurs/distillation (REGISTRE)
                "valide_genetique.py", "valide_references.py", "valide_classifieur.py",
                "valide_ia.py", "valide_regle.py", "valide_base_faits.py", "valide_juge_rapide.py",
                "valide_incertitude.py", "valide_lecteur.py", "valide_sources.py",
                "valide_lecteur_t7.py",                                          # T7 : patron numérique + technique
                "valide_lecteur_t4.py",                                          # T4 : VIVANT (taxons/gènes)
                "valide_lecteur_t6.py",                                          # T6 : PERSONNES & ORGANISATIONS
                "valide_lecteur_t11.py",                                         # T11 : TRANSPORT/VÉHICULES/INFRA
                "valide_lecteur_t8.py",                                          # T8 : HISTOIRE/DATES/POLITIQUE
                "valide_lecteur_t9.py",                                          # T9 : LANGUE/LEXIQUE/ÉCRITURE
                "valide_lecteur_t10.py",                                        # T10 : SPORT & COMPÉTITIONS
                "valide_lecteur_t12.py",                                        # T12 : RELIGION/MYTHO/PHILO
                "valide_lecteur_t5.py",                                          # T5 : ŒUVRES (créateurs/production)
                "valide_lecteur_nuit.py",                                        # NUIT 2026-06-29 : veines harvester (amorce-seule+mmap)
                "valide_lecteur_dirigeants.py"]                                  # ROUTE 4 : dirigeants pays-année (jsonl pur, léger)
    memoire = ["valide_memoire.py", "valide_restitution.py", "valide_deduction.py",   # moteur de mémoire/restitution
               "valide_conversation.py"]                                              # mémoire de DIALOGUE (anti-éphémère)
    incertitude = ["valide_calibration.py", "valide_bayes.py",                        # PALIER 2 (T2) : calibration + bayes
                   "valide_conformal.py", "valide_classif.py",                        #   + conforme + classif calibrée
                   "valide_propagation.py", "valide_conformal_adaptatif.py",          #   + propagation + conforme adaptatif
                   "valide_classif_multiclasse.py", "valide_decision.py",             #   + classif multi-classe + décision
                   "valide_conformal_normalise.py", "valide_scores_propres.py",       #   + conforme hétéro + scores propres
                   "valide_nouveaute.py", "valide_risque_conforme.py",                #   + nouveauté/OOD + contrôle de risque
                   "valide_derive_calibration.py", "valide_bayes_correle.py",         #   + dérive calibration + bayes corrélé
                   "valide_ensemble_calibre.py", "valide_venn_abers.py",              #   + ensemble calibré + Venn-Abers
                   "valide_conformal_pondere.py",                                     #   + conforme pondéré (covariate shift)
                   "valide_calibrateurs.py", "valide_temperature.py",                 #   + calibrateurs paramétriques + temperature
                   "valide_conformal_jackknife.py", "valide_conformal_quantile.py",   #   + jackknife+ + CQR
                   "valide_conformal_label.py", "valide_multilabel.py",               #   + conforme label-conditional + multi-label
                   "valide_bandit.py", "valide_opinions.py",                          #   + bandit + opinions d'experts
                   "valide_predictif.py", "valide_test_calibration.py",               #   + PIT + test d'hypothèse de calibration
                   "valide_echantillon_pondere.py", "valide_fermi.py", "valide_causal.py",  # + pondérée + Fermi + causal
                   "valide_prevision.py", "valide_changepoint.py",                    #   + prévision + changepoint
                   "valide_valeurs_extremes.py", "valide_bayes_sequentiel.py",        #   + valeurs extrêmes + bayésien séquentiel
                   "valide_inference_anytime.py", "valide_poisson.py",                #   + inférence anytime + Poisson
                   "valide_meta_analyse.py",                                          #   + méta-analyse (effets aléatoires)
                   "valide_incertitude_decomposee.py",                                #   + décomposition épistémique/aléatoire
                   "valide_survie.py",                                                 #   + analyse de survie (Kaplan-Meier sous censure)
                   "valide_donnees_manquantes.py",                                     #   + données manquantes (imputation multiple/Rubin)
                   "valide_regression_robuste.py",                                     #   + régression robuste (Huber M-estimateur)
                   "valide_region_multivariee.py",                                     #   + régions multivariées conformes (Mahalanobis)
                   "valide_quantile_regression.py",                                    #   + régression quantile (pinball, hétéroscédastique)
                   "valide_poisson_nonhomogene.py",                                    #   + processus de Poisson non-homogène (intensité variable)
                   "valide_processus_gaussien.py",                                     #   + régression par processus gaussien (incertitude épistémique)
                   "valide_serie_autoregressive.py",                                   #   + prévision AR(1) à h pas (incertitude croît avec l'horizon)
                   "valide_calibration_sequence.py",                                   #   + calibration de séquence (type LLM, confiance composée)
                   "valide_surdispersion.py",                                          #   + sur-dispersion des comptages (Poisson vs binomiale négative)
                   "valide_erreurs_variables.py",                                      #   + erreurs-en-variables (biais d'atténuation)
                   "valide_proportion_binomiale.py",                                   #   + proportion binomiale (Wilson vs Wald sur-confiant)
                   "valide_optimisation_bayesienne.py",                                #   + optimisation bayésienne (acquisition UCB/EI vs glouton)
                   "valide_calibration_ranking.py",                                    #   + calibration du classement (confiance des paires)
                   "valide_serie_multivariee.py",                                      #   + prévision VAR multivariée (région conjointe vs boîte)
                   "valide_bootstrap.py",                                              #   + IC bootstrap percentile/BCa (vs formule plaquée)
                   "valide_roc_auc.py",                                                #   + AUC + IC Hanley-McNeil (vs paires indépendantes)
                   "valide_prior_shift.py",                                            #   + correction de prévalence / label shift (Saerens EM)
                   "valide_bma.py",                                                    #   + moyennage bayésien de modèles (incertitude de sélection)
                   "valide_agregation_previsions.py",                                  #   + agrégation de prévisions (track-record + extremize)
                   "valide_multinomial_simultane.py",                                  #   + IC simultanés multinomiaux (multiplicité)
                   "valide_multicalibration.py",                                       #   + multicalibration (calibration par sous-groupe)
                   "valide_intervalle_tolerance.py",                                   #   + intervalle de tolérance (β,γ) vs IC moyenne
                   "valide_fdr_controle.py",                                           #   + contrôle du FDR (Benjamini-Hochberg, multiplicité des tests)
                   "valide_croyance_dempster_shafer.py",                               #   + fonctions de croyance (Dempster-Shafer, prob. imprécise, conflit de Zadeh)
                   "valide_possibilite.py",                                            #   + théorie des possibilités (Π/N, Dubois-Prade, encadrement de proba)
                   "valide_arithmetique_intervalles.py",                               #   + arithmétique d'intervalles (propagation garantie, théorème de Moore)
                   "valide_info_gap.py",                                               #   + décision info-gap (robustesse Ben-Haim, incertitude sévère non-probabiliste)
                   "valide_dirichlet_imprecis.py",                                     #   + Dirichlet imprécis (IDM Walley, multinomial robuste, invariance de représentation)
                   "valide_choquet.py",                                                #   + intégrale de Choquet / capacités (espérance inf/sup, Schmeidler, interaction)
                   "valide_robust_bayes.py",                                           #   + Bayes robuste ε-contamination (Berger, intervalle de posterior sur classe de priors)
                   "valide_p_box.py",                                                  #   + p-boxes (paire de CDF, encadrement loi inconnue, données intervalles)
                   "valide_prevision_walley.py",                                       #   + prévisions inf/sup de Walley (cadre général proba imprécise, perte sûre, enveloppe crédale)
                   "valide_tbm.py",                                                    #   + transferable belief model (Smets, monde ouvert m(∅), pignistique, ⊕ non normalisée)
                   "valide_decision_ambiguite.py",                                     #   + décision sous ambiguïté (maxmin EU Gilboa-Schmeidler, α-Hurwicz, regret minimax, Ellsberg)
                   "valide_smooth_ambiguity.py",                                       #   + ambiguïté lisse (Klibanoff-Marinacci-Mukerji, prior 2ᵉ ordre, sépare risque/ambiguïté)
                   "valide_variational_preferences.py",                                #   + préférences variationnelles/multiplier (Hansen-Sargent, robustesse à l'entropie)
                   "valide_pac_bayes.py",                                              #   + bornes PAC-Bayes (risque vrai garanti vs empirique optimiste, généralisation)
                   "valide_kalman_robuste.py",                                         #   + filtre de Kalman robuste (sur-confiance par covariance mal spécifiée, détecteur NIS, inflation)
                   "valide_dkw.py",                                                    #   + bande de confiance DKW (CDF, distribution-free, simultanée, multiplicité démasquée)
                   "valide_rademacher.py",                                             #   + complexité de Rademacher (borne de généralisation uniforme, capacité de sur-apprentissage)
                   "valide_shiryaev.py",                                               #   + détection au plus tôt (Shiryaev, quickest detection, fausse alarme contrôlée, posterior calibré)
                   "valide_concentration.py",                                          #   + bornes de concentration (Hoeffding/empirical-Bernstein, IC garanti n fini vs gaussien sur-confiant)
                   "valide_e_process.py",                                              #   + e-process / test par pari (e-values, Ville, type I contrôlé sous arrêt optionnel vs p-value répété)
                   "valide_jeux_zero_somme.py",                                        #   + jeux à somme nulle (sécurité maximin, théorème minimax, BR à adversaire présumé exploitable)
                   "valide_winner_curse.py",                                           #   + malédiction du vainqueur / inférence sélective (estimé sélectionné biaisé, IC naïf sous-couvre)
                   "valide_copules.py",                                                #   + copules & dépendance de queue (indépendance présumée sous-estime le risque conjoint extrême)
                   "valide_exp3.py",                                                   #   + bandit adversarial EXP3 (regret sous-linéaire garanti vs glouton exploitable, no-regret)
                   "valide_stabilite_algorithmique.py",                                #   + stabilité algorithmique (Bousquet-Elisseeff, algo instable mémorise/sur-confiant, borne par β)
                   "valide_confidentialite_differentielle.py",                         #   + confidentialité différentielle (Laplace ε-DP, sous-bruitage = sur-confiance vie privée, composition)
                   "valide_mdl.py",                                                    #   + MDL / longueur de description minimale (sélection par compression vs erreur d'entraînement sur-confiante)
                   "valide_covariance_grande_dim.py",                                  #   + covariance grande dim (Marchenko-Pastur, valeurs propres sur-confiantes, rétrécissement Ledoit-Wolf)
                   "valide_importance_sampling.py",                                    #   + échantillonnage préférentiel & ESS (poids dégénérés = SE naïf sous-estimé/sur-confiant, diagnostic ESS)
                   "valide_kelly.py",                                                  #   + critère de Kelly (croissance log ; sur-miser par sur-confiance = ruine malgré espérance positive)
                   "valide_maximum_entropie.py",                                       #   + maximum d'entropie (Jaynes ; loi la moins engagée ; toute loi plus piquée = info injectée/sur-confiance)
                   "valide_kde.py",                                                    #   + estimation de densité KDE (fenêtre trop étroite = modes-fantômes/sur-confiance, choix LOO)
                   "valide_test_permutation.py",                                       #   + test de permutation (distribution-free ; t-test sur-rejette sous asymétrie = sur-confiance)
                   "valide_choix_social.py",                                           #   + choix social (Condorcet/Arrow ; cycle ou méthodes divergentes → pas de gagnant objectif = sur-confiance)
                   "valide_matrice_confusion.py",                                      #   + matrice de confusion & taux de base (exactitude trompeuse sous déséquilibre, PPV de Bayes)
                   "valide_biais_survie.py",                                           #   + biais de survie (estimer sur les survivants sur-estime, leçon de Wald, tronquée-normale)
                   "valide_regression_moyenne.py",                                     #   + régression vers la moyenne (rebond statistique d'un groupe extrême ≠ effet causal)
                   "valide_simpson.py",                                                #   + paradoxe de Simpson (renversement d'agrégation ; trancher d'un seul niveau = sur-confiance)
                   "valide_benford.py",                                                #   + loi de Benford (anomalie/fraude par 1er chiffre ; écart ≠ preuve = double prudence)
                   "valide_ridge.py",                                                  #   + régression ridge (coefficients OLS instables sous colinéarité = sur-confiance, régularisation)
                   "valide_loi_puissance.py",                                          #   + lois à queue lourde (Hill ; IC du TCL sous-couvre si variance infinie = sur-confiance)
                   "valide_saint_petersbourg.py",                                      #   + paradoxe de St-Pétersbourg (espérance ∞ ≠ prix rationnel fini ; utilité bornée/bankroll fini)
                   "valide_berkson.py",                                                #   + paradoxe de Berkson/biais de collision (sélection sur effet commun = corrélation fantôme)
                   "valide_ergodicite.py",                                             #   + ergodicité (moyenne temporelle ≠ d'ensemble ; E[X] trompeur pour processus multiplicatif)
                   "valide_petits_nombres.py",                                         #   + loi des petits nombres (classement par taux brut à n inégaux = sur-confiant ; rétrécissement EB)
                   "valide_dirichlet_process.py",                                      #   + processus de Dirichlet (K fixé = sur-confiant, aucune masse 'classe neuve' ; CRP/DP-mixture infère K)
                   "valide_portefeuille_universel.py",                                 #   + portefeuille universel Cover (miser sur le meilleur actif a posteriori = sur-confiant ; regret log borné)
                   "valide_bandit_contextuel.py",                                      #   + bandit contextuel LinUCB (glouton ε=0 = sur-confiant, verrouillage/regret linéaire ; largeur de confiance UCB)
                   "valide_p_hacking.py",                                              #   + p-hacking/chemins bifurquants (p brut du gagnant = sur-confiant, min-p~Beta(1,m) ; inférence sélective Šidák)
                   "valide_revelation_bayesienne.py",                                  #   + révélation bayésienne/Monty Hall (50/50 naïf = sur-confiant ; la vraisemblance dépend du protocole de révélation)
                   "valide_lindley.py",                                                #   + paradoxe de Lindley (seuil α fixe = sur-confiant à grand n ; B01→∞ favorise H0 quand le fréquentiste rejette)
                   "valide_will_rogers.py",                                            #   + phénomène de Will Rogers (les 2 moyennes montent après reclassification = artefact ; groupé invariant)
                   "valide_biais_longueur.py",                                         #   + biais de longueur/inspection/amitié (échantillon ∝ taille sur-estime μ de σ²/μ ; correction harmonique)
                   "valide_taux_de_base.py",                                           #   + négligence du taux de base/faux positif (confondre sens et VPP = sur-confiant ; la prévalence domine)
                   "valide_deux_enveloppes.py",                                        #   + paradoxe des deux enveloppes (échanger=+25% = sur-confiant ; a priori impropre, gain inconditionnel 0)
                   "valide_parrondo.py",                                               #   + paradoxe de Parrondo (perdant+perdant=perdant = sur-confiant ; le mélange change la distribution de l'état)
                   "valide_braess.py",                                                 #   + paradoxe de Braess (ajouter une route aide toujours = sur-confiant ; l'équilibre égoïste empire 65→80)
                   "valide_main_chaude.py",                                            #   + sophisme du joueur/main chaude (renversement attendu ET débunkage naïf = sur-confiants ; biais Miller-Sanjurjo)
                   "valide_cadrage.py",                                                #   + effet de cadrage (préférence énoncée = sur-confiant ; renversement gain/perte sous loteries identiques, money pump)
                   "valide_good_turing.py",                                            #   + Good-Turing/masse manquante (proba 0 à l'inédit = sur-confiant, log-loss ∞ ; N₁/N + Chao1)
                   "valide_conjonction.py",                                            #   + sophisme de la conjonction/Linda (P(A∧B)>P(A) = sur-confiant ; bornes de Fréchet, livre hollandais)
                   "valide_cout_irrecuperable.py",                                     #   + coût irrécupérable/Concorde (peser le sunk = sur-confiant ; décision rationnelle invariante au sunk)
                   "valide_bertrand.py",                                               #   + paradoxe de Bertrand (« la » proba géométrique sans mécanisme = sur-confiant ; 1/3 vs 1/2 vs 1/4)
                   "valide_goodhart.py",                                               #   + loi de Goodhart (optimiser un proxy = sur-confiant ; la mesure cesse de suivre l'objectif sous pression)
                   "valide_stein.py",                                                  #   + paradoxe de Stein (MLE inadmissible d≥3 = sur-confiant ; James-Stein domine en risque total)
                   "valide_anscombe.py",                                               #   + quartet d'Anscombe (stats résumées identiques = sur-confiant ; diagnostics distinguent courbe/aberrant/levier)
                   "valide_aumann.py",                                                 #   + théorème d'accord d'Aumann (convenir d'être en désaccord = sur-confiant ; convergence des postérieurs à prior commun)
                   "valide_jury_condorcet.py",                                         #   + jury de Condorcet/sagesse des foules (plus de votants=mieux = sur-confiant ; faux si incompétent/corrélé)
                   "valide_allais.py",                                                 #   + paradoxe d'Allais (supposer l'axiome d'indépendance/l'EU = sur-confiant ; schéma incohérent avec toute utilité)
                   "valide_lord.py",                                                   #   + paradoxe de Lord (« l'effet » sans modèle causal = sur-confiant ; score de changement vs ANCOVA s'opposent)
                   "valide_borel_kolmogorov.py",                                       #   + paradoxe de Borel-Kolmogorov (P(X|Y=y) continu = sur-confiant ; lois conditionnelles dépendent de la limite)
                   "valide_regression_fallacieuse.py",                                 #   + régression fallacieuse Granger-Newbold (t/R² de séries non-stationnaires = sur-confiant ; différencier)
                   "valide_malediction_dimension.py",                                  #   + malédiction de la dimension (kNN/distances en haute-d = sur-confiant ; concentration des distances → coquille √d)
                   "valide_pascal_mugging.py",                                         #   + problème de Pascal/mugging (EU à gains non bornés = sur-confiant ; utilité bornée / pénalité de levier)
                   "valide_ellsberg.py",                                               #   + paradoxe d'Ellsberg (prior unique = sur-confiant ; schéma incohérent, aversion à l'ambiguïté/maxmin)
                   "valide_ancrage.py",                                                #   + effet d'ancrage (estimation contaminée par ancre non pertinente = sur-confiant ; ajuster pleinement)
                   "valide_biais_publication.py",                                      #   + biais de publication/file-drawer (moyenne publiée = sur-confiant ; sélection inter-études, asymétrie entonnoir)
                   "valide_no_free_lunch.py",                                          #   + No Free Lunch (apprenant universellement meilleur = sur-confiant ; même erreur moyenne sur toutes les fonctions)
                   "valide_gibbard_satterthwaite.py",                                  #   + Gibbard-Satterthwaite (règle de vote révèle le sincère = sur-confiant ; manipulable à ≥3 options)
                   "valide_jensen.py",                                                 #   + inégalité de Jensen/flaw of averages (brancher la moyenne dans f non linéaire = sur-confiant ; gap σ²)
                   "valide_dunning_kruger.py",                                         #   + Dunning-Kruger artefact (graphe DK = sur-confiant ; émerge à info nulle, régression vers la moyenne)
                   "valide_surapprentissage.py",                                       #   + sur-apprentissage/overfitting (ajustement en échantillon = sur-confiant ; courbe test en U, hold-out)
                   "valide_loi_grands_nombres.py"]                                     #   + LGN mal comprise (« ça s'équilibre » = sur-confiant ; moyenne→0 mais |S_n|~√n, loi de l'arcsinus)
    interface = ["interface/valide_interface.py"]                                      # INTERFACE locale (T3) — léger
    moteur = ["valide_resolution.py",                                                  # résolution floue d'entités (T3) — lourd
              "valide_fonction.py"]                                                    # routage NL → fonctions calculées (T3) — léger
    briques_v1 = ["valide_dimensions.py",                                              # BRIQUES GÉNÉRIQUES (socle machine, FAUX=0, légères) — Vague 1 :
                  "valide_grandeur.py",                                                #   grandeur typée (valeur+unité+incertitude) sur l'algèbre dimensionnelle
                  "valide_frame.py",                                                   #   relations n-aires réifiées (mécanismes/causalité)
                  "valide_mereologie.py",                                              #   composition partie-tout (design/assemblage)
                  "valide_loi.py",                                                    # Vague 2 : lois manipulables (résout/inverse, dimensionnellement sound)
                  "valide_identite.py",                                                #   identité canonique unifiée (union-find, fusion gatée par preuve, distinct au doute)
                  "valide_contrainte.py",                                              #   solveur CSP (backtracking complet, solution re-vérifiée, UNSAT honnête) — débloque le design
                  "valide_causalite.py",                                               #   graphe causal + intervention (agir≠observer, acyclique) — cœur invention
                  "valide_limite.py",                                                  # Vague 3 : limite théorique + écart (marge d'invention ; réel violant la borne -> impossible)
                  "valide_etat.py",                                                    #   états & variables typés + transitions (immuable, hors-domaine refusé) — socle simulation/planif
                  "valide_conservation.py",                                            # Vague 3 : bilan de conservation (mouvement perpétuel refusé)
                  "valide_simulation.py",                                              # Vague 3 : forward-model (déterministe, conflit de règles détecté, convergence honnête)
                  "valide_logique_tri.py",                                             # Vague 1 (fin) : logique trivaluée + monde ouvert/fermé (INCONNU au doute)
                  "valide_structure_mapping.py",                                       # Vague 4 : analogie inter-domaines (structure préservée ou None)
                  "valide_qualitatif.py",                                              # Vague 4 : raisonnement qualitatif (ambiguïté + et - -> ? honnête)
                  "valide_decouverte_loi.py",                                          # Vague 4 : découverte symbolique data->loi (exact-fit-ou-abstention)
                  "valide_planification.py",                                           # Vague 5 : planification STRIPS (plan re-joué atteint le but)
                  "valide_relaxation.py",                                              # Vague 5 : relâchement minimal de contraintes (TRIZ) vérifié SAT
                  "valide_pareto.py",                                                  # Vague 5 : front de Pareto (dominance exacte, aucun compromis inventé)
                  "valide_abduction.py",                                               # Vague 5 : abduction (explication via chemin causal réel, inexpliquées signalées)
                  "valide_ancres.py",                                                  # Vague 6 : banque d'ancres non-circulaire (source indépendante, auto-corroboration interdite)
                  "valide_falsification.py",                                           # Vague 6 : falsification active (contre-exemple réel ; sinon 'non réfutée', pas 'prouvée')
                  "valide_cas_limites.py",                                             # Vague 6 : cas-limites/asymptotes/symétries (crible factuel)
                  "valide_triangulation.py",                                           # Vague 6 : accord de 2 dérivations indépendantes (même méthode -> non_independant)
                  "valide_blackboard.py",                                              # Vague 7 : mémoire de travail partagée (provenance obligatoire, append-only)
                  "valide_arbitre.py",                                                 # Vague 7 : arbitrage de contradiction (fiabilité stricte, égalité -> abstention)
                  "valide_abstention.py",                                              # Vague 7 : politique d'abstention unifiée (défaut ABSTENTION, HORS domine)
                  "valide_trace.py",                                                   # Vague 7 : trace de raisonnement vérifiable (justification obligatoire, acyclique)
                  "valide_extraction.py",                                              # Vague 8 : texte->triplets (hors motif -> rien ; sûrs filtrés par seuil)
                  "valide_fraicheur.py",                                               # Vague 8 : péremption temporelle (jamais 'frais' par défaut ; atemporel jamais périmé)
                  "valide_revision.py"]                                                # Vague 8 : révision de croyances (jamais 2 valeurs contradictoires ; remplacement tracé)
    curee = vagues + extras + invention + domaines + memoire + incertitude + interface + moteur + briques_v1
    # AUTO-DÉCOUVERTE (2026-07-02) : tout valide_*.py présent sur disque est inclus, pour qu'AUCUNE capacité réelle ne
    # reste hors du filet de non-régression (fini les « orphelins »). La liste curée reste EN TÊTE (préserve l'ordre et
    # la détection des tests LOURDS) ; les validateurs non curés sont ajoutés triés. Tout nouveau valide_*.py est ainsi
    # protégé automatiquement. `_EXCLUS` = validateurs sciemment hors-gate (documenter la raison) — vide aujourd'hui.
    _EXCLUS: set = {"valide_commun.py"}   # module de HELPERS partagés (resolu/brique_vivante), PAS un validateur
    deja = set(curee)
    src_dir = TESTS if os.path.isdir(TESTS) else HARN     # portage : validateurs dans tests/
    auto = sorted(f for f in os.listdir(src_dir)
                  if f.startswith("valide_") and f.endswith(".py") and f not in deja and f not in _EXCLUS)
    tous = curee + auto
    return [f for f in tous if os.path.exists(os.path.join(HARN, _chemin(f)))]


def modules_locaux():
    # modules LOCAUX (pour l'analyse de dépendances du cache) : racine + src/ + interface/ + ingestion/.
    mods = set()
    for d in (HARN, os.path.join(HARN, "src"), os.path.join(HARN, "interface"), os.path.join(HARN, "ingestion")):
        try:
            mods |= {f[:-3] for f in os.listdir(d) if f.endswith(".py")}
        except OSError:
            pass
    return mods


def imports_directs(fichier, locaux):
    """Modules LOCAUX importés directement par `fichier` (statique). Renvoie (set_modules, dynamique_suspect)."""
    chemin = os.path.join(HARN, _chemin(fichier))
    try:
        with open(chemin, "r", encoding="utf-8") as fh:
            src = fh.read()
        arbre = ast.parse(src)
    except (OSError, SyntaxError):
        return set(), True
    mods, suspect = set(), False
    for n in ast.walk(arbre):
        if isinstance(n, ast.Import):
            for a in n.names:
                base = a.name.split(".")[0]
                if base in locaux:
                    mods.add(base)
        elif isinstance(n, ast.ImportFrom):
            if n.module:
                base = n.module.split(".")[0]
                if base in locaux:
                    mods.add(base)
        elif isinstance(n, ast.Call):
            f = n.func
            if isinstance(f, ast.Name) and f.id == "__import__":
                if n.args and isinstance(n.args[0], ast.Constant):
                    # argument LITTÉRAL : résolvable. Local -> dépendance ; stdlib (math, itertools…) -> inoffensif.
                    if n.args[0].value in locaux:
                        mods.add(n.args[0].value)
                else:
                    suspect = True            # __import__ à argument DYNAMIQUE (non littéral) -> prudence : toujours relancer
    return mods, suspect


def cloture(fichier, locaux, cache_imp):
    """Clôture transitive des modules locaux importés par `fichier`. (suspect=True -> toujours relancer)."""
    vus, pile, suspect = set(), [fichier[:-3]], False
    vus_fichiers = {fichier}
    while pile:
        mod = pile.pop()
        f = mod + ".py"
        if mod in cache_imp:
            mods, susp = cache_imp[mod]
        else:
            mods, susp = imports_directs(f, locaux)
            cache_imp[mod] = (mods, susp)
        suspect = suspect or susp
        for m in mods | set(UNIVERSELS):
            if m not in vus and m in locaux:
                vus.add(m)
                vus_fichiers.add(m + ".py")
                pile.append(m)
    return vus_fichiers, suspect


def hash_fichiers(fichiers):
    h = hashlib.sha1()
    for f in sorted(fichiers):
        h.update(f.encode())
        try:
            with open(os.path.join(HARN, f), "rb") as fh:
                h.update(fh.read())
        except OSError:
            h.update(b"<absent>")
    return h.hexdigest()


def empreinte_datasets():
    """Empreinte LÉGÈRE de l'état des données du lecteur : (nom, taille, mtime_ns) de chaque datasets/lecteur/*.jsonl,
    SANS lire le contenu (juste os.stat -> rapide même sur 9p). Repliée dans le fingerprint des validateurs
    data-driven (ceux qui importent lecteur.py) : SANS ça, une ingestion qui ne touche aucun .py ne change aucun
    fingerprint -> le cache rejoue un PASS PÉRIMÉ sur des données modifiées (trou de soundness : un fait faux
    ingéré après le gel du code passerait inaperçu). Toute modif d'un .jsonl -> empreinte différente -> re-run."""
    d = os.path.join(HARN, "datasets", "lecteur")
    h = hashlib.sha1()
    try:
        noms = sorted(n for n in os.listdir(d) if n.endswith(".jsonl"))
    except OSError:
        return "<absent>"
    for n in noms:
        try:
            st = os.stat(os.path.join(d, n))
            h.update(f"{n}:{st.st_size}:{st.st_mtime_ns}\n".encode())
        except OSError:
            h.update(f"{n}:<absent>\n".encode())
    return h.hexdigest()


def lance(fichier):
    """Exécute un validateur en sous-process borné. Renvoie (ok, resume, duree_s)."""
    # CAP MÉMOIRE par test (RLIMIT_AS=14 Go, virtuel) + MALLOC_ARENA_MAX=2 (rend l'AS déterministe ~RSS, sinon glibc
    # sur-réserve 8×cœurs arènes). NB le vrai filet anti-saturation est le SÉMAPHORE des tests LOURDS dans main()
    # (cf. set `lourd`) : plusieurs chargements concurrents du lecteur déclenchent le tueur OOM WSL (-9).
    # 2026-06-26 : le lecteur auto-chargé fait désormais 33,5 M faits -> pic RSS mesuré ~5,1 Go (était 4 Go quand le
    # lecteur faisait 6,38 M faits). Cap relevé 4->14 Go pour couvrir le pic + la façade ia.py de valide_ia ;
    # lourds sérialisés ≤1 dans main() -> sûr vs RAM système (47 Go).
    pre = "import resource; resource.setrlimit(resource.RLIMIT_AS,(14680064*1024,14680064*1024))"
    env = _env_pipeline(dict(os.environ, MALLOC_ARENA_MAX="2"))   # PYTHONPATH src+interface+ingestion (portage)
    cible = _chemin(fichier)                                       # tests/valide_X.py (ou interface/valide_interface.py)
    t0 = time.monotonic()
    try:
        p = subprocess.run([sys.executable, "-c", f"{pre}\nimport runpy; runpy.run_path({cible!r}, run_name='__main__')"],
                           cwd=HARN, capture_output=True, text=True, timeout=TIMEOUT, env=env)
        dt = time.monotonic() - t0
        ok = p.returncode == 0
        ligne = ""
        for l in reversed((p.stdout or "").splitlines()):
            if "/" in l or "VALID" in l.upper() or "ÉCHEC" in l.upper():
                ligne = l.strip()
                break
        resume = ligne if ok else (ligne or ((p.stderr or "").splitlines()[-1:] or [""])[-1])
        if not ok:
            resume = f"[rc={p.returncode}] {resume}"   # diag : 137=SIGKILL/OOM, -24/152=SIGXCPU, 1=erreur Python
        return ok, resume, dt
    except subprocess.TimeoutExpired:
        return False, "TIMEOUT", time.monotonic() - t0


def main():
    jobs = 16
    use_cache = "--no-cache" not in sys.argv and "--full" not in sys.argv
    if "--jobs" in sys.argv:
        jobs = int(sys.argv[sys.argv.index("--jobs") + 1])

    vals = liste_validateurs()
    locaux = modules_locaux()
    cache_imp: dict = {}
    fingerprints, toujours, lourd = {}, set(), set()
    # Gates qui importent lecteur.py MAIS posent LECTEUR_AMORCE_SEULE=1 : elles ne chargent que LEURS relations
    # dans un Lecteur frais (jamais le singleton global de 33,5 M faits) → pic <~5 Go, donc LÉGÈRES et
    # parallélisables plein. NE PAS y mettre valide_lecteur.py / t4 / t5 : eux itèrent le singleton global.
    _LEGER_AMORCE = {"valide_lecteur_t6.py", "valide_lecteur_t8.py", "valide_lecteur_t9.py",
                     "valide_lecteur_t10.py", "valide_lecteur_t11.py", "valide_lecteur_t12.py",
                     "valide_lecteur_nuit.py", "valide_lecteur_dirigeants.py"}
    # Empreinte des DONNÉES calculée UNE fois (stat de ~1351 .jsonl ~1 s sur 9p) puis repliée dans le
    # fingerprint de chaque validateur data-driven -> le cache n'est plus aveugle aux ingestions.
    emp_data = empreinte_datasets()
    for v in vals:
        fichiers, suspect = cloture(v, locaux, cache_imp)
        fp = hash_fichiers(fichiers)
        # Validateur data-driven (importe lecteur.py) : le verdict dépend des datasets/lecteur/*.jsonl, pas
        # seulement du code -> replier l'empreinte des données. Une ingestion (même sans toucher un .py)
        # invalide alors le cache et force la re-validation. FAUX=0 : plus de PASS périmé sur données changées.
        if "lecteur.py" in fichiers:
            fp = hashlib.sha1(f"{fp}:{emp_data}".encode()).hexdigest()
        fingerprints[v] = fp
        if suspect:
            toujours.add(v)
        # LOURD = charge tout le lecteur (6,38 M faits, ~1,1 Go RSS). En faire tourner plusieurs EN PARALLÈLE
        # sature la mémoire (le tueur OOM du noyau WSL SIGKILL -9 sous pression, même avec 44 Go « libres »).
        # On les SÉRIALISE via un sémaphore (HEAVY_MAX) tout en gardant le parallélisme plein sur les légers.
        if "lecteur.py" in fichiers and v not in _LEGER_AMORCE:
            lourd.add(v)

    cache = {}
    if use_cache and os.path.exists(CACHE):
        try:
            with open(CACHE) as fh:
                cache = json.load(fh)
        except (OSError, ValueError):
            cache = {}

    # durées pour longest-first
    durees = {}
    if os.path.exists(DUREES):
        for l in open(DUREES):
            parts = l.split()
            if len(parts) == 2:
                durees[parts[1]] = float(parts[0])

    a_lancer, en_cache = [], []
    for v in vals:
        if use_cache and v not in toujours and cache.get(v, {}).get("fp") == fingerprints[v] and cache[v].get("ok"):
            en_cache.append(v)
        else:
            a_lancer.append(v)
    a_lancer.sort(key=lambda v: durees.get(v, 50), reverse=True)   # longest-first

    # Sémaphore des tests LOURDS : au plus HEAVY_MAX chargements concurrents du lecteur (sinon le tueur OOM WSL
    # SIGKILL -9 sous pression mémoire). Les tests légers gardent le parallélisme plein (jobs).
    import threading
    # HEAVY_MAX ADAPTATIF : chaque validateur lourd charge le lecteur (~5 Go pic, mesuré 2026-06-26 à 33,5M
    # faits). Sérialiser à 1 explique l'essentiel du temps de gate (~13 lourds × ~6 min de chargement). On
    # parallélise selon la RAM DISPONIBLE au lancement (budget 6 Go/slot, clamp 1..4) -> rapide quand libre,
    # sûr sous contention (reste à 1 si peu de RAM). Ne change AUCUN résultat, seulement l'ordonnancement.
    def _mem_avail_go():
        try:
            for _l in open("/proc/meminfo"):
                if _l.startswith("MemAvailable:"):
                    return int(_l.split()[1]) / 1024 / 1024
        except OSError:
            pass
        return 8.0
    # budget 10 Go/slot (5 pic + 5 marge pour les pics des AUTRES terminaux), clamp 1..3 : coexiste sans OOM système.
    HEAVY_MAX = max(1, min(3, int(_mem_avail_go() // 10)))
    sem_lourd = threading.Semaphore(HEAVY_MAX)
    def lance_gated(v):
        if v in lourd:
            with sem_lourd:
                return lance(v)
        return lance(v)

    print(f"[non-rég] {len(vals)} validateurs : {len(en_cache)} en cache, {len(a_lancer)} à lancer "
          f"(jobs={jobs}, lourds={len(lourd & set(a_lancer))} sérialisés ≤{HEAVY_MAX})", flush=True)
    t0 = time.monotonic()
    resultats = {v: (True, "(cache) " + cache[v].get("resume", "")) for v in en_cache}
    fails = []
    nouvelles_durees = dict(durees)
    if a_lancer:
        with cf.ThreadPoolExecutor(max_workers=jobs) as ex:
            futurs = {ex.submit(lance_gated, v): v for v in a_lancer}
            for fut in cf.as_completed(futurs):
                v = futurs[fut]
                ok, resume, dt = fut.result()
                resultats[v] = (ok, resume)
                nouvelles_durees[v] = dt          # auto-tune le longest-first (durées réelles courantes)
                cache.setdefault(v, {})
                if ok:
                    cache[v] = {"fp": fingerprints[v], "ok": True, "resume": resume}
                else:
                    cache.pop(v, None)            # un FAIL n'est jamais mémorisé
                    fails.append(v)
                print(f"  {'OK ' if ok else 'FAIL'} {v}  {resume}", flush=True)
        try:                                       # persiste les durées pour le prochain ordonnancement
            with open(DUREES, "w") as fh:
                for k, val in sorted(nouvelles_durees.items(), key=lambda kv: kv[1], reverse=True):
                    fh.write(f"{val:.0f} {k}\n")
        except OSError:
            pass

    if use_cache:
        try:
            with open(CACHE, "w") as fh:
                json.dump(cache, fh)
        except OSError:
            pass

    dt = time.monotonic() - t0
    npass = sum(1 for ok, _ in resultats.values() if ok)
    print(f"\n=== NON-RÉG : {npass}/{len(vals)} PASS ({len(en_cache)} via cache) en {dt:.0f}s ===")
    if fails:
        print("FAILS:", " ".join(fails))
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
