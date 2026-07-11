"""
MATÉRIALISATION D'UNE BRIQUE — la sortie de première classe DURABLE (chantier FORGE, piste (a)).

`ia.forge_brique` sert une brique en mémoire (JSON) ; le mandat de Yohan veut qu'elle serve aussi « aux
autres moteurs » et à l'utilisateur. Ce module GRAVE une brique apprise en artefact réutilisable HORS
processus : un module `.py` importable (la fonction + sa provenance) ET sa gate auto-écrite qui RE-EXÉCUTE
le spec — le FAIT borné se re-prouve seul, sans rien importer du moteur (auto-portant).

FAUX=0 / innocuité (héritent des atomes 1 et 7) : on ne grave QUE ce qui (a) reproduit son spec ICI, et
(b) est jugé SÛR par `expression_sure` — jamais de code faux ni hostile écrit sur disque. Rien n'est gravé
si l'une des deux gardes tombe (retour None, raison dite).
"""
from __future__ import annotations

import datetime
import keyword
import os
import re


def _identifiant(nom: str) -> str:
    """Nom de fonction/fichier VALIDE dérivé de `nom` (le moteur produit des noms parlants, pas toujours des
    identifiants). Non-alphanum -> '_', préfixe si commence par un chiffre, suffixe si mot-clé. Déterministe."""
    s = re.sub(r"\W", "_", nom).strip("_") or "brique"
    if s[0].isdigit():
        s = "b_" + s
    if keyword.iskeyword(s):
        s += "_"
    return s


def _rendu_module(ident: str, expr: str, origine: str, n: int, quand: str) -> str:
    return (f'"""Brique forgée « {ident} » (origine : {origine}, {quand}).\n'
            f'FAIT borné au spec : reproduit ses {n} paires (spec+held) par exécution réelle ; audité sûr\n'
            f'(expression_sure). La GÉNÉRALISATION au-delà du spec reste une supposition. Régénéré par\n'
            f'ia.materialise_brique — ne pas éditer à la main."""\n\n\n'
            f'def {ident}(x):\n    return {expr}\n')


def _rendu_gate(ident: str, paires) -> str:
    return ('"""Gate AUTO-ÉCRITE : re-prouve la brique en RÉ-EXÉCUTANT son spec, sans rien importer du moteur\n'
            '(le FAIT borné se vérifie seul, hors processus). Sortie non nulle si une paire ne reproduit plus."""\n'
            f'from {ident} import {ident}\n\n'
            f'SPEC = {paires!r}\n\n'
            'echecs = 0\n'
            'for a, o in SPEC:\n'
            f'    r = {ident}(a)\n'
            '    if not (r == o and isinstance(r, bool) == isinstance(o, bool)):\n'
            '        echecs += 1\n'
            f'        print(f"  [XXX] {ident}({{a!r}}) = {{r!r}} attendu {{o!r}}")\n'
            f'print(f"== BRIQUE {ident} : {{len(SPEC) - echecs}}/{{len(SPEC)}} paires reproduites ==")\n'
            'assert echecs == 0\n')


def materialise_brique(nom: str, expr: str, spec, held, dossier: str, *, origine: str = "") -> dict | None:
    """Grave la brique en `<dossier>/<ident>.py` (+ `valide_<ident>.py`). Renvoie {ident, module, gate,
    n_verifie} ou None si refus (spec non reproduit ou expr non sûre — raison dans le champ 'refus').

    Ne dépend PAS d'un store : appelable sur n'importe quelle (expr, spec) déjà vérifiée par le moteur."""
    import expression_sure as ES
    import moteur_invention as MI

    paires = [(list(a) if isinstance(a, (list, tuple)) else a, o) for a, o in list(spec) + list(held or [])]
    # GARDE 1 (innocuité, atome 7) : jamais graver du code non audité — AVANT toute exécution.
    raison = ES.raison_danger(expr)
    if raison is not None:
        return {"refus": f"expression non sûre ({raison})"}
    # GARDE 2 (correction, atome 1) : la brique doit reproduire son spec ICI, sinon rien à graver.
    if not paires or not MI._reproduit(MI._callable(expr, "f"), paires):
        return {"refus": "l'expression ne reproduit pas son spec (rien de prouvé à graver)"}

    ident = _identifiant(nom)
    n = len(paires)
    quand = datetime.date.today().isoformat()
    os.makedirs(dossier, exist_ok=True)
    p_mod = os.path.join(dossier, f"{ident}.py")
    p_gate = os.path.join(dossier, f"valide_{ident}.py")
    with open(p_mod, "w", encoding="utf-8") as f:
        f.write(_rendu_module(ident, expr, origine or nom, n, quand))
    with open(p_gate, "w", encoding="utf-8") as f:
        f.write(_rendu_gate(ident, paires))
    return {"ident": ident, "module": p_mod, "gate": p_gate, "n_verifie": n, "refus": None}
