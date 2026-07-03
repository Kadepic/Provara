# Data & ingestion

This page describes **where VERAX's facts come from** and **how they get in**. It
documents only what actually exists in the code (`sources.py`, `veille.py`,
`veille_corroboration.py`, the `ingere_*.py` family). One principle governs everything that follows
and admits no exception:

> **FAUX=0.** A fact enters the store only if it is verified. At the slightest doubt,
> it does not enter — the AI prefers abstention (“HORS”) over a wrong answer.

This principle is applied **twice**: once when reading the sources (only the certain is
retained), once when writing to the store (a value diverging from what is
already known is **refused**).

---

## 1. Where the facts come from

Facts are imported from **structured and authoritative sources**. The network
lives only in the ingestion scripts; each fact table **cites its source**. The
sources actually used by the code:

- **Wikidata**, in two ways:
  - via the official **WDQS** endpoint (`query.wikidata.org`, SPARQL) — read in the registry
    under the identifier `wikidata-wdqs` (`ingere_wikidata.py`). This endpoint is aggressively
    rate-limited (429, “1 req/min”), hence a built-in polite *retry*.
  - via **QLever** (`qlever.dev/api/wikidata`), a high-performance SPARQL mirror NOT
    limited in the same way (`ingere_qlever.py`). It is what unlocks the volume;
    slightly different syntax (no `SERVICE wikibase:label` — the FR labels are
    fetched explicitly via `rdfs:label` + `FILTER(lang=...)`).
- **World Bank** — public keyless v2 API (`api.worldbank.org`), for country
  indicators: population, GDP, GDP per capita, unemployment, inflation, life expectancy, Gini index
  (`ingere_worldbank.py`).
- **Periodic-Table-JSON** (Bowserinator, CC-BY-SA 3.0), served as *raw* GitHub un-rate-limited —
  physical properties of the chemical elements (`ingere_elements_ptjson.py`, registry id
  `periodic-table-json`).
- **mledoze/countries** (*raw* GitHub, the base behind the former REST Countries) — language-neutral
  geography: ISO codes, calling codes, continents (`ingere_geo.py`, id `mledoze-countries`).
- **Dictionaries** — the French Wiktionary via **kaikki.org**, as an already-converted
  local *dump* (`datasets/lexique_kaikki_full.jsonl`), for the lexicon: grammatical
  gender, definitions, lexical category (`ingere_lexique.py`, `ingere_kaikki.py`);
  and the Wikidata **lexemes** (`ontolex:LexicalEntry`) via QLever (`ingere_t9_lexemes.py`).

Alongside these networked sources, a set of small **offline** scripts brings
**stable and uncontested** convention tables (canonical sRGB colors, raw
“textbook” formulas, dance → country of origin, etc.). They have no network source but follow
**exactly the same verification pipeline** (section 4).

---

## 2. The source registry (`sources.py`)

`sources.py` loads a local catalog (`datasets/sources/registry.jsonl`): for each
source, its `id`, its `url`, its `type`, the `domaines` covered, the `relations` fed,
a reliability note. It is **the single source of truth for URLs**: the ingestion
scripts have no hard-coded endpoint, they read it here.

```python
import sources
sources.url("wikidata-wdqs")        # l'endpoint SPARQL officiel, lu depuis le registre
sources.pour_domaine("chimie")      # « où irais-je apprendre la chimie ? »
sources.pour_relation("capitale")   # « d'où vient un fait de type 'capitale' ? »
```

The registry is the “provenance” counterpart of the reader: the reader says *what the AI knows*, the
registry says *where it got it from and where to go re-learn it*. Its loading is **purely
local** (no network access).

---

## 3. Online once, offline in use

This is the central architecture, and it is explicit in every ingestion docstring:

- **Ingestion is ONLINE and launched by hand**, once. An `ingere_*.py` script
  downloads (SPARQL / API), filters, reconciles, and **writes** self-describing
  `datasets/lecteur/<relation>.jsonl` files.
- **Reading the base is offline.** The `lecteur.py` loads these `.jsonl` by auto-discovery,
  without network. The validators and non-regression therefore run **without connection**.
