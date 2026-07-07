# Provara — Analyse des manques (ce qui reste pour performer au maximum)

_Établie 2026-07-03, après le chantier « assistant conversationnel » et les mesures de ressources._
_Base : 71,9 M faits · 1387 relations · ~30 Mo RAM (colonnaire mémoire-mappée, paginée à la demande — voir P6 RÉSOLU) · lookup ~0,004 ms · 0 GPU · 0 dépendance._

Priorisé par IMPACT × faisabilité model-free. Provara a une base de faits énorme et un moteur FAUX=0 solide ;
les vrais leviers ci-dessous exploitent MIEUX ce qui existe déjà plutôt que d'ajouter de la donnée.

## STATUT (mis à jour 2026-07-06) — la plupart des leviers sont LIVRÉS

| # | Levier | Statut |
|---|--------|--------|
| P1 | Raisonnement compositionnel (+ résolution par famille) | ✅ **LIVRÉ** (`_compose_relations`, valide_composition 9/9) |
| P2 | Scanner d'inventions manquantes (OBJECTIF FINAL) | ✅ **LIVRÉ** (`inventions_composites` câblé au chat) |
| P3 | Fraîcheur / temporel | ✅ **LIVRÉ** (`_est_volatil` → source live, valide_fraicheur 10/10) |
| P4 | Compréhension conversationnelle (multi-tours/coréférence) | ✅ **EN PLACE** (« et sa monnaie » → yen… ; **clarification à trou** : « pour quelle ville ? » → « À Brives » complète, 2026-07-06) |
| P5 | Traduction FR↔EN | ✅ **LIVRÉ** (`traduction`, concept_du_mot + dico curé, valide_traduction 8/8) |
| P7 | OCR minuscules | ✅ **LIVRÉ** (casse par hauteur de ligne, valide_ocr 28/28) |
| P6 | Performance / cold-load | ~ Adressé (préchargement en fond ; daemon = Linux, hors .exe) |
| P7 | OCR multi-**police** arbitraire / audio | ⛔ Bloqué sur données de polices / hors model-free strict |
| P8 | Confiance étendue (score fiabilité, concordance de valeurs) | ~ Base en place, extension marginale |
| P9 | **Avis sur du non-tranché** (« mon avis est… ») | ✅ **LIVRÉ 2026-07-06** (`_cap_avis` : Pareto/Condorcet + critère utilisateur ; `_reponse_opinion` : pour/contre sourcé, avis conditionnel) |
| P10 | **Apprentissage des faits web** (réutilisables hors-ligne) | ✅ **LIVRÉ 2026-07-06** (`faits_appris` : Wikidata appris, typé source+date, resservi hors-ligne ; FAUX=0 structuré seul) |
| P11 | **Visite d'un site nommé** + météo en direct | ✅ **LIVRÉ 2026-07-06** (`_cap_site`/`apercu_site` ; `_cap_quotidien`/`meteo` Open-Meteo) |
| — | **Zéro orphelin** (tout module construit câblé) | ✅ **LIVRÉ 2026-07-06** (`valide_cablage` : atteignabilité prouvée ; 280 capacités auto-prouvées au diagnostic) |

Le détail d'origine de chaque levier suit ci-dessous (conservé pour la traçabilité).

---

