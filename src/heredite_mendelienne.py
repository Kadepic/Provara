"""
HÉRÉDITÉ MENDÉLIENNE — croisements et échiquier de Punnett, EXACTS (PARTIE V, B-NEC).

ATTENTION aux pièges de nom de ce dépôt : `bioinfo.py` traite des SÉQUENCES d'ADN (distance de Hamming,
taux GC) et n'a rien à voir avec l'hérédité ; `genetique.py` porte le code génétique (codon -> acide aminé).
Ce module-ci est le seul à traiter les LOIS DE MENDEL.

Le sujet est borné par NÉCESSITÉ : une fois les allèles et la dominance POSÉS, les proportions découlent du
dénombrement. Rien n'est estimé, tout est compté — en `Fraction` exacte, jamais en flottant.

MÉCANISME (lois de Mendel, 1866) :
  • Loi de SÉGRÉGATION : chaque parent transmet UN allèle par gène, tiré équiprobablement parmi ses deux.
  • Loi d'ASSORTIMENT INDÉPENDANT : deux gènes situés sur des chromosomes différents se transmettent
    indépendamment. Le module l'ASSUME et le DIT : pour deux gènes LIÉS (même chromosome), les proportions
    dépendent du taux de recombinaison, qui n'est pas déductible — `croisement_dihybride` prend donc un
    paramètre `independants` et lève ValueError si on le met à False (on ne devine pas une distance génétique).

TROIS RÉGIMES DE DOMINANCE, nommés explicitement à chaque appel (jamais implicites) :
  • 'complete'    — l'hétérozygote a le phénotype du dominant           (Aa -> [A]) ;
  • 'incomplete'  — l'hétérozygote a un phénotype INTERMÉDIAIRE          (Aa -> [Aa], ex. fleur rose) ;
  • 'codominance' — l'hétérozygote exprime les DEUX allèles              (Aa -> [A et a], ex. groupe AB).
Le régime CHANGE les proportions phénotypiques (3:1 contre 1:2:1) : le laisser implicite serait un faux.

GARANTIES (vérifiées en adverse par `valide_heredite_mendelienne.py`) :
  - génotype mal formé (longueur ≠ 2, allèles de gènes différents, caractères non alphabétiques) -> ValueError ;
  - régime de dominance hors des trois nommés -> ValueError ;
  - `croisement_dihybride(..., independants=False)` -> ValueError (le taux de recombinaison est inconnu) ;
  - INVARIANT DUR : la somme des proportions vaut EXACTEMENT 1 (Fraction), sinon RuntimeError ;
  - déterministe, pur, stdlib seule (`fractions`, `itertools`, `collections`).
"""
from __future__ import annotations

import collections
import itertools
from fractions import Fraction

SOURCE = "lois de Mendel (ségrégation, assortiment indépendant) — dénombrement exact sur l'échiquier de Punnett"

DOMINANCES = ("complete", "incomplete", "codominance")


def _exige_genotype(g, nom: str = "génotype") -> str:
    """Un génotype mono-génique : deux allèles du MÊME gène, ex. 'Aa', 'AA', 'aa'."""
    if isinstance(g, bool) or not isinstance(g, str):
        raise ValueError("%s invalide : une chaîne de deux allèles est requise" % nom)
    if len(g) != 2 or not g.isalpha():
        raise ValueError("%s invalide : exactement deux lettres (ex. 'Aa'), reçu %r" % (nom, g))
    if g[0].lower() != g[1].lower():
        raise ValueError("%s invalide : les deux allèles doivent porter sur le MÊME gène "
                         "(reçu %r : '%s' et '%s')" % (nom, g, g[0], g[1]))
    return g


def _exige_dominance(d) -> str:
    if d not in DOMINANCES:
        raise ValueError("régime de dominance à NOMMER explicitement parmi %s, reçu %r"
                         % (list(DOMINANCES), d))
    return d


def _ordonne(a: str, b: str) -> str:
    """Génotype canonique : le dominant (majuscule) d'abord. 'aA' et 'Aa' sont le même génotype."""
    return "".join(sorted((a, b), key=lambda c: (c.islower(), c)))


def gametes(genotype: str) -> tuple:
    """Les allèles transmissibles, avec leur probabilité EXACTE (loi de ségrégation).

    'Aa' -> (('A', 1/2), ('a', 1/2)) ; 'AA' -> (('A', 1),)."""
    g = _exige_genotype(genotype)
    compte = collections.Counter(g)
    return tuple(sorted((a, Fraction(n, 2)) for a, n in compte.items()))


