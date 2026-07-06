# Provara — Catalogue des capacités

> Panorama thématique des capacités de Provara, **tiré des docstrings du code** (rien inventé).
> Pour la liste exhaustive, module par module, voir [`INVENTORY.md`](INVENTORY.md).

## Géographie & cartographie

Cette famille de capacités permet de **calculer, sur des bases exactes, les grandeurs de la géographie et des sciences de la Terre** : lire et convertir une carte, se positionner et mesurer des distances sur le globe, quantifier les écoulements et les cycles de la surface terrestre, la mécanique des sols, les indicateurs de peuplement, et ingérer des faits géographiques/astronomiques réels. Dans tous les cas le mécanisme employé est une **identité de définition ou un théorème établi**, jamais une corrélation ou une valeur devinée : la réponse est entièrement déterminée par les entrées observées, et le module s'abstient (erreur) plutôt que de rendre un nombre absurde.

### Cartographie & géomatique

Le module `cartographie` couvre les calculs exacts liés à une carte, à partir de conventions établies (échelle 1:N, 1 pouce = 2,54 cm exactement, 1° = 60′ = 3600″) :

- **Échelle** : passage carte ↔ terrain (`echelle_distance_reelle`, `distance_carte`) selon *distance réelle = distance carte × N*.
- **Résolution au sol** d'une carte numérisée (`resolution_au_sol`, `resolution_au_sol_depuis_dpi`), y compris depuis une numérisation en `dpi`.
- **Coordonnées** : conversion sexagésimale (DMS) → décimale (DD), et conversions d'unités de longueur (`cm_en_m`, `cm_en_km`).

```python
cartographie.conversion_dms_dd(48, 51, 12)   # 48°51'12" -> 48.8533... °
```

Le module refuse une échelle ≤ 0, des minutes/secondes hors [0, 60) ou des degrés non entiers en DMS (jamais une coordonnée « corrigée » en douce).

### Navigation & géométrie du globe

Deux modules traitent le positionnement et la mesure sur une sphère.

- `navigation` calcule la **distance orthodromique** (grand cercle) par la formule de haversine (rayon terrestre R = 6371 km) et le **cap initial** (azimut de départ). Fonctions pures, sortie à 6 chiffres significatifs ; ancre documentée du validateur : Paris→Londres ≈ 344 km.

  ```python
  navigation.distance_orthodromique(lat1, lon1, lat2, lon2)  # km, grand cercle
  navigation.cap_initial(lat1, lon1, lat2, lon2)             # azimut vrai dans [0, 360[
  ```

- `geometries_non_euclidiennes` fournit la **géométrie sphérique** (courbure positive constante) : courbure de Gauss K = 1/R², excès sphérique, somme des angles et aire d'un triangle géodésique (théorème de Girard, A = R²·(Σ angles − π)).

  ```python
  geometries_non_euclidiennes.courbure_gauss_sphere(R)   # K = 1/R²
  ```

Les entrées invalides (latitude hors [−90, 90], longitude hors [−180, 180], rayon ≤ 0, angle hors ]0, π[) lèvent une erreur : abstention structurelle, jamais un faux positif.

### Sciences de la Terre & physique de l'environnement

Trois modules quantifient des processus de la surface et du sous-sol par des formules établies (sortie à 6 chiffres significatifs, abstention sur domaine invalide).

- `hydrologie` — eaux continentales : débit par continuité (Q = A·v), méthode rationnelle, vitesse d'écoulement de Manning, temps de concentration de Kirpich.

  ```python
  hydrologie.debit(section_A, vitesse_v)   # Q = A · v (m³/s)
  ```

- `cycles_biogeochimiques` — bilans de réservoir : temps de résidence τ = M/Φ, bilan stationnaire (entrée = sortie), et catalogue **sourcé** des 4 grands cycles (carbone, azote, eau, phosphore). Hors de ces cycles connus, le module s'abstient.

- `geotechnique` — mécanique des sols : contrainte verticale (σ = γ·z), contrainte effective de Terzaghi (σ' = σ − u), coefficient de poussée active de Rankine (Ka = tan²(45° − φ/2)) et poussée sur un mur.

  ```python
  geotechnique.coefficient_poussee_active(30)   # Rankine, φ=30° -> Ka = 1/3
  ```

### Géographie humaine (peuplement)

Le module `demographie` implémente les **définitions démographiques standard** (INED / ONU) sans jamais coder en dur une valeur-pays : taux d'accroissement naturel, densité de population, temps de doublement (règle des 70), taux de dépendance, indice synthétique de fécondité. Le résultat n'est fonction que des comptages et indices fournis.

```python
demographie.densite_population(1_000_000, 500)   # -> 2000 hab/km²
```

### Ingestion de faits géographiques réels

Le script `_ingere_astre_relief_t1` alimente la base à partir de sources réelles : il relie chaque relief de surface (cratère, mont, mer, vallis…) au **corps céleste réel** sur lequel il se trouve (Wikidata P376). La garantie FAUX=0 y est explicite : un *closed-set* des corps réels du système solaire écarte toute contamination fictive (Krypton, Naboo, Coruscant…), la relation est traitée comme fonctionnelle (un relief associé à plusieurs corps distincts → écarté), et des ancres vérité-terrain (tycho → Lune, olympus mons → Mars) sont vérifiées.

### Garantie commune

Tous ces modules partagent la posture **FAUX=0** : le mécanisme est une identité de définition ou un théorème exact, les seules données employées sont des conventions ou des faits sourcés certains, la sortie est arrondie à une précision honnête (6 ou 10 chiffres significatifs) et — invariant décisif — un faux positif est interdit. Face à une entrée hors domaine ou à un cas inconnu, le module **s'abstient** en levant une erreur plutôt que d'inventer une valeur.

---

## Économie & démographie

Cette famille de capacités réunit deux choses complémentaires : d'une part le **calcul exact d'indicateurs économiques et de dynamiques de populations** (marché du travail, cycle des affaires, chaînes trophiques, dynamique proies/prédateurs), d'autre part l'**outillage statistique nécessaire pour tirer des conclusions justes à partir d'un échantillon** (correction des biais d'échantillonnage, estimation calibrée, décision sous incertitude). Le fil conducteur est le même partout : les modules n'inventent jamais une valeur-pays ni une donnée conjoncturelle ; ils implémentent uniquement le *mécanisme* (l'identité comptable, la formule, la règle établie) et **s'abstiennent** (levée d'erreur ou verdict d'abstention) dès que l'entrée sort de leur domaine de validité.

### Économie appliquée : travail et conjoncture

**`chomage`** applique les définitions normatives du BIT (reprises par Eurostat / INSEE / OIT). Chaque indicateur est un ratio arithmétique exact entre des effectifs de personnes observés : `population_active` (identité comptable actifs occupés + chômeurs), `taux_chomage` (chômeurs rapportés à la population active, et non à la population totale), `taux_activite` et `taux_emploi` (rapportés à la population en âge de travailler). L'abstention est structurelle : population active nulle, effectif négatif, ou taux mathématiquement > 100 % (par ex. plus de chômeurs que d'actifs) lèvent une erreur au lieu de produire un chiffre faux.

```python
chomage.taux_chomage(2_500_000, 25_000_000)   # → 10.0  (en %)
```

**`cycles_economiques`** restitue la structure *établie* du cycle des affaires (consensus macroéconomique, NBER, Conference Board), sans jamais dater ni chiffrer une conjoncture. Il expose les quatre phases canoniques (expansion → sommet/pic → récession → creux/dépression) et leur enchaînement, la règle technique de la récession (deux trimestres consécutifs de baisse du PIB réel, explicitement distinguée de la datation officielle multicritère), et la classification des indicateurs conjoncturels (avancé / coïncident / retardé). Tout libellé hors catalogue ou ambigu déclenche l'abstention.

```python
cycles_economiques.phase_suivante("expansion")                 # → "sommet/pic"
cycles_economiques.est_recession_technique([-0.2, -0.4, 0.1])  # → True
```

### Dynamique des populations et écosystèmes

**`ecologie`** traite les populations non humaines par des lois écologiques exactes. Deux mécanismes : le transfert d'énergie trophique (règle des 10 % de Lindeman, `energie_niveau` / `efficacite_ecologique`) et le modèle proie–prédateur de Lotka–Volterra, dont il fournit les dérivées instantanées (`derivee_proie`, `derivee_predateur`) et le point d'équilibre non trivial (`equilibre_lotka_volterra` → proie\* = γ/δ, prédateur\* = α/β). Les sorties sont arrondies à 10 chiffres significatifs (précision honnête) et toute entrée hors domaine (niveau trophique < 1, énergie négative, paramètre ≤ 0, abondance négative) est refusée.

```python
ecologie.energie_niveau(10000, 3)   # → 100.0  (10000 · 0.1²)
```

### Estimer une population à partir d'un échantillon biaisé

C'est le cœur « démographique » statistique du domaine : la vraie moyenne d'une population existe, mais un échantillon biaisé la fausse *systématiquement* — un biais, pas du bruit, que l'on ne corrige pas en augmentant la taille.

- **`echantillon_pondere`** corrige un biais d'inclusion connu par les estimateurs de Horvitz-Thompson (`estime_ht`, moyenne de population de taille N connue) et de Hájek (`estime_hajek`, robuste, recommandé par défaut), avec intervalle de confiance par bootstrap pondéré (`intervalle_hajek`) et taille d'échantillon effective de Kish (`n_effectif`). Il s'abstient si les poids sont dégénérés ou l'échantillon trop petit.
- **`biais_longueur`** traite le biais de taille (paradoxes d'inspection, du temps d'attente, et d'amitié « vos amis ont plus d'amis que vous ») : la moyenne observée vaut E[X²]/E[X] = μ + σ²/μ ≥ μ, et la correction se fait par moyenne harmonique.
- **`berkson`** démasque le biais de collision : deux traits indépendants dans la population apparaissent corrélés (souvent négativement) dès qu'on ne regarde qu'un sous-ensemble sélectionné sur un effet commun. Le module quantifie la corrélation en population vs dans l'échantillon sélectionné.

```python
echantillon_pondere.estime_hajek(valeurs, poids)   # Σwy / Σw : moyenne corrigée du biais
```

### Décision sous incertitude et paradoxes de valeur

- **`saint_petersbourg`** montre que l'espérance de gain n'est pas le prix rationnel d'un pari quand la queue de distribution domine (espérance infinie, prix pourtant petit). Il fournit l'espérance tronquée, l'équivalent-certain par utilité logarithmique (Bernoulli) et la valeur sous bankroll fini.
- **`bandit`** couvre la décision séquentielle sous incertitude (classe `Bandit`, `simule`) : arbitrer exploration et exploitation dans le temps.
- **`incertitude_decomposee`** sépare l'incertitude *épistémique* (réductible par plus de données) de l'incertitude *aléatoire* (irréductible), à partir d'un échantillon ou d'un ensemble de prédicteurs, et fournit l'intervalle prédictif associé.

### Inférence statistique en grande dimension et calibrée

Un ensemble d'outils pour raisonner sans sur-confiance sur des données multivariées ou soumises à un changement de contexte :

- **`covariance_grande_dim`** : estimation de covariance quand le nombre de variables approche celui des observations (loi de Marchenko-Pastur, rétrécissement de Ledoit-Wolf, conditionnement).
- **`intervalle_tolerance`** : intervalle censé contenir une *proportion* donnée de la population (et non la moyenne), avec comparaison à l'intervalle naïf.
- **`region_multivariee`** : régions de prédiction conformes multivariées (distance de Mahalanobis) et leur test d'appartenance.
- **`prior_shift`** : correction d'un changement de prior / *label shift* (méthode Saerens-Latinne-Decaestecker) pour réajuster des probabilités a posteriori quand les proportions de classes changent entre apprentissage et cible.
- **`calibration_ranking`** : calibration d'un classement (probabilité qu'un item soit mieux qu'un autre, ajustement de température, mesures DCG / NDCG).

### Mécanismes techniques rattachés

Deux modules de mécanisme exact, calculables sans donnée inventée, rangés dans ce domaine :

- **`blockchain`** : intégrité d'une chaîne de blocs (`hash_bloc`, `cree_bloc`, `chaine_valide`, `merkle_root`, `preuve_travail_valide`).
- **`telecom`** : capacité de canal et grandeurs associées (`capacite_shannon`, `debit_nyquist`, `gain_db`, `longueur_onde`, `snr_depuis_db`).

### Découverte de lois et méta-modèle

- **`decouverte_loi`** : découverte symbolique d'une loi à partir d'observations.
- **`invention_divergente`** : câblage des briques qui inventent hors de la simple recombinaison de l'existant (apprentissage de loi, levée de contrainte, transfert par analogie, arbitrage de compromis, explication d'observations, plan de procédé).
- **`schema_relations`** : méta-modèle *mesuré* des relations (profil d'une relation, compatibilité des inverses, relations hiérarchiques).

### Garantie commune

Sur tout le domaine, la posture est uniforme et vérifiée en adverse : les modules « faits/formules » (chomage, cycles_economiques, ecologie…) implémentent le seul mécanisme établi et lèvent une erreur plutôt que de produire une valeur hors domaine ; les modules statistiques (Palier 2) exposent explicitement le mode d'échec qu'ils corrigent et **s'abstiennent** quand les données sont insuffisantes ou dégénérées. Aucun d'eux ne fabrique de chiffre conjoncturel ou de valeur-pays. C'est l'invariant FAUX=0 : préférer l'abstention explicite à une réponse fausse.

---

## Chimie & matériaux

Cette famille de capacités couvre le calcul **borné et exact** en chimie et en science des matériaux : partir d'une formule brute ou de quelques grandeurs mesurées et en déduire, sans jamais deviner, une masse molaire, l'équilibrage d'une réaction, une concentration, une enthalpie, la nature d'une liaison, ou encore une contrainte mécanique dans un matériau. La posture est celle de tout Provara : le **mécanisme** (la formule, la définition, la règle établie) est EXACT et constitue la garantie ; les **données** qu'il consomme (masses atomiques IUPAC, électronégativités de Pauling, constantes matériau) sont sourcées et fournies, jamais inventées. Toute entrée hors domaine déclenche une **abstention structurelle** (renvoi `HORS` ou `ValueError`) plutôt qu'un résultat plausible mais faux. Les modules sont déterministes et écrits en stdlib pure.

### Composition et stœchiométrie moléculaire

Le noyau de la chimie quantitative de base. `chimie` analyse une formule (y compris parenthèses imbriquées, groupes multiplicatifs et hydrates comme `CuSO4·5H2O`) et en tire la composition élémentaire, le nombre d'atomes, la masse molaire et le pourcentage massique d'un élément — un élément absent du référentiel IUPAC ou une formule mal formée donne `(HORS, None)`, jamais une masse fabriquée.

```python
chimie.masse_molaire("H2O")          # somme pondérée des masses atomiques standard
chimie.pourcentage_massique("H2O", "O")
```

`stoechiometrie` équilibre une équation en cherchant les plus petits coefficients entiers positifs qui annulent le bilan atomique — calcul exact sur ℚ (noyau de la matrice atomes×espèces) réutilisant le parseur de `chimie` ; la conservation de chaque élément est vérifiée sur les coefficients rendus, et une réaction non équilibrable ou à solution non unique déclenche `ValueError`. `chimie_quantitative` étend l'ensemble aux **solutions** (molarité `c = n/V`, dilution `c₁V₁ = c₂V₂`, concentration massique), à la **thermochimie** (loi de Hess `ΔH = ΣΔH_f(produits) − ΣΔH_f(réactifs)`, test exothermique) et à l'**électrochimie** (potentiel de pile `E = E_cathode − E_anode`, spontanéité), avec sortie arrondie à 6 chiffres significatifs et rejet des volumes/quantités ≤ 0.

```python
chimie_quantitative.molarite(0.5, 2.0)     # n/V en mol/L
chimie_quantitative.dilution(c1, v1, v2)   # c2 après dilution
```

### Liaisons, équilibres et réactions

Cette sous-famille raisonne sur la nature et le sens des transformations. `liaisons_chimiques` classe une liaison à partir des électronégativités de Pauling (covalente non polaire pour Δχ < 0.4, covalente polaire pour 0.4 ≤ Δχ < 1.7, ionique au-delà) et calcule le pourcentage de caractère ionique. `equilibre_chimique` calcule le quotient de réaction `Q = Π[produits]^ν / Π[réactifs]^ν` et le compare à la constante K pour prédire le sens d'évolution (loi d'action de masse : Q < K sens direct, Q > K sens inverse). `mecanismes_reactionnels` classe les substitutions et éliminations nucléophiles (SN1/SN2/E1/E2) d'après les règles établies de la chimie organique (nombre d'étapes, passage par carbocation, ordre cinétique, stéréochimie). `stereochimie` dénombre les stéréoisomères et qualifie la relation entre configurations, et `analyse_chimique` couvre les méthodes instrumentales élémentaires (loi de Beer-Lambert pour l'absorbance et la concentration, facteur de rétention `Rf` en chromatographie).

```python
liaisons_chimiques.nature_liaison(3.16, 0.93)   # -> 'ionique' (NaCl)
```

### Matériaux et leurs propriétés

Le versant « matériaux » calcule des propriétés physiques mesurables. `proprietes_materiaux` implémente l'élasticité linéaire (contrainte `σ = F/A`, déformation `ε = ΔL/L₀`, loi de Hooke `σ = E·ε`, allongement) — aucune constante matériau n'est codée en dur, le module de Young est une donnée fournie par l'appelant. `composites` applique la loi des mélanges à un matériau biphasé fibre/matrice : borne supérieure de Voigt (module d'Young en chargement parallèle), densité effective, borne inférieure de Reuss (chargement transverse), avec la propriété d'encadrement Reuss ≤ Voigt vérifiée. `alliages` fournit la règle du levier (fractions de phase) et un catalogue d'alliages binaires ; `ceramiques` couvre le retrait de cuisson, la porosité, la classification par température de cuisson (terre cuite < faïence < grès < porcelaine) et le fait établi de la fragilité céramique ; `batteries` calcule les grandeurs de stockage électrique (énergie en Wh, capacité en Ah, régime C, temps de charge, rendement énergétique).

