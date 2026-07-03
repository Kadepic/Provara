# VERAX Architecture

> Founding rule, engraved in every layer: **FAUX = 0**. VERAX answers only
> when a real judge (a verified lookup, an actually evaluated computation, a
> sourced reference) has ruled. Everywhere else, it *frames* (assumption), *asks*
> (clarification), or *abstains* (HORS). It never asserts at random.

This document describes the architecture **as it exists in the code**
(`ia.py`, `lecteur.py`, `base_faits.py`, `classifieur_bornage.py`,
`assistant_nl.py`). It describes no capability that is not there.

---

## 1. Guiding principle: atomic modules with watertight boundaries

VERAX is not a monolithic model: it is an **assembly of atomic
modules**, each responsible for a single kind of truth and each accompanied by
its own validator.

The entry point `ia.py` states it itself: *"This façade adds no truth
logic — it ORCHESTRATES."* The façade merely routes to already-validated
bricks; its docstring cites for example `classifieur 26/26`,
`invention_gap 12/12`, `chercheur 11/11`, `bibliothèque 11/11`,
`auto_optimise 12/12`.

Three properties follow from this decomposition:

- **Watertight boundary**: each module has a clear contract (inputs, outputs,
  status). One module never overwrites the truth of another. Concrete example in
  `lecteur.py`: ingesting a *divergent* value for an already-present key raises
  `ValueError` — refusal, not silent overwrite.
- **Abstention by default**: without proof, a brick returns `HORS` / `None` /
  `ABSTENTION` rather than a guess. A routing error therefore degrades at
  worst the *framing*, never the *truthfulness*.
- **Dedicated validator**: each brick has its own non-regression harness. The
  soundness is verified module by module, not globally assumed.

This is what makes the FAUX=0 slogan structural rather than declarative: there is
not a single place to "be careful", there are boundaries that refuse
to invent.

---

## 2. The layers

### 2.1 The fact store (`base_faits.py` + `lecteur.py`)

This is the foundation: *"we answer ONLY if the fact is present and verified;
otherwise an honest HORS. Never a probabilistic derivation, never a guess."*

**`base_faits.py` — the hand-verified seed.**
Each fact is an immutable record `Fait(valeur, categorie, source)`:

- `categorie` carries the *nature* of the constraint: `CAT_PHYSIQUE` (observed,
  revisable models), `CAT_PASSE` (frozen, irreversible), `CAT_CONVENTION` (fixed
  by agreement: language, units, standards);
- `source` carries the *traceability* (what anchors the truth).

The lookup is exact, on a key normalized by `normalise()` (lowercase, without
accents, without punctuation, whitespace compacted):

```python
cherche(relation, entite)   # -> Fait, ou None (jamais un faux)
repond_nl(question)         # extrait (relation, entite) de quelques gabarits sûrs
```

It is a *deliberately small but 100% verified* seed. What matters is
the mechanism (judged lookup + HORS), not the volume.

**`lecteur.py` — the generic reader of bounded DATA.**
Same sound contract, generalized to entire tables. The docstring explains it:
for a past fact, a convention, or a measured constant, *reality fixes the
answer but the AI cannot DEDUCE it — guessing it would be hallucinating*. The
self-buildable brick is therefore the *reader of a reference*, never the
content.

- `ingere_table(relation, lignes, categorie, source)`: generic ingestion
  of an `entity -> value` table. A divergent value on an existing key ->
  `ValueError` (inconsistent authoritative source, no overwrite). Re-ingesting
  the same value is idempotent; an empty key/value is ignored.
- `cherche` / `repond(relation, entite)`: exact lookup over the ingested
  tables, **fallback** to the frozen seed `base_faits` (complementary corpora,
  distinct relations).
- `repond_nl(question)`: a few NL templates for the ingested tables, full
  fallback to `base_faits.repond_nl` — never a coverage regression,
  never an invention.

