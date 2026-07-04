# Architecture de Provara

> Règle fondatrice, gravée dans chaque couche : **FAUX = 0**. Provara ne répond que
> lorsqu'un juge réel (lookup vérifié, calcul effectivement évalué, référentiel
> sourcé) a tranché. Partout ailleurs, il *cadre* (supposition), *demande*
> (clarification) ou *s'abstient* (HORS). Il n'affirme jamais au hasard.

Ce document décrit l'architecture **telle qu'elle existe dans le code**
(`ia.py`, `lecteur.py`, `base_faits.py`, `classifieur_bornage.py`,
`assistant_nl.py`). Il ne décrit aucune capacité qui n'y figure pas.

---

## 1. Principe directeur : des modules atomiques à frontières étanches

Provara n'est pas un modèle monolithique : c'est un **assemblage de modules
atomiques**, chacun responsable d'un seul type de vérité et chacun accompagné de
son propre validateur.

Le point d'entrée `ia.py` l'énonce lui-même : *« Cette façade n'ajoute pas de
logique de vérité — elle ORCHESTRE. »* La façade se contente de router vers des
briques déjà validées ; sa docstring cite par exemple `classifieur 26/26`,
`invention_gap 12/12`, `chercheur 11/11`, `bibliothèque 11/11`,
`auto_optimise 12/12`.

Trois propriétés découlent de ce découpage :

- **Frontière étanche** : chaque module a un contrat clair (entrées, sorties,
  statut). Un module n'écrase jamais la vérité d'un autre. Exemple concret dans
  `lecteur.py` : ingérer une valeur *divergente* pour une clé déjà présente lève
  `ValueError` — refus, pas d'écrasement silencieux.
- **Abstention par défaut** : sans preuve, une brique renvoie `HORS` / `None` /
  `ABSTENTION` plutôt qu'une devinette. Une erreur de routage dégrade donc au
  pire le *cadrage*, jamais la *véracité*.
- **Validateur dédié** : chaque brique a son harnais de non-régression. La
  soundness est vérifiée module par module, pas globalement supposée.

C'est ce qui rend le slogan FAUX=0 structurel plutôt que déclaratif : il n'y a
pas un endroit unique où « faire attention », il y a des frontières qui refusent
d'inventer.

---

## 2. Les couches

### 2.1 Le magasin de faits (`base_faits.py` + `lecteur.py`)

C'est le socle : *« on ne répond QUE si le fait est présent et vérifié ; sinon
HORS honnête. Jamais de dérivation probabiliste, jamais de devinette. »*

**`base_faits.py` — l'amorce vérifiée à la main.**
Chaque fait est un enregistrement immuable `Fait(valeur, categorie, source)` :

- `categorie` porte la *nature* de la contrainte : `CAT_PHYSIQUE` (observé,
  modèles révisables), `CAT_PASSE` (figé, irréversible), `CAT_CONVENTION` (fixé
  par accord : langue, unités, normes) ;
- `source` porte la *traçabilité* (ce qui ancre la vérité).

Le lookup est exact, sur clé normalisée par `normalise()` (minuscule, sans
accents, sans ponctuation, espaces compactés) :

```python
cherche(relation, entite)   # -> Fait, ou None (jamais un faux)
repond_nl(question)         # extrait (relation, entite) de quelques gabarits sûrs
```

C'est une amorce *volontairement petite mais 100 % vérifiée*. Ce qui compte est
le mécanisme (lookup-jugé + HORS), pas le volume.

**`lecteur.py` — le lecteur générique du borné DATA.**
Même contrat sound, généralisé à des tables entières. La docstring l'explique :
pour un fait passé, une convention ou une constante mesurée, *la réalité fixe la
réponse mais l'IA ne peut pas la DÉDUIRE — la deviner serait halluciner*. La
brique auto-constructible est donc le *lecteur d'un référentiel*, jamais le
contenu.