```python
proprietes_materiaux.contrainte(F, A)                 # σ = F/A, A > 0 exigé
composites.module_young_composite(Vf, Ef, Em)         # borne de Voigt
```

### Procédés, fabrication et molécules d'intérêt

Modules tournés vers l'ingénierie chimique et la mise en œuvre. `genie_chimique` traite les réacteurs et la distillation (temps de séjour, conversion en réacteur CSTR/PFR d'ordre 1, nombre d'étages de Fenske) ; `petrochimie` couvre les coupes de distillation et l'indice d'octane d'un mélange en raffinage ; `pharmacochimie` applique la règle de cinq de Lipinski pour évaluer le caractère « drug-like » d'une molécule. Côté fabrication, `usinage` calcule les paramètres de coupe (vitesse de coupe, rotation de broche, taux d'enlèvement, temps d'usinage), `impression_3d` les paramètres de tranchage FDM (nombre de couches, temps, masse et longueur de filament), et `mecanismes` la transmission de mouvement et de force (rapports d'engrenages, avantage mécanique du levier, couple de sortie).

### Thermodynamique et physique des matériaux

Le bucket rassemble aussi les modules physiques adjacents mobilisés par la chimie et les matériaux. `entropie_thermo` implémente le deuxième principe (variation d'entropie, entropie de l'univers, critère de spontanéité) et `nucleosynthese` l'énergie nucléaire bornée (défaut de masse, énergie de liaison par nucléon, pic du fer). S'y ajoutent des noyaux de physique générale exacte présents dans ce domaine : `physique` (grandeurs calculables par formule), `maxwell` (conséquences quantitatives de l'électromagnétisme du vide), `relativite_restreinte` et `relativite_generale`, ainsi que `intrication` (test de Bell / CHSH). Tous partagent la même règle : formule établie appliquée telle quelle, abstention hors domaine.

### Modules connexes regroupés dans ce domaine

Fidèlement au contenu du bucket, celui-ci agrège également des modules de sciences voisines et d'infrastructure, décrits ici par leur objet réel : sciences du vivant (`bioinfo` séquences ADN, `bioingenierie` cinétique de Michaelis-Menten, `proteines`, `transport_membranaire`, `croissance_bacterienne`, `biostatistique` et `essais_cliniques` en épidémiologie) ; sciences de l'espace (`asteroides`, `astronautique`, `big_bang`, `habitabilite`, `drake`) ; l'aéronautique (`aerodynamique`) ; les mathématiques exactes (`maths_discretes`, `cardinalite`, `ordinaux`) ; les conventions et procédures (`recettes`, `conjugaison`) ; et le socle méta de Provara (`atome` le contrat d'atome, `classifieur_bornage` le routeur de statut anti-hallucination, `invention_atomes`, `boucle_invention`, `veille_corroboration`).

### Garantie commune

Sur tout le domaine, la même invariante ressort explicitement des docstrings : le mécanisme est exact et vérifié en adverse par un validateur dédié (`valide_chimie.py`, `valide_stoechiometrie.py`, `valide_composites.py`…), l'abstention est structurelle, et le comportement est conservateur — **un faux négatif (abstention) est toléré, un faux positif est interdit**. C'est l'application directe du principe FAUX=0 : mieux vaut renvoyer `HORS` que produire un chiffre chimiquement ou mécaniquement inexact.

---

## Physique & mesures

Cette famille regroupe les capacités de Provara qui **calculent une grandeur physique ou une mesure par une formule établie**, plutôt que de la restituer de mémoire. Le principe commun est celui du reste du projet : le mécanisme (la loi) est exact, les constantes sont des données sourcées (SI 2019 / CODATA), et toute entrée hors domaine provoque une abstention explicite (`ValueError`, `None`/`HORS`) au lieu d'un résultat faux. On y trouve le socle de représentation des grandeurs, les grands chapitres de la physique calculable (mécanique, électromagnétisme, quantique, thermique), des domaines de mesure appliqués (acoustique, sismologie, qualité, procédés) et un détecteur d'impossibilités qui sert de garde physique. Le bucket agrège aussi, par proximité de posture (calcul exact + abstention), des briques de mathématiques formelles, de mécanismes du vivant, d'inférence calibrée et des moteurs d'infrastructure, décrits plus bas.

### Socle de représentation : grandeurs, dimensions, états

Avant de calculer, la machine doit **typer** ce qu'elle manipule. `dimensions` fournit l'algèbre dimensionnelle : chaque grandeur porte un vecteur d'exposants sur les 7 dimensions de base SI (masse, longueur, temps, courant, température, quantité de matière, intensité lumineuse), avec une arithmétique d'exposants **exacte** (via `Fraction`, sans dérive flottante). C'est le premier filtre anti-absurdité : additionner ou comparer deux grandeurs de dimensions différentes, ou convertir entre unités incommensurables (mètre vs seconde), renvoie `None` (HORS) — jamais un nombre inventé ; les unités définies exactement (1 km = 1000 m, 0 °C = 273.15 K) sont exactes.

- `grandeur` porte une valeur avec son unité/dimension **et son incertitude**, et lève `IncoherenceDimensionnelle` sur une opération non homogène ; `grandeur_vectorielle` étend cela aux grandeurs non scalaires.
- `etat` modélise variables, états et espaces d'états (avec une valeur hors-domaine explicite) ; `etats_matiere` détermine l'état physique selon la température et convertit °C / K / °F.

### Mécanique, statique et structures

Le cœur « forces et solides ». `mecanique` couvre le frottement sec (F = μN), l'oscillateur harmonique (période/pulsation/fréquence d'un système masse-ressort, pendule simple), l'énergie élastique et la statique des fluides (pression, pression hydrostatique, poussée d'Archimède), avec la gravité standard sourcée (BIPM, 9.80665 m/s²) et une sortie arrondie à 6 chiffres significatifs. Un domaine invalide (masse ou raideur ≤ 0, coefficient < 0…) lève `ValueError`.

