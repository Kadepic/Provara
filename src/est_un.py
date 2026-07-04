#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EST-UN — raisonnement is-a SAIN à partir des données DÉJÀ présentes (2026-07-04). Aucune ressource externe.

Deux sources, toutes deux dans la base (72 M de faits) :
  • relations CURÉES `classe_*` / `categorie_*` (« classe_animal » : chat -> mammifère, « faits certains ») ;
  • GENRE des `definition_nom` (Wiktionnaire via kaikki, genus-first : « chat = *mammifère* carnivore félin… »)
    -> le 1er mot significatif de la définition est l'hyperonyme, UN SEUL SENS par définition (pas de bruit de
    polysémie, contrairement au réseau de foule JeuxDeMots qui reste réservé au RECALL/paraphrase, jamais aux
    assertions is-a).

Chaînage transitif du genre : chat -> mammifère -> animal -> métazoaire. FAUX=0 : `est_un(x, y)` == True SEULEMENT
si un chemin de faits/définitions RÉELS relie x à y ; False = non dérivable (monde ouvert), jamais une négation
affirmée. Lecture directe des .jsonl (léger, pas le moteur lourd), cache mémoïsé. stdlib pur, souverain, hors-ligne.
"""
from __future__ import annotations

import json
import os
import re
import unicodedata

_DOSSIER = None
_DEFS = None                 # {entite_norm : (genus_norm, genus_affiché)}
_CLASSE = None               # {entite_norm : set(hyperonymes_norm)} depuis les relations classe_*/categorie_*
_AFFICHE = {}                # {norm : forme accentuée d'affichage} (pour rendre « mammifère », pas « mammifere »)


def affiche(n: str) -> str:
    """Forme accentuée d'affichage d'un terme normalisé (« mammifere » -> « mammifère »), sinon le terme tel quel."""
    return _AFFICHE.get(_norm(n), n)

_STOP_GENUS = frozenset(
    "un une le la les de du des d l qui se qu il elle qui qu a à en et ou par pour sur qui qui ce qui "
    "action fait partie".split())
# Mots « méta-genre » : « ESPÈCE de poisson », « SORTE de fleur », « TYPE de véhicule » -> le vrai genre est le nom
# APRÈS (« poisson »). On saute donc ces têtes et on prend le contenu suivant.
_META_GENUS = frozenset(
    "espece sorte type genre variete famille groupe categorie ensemble classe forme membre representant "
    "sous-espece sous-genre nom terme unite element".split())


def _sans_accent(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")


def _norm(s: str) -> str:
    return _sans_accent(str(s).lower()).strip()


def _dossier() -> str:
    global _DOSSIER
    if _DOSSIER is None:
        _DOSSIER = os.environ.get("LECTEUR_DATASETS_DIR") or os.path.join(
            os.environ.get("VERAX_ROOT", "."), "datasets", "lecteur")
    return _DOSSIER


def _lignes(relation: str):
    chemin = os.path.join(_dossier(), relation + ".jsonl")
    try:
        with open(chemin, encoding="utf-8") as fh:
            for ligne in fh:
                ligne = ligne.strip()
                if not ligne:
                    continue
                obj = json.loads(ligne)
                if "_relation" in obj:
                    continue
                yield obj
    except (OSError, ValueError):
        return


_POS = None
# adjectifs très courants en tête de définition (« Grand poisson… ») — filet si le POS ne couvre pas le mot.
_ADJ_COURANTS = frozenset(
    "grand grande gros grosse petit petite long longue court courte haut haute bas basse vieux vieille jeune "
    "beau belle joli jolie bon bonne mauvais nouveau ancien premier dernier gros petit large etroit".split())


def _pos() -> dict:
    """{mot_normalisé: classe} depuis `lexique_fr_pos.jsonl` (19k) — pour distinguer NOM d'ADJECTIF dans le genre."""
    global _POS
    if _POS is None:
        _POS = {}
        chemin = os.path.join(os.path.dirname(os.path.abspath(__file__)), "lexique_fr_pos.jsonl")
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
                    m, c = o.get("mot"), o.get("classe")
                    if m and c:
                        _POS.setdefault(_norm(m), c)
        except OSError:
            pass
    return _POS


def _est_adjectif(n: str) -> bool:
    return n in _ADJ_COURANTS or _pos().get(n) == "adjectif"


