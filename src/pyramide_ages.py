"""
PYRAMIDE DES ÂGES — structure par âge et sexe d'une population donnée (démographie classique).

Même posture FAUX=0 que `physique` / `geometries_non_euclidiennes` (la réalité juge, jamais un faux) :
  • Le MÉCANISME est de l'ARITHMÉTIQUE EXACTE sur des effectifs recensés, pas une estimation :
      – une pyramide = tranches d'âge [borne_basse, borne_haute) CONTIGUËS et NON RECOUVRANTES,
        chacune portant (hommes, femmes) en effectifs ENTIERS ≥ 0 (un recensement compte, il n'estime pas) ;
      – sex-ratio  = hommes / femmes × 100  (convention démographique standard : nombre d'hommes
        pour 100 femmes) ;
      – âge médian = âge qui partage la population en deux moitiés égales, obtenu par INTERPOLATION
        LINÉAIRE dans la tranche médiane (méthode standard des données groupées) — l'interpolation
        SUPPOSE l'uniformité dans la tranche : la valeur est donc APPROCHÉE et documentée comme telle ;
      – taux de dépendance = (moins de 15 ans + 65 ans et plus) / (15–64 ans) × 100 (définition ONU) ;
      – type de pyramide : critère EXPLICITE et CALCULÉ  rapport = effectif(base) / effectif(milieu) ;
            rapport > 1.1  -> 'expansive'   (base large, décroissance rapide) ;
            rapport < 0.9  -> 'regressive'  (base plus étroite que le milieu) ;
            sinon          -> 'stationnaire' (flancs quasi parallèles).
        Le verdict n'est JAMAIS rendu nu : la fonction renvoie (verdict, rapport).
  • Les calculs internes passent par `fractions.Fraction` (exactitude) ; la sortie flottante est
    ARRONDIE à 10 chiffres significatifs — précision honnête, et on le dit.

GARANTIES (vérifiées en adverse par `valide_pyramide_ages.py`) :
  - liste de tranches vide -> ValueError ;
  - bornes inversées (borne_basse ≥ borne_haute) -> ValueError ;
  - borne d'âge NÉGATIVE (borne_basse < 0) -> ValueError (un âge est ≥ 0 par nature) ;
  - tranches non contiguës -> ValueError NOMMANT le trou (« trou entre X et Y ») ;
  - tranches recouvrantes -> ValueError NOMMANT le recouvrement (« recouvrement entre X et Y ») ;
  - effectif négatif, flottant, bool -> ValueError (un effectif est un ENTIER ≥ 0) ;
  - bornes non réelles finies (bool, str, NaN, ±inf) -> ValueError ;
  - sex_ratio avec 0 femme -> ValueError (division par zéro = abstention, pas un infini) ;
  - part_tranche / taux_dependance sur des bornes qui ne tombent PAS sur des frontières de tranches
    -> ValueError (découper une tranche exigerait une hypothèse de répartition : on s'abstient) ;
  - population totale nulle (âge médian), tranche du milieu vide (type), actifs nuls (dépendance)
    -> ValueError ;
  - déterministe ; conservateur (faux négatif/abstention toléré, faux POSITIF interdit).

Le module n'importe que `math` et `fractions` (stdlib) ; aucune dépendance, aucun état global mutable.
`src/demographie.py` (réservé) n'est NI importé NI modifié.
"""
from __future__ import annotations

import math
from fractions import Fraction

SOURCE = ("démographie classique : sex-ratio H/F×100, âge médian par interpolation linéaire "
          "(données groupées), taux de dépendance ONU (0-14 + 65+)/(15-64)×100, "
          "typologie expansive/stationnaire/régressive (rapport base/milieu)")

_CHIFFRES_SIGNIFICATIFS = 10

# Seuils EXPLICITES du critère de forme (rapport base/milieu) — rendus avec le verdict, jamais cachés.
SEUIL_EXPANSIVE = Fraction(11, 10)   # rapport > 1.1  -> base nettement plus large que le milieu
SEUIL_REGRESSIVE = Fraction(9, 10)   # rapport < 0.9  -> base nettement plus étroite que le milieu

# Bornes de la définition ONU du taux de dépendance.
_AGE_FIN_JEUNES = 15    # « moins de 15 ans »
_AGE_DEBUT_AGES = 65    # « 65 ans et plus »


