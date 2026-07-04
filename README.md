<p align="right"><strong>🇬🇧 English</strong> · <a href="README.fr.md">🇫🇷 Français</a></p>

<div align="center">

# Provara

### The AI that never makes things up. Either it knows — with proof — or it says so.

**~1.1M facts bundled · full base 72M via one download · 0 GPU · 0 dependencies · Python 3.10+**

</div>

---

Provara is a **sovereign** artificial intelligence built on a single, non-negotiable rule: **it never asserts anything it cannot prove.** Where a large language model answers with confidence — and is sometimes wrong without knowing it — Provara answers with its **source**, **computes** exactly, or **honestly abstains**. It never hallucinates.

It runs **without a GPU and without dependencies**, on an ordinary laptop, and **answers offline — no cloud required**. Its full knowledge base — nearly 72 million facts — loads in about 2 seconds and runs in ~30 MB of memory (the corpus is memory-mapped: pages become resident only on demand). It is written entirely in the **Python standard library**, without a single third-party package. It goes online only when you let it: to **learn** (ingest new data) or to **search its trusted sources** (opt-in).

## In 30 seconds

```bash
git clone https://github.com/Provara-IA/Provara.git
cd Provara
python3 demo_verax.py        # no install, no network, no GPU
```

The demo runs on the bundled **sample** (16 fact domains) plus the computation engines, which need no data at all. A glimpse of what it shows:

```
"What is the capital of Japan?"          ✔ FACT           Tokyo
"What is the atomic number of iron?"     ✔ FACT           26
  molar mass of glucose C₆H₁₂O₆         = 180.156   (engine, zero data)
  distance Tokyo → Paris (great circle) = 9712 km   (computed)

"Population of the city of Wakanda?"      ∅ ABSTAINS       "I abstain rather than guess"
"What is the most beautiful country?"     ≈ SUPPOSITION    "reality does not fix a single answer"
```

## What makes Provara different

| | |
|---|---|
| **Zero hallucination (FAUX=0)** | Every assertion comes from a verified fact or an actually-evaluated computation. At the slightest doubt: abstention. This is an invariant enforced by **683 non-regression tests** that fail if a single false fact gets in. |
| **It knows what it doesn't know (bounding)** | Provara tells apart what reality **settles** (→ a FACT, with a source) from what it **does not** (→ a framed SUPPOSITION, never served as a fact). This calibrated boundary is the heart of the system. |
| **Sovereign, frugal, GPU-free** | the full ~72M-fact base runs in ~30 MB of RAM (columnar, memory-mapped, demand-paged; ~1.7 GB on disk), 0 dependencies, no GPU, answers with no cloud. Deployable where an LLM is unthinkable: air-gapped machines, embedded, sovereign sectors — at near-zero running cost. Online only on demand, to learn or to search its trusted sources. |
| **Non-ephemeral memory** | It remembers exchanges per conversation and can recall the right item — but what is recalled stays **typed as "reported,"** never promoted to a fact. |
| **It learns by going and fetching** | Provara does not depend on shipped data: it **ingests by itself** from real sources and verifies every fact before accepting it. See "Watch it learn" below. |

> **Honest about scope** — Provara **covers fewer topics** than a general-purpose LLM: that is the accepted price of zero-hallucination. Its promise is not "it answers everything," it is "**it is never falsely confident**." On what it covers, it is not wrong; on the rest, it says so.

## In conversation

Provara is not just a fact store: it is a full local assistant that never lies.

- **It reasons — it doesn't just look up** — "is a cat a mammal?" → *Yes — cat → mammal*; "what continent is Abuja on?" → *Africa* (**derived**: Abuja is the capital of Nigeria, which is in Africa); "is Phobos part of the solar system?" → the machine **discovers** that "orbits" is transitive (and rejects symmetry), then **applies it with proof**; "Paris is to France as Berlin is to…?" → *Germany* (**analogy**: it recovers the relation and transfers it). A non-stored fact becomes known — and proven.
- **It counts, ranks, filters and compares — exactly** — "how many countries in Africa?" → an **exact** count; "the 5 most populous countries in Africa" → an exact ranking with the values; "which African countries have more than 100 million people?" → an **exhaustive filter**; "is China more populous than India?" → a numeric **comparison**; "total population of Africa?" → an exact **aggregation** (sum, mean, median); "which came first, the battle of Marignan or Verdun?" → *Marignan (1515)*, a **date** comparison. Where an LLM enumerates from memory (and errs), Provara **scans the whole base**.
- **It defines and develops** — "what is malaria?" → the verified definition; "tell me about Nigeria" → a **developed profile** (capital, population with the **computed rank** "most populous in Africa", currency).
- **It understands you despite typos and slang** — "commen vas-tu" → understood (spelling + **phonetic** correction); French slang → mapped to the standard term (**paraphrase**, JeuxDeMots network).
- **It says who created it** — "who created you?" → Yohan Fauck, with his links.
- **It searches the web when it doesn't know** (opt-in) — first a reliable structured source (Wikidata) for a **verified fact**; otherwise an **attributed** Wikipedia extract with the **link** ("according to Wikipedia…, verify if needed"). Never presented as its own truth. *("the king of pop" → Michael Jackson; "who invented dynamite?" → Alfred Nobel, 1866.)*
- **It draws what it knows** — "show me what you know about France" → a **diagram** (graph) of its real relations.
- **It reads your files** — a file (JSON, CSV, XML, SQLite, ZIP…) → a faithful summary, **read locally**, never sent anywhere.
- **It answers several questions at once** — "capital of Japan, 5×9, and who invented dynamite?" without blocking.
- **It remembers** — per-conversation memory, recalls the right item, always typed as "reported."
- **It greets you** — introduce yourself ("my name is Yohan") and it answers socially, by name — it never searches the web for your name.

