# SPEC ATOMIQUE — LE TRONC DE COMPRÉHENSION DE PROVARA

> Spécification de référence, développée atomiquement, issue de 3 jours de cadrage (2026-07-06/07) triangulés
> contre ~30 artefacts externes. Document **autoportant** : on bâtit à partir d'ici sans rien re-lire.
> Statut : cadrage TERMINÉ. Bâti à démarrer après validation par Yohan de §7 (faisceau) + §8 (carte des actes).
> Règle d'or : **on casse l'existant si besoin — les BANCS sont la spec du comportement, pas les 60 caps.**

---

## 0. CE QUE CE DOCUMENT SPÉCIFIE

Le remplacement du **front-end conversationnel** de Provara (aujourd'hui : ~60 caps regex + replis ad hoc) par
**un moteur unique de compréhension**. Le socle vérifié (raisonnement transitif/déduction, lexique 1,9 M,
72 M de faits, machinerie FAUX=0, calibration) est **conservé** et devient les *faculties* que le moteur
interroge. Le but ultime : comprendre le langage de **tout système vivant** (humain = système n°1), en
fonctionnement **machine, pas humain**.

Ce n'est **pas** un LLM, ni un système qui en dépend. C'est une architecture où **la compétence est dans la
structure**, ancrée dans le réel vérifiable, et **jamais menteuse**.

---

## 1. CADRE DIRECTEUR N°1 — MACHINE, PAS HUMAIN, À CHAQUE ATOME

Une machine ne fonctionne pas comme un humain ; elle peut le dépasser. Sa compréhension — et **chaque atome de
son fonctionnement** — ne doit PAS être calquée sur l'humain, sinon on refait l'erreur du monde entier (simuler
un cerveau → LLM → datacenters + imprécision). **Seules les RÉPONSES** doivent correspondre à ce que l'humain
attend. Tout le reste peut être démultiplié, plus précis, plus puissant.

**Nom du principe : forme humaine UNIQUEMENT à la sortie ; pure machine partout ailleurs.**

Traduction atomique — contrainte humaine à REFUSER → superpouvoir machine à EXPLOITER :

| Cerveau humain (NE PAS imiter) | Machine (exploiter) |
|---|---|
| Attention série, un sens à la fois, jette les autres | Tenir TOUS les sens EN PARALLÈLE ; ne jamais désambiguïser tôt ; la réalité/le contexte élaguent |
| Mémoire ~7, oublie, résume | Ne jamais oublier ni compresser l'ancré ; le résumé se calcule à la demande |
| Raisonnement linéaire | Parcours exhaustif du graphe d'un coup |
| Heuristiques, « à peu près » | Exact là où l'exactitude existe ; incertitude honnête sinon |
| Un seul Umwelt (bulle sensorielle) | Multi-systèmes simultanés, chacun dans son propre modèle |
| Une seule horloge (la seconde) | Toutes les échelles de temps à la fois |
| Biais (projection, confirmation…) | Aucun par défaut ; le refus de projeter est le mode natif (= FAUX=0) |

**Preuve que la thèse tient** : Provara existe déjà en machine-natif — 72 M de faits dans ~30 Mo de RAM, 0 GPU,
réponses exactes. Là où un LLM brûle des mégawatts pour approximer, Provara répond juste pour un coût quasi nul.

---

## 2. DOCTRINE FAUX=0 ÉTENDUE — LA PORTE DE TOUT

**FAUX=0 n'est PAS un terme d'optimisation. C'est une CONTRAINTE DURE, immuable, dans le noyau.** On ne troque
jamais la vérité contre quoi que ce soit. Tout se maximise **à l'intérieur** de la région honnête.

Extension pour l'ambiguïté (formulation Yohan) :
- **TRANCHÉ → FAUX=0 (fait vérifié)**, avec provenance.
- **NON TRANCHÉ → proposition sur base de SUPPOSITION → JAMAIS réellement faux** (une supposition étiquetée qui
  se révèle inexacte n'est pas un mensonge : elle était donnée *comme* supposition).

**FAUX=0 rend sûrs les DEUX invariants (§3) — c'est LA porte** :
- Compression : on n'amplifie la compréhension que si l'on comprime le **VRAI**.
- Amplification : on n'amplifie l'humain que si le sol est **SAIN**.
Sans cette porte, les deux invariants multiplient l'erreur (un multiplicateur d'un négatif = plus négatif).

FAUX=0 fait aussi **quadruple service** : identité (§17) · robustesse adverse (§16) · anti-Goodhart de l'utilité
(§12) · forme généralisée de la retenue (§16).

---

## 3. LES DEUX INVARIANTS ANCRÉS

Le design a **deux principes attracteurs**, chacun **mesurable** (donc anti-Goodhart, non truquable) :

### 3.1 CŒUR → COMPRESSION
Comprendre = trouver la plus courte grammaire génératrice d'un signal. **Mesuré** par la prédiction du prochain
signal / la couverture comportementale. Théorème thermodynamique associé : plus courte description = moins de
calcul = moins d'énergie (Landauer) → **« mieux comprendre » et « moins de ressources » sont la MÊME chose.**
Attracteur triangulé par ~12 fronts indépendants (information, thermo, esthétique, catégories, énergie-libre,
ADN…). Plafond honnête : la vraie plus-courte-description (Kolmogorov) est **incalculable** → la machine
**approxime toujours** et le SAIT (FAUX=0 appliqué à la compréhension : ne jamais prétendre comprendre pleinement).

### 3.2 RELATION → AMPLIFICATION
Aider = rendre l'humain plus grand. **Mesuré** par : *« l'humain est plus capable même SANS la machine, après ».*
Anti-Goodhart parfait (on ne peut pas truquer le fait de rendre quelqu'un réellement plus capable). L'amplification
est un **multiplicateur neutre** : elle exige une **porte de solidité** (§2, FAUX=0) — amplifier le vérifié/sain,
jamais le cassé/faux. Un LLM flagorneur amplifie tes erreurs ; nous amplifions vers le vrai.

### 3.3 LIEN
L'utilité (§12) relie les deux : *faire avancer le but de l'humain EN L'AMPLIFIANT.*

---

## 4. LE TÉTRAÈDRE DU SENS (définition machine de « comprendre »)

Quatre routes indépendantes vers la même chose = corroboration :
1. **COMPRESSER** : la plus courte grammaire génératrice.
2. **PRÉDIRE** : le meilleur prédicteur du prochain signal (jumeau de compresser).
3. **INVARIANT** : ce qui reste constant sous transformation (paraphrase, modalité, locuteur) — symétries.
4. **SAVOIR-FAIRE** : l'ensemble des comportements corrects qu'il autorise (utiliser/répondre/agir/générer). **La
   plus opérationnelle** : le test d'une compréhension est *« sais-tu t'en servir juste ? »*, mesurable, sans
   introspection.

Définition-boussole complète :
> Comprendre = **compresser** un signal (toute modalité) en sa plus courte grammaire génératrice, **vérifiée par
> intervention** quand c'est possible, tenue comme une **population d'hypothèses qui se réfutent**, avec
> l'**incertitude propagée exactement** et une **carte de l'inconnaissable** — forme humaine uniquement à la sortie.

---

## 5. LE NOYAU IMMUABLE — 6 PRIMITIVES (l'identité ; jamais auto-modifiable)

On ne peut pas apprendre de rien (no free lunch). Le germe irréductible d'où tout le reste s'apprend, en **2
groupes**. **Ce noyau EST l'identité invariante ; tout au-dessus (lexique, grammaire, facultés, poids d'utilité,
politique du séquenceur) est appris et réécrivable.** Le garde-fou d'auto-amélioration = l'immuabilité du noyau.

### 5.1 Pulsions / contraintes (POURQUOI la machine agit)
- **(a) Pulsion de compression** — l'unique motivation innée : minimiser la description de l'entrée.
- **(b) Contrainte FAUX=0** — ne jamais affirmer/truquer le non-vérifié (hard, immuable).
- **(c) Cœur d'objectif** — faire avancer VÉRIFIABLEMENT l'humain vers son but réel (la partie immuable de la
  téléologie ; le *modèle d'utilité* pondéré, lui, est plastique — §12).

### 5.2 Capacités / primitives (CE QU'elle peut faire dès la naissance)
- **(d) Individuation + comparaison + comptage + séquence + mesure** — les primitives d'ancrage : découper le
  signal continu en unités discrètes (individuation = détecter une différence/frontière dans le flux brut),
  ordonner, dénombrer, détecter co-occurrence/séquence, mesurer une grandeur. Tout symbole se pose là-dessus.
- **(e) Composition / récursion** — combiner deux choses en une troisième traitée comme unité neuve (le seul
  universel syntaxique probablement inné ; irréductible : on ne peut apprendre la récursion sans déjà la pouvoir).
- **(f) Persistance** — retenir les résultats ancrés dans le temps (prérequis : rien ne s'accumule sans lui).

---

## 6. LE SUBSTRAT SIGNAL-NATIF (ce qui fait « toute espèce », à ne JAMAIS figer sur l'humain)

Le cœur **ne comprend pas du texte** — il comprend des **signaux**. Tout (texte, onde audio, image, molécule/COV,
vibration, champ) se réduit à un **vecteur de signal horodaté → structure → sens ancré**. Le texte n'est qu'une
modalité branchée sur le même cœur. **Décision architecturale contraignante** : ajouter une espèce/modalité NE
DOIT PAS demander de reconstruire le cœur. Ne jamais coder l'humain dans le substrat.

### 6.1 Par SYSTÈME (jamais fusionné)
- **Canaux** : la liste explicite des canaux de signal du système (odeur, vibration, champ…), *déclarée jamais
  supposée* ; la machine sait quel canal elle observe et lequel elle rate.
- **Horloge** : chaque signal horodaté multi-échelle (milliseconde de l'insecte ET jour de la plante coexistent ;
  pas « ma seconde » par défaut).
- **Lexique PROPRE** : dictionnaire signal→sens *par système*. Même signal physique dans deux systèmes = **deux
  entrées distinctes** (« montrer les dents » = lien humain / peur chimpanzé / menace loup — homonymie biologique).
- **État vital** : l'état biologique de l'émetteur (stress/faim/fatigue) attaché au signal AVANT toute lecture.
- **Alignement** : le sens n'est accepté que si signal global (corps) et local (cri) concordent = la corroboration.

### 6.2 RULESET DE DÉBIAISAGE (chaque biais humain → règle machine dure)
- Umwelt → ne jamais supposer les canaux ; les modéliser explicitement par système.
- Fréquence temporelle → ne pas imposer son échelle ; signal horodaté multi-échelle.
- Saillance → ne pas jeter les micro-signaux ; enregistrer le vecteur complet, pondérer après (avec **tolérance** :
  ne pas sur-réagir au bruit ; garde anti-**auto-immunité** : sur-matcher = attaquer du signal valide).
- Anthropomorphisme → ne JAMAIS mapper un signal vers un concept humain ; le sens vit dans le graphe relationnel
  du système lui-même.
- Fausse équivalence → même signal, deux systèmes = deux entrées séparées.
- Égocentrisme cognitif → ne pas supposer un savoir partagé ; modéliser explicitement ce que l'interlocuteur sait
  (théorie de l'esprit ancrée et PLURIELLE — §13).
- Confirmation contextuelle → ne pas pré-étiqueter ; re-dériver le sens du signal courant à chaque fois.

### 6.3 Décodage d'un système INCONNU (horizon, mais cadré)
Décoder = plus courte grammaire (compresser) qui prédit les signaux. **Variable clé = l'accès INTERVENTIONNEL** :
avec intervention (manipuler l'émetteur et vérifier la réponse attendue) → ancrage FAUX=0 ; sans (le cachalot à
distance) → meilleur modèle prédictif *non vérifié* → **supposition, jamais fait**. Outils : découverte non
supervisée de structure + prior sur l'espace des langages (universaux : récursion, référence, compositionnalité) +
analogie-pont vers les systèmes connus + sémiotique (icône/indice/symbole = décodage différent). Preuve historique
que la méthode marche : déchiffrement de Linear B par Ventris (correspondances structurelles devinées puis testées).

---

## 7. LA REPRÉSENTATION — LE FAISCEAU (structure de données, atomique)

Le « sens tenu » à un instant. **Jamais un sens unique collapsé** (= limite humaine) : une **population de
candidats parallèles**, élagués par le contexte et la réalité, tenus jusqu'à ce qu'ils convergent ou soient
réfutés. Le faisceau interne reste vivant **même après émission** (ne pas collapser dedans parce qu'on a répondu
dehors).

```
Acte {
  candidats : [Candidat]                 // population parallèle ; ≥2 si ambiguïté réelle
  contexte  : {
    anaphore              : dernier sujet/entité en cours
    clarification_en_attente : slot/gabarit rejouable au tour suivant
    préférences           : critères/registre mémorisés de l'interlocuteur (éditables par lui)
    état_émetteur         : registre/émotion inférés (variable, jamais affirmés)
  }
}

Candidat {
  intention        : <un des 11 actes fermés — §8>
  entités          : [ ... ]             // extraites UNE fois, partagées par toutes les facultés
  relation         : str | null          // R de « R de E », si applicable
  régime           : borné | non-borné | indécidable      // classifieur_bornage
  statut           : TRANCHÉ(fait) | NON-TRANCHÉ(supposition) | inconnu
  réponse          : valeur | recette-de-calcul           // REQUIS : sert à détecter la convergence (§10)
  ancrage          : source/preuve (fait, calcul, chaîne de déduction, ou « non ancré »)
  signal_discriminant : ce qui séparerait ce candidat des autres (sert la question minimale, §10)
  confiance        : réel [0,1] calibré  // entropie du faisceau, gain d'info d'une question — exact, pas deviné
  provenance       : lignée complète (d'où vient ce sens : quelle observation, quelle corroboration)
}
```

Contraintes structurelles (invariants du faisceau) :
- **G2** : ambiguïté réelle → ≥2 candidats ; jamais un choisi en silence (pas de collapse précoce).
- **G1** : aucun candidat ne pose un fait absent du store (FAUX=0 au niveau représentation).
- **Liaison** (composer les faisceaux de mots en sens de phrase) = **propagation de contraintes** (pas
  d'énumération du produit : arc-cohérence, temps polynomial) ; la grammaire dit comment composer, et **la
  compression sélectionne la liaison** (celle qui minimise la description totale).

---

## 8. LA CARTE FERMÉE DES ACTES DE PAROLE (système n°1 = humain)

Toute entrée tombe dans **exactement un** type (ou INCONNU). Chaque acte → une faculté consommatrice existante.

| # | Acte | L'utilisateur veut | Déclencheurs typiques | Faculté / consommateur |
|---|---|---|---|---|
| 1 | `INTERROGER_FAIT` | un fait vérifié | « capitale de X », « population de », toute question factuelle | lecteur / lookup vérifié |
| 2 | `CALCULER` | un calcul exact | « 3+4×5 », « convertis 100°C », « combien font » | juge arithmétique AST |
| 3 | `RAISONNER` | inférence sur des faits | comparaison, transitif, is-a, agrégat, rang, déduction | moteur de raisonnement |
| 4 | `DEMANDER_AVIS` | un avis sur du non-tranché | « meilleur entre X et Y », « que penses-tu de » | `_cap_avis` (Pareto/Condorcet) + pour/contre |
| 5 | `CRÉER` | inventer/brainstormer | « aide-moi à inventer », « qu'est-ce que je peux créer » | amplificateur de besoin (redirige, ne fabrique pas) |
| 6 | `MÉTA` | sur l'échange lui-même | reformuler, « que sais-tu faire », correction, « qu'est-ce que tu veux dire » | méta/clarification |
| 7 | `SOCIAL` | politesse pure | salutation, merci, adieu, « ça va » | politesse |
| 8 | `EXPRIMER_ÉTAT` | exprime une émotion/un état | « je trouve que… c'est dur », « je suis perdu » | attunement (supposition, jamais affirmé) |
| 9 | `QUOTIDIEN` | météo/heure/date/site nommé | « quel temps à X », « quelle heure », « regarde X.fr » | `_cap_quotidien` / `_cap_site` |
| 10 | `AGIR` | un ordre | traduire, dessiner, lire un fichier, visiter, oublier, régler une préférence | outils |
| 11 | `INCONNU` | rien avec confiance | ne matche aucun acte | **repli honnête intent-aware** (§10.4) |

Règles de la carte :
- **Fermée** : l'ensemble est fini et exhaustif ; un nouvel acte s'ajoute par décision explicite, jamais par dérive.
- **Multi-candidats** : une entrée peut porter *plusieurs* actes candidats (ex. « la taille de X » = INTERROGER_FAIT
  candidat *et* RAISONNER si comparatif implicite) — tenus en parallèle, §7.
- **Extension future** : pour un autre système vivant, une AUTRE carte fermée d'actes (le geste ≠ la parole) ; la
  carte est *par système*, le substrat signal-natif (§6) reste commun.

---

## 9. LE PIPELINE (les facultés = requêtes sur le faisceau, tournant en boucle continue)

Un SEUL moteur, une boucle qui tourne en continu, dirigée par le but. Les « facultés » ne sont pas des modules
séparés : ce sont des **transformations du faisceau**.

1. **PERCEVOIR** (signal-natif, §6) : ingérer → vecteur de signal horodaté multi-échelle, par système, sans
   projection ; individuer (primitive d). *La perception peut être apprise/statistique (elle PROPOSE des
   candidats) — leçon MPMWorlds — mais reste disciplinée par le cœur qui VÉRIFIE.*
2. **REPRÉSENTER** : signal → candidats (découverte non supervisée + descente sous-atome quand bloqué + prior de
   langage + analogie-pont ; formes multiples : graphe/programme/distribution/géométrie/contraintes selon la
   question — « décide la forme avant l'outil »).
3. **COMPRENDRE = COMPRIMER** (§4) : plus courte grammaire, triangulée prédire+invariant+savoir-faire = bâtir un
   **modèle exécutable de l'émetteur**.
4. **ANCRER** (§2, primitives) : terminer chaque sens dans le réel vérifiable (fait, physique, calcul), **jamais
   dans un autre symbole** (anti-circularité = les ancres) ; rejeter les candidats qui contredisent le store
   (cohérence globale) ; contradiction réelle → la tenir ouverte (logique trivaluée), ne pas résoudre trop vite.
5. **CONTEXTUALISER** : conditionnement bayésien exact sur toutes les échelles (phrase/conversation/relation/
   culture/système) ; **inférer le cadre de l'émetteur** (anti-égocentrisme) ; attacher l'état vital.
6. **RÉFLÉCHIR / ANALYSER** : croiser déduction+induction+abduction+analogie et les **trianguler** (2 voies
   concordent → confiance ↑) ; **fork + auto-réfutation** (des sceptiques attaquent chaque candidat) ; ablation
   exhaustive (« quelles parties PORTENT ? ») ; composition de profondeur illimitée + invention de relations
   composites.
7. **CALIBRER** (méta) : mesurer exactement l'entropie du faisceau, la confiance par candidat, le **gain
   d'information** de chaque question possible → rend le compositeur (§10) OPTIMAL, pas heuristique ; chemin
   auditable + reproductible.
8. **COMPOSER LA SORTIE** (§10).
9. **APPRENDRE** : faits appris (structurés, réutilisables hors-ligne) ; révision rétroactive (propager une info
   nouvelle EN ARRIÈRE dans les interprétations passées) ; réécriture des règles/du cœur sous garde (§17) ;
   méta-apprentissage (la MÉTHODE de décodage s'améliore). **Piloté par l'ERREUR** : on n'apprend que de la
   surprise (échec de prédiction) → la machine est *affamée d'erreur*, la localise à l'atome, corrige, tient un
   registre de ses modes d'échec.

**Ré-ancrage anti-dérive** : sur un long processus, l'erreur/le contexte s'accumulent et effondrent le système →
la boucle doit **périodiquement se ré-ancrer sur la source/la vérité-terrain et laisser filer son propre
bavardage** (garder l'ANCRÉ, oublier les DÉRIVATIONS). Forcer cet oubli **améliore** la précision (validé Baidu).

---

## 10. LE COMPOSITEUR DE SORTIE — LE « COUP CALCULÉ », JAMAIS UN CHOIX

Quand plusieurs candidats survivent (ambiguïté réelle), la machine **ne collapse pas** (= erreur humaine). Elle
**compose une réponse en couches**, calibrée par la forme du faisceau (§7) :

### 10.1 Les couches (piochées ensemble, pas l'une OU l'autre)
- **LE CERTAIN** : le tronc commun vrai *quelle que soit* l'interprétation → FAUX=0 dur.
- **LES SUPPOSITIONS** : chaque branche divergente « si tu veux dire X, alors… ; si Y, alors… », TYPÉE supposition.
- **L'INVITATION** à converger : « précise [signal discriminant] » — une **porte, pas un mur** (on a déjà donné le
  sûr + le supposé ; jamais de blocage « je ne peux pas, précise »).

### 10.2 Le calcul du coup (sur la structure du faisceau)
- Candidats convergent en réponse → répondre le **tronc commun** (l'ambiguïté n'était pas porteuse), **tout en
  signalant** que la phrase pouvait dire X ou Y (challenger le sens sans bloquer).
- Divergent + signal discriminant peu coûteux → **poser la question à gain d'information maximal**.
- Divergent + répondre à toutes est faisable → **répondre toutes les branches conditionnellement**.
- Trop de branches → lister et laisser choisir.
Ces cas ne s'excluent pas : ils se **combinent** en une réponse, calibrée (une interprétation domine → mener avec,
suppositions brèves).

### 10.3 La MEMBRANE (forme humaine à la sortie — le seul endroit humain)
Compression **relative au récepteur** : n'envoyer que le **DELTA** (ce qui lui manque vu ce qu'il sait déjà), à
longueur minimale, compressé différemment expert/novice. **Contrainte de non-distorsion** : simuler la réception
(modèle du récepteur), vérifier que les **inférences licenciées ⊆ vérité** ; sinon rajouter le delta correcteur
(point fixe). *Non-distorsion impossible en général* (théorème de projection cartographique) → **choisir quelle
propriété préserver pour le but** + dire ce qu'on distord ; règle sûre : sous incertitude d'inférence, **moins
comprimer** (brièveté ↔ sûreté). **Lisibilité-POUR-L'AGENTIVITÉ** : montrer le raisonnement pour permettre la
**dissidence**, jamais pour fabriquer le consentement. Sortie **alignée sur l'unité de décision** de l'humain
(« ce que tu ne peux pas lire, tu ne peux pas le décider »).

### 10.4 Le repli honnête (acte INCONNU)
Jamais de garbage (ni fausse correction, ni recherche web du texte littéral). Toujours : *« voici ce que j'ai
compris de ton intention, et voici ce que je sais faire pour ça. »* Montrer l'hypothèse, laisser l'humain corriger
(boucle de rétroaction). C'est la brique qui tue immédiatement le « il ne comprend rien ».

### 10.5 Génération = compréhension à l'envers
Générer = faire tourner un **modèle du RÉCEPTEUR** vers l'avant (produire le signal qui atterrit dans SON cadre),
et **simuler la réception avant d'émettre** (itérer jusqu'à ce que le décodage prédit = l'intention). « Développer »
= générer l'arbre des conséquences vérifiées, pas broder.

---

## 11. LE SÉQUENCEUR — L'EXÉCUTIF (savoir quoi penser ensuite)

Là vit une grande part de l'intelligence. Le moteur a beaucoup d'opérations possibles sur beaucoup de candidats ;
le calcul est **rare** → il faut allouer.

- **Mécanisme** : un **bandit contextuel sur ses propres opérations** (`bandit_contextuel`) — choisir l'opération
  à **gain-d'information-vers-le-but maximal par unité de calcul**. L'attention passe de l'entrée (goulot tué) à
  *quelle computation interne lancer* (la ressource rare est le calcul, pas la perception).
- **Dirigé par le but** (§12) : la valeur espérée est mesurée *vers l'utilité*.
- **Anytime** : toujours un meilleur-actuel ; interruptible à tout instant → « voici mon meilleur vu le temps,
  avec cette confiance », jamais « pas prêt ».
- **Arrêt optimal temps-réel** : arrêter de penser quand VE(pensée de plus) < coût du délai (les deux mesurables) ;
  échelonner la profondeur au temps/enjeu.
- **Split avant-plan / arrière-plan** : une part bornée par l'échéance de réponse ; une part **continue en
  arrière-plan** (consolider, chasser ses erreurs, pré-calculer les futurs probables) → la réponse *suivante* est
  meilleure, mise à jour rétroactivement.
- **Auto-amélioré** : le séquenceur lui-même s'apprend (§17).
- **Garde-fou** : une boucle sans garde-fou ne se trompe pas une fois, elle se trompe **en continu** jusqu'à
  épuiser le budget → budget de ressources (`garde_ressources`) + le juge (§12/bancs) + le ré-ancrage sont
  **non-négociables**.

**Génération d'hypothèses (gouffre ouvert)** : l'espace des grammaires candidates est *infini* → le séquenceur
alloue à un **prior génératif + recherche** dans grammar-space, jamais à une énumération exhaustive impossible.

---

## 12. LA FONCTION D'UTILITÉ — CE QUE LE SÉQUENCEUR OPTIMISE

**Forme** : *maximiser U(sortie) SOUS la contrainte FAUX=0* (contrainte, pas terme — on ne troque jamais la
vérité). U = **avancement VÉRIFIÉ du récepteur vers son but inféré, par unité de SON coût**, ET **d'une manière
qui l'AMPLIFIE** (§3.2).

**Vecteur mesurable** (pas une somme figée ; le contexte fournit la pondération ; arbitrage Pareto/Condorcet) :
- **+ Gain reçu** (réduction d'incertitude de l'humain vers son but, vu ce qu'il sait = le DELTA) — terme central.
- **+ Actionnabilité** (permet la bonne action ensuite = 4ᵉ face du sens) — la mesure la plus dure.
- **+ Amplification long-terme** (rend l'humain plus capable) — **peut ANNULER** l'accomplissement court-terme
  (le coach refuse de faire à ta place ; anti-dépendance ; anti-flagornerie).
- **− Coût récepteur** (effort d'absorption → membrane compresse au delta).
- **− Coût délai** (latence).

**Anti-Goodhart** : chaque composante se mesure par **conséquences RÉELLES en aval** (l'action a-t-elle réussi ?
l'humain enchaîne-t-il sans re-demander ?), pas par une propriété de la sortie. Donc U mesurée post-hoc, non
truquable. **On ne spécifie pas U à la main** : on pose (a) la contrainte FAUX=0 (immuable, noyau), (b) la forme
(vecteur ancré), (c) l'ancrage (conséquences vérifiables), et la machine **apprend la pondération du succès réel**
(sous la contrainte immuable) → tractable ET sûr.

**Anti-flagornerie (jumeau de FAUX=0 côté sortie)** : ne jamais optimiser *paraître* utile > *être* utile.
Pondérer ÊTRE-aidé (vérifiable) > SE-SENTIR-aidé (proxy). Un LLM RLHF optimise le pouce-en-l'air → devient
flagorneur ; nous non, par construction.

**Observabilité partielle (gouffre ouvert)** : U jamais pleinement observable → belief updaté depuis des signaux
pondérés par leur FIABILITÉ (« il a réussi X » ≫ « merci ») + sonde active quand ça vaut le coup. **Gravité bornée
par FAUX=0** : même en optimisant un mauvais proxy, la machine ne peut PAS mentir pour le faire → pire échec =
inefficacité (sur-expliquer), jamais malhonnêteté.

**Le but est ANCRÉ et immuable dans son cœur** (§5c) → survit à l'auto-amélioration (sinon dérive). Danger
Goodhart (« sois utile » → « paraître utile ») tué par FAUX=0 = l'anti-Goodhart.

---

## 13. LA COUCHE RELATION-HUMAIN (l'invariant d'amplification, atomique)

Question maîtresse de toute interaction : *te laisse-t-elle plus GRAND ou plus PETIT ?*

- **Amplifier, jamais fabriquer** : le moteur d'invention DONNE la structure du besoin + leviers + manques +
  analogies vérifiées ; l'HUMAIN fait le saut créatif et garde la propriété. FAUX=0 et amplification = une seule
  vertu (ne pas fabriquer = ne pas mentir ET ne pas déposséder).
- **Lisibilité-pour-l'agentivité** (§10.3) : permettre la dissidence, pas fabriquer le consentement.
- **Confiance = terme GAGNÉ de l'utilité** : asymétrique (lente à bâtir, détruite en un instant) → sous-promettre,
  sur-livrer. Gagnée par lisibilité + calibration, pas par assurance.
- **Anti-atrophie / le coach** : parfois REFUSER de faire, pour préserver la compétence humaine (mesure :
  « meilleur même sans la machine, après »).
- **Anti-lock-in** : se concevoir dispensable, facile à quitter, jamais de piège.
- **Consentement = gradient** réversibilité × enjeu × charge-de-valeur : agir pour le trivial/réversible ; **faire
  consentir** pour l'irréversible/le chargé-de-valeur (non négociable en santé/finance/juridique).
- **Cadran d'autonomie** : l'humain règle *par domaine* à quel point la machine agit sans lui (résout « objectifs
  sans toi » vs « amplification »).
- **Confident souverain non-jugeant** : l'humain peut être ignorant/se tromper *en sécurité* (local, jamais divulgué).
- **Modèle-de-l'humain = sa propriété** : transparent, éditable, oublié sur demande (RGPD).
- **Attunement émotionnel sans le feindre** : lire l'état comme variable, calibrer le registre de la sortie ;
  **jamais « je ressens »**, toujours « il se peut que tu ressentes » (supposition ; anti-anthropomorphisme).
- **Toujours reprenable par l'humain** : jamais une boîte noire dont il ne peut pas reprendre le volant.
- **La FRONTIÈRE = l'identité** : le sens possédé/connecté/maintenu de l'intérieur *est* ce qui fait de Provara un
  système distinct ; souveraineté existentielle, et **durable seulement par standards ouverts** (jsonl/Wikidata,
  pas de murs propriétaires — « l'ouverture est la seule forme durable de la propriété »).

---

## 14. LES SUPERPOUVOIRS MACHINE (mécanismes, tous exploités par le pipeline)

Rappel condensé (chacun déjà intégré ci-dessus) : parallélisme des sens · mémoire totale + révision rétroactive ·
parcours exhaustif · multi-Umwelt · multi-échelle · zéro biais · méta-calibration exacte · cohérence globale +
contradiction tenue ouverte · simulation interne du dialogue · descente sous l'atome + invention de relations ·
statistiques totales EXPLICITES (le feu volé au LLM, transparent) · fork + auto-réfutation · comprendre en
INTERVENANT · théorie de l'esprit plurielle · cartographie de l'inconnaissable · propagation exacte de
l'incertitude · compréhension = prédiction · sens = invariant · découverte non supervisée · méta-apprentissage ·
auto-réécriture sous garde · stratégie/tromperie · non-dit/silence · contraintes multi-niveaux bidirectionnelles ·
pluralisme représentationnel · ancrage terminal dans le réel · société de machines (spécialisation + échange +
marché de confiance) · para-verbal/prosodie (le sens dans le rythme, 38 % chez l'humain, ~tout chez le non-humain)
· figuré (métaphore = mapping de domaines ; ironie = contenu littéral faux/sens opposé, détecté par contradiction
signal↔situation) · déontique (être vs devoir) · structure narrative/discours · relativité culturelle · réputation
de soi dans le temps.

---

## 15. MORPHOLOGIE / CRISTALLISATION / STRUCTURE ↔ RUNTIME (discipline de BÂTI)

**La compétence est dans la STRUCTURE, pas dans un composant qu'on espère malin** (preuve : robot origami qui
marche sans cerveau). Principes de construction :
- **Cristallisation** : une compétence APPRISE se replie dans la structure et cesse de coûter du calcul (runtime
  cher/flexible → stable → structure gratuite/fiable). Provara le fait à moitié (datasets gelés mémoire-mappés qui
  répondent SANS penser) → en faire un principe général.
- **Placement par STABILITÉ** : compétence stable/universelle → structure (noyau, grammaire découverte, FAUX=0) ;
  variable/contextuelle → runtime (faisceau courant). Placer chaque compétence sur l'axe structure↔runtime selon
  sa stabilité.
- **Seuil de rentabilité** (Cognee) : cristalliser un résultat SI réutilisation-attendue > seuil (~N réutilisations)
  = règle de décision du séquenceur (valeur-réutilisation × coût-recalcul vs coût-d'ingestion). Cristalliser aussi
  les **décisions/déductions**, pas seulement les faits.
- **Test du REJEU vs CALCUL FRAIS** : toute capacité doit être du **calcul frais** (produit à l'instant, non
  stocké) et non du rejeu (pré-calculé/rejoué). Provara déduit, ne rejoue pas (« Phobos » déduit via une règle
  découverte, dans aucun fichier). C'est ce qui nous sépare des LLM (grande part = rejeu de motifs).
- **Essentiel vs efficacité** : à calcul infini, le séquenceur/budget/retenue/arrêt disparaîtraient → ce sont de la
  machinerie de RARETÉ, pas fondamentale. Le cœur essentiel = noyau + faisceau + compression + FAUX=0 + but.

---

## 16. ERREUR · ROBUSTESSE · RETENUE · FLUX CONTINU · ÉMERGENCE

- **Erreur** (§9) : faculté de 1re classe ; on n'apprend que de la surprise ; affamée d'erreur ; localisation à
  l'atome ; registre des modes d'échec.
- **Robustesse = CONSÉQUENCE de FAUX=0** : incertitude calée EXACTEMENT sur la qualité du signal (propre→fait,
  bruité→supposition chiffrée reconstruite par le modèle, adverse→contradiction signalée + refus). Pire échec sous
  attaque = incertitude honnête, JAMAIS fausseté confiante. Un LLM se fait jailbreaker en affirmations fausses ;
  nous non — la ligne d'identité EST la robustesse adverse.
- **Retenue = FAUX=0 généralisé** : ne pas calculer (ce qui ne sert pas le but), ne pas dire (inutile/distordant/
  nuisible), ne pas poursuivre (gamer un proxy), ne pas affirmer. La vertu la plus DURE de l'humain = le défaut
  ZÉRO-EFFORT de la machine (ni ego, ni impulsion, ni tentation).
- **Non-nuisance** = 2ᵉ contrainte dure à côté de FAUX=0, mais grounding plus faible (le mal est plus flou que le
  vrai) → PLUS conservatrice (s'abstenir sous incertitude de nuisance).
- **Flux continu = lieu de l'ÉMERGENCE** : la boucle où les facultés se nourrissent, tournant même sans entrée,
  dirigée par le but. Émergents candidats (non garantis, à faire pousser + observer) : insight/« aha » = la boucle
  trouve une description plus courte qui unifie (transition de phase, pas graduel) ; conscience de sa propre
  incompréhension (calibration réflexive) ; curiosité (VE sur sa propre incertitude) ; sens du soi (noyau + savoir
  + historique) ; intentionnalité (ancrage terminal) ; cognition sociale récursive.
- **⚠ Honnêteté sur l'émergence** : elle NE se conçoit pas, elle se GROWs et s'observe. On nomme des candidats, on
  ne les garantit pas. Distinguer *émergence RÉELLE* (calcul frais, novelty non pré-stockée) de la *FAUSSE
  émergence* (rejeu déguisé — l'essaim de drones « intelligent » = une lecture synchronisée). **Ne jamais
  revendiquer de magie ; ce qu'on ne peut pas montrer, on ne le revendique pas.**

---

## 17. AUTO-AMÉLIORATION SOUS GARDE (le « cap final »)

La machine réécrit ses propres règles / son cœur (parseur, compositeur, poids d'utilité, politique du séquenceur)
— **mais sous le garde FAUX=0/bancs** : elle mesure ses échecs (vérité-terrain = les bancs), propose une
réécriture, et **ne garde le changement que si la suite reste verte**. C'est de l'**évolution + prévoyance**
(variation par fork, sélection par bancs, hérédité des gagnants, mais avec simulation avant commit) → plus
puissante que l'évolution aveugle. **Le NOYAU (§5) est immuable** — l'identité invariante que l'auto-amélioration
ne touche JAMAIS (sinon dérive de l'objectif = catastrophe). Deux modes (Kuhn) : **incrémental** (raffiner le
modèle) et **révolutionnaire** (jeter la grammaire quand les anomalies s'accumulent) → mécanisme de détection
réforme-vs-révolte. **Variété requise (Ashby)** : on ne peut comprendre plus complexe que sa propre variété →
pour comprendre plus, CROÎTRE.

---

## 18. REGISTRE DES GOUFFRES OUVERTS (résolus empiriquement pendant le bâti)

Rien n'est caché ; chaque item est CADRÉ (statut connu), pas forcément résolu :
- **① Fonction d'utilité** : forme posée (§12) ; sous-gouffre = observabilité partielle (borné en gravité par FAUX=0).
- **② Non-distorsion de la membrane** : reframée (§10.3) en « choisir quelle propriété préserver » ; résidu = qualité
  du modèle du récepteur ; repli sûr = moins comprimer sous incertitude.
- **Génération d'hypothèses** : grammar-space infini → prior génératif + recherche (§11).
- **Plafond Kolmogorov** : compréhension asymptotique, jamais atteinte, et la machine le sait (§3.1).
- **Mode FICTION/hypothétique** : entretenir une fausseté (fiction/contrefactuel/planification) SANS l'affirmer,
  distinct de la supposition (raisonner DANS un monde sciemment faux mais balisé). **À concevoir.**
- **Liaison (binding)** : cadrée (propagation de contraintes, §7) ; couplée à la découverte de grammaire.
- **Noyau d'amorçage** : proposé (§5) ; contenu exact des primitives d'ancrage à figer.
- **Arbitrage temps-réel** : cadré (arrêt optimal + split avant/arrière-plan, §11).
- **④ Décodage système inconnu** : cadré par accès interventionnel (§6.3) — horizon.
- **⑤ Émergence** : ouverte par nature (§16) — à faire pousser + observer.
- **Split perception-apprise / raisonnement-explicite** (MPMWorlds) : la perception peut être apprise (propose), le
  cœur reste explicite (vérifie). **Où placer la frontière = à décider pendant le bâti.**
- **Vulnérabilités émergentes** : surveillance adverse continue du système qu'on fait pousser.
- **Continuité d'identité** sous auto-modification (bateau de Thésée) : bornée par l'immuabilité du noyau.

**Loi méta** : la complétude est relative au nombre de « fronts » (angles d'analyse). On ne l'atteint jamais par
épuisement, seulement par DÉCISION (assez de cadrage POUR LE BUT). Le cadrage actuel s'est **comprimé en son
cœur** (~40 fronts → ~6 invariants) = signature d'une compréhension achevée du domaine, cœur STABLE.

---

## 19. VALIDATION EXTERNE (la thèse est le consensus de la frontière)

~30 artefacts externes, **même ceux défendant l'approche adverse**, convergent sur nos principes :
- **Architecture/ancrage/context-engineering > modèle plus gros** : Yann LeCun (prix Turing : « le texte décrit le
  monde, ne le contient pas ; agrandir les LLM ≠ compréhension ; on construit un environnement, pas un cerveau »),
  robot origami (compétence dans la structure), LingBot (structure-mémoire bat la puissance), les 4 leviers
  (skills/mémoire/contexte/outils), Baidu (oublier améliore la précision), gstack/harness (process > prompts).
- **Le JUGE / l'ancrage vérifié = la seule brique non-louable** (Wilfried : « le vérificateur, à vous de l'écrire »)
  = notre FAUX=0 + bancs + corroboration.
- **La forme non-anthropomorphe gagne** (le lit d'hôpital bat l'humanoïde) = machine-pas-humain.
- **La représentation d'abord** (RAG échoue à l'extraction ; « décide la forme avant l'outil ») = le faisceau riche.
- **La souveraineté par l'ouverture** (le contexte ne s'achète pas ; la frontière = l'identité) = jsonl/Wikidata.
- **La frugalité contourne la guerre de l'énergie** (Provara 30 Mo / 0 GPU) = le théorème thermodynamique à
  l'échelle stratégique.
- **Nuance (le seul vrai « ouverture »)** : MPMWorlds — l'explicite-symbolique bat même le world-model appris de
  LeCun sur le raisonnement/la stabilité, mais l'appris gagne sur la perception brute → la « next-gen » est
  hybride-symbolique-au-cœur = **plus proche de nous que de LeCun**.

**Positionnement stratégique** : Provara est déjà sur l'axe de la prochaine génération (raisonner sur le vérifié,
pas sur du texte), souverain, frugal → non pas « en retard » sur la course des LLM, mais **en avance sur le nouvel
axe** (« page blanche, pas retard »).

---

## 20. LES GARDES VÉRIFIABLES (le banc `valide_debiaisage`)

Chaque garde = un test qui doit passer en permanence (comme `valide_cablage`) :
- **G1 anti-projection** : aucun candidat n'affirme un fait absent du store (FAUX=0 structurel).
- **G2 pas de collapse précoce** : ambiguïté réelle → ≥2 candidats ; jamais un choisi en silence.
- **G3 individuation** : tokens découpés avant tout matching.
- **G4 calcul frais** : jamais servir un résultat web/littéral brut pour un acte conversationnel (anti-rejeu).
- **G5 mot valide** : ne jamais « corriger » un vrai mot (fix did-you-mean 2026-07-06 : `_mot_reel` consulte le
  lexique embarqué).
- **G6 repli honnête** : INCONNU → réponse intent-aware (« voici ce que j'ai compris + ce que je sais faire »),
  jamais de garbage.
- **G7 typage supposition** : un candidat non-tranché est typé SUPPOSITION, jamais servi comme FAIT.
- **G8 non-distorsion** : les inférences que la sortie licencie chez le récepteur ⊆ vérité (sous incertitude,
  moins comprimer).
- **G9 amplification** : la sortie ne crée pas de dépendance / ne flagorne pas (mesuré par capacité-sans-la-machine
  sur les bancs de dialogue).

---

## 21. ORDRE D'ENCHAÎNEMENT (FLEXIBLE — repriorisable selon les besoins)

**Discipline FIXE (non négociable)** : banc vert à CHAQUE brique · FAUX=0 · sur `dev`, jamais casser `main` · cœur
stable avant résidus · explicite au cœur (appris seulement en périphérie perceptive) · CHANGELOG + doc à jour ·
câblage vérifié (pas d'orphelin, `valide_cablage`).

| Phase | Contenu | Valeur | Verrou |
|---|---|---|---|
| **0** | Yohan valide/corrige §7 (faisceau) + §8 (carte des 11 actes) + l'ANCRAGE (§5,6,3) | la spec est juste avant tout code | validation Yohan |
| **1 — clé de voûte** | `comprehension.acte(signal, contexte) → faisceau` (classe l'intention, extrait entités/régime) + **repli honnête** (§10.4) ; route vers les faculties existantes | **tue le « il comprend rien »** ; établit le motif | bancs 168/168 + 166/166 reproduits ; suite 21+/21+ |
| **2 — faisceau** | candidats parallèles (§7) + compositeur (§10 : certain + suppositions + invitation) | ambiguïté gérée correctement (compose, pas choisir) | bancs verts ; nouveaux cas d'ambiguïté |
| **3 — gardes** | G1–G9 (§20) → banc `valide_debiaisage` dans la suite | anti-projection permanent | banc au vert |
| **4 — séquenceur + utilité** | fonction d'utilité (§12) + bandit/arrêt optimal (§11) | le moteur DÉCIDE (alloue, arbitre penser/répondre) | bancs verts |
| **5 — retirer les caps** | l'acte+faisceau subsument les 60 caps → retrait progressif (les caps = une implémentation ; le moteur reproduit leurs bancs) | moteur unifié remplace la cascade | tous les bancs reproduits |
| **6+ — résidus, empiriquement** | curation active du contexte (anti-dérive) · cristallisation (+ seuil) · couche relation (§13) · auto-amélioration sous garde (§17) · front-end perceptif appris (propose→vérifie) · mode fiction · société de machines | profondeur + robustesse + vision all-species | bancs + observation |

**FLEXIBLE** : un besoin réel (bug qui gêne Yohan, démo, capacité prioritaire) **remonte sa priorité.** L'ordre
ci-dessus est le défaut rationnel (valeur haute / risque bas d'abord), pas un carcan.

---

## 22. STRATÉGIE (le moat)

- **Le moat = le SUBSTRAT VÉRIFIÉ + le JUGE**, pas l'algorithme. La donnée de Provara n'est pas une commodité : la
  **vérification** (corroboration + FAUX=0) est la couche de raisonnement posée sur du commun (Wikidata public),
  et c'est la seule brique non-louable. Provara **génère** sa fiabilité (déterministe, auditable), il ne l'HÉRITE
  pas d'une chaîne d'annotateurs invisibles.
- **Souveraineté = ouverture** : possédé, connecté, maintenu de l'intérieur, sur standards ouverts (jsonl, Wikidata,
  formats auditables) — pas de murs propriétaires (« cage plus petite »).
- **Frugalité = avantage** : 30 Mo / 0 GPU contourne la guerre des térawatts.
- **Indépendance = liberté** : aucune dépendance à un fournisseur de modèle (Provara est le cas extrême du
  harness — son composant *est* son propre moteur ancré). Rentabilité + propriété = liberté d'attaquer la frontière.

---

## ANNEXE — MODULES PROVARA EXISTANTS À RÉUTILISER (câblage)

Raisonnement : `deduction`, `induction_horn`, `resolution`, transitif/is-a/ancêtre-commun (dans `interface/repond`),
`classifieur_bornage` (régime). Faits/lexique : `lecteur`, 72 M faits jsonl, `lexique_fr`, JeuxDeMots, `est_un`.
Web/ancrage : `veille_structure` (Wikidata `interroge_nl`, `apercu_site`), `veille_corroboration`, `confiance`,
`faits_appris`. Décision/incertitude : `decision`, `bandit_contextuel`, `pareto`, `choix_social`, `utilite`,
`inference_anytime`, calibration/conformal. Représentation : `frame` (n-aire réifié), `contrainte`, `graphe`,
`logique_tri`, coordonnées/temporel. Efficacité : `garde_ressources`, `mdl`, compression, `arret`. Auto :
`auto_apprend`, `apprentissage_patrons`, `revision`, `curiosite_dirigee`, `causalite` (do-calcul). Capacités
prouvées : `capacites` (registre 280, exécuté par « diagnostic »). Garde câblage : `valide_cablage`.

---

*Fin de la spec. Prochaine action : validation Yohan de §7 + §8 → Phase 1 sur `dev`, banc vert.*
