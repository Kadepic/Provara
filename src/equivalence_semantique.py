"""
ÉQUIVALENCE SÉMANTIQUE DE FONCTIONS — décider si deux fonctions calculent la MÊME chose (code avancé, 2026-07-02).

POURQUOI : c'est le PRÉREQUIS du refactor préservant-le-comportement (adopter une variante plus propre SEULEMENT si
elle calcule exactement la même fonction) et de la déduplication de solutions. « Vérifier, pas plausibiliser » :
on ne CROIT pas deux codes équivalents, on le PROUVE (domaine fini exhaustif) ou on cherche activement à les
DISTINGUER (property-based + shrinking).

FAUX=0 — la ligne rouge :
  • EQUIVALENTES n'est affirmé QUE par vérification EXHAUSTIVE sur un domaine FINI énuméré (chaque point testé,
    f(x)==g(x) partout). Certitude réelle, bornée au domaine.
  • Sur un domaine infini/échantillonné : soit DIFFERENTES (un contre-exemple x où f(x)≠g(x), re-vérifiable, réduit),
    soit NON_DISTINGUEES (aucune différence en N essais) — ce dernier n'est PAS « équivalentes » (honnête sur la limite).
  • Une exception d'un seul côté sur un x compte comme une DIFFÉRENCE (comportements distincts).
Stdlib pur, déterministe (RNG seedé), souverain. Compose avec property_based (shrinking du contre-exemple).
"""
from __future__ import annotations

EQUIVALENTES = "equivalentes"       # prouvé sur un domaine fini exhaustif
DIFFERENTES = "differentes"         # contre-exemple trouvé (certain)
NON_DISTINGUEES = "non_distinguees"  # aucune différence en N essais (PAS une preuve d'équivalence)


def _resultat(f, x):
    """(ok, valeur) : ok=False si f(x) lève -> le comportement 'exception' est une valeur observable distincte."""
    try:
        return (True, f(x))
    except Exception as ex:
        return (False, type(ex).__name__)


def _distincts(f, g, x) -> bool:
    return _resultat(f, x) != _resultat(g, x)


def sur_domaine(f, g, domaine) -> dict:
    """Vérifie l'équivalence EXHAUSTIVEMENT sur un `domaine` FINI énumérable. Renvoie {statut, contre_exemple}.
    statut = EQUIVALENTES (aucune différence sur TOUT le domaine) ou DIFFERENTES (1er point distinct)."""
    for x in domaine:
        if _distincts(f, g, x):
            return {"statut": DIFFERENTES, "contre_exemple": x}
    return {"statut": EQUIVALENTES, "contre_exemple": None}


def par_echantillon(f, g, generateur, n: int = 500, graine: int = 0) -> dict:
    """Cherche activement à DISTINGUER f et g sur `n` entrées de `generateur(rng)`. Renvoie {statut, contre_exemple}.
    statut = DIFFERENTES (contre-exemple réduit) ou NON_DISTINGUEES (aucune différence en n essais — jamais
    « équivalentes »). FAUX=0 : le contre-exemple, s'il existe, distingue RÉELLEMENT f et g (re-vérifiable + réduit)."""
    import property_based
    # une "propriété" = f et g s'accordent sur x ; property_based cherche un x qui la viole (les distingue)
    r = property_based.pour_tout(lambda x: not _distincts(f, g, x), generateur, n=n, graine=graine)
    if r["refute"]:
        ce = r["contre_exemple"]
        if _distincts(f, g, ce):                 # garde FAUX=0 : le contre-exemple distingue bien
            return {"statut": DIFFERENTES, "contre_exemple": ce}
    return {"statut": NON_DISTINGUEES, "contre_exemple": None}


def equivalent(f, g, domaine=None, generateur=None, n: int = 500, graine: int = 0) -> dict:
    """Façade : si un `domaine` FINI est fourni -> preuve exhaustive (EQUIVALENTES/DIFFERENTES) ; sinon échantillonnage
    (DIFFERENTES/NON_DISTINGUEES). FAUX=0 : ne rend EQUIVALENTES que sur un domaine fini exhaustif."""
    if domaine is not None:
        return sur_domaine(f, g, domaine)
    if generateur is not None:
        return par_echantillon(f, g, generateur, n=n, graine=graine)
    raise ValueError("fournir un domaine fini (preuve) OU un generateur (échantillon)")