- **Reproducibility:** each network *pull* is archived as a **raw snapshot** under
  `datasets/_raw/<nom>.json` (compressible to `.xz`, transparent replay). Re-running a script
  when the snapshot exists **does not re-hit the network**: it replays the raw offline and
  regenerates the tables identically.

During ingestion, the reader is imported in “boot only” mode
(`LECTEUR_AMORCE_SEULE=1`) to stay light (near-instant import, RAM ~0).

---

## 4. The common pipeline: `publie()`

Whether a source is networked or offline, each relation goes through the same
`publie(relation, categorie, source, paires)` function (in `ingere_wikidata.py`). It chains:

1. **`fonctionnel`** — only **one fact per entity** is kept if it has **only a single
   distinct value**. A multi-valued entity (two official languages, two genders…) is
   **rejected (HORS)** — never an arbitrary choice. This is the first FAUX=0 guard.
2. **`reconcilie`** — each value is compared to the **canonical boot**
   (`lecteur.amorce_cherche`). Identical → rewritten (idempotent). **Divergent → NOT written**:
   it goes to `datasets/_conflits/<relation>.jsonl` for **human audit** (often a
   mere surface variant). The verified store cannot be silently overwritten.
3. **`ecrit_jsonl`** — writing a **self-describing** file: a header
   (`_relation`, `_categorie`, `_source`, `_articles`) then the facts `{entite, valeur}`.
   The write is **atomic** (temporary file + `os.replace`): a crash mid-write
   never leaves a truncated `.jsonl` nor destroys the previous valid table.
4. **`ecrit_conflits`** — logs the divergences for review.

The `categorie` notably distinguishes `physique` (fixed by measurable reality) from `convention`
(fixed by a usage: symbol, currency, standardized term). The source is **always cited**
in the table (e.g. “Wikidata — capitale P36”, “World Bank SP.POP.TOTL — vintage …”).

**Volatile** values (population, GDP…) are handled honestly: the **most recent** value
is taken (`mrnev=1` on the World Bank side) and its **vintage is traced** in the
source — it is a **dated** snapshot, never served as “live”.

---

## 5. The “go fetch → corroborate → judge → write only the verified” loop

To learn beyond deterministic imports, VERAX has a **disciplined** web access
(`veille.py`) and the promotion loop (`veille_corroboration.py`). It makes
learning **non-ephemeral** without ever relaxing FAUX=0.

Discipline (`veille.py`):

- Any information from the web is a **reported SUPPOSITION**, **never a fact**. It carries
  its **provenance** (URL + domain + content fingerprint) and a low confidence.
- **Sovereign** access: `urllib` only, `http/https` only, bounded size (2 MB), explicit
  UA. Any error (no network, status ≥ 400, empty/oversized response) →
  **HORS**, never a fabricated piece of info (graceful degradation).
- **No fact extraction from free HTML**: it is a hallucination risk
  acknowledged and refused. Reliable facts come from **structured** sources (SPARQL/API), where
  extraction is deterministic. The watch provides the fetching, the “reported” typing,
  the provenance and the corroboration — not the fabrication.

Promotion (`veille_corroboration.corrobore_valeur`) — a reported value becomes a persisted
fact only if **all** the links hold; otherwise we **stop at the first failure**:

1. **OBSERVE** — the value is seen on sources (each observation = domain + url + value).
   It is still only a supposition.
2. **CORROBORATE** — we count the **INDEPENDENT** sources. `independantes()` requires a single
   testimony per **domain** AND **distinct** content fingerprints: *three sources that
   copy each other ≠ corroboration*. At least `minimum` (default: 2) independent domains are needed.
3. **JUDGE** — a **real judge** (`atome.Verdict`, not a bare boolean). The default judge,
   `juge_coherence_store`, confronts the candidate value with the store: it **must not
   contradict** an already-known fact. The caller can inject another judge (physical
   coherence, a test, a falsification…).
4. **PERSIST** — **conflict-refused** write (`ia.ingere_donnees` / `lecteur.ingere_table`
   raises on a divergent value): the **second FAUX=0 guard**, at write time. The provenance
   (sources + judge) is traced in the fact's source.

