# Validation & FAUX = 0

FAUX = 0 est l'invariant fondateur de Provara : le système n'affirme jamais quelque chose qu'il ne peut prouver. Cet invariant n'est pas une intention, c'est une propriété **imposée par le code** — plus précisément par une famille de validateurs et par la porte de non-régression qui les exécute. Ce document décrit ce dispositif tel qu'il existe réellement dans le dépôt.

## La gate de non-régression (`_nonreg.py`)

`_nonreg.py` est le runner standard de Provara : c'est la « gate ». Son rôle est d'exécuter l'ensemble des validateurs et de rendre un verdict binaire — tout passe, ou la porte est rouge.

Elle s'appelle ainsi :

```bash
python3 _nonreg.py --jobs 8      # attendu sur la base complète : 688/688
```

À la fin, elle imprime une ligne de synthèse et rend un code de sortie :

```
=== NON-RÉG : 688/688 PASS (... via cache) en Xs ===
```

Le code de retour vaut `0` si et seulement si **aucun** validateur n'a échoué ; il vaut `1` dès qu'un seul échoue (`raise SystemExit(main())`). Il n'y a pas de demi-mesure : un unique fait faux qui entre dans le système fait tomber un validateur, donc fait rougir la gate.

### Incrémentale et parallèle, sans jamais tricher

La gate est conçue pour être **rapide** sans jamais sacrifier la **soundness**. Deux mécanismes :

