# ÉTAT DES LIEUX TOTAL — Provara — 2026-07-09 (audit chirurgical, zéro raccourci)

> Mandat Yohan : vérifier chaque atome, ne rien modifier, cartographier le parfait / les trous / la suite.
> Tout chiffre ci-dessous a été MESURÉ aujourd'hui (aucun report d'hier).

## 1. Verdicts globaux du jour (source, mesurés)

| Gate | Verdict | Note |
|---|---|---|
| verifie_demo | 31/31 | 783 checks, 0 GPU |
| valide_capacites | 73/73 (306 preuves) | |
| valide_atomes (cliquet dette) | 20/20, dette 0 | |
| valide_cablage | 504 modules atteignables, 0 orphelin | |
| valide_editeur (adverse) | 57/57 | |
| valide_maj | 42/42 | |
| valide_juge + juge_rapide | 6/6 + 25/25 | |
| valide_assistant_nl | 485/485 | |
| valide_capacites_chat | 184/184 ×2 | après correctif quiz (cf. §4) |
| suite_conversation | 26/26 gates | |
| banc_raisonnement / paraphrases | 2 + 1 ✗ sur échantillon | **base complète : les 3 répondent JUSTE** (mesuré .exe) |
| valide_interface | 55/58 | les 3 restants = classe « base complète » (§5) |

## 2. E2E .exe (produit réel, machine de Yohan)

- Build 79 installé, mono-instance, MAJ 78→79 auto OK.
- **Diagnostic : 306/306 preuves en 13,7 s** (3 servies du mémo de préchauffage daté). Matin : 273/306 en 70 s.
- Ellipse deux tours (« Marignan ? … et celle de Waterloo ? ») → « Bataille de Waterloo : 1815 » ✓.
- Bornage fictionnel : wakanda → « fictif (univers de Marvel) » + abstention ✓ ; necronomicon → « livre fictif, œuvre de Lovecraft » ✓.

## 3. Couverture atomique (654 modules produit)

- **463 modules** : validateur éponyme dédié.
- **145 scripts d'ingestion** : one-shot, jugés à l'ingestion (gates t4–t12, FAUX=0), pas de code runtime.
- **35 modules** : couverture croisée tracée (preuves capacites et/ou autres validateurs — détail en annexe).
- **11 modules à preuve UNIQUEMENT transitive** (constat, décision Yohan requise — rien modifié) :
  correction_ortho, est_un, fleuve_ville, formulation, realisation_fr (pipeline repond) ;
  prefiltre, solveur_type, typage (moteur de résolution) ; https_confiance, telecharge_donnees (infra) ;
  memoire_faits (via restitution). Tous CONSOMMÉS par le produit (0 orphelin).

## 4. Trous trouvés AUJOURD'HUI (statut exact)

