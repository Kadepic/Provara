# -*- coding: utf-8 -*-
"""COUVERTURE DES SUJETS — le compagnon de `sujets.py` (RECONSTRUIT 2026-07-10, mandat Yohan : « cartographier
réellement tout ce qui existe, séparer ceux qui sont traités de ceux qui ne le sont pas, et parmi les traités :
complets ou non »).

MESURÉ, JAMAIS DÉCLARÉ — c'est tout le principe : un sujet n'est TRAITÉ que si sa PREUVE existe RÉELLEMENT
dans le produit, et la preuve est vérifiée sur le disque à chaque appel :
  • ("gate", f)   -> `tests/f` existe ;
  • ("module", m) -> `src/m.py` existe ;
  • ("roue", nom) -> `nom` est une roue câblée de `pont_grandeurs._ROUES` ;
  • ("store",)    -> le sujet EST une table vérifiée du lecteur (annexe S ; ancrage audité à 100 %) ;
  • ("routage",)  -> sujet NON BORNÉ pris honnêtement par le repli intent-aware + gardes G1-G9 (jamais une
                    réponse inventée : router honnêtement EST le traitement correct du non-borné).
Une preuve DÉCLARÉE mais introuvable rend le sujet NON TRAITÉ et le dit (auto-détection de la dette : c'est
ainsi que `valide_jeux.py` inexistant a été débusqué à l'écriture).

TROIS ÉTATS : TRAITÉ · PARTIEL (mécanisme générique, périmètre incomplet CONNU) · NON TRAITÉ (= le BACKLOG).
`rapport()` est la liste de travail des vagues suivantes — l'équivalent mesuré du « 254/690 » d'origine.
"""
from __future__ import annotations

import os
import re

import sujets as _S

_ICI = os.path.dirname(os.path.abspath(__file__))
_TESTS = os.path.join(os.path.dirname(_ICI), "tests")
# FROZEN (.exe) : les `tests/` ne sont PAS embarqués — une preuve-gate n'y est donc pas VÉRIFIABLE. Ce n'est
# pas une dette (la gate `valide_sujets` la vérifie EN SOURCE à chaque suite) : on le DIT au lieu de le
# masquer ou de mentir (vécu e2e 2026-07-10 : le .exe annonçait « 69 dettes » qui n'existaient pas).
_GEL = bool(getattr(__import__("sys"), "frozen", False)) and not os.path.isdir(_TESTS)

TRAITE, PARTIEL, NON_TRAITE = "TRAITÉ", "PARTIEL", "NON TRAITÉ"

