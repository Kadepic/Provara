"""
BIAIS DE SÉLECTION GÉNÉRIQUE — mécanisme de COLLISION (common-effect / collider).

MÉCANISME EXACT (pas une corrélation empirique) :
  Conditionner sur un EFFET COMMUN S de deux variables A et B crée une association A–B là où il n'y en avait
  aucune. C'est le paradoxe de Berkson (Berkson, 1946) : deux maladies A, B INDÉPENDANTES dans la population
  (odds ratio = 1) deviennent NÉGATIVEMENT associées dans le sous-groupe hospitalisé (S=1), parce que
  l'hospitalisation est causée par « A OU B » — savoir qu'un hospitalisé n'a pas A rend B plus probable.
  En termes de d-séparation (Pearl) : A ⟂ B mais A ̸⟂ B | S dès que S est un collider  A → S ← B.

POSTURE FAUX=0 (jamais un biais affirmé à tort, jamais un odds ratio inventé) :
  • Les odds ratios sont EXACTS (fractions.Fraction) : OR = (n11·n00) / (n10·n01). Aucun flottant, aucun arrondi.
  • `biais_berkson` exige la table COMPLÈTE (la population entière : au moins un non-sélectionné ET au moins un
    sélectionné). Avec le seul échantillon sélectionné, l'OR de population est INCALCULABLE -> ValueError.
  • HONNÊTETÉ FONDAMENTALE : détecter un biais de sélection EXIGE de connaître le MÉCANISME de sélection. Le
    module ne l'INFÈRE PAS des données seules (cf. `pourquoi_le_mecanisme_est_requis`). Il compare deux
    odds ratios ; il ne prétend jamais deviner pourquoi la sélection a eu lieu.
  • Effectif nul dans une case (l'OR devient indéfini / dégénéré) -> ValueError. Variable non binaire -> ValueError.

GARANTIES vérifiées en adverse (`valide_biais_collision.py`) :
  - ANCRE de Berkson (1946) : population OR = 1 (A,B indépendantes) ; échantillon hospitalisé OR < 1 ;
  - TÉMOIN : sélection indépendante de A et B -> OR_sélectionné == OR_population (aucun biais) ;
  - table incomplète (que des S=1, ou que des S=0) -> ValueError ;
  - case nulle (population ou échantillon), clé non binaire, effectif non entier, bool/str/NaN -> ValueError ;
  - `est_collider` réutilise le DAG de `causalite` (effet commun = deux parents) ;
  - déterministe, pur stdlib, conservateur (faux négatif toléré, faux POSITIF interdit).

Trois biais de sélection SPÉCIFIQUES ont leur propre module (cités ici, non modifiés) : biais_survie,
biais_publication, biais_longueur. Ce module traite la collision GÉNÉRIQUE et les catalogue.
"""
from __future__ import annotations

from fractions import Fraction

import biais_longueur
import biais_publication
import biais_survie
from causalite import GrapheCausal

SOURCE = "paradoxe de Berkson (1946) ; collision/common-effect — Pearl, Causality (d-séparation, colliders)"


# ── helpers de validation (FAUX=0 : bool refusé, non-binaire refusé) ────────────────────────────────────────────--
def _bit(x) -> int:
    """0 ou 1 STRICT (bool refusé : True n'est pas 1). Sinon ValueError (variable non binaire)."""
    if not isinstance(x, int) or isinstance(x, bool) or x not in (0, 1):
        raise ValueError(f"valeur binaire (0/1) attendue, reçu {x!r} — variable non binaire")
    return x


def _compte(x) -> int:
    """Effectif : entier ≥ 0 (bool refusé). Sinon ValueError."""
    if not isinstance(x, int) or isinstance(x, bool) or x < 0:
        raise ValueError(f"effectif entier ≥ 0 attendu, reçu {x!r}")
    return x


def _odds_ratio(n11: int, n10: int, n01: int, n00: int) -> Fraction:
    """OR EXACT = (n11·n00)/(n10·n01). Toute case nulle -> OR indéfini/dégénéré -> ValueError."""
    if n11 <= 0 or n10 <= 0 or n01 <= 0 or n00 <= 0:
        raise ValueError("case nulle dans la table 2×2 : odds ratio indéfini (abstention)")
    return Fraction(n11 * n00, n10 * n01)


