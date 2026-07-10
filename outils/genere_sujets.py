#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""GÉNÉRATEUR DE LA CARTE DES SUJETS (mandat Yohan 2026-07-10 : « cartographier réellement tout ce qui existe,
séparer traités/non traités, dépasser largement 10 000 — voire 50 000 — sujets, et pas seulement Wikidata »).

DEUX SORTIES :
  1. `SUJETS_BORNE_OU_NON.md` (COMMITTÉ, lisible, ~1 700 sujets) : les PARTIES conceptuelles rédigées à la
     main (`outils/parties_a.md`, `parties_b.md`) + l'ANNEXE T des taxonomies NORMALISÉES hors-Wikidata
     (Dewey, ISCO-08 — sources : ILO, OCLC) + l'ANNEXE S dérivée du STORE (une table vérifiée = un sujet).
  2. `SUJETS_ANNEXES_AUTO.md` (GÉNÉRÉ, gitignoré, ~85 000 sujets) : le produit cartésien
     MÉTIERS RÉELS × AXES ATOMIQUES et DOMAINES RÉELS × AXES. Frugalité (esprit fusée) : 9 Mo de texte
     DÉRIVABLE ne vivent pas dans git — le générateur, lui, est committé et déterministe.

FAUX=0 : les métiers/domaines ne sont pas inventés, ils sont LUS du store réel (`occupation_personne`,
`domaine_travail`) ; chaque AXE porte un code de bornage justifié UNE fois (« tour de main tacite » = MIX,
« ce métier est-il fait pour moi » = NB-SUBJ, jamais un B- forcé). Les libellés impropres au format
(« :: » interne) sont ÉCARTÉS, jamais tordus.
"""
from __future__ import annotations

import collections
import json
import os
import sys

_ICI = os.path.dirname(os.path.abspath(__file__))
_RACINE = os.path.dirname(_ICI)
_STORE = os.environ.get("LECTEUR_DATASETS_DIR",
                        os.path.join(os.path.expanduser("~"), ".verax", "datasets", "lecteur"))

# Support minimal d'un métier/domaine pour entrer dans la carte (1 = tout ce que le store atteste).
SUPPORT_MIN = int(os.environ.get("SUJETS_SUPPORT_MIN", "1"))

# ── LES AXES : ce qui « entoure chaque métier » (mandat Yohan). Code de bornage JUSTIFIÉ par axe. ──
AXES_METIER = (
    ("définition et périmètre du métier", "B-CONV", "nomenclature d'emploi publiée (ISCO-08, ROME, registres)"),
    ("gestes et savoir-faire techniques", "MIX", "gestes codifiés bornés ; le tour de main tacite ne se transmet "
                                                 "pas par texte"),
    ("outils, machines et logiciels", "B-FAIT", "matériel et logiciels attestés"),
    ("normes, réglementation et certifications", "B-CONV", "textes et référentiels publiés"),
    ("risques professionnels et prévention", "B-FAIT", "tables de risques et obligations publiées"),
    ("formation, diplômes et voies d'accès", "B-FAIT", "référentiels de formation publiés"),
    ("rémunération médiane (pays et année donnés)", "B-FAIT", "statistiques publiques"),
    ("« ce métier est-il fait pour moi ? »", "NB-SUBJ", "préférence personnelle : l'utilisateur est la seule source"),
)
AXES_DOMAINE = (
    ("résultats établis du domaine", "B-FAIT", "littérature et mesures attestées"),
    ("questions ouvertes du domaine", "NB-OUV", "bornées en principe, accès manquant"),
)

# ── ANNEXE T : taxonomies NORMALISÉES (hors Wikidata). Seulement ce qui est CERTAIN (au doute : écarté). ──
DEWEY = (("000", "Généralités, informatique, information"), ("100", "Philosophie et psychologie"),
         ("200", "Religion"), ("300", "Sciences sociales"), ("400", "Langues"),
         ("500", "Sciences de la nature et mathématiques"), ("600", "Technologie (sciences appliquées)"),
         ("700", "Arts et loisirs"), ("800", "Littérature"), ("900", "Histoire et géographie"))
DEWEY_500 = (("500", "Sciences naturelles"), ("510", "Mathématiques"), ("520", "Astronomie"),
             ("530", "Physique"), ("540", "Chimie"), ("550", "Sciences de la Terre"),
             ("560", "Paléontologie"), ("570", "Sciences de la vie"), ("580", "Botanique"), ("590", "Zoologie"))
ISCO_MAJEURS = (("0", "Forces armées"), ("1", "Directeurs, cadres de direction et gérants"),
                ("2", "Professions intellectuelles et scientifiques"),
                ("3", "Professions intermédiaires"), ("4", "Employés de type administratif"),
                ("5", "Personnel des services directs aux particuliers, commerçants et vendeurs"),
                ("6", "Agriculteurs et ouvriers qualifiés de l'agriculture, de la sylviculture et de la pêche"),
                ("7", "Métiers qualifiés de l'industrie et de l'artisanat"),
                ("8", "Conducteurs d'installations et de machines, et ouvriers de l'assemblage"),
                ("9", "Professions élémentaires"))


def _valeurs(table: str) -> collections.Counter:
    """Les valeurs distinctes d'une table du store, avec leur support (lecture en flux, stdlib pure)."""
    c: collections.Counter = collections.Counter()
    chemin = os.path.join(_STORE, table + ".jsonl")
    with open(chemin, encoding="utf-8") as f:
        for ligne in f:
            if ligne.startswith('{"_relation"'):
                continue
            try:
                c[json.loads(ligne)["valeur"]] += 1
            except (ValueError, KeyError):
                continue
    return c