# ── PREUVES des sujets CONCEPTUELS (carte fermée, étendue vague par vague ; 1er motif qui matche gagne) ──
_REGLES: tuple = (
    (r"raisonnement propositionnel|syllogisme|logiques? modale|logique temporelle|logique trivalu",
     "gate", "valide_logique.py", TRAITE),
    # Sondé : backtracking COMPLET (SAT et UNSAT décidés, jamais devinés) + re-vérification de la solution.
    (r"satisfiabilité d'un système|cohérence d'un petit système", "module", "contrainte", TRAITE),
    (r"calcul arithmétique|primalité|PGCD|factorisation|divisibilité|congruence|irrationalité",
     "gate", "valide_fonction.py", TRAITE),
    # DÉCOUPE (2026-07-11) : une seule règle couvrait SIX sujets et les forçait tous en PARTIEL, alors que
    # deux d'entre eux sont pleinement traités. Un regex trop large est une mesure fausse : il masque ce qui
    # est fait ET ce qui ne l'est pas. Chaque sujet a désormais sa règle et son état mesuré.
    (r"résolution d'équation du 1er degré|résolution d'équation du 2nd degré",
     "module", "equations_polynomiales", TRAITE),      # racines exactes + irrationnelles ENCADRÉES (Sturm)
    (r"identités remarquables", "module", "algebre_symbolique", TRAITE),
    (r"systèmes linéaires \(pivot de Gauss\)|déterminant, rang, inverse d'une matrice",
     "module", "algebre_lineaire", TRAITE),             # Gauss exact + Rouché-Capelli ; M·M⁻¹ re-vérifié
    (r"algèbre de Boole \(simplification\)", "module", "simplification_booleenne", TRAITE),  # Quine-McCluskey
    # DÉCOUPE : `calcul_infinitesimal` dérive et intègre EXACTEMENT — mais des POLYNÔMES seulement.
    # « fonction élémentaire » englobe sin/cos/exp/ln et les règles produit/quotient/chaîne : donc PARTIEL,
    # avec le périmètre DIT. Les trois autres sujets ont chacun leur manque propre.
    (r"dérivée d'une fonction élémentaire|primitive/intégrale d'une fonction élémentaire",
     "module", "derivation_symbolique", TRAITE),   # sin/cos/exp/ln + Leibniz, quotient, chaîne
    # Un développement limité SANS borne du reste ne dit rien : `approxime` rend (valeur, borne de Lagrange).
    (r"développement limité", "module", "developpement_limite", TRAITE),
    (r"convergence d'une série donnée", "module", "convergence_series", TRAITE),   # d'Alembert, Cauchy, Leibniz
    (r"équations différentielles linéaires", "module", "edo_lineaires", TRAITE),   # 2e ordre, 3 régimes
    (r"périmètres, aires|Pythagore|géométrie analytique|géométrie vectorielle", "gate", "valide_fonction.py", TRAITE),
    # Le cas SSA est ambigu : ZÉRO, UNE ou DEUX solutions. `resout_triangle` rend la LISTE des triangles.
    (r"trigonométrie", "module", "trigonometrie_triangle", TRAITE),
    # DÉCOUPE : le dénombrement est COMPLET (maths_discretes : binomial, Catalan, dérangements, partitions).
    # `bayes` fait la mise à jour en log-cotes (équivalente au théorème), mais la probabilité CLASSIQUE d'un
    # événement, l'espérance et la variance d'une loi n'existent nulle part.
    (r"dénombrement combinatoire", "module", "maths_discretes", TRAITE),
    (r"probabilité d'un événement dans un modèle donné|espérance, variance, moments",
     "module", "probabilites_elementaires", TRAITE),    # Fraction exacte ; Var = E[X²]−E[X]² re-vérifié
    # `bayes.py` fait la mise à jour en LOG-COTES ; la forme DIRECTE P(A|B) = P(B|A)P(A)/P(B) et la loi des
    # probabilités totales vivent dans `probabilites_elementaires` (exactes en Fraction). Sondé : le piège du
    # taux de base rend 11/122 (= 99/1098), pas 0,99.
    (r"théorème de Bayes appliqué à des données", "module", "probabilites_elementaires", TRAITE),
    (r"statistiques descriptives", "gate", "valide_fonction_stats_nl.py", TRAITE),
    # `conformal` fait de la PRÉDICTION conforme (une observation future) ; le test d'hypothèse et
    # l'intervalle de confiance portent sur un PARAMÈTRE. Deux questions distinctes, deux modules.
    (r"test d'hypothèse|intervalle de confiance", "module", "inference_classique", TRAITE),
    # `causalite` porte le GRAPHE, `simpson` DÉTECTE le renversement ; ni l'un ni l'autre n'ESTIMAIT l'effet.
    # Sondé sur les calculs rénaux (Charig 1986) : ajusté, A = 0,8325 > B = 0,7789, le renversement est corrigé.
    (r"inférence causale|paradoxe de Simpson", "module", "ajustement_causal", TRAITE),
    # Le mécanisme GÉNÉRIQUE du biais de sélection est la COLLISION. Sondé : deux maladies indépendantes
    # (OR = 1) deviennent négativement associées chez les hospitalisés (OR = 9/25).
    (r"biais de sélection", "module", "biais_collision", TRAITE),
    # `algo_analyse` lisait le n·log n du tri fusion dans une table ; `recurrences` le DÉRIVE du théorème maître.
    (r"complexité d'un algorithme|complexité et coût", "module", "recurrences", TRAITE),
    (r"comportement d'un code exécutable|correction d'un programme", "gate", "valide_capacites_chat.py", TRAITE),
    (r"vulnérabilités canoniques", "gate", "valide_audit_code.py", TRAITE),
    # `langages_formels` exigeait une grammaire DÉJÀ en CNF. `grammaires_formelles` convertit (START/TERM/
    # BIN/DEL/UNIT) et VÉRIFIE que le langage engendré est inchangé, puis déterminise les AFN.
    (r"grammaires formelles et automates", "module", "grammaires_formelles", TRAITE),
    # ── VAGUE A (2026-07-10 nuit) : preuves AUDITÉES module par module, gate exécutée VERTE avant câblage.
    #    Les « pièges de nom » débusqués à l'audit (limite.py = bornes physiques, temperature.py =
    #    calibration ML, loi.py = solveur physique, atome.py = contrat épistémique, architecture.py =
    #    architecture INFORMATIQUE, induction_horn.py = induction LOGIQUE) ne sont JAMAIS cités ici.
    (r"théorèmes d'incomplétude", "module", "godel", TRAITE),
    (r"insolubilité par radicaux", "module", "galois", TRAITE),
    (r"valeurs propres d'une matrice", "module", "valeurs_propres", TRAITE),
    (r"transformations affines et isométries", "module", "geometrie2d", TRAITE),
    (r"invariants topologiques", "module", "topologie", TRAITE),
    (r"classes P, NP, NP-complétude", "module", "classes_complexite", TRAITE),
    # ── VAGUE A, 2e lot : briques BÂTIES cette nuit (module + gate adverse + sonde indépendante). ──
    (r"structures de groupe/anneau/corps", "module", "anneaux_corps", TRAITE),
    (r"limite d'une suite/fonction usuelle", "module", "limites_usuelles", TRAITE),
    # ATTENTION au périmètre : le module fait du model-checking sur DOMAINE FINI (fragment décidable).
    # Le sujet « cas général » est SEMI-décidable (Church-Turing) : il ne doit PAS matcher ici, sinon on
    # déclare traité ce qu'aucun algorithme ne termine. Faux corrigé le 2026-07-11.
    (r"conséquence en logique du premier ordre \(cas décidables\)", "module", "logique_premier_ordre", TRAITE),
    (r"développement décimal d'un rationnel", "module", "developpement_decimal", TRAITE),
    (r"résolution d'équations de degré 3 et 4", "module", "equations_polynomiales", TRAITE),
    (r"intégrale sans primitive élémentaire", "module", "integrale_elementaire", TRAITE),
    (r"conjecture de Poincaré", "module", "conjectures_celebres", TRAITE),
    (r"géométries non euclidiennes", "module", "geometrie_hyperbolique", TRAITE),
    (r"cinématique à accélération constante", "module", "cinematique_uniformement_acceleree", TRAITE),
    (r"conservation de l'énergie mécanique", "module", "energie_mecanique", TRAITE),
    (r"moment cinétique et rotation du solide", "module", "rotation_solide", TRAITE),
    (r"température, chaleur, capacité thermique", "module", "thermique", TRAITE),
    (r"lois de Kirchhoff", "module", "circuits_kirchhoff", TRAITE),
    (r"induction \(Faraday-Lenz\)", "module", "induction_em", TRAITE),
    (r"réflexion, réfraction", "module", "optique_geometrique", TRAITE),
    (r"interférences et diffraction", "module", "interferences_diffraction", TRAITE),
    (r"effet Doppler", "module", "effet_doppler", TRAITE),
    (r"niveaux d'énergie de l'atome d'hydrogène", "module", "atome_hydrogene", TRAITE),
    # ── VAGUE B (2026-07-10 nuit) : PARTIES III, IV, V. Gates vertes (1 213 assertions) + sonde
    #    indépendante 29/29 (Pd sans couche 5s · ulcère = H. pylori · omnivore au niveau 3,0 fractionnaire).
    (r"configuration électronique", "module", "configuration_electronique", TRAITE),
    (r"propriétés périodiques", "module", "proprietes_periodiques", TRAITE),
    (r"isomérie \(dénombrement", "module", "isomerie_constitutionnelle", TRAITE),
    (r"propriétés mécaniques d'un matériau", "module", "proprietes_mecaniques_materiaux", TRAITE),
    (r"conductivité thermique/électrique", "module", "conductivite_materiaux", TRAITE),
    (r"tectonique des plaques", "module", "tectonique_plaques", TRAITE),
    (r"échelle des temps géologiques", "module", "temps_geologiques", TRAITE),
    (r"classification d'une roche", "module", "classification_roches", TRAITE),
    (r"cycle de l'eau", "module", "cycle_eau", TRAITE),
    (r"effet de serre", "module", "effet_de_serre", TRAITE),
    (r"types de biomes et de climats", "module", "climats_biomes", TRAITE),
    (r"réplication, transcription, traduction", "module", "expression_genique", TRAITE),
    (r"sélection naturelle", "module", "selection_naturelle", TRAITE),
    (r"réseaux trophiques", "module", "reseau_trophique", TRAITE),
    (r"étiologie des maladies", "module", "etiologie_infectieuse", TRAITE),
    # ── VAGUE C (2026-07-10 nuit) : PARTIES VI à XII. Gates vertes, sonde indépendante.
    (r"métrique et versification", "module", "versification_fr", TRAITE),
    (r"calcul d'intérêts", "module", "finance_actualisation", TRAITE),
    (r"élasticité prix", "module", "elasticite_prix", TRAITE),
    (r"pyramide des âges", "module", "pyramide_ages", TRAITE),
    (r"mobilité sociale", "module", "mobilite_sociale", TRAITE),
    (r"encodage et compression", "module", "compression_sans_perte", TRAITE),
    (r"correction d'erreurs", "module", "codes_correcteurs", TRAITE),
    (r"harmonie et gammes", "module", "musique_gammes", TRAITE),
    (r"colorimétrie", "module", "colorimetrie", TRAITE),
    (r"bilan énergétique d'un système", "module", "bilan_energetique", TRAITE),
    (r"reproductibilité d'un build", "module", "reproductibilite_build", TRAITE),
    (r"archéologie : datation", "module", "datation_radiocarbone", TRAITE),
    (r"calendriers et fuseaux", "module", "calendriers", TRAITE),
    (r"formats de date/nombre", "module", "formats_locaux", TRAITE),
    (r"anatomie et physiologie", "module", "anatomie_systemes", TRAITE),
    # physique (modules exacts, gates vertes)
    (r"oscillateur harmonique|pendule simple|pression hydrostatique et poussée d'Archimède",
     "module", "mecanique", TRAITE),
    (r"transitions de phase", "module", "etats_matiere", TRAITE),
    (r"équations de Maxwell|propagation d'une onde électromagnétique", "module", "maxwell", TRAITE),
    (r"intensité sonore en décibels", "module", "audiologie", TRAITE),
    (r"dilatation du temps / contraction des longueurs", "module", "relativite_restreinte", TRAITE),
    (r"défaut de masse et énergie de liaison", "module", "nucleosynthese", TRAITE),
    (r"principe d'incertitude", "module", "quantique", TRAITE),
    (r"théorème de Bernoulli", "module", "hydraulique", TRAITE),
    # chimie / matériaux
    (r"constante d'équilibre et déplacement", "module", "equilibre_chimique", TRAITE),
    (r"oxydoréduction", "module", "redox", TRAITE),
    (r"électronégativité et polarité", "module", "liaisons_chimiques", TRAITE),
    (r"mécanismes réactionnels canoniques", "module", "mecanismes_reactionnels", TRAITE),
    (r"dopage et semi-conducteurs", "module", "semiconducteurs", TRAITE),
    # PARTIELS ASSUMÉS, périmètre DIT (jamais présenté comme complet) :
    #   IUPAC = composés binaires + catalogue (pas la nomenclature organique générale) ;
    #   alliages = catalogue de 4 alliages (lookup-ou-HORS) ; normes = hiérarchie FRANÇAISE seule.
    # PARTIEL ASSUMÉ, périmètre DIT : chaînes linéaires monofonctionnelles (+ composés binaires via
    # `nomenclature_chimique`). Ramifiées et cycliques -> abstention. `identifie('C3H6O')` rend l'AMBIGUÏTÉ
    # (propanal ET propanone) : rendre un composé unique serait un faux.
    (r"nomenclature IUPAC|identification d'un composé par sa formule",
     "module", "nomenclature_organique", PARTIEL),
    (r"composition d'un alliage nommé", "module", "alliages", PARTIEL),
    (r"hiérarchie des normes d'un pays", "module", "hierarchie_normes", PARTIEL),
    # vivant / société / arts
    (r"code génétique", "module", "genetique", TRAITE),
    (r"comptabilité d'une entité", "module", "comptabilite", TRAITE),
    (r"perspective géométrique", "module", "geometrie_projective", TRAITE),
    (r"validité d'un argument philosophique", "module", "preuve_propositionnelle", TRAITE),
    # physique : les roues (preuve = câblage réel dans _ROUES)
    (r"cinématique moyenne", "roue", "cinématique moyenne", TRAITE),
    (r"dynamique newtonienne", "roue", "force (Newton)", TRAITE),
    (r"poids et pesanteur", "roue", "poids", TRAITE),
    (r"travail et puissance mécanique", "roue", "travail", TRAITE),
    (r"énergie cinétique et potentielle", "roue", "énergie cinétique", TRAITE),
    (r"quantité de mouvement", "roue", "quantité de mouvement", TRAITE),
    (r"moment de force", "roue", "moment de force", TRAITE),
    (r"masse volumique|pression = force|conservation du débit|volume écoulé",
     "roue", "masse volumique", TRAITE),
    (r"loi d'Ohm|puissance et énergie électriques", "roue", "électrique", TRAITE),
    (r"autonomie d'une batterie", "roue", "autonomie", TRAITE),
    (r"énergie d'une batterie", "roue", "batterie", TRAITE),
    (r"équivalence masse-énergie", "roue", "énergie de masse", TRAITE),
    (r"consommation de carburant", "roue", "consommation carburant", TRAITE),
    (r"production d'une centrale", "roue", "énergie", TRAITE),
    (r"problème de rencontre", "gate", "valide_cinematique_nl.py", TRAITE),
    (r"échangeur : DTLM|DTLM et surface", "gate", "valide_pont_grandeurs.py", TRAITE),
    (r"rendement de Carnot|COP d'une pompe|loi des gaz parfaits|loi de Coulomb|"
     r"décroissance radioactive|énergie d'un photon|relation v = λ", "module", "physique", TRAITE),
    (r"cohérence thermodynamique|mouvement perpétuel", "module", "coherence_physique", TRAITE),
    # `coherence_physique` JUGE des dispositifs ; `entropie_thermo` ne fait que l'isotherme réversible.
    # `thermodynamique_principes` calcule : ΔU = Q − W, travaux, et l'entropie des processus NON isothermes
    # (m·c·ln(T2/T1), en KELVIN — la même formule en °C donnerait un faux d'un facteur 5).
    (r"premier principe|second principe et entropie", "module", "thermodynamique_principes", TRAITE),
    (r"masse molaire|stœchiométrie|équilibrage d'une équation chimique|pH d'une concentration",
     "module", "chimie", TRAITE),
    (r"aérodynamique", "module", "aerodynamique", PARTIEL),
    # PREUVE FAUSSE CORRIGÉE (2026-07-10 nuit) : ce sujet citait `architecture.py`, qui est l'architecture
    # des ORDINATEURS (conversions binaires, complément à deux) — un piège de nom. Le vrai module de
    # résistance des matériaux est `structures_genie` ; il calcule contrainte/flèche/flambage mais ne
    # DIMENSIONNE pas encore (pas de comparaison à une contrainte admissible). Donc PARTIEL, honnêtement.
    # `structures_genie` CALCULE ; `dimensionnement_structure` VÉRIFIE et DIMENSIONNE contre la contrainte
    # admissible (borne BASSE de l'intervalle : dimensionner sur la borne haute serait dangereux).
    (r"dimensionnement d'une structure", "module", "dimensionnement_structure", TRAITE),
    # faits : les gates du lecteur
    (r"taxonomie \(|caractéristiques d'une espèce|statut de conservation", "gate", "valide_lecteur_t4.py", TRAITE),
    (r"relief, sommets|fleuves, longueurs|superficies des terres|coordonnées d'un lieu|"
     r"population, natalité|géographie", "gate", "valide_lecteur.py", TRAITE),
    (r"distances orthodromiques", "gate", "valide_coordonnees.py", TRAITE),
    (r"astronomie descriptive|structure interne de la Terre|composition de l'atmosphère",
     "gate", "valide_ancres_types.py", TRAITE),
    # `physique` n'a que la décroissance DIRECTE ; la datation est le problème INVERSE, bâti le 2026-07-10.
    (r"datation radiométrique", "module", "datation_radiocarbone", TRAITE),
    (r"mécanique céleste", "module", "physique", PARTIEL),          # orbites circulaires seules
    (r"datation d'un événement|chronologie et successions|dirigeants par pays|régime politique|"
     r"résultats d'élections passées", "gate", "valide_lecteur_t8.py", TRAITE),
    (r"biographies", "gate", "valide_lecteur_t6.py", TRAITE),
    (r"auteur, compositeur|année de création d'une œuvre|dimensions, durée, support",
     "gate", "valide_lecteur_t5.py", TRAITE),
    (r"résultats sportifs|records du monde", "gate", "valide_lecteur_t10.py", TRAITE),
    (r"doctrines et textes|généalogies mythologiques|écoles philosophiques",
     "gate", "valide_lecteur_t12.py", TRAITE),
    (r"orthographe|conjugaison|accord du participe|genre grammatical|grammaire et accords",
     "gate", "valide_grammaire_fr.py", TRAITE),
    (r"sens lexical|synonymes|étymologie", "gate", "valide_lecteur_t9.py", TRAITE),
    (r"traduction d'un mot|traduction de mots", "gate", "valide_traduction.py", TRAITE),
    (r"conversions d'unités|unités du système international|heure et date locales",
     "gate", "valide_capacites_chat.py", TRAITE),
    (r"météo observée", "gate", "valide_capacites_chat.py", TRAITE),
    # LANGUES (tables ingérées cette nuit). « parenté » = la généalogie complète : Wikidata ne la porte PAS
    # (« langue d'oïl » n'a aucun ancêtre typé) -> le sujet reste PARTIEL, la famille immédiate est acquise.
    # Wikidata ne porte pas la généalogie (mesuré) ; `familles_langues` la catalogue.
    # « turc » -> turcique, jamais « altaïque » (regroupement contesté) ; le basque est un ISOLAT.
    (r"famille et parenté d'une langue", "module", "familles_langues", TRAITE),
    (r"nombre de locuteurs d'une langue", "table", "locuteurs_langue", TRAITE),
    # Ce sujet était classé « bloqué sur un corpus externe ». Il ne l'était pas : Our World in Data publie
    # la part de l'électricité par source, par PAYS et par ANNÉE (données Ember). 5 907 couples ingérés ;
    # les agrégats (« World ») et les années à couverture partielle (« Algérie 1985 : somme = 5 % ») rejetés.
    (r"mix électrique d'un pays/année", "table", "mix_electrique", TRAITE),
    # Deux autres sujets crus « bloqués sur un corpus externe » : les cadres CITE (UNESCO) et CEC (UE) sont
    # PUBLIÉS ; les conciles, édits et schismes sont DATÉS par des sources contemporaines. Ce qui est
    # réellement contesté (naissance de Jésus, vie du Bouddha) est rendu comme FOURCHETTE, jamais comme date.
    (r"équivalences internationales de diplômes", "module", "equivalences_diplomes", TRAITE),
    (r"histoire et datation des faits religieux", "module", "chronologie_religieuse", TRAITE),
    # ANNEXE T — DÉCOUPE (2026-07-11). `bibliotheconomie` porte les 10 classes Dewey (complet) et l'ISBN
    # (1 des 4 codes normalisés cités). `nomenclatures` ajoute ISCO-08, les divisions Dewey du 500 et la
    # NACE. Les cinq classifications CITÉES mais non ingérées (MSC, ACM, CIM-11, ROME) restent PARTIELLES :
    # on connaît leur éditeur et leur nature, pas leur contenu — et `classes()` y lève ValueError.
    (r"classe Dewey", "module", "bibliotheconomie", TRAITE),
    (r"division Dewey", "module", "nomenclatures", TRAITE),
    (r"grand groupe ISCO", "module", "nomenclatures", TRAITE),
    (r"structure de classification", "module", "nomenclatures", PARTIEL),
    # PARTIEL ASSUMÉ, périmètre DIT : l'ISBN est complet (algorithmique, 10 et 13) ; l'ISO 4217 embarque
    # 25 monnaies, les indicatifs 23 pays, les plaques la France seule. Hors table -> abstention, jamais une
    # devinette. Même standard que `alliages` : un catalogue étroit se déclare étroit.
    (r"codes normalisés", "module", "codes_normalises", PARTIEL),
    # « coup optimal » : minimax générique sur tout jeu FINI à information parfaite -> TRAITÉ.
    # « règles d'un jeu institué (échecs, go, cartes) » : le go et les cartes ne sont pas au catalogue,
    # et le module REFUSE de jouer aux échecs -> PARTIEL, périmètre dit.
    (r"coup optimal", "module", "jeux_institues", TRAITE),
    (r"règles d'un jeu institué", "module", "jeux_institues", PARTIEL),
    # PREUVE MAL DIRIGÉE : `cycles_economiques` est un CATALOGUE de phases, il ne calcule rien. Les formules
    # exactes vivent dans `inflation.py`, `pib.py`, `chomage.py`. Sondé : IPC 100->110 = +10 %, chômage 10 %.
    (r"inflation mesurée sur une période", "module", "inflation", TRAITE),
    (r"PIB, chômage, balance commerciale", "module", "pib", TRAITE),
    (r"calcul d'intérêts", "aucun", None, NON_TRAITE),
    (r"mode de scrutin et paradoxes", "module", "choix_social", TRAITE),
    # L'entropie d'une SOURCE n'est pas celle d'une distribution donnée : estimation biaisée, taux d'entropie
    # d'une chaîne de Markov (la mémoire réduit l'incertitude : 0,469 bit au lieu de 1).
    (r"entropie d'une source", "module", "entropie_source", TRAITE),
    (r"encodage et compression|correction d'erreurs", "aucun", None, NON_TRAITE),
    # Modèle à un compartiment, ordre 1. Refuse l'éthanol et la phénytoïne (cinétique saturable).
    (r"pharmacocinétique", "module", "pharmacocinetique", TRAITE),
    # RR / ARR / NNT / OR sont EXACTS depuis les effectifs d'un essai publié : c'est le traitement correct
    # du sujet (le module calcule, l'essai fournit les nombres). Sondé à la main : RR=0,5 · ARR=0,10 · NNT=10.
    (r"efficacité d'un traitement", "module", "essais_cliniques", TRAITE),
    # Ce sujet citait jadis `bioinfo.py` (séquences ADN) : preuve FAUSSE, corrigée le 2026-07-10.
    # Les deux vrais modules ont été bâtis le 2026-07-11, chacun avec sa gate à ancres non circulaires.
    (r"hérédité mendélienne", "module", "heredite_mendelienne", TRAITE),
    (r"dynamique des populations", "module", "dynamique_populations", TRAITE),
    # `recettes` abstenait sur tout ingrédient autre que l'eau. Les masses volumiques APPARENTES sont
    # rendues avec leur incertitude : une tasse de farine tassée pèse 30 % de plus qu'une tasse aérée.
    (r"calcul de recette", "module", "densites_ingredients", TRAITE),
    (r"préférences personnelles de l'utilisateur", "gate", "valide_faits_conversation.py", TRAITE),
)
_REGLES_C = tuple((re.compile(m, re.I), g, r, e) for m, g, r, e in _REGLES)

