# Validation & FAUX = 0

FAUX = 0 is Provara's founding invariant: the system never asserts something it cannot prove. This invariant is not an intention, it is a property **enforced by the code** — more precisely by a family of validators and by the non-regression gate that runs them. This document describes that mechanism as it actually exists in the repository.

## The non-regression gate (`_nonreg.py`)

`_nonreg.py` is Provara's standard runner: it is the "gate". Its role is to execute the full set of validators and deliver a binary verdict — everything passes, or the gate is red.

It is called like this:

```bash
python3 _nonreg.py --jobs 8      # expected on the full base: 688/688
```

At the end, it prints a summary line and returns an exit code:

```
=== NON-RÉG : 688/688 PASS (... via cache) en Xs ===
```

The return code is `0` if and only if **no** validator has failed; it is `1` as soon as a single one fails (`raise SystemExit(main())`). There is no middle ground: a single false fact entering the system makes a validator fall, and therefore turns the gate red.

### Incremental and parallel, without ever cheating

The gate is designed to be **fast** without ever sacrificing **soundness**. Two mechanisms:

- **Fingerprint cache (build-system style).** A validator is deterministic for a given code. The gate computes the SHA-1 hash of the **contents of the validator's import closure** — itself plus all the project modules it imports, transitively (static AST analysis: `import` / `from … import`). If this fingerprint has not changed since the last memorized PASS, the verdict is replayed from the cache instantly; otherwise, the validator is re-run. Only the validators actually impacted by a modified file re-run.

- **Bounded parallelism.** The validators run in subprocesses, by default 16 in parallel (the README example uses 8), ordered from longest to shortest to minimize the tail. Each validator runs under a memory ceiling (`RLIMIT_AS` 14 GB, `MALLOC_ARENA_MAX=2`) and a deadline (`timeout`). The "heavy" validators — those that load the full reader (tens of millions of facts, ~5 GB peak) — are serialized by an adaptive semaphore (1 to 3 depending on available RAM) to avoid the OOM killer, without changing any result.

The cache is protected against three classic pitfalls, which makes it **sound**:

1. A **FAIL is never memorized**: a validator that fails is systematically retried.
2. An **unresolved dynamic import** (`__import__` with a non-literal argument) marks the validator "always re-run": never a false cache.
3. For **data-driven** validators (those that import `lecteur.py`), the fingerprint also folds in a lightweight signature of the datasets (`datasets/lecteur/*.jsonl`: name, size, `mtime`). Thus, an **ingestion** that touches no `.py` file still invalidates the cache and forces re-validation. Without this, a false fact ingested after the code freeze would go unnoticed behind a stale PASS — that is precisely the soundness hole that this fold-in closes.

## How many validators, and which ones

The gate protects **688 active validators** (`valide_*.py`): this is the reference gate, **688/688**. This number corresponds exactly to the `valide_*.py` files present at the root of the repository (minus `valide_commun.py`, which is a module of shared *helpers* explicitly excluded — it is not a validator), plus the interface validator `interface/valide_interface.py`.

On disk, the **688 `valide_*.py` files** live in the `tests/` folder (there is no separate archive directory).

The selection is **self-discovering**: `liste_validateurs()` maintains a curated list (which fixes the order and flags the heavy tests), then **automatically adds every `valide_*.py`** not yet listed. Direct consequence for FAUX = 0: no real capability can remain "orphaned" outside the net; any newly deposited validator is protected by default.

> **`_nonreg` layout (port, fixed 2026-07-03):** validators live in `tests/` (and `interface/valide_interface.py` in `interface/`), not at the root as in the origin repo. `_nonreg.py` now resolves each validator via `_chemin()` (bare → `tests/…`, explicit path kept as-is), discovers in `tests/`, and sets the pipeline `PYTHONPATH` (`src`+`interface`+`ingestion`) on every subprocess. Verified: `liste_validateurs()` returns **687** (was 1), and `lance()` runs correctly (composition 9/9, ocr 28/28…). Before this fix, `python3 _nonreg.py` found only one validator and failed.

### Conversational suite (`tests/suite_conversation.py`)

The conversational-assistant gates (grammar, conjugation, OCR, **translation**, **composition**, **freshness**, confidence, language, NL-stats, documents, patterns, chat capabilities, plus conversation/assistant_nl) are aggregated by a **dedicated runner** — they need the `PYTHONPATH` `interface`+`src`+`ingestion` that the core gate does not set:

```bash
python3 tests/suite_conversation.py     # expected: 22/22 gates green
```

It runs each gate in an isolated subprocess with the right environment and exits red as soon as one regresses. Run it before any commit touching `interface/` or a conversational building block.

### What these families cover

The validators are not an undifferentiated heap; they group by what they guarantee:

- **Generic core building blocks** (`valide_dimensions`, `valide_grandeur`, `valide_frame`, `valide_causalite`, `valide_contrainte`, `valide_ancres`, `valide_abstention`, `valide_falsification`…): the machine primitives — typed quantities, dimensional algebra, causal graphs, constraint solver, non-circular anchor bank, abstention policy. They guarantee that the reasoning itself refuses in the face of doubt.
- **Per-domain computation engines**: chemistry, physics, modular arithmetic, navigation, conjugation, stoichiometry, relativity, applied cryptography, etc. These validators verify that the result is **exactly** the one expected and that any out-of-domain input returns an abstention (not a plausible number).
- **The fact store** (`valide_lecteur` and its variants `t4`…`t12`): the capabilities driven by ingested data (geography, living world, people, works, sport, language…), with the *lookup-or-abstention* contract.
- **Memory and restitution** (`valide_memoire`, `valide_restitution`, `valide_conversation`): what is recalled stays typed as "reported", never promoted to fact.
- **Uncertainty calibration** (the most numerous family: `valide_calibration`, `valide_conformal…`, plus a large collection of statistical paradoxes and traps — Simpson, Berkson, Stein, Ellsberg, Goodhart…). In an open domain, these validators verify that the system **quantifies what it does not know** and unmasks any over-confidence, rather than bluffing.
- **Ingestion and invention** (`valide_veille_corroboration`, `valide_boucle_invention`, `valide_invention_gap`…): corroboration before writing, and the exploration of framed suppositions.

## The principle: building block → validator with external anchors → green gate

Provara is built atom by atom. The working rule is simple and non-negotiable:

> **a building block is only acquired once its validator passes, and work only advances with a green gate.**

Concretely, each module `X.py` has its validator `valide_X.py`, and this validator follows a constant pattern:

1. It **imports the real module** it tests (`import chimie as K`, `import physique as P`, `from ancres import …`).
2. It checks **exactness** against **non-circular external anchors** — reference values known independently, **never recomputed by the tested expression itself**. Without this non-circularity, "it works" would only test the code against itself.
3. It tests **soundness in adversarial mode**: a large battery of unknown, malformed or out-of-domain inputs, which must **all** return the abstention (`HORS`), never a false one.
4. It ends with a canonical line `=== valide_X : N/N ===` and exits with code `0` if everything passes, `1` otherwise (`sys.exit`, `raise SystemExit`, or `assert ok == total`).

The requirement of **external anchors** is the heart of anti-circularity. A few real examples:

- `valide_chimie` compares the computed molar masses to a table of references (`O2` = 31.998, `KMnO4` = 158.032…), to within 0.05 g/mol — table values, not engine outputs. The test cases deliberately do not appear in the module's `__main__`.

  ```python
  # valide_chimie.py — external anchor, table tolerance
  st, m = K.masse_molaire("KMnO4")
  check(st == K.VERIFIE and abs(m - 158.032) < 0.05, "masse KMnO4")
  # adversarial soundness: unknown element -> HORS, never an invented mass
  check(K.masse_molaire("Xx2")[0] == K.HORS, "élément inconnu -> HORS")
  ```

- `valide_physique` anchors its formulas on **known physical values** (Earth surface gravity ≈ 9.81 m/s², escape velocity ≈ 11.19 km/s, orbital period of 1 AU ≈ 1 year, pH of neutral water = 7), and not on a re-evaluation of the same expression. It also checks that any invalid domain (negative mass, `Th < Tc`, `[H+] = 0`) returns `HORS`.

- `valide_ancres` verifies that the anchor bank requires an **independent source**: an answer coming from the **same** source as the anchor is refused as `CIRCULAIRE`, and a false answer is `CONTREDIT`.

- `valide_lecteur` samples externally verified values (iron Z = 26, gold Z = 79, uranium Z = 92, February = 28 days) and checks a sequential consistency (Z = 1…36) to catch any transcription error in the seed, then submits a large battery of unknowns that must all return `(HORS, None)`.

## Why this guarantees FAUX = 0

The chain of guarantees closes as follows:

- **Every capability is under the net.** Auto-discovery includes every `valide_*.py` at the root; nothing real stays outside the gate.
- **Each validator tests against reality, not against itself.** Non-circular external anchors detect both a false formula and a data-entry error in a seed table.
- **Abstention is verified as much as exactness.** The "adversarial soundness" strand requires that the unknown, the malformed and the out-of-domain return `HORS` — this is what prevents a plausible but false answer.
- **Data changes cannot slip behind a stale cache**, thanks to the fingerprint of the `datasets/lecteur/*.jsonl` folded into the fingerprint of the data-driven validators.
- **A failure is never absorbed.** A FAIL is not cached, the gate returns a non-zero exit code, and the "green gate before moving on" rule forbids advancing as long as a single false fact remains.

A false fact therefore cannot enter Provara without making at least one validator fail, which turns the gate red and blocks the work. It is in this precise sense that **FAUX = 0** is proven by the code, and not merely asserted.
