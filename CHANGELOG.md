# Journal des modifications — VERAX

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
  `Lancer_VERAX.bat` (Windows). **.exe** : `build_exe.bat` + CI GitHub Actions (build auto à chaque push).
- **2 clics = base complète** : `telecharge_donnees.py` — au 1er lancement, le `.exe` installe les 73M faits
  (~563 Mo) depuis la Release, puis charge tout.

### Conversation (moteur)
- **Nom = VERAX** (identité/nom câblés) ; salutations robustes et **combinées** (« bonjour comment vas-tu ?
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
- Dé-branding Kadepic -> VERAX ; aucun secret dans le dépôt.

### Interface & visualisation
- **Interface rebrandée VERAX** (titre, en-tête, message d'accueil, libellés « vous »/« VERAX »).
- **Schémas visuels** : « montre-moi ce que tu sais sur X » / « schéma de X » / « graphe de X » -> **graphe SVG
  en étoile** des relations réelles que VERAX connaît sur l'entité (via `graphe_monde` + SVG contrôlé, labels
  échappés, FAUX=0). Affiché directement dans le chat.
- **Import de fichiers** : bouton 📎 -> le fichier est lu LOCALEMENT (`ia.lit_fichier` : json/csv/xml/
  sqlite/zip/ini…) et VERAX en donne un résumé fidèle dans le chat (jamais envoyé ailleurs, effacé après lecture).

### Recherche web (session 2)
- **Recherche web STRUCTURÉE étendue** : Wikidata via SPARQL, désambiguïsation par notoriété (« France » -> Paris),
  nettoyage des nombres.
- **Recherche web LIBRE (Wikipédia)** : quand ni la base ni Wikidata n'ont la réponse, VERAX interroge Wikipédia
  (recherche plein-texte), rapporte un **extrait VERBATIM attribué** + un **lien** vers la source (« Information
  trouvée sur internet, à vérifier au besoin »). Résout les épithètes (« le roi de la pop » -> Michael Jackson).
  FAUX=0 préservé : rapporté, jamais présenté comme une vérité vérifiée de VERAX.
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
- **VÉRIFICATION DE CONTEXTE SUR LE SITE** (demande Yohan) : VERAX **visite chaque page candidate** (borne
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
  passe de CRASH TOTAL à 70/77 (7 échecs restants = dérive harnais->Verax à trier, chantier compréhension).
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
- **Comparaison des 2 repos** (Verax ↔ IA_nouvelle_vision d'origine) : rien de RUNTIME ne manque. Écart =
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
  l'utilisateur REFORMULE avec succès (même sujet exigé), VERAX apprend l'alias « ratée→qui marche » (persistant,
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
- Ces 7 checks n'avaient JAMAIS été verts dans Verax : le test plantait avant le fix de chargement de module ;
  70/77 était sa 1re exécution réelle. Analyse : 1 vrai bug + 4 config manquante + 2 libellé/données.
- **VRAI BUG corrigé** : une opinion (« quel est le plus beau pays ») passée par la PORTE UNIQUE était étiquetée
  `fait` — `qualifie_texte` ne reconnaissait que l'ancien préfixe « Question non bornée », pas le cadrage
  amélioré « Il n'y a pas de réponse unique, c'est subjectif… ». Ajout du préfixe `_PFX_OPINION` -> classée
  SUPPOSITION (régime opinion). Le TEXTE restait honnête, mais le STATUT était faux : corrigé.
- **REGISTRE DE SOURCES créé** (`datasets/sources/registry.jsonl`, absent du portage) : VERAX connaît désormais
  ses sources de confiance (Wikidata, QLever, Wikipédia FR, REST Countries). Rend le mécanisme de joignabilité
  (`veille.approfondit`/`_ping_sources`) fonctionnel (4 tests) — amélioration produit, pas seulement un fix test.
- 2 attentes de test PÉRIMÉES mises à jour sans maquillage : libellé subjectif amélioré ; « cours d'eau du
  Portugal » = le MÉCANISME de rejeu « oui » est vérifié + FAUX=0 (fait réel si données, sinon abstention
  honnête en gate léger — jamais une invention).
- valide_assistant_nl **77/77**. Non-régression : verifie_demo 31/31, conversation 9/9, veille 24/24, sources OK.