- `statique` : équilibre des solides et des structures (moments, équilibre des moments, réactions d'appui, centre de masse).
- `structures_genie` : résistance des matériaux (contrainte de flexion et de traction, moment quadratique, flèche d'une poutre, flambement d'Euler).
- `biomecanique` : physique du geste sportif (portée et hauteur d'un projectile, temps de vol, angle optimal, moment de force, impulsion).
- `mecanismes_machines` : mobilité d'un mécanisme plan (critère de Grübler–Kutzbach) ; `maritime` : architecture navale (vitesse de coque, poussée d'Archimède, masse maximale flottante, nombre de Froude).

### Électromagnétisme, ondes et physique quantique

`electronique` calcule les associations de résistances (série/parallèle), le diviseur de tension, la constante de temps RC, les impédances (condensateur 1/2πfC, bobine 2πfL) et la fréquence de résonance LC. `quantique` implémente les relations fondamentales avec constantes SI 2019 (h exacte) :

```
quantique.energie_photon(f)         # E = h·f   (Planck-Einstein)
quantique.longueur_onde_broglie(p)  # λ = h/p   (de Broglie)
quantique.borne_heisenberg(dx)      # Δp ≥ ħ/(2·Δx)
```

- `rayonnement_thermique` : corps noir — loi de déplacement de Wien (formes longueur d'onde et fréquence, qui ne désignent pas le même point du spectre) et loi de Stefan-Boltzmann, ancré sur des valeurs externes connues (CMB à 2.725 K → λ_max ≈ 1.063 mm ; Soleil à 5778 K → ≈ 501 nm).
- `semiconducteurs` : conversion gap eV → J, longueur d'onde seuil, type de dopage (n/p) ; `cosmologie` : expansion de l'univers (vitesse de récession, distance de Hubble, âge, décalage vers le rouge).

### Mesures appliquées et grandeurs de terrain

Domaines où l'on mesure et classe selon des barèmes ou lois établies.

- `audiologie` : échelle décibel, addition de niveaux en dB, classification de la perte auditive, plage audible.
- `seismologie` : magnitude de moment, conversion magnitude ↔ énergie (joules), classe d'un séisme.
- `controle_qualite` : maîtrise statistique des procédés (indices de capabilité Cp/Cpk, limites de contrôle, ppm hors spécifications, référence six sigma).
- `procedes_industriels` : rendement, bilan matière, débit de production, taux de conversion ; `energies_comparees` : facteur de charge, contenu énergétique, retour énergétique, émissions de CO₂ ; `cybernetique` : boucle de régulation (gain en boucle fermée, erreur statique, stabilité, effet de la rétroaction négative) ; `cryobiologie` : congélation et conservation.

### Détecteur d'impossibilités et bilans (le garde physique)

`coherence_physique` juge si un dispositif décrit **viole une loi établie**. Il s'appuie sur le 1er principe (conservation de l'énergie, rendement de conversion ≤ 1) et le 2nd principe (entropie, rendement ≤ Carnot, un système fermé ne se refroidit pas net). Sa posture est symétrique du « jamais un faux » : il rend `VIOLE` (une loi précise est enfreinte par la spec déclarée, en la nommant), `COHERENT_BORNE` (aucune violation détectée — ce n'est pas une preuve que ça marche) ou `HORS` (spec insuffisante). Conservateur : un faux positif est interdit, l'abstention est tolérée.

```
coherence_physique.juge_dispositif(spec)  # -> "viole" | "coherent_borne" | "hors"
```

- `conservation` établit un bilan et signale une violation de conservation ; `limite` porte une limite théorique et l'écart au réel observé.

### Briques adjacentes regroupées dans ce domaine

Le bucket rassemble, sous la même exigence de calcul exact et d'abstention, plusieurs briques qui débordent la physique au sens strict :

- **Mathématiques et systèmes formels exacts** : `algebre_calcul` (résolution d'équations linéaires/quadratiques), `topologie` (invariants d'Euler, genre), `galois` (résolubilité par radicaux), `godel` (numérotation de Gödel), `langages_formels` (grammaires, hiérarchie de Chomsky), `information_calcul` (entropie de Shannon, information mutuelle, divergence KL), `fractales` (dimension d'auto-similarité), `algo_analyse` (complexité), ainsi que les systèmes dynamiques `chaos` et `bifurcations` (application logistique, stabilité des points fixes).
- **Mécanismes du vivant (bornés)** : `genetique` (complément ADN, transcription, traduction codon → acide aminé), `mutations` (classification et effet d'une substitution), `immunite` (seuil d'immunité de groupe, taux de reproduction effectif).
- **Inférence calibrée (Palier 2)** : `propagation` (propagation d'incertitude Monte-Carlo), `fermi` (ordre de grandeur avec incertitude), `dkw` (bande de confiance), `conformal_adaptatif` et `conformal_pondere` (prédiction conforme), `exp3` (bandit adversarial), `tbm` (Transferable Belief Model).
- **Moteurs et infrastructure** : `base_faits` et `lecteur` (lookup de faits constatés / lecteur générique de données), `loi`, `deduction`, `simulation`, `logique_tri`, `questions`, `substrat_physique` et `substrat_reel` (découverte d'inventions par transduction), `_test_geant` (entraînement à grande échelle).

**Garantie commune.** Dans tout ce domaine, le mécanisme est exact et les constantes sont sourcées ; l'abstention est structurelle et conservatrice — face à une entrée invalide ou à une spec insuffisante, la machine renvoie une erreur, `None` ou `HORS` plutôt qu'un résultat faux : le faux négatif est toléré, le faux positif est interdit (FAUX = 0).

---

## Biologie & médecine

Cette famille rassemble des mécanismes **bornés** du vivant (physiologie régulée, électrophysiologie du neurone, rythmes biologiques), des outils de **raisonnement médical** (probabilité diagnostique bayésienne, catalogues de niveau de preuve, rythme d'événements), et un ensemble de briques **transverses de construction du savoir** que le classement automatique a regroupées ici (taxonomies, ontologie, induction de règles, boucle d'auto-amélioration). Le fil commun est celui de tout Provara : chaque module calcule un résultat **exact** à partir de faits ou de formules établis, ou **s'abstient** (généralement par `ValueError`) plutôt que d'inventer. Les modules sont en Python pur, déterministes, sans réseau ni GPU.

### Physiologie et régulation du vivant

Trois modules décrivent des mécanismes physiologiques dont la partie calcul est exacte et les valeurs de référence sont sourcées.

- **`homeostasie`** modélise la **rétroaction négative** qui maintient une variable physiologique près d'une consigne (set-point). Le mécanisme est exact (algèbre du signe) ; les consignes de référence sont des données sourcées de la physiologie humaine (glycémie à jeun ≈ 1 g/L, température centrale ≈ 37 °C, pH artériel ≈ 7,4). `ecart_consigne(valeur, consigne)` donne le sens du déséquilibre, `correction(valeur, consigne, gain) = −gain·(valeur − consigne)` produit une correction de signe opposé à l'écart, et `est_regule(valeur, consigne, tolerance)` teste l'appartenance à la bande régulée. Un `gain < 0` (qui serait une rétroaction *positive* amplifiant l'écart) ou une tolérance négative lèvent `ValueError`. Exemple : `homeostasie.correction(1.6, 1.0, 0.5)` renvoie `-0.3` (ramener une glycémie de 1,6 g/L vers 1,0).

- **`neurone_biologique`** implémente le modèle **intègre-et-tire à fuite (LIF)** de l'électrophysiologie classique. `potentiel_repos()` renvoie le fait établi −70 mV ; `depasse_seuil(potentiel_mV, seuil_mV)` déclenche un potentiel d'action quand la membrane atteint le seuil (≈ −55 mV) ; `frequence_decharge` donne la courbe fréquence-courant (f-I) rectifiée, et `frequence_decharge_bornee` la borne par la fréquence maximale imposée par la période réfractaire. Un gain négatif ou une période réfractaire ≤ 0 lèvent `ValueError`. Exemple : `neurone_biologique.depasse_seuil(-50, -55)` → `True`.

- **`chronobiologie`** couvre les **rythmes circadiens et cycles de sommeil**. `periode_circadienne()` renvoie le fait ≈ 24,2 h (période intrinsèque *free-running*, Czeisler et al., Science 1999) ; `nombre_cycles_sommeil(duree_min, cycle_min=90)` et `duree_pour_cycles` font l'arithmétique exacte des cycles de ≈ 90 min ; `phase_circadienne(heure)` classe une heure d'horloge (`'pic_melatonine'` / `'nuit'` / `'jour'`). Une durée négative, un cycle ≤ 0 ou une heure hors [0, 24) lèvent `ValueError`. Exemple : `chronobiologie.nombre_cycles_sommeil(480)` ≈ `5.33`.

### Médecine : raisonnement diagnostic et rythme des événements

- **`taux_de_base`** corrige la **négligence du taux de base** (paradoxe du faux positif) : confondre la sensibilité P(+|malade) avec la valeur prédictive P(malade|+) est sur-confiant car cela ignore la prévalence. Le module calcule la **VPP bayésienne** `vpp(sens, spec, prev) = sens·prév / [sens·prév + (1−spéc)(1−prév)]` et la **VPN** `vpn`, expose `estimation_naive` (le raccourci fautif), compare les scores de Brier des deux prévisionnistes (`brier_naif_vs_bayes`) et fournit une façade `analyse`. Des entrées hors [0, 1] entraînent l'abstention. Exemple : `taux_de_base.vpp(0.99, 0.99, 0.001)` ≈ `0.09` — même avec un excellent test, 91 % des positifs sont faux sur une maladie rare.

- **`poisson_nonhomogene`** répond à « combien d'événements dans la prochaine fenêtre, avec quelle incertitude honnête ? » quand le **rythme change dans le temps** (appels selon l'heure, pannes selon l'âge). Il estime une intensité *locale* λ̂(t) par bacs plutôt qu'un taux constant λ̄ (qui sous-couvre dans les fenêtres chargées), et construit l'intervalle prédictif à partir des quantiles de Poisson (`intensite_bins`, `comptage`, `intervalle_comptage`, `predit_fenetre`). Il s'abstient si les événements sont trop peu nombreux.

### Catalogues de consensus établi

Deux modules ne *déduisent* pas mais *constatent* un état de consensus, avec abstention hors référentiel.

- **`medecines_alternatives`** associe à chaque pratique son **niveau de preuve** établi (échelle fermée : `aucune_preuve`, `preuve_faible`, `preuve_limitee`, `preuve_moderee`, `preuve_forte`, `variable`), issu de méta-analyses et revues (ex. homéopathie → `aucune_preuve` ; méditation de pleine conscience → `preuve_moderee`). `niveau_preuve(pratique)` renvoie un libellé de l'échelle ou lève `ValueError` ; `depasse_placebo(pratique)` en est dérivé mais **ne renvoie jamais `True` pour une pratique `aucune_preuve`** (faux positif interdit) et s'abstient sur les niveaux non tranchés. `est_catalogue` et `pratiques` inspectent le catalogue. Toute pratique hors catalogue lève `ValueError`. Exemple : `medecines_alternatives.niveau_preuve("homeopathie")` → `'aucune_preuve'`.

- **`propagande`** est le catalogue **des sept techniques de propagande** codifiées par l'Institute for Propaganda Analysis (1937-1942) et de la **taxonomie du désordre informationnel** de Wardle & Derakhshan (Conseil de l'Europe, 2017), structurée par deux axes établis : l'information est-elle fausse (`est_faux`) et y a-t-il intention de nuire (`est_intentionnel`). `technique`, `liste_techniques`, `type_desinformation` interrogent ces référentiels ; toute entrée hors répertoire lève `ValueError`.

### Construction et organisation autonome du savoir

Ces briques transverses, regroupées ici par le classement automatique, servent à *bâtir et gouverner* la connaissance de l'IA — pas à décrire la biologie.

- **`bootstrap_savoir`** construit **seule une taxonomie is-a** en lisant des définitions (Wiktionnaire) : le genre est le premier mot d'une définition, qui a elle-même une définition, d'où un graphe is-a profond (`chat → mammifère → animal`). La `frontiere` (genres cités mais non encore définis) indique quoi aller chercher ensuite. API : `genus`, `graphe`, `chaine`, `frontiere`, classe `Savoir`.

- **`ontologie`** raisonne sur les hiérarchies **EST-UN présentes dans le corpus** (ex. `taxon_parent`) : subsomption transitive, `ancetres`, `est_un`, `plus_proche_commun`. La traversée est **paresseuse** (aucune matérialisation de fermeture transitive, qui exploserait la RAM). Invariant monde ouvert : `est_un(x, T)` n'est `True` que si un chemin réel de faits le prouve ; `False` signifie « non dérivable », jamais « faux dans le monde », et jamais d'inférence de type par ressemblance de nom ; les cycles de données sont détectés (`cycle`).

- **`taxonomie`** dérive une **taxonomie de types depuis les données** pour remplacer des listes de catégories écrites à la main : elle mesure la fraction d'échantillon (`frac_ech`) et la densité de couverture (`densite`) d'une relation sur un ensemble de référence. Ces mesures ne servent qu'à **autoriser ou bloquer** une réponse déjà vérifiée par ailleurs (un garde d'abstention), jamais à produire un fait. API : `ensembles`, `types_de`, `frac_ech`, `densite`, `source_lexicale_rel`, `population_compatible`, `hubs`.

- **`induction_horn`** **induit des règles de Horn** candidates (transitivité, symétrie, réflexivité, inverse) sur une relation binaire, puis les *valide* contre des exemples avant toute adoption. Ligne rouge FAUX=0 : une règle n'est jamais déclarée « vraie », au mieux **consistante** (couvre ≥ 1 positif, 0 négatif dérivé au point fixe) ; sans exemples négatifs on ne valide pas (`non_refutable`, monde ouvert) ; les faits impliqués au-delà des exemples sont marqués **incertains**. API : `derive`, `cloture_derives`, `evalue`, `induit`.

### Boucle vivante d'auto-amélioration

- **`compounding`** est la **montée autonome** : un curateur sert un curriculum gradué, l'orchestrateur escalade seul sur chaque tâche et s'arrête au premier candidat qui passe le visible *et* généralise (held-out) ; le succès confirmé rejoint le store et le registre de primitives, de sorte que les étages hauts grandissent seuls. API : `route`, `resoudre`, `resoudre_niveau`, `montee`, `franchies`, `etages_atteints`, classe `PasMontee`.

- **`generateur`** est le producteur de candidats (`Generateur` et ses variantes : apprenant, améliorant, recombinant, fusion, composé, à partir de briques), et **`generation_coherente`** fournit un `Ecrivain` qui produit des phrases complètes et cohérentes.

- **`utilite`** ajoute une **utilité évolutive** : l'utilité n'est plus binaire mais riche et **jugée par le réel** (correct, puis généralise, robuste, simple, rapide — ordre lexicographique), et le choix n'est pas définitif : on garde le plus utile par tâche, une meilleure solution supplante l'ancienne. API : classe `Utilite`, `evalue_utilite`, classe `Selection`.

### Garantie commune

Dans tout ce domaine, la règle FAUX=0 tient de bout en bout. Les modules physiologiques et médicaux ne renvoient que des grandeurs calculées à partir de formules ou de faits sourcés, et **lèvent `ValueError` hors référentiel** (gain négatif, entrée non finie, prévalence hors [0, 1], pratique inconnue) au lieu de deviner. Les catalogues répondent depuis un consensus fermé ou s'abstiennent. Les briques de savoir n'affirment `est_un`/une règle que si un chemin de faits réel le prouve, restent honnêtes en monde ouvert (`False` = « non dérivable », jamais « faux »), et marquent comme *incertain* tout ce qui dépasse les exemples validés. La posture est constante : produire l'exact, ou s'abstenir.

---

## Langue, lexique & écriture

Cette famille de capacités permet à Provara de traiter le mot et la phrase comme des
objets **vérifiables**, et non comme les intuitions d'un modèle : le principe fondateur
est « la définition officielle = la vérité » — la définition d'un mot est actée,
officielle, donc un *oracle de sens* que la réalité humaine juge. Sur ce socle, Provara
sait constituer un dictionnaire certifié, l'étendre à l'échelle d'un Wiktionnaire
complet, raisonner sur le sens et les relations des mots (hyperonymie, synonymie,
antonymie), lire une phrase française de bout en bout et répondre par **logique**,
puis fabriquer des corpus de compréhension entièrement vérifiés. Un second volet,
« écriture » au sens du code, couvre le *portfolio polyglotte* : détecter les langages
de programmation disponibles, choisir le mieux placé pour un besoin, et faire trancher
le résultat par un juge — quel que soit le langage.

### Le lexique certifié (l'oracle de sens)

Le point de départ est une graine de dictionnaire français réelle et certifiée. Chaque
entrée porte tous les axes vérifiables du mot : définition, classe grammaticale, genre,
hyperonyme (est-une-sorte-de), synonymes, antonymes.

- **`lexique_fr`** — la graine certifiée (structure de référence), avec les vues
  `edges_isa(lex)`, `edges_syn(lex)` et la remontée `ancetres(mot, lex)`.
- **`charge_lexique`** — l'ingesteur scalable : n'importe quel dump converti au format
  JSONL `{mot, classe, genre, definition, hyper, syn, ant}` est chargé, puis **contrôlé**
  avant d'alimenter l'aval. La cohérence exigée comprend les champs requis, un graphe
  is-a `mot -> hyper` **acyclique** (une boucle « X est une sorte de X » casserait la
  clôture) et le signalement des hyperonymes orphelins.

```python
lex = charge_lexique.charge("datasets/lexique.jsonl")
charge_lexique.coherence(lex)   # valide champs, acyclicité is-a, orphelins
```

### Passer à l'échelle : ingérer les grands dictionnaires

Franchir les murs lexicaux (mots irréguliers, sens ouvert) se fait par la **donnée**, pas
par la règle : on extrait ce que le dictionnaire dit déjà, sans rien inventer.

- **`convertit_kaikki`** — pont, en fonction **pure** (aucun réseau), d'un dump
  kaikki.org/frwiktionary vers le format `charge_lexique`. Les définitions françaises
  étant écrites « genus-first » (« chat = mammifère carnivore félin… »), le *genus* de la
  définition sert d'hyperonyme ; classe, genre, synonymes et antonymes sont mappés depuis
  les champs structurés.
- **`savoir_massif`** — branche le lexique massif (1,9 M entrées, graphe is-a de 1,87 M
  arêtes) comme ressource des briques de sens. Le graphe étant trop gros et cyclique pour
  une clôture directe, chaque question extrait le **sous-graphe pertinent** (chaînes
  d'ascendance, remontée garde-anti-cycle).
- **`relations_lexique`** — expose la synonymie (non dirigée) et l'antonymie (symétrique)
  extraites du lexique converti, via `aretes_syn(lex)` et `paires_ant(lex)`.

```python
sav = savoir_massif.SavoirMassif()
sav.est_un("chat", "animal")            # -> True
sav.ancetre_commun("chat", "chien")     # -> "mammifère"
sav.chemin("voiture", "objet")          # -> ["voiture", "véhicule", …, "objet"]
```

### Comprendre le texte français

Provara ne se contente pas de rappeler des mots : il analyse une phrase et en tire des
conséquences logiques.

- **`comprehension_integree`** — un seul moteur résout, sur la même phrase, la chaîne
  complète : structure (analyse) → rôles qui-fait-quoi (sujet/action/objet) → sens des
  mots (est-une-sorte-de, catégorie commune) → genre tiré de la définition → **déduction**.
  Les sorties se recoupent (la catégorie commune chat/chien doit coïncider avec le genre
  tiré de la définition de « chat »).
- **`lecture_comprehension`** — l'IA reçoit des faits en français (« le chat est un félin »,
  « le chat mange la souris »), les comprend (parse sujet/relation/objet) et répond :
  « X est-il un Z ? » par déduction transitive à trois valeurs (oui / non / **inconnu**),
  « qui \<verbe\> Y ? » en retrouvant le sujet. Ce qui n'est pas dérivable → « inconnu ».
- **`comprehension`** — le premier pas de l'abstraction : « comprendre, c'est compresser ».
  Plusieurs succès partageant une structure sont réduits à un concept réutilisable, qui
  n'est dit *compris* que si, régénéré puis re-jugé, il couvre réellement tous ses cas.

### Fabriquer des corpus de compréhension vérifiés

Ces modules transforment le lexique certifié en jeux d'entraînement instruction→réponse
où **rien de non vérifié n'entre**.

- **`fabrique_semantique`** — produit des paires vérifiées sur tous les axes du mot :
  définition, mot→définition (réversible), genre, hyperonymie **transitive**, synonyme,
  antonyme. Anti-dérive : une relation que la brique de sens ne confirme pas n'est jamais
  émise ; sortie JSONL prête pour l'entraînement.
- **`fabrique_comprehension`** — le capstone : un jeu unique couvrant toutes les capacités
  (sens des mots, catégorie, phrase SVO / accord / détection d'erreur, inférence,
  paraphrase), chaque paire étant confirmée par la brique-oracle correspondante exécutée
  par le juge.

### Couverture lexicale et mots inédits

- **`good_turing`** — corrige la sur-confiance « ce que je n'ai jamais vu a une probabilité
  0 » sur les distributions de mots à longue traîne (Zipf). Il estime la **masse manquante**
  (P₀ ≈ N₁/N, N₁ = nombre de singletons) et la richesse cachée (Chao1 : Ŝ = S_obs + N₁²/(2·N₂)),
  réservant une probabilité positive à l'inédit (log-loss fini). Fonctions : `masse_manquante`,
  `richesse_chao1`, `logloss_inedit`, `analyse`.

### Portfolio polyglotte (choisir et écrire dans le bon langage)

Le versant « écriture » : plutôt que de tout écrire en Python, Provara cumule les langages
de programmation et trie selon le besoin, en s'assurant que le résultat reste jugeable.

- **`environnement`** — détecte ce qui est réellement exécutable sur la machine (découverte
  locale, zéro réseau) et mappe chaque langage à ses forces via un registre curé.
- **`routeur_langage`** — pour un besoin (perf, web, système…), `choisit` le meilleur langage
  à la fois **présent** et doté d'un exécuteur jugeable ; aucun match → `None` (l'appelant
  garde Python par défaut).
- **`polyglotte`** — génère une solution dans un autre langage (JS/Perl/Bash) sur une famille
  bornée (opérations binaires scalaires : arithmétique, bit-à-bit, max/min) et la fait vérifier
  par le juge ; hors de sa famille, `demande_lang` rend HORS, jamais du faux.
- **`executeur_niches`** — Prolog (logique), R (statistique) et SQL (relationnel) : trois
  paradigmes, un même juge qui tranche par l'exemple.
- **`equivalence_semantique`** — décide si deux fonctions calculent la même chose : EQUIVALENTES
  n'est affirmé que par vérification **exhaustive** sur un domaine fini ; sinon, soit un
  contre-exemple re-vérifiable (DIFFERENTES), soit NON_DISTINGUEES. C'est le prérequis du
  refactor préservant le comportement.

### La garantie commune : exactitude ou abstention (FAUX=0)

Sur tout le domaine, la même règle ressort des docstrings : la vérité vient d'une source
actée (la définition officielle, le dictionnaire) et non d'une génération ; une relation
que la brique de sens ne confirme pas n'est **jamais** émise ; ce qui n'est pas dérivable
est répondu « inconnu » plutôt qu'inventé ; une équivalence n'est déclarée que si elle est
prouvée ; et un langage n'est proposé que s'il est réellement exécutable et jugeable. Provara
préfère systématiquement l'abstention à l'affirmation non vérifiée.

---

## Mathématiques & algorithmes

Cette famille rassemble les capacités *calculatoires* de Provara : arithmétique exacte, analyse, structures discrètes, théorie du calcul, architecture machine, génie logiciel, théorie des jeux et raisonnement statistique. Le fil commun est le même que partout dans le système : le mécanisme est *exact et déterministe* (entiers arbitraires, fractions `Fraction`, arithmétique binaire, énumération), et toute entrée invalide ou hors domaine lève `ValueError` plutôt que de produire une réponse fausse. Ces modules ne « devinent » pas : ils *calculent* quand la réponse est déterminée, et *s'abstiennent* sinon. Ce sont, pour beaucoup, des primitives directement appelables (même posture que `physique.py` : « le réel juge, jamais un faux »).

### Arithmétique, théorie des nombres et cryptographie

`arithmetique_modulaire` fournit les briques de la cryptographie mathématique : `pgcd`, `euclide_etendu`, `inverse_modulaire`, exponentiation modulaire (`exp_modulaire`, square-and-multiply), test de primalité de Miller-Rabin *déterministe* (jeu de témoins prouvé pour n < 3,3·10²⁴) et chiffrement/déchiffrement RSA (`rsa_chiffre`, `rsa_dechiffre`). Tout est exact ; un inverse modulaire inexistant (pgcd ≠ 1) lève `ValueError` au lieu d'inventer une valeur.

```python
arithmetique_modulaire.est_premier(97)        # True
arithmetique_modulaire.inverse_modulaire(3, 7)  # 5  (car 3*5 = 15 ≡ 1 mod 7)
```

`cryptographie_appliquee` couvre le volet symétrique : César (décalage), Vigenère (clé répétée), XOR (involutif). La propriété garantie est la réversibilité exacte : `dechiffre(chiffre(m, k), k) == m` ; clé vide ou caractère hors alphabet → `ValueError`.

### Analyse : calcul, séries, encadrement rigoureux

`calcul_infinitesimal` manipule les polynômes de façon exacte sur ℚ : `evalue`, `derivee`, `primitive`, `integrale_definie`, ainsi que les limites de polynômes et de fractions rationnelles en un point. `series_calcul` calcule les sommes arithmétiques et géométriques (finies exactes, et infinie `a/(1−r)` si |r|<1) et applique les critères de convergence (géométrique, série de Riemann Σ1/nˢ convergente ssi s>1) — une série divergente interrogée sur sa somme → `ValueError`, aucune limite inventée.

`arithmetique_intervalles` (Palier 2) propage une incertitude bornée `x ∈ [a,b]` à travers `+ − × ÷` avec *arrondi extérieur* : par le théorème de Moore, le résultat *contient toujours* la vraie valeur (couverture = 1). C'est l'inverse de la sur-confiance : la méthode ne peut jamais être trop étroite ; elle s'abstient sur une division par un intervalle contenant 0.

### Structures discrètes : groupes et graphes

`groupes` traite les groupes finis : ordre d'un élément dans ℤ/nℤ, composition et signature de permutations, ordre d'une permutation, vérification qu'une table de Cayley définit bien un groupe, théorème de Lagrange. `theorie_reseaux` calcule les métriques de graphes non orientés : degré, degré moyen, densité `2|E|/(n(n−1))`, centralité de degré normalisée, distribution des degrés, coefficient de clustering local.

### Théorie du calcul et fondations

Un noyau dédié à ce que l'on peut décider, calculer et typer :

- `complexite` — théorème maître de diviser-pour-régner (`classe_master(a,b,d)` rend la forme Θ symbolique) et comparaison d'ordres de croissance asymptotiques sur un vocabulaire fixe. Ancres CLRS : mergesort → `n log n`, Karatsuba → n^log2(3), Strassen → n^log2(7).
- `calculabilite` — fonctions récursives par leur définition : Ackermann-Péter (récursive mais *non* primitive récursive, calcul itératif borné pour rester un outil sûr), récursion primitive (addition/multiplication/puissance), numéraux de Church.
- `decidabilite` — catalogue de faits *prouvés* : arrêt (indécidable, Turing 1936), SAT (décidable, NP-complet), primalité (P, AKS 2002), PCP, équivalence de machines de Turing… ; hors catalogue → `ValueError`.
- `types_categories` — typage du lambda-calcul simplement typé (`type_de`) et lois des morphismes d'une catégorie libre (identité, associativité comme *théorèmes* toujours vrais) ; terme mal typé ou composition incompatible → `ValueError`.

```python
complexite.classe_master(2, 2, 1)   # 'n log n'  (mergesort)
```

### Architecture machine et réseaux

`architecture` code la représentation des nombres (binaire, hexadécimal, complément à deux, addition binaire). `microprocesseurs` descend au niveau logique : portes, additionneur complet, ALU. `reseaux_ip` calcule l'adressage IPv4 exact (adresse de réseau, broadcast, masque, nombre d'hôtes, appartenance à un même sous-réseau) par arithmétique 32 bits ; octet ∉ 0..255 ou CIDR ∉ 0..32 → `ValueError`.