# ── AXES des annexes AUTO — FERMETURE ATOMIQUE (règle Yohan, 2026-07-10 nuit) ────────────────────────────────
# AVANT : l'état était décidé par l'AXE et appliqué en bloc à 8 238 métiers. C'était une DÉCLARATION.
# MAINTENANT : l'état est décidé PAR ENTITÉ, par LOOKUP réel dans la table ingérée. Un métier n'est TRAITÉ
# que si SON libellé est présent dans une table du store. Les métiers absents restent NON TRAITÉS et le
# DISENT, nommément. Jamais « l'axe est couvert ». Jamais un échantillon présenté comme la couverture.
#
# Trois modes :
#   "routage" — sujet NON BORNÉ : router honnêtement EST le traitement correct (abstention actionnable) ;
#   "lookup"  — sujet BORNÉ : TRAITÉ ssi l'entité est dans l'une des tables citées (union) ;
#   "aucun"   — aucune source ingérée à ce jour : NON TRAITÉ, avec la raison MESURÉE.
_AXES_M = (
    (re.compile(r"est-il fait pour moi", re.I), "routage", (),
     "routage honnête (NB-SUBJ : l'utilisateur est la seule source)"),
    (re.compile(r"questions ouvertes du domaine", re.I), "routage", (),
     "routage honnête (NB-OUV : abstention dite)"),
    (re.compile(r"définition et périmètre", re.I), "lookup",
     ("definition_esco_metier", "definition_metier", "surclasse_metier"),
     "description ESCO, description Wikidata, ou sur-classe P279 attestée"),
    # MIX assumé : O*NET codifie l'outillage du marché US par occupation SOC (granularité dite dans la
    # valeur). P2283 reste rejeté (« soliste -> solo ») ; l'outillage réel n'est borné par aucun référentiel.
    (re.compile(r"outils, machines", re.I), "lookup_partiel", ("outil_technologie_soc_metier",),
     "part CODIFIÉE fermée par O*NET (catégories par occupation SOC, marché US) ; le reste non couvert (sujet MIX)"),
    # MIX assumé : ESCO codifie la part TRANSMISSIBLE PAR TEXTE du savoir-faire (compétences essentielles
    # de type `skill`). Le TOUR DE MAIN tacite n'y est pas et ne peut pas y être. Donc PARTIEL, jamais TRAITÉ.
    (re.compile(r"gestes et savoir-faire", re.I), "lookup_partiel", ("geste_metier",),
     "part CODIFIÉE fermée par ESCO ; le tour de main tacite reste non borné (le sujet est MIX)"),
    # MIX assumé : REGPROF (Commission, directive 2005/36/CE) et ESCO couvrent la réglementation d'ACCÈS
    # à la profession ; les normes TECHNIQUES du métier (ISO/AFNOR, contenu payant) restent non couvertes.
    (re.compile(r"normes, réglementation", re.I), "lookup_partiel",
     ("profession_reglementee_metier", "reglementation_metier"),
     "réglementation d'ACCÈS fermée par REGPROF/ESCO ; les normes techniques restent non couvertes (sujet MIX)"),
    # MIX assumé : le SOII mesure les taux d'incidence US par occupation SOC (granularité dite). La
    # PRÉVENTION n'est pas une statistique, et la part française (INRS) reste sans table structurée.
    (re.compile(r"risques professionnels", re.I), "lookup_partiel", ("risque_professionnel_soc_metier",),
     "part MESURÉE fermée par BLS SOII (taux par occupation SOC, États-Unis) ; prévention et part FR non couvertes (sujet MIX)"),
    # MIX assumé : le RNCP ferme la part FRANÇAISE (certifications actives sous le code ROME du métier,
    # granularité CODE dite dans la valeur — cf. ingere_rome_rncp). La formation varie par PAYS et par
    # ANNÉE (la PARTIE VI le dit : « programmes et diplômes officiels »). Donc PARTIEL, jamais TRAITÉ.
    (re.compile(r"formation, diplômes", re.I), "lookup_partiel", ("certification_rncp_metier",),
     "part FRANÇAISE fermée par RNCP×ROME ; les autres systèmes nationaux restent non couverts (sujet MIX)"),
    # MIX assumé : BLS OEWS ferme la part ÉTATS-UNIS (vraies MÉDIANES, par occupation SOC — granularité
    # dite dans la valeur). La rémunération des autres pays (dont la France) reste non couverte.
    (re.compile(r"rémunération médiane", re.I), "lookup_partiel", ("salaire_median_soc_us_metier",),
     "part ÉTATS-UNIS fermée par BLS OEWS (médianes par occupation SOC) ; autres pays non couverts (sujet MIX)"),
    (re.compile(r"résultats établis du domaine", re.I), "aucun", (), "corpus de domaine non ingéré"),
)

