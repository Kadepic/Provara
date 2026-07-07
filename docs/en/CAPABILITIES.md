# Provara — Capability catalogue

> Thematic overview of Provara's capabilities, **drawn from the code's docstrings** (nothing invented).
> For the exhaustive, module-by-module list, see [`INVENTORY.md`](INVENTORY.md).

## Geography & cartography

This family of capabilities makes it possible to **compute, on exact foundations, the quantities of geography and the Earth sciences**: reading and converting a map, positioning oneself and measuring distances on the globe, quantifying the flows and cycles of the Earth's surface, soil mechanics, settlement indicators, and ingesting real geographic/astronomical facts. In every case the mechanism employed is a **definitional identity or an established theorem**, never a correlation or a guessed value: the answer is entirely determined by the observed inputs, and the module abstains (error) rather than returning an absurd number.

### Cartography & geomatics

The `cartographie` module covers the exact computations tied to a map, based on established conventions (scale 1:N, 1 inch = 2,54 cm exactly, 1° = 60′ = 3600″):

- **Scale**: map ↔ ground conversion (`echelle_distance_reelle`, `distance_carte`) following *real distance = map distance × N*.
- **Ground resolution** of a digitized map (`resolution_au_sol`, `resolution_au_sol_depuis_dpi`), including from a scan in `dpi`.
- **Coordinates**: sexagesimal (DMS) → decimal (DD) conversion, and length-unit conversions (`cm_en_m`, `cm_en_km`).

```python
cartographie.conversion_dms_dd(48, 51, 12)   # 48°51'12" -> 48.8533... °
```

The module refuses a scale ≤ 0, minutes/seconds outside [0, 60) or non-integer degrees in DMS (never a quietly "corrected" coordinate).

### Navigation & geometry of the globe

Two modules handle positioning and measurement on a sphere.

- `navigation` computes the **orthodromic distance** (great circle) via the haversine formula (Earth radius R = 6371 km) and the **initial bearing** (departure azimuth). Pure functions, output to 6 significant figures; documented anchor of the validator: Paris→London ≈ 344 km.

  ```python
  navigation.distance_orthodromique(lat1, lon1, lat2, lon2)  # km, grand cercle
  navigation.cap_initial(lat1, lon1, lat2, lon2)             # azimut vrai dans [0, 360[
  ```