def _tables_2x2(donnees):
    """Depuis {(a,b,s): effectif}, agrège la table 2×2 A–B en POPULATION (tous s) et SÉLECTIONNÉE (s=1).

    Exige la table COMPLÈTE : au moins un effectif s=0 ET au moins un effectif s=1 (sinon on ne dispose pas de
    la population entière et l'OR de population est incalculable). Renvoie (pop, sel) : deux dicts (a,b)->effectif.
    """
    if not isinstance(donnees, dict) or not donnees:
        raise ValueError("donnees : dictionnaire non vide {(a,b,s): effectif} attendu")
    pop = {(a, b): 0 for a in (0, 1) for b in (0, 1)}
    sel = {(a, b): 0 for a in (0, 1) for b in (0, 1)}
    total_s0 = 0
    total_s1 = 0
    for cle, val in donnees.items():
        if not isinstance(cle, tuple) or len(cle) != 3:
            raise ValueError(f"clé (a,b,s) à trois composantes attendue, reçu {cle!r}")
        a = _bit(cle[0])
        b = _bit(cle[1])
        s = _bit(cle[2])
        n = _compte(val)
        pop[(a, b)] += n
        if s == 1:
            sel[(a, b)] += n
            total_s1 += n
        else:
            total_s0 += n
    if total_s1 == 0:
        raise ValueError("aucun individu sélectionné (s=1) : rien à comparer (abstention)")
    if total_s0 == 0:
        raise ValueError("table incomplète : aucun non-sélectionné (s=0) — la population entière est requise "
                         "pour calculer l'OR de population, l'échantillon sélectionné seul ne suffit pas")
    return pop, sel


# ── (a) PARADOXE DE BERKSON : OR population vs OR sélectionné ────────────────────────────────────────────────────
def biais_berkson(donnees) -> dict:
    """Association A–B dans la POPULATION vs dans l'échantillon SÉLECTIONNÉ (s=1), en odds ratio EXACT.

    `donnees` : dict {(a, b, s): effectif} avec a,b,s ∈ {0,1}, effectifs entiers ≥ 0 ; la table doit être
    COMPLÈTE (des s=0 ET des s=1). Renvoie {'or_population', 'or_selectionne', 'biais_detecte'} où les OR sont
    des Fraction exactes et biais_detecte = (or_selectionne ≠ or_population).

    ABSTENTION (ValueError) : table incomplète, case nulle (OR indéfini), clé non binaire, effectif invalide.
    Le biais_detecte signale une DISTORSION par la sélection ; il ne prétend pas en connaître le mécanisme
    (cf. pourquoi_le_mecanisme_est_requis)."""
    pop, sel = _tables_2x2(donnees)
    or_pop = _odds_ratio(pop[(1, 1)], pop[(1, 0)], pop[(0, 1)], pop[(0, 0)])
    or_sel = _odds_ratio(sel[(1, 1)], sel[(1, 0)], sel[(0, 1)], sel[(0, 0)])
    return {
        "or_population": or_pop,
        "or_selectionne": or_sel,
        "biais_detecte": or_sel != or_pop,
    }


# ── (b) DÉTECTION DE COLLIDER dans un DAG (réutilise causalite) ─────────────────────────────────────────────────
def est_collider(dag, variable, a, b) -> bool:
    """`variable` est-elle un EFFET COMMUN (collider a → variable ← b) de a et b dans le DAG ?

    Vrai ssi a ET b sont des causes DIRECTES (parents) de `variable`, avec a, b, variable distincts.
    Conditionner sur un tel collider ouvre le chemin a—b (crée une association). `dag` : GrapheCausal
    (module causalite). Type invalide ou a==b / variable confondue -> ValueError."""
    if not isinstance(dag, GrapheCausal):
        raise ValueError("dag : instance de causalite.GrapheCausal attendue")
    if a == b:
        raise ValueError("a et b doivent être distincts pour un collider a → v ← b")
    if variable == a or variable == b:
        raise ValueError("la variable collider doit être distincte de a et de b")
    parents = dag.causes_directes(variable)
    return a in parents and b in parents