def _genus_de(definition: str):
    """GENRE (genus-first) d'une définition = 1er NOM significatif. On saute : mots-outils, « méta-genres » (« espèce
    de poisson » -> poisson) ET adjectifs de tête (« grand poisson » -> poisson, via le POS du lexique). (norm, affiché)."""
    contenu = []
    for mot in re.findall(r"[A-Za-zÀ-ÿ’'\-]+", definition):
        n = _norm(mot)
        if len(n) >= 3 and n not in _STOP_GENUS:
            contenu.append((n, mot.lower()))
    for n, aff in contenu:
        if n not in _META_GENUS and not _est_adjectif(n):
            return n, aff                 # 1er contenu non-méta, non-adjectif = le vrai genre (nom)
    for n, aff in contenu:
        if n not in _META_GENUS:
            return n, aff
    return contenu[0] if contenu else None


def _defs() -> dict:
    global _DEFS
    if _DEFS is None:
        _DEFS = {}
        for obj in _lignes("definition_nom"):
            e, v = obj.get("entite"), obj.get("valeur")
            if e and v:
                g = _genus_de(v)
                if g:
                    _DEFS[_norm(e)] = g
                    _AFFICHE.setdefault(g[0], g[1])
    return _DEFS


def _hyper_propre(v: str):
    """Valeur de classe RETENUE seulement si c'est un hyperonyme PROPRE : mot(s) court(s), sans ponctuation de
    libellé (« : », chiffres, parenthèses). Élimine le bruit « categorie IV : aire de gestion… »."""
    v = str(v).strip()
    if not v or any(c in v for c in ":()[]/;0123456789") or len(v.split()) > 2:
        return None
    return _norm(v)


def _classe() -> dict:
    """Index is-a DIRECT depuis les relations `classe_*` (curées, « faits certains » : classe_animal, classe_poisson…).
    On EXCLUT les `categorie_*` (souvent des libellés, pas des hyperonymes) et on filtre les valeurs propres."""
    global _CLASSE
    if _CLASSE is None:
        _CLASSE = {}
        try:
            rels = [f[:-6] for f in os.listdir(_dossier())
                    if f.endswith(".jsonl") and f.startswith("classe_")]
        except OSError:
            rels = []
        for rel in rels:
            for obj in _lignes(rel):
                e, v = obj.get("entite"), obj.get("valeur")
                h = _hyper_propre(v) if (e and v) else None
                if e and h:
                    _CLASSE.setdefault(_norm(e), set()).add(h)
                    _AFFICHE.setdefault(h, str(v).strip().lower())
    return _CLASSE


def hyperonymes_directs(mot: str) -> list:
    """Hyperonymes DIRECTS sains de `mot` : classe(s) curée(s) + genre de la définition. Normalisés, sans doublon."""
    n = _norm(mot)
    res = []
    for h in sorted(_classe().get(n, ())):
        if h not in res:
            res.append(h)
    g = _defs().get(n)
    if g and g[0] not in res:
        res.append(g[0])
    return res


def chaine_isa(mot: str, max_prof: int = 16) -> list:
    """Chaîne is-a transitive (du plus proche au plus lointain), sans cycle, bornée. La COLONNE VERTÉBRALE est le
    GENRE des définitions (`definition_nom`) — un seul par mot, fiable — avec repli sur une classe curée propre au
    1er saut. chat -> mammifère -> animal -> métazoaire. Faits/définitions réels uniquement (FAUX=0)."""
    from collections import deque
    depart = _norm(mot)
    vus = {depart}
    chaine = []
    q = deque([(depart, 0)])
    while q:
        w, d = q.popleft()
        if d >= max_prof:
            continue
        for h in hyperonymes_directs(w):             # genre (definition_nom) + classes curées propres
            if h not in vus:
                vus.add(h)
                chaine.append(h)
                q.append((h, d + 1))
    return chaine


def est_un(x: str, y: str) -> bool:
    """True SSI `y` est un hyperonyme (direct ou transitif) de `x`, dérivé de faits/définitions RÉELS. FAUX=0."""
    ny = _norm(y)
    if ny == _norm(x):
        return True
    return ny in hyperonymes_directs(x) or ny in set(chaine_isa(x))


def genre_commun(x: str, y: str):
    """Plus proche hyperonyme COMMUN de x et y (None si aucun). « chat » & « requin » -> « animal »."""
    cx = [_norm(x)] + chaine_isa(x)
    cy = set([_norm(y)] + chaine_isa(y))
    for a in cx:
        if a in cy:
            return a
    return None


def disponible() -> bool:
    return bool(_defs()) or bool(_classe())