### Génie logiciel : localiser, réparer, mesurer les tests

Deux modules « code avancé » outillent le cycle debug → fix. `localisation_faute` classe les instructions par suspicion (Ochiai, spectrum-based : ce qui est surtout exécuté par les tests qui *échouent*) puis cherche parmi des patches candidats le premier qui passe *tout*, held-out compris — un patch qui ne passe que les tests visibles est du sur-apprentissage, donc rejeté. `mutation_testing` mesure l'adéquation *réelle* d'une suite de tests en injectant des mutants : un survivant *prouvé non équivalent* révèle une lacune ; les mutants sémantiquement équivalents sont filtrés pour ne pas fausser le score.

### Théorie des jeux et décision séquentielle

`jeux_appliques` calcule les équilibres de Nash *purs* et les stratégies dominantes d'un jeu bimatriciel (ancres : dilemme du prisonnier, bataille des sexes, matching pennies). `jeux_zero_somme` (Palier 2) traite le maximin et le théorème minimax (stratégie de sécurité, jeu fictif). `kelly` donne la fraction de pari à croissance logarithmique optimale. `no_free_lunch` illustre le théorème de Wolpert-Macready (aucun apprenant universellement meilleur). L'énumération des profils est exacte ; une matrice mal formée → `ValueError`.

### Raisonnement statistique et pièges démasqués (Palier 2)

Une série de modules « Palier 2 » *quantifie* des phénomènes statistiques et démasque le raisonnement naïf correspondant : ancrage (`ancrage`), effet Dunning-Kruger comme artefact statistique (`dunning_kruger`), loi des grands nombres mal comprise (`loi_grands_nombres`) et loi des petits nombres / classement par taux brut (`petits_nombres`), ergodicité (moyenne d'ensemble vs temporelle, `ergodicite`). Pour l'évaluation de classifieurs : `matrice_confusion` (précision, rappel, F1, MCC, exactitude équilibrée) et `roc_auc` (AUC avec intervalle de confiance de Hanley). S'y ajoutent le clustering non-paramétrique de Dirichlet (`dirichlet_process`), la stabilité algorithmique et la borne de généralisation (`stabilite_algorithmique`), et la prévision temporelle à incertitude croissante avec l'horizon : auto-régressive (`serie_autoregressive`) et multivariée VAR(1) avec région conjointe (`serie_multivariee`). Chacun rend une *mesure* et l'incertitude associée, jamais une certitude non justifiée.

### Moteurs d'invention, de recherche et de raisonnement

Le domaine contient aussi la machinerie *méta* qui pilote l'exploration de Provara : `auto_invention_ouverte` (moteur compositionnel multi-domaines), `recherche_dirigee` (dompter l'explosion combinatoire de l'invention), `planification` (plans multi-étapes via opérateurs), `causalite` (graphe causal + intervention), `identite` (identité canonique unifiée), le lot d'exercices curés (`exercices`), et les harnais de mesure d'architecture (`cherche_architecture_max`, `mesure_phase3_exhaustif`, `mesure_structure2`) qui comparent des stratégies de résolution jugées par le réel. `garde_ressources` est le filet kernel qui borne cette exploration (pmap, RLIMIT) pour ne jamais faire tomber l'environnement.

### Calculs appliqués et modules connexes

Le domaine héberge enfin des calculateurs applicatifs exacts et déterministes : finances personnelles (`budget_personnel` : solde, taux d'épargne, règle 50/30/20 ; `retraite` : proratisation, décote ; `gestion_risque` : VaR paramétrique, ratio de Sharpe), posologie médicale (`posologie` : débit de perfusion, surface corporelle de Mosteller, dose pédiatrique) et répartition électorale (`scrutin` : d'Hondt, Sainte-Laguë, quotient de Hare). Sont également rangés dans ce bucket des noyaux de *production* (graphiques `graphique`, images matricielles `raster_png`, tableur OOXML `tableur_xlsx`, tous « pur stdlib ») et quelques calculateurs relevant d'autres domaines applicatifs mais exposant des formules exactes (`hydraulique`, `topographie_arpentage`, `redox`), plus l'accès web souverain `veille`.

---

**Garantie commune.** Sur tout ce domaine, l'invariant est *FAUX = 0* : le mécanisme est exact (entiers/fractions/arithmétique binaire, définitions et théorèmes établis) et l'abstention est *structurelle* — toute entrée invalide, hors domaine ou indéterminée lève `ValueError` au lieu de renvoyer un résultat faux. Le faux négatif (s'abstenir) est toléré ; le faux positif est interdit. Plusieurs modules sont explicitement vérifiés en adverse par un validateur dédié (`valide_<module>.py`) combinant ancres connues, tests de soundness et allers-retours (round-trip RSA, réversibilité des chiffrements).

---

## Temps, dates & histoire

Cette famille de capacités permet à Provara de **situer des faits et des événements dans le temps, de raisonner sur leur ordre, de retenir durablement ce qu'elle a appris, et de prévoir honnêtement** — le tout sans arithmétique floue ni devinette. Son cœur est temporel : une algèbre de relations entre intervalles, une mémoire persistante et horodatée qui « ne perd pas le contexte au fil du temps », et une prévision qui assume l'incertitude du futur par un intervalle plutôt qu'une fausse précision. Autour de ce noyau, le domaine rassemble aussi des catalogues de faits et de conventions établis que l'IA restitue exactement ou pour lesquels elle s'abstient. Partout, la même posture : le mécanisme est exact, et hors référentiel c'est l'abstention, jamais un faux.

### Situer et ordonner dans le temps

`allen` implémente l'**algèbre d'intervalles d'Allen** : entre deux intervalles propres `[début, fin]` (début < fin), il existe exactement 13 relations qualitatives mutuellement exclusives et exhaustives (`before`, `meets`, `overlaps`, `during`, `equals`, leurs inverses…). C'est le socle du raisonnement temporel qualitatif : « le mandat de X a-t-il chevauché celui de Y ? », « la cause précède-t-elle l'effet ? ». `relation(a, b)` rend toujours exactement une relation ; un intervalle mal formé (début ≥ fin) lève `ValueError` plutôt que de juger une entrée dégénérée. Les bornes peuvent être tout type ordonné (nombres, dates ISO comparables comme chaînes). Des prédicats de commodité (`avant`, `chevauche`, `contient`) et l'`inverse` (relation-miroir vérifiée involutive) complètent l'API.

```python
allen.relation((1, 3), (2, 5))   # 'overlaps'  (1 < 2 < 3 < 5)
allen.inverse('overlaps')        # 'overlapped_by'
```

### Retenir dans la durée : mémoire persistante et restitution

Trois modules réalisent le mandat « l'IA apprend ET retient », sans téraoctets ni dépendance à une IA tierce :

- **`memoire_faits` (`MemoireFaits`)** — mémoire d'informations/faits persistante, branchée sur `base_faits` (le juge de lookup vérifié). Chaque fait est une entrée structurée minuscule `(relation, entité, contexte) -> (valeur, catégorie, source, horodatage)`, dé-dupliquée et append-only sur disque (JSON). Elle est **bitemporelle** : le contexte porte le temps ou la situation, si bien que « Macron président de la France **en 2026** » se retient sans écraser la valeur de 2017, et un historique des révisions (temps de transaction) est conservé pour l'audit. Lookup O(1) par clé normalisée ; fait absent → `HORS` honnête, jamais une devinette.
- **`memoire_briques` (`MemoireBriques`)** — pendant de la précédente pour les **capacités** : une bibliothèque persistée de briques vérifiées, réinjectable dans le registre `existant` du moteur d'analyse (`examine_cible`). Une cible déjà apprise redevient reconnue d'emblée au lieu d'être re-dérivée. La soundness est inchangée : une brique n'est réutilisée que si elle **reproduit** réellement les données de la nouvelle cible.
- **`restitution` (`MoteurRestitution`)** — le moteur qui *rappelle* vite ce qui est déjà su (par opposition à l'analyse qui *dérive* l'inconnu). Faits shardés par domaine (activation parcimonieuse, façon mixture-of-experts), rappel exact mémoire-d'abord en O(1), scoring de récence/fréquence **ACT-R** (`B = ln(Σ (Δt+1)^-d)`) pour distinguer le chaud du froid, et consolidation « sommeil » qui compresse N faits mémorisés en une règle. Rappel exact ou `HORS` : jamais une réponse inventée.

### Prévoir, et se garder des pièges des séries temporelles

- **`prevision`** prévoit la prochaine valeur d'une série avec un **intervalle de prédiction calibré**, jamais un point seul. Méthode model-free : tendance par régression linéaire, saisonnalité optionnelle (période `m`), et intervalle obtenu par un hold-out temporel (la prévision à 1 pas est rejouée sur l'historique avec le seul passé) → quantile conforme des résidus honnêtes. La couverture visée est le niveau `confiance` ; si la série est trop courte, le module s'abstient.

  ```python
  prevision.prevoit(serie, periode=12, confiance=0.90)
  # -> (ESTIMATION, (point, (bas, haut)), confiance)  ou  ABSTENTION
  ```

- **`regression_fallacieuse`** démasque le mode d'échec de Granger-Newbold : régresser deux séries **non-stationnaires** (marches aléatoires, séries à tendance) produit un `t` « significatif » et un `R²` élevé même quand les séries sont totalement indépendantes (~75 % de faux positifs au lieu de 5 %). Le module quantifie le piège et rappelle la correction (travailler sur les différences, ou tester la cointégration). Pour des séries stationnaires, l'inférence OLS reste valide.

### Catalogues de faits établis et de conventions

Plusieurs modules bornent un domaine par un **référentiel fermé** de faits ou de conventions sourcés ; toute entrée hors table donne une abstention (`HORS` ou `ValueError`), jamais une valeur devinée :

- **`references`** — codes et tables posés par une norme : code Morse international, alphabet phonétique OTAN/ITU, code des couleurs des résistances, fréquence d'une note en gamme tempérée (A4 = 440 Hz, formule 12-TET). Ex. `references.vers_morse("SOS")`, `references.nato("A")`, `references.frequence_note(...)`.
- **`conservation_aliments`** — méthodes et seuils de conservation (réfrigération 0–4 °C, congélation −18 °C, pasteurisation, stérilisation/UHT, séchage, salaison, fumage) et zone de danger de température microbiologique.
- **`plastiques`** — code d'identification des résines (PET=1, PEHD=2, PVC=3, PEBD=4, PP=5, PS=6, autres=7), classe thermique (thermoplastique vs thermodurcissable) et température de transition vitreuse pour quelques polymères.
- **`cardiologie`** — formules cliniques consensuelles : fréquence cardiaque maximale (220 − âge), QTc de Bazett, fraction d'éjection, classes de fréquence au repos ; la soundness bloque tout domaine physiologiquement absurde (âge hors [0, 120], volumes ≤ 0…).
- **`pseudosciences`** — statut scientifique de validité (consensus établi) : `aucune` (réfutée par études contrôlées) ou `non_demontree` (aucune preuve reproductible). Le module rapporte le **statut de preuve** sur les claims, pas un jugement sur le vécu subjectif.
- **`procedes_fabrication`** — classification conventionnelle des procédés (soustractif / additif / formage / assemblage) et rendement matière (`masse_finale / masse_initiale`, borné [0, 1] ; un rendement > 1 lève une erreur).
- **`strategie_jeux`** — stratégie optimale des jeux résolus à information parfaite par **minimax énuméré** sur l'arbre complet : le morpion est prouvé nul par construction, et `morpion_coup_optimal` renvoie le coup gagnant ou bloque une menace imparable ; plateau invalide → `ValueError`.

### Développement/sécurité et mesure interne

- **`audit_code`** borne le développement par un référentiel de règles vérifiables : la **présence** d'un motif dangereux défini (injection via `eval` — CWE-95, injection SQL — CWE-89, anti-patterns déterministes) est un fait constatable, rendu comme un `Constat` daté et sourcé (id CWE). Ce qui n'est pas borné — affirmer qu'« un code est sûr / sans faille » — n'est jamais prétendu (l'absence de vulnérabilité est indécidable).
- **`mesure_structure_pertache`** est un banc de mesure interne : il compare des stratégies de traversée « structure → par tâche » (round-robin `rr2` et variantes stride/occam/topfirst/costweight) pour atteindre au plus vite le bon candidat de chaque tâche, sans choisir de stratégie à la main. Le choix de stratégie est **neutre en correction** (couverture identique) ; on ne mesure que le coût.

**Garantie commune du domaine (FAUX=0).** Tous ces modules partagent la même règle : le mécanisme — relation d'Allen, formule clinique, table de conventions, minimax, prévision calibrée — est exact et déterministe, et hors de son domaine de validité la réponse est l'abstention explicite (`HORS`, `ABSTENTION` ou `ValueError`), jamais une valeur inventée. Pour la mémoire temporelle, cette exactitude s'étend dans la durée : les faits sont horodatés, bitemporels et sourcés, un fait absent renvoie `HORS`, et une capacité n'est réutilisée que si elle reproduit réellement les données.

---

## Raisonnement & logique

Cette famille de capacités permet à Provara de **tirer des conclusions à partir de prémisses** — et non seulement de restituer des faits. Elle couvre l'inférence logique classique, le raisonnement non-monotone (cas général et exceptions), l'abduction (remonter aux causes), l'application de règles posées par une autorité, ainsi que l'infrastructure qui rend ces raisonnements *sûrs* : vérité-terrain non circulaire, arbitrage des contradictions et traces vérifiables. Le fil conducteur est constant avec le reste du système : chaque module est déterministe, en Python pur (stdlib), souverain/offline, et s'abstient plutôt que d'affirmer quand la réalité ne tranche pas.

### Inférence logique et argumentation

Deux modules travaillent sur la **forme** d'un raisonnement, indépendamment du contenu.

- **`sophismes`** identifie la forme d'un syllogisme conditionnel (prémisse majeure `A→B`) et juge sa validité en logique propositionnelle classique. Il reconnaît les schémas valides (*modus ponens*, *modus tollens*) et les schémas invalides (affirmation du conséquent, négation de l'antécédent) ; toute combinaison hors de ces schémas reconnus lève une erreur (abstention). Il fournit aussi un catalogue de sophismes informels nommés avec leur définition.

  ```python
  forme = sophismes.identifie_forme("p->q", "p", "q")   # forme du raisonnement
  sophismes.est_valide(forme)                            # validité logique
  ```

- **`paradoxes`** traite les paradoxes logiques établis (menteur, Russell, barbier, Grelling–Nelson) via des mécanismes exacts : détection d'auto-référence (`est_autoreferentiel`), diagonale `p ⟺ ¬p`, test d'un adjectif hétérologique (`est_heterologique`), et un catalogue des cas classiques.

### Raisonnement non-monotone : défaut, exceptions et signes

Quand la connaissance est partielle, il faut conclure sans sur-affirmer.

- **`raisonnement_defaut`** modélise le « cas général vs cas particulier » (non-monotone, à la Reiter) : une règle « normalement les *X* sont *Y* » admet des exceptions explicites qui la révisent. Trois garde-fous assurent FAUX=0 : l'exception déclarée prime toujours le défaut ; le défaut n'est conclu que pour un membre *connu* de la classe (sinon `ABSTIENT`) ; « pas dérivable » n'est jamais « faux ». `conclut(membre)` renvoie un triplet `(statut, valeur, raison)` avec `statut ∈ {DEFAUT, EXCEPTION, ABSTIENT}`.

  ```python
  r = raisonnement_defaut.RegleDefaut("oiseau", "vole", True)
  r.ajoute_membre("titi"); r.sauf("pingu", False)
  r.conclut("titi")   # -> défaut ; r.conclut("pingu") -> exception ; membre inconnu -> abstient
  ```

- **`qualitatif`** raisonne sur les *sens* de variation plutôt que sur des valeurs : algèbre des signes (`+`, `−`, `0`, `?`) et réseaux d'influences monotones (`ReseauInfluences`). L'ambiguïté est honnête : la somme de signes opposés donne `?` (indéterminé), jamais un signe deviné, et un chemin passant par `?` propage `?`.

  ```python
  qualitatif.signe_somme("+", "-")   # -> "?" (indéterminé, non tranché au hasard)
  ```

### Abduction : inférer la meilleure explication

- **`abduction`** (adossé à `causalite`) propose, face à des observations, les hypothèses qui les expliqueraient. Sur un graphe causal, `hypotheses_possibles` liste les causes candidates (ancêtres causals) et `meilleure_explication(graphe, observations, taille_max=3)` retourne le plus petit ensemble d'hypothèses expliquant *toutes* les observations (parcimonie, rasoir d'Ockham). `explique` vérifie qu'une hypothèse est bien une cause (directe ou transitive) par un chemin réel du graphe.