The soundness contract is structural: present + verified -> complete `Fait`
(value + category + source); absent or off-template -> `(HORS, None)`.

**Storage.** The reader loads frozen, compact tables into memory. A
frozen mono-source table is represented in columns (`_ColTable`): sorted keys
de-objectified into a single `str` blob + an `array` of offsets (`_Cles`), integer
codes for values, category/source stored once per table, `Fait`
reconstructed on the fly and shared by distinct value. An *mmapped* `.colf`
backend (`_ColTableMmap`) enables shared/reclaimable RAM and a near-free
load. The answers stay identical; only the memory cost drops.

### 2.2 The bounding guardian (`classifieur_bornage.py`)

This is the anti-hallucination **status router**. It never produces an
answer — it decides *which regime of the atom contract* applies, hence whether
reality is allowed to rule.

It crosses **two axes**:

- **ontological**: does reality fix the answer, independently of who
  asks the question? -> `BORNE` / `NON_BORNE` / `INDECIDABLE`;
- **access**: can a real judge rule *now*? ->
  `JUGE_DISPO` / `PAS_DE_JUGE`.

The crossing produces the regime:

| Ontologie × Accès          | Régime                       | Signification                              |
|----------------------------|------------------------------|--------------------------------------------|
| BORNÉ + JUGE_DISPO         | `R_FAIT`                     | reality rules — **the only path that asserts** |
| BORNÉ + PAS_DE_JUGE        | `R_SUPPOSITION_A_CHERCHER`   | a truth exists, unverified -> to be searched |
| NON_BORNÉ                  | `R_SUPPOSITION_OPINION`      | calibrated judgment, no truth to rule on |
| INDÉCIDABLE                | non-borné conservateur       | when in doubt about the *status*, never bounded     |

Design points that guarantee FAUX=0:

- **`JUGE_DISPO` is never inferred from a lexical marker.** The only *internal*
  judge is arithmetic (`_juge_arith`): it actually evaluates an
  expression via a safe AST, and only if the expression **covers the whole**
  question (no orphan number, no operation spelled out in words). The verb
  "compute" alone, or a "1990-2000" range, does not grant the judge.
- **Conservative bias.** A hard non-bounded predicate (taste, aesthetics,
  moral prescription, future prediction, fiction, requested opinion) *preempts*
  the judge: an opinion never becomes a fact because of a number it
  might contain. A *future* year is classified non-bounded (the future is not a
  fact), but a past year remains a datable fact.
- An external `juge_verdict` (the result of a real judge already run by the
  caller) can be supplied and **takes precedence**: a question ruled by
  reality is bounded-accessible, even if its wording contains an ambiguous marker.

`Classement.route_fait()` returns `True` **only** if `BORNE` and
`JUGE_DISPO`. A misclassification therefore degrades the framing (searching vs
opinion), never the truthfulness.

### 2.3 The conversational gate (`assistant_nl.py`)

This is the **wrapper that speaks a single language** on output. It *adds no
knowledge layer*: it reuses the existing conversational pipeline
(`interface/repond.py`: politeness, meta, verified factual cascade, dialogue
memory, did-you-mean) and complements it with three capabilities.

Every answer comes out in a uniform envelope:

```python
@dataclass(frozen=True)
class Reponse:
    statut: str      # fait | supposition | clarification | echange | hors
    texte: str
    regime: str      # régime d'atome décidé par le gardien de bornage
    source: str      # provenance quand FAIT
    attente: str     # ce que le tour suivant doit préciser (clarification)
```

The three added capabilities:

1. **Bounding-based routing after HORS.** When the factual cascade finds
   nothing, `classifieur_bornage` is consulted: FAIT regime (a covering
   computation actually evaluated) -> we answer; NON-BOUNDED -> honest
   framing; BOUNDED without a judge -> autonomous search over trusted sources
   (`veille.py`, opt-in `IA_WEB=1`); INDÉCIDABLE -> a clarification question.
