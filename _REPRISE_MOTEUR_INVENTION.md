# REPRISE — Moteur d'invention Provara (mandat autonome nuit, écrit avant /clear 2026-07-11)

## MANDAT DE YOHAN (à exécuter APRÈS /clear, en TROIS PHASES, en autonomie totale)

Yohan part pour la nuit. Il ARRÊTERA lui-même demain. Consignes explicites :
- **NE PAS s'arrêter, NE PAS faire de point d'étape pendant la nuit.** Enchaîner sans demander.
- Ordre ferme des phases :
  1. **PHASE 1 — DOMAINES** : continuer à ajouter des besoins-domaines d'invention (11e, 12e, …) jusqu'à
     ÉPUISEMENT (plus de domaine borné pertinent à modéliser).
  2. **PHASE 2 — LES 3 AXES** : quand les domaines sont épuisés, câbler les 3 axes ci-dessous (« ça ouvre le
     champ des possibles »).
  3. **PHASE 3 — INGESTION** : quand les 3 axes sont finis, reprendre l'INGESTION DE DONNÉES à l'échelle, en
     autonomie totale (cf. mémoires `project-ia-ingestion-sources`, `project-ia-mandat-autonomie-2026-07-02`,
     `project-ia-run-autonome-3j`, runbook `RECON-COUVERTURE-*` / `_REPRISE_MANDAT_SUJETS.md`).
- Garde inviolable partout : **FAUX=0**, non-régression complète verte, commits atomiques.

## ÉTAT AU MOMENT DU /CLEAR

- HEAD `dev` = `6ac0c20` (10e domaine communication). Working tree PROPRE, tout committé & poussé.
- `src/besoin.py` = **registre de 10 domaines** ; `src/coherence_physique.py` = juge à **7 lois (L1–L7)**.
- Gates : `valide_besoin` **220/220**, `valide_coherence_physique` **114/114**, `valide_boucle_invention`
  16/16, `valide_transfert` 16/16, **non-régression complète `_nonreg.py` : 797/797 PASS, 0 échec**.
- Le process de release de Yohan committe/pousse/merge `dev`→`main` tout seul ; NE PAS `git push`.

### Les 10 domaines livrés (nom besoin.py — loi qui réfute — nb principes)
1. `rafraichissement_confort` — Carnot (L2) — 18
2. `chauffage_confort` — conservation + Carnot chauffage — 13
3. `dessalement_eau` — **L3** travail min. séparation (osmotique) — 14
4. `stockage_energie` — conservation, rendement A/R ≤ 1 (type `conversion`) — 13
5. `capture_co2` — **L3 généralisée** R·T·ln(1/x) (type `separation`) — 12
6. `eau_potable_air` (AWG) — L3 réutilisée, x = humidité relative — 10
7. `propulsion` — **L4** quantité de mouvement + v≤c — 11
8. `eclairage` — **L5** efficacité lumineuse ≤ 683 lm/W — 11
9. `calcul` — **L6** Landauer (k·T·ln2 / bit effacé) — 11
10. `communication` — **L7** Shannon (débit ≤ B·log₂(1+S/N)) — 10

### Les 7 lois du juge `coherence_physique` (types reconnus + constante/loi)
- L1 conservation énergie (`conversion`/`moteur_thermique`, rendement ≤ 1, over-unity, mvt perpétuel/énergie libre)
- L2 Carnot (`refroidissement`/`moteur_thermique`/`pompe_chaleur`, + système fermé qui « refroidit »)
- L3 travail min. séparation : `dessalement` (osmotique, π bar ou concentration) + `separation` (R·T·ln(1/x))
- L4 `propulsion` : quantité de mouvement (poussée sans milieu NI éjection = réfuté) + v_éjection ≤ c
- L5 `eclairage` : efficacité lumineuse ≤ 683 lm/W
- L6 `calcul` : Landauer, énergie par bit effacé ≥ k·T·ln2
- L7 `communication` : débit ≤ B·log₂(1+S/N)

## LE PATRON (à copier À L'IDENTIQUE pour chaque nouveau domaine)

Fichiers : `src/besoin.py`, `src/coherence_physique.py`, `tests/valide_besoin.py`,
`tests/valide_coherence_physique.py`, `CHANGELOG.md`, `_nonreg.py`.