def phenotype(genotype: str, dominance: str) -> str:
    """Phénotype d'un génotype, SOUS LE RÉGIME NOMMÉ. Le régime change la réponse : il n'est jamais implicite."""
    g = _exige_genotype(genotype)
    d = _exige_dominance(dominance)
    dom = g[0].upper()
    rec = dom.lower()
    homo_dom, homo_rec = dom + dom, rec + rec
    canon = _ordonne(*g)
    if canon == homo_dom:
        return "[%s]" % dom
    if canon == homo_rec:
        return "[%s]" % rec
    if d == "complete":
        return "[%s]" % dom                      # l'hétérozygote est indiscernable du dominant homozygote
    if d == "incomplete":
        return "[%s%s intermédiaire]" % (dom, rec)
    return "[%s et %s]" % (dom, rec)             # codominance : les deux allèles s'expriment


def _verifie_somme(proportions: dict) -> None:
    total = sum(proportions.values(), Fraction(0))
    if total != 1:
        raise RuntimeError("invariant violé : les proportions somment à %s, pas à 1" % total)


def croisement(parent1: str, parent2: str) -> dict:
    """Échiquier de Punnett mono-hybride : génotype -> proportion EXACTE (Fraction). Somme = 1."""
    g1, g2 = gametes(parent1), gametes(parent2)
    out: dict = collections.defaultdict(Fraction)
    for a1, p1 in g1:
        for a2, p2 in g2:
            out[_ordonne(a1, a2)] += p1 * p2
    res = dict(out)
    _verifie_somme(res)
    return res


def proportions_phenotypiques(parent1: str, parent2: str, dominance: str) -> dict:
    """Phénotype -> proportion EXACTE, sous le régime de dominance NOMMÉ."""
    d = _exige_dominance(dominance)
    out: dict = collections.defaultdict(Fraction)
    for genotype, part in croisement(parent1, parent2).items():
        out[phenotype(genotype, d)] += part
    res = dict(out)
    _verifie_somme(res)
    return res


def croisement_dihybride(parent1: str, parent2: str, independants: bool = True) -> dict:
    """Croisement à DEUX gènes ('AaBb' × 'AaBb') -> génotype -> proportion exacte.

    `independants=False` -> ValueError : deux gènes LIÉS ne se transmettent pas indépendamment, et leurs
    proportions dépendent du taux de recombinaison, qui n'est PAS déductible des génotypes. On abstient."""
    if independants is not True:
        raise ValueError("gènes liés : les proportions dépendent du taux de recombinaison, inconnu ici "
                         "(abstention — la loi d'assortiment indépendant ne s'applique pas)")
    for nom, p in (("parent1", parent1), ("parent2", parent2)):
        if isinstance(p, bool) or not isinstance(p, str) or len(p) != 4 or not p.isalpha():
            raise ValueError("%s invalide : quatre lettres attendues (ex. 'AaBb'), reçu %r" % (nom, p))
    g1 = (_exige_genotype(parent1[:2], "gène 1"), _exige_genotype(parent1[2:], "gène 2"))
    g2 = (_exige_genotype(parent2[:2], "gène 1"), _exige_genotype(parent2[2:], "gène 2"))
    if g1[0][0].lower() == g1[1][0].lower():
        raise ValueError("les deux gènes doivent être DISTINCTS (reçu deux fois le même)")

    out: dict = collections.defaultdict(Fraction)
    for (a1, pa1), (b1, pb1) in itertools.product(gametes(g1[0]), gametes(g1[1])):
        for (a2, pa2), (b2, pb2) in itertools.product(gametes(g2[0]), gametes(g2[1])):
            cle = _ordonne(a1, a2) + _ordonne(b1, b2)
            out[cle] += pa1 * pb1 * pa2 * pb2
    res = dict(out)
    _verifie_somme(res)
    return res


def proportions_phenotypiques_dihybride(parent1: str, parent2: str, dominance: str,
                                        independants: bool = True) -> dict:
    """Phénotypes d'un dihybride, sous le régime NOMMÉ. AaBb × AaBb en dominance complète -> 9:3:3:1."""
    d = _exige_dominance(dominance)
    out: dict = collections.defaultdict(Fraction)
    for g, part in croisement_dihybride(parent1, parent2, independants).items():
        out[phenotype(g[:2], d) + phenotype(g[2:], d)] += part
    res = dict(out)
    _verifie_somme(res)
    return res


def test_cross(genotype_inconnu_phenotype_dominant: str) -> dict:
    """Croisement-test : l'inconnu (phénotype dominant) × homozygote récessif.

    C'est LE geste expérimental de Mendel : la descendance révèle le génotype de l'inconnu.
    'AA' -> 100 % dominants ; 'Aa' -> 1/2 dominants, 1/2 récessifs."""
    g = _exige_genotype(genotype_inconnu_phenotype_dominant)
    rec = g[0].lower()
    return proportions_phenotypiques(g, rec + rec, "complete")
