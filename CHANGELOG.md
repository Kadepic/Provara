# Journal des modifications — VERAX

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
