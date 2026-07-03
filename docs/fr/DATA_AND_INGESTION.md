# Données & ingestion

Cette page décrit **d'où viennent les faits de VERAX** et **comment ils y entrent**. Elle
ne documente que ce qui existe réellement dans le code (`sources.py`, `veille.py`,
`veille_corroboration.py`, la famille `ingere_*.py`). Un principe gouverne tout ce qui suit
et n'admet aucune exception :

> **FAUX = 0.** Un fait n'entre dans le magasin que s'il est vérifié. Au moindre doute,
> il n'entre pas — l'IA préfère l'abstention (« HORS ») à une réponse fausse.

Ce principe est appliqué **deux fois** : une fois à la lecture des sources (on ne retient
que le certain), une fois à l'écriture dans le magasin (une valeur divergente de ce qui est
déjà connu est **refusée**).

---

## 1. D'où viennent les faits

Les faits sont importés depuis des **sources structurées et autoritatives**. Le réseau ne
vit que dans les scripts d'ingestion ; chaque table de faits **cite sa source**. Les
sources réellement utilisées par le code :

- **Wikidata**, de deux façons :
  - via l'endpoint officiel **WDQS** (`query.wikidata.org`, SPARQL) — lu dans le registre
    sous l'identifiant `wikidata-wdqs` (`ingere_wikidata.py`). Cet endpoint est agressivement
    limité (429, « 1 req/min »), d'où un *retry* poli intégré.
  - via **QLever** (`qlever.dev/api/wikidata`), un miroir SPARQL haute-performance NON
    limité de la même manière (`ingere_qlever.py`). C'est lui qui débloque le volume ;
    syntaxe légèrement différente (pas de `SERVICE wikibase:label` — les libellés FR sont
    récupérés explicitement via `rdfs:label` + `FILTER(lang=...)`).
- **Banque mondiale** — API v2 publique sans clé (`api.worldbank.org`), pour les indicateurs
  pays : population, PIB, PIB/habitant, chômage, inflation, espérance de vie, indice de Gini
  (`ingere_worldbank.py`).
- **Periodic-Table-JSON** (Bowserinator, CC-BY-SA 3.0), servi en *raw* GitHub non limité —
  propriétés physiques des éléments chimiques (`ingere_elements_ptjson.py`, id registre
  `periodic-table-json`).