## Watch it learn

The full knowledge base is **not shipped** in this repository — not by constraint, but by design: Provara **goes and fetches its data and learns it itself**. Each `ingere_*.py` script pulls a domain from a real, trustworthy source (Wikidata via the QLever mirror, the World Bank, a multilingual dictionary…), **verifies** every fact, and writes only what survives — never an uncorroborated fact.

```bash
python3 ingestion/ingere_worldbank.py          # fetches economic indicators from the World Bank
python3 ingestion/ingere_elements_ptjson.py    # ingests the 118 chemical elements
# … then Provara answers on those domains, offline, with a source
```

> ⚠️ **The ingestion phase needs the network** (it downloads from the sources). This is a **one-time, online build**. Answering from the base then needs no network (searching its trusted sources stays an opt-in, off by default). Rebuilding the entire 72M facts takes several hours; start with a bounded domain (economics, chemistry) to see the learning loop in action.

## Installation & launch

**Requirements** — that's all: **Python 3.10+**, no third-party libraries, no `pip install`, no GPU. (Linux, macOS, or Windows.)

**Windows** — download `Provara.exe` from the [Releases](https://github.com/Provara-IA/Provara/releases) page and **double-click it**. No Python, no install needed. It opens in your browser and works **immediately** on a bundled **sample** (~1M facts) — no waiting. To unlock the **full 72M-fact base**, click **“Base complète”** in the interface: a **one-time** download (about **6 GB of free disk space**, **15–20 minutes**) that you can also skip. A loading dialog keeps you informed throughout; the app runs **windowed** (no console window) and has a **Quit** button. *(From source instead: double-click `Lancer_Provara.bat`, which needs Python installed.)*

**Linux / macOS** — from source:

```bash
./install.sh        # checks Python + runs the self-test
python3 lance.py     # or ./lance.sh
```

Either way, Provara opens at **http://127.0.0.1:8765** — localhost only, your data never leaves the machine.

- **Just the demo** (no server): `python3 demo_verax.py`
- **Full knowledge base**: run the `ingestion/ingere_*.py` scripts once (network required) — see "Watch it learn."

**Project layout** — `src/` the engine and capability modules · `ingestion/` the data fetchers · `tests/` the FAUX=0 validators · `interface/` the local web UI · `docs/` full documentation · `examples/` standalone proofs.

## Verify it yourself (FAUX=0 is not a slogan)

The zero-hallucination discipline is **proven by code**, not asserted. The repository ships hundreds of validators (`valide_*.py`) that test each capability against external anchors; the smallest regression fails the gate:

```bash
python3 verifie_demo.py          # out-of-the-box: 31 engine validators, 783 checks, no data needed
python3 _nonreg.py --jobs 8      # full gate: 683/683 (requires the rebuilt knowledge base)
```

> `verifie_demo.py` runs the computation-engine validators (chemistry, physics, geometry, calibration, the `ia.py` facade…) that need no external data — it proves FAUX=0 on a fresh clone. The full `_nonreg.py` gate additionally validates the ingested facts and requires the rebuilt knowledge base.

## Architecture (overview)

Provara is an assembly of **atomic modules**, each with its own guarantee and its own validator, with watertight boundaries:

- **The reader** (`lecteur.py`) — the store of verified facts: lookup-or-abstain, compact columnar storage, memory-mapped and demand-paged (labels included): the ~72M-fact base runs in ~30 MB of RAM (~1.7 GB on disk); pages become resident only when a query touches them, and `libere_cache()` releases them again.
- **The bounding guard** (`classifieur_bornage.py`) — routes every question: bounded → fact / unbounded → framed supposition / undecidable → clarifying question.
- **The conversational door** (`assistant_nl.py`) — understands natural language, answers from the verified, computes, or asks a question; never guesses.
- **The computation engines** — chemistry, physics (CODATA constants), navigation (great-circle), arithmetic, conjugation, conversions… : exact, with no data at all.
- **Ingestion** (`ingere_*.py` + `veille_corroboration.py`) — fetches from real sources, corroborates, writes only the verified.
- **Uncertainty calibration** — in open domains, quantifies what it does not know rather than bluffing.
- **Fast interactive path** (`lecteur_daemon.py` + `lecteur_client.py`) — an optional resident daemon serves the reader over a local socket, so the interactive UI answers in milliseconds without reloading the base. Opt-in: when it is off, behavior is identical (zero regression).

See [`examples/`](examples/) for standalone proofs (language-agnostic reasoning, a polyglot judge across programming languages).

📖 *Full documentation of every subsystem: see [`docs/`](docs/).*

## License

Code under the **MIT** license (see [`LICENSE`](LICENSE)). Ingested facts come from open sources (Wikidata is CC0; check the terms of each source before redistributing datasets).

---

<div align="center">
<sub>Provara — built atom by atom, every brick validated against reality.<br>
"An invention is a supposition that survived reality."</sub>
</div>
