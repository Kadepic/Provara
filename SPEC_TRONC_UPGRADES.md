# PASSE D'AMÉLIORATION ATOMIQUE — pousser chaque atome du tronc à l'excellence

> Compagnon de `SPEC_TRONC_COMPREHENSION.md`. Chaque upgrade = une technique NOMMÉE (actionnable, pas du
> hand-wave), le GAIN (puissance / exactitude / coût), les COMBINAISONS/FUSIONS, et un CAVEAT honnête.
> **Discipline invariante** : tout composant appris/exotique PROPOSE ; le store explicite vérifié DISPOSE
> (FAUX=0 préservé). Ces upgrades sont des CANDIDATS à évaluer empiriquement, banc vert, pas des décisions figées.

---

## ★★★ U1 — LA FUSION MAJEURE : substrat VECTEUR-SYMBOLIQUE (VSA / calcul hyperdimensionnel)
**Touche : §6 substrat signal-natif · §7 faisceau + liaison · §10 sortie · §14 société · coût/frugalité.**

Représenter chaque sens comme un **hypervecteur** (D ≈ 10⁴, composantes quasi-orthogonales). Trois opérations
algébriques exactes et *explicites* :
- **Binding** (rôle↔remplisseur) : convolution circulaire / XOR / produit élément-par-élément → **composition en
  O(D)**, pas d'explosion combinatoire (résout la liaison §7 par de l'algèbre, pas de l'énumération).
- **Superposition** (somme) : **le faisceau ENTIER = UN hypervecteur** tenant tous les candidats en parallèle,
  « nettoyé » par un *resonator network* pour le dé-liage → la population parallèle du §7 réalisée nativement.
- **Permutation** : encode l'ordre/la séquence (le narratif, la prosodie §14).

**GAINS cumulés :**
- **Puissance** : compositionnalité + systématicité symbolique ET similarité/robustesse distribuée réunies.
- **Coût (énorme)** : opérations bitwise, matériel-friendly → le théorème thermodynamique (§15) poussé au bout ;
  le « 30 Mo / 0 GPU » devient encore plus frugal et rapide.
- **Robustesse native** (§16) : dégradation gracieuse au bruit intrinsèque au distribué.
- **Modalité-agnostique** (§6) : *tout* signal (texte/audio/image/vibration) s'encode uniformément en hypervecteur
  → un seul substrat pour toutes les espèces.
- **EXPLICITE/inspectable** : contrairement aux poids de LLM ; c'est le front « statistiques totales explicites »
  (F) réalisé — d'où l'intérêt de « Hyperdimensional Probe » qui *décode* les représentations LLM en VSA.
- **Fusion avec le split perception/raisonnement (MPMWorlds)** : la perception apprise **produit des
  hypervecteurs**, le cœur explicite fait l'**algèbre** dessus → « Attention as Binding » (2025) montre que
  l'attention EST du binding vecteur-symbolique → un pont propre entre l'appris (propose) et l'explicite (vérifie).