- **mledoze/countries** (*raw* GitHub, base derrière l'ancien REST Countries) — géographie
  neutre en langue : codes ISO, indicatifs, continents (`ingere_geo.py`, id `mledoze-countries`).
- **Dictionnaires** — le Wiktionnaire français via **kaikki.org**, sous forme d'un *dump*
  local déjà converti (`datasets/lexique_kaikki_full.jsonl`), pour le lexique : genre
  grammatical, définitions, catégorie lexicale (`ingere_lexique.py`, `ingere_kaikki.py`) ;
  et les **lexèmes** Wikidata (`ontolex:LexicalEntry`) via QLever (`ingere_t9_lexemes.py`).

À côté de ces sources en réseau, un ensemble de petits scripts **hors-ligne** apporte des
tables de convention **stables et non contestées** (couleurs sRGB canoniques, formules brutes
« textbook », danse → pays d'origine, etc.). Elles n'ont pas de source réseau mais suivent
**exactement le même pipeline de vérification** (section 4).

---

## 2. Le registre de sources (`sources.py`)

`sources.py` charge un catalogue local (`datasets/sources/registry.jsonl`) : pour chaque
source, son `id`, son `url`, son `type`, les `domaines` couverts, les `relations` alimentées,
une note de fiabilité. C'est **la seule source de vérité pour les URLs** : les scripts
d'ingestion n'ont pas d'endpoint codé en dur, ils le lisent ici.

```python
import sources
sources.url("wikidata-wdqs")        # l'endpoint SPARQL officiel, lu depuis le registre
sources.pour_domaine("chimie")      # « où irais-je apprendre la chimie ? »
sources.pour_relation("capitale")   # « d'où vient un fait de type 'capitale' ? »
```

Le registre est le pendant « provenance » du lecteur : le lecteur dit *ce que l'IA sait*, le
registre dit *d'où elle le tient et où aller le ré-apprendre*. Son chargement est **purement
local** (aucun accès réseau).

---

## 3. Online une fois, offline à l'usage

C'est l'architecture centrale, et elle est explicite dans chaque docstring d'ingestion :

- **L'ingestion est ONLINE et lancée à la main**, une fois. Un script `ingere_*.py`
  télécharge (SPARQL / API), filtre, réconcilie, et **écrit des fichiers**
  `datasets/lecteur/<relation>.jsonl` auto-descriptifs.
- **La lecture de la base est hors-ligne.** Le `lecteur.py` charge ces `.jsonl` par auto-découverte,
  sans réseau. Les validateurs et la non-régression tournent donc **sans connexion**.
- **Reproductibilité :** chaque *pull* réseau est archivé en **snapshot brut** sous
  `datasets/_raw/<nom>.json` (compressible en `.xz`, rejeu transparent). Relancer un script
  quand le snapshot existe **ne re-tape pas le réseau** : il rejoue le brut hors-ligne et
  régénère les tables à l'identique.

Pendant l'ingestion, le lecteur est importé en mode « amorce seule »
(`LECTEUR_AMORCE_SEULE=1`) pour rester léger (import quasi-instantané, RAM ~0).

---

## 4. Le pipeline commun : `publie()`

Qu'une source soit en réseau ou hors-ligne, chaque relation passe par la même fonction
`publie(relation, categorie, source, paires)` (dans `ingere_wikidata.py`). Elle enchaîne :

1. **`fonctionnel`** — on ne garde qu'**un fait par entité** s'il n'a **qu'une seule valeur
   distincte**. Une entité multivaluée (deux langues officielles, deux genres…) est
   **rejetée (HORS)** — jamais un choix arbitraire. C'est la première garde FAUX=0.
2. **`reconcilie`** — chaque valeur est comparée à l'**amorce canonique**
   (`lecteur.amorce_cherche`). Identique → réécrite (idempotent). **Divergente → NON écrite** :
   elle part dans `datasets/_conflits/<relation>.jsonl` pour **audit humain** (souvent une
   simple variante de surface). Le magasin vérifié ne peut pas être écrasé silencieusement.
3. **`ecrit_jsonl`** — écriture d'un fichier **auto-descriptif** : un en-tête
   (`_relation`, `_categorie`, `_source`, `_articles`) puis les faits `{entite, valeur}`.
   L'écriture est **atomique** (fichier temporaire + `os.replace`) : un crash en cours
   d'écriture ne laisse jamais un `.jsonl` tronqué ni ne détruit la table valide précédente.
4. **`ecrit_conflits`** — journalise les divergences pour relecture.

La `categorie` distingue notamment `physique` (fixé par la réalité mesurable) de `convention`
(fixé par un usage : symbole, monnaie, terme normalisé). La source est **toujours citée**
dans la table (ex. « Wikidata — capitale P36 », « Banque mondiale SP.POP.TOTL — millésime … »).

Les valeurs **volatiles** (population, PIB…) sont traitées honnêtement : on prend la valeur
la **plus récente** (`mrnev=1` côté Banque mondiale) et on **trace son millésime** dans la
source — c'est un instantané **daté**, jamais servi comme « live ».

---

## 5. La boucle « va chercher → corrobore → juge → n'écrit que le vérifié »

Pour apprendre au-delà des imports déterministes, VERAX dispose d'un accès web **discipliné**
(`veille.py`) et de la boucle de promotion (`veille_corroboration.py`). Elle rend
l'apprentissage **non-éphémère** sans jamais relâcher FAUX=0.

Discipline (`veille.py`) :

- Toute information du web est une **SUPPOSITION rapportée**, **jamais un fait**. Elle porte
  sa **provenance** (URL + domaine + empreinte de contenu) et une confiance basse.
- Accès **souverain** : `urllib` seul, `http/https` uniquement, taille bornée (2 Mo), UA
  explicite. Toute erreur (pas de réseau, statut ≥ 400, réponse vide/hors-taille) →
  **HORS**, jamais une info fabriquée (dégradation gracieuse).
- **Pas d'extraction de faits depuis du HTML libre** : c'est un risque d'hallucination
  assumé et refusé. Les faits fiables viennent des sources **structurées** (SPARQL/API), où
  l'extraction est déterministe. La veille fournit la récupération, le typage « rapporté »,
  la provenance et la corroboration — pas la fabrication.

Promotion (`veille_corroboration.corrobore_valeur`) — une valeur rapportée ne devient un fait
persisté que si **tous** les maillons tiennent ; sinon on **s'arrête au premier échec** :

1. **OBSERVER** — la valeur est vue sur des sources (chaque observation = domaine + url + valeur).
   Ce n'est encore qu'une supposition.
2. **CORROBORER** — on compte les sources **INDÉPENDANTES**. `independantes()` exige un seul
   témoignage par **domaine** ET des empreintes de contenu **distinctes** : *trois sources qui
   se recopient ≠ corroboration*. Il faut au moins `minimum` (défaut : 2) domaines indépendants.
3. **JUGER** — un **juge réel** (`atome.Verdict`, pas un booléen nu). Le juge par défaut,
   `juge_coherence_store`, confronte la valeur candidate au magasin : elle **ne doit pas
   contredire** un fait déjà connu. L'appelant peut injecter un autre juge (cohérence
   physique, un test, une falsification…).
4. **PERSISTER** — écriture **conflit-refusée** (`ia.ingere_donnees` / `lecteur.ingere_table`
   lève sur valeur divergente) : la **seconde garde FAUX=0**, au moment d'écrire. La provenance
   (sources + juge) est tracée dans la source du fait.

Le résultat est l'un de quatre statuts explicites :

| statut     | signification |
|------------|---------------|
| `PERSISTE` | corroboré + jugé + écrit dans le magasin |
| `SUPPOSE`  | corroboration ou juge insuffisant → reste supposition, **rien n'est stocké** |
| `CONFLIT`  | promu, mais le magasin détenait une valeur divergente → **écriture refusée** |
| `REFUTE`   | le juge réel a réfuté le candidat (garde anti-re-proposition) |

La boucle est **injectable** (observations et fonction de persistance) : elle se teste
entièrement hors réseau et hors lecteur lourd.

---

## 6. Les familles de scripts d'ingestion

Il existe 147 scripts `ingere_*.py`. Tous convergent vers `publie()` (donc mêmes gardes),
mais ils se regroupent en familles selon ce qu'ils permettent d'apprendre :

- **Wikidata à grande échelle (WDQS + QLever).** Le cœur du volume. `ingere_wikidata.py`
  fournit les briques génériques (`sparql`, `fonctionnel`, `reconcilie`, `publie`,
  snapshots) et couvre p. ex. géographie FR (capitale/monnaie/langue), éléments chimiques,
  points culminants. `ingere_qlever.py` passe par le miroir non-limité et ajoute des
  garde-fous (rejet des dates ayant « fui » dans un champ lieu, rejet des libellés = Q-ID
  nu). Les gros scripts de **couloirs thématiques** (`ingere_t4.py` … `ingere_t12.py`)
  réutilisent ces fabriques pour importer, domaine par domaine, à l'échelle — chacun scouté
  puis relu, `fonctionnel` rejetant tout libellé multivalué.
- **Indicateurs pays (Banque mondiale).** `ingere_worldbank.py` — débloque les moteurs
  éco/démo (densité, PIB/habitant, chômage, inflation, Gini…). Une fonction générique
  `ingere_indicateur` applique la recette « population » à chaque indicateur, en alignant
  les clés sur le **nom FR** via le mapping ISO-3 (mêmes clés que `superficie`).
- **Chimie / tableau périodique.** `ingere_elements_ptjson.py` (propriétés physiques :
  masse, électronégativité, points de fusion/ébullition, configuration électronique…),
  plus les tables de composés, ions, familles chimiques. La jointure vers le nom français
  se fait **par le symbole** (jamais de traduction hasardeuse) ; les valeurs prédictives
  d'éléments non confirmés sont écartées.
- **Géographie neutre en langue (mledoze).** `ingere_geo.py` — uniquement le sûr et le
  neutre (codes ISO, indicatif, continent) ; les libellés qui seraient en anglais dans la
  source ne sont **pas** chargés, pour ne pas polluer une base francophone.
- **Langue & lexique (dictionnaires).** `ingere_lexique.py` / `ingere_kaikki.py` (dump
  Wiktionnaire FR : genre, définitions), `ingere_t9_lexemes.py` (lexèmes Wikidata),
  affixes, écritures… Permet de répondre sur le genre grammatical, la catégorie lexicale,
  le sens d'un mot — avec rejet des formes fléchies et des mots à genre ambigu.
- **Tables de convention hors-ligne, stables et certaines.** Une longue série de petits
  scripts (couleurs sRGB, formules brutes, danses → pays, symboles, unités, notes de
  musique, lettres grecques…). Pas de réseau ; faits non contestés ; même pipeline
  `publie()`, donc mêmes gardes fonctionnelles et anti-conflit.

Regroupées ainsi, ces familles couvrent le **borné** (là où la réalité fixe la réponse) :
géographie, chimie, physique, économie/démographie pays, biologie, langue, culture de
référence — chacune traçable jusqu'à sa source.

---

## 7. Lancer une ingestion

Un script d'ingestion est une commande **manuelle**. Il télécharge (ou rejoue le snapshot),
écrit les `.jsonl`, et rappelle de valider hors-ligne.

```bash
# Wikidata WDQS — un ou plusieurs domaines en argument (défaut : geo)
python3 ingestion/ingere_wikidata.py geo
python3 ingestion/ingere_wikidata.py elements sommets

# Wikidata via le miroir QLever (défaut : tous les domaines)
python3 ingestion/ingere_qlever.py

# Propriétés des éléments (nécessite d'abord symbole_chimique.jsonl, cf. ingere_wikidata elements)
python3 ingestion/ingere_elements_ptjson.py

# Indicateurs Banque mondiale (population + éco/social)
python3 ingestion/ingere_worldbank.py

# Table de convention hors-ligne
python3 ingere_danses.py
```

Chaque exécution affiche, par relation, le nombre de faits écrits, les rejets pour
multivaluation et les conflits d'amorce :

```
[capitale                ] écrits= 191  rejets_multi=  3  conflits_amorce=  1  -> _conflits/capitale.jsonl
```

Après toute ingestion, on **rejoue la non-régression OFFLINE** pour vérifier que rien n'a
régressé et que FAUX=0 tient :

```bash
python3 _nonreg.py --full --jobs 6
```

Les conflits éventuels (`datasets/_conflits/<relation>.jsonl`) sont relus à la main : ils
signalent une divergence entre la source et l'amorce canonique, et **rien n'a été écrasé** en
attendant l'arbitrage. C'est, une fois de plus, FAUX=0 : on préfère un trou honnête à un
fait douteux.
