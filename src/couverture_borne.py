# -*- coding: utf-8 -*-
"""COUVERTURE DES SUJETS — le compagnon de `sujets.py` (RECONSTRUIT 2026-07-10, mandat Yohan : « cartographier
réellement tout ce qui existe, séparer ceux qui sont traités de ceux qui ne le sont pas, et parmi les traités :
complets ou non »).

MESURÉ, JAMAIS DÉCLARÉ — c'est tout le principe : un sujet n'est TRAITÉ que si sa PREUVE existe RÉELLEMENT
dans le produit, et la preuve est vérifiée sur le disque à chaque appel :
  • ("gate", f)   -> `tests/f` existe ;
  • ("module", m) -> `src/m.py` existe ;
  • ("roue", nom) -> `nom` est une roue câblée de `pont_grandeurs._ROUES` ;
  • ("store",)    -> le sujet EST une table vérifiée du lecteur (annexe S ; ancrage audité à 100 %) ;
  • ("routage",)  -> sujet NON BORNÉ pris honnêtement par le repli intent-aware + gardes G1-G9 (jamais une
                    réponse inventée : router honnêtement EST le traitement correct du non-borné).
Une preuve DÉCLARÉE mais introuvable rend le sujet NON TRAITÉ et le dit (auto-détection de la dette : c'est
ainsi que `valide_jeux.py` inexistant a été débusqué à l'écriture).

TROIS ÉTATS : TRAITÉ · PARTIEL (mécanisme générique, périmètre incomplet CONNU) · NON TRAITÉ (= le BACKLOG).
`rapport()` est la liste de travail des vagues suivantes — l'équivalent mesuré du « 254/690 » d'origine.
"""
from __future__ import annotations

import os
import re

import sujets as _S

_ICI = os.path.dirname(os.path.abspath(__file__))
_TESTS = os.path.join(os.path.dirname(_ICI), "tests")
# FROZEN (.exe) : les `tests/` ne sont PAS embarqués — une preuve-gate n'y est donc pas VÉRIFIABLE. Ce n'est
# pas une dette (la gate `valide_sujets` la vérifie EN SOURCE à chaque suite) : on le DIT au lieu de le
# masquer ou de mentir (vécu e2e 2026-07-10 : le .exe annonçait « 69 dettes » qui n'existaient pas).
_GEL = bool(getattr(__import__("sys"), "frozen", False)) and not os.path.isdir(_TESTS)

TRAITE, PARTIEL, NON_TRAITE = "TRAITÉ", "PARTIEL", "NON TRAITÉ"