| Trou | Gravité | Statut |
|---|---|---|
| Quiz : « pas Paris » et « Ouagadougou-les-Bains » jugés ✔ Exact (sous-chaîne) | **violation FAUX=0 mesurée** | corrigé (jetons épurés), 9 pièges verts, 184/184 ×2 — commit 40df3d5, EN ATTENTE DE PUSH |
| Double LISTENING 8765 (2 instances silencieuses, Windows SO_REUSEADDR) | produit | corrigé (SO_EXCLUSIVEADDRUSE + « tourne déjà » honnête) — commit 229719b, EN ATTENTE DE PUSH |
| Échec de MAJ auto sans trace (vécu 77→78) | produit | instrumenté (log nomme la cause) — commit f4eb9eb poussé (build 79) ; cause exacte à observer |
| valide_audit_ancres 5/7 | classe « base complète » | à re-passer sur les 72M (passage dédié planifié) |
| valide_surface_ia : FileNotFoundError | artefact de MON runner (VERAX_ROOT absent) | re-mesuré avec env correct : **3/3 OK** (160 alias, 388 accès vérifiés) |
| valide_taxonomie / valide_resolution / valide_substrat_reel | classe « base complète » | densités et ancres lexicales sur la base 72M |
| FAMILLE valide_lecteur_t4…t12 / nuit / client (gates d'ancres ingestion) | classe « base complète » | vérifient les relations de la base 72M, absentes de l'échantillon PAR CONSTRUCTION (messages explicites « datasets manquants ») — toutes au passage dédié |
| valide_lecteur : ancre genre_grammatical(eau) introuvable | classe « base complète » | le lexique T9 n'est pas dans l'échantillon. CONSTAT SYSTÉMIQUE : l'env source WSL n'a plus la base 72M — la classe « base complète » ne se prouve que contre ~/.verax (passage dédié via /mnt/c + cache .colf) |
| valide_invention_atomes : « relation cible inconnue population_ville » | classe « base complète » | population_ville.jsonl n'est que dans la base 72M — au passage dédié |
| valide_graphe_typé : schéma taxon_parent non vérifiable | classe « base complète » | charge lecteur.LECTEUR ; l'échantillon n'a pas la hiérarchie du vivant — au passage dédié 72M |
| valide_fonction : piège « √145 » répond au lieu de HORS | **validateur périmé, pas un FAUX** | le produit dit l'irrationalité + approximation MARQUÉE (honnête, identique hier soir 52794b6) ; le piège date d'avant la capacité « irrationalité dite ». DÉCISION YOHAN : mettre à jour le piège (recommandé) ou re-brider vers HORS |
| interface 55/58 (3 cas) | classe « base complète » | idem — 2 des 3 déjà validés indirectement sur .exe |

## 5. Passage exhaustif TERMINÉ : 695 fichiers, 100 % triés

**Source (WSL, échantillon)** : 675 OK / 20 FAIL — chaque FAIL disséqué jusqu'à sa cause.
**Passage « base complète » (validateurs exécutés DANS le .exe, base 72M réelle, via --juge-exec + wrapper)** :

| Validateur | Verdict base réelle |
|---|---|
| valide_lecteur (le socle) | **1615/1615 ancres** ✓ |
| lecteur_t5 / t6 / t9 / t10 / t11 / nuit | **316/316 · ✓ · 223/223 · 136/136 · 198/198 · 8 veines** ✓ |
| lecteur_t7 (mesures) | **152/153** — 1 seul écart RÉEL : `superficie_ile(Honshū)` ABSENT de la base livrée (présent au harnais T7 ; perdu à l'export — clé sur 17 032 faits) |
| taxonomie / graphe_typé / substrat_reel / invention_atomes / interface / surface_ia | **32/32 · 24/24 · 25/25 · 18/18 · 58/58 · 3/3** ✓ |
| audit_ancres (outil d'audit interne) | 6/22 — DOSSIER OUVERT : l'outil compte 1,1M faits (inventaire partiel ?) et classe mal les relations à validateur dédié ; instruction dédiée requise (outil, pas produit) |
| villes_coordonnees | fixture `tests/datasets/lecteur/` inexistante dans le repo (héritage harnais) — à réparer ou re-pointer |
| lecteur_client | POSIX-only (socket Unix) — légitime hors Windows |
| valide_fonction (piège √145) | validateur périmé — décision Yohan (maj du piège recommandée) |

**Bilan du passage exhaustif : 1 fait de données perdu (Honshū), 0 défaut de code produit découvert.**
Le harnais d'audit lui-même a coûté 5 itérations (CWD, env, quoting, cp1252/config isolée PyInstaller,
pkill auto-référent) — leçons consignées pour la prochaine fois ; la sonde frozen `--juge-exec` + wrapper
UTF-8 est désormais l'outil canonique pour prouver quoi que ce soit contre la base réelle.

## 6. Architecture des moteurs : qui invoque qui (mesuré par imports)

- Topologie : **étoile autour de la façade ia.py (~2 500 fonctions)** + liaisons point-à-point.
- CONVERSATION → SAVOIR, MEMOIRE, WEB, APPRENTISSAGE, FACADE. INVENTION → JUGE, APPRENTISSAGE.
  MEMOIRE → INVENTION, SAVOIR. WEB → SAVOIR, FACADE. APPRENTISSAGE → JUGE, SAVOIR.
- **SAVOIR et JUGE = fournisseurs purs** (zéro dépendance sortante — sain).
- **Constat clé : CONVERSATION n'atteint INVENTION/JUGE que via la façade** — le chat ne compose pas
  librement ces moteurs.
- **Vision Yohan (consignée, à bâtir)** : moteurs séparés mais communicants, capables d'invoquer n'importe
  quelle fonctionnalité au besoin, et de se COMBINER/FUSIONNER éphémèrement sur un besoin précis — pensée
  machine (jugée au résultat), pas modularité humaine figée. Étage candidat : un PLANIFICATEUR au-dessus du
  routage par acte, qui compose des pipelines ad hoc jugés par le réel.
- **Pollinisation croisée (mandat #8)** : greffes candidates à instruire (corroboration→quiz,
  calibration→routeur, prefiltre→autres générateurs…) — liste à établir après le passage exhaustif.

## 7. Phase 2 EXÉCUTÉE — carte chirurgicale des limites (36 sondes, .exe, base 72M, mesuré)

### Ce qui TIENT sous pression (parfait)
- **FAUX=0 structurel tient** : abstentions honnêtes partout, aucune invention ; l'affirmation fausse de
  l'utilisateur (« capitale = Marseille ») ne contamine RIEN (re-demande → « Paris » ✓).
- **Contestation directe = contrat exact** : « c'est faux, c'est Sydney » → « sur quelle SOURCE t'appuies-tu ?
  je ne modifie pas une information sans source vérifiable » ✓.
- Pièges classiques justes : Canberra ✓, Naypyidaw ✓, Nil > Amazone (chiffres) ✓, hydrogène (web attribué) ✓.
- **Import : 5/5 types LUS** (txt, csv parsé, json parsé, md, et le PDF maison extrait parfaitement).

### FAUX mesurés (2 — les seuls de la journée côté produit)
1. **« 14h37 + 2h48 » → « 16h37 (+ 2 heures) »** : les 48 minutes AVALÉES (route horaire de resout_math).
2. **« que pèse un litre d'eau sur la Lune » → « ≈ 1 kg »** : le contexte lunaire IGNORÉ (poids ≈ 1/6).

### LIMITES structurantes — le motif dominant : LE MOTEUR EXISTE, IL N'EST PAS INVOQUÉ
3. Pas de composition multi-hop (« capitale du pays où est né Einstein » — les 2 faits SONT dans la base).
4. Pas de requête temporelle (« qui dirigeait la France en 1962 » — les qualificatifs de dates T8 sont ingérés).
5. Conversions impériales non routées (« pieds » — relations T7 présentes).
6. Pas de composition d'opérations (« √20 × √5 » → répond sur √5 seul ; la vraie réponse est EXACTE : 10).
7. Problèmes à étapes (trains qui se croisent) : pas de solveur cinématique NL (greffe solveur_type identifiée).
8. **Fichiers lus mais pas INTERROGEABLES** : max d'une colonne CSV, comptage JSON, résumé MD, extraction
   ciblée PDF → tous refusés après lecture parfaite.
9. **Synthèse de code NON atteignable en NL : 0/5** — genere_langage est PROUVÉ (diagnostic) mais aucune route
   chat ; pire : « tours de Hanoï » part au lexique (liste de mots surréaliste — à-côté le plus laid du jour).
10. **Invention non invoquée sur « invente X »** — assemble_invention prouvé, mais le chat demande de préciser.
11. « es-tu sûr ? / prouve-le » → pas de production de preuve à la demande (les ancres existent).
12. **Mémoire conversationnelle = verbatim, pas extraction** : « le chien s'appelle Rex » rappelé en écho brut ;
    la correction « en fait c'est Max » NE REMPLACE PAS (re-demande → ressort Rex). Contredit le mandat
    « corrections font autorité » — trou réel (borné : verbatim, jamais affirmé comme fait).
13. Écho « D'après ce que tu m'as dit » servi à contretemps (suivis de conversation E2/D3) — perte de contexte.

### Lecture stratégique
2 FAUX à tuer (routes calcul), puis l'essentiel des limites = ROUTAGE et COMPOSITION, pas des capacités
manquantes — exactement la vision « invocation universelle + fusion éphémère » : les briques sont là,
l'orchestration ne les sert pas encore au chat.