1. **Choisir un besoin borné + sa LOI DURE** (celle qui rend une classe de revendications impossibles).
2. **Si le juge ne couvre pas la loi → étendre `coherence_physique` D'ABORD** :
   - ajouter `Ln = "..."` + constante(s) si besoin, en tête ;
   - ajouter le `type` au tuple de types reconnus dans `juge_dispositif` ;
   - ajouter une BRANCHE `if t == "<type>":` — CONSERVATRICE : ne réfuter (`VIOLE`) que sur une contradiction
     CERTAINE de la spec DÉCLARÉE ; faux négatif toléré, **faux positif INTERDIT** ; info absente → ne pas trancher.
   - étendre `tests/valide_coherence_physique.py` : (a) violations certaines → VIOLE + bonne loi ; (b) ajouter
     des dispositifs RÉELS à la liste `reels` (jamais VIOLE) ; (c) cas LIMITE (au plancher = cohérent) ;
     (d) spec insuffisante → pas de faux positif.
   - `PYTHONPATH=src python3 tests/valide_coherence_physique.py` → doit être vert.
3. **Ajouter le domaine dans `src/besoin.py`**, juste avant `if __name__ == "__main__":` :
   - `_NOM = "..."`, `_ALIAS_ = {…}` (libellés QUALIFIÉS ; un libellé nu ambigu doit rester HORS) ;
   - `_CANAUX_ = [Canal(…) × 4]` (leviers physiques ; `grandeur` = la grandeur manipulée) ;
   - `_PRINCIPES_ = [_P(…)]` (~8–14) : chacun une `spec` jugée par le juge ; INCLURE ~2 IMPOSSIBLES (→ RÉFUTÉS)
     et des pistes RÉELLES sous-exploitées ; les cohérents restent des SUPPOSITIONS ;
   - `_OBJECTIF_` (le REFRAMING machine), `_LOI_` (la loi structurante), `_STRATEGIES_NATURE_` (4–5 exemples
     biomimétiques réduits à des leviers, PROPRES au domaine — vérifier zéro fuite depuis les autres) ;
   - `enregistre(Domaine(nom, aliases=frozenset(...), objectif, canaux, principes, strategies, loi, extras))`.
