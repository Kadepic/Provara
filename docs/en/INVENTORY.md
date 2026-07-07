# Complete inventory of Provara

> Generated mechanically from the code (docstrings + API). Represents the entirety of the shipped modules.

**1306 modules · 4686 public functions/classes · 171 496 lines** (mechanical snapshot; faits_appris added by hand on 2026-07-06, tronc on 2026-07-07)


## Core — 6 modules

| Module | Role | API |
|---|---|---|
| `assistant_nl` | NL ASSISTANT — the AUTONOMOUS CONVERSATIONAL GATEWAY ("big leap", night mandate 2026-07-03). | class Reponse, note_clarification, note_reformulation, oublie_etat, reprend_clarification, apres_hors, complement, qualifie_texte |
| `classifieur_bornage` | BOUNDEDNESS CLASSIFIER — the STATUS ROUTER of the atom contract, anti-hallucination guardian (2026-07-02). | class Classement, classe, regime_atome_pour |
| `ia` | AI — UNIFIED ENTRY POINT ("complete ≠ usable": | juge_dispositif, reference, donnee, donnee_nl, coordonnees_lieu, distance_lieux, cap_lieux, dms_vers_dd |
| `lecteur` | GENERIC DATA READER — the engine of bounded DATA (workstream #3 ; 566 subjects: | class Lecteur, amorce_cherche, cherche, repond, repond_nl |
| `repond` | CONVERSATIONAL LAYER of the interface — making the assistant able to ANSWER, without ever inventing. | pret, est_fallback, repond |
| `serveur` | LOCAL INTERFACE — small sovereign web server on top of the conversation memory. | liste_conversations, archive_conversation, desarchive_conversation, lire_conversation, ajoute_message, nouvelle_conversation, oublie_conversation, class Handler |

## Capability library (engines & atoms) — 493 modules

| Module | Role | API |
|---|---|---|
| `_nonreg` | INCREMENTAL + PARALLEL NON-REGRESSION (the standard runner, fast AND sound). | liste_validateurs, modules_locaux, imports_directs, cloture, hash_fichiers, empreinte_datasets, lance, main |
| `abduction` | ABDUCTION — Wave 5 brick (inference to the best explanation). | explique, hypotheses_possibles, meilleure_explication |
| `abstention` | UNIFIED ABSTENTION POLICY — Wave 7 brick (the capstone of honesty). | decide, affirme_ou_abstient |
| `aerodynamique` | AERONAUTICS — flight, aerodynamics (Yohan's mandate: | portance, trainee, finesse, reynolds, vol_equilibre |
| `agregation_previsions` | TIER 2 — AGGREGATION OF PROBABILISTIC FORECASTS (track-record weighting + EXTREMIZE) (brick, 2026-06-26). | brier, poids_track_record, moyenne_logit_ponderee, ajuste_extremize, agrege, moyenne_naive, calibre_agregateur, formule |
| `algebre_boole` | BOOLEAN ALGEBRA — EXACT evaluation of boolean expressions & truth tables, FAUX=0 (formula/concept 2026-06-29). | variables, evalue, table_verite, est_tautologie, est_contradiction, est_satisfiable, equivalent |
| `algebre_calcul` | ALGEBRA — EXACT solving of equations (linear, polynomial), FAUX=0 (formula/concept mission 2026-06-29). | equation_lineaire, equation_quadratique, evalue_polynome, est_racine |
| `algo_analyse` | ALGO_ANALYSE — complexity analysis & algorithm correctness, EXACT MECHANISM, FAUX=0 (formula/concept mission 2026-0 | complexite_boucle, compare_asymptotique, nombre_operations_tri, comparaisons_pire_cas, invariant_boucle_somme |
| `allais` | TIER 2 — ALLAIS PARADOX (violation of the independence axiom): | eu, rdu, schema_allais, contradiction_eu, analyse, formule |
| `allen` | ALLEN'S INTERVAL ALGEBRA — TEMPORAL reference frame (representation brick, 2026-07-02). | inverse, relation, avant, chevauche, contient |
| `alliages` | METALS AND ALLOYS — the lever rule + catalogue of binary alloys (Yohan's mandate: | fraction_phase, classe_alliage |
| `analyse_chimique` | BOUNDED CHEMICAL ANALYSIS — analytical methods (UV-visible spectroscopy, chromatography). | absorbance, concentration_depuis_absorbance, transmittance, facteur_retention_rf |
| `analyse_fonctionnelle` | FUNCTIONAL ANALYSIS — normed vector spaces, FAUX=0 (formula/concept mission 2026-06-29). | produit_scalaire, norme, distance, cauchy_schwarz_verifiee, sont_orthogonaux, projection |
| `ancrage` | TIER 2 — QUANTITATIVE ANCHORING EFFECT: | estimateur_ancre, correlation, simule, analyse, formule |
| `ancres` | NON-CIRCULAR ANCHOR BANK — Wave 6 founding brick. | class Incoherence, class BanqueAncres |
| `anscombe` | TIER 2 — ANSCOMBE'S QUARTET / INADEQUACY OF SUMMARY STATISTICS: | regression, stats_resumees, diagnostics, analyse, formule |
| `arbitre` | CONTRADICTION ARBITER (runtime) — Wave 7 brick. | arbitre, valeur_arbitree |
| `architecture` | COMPUTER ARCHITECTURE — number representation, FAUX=0 (formula/concept mission 2026-06-29). | vers_binaire, vers_hexa, depuis_binaire, complement_a_deux, depuis_complement_a_deux, addition_binaire |
| `arithmetique_intervalles` | TIER 2 — INTERVAL ARITHMETIC: | class Intervalle, evalue, plugin_point, formule |
| `arithmetique_modulaire` | MODULAR ARITHMETIC & CRYPTO — EXACT primitives (integers), FAUX=0 (formula/concept mission 2026-06-29). | pgcd, euclide_etendu, inverse_modulaire, exp_modulaire, est_premier, rsa_chiffre, rsa_dechiffre |
| `arret` | Halting problem — EXACT mechanism, FAUX=0. | sarrete_dans, arret_general_decidable, programme_diagonal, argument_diagonal |
| `asteroides` | ASTEROIDS & COMETS — Tisserand parameter (orbital invariant) and EXACT dynamical classification. | tisserand, classifie, classifie_orbite |
| `astronautique` | ASTRONAUTICS — flight mechanics (compute/proof capability, Yohan's mandate: | delta_v, rapport_de_masse, masse_finale, vitesse_orbitale, vitesse_liberation, periode_orbitale |
| `atome` | ATOM CONTRACT — the universal unit of the AI's knowledge (bounded AND unbounded), FAUX=0 (2026-07-02, hardened). | rouvre, est_refute, class Portee, class Verdict, class Atome, atteste, convention, suppose |
| `audio_wav` | AUDIO WAV — BOUNDED core of the SOUND modality (uncompressed PCM), pure stdlib (2026-07-02). | encode, ecris, decode, silence, sinus, carre |
| `audiologie` | AUDIOLOGY (hearing) — decibel scale, classification of hearing loss, facts (Yohan's mandate: | niveau_db, classe_perte_auditive, plage_audible_hz, addition_db |
| `audit_ancres` | ANCHOR AUDIT — which reader relations carry an EXTERNAL (non-circular) truth assertion? The store (dataset | audit |
| `audit_code` | CODE AUDIT — the DEVELOPMENT/SECURITY domain, bounded by POSITED RULES (Yohan's mandate 2026-06-23). | class Constat, audite, explique |
| `aumann` | TIER 2 — AUMANN'S AGREEMENT THEOREM: | dialogue, analyse, formule |
| `auto_apprend` | AUTONOMOUS SELF-LEARNING (2026-06-22, phase "the AI creates what it lacks, judged by reality" — Yohan's vision). | class MoteurAutonome |
| `auto_invention` | SELF-INVENTION ENGINE — AUTONOMOUS exploration judged by reality (2026-06-18, goal "reflection network that does not depend | class MoteurAutoInvention |
| `auto_invention_ouverte` | OPEN SELF-INVENTION ENGINE — compositional & multi-domain (2026-06-18, goal project-vision-auto-evolution-verite) | class MoteurOuvert |
| `auto_optimise` | RECURSIVE SELF-OPTIMIZATION LOOP (Yohan's "final goal": | cout_expr, optimise_expr, optimise_jusqu_fixe |
| `auto_synthese` | SELF-SYNTHESIS FROM SKELETONS (2026-06-24, Yohan's order "let it build its own bricks"). | synthetise |
| `automates` | FINITE AUTOMATA (DFA) — EXACT simulation, FAUX=0 (formula/concept mission 2026-06-29). | accepte, etats_accessibles |
| `automobile` | automobile.py — Elementary automotive mechanics (established formulas). | distance_freinage, puissance, rapport_transmission, regime_roue, consommation_100km |
| `bandit` | TIER 2 — SEQUENTIAL DECISION UNDER UNCERTAINTY: | class Bandit, simule, formule |
| `bandit_contextuel` | TIER 2 — CONTEXTUAL BANDIT (LinUCB): | class Agent, simule, analyse, formule |
| `base_faits` | VERIFIED FACT BASE — the lookup JUDGES for categories where truth is not DEDUCED but OBSERVED (cat 2 m | class Fait, normalise, cherche, repond_nl |
| `bases_donnees` | DATABASES — EXACT relational algebra, FAUX=0 (formula/concept mission 2026-06-29). | selection, projection, jointure, union, difference, agregat |
| `batteries` | BATTERIES / ELECTRICAL STORAGE — EXACT primitives, directly callable, FAUX=0 (formula/concept mission). | energie_wh, capacite_Ah_depuis_energie, courant_c_rate, temps_charge, rendement_energetique |
| `bayes` | TIER 2 — BAYESIAN COMBINATION OF EVIDENCE (brick 2, 2026-06-25). | maj_log_odds, lr_indice, posterior, formule, posterior_correle, rho_empirique |
| `bayes_sequentiel` | TIER 2 — SEQUENTIAL BAYESIAN (online Beta-Bernoulli, brick 34, 2026-06-25). | betai, quantile_beta, class BetaBernoulli, formule |
| `benford` | TIER 2 — BENFORD'S LAW: | proba_benford, premier_chiffre, distribution, test_benford, analyse, formule |
| `berkson` | TIER 2 — BERKSON'S PARADOX / COLLIDER BIAS: | correlation, selectionne_collisionneur, correlation_population, correlation_selectionnee, analyse, formule |
| `bertrand` | TIER 2 — BERTRAND'S PARADOX (geometric probability): | tire_corde_longue, probabilite, analyse, formule |
| `besoin` | NEED / GOAL — GOALS layer for the invention engine (Yohan's request 2026-07-02: | objectif_reel, decompose, principes, strategies_naturelles, chaines_physiques |
| `biais_longueur` | TIER 2 — LENGTH BIAS / INSPECTION & FRIENDSHIP PARADOX: | moyenne, variance, moyenne_biaisee_taille, echantillonne_biais_taille, correction_harmonique, degre_moyen, degre_voisin_moyen, analyse |
| `biais_publication` | TIER 2 — PUBLICATION BIAS (file-drawer): | simule, analyse, formule |
| `biais_survie` | TIER 2 — SURVIVORSHIP BIAS (survivorship bias): | moyenne, survivants, biais, ratio_mills, moyenne_tronquee_normale, taux_succes_survivant, analyse, formule |
| `bibliotheconomie` | bibliotheconomie.py — Library science / information science. | classes_dewey, classe_dewey, isbn_valide |
| `bibliotheque_invention` | RECURSIVE CAPSTONE — "SLEEP" phase (DreamCoder): | promeut_abstraction, etend_bibliotheque, gain_reconnaissance, verifie_non_regression |
| `bifurcations` | CATASTROPHE THEORY / BIFURCATIONS — fixed-point stability and normal forms. | stabilite_point_fixe, stabilite_point_fixe_discret, point_fixe_logistique, multiplicateur_logistique, bifurcation_logistique, nb_points_fixes_pli, nb_points_fixes_fourche |
| `big_bang` | BIG BANG — established cosmology (sourced formulas/facts). | age_univers_hubble, abondance_primordiale, temperature_cmb, densite_critique |
| `big_data` | BIG DATA — at-scale processing primitives, FAUX=0 (formula/concept mission 2026-06-29). | mapreduce, compte_mots, class FiltreBloom, echantillon_reservoir |
| `bioinfo` | BIOINFORMATICS / SEQUENCING — EXACT primitives on DNA sequences/strings, FAUX=0 (formula/concept mission). | distance_hamming, taux_gc, complement_inverse, distance_edition |
| `bioingenierie` | BIOENGINEERING — Michaelis-Menten enzyme kinetics (ESTABLISHED law, EXACT mechanism). | vitesse, km_vitesse_demi, efficacite_catalytique |
| `biomecanique` | BIOMECHANICS OF MOVEMENT — EXACT physics of athletic motion (Yohan's mandate: | portee_projectile, hauteur_max, temps_de_vol, angle_optimal_portee, moment_force, couple, impulsion |
| `biostatistique` | BIOSTATISTICS — diagnostic tests (EXACT epidemiology). | sensibilite, specificite, valeur_predictive_positive, valeur_predictive_negative, prevalence, rapport_vraisemblance_positif, rapport_vraisemblance_negatif, exactitude |
| `blackboard` | BLACKBOARD / SHARED WORKING MEMORY — Wave 7 founding brick (orchestration). | class Entree, class Blackboard |
| `blockchain` | BLOCKCHAIN / CRYPTOCURRENCIES (mechanism) — integrity of a chain, FAUX=0 (formula/concept mission 2026-06-29). | hash_bloc, cree_bloc, chaine_valide, merkle_root, preuve_travail_valide |
| `bma` | TIER 2 — BAYESIAN MODEL AVERAGING (BMA): | ajuste_polynome, bic, predit_modele, poids_bic, ajuste, intervalle_bma, intervalle_meilleur, formule |
| `bootstrap` | TIER 2 — BOOTSTRAP CONFIDENCE INTERVAL (percentile & BCa) for an ARBITRARY statistic (brick, 2026-06-26) | repliques, ic_normal, ic_naif_moyenne, ic_percentile, ic_bca, intervalle, formule |
| `bootstrap_savoir` | BOOTSTRAP_SAVOIR — the AI builds a multi-level taxonomy ON ITS OWN by reading definitions (2026-06-18). | genus, graphe, chaine, frontiere, class Savoir |
| `borel_kolmogorov` | TIER 2 — BOREL-KOLMOGOROV PARADOX: | simule, e_abs_latitude, analyse, formule |
| `boucle` | Brick 4 — THE orchestration LOOP. | class Rapport, tour, campagne |
| `boucle_invention` | CAPSTONE — THE COMPLETE INVENTION LOOP: | boucle |
| `braess` | TIER 2 — BRAESS'S PARADOX: | equilibre_nash, optimum_social, analyse, formule |
| `braille` | BRAILLE — BOUNDED core of tactile writing (FIXED, bijective convention), pure stdlib (2026-07-02). | lettre_vers_points, points_vers_lettre, lettre_vers_unicode, unicode_vers_lettre, texte_vers_braille, braille_vers_texte, cellule_ascii |
| `budget_personnel` | budget_personnel.py — Personal budget management: | solde, taux_epargne, regle_50_30_20, capacite_emprunt, reste_a_vivre |
| `cadrage` | TIER 2 — FRAMING EFFECT / DESCRIPTION INVARIANCE: | v_prospect, choix_prospect, choix_eu, money_pump, analyse, formule |
| `calcul_infinitesimal` | INFINITESIMAL CALCULUS — EXACT limits, differentiation, integration on polynomials, FAUX=0 (formula/concept 2026-06-29). | evalue, derivee, primitive, integrale_definie, limite_polynome_en, limite_rationnelle_en |
| `calculabilite` | Computability theory — EXACT MECHANISM, FAUX=0. | fonction_ackermann, est_primitive_recursive_ackermann, successeur, recursion_primitive, addition, multiplication, puissance, primitive_recursive |
| `calibrateurs` | TIER 2 — PARAMETRIC CALIBRATORS (brick 18, 2026-06-25). | class CalibrateurPlatt, ajuste_platt, class CalibrateurHistogramme, ajuste_histogramme, class CalibrateurBeta, ajuste_beta, ajuste |
| `calibration` | TIER 2 — THE CALIBRATION INSTRUMENT (the cross-cutting judge, 2026-06-25). | depuis_probas, brier, diagramme_fiabilite, ece, mce, ecart_signe, est_calibre, couverture |
| `calibration_ranking` | TIER 2 — RANKING CALIBRATION (ranking): | proba_mieux, ajuste_temperature, classe, dcg, ndcg, calibre, formule |
| `calibration_sequence` | TIER 2 — SEQUENCE CALIBRATION (confidence of a multi-step, LLM-like generation, brick 47, 2026-06-26). | confiance_sequence, ajuste_par_etape, confiance_sequence_calibree, formule |
| `capacites` | CAPABILITIES — explicit and AUDITABLE manifest of the AI's formula/concept capabilities (2026-06-29 mission). | couvert, preuve_de, sujets_couverts, verifie_tout |
| `cardinalite` | CARDINALITY & COUNTABILITY — EXACT primitives (integers), FAUX=0 (formula/concept mission 2026-06-29). | cardinal_ensemble, cardinal_parties, couple_cantor, decouple_cantor, est_denombrable |
| `cardiologie` | QUANTITATIVE CARDIOLOGY — ESTABLISHED clinical formulas (Yohan's mandate: | frequence_cardiaque_max, qt_corrige_bazett, fraction_ejection, classe_fc_repos |
| `carte_limites_francais` | CARTE_LIMITES_FRANCAIS — how far model-free climbs in French, and where the wall is (2026-06-18, Yohan "determine the | carte, verdict, main |
| `cartographie` | CARTOGRAPHY / GIS / GEOMATICS — EXACT computations (Yohan's mandate: | echelle_distance_reelle, distance_carte, resolution_au_sol, resolution_au_sol_depuis_dpi, conversion_dms_dd, cm_en_m, cm_en_km |
| `cas_limites` | EDGE CASES / ASYMPTOTES / SYMMETRIES — Wave 6 brick (verification at the boundaries). | limite_en, monotone, bornee, parite, homogene_degre |
| `causal` | TIER 2 — CAUSAL INFERENCE UNDER UNCERTAINTY (ATE, brick 31, 2026-06-25). | ate_diff_moyennes, ate_ipw, formule |
| `causalite` | CAUSALITY — Wave 1 brick (causal graph + intervention). | class CycleCausal, class GrapheCausal |
| `ceramiques` | BOUNDED CERAMICS — ceramic properties (established facts + exact computations). | retrait_cuisson, porosite, classe_ceramique, proprietes_ceramique, proprietes_mecaniques, est_fragile, classes_connues |
| `changepoint` | TIER 2 — CHANGEPOINT DETECTION (changepoint, brick 32, 2026-06-25). | statistique, detecte_changement, formule |
| `chaos` | CHAOS THEORY — sensitivity to initial conditions via the LOGISTIC MAP (Yohan's mandate, bounded "FORMULA"). | iterer_logistique, point_fixe_logistique, sensibilite |
| `charge_lexique` | CHARGE_LEXIQUE — scalable lexicon ingester (2026-06-18, "extend the lexicon → large verified dataset"). | ecris, charge, coherence |
| `chemin2d` | 2D PATHS — line segments + cubic BÉZIER curves, SVG `<path>` export (modality, 2026-07-02). | class Ligne, class Bezier, class Chemin, cercle_approx |
| `cherche_architecture_max` | ARCHITECTURE SEARCH — MAXIMAL VERSION (all stages, multi-domain, large budget, judged by REALITY). | evalue1, main |
| `chercheur_invention` | AUTONOMOUS INVENTION SEEKER — layer above `moteur_invention` toward the FINAL OBJECTIVE (cf. | class Inventaire, inventorie |
| `chimie` | BOUNDED CHEMISTRY — basic stoichiometry (Yohan's mandate 2026-06-23: | composition, masse_molaire, nb_atomes, pourcentage_massique, repond_nl |
| `chimie_quantitative` | QUANTITATIVE CHEMISTRY — solutions, thermochemistry, electrochemistry, FAUX=0 (formula/concept 2026-06-29). | molarite, dilution, volume_dilution, concentration_massique, enthalpie_reaction, est_exothermique, potentiel_cellule, est_spontanee |
| `choix_social` | TIER 2 — SOCIAL CHOICE (Condorcet paradox, Arrow's theorem): | matrice_majorite, bat, gagnant_condorcet, cycle_condorcet, gagnant_pluralite, gagnant_borda, analyse, formule |
| `chomage` | chomage.py — Labour market: | population_active, taux_chomage, taux_activite, taux_emploi |
| `choquet` | TIER 2 — CHOQUET INTEGRAL & NON-ADDITIVE MEASURES (capacities): | capacite_additive, capacite_croyance, conjuguee, choquet, est_capacite, encadre_esperance, formule |
| `chronobiologie` | chronobiologie.py — Circadian rhythms and sleep cycles (established facts + arithmetic). | periode_circadienne, nombre_cycles_sommeil, duree_pour_cycles, phase_circadienne |
| `citoyennete` | CITIZENSHIP (RIGHTS AND DUTIES) — ESTABLISHED catalogue, not an invention. | categorie, est_droit, est_devoir, age_majorite_civique, elements |
| `classes_complexite` | COMPLEXITY CLASSES (P, NP, NP-complete, NP-hard, undecidable) — CATALOGUE of ESTABLISHED facts, FAUX=0 (formula/concept mis | classe_probleme, est_dans_p, est_np_complet, est_np_difficile, est_indecidable, dans_np, verification_polynomiale, relation_classes |
| `classif_calibree` | TIER 2 — CALIBRATED CLASSIFICATION (brick 4, 2026-06-25). | class Calibrateur, ajuste_isotonique, predit, formule |
| `classif_multiclasse` | TIER 2 — CALIBRATED MULTI-CLASS CLASSIFICATION (brick 7, 2026-06-25). | class CalibrateurMC, ajuste_multiclasse, predit, brier_multiclasse, formule |
| `classification_surfaces` | classification_surfaces.py — Classification of CLOSED surfaces (2D case, fully solved). | genre, classifie_surface, est_sphere |
| `classifieur_domaine` | DOMAIN-NATURE CLASSIFIER — the GAP of [[project-ia-domaines-realite]], the KEYSTONE. | class Reponse, repond |
| `cloud_distribue` | CLOUD / DISTRIBUTED SYSTEMS — EXACT mechanisms, FAUX=0 (formula/concept mission 2026-06-29). | noeud_responsable, quorum_coherent, cap_choix, facteur_replication_disponibilite |
| `coherence_physique` | PHYSICAL COHERENCE — detector of IMPOSSIBILITIES (Yohan's mandate 2026-06-23, inspired by the "Coolzy" announcement). | juge_dispositif, explique |
| `commerce_international` | INTERNATIONAL TRADE — EXACT identities and laws of international exchange (mechanism, never an invented country-value | balance_commerciale, nature_balance, taux_couverture, avantage_comparatif, termes_echange |
| `complexite` | ALGORITHMIC COMPLEXITY — master theorem + asymptotic growth order, EXACT, FAUX=0 (formula/concept mission 2 | exposant_critique, regime_master, classe_master, ordre_croissance, compare_croissance |
| `composites` | COMPOSITES — rule of mixtures, EXACT directly callable primitives, FAUX=0 (formula/concept mission | module_young_composite, densite_composite, borne_inferieure_reuss |
| `compounding` | THE AUTONOMOUS CLIMB (compounding) — the living loop. | route, class PasMontee, resoudre, resoudre_niveau, montee, franchies, etages_atteints |
| `comprehension` | COMPREHENSION (1/2) — abstracting by compression (the "sleep"). | class Abstraction, abstrais, class Predicteur, confirme |
| `comprehension_integree` | INTEGRATED COMPREHENSION — the AI reads ONE sentence and understands it end to end (2026-06-18, Yohan's night mandate). | comprend |
| `comptabilite` | comptabilite.py — Accounting (rules): | equation_bilan, resultat_net, fonds_roulement, ratio_liquidite, partie_double |
| `concentration` | TIER 2 — CONCENTRATION BOUNDS (Hoeffding, empirical-Bernstein): | hoeffding, empirical_bernstein, gaussien, intervalle, formule |
| `confidentialite_differentielle` | TIER 2 — DIFFERENTIAL PRIVACY (Laplace mechanism, ε-DP): | laplace, mecanisme, echelle_bruit, perte_confidentialite, ratio_log_max, composition, borne_avantage, analyse |
| `conformal` | TIER 2 — CONFORMAL PREDICTION (brick 3, 2026-06-25). | quantile_conforme, intervalle_conforme, ensemble_conforme, formule |
| `conformal_adaptatif` | TIER 2 — ONLINE ADAPTIVE CONFORMAL (brick 6, 2026-06-25). | class ConformeAdaptatif, formule |
| `conformal_jackknife` | TIER 2 — CONFORMAL JACKKNIFE+ (brick 20, 2026-06-25). | intervalle_jackknife_plus, jackknife_plus_moyenne, formule |
| `conformal_label` | TIER 2 — LABEL-CONDITIONAL CONFORMAL (per-class Mondrian, brick 22, 2026-06-25). | ajuste_label, ensemble_label, formule |
| `conformal_normalise` | TIER 2 — HETEROSCEDASTIC CONFORMAL (brick 9, 2026-06-25). | class ConformeMondrian, intervalle_normalise, formule |
| `conformal_pondere` | TIER 2 — WEIGHTED CONFORMAL UNDER COVARIATE SHIFT (brick 17, 2026-06-25). | quantile_pondere, intervalle_pondere, poids_ratio_gaussien, formule |
| `conformal_quantile` | TIER 2 — CQR: | scores_cqr, correction_cqr, ajuste_cqr, intervalle_cqr, formule |
| `conjonction` | TIER 2 — CONJUNCTION FALLACY (Linda problem) & COHERENCE OF JUDGMENTS: | bornes_frechet, coherent, sophisme_conjonction, livre_hollandais, analyse, formule |
| `conjugaison` | REGULAR FRENCH CONJUGATION — ESTABLISHED rules of grammar (the MECHANISM is exact, never guessed). | groupe, terminaisons_present, conjugue |
| `conservation` | CONSERVATION BALANCE — Wave 3 brick (physical anchoring). | bilan, viole_conservation, rendement |
| `conservation_aliments` | FOOD PRESERVATION — catalogue of ESTABLISHED methods and thresholds (Yohan's mandate: | methode, methodes, zone_danger_temperature, dans_zone_danger, activite_eau_limite, bacteries_inhibees |
| `contrainte` | CONSTRAINT SOLVER (CSP) — Wave 2 founding brick. | class Contrainte, class CSP |
| `controle` | AUTOMATIC CONTROL — stability of a linear system, FAUX=0 (formula/concept mission 2026-06-29). | table_routh, est_stable, changements_de_signe |
| `controle_qualite` | QUALITY CONTROL — statistical process control (SPC), EXACT primitives, FAUX=0. | indice_capabilite_cp, cpk, limites_controle, phi, ppm_hors_specs, six_sigma_ppm |
| `conversation` | PERSISTENT CONVERSATION MEMORY — "that it remembers conversations: | class MemoireConversation, ajoute, reprend, rappelle |
| `convertit_kaikki` | CONVERTIT_KAIKKI — bridge from a kaikki.org dump (structured Wiktionary) to the `charge_lexique` format (2026-06-18). | genre_grammatical, genus, convertit_entree, convertit, aretes_isa |
| `coordination` | COORDINATION / COMPLEXES — coordination chemistry, EXACT mechanism, FAUX=0 (formula/concept 2026-06-29). | charge_ligand, denticite, nombre_oxydation_metal, nombre_coordination, compte_electrons_18, respecte_regle_18 |
| `copules` | TIER 2 — COPULAS & TAIL DEPENDENCE: | borne_inf, borne_sup, independance, clayton, lambda_inf_clayton, echantillon_clayton, proba_jointe_extreme, proba_jointe_independance |
| `cosmologie` | COSMOLOGY — Expansion of the universe: | vitesse_recession, distance_hubble, age_univers, decalage_rouge |
| `cout_irrecuperable` | TIER 2 — SUNK COST FALLACY (Concorde effect): | continuer_rationnel, continuer_cout_irrecuperable, payoff_forward, escalade_concorde, analyse, formule |
| `covariance_grande_dim` | TIER 2 — HIGH-DIMENSIONAL COVARIANCE (Marchenko-Pastur, Ledoit-Wolf shrinkage): | valeurs_propres, covariance_echantillon, bornes_marchenko_pastur, retrecissement, conditionnement, frobenius, max_correlation_hors_diag, analyse |
| `croissance_bacterienne` | BOUNDED BACTERIAL GROWTH — exponential growth by doubling model, EXACT mechanism. | population, temps_generation, nombre_generations |
| `croyance_dempster_shafer` | TIER 2 — BELIEF FUNCTIONS (Dempster-Shafer): | cadre, belief, plausibility, intervalle_croyance, conflit, combine_dempster, combine_yager, combine |
| `cryobiologie` | cryobiologie.py — Freezing and preservation (cryobiology). | vitesse_refroidissement, point_congelation_solution, azote_liquide |
| `cryptographie_appliquee` | APPLIED CRYPTOGRAPHY — symmetric ciphers, FAUX=0 (formula/concept mission 2026-06-29). | chiffre_cesar, dechiffre_cesar, chiffre_vigenere, dechiffre_vigenere, chiffre_xor |
| `curateur` | Brick 8 — THE CURATOR. | class RapportTache, valide_tache, class CurateurGradue |
| `cybernetique` | BOUNDED CYBERNETICS — regulation & feedback (control loop), "FORMULA" block (Yohan's mandate: | gain_boucle_fermee, erreur_statique, fonction_sensibilite, transfert_complementaire, gain_ideal, est_stable, effet_retroaction_negative |
| `cycles_biogeochimiques` | BIOGEOCHEMICAL CYCLES — residence time, reservoir balances and a catalogue of the major cycles (compute/proof capability | temps_residence, bilan_equilibre, cycles_connus, cycle |
| `cycles_economiques` | cycles_economiques.py — ESTABLISHED catalogue of the economic cycle (business cycle). | phases, phase_cycle, phase_suivante, definition_recession, est_recession_technique, type_indicateur, definition_indicateur, indicateurs |
| `decidabilite` | decidabilite.py — Decidability / undecidability of a statement (decision problem). | statut_decidabilite, est_decidable, classe_complexite, reference, catalogue |
| `decision` | TIER 2 — DECISION UNDER CALIBRATED UNCERTAINTY (brick 8, 2026-06-25). | utilites_attendues, decide, formule |
| `decision_ambiguite` | TIER 2 — DECISION UNDER AMBIGUITY: | eu, valeur_maxmin, valeur_maxmax, valeur_hurwicz, regret_pire, choisir, e_admissibles, domine |
| `decouverte_loi` | SYMBOLIC LAW DISCOVERY — Wave 4 brick. | decouvre |
| `deduction` | DEDUCTION ENGINE — the memory that REASONS (not merely recalls). | class Regle, class MoteurDeduction |
| `delta_debug` | DELTA-DEBUGGING (ddmin) — failure-reproducer minimization (advanced-code brick, 2026-07-02). | ddmin, est_1_minimal, minimise_texte |
| `demande` | DEMANDE — THE QUERY INTERFACE ("speech", 2026-06-17, Yohan's reframing "one must be able to ASK it things, | construit_moteur, class Reponse, demande, class AssistantIA |
| `demo_anglais` |  | main |
| `demo_verax` | Provara DEMO — "Either it knows, or it says so. | titre, q, calcule, main |
| `demographie` | demographie.py — Demography (populations, facts): | taux_croissance_naturel, densite_population, temps_doublement, taux_dependance, indice_fecondite |
| `derive_calibration` | TIER 2 — CALIBRATION DRIFT DETECTOR (brick 13, 2026-06-25). | class DetecteurDerive, formule |
| `deux_enveloppes` | TIER 2 — TWO-ENVELOPE PARADOX: | p_petite_sachant, gain_conditionnel, esperance_gain_inconditionnel, simule, analyse, formule |
| `diable` | THE DEVIL'S TEST — "everything serves, in the WHOLE" (2026-06-17). | partie_A, partie_B, partie_C, main, partie_A_rapport |
| `dimensions` | DIMENSIONAL ALGEBRA — founding brick (Wave 1, representation foundation). | class Dimension, homogene, verifie_somme, verifie_egalite, class Unite, convertit, dimension_de, commensurables |
| `dirichlet_imprecis` | TIER 2 — IMPRECISE DIRICHLET MODEL (IDM, Walley 1996): | bornes, intervalle_evenement, mle, laplace, predictif_credal, estime, formule |
| `dirichlet_process` | TIER 2 — DIRICHLET PROCESS / nonparametric clustering: | crp_predictive, esperance_nb_tables, gibbs_dp, nb_clusters, assignation_k_fixe, masse_nouveaute_dp, analyse, formule |
| `dkw` | TIER 2 — DKW CONFIDENCE BAND (Dvoretzky-Kiefer-Wolfowitz ; Massart constant): | epsilon, bande, F_n, F_inf, F_sup, ks_statistique, couvre, intervalle_quantile |
| `document_pdf` | PDF DOCUMENT — BOUNDED core of the PRINTABLE DOCUMENT modality (PDF 1.4), pure stdlib (2026-07-02). | class Page, class Document, encode, ecris, lit_xref |
| `donnees_manquantes` | TIER 2 — MISSING DATA: | cas_complet, imputation_multiple, imputation_simple, formule |
| `drake` | DRAKE — Search for life (SETI): | nombre_civilisations |
| `dunning_kruger` | TIER 2 — DUNNING-KRUGER EFFECT AS A STATISTICAL ARTIFACT: | simule, moyennes_par_quartile, pente_ecart_competence, analyse, formule |
| `e_process` | TIER 2 — E-PROCESS / TESTING BY BETTING (e-values, Ville): | e_process_simple, e_process_melange, seuil, p_anytime, test_sequentiel, formule |
| `echafaudage` | G3 — REMOVE THE SCAFFOLDING AND MEASURE (the ablation). | couverture, briques, retire, ablation, minimal |
| `echantillon_pondere` | TIER 2 — ESTIMATION UNDER SAMPLING BIAS (Horvitz-Thompson / Hájek, brick 28, 2026-06-25). | estime_hajek, estime_ht, n_effectif, intervalle_hajek, formule |
| `eclipses` | eclipses.py — Mechanics of lunar phases and eclipse conditions. | periode_synodique, phase_lune, fraction_illuminee, condition_eclipse |
| `ecologie` | BOUNDED ECOLOGY — ecosystems & food chains: | energie_niveau, efficacite_ecologique, derivee_proie, derivee_predateur, equilibre_lotka_volterra, proie_equilibre, predateur_equilibre |
| `editeur` | REPOSITORY EDITOR — DETERMINISTIC substrate for creating/modifying files, FAUX=0 (sovereign, stdlib, offline). | empreinte, class Depot |
| `electronique` | ELECTRONICS (circuits) — COMPUTABLE quantities, FAUX=0 (formula/concept mission 2026-06-29). | resistance_serie, resistance_parallele, diviseur_tension, constante_temps_rc, impedance_condensateur, impedance_bobine, frequence_resonance_lc |
| `ellsberg` | TIER 2 — ELLSBERG PARADOX (ambiguity aversion / sure-thing principle): | paris_eu, schema_ellsberg, paris_maxmin, analyse, formule |
| `energies_comparees` | energies_comparees.py — Energy comparison of fossil vs renewable. | facteur_charge, contenu_energetique, retour_energetique, emissions_co2, facteur_co2_reference |
| `ensemble_calibre` | TIER 2 — CALIBRATED ENSEMBLE (stacking of forecasters, brick 15, 2026-06-25). | moyenne_ponderee, class EnsembleCalibre, ajuste_ensemble, formule |
| `entrainement` | entrainement.py — Training physiology: | un_rep_max_epley, frequence_cardiaque_max, zone_cible_karvonen, vo2max_estime |
| `entropie_thermo` | SECOND LAW (ENTROPY) — EXACT thermodynamic primitives, directly callable, FAUX=0 (formula/concept mis | variation_entropie, entropie_univers, spontane |
| `environnement` | ENVIRONMENT & POLYGLOT PORTFOLIO — the brick that "sorts languages by need" (2026-07-02, Yohan's vision). | detecte, disponibles, executeurs_disponibles, pour_besoin, suggestions_install, peut_installer |
| `equa_diff` | DIFFERENTIAL EQUATIONS — analytical and numerical solutions, FAUX=0 (formula/concept mission 2026-06-29). | solution_exponentielle, solution_affine, demi_vie, euler |
| `equilibre_chimique` | CHEMICAL EQUILIBRIA — reaction quotient and direction of evolution, FAUX=0 (formula/concept mission 2026-06-29). | quotient_reaction, sens_evolution, deplace_equilibre_temperature |
| `equivalence_semantique` | SEMANTIC EQUIVALENCE OF FUNCTIONS — deciding whether two functions compute the SAME thing (advanced code, 2026-07-02). | sur_domaine, par_echantillon, equivalent |
| `ergodicite` | TIER 2 — ERGODICITY: | moyenne_ensemble, taux_croissance_temporel, trajectoire_multiplicative, trajectoire_additive, analyse, formule |
| `erreurs_variables` | TIER 2 — ERRORS-IN-VARIABLES: | pente_ols, fiabilite, pente_corrigee, pente_corrigee_ic, pente_ols_ic, formule |
| `essais_cliniques` | CLINICAL TRIALS — clinical epidemiology (EXACT effect measures). | risque_relatif, reduction_risque_absolue, nombre_sujets_a_traiter, odds_ratio |
| `etat` | STATES & VARIABLES — Wave 1 brick. | class ValeurHorsDomaine, class Variable, class Etat, class EspaceEtats |
| `etats_matiere` | STATES OF MATTER — physical state as a function of temperature, FAUX=0 (formula/concept mission 2026-06-29). | etat_physique, celsius_vers_kelvin, kelvin_vers_celsius, celsius_vers_fahrenheit, fahrenheit_vers_celsius, nombre_changements_etat |
| `etend_savoir` | ETEND_SAVOIR — self-extension of knowledge by TRANSITIVE CLOSURE from kaikki (§6.2 b/c, 2026-06-18). | frontiere, acyclise, etend, chaine, raisonneur, main |
| `executeur` | THE MULTI-LANGUAGE SEAM — the Executor. | class Executeur, class ExecuteurPython, class ExecuteurJS, class ExecuteurPerl, class ExecuteurBash, class ExecuteurC, class ExecuteurCpp, class ExecuteurRust |
| `executeur_niches` | NICHE EXECUTORS — Prolog / R / SQL: | class ExecuteurProlog, class ExecuteurR, class ExecuteurSQL |
| `exercices` | THE CURATED EXERCISE BATCH — the raw material, supplied from OUTSIDE. | — |
| `exp3` | TIER 2 — ADVERSARIAL BANDIT (EXP3): | gamma_optimal, exp3, glouton, meilleur_bras_fixe, regret, joue, formule |
| `exploits` | Brick 5 — THE EXPLOIT OBSERVATORY. | sonde_statique, class Diagnostic, caracterise, class Incident, class Inspecteur |
| `exporte_dataset` | EXPORTE_DATASET — the LEARN link, without a GPU (2026-06-17, "making the AI ready to learn"). | exporte, resume |
| `externalites` | ECONOMICS OF EXTERNALITIES — mechanism + catalogue of sourced examples (manual microeconomics consensus). | type_externalite, cout_social, taxe_pigou, defaillance_marche, internalisee |
| `extraction` | EXTRACTION FROM DIRTY SOURCES (text -> triples) — Wave 8 brick. | extrait, extrait_surs |
| `fabrique_comprehension` | FABRIQUE_COMPREHENSION — the VERIFIED training corpus of all comprehension (2026-06-18, capstone of the mandate). | fabrique |
| `fabrique_francais` | FABRIQUE_FRANCAIS — VERIFIED French dataset, model-free (2026-06-18, Yohan's idea "train in French" + LEARN leap | instruction, fabrique, resume |
| `fabrique_semantique` | FABRIQUE_SEMANTIQUE — VERIFIED French COMPREHENSION dataset (2026-06-18, "the official definition = the truth"). | construit_paires, fabrique, resume |
| `fait_negatif` | FIRST-CLASS NEGATIVE FACT (module `fait_negatif`) — distinguishing the KNOWN-FALSE from the UNKNOWN (representation, 2026-07-02). | statut_fait, negatifs_certains, coherent |
| `faits_appris` | LEARNED WEB FACTS — persistent local memory of STRUCTURED facts found online (Wikidata), reusable offline, attributed + dated (2026-07-06). FAUX=0: free text is never learned. | apprend, rappelle, rappelle_texte, nombre_appris |
| `falsification` | ACTIVE FALSIFICATION — Wave 6 brick (Popper: | refute, corrobore, resiste |
| `fdr_controle` | TIER 2 — FALSE DISCOVERY RATE CONTROL (multiplicity of TESTS, Benjamini-Hochberg) (brick, 2026-06-26). | naif, bonferroni, benjamini_hochberg, decouvre, formule |
| `fermi` | TIER 2 — ORDER-OF-MAGNITUDE (FERMI) ESTIMATION WITH UNCERTAINTY (brick 29, 2026-06-25). | estime_fermi, estime_fermi_mc, formule |
| `fonction_nl` | NL ROUTING → FUNCTION SUBSYSTEMS (LIGHTWEIGHT module — no reader). | resout_physique, resout_conversion, resout_arithmetique, resout_fonction |
| `fractales` | FRACTALS — self-similarity dimension, EXACT and directly callable primitive, FAUX=0 (formula/concept mission 2026 | dimension_similarite, dimension_connue, fractales_connues |
| `fraicheur` | FRESHNESS / TEMPORAL PROVENANCE — Wave 8 brick. | class FaitDate, a_rafraichir, frais |
| `frame` | REIFIED N-ARY FRAME — Wave 1 brick (role-bearing relation). | register_schema, class RoleInconnu, class Frame |
| `fuzz` | Brick 6 — THE SECURITY SIEVE (differential fuzzing). | class RapportFuzz, crible |
| `galois` | GALOIS THEORY — ESTABLISHED facts, EXACT mechanism, FAUX=0 (formula/concept mission 2026-06-29). | indicatrice_euler, resoluble_par_radicaux, groupe_symetrique_resoluble, groupe_resoluble, groupe_alterne_resoluble, ordre_groupe_symetrique, ordre_groupe_alterne, ordre_groupe_galois_cyclotomique |
| `garde_ressources` | RESOURCE GUARD — hard kernel net so that exploration NEVER brings down WSL (2026-06-19). | pmap, borne |
| `generateur` | Brick 3 — THE GENERATOR. | class Generateur, class GenerateurFactice, class GenerateurApprenant, class GenerateurAmeliorant, class GenerateurAleatoire, class GenerateurBriques, fragments_riches, class GenerateurRecombinant |
| `generation_coherente` | COHERENT GENERATION — the AI produces COMPLETE and TOTALLY COHERENT SENTENCES (2026-06-18, Yohan's mandate). | class Ecrivain |
| `genetique` | BOUNDED MOLECULAR GENETICS (Yohan's mandate 2026-06-23: | complement_adn, complement_inverse, transcrit, codon_vers_aa, traduit, repond_nl |
| `genie_chimique` | CHEMICAL ENGINEERING — reactors and distillation, FAUX=0 (formula/concept mission 2026-06-29). | temps_sejour, conversion_cstr_ordre1, conversion_pfr_ordre1, etages_fenske |
| `geometrie2d` | CONSTRUCTIVE 2D GEOMETRY — BOUNDED core of drawing / plans / vector images (modality, 2026-07-02). | class Point, class Affine, class Polygone, class Cercle, scene_svg |
| `geometrie3d` | CONSTRUCTIVE 3D GEOMETRY — BOUNDED core of 3D modelling / plans (modality, 2026-07-02). | class Point3D, class Affine3D, class Maillage, cube |
| `geometrie_differentielle` | DIFFERENTIAL GEOMETRY — EXACT primitives on plane parametric curves, FAUX=0 (formula/concept mission 2026-0 | courbure, courbure_graphe, rayon_courbure, longueur_arc_segment, longueur_polyligne, tangente_unitaire, normale_unitaire |
| `geometrie_projective` | PROJECTIVE GEOMETRY — cross-ratio and invariants, FAUX=0 (formula/concept mission 2026-06-29). | birapport, homographie, est_division_harmonique, conjugue_harmonique |
| `geometries_non_euclidiennes` | NON-EUCLIDEAN GEOMETRIES — SPHERICAL geometry (constant positive curvature). | courbure_gauss_sphere, exces_spherique, somme_angles_triangle_spherique, aire_triangle_spherique |
| `geotechnique` | GEOTECHNICS — soil mechanics, FAUX=0 (formula/concept mission 2026-06-29). | contrainte_verticale, contrainte_effective, coefficient_poussee_active, coefficient_poussee_passive, poussee_active |
| `gestion_risque` | gestion_risque.py — Risk management (finance / insurance): | esperance_perte, value_at_risk_parametrique, ratio_sharpe, variance_portefeuille_2_actifs, ecart_type_portefeuille_2_actifs, prime_pure |
| `gibbard_satterthwaite` | TIER 2 — GIBBARD-SATTERTHWAITE THEOREM (strategic voting): | borda, pluralite, majorite2, prefere, trouve_manipulation, taux_manipulables, analyse, formule |
| `glaciologie` | glaciologie.py — Glaciology: | bilan_massique, vitesse_deformation_glace, epaisseur_equilibre, fraction_emergee_iceberg |
| `godel` | GÖDEL — Gödel numbering (bijective TECHNICAL core, exact) + statements of the incompleteness theorems as FACTS. | code_symbole, godel_numero, decode_godel, theoreme |
| `good_turing` | TIER 2 — GOOD-TURING / MISSING MASS & UNSEEN SPECIES: | frequences_de_frequences, masse_manquante, richesse_chao1, proba_inedit_naive, logloss_inedit, analyse, formule, echantillon_zipf |
| `goodhart` | TIER 2 — GOODHART'S LAW: | correlation, simule, analyse, formule |
| `grandeur` | TYPED QUANTITY — Wave 1 brick (value + unit/dimension + uncertainty). | class IncoherenceDimensionnelle, class Grandeur, homogene |
| `grandeur_vectorielle` | DIMENSIONED VECTOR QUANTITY — non-scalar quantities (representation brick, 2026-07-02). | class GrandeurVectorielle |
| `graphe_monde` | TYPED RELATIONAL GRAPH (navigable view of the corpus) — promotion of the 🟡 brick (2026-07-02). | est_entite, sortants, voisins, chaine, chemin, verifie_chemin |
| `graphique` | DATA CHART — BOUNDED core of PLOTTING (bar/line/scatter), pure stdlib (2026-07-02). | class Echelle, bornes, class Rect, class Pt, class Disposition, barres, nuage, courbe |
| `groupes` | GROUP THEORY (finite) — EXACT computations, FAUX=0 (formula/concept mission 2026-06-29). | ordre_element_zn, compose_permutations, ordre_permutation, signature_permutation, est_groupe, lagrange_divise |
| `habitabilite` | BOUNDED HABITABILITY — circumstellar habitable zone & equilibrium temperature (Yohan's mandate: | temperature_equilibre, zone_habitable, flux_stellaire_recu, dans_zone_habitable |
| `harvester` | HARVESTER — industrializes the FAUX=0 DISCOVERY+CLASSIFICATION of ingestion veins (Lever 3, night 2026-06-29). | type_propriete, route, propose |
| `heraldique` | HERALDRY — BOUNDED core of the rules of the coat of arms (CLOSED convention), pure stdlib (2026-07-02). | categorie, teintes_modernes, contraste_valide, teintures |
| `hierarchie_normes` | HIERARCHY OF NORMS — Kelsen's pyramid (French / continental law, ESTABLISHED hierarchy). | rang, superieur, inferieur, meme_rang, conforme, domine, hierarchie |
| `homeostasie` | HOMEOSTASIS — regulation by negative feedback (BOUNDED domain, EXACT mechanism). | ecart_consigne, correction, est_regule, consigne_reference |
| `hydraulique` | HYDRAULICS — fluid flow, FAUX=0 (formula/concept mission 2026-06-29). | debit_volumique, vitesse_continuite, nombre_reynolds, regime_ecoulement, charge_bernoulli |
| `hydrologie` | HYDROLOGY (inland waters) — flows and discharges COMPUTABLE by established formula. | debit, methode_rationnelle, ruissellement, manning_vitesse, temps_concentration |
| `identite` | UNIFIED CANONICAL IDENTITY — Wave 1 founding brick. | class PreuveRequise, class RegistreIdentite |
| `immunite` | IMMUNITY / VACCINES — BOUNDED MECHANISM (subject "Vaccines (mechanism)"). | seuil_immunite_groupe, taux_reproduction_effectif, epidemie_eteinte, type_immunite |
| `importance_sampling` | TIER 2 — IMPORTANCE SAMPLING & EFFECTIVE SAMPLE SIZE (ESS): | normal_pdf, poids, estimateur, ess, erreur_naive, intervalle_naif, analyse, formule |
| `impression_3d` | 3D PRINTING (FDM) — slicing parameters COMPUTABLE by established formula (Yohan's mandate: | nombre_couches, temps_impression, masse_filament, longueur_filament |
| `incertitude` | PHASE 2 — UNBOUNDED: | estime_moyenne, estime_proportion, compare_moyennes, predit_intervalle, est_anormal, tendance, formule |
| `incertitude_decomposee` | TIER 2 — EPISTEMIC / ALEATORIC DECOMPOSITION (brick 38, 2026-06-25). | decompose_echantillon, decompose_ensemble, intervalle_predictif, formule |
| `induction_horn` | HORN RULE INDUCTION (bounded ILP) — producing VALIDATED rules for deduction.py (2026-07-02). | derive, cloture_derives, evalue, induit |
| `industrie40` | industrie40.py — Automation / Industry 4.0. | disponibilite, performance, qualite, oee, est_classe_mondiale |
| `inference_anytime` | TIER 2 — ANYTIME-VALID INFERENCE (confidence sequence, brick 35, 2026-06-25). | rayon_cs, class SequenceConfiance, formule |
| `inflation` | INFLATION — EXACT definitions and computations (established mechanism, FAUX=0). | taux_inflation, pouvoir_achat, valeur_reelle, taux_reel, taux_reel_exact |
| `info_gap` | TIER 2 — INFO-GAP DECISION (Ben-Haim): | pire_cas, meilleur_cas, robustesse, opportunite, choisis, formule |
| `information_calcul` | INFORMATION THEORY (Shannon) — COMPUTABLE quantities, FAUX=0 (formula/concept mission 2026-06-29). | entropie, entropie_conjointe, information_mutuelle, divergence_kl |
| `intervalle_tolerance` | TIER 2 — TOLERANCE INTERVAL (containing a PROPORTION of the population, not the mean) (brick, 2026-06-26). | facteur_tolerance, intervalle_tolerance, intervalle_naif, ic_moyenne, formule |
| `intrication` | QUANTUM ENTANGLEMENT — Bell inequality / CHSH test (Yohan's mandate: | borne_classique_chsh, borne_quantique_chsh, valeur_chsh, viole_inegalite_bell, etat_bell_correlation |
| `invention_atomes` | BRIDGE FROM THE INVENTION ENGINE → ATOM CONTRACT (2026-07-02). | atome_derivable, atome_temoin, atome_generatif, invente_attribut, invente_dispositif |
| `invention_divergente` | DIVERGENT INVENTION — wiring of the 6 bricks that invent OUTSIDE the recombination of the existing (2026-07-02). | apprend_loi, leve_contrainte, transfere_analogie, arbitre_compromis, explique_observations, plan_procede, Operateur |
| `jensen` | TIER 2 — JENSEN'S INEQUALITY / "FLAW OF AVERAGES": | gap_jensen, analyse, formule |
| `jeux_appliques` | APPLIED GAME THEORY — equilibria of classic games in PURE strategies (m×n bimatrix, focus 2×2). | meilleure_reponse_J1, meilleure_reponse_J2, equilibre_nash_pur, strategie_dominante, pareto_domine, dilemme_prisonnier, bataille_des_sexes, matching_pennies |
| `jeux_zero_somme` | TIER 2 — ZERO-SUM GAMES & SECURITY STRATEGY (maximin, von Neumann minimax theorem) (brick 70, 2026-06-27) | securite_ligne, plafond_colonne, meilleure_reponse_ligne, jeu_fictif, analyse, formule |
| `journalisme_deontologie` | JOURNALISM (ETHICS) — catalogue of the established duties of the journalist. | liste_principes, principe, respecte_deontologie, est_conforme, principe_concerne, evalue |
| `juge` | Brick 1 — THE JUDGE. | class Verdict, class Limites, juge |
| `juge_rapide` | FAST JUDGE (fork-per-candidate) — PYTHON-only path, OPT-IN, verdict BIT-IDENTICAL to the subprocess judge. | juge_fork |
| `jury_condorcet` | TIER 2 — CONDORCET JURY THEOREM / WISDOM OF CROWDS: | precision_majorite, analyse, formule |
| `kalman_robuste` | TIER 2 — ROBUST KALMAN FILTER: | filtre, nis_moyen, diagnostic, steady_state_P, inflation_pour_coherence, analyse, formule |
| `kde` | TIER 2 — KERNEL DENSITY ESTIMATION (KDE) & bandwidth selection: | noyau, densite, log_vraisemblance_loo, silverman, h_optimal, n_modes, analyse, formule |
| `kelly` | TIER 2 — KELLY CRITERION (proportional betting, logarithmic growth): | fraction_kelly, croissance, fortune_finale, conseille, formule |
| `langages_formels` | FORMAL LANGUAGES & GRAMMARS — EXACT, deterministic primitives, FAUX=0 (formula/concept mission 2026-06-29). | non_terminaux, terminaux, est_forme_normale_chomsky, classe_chomsky, appartient |
| `lecteur_client` | Lightweight client of the reader daemon (T9 OPTIM — additive, pure stdlib, NO `import lecteur`). | disponible, cherche, repond_nl |
| `lecteur_daemon` | RESIDENT DAEMON of the reader (T9 OPTIM — additive, pure stdlib). | main |
| `lecture_comprehension` | READING & COMPREHENSION — the AI reads fact-sentences and answers questions by LOGIC (2026-06-18, night capstone). | class Lecteur |
| `lexique_fr` | LEXIQUE_FR — seed of a CERTIFIED French dictionary (2026-06-18, Yohan's idea "the official definition = the truth"). | edges_isa, edges_syn, ancetres |
| `liaisons_chimiques` | CHEMICAL BONDS — nature of the bond by electronegativity, FAUX=0 (formula/concept mission 2026-06-29). | difference_electronegativite, nature_liaison, pourcentage_ionique |
| `limite` | THEORETICAL LIMIT & GAP — Wave 3 brick. | class Limite |
| `lindley` | TIER 2 — LINDLEY'S PARADOX: | probit, z_pour_p, facteur_bayes_01, posterior_h0, analyse, formule |
| `localisation_faute` | FAULT LOCALIZATION + REPAIR BY SEARCH — the debug→fix cycle (advanced code, 2026-07-02). | localise, element_le_plus_suspect, couverture_python, repare |
| `logique_tri` | THREE-VALUED LOGIC + OPEN/CLOSED WORLD (logique_tri) — Wave 1 brick (end of the representation foundation). | class Contradiction, non, et, ou, class BaseTrivaluee |
| `logistique` | logistique.py — Logistics / supply chain: | quantite_economique_commande, point_commande, stock_securite, cout_total_stock |
| `loi` | MANIPULABLE LAWS — Wave 2 founding brick (symbolic/numeric engine). | class Loi, solveur_numerique |
| `loi_grands_nombres` | TIER 2 — MISUNDERSTOOD LAW OF LARGE NUMBERS: | marche, esperance_moyenne, esperance_abs_somme, distribution_temps_en_tete, analyse, formule |
| `loi_puissance` | TIER 2 — HEAVY-TAILED LAWS (power law / Pareto): | pareto, hill, moyenne, ic_tcl, moyenne_theorique, analyse, formule |
| `lord` | TIER 2 — LORD'S PARADOX (change score vs ANCOVA): | genere_groupe, score_changement, ancova, analyse, formule |
| `main_chaude` | TIER 2 — GAMBLER'S FALLACY & HOT HAND (Miller-Sanjurjo bias): | estimateur_naif, conditionnelle_flux_long, biais_miller_sanjurjo, detecte_main_chaude, analyse, formule |
| `malediction_dimension` | TIER 2 — CURSE OF DIMENSIONALITY (concentration of distances): | contraste_distances, coquille_gaussienne, analyse, formule |
| `maritime` | MARITIME — naval architecture, FAUX=0 (formula/concept mission 2026-06-29). | vitesse_coque, vitesse_coque_max, vitesse_coque_depuis_pieds, poussee_archimede, masse_max_flottante, flotte, nombre_froude |
| `marketing_mecanismes` | ADVERTISING / MARKETING (MECHANISMS) — ESTABLISHED models of advertising persuasion (Yohan's mandate: | etape_aida, ordre_aida, rang_aida, principe_cialdini, definition_cialdini, principes_cialdini |
| `marketing_metrics` | marketing_metrics.py — Effectiveness of a campaign (measurable): | taux_conversion, ctr, roi, cac, roas |
| `maths_discretes` | DISCRETE MATHS — EXACT primitives (integers), directly callable, FAUX=0 (formula/concept mission 2026-06-29). | factorielle, binomial, catalan, derangements, partitions, suite_recurrente, fibonacci, lucas |
| `maths_financieres` | FINANCIAL MATHEMATICS (interest) — bounded FORMULA, reality (the definition) judges, never a false one. | interet_simple, valeur_acquise_simple, interet_compose, valeur_acquise, valeur_future, valeur_actuelle, annuite_constante, van |
| `matrice_confusion` | TIER 2 — CONFUSION MATRIX, IMBALANCE & BASE RATE: | confusion, exactitude, precision, rappel, specificite, f1, exactitude_equilibree, mcc |
| `maximum_entropie` | TIER 2 — MAXIMUM ENTROPY PRINCIPLE (Jaynes): | entropie, uniforme, maxent_moyenne, deux_points, analyse, formule |
| `maxwell` | MAXWELL'S EQUATIONS — EXACT quantitative consequences of vacuum electromagnetism. | vitesse_lumiere_calculee, impedance_vide, densite_energie_E, densite_energie_B, densite_energie_totale |
| `mdl` | TIER 2 — MINIMUM DESCRIPTION LENGTH (MDL, Rissanen): | ajuste_poly, rss, codelength, selectionne_mdl, selectionne_train, predit, analyse, formule |
| `mecanique` | MECHANICS (friction, oscillators, fluids) — quantities COMPUTABLE by formula, FAUX=0 (formula/concept 2026-06-29). | force_frottement, pulsation_ressort, periode_ressort, frequence_ressort, periode_pendule, energie_ressort, pression, pression_hydrostatique |
| `mecanismes` | MECHANICAL DESIGN — transmission of motion and force (Yohan's mandate: | rapport_engrenages, vitesse_sortie, avantage_mecanique_levier, couple_sortie |
| `mecanismes_machines` | MACHINES AND MECHANISMS — mobility of a planar mechanism (Grübler–Kutzbach criterion). | mobilite, mouvement_determine, est_structure, nature |
| `mecanismes_reactionnels` | REACTION MECHANISMS — classification of nucleophilic substitutions/eliminations (SN1/SN2/E1/E2) by chemistry RULES | type_substitution, sn2_defavorise_par_encombrement, type_elimination, ordre_cinetique, concerte, passe_par_carbocation, nombre_etapes, stereochimie |
| `medecines_alternatives` | ALTERNATIVE MEDICINES — level of scientific evidence (catalogue of established CONSENSUS). | est_catalogue, pratiques, niveau_preuve, depasse_placebo |
| `memoire_briques` | PERSISTENT BRICK MEMORY — "the AI learns AND RETAINS" (Yohan's mandate 2026-06-24). | class MemoireBriques |
| `memoire_faits` | PERSISTENT INFORMATION MEMORY — "the AI does not lose context over time, WITHOUT terabytes of data, WITHOUT depending | class MemoireFaits |
| `mereologie` | MEREOLOGY (part-whole composition) — Wave 1 brick. | class CycleMereologique, class Assemblage |
| `mesure` | Brick 7 — THE LEARNING METER (the glass box). | class Point, evalue, class Diagnostic, analyse, trace |
| `mesure_structure_pertache` | MEASURE — "STRUCTURE DECIDES PER TASK" pushed to the max (2026-06-19, Yohan's mandate "test all ideas of the same pri | st_rr2, st_stride2, st_stride3, st_occam, st_costweight, st_topfirst, main |
| `mesures_sociales` | SOCIAL MEASURES — MEASURABLE social facts (inequality and poverty statistics, EXACT computations). | mediane, gini, coefficient_gini, taux_pauvrete, seuil_pauvrete, indice_dimension, idh |
| `meta_analyse` | TIER 2 — META-ANALYSIS (random effects, brick 37, 2026-06-25). | meta_analyse, formule |
| `microprocesseurs` | MICROPROCESSORS — logic gates and ALU, FAUX=0 (formula/concept mission 2026-06-29). | porte, additionneur_complet, alu |
| `mineraux` | mineraux.py — Mohs scale (hardness of minerals): | durete_mohs, raye, plus_dur, catalogue |
| `moteur_invention` | INVENTION-DISCOVERY ENGINE — the SEED of Yohan's FINAL OBJECTIVE (cf. | class Verdict, examine_cible |
| `moteur_raisonnement` | REASONING ENGINE — end-to-end WIRING of the bricks (2026-07-02). | class MoteurRaisonnement |
| `multicalibration` | TIER 2 — MULTICALIBRATION: | ajuste, applique, applique_lot, formule |
| `multilabel` | TIER 2 — MULTI-LABEL CALIBRATION (brick 23, 2026-06-25). | class CalibrateurMultiLabel, ajuste_multilabel, seuil_rappel, formule |
| `multinomial_simultane` | TIER 2 — SIMULTANEOUS CONFIDENCE INTERVALS FOR MULTINOMIAL SHARES (brick, 2026-06-26). | marginaux, simultanes_bonferroni, simultanes_quesenberry_hurst, intervalles, formule |
| `mutation_testing` | MUTATION TESTING — measuring the ADEQUACY of a test suite (advanced code, 2026-07-02). | analyse, suite_adequate |
| `mutations` | MUTATIONS — classification of DNA mutations + effect of a substitution on translation. | type_mutation, effet_substitution_codon, decrit_substitution |
| `navigation` | NAVIGATION — orientation & positioning on the globe, FAUX=0 (formula/concept mission). | distance_orthodromique, haversine, cap_initial |
| `neurone_biologique` | neurone_biologique.py — Biological neural networks (integrate-and-fire model). | potentiel_repos, depasse_seuil, frequence_decharge, frequence_max_refractaire, frequence_decharge_bornee |
| `no_free_lunch` | TIER 2 — NO FREE LUNCH THEOREM (Wolpert-Macready): | majorite_train, erreur_hors_echantillon, erreur_moyenne, erreur_sur_classe, analyse, formule |
| `nombres_complexes` | COMPLEX ANALYSIS — operations on complex numbers, FAUX=0 (formula/concept mission 2026-06-29). | module, argument, conjugue, somme, produit, quotient, puissance, racines_nieme |
| `nomenclature_chimique` | BOUNDED CHEMICAL NOMENCLATURE — naming SIMPLE compounds (IUPAC rules, established facts). | prefixe, nom_element, nom_compose_binaire, formules_connues |
| `nouveaute` | TIER 2 — NOVELTY / OUT-OF-DISTRIBUTION DETECTION (brick 11, 2026-06-25). | pvaleur_conforme, est_nouveau, scoreur_knn, formule |
| `nucleosynthese` | NUCLEOSYNTHESIS — bounded nuclear energy (mass↔energy equivalence, mass defect, binding energy). | energie_liaison, energie_liaison_par_nucleon, q_reaction, pic_fer |
| `ontologie` | ONTOLOGY / TYPE SYSTEM (subsumption over the data) — promotion of the 🟡 brick (2026-07-02). | ancetres, est_un, plus_proche_commun, cycle |
| `opinions` | TIER 2 — AGGREGATION OF EXPERT OPINIONS (brick 25, 2026-06-25). | pool_lineaire, pool_log, poids_fiabilite, combine, formule |
| `optimisation_bayesienne` | TIER 2 — BAYESIAN OPTIMIZATION (Gaussian-process surrogate + acquisition) (brick, 2026-06-26). | acquisition_ucb, acquisition_ei, propose_prochain, optimise, formule |
| `oracle_definitions` | ORACLE DEFINITIONS — the official definition = truth, hence self-construction of knowledge (2026-06-18, Yohan's insight: | genre_de, construit_isa, class Savoir |
| `orchestrateur_invention` | MULTI-MODE INVENTION ORCHESTRATOR — the CAPSTONE of the HOW layer (2026-07-02). | class OrchestrateurInvention |
| `ordinaux` | ORDINALS & CARDINALS — EXACT arithmetic, FAUX=0 (formula/concept mission). | fini, omega_puissance, addition_ordinale, multiplication_ordinale, compare_ordinaux, est_fini, est_limite, est_successeur |
| `p_box` | TIER 2 — P-BOXES (probability boxes): | class PBox, depuis_intervalles, cdf_precise, formule |
| `p_hacking` | TIER 2 — P-HACKING / GARDEN OF FORKING PATHS: | p_bilateral, cdf_p_min, prob_au_moins_un_significatif, p_ajuste_sidak, p_ajuste_bonferroni, analyse, formule |
| `pac_bayes` | TIER 2 — PAC-BAYES BOUNDS: | kl_bernoulli, kl_inverse, kl_distributions, risque, borne, borne_mcallester, gibbs, formule |
| `paradoxes` | paradoxes.py — Logical paradoxes (liar, Russell, etc.). | est_autoreferentiel, ensemble_russell_paradoxal, barbier_paradoxal, menteur_paradoxal, grelling_paradoxal, est_heterologique, catalogue |
| `pareto` | MULTI-OBJECTIVE OPTIMIZATION / PARETO FRONT — Wave 5 brick. | domine, front, domines |
| `parrondo` | TIER 2 — PARRONDO'S PARADOX: | joue, joue_motif, derive_motif, derive_moyenne, analyse, formule |
| `parseur_fichiers` | FILE-FORMAT ROUTER — "read and understand all file types" (modality, 2026-07-02). | detecte_type, lit, formats_supportes |
| `pascal_mugging` | TIER 2 — PASCAL'S PROBLEM (Pascal's mugging) / UNBOUNDED UTILITY: | paye_naif, paye_borne, proba_levier, paye_levier, analyse, formule |
| `pedologie` | pedologie.py — Pedology (soil science): | classe_texture, porosite |
| `petits_nombres` | TIER 2 — LAW OF SMALL NUMBERS & ranking by raw rate: | taux_brut, moyenne_globale, kappa_optimal, retrecissement, analyse, formule |
| `petrochimie` | petrochimie.py — Oil refining: | fraction_distillation, indice_octane_melange, coupes |
| `pharmacochimie` | pharmacochimie.py — Lipinski's rule of five (druglikeness). | nombre_violations, respecte_lipinski, est_drug_like, indice_lipinski |
| `physique` | BOUNDED PHYSICS — quantities COMPUTABLE by formula (Yohan's mandate: | grandeurs, calcule |
| `pib` | GDP, GROWTH — national-accounting identities (EXACT mechanism, never an invented country-value). | pib_depenses, taux_croissance, pib_par_habitant, pib_reel |
| `planification` | MULTI-STEP PLANNING — Wave 5 brick. | class Operateur, plan, atteignable |
| `plastiques` | POLYMERS / PLASTICS — identification and properties (Yohan's mandate: | code_recyclage, nom_depuis_code, classe_thermique, est_thermoplastique, est_thermodurcissable, temperature_transition_vitreuse, nom_complet |
| `poisson` | TIER 2 — POISSON RATE ESTIMATION (counts, brick 36, 2026-06-25). | estime_taux, proba_compte, proba_au_moins, formule |
| `poisson_nonhomogene` | TIER 2 — NON-HOMOGENEOUS POISSON PROCESS (variable intensity λ(t), brick 44, 2026-06-26). | intensite_bins, comptage, intervalle_comptage, predit_fenetre, formule |
| `polyglotte` | MULTI-LANGUAGE GENERATION (2026-06-17, Yohan's choice "multi-language generation") — the AI no longer writes only Python | class GenerateurPolyglotte, class ReponseLang, demande_lang |
| `polymeres` | BOUNDED POLYMERS — quantities COMPUTABLE by exact formula (Yohan's mandate: | degre_polymerisation, masse_molaire_polymere, masse_molaire_monomere, indice_polymolecularite, degre_polymerisation_carothers, taux_conversion |
| `portefeuille_universel` | TIER 2 — UNIVERSAL PORTFOLIO (Cover 1991): | richesse_crp, richesse_actif_pur, richesse_universelle, meilleur_crp, poids_universels_suivants, regret_log, analyse, formule |
| `posologie` | posologie.py — DOSAGE / POSOLOGY computations (exact, deterministic). | dose_totale, debit_perfusion, debit_gouttes, surface_corporelle_mosteller, dose_pediatrique, dose_pediatrique_bsa |
| `possibilite` | TIER 2 — POSSIBILITY THEORY (Zadeh ; Dubois & Prade): | normalisee, possibilite, necessite, intervalle_proba, domine, depuis_emboitees, encadre, formule |
| `predictif` | TIER 2 — CALIBRATION OF A PREDICTIVE DISTRIBUTION (PIT + pinball, brick 26, 2026-06-25). | pit_echantillon, pit_cdf, histogramme_pit, variance_pit, est_calibre_pit, perte_pinball, quantile_pinball, formule |
| `prefiltre` | IN-PROCESS PRE-FILTER OF CANDIDATES (2026-06-19, "drop to the smallest possible" lever — Yohan). | pre_juge, faire_gagne_prefiltre |
| `preuve_domaines` |  | passe, noyau, main |
| `preuve_polyglotte` |  | class ExecuteurJS, main |
| `preuve_propositionnelle` | PROOF THEORY — EXACT verification of the validity of propositional inferences, FAUX=0. | inference_valide, regle_modus_ponens, regle_modus_tollens |
| `prevision` | TIER 2 — TIME-SERIES FORECASTING WITH PREDICTION INTERVAL (brick 30, 2026-06-25). | prevoit, formule |
| `prevision_walley` | TIER 2 — LOWER / UPPER PREVISIONS (Walley): | lower, upper, intervalle, perte_sure, credal_depuis_croyance, encadre_gamble, formule |
| `prior_shift` | TIER 2 — PRIOR-SHIFT / LABEL-SHIFT CORRECTION (Saerens-Latinne-Decaestecker) (brick, 2026-06-26). | corrige_posterior, estime_prior_cible, adapte, formule |
| `procedes_fabrication` | MANUFACTURING PROCESSES — CONVENTIONAL classification + material yield (Yohan's mandate: | type_procede, rendement_matiere |
| `procedes_industriels` | Industrial processes: | rendement, bilan_matiere, debit_production, taux_conversion |
| `processus_gaussien` | TIER 2 — GAUSSIAN-PROCESS REGRESSION (GP, brick 45, 2026-06-26). | gp_fit, gp_predict, gp_intervalle, ajuste, formule |
| `profilage` | PROFILING & EMPIRICAL COMPLEXITY — measuring the real cost of a piece of code (advanced-code brick, 2026-07-02). | mesure_temps, mesure_memoire, classe_croissance |
| `propagande` | propagande.py — ESTABLISHED catalogue of propaganda techniques and taxonomy of information disorder (sourced facts, ab | technique, liste_techniques, type_desinformation, est_intentionnel, est_faux, liste_types_desinformation |
| `propagation` | TIER 2 — UNCERTAINTY PROPAGATION (brick 5, 2026-06-25). | propage_mc, propage_lineaire, intervalle_lineaire, formule |
| `property_based` | PROPERTY-BASED TESTING — active falsification of an invariant (verification/advanced-code brick, 2026-07-02). | pour_tout |
| `proportion_binomiale` | TIER 2 — BINOMIAL PROPORTION CONFIDENCE INTERVAL (Wald vs Wilson vs Agresti-Coull) (brick, 2026-06-26). | wald, wilson, agresti_coull, intervalle, formule |
| `proprietes_materiaux` | MATERIAL PROPERTIES (measurable) — Hooke's law & linear elasticity (Yohan's mandate: | contrainte, deformation, module_young, hooke_contrainte, hooke_deformation, allongement |
| `proteines` | PROTEINS, ENZYMES — structure and classification (established SOURCED facts + EXACT computations). | niveau_structure, nombre_niveaux_structure, classe_enzyme_ec, nombre_liaisons_peptidiques |
| `pseudosciences` | PSEUDOSCIENCES — BOUNDED catalogue of the scientific validity STATUS (established consensus), pure stdlib (2026-07-02). | est_catalogue, validite_scientifique, base_consensus, a_validite_demontree, pratiques |
| `psychometrie` | psychometrie.py — Psychometric tests (validity / reliability): | qi_standardise, rang_percentile_qi, alpha_cronbach, erreur_standard_mesure |
| `qualitatif` | QUALITATIVE REASONING — Wave 4 brick (sign algebra + monotone influences). | signe_produit, signe_somme, class ReseauInfluences |
| `quantile_regression` | TIER 2 — QUANTILE REGRESSION (pinball loss, multi-τ) under HETEROSCEDASTICITY (brick 43, 2026-06-26). | pinball, quantile_fit, predit, bande_quantile, bande_homoscedastique, formule |
| `quantique` | QUANTUM MECHANICS — EXACT fundamental relations, directly callable, FAUX=0 (formula/concept mission 2026-06-2 | energie_photon, longueur_onde_broglie, niveaux_puits_infini, borne_heisenberg |
| `questions` | AI ANSWERER — unified questions/answers, model-free (2026-06-18, "seeing what the AI can do without a model"). | class RepondeurIA |
| `rademacher` | TIER 2 — RADEMACHER COMPLEXITY & UNIFORM generalization bound (Bartlett-Mendelson ; Mohri) (brick 66, 2026-06- | rademacher_empirique, borne_massart, borne_generalisation, borne, formule |
| `raisonnement_defaut` | DEFAULT REASONING — BOUNDED core of "general case vs particular case / exception" (B-NEC), pure stdlib (2026-07-02) | class RegleDefaut |
| `rapport_invention` | UNIFIED INVENTION REPORT — the "product" surface of Yohan's objective: | rapport, texte |
| `raster_png` | PNG RASTER — BOUNDED core of the RASTER IMAGE modality (pixels), pure stdlib (2026-07-02). | class Image, encode, ecris, decode |
| `rayonnement_thermique` | BLACK-BODY THERMAL RADIATION — EXACT primitives, FAUX=0 (subject: | longueur_onde_max, temperature_depuis_pic, frequence_max, loi_stefan_boltzmann, puissance_rayonnee |
| `recettes` | RECIPES (procedures) — scaling and culinary conversions (CONVENTIONS). | adapte_quantite, facteur_echelle, convertir_mesure, temps_cuisson_adapte |
| `recherche_dirigee` | DIRECTED SEARCH — taming the combinatorial explosion of open invention (2026-06-18, auto-evolution goal). | class Banque, synthetise |
| `redox` | OXIDATION-REDUCTION — oxidation number (o.n.) in a NEUTRAL compound + electrons exchanged. | nombre_oxydation, equilibre_electronique |
| `refactor` | BEHAVIOR-PRESERVING REFACTOR — adopting a cleaner variant ONLY if it computes the same (2026-07-02). | adopte_refactor, meilleur_si_equivalent |
| `references` | BOUNDED CONVENTION REFERENCES (Yohan's mandate 2026-06-23: | vers_morse, depuis_morse, nato, couleur_resistance, frequence_note |
| `region_multivariee` | TIER 2 — MULTIVARIATE CONFORMAL PREDICTION REGIONS (Mahalanobis, brick 42, 2026-06-26). | region_conforme, dans_region, boite_marginale, dans_boite, formule |
| `regle` | NORMATIVE RULE ENGINE — the domain "rules laid down by an authority", entirely BOUNDED (cf. | class Regle, class Referentiel, evalue_predicat, class Jugement, applique, apprend_predicat, prevaut, cherche_partout |
| `regles_induites` | INDUCTION → DEDUCTION BRIDGE — the rules VALIDATED by induction_horn become Datalog clauses (2026-07-02). | clauses_datalog, class MoteurInduit |
| `regression_fallacieuse` | TIER 2 — SPURIOUS REGRESSION (Granger-Newbold 1974): | marche_aleatoire, bruit_blanc, t_et_r2, taux_faux_positif, analyse, formule |
| `regression_moyenne` | TIER 2 — REGRESSION TOWARD THE MEAN (Galton): | moyenne, correlation, selectionne, regression_vers_moyenne, analyse, formule |
| `regression_robuste` | TIER 2 — ROBUST REGRESSION (Huber M-estimator) under CONTAMINATION (brick 41, 2026-06-26). | ols, huber_fit, huber_slope_ic, ols_slope_ic, formule |
| `relations_lexique` | RELATIONS_LEXIQUE — exploits syn/ant of the converted lexicon (§6.2 d, 2026-06-18). | aretes_syn, paires_ant, raisonneurs |
| `relativite_generale` | GENERAL RELATIVITY — EXACT primitives, directly callable, FAUX=0 (formula/concept mission 2026-06-29). | rayon_schwarzschild, dilatation_gravitationnelle |
| `relativite_restreinte` | SPECIAL RELATIVITY — Einstein kinematics and energy, EXACT MECHANISM (Yohan's mandate: | facteur_lorentz, dilatation_temps, contraction_longueur, energie_totale, energie_repos, addition_vitesses |
| `relaxation` | CONSTRAINT RELAXATION / CONTRADICTION RESOLUTION — Wave 5 brick (TRIZ spirit). | relache_minimal, conflit |
| `reseaux_ip` | IP NETWORKS — IPv4 subnet computation, FAUX=0 (formula/concept mission 2026-06-29). | ip_vers_entier, entier_vers_ip, masque_entier, masque, adresse_reseau, adresse_broadcast, nombre_hotes, meme_reseau |
| `reseaux_neurones` | NEURAL NETWORKS (mechanisms) — EXACT forward propagation, FAUX=0 (formula/concept mission 2026-06-29). | echelon, signe, relu, sigmoide, tanh, potentiel, neurone, couche_dense |
| `resolution` | FUZZY ENTITY RESOLUTION (engine — ADDITIVE, does not modify lecteur.py). | corrige, negation_fait_partie_entite, resout_superlatif, resout_comparaison, resout_fiche, resout_nl_generique, resout_liste, repond_floue |
| `resoudre_tout` | CHAINED RESOLUTION (2026-06-22, point 4: | resoudre_tout |
| `restitution` | RESTITUTION ENGINE — the counterpart of the ANALYSIS engine (examine_cible). | class MoteurRestitution |
| `restitution_fraiche` | FRESHNESS-GATED RESTITUTION — never serving a stale fact as current (temporal acquisition, 2026-07-02). | sert_ou_hors, sert_le_plus_frais, a_rafraichir |
| `retraite` | retraite.py — Retirement pension: | coefficient_proratisation, pension, taux_remplacement, decote |
| `revelation_bayesienne` | TIER 2 — BAYESIAN REVELATION & PROTOCOL DEPENDENCE (Monty Hall): | posterior, prob_gain_changer, simule, brier_naif_vs_bayes, analyse, formule |
| `revision` | BELIEF REVISION — Wave 8 brick (reconcile, do not pile up). | class Croyance, class BaseCroyances |
| `rhetorique` | RHETORIC / PERSUASION (techniques) — ESTABLISHED CATALOGUE (consensus, source: | mode_persuasion, modes, figure_style, figures, identifie_mode |
| `ridge` | TIER 2 — RIDGE REGRESSION under COLLINEARITY: | ajuste, predit, mse, analyse, formule |
| `risque_conforme` | TIER 2 — CONFORMAL RISK CONTROL (CRC, brick 12, 2026-06-25). | seuil_crc, controle_fnr, ensemble_au_seuil |
| `robotique` | ROBOTICS (kinematics) — forward geometric model, FAUX=0 (formula/concept mission 2026-06-29). | cinematique_directe_2r, portee_max, portee_min, atteignable |
| `robust_bayes` | TIER 2 — ROBUST BAYES by ε-CONTAMINATION (Berger): | indicatrice, posterieur_contamine, posterieur_nominal, estime, formule |
| `roc_auc` | TIER 2 — AUC (DISCRIMINATIVE power) WITH CONFIDENCE INTERVAL (brick, 2026-06-26). | auc, se_hanley, se_naive, ic_hanley, ic_naif, evalue, bat_le_hasard, formule |
| `routeur` | ZONE-ROUTING — sparse "brain-like" activation (2026-06-17, Yohan's vision). | cle_tache, class RouteurZone, resoudre_route, resoudre_route_rr, auto_configure, sauve_config, charge_config, resoudre_route_rr2 |
| `routeur_langage` | LANGUAGE ROUTER — "the AI sorts languages by need" (2026-07-02, Yohan's vision, polyglot portfolio). | backends_disponibles, choisit, executeur_pour |
| `saint_petersbourg` | TIER 2 — SAINT PETERSBURG PARADOX: | paiement, esperance_tronquee, equivalent_certain_log, valeur_casino_fini, moyenne_jeux, analyse, formule |
| `savoir_massif` | SAVOIR_MASSIF — wires the MASSIVE LEXICON (1.9 M entries from the frwiktionary dump) as a resource of the SENSE bricks (§6.2 b, | class SavoirMassif, main |
| `schema_relations` | SCHEMA OF RELATIONS (MEASURED meta-model) — promotion of the 🟡 brick to a first-class object (2026-07-02). | class ProfilRelation, profil, inverses_compatibles, relations_hierarchiques |
| `scores_propres` | TIER 2 — PROPER SCORING RULES & RANKING OF FORECASTERS (brick 10, 2026-06-25). | log_loss, brier, score_spherique, crps, classe_forecasters |
| `scout_qlever` | QLever INGESTION SCOUT — automates the FAUX=0 DUE DILIGENCE over a BATCH of candidate "X -> country" relations (Yohan's mandate | val, decouvre, collision, sonde, sonde_generique, rapport_generique, rapport |
| `scrutin` | BALLOT — Vote / electoral process (mechanics). | dhondt, sainte_lague, quotient_hare, majorite_absolue |
| `seismologie` | SEISMOLOGY — BOUNDED core of earthquakes (magnitude, energy), established laws, pure stdlib (2026-07-02). | magnitude_moment, moment_depuis_magnitude, energie_joules, magnitude_depuis_energie, rapport_amplitude, rapport_energie, classe |
| `selecteur` | GENERIC SITUATIONAL SELECTOR — the "brain-like" meta-architecture (2026-06-19, Yohan's vision: | class Selecteur |
| `semiconducteurs` | SEMICONDUCTORS — bounded-physics COMPUTABLE by formula (FAUX=0 mandate, same posture as `physique.py`). | energie_gap_eV_vers_joule, longueur_onde_seuil, longueur_onde_seuil_nm, type_dopage, dopants_connus |
| `serie_autoregressive` | TIER 2 — AUTOREGRESSIVE FORECASTING AT h STEPS, uncertainty GROWING with the horizon (brick 46, 2026-06-26). | ar1_fit, prevoit_h, prevoit, formule |
| `serie_multivariee` | TIER 2 — MULTIVARIATE FORECASTING BY VAR(1) + JOINT REGION (brick, 2026-06-26). | var_fit, prevision, mahalanobis2, seuil_conforme, demi_largeurs_boite, ajuste, formule |
| `series_calcul` | SERIES & CONVERGENCE — EXACT sums and criteria, FAUX=0 (formula/concept mission 2026-06-29). | somme_arithmetique, somme_geometrique, somme_geometrique_infinie, converge_geometrique, converge_riemann, somme_carres |
| `session` | Brick 9 — THE TRAINING SESSION (the full orchestrator). | class Etape, session |
| `shiryaev` | TIER 2 — QUICKEST DETECTION (Shiryaev, Bayesian quickest detection): | gaussienne, posteriors, detecte, seuil_pour_alpha, analyse, formule |
| `simpson` | TIER 2 — SIMPSON'S PARADOX: | taux, taux_strates, taux_agrege, gagnant_par_strate, gagnant_agrege, analyse, formule |
| `simulation` | SIMULATION / FORWARD-MODEL — Wave 3 brick. | class ConflitDeRegles, class Simulateur |
| `smooth_ambiguity` | TIER 2 — SMOOTH AMBIGUITY (smooth ambiguity, Klibanoff-Marinacci-Mukerji 2005): | eu, phi_lineaire, phi_cara, prior_reduit, valeur, eu_reduit, equiv_certain_cara, choisir |
| `solveur_type` | TYPE-DRIVEN SOLVER (means-end) — "the how" against "the more" (2026-06-19). | class Solveur, resoudre_demande, main |
| `sophismes` | sophismes.py — Identification of the FORM of a conditional argument and catalogue of named informal fallacies (established f | identifie_forme, est_valide, est_sophisme, definition_sophisme, liste_sophismes |
| `sources` | REGISTRY OF RELIABLE SOURCES — the AI knows WHERE to learn (data, not code). | source, url, toutes, pour_domaine, pour_relation, domaines |
| `stabilite_algorithmique` | TIER 2 — ALGORITHMIC STABILITY & generalization (Bousquet-Elisseeff 2002) (brick 74, 2026-06-27). | knn, risque, stabilite_empirique, borne_generalisation, analyse, formule |
| `statique` | STATICS — equilibrium of solids and structures, FAUX=0 (formula/concept mission 2026-06-29). | moment, equilibre_moments, force_levier, centre_de_masse, reactions_appui |
| `stein` | TIER 2 — STEIN'S PARADOX (James-Stein estimator): | james_stein, risque_mle, risque_js, risques_apparies, analyse, formule |
| `stereochimie` | stereochimie.py — Counting stereoisomers and the relation between configurations. | nombre_stereoisomeres, paires_enantiomeres, nombre_enantiomeres, classe_relation |
| `stoechiometrie` | STOICHIOMETRY — EXACT balancing of chemical equations, FAUX=0 (formula/concept mission 2026-06-29). | equilibre, equation_equilibree |
| `store` | Brick 2 — THE STORE. | class Succes, class Store |
| `strategie_jeux` | OPTIMAL STRATEGY — games solved with perfect information (mandate: | gagnant, valeur_minimax, morpion_coup_optimal |
| `strategies` | TRAVERSAL STRATEGIES + STRATEGY ROUTING BY KEY (2026-06-19, Yohan's idea "occam where it wins, rr2 where it loses | st_rr2, st_costw, st_rr_occam, st_costw_occam, st_smith, st_sunny, st_presolve, class RouteurStrategie |
| `structure_mapping` | STRUCTURE-MAPPING (cross-domain analogy) — Wave 4 brick. | trouve, couverture |
| `structures_genie` | STRUCTURES / CIVIL ENGINEERING — EXACT strength of materials (beams, sections), direct call, FAUX=0. | contrainte_flexion, contrainte_traction, moment_quadratique_rectangle, moment_quadratique_cercle, module_resistance_rectangle, fleche_poutre_appuyee_charge_centree, flambement_euler |
| `substrat_physique` | SUBSTRAT-RÉEL — invention discovery by PHYSICAL TRANSDUCTION (toward the "inventions that change the world" objective, | class Concept, chaines, examine, lacunes_prioritaires |
| `substrat_reel` | SUBSTRAT-RÉEL — invention discovery by RELATIONAL TRANSDUCTION over the 71 M facts (FINAL OBJECTIVE, 2026-07-02). | types_reels, transducteurs_reels, connus_reel, chaines_types, class ConceptReel, examine_reel, relations_pont, class Composite |
| `sujets` | SUBJECT TAXONOMY — parser of `SUJETS_BORNE_OU_NON.md` into a machine-readable source of truth. | class Sujet, charge, bornes, par_code |
| `surapprentissage` | TIER 2 — OVERFITTING (overfitting): | genere, ajuste_poly, mse, degre_par_holdout, analyse, formule |
| `surdispersion` | TIER 2 — OVERDISPERSION OF COUNTS (Poisson vs negative binomial, brick 48, 2026-06-26). | moyenne_variance, dispersion, test_surdispersion, intervalle_poisson, intervalle_negbin, formule |
| `survie` | TIER 2 — SURVIVAL ANALYSIS / TIME-TO-EVENT under CENSORING (Kaplan-Meier, brick 39, 2026-06-26). | kaplan_meier, survie_a, mediane, km_avec_ic, km_naif_a, d_calibration, formule |
| `systemes_politiques` | POLITICAL SYSTEMS (definitions) — ESTABLISHED political conventions, deterministic pure functions, FAUX=0. | systemes, definition, classe_par_criteres, separation_pouvoirs, attribution_pouvoir |
| `tableur_xlsx` | XLSX SPREADSHEET — BOUNDED core of the SPREADSHEET modality (Excel/OOXML), pure stdlib (2026-07-02). | colonne_vers_lettre, lettre_vers_colonne, class Feuille, class Classeur, encode, ecris, decode |
| `taches` | The TASKS — the raw material offered to the model. | class Tache |
| `taux_de_base` | TIER 2 — BASE-RATE NEGLECT / FALSE-POSITIVE PARADOX: | vpp, vpn, estimation_naive, brier_naif_vs_bayes, analyse, formule |
| `taxonomie` | DATA-DERIVED TYPE TAXONOMY (service — ADDITIVE, read-only over the reader). | ensembles, types_de, frac_ech, densite, source_lexicale_rel, population_compatible, hubs |
| `tbm` | TIER 2 — TRANSFERABLE BELIEF MODEL (TBM, Smets): | masse_vide, belief, plausibilite, conjonctive, ferme_le_monde, pignistique, betp_evenement, decide |
| `techniques_culinaires` | CULINARY TECHNIQUES — BOUNDED classification by mode of heat transfer + reference temperatures. | mode_cuisson, milieu_cuisson, decrit, techniques_du_mode, temperature_reference, plage_maillard, point_de_fumee, convient_friture |
| `telecom` | TELECOMMUNICATIONS — channel capacity and quantities, FAUX=0 (formula/concept mission 2026-06-29). | capacite_shannon, debit_nyquist, gain_db, longueur_onde, snr_depuis_db |
| `teledetection` | teledetection.py — Remote sensing (satellites, imaging). | resolution_spatiale, ndvi, resolution_temporelle |
| `temperature` | TIER 2 — TEMPERATURE SCALING (brick 19, 2026-06-25). | softmax_temp, logits_depuis_probas, class TemperatureScaling, ajuste_temperature, formule |
| `test_calibration` | TIER 2 — CALIBRATION HYPOTHESIS TEST (brick 27, 2026-06-25). | test_spiegelhalter, test_hosmer_lemeshow, est_calibre_test, formule |
| `test_permutation` | TIER 2 — PERMUTATION TEST: | difference_moyennes, p_permutation, p_ttest_welch, teste, formule |
| `theorie_reseaux` | NETWORK THEORY (applied) — graph metrics, FAUX=0 (formula/concept mission 2026-06-29). | degre, degre_moyen, densite, centralite_degre, distribution_degres, clustering_local |
| `topographie_arpentage` | TOPOGRAPHY / SURVEYING — exact metric relations of the terrain, FAUX=0. | pente_pourcent, distance_horizontale, denivele, aire_polygone_coords |
| `topologie` | GENERAL TOPOLOGY — EXACT invariants (integers), directly callable, FAUX=0 (formula/concept mission 2026-06-29). | caracteristique_euler, caracteristique_euler_betti, caracteristique_euler_somme_connexe, genre_depuis_euler, genre_non_orientable_depuis_euler, est_homeomorphe_sphere |
| `toxicologie` | toxicologie.py — Dose-response, therapeutic index and toxicity classes (LD50). | index_therapeutique, dose_totale, marge_securite, classe_toxicite_dl50 |
| `trace` | VERIFIABLE REASONING TRACE — Wave 7 brick. | class Cycle, class Trace |
| `transfert` | CROSS-DOMAIN TRANSFER — the ASSEMBLER (machine-inventor): | transfere, manque |
| `transport_membranaire` | MEMBRANE TRANSPORT — bounded "Membranes, organelles" (established cell biology). | tonicite, sens_osmose, flux_fick |
| `triangulation` | TRIANGULATION — Wave 6 brick (agreement of two INDEPENDENT derivations = non-circular corroboration). | triangule, confirme |
| `tronc` | COMPREHENSION TRUNK — Phases 1-2 (SPEC_TRONC_COMPREHENSION §7-§10): acte(signal, contexte) → Faisceau — closed map of 11 speech acts, parallel candidates (G2), intent-aware honest fallback (G6), attunement, §10 composer (ambiguity is composed, never silently picked) (2026-07-07). | acte, compose, repli, attunement, class Candidat, class Faisceau |
| `trigonometrie` | TRIGONOMETRY — functions and triangle solving, FAUX=0 (formula/concept mission 2026-06-29). | deg_vers_rad, rad_vers_deg, sin_deg, cos_deg, tan_deg, loi_cosinus, angle_par_cotes, hypotenuse |
| `turing` | TURING MACHINES — bounded DETERMINISTIC simulation, FAUX=0 (formula/concept mission 2026-06-29). | execute |
| `typage` | OUTPUT TYPING OF CANDIDATES (2026-06-22, "elegance" lever: | type_sortie, type_attendu, reordonne_par_type |
| `types_categories` | ALTERNATIVE FOUNDATIONS (category theory, types) — two EXACT, deterministic mechanisms, FAUX=0 (formula/concept | parse_type, var, app, lam, type_de, bien_type, morphisme, identite |
| `urgence_medicale` | urgence_medicale.py — Established clinical emergency scores. | score_glasgow, est_coma_grave, gravite_glasgow, score_apgar, interpretation_apgar, indice_choc, est_choc |
| `usinage` | BOUNDED MACHINING — cutting parameters (machining), EXACT and established formulas. | vitesse_coupe, rotation_broche, taux_enlevement_matiere, temps_usinage, avance_par_minute |
| `usine_donnees` | DATA FACTORY (2026-06-17, "making the AI ready to learn") — accumulating a CORPUS of VERIFIED successes in a persistent store | accumule |
| `utilite` | "EVOLUTIONARY UTILITY" brick — keep the most useful, supplant, re-judge. | class Utilite, evalue_utilite, class Selection |
| `valeurs_extremes` | TIER 2 — EXTREME VALUES / TAIL RISK (VaR, brick 33, 2026-06-25). | ajuste_gpd, var_pot, proba_depassement, var_pot_ic, formule |
| `variational_preferences` | TIER 2 — VARIATIONAL PREFERENCES / MULTIPLIER (Hansen-Sargent ; Maccheroni-Marinacci-Rustichini): | eu, kl, pire_distribution, valeur_robuste, valeur_directe, choisir, formule |
| `veille` | WATCH / WEB ACCESS — SOVEREIGN search, FAUX=0 (roadmap #11: | recupere, rapporte, independantes, corrobore, approfondit |
| `veille_corroboration` | WEB -> REALITY -> FACT-STORE LOOP: | juge_coherence_store, corrobore_valeur |
| `venn_abers` | TIER 2 — VENN-ABERS PREDICTOR (brick 16, 2026-06-25). | class VennAbers, formule |
| `verifie_demo` | Provara — out-of-the-box verification / ready-to-use verification. | main |
| `web` | WEB (HTML/CSS/standards) — exact STRUCTURAL checks, FAUX=0 (formula/concept mission 2026-06-29). | balises_equilibrees, specificite, compare_specificite |
| `will_rogers` | TIER 2 — WILL ROGERS PHENOMENON / STAGE MIGRATION: | moyenne, migrants_will_rogers, migration, analyse, formule |
| `winner_curse` | TIER 2 — WINNER'S CURSE & SELECTIVE INFERENCE (brick 71, 2026-06-27). | selectionne, ic_naif, ic_simultane, estime, formule |

## Ingestion (real sources) — 147 modules

| Module | Role | API |
|---|---|---|
| `ingere_affixes` | LANGUAGE INGESTION — prefix/suffix -> sense -> datasets/lecteur/sens_prefixe.jsonl + sens_suffixe.jsonl (OFFLINE). | ingere |
| `ingere_alliages` | MATERIALS INGESTION — alloy -> composition -> datasets/lecteur/composition_alliage.jsonl (OFFLINE). | ingere |
| `ingere_angles` | GEOMETRY INGESTION — type of angle -> measure -> datasets/lecteur/mesure_angle.jsonl (OFFLINE). | ingere |
| `ingere_animaux_dieux` | MYTHOLOGY INGESTION — Greek god -> sacred animal/attribute -> datasets/lecteur/animal_dieu.jsonl (OFFLINE). | ingere |
| `ingere_arts_martiaux` | SPORT INGESTION — martial art -> country of origin -> datasets/lecteur/pays_art_martial.jsonl (OFFLINE). | ingere |
| `ingere_astro_chimie2` | ASTRO + CHEMISTRY INGESTION — element -> flame colour, planet -> largest moon (OFFLINE). | ingere |
| `ingere_astronomie` | ASTRONOMY INGESTION (8 planets of the solar system) -> datasets/lecteur/*.jsonl (OFFLINE). | ingere |
| `ingere_atmospheres` | ASTRONOMY INGESTION — body -> presence of a significant atmosphere (yes/no) (OFFLINE). | ingere |
| `ingere_aviation` | AVIATION INGESTION — aircraft models (Q15056993) -> datasets/lecteur/*.jsonl (ONLINE, run by hand). | ingere_tout |
| `ingere_banques` | ECONOMICS INGESTION — currency -> issuing central bank -> datasets/lecteur/banque_centrale.jsonl (OFFLINE). | ingere |
| `ingere_batailles` | HISTORY INGESTION — battle -> war/conflict -> datasets/lecteur/guerre_bataille.jsonl (OFFLINE). | ingere |
| `ingere_bd` | COMICS INGESTION — series -> author/creator -> datasets/lecteur/auteur_bd.jsonl (OFFLINE). | ingere |
| `ingere_beaufort` | WEATHER INGESTION — Beaufort degree -> wind name -> datasets/lecteur/beaufort_description.jsonl (OFFLINE). | ingere |
| `ingere_biologie` | BIOLOGY INGESTION — animal -> zoological class -> datasets/lecteur/classe_animal.jsonl (OFFLINE). | ingere |
| `ingere_bloc_element` | CHEMISTRY INGESTION — element -> block of the periodic table (s/p/d/f) -> datasets/lecteur/bloc_element.jsonl (OFFLINE). | ingere |
| `ingere_cardinaux` | GEO INGESTION — cardinal point -> opposite cardinal point -> datasets/lecteur/oppose_cardinal.jsonl (OFFLINE). | ingere |
| `ingere_carences` | HEALTH INGESTION — vitamin -> deficiency disease -> datasets/lecteur/carence_vitamine.jsonl (OFFLINE). | ingere |
| `ingere_cepages` | OENOLOGY INGESTION — grape variety -> wine/grape colour (white/red) -> datasets/lecteur/couleur_cepage.jsonl (OFFLINE). | ingere |
| `ingere_chats` | FELINOLOGY INGESTION — cat breed -> country of origin -> datasets/lecteur/pays_race_chat.jsonl (OFFLINE). | ingere |
| `ingere_chiens` | CYNOLOGY INGESTION — dog breed -> country of origin -> datasets/lecteur/pays_race_chien.jsonl (OFFLINE). | ingere |
| `ingere_cinema` | CINEMA INGESTION — film -> director -> datasets/lecteur/realisateur_film.jsonl (OFFLINE). | ingere |
| `ingere_composes` | CHEMISTRY INGESTION — compound -> molecular formula (extension of `formule_chimique`) (OFFLINE). | ingere |
| `ingere_constantes_math` | MATHEMATICS INGESTION — constant -> numerical value -> datasets/lecteur/valeur_constante.jsonl (OFFLINE). | ingere |
| `ingere_coordonnees` | GEOGRAPHIC COORDINATES INGESTION (Wikidata/QLever P625) -> datasets/lecteur/*.jsonl (ONLINE, by hand). | ingere_capitales |
| `ingere_cordes` | MUSIC INGESTION — string instrument -> number of strings -> datasets/lecteur/nombre_cordes.jsonl (OFFLINE). | ingere |
| `ingere_corps_humain` | HUMAN BODY INGESTION — organ -> system -> datasets/lecteur/systeme_organe.jsonl (OFFLINE). | ingere |
| `ingere_cote_organe` | ANATOMY INGESTION — organ -> side of the body -> datasets/lecteur/cote_organe.jsonl (OFFLINE). | ingere |
| `ingere_couleurs` | COLOURS INGESTION — colour -> hexadecimal code (sRGB) -> datasets/lecteur/code_hex_couleur.jsonl (OFFLINE). | ingere |
| `ingere_couleurs_complementaires` | COLOURS INGESTION — colour -> complementary colour -> datasets/lecteur/couleur_complementaire.jsonl (OFFLINE). | ingere |
| `ingere_couleurs_secondaires` | COLOURS INGESTION — secondary colour -> mixture (subtractive synthesis) (OFFLINE). | ingere |
| `ingere_creatures` | MYTHOLOGY INGESTION — legendary creature -> mythology of origin -> datasets/lecteur/origine_creature.jsonl (OFFLINE). | ingere |
| `ingere_cris_animaux` | ZOOLOGY/LANGUAGE INGESTION — animal -> cry (name of the cry) -> datasets/lecteur/cri_animal.jsonl (OFFLINE). | ingere |
| `ingere_danses` | CULTURE INGESTION — dance -> country of origin -> datasets/lecteur/pays_danse.jsonl (OFFLINE). | ingere |
| `ingere_dents` | HUMAN BODY INGESTION — type of tooth -> function -> datasets/lecteur/fonction_dent.jsonl (OFFLINE). | ingere |
| `ingere_deserts` | GEO INGESTION — desert -> continent -> datasets/lecteur/continent_desert.jsonl (OFFLINE). | ingere |
| `ingere_devises_pays` | CIVICS INGESTION — country -> national motto -> datasets/lecteur/devise_pays.jsonl (OFFLINE). | ingere |
| `ingere_dump` | INGERE_DUMP — STREAMING ingestion of the FULL frwiktionary DUMP (§6.2 a, pure scale — 2026-06-18). | ingere_dump, main |
| `ingere_duree_match` | SPORT INGESTION — sport -> regulation match duration -> datasets/lecteur/duree_match.jsonl (OFFLINE). | ingere |
| `ingere_duree_notes` | MUSIC INGESTION — note figure -> duration (in beats, 4/4 time) -> datasets/lecteur/duree_note.jsonl (OFFLINE). | ingere |
| `ingere_dynasties` | HISTORY INGESTION — dynasty -> main country -> datasets/lecteur/pays_dynastie.jsonl (OFFLINE). | ingere |
| `ingere_echecs` | CHESS INGESTION — piece -> movement + value -> datasets/lecteur/*.jsonl (OFFLINE). | ingere |
| `ingere_ecritures` | LINGUISTICS INGESTION — language -> writing system -> datasets/lecteur/ecriture_langue.jsonl (OFFLINE). | ingere |
| `ingere_elements_ptjson` | ELEMENT PROPERTIES INGESTION -> datasets/lecteur/*.jsonl (ONLINE, run by hand). | ingere |
| `ingere_emblemes_floraux` | CULTURE INGESTION — country -> national floral emblem -> datasets/lecteur/embleme_floral.jsonl (OFFLINE). | ingere |
| `ingere_epices` | GASTRONOMY INGESTION — spice -> country/region of origin -> datasets/lecteur/origine_epice.jsonl (OFFLINE). | ingere |
| `ingere_espace` | SPACE INGESTION — probes & spacecraft (Q26529) -> datasets/lecteur/*.jsonl (ONLINE, run by hand). | ingere_tout |
| `ingere_famille_chimique` | CHEMISTRY INGESTION — element -> chemical family (named groups) (OFFLINE). | ingere |
| `ingere_fetes_nationales` | NATIONAL HOLIDAYS INGESTION — country -> date of the national holiday (OFFLINE). | ingere |
| `ingere_fonction_organe` | HUMAN BODY INGESTION — organ -> main function -> datasets/lecteur/fonction_organe.jsonl (OFFLINE). | ingere |
| `ingere_fondateurs_religions` | RELIGIONS INGESTION — religion -> founder -> datasets/lecteur/fondateur_religion.jsonl (OFFLINE). | ingere |
| `ingere_fromages` | GASTRONOMY INGESTION — cheese -> country of origin -> datasets/lecteur/pays_fromage.jsonl (OFFLINE). | ingere |
| `ingere_fruits_arbres` | BOTANY INGESTION — fruit -> tree that produces it -> datasets/lecteur/arbre_fruit.jsonl (OFFLINE). | ingere |
| `ingere_fuseaux` | GEO INGESTION — local time of a city/region -> UTC offset (standard time, excluding DST) (OFFLINE). | ingere |
| `ingere_gammes` | MUSIC INGESTION — scale -> number of notes -> datasets/lecteur/nombre_notes_gamme.jsonl (OFFLINE). | ingere |
| `ingere_genres_musicaux` | MUSIC INGESTION — musical genre -> country/region of origin -> datasets/lecteur/pays_genre_musical.jsonl (OFFLINE). | ingere |
| `ingere_geo` | GEOGRAPHY INGESTION -> datasets/lecteur/*.jsonl (ONLINE, run by hand). | ingere_geo |
| `ingere_geo_physique` | PHYSICAL GEOGRAPHY INGESTION — river/mountain -> continent -> datasets/lecteur/*.jsonl (OFFLINE). | ingere |
| `ingere_groupes_animaux` | LANGUAGE/ZOO INGESTION — animal -> group name (collective) -> datasets/lecteur/nom_groupe_animal.jsonl (OFFLINE). | ingere |
| `ingere_histoire` | HISTORY INGESTION — event -> year -> datasets/lecteur/annee.jsonl (OFFLINE). | ingere |
| `ingere_hormones` | PHYSIOLOGY INGESTION — organ/gland -> main hormone produced -> datasets/lecteur/hormone_organe.jsonl (OFFLINE). | ingere |
| `ingere_informatique` | COMPUTING INGESTION — extension -> programming language, and extension -> file type (OFFLINE). | ingere |
| `ingere_instruments_mesure` | METROLOGY INGESTION — instrument -> measured quantity -> datasets/lecteur/mesure_instrument.jsonl (OFFLINE). | ingere |
| `ingere_inventeurs` | INVENTIONS INGESTION — invention -> inventor -> datasets/lecteur/inventeur.jsonl (OFFLINE). | ingere |
| `ingere_ions` | CHEMISTRY INGESTION — ion -> charge -> datasets/lecteur/charge_ion.jsonl (OFFLINE). | ingere |
| `ingere_jo` | SPORT INGESTION — year -> host city of the Summer Olympic Games -> datasets/lecteur/ville_jo_ete.jsonl (OFFLINE). | ingere |
| `ingere_jo_hiver` | SPORT INGESTION — year -> host city of the Winter Olympics -> datasets/lecteur/ville_jo_hiver.jsonl (OFFLINE). | ingere |
| `ingere_jours_saints` | RELIGIONS INGESTION — religion -> weekly holy day -> datasets/lecteur/jour_saint_religion.jsonl (OFFLINE). | ingere |
| `ingere_kaikki` | INGERE_KAIKKI — CLI (network/file): | telecharge, ingere, main |
| `ingere_langues_famille` | LINGUISTICS INGESTION — language -> language family -> datasets/lecteur/famille_langue.jsonl (OFFLINE). | ingere |
| `ingere_lettres_grecques` | GREEK INGESTION — Greek letter (name) -> lowercase symbol -> datasets/lecteur/symbole_grec.jsonl (OFFLINE). | ingere |
| `ingere_lexique` | FR LEXICON INGESTION -> datasets/lecteur/*.jsonl (OFFLINE — local dump already converted, ZERO network). | ingere_genre, ingere_definition, ingere_definition_verbe, ingere_definition_adjectif, ingere_definition_adverbe, ingere_pluriel |
| `ingere_lieux_saints` | RELIGIONS INGESTION — religion -> main holy city/place -> datasets/lecteur/lieu_saint_religion.jsonl (OFFLINE). | ingere |
| `ingere_litterature` | LITERATURE INGESTION — work -> author -> datasets/lecteur/auteur_oeuvre.jsonl (OFFLINE). | ingere |
| `ingere_locutions_latines` | LATIN INGESTION — Latin phrase -> meaning in French -> datasets/lecteur/sens_locution_latine.jsonl (OFFLINE). | ingere |
| `ingere_maladies` | HEALTH INGESTION — disease -> type of pathogen -> datasets/lecteur/agent_maladie.jsonl (OFFLINE). | ingere |
| `ingere_marques` | ECONOMICS INGESTION — brand -> country of origin (auto / tech / luxury) -> datasets/lecteur/*.jsonl (OFFLINE). | ingere |
| `ingere_mineraux` | MINERALS INGESTION — mineral species (Q12089225) -> datasets/lecteur/*.jsonl (ONLINE, run by hand). | ingere_tout |
| `ingere_monuments` | MONUMENTS INGESTION — monument -> country, and monument -> city (OFFLINE). | ingere |
| `ingere_morse` | COMMUNICATION INGESTION — character -> international Morse code -> datasets/lecteur/code_morse.jsonl (OFFLINE). | ingere |
| `ingere_musique` | MUSIC INGESTION — instrument -> family -> datasets/lecteur/famille_instrument.jsonl (OFFLINE). | ingere |
| `ingere_musique_classique` | CLASSICAL MUSIC INGESTION — work -> composer -> datasets/lecteur/compositeur_oeuvre.jsonl (OFFLINE). | ingere |
| `ingere_mythologie` | GREEK MYTHOLOGY INGESTION — god -> domain, and Greek god -> Roman equivalent (OFFLINE). | ingere |
| `ingere_mythologie2` | MYTHOLOGIES INGESTION — extension of `domaine_dieu` (Egyptian + Norse) + `pantheon_dieu` (OFFLINE). | ingere |
| `ingere_mythologie3` | HINDU MYTHOLOGY INGESTION — adds the Hindu gods to `domaine_dieu` + `pantheon_dieu` (OFFLINE). | ingere |
| `ingere_nombre_organe` | ANATOMY INGESTION — organ -> number in the human body -> datasets/lecteur/nombre_organe.jsonl (OFFLINE). | ingere |
| `ingere_nombres_lettres` | FRENCH INGESTION — number -> spelling in letters -> datasets/lecteur/nombre_en_lettres.jsonl (OFFLINE). | ingere |
| `ingere_notes_musique` | MUSIC INGESTION — note (Latin solfège) -> Anglo-Saxon notation (OFFLINE). | ingere |
| `ingere_nuit_dates` | NIGHT ingestion 2026-06-29: | ingere_date |
| `ingere_objet_etude` | SCIENCES INGESTION — discipline ("-logy/-graphy") -> object of study (OFFLINE). | ingere |
| `ingere_oceans` | GEO INGESTION — ocean -> rank by area -> datasets/lecteur/rang_ocean.jsonl (OFFLINE). | ingere |
| `ingere_optique` | OPTICS INGESTION — optical instrument -> use -> datasets/lecteur/usage_instrument_optique.jsonl (OFFLINE). | ingere |
| `ingere_orbites` | ASTRONOMY INGESTION — planet -> orbital period + distance to the Sun (OFFLINE). | ingere |
| `ingere_ordres` | CONVENTIONAL ORDERS INGESTION — Chinese sign / judo belt / rainbow -> rank (OFFLINE). | ingere |
| `ingere_otan` | COMMUNICATION INGESTION — letter -> word of the NATO/ICAO phonetic alphabet -> datasets/lecteur/alphabet_otan.jsonl (OFFL | ingere |
| `ingere_pays_renommes` | GEO/HISTORY INGESTION — former country name -> current name -> datasets/lecteur/nom_actuel.jsonl (OFFLINE). | ingere |
| `ingere_peinture` | PAINTING INGESTION — work -> painter -> datasets/lecteur/peintre_oeuvre.jsonl (OFFLINE). | ingere |
| `ingere_personnages` | FICTION INGESTION — character -> creator (author) -> datasets/lecteur/createur_personnage.jsonl (OFFLINE). | ingere |
| `ingere_personnages_histoire` | HISTORY INGESTION — historical figure -> function/role -> datasets/lecteur/fonction_personnage.jsonl (OFFLINE). | ingere |
| `ingere_petits_animaux` | ZOOLOGY/LANGUAGE INGESTION — animal -> name of the young -> datasets/lecteur/petit_animal.jsonl (OFFLINE). | ingere |
| `ingere_ph` | CHEMISTRY INGESTION — substance -> acid-base character -> datasets/lecteur/ph_substance.jsonl (OFFLINE). | ingere |
| `ingere_phobies` | PHOBIAS INGESTION — phobia -> object of the fear -> datasets/lecteur/objet_phobie.jsonl (OFFLINE). | ingere |
| `ingere_pierres` | GEMMOLOGY INGESTION — gemstone -> characteristic colour -> datasets/lecteur/couleur_pierre.jsonl (OFFLINE). | ingere |
| `ingere_plats` | GASTRONOMY INGESTION — dish -> country of origin -> datasets/lecteur/pays_plat.jsonl (OFFLINE). | ingere |
| `ingere_ponctuation` | LANGUAGE INGESTION — punctuation mark (name) -> symbol -> datasets/lecteur/symbole_ponctuation.jsonl (OFFLINE). | ingere |
| `ingere_prix` | DISTINCTIONS INGESTION — prize/award -> domain -> datasets/lecteur/domaine_prix.jsonl (OFFLINE). | ingere |
| `ingere_qlever` | WIKIDATA INGESTION via QLEVER -> datasets/lecteur/*.jsonl (ONLINE, run by hand). | qlever, val, domaine, ingere_sommets, ingere_capitales, ingere_hymnes, ingere_conduite, ingere_iso_num |
| `ingere_raccourcis` | COMPUTING INGESTION — action -> keyboard shortcut -> datasets/lecteur/raccourci_clavier.jsonl (OFFLINE). | ingere |
| `ingere_regime_alimentaire` | BIOLOGY INGESTION — animal -> diet -> datasets/lecteur/regime_alimentaire.jsonl (OFFLINE). | ingere |
| `ingere_region_os` | HUMAN BODY INGESTION — bone -> region of the body -> datasets/lecteur/region_os.jsonl (OFFLINE). | ingere |
| `ingere_religions` | RELIGIONS INGESTION — religion -> sacred text, and religion -> place of worship (OFFLINE). | ingere |
| `ingere_resistances` | ELECTRONICS INGESTION — resistor band colour -> digit (0-9) -> datasets/lecteur/valeur_couleur_resistance.j | ingere |
| `ingere_rest` | REST INGESTION BRIDGE (NON-SPARQL) — datasets/lecteur/*.jsonl via the MediaWiki/Wikidata API. | est_date_nue, cirrus_qids, qids_par_decoupe, collecte_date_rest, ingere_date_rest, republie_date_rest, collecte_entite_rest, ingere_entite_rest |
| `ingere_roches` | GEOLOGY INGESTION — rock -> type (igneous/sedimentary/metamorphic) (OFFLINE). | ingere |
| `ingere_saison_olympique` | SPORT INGESTION — sport -> Olympic season (summer / winter) -> datasets/lecteur/saison_olympique.jsonl (OFFLINE). | ingere |
| `ingere_salutations` | LANGUAGES INGESTION — language -> "hello" and language -> "thank you" (OFFLINE). | ingere |
| `ingere_sciences` | SCIENCES INGESTION — discovery/theory -> author -> datasets/lecteur/auteur_decouverte.jsonl (OFFLINE). | ingere |
| `ingere_sens_organe` | HUMAN BODY INGESTION — sensory organ -> sense -> datasets/lecteur/sens_organe.jsonl (OFFLINE). | ingere |
| `ingere_sigles` | ACRONYMS INGESTION — acronym/initialism -> meaning -> datasets/lecteur/signification_sigle.jsonl (OFFLINE). | ingere |
| `ingere_sport` | SPORT INGESTION — discipline -> number of players per team (on the field) (OFFLINE). | ingere |
| `ingere_subdivisions_monnaie` | ECONOMICS INGESTION — currency -> subdivision (hundredth) -> datasets/lecteur/subdivision_monnaie.jsonl (OFFLINE). | ingere |
| `ingere_surnoms_rois` | HISTORY INGESTION — sovereign -> nickname -> datasets/lecteur/surnom_roi.jsonl (OFFLINE). | ingere |
| `ingere_symbole_astro` | ASTRONOMY INGESTION — planet -> astronomical symbol (OFFLINE). | ingere |
| `ingere_symbole_monnaie` | ECONOMICS INGESTION — currency -> currency symbol -> datasets/lecteur/symbole_monnaie.jsonl (OFFLINE). | ingere |
| `ingere_symboles_math` | MATHEMATICS INGESTION — operation/concept -> symbol -> datasets/lecteur/symbole_math.jsonl (OFFLINE). | ingere |
| `ingere_t10` | T10 INGESTION — SPORT & COMPETITIONS (ONLINE, run by hand). | ingere_sport_competition, ingere_pays_equipe_nationale, ingere_vainqueur_competition, ingere_ligue_club, ingere_stade_club, ingere_pays_competition, ingere_sport_equipe, ingere_organisateur_competition |
| `ingere_t11` | T11 INGESTION — TRANSPORT, VEHICLES & INFRASTRUCTURE -> datasets/lecteur/*.jsonl (ONLINE QLever, offline afterwards). | ingere_codes, ingere_tout, sonde |
| `ingere_t12` | T12 INGESTION — RELIGION, MYTHOLOGY & PHILOSOPHY (ONLINE, run by hand). | ingere_pere_divinite, ingere_mere_divinite, ingere_fondateur_ordre_religieux, ingere_religion_ordre_religieux, ingere_dedicace_edifice_religieux, ingere_pere_personnage_mythique, ingere_mere_personnage_mythique, ingere_conjoint_personnage_mythique |
| `ingere_t4` | T4 INGESTION — "LIVING" CORRIDOR (biology: | domaine, ingere_organisme_gene, ingere_chromosome_gene, ingere_specialite_medicale_maladie, ingere_agent_pathogene_maladie, ingere_vecteur_maladie, ingere_glande_hormone, ingere_regime_alimentaire |
| `ingere_t5` | T5 INGESTION — CULTURAL WORKS, CREATORS / PRODUCTION side (Wikidata via QLever). | main |
| `ingere_t5_canon` | T5 INGESTION — WORKS CANON (opera / musical composer) FROM THE MODEL'S KNOWLEDGE. | main |
| `ingere_t6` | T6 INGESTION — PERSONS (NON-place attributes) & ORGANIZATIONS (ONLINE, run by hand). | ingere_sexe_personne, ingere_langue_maternelle, ingere_secteur_entreprise, ingere_occupation_personne, ingere_poste_occupe, ingere_domaine_travail, ingere_cause_deces, ingere_bourse_cotation |
| `ingere_t7` | T7 INGESTION — NUMERICAL MEASURES & TECHNICAL -> datasets/lecteur/*.jsonl (ONLINE via QLever, offline afterwards). | ingere_numerique, ingere_tout, sonde, ingere_une |
| `ingere_t8` | T8 INGESTION — HISTORY, DATES & POLITICS -> datasets/lecteur/*.jsonl (ONLINE via QLever, offline afterwards). | ingere_date, ingere_regne, ingere_succession, ingere_batailles, ingere_traites, ingere_sieges, ingere_operations, ingere_etat_vers_etat |
| `ingere_t9` | T9 INGESTION — "LANGUAGE, LEXICON & WRITING" CORRIDOR (category `convention`). | ingere_systeme_ecriture, ingere_code_iso6393, ingere_code_iso6392, ingere_code_glottolog, ingere_code_ethnologue, ingere_statut_vitalite, ingere_code_ietf, ingere_code_linguasphere |
| `ingere_t9_autosource` | T9 AUTO-SOURCING — TYPOLOGY OF WRITING SYSTEMS -> datasets/lecteur/type_systeme_ecriture.jsonl (OFFLINE). | ingere, ingere_ordre, ingere_morpho, ingere_ton, ingere_align, ingere_genre, ingere_article, ingere_classif |
| `ingere_t9_lexemes` | T9 INGESTION — Wikidata LEXEMES -> datasets/lecteur/{categorie_lexicale_mot,genre_grammatical_mot}.jsonl (ONLINE). | ingere_categorie, ingere_genre, ingere_concept, ingere_etymon |
| `ingere_type_astre` | ASTRONOMY INGESTION — celestial body -> type -> datasets/lecteur/type_astre.jsonl (OFFLINE). | ingere |
| `ingere_types_arbres` | BOTANY INGESTION — tree -> type (broadleaf / conifer) -> datasets/lecteur/type_arbre.jsonl (OFFLINE). | ingere |
| `ingere_unites_imperiales` | METROLOGY INGESTION — imperial/Anglo-Saxon unit -> metric equivalent -> datasets/lecteur/equivalent_metrique.json | ingere |
| `ingere_vents` | WEATHER INGESTION — regional wind -> region/origin -> datasets/lecteur/origine_vent.jsonl (OFFLINE). | ingere |
| `ingere_vetements` | CLOTHING INGESTION — garment/accessory -> part of the body -> datasets/lecteur/partie_corps_vetement.jsonl (OFFLINE). | ingere |
| `ingere_villes` | GEO INGESTION — large city (NON capital) -> country -> datasets/lecteur/pays_ville.jsonl (OFFLINE). | ingere |
| `ingere_villes_coordonnees` | LOCALITY COORDINATES INGESTION (Wikidata/QLever P625, CYCLE 2) -> latitude_localite / longitude_localite. | ingere_localites |
| `ingere_vitamines` | HEALTH INGESTION — vitamin -> chemical name -> datasets/lecteur/nom_vitamine.jsonl (OFFLINE). | ingere |
| `ingere_wikidata` | WIKIDATA INGESTION -> datasets/lecteur/*.jsonl (ONLINE — run BY HAND, never at reader import). | sparql, val, fonctionnel, reconcilie, ecrit_jsonl, ecrit_conflits, publie, snapshot_brut |
| `ingere_worldbank` | WORLD BANK INGESTION -> datasets/lecteur/*.jsonl (ONLINE, run by hand). | ingere_population, ingere_indicateur, ingere_economie |
| `ingere_zodiaque` | ZODIAC INGESTION — astrological sign -> element -> datasets/lecteur/element_zodiaque.jsonl (OFFLINE). | ingere |

## Validators (FAUX=0 gate) — 683 modules

| Validator | What it proves |
|---|---|
| `valide_abduction` | VALIDATION abduction.py (Wave 5). |
| `valide_abstention` | VALIDATION abstention.py (Wave 7). |
| `valide_accord_correct` | AGREEMENT-ERROR DETECTION (COMPREHENSION brick) — knowing when the French is wrong. |
| `valide_accord_phrase` | AGREEMENT IN THE NOUN PHRASE (COMPREHENSION brick — sentence) — propagates the plural across the whole group. |
| `valide_adjacence` | ADJACENCY — aggregating a relation between NEIGHBOURING elements (theme II: |
| `valide_adverbe` | ADVERB IN -MENT (FORM DERIVATION brick) — deriving an adverb from an adjective is RULE-GOVERNED hence VERIFIABLE. |
| `valide_aerodynamique` | VALIDATES aerodynamique.py — held-out ADVERSARIAL. |
| `valide_agregation_previsions` | VALIDATION of FORECAST AGGREGATION (agregation_previsions.py) — judged by calibration.py. |
| `valide_algebre_boole` | VALIDATES algebre_boole.py — ADVERSARIAL, FAUX=0. |
| `valide_algebre_calcul` | VALIDATES algebre_calcul.py — held-out ADVERSARIAL, FAUX=0. |
| `valide_algo_analyse` | VALIDATES algo_analyse.py — held-out ADVERSARIAL, FAUX=0. |
| `valide_allais` | VALIDATION of the ALLAIS PARADOX (allais.py). |
| `valide_allen` | VALIDATION of allen.py — the 13 Allen interval relations. |
| `valide_alliages` | VALIDATES alliages.py — held-out ADVERSARIAL. |
| `valide_analogie` | ANALOGY / TRANSFER (COMPREHENSION brick) — a learned pattern is reused/adapted across DOMAINS. |
| `valide_analyse_chimique` | VALIDATES analyse_chimique.py — held-out ADVERSARIAL. |
| `valide_analyse_fonctionnelle` | VALIDATES analyse_fonctionnelle.py — held-out ADVERSARIAL. |
| `valide_analyse_phrase` | SENTENCE ANALYSIS (COMPREHENSION brick — sentence) — decomposing the sentence into grammatical classes. |
| `valide_ancetre_commun` | COMMON ANCESTOR / LINK (COMPREHENSION brick) — what two words have in common, on the sense graph. |
| `valide_ancrage` | VALIDATION of the ANCHORING EFFECT (ancrage.py). |
| `valide_ancres` | VALIDATION ancres.py (Wave 6). |
| `valide_anscombe` | VALIDATION of ANSCOMBE'S QUARTET (anscombe.py). |
| `valide_anticipation` | ANTICIPATION — predicting the NEXT TERM of a sequence (2026-06-17, Yohan's insight "anticipation is a bri |
| `valide_antonyme` | ANTONYMS (COMPREHENSION brick — sense axis: |
| `valide_arbitre` | VALIDATION arbitre.py (Wave 7). |
| `valide_architecture` | VALIDATES architecture.py — ADVERSARIAL, FAUX=0. |
| `valide_arithmetique_intervalles` | VALIDATION of INTERVAL ARITHMETIC (arithmetique_intervalles.py) — judged by calibration.py. |
| `valide_arithmetique_modulaire` | VALIDATES arithmetique_modulaire.py — held-out ADVERSARIAL, FAUX=0. |
| `valide_arret` | VALIDATES arret.py — ADVERSARIAL, FAUX=0. |
| `valide_assistant` | PERSISTENT-MEMORY AI ASSISTANT (2026-06-17) — the AI improves WITH USE: |
| `valide_assistant_nl` | VALIDATES assistant_nl — the AUTONOMOUS conversational gateway (boundedness -> answers/computes/searches/ASKS) — ADVERS |
| `valide_asteroides` | VALIDATES asteroides.py — held-out ADVERSARIAL. |
| `valide_astronautique` | VALIDATES astronautique.py — held-out ADVERSARIAL. |
| `valide_atome` | VALIDATES atome.py — FAUX=0 contract: |
| `valide_audio_wav` | VALIDATES audio_wav.py — exact PCM round-trip (stdlib `wave` oracle) + FAUX=0 (range, formats, invalid stream). |
| `valide_audiologie` | VALIDATES audiologie.py — held-out ADVERSARIAL. |
| `valide_audit_ancres` | VALIDATES the anchor-audit MECHANISM (audit_ancres.py) — FAUX=0 on the diagnosis itself. |
| `valide_audit_code` | VALIDATES audit_code.py — held-out ADVERSARIAL, SOUNDNESS-focused (never a false positive). |
| `valide_aumann` | VALIDATION of AUMANN'S AGREEMENT THEOREM (aumann.py). |
| `valide_auto_apprend` | VALIDATES — AUTONOMOUS SELF-LEARNING (2026-06-22). |
| `valide_auto_invention` | SELF-INVENTION ENGINE — the AI extends its repertoire ON ITS OWN, judged by reality (cf. |
| `valide_auto_invention_ouverte` | OPEN SELF-INVENTION ENGINE — universal composition, multi-domain, judged by reality (goal auto-evolu |
| `valide_auto_optimise` | VALIDATION of RECURSIVE SELF-OPTIMIZATION (auto_optimise.py). |
| `valide_auto_synthese` | SELF-SYNTHESIS FROM SKELETONS (2026-06-24) — the AI BUILDS its own bricks from generic skeleton |
| `valide_automates` | VALIDATES automates.py — ADVERSARIAL, FAUX=0. |
| `valide_automobile` | VALIDATES automobile.py — held-out ADVERSARIAL. |
| `valide_bandit` | VALIDATION of the BANDITS (bandit.py). |
| `valide_bandit_contextuel` | VALIDATION of the CONTEXTUAL BANDIT (bandit_contextuel.py). |
| `valide_base_faits` | VALIDATION of the VERIFIED FACT BASE (`base_faits.py`) — load-bearing judge of categories 2/3/4. |
| `valide_bases_donnees` | VALIDATES bases_donnees.py — ADVERSARIAL, FAUX=0. |
| `valide_batteries` | VALIDATES batteries.py — held-out ADVERSARIAL. |
| `valide_bayes` | VALIDATION of BAYESIAN COMBINATION (bayes.py) — is the posterior CALIBRATED? Monte-Carlo proof, JU |
| `valide_bayes_correle` | VALIDATION of CORRELATED BAYESIAN AGGREGATION (bayes.posterior_correle) — fixes the caveat of brick 2. |
| `valide_bayes_sequentiel` | VALIDATION of the SEQUENTIAL BAYESIAN (bayes_sequentiel.py) — judged by calibration.py. |
| `valide_benford` | VALIDATION of BENFORD'S LAW (benford.py). |
| `valide_berkson` | VALIDATION of BERKSON'S PARADOX (berkson.py). |
| `valide_bertrand` | VALIDATION of BERTRAND'S PARADOX (bertrand.py). |
| `valide_besoin` | VALIDATES besoin.py — goal/need layer of the invention engine. |
| `valide_biais_longueur` | VALIDATION of LENGTH BIAS (biais_longueur.py). |
| `valide_biais_publication` | VALIDATION of PUBLICATION BIAS (biais_publication.py). |
| `valide_biais_survie` | VALIDATION of SURVIVORSHIP BIAS (biais_survie.py). |
| `valide_bibliotheconomie` | VALIDATES bibliotheconomie.py — held-out ADVERSARIAL. |
| `valide_bibliotheque_invention` | VALIDATION of the RECURSIVE CAPSTONE — sleep phase (bibliotheque_invention.py). |
| `valide_bifurcations` | VALIDATES bifurcations.py — held-out ADVERSARIAL. |
| `valide_big_bang` | VALIDATES big_bang.py — held-out ADVERSARIAL. |
| `valide_big_data` | VALIDATES big_data.py — ADVERSARIAL, FAUX=0. |
| `valide_bioinfo` | VALIDATES bioinfo.py — held-out ADVERSARIAL, FAUX=0. |
| `valide_bioingenierie` | VALIDATES bioingenierie.py — held-out ADVERSARIAL. |
| `valide_biomecanique` | VALIDATES biomecanique.py — held-out ADVERSARIAL. |
| `valide_biostatistique` | VALIDATES biostatistique.py — held-out ADVERSARIAL. |
| `valide_bits` | BINARY / BITS DOMAIN — bitwise operations (2026-06-17, broaden the verifiable domains). |
| `valide_blackboard` | VALIDATION blackboard.py (Wave 7). |
| `valide_blockchain` | VALIDATES blockchain.py — ADVERSARIAL, FAUX=0. |
| `valide_bma` | VALIDATION of BAYESIAN MODEL AVERAGING (bma.py) — judged by calibration.py. |
| `valide_bootstrap` | VALIDATION of the BOOTSTRAP CI (bootstrap.py) — judged by calibration.py. |
| `valide_bootstrap_savoir` | BOOTSTRAP_SAVOIR — the AI builds a multi-level taxonomy ON ITS OWN by tracing back the definitions. |
| `valide_borel_kolmogorov` | VALIDATION of the BOREL-KOLMOGOROV PARADOX (borel_kolmogorov.py). |
| `valide_boucle` | Validation of BRICK 4 (the orchestration loop). |
| `valide_boucle_bornee` | BOUNDED LOOP — early stopping, in a fixed schema (the control part that remained deferred). |
| `valide_boucle_invention` | VALIDATES the boucle_invention capstone (need->assembly->gap->corroboration->writeback) — ADVERSARIAL, FAUX=0. |
| `valide_braess` | VALIDATION of BRAESS'S PARADOX (braess.py). |
| `valide_braille` | VALIDATES braille.py — bijection + round-trip + FAUX=0 (explicit domain, abstention outside the table). |
| `valide_branche` | BRANCHING — lifting the last wall of the ceiling (CONTROL), on a narrow perimeter. |
| `valide_budget` | POWER BUDGET — the 2nd notch (2026-06-17, Yohan's vision "spend power to match the need", by- |
| `valide_budget_personnel` | VALIDATES budget_personnel.py — held-out ADVERSARIAL. |
| `valide_cadrage` | VALIDATION of the FRAMING EFFECT (cadrage.py). |
| `valide_calcul_infinitesimal` | VALIDATES calcul_infinitesimal.py — ADVERSARIAL, FAUX=0. |
| `valide_calculabilite` | VALIDATES calculabilite.py — held-out ADVERSARIAL, FAUX=0. |
| `valide_calendrier_bits_geo` | CALENDAR BRICK + BITS & GEOMETRY EXTENSIONS (2026-06-19) — gaps MEASURED by gap_probe 3rd wave: |
| `valide_calibrateurs` | VALIDATION of the PARAMETRIC CALIBRATORS (calibrateurs.py) — judged by calibration.py. |
| `valide_calibration` | VALIDATION of the CALIBRATION INSTRUMENT (calibration.py) — the Tier 2 judge judges ITSELF by MONTE-CA |
| `valide_calibration_ranking` | VALIDATION of RANKING CALIBRATION (calibration_ranking.py) — judged by calibration.py. |
| `valide_calibration_sequence` | VALIDATION of SEQUENCE CALIBRATION (calibration_sequence.py) — judged by calibration.py. |
| `valide_capacites` | VALIDATES capacites.py — manifest of formula/concept capabilities. |
| `valide_cardinalite` | VALIDATES cardinalite.py — held-out ADVERSARIAL. |
| `valide_cardiologie` | VALIDATES cardiologie.py — held-out ADVERSARIAL. |
| `valide_carte` | DEEPEN THE MAP — which walls are SOFT (close by seeding), which is the REAL one. |
| `valide_carte_limites` | CARTE_LIMITES_FRANCAIS — the model-free frontier is measured, not asserted. |
| `valide_cartographie` | VALIDATES cartographie.py — held-out ADVERSARIAL. |
| `valide_cas_limites` | VALIDATION cas_limites.py (Wave 6). |
| `valide_causal` | VALIDATION of CAUSAL INFERENCE (causal.py) — judged by calibration.py. |
| `valide_causalite` | VALIDATION of CAUSALITY (causalite.py) — Wave 1. |
| `valide_ceramiques` | VALIDATES ceramiques.py — held-out ADVERSARIAL (FAUX=0). |
| `valide_cesar` | CAESAR CIPHER (powerful brick) — mod 26 shift (ord/chr). |
| `valide_chaines_avancees` | ADVANCED STRINGS — anagram/substring/replace. |
| `valide_changepoint` | VALIDATION of CHANGEPOINT DETECTION (changepoint.py). |
| `valide_chaos` | VALIDATES chaos.py — held-out ADVERSARIAL. |
| `valide_charge_lexique` | CHARGE_LEXIQUE — scalable lexicon ingester (Wiktionary route) — coherence is verified, not assumed. |
| `valide_chemin` | PATH / EXPLANATION (COMPREHENSION brick) — the chain linking x to y (the "because"). |
| `valide_chemin2d` | VALIDATION of chemin2d.py — paths (lines + cubic Bézier), SVG <path> export. |
| `valide_chercheur_invention` | VALIDATION of the AUTONOMOUS INVENTION SEEKER (chercheur_invention.py). |
| `valide_chevauchement` | OVERLAP BRICK / INTERVAL SWEEP (sweep-line) (2026-06-19) — ±1 events at the bounds, sort, max c |
| `valide_chiffres` | DECIMAL DECOMPOSITION — sum/count/reverse of digits. |
| `valide_chimie` | VALIDATES chimie.py — held-out ADVERSARIAL. |
| `valide_chimie_quantitative` | VALIDATES chimie_quantitative.py — ADVERSARIAL, FAUX=0. |
| `valide_choix_social` | VALIDATION of SOCIAL CHOICE (choix_social.py). |
| `valide_chomage` | VALIDATES chomage.py — held-out ADVERSARIAL. |
| `valide_choquet` | VALIDATION of the CHOQUET INTEGRAL (choquet.py) — judged by calibration.py. |
| `valide_chronobiologie` | VALIDATES chronobiologie.py — held-out ADVERSARIAL. |
| `valide_citoyennete` | VALIDATES citoyennete.py — ADVERSARIAL. |
| `valide_classes_complexite` | VALIDATES classes_complexite.py — held-out ADVERSARIAL, FAUX=0. |
| `valide_classif` | VALIDATION of CALIBRATED CLASSIFICATION (classif_calibree.py) — is the calibration repair REAL |
| `valide_classif_multiclasse` | VALIDATION of CALIBRATED MULTI-CLASS CLASSIFICATION (classif_multiclasse.py) — judged by calibration.py. |
| `valide_classification_surfaces` | VALIDATES classification_surfaces.py — held-out ADVERSARIAL, FAUX=0. |
| `valide_classifieur` | VALIDATION of the DOMAIN-NATURE CLASSIFIER. |
| `valide_classifieur_bornage` | VALIDATES classifieur_bornage.py — the status router: |
| `valide_cloture` | CLOSURE — a mechanism composes over an INVENTED atom (invention -> registry -> composition). |
| `valide_cloud_distribue` | VALIDATES cloud_distribue.py — ADVERSARIAL, FAUX=0. |
| `valide_coherence_physique` | VALIDATES coherence_physique.py — held-out ADVERSARIAL. |
| `valide_combinatoire` | GENERATIVE COMBINATORICS — permutations/subsets/product. |
| `valide_commerce_international` | VALIDATES commerce_international.py — held-out ADVERSARIAL. |
| `valide_commun` | COMMON VALIDATOR HELPERS — machine thinking: |
| `valide_comparatif` | COMPARATIVE (PRODUCTION + COGNITION) — expressing an a/b comparison via an agreeing adjective, RULE-GOVERNED hence VERIFIA |
| `valide_completude` | COMPLETENESS AUDIT (2026-06-17) — outside the INTERFACE and outside the GPU, is NOTHING missing across absolutely all the pla |
| `valide_complexite` | VALIDATES complexite.py — held-out ADVERSARIAL, FAUX=0. |
| `valide_compose` | VERTICAL FUSION — 2nd stage: |
| `valide_compose_profond` | INDUSTRIALIZING DEPTH — composition nests beyond depth 2 (taller skill towers) |
| `valide_composites` | VALIDATES composites.py — held-out ADVERSARIAL. |
| `valide_compounding` | THE AUTONOMOUS CLIMB (compounding) — the most informative test of the project. |
| `valide_compounding_arite` | COMPOUNDING of ARITY 2 — an arity-2 compound feeds the present (goal 2, continued). |
| `valide_compounding_stress` | compounding STRESS — PUSH to the ceiling, and LOCATE the cause (goal 1 before goal 2). |
| `valide_comprehension` | Validation of COMPREHENSION (1/2) — abstracting by compression. |
| `valide_comprehension_definition` | DEFINITION COMPREHENSION (COMPREHENSION brick) — decomposing a definition into genus + difference. |
| `valide_comprehension_generale` | GENERAL COMPREHENSION — transform + filter(aggregate) + reduce in ONE pass (the remaining "real" front). |
| `valide_comprehension_integree` | INTEGRATED COMPREHENSION — the ASSEMBLED engine understands a sentence end to end (verify the integrated, not the iso |
| `valide_comprehension_phrase` | SENTENCE COMPREHENSION (COMPREHENSION brick — sense + logic) — who does what (SVO roles around the verb). |
| `valide_comptabilite` | VALIDATES comptabilite.py — held-out ADVERSARIAL. |
| `valide_comptage` | COUNTING (COMPREHENSION brick — quantitative) — how many / which of a set belong to a category. |
| `valide_comptage_combinatoire` | COMBINATORIAL COUNTING BRICK (2026-06-19) — GenerateurComptageCombinatoire: |
| `valide_comptage_membre` | MEMBERSHIP COUNTING — `sum(c in LIT for c in s)` (family D: |
| `valide_concentration` | VALIDATION of the CONCENTRATION BOUNDS (concentration.py) — judged by calibration.py. |
| `valide_conditionnel` | PRESENT CONDITIONAL (FORM brick, mood) — built on the infinitive + imperfect endings, RULE-GOVERNED hence VE |
| `valide_confidentialite_differentielle` | VALIDATION of DIFFERENTIAL PRIVACY (confidentialite_differentielle.py). |
| `valide_conformal` | VALIDATION of CONFORMAL PREDICTION (conformal.py) — the DISTRIBUTION-FREE coverage guarantee, proven by |
| `valide_conformal_adaptatif` | VALIDATION of ADAPTIVE CONFORMAL (conformal_adaptatif.py) — does coverage hold UNDER DRIFT? Judged by ca |
| `valide_conformal_jackknife` | VALIDATION of JACKKNIFE+ (conformal_jackknife.py) — judged by calibration.py. |
| `valide_conformal_label` | VALIDATION of LABEL-CONDITIONAL CONFORMAL (conformal_label.py). |
| `valide_conformal_normalise` | VALIDATION of HETEROSCEDASTIC CONFORMAL (conformal_normalise.py) — the CONDITIONAL coverage, judged by ca |
| `valide_conformal_pondere` | VALIDATION of WEIGHTED CONFORMAL (conformal_pondere.py) — judged by calibration.py. |
| `valide_conformal_quantile` | VALIDATION of CQR (conformal_quantile.py) — judged by calibration.py. |
| `valide_conjonction` | VALIDATION of the CONJUNCTION FALLACY (conjonction.py). |
| `valide_conjugaison` | VALIDATES conjugaison.py — ADVERSARIAL. |
| `valide_conjugaison2` | CONJUGATION GROUP 2 (-ir with -iss-) — knocks down the `finir` wall ; rule-governed hence verifiable. |
| `valide_conjugaison_generateur` | CONJUGATION (language FORM brick) — conjugating is RULE-GOVERNED hence VERIFIABLE (the SENSE, however, has no judge). |
| `valide_conservation` | VALIDATION of the CONSERVATION BALANCE (conservation.py) — Wave 3. |
| `valide_conservation_aliments` | VALIDATES conservation_aliments.py — held-out ADVERSARIAL. |
| `valide_consolidation` | Validation of CONSOLIDATION: |
| `valide_contrainte` | VALIDATION of the CONSTRAINT SOLVER (contrainte.py) — Wave 2. |
| `valide_controle` | VALIDATES controle.py — ADVERSARIAL, FAUX=0. |
| `valide_controle_qualite` | VALIDATES controle_qualite.py — held-out ADVERSARIAL. |
| `valide_conversation` | CONVERSATION MEMORY — validation (Yohan's mandate 2026-06-25, "the gap of ephemeral intelligence"). |
| `valide_conversion` | BASE CONVERSION (2026-06-17, "transcription" faculty) — dec↔bin↔hex. |
| `valide_convertit_en` | multilingual CONVERTIT_KAIKKI — the genus MECHANISM is agnostic: |
| `valide_convertit_kaikki` | CONVERTIT_KAIKKI — Wiktionary-dump -> core-lexicon bridge, VERIFIED on REAL kaikki records (in li |
| `valide_coordination` | VALIDATES coordination.py — held-out ADVERSARIAL. |
| `valide_coordonnees` | VALIDATES the COORDINATES ingestion (ingere_coordonnees.py) + the ia wiring (coordonnees_lieu / distance_lieux |
| `valide_copules` | VALIDATION of the COPULAS (copules.py). |
| `valide_coreference` | COREFERENCE (COMPREHENSION brick — discourse) — resolving a pronoun to its antecedent by gender. |
| `valide_cosmologie` | VALIDATES cosmologie.py — held-out ADVERSARIAL, FAUX=0. |
| `valide_cout_irrecuperable` | VALIDATION of the SUNK COST FALLACY (cout_irrecuperable.py). |
| `valide_covariance_grande_dim` | VALIDATION of HIGH-DIMENSIONAL COVARIANCE (covariance_grande_dim.py). |
| `valide_croissance_bacterienne` | VALIDATES croissance_bacterienne.py — held-out ADVERSARIAL. |
| `valide_croyance_dempster_shafer` | VALIDATION of the BELIEF FUNCTIONS (croyance_dempster_shafer.py). |
| `valide_cryobiologie` | VALIDATES cryobiologie.py — held-out ADVERSARIAL. |
| `valide_cryptographie_appliquee` | VALIDATES cryptographie_appliquee.py — ADVERSARIAL, FAUX=0. |
| `valide_curateur` | Validation of BRICK 8 (the curator). |
| `valide_curiosite_dirigee` | DIRECTED CURIOSITY — steering invention toward the hole, measured in judge-calls (the EXPLORATION wall). |
| `valide_cybernetique` | VALIDATES cybernetique.py — held-out ADVERSARIAL. |
| `valide_cycles_biogeochimiques` | VALIDATES cycles_biogeochimiques.py — held-out ADVERSARIAL. |
| `valide_cycles_economiques` | VALIDATES cycles_economiques.py — held-out ADVERSARIAL. |
| `valide_decidabilite` | VALIDATES decidabilite.py — held-out ADVERSARIAL, FAUX=0. |
| `valide_decision` | VALIDATION of DECISION UNDER UNCERTAINTY (decision.py). |
| `valide_decision_ambiguite` | VALIDATION of DECISION UNDER AMBIGUITY (decision_ambiguite.py). |
| `valide_decouverte_loi` | VALIDATION decouverte_loi.py (Wave 4). |
| `valide_deduction` | VALIDATION — DEDUCTION ENGINE (the memory that reasons). |
| `valide_dedup` | ORDERED DEDUP (powerful brick) — set state (already-seen). |
| `valide_delta_debug` | VALIDATION of delta_debug.py — ddmin. |
| `valide_demande` | DEMANDE — the query interface "speech" (2026-06-17). |
| `valide_demographie` | VALIDATES demographie.py — held-out ADVERSARIAL. |
| `valide_derive_calibration` | VALIDATION of the CALIBRATION DRIFT DETECTOR (derive_calibration.py). |
| `valide_desambiguisation` | MULTI-CHANNEL DISAMBIGUATION (SENSE brick: |
| `valide_deux_enveloppes` | VALIDATION of the TWO-ENVELOPE PARADOX (deux_enveloppes.py). |
| `valide_dict_accu` | DICT as ACCUMULATOR — building a key -> measure dictionary (theme I: |
| `valide_dict_transform` | DICTIONARY TRANSFORMATION — rewriting an EXISTING dict (next front, theme 8). |
| `valide_dimensions` | VALIDATION of DIMENSIONAL ALGEBRA (dimensions.py) — Wave 1 founding brick. |
| `valide_direction` | Validation of DIRECTION — the comprehension that STEERS the living loop. |
| `valide_dirichlet_imprecis` | VALIDATION of the IMPRECISE DIRICHLET (dirichlet_imprecis.py) — judged by calibration.py. |
| `valide_dirichlet_process` | VALIDATION of the DIRICHLET PROCESS (dirichlet_process.py). |
| `valide_distance_semantique` | SEMANTIC DISTANCE (COMPREHENSION brick) — closeness of sense on the is-a graph. |
| `valide_diviseurs` | DIVISOR THEORY — divisors/count/prime factors. |
| `valide_dkw` | VALIDATION of the DKW BAND (dkw.py). |
| `valide_document_pdf` | VALIDATES document_pdf.py — exact xref (offset-independent scan) + structure + FAUX=0. |
| `valide_donnees_manquantes` | VALIDATION of MISSING DATA (donnees_manquantes.py) — judged by calibration.py. |
| `valide_dp2d` | DP 2D BRICK / DYNAMIC PROGRAMMING OVER TWO SEQUENCES (2026-06-19) — dp[m+1][n+1] table by recurrence (di |
| `valide_drake` | VALIDATES drake.py — held-out ADVERSARIAL. |
| `valide_dunning_kruger` | VALIDATION of the DUNNING-KRUGER effect as an artifact (dunning_kruger.py). |
| `valide_e_process` | VALIDATION of the E-PROCESS / TESTING BY BETTING (e_process.py). |
| `valide_echantillon_pondere` | VALIDATION of WEIGHTED ESTIMATION (echantillon_pondere.py) — judged by calibration.py. |
| `valide_eclipses` | VALIDATES eclipses.py — held-out ADVERSARIAL. |
| `valide_ecologie` | VALIDATES ecologie.py — held-out ADVERSARIAL, FAUX=0. |
| `valide_editeur` | VALIDATES editeur.py — ADVERSARIAL, FAUX=0. |
| `valide_electronique` | VALIDATES electronique.py — ADVERSARIAL, FAUX=0. |
| `valide_ellsberg` | VALIDATION of the ELLSBERG PARADOX (ellsberg.py). |
| `valide_energies_comparees` | VALIDATES energies_comparees.py — held-out ADVERSARIAL. |
| `valide_ensemble_calibre` | VALIDATION of the CALIBRATED ENSEMBLE (ensemble_calibre.py). |
| `valide_ensembles` | SET DOMAIN — algebra of two sets (2026-06-17, broaden the verifiable domains). |
| `valide_entrainement` | VALIDATES entrainement.py — held-out ADVERSARIAL (FAUX=0). |
| `valide_entropie_thermo` | VALIDATES entropie_thermo.py — held-out ADVERSARIAL (second law / entropy). |
| `valide_environnement` | VALIDATION of environnement.py — polyglot portfolio: |
| `valide_equa_diff` | VALIDATES equa_diff.py — held-out ADVERSARIAL. |
| `valide_equilibre` | BALANCE BRICK / DEPTH-COUNTER SCAN (2026-06-19) — scanning a string while maintaining a depth |
| `valide_equilibre_chimique` | VALIDATES equilibre_chimique.py — ADVERSARIAL, FAUX=0. |
| `valide_equivalence_semantique` | VALIDATION of equivalence_semantique.py. |
| `valide_ergodicite` | VALIDATION of ERGODICITY (ergodicite.py). |
| `valide_erreurs_variables` | VALIDATION of ERRORS-IN-VARIABLES (erreurs_variables.py) — judged by calibration.py. |
| `valide_essais_cliniques` | VALIDATES essais_cliniques.py — held-out ADVERSARIAL. |
| `valide_etat` | VALIDATION of STATES & VARIABLES (etat.py) — Wave 1. |
| `valide_etats_matiere` | VALIDATES etats_matiere.py — ADVERSARIAL, FAUX=0. |
| `valide_etend_savoir` | ETEND_SAVOIR — the AI extends its taxonomy ON ITS OWN by transitive closure (INJECTED fetcher, offline, reproduc |
| `valide_executeur_c` | VALIDATION of the C backend (executeur.ExecuteurC) — first COMPILED language judged by the SAME judge (compile && exe |
| `valide_executeur_niches` | VALIDATION of the NICHE backends Prolog/R/SQL (executeur_niches) — 3 PARADIGMS judged by the SAME judge, sentin |
| `valide_executeurs_compiles` | VALIDATION of the COMPILED backends C++/Rust/Go (executeur) — the SAME judge compiles+runs+judges each, sentinel |
| `valide_exp3` | VALIDATION of the ADVERSARIAL BANDIT EXP3 (exp3.py). |
| `valide_exploits` | Validation of BRICK 5 (the exploit observatory). |
| `valide_externalites` | ADVERSARIAL VALIDATION of EXTERNALITIES (externalites.py). |
| `valide_extraction` | VALIDATION extraction.py (Wave 8). |
| `valide_fabrique_comprehension` | FABRIQUE_COMPREHENSION — verified training corpus of ALL comprehension (capstone of the mandate). |
| `valide_fabrique_francais` | FABRIQUE_FRANCAIS — French FORM dataset, verified by teacher↔brick agreement (the judge decides). |
| `valide_fabrique_semantique` | FABRIQUE_SEMANTIQUE — comprehension dataset verified by the official oracle (the definition = the truth). |
| `valide_fait_negatif` | VALIDATION of fait_negatif.py — three-valued negative fact at the store. |
| `valide_falsification` | VALIDATION falsification.py (Wave 6). |
| `valide_fdr_controle` | VALIDATION of FDR CONTROL (fdr_controle.py) — judged by calibration.py. |
| `valide_feminin` | FEMININE (language FORM brick: |
| `valide_fenetre` | SLIDING WINDOW — aggregate over CONTIGUOUS subsequences of size k (next front, theme 1). |
| `valide_fermi` | VALIDATION of FERMI ESTIMATION (fermi.py) — judged by calibration.py. |
| `valide_filtre_seuil` | PARAMETERIZED FILTER (powerful brick) — filter/reduce by a threshold COMING FROM THE INPUT (args[1]). |
| `valide_fonction` | LIGHTWEIGHT validator of NL routing → FUNCTION subsystems (fonction_nl.resout_fonction). |
| `valide_fractales` | VALIDATES fractales.py — held-out ADVERSARIAL, FAUX=0. |
| `valide_fragments_riches` | Validation of RICH FRAGMENTS — broaden the vocabulary, not the engine. |
| `valide_fraicheur` | VALIDATION fraicheur.py (Wave 8). |
| `valide_frame` | VALIDATION of the N-ARY FRAME (frame.py) — Wave 1. |
| `valide_fusion` | VERTICAL FUSION — 1st stage: |
| `valide_fusion_collections` | BROADEN STAGE 1 — fusion of expressions to SET and DICT comprehensions (vocabulary). |
| `valide_fusion_large` | BROADEN stage 1 — how far EXPRESSION fusion reaches (before stepping up a notch). |
| `valide_fuzz` | Validation of BRICK 6 (the security sieve / differential fuzzing). |
| `valide_g0` | Validation of G0 — THE FLOOR (random generator). |
| `valide_g1` | Validation of G1 — REUSE OF THE STORE (the memory). |
| `valide_g2` | Validation of G2 — SYNTHESIS FROM BRICKS (the scaffolding that bootstraps). |
| `valide_g3` | Validation of G3 — ablation of the scaffolding. |
| `valide_g4` | G4 — QUANTIFY THE WALL: |
| `valide_g5` | Validation of G5 — RECOMBINATION (autonomy: |
| `valide_galois` | VALIDATES galois.py — held-out ADVERSARIAL, FAUX=0. |
| `valide_generateur` | Validation of BRICK 3 (the generator). |
| `valide_generation` | SENTENCE GENERATION (COMPREHENSION brick — production) — the AI writes a complete sentence from a sense. |
| `valide_generation_coherente` | COHERENT GENERATION — the AI produces complete TOTALLY coherent sentences (grammar + semantics + re-a |
| `valide_generer_tester` | GENERATE-AND-TEST — the n-th integer satisfying a predicate (last niche of theme II: |
| `valide_genetique` | VALIDATES genetique.py — held-out ADVERSARIAL. |
| `valide_genie_chimique` | VALIDATES genie_chimique.py — ADVERSARIAL, FAUX=0. |
| `valide_geometrie` | INTEGER COMPUTATIONAL GEOMETRY BRICK (2026-06-19) — GenerateurGeometrie: |
| `valide_geometrie2d` | VALIDATION of geometrie2d.py — bounded core of vector drawing. |
| `valide_geometrie3d` | VALIDATION of geometrie3d.py — 3D meshes. |
| `valide_geometrie_differentielle` | VALIDATES geometrie_differentielle.py — held-out ADVERSARIAL, FAUX=0. |
| `valide_geometrie_projective` | VALIDATES geometrie_projective.py — ADVERSARIAL, FAUX=0. |
| `valide_geometries_non_euclidiennes` | VALIDATES geometries_non_euclidiennes.py — held-out ADVERSARIAL. |
| `valide_geotechnique` | VALIDATES geotechnique.py — ADVERSARIAL, FAUX=0. |
| `valide_gestion_risque` | VALIDATES gestion_risque.py — held-out ADVERSARIAL. |
| `valide_gibbard_satterthwaite` | VALIDATION of GIBBARD-SATTERTHWAITE (gibbard_satterthwaite.py). |
| `valide_glaciologie` | VALIDATES glaciologie.py — held-out ADVERSARIAL (KNOWN non-circular anchors + soundness + determinism). |
| `valide_godel` | VALIDATES godel.py — held-out ADVERSARIAL, FAUX=0. |
| `valide_good_turing` | VALIDATION of GOOD-TURING (good_turing.py). |
| `valide_goodhart` | VALIDATION of GOODHART'S LAW (goodhart.py). |
| `valide_grandeur` | VALIDATION of the TYPED QUANTITY (grandeur.py) — Wave 1. |
| `valide_grandeur_vectorielle` | VALIDATION of grandeur_vectorielle.py — dimensioned vector quantities. |
| `valide_graphe` | GRAPHS — neighbours/degree/vertices/edge on an edge list. |
| `valide_graphe_typé` | VALIDATION of the 3 STRUCTURAL bricks promoted 🟡→🟢 (2026-07-02) on the REAL corpus: |
| `valide_graphique` | VALIDATES graphique.py — EXACT affine projection (re-derived oracle) + deterministic renders + FAUX=0. |
| `valide_group_by` | GROUP-BY — grouping pairs by key and aggregating (theme I: |
| `valide_groupes` | VALIDATES groupes.py — ADVERSARIAL, FAUX=0. |
| `valide_habitabilite` | VALIDATES habitabilite.py — held-out ADVERSARIAL. |
| `valide_heraldique` | VALIDATES heraldique.py — closed catalogue + exact contrast rule + FAUX=0 (abstention outside the catalogue). |
| `valide_hierarchie_normes` | VALIDATES hierarchie_normes.py — held-out ADVERSARIAL. |
| `valide_homeostasie` | VALIDATES homeostasie.py — held-out ADVERSARIAL. |
| `valide_hydraulique` | VALIDATES hydraulique.py — ADVERSARIAL, FAUX=0. |
| `valide_hydrologie` | VALIDATES hydrologie.py — held-out ADVERSARIAL. |
| `valide_ia` | VALIDATION of the UNIFIED ENTRY POINT (ia.py) — the façade routes correctly to each subsystem, preserving the |
| `valide_identite` | VALIDATION of CANONICAL IDENTITY (identite.py) — Wave 1. |
| `valide_imbrique` | NESTED DATA — iterating two levels (theme I: |
| `valide_immunite` | VALIDATES immunite.py — held-out ADVERSARIAL. |
| `valide_imperatif` | IMPERATIVE (FORM brick, mood) — RULE-GOVERNED form hence VERIFIABLE (-er: |
| `valide_importance_sampling` | VALIDATION of IMPORTANCE SAMPLING & ESS (importance_sampling.py). |
| `valide_impression_3d` | VALIDATES impression_3d.py — held-out ADVERSARIAL. |
| `valide_incertitude` | VALIDATION of the UNCERTAINTY JUDGE (incertitude.py) — UNBOUNDED SOUNDNESS = CALIBRATION, verified by SIM |
| `valide_incertitude_decomposee` | VALIDATION of the EPISTEMIC/ALEATORIC DECOMPOSITION (incertitude_decomposee.py) — judged by calibration.py. |
| `valide_index_ordonne` | ORDERED INDEXING — access driven by a 2nd input (next front, theme 3). |
| `valide_induction_horn` | VALIDATION of induction_horn.py — Horn-rule induction validated by examples. |
| `valide_industrie40` | valide_industrie40.py — adversarial validation of industrie40.py (TRS/OEE). |
| `valide_inference` | LOGICAL INFERENCE (COMPREHENSION brick — logic) — 3-valued deduction (yes/no/unknown) over premises. |
| `valide_inference_anytime` | VALIDATION of ANYTIME-VALID INFERENCE (inference_anytime.py). |
| `valide_inflation` | VALIDATES inflation.py — held-out ADVERSARIAL. |
| `valide_info_gap` | VALIDATION of INFO-GAP DECISION (info_gap.py). |
| `valide_information_calcul` | VALIDATES information_calcul.py — ADVERSARIAL, FAUX=0. |
| `valide_ingere_dump` | INGERE_DUMP — streaming + deduplication of the full dump, VERIFIED on a local mini-dump (reproducible, without n |
| `valide_ingestion_espace_mineraux` | VALIDATION of the veins ingested 2026-07-02 (autonomous run): |
| `valide_intention` | INTENTION / GOAL (SENSE brick: |
| `valide_interface` | VALIDATION of the interface — tests the BACKEND without a browser (lightweight, sound, autonomous). |
| `valide_interrogation` | INTERROGATION (PRODUCTION brick) — turning a sense into a question (inversion + euphonic -t-), RULE-GOVERNED hence VERIF |
| `valide_intervalle_tolerance` | VALIDATION of the TOLERANCE INTERVAL (intervalle_tolerance.py) — judged by calibration.py. |
| `valide_intrication` | VALIDATES intrication.py — held-out ADVERSARIAL. |
| `valide_intrus` | ODD-ONE-OUT / COMMON CATEGORY (COMPREHENSION brick) — category logic on the sense graph. |
| `valide_invariant` | STRUCTURAL PREDICATE — "x invariant under a primitive": |
| `valide_invention` | INVENTION by MUTATION — minting a NEW atom, judged by reality (the wall AFTER). |
| `valide_invention_atomes` | VALIDATES invention_atomes.py — the invention engine returns ATOMS with the right status (atom contract), FAUX=0. |
| `valide_invention_compounding` | CLOSED LOOP: |
| `valide_invention_divergente` | VALIDATION of invention_divergente.py — the 6 invention modes OUTSIDE recombination (Yohan's priority #1), wired |
| `valide_invention_gap` | VALIDATION of the INVENTION-DISCOVERY ENGINE (moteur_invention.py). |
| `valide_invention_portee` | THE SCOPE OF MUTATION — how far invention-by-mutation mints, and where it stops. |
| `valide_invention_substrat` | INVENTION by SUBSTRATE ENUMERATION — crossing the wall of mutation (missing language token). |
| `valide_invention_vivante` | INVENTION IN THE LIVING LOOP — the system climbs AND creates its own bricks, autonomously. |
| `valide_iteration` | ITERATION / FIXED-POINT BRICK (2026-06-19) — repeating a scalar step until a condition. |
| `valide_jensen` | VALIDATION of JENSEN'S INEQUALITY (jensen.py). |
| `valide_jeux_appliques` | VALIDATES jeux_appliques.py — held-out ADVERSARIAL. |
| `valide_jeux_zero_somme` | VALIDATION of ZERO-SUM GAMES (jeux_zero_somme.py). |
| `valide_jointure` | VERTICAL FUSION — GOAL 2: |
| `valide_jointure_profonde` | DEEP JOIN — joining two DEEP sub-results by an op (end of family C of the map). |
| `valide_jointure_profonde_stress` | DEEP JOIN STRESS — putting the brick to the test (Yohan's instruction: |
| `valide_journalisme_deontologie` | VALIDATES journalisme_deontologie.py — held-out ADVERSARIAL. |
| `valide_juge` | Validation of BRICK 1 (the judge). |
| `valide_juge_rapide` | EQUIVALENCE + SAFETY of the FAST JUDGE (fork) vs the reference subprocess judge. |
| `valide_jury_condorcet` | VALIDATION of the CONDORCET JURY THEOREM (jury_condorcet.py). |
| `valide_kalman_robuste` | VALIDATION of the ROBUST KALMAN FILTER (kalman_robuste.py). |
| `valide_kde` | VALIDATION of KDE (kde.py). |
| `valide_kelly` | VALIDATION of the KELLY CRITERION (kelly.py). |
| `valide_langages_formels` | VALIDATES langages_formels.py — held-out ADVERSARIAL, FAUX=0. |
| `valide_langue_ia` | VALIDATION of the LANGUAGE wiring of ia.py — `ia.conjugue` / `ia.ecris` / `ia.comprends` / `ia.comprends_texte` (the |
| `valide_lecteur` | VALIDATION of the GENERIC DATA READER (`lecteur.py`) — the engine of bounded DATA (workstream #3). |
| `valide_lecteur_client` | VALIDATES lecteur_daemon + lecteur_client — the interactive FAST PATH (OPTIM), FAUX=0, without regression. |
| `valide_lecteur_norme` | VALIDATION of VALUE normalization before conflict (lecteur._norme_valeur, hardening 2026-07-02). |
| `valide_lecteur_nuit` | FAUX=0 validator of the veins ingested during the autonomous NIGHT 2026-06-29 (Lever 3 harvester). |
| `valide_lecteur_t10` | VALIDATION T10 — SPORT & COMPETITIONS (ingestion corridor). |
| `valide_lecteur_t11` | VALIDATION T11 — TRANSPORT, VEHICLES & INFRASTRUCTURE (ingestion corridor). |
| `valide_lecteur_t12` | T12 VALIDATOR — FAUX=0 sanity of the RELIGION / MYTHOLOGY / PHILOSOPHY relations (OFFLINE). |
| `valide_lecteur_t4` | T4 SANITY — LIVING corridor (biology). |
| `valide_lecteur_t5` | VALIDATION T5 — CULTURAL WORKS (creators/production). |
| `valide_lecteur_t6` | T6 VALIDATOR — FAUX=0 sanity of the PERSONS & ORGANIZATIONS relations (OFFLINE). |
| `valide_lecteur_t7` | VALIDATION T7 — NUMERICAL MEASURES & TECHNICAL (ingestion corridor). |
| `valide_lecteur_t8` | VALIDATION T8 — HISTORY, DATES & POLITICS (ingestion corridor). |
| `valide_lecteur_t9` | VALIDATION T9 — LANGUAGE, LEXICON & WRITING (ingestion corridor). |
| `valide_lecture_comprehension` | READING & COMPREHENSION — the AI reads facts and answers by LOGIC (capstone of the comprehension mandate). |
| `valide_liaisons_chimiques` | VALIDATES liaisons_chimiques.py — held-out ADVERSARIAL. |
| `valide_limite` | VALIDATION of the THEORETICAL LIMIT & GAP (limite.py) — Wave 3. |
| `valide_lindley` | VALIDATION of LINDLEY'S PARADOX (lindley.py). |
| `valide_liste_transforms` | LIST TRANSFORMS — rotation/blocks/interleave. |
| `valide_localisation_faute` | VALIDATION of localisation_faute.py — spectrum-based localization (Ochiai) + repair by search. |
| `valide_logique` | LOGIC DOMAIN — counting quantifiers (2026-06-17, broaden the verifiable domains). |
| `valide_logique_tri` | VALIDATION logique_tri.py (Wave 1). |
| `valide_logistique` | VALIDATES logistique.py — held-out ADVERSARIAL. |
| `valide_loi` | VALIDATION of the MANIPULABLE LAWS (loi.py) — Wave 2. |
| `valide_loi_grands_nombres` | VALIDATION of the MISUNDERSTOOD LAW OF LARGE NUMBERS (loi_grands_nombres.py). |
| `valide_loi_puissance` | VALIDATION of the HEAVY-TAILED LAWS (loi_puissance.py). |
| `valide_lord` | VALIDATION of LORD'S PARADOX (lord.py). |
| `valide_main_chaude` | VALIDATION of the GAMBLER'S FALLACY & HOT HAND (main_chaude.py). |
| `valide_malediction_dimension` | VALIDATION of the CURSE OF DIMENSIONALITY (malediction_dimension.py). |
| `valide_map_repli` | MAP-THEN-FOLD — folding an aggregator over a sequence TRANSFORMED by a primitive (family C of the map). |
| `valide_maritime` | VALIDATES maritime.py — ADVERSARIAL, FAUX=0. |
| `valide_marketing_mecanismes` | VALIDATES marketing_mecanismes.py — held-out ADVERSARIAL. |
| `valide_marketing_metrics` | VALIDATES marketing_metrics.py — held-out ADVERSARIAL. |
| `valide_math_avance` | ADVANCED MATH (analysis/computation faculty) — isqrt/lcm/comb/pow_mod. |
| `valide_maths_discretes` | VALIDATES maths_discretes.py — held-out ADVERSARIAL, FAUX=0. |
| `valide_maths_financieres` | VALIDATES maths_financieres.py — held-out ADVERSARIAL. |
| `valide_matrice` | 2D MATRIX — STRUCTURAL operations on a list of lists (next front, theme 2). |
| `valide_matrice_confusion` | VALIDATION of the CONFUSION MATRIX & BASE RATE (matrice_confusion.py). |
| `valide_matrice_reduce` | MATRIX + REDUCE (powerful brick) — reducing row/column aggregates to a scalar. |
| `valide_maximum_entropie` | VALIDATION of MAXIMUM ENTROPY (maximum_entropie.py). |
| `valide_maxwell` | VALIDATES maxwell.py — held-out ADVERSARIAL. |
| `valide_mdl` | VALIDATION of MDL (mdl.py). |
| `valide_mecanique` | VALIDATES mecanique.py — ADVERSARIAL, FAUX=0. |
| `valide_mecanismes` | VALIDATES mecanismes.py — held-out ADVERSARIAL. |
| `valide_mecanismes_machines` | VALIDATES mecanismes_machines.py — held-out ADVERSARIAL. |
| `valide_mecanismes_reactionnels` | VALIDATES mecanismes_reactionnels.py — held-out ADVERSARIAL, FAUX=0. |
| `valide_medecines_alternatives` | VALIDATES medecines_alternatives.py — held-out ADVERSARIAL. |
| `valide_memoire` | VALIDATION — PERSISTENT BRICK MEMORY (learns / retains / reuses, sound). |
| `valide_mereologie` | VALIDATION of MEREOLOGY (mereologie.py) — Wave 1. |
| `valide_mesure` | Validation of BRICK 7 (the learning meter). |
| `valide_mesures_sociales` | VALIDATES mesures_sociales.py — held-out ADVERSARIAL. |
| `valide_meta` | INTEGRATED META-ROUTER (2026-06-19, Yohan's vision "adapt to the situation, route by key/x/y like the brain |
| `valide_meta_analyse` | VALIDATION of META-ANALYSIS (meta_analyse.py) — judged by calibration.py. |
| `valide_microprocesseurs` | VALIDATES microprocesseurs.py — ADVERSARIAL, FAUX=0. |
| `valide_mineraux` | VALIDATES mineraux.py — held-out ADVERSARIAL. |
| `valide_monnaie` | MAKING CHANGE (powerful brick) — optimization DP (min coins). |
| `valide_moteur_raisonnement` | VALIDATION of the end-to-end WIRING (moteur_raisonnement.py) — the bricks truly talk to each other. |
| `valide_mots` | STRING PARSING — split / transform / rejoin the WORDS (family D: |
| `valide_multicalibration` | VALIDATION of MULTICALIBRATION (multicalibration.py) — judged by calibration.py applied PER GROUP. |
| `valide_multientree` | MULTI-INPUT COMPOSITION — lifting the arity ≥ 2 wall (joining several arguments). |
| `valide_multilabel` | VALIDATION of MULTI-LABEL CALIBRATION (multilabel.py) — judged by calibration.py + risque_conforme. |
| `valide_multinomial_simultane` | VALIDATION of the SIMULTANEOUS MULTINOMIAL CIs (multinomial_simultane.py) — judged by calibration.py. |
| `valide_multipasse` | MULTI-PASS — filtering by an AGGREGATE of the WHOLE (theme II of the next front: |
| `valide_mur` | DIAGNOSTIC — mapping the WALL (measure and analyze before deciding). |
| `valide_mutation_comparaisons` | MUTATION OF COMPARISONS → INVENTED PREDICATES, in the living loop (the wall before control). |
| `valide_mutation_testing` | VALIDATION of mutation_testing.py. |
| `valide_mutations` | VALIDATES mutations.py — held-out ADVERSARIAL. |
| `valide_navigation` | VALIDATES navigation.py — ADVERSARIAL, FAUX=0. |
| `valide_negation` | NEGATION (COMPREHENSION brick — sentence) — understanding "ne…pas": |
| `valide_negation_phrase` | NEGATION (PRODUCTION) — turning a sense into a negative sentence (ne…pas bracketing), RULE-GOVERNED hence VERIFIABLE. |
| `valide_neurone_biologique` | VALIDATES neurone_biologique.py — held-out ADVERSARIAL. |
| `valide_no_free_lunch` | VALIDATION of the NO FREE LUNCH THEOREM (no_free_lunch.py). |
| `valide_nombres_complexes` | VALIDATES nombres_complexes.py — held-out ADVERSARIAL. |
| `valide_nomenclature_chimique` | VALIDATES nomenclature_chimique.py — held-out ADVERSARIAL. |
| `valide_normalisation` | NORMALIZATION / ROBUSTNESS (SENSE brick: |
| `valide_nouveaute` | VALIDATION of NOVELTY DETECTION (nouveaute.py). |
| `valide_noyau_comprehension` | COMPREHENSION CORE — letting REALITY decide the SCOPE of deduplication, EXHAUSTIVELY (idea of Yoh |
| `valide_nucleosynthese` | VALIDATES nucleosynthese.py — held-out ADVERSARIAL. |
| `valide_opinions` | VALIDATION of OPINION AGGREGATION (opinions.py) — judged by scores_propres.py. |
| `valide_optimisation` | DECISION / OPTIMIZATION — choosing the BEST element by a derived criterion (2026-06-17, cognitive brick 2/2 |
| `valide_optimisation_bayesienne` | VALIDATION of BAYESIAN OPTIMIZATION (optimisation_bayesienne.py) — judged by calibration.py. |
| `valide_oracle_definitions` | ORACLE DEFINITIONS — the official definition = truth -> self-built knowledge -> provable new domain |
| `valide_orchestrateur_invention` | VALIDATION of orchestrateur_invention.py — the multi-mode capstone. |
| `valide_orchestre` | THE ORCHESTRATOR — a single façade over the whole toolkit, in DIRECTED ESCALATION. |
| `valide_ordinaux` | VALIDATES ordinaux.py — ADVERSARIAL, FAUX=0. |
| `valide_p_box` | VALIDATION of the P-BOXES (p_box.py) — judged by calibration.py. |
| `valide_p_hacking` | VALIDATION of P-HACKING (p_hacking.py). |
| `valide_pac_bayes` | VALIDATION of the PAC-BAYES bounds (pac_bayes.py). |
| `valide_paires` | PAIRS — ∃ quantification over all pairs i<j (next front, theme 5). |
| `valide_paradoxes` | VALIDATES paradoxes.py — held-out ADVERSARIAL, FAUX=0. |
| `valide_paraphrase` | PARAPHRASE / SAME SENSE (COMPREHENSION brick) — seeing beyond surface words (synonyms). |
| `valide_pareto` | VALIDATION pareto.py (Wave 5). |
| `valide_parrondo` | VALIDATION of PARRONDO'S PARADOX (parrondo.py). |
| `valide_parseur_fichiers` | VALIDATION of parseur_fichiers.py — format router. |
| `valide_parsing` | STRUCTURED PARSING (2026-06-17, "analysis/transcription" faculty) — string -> dict/list. |
| `valide_participe_present` | PRESENT PARTICIPLE (FORM brick, -ant) — RULE-GOVERNED verb form hence VERIFIABLE. |
| `valide_pascal_mugging` | VALIDATION of PASCAL'S PROBLEM (pascal_mugging.py). |
| `valide_passe_compose` | PASSÉ COMPOSÉ (COMPOUND FORM brick) — compound tense = auxiliary avoir + past participle, RULE-GOVERNED hence VERIFIA |
| `valide_pedologie` | VALIDATES pedologie.py — held-out ADVERSARIAL. |
| `valide_petits_nombres` | VALIDATION of the LAW OF SMALL NUMBERS (petits_nombres.py). |
| `valide_petrochimie` | VALIDATES petrochimie.py — held-out ADVERSARIAL. |
| `valide_pharmacochimie` | VALIDATES pharmacochimie.py — ADVERSARIAL, FAUX=0. |
| `valide_physique` | VALIDATES physique.py — held-out ADVERSARIAL. |
| `valide_pib` | VALIDATES pib.py — held-out ADVERSARIAL. |
| `valide_pile` | STACK / MONOTONE BRICK (2026-06-19) — GenerateurPile: |
| `valide_planification` | VALIDATION planification.py (Wave 5). |
| `valide_plastiques` | VALIDATES plastiques.py — held-out ADVERSARIAL. |
| `valide_plateau` | THE MAP OF THE CEILING — measuring WHERE composition-over-seeded-atoms stalls, and WHY. |
| `valide_pli` | VERTICAL FUSION — 2nd stage, variant 2b: |
| `valide_pluriel` | PLURAL (language FORM brick: |
| `valide_poisson` | VALIDATION of POISSON ESTIMATION (poisson.py) — judged by calibration.py. |
| `valide_poisson_nonhomogene` | VALIDATION of the NON-HOMOGENEOUS POISSON PROCESS (poisson_nonhomogene.py) — judged by calibration.py. |
| `valide_polyglotte` | MULTI-LANGUAGE GENERATION (2026-06-17) — the AI WRITES code in a language other than Python, verified by the exe |
| `valide_polymeres` | VALIDATES polymeres.py — held-out ADVERSARIAL. |
| `valide_population_pays` | VALIDATES the population_pays ingestion (World Bank) + the ia.densite_pays wiring — ADVERSARIAL, FAUX=0. |
| `valide_portefeuille_universel` | VALIDATION of the UNIVERSAL PORTFOLIO (portefeuille_universel.py). |
| `valide_positionnel` | POSITIONAL LOGIC — aggregates of even vs odd positions (family D: |
| `valide_posologie` | VALIDATES posologie.py — held-out ADVERSARIAL. |
| `valide_possibilite` | VALIDATION of POSSIBILITY THEORY (possibilite.py) — judged by calibration.py. |
| `valide_predicat_mesures` | STRUCTURAL PREDICATE on MEASURES — `m1(x) CMP m2(x)` (family B: |
| `valide_predictif` | VALIDATION of PREDICTIVE CALIBRATION (predictif.py). |
| `valide_prediction` | Validation of COMPREHENSION (2/2) — prediction. |
| `valide_prefixe_commun` | COMMON PREFIX/SUFFIX (powerful brick) — cross-reduction of a list of strings. |
| `valide_premier_unique` | FIRST-UNIQUE BRICK / FREQUENCY THEN FIRST SATISFYING (2026-06-19) — two passes: |
| `valide_prete_a_apprendre` | VALIDATES — THE AI IS READY TO LEARN (2026-06-17). |
| `valide_preuve_propositionnelle` | ADVERSARIAL validator of preuve_propositionnelle — known logical anchors + independent oracle (est_tautolog |
| `valide_prevision` | VALIDATION of TIME-SERIES FORECASTING (prevision.py) — judged by calibration.py. |
| `valide_prevision_walley` | VALIDATION of Walley's LOWER/UPPER PREVISIONS (prevision_walley.py) — judged by calibration.py. |
| `valide_prior_shift` | VALIDATION of PRIOR / LABEL SHIFT CORRECTION (prior_shift.py) — judged by calibration.py. |
| `valide_procedes_fabrication` | VALIDATES procedes_fabrication.py — held-out ADVERSARIAL. |
| `valide_procedes_industriels` | Adversarial validator of procedes_industriels (FAUX=0). |
| `valide_processus_gaussien` | VALIDATION of the GAUSSIAN PROCESS (processus_gaussien.py) — judged by calibration.py. |
| `valide_profilage` | VALIDATION of profilage.py — empirical complexity classification (deterministic, on counted operation cost |
| `valide_profond` | RECURSION OVER STRUCTURE (powerful brick) — reducing the leaves of an ARBITRARY-depth nesting. |
| `valide_propagande` | valide_propagande.py — ADVERSARIAL validation of propagande.py. |
| `valide_propagation` | VALIDATION of UNCERTAINTY PROPAGATION (propagation.py) — is the propagated interval CALIBRATED? Judged by c |
| `valide_property_based` | VALIDATION of property_based.py — active falsification. |
| `valide_proportion_binomiale` | VALIDATION of the BINOMIAL PROPORTION INTERVAL (proportion_binomiale.py) — judged by calibration.py. |
| `valide_proprietes_materiaux` | VALIDATES proprietes_materiaux.py — held-out ADVERSARIAL. |
| `valide_proteines` | VALIDATES proteines.py — held-out ADVERSARIAL. |
| `valide_pseudosciences` | VALIDATES pseudosciences.py — closed consensus catalogue + abstention outside the catalogue (FAUX=0). |
| `valide_psychometrie` | VALIDATES psychometrie.py — held-out ADVERSARIAL. |
| `valide_qualitatif` | VALIDATION qualitatif.py (Wave 4). |
| `valide_quantificateur` | QUANTIFIERS (COMPREHENSION brick — logic) — all / some / none over a set, via is-a closure. |
| `valide_quantile_regression` | VALIDATION of QUANTILE REGRESSION (quantile_regression.py) — judged by calibration.py. |
| `valide_quantique` | VALIDATES quantique.py — held-out ADVERSARIAL. |
| `valide_questions` | AI ANSWERER — unified questions/answers, model-free (demonstration of the breadth WITHOUT a model). |
| `valide_rademacher` | VALIDATION of RADEMACHER COMPLEXITY (rademacher.py). |
| `valide_raisonnement_defaut` | VALIDATES raisonnement_defaut.py — exception takes precedence, default on known member, abstention on unknown, FAUX=0. |
| `valide_ranking` | RANKING / PRIORITIZATION — ordering by a derived criterion (2026-06-17, cognitive brick). |
| `valide_rapport_invention` | VALIDATION of the UNIFIED INVENTION REPORT (rapport_invention.py). |
| `valide_raster_png` | VALIDATES raster_png.py — pixel-perfect round-trip + FAUX=0 (rejection of corrupt streams, abstention out of frame). |
| `valide_rayonnement_thermique` | VALIDATES rayonnement_thermique.py — held-out ADVERSARIAL, FAUX=0. |
| `valide_recettes` | VALIDATES recettes.py — held-out ADVERSARIAL. |
| `valide_record` | RECORD WITH GRADUAL COMPLETENESS — 1st brick of the GENERATIVE FRONT (2026-06-17, Yohan's vision "select what o |
| `valide_recurrence` | GENERALIZED CONTROL (1) — TWO-STATE RECURRENCE over a count (the fold/loop have only ONE accumulator). |
| `valide_redox` | VALIDATES redox.py — held-out ADVERSARIAL. |
| `valide_refactor` | VALIDATION of refactor.py — behavior-preserving refactor. |
| `valide_references` | VALIDATES references.py — held-out ADVERSARIAL. |
| `valide_region_multivariee` | VALIDATION of the MULTIVARIATE CONFORMAL REGIONS (region_multivariee.py) — judged by calibration.py. |
| `valide_regle` | VALIDATION of the NORMATIVE RULE ENGINE (regle.py). |
| `valide_regles_induites` | VALIDATION of regles_induites.py — induction→deduction bridge. |
| `valide_regression_fallacieuse` | VALIDATION of SPURIOUS REGRESSION (regression_fallacieuse.py). |
| `valide_regression_moyenne` | VALIDATION of REGRESSION TOWARD THE MEAN (regression_moyenne.py). |
| `valide_regression_robuste` | VALIDATION of ROBUST REGRESSION (regression_robuste.py) — judged by calibration.py. |
| `valide_relation_lexicale` | LEXICAL RELATIONS (SENSE brick lvl.2: |
| `valide_relations_lexique` | RELATIONS_LEXIQUE — dictionary syn/ant wired into the SENSE bricks, VERIFIED on REAL record |
| `valide_relativite_generale` | VALIDATES relativite_generale.py — held-out ADVERSARIAL, FAUX=0. |
| `valide_relativite_restreinte` | VALIDATES relativite_restreinte.py — held-out ADVERSARIAL. |
| `valide_relaxation` | VALIDATION relaxation.py (Wave 5). |
| `valide_repetition` | COUNTED REPETITION — applying a binary op args[1] times (count = 2nd input). |
| `valide_reseaux_ip` | VALIDATES reseaux_ip.py — ADVERSARIAL, FAUX=0. |
| `valide_reseaux_neurones` | VALIDATES reseaux_neurones.py — ADVERSARIAL, FAUX=0. |
| `valide_resolution` | VALIDATION of fuzzy entity resolution (resolution.py) — typo tolerance, FAUX=0. |
| `valide_resoudre_tout` | VALIDATES — CHAINED RESOLUTION (2026-06-22, point 4). |
| `valide_restitution` | VALIDATION — RESTITUTION ENGINE (routed, exact, ACT-R, consolidation, sound). |
| `valide_restitution_fraiche` | VALIDATION of restitution_fraiche.py — freshness gate. |
| `valide_retraite` | VALIDATES retraite.py — held-out ADVERSARIAL. |
| `valide_revelation_bayesienne` | VALIDATION of BAYESIAN REVELATION (revelation_bayesienne.py). |
| `valide_revision` | VALIDATION revision.py (Wave 8). |
| `valide_rhetorique` | VALIDATES rhetorique.py — held-out ADVERSARIAL. |
| `valide_richesse` | RICHNESS LEVEL — the selectable "notch" (2026-06-17, Yohan's vision: |
| `valide_ridge` | VALIDATION of RIDGE REGRESSION (ridge.py). |
| `valide_risque_conforme` | VALIDATION of CONFORMAL RISK CONTROL (risque_conforme.py). |
| `valide_robotique` | VALIDATES robotique.py — ADVERSARIAL, FAUX=0. |
| `valide_robust_bayes` | VALIDATION of ROBUST BAYES by ε-contamination (robust_bayes.py) — judged by calibration.py. |
| `valide_roc_auc` | VALIDATION of AUC + CI (roc_auc.py) — judged by calibration.py. |
| `valide_routage` | AUTO-ROUTING OF THE WRITEBACK — the final weld so that the closure runs AUTONOMOUSLY. |
| `valide_routage_sota` | SOTA ROUTING REFINEMENTS (2026-07-02) — Smith's rule / SUNNY / SATzilla presolve / AutoFolio auto-config. |
| `valide_routage_strategie` | STRATEGY ROUTING BY KEY (2026-06-19, Yohan's idea) — the AI learns, per key, the most effective traversal st |
| `valide_routeur_langage` | VALIDATION of routeur_langage.py — sorts the present+judgeable languages by need. |
| `valide_run_length` | RUN-LENGTH ENCODE — stateful compression with output construction (next front, theme 7). |
| `valide_saint_petersbourg` | VALIDATION of the SAINT PETERSBURG PARADOX (saint_petersbourg.py). |
| `valide_savoir_massif` | SAVOIR_MASSIF — the lexicon wired as a resource of the SENSE bricks, VERIFIED on a small inline taxonomy ( |
| `valide_scores_propres` | VALIDATION of PROPER SCORES (scores_propres.py) — PROPERNESS (a score minimized in expectation by the TRUE |
| `valide_scrutin` | VALIDATES scrutin.py — held-out ADVERSARIAL. |
| `valide_seismologie` | VALIDATES seismologie.py — exact laws (re-derived oracle), inverses, scale invariants, FAUX=0. |
| `valide_semiconducteurs` | VALIDATES semiconducteurs.py — held-out ADVERSARIAL. |
| `valide_sens_executable` | EXECUTABLE SENSE (SENSE brick lvl.3, core of the challenge) — a VERB (word) -> an ACTION that the judge RUNS (grounding |
| `valide_serie` | LONGEST RUN — run-length, state across the sequence (last niche of theme II). |
| `valide_serie_autoregressive` | VALIDATION of AUTOREGRESSIVE FORECASTING (serie_autoregressive.py) — judged by calibration.py. |
| `valide_serie_multivariee` | VALIDATION of VAR MULTIVARIATE FORECASTING (serie_multivariee.py) — judged by calibration.py. |
| `valide_series_calcul` | VALIDATES series_calcul.py — ADVERSARIAL, FAUX=0. |
| `valide_session` | Validation of BRICK 9 (the end-to-end training session). |
| `valide_shiryaev` | VALIDATION of QUICKEST DETECTION (shiryaev.py) — judged by calibration.py. |
| `valide_simpson` | VALIDATION of SIMPSON'S PARADOX (simpson.py). |
| `valide_simulation` | VALIDATION of the SIMULATION / FORWARD-MODEL (simulation.py) — Wave 3. |
| `valide_smooth_ambiguity` | VALIDATION of SMOOTH AMBIGUITY (smooth_ambiguity.py). |
| `valide_sophismes` | valide_sophismes.py — ADVERSARIAL validation of sophismes.py. |
| `valide_sources` | VALIDATION of the SOURCE REGISTRY (`sources.py` / datasets/sources/registry.jsonl). |
| `valide_sous_suite` | LONGEST MONOTONE SUBSEQUENCE (DP/LIS) — NON-contiguous subsequence (next front, theme 4). |
| `valide_stabilite_algorithmique` | VALIDATION of ALGORITHMIC STABILITY (stabilite_algorithmique.py). |
| `valide_statique` | VALIDATES statique.py — ADVERSARIAL, FAUX=0. |
| `valide_statistiques` | STATISTICAL ANALYSIS (2026-06-17, "analysis" faculty) — median/mode/mean/deviation. |
| `valide_stein` | VALIDATION of STEIN'S PARADOX (stein.py). |
| `valide_stereochimie` | VALIDATES stereochimie.py — ADVERSARIAL, FAUX=0. |
| `valide_stoechiometrie` | VALIDATES stoechiometrie.py — ADVERSARIAL, FAUX=0. |
| `valide_store` | Validation of BRICK 2 (the store). |
| `valide_strategie_jeux` | VALIDATES strategie_jeux.py — held-out ADVERSARIAL. |
| `valide_stress_noyau` | HELL+ STRESS / PERF of the comprehension core — REALITY (the judge + its timeout) demands the EFFICIENT form. |
| `valide_structure_mapping` | VALIDATION structure_mapping.py (Wave 4). |
| `valide_structures_genie` | VALIDATES structures_genie.py — held-out ADVERSARIAL, FAUX=0. |
| `valide_subjonctif` | PRESENT SUBJUNCTIVE (FORM brick, mood) — "que je parle", RULE-GOVERNED hence VERIFIABLE. |
| `valide_substrat_physique` | VALIDATION of the SUBSTRAT-RÉEL (substrat_physique.py). |
| `valide_substrat_reel` | VALIDATES substrat_reel.py — the invention gap-engine wired onto the 71 M facts, FAUX=0. |
| `valide_substrat_vivant` | THE SUBSTRATE IN THE LIVING LOOP — invention by enumeration becomes a STAGE of the orchestrator. |
| `valide_suite` | SEQUENCES & PATTERNS BRICK (2026-06-19) — GenerateurSuite: |
| `valide_surapprentissage` | VALIDATION of OVERFITTING (surapprentissage.py). |
| `valide_surdispersion` | VALIDATION of OVERDISPERSION (surdispersion.py) — judged by calibration.py. |
| `valide_surface_ia` | VALIDATION OF THE SURFACE OF ia.py — near-free static gate (AST, no loading of the reader). |
| `valide_survie` | VALIDATION of SURVIVAL ANALYSIS (survie.py) — judged by calibration.py. |
| `valide_systeme` | VALIDATES SYSTEM — HARD COMPOSITE tasks on the climb (Yohan's instruction: |
| `valide_systemes_politiques` | VALIDATES systemes_politiques.py — held-out ADVERSARIAL. |
| `valide_tableur_xlsx` | VALIDATES tableur_xlsx.py — round-trip of values (unzip+XML oracle) + exact A1 refs + FAUX=0. |
| `valide_taux_de_base` | VALIDATION of BASE-RATE NEGLECT (taux_de_base.py). |
| `valide_taxonomie` | VALIDATION of taxonomie.py — data-derived type taxonomy (FAUX=0). |
| `valide_tbm` | VALIDATION of the TRANSFERABLE BELIEF MODEL (tbm.py) — judged by calibration.py. |
| `valide_techniques_culinaires` | VALIDATES techniques_culinaires.py — held-out ADVERSARIAL. |
| `valide_telecom` | VALIDATES telecom.py — ADVERSARIAL, FAUX=0. |
| `valide_teledetection` | VALIDATES teledetection.py — held-out ADVERSARIAL. |
| `valide_temperature` | VALIDATION of TEMPERATURE SCALING (temperature.py) — judged by calibration.py. |
| `valide_temporel` | TEMPORAL LOGIC (COMPREHENSION brick — logic) — ordering events by "before" (topological sort |
| `valide_test_calibration` | VALIDATION of the CALIBRATION TEST (test_calibration.py). |
| `valide_test_permutation` | VALIDATION of the PERMUTATION TEST (test_permutation.py). |
| `valide_theorie_nombres` | NUMBER THEORY BRICK — AGGREGATES OVER 1..n (2026-06-19) — extension of GenerateurDiviseurs: |
| `valide_theorie_reseaux` | VALIDATES theorie_reseaux.py — ADVERSARIAL, FAUX=0. |
| `valide_topographie_arpentage` | VALIDATES topographie_arpentage.py — ADVERSARIAL, FAUX=0. |
| `valide_topologie` | VALIDATES topologie.py — held-out ADVERSARIAL, FAUX=0. |
| `valide_toxicologie` | VALIDATES toxicologie.py — held-out ADVERSARIAL. |
| `valide_trace` | VALIDATION trace.py (Wave 7). |
| `valide_transfert` | VALIDATES transfert.py — the cross-domain assembler. |
| `valide_transport_membranaire` | VALIDATES transport_membranaire.py — held-out ADVERSARIAL. |
| `valide_triangulation` | VALIDATION triangulation.py (Wave 6). |
| `valide_trigonometrie` | VALIDATES trigonometrie.py — ADVERSARIAL, FAUX=0. |
| `valide_turing` | VALIDATES turing.py — ADVERSARIAL, FAUX=0. |
| `valide_types_categories` | VALIDATES types_categories.py — ADVERSARIAL, FAUX=0. |
| `valide_urgence_medicale` | VALIDATES urgence_medicale.py — ADVERSARIAL, FAUX=0. |
| `valide_usinage` | VALIDATES usinage.py — held-out ADVERSARIAL. |
| `valide_utilite` | Validation of the EVOLUTIONARY UTILITY brick. |
| `valide_vague10` | WAVE 10 — computational geometry / CRT / DP / strings (2026-06-19, autonomy). |
| `valide_vague11` | WAVE 11 — Bellman-Ford / spiral / 3D / wildcards / DP / zigzag / max-xor / digits (2026-06-19, autonomy). |
| `valide_vague12` | WAVE 12 — Floyd-Warshall / topo / KMP / Z-function / sum-of-2-squares / variance / consecutive run (2026-06-1 |
| `valide_vague13` | WAVE 13 — DP (word break, profit, decodings) / combinatorics (Bell, Stirling) / integer determinant / Möbius / |
| `valide_vague14` | WAVE 14 — INTERVAL SCHEDULING (web transfer) + breadth (2026-06-19, night). |
| `valide_vague15` | WAVE 15 — MONOTONE STACK + GREEDY (2026-06-20, night). |
| `valide_vague16` | WAVE 16 — DP / two-pointers / window / stack / string (2026-06-20, night, 1.5 GB protocol). |
| `valide_vague17` | WAVE 17 — greedy / DP / window / arithmetic strings (2026-06-20, night, 1.5 GB). |
| `valide_vague18` | WAVE 18 — dates / 3D geometry / game theory / bits / cellular automaton (2026-06-20, night, 1.5 GB). |
| `valide_vague19` | WAVE 19 — Excel / strings / DP / number theory (2026-06-20, night, 1.5 GB). |
| `valide_vague20` | WAVE 20 — counting / numeration / string (2026-06-20, night, 1.5 GB). |
| `valide_vague21` | WAVE 21 — parsing / digits / strings / DP / greedy (2026-06-20, night, 1.5 GB). |
| `valide_vague22` | WAVE 22 — number theory / DP / string / bits / geometry (2026-06-20, night, 1.5 GB). |
| `valide_vague23` | WAVE 23 — arithmetic strings / stack / numbers / array (2026-06-20, night, 1.5 GB). |
| `valide_vague24` | WAVE 24 — DP / arrays / bits (2026-06-20, night, 1.5 GB). |
| `valide_vague25` | WAVE 25 — DP / window / BFS grid / bits (2026-06-20, night, 1.5 GB). |
| `valide_vague26` | WAVE 26 — arrays / DP / stack / bits / string (2026-06-20, night, 1.5 GB). |
| `valide_vague27` | WAVE 27 — stack / arrays / numeration / bits (2026-06-20, night, 1.5 GB). |
| `valide_vague28` | WAVE 28 — arrays / unique / stats / numeration (2026-06-20, night, 1.5 GB). |
| `valide_vague29` | WAVE 29 — strings / numeration / arrays (2026-06-20, night, 1.5 GB). |
| `valide_vague30` | WAVE 30 — arrays / digits / DP-2D / strings (2026-06-20, night, 1.5 GB). |
| `valide_vague31` | WAVE 31 — matrix / numeration / digits / strings (2026-06-20, night, 1.5 GB). |
| `valide_vague32` | WAVE 32 — arrays / grid / strings (2026-06-20, night, 1.5 GB). |
| `valide_vague33` | WAVE 33 — arrays / grid / string / numeration (2026-06-20, night, 1.5 GB). |
| `valide_vague34` | WAVE 34 — arrays / strings (2026-06-20, night, 1.5 GB). |
| `valide_vague35` | WAVE 35 — arrays / numeration (2026-06-20, night, 1.5 GB). |
| `valide_vague36` | WAVE 36 — strings (2026-06-20, night, 1.5 GB). |
| `valide_vague37` | WAVE 37 — number theory / numeration (2026-06-20, night, 1.5 GB). |
| `valide_vague38` | WAVE 38 — matrix / grid / DP (2026-06-20, night, 1.5 GB). |
| `valide_vague39` | WAVE 39 — sets / numbers (2026-06-20, night, 1.5 GB). |
| `valide_vague4` | WAVE 4 — graph connectivity / base conversions / str_index (2026-06-19). |
| `valide_vague40` | WAVE 40 — in-place lists / order statistic / greedy / strings (2026-06-20, resumed after restart, 1.5 |
| `valide_vague41` | WAVE 41 — CONFIRMATION (2026-06-20, resumed after restart, 1.5 GB). |
| `valide_vague42` | WAVE 42 — DEEP (DP/greedy/combinatorics) (2026-06-20, resumed after restart, 1.5 GB). |
| `valide_vague43` | WAVE 43 — INTERVALS (extended domain) + MATRIX + COMPARATOR-SORT (2026-06-20, resumed after restart, 1.5 |
| `valide_vague44` | WAVE 44 — 2D GRIDS & INTEGER GEOMETRY (2026-06-22 night, autonomy). |
| `valide_vague45` | WAVE 45 — STACK ALGORITHMS (monotone & parsing) (2026-06-22 night, autonomy). |
| `valide_vague46` | WAVE 46 — ADVANCED SEARCH / WINDOW / NUMBER THEORY (2026-06-22 night, autonomy). |
| `valide_vague47` | WAVE 47 — DP CLASSICS (CONFIRMATION, 0 gap) (2026-06-22 night, autonomy). |
| `valide_vague48` | WAVE 48 — GREEDY / HASHING / STRINGS / BITS (CONFIRMATION, 0 gap) (2026-06-22 night, autonomy). |
| `valide_vague49` | WAVE 49 — ADVANCED STRINGS + MODULAR MATH (2026-06-22 night, autonomy). |
| `valide_vague5` | WAVE 5 — strings / number theory / digits / matrices / arrays (2026-06-19, autonomy). |
| `valide_vague50` | WAVE 50 — BACKTRACKING & COUNTING (2026-06-23 night, autonomy). |
| `valide_vague51` | WAVE 51 — TWO-POINTERS / ARRAY PARTITION (2026-06-23 night, autonomy). |
| `valide_vague6` | WAVE 6 — BFS graphs / numeric / matmul / strings / multi-delimiter stack (2026-06-19, autonomy). |
| `valide_vague7` | WAVE 7 — directed graphs / DP / point geometry / combinatorics (2026-06-19, autonomy). |
| `valide_vague8` | WAVE 8 — tree/grid / iterative number theory / DP / strings / geometry (2026-06-19, autonomy). |
| `valide_vague9` | WAVE 9 — weighted graphs / modular numbers / DP / encoding / encryption (2026-06-19, autonomy). |
| `valide_valeurs_extremes` | VALIDATION of EXTREME VALUES (valeurs_extremes.py) — judged by calibration.py. |
| `valide_variational_preferences` | VALIDATION of VARIATIONAL PREFERENCES / MULTIPLIER (variational_preferences.py). |
| `valide_veille` | VALIDATES veille.py — sovereign web access, FAUX=0. |
| `valide_veille_corroboration` | VALIDATES the web->reality->fact-store loop (veille_corroboration) — ADVERSARIAL, FAUX=0. |
| `valide_venn_abers` | VALIDATION of the VENN-ABERS PREDICTOR (venn_abers.py) — judged by calibration.py. |
| `valide_villes_coordonnees` | VALIDATES the LOCALITY coordinates ingestion (Wikidata/QLever P625, scope Q486972) + navigation wiring — ADV |
| `valide_web` | VALIDATES web.py — ADVERSARIAL, FAUX=0. |
| `valide_while` | GENERALIZED CONTROL (2) — WHILE loop driven by a CONDITION (the `while`, gcd class). |
| `valide_will_rogers` | VALIDATION of the WILL ROGERS PHENOMENON (will_rogers.py). |
| `valide_winner_curse` | VALIDATION of the WINNER'S CURSE (winner_curse.py) — judged by calibration.py. |
| `valide_worldbank_eco` | VALIDATES the World Bank eco/social ingestion (6 relations) + the ia.* bridges — ADVERSARIAL, FAUX=0. |
## Conversational assistant — recent modules (cabled to the chat)

These recent modules implement the conversational assistant wired into `interface/repond.py` (detailed in CAPABILITIES):

| Module | Role |
|---|---|
| `grammaire_fr` | French grammatical analysis (part of speech, sentence type, SVO) over an embedded lexicon |
| `formes_verbales` | conjugated-form recognition (Bescherelle models, 116k forms) |
| `fonction_stats_nl` | natural-language statistics router (~46 Tier-2 functions) |
| `explications` | self-contained concept/paradox explanations |
| `extrait_pdf` | PDF text extraction (Tj/TJ + FlateDecode) |
| `lecteur_document` | long-document Q&A (passage + page + table of contents) |
| `ocr` | bounded OCR (templates + features + Otsu) of clean printed text |
| `apprentissage_patrons` | reformulation learning + word-substitution rule induction |
| `confiance` | user corrections (source required) + source banning |
| `langue` | detection + multilingual factual answering (fr/en/es/de/it/pt) |
| `veille_structure` | structured search (Wikidata/QLever/SPARQL) → VERIFIED fact + attributed free web |
| `https_confiance` | trusted TLS egress (pinned-anchor fallback for the .exe) |
| `telecharge_donnees` | installs the full base (~72M facts) from Releases |
