"""
RÉSOLUTION CHAÎNÉE (2026-06-22, point 4 : brancher l'auto-création sur le moteur principal SANS le modifier).

`resoudre_tout` = le moteur PRINCIPAL (`demande`, 73 étages + means-end) d'ABORD ; s'il rend HORS et que la tâche est
MONO-ARG, la BOUCLE AUTONOME (`auto_apprend.MoteurAutonome` : invente le vocabulaire manquant + recherche dirigée +
chaînes) prend le relais en DERNIER RECOURS. Le candidat autonome n'est RETENU que s'il passe le juge sur le visible ET
le held-out (soundness : jamais un faux ; pas d'oracle dans ce contexte -> pas d'active learning, on exige la preuve
held-out). `demande.py` reste intact -> zéro régression sur les validations existantes.
"""
from __future__ import annotations

from auto_apprend import MoteurAutonome
from auto_invention_ouverte import LIM
from demande import _asserts, demande
from juge import juge
from taches import Tache


def resoudre_tout(point_entree: str, signature: str, exemples, exemples_held=None, budget: int = 2000):
    """Renvoie (origine, code) : origine ∈ {'principal','auto-invention','HORS'}. `exemples`/`exemples_held` =
    [(entrée, sortie), …] (entrée = l'argument direct ; tâches MONO-ARG pour le relais autonome)."""
    # 1) MOTEUR PRINCIPAL (la voie normale, riche, optimisée).
    ex_pairs = [((a,), o) for a, o in exemples]
    held_pairs = [((a,), o) for a, o in exemples_held] if exemples_held else None
    rep = demande(point_entree, signature, ex_pairs, held_pairs)
    if rep.ok:
        return ("principal", rep.code)

    # 2) DERNIER RECOURS : la boucle AUTONOME (mono-arg uniquement).
    if "," in signature:
        return ("HORS", None)
    m = MoteurAutonome()
    m.explore_combine(budget=budget)
    t = Tache(id=point_entree, point_entree=point_entree, prompt=f"def {point_entree}(x):\n  pass",
              tests=_asserts(point_entree, ex_pairs), tests_held_out="")
    r = m.resoudre_confiant(t, exemples)
    if r["etat"] == "hors":                       # gap -> l'IA étend son vocabulaire puis réessaie
        m.etend_vocabulaire(exemples)
        m.etend_composition(exemples)
        r = m.resoudre_confiant(t, exemples)
    expr = r.get("expr")
    if expr:
        code = f"def {point_entree}(x):\n    return {expr}\n"
        ok = juge(code, _asserts(point_entree, ex_pairs), LIM).passe
        if ok and held_pairs:                     # SOUNDNESS : exiger la généralisation held-out
            ok = juge(code, _asserts(point_entree, held_pairs), LIM).passe
        if ok:
            return ("auto-invention", code)
    return ("HORS", None)


if __name__ == "__main__":
    from garde_ressources import borne
    borne()
    print("=== RÉSOLUTION CHAÎNÉE (principal -> auto-invention -> HORS) ===\n")
    DEMANDES = [
        # tâche que le moteur principal résout normalement
        ("somme_carres", "xs", [([1, 2, 3], 14), ([2, 3], 13)], [([5], 25), ([0, 4], 16)]),
        # tâches « inconnues » mono-arg -> relais autonome (held-out exigé)
        ("renverse_str", "x", [("abc", "cba"), ("hello", "olleh")], [("xy", "yx"), ("a", "a")]),
        ("somme_cubes", "x", [([1, 2], 9), ([2, 3], 35), ([1, 1, 1], 3)], [([2, 2], 16), ([3], 27)]),
        ("deuxieme", "x", [([9, 8, 7], 8), ([3, 9, 1], 9)], [([5, 6, 7], 6)]),   # held adverse non trié
        ("incoherent", "x", [([3, 1, 2], 42)], [([5], 99)]),                     # -> HORS honnête
    ]
    for spec in DEMANDES:
        pe, sig, ex, held = spec
        origine, code = resoudre_tout(pe, sig, ex, held)
        ligne = code.split("return ")[1].strip()[:48] if code else "—"
        print(f"  {pe:14s} [{origine:13s}] {ligne}")
