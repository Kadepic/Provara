# PARTIE I — Logique, mathématiques et calcul (le nécessaire)
## I.1 — Logique formelle
  - validité d'un raisonnement propositionnel :: B-NEC → tables de vérité, décidable
  - syllogismes et déduction classique :: B-NEC → règles d'inférence vérifiables mécaniquement
  - satisfiabilité d'un système de contraintes borné :: B-NEC → énumération/propagation exacte
  - conséquence en logique du premier ordre (cas décidables) :: B-NEC → fragments décidables
  - conséquence en logique du premier ordre (cas général) :: NB-INDEC → semi-décidable seulement
  - logiques modales (nécessité, possibilité) :: B-NEC → sémantique des mondes possibles fixée
  - logique temporelle (Allen, intervalles) :: B-NEC → algèbre d'intervalles exacte
  - logique trivaluée / paraconsistante :: B-NEC → tables fixées par la définition
  - paradoxes autoréférentiels (menteur) :: NB-INDEC → indécidable par construction
  - théorèmes d'incomplétude (portée) :: B-NEC → résultat prouvé
  - problème de l'arrêt sur machine universelle :: NB-INDEC → indécidable (prouvé)
## I.2 — Arithmétique et théorie des nombres
  - calcul arithmétique exact :: B-NEC → évaluation mécanique (juge AST)
  - primalité d'un entier donné :: B-NEC → test déterministe
  - factorisation d'un entier de taille modérée :: B-NEC → algorithme exact
  - PGCD, PPCM, arithmétique modulaire :: B-NEC → Euclide, exact
  - divisibilité et congruences :: B-NEC → définitions
  - développement décimal d'un rationnel :: B-NEC → division exacte, période calculable
  - irrationalité d'un radical donné :: B-NEC → critère décidable
  - conjecture de Goldbach :: NB-OUV → bornée en principe, preuve manquante
  - conjecture des nombres premiers jumeaux :: NB-OUV
  - hypothèse de Riemann :: NB-OUV