- `geometries_non_euclidiennes` provides **spherical geometry** (constant positive curvature): Gaussian curvature K = 1/R², spherical excess, angle sum and area of a geodesic triangle (Girard's theorem, A = R²·(Σ angles − π)).

  ```python
  geometries_non_euclidiennes.courbure_gauss_sphere(R)   # K = 1/R²
  ```

Invalid inputs (latitude outside [−90, 90], longitude outside [−180, 180], radius ≤ 0, angle outside ]0, π[) raise an error: structural abstention, never a false positive.

### Earth sciences & environmental physics

Three modules quantify surface and subsurface processes through established formulas (output to 6 significant figures, abstention on invalid domain).

- `hydrologie` — continental waters: discharge by continuity (Q = A·v), rational method, Manning flow velocity, Kirpich time of concentration.

  ```python
  hydrologie.debit(section_A, vitesse_v)   # Q = A · v (m³/s)
  ```

- `cycles_biogeochimiques` — reservoir balances: residence time τ = M/Φ, steady-state balance (input = output), and a **sourced** catalogue of the 4 major cycles (carbon, nitrogen, water, phosphorus). Outside these known cycles, the module abstains.

- `geotechnique` — soil mechanics: vertical stress (σ = γ·z), Terzaghi effective stress (σ' = σ − u), Rankine active earth-pressure coefficient (Ka = tan²(45° − φ/2)) and thrust on a wall.

  ```python
  geotechnique.coefficient_poussee_active(30)   # Rankine, φ=30° -> Ka = 1/3
  ```

### Human geography (settlement)

The `demographie` module implements the **standard demographic definitions** (INED / UN) without ever hard-coding a country value: rate of natural increase, population density, doubling time (rule of 70), dependency ratio, total fertility rate. The result is a function solely of the counts and indices provided.

```python
demographie.densite_population(1_000_000, 500)   # -> 2000 hab/km²
```

### Ingestion of real geographic facts

The `_ingere_astre_relief_t1` script feeds the base from real sources: it links each surface landform (crater, mount, sea, vallis…) to the **real celestial body** on which it lies (Wikidata P376). The FAUX=0 guarantee is explicit here: a *closed-set* of the real bodies of the solar system rules out any fictional contamination (Krypton, Naboo, Coruscant…), the relation is treated as functional (a landform associated with several distinct bodies → discarded), and ground-truth anchors (tycho → Moon, olympus mons → Mars) are checked.

### Common guarantee

All these modules share the **FAUX=0** posture: the mechanism is a definitional identity or an exact theorem, the only data used are conventions or certain sourced facts, the output is rounded to an honest precision (6 or 10 significant figures) and — the decisive invariant — a false positive is forbidden. Faced with an out-of-domain input or an unknown case, the module **abstains** by raising an error rather than inventing a value.

---

## Economy & demography

This family of capabilities brings together two complementary things: on the one hand the **exact computation of economic indicators and population dynamics** (labour market, business cycle, trophic chains, prey/predator dynamics), and on the other hand the **statistical tooling required to draw sound conclusions from a sample** (correction of sampling biases, calibrated estimation, decision under uncertainty). The guiding thread is the same everywhere: the modules never invent a country-value or an economic-conditions datum; they only implement the *mechanism* (the accounting identity, the formula, the established rule) and **abstain** (raising an error or returning an abstention verdict) as soon as the input falls outside their domain of validity.

### Applied economics: labour and economic conditions

**`chomage`** applies the ILO normative definitions (adopted by Eurostat / INSEE / ILO). Each indicator is an exact arithmetic ratio between observed head-counts of people: `population_active` (accounting identity: employed + unemployed), `taux_chomage` (unemployed relative to the labour force, not to the total population), `taux_activite` and `taux_emploi` (relative to the working-age population). Abstention is structural: a zero labour force, a negative head-count, or a rate that is mathematically > 100 % (e.g. more unemployed than economically active people) raises an error instead of producing a false figure.

```python
chomage.taux_chomage(2_500_000, 25_000_000)   # → 10.0  (en %)
```

**`cycles_economiques`** restores the *established* structure of the business cycle (macroeconomic consensus, NBER, Conference Board), without ever dating or quantifying an economic situation. It exposes the four canonical phases (expansion → peak → recession → trough/depression) and their sequence, the technical rule for a recession (two consecutive quarters of decline in real GDP, explicitly distinguished from the official multi-criteria dating), and the classification of economic indicators (leading / coincident / lagging). Any label outside the catalogue or ambiguous triggers abstention.

```python
cycles_economiques.phase_suivante("expansion")                 # → "sommet/pic"
cycles_economiques.est_recession_technique([-0.2, -0.4, 0.1])  # → True
```

### Population dynamics and ecosystems

**`ecologie`** handles non-human populations through exact ecological laws. Two mechanisms: trophic energy transfer (Lindeman's 10 % rule, `energie_niveau` / `efficacite_ecologique`) and the Lotka–Volterra prey–predator model, for which it provides the instantaneous derivatives (`derivee_proie`, `derivee_predateur`) and the non-trivial equilibrium point (`equilibre_lotka_volterra` → prey\* = γ/δ, predator\* = α/β). Outputs are rounded to 10 significant digits (honest precision) and any out-of-domain input (trophic level < 1, negative energy, parameter ≤ 0, negative abundance) is refused.

```python
ecologie.energie_niveau(10000, 3)   # → 100.0  (10000 · 0.1²)
```

### Estimating a population from a biased sample

This is the statistical "demographic" core of the domain: the true mean of a population exists, but a biased sample distorts it *systematically* — a bias, not noise, which is not corrected by increasing the size.

- **`echantillon_pondere`** corrects a known inclusion bias by means of the Horvitz-Thompson estimators (`estime_ht`, mean of a population of known size N) and the Hájek estimator (`estime_hajek`, robust, recommended by default), with a confidence interval by weighted bootstrap (`intervalle_hajek`) and Kish's effective sample size (`n_effectif`). It abstains if the weights are degenerate or the sample too small.
- **`biais_longueur`** handles length bias (the inspection, waiting-time, and friendship "your friends have more friends than you" paradoxes): the observed mean equals E[X²]/E[X] = μ + σ²/μ ≥ μ, and the correction is done through the harmonic mean.
- **`berkson`** exposes collision bias: two traits that are independent in the population appear correlated (often negatively) as soon as one looks only at a subset selected on a common effect. The module quantifies the correlation in the population vs in the selected sample.

```python
echantillon_pondere.estime_hajek(valeurs, poids)   # Σwy / Σw : moyenne corrigée du biais
```

### Decision under uncertainty and value paradoxes

- **`saint_petersbourg`** shows that the expected gain is not the rational price of a bet when the distribution's tail dominates (infinite expectation, yet a small price). It provides the truncated expectation, the certainty-equivalent by logarithmic utility (Bernoulli) and the value under a finite bankroll.
- **`bandit`** covers sequential decision under uncertainty (class `Bandit`, `simule`): trading off exploration and exploitation over time.
- **`incertitude_decomposee`** separates *epistemic* uncertainty (reducible by more data) from *aleatoric* uncertainty (irreducible), from a sample or a set of predictors, and provides the associated predictive interval.

### High-dimensional and calibrated statistical inference

A set of tools to reason without over-confidence on multivariate data or data subject to a change of context:

- **`covariance_grande_dim`**: covariance estimation when the number of variables approaches that of the observations (Marchenko-Pastur law, Ledoit-Wolf shrinkage, conditioning).
- **`intervalle_tolerance`**: an interval meant to contain a given *proportion* of the population (and not the mean), with a comparison to the naive interval.
- **`region_multivariee`**: multivariate conformal prediction regions (Mahalanobis distance) and their membership test.
- **`prior_shift`**: correction of a prior change / *label shift* (Saerens-Latinne-Decaestecker method) to readjust posterior probabilities when class proportions change between training and target.
- **`calibration_ranking`**: calibration of a ranking (probability that one item is better than another, temperature adjustment, DCG / NDCG measures).

### Attached technical mechanisms

Two exact-mechanism modules, computable without any invented data, placed in this domain:

- **`blockchain`**: integrity of a block chain (`hash_bloc`, `cree_bloc`, `chaine_valide`, `merkle_root`, `preuve_travail_valide`).
- **`telecom`**: channel capacity and related quantities (`capacite_shannon`, `debit_nyquist`, `gain_db`, `longueur_onde`, `snr_depuis_db`).

### Law discovery and meta-model

- **`decouverte_loi`**: symbolic discovery of a law from observations.
- **`invention_divergente`**: wiring of the building blocks that invent beyond the mere recombination of the existing (law learning, constraint lifting, transfer by analogy, trade-off arbitration, explanation of observations, process planning).
- **`schema_relations`**: *measured* meta-model of relations (profile of a relation, compatibility of inverses, hierarchical relations).

### Common guarantee

Across the whole domain, the stance is uniform and adversarially verified: the "facts/formulas" modules (chomage, cycles_economiques, ecologie…) implement only the established mechanism and raise an error rather than producing an out-of-domain value; the statistical modules (Tier 2) explicitly expose the failure mode they correct and **abstain** when the data are insufficient or degenerate. None of them fabricates an economic-conditions figure or a country-value. This is the FAUX=0 invariant: prefer explicit abstention to a false answer.

---

## Chemistry & materials

This family of capabilities covers **bounded and exact** computation in chemistry and materials science: starting from a raw formula or a few measured quantities and deducing, without ever guessing, a molar mass, the balancing of a reaction, a concentration, an enthalpy, the nature of a bond, or even a mechanical stress in a material. The stance is that of all of Provara: the **mechanism** (the formula, the definition, the established rule) is EXACT and constitutes the guarantee; the **data** it consumes (IUPAC atomic masses, Pauling electronegativities, material constants) are sourced and supplied, never invented. Any out-of-domain input triggers a **structural abstention** (returning `HORS` or `ValueError`) rather than a plausible but wrong result. The modules are deterministic and written in pure stdlib.

### Molecular composition and stoichiometry

The core of basic quantitative chemistry. `chimie` analyzes a formula (including nested parentheses, multiplicative groups and hydrates such as `CuSO4·5H2O`) and derives from it the elemental composition, the number of atoms, the molar mass and the mass percentage of an element — an element absent from the IUPAC reference or a malformed formula yields `(HORS, None)`, never a fabricated mass.

```python
chimie.masse_molaire("H2O")          # somme pondérée des masses atomiques standard
chimie.pourcentage_massique("H2O", "O")
```

`stoechiometrie` balances an equation by seeking the smallest positive integer coefficients that cancel the atomic balance — an exact computation over ℚ (kernel of the atoms×species matrix) reusing the parser from `chimie`; the conservation of each element is verified on the returned coefficients, and a non-balanceable reaction or one with a non-unique solution triggers `ValueError`. `chimie_quantitative` extends the set to **solutions** (molarity `c = n/V`, dilution `c₁V₁ = c₂V₂`, mass concentration), to **thermochemistry** (Hess's law `ΔH = ΣΔH_f(produits) − ΣΔH_f(réactifs)`, exothermic test) and to **electrochemistry** (cell potential `E = E_cathode − E_anode`, spontaneity), with output rounded to 6 significant figures and rejection of volumes/quantities ≤ 0.

```python
chimie_quantitative.molarite(0.5, 2.0)     # n/V en mol/L
chimie_quantitative.dilution(c1, v1, v2)   # c2 après dilution
```

### Bonds, equilibria and reactions

This sub-family reasons about the nature and direction of transformations. `liaisons_chimiques` classifies a bond from Pauling electronegativities (nonpolar covalent for Δχ < 0.4, polar covalent for 0.4 ≤ Δχ < 1.7, ionic beyond) and computes the percentage of ionic character. `equilibre_chimique` computes the reaction quotient `Q = Π[produits]^ν / Π[réactifs]^ν` and compares it with the constant K to predict the direction of evolution (law of mass action: Q < K forward direction, Q > K reverse direction). `mecanismes_reactionnels` classifies nucleophilic substitutions and eliminations (SN1/SN2/E1/E2) according to the established rules of organic chemistry (number of steps, passage through a carbocation, kinetic order, stereochemistry). `stereochimie` counts stereoisomers and qualifies the relationship between configurations, and `analyse_chimique` covers elementary instrumental methods (Beer-Lambert law for absorbance and concentration, retention factor `Rf` in chromatography).

```python
liaisons_chimiques.nature_liaison(3.16, 0.93)   # -> 'ionique' (NaCl)
```

### Materials and their properties

The "materials" side computes measurable physical properties. `proprietes_materiaux` implements linear elasticity (stress `σ = F/A`, strain `ε = ΔL/L₀`, Hooke's law `σ = E·ε`, elongation) — no material constant is hard-coded, Young's modulus is a datum supplied by the caller. `composites` applies the rule of mixtures to a two-phase fiber/matrix material: Voigt upper bound (Young's modulus under parallel loading), effective density, Reuss lower bound (transverse loading), with the bounding property Reuss ≤ Voigt verified. `alliages` provides the lever rule (phase fractions) and a catalog of binary alloys; `ceramiques` covers firing shrinkage, porosity, classification by firing temperature (earthenware < faience < stoneware < porcelain) and the established fact of ceramic brittleness; `batteries` computes electrical storage quantities (energy in Wh, capacity in Ah, C-rate, charge time, energy efficiency).

```python
proprietes_materiaux.contrainte(F, A)                 # σ = F/A, A > 0 exigé
composites.module_young_composite(Vf, Ef, Em)         # borne de Voigt
```

### Processes, manufacturing and molecules of interest

Modules oriented toward chemical engineering and implementation. `genie_chimique` handles reactors and distillation (residence time, conversion in a first-order CSTR/PFR reactor, number of Fenske stages); `petrochimie` covers distillation cuts and the octane number of a blend in refining; `pharmacochimie` applies Lipinski's rule of five to evaluate the "drug-like" character of a molecule. On the manufacturing side, `usinage` computes cutting parameters (cutting speed, spindle rotation, removal rate, machining time), `impression_3d` the FDM slicing parameters (number of layers, time, mass and length of filament), and `mecanismes` the transmission of motion and force (gear ratios, mechanical advantage of the lever, output torque).

### Thermodynamics and materials physics

The bucket also gathers the adjacent physics modules mobilized by chemistry and materials. `entropie_thermo` implements the second law (entropy change, entropy of the universe, spontaneity criterion) and `nucleosynthese` bounded nuclear energy (mass defect, binding energy per nucleon, iron peak). Added to these are exact general-physics cores present in this domain: `physique` (quantities computable by formula), `maxwell` (quantitative consequences of vacuum electromagnetism), `relativite_restreinte` and `relativite_generale`, as well as `intrication` (Bell / CHSH test). All share the same rule: established formula applied as is, abstention out of domain.

### Related modules grouped in this domain

Faithful to the content of the bucket, this one also aggregates modules from neighboring sciences and infrastructure, described here by their real purpose: life sciences (`bioinfo` DNA sequences, `bioingenierie` Michaelis-Menten kinetics, `proteines`, `transport_membranaire`, `croissance_bacterienne`, `biostatistique` and `essais_cliniques` in epidemiology); space sciences (`asteroides`, `astronautique`, `big_bang`, `habitabilite`, `drake`); aeronautics (`aerodynamique`); exact mathematics (`maths_discretes`, `cardinalite`, `ordinaux`); conventions and procedures (`recettes`, `conjugaison`); and the meta foundation of Provara (`atome` the atom contract, `classifieur_bornage` the anti-hallucination status router, `invention_atomes`, `boucle_invention`, `veille_corroboration`).

### Common guarantee

Across the whole domain, the same invariant emerges explicitly from the docstrings: the mechanism is exact and adversarially verified by a dedicated validator (`valide_chimie.py`, `valide_stoechiometrie.py`, `valide_composites.py`…), the abstention is structural, and the behavior is conservative — **a false negative (abstention) is tolerated, a false positive is forbidden**. This is the direct application of the FAUX=0 principle: better to return `HORS` than to produce a chemically or mechanically inexact figure.

---

## Physics & measurements

This family gathers the Provara capabilities that **compute a physical quantity or a measurement via an established formula**, rather than recalling it from memory. The common principle is the same as the rest of the project: the mechanism (the law) is exact, the constants are sourced data (SI 2019 / CODATA), and any out-of-domain input triggers an explicit abstention (`ValueError`, `None`/`HORS`) instead of a false result. It contains the foundation for representing quantities, the major chapters of computable physics (mechanics, electromagnetism, quantum, thermal), applied measurement domains (acoustics, seismology, quality, processes) and an impossibility detector that serves as a physical guard. The bucket also aggregates, by posture proximity (exact computation + abstention), building blocks of formal mathematics, mechanisms of the living, calibrated inference and infrastructure engines, described further below.

### Representation foundation: quantities, dimensions, states

Before computing, the machine must **type** what it manipulates. `dimensions` provides dimensional algebra: each quantity carries a vector of exponents over the 7 SI base dimensions (mass, length, time, current, temperature, amount of substance, luminous intensity), with **exact** exponent arithmetic (via `Fraction`, without floating-point drift). This is the first anti-absurdity filter: adding or comparing two quantities of different dimensions, or converting between incommensurable units (metre vs second), returns `None` (HORS) — never a made-up number; the exactly defined units (1 km = 1000 m, 0 °C = 273.15 K) are exact.

- `grandeur` carries a value with its unit/dimension **and its uncertainty**, and raises `IncoherenceDimensionnelle` on a non-homogeneous operation; `grandeur_vectorielle` extends this to non-scalar quantities.
- `etat` models variables, states and state spaces (with an explicit out-of-domain value); `etats_matiere` determines the physical state according to temperature and converts °C / K / °F.

### Mechanics, statics and structures

The "forces and solids" core. `mecanique` covers dry friction (F = μN), the harmonic oscillator (period/angular frequency/frequency of a mass-spring system, simple pendulum), elastic energy and fluid statics (pressure, hydrostatic pressure, Archimedes' buoyancy), with the sourced standard gravity (BIPM, 9.80665 m/s²) and an output rounded to 6 significant figures. An invalid domain (mass or stiffness ≤ 0, coefficient < 0…) raises `ValueError`.

- `statique`: equilibrium of solids and structures (moments, moment equilibrium, support reactions, centre of mass).
- `structures_genie`: strength of materials (bending and tensile stress, second moment of area, beam deflection, Euler buckling).
- `biomecanique`: physics of the sporting gesture (range and height of a projectile, flight time, optimal angle, moment of force, impulse).
- `mecanismes_machines`: mobility of a planar mechanism (Grübler–Kutzbach criterion); `maritime`: naval architecture (hull speed, Archimedes' buoyancy, maximum floating mass, Froude number).

### Electromagnetism, waves and quantum physics

`electronique` computes resistor combinations (series/parallel), the voltage divider, the RC time constant, impedances (capacitor 1/2πfC, inductor 2πfL) and the LC resonance frequency. `quantique` implements the fundamental relations with SI 2019 constants (exact h):

```
quantique.energie_photon(f)         # E = h·f   (Planck-Einstein)
quantique.longueur_onde_broglie(p)  # λ = h/p   (de Broglie)
quantique.borne_heisenberg(dx)      # Δp ≥ ħ/(2·Δx)
```

- `rayonnement_thermique`: black body — Wien's displacement law (wavelength and frequency forms, which do not designate the same point of the spectrum) and the Stefan-Boltzmann law, anchored on known external values (CMB at 2.725 K → λ_max ≈ 1.063 mm; Sun at 5778 K → ≈ 501 nm).
- `semiconducteurs`: gap conversion eV → J, threshold wavelength, doping type (n/p); `cosmologie`: expansion of the universe (recession velocity, Hubble distance, age, redshift).

### Applied measurements and field quantities

Domains where one measures and classifies according to established scales or laws.

- `audiologie`: decibel scale, addition of levels in dB, classification of hearing loss, audible range.
- `seismologie`: moment magnitude, magnitude ↔ energy (joules) conversion, class of an earthquake.
- `controle_qualite`: statistical process control (Cp/Cpk capability indices, control limits, ppm out of specification, six sigma reference).
- `procedes_industriels`: yield, mass balance, production rate, conversion ratio; `energies_comparees`: capacity factor, energy content, energy return, CO₂ emissions; `cybernetique`: control loop (closed-loop gain, static error, stability, effect of negative feedback); `cryobiologie`: freezing and preservation.

### Impossibility detector and balances (the physical guard)

`coherence_physique` judges whether a described device **violates an established law**. It relies on the 1st principle (conservation of energy, conversion efficiency ≤ 1) and the 2nd principle (entropy, efficiency ≤ Carnot, a closed system does not cool down net). Its posture is symmetric to "never a false one": it returns `VIOLE` (a specific law is broken by the declared spec, naming it), `COHERENT_BORNE` (no violation detected — this is not a proof that it works) or `HORS` (insufficient spec). Conservative: a false positive is forbidden, abstention is tolerated.

```
coherence_physique.juge_dispositif(spec)  # -> "viole" | "coherent_borne" | "hors"
```

- `conservation` establishes a balance and flags a conservation violation; `limite` carries a theoretical limit and the gap to the observed reality.

### Adjacent building blocks grouped in this domain

The bucket brings together, under the same requirement of exact computation and abstention, several building blocks that go beyond physics in the strict sense:

- **Exact mathematics and formal systems**: `algebre_calcul` (solving linear/quadratic equations), `topologie` (Euler invariants, genus), `galois` (solvability by radicals), `godel` (Gödel numbering), `langages_formels` (grammars, Chomsky hierarchy), `information_calcul` (Shannon entropy, mutual information, KL divergence), `fractales` (self-similarity dimension), `algo_analyse` (complexity), as well as the dynamical systems `chaos` and `bifurcations` (logistic map, stability of fixed points).
- **Mechanisms of the living (bounded)**: `genetique` (DNA complement, transcription, codon → amino acid translation), `mutations` (classification and effect of a substitution), `immunite` (herd immunity threshold, effective reproduction number).
- **Calibrated inference (Tier 2)**: `propagation` (Monte-Carlo uncertainty propagation), `fermi` (order of magnitude with uncertainty), `dkw` (confidence band), `conformal_adaptatif` and `conformal_pondere` (conformal prediction), `exp3` (adversarial bandit), `tbm` (Transferable Belief Model).
- **Engines and infrastructure**: `base_faits` and `lecteur` (lookup of observed facts / generic data reader), `loi`, `deduction`, `simulation`, `logique_tri`, `questions`, `substrat_physique` and `substrat_reel` (invention discovery by transduction), `_test_geant` (large-scale training).

**Common guarantee.** Throughout this domain, the mechanism is exact and the constants are sourced; abstention is structural and conservative — faced with an invalid input or an insufficient spec, the machine returns an error, `None` or `HORS` rather than a false result: the false negative is tolerated, the false positive is forbidden (FAUX = 0).

---

## Biology & medicine

This family brings together **bounded** mechanisms of the living world (regulated physiology, neuron electrophysiology, biological rhythms), tools for **medical reasoning** (Bayesian diagnostic probability, level-of-evidence catalogues, event rates), and a set of **cross-cutting knowledge-building bricks** that the automatic classification grouped here (taxonomies, ontology, rule induction, self-improvement loop). The common thread is that of all of Provara: each module computes an **exact** result from established facts or formulas, or **abstains** (generally via `ValueError`) rather than inventing. The modules are in pure Python, deterministic, with no network or GPU.

### Physiology and regulation of the living

Three modules describe physiological mechanisms whose computation part is exact and whose reference values are sourced.

- **`homeostasie`** models the **negative feedback** that keeps a physiological variable near a set-point. The mechanism is exact (algebra of the sign); the reference set-points are sourced data from human physiology (fasting blood glucose ≈ 1 g/L, core temperature ≈ 37 °C, arterial pH ≈ 7.4). `ecart_consigne(valeur, consigne)` gives the direction of the imbalance, `correction(valeur, consigne, gain) = −gain·(valeur − consigne)` produces a correction of opposite sign to the deviation, and `est_regule(valeur, consigne, tolerance)` tests membership in the regulated band. A `gain < 0` (which would be a *positive* feedback amplifying the deviation) or a negative tolerance raise `ValueError`. Example: `homeostasie.correction(1.6, 1.0, 0.5)` returns `-0.3` (bringing a blood glucose of 1.6 g/L back toward 1.0).

- **`neurone_biologique`** implements the **leaky integrate-and-fire (LIF)** model of classical electrophysiology. `potentiel_repos()` returns the established fact −70 mV; `depasse_seuil(potentiel_mV, seuil_mV)` triggers an action potential when the membrane reaches the threshold (≈ −55 mV); `frequence_decharge` gives the rectified frequency-current (f-I) curve, and `frequence_decharge_bornee` bounds it by the maximum frequency imposed by the refractory period. A negative gain or a refractory period ≤ 0 raise `ValueError`. Example: `neurone_biologique.depasse_seuil(-50, -55)` → `True`.

- **`chronobiologie`** covers **circadian rhythms and sleep cycles**. `periode_circadienne()` returns the fact ≈ 24.2 h (intrinsic *free-running* period, Czeisler et al., Science 1999); `nombre_cycles_sommeil(duree_min, cycle_min=90)` and `duree_pour_cycles` do the exact arithmetic of the ≈ 90 min cycles; `phase_circadienne(heure)` classifies a clock hour (`'pic_melatonine'` / `'nuit'` / `'jour'`). A negative duration, a cycle ≤ 0 or an hour outside [0, 24) raise `ValueError`. Example: `chronobiologie.nombre_cycles_sommeil(480)` ≈ `5.33`.

### Medicine: diagnostic reasoning and event rate

- **`taux_de_base`** corrects the **base-rate neglect** (false positive paradox): confusing sensitivity P(+|malade) with predictive value P(malade|+) is over-confident because it ignores prevalence. The module computes the **Bayesian PPV** `vpp(sens, spec, prev) = sens·prév / [sens·prév + (1−spéc)(1−prév)]` and the **NPV** `vpn`, exposes `estimation_naive` (the faulty shortcut), compares the Brier scores of the two forecasters (`brier_naif_vs_bayes`) and provides an `analyse` façade. Inputs outside [0, 1] lead to abstention. Example: `taux_de_base.vpp(0.99, 0.99, 0.001)` ≈ `0.09` — even with an excellent test, 91 % of positives are false for a rare disease.

- **`poisson_nonhomogene`** answers "how many events in the next window, with what honest uncertainty?" when the **rate changes over time** (calls by hour, failures by age). It estimates a *local* intensity λ̂(t) by bins rather than a constant rate λ̄ (which under-covers in busy windows), and builds the prediction interval from Poisson quantiles (`intensite_bins`, `comptage`, `intervalle_comptage`, `predit_fenetre`). It abstains if the events are too few.

### Catalogues of established consensus

Two modules do not *deduce* but *observe* a state of consensus, with abstention outside the reference frame.

- **`medecines_alternatives`** associates each practice with its established **level of evidence** (closed scale: `aucune_preuve`, `preuve_faible`, `preuve_limitee`, `preuve_moderee`, `preuve_forte`, `variable`), drawn from meta-analyses and reviews (e.g. homeopathy → `aucune_preuve`; mindfulness meditation → `preuve_moderee`). `niveau_preuve(pratique)` returns a label from the scale or raises `ValueError`; `depasse_placebo(pratique)` is derived from it but **never returns `True` for an `aucune_preuve` practice** (false positive forbidden) and abstains on the undecided levels. `est_catalogue` and `pratiques` inspect the catalogue. Any practice outside the catalogue raises `ValueError`. Example: `medecines_alternatives.niveau_preuve("homeopathie")` → `'aucune_preuve'`.

- **`propagande`** is the catalogue **of the seven propaganda techniques** codified by the Institute for Propaganda Analysis (1937-1942) and of the **information disorder taxonomy** of Wardle & Derakhshan (Council of Europe, 2017), structured along two established axes: is the information false (`est_faux`) and is there intent to harm (`est_intentionnel`). `technique`, `liste_techniques`, `type_desinformation` query these reference frames; any entry outside the repertoire raises `ValueError`.

### Autonomous construction and organization of knowledge

These cross-cutting bricks, grouped here by the automatic classification, serve to *build and govern* the AI's knowledge — not to describe biology.

- **`bootstrap_savoir`** builds **an is-a taxonomy on its own** by reading definitions (Wiktionary): the genus is the first word of a definition, which itself has a definition, hence a deep is-a graph (`chat → mammifère → animal`). The `frontiere` (genera cited but not yet defined) indicates what to fetch next. API: `genus`, `graphe`, `chaine`, `frontiere`, class `Savoir`.

- **`ontologie`** reasons over the **IS-A hierarchies present in the corpus** (e.g. `taxon_parent`): transitive subsumption, `ancetres`, `est_un`, `plus_proche_commun`. The traversal is **lazy** (no materialization of transitive closure, which would blow up the RAM). Open-world invariant: `est_un(x, T)` is only `True` if a real path of facts proves it; `False` means "not derivable", never "false in the world", and never a type inference by name resemblance; data cycles are detected (`cycle`).

- **`taxonomie`** derives a **taxonomy of types from the data** to replace hand-written category lists: it measures the sample fraction (`frac_ech`) and the coverage density (`densite`) of a relation over a reference set. These measures serve only to **authorize or block** an answer already verified elsewhere (an abstention guard), never to produce a fact. API: `ensembles`, `types_de`, `frac_ech`, `densite`, `source_lexicale_rel`, `population_compatible`, `hubs`.

- **`induction_horn`** **induces candidate Horn rules** (transitivity, symmetry, reflexivity, inverse) over a binary relation, then *validates* them against examples before any adoption. FAUX=0 red line: a rule is never declared "true", at best **consistent** (covers ≥ 1 positive, 0 negative derived at the fixed point); without negative examples one does not validate (`non_refutable`, open world); the facts implied beyond the examples are marked **uncertain**. API: `derive`, `cloture_derives`, `evalue`, `induit`.

### Living self-improvement loop

- **`compounding`** is the **autonomous climb**: a curator serves a graded curriculum, the orchestrator escalates on its own on each task and stops at the first candidate that passes the visible *and* generalizes (held-out); the confirmed success joins the store and the primitives registry, so that the high stages grow on their own. API: `route`, `resoudre`, `resoudre_niveau`, `montee`, `franchies`, `etages_atteints`, class `PasMontee`.

- **`generateur`** is the producer of candidates (`Generateur` and its variants: learner, improver, recombiner, fusion, composite, from bricks), and **`generation_coherente`** provides an `Ecrivain` that produces complete and coherent sentences.

- **`utilite`** adds an **evolving utility**: utility is no longer binary but rich and **judged by the real** (correct, then generalizes, robust, simple, fast — lexicographic order), and the choice is not final: one keeps the most useful per task, a better solution supplants the old one. API: class `Utilite`, `evalue_utilite`, class `Selection`.

### Common guarantee

Across this whole domain, the FAUX=0 rule holds from end to end. The physiological and medical modules return only quantities computed from formulas or sourced facts, and **raise `ValueError` outside the reference frame** (negative gain, non-finite input, prevalence outside [0, 1], unknown practice) instead of guessing. The catalogues answer from a closed consensus or abstain. The knowledge bricks assert `est_un`/a rule only if a real path of facts proves it, remain honest in the open world (`False` = "not derivable", never "false"), and mark as *uncertain* anything that goes beyond the validated examples. The stance is constant: produce the exact, or abstain.

---

## Language, lexicon & writing

This family of capabilities lets Provara treat the word and the sentence as **verifiable**
objects, and not as the intuitions of a model: the founding principle is
"the official definition = the truth" — a word's definition is enacted, official, and
therefore a *sense oracle* that human reality judges. On this foundation, Provara
can build a certified dictionary, extend it to the scale of a complete Wiktionary,
reason about the meaning and the relations of words (hyperonymy, synonymy,
antonymy), read a French sentence from end to end and answer by **logic**,
then manufacture fully verified comprehension corpora. A second strand,
"writing" in the sense of code, covers the *polyglot portfolio*: detect the programming
languages available, choose the best-suited one for a need, and have the
result adjudicated by a judge — whatever the language.

### The certified lexicon (the sense oracle)

The starting point is a real, certified seed of a French dictionary. Each
entry carries all the verifiable axes of the word: definition, part of speech, gender,
hyperonym (is-a-kind-of), synonyms, antonyms.

- **`lexique_fr`** — the certified seed (reference structure), with the views
  `edges_isa(lex)`, `edges_syn(lex)` and the ascent `ancetres(mot, lex)`.
- **`charge_lexique`** — the scalable ingester: any dump converted to the JSONL
  format `{mot, classe, genre, definition, hyper, syn, ant}` is loaded, then **checked**
  before feeding downstream. The required coherence includes the required fields, an is-a
  graph `mot -> hyper` that is **acyclic** (a loop "X is a kind of X" would break the
  closure) and the flagging of orphan hyperonyms.

```python
lex = charge_lexique.charge("datasets/lexique.jsonl")
charge_lexique.coherence(lex)   # valide champs, acyclicité is-a, orphelins
```

### Scaling up: ingesting the large dictionaries

Crossing the lexical walls (irregular words, open sense) is done through **data**, not
through rules: we extract what the dictionary already says, without inventing anything.

- **`convertit_kaikki`** — a bridge, as a **pure** function (no network), from a
  kaikki.org/frwiktionary dump to the `charge_lexique` format. French definitions
  being written "genus-first" ("chat = mammifère carnivore félin…"), the *genus* of the
  definition serves as the hyperonym; part of speech, gender, synonyms and antonyms are mapped from
  the structured fields.
- **`savoir_massif`** — plugs the massive lexicon (1.9M entries, is-a graph of 1.87M
  edges) in as a resource for the sense bricks. The graph being too large and cyclic for
  a direct closure, each question extracts the **relevant sub-graph** (ancestry chains,
  ascent with anti-cycle guard).
- **`relations_lexique`** — exposes synonymy (undirected) and antonymy (symmetric)
  extracted from the converted lexicon, via `aretes_syn(lex)` and `paires_ant(lex)`.

```python
sav = savoir_massif.SavoirMassif()
sav.est_un("chat", "animal")            # -> True
sav.ancetre_commun("chat", "chien")     # -> "mammifère"
sav.chemin("voiture", "objet")          # -> ["voiture", "véhicule", …, "objet"]
```

### Understanding French text

Provara does not merely recall words: it analyses a sentence and draws
logical consequences from it.

- **`comprehension_integree`** — a single engine resolves, on the same sentence, the complete
  chain: structure (parsing) → who-does-what roles (subject/action/object) → sense of the
  words (is-a-kind-of, common category) → gender drawn from the definition → **deduction**.
  The outputs cross-check each other (the common category chat/chien must coincide with the gender
  drawn from the definition of "chat").
- **`lecture_comprehension`** — the AI receives facts in French ("le chat est un félin",
  "le chat mange la souris"), understands them (parses subject/relation/object) and answers:
  "Is X a Z?" by three-valued transitive deduction (yes / no / **unknown**),
  "who \<verb\> Y?" by recovering the subject. What is not derivable → "unknown".
- **`comprehension`** — the first step of abstraction: "to understand is to compress".
  Several successes sharing a structure are reduced to a reusable concept, which
  is said to be *understood* only if, regenerated then re-judged, it actually covers all its cases.

### Manufacturing verified comprehension corpora

These modules transform the certified lexicon into instruction→answer training sets
where **nothing unverified enters**.

- **`fabrique_semantique`** — produces verified pairs on all the axes of the word:
  definition, word→definition (reversible), gender, **transitive** hyperonymy, synonym,
  antonym. Anti-drift: a relation that the sense brick does not confirm is never
  emitted; JSONL output ready for training.
- **`fabrique_comprehension`** — the capstone: a single set covering all the capabilities
  (sense of words, category, SVO sentence / agreement / error detection, inference,
  paraphrase), each pair being confirmed by the corresponding oracle-brick executed
  by the judge.

### Lexical coverage and unseen words

- **`good_turing`** — corrects the over-confidence "what I have never seen has probability
  0" on long-tail word distributions (Zipf). It estimates the **missing mass**
  (P₀ ≈ N₁/N, N₁ = number of singletons) and the hidden richness (Chao1: Ŝ = S_obs + N₁²/(2·N₂)),
  reserving a positive probability for the unseen (finite log-loss). Functions: `masse_manquante`,
  `richesse_chao1`, `logloss_inedit`, `analyse`.

### Polyglot portfolio (choosing and writing in the right language)

The "writing" side: rather than writing everything in Python, Provara accumulates programming
languages and sorts among them according to the need, making sure that the result stays judgeable.

- **`environnement`** — detects what is actually executable on the machine (local discovery,
  zero network) and maps each language to its strengths via a curated registry.
- **`routeur_langage`** — for a need (performance, web, systems…), `choisit` the best language
  that is both **present** and equipped with a judgeable executor; no match → `None` (the caller
  keeps Python by default).
- **`polyglotte`** — generates a solution in another language (JS/Perl/Bash) over a bounded
  family (scalar binary operations: arithmetic, bitwise, max/min) and has it verified
  by the judge; outside its family, `demande_lang` returns HORS, never anything false.
- **`executeur_niches`** — Prolog (logic), R (statistics) and SQL (relational): three
  paradigms, a single judge that decides by example.
- **`equivalence_semantique`** — decides whether two functions compute the same thing: EQUIVALENTES
  is asserted only by **exhaustive** verification over a finite domain; otherwise, either a
  re-verifiable counter-example (DIFFERENTES), or NON_DISTINGUEES. This is the prerequisite of the
  behaviour-preserving refactor.

### The common guarantee: exactness or abstention (FAUX=0)

Across the whole domain, the same rule emerges from the docstrings: the truth comes from an enacted
source (the official definition, the dictionary) and not from a generation; a relation
that the sense brick does not confirm is **never** emitted; what is not derivable
is answered "unknown" rather than invented; an equivalence is declared only if it is
proven; and a language is proposed only if it is actually executable and judgeable. Provara
systematically prefers abstention over unverified assertion.

---

## Mathematics & algorithms

This family gathers the *computational* capabilities of Provara: exact arithmetic, analysis, discrete structures, computation theory, machine architecture, software engineering, game theory and statistical reasoning. The common thread is the same as everywhere in the system: the mechanism is *exact and deterministic* (arbitrary integers, `Fraction` fractions, binary arithmetic, enumeration), and any invalid or out-of-domain input raises `ValueError` rather than producing a wrong answer. These modules do not "guess": they *compute* when the answer is determined, and *abstain* otherwise. Many of them are directly callable primitives (same stance as `physique.py`: "reality judges, never a falsehood").

### Arithmetic, number theory and cryptography

`arithmetique_modulaire` provides the building blocks of mathematical cryptography: `pgcd`, `euclide_etendu`, `inverse_modulaire`, modular exponentiation (`exp_modulaire`, square-and-multiply), *deterministic* Miller-Rabin primality test (proven witness set for n < 3.3·10²⁴) and RSA encryption/decryption (`rsa_chiffre`, `rsa_dechiffre`). Everything is exact; a nonexistent modular inverse (gcd ≠ 1) raises `ValueError` instead of inventing a value.

```python
arithmetique_modulaire.est_premier(97)        # True
arithmetique_modulaire.inverse_modulaire(3, 7)  # 5  (car 3*5 = 15 ≡ 1 mod 7)
```

`cryptographie_appliquee` covers the symmetric side: Caesar (shift), Vigenère (repeated key), XOR (involutive). The guaranteed property is exact reversibility: `dechiffre(chiffre(m, k), k) == m`; empty key or character outside the alphabet → `ValueError`.

### Analysis: calculus, series, rigorous bounding

`calcul_infinitesimal` manipulates polynomials exactly over ℚ: `evalue`, `derivee`, `primitive`, `integrale_definie`, as well as the limits of polynomials and rational fractions at a point. `series_calcul` computes arithmetic and geometric sums (exact finite ones, and the infinite `a/(1−r)` if |r|<1) and applies the convergence criteria (geometric, Riemann series Σ1/nˢ convergent iff s>1) — a divergent series queried on its sum → `ValueError`, no invented limit.

`arithmetique_intervalles` (Tier 2) propagates a bounded uncertainty `x ∈ [a,b]` through `+ − × ÷` with *outward rounding*: by Moore's theorem, the result *always contains* the true value (coverage = 1). This is the opposite of overconfidence: the method can never be too narrow; it abstains on a division by an interval containing 0.

### Discrete structures: groups and graphs

`groupes` handles finite groups: order of an element in ℤ/nℤ, composition and signature of permutations, order of a permutation, verification that a Cayley table indeed defines a group, Lagrange's theorem. `theorie_reseaux` computes the metrics of undirected graphs: degree, average degree, density `2|E|/(n(n−1))`, normalized degree centrality, degree distribution, local clustering coefficient.

### Computation theory and foundations

A core dedicated to what one can decide, compute and type:

- `complexite` — master theorem of divide-and-conquer (`classe_master(a,b,d)` returns the symbolic Θ form) and comparison of asymptotic growth orders over a fixed vocabulary. CLRS anchors: mergesort → `n log n`, Karatsuba → n^log2(3), Strassen → n^log2(7).
- `calculabilite` — recursive functions by their definition: Ackermann-Péter (recursive but *not* primitive recursive, bounded iterative computation to remain a safe tool), primitive recursion (addition/multiplication/power), Church numerals.
- `decidabilite` — catalogue of *proven* facts: halting (undecidable, Turing 1936), SAT (decidable, NP-complete), primality (P, AKS 2002), PCP, equivalence of Turing machines… ; outside the catalogue → `ValueError`.
- `types_categories` — typing of the simply typed lambda calculus (`type_de`) and the laws of the morphisms of a free category (identity, associativity as *theorems* always true); ill-typed term or incompatible composition → `ValueError`.

```python
complexite.classe_master(2, 2, 1)   # 'n log n'  (mergesort)
```

### Machine architecture and networks

`architecture` encodes the representation of numbers (binary, hexadecimal, two's complement, binary addition). `microprocesseurs` goes down to the logic level: gates, full adder, ALU. `reseaux_ip` computes exact IPv4 addressing (network address, broadcast, mask, number of hosts, membership in a same subnet) by 32-bit arithmetic; byte ∉ 0..255 or CIDR ∉ 0..32 → `ValueError`.

### Software engineering: locate, repair, measure the tests

Two "advanced code" modules tool the debug → fix cycle. `localisation_faute` ranks the instructions by suspicion (Ochiai, spectrum-based: what is mostly executed by the tests that *fail*) then searches among candidate patches for the first one that passes *everything*, held-out included — a patch that only passes the visible tests is overfitting, therefore rejected. `mutation_testing` measures the *real* adequacy of a test suite by injecting mutants: a survivor *proven non-equivalent* reveals a gap; semantically equivalent mutants are filtered out so as not to distort the score.

### Game theory and sequential decision

`jeux_appliques` computes the *pure* Nash equilibria and dominant strategies of a bimatrix game (anchors: prisoner's dilemma, battle of the sexes, matching pennies). `jeux_zero_somme` (Tier 2) handles the maximin and the minimax theorem (security strategy, fictitious play). `kelly` gives the optimal logarithmic-growth betting fraction. `no_free_lunch` illustrates the Wolpert-Macready theorem (no universally best learner). The enumeration of profiles is exact; a malformed matrix → `ValueError`.

### Statistical reasoning and unmasked pitfalls (Tier 2)

A series of "Tier 2" modules *quantifies* statistical phenomena and unmasks the corresponding naive reasoning: anchoring (`ancrage`), the Dunning-Kruger effect as a statistical artifact (`dunning_kruger`), the misunderstood law of large numbers (`loi_grands_nombres`) and the law of small numbers / ranking by raw rate (`petits_nombres`), ergodicity (ensemble average vs temporal, `ergodicite`). For classifier evaluation: `matrice_confusion` (precision, recall, F1, MCC, balanced accuracy) and `roc_auc` (AUC with Hanley confidence interval). Added to this are non-parametric Dirichlet clustering (`dirichlet_process`), algorithmic stability and the generalization bound (`stabilite_algorithmique`), and temporal forecasting with uncertainty growing with the horizon: auto-regressive (`serie_autoregressive`) and multivariate VAR(1) with joint region (`serie_multivariee`). Each returns a *measure* and the associated uncertainty, never an unjustified certainty.

### Engines of invention, search and reasoning

The domain also contains the *meta* machinery that drives Provara's exploration: `auto_invention_ouverte` (multi-domain compositional engine), `recherche_dirigee` (taming the combinatorial explosion of invention), `planification` (multi-step plans via operators), `causalite` (causal graph + intervention), `identite` (unified canonical identity), the set of curated exercises (`exercices`), and the architecture measurement harnesses (`cherche_architecture_max`, `mesure_phase3_exhaustif`, `mesure_structure2`) which compare resolution strategies judged by reality. `garde_ressources` is the kernel net that bounds this exploration (pmap, RLIMIT) so as never to bring down the environment.

### Applied computations and related modules

The domain finally hosts exact and deterministic applicative calculators: personal finance (`budget_personnel`: balance, savings rate, 50/30/20 rule; `retraite`: proration, discount; `gestion_risque`: parametric VaR, Sharpe ratio), medical dosage (`posologie`: infusion rate, Mosteller body surface, pediatric dose) and electoral apportionment (`scrutin`: d'Hondt, Sainte-Laguë, Hare quota). Also placed in this bucket are *production* cores (charts `graphique`, raster images `raster_png`, OOXML spreadsheet `tableur_xlsx`, all "pure stdlib") and a few calculators belonging to other applicative domains but exposing exact formulas (`hydraulique`, `topographie_arpentage`, `redox`), plus the sovereign web access `veille`.

---

**Common guarantee.** Across this entire domain, the invariant is *FAUX=0*: the mechanism is exact (integers/fractions/binary arithmetic, established definitions and theorems) and abstention is *structural* — any invalid, out-of-domain or indeterminate input raises `ValueError` instead of returning a false result. The false negative (abstaining) is tolerated; the false positive is forbidden. Several modules are explicitly adversarially verified by a dedicated validator (`valide_<module>.py`) combining known anchors, soundness tests and round-trips (RSA round-trip, reversibility of encryptions).

---

## Time, dates & history

This family of capabilities lets Provara **situate facts and events in time, reason about their order, durably retain what it has learned, and forecast honestly** — all without fuzzy arithmetic or guesswork. Its core is temporal: an algebra of relations between intervals, a persistent, timestamped memory that "does not lose context over time," and a forecast that owns the uncertainty of the future through an interval rather than false precision. Around this nucleus, the domain also gathers catalogs of established facts and conventions that the AI restitutes exactly or, failing that, abstains on. Everywhere, the same stance: the mechanism is exact, and outside its reference frame it abstains, never a falsehood.

### Situating and ordering in time

`allen` implements **Allen's interval algebra**: between two proper intervals `[début, fin]` (début < fin), there exist exactly 13 mutually exclusive and exhaustive qualitative relations (`before`, `meets`, `overlaps`, `during`, `equals`, their inverses…). It is the bedrock of qualitative temporal reasoning: "did X's term overlap Y's?", "does the cause precede the effect?". `relation(a, b)` always returns exactly one relation; a malformed interval (début ≥ fin) raises `ValueError` rather than judging a degenerate input. The bounds can be any ordered type (numbers, ISO dates comparable as strings). Convenience predicates (`avant`, `chevauche`, `contient`) and the `inverse` (mirror relation, verified involutive) complete the API.

```python
allen.relation((1, 3), (2, 5))   # 'overlaps'  (1 < 2 < 3 < 5)
allen.inverse('overlaps')        # 'overlapped_by'
```

### Retaining over time: persistent memory and restitution

Three modules fulfill the mandate "the AI learns AND retains," without terabytes or dependence on a third-party AI:

- **`memoire_faits` (`MemoireFaits`)** — persistent memory of information/facts, wired into `base_faits` (the verified lookup judge). Each fact is a tiny structured entry `(relation, entité, contexte) -> (valeur, catégorie, source, horodatage)`, de-duplicated and append-only on disk (JSON). It is **bitemporal**: the context carries the time or situation, so that "Macron president of France **in 2026**" is retained without overwriting the 2017 value, and a revision history (transaction time) is kept for auditing. O(1) lookup by normalized key; absent fact → honest `HORS`, never a guess.
- **`memoire_briques` (`MemoireBriques`)** — the counterpart of the previous one for **capabilities**: a persisted library of verified bricks, re-injectable into the `existant` registry of the analysis engine (`examine_cible`). An already-learned target becomes recognized right away instead of being re-derived. Soundness is unchanged: a brick is reused only if it actually **reproduces** the data of the new target.
- **`restitution` (`MoteurRestitution`)** — the engine that quickly *recalls* what is already known (as opposed to analysis, which *derives* the unknown). Facts sharded by domain (parsimonious activation, mixture-of-experts style), exact memory-first recall in O(1), **ACT-R** recency/frequency scoring (`B = ln(Σ (Δt+1)^-d)`) to distinguish hot from cold, and "sleep" consolidation that compresses N memorized facts into one rule. Exact recall or `HORS`: never an invented answer.

### Forecasting, and guarding against the pitfalls of time series

- **`prevision`** forecasts the next value of a series with a **calibrated prediction interval**, never a point alone. Model-free method: trend by linear regression, optional seasonality (period `m`), and interval obtained by a temporal hold-out (the 1-step forecast is replayed over the history using only the past) → conformal quantile of the honest residuals. The target coverage is the `confiance` level; if the series is too short, the module abstains.

  ```python
  prevision.prevoit(serie, periode=12, confiance=0.90)
  # -> (ESTIMATION, (point, (bas, haut)), confiance)  ou  ABSTENTION
  ```

- **`regression_fallacieuse`** exposes the Granger-Newbold failure mode: regressing two **non-stationary** series (random walks, trending series) produces a "significant" `t` and a high `R²` even when the series are entirely independent (~75 % false positives instead of 5 %). The module quantifies the trap and recalls the fix (work on the differences, or test for cointegration). For stationary series, OLS inference remains valid.

### Catalogs of established facts and conventions

Several modules bound a domain through a **closed reference frame** of sourced facts or conventions; any entry outside the table yields an abstention (`HORS` or `ValueError`), never a guessed value:

- **`references`** — codes and tables laid down by a standard: international Morse code, NATO/ITU phonetic alphabet, resistor color code, frequency of a note in equal temperament (A4 = 440 Hz, 12-TET formula). E.g. `references.vers_morse("SOS")`, `references.nato("A")`, `references.frequence_note(...)`.
- **`conservation_aliments`** — food preservation methods and thresholds (refrigeration 0–4 °C, freezing −18 °C, pasteurization, sterilization/UHT, drying, salting, smoking) and the microbiological temperature danger zone.
- **`plastiques`** — resin identification code (PET=1, HDPE=2, PVC=3, LDPE=4, PP=5, PS=6, others=7), thermal class (thermoplastic vs thermoset) and glass transition temperature for a few polymers.
- **`cardiologie`** — consensus clinical formulas: maximum heart rate (220 − âge), Bazett's QTc, ejection fraction, resting-rate classes; soundness blocks any physiologically absurd domain (age outside [0, 120], volumes ≤ 0…).
- **`pseudosciences`** — scientific validity status (established consensus): `aucune` (refuted by controlled studies) or `non_demontree` (no reproducible evidence). The module reports the **evidence status** on the claims, not a judgment on subjective experience.
- **`procedes_fabrication`** — conventional classification of processes (subtractive / additive / forming / assembly) and material yield (`masse_finale / masse_initiale`, bounded [0, 1]; a yield > 1 raises an error).
- **`strategie_jeux`** — optimal strategy of solved perfect-information games by **enumerated minimax** over the complete tree: tic-tac-toe is proven a draw by construction, and `morpion_coup_optimal` returns the winning move or blocks an unstoppable threat; invalid board → `ValueError`.

### Development/security and internal measurement

- **`audit_code`** bounds development through a reference frame of verifiable rules: the **presence** of a defined dangerous pattern (injection via `eval` — CWE-95, SQL injection — CWE-89, deterministic anti-patterns) is an observable fact, returned as a dated and sourced `Constat` (CWE id). What is not bounded — asserting that "code is safe / flawless" — is never claimed (the absence of a vulnerability is undecidable).
- **`mesure_structure_pertache`** is an internal measurement bench: it compares "structure → per-task" traversal strategies (round-robin `rr2` and stride/occam/topfirst/costweight variants) to reach the right candidate of each task as fast as possible, without hand-picking a strategy. The strategy choice is **correctness-neutral** (identical coverage); only the cost is measured.

**Common guarantee of the domain (FAUX=0).** All these modules share the same rule: the mechanism — Allen relation, clinical formula, table of conventions, minimax, calibrated forecast — is exact and deterministic, and outside its domain of validity the answer is explicit abstention (`HORS`, `ABSTENTION` or `ValueError`), never an invented value. For temporal memory, this exactness extends over time: facts are timestamped, bitemporal and sourced, an absent fact returns `HORS`, and a capability is reused only if it actually reproduces the data.

---

## Reasoning & logic

This family of capabilities lets Provara **draw conclusions from premises** — and not merely recall facts. It covers classical logical inference, non-monotonic reasoning (general case and exceptions), abduction (tracing back to causes), the application of rules laid down by an authority, as well as the infrastructure that makes such reasoning *safe*: non-circular ground truth, arbitration of contradictions, and verifiable traces. The guiding thread is constant with the rest of the system: each module is deterministic, in pure Python (stdlib), sovereign/offline, and abstains rather than asserting when reality does not decide.

### Logical inference and argumentation

Two modules work on the **form** of a piece of reasoning, independently of the content.

- **`sophismes`** identifies the form of a conditional syllogism (major premise `A→B`) and judges its validity in classical propositional logic. It recognizes valid schemas (*modus ponens*, *modus tollens*) and invalid schemas (affirming the consequent, denying the antecedent); any combination outside these recognized schemas raises an error (abstention). It also provides a catalog of named informal fallacies with their definition.

  ```python
  forme = sophismes.identifie_forme("p->q", "p", "q")   # forme du raisonnement
  sophismes.est_valide(forme)                            # validité logique
  ```

- **`paradoxes`** handles the established logical paradoxes (liar, Russell, barber, Grelling–Nelson) via exact mechanisms: self-reference detection (`est_autoreferentiel`), the diagonal `p ⟺ ¬p`, a test of a heterological adjective (`est_heterologique`), and a catalog of the classic cases.

### Non-monotonic reasoning: default, exceptions and signs

When knowledge is partial, one must conclude without over-asserting.

- **`raisonnement_defaut`** models the "general case vs particular case" (non-monotonic, à la Reiter): a rule "normally the *X* are *Y*" admits explicit exceptions that revise it. Three safeguards ensure FAUX=0: the declared exception always overrides the default; the default is concluded only for a *known* member of the class (otherwise `ABSTIENT`); "not derivable" is never "false". `conclut(membre)` returns a triple `(statut, valeur, raison)` with `statut ∈ {DEFAUT, EXCEPTION, ABSTIENT}`.

  ```python
  r = raisonnement_defaut.RegleDefaut("oiseau", "vole", True)
  r.ajoute_membre("titi"); r.sauf("pingu", False)
  r.conclut("titi")   # -> défaut ; r.conclut("pingu") -> exception ; membre inconnu -> abstient
  ```

- **`qualitatif`** reasons on the *directions* of variation rather than on values: an algebra of signs (`+`, `−`, `0`, `?`) and networks of monotonic influences (`ReseauInfluences`). The ambiguity is honest: the sum of opposite signs yields `?` (indeterminate), never a guessed sign, and a path passing through `?` propagates `?`.

  ```python
  qualitatif.signe_somme("+", "-")   # -> "?" (indéterminé, non tranché au hasard)
  ```

### Abduction: inferring the best explanation

- **`abduction`** (backed by `causalite`) proposes, given observations, the hypotheses that would explain them. On a causal graph, `hypotheses_possibles` lists the candidate causes (causal ancestors) and `meilleure_explication(graphe, observations, taille_max=3)` returns the smallest set of hypotheses explaining *all* the observations (parsimony, Occam's razor). `explique` checks that a hypothesis is indeed a cause (direct or transitive) via a real path of the graph.

### Rules laid down by an authority and established norms

- **`regle`** is a generic engine of **normative rules** (laws, business rules, procedures, hygiene, standards): the AI "learns" a domain by ingesting a `Referentiel` (verified rules + sources). Bounded is: the *letter* of the rule (exact, dated, scoped lookup) and the *application* of an explicit predicate to an unambiguous case. Not bounded, hence `ABSTENTION`: interpretation, fine qualification, conflicts. Structural guarantees: an absent rule is never invented; a repealed or not-yet-in-force rule is not applied; two scopes (FR/EU/company) do not mix; a missing field of the case → abstention; `prevaut` applies the hierarchy of norms.

  ```python
  ref = regle.Referentiel("HACCP").apprend(mes_regles)
  ref.cherche("FR", "art_L123", date="2026-07-03")   # Regle en vigueur, ou None (jamais inventée)
  ```

- **`journalisme_deontologie`** applies the same stance to a **catalog of established duties** (Munich Charter, SPJ Code of Ethics): `principe(nom)` recognizes only the 7 principles in *closed-set* and `respecte_deontologie` judges only cataloged practices without ambiguity — any practice outside the catalog raises an error (abstention).

### From learned knowledge to reasoned knowledge

- **`regles_induites`** is the **induction → deduction** bridge: the rules validated by `induction_horn` become Datalog clauses consumed by `deduction`. The red line: only validated rules (consistent at the fixed point, support > 0, refutable) enter; a fact whose derivation depends on an induced rule is marked `INCERTAIN` (a generalization), never `VERIFIE`; the declared negative examples are persisted as guards (a fact declared false remains served `REFUTE`).

### FAUX=0 guarantees: ground truth, arbitration, traceability

Three building blocks found the reliability of the whole reasoning layer.

- **`ancres`** — a **non-circular** anchor bank: the ground-truth reference. An anchor is `(clé, valeur, source)` with an independent source; `verifie(cle, valeur, source_de_la_reponse)` returns `CONFIRME / CONTREDIT / INCONNU`, but **refuses** (`CIRCULAIRE`) if the source of the answer is that of the anchor: one does not corroborate oneself. Two contradictory anchors on a key → `Incoherence`.

- **`arbitre`** decides contradictions at runtime: from propositions `(valeur, source)` and a reliability table, it aggregates the weights by value and returns `CONSENSUS`, `TRANCHE` or `ABSTENTION`. `valeur_arbitree(propositions, fiabilites)` directly gives the retained value, or `None`.

  ```python
  arbitre.valeur_arbitree([(42, "capteur"), (41, "estimation")], {"capteur": 3, "estimation": 1})
  ```

- **`trace`** makes any conclusion **traceable back to the premises and re-verifiable**: a DAG of steps `(id, opération, entrées, sortie, justification, vérificateur)`. `remonte(id)` returns the whole sub-trace (and detects cycles → `Cycle`), `verifie(id)` replays the verifiers of the sub-trace and is true only if none returns false.

### Confidence of inference chains

Two "Tier 2" building blocks calibrate the confidence of sequential reasoning.

- **`calibration_sequence`**: the confidence of a multi-step generation (LLM type) is the *product* of the per-step confidences; per-step over-confidence compounds and blows up. The remedy is to recalibrate each step (isotonic, out-of-sample) *before* multiplying, with abstention if the calibration set is too small.

- **`inference_anytime`** provides an **anytime-valid confidence sequence** (Robbins, normal mixture): an interval valid *at all instants simultaneously*, which allows continuous monitoring and stopping at any time without inflating the error rate (against *peeking*).

### Querying, aiming and producing

This last sub-family connects reasoning to use.

- **`demande`** is the **query interface**: a request = signature + input→output examples; the engine returns verified code (the examples *are* the verifier), or an honest `HORS` rather than a false answer.
- **`besoin`** adds a layer of **objectives** for invention: it decomposes a bounded need into physical sub-objectives and levers, enumerates candidate principles judged by `coherence_physique` (the impossible is refuted, the possible remains a supposition), and returns `HORS` on an unknown need — to make the gap visible.
- **`chercheur_invention`** reasons over a *corpus* of targets: inventory (`EXISTE_DEJA / INVENTION / AMBIGU / BRIQUE_MANQUANTE`) and prioritization by measured reuse (a component that recurs across several verified solutions is an abstraction to extract).
- **`editeur`** is a **deterministic** substrate for creating/modifying files: the mutation applies exactly as specified or fails honestly (`ValueError`), without overwriting unread content or following symlinks (hardened against TOCTOU). It does not judge the correctness of the content, which is left to a real judge (tests, `refactor`).

*(Fidelity note: the module **`teledetection`** appears in this batch but pertains to remote sensing — GSD, NDVI, temporal resolution — and not to logical reasoning.)*

### Common guarantee of the domain

All these building blocks share the FAUX=0 invariant made explicit in their docstrings: they are **sound before being fast**. Nothing is invented (an absent rule, anchor or explanation is never fabricated), ambiguity and the unknown produce an **abstention** or an explicit `HORS` rather than an assertion, and the derived conclusions remain traceable and re-verifiable back to their premises.

---

## Uncertainty & calibration

This domain is the **unbounded** side of Provara. Where the bounded side guarantees "never a false" (exact, verified answer, or abstention), a statistical estimate cannot guarantee the exactness of a single isolated figure. The discipline therefore changes without losing its honesty: instead of a certain answer, it produces an **estimate accompanied by a calibrated confidence**, and it abstains as soon as the sample does not allow that confidence to be guaranteed. The invariant that replaces "FAUX=0" here is **calibration**: a confidence announced as "90 %" must turn out to be right ~90 % of the time, and an interval announced "at 90 %" must contain the true value ~90 % of the time. This property is checked by Monte-Carlo simulation against a known ground truth; it is reality that judges the honesty of the uncertainty, not the answer. The red line is **over-confidence** (claiming more certainty than one has), treated as just as unacceptable as a false in the bounded side.

The family gathers about fifty modules, pure Python and dependency-free, organized around this same judge.

### The transverse judge: measuring the honesty of the uncertainty

`calibration` is the domain's "reference standard": it takes pairs `(confiance, justesse)` and returns a verdict — `CALIBRE`, `SURCONFIANT`, `SOUSCONFIANT` or `ABSTENTION` when the cases are too few to judge. It provides the standard metrics (Brier score, ECE/MCE, reliability diagram, signed gap) and also judges intervals via their nominal coverage.

```python
calibration.est_calibre(confiances, justesses)        # verdict + métriques
calibration.verdict_couverture(intervalles, verites, nominal=0.9)
```

Around it revolve the complementary instruments: `scores_propres` (log-loss, Brier, CRPS, spherical score) which *ranks* forecasters by rules minimized in expectation by the true probability — the mathematical incentive to sincerity; `test_calibration` (Spiegelhalter / Hosmer-Lemeshow tests) which turns calibration into a hypothesis test; `predictif` which judges a complete predictive distribution (PIT, pinball loss); and `derive_calibration`, an online detector that alerts when a system becomes progressively over-confident.

### Repairing a poorly calibrated predictor

When a classifier announces biased probabilities, these modules recalibrate them, each in its own regime, all subject to the same judge:

- `classif_calibree` — isotonic recalibration (non-parametric, monotone).
- `calibrateurs` — the parametric toolkit: Platt (sigmoid, robust on small samples), histogram binning, beta calibration (handles asymmetry).
- `temperature` — temperature scaling for multi-class logits.
- `venn_abers` — Venn-Abers predictor, with automatic validity.
- `multilabel` — calibration of multi-label problems.
- `multicalibration` — simultaneous calibration over subgroups.

### Conformal prediction: intervals with guaranteed coverage

The cleanest guarantee of the unbounded side. `conformal` produces an interval (regression) or a set of classes (classification) that contains the true answer **at least (1−α) of the time, without any distributional assumption** — only the exchangeability of the data. If the calibration set is too small to guarantee the requested level, the module **abstains** rather than manufacturing a misleading finite interval.

```python
conformal.intervalle_conforme(residus_cal, prediction, alpha=0.1)   # couverture >= 90 %
```

The variants cover the real cases: `conformal_normalise` (*conditional* coverage under heteroscedasticity, via group-wise Mondrian or normalized score), `conformal_jackknife` (jackknife+), `conformal_label` (class-wise Mondrian), `conformal_quantile` (CQR). Two direct applications rely on the same mechanism: `risque_conforme` (risk control, e.g. bounding the false-negative rate) and `nouveaute` (out-of-distribution detection by conformal p-value, with controlled false alarm).

### Estimating with honest intervals

`incertitude` is the base building block: confidence intervals by bootstrap / Wilson (mean, proportion, comparison, trend, anomaly detection), without distributional assumption, with abstention if the sample is too small.

```python
incertitude.estime_moyenne(echantillon, confiance=0.95)
```

Added to it are specialized estimators that each avoid a precise mode of over-confidence: `meta_analyse` (DerSimonian-Laird random effects — incorporates the between-study heterogeneity that the fixed-effect model underestimates), `valeurs_extremes` (tail risk / VaR by generalized Pareto distribution), and `surdispersion` (Poisson counts vs negative binomial, when the variance exceeds the mean).

### Combining and aggregating evidence

Fusing several sources into a calibrated belief. `bayes` updates in log-odds from a **mandatory explicit prior** (never a hidden uniform), refuses degenerate likelihoods (p=0/1) that assert the impossible, and documents its caveat: correlated clues make the posterior over-confident — the module exposes it instead of hiding it (`posterior_correle`).

```python
bayes.posterior(prior, indices)
```

The rest of the family covers the other combination schemes: `bayes_sequentiel` (online Beta-Bernoulli), `bma` (Bayesian model averaging), `robust_bayes` (robust Bayes by ε-contamination), `pac_bayes` (generalization bounds), `ensemble_calibre` (stacking of forecasters), `opinions` (linear/logarithmic pools weighted by reliability), and `agregation_previsions` which weights each forecaster by its past Brier then *extremizes* the aggregate to undo the under-confidence of the naive average. `revelation_bayesienne` illustrates the dependence on the protocol (Monty Hall), where the naive estimate fails.

### Imprecise uncertainty: bounding without inventing precision

When knowledge is too poor for a point probability, these modules represent it honestly by an **interval** of probability, with the ignorance living explicitly in the gap. `croyance_dempster_shafer` associates with each hypothesis a pair `[croyance, plausibilité]` and unmasks Zadeh's paradox (Dempster's normalization can amplify a marginal hypothesis to an absurd certainty on conflicting sources). `possibilite` (Zadeh, Dubois-Prade) bounds any compatible probability by `[nécessité, possibilité]`. `p_box` (probability boxes), `prevision_walley` (lower/upper previsions) and `choquet` (Choquet integral, non-additive measures) complete this "out-of-calibration" paradigm.

### Deciding under uncertainty and ambiguity

Choosing an action when one has not a single probability but a set (credal). `decision_ambiguite` implements the rational criteria: maxmin EU (Gilboa-Schmeidler, guaranteed floor on the worst case), maxmax, Hurwicz α-maxmin, Savage minimax regret.

```python
decision_ambiguite.choisir(credal, actes, "maxmin")
```

It unmasks its failure mode: optimizing the expected utility under the single "center" of the credal set ignores the ambiguity and can choose a fragile act. `ellsberg` rationalizes ambiguity aversion, `smooth_ambiguity` models it continuously (Klibanoff-Marinacci-Mukerji), `info_gap` provides Ben-Haim's robust decision, and `optimisation_bayesienne` proposes the next point to evaluate via a Gaussian surrogate (UCB / EI acquisitions).

### Correcting biases and reasoning about causes

`causal` estimates an average treatment effect (difference of means, IPW). `donnees_manquantes` handles imputation (complete case, single, multiple). `regression_moyenne` explains Galton's regression to the mean (a rebound wrongly attributed to an intervention), and `bertrand` illustrates how a geometric probability depends on the way of drawing — a pitfall of an ill-posed definition. `confidentialite_differentielle` completes the domain on the noise-mechanism side (Laplace, ε-DP, composition).

### Common guarantee

All these modules share the same contract, inherited from calibration: **one never certifies that an isolated estimate is right — one guarantees that the announced uncertainty is calibrated** (nominal coverage respected, over-confidence forbidden), and **one abstains explicitly** as soon as the data are insufficient to hold that guarantee, rather than producing a false precision.

---

*Fidelity note: four modules present in this grouping actually belong to other domains and have no uncertainty role — `frame` (reified n-ary relation, representation foundation), `contrainte` (CSP solver, reasoning), `fabrique_francais` (verified French dataset, language) and `urgence_medicale` (established clinical scores: Glasgow, Apgar). They are documented in their own domain.*

---

## Invention & need

This family of capabilities addresses Provara's ultimate goal: *relative to what already exists, determine what is missing and provide the elements to build it*. It does not "generate" at random: it starts from a registry of known capabilities, seeks to reach a target through recombination, analogy or constraint relaxation, and retains an invention only if reality validates it (execution, held-out, uniqueness). Alongside these discovery engines, the domain gathers autonomy building blocks (the AI learns and optimizes itself), the routing toward the right judge, and a series of concrete "need" domains (accounting, training, psychometrics, citizenship, cooking) where established facts are computed rather than guessed.

### Discovering what is missing: the invention engine

`moteur_invention` is the seed of the mechanism. Given a **registry of what exists** (known, executable capabilities) and a **target function** defined by examples + adversarial held-out, it decides among five statuses, all judged by reality:

- `EXISTE_DEJA` — a known capability already reproduces the target (not a gap);
- `INVENTION` — achievable by recombining known building blocks, novel behavior, **unique** under the spec, verified on held-out → the elements are provided;
- `AMBIGU` — achievable but the spec is underdetermined (≥2 functions satisfy it) → returns a discriminating probe instead of committing;
- `BRIQUE_MANQUANTE` — coherent but no known recombination realizes it = frontier, a new atom is required;
- `INCOHERENT` — contradictory examples → HORS.

A target not decided as `INVENTION` never produces a false; it falls back onto one of the four other statuses.

```python
verdict = moteur_invention.examine_cible("somme_carres", "x", exemples, held_out)
```

`rapport_invention` is the "product" surface: it aggregates the engine (and the physical substrate) into three actionable sections — **A. achievable now** (verified recombinations + elements to build), **B. to be specified** (ambiguous targets, what reality must decide), **C. frontiers** (where a new principle is required, ranked by leverage). It has no truth logic of its own.

```python
rap = rapport_invention.rapport(corpus_code, paires_physiques)
print(rapport_invention.texte(rap))
```

### The gestures of invention: assemble, analogize, relax, orchestrate

These building blocks embody the ways a human invents without ever violating a law.

- **`transfert`** — the assembler: it composes the honest levers of a need (channels of the body, judged principles, natural strategies) into unprecedented combinations, each served as a *supposition* (generative atom), never as a fact. A built-in physical guard excludes any candidate containing a refuted principle or without a named heat sink; an unknown need → HORS, so that the gap becomes visible.
- **`structure_mapping`** — cross-domain analogy: two sets of relations (source, target) are put into bijection over the objects while preserving the predicates. An analogy is retained only if it truly preserves the structure; otherwise `None`. The score is the factual coverage of the aligned relations.
- **`relaxation`** — the TRIZ spirit: on an over-constrained problem (unsatisfiable CSP), it seeks the **smallest** set of constraints to remove in order to make it solvable, and verifies the solution of the reduced CSP. If already satisfiable → `[]`.
- **`orchestrateur_invention`** — the capstone: it makes the six divergent gestures converse (learning a law, lifting a constraint, transferring an analogy, arbitrating a Pareto trade-off, explaining observations by abduction, planning a process) via a blackboard. It has no decision logic of its own: it posts only non-`None` outputs, abstains at the first mode that returns `None`, and reports the auditable trace.

```python
mapping = structure_mapping.trouve(source, cible)   # None si aucune structure ne s'aligne
conflit = relaxation.conflit(csp)                    # noms des contraintes à relâcher, [] ou None
```

### Learning and improving on its own

A second group removes the human from the discovery and optimization loop, always under the judgment of reality (determinism, totality over the probed domain, novel behavior, generalization on held-out).

- **`auto_invention`** (`MoteurAutoInvention`) mutates its own repertoire and keeps every atom that reality validates, without being told what to look for.
- **`auto_apprend`** (`MoteurAutonome`) extends this engine with a deeper vocabulary (binary combinator `op(f(x), g(x))`) and a *confident* resolution: it gathers all candidates that pass the examples; if they agree on varied probes → robust solution, otherwise it returns the discriminating input (active learning) rather than committing a false.
- **`auto_optimise`** seeks, for an already verified solution, an equivalent but strictly less costly solution (number of O(n) passes over the input, then AST size), and adopts it only if the judge and the adversarial probes confirm the equivalence — recursively until a fixed point. At worst it changes nothing.
- **`bibliotheque_invention`** is the "sleep" phase (DreamCoder spirit): it promotes a reused abstraction into a named capability of the "what exists" library (a target then moves from re-derived `INVENTION` to `EXISTE_DEJA`), while verifying that no solvable target regresses.

### Route and answer without inventing

- **`classifieur_domaine`** is the keystone: for a request, it decides which reality constraint applies and switches to the right judge (necessity → executor/computation; physics/past/convention → fact base; posited rule → rule engine; unbounded → abstention). It is not an oracle but a router: only the verified branches emit a value, so a classification error never produces a false, at worst an "I don't know".
- **`repond`** is the conversational layer of the interface: making the assistant able to answer (`pret`, `est_fallback`, `repond`) without ever inventing.

```python
reponse = classifieur_domaine.repond(demande)
```

### Framing and demonstration

- **`mesure_richesse`** produces the map of capabilities (richness × power) — a framing, explicitly not a validation.
- **`demo_verax`** is the "either it knows, or it says so" demonstration: a set of computed questions illustrating the stance of exactness/abstention.

### Concrete need domains

Finally, several modules address direct human needs through **established** formulas and catalogs, the mechanism being exact and never guessed:

- **`comptabilite`** — accounting rules: balance sheet equation, net income, working capital, liquidity ratio, double entry.
- **`entrainement`** — training physiology: Epley 1-RM, maximum heart rate, Karvonen target zone, VO₂max estimation.
- **`psychometrie`** — test validity/reliability: standardized IQ, percentile rank, Cronbach's alpha, standard error of measurement.
- **`citoyennete`** — established catalog of rights and duties (category, is-a-right/duty, age of civic majority) — not an invention.
- **`techniques_culinaires`** — classification bounded by mode of heat transfer and reference temperatures (cooking mode and medium, Maillard range, smoke point).
- **`maximum_entropie`** — Jaynes's maximum entropy principle: the least committed distribution compatible with known constraints.

### Common guarantee

The whole domain shares the FAUX=0 red line: an invention is asserted only after verified realization (judge, held-out), behavioral uniqueness and novelty; the orchestrators and reports synthesize no conclusion beyond what each building block has verified; and lacking proof, the output is an informative abstention (`None`, HORS, discriminating probe, or "to be specified") rather than a false. The physical effectiveness of a coherent candidate itself remains a "concept to evaluate", never a fact.

---

## Memory & conversation

This family of capabilities addresses the "gap of ephemeral intelligence": an agent solves a problem, the context window empties, and the knowledge leaves with it. Provara counters it with a **persistent, sovereign and exact dialogue memory**, a **local interface** to consult it, and a module for calibrated **contextual sequential decision-making**. The common thread is the same as throughout the project: we only restore what was actually said (verbatim) or nothing, and we abstain when the data is missing — never any invention.

### Retaining and retrieving the dialogue (`conversation`)

`conversation.py` provides `MemoireConversation`, a dialogue memory **per conversation**, model-free, 100% local (no network, no third-party AI). Each turn (who speaks, what, when) is added append-only on disk (JSONL), durable and timestamped; it survives runs, `/clear` and restarts.

The four main gestures:

- **Deposit** a turn: `MEMOIRE.ajoute("bug-42", "user", "NPE au login", scope="public")`.
- **Resume** a conversation verbatim, or only its recent window: `MEMOIRE.reprend("bug-42", n=5)` (the last 5 turns, in order).
- **Recall** what is relevant without ever reloading the whole history: `MEMOIRE.rappelle("login NPE", k=3)`. An inverted index (token → turns) brings back the k relevant turns from an arbitrarily long history, weighted by idf; the memory grows, but the recall cost does not. Without `conv_id`, the recall searches across **all** conversations — this is the "deposit-for-the-next-one": an agent B finds the answer that an agent A validated.
- **Forget** in the GDPR sense: `MEMOIRE.oublie("bug-42")` fully deletes a conversation (memory + index + file), a real erasure and not a mere flag.

Two structural safeguards are built in: a **public/private boundary** (each conversation has a `scope`, "prive" by default; the public recall never sees the private) and **sovereignty** (the files never leave the machine). Module-level convenience functions (`ajoute`, `reprend`, `rappelle`) directly expose the shared instance.

### Sovereign local interface (`interface/serveur`)

`interface/serveur.py` is a thin web server built on the standard library alone (`http.server`), **localhost only**, without any framework or build step. It does not reimplement storage: it calls the API of `conversation.MEMOIRE`, and deliberately imports `conversation` (lightweight) and not `ia` (to avoid loading the reader and the risk of memory saturation).

It allows to:

- list and read the history verbatim: `liste_conversations(memoire)`, `lire_conversation(memoire, conv_id)`;
- create a conversation and write in it: `nouvelle_conversation(memoire, conv_id)`, `ajoute_message(memoire, conv_id, texte)` — the latter records the user turn, generates a *sound* answer (drawn from the real memory, never a reformulation), then returns the re-read state; the computation order is chosen so that the assistant does not quote its own question back;
- distinguish **archiving** from **forgetting**: `archive_conversation` / `desarchive_conversation` hide a conversation from the displayed history **without erasing the data** (the AI keeps remembering it, `rappelle` still sees it; reversible), whereas `oublie_conversation` is a **definitive purge** (memory + index + file + archive entry). The common UI gesture archives; forgetting is only used to erase for good.

### Contextual sequential decision-making (`bandit_contextuel`)

`bandit_contextuel.py` implements a **LinUCB contextual bandit** (Palier 2). At each turn a context `x` arrives and one chooses an arm whose reward depends on the context. A greedy agent (point estimate, zero exploration) is **over-confident**: it locks onto an arm that "seems" good and accumulates linear regret. LinUCB keeps an honest confidence width on each estimate and plays the optimistic score `θ̂_a·x + α·√(xᵀ A_a⁻¹ x)`: the bonus is large when an arm is little tested in that direction (we explore), small when it is well estimated (we exploit), which yields sub-linear regret.

The class `Agent` (K arms, `alpha=0` ⇒ greedy, `alpha>0` ⇒ LinUCB) exposes `choisir(x)`, `maj(a, x, r)`, `score`, `largeur`. The facade `analyse(thetas, contextes, rng, alpha)` compares LinUCB to the greedy agent and returns `(ANALYSE, {...})` or `(ABSTENTION, raison)` if the data is insufficient. The module is in pure Python (home-made linear algebra, seeded random generator required).

### Common guarantee

As everywhere in Provara, this domain holds the FAUX=0 rule. The conversation memory **restores the verbatim actually stored or nothing** (empty list, "no relevant turn"), and a turn is recalled only if it shares a discriminating token (excluding stop-words) with the query — no guessing. The interface only displays real turns, with explicit empty states. And the bandit **abstains** rather than exploiting an estimate that is too noisy. The rule is always: say the exact, or stay silent.

---

## Modalities & production

This domain groups together the capabilities that allow Provara to **read and produce concrete artifacts** (files, sound) and to **build/validate code reliably**. Where the other domains compute answers, this one deals with the AI's *inputs and outputs* (understanding a file, generating an exact audio signal) and with the *quality chain* that guarantees that produced code behaves as expected when confronted with reality. All the modules remain pure stdlib, sovereign and offline, and apply the same FAUX=0 discipline: when reality does not decide, we abstain rather than invent.

### Input/output modalities: reading files, producing sound

Two modules give the AI a *bounded and verifiable* core for manipulating external artifacts.

- **`parseur_fichiers`** is a format router: it determines a file's type by its extension *corroborated by the magic bytes* (never guessed), then parses it into a usable structure. It covers the text/structured formats of the stdlib (json/csv/tsv/xml/html/ini/sqlite/zip/tar/gzip/text). An unknown or unstructured binary format returns the status `HORS` (we do not fabricate content); a parse that fails is reported as an honest `ERREUR` with its reason, never a silent partial content.

  ```python
  parseur_fichiers.lit("donnees.csv")     # -> dict structuré
  parseur_fichiers.detecte_type("x.bin")  # -> "inconnu" au doute
  ```

- **`audio_wav`** is the bounded core of the **sound** modality: uncompressed integer PCM in the WAV/RIFF container (mono or stereo, 8/16/32 bits). Its guarantee is an *exact round-trip* — `encode(...)` then `decode(...)` return exactly the same integers, without loss or approximation — verified by the validator that recomputes the signal. The generators `silence`, `sinus`, `carre` produce deterministic and re-derivable samples; any overshoot of the quantization range raises a `ValueError` (no hidden clipping). The module guarantees the numerical exactness of the sample, not the fact that a sound is "pleasant" (unbounded).

  ```python
  octets = audio_wav.encode(audio_wav.sinus(440, 1.0))  # la 440 Hz, 1 s
  audio_wav.decode(octets)                               # -> mêmes échantillons
  ```

### Building reliable code: the judge and its verification ecosystem

The heart of "production" is a test chain whose signal always comes from reality (the code runs or it doesn't), never from a self-evaluation.

- **`juge`** is the founding building block: it runs a candidate code against *hidden* tests in an **isolated sandbox** (separate process, time and memory limits) and returns a binary verdict — `PASS`, `FAIL`, `TIMEOUT`, `ERROR`, `KILLED` or `SABOTAGE` (premature exit that attempts to simulate a success, detected structurally by a sentinel). It is language-agnostic: the specific part is delegated to an executor.
- **`fuzz`** is the security sieve: instead of "does it pass the tests?", it asks "does it survive reality?". Through **differential fuzzing** against a reference solution (the oracle), it generates hundreds of inputs, including aberrant cases, and classifies each discrepancy as `CRASH` (the candidate raises an exception where the reference does not) or divergence (different result). It reuses the judge as-is to run the fuzzing program.
- **`delta_debug`** minimizes a failure reproducer (Zeller-Hildebrand `ddmin` algorithm): starting from an input that triggers a bug, it returns the smallest *1-minimal* subset that still fails (removing any element makes the failure disappear), making fuzzing counter-examples actionable. The failure predicate is supplied by the caller: reality decides.
- **`profilage`** measures the *real* cost of a code (`mesure_temps`, `mesure_memoire`) and infers its **growth class** by observing how the cost evolves when the size doubles. The classification relies on a deterministic cost (counted operations, peak memory), not the noisy wall-clock time; if the empirical exponents are inconsistent across doublings, it returns `INDETERMINE` rather than an invented class.

  ```python
  profilage.classe_croissance(tailles, couts)  # -> "lineaire" / "quadratique" / INDETERMINE
  ```

- **`_nonreg`** is the standard non-regression runner, incremental and parallel. In the manner of a build system, it *hashes the import closure* of each validator and replays its verdict from a cache as long as the fingerprint has not changed, re-running only the validators actually impacted. Soundness is preserved: an unresolved dynamic import forces "always re-run", and a `FAIL` is never cached.

### Knowing one's own capabilities and sources

Two modules give the AI an auditable view of itself.

- **`capacites`** is the explicit manifest of the formula/concept capabilities: a subject is only "covered" if a *named* mechanism makes the answer known-correct, the proof *executing at call time* on cases with a known answer. This eliminates lexical false positives and forbids gaming: if a mechanism regressed, its proof would fail and the subject would become uncovered again.
- **`sources`** is the registry of reliable sources (loaded from `datasets/sources/registry.jsonl`): the authoritative catalog of where the AI gets its data from (URL, domains, relations fed, reliability, rate-limit, ingestion script). It is the "where from" counterpart of the reader, which would allow an autonomous re-ingestion; it remains purely offline.

### Logical evaluation and robust decision

- **`algebre_boole`** exactly evaluates boolean expressions and builds their truth table (recursive-descent parser over NOT/AND/XOR/OR/IMPL/EQUIV), from which tautology, satisfiability, contradiction and equivalence follow. A malformed expression raises a `ValueError` (structural abstention, never a false verdict).

  ```python
  algebre_boole.est_tautologie("a | ~a")  # -> True
  ```

- **`variational_preferences`** is a more specialized use (Palier 2): decision robust to the *misspecification* of a reference model P₀. It evaluates an act by its robust value V(f) = min_P { E_P[u(f)] + c(P) } (Hansen-Sargent multiplier case, cost = θ·KL(P‖P₀)), unmasking the over-confidence there would be in fully trusting the model. It abstains if θ ≤ 0 or if P₀ is not normalized.

### Common guarantee

The whole domain shares the FAUX=0 invariant: each module returns either a result *verifiable by reality* (exact round-trip, pass/fail verdict from execution, truth table, re-testable minimal), or an honest abstention status (`HORS`, `ERREUR`, `INDETERMINE`, `ValueError`). Nothing is ever guessed or silently fabricated: at the slightest doubt, Provara abstains rather than producing a potentially false artifact or verdict.

---

## Core & infrastructure

This family holds no domain knowledge: these are the cross-cutting mechanisms that hold the whole together. They orchestrate the dozens of specialized engines into a coherent chain, route the work to the right stage at the lowest cost, understand questions asked in natural language even when misspelled, and integrate new knowledge without ever introducing anything false. Each brick is pure Python (stdlib), deterministic and sovereign, and enforces the FAUX=0 discipline through traceability and abstention rather than guessing.

### Orchestration and routing

Two bricks turn isolated engines into a real flow and cut its cost.

The **blackboard** (`blackboard.py`) is a shared working memory. Each engine (reader, law, simulation, limit…) POSTS its intermediate results there, from which the others READ: the flow "fact → law → limit → gap → mechanism → design → verification → confidence" thus circulates end to end. The board is indexed by subject, append-only (traceable) and each entry carries a MANDATORY provenance plus an optional confidence; the arbitration of contradictions is left to another module, the blackboard merely makes the conflicts visible.

```python
bb.poste("capitale_france", "Paris", source="lecteur")
bb.lis("capitale_france")     # entrées réellement postées, ou [] — jamais inventé
bb.en_conflit("capitale_france")
```

The **router** (`routeur.py`) performs a "brain-like" parsimonious activation. The single engine has about 35 stages (zones); the canonical escalation tries them all, from the cheapest to the most expensive. `RouteurZone` learns from the past a map `clé(tâche) -> votes d'étages`, where the key `(arité, type d'entrée, type de sortie)` is readable before resolving. On a new task it PREDICTS the probable zones, tries them first, then FALLS BACK on the full escalation of the remaining zones. Central rule: "reorder, never filter" — the coverage stays strictly identical to the escalation, so no loss; cold (no vote), the prediction is empty and the behavior is exactly that of the escalation. The gain (skipped zones) grows with experience and generalizes to any task with the same key.

### Chained resolution of the main engine

`resoudre_tout` (`resoudre_tout.py`) grafts auto-creation onto the main engine without modifying it. It first calls the main engine; if it returns HORS and the task is single-argument, the autonomous loop (invention of the missing vocabulary, directed search, chains) takes over as a LAST RESORT. The autonomous candidate is kept only if it passes the judge on the visible AND on the held-out (soundness requirement: no oracle here, so held-out proof is mandatory). The base engine stays intact, with no regression on the existing validations.

```python
resoudre_tout(point_entree, signature, exemples, exemples_held, budget)
```

### Natural language understanding (fuzzy entity resolution)

`resolution.py` makes the AI tolerant to typos on the entity of a question ("protugal" → "portugal") before the lookup, without ever inventing. It is an ADDITIVE engine: it reads the reader and the fact base read-only, without touching the reader's code. `corrige(relation, saisie)` corrects ONLY if there exists a unique and close match (edit distance below a threshold) among the real keys of the relation; in case of ambiguity (two equally close candidates) or absence of a close one, no correction — we stay HORS, honest, and we do not try very short entities (too many neighbors). Beyond simple correction, the module carries a richer NL resolution: `resout_superlatif`, `resout_comparaison`, `resout_fiche`, `resout_liste` and `resout_nl_generique`, gathered behind `repond_floue(question)`.

```python
resolution.corrige("monnaie", "protugal")   # -> "portugal" si correspondance unique et proche, sinon rien
resolution.repond_floue(question)
```

### Reliable ingestion and knowledge coherence

Three bricks frame the arrival of new knowledge (typically coming from monitoring) while keeping FAUX=0.

**Extraction** (`extraction.py`) turns dirty text (articles, patents) into triples (subject, relation, object). This is the point where the false enters most easily, so extraction is DETERMINISTIC by exact patterns (French regex): `extrait(texte)` returns all candidates with confidence and provenance (pattern + source text), `extrait_surs(texte, seuil)` keeps only the top of the confidence. A sentence that matches no pattern produces NOTHING (abstention); the rest remains a candidate, to be corroborated elsewhere.

**Belief revision** (`revision.py`) reconciles instead of piling up. On a functional key (a single true value), `integre(nouvelle)` compares a belief `(clé, valeur, fiabilité, date)` to the one in place and decides: keep the old one, replace it (only if strictly higher reliability, or equal reliability but more recent) with a traced RETRACTION, or flag an undecidable CONFLICT (same reliability, same date, different values) that we do not settle at random. Never are two contradictory values held at the same time.

**Anchor auditing** (`audit_ancres.py`) diagnoses the coverage of external truth: which relations of the reader are referenced by a validator carrying external anchors (reference values coded and verified independently of the source), and which are not — priority candidates to anchor, by decreasing fact volume. The method is a SOUND over-approximation: a relation never mentioned is certainly not anchored, so the list of the non-referenced ones is a safe subset of the non-anchored ones. Read-only; `audit()` returns a dict.

### Common guarantee

All these bricks share the same FAUX=0 stance, readable in their docstrings: mandatory provenance (we always know where a result comes from), abstention (returning HORS, `[]` or nothing rather than a guessed value), reordering without filtering to preserve the exact coverage, append-only log and traced retractions, and refusal to hold a fact and its negation. The infrastructure does not seek to answer at all costs: it prefers to stay silent rather than be wrong.

---

## Other capabilities

This domain is Provara's point of convergence: it brings together, on one side, the *cross-cutting* building blocks that make everything else usable and honest (the unified entry point, the abstention policy, candidate routing), and on the other side a broad collection of bounded capabilities that fit into no single thematic family — reasoning traps, robust statistics, theoretical computer science, verifiable output modalities, applied domains grounded in established facts, and the internal self-learning machinery. All share the same stance: pure Python (stdlib), deterministic, sovereign/offline, and above all FAUX=0 — when in doubt, we abstain rather than assert.

### The unified entry point and the honesty policy

The `ia` module is **the single gateway** to everything that has been built. It adds no truth logic of its own: it *orchestrates* already-validated building blocks and routes each request, by the nature of reality, to the right judge (necessity/executor, physical/past facts/conventions, unbounded → abstention, unknown → HORS). It returns a *verified answer with its source*, or an abstention — never a falsehood.

```python
ia.demande(texte)          # aiguille et répond (valeur vérifiée + source, ou ABSTENTION/HORS)
ia.chimie("H2O")           # accès direct à une capacité bornée
ia.invente(nom, signature, exemples)   # EXISTE_DEJA / INVENTION / AMBIGU / BRIQUE_MANQUANTE
```

Behind this façade, `abstention` centralizes **the honesty decision** at a single point: `decide(preuve, confiance, seuil, contradiction, impossible)` returns `VERIFIE`, `ABSTENTION` or `HORS`. The default is abstention; we assert only if the bar is cleared; an impossibility or a contradiction dominates everything (HORS); an unknown confidence never clears a threshold. Around it revolve the plumbing blocks that make this routing safe: `fait_negatif` (distinguishing the known-false from the unknown), `prefiltre` and `typage` (discarding candidates early), `solveur_type` (type-driven resolution, "the how" rather than "the most"), `strategies` (traversal-strategy routing) and `cas_limites` (verification by the edges: limits, monotonicity, parity, homogeneity).

### Unmasking reasoning traps

A large part of the domain (the "Palier 2" blocks) does not compute a value but **unmasks a failure mode of reasoning**: it detects when a naïve conclusion would be over-confident and flags it. Here we find the great paradoxes and fallacies: Simpson (trend reversal upon aggregation), Allais, Berkson/collision, two envelopes, Parrondo, Braess, Borel-Kolmogorov, Lord, Lindley; the cognitive biases and fallacies: framing effect, the conjunction fallacy ("Linda"), sunk cost (Concorde effect), hot hand / gambler's fallacy, winner's curse, Goodhart's law, Jensen's inequality ("flaw of averages"), Pascal's mugging; the social-choice results: Condorcet jury, social choice (Condorcet/Arrow), Gibbard-Satterthwaite (strategic voting); and the statistical artifacts: Benford's law, Anscombe's quartet, publication bias, the Will Rogers phenomenon.

The common message is that **data alone do not settle the matter**: the honest attitude is to detect the reversal/artifact and to flag the dependence on the model (often causal), abstaining if the data are inconsistent.

```python
simpson.analyse(donnees, a, b)   # détecte le renversement entre strates et agrégat, et le signale
```

### Robust statistics with guaranteed coverage

Mirroring the traps, a set of modules provides **methods whose coverage stays close to nominal** where the naïve "slapped-on" formula collapses into over-confidence. Confidence intervals: `bootstrap` (percentile and BCa for an arbitrary statistic), `proportion_binomiale` (Wald / Wilson / Agresti-Coull), `multinomial_simultane`, `test_permutation`. Robust regression and filtering: `quantile_regression` (pinball loss, heteroscedasticity), `ridge` (collinearity), `erreurs_variables`, `kalman_robuste`, `processus_gaussien`. Detection and survival: `changepoint`, `shiryaev` (earliest detection), `survie` (Kaplan-Meier under censoring). Multiplicity and selection: `fdr_controle` (Benjamini-Hochberg), `p_hacking`, `surapprentissage`, `mdl` (minimum description length), `rademacher` (generalization bound), `loi_puissance` (heavy tails), `portefeuille_universel`.

```python
bootstrap.intervalle(data, stat)   # IC dont la couverture ≈ nominal, sans formule d'écart-type
```

### Theoretical computer science: computability, complexity, logic

Exact kernels cover the theory of computation: `turing` simulates a Turing machine step by step with an **explicit budget** — overrun → an honest `timeout` (the halting problem being undecidable, we do not invent the verdict of a non-terminating computation); `arret` formally handles the halting problem and the diagonal argument; `automates` simulates a deterministic finite automaton; `classes_complexite` is a catalogue of established facts (P, NP, NP-complete, NP-hard, undecidable); `preuve_propositionnelle` checks the validity of inferences (modus ponens/tollens); `controle` judges the stability of a linear system (Routh table); `bases_donnees` implements exact relational algebra (selection, projection, join, union, aggregate). `big_data` adds primitives for at-scale processing (MapReduce, Bloom filter, reservoir sampling).

### Exact mathematical computation

A few modules deliver direct and verifiable mathematical solutions: `equa_diff` (analytical solutions and Euler's method, half-life), `trigonometrie` (functions and triangle solving: law of cosines, hypotenuse), `classification_surfaces` (classification of closed 2D surfaces by genus), `pareto` (dominance and Pareto front for multi-objective optimization).

### Verifiable bounded modalities and formats

Provara can produce outputs in formats whose **kernel is exact and re-verifiable to the correct byte / up to the bijection**, explicitly refusing anything outside the supported domain (→ `ValueError`). `document_pdf` generates a PDF 1.4 whose cross-reference table `xref` points to the real byte offset of each object (re-scanned by the validator); `braille` realizes the bijection letter ↔ dots ↔ Unicode character (round-trip proven on the grade-1 alphabet); `heraldique` encodes the closed rules of the coat of arms (tinctures, rule of contrast); `web` performs exact structural checks (balanced tags, CSS specificity).

```python
document_pdf.ecris(doc, chemin)          # PDF structurellement valide, xref exacte
braille.texte_vers_braille("bonjour")    # bijectif ; hors domaine -> ValueError (jamais deviné)
```

### Applied domains grounded in established facts and formulas

A set of "science/engineering/society" modules applies **established** formulas or catalogues, with abstention on the unknown: `eclipses` (lunar phases, eclipse conditions), `glaciologie` (mass balance, iceberg), `mineraux` (Mohs scale), `pedologie` (soil texture), `toxicologie` (LD50, therapeutic index), `logistique` (economic order quantity, safety stock), `industrie40` (OEE), `marketing_metrics` (CTR, ROI, CAC), `externalites` (social cost, Pigouvian tax), `systemes_politiques` and `rhetorique` (definitions and consensus catalogues), `reseaux_neurones` (exact forward propagation: ReLU, sigmoid, dense layer) and `robotique` (forward kinematics, reachability).

### The autonomous self-learning machinery

Finally, the domain hosts **the internal workshop** that lets Provara accumulate verified successes and build its own building blocks: `store` (the success store), `boucle` and `session` (training orchestration), `taches` (the raw material), `usine_donnees` and `exporte_dataset` (assembling a learn-ready corpus), `mesure` and `mesure_v3b_net` (the "glass box" that measures learning), `exploits` and `curateur` (observatory and graduated validation), `executeur` (multi-language seam: Python, JS, Perl, Bash, C, C++, Rust, Go), `auto_synthese` (synthesis of building blocks by skeletons), `etend_savoir` and `oracle_definitions` (self-extension of knowledge through definitions), `diable` and `carte_limites_francais` (stress-testing and mapping the limits of the model-free approach).

### Common guarantee

Despite their diversity, all these capabilities rest on the same FAUX=0 contract that emerges explicitly from the docstrings: **abstention is the default** and HORS dominates (impossibility or contradiction above all); the **domain is explicit** (any out-of-scope input is refused, never guessed); the outputs are **deterministic and re-verified** (PDF structure to the correct byte, braille bijection, `xref` re-scanned); and for the statistical blocks, **coverage stays close to nominal** where the naïve formula would be over-confident. Provara prefers to say "I don't know" rather than be wrong.

## Conversational assistant (2026-07 — cabled to the chat)

Beyond the verified-facts engine, Provara now reaches these capabilities directly in conversation, each abstaining outside its guaranteed scope (FAUX=0):

- **French grammar** (`grammaire_fr`, `formes_verbales`): part of speech of any word (function words = closed finite sets; 19,200-word embedded lexicon; conjugated forms recognized via Bescherelle models over 116k forms), sentence type (question/statement/order/negation) and subject-verb-object structure. Ambiguous/unknown → "inconnu", never a wrong tag.
- **Conjugation** (`conjugaison`): present-tense table of a regular verb; honest abstention outside the guaranteed scope.
- **Statistics in natural language** (`fonction_stats_nl`): mean/median/std (exact) and ~46 calibrated functions — trend, Fermi estimate, Benford, Wilson proportion interval, Poisson rate, Kelly, anomaly, correlation/slope, group comparison, causal effect, meta-analysis. Relays the honest abstention when the sample is too small.
- **Concept/paradox explanations** (`explications`): "explain Braess's paradox / Allais / Ellsberg / Kelly…" — the brick's real computation, never a hollow paraphrase.
- **Compositional reasoning** (`_compose_relations`): composes several verified relations — "continent of the country of X" resolves the inner (country of X → verified entity E) then the outer (continent of E). Each link is an exact lookup; a missing link → abstention. Multiplies answers over the base without adding any data. Complemented by **relation-family resolution** ("country of X" reaches the `pays_de_capitale` relation, uniqueness required).
- **Document reading**: PDF text extraction (`extrait_pdf`, FlateDecode) and long-document Q&A (`lecteur_document`: verbatim passage + page + table of contents). OCR of clean printed text (`ocr`, Otsu binarization) — **uppercase AND lowercase** (vertical position in the line distinguishes case); unrecognized glyph → "?".
- **Invention engine** (`besoin`/`invention_atomes`): "how to cool a room without an air conditioner" → the physical reframing of the need.
- **Missing-invention scanner** (`inventions_composites`/`substrat_reel`): "which inventions/relations are missing for countries?" → derivable composite attributes (new "bridge ∘ target" relation with a re-verified witness over the 71.9M facts), e.g. "country → (capital ∘ city_population)". FAUX=0: each composite is a re-verified fact; usefulness not judged.
- **Geography**: distance and initial bearing between two known places.
- **Multi-source web search** with on-site context verification (Mojeek/Bing/DuckDuckGo), each passage attributed and linked.
- **Pattern learning** (`apprentissage_patrons`): learns a user's reformulations, and induces word-substitution rules that generalize to new phrases (FAUX=0: re-routing only, the answer stays verified).
- **Trust system** (`confiance`): a user correction takes effect only when backed by a **source** — Provara challenges bare assertions ("what source are you relying on?") and never overwrites a truth without one; corrections are attributed to their source. "Forget this site X" bans a domain from searches.
- **Multilingual** (`langue`): factual questions asked in English/Spanish/German/Italian/Portuguese are answered in that language (capital/population/currency/language/area of countries), resolved through the verified French pipeline. Interface localized in these 6 languages.
- **FR↔EN translation** (`traduction`): **assisted** word-by-word translation — embedded curated dictionary (common words, offline) + the cross-lingual `concept_du_mot` lexicon of the full base (~165k terms). FAUX=0: an unknown word is kept as-is and flagged, never invented; output labeled "assisted word-by-word". No fluency/reordering (honest boundary).
- **Freshness** (`_est_volatil`): a question with a temporal marker ("**current** president", "**latest** winner", "in 2026") prefers the **live** source (Wikidata) over the static base which may be stale — when the web is allowed; falls back to the base otherwise. Fresh, attributed answer.
- **Everyday decision under uncertainty** (`_conseil_parapluie`, `meteo.pluie_aujourdhui`, `decision`): "should I take an umbrella?" → today's rain probability **reported** (Open-Meteo, structured) × a **displayed** utility rule (getting soaked = 10× carrying) → advice by **expected utility**, honest abstention when the gap is too thin ("a true coin flip"), re-decided if your weighting differs. Always classed SUPPOSITION (conditional advice), never a fact.
- **Everyday life** (`_cap_quotidien`, `meteo`): **live weather** (structured Open-Meteo source, no key) — "what's the weather in Toulouse?" → a real, attributed, timestamped reading; local time and date (machine clock). With no city, Provara **asks for the city** and the next turn naming it ("In Brives") **completes** the question — a real conversation, not question-and-answer. Web off → honest, actionable refusal.
- **Visiting a named site** (`_cap_site`, `apercu_site`): "look at X.fr and tell me what you think" → Provara **reads the page** (HTTPS then HTTP fallback, never a local address/IP), reporting its title and most "prose" passage (navigation menus are discarded), attributed and linked. Asked for an opinion on the site → it quotes the page, it does not judge (FAUX=0).
- **"My opinion"** (`_cap_avis`, `_cap_avis_critere`, `_reponse_opinion` — via `pareto`/`choix_social`): on unsettled matters, Provara gives an opinion that is **built, not felt**. Numeric comparison of 2+ candidates ("best destination between France, Italy and Spain?") → each verified criterion of the base votes, verdict by **Pareto dominance** (robust opinion) or **Condorcet/Borda** (3+ candidates), with the **sensitivity** shown. The next turn "my #1 criterion is GDP per capita" **re-decides** on that criterion. Debates without numbers ("what do you think of electric cars?") → both sides sourced + an opinion **conditional** on the user's criterion. The decision rule is always shown, the opinion always falsifiable.
- **Verified-sources registry** (`sources`, `datasets/sources/registry.jsonl`): 32 official or structured sources typed by AUTHORITY (INSEE, Légifrance, WHO, World Bank, Eurostat, PubChem, NASA JPL, GBIF…), each with domains, fed relations and limits (rate-limit, key, collaborative). FAUX=0 boundary at the source: structured → may feed a verified/learned fact; consultation → attributed report only. "Where does your information come from?" lists the real registry; `ou_apprendre(domain)` says where the AI would go learn.
- **Learning web facts** (`faits_appris`): when Provara resolves a fact from a **structured** source (Wikidata), it **learns** it — stored locally (`~/.verax`), typed with source + date — and re-serves it later **without the network, even offline**, always attributed and dated ("learned from Wikidata on 2026-07-06"). Strict FAUX=0 boundary: **only structured facts are learned**; free text (Wikipedia) stays "reported", never learned. A re-served fact is a dated snapshot, not a timeless truth. **Freshness TTL** (90 days, configurable): a stale fact is re-searched first when the web is on (re-learned fresh), and still served dated offline. The diagnostic shows the count of learned facts.
- **Comprehension trunk — Phase 1** (`tronc`): the **speech-act engine** from the spec (`SPEC_TRONC_COMPREHENSION.md`) — every message is classified into a **closed map of 11 acts** (fact, calculation, reasoning, opinion, create, meta, social, state, everyday, act, unknown), with entities/relation/regime extracted ONCE and candidates **held in parallel** (never a meaning silently picked). Two visible effects: the **intent-aware honest fallback** — when nothing matches, "here is what I understood (hypothesis) + here is what I can do", never garbage — and **attunement** — "I'm lost" gets a state reading as a **supposition** ("it may be that you…", never "I feel"), no more "Noted". A gzip-kNN periphery (compression distance, zero training) **proposes** a neighbouring intention at bounded confidence; the core stays 100% explicit. **Phase 2 — the composer (§10)**: ambiguity is COMPOSED instead of silently picked — "what is the size of France?" → the verified readings served together (area 551,695 km² **and** population) + an invitation to specify; "the size of the Eiffel Tower" → height (330 m) led with, other readings flagged. Homonym guard (a country has no "height" — the ocean liner France no longer answers for the country). Gate `valide_tronc` 72/72.
- **Self-proving capability registry** (`capacites`): 281 reasoning capabilities (causality, physical laws, simulation, Pareto, Condorcet, belief revision, lexicon…) each carry a **known-answer proof** run live — the "diagnostic" command shows "capabilities proven right now: 281/281". A reachability gate (`valide_cablage`) guarantees that **every built module is cabled into the product** (zero orphans): an unwired module turns the suite red.