def _sig(x: float, n: int = _CHIFFRES_SIGNIFICATIFS) -> float:
    """Arrondit à n chiffres significatifs (précision honnête, indépendante de la magnitude)."""
    if x == 0:
        return 0.0
    return float(f"{x:.{n}g}")


def _est_reel(x) -> bool:
    """True ssi x est un réel fini (les bool sont REFUSÉS : True n'est pas une mesure)."""
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x)


def _exige_borne(x, quoi: str) -> float:
    if not _est_reel(x):
        raise ValueError(f"{quoi} invalide : un réel fini est requis (bool/str/NaN/inf refusés)")
    return float(x)


def _exige_effectif(x, quoi: str) -> int:
    """Un effectif recensé est un ENTIER ≥ 0 : bool, flottant, négatif -> ValueError."""
    if not isinstance(x, int) or isinstance(x, bool):
        raise ValueError(f"{quoi} invalide : un effectif est un entier (bool et flottants refusés)")
    if x < 0:
        raise ValueError(f"{quoi} invalide : un effectif est ≥ 0 (reçu {x})")
    return x


class Pyramide:
    """Pyramide des âges : tranches [borne_basse, borne_haute) contiguës, effectifs (hommes, femmes).

    INVARIANT DUR vérifié à la construction : tranches contiguës et non recouvrantes, sinon
    ValueError nommant le trou ou le recouvrement. L'objet est ensuite immuable (tuples)."""

    def __init__(self, tranches):
        if not isinstance(tranches, (list, tuple)) or len(tranches) == 0:
            raise ValueError("tranches invalide : une liste NON VIDE de (borne_basse, borne_haute, "
                             "hommes, femmes) est requise")
        propres = []
        for i, t in enumerate(tranches):
            if not isinstance(t, (list, tuple)) or len(t) != 4:
                raise ValueError(f"tranche #{i} invalide : exactement (borne_basse, borne_haute, "
                                 f"hommes, femmes) est requis")
            bas = _exige_borne(t[0], f"tranche #{i} borne_basse")
            haut = _exige_borne(t[1], f"tranche #{i} borne_haute")
            if bas < 0:
                raise ValueError(f"tranche #{i} : borne_basse négative ({bas}) ; "
                                 f"un âge est ≥ 0 par nature")
            if bas >= haut:
                raise ValueError(f"tranche #{i} : bornes inversées ou nulles "
                                 f"(borne_basse={bas} ≥ borne_haute={haut})")
            h = _exige_effectif(t[2], f"tranche #{i} hommes")
            f = _exige_effectif(t[3], f"tranche #{i} femmes")
            propres.append((bas, haut, h, f))
        # INVARIANT DUR : contiguïté stricte, sans trou ni recouvrement (ordre croissant exigé).
        for i in range(1, len(propres)):
            haut_prec = propres[i - 1][1]
            bas_suiv = propres[i][0]
            if bas_suiv > haut_prec:
                raise ValueError(f"tranches non contiguës : trou entre {haut_prec} et {bas_suiv}")
            if bas_suiv < haut_prec:
                raise ValueError(f"tranches recouvrantes : recouvrement entre {bas_suiv} et {haut_prec}")
        self._tranches = tuple(propres)

    # ── EFFECTIFS ───────────────────────────────────────────────────────────────────────────────────
    def effectif_total(self) -> int:
        """Effectif total (hommes + femmes, toutes tranches) — entier exact."""
        return sum(h + f for (_, _, h, f) in self._tranches)

    def sex_ratio(self) -> float:
        """Sex-ratio = hommes / femmes × 100 (hommes pour 100 femmes). 0 femme -> ValueError."""
        hommes = sum(h for (_, _, h, _) in self._tranches)
        femmes = sum(f for (_, _, _, f) in self._tranches)
        if femmes == 0:
            raise ValueError("sex_ratio indéfini : 0 femme dans la population (division par zéro)")
        return _sig(float(Fraction(hommes * 100, femmes)))

    def part_tranche(self, bas, haut) -> float:
        """Part (%) de la population dont l'âge est dans [bas, haut).

        bas et haut DOIVENT tomber sur des frontières de tranches existantes (sinon il faudrait
        découper une tranche, donc supposer une répartition interne : ValueError, on s'abstient)."""
        bas = _exige_borne(bas, "bas")
        haut = _exige_borne(haut, "haut")
        if bas >= haut:
            raise ValueError(f"part_tranche : bornes inversées ou nulles (bas={bas} ≥ haut={haut})")
        frontieres = {self._tranches[0][0]} | {t[1] for t in self._tranches}
        if bas not in frontieres or haut not in frontieres:
            raise ValueError(f"part_tranche : [{bas}, {haut}) ne tombe pas sur des frontières de "
                             f"tranches ({sorted(frontieres)}) ; découper exigerait une hypothèse")
        total = self.effectif_total()
        if total == 0:
            raise ValueError("part_tranche indéfinie : population totale nulle")
        dedans = sum(h + f for (b, ht, h, f) in self._tranches if b >= bas and ht <= haut)
        return _sig(float(Fraction(dedans * 100, total)))

    # ── FORME ───────────────────────────────────────────────────────────────────────────────────────
    def type_pyramide(self):
        """Type de la pyramide, avec le rapport base/milieu RENDU (jamais un verdict nu).

        rapport = effectif(première tranche) / effectif(tranche du milieu, indice len//2) ;
        rapport > 1.1 -> ('expansive', rapport) ; rapport < 0.9 -> ('regressive', rapport) ;
        sinon -> ('stationnaire', rapport). Tranche du milieu vide -> ValueError."""
        base = self._tranches[0][2] + self._tranches[0][3]
        t_mil = self._tranches[len(self._tranches) // 2]
        milieu = t_mil[2] + t_mil[3]
        if milieu == 0:
            raise ValueError("type_pyramide indéfini : la tranche du milieu est vide "
                             "(rapport base/milieu = division par zéro)")
        rapport = Fraction(base, milieu)
        if rapport > SEUIL_EXPANSIVE:
            verdict = "expansive"
        elif rapport < SEUIL_REGRESSIVE:
            verdict = "regressive"
        else:
            verdict = "stationnaire"
        return (verdict, _sig(float(rapport)))

    # ── ÂGE MÉDIAN ──────────────────────────────────────────────────────────────────────────────────
    def age_median(self) -> float:
        """Âge médian par interpolation linéaire dans la tranche médiane (données groupées).

        médiane = bas + (N/2 − cumul_avant) / effectif_tranche × (haut − bas).
        Valeur APPROCHÉE : l'interpolation suppose la répartition uniforme DANS la tranche.
        Population totale nulle -> ValueError."""
        total = self.effectif_total()
        if total == 0:
            raise ValueError("age_median indéfini : population totale nulle")
        moitie = Fraction(total, 2)
        cumul = Fraction(0)
        for (bas, haut, h, f) in self._tranches:
            eff = h + f
            if eff > 0 and cumul + eff >= moitie:
                age = (Fraction(bas) + (moitie - cumul) / eff * (Fraction(haut) - Fraction(bas)))
                return _sig(float(age))
            cumul += eff
        # Inatteignable si total > 0 (le cumul final vaut total ≥ moitié) ; abstention par principe.
        raise ValueError("age_median : tranche médiane introuvable (état incohérent)")

    # ── TAUX DE DÉPENDANCE (définition ONU) ─────────────────────────────────────────────────────────
    def taux_dependance(self) -> float:
        """Taux de dépendance = (moins de 15 ans + 65 ans et plus) / (15–64 ans) × 100.

        Les âges 15 et 65 DOIVENT tomber sur des frontières de tranches (ou hors de la pyramide),
        sinon une tranche à cheval exigerait une hypothèse de répartition -> ValueError.
        0 actif (15–64) -> ValueError (division par zéro = abstention)."""
        premiere_basse = self._tranches[0][0]
        derniere_haute = self._tranches[-1][1]
        frontieres = {premiere_basse} | {t[1] for t in self._tranches}
        for coupe in (float(_AGE_FIN_JEUNES), float(_AGE_DEBUT_AGES)):
            if premiere_basse < coupe < derniere_haute and coupe not in frontieres:
                raise ValueError(f"taux_dependance : l'âge {coupe} coupe une tranche en deux "
                                 f"(frontières {sorted(frontieres)}) ; découper exigerait une hypothèse")
        jeunes = sum(h + f for (b, ht, h, f) in self._tranches if ht <= _AGE_FIN_JEUNES)
        ages = sum(h + f for (b, ht, h, f) in self._tranches if b >= _AGE_DEBUT_AGES)
        actifs = self.effectif_total() - jeunes - ages
        if actifs == 0:
            raise ValueError("taux_dependance indéfini : 0 personne d'âge actif (15-64 ans)")
        return _sig(float(Fraction((jeunes + ages) * 100, actifs)))
