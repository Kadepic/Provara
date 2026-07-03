"""
SCRUTIN — Vote / processus électoral (mécanique). MÉCANISME EXACT, FAUX=0.

Posture (la réalité/le mécanisme juge, jamais un faux) :
  • Les algorithmes de répartition des sièges (D'Hondt, Sainte-Laguë) sont EXACTS — c'est la garantie
    structurelle. On calcule les quotients en arithmétique RATIONNELLE (fractions.Fraction), donc les
    comparaisons de quotients sont EXACTES (aucune erreur de virgule flottante ne peut fausser un départage).
  • Le seul cas non déterminé par le mécanisme pur est l'ÉGALITÉ de quotient au siège-frontière entre deux
    partis distincts : la loi exige alors un départage externe (tirage au sort, plus fort total…). On REFUSE
    d'inventer ce départage -> ValueError (abstention), jamais un siège attribué arbitrairement.

GARANTIES (vérifiées en adverse par valide_scrutin.py) :
  - n_sieges <= 0  -> ValueError ;
  - voix négative / non entière / booléen / dict de voix vide -> ValueError ;
  - total <= 0, voix > total (majorité) -> ValueError ;
  - égalité de quotient au seuil entre partis distincts -> ValueError (départage non mécanique) ;
  - déterministe ; conservateur (abstention tolérée, faux POSITIF interdit).
"""
from __future__ import annotations

from fractions import Fraction


def _voix_valide(v) -> bool:
    """Une voix est un entier >= 0 (un bulletin se compte ; pas de booléen, pas de flottant)."""
    return isinstance(v, int) and not isinstance(v, bool) and v >= 0


def _valide_scrutin(votes, n_sieges) -> None:
    if not isinstance(votes, dict) or len(votes) == 0:
        raise ValueError("votes doit être un dict non vide {parti: voix}")
    if isinstance(n_sieges, bool) or not isinstance(n_sieges, int):
        raise ValueError("n_sieges doit être un entier")
    if n_sieges <= 0:
        raise ValueError("n_sieges doit être > 0")
    for parti, voix in votes.items():
        if not _voix_valide(voix):
            raise ValueError(f"voix invalide pour {parti!r} : {voix!r} (entier >= 0 attendu)")


def _plus_forte_moyenne(votes: dict, n_sieges: int, pas: int, depart: int) -> dict:
    """
    Méthode du plus fort quotient (diviseurs depart, depart+pas, depart+2·pas, …).
      D'Hondt      : depart=1, pas=1  -> diviseurs 1, 2, 3, …
      Sainte-Laguë : depart=1, pas=2  -> diviseurs 1, 3, 5, …
    On retient les n_sieges plus grands quotients. Égalité non mécanique au seuil -> ValueError.
    """
    quotients = []  # (quotient_exact, parti)
    for parti, voix in votes.items():
        for k in range(n_sieges):  # au plus n_sieges quotients utiles par parti
            div = depart + pas * k
            quotients.append((Fraction(voix, div), parti))
    quotients.sort(key=lambda qp: qp[0], reverse=True)

    seuil = quotients[n_sieges - 1][0]  # n-ième plus grand quotient
    sieges = {p: 0 for p in votes}

    # 1) quotients STRICTEMENT au-dessus du seuil -> sièges garantis
    for q, p in quotients:
        if q > seuil:
            sieges[p] += 1
    restant = n_sieges - sum(sieges.values())

    # 2) quotients EXACTEMENT égaux au seuil -> sièges contestés
    ex_aequo = [p for q, p in quotients if q == seuil]
    if restant == len(ex_aequo):
        for p in ex_aequo:                       # pas de contestation : tous entrent
            sieges[p] += 1
    elif len(set(ex_aequo)) == 1:
        sieges[ex_aequo[0]] += restant           # ex æquo d'un SEUL parti : déterministe
    else:
        raise ValueError(
            "égalité de quotient au siège-frontière entre partis distincts : "
            "départage non mécanique (la loi exige tirage au sort / plus fort total)"
        )
    return sieges


def dhondt(votes: dict, n_sieges: int) -> dict:
    """Répartition D'Hondt (diviseurs 1, 2, 3, …) — favorise légèrement les grands partis."""
    _valide_scrutin(votes, n_sieges)
    return _plus_forte_moyenne(votes, n_sieges, pas=1, depart=1)


def sainte_lague(votes: dict, n_sieges: int) -> dict:
    """Répartition Sainte-Laguë (diviseurs 1, 3, 5, …) — plus proportionnelle aux petits partis."""
    _valide_scrutin(votes, n_sieges)
    return _plus_forte_moyenne(votes, n_sieges, pas=2, depart=1)


def quotient_hare(total_voix: int, n_sieges: int) -> float:
    """Quotient de Hare (quota simple) = total des voix / nombre de sièges."""
    if isinstance(total_voix, bool) or not isinstance(total_voix, int) or total_voix < 0:
        raise ValueError("total_voix doit être un entier >= 0")
    if isinstance(n_sieges, bool) or not isinstance(n_sieges, int) or n_sieges <= 0:
        raise ValueError("n_sieges doit être un entier > 0")
    return total_voix / n_sieges


def majorite_absolue(voix: int, total: int) -> bool:
    """Vrai si voix > total/2 (majorité absolue, strictement plus de la moitié)."""
    if isinstance(voix, bool) or not isinstance(voix, int) or voix < 0:
        raise ValueError("voix doit être un entier >= 0")
    if isinstance(total, bool) or not isinstance(total, int) or total <= 0:
        raise ValueError("total doit être un entier > 0")
    if voix > total:
        raise ValueError("voix ne peut excéder le total des suffrages")
    return voix > Fraction(total, 2)