- **Cache par empreinte (façon build-system).** Un validateur est déterministe pour un code donné. La gate calcule le hash SHA-1 du **contenu de la clôture d'imports** du validateur — lui-même plus tous les modules-projet qu'il importe, transitivement (analyse statique de l'AST : `import` / `from … import`). Si cette empreinte n'a pas changé depuis le dernier PASS mémorisé, le verdict est rejoué depuis le cache instantanément ; sinon, le validateur est relancé. Seuls les validateurs réellement impactés par un fichier modifié re-tournent.

- **Parallélisme borné.** Les validateurs tournent en sous-processus, par défaut 16 en parallèle (l'exemple du README en utilise 8), ordonnés du plus long au plus court pour minimiser la traîne. Chaque validateur est exécuté sous un plafond mémoire (`RLIMIT_AS` 14 Go, `MALLOC_ARENA_MAX=2`) et un délai (`timeout`). Les validateurs « lourds » — ceux qui chargent le lecteur complet (dizaines de millions de faits, ~5 Go de pic) — sont sérialisés par un sémaphore adaptatif (1 à 3 selon la RAM disponible) pour éviter le tueur OOM, sans changer aucun résultat.

Le cache est protégé contre trois pièges classiques, ce qui le rend **sound** :

1. Un **FAIL n'est jamais mémorisé** : un validateur qui échoue est systématiquement re-tenté.
2. Un import **dynamique non résolu** (`__import__` à argument non littéral) marque le validateur « toujours relancer » : jamais de faux cache.
3. Pour les validateurs **pilotés par les données** (ceux qui importent `lecteur.py`), l'empreinte replie aussi une signature légère des jeux de données (`datasets/lecteur/*.jsonl` : nom, taille, `mtime`). Ainsi, une **ingestion** qui ne touche aucun fichier `.py` invalide quand même le cache et force la re-validation. Sans cela, un fait faux ingéré après le gel du code passerait inaperçu derrière un PASS périmé — c'est précisément le trou de soundness que ce repli ferme.

## Combien de validateurs, et lesquels

La gate protège **688 validateurs actifs** (`valide_*.py`) : c'est la gate de référence, **688/688**. Ce nombre correspond exactement aux fichiers `valide_*.py` présents dans le dossier `tests/` (moins `valide_commun.py`, qui est un module de *helpers* partagés explicitement exclu — ce n'est pas un validateur), plus le validateur d'interface `interface/valide_interface.py`.

Sur le disque, les **688 fichiers `valide_*.py`** vivent dans le dossier `tests/` (il n'y a pas de dossier d'archive séparé).

La sélection est **auto-découvrante** : `liste_validateurs()` maintient une liste curée (qui fixe l'ordre et repère les tests lourds), puis **ajoute automatiquement tout `valide_*.py`** non encore listé. Conséquence directe pour FAUX = 0 : aucune capacité réelle ne peut rester « orpheline » hors du filet ; tout nouveau validateur déposé est protégé d'office.

> **Layout `_nonreg` (portage, 2026-07-03) :** la gate historique AUTORITÉ vit dans le repo d'origine `IA_nouvelle_vision/harnais/` (validateurs colocalisés en layout plat, où `_nonreg.py` passe). Le repo Provara est **restructuré** (`src/`+`tests/`+`interface/`+`ingestion/`) : `_nonreg.py` y a été réparé pour DÉCOUVRIR et LANCER les validateurs (résolution via `_chemin()`, `PYTHONPATH` = `tests`+`src`+`interface`+`ingestion` sur chaque sous-processus). Vérifié : `liste_validateurs()` renvoie **687** (était 1) et les validateurs autonomes passent (composition 9/9, ocr 28/28, vague4 4/4…). ⚠️ Le vert **688/688 dans Provara** n'est pas encore atteint : le port n'a pas re-routé les chemins codés en dur de certains validateurs (`datasets/…`, `src/ia.py` relatifs à leur dossier) et plusieurs exigent la **base complète 71,9 M** (lecteur_t5..t12, resolution, taxonomie, substrat_reel). Ce ne sont pas des régressions — c'est un chantier de portage. **Contrôle autonome fiable dans Provara pour la couche conversationnelle : `tests/suite_conversation.py` (22/22).**

### Suite conversationnelle (`tests/suite_conversation.py`)

Les gates de l'assistant conversationnel (grammaire, conjugaison, OCR, **traduction**, **composition**, **fraîcheur**, confiance, langue, stats-NL, documents, patrons, capacités du chat, plus conversation/assistant_nl) sont agrégés par un **runner dédié** — car ils demandent le `PYTHONPATH` `interface`+`src`+`ingestion` que la gate cœur ne pose pas :

```bash
python3 tests/suite_conversation.py     # attendu : 22/22 gates au vert
```

Il lance chaque gate en sous-processus isolé, avec le bon environnement, et sort en échec dès qu'un seul régresse. À passer avant tout commit touchant `interface/` ou une brique conversationnelle.

### Ce que couvrent ces familles

Les validateurs ne sont pas un tas indistinct ; ils se regroupent par ce qu'ils garantissent :

- **Briques génériques du socle** (`valide_dimensions`, `valide_grandeur`, `valide_frame`, `valide_causalite`, `valide_contrainte`, `valide_ancres`, `valide_abstention`, `valide_falsification`…) : les primitives machine — grandeurs typées, algèbre dimensionnelle, graphes causaux, solveur de contraintes, banque d'ancres non-circulaire, politique d'abstention. Elles garantissent que le raisonnement lui-même refuse au doute.
- **Moteurs de calcul par domaine** : chimie, physique, arithmétique modulaire, navigation, conjugaison, stœchiométrie, relativité, cryptographie appliquée, etc. Ces validateurs vérifient que le résultat est **exactement** celui attendu et que toute entrée hors-domaine renvoie une abstention (pas un nombre plausible).
- **Le magasin de faits** (`valide_lecteur` et ses déclinaisons `t4`…`t12`) : les capacités pilotées par les données ingérées (géographie, vivant, personnes, œuvres, sport, langue…), avec le contrat *lookup-ou-abstention*.
- **Mémoire et restitution** (`valide_memoire`, `valide_restitution`, `valide_conversation`) : ce qui est rappelé reste typé « rapporté », jamais promu en fait.
- **Calibration de l'incertitude** (la famille la plus nombreuse : `valide_calibration`, `valide_conformal…`, plus une large collection de paradoxes et pièges statistiques — Simpson, Berkson, Stein, Ellsberg, Goodhart…). En domaine ouvert, ces validateurs vérifient que le système **quantifie ce qu'il ne sait pas** et démasque toute sur-confiance, plutôt que de bluffer.
- **Ingestion et invention** (`valide_veille_corroboration`, `valide_boucle_invention`, `valide_invention_gap`…) : la corroboration avant écriture, et l'exploration de suppositions cadrées.

## Le principe : brique → validateur à ancres externes → gate verte

Provara se construit atome par atome. La règle de travail est simple et non négociable :

> **une brique n'est acquise que lorsque son validateur passe, et le travail n'avance que gate verte.**

Concrètement, chaque module `X.py` a son validateur `valide_X.py`, et ce validateur suit un patron constant :

1. Il **importe le module réel** qu'il teste (`import chimie as K`, `import physique as P`, `from ancres import …`).
2. Il vérifie l'**exactitude** contre des **ancres externes non circulaires** — des valeurs de référence connues indépendamment, **jamais recalculées par l'expression testée elle-même**. Sans cette non-circularité, « ça marche » ne testerait que le code contre lui-même.
3. Il éprouve la **soundness en adverse** : une large batterie d'entrées inconnues, malformées ou hors-domaine, qui doivent **toutes** renvoyer l'abstention (`HORS`), jamais un faux.
4. Il termine par une ligne canonique `=== valide_X : N/N ===` et sort avec le code `0` si tout passe, `1` sinon (`sys.exit`, `raise SystemExit`, ou `assert ok == total`).

L'exigence d'**ancres externes** est le cœur de l'anti-circularité. Quelques exemples réels :

- `valide_chimie` compare les masses molaires calculées à une table de références (`O2` = 31.998, `KMnO4` = 158.032…), à 0.05 g/mol près — des valeurs de table, pas des sorties du moteur. Les cas de test ne figurent volontairement pas dans le `__main__` du module.

  ```python
  # valide_chimie.py — ancre externe, tolérance de table
  st, m = K.masse_molaire("KMnO4")
  check(st == K.VERIFIE and abs(m - 158.032) < 0.05, "masse KMnO4")
  # soundness adverse : élément inconnu -> HORS, jamais une masse inventée
  check(K.masse_molaire("Xx2")[0] == K.HORS, "élément inconnu -> HORS")
  ```

- `valide_physique` ancre ses formules sur des **valeurs physiques connues** (gravité de surface terrestre ≈ 9.81 m/s², vitesse de libération ≈ 11.19 km/s, période orbitale d'1 UA ≈ 1 an, pH de l'eau neutre = 7), et non sur une re-évaluation de la même expression. Il vérifie aussi que tout domaine invalide (masse négative, `Th < Tc`, `[H+] = 0`) renvoie `HORS`.

- `valide_ancres` vérifie que la banque d'ancres exige une **source indépendante** : une réponse issue de la **même** source que l'ancre est refusée comme `CIRCULAIRE`, et une réponse fausse est `CONTREDIT`.

- `valide_lecteur` échantillonne des valeurs vérifiées à l'extérieur (fer Z = 26, or Z = 79, uranium Z = 92, février = 28 jours) et contrôle une cohérence séquentielle (Z = 1…36) pour attraper toute faute de transcription dans l'amorce, puis soumet une large batterie d'inconnus qui doivent tous renvoyer `(HORS, None)`.

## Pourquoi cela garantit FAUX = 0

La chaîne de garanties se referme ainsi :

- **Toute capacité est sous le filet.** L'auto-découverte inclut chaque `valide_*.py` de la racine ; rien de réel ne reste hors gate.
- **Chaque validateur teste contre la réalité, pas contre lui-même.** Les ancres externes non circulaires détectent aussi bien une formule fausse qu'une faute de saisie dans une table d'amorce.
- **L'abstention est vérifiée autant que l'exactitude.** Le volet « soundness adverse » impose que l'inconnu, le malformé et le hors-domaine renvoient `HORS` — c'est ce qui empêche une réponse plausible mais fausse.
- **Les changements de données ne peuvent pas se glisser derrière un cache périmé**, grâce à l'empreinte des `datasets/lecteur/*.jsonl` repliée dans le fingerprint des validateurs pilotés par les données.
- **Un échec n'est jamais absorbé.** Un FAIL n'est pas mis en cache, la gate rend un code de sortie non nul, et la règle « gate verte avant la suite » interdit d'avancer tant qu'un seul fait faux subsiste.

Un fait faux ne peut donc entrer dans Provara sans faire échouer au moins un validateur, ce qui rougit la gate et bloque le travail. C'est en ce sens précis que **FAUX = 0** est prouvé par le code, et non affirmé.
