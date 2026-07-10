"""
BILAN ÉNERGÉTIQUE d'un système décrit par des flux de puissance (watts).

Même posture FAUX=0 que `physique` / `coherence_physique` (la réalité/le théorème juge, jamais un faux) :
  • Le MÉCANISME est le PREMIER PRINCIPE DE LA THERMODYNAMIQUE (conservation de l'énergie) appliqué en
    régime de puissance : pour un système décrit par des flux,
        P_entrant = P_sortant + P_pertes + P_stocké,
    donc l'ÉCART  e = entrant − sortant − pertes − stocké  DOIT être nul pour un système bouclé.
    Un écart non nul n'est JAMAIS absorbé en silence : il est NOMMÉ (excédent ou déficit chiffré).
  • PLANCHER D'INDISCERNABILITÉ IEEE754 : les flux sont des flottants binaires ; la somme/différence
    de valeurs décimales banales laisse un résidu d'arrondi (ex. 0.3 − 0.1 − 0.2 = −5.55e-17 en double).
    Ce résidu est du BRUIT DE REPRÉSENTATION, pas de la physique : l'affirmer comme anomalie serait un
    FAUX POSITIF — interdit. Tout |écart| ≤ plancher est donc traité comme NUL, où le plancher est la
    borne classique d'erreur de sommation flottante (Higham, « Accuracy and Stability of Numerical
    Algorithms », §4.2 : |erreur| ≤ n·eps·Σ|xᵢ|) prise avec un facteur de sécurité 4. Un écart AU-DESSUS
    du plancher reste nommé, jamais absorbé (le plancher ne masque pas les vraies anomalies : pour des
    flux de l'ordre du watt il vaut ~1e-15 W).
  • Le RENDEMENT η = utile / entrant (utile = somme des flux 'sortant') ne peut JAMAIS dépasser 1 :
    η > 1 violerait le premier principe -> ValueError. De plus, `rendement()` EXIGE que le bilan boucle
    du côté impossible : un DÉFICIT au-delà du plancher (sortant + pertes + stocké > entrant, c'est-à-dire
    une CRÉATION d'énergie) -> ValueError même si η ≤ 1 — un rendement « plausible » calculé sur un
    système physiquement impossible serait un faux (cœur du FAUX=0 ici). Un EXCÉDENT (entrant non
    entièrement expliqué) est toléré pour η : il signifie des pertes non déclarées, ce qui ne change pas
    η = utile/entrant ; sans aucune perte déclarée, un UserWarning est émis (bilan probablement incomplet).
  • DÉDUCTION D'UN FLUX MANQUANT : le bilan fournit UNE équation ; si exactement UNE valeur est inconnue
    (None), elle est déduite (système déterminé) ; si N > 1 valeurs sont inconnues, le système est
    sous-déterminé -> ValueError ('sous-déterminé : N inconnues, 1 équation'). Jamais une devinette.
    Une valeur déduite dont la magnitude est ≤ plancher est rendue comme 0.0 (le résidu est du bruit) ;
    une valeur déduite négative AU-DELÀ du plancher -> ValueError (flux déclarés incohérents).
  • Les sorties flottantes sont ARRONDIES à 10 chiffres significatifs — précision honnête.

GARANTIES (vérifiées en adverse par `valide_bilan_energetique.py`) :
  - valeur de flux négative -> ValueError (un flux est une grandeur orientée par son `sens` ; une valeur
    négative serait un sens déguisé — on refuse plutôt que d'interpréter) ;
  - sens hors de {'entrant', 'sortant', 'stocke'} -> ValueError ;
  - nom vide, nom dupliqué (ambiguïté), système vide -> ValueError ;
  - tol < 0 -> ValueError ; rendement > 1 -> ValueError (1er principe) ; entrant nul -> ValueError ;
  - bilan en DÉFICIT au-delà du plancher -> rendement -> ValueError (création d'énergie, abstention) ;
  - AUCUN faux positif IEEE754 : 0.3 entrant / 0.1 + 0.2 sortant est bouclé (écart 0, conserve(0.0) True,
    bilan_incoherent None) ; un déficit RÉEL de 1e-9 W reste détecté (le plancher ne masque rien) ;
  - bilan/rendement/conserve exigent des valeurs TOUTES connues (une inconnue -> ValueError, il faut
    passer par flux_manquant) ;
  - flux_manquant déduisant une valeur NÉGATIVE au-delà du plancher -> ValueError (flux incohérents) ;
    sous le plancher, la déduction vaut 0.0 (bruit, pas incohérence) ;
  - types invalides (bool, str, NaN, ±inf) -> ValueError ;
  - déterministe ; conservateur (faux négatif/abstention toléré, faux POSITIF interdit).

Le module n'importe que `math`, `sys` et `warnings` (stdlib). Aucune dépendance graphique : le diagramme
de Sankey est TEXTUEL (barres proportionnelles en caractères).
"""
from __future__ import annotations

