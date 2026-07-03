<p align="right"><strong>🇫🇷 Français</strong> · <a href="README.md">🇬🇧 English</a></p>

<div align="center">

# VERAX

### L'IA qui n'invente jamais. Ou elle sait — avec preuve — ou elle le dit.

**73 M de faits · chargés en 3,3 s · 520 Mo de RAM · 0 GPU · 0 dépendance · Python 3.10+**

</div>

---

VERAX est une intelligence artificielle **souveraine** construite sur une règle unique et non négociable : **elle n'affirme jamais quelque chose qu'elle ne peut prouver.** Là où un grand modèle de langage répond avec assurance — et se trompe parfois sans le savoir — VERAX répond avec sa **source**, **calcule** exactement, ou **s'abstient honnêtement**. Jamais elle n'hallucine.

Elle tourne **sans GPU et sans dépendance**, sur un ordinateur portable ordinaire, et **répond hors-ligne, sans aucun cloud**. Sa base de connaissances complète — 73 millions de faits — se charge en 3,3 secondes et tient dans 520 Mo de mémoire. Elle est écrite entièrement en **Python de la bibliothèque standard**, sans une seule bibliothèque tierce. Elle ne se connecte que si tu l'y autorises : pour **apprendre** (ingérer de nouvelles données) ou **chercher sur ses sources de confiance** (opt-in).

## En 30 secondes

```bash
git clone https://github.com/Verax-IA/Verax.git
cd Verax
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

## Ce qui rend VERAX différent

| | |
|---|---|
| **Zéro hallucination (FAUX=0)** | Toute affirmation vient d'un fait vérifié ou d'un calcul réellement évalué. Au moindre doute : abstention. C'est un invariant imposé par **669 tests de non-régression** qui échouent si un seul fait faux entre. |
| **Il sait ce qu'il ne sait pas (bornage)** | VERAX distingue ce que la réalité **tranche** (→ un FAIT, avec source) de ce qu'elle **ne tranche pas** (→ une SUPPOSITION cadrée, jamais servie comme un fait). Cette frontière calibrée est le cœur du système. |
| **Souverain, frugal, sans GPU** | 73 M faits en 520 Mo, 0 dépendance, aucun cloud requis pour répondre. Déployable là où un LLM est impensable : poste isolé, embarqué, secteur souverain — pour un coût d'exploitation quasi nul. Elle ne se connecte que sur demande, pour apprendre ou chercher sur ses sources de confiance. |
| **Mémoire non-éphémère** | Il retient les échanges par conversation et sait rappeler le bon élément — mais le rappelé reste **typé « rapporté »**, jamais promu en fait. |
| **Il apprend en allant chercher** | VERAX ne dépend pas de données livrées : il **ingère lui-même** depuis des sources réelles et vérifie chaque fait avant de l'accepter. Voir « Regarde-le apprendre » ci-dessous. |

> **Honnêteté sur la portée** — VERAX **couvre moins de sujets** qu'un LLM généraliste : c'est le prix, assumé, du zéro-hallucination. Sa promesse n'est pas « il répond à tout », c'est « **il n'est jamais faussement sûr** ». Sur ce qu'il couvre, il ne se trompe pas ; sur le reste, il le dit.

## Regarde-le apprendre

La base complète n'est **pas livrée** dans ce dépôt — non par contrainte, mais par principe : VERAX **va chercher ses données et les apprend lui-même**. Chaque script `ingere_*.py` récupère un domaine depuis une source réelle et fiable (Wikidata via le miroir QLever, la Banque mondiale, un dictionnaire multilingue…), **vérifie** chaque fait, et n'écrit que ce qui survit — jamais un fait non corroboré.

```bash
python3 ingere_worldbank.py     # va chercher les indicateurs éco chez la Banque mondiale
python3 ingere_elements_ptjson.py   # ingère les 118 éléments chimiques
# … puis VERAX répond sur ces domaines, hors-ligne, avec source
```

> ⚠️ **La phase d'ingestion a besoin du réseau** (elle télécharge depuis les sources). C'est une **construction en ligne, une seule fois**. Répondre depuis la base ne demande alors aucun réseau (chercher sur ses sources de confiance reste un opt-in, désactivé par défaut). Reconstruire l'intégralité des 73 M faits prend plusieurs heures ; commencez par un domaine borné (éco, chimie) pour voir la boucle d'apprentissage en action.

## Installation

**Prérequis** — c'est tout :

- **Python 3.10 ou supérieur** (`python3 --version`)
- **Aucune** bibliothèque tierce. Pas de `pip install`. Pas d'environnement virtuel obligatoire. Pas de GPU, pas de CUDA.
- Système : Linux, macOS, ou Windows (WSL recommandé sous Windows).

**Pour la démo et l'usage sur l'échantillon** : rien de plus, `python3 demo_verax.py`.

**Pour la base complète** : lancer les scripts `ingere_*.py` (réseau requis, une fois) — voir « Regarde-le apprendre ».

## Vérifier soi-même (FAUX=0 n'est pas un slogan)

La discipline zéro-hallucination est **prouvée par le code**, pas affirmée. Le dépôt contient **669 validateurs** (`valide_*.py`) qui testent chaque capacité contre des ancres externes ; la moindre régression fait échouer la porte :

```bash
python3 verifie_demo.py          # prêt à l'emploi : 30 validateurs moteurs, 773 checks, ~8 s, sans données
python3 _nonreg.py --jobs 8      # gate complet : 669/669 (nécessite la base reconstruite)
```

> `verifie_demo.py` lance les validateurs des moteurs de calcul (chimie, physique, géométrie, calibration, façade `ia.py`…) qui n'ont besoin d'aucune donnée externe — il prouve FAUX=0 sur un clone frais. Le gate complet `_nonreg.py` valide en plus les faits ingérés et nécessite la base reconstruite.

## Architecture (vue d'ensemble)

VERAX est un assemblage de **modules atomiques**, chacun avec sa propre garantie et son propre validateur, à frontières étanches :

- **Le lecteur** (`lecteur.py`) — le magasin de faits vérifiés : lookup-ou-abstention, stockage colonnaire compact (73 M faits en 520 Mo).
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
<sub>VERAX — construit atome par atome, chaque brique validée contre la réalité.<br>
« Une invention est une supposition qui a survécu à la réalité. »</sub>
</div>