def _entites(table: str) -> set:
    """Les ENTITÉS d'une table du store (les clés). Lève si la table manque : mieux vaut ne rien régénérer
    qu'écrire une carte fausse."""
    chemin = os.path.join(_STORE, table + ".jsonl")
    if not os.path.exists(chemin):
        raise SystemExit(
            "ERREUR : table « %s » absente du store (%s).\n"
            "La liste des métiers se filtre par LOOKUP dans cet oracle. Sans lui, l'ANNEXE M compterait des\n"
            "non-métiers (noms de famille, énumérations jointes par ingere_celebres) comme sujets à traiter :\n"
            "une MESURE FAUSSE. Ingère-le d'abord :\n"
            "    PYTHONPATH=src:ingestion python3 ingestion/ingere_metiers_attestes.py" % (table, _STORE))
    out = set()
    with open(chemin, encoding="utf-8") as f:
        for ligne in f:
            if ligne.startswith('{"_relation"'):
                continue
            try:
                out.add(json.loads(ligne)["entite"])
            except (ValueError, KeyError):
                continue
    return out


def _propre(libelle: str) -> bool:
    """Un libellé utilisable : non vide, sans « :: » (séparateur du format), longueur raisonnable."""
    return bool(libelle) and "::" not in libelle and 2 <= len(libelle) <= 90 and "\n" not in libelle


def metiers_de_la_carte() -> tuple:
    """(métiers, taille de l'oracle, nombre de valeurs écartées).

    Une valeur de `occupation_personne` n'est PAS un métier du seul fait d'y figurer. Le filtre est un
    LOOKUP dans `est_metier`, jamais une heuristique de chaîne : « Employés de réception, guichetiers et
    assimilés » est UN libellé CITP, alors que « acteur ou actrice, basketteur ou basketteuse et athlète
    professionnel » est une énumération fabriquée. Aucune règle sur la virgule ne les sépare ; la source, si.
    """
    atteste = _entites("est_metier")
    bruts = sorted(m for m, n in _valeurs("occupation_personne").items()
                   if n >= SUPPORT_MIN and _propre(m))
    metiers = [m for m in bruts if m in atteste]
    return metiers, len(atteste), len(bruts) - len(metiers)