- `ingere_table(relation, lignes, categorie, source)` : ingestion générique
  d'une table `entité -> valeur`. Une valeur divergente sur une clé existante ->
  `ValueError` (source autoritative incohérente, pas d'écrasement). Réingérer la
  même valeur est idempotent ; clé/valeur vide est ignorée.
- `cherche` / `repond(relation, entite)` : lookup exact sur les tables ingérées,
  **repli** sur l'amorce figée `base_faits` (corpus complémentaires, relations
  distinctes).
- `repond_nl(question)` : quelques gabarits NL pour les tables ingérées, repli
  complet sur `base_faits.repond_nl` — jamais de régression de couverture,
  jamais d'invention.

Le contrat de soundness est structurel : présent + vérifié -> `Fait` complet
(valeur + catégorie + source) ; absent ou hors-gabarit -> `(HORS, None)`.

**Stockage.** Le lecteur charge en mémoire des tables figées et compactes. Une
table mono-source gelée est représentée en colonnes (`_ColTable`) : clés triées
dé-objetisées en un seul blob `str` + `array` d'offsets (`_Cles`), codes entiers
de valeurs, catégorie/source stockées une seule fois par table, `Fait`
reconstruits à la volée et mutualisés par valeur distincte. Un backend `.colf`
*mmappé* (`_ColTableMmap`) permet une RAM partagée/réclamable et un chargement
quasi gratuit. Les réponses restent identiques ; seule la dépense mémoire baisse.

### 2.2 Le gardien de bornage (`classifieur_bornage.py`)

C'est le **routeur de statut** anti-hallucination. Il ne produit jamais de
réponse — il décide *quel régime du contrat d'atome* s'applique, donc si la
réalité a le droit de trancher.

Il croise **deux axes** :

- **ontologique** : la réalité fixe-t-elle la réponse, indépendamment de qui
  pose la question ? -> `BORNE` / `NON_BORNE` / `INDECIDABLE` ;
- **accès** : un juge réel peut-il trancher *maintenant* ? ->
  `JUGE_DISPO` / `PAS_DE_JUGE`.

Le croisement produit le régime :

| Ontologie × Accès          | Régime                       | Signification                              |
|----------------------------|------------------------------|--------------------------------------------|
| BORNÉ + JUGE_DISPO         | `R_FAIT`                     | la réalité tranche — **seul chemin qui affirme** |
| BORNÉ + PAS_DE_JUGE        | `R_SUPPOSITION_A_CHERCHER`   | une vérité existe, non vérifiée -> à chercher |
| NON_BORNÉ                  | `R_SUPPOSITION_OPINION`      | jugement calibré, pas de vérité à trancher |
| INDÉCIDABLE                | non-borné conservateur       | au doute sur le *statut*, jamais borné     |

Points de conception qui garantissent FAUX=0 :

- **`JUGE_DISPO` n'est jamais déduit d'un marqueur lexical.** Le seul juge
  *interne* est arithmétique (`_juge_arith`) : il évalue réellement une
  expression via un AST sûr, et seulement si l'expression **couvre toute** la
  question (aucun chiffre orphelin, aucune opération en toutes lettres). Le verbe
  « calculer » seul, ou une plage « 1990-2000 », n'accordent pas le juge.
- **Biais conservateur.** Un prédicat non-borné dur (goût, esthétique,
  prescription morale, prédiction future, fiction, opinion demandée) *préempte*
  le juge : une opinion ne devient jamais un fait à cause d'un chiffre qu'elle
  contiendrait. Une année *future* est classée non-bornée (le futur n'est pas un
  fait), mais une année passée reste un fait datable.
