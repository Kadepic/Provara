"""
LOCALISATION DE FAUTE + RÉPARATION PAR RECHERCHE — le cycle debug→fix (code avancé, 2026-07-02).

POURQUOI : quand un code échoue des tests, LOCALISER l'élément responsable (spectrum-based : ce qui est exécuté
surtout par les tests qui ÉCHOUENT) puis PROPOSER/valider un patch, c'est le cœur du codage itératif — bien plus
efficace que la re-synthèse aveugle. Deux primitives :
  • `localise` : suspicion Ochiai par élément (ligne/instruction), à partir d'une couverture + des verdicts.
  • `repare` : cherche parmi des patches candidats le premier qui passe TOUT (y compris le held-out), sinon None.

FAUX=0 :
  • La suspicion est une MESURE, pas une affirmation de faute. L'élément le plus suspect est un CANDIDAT classé,
    jamais « le bug » certain — on rend les scores, la réalité (le juge) tranche.
  • Un patch n'est RÉPARÉ que s'il passe le prédicat `teste` fourni par l'appelant, qui DOIT inclure le held-out
    (un patch qui ne passe que les tests visibles est du sur-apprentissage -> rejeté). None si aucun ne répare.
Stdlib pur, déterministe (ordre stable), souverain.
"""
from __future__ import annotations

import math
import sys


def localise(couverture: dict, verdicts: dict) -> list:
    """Suspicion Ochiai par élément. `couverture` = {test: set(éléments exécutés)} ; `verdicts` = {test: passe:bool}.
    Renvoie [(element, score)] trié par suspicion décroissante (départage : score puis élément). Score ∈ [0, 1]."""
    echoues = [t for t, ok in verdicts.items() if not ok]
    passes = [t for t, ok in verdicts.items() if ok]
    nf = len(echoues)
    elements = set()
    for s in couverture.values():
        elements |= set(s)
    scores = []
    for e in elements:
        ef = sum(1 for t in echoues if e in couverture.get(t, ()))
        ep = sum(1 for t in passes if e in couverture.get(t, ()))
        denom = math.sqrt(nf * (ef + ep)) if (nf and (ef + ep)) else 0.0
        score = (ef / denom) if denom > 0 else 0.0
        scores.append((e, score))
    scores.sort(key=lambda es: (-es[1], repr(es[0])))
    return scores


def element_le_plus_suspect(couverture: dict, verdicts: dict):
    """L'élément de suspicion maximale (candidat #1), ou None si aucun test n'échoue / aucune couverture."""
    s = localise(couverture, verdicts)
    return s[0][0] if (s and s[0][1] > 0) else None


def couverture_python(fn, entrees) -> dict:
    """BONUS : capture les LIGNES exécutées de `fn` pour chaque entrée (via sys.settrace). Renvoie {entree_repr:
    set(no_ligne)}. Déterministe. (Ne trace que le fichier de `fn`.)"""
    fichier = fn.__code__.co_filename
    cov = {}
    for x in entrees:
        lignes = set()

        def tracer(frame, event, arg, _lignes=lignes):
            if event == "line" and frame.f_code.co_filename == fichier:
                _lignes.add(frame.f_lineno)
            return tracer

        sys.settrace(tracer)
        try:
            try:
                fn(x)
            except Exception:
                pass
        finally:
            sys.settrace(None)
        cov[repr(x)] = lignes
    return cov


def repare(candidats, teste) -> dict:
    """Cherche parmi `candidats` (itérable de patches) le PREMIER qui satisfait `teste(patch) -> bool`. `teste` DOIT
    inclure le held-out (sinon sur-apprentissage). Renvoie {repare: patch|None, essais: int, trouve: bool}."""
    essais = 0
    for patch in candidats:
        essais += 1
        try:
            if teste(patch):
                return {"repare": patch, "essais": essais, "trouve": True}
        except Exception:
            continue                                 # un patch qui plante le test n'est pas une réparation
    return {"repare": None, "essais": essais, "trouve": False}
