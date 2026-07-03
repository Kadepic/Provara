"""
HIÉRARCHIE DES NORMES — pyramide de Kelsen (droit français / continental, hiérarchie ÉTABLIE).

Posture FAUX=0 (la réalité juridique juge, jamais un faux) :
  • Le CATALOGUE des rangs est une convention juridique ÉTABLIE et SOURCÉE (théorie de Hans Kelsen,
    « Théorie pure du droit » ; bloc de constitutionnalité, art. 55 de la Constitution de 1958 pour la
    primauté des traités sur la loi ; hiérarchie réglementaire décret > arrêté). Ce n'est pas une opinion :
    c'est l'ordonnancement juridique du droit positif français.
  • Le MÉCANISME (comparaison de rangs entiers) est EXACT et déterministe.
  • Toute entrée HORS référentiel -> ValueError (abstention) : on n'invente JAMAIS un rang pour un
    type de norme inconnu.

PYRAMIDE (du sommet vers la base, rang croissant = autorité décroissante) :
  1. constitution           — bloc de constitutionnalité (Constitution + Préambule + DDHC + PFRLR)
  2. traite_international    — traités ratifiés (art. 55 C. : supérieurs aux lois)
  3. loi                    — lois votées par le Parlement (+ lois organiques au même étage légal)
  4. reglement / decret     — pouvoir réglementaire (art. 21 C. : décret du Premier ministre / Président)
  5. arrete                 — arrêtés ministériels, préfectoraux, municipaux (réglementaire subordonné)
  6. contrat / acte_individuel — actes individuels, contrats, décisions d'espèce (base de la pyramide)

GARANTIES (vérifiées en adverse par valide_hierarchie_normes.py) :
  - type de norme hors hiérarchie -> ValueError (jamais un rang inventé) ;
  - déterministe, fonctions pures ;
  - conservateur : au moindre doute (type inconnu) -> abstention.
"""
from __future__ import annotations

# ── CATALOGUE ÉTABLI : rang de chaque type de norme (1 = sommet, autorité maximale) ──────────────
# Les synonymes pointent vers le même rang (ex. 'reglement' et 'decret' = rang 4).
_RANGS: dict[str, int] = {
    "constitution": 1,
    "bloc_constitutionnalite": 1,
    "traite_international": 2,
    "traite": 2,
    "convention_internationale": 2,
    "droit_europeen": 2,            # traités/règlements UE : étage supra-législatif (art. 55)
    "loi": 3,
    "loi_organique": 3,
    "loi_ordinaire": 3,
    "ordonnance": 3,                # ordonnance ratifiée = valeur législative
    "reglement": 4,
    "decret": 4,
    "arrete": 5,
    "contrat": 6,
    "acte_individuel": 6,
    "decision_individuelle": 6,
}

SOURCE = "Kelsen, Théorie pure du droit ; Constitution française 1958 (art. 21, 34, 37, 55)"


def _normalise(type_norme: str) -> str:
    if not isinstance(type_norme, str):
        raise ValueError(f"type de norme invalide (attendu str) : {type_norme!r}")
    return type_norme.strip().lower()


def rang(type_norme: str) -> int:
    """Rang hiérarchique du type de norme (1 = constitution au sommet … 6 = acte individuel).
    Type hors pyramide -> ValueError (abstention, jamais un rang inventé)."""
    clef = _normalise(type_norme)
    if clef not in _RANGS:
        raise ValueError(f"type de norme hors hiérarchie de Kelsen : {type_norme!r}")
    return _RANGS[clef]


def superieur(norme1: str, norme2: str) -> bool:
    """True si norme1 PRIME sur norme2 (rang strictement plus petit = plus haut dans la pyramide).
    Types inconnus -> ValueError."""
    return rang(norme1) < rang(norme2)


def inferieur(norme1: str, norme2: str) -> bool:
    """True si norme1 est SUBORDONNÉE à norme2 (rang strictement plus grand)."""
    return rang(norme1) > rang(norme2)


def meme_rang(norme1: str, norme2: str) -> bool:
    """True si les deux types occupent le même étage de la pyramide (ex. loi et loi organique)."""
    return rang(norme1) == rang(norme2)


def conforme(norme_inferieure: str, norme_superieure: str) -> bool:
    """Une norme doit RESPECTER les normes de rang supérieur (ou égal) pour être conforme.

    Renvoie True si la relation de conformité est REQUISE et VALIDE structurellement :
    norme_inferieure est bien de rang >= norme_superieure (donc elle lui est subordonnée et
    doit s'y conformer). Renvoie False si norme_inferieure est en réalité SUPÉRIEURE
    (elle n'a alors pas à se conformer à une norme de rang inférieur).
    Types inconnus -> ValueError.

    Ex. conforme('decret', 'loi') = True  (un décret doit respecter la loi)
        conforme('loi', 'decret') = False (la loi ne se conforme pas à un décret)
    """
    return rang(norme_inferieure) >= rang(norme_superieure)


def domine(type_norme: str) -> list[str]:
    """Liste (triée par rang) des étages STRICTEMENT subordonnés au type donné.
    Type inconnu -> ValueError."""
    r = rang(type_norme)
    etages = sorted({v for v in _RANGS.values() if v > r})
    repr_par_rang = {}
    for nom, v in _RANGS.items():
        repr_par_rang.setdefault(v, nom)
    return [repr_par_rang[v] for v in etages]


def hierarchie() -> list[tuple[int, str]]:
    """Pyramide canonique (rang, libellé représentatif) du sommet vers la base — déterministe."""
    canon = {
        1: "constitution",
        2: "traite_international",
        3: "loi",
        4: "decret",
        5: "arrete",
        6: "acte_individuel",
    }
    return [(r, canon[r]) for r in sorted(canon)]
