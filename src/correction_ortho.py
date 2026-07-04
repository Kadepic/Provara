#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CORRECTION ORTHOGRAPHIQUE DE L'ENTRÉE — « guérir » le message avant tout matching conversationnel (2026-07-04).

POURQUOI : la couche conversationnelle (politesse, « ça va », intentions, têtes de relations) matchait le texte
EXACTEMENT. Une seule faute sur un mot-outil (« commen vas-tu », « bonjur », « coment ça va ») rendait tout l'étage
social AVEUGLE, et la question partait à tort en factuel/web. La correction floue existante ne visait QUE les entités
de la base ; l'entrée entière, elle, n'était pas soignée.

PRINCIPE (fusion de signaux, sans LLM) : on corrige chaque mot vers un VOCABULAIRE FERMÉ et curé (mots sociaux,
interrogatifs, connecteurs, têtes de relations) par la FUSION de deux mesures — distance d'édition (Levenshtein) ET
clé PHONÉTIQUE française (le « t » final muet fait sonner « commen » comme « comment »). Aucune des deux seule n'est
sûre ; ensemble elles corrigent robustement.

FAUX=0 — garanties :
  • On ne corrige QUE vers un vocabulaire FERMÉ de mots-outils/relations (jamais vers un nom d'entité : corriger une
    entité changerait le SENS de la question — ça reste au ressort de la résolution floue d'entité, séparée).
  • On ne touche JAMAIS un mot déjà VALIDE (test `est_mot_valide`) : « pomme », « somme », « ville » restent intacts.
  • La correction ne CHANGE PAS un fait : elle ne fait que rendre lisible l'INTENTION (social/relation) d'un message
    mal orthographié. La réponse factuelle, elle, reste vérifiée-ou-abstention en aval.

stdlib pur, déterministe, souverain, hors-ligne.
"""
from __future__ import annotations

import unicodedata

__all__ = ["cle_phonetique", "distance", "corrige_mot", "guerit"]


def _sans_accent(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")


def _norm(mot: str) -> str:
    return _sans_accent(str(mot).lower()).strip()


def distance(a: str, b: str, plafond: int = 2) -> int:
    """Distance de Damerau (OSA) bornée : compte l'ÉCHANGE de deux lettres adjacentes comme UNE seule faute
    (« combein »↔« combien », « pesudo »↔« pseudo ») — les transpositions sont parmi les fautes de frappe les plus
    fréquentes. Si l'écart de longueur dépasse `plafond`, on renonce (retourne plafond+1)."""
    if a == b:
        return 0
    la, lb = len(a), len(b)
    if abs(la - lb) > plafond:
        return plafond + 1
    prev2 = None                                       # ligne i-2 (pour la transposition)
    prev = list(range(lb + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        mini = i
        for j, cb in enumerate(b, 1):
            v = min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb))
            if (prev2 is not None and j >= 2 and ca == b[j - 2] and a[i - 2] == cb):
                v = min(v, prev2[j - 2] + 1)           # transposition adjacente = 1
            cur.append(v)
            if v < mini:
                mini = v
        if mini > plafond:                 # toute la ligne dépasse déjà -> inutile de continuer
            return plafond + 1
        prev2, prev = prev, cur
    return prev[lb]


# — CLÉ PHONÉTIQUE FRANÇAISE (simplifiée, inspirée de Soundex-FR/Phonex). Deux mots qui « sonnent » pareil en
#   français partagent la même clé : « comment »/« commen »/« coment » -> « KOMAN » ; « bonjour »/« bonjours » ->
#   « BONJUR ». Suffisant pour rapprocher les fautes phonétiques que la distance d'édition seule rate. Pas une
#   transcription IPA exacte : un ensemble de règles robustes qui préservent le squelette consonne+voyelle audible.
_DIGRAMMES = [
    ("eau", "o"), ("au", "o"), ("ai", "e"), ("ei", "e"), ("ou", "u"), ("eu", "e"), ("oeu", "e"),
    ("ph", "f"), ("ch", "5"), ("sch", "5"), ("gn", "n"), ("qu", "k"), ("gu", "g"),
    ("ss", "s"), ("sc", "s"), ("th", "t"),
]


def cle_phonetique(mot: str) -> str:
    """Clé phonétique française approximative d'un mot (chaîne). Mots homophones -> même clé."""
    s = _norm(mot)
    if not s:
        return ""
    s = "".join(c for c in s if c.isalpha())
    if not s:
        return ""
    # h muet
    s = s.replace("h", "")
    # digrammes/voyelles composées (ordre : les plus longs d'abord via la liste)
    for a, b in _DIGRAMMES:
        s = s.replace(a, b)
    # c/g contextuels
    out = []
    for i, c in enumerate(s):
        suiv = s[i + 1] if i + 1 < len(s) else ""
        if c == "c":
            out.append("s" if suiv in "eiy" else "k")
        elif c == "g":
            out.append("j" if suiv in "eiy" else "g")
        elif c == "q":
            out.append("k")
        elif c == "y":
            out.append("i")
        else:
            out.append(c)
    s = "".join(out)
    # consonnes finales muettes courantes en français (t, d, s, x, p, g, z + e final muet)
    while s and s[-1] in "tdsxpgze":
        s = s[:-1]
    # réductions : doublons consécutifs
    red = []
    for c in s:
        if not red or red[-1] != c:
            red.append(c)
    return "".join(red)


def corrige_mot(mot: str, vocab_norm, phon_index=None, est_mot_valide=None):
    """Corrige `mot` vers le meilleur candidat du VOCABULAIRE FERMÉ (dict {forme_normalisée: forme_affichée}), ou
    renvoie `mot` inchangé. Fusion : (a) distance d'édition ≤1 ; sinon (b) même clé phonétique ET distance ≤2.
      • `vocab_norm` : {clé normalisée sans accent -> forme à réinjecter}.
      • `phon_index` : {clé phonétique -> [clés normalisées]} (optionnel, accélère (b)).
      • `est_mot_valide(mot_norm)` : True si le mot EST déjà un vrai mot -> on NE corrige PAS (anti-corruption).
    FAUX=0 : ne corrige jamais un mot valide, ne vise qu'un vocabulaire fermé."""
    mn = _norm(mot)
    if not mn or mn in vocab_norm:
        return mot
    if len(mn) < 3:                                  # trop court : correction hasardeuse (« de », « la »…)
        return mot
    if est_mot_valide is not None and est_mot_valide(mn):
        return mot                                   # déjà un vrai mot -> intact
    # (a) distance d'édition ≤1, même initiale (une faute la préserve quasi toujours)
    meilleur, meilleure_d = None, 3
    for cible in vocab_norm:
        if cible[0] != mn[0] or abs(len(cible) - len(mn)) > 1:
            continue
        d = distance(mn, cible, plafond=1)
        if d <= 1 and d < meilleure_d:
            meilleur, meilleure_d = cible, d
    if meilleur is not None:
        return vocab_norm[meilleur]
    # (b) homophonie : même clé phonétique, distance ≤2 (rattrape « koman »->« comment »)
    kp = cle_phonetique(mn)
    if kp:
        candidats = phon_index.get(kp, []) if phon_index else [c for c in vocab_norm if cle_phonetique(c) == kp]
        meilleur, meilleure_d = None, 3
        for cible in candidats:
            d = distance(mn, cible, plafond=2)
            if d <= 2 and d < meilleure_d:
                meilleur, meilleure_d = cible, d
        if meilleur is not None:
            return vocab_norm[meilleur]
    return mot


def construit_index(vocab):
    """Prépare (vocab_norm, phon_index) à partir d'un itérable de formes. Réutilisable (à construire une fois)."""
    vocab_norm = {}
    for forme in vocab:
        vocab_norm.setdefault(_norm(forme), forme)
    phon_index: dict = {}
    for cn in vocab_norm:
        phon_index.setdefault(cle_phonetique(cn), []).append(cn)
    return vocab_norm, phon_index


def guerit(texte: str, vocab_norm, phon_index=None, est_mot_valide=None) -> str:
    """Renvoie `texte` avec chaque mot corrigé vers le vocabulaire fermé (ponctuation et casse des mots non corrigés
    préservées au mieux). Utilisé pour la DÉTECTION d'intention/social — pas pour altérer un fait."""
    import re
    def _remp(m):
        return corrige_mot(m.group(0), vocab_norm, phon_index, est_mot_valide)
    return re.sub(r"[A-Za-zÀ-ÿ]+", _remp, texte)