_DOSSIER_STORE = os.environ.get(
    "LECTEUR_DATASETS_DIR", os.path.join(os.path.expanduser("~"), ".verax", "datasets", "lecteur"))
_CACHE_CLES: dict = {}


def _cles(table: str):
    """Les entités présentes dans une table du store, en flux (stdlib pure). None si la table n'existe pas.

    C'est le LOOKUP qui prouve : « ce métier-ci est traité » — pas « cet axe est couvert »."""
    if table in _CACHE_CLES:
        return _CACHE_CLES[table]
    chemin = os.path.join(_DOSSIER_STORE, table + ".jsonl")
    if not os.path.exists(chemin):
        _CACHE_CLES[table] = None
        return None
    vus = set()
    try:
        with open(chemin, encoding="utf-8") as f:
            for ligne in f:
                if ligne.startswith('{"_relation"'):
                    continue
                d = ligne.find('"entite":')
                if d < 0:
                    continue
                deb = ligne.find('"', d + 9)
                fin = ligne.find('"', deb + 1)
                while fin > 0 and ligne[fin - 1] == "\\":
                    fin = ligne.find('"', fin + 1)
                if deb > 0 and fin > deb:
                    vus.add(ligne[deb + 1:fin].encode().decode("unicode_escape")
                            if "\\" in ligne[deb + 1:fin] else ligne[deb + 1:fin])
    except OSError:
        _CACHE_CLES[table] = None
        return None
    _CACHE_CLES[table] = vus
    return vus