import math
import sys
import warnings

SOURCE = ("premier principe de la thermodynamique (conservation de l'énergie, Clausius 1850) : "
          "P_entrant = P_sortant + P_pertes + P_stocké ; rendement η = P_utile/P_entrant ≤ 1 ; "
          "plancher d'indiscernabilité flottante : borne de sommation n·eps·Σ|xᵢ| (Higham §4.2)")

_SENS_VALIDES = ("entrant", "sortant", "stocke")
_CHIFFRES_SIGNIFICATIFS = 10
_FACTEUR_SECURITE_IEEE = 4  # marge sur la borne d'erreur de sommation (Higham §4.2 : n·eps·Σ|xᵢ|)


def _sig(x: float, n: int = _CHIFFRES_SIGNIFICATIFS) -> float:
    """Arrondit à n chiffres significatifs (précision honnête, indépendante de la magnitude)."""
    if x == 0:
        return 0.0
    return float(f"{x:.{n}g}")


def _est_reel(x) -> bool:
    """True ssi x est un réel fini (les bool sont REFUSÉS : True n'est pas une mesure)."""
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x)


def _plancher_ieee(entrant: float, sortant: float, pertes: float, stocke: float, n_valeurs: int) -> float:
    """Plancher d'indiscernabilité IEEE754 du bilan : borne supérieure de l'erreur d'arrondi accumulée
    par la somme/différence des flux (tous ≥ 0, donc Σ|xᵢ| = Σxᵢ).

    Borne classique de sommation flottante : |erreur| ≤ n·eps·Σ|xᵢ| (Higham, « Accuracy and Stability
    of Numerical Algorithms », §4.2), prise avec le facteur de sécurité _FACTEUR_SECURITE_IEEE.
    Un |écart| ≤ plancher est INDISCERNABLE de zéro : l'affirmer comme anomalie serait un FAUX POSITIF
    (bruit de représentation binaire, pas de la physique)."""
    somme_magnitudes = entrant + sortant + pertes + stocke
    return _FACTEUR_SECURITE_IEEE * max(1, n_valeurs) * sys.float_info.epsilon * somme_magnitudes


def _exige_nom(nom) -> str:
    if not isinstance(nom, str) or not nom.strip():
        raise ValueError("nom de flux invalide : une chaîne non vide est requise")
    return nom.strip()


def _exige_valeur_ou_none(valeur, contexte: str):
    """Valeur d'un flux : None (inconnue, à déduire) OU un réel fini ≥ 0 (watts).

    Une valeur NÉGATIVE est refusée : le sens du flux est porté par `sens`, pas par le signe —
    accepter un signe serait interpréter à la place de l'énoncé (FAUX=0)."""
    if valeur is None:
        return None
    if not _est_reel(valeur):
        raise ValueError(f"{contexte} : valeur invalide (réel fini requis ; bool/str/NaN/inf refusés)")
    if valeur < 0:
        raise ValueError(f"{contexte} : valeur négative refusée (le sens est porté par le champ `sens`, "
                         f"pas par le signe ; déclarez le flux dans l'autre sens)")
    return float(valeur)


def _exige_tolerance(tol) -> float:
    if not _est_reel(tol) or tol < 0:
        raise ValueError("tolérance invalide : un réel fini ≥ 0 est requis")
    return float(tol)


