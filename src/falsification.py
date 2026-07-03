"""
FALSIFICATION ACTIVE — brique Vague 6 (Popper : chercher à RÉFUTER, pas à confirmer).

POURQUOI : une machine honnête ne cherche pas à conforter ses hypothèses mais à les BRISER. Une hypothèse (loi,
design, invariant) n'est crédible que si une recherche active de contre-exemple a ÉCHOUÉ à la réfuter. Confirmer ne
prouve rien ; ne pas réussir à réfuter (sur un large espace testé) corrobore — honnêtement, dans les limites testées.

MODÈLE : une hypothèse = un prédicat `h(x) -> bool` censé valoir sur tout un espace de candidats. `refute(h, espace)`
parcourt l'espace et renvoie le PREMIER contre-exemple (x tel que non h(x)), ou None si aucun trouvé.

FAUX=0 :
  • Un contre-exemple renvoyé est RÉEL (on re-vérifie que h(x) est bien faux) — jamais un faux positif de réfutation.
  • Aucun contre-exemple trouvé -> `corrobore` renvoie « non réfutée dans l'espace testé » (JAMAIS « prouvée » : on
    est honnête sur la portée finie de la recherche).
  • Déterministe (parcours ordonné) ; borné (espace fini ou cap).
Stdlib pur, souverain.
"""
from __future__ import annotations


def refute(hypothese, espace, cap: int = 10 ** 7):
    """Cherche activement un contre-exemple de `hypothese` (prédicat) dans `espace` (itérable de candidats).
    Renvoie le premier x tel que hypothese(x) est faux (ou lève), RE-VÉRIFIÉ ; None si aucun trouvé (dans le cap)."""
    n = 0
    for x in espace:
        n += 1
        if n > cap:
            break
        try:
            ok = bool(hypothese(x))
        except Exception:
            return x                             # une hypothèse qui plante sur un cas = réfutée par ce cas
        if not ok:
            # re-vérification du contre-exemple (FAUX=0 : on ne renvoie que de VRAIS contre-exemples)
            try:
                if not bool(hypothese(x)):
                    return x
            except Exception:
                return x
    return None


def corrobore(hypothese, espace, cap: int = 10 ** 7):
    """(non_refutee: bool, contre_exemple). non_refutee=True signifie « aucun contre-exemple dans l'espace testé »
    — corroboration, PAS preuve. Honnête sur la portée finie."""
    ce = refute(hypothese, espace, cap)
    return (ce is None, ce)


def resiste(hypothese, espace, cap: int = 10 ** 7) -> bool:
    """Raccourci : True ssi l'hypothèse résiste à la falsification sur tout l'espace testé (aucun contre-exemple)."""
    return refute(hypothese, espace, cap) is None