- Un `juge_verdict` externe (résultat d'un vrai juge déjà exécuté par
  l'appelant) peut être fourni et **prime** : une question tranchée par la
  réalité est bornée-accessible, même si son libellé contient un marqueur ambigu.

`Classement.route_fait()` renvoie `True` **uniquement** si `BORNE` et
`JUGE_DISPO`. Une mauvaise classification dégrade donc le cadrage (chercher vs
opinion), jamais la véracité.

### 2.3 La porte conversationnelle (`assistant_nl.py`)

C'est l'**enveloppe qui parle une seule langue** en sortie. Elle *n'ajoute aucun
étage de connaissance* : elle réutilise le pipeline conversationnel existant
(`interface/repond.py` : politesse, méta, cascade factuelle vérifiée, mémoire de
dialogue, did-you-mean) et le complète de trois capacités.

Toute réponse sort dans une enveloppe uniforme :

```python
@dataclass(frozen=True)
class Reponse:
    statut: str      # fait | supposition | clarification | echange | hors
    texte: str
    regime: str      # régime d'atome décidé par le gardien de bornage
    source: str      # provenance quand FAIT
    attente: str     # ce que le tour suivant doit préciser (clarification)
```

Les trois capacités ajoutées :

1. **Routage par bornage après HORS.** Quand la cascade factuelle n'a rien, on
   consulte `classifieur_bornage` : régime FAIT (calcul couvrant réellement
   évalué) -> on répond ; NON-BORNÉ -> cadrage honnête ; BORNÉ sans juge ->
   recherche autonome sur les sources de confiance (`veille.py`, opt-in
   `IA_WEB=1`) ; INDÉCIDABLE -> question de clarification.
2. **Clarification avec état.** Une question de clarification (« vouliez-vous
   dire X ? ») reste *en attente* par conversation. Si le tour suivant la
   *confirme*, la question d'origine est réécrite avec la correction confirmée
   puis retraitée. Jamais de substitution silencieuse ; un anti-boucle limite les
   clarifications « indécidable » consécutives.
3. **Enveloppe uniforme** via la porte unique `ia.assistant(question)`.

La classification de l'enveloppe est **positive** : chaque texte terminal
non-factuel est reconnu par sa constante/son préfixe (`qualifie_texte`). Il n'y a
jamais de défaut « fait » pour un texte non identifié. Le rappel de dialogue est
typé *supposition rapportée* (l'utilisateur l'a dit — vrai ; le contenu n'est pas
vérifié) ; le web reste *supposition rapportée* tant que non corroboré.

Le module est *import-léger* (OOM-safe) : au niveau top, seulement la stdlib +
`base_faits` + `classifieur_bornage`. Le pipeline complet, `veille` et
`conversation` sont importés paresseusement.

### 2.4 Les moteurs de calcul (façade `ia.py`)

Au-delà du lookup, Provara expose des **moteurs déterministes** dont chaque réponse
est re-vérifiable. La façade `ia.py` les regroupe par familles ; l'idée commune
est *calcul exact ou abstention*, jamais d'approximation servie comme un fait.

- **Sciences bornées.** `ia.chimie("H2O")` (masse molaire…), `ia.physique(...)`
  (grandeurs SI transcrites de CODATA), `ia.genetique(seq)`, et un juge de
  **cohérence physique** — `ia.juge_dispositif(spec)` tranche l'*impossibilité*
  d'un dispositif vs les principes de conservation/entropie (VIOLE /
  COHERENT_BORNE / HORS). La cohérence n'est jamais une preuve d'efficacité :
  l'asymétrie est explicite.
- **Conventions & référentiels.** `ia.reference(v, quoi="morse"|"nato"|...)`,
  `ia.donnee(relation, entite)` et sa variante NL `ia.donnee_nl(question)`
  (lecteur DATA : lookup-ou-HORS + repli amorce).
- **Géographie dérivée.** À partir de coordonnées ingérées : `ia.coordonnees_lieu`,
  `ia.distance_lieux` (orthodromie, modèle sphérique — fait *dérivé* à portée
  explicite, pas une donnée stockée), `ia.cap_lieux`, conversions cartographiques.
  Indicateurs pays (Banque mondiale, instantanés datés) et dérivés
  (`densite_pays`, `pib_par_habitant_calcule`) renvoient `None` (HORS) si un
  pivot manque.