class Systeme:
    """Système énergétique décrit par des flux nommés (watts) + pertes nommées.

    Chaque flux a un `sens` ∈ {'entrant', 'sortant', 'stocke'} ; les pertes sont un canal dédié
    (elles comptent négativement dans le bilan, comme les sorties). Une valeur None = inconnue,
    déductible par `flux_manquant()` si et seulement si elle est la SEULE inconnue."""

    def __init__(self) -> None:
        self._flux: list = []    # liste de (nom, valeur_ou_None, sens)
        self._pertes: list = []  # liste de (nom, valeur_ou_None)

    # ── construction ──────────────────────────────────────────────────────────────────────────────
    def _exige_nom_libre(self, nom: str) -> None:
        deja = {n for (n, _v, _s) in self._flux} | {n for (n, _v) in self._pertes}
        if nom in deja:
            raise ValueError(f"nom de flux dupliqué : '{nom}' existe déjà (ambiguïté refusée)")

    def ajoute_flux(self, nom, valeur_watt, sens) -> None:
        """Déclare un flux. sens ∈ {'entrant','sortant','stocke'} ; valeur en watts ≥ 0 ou None (inconnue)."""
        nom = _exige_nom(nom)
        if not isinstance(sens, str) or sens not in _SENS_VALIDES:
            raise ValueError(f"sens de flux inconnu : {sens!r} (attendu : 'entrant', 'sortant' ou 'stocke')")
        valeur = _exige_valeur_ou_none(valeur_watt, f"flux '{nom}' ({sens})")
        self._exige_nom_libre(nom)
        self._flux.append((nom, valeur, sens))

    def ajoute_perte(self, nom, valeur_watt) -> None:
        """Déclare une perte (watts ≥ 0, ou None si inconnue)."""
        nom = _exige_nom(nom)
        valeur = _exige_valeur_ou_none(valeur_watt, f"perte '{nom}'")
        self._exige_nom_libre(nom)
        self._pertes.append((nom, valeur))

    # ── état interne ──────────────────────────────────────────────────────────────────────────────
    def _exige_non_vide(self) -> None:
        if not self._flux and not self._pertes:
            raise ValueError("système vide : aucun flux déclaré, aucun bilan possible")

    def _inconnues(self) -> list:
        """Liste des (nom, sens) dont la valeur est None ; sens='perte' pour les pertes."""
        res = [(n, s) for (n, v, s) in self._flux if v is None]
        res += [(n, "perte") for (n, v) in self._pertes if v is None]
        return res

    def _exige_tout_connu(self) -> None:
        inc = self._inconnues()
        if inc:
            noms = ", ".join(f"'{n}'" for (n, _s) in inc)
            raise ValueError(f"valeur(s) inconnue(s) : {noms} — utilisez flux_manquant() pour déduire "
                             f"l'unique inconnue, un bilan sur inconnues serait une devinette")

    def _sommes(self):
        """(entrant, sortant, pertes, stocke) — exige un système non vide, tout connu."""
        self._exige_non_vide()
        self._exige_tout_connu()
        entrant = sum(v for (_n, v, s) in self._flux if s == "entrant")
        sortant = sum(v for (_n, v, s) in self._flux if s == "sortant")
        stocke = sum(v for (_n, v, s) in self._flux if s == "stocke")
        pertes = sum(v for (_n, v) in self._pertes)
        return float(entrant), float(sortant), float(pertes), float(stocke)

    def _bilan_brut(self):
        """(entrant, sortant, pertes, stocke, ecart, plancher) — l'écart est mis à 0.0 exactement si sa
        magnitude est ≤ plancher IEEE754 (résidu de représentation binaire, pas une anomalie physique :
        le rapporter comme écart serait un faux positif). Au-delà du plancher, l'écart est rendu brut."""
        entrant, sortant, pertes, stocke = self._sommes()
        ecart = entrant - sortant - pertes - stocke
        plancher = _plancher_ieee(entrant, sortant, pertes, stocke,
                                  len(self._flux) + len(self._pertes))
        if abs(ecart) <= plancher:
            ecart = 0.0
        return entrant, sortant, pertes, stocke, ecart, plancher

    # ── (b) bilan ─────────────────────────────────────────────────────────────────────────────────
    def bilan(self) -> dict:
        """Bilan général : {entrant, sortant, pertes, stocke, ecart} en watts.

        ecart = entrant − sortant − pertes − stocke (1er principe : nul si le système est bouclé).
        Un écart de magnitude ≤ plancher IEEE754 est rapporté 0.0 (bruit de représentation)."""
        entrant, sortant, pertes, stocke, ecart, _plancher = self._bilan_brut()
        return {
            "entrant": _sig(entrant),
            "sortant": _sig(sortant),
            "pertes": _sig(pertes),
            "stocke": _sig(stocke),
            "ecart": _sig(ecart),
        }

    # ── (c) invariant : 1er principe ──────────────────────────────────────────────────────────────
    def conserve(self, tol) -> bool:
        """True ssi |ecart| ≤ max(tol, plancher IEEE754) (le système boucle son bilan).

        tol < 0 -> ValueError. Le plancher garantit qu'un résidu de flottant binaire (0.3−0.1−0.2)
        ne rend jamais False à tort — le faux positif est interdit, même avec tol=0."""
        tol = _exige_tolerance(tol)
        _e, _s, _p, _st, ecart, _plancher = self._bilan_brut()
        return abs(ecart) <= tol

    def bilan_incoherent(self, tol=0.0):
        """None si le bilan boucle (|ecart| ≤ max(tol, plancher IEEE754)) ; sinon une phrase NOMMANT
        l'anomalie chiffrée :

          ecart > 0 -> 'EXCÉDENT non expliqué de X W' (de l'énergie entre sans destination déclarée) ;
          ecart < 0 -> 'DÉFICIT non expliqué de X W'  (il sort plus d'énergie qu'il n'en entre).

        Le module ne l'absorbe JAMAIS en silence : l'anomalie est explicite ou le bilan est bouclé.
        Le plancher IEEE754 empêche de nommer comme anomalie un simple résidu de flottant binaire."""
        tol = _exige_tolerance(tol)
        entrant, sortant, pertes, stocke, ecart, _plancher = self._bilan_brut()
        if abs(ecart) <= tol:
            return None
        if ecart > 0:
            return (f"EXCÉDENT non expliqué de {_sig(ecart)} W : il entre {_sig(entrant)} W mais seuls "
                    f"{_sig(sortant + pertes + stocke)} W sont expliqués (sortant + pertes + stocké)")
        return (f"DÉFICIT non expliqué de {_sig(-ecart)} W : il sort {_sig(sortant + pertes + stocke)} W "
                f"(sortant + pertes + stocké) mais seuls {_sig(entrant)} W entrent")

    # ── (d) rendement ─────────────────────────────────────────────────────────────────────────────
    def rendement(self) -> float:
        """Rendement η = utile / entrant, avec utile = somme des flux 'sortant'.

        Abstentions (ValueError) — cœur du FAUX=0 :
          • entrant nul (division par zéro refusée) ;
          • η > 1 au-delà du plancher (violation du 1er principe : jamais rendre un rendement > 1) ;
          • bilan en DÉFICIT au-delà du plancher (sortant + pertes + stocké > entrant : le système
            décrit CRÉE de l'énergie ; un η « plausible » calculé dessus serait un faux, même s'il
            est ≤ 1).
        Un EXCÉDENT (entrant non entièrement expliqué) est toléré : il signifie des pertes non
        déclarées et ne change pas η = utile/entrant. Aucune perte déclarée -> UserWarning (bilan
        probablement incomplet : un dispositif réel dissipe toujours quelque chose)."""
        entrant, sortant, pertes, stocke, ecart, _plancher = self._bilan_brut()
        if entrant <= 0:
            raise ValueError("rendement indéfini : puissance entrante nulle (division par zéro refusée)")
        eta = sortant / entrant
        if ecart < 0:  # déficit AU-DELÀ du plancher (sinon ecart aurait été mis à 0) : impossible physiquement
            if eta > 1.0:
                raise ValueError(f"rendement {_sig(eta)} > 1 : violation du premier principe de la "
                                 f"thermodynamique ({_sig(sortant)} W utiles pour {_sig(entrant)} W entrants) "
                                 f"— jamais rendu, le système décrit est incohérent")
            raise ValueError(f"bilan non bouclé : DÉFICIT de {_sig(-ecart)} W — il sort "
                             f"{_sig(sortant + pertes + stocke)} W (sortant + pertes + stocké) pour "
                             f"{_sig(entrant)} W entrants, création d'énergie interdite par le premier "
                             f"principe de la thermodynamique ; un rendement calculé sur ce système "
                             f"serait un faux, abstention")
        if eta > 1.0:
            # ecart ≥ 0 après plancher : le dépassement de 1 est un résidu IEEE754 (ex. 0.3 entrant,
            # 0.1 + 0.2 sortant -> η = 1.0000000000000002). Le bilan boucle, donc η = 1 exactement.
            eta = 1.0
        if not self._pertes:
            warnings.warn("rendement calculé SANS aucune perte déclarée : bilan probablement incomplet "
                          "(un dispositif réel dissipe toujours de l'énergie)", UserWarning, stacklevel=2)
        return _sig(eta)

    # ── (e) diagramme de Sankey textuel ───────────────────────────────────────────────────────────
    def diagramme_sankey_texte(self, largeur=30) -> str:
        """Représentation textuelle des flux : une barre '█' proportionnelle par flux (aucune dépendance
        graphique). largeur = nombre de caractères de la plus grande barre (entier ≥ 1)."""
        if not isinstance(largeur, int) or isinstance(largeur, bool) or largeur < 1:
            raise ValueError("largeur invalide : un entier ≥ 1 est requis")
        entrant, sortant, pertes, stocke, ecart, _plancher = self._bilan_brut()
        lignes_source = ([(n, v, s) for (n, v, s) in self._flux]
                         + [(n, v, "perte") for (n, v) in self._pertes])
        maxi = max(v for (_n, v, _s) in lignes_source) if lignes_source else 0.0
        fleche = {"entrant": "──▶ [SYSTÈME]", "sortant": "[SYSTÈME] ──▶",
                  "stocke": "[SYSTÈME] ▣  ", "perte": "[SYSTÈME] ─▷ "}
        ordre = {"entrant": 0, "sortant": 1, "stocke": 2, "perte": 3}
        lignes = ["=== BILAN ÉNERGÉTIQUE (W) ==="]
        for (n, v, s) in sorted(lignes_source, key=lambda t: (ordre[t[2]], t[0])):
            barre = "█" * max(1, round(largeur * v / maxi)) if maxi > 0 and v > 0 else "·"
            lignes.append(f"{fleche[s]} {n:<20} {_sig(v):>12g} W {barre}")
        lignes.append(f"entrant={_sig(entrant):g}  sortant={_sig(sortant):g}  pertes={_sig(pertes):g}  "
                      f"stocke={_sig(stocke):g}  ecart={_sig(ecart):g}")
        return "\n".join(lignes)

    # ── (f) déduction de l'unique flux manquant ───────────────────────────────────────────────────
    def flux_manquant(self) -> dict:
        """Déduit l'UNIQUE valeur inconnue (None) du bilan bouclé (ecart = 0) : le bilan fournit UNE
        équation, donc exactement UNE inconnue est déductible.

        Renvoie {'nom', 'sens', 'valeur_watt'} sans modifier le système (fonction de lecture).
        0 inconnue -> ValueError (rien à déduire) ; N > 1 -> ValueError ('sous-déterminé') ;
        valeur déduite de magnitude ≤ plancher IEEE754 -> 0.0 (résidu binaire, pas une valeur) ;
        valeur déduite négative AU-DELÀ du plancher -> ValueError (les flux déclarés violent le
        1er principe — jamais un faux 'incohérent' sur du bruit de flottant)."""
        self._exige_non_vide()
        inconnues = self._inconnues()
        if not inconnues:
            raise ValueError("aucune inconnue : toutes les valeurs sont déjà connues, rien à déduire")
        if len(inconnues) > 1:
            raise ValueError(f"sous-déterminé : {len(inconnues)} inconnues, 1 équation "
                             f"(le bilan ne fournit qu'une seule équation de conservation)")
        (nom, sens) = inconnues[0]
        entrant = sum(v for (_n, v, s) in self._flux if s == "entrant" and v is not None)
        sortant = sum(v for (_n, v, s) in self._flux if s == "sortant" and v is not None)
        stocke = sum(v for (_n, v, s) in self._flux if s == "stocke" and v is not None)
        pertes = sum(v for (_n, v) in self._pertes if v is not None)
        # 1er principe : entrant = sortant + pertes + stocke ; on isole l'inconnue.
        if sens == "entrant":
            valeur = (sortant + pertes + stocke) - entrant
        else:  # sortant, stocke ou perte : tous du même côté de l'équation
            valeur = entrant - (sortant + pertes + stocke)
        plancher = _plancher_ieee(entrant, sortant, pertes, stocke,
                                  len(self._flux) + len(self._pertes))
        if abs(valeur) <= plancher:
            valeur = 0.0  # résidu IEEE754 (ex. 0.3 − 0.1 − 0.2) : la déduction est NULLE, pas incohérente
        if valeur < 0:
            raise ValueError(f"flux '{nom}' ({sens}) déduit NÉGATIF ({_sig(valeur)} W) : les flux déclarés "
                             f"sont incohérents (1er principe), déduction refusée")
        return {"nom": nom, "sens": sens, "valeur_watt": _sig(valeur)}