def _entete() -> str:
    return """# SUJETS BORNÉ OU NON — carte des sujets et de leur bornage

> **RECONSTRUCTION + EXTENSION 2026-07-10** (l'original vivait à la racine du projet harnais, absent de ce
> disque). Mandat Yohan : « cartographier réellement tout ce qui existe, séparer ceux qui sont traités de ceux
> qui ne le sont pas, et parmi les traités : complets ou non ; à terme dépasser largement 10 000 sujets — et
> si on prend les métiers et tout ce qui les entoure, bien plus ; pas seulement Wikidata ; il n'y a pas de
> limites. »
>
> **CE FICHIER** = les parties CONCEPTUELLES (rédigées, jugement de bornage assumé) + l'ANNEXE T
> (taxonomies normalisées HORS-Wikidata : Dewey/OCLC, ISCO-08/OIT) + l'ANNEXE S (une table vérifiée du store
> = un sujet borné DE FAIT ; ancrage audité à 100 %).
> **`SUJETS_ANNEXES_AUTO.md`** (généré par `outils/genere_sujets.py`, gitignoré car dérivable) porte les
> dizaines de milliers de sujets MÉTIERS × AXES et DOMAINES × AXES, lus du store réel.
>
> **À VALIDER / CORRIGER PAR YOHAN** : les codes de bornage engagent un jugement. Au doute, le code prudent
> a été choisi (NB-INDEC / MIX plutôt qu'un B- forcé). `src/couverture_borne.py` mesure — jamais ne déclare —
> ce qui est TRAITÉ, PARTIEL ou NON TRAITÉ, et produit le backlog des vagues suivantes.

Légende des codes (héritée, cf. `src/sujets.py`) :
  B-NEC   — borné par NÉCESSITÉ (logique/mathématiques : la réponse découle des définitions)
  B-PHY   — borné par la PHYSIQUE (lois et mécanismes mesurables, rejouables)
  B-FAIT  — borné par les FAITS enregistrés (vérifiables dans une source)
  B-CONV  — borné par CONVENTION humaine figée (orthographe, unités, normes, codes)
  NB-OUV  — borné EN PRINCIPE, accès manquant (science ouverte)
  NB-SUBJ — non borné : subjectif (goûts, préférences)
  NB-SPEC — non borné : spéculatif (futur contingent)
  NB-NORM — non borné : normatif (morale, politique, esthétique)
  NB-INDEC— non borné : indécidable en l'état
  MIX     — part bornée + part non bornée (les séparer dans la réponse)

"""


def _annexe_t() -> str:
    lignes = ["# ANNEXE T — TAXONOMIES NORMALISÉES (hors Wikidata : OCLC/Dewey, OIT/ISCO-08)",
              "## T.1 — Classes principales de la Classification décimale de Dewey (OCLC)"]
    for code, nom in DEWEY:
        lignes.append("  - classe Dewey %s — %s :: B-CONV → classification publiée (OCLC)" % (code, nom))
    lignes.append("## T.2 — Divisions Dewey des sciences (500)")
    for code, nom in DEWEY_500:
        lignes.append("  - division Dewey %s — %s :: B-CONV → classification publiée (OCLC)" % (code, nom))
    lignes.append("## T.3 — Grands groupes professionnels ISCO-08 (Organisation internationale du travail)")
    for code, nom in ISCO_MAJEURS:
        lignes.append("  - grand groupe ISCO-08 %s — %s :: B-CONV → nomenclature publiée (OIT)" % (code, nom))
    lignes.append("## T.4 — Structures de classification citées (périmètre déclaré, contenu non énuméré ici)")
    for nom, src in (("Mathematics Subject Classification MSC2020 (63 classes à 2 chiffres)", "AMS/zbMATH"),
                     ("ACM Computing Classification System", "ACM"),
                     ("Classification internationale des maladies CIM-11", "OMS"),
                     ("Nomenclature statistique des activités NACE", "Eurostat"),
                     ("Répertoire opérationnel des métiers et des emplois ROME", "France Travail")):
        lignes.append("  - structure de classification : %s :: B-CONV → publiée (%s) ; contenu à ingérer" % (nom, src))
    return "\n".join(lignes) + "\n\n"


def _annexe_s(tables) -> str:
    lignes = ["# ANNEXE S — SUJETS DÉRIVÉS DU STORE RÉEL (%d tables vérifiées)" % len(tables),
              "## S.1 — Chaque relation vérifiée du lecteur est un sujet borné DE FAIT",
              "## (couverture d'ancrage prouvée : audit_ancres 1371/1371, valide_ancres_types)"]
    for t in tables:
        lignes.append("  - donnée du store : %s :: B-FAIT → table vérifiée du lecteur (ancrage audité)" % t)
    return "\n".join(lignes) + "\n"


