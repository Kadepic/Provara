#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SYNONYMES / PARAPHRASE — réseau lexico-sémantique français hors-ligne (JeuxDeMots, LIRMM, licence CC-BY-SA).

POURQUOI : le routeur conversationnel ne comprenait une question que dans la formulation prévue. « la bagnole de
sport », « combien gagne un toubib » ne touchaient pas les faits rangés sous « voiture », « médecin ». Ici on charge
un dictionnaire de synonymes/hyperonymes/contraires (extrait d'un dump JeuxDeMots, pondéré par les joueurs et filtré
par poids -> qualité), et on l'expose au routeur pour REFORMULER une requête ratée vers un terme que la base connaît.

FAUX=0 — rôle strictement de RAPPEL (recall), jamais d'assertion : les synonymes ne servent qu'à RETROUVER un fait ;
la réponse renvoyée reste un fait VÉRIFIÉ de la base (ou rien). Une reformulation par synonyme est SIGNALÉE à
l'utilisateur (« en comprenant … ») pour rester honnête. Aucun fait n'est fabriqué.

Données : `synonymes_fr.jsonl` (une ligne {"mot":…, "syn":[…], "hyper":[…], "anto":[…]}, triée par poids décroissant).
stdlib pur, chargement paresseux, souverain, hors-ligne.
"""
from __future__ import annotations

import json
import os
import unicodedata

_INDEX = None                       # {mot_normalisé: {"syn":[...], "hyper":[...], "anto":[...]}}

# mots-outils à NE PAS reformuler (ni les prendre pour du contenu à substituer)
_STOP = frozenset(
    "le la les un une de du des au aux et ou est sont a as ai en dans sur sous pour par avec sans "
    "que qui quoi dont ou quel quelle quels quelles combien comment pourquoi quand ce cet cette ces "
    "mon ma mes ton ta tes son sa ses notre nos votre vos leur leurs je tu il elle on nous vous ils elles "
    "me te se lui y ne pas plus tres bien c cela ca".split())


def _sans_accent(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")


def _norm(mot: str) -> str:
    return _sans_accent(str(mot).lower()).strip()


def _chemin_donnees() -> str:
    base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, "synonymes_fr.jsonl")


def _charge() -> dict:
    global _INDEX
    if _INDEX is None:
        _INDEX = {}
        chemin = os.environ.get("SYNONYMES_JSONL") or _chemin_donnees()
        try:
            with open(chemin, encoding="utf-8") as fh:
                for ligne in fh:
                    ligne = ligne.strip()
                    if not ligne:
                        continue
                    try:
                        o = json.loads(ligne)
                    except ValueError:
                        continue
                    mot = o.get("mot")
                    if not mot:
                        continue
                    _INDEX[_norm(mot)] = o
        except OSError:
            _INDEX = {}
    return _INDEX


def disponible() -> bool:
    return bool(_charge())


def synonymes(mot: str, k: int = 8) -> list:
    """Top-k synonymes (déjà triés par poids décroissant = plus validés d'abord). Liste normalisée, sans doublon."""
    o = _charge().get(_norm(mot))
    if not o:
        return []
    vus, res = set(), []
    for s in o.get("syn", [])[:k]:
        ns = _norm(s)
        if ns and ns != _norm(mot) and ns not in vus:
            vus.add(ns)
            res.append(ns)
    return res


def hyperonymes(mot: str, k: int = 6) -> list:
    o = _charge().get(_norm(mot))
    return [_norm(h) for h in o.get("hyper", [])[:k]] if o else []


def contraires(mot: str, k: int = 6) -> list:
    o = _charge().get(_norm(mot))
    return [_norm(a) for a in o.get("anto", [])[:k]] if o else []


def chaine_hyper(mot: str, max_prof: int = 8, k: int = 4) -> list:
    """Clôture TRANSITIVE des hyperonymes (chat -> félin -> mammifère -> animal…), en largeur, bornée et sans
    cycle. Faits lexicaux réels (JeuxDeMots r_isa filtré) — sert au raisonnement « est-un »."""
    from collections import deque
    depart = _norm(mot)
    vus, out = {depart}, []
    q = deque([(depart, 0)])
    while q:
        w, d = q.popleft()
        if d >= max_prof:
            continue
        for h in hyperonymes(w, k=k):
            if h and h not in vus:
                vus.add(h)
                out.append(h)
                q.append((h, d + 1))
    return out


def est_hyper(x: str, y: str) -> bool:
    """`y` est-il un hyperonyme (générique) de `x`, directement ou transitivement ? (chat est-un mammifère)."""
    ny = _norm(y)
    return ny != _norm(x) and (ny in set(chaine_hyper(x)) or ny in hyperonymes(x, k=30))


def est_synonyme(a: str, b: str) -> bool:
    """a et b sont-ils synonymes (relation directe dans le réseau, dans un sens ou l'autre) ?"""
    na, nb = _norm(a), _norm(b)
    return nb in synonymes(na, k=30) or na in synonymes(nb, k=30)


def variantes_requete(texte: str, k_syn: int = 3, max_variantes: int = 8, est_connu=None):
    """Reformulations de `texte` en substituant UN mot de contenu par un de ses synonymes forts. Renvoie une liste
    de (variante, mot_original, synonyme), la plus prometteuse d'abord. Sert de REPLI quand la requête exacte échoue.
    On ne substitue qu'un mot à la fois (précision) et on saute les mots-outils. FAUX=0 : ce n'est qu'une piste de
    RAPPEL — l'appelant doit re-vérifier le fait et signaler la reformulation.

    GARDE DÉSAMBIGUÏSATION : si `est_connu(mot_normalisé)` est fourni, on ne substitue QUE les mots INCONNUS de la
    base (argot/abréviations : « bagnole », « toubib »), jamais un mot courant déjà géré (« prix », « bosse ») —
    ça évite les substitutions de MAUVAIS SENS (« bosse »->« mont ») qui rendraient une réponse hors-sujet."""
    import re
    toks = re.findall(r"[\wà-ÿ']+", texte, re.UNICODE)
    variantes = []
    for i, tok in enumerate(toks):
        nt = _norm(tok)
        if len(nt) < 4 or nt in _STOP:
            continue
        if est_connu is not None and est_connu(nt):
            continue                       # mot standard déjà géré -> ne pas risquer un synonyme de mauvais sens
        for syn in synonymes(nt, k=k_syn):
            # remplace l'occurrence (insensible à la casse/accent via re) — 1re occurrence de ce token
            patron = re.compile(r"\b" + re.escape(tok) + r"\b")
            var = patron.sub(syn, texte, count=1)
            if var != texte:
                variantes.append((var, nt, syn))
            if len(variantes) >= max_variantes:
                return variantes
    return variantes