def _entite_annexe(sujet) -> str:
    """L'ENTITÉ d'un sujet d'annexe auto : le métier, ou le domaine. Les axes ne contiennent pas « — »."""
    lib = sujet.libelle
    if sujet.partie.startswith("ANNEXE D"):
        g, d = lib.find("«"), lib.rfind("»")
        if 0 <= g < d:
            return lib[g + 1:d].strip()
    return lib.rsplit(" — ", 1)[0].strip()


def _preuve_existe(genre: str, ref) -> bool:
    if genre == "aucun":                                  # NON TRAITÉ assumé (déclaré tel quel, pas une dette)
        return True
    if ref is None:
        return False
    if genre == "gate":
        if _GEL:
            return True                                   # non vérifiable ici ; vérifiée en source par la gate
        return os.path.exists(os.path.join(_TESTS, ref))
    if genre == "module":
        return os.path.exists(os.path.join(_ICI, ref + ".py"))
    if genre == "table":                                  # une table INGÉRÉE du store, interrogeable par ia.donnee
        return _cles(ref) is not None
    if genre == "roue":
        try:
            import pont_grandeurs as _P
            return any(r["nom"] == ref for r in _P._ROUES)
        except Exception:
            return False
    return True


def etat(sujet) -> tuple:
    """(état, preuve) d'un sujet — l'état TRAITÉ exige une preuve qui EXISTE réellement sur le disque."""
    partie = sujet.partie
    if partie.startswith("ANNEXE S"):
        return (TRAITE, "table vérifiée du store (ancrage audité 1371/1371)")
    if partie.startswith(("ANNEXE M", "ANNEXE D")):
        for rx, mode, tables, raison in _AXES_M:
            if not rx.search(sujet.libelle):
                continue
            if mode == "routage":
                return (TRAITE, raison)
            if mode == "aucun":
                return (NON_TRAITE, raison)
            # modes "lookup" / "lookup_partiel" : FERMETURE ATOMIQUE — c'est CETTE entité qui est vérifiée,
            # jamais l'axe. « lookup_partiel » = la source ne couvre qu'une PART du sujet (cas MIX).
            trouve = TRAITE if mode == "lookup" else PARTIEL
            entite = _entite_annexe(sujet)
            presentes = [t for t in tables if _cles(t) is not None]
            if not presentes:
                return (NON_TRAITE, "table(s) %s absente(s) du store" % ", ".join(tables))
            for t in presentes:
                if entite in _cles(t):
                    return (trouve, "%s : « %s » vérifié par lookup%s"
                            % (t, entite, "" if trouve == TRAITE else " (part codifiée seule ; %s)" % raison))
            return (NON_TRAITE, "« %s » absent de %s (entité non couverte)" % (entite, ", ".join(presentes)))
        return (NON_TRAITE, "axe non classé")
    for rx, genre, ref, prevu in _REGLES_C:
        if not rx.search(sujet.libelle):
            continue
        if not _preuve_existe(genre, ref):
            if genre == "table":
                # Une TABLE est une DONNÉE, pas du code. Son absence d'un store donné (l'échantillon
                # embarqué, par exemple) n'est PAS une dette : c'est un fait sur ce store, et on le dit.
                # Confondre les deux ferait rougir la suite pour une base volontairement allégée.
                return (NON_TRAITE, "table « %s » absente de ce store (donnée non embarquée ici)" % ref)
            return (NON_TRAITE, "preuve DÉCLARÉE INTROUVABLE (%s %s) — dette détectée" % (genre, ref))
        if genre == "aucun":
            return (NON_TRAITE, "aucun mécanisme dédié (backlog assumé)")
        if genre == "gate" and _GEL:
            return (prevu, "gate %s (vérifiée en source ; tests non embarqués dans le binaire)" % ref)
        return (prevu, "%s : %s" % (genre, ref))
    if sujet.non_borne or sujet.code in _S.FRONTIERE:
        return (TRAITE, "routage honnête : repli intent-aware + gardes G1-G9 (jamais une réponse inventée)")
    if sujet.mixte:
        return (PARTIEL, "part bornée servie par les mécanismes généraux ; séparation à durcir")
    return (NON_TRAITE, "aucun mécanisme dédié (backlog)")