## P1 — Raisonnement COMPOSITIONNEL (le plus gros levier)
**Manque** : « monnaie de la capitale de la France », « langue du pays le plus peuplé d'Europe » sont REFUSÉS
(garde relations-imbriquées) — honnête mais bridant. Provara répond à un fait atomique, jamais à une CHAÎNE.
**Pourquoi c'est le levier n°1** : avec les 71,9 M faits DÉJÀ présents, composer 2-3 relations démultiplie les
questions répondables sans ajouter une seule donnée. C'est le passage de « base de faits » à « moteur de
raisonnement ».
**Faisabilité** : élevée, model-free — traversée de graphe bornée (résoudre l'inner, typer le résultat, chaîner),
avec garde FAUX=0 (chaque maillon vérifié, abstention si un maillon manque). Le graphe et `voisins`/`chemin`
existent déjà.

## P2 — Le SCANNER D'INVENTIONS MANQUANTES (la vision produit ultime)
**Manque** : le moteur d'invention (`besoin`/`invention_atomes`) est câblé mais ne s'exécute que sur un CATALOGUE
de besoins minuscule. L'OBJECTIF FINAL — « déterminer s'il manque des inventions qui changeraient le monde et
fournir de quoi les construire » — n'est pas systématisé.
**Pourquoi** : c'est la raison d'être différenciante de Provara (ce qu'un LLM ne fait pas : parcourir
SYSTÉMATIQUEMENT le réel jugé pour trouver les trous). Le substrat (71,9 M faits) est là.
**Faisabilité** : moyenne — bâtir un « gap-engine » qui balaie le graphe (attributs composites dérivables,
combinaisons de leviers physiques non exploitées) et propose des candidats jugés par la réalité (coherence_physique).
Partiellement esquissé dans la mémoire projet ; à industrialiser.

## P3 — FRAÎCHEUR & TEMPOREL de la connaissance
**Manque** : la base est STATIQUE (snapshot). « président actuel de X », « dernier vainqueur de Y » peuvent être
périmés. La boucle `veille_corroboration` (N sources concordent → fait) existe mais ne tourne pas en continu.
**Faisabilité** : moyenne — brancher une boucle de veille sur les sources structurées (Wikidata live) pour les
relations volatiles, avec datation des faits (bitemporel) et le système de confiance déjà construit.

## P4 — COMPRÉHENSION conversationnelle plus profonde — 🔨 EN CHANTIER (tronc, 2026-07-07)
**Manque** : la couche grammaticale (nature, SVO) est branchée mais SHALLOW. Manquent : coréférence (« sa
capitale », « il »), portée de négation, décomposition de questions complexes multi-clauses, suivi d'état de
dialogue robuste (le contexte du tour précédent est partiel).
**Avancée 2026-07-07** : le **tronc de compréhension** (spec `SPEC_TRONC_COMPREHENSION.md`, Phases 1 ET 2
livrées — `src/tronc.py`) attaque le manque à la racine : carte fermée de 11 actes de parole, faisceau de
candidats parallèles, repli honnête intent-aware (fin du « il comprend rien »), attunement, et le
**compositeur** (§10) — l'ambiguïté se compose (« taille de la France » → superficie ET population + invitation)
au lieu d'être choisie en silence. Phases suivantes : gardes G1-G9 (banc `valide_debiaisage`), séquenceur/
utilité, puis retrait progressif des caps.
**Faisabilité** : moyenne, model-free — s'appuie sur `grammaire_fr`/`formes_verbales` déjà là ; ajouter
résolution d'anaphores bornée + parseur de questions.

## P5 — TRADUCTION LIBRE (au-delà du factuel)
**Manque** : le multilingue répond aux questions FACTUELLES en 6 langues, mais ne TRADUIT pas un texte libre.
**Faisabilité** : moyenne-élevée — le lexique T9 multilingue (~1 M mots) est le carburant ; ajouter dictionnaire
bilingue + règles de transfert (model-free, volumineux mais borné).

## P6 — PERFORMANCE à l'échelle de la base complète — ✅ RÉSOLU (2026-07-04)
**Manque (historique)** : charger 71,9 M faits prenait plusieurs minutes et 3,3 Go de RAM privée.
**Résolu** : (1) LABELS mémoire-mappés (`.colf` VER 2, `_LabelsMmap`) → les ~245 Mo de valeurs distinctes qui
restaient en tas anonyme passent en pages file-backed réclamables ; (2) RÉSIDENCE À LA DEMANDE (`MADV_RANDOM`+
`MADV_DONTNEED`) + `libere_cache()` → une requête ne rend résidentes QUE les pages qu'elle touche. **Mesuré** :
base complète 71,9 M en **~30 Mo de RAM / ~2 s** (cache chaud), lookup ~0,005 ms. Levier (b/c) du plan = FAIT.
Reste optionnel : (a) daemon persistant ; livrer le `.colf` pré-construit dans la Release pour que le TOUT PREMIER
lancement (build d'index, pic ~2,7 Go / une fois) soit lui aussi léger. Sur Windows, `madvise` est absent (no-op
sûr) mais les pages mmappées y sont aussi paginées à la demande.

## P7 — MULTIMODAL élargi
**Manque** : OCR borné au texte imprimé net (le multi-police exige une bibliothèque de gabarits de VRAIES
polices = données) ; pas d'audio/parole (le module `audio_wav` existe mais pas de reconnaissance) ; pas de
compréhension de tableaux/structure dans les documents.
**Faisabilité** : variable — OCR multi-police = chantier de données ; parole = très gros (probablement hors
model-free strict) ; tables PDF = moyen.

## P8 — Confiance & auto-amélioration (étendre l'existant)
**Manque** : le système de confiance (corrections sourcées + bannissement) est neuf. À étendre : score de
FIABILITÉ des sources, concordance de VALEURS entre sources structurées multiples (pas seulement de domaines),
et apprentissage de patrons plus profond (induction de règles au-delà des substitutions de mots).
**Faisabilité** : moyenne — briques existantes (`veille_corroboration`, `confiance`, `apprentissage_patrons`).

---

## Recommandation d'ordre
1. **P1 (compositionnel)** — le meilleur rapport impact/effort : décuple les réponses sur la base existante.
2. **P2 (scanner d'inventions)** — la valeur différenciante ultime ; à lancer une fois P1 en place (le raisonnement
   compositionnel nourrit la détection de gaps).
3. **P3/P4 en parallèle** — fraîcheur + compréhension profonde consolident l'usage quotidien.
4. Le reste (P5-P8) selon les besoins produit.

Invariant sur tout : **FAUX=0** (vérifié / attribué / abstention), model-free, souverain.