## I.3 — Algèbre
  - identités remarquables et simplification symbolique :: B-NEC → réécriture prouvable
  - résolution d'équation du 1er degré :: B-NEC → forme fermée
  - résolution d'équation du 2nd degré (discriminant) :: B-NEC → forme fermée
  - résolution d'équations de degré 3 et 4 :: B-NEC → formules de Cardan/Ferrari
  - insolubilité par radicaux du degré ≥ 5 :: B-NEC → théorème d'Abel-Ruffini
  - systèmes linéaires (pivot de Gauss) :: B-NEC → algorithme exact
  - déterminant, rang, inverse d'une matrice :: B-NEC → calcul exact
  - valeurs propres d'une matrice donnée :: B-NEC → polynôme caractéristique
  - algèbre de Boole (simplification) :: B-NEC → tables et lois fixées
  - structures de groupe/anneau/corps (vérification d'axiomes) :: B-NEC
## I.4 — Analyse
  - limite d'une suite/fonction usuelle :: B-NEC → définition, calcul
  - dérivée d'une fonction élémentaire :: B-NEC → règles de dérivation
  - primitive/intégrale d'une fonction élémentaire :: B-NEC → tables et méthodes exactes
  - intégrale sans primitive élémentaire (Risch) :: B-NEC → décidable pour les élémentaires
  - développement limité / série de Taylor :: B-NEC → coefficients exacts
  - convergence d'une série donnée :: B-NEC → critères
  - équations différentielles linéaires à coefficients constants :: B-NEC → forme fermée
  - solutions d'équations différentielles non linéaires générales :: NB-OUV → pas de forme fermée générale
## I.5 — Géométrie et topologie
  - périmètres, aires, volumes des figures usuelles :: B-NEC → formules exactes
  - théorème de Pythagore et applications :: B-NEC → calcul exact
  - trigonométrie du triangle (valeurs exactes ou approchées MARQUÉES) :: B-NEC
  - géométrie analytique (droites, cercles, coniques) :: B-NEC → équations exactes
  - géométrie vectorielle (produit scalaire, vectoriel) :: B-NEC
  - transformations affines et isométries :: B-NEC
  - géométries non euclidiennes (cohérence) :: B-NEC → modèles prouvés
  - conjecture de Poincaré (statut) :: B-FAIT → résolue (Perelman, 2003)
  - invariants topologiques d'un objet donné :: B-NEC → calculables sur objets finis
## I.6 — Probabilités et statistiques
  - dénombrement combinatoire :: B-NEC → formules exactes
  - probabilité d'un événement dans un modèle donné :: B-NEC → axiomes de Kolmogorov
  - espérance, variance, moments d'une loi donnée :: B-NEC → définitions
  - théorème de Bayes appliqué à des données :: B-NEC → calcul exact
  - statistiques descriptives d'un jeu de données fourni :: B-NEC → calcul sur les données
  - test d'hypothèse (p-valeur) sur données fournies :: B-NEC → procédure définie
  - intervalle de confiance / conformal prediction :: B-NEC → couverture garantie
  - inférence causale depuis l'observationnel seul :: MIX → calcul borné, identifiabilité conditionnelle
  - paradoxe de Simpson (détection sur données) :: B-NEC → vérifiable
  - biais de sélection / survie / publication (détection) :: B-NEC → diagnostics définis
  - « chance » au sens du sort personnel :: NB-SUBJ
## I.7 — Informatique théorique
  - complexité d'un algorithme donné :: B-NEC → analyse prouvable
  - classes P, NP, NP-complétude d'un problème connu :: B-FAIT → résultats établis
  - P vs NP :: NB-OUV → question ouverte
  - correction d'un programme fourni (spécification donnée) :: B-NEC → preuve/exécution
  - comportement d'un code exécutable fourni :: B-NEC → exécution = juge
  - terminaison d'un programme arbitraire :: NB-INDEC → problème de l'arrêt
  - compressibilité (complexité de Kolmogorov) d'une chaîne :: NB-INDEC → non calculable
  - grammaires formelles et automates (appartenance) :: B-NEC → décidable

# PARTIE II — Matière et énergie (physique fondamentale)
## II.1 — Mécanique classique
  - cinématique moyenne (v = d/t) :: B-PHY → définition, roue compilée
  - cinématique à accélération constante :: B-PHY → équations horaires exactes
  - problème de rencontre / poursuite :: B-PHY → résolution exacte
  - dynamique newtonienne F = m·a :: B-PHY → loi vérifiée, roue
  - poids et pesanteur locale :: B-PHY → P = m·g, roue
  - travail et puissance mécanique :: B-PHY → W = F·d, P = F·v, roues
  - énergie cinétique et potentielle :: B-PHY → formules exactes, roues
  - conservation de l'énergie mécanique (système isolé) :: B-PHY
  - quantité de mouvement et chocs :: B-PHY → conservation, roue p = m·v
  - moment de force et équilibre du levier :: B-PHY → M = F·b, roue
  - moment cinétique et rotation du solide :: B-PHY → lois exactes
  - oscillateur harmonique (période) :: B-PHY → formule exacte
  - pendule simple aux petites oscillations :: B-PHY → approximation DITE
  - problème à trois corps (solution générale) :: NB-OUV → pas de forme fermée
  - frottements réels d'un système décrit :: MIX → lois bornées, coefficients à mesurer
## II.2 — Thermodynamique
  - température, chaleur, capacité thermique :: B-PHY → définitions
  - premier principe (bilan énergétique) :: B-PHY → loi
  - second principe et entropie :: B-PHY → loi
  - rendement de Carnot :: B-PHY → borne théorique exacte
  - COP d'une pompe à chaleur idéale :: B-PHY → formule exacte
  - échangeur : DTLM et surface d'échange :: B-PHY → formules sous hypothèses DITES
  - loi des gaz parfaits :: B-PHY → équation d'état
  - transitions de phase (conditions standard) :: B-FAIT → tables mesurées
  - cohérence thermodynamique d'un dispositif décrit :: B-PHY → principes = juge
  - mouvement perpétuel de 1re/2e espèce :: B-PHY → impossible (prouvé par les principes)
## II.3 — Électromagnétisme
  - loi d'Ohm U = R·I :: B-PHY → roue
  - puissance et énergie électriques :: B-PHY → roues P = U·I, E = P·t
  - autonomie d'une batterie (charge/courant) :: B-PHY → roue t = Q/I
  - énergie d'une batterie (charge × tension) :: B-PHY → roue E = Q·U
  - loi de Coulomb et champ électrostatique :: B-PHY → formules exactes
  - lois de Kirchhoff sur un circuit donné :: B-PHY → système linéaire exact
  - induction (Faraday-Lenz) :: B-PHY → loi
  - équations de Maxwell (conséquences) :: B-PHY → cadre prouvé
  - propagation d'une onde électromagnétique dans le vide :: B-PHY → c constante
## II.4 — Ondes, optique et acoustique
  - relation v = λ·f :: B-PHY → définition
  - réflexion, réfraction (Snell-Descartes) :: B-PHY → loi exacte
  - interférences et diffraction (dispositifs standards) :: B-PHY → formules exactes
  - effet Doppler (source/observateur) :: B-PHY → formule exacte
  - intensité sonore en décibels :: B-CONV → échelle conventionnelle définie
  - seuil d'audibilité d'une personne donnée :: MIX → mécanisme borné, valeur individuelle mesurée
## II.5 — Physique moderne
  - dilatation du temps / contraction des longueurs (relativité restreinte) :: B-PHY → formules exactes
  - équivalence masse-énergie E = m·c² :: B-PHY → roue
  - décroissance radioactive (demi-vie donnée) :: B-PHY → loi exponentielle exacte
  - défaut de masse et énergie de liaison nucléaire :: B-PHY → calcul exact
  - niveaux d'énergie de l'atome d'hydrogène :: B-PHY → formule exacte
  - énergie d'un photon (E = h·ν) :: B-PHY → définition
  - principe d'incertitude (borne) :: B-PHY → inégalité prouvée
  - interprétation de la mécanique quantique :: NB-INDEC → interprétations empiriquement équivalentes
  - gravité quantique / théorie du tout :: NB-OUV
  - nature de la matière noire et de l'énergie noire :: NB-OUV
## II.6 — Fluides
  - masse volumique et densité :: B-PHY → roue ρ = m/V
  - pression hydrostatique et poussée d'Archimède :: B-PHY → formules exactes
  - pression = force / surface :: B-PHY → roue P = F/S
  - conservation du débit (Q = S·v) :: B-PHY → roue
  - volume écoulé (V = Q·t) :: B-PHY → roue
  - théorème de Bernoulli (fluide parfait) :: B-PHY → hypothèses DITES
  - pertes de charge d'un réseau réel :: MIX → mécanisme borné, coefficients empiriques
  - turbulence pleinement développée (prédiction fine) :: NB-OUV
  - aérodynamique d'un profil donné (portance/traînée) :: MIX → lois bornées, coefficients mesurés

# PARTIE III — Chimie et matériaux
## III.1 — Chimie générale
  - masse molaire d'un composé :: B-PHY → table périodique + calcul exact
  - stœchiométrie d'une réaction équilibrée :: B-PHY → conservation des atomes
  - équilibrage d'une équation chimique :: B-NEC → système linéaire exact
  - pH d'une concentration donnée :: B-PHY → définition (-log₁₀)
  - constante d'équilibre et déplacement (Le Chatelier) :: B-PHY → lois
  - oxydoréduction (nombres d'oxydation) :: B-CONV → règles fixées
  - électronégativité et polarité d'une liaison :: B-FAIT → échelle mesurée (Pauling)
  - configuration électronique d'un élément :: B-NEC → règles de remplissage
  - propriétés périodiques (rayon, ionisation) :: B-FAIT → mesures tabulées
## III.2 — Chimie organique et biochimie
  - nomenclature IUPAC d'une molécule donnée :: B-CONV → règles publiées
  - identification d'un composé par sa formule :: B-FAIT → registres (CAS/PubChem)
  - isomérie (dénombrement pour formule brute) :: B-NEC → énumération exacte
  - mécanismes réactionnels canoniques :: B-FAIT → mécanismes établis
  - prédiction de réactivité d'une molécule inédite :: NB-OUV
  - « meilleure » molécule pour un usage ouvert :: NB-OUV → espace chimique non exploré
## III.3 — Matériaux
  - propriétés mécaniques d'un matériau nommé :: B-FAIT → mesures tabulées
  - composition d'un alliage nommé :: B-FAIT → normes/registres
  - conductivité thermique/électrique d'un matériau :: B-FAIT → mesurée
  - dopage et semi-conducteurs (principe) :: B-PHY → mécanisme établi
  - toxicité d'une substance à dose donnée :: MIX → mécanismes bornés, seuils réglementaires conventionnels

# PARTIE IV — La Terre
## IV.1 — Géologie
  - structure interne de la Terre :: B-FAIT → sismologie
  - tectonique des plaques (mouvements mesurés) :: B-FAIT → GPS/paléomagnétisme
  - datation radiométrique d'un échantillon :: B-PHY → loi de décroissance
  - échelle des temps géologiques :: B-CONV → nomenclature ratifiée (ICS)
  - classification d'une roche donnée :: B-CONV → nomenclature pétrographique
  - prédiction de la date d'un séisme :: NB-OUV → pas de mécanisme prédictif fiable
## IV.2 — Hydrosphère et atmosphère
  - cycle de l'eau (mécanismes) :: B-PHY
  - composition de l'atmosphère :: B-FAIT → mesures
  - effet de serre (mécanisme radiatif) :: B-PHY → physique établie
  - météo à quelques jours :: MIX → borné à court terme, chaotique au-delà
  - météo au-delà de deux semaines :: NB-SPEC → horizon de prédictibilité dépassé
  - climat projeté sous scénario d'émissions donné :: MIX → physique bornée, scénario = hypothèse
## IV.3 — Géographie physique
  - relief, sommets, altitudes :: B-FAIT → mesures enregistrées
  - fleuves, longueurs, bassins, embouchures :: B-FAIT
  - superficies des terres émergées et des îles :: B-FAIT
  - coordonnées d'un lieu nommé :: B-FAIT → géodésie
  - distances orthodromiques entre deux lieux :: B-NEC → calcul exact sur le géoïde
  - types de biomes et de climats (classification) :: B-CONV → Köppen et consorts
  - « le plus beau paysage » :: NB-SUBJ

# PARTIE V — La vie
## V.1 — Biologie fondamentale
  - taxonomie (règne, embranchement, classe, ordre, famille, genre, espèce) :: B-FAIT → classifications
  - caractéristiques d'une espèce nommée (habitat, régime, longévité) :: B-FAIT
  - anatomie et physiologie descriptives :: B-FAIT → connaissances établies
  - code génétique (correspondance codon-acide aminé) :: B-CONV → table universelle établie
  - réplication, transcription, traduction (mécanismes) :: B-PHY
  - hérédité mendélienne (croisements) :: B-NEC → calcul probabiliste exact
  - phylogénie d'un clade (arbre) :: MIX → données bornées, topologie parfois débattue
  - origine de la vie :: NB-OUV
## V.2 — Écologie et évolution
  - sélection naturelle (mécanisme) :: B-PHY → mécanisme établi
  - dynamique des populations (modèles donnés) :: B-NEC → équations exactes
  - réseaux trophiques d'un écosystème décrit :: B-FAIT
  - statut de conservation d'une espèce :: B-FAIT → registres (UICN)
  - date d'extinction future d'une espèce :: NB-SPEC
## V.3 — Médecine et santé
  - étiologie des maladies infectieuses courantes :: B-FAIT → agents identifiés
  - pharmacocinétique (demi-vie, posologie standard) :: B-FAIT → études enregistrées
  - efficacité d'un traitement (essais publiés) :: B-FAIT → résultats mesurés, incertitude DITE
  - diagnostic d'un cas individuel :: NB-INDEC → exige examen, hors périmètre
  - « faut-il » tel traitement pour telle personne :: NB-NORM → décision médicale individuelle
  - conscience et expérience subjective (problème difficile) :: NB-OUV