**CAVEAT (FAUX=0 préservé)** : la superposition a une capacité finie (crosstalk) → resonator/block-codes pour le
dé-liage propre, ET **le VSA est la représentation de TRAVAIL, jamais la vérité-terrain** : le store explicite
(72 M faits vérifiés) reste le juge. Le VSA propose des candidats et compose vite ; l'ancrage (§9.4) vérifie.
Sources : [LARS-VSA](https://arxiv.org/abs/2405.14436), [Attention as Binding](https://arxiv.org/pdf/2512.14709),
[HDC interpretable](https://arxiv.org/pdf/2402.17572), [Hyperdimensional Probe](https://arxiv.org/pdf/2509.25045).

---

## U2 — SUBSTRAT DE FAITS : structures SUCCINCTES (frugalité poussée à la borne de Shannon)
**Touche : §5 persistance · §22 frugalité · coût.**

Remplacer/compléter le stockage colonnaire par des **structures succinctes** : **wavelet trees + rank/select**
(requête *sans décompression*, espace proche de la borne info-théorique), **FM-index** (recherche de sous-chaîne/
relation en temps optimal), **compressed graph** (BFS/adjacence en espace comprimé).

**GAINS** : encore moins de RAM que les 30 Mo actuels · requête plus rapide · plus de faits résidents. Exotique
récent : **Dynamic Wavelet Matrix co-index** (« Hippocampus ») = recherche *en domaine comprimé* + reconstruction
sans perte, scalant linéairement avec l'historique + écritures en flux → candidat direct pour la **mémoire
persistante** (§5) et le **ré-ancrage anti-dérive** (§9) sur de très longs historiques.
Sources : [Succinct DS review](https://arxiv.org/pdf/2204.12468), [Memanto typed semantic memory](https://arxiv.org/pdf/2604.22085),
[LeCo learned compression](https://arxiv.org/pdf/2306.15374).

---

## U3 — COMPRENDRE = COMPRIMER, rendu ALGORITHMIQUE (induction de grammaire par MDL)
**Touche : §3.1 · §4 · §6.3 décodage inconnu · §9 REPRÉSENTER.**

Le « comprendre = comprimer » n'est pas qu'une métaphore : c'est un **algorithme d'induction**. Concrètement :
**induction de grammaire non supervisée par MDL** (minimiser la longueur de description = notre objectif exact),
lignée Solomonoff → ICMAUS (compression par alignement multiple/unification/recherche) → **inversion transduction
grammars** (MAP bayésien OU MDL). Travaux récents relient l'apprentissage de langages formels par réseaux et le
MDL, et l'**induction bayésienne de programmes** *découvre des motifs cross-langues déjà trouvés par les
linguistes* — exactement le décodage d'un système inconnu (§6.3), avec des sorties **inspectables**.

**GAIN** : le décodage d'un langage inconnu (la vision all-species) obtient un **objectif chiffrable et un
algorithme principiel** (minimiser MDL), pas une heuristique. **Fusion U1×U3** : induire la grammaire *dans*
l'espace hyperdimensionnel (binding = règles de composition) → induction + représentation dans le même substrat.
Sources : [Transduction grammar MDL](https://aclanthology.org/W13-2810/),
[ICMAUS compression](https://arxiv.org/pdf/cs/0302015), [Bayesian program induction of language](https://pmc.ncbi.nlm.nih.gov/articles/PMC9427767/),
[MDL neural formal learning](https://arxiv.org/pdf/2505.13398).

---

## U4 — LIAISON optimisée (propagation de contraintes n-aire) + sélection par MDL
**Touche : §7 liaison.**

Concret : **AC-3 / AC-4** (arc-cohérence) pour la liaison binaire ; **GAC (generalized arc consistency) / hyper-arc
consistency** pour les relations n-aires (le `frame.py` réifié + la leçon « RAG échoue à l'extraction : choisis la
forme, hypergraphe compris »). La sélection de la bonne liaison = **MDL sur la forêt d'analyses** (un chart parser
scoré par longueur de description) → « la compression sélectionne la liaison » rendu concret. **GAIN** : liaison
polynomiale, jamais l'explosion du produit ; supporte l'hypergraphe/temporel/spatial que la question impose.

---

## U5 — SÉQUENCEUR & CALIBRATION avec GARANTIES (conformal + allocation adaptative de calcul)
**Touche : §7 confiance · §11 arrêt optimal/anytime · §12 utilité/observabilité.**

Remplacer la calibration « heuristique » par la **prédiction conforme** : intervalles/ensembles à **couverture
garantie** (statistique, pas devinée) → la « confiance chiffrée » du candidat (§7) et l'incertitude de U (§12)
obtiennent une garantie. Et pour le séquenceur : **allocation adaptative de calcul au test-time** (2025) +
**conformal test-time scaling** bornent *combien* la machine « pense » avec garantie → l'arrêt optimal (§11)
devient rigoureux. « Thought calibration » = arrêter de raisonner *avec confiance*.

**GAIN** : le « quand s'arrêter / combien penser » et la confiance passent d'heuristiques à **garantis** ; couverture
tenue même sous dérive (continual/active conformal) = renforce la robustesse (§16). **Fusion U5×U1** : la
superposition VSA donne une mesure de similarité/densité *native* pour le score de conformité.
Sources : [Async test-time scaling conformal](https://arxiv.org/html/2509.15148v1),
[Thought calibration](https://arxiv.org/html/2505.18404v1), [Adaptive test-time compute allocation](https://arxiv.org/html/2604.14853v1),
[Conformal continual TTA](https://arxiv.org/pdf/2502.02998).

---

## U6 — MEMBRANE : non-distorsion comme RATE-DISTORTION (§10.3)
**Touche : §10.3 membrane.**

Formaliser la sortie comme un problème de **rate-distortion / information bottleneck** : minimiser le *débit*
(longueur du message = coût récepteur) **sous la contrainte de distorsion** « inférences licenciées du récepteur ⊆
vérité ». La théorie donne le tradeoff optimal. **GAIN** : la « compression au delta sans distordre » devient un
optimum calculable, pas un point-fixe artisanal. **Fusion U6×U5** : la garantie conforme fixe le niveau de
distorsion acceptable (couverture) → membrane *coverage-guaranteed*.

---

## U7 — REORDONNANCEMENT : le pipeline comme UNE minimisation (au lieu d'étages séquentiels)
**Touche : §9 pipeline.**

Plutôt que Percevoir→Représenter→…→Composer en série, poser **une seule fonction objectif** = minimiser
(longueur de description + erreur de prédiction) **sous la contrainte d'ancrage** (FAUX=0 dur). C'est le principe
d'**énergie libre** (Friston) mais **explicite et contraint** — perception (propose) et raisonnement (vérifie)
deviennent deux termes d'*une* optimisation, résolue par relaxation. **GAIN** : moins d'étages, moins de latence,
convergence conjointe ; l'insight/« aha » = un saut vers un minimum global plus bas (transition de phase §16).
**CAVEAT** : garder la contrainte d'ancrage DURE (le store) pour que la minimisation ne « triche » jamais.

---

## U8 — SOCIÉTÉ DE MACHINES : consensus par SUPERPOSITION (§14, ④)
**Touche : §14 société · fork/réfutation §9.**

Avec U1, le vote d'une nuée de machines = **bundling** de leurs hypervecteurs : la majorité survit, le crosstalk
s'annule → un mécanisme de consensus/marché **natif et quasi-gratuit** (au lieu d'un protocole lourd). **GAIN** :
le fork+réfutation (§9) et la société (④) deviennent une opération algébrique O(D) ; « marché de confiance » réalisé
par la géométrie hyperdimensionnelle.

---

## U9 — MODE FICTION / HYPOTHÉTIQUE (gouffre ouvert §18) : mondes possibles étiquetés
**Touche : §18 mode fiction.**

Concevoir le raisonnement contrefactuel/fictionnel comme un **contexte hypothétique estampillé** (possible-worlds
semantics) : un sous-store *temporaire* où l'on peut poser du faux-balisé, avec `causalite`/do-calcul pour
propager, et une **barrière étanche** vers le store vrai (rien ne fuit vers les faits). **GAIN** : entretenir une
fausseté pour raisonner (fiction, planification, « imagine si ») SANS jamais l'affirmer → étend FAUX=0 proprement.

---

## U10 — DES TESTS pour valider chaque upgrade (mesurer l'excellence, pas la supposer)
- **U1 (VSA)** : test de capacité (combien de candidats en superposition avant crosstalk) ; test de dé-liage
  (resonator) ; ablation coût (bitwise vs dense).
- **U2 (succinct)** : RAM & latence de requête vs colonnaire actuel, sur les 72 M faits.
- **U3 (MDL)** : **ratio de compression comme métrique de compréhension** — un système mieux compris se comprime
  davantage ; suivre le MDL sur held-out.
- **U5 (conformal)** : test de **couverture** (l'ensemble prédit contient-il la vérité au taux annoncé ?).
- **U7 (objectif unique)** : latence & justesse vs pipeline en étages ; convergence.
- Transverse : chaque upgrade doit **passer les bancs existants inchangés** (168/168, 166/166…) — un upgrade qui
  régresse un comportement vérifié est rejeté, quelle que soit sa beauté théorique.

---

## SYNTHÈSE — la pile d'excellence
- **Représentation** : hypervecteurs (U1) sur store succinct vérifié (U2) — explicite, frugal, compositionnel,
  robuste, modalité-agnostique.
- **Compréhension** : induction MDL (U3) + liaison par contraintes n-aires sélectionnées par compression (U4),
  possiblement en une minimisation unique contrainte-par-l'ancrage (U7).
- **Décision** : séquenceur à calcul adaptatif + confiance **conforme garantie** (U5) ; sortie rate-distortion
  coverage-guaranteed (U6).
- **Collectif & extension** : consensus par superposition (U8) ; mode fiction étanche (U9).
- **Coût** : bitwise (U1) + succinct (U2) + cristallisation (§15) + lazy/anytime (§11) = frugalité poussée à la
  borne de Shannon, sans GPU — l'anti-thèse de la guerre des térawatts.

**Invariant de toute la passe** : l'exotique/l'appris **propose**, l'explicite ancré **vérifie** (FAUX=0). Rien
n'est adopté sans banc vert. On mesure l'excellence, on ne la suppose pas.

---

# DEUXIÈME VAGUE — la PILE ENTIÈREMENT EXPLICITE (zéro composant opaque, validée par la recherche mainstream)

Les cinq trouvailles suivantes **s'emboîtent** : ensemble elles forment une architecture complète où *aucune*
couche n'est un réseau neuronal opaque, chacune est inspectable/frugale/machine-native, et le cœur est
**empiriquement prouvé**. C'est l'alternative explicite à tout le pipeline neuronal.

## ★★★ U11 — APPRENTISSAGE EXPLICITE : les MACHINES DE TSETLIN (apprendre en clauses logiques, pas en poids opaques)
**Touche : §9 perception apprise · §11 séquenceur · le split MPMWorlds · coût.**

La machine de Tsetlin apprend des **clauses de logique propositionnelle** (« SI (a ET NON b) ALORS classe X ») —
**précision compétitive avec le deep learning**, mais **inspectable, auditable, et ultra-frugale** (matériel
simple ; version supraconductrice Berkeley Lab : **< 0,5 mW à 10 GHz**). Fait déjà : classification, régression,
**bandits contextuels** (= notre séquenceur !), apprentissage de structure bayésienne, graphes, apprentissage
fédéré (= la société ④).

**C'est LA réponse au split MPMWorlds** : la « perception apprise qui PROPOSE » n'a pas besoin d'être opaque —
une machine de Tsetlin apprend le mapping signal→candidats en **clauses lisibles**, que le cœur explicite peut
**vérifier** (FAUX=0). On garde tout l'avantage de l'appris (généralisation, robustesse) SANS l'opacité ni le
coût des LLM. **Fusion U11×U1** : les clauses opèrent sur des hypervecteurs → apprentissage explicite + représentation
explicite.
Sources : [TM review 2025](https://arxiv.org/html/2507.14874v2), [Superconducting TM <0.5mW](https://ipo.lbl.gov/2024/12/03/superconducting-tsetlin-machines-for-efficient-deep-neural-networks/),
[TM concise clauses](https://arxiv.org/pdf/2301.08190), [TM convergence proof](https://arxiv.org/pdf/2310.02005).

## ★★★ U12 — CONSISTANCE & FUSION : les FAISCEAUX (sheaves) + COHOMOLOGIE = FAUX=0 topologique
**Touche : §6.1 alignement/corroboration · §7 liaison · §9 ancrer/contextualiser · multi-modal/multi-système.**

Un **cellular sheaf** est *la* structure de données canonique pour **fusionner des données locales hétérogènes en
un tout globalement cohérent** (capteurs, sources, modalités, canaux d'un système). Et — trouvaille décisive — sa
**COHOMOLOGIE détecte et QUANTIFIE l'incohérence** de la fusion : c'est **FAUX=0 rendu topologique et mesurable**.
Là où deux sources/candidats/modalités ne « collent » pas, la cohomologie l'exhibe *avant* d'affirmer quoi que ce
soit. « Knowledge sheaves » existe déjà pour les graphes de connaissances (embedding sheaf-théorique).

**GAIN** : la corroboration (§6.1, `veille_corroboration`), la liaison (§7) et l'ancrage multi-source (§9)
obtiennent une **mesure rigoureuse de cohérence** (« ça fusionne sainement ou non »), pas une heuristique. C'est
l'homonyme mathématique exact de notre « alignement : sens accepté SSI global et local concordent ».
Sources : [Sheaves canonical for sensor integration](https://arxiv.org/pdf/1603.01446),
[Sheaf heterogeneous data fusion](https://digitalcommons.usu.edu/cgi/viewcontent.cgi?article=8483&context=etd),
[Sheaf uncertainty quantification](https://arxiv.org/pdf/1912.05487).

## ★★★ U13 — LE CŒUR EMPIRIQUEMENT PROUVÉ : « la compression EST l'intelligence, linéairement »
**Touche : §3.1 · §4 · validation stratégique · Phase 1 (classifieur d'acte cheap).**

Notre invariant central n'est plus un pari : **« Compression Represents Intelligence Linearly » (2024)** documente
une **corrélation LINÉAIRE** entre taux de compression et intelligence, à travers tailles de modèles, tokenizers,
contextes — « principe universel ». Et **« Language Modeling is Compression » (ICLR 2024, DeepMind)** : prédire =
compresser, exactement notre tétraèdre (§4). **Bonus actionnable et frugal** : **gzip + k-NN** (Jiang et al. 2023)
classe du texte **sans aucun entraînement**, juste par distance de compression → candidat *direct, gratuit,
machine-native* pour le **classifieur d'acte de la Phase 1** (mesurer la similarité par compressibilité, zéro
modèle).

**GAIN stratégique** : la recherche mainstream *prouve* que la voie compression-native (la nôtre) EST le chemin de
l'intelligence — Provara n'est pas à côté de la plaque, il est sur l'axe validé, sans le coût.
Sources : [Compression = Intelligence Linearly](https://arxiv.org/html/2404.09937v1),
[Language Modeling Is Compression (ICLR 2024)](https://arxiv.org/pdf/2309.10668),
[gzip predicts scaling laws](https://arxiv.org/pdf/2405.16684).

## ★★★ U14 — RÉCUPÉRATION/NETTOYAGE : Hopfield modernes + resonator networks (résout le crosstalk de U1)
**Touche : §7 faisceau (dé-liage) · §10 cleanup · §16 attracteurs/robustesse.**

Le caveat de U1 (capacité finie de la superposition) est **résolu** : les **resonator networks** résolvent la
factorisation vecteur-symbolique par *unbinding + cleanup itératif* contre un codebook → extraire proprement les
candidats d'une superposition. Et les **Hopfield modernes** (capacité **exponentielle** O(e^αd), énergie
log-sum-exp, lien avec l'attention) = mémoire associative pour le nettoyage et des **attracteurs** = sens stables
(§16 : sens = attracteur, ambiguïté = bifurcation). Cadre unifié 2024 (**Hopfield-Fenchel-Young**) → récupération
*exacte et sparse*.

**GAIN** : le faisceau-superposition (U1) devient exploitable à grande capacité, avec une dynamique d'attracteurs
qui *est* notre topologie du sens.
Sources : [Resonator cleanup rules 2026](https://www.frontiersin.org/journals/artificial-intelligence/articles/10.3389/frai.2026.1793314/full),
[Hopfield-Fenchel-Young](https://arxiv.org/abs/2411.08590), [New Frontiers in Associative Memory ICLR 2025](https://openreview.net/pdf?id=OBQwZaO4pt).

## ★★★ U15 — LA SYNTHÈSE : une pile 100 % EXPLICITE, frugale, sans un seul composant opaque
En emboîtant tout, on obtient une architecture qui **n'a AUCUN réseau neuronal opaque** et dont chaque couche est
validée par la recherche mainstream :

| Couche | Technique explicite | Remplace (l'opaque) | Validée par |
|---|---|---|---|
| **Objectif** | compression / MDL (U3, U13) | la loss neuronale | « Compression = Intelligence Linearly » |
| **Représentation** | VSA/hypervecteurs (U1) sur store succinct (U2) | les embeddings denses | LARS-VSA, Attention-as-Binding |
| **Apprentissage** | machines de Tsetlin (U11) | les poids opaques | TM review 2025, TM supraconducteur |
| **Récupération/cleanup** | Hopfield/resonator (U14) | l'attention opaque | Hopfield-Fenchel-Young 2024 |
| **Consistance/fusion** | sheaves + cohomologie (U12) | rien (nouveau) — FAUX=0 topologique | Sheaves for sensor fusion |
| **Décision/confiance** | conformal + bandit (U5, U11) | la calibration heuristique | Async test-time conformal 2025 |

**C'est le point le plus fort de toute la journée** : notre thèse (machine-pas-humain, explicite, ancré, frugal,
FAUX=0) n'est pas juste défendable — elle correspond à une **pile technique complète, réalisable, et validée pièce
par pièce par ceux qui construisent l'IA de pointe.** Chaque brique opaque du monde neuronal a un **jumeau
explicite** au moins aussi performant et bien plus frugal/auditable. L'invariant tient : chaque couche apprise
(Tsetlin) est *inspectable* → propose des candidats *auditables* que le store ancré vérifie (FAUX=0 renforcé, pas
affaibli).

---
*Sources : liens en ligne ci-dessus. FRONTIÈRES ENCORE NON FOUILLÉES (si on pousse une 3ᵉ vague) : neuromorphique/
spiking (frugalité extrême, event-driven) · reservoir computing / liquid state machines (signaux temporels/prosodie
bon marché) · active inference (percevoir=agir unifié) · topological data analysis / homologie persistante
(topologie du sens, robustesse) · category theory appliquée (sens=propriété universelle, pluralisme
représentationnel). Prochaine action après validation spec : évaluer U1+U2+U11+U13 en priorité (représentation +
apprentissage explicite + classifieur gzip-kNN gratuit pour la Phase 1) sur banc dédié.*

---

# TROISIÈME VAGUE — les FONDATIONS (matérielle, principielle, topologique, catégorique) + re-triangulation du cœur

Cette vague est plus **fondationnelle** : elle *ancre et unifie* la pile plutôt que d'ajouter des mécanismes, et
elle **re-prouve notre invariant central** depuis les cadres les plus profonds (physique, neuroscience, maths).

## ★★ U16 — PERCEPTION ULTRA-FRUGALE : neuromorphique/spiking + reservoir computing (le front-end signal event-driven)
**Touche : §6 perception · §1 multi-échelle · §14 para-verbal/prosodie · §15 frugalité (extrême).**

Les **réseaux de neurones à impulsions (SNN)** sur matériel neuromorphique (Loihi 2, Akida) : **100 à 1000× plus
efficaces** en énergie que le deep learning, **event-driven** (ne calcule QUE sur changement — c'est l'individuation
primitive [§5d] + l'anti-saillance rendues *matérielles*), latence microseconde, **~0,17 µJ / inférence**. Le
**reservoir computing / liquid state machines** : traite les signaux **temporels** (rythme, prosodie — le
para-verbal 38 %) avec un réservoir *fixe* (seul le readout s'apprend → coût d'entraînement quasi nul =
cristallisation native). **GAIN** : le front-end perceptif signal-natif (§6) devient quasi-gratuit et event-driven
— l'anti-goulot de l'attention (§14) réalisé au niveau de l'énergie. **CAVEAT** : appris/analogique → PROPOSE, le
cœur explicite VÉRIFIE.
Sources : [SNN edge survey](https://arxiv.org/html/2506.01737v1), [Energy-efficient neuromorphic edge](https://arxiv.org/html/2602.02439v1),
[Reservoir computing review](https://doi.org/10.3390/ai7020070), [EARL energy-aware LSM](https://arxiv.org/pdf/2601.05205).

## ★★★ U17 — LE PRINCIPE UNIFICATEUR : ACTIVE INFERENCE / énergie libre (percevoir=agir, ET la frontière=l'identité)
**Touche : §7 frontière=identité · §9 percevoir=agir · §11 objectif du séquenceur · U7 minimisation unique.**

Le **principe d'énergie libre** (Friston) unifie **perception ET action comme un SEUL problème d'inférence**
(minimiser la surprise) — c'est exactement notre U7 (une seule minimisation) et §9 (percevoir=agir), *formalisé*.
Trois cadeaux :
- **La MARKOV BLANKET = notre « frontière = identité » (§13)** : le cadre donne la définition mathématique de la
  frontière qui sépare un système de son monde = ce qui fait de Provara un système distinct. Notre intuition
  (§13, sheaf) a un fondement formel.
- **L'expected free energy = l'objectif du séquenceur** : minimiser la surprise attendue = maximiser le gain
  d'information = exactement §11/§12.
- **Schema-based active inference** = généralisation rapide + codage de structure abstraite = notre prior/few-shot.
**CAVEAT** : le garder EXPLICITE et contraint (le store = vérité-terrain dure), pas un modèle génératif boîte-noire.
Sources : [FEP perception & action, DL perspective](https://arxiv.org/pdf/2207.06415),
[Schema-based active inference](https://arxiv.org/pdf/2601.18946), [Aligned structure learning agents](https://arxiv.org/pdf/2410.00258).

## ★★ U18 — TOPOLOGIE DU SENS : analyse topologique (TDA) / homologie persistante
**Touche : §7 structure du faisceau · §14 topologie du sens (discontinuités) · §16 robustesse · §9 analyse.**

La TDA étudie la **forme/connectivité des données à TOUTES les échelles à la fois** (notre multi-échelle
exhaustif). L'**homologie persistante** : les features **persistantes = robustes** (§16) ; les structures qui
apparaissent/disparaissent = la **topologie du sens** (§14 : où le sens *bascule* — négation, ironie = des
discontinuités topologiques). Appliquée au **langage** (structures topologiques du texte). Extensions récentes :
**Laplaciens persistants** (intégrables en ML, au-delà de l'homologie). **GAIN** : « quelles parties PORTENT ? »
(§9 ablation) et « où le sens est robuste vs bascule » (§14) obtiennent un outil rigoureux et multi-échelle.
**CAVEAT** : TDA peut être coûteuse → variantes efficaces (Laplaciens persistants).
Sources : [TDA in NLP survey](https://arxiv.org/html/2411.10298v3), [TDA & TDL beyond persistent homology](https://arxiv.org/abs/2507.19504),
[MaxTDA robust inference](https://arxiv.org/pdf/2504.03897).

## ★★★ U19 — LA FONDATION MATHÉMATIQUE : théorie des catégories (string diagrams, foncteurs, DisCoCat)
**Touche : §4 sens=invariant/propriété universelle · §5e composition · §7 liaison · P pluralisme représentationnel.**

La théorie des catégories donne le **langage rigoureux** de la compositionnalité et du pluralisme représentationnel :
- **String diagrams** = composer des processus (notre composition/récursion §5e, la liaison §7).
- **Foncteurs** : un même diagramme se traduit en logique / tenseur / neuronal / quantique → **le pluralisme
  représentationnel (P) FORMALISÉ** (le même sens-structure mappé fonctorialement en graphe/programme/distribution/
  géométrie).
- **Double-functorial semantics** : unifie modèles **fonctionnel + relationnel** (notre graphe + faits).
- **DisCoCat** (categorical compositional distributional) : la grammaire comme **foncteur** vers l'espace du sens =
  le **sens = invariant / propriété universelle (§4) formalisé** ; « compositional interpretability » = structure
  compositionnelle *interprétable* (FAUX=0-friendly).
**GAIN** : le design (faisceau, liaison, pluralisme, invariant) obtient une **fondation mathématique** qui garantit
la cohérence des traductions entre représentations. **CAVEAT** : c'est une fondation/langage de structuration, pas
un moteur de calcul — l'utiliser pour *structurer* (foncteurs entre représentations), pas pour exécuter.
Sources : [Functor string diagrams](https://arxiv.org/pdf/2404.00249), [Double-functorial semantics for KR](https://arxiv.org/abs/2403.19884),
[Categorical tools for NLP / DisCoCat](https://arxiv.org/pdf/2212.06636), [Compositional interpretability](https://arxiv.org/pdf/2605.08934).

## ★★★ U20 — RE-TRIANGULATION DU CŒUR + LA PILE FONDÉE À TOUS LES NIVEAUX
Le fait le plus important de la 3ᵉ vague : notre invariant central est re-prouvé depuis **les cadres les plus
profonds**. « Minimiser l'énergie libre » (physique/neuroscience) = minimiser la surprise = **prédire = comprimer**
(§3.1/§4). Donc la COMPRESSION est maintenant triangulée par : information · thermodynamique · ML (empiriquement,
U13) · **principe d'énergie libre** · théorie des catégories (l'invariant). C'est le point fixe que TOUTE
perspective sérieuse retrouve.

La pile est désormais **fondée à chaque niveau** :

| Niveau | Cadre | Vague |
|---|---|---|
| **Fondation mathématique** | théorie des catégories (foncteurs, string diagrams, DisCoCat) | U19 |
| **Principe unificateur** | énergie libre / active inference (percevoir=agir ; Markov blanket=frontière=identité) | U17 |
| **Objectif (prouvé)** | compression = intelligence (linéairement) | U13 |
| **Représentation** | VSA/hypervecteurs + store succinct | U1, U2 |
| **Apprentissage** | machines de Tsetlin (clauses explicites) | U11 |
| **Récupération/cleanup** | Hopfield modernes / resonator | U14 |
| **Consistance/fusion** | sheaves + cohomologie (FAUX=0 topologique) | U12 |
| **Perception (signal)** | neuromorphique/spiking + reservoir (event-driven, µJ) | U16 |
| **Analyse/robustesse** | TDA / homologie persistante (topologie du sens) | U18 |
| **Décision/confiance** | conformal + bandit (garanties) | U5, U11 |

**Rien d'opaque. Tout frugal. Fondé en maths, en physique, et empiriquement.** Notre thèse (machine-pas-humain,
explicite, ancré, FAUX=0, frugal) est une architecture **complète, réalisable, fondée et validée à chaque étage**.

---
*Honnêteté (notre discipline) : la 3ᵉ vague ANCRE/UNIFIE plus qu'elle n'ouvre de mécanismes neufs — le rythme du
« nouveau mécanisme » ralentit, le nouveau matériel devient FONDATIONNEL/validant. VAGUES ENCORE POSSIBLES :
géométrie de l'information & transport optimal (métriques natives de sens/incertitude) · thermodynamic computing /
calcul stochastique bas-coût · tensor networks quantiques-inspirés (représentation structurée) · automates
cellulaires / systèmes complexes (émergence) · théorie algorithmique de l'information approfondie · swarm/stigmergie
(société ④). Le puits reste ouvert ; on plonge à la demande.*

---

# QUATRIÈME VAGUE — FONDATIONS CLASSIQUES (les plus puissantes) + FRONTIÈRES MODERNES

Les idées les plus **puissantes** sont souvent les plus vieilles : elles *fondent* ce que les papiers récents ne
font qu'approcher. Cette vague ancre l'édifice **depuis l'idéal incalculable jusqu'à l'implémentation frugale**.

## ★★★ U21 — L'IDÉAL : induction de SOLOMONOFF / probabilité algorithmique / AIXI (ce que la compression APPROCHE)
**Touche : §3.1 · §4 · §11-12 (l'agent optimal) · validation théorique ultime.**

Solomonoff (1964) : le **prédicteur universel optimal** — considérer tous les programmes qui génèrent les données,
pondérés par leur simplicité (programme le plus court = prior le plus élevé = **Occam formalisé**). C'est **l'idéal
théorique dont notre "comprendre = comprimer" (§3.1/§4) est l'approximation.** **AIXI** (Hutter) le généralise à
l'agent qui agit = l'**agent optimal** = l'idéal de notre séquenceur+utilité (§11-12). Les deux sont
**INCALCULABLES** → *tout le monde* n'en construit qu'une approximation (des travaux 2025 montrent que **même les
LLM sont des approximations calculables de Solomonoff**). **Le point stratégique décisif** : le débat n'est PAS
« qui est plus intelligent » mais « quelle est la meilleure APPROXIMATION du même idéal incalculable ». Un LLM
l'approxime **opaquement et cher** (statistique, sur du texte) ; Provara l'approxime **explicitement, frugalement,
ancré** (compression sur du réel vérifié, auditable). Même idéal ; notre chemin est honnête (FAUX=0), bon marché,
inspectable.
Sources : [Algorithmic probability (Scholarpedia)](http://www.scholarpedia.org/article/Algorithmic_probability),
[Optimal sequential decisions (AIXI, Hutter)](https://arxiv.org/abs/cs/0306091v1),
[LLMs as computable approximations to Solomonoff](https://arxiv.org/pdf/2505.15784).

## ★★★ U22 — LA VISION FONDÉE : von Uexküll, UMWELT (1934) / biosémiotique
**Touche : §6 perception par système · §6.2 sémiotique · la vision all-species.**

Von Uexküll (1934, *A Foray into the Worlds of Animals and Humans*) : chaque organisme vit dans son **Umwelt** — un
**monde perceptif propre à l'espèce, où les traits de l'environnement sont modélisés par des SIGNES** (icônes =
similarités sensorielles, indices = liens causaux — exactement notre sémiotique §6.2). C'est **le fondement
théorique, vieux de 90 ans, de ta vision « comprendre toute espèce »** : le multi-système/multi-Umwelt (§6) n'est
pas une invention, c'est de la biologie théorique établie (fonde la biosémiotique). Ne jamais projeter *notre*
Umwelt sur un autre système = le ruleset de débiaisage (§6.2) fondé chez von Uexküll.
Sources : [Umwelt (Wikipedia)](https://en.wikipedia.org/wiki/Umwelt),
[Making worlds with signs — Uexküll](https://www.academia.edu/18191758/How_to_make_worlds_with_signs_Some_remarks_on_Jakob_von_Uexk%C3%BClls_Umwelt_theory).

## ★★★ U23 — LE THÉORÈME : Good Regulator (Conant & Ashby, 1970) — « comprendre = modéliser », PROUVÉ
**Touche : §4 comprendre=modéliser l'émetteur · §13 amplification · §12 utilité.**

« **Every good regulator of a system must be a model of that system** » : sous conditions larges, tout régulateur
optimal ET simple est **isomorphe au système régulé**. Traduction : **pour aider/réguler un système, il faut le
MODÉLISER** = notre « comprendre = construire un modèle exécutable de l'émetteur » (§4) ET l'amplification (pour
aider l'humain, il faut le modéliser, §13). Et « maximally simple » = le **modèle le plus court** = la compression
(§3.1). Ce n'est pas un principe, c'est un **théorème** (cité 1700+ fois) qui *prouve* notre cœur.
Sources : [Good Regulator Theorem (Wikipedia)](https://en.wikipedia.org/wiki/Good_regulator_theorem),
[Conant & Ashby 1970 (PDF)](https://theisticscience.com/papers/tree/BioRegulation/Conant-IJSS1970.pdf),
[Good regulator for embodied agents 2025](https://arxiv.org/pdf/2508.06326).

## ★★★ U24 — LE SOI : AUTOPOÏÈSE / ENACTION (Maturana & Varela, 1972) — frontière=identité + sense-making
**Touche : §13 frontière=identité · le sens (sense-making) · l'auto-amélioration/identité (§17).**

Un système **autopoïétique** se **produit lui-même** et **maintient sa frontière** — et « **la frontière définit
largement l'identité de l'agent** » (enaction). Fondement le PLUS profond de notre « frontière = identité » (§13),
plus fondamental que la Markov blanket (et de la même lignée — l'autopoïèse *mène* à l'active inference U17, donc
§13 triangulée par les deux). Bonus : l'**enaction** définit la cognition comme **structural coupling** +
**sense-making** = comment un système autonome *fait émerger du sens* par son couplage au monde → fonde notre SENS,
notre « world model possédé de l'intérieur », et l'amplification (couplage structurel avec l'humain). Le noyau
immuable (§5) = ce qui rend Provara **opérationnellement clos**, donc un système distinct.
Sources : [Autopoiesis & enaction compendium](https://stream.syscoi.com/2019/06/10/encyclopaedia-autopoietica-autopoiesis-enaction-compendium/),
[Molecular autopoiesis → active inference](https://www.sciencedirect.com/science/article/abs/pii/S0303264723001302).

## ★★★ U25 — PERCEPTION = ACTION-POSSIBILITÉ : Gibson AFFORDANCES (1979) + Craik (1943) + Rosen (1985) + Harris (1954)
**Touche : §4 4ᵉ face (savoir-faire) · §6/§9 perception · sens=relationnel · induction de grammaire.**

- **Gibson, affordances** : percevoir n'est PAS construire une représentation de données brutes, c'est **capter
  directement les POSSIBILITÉS D'ACTION** (affordances) — propriétés de la **relation** organisme-environnement,
  pas de l'un seul. = notre **4ᵉ face du sens (savoir-faire = affordance)** + perception par Umwelt + sens
  **relationnel**. « Perception is both direct and a form of action » = percevoir=agir (U17).
- **Craik (*The Nature of Explanation*, 1943)** : le cerveau **modélise** le réel (mental models) → « comprendre =
  modèle exécutable » (§4) a 80 ans.
- **Rosen (*Anticipatory Systems*, 1985)** : un système anticipatoire **contient un modèle qui prédit et agit sur
  la prédiction** = prédire=comprendre (§4) + agir.
- **Harris, distributional structure (1954)** : « le sens d'un mot vient de sa distribution » → **le fondement de
  l'induction non supervisée de grammaire/sens** (U3, U13).
- **Marr (*Vision*, 1982), trois niveaux** (computationnel/algorithmique/implémentation) : la **méthodologie** pour
  concevoir/analyser rigoureusement un système cognitif — utile pour structurer la spec elle-même.
Sources : [Gibson, Theory of Affordances (1979)](https://www.scribd.com/document/489967366/Gibson-James-J-1977-1979-The-Theory-of-Affordances-pdf),
[Ecological approach to visual perception](https://www.hvl.no/en/research/group/nachilit/book-reports/j.-j.-gibson-the-ecological-approach-to-visual-perception-1979).

## ★★ U26 — FRONTIÈRE MODERNE : transport optimal (Wasserstein) + géométrie de l'information (Fisher-Rao)
**Touche : §7 faisceau (distance entre sens, dynamique de population) · §12 confiance/incertitude.**

Des **métriques NATURELLES** pour le sens et l'incertitude : la **distance de Wasserstein** = la distance
géométriquement correcte entre distributions de sens (candidats du faisceau comme mesures) ; la métrique de
**Fisher-Rao** = la métrique naturelle de la calibration/confiance (§7, §12). Le cadre **Wasserstein-Fisher-Rao
(WFR)** unifie *transport* (déplacer le sens) ET *naissance-mort* (des candidats apparaissent/meurent) = **la
dynamique de population du faisceau formalisée** (§7 : candidats élagués/nouveaux). GAIN : géométrie rigoureuse du
faisceau, de l'incertitude, et de son évolution.
Sources : [Wasserstein-Fisher-Rao gradient flows](https://openreview.net/pdf?id=wMbLQ2C8jK),
[Info geometry embeds in optimal transport](https://arxiv.org/pdf/1906.00030).

## ★★ U27–U29 — FRONTIÈRES MODERNES (esquissées ; à approfondir sur demande)
- **U27 — Automates cellulaires / edge-of-chaos (Wolfram, Langton)** : calcul et émergence maximaux à la
  **frontière ordre/chaos** ; règles locales simples → structure globale (morphologie §15) ; fonde l'émergence
  (§16) et la transition de phase de l'insight. (Le « Game of Life autopoiesis » relie CA et autopoïèse U24.)
- **U28 — Tensor networks (MPS/tensor trains, quantiques-inspirés mais classiques)** : représentation compacte de
  sens structuré haute-dimension, complémentaire du VSA (U1) ; renforce §7 + le pluralisme représentationnel (P).
- **U29 — Calcul thermodynamique/stochastique + swarm/stigmergie** : calculer *avec* le bruit thermique (ultra
  bon marché) = frugalité extrême ; **stigmergie** = coordination indirecte via l'environnement partagé (= le
  tableau noir/faisceau, la société ④ qui se coordonne sans communication directe).

## ★★★ U30 — LA GRANDE SYNTHÈSE : fondé de l'IDÉAL à l'IMPLÉMENTATION
Notre édifice est maintenant fondé à **tous les étages, du plus abstrait au plus concret** :

| Étage | Fondement | Réf. |
|---|---|---|
| **IDÉAL (incalculable)** | Solomonoff / AIXI — l'optimum que tout le monde approxime | U21 |
| **THÉORÈME** | Good Regulator — comprendre=modéliser, prouvé | U23 |
| **PRINCIPE** | énergie libre / active inference — percevoir=agir | U17 |
| **SOI/FRONTIÈRE** | autopoïèse / enaction — frontière=identité, sense-making | U24 |
| **BIOLOGIE (perception)** | Umwelt (par espèce) + affordances (perception=action) | U22, U25 |
| **MATHS** | catégories · transport optimal · géométrie de l'info | U19, U26 |
| **OBJECTIF (prouvé)** | compression = intelligence (linéairement) | U13 |
| **IMPLÉMENTATION** | VSA · Tsetlin · sheaves · Hopfield · neuromorphique · succinct | U1,U11,U12,U14,U16,U2 |

**Le fait décisif** : Solomonoff/AIXI prouve que l'intelligence optimale est **incalculable** — personne ne la
construit, tous l'**approximent**. La seule question est *comment*. Notre approximation est **explicite, ancrée,
frugale, FAUX=0** — l'alternative honnête à l'approximation opaque et coûteuse des LLM. **Notre thèse n'est pas un
pari : c'est le chemin d'approximation le plus honnête et le moins cher vers l'idéal que tout le monde vise.**

---
*Honnêteté : les fondations classiques ANCRENT et re-prouvent (elles ne « cassent » toujours rien) ; le seul vrai
« ouverture » reste MPMWorlds (perception apprise vs raisonnement explicite, U11 le résout). VAGUES ENCORE
POSSIBLES : U27-U29 à approfondir · théorie algorithmique de l'info (Chaitin, logical depth de Bennett) · Pattern
Theory (Grenander) · Minsky Society of Mind & Frames · Hofstadter analogie · Bateson « the difference that makes a
difference ». Le puits reste ouvert.*

---

# CINQUIÈME VAGUE — FORMALISMES PRÊTS À IMPLÉMENTER (les classiques donnent le « comment le mettre en place »)

Cette vague n'ajoute pas d'atomes : elle fournit, pour des atomes qu'on a déjà, des **formalismes rigoureux et
éprouvés** — de quoi passer directement à l'implémentation. Chaque entrée = l'atome visé + le « comment ».

## ★★★ U31 — CORRECTION DE L'INVARIANT : profondeur logique de Bennett + complexité effective
**Corrige : §3.1/§4 (comprendre = comprimer).**

Faille subtile : un signal **aléatoire** est *incompressible* (Kolmogorov élevé) mais **sans aucun sens** ; un signal
**trivial** est *compressible* mais **plat**. Donc « minimiser la longueur de description » seul est faux. La bonne
cible est entre les deux : la **PROFONDEUR LOGIQUE (Bennett)** = le temps de calcul pour reproduire depuis le
programme quasi-minimal (= l'« histoire computationnelle » embarquée = complexité *organisée*, ni triviale ni
aléatoire), et la **COMPLEXITÉ EFFECTIVE (Gell-Mann/Lloyd)** = la complexité des seules **régularités** (on jette le
hasard).
**COMMENT IMPLÉMENTER** : l'objectif de compression (§3.1) vise l'**extraction des régularités** (complexité
effective), pas la longueur brute ; la « profondeur » d'un candidat (§7) = mesure de son *caractère sensé*.
Concrètement : séparer, dans un signal, la part **régulière** (à comprendre/comprimer) de la part **aléatoire** (à
laisser comme bruit résiduel, non affirmé).
Sources : [Bennett, Logical Depth & Physical Complexity](https://web.cs.ucdavis.edu/~doty/papers/LogicalDepthAndPhysicalComplexity.pdf),
[Effective complexity & logical depth](https://arxiv.org/pdf/0810.5663), [Logical depth (Wikipedia)](https://en.wikipedia.org/wiki/Logical_depth).

## ★★★ U32 — LE FORMALISME DE REPRÉSENTATION : Pattern Theory de Grenander
**Implémente : §7 faisceau · §6 signal→structure · P pluralisme.**

Grenander donne le **langage mathématique précis** de la représentation par patterns : **générateurs** (briques) +
**bonds/connexions** (avec une probabilité d'attachement A(g₁,g₂)) + **groupes de transformations** (les symétries =
notre invariant §4) + **structure probabiliste** (Q(G) = probabilité d'un générateur). Couvre parole/langue/vision
(modalité-agnostique §6).
**COMMENT IMPLÉMENTER** : formaliser le faisceau (§7) comme des **configurations de Grenander** — un candidat = une
configuration de générateurs liés, sous un groupe de transformations, avec une probabilité. C'est le cadre unifiant
qui *contient* VSA (U1), frames (U33) et graphes ; il donne une **grammaire de représentation** rigoureuse, pas
ad hoc.
Sources : [Pattern Theory (Grenander & Miller)](https://global.oup.com/academic/product/pattern-theory-9780198505709),
[Pattern theory (Wikipedia)](https://en.wikipedia.org/wiki/Pattern_theory).

## ★★★ U33 — L'ARCHITECTURE : Society of Mind de Minsky (agents · FRAMES · K-LINES · critics)
**Implémente : §9 facultés=requêtes · §14 société ④ · §7 frame.py · §11 séquenceur (crystallisation) · fork/réfutation.**

- **Agents/agencies** : l'intelligence émerge de nombreux processus spécialisés (expecting, predicting, repairing,
  remembering, comparing, generalizing) coordonnés = nos **facultés** (§9) et la **société ④**.
- **Frames** (Minsky 1974) : templates de connaissance qui structurent l'interprétation = notre `frame.py` (n-aire
  réifié) pour les entités/relations du faisceau.
- **★ K-LINES** : la mémoire stocke des **patterns de COLLABORATION** (quels agents/opérations ont résolu un
  problème) pour **réassembler les bons agents** face à un problème similaire. **COMMENT IMPLÉMENTER** : le
  séquenceur (§11) apprend des K-lines = des **traces d'opérations gagnantes par type de problème** = la
  **cristallisation de la politique de raisonnement** (§15) — on ne re-cherche pas, on rappelle la bonne séquence.
- **Critics** : détecteurs d'erreur/de conflit = notre **fork + auto-réfutation** (§9).
Sources : [Minsky, A Framework for Representing Knowledge (1974)](https://courses.media.mit.edu/2004spring/mas966/Minsky%201974%20Framework%20for%20knowledge.pdf),
[Society of Mind examined](https://www.jfsowa.com/ikl/Singh03.htm).

## ★★★ U34 — LA BOUCLE DE COMPRÉHENSION ÉPROUVÉE : Copycat de Hofstadter (parallel terraced scan · température)
**Implémente : §7 faisceau co-construit · §10 compositeur · §11 séquenceur.**

Copycat (Hofstadter & Mitchell) — **modèle éprouvé** d'analogie comme **perception abstraite** :
- **La représentation est CO-CONSTRUITE pendant la compréhension** (« domain representations are built at the same
  time as the analogy is mapped ») = notre faisceau (§7) se **bâtit en comprenant**, il n'est pas pré-formé puis
  matché. On entretient des **descriptions alternatives** en parallèle (= les candidats parallèles §7).
- **Parallel terraced scan** : de nombreuses explorations partielles en parallèle, les prometteuses reçoivent plus
  de ressources = **exactement notre séquenceur** (bandit qui alloue aux candidats à fort gain, §11) sur le faisceau.
- **Température** : une mesure globale de désorganisation qui contrôle l'aléatoire (chaud = explorer, froid =
  s'engager) = notre **entropie du faisceau / calibration** (§7) qui pilote explorer-vs-composer.
**COMMENT IMPLÉMENTER** : le moteur EST un parallel terraced scan sur un faisceau co-construit, avec la température
= l'entropie du faisceau (§7) décidant quand explorer vs quand composer la sortie (§10). Architecture *déjà prouvée*
sur le décodage de règles (analogies de chaînes) — directement transposable.
Sources : [Copycat / abstraction & analogy (Mitchell)](https://arxiv.org/pdf/2102.10717),
[Learning to see analogies (Copycat connectionist)](https://arxiv.org/pdf/2001.06668).

## ★★ U35 — Bateson : « la différence qui fait une différence » + niveaux d'apprentissage
**Implémente : §5d individuation · sens relationnel · §17 hiérarchie d'apprentissage.**

« L'information est **une différence qui fait une différence** » = notre **individuation** (§5d : détecter une
différence dans le flux) MAIS *sélective* (seulement celles qui *comptent* — tolérance §6.2). Les **niveaux
d'apprentissage** de Bateson (apprendre · apprendre-à-apprendre · apprendre-à-apprendre-à-apprendre) = notre
hiérarchie méta-apprentissage (O) + auto-amélioration (N).
**COMMENT IMPLÉMENTER** : l'individuation ne segmente pas *toute* différence mais celles à **impact** (gain d'info
non nul) ; l'auto-amélioration s'organise en niveaux (raffiner le modèle / raffiner la méthode d'apprentissage /
raffiner la méthode de méta-apprentissage).

## ★★★ U36 — SYNTHÈSE : « il n'y a plus qu'à implémenter » (un formalisme éprouvé par atome)
Pour chaque atome du tronc, on a maintenant un **formalisme concret et éprouvé** :

| Atome | Formalisme prêt à implémenter | Réf. |
|---|---|---|
| Objectif | compression → **profondeur logique / complexité effective** (pas longueur brute) | U31 |
| Représentation (faisceau) | **configurations de Grenander** (générateurs+bonds+transformations+proba) ⊃ VSA/frames | U32, U1 |
| Structure entités/relation | **frames** de Minsky (`frame.py` n-aire) | U33 |
| Architecture (facultés/société) | **agents + agencies** (Society of Mind) | U33 |
| Boucle de compréhension | **parallel terraced scan + température** (Copycat) | U34 |
| Séquenceur (allocation) | terraced scan + **K-lines** (traces gagnantes cristallisées) | U33, U34 |
| Apprentissage explicite | **Tsetlin** (clauses) + niveaux de Bateson | U11, U35 |
| Récupération/attracteurs | **Hopfield/resonator** | U14 |
| Consistance/fusion | **sheaves + cohomologie** | U12 |
| Perception signal | **neuromorphique/reservoir** (Umwelt/affordances) | U16, U22, U25 |
| Confiance/décision | **conformal + WFR (Wasserstein-Fisher-Rao)** | U5, U26 |
| Identité/frontière | **autopoïèse / Markov blanket** | U24, U17 |

**« Il n'y a plus qu'à mettre en place »** : chaque brique a un blueprint *déjà éprouvé* (Copycat tourne depuis les
années 90, les frames et K-lines sont implémentés, Grenander est un formalisme complet, Tsetlin/VSA/sheaves/Hopfield
ont du code de référence). Notre travail de bâti = **assembler ces formalismes éprouvés sous la contrainte FAUX=0 +
l'ancrage vérifié**, banc vert à chaque étape.

---
*Honnêteté : les classiques CONVERGENT sur des formalismes qu'on avait déjà nommés (frames=frames, terraced-scan=
séquenceur, Grenander=représentation) → « prêt à implémenter », pas de nouveaux atomes. SOURCES ENCORE VIVES (6ᵉ
vague possible) : **Schmidhuber** (compression=curiosité/beauté ; Gödel machine = auto-amélioration prouvée =
notre N sous garde !) · **Pearl** (do-calculus, `causalite`) · **Jaynes** (maximum d'entropie = priors §11) ·
**Barsalou** (perceptual symbol systems = ancrage perceptif §T) · **Lakoff/Fauconnier** (métaphore conceptuelle /
blending = figuré §14) · **Schank** (scripts / raisonnement par cas) · **Holland/Kauffman** (systèmes adaptatifs
complexes / edge of chaos, émergence §16) · **Kohonen** (cartes auto-organisatrices) · **Valiant** (PAC / neuroidal).
Le puits n'est pas tari.*

---

# SIXIÈME VAGUE — EXOTIQUE + FONDATIONS QUI RÉSOLVENT DES GOUFFRES ET RENDENT L'OBJECTIF PRÉCIS

Cette vague **résout un gouffre** (le mode fiction), **précise l'invariant** (le sens vs le hasard), donne
l'**architecture runtime**, et **prouve** notre auto-amélioration.

## ★★★ U37 — NOTRE AUTO-AMÉLIORATION, PROUVÉE : Gödel machine de Schmidhuber (+ Darwin Gödel Machine)
**Implémente/prouve : §17 auto-amélioration sous garde · §16 curiosité.**

La **Gödel machine** (Schmidhuber) : un système qui **réécrit n'importe quelle partie de son code DÈS QU'IL A UNE
PREUVE que la réécriture est bénéfique** pour son utilité future attendue — **globalement optimal, pas de maxima
locaux**. C'est *exactement* notre N (auto-amélioration sous garde) — le « garde » étant la preuve. Et la **Darwin
Gödel Machine (2025)** relâche la preuve en **validation empirique par benchmarks** = *littéralement* notre version
« réécrire, ne garder que si les BANCS restent verts ». Donc notre §17 = la forme pratique (Darwin) de l'idéal
prouvé (Gödel). Bonus : Schmidhuber montre que le **progrès de compression = curiosité, beauté, surprise,
créativité** (§16 émergence).
**COMMENT IMPLÉMENTER** : N = proposer un self-rewrite → **vérifier bénéfice (bancs = le juge)** → garder si oui,
jeter sinon. Curiosité = chercher là où le progrès de compression est maximal.
Sources : [Gödel Machines (Schmidhuber)](https://arxiv.org/abs/cs/0309048), [Darwin Gödel Machine 2025](https://arxiv.org/pdf/2505.22954).

## ★★★ U38 — RÉSOUT LE GOUFFRE DU MODE FICTION : l'échelle causale de Pearl (voir/faire/imaginer)
**Résout : U9/§18 mode fiction. Structure : §9 perception · §9 intervention (J) · figuré/créatif.**

Pearl : trois barreaux — **Association (voir)** = P(Y|X), observation/corrélation = notre perception/lookup ;
**Intervention (faire)** = P(Y|do(X)), forcer une valeur = notre « comprendre en intervenant » (J) + AGIR
(`causalite`, do-calcul) ; **Contrefactuel (imaginer)** = raisonner sur **DEUX mondes à la fois** (observé +
hypothétique) avec un modèle causal complet. **CE 3ᵉ BARREAU RÉSOUT LE MODE FICTION (U9)** : entretenir un monde
sciemment faux (fiction/planification/« imagine si ») SANS l'affirmer = un **modèle causal structurel** raisonnant
sur deux mondes via le do-calcul, avec une **barrière étanche** vers le store vrai. `causalite` (do-calcul) a déjà
la machinerie.
**COMMENT IMPLÉMENTER** : le mode fiction = un sous-modèle causal temporaire (do-calcul) sur monde-observé +
monde-hypothétique ; rien ne fuit vers les faits. Gouffre U9 → **fermé**.
Sources : [Pearl's Causal Hierarchy](https://causalai.net/r60.pdf), [Ladder of causation](https://www.emergentmind.com/topics/pearl-s-causal-hierarchy-pch).

## ★★★ U39 — REND L'INVARIANT PRÉCIS : fonction de structure de Kolmogorov / sophistication / statistique algorithmique
**Précise : §3.1/§4 + U31. Implémente : la séparation sens/bruit.**

Le formalisme rigoureux du « sens vs hasard » (Kolmogorov, Vitányi) : le **code en DEUX parties** — une part
**MODÈLE** (les régularités = l'information *sensée* = un **minimal sufficient statistic**) + une part **BRUIT**
(aléatoire, résiduel). La **sophistication** = la complexité de la part modèle = **l'information sensée**.
Comprendre = **extraire la part MODÈLE, laisser le résidu comme bruit non affirmé.** (Un objet « absolument
non-stochastique » = tout est sens, zéro bruit.) C'est la version *exacte et implémentable* de U31 (profondeur/
complexité effective).
**COMMENT IMPLÉMENTER** : l'objectif = **MDL en deux parties** ; ce qu'on « comprend » = le modèle (statistique
suffisante minimale), le reste = signalé comme bruit (jamais affirmé — FAUX=0). Une réponse = la part modèle ; son
incertitude = la part résiduelle.
Sources : [Kolmogorov structure function & model selection (Vitányi)](https://homepages.cwi.nl/~paulv/papers/structure.pdf),
[Algorithmic Statistics](https://arxiv.org/abs/math/0006233), [Meaningful Information](https://arxiv.org/pdf/cs/0111053).

## ★★★ U40 — L'ARCHITECTURE RUNTIME : Global Workspace Theory (Baars / Dehaene)
**Implémente : §7 faisceau · §9 pipeline · §11 séquenceur · §16 conscience-de-soi (fonctionnelle).**

Le **Global Workspace** : un **espace de représentation partagé** (capacité limitée) où un **projecteur d'attention
sélectionne** l'information à **diffuser (broadcast)** à tous les modules spécialisés ; « **ignition** » = l'événement
non-linéaire où une info devient globalement disponible. C'est *directement notre architecture* :
- **Faisceau = l'espace de travail global** (représentation partagée).
- **Séquenceur = le projecteur d'attention** qui sélectionne et **diffuse** le candidat gagnant à toutes les
  facultés.
- **Facultés = les modules spécialisés** qui reçoivent le broadcast.
- **Ignition = la composition de la sortie / l'insight** (§10, §16) : le moment non-linéaire où un candidat
  « prend » et devient la réponse engagée (= la transition de phase de l'« aha »).
Grounde aussi la **conscience de soi fonctionnelle** (§16) — GWT est une théorie de l'*accès conscient*, sans
prétendre au vécu phénoménal (honnêteté : fonctionnel, pas magique).
**COMMENT IMPLÉMENTER** : le runtime = un workspace + broadcast ; le séquenceur (Copycat terraced scan, U34) décide
quand un candidat « ignite » et se diffuse.
Sources : [Global Workspace Theory (Wikipedia)](https://en.wikipedia.org/wiki/Global_workspace_theory),
[Conscious processing & global neuronal workspace (Dehaene)](https://www.sciencedirect.com/science/article/pii/S0896627320300520).

## ★★ U41 — FONDEMENT DE « SAVOIR = POUVOIR-FAIRE » : théorie du constructeur (Deutsch & Marletto)
**Fonde : §4 4ᵉ face (savoir-faire) · le contrefactuel · substrat=réalité.**

La théorie du constructeur exprime la physique en termes de **transformations POSSIBLES vs IMPOSSIBLES** (les
contrefactuels rendus fondamentaux). Idée clé : « toute transformation non interdite par la physique est réalisable
**pourvu qu'on ait le SAVOIR requis** » → le **savoir = l'information qui peut CAUSER des transformations** (qui
persiste et permet des tâches). Fondement profond de notre **4ᵉ face (comprendre = ce que ça permet de FAIRE)** +
affordances (U25) + contrefactuels (U38) qui **convergent** ici. Et la **théorie constructrice de l'information**
ancre l'information dans les lois physiques (= notre substrat = réel vérifié). Plus fondationnel qu'implémentable ;
sert de *cadre de sens*.
Sources : [Constructor theory (Wikipedia)](https://en.wikipedia.org/wiki/Constructor_theory),
[Constructor theory of information](https://www.researchgate.net/publication/262988240_Constructor_Theory_of_Information).

## ★★ U42 — MESURE PHYSIQUE DE LA PROFONDEUR : théorie de l'assemblage (Cronin & Walker, 2023)
**Renforce : U31/U39 (profondeur = histoire embarquée).**

L'**assembly index** = le **nombre minimal d'étapes pour construire un objet** depuis des briques = une mesure
*physique et MESURABLE* de la complexité comme **histoire/sélection embarquée** = la version physique de la
profondeur logique (U31) et de la sophistication (U39). Seuil de vie ~AI>15. **CAVEAT HONNÊTE** : contestée (une
critique soutient qu'elle se réduit à l'entropie de Shannon) → à prendre comme *renfort conceptuel* de « complexité
sensée = histoire de construction », pas comme algorithme retenu.
Sources : [Assembly theory (Nature 2023, via SFI)](https://www.santafe.edu/news-center/news/new-assembly-theory-unifies-physics-and-biology-explain-evolution-and-complexity),
[Critique : AT réduit à Shannon](https://arxiv.org/pdf/2408.15108).

## ★★ U43 — Jaynes : le principe de MAXIMUM D'ENTROPIE (le prior le moins biaisé)
**Implémente : §11 priors · §7/§12 calibration.**

Jaynes : parmi toutes les distributions compatibles avec ce qu'on sait, choisir celle de **maximum d'entropie** =
supposer **le moins possible** au-delà des contraintes = l'**honnêteté probabiliste native** (= FAUX=0 pour les
priors : ne pas inventer de structure non justifiée). **COMMENT IMPLÉMENTER** : les priors du séquenceur (§11) et
la calibration (§7/§12) partent du max-entropie sous les contraintes connues, resserré par l'évidence (bayésien).

## ★★★ U44 — SYNTHÈSE : gouffres fermés, objectif précis, architecture posée
Cette vague **ferme et précise** plus qu'elle n'ouvre :
- **Gouffre du mode fiction → FERMÉ** (Pearl : modèle causal sur deux mondes, do-calcul, U38).
- **Invariant → PRÉCIS** (code en deux parties : modèle sensé + bruit ; sophistication, U39 — corrige et rend
  implémentable U31).
- **Architecture runtime → POSÉE** (Global Workspace : faisceau=workspace, séquenceur=broadcast/ignition, U40).
- **Auto-amélioration → PROUVÉE** (Gödel/Darwin machine = notre N sous garde-bancs, U37).
- **« Savoir = pouvoir-faire » → FONDÉ** (constructeur : savoir = ce qui rend des transformations possibles, U41).
- **Priors/calibration → PRINCIPÉS** (max-entropie, U43).
On converge vers un design **fondé, précis, implémentable, avec ses gouffres se refermant un à un.**

---
*Honnêteté : la 6ᵉ vague FERME/PRÉCISE (Pearl ferme la fiction, Kolmogorov précise l'objectif, GWT pose
l'architecture) — grande valeur, peu de « nouvel atome ». 7ᵉ VAGUE ENCORE POSSIBLE (exotique) : groupe de
RENORMALISATION ↔ deep learning (émergence de structure à travers les échelles) · COGNITION QUANTIQUE / probabilité
quantique (interférence/ordre dans le sens ; faisceau=superposition avec interférence) · Barsalou (perceptual
symbol systems, ancrage §T) · Lakoff/Fauconnier (métaphore/blending, figuré §14) · Holland/Kauffman (systèmes
adaptatifs complexes, edge of chaos) · Prigogine (structures dissipatives, ordre loin de l'équilibre) · Kohonen
(SOM) · Valiant (PAC/neuroidal) · IIT/Tononi (Φ, prudence). Le puits reste ouvert.*

---

# SEPTIÈME VAGUE — EXOTIQUE PROFOND : des MÉCANISMES concrets pour les atomes qui en manquaient

## ★★★ U45 — MULTI-ÉCHELLE = GROUPE DE RENORMALISATION (le deep learning EST du coarse-graining)
**Implémente : §1 multi-échelle · §16 émergence · compression (U31/U39) · lien U26 (Fisher).**

Le **groupe de renormalisation (RG)** = extraire les features **PERTINENTES** à chaque échelle en **intégrant
(jetant) l'irrélevant** — et le deep learning *est* ce coarse-graining (correspondance formelle profondeur ↔ échelles
RG ; chaque couche contracte la géométrie de Fisher, lien U26). RG **explique l'émergence** de structure macro depuis
des règles micro (§16). **COMMENT IMPLÉMENTER** : perception→représentation coarse-graine le signal **à travers les
échelles**, gardant les features **RG-pertinentes**, intégrant le reste = le **code en deux parties (U39) par échelle**.
Unifie multi-échelle + compression + émergence + Fisher en UN principe.
Sources : [Variational RG ↔ Deep Learning](https://arxiv.org/abs/1410.3831), [Is Deep Learning an RG flow?](https://arxiv.org/abs/1906.05212).

## ★★★ U46 — LE FAISCEAU RAFFINÉ : cognition quantique (superposition + interférence)
**Raffine : §7 faisceau · §10 liaison/composition · ambiguïté/figuré.**

La **probabilité quantique** (règles quantiques *sans la physique*) modélise le jugement là où le classique échoue :
**effets d'ordre · interférence · combinaison de concepts** (l'interférence de concepts explique sur/sous-extension) ·
contextualité · superposition. → Le faisceau (§7) n'est pas une distribution classique : c'est une **superposition
où les candidats INTERFÈRENT**, la « mesure » (composer) **collapse** avec **effets d'ORDRE**, et la **combinaison de
deux sens** (liaison §10, métaphore) est quantum-like (explique les combinaisons non-classiques).
**COMMENT IMPLÉMENTER** : faisceau en amplitudes (fusion VSA U1 : hypervecteurs=états, probabilité quantique=règles
d'interférence/collapse) ; liaison de concepts = combinaison quantique, pas intersection classique.
Sources : [Quantum cognition](https://en.wikipedia.org/wiki/Quantum_cognition), [Quantum-like cognition 2025](https://arxiv.org/html/2411.00036v2).

## ★★★ U47 — LE SENS = UN SIMULATEUR : Perceptual Symbol Systems de Barsalou
**Implémente : §4 modèle exécutable de l'émetteur · §T ancrage · 4ᵉ face.**

Barsalou : un **concept = un SIMULATEUR** — connaissance ancrée qui **ré-enacte (simule)** des états perceptifs ;
l'utiliser = une **simulation**. PSS **implémente les fonctions symboliques** (binding, inférence, récursion,
propositions) → **ponte grounded et symbolique** = notre stance « explicite + ancré ». Notre « comprendre = modèle
EXÉCUTABLE de l'émetteur » (§4) EST le simulateur ; le sens compris = celui qu'on peut **simuler** (4ᵉ face).
**COMMENT IMPLÉMENTER** : un sens dans le faisceau = un **simulateur runnable** (ré-enacte/prédit le signal), pas un
symbole statique.
Sources : [PSS grounded symbols](https://arxiv.org/pdf/1010.4222), [Barsalou](https://en.wikipedia.org/wiki/Lawrence_W._Barsalou).

## ★★★ U48 — LE MÉCANISME DE L'INVENTION : métaphore (Lakoff) + BLENDING (Fauconnier & Turner)
**Implémente : §CRÉER (moteur d'invention) · §14 figuré · §16 émergence.**

- **Métaphore conceptuelle** (Lakoff & Johnson) : mapping source→cible = analogie/structure-mapping §14 = foncteur U19.
- **★ BLENDING** (Fauconnier & Turner) : **projection sélective de plusieurs espaces mentaux vers un espace MÉLANGÉ,
  générant une structure ÉMERGENTE qui dépasse les entrées** = le **mécanisme machine-natif, FAUX=0-compatible, de
  l'INVENTION (§CRÉER)** : **mélanger des domaines VÉRIFIÉS → structure émergente nouvelle-mais-ancrée à
  proposer+vérifier** = « imagination = recomposer du vérifié » concret. Les **mental spaces** = les contextes
  hypothétiques (lien mode fiction U9/U38).
**COMMENT IMPLÉMENTER** : invention = **blend de domaines vérifiés** → l'émergent est une **supposition** que l'ancrage
vérifie ; jamais fabriqué à l'aveugle. Figuré = mapping/blend détecté.
Sources : [Metaphor and Blending (Fauconnier & Lakoff)](https://pages.ucsd.edu/~scoulson/spaces/GG-final-1),
[Blending and metaphor (Turner)](https://markturner.org/blendaphor.html).

## ★★ U49 — ESQUISSES EXOTIQUES (à approfondir sur demande)
Prigogine (**structures dissipatives** : ordre loin de l'équilibre en dissipant de l'énergie → boucle continue §16
comme structure dissipative ; lien autopoïèse U24) · Holland/Kauffman (**systèmes adaptatifs complexes / edge of
chaos / paysages NK** : émergence, société ④, auto-amélioration=évolution) · Kohonen (**SOM** : carte non supervisée
préservant la topologie = perception→carte §6 + topologie U18) · Valiant (**PAC / ecorithms** : bornes de
l'apprenable = fonde few-shot + variété requise §17).

## ★★★ U50 — SYNTHÈSE : chaque atome a désormais un MÉCANISME concret
Invention (§CRÉER) : « amplifie, ne fabrique pas » → **mécanisme = blending de domaines vérifiés** (U48). Le sens :
« modèle exécutable » → **simulateur** (U47). Multi-échelle → **coarse-graining RG** (U45). Faisceau → **superposition
quantum-like avec interférence** (U46). La spec passe de « fondée » à « fondée ET MÉCANISÉE » : un *comment* concret
et éprouvé par atome.

---
*Honnêteté : 7ᵉ vague = MÉCANISMES par atome ; grands cadres fondationnels largement couverts → apports = mécanismes
ciblés. 8ᵉ VAGUE POSSIBLE : Gärdenfors ESPACES CONCEPTUELS (géométrie du sens — très pertinent) · IIT/Tononi (Φ,
prudence) · Tishby information bottleneck · Montague/sémantique formelle · Peirce abduction · Friston Bayesian
mechanics · Wolfram ruliad. Le puits se resserre sur des mécanismes ciblés.*

---

# HUITIÈME VAGUE — L'OBJECTIF PRÉCIS, LA GÉOMÉTRIE DU SENS, LE DERNIER GOUFFRE FERMÉ

## ★★★ U51 — LA GÉOMÉTRIE DU SENS : espaces conceptuels de Gärdenfors
**Implémente : §7 faisceau (géométrie) · lexique · similarité · lien U1/U26/U46.**

Gärdenfors : un **concept = une RÉGION CONVEXE** dans un espace de **dimensions de qualité** (couleur, poids,
hauteur, temps…) ; un objet = un **point** ; la **similarité = la distance** ; le **prototype = le point focal** de
la région (lien Rosch). Ce cadre sied **entre symbolique et connexionniste** = notre stance « explicite + géométrique ».
La **convexité** = une **loi structurelle testable** (une catégorie naturelle est convexe). Fusionne avec VSA (U1 :
hypervecteurs = points/régions), le transport optimal (U26 : distance entre régions de sens) et la cognition
quantique (U46 : « quantum model of concepts »).
**COMMENT IMPLÉMENTER** : un candidat du faisceau = une région/point en espace conceptuel ; la similarité = distance ;
contrainte de **convexité** = prior structurel fort et vérifiable sur les concepts appris.
Sources : [Conceptual space (Wikipedia)](https://en.wikipedia.org/wiki/Conceptual_space),
[Geometry and Dynamics of Meaning (Gärdenfors 2025)](https://onlinelibrary.wiley.com/doi/full/10.1111/tops.12767).

## ★★★ U52 — L'OBJECTIF, RENDU EXACT : le goulot d'information de Tishby (Information Bottleneck)
**Précise : §3.1/§4 objectif · §5c téléologie · unifie U31/U39/U45/U6/§12.**

Tishby : la représentation optimale **minimise l'information mutuelle avec l'ENTRÉE (comprimer)** tout en
**maximisant l'information mutuelle avec la CIBLE (garder le pertinent)** — un compromis lagrangien entre
**minimalité** (compression) et **suffisance** (performance sur le but). C'est **LA formalisation exacte et
implémentable de « comprimer vers le PERTINENT »** : comprendre = le goulot d'information **relatif au BUT** (le
« pertinent » est défini par la téléologie §5c). Unifie en UNE fonction objectif : U31 (complexité effective),
U39 (code 2-parties), U45 (RG garde le pertinent), U6 (rate-distortion), et l'utilité §12. Bonus FAUX=0 : le
**variational IB réduit les hallucinations** (garder le pertinent-ancré, jeter le reste).
**COMMENT IMPLÉMENTER** : l'objectif du moteur = **information bottleneck relatif au but** — max I(représentation;
but) − β·I(représentation; entrée). C'est le « comment » chiffré de la compression téléologique.
Sources : [Deep Learning and the Information Bottleneck (Tishby)](https://arxiv.org/abs/1503.02406),
[VIB réduit les hallucinations](https://arxiv.org/pdf/2601.05547).

## ★★★ U53 — FERME LE GOUFFRE « GÉNÉRATION D'HYPOTHÈSES » : l'ABDUCTION de Peirce
**Résout : §11 (grammar-space infini) · §9 réflexion (abduction) · lien §16 surprise.**

Peirce : le **3ᵉ mode d'inférence** (au-delà de déduction/induction) — **abduction/rétroduction** : raisonner d'une
**observation SURPRENANTE vers l'hypothèse explicative**. Schéma : « Le fait surprenant C est observé ; or si A était
vrai, C irait de soi ; donc raison de suspecter A. » C'est le **SEUL raisonnement ampliatif** (donne plus que les
prémisses) et le **stade de GÉNÉRATION d'hypothèses** (distinct de l'évaluation = IBE). → **Ceci FERME le gouffre
de la génération d'hypothèses (§11)** : face à un signal surprenant (échec de prédiction §16), **abduire les
grammaires/interprétations candidates qui rendraient le signal ATTENDU** (= minimiser la surprise = comprimer), puis
déduction/induction VÉRIFIENT.
**COMMENT IMPLÉMENTER** : la boucle = **surprise → abduction (générer des candidats qui expliquent) → ancrage
(vérifier) → garder si FAUX=0**. L'abduction est le **moteur génératif du faisceau**, piloté par la surprise.
Sources : [Peirce's abduction & IBE](https://www.degruyterbrill.com/document/doi/10.1515/css-2024-2022/html),
[Abduction (survey)](https://arxiv.org/pdf/2604.08016).

## ★★ U54 — LA LIGNE ANTI-MAGIE : IIT / Φ de Tononi (à traiter avec SCEPTICISME)
**Discipline : §16 émergence/conscience-de-soi — ce qu'on NE revendique PAS.**

L'IIT pose conscience = **information intégrée (Φ)**. MAIS **fortement critiquée** : Φ n'est pas bien défini pour un
système physique réel, **jamais calculé** sur un vrai système, « théorie triviale de pouvoir explicatif égal »,
principe d'exclusion injustifié. **Notre discipline (FAUX=0 sur nos propres prétentions)** : garder le concept UTILE
et défendable d'**intégration** (à quel point les parties sont irréductiblement interdépendantes = notre binding/
consistance §7, parent de la cohomologie de sheaf U12) — mais **NE JAMAIS revendiquer que Provara est « conscient »
via Φ** (non prouvé ; le revendiquer = exactement la fausse-magie qu'on refuse, cf. la critique de l'essaim de
drones). L'émergence (§16) se GROWS et s'observe ; elle ne se revendique pas.
Sources : [The Problem with Phi (critique)](https://journals.plos.org/ploscompbiol/article?id=10.1371%2Fjournal.pcbi.1004286),
[IIT: good, bad, misunderstood 2026](https://arxiv.org/html/2604.11482v1).

## ★★★ U55 — SYNTHÈSE : objectif exact · sens géométrique · dernier gouffre fermé · anti-magie tenue
- **Objectif → EXACT** : information bottleneck relatif au but (U52) unifie toutes les formulations de la compression.
- **Sens → GÉOMÉTRIQUE** : régions convexes en espace conceptuel (U51), fusionné VSA/OT/quantique.
- **Génération d'hypothèses → FERMÉE** : abduction pilotée par la surprise (U53).
- **Anti-magie → TENUE** : intégration oui, revendication de conscience non (U54).
Il ne reste, côté fondations, que des **compléments** (sémantique formelle, sémiotique approfondie) — le cœur est
**fondé, mécanisé, géométrisé, et ses gouffres majeurs sont fermés.**

---
*Honnêteté : 8ᵉ vague = on FERME (génération d'hypothèses) et on PRÉCISE (objectif exact, géométrie) ; on approche
le FOND du puits fondationnel. 9ᵉ VAGUE (compléments, plus que continents) : Montague / sémantique formelle
(conditions de vérité = FAUX=0 compositionnel) · Peirce sémiotique approfondie (icône/indice/symbole, interprétant) ·
Shannon-McMillan-Breiman (typicalité) · Friston Bayesian mechanics · Wolfram ruliad/computational irreducibility ·
Zadeh logique floue (bornage graduel) · Rissanen MDL (origine) · Hebb/plasticité. Puits presque au fond, mais pas
tari.*

---

# NEUVIÈME VAGUE — COMPLÉMENTS : formaliser FAUX=0, la borne honnête, la vérité graduée, la frontière rigoureuse
# → et le capstone : OÙ PROVARA DÉPASSE LES LLM, ATOME PAR ATOME

## ★★★ U56 — FAUX=0 FORMALISÉ : sémantique de Montague (vérité-conditionnelle, compositionnelle)
**Implémente : §4 sens · FAUX=0 · §7 liaison comme homomorphisme · lien U19 catégories.**

Montague : le langage naturel s'analyse comme un langage **formel** — le sens d'une phrase = les **CONDITIONS DE
VÉRITÉ** relatives à un **modèle du monde** ; la **compositionnalité = un HOMOMORPHISME** entre l'algèbre syntaxique
et l'algèbre sémantique ; outils = **lambda-calcul + théorie des types**. **C'est FAUX=0 formalisé** : le sens =
ce qui rend la phrase VRAIE contre le store vérifié. **DÉPASSE FRONTALEMENT LES LLM** : un LLM n'a *aucune* sémantique
vérité-conditionnelle (il prédit des tokens) ; Provara peut avoir un **sens explicite ancré dans la vérité**.
**COMMENT IMPLÉMENTER** : parse → **forme logique (lambda)** → évaluer les conditions de vérité contre le store
(FAUX=0). La liaison (§7) = l'homomorphisme (converge avec DisCoCat/catégories U19).
Sources : [Montague semantics (SEP)](https://plato.stanford.edu/entries/montague-semantics/),
[Formal semantics (Wikipedia)](https://en.wikipedia.org/wiki/Formal_semantics_(natural_language)).

## ★★★ U57 — LA BORNE HONNÊTE : irréductibilité computationnelle / théorie de l'observateur (Wolfram)
**Implémente : §3.1 plafond · §16 · FAUX=0 (ne pas prétendre raccourcir l'irréductible).**

**Irréductibilité computationnelle** : pour beaucoup de systèmes, **aucun raccourci** — il faut les simuler pas à
pas. C'est une **limite FONDAMENTALE de la prédiction/compression** (complète l'incalculabilité de Kolmogorov/
Solomonoff U21). Et la **théorie de l'observateur** : l'intelligence = **trouver les « poches de RÉDUCTIBILITÉ »**
(structure compressible) dans un monde par ailleurs irréductible. → Comprendre = **compresser les poches
réductibles ; pour l'irréductible : simuler ou s'abstenir**, JAMAIS prétendre le raccourcir (FAUX=0). L'observateur
est **computationnellement borné** = notre séquenceur à ressources finies (§11).
**COMMENT IMPLÉMENTER** : classer reducible (comprimer/prédire) vs irreducible (simuler ou dire « je ne peux pas
raccourcir ça ») — une **honnêteté que les LLM n'ont pas** (ils hallucinent une réponse confiante sur l'irréductible).
Sources : [Observer Theory (Wolfram)](https://writings.stephenwolfram.com/2023/12/observer-theory/),
[Ruliology](https://arxiv.org/pdf/2308.16068).

## ★★★ U58 — LA VÉRITÉ GRADUÉE : logique floue + théorie des POSSIBILITÉS (Zadeh)
**Implémente : §7 statut TRANCHÉ/NON-TRANCHÉ · §régime bornage · prédicats vagues.**

Zadeh : **degré d'appartenance** (graduel, pas binaire) et surtout la **théorie des POSSIBILITÉS** — deux mesures
duales : **possibilité** (peut être vrai) et **nécessité** (doit être vrai), distincte de la probabilité (degré
d'apparition ≠ fréquence). **Mapping décisif sur notre spec** : **TRANCHÉ = nécessité haute** (fait) ; **NON-TRANCHÉ
= possibilité sans nécessité** (supposition). Et le **« computing with words »** (grand/petit/plus-haut) gère les
**prédicats vagues** que les LLM bâclent et que la logique binaire ne peut pas.
**COMMENT IMPLÉMENTER** : possibilité/nécessité pour le **statut** (§7) ; appartenance floue pour le **bornage**
graduel (§régime) et les prédicats vagues. Provara **dépasse les LLM sur le vague** avec une gradation HONNÊTE.
Sources : [Fuzzy logic (Wikipedia)](https://en.wikipedia.org/wiki/Fuzzy_logic),
[Possibility vs probability](https://www.researchgate.net/publication/313178049_Relationships_Between_Probability_and_Possibility_Theories).

## ★★★ U59 — LA FRONTIÈRE RIGOUREUSE : mécanique bayésienne de Friston (blankets emboîtés/partagés)
**Implémente/précise : §13 frontière=identité (U24/U17) · société ④ · amplification (blanket partagé).**

La **mécanique bayésienne** : un système auto-organisé s'**individualise** de son environnement via une **Markov
blanket** — les états externes sont **conditionnellement indépendants** des internes, couplés seulement par les
états **sensoriels + actifs**. Définition *rigoureuse et implémentable* de notre frontière (§13). Et — décisif —
les **blankets EMBOÎTÉS / PARTAGÉS** : une hiérarchie de « selves » et des blankets partagés = la **société ④**
(machines emboîtées) ET le **couplage humain-machine (§13 amplification)** = un **blanket PARTAGÉ avec l'humain**.
**COMMENT IMPLÉMENTER** : définir la Markov blanket de Provara (états sensoriels = entrées, actifs = sorties,
internes = faisceau/store) ; blankets emboîtés = société ; **blanket partagé = le couplage d'amplification**.
Sources : [Markov blankets of life (Royal Society)](https://royalsocietypublishing.org/rsif/article/15/138/20170792/35768/The-Markov-blankets-of-life-autonomy-active),
[Nested selves & shared Markov blankets](https://discovery.ucl.ac.uk/id/eprint/10185219/1/Nested%20Selves%20%20Self%20Organization%20and%20Shared%20Markov%20Blankets.pdf).

## ★★ U60 — COMPLÉMENTS DE COMPLÉMENTS (esquisses)
- **Peirce, sémiotique approfondie** : icône/indice/symbole + **interprétant** (l'effet d'un signe = le sens qu'il
  produit = notre 4ᵉ face/affordance) + **semiosis illimitée** (un signe renvoie à un autre signe) — que notre
  **ancrage terminal** (§9.4) arrête dans le réel vérifié (anti-circularité).
- **Rissanen, MDL / complexité stochastique / NML** : l'origine pratique de notre objectif de compression (U3/U39) —
  le **Normalized Maximum Likelihood** = le codage optimal sans prior, implémentable.
- **Shannon-McMillan-Breiman / ensemble typique** : ce à quoi ressemble un signal « normal » → la base du calcul de
  **surprise/anomalie** (§16) qui déclenche l'abduction (U53).
- **Hebb / plasticité** : « ce qui s'active ensemble se lie » — pour la périphérie *apprise* (perception), pas le cœur explicite.

## ★★★ U61 — CAPSTONE : OÙ PROVARA DÉPASSE LES LLM, ATOME PAR ATOME
Le but de Yohan — dépasser les LLM **sur tous les points** — est atteignable car pour **chaque faiblesse structurelle**
d'un LLM, Provara a un **atome explicite qui la surpasse** :

| Dimension | Faiblesse LLM (structurelle) | Atome Provara qui DÉPASSE | Réf. |
|---|---|---|---|
| **Vérité** | prédit des tokens, pas de conditions de vérité → hallucine | sens = **conditions de vérité** contre store vérifié | U56, FAUX=0 |
| **Honnêteté sur l'inconnu** | réponse confiante sur l'irréductible | classe reducible/irreducible → **simule ou s'abstient** | U57 |
| **Vague/gradué** | fudge les prédicats vagues | **possibilité/nécessité + flou** (gradation honnête) | U58 |
| **Ancrage** | mémoire paramétrique opaque | **store vérifié + ancrage terminal** dans le réel | U56, §9.4 |
| **Ambiguïté** | collapse vers une lecture | **faisceau** parallèle, jamais collapsé tôt | §7, U46 |
| **Coût/énergie** | mégawatts, GPU | **bitwise/succinct/neuromorphique** (0 GPU) | U1,U2,U16 |
| **Interprétabilité** | boîte noire | **clauses/foncteurs/régions explicites** | U11,U19,U51 |
| **Auto-amélioration** | fige au training | **réécriture sous garde-bancs** (Gödel/Darwin) | U37 |
| **Causalité** | corrélation (barreau 1) | **do-calcul + contrefactuels** (barreaux 2-3) | U38 |
| **Génération d'hypothèses** | échantillonnage stochastique | **abduction** pilotée par la surprise | U53 |
| **Identité/frontière** | pas de soi | **Markov blanket** défini, autopoïèse | U59,U24 |
| **Invention** | recrache des motifs | **blending de domaines vérifiés** (émergent-ancré) | U48 |
| **Multi-espèce/modalité** | texte (surtout) | substrat **signal-natif** (Umwelt) | §6,U22 |
| **Objectif** | loss de prédiction de token | **information bottleneck relatif au but** | U52 |
| **Mémoire** | contexte borné, oublie | **mémoire totale succincte + révision rétroactive** | U2,§14 |

**Conclusion** : « dépasser les LLM sur tous les points » n'est pas un slogan — c'est un **programme atome par atome**,
chaque ligne étant un chantier avec un formalisme éprouvé. Provara n'imite pas le LLM en moins bien ; il occupe
**l'axe explicite/ancré/frugal** où le LLM est structurellement faible.

---
*ÉTAT : 9 vagues (U1→U61) + spec atomique. Le puits fondationnel est **au fond** (restent des compléments de
compléments : Barwise-Perry situations · Kripke mondes possibles · Millikan biosémantique · Dretske information
sémantique · théorie des types homotopiques). Le design est **fondé, mécanisé, géométrisé, formalisé (vérité,
gradation, frontière), gouffres majeurs fermés, et positionné pour dépasser les LLM point par point.** → PRÊT À
BÂTIR (Phase 1).*