def rapport(tous=None) -> dict:
    """Mesure complète : totaux, ventilation par état, et BACKLOG (la liste de travail des vagues suivantes)."""
    tous = tous if tous is not None else _S.charge_tout()
    out = {"total": len(tous), TRAITE: 0, PARTIEL: 0, NON_TRAITE: 0,
           "par_partie": {}, "backlog": [], "dettes": []}
    for s in tous:
        e, p = etat(s)
        out[e] += 1
        cle = s.partie.split("—")[0].strip() or "(sans partie)"
        d = out["par_partie"].setdefault(cle, {TRAITE: 0, PARTIEL: 0, NON_TRAITE: 0})
        d[e] += 1
        if e == NON_TRAITE:
            out["backlog"].append((s.libelle, cle, p))
            if "DÉCLARÉE INTROUVABLE" in p:
                out["dettes"].append((s.libelle, p))
    return out


if __name__ == "__main__":
    r = rapport()
    print("%d sujets : %d traités · %d partiels · %d NON traités"
          % (r["total"], r[TRAITE], r[PARTIEL], r[NON_TRAITE]))
    print("\nPar partie :")
    for partie, d in sorted(r["par_partie"].items()):
        print("  %-28s traités %6d · partiels %5d · non traités %6d"
              % (partie[:28], d[TRAITE], d[PARTIEL], d[NON_TRAITE]))
    if r["dettes"]:
        print("\nDETTES (preuve déclarée introuvable) :")
        for lib, p in r["dettes"][:10]:
            print("  ·", lib, "->", p)
    print("\nBacklog conceptuel (hors annexes auto), 25 premiers :")
    n = 0
    for lib, partie, p in r["backlog"]:
        if partie.startswith("ANNEXE"):
            continue
        print("  ·", lib, "(%s)" % partie)
        n += 1
        if n >= 25:
            break