- **Graphe & ontologie du monde.** `ia.voisins(entite)` / `ia.chemin(a, b)`
  (arêtes = faits réels re-vérifiables), `ia.est_un(x, type_)` (subsomption
  transitive en monde ouvert : `False` = « non dérivable des faits présents »,
  jamais « faux »).
- **Modalités & production de fichiers.** Géométrie, dessin SVG, image raster/PNG,
  audio WAV, tableur XLSX, PDF, graphiques : chaque encodeur produit des octets
  valides, déterministes, re-décodables à l'identique. Le noyau est borné
  (géométrie/octets exacts) ; l'esthétique reste non jugée.
- **Raisonnement structuré & découverte.** `ia.demande(...)` (aiguillage par
  nature de réalité vers l'exécuteur, le moteur de règles ou l'audit de code),
  `ia.invente(...)` (tranche une fonction-cible vs l'existant :
  EXISTE_DEJA / INVENTION / AMBIGU / BRIQUE_MANQUANTE / INCOHERENT),
  `ia.decouvre_loi(data)` (loi symbolique exact-fit-ou-abstention, held-out
  obligatoire), invention divergente (`apprend_loi`, `leve_contrainte`,
  `transfere_analogie`, `arbitre_compromis`, `explique_observations`,
  `plan_procede`) et invention sur le réel (`attribut_derivable`,
  `inventions_composites`). Toutes ces briques *abstiennent sans preuve*.

### 2.5 L'ingestion (scripts `ingere_*` -> `datasets/*.jsonl` -> lecteur)

L'architecture d'ingestion sépare strictement l'*online* de l'*offline* :

- les scripts `ingere_*.py` (online) récupèrent des sources réelles et écrivent
  des fichiers `*.jsonl` ;
- le lecteur charge ces fichiers **offline** via `charge_dossier()` : chaque
  fichier est *self-describing* — sa première ligne non vide est un en-tête
  `{_relation, _categorie, _source, _articles?}`, les suivantes des faits
  `{entite, valeur}`. `charge_dossier` ne fait **aucun accès réseau** (le réseau
  vit dans les scripts `ingere_*`).

Toute ligne passe par les mêmes garde-fous que `ingere_table` : conflit divergent
refusé, idempotence, clé/valeur vide ignorée. Le chargement gèle les tables
mono-source en colonnes (et peut warm un cache binaire `.colf` mmappable) pour
réduire le pic mémoire, sans changer les réponses.

### 2.6 La calibration (familles de modules non-bornés, façade `ia.py`)

Le non-borné n'est pas de la vérité : c'est de l'opinion qui doit rester
*honnête sur son incertitude*. Provara expose une large famille de briques
statistiques, toutes accessibles derrière des wrappers `ia.*` uniformes (souvent
un paramètre `phrase=` pour une sortie en langue). Regroupées par ce qu'elles
permettent de FAIRE :

- **Instrumenter la confiance** : calibration (ECE/Brier), scores propres
  (log-loss, CRPS), tests de calibration, détection de dérive de calibration.
- **Encadrer par intervalles garantis** : méthodes conformes (adaptatif,
  normalisé/Mondrian, quantile, jackknife+, pondéré pour covariate shift),
  intervalles de tolérance, bandes CDF.
- **Combiner et décider** : combinaison bayésienne d'indices (y compris
  corrélés), agrégation d'opinions d'experts, décision à utilité espérée,
  bandits, contrôle de risque (FNR/FDR).
- **Modéliser sous incertitude épaisse** : Dempster-Shafer, arithmétique
  d'intervalles, p-box, modèles imprécis/robustes, décision sous ambiguïté.
- **Ordre de grandeur & populations biaisées** : Fermi, échantillon pondéré,
  méta-analyse, taux de Poisson, valeurs extrêmes, survie, données manquantes.

Le rôle de la calibration dans l'invariant FAUX=0 est net : ces sorties ne sont
jamais servies comme des *faits*. Elles portent leur statut de supposition
calibrée — l'honnêteté sur l'incertitude, pas une prétention au vrai.