# ── (c) DÉMONSTRATION CHIFFRÉE : conditionner sur un collider crée une association ───────────────────────────────
def conditionner_sur_collider_cree_association() -> dict:
    """Démonstration chiffrée EXACTE sur variables binaires INDÉPENDANTES A, B et un collider S (A → S ← B).

    Construit la population entière (1000 personnes, P(A)=P(B)=1/10, indépendantes) et une sélection S causée
    par les maladies (probabilité d'hospitalisation croissante avec le nombre de maladies). Montre que
    l'OR de population vaut 1 (indépendance) mais que l'OR conditionné à S=1 est < 1 (association CRÉÉE).

    Renvoie {'or_population', 'or_conditionne', 'association_creee', 'table', 'explication'} — tout exact."""
    # Population : A,B indépendantes, P(A)=P(B)=1/10 sur 1000 -> 10 / 90 / 90 / 810 (produit des marges).
    # Sélection (hospitalisation) = collider : plus de maladies -> plus d'hospitalisation.
    #   h(A=1,B=1)=9/10 -> 9 ;  h(A=1,B=0)=h(A=0,B=1)=1/2 -> 45 ;  h(A=0,B=0)=1/10 -> 81.
    table = {
        (1, 1, 1): 9,  (1, 1, 0): 1,
        (1, 0, 1): 45, (1, 0, 0): 45,
        (0, 1, 1): 45, (0, 1, 0): 45,
        (0, 0, 1): 81, (0, 0, 0): 729,
    }
    res = biais_berkson(table)
    return {
        "or_population": res["or_population"],       # (10·810)/(90·90) = 1
        "or_conditionne": res["or_selectionne"],     # (9·81)/(45·45) = 729/2025 = 9/25 = 0.36
        "association_creee": res["biais_detecte"],   # True : 9/25 ≠ 1
        "table": dict(table),
        "explication": "A et B sont indépendantes (OR population = 1) ; conditionner sur le collider S=1 "
                       "(hospitalisation causée par A ou B) crée une association négative (OR = 9/25 < 1).",
    }


# ── (d) CATALOGUE des mécanismes de sélection nommés ────────────────────────────────────────────────────────────
def catalogue_biais() -> tuple:
    """Mécanismes de sélection nommés : pour chacun le MÉCANISME, le REMÈDE, et le module du dépôt qui le traite.

    Renvoie un tuple de dicts {'nom', 'mecanisme', 'remede', 'module'} ; 'module' = nom du module dédié
    (biais_survie / biais_publication / biais_longueur) ou None si traité par la collision générique d'ici."""
    return (
        {
            "nom": "Berkson (collision)",
            "mecanisme": "conditionner sur un effet commun S de A et B (collider A→S←B) crée une association A–B",
            "remede": "disposer de la population entière ; ne pas conditionner sur le collider (d-séparation)",
            "module": __name__,
        },
        {
            "nom": "survie",
            "mecanisme": "n'observer que les survivants (S = franchir un seuil) sur-estime la moyenne",
            "remede": "modéliser les disparus ; l'estimé survivant n'est qu'une borne supérieure (leçon de Wald)",
            "module": biais_survie.__name__,
        },
        {
            "nom": "publication (tiroir)",
            "mecanisme": "ne publier que les résultats significatifs gonfle l'effet apparent (file-drawer)",
            "remede": "pré-enregistrement, funnel plot / trim-and-fill, méta-analyse des non-significatifs",
            "module": biais_publication.__name__,
        },
        {
            "nom": "longueur / inspection",
            "mecanisme": "échantillonner proportionnellement à la taille/durée sur-représente les gros/longs",
            "remede": "pondérer par 1/longueur (correction harmonique) ; length-biased sampling",
            "module": biais_longueur.__name__,
        },
        {
            "nom": "non-réponse",
            "mecanisme": "la sélection S dépend de la disposition à répondre (répondants ≠ non-répondants)",
            "remede": "relances, pondération par propension de réponse, bornes ; mécanisme de sélection explicite",
            "module": None,
        },
        {
            "nom": "auto-sélection",
            "mecanisme": "les sujets se sélectionnent eux-mêmes (volontaires) selon un trait lié à l'issue",
            "remede": "échantillon aléatoire ; instrument/randomisation ; modéliser la règle de sélection",
            "module": None,
        },
    )


# ── (e) HONNÊTETÉ : le mécanisme de sélection est indispensable ─────────────────────────────────────────────────
def pourquoi_le_mecanisme_est_requis() -> str:
    """Déclaration d'honnêteté : pourquoi le biais de sélection ne s'infère PAS des données seules."""
    return (
        "Détecter un biais de sélection exige de connaître le MÉCANISME de sélection (la règle qui a produit "
        "S=1). Les données de l'échantillon sélectionné seul ne le révèlent pas : le même échantillon est "
        "compatible avec 'aucun biais' ou 'fort biais' selon la règle inconnue. Ce module ne DEVINE pas le "
        "mécanisme ; il compare deux odds ratios quand la population ENTIÈRE est fournie, et abstient sinon."
    )
