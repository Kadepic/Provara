"""
PROPERTY-BASED TESTING — falsification active d'un invariant (brique vérification/code avancé, 2026-07-02).

POURQUOI : « vérifier, pas plausibiliser ». Au lieu d'accepter une propriété sur quelques cas triés, on GÉNÈRE des
centaines d'entrées et on cherche ACTIVEMENT un contre-exemple ; s'il existe, on le RÉDUIT (delta_debug / dichotomie)
au plus petit reproducteur. C'est le harnais de falsification générique (Popper mécanisé) qui manquait, réutilisable
pour toute loi/fonction/invariant.

FAUX=0 — l'honnêteté du test :
  • On ne déclare JAMAIS une propriété « vraie » / « prouvée ». Au mieux « non réfutée en N essais » (le testing ne
    prouve pas l'universel). refute=False n'est PAS une garantie.
  • refute=True est un FAIT : le `contre_exemple` VIOLE réellement la propriété (re-vérifiable), et le shrinking
    PRÉSERVE la violation (le reproducteur minimal réfute toujours).
  • Déterministe : RNG seedé -> même graine, même verdict/contre-exemple.
Stdlib pur, souverain. `propriete(x) -> bool` et `generateur(rng) -> x` sont fournis par l'appelant.
"""
from __future__ import annotations

import random

import delta_debug


def _reduit_auto(x, viole):
    """Shrinking générique préservant la violation (`viole(v) == True`). Séquences -> ddmin ; entiers -> dichotomie
    vers 0 (signe conservé) ; autre -> inchangé. Le résultat réfute TOUJOURS (FAUX=0)."""
    if isinstance(x, bool):
        return x
    if isinstance(x, int):
        signe = -1 if x < 0 else 1
        v = abs(x)
        # cherche le plus petit |v| (>=0) qui viole encore, par recherche décroissante bornée-log
        meilleur = v
        pas = v
        while pas > 0:
            cand = meilleur - pas
            if cand >= 0 and viole(signe * cand):
                meilleur = cand
            else:
                pas //= 2
        return signe * meilleur
    if isinstance(x, (list, tuple)):
        red = delta_debug.ddmin(list(x), lambda s: viole(type(x)(s)))
        return type(x)(red)
    if isinstance(x, str):
        return delta_debug.minimise_texte(x, lambda s: viole(s))
    return x


def pour_tout(propriete, generateur, n: int = 200, graine: int = 0, reduit=None) -> dict:
    """Cherche un contre-exemple à `propriete` sur `n` entrées de `generateur(rng)`. Renvoie
      {refute: bool, contre_exemple: x|None, essais: int, minimise: bool}.
    refute=True -> contre_exemple viole réellement la propriété (réduit au plus petit reproducteur)."""
    rng = random.Random(graine)
    viole = lambda x: not _sur(propriete, x)
    for i in range(1, n + 1):
        x = generateur(rng)
        if not _sur(propriete, x):
            xr = (reduit or _reduit_auto)(x, viole)
            if not viole(xr):                        # garde FAUX=0 : ne renvoyer QUE si le réduit réfute encore
                xr = x
            return {"refute": True, "contre_exemple": xr, "essais": i, "minimise": xr != x}
    return {"refute": False, "contre_exemple": None, "essais": n, "minimise": False}


def _sur(propriete, x) -> bool:
    """Évalue `propriete(x)` en traitant une exception comme une VIOLATION (un crash est un échec de la propriété)."""
    try:
        return bool(propriete(x))
    except Exception:
        return False