### Règles posées par une autorité et normes établies

- **`regle`** est un moteur générique de **règles normatives** (lois, règles métier, procédures, hygiène, normes) : l'IA « apprend » un domaine en ingérant un `Referentiel` (règles vérifiées + sources). Est borné : la *lettre* de la règle (lookup exact, daté, scopé) et l'*application* d'un prédicat explicite à un cas non ambigu. N'est pas borné, donc `ABSTENTION` : l'interprétation, la qualification fine, les conflits. Garanties structurelles : une règle absente n'est jamais inventée ; une règle abrogée ou pas encore en vigueur n'est pas appliquée ; deux portées (FR/UE/entreprise) ne se mélangent pas ; un champ manquant du cas → abstention ; `prevaut` applique la hiérarchie des normes.

  ```python
  ref = regle.Referentiel("HACCP").apprend(mes_regles)
  ref.cherche("FR", "art_L123", date="2026-07-03")   # Regle en vigueur, ou None (jamais inventée)
  ```

- **`journalisme_deontologie`** applique la même posture à un **catalogue de devoirs établis** (Charte de Munich, SPJ Code of Ethics) : `principe(nom)` ne reconnaît que les 7 principes en *closed-set* et `respecte_deontologie` ne juge que des pratiques cataloguées sans ambiguïté — toute pratique hors catalogue lève une erreur (abstention).

### Du savoir appris au savoir raisonné

- **`regles_induites`** est le **pont induction → déduction** : les règles validées par `induction_horn` deviennent des clauses Datalog consommées par `deduction`. La ligne rouge : seules les règles validées (consistantes au point fixe, support > 0, réfutables) entrent ; un fait dont la dérivation dépend d'une règle induite est marqué `INCERTAIN` (une généralisation), jamais `VERIFIE` ; les exemples négatifs déclarés sont persistés comme gardes (un fait déclaré faux reste servi `REFUTE`).

### Garanties FAUX=0 : vérité-terrain, arbitrage, traçabilité

Trois briques fondent la fiabilité de toute la couche de raisonnement.

- **`ancres`** — banque d'ancres **non circulaire** : le référentiel de vérité-terrain. Une ancre est `(clé, valeur, source)` avec source indépendante ; `verifie(cle, valeur, source_de_la_reponse)` renvoie `CONFIRME / CONTREDIT / INCONNU`, mais **refuse** (`CIRCULAIRE`) si la source de la réponse est celle de l'ancre : on ne se corrobore pas soi-même. Deux ancres contradictoires sur une clé → `Incoherence`.

- **`arbitre`** tranche les contradictions à l'exécution : à partir de propositions `(valeur, source)` et d'une table de fiabilités, il agrège les poids par valeur et rend `CONSENSUS`, `TRANCHE` ou `ABSTENTION`. `valeur_arbitree(propositions, fiabilites)` donne directement la valeur retenue, ou `None`.

  ```python
  arbitre.valeur_arbitree([(42, "capteur"), (41, "estimation")], {"capteur": 3, "estimation": 1})
  ```

- **`trace`** rend toute conclusion **remontable jusqu'aux prémisses et re-vérifiable** : un DAG d'étapes `(id, opération, entrées, sortie, justification, vérificateur)`. `remonte(id)` renvoie toute la sous-trace (et détecte les cycles → `Cycle`), `verifie(id)` rejoue les vérificateurs de la sous-trace et n'est vrai que si aucun ne renvoie faux.

### Confiance des chaînes d'inférence

Deux briques du « Palier 2 » calibrent la confiance d'un raisonnement séquentiel.

- **`calibration_sequence`** : la confiance d'une génération multi-étapes (type LLM) est le *produit* des confiances par étape ; la sur-confiance par étape se compose et explose. Le remède est de recalibrer chaque étape (isotonique, hors-échantillon) *avant* de multiplier, avec abstention si le jeu de calibration est trop petit.

- **`inference_anytime`** fournit une **séquence de confiance anytime-valid** (Robbins, mélange normal) : un intervalle valide *à tous les instants simultanément*, ce qui autorise à surveiller en continu et s'arrêter n'importe quand sans gonfler le taux d'erreur (contre le *peeking*).

### Interroger, viser et produire

Cette dernière sous-famille relie le raisonnement à l'usage.

- **`demande`** est l'**interface de requête** : une demande = signature + exemples entrée→sortie ; le moteur rend du code vérifié (les exemples *sont* le vérificateur), ou un `HORS` honnête plutôt qu'un faux.
- **`besoin`** ajoute une couche d'**objectifs** pour l'invention : décompose un besoin borné en sous-objectifs physiques et leviers, énumère des principes candidats jugés par `coherence_physique` (l'impossible est réfuté, le possible reste une supposition), et rend `HORS` sur un besoin inconnu — pour rendre le manque visible.
- **`chercheur_invention`** raisonne sur un *corpus* de cibles : inventaire (`EXISTE_DEJA / INVENTION / AMBIGU / BRIQUE_MANQUANTE`) et priorisation par réutilisation mesurée (un composant qui revient dans plusieurs solutions vérifiées est une abstraction à extraire).
- **`editeur`** est un substrat **déterministe** de création/modification de fichiers : la mutation s'applique exactement comme spécifiée ou échoue honnêtement (`ValueError`), sans écrasement d'un contenu non lu ni suivi de symlink (durci contre les TOCTOU). Il ne juge pas la justesse du contenu, laissée à un juge réel (tests, `refactor`).

*(Note de fidélité : le module **`teledetection`** figure dans ce lot mais relève de la télédétection — GSD, NDVI, résolution temporelle — et non du raisonnement logique.)*

### Garantie commune du domaine

Toutes ces briques partagent l'invariant FAUX=0 explicité dans leurs docstrings : elles sont **sound avant d'être rapides**. Rien n'est inventé (une règle, une ancre ou une explication absente n'est jamais fabriquée), l'ambiguïté et l'inconnu produisent une **abstention** ou un `HORS` explicite plutôt qu'une affirmation, et les conclusions dérivées restent traçables et re-vérifiables jusqu'à leurs prémisses.

---

## Incertitude & calibration

Ce domaine est le versant **non-borné** de Provara. Là où le borné garantit « jamais un faux » (réponse exacte, vérifiée, ou abstention), une estimation statistique ne peut pas garantir l'exactitude d'un chiffre isolé. La discipline change donc sans perdre l'honnêteté : au lieu d'une réponse certaine, on produit une **estimation accompagnée d'une confiance calibrée**, et on s'abstient dès que l'échantillon ne permet pas de la garantir. L'invariant qui remplace ici « FAUX=0 » est la **calibration** : une confiance annoncée « 90 % » doit s'avérer juste ~90 % du temps, et un intervalle annoncé « à 90 % » doit contenir la vraie valeur ~90 % du temps. Cette propriété se vérifie par simulation Monte-Carlo contre une vérité connue ; c'est la réalité qui juge l'honnêteté de l'incertitude, pas la réponse. La ligne rouge est la **sur-confiance** (annoncer plus de certitude qu'on n'en a), traitée comme aussi inacceptable qu'un faux dans le borné.

La famille regroupe une cinquantaine de modules, purs Python et sans dépendance, organisés autour de ce même juge.

### Le juge transverse : mesurer l'honnêteté de l'incertitude

`calibration` est le « mètre-étalon » du domaine : il prend des couples `(confiance, justesse)` et rend un verdict — `CALIBRE`, `SURCONFIANT`, `SOUSCONFIANT` ou `ABSTENTION` quand les cas sont trop peu nombreux pour juger. Il fournit les métriques standard (score de Brier, ECE/MCE, diagramme de fiabilité, écart signé) et juge aussi les intervalles via leur couverture nominale.

```python
calibration.est_calibre(confiances, justesses)        # verdict + métriques
calibration.verdict_couverture(intervalles, verites, nominal=0.9)
```

Autour de lui gravitent les instruments complémentaires : `scores_propres` (log-loss, Brier, CRPS, score sphérique) qui *classe* des prévisionnistes par des règles minimisées en espérance par la vraie probabilité — l'incitation mathématique à la sincérité ; `test_calibration` (tests de Spiegelhalter / Hosmer-Lemeshow) qui transforme la calibration en test d'hypothèse ; `predictif` qui juge une distribution prédictive complète (PIT, perte pinball) ; et `derive_calibration`, un détecteur en ligne qui alerte quand un système devient progressivement sur-confiant.

### Réparer un prédicteur mal calibré

Quand un classifieur annonce des probabilités biaisées, ces modules les recalibrent, chacun dans son régime, tous soumis au même juge :

- `classif_calibree` — recalibration isotonique (non paramétrique, monotone).
- `calibrateurs` — la trousse paramétrique : Platt (sigmoïde, robuste en petit échantillon), histogram binning, beta calibration (gère l'asymétrie).
- `temperature` — temperature scaling pour des logits multi-classes.
- `venn_abers` — prédicteur de Venn-Abers, à validité automatique.
- `multilabel` — calibration de problèmes multi-étiquettes.
- `multicalibration` — calibration simultanée sur des sous-groupes.

### Prédiction conforme : des intervalles à couverture garantie

La garantie la plus propre du non-borné. `conformal` produit un intervalle (régression) ou un ensemble de classes (classification) qui contient la vraie réponse **au moins (1−α) du temps, sans aucune hypothèse de loi** — seulement l'échangeabilité des données. Si le jeu de calibration est trop petit pour garantir le niveau demandé, le module **s'abstient** plutôt que de fabriquer un intervalle fini trompeur.

```python
conformal.intervalle_conforme(residus_cal, prediction, alpha=0.1)   # couverture >= 90 %
```

Les variantes couvrent les cas réels : `conformal_normalise` (couverture *conditionnelle* sous hétéroscédasticité, via Mondrian par groupe ou score normalisé), `conformal_jackknife` (jackknife+), `conformal_label` (Mondrian par classe), `conformal_quantile` (CQR). Deux applications directes s'appuient sur le même mécanisme : `risque_conforme` (contrôle du risque, p. ex. borner le taux de faux négatifs) et `nouveaute` (détection hors-distribution par p-value conforme, avec fausse alarme contrôlée).

### Estimer avec des intervalles honnêtes

`incertitude` est la brique de base : intervalles de confiance par bootstrap / Wilson (moyenne, proportion, comparaison, tendance, détection d'anomalie), sans hypothèse de loi, avec abstention si l'échantillon est trop petit.

```python
incertitude.estime_moyenne(echantillon, confiance=0.95)
```

S'y ajoutent des estimateurs spécialisés qui évitent chacun un mode de sur-confiance précis : `meta_analyse` (effets aléatoires DerSimonian-Laird — intègre l'hétérogénéité inter-études que le modèle à effet fixe sous-estime), `valeurs_extremes` (risque de queue / VaR par loi de Pareto généralisée), et `surdispersion` (comptages Poisson vs binomiale négative, quand la variance dépasse la moyenne).

### Combiner et agréger l'évidence

Fusionner plusieurs sources en une croyance calibrée. `bayes` met à jour en log-odds à partir d'un **prior explicite obligatoire** (jamais d'uniforme caché), refuse les vraisemblances dégénérées (p=0/1) qui affirment l'impossible, et documente son caveat : des indices corrélés rendent la postérieure sur-confiante — le module l'expose au lieu de le cacher (`posterior_correle`).

