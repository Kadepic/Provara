# CHANTIER FORGE DE BRIQUES — générateur de code sous juge d'exécution (self-improving)

> **Dev-only, gitignoré.** Runbook VIVANT du chantier validé par Yohan le 2026-07-12.
> Lire aussi : `_REPRISE_MANDAT_SUJETS.md` (couloir ingestion), `CHANGELOG.md`, mémoire
> `projet-ia-auto-amelioration`.

## 1. LE MANDAT (verbatim d'intention, Yohan, 2026-07-12)

« On lance ce chantier oui, et on va le faire **jusqu'au dernier atome possible dans l'excellence
chirurgicale atomique**. Il ne faut pas hésiter à **chercher des idées sur internet** plus ou moins
récentes (même avant 2000) ou des théories plus ou moins exotiques. Il ne faut pas oublier la mise en
place, la **pensée machine** qui est bien plus performante que l'humain, la recalibration, l'adaptation,
les **combinaisons, les fusions, l'orchestration**, la réflexion, l'analyse, la compréhension,
l'exécution. **Carte blanche** pour trouver l'excellence en te servant de notre domaine, ou d'autres
domaines qui n'ont rien à voir. » — Et : « **ce générateur de briques pourra servir au moteur d'invention
en sortie pour l'utilisateur aussi, et peut-être aux autres moteurs, donc il faut rendre tout ça
parfait.** » (= composant de PREMIÈRE CLASSE : provenance et verdicts servables à l'utilisateur.)

Pourquoi ce chantier est LE levier (validé) : le code est le seul domaine où le juge de réalité est
parfait, gratuit et instantané (l'exécution) → la génération peut être 100 % FAUX=0. Le goulot du projet
est le DÉBIT de fabrication de briques vérifiées ; ce chantier le multiplie pour tous les autres fronts
(ingesteurs, capacités, roues, couches de langue, gabarits de parole).

## 2. LA RECHERCHE (2026-07-12) — idées retenues et leur mapping

- **Mutation testing (DeMillo 1978, pré-2000)** → mécanise le TEST DU DIABLE : mesurer la FORCE d'un
  spec/d'une gate en comptant les mutants du candidat qui survivent. Un spec faible se DIT.
- **Version spaces (Mitchell 1982, pré-2000)** → l'AMBIGU structurel : ≥2 programmes minimaux distincts
  sous le spec = abstention + sonde discriminante. (DÉJÀ IMPLÉMENTÉ dans examine_cible.)
- **Superoptimisation (Massalin 1987, pré-2000)** → plus-petit-programme-d'abord = Occam/MDL. (DÉJÀ LÀ :
  min(candidats, key=len).)
- **Metamorphic testing (Chen 1998, pré-2000)** + property-based (QuickCheck 2000) → durcir le held-out
  sans oracle exact (relations f(perm(x))=f(x), etc.).
- **CEGIS (Solar-Lezama 2006)** → le contre-exemple du vérificateur ENRICHIT le spec et relance la
  recherche, au lieu de conclure. Notre boucle sonde→HORS→brique→held-out EST une CEGIS manuelle ; la
  mécaniser.
- **STOKE (Schkufza 2013)** → leçon d'or : la RECHERCHE peut être stochastique/sale, la PROMOTION doit
  être prouvée (« jamais du code faux à l'utilisateur ») = FAUX=0 exactement.
- **DreamCoder (Ellis 2021)** → sommeil : extraire les sous-expressions communes des inventions réussies,
  scorer par COMPRESSION (MDL total bibliothèque+programmes), promouvoir ce qui paie. = les
  « fusions/combinaisons » du mandat. (EMBRYON DÉJÀ LÀ : bibliotheque_invention ne promeut qu'UNE
  map-abstraction.)

## 3. L'AUDIT DU CODE EXISTANT (la carte était périmée — tout ceci EXISTE dans src/)

- `moteur_invention.examine_cible` : 5 verdicts sound (EXISTE_DEJA/INVENTION/AMBIGU/BRIQUE_MANQUANTE/
  INCOHERENT), unicité comportementale par sondes, Occam, held-out jugé en subprocess (juge.py),
  nouveauté vs existant.
- `auto_apprend.MoteurAutonome` (1014 l.) : recherche compositionnelle, ~15 familles d'extension de
  vocabulaire (composition générale prof. 2-3, filtres, matrices, dicts, chaînes, fusions, auto-synthèse
  de constantes).
- `bibliotheque_invention` : sommeil v0 (1 abstraction map, en mémoire, gain mesuré + non-régression).
- `memoire_briques.MemoireBriques` : persistance v0 (JSON nom→expr), câblée dans `ia.py`
  (invente self-improving) et `restitution.py` (briques.json). Gate `valide_memoire`.
- `invention_atomes` : le pont vers le contrat d'atome (INVENTION → SUPPOSITION générative (n+1)/(n+2)
  + FAIT borné au spec avec Verdict d'exécution réelle).
- 19 gates valide_*invention*/juge*.

## 4. LES TROUS MESURÉS (= la file d'atomes) — état

- [x] **ATOME 1 — LIVRÉ** (commit 840b9de) : memoire_briques v2, confiance zéro au disque, re-jugement au
  chargement, quarantaine tracée, spec à tuples fidèle, admission gardée dans retient(), provenance()
  servable. valide_memoire 10→28.
- [x] **ATOME 2 — LIVRÉ** (commit 5c9f792) : sommeil généralisé, promotion MULTIPLE sous score MDL
  (gain = s·(k−1)−k), garde-fou qui mord à k=1. valide_bibliotheque_invention 11→20.

- [~] **ATOME 1 (détail archivé) — Confiance zéro au disque + provenance complète** (memoire_briques). Défauts actuels :
  `charge()` croit le JSON aveuglément (un fichier altéré injecte des exprs qui seront EXÉCUTÉES par
  `_callable`/exec au probing, et servies EXISTE_DEJA) ; briques sans spec/provenance/date/verdict
  (noms opaques `appris_N`, rien de servable à l'utilisateur) ; admission sans garde interne (chaque
  appelant refait — ou oublie — le `_reproduit`). FIX : format enrichi {nom parlant, expr, spec
  (exemples+held), origine, quand, n_verifie} ; **RE-JUGEMENT de chaque brique sur SON spec au
  chargement** (la réalité re-juge à chaque session ; échec/format legacy → QUARANTAINE comptée,
  jamais injectée, jamais silencieuse) ; admission DANS retient() (reproduit exigé là, plus chez les
  appelants) ; écriture atomique try/finally (leçon 3.0ter). Même leçon que « le cache ne signait pas
  la clé ».
- [ ] **ATOME 2 — Sommeil généralisé** : compression multi-abstractions MDL (sous-exprs communes des
  briques apprises → candidates primitives si compression totale ↓), avec gain_reconnaissance +
  verifie_non_regression déjà là comme juges d'admission.
- [ ] **ATOME 3 — Boucle CEGIS** : held-out qui tue un candidat → le contre-exemple entre au spec,
  relance (budget borné) au lieu de BRIQUE_MANQUANTE immédiat.
- [x] **ATOME 4 — LIVRÉ** (commit à venir) : `force_spec` (mutation testing) + façade `ia.force_du_spec`.
  Mutants systématiques (constantes ±1/0, BinOp, Compare, BoolOp), problème du mutant équivalent géré par
  sondage, sondes ASYMÉTRIQUES qui démasquent les faiblesses cachées par la symétrie, discriminant =
  boucle CEGIS. valide_force_spec 22/22, suite 800. Bug _nb_graines (BinOp/Compare sous-comptés) tué.
- [ ] **ATOME 5 — Sortie utilisateur de première classe** : la brique servie porte son atome (FAIT
  borné + SUPPOSITION générative), sa provenance, son spec — via invention_atomes, façade ia,
  restitution. + matérialisation .py optionnelle avec gate auto-écrite et câblage capacites.
- [ ] **ATOME 6 — Held-out durci métamorphique** (relations sans oracle exact), si mesure d'un gap réel.
- [ ] **ATOME 7 (générer du code SÉCURISÉ)** — quand la forge produira du code pour l'utilisateur, s'inspirer
  de `https://github.com/rawfilejson/awesome-osint-arsenal` (à ANALYSER — note de Yohan 2026-07-12) : en
  tirer un jeu de contraintes/anti-patterns de sécurité que le juge d'exécution vérifiera EN PLUS de la
  correction fonctionnelle (pas de secret en clair, pas d'injection, entrées validées…). Croiser avec
  `audit_code` (CWE 109/109, déjà au store) : la forge doit refuser un candidat correct mais non sûr.
  Repos à ANALYSER pour en tirer contraintes/anti-patterns (notes Yohan 2026-07-12, EN TROUVER D'AUTRES) :
  · `https://github.com/rawfilejson/awesome-osint-arsenal`
  · `https://github.com/Webba-Creative-Technologies/vice`

Règles inviolables : FAUX=0 ; non-rég complète verte après CHAQUE atome ; commits atomiques
`--no-gpg-sign` sans push ; recherche web à chaque brique ; held-out durci à froid (une résolution par
recombinaison sur peu d'exemples = coïncidence probable) ; un seul process lourd.

## 5. COMMANDES

```bash
cd /mnt/c/Users/yohan/Download/Provara
export PYTHONPATH="$PWD/src:$PWD/ingestion:$PWD/interface:$PWD/outils"
PYTHONPATH=src python3 tests/valide_memoire.py         # la gate de la mémoire de briques
PYTHONPATH=src python3 tests/valide_bibliotheque_invention.py
PYTHONPATH=src python3 tests/valide_invention_atomes.py
python3 _nonreg.py                                     # ~50 s chaud, 799+ gates
```
