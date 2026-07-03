# Inventaire complet de VERAX

> Généré mécaniquement depuis le code (docstrings + API). Représente l'intégralité des modules livrés.

**1304 modules · 4682 fonctions/classes publiques · 171 496 lignes**


## Noyau — 6 modules

| Module | Rôle | API |
|---|---|---|
| `assistant_nl` | ASSISTANT NL — la PORTE CONVERSATIONNELLE AUTONOME (« gros bond », mandat nuit 2026-07-03). | class Reponse, note_clarification, note_reformulation, oublie_etat, reprend_clarification, apres_hors, complement, qualifie_texte |
| `classifieur_bornage` | CLASSIFIEUR DE BORNAGE — le ROUTEUR DE STATUT du contrat d'atome, gardien anti-hallucination (2026-07-02). | class Classement, classe, regime_atome_pour |
| `ia` | IA — POINT D'ENTRÉE UNIFIÉ (« complet ≠ utilisable » : | juge_dispositif, reference, donnee, donnee_nl, coordonnees_lieu, distance_lieux, cap_lieux, dms_vers_dd |
| `lecteur` | LECTEUR GÉNÉRIQUE DE DONNÉES — le moteur du borné DATA (chantier #3 ; 566 sujets : | class Lecteur, amorce_cherche, cherche, repond, repond_nl |
| `repond` | COUCHE CONVERSATIONNELLE de l'interface — rendre l'assistant capable de RÉPONDRE, sans jamais inventer. | pret, est_fallback, repond |
| `serveur` | INTERFACE LOCALE — petit serveur web souverain par-dessus la mémoire de conversation. | liste_conversations, archive_conversation, desarchive_conversation, lire_conversation, ajoute_message, nouvelle_conversation, oublie_conversation, class Handler |

## Bibliothèque de capacités (moteurs & atomes) — 492 modules

| Module | Rôle | API |
|---|---|---|
| `_nonreg` | NON-RÉGRESSION INCRÉMENTALE + PARALLÈLE (le runner standard, rapide ET sound). | liste_validateurs, modules_locaux, imports_directs, cloture, hash_fichiers, empreinte_datasets, lance, main |
| `abduction` | ABDUCTION — brique Vague 5 (inférence de la meilleure explication). | explique, hypotheses_possibles, meilleure_explication |
| `abstention` | POLITIQUE D'ABSTENTION UNIFIÉE — brique Vague 7 (le capstone de l'honnêteté). | decide, affirme_ou_abstient |
| `aerodynamique` | AÉRONAUTIQUE — vol, aérodynamique (mandat Yohan : | portance, trainee, finesse, reynolds, vol_equilibre |
| `agregation_previsions` | PALIER 2 — AGRÉGATION DE PRÉVISIONS PROBABILISTES (pondération par historique + EXTREMIZE) (brique, 2026-06-26). | brier, poids_track_record, moyenne_logit_ponderee, ajuste_extremize, agrege, moyenne_naive, calibre_agregateur, formule |
| `algebre_boole` | ALGÈBRE DE BOOLE — évaluation EXACTE d'expressions booléennes & tables de vérité, FAUX=0 (formule/concept 2026-06-29). | variables, evalue, table_verite, est_tautologie, est_contradiction, est_satisfiable, equivalent |
| `algebre_calcul` | ALGÈBRE — résolution EXACTE d'équations (linéaires, polynomiales), FAUX=0 (mission formule/concept 2026-06-29). | equation_lineaire, equation_quadratique, evalue_polynome, est_racine |
| `algo_analyse` | ALGO_ANALYSE — analyse de complexité & correction d'algorithmes, MÉCANISME EXACT, FAUX=0 (mission formule/concept 2026-0 | complexite_boucle, compare_asymptotique, nombre_operations_tri, comparaisons_pire_cas, invariant_boucle_somme |
| `allais` | PALIER 2 — PARADOXE D'ALLAIS (violation de l'axiome d'indépendance) : | eu, rdu, schema_allais, contradiction_eu, analyse, formule |
| `allen` | ALGÈBRE D'INTERVALLES D'ALLEN — référentiel TEMPOREL (brique représentation, 2026-07-02). | inverse, relation, avant, chevauche, contient |
| `alliages` | MÉTAUX ET ALLIAGES — règle du levier (lever rule) + catalogue d'alliages binaires (mandat Yohan : | fraction_phase, classe_alliage |
| `analyse_chimique` | ANALYSE CHIMIQUE BORNÉE — méthodes d'analyse (spectroscopie UV-visible, chromatographie). | absorbance, concentration_depuis_absorbance, transmittance, facteur_retention_rf |
| `analyse_fonctionnelle` | ANALYSE FONCTIONNELLE — espaces vectoriels normés, FAUX=0 (mission formule/concept 2026-06-29). | produit_scalaire, norme, distance, cauchy_schwarz_verifiee, sont_orthogonaux, projection |
| `ancrage` | PALIER 2 — EFFET D'ANCRAGE QUANTITATIF : | estimateur_ancre, correlation, simule, analyse, formule |
| `ancres` | BANQUE D'ANCRES NON-CIRCULAIRE — brique fondatrice Vague 6. | class Incoherence, class BanqueAncres |
| `anscombe` | PALIER 2 — QUARTET D'ANSCOMBE / INSUFFISANCE DES STATISTIQUES RÉSUMÉES : | regression, stats_resumees, diagnostics, analyse, formule |
| `arbitre` | ARBITRE DE CONTRADICTION (runtime) — brique Vague 7. | arbitre, valeur_arbitree |
| `architecture` | ARCHITECTURE DES ORDINATEURS — représentation des nombres, FAUX=0 (mission formule/concept 2026-06-29). | vers_binaire, vers_hexa, depuis_binaire, complement_a_deux, depuis_complement_a_deux, addition_binaire |
| `arithmetique_intervalles` | PALIER 2 — ARITHMÉTIQUE D'INTERVALLES : | class Intervalle, evalue, plugin_point, formule |
| `arithmetique_modulaire` | ARITHMÉTIQUE MODULAIRE & CRYPTO — primitives EXACTES (entiers), FAUX=0 (mission formule/concept 2026-06-29). | pgcd, euclide_etendu, inverse_modulaire, exp_modulaire, est_premier, rsa_chiffre, rsa_dechiffre |
| `arret` | Problème de l'arrêt — mécanisme EXACT, FAUX=0. | sarrete_dans, arret_general_decidable, programme_diagonal, argument_diagonal |
| `asteroides` | ASTÉROÏDES & COMÈTES — paramètre de Tisserand (invariant orbital) et classification dynamique EXACTE. | tisserand, classifie, classifie_orbite |
| `astronautique` | ASTRONAUTIQUE — mécanique du vol (capacité de calcul/preuve, mandat Yohan : | delta_v, rapport_de_masse, masse_finale, vitesse_orbitale, vitesse_liberation, periode_orbitale |
| `atome` | CONTRAT D'ATOME — l'unité universelle de connaissance de l'IA (borné ET non-borné), FAUX=0 (2026-07-02, durci). | rouvre, est_refute, class Portee, class Verdict, class Atome, atteste, convention, suppose |
| `audio_wav` | AUDIO WAV — noyau BORNÉ de la modalité SON (PCM non compressé), pur stdlib (2026-07-02). | encode, ecris, decode, silence, sinus, carre |
| `audiologie` | AUDIOLOGIE (audition) — échelle décibel, classification de la perte auditive, faits (mandat Yohan : | niveau_db, classe_perte_auditive, plage_audible_hz, addition_db |
| `audit_ancres` | AUDIT DES ANCRES — quelles relations du lecteur ont une assertion de vérité EXTERNE (non circulaire) ? Le store (dataset | audit |
| `audit_code` | AUDIT DE CODE — le domaine DÉVELOPPEMENT/SÉCURITÉ, borné par des RÈGLES POSÉES (mandat Yohan 2026-06-23). | class Constat, audite, explique |
| `aumann` | PALIER 2 — THÉORÈME D'ACCORD D'AUMANN : | dialogue, analyse, formule |
| `auto_apprend` | AUTO-APPRENTISSAGE AUTONOME (2026-06-22, phase « l'IA crée ce qui lui manque, jugée par la réalité » — vision Yohan). | class MoteurAutonome |
| `auto_invention` | MOTEUR D'AUTO-INVENTION — exploration AUTONOME jugée par la réalité (2026-06-18, cap « réseau de réflexion qui ne dépend | class MoteurAutoInvention |
| `auto_invention_ouverte` | MOTEUR D'AUTO-INVENTION OUVERTE — compositionnel & multi-domaines (2026-06-18, cap project-vision-auto-evolution-verite) | class MoteurOuvert |
| `auto_optimise` | BOUCLE RÉCURSIVE D'AUTO-OPTIMISATION (le « cap final » de Yohan : | cout_expr, optimise_expr, optimise_jusqu_fixe |
| `auto_synthese` | AUTO-SYNTHÈSE PAR SQUELETTES (2026-06-24, ordre Yohan « lui permettre de construire ses propres briques »). | synthetise |
| `automates` | AUTOMATES FINIS (DFA) — simulation EXACTE, FAUX=0 (mission formule/concept 2026-06-29). | accepte, etats_accessibles |
| `automobile` | automobile.py — Mécanique automobile élémentaire (formules établies). | distance_freinage, puissance, rapport_transmission, regime_roue, consommation_100km |
| `bandit` | PALIER 2 — DÉCISION SÉQUENTIELLE SOUS INCERTITUDE : | class Bandit, simule, formule |
| `bandit_contextuel` | PALIER 2 — BANDIT CONTEXTUEL (LinUCB) : | class Agent, simule, analyse, formule |
| `base_faits` | BASE DE FAITS VÉRIFIÉS — les JUGES de lookup pour les catégories où la vérité ne se DÉDUIT pas mais se CONSTATE (cat 2 m | class Fait, normalise, cherche, repond_nl |
| `bases_donnees` | BASES DE DONNÉES — algèbre relationnelle EXACTE, FAUX=0 (mission formule/concept 2026-06-29). | selection, projection, jointure, union, difference, agregat |
| `batteries` | BATTERIES / STOCKAGE ÉLECTRIQUE — primitives EXACTES, directement appelables, FAUX=0 (mission formule/concept). | energie_wh, capacite_Ah_depuis_energie, courant_c_rate, temps_charge, rendement_energetique |
| `bayes` | PALIER 2 — COMBINAISON BAYÉSIENNE D'ÉVIDENCE (brique 2, 2026-06-25). | maj_log_odds, lr_indice, posterior, formule, posterior_correle, rho_empirique |
| `bayes_sequentiel` | PALIER 2 — BAYÉSIEN SÉQUENTIEL (Beta-Bernoulli en ligne, brique 34, 2026-06-25). | betai, quantile_beta, class BetaBernoulli, formule |
| `benford` | PALIER 2 — LOI DE BENFORD : | proba_benford, premier_chiffre, distribution, test_benford, analyse, formule |
| `berkson` | PALIER 2 — PARADOXE DE BERKSON / BIAIS DE COLLISION : | correlation, selectionne_collisionneur, correlation_population, correlation_selectionnee, analyse, formule |
| `bertrand` | PALIER 2 — PARADOXE DE BERTRAND (probabilités géométriques) : | tire_corde_longue, probabilite, analyse, formule |
| `besoin` | BESOIN / OBJECTIF — couche d'OBJECTIFS pour le moteur d'invention (demande Yohan 2026-07-02 : | objectif_reel, decompose, principes, strategies_naturelles, chaines_physiques |
| `biais_longueur` | PALIER 2 — BIAIS DE LONGUEUR / PARADOXE D'INSPECTION & D'AMITIÉ : | moyenne, variance, moyenne_biaisee_taille, echantillonne_biais_taille, correction_harmonique, degre_moyen, degre_voisin_moyen, analyse |
| `biais_publication` | PALIER 2 — BIAIS DE PUBLICATION (file-drawer) : | simule, analyse, formule |
| `biais_survie` | PALIER 2 — BIAIS DE SURVIE (survivorship bias) : | moyenne, survivants, biais, ratio_mills, moyenne_tronquee_normale, taux_succes_survivant, analyse, formule |
| `bibliotheconomie` | bibliotheconomie.py — Bibliothéconomie / sciences de l'information. | classes_dewey, classe_dewey, isbn_valide |
| `bibliotheque_invention` | CAPSTONE RÉCURSIF — phase « SOMMEIL » (DreamCoder) : | promeut_abstraction, etend_bibliotheque, gain_reconnaissance, verifie_non_regression |
| `bifurcations` | THÉORIE DES CATASTROPHES / BIFURCATIONS — stabilité des points fixes et formes normales. | stabilite_point_fixe, stabilite_point_fixe_discret, point_fixe_logistique, multiplicateur_logistique, bifurcation_logistique, nb_points_fixes_pli, nb_points_fixes_fourche |
| `big_bang` | BIG BANG — cosmologie établie (formules/faits sourcés). | age_univers_hubble, abondance_primordiale, temperature_cmb, densite_critique |
| `big_data` | BIG DATA — primitives de traitement à l'échelle, FAUX=0 (mission formule/concept 2026-06-29). | mapreduce, compte_mots, class FiltreBloom, echantillon_reservoir |
| `bioinfo` | BIO-INFORMATIQUE / SÉQUENÇAGE — primitives EXACTES sur séquences ADN/chaînes, FAUX=0 (mission formule/concept). | distance_hamming, taux_gc, complement_inverse, distance_edition |
| `bioingenierie` | BIO-INGÉNIERIE — cinétique enzymatique de Michaelis-Menten (loi ÉTABLIE, mécanisme EXACT). | vitesse, km_vitesse_demi, efficacite_catalytique |
| `biomecanique` | BIOMÉCANIQUE DU GESTE — physique EXACTE du mouvement sportif (mandat Yohan : | portee_projectile, hauteur_max, temps_de_vol, angle_optimal_portee, moment_force, couple, impulsion |
| `biostatistique` | BIOSTATISTIQUE — tests diagnostiques (épidémiologie EXACTE). | sensibilite, specificite, valeur_predictive_positive, valeur_predictive_negative, prevalence, rapport_vraisemblance_positif, rapport_vraisemblance_negatif, exactitude |
| `blackboard` | BLACKBOARD / MÉMOIRE DE TRAVAIL PARTAGÉE — brique fondatrice Vague 7 (l'orchestration). | class Entree, class Blackboard |
| `blockchain` | BLOCKCHAIN / CRYPTOMONNAIES (mécanisme) — intégrité d'une chaîne, FAUX=0 (mission formule/concept 2026-06-29). | hash_bloc, cree_bloc, chaine_valide, merkle_root, preuve_travail_valide |
| `bma` | PALIER 2 — MOYENNAGE BAYÉSIEN DE MODÈLES (BMA) : | ajuste_polynome, bic, predit_modele, poids_bic, ajuste, intervalle_bma, intervalle_meilleur, formule |
| `bootstrap` | PALIER 2 — INTERVALLE DE CONFIANCE PAR BOOTSTRAP (percentile & BCa) pour une statistique ARBITRAIRE (brique, 2026-06-26) | repliques, ic_normal, ic_naif_moyenne, ic_percentile, ic_bca, intervalle, formule |
| `bootstrap_savoir` | BOOTSTRAP_SAVOIR — l'IA construit SEULE une taxonomie multi-niveaux en lisant les définitions (2026-06-18). | genus, graphe, chaine, frontiere, class Savoir |
| `borel_kolmogorov` | PALIER 2 — PARADOXE DE BOREL-KOLMOGOROV : | simule, e_abs_latitude, analyse, formule |
| `boucle` | Brique 4 — LA BOUCLE d'orchestration. | class Rapport, tour, campagne |
| `boucle_invention` | CAPSTONE — LA BOUCLE D'INVENTION COMPLÈTE : | boucle |
| `braess` | PALIER 2 — PARADOXE DE BRAESS : | equilibre_nash, optimum_social, analyse, formule |
| `braille` | BRAILLE — noyau BORNÉ de l'écriture tactile (convention FIXE, bijective), pur stdlib (2026-07-02). | lettre_vers_points, points_vers_lettre, lettre_vers_unicode, unicode_vers_lettre, texte_vers_braille, braille_vers_texte, cellule_ascii |
| `budget_personnel` | budget_personnel.py — Gestion d'un budget personnel : | solde, taux_epargne, regle_50_30_20, capacite_emprunt, reste_a_vivre |
| `cadrage` | PALIER 2 — EFFET DE CADRAGE / INVARIANCE DE DESCRIPTION : | v_prospect, choix_prospect, choix_eu, money_pump, analyse, formule |
| `calcul_infinitesimal` | CALCUL INFINITÉSIMAL — limites, dérivation, intégration EXACTES sur les polynômes, FAUX=0 (formule/concept 2026-06-29). | evalue, derivee, primitive, integrale_definie, limite_polynome_en, limite_rationnelle_en |
| `calculabilite` | Théorie de la calculabilité — MÉCANISME EXACT, FAUX=0. | fonction_ackermann, est_primitive_recursive_ackermann, successeur, recursion_primitive, addition, multiplication, puissance, primitive_recursive |
| `calibrateurs` | PALIER 2 — CALIBRATEURS PARAMÉTRIQUES (brique 18, 2026-06-25). | class CalibrateurPlatt, ajuste_platt, class CalibrateurHistogramme, ajuste_histogramme, class CalibrateurBeta, ajuste_beta, ajuste |
| `calibration` | PALIER 2 — L'INSTRUMENT DE CALIBRATION (le juge transverse, 2026-06-25). | depuis_probas, brier, diagramme_fiabilite, ece, mce, ecart_signe, est_calibre, couverture |
| `calibration_ranking` | PALIER 2 — CALIBRATION DU CLASSEMENT (ranking) : | proba_mieux, ajuste_temperature, classe, dcg, ndcg, calibre, formule |
| `calibration_sequence` | PALIER 2 — CALIBRATION DE SÉQUENCE (confiance d'une génération multi-étapes, type LLM, brique 47, 2026-06-26). | confiance_sequence, ajuste_par_etape, confiance_sequence_calibree, formule |
| `capacites` | CAPACITÉS — manifeste explicite et AUDITABLE des capacités formule/concept de l'IA (mission 2026-06-29). | couvert, preuve_de, sujets_couverts, verifie_tout |
| `cardinalite` | CARDINALITÉ & DÉNOMBRABILITÉ — primitives EXACTES (entiers), FAUX=0 (mission formule/concept 2026-06-29). | cardinal_ensemble, cardinal_parties, couple_cantor, decouple_cantor, est_denombrable |
| `cardiologie` | CARDIOLOGIE QUANTITATIVE — formules cliniques ÉTABLIES (mandat Yohan : | frequence_cardiaque_max, qt_corrige_bazett, fraction_ejection, classe_fc_repos |
| `carte_limites_francais` | CARTE_LIMITES_FRANCAIS — jusqu'où le model-free monte en français, et où est le mur (2026-06-18, Yohan « déterminer les  | carte, verdict, main |
| `cartographie` | CARTOGRAPHIE / SIG / GÉOMATIQUE — calculs EXACTS (mandat Yohan : | echelle_distance_reelle, distance_carte, resolution_au_sol, resolution_au_sol_depuis_dpi, conversion_dms_dd, cm_en_m, cm_en_km |
| `cas_limites` | CAS-LIMITES / ASYMPTOTES / SYMÉTRIES — brique Vague 6 (vérification par les bords). | limite_en, monotone, bornee, parite, homogene_degre |
| `causal` | PALIER 2 — INFÉRENCE CAUSALE SOUS INCERTITUDE (ATE, brique 31, 2026-06-25). | ate_diff_moyennes, ate_ipw, formule |
| `causalite` | CAUSALITÉ — brique Vague 1 (graphe causal + intervention). | class CycleCausal, class GrapheCausal |
| `ceramiques` | CÉRAMIQUES BORNÉ — propriétés des céramiques (faits établis + calculs exacts). | retrait_cuisson, porosite, classe_ceramique, proprietes_ceramique, proprietes_mecaniques, est_fragile, classes_connues |
| `changepoint` | PALIER 2 — DÉTECTION DE POINT DE CHANGEMENT (changepoint, brique 32, 2026-06-25). | statistique, detecte_changement, formule |
| `chaos` | THÉORIE DU CHAOS — sensibilité aux conditions initiales via l'APPLICATION LOGISTIQUE (mandat Yohan, borné « FORMULE »). | iterer_logistique, point_fixe_logistique, sensibilite |
| `charge_lexique` | CHARGE_LEXIQUE — ingesteur de lexique scalable (2026-06-18, « étendre le lexique → gros dataset vérifié »). | ecris, charge, coherence |
| `chemin2d` | CHEMINS 2D — segments de droite + courbes de BÉZIER cubiques, export SVG `<path>` (modalité, 2026-07-02). | class Ligne, class Bezier, class Chemin, cercle_approx |
| `cherche_architecture_max` | RECHERCHE D'ARCHITECTURE — VERSION MAXIMALE (tous les étages, multi-domaine, gros budget, jugée par le RÉEL). | evalue1, main |
| `chercheur_invention` | CHERCHEUR D'INVENTIONS AUTONOME — couche au-dessus de `moteur_invention` vers l'OBJECTIF FINAL (cf. | class Inventaire, inventorie |
| `chimie` | CHIMIE BORNÉE — stœchiométrie de base (mandat Yohan 2026-06-23 : | composition, masse_molaire, nb_atomes, pourcentage_massique, repond_nl |
| `chimie_quantitative` | CHIMIE QUANTITATIVE — solutions, thermochimie, électrochimie, FAUX=0 (formule/concept 2026-06-29). | molarite, dilution, volume_dilution, concentration_massique, enthalpie_reaction, est_exothermique, potentiel_cellule, est_spontanee |
| `choix_social` | PALIER 2 — CHOIX SOCIAL (paradoxe de Condorcet, théorème d'Arrow) : | matrice_majorite, bat, gagnant_condorcet, cycle_condorcet, gagnant_pluralite, gagnant_borda, analyse, formule |
| `chomage` | chomage.py — Marché du travail : | population_active, taux_chomage, taux_activite, taux_emploi |
| `choquet` | PALIER 2 — INTÉGRALE DE CHOQUET & MESURES NON-ADDITIVES (capacités) : | capacite_additive, capacite_croyance, conjuguee, choquet, est_capacite, encadre_esperance, formule |
| `chronobiologie` | chronobiologie.py — Rythmes circadiens et cycles de sommeil (faits établis + arithmétique). | periode_circadienne, nombre_cycles_sommeil, duree_pour_cycles, phase_circadienne |
| `citoyennete` | CITOYENNETÉ (DROITS ET DEVOIRS) — catalogue ÉTABLI, pas une invention. | categorie, est_droit, est_devoir, age_majorite_civique, elements |
| `classes_complexite` | CLASSES DE COMPLEXITÉ (P, NP, NP-complet, NP-difficile, indécidable) — CATALOGUE de faits ÉTABLIS, FAUX=0 (mission formu | classe_probleme, est_dans_p, est_np_complet, est_np_difficile, est_indecidable, dans_np, verification_polynomiale, relation_classes |
| `classif_calibree` | PALIER 2 — CLASSIFICATION CALIBRÉE (brique 4, 2026-06-25). | class Calibrateur, ajuste_isotonique, predit, formule |
| `classif_multiclasse` | PALIER 2 — CLASSIFICATION CALIBRÉE MULTI-CLASSE (brique 7, 2026-06-25). | class CalibrateurMC, ajuste_multiclasse, predit, brier_multiclasse, formule |
| `classification_surfaces` | classification_surfaces.py — Classification des surfaces CLOSES (cas 2D, entièrement résolu). | genre, classifie_surface, est_sphere |
| `classifieur_domaine` | CLASSIFIEUR DE NATURE DE DOMAINE — le GAP de [[project-ia-domaines-realite]], le KEYSTONE. | class Reponse, repond |
| `cloud_distribue` | CLOUD / SYSTÈMES DISTRIBUÉS — mécanismes EXACTS, FAUX=0 (mission formule/concept 2026-06-29). | noeud_responsable, quorum_coherent, cap_choix, facteur_replication_disponibilite |
| `coherence_physique` | COHÉRENCE PHYSIQUE — détecteur d'IMPOSSIBILITÉS (mandat Yohan 2026-06-23, inspiré de l'annonce « Coolzy »). | juge_dispositif, explique |
| `commerce_international` | COMMERCE INTERNATIONAL — identités et lois EXACTES des échanges internationaux (mécanisme, jamais une valeur-pays invent | balance_commerciale, nature_balance, taux_couverture, avantage_comparatif, termes_echange |
| `complexite` | COMPLEXITÉ ALGORITHMIQUE — théorème maître + ordre de croissance asymptotique, EXACTS, FAUX=0 (mission formule/concept 2 | exposant_critique, regime_master, classe_master, ordre_croissance, compare_croissance |
| `composites` | COMPOSITES — loi des mélanges (rule of mixtures), primitives EXACTES directement appelables, FAUX=0 (mission formule/con | module_young_composite, densite_composite, borne_inferieure_reuss |
| `compounding` | LA MONTÉE AUTONOME (compounding) — la boucle vivante. | route, class PasMontee, resoudre, resoudre_niveau, montee, franchies, etages_atteints |
| `comprehension` | LA COMPRÉHENSION (1/2) — abstraire par compression (le « sommeil »). | class Abstraction, abstrais, class Predicteur, confirme |
| `comprehension_integree` | COMPRÉHENSION INTÉGRÉE — l'IA lit UNE phrase et la comprend de bout en bout (2026-06-18, mandat nuit Yohan). | comprend |
| `comptabilite` | comptabilite.py — Comptabilité (règles) : | equation_bilan, resultat_net, fonds_roulement, ratio_liquidite, partie_double |
| `concentration` | PALIER 2 — BORNES DE CONCENTRATION (Hoeffding, empirical-Bernstein) : | hoeffding, empirical_bernstein, gaussien, intervalle, formule |
| `confidentialite_differentielle` | PALIER 2 — CONFIDENTIALITÉ DIFFÉRENTIELLE (mécanisme de Laplace, ε-DP) : | laplace, mecanisme, echelle_bruit, perte_confidentialite, ratio_log_max, composition, borne_avantage, analyse |
| `conformal` | PALIER 2 — PRÉDICTION CONFORME (brique 3, 2026-06-25). | quantile_conforme, intervalle_conforme, ensemble_conforme, formule |
| `conformal_adaptatif` | PALIER 2 — CONFORME ADAPTATIF EN LIGNE (brique 6, 2026-06-25). | class ConformeAdaptatif, formule |
| `conformal_jackknife` | PALIER 2 — JACKKNIFE+ CONFORME (brique 20, 2026-06-25). | intervalle_jackknife_plus, jackknife_plus_moyenne, formule |
| `conformal_label` | PALIER 2 — CONFORME LABEL-CONDITIONAL (Mondrian par classe, brique 22, 2026-06-25). | ajuste_label, ensemble_label, formule |
| `conformal_normalise` | PALIER 2 — CONFORME HÉTÉROSCÉDASTIQUE (brique 9, 2026-06-25). | class ConformeMondrian, intervalle_normalise, formule |
| `conformal_pondere` | PALIER 2 — CONFORME PONDÉRÉ SOUS COVARIATE SHIFT (brique 17, 2026-06-25). | quantile_pondere, intervalle_pondere, poids_ratio_gaussien, formule |
| `conformal_quantile` | PALIER 2 — CQR : | scores_cqr, correction_cqr, ajuste_cqr, intervalle_cqr, formule |
| `conjonction` | PALIER 2 — SOPHISME DE LA CONJONCTION (problème de Linda) & COHÉRENCE DES JUGEMENTS : | bornes_frechet, coherent, sophisme_conjonction, livre_hollandais, analyse, formule |
| `conjugaison` | CONJUGAISON FRANÇAISE RÉGULIÈRE — règles ÉTABLIES de la grammaire (le MÉCANISME est exact, jamais deviné). | groupe, terminaisons_present, conjugue |
| `conservation` | BILAN DE CONSERVATION — brique Vague 3 (ancrage physique). | bilan, viole_conservation, rendement |
| `conservation_aliments` | CONSERVATION DES ALIMENTS — catalogue de méthodes et seuils ÉTABLIS (mandat Yohan : | methode, methodes, zone_danger_temperature, dans_zone_danger, activite_eau_limite, bacteries_inhibees |
| `contrainte` | SOLVEUR DE CONTRAINTES (CSP) — brique fondatrice Vague 2. | class Contrainte, class CSP |
| `controle` | AUTOMATIQUE / CONTRÔLE — stabilité d'un système linéaire, FAUX=0 (mission formule/concept 2026-06-29). | table_routh, est_stable, changements_de_signe |
| `controle_qualite` | CONTRÔLE QUALITÉ — maîtrise statistique des procédés (SPC), primitives EXACTES, FAUX=0. | indice_capabilite_cp, cpk, limites_controle, phi, ppm_hors_specs, six_sigma_ppm |
| `conversation` | MÉMOIRE DE CONVERSATION PERSISTANTE — « qu'elle se rappelle des conversations : | class MemoireConversation, ajoute, reprend, rappelle |
| `convertit_kaikki` | CONVERTIT_KAIKKI — pont d'un dump kaikki.org (Wiktionnaire structuré) vers le format `charge_lexique` (2026-06-18). | genre_grammatical, genus, convertit_entree, convertit, aretes_isa |
| `coordination` | COORDINATION / COMPLEXES — chimie de coordination, mécanisme EXACT, FAUX=0 (formule/concept 2026-06-29). | charge_ligand, denticite, nombre_oxydation_metal, nombre_coordination, compte_electrons_18, respecte_regle_18 |
| `copules` | PALIER 2 — COPULES & DÉPENDANCE DE QUEUE : | borne_inf, borne_sup, independance, clayton, lambda_inf_clayton, echantillon_clayton, proba_jointe_extreme, proba_jointe_independance |
| `cosmologie` | COSMOLOGIE — Expansion de l'univers : | vitesse_recession, distance_hubble, age_univers, decalage_rouge |
| `cout_irrecuperable` | PALIER 2 — SOPHISME DU COÛT IRRÉCUPÉRABLE (effet Concorde) : | continuer_rationnel, continuer_cout_irrecuperable, payoff_forward, escalade_concorde, analyse, formule |
| `covariance_grande_dim` | PALIER 2 — COVARIANCE EN GRANDE DIMENSION (Marchenko-Pastur, rétrécissement de Ledoit-Wolf) : | valeurs_propres, covariance_echantillon, bornes_marchenko_pastur, retrecissement, conditionnement, frobenius, max_correlation_hors_diag, analyse |
| `croissance_bacterienne` | CROISSANCE BACTÉRIENNE BORNÉE — modèle de croissance exponentielle par doublement, mécanisme EXACT. | population, temps_generation, nombre_generations |
| `croyance_dempster_shafer` | PALIER 2 — FONCTIONS DE CROYANCE (Dempster-Shafer) : | cadre, belief, plausibility, intervalle_croyance, conflit, combine_dempster, combine_yager, combine |
| `cryobiologie` | cryobiologie.py — Congélation et conservation (cryobiologie). | vitesse_refroidissement, point_congelation_solution, azote_liquide |
| `cryptographie_appliquee` | CRYPTOGRAPHIE APPLIQUÉE — chiffrements symétriques, FAUX=0 (mission formule/concept 2026-06-29). | chiffre_cesar, dechiffre_cesar, chiffre_vigenere, dechiffre_vigenere, chiffre_xor |
| `curateur` | Brique 8 — LE CURATEUR. | class RapportTache, valide_tache, class CurateurGradue |
| `cybernetique` | CYBERNÉTIQUE BORNÉE — régulation & rétroaction (boucle de commande), bloc « FORMULE » (mandat Yohan : | gain_boucle_fermee, erreur_statique, fonction_sensibilite, transfert_complementaire, gain_ideal, est_stable, effet_retroaction_negative |
| `cycles_biogeochimiques` | CYCLES BIOGÉOCHIMIQUES — temps de résidence, bilans de réservoir et catalogue des grands cycles (capacité de calcul/preu | temps_residence, bilan_equilibre, cycles_connus, cycle |
| `cycles_economiques` | cycles_economiques.py — CATALOGUE établi du cycle économique (cycle des affaires / business cycle). | phases, phase_cycle, phase_suivante, definition_recession, est_recession_technique, type_indicateur, definition_indicateur, indicateurs |
| `decidabilite` | decidabilite.py — Décidabilité / indécidabilité d'un énoncé (problème de décision). | statut_decidabilite, est_decidable, classe_complexite, reference, catalogue |
| `decision` | PALIER 2 — DÉCISION SOUS INCERTITUDE CALIBRÉE (brique 8, 2026-06-25). | utilites_attendues, decide, formule |
| `decision_ambiguite` | PALIER 2 — DÉCISION SOUS AMBIGUÏTÉ : | eu, valeur_maxmin, valeur_maxmax, valeur_hurwicz, regret_pire, choisir, e_admissibles, domine |
| `decouverte_loi` | DÉCOUVERTE SYMBOLIQUE DE LOI — brique Vague 4. | decouvre |
| `deduction` | MOTEUR DE DÉDUCTION — la mémoire qui RAISONNE (pas seulement qui rappelle). | class Regle, class MoteurDeduction |
| `delta_debug` | DELTA-DEBUGGING (ddmin) — minimisation de reproducteur d'échec (brique code avancé, 2026-07-02). | ddmin, est_1_minimal, minimise_texte |
| `demande` | DEMANDE — L'INTERFACE DE REQUÊTE (« la parole », 2026-06-17, recadrage Yohan « il faut pouvoir lui DEMANDER des choses,  | construit_moteur, class Reponse, demande, class AssistantIA |
| `demo_anglais` |  | main |
| `demo_verax` | DÉMO VERAX — « Ou il sait, ou il le dit. | titre, q, calcule, main |
| `demographie` | demographie.py — Démographie (populations, faits) : | taux_croissance_naturel, densite_population, temps_doublement, taux_dependance, indice_fecondite |
| `derive_calibration` | PALIER 2 — DÉTECTEUR DE DÉRIVE DE CALIBRATION (brique 13, 2026-06-25). | class DetecteurDerive, formule |
| `deux_enveloppes` | PALIER 2 — PARADOXE DES DEUX ENVELOPPES : | p_petite_sachant, gain_conditionnel, esperance_gain_inconditionnel, simule, analyse, formule |
| `diable` | TEST DU DIABLE — « tout sert, dans le TOUT » (2026-06-17). | partie_A, partie_B, partie_C, main, partie_A_rapport |
| `dimensions` | ALGÈBRE DIMENSIONNELLE — brique fondatrice (Vague 1, socle de représentation). | class Dimension, homogene, verifie_somme, verifie_egalite, class Unite, convertit, dimension_de, commensurables |
| `dirichlet_imprecis` | PALIER 2 — MODÈLE DE DIRICHLET IMPRÉCIS (IDM, Walley 1996) : | bornes, intervalle_evenement, mle, laplace, predictif_credal, estime, formule |
| `dirichlet_process` | PALIER 2 — PROCESSUS DE DIRICHLET / clustering non-paramétrique : | crp_predictive, esperance_nb_tables, gibbs_dp, nb_clusters, assignation_k_fixe, masse_nouveaute_dp, analyse, formule |
| `dkw` | PALIER 2 — BANDE DE CONFIANCE DKW (Dvoretzky-Kiefer-Wolfowitz ; constante de Massart) : | epsilon, bande, F_n, F_inf, F_sup, ks_statistique, couvre, intervalle_quantile |
| `document_pdf` | DOCUMENT PDF — noyau BORNÉ de la modalité DOCUMENT IMPRIMABLE (PDF 1.4), pur stdlib (2026-07-02). | class Page, class Document, encode, ecris, lit_xref |
| `donnees_manquantes` | PALIER 2 — DONNÉES MANQUANTES : | cas_complet, imputation_multiple, imputation_simple, formule |
| `drake` | DRAKE — Recherche de vie (SETI) : | nombre_civilisations |
| `dunning_kruger` | PALIER 2 — EFFET DUNNING-KRUGER COMME ARTEFACT STATISTIQUE : | simule, moyennes_par_quartile, pente_ecart_competence, analyse, formule |
| `e_process` | PALIER 2 — E-PROCESS / TEST PAR PARI (e-values, Ville) : | e_process_simple, e_process_melange, seuil, p_anytime, test_sequentiel, formule |
| `echafaudage` | G3 — RETIRER L'ÉCHAFAUDAGE ET MESURER (l'ablation). | couverture, briques, retire, ablation, minimal |
| `echantillon_pondere` | PALIER 2 — ESTIMATION SOUS BIAIS D'ÉCHANTILLONNAGE (Horvitz-Thompson / Hájek, brique 28, 2026-06-25). | estime_hajek, estime_ht, n_effectif, intervalle_hajek, formule |
| `eclipses` | eclipses.py — Mécanique des phases lunaires et conditions d'éclipse. | periode_synodique, phase_lune, fraction_illuminee, condition_eclipse |
| `ecologie` | ÉCOLOGIE BORNÉE — écosystèmes & chaînes alimentaires : | energie_niveau, efficacite_ecologique, derivee_proie, derivee_predateur, equilibre_lotka_volterra, proie_equilibre, predateur_equilibre |
| `editeur` | ÉDITEUR DE DÉPÔT — substrat DÉTERMINISTE de création/modification de fichiers, FAUX=0 (souverain, stdlib, offline). | empreinte, class Depot |
| `electronique` | ÉLECTRONIQUE (circuits) — grandeurs CALCULABLES, FAUX=0 (mission formule/concept 2026-06-29). | resistance_serie, resistance_parallele, diviseur_tension, constante_temps_rc, impedance_condensateur, impedance_bobine, frequence_resonance_lc |
| `ellsberg` | PALIER 2 — PARADOXE D'ELLSBERG (aversion à l'ambiguïté / principe de la chose sûre) : | paris_eu, schema_ellsberg, paris_maxmin, analyse, formule |
| `energies_comparees` | energies_comparees.py — Comparaison énergétique fossiles vs renouvelables. | facteur_charge, contenu_energetique, retour_energetique, emissions_co2, facteur_co2_reference |
| `ensemble_calibre` | PALIER 2 — ENSEMBLE CALIBRÉ (stacking de forecasters, brique 15, 2026-06-25). | moyenne_ponderee, class EnsembleCalibre, ajuste_ensemble, formule |
| `entrainement` | entrainement.py — Physiologie de l'entraînement : | un_rep_max_epley, frequence_cardiaque_max, zone_cible_karvonen, vo2max_estime |
| `entropie_thermo` | DEUXIÈME PRINCIPE (ENTROPIE) — primitives thermodynamiques EXACTES, directement appelables, FAUX=0 (mission formule/conc | variation_entropie, entropie_univers, spontane |
| `environnement` | ENVIRONNEMENT & PORTFOLIO POLYGLOTTE — la brique qui « trie les langages selon le besoin » (2026-07-02, vision Yohan). | detecte, disponibles, executeurs_disponibles, pour_besoin, suggestions_install, peut_installer |
| `equa_diff` | ÉQUATIONS DIFFÉRENTIELLES — solutions analytiques et numériques, FAUX=0 (mission formule/concept 2026-06-29). | solution_exponentielle, solution_affine, demi_vie, euler |
| `equilibre_chimique` | ÉQUILIBRES CHIMIQUES — quotient de réaction et sens d'évolution, FAUX=0 (mission formule/concept 2026-06-29). | quotient_reaction, sens_evolution, deplace_equilibre_temperature |
| `equivalence_semantique` | ÉQUIVALENCE SÉMANTIQUE DE FONCTIONS — décider si deux fonctions calculent la MÊME chose (code avancé, 2026-07-02). | sur_domaine, par_echantillon, equivalent |
| `ergodicite` | PALIER 2 — ERGODICITÉ : | moyenne_ensemble, taux_croissance_temporel, trajectoire_multiplicative, trajectoire_additive, analyse, formule |
| `erreurs_variables` | PALIER 2 — ERREURS-EN-VARIABLES : | pente_ols, fiabilite, pente_corrigee, pente_corrigee_ic, pente_ols_ic, formule |
| `essais_cliniques` | ESSAIS CLINIQUES — épidémiologie clinique (mesures d'effet EXACTES). | risque_relatif, reduction_risque_absolue, nombre_sujets_a_traiter, odds_ratio |
| `etat` | ÉTATS & VARIABLES — brique Vague 1. | class ValeurHorsDomaine, class Variable, class Etat, class EspaceEtats |
| `etats_matiere` | ÉTATS DE LA MATIÈRE — état physique selon la température, FAUX=0 (mission formule/concept 2026-06-29). | etat_physique, celsius_vers_kelvin, kelvin_vers_celsius, celsius_vers_fahrenheit, fahrenheit_vers_celsius, nombre_changements_etat |
| `etend_savoir` | ETEND_SAVOIR — auto-extension du savoir par FERMETURE TRANSITIVE depuis kaikki (§6.2 b/c, 2026-06-18). | frontiere, acyclise, etend, chaine, raisonneur, main |
| `executeur` | LA COUTURE MULTI-LANGAGE — l'Executeur. | class Executeur, class ExecuteurPython, class ExecuteurJS, class ExecuteurPerl, class ExecuteurBash, class ExecuteurC, class ExecuteurCpp, class ExecuteurRust |
| `executeur_niches` | EXECUTEURS DE NICHE — Prolog / R / SQL : | class ExecuteurProlog, class ExecuteurR, class ExecuteurSQL |
| `exercices` | LE LOT D'EXERCICES CURÉS — la matière première, fournie de l'EXTÉRIEUR. | — |
| `exp3` | PALIER 2 — BANDIT ADVERSARIAL (EXP3) : | gamma_optimal, exp3, glouton, meilleur_bras_fixe, regret, joue, formule |
| `exploits` | Brique 5 — L'OBSERVATOIRE D'EXPLOITS. | sonde_statique, class Diagnostic, caracterise, class Incident, class Inspecteur |
| `exporte_dataset` | EXPORTE_DATASET — le maillon APPRENDRE, sans GPU (2026-06-17, « rendre l'IA prête à apprendre »). | exporte, resume |
| `externalites` | ÉCONOMIE DES EXTERNALITÉS — mécanisme + catalogue d'exemples sourcés (consensus manuel de microéconomie). | type_externalite, cout_social, taxe_pigou, defaillance_marche, internalisee |
| `extraction` | EXTRACTION DEPUIS SOURCES SALES (texte -> triplets) — brique Vague 8. | extrait, extrait_surs |
| `fabrique_comprehension` | FABRIQUE_COMPREHENSION — le corpus d'entraînement VÉRIFIÉ de toute la compréhension (2026-06-18, capstone du mandat). | fabrique |
| `fabrique_francais` | FABRIQUE_FRANCAIS — dataset français VÉRIFIÉ, model-free (2026-06-18, idée Yohan « entraîner en français » + saut APPREN | instruction, fabrique, resume |
| `fabrique_semantique` | FABRIQUE_SEMANTIQUE — dataset de COMPRÉHENSION français vérifié (2026-06-18, « la définition officielle = la vérité »). | construit_paires, fabrique, resume |
| `fait_negatif` | FAIT NÉGATIF DE 1RE CLASSE (module `fait_negatif`) — distinguer le FAUX-connu de l'INCONNU (représentation, 2026-07-02). | statut_fait, negatifs_certains, coherent |
| `falsification` | FALSIFICATION ACTIVE — brique Vague 6 (Popper : | refute, corrobore, resiste |
| `fdr_controle` | PALIER 2 — CONTRÔLE DU TAUX DE FAUSSES DÉCOUVERTES (multiplicité des TESTS, Benjamini-Hochberg) (brique, 2026-06-26). | naif, bonferroni, benjamini_hochberg, decouvre, formule |
| `fermi` | PALIER 2 — ESTIMATION D'ORDRE DE GRANDEUR (FERMI) AVEC INCERTITUDE (brique 29, 2026-06-25). | estime_fermi, estime_fermi_mc, formule |
| `fonction_nl` | ROUTAGE NL → SOUS-SYSTÈMES FONCTION (module LÉGER — pas de lecteur). | resout_physique, resout_conversion, resout_arithmetique, resout_fonction |
| `fractales` | FRACTALES — dimension d'auto-similarité, primitive EXACTE et directement appelable, FAUX=0 (mission formule/concept 2026 | dimension_similarite, dimension_connue, fractales_connues |
| `fraicheur` | FRAÎCHEUR / PROVENANCE TEMPORELLE — brique Vague 8. | class FaitDate, a_rafraichir, frais |
| `frame` | FRAME N-AIRE RÉIFIÉ — brique Vague 1 (relation à rôles). | register_schema, class RoleInconnu, class Frame |
| `fuzz` | Brique 6 — LE CRIBLE SÉCURITÉ (fuzzing différentiel). | class RapportFuzz, crible |
| `galois` | THÉORIE DE GALOIS — faits ÉTABLIS, mécanisme EXACT, FAUX=0 (mission formule/concept 2026-06-29). | indicatrice_euler, resoluble_par_radicaux, groupe_symetrique_resoluble, groupe_resoluble, groupe_alterne_resoluble, ordre_groupe_symetrique, ordre_groupe_alterne, ordre_groupe_galois_cyclotomique |
| `garde_ressources` | GARDE-RESSOURCES — filet dur kernel pour que l'exploration ne fasse JAMAIS tomber WSL (2026-06-19). | pmap, borne |
| `generateur` | Brique 3 — LE GÉNÉRATEUR. | class Generateur, class GenerateurFactice, class GenerateurApprenant, class GenerateurAmeliorant, class GenerateurAleatoire, class GenerateurBriques, fragments_riches, class GenerateurRecombinant |
| `generation_coherente` | GÉNÉRATION COHÉRENTE — l'IA produit des PHRASES COMPLÈTES et TOTALEMENT COHÉRENTES (2026-06-18, mandat Yohan). | class Ecrivain |
| `genetique` | GÉNÉTIQUE MOLÉCULAIRE BORNÉE (mandat Yohan 2026-06-23 : | complement_adn, complement_inverse, transcrit, codon_vers_aa, traduit, repond_nl |
| `genie_chimique` | GÉNIE CHIMIQUE — réacteurs et distillation, FAUX=0 (mission formule/concept 2026-06-29). | temps_sejour, conversion_cstr_ordre1, conversion_pfr_ordre1, etages_fenske |
| `geometrie2d` | GÉOMÉTRIE CONSTRUCTIVE 2D — noyau BORNÉ du dessin / des plans / des images vectorielles (modalité, 2026-07-02). | class Point, class Affine, class Polygone, class Cercle, scene_svg |
| `geometrie3d` | GÉOMÉTRIE 3D CONSTRUCTIVE — noyau BORNÉ de la modélisation 3D / des plans (modalité, 2026-07-02). | class Point3D, class Affine3D, class Maillage, cube |
| `geometrie_differentielle` | GÉOMÉTRIE DIFFÉRENTIELLE — primitives EXACTES sur les courbes paramétrées planes, FAUX=0 (mission formule/concept 2026-0 | courbure, courbure_graphe, rayon_courbure, longueur_arc_segment, longueur_polyligne, tangente_unitaire, normale_unitaire |
| `geometrie_projective` | GÉOMÉTRIE PROJECTIVE — birapport et invariants, FAUX=0 (mission formule/concept 2026-06-29). | birapport, homographie, est_division_harmonique, conjugue_harmonique |
| `geometries_non_euclidiennes` | GÉOMÉTRIES NON-EUCLIDIENNES — géométrie SPHÉRIQUE (courbure positive constante). | courbure_gauss_sphere, exces_spherique, somme_angles_triangle_spherique, aire_triangle_spherique |
| `geotechnique` | GÉOTECHNIQUE — mécanique des sols, FAUX=0 (mission formule/concept 2026-06-29). | contrainte_verticale, contrainte_effective, coefficient_poussee_active, coefficient_poussee_passive, poussee_active |
| `gestion_risque` | gestion_risque.py — Gestion du risque (finance / assurance) : | esperance_perte, value_at_risk_parametrique, ratio_sharpe, variance_portefeuille_2_actifs, ecart_type_portefeuille_2_actifs, prime_pure |
| `gibbard_satterthwaite` | PALIER 2 — THÉORÈME DE GIBBARD-SATTERTHWAITE (vote stratégique) : | borda, pluralite, majorite2, prefere, trouve_manipulation, taux_manipulables, analyse, formule |
| `glaciologie` | glaciologie.py — Glaciologie : | bilan_massique, vitesse_deformation_glace, epaisseur_equilibre, fraction_emergee_iceberg |
| `godel` | GÖDEL — numérotation de Gödel (cœur TECHNIQUE bijectif, exact) + énoncés des théorèmes d'incomplétude comme FAITS. | code_symbole, godel_numero, decode_godel, theoreme |
| `good_turing` | PALIER 2 — GOOD-TURING / MASSE MANQUANTE & ESPÈCES INVISIBLES : | frequences_de_frequences, masse_manquante, richesse_chao1, proba_inedit_naive, logloss_inedit, analyse, formule, echantillon_zipf |
| `goodhart` | PALIER 2 — LOI DE GOODHART : | correlation, simule, analyse, formule |
| `grandeur` | GRANDEUR TYPÉE — brique Vague 1 (valeur + unité/dimension + incertitude). | class IncoherenceDimensionnelle, class Grandeur, homogene |
| `grandeur_vectorielle` | GRANDEUR VECTORIELLE DIMENSIONNÉE — grandeurs non-scalaires (brique représentation, 2026-07-02). | class GrandeurVectorielle |
| `graphe_monde` | GRAPHE RELATIONNEL TYPÉ (vue navigable du corpus) — promotion de la brique 🟡 (2026-07-02). | est_entite, sortants, voisins, chaine, chemin, verifie_chemin |
| `graphique` | GRAPHIQUE DE DONNÉES — noyau BORNÉ du TRACÉ (bar/ligne/nuage), pur stdlib (2026-07-02). | class Echelle, bornes, class Rect, class Pt, class Disposition, barres, nuage, courbe |
| `groupes` | THÉORIE DES GROUPES (finis) — calculs EXACTS, FAUX=0 (mission formule/concept 2026-06-29). | ordre_element_zn, compose_permutations, ordre_permutation, signature_permutation, est_groupe, lagrange_divise |
| `habitabilite` | HABITABILITÉ BORNÉE — zone habitable circumstellaire & température d'équilibre (mandat Yohan : | temperature_equilibre, zone_habitable, flux_stellaire_recu, dans_zone_habitable |
| `harvester` | HARVESTER — industrialise la DÉCOUVERTE+CLASSIFICATION FAUX=0 des veines d'ingestion (Levier 3, nuit 2026-06-29). | type_propriete, route, propose |
| `heraldique` | HÉRALDIQUE — noyau BORNÉ des règles du blason (convention FERMÉE), pur stdlib (2026-07-02). | categorie, teintes_modernes, contraste_valide, teintures |
| `hierarchie_normes` | HIÉRARCHIE DES NORMES — pyramide de Kelsen (droit français / continental, hiérarchie ÉTABLIE). | rang, superieur, inferieur, meme_rang, conforme, domine, hierarchie |
| `homeostasie` | HOMÉOSTASIE — régulation par rétroaction négative (domaine BORNÉ, mécanisme EXACT). | ecart_consigne, correction, est_regule, consigne_reference |
| `hydraulique` | HYDRAULIQUE — écoulement des fluides, FAUX=0 (mission formule/concept 2026-06-29). | debit_volumique, vitesse_continuite, nombre_reynolds, regime_ecoulement, charge_bernoulli |
| `hydrologie` | HYDROLOGIE (eaux continentales) — débits et écoulements CALCULABLES par formule établie. | debit, methode_rationnelle, ruissellement, manning_vitesse, temps_concentration |
| `identite` | IDENTITÉ CANONIQUE UNIFIÉE — brique fondatrice Vague 1. | class PreuveRequise, class RegistreIdentite |
| `immunite` | IMMUNITÉ / VACCINS — MÉCANISME BORNÉ (sujet « Vaccins (mécanisme) »). | seuil_immunite_groupe, taux_reproduction_effectif, epidemie_eteinte, type_immunite |
| `importance_sampling` | PALIER 2 — ÉCHANTILLONNAGE PRÉFÉRENTIEL & TAILLE EFFECTIVE D'ÉCHANTILLON (ESS) : | normal_pdf, poids, estimateur, ess, erreur_naive, intervalle_naif, analyse, formule |
| `impression_3d` | IMPRESSION 3D (FDM) — paramètres de tranchage CALCULABLES par formule établie (mandat Yohan : | nombre_couches, temps_impression, masse_filament, longueur_filament |
| `incertitude` | PHASE 2 — NON-BORNÉ : | estime_moyenne, estime_proportion, compare_moyennes, predit_intervalle, est_anormal, tendance, formule |
| `incertitude_decomposee` | PALIER 2 — DÉCOMPOSITION ÉPISTÉMIQUE / ALÉATOIRE (brique 38, 2026-06-25). | decompose_echantillon, decompose_ensemble, intervalle_predictif, formule |
| `induction_horn` | INDUCTION DE RÈGLES DE HORN (ILP borné) — produire des règles VALIDÉES pour deduction.py (2026-07-02). | derive, cloture_derives, evalue, induit |
| `industrie40` | industrie40.py — Automatisation / Industrie 4.0. | disponibilite, performance, qualite, oee, est_classe_mondiale |
| `inference_anytime` | PALIER 2 — INFÉRENCE ANYTIME-VALID (séquence de confiance, brique 35, 2026-06-25). | rayon_cs, class SequenceConfiance, formule |
| `inflation` | INFLATION — définitions et calculs EXACTS (mécanisme établi, FAUX=0). | taux_inflation, pouvoir_achat, valeur_reelle, taux_reel, taux_reel_exact |
| `info_gap` | PALIER 2 — DÉCISION INFO-GAP (Ben-Haim) : | pire_cas, meilleur_cas, robustesse, opportunite, choisis, formule |
| `information_calcul` | THÉORIE DE L'INFORMATION (Shannon) — grandeurs CALCULABLES, FAUX=0 (mission formule/concept 2026-06-29). | entropie, entropie_conjointe, information_mutuelle, divergence_kl |
| `intervalle_tolerance` | PALIER 2 — INTERVALLE DE TOLÉRANCE (contenir une PROPORTION de la population, pas la moyenne) (brique, 2026-06-26). | facteur_tolerance, intervalle_tolerance, intervalle_naif, ic_moyenne, formule |
| `intrication` | INTRICATION QUANTIQUE — inégalité de Bell / test CHSH (mandat Yohan : | borne_classique_chsh, borne_quantique_chsh, valeur_chsh, viole_inegalite_bell, etat_bell_correlation |
| `invention_atomes` | PONT MOTEUR D'INVENTION → CONTRAT D'ATOME (2026-07-02). | atome_derivable, atome_temoin, atome_generatif, invente_attribut, invente_dispositif |
| `invention_divergente` | INVENTION DIVERGENTE — câblage des 6 briques qui inventent HORS de la recombinaison de l'existant (2026-07-02). | apprend_loi, leve_contrainte, transfere_analogie, arbitre_compromis, explique_observations, plan_procede, Operateur |
| `jensen` | PALIER 2 — INÉGALITÉ DE JENSEN / « FLAW OF AVERAGES » : | gap_jensen, analyse, formule |
| `jeux_appliques` | THÉORIE DES JEUX APPLIQUÉE — équilibres de jeux classiques en stratégies PURES (bimatrice m×n, focus 2×2). | meilleure_reponse_J1, meilleure_reponse_J2, equilibre_nash_pur, strategie_dominante, pareto_domine, dilemme_prisonnier, bataille_des_sexes, matching_pennies |
| `jeux_zero_somme` | PALIER 2 — JEUX À SOMME NULLE & STRATÉGIE DE SÉCURITÉ (maximin, théorème minimax de von Neumann) (brique 70, 2026-06-27) | securite_ligne, plafond_colonne, meilleure_reponse_ligne, jeu_fictif, analyse, formule |
| `journalisme_deontologie` | JOURNALISME (DÉONTOLOGIE) — catalogue des devoirs établis du/de la journaliste. | liste_principes, principe, respecte_deontologie, est_conforme, principe_concerne, evalue |
| `juge` | Brique 1 — LE JUGE. | class Verdict, class Limites, juge |
| `juge_rapide` | JUGE RAPIDE (fork-par-candidat) — chemin PYTHON uniquement, OPT-IN, verdict BIT-IDENTIQUE au juge subprocess. | juge_fork |
| `jury_condorcet` | PALIER 2 — THÉORÈME DU JURY DE CONDORCET / SAGESSE DES FOULES : | precision_majorite, analyse, formule |
| `kalman_robuste` | PALIER 2 — FILTRE DE KALMAN ROBUSTE : | filtre, nis_moyen, diagnostic, steady_state_P, inflation_pour_coherence, analyse, formule |
| `kde` | PALIER 2 — ESTIMATION DE DENSITÉ PAR NOYAU (KDE) & choix de la fenêtre : | noyau, densite, log_vraisemblance_loo, silverman, h_optimal, n_modes, analyse, formule |
| `kelly` | PALIER 2 — CRITÈRE DE KELLY (pari proportionnel, croissance logarithmique) : | fraction_kelly, croissance, fortune_finale, conseille, formule |
| `langages_formels` | LANGAGES FORMELS & GRAMMAIRES — primitives EXACTES, déterministes, FAUX=0 (mission formule/concept 2026-06-29). | non_terminaux, terminaux, est_forme_normale_chomsky, classe_chomsky, appartient |
| `lecteur_client` | Client léger du daemon lecteur (OPTIM T9 — additif, stdlib pur, AUCUN `import lecteur`). | disponible, cherche, repond_nl |
| `lecteur_daemon` | DAEMON RÉSIDENT du lecteur (OPTIM T9 — additif, stdlib pur). | main |
| `lecture_comprehension` | LECTURE & COMPRÉHENSION — l'IA lit des phrases-faits et répond à des questions par LOGIQUE (2026-06-18, capstone nuit). | class Lecteur |
| `lexique_fr` | LEXIQUE_FR — graine de dictionnaire français CERTIFIÉ (2026-06-18, idée Yohan « la définition officielle = la vérité »). | edges_isa, edges_syn, ancetres |
| `liaisons_chimiques` | LIAISONS CHIMIQUES — nature de la liaison par électronégativité, FAUX=0 (mission formule/concept 2026-06-29). | difference_electronegativite, nature_liaison, pourcentage_ionique |
| `limite` | LIMITE THÉORIQUE & ÉCART — brique Vague 3. | class Limite |
| `lindley` | PALIER 2 — PARADOXE DE LINDLEY : | probit, z_pour_p, facteur_bayes_01, posterior_h0, analyse, formule |
| `localisation_faute` | LOCALISATION DE FAUTE + RÉPARATION PAR RECHERCHE — le cycle debug→fix (code avancé, 2026-07-02). | localise, element_le_plus_suspect, couverture_python, repare |
| `logique_tri` | LOGIQUE TRIVALUÉE + MONDE OUVERT/FERMÉ (logique_tri) — brique Vague 1 (fin du socle de représentation). | class Contradiction, non, et, ou, class BaseTrivaluee |
| `logistique` | logistique.py — Logistique / chaîne d'approvisionnement : | quantite_economique_commande, point_commande, stock_securite, cout_total_stock |
| `loi` | LOIS MANIPULABLES — brique fondatrice Vague 2 (moteur symbolique/numérique). | class Loi, solveur_numerique |
| `loi_grands_nombres` | PALIER 2 — LOI DES GRANDS NOMBRES MAL COMPRISE : | marche, esperance_moyenne, esperance_abs_somme, distribution_temps_en_tete, analyse, formule |
| `loi_puissance` | PALIER 2 — LOIS À QUEUE LOURDE (loi de puissance / Pareto) : | pareto, hill, moyenne, ic_tcl, moyenne_theorique, analyse, formule |
| `lord` | PALIER 2 — PARADOXE DE LORD (score de changement vs ANCOVA) : | genere_groupe, score_changement, ancova, analyse, formule |
| `main_chaude` | PALIER 2 — SOPHISME DU JOUEUR & MAIN CHAUDE (biais de Miller-Sanjurjo) : | estimateur_naif, conditionnelle_flux_long, biais_miller_sanjurjo, detecte_main_chaude, analyse, formule |
| `malediction_dimension` | PALIER 2 — MALÉDICTION DE LA DIMENSION (concentration des distances) : | contraste_distances, coquille_gaussienne, analyse, formule |
| `maritime` | MARITIME — architecture navale, FAUX=0 (mission formule/concept 2026-06-29). | vitesse_coque, vitesse_coque_max, vitesse_coque_depuis_pieds, poussee_archimede, masse_max_flottante, flotte, nombre_froude |
| `marketing_mecanismes` | PUBLICITÉ / MARKETING (MÉCANISMES) — modèles de persuasion publicitaire ÉTABLIS (mandat Yohan : | etape_aida, ordre_aida, rang_aida, principe_cialdini, definition_cialdini, principes_cialdini |
| `marketing_metrics` | marketing_metrics.py — Efficacité d'une campagne (mesurable) : | taux_conversion, ctr, roi, cac, roas |
| `maths_discretes` | MATHS DISCRÈTES — primitives EXACTES (entiers), directement appelables, FAUX=0 (mission formule/concept 2026-06-29). | factorielle, binomial, catalan, derangements, partitions, suite_recurrente, fibonacci, lucas |
| `maths_financieres` | MATHÉMATIQUES FINANCIÈRES (intérêts) — borné FORMULE, la réalité (la définition) juge, jamais un faux. | interet_simple, valeur_acquise_simple, interet_compose, valeur_acquise, valeur_future, valeur_actuelle, annuite_constante, van |
| `matrice_confusion` | PALIER 2 — MATRICE DE CONFUSION, DÉSÉQUILIBRE & TAUX DE BASE : | confusion, exactitude, precision, rappel, specificite, f1, exactitude_equilibree, mcc |
| `maximum_entropie` | PALIER 2 — PRINCIPE DU MAXIMUM D'ENTROPIE (Jaynes) : | entropie, uniforme, maxent_moyenne, deux_points, analyse, formule |
| `maxwell` | ÉQUATIONS DE MAXWELL — conséquences quantitatives EXACTES de l'électromagnétisme du vide. | vitesse_lumiere_calculee, impedance_vide, densite_energie_E, densite_energie_B, densite_energie_totale |
| `mdl` | PALIER 2 — LONGUEUR DE DESCRIPTION MINIMALE (MDL, Rissanen) : | ajuste_poly, rss, codelength, selectionne_mdl, selectionne_train, predit, analyse, formule |
| `mecanique` | MÉCANIQUE (frottements, oscillateurs, fluides) — grandeurs CALCULABLES par formule, FAUX=0 (formule/concept 2026-06-29). | force_frottement, pulsation_ressort, periode_ressort, frequence_ressort, periode_pendule, energie_ressort, pression, pression_hydrostatique |
| `mecanismes` | CONCEPTION MÉCANIQUE — transmission de mouvement et de force (mandat Yohan : | rapport_engrenages, vitesse_sortie, avantage_mecanique_levier, couple_sortie |
| `mecanismes_machines` | MACHINES ET MÉCANISMES — mobilité d'un mécanisme plan (critère de Grübler–Kutzbach). | mobilite, mouvement_determine, est_structure, nature |
| `mecanismes_reactionnels` | MÉCANISMES RÉACTIONNELS — classification des substitutions/éliminations nucléophiles (SN1/SN2/E1/E2) par RÈGLES de chimi | type_substitution, sn2_defavorise_par_encombrement, type_elimination, ordre_cinetique, concerte, passe_par_carbocation, nombre_etapes, stereochimie |
| `medecines_alternatives` | MÉDECINES ALTERNATIVES — niveau de preuve scientifique (catalogue de CONSENSUS établi). | est_catalogue, pratiques, niveau_preuve, depasse_placebo |
| `memoire_briques` | MÉMOIRE DE BRIQUES PERSISTANTE — « l'IA apprend ET RETIENT » (mandat Yohan 2026-06-24). | class MemoireBriques |
| `memoire_faits` | MÉMOIRE D'INFORMATIONS PERSISTANTE — « l'IA ne perd pas le contexte au fil du temps, SANS téras de données, SANS dépendr | class MemoireFaits |
| `mereologie` | MÉRÉOLOGIE (composition partie-tout) — brique Vague 1. | class CycleMereologique, class Assemblage |
| `mesure` | Brique 7 — LE MESUREUR D'APPRENTISSAGE (la boîte de verre). | class Point, evalue, class Diagnostic, analyse, trace |
| `mesure_structure_pertache` | MESURE — « LA STRUCTURE TRANCHE PAR TÂCHE » poussé au max (2026-06-19, mandat Yohan « teste toutes les idées du même pri | st_rr2, st_stride2, st_stride3, st_occam, st_costweight, st_topfirst, main |
| `mesures_sociales` | MESURES SOCIALES — faits sociaux MESURABLES (statistiques d'inégalité et de pauvreté, calculs EXACTS). | mediane, gini, coefficient_gini, taux_pauvrete, seuil_pauvrete, indice_dimension, idh |
| `meta_analyse` | PALIER 2 — MÉTA-ANALYSE (effets aléatoires, brique 37, 2026-06-25). | meta_analyse, formule |
| `microprocesseurs` | MICROPROCESSEURS — portes logiques et ALU, FAUX=0 (mission formule/concept 2026-06-29). | porte, additionneur_complet, alu |
| `mineraux` | mineraux.py — Échelle de Mohs (dureté des minéraux) : | durete_mohs, raye, plus_dur, catalogue |
| `moteur_invention` | MOTEUR DE DÉCOUVERTE D'INVENTIONS — la GRAINE de l'OBJECTIF FINAL de Yohan (cf. | class Verdict, examine_cible |
| `moteur_raisonnement` | MOTEUR DE RAISONNEMENT — CÂBLAGE end-to-end des briques (2026-07-02). | class MoteurRaisonnement |
| `multicalibration` | PALIER 2 — MULTICALIBRATION : | ajuste, applique, applique_lot, formule |
| `multilabel` | PALIER 2 — CALIBRATION MULTI-LABEL (brique 23, 2026-06-25). | class CalibrateurMultiLabel, ajuste_multilabel, seuil_rappel, formule |
| `multinomial_simultane` | PALIER 2 — INTERVALLES DE CONFIANCE SIMULTANÉS POUR DES PARTS MULTINOMIALES (brique, 2026-06-26). | marginaux, simultanes_bonferroni, simultanes_quesenberry_hurst, intervalles, formule |
| `mutation_testing` | MUTATION TESTING — mesurer l'ADÉQUATION d'une suite de tests (code avancé, 2026-07-02). | analyse, suite_adequate |
| `mutations` | MUTATIONS — classification de mutations de l'ADN + effet d'une substitution sur la traduction. | type_mutation, effet_substitution_codon, decrit_substitution |
| `navigation` | NAVIGATION — orientation & positionnement sur le globe, FAUX=0 (mission formule/concept). | distance_orthodromique, haversine, cap_initial |
| `neurone_biologique` | neurone_biologique.py — Réseaux neuronaux biologiques (modèle intègre-et-tire). | potentiel_repos, depasse_seuil, frequence_decharge, frequence_max_refractaire, frequence_decharge_bornee |
| `no_free_lunch` | PALIER 2 — THÉORÈME NO FREE LUNCH (Wolpert-Macready) : | majorite_train, erreur_hors_echantillon, erreur_moyenne, erreur_sur_classe, analyse, formule |
| `nombres_complexes` | ANALYSE COMPLEXE — opérations sur les nombres complexes, FAUX=0 (mission formule/concept 2026-06-29). | module, argument, conjugue, somme, produit, quotient, puissance, racines_nieme |
| `nomenclature_chimique` | NOMENCLATURE CHIMIQUE BORNÉE — nommer des composés SIMPLES (règles IUPAC, faits établis). | prefixe, nom_element, nom_compose_binaire, formules_connues |
| `nouveaute` | PALIER 2 — DÉTECTION DE NOUVEAUTÉ / HORS-DISTRIBUTION (brique 11, 2026-06-25). | pvaleur_conforme, est_nouveau, scoreur_knn, formule |
| `nucleosynthese` | NUCLÉOSYNTHÈSE — énergie nucléaire bornée (équivalence masse↔énergie, défaut de masse, énergie de liaison). | energie_liaison, energie_liaison_par_nucleon, q_reaction, pic_fer |
| `ontologie` | ONTOLOGIE / SYSTÈME DE TYPES (subsomption sur les données) — promotion de la brique 🟡 (2026-07-02). | ancetres, est_un, plus_proche_commun, cycle |
| `opinions` | PALIER 2 — AGRÉGATION D'OPINIONS D'EXPERTS (brique 25, 2026-06-25). | pool_lineaire, pool_log, poids_fiabilite, combine, formule |
| `optimisation_bayesienne` | PALIER 2 — OPTIMISATION BAYÉSIENNE (surrogate par processus gaussien + acquisition) (brique, 2026-06-26). | acquisition_ucb, acquisition_ei, propose_prochain, optimise, formule |
| `oracle_definitions` | ORACLE DÉFINITIONS — la définition officielle = vérité, donc auto-construction du savoir (2026-06-18, insight Yohan : | genre_de, construit_isa, class Savoir |
| `orchestrateur_invention` | ORCHESTRATEUR MULTI-MODE D'INVENTION — le CAPSTONE de la couche COMMENT (2026-07-02). | class OrchestrateurInvention |
| `ordinaux` | ORDINAUX & CARDINAUX — arithmétique EXACTE, FAUX=0 (mission formule/concept). | fini, omega_puissance, addition_ordinale, multiplication_ordinale, compare_ordinaux, est_fini, est_limite, est_successeur |
| `p_box` | PALIER 2 — P-BOXES (boîtes de probabilité) : | class PBox, depuis_intervalles, cdf_precise, formule |
| `p_hacking` | PALIER 2 — P-HACKING / JARDIN DES CHEMINS BIFURQUANTS : | p_bilateral, cdf_p_min, prob_au_moins_un_significatif, p_ajuste_sidak, p_ajuste_bonferroni, analyse, formule |
| `pac_bayes` | PALIER 2 — BORNES PAC-BAYES : | kl_bernoulli, kl_inverse, kl_distributions, risque, borne, borne_mcallester, gibbs, formule |
| `paradoxes` | paradoxes.py — Paradoxes logiques (menteur, Russell, etc.). | est_autoreferentiel, ensemble_russell_paradoxal, barbier_paradoxal, menteur_paradoxal, grelling_paradoxal, est_heterologique, catalogue |
| `pareto` | OPTIMISATION MULTI-OBJECTIF / FRONT DE PARETO — brique Vague 5. | domine, front, domines |
| `parrondo` | PALIER 2 — PARADOXE DE PARRONDO : | joue, joue_motif, derive_motif, derive_moyenne, analyse, formule |
| `parseur_fichiers` | ROUTEUR DE FORMATS DE FICHIERS — « lire et comprendre tous les types de fichiers » (modalité, 2026-07-02). | detecte_type, lit, formats_supportes |
| `pascal_mugging` | PALIER 2 — PROBLÈME DE PASCAL (Pascal's mugging) / UTILITÉ NON BORNÉE : | paye_naif, paye_borne, proba_levier, paye_levier, analyse, formule |
| `pedologie` | pedologie.py — Pédologie (science des sols) : | classe_texture, porosite |
| `petits_nombres` | PALIER 2 — LOI DES PETITS NOMBRES & classement par taux brut : | taux_brut, moyenne_globale, kappa_optimal, retrecissement, analyse, formule |
| `petrochimie` | petrochimie.py — Raffinage du pétrole : | fraction_distillation, indice_octane_melange, coupes |
| `pharmacochimie` | pharmacochimie.py — Règle de cinq de Lipinski (druglikeness). | nombre_violations, respecte_lipinski, est_drug_like, indice_lipinski |
| `physique` | PHYSIQUE BORNÉE — grandeurs CALCULABLES par formule (mandat Yohan : | grandeurs, calcule |
| `pib` | PIB, CROISSANCE — identités de la comptabilité nationale (mécanisme EXACT, jamais une valeur-pays inventée). | pib_depenses, taux_croissance, pib_par_habitant, pib_reel |
| `planification` | PLANIFICATION MULTI-ÉTAPES — brique Vague 5. | class Operateur, plan, atteignable |
| `plastiques` | POLYMÈRES / PLASTIQUES — identification et propriétés (mandat Yohan : | code_recyclage, nom_depuis_code, classe_thermique, est_thermoplastique, est_thermodurcissable, temperature_transition_vitreuse, nom_complet |
| `poisson` | PALIER 2 — ESTIMATION DE TAUX POISSON (comptages, brique 36, 2026-06-25). | estime_taux, proba_compte, proba_au_moins, formule |
| `poisson_nonhomogene` | PALIER 2 — PROCESSUS DE POISSON NON-HOMOGÈNE (intensité variable λ(t), brique 44, 2026-06-26). | intensite_bins, comptage, intervalle_comptage, predit_fenetre, formule |
| `polyglotte` | GÉNÉRATION MULTI-LANGAGE (2026-06-17, choix Yohan « génération multi-langage ») — l'IA n'écrit plus seulement du Python  | class GenerateurPolyglotte, class ReponseLang, demande_lang |
| `polymeres` | POLYMÈRES BORNÉ — grandeurs CALCULABLES par formule exacte (mandat Yohan : | degre_polymerisation, masse_molaire_polymere, masse_molaire_monomere, indice_polymolecularite, degre_polymerisation_carothers, taux_conversion |
| `portefeuille_universel` | PALIER 2 — PORTEFEUILLE UNIVERSEL (Cover 1991) : | richesse_crp, richesse_actif_pur, richesse_universelle, meilleur_crp, poids_universels_suivants, regret_log, analyse, formule |
| `posologie` | posologie.py — Calculs de POSOLOGIE / DOSAGE (exacts, déterministes). | dose_totale, debit_perfusion, debit_gouttes, surface_corporelle_mosteller, dose_pediatrique, dose_pediatrique_bsa |
| `possibilite` | PALIER 2 — THÉORIE DES POSSIBILITÉS (Zadeh ; Dubois & Prade) : | normalisee, possibilite, necessite, intervalle_proba, domine, depuis_emboitees, encadre, formule |
| `predictif` | PALIER 2 — CALIBRATION D'UNE DISTRIBUTION PRÉDICTIVE (PIT + pinball, brique 26, 2026-06-25). | pit_echantillon, pit_cdf, histogramme_pit, variance_pit, est_calibre_pit, perte_pinball, quantile_pinball, formule |
| `prefiltre` | PRÉ-FILTRE EN-PROCESS DES CANDIDATS (2026-06-19, levier « tomber au plus petit possible » — Yohan). | pre_juge, faire_gagne_prefiltre |
| `preuve_domaines` |  | passe, noyau, main |
| `preuve_polyglotte` |  | class ExecuteurJS, main |
| `preuve_propositionnelle` | THÉORIE DE LA DÉMONSTRATION — vérification EXACTE de la validité d'inférences propositionnelles, FAUX=0. | inference_valide, regle_modus_ponens, regle_modus_tollens |
| `prevision` | PALIER 2 — PRÉVISION TEMPORELLE AVEC INTERVALLE DE PRÉDICTION (brique 30, 2026-06-25). | prevoit, formule |
| `prevision_walley` | PALIER 2 — PRÉVISIONS INFÉRIEURES / SUPÉRIEURES (Walley) : | lower, upper, intervalle, perte_sure, credal_depuis_croyance, encadre_gamble, formule |
| `prior_shift` | PALIER 2 — CORRECTION DE CHANGEMENT DE PRIOR / LABEL SHIFT (Saerens-Latinne-Decaestecker) (brique, 2026-06-26). | corrige_posterior, estime_prior_cible, adapte, formule |
| `procedes_fabrication` | PROCÉDÉS DE FABRICATION — classification CONVENTIONNELLE + rendement matière (mandat Yohan : | type_procede, rendement_matiere |
| `procedes_industriels` | Procedes industriels : | rendement, bilan_matiere, debit_production, taux_conversion |
| `processus_gaussien` | PALIER 2 — RÉGRESSION PAR PROCESSUS GAUSSIEN (GP, brique 45, 2026-06-26). | gp_fit, gp_predict, gp_intervalle, ajuste, formule |
| `profilage` | PROFILAGE & COMPLEXITÉ EMPIRIQUE — mesurer le coût réel d'un code (brique code avancé, 2026-07-02). | mesure_temps, mesure_memoire, classe_croissance |
| `propagande` | propagande.py — Catalogue ÉTABLI des techniques de propagande et taxonomie du désordre informationnel (faits sourcés, ab | technique, liste_techniques, type_desinformation, est_intentionnel, est_faux, liste_types_desinformation |
| `propagation` | PALIER 2 — PROPAGATION D'INCERTITUDE (brique 5, 2026-06-25). | propage_mc, propage_lineaire, intervalle_lineaire, formule |
| `property_based` | PROPERTY-BASED TESTING — falsification active d'un invariant (brique vérification/code avancé, 2026-07-02). | pour_tout |
| `proportion_binomiale` | PALIER 2 — INTERVALLE DE CONFIANCE D'UNE PROPORTION BINOMIALE (Wald vs Wilson vs Agresti-Coull) (brique, 2026-06-26). | wald, wilson, agresti_coull, intervalle, formule |
| `proprietes_materiaux` | PROPRIÉTÉS DES MATÉRIAUX (mesurables) — loi de Hooke & élasticité linéaire (mandat Yohan : | contrainte, deformation, module_young, hooke_contrainte, hooke_deformation, allongement |
| `proteines` | PROTÉINES, ENZYMES — structure et classification (faits SOURCÉS établis + calculs EXACTS). | niveau_structure, nombre_niveaux_structure, classe_enzyme_ec, nombre_liaisons_peptidiques |
| `pseudosciences` | PSEUDOSCIENCES — catalogue BORNÉ du STATUT scientifique de validité (consensus établi), pur stdlib (2026-07-02). | est_catalogue, validite_scientifique, base_consensus, a_validite_demontree, pratiques |
| `psychometrie` | psychometrie.py — Tests psychométriques (validité / fiabilité) : | qi_standardise, rang_percentile_qi, alpha_cronbach, erreur_standard_mesure |
| `qualitatif` | RAISONNEMENT QUALITATIF — brique Vague 4 (algèbre des signes + influences monotones). | signe_produit, signe_somme, class ReseauInfluences |
| `quantile_regression` | PALIER 2 — RÉGRESSION QUANTILE (perte pinball, multi-τ) sous HÉTÉROSCÉDASTICITÉ (brique 43, 2026-06-26). | pinball, quantile_fit, predit, bande_quantile, bande_homoscedastique, formule |
| `quantique` | MÉCANIQUE QUANTIQUE — relations fondamentales EXACTES, appelables directement, FAUX=0 (mission formule/concept 2026-06-2 | energie_photon, longueur_onde_broglie, niveaux_puits_infini, borne_heisenberg |
| `questions` | RÉPONDEUR IA — questions/réponses unifiées, model-free (2026-06-18, « voir ce que l'IA peut faire sans modèle »). | class RepondeurIA |
| `rademacher` | PALIER 2 — COMPLEXITÉ DE RADEMACHER & borne de généralisation UNIFORME (Bartlett-Mendelson ; Mohri) (brique 66, 2026-06- | rademacher_empirique, borne_massart, borne_generalisation, borne, formule |
| `raisonnement_defaut` | RAISONNEMENT PAR DÉFAUT — noyau BORNÉ de « cas général vs cas particulier / exception » (B-NEC), pur stdlib (2026-07-02) | class RegleDefaut |
| `rapport_invention` | RAPPORT D'INVENTION UNIFIÉ — la surface « produit » de l'objectif de Yohan : | rapport, texte |
| `raster_png` | RASTER PNG — noyau BORNÉ de la modalité IMAGE MATRICIELLE (pixels), pur stdlib (2026-07-02). | class Image, encode, ecris, decode |
| `rayonnement_thermique` | RAYONNEMENT THERMIQUE DU CORPS NOIR — primitives EXACTES, FAUX=0 (sujet : | longueur_onde_max, temperature_depuis_pic, frequence_max, loi_stefan_boltzmann, puissance_rayonnee |
| `recettes` | RECETTES (procédures) — mise à l'échelle et conversions culinaires (CONVENTIONS). | adapte_quantite, facteur_echelle, convertir_mesure, temps_cuisson_adapte |
| `recherche_dirigee` | RECHERCHE DIRIGÉE — dompter l'explosion combinatoire de l'invention ouverte (2026-06-18, cap auto-évolution). | class Banque, synthetise |
| `redox` | OXYDORÉDUCTION — nombre d'oxydation (n.o.) dans un composé NEUTRE + électrons échangés. | nombre_oxydation, equilibre_electronique |
| `refactor` | REFACTOR PRÉSERVANT LE COMPORTEMENT — adopter une variante plus propre SEULEMENT si elle calcule le même (2026-07-02). | adopte_refactor, meilleur_si_equivalent |
| `references` | RÉFÉRENCES DE CONVENTION BORNÉES (mandat Yohan 2026-06-23 : | vers_morse, depuis_morse, nato, couleur_resistance, frequence_note |
| `region_multivariee` | PALIER 2 — RÉGIONS DE PRÉDICTION MULTIVARIÉES CONFORMES (Mahalanobis, brique 42, 2026-06-26). | region_conforme, dans_region, boite_marginale, dans_boite, formule |
| `regle` | MOTEUR DE RÈGLES NORMATIVES — le domaine « règles posées par une autorité », entièrement BORNÉ (cf. | class Regle, class Referentiel, evalue_predicat, class Jugement, applique, apprend_predicat, prevaut, cherche_partout |
| `regles_induites` | PONT INDUCTION → DÉDUCTION — les règles VALIDÉES par induction_horn deviennent des clauses Datalog (2026-07-02). | clauses_datalog, class MoteurInduit |
| `regression_fallacieuse` | PALIER 2 — RÉGRESSION FALLACIEUSE (Granger-Newbold 1974) : | marche_aleatoire, bruit_blanc, t_et_r2, taux_faux_positif, analyse, formule |
| `regression_moyenne` | PALIER 2 — RÉGRESSION VERS LA MOYENNE (Galton) : | moyenne, correlation, selectionne, regression_vers_moyenne, analyse, formule |
| `regression_robuste` | PALIER 2 — RÉGRESSION ROBUSTE (M-estimateur de Huber) sous CONTAMINATION (brique 41, 2026-06-26). | ols, huber_fit, huber_slope_ic, ols_slope_ic, formule |
| `relations_lexique` | RELATIONS_LEXIQUE — exploite syn/ant du lexique converti (§6.2 d, 2026-06-18). | aretes_syn, paires_ant, raisonneurs |
| `relativite_generale` | RELATIVITÉ GÉNÉRALE — primitives EXACTES, directement appelables, FAUX=0 (mission formule/concept 2026-06-29). | rayon_schwarzschild, dilatation_gravitationnelle |
| `relativite_restreinte` | RELATIVITÉ RESTREINTE — cinématique et énergie d'Einstein, MÉCANISME EXACT (mandat Yohan : | facteur_lorentz, dilatation_temps, contraction_longueur, energie_totale, energie_repos, addition_vitesses |
| `relaxation` | RELAXATION DE CONTRAINTE / RÉSOLUTION DE CONTRADICTION — brique Vague 5 (esprit TRIZ). | relache_minimal, conflit |
| `reseaux_ip` | RÉSEAUX IP — calcul de sous-réseaux IPv4, FAUX=0 (mission formule/concept 2026-06-29). | ip_vers_entier, entier_vers_ip, masque_entier, masque, adresse_reseau, adresse_broadcast, nombre_hotes, meme_reseau |
| `reseaux_neurones` | RÉSEAUX DE NEURONES (mécanismes) — propagation avant EXACTE, FAUX=0 (mission formule/concept 2026-06-29). | echelon, signe, relu, sigmoide, tanh, potentiel, neurone, couche_dense |
| `resolution` | RÉSOLUTION FLOUE D'ENTITÉS (moteur — ADDITIF, ne modifie pas lecteur.py). | corrige, negation_fait_partie_entite, resout_superlatif, resout_comparaison, resout_fiche, resout_nl_generique, resout_liste, repond_floue |
| `resoudre_tout` | RÉSOLUTION CHAÎNÉE (2026-06-22, point 4 : | resoudre_tout |
| `restitution` | MOTEUR DE RESTITUTION — le pendant du moteur d'ANALYSE (examine_cible). | class MoteurRestitution |
| `restitution_fraiche` | RESTITUTION GATÉE PAR LA FRAÎCHEUR — ne jamais servir un fait périmé comme courant (acquisition temporelle, 2026-07-02). | sert_ou_hors, sert_le_plus_frais, a_rafraichir |
| `retraite` | retraite.py — Pension de retraite : | coefficient_proratisation, pension, taux_remplacement, decote |
| `revelation_bayesienne` | PALIER 2 — RÉVÉLATION BAYÉSIENNE & DÉPENDANCE AU PROTOCOLE (Monty Hall) : | posterior, prob_gain_changer, simule, brier_naif_vs_bayes, analyse, formule |
| `revision` | RÉVISION DE CROYANCES — brique Vague 8 (réconcilier, pas empiler). | class Croyance, class BaseCroyances |
| `rhetorique` | RHÉTORIQUE / PERSUASION (techniques) — CATALOGUE ÉTABLI (consensus, source : | mode_persuasion, modes, figure_style, figures, identifie_mode |
| `ridge` | PALIER 2 — RÉGRESSION RIDGE sous COLINÉARITÉ : | ajuste, predit, mse, analyse, formule |
| `risque_conforme` | PALIER 2 — CONTRÔLE DE RISQUE CONFORME (CRC, brique 12, 2026-06-25). | seuil_crc, controle_fnr, ensemble_au_seuil |
| `robotique` | ROBOTIQUE (cinématique) — modèle géométrique direct, FAUX=0 (mission formule/concept 2026-06-29). | cinematique_directe_2r, portee_max, portee_min, atteignable |
| `robust_bayes` | PALIER 2 — BAYES ROBUSTE par ε-CONTAMINATION (Berger) : | indicatrice, posterieur_contamine, posterieur_nominal, estime, formule |
| `roc_auc` | PALIER 2 — AUC (pouvoir DISCRIMINANT) AVEC INTERVALLE DE CONFIANCE (brique, 2026-06-26). | auc, se_hanley, se_naive, ic_hanley, ic_naif, evalue, bat_le_hasard, formule |
| `routeur` | ZONE-ROUTING — activation parcimonieuse « façon cerveau » (2026-06-17, vision Yohan). | cle_tache, class RouteurZone, resoudre_route, resoudre_route_rr, auto_configure, sauve_config, charge_config, resoudre_route_rr2 |
| `routeur_langage` | ROUTEUR DE LANGAGE — « l'IA trie les langages selon le besoin » (2026-07-02, vision Yohan, portfolio polyglotte). | backends_disponibles, choisit, executeur_pour |
| `saint_petersbourg` | PALIER 2 — PARADOXE DE SAINT-PÉTERSBOURG : | paiement, esperance_tronquee, equivalent_certain_log, valeur_casino_fini, moyenne_jeux, analyse, formule |
| `savoir_massif` | SAVOIR_MASSIF — branche le LEXIQUE MASSIF (1,9 M entrées du dump frwiktionary) comme ressource des briques SENS (§6.2 b, | class SavoirMassif, main |
| `schema_relations` | SCHÉMA DES RELATIONS (méta-modèle MESURÉ) — promotion de la brique 🟡 en objet de 1re classe (2026-07-02). | class ProfilRelation, profil, inverses_compatibles, relations_hierarchiques |
| `scores_propres` | PALIER 2 — RÈGLES DE SCORE PROPRES & CLASSEMENT DE FORECASTERS (brique 10, 2026-06-25). | log_loss, brier, score_spherique, crps, classe_forecasters |
| `scout_qlever` | SCOUT D'INGESTION QLever — automatise la DILIGENCE FAUX=0 sur un LOT de relations candidates « X -> pays » (mandat Yohan | val, decouvre, collision, sonde, sonde_generique, rapport_generique, rapport |
| `scrutin` | SCRUTIN — Vote / processus électoral (mécanique). | dhondt, sainte_lague, quotient_hare, majorite_absolue |
| `seismologie` | SÉISMOLOGIE — noyau BORNÉ des séismes (magnitude, énergie), lois établies, pur stdlib (2026-07-02). | magnitude_moment, moment_depuis_magnitude, energie_joules, magnitude_depuis_energie, rapport_amplitude, rapport_energie, classe |
| `selecteur` | SÉLECTEUR SITUATIONNEL GÉNÉRIQUE — la méta-architecture « façon cerveau » (2026-06-19, vision Yohan : | class Selecteur |
| `semiconducteurs` | SEMI-CONDUCTEURS — borné-physique CALCULABLE par formule (mandat FAUX=0, même posture que `physique.py`). | energie_gap_eV_vers_joule, longueur_onde_seuil, longueur_onde_seuil_nm, type_dopage, dopants_connus |
| `serie_autoregressive` | PALIER 2 — PRÉVISION AUTO-RÉGRESSIVE À h PAS, incertitude CROISSANTE avec l'horizon (brique 46, 2026-06-26). | ar1_fit, prevoit_h, prevoit, formule |
| `serie_multivariee` | PALIER 2 — PRÉVISION MULTIVARIÉE PAR VAR(1) + RÉGION CONJOINTE (brique, 2026-06-26). | var_fit, prevision, mahalanobis2, seuil_conforme, demi_largeurs_boite, ajuste, formule |
| `series_calcul` | SÉRIES & CONVERGENCE — sommes EXACTES et critères, FAUX=0 (mission formule/concept 2026-06-29). | somme_arithmetique, somme_geometrique, somme_geometrique_infinie, converge_geometrique, converge_riemann, somme_carres |
| `session` | Brique 9 — LA SESSION D'ENTRAÎNEMENT (l'orchestrateur complet). | class Etape, session |
| `shiryaev` | PALIER 2 — DÉTECTION AU PLUS TÔT (Shiryaev, quickest detection bayésienne) : | gaussienne, posteriors, detecte, seuil_pour_alpha, analyse, formule |
| `simpson` | PALIER 2 — PARADOXE DE SIMPSON : | taux, taux_strates, taux_agrege, gagnant_par_strate, gagnant_agrege, analyse, formule |
| `simulation` | SIMULATION / FORWARD-MODEL — brique Vague 3. | class ConflitDeRegles, class Simulateur |
| `smooth_ambiguity` | PALIER 2 — AMBIGUÏTÉ LISSE (smooth ambiguity, Klibanoff-Marinacci-Mukerji 2005) : | eu, phi_lineaire, phi_cara, prior_reduit, valeur, eu_reduit, equiv_certain_cara, choisir |
| `solveur_type` | SOLVEUR DIRIGÉ PAR LES TYPES (means-end) — « le comment » contre « le plus » (2026-06-19). | class Solveur, resoudre_demande, main |
| `sophismes` | sophismes.py — Identification de la FORME d'un argument conditionnel et catalogue de sophismes informels nommés (faits é | identifie_forme, est_valide, est_sophisme, definition_sophisme, liste_sophismes |
| `sources` | REGISTRE DES SOURCES FIABLES — l'IA connaît OÙ apprendre (donnée, pas code). | source, url, toutes, pour_domaine, pour_relation, domaines |
| `stabilite_algorithmique` | PALIER 2 — STABILITÉ ALGORITHMIQUE & généralisation (Bousquet-Elisseeff 2002) (brique 74, 2026-06-27). | knn, risque, stabilite_empirique, borne_generalisation, analyse, formule |
| `statique` | STATIQUE — équilibre des solides et des structures, FAUX=0 (mission formule/concept 2026-06-29). | moment, equilibre_moments, force_levier, centre_de_masse, reactions_appui |
| `stein` | PALIER 2 — PARADOXE DE STEIN (estimateur de James-Stein) : | james_stein, risque_mle, risque_js, risques_apparies, analyse, formule |
| `stereochimie` | stereochimie.py — Dénombrement de stéréoisomères et relation entre configurations. | nombre_stereoisomeres, paires_enantiomeres, nombre_enantiomeres, classe_relation |
| `stoechiometrie` | STŒCHIOMÉTRIE — équilibrage EXACT d'équations chimiques, FAUX=0 (mission formule/concept 2026-06-29). | equilibre, equation_equilibree |
| `store` | Brique 2 — LE STORE. | class Succes, class Store |
| `strategie_jeux` | STRATÉGIE OPTIMALE — jeux résolus à information parfaite (mandat : | gagnant, valeur_minimax, morpion_coup_optimal |
| `strategies` | STRATÉGIES DE TRAVERSÉE + ROUTAGE DE STRATÉGIE PAR CLÉ (2026-06-19, idée Yohan « occam là où il gagne, rr2 là où il perd | st_rr2, st_costw, st_rr_occam, st_costw_occam, st_smith, st_sunny, st_presolve, class RouteurStrategie |
| `structure_mapping` | STRUCTURE-MAPPING (analogie inter-domaines) — brique Vague 4. | trouve, couverture |
| `structures_genie` | STRUCTURES / GÉNIE CIVIL — résistance des matériaux EXACTE (poutres, sections), appel direct, FAUX=0. | contrainte_flexion, contrainte_traction, moment_quadratique_rectangle, moment_quadratique_cercle, module_resistance_rectangle, fleche_poutre_appuyee_charge_centree, flambement_euler |
| `substrat_physique` | SUBSTRAT-RÉEL — découverte d'inventions par TRANSDUCTION PHYSIQUE (vers l'objectif « inventions qui changent le monde », | class Concept, chaines, examine, lacunes_prioritaires |
| `substrat_reel` | SUBSTRAT-RÉEL — découverte d'inventions par TRANSDUCTION RELATIONNELLE sur les 71 M faits (OBJECTIF FINAL, 2026-07-02). | types_reels, transducteurs_reels, connus_reel, chaines_types, class ConceptReel, examine_reel, relations_pont, class Composite |
| `sujets` | TAXONOMIE DES SUJETS — parseur de `SUJETS_BORNE_OU_NON.md` en source de vérité machine-lisible. | class Sujet, charge, bornes, par_code |
| `surapprentissage` | PALIER 2 — SUR-APPRENTISSAGE (overfitting) : | genere, ajuste_poly, mse, degre_par_holdout, analyse, formule |
| `surdispersion` | PALIER 2 — SUR-DISPERSION DES COMPTAGES (Poisson vs binomiale négative, brique 48, 2026-06-26). | moyenne_variance, dispersion, test_surdispersion, intervalle_poisson, intervalle_negbin, formule |
| `survie` | PALIER 2 — ANALYSE DE SURVIE / TEMPS-JUSQU'À-ÉVÉNEMENT sous CENSURE (Kaplan-Meier, brique 39, 2026-06-26). | kaplan_meier, survie_a, mediane, km_avec_ic, km_naif_a, d_calibration, formule |
| `systemes_politiques` | SYSTÈMES POLITIQUES (définitions) — conventions politiques ÉTABLIES, fonctions pures déterministes, FAUX=0. | systemes, definition, classe_par_criteres, separation_pouvoirs, attribution_pouvoir |
| `tableur_xlsx` | TABLEUR XLSX — noyau BORNÉ de la modalité FEUILLE DE CALCUL (Excel/OOXML), pur stdlib (2026-07-02). | colonne_vers_lettre, lettre_vers_colonne, class Feuille, class Classeur, encode, ecris, decode |
| `taches` | Les TÂCHES — la matière première que l'on propose au modèle. | class Tache |
| `taux_de_base` | PALIER 2 — NÉGLIGENCE DU TAUX DE BASE / PARADOXE DU FAUX POSITIF : | vpp, vpn, estimation_naive, brier_naif_vs_bayes, analyse, formule |
| `taxonomie` | TAXONOMIE DE TYPES DÉRIVÉE DES DONNÉES (service — ADDITIF, lecture seule du lecteur). | ensembles, types_de, frac_ech, densite, source_lexicale_rel, population_compatible, hubs |
| `tbm` | PALIER 2 — TRANSFERABLE BELIEF MODEL (TBM, Smets) : | masse_vide, belief, plausibilite, conjonctive, ferme_le_monde, pignistique, betp_evenement, decide |
| `techniques_culinaires` | TECHNIQUES CULINAIRES — classification BORNÉE par mode de transfert thermique + températures de référence. | mode_cuisson, milieu_cuisson, decrit, techniques_du_mode, temperature_reference, plage_maillard, point_de_fumee, convient_friture |
| `telecom` | TÉLÉCOMMUNICATIONS — capacité de canal et grandeurs, FAUX=0 (mission formule/concept 2026-06-29). | capacite_shannon, debit_nyquist, gain_db, longueur_onde, snr_depuis_db |
| `teledetection` | teledetection.py — Télédétection (satellites, imagerie). | resolution_spatiale, ndvi, resolution_temporelle |
| `temperature` | PALIER 2 — TEMPERATURE SCALING (brique 19, 2026-06-25). | softmax_temp, logits_depuis_probas, class TemperatureScaling, ajuste_temperature, formule |
| `test_calibration` | PALIER 2 — TEST D'HYPOTHÈSE DE CALIBRATION (brique 27, 2026-06-25). | test_spiegelhalter, test_hosmer_lemeshow, est_calibre_test, formule |
| `test_permutation` | PALIER 2 — TEST DE PERMUTATION : | difference_moyennes, p_permutation, p_ttest_welch, teste, formule |
| `theorie_reseaux` | THÉORIE DES RÉSEAUX (appliquée) — métriques de graphes, FAUX=0 (mission formule/concept 2026-06-29). | degre, degre_moyen, densite, centralite_degre, distribution_degres, clustering_local |
| `topographie_arpentage` | TOPOGRAPHIE / ARPENTAGE — relations métriques exactes du terrain, FAUX=0. | pente_pourcent, distance_horizontale, denivele, aire_polygone_coords |
| `topologie` | TOPOLOGIE GÉNÉRALE — invariants EXACTS (entiers), directement appelables, FAUX=0 (mission formule/concept 2026-06-29). | caracteristique_euler, caracteristique_euler_betti, caracteristique_euler_somme_connexe, genre_depuis_euler, genre_non_orientable_depuis_euler, est_homeomorphe_sphere |
| `toxicologie` | toxicologie.py — Dose-réponse, index thérapeutique et classes de toxicité (DL50). | index_therapeutique, dose_totale, marge_securite, classe_toxicite_dl50 |
| `trace` | TRACE DE RAISONNEMENT VÉRIFIABLE — brique Vague 7. | class Cycle, class Trace |
| `transfert` | TRANSFERT INTER-DOMAINES — l'ASSEMBLEUR (machine-inventeur) : | transfere, manque |
| `transport_membranaire` | TRANSPORT MEMBRANAIRE — borné « Membranes, organites » (biologie cellulaire établie). | tonicite, sens_osmose, flux_fick |
| `triangulation` | TRIANGULATION — brique Vague 6 (accord de deux dérivations INDÉPENDANTES = corroboration non-circulaire). | triangule, confirme |
| `trigonometrie` | TRIGONOMÉTRIE — fonctions et résolution de triangles, FAUX=0 (mission formule/concept 2026-06-29). | deg_vers_rad, rad_vers_deg, sin_deg, cos_deg, tan_deg, loi_cosinus, angle_par_cotes, hypotenuse |
| `turing` | MACHINES DE TURING — simulation DÉTERMINISTE bornée, FAUX=0 (mission formule/concept 2026-06-29). | execute |
| `typage` | TYPAGE DE SORTIE DES CANDIDATS (2026-06-22, levier « élégance : | type_sortie, type_attendu, reordonne_par_type |
| `types_categories` | FONDATIONS ALTERNATIVES (théorie des catégories, types) — deux mécanismes EXACTS, déterministes, FAUX=0 (formule/concept | parse_type, var, app, lam, type_de, bien_type, morphisme, identite |
| `urgence_medicale` | urgence_medicale.py — Scores d'urgence cliniques établis. | score_glasgow, est_coma_grave, gravite_glasgow, score_apgar, interpretation_apgar, indice_choc, est_choc |
| `usinage` | USINAGE BORNÉ — paramètres de coupe (machining), formules EXACTES et établies. | vitesse_coupe, rotation_broche, taux_enlevement_matiere, temps_usinage, avance_par_minute |
| `usine_donnees` | USINE À DONNÉES (2026-06-17, « rendre l'IA prête à apprendre ») — accumuler un CORPUS de succès VÉRIFIÉS dans un store p | accumule |
| `utilite` | Brique « UTILITÉ ÉVOLUTIVE » — garder le plus utile, supplanter, re-juger. | class Utilite, evalue_utilite, class Selection |
| `valeurs_extremes` | PALIER 2 — VALEURS EXTRÊMES / RISQUE DE QUEUE (VaR, brique 33, 2026-06-25). | ajuste_gpd, var_pot, proba_depassement, var_pot_ic, formule |
| `variational_preferences` | PALIER 2 — PRÉFÉRENCES VARIATIONNELLES / MULTIPLIER (Hansen-Sargent ; Maccheroni-Marinacci-Rustichini) : | eu, kl, pire_distribution, valeur_robuste, valeur_directe, choisir, formule |
| `veille` | VEILLE / ACCÈS WEB — recherche SOUVERAINE, FAUX=0 (roadmap #11 : | recupere, rapporte, independantes, corrobore, approfondit |
| `veille_corroboration` | BOUCLE WEB -> RÉALITÉ -> FAIT-STORE : | juge_coherence_store, corrobore_valeur |
| `venn_abers` | PALIER 2 — PRÉDICTEUR DE VENN-ABERS (brique 16, 2026-06-25). | class VennAbers, formule |
| `verifie_demo` | VERAX — out-of-the-box verification / vérification prête à l'emploi. | main |
| `web` | WEB (HTML/CSS/standards) — vérifications STRUCTURELLES exactes, FAUX=0 (mission formule/concept 2026-06-29). | balises_equilibrees, specificite, compare_specificite |
| `will_rogers` | PALIER 2 — PHÉNOMÈNE DE WILL ROGERS / MIGRATION DE STADE : | moyenne, migrants_will_rogers, migration, analyse, formule |
| `winner_curse` | PALIER 2 — MALÉDICTION DU VAINQUEUR & INFÉRENCE SÉLECTIVE (brique 71, 2026-06-27). | selectionne, ic_naif, ic_simultane, estime, formule |

## Ingestion (sources réelles) — 147 modules

| Module | Rôle | API |
|---|---|---|
| `ingere_affixes` | INGESTION LANGUE — préfixe/suffixe -> sens -> datasets/lecteur/sens_prefixe.jsonl + sens_suffixe.jsonl (OFFLINE). | ingere |
| `ingere_alliages` | INGESTION MATÉRIAUX — alliage -> composition -> datasets/lecteur/composition_alliage.jsonl (OFFLINE). | ingere |
| `ingere_angles` | INGESTION GÉOMÉTRIE — type d'angle -> mesure -> datasets/lecteur/mesure_angle.jsonl (OFFLINE). | ingere |
| `ingere_animaux_dieux` | INGESTION MYTHOLOGIE — dieu grec -> animal/attribut sacré -> datasets/lecteur/animal_dieu.jsonl (OFFLINE). | ingere |
| `ingere_arts_martiaux` | INGESTION SPORT — art martial -> pays d'origine -> datasets/lecteur/pays_art_martial.jsonl (OFFLINE). | ingere |
| `ingere_astro_chimie2` | INGESTION ASTRO + CHIMIE — élément -> couleur de flamme, planète -> plus grande lune (OFFLINE). | ingere |
| `ingere_astronomie` | INGESTION ASTRONOMIE (8 planètes du système solaire) -> datasets/lecteur/*.jsonl (OFFLINE). | ingere |
| `ingere_atmospheres` | INGESTION ASTRONOMIE — corps -> présence d'une atmosphère significative (oui/non) (OFFLINE). | ingere |
| `ingere_aviation` | INGESTION AVIATION — modèles d'aéronef (Q15056993) -> datasets/lecteur/*.jsonl (ONLINE, lancé à la main). | ingere_tout |
| `ingere_banques` | INGESTION ÉCONOMIE — monnaie -> banque centrale émettrice -> datasets/lecteur/banque_centrale.jsonl (OFFLINE). | ingere |
| `ingere_batailles` | INGESTION HISTOIRE — bataille -> guerre/conflit -> datasets/lecteur/guerre_bataille.jsonl (OFFLINE). | ingere |
| `ingere_bd` | INGESTION BANDE DESSINÉE — série -> auteur/créateur -> datasets/lecteur/auteur_bd.jsonl (OFFLINE). | ingere |
| `ingere_beaufort` | INGESTION MÉTÉO — degré Beaufort -> appellation du vent -> datasets/lecteur/beaufort_description.jsonl (OFFLINE). | ingere |
| `ingere_biologie` | INGESTION BIOLOGIE — animal -> classe zoologique -> datasets/lecteur/classe_animal.jsonl (OFFLINE). | ingere |
| `ingere_bloc_element` | INGESTION CHIMIE — élément -> bloc du tableau périodique (s/p/d/f) -> datasets/lecteur/bloc_element.jsonl (OFFLINE). | ingere |
| `ingere_cardinaux` | INGESTION GÉO — point cardinal -> point cardinal opposé -> datasets/lecteur/oppose_cardinal.jsonl (OFFLINE). | ingere |
| `ingere_carences` | INGESTION SANTÉ — vitamine -> maladie de carence -> datasets/lecteur/carence_vitamine.jsonl (OFFLINE). | ingere |
| `ingere_cepages` | INGESTION ŒNOLOGIE — cépage -> couleur du vin/raisin (blanc/rouge) -> datasets/lecteur/couleur_cepage.jsonl (OFFLINE). | ingere |
| `ingere_chats` | INGESTION FÉLINOLOGIE — race de chat -> pays d'origine -> datasets/lecteur/pays_race_chat.jsonl (OFFLINE). | ingere |
| `ingere_chiens` | INGESTION CYNOLOGIE — race de chien -> pays d'origine -> datasets/lecteur/pays_race_chien.jsonl (OFFLINE). | ingere |
| `ingere_cinema` | INGESTION CINÉMA — film -> réalisateur -> datasets/lecteur/realisateur_film.jsonl (OFFLINE). | ingere |
| `ingere_composes` | INGESTION CHIMIE — composé -> formule brute (extension de `formule_chimique`) (OFFLINE). | ingere |
| `ingere_constantes_math` | INGESTION MATHÉMATIQUES — constante -> valeur numérique -> datasets/lecteur/valeur_constante.jsonl (OFFLINE). | ingere |
| `ingere_coordonnees` | INGESTION COORDONNÉES GÉOGRAPHIQUES (Wikidata/QLever P625) -> datasets/lecteur/*.jsonl (ONLINE, à la main). | ingere_capitales |
| `ingere_cordes` | INGESTION MUSIQUE — instrument à cordes -> nombre de cordes -> datasets/lecteur/nombre_cordes.jsonl (OFFLINE). | ingere |
| `ingere_corps_humain` | INGESTION CORPS HUMAIN — organe -> appareil/système -> datasets/lecteur/systeme_organe.jsonl (OFFLINE). | ingere |
| `ingere_cote_organe` | INGESTION ANATOMIE — organe -> côté du corps -> datasets/lecteur/cote_organe.jsonl (OFFLINE). | ingere |
| `ingere_couleurs` | INGESTION COULEURS — couleur -> code hexadécimal (sRGB) -> datasets/lecteur/code_hex_couleur.jsonl (OFFLINE). | ingere |
| `ingere_couleurs_complementaires` | INGESTION COULEURS — couleur -> couleur complémentaire -> datasets/lecteur/couleur_complementaire.jsonl (OFFLINE). | ingere |
| `ingere_couleurs_secondaires` | INGESTION COULEURS — couleur secondaire -> mélange (synthèse soustractive) (OFFLINE). | ingere |
| `ingere_creatures` | INGESTION MYTHOLOGIE — créature légendaire -> mythologie d'origine -> datasets/lecteur/origine_creature.jsonl (OFFLINE). | ingere |
| `ingere_cris_animaux` | INGESTION ZOOLOGIE/LANGUE — animal -> cri (nom du cri) -> datasets/lecteur/cri_animal.jsonl (OFFLINE). | ingere |
| `ingere_danses` | INGESTION CULTURE — danse -> pays d'origine -> datasets/lecteur/pays_danse.jsonl (OFFLINE). | ingere |
| `ingere_dents` | INGESTION CORPS HUMAIN — type de dent -> fonction -> datasets/lecteur/fonction_dent.jsonl (OFFLINE). | ingere |
| `ingere_deserts` | INGESTION GÉO — désert -> continent -> datasets/lecteur/continent_desert.jsonl (OFFLINE). | ingere |
| `ingere_devises_pays` | INGESTION CIVISME — pays -> devise nationale -> datasets/lecteur/devise_pays.jsonl (OFFLINE). | ingere |
| `ingere_dump` | INGERE_DUMP — ingestion du DUMP COMPLET frwiktionary en STREAMING (§6.2 a, échelle pure — 2026-06-18). | ingere_dump, main |
| `ingere_duree_match` | INGESTION SPORT — sport -> durée réglementaire d'un match -> datasets/lecteur/duree_match.jsonl (OFFLINE). | ingere |
| `ingere_duree_notes` | INGESTION MUSIQUE — figure de note -> durée (en temps, mesure 4/4) -> datasets/lecteur/duree_note.jsonl (OFFLINE). | ingere |
| `ingere_dynasties` | INGESTION HISTOIRE — dynastie -> pays principal -> datasets/lecteur/pays_dynastie.jsonl (OFFLINE). | ingere |
| `ingere_echecs` | INGESTION ÉCHECS — pièce -> déplacement + valeur -> datasets/lecteur/*.jsonl (OFFLINE). | ingere |
| `ingere_ecritures` | INGESTION LINGUISTIQUE — langue -> système d'écriture -> datasets/lecteur/ecriture_langue.jsonl (OFFLINE). | ingere |
| `ingere_elements_ptjson` | INGESTION PROPRIÉTÉS DES ÉLÉMENTS -> datasets/lecteur/*.jsonl (ONLINE, lancé à la main). | ingere |
| `ingere_emblemes_floraux` | INGESTION CULTURE — pays -> emblème floral national -> datasets/lecteur/embleme_floral.jsonl (OFFLINE). | ingere |
| `ingere_epices` | INGESTION GASTRONOMIE — épice -> pays/région d'origine -> datasets/lecteur/origine_epice.jsonl (OFFLINE). | ingere |
| `ingere_espace` | INGESTION ESPACE — sondes & véhicules spatiaux (Q26529) -> datasets/lecteur/*.jsonl (ONLINE, lancé à la main). | ingere_tout |
| `ingere_famille_chimique` | INGESTION CHIMIE — élément -> famille chimique (groupes nommés) (OFFLINE). | ingere |
| `ingere_fetes_nationales` | INGESTION FÊTES NATIONALES — pays -> date de la fête nationale (OFFLINE). | ingere |
| `ingere_fonction_organe` | INGESTION CORPS HUMAIN — organe -> fonction principale -> datasets/lecteur/fonction_organe.jsonl (OFFLINE). | ingere |
| `ingere_fondateurs_religions` | INGESTION RELIGIONS — religion -> fondateur -> datasets/lecteur/fondateur_religion.jsonl (OFFLINE). | ingere |
| `ingere_fromages` | INGESTION GASTRONOMIE — fromage -> pays d'origine -> datasets/lecteur/pays_fromage.jsonl (OFFLINE). | ingere |
| `ingere_fruits_arbres` | INGESTION BOTANIQUE — fruit -> arbre qui le produit -> datasets/lecteur/arbre_fruit.jsonl (OFFLINE). | ingere |
| `ingere_fuseaux` | INGESTION GÉO — heure locale d'une ville/région -> décalage UTC (heure standard, hors heure d'été) (OFFLINE). | ingere |
| `ingere_gammes` | INGESTION MUSIQUE — gamme -> nombre de notes -> datasets/lecteur/nombre_notes_gamme.jsonl (OFFLINE). | ingere |
| `ingere_genres_musicaux` | INGESTION MUSIQUE — genre musical -> pays/région d'origine -> datasets/lecteur/pays_genre_musical.jsonl (OFFLINE). | ingere |
| `ingere_geo` | INGESTION GÉOGRAPHIE -> datasets/lecteur/*.jsonl (ONLINE, lancé à la main). | ingere_geo |
| `ingere_geo_physique` | INGESTION GÉOGRAPHIE PHYSIQUE — fleuve/montagne -> continent -> datasets/lecteur/*.jsonl (OFFLINE). | ingere |
| `ingere_groupes_animaux` | INGESTION LANGUE/ZOO — animal -> nom du groupe (collectif) -> datasets/lecteur/nom_groupe_animal.jsonl (OFFLINE). | ingere |
| `ingere_histoire` | INGESTION HISTOIRE — événement -> année -> datasets/lecteur/annee.jsonl (OFFLINE). | ingere |
| `ingere_hormones` | INGESTION PHYSIOLOGIE — organe/glande -> hormone principale produite -> datasets/lecteur/hormone_organe.jsonl (OFFLINE). | ingere |
| `ingere_informatique` | INGESTION INFORMATIQUE — extension -> langage de programmation, et extension -> type de fichier (OFFLINE). | ingere |
| `ingere_instruments_mesure` | INGESTION MÉTROLOGIE — instrument -> grandeur mesurée -> datasets/lecteur/mesure_instrument.jsonl (OFFLINE). | ingere |
| `ingere_inventeurs` | INGESTION INVENTIONS — invention -> inventeur -> datasets/lecteur/inventeur.jsonl (OFFLINE). | ingere |
| `ingere_ions` | INGESTION CHIMIE — ion -> charge -> datasets/lecteur/charge_ion.jsonl (OFFLINE). | ingere |
| `ingere_jo` | INGESTION SPORT — année -> ville hôte des Jeux olympiques d'été -> datasets/lecteur/ville_jo_ete.jsonl (OFFLINE). | ingere |
| `ingere_jo_hiver` | INGESTION SPORT — année -> ville hôte des JO d'hiver -> datasets/lecteur/ville_jo_hiver.jsonl (OFFLINE). | ingere |
| `ingere_jours_saints` | INGESTION RELIGIONS — religion -> jour saint hebdomadaire -> datasets/lecteur/jour_saint_religion.jsonl (OFFLINE). | ingere |
| `ingere_kaikki` | INGERE_KAIKKI — CLI (réseau/fichier) : | telecharge, ingere, main |
| `ingere_langues_famille` | INGESTION LINGUISTIQUE — langue -> famille linguistique -> datasets/lecteur/famille_langue.jsonl (OFFLINE). | ingere |
| `ingere_lettres_grecques` | INGESTION GREC — lettre grecque (nom) -> symbole minuscule -> datasets/lecteur/symbole_grec.jsonl (OFFLINE). | ingere |
| `ingere_lexique` | INGESTION LEXIQUE FR -> datasets/lecteur/*.jsonl (OFFLINE — dump local déjà converti, ZÉRO réseau). | ingere_genre, ingere_definition, ingere_definition_verbe, ingere_definition_adjectif, ingere_definition_adverbe, ingere_pluriel |
| `ingere_lieux_saints` | INGESTION RELIGIONS — religion -> ville/lieu saint principal -> datasets/lecteur/lieu_saint_religion.jsonl (OFFLINE). | ingere |
| `ingere_litterature` | INGESTION LITTÉRATURE — œuvre -> auteur -> datasets/lecteur/auteur_oeuvre.jsonl (OFFLINE). | ingere |
| `ingere_locutions_latines` | INGESTION LATIN — locution latine -> sens en français -> datasets/lecteur/sens_locution_latine.jsonl (OFFLINE). | ingere |
| `ingere_maladies` | INGESTION SANTÉ — maladie -> type d'agent pathogène -> datasets/lecteur/agent_maladie.jsonl (OFFLINE). | ingere |
| `ingere_marques` | INGESTION ÉCONOMIE — marque -> pays d'origine (auto / tech / luxe) -> datasets/lecteur/*.jsonl (OFFLINE). | ingere |
| `ingere_mineraux` | INGESTION MINÉRAUX — espèces minérales (Q12089225) -> datasets/lecteur/*.jsonl (ONLINE, lancé à la main). | ingere_tout |
| `ingere_monuments` | INGESTION MONUMENTS — monument -> pays, et monument -> ville (OFFLINE). | ingere |
| `ingere_morse` | INGESTION COMMUNICATION — caractère -> code Morse international -> datasets/lecteur/code_morse.jsonl (OFFLINE). | ingere |
| `ingere_musique` | INGESTION MUSIQUE — instrument -> famille -> datasets/lecteur/famille_instrument.jsonl (OFFLINE). | ingere |
| `ingere_musique_classique` | INGESTION MUSIQUE CLASSIQUE — œuvre -> compositeur -> datasets/lecteur/compositeur_oeuvre.jsonl (OFFLINE). | ingere |
| `ingere_mythologie` | INGESTION MYTHOLOGIE GRECQUE — dieu -> domaine, et dieu grec -> équivalent romain (OFFLINE). | ingere |
| `ingere_mythologie2` | INGESTION MYTHOLOGIES — extension `domaine_dieu` (égyptiens + nordiques) + `pantheon_dieu` (OFFLINE). | ingere |
| `ingere_mythologie3` | INGESTION MYTHOLOGIE HINDOUE — ajoute les dieux hindous à `domaine_dieu` + `pantheon_dieu` (OFFLINE). | ingere |
| `ingere_nombre_organe` | INGESTION ANATOMIE — organe -> nombre dans le corps humain -> datasets/lecteur/nombre_organe.jsonl (OFFLINE). | ingere |
| `ingere_nombres_lettres` | INGESTION FRANÇAIS — nombre -> écriture en lettres -> datasets/lecteur/nombre_en_lettres.jsonl (OFFLINE). | ingere |
| `ingere_notes_musique` | INGESTION MUSIQUE — note (solfège latin) -> notation anglo-saxonne (OFFLINE). | ingere |
| `ingere_nuit_dates` | Ingestion NUIT 2026-06-29 : | ingere_date |
| `ingere_objet_etude` | INGESTION SCIENCES — discipline (« -logie/-graphie ») -> objet d'étude (OFFLINE). | ingere |
| `ingere_oceans` | INGESTION GÉO — océan -> rang par superficie -> datasets/lecteur/rang_ocean.jsonl (OFFLINE). | ingere |
| `ingere_optique` | INGESTION OPTIQUE — instrument d'optique -> usage -> datasets/lecteur/usage_instrument_optique.jsonl (OFFLINE). | ingere |
| `ingere_orbites` | INGESTION ASTRONOMIE — planète -> période de révolution + distance au Soleil (OFFLINE). | ingere |
| `ingere_ordres` | INGESTION ORDRES CONVENTIONNELS — signe chinois / ceinture judo / arc-en-ciel -> rang (OFFLINE). | ingere |
| `ingere_otan` | INGESTION COMMUNICATION — lettre -> mot de l'alphabet phonétique OTAN/OACI -> datasets/lecteur/alphabet_otan.jsonl (OFFL | ingere |
| `ingere_pays_renommes` | INGESTION GÉO/HISTOIRE — ancien nom de pays -> nom actuel -> datasets/lecteur/nom_actuel.jsonl (OFFLINE). | ingere |
| `ingere_peinture` | INGESTION PEINTURE — œuvre -> peintre -> datasets/lecteur/peintre_oeuvre.jsonl (OFFLINE). | ingere |
| `ingere_personnages` | INGESTION FICTION — personnage -> créateur (auteur) -> datasets/lecteur/createur_personnage.jsonl (OFFLINE). | ingere |
| `ingere_personnages_histoire` | INGESTION HISTOIRE — personnage historique -> fonction/rôle -> datasets/lecteur/fonction_personnage.jsonl (OFFLINE). | ingere |
| `ingere_petits_animaux` | INGESTION ZOOLOGIE/LANGUE — animal -> nom du petit -> datasets/lecteur/petit_animal.jsonl (OFFLINE). | ingere |
| `ingere_ph` | INGESTION CHIMIE — substance -> caractère acido-basique -> datasets/lecteur/ph_substance.jsonl (OFFLINE). | ingere |
| `ingere_phobies` | INGESTION PHOBIES — phobie -> objet de la peur -> datasets/lecteur/objet_phobie.jsonl (OFFLINE). | ingere |
| `ingere_pierres` | INGESTION GEMMOLOGIE — pierre précieuse -> couleur caractéristique -> datasets/lecteur/couleur_pierre.jsonl (OFFLINE). | ingere |
| `ingere_plats` | INGESTION GASTRONOMIE — plat -> pays d'origine -> datasets/lecteur/pays_plat.jsonl (OFFLINE). | ingere |
| `ingere_ponctuation` | INGESTION LANGUE — signe de ponctuation (nom) -> symbole -> datasets/lecteur/symbole_ponctuation.jsonl (OFFLINE). | ingere |
| `ingere_prix` | INGESTION DISTINCTIONS — prix/récompense -> domaine -> datasets/lecteur/domaine_prix.jsonl (OFFLINE). | ingere |
| `ingere_qlever` | INGESTION WIKIDATA via QLEVER -> datasets/lecteur/*.jsonl (ONLINE, lancé à la main). | qlever, val, domaine, ingere_sommets, ingere_capitales, ingere_hymnes, ingere_conduite, ingere_iso_num |
| `ingere_raccourcis` | INGESTION INFORMATIQUE — action -> raccourci clavier -> datasets/lecteur/raccourci_clavier.jsonl (OFFLINE). | ingere |
| `ingere_regime_alimentaire` | INGESTION BIOLOGIE — animal -> régime alimentaire -> datasets/lecteur/regime_alimentaire.jsonl (OFFLINE). | ingere |
| `ingere_region_os` | INGESTION CORPS HUMAIN — os -> région du corps -> datasets/lecteur/region_os.jsonl (OFFLINE). | ingere |
| `ingere_religions` | INGESTION RELIGIONS — religion -> texte sacré, et religion -> lieu de culte (OFFLINE). | ingere |
| `ingere_resistances` | INGESTION ÉLECTRONIQUE — couleur d'anneau de résistance -> chiffre (0-9) -> datasets/lecteur/valeur_couleur_resistance.j | ingere |
| `ingere_rest` | PONT D'INGESTION REST (NON-SPARQL) — datasets/lecteur/*.jsonl via l'API MediaWiki/Wikidata. | est_date_nue, cirrus_qids, qids_par_decoupe, collecte_date_rest, ingere_date_rest, republie_date_rest, collecte_entite_rest, ingere_entite_rest |
| `ingere_roches` | INGESTION GÉOLOGIE — roche -> type (magmatique/sédimentaire/métamorphique) (OFFLINE). | ingere |
| `ingere_saison_olympique` | INGESTION SPORT — sport -> saison olympique (été / hiver) -> datasets/lecteur/saison_olympique.jsonl (OFFLINE). | ingere |
| `ingere_salutations` | INGESTION LANGUES — langue -> « bonjour » et langue -> « merci » (OFFLINE). | ingere |
| `ingere_sciences` | INGESTION SCIENCES — découverte/théorie -> auteur -> datasets/lecteur/auteur_decouverte.jsonl (OFFLINE). | ingere |
| `ingere_sens_organe` | INGESTION CORPS HUMAIN — organe sensoriel -> sens -> datasets/lecteur/sens_organe.jsonl (OFFLINE). | ingere |
| `ingere_sigles` | INGESTION SIGLES — sigle/acronyme -> signification -> datasets/lecteur/signification_sigle.jsonl (OFFLINE). | ingere |
| `ingere_sport` | INGESTION SPORT — discipline -> nombre de joueurs par équipe (sur le terrain) (OFFLINE). | ingere |
| `ingere_subdivisions_monnaie` | INGESTION ÉCONOMIE — monnaie -> subdivision (centième) -> datasets/lecteur/subdivision_monnaie.jsonl (OFFLINE). | ingere |
| `ingere_surnoms_rois` | INGESTION HISTOIRE — souverain -> surnom -> datasets/lecteur/surnom_roi.jsonl (OFFLINE). | ingere |
| `ingere_symbole_astro` | INGESTION ASTRONOMIE — planète -> symbole astronomique (OFFLINE). | ingere |
| `ingere_symbole_monnaie` | INGESTION ÉCONOMIE — monnaie -> symbole monétaire -> datasets/lecteur/symbole_monnaie.jsonl (OFFLINE). | ingere |
| `ingere_symboles_math` | INGESTION MATHÉMATIQUES — opération/concept -> symbole -> datasets/lecteur/symbole_math.jsonl (OFFLINE). | ingere |
| `ingere_t10` | INGESTION T10 — SPORT & COMPÉTITIONS (ONLINE, lancé à la main). | ingere_sport_competition, ingere_pays_equipe_nationale, ingere_vainqueur_competition, ingere_ligue_club, ingere_stade_club, ingere_pays_competition, ingere_sport_equipe, ingere_organisateur_competition |
| `ingere_t11` | INGESTION T11 — TRANSPORT, VÉHICULES & INFRASTRUCTURE -> datasets/lecteur/*.jsonl (ONLINE QLever, offline ensuite). | ingere_codes, ingere_tout, sonde |
| `ingere_t12` | INGESTION T12 — RELIGION, MYTHOLOGIE & PHILOSOPHIE (ONLINE, lancé à la main). | ingere_pere_divinite, ingere_mere_divinite, ingere_fondateur_ordre_religieux, ingere_religion_ordre_religieux, ingere_dedicace_edifice_religieux, ingere_pere_personnage_mythique, ingere_mere_personnage_mythique, ingere_conjoint_personnage_mythique |
| `ingere_t4` | INGESTION T4 — COULOIR « VIVANT » (biologie : | domaine, ingere_organisme_gene, ingere_chromosome_gene, ingere_specialite_medicale_maladie, ingere_agent_pathogene_maladie, ingere_vecteur_maladie, ingere_glande_hormone, ingere_regime_alimentaire |
| `ingere_t5` | INGESTION T5 — ŒUVRES CULTURELLES, côté CRÉATEURS / PRODUCTION (Wikidata via QLever). | main |
| `ingere_t5_canon` | INGESTION T5 — CANON ŒUVRES (compositeur d'opéra / de comédie musicale) DEPUIS LA CONNAISSANCE DU MODÈLE. | main |
| `ingere_t6` | INGESTION T6 — PERSONNES (attributs NON-lieu) & ORGANISATIONS (ONLINE, lancé à la main). | ingere_sexe_personne, ingere_langue_maternelle, ingere_secteur_entreprise, ingere_occupation_personne, ingere_poste_occupe, ingere_domaine_travail, ingere_cause_deces, ingere_bourse_cotation |
| `ingere_t7` | INGESTION T7 — MESURES NUMÉRIQUES & TECHNIQUE -> datasets/lecteur/*.jsonl (ONLINE via QLever, offline ensuite). | ingere_numerique, ingere_tout, sonde, ingere_une |
| `ingere_t8` | INGESTION T8 — HISTOIRE, DATES & POLITIQUE -> datasets/lecteur/*.jsonl (ONLINE via QLever, offline ensuite). | ingere_date, ingere_regne, ingere_succession, ingere_batailles, ingere_traites, ingere_sieges, ingere_operations, ingere_etat_vers_etat |
| `ingere_t9` | INGESTION T9 — COULOIR « LANGUE, LEXIQUE & ÉCRITURE » (catégorie `convention`). | ingere_systeme_ecriture, ingere_code_iso6393, ingere_code_iso6392, ingere_code_glottolog, ingere_code_ethnologue, ingere_statut_vitalite, ingere_code_ietf, ingere_code_linguasphere |
| `ingere_t9_autosource` | AUTO-SOURCING T9 — TYPOLOGIE DES SYSTÈMES D'ÉCRITURE -> datasets/lecteur/type_systeme_ecriture.jsonl (OFFLINE). | ingere, ingere_ordre, ingere_morpho, ingere_ton, ingere_align, ingere_genre, ingere_article, ingere_classif |
| `ingere_t9_lexemes` | INGESTION T9 — LEXÈMES Wikidata -> datasets/lecteur/{categorie_lexicale_mot,genre_grammatical_mot}.jsonl (ONLINE). | ingere_categorie, ingere_genre, ingere_concept, ingere_etymon |
| `ingere_type_astre` | INGESTION ASTRONOMIE — astre -> type -> datasets/lecteur/type_astre.jsonl (OFFLINE). | ingere |
| `ingere_types_arbres` | INGESTION BOTANIQUE — arbre -> type (feuillu / conifère) -> datasets/lecteur/type_arbre.jsonl (OFFLINE). | ingere |
| `ingere_unites_imperiales` | INGESTION MÉTROLOGIE — unité impériale/anglo-saxonne -> équivalent métrique -> datasets/lecteur/equivalent_metrique.json | ingere |
| `ingere_vents` | INGESTION MÉTÉO — vent régional -> région/origine -> datasets/lecteur/origine_vent.jsonl (OFFLINE). | ingere |
| `ingere_vetements` | INGESTION VÊTEMENTS — vêtement/accessoire -> partie du corps -> datasets/lecteur/partie_corps_vetement.jsonl (OFFLINE). | ingere |
| `ingere_villes` | INGESTION GÉO — grande ville (NON capitale) -> pays -> datasets/lecteur/pays_ville.jsonl (OFFLINE). | ingere |
| `ingere_villes_coordonnees` | INGESTION COORDONNÉES DES LOCALITÉS (Wikidata/QLever P625, CYCLE 2) -> latitude_localite / longitude_localite. | ingere_localites |
| `ingere_vitamines` | INGESTION SANTÉ — vitamine -> nom chimique -> datasets/lecteur/nom_vitamine.jsonl (OFFLINE). | ingere |
| `ingere_wikidata` | INGESTION WIKIDATA -> datasets/lecteur/*.jsonl (ONLINE — lancé À LA MAIN, jamais à l'import du lecteur). | sparql, val, fonctionnel, reconcilie, ecrit_jsonl, ecrit_conflits, publie, snapshot_brut |
| `ingere_worldbank` | INGESTION BANQUE MONDIALE -> datasets/lecteur/*.jsonl (ONLINE, lancé à la main). | ingere_population, ingere_indicateur, ingere_economie |
| `ingere_zodiaque` | INGESTION ZODIAQUE — signe astrologique -> élément -> datasets/lecteur/element_zodiaque.jsonl (OFFLINE). | ingere |

## Validateurs (gate FAUX=0) — 681 modules

| Validateur | Ce qu'il prouve |
|---|---|
| `valide_abduction` | VALIDATION abduction.py (Vague 5). |
| `valide_abstention` | VALIDATION abstention.py (Vague 7). |
| `valide_accord_correct` | DÉTECTION D'ERREUR D'ACCORD (brique COMPRÉHENSION) — savoir quand le français est faux. |
| `valide_accord_phrase` | ACCORD DANS LE GROUPE NOMINAL (brique COMPRÉHENSION — phrase) — propage le pluriel sur tout le groupe. |
| `valide_adjacence` | ADJACENCE — agréger une relation entre éléments VOISINS (thème II : |
| `valide_adverbe` | ADVERBE EN -MENT (brique FORME DÉRIVATION) — dériver un adverbe depuis un adjectif est RÉGLÉ donc VÉRIFIABLE. |
| `valide_aerodynamique` | VALIDE aerodynamique.py — held-out ADVERSE. |
| `valide_agregation_previsions` | VALIDATION de l'AGRÉGATION DE PRÉVISIONS (agregation_previsions.py) — jugée par calibration.py. |
| `valide_algebre_boole` | VALIDE algebre_boole.py — ADVERSE, FAUX=0. |
| `valide_algebre_calcul` | VALIDE algebre_calcul.py — held-out ADVERSE, FAUX=0. |
| `valide_algo_analyse` | VALIDE algo_analyse.py — held-out ADVERSE, FAUX=0. |
| `valide_allais` | VALIDATION du PARADOXE D'ALLAIS (allais.py). |
| `valide_allen` | VALIDATION de allen.py — les 13 relations d'intervalles d'Allen. |
| `valide_alliages` | VALIDE alliages.py — held-out ADVERSE. |
| `valide_analogie` | ANALOGIE / TRANSFERT (brique COMPRÉHENSION) — un motif appris se réutilise/adapte à travers les DOMAINES. |
| `valide_analyse_chimique` | VALIDE analyse_chimique.py — held-out ADVERSE. |
| `valide_analyse_fonctionnelle` | VALIDE analyse_fonctionnelle.py — held-out ADVERSE. |
| `valide_analyse_phrase` | ANALYSE DE PHRASE (brique COMPRÉHENSION — phrase) — décomposer la phrase en classes grammaticales. |
| `valide_ancetre_commun` | ANCÊTRE COMMUN / LIEN (brique COMPRÉHENSION) — ce que deux mots ont en commun, sur le graphe de sens. |
| `valide_ancrage` | VALIDATION de l'EFFET D'ANCRAGE (ancrage.py). |
| `valide_ancres` | VALIDATION ancres.py (Vague 6). |
| `valide_anscombe` | VALIDATION du QUARTET D'ANSCOMBE (anscombe.py). |
| `valide_anticipation` | ANTICIPATION — prédire le TERME SUIVANT d'une séquence (2026-06-17, insight Yohan « l'anticipation est une bri |
| `valide_antonyme` | ANTONYMES (brique COMPRÉHENSION — axe du sens : |
| `valide_arbitre` | VALIDATION arbitre.py (Vague 7). |
| `valide_architecture` | VALIDE architecture.py — ADVERSE, FAUX=0. |
| `valide_arithmetique_intervalles` | VALIDATION de l'ARITHMÉTIQUE D'INTERVALLES (arithmetique_intervalles.py) — jugée par calibration.py. |
| `valide_arithmetique_modulaire` | VALIDE arithmetique_modulaire.py — held-out ADVERSE, FAUX=0. |
| `valide_arret` | VALIDE arret.py — ADVERSE, FAUX=0. |
| `valide_assistant` | ASSISTANT IA À MÉMOIRE PERSISTANTE (2026-06-17) — l'IA s'améliore À L'USAGE : |
| `valide_assistant_nl` | VALIDE assistant_nl — la porte conversationnelle AUTONOME (bornage -> répond/calcule/cherche/DEMANDE) — ADVERS |
| `valide_asteroides` | VALIDE asteroides.py — held-out ADVERSE. |
| `valide_astronautique` | VALIDE astronautique.py — held-out ADVERSE. |
| `valide_atome` | VALIDE atome.py — contrat FAUX=0 : |
| `valide_audio_wav` | VALIDE audio_wav.py — round-trip PCM exact (oracle stdlib `wave`) + FAUX=0 (plage, formats, flux invalide). |
| `valide_audiologie` | VALIDE audiologie.py — held-out ADVERSE. |
| `valide_audit_ancres` | VALIDE le MÉCANISME d'audit des ancres (audit_ancres.py) — FAUX=0 sur le diagnostic lui-même. |
| `valide_audit_code` | VALIDE audit_code.py — held-out ADVERSE, axé SOUNDNESS (jamais un faux positif). |
| `valide_aumann` | VALIDATION du THÉORÈME D'ACCORD D'AUMANN (aumann.py). |
| `valide_auto_apprend` | VALIDE — AUTO-APPRENTISSAGE AUTONOME (2026-06-22). |
| `valide_auto_invention` | MOTEUR D'AUTO-INVENTION — l'IA étend SEULE son répertoire, jugée par la réalité (cf. |
| `valide_auto_invention_ouverte` | MOTEUR D'AUTO-INVENTION OUVERTE — composition universelle, multi-domaines, jugé par la réalité (cap auto-évolu |
| `valide_auto_optimise` | VALIDATION de l'AUTO-OPTIMISATION RÉCURSIVE (auto_optimise.py). |
| `valide_auto_synthese` | AUTO-SYNTHÈSE PAR SQUELETTES (2026-06-24) — l'IA CONSTRUIT ses propres briques à partir de squelettes génériqu |
| `valide_automates` | VALIDE automates.py — ADVERSE, FAUX=0. |
| `valide_automobile` | VALIDE automobile.py — held-out ADVERSE. |
| `valide_bandit` | VALIDATION des BANDITS (bandit.py). |
| `valide_bandit_contextuel` | VALIDATION du BANDIT CONTEXTUEL (bandit_contextuel.py). |
| `valide_base_faits` | VALIDATION de la BASE DE FAITS VÉRIFIÉS (`base_faits.py`) — juge load-bearing des catégories 2/3/4. |
| `valide_bases_donnees` | VALIDE bases_donnees.py — ADVERSE, FAUX=0. |
| `valide_batteries` | VALIDE batteries.py — held-out ADVERSE. |
| `valide_bayes` | VALIDATION de la COMBINAISON BAYÉSIENNE (bayes.py) — la postérieure est-elle CALIBRÉE ? Preuve Monte-Carlo, JU |
| `valide_bayes_correle` | VALIDATION de l'AGRÉGATION BAYÉSIENNE CORRÉLÉE (bayes.posterior_correle) — corrige le caveat de la brique 2. |
| `valide_bayes_sequentiel` | VALIDATION du BAYÉSIEN SÉQUENTIEL (bayes_sequentiel.py) — jugé par calibration.py. |
| `valide_benford` | VALIDATION de la LOI DE BENFORD (benford.py). |
| `valide_berkson` | VALIDATION du PARADOXE DE BERKSON (berkson.py). |
| `valide_bertrand` | VALIDATION du PARADOXE DE BERTRAND (bertrand.py). |
| `valide_besoin` | VALIDE besoin.py — couche objectif/besoin du moteur d'invention. |
| `valide_biais_longueur` | VALIDATION du BIAIS DE LONGUEUR (biais_longueur.py). |
| `valide_biais_publication` | VALIDATION du BIAIS DE PUBLICATION (biais_publication.py). |
| `valide_biais_survie` | VALIDATION du BIAIS DE SURVIE (biais_survie.py). |
| `valide_bibliotheconomie` | VALIDE bibliotheconomie.py — held-out ADVERSE. |
| `valide_bibliotheque_invention` | VALIDATION du CAPSTONE RÉCURSIF — phase sommeil (bibliotheque_invention.py). |
| `valide_bifurcations` | VALIDE bifurcations.py — held-out ADVERSE. |
| `valide_big_bang` | VALIDE big_bang.py — held-out ADVERSE. |
| `valide_big_data` | VALIDE big_data.py — ADVERSE, FAUX=0. |
| `valide_bioinfo` | VALIDE bioinfo.py — held-out ADVERSE, FAUX=0. |
| `valide_bioingenierie` | VALIDE bioingenierie.py — held-out ADVERSE. |
| `valide_biomecanique` | VALIDE biomecanique.py — held-out ADVERSE. |
| `valide_biostatistique` | VALIDE biostatistique.py — held-out ADVERSE. |
| `valide_bits` | DOMAINE BINAIRE / BITS — opérations bit-à-bit (2026-06-17, élargir les domaines vérifiables). |
| `valide_blackboard` | VALIDATION blackboard.py (Vague 7). |
| `valide_blockchain` | VALIDE blockchain.py — ADVERSE, FAUX=0. |
| `valide_bma` | VALIDATION du MOYENNAGE BAYÉSIEN DE MODÈLES (bma.py) — jugé par calibration.py. |
| `valide_bootstrap` | VALIDATION de l'IC BOOTSTRAP (bootstrap.py) — jugé par calibration.py. |
| `valide_bootstrap_savoir` | BOOTSTRAP_SAVOIR — l'IA construit SEULE une taxonomie multi-niveaux en remontant les définitions. |
| `valide_borel_kolmogorov` | VALIDATION du PARADOXE DE BOREL-KOLMOGOROV (borel_kolmogorov.py). |
| `valide_boucle` | Validation de la BRIQUE 4 (la boucle d'orchestration). |
| `valide_boucle_bornee` | BOUCLE BORNÉE — l'arrêt anticipé, en un schéma figé (la part de contrôle qui restait différée). |
| `valide_boucle_invention` | VALIDE le capstone boucle_invention (besoin->assemblage->gap->corroboration->writeback) — ADVERSE, FAUX=0. |
| `valide_braess` | VALIDATION du PARADOXE DE BRAESS (braess.py). |
| `valide_braille` | VALIDE braille.py — bijection + round-trip + FAUX=0 (domaine explicite, abstention hors table). |
| `valide_branche` | BRANCHEMENT — lever le dernier mur du plafond (le CONTRÔLE), en périmètre étroit. |
| `valide_budget` | BUDGET DE PUISSANCE — le 2e cran (2026-06-17, vision Yohan « dépenser la puissance à hauteur du besoin », par- |
| `valide_budget_personnel` | VALIDE budget_personnel.py — held-out ADVERSE. |
| `valide_cadrage` | VALIDATION de l'EFFET DE CADRAGE (cadrage.py). |
| `valide_calcul_infinitesimal` | VALIDE calcul_infinitesimal.py — ADVERSE, FAUX=0. |
| `valide_calculabilite` | VALIDE calculabilite.py — held-out ADVERSE, FAUX=0. |
| `valide_calendrier_bits_geo` | BRIQUE CALENDRIER + EXTENSIONS BITS & GÉOMÉTRIE (2026-06-19) — lacunes MESURÉES par gap_probe 3ᵉ vague : |
| `valide_calibrateurs` | VALIDATION des CALIBRATEURS PARAMÉTRIQUES (calibrateurs.py) — jugés par calibration.py. |
| `valide_calibration` | VALIDATION de l'INSTRUMENT DE CALIBRATION (calibration.py) — le juge du Palier 2 se juge LUI-MÊME par MONTE-CA |
| `valide_calibration_ranking` | VALIDATION de la CALIBRATION DU CLASSEMENT (calibration_ranking.py) — jugée par calibration.py. |
| `valide_calibration_sequence` | VALIDATION de la CALIBRATION DE SÉQUENCE (calibration_sequence.py) — jugée par calibration.py. |
| `valide_capacites` | VALIDE capacites.py — manifeste de capacités formule/concept. |
| `valide_cardinalite` | VALIDE cardinalite.py — held-out ADVERSE. |
| `valide_cardiologie` | VALIDE cardiologie.py — held-out ADVERSE. |
| `valide_carte` | APPROFONDIR LA CARTE — quels murs sont MOUS (se ferment par seeding), lequel est le VRAI. |
| `valide_carte_limites` | CARTE_LIMITES_FRANCAIS — la frontière du model-free est mesurée, pas affirmée. |
| `valide_cartographie` | VALIDE cartographie.py — held-out ADVERSE. |
| `valide_cas_limites` | VALIDATION cas_limites.py (Vague 6). |
| `valide_causal` | VALIDATION de l'INFÉRENCE CAUSALE (causal.py) — jugée par calibration.py. |
| `valide_causalite` | VALIDATION de la CAUSALITÉ (causalite.py) — Vague 1. |
| `valide_ceramiques` | VALIDE ceramiques.py — held-out ADVERSE (FAUX=0). |
| `valide_cesar` | CHIFFRE DE CÉSAR (brique puissante) — décalage mod 26 (ord/chr). |
| `valide_chaines_avancees` | CHAÎNES AVANCÉES — anagramme/sous-chaîne/remplace. |
| `valide_changepoint` | VALIDATION de la DÉTECTION DE CHANGEMENT (changepoint.py). |
| `valide_chaos` | VALIDE chaos.py — held-out ADVERSE. |
| `valide_charge_lexique` | CHARGE_LEXIQUE — ingesteur de lexique scalable (voie Wiktionnaire) — la cohérence est vérifiée, pas supposée. |
| `valide_chemin` | CHEMIN / EXPLICATION (brique COMPRÉHENSION) — la chaîne qui relie x à y (le « parce que »). |
| `valide_chemin2d` | VALIDATION de chemin2d.py — chemins (lignes + Bézier cubiques), export SVG <path>. |
| `valide_chercheur_invention` | VALIDATION du CHERCHEUR D'INVENTIONS AUTONOME (chercheur_invention.py). |
| `valide_chevauchement` | BRIQUE CHEVAUCHEMENT / BALAYAGE D'INTERVALLES (sweep-line) (2026-06-19) — événements ±1 aux bornes, tri, max c |
| `valide_chiffres` | DÉCOMPOSITION DÉCIMALE — somme/nb/inverse des chiffres. |
| `valide_chimie` | VALIDE chimie.py — held-out ADVERSE. |
| `valide_chimie_quantitative` | VALIDE chimie_quantitative.py — ADVERSE, FAUX=0. |
| `valide_choix_social` | VALIDATION du CHOIX SOCIAL (choix_social.py). |
| `valide_chomage` | VALIDE chomage.py — held-out ADVERSE. |
| `valide_choquet` | VALIDATION de l'INTÉGRALE DE CHOQUET (choquet.py) — jugée par calibration.py. |
| `valide_chronobiologie` | VALIDE chronobiologie.py — held-out ADVERSE. |
| `valide_citoyennete` | VALIDE citoyennete.py — ADVERSARIAL. |
| `valide_classes_complexite` | VALIDE classes_complexite.py — held-out ADVERSE, FAUX=0. |
| `valide_classif` | VALIDATION de la CLASSIFICATION CALIBRÉE (classif_calibree.py) — la réparation de calibration est-elle RÉELLE  |
| `valide_classif_multiclasse` | VALIDATION de la CLASSIFICATION CALIBRÉE MULTI-CLASSE (classif_multiclasse.py) — jugée par calibration.py. |
| `valide_classification_surfaces` | VALIDE classification_surfaces.py — held-out ADVERSE, FAUX=0. |
| `valide_classifieur` | VALIDATION du CLASSIFIEUR DE NATURE DE DOMAINE. |
| `valide_classifieur_bornage` | VALIDE classifieur_bornage.py — le routeur de statut : |
| `valide_cloture` | CLÔTURE — un mécanisme compose sur un atome INVENTÉ (invention -> registre -> composition). |
| `valide_cloud_distribue` | VALIDE cloud_distribue.py — ADVERSE, FAUX=0. |
| `valide_coherence_physique` | VALIDE coherence_physique.py — held-out ADVERSE. |
| `valide_combinatoire` | COMBINATOIRE GÉNÉRATIVE — permutations/sous-ensembles/produit. |
| `valide_commerce_international` | VALIDE commerce_international.py — held-out ADVERSE. |
| `valide_commun` | HELPERS COMMUNS DES VALIDATEURS — pensée machine : |
| `valide_comparatif` | COMPARATIF (PRODUCTION + COGNITION) — exprimer une comparaison a/b via un adjectif accordé, RÉGLÉ donc VÉRIFIA |
| `valide_completude` | AUDIT DE COMPLÉTUDE (2026-06-17) — hors INTERFACE et hors GPU, ne manque-t-il RIEN sur absolument tous les pla |
| `valide_complexite` | VALIDE complexite.py — held-out ADVERSE, FAUX=0. |
| `valide_compose` | FUSION VERTICALE — 2e étage : |
| `valide_compose_profond` | INDUSTRIALISER LA PROFONDEUR — la composition nidifie au-delà de la profondeur 2 (tours de skills plus hautes) |
| `valide_composites` | VALIDE composites.py — held-out ADVERSE. |
| `valide_compounding` | LA MONTÉE AUTONOME (compounding) — le test le plus informatif du projet. |
| `valide_compounding_arite` | COMPOUNDING de l'ARITÉ 2 — un composé d'arité-2 nourrit le présent (cap 2, suite). |
| `valide_compounding_stress` | STRESS du compounding — POUSSER jusqu'au plafond, et LOCALISER la cause (cap 1 avant cap 2). |
| `valide_comprehension` | Validation de la COMPRÉHENSION (1/2) — abstraire par compression. |
| `valide_comprehension_definition` | COMPRÉHENSION DE DÉFINITION (brique COMPRÉHENSION) — décomposer une définition en genre + différence. |
| `valide_comprehension_generale` | COMPRÉHENSION GÉNÉRALE — transform + filtre(agrégat) + reduce en UNE passe (le front « réel » restant). |
| `valide_comprehension_integree` | COMPRÉHENSION INTÉGRÉE — le moteur ASSEMBLÉ comprend une phrase de bout en bout (vérifier l'intégré, pas l'iso |
| `valide_comprehension_phrase` | COMPRÉHENSION DE PHRASE (brique COMPRÉHENSION — sens + logique) — qui fait quoi (rôles SVO autour du verbe). |
| `valide_comptabilite` | VALIDE comptabilite.py — held-out ADVERSE. |
| `valide_comptage` | COMPTAGE (brique COMPRÉHENSION — quantitatif) — combien / lesquels d'un ensemble sont d'une catégorie. |
| `valide_comptage_combinatoire` | BRIQUE COMPTAGE COMBINATOIRE (2026-06-19) — GenerateurComptageCombinatoire : |
| `valide_comptage_membre` | COMPTAGE PAR APPARTENANCE — `sum(c in LIT for c in s)` (famille D : |
| `valide_concentration` | VALIDATION des BORNES DE CONCENTRATION (concentration.py) — jugée par calibration.py. |
| `valide_conditionnel` | CONDITIONNEL PRÉSENT (brique FORME, mode) — se bâtit sur l'infinitif + terminaisons d'imparfait, RÉGLÉ donc VÉ |
| `valide_confidentialite_differentielle` | VALIDATION de la CONFIDENTIALITÉ DIFFÉRENTIELLE (confidentialite_differentielle.py). |
| `valide_conformal` | VALIDATION de la PRÉDICTION CONFORME (conformal.py) — la garantie de couverture DISTRIBUTION-FREE, prouvée par |
| `valide_conformal_adaptatif` | VALIDATION du CONFORME ADAPTATIF (conformal_adaptatif.py) — la couverture tient-elle SOUS DÉRIVE ? Jugé par ca |
| `valide_conformal_jackknife` | VALIDATION du JACKKNIFE+ (conformal_jackknife.py) — jugé par calibration.py. |
| `valide_conformal_label` | VALIDATION du CONFORME LABEL-CONDITIONAL (conformal_label.py). |
| `valide_conformal_normalise` | VALIDATION du CONFORME HÉTÉROSCÉDASTIQUE (conformal_normalise.py) — la couverture CONDITIONNELLE, jugée par ca |
| `valide_conformal_pondere` | VALIDATION du CONFORME PONDÉRÉ (conformal_pondere.py) — jugé par calibration.py. |
| `valide_conformal_quantile` | VALIDATION du CQR (conformal_quantile.py) — jugé par calibration.py. |
| `valide_conjonction` | VALIDATION du SOPHISME DE LA CONJONCTION (conjonction.py). |
| `valide_conjugaison` | VALIDE conjugaison.py — ADVERSARIAL. |
| `valide_conjugaison2` | CONJUGAISON GROUPE 2 (-ir en -iss-) — abat le mur `finir` ; réglé donc vérifiable. |
| `valide_conjugaison_generateur` | CONJUGAISON (brique FORME du langage) — conjuguer est RÉGLÉ donc VÉRIFIABLE (le SENS, lui, n'a pas de juge). |
| `valide_conservation` | VALIDATION du BILAN DE CONSERVATION (conservation.py) — Vague 3. |
| `valide_conservation_aliments` | VALIDE conservation_aliments.py — held-out ADVERSE. |
| `valide_consolidation` | Validation de la CONSOLIDATION : |
| `valide_contrainte` | VALIDATION du SOLVEUR DE CONTRAINTES (contrainte.py) — Vague 2. |
| `valide_controle` | VALIDE controle.py — ADVERSE, FAUX=0. |
| `valide_controle_qualite` | VALIDE controle_qualite.py — held-out ADVERSE. |
| `valide_conversation` | MÉMOIRE DE CONVERSATION — validation (mandat Yohan 2026-06-25, « fossé de l'intelligence éphémère »). |
| `valide_conversion` | CONVERSION DE BASE (2026-06-17, faculté « retranscription ») — déc↔bin↔hex. |
| `valide_convertit_en` | CONVERTIT_KAIKKI multilingue — le MÉCANISME genus est agnostique : |
| `valide_convertit_kaikki` | CONVERTIT_KAIKKI — pont dump Wiktionnaire -> lexique noyau, VÉRIFIÉ sur de VRAIS enregistrements kaikki (en li |
| `valide_coordination` | VALIDE coordination.py — held-out ADVERSE. |
| `valide_coordonnees` | VALIDE l'ingestion des COORDONNÉES (ingere_coordonnees.py) + le câblage ia (coordonnees_lieu / distance_lieux  |
| `valide_copules` | VALIDATION des COPULES (copules.py). |
| `valide_coreference` | CORÉFÉRENCE (brique COMPRÉHENSION — discours) — résoudre un pronom vers son antécédent par le genre. |
| `valide_cosmologie` | VALIDE cosmologie.py — held-out ADVERSE, FAUX=0. |
| `valide_cout_irrecuperable` | VALIDATION du SOPHISME DU COÛT IRRÉCUPÉRABLE (cout_irrecuperable.py). |
| `valide_covariance_grande_dim` | VALIDATION de la COVARIANCE EN GRANDE DIMENSION (covariance_grande_dim.py). |
| `valide_croissance_bacterienne` | VALIDE croissance_bacterienne.py — held-out ADVERSE. |
| `valide_croyance_dempster_shafer` | VALIDATION des FONCTIONS DE CROYANCE (croyance_dempster_shafer.py). |
| `valide_cryobiologie` | VALIDE cryobiologie.py — held-out ADVERSE. |
| `valide_cryptographie_appliquee` | VALIDE cryptographie_appliquee.py — ADVERSE, FAUX=0. |
| `valide_curateur` | Validation de la BRIQUE 8 (le curateur). |
| `valide_curiosite_dirigee` | CURIOSITÉ DIRIGÉE — diriger l'invention vers le trou, mesuré en appels-juge (le mur de l'EXPLORATION). |
| `valide_cybernetique` | VALIDE cybernetique.py — held-out ADVERSE. |
| `valide_cycles_biogeochimiques` | VALIDE cycles_biogeochimiques.py — held-out ADVERSE. |
| `valide_cycles_economiques` | VALIDE cycles_economiques.py — held-out ADVERSE. |
| `valide_decidabilite` | VALIDE decidabilite.py — held-out ADVERSE, FAUX=0. |
| `valide_decision` | VALIDATION de la DÉCISION SOUS INCERTITUDE (decision.py). |
| `valide_decision_ambiguite` | VALIDATION de la DÉCISION SOUS AMBIGUÏTÉ (decision_ambiguite.py). |
| `valide_decouverte_loi` | VALIDATION decouverte_loi.py (Vague 4). |
| `valide_deduction` | VALIDATION — MOTEUR DE DÉDUCTION (la mémoire qui raisonne). |
| `valide_dedup` | DÉDUP ORDONNÉE (brique puissante) — état ensembliste (déjà-vus). |
| `valide_delta_debug` | VALIDATION de delta_debug.py — ddmin. |
| `valide_demande` | DEMANDE — l'interface de requête « la parole » (2026-06-17). |
| `valide_demographie` | VALIDE demographie.py — held-out ADVERSE. |
| `valide_derive_calibration` | VALIDATION du DÉTECTEUR DE DÉRIVE DE CALIBRATION (derive_calibration.py). |
| `valide_desambiguisation` | DÉSAMBIGUÏSATION MULTI-CANAL (brique SENS : |
| `valide_deux_enveloppes` | VALIDATION du PARADOXE DES DEUX ENVELOPPES (deux_enveloppes.py). |
| `valide_dict_accu` | DICT comme ACCUMULATEUR — bâtir un dictionnaire clé -> mesure (thème I : |
| `valide_dict_transform` | TRANSFORMATION DE DICTIONNAIRE — réécrire un dict EXISTANT (front d'après, thème 8). |
| `valide_dimensions` | VALIDATION de l'ALGÈBRE DIMENSIONNELLE (dimensions.py) — brique fondatrice Vague 1. |
| `valide_direction` | Validation de la DIRECTION — la compréhension qui DIRIGE la boucle vivante. |
| `valide_dirichlet_imprecis` | VALIDATION du DIRICHLET IMPRÉCIS (dirichlet_imprecis.py) — jugé par calibration.py. |
| `valide_dirichlet_process` | VALIDATION du PROCESSUS DE DIRICHLET (dirichlet_process.py). |
| `valide_distance_semantique` | DISTANCE SÉMANTIQUE (brique COMPRÉHENSION) — proximité de sens sur le graphe is-a. |
| `valide_diviseurs` | THÉORIE DES DIVISEURS — diviseurs/nb/facteurs premiers. |
| `valide_dkw` | VALIDATION de la BANDE DKW (dkw.py). |
| `valide_document_pdf` | VALIDE document_pdf.py — xref exacte (scan indépendant des offsets) + structure + FAUX=0. |
| `valide_donnees_manquantes` | VALIDATION des DONNÉES MANQUANTES (donnees_manquantes.py) — jugée par calibration.py. |
| `valide_dp2d` | BRIQUE DP 2D / PROGRAMMATION DYNAMIQUE SUR DEUX SÉQUENCES (2026-06-19) — table dp[m+1][n+1] par récurrence (di |
| `valide_drake` | VALIDE drake.py — held-out ADVERSE. |
| `valide_dunning_kruger` | VALIDATION de l'effet DUNNING-KRUGER comme artefact (dunning_kruger.py). |
| `valide_e_process` | VALIDATION de l'E-PROCESS / TEST PAR PARI (e_process.py). |
| `valide_echantillon_pondere` | VALIDATION de l'ESTIMATION PONDÉRÉE (echantillon_pondere.py) — jugée par calibration.py. |
| `valide_eclipses` | VALIDE eclipses.py — held-out ADVERSE. |
| `valide_ecologie` | VALIDE ecologie.py — held-out ADVERSE, FAUX=0. |
| `valide_editeur` | VALIDE editeur.py — ADVERSE, FAUX=0. |
| `valide_electronique` | VALIDE electronique.py — ADVERSE, FAUX=0. |
| `valide_ellsberg` | VALIDATION du PARADOXE D'ELLSBERG (ellsberg.py). |
| `valide_energies_comparees` | VALIDE energies_comparees.py — held-out ADVERSE. |
| `valide_ensemble_calibre` | VALIDATION de l'ENSEMBLE CALIBRÉ (ensemble_calibre.py). |
| `valide_ensembles` | DOMAINE ENSEMBLISTE — algèbre de deux ensembles (2026-06-17, élargir les domaines vérifiables). |
| `valide_entrainement` | VALIDE entrainement.py — held-out ADVERSE (FAUX=0). |
| `valide_entropie_thermo` | VALIDE entropie_thermo.py — held-out ADVERSE (deuxième principe / entropie). |
| `valide_environnement` | VALIDATION de environnement.py — portfolio polyglotte : |
| `valide_equa_diff` | VALIDE equa_diff.py — held-out ADVERSE. |
| `valide_equilibre` | BRIQUE ÉQUILIBRE / SCAN À COMPTEUR DE PROFONDEUR (2026-06-19) — balayer une chaîne en maintenant une profondeu |
| `valide_equilibre_chimique` | VALIDE equilibre_chimique.py — ADVERSE, FAUX=0. |
| `valide_equivalence_semantique` | VALIDATION de equivalence_semantique.py. |
| `valide_ergodicite` | VALIDATION de l'ERGODICITÉ (ergodicite.py). |
| `valide_erreurs_variables` | VALIDATION des ERREURS-EN-VARIABLES (erreurs_variables.py) — jugée par calibration.py. |
| `valide_essais_cliniques` | VALIDE essais_cliniques.py — held-out ADVERSE. |
| `valide_etat` | VALIDATION des ÉTATS & VARIABLES (etat.py) — Vague 1. |
| `valide_etats_matiere` | VALIDE etats_matiere.py — ADVERSE, FAUX=0. |
| `valide_etend_savoir` | ETEND_SAVOIR — l'IA étend SEULE sa taxonomie par fermeture transitive (fetcher INJECTÉ, hors réseau, reproduct |
| `valide_executeur_c` | VALIDATION du backend C (executeur.ExecuteurC) — premier langage COMPILÉ jugé par le MÊME juge (compile && exé |
| `valide_executeur_niches` | VALIDATION des backends de NICHE Prolog/R/SQL (executeur_niches) — 3 PARADIGMES jugés par le MÊME juge, sentin |
| `valide_executeurs_compiles` | VALIDATION des backends COMPILÉS C++/Rust/Go (executeur) — le MÊME juge compile+exécute+juge chacun, sentinell |
| `valide_exp3` | VALIDATION du BANDIT ADVERSARIAL EXP3 (exp3.py). |
| `valide_exploits` | Validation de la BRIQUE 5 (l'observatoire d'exploits). |
| `valide_externalites` | VALIDATION ADVERSARIALE des EXTERNALITÉS (externalites.py). |
| `valide_extraction` | VALIDATION extraction.py (Vague 8). |
| `valide_fabrique_comprehension` | FABRIQUE_COMPREHENSION — corpus d'entraînement vérifié de TOUTE la compréhension (capstone du mandat). |
| `valide_fabrique_francais` | FABRIQUE_FRANCAIS — dataset français de FORME, vérifié par accord prof↔brique (le juge tranche). |
| `valide_fabrique_semantique` | FABRIQUE_SEMANTIQUE — dataset de compréhension vérifié par l'oracle officiel (la définition = la vérité). |
| `valide_fait_negatif` | VALIDATION de fait_negatif.py — fait négatif trivalué au store. |
| `valide_falsification` | VALIDATION falsification.py (Vague 6). |
| `valide_fdr_controle` | VALIDATION du CONTRÔLE DU FDR (fdr_controle.py) — jugé par calibration.py. |
| `valide_feminin` | FÉMININ (brique FORME du langage : |
| `valide_fenetre` | FENÊTRE GLISSANTE — agrégat sur les sous-séquences CONTIGUËS de taille k (front d'après, thème 1). |
| `valide_fermi` | VALIDATION de l'ESTIMATION DE FERMI (fermi.py) — jugée par calibration.py. |
| `valide_filtre_seuil` | FILTRE PARAMÉTRÉ (brique puissante) — filtrer/réduire par un seuil VENANT DE L'ENTRÉE (args[1]). |
| `valide_fonction` | Validateur LÉGER du routage NL → sous-systèmes FONCTION (fonction_nl.resout_fonction). |
| `valide_fractales` | VALIDE fractales.py — held-out ADVERSE, FAUX=0. |
| `valide_fragments_riches` | Validation des FRAGMENTS RICHES — élargir le vocabulaire, pas le moteur. |
| `valide_fraicheur` | VALIDATION fraicheur.py (Vague 8). |
| `valide_frame` | VALIDATION du FRAME N-AIRE (frame.py) — Vague 1. |
| `valide_fusion` | FUSION VERTICALE — 1er étage : |
| `valide_fusion_collections` | ÉLARGIR L'ÉTAGE 1 — la fusion d'expressions aux compréhensions ENSEMBLE et DICT (vocabulaire). |
| `valide_fusion_large` | ÉLARGIR l'étage 1 — jusqu'où la fusion d'EXPRESSIONS porte (avant de monter d'un cran). |
| `valide_fuzz` | Validation de la BRIQUE 6 (le crible sécurité / fuzzing différentiel). |
| `valide_g0` | Validation de G0 — LE PLANCHER (générateur aléatoire). |
| `valide_g1` | Validation de G1 — RÉUTILISATION DU STORE (la mémoire). |
| `valide_g2` | Validation de G2 — SYNTHÈSE PAR BRIQUES (l'échafaudage qui bootstrap). |
| `valide_g3` | Validation de G3 — ablation de l'échafaudage. |
| `valide_g4` | G4 — QUANTIFIER LE MUR : |
| `valide_g5` | Validation de G5 — RECOMBINAISON (l'autonomie : |
| `valide_galois` | VALIDE galois.py — held-out ADVERSE, FAUX=0. |
| `valide_generateur` | Validation de la BRIQUE 3 (le générateur). |
| `valide_generation` | GÉNÉRATION DE PHRASE (brique COMPRÉHENSION — production) — l'IA écrit une phrase complète depuis un sens. |
| `valide_generation_coherente` | GÉNÉRATION COHÉRENTE — l'IA produit des phrases complètes TOTALEMENT cohérentes (grammaire + sémantique + ré-a |
| `valide_generer_tester` | GÉNÉRER-ET-TESTER — le n-ième entier satisfaisant un prédicat (dernière niche du thème II : |
| `valide_genetique` | VALIDE genetique.py — held-out ADVERSE. |
| `valide_genie_chimique` | VALIDE genie_chimique.py — ADVERSE, FAUX=0. |
| `valide_geometrie` | BRIQUE GÉOMÉTRIE COMPUTATIONNELLE ENTIÈRE (2026-06-19) — GenerateurGeometrie : |
| `valide_geometrie2d` | VALIDATION de geometrie2d.py — noyau borné du dessin vectoriel. |
| `valide_geometrie3d` | VALIDATION de geometrie3d.py — maillages 3D. |
| `valide_geometrie_differentielle` | VALIDE geometrie_differentielle.py — held-out ADVERSE, FAUX=0. |
| `valide_geometrie_projective` | VALIDE geometrie_projective.py — ADVERSE, FAUX=0. |
| `valide_geometries_non_euclidiennes` | VALIDE geometries_non_euclidiennes.py — held-out ADVERSE. |
| `valide_geotechnique` | VALIDE geotechnique.py — ADVERSE, FAUX=0. |
| `valide_gestion_risque` | VALIDE gestion_risque.py — held-out ADVERSE. |
| `valide_gibbard_satterthwaite` | VALIDATION de GIBBARD-SATTERTHWAITE (gibbard_satterthwaite.py). |
| `valide_glaciologie` | VALIDE glaciologie.py — held-out ADVERSE (ancres CONNUES non circulaires + soundness + déterminisme). |
| `valide_godel` | VALIDE godel.py — held-out ADVERSE, FAUX=0. |
| `valide_good_turing` | VALIDATION de GOOD-TURING (good_turing.py). |
| `valide_goodhart` | VALIDATION de la LOI DE GOODHART (goodhart.py). |
| `valide_grandeur` | VALIDATION de la GRANDEUR TYPÉE (grandeur.py) — Vague 1. |
| `valide_grandeur_vectorielle` | VALIDATION de grandeur_vectorielle.py — grandeurs vectorielles dimensionnées. |
| `valide_graphe` | GRAPHES — voisins/degré/sommets/arête sur liste d'arêtes. |
| `valide_graphe_typé` | VALIDATION des 3 briques STRUCTURELLES promues 🟡→🟢 (2026-07-02) sur le VRAI corpus : |
| `valide_graphique` | VALIDE graphique.py — projection affine EXACTE (oracle re-dérivé) + rendus déterministes + FAUX=0. |
| `valide_group_by` | GROUP-BY — grouper des paires par clé et agréger (thème I : |
| `valide_groupes` | VALIDE groupes.py — ADVERSE, FAUX=0. |
| `valide_habitabilite` | VALIDE habitabilite.py — held-out ADVERSE. |
| `valide_heraldique` | VALIDE heraldique.py — catalogue fermé + règle de contrariété exacte + FAUX=0 (abstention hors catalogue). |
| `valide_hierarchie_normes` | VALIDE hierarchie_normes.py — held-out ADVERSE. |
| `valide_homeostasie` | VALIDE homeostasie.py — held-out ADVERSE. |
| `valide_hydraulique` | VALIDE hydraulique.py — ADVERSE, FAUX=0. |
| `valide_hydrologie` | VALIDE hydrologie.py — held-out ADVERSE. |
| `valide_ia` | VALIDATION du POINT D'ENTRÉE UNIFIÉ (ia.py) — la façade route bien vers chaque sous-système, en préservant la  |
| `valide_identite` | VALIDATION de l'IDENTITÉ CANONIQUE (identite.py) — Vague 1. |
| `valide_imbrique` | DONNÉES IMBRIQUÉES — itérer deux niveaux (thème I : |
| `valide_immunite` | VALIDE immunite.py — held-out ADVERSE. |
| `valide_imperatif` | IMPÉRATIF (brique FORME, mode) — forme RÉGLÉE donc VÉRIFIABLE (-er : |
| `valide_importance_sampling` | VALIDATION de l'ÉCHANTILLONNAGE PRÉFÉRENTIEL & ESS (importance_sampling.py). |
| `valide_impression_3d` | VALIDE impression_3d.py — held-out ADVERSE. |
| `valide_incertitude` | VALIDATION du JUGE D'INCERTITUDE (incertitude.py) — la SOUNDNESS NON-BORNÉE = la CALIBRATION, vérifiée par SIM |
| `valide_incertitude_decomposee` | VALIDATION de la DÉCOMPOSITION ÉPISTÉMIQUE/ALÉATOIRE (incertitude_decomposee.py) — jugée par calibration.py. |
| `valide_index_ordonne` | INDEXATION ORDONNÉE — accès piloté par une 2ᵉ entrée (front d'après, thème 3). |
| `valide_induction_horn` | VALIDATION de induction_horn.py — induction de règles de Horn validée par exemples. |
| `valide_industrie40` | valide_industrie40.py — validation adversariale de industrie40.py (TRS/OEE). |
| `valide_inference` | INFÉRENCE LOGIQUE (brique COMPRÉHENSION — logique) — déduction 3 valeurs (oui/non/inconnu) sur prémisses. |
| `valide_inference_anytime` | VALIDATION de l'INFÉRENCE ANYTIME-VALID (inference_anytime.py). |
| `valide_inflation` | VALIDE inflation.py — held-out ADVERSE. |
| `valide_info_gap` | VALIDATION de la DÉCISION INFO-GAP (info_gap.py). |
| `valide_information_calcul` | VALIDE information_calcul.py — ADVERSE, FAUX=0. |
| `valide_ingere_dump` | INGERE_DUMP — streaming + déduplication du dump complet, VÉRIFIÉ sur un mini-dump local (reproductible, sans r |
| `valide_ingestion_espace_mineraux` | VALIDATION des veines ingérées 2026-07-02 (run autonome) : |
| `valide_intention` | INTENTION / BUT (brique SENS : |
| `valide_interface` | VALIDATION de l'interface — teste le BACKEND sans navigateur (léger, sound, autonome). |
| `valide_interrogation` | INTERROGATION (brique PRODUCTION) — tourner un sens en question (inversion + -t- euphonique), RÉGLÉ donc VÉRIF |
| `valide_intervalle_tolerance` | VALIDATION de l'INTERVALLE DE TOLÉRANCE (intervalle_tolerance.py) — jugé par calibration.py. |
| `valide_intrication` | VALIDE intrication.py — held-out ADVERSE. |
| `valide_intrus` | INTRUS / CATÉGORIE COMMUNE (brique COMPRÉHENSION) — logique de catégorie sur le graphe de sens. |
| `valide_invariant` | PRÉDICAT STRUCTUREL — « x invariant sous une primitive » : |
| `valide_invention` | L'INVENTION par MUTATION — minter un atome NEUF, jugé par le réel (le mur d'APRÈS). |
| `valide_invention_atomes` | VALIDE invention_atomes.py — le moteur d'invention rend des ATOMES au bon statut (contrat d'atome), FAUX=0. |
| `valide_invention_compounding` | BOUCLE FERMÉE : |
| `valide_invention_divergente` | VALIDATION de invention_divergente.py — les 6 modes d'invention HORS recombinaison (priorité #1 Yohan), câblés |
| `valide_invention_gap` | VALIDATION du MOTEUR DE DÉCOUVERTE D'INVENTIONS (moteur_invention.py). |
| `valide_invention_portee` | LA PORTÉE DE LA MUTATION — jusqu'où l'invention-par-mutation minte, et où elle s'arrête. |
| `valide_invention_substrat` | INVENTION par ÉNUMÉRATION D'UN SUBSTRAT — franchir le mur de la mutation (token de langage absent). |
| `valide_invention_vivante` | L'INVENTION DANS LA BOUCLE VIVANTE — le système grimpe ET se crée ses briques, en autonomie. |
| `valide_iteration` | BRIQUE ITÉRATION / POINT-FIXE (2026-06-19) — répéter un pas scalaire jusqu'à une condition. |
| `valide_jensen` | VALIDATION de l'INÉGALITÉ DE JENSEN (jensen.py). |
| `valide_jeux_appliques` | VALIDE jeux_appliques.py — held-out ADVERSE. |
| `valide_jeux_zero_somme` | VALIDATION des JEUX À SOMME NULLE (jeux_zero_somme.py). |
| `valide_jointure` | FUSION VERTICALE — CAP 2 : |
| `valide_jointure_profonde` | JOINTURE PROFONDE — joindre deux sous-résultats PROFONDS par une op (fin de la famille C de la carte). |
| `valide_jointure_profonde_stress` | STRESS de JOINTURE PROFONDE — mettre la brique à l'épreuve (consigne Yohan : |
| `valide_journalisme_deontologie` | VALIDE journalisme_deontologie.py — held-out ADVERSE. |
| `valide_juge` | Validation de la BRIQUE 1 (le juge). |
| `valide_juge_rapide` | ÉQUIVALENCE + SÛRETÉ du JUGE RAPIDE (fork) vs le juge subprocess de référence. |
| `valide_jury_condorcet` | VALIDATION du THÉORÈME DU JURY DE CONDORCET (jury_condorcet.py). |
| `valide_kalman_robuste` | VALIDATION du FILTRE DE KALMAN ROBUSTE (kalman_robuste.py). |
| `valide_kde` | VALIDATION du KDE (kde.py). |
| `valide_kelly` | VALIDATION du CRITÈRE DE KELLY (kelly.py). |
| `valide_langages_formels` | VALIDE langages_formels.py — held-out ADVERSE, FAUX=0. |
| `valide_langue_ia` | VALIDATION du câblage LANGUE de ia.py — `ia.conjugue` / `ia.ecris` / `ia.comprends` / `ia.comprends_texte` (le |
| `valide_lecteur` | VALIDATION du LECTEUR GÉNÉRIQUE DE DONNÉES (`lecteur.py`) — le moteur du borné DATA (chantier #3). |
| `valide_lecteur_client` | VALIDE lecteur_daemon + lecteur_client — le CHEMIN RAPIDE interactif (OPTIM), FAUX=0, sans régression. |
| `valide_lecteur_norme` | VALIDATION de la normalisation de VALEUR avant conflit (lecteur._norme_valeur, durcissement 2026-07-02). |
| `valide_lecteur_nuit` | Validateur FAUX=0 des veines ingérées pendant la NUIT autonome 2026-06-29 (Levier 3 harvester). |
| `valide_lecteur_t10` | VALIDATION T10 — SPORT & COMPÉTITIONS (couloir d'ingestion). |
| `valide_lecteur_t11` | VALIDATION T11 — TRANSPORT, VÉHICULES & INFRASTRUCTURE (couloir d'ingestion). |
| `valide_lecteur_t12` | VALIDATEUR T12 — sanité FAUX=0 des relations RELIGION / MYTHOLOGIE / PHILOSOPHIE (OFFLINE). |
| `valide_lecteur_t4` | SANITÉ T4 — couloir VIVANT (biologie). |
| `valide_lecteur_t5` | VALIDATION T5 — ŒUVRES CULTURELLES (créateurs/production). |
| `valide_lecteur_t6` | VALIDATEUR T6 — sanité FAUX=0 des relations PERSONNES & ORGANISATIONS (OFFLINE). |
| `valide_lecteur_t7` | VALIDATION T7 — MESURES NUMÉRIQUES & TECHNIQUE (couloir d'ingestion). |
| `valide_lecteur_t8` | VALIDATION T8 — HISTOIRE, DATES & POLITIQUE (couloir d'ingestion). |
| `valide_lecteur_t9` | VALIDATION T9 — LANGUE, LEXIQUE & ÉCRITURE (couloir d'ingestion). |
| `valide_lecture_comprehension` | LECTURE & COMPRÉHENSION — l'IA lit des faits et répond par LOGIQUE (capstone du mandat compréhension). |
| `valide_liaisons_chimiques` | VALIDE liaisons_chimiques.py — held-out ADVERSE. |
| `valide_limite` | VALIDATION de la LIMITE THÉORIQUE & ÉCART (limite.py) — Vague 3. |
| `valide_lindley` | VALIDATION du PARADOXE DE LINDLEY (lindley.py). |
| `valide_liste_transforms` | TRANSFORMS DE LISTE — rotation/blocs/entrelace. |
| `valide_localisation_faute` | VALIDATION de localisation_faute.py — localisation spectrum-based (Ochiai) + réparation par recherche. |
| `valide_logique` | DOMAINE LOGIQUE — quantificateurs de comptage (2026-06-17, élargir les domaines vérifiables). |
| `valide_logique_tri` | VALIDATION logique_tri.py (Vague 1). |
| `valide_logistique` | VALIDE logistique.py — held-out ADVERSE. |
| `valide_loi` | VALIDATION des LOIS MANIPULABLES (loi.py) — Vague 2. |
| `valide_loi_grands_nombres` | VALIDATION de la LOI DES GRANDS NOMBRES MAL COMPRISE (loi_grands_nombres.py). |
| `valide_loi_puissance` | VALIDATION des LOIS À QUEUE LOURDE (loi_puissance.py). |
| `valide_lord` | VALIDATION du PARADOXE DE LORD (lord.py). |
| `valide_main_chaude` | VALIDATION du SOPHISME DU JOUEUR & MAIN CHAUDE (main_chaude.py). |
| `valide_malediction_dimension` | VALIDATION de la MALÉDICTION DE LA DIMENSION (malediction_dimension.py). |
| `valide_map_repli` | MAP-PUIS-REPLI — replier un agrégateur sur une séquence TRANSFORMÉE par une primitive (famille C de la carte). |
| `valide_maritime` | VALIDE maritime.py — ADVERSE, FAUX=0. |
| `valide_marketing_mecanismes` | VALIDE marketing_mecanismes.py — held-out ADVERSE. |
| `valide_marketing_metrics` | VALIDE marketing_metrics.py — held-out ADVERSE. |
| `valide_math_avance` | MATH AVANCÉ (faculté analyse/calcul) — isqrt/lcm/comb/pow_mod. |
| `valide_maths_discretes` | VALIDE maths_discretes.py — held-out ADVERSE, FAUX=0. |
| `valide_maths_financieres` | VALIDE maths_financieres.py — held-out ADVERSE. |
| `valide_matrice` | MATRICE 2D — opérations STRUCTURELLES sur une liste de listes (front d'après, thème 2). |
| `valide_matrice_confusion` | VALIDATION de la MATRICE DE CONFUSION & TAUX DE BASE (matrice_confusion.py). |
| `valide_matrice_reduce` | MATRICE + REDUCE (brique puissante) — réduire les agrégats de lignes/colonnes en un scalaire. |
| `valide_maximum_entropie` | VALIDATION du MAXIMUM D'ENTROPIE (maximum_entropie.py). |
| `valide_maxwell` | VALIDE maxwell.py — held-out ADVERSE. |
| `valide_mdl` | VALIDATION du MDL (mdl.py). |
| `valide_mecanique` | VALIDE mecanique.py — ADVERSE, FAUX=0. |
| `valide_mecanismes` | VALIDE mecanismes.py — held-out ADVERSE. |
| `valide_mecanismes_machines` | VALIDE mecanismes_machines.py — held-out ADVERSE. |
| `valide_mecanismes_reactionnels` | VALIDE mecanismes_reactionnels.py — held-out ADVERSE, FAUX=0. |
| `valide_medecines_alternatives` | VALIDE medecines_alternatives.py — held-out ADVERSE. |
| `valide_memoire` | VALIDATION — MÉMOIRE DE BRIQUES PERSISTANTE (apprend / retient / réutilise, sound). |
| `valide_mereologie` | VALIDATION de la MÉRÉOLOGIE (mereologie.py) — Vague 1. |
| `valide_mesure` | Validation de la BRIQUE 7 (le mesureur d'apprentissage). |
| `valide_mesures_sociales` | VALIDE mesures_sociales.py — held-out ADVERSE. |
| `valide_meta` | MÉTA-ROUTEUR INTÉGRÉ (2026-06-19, vision Yohan « s'adapter à la situation, router par clé/x/y comme le cerveau |
| `valide_meta_analyse` | VALIDATION de la MÉTA-ANALYSE (meta_analyse.py) — jugée par calibration.py. |
| `valide_microprocesseurs` | VALIDE microprocesseurs.py — ADVERSE, FAUX=0. |
| `valide_mineraux` | VALIDE mineraux.py — held-out ADVERSE. |
| `valide_monnaie` | RENDU DE MONNAIE (brique puissante) — DP d'optimisation (min pièces). |
| `valide_moteur_raisonnement` | VALIDATION du CÂBLAGE end-to-end (moteur_raisonnement.py) — les briques dialoguent vraiment. |
| `valide_mots` | PARSING CHAÎNE — découper / transformer / rejoindre les MOTS (famille D : |
| `valide_multicalibration` | VALIDATION de la MULTICALIBRATION (multicalibration.py) — jugée par calibration.py appliquée PAR GROUPE. |
| `valide_multientree` | COMPOSITION MULTI-ENTRÉE — lever le mur de l'arité ≥ 2 (joindre plusieurs arguments). |
| `valide_multilabel` | VALIDATION de la CALIBRATION MULTI-LABEL (multilabel.py) — jugée par calibration.py + risque_conforme. |
| `valide_multinomial_simultane` | VALIDATION des IC SIMULTANÉS MULTINOMIAUX (multinomial_simultane.py) — jugés par calibration.py. |
| `valide_multipasse` | MULTI-PASSE — filtrer par un AGRÉGAT du TOUT (thème II du prochain front : |
| `valide_mur` | DIAGNOSTIC — cartographier le MUR (mesurer et analyser avant de décider). |
| `valide_mutation_comparaisons` | MUTATION DES COMPARAISONS → PRÉDICATS INVENTÉS, dans la boucle vivante (le mur d'avant le contrôle). |
| `valide_mutation_testing` | VALIDATION de mutation_testing.py. |
| `valide_mutations` | VALIDE mutations.py — held-out ADVERSE. |
| `valide_navigation` | VALIDE navigation.py — ADVERSE, FAUX=0. |
| `valide_negation` | NÉGATION (brique COMPRÉHENSION — phrase) — comprendre « ne…pas » : |
| `valide_negation_phrase` | NÉGATION (PRODUCTION) — tourner un sens en phrase négative (encadrement ne…pas), RÉGLÉ donc VÉRIFIABLE. |
| `valide_neurone_biologique` | VALIDE neurone_biologique.py — held-out ADVERSE. |
| `valide_no_free_lunch` | VALIDATION du THÉORÈME NO FREE LUNCH (no_free_lunch.py). |
| `valide_nombres_complexes` | VALIDE nombres_complexes.py — held-out ADVERSE. |
| `valide_nomenclature_chimique` | VALIDE nomenclature_chimique.py — held-out ADVERSE. |
| `valide_normalisation` | NORMALISATION / ROBUSTESSE (brique SENS : |
| `valide_nouveaute` | VALIDATION de la DÉTECTION DE NOUVEAUTÉ (nouveaute.py). |
| `valide_noyau_comprehension` | NOYAU DE COMPRÉHENSION — laisser le RÉEL décider du PÉRIMÈTRE de la déduplication, EXHAUSTIVEMENT (idée de Yoh |
| `valide_nucleosynthese` | VALIDE nucleosynthese.py — held-out ADVERSE. |
| `valide_opinions` | VALIDATION de l'AGRÉGATION D'OPINIONS (opinions.py) — jugée par scores_propres.py. |
| `valide_optimisation` | DÉCISION / OPTIMISATION — choisir le MEILLEUR élément par un critère dérivé (2026-06-17, brique cognitive 2/2  |
| `valide_optimisation_bayesienne` | VALIDATION de l'OPTIMISATION BAYÉSIENNE (optimisation_bayesienne.py) — jugée par calibration.py. |
| `valide_oracle_definitions` | ORACLE DÉFINITIONS — la définition officielle = vérité -> savoir auto-construit -> domaines nouveaux prouvable |
| `valide_orchestrateur_invention` | VALIDATION de orchestrateur_invention.py — le capstone multi-mode. |
| `valide_orchestre` | L'ORCHESTRATEUR — une seule façade sur toute la trousse, en ESCALADE DIRIGÉE. |
| `valide_ordinaux` | VALIDE ordinaux.py — ADVERSE, FAUX=0. |
| `valide_p_box` | VALIDATION des P-BOXES (p_box.py) — jugée par calibration.py. |
| `valide_p_hacking` | VALIDATION du P-HACKING (p_hacking.py). |
| `valide_pac_bayes` | VALIDATION des bornes PAC-BAYES (pac_bayes.py). |
| `valide_paires` | PAIRES — quantification ∃ sur tous les couples i<j (front d'après, thème 5). |
| `valide_paradoxes` | VALIDE paradoxes.py — held-out ADVERSE, FAUX=0. |
| `valide_paraphrase` | PARAPHRASE / MÊME SENS (brique COMPRÉHENSION) — voir au-delà des mots de surface (synonymes). |
| `valide_pareto` | VALIDATION pareto.py (Vague 5). |
| `valide_parrondo` | VALIDATION du PARADOXE DE PARRONDO (parrondo.py). |
| `valide_parseur_fichiers` | VALIDATION de parseur_fichiers.py — routeur de formats. |
| `valide_parsing` | PARSING STRUCTURÉ (2026-06-17, faculté « analyse/retranscription ») — chaîne -> dict/liste. |
| `valide_participe_present` | PARTICIPE PRÉSENT (brique FORME, -ant) — forme verbale RÉGLÉE donc VÉRIFIABLE. |
| `valide_pascal_mugging` | VALIDATION du PROBLÈME DE PASCAL (pascal_mugging.py). |
| `valide_passe_compose` | PASSÉ COMPOSÉ (brique FORME COMPOSÉE) — temps composé = auxiliaire avoir + participe passé, RÉGLÉ donc VÉRIFIA |
| `valide_pedologie` | VALIDE pedologie.py — held-out ADVERSE. |
| `valide_petits_nombres` | VALIDATION de la LOI DES PETITS NOMBRES (petits_nombres.py). |
| `valide_petrochimie` | VALIDE petrochimie.py — held-out ADVERSE. |
| `valide_pharmacochimie` | VALIDE pharmacochimie.py — ADVERSE, FAUX=0. |
| `valide_physique` | VALIDE physique.py — held-out ADVERSE. |
| `valide_pib` | VALIDE pib.py — held-out ADVERSE. |
| `valide_pile` | BRIQUE PILE / MONOTONE (2026-06-19) — GenerateurPile : |
| `valide_planification` | VALIDATION planification.py (Vague 5). |
| `valide_plastiques` | VALIDE plastiques.py — held-out ADVERSE. |
| `valide_plateau` | LA CARTE DU PLAFOND — mesurer OÙ la composition-sur-atomes-semés cale, et POURQUOI. |
| `valide_pli` | FUSION VERTICALE — 2e étage, variante 2b : |
| `valide_pluriel` | PLURIEL (brique FORME du langage : |
| `valide_poisson` | VALIDATION de l'ESTIMATION POISSON (poisson.py) — jugée par calibration.py. |
| `valide_poisson_nonhomogene` | VALIDATION du PROCESSUS DE POISSON NON-HOMOGÈNE (poisson_nonhomogene.py) — jugée par calibration.py. |
| `valide_polyglotte` | GÉNÉRATION MULTI-LANGAGE (2026-06-17) — l'IA ÉCRIT du code dans un autre langage que Python, vérifié par l'exe |
| `valide_polymeres` | VALIDE polymeres.py — held-out ADVERSE. |
| `valide_population_pays` | VALIDE l'ingestion population_pays (Banque mondiale) + le câblage ia.densite_pays — ADVERSE, FAUX=0. |
| `valide_portefeuille_universel` | VALIDATION du PORTEFEUILLE UNIVERSEL (portefeuille_universel.py). |
| `valide_positionnel` | LOGIQUE POSITIONNELLE — agrégats positions paires vs impaires (famille D : |
| `valide_posologie` | VALIDE posologie.py — held-out ADVERSE. |
| `valide_possibilite` | VALIDATION de la THÉORIE DES POSSIBILITÉS (possibilite.py) — jugée par calibration.py. |
| `valide_predicat_mesures` | PRÉDICAT STRUCTUREL sur MESURES — `m1(x) CMP m2(x)` (famille B : |
| `valide_predictif` | VALIDATION de la CALIBRATION PRÉDICTIVE (predictif.py). |
| `valide_prediction` | Validation de la COMPRÉHENSION (2/2) — la prédiction. |
| `valide_prefixe_commun` | PRÉFIXE/SUFFIXE COMMUN (brique puissante) — réduction croisée d'une liste de chaînes. |
| `valide_premier_unique` | BRIQUE PREMIER-UNIQUE / FRÉQUENCE PUIS PREMIER SATISFAISANT (2026-06-19) — deux passes : |
| `valide_prete_a_apprendre` | VALIDE — L'IA EST PRÊTE À APPRENDRE (2026-06-17). |
| `valide_preuve_propositionnelle` | Validateur ADVERSARIAL de preuve_propositionnelle — ancres logiques connues + oracle indépendant (est_tautolog |
| `valide_prevision` | VALIDATION de la PRÉVISION TEMPORELLE (prevision.py) — jugée par calibration.py. |
| `valide_prevision_walley` | VALIDATION des PRÉVISIONS INFÉRIEURES/SUPÉRIEURES de Walley (prevision_walley.py) — jugée par calibration.py. |
| `valide_prior_shift` | VALIDATION de la CORRECTION DE PRIOR / LABEL SHIFT (prior_shift.py) — jugée par calibration.py. |
| `valide_procedes_fabrication` | VALIDE procedes_fabrication.py — held-out ADVERSE. |
| `valide_procedes_industriels` | Validateur adversarial de procedes_industriels (FAUX=0). |
| `valide_processus_gaussien` | VALIDATION du PROCESSUS GAUSSIEN (processus_gaussien.py) — jugée par calibration.py. |
| `valide_profilage` | VALIDATION de profilage.py — classification de complexité empirique (déterministe, sur coûts d'opérations comp |
| `valide_profond` | RÉCURSION SUR STRUCTURE (brique puissante) — réduire les feuilles d'une imbrication de profondeur ARBITRAIRE. |
| `valide_propagande` | valide_propagande.py — validation ADVERSARIALE de propagande.py. |
| `valide_propagation` | VALIDATION de la PROPAGATION D'INCERTITUDE (propagation.py) — l'intervalle propagé est-il CALIBRÉ ? Jugé par c |
| `valide_property_based` | VALIDATION de property_based.py — falsification active. |
| `valide_proportion_binomiale` | VALIDATION de l'INTERVALLE DE PROPORTION BINOMIALE (proportion_binomiale.py) — jugé par calibration.py. |
| `valide_proprietes_materiaux` | VALIDE proprietes_materiaux.py — held-out ADVERSE. |
| `valide_proteines` | VALIDE proteines.py — held-out ADVERSE. |
| `valide_pseudosciences` | VALIDE pseudosciences.py — catalogue de consensus fermé + abstention hors catalogue (FAUX=0). |
| `valide_psychometrie` | VALIDE psychometrie.py — held-out ADVERSE. |
| `valide_qualitatif` | VALIDATION qualitatif.py (Vague 4). |
| `valide_quantificateur` | QUANTIFICATEURS (brique COMPRÉHENSION — logique) — tous / certains / aucun sur un ensemble, via closure is-a. |
| `valide_quantile_regression` | VALIDATION de la RÉGRESSION QUANTILE (quantile_regression.py) — jugée par calibration.py. |
| `valide_quantique` | VALIDE quantique.py — held-out ADVERSE. |
| `valide_questions` | RÉPONDEUR IA — questions/réponses unifiées model-free (démonstration de l'étendue SANS modèle). |
| `valide_rademacher` | VALIDATION de la COMPLEXITÉ DE RADEMACHER (rademacher.py). |
| `valide_raisonnement_defaut` | VALIDE raisonnement_defaut.py — exception prime, défaut sur membre connu, abstention sur inconnu, FAUX=0. |
| `valide_ranking` | CLASSEMENT / PRIORISATION — ordonner par critère dérivé (2026-06-17, brique cognitive). |
| `valide_rapport_invention` | VALIDATION du RAPPORT D'INVENTION UNIFIÉ (rapport_invention.py). |
| `valide_raster_png` | VALIDE raster_png.py — round-trip pixel-parfait + FAUX=0 (rejet des flux corrompus, abstention hors cadre). |
| `valide_rayonnement_thermique` | VALIDE rayonnement_thermique.py — held-out ADVERSE, FAUX=0. |
| `valide_recettes` | VALIDE recettes.py — held-out ADVERSE. |
| `valide_record` | RECORD À COMPLÉTUDE GRADUABLE — 1ʳᵉ brique du FRONT GÉNÉRATIF (2026-06-17, vision Yohan « sélectionner ce qu'o |
| `valide_recurrence` | CONTRÔLE GÉNÉRALISÉ (1) — RÉCURRENCE à DEUX ÉTATS sur un compte (le pli/boucle n'ont qu'UN accumulateur). |
| `valide_redox` | VALIDE redox.py — held-out ADVERSE. |
| `valide_refactor` | VALIDATION de refactor.py — refactor préservant le comportement. |
| `valide_references` | VALIDE references.py — held-out ADVERSE. |
| `valide_region_multivariee` | VALIDATION des RÉGIONS MULTIVARIÉES CONFORMES (region_multivariee.py) — jugée par calibration.py. |
| `valide_regle` | VALIDATION du MOTEUR DE RÈGLES NORMATIVES (regle.py). |
| `valide_regles_induites` | VALIDATION de regles_induites.py — pont induction→déduction. |
| `valide_regression_fallacieuse` | VALIDATION de la RÉGRESSION FALLACIEUSE (regression_fallacieuse.py). |
| `valide_regression_moyenne` | VALIDATION de la RÉGRESSION VERS LA MOYENNE (regression_moyenne.py). |
| `valide_regression_robuste` | VALIDATION de la RÉGRESSION ROBUSTE (regression_robuste.py) — jugée par calibration.py. |
| `valide_relation_lexicale` | RELATIONS LEXICALES (brique SENS niv.2 : |
| `valide_relations_lexique` | RELATIONS_LEXIQUE — syn/ant du dictionnaire branchés sur les briques SENS, VÉRIFIÉ sur de VRAIS enregistrement |
| `valide_relativite_generale` | VALIDE relativite_generale.py — held-out ADVERSE, FAUX=0. |
| `valide_relativite_restreinte` | VALIDE relativite_restreinte.py — held-out ADVERSE. |
| `valide_relaxation` | VALIDATION relaxation.py (Vague 5). |
| `valide_repetition` | RÉPÉTITION COMPTÉE — appliquer une op binaire args[1] fois (compte = 2ᵉ entrée). |
| `valide_reseaux_ip` | VALIDE reseaux_ip.py — ADVERSE, FAUX=0. |
| `valide_reseaux_neurones` | VALIDE reseaux_neurones.py — ADVERSE, FAUX=0. |
| `valide_resolution` | VALIDATION de la résolution floue d'entités (resolution.py) — tolérance aux fautes, FAUX=0. |
| `valide_resoudre_tout` | VALIDE — RÉSOLUTION CHAÎNÉE (2026-06-22, point 4). |
| `valide_restitution` | VALIDATION — MOTEUR DE RESTITUTION (routé, exact, ACT-R, consolidation, sound). |
| `valide_restitution_fraiche` | VALIDATION de restitution_fraiche.py — gate de fraîcheur. |
| `valide_retraite` | VALIDE retraite.py — held-out ADVERSE. |
| `valide_revelation_bayesienne` | VALIDATION de la RÉVÉLATION BAYÉSIENNE (revelation_bayesienne.py). |
| `valide_revision` | VALIDATION revision.py (Vague 8). |
| `valide_rhetorique` | VALIDE rhetorique.py — held-out ADVERSE. |
| `valide_richesse` | NIVEAU DE RICHESSE — le « cran » sélectionnable (2026-06-17, vision Yohan : |
| `valide_ridge` | VALIDATION de la RÉGRESSION RIDGE (ridge.py). |
| `valide_risque_conforme` | VALIDATION du CONTRÔLE DE RISQUE CONFORME (risque_conforme.py). |
| `valide_robotique` | VALIDE robotique.py — ADVERSE, FAUX=0. |
| `valide_robust_bayes` | VALIDATION du BAYES ROBUSTE par ε-contamination (robust_bayes.py) — jugé par calibration.py. |
| `valide_roc_auc` | VALIDATION de l'AUC + IC (roc_auc.py) — jugée par calibration.py. |
| `valide_routage` | AUTO-ROUTAGE DU VERSEMENT — la dernière soudure pour que la clôture tourne EN AUTONOMIE. |
| `valide_routage_sota` | RAFFINEMENTS SOTA DU ROUTAGE (2026-07-02) — Smith's rule / SUNNY / presolve SATzilla / auto-config AutoFolio. |
| `valide_routage_strategie` | ROUTAGE DE STRATÉGIE PAR CLÉ (2026-06-19, idée Yohan) — l'IA apprend, par clé, la stratégie de traversée la MO |
| `valide_routeur_langage` | VALIDATION de routeur_langage.py — trie les langages présents+jugeables par besoin. |
| `valide_run_length` | RUN-LENGTH ENCODE — compression stateful avec construction de sortie (front d'après, thème 7). |
| `valide_saint_petersbourg` | VALIDATION du PARADOXE DE SAINT-PÉTERSBOURG (saint_petersbourg.py). |
| `valide_savoir_massif` | SAVOIR_MASSIF — le lexique branché comme ressource des briques SENS, VÉRIFIÉ sur une petite taxonomie inline ( |
| `valide_scores_propres` | VALIDATION des SCORES PROPRES (scores_propres.py) — la PROPERNESS (un score minimisé en espérance par la VRAIE |
| `valide_scrutin` | VALIDE scrutin.py — held-out ADVERSE. |
| `valide_seismologie` | VALIDE seismologie.py — lois exactes (oracle re-dérivé), réciproques, invariants d'échelle, FAUX=0. |
| `valide_semiconducteurs` | VALIDE semiconducteurs.py — held-out ADVERSE. |
| `valide_sens_executable` | SENS EXÉCUTABLE (brique SENS niv.3, cœur du défi) — un VERBE (mot) -> une ACTION que le juge LANCE (grounding  |
| `valide_serie` | PLUS LONGUE SÉRIE — run-length, état à travers la séquence (dernière niche du thème II). |
| `valide_serie_autoregressive` | VALIDATION de la PRÉVISION AUTO-RÉGRESSIVE (serie_autoregressive.py) — jugée par calibration.py. |
| `valide_serie_multivariee` | VALIDATION de la PRÉVISION MULTIVARIÉE VAR (serie_multivariee.py) — jugée par calibration.py. |
| `valide_series_calcul` | VALIDE series_calcul.py — ADVERSE, FAUX=0. |
| `valide_session` | Validation de la BRIQUE 9 (la session d'entraînement de bout en bout). |
| `valide_shiryaev` | VALIDATION de la DÉTECTION AU PLUS TÔT (shiryaev.py) — jugée par calibration.py. |
| `valide_simpson` | VALIDATION du PARADOXE DE SIMPSON (simpson.py). |
| `valide_simulation` | VALIDATION de la SIMULATION / FORWARD-MODEL (simulation.py) — Vague 3. |
| `valide_smooth_ambiguity` | VALIDATION de l'AMBIGUÏTÉ LISSE (smooth_ambiguity.py). |
| `valide_sophismes` | valide_sophismes.py — validation ADVERSARIALE de sophismes.py. |
| `valide_sources` | VALIDATION du REGISTRE DES SOURCES (`sources.py` / datasets/sources/registry.jsonl). |
| `valide_sous_suite` | PLUS LONGUE SOUS-SUITE MONOTONE (DP/LIS) — sous-suite NON contiguë (front d'après, thème 4). |
| `valide_stabilite_algorithmique` | VALIDATION de la STABILITÉ ALGORITHMIQUE (stabilite_algorithmique.py). |
| `valide_statique` | VALIDE statique.py — ADVERSE, FAUX=0. |
| `valide_statistiques` | ANALYSE STATISTIQUE (2026-06-17, faculté « analyse ») — médiane/mode/moyenne/écart. |
| `valide_stein` | VALIDATION du PARADOXE DE STEIN (stein.py). |
| `valide_stereochimie` | VALIDE stereochimie.py — ADVERSE, FAUX=0. |
| `valide_stoechiometrie` | VALIDE stoechiometrie.py — ADVERSE, FAUX=0. |
| `valide_store` | Validation de la BRIQUE 2 (le store). |
| `valide_strategie_jeux` | VALIDE strategie_jeux.py — held-out ADVERSE. |
| `valide_stress_noyau` | STRESS / PERF ENFER+ du noyau de compréhension — la RÉALITÉ (le juge + son timeout) exige la forme EFFICACE. |
| `valide_structure_mapping` | VALIDATION structure_mapping.py (Vague 4). |
| `valide_structures_genie` | VALIDE structures_genie.py — held-out ADVERSE, FAUX=0. |
| `valide_subjonctif` | SUBJONCTIF PRÉSENT (brique FORME, mode) — « que je parle », RÉGLÉ donc VÉRIFIABLE. |
| `valide_substrat_physique` | VALIDATION du SUBSTRAT-RÉEL (substrat_physique.py). |
| `valide_substrat_reel` | VALIDE substrat_reel.py — le gap-engine d'invention branché sur les 71 M faits, FAUX=0. |
| `valide_substrat_vivant` | LE SUBSTRAT DANS LA BOUCLE VIVANTE — l'invention par énumération devient un ÉTAGE de l'orchestrateur. |
| `valide_suite` | BRIQUE SUITES & MOTIFS (2026-06-19) — GenerateurSuite : |
| `valide_surapprentissage` | VALIDATION du SUR-APPRENTISSAGE (surapprentissage.py). |
| `valide_surdispersion` | VALIDATION de la SUR-DISPERSION (surdispersion.py) — jugée par calibration.py. |
| `valide_surface_ia` | VALIDATION DE LA SURFACE DE ia.py — gate statique quasi-gratuite (AST, aucun chargement du lecteur). |
| `valide_survie` | VALIDATION de l'ANALYSE DE SURVIE (survie.py) — jugée par calibration.py. |
| `valide_systeme` | VALIDE SYSTÈME — tâches COMPOSITES DURES en montée (consigne Yohan : |
| `valide_systemes_politiques` | VALIDE systemes_politiques.py — held-out ADVERSE. |
| `valide_tableur_xlsx` | VALIDE tableur_xlsx.py — round-trip des valeurs (oracle unzip+XML) + refs A1 exactes + FAUX=0. |
| `valide_taux_de_base` | VALIDATION de la NÉGLIGENCE DU TAUX DE BASE (taux_de_base.py). |
| `valide_taxonomie` | VALIDATION de taxonomie.py — taxonomie de types dérivée des DONNÉES (FAUX=0). |
| `valide_tbm` | VALIDATION du TRANSFERABLE BELIEF MODEL (tbm.py) — jugé par calibration.py. |
| `valide_techniques_culinaires` | VALIDE techniques_culinaires.py — held-out ADVERSE. |
| `valide_telecom` | VALIDE telecom.py — ADVERSE, FAUX=0. |
| `valide_teledetection` | VALIDE teledetection.py — held-out ADVERSE. |
| `valide_temperature` | VALIDATION du TEMPERATURE SCALING (temperature.py) — jugé par calibration.py. |
| `valide_temporel` | LOGIQUE TEMPORELLE (brique COMPRÉHENSION — logique) — ordonner des événements selon « avant » (tri topologique |
| `valide_test_calibration` | VALIDATION du TEST DE CALIBRATION (test_calibration.py). |
| `valide_test_permutation` | VALIDATION du TEST DE PERMUTATION (test_permutation.py). |
| `valide_theorie_nombres` | BRIQUE THÉORIE DES NOMBRES — AGRÉGATS SUR 1..n (2026-06-19) — extension de GenerateurDiviseurs : |
| `valide_theorie_reseaux` | VALIDE theorie_reseaux.py — ADVERSE, FAUX=0. |
| `valide_topographie_arpentage` | VALIDE topographie_arpentage.py — ADVERSE, FAUX=0. |
| `valide_topologie` | VALIDE topologie.py — held-out ADVERSE, FAUX=0. |
| `valide_toxicologie` | VALIDE toxicologie.py — held-out ADVERSE. |
| `valide_trace` | VALIDATION trace.py (Vague 7). |
| `valide_transfert` | VALIDE transfert.py — l'assembleur inter-domaines. |
| `valide_transport_membranaire` | VALIDE transport_membranaire.py — held-out ADVERSE. |
| `valide_triangulation` | VALIDATION triangulation.py (Vague 6). |
| `valide_trigonometrie` | VALIDE trigonometrie.py — ADVERSE, FAUX=0. |
| `valide_turing` | VALIDE turing.py — ADVERSE, FAUX=0. |
| `valide_types_categories` | VALIDE types_categories.py — ADVERSE, FAUX=0. |
| `valide_urgence_medicale` | VALIDE urgence_medicale.py — ADVERSE, FAUX=0. |
| `valide_usinage` | VALIDE usinage.py — held-out ADVERSE. |
| `valide_utilite` | Validation de la brique UTILITÉ ÉVOLUTIVE. |
| `valide_vague10` | VAGUE 10 — géométrie computationnelle / CRT / DP / chaînes (2026-06-19, autonomie). |
| `valide_vague11` | VAGUE 11 — Bellman-Ford / spirale / 3D / jokers / DP / zigzag / max-xor / chiffres (2026-06-19, autonomie). |
| `valide_vague12` | VAGUE 12 — Floyd-Warshall / topo / KMP / Z-function / somme-2-carrés / variance / suite consécutive (2026-06-1 |
| `valide_vague13` | VAGUE 13 — DP (word break, profit, décodages) / combinatoire (Bell, Stirling) / déterminant entier / Möbius /  |
| `valide_vague14` | VAGUE 14 — INTERVAL SCHEDULING (transfer web) + breadth (2026-06-19, nuit). |
| `valide_vague15` | VAGUE 15 — PILE MONOTONE + GREEDY (2026-06-20, nuit). |
| `valide_vague16` | VAGUE 16 — DP / deux-pointeurs / fenêtre / pile / chaîne (2026-06-20, nuit, protocole 1.5 Go). |
| `valide_vague17` | VAGUE 17 — greedy / DP / fenêtre / chaînes arithmétiques (2026-06-20, nuit, 1.5 Go). |
| `valide_vague18` | VAGUE 18 — dates / géométrie 3D / théorie des jeux / bits / automate cellulaire (2026-06-20, nuit, 1.5 Go). |
| `valide_vague19` | VAGUE 19 — Excel / chaînes / DP / théorie des nombres (2026-06-20, nuit, 1.5 Go). |
| `valide_vague20` | VAGUE 20 — dénombrement / numération / chaîne (2026-06-20, nuit, 1.5 Go). |
| `valide_vague21` | VAGUE 21 — parsing / chiffres / chaînes / DP / greedy (2026-06-20, nuit, 1.5 Go). |
| `valide_vague22` | VAGUE 22 — théorie des nombres / DP / chaîne / bits / géométrie (2026-06-20, nuit, 1.5 Go). |
| `valide_vague23` | VAGUE 23 — chaînes arithmétiques / pile / nombres / tableau (2026-06-20, nuit, 1.5 Go). |
| `valide_vague24` | VAGUE 24 — DP / tableaux / bits (2026-06-20, nuit, 1.5 Go). |
| `valide_vague25` | VAGUE 25 — DP / fenêtre / grille BFS / bits (2026-06-20, nuit, 1.5 Go). |
| `valide_vague26` | VAGUE 26 — tableaux / DP / pile / bits / chaîne (2026-06-20, nuit, 1.5 Go). |
| `valide_vague27` | VAGUE 27 — pile / tableaux / numération / bits (2026-06-20, nuit, 1.5 Go). |
| `valide_vague28` | VAGUE 28 — tableaux / unique / stats / numération (2026-06-20, nuit, 1.5 Go). |
| `valide_vague29` | VAGUE 29 — chaînes / numération / tableaux (2026-06-20, nuit, 1.5 Go). |
| `valide_vague30` | VAGUE 30 — tableaux / chiffres / DP-2D / chaînes (2026-06-20, nuit, 1.5 Go). |
| `valide_vague31` | VAGUE 31 — matrice / numération / chiffres / chaînes (2026-06-20, nuit, 1.5 Go). |
| `valide_vague32` | VAGUE 32 — tableaux / grille / chaînes (2026-06-20, nuit, 1.5 Go). |
| `valide_vague33` | VAGUE 33 — tableaux / grille / chaîne / numération (2026-06-20, nuit, 1.5 Go). |
| `valide_vague34` | VAGUE 34 — tableaux / chaînes (2026-06-20, nuit, 1.5 Go). |
| `valide_vague35` | VAGUE 35 — tableaux / numération (2026-06-20, nuit, 1.5 Go). |
| `valide_vague36` | VAGUE 36 — chaînes (2026-06-20, nuit, 1.5 Go). |
| `valide_vague37` | VAGUE 37 — théorie des nombres / numération (2026-06-20, nuit, 1.5 Go). |
| `valide_vague38` | VAGUE 38 — matrice / grille / DP (2026-06-20, nuit, 1.5 Go). |
| `valide_vague39` | VAGUE 39 — ensembles / nombres (2026-06-20, nuit, 1.5 Go). |
| `valide_vague4` | VAGUE 4 — graphes connexité / conversions-numération / str_index (2026-06-19). |
| `valide_vague40` | VAGUE 40 — listes in-place / statistique d'ordre / greedy / chaînes (2026-06-20, reprise post-redémarrage, 1.5 |
| `valide_vague41` | VAGUE 41 — CONFIRMATION (2026-06-20, reprise post-redémarrage, 1.5 Go). |
| `valide_vague42` | VAGUE 42 — PROFONDE (DP/greedy/combinatoire) (2026-06-20, reprise post-redémarrage, 1.5 Go). |
| `valide_vague43` | VAGUE 43 — INTERVALLES (domaine étendu) + MATRICE + TRI-COMPARATEUR (2026-06-20, reprise post-redémarrage, 1.5 |
| `valide_vague44` | VAGUE 44 — GRILLES 2D & GÉOMÉTRIE ENTIÈRE (2026-06-22 nuit, autonomie). |
| `valide_vague45` | VAGUE 45 — ALGORITHMES À PILE (monotone & parsing) (2026-06-22 nuit, autonomie). |
| `valide_vague46` | VAGUE 46 — RECHERCHE AVANCÉE / FENÊTRE / THÉORIE DES NOMBRES (2026-06-22 nuit, autonomie). |
| `valide_vague47` | VAGUE 47 — CLASSIQUES DP (CONFIRMATION, 0 trou) (2026-06-22 nuit, autonomie). |
| `valide_vague48` | VAGUE 48 — GREEDY / HACHAGE / CHAÎNES / BITS (CONFIRMATION, 0 trou) (2026-06-22 nuit, autonomie). |
| `valide_vague49` | VAGUE 49 — CHAÎNES AVANCÉES + MATHS MODULAIRES (2026-06-22 nuit, autonomie). |
| `valide_vague5` | VAGUE 5 — chaînes / théorie des nombres / chiffres / matrices / tableaux (2026-06-19, autonomie). |
| `valide_vague50` | VAGUE 50 — BACKTRACKING & COMPTAGE (2026-06-23 nuit, autonomie). |
| `valide_vague51` | VAGUE 51 — DEUX-POINTEURS / PARTITION DE TABLEAU (2026-06-23 nuit, autonomie). |
| `valide_vague6` | VAGUE 6 — graphes BFS / numérique / matmul / chaînes / pile multi-délimiteurs (2026-06-19, autonomie). |
| `valide_vague7` | VAGUE 7 — graphes dirigés / DP / géométrie point / combinatoire (2026-06-19, autonomie). |
| `valide_vague8` | VAGUE 8 — arbre/grille / théorie nombres itérative / DP / chaînes / géométrie (2026-06-19, autonomie). |
| `valide_vague9` | VAGUE 9 — graphes pondérés / nombres modulaires / DP / encodage / chiffrement (2026-06-19, autonomie). |
| `valide_valeurs_extremes` | VALIDATION des VALEURS EXTRÊMES (valeurs_extremes.py) — jugée par calibration.py. |
| `valide_variational_preferences` | VALIDATION des PRÉFÉRENCES VARIATIONNELLES / MULTIPLIER (variational_preferences.py). |
| `valide_veille` | VALIDE veille.py — accès web souverain, FAUX=0. |
| `valide_veille_corroboration` | VALIDE la boucle web->réalité->fait-store (veille_corroboration) — ADVERSE, FAUX=0. |
| `valide_venn_abers` | VALIDATION du PRÉDICTEUR DE VENN-ABERS (venn_abers.py) — jugé par calibration.py. |
| `valide_villes_coordonnees` | VALIDE l'ingestion coordonnées des LOCALITÉS (Wikidata/QLever P625, portée Q486972) + câblage navigation — ADV |
| `valide_web` | VALIDE web.py — ADVERSE, FAUX=0. |
| `valide_while` | CONTRÔLE GÉNÉRALISÉ (2) — boucle WHILE pilotée par une CONDITION (le `while`, classe gcd). |
| `valide_will_rogers` | VALIDATION du PHÉNOMÈNE DE WILL ROGERS (will_rogers.py). |
| `valide_winner_curse` | VALIDATION de la MALÉDICTION DU VAINQUEUR (winner_curse.py) — jugée par calibration.py. |
| `valide_worldbank_eco` | VALIDE l'ingestion éco/social Banque mondiale (6 relations) + les ponts ia.* — ADVERSE, FAUX=0. |
## Assistant conversationnel — modules récents (câblés au chat)

Ces modules récents implémentent l'assistant conversationnel branché dans `interface/repond.py` (documentés en détail dans CAPABILITIES) :

| Module | Rôle |
|---|---|
| `grammaire_fr` | analyse grammaticale FR (nature, type de phrase, SVO) sur lexique embarqué |
| `formes_verbales` | reconnaissance des formes conjuguées (modèles Bescherelle, 116k formes) |
| `fonction_stats_nl` | routeur stats en langage naturel (~46 fonctions du Palier 2) |
| `explications` | explications de concepts/paradoxes auto-contenus |
| `extrait_pdf` | extraction de texte PDF (Tj/TJ + FlateDecode) |
| `lecteur_document` | interrogation de documents longs (passage + page + sommaire) |
| `ocr` | OCR borné (gabarits + traits + Otsu) du texte imprimé net |
| `apprentissage_patrons` | apprentissage de reformulations + induction de règles de substitution |
| `confiance` | corrections utilisateur (avec source obligatoire) + bannissement de sources |
| `langue` | détection + réponse factuelle multilingue (fr/en/es/de/it/pt) |
| `veille_structure` | recherche structurée (Wikidata/QLever/SPARQL) → fait VÉRIFIÉ + web libre attribué |
| `https_confiance` | sortie TLS fiable (repli ancres épinglées pour le .exe) |
| `telecharge_donnees` | installe la base complète (~80M faits) depuis les Releases |