---

## 3. Le trajet d'une question : du langage naturel au verdict typé

Une question arrive en langage naturel. Elle traverse les couches jusqu'à un
**verdict typé** : fait, supposition, clarification, échange, ou abstention.

```
                            question en langage naturel
                                       │
                                       ▼
                    ┌──────────────────────────────────────┐
                    │  PORTE CONVERSATIONNELLE (assistant_nl) │
                    │  pipeline vérifié : politesse / méta /  │
                    │  cascade factuelle / mémoire dialogue   │
                    └──────────────────────────────────────┘
                          │ trouvé ?                 │ social / méta ?
             ┌────────────┴───────────┐              └──────────► ECHANGE
             │ OUI                    │ NON (HORS)
             ▼                        ▼
   MAGASIN DE FAITS         ┌──────────────────────────────────┐
   base_faits / lecteur     │  GARDIEN DE BORNAGE               │
   lookup exact + repli     │  (classifieur_bornage.classe)     │
             │              │  ontologie × accès -> régime      │
             ▼              └──────────────────────────────────┘
           FAIT               │            │             │            │
     (valeur + source)   R_FAIT      NON_BORNE   BORNE ss juge   INDECIDABLE
                              │            │             │            │
                              ▼            ▼             ▼            ▼
                    juge arithmétique  cadrage      recherche     question de
                    AST couvrant       honnête      web opt-in    clarification
                              │        (SUPPO-      (SUPPO         (on demande,
                              ▼         SITION)      rapportée)     jamais deviner)
                            FAIT                        │            │
                     (calcul évalué)                  HORS +      CLARIFICATION
                                                     provenance
```

Lecture du schéma :

1. La **porte conversationnelle** tente d'abord le pipeline vérifié. Un fait
   présent dans le **magasin** (base_faits/lecteur) ressort en `FAIT` avec sa
   provenance. Une interaction sociale/méta ressort en `ECHANGE`.
2. Si rien n'est trouvé (`HORS`), le **gardien de bornage** classe la question.
3. Selon le régime :
   - `R_FAIT` via le juge arithmétique interne (et seulement s'il *couvre toute*
     la question) -> `FAIT`, source « calcul arithmétique (AST évalué,
     couvrant) » ;
   - `NON_BORNE` -> `SUPPOSITION` (cadrage honnête : « la réalité ne fixe pas de
     réponse unique, je n'affirmerai donc pas un fait ici ») ;
   - `BORNE` sans juge -> recherche autonome sur les sources de confiance ;
     résultat *rapporté* (SUPPOSITION) ou `HORS` honnête + provenance ;
   - `INDECIDABLE` -> `CLARIFICATION` : on pose la question, on ne devine jamais.

À aucun moment un chemin ne fabrique un fait : les seules affirmations sortantes
viennent du pipeline vérifié, du magasin de faits, ou d'un calcul réellement
évalué et couvrant.

---

## 4. Où vit l'invariant FAUX=0

L'invariant n'est pas un contrôle central ; il est réparti sur les frontières :

- **`base_faits` / `lecteur`** : lookup exact ou `(HORS, None)` ; conflit
  d'ingestion refusé (`ValueError`).
- **`classifieur_bornage`** : sound par construction — il *route*, ne produit
  aucune affirmation ; le seul chemin qui affirme exige un juge réel ; biais
  conservateur au doute.
- **`assistant_nl`** : classification positive de l'enveloppe (jamais un défaut
  « fait ») ; web et mémoire de dialogue typés *supposition rapportée*.
- **Moteurs de calcul** : exact-fit-ou-abstention, held-out, encodages
  re-décodables ; l'efficacité/l'esthétique explicitement *non jugées*.
- **Calibration** : sorties portées comme suppositions calibrées, jamais comme
  faits.

C'est la somme de ces refus locaux — et non une garantie globale posée après
coup — qui fait tenir la promesse : *au moindre doute, cadrer, demander, ou
s'abstenir ; ne jamais affirmer un faux.*