# ── PREUVES des sujets CONCEPTUELS (carte fermée, étendue vague par vague ; 1er motif qui matche gagne) ──
_REGLES: tuple = (
    (r"raisonnement propositionnel|syllogisme|logiques? modale|logique temporelle|logique trivalu",
     "gate", "valide_logique.py", TRAITE),
    (r"satisfiabilité d'un système|cohérence d'un petit système", "module", "contrainte", PARTIEL),
    (r"calcul arithmétique|primalité|PGCD|factorisation|divisibilité|congruence|irrationalité",
     "gate", "valide_fonction.py", TRAITE),
    (r"identités remarquables|équation du 1er degré|équation du 2nd degré|systèmes linéaires|"
     r"déterminant, rang|algèbre de Boole", "gate", "valide_algebre_calcul.py", PARTIEL),
    (r"dérivée|primitive/intégrale|développement limité|convergence d'une série|"
     r"équations différentielles linéaires", "module", "algebre_calcul", PARTIEL),
    (r"périmètres, aires|Pythagore|géométrie analytique|géométrie vectorielle", "gate", "valide_fonction.py", TRAITE),
    (r"trigonométrie", "module", "fonction_nl", PARTIEL),
    (r"dénombrement combinatoire|probabilité d'un événement|espérance, variance|théorème de Bayes",
     "module", "bayes", PARTIEL),
    (r"statistiques descriptives", "gate", "valide_fonction_stats_nl.py", TRAITE),
    (r"test d'hypothèse|intervalle de confiance", "module", "conformal", PARTIEL),
    (r"inférence causale|paradoxe de Simpson", "module", "causalite", PARTIEL),
    (r"biais de sélection", "module", "biais_survie", PARTIEL),
    (r"complexité d'un algorithme|complexité et coût", "module", "algo_analyse", PARTIEL),
    (r"comportement d'un code exécutable|correction d'un programme", "gate", "valide_capacites_chat.py", TRAITE),
    (r"vulnérabilités canoniques", "gate", "valide_audit_code.py", TRAITE),
    (r"grammaires formelles et automates", "module", "automates", PARTIEL),
    # physique : les roues (preuve = câblage réel dans _ROUES)
    (r"cinématique moyenne", "roue", "cinématique moyenne", TRAITE),
    (r"dynamique newtonienne", "roue", "force (Newton)", TRAITE),
    (r"poids et pesanteur", "roue", "poids", TRAITE),
    (r"travail et puissance mécanique", "roue", "travail", TRAITE),
    (r"énergie cinétique et potentielle", "roue", "énergie cinétique", TRAITE),
    (r"quantité de mouvement", "roue", "quantité de mouvement", TRAITE),
    (r"moment de force", "roue", "moment de force", TRAITE),
    (r"masse volumique|pression = force|conservation du débit|volume écoulé",
     "roue", "masse volumique", TRAITE),
    (r"loi d'Ohm|puissance et énergie électriques", "roue", "électrique", TRAITE),
    (r"autonomie d'une batterie", "roue", "autonomie", TRAITE),
    (r"énergie d'une batterie", "roue", "batterie", TRAITE),
    (r"équivalence masse-énergie", "roue", "énergie de masse", TRAITE),
    (r"consommation de carburant", "roue", "consommation carburant", TRAITE),
    (r"production d'une centrale", "roue", "énergie", TRAITE),
    (r"problème de rencontre", "gate", "valide_cinematique_nl.py", TRAITE),
    (r"échangeur : DTLM|DTLM et surface", "gate", "valide_pont_grandeurs.py", TRAITE),
    (r"rendement de Carnot|COP d'une pompe|loi des gaz parfaits|loi de Coulomb|"
     r"décroissance radioactive|énergie d'un photon|relation v = λ", "module", "physique", TRAITE),
    (r"cohérence thermodynamique|mouvement perpétuel", "module", "coherence_physique", TRAITE),
    (r"premier principe|second principe et entropie", "module", "coherence_physique", PARTIEL),
    (r"masse molaire|stœchiométrie|équilibrage d'une équation chimique|pH d'une concentration",
     "module", "chimie", TRAITE),
    (r"aérodynamique", "module", "aerodynamique", PARTIEL),
    (r"dimensionnement d'une structure", "module", "architecture", PARTIEL),
    # faits : les gates du lecteur
    (r"taxonomie \(|caractéristiques d'une espèce|statut de conservation", "gate", "valide_lecteur_t4.py", TRAITE),
    (r"relief, sommets|fleuves, longueurs|superficies des terres|coordonnées d'un lieu|"
     r"population, natalité|géographie", "gate", "valide_lecteur.py", TRAITE),
    (r"distances orthodromiques", "gate", "valide_coordonnees.py", TRAITE),
    (r"astronomie descriptive|structure interne de la Terre|composition de l'atmosphère",
     "gate", "valide_ancres_types.py", TRAITE),
    (r"mécanique céleste|datation radiométrique", "module", "physique", PARTIEL),
    (r"datation d'un événement|chronologie et successions|dirigeants par pays|régime politique|"
     r"résultats d'élections passées", "gate", "valide_lecteur_t8.py", TRAITE),
    (r"biographies", "gate", "valide_lecteur_t6.py", TRAITE),
    (r"auteur, compositeur|année de création d'une œuvre|dimensions, durée, support",
     "gate", "valide_lecteur_t5.py", TRAITE),
    (r"résultats sportifs|records du monde", "gate", "valide_lecteur_t10.py", TRAITE),
    (r"doctrines et textes|généalogies mythologiques|écoles philosophiques",
     "gate", "valide_lecteur_t12.py", TRAITE),
    (r"orthographe|conjugaison|accord du participe|genre grammatical|grammaire et accords",
     "gate", "valide_grammaire_fr.py", TRAITE),
    (r"sens lexical|synonymes|étymologie", "gate", "valide_lecteur_t9.py", TRAITE),
    (r"traduction d'un mot|traduction de mots", "gate", "valide_traduction.py", TRAITE),
    (r"conversions d'unités|unités du système international|heure et date locales",
     "gate", "valide_capacites_chat.py", TRAITE),
    (r"météo observée", "gate", "valide_capacites_chat.py", TRAITE),
    (r"codes normalisés|classe Dewey|division Dewey", "module", "bibliotheconomie", PARTIEL),
    (r"grand groupe ISCO|structure de classification", "aucun", None, NON_TRAITE),
    (r"règles d'un jeu institué|coup optimal", "gate", "valide_strategie_jeux.py", PARTIEL),
    (r"inflation mesurée|PIB, chômage", "module", "cycles_economiques", PARTIEL),
    (r"calcul d'intérêts", "aucun", None, NON_TRAITE),
    (r"mode de scrutin et paradoxes", "module", "choix_social", TRAITE),
    (r"entropie d'une source", "module", "information_calcul", PARTIEL),
    (r"encodage et compression|correction d'erreurs", "aucun", None, NON_TRAITE),
    (r"pharmacocinétique", "module", "pharmacochimie", PARTIEL),
    (r"efficacité d'un traitement|étiologie des maladies", "aucun", None, NON_TRAITE),
    (r"hérédité mendélienne|dynamique des populations", "module", "bioinfo", PARTIEL),
    (r"calcul de recette", "gate", "valide_fonction.py", PARTIEL),
    (r"préférences personnelles de l'utilisateur", "gate", "valide_faits_conversation.py", TRAITE),
)
_REGLES_C = tuple((re.compile(m, re.I), g, r, e) for m, g, r, e in _REGLES)