```python
bayes.posterior(prior, indices)
```

Le reste de la famille couvre les autres schémas de combinaison : `bayes_sequentiel` (Beta-Bernoulli en ligne), `bma` (moyennage bayésien de modèles), `robust_bayes` (Bayes robuste par ε-contamination), `pac_bayes` (bornes de généralisation), `ensemble_calibre` (stacking de prévisionnistes), `opinions` (pools linéaire/logarithmique pondérés par fiabilité), et `agregation_previsions` qui pondère chaque prévisionniste par son Brier passé puis *extrémise* l'agrégat pour défaire la sous-confiance de la moyenne naïve. `revelation_bayesienne` illustre la dépendance au protocole (Monty Hall), où l'estimation naïve échoue.

### Incertitude imprécise : encadrer sans inventer de précision

Quand la connaissance est trop pauvre pour une probabilité ponctuelle, ces modules la représentent honnêtement par un **intervalle** de probabilité, l'ignorance vivant explicitement dans l'écart. `croyance_dempster_shafer` associe à chaque hypothèse un couple `[croyance, plausibilité]` et démasque le paradoxe de Zadeh (la normalisation de Dempster peut amplifier une hypothèse marginale jusqu'à une certitude absurde sur des sources en conflit). `possibilite` (Zadeh, Dubois-Prade) encadre toute probabilité compatible par `[nécessité, possibilité]`. `p_box` (boîtes de probabilité), `prevision_walley` (prévisions inférieure/supérieure) et `choquet` (intégrale de Choquet, mesures non-additives) complètent ce paradigme « hors-calibration ».

### Décider sous incertitude et ambiguïté

Choisir une action quand on n'a pas une seule probabilité mais un ensemble (crédal). `decision_ambiguite` implémente les critères rationnels : maxmin EU (Gilboa-Schmeidler, plancher garanti sur le pire cas), maxmax, α-maxmin de Hurwicz, regret minimax de Savage.

```python
decision_ambiguite.choisir(credal, actes, "maxmin")
```

Il démasque son mode d'échec : optimiser l'utilité espérée sous le seul « centre » du crédal ignore l'ambiguïté et peut choisir un acte fragile. `ellsberg` rationalise l'aversion à l'ambiguïté, `smooth_ambiguity` la modélise en continu (Klibanoff-Marinacci-Mukerji), `info_gap` fournit la décision robuste de Ben-Haim, et `optimisation_bayesienne` propose le prochain point à évaluer via un surrogate gaussien (acquisitions UCB / EI).

### Corriger les biais et raisonner sur les causes

`causal` estime un effet moyen de traitement (différence de moyennes, IPW). `donnees_manquantes` gère l'imputation (cas complet, simple, multiple). `regression_moyenne` explique la régression vers la moyenne de Galton (un rebond attribué à tort à une intervention), et `bertrand` illustre comment une probabilité géométrique dépend de la manière de tirer — un piège de définition mal posée. `confidentialite_differentielle` complète le domaine côté mécanisme de bruit (Laplace, ε-DP, composition).

### Garantie commune

Tous ces modules partagent le même contrat, hérité de la calibration : **on ne certifie jamais qu'une estimation isolée est juste — on garantit que l'incertitude annoncée est calibrée** (couverture nominale respectée, sur-confiance interdite), et **on s'abstient explicitement** dès que les données sont insuffisantes pour tenir cette garantie, plutôt que de produire une fausse précision.

---

*Note de fidélité : quatre modules présents dans ce regroupement relèvent en réalité d'autres domaines et n'ont pas de rôle d'incertitude — `frame` (relation n-aire réifiée, socle de représentation), `contrainte` (solveur CSP, raisonnement), `fabrique_francais` (dataset français vérifié, langue) et `urgence_medicale` (scores cliniques établis : Glasgow, Apgar). Ils sont documentés à leur domaine propre.*

---

## Invention & besoin

Cette famille de capacités répond à l'objectif final de Provara : *par rapport à ce qui existe déjà, déterminer ce qui manque et fournir les éléments pour le construire*. Elle ne « génère » pas au hasard : elle part d'un registre de capacités connues, cherche à atteindre une cible par recombinaison, analogie ou relâchement de contrainte, et ne retient une invention que si la réalité la valide (exécution, held-out, unicité). À côté de ces moteurs de découverte, le domaine regroupe des briques d'autonomie (l'IA apprend et s'optimise seule), l'aiguillage vers le bon juge, et une série de domaines de « besoins » concrets (comptabilité, entraînement, psychométrie, citoyenneté, cuisine) où l'on calcule des faits établis plutôt qu'on ne les devine.

### Découvrir ce qui manque : le moteur d'invention

`moteur_invention` est la graine du dispositif. Étant donné un **registre de ce qui existe** (capacités connues, exécutables) et une **fonction-cible** définie par exemples + held-out adverse, il tranche en cinq statuts, tous jugés par la réalité :

- `EXISTE_DEJA` — une capacité connue reproduit déjà la cible (pas un manque) ;
- `INVENTION` — réalisable par recombinaison de briques connues, comportement nouveau, **unique** sous le spec, vérifié sur held-out → on fournit les éléments ;
- `AMBIGU` — réalisable mais le spec est sous-déterminé (≥2 fonctions le satisfont) → renvoie une sonde discriminante au lieu de committer ;
- `BRIQUE_MANQUANTE` — cohérente mais aucune recombinaison connue ne la réalise = frontière, un atome neuf est requis ;
- `INCOHERENT` — exemples contradictoires → HORS.

Une cible non tranchée en `INVENTION` ne produit jamais un faux ; elle retombe sur l'un des quatre autres statuts.

```python
verdict = moteur_invention.examine_cible("somme_carres", "x", exemples, held_out)
```

`rapport_invention` est la surface « produit » : il agrège le moteur (et le substrat physique) en trois sections actionnables — **A. réalisables maintenant** (recombinaisons vérifiées + éléments à construire), **B. à préciser** (cibles ambiguës, ce que la réalité doit trancher), **C. frontières** (là où un principe neuf est requis, classé par levier). Il n'a aucune logique de vérité propre.

```python
rap = rapport_invention.rapport(corpus_code, paires_physiques)
print(rapport_invention.texte(rap))
```

### Les gestes de l'invention : assembler, analogiser, relâcher, orchestrer

Ces briques incarnent les manières dont un humain invente sans jamais violer une loi.

- **`transfert`** — l'assembleur : il compose les leviers honnêtes d'un besoin (canaux du corps, principes jugés, stratégies naturelles) en combinaisons inédites, chacune servie comme *supposition* (atome génératif), jamais comme fait. Une garde physique intégrée exclut tout candidat contenant un principe réfuté ou sans puits de chaleur nommé ; un besoin inconnu → HORS, de sorte que le manque devient visible.
- **`structure_mapping`** — l'analogie inter-domaines : deux ensembles de relations (source, cible) sont mis en bijection sur les objets en préservant les prédicats. Une analogie n'est retenue que si elle préserve réellement la structure ; sinon `None`. Le score est la couverture factuelle des relations alignées.
- **`relaxation`** — l'esprit TRIZ : sur un problème sur-contraint (CSP insatisfiable), elle cherche le **plus petit** ensemble de contraintes à retirer pour le rendre soluble, et vérifie la solution du CSP réduit. Si déjà satisfiable → `[]`.
- **`orchestrateur_invention`** — le capstone : il fait dialoguer les six gestes divergents (apprendre une loi, lever une contrainte, transférer une analogie, arbitrer un compromis Pareto, expliquer des observations par abduction, planifier un procédé) via un blackboard. Il n'a aucune logique de décision propre : il ne poste que des sorties non-`None`, abstient au premier mode qui rend `None`, et rapporte la trace auditable.

```python
mapping = structure_mapping.trouve(source, cible)   # None si aucune structure ne s'aligne
conflit = relaxation.conflit(csp)                    # noms des contraintes à relâcher, [] ou None
```

### Apprendre et s'améliorer seul

Un second groupe retire l'humain de la boucle de découverte et d'optimisation, toujours sous jugement de la réalité (déterminisme, totalité sur le domaine sondé, comportement nouveau, généralisation sur held-out).

- **`auto_invention`** (`MoteurAutoInvention`) mute son propre répertoire et garde tout atome que la réalité valide, sans qu'on lui dise quoi chercher.
- **`auto_apprend`** (`MoteurAutonome`) étend ce moteur avec un vocabulaire plus profond (combinateur binaire `op(f(x), g(x))`) et une résolution *confiante* : il rassemble tous les candidats qui passent les exemples ; s'ils s'accordent sur des sondes variées → solution robuste, sinon il renvoie l'entrée discriminante (apprentissage actif) plutôt que de commettre un faux.
- **`auto_optimise`** cherche, pour une solution déjà vérifiée, une solution équivalente mais strictement moins coûteuse (nombre de passes O(n) sur l'entrée, puis taille d'AST), et ne l'adopte que si le juge et les sondes adverses confirment l'équivalence — récursivement jusqu'au point fixe. Au pire elle ne change rien.
- **`bibliotheque_invention`** est la phase « sommeil » (esprit DreamCoder) : elle promeut une abstraction réutilisée en capacité nommée de la bibliothèque de « ce qui existe » (une cible passe alors de `INVENTION` re-dérivée à `EXISTE_DEJA`), en vérifiant qu'aucune cible solvable ne régresse.

### Aiguiller et répondre sans inventer

- **`classifieur_domaine`** est le keystone : pour une demande, il décide quelle contrainte de réalité s'applique et bascule le bon juge (nécessité → exécuteur/calcul ; physique/passé/convention → base de faits ; règle posée → moteur de règles ; non-borné → abstention). Ce n'est pas un oracle mais un aiguilleur : seules les branches vérifiées émettent une valeur, donc une erreur de classification ne produit jamais un faux, au pire un « je ne sais pas ».
- **`repond`** est la couche conversationnelle de l'interface : rendre l'assistant capable de répondre (`pret`, `est_fallback`, `repond`) sans jamais inventer.

```python
reponse = classifieur_domaine.repond(demande)
```

### Cadrage et démonstration

- **`mesure_richesse`** produit la carte des capacités (richesse × puissance) — un cadrage, explicitement pas une validation.
- **`demo_verax`** est la démonstration « ou il sait, ou il le dit » : un jeu de questions calculées illustrant la posture d'exactitude/abstention.

### Domaines de besoins concrets

Enfin, plusieurs modules traitent des besoins humains directs par formules et catalogues **établis**, le mécanisme étant exact et jamais deviné :

- **`comptabilite`** — règles comptables : équation du bilan, résultat net, fonds de roulement, ratio de liquidité, partie double.
- **`entrainement`** — physiologie de l'entraînement : 1-RM d'Epley, fréquence cardiaque max, zone cible de Karvonen, estimation de VO₂max.
- **`psychometrie`** — validité/fiabilité des tests : QI standardisé, rang percentile, alpha de Cronbach, erreur standard de mesure.
- **`citoyennete`** — catalogue établi des droits et devoirs (catégorie, est-un-droit/devoir, âge de la majorité civique) — pas une invention.
- **`techniques_culinaires`** — classification bornée par mode de transfert thermique et températures de référence (mode et milieu de cuisson, plage de Maillard, point de fumée).
- **`maximum_entropie`** — principe du maximum d'entropie de Jaynes : la distribution la moins engagée compatible avec des contraintes connues.

### Garantie commune

Tout le domaine partage la ligne rouge FAUX=0 : une invention n'est affirmée qu'après réalisation vérifiée (juge, held-out), unicité comportementale et nouveauté ; les orchestrateurs et rapports ne synthétisent aucune conclusion au-delà de ce que chaque brique a vérifié ; et faute de preuve, la sortie est une abstention informative (`None`, HORS, sonde discriminante, ou « à préciser ») plutôt qu'un faux. L'efficacité physique d'un candidat cohérent reste, elle, un « concept à évaluer », jamais un fait.

---

## Mémoire & conversation

Cette famille de capacités répond au « fossé de l'intelligence éphémère » : un agent règle un problème, la fenêtre de contexte se vide, et le savoir part avec elle. Provara y oppose une **mémoire de dialogue persistante, souveraine et exacte**, une **interface locale** pour la consulter, et un module de **décision séquentielle contextuelle** calibrée. Le fil commun est le même que dans tout le projet : on ne restitue que ce qui a réellement été dit (verbatim) ou rien, et on s'abstient quand les données manquent — jamais d'invention.

### Retenir et retrouver le dialogue (`conversation`)

`conversation.py` fournit `MemoireConversation`, une mémoire de dialogue **par conversation**, model-free, 100 % locale (aucun réseau, aucune IA tierce). Chaque tour (qui parle, quoi, quand) est ajouté en append-only sur disque (JSONL), durable et horodaté ; il survit aux runs, aux `/clear` et aux redémarrages.

Les quatre gestes principaux :

- **Déposer** un tour : `MEMOIRE.ajoute("bug-42", "user", "NPE au login", scope="public")`.
- **Reprendre** une conversation verbatim, ou seulement sa fenêtre récente : `MEMOIRE.reprend("bug-42", n=5)` (les 5 derniers tours, dans l'ordre).
- **Rappeler** ce qui est pertinent sans jamais recharger tout l'historique : `MEMOIRE.rappelle("login NPE", k=3)`. Un index inversé (token → tours) ramène les k tours pertinents d'un historique arbitrairement long, pondérés idf ; la mémoire croît, mais le coût de rappel non. Sans `conv_id`, le rappel cherche dans **toutes** les conversations — c'est le « dépôt-pour-le-suivant » : un agent B retrouve la réponse qu'un agent A a validée.
- **Oublier** au sens RGPD : `MEMOIRE.oublie("bug-42")` supprime intégralement une conversation (mémoire + index + fichier), un effacement réel et non un simple drapeau.

Deux garde-fous structurels sont intégrés : une **frontière public/privé** (chaque conversation a un `scope`, « prive » par défaut ; le rappel public ne voit jamais le privé) et la **souveraineté** (les fichiers ne quittent pas la machine). Des fonctions de commodité au niveau module (`ajoute`, `reprend`, `rappelle`) exposent directement l'instance partagée.

### Interface locale souveraine (`interface/serveur`)

`interface/serveur.py` est un mince serveur web bâti sur la seule bibliothèque standard (`http.server`), en **localhost uniquement**, sans framework ni build. Il ne réimplémente pas le stockage : il appelle l'API de `conversation.MEMOIRE`, et importe volontairement `conversation` (léger) et non `ia` (pour éviter de charger le lecteur et le risque de saturation mémoire).

Il permet de :

- lister et lire l'historique verbatim : `liste_conversations(memoire)`, `lire_conversation(memoire, conv_id)` ;
- créer une conversation et y écrire : `nouvelle_conversation(memoire, conv_id)`, `ajoute_message(memoire, conv_id, texte)` — ce dernier enregistre le tour utilisateur, génère une réponse *sound* (issue de la mémoire réelle, jamais une reformulation), puis renvoie l'état relu ; l'ordre de calcul est choisi pour que l'assistant ne se cite pas sa propre question ;
- distinguer **archiver** et **oublier** : `archive_conversation` / `desarchive_conversation` masquent une conversation de l'historique affiché **sans effacer les données** (l'IA continue de s'en souvenir, `rappelle` la voit toujours ; réversible), tandis que `oublie_conversation` est une **purge définitive** (mémoire + index + fichier + entrée d'archive). Le geste courant de l'UI archive ; l'oubli n'est utilisé que pour effacer pour de bon.

### Décision séquentielle contextuelle (`bandit_contextuel`)

`bandit_contextuel.py` implémente un **bandit contextuel LinUCB** (Palier 2). À chaque tour un contexte `x` arrive et l'on choisit un bras dont la récompense dépend du contexte. Un agent glouton (estimation ponctuelle, exploration nulle) est **sur-confiant** : il se verrouille sur un bras qui « semble » bon et accumule un regret linéaire. LinUCB conserve une largeur de confiance honnête sur chaque estimation et joue le score optimiste `θ̂_a·x + α·√(xᵀ A_a⁻¹ x)` : le bonus est grand quand un bras est peu testé dans cette direction (on explore), petit quand il est bien estimé (on exploite), ce qui donne un regret sous-linéaire.

La classe `Agent` (K bras, `alpha=0` ⇒ glouton, `alpha>0` ⇒ LinUCB) expose `choisir(x)`, `maj(a, x, r)`, `score`, `largeur`. La façade `analyse(thetas, contextes, rng, alpha)` compare LinUCB au glouton et renvoie `(ANALYSE, {...})` ou `(ABSTENTION, raison)` si les données sont insuffisantes. Le module est en Python pur (algèbre linéaire maison, générateur aléatoire seedé requis).

### Garantie commune

Comme partout dans Provara, ce domaine tient la règle FAUX=0. La mémoire de conversation **restitue le verbatim réellement stocké ou rien** (liste vide, « pas de tour pertinent »), et un tour n'est rappelé que s'il partage un token discriminant (hors mots-vides) avec la requête — aucune devinette. L'interface n'affiche que des tours réels, avec des états vides explicites. Et le bandit **s'abstient** plutôt que d'exploiter une estimation trop bruitée. La règle est toujours : dire l'exact, ou se taire.

---

## Modalités & production

Ce domaine regroupe les capacités qui permettent à Provara de **lire et produire des artefacts concrets** (fichiers, son) et de **fabriquer/valider du code de manière fiable**. Là où les autres domaines calculent des réponses, celui-ci s'occupe des *entrées-sorties* de l'IA (comprendre un fichier, générer un signal audio exact) et de la *chaîne de qualité* qui garantit qu'un code produit se comporte comme prévu face au réel. Tous les modules restent purs stdlib, souverains et hors-ligne, et appliquent la même discipline FAUX=0 : quand la réalité ne tranche pas, on s'abstient plutôt que d'inventer.

### Modalités d'entrée/sortie : lire des fichiers, produire du son

Deux modules donnent à l'IA un noyau *borné et vérifiable* pour manipuler des artefacts extérieurs.

- **`parseur_fichiers`** est un routeur de formats : il détermine le type d'un fichier par son extension *corroborée par les magic bytes* (jamais deviné), puis le parse en une structure exploitable. Il couvre les formats texte/structurés de la stdlib (json/csv/tsv/xml/html/ini/sqlite/zip/tar/gzip/texte). Un format inconnu ou binaire non structuré renvoie le statut `HORS` (on ne fabrique pas de contenu) ; un parse qui échoue est rapporté comme `ERREUR` honnête avec sa raison, jamais un contenu partiel silencieux.

  ```python
  parseur_fichiers.lit("donnees.csv")     # -> dict structuré
  parseur_fichiers.detecte_type("x.bin")  # -> "inconnu" au doute
  ```

- **`audio_wav`** est le noyau borné de la modalité **son** : PCM entier non compressé dans le conteneur WAV/RIFF (mono ou stéréo, 8/16/32 bits). Sa garantie est un *round-trip exact* — `encode(...)` puis `decode(...)` rendent exactement les mêmes entiers, sans perte ni approximation — vérifié par le validateur qui recalcule le signal. Les générateurs `silence`, `sinus`, `carre` produisent des échantillons déterministes et re-dérivables ; tout dépassement de la plage de quantification lève une `ValueError` (pas de clipping caché). Le module garantit l'exactitude numérique de l'échantillon, pas le fait qu'un son soit « agréable » (non-borné).

  ```python
  octets = audio_wav.encode(audio_wav.sinus(440, 1.0))  # la 440 Hz, 1 s
  audio_wav.decode(octets)                               # -> mêmes échantillons
  ```

### Fabriquer du code fiable : le juge et son écosystème de vérification

Le cœur de la « production » est une chaîne de test dont le signal vient toujours de la réalité (le code tourne ou pas), jamais d'une auto-évaluation.

- **`juge`** est la brique fondatrice : il exécute un code candidat contre des tests *cachés* dans une **sandbox isolée** (processus séparé, limites de temps et de mémoire) et rend un verdict binaire — `PASS`, `FAIL`, `TIMEOUT`, `ERROR`, `KILLED` ou `SABOTAGE` (sortie prématurée qui tente de simuler un succès, détectée structurellement par une sentinelle). Il est agnostique au langage : le spécifique est délégué à un exécuteur.
- **`fuzz`** est le crible sécurité : au lieu de « ça passe les tests ? », il demande « ça survit au réel ? ». Par **fuzzing différentiel** contre une solution de référence (l'oracle), il génère des centaines d'entrées, dont des cas aberrants, et classe chaque écart en `CRASH` (le candidat lève une exception là où la référence non) ou divergence (résultat différent). Il réutilise le juge tel quel pour exécuter le programme de fuzz.
- **`delta_debug`** minimise un reproducteur d'échec (algorithme `ddmin` de Zeller-Hildebrand) : à partir d'une entrée qui déclenche un bug, il renvoie le plus petit sous-ensemble *1-minimal* qui échoue encore (retirer n'importe quel élément fait disparaître l'échec), rendant les contre-exemples du fuzzing actionnables. Le prédicat d'échec est fourni par l'appelant : la réalité tranche.
- **`profilage`** mesure le coût *réel* d'un code (`mesure_temps`, `mesure_memoire`) et infère sa **classe de croissance** en observant l'évolution du coût quand la taille double. La classification s'appuie sur un coût déterministe (opérations comptées, pic mémoire), pas le temps mur bruité ; si les exposants empiriques sont incohérents entre doublements, elle rend `INDETERMINE` plutôt qu'une classe inventée.

  ```python
  profilage.classe_croissance(tailles, couts)  # -> "lineaire" / "quadratique" / INDETERMINE
  ```

- **`_nonreg`** est le runner de non-régression standard, incrémental et parallèle. À la manière d'un build-system, il *hashe la clôture d'imports* de chaque validateur et rejoue son verdict depuis un cache tant que l'empreinte n'a pas changé, ne relançant que les validateurs réellement impactés. La soundness est préservée : un import dynamique non résolu force « toujours relancer », et un `FAIL` n'est jamais mis en cache.

### Connaître ses propres capacités et ses sources

Deux modules donnent à l'IA une vue auditable d'elle-même.

- **`capacites`** est le manifeste explicite des capacités formule/concept : un sujet n'est « couvert » que si un mécanisme *nommé* rend la réponse connue-correcte, la preuve s'*exécutant à l'appel* sur des cas à réponse connue. Cela élimine les faux positifs lexicaux et interdit le gaming : si un mécanisme régressait, sa preuve échouerait et le sujet redeviendrait non-couvert.
- **`sources`** est le registre des sources fiables (chargé depuis `datasets/sources/registry.jsonl`) : le catalogue autoritatif d'où l'IA tient ses données (URL, domaines, relations alimentées, fiabilité, rate-limit, script d'ingestion). C'est le pendant « d'où » du lecteur, qui permettrait une ré-ingestion autonome ; il reste purement offline.

### Évaluation logique et décision robuste

- **`algebre_boole`** évalue exactement des expressions booléennes et construit leur table de vérité (parseur à descente récursive sur NOT/AND/XOR/OR/IMPL/EQUIV), d'où découlent tautologie, satisfiabilité, contradiction et équivalence. Une expression mal formée lève une `ValueError` (abstention structurelle, jamais un verdict faux).

  ```python
  algebre_boole.est_tautologie("a | ~a")  # -> True
  ```

- **`variational_preferences`** relève d'un usage plus spécialisé (Palier 2) : la décision robuste à la *mauvaise spécification* d'un modèle de référence P₀. Il évalue un acte par sa valeur robuste V(f) = min_P { E_P[u(f)] + c(P) } (cas multiplier de Hansen-Sargent, coût = θ·KL(P‖P₀)), démasquant la sur-confiance qu'il y aurait à faire pleinement confiance au modèle. Il s'abstient si θ ≤ 0 ou si P₀ n'est pas normalisé.

### Garantie commune

Tout le domaine partage l'invariant FAUX=0 : chaque module rend soit un résultat *vérifiable par la réalité* (round-trip exact, verdict pass/fail issu de l'exécution, table de vérité, minimal ré-testable), soit un statut d'abstention honnête (`HORS`, `ERREUR`, `INDETERMINE`, `ValueError`). Rien n'est jamais deviné ni fabriqué silencieusement : au moindre doute, Provara s'abstient plutôt que de produire un artefact ou un verdict potentiellement faux.

---

## Noyau & infrastructure

Cette famille ne contient pas de savoir de domaine : ce sont les mécanismes transversaux qui font tenir l'ensemble. Ils orchestrent les dizaines de moteurs spécialisés en une chaîne cohérente, aiguillent le travail vers le bon étage au moindre coût, comprennent les questions posées en langage naturel même fautives, et intègrent du savoir nouveau sans jamais introduire de faux. Chaque brique est en Python pur (stdlib), déterministe et souveraine, et applique la discipline FAUX=0 par la traçabilité et l'abstention plutôt que par la devinette.

### Orchestration et aiguillage

Deux briques transforment des moteurs isolés en un flux réel et en réduisent le coût.

Le **blackboard** (`blackboard.py`) est une mémoire de travail partagée. Chaque moteur (lecteur, loi, simulation, limite…) y POSTE ses résultats intermédiaires, d'où les autres LISENT : le flux « fait → loi → limite → écart → mécanisme → design → vérification → confiance » circule ainsi de bout en bout. Le tableau est indexé par sujet, append-only (traçable) et chaque entrée porte une provenance OBLIGATOIRE plus une confiance optionnelle ; l'arbitrage des contradictions est laissé à un autre module, le blackboard se contente de rendre les conflits visibles.

```python
bb.poste("capitale_france", "Paris", source="lecteur")
bb.lis("capitale_france")     # entrées réellement postées, ou [] — jamais inventé
bb.en_conflit("capitale_france")
```

Le **routeur** (`routeur.py`) réalise une activation parcimonieuse « façon cerveau ». Le moteur unique a environ 35 étages (zones) ; l'escalade canonique les essaie tous, du moins cher au plus cher. `RouteurZone` apprend depuis le passé une carte `clé(tâche) -> votes d'étages`, où la clé `(arité, type d'entrée, type de sortie)` est lisible avant de résoudre. Sur une nouvelle tâche il PRÉDIT les zones probables, les essaie d'abord, puis RETOMBE sur l'escalade complète des zones restantes. Règle centrale : « réordonner, jamais filtrer » — la couverture reste strictement identique à l'escalade, donc aucune perte ; à froid (aucun vote), la prédiction est vide et le comportement est exactement celui de l'escalade. Le gain (zones sautées) croît avec l'expérience et se généralise à toute tâche de même clé.

### Résolution chaînée du moteur principal

`resoudre_tout` (`resoudre_tout.py`) branche l'auto-création sur le moteur principal sans le modifier. Il appelle d'abord le moteur principal ; si celui-ci rend HORS et que la tâche est mono-argument, la boucle autonome (invention du vocabulaire manquant, recherche dirigée, chaînes) prend le relais en DERNIER RECOURS. Le candidat autonome n'est retenu que s'il passe le juge sur le visible ET sur le held-out (exigence de soundness : pas d'oracle ici, donc preuve held-out obligatoire). Le moteur de base reste intact, sans régression sur les validations existantes.

```python
resoudre_tout(point_entree, signature, exemples, exemples_held, budget)
```

### Compréhension du langage naturel (résolution floue d'entités)

`resolution.py` rend l'IA tolérante aux fautes de frappe sur l'entité d'une question (« protugal » → « portugal ») avant le lookup, sans jamais inventer. C'est un moteur ADDITIF : il lit le lecteur et la base de faits en lecture seule, sans toucher au code du lecteur. `corrige(relation, saisie)` ne corrige QUE s'il existe une correspondance unique et proche (distance d'édition sous un seuil) parmi les clés réelles de la relation ; en cas d'ambiguïté (deux candidats aussi proches) ou d'absence de proche, aucune correction — on reste HORS, honnête, et on n'essaie pas les entités très courtes (trop de voisins). Au-delà de la simple correction, le module porte une résolution NL plus riche : `resout_superlatif`, `resout_comparaison`, `resout_fiche`, `resout_liste` et `resout_nl_generique`, réunies derrière `repond_floue(question)`.

```python
resolution.corrige("monnaie", "protugal")   # -> "portugal" si correspondance unique et proche, sinon rien
resolution.repond_floue(question)
```

### Ingestion fiable et cohérence du savoir

Trois briques encadrent l'arrivée de savoir nouveau (typiquement issu de la veille) en gardant FAUX=0.

L'**extraction** (`extraction.py`) transforme du texte sale (articles, brevets) en triplets (sujet, relation, objet). C'est le point où le faux entre le plus facilement, donc l'extraction est DÉTERMINISTE par motifs exacts (regex français) : `extrait(texte)` renvoie tous les candidats avec confiance et provenance (motif + texte source), `extrait_surs(texte, seuil)` ne garde que le haut de la confiance. Une phrase qui ne matche aucun motif ne produit RIEN (abstention) ; le reste demeure candidat, à corroborer ailleurs.

La **révision de croyances** (`revision.py`) réconcilie au lieu d'empiler. Sur une clé fonctionnelle (une seule valeur vraie), `integre(nouvelle)` compare une croyance `(clé, valeur, fiabilité, date)` à celle en place et décide : garder l'ancienne, la remplacer (uniquement si fiabilité strictement supérieure, ou fiabilité égale mais plus récente) avec RÉTRACTATION tracée, ou signaler un CONFLIT indécidable (même fiabilité, même date, valeurs différentes) qu'on ne tranche pas au hasard. Jamais deux valeurs contradictoires ne sont tenues en même temps.

L'**audit des ancres** (`audit_ancres.py`) diagnostique la couverture de vérité externe : quelles relations du lecteur sont référencées par un validateur portant des ancres externes (valeurs de référence codées et vérifiées indépendamment de la source), et lesquelles ne le sont pas — candidates prioritaires à ancrer, par volume de faits décroissant. La méthode est une sur-approximation SOUND : une relation jamais mentionnée n'est certainement pas ancrée, donc la liste des non-référencées est un sous-ensemble sûr des non-ancrées. Read-only ; `audit()` renvoie un dict.

### Garantie commune

Toutes ces briques partagent la même posture FAUX=0, lisible dans leurs docstrings : provenance obligatoire (on sait toujours d'où vient un résultat), abstention (renvoyer HORS, `[]` ou rien plutôt qu'une valeur devinée), réordonnancement sans filtrage pour préserver la couverture exacte, journal append-only et rétractations tracées, et refus de tenir un fait et sa négation. L'infrastructure ne cherche pas à répondre à tout prix : elle préfère se taire à se tromper.

---

## Autres capacités

Ce domaine est le point de convergence de Provara : il rassemble d'un côté les briques *transversales* qui rendent tout le reste utilisable et honnête (le point d'entrée unifié, la politique d'abstention, le routage des candidats), et de l'autre une large collection de capacités bornées qui n'entrent dans aucune famille thématique unique — pièges du raisonnement, statistique robuste, informatique théorique, modalités de sortie vérifiables, domaines appliqués à faits établis, et la machinerie interne d'auto-apprentissage. Toutes partagent la même posture : pur Python (stdlib), déterministe, souverain/hors-ligne, et surtout FAUX=0 — au doute, on s'abstient plutôt que d'affirmer.

### Le point d'entrée unifié et la politique d'honnêteté

Le module `ia` est **la porte unique** vers tout ce qui a été bâti. Il n'ajoute aucune logique de vérité : il *orchestre* des briques déjà validées et aiguille chaque demande, par nature de réalité, vers le bon juge (nécessité/exécuteur, faits physiques/passés/conventions, non-borné → abstention, inconnu → HORS). Il renvoie une réponse *vérifiée avec sa source*, ou une abstention — jamais un faux.

```python
ia.demande(texte)          # aiguille et répond (valeur vérifiée + source, ou ABSTENTION/HORS)
ia.chimie("H2O")           # accès direct à une capacité bornée
ia.invente(nom, signature, exemples)   # EXISTE_DEJA / INVENTION / AMBIGU / BRIQUE_MANQUANTE
```

Sous cette façade, `abstention` centralise **la décision d'honnêteté** en un seul point : `decide(preuve, confiance, seuil, contradiction, impossible)` renvoie `VERIFIE`, `ABSTENTION` ou `HORS`. Le défaut est l'abstention ; on n'affirme que si la barre est franchie ; une impossibilité ou une contradiction domine tout (HORS) ; une confiance inconnue ne franchit jamais un seuil. Autour gravitent les briques de plomberie qui rendent ce routage sûr : `fait_negatif` (distinguer le faux-connu de l'inconnu), `prefiltre` et `typage` (écarter tôt les candidats), `solveur_type` (résolution dirigée par les types, « le comment » plutôt que « le plus »), `strategies` (routage de stratégie de traversée) et `cas_limites` (vérification par les bords : limites, monotonie, parité, homogénéité).

### Démasquer les pièges du raisonnement

Une grande partie du domaine (briques « Palier 2 ») ne calcule pas une valeur mais **démasque un mode d'échec du raisonnement** : elle détecte quand une conclusion naïve serait sur-confiante et le signale. On y trouve les grands paradoxes et sophismes : Simpson (inversion de tendance à l'agrégation), Allais, Berkson/collision, deux enveloppes, Parrondo, Braess, Borel-Kolmogorov, Lord, Lindley ; les biais et sophismes cognitifs : effet de cadrage, sophisme de la conjonction (« Linda »), coût irrécupérable (effet Concorde), main chaude / sophisme du joueur, malédiction du vainqueur, loi de Goodhart, inégalité de Jensen (« flaw of averages »), Pascal's mugging ; les résultats de choix collectif : jury de Condorcet, choix social (Condorcet/Arrow), Gibbard-Satterthwaite (vote stratégique) ; et les artefacts statistiques : loi de Benford, quartet d'Anscombe, biais de publication, phénomène de Will Rogers.

Le message commun est que **les données seules ne tranchent pas** : l'attitude honnête est de détecter le renversement/l'artefact et de signaler la dépendance au modèle (souvent causal), avec abstention si les données sont incohérentes.

```python
simpson.analyse(donnees, a, b)   # détecte le renversement entre strates et agrégat, et le signale
```

### Statistique robuste à couverture garantie

En miroir des pièges, un ensemble de modules fournit des **méthodes dont la couverture reste proche du nominal** là où la formule naïve « plaquée » s'effondre en sur-confiance. Intervalles de confiance : `bootstrap` (percentile et BCa pour une statistique arbitraire), `proportion_binomiale` (Wald / Wilson / Agresti-Coull), `multinomial_simultane`, `test_permutation`. Régression et filtrage robustes : `quantile_regression` (perte pinball, hétéroscédasticité), `ridge` (colinéarité), `erreurs_variables`, `kalman_robuste`, `processus_gaussien`. Détection et survie : `changepoint`, `shiryaev` (détection au plus tôt), `survie` (Kaplan-Meier sous censure). Multiplicité et sélection : `fdr_controle` (Benjamini-Hochberg), `p_hacking`, `surapprentissage`, `mdl` (longueur de description minimale), `rademacher` (borne de généralisation), `loi_puissance` (queues lourdes), `portefeuille_universel`.

```python
bootstrap.intervalle(data, stat)   # IC dont la couverture ≈ nominal, sans formule d'écart-type
```

### Informatique théorique : calculabilité, complexité, logique

Des noyaux exacts couvrent la théorie du calcul : `turing` simule une machine de Turing pas-à-pas avec **budget explicite** — dépassement → `timeout` honnête (le problème de l'arrêt étant indécidable, on n'invente pas le verdict d'un calcul non terminé) ; `arret` traite formellement le problème de l'arrêt et l'argument diagonal ; `automates` simule un automate fini déterministe ; `classes_complexite` est un catalogue de faits établis (P, NP, NP-complet, NP-difficile, indécidable) ; `preuve_propositionnelle` vérifie la validité d'inférences (modus ponens/tollens) ; `controle` juge la stabilité d'un système linéaire (table de Routh) ; `bases_donnees` implémente l'algèbre relationnelle exacte (sélection, projection, jointure, union, agrégat). `big_data` ajoute des primitives de traitement à l'échelle (MapReduce, filtre de Bloom, échantillonnage par réservoir).

### Calcul mathématique exact

Quelques modules livrent des résolutions mathématiques directes et vérifiables : `equa_diff` (solutions analytiques et méthode d'Euler, demi-vie), `trigonometrie` (fonctions et résolution de triangles : loi des cosinus, hypoténuse), `classification_surfaces` (classification des surfaces closes 2D par le genre), `pareto` (domination et front de Pareto pour l'optimisation multi-objectif).

### Modalités et formats bornés vérifiables

Provara sait produire des sorties dans des formats dont le **noyau est exact et re-vérifiable au bon octet/à la bijection près**, en refusant explicitement tout ce qui sort du domaine supporté (→ `ValueError`). `document_pdf` génère un PDF 1.4 dont la table de références croisées `xref` pointe l'offset-octet réel de chaque objet (re-scanné par le validateur) ; `braille` réalise la bijection lettre ↔ points ↔ caractère Unicode (round-trip prouvé sur l'alphabet grade 1) ; `heraldique` encode les règles fermées du blason (teintures, règle de contraste) ; `web` fait des vérifications structurelles exactes (balises équilibrées, spécificité CSS).

```python
document_pdf.ecris(doc, chemin)          # PDF structurellement valide, xref exacte
braille.texte_vers_braille("bonjour")    # bijectif ; hors domaine -> ValueError (jamais deviné)
```

### Domaines appliqués à faits établis et formules

Un ensemble de modules « science/ingénierie/société » applique des formules ou catalogues **établis**, avec abstention sur l'inconnu : `eclipses` (phases lunaires, conditions d'éclipse), `glaciologie` (bilan massique, iceberg), `mineraux` (échelle de Mohs), `pedologie` (texture des sols), `toxicologie` (DL50, index thérapeutique), `logistique` (quantité économique de commande, stock de sécurité), `industrie40` (OEE), `marketing_metrics` (CTR, ROI, CAC), `externalites` (coût social, taxe de Pigou), `systemes_politiques` et `rhetorique` (définitions et catalogues de consensus), `reseaux_neurones` (propagation avant exacte : ReLU, sigmoïde, couche dense) et `robotique` (cinématique directe, atteignabilité).

