<p align="right"><strong>🇫🇷 Français</strong> · <a href="README.md">🇬🇧 English</a></p>

<div align="center">

# Provara

### L'IA qui n'invente jamais. Ou elle sait — avec preuve — ou elle le dit.

**~1,1 M faits embarqués · base complète 72 M en un téléchargement · 0 GPU · 0 dépendance · Python 3.10+**

</div>

---

Provara est une intelligence artificielle **souveraine** construite sur une règle unique et non négociable : **elle n'affirme jamais quelque chose qu'elle ne peut prouver.** Là où un grand modèle de langage répond avec assurance — et se trompe parfois sans le savoir — Provara répond avec sa **source**, **calcule** exactement, ou **s'abstient honnêtement**. Jamais elle n'hallucine.

Elle tourne **sans GPU et sans dépendance**, sur un ordinateur portable ordinaire, et **répond hors-ligne, sans aucun cloud**. Sa base de connaissances complète — près de 72 millions de faits — se charge en environ 2 secondes et tient dans ~30 Mo de mémoire (le corpus est mémoire-mappé : les pages ne deviennent résidentes qu'à la demande). Elle est écrite entièrement en **Python de la bibliothèque standard**, sans une seule bibliothèque tierce. Elle ne se connecte que si tu l'y autorises : pour **apprendre** (ingérer de nouvelles données) ou **chercher sur ses sources de confiance** (opt-in).

## En 30 secondes

```bash
git clone https://github.com/Provara-IA/Provara.git
cd Provara
python3 demo_verax.py        # aucune installation, aucun réseau, aucun GPU
```

La démo tourne sur l'**échantillon** livré (16 domaines de faits) plus les moteurs de calcul, qui n'ont besoin d'aucune donnée. Extrait de ce qu'elle montre :

```
« Quelle est la capitale du Japon ? »       ✔ FAIT          Tokyo
« Quel est le numéro atomique du fer ? »    ✔ FAIT          26
  masse molaire du glucose C₆H₁₂O₆         = 180.156   (moteur, zéro donnée)
  distance Tokyo → Paris (grand cercle)    = 9712 km   (calculée)

« Population de la ville de Wakanda ? »      ∅ ABSTENTION    « je m'abstiens plutôt que deviner »
« Quel est le plus beau pays du monde ? »    ≈ SUPPOSITION   « la réalité ne fixe pas de réponse unique »
```

## Ce qui rend Provara différent

| | |
|---|---|
| **Zéro hallucination (FAUX=0)** | Toute affirmation vient d'un fait vérifié ou d'un calcul réellement évalué. Au moindre doute : abstention. C'est un invariant imposé par **683 tests de non-régression** qui échouent si un seul fait faux entre. |
| **Il sait ce qu'il ne sait pas (bornage)** | Provara distingue ce que la réalité **tranche** (→ un FAIT, avec source) de ce qu'elle **ne tranche pas** (→ une SUPPOSITION cadrée, jamais servie comme un fait). Cette frontière calibrée est le cœur du système. |
| **Souverain, frugal, sans GPU** | la base complète ~72 M faits tient dans ~30 Mo de RAM (colonnaire, mémoire-mappée, paginée à la demande ; ~1,7 Go sur disque), 0 dépendance, aucun cloud requis pour répondre. Déployable là où un LLM est impensable : poste isolé, embarqué, secteur souverain — pour un coût d'exploitation quasi nul. Elle ne se connecte que sur demande, pour apprendre ou chercher sur ses sources de confiance. |
| **Mémoire non-éphémère** | Il retient les échanges par conversation et sait rappeler le bon élément — mais le rappelé reste **typé « rapporté »**, jamais promu en fait. |
| **Il apprend en allant chercher** | Provara ne dépend pas de données livrées : il **ingère lui-même** depuis des sources réelles et vérifie chaque fait avant de l'accepter. Voir « Regarde-le apprendre » ci-dessous. |

> **Honnêteté sur la portée** — Provara **couvre moins de sujets** qu'un LLM généraliste : c'est le prix, assumé, du zéro-hallucination. Sa promesse n'est pas « il répond à tout », c'est « **il n'est jamais faussement sûr** ». Sur ce qu'il couvre, il ne se trompe pas ; sur le reste, il le dit.

## En conversation

Provara n'est pas qu'une base de faits : c'est un assistant local complet, qui ne ment jamais.

- **Il raisonne — il ne se contente pas de retrouver** — « un chat est-il un mammifère ? » → *Oui — chat → mammifère* ; « sur quel continent est Abuja ? » → *Afrique* (**déduit** : Abuja est la capitale du Nigéria, qui est en Afrique) ; « Phobos fait-il partie du système solaire ? » → la machine **découvre** que « orbiter » est transitive (et rejette la symétrie), puis l'**applique avec preuve**. Un fait non stocké devient connu — et prouvé.
- **Il compte et classe — exactement** — « combien de pays en Afrique ? » → un décompte **exact** ; « les 5 pays les plus peuplés d'Afrique » → un tri exact avec les valeurs. Là où un LLM devine, Provara **compte**.
- **Il définit et développe** — « c'est quoi le paludisme ? » → la définition vérifiée ; « parle-moi du Nigéria » / « explique-moi le Japon » → une **fiche développée** (capitale, population avec le **rang calculé** « le plus peuplé d'Afrique », monnaie).
- **Il te comprend malgré les fautes et l'argot** — « commen vas-tu » → compris (correction orthographe + **phonétique**) ; « combien gagne un toubib » → il comprend *médecin* (**paraphrase**, réseau JeuxDeMots).
- **Il sait dire qui l'a créé** — « qui t'a créé ? » → Yohan Fauck, avec ses liens.
- **Il cherche sur le web quand il ne sait pas** (opt-in) — d'abord une source structurée fiable (Wikidata) pour un **fait vérifié** ; sinon un extrait **attribué** de Wikipédia avec le **lien** (« d'après Wikipédia…, à vérifier au besoin »). Jamais présenté comme sa propre vérité. *(« le roi de la pop » → Michael Jackson ; « qui a inventé la dynamite ? » → Alfred Nobel, 1866.)*
- **Il dessine ce qu'il sait** — « montre-moi ce que tu sais sur la France » → un **schéma** (graphe) de ses relations réelles.
- **Il lit tes fichiers** — un fichier (JSON, CSV, XML, SQLite, ZIP…) → un résumé fidèle, **lu localement**, jamais envoyé ailleurs.
- **Il répond à plusieurs questions d'un coup** — « capitale du Japon, 5×9, et qui a inventé la dynamite ? » sans blocage.
- **Il se souvient** — mémoire par conversation, rappel du bon élément, toujours typé « rapporté ».
- **Il te salue** — présente-toi (« je m'appelle Yohan ») et il répond socialement, par ton prénom — jamais de recherche web sur ton nom.

## Regarde-le apprendre

La base complète n'est **pas livrée** dans ce dépôt — non par contrainte, mais par principe : Provara **va chercher ses données et les apprend lui-même**. Chaque script `ingere_*.py` récupère un domaine depuis une source réelle et fiable (Wikidata via le miroir QLever, la Banque mondiale, un dictionnaire multilingue…), **vérifie** chaque fait, et n'écrit que ce qui survit — jamais un fait non corroboré.

```bash
python3 ingestion/ingere_worldbank.py     # va chercher les indicateurs éco chez la Banque mondiale
python3 ingestion/ingere_elements_ptjson.py   # ingère les 118 éléments chimiques
# … puis Provara répond sur ces domaines, hors-ligne, avec source
```

> ⚠️ **La phase d'ingestion a besoin du réseau** (elle télécharge depuis les sources). C'est une **construction en ligne, une seule fois**. Répondre depuis la base ne demande alors aucun réseau (chercher sur ses sources de confiance reste un opt-in, désactivé par défaut). Reconstruire l'intégralité des 72 M faits prend plusieurs heures ; commencez par un domaine borné (éco, chimie) pour voir la boucle d'apprentissage en action.

## Installation & lancement

**Prérequis** — c'est tout : **Python 3.10+**, aucune bibliothèque tierce, pas de `pip install`, pas de GPU. (Linux, macOS ou Windows.)

**Windows** — télécharge `Provara.exe` depuis la page [Releases](https://github.com/Provara-IA/Provara/releases) et **double-clique dessus**. Aucun Python, aucune installation. Il s'ouvre dans ton navigateur et fonctionne **tout de suite** sur un **échantillon** embarqué (~1 M de faits) — sans attente. Pour débloquer la **base complète de 72 M de faits**, clique sur **« Base complète »** dans l'interface : un téléchargement **unique** (environ **6 Go d'espace disque libre**, **15 à 20 minutes**) que tu peux aussi ignorer. Une fenêtre de chargement t'informe en continu ; l'application tourne en mode **fenêtré** (pas de fenêtre console) et propose un bouton **Quitter**. *(Depuis les sources à la place : double-clique `Lancer_Provara.bat`, qui nécessite Python installé.)*

**Linux / macOS** — depuis les sources :

```bash
./install.sh        # vérifie Python + lance l'auto-test
python3 lance.py     # ou ./lance.sh
```

Dans les deux cas, Provara s'ouvre sur **http://127.0.0.1:8765** — localhost uniquement, tes données ne quittent jamais la machine.

- **Juste la démo** (sans serveur) : `python3 demo_verax.py`
- **Base complète** : lancer les scripts `ingestion/ingere_*.py` une fois (réseau requis) — voir « Regarde-le apprendre ».

**Organisation** — `src/` le moteur et les capacités · `ingestion/` les récupérateurs de données · `tests/` les validateurs FAUX=0 · `interface/` l'UI web locale · `docs/` la documentation · `examples/` les preuves autonomes.

## Vérifier soi-même (FAUX=0 n'est pas un slogan)

La discipline zéro-hallucination est **prouvée par le code**, pas affirmée. Le dépôt contient **683 validateurs** (`valide_*.py`) qui testent chaque capacité contre des ancres externes ; la moindre régression fait échouer la porte :

```bash
python3 verifie_demo.py          # prêt à l'emploi : 31 validateurs moteurs, 783 checks, sans données
python3 _nonreg.py --jobs 8      # gate complet : 683/683 (nécessite la base reconstruite)
```

> `verifie_demo.py` lance les validateurs des moteurs de calcul (chimie, physique, géométrie, calibration, façade `ia.py`…) qui n'ont besoin d'aucune donnée externe — il prouve FAUX=0 sur un clone frais. Le gate complet `_nonreg.py` valide en plus les faits ingérés et nécessite la base reconstruite.

## Architecture (vue d'ensemble)

Provara est un assemblage de **modules atomiques**, chacun avec sa propre garantie et son propre validateur, à frontières étanches :

- **Le lecteur** (`lecteur.py`) — le magasin de faits vérifiés : lookup-ou-abstention, stockage colonnaire compact, mémoire-mappé et paginé à la demande (labels compris) : la base ~72 M faits tient dans ~30 Mo de RAM (~1,7 Go sur disque) ; les pages ne deviennent résidentes que lorsqu'une requête les touche, et `libere_cache()` les rend ensuite.
- **Le gardien de bornage** (`classifieur_bornage.py`) — route chaque question : borné → fait / non-borné → supposition cadrée / indécidable → question de clarification.
- **La porte conversationnelle** (`assistant_nl.py`) — comprend en langage naturel, répond depuis le vérifié, calcule, ou pose une question ; ne devine jamais.
- **Les moteurs de calcul** — chimie, physique (constantes CODATA), navigation (orthodromie), arithmétique, conjugaison, conversions… : exacts, sans aucune donnée.
- **L'ingestion** (`ingere_*.py` + `veille_corroboration.py`) — récupère depuis des sources réelles, corrobore, n'écrit que le vérifié.
- **La calibration de l'incertitude** — en domaine ouvert, quantifie ce qu'il ne sait pas plutôt que de bluffer.
- **Le chemin interactif rapide** (`lecteur_daemon.py` + `lecteur_client.py`) — un daemon résident optionnel sert le lecteur sur une socket locale, pour que l'interface réponde en millisecondes sans recharger la base. Opt-in : éteint, le comportement est identique (zéro régression).

Voir [`examples/`](examples/) pour des preuves autonomes (raisonnement agnostique à la langue, un juge polyglotte sur plusieurs langages de programmation).

📖 *Documentation complète de tous les sous-systèmes : voir [`docs/`](docs/).*

## Licence

Code sous licence **MIT** (voir [`LICENSE`](LICENSE)). Les faits ingérés proviennent de sources ouvertes (Wikidata est CC0 ; vérifiez les conditions propres à chaque source avant redistribution des données).

---

<div align="center">
<sub>Provara — construit atome par atome, chaque brique validée contre la réalité.<br>
« Une invention est une supposition qui a survécu à la réalité. »</sub>
</div>