4. **Étendre `tests/valide_besoin.py`** (nouvelle section + incrémenter le n° de la section « registre ») :
   decompose OK ; mots-clés de l'objectif ; clé d'`extras` ; set des canaux ; principes impossibles → `A.REFUTE`
   + `A.est_refute(contenu)` ; réels → `A.SUPPOSITION` + confiance ∈ ]0,1[ ; `all(... in (SUPPOSITION,REFUTE))` ;
   portée nommant le domaine ; appels `COH.juge_dispositif(...)` (VIOLE + bonne loi, réel → COHERENT_BORNE) ;
   pistes sous-exploitées présentes ; stratégies propres + pas de fuite ; **domaines précédents INTACTS** ;
   `B.domaines_connus() == [… + nouveau]`.
   - `PYTHONPATH=src python3 tests/valide_besoin.py` + `valide_boucle_invention.py` + `valide_transfert.py` verts.
5. **CHANGELOG.md** : préfixer une entrée datée (le fichier a été corrompu une fois par une écriture concurrente
   du release — si l'entête paraît incohérente, `git checkout -- CHANGELOG.md` puis re-préfixer proprement).
6. **Non-régression complète** en arrière-plan : `python3 _nonreg.py` (≈ 11 min, 797 gates). Attendre
   `797/797 PASS` + `EXIT=0`. (Un changement de `besoin.py`/`coherence_physique.py` invalide large → tout re-tourne.)
7. **Commits atomiques** `git commit --no-gpg-sign` (gpg interactif impossible ici) :
   - si le juge a été étendu : commit 1 = `coherence_physique.py` + sa gate ; commit 2 = `besoin.py` +
     `valide_besoin.py` + `CHANGELOG.md` ;
   - sinon : un seul commit domaine. NE PAS `git push` (le release le fait).
8. **Mettre à jour la mémoire** `project-ia-moteur-invention-carte` (+ sa ligne `description`).

Règle de fond (mémoires `activation-parcimonieuse`, `cap-le-comment`, `perfection-atomique-frugalite`) : le plafond
du moteur N'EST PAS le juge, c'est la modélisation des besoins. On n'étend le juge QUE si la loi dure manque.

## PHASE 1 — FILE D'ATTENTE DES DOMAINES (candidats ; ✚ = nouvelle loi au juge, ↻ = loi déjà là)

- ✚ **capter l'énergie solaire** — limite de Shockley-Queisser (~33,7 % jonction simple ; ~86 % Landsberg multi-jonction/thermo). Belle loi neuve.
- ✚ **produire de l'hydrogène (électrolyse)** — tension réversible 1,23 V / ΔG 237 kJ/mol (ou thermoneutre 1,48 V) : énergie ≥ ΔG. Nouvelle loi (ou variante conversion).
- ↻ **recycler / trier les matériaux** — entropie de mélange → RÉUTILISE L3 (`separation`, séparer un métal d'un mélange). Élégant.
- ↻ **transmettre l'énergie sans fil** (inductif/laser) — rendement ≤ 1 (L1) + faisceau/couplage. Loi déjà là.
- ↻ **réfrigérer/climatiser sans électricité** (absorption solaire, froid par la chaleur) — Carnot (L2). Attention chevauchement avec cooling → cadrer distinctement.
- ↻ **potabiliser l'eau polluée** (filtration/UV) — séparation/dose. Réutilise L3 en partie.
- ✚ **stériliser / désinfecter** — dose minimale (UV, thermique) pour inactiver un pathogène. Loi neuve possible.
- ✚ **nourrir / cultiver** — plafond de rendement photosynthétique (~1–2 % de l'énergie solaire en biomasse). Loi neuve.
- ↻ **chauffer l'eau sanitaire / produire du travail mécanique** — Carnot/COP (L2). Chevauchements → cadrer ou écarter.
- ✚ **capter la chaleur fatale / thermoélectricité** — rendement ≤ Carnot du ΔT disponible (L2) + figure de mérite ZT. Souvent L2.

Choisir librement l'ordre ; privilégier les domaines à LOI NEUVE (plus d'apport). S'ARRÊTER la Phase 1 quand il
ne reste que des chevauchements/redites (annoncer l'épuisement dans le CHANGELOG, puis passer à la Phase 2).

## PHASE 2 — LES 3 AXES (« brancher tout à tout », proprement — décidé avec Yohan)

Objectif : que toute capacité (analyse, compréhension, invention, sortie…) puisse SE COMPOSER avec toute autre —
PAS par un maillage N×M (coût + bruit + casse FAUX=0 et la parcimonie), mais par :
1. **Contrat d'atome UNIVERSEL** : rendre le contrat `atome` (borné=FAIT / non-borné=SUPPOSITION, jugé par la
   réalité) l'interface de sortie/entrée de TOUTES les briques → composition typée et sûre. Cf. `atome.py`,
   mémoire `project-ia-contrat-atome-vision`.
- **Blackboard / substrat partagé universel** : toute capacité lit/écrit une donnée commune (le blackboard,
   `substrat_reel`, la mémoire de conversation) au lieu de fils directs. Cf. `valide_blackboard`.
3. **Routeur multi-domaines** : muscler le méta-routeur / `capacites.py` / `solveur_type` pour COMPOSER
   plusieurs domaines-briques sur un même besoin (ex. data-center = thermique + stockage + calcul + communication
   sous 4 lois). Cf. mémoires `activation-parcimonieuse`, `cap-le-comment`, `rechercher-architecture-chaque-brique`.
Méthode : sonde → HORS → brique → held-out durci → non-reg ; l'orchestration co-évolue avec les briques.

## PHASE 3 — INGESTION AUTONOME (voir les mémoires dédiées)

Reprendre l'ingestion à l'échelle offline, FAUX=0, jusqu'à épuisement, sans s'arrêter. Ancrages :
`project-ia-ingestion-sources`, `project-ia-mandat-autonomie-2026-07-02`, `project-ia-run-autonome-3j`,
`project-ia-carte-sujets` (+ `_REPRISE_MANDAT_SUJETS.md`, `RECON-COUVERTURE-*.md`).

## RAPPELS OPÉRATIONNELS
- Toujours `PYTHONPATH=src` pour lancer une gate isolée depuis `tests/`.
- `_nonreg.py` : lancer en arrière-plan, surveiller `EXIT=` + `797/797 PASS` ; `outils/` est bien dans son path
  (correctif de cette session — sinon `valide_oracle_metier/_domaine` dorment).
- Un seul process lourd à la fois (mémoire `un-process-lourd-a-la-fois`).
- Répondre en français à Yohan ; tâches intermédiaires en anglais possible.
