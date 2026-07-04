#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FORMULATION NATURELLE PAR GABARITS — faire sonner Provara comme un PAIR, pas comme un formulaire (2026-07-04).

Un assistant qui répond « C'est noté. » au mot près à chaque fois sonne robotique. Ici : des BANQUES de variantes
par intention (accusé, inconnu, refus, salutation…) et un choix DÉTERMINISTE (hash stable de l'entrée) — même
message pour la même entrée (reproductible, testable), mais varié d'une entrée à l'autre. Zéro aléa non maîtrisé.

FAUX=0 : les gabarits n'habillent QUE du méta conversationnel ou une valeur DÉJÀ VÉRIFIÉE — jamais un fait inventé.
La sélection est pure (pas de RNG), déterministe, souveraine. stdlib pur.
"""
from __future__ import annotations

import zlib

# Banques de variantes. La 1re de chaque liste reste le libellé « canonique » (compat détection de repli).
_VARIANTES = {
    "note": [
        "C'est noté, je m'en souviendrai. Tu pourras me le redemander.",
        "Noté — je le retiens, tu pourras me le redemander.",
        "Entendu, c'est enregistré ; reviens me le demander quand tu veux.",
        "D'accord, je garde ça en mémoire.",
    ],
    "refus": [
        "D'accord — reformule ta question et je réponds.",
        "Pas de souci, reformule et je m'en occupe.",
        "Reformule-moi ça autrement et je réponds.",
    ],
    "salut": [
        "Bonjour !", "Salut !", "Bonjour, ravie de te parler !", "Coucou !",
    ],
    "cava": [
        "Je vais très bien, merci \U0001F642.",
        "Tout va bien, merci \U0001F642.",
        "Au top, merci \U0001F642. Et toi ?",
        "Ça roule, merci \U0001F642.",
    ],
    "invite": [
        "Pose-moi une question et je te réponds avec ce que je sais.",
        "Demande-moi ce que tu veux, je réponds avec ce que je sais.",
        "Vas-y, pose ta question.",
    ],
}


def _graine(s) -> int:
    """Hash STABLE (crc32) d'une graine — indépendant de PYTHONHASHSEED, donc reproductible entre exécutions."""
    return zlib.crc32(str(s).encode("utf-8"))


def varie(cle: str, graine="") -> str:
    """Variante déterministe pour l'intention `cle` selon `graine` (souvent le message utilisateur). '' si inconnue."""
    opts = _VARIANTES.get(cle)
    if not opts:
        return ""
    return opts[_graine(graine) % len(opts)]


def variantes(cle: str) -> list:
    """Toutes les variantes d'une intention (pour une détection robuste côté appelant, ex. est_fallback)."""
    return list(_VARIANTES.get(cle, []))