2. **Stateful clarification.** A clarification question ("did you
   mean X?") remains *pending* per conversation. If the following turn
   *confirms* it, the original question is rewritten with the confirmed
   correction then reprocessed. Never a silent substitution; an anti-loop limits
   consecutive "indécidable" clarifications.
3. **Uniform envelope** via the single gate `ia.assistant(question)`.

The envelope classification is **positive**: each terminal non-factual text
is recognized by its constant/its prefix (`qualifie_texte`). There is
never a "fact" default for an unidentified text. Dialogue recall is
typed *reported assumption* (the user said it — true; the content is not
verified); the web stays *reported assumption* as long as it is not corroborated.

The module is *import-light* (OOM-safe): at top level, only the stdlib +
`base_faits` + `classifieur_bornage`. The full pipeline, `veille` and
`conversation` are imported lazily.

### 2.4 The computation engines (`ia.py` façade)

Beyond lookup, VERAX exposes **deterministic engines** whose every answer
is re-verifiable. The `ia.py` façade groups them by families; the common idea
is *exact computation or abstention*, never an approximation served as a fact.

- **Bounded sciences.** `ia.chimie("H2O")` (molar mass…), `ia.physique(...)`
  (SI quantities transcribed from CODATA), `ia.genetique(seq)`, and a judge of
  **physical coherence** — `ia.juge_dispositif(spec)` rules on the *impossibility*
  of a device vs conservation/entropy principles (VIOLE /
  COHERENT_BORNE / HORS). Coherence is never a proof of efficacy:
  the asymmetry is explicit.
- **Conventions & references.** `ia.reference(v, quoi="morse"|"nato"|...)`,
  `ia.donnee(relation, entite)` and its NL variant `ia.donnee_nl(question)`
  (DATA reader: lookup-or-HORS + seed fallback).
- **Derived geography.** From ingested coordinates: `ia.coordonnees_lieu`,
  `ia.distance_lieux` (great-circle, spherical model — a *derived* fact of
  explicit scope, not a stored datum), `ia.cap_lieux`, cartographic conversions.
  Country indicators (World Bank, dated snapshots) and derivatives
  (`densite_pays`, `pib_par_habitant_calcule`) return `None` (HORS) if a
  pivot is missing.
- **Graph & ontology of the world.** `ia.voisins(entite)` / `ia.chemin(a, b)`
  (edges = real re-verifiable facts), `ia.est_un(x, type_)` (transitive
  subsumption in an open world: `False` = "not derivable from the present facts",
  never "false").
- **Modalities & file production.** Geometry, SVG drawing, raster/PNG image,
  WAV audio, XLSX spreadsheet, PDF, charts: each encoder produces
  valid, deterministic bytes, re-decodable identically. The core is bounded
  (exact geometry/bytes); aesthetics remain unjudged.
- **Structured reasoning & discovery.** `ia.demande(...)` (routing by
  nature of reality toward the executor, the rules engine, or the code audit),
  `ia.invente(...)` (rules on a target function vs the existing one:
  EXISTE_DEJA / INVENTION / AMBIGU / BRIQUE_MANQUANTE / INCOHERENT),
  `ia.decouvre_loi(data)` (symbolic law, exact-fit-or-abstention, held-out
  mandatory), divergent invention (`apprend_loi`, `leve_contrainte`,
  `transfere_analogie`, `arbitre_compromis`, `explique_observations`,
  `plan_procede`) and invention on the real (`attribut_derivable`,
  `inventions_composites`). All these bricks *abstain without proof*.

### 2.5 Ingestion (`ingere_*` scripts -> `datasets/*.jsonl` -> reader)

The ingestion architecture strictly separates *online* from *offline*:

- the `ingere_*.py` scripts (online) fetch real sources and write
  `*.jsonl` files;
- the reader loads these files **offline** via `charge_dossier()`: each
  file is *self-describing* — its first non-empty line is a header
  `{_relation, _categorie, _source, _articles?}`, the following ones are facts
  `{entite, valeur}`. `charge_dossier` makes **no network access** (the network
  lives in the `ingere_*` scripts).

Every line goes through the same guardrails as `ingere_table`: divergent
conflict refused, idempotence, empty key/value ignored. The load freezes the
mono-source tables into columns (and can warm an mmappable `.colf` binary cache) to
reduce the memory peak, without changing the answers.

### 2.6 Calibration (families of non-bounded modules, `ia.py` façade)

The non-bounded is not truth: it is opinion that must stay
*honest about its uncertainty*. VERAX exposes a large family of statistical
bricks, all accessible behind uniform `ia.*` wrappers (often
a `phrase=` parameter for a natural-language output). Grouped by what they
allow you to DO:

- **Instrument confidence**: calibration (ECE/Brier), proper scores
  (log-loss, CRPS), calibration tests, calibration-drift detection.
- **Frame with guaranteed intervals**: conformal methods (adaptive,
  normalized/Mondrian, quantile, jackknife+, weighted for covariate shift),
  tolerance intervals, CDF bands.
- **Combine and decide**: Bayesian combination of evidence (including
  correlated), aggregation of expert opinions, expected-utility decision,
  bandits, risk control (FNR/FDR).
- **Model under thick uncertainty**: Dempster-Shafer, interval
  arithmetic, p-box, imprecise/robust models, decision under ambiguity.
- **Order of magnitude & biased populations**: Fermi, weighted sample,
  meta-analysis, Poisson rate, extreme values, survival, missing data.

Calibration's role in the FAUX=0 invariant is clear: these outputs are
never served as *facts*. They carry their status of calibrated
assumption — honesty about uncertainty, not a claim to truth.

---

## 3. A question's journey: from natural language to a typed verdict

A question arrives in natural language. It crosses the layers down to a
**typed verdict**: fact, assumption, clarification, exchange, or abstention.

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

Reading the diagram:

1. The **conversational gate** first tries the verified pipeline. A fact
   present in the **store** (base_faits/lecteur) comes out as a `FAIT` with its
   provenance. A social/meta interaction comes out as an `ECHANGE`.
2. If nothing is found (`HORS`), the **bounding guardian** classifies the question.
3. Depending on the regime:
   - `R_FAIT` via the internal arithmetic judge (and only if it *covers the
     whole* question) -> `FAIT`, source "calcul arithmétique (AST évalué,
     couvrant)";
   - `NON_BORNE` -> `SUPPOSITION` (honest framing: "reality does not fix a
     single answer, so I will not assert a fact here");
   - `BORNE` without a judge -> autonomous search over trusted sources;
     result *reported* (SUPPOSITION) or an honest `HORS` + provenance;
   - `INDECIDABLE` -> `CLARIFICATION`: we ask the question, we never guess.

At no point does a path fabricate a fact: the only outgoing assertions
come from the verified pipeline, from the fact store, or from a computation actually
evaluated and covering.

---

## 4. Where the FAUX=0 invariant lives

The invariant is not a central check; it is distributed across the boundaries:

- **`base_faits` / `lecteur`**: exact lookup or `(HORS, None)`; ingestion
  conflict refused (`ValueError`).
- **`classifieur_bornage`**: sound by construction — it *routes*, produces
  no assertion; the only path that asserts requires a real judge;
  conservative bias when in doubt.
- **`assistant_nl`**: positive envelope classification (never a "fact"
  default); web and dialogue memory typed *reported assumption*.
- **Computation engines**: exact-fit-or-abstention, held-out, re-decodable
  encodings; efficacy/aesthetics explicitly *unjudged*.
- **Calibration**: outputs carried as calibrated assumptions, never as
  facts.

It is the sum of these local refusals — and not a global guarantee posted after
the fact — that upholds the promise: *at the slightest doubt, frame, ask, or
abstain; never assert a falsehood.*
