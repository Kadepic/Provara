"""
CYBERNÉTIQUE BORNÉE — régulation & rétroaction (boucle de commande), bloc « FORMULE » (mandat Yohan : couvrir le
borné jugeable par la réalité). Même posture que `physique` / `maths_discretes` :
  • Le MÉCANISME (l'algèbre de la boucle asservie) est EXACT — c'est la garantie structurelle, pas une heuristique.
  • Les sorties sont ARRONDIES à 10 chiffres significatifs — précision HONNÊTE (on n'invente pas de décimales).
  • ABSTENTION STRUCTURELLE : toute entrée invalide (type non numérique, valeur non finie, dénominateur nul =
    système singulier/instable, gain de retour nul…) lève ValueError — JAMAIS un nombre faux.
  • Déterministe ; conservateur : faux négatif (abstention) toléré, faux POSITIF interdit.

MODÈLE (rétroaction NÉGATIVE, schéma standard de l'automatique) :
        consigne ──►(Σ)──► [ G ] ──┬──► sortie
                     ▲             │
                     └──[ H ]◄─────┘
  où G = gain de la chaîne directe (open loop), H = gain de la chaîne de retour (feedback factor).

  • gain_boucle_fermee(G, H) = G / (1 + G·H)          — transmittance en boucle fermée (closed loop)
  • erreur_statique(consigne, G) = consigne / (1 + G) — erreur permanente à un échelon (retour unitaire, système
                                                        de type 0 : ess = 1/(1+Kp), Kp = G)
  • fonction_sensibilite(G, H)  = 1 / (1 + G·H)       — S : sensibilité de la sortie aux perturbations
  • transfert_complementaire(G, H) = G·H / (1 + G·H)  — T : suivi de consigne ;  IDENTITÉ  S + T = 1
  • gain_ideal(H) = 1 / H                              — limite du gain en boucle fermée quand G → ∞
  • est_stable(G, H)                                   — vrai ssi 1 + G·H ≠ 0 et le gain est fini
  • effet_retroaction_negative(G1, G2, H)             — propriété : augmenter le gain direct (G2 > G1 ≥ 0, H > 0)
                                                        RAPPROCHE le gain en boucle fermée de 1/H (l'écart décroît).

CAS DE RÉFÉRENCE : G=10,H=1 → 10/11 ≈ 0.9090909091 ;  G=100,H=0.1 → 100/11 ≈ 9.090909091 ;
                   G→∞ → gain → 1/H ;  retour unitaire G→∞ → erreur statique → 0.
"""
from __future__ import annotations

import math

_SIG = 10  # chiffres significatifs rendus (précision honnête)


def _sig(x: float, n: int = _SIG) -> float:
    """Arrondit à n chiffres significatifs (indépendant de la magnitude)."""
    if x == 0:
        return 0.0
    return float(f"{x:.{n}g}")


def _num(x, nom: str) -> float:
    """Coerce en flottant fini ou lève ValueError (abstention structurelle). Refuse bool (pas un scalaire physique)."""
    if isinstance(x, bool):
        raise ValueError(f"{nom} : booléen refusé (pas un gain)")
    if not isinstance(x, (int, float)):
        raise ValueError(f"{nom} : type non numérique ({type(x).__name__})")
    xf = float(x)
    if not math.isfinite(xf):
        raise ValueError(f"{nom} : valeur non finie")
    return xf


def gain_boucle_fermee(G, H) -> float:
    """Transmittance en boucle fermée G/(1+G·H). 1+G·H = 0 (singulier) ou gain non fini -> ValueError."""
    g = _num(G, "G")
    h = _num(H, "H")
    denom = 1.0 + g * h
    if denom == 0.0:
        raise ValueError("1 + G·H = 0 : boucle singulière (instable), pas de gain fini")
    val = g / denom
    if not math.isfinite(val):
        raise ValueError("gain non fini (débordement)")
    return _sig(val)


def erreur_statique(consigne, G) -> float:
    """Erreur statique consigne/(1+G) (retour unitaire, échelon). 1+G = 0 -> ValueError."""
    c = _num(consigne, "consigne")
    g = _num(G, "G")
    denom = 1.0 + g
    if denom == 0.0:
        raise ValueError("1 + G = 0 : erreur statique indéfinie")
    val = c / denom
    if not math.isfinite(val):
        raise ValueError("erreur statique non finie")
    return _sig(val)


def fonction_sensibilite(G, H) -> float:
    """Fonction de sensibilité S = 1/(1+G·H). 1+G·H = 0 -> ValueError."""
    g = _num(G, "G")
    h = _num(H, "H")
    denom = 1.0 + g * h
    if denom == 0.0:
        raise ValueError("1 + G·H = 0 : sensibilité indéfinie")
    val = 1.0 / denom
    if not math.isfinite(val):
        raise ValueError("sensibilité non finie")
    return _sig(val)


def transfert_complementaire(G, H) -> float:
    """Transfert complémentaire T = G·H/(1+G·H) (S + T = 1). 1+G·H = 0 -> ValueError."""
    g = _num(G, "G")
    h = _num(H, "H")
    denom = 1.0 + g * h
    if denom == 0.0:
        raise ValueError("1 + G·H = 0 : transfert indéfini")
    val = (g * h) / denom
    if not math.isfinite(val):
        raise ValueError("transfert non fini")
    return _sig(val)


def gain_ideal(H) -> float:
    """Limite du gain en boucle fermée quand G → ∞ : 1/H. H = 0 -> ValueError (pas de retour, pas de limite)."""
    h = _num(H, "H")
    if h == 0.0:
        raise ValueError("H = 0 : aucune rétroaction, le gain ne tend pas vers une limite finie")
    val = 1.0 / h
    if not math.isfinite(val):
        raise ValueError("gain idéal non fini")
    return _sig(val)


def est_stable(G, H) -> bool:
    """Vrai ssi 1 + G·H ≠ 0 ET le gain est fini. Types invalides -> ValueError (jamais un faux booléen)."""
    g = _num(G, "G")
    h = _num(H, "H")
    denom = 1.0 + g * h
    if denom == 0.0:
        return False
    return math.isfinite(g / denom)


def effet_retroaction_negative(G1, G2, H) -> bool:
    """
    Propriété FONDATRICE de la rétroaction négative : avec H > 0 et 0 ≤ G1 < G2, augmenter le gain direct
    RAPPROCHE le gain en boucle fermée de la valeur idéale 1/H. On le PROUVE numériquement : l'écart
    |gain(G,H) − 1/H| décroît strictement de G1 à G2. Renvoie True dans ce régime.
    Domaine hors régime (G1 < 0, G2 ≤ G1, H ≤ 0) -> ValueError (abstention, pas de faux positif).
    """
    g1 = _num(G1, "G1")
    g2 = _num(G2, "G2")
    h = _num(H, "H")
    if not (h > 0.0):
        raise ValueError("H ≤ 0 hors du régime de rétroaction négative étudié")
    if g1 < 0.0:
        raise ValueError("G1 < 0 hors domaine (gain direct ≥ 0)")
    if not (g2 > g1):
        raise ValueError("G2 ≤ G1 : pas d'augmentation du gain direct")
    cible = 1.0 / h
    ecart1 = abs(g1 / (1.0 + g1 * h) - cible)
    ecart2 = abs(g2 / (1.0 + g2 * h) - cible)
    return ecart2 < ecart1
