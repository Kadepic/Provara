<p align="right"><strong>🇬🇧 English</strong> · <a href="README.fr.md">🇫🇷 Français</a></p>

<div align="center">

# VERAX

### The AI that never makes things up. Either it knows — with proof — or it says so.

**73M facts · loaded in 3.3 s · 520 MB of RAM · 0 GPU · 0 dependencies · Python 3.10+**

</div>

---

VERAX is a **sovereign** artificial intelligence built on a single, non-negotiable rule: **it never asserts anything it cannot prove.** Where a large language model answers with confidence — and is sometimes wrong without knowing it — VERAX answers with its **source**, **computes** exactly, or **honestly abstains**. It never hallucinates.

It runs **without a GPU and without dependencies**, on an ordinary laptop, and **answers offline — no cloud required**. Its full knowledge base — 73 million facts — loads in 3.3 seconds and fits in 520 MB of memory. It is written entirely in the **Python standard library**, without a single third-party package. It goes online only when you let it: to **learn** (ingest new data) or to **search its trusted sources** (opt-in).

## In 30 seconds

```bash
git clone https://github.com/Verax-IA/Verax.git
cd Verax
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

## What makes VERAX different

| | |
|---|---|
| **Zero hallucination (FAUX=0)** | Every assertion comes from a verified fact or an actually-evaluated computation. At the slightest doubt: abstention. This is an invariant enforced by **669 non-regression tests** that fail if a single false fact gets in. |
| **It knows what it doesn't know (bounding)** | VERAX tells apart what reality **settles** (→ a FACT, with a source) from what it **does not** (→ a framed SUPPOSITION, never served as a fact). This calibrated boundary is the heart of the system. |
| **Sovereign, frugal, GPU-free** | 73M facts in 520 MB, 0 dependencies, no GPU, answers with no cloud. Deployable where an LLM is unthinkable: air-gapped machines, embedded, sovereign sectors — at near-zero running cost. Online only on demand, to learn or to search its trusted sources. |
| **Non-ephemeral memory** | It remembers exchanges per conversation and can recall the right item — but what is recalled stays **typed as "reported,"** never promoted to a fact. |
| **It learns by going and fetching** | VERAX does not depend on shipped data: it **ingests by itself** from real sources and verifies every fact before accepting it. See "Watch it learn" below. |

> **Honest about scope** — VERAX **covers fewer topics** than a general-purpose LLM: that is the accepted price of zero-hallucination. Its promise is not "it answers everything," it is "**it is never falsely confident**." On what it covers, it is not wrong; on the rest, it says so.

## Watch it learn

The full knowledge base is **not shipped** in this repository — not by constraint, but by design: VERAX **goes and fetches its data and learns it itself**. Each `ingere_*.py` script pulls a domain from a real, trustworthy source (Wikidata via the QLever mirror, the World Bank, a multilingual dictionary…), **verifies** every fact, and writes only what survives — never an uncorroborated fact.

```bash
python3 ingere_worldbank.py          # fetches economic indicators from the World Bank
python3 ingere_elements_ptjson.py    # ingests the 118 chemical elements
# … then VERAX answers on those domains, offline, with a source
```

> ⚠️ **The ingestion phase needs the network** (it downloads from the sources). This is a **one-time, online build**. Answering from the base then needs no network (searching its trusted sources stays an opt-in, off by default). Rebuilding the entire 73M facts takes several hours; start with a bounded domain (economics, chemistry) to see the learning loop in action.

## Installation & launch

**Requirements** — that's all: **Python 3.10+**, no third-party libraries, no `pip install`, no GPU. (Linux, macOS, or Windows.)

**Windows** — download `VERAX.exe` from the [Releases](https://github.com/Verax-IA/Verax/releases) page and **double-click it**. No Python, no install needed. *(From source instead: double-click `Lancer_VERAX.bat`, which needs Python installed.)*

**Linux / macOS** — from source:

```bash
./install.sh        # checks Python + runs the self-test
python3 lance.py     # or ./lance.sh
```

Either way, VERAX opens at **http://127.0.0.1:8765** — localhost only, your data never leaves the machine.

- **Just the demo** (no server): `python3 demo_verax.py`
- **Full knowledge base**: run the `ingestion/ingere_*.py` scripts once (network required) — see "Watch it learn."

**Project layout** — `src/` the engine and capability modules · `ingestion/` the data fetchers · `tests/` the FAUX=0 validators · `interface/` the local web UI · `docs/` full documentation · `examples/` standalone proofs.

## Verify it yourself (FAUX=0 is not a slogan)

The zero-hallucination discipline is **proven by code**, not asserted. The repository ships hundreds of validators (`valide_*.py`) that test each capability against external anchors; the smallest regression fails the gate:

```bash
python3 verifie_demo.py          # out-of-the-box: 30 engine validators, 773 checks, ~8 s, no data needed
python3 _nonreg.py --jobs 8      # full gate: 669/669 (requires the rebuilt knowledge base)
```

> `verifie_demo.py` runs the computation-engine validators (chemistry, physics, geometry, calibration, the `ia.py` facade…) that need no external data — it proves FAUX=0 on a fresh clone. The full `_nonreg.py` gate additionally validates the ingested facts and requires the rebuilt knowledge base.

## Architecture (overview)

VERAX is an assembly of **atomic modules**, each with its own guarantee and its own validator, with watertight boundaries:

- **The reader** (`lecteur.py`) — the store of verified facts: lookup-or-abstain, compact columnar storage (73M facts in 520 MB).
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
<sub>VERAX — built atom by atom, every brick validated against reality.<br>
"An invention is a supposition that survived reality."</sub>
</div>