# ── AXES des annexes AUTO : l'état est décidé par l'AXE (pas par le métier) — mesuré une fois, appliqué à tous.
#    Aucun n'est traité aujourd'hui SAUF le non-borné, pris honnêtement par le routage (c'est le traitement
#    CORRECT d'un NB : abstention actionnable, jamais une réponse inventée). Le reste EST le backlog.
_AXES_ETAT = (
    (re.compile(r"est-il fait pour moi", re.I), TRAITE, "routage honnête (NB-SUBJ : l'utilisateur est la source)"),
    (re.compile(r"questions ouvertes du domaine", re.I), TRAITE, "routage honnête (NB-OUV : abstention dite)"),
    (re.compile(r"définition et périmètre", re.I), NON_TRAITE, "aucune table de définitions de métiers ingérée"),
    (re.compile(r"gestes et savoir-faire", re.I), NON_TRAITE, "part tacite : à séparer de la part codifiée"),
    (re.compile(r"outils, machines", re.I), NON_TRAITE, "aucune table outils×métier ingérée"),
    (re.compile(r"normes, réglementation", re.I), NON_TRAITE, "aucun corpus réglementaire ingéré"),
    (re.compile(r"risques professionnels", re.I), NON_TRAITE, "aucune table de risques ingérée"),
    (re.compile(r"formation, diplômes", re.I), NON_TRAITE, "aucun référentiel de formation ingéré"),
    (re.compile(r"rémunération médiane", re.I), NON_TRAITE, "aucune statistique salariale ingérée"),
    (re.compile(r"résultats établis du domaine", re.I), NON_TRAITE, "corpus de domaine non ingéré"),
)


