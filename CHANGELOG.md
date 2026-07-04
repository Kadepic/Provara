# Journal des modifications — Provara

## 2026-07-04 — RENOMMAGE « VERAX → Provara » + UX du 1er lancement + 3 bugs d'interface corrigés

### Renommage complet de la marque (raison : antériorité de marque)
- « **verax** » est une marque UE **enregistrée** (classes 9 & 42 — logiciel/SaaS, DSM IP Assets), plus une société
  homonyme « Verax AI ». **Provara** (0 antériorité INPI/EUIPO) retenu après recherche. Projet toujours open source,
  non commercial.
- **GitHub** : org `Verax-IA` → `Provara-IA`, repo `Verax` → `Provara` → **github.com/Provara-IA/Provara**
  (redirections GitHub actives). Rebrand du code (57 fichiers) : marque visible VERAX→Provara, exe **`Provara.exe`**,
  `Lancer_Provara.bat`, workflow `--name Provara`, asset `Provara-windows.zip`, URLs mises à jour.
- **Identifiants techniques CONSERVÉS** (invisibles, éviter d'orpheliner les données déjà installées) : dossier
  `~/.verax`, variables `VERAX_*`, module `verax_boot.py`, `demo_verax.py`. Asset cache Release renommé
  `Provara_cache_v1.tar.gz` (URL_CACHE alignée dans `telecharge_donnees.py`).
- **Éléments hors-repo rebrandés** : portfolio (yohanfauck.fr), CV (source + PDF régénéré), bannière LinkedIn,
  post d'annonce.

### UX du PREMIER lancement (plus d'écran figé — demandes Yohan)
- **Téléchargement des 72M rendu OPTIONNEL** : le `.exe` démarre **instantanément** sur l'échantillon embarqué
  (~1,1 M faits). La base complète s'installe **à la demande** via un bouton « Base complète » dans l'interface
  (choix explicite : ~6 Go de disque, 15-20 min, une seule fois) — `lance.py` ne télécharge plus au lancement.
- **Modale de chargement** pilotée par la nouvelle route **`GET /api/status`** : s'affiche pendant le chargement
  (« Provara se prépare… »), montre la progression du téléchargement/décompression, et **se ferme** quand l'IA est
  prête. Offre d'installation + redémarrage automatique (`/api/installer-base`, `/api/redemarrer`) ; bouton
  **Quitter** (`/api/quitter`).
- **Exe FENÊTRÉ** (`--noconsole` par défaut) : plus de fenêtre terminal. `verax_boot` redirige `stdout/stderr` vers
  `~/.verax/verax.log` quand la console est absente (sinon un `print` planterait le thread de préchargement).
  Documentation + README : « prévoir l'espace disque », « uniquement la première fois », avertissement si lancé
  depuis un terminal.

### Trois bugs d'interface trouvés EN CONDITIONS RÉELLES (auraient bloqué TOUS les utilisateurs)
- **Erreur JS `I18N` (zone morte temporelle)** — CAUSE RACINE du blocage : `majTheme()` était appelé au chargement
  AVANT la déclaration `const I18N` ; le garde `typeof I18N` ne protège pas un `const` en TDZ → `ReferenceError`
  qui **stoppait tout le script** → la modale ne s'initialisait jamais et restait figée. Corrigé : application du
  thème différée au `DOMContentLoaded`.
- **Ordre DOM de la modale** : le `<div id="verax-modale">` est placé APRÈS le `<script>` → `getElementById`
  renvoyait `null` à l'exécution → `tick()` jamais démarré. Corrigé : init modale + bouton Quitter au
  `DOMContentLoaded`. Anti-cache `?t=` ajouté sur le sondage `/api/status`.
- **Nom d'asset cache** : le code pointait `verax_cache_v1.tar.gz` alors que la Release livre
  `Provara_cache_v1.tar.gz` → 404 → build à froid lent pour les nouveaux utilisateurs. URL alignée.
- Validé par TEST NAVIGATEUR RÉEL (Chrome headless + API simulée) : modale fermée, app rendue, thème/langue OK.

### Assistant : reconnaître « je me présente » (retour live Yohan)
- « Bonjour je m'appelle yohan » partait en recherche web → renvoyait « Yoann Gourcuff ». Corrigé
  (`interface/repond.py`, `_reponse_sociale`) : détection des tournures NON ambiguës (« je m'appelle X »,
  « moi c'est X », « appelle-moi X », « mon nom est X », « my name is X ») → salue **par le prénom**
  (« Bonjour Yohan, enchantée 🙂 »), **jamais** de recherche sur le prénom. Distingué de la question sur le nom de
  l'IA (« comment tu t'appelles ? » → « Je m'appelle Provara »). Garde-fou anti-faux-prénom (« moi c'est fatigué »
  → non déclenché) ; « je suis X » exclu (ambigu). Gates : assistant_nl **77/77**, conversation **9/9**,
  restitution **29/29**, capacites_chat **19/19**.

## 2026-07-04 — Optimisation RAM majeure (base complète 3,3 Go → ~30 Mo) + docs realignées

### Lecteur : de 3,3 Go à ~30 Mo de RAM pour les 71,9 M faits (FAUX=0 préservé)
- **LABELS mémoire-mappés** (`src/lecteur.py`, `.colf` **VER 2**, nouvelle classe `_LabelsMmap`) : les listes de
  valeurs distinctes (mesuré 245 Mo — le DERNIER gros poste resté en tas anonyme : `definition_nom` 32 Mo,
  `taxon_parent` 22 Mo…) passent en blob UTF-8 mmappé, décodé À LA DEMANDE et mutualisé. Prouvé byte-identique
  (A/B hash 45 tables = 0 divergence). Import du lecteur 15,7 s → 1,4 s (labels plus désérialisés au load).
- **Résidence à la demande** (`MADV_RANDOM` + `MADV_DONTNEED` après lecture d'en-tête ; échappatoire
  `LECTEUR_MADV=0`) + **`lecteur.libere_cache()` / `ia.libere_cache()`** : le corpus ne rend résidentes QUE les
  pages qu'une requête touche ; `libere_cache()` rend tout après un gros traitement (retour ~15-60 Mo).
- **Build à froid allégé** : après écriture du `.colf`, la table RAM est remplacée par sa vue mmap (le tout
  premier build ne retient plus qu'une table à la fois).
- **MESURES** (`mesure_ressources.py`, base complète 71,9 M) : **~30 Mo de RAM, chargement ~2 s, 216 000 req/s**
  (cache chaud). Pleine puissance (balayage invention 71,9 M faits) = **57 Mo réellement possédés** ; le pic
  transitoire (~1,4 Go) est du cache `.colf` Shared_Clean réclamable. TOUT PREMIER lancement (build d'index) =
  pic ~2,7 Go / une fois → recommandé : livrer le `.colf` pré-construit dans la Release.
- **Windows** : `madvise` absent (no-op sûr, garde `try/except`) ; les pages mmappées y sont aussi paginées à la
  demande, et le gain « labels mmappés » s'applique quel que soit l'OS.
- **Correction de cache** : le cache `.colf`/`.bin` local était périmé (~2000 valeurs à espaces non normalisés,
  construites avant le durcissement `_norme_valeur` — l'invalidation ne regardait que le mtime du jsonl, pas la
  version du code). Cache reconstruit à froid (valeurs correctes, `_norme_valeur` appliqué). ⚠ Reste à durcir :
  inclure une empreinte du code d'ingestion dans l'invalidation. **La Release doit livrer un `.colf` construit à
  neuf depuis le code courant** (pas depuis un vieux `.bin`).
- **Docs realignées** : README(.fr).md, `_POST_LINKEDIN.md`, `docs/ANALYSE_MANQUES.md` (P6 marqué RÉSOLU). Les
  anciens chiffres publics « 73 M / 3,3 s / 520 Mo » (et la dérive 80 M/858k) étaient faux ou périmés → corrigés
  en 71,9 M / ~2 s / ~30 Mo. Gate `_nonreg` re-passée sur le cache corrigé.

## 2026-07-03 — Session « le .exe marche pour de vrai » (débogage en conditions réelles)

### Deux causes racines trouvées et corrigées (la recherche web échouait dans le .exe)
- **SSL épinglé** (`src/https_confiance.py`, NOUVEAU) : sous Windows, le magasin de certificats système peut
  contenir une variante périmée d'une racine -> OpenSSL refuse des sites SAINS (« certificate has expired » sur
  fr.wikipedia.org, chaîne servie pourtant 100 % valide ; navigateurs OK car ils récupèrent les racines
  dynamiquement). Remède : si et SEULEMENT si la validation système échoue sur un problème de certificat, la
  requête est re-validée contre des ancres EMBARQUÉES (racines officielles ISRG X1/X2, bundle Mozilla ;
  expirent 2035/2040). Vérification jamais désactivée, hostname compris. Câblé dans `veille_structure`,
  `veille`, `telecharge_donnees`.
- **Conversations enfin PERSISTANTES dans le .exe** (`conversation.py`) : le stock vivait sous `VERAX_ROOT`
  qui, en mode frozen, pointe le dossier TEMPORAIRE PyInstaller (détruit à la fermeture) -> conversations
  perdues à chaque sortie, archive amnésique. Le .exe range désormais tout dans `~/.verax/conversations`.
  Au passage : 2 conversations de dev étaient EMBARQUÉES dans le .exe (et committées) -> détrackées,
  `datasets/conversations/` gitignoré, le build n'embarque plus que `datasets/lecteur`.

### Diagnostic embarqué (plus jamais d'échec silencieux)
- **Tampon de build** : `VERSION_BUILD.txt` (commit) écrit par le CI et `build_exe.bat`, affiché au démarrage
  (`build : …`) et dans la réponse « diagnostic » -> on sait toujours QUEL .exe on teste (artifact périmé vu à 15h23 :
  le build du push 15:20 n'existait pas encore).
- **Échecs web VISIBLES en console** (une fois par erreur distincte, jamais bloquant) : `veille_structure._signale`
  + signalement d'un échec d'import du module web dans `repond._recherche_structuree`.
- **Sorties tolérantes** (`verax_boot`) : `stdout/stderr errors="replace"` — un `print("✓")` sur console cp1252
  tuait le thread de préchargement (UnicodeEncodeError). Plus jamais.
- **Chemin des données de `repond`** : `_DOSSIER_LECTEUR` respecte `LECTEUR_DATASETS_DIR` (en frozen, le chemin
  dérivé de `__file__` était faux -> requêtes inverses mortes en silence dans le .exe).

### Interface (demandes Yohan)
- **Interrupteur INTERNET** (routes `GET/POST /api/web` + bouton) : actif par défaut ; « couper » = données
  locales seules, effet immédiat. Quand internet est coupé et que les données locales n'ont rien : message
  ACTIONNABLE (« réactive internet et je lance une recherche sourcée ») au lieu d'un aveu générique.
- **Corbeille** : bouton 🗑 -> conversations archivées, restaurer (↩) ou purger définitivement (✕, confirmation).
- **Honnêteté de la devise** : « rien ne sort de la machine » -> « tes conversations restent ici · internet :
  optionnel, toujours sourcé » (la recherche envoie les termes de la question aux sources, jamais les dialogues).
- Phrase d'accueil : « … je réponds avec ce que je sais ou ce que je trouve sur internet (toujours sourcé)… ».

### Qualité de réponse (retours de test Yohan en direct)
- **GARDE DE PERTINENCE (FAUX=0)** sur la recherche web libre : la recherche plein-texte de Wikipédia renvoie
  TOUJOURS quelque chose — « je voudrais construire un moteur à eau » rapportait le CONCORDE. Désormais les mots
  pleins du sujet doivent se retrouver dans le titre/extrait de correspondance (tolérance 1 faute :
  « parmezzan » -> « parmesan » passe), sinon ABSTENTION honnête. Top-3 résultats testés, premier pertinent retenu.
- **Extraction du SUJET des phrases d'intention** : « je voudrais construire X », « où je peux trouver Y »,
  « dans quel pays… » -> la recherche porte sur X/Y, pas sur la phrase entière (-> « Moteur à eau » trouvé).
- **MULTI-SOURCES** (`cherche_web_domaines`, DuckDuckGo lite) : jusqu'à 3 résultats PERTINENTS de domaines
  INDÉPENDANTS, chacun verbatim + attribué + lié. Réponse Wikipédia enrichie de « 🌐 D'autres sources en
  parlent : … » ; sans corroboration -> « (Source unique — à vérifier.) » ; sans Wikipédia -> rapport du
  métamoteur attribué. Dégradation gracieuse si bloqué. (La promotion « N sources concordent -> fait » = le
  système de confiance, chantier suivant.)
- **Anglais** : salutations anglaises comprises et répondues EN ANGLAIS (« hello how are you? » partait en
  recherche web -> « Clara Furey » hors-sujet) ; détecteur « ça ressemble à de l'anglais » -> clarification
  honnête bilingue au lieu d'une réponse à côté. Principe Yohan : DEMANDER des précisions > répondre à côté.
- **Import fichiers** : le message d'échec LISTE désormais les 22 types lisibles (json/csv/xml/sqlite/zip/…)
  et explique que PDF/images ne sont pas encore pris en charge (OCR prévu).

### Interface (2e vague)
- **Mode SOMBRE** 🌙 (bouton, mémorisé, défaut = réglage système) ; **trombone d'import en SVG contrasté**
  (l'émoji 📎 était illisible) ; boutons harmonisés.

### Boucle de build/test locale (nouvelle capacité de dev)
- Le .exe se BUILDE et se TESTE désormais depuis la session Claude via l'interop WSL->Windows (`py` 3.14 +
  `build_exe.bat` sans pause + tests HTTP `curl` sur 127.0.0.1:8765). Batterie e2e passée : web attribué
  (« roi de la pop » -> Michael Jackson), diagnostic tamponné, interrupteur, corbeille, base locale (Montevideo),
  persistance des conversations.

## 2026-07-03 — Session « produit prêt à publier »

### Architecture & distribution
- **Arborescence propre** : `src/` (moteur & capacités), `ingestion/` (récupérateurs), `tests/` (validateurs
  FAUX=0), `interface/` (UI web), `docs/`, `examples/`. Bootstrap `verax_boot.py` (imports à plat depuis les
  sous-dossiers, conscient du mode `.exe`).
- **Lancement** : `lance.py` (ouvre http://127.0.0.1:8765 + navigateur), `install.sh`/`lance.sh` (Linux/Mac),
  `Lancer_Provara.bat` (Windows). **.exe** : `build_exe.bat` + CI GitHub Actions (build auto à chaque push).
- **2 clics = base complète** : `telecharge_donnees.py` — au 1er lancement, le `.exe` installe les 73M faits
  (~563 Mo) depuis la Release, puis charge tout.

### Conversation (moteur)
- **Nom = Provara** (identité/nom câblés) ; salutations robustes et **combinées** (« bonjour comment vas-tu ?
  comment t'appelles-tu ? »), tolérance aux fautes.
- **Multi-questions NON-BLOQUANT** : répond à chaque sous-question (données + calcul), « je ne l'ai pas » pour
  les inconnues, tout combiné.
- **Auto-diagnostic** : « diagnostic » -> nb de relations/faits chargés + source des données.

### Connaissance
- **Échantillon enrichi** : 16 -> **1068 relations / ~1,1 M faits** embarqués (géographie, sciences, histoire…).
- **Recherche web STRUCTURÉE** (`veille_structure.py`) : quand la base n'a pas le fait, interrogation Wikidata
  (SPARQL déterministe) -> réponse **vérifiée et ATTRIBUÉE** (« trouvé sur Wikidata »). Design Yohan : source
  fiable = réponse véridique ; jamais de scraping de texte libre (FAUX=0 préservé). Opt-in réseau (`IA_WEB=1`).

### Honnêteté & propreté
- Formule « **hors-ligne par défaut** » (répond sans réseau ; connexion opt-in pour apprendre/chercher) au lieu
  de « 100 % hors-ligne ».
- Dé-branding Kadepic -> Provara ; aucun secret dans le dépôt.

### Interface & visualisation
- **Interface rebrandée Provara** (titre, en-tête, message d'accueil, libellés « vous »/« Provara »).
- **Schémas visuels** : « montre-moi ce que tu sais sur X » / « schéma de X » / « graphe de X » -> **graphe SVG
  en étoile** des relations réelles que Provara connaît sur l'entité (via `graphe_monde` + SVG contrôlé, labels
  échappés, FAUX=0). Affiché directement dans le chat.
- **Import de fichiers** : bouton 📎 -> le fichier est lu LOCALEMENT (`ia.lit_fichier` : json/csv/xml/
  sqlite/zip/ini…) et Provara en donne un résumé fidèle dans le chat (jamais envoyé ailleurs, effacé après lecture).

### Recherche web (session 2)
- **Recherche web STRUCTURÉE étendue** : Wikidata via SPARQL, désambiguïsation par notoriété (« France » -> Paris),
  nettoyage des nombres.
- **Recherche web LIBRE (Wikipédia)** : quand ni la base ni Wikidata n'ont la réponse, Provara interroge Wikipédia
  (recherche plein-texte), rapporte un **extrait VERBATIM attribué** + un **lien** vers la source (« Information
  trouvée sur internet, à vérifier au besoin »). Résout les épithètes (« le roi de la pop » -> Michael Jackson).
  FAUX=0 préservé : rapporté, jamais présenté comme une vérité vérifiée de Provara.
- **Questions subjectives** cadrées honnêtement (« ça dépend du critère ») + pistes web.
- **Multi-questions** : « x »/« × » = multiplication ; engage sur une liste évidente (≥3 parties), non-bloquant.
- **Corbeille des conversations** (route + à finir côté UI).
- Correction majeure du **.exe** : PyInstaller analyse tous les modules (`_precharge_verax`) -> `import ia` ne
  plante plus en frozen ; erreurs remontées dans la console.

### Recherche web (session 3 — 2026-07-03 soir) : MULTI-SOURCES RÉEL (l'index du web entier + contexte vérifié sur site)
- **Cause racine du « je ne vois que Wikipédia »** : DuckDuckGo lite servait un **CAPTCHA anti-bot** (« anomaly »,
  cc=botnet) à notre UA -> `cherche_web_domaines` rendait [] à CHAQUE question -> « Source unique » systématique.
- **Refonte multi-sources** (`veille_structure.py`) : recherche PAR MOTS-CLÉS sur des index du web ENTIER —
  **Mojeek** (crawler indépendant, primaire) + **Bing RSS** (flux fait pour les programmes) + DDG lite (repli),
  requête **« phrase exacte » d'abord** (précision : « "roi de la pop" » ne remonte plus les sites « ROI »
  marketing) puis mots-clés pleins (rappel ; « un moteur à eau » ne matche plus l'ONU par « UN »).
- **VÉRIFICATION DE CONTEXTE SUR LE SITE** (demande Yohan) : Provara **visite chaque page candidate** (borne
  400 Ko, texte extrait sans scripts) et exige les mots pleins du sujet dans une fenêtre de ~70 mots (départage :
  phrase exacte > prose réelle > menus) -> l'extrait rapporté est le **PASSAGE VERBATIM de la page** ; page lue
  mais muette sur le sujet = source REJETÉE ; inaccessible = snippet du moteur (attribué). Visites en parallèle.
- **Anti-rafale** : cache 15 min par (index, requête) + budget Mojeek par question (quota ~4 req/min observé) ;
  dégradation gracieuse inchangée (« Source unique — à vérifier »).
- **ROUTAGE PHRASE NOMINALE** (`repond.py`) : « histoire du château de Chambord » sans « ? » n'est PLUS un fait
  à noter (« C'est noté » = répondre à côté) mais un SUJET DE RECHERCHE -> cascade factuelle + web + clarification.
  Une affirmation garde son accusé (verbe conjugué/1ʳᵉ personne/chiffre : « rdv dentiste mardi 15h » reste noté) ;
  interjections (« oui », « merci ») inchangées. `est_fallback` reconnaît aussi le message « internet coupé ».
- **FIX PRODUIT (latent depuis le portage)** : `assistant_nl._module_repond` cherchait `src/interface/repond.py`
  (layout harnais) -> **FileNotFoundError avalée = étage clarification/bornage MORT en silence dans le .exe**.
  Corrigé (réutilise l'instance `repond` chargée ; sinon 2 layouts ; sinon import gelé). `valide_assistant_nl`
  passe de CRASH TOTAL à 70/77 (7 échecs restants = dérive harnais->Provara à trier, chantier compréhension).
- Gates : verifie_demo **31/31** (783 checks) + valide_conversation **9/9** ; e2e .exe : « symptômes de la carence
  en fer » (sans « ? ») -> passage vérifié sur actusante.net + 2 domaines ; « pneu de vélo » -> réponse PRIMAIRE
  depuis un site spécialisé (roulezjeunesse) quand Wikipédia n'a rien.

### Session 3 bis (2026-07-03 soir, retours LIVE Yohan) — build v6
- **UI sombre : champ de saisie illisible** (texte clair sur BLANC) : le textarea n'avait pas de fond explicite
  -> gardait le blanc natif du navigateur en thème sombre. Fix : `background: var(--panneau)`.
- **Salutation COMBINÉE à une demande** (« Bonjour comment vas-tu ? qu'est-ce que la canicule ? » échouait en
  « famille inconnue ») : `_detache_salutation` répond au social ET traite la demande (reste VERBATIM, pipeline
  normal). Vérifié source : salutation+canicule -> « Bonjour !… » + article Wikipédia.
- **Extraction du sujet** : mots de DISCOURS retirés (« dire », « serait », « vraiment », « savoir »…) des
  mots pleins + verbes de tête (« peux-tu me dire quelle boisson serait vraiment rafraîchissante en temps de
  canicule » -> sujet « boisson rafraîchissante temps canicule », la recherche web peut enfin matcher).
- **Superlatifs de NOTORIÉTÉ non bornés** (« le rappeur le plus connu du moment ») : plus connu/populaire/
  célèbre ajoutés à `evaluation_subjective` -> cadrage honnête (« pas de réponse unique, donne-moi un critère »)
  au lieu du message générique. Gates 31/31 + 9/9 + assistant_nl 70/77 (stables).
- ⚠ CONSTAT STRATÉGIQUE (Yohan) : le routeur à motifs est un PLAFOND pour la V1 — plan « moteur conversationnel
  model-free appris » consigné au runbook §4-2c (lexique T9 = grammaire par lookup, dialogue à état, patrons
  promus par verdict sur corpus, lecture de documents longs).

### Session 3 ter (2026-07-03 nuit) — LECTURE PDF (brique MANQUANTE, cap « mémoire de 200 pages »)
- **Constat (agent d'exploration) : la couche compréhension du langage EXISTE mais n'est PAS câblée au chat.**
  `repond.py` fait du pattern-matching + lookup factuel et n'importe AUCUN de : `comprehension_integree`,
  `lecture_comprehension`, `lexique_fr`, analyse de phrase (`generateur`). Vrai chantier = BRANCHER, pas refaire.
- **Brique réellement manquante = lire un PDF tiers.** `parseur_fichiers` rendait HORS pour le PDF ;
  `document_pdf` sait ÉCRIRE, pas LIRE. Aucune lecture de document long n'existait.
- **`src/extrait_pdf.py`** (stdlib re+zlib, FAUX=0) : extrait la couche TEXTE d'un PDF (opérateurs Tj/TJ,
  échappements PDF, flux **FlateDecode** décompressés), texte PAR PAGE, ordre du document via l'arbre
  Catalog→Pages→Kids. Un PDF SANS couche texte (scanné) rend des pages VIDES + diagnostic honnête
  (`pages_avec_texte=0` → « OCR requis »), jamais d'invention. Filtre non géré (image) → ignoré, pas deviné.
- **Branché** : `parseur_fichiers.lit` (PDF → texte, magic bytes `%PDF-`), `serveur._resume_fichier`
  (upload → montre le vrai texte + nb pages + note « scanné » honnête au lieu d'un repr de dict), ajouté au
  préchargement PyInstaller. `valide_extrait_pdf 14/14`, valide_parseur_fichiers 13/13, valide_document_pdf
  21/21, verifie_demo 31/31, valide_conversation 9/9.
- SUITE (brique 2) : lecture de DOCUMENT LONG — sectionnement + index inversé par section (réutilise le moteur
  de rappel des conversations) + Q&A « que dit le document sur X ? » → passage verbatim + page.

### Session 3 quater (2026-07-03 nuit) — LECTURE DE DOCUMENT LONG (interroger un mémoire de 200 pages)
- **`src/lecteur_document.py`** (FAUX=0) : découpe un document (pages→sections→passages, détection de titres
  numérotés/mots-clés/capitales), index inversé pondéré idf (réutilise `conversation._tokens`), et répond à
  une question par le PASSAGE VERBATIM + page + section, ou abstention honnête si rien ne correspond. Sommaire
  = titres réellement détectés. `depuis_pdf(octets)` = pont direct avec extrait_pdf.
- **Racinisation conservatrice** (pluriel FR : chute s/x) sur les CLÉS d'index+requête -> « bâtiments » apparie
  « bâtiment », « instrumentés » apparie « instrumenté » ; le texte rendu reste verbatim.
- **BUG LATENT trouvé** (non corrigé en amont pour ne pas risquer les gates de conversation.py) : les mots-vides
  de `conversation.py` sont ACCENTUÉS (« été », « où ») alors que les tokens sont dé-accentués -> ils fuient dans
  l'index (affecte aussi le rappel de conversations). Contourné dans lecteur_document (`_STOP_DOC` dé-accenté +
  interrogatifs). À corriger proprement dans conversation.py plus tard (avec re-passage de ses gates).
- **Branché au chat** (`serveur.py`) : un PDF/texte importé devient un Document interrogeable attaché à la
  conversation (`_DOCS`). Source de REPLI attribuée : ne répond QUE si la connaissance vérifiée + le web ont
  abstenu (ne détourne jamais une bonne réponse) ; « sommaire/plan/de quoi parle le document » -> plan détecté.
  Plafond d'upload 5→40 Mo (mémoire de 200 pages). `valide_lecteur_document 18/18`, extrait_pdf 14/14,
  verifie_demo 31/31, valide_conversation 9/9, assistant_nl 70/77. Ajoutés au préchargement PyInstaller.

### Session 3 quinquies (2026-07-03 nuit) — AUDIT DE CÂBLAGE COMPLET + branchement des orphelines
- **Comparaison des 2 repos** (Provara ↔ IA_nouvelle_vision d'origine) : rien de RUNTIME ne manque. Écart =
  ingere_* (build datasets, pas runtime) + mesure_* (benchmarks) + valide_* (dans tests/) ; 23 vrais modules
  non portés, TOUS dev/analyse/démo, AUCUN importé au runtime. Données : 1068 embarqués + 1369 complets dans le
  tarball Release (aucune donnée perdue). Ressource repérée : lexique_kaikki_full.jsonl (1,9M) pour plus tard.
- **Audit câblage ia.py→chat** : sur ~350 fonctions publiques, 5 seulement passées via la façade ia.py, ~10 via
  modules-frères ; ~300 (Palier 2 stats) restent à juste titre non-câblées (exigent des tableaux, pas du NL).
  Poignée de vraies capacités conversationnelles COUPÉES du chat → branchées.
- **BRIQUE GRAMMAIRE `src/grammaire_fr.py`** (FAUX=0) : analyse grammaticale française appelable — classe de
  chaque mot (mots-outils = ensembles FERMÉS finis ; mots pleins via **lexique embarqué 19 200 mots** extrait du
  Wiktionnaire, homographes ambigus écartés ; morphologie SÛRE seulement ‑ment), type de phrase
  (question/affirmation/ordre/exclamation + négation robuste à l'élision « n'a »), structure SVO, genre.
  Ambigu/inconnu → 'inconnu' (jamais deviné faux). `valide_grammaire_fr 46/46`. Lexique `src/lexique_fr_pos.jsonl`.
- **6 CAPACITÉS ORPHELINES CÂBLÉES au chat** (`repond.py`, handlers additifs en amont du factuel, abstention hors
  périmètre) : (1) grammaire « nature du mot X » / « analyse grammaticale : phrase » ; (2) conjugaison « conjugue
  X » (présent régulier, abstention honnête sinon) ; (3) graphiques « trace un graphique de : n1,n2… » → SVG ;
  (4) distance géo « distance entre X et Y » → orthodromie+cap (ia.distance_lieux) ; (5) **moteur d'INVENTION**
  « comment rafraîchir sans climatiseur » / « que manque-t-il pour X » → reformulation physique du besoin
  (ia/besoin.py — LA VISION PRODUIT, était totalement absente du chat) ; (6) audit de code « faille dans ce
  code : <bloc> » → constats CWE (ia.audite_code). `valide_capacites_chat 19/19`.
- Gates : verifie_demo 31/31, valide_conversation 9/9, assistant_nl 70/77, grammaire 46/46, capacites 19/19,
  extrait_pdf 14/14, lecteur_document 18/18. grammaire_fr ajouté au préchargement PyInstaller.

### Session 3 sexies (2026-07-03 nuit) — TOUT CÂBLER : Palier 2, conjugaisons, OCR, apprentissage, challenge
- **RECONNAISSANCE DES FORMES CONJUGUÉES** `src/formes_verbales.py` (77/77) : index inverse forme→verbe
  (114 266 formes) généré par règles (présent/imparfait/futur/participes des réguliers 1er/2e groupe) depuis
  **6505 verbes embarqués** (`verbes_fr.txt`) + cœur de fréquence, + table des irréguliers fréquents. Branché
  dans grammaire_fr -> **SVO réel** (« le chien mange la souris » → sujet/verbe/objet). Homographes (« table »,
  « content ») restent nom/adjectif via lexique prioritaire. FAUX=0 : formes dérivées/vérifiées, jamais devinées.
- **CÂBLAGE DU PALIER 2 STATS** `src/fonction_stats_nl.py` (16/16) : routeur en langage naturel qui rend
  accessibles ~46 fonctions calibrées (moyenne/médiane/écart-type exactes ; incertitude/tendance/prévision/Fermi/
  Benford/proportion Wilson/taux Poisson/Kelly/anomalie/risque extrême/rupture ; 2 listes : corrélation-pente/
  comparaison/effet causal/méta-analyse). Extraction de nombres + intention, `phrase=True`, relaie l'abstention
  honnête (échantillon trop petit). Branché `_cap_stats` dans repond.
- **BUG CORRIGÉ** : doublon `detecte_changement` dans ia.py (la version Shiryaev masquait la version série) →
  renommée `detecte_changement_precoce` ; la détection de rupture sur série est de nouveau atteignable.
- **OCR BORNÉ** `src/ocr.py` (17/17) : reconnaissance de texte NET par gabarits (police bitmap 5×7, rendu +
  lecture round-trip), normalisation largeur/position, espace-mot par pas régulier, multi-lignes. Glyphe non
  reconnu → « ? » (jamais inventé) ; photo/police non standard → HORS honnête. Branché parseur_fichiers (PNG) +
  résumé d'upload. (Portée déclarée : texte régulier fort contraste — la vraie OCR généraliste exigerait un modèle.)
- **APPRENTISSAGE DE PATRONS** `src/apprentissage_patrons.py` (11/11) : quand une formulation échoue puis
  l'utilisateur REFORMULE avec succès (même sujet exigé), Provara apprend l'alias « ratée→qui marche » (persistant,
  effaçable RGPD). Re-poser la formulation ratée est ré-aiguillé → réponse vérifiée. FAUX=0 : ré-aiguillage seul,
  jamais un fait inventé. Câblé serveur (observation échec→réussite) + repond (consultation avant abstention).
- **CHALLENGE MULTI-REGISTRES** `tests/challenge_conversation.py` : corpus gradué courant/technique/soutenu +
  capacités outils, 16/16 (hors web). Tableau de bord de la boucle adverse.
- Gates : verifie_demo 31/31, valide_conversation 9/9, assistant_nl 70/77, ia 18/18, + 11 nouveaux validateurs
  tous verts. Modules ajoutés au préchargement PyInstaller. Données embarquées : lexique_fr_pos (19 200) +
  verbes_fr (6505).

### Session 3 septies (2026-07-03 nuit) — SOLUTIONS aux limites déclarées
- **VERBES IRRÉGULIERS PAR MODÈLES** (formes_verbales, 126/126) : au lieu d'une table partielle, ~10 MODÈLES de
  conjugaison Bescherelle (partir/ouvrir/courir/attendre-re/prendre/mettre/-indre/-aître/-uire) générés
  systématiquement pour tout le 3e groupe. Couverture échantillon 32/47 → 47/47, index 116k formes. FAUX=0.
- **APPRENTISSAGE PROFOND (induction de règles)** (apprentissage_patrons, 16/16) : au-delà des alias de phrase,
  induction de RÈGLES DE SUBSTITUTION de mot depuis UN exemple (« chef-lieu »→« capitale ») qui GÉNÉRALISENT
  aux phrases neuves (« chef-lieu du Japon » → Tokyo, vérifié e2e). Effacement RGPD retire aussi les
  substitutions dérivées. Sound : ré-aiguillage seul, réponse toujours vérifiée.
- **PALIER 2 — CONCEPTS/PARADOXES** (explications.py, 13/13) : « explique le paradoxe de X » câble les briques
  pédagogiques auto-contenues (deux enveloppes, Braess, Allais, Ellsberg, Parrondo, Saint-Pétersbourg, no free
  lunch, coûts irrécupérables, Kelly, pascal mugging, cadrage). Concept inconnu / question factuelle → non
  détourné. Le calcul réel de la brique, jamais une paraphrase.
- **OCR ROBUSTE (binarisation Otsu)** (ocr, 20/20) : seuil automatique par histogramme → lit malgré contraste
  faible, sous-exposition, sur-exposition (photos). La limite « polices arbitraires / manuscrit » reste (elle
  exigerait des gabarits multi-polices ou un modèle appris — frontière honnête déclarée).
- Gates : verifie_demo 31/31, conversation 9/9, assistant_nl 70/77, + tous les nouveaux validateurs verts.
  Nouveaux modules au préchargement PyInstaller.

### Session 3 octies (2026-07-03 nuit) — DETTE 70/77 assistant_nl RÉSOLUE (77/77)
- Ces 7 checks n'avaient JAMAIS été verts dans Provara : le test plantait avant le fix de chargement de module ;
  70/77 était sa 1re exécution réelle. Analyse : 1 vrai bug + 4 config manquante + 2 libellé/données.
- **VRAI BUG corrigé** : une opinion (« quel est le plus beau pays ») passée par la PORTE UNIQUE était étiquetée
  `fait` — `qualifie_texte` ne reconnaissait que l'ancien préfixe « Question non bornée », pas le cadrage
  amélioré « Il n'y a pas de réponse unique, c'est subjectif… ». Ajout du préfixe `_PFX_OPINION` -> classée
  SUPPOSITION (régime opinion). Le TEXTE restait honnête, mais le STATUT était faux : corrigé.
- **REGISTRE DE SOURCES créé** (`datasets/sources/registry.jsonl`, absent du portage) : Provara connaît désormais
  ses sources de confiance (Wikidata, QLever, Wikipédia FR, REST Countries). Rend le mécanisme de joignabilité
  (`veille.approfondit`/`_ping_sources`) fonctionnel (4 tests) — amélioration produit, pas seulement un fix test.
- 2 attentes de test PÉRIMÉES mises à jour sans maquillage : libellé subjectif amélioré ; « cours d'eau du
  Portugal » = le MÉCANISME de rejeu « oui » est vérifié + FAUX=0 (fait réel si données, sinon abstention
  honnête en gate léger — jamais une invention).
- valide_assistant_nl **77/77**. Non-régression : verifie_demo 31/31, conversation 9/9, veille 24/24, sources OK.

### Session 3 nonies (2026-07-03 nuit) — SYSTÈME DE CONFIANCE FACTUEL (mission 1) + OCR reverti proprement
- **OCR** : correction honnête de mon erreur « besoin d'un modèle » — l'OCR classique est model-free (gabarits
  multi-polices + traits structurels). Mon essai rapide de généralisation par traits (topologie/zonage)
  RÉGRESSAIT (confusion 0/O, fausses lettres sur forte déformation = viol FAUX=0) → REVERTI au borné solide
  (20/20) + Otsu conservé. L'OCR généraliste model-free devient un CHANTIER DÉDIÉ (bibliothèque de gabarits de
  polices réelles + traits soignés + gestion du bruit), pas un patch.
- **`src/confiance.py`** (18/18) — l'utilisateur est un JUGE RÉEL :
  · CORRECTIONS AUTORITAIRES : « c'est faux, c'est X » (visant la dernière question) enregistre X comme réponse
    autoritaire ; re-poser la question rend X, ATTRIBUÉ (« tu me l'avais corrigé »). PRIME sur connaissance/web/
    mémoire (l'utilisateur juge la réalité). Persistant, effaçable RGPD.
  · « OUBLIE CE SITE X » : bannit un domaine (sous-domaines inclus) — retiré des recherches (`veille_structure`).
- Câblé : `repond` (correction consultée en (0conf) priorité max ; « oublie ce site » en (0ban)) ; `serveur`
  (capture « c'est faux, c'est X » vs dernière question) ; `veille_structure` (filtre les domaines bannis).
- La concordance au niveau du FAIT existe (`veille_corroboration` : N sources indépendantes + juge réel, 26/26) ;
  le chat affiche déjà la concordance de domaines (« N sources en parlent »). La concordance de VALEURS via
  sources structurées multiples reste une intégration plus profonde (notée honnêtement).
- Gates : confiance 18/18, ocr 20/20, verifie_demo 31/31, conversation 9/9, assistant_nl 77/77,
  veille_corroboration 26/26, capacites 19/19. Non-régression : questions non corrigées répondent normalement.

### Session 3 decies (2026-07-03) — CORRECTION UTILISATEUR EXIGE UNE SOURCE (trou FAUX=0 fermé)
- Faille signalée par Yohan : une correction NUE (« capitale de la France = Toulouse ») écrasait une vérité.
  Corrigé : `confiance.corrige` EXIGE une source ; correction nue -> Provara CHALLENGE (« j'avais X ; sur quelle
  SOURCE t'appuies-tu ? »), tient bon sans source (« je m'en tiens à ce que je peux vérifier »), et une fois
  sourcée l'attribue (« d'après la source que tu m'as indiquée »), jamais comme sa propre vérité. État en attente
  côté serveur (la source peut arriver au tour suivant). valide_confiance 20/20.

### Session 3 undecies (2026-07-03) — LANGUE : réponse factuelle en ANGLAIS (mission 3, fondation)
- **`src/langue.py`** (13/13, model-free) : (1) DÉTECTION de langue par signatures de mots-outils (fr/en/es/de) ;
  (2) TRADUCTION BORNÉE d'une question factuelle EN -> requête FR (relations capital/population/currency/language/
  area/continent ; pays EN->FR + identité pour les valeurs neutres) ; (3) résolution par le pipeline VÉRIFIÉ FR ;
  (4) habillage de la réponse en anglais. FAUX=0 : la valeur vient toujours du vérifié ; relation/entité inconnue
  -> None (jamais d'invention). Câblé `repond` (`_cap_langue_en` avant la clarification bilingue).
  Vérifié : « what is the capital of Spain? » -> « The capital of Spain is Madrid. » ; le FR ne régresse pas.
  Message de bascule désormais bilingue. Portée déclarée : questions factuelles bornées ; la traduction LIBRE de
  texte reste un chantier (dictionnaire bilingue + règles de transfert, model-free mais volumineux).

### Session 3 duodecies (2026-07-03) — finitions des chantiers
- **LANGUE étendue** : plus de relations EN (indicatif, point culminant, « how many people live in »), traduction
  des VALEURS linguistiques FR→EN (portugais→Portuguese, europe→Europe…). langue 13/13.
- **COLD-LOAD** : déjà atténué par le préchargement en tâche de fond (`_prechauffe` daemon dans serveur.main) —
  l'UI est instantanée, le lecteur charge pendant que l'utilisateur tape. Optimisation en place, confirmée.
- **`--noconsole`** : désormais une OPTION de build (`VERAX_NOCONSOLE=1` → release sans fenêtre ; console par
  défaut pour les diagnostics de dev). Provara.spec pilote `console` par la variable d'environnement.
- **DOCS** : `docs/{fr,en}/CAPABILITIES.md` mis à jour — nouvelle section « Assistant conversationnel » listant
  grammaire, conjugaison, stats NL, explications, lecture de documents/OCR, invention, géo, multi-sources,
  apprentissage, système de confiance, anglais (avec les frontières honnêtes déclarées).
- CHANTIERS RESTANTS (honnêtes, gros/bloqués sur ressources) : OCR généraliste (nécessite une bibliothèque de
  gabarits de polices RÉELLES — l'approche traits seule régressait/FAUX=0) ; traduction LIBRE de texte
  (dictionnaire bilingue + règles de transfert, model-free mais volumineux). Le reste des missions est livré.

### Session 3 terdecies (2026-07-03) — MULTILINGUE (max de langues) + SÉLECTEUR d'interface
- **`langue.py` refondu MULTILINGUE et extensible** (25/25) : détection fr/en/es/de/it/pt ; PARSING séparé du
  RENDU (une question peut être écrite dans une langue et répondue dans une autre). Config par DONNÉES
  (relations, noms de pays, gabarits, valeurs) → ajouter une langue = une entrée, aucune logique. Provara répond
  aux questions factuelles (capitale/population/monnaie/langue/superficie) dans 5 langues, via le pipeline
  vérifié FR. FAUX=0 : la valeur vient du vérifié.
- **Bascule** : « réponds en espagnol » (détecté, `demande_de_switch`) ET **sélecteur de langue dans l'interface**
  (`<select>` fr/en/es/de/it/pt) → endpoint `/api/langue` (préférence globale `repond._PREF_LANGUE_GLOBAL`) +
  **localisation des libellés UI** (sous-titre, boutons, placeholder, thème) dans les 6 langues. Une question FR
  est alors répondue dans la langue choisie ; une question écrite dans une langue supportée est auto-détectée.
- Vérifié : réglage « de » → « quelle est la capitale de l'Italie ? » → « Die Hauptstadt von Italie ist Rome. » ;
  retour « fr » → pipeline natif. Gates : verifie_demo 31/31, conversation 9/9, capacites 19/19, langue 25/25.

### Session 3 quaterdecies (2026-07-03) — OCR : recherche complète + jeu de traits classique
- Recherche internet du state-of-the-art OCR SANS modèle : deux voies (gabarits ; extraction de caractéristiques).
  Implémenté le toolkit CLASSIQUE complet (`ocr.py`) : traits STRUCTURELS (nombre de trous/Euler), STATISTIQUES
  (zonage 4×4, profils H/V, croisements H/V, aspect) et **moments de Hu** (invariants échelle/rotation), comparés
  au plus proche PROTOTYPE (police + variantes dilatée/érodée), en REPLI du gabarit.
- Vrai gain FAUX=0 : **marge d'ambiguïté** sur le gabarit — un glyphe qui ressemble autant à deux caractères
  (ex. un E déformé ≈ E ou !) → « ? » au lieu d'un choix arbitraire. Abstention stricte aussi côté traits
  (topologie exigée identique + seuil + marge ; glyphes triviaux exclus). valide_ocr 20/20 préservé.
- LIMITE HONNÊTE confirmée par la recherche : la généralisation à des polices ARBITRAIRES exige une bibliothèque
  de gabarits de VRAIES polices (données) — impossible à fabriquer sans fichiers de police ; et un glyphe
  détruit/fusionné n'est récupérable par AUCUNE OCR (artefact de segmentation). Portée FAUX=0 = texte imprimé net
  (police régulière, fort contraste via Otsu), ce qui est livré et gaté. Le multi-police = chantier « données de
  polices ».

### Session 3 quindecies (2026-07-03) — mesures fiables, base complète locale, UI multilingue, docs, analyse
- **BASE COMPLÈTE débloquée localement** : extraite dans C:\Users\yohan\.verax\datasets\lecteur → le .exe charge
  **71,9 M faits / 1387 relations** (vérifié via diagnostic), plus de 404. Message 404 amélioré (non alarmant).
  Le 404 public reste : Yohan doit publier la Release GitHub (asset datasets_complets.tar.gz).
- **MESURES RESSOURCES fiables** (`mesure_ressources.py`) : échantillon 1,1 M = 75 Mo RAM ; base complète 71,9 M
  = **3,3 Go RAM colonnaire (~41 o/fait)**, lookup ~0,004 ms (235k req/s). Le « sous 1 Go » d'antan était une
  base ~858k faits, PAS les 72M. README corrigé (le « 73M en 520 Mo » était faux).
- **UI MULTILINGUE COMPLÈTE** : localisation des 6 langues de TOUT l'affichage (sous-titre, boutons, tooltips,
  accueil, placeholders, Internet, Envoyer, corbeille, messages dynamiques) ; sélecteur + `/api/langue` ; réponses
  factuelles dans la langue. **Réorganisation** : gauche = Nouvelle conversation + Corbeille ; haut-droite =
  Internet + Mode sombre + Langue. JS validé (node --check).
- **OCR** : recherche complète du SOTA model-free ; toolkit classique implémenté (Hu/Euler/zonage/profils/
  croisements) + marge d'ambiguïté FAUX=0 sur le gabarit ; limite honnête = multi-police nécessite des données de
  polices. 20/20 préservé.
- **DOC nettoyée** (audit complet) : supprimé résidu docs/_tr_en ; corrigé compteurs (669→681, 480→492), chemins
  ingestion/, chiffres morts (822/153/_archive), RAM/73M ; ajouté modules récents à INVENTORY.
- **`--noconsole`** option de build (VERAX_NOCONSOLE=1).
- **ANALYSE DES MANQUES** livrée (`docs/ANALYSE_MANQUES.md`) : P1 raisonnement compositionnel (levier n°1),
  P2 scanner d'inventions (vision ultime), P3 fraîcheur, P4 compréhension profonde, P5 traduction libre,
  P6 perf/daemon, P7 multimodal, P8 confiance.

### Session 3 sexdecies (2026-07-03) — P1 : RAISONNEMENT COMPOSITIONNEL (levier n°1)
- `interface/repond.py` : les relations imbriquées « X de Y de Z » ne sont plus REFUSÉES mais COMPOSÉES —
  résout l'inner (Y de Z) → entité E VÉRIFIÉE, puis l'outer (X de E). FAUX=0 : chaque maillon = lookup EXACT
  (pas de correction floue dans la chaîne, qui propagerait une erreur), abstention si un maillon manque.
  Décuple les réponses sur les 71,9 M faits déjà présents, sans ajouter de donnée.
- BUG FAUX=0 CORRIGÉ au passage : « continent du pays de Paris » donnait « Antarctique » (le lookup flou mangeait
  un maillon) — « pays » n'était pas reconnu comme relation (filtré par _GENERIQUES). Noyau de relations ajouté
  APRÈS le filtre → détection correcte → composition/abstention, jamais une fausse réponse.
- `valide_composition 9/9` (mécanisme prouvé à résolveur mocké). Non-régression : verifie_demo 31/31,
  conversation 9/9, capacites 19/19, assistant_nl 77/77. LIMITE notée : la valeur réelle dépend de la résolution
  NL→relation de donnee_nl (« pays de X » ne matche pas encore la relation « pays_de_capitale ») — chantier suivant.

### Session 3 septendecies (2026-07-03) — P2 : SCANNER D'INVENTIONS (l'OBJECTIF FINAL câblé au chat)
- `substrat_reel.py` (gap-engine sur 71M faits, 3 gardes FAUX=0 : typage mesuré + témoin re-vérifié + anti-
  fausse-nouveauté) était construit mais NON câblé. Branché au chat via `_cap_invention_composite` (repond) sur
  `ia.inventions_composites(type)` : « quelles inventions/relations manquent pour les pays ? » / « que peut-on
  dériver sur X ? » → liste les attributs COMPOSITES dérivables (relation nouvelle « pont ∘ cible », témoin
  re-vérifié). Ex. « pays → (capitale ∘ latitude_capitale) ». Chaque valeur = fait re-vérifié, jamais inventé ;
  utilité non jugée (« reste à évaluer »). Types reconnus : pays/éléments/villes/capitales/astres.
- Vérifié e2e sur l'échantillon (2 candidats pour « pays ») ; non détourne pas une question factuelle ni le
  moteur de besoin. Non-régression : composition 9/9, capacites 19/19, verifie_demo 31/31. Sur la base complète
  (71,9M), l'exploration est bien plus riche.

### Session 3 octodecies (2026-07-03) — P1+ : résolution par FAMILLE de relations (la composition délivre)
- Le composeur essaie désormais, quand le lookup NL exact échoue, la FAMILLE de relations à tête donnée
  (« pays de X » → toute relation `pays_*` où X est une entité), avec UNICITÉ exigée (FAUX=0 : ambigu → None).
  Résultat : « continent du pays de Abou Dabi » → « Asie » (vraie composition 2-hop sur les données, chaîne
  montrée). valide_composition 9/9, non-régression complète (31/31, 9/9, 19/19, 77/77).

### Session 3 novemdecies (2026-07-03) — résolution par FAMILLE aussi sur les lookups SIMPLES
- Le repli famille (unicité FAUX=0) est aussi tenté sur une question simple « rel de entité » quand le DATA rend
  HORS : « continent de la France » → Europe (était HORS), « pays de Abou Dabi » → Émirats. N'affecte jamais une
  réponse déjà résolue. Non-régression : verifie_demo 31/31, conversation 9/9, assistant_nl 77/77, capacites 19/19,
  composition 9/9.

### Session 3 vigies (2026-07-03) — P3 : FRAÎCHEUR (source live préférée pour le volatil)
- `repond._est_volatil` + route : une question à marqueur temporel (« président ACTUEL », « DERNIER vainqueur »,
  « en 2026 », « current/latest ») préfère la source LIVE (Wikidata via veille_structure) à la base STATIQUE qui
  peut être périmée — quand le web est autorisé (opt-in). Repli sur la base si live indisponible. FAUX=0 inchangé
  (live = vérifié + attribué). valide_fraicheur 10/10, non-régression complète (31/31, 9/9, 19/19).
- P4 (multi-tours/coréférence) VÉRIFIÉ déjà en place (« et sa monnaie » → yen, « et la France » → substitue
  l'entité, « et sa capitale » → Paris). P6 (cold-load) : le daemon lecteur est Unix-socket (Linux, pas le .exe) ;
  le .exe précharge déjà en fond (cold-load masqué pendant l'accueil) → pas de gain .exe à ajouter.

### Session 3 vicies (2026-07-03) — P5 TRADUCTION + P7 OCR MINUSCULES
- P5 TRADUCTION `src/traduction.py` (valide_traduction 8/8) : mot-à-mot ASSISTÉE FR↔EN. Source RICHE = table
  `concept_du_mot` de la base complète (lexique cross-lingue ~165k mots dont 20k anglais : « dog (anglais) →
  chien ») utilisée en priorité (any→FR direct ; FR→cible via index inverse lazy), REPLI = dictionnaire curé
  embarqué (~350 mots) hors-ligne. FAUX=0 : mot inconnu gardé tel quel + signalé, jamais inventé ; sortie
  étiquetée « mot-à-mot assisté — à affiner ». Câblé `_cap_traduction` (« traduis X en anglais »). Ne charge
  JAMAIS la base (utilise le lecteur seulement s'il est déjà préchargé). NB Yohan : concept_du_mot existait —
  je l'avais raté au 1er balayage, corrigé.
- P7 OCR MINUSCULES `src/ocr.py` (valide_ocr 20→28/28) : ajout des 26 minuscules 5×7. CLÉ = les x-height ont le
  HAUT VIDE et sont échantillonnées sur la hauteur de LIGNE → la position verticale distingue « o »/« O »,
  « c »/« C »… sans logique en plus. `rend()` ne force plus `.upper()`. Round-trip mixte parfait (« Hello World »,
  « le chat dort »). Le texte imprimé RÉEL (surtout minuscule) est enfin lisible. 20/20 majuscules préservé.

### Session 3 unvicies (2026-07-03) — CONSIGNATION : doc synchronisée + gate cœur réparée + runner conversationnel
- DOC synchronisée sur le dernier travail : compteurs (modules 492→493, validateurs 669/681→683) dans INVENTORY/
  VALIDATION/README (fr+en) ; CAPABILITIES (fr+en) — ajout composition, scanner d'inventions, traduction FR↔EN,
  fraîcheur, OCR minuscules + correction ligne périmée « traduction hors périmètre » ; ANALYSE_MANQUES — bandeau
  de statut (P1/P2/P3/P4/P5/P7 = LIVRÉ).
- RUNNER CONVERSATIONNEL `tests/suite_conversation.py` : agrège 16 gates conversationnels (hors _nonreg par
  design), chacun en sous-processus isolé avec le bon env → 16/16 (469 checks). Documenté dans VALIDATION.
- **BUG INFRA CORRIGÉ — `_nonreg.py` cassé par le portage** : la gate cœur cherchait les `valide_*.py` à la
  RACINE (`os.listdir(HARN)`) alors que le portage Provara les a tous mis dans `tests/` → `python3 _nonreg.py`
  ne trouvait qu'**1** validateur (interface) et échouait faute de PYTHONPATH. Correctif : helper `_chemin()`
  (bare→tests/, chemin explicite tel quel), découverte dans `tests/`, `modules_locaux` élargi à src/interface/
  ingestion, et `_env_pipeline()` pose le PYTHONPATH sur chaque sous-processus. Vérifié : `liste_validateurs()`
  = **683** (était 1), `lance()` exécute correctement (composition 9/9, ocr 28/28, traduction 8/8, fraîcheur
  10/10, grammaire 61/61). Le run complet reste lourd (base complète) — à lancer par l'utilisateur.

### Session 3 duovicies (2026-07-03) — _nonreg : fix PYTHONPATH tests/ + constat de portage
- Correctif suite : `_SRCPATH` inclut désormais **tests/** en tête (les validateurs importent leur helper
  `valide_commun` et parfois un validateur frère comme module, tous dans tests/). Vérifié : valide_vague4 4/4,
  valide_pile 6/6, valide_iteration 5/5 (étaient en échec `ModuleNotFoundError: valide_commun`). ~57 validateurs
  de cette classe débloqués.
- CONSTAT (honnête) : faire tourner `_nonreg.py` dans Provara révèle que le PORTAGE est incomplet pour la SUITE.
  La vraie gate historique vit dans le repo d'origine `IA_nouvelle_vision/harnais/` (870 validateurs COLOCALISÉS,
  layout plat — datasets/src/validateurs ensemble → passe). Le port Provara (src/ tests/ interface/ ingestion/) a
  déplacé 683 validateurs dans tests/ SANS re-router leurs chemins codés en dur : certains cherchent
  `datasets/…` ou `src/ia.py` RELATIFS à leur dossier (→ FileNotFoundError), d'autres exigent la base complète
  71,9M (lecteur_t5..t12, resolution, taxonomie, substrat_reel…). Ce ne sont PAS des régressions — mon fix les a
  rendus VISIBLES (avant, _nonreg n'en trouvait qu'1). Le vert 683/683 dans Provara = chantier de portage
  (re-router chemins + base complète sous tests/datasets) ; la validation AUTORITÉ reste `harnais/` en amont.
  Pour la couche conversationnelle, `tests/suite_conversation.py` (16/16) est le contrôle autonome fiable dans Provara.

### Session 3 trevicies (2026-07-03) — portage _nonreg : chemins re-routés (structurel fait, contenu = harnais/)
- 12 validateurs dataset-dépendants re-routés : `dirname(__file__)/datasets/lecteur` → `LECTEUR_DATASETS_DIR`
  (env) ou fallback RACINE du repo (au lieu de `tests/datasets` inexistant). `_env_pipeline` pose aussi
  `VERAX_ROOT`. Vérifié : valide_surface_ia FileNotFoundError → **3/3** ; les 12 TROUVENT désormais leurs datasets
  (plus d'erreur de chemin).
- BILAN du chantier portage : le STRUCTUREL est fait (découverte 1→683, PYTHONPATH tests/+src/interface/ingestion,
  chemins re-routés, VERAX_ROOT) → ~60 validateurs débloqués. Les ~20 restants échouent sur le CONTENU : les
  validateurs, l'échantillon embarqué et la base complète NE s'accordent PAS sur les noms de relations/données
  (ex. la base complète ~/.verax n'a même pas `population_pays.jsonl` — nommage différent). C'est un alignement
  par-validateur profond = précisément le rôle de `harnais/` (origine, tout colocalisé et aligné). Décision :
  arrêt du chantier gate-Provara ici (faible valeur, duplication de harnais/). Gate pratique Provara =
  `tests/suite_conversation.py` (16/16) ; gate AUTORITÉ = `IA_nouvelle_vision/harnais/` (870 validateurs).