### La machinerie d'auto-apprentissage autonome

Enfin, le domaine héberge **l'atelier interne** qui permet à Provara d'accumuler des succès vérifiés et de construire ses propres briques : `store` (le magasin de succès), `boucle` et `session` (l'orchestration d'entraînement), `taches` (la matière première), `usine_donnees` et `exporte_dataset` (constituer un corpus prêt à apprendre), `mesure` et `mesure_v3b_net` (la « boîte de verre » qui mesure l'apprentissage), `exploits` et `curateur` (observatoire et validation graduée), `executeur` (couture multi-langage : Python, JS, Perl, Bash, C, C++, Rust, Go), `auto_synthese` (synthèse de briques par squelettes), `etend_savoir` et `oracle_definitions` (auto-extension du savoir par les définitions), `diable` et `carte_limites_francais` (éprouver et cartographier les limites du sans-modèle).

### Garantie commune

Malgré leur diversité, toutes ces capacités reposent sur le même contrat FAUX=0 qui ressort explicitement des docstrings : l'**abstention est le défaut** et le HORS domine (impossibilité ou contradiction avant tout) ; le **domaine est explicite** (toute entrée hors périmètre est refusée, jamais devinée) ; les sorties sont **déterministes et re-vérifiées** (structure PDF au bon octet, bijection braille, `xref` re-scannée) ; et pour les briques statistiques, la **couverture reste proche du nominal** là où la formule naïve serait sur-confiante. Provara préfère dire « je ne sais pas » plutôt que se tromper.

---


## Assistant conversationnel (2026-07 — câblé au chat)

Au-delà du moteur de faits vérifiés, Provara atteint désormais ces capacités directement en conversation, chacune s'abstenant hors de son périmètre garanti (FAUX=0) :

- **Grammaire française** (`grammaire_fr`, `formes_verbales`) : nature de chaque mot (mots-outils = ensembles finis fermés ; lexique embarqué de 19 200 mots ; formes conjuguées reconnues par modèles Bescherelle sur 116k formes), type de phrase (question/affirmation/ordre/négation) et structure sujet-verbe-objet. Ambigu/inconnu → « inconnu », jamais un tag faux.
- **Conjugaison** (`conjugaison`) : table du présent d'un verbe régulier ; abstention honnête hors périmètre.
- **Statistiques en langage naturel** (`fonction_stats_nl`) : moyenne/médiane/écart-type (exacts) et ~46 fonctions calibrées — tendance, Fermi, Benford, intervalle de proportion de Wilson, taux de Poisson, Kelly, anomalie, corrélation/pente, comparaison de groupes, effet causal, méta-analyse. Relaie l'abstention honnête quand l'échantillon est trop petit.
- **Explications de concepts/paradoxes** (`explications`) : « explique le paradoxe de Braess / Allais / Ellsberg / Kelly… » — le calcul réel de la brique, jamais une paraphrase creuse.
- **Raisonnement compositionnel** (`_compose_relations`) : compose plusieurs relations vérifiées — « continent du pays de X » = résout l'intérieur (pays de X → entité E vérifiée) puis l'extérieur (continent de E). Chaque maillon est un lookup exact ; un maillon manquant → abstention. Décuple les réponses sur la base sans ajouter de donnée. Complété par la **résolution par famille** (« pays de X » atteint la relation `pays_de_capitale`, unicité exigée).
- **Lecture de documents** : extraction de texte PDF (`extrait_pdf`, FlateDecode) et interrogation de documents longs (`lecteur_document` : passage verbatim + page + sommaire). OCR du texte imprimé net (`ocr`, binarisation Otsu) — **majuscules ET minuscules** (la position verticale dans la ligne distingue la casse) ; glyphe non reconnu → « ? ».
- **Moteur d'invention** (`besoin`/`invention_atomes`) : « comment rafraîchir une pièce sans climatiseur » → la reformulation physique du besoin.
- **Scanner d'inventions** (`inventions_composites`/`substrat_reel`) : « quelles inventions/relations manquent pour les pays ? » → attributs composites dérivables (relation nouvelle « pont ∘ cible » avec témoin re-vérifié sur les 71,9 M faits), ex. « pays → (capitale ∘ population_ville) ». FAUX=0 : chaque composite est un fait re-vérifié ; utilité non jugée.
- **Géographie** : distance et cap initial entre deux lieux connus.
- **Recherche web multi-sources** avec vérification du contexte sur site (Mojeek/Bing/DuckDuckGo), chaque passage attribué et lié.
- **Apprentissage de patrons** (`apprentissage_patrons`) : apprend les reformulations de l'utilisateur et induit des règles de substitution de mots qui généralisent (FAUX=0 : ré-aiguillage seul, la réponse reste vérifiée).
- **Système de confiance** (`confiance`) : une correction utilisateur ne prend effet que si elle s'appuie sur une **source** — Provara challenge les affirmations nues (« sur quelle source t'appuies-tu ? ») et n'écrase jamais une vérité sans source ; les corrections sont attribuées à leur source. « Oublie ce site X » bannit un domaine des recherches.
- **Multilingue** (`langue`) : les questions factuelles posées en anglais/espagnol/allemand/italien/portugais reçoivent une réponse dans la langue (capitale/population/monnaie/langue/superficie de pays), résolues par le pipeline vérifié français. Interface localisée dans ces 6 langues.
- **Traduction FR↔EN** (`traduction`) : traduction mot-à-mot **assistée** — dictionnaire curé embarqué (mots courants, hors-ligne) + lexique cross-lingue `concept_du_mot` de la base complète (~165k termes). FAUX=0 : un mot inconnu est gardé tel quel et signalé, jamais inventé ; sortie étiquetée « mot-à-mot assisté ». Pas de fluidité/réordonnancement (frontière honnête).
- **Fraîcheur** (`_est_volatil`) : une question à marqueur temporel (« président **actuel** », « **dernier** vainqueur », « en 2026 ») préfère la source **live** (Wikidata) à la base statique qui peut être périmée — quand le web est autorisé ; repli sur la base sinon. Réponse fraîche et attribuée.
- **Vie quotidienne** (`_cap_quotidien`, `meteo`) : **météo en direct** (source structurée Open-Meteo, sans clé) — « quel temps fait-il à Toulouse ? » → relevé réel attribué et daté ; heure et date locales (horloge machine). Sans ville, Provara **demande la ville** et le tour suivant qui la nomme (« À Brives ») **complète** la question — une vraie conversation, pas du question-réponse. Web coupé → refus honnête actionnable.
- **Visite d'un site nommé** (`_cap_site`, `apercu_site`) : « regarde le site X.fr et dis-moi ce que tu en penses » → Provara **va lire la page** (HTTPS puis repli HTTP, jamais d'adresse locale/IP), en rapporte le titre et le passage le plus « prose » (les menus de navigation sont écartés), attribué et lié. Un avis demandé sur le site → il cite la page, il ne juge pas (FAUX=0).
- **« Mon avis »** (`_cap_avis`, `_cap_avis_critere`, `_reponse_opinion` — via `pareto`/`choix_social`) : sur du non-tranché, Provara donne un avis **construit, pas ressenti**. Comparaison chiffrée de 2+ candidats (« meilleure destination entre la France, l'Italie et l'Espagne ? ») → chaque critère vérifié de la base vote, verdict par **dominance de Pareto** (avis robuste) ou **Condorcet/Borda** (3+ candidats), avec la **sensibilité** affichée. Le tour suivant « mon critère n°1 est le PIB par habitant » **re-tranche** sur ce critère. Débats sans chiffres (« que penses-tu des voitures électriques ? ») → les deux faces sourcées + avis **conditionnel** au critère de l'utilisateur. Règle de décision toujours affichée, avis toujours falsifiable.
- **Apprentissage des faits web** (`faits_appris`) : quand Provara résout un fait sur une source **structurée** (Wikidata), il l'**apprend** — rangé en local (`~/.verax`), typé source + date — et le ressert ensuite **sans réseau, même Internet coupé**, toujours attribué et daté (« appris de Wikidata le 2026-07-06 »). Frontière FAUX=0 stricte : **seul le structuré est appris** ; le texte libre (Wikipédia) reste « rapporté », jamais appris. Un fait resservi est un instantané daté, pas une vérité intemporelle. Le diagnostic affiche le nombre de faits appris.
- **Registre de capacités auto-prouvé** (`capacites`) : 280 capacités de raisonnement (causalité, lois physiques, simulation, Pareto, Condorcet, révision de croyances, lexique…) portent chacune une **preuve à réponse connue** exécutée en direct — la commande « diagnostic » affiche « capacités prouvées à l'instant : 280/280 ». Un gate d'atteignabilité (`valide_cablage`) garantit que **tout module construit est câblé au produit** (zéro orphelin) : un module non branché met la suite au rouge.