def _preuve_existe(genre: str, ref) -> bool:
    if genre == "aucun":                                  # NON TRAITÉ assumé (déclaré tel quel, pas une dette)
        return True
    if ref is None:
        return False
    if genre == "gate":
        if _GEL:
            return True                                   # non vérifiable ici ; vérifiée en source par la gate
        return os.path.exists(os.path.join(_TESTS, ref))
    if genre == "module":
        return os.path.exists(os.path.join(_ICI, ref + ".py"))
    if genre == "roue":
        try:
            import pont_grandeurs as _P
            return any(r["nom"] == ref for r in _P._ROUES)
        except Exception:
            return False
    return True


def etat(sujet) -> tuple:
    """(état, preuve) d'un sujet — l'état TRAITÉ exige une preuve qui EXISTE réellement sur le disque."""
    partie = sujet.partie
    if partie.startswith("ANNEXE S"):
        return (TRAITE, "table vérifiée du store (ancrage audité 1371/1371)")
    if partie.startswith(("ANNEXE M", "ANNEXE D")):
        for rx, e, raison in _AXES_ETAT:
            if rx.search(sujet.libelle):
                return (e, raison)
        return (NON_TRAITE, "axe non classé")
    for rx, genre, ref, prevu in _REGLES_C:
        if not rx.search(sujet.libelle):
            continue
        if not _preuve_existe(genre, ref):
            return (NON_TRAITE, "preuve DÉCLARÉE INTROUVABLE (%s %s) — dette détectée" % (genre, ref))
        if genre == "aucun":
            return (NON_TRAITE, "aucun mécanisme dédié (backlog assumé)")
        if genre == "gate" and _GEL:
            return (prevu, "gate %s (vérifiée en source ; tests non embarqués dans le binaire)" % ref)
        return (prevu, "%s : %s" % (genre, ref))
    if sujet.non_borne or sujet.code in _S.FRONTIERE:
        return (TRAITE, "routage honnête : repli intent-aware + gardes G1-G9 (jamais une réponse inventée)")
    if sujet.mixte:
        return (PARTIEL, "part bornée servie par les mécanismes généraux ; séparation à durcir")
    return (NON_TRAITE, "aucun mécanisme dédié (backlog)")


def rapport(tous=None) -> dict:
    """Mesure complète : totaux, ventilation par état, et BACKLOG (la liste de travail des vagues suivantes)."""
    tous = tous if tous is not None else _S.charge_tout()
    out = {"total": len(tous), TRAITE: 0, PARTIEL: 0, NON_TRAITE: 0,
           "par_partie": {}, "backlog": [], "dettes": []}
    for s in tous:
        e, p = etat(s)
        out[e] += 1
        cle = s.partie.split("—")[0].strip() or "(sans partie)"
        d = out["par_partie"].setdefault(cle, {TRAITE: 0, PARTIEL: 0, NON_TRAITE: 0})
        d[e] += 1
        if e == NON_TRAITE:
            out["backlog"].append((s.libelle, cle, p))
            if "DÉCLARÉE INTROUVABLE" in p:
                out["dettes"].append((s.libelle, p))
    return out


if __name__ == "__main__":
    r = rapport()
    print("%d sujets : %d traités · %d partiels · %d NON traités"
          % (r["total"], r[TRAITE], r[PARTIEL], r[NON_TRAITE]))
    print("\nPar partie :")
    for partie, d in sorted(r["par_partie"].items()):
        print("  %-28s traités %6d · partiels %5d · non traités %6d"
              % (partie[:28], d[TRAITE], d[PARTIEL], d[NON_TRAITE]))
    if r["dettes"]:
        print("\nDETTES (preuve déclarée introuvable) :")
        for lib, p in r["dettes"][:10]:
            print("  ·", lib, "->", p)
    print("\nBacklog conceptuel (hors annexes auto), 25 premiers :")
    n = 0
    for lib, partie, p in r["backlog"]:
        if partie.startswith("ANNEXE"):
            continue
        print("  ·", lib, "(%s)" % partie)
        n += 1
        if n >= 25:
            break