The result is one of four explicit statuses:

| statut     | signification |
|------------|---------------|
| `PERSISTE` | corroborated + judged + written to the store |
| `SUPPOSE`  | insufficient corroboration or judge → stays a supposition, **nothing is stored** |
| `CONFLIT`  | promoted, but the store held a divergent value → **write refused** |
| `REFUTE`   | the real judge refuted the candidate (anti-re-proposal guard) |

The loop is **injectable** (observations and persistence function): it tests
entirely off-network and without the heavy reader.

---

## 6. The families of ingestion scripts

There are 147 `ingere_*.py` scripts. They all converge on `publie()` (hence the same guards),
but they group into families according to what they allow to be learned:

- **Wikidata at scale (WDQS + QLever).** The core of the volume. `ingere_wikidata.py`
  provides the generic building blocks (`sparql`, `fonctionnel`, `reconcilie`, `publie`,
  snapshots) and covers e.g. FR geography (capital/currency/language), chemical elements,
  highest points. `ingere_qlever.py` goes through the un-rate-limited mirror and adds
  guard-rails (rejection of dates that “leaked” into a place field, rejection of labels = bare
  Q-ID). The big **thematic corridor** scripts (`ingere_t4.py` … `ingere_t12.py`)
  reuse these factories to import, domain by domain, at scale — each scouted
  then re-read, `fonctionnel` rejecting any multi-valued label.
- **Country indicators (World Bank).** `ingere_worldbank.py` — unlocks the
  eco/demo engines (density, GDP per capita, unemployment, inflation, Gini…). A generic
  `ingere_indicateur` function applies the “population” recipe to each indicator, aligning
  the keys onto the **FR name** via the ISO-3 mapping (same keys as `superficie`).
- **Chemistry / periodic table.** `ingere_elements_ptjson.py` (physical properties:
  mass, electronegativity, melting/boiling points, electronic configuration…),
  plus the tables of compounds, ions, chemical families. The join to the French name
  is done **by the symbol** (never a hazardous translation); the predictive values
  of unconfirmed elements are discarded.
- **Language-neutral geography (mledoze).** `ingere_geo.py` — only the safe and the
  neutral (ISO codes, calling code, continent); labels that would be in English in the
  source are **not** loaded, so as not to pollute a French-language base.
- **Language & lexicon (dictionaries).** `ingere_lexique.py` / `ingere_kaikki.py` (FR
  Wiktionary dump: gender, definitions), `ingere_t9_lexemes.py` (Wikidata lexemes),
  affixes, writing systems… Allows answering on grammatical gender, lexical category,
  the meaning of a word — with rejection of inflected forms and words with ambiguous gender.
- **Offline convention tables, stable and certain.** A long series of small
  scripts (sRGB colors, raw formulas, dances → countries, symbols, units, musical
  notes, Greek letters…). No network; uncontested facts; same `publie()`
  pipeline, hence the same functional and anti-conflict guards.

Grouped this way, these families cover the **bounded** (where reality fixes the answer):
geography, chemistry, physics, country economy/demography, biology, language, reference
culture — each traceable back to its source.

---

## 7. Running an ingestion

An ingestion script is a **manual** command. It downloads (or replays the snapshot),
writes the `.jsonl`, and reminds you to validate offline.

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

Each execution displays, per relation, the number of facts written, the rejections for
multi-valuation and the boot conflicts:

```
[capitale                ] écrits= 191  rejets_multi=  3  conflits_amorce=  1  -> _conflits/capitale.jsonl
```

After any ingestion, we **replay the non-regression OFFLINE** to check that nothing has
regressed and that FAUX=0 holds:

```bash
python3 _nonreg.py --full --jobs 6
```

Any conflicts (`datasets/_conflits/<relation>.jsonl`) are reviewed by hand: they
signal a divergence between the source and the canonical boot, and **nothing has been overwritten**
pending arbitration. This is, once again, FAUX=0: we prefer an honest hole to a
doubtful fact.
