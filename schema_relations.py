"""
SCHÉMA DES RELATIONS (méta-modèle MESURÉ) — promotion de la brique 🟡 en objet de 1re classe (2026-07-02).

Décrit chaque relation du corpus comme un OBJET : cardinalité, populations de domaine/codomaine,
irréflexivité, symétrie, inversions, caractère hiérarchique (les valeurs sont elles-mêmes des clés ->
chaînes navigables). TOUT est MESURÉ sur les faits (pensée machine), rien n'est postulé.

INVARIANT FAUX=0 — deux forces de verdict, jamais confondues :
  • RÉFUTÉE (certaine)   : un CONTRE-EXEMPLE réel a été trouvé -> la propriété est fausse, point.
  • COMPATIBLE (échantillon) : aucun contre-exemple dans l'échantillon borné -> ce N'EST PAS une preuve.
    Un consommateur ne doit JAMAIS dériver un fait nouveau (arête miroir, fermeture) d'un simple
    « compatible » — seule une vérification exacte au cas par cas (lookup du fait miroir) reste sound.

Complète `taxonomie.py` (types de populations) ; sert `graphe_monde.py` (navigabilité) et
`ontologie.py` (choix des relations hiérarchiques). Lecture seule du lecteur, stdlib.
"""
from __future__ import annotations

import dataclasses
from itertools import islice

import lecteur
import taxonomie
from base_faits import normalise

_ECH = 400          # taille d'échantillon des mesures (bornée, déterministe : premiers de la table)


@dataclasses.dataclass(frozen=True)
class ProfilRelation:
    """Le méta-objet d'une relation, entièrement mesuré. `None` = non mesurable (table absente/vide)."""
    relation: str
    taille: int                      # nb d'entrées (clés)
    fonctionnelle: bool              # 1 clé -> 1 valeur (VRAI par construction du lecteur : conflit refusé)
    frac_valeurs_distinctes: float   # |valeurs distinctes| / |clés| sur l'échantillon (1.0 ≈ inversible)
    irreflexive_refutee: bool        # ∃ clé == valeur normalisée (contre-exemple RÉEL -> réflexivité avérée)
    symetrique_refutee: bool         # ∃ (x,y) avec r(y) ≠ x alors que y est clé (contre-exemple RÉEL)
    symetrique_compatible: float     # part des (x,y) échantillonnés avec r(y)==x (1.0 = compatible, PAS une preuve)
    hierarchique: float              # part des valeurs qui sont elles-mêmes des CLÉS de la relation (chaînes)
    types_domaine: tuple             # ensembles de référence compatibles avec les CLÉS (mesure taxonomie)
    types_codomaine: tuple           # ensembles de référence compatibles avec les VALEURS (mesure directe)
    source: str                      # source de la table (1er fait)


_PROFILS: dict = {}


def _table(rel):
    return lecteur.LECTEUR.tables.get(rel)


def profil(rel: str) -> ProfilRelation | None:
    """Mesure (et cache) le profil complet d'une relation. Coût : un échantillon borné + |ensembles| lookups."""
    if rel in _PROFILS:
        return _PROFILS[rel]
    t = _table(rel)
    if t is None or len(t) == 0:
        _PROFILS[rel] = None
        return None
    ech = list(islice(t.items(), _ECH))
    vals_norm = [normalise(str(f.valeur)) for _k, f in ech]
    n = len(ech)
    refl = any(k == v for (k, _f), v in zip(ech, vals_norm))
    # symétrie : pour les paires dont la VALEUR est aussi une clé, le fait miroir r(y)==x tient-il ?
    sym_paires = [(k, v) for (k, _f), v in zip(ech, vals_norm) if v in t]
    sym_ok = sum(1 for k, v in sym_paires if normalise(str(t.get(v).valeur)) == k)
    ens = taxonomie.ensembles()
    types_dom = tuple(nm for nm in ens if taxonomie.frac_ech(rel, nm) >= 0.5)
    types_cod = tuple(nm for nm, e in ens.items() if n and sum(1 for v in vals_norm if v in e) >= 0.5 * n)
    src = ""
    for _k, f in islice(t.items(), 1):
        src = getattr(f, "source", "") or ""
    p = ProfilRelation(
        relation=rel, taille=len(t), fonctionnelle=True,
        frac_valeurs_distinctes=(len(set(vals_norm)) / n) if n else 0.0,
        irreflexive_refutee=refl,
        symetrique_refutee=bool(sym_paires) and sym_ok < len(sym_paires),
        symetrique_compatible=(sym_ok / len(sym_paires)) if sym_paires else 0.0,
        hierarchique=(len(sym_paires) / n) if n else 0.0,   # valeurs qui sont des clés = maillons de chaîne
        types_domaine=types_dom, types_codomaine=types_cod, source=src,
    )
    _PROFILS[rel] = p
    return p


def inverses_compatibles(rel1: str, rel2: str, ech: int = 200) -> tuple:
    """(refutee, compatible) : r1(x)=y ∧ y clé de r2 -> r2(y)==x ? Mesuré sur échantillon.
    `refutee=True` = contre-exemple RÉEL (certain) ; `compatible` = part des paires qui tiennent (PAS une preuve)."""
    t1, t2 = _table(rel1), _table(rel2)
    if t1 is None or t2 is None:
        return (False, 0.0)
    paires = []
    for k, f in islice(t1.items(), ech):
        v = normalise(str(f.valeur))
        if v in t2:
            paires.append((k, v))
    if not paires:
        return (False, 0.0)
    ok = sum(1 for k, v in paires if normalise(str(t2.get(v).valeur)) == k)
    return (ok < len(paires), ok / len(paires))


def relations_hierarchiques(seuil: float = 0.5, min_taille: int = 50) -> list:
    """Relations NAVIGABLES EN CHAÎNE (valeurs majoritairement elles-mêmes clés : parent→parent→…),
    candidates au raisonnement hiérarchique (`ontologie.py`). Mesuré, trié par taille décroissante."""
    out = []
    for rel in sorted(lecteur.LECTEUR.tables.keys()):
        t = _table(rel)
        if t is None or len(t) < min_taille:
            continue
        p = profil(rel)
        if p is not None and p.hierarchique >= seuil:
            out.append((p.taille, rel, round(p.hierarchique, 2)))
    out.sort(reverse=True)
    return out