def _annexes_auto(metiers, domaines) -> str:
    lignes = ["# SUJETS — ANNEXES AUTO (généré par outils/genere_sujets.py ; NE PAS ÉDITER À LA MAIN)",
              "",
              "> Dérivé du STORE RÉEL : les métiers viennent de `occupation_personne`, les domaines de",
              "> `domaine_travail` — aucun n'est inventé. Chaque AXE porte un code de bornage justifié une fois",
              "> (cf. AXES_METIER / AXES_DOMAINE dans le générateur). Fichier gitignoré : dérivable, régénérable.",
              "",
              "# ANNEXE M — MÉTIERS RÉELS × AXES ATOMIQUES (%d métiers × %d axes)" % (len(metiers), len(AXES_METIER)),
              "## M.1 — « tout ce qui entoure chaque métier » (mandat Yohan)"]
    for m in metiers:
        for axe, code, raison in AXES_METIER:
            lignes.append("  - %s — %s :: %s → %s" % (m, axe, code, raison))
    lignes.append("")
    lignes.append("# ANNEXE D — DOMAINES D'ACTIVITÉ RÉELS × AXES (%d domaines × %d axes)"
                  % (len(domaines), len(AXES_DOMAINE)))
    lignes.append("## D.1 — domaines lus de `domaine_travail`")
    for d in domaines:
        for axe, code, raison in AXES_DOMAINE:
            lignes.append("  - domaine « %s » — %s :: %s → %s" % (d, axe, code, raison))
    return "\n".join(lignes) + "\n"


def main() -> int:
    if not os.path.isdir(_STORE):
        print("ERREUR : store introuvable (%s). Exporte LECTEUR_DATASETS_DIR." % _STORE, file=sys.stderr)
        return 2
    tables = sorted(f[:-6] for f in os.listdir(_STORE) if f.endswith(".jsonl"))
    # ORACLE DE MÉTIER (correctif de MESURE, 2026-07-12). Une valeur de `occupation_personne` n'est pas un
    # métier du seul fait d'y figurer : la table contient des noms de famille (« Abogado »), des objets
    # (« Anime ») et des ÉNUMÉRATIONS fabriquées par `ingere_celebres` (« physicien, professeur d'université
    # et philosophe » — le fait est vrai, mais ce n'est pas UN métier). Aucun d'eux ne peut jamais être
    # traité : ni définition, ni gestes, ni risques professionnels n'existent pour un nom de famille. Les
    # compter comme sujets fabriquait un backlog inépuisable. On filtre par LOOKUP dans `est_metier`.
    #
    # L'oracle est défini sur les libellés FRANÇAIS, et c'est délibéré : la carte est française. Mesuré,
    # accepter aussi les libellés anglais ne rattrape que 6 libellés sur 2 636 — dont « Mann » (Q2552697,
    # constructeur anglais de camions, rangé sous « profession » par conflation Wikidata), tandis que
    # « magistrate », « general manager » et « credit manager » sont DÉJÀ dans l'oracle sous leur nom
    # français. Élargir à l'anglais réimporterait le bruit d'entreprises pour ne gagner aucun métier réel.
    metiers, n_atteste, ecartes = metiers_de_la_carte()
    domaines = sorted(d for d, n in _valeurs("domaine_travail").items()
                      if n >= SUPPORT_MIN and _propre(d))

    doc = _entete()
    for frag in ("parties_a.md", "parties_b.md"):
        with open(os.path.join(_ICI, frag), encoding="utf-8") as f:
            doc += f.read().rstrip("\n") + "\n\n"
    doc += _annexe_t() + _annexe_s(tables)
    with open(os.path.join(_RACINE, "SUJETS_BORNE_OU_NON.md"), "w", encoding="utf-8") as f:
        f.write(doc)

    auto = _annexes_auto(metiers, domaines)
    with open(os.path.join(_RACINE, "SUJETS_ANNEXES_AUTO.md"), "w", encoding="utf-8") as f:
        f.write(auto)

    n_auto = len(metiers) * len(AXES_METIER) + len(domaines) * len(AXES_DOMAINE)
    print("SUJETS_BORNE_OU_NON.md : parties conceptuelles + %d tables (annexe S) + annexe T" % len(tables))
    print("SUJETS_ANNEXES_AUTO.md : %d métiers × %d axes + %d domaines × %d axes = %d sujets"
          % (len(metiers), len(AXES_METIER), len(domaines), len(AXES_DOMAINE), n_auto))
    print("  oracle `est_metier` : %d libellés attestés ; %d valeurs de P106 ÉCARTÉES (non-métiers : noms "
          "de famille, objets, énumérations jointes) — elles ne sont PAS des sujets." % (n_atteste, ecartes))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
