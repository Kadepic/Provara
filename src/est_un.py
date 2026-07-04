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
import sys
import unicodedata

_DOSSIER = None
_DEFS = None                 # {entite_norm : genus_norm interné} (affichage du genre via _AFFICHE)
_CLASSE = None               # {entite_norm : set(hyperonymes_norm)} depuis les relations classe_*/categorie_*
_AFFICHE = {}                # {norm : forme accentuée d'affichage} (pour rendre « mammifère », pas « mammifere »)
_OFFSET = None               # {entite_norm : offset_octets dans definition_nom.jsonl} — la définition COMPLÈTE
                             # n'est PAS gardée en RAM (~70 MB économisés) : on la relit à la demande (seek).


def affiche(n: str) -> str:
    """Forme accentuée d'affichage d'un terme normalisé (« mammifere » -> « mammifère »), sinon le terme tel quel."""
    return _AFFICHE.get(_norm(n), n)


def definition(mot: str):
    """Définition COMPLÈTE d'un nom (texte du Wiktionnaire via `definition_nom`), ou None. Sert à « c'est quoi X ? ».
    Lecture À LA DEMANDE : l'index d'offsets (construit avec _defs, une passe unique) pointe la ligne du .jsonl ;
    on la relit au moment voulu au lieu de garder 292k textes en mémoire."""
    _defs()                                            # construit aussi _OFFSET (même passe)
    off = (_OFFSET or {}).get(_norm(mot))
    if off is None:
        return None
    try:
        with open(os.path.join(_dossier(), "definition_nom.jsonl"), "rb") as fh:
            fh.seek(off)
            obj = json.loads(fh.readline().decode("utf-8"))
            return obj.get("valeur")
    except (OSError, ValueError):
        return None

_STOP_GENUS = frozenset(
    "un une le la les de du des d l qui se qu il elle qui qu a à en et ou par pour sur qui qui ce qui "
    "action fait partie".split())
# Mots « méta-genre » : « ESPÈCE de poisson », « SORTE de fleur », « TYPE de véhicule » -> le vrai genre est le nom
# APRÈS (« poisson »). On saute donc ces têtes et on prend le contenu suivant.
_META_GENUS = frozenset(
    "espece sorte type genre variete famille groupe categorie ensemble classe forme membre representant "
    "sous-espece sous-genre nom terme unite element".split())


def _sans_accent(s: str) -> str:
    if s.isascii():                                   # fast-path : rien à désaccentuer (majorité des tokens)
        return s
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


_MOT_RE = re.compile(r"[A-Za-zÀ-ÿ’'\-]+")
# MARQUEURS DE CONTEXTE Wiktionnaire en tête de définition (registre/domaine/géo) : « (Afrique) », « (Biologie) »,
# « en Afrique du Sud, », « au Québec, ». Le GENRE est APRÈS ce marqueur, pas dedans — sans nettoyage, « apartheid »
# (« en Afrique du Sud, régime… ») recevait le genre « afrique » -> « continent » (faux is-a). FAUX=0 : on retire
# le marqueur pour lire le VRAI genre (« régime »). Un seul retrait de tête, très cadré (préposition + court + virgule).
_PAREN_TETE_RE = re.compile(r"^\s*(?:\([^)]{1,40}\)\s*)+")
# une clause locative de tête « (et) en Afrique du Sud, » — appliquée en BOUCLE pour absorber les listes
# (« en Asie du Sud, en Asie du Sud-Est et en Afrique du Sud, nom… » -> « nom… »).
_LOC_TETE_RE = re.compile(
    r"^\s*(?:et\s+)?(?:en|au|aux|dans|à|a|sur|chez|pour)\s+[^,.;]{1,40},\s+", re.IGNORECASE)


def _sans_contexte(definition: str) -> str:
    """Retire les marqueurs de contexte Wiktionnaire de TÊTE (« (Afrique) », « en Afrique du Sud, », listes de
    lieux) pour lire le VRAI genre (« régime », « aubergine »), pas le lieu. Ne retire que la tête ; rend le reste
    (ou l'original si tout serait retiré)."""
    d = _PAREN_TETE_RE.sub("", definition)
    for _ in range(6):                                # boucle bornée : absorbe une liste de clauses locatives
        d2 = _LOC_TETE_RE.sub("", d)
        if d2 == d:
            break
        d = d2
    return d if d.strip() else definition


def _genus_choisit(tokens):
    """Applique la cascade genus sur une liste de tokens : 1er nom non-méta non-adjectif, sinon 1er non-méta,
    sinon 1er contenu. (norm, affiché) ou None."""
    repli_meta = repli_contenu = None
    for mot in tokens:
        n = _norm(mot)
        if len(n) < 3 or n in _STOP_GENUS:
            continue
        if repli_contenu is None:
            repli_contenu = (n, mot.lower())
        if n in _META_GENUS:
            continue
        if not _est_adjectif(n):
            return n, mot.lower()         # 1er contenu non-méta, non-adjectif = le vrai genre (nom)
        if repli_meta is None:
            repli_meta = (n, mot.lower())
    return repli_meta or repli_contenu


def _genus_de(definition: str):
    """GENRE (genus-first) d'une définition = 1er NOM significatif. On saute : mots-outils, « méta-genres » (« espèce
    de poisson » -> poisson) ET adjectifs de tête (« grand poisson » -> poisson, via le POS du lexique). (norm, affiché).
    FENÊTRE DE TÊTE : le genus vit au début de la définition — on ne tokenise que les ~96 premiers caractères
    (findall C-speed sur 292k définitions au chargement), repli plein texte si la fenêtre ne donne rien. Le dernier
    token de la fenêtre est écarté s'il a pu être TRONQUÉ à la coupe (« mammif » n'est pas un genre)."""
    definition = _sans_contexte(definition)           # retire un marqueur de contexte de tête (registre/domaine/géo)
    if len(definition) > 96:
        tokens = _MOT_RE.findall(definition[:96])
        if tokens:
            tokens = tokens[:-1]                      # potentiellement coupé en plein mot
        g = _genus_choisit(tokens)
        if g:
            return g
    return _genus_choisit(_MOT_RE.findall(definition))


def _defs() -> dict:
    """Index {entité -> genus} PLUS index d'offsets (une SEULE passe binaire sur definition_nom.jsonl : le fichier
    de 292k lignes n'est lu qu'une fois pour les deux structures, et les clés sont PARTAGÉES entre les deux dicts).
    Le genus est interné (sys.intern) : « mammifere » n'existe qu'une fois en RAM, pas 8 000 fois."""
    global _DEFS, _OFFSET
    if _DEFS is None:
        _DEFS, _OFFSET = {}, {}
        chemin = os.path.join(_dossier(), "definition_nom.jsonl")
        try:
            with open(chemin, "rb") as fh:
                off = 0
                reste = b""
                fini = False
                while not fini:
                    # GROS BLOCS + split manuel : l'itération binaire ligne-à-ligne est ~8x plus lente sur un
                    # montage Windows (DrvFS) ; par blocs de 4 Mo on garde la vitesse ET les offsets exacts.
                    bloc = fh.read(1 << 22)
                    if bloc:
                        bloc = reste + bloc
                        lignes = bloc.split(b"\n")
                        reste = lignes.pop()
                    else:                             # fin de fichier : traiter l'éventuelle dernière ligne nue
                        lignes = [reste] if reste else []
                        fini = True
                    for brut in lignes:
                        ligne_off, off = off, off + len(brut) + 1
                        ligne = brut.strip()
                        if not ligne:
                            continue
                        try:                          # décodage EXPLICITE : json.loads(bytes) paierait
                            obj = json.loads(ligne.decode("utf-8"))   # detect_encoding à chaque ligne
                        except (ValueError, UnicodeDecodeError):
                            continue
                        if "_relation" in obj:
                            continue
                        e, v = obj.get("entite"), obj.get("valeur")
                        if e and v:
                            ne = _norm(e)
                            _OFFSET.setdefault(ne, ligne_off)
                            g = _genus_de(v)
                            if g:
                                _DEFS[ne] = sys.intern(g[0])
                                _AFFICHE.setdefault(g[0], g[1])
        except OSError:
            pass
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


_SEED = None                 # {entité_norm : genus_norm} — seed curé main (faits certains, prioritaire)


def _seed() -> dict:
    """Seed CURÉ à la main (est_un_seed.jsonl) : noms communs FR absents ou bruités dans definition_nom (rose->
    fleur, pomme->fruit, chêne->arbre…). Chaque entrée est un is-a VRAI incontestable -> PRIORITAIRE sur la
    définition (dont le genre peut être bruité : « chêne = *representants* de… », « laitue = *donne*… »)."""
    global _SEED
    if _SEED is None:
        _SEED = {}
        chemin = os.path.join(os.path.dirname(os.path.abspath(__file__)), "est_un_seed.jsonl")
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
                    e, v = o.get("entite"), o.get("valeur")
                    if e and v and "_relation" not in o:
                        _SEED[_norm(e)] = _norm(v)
                        _AFFICHE.setdefault(_norm(v), str(v).strip().lower())
        except OSError:
            pass
    return _SEED


def hyperonymes_directs(mot: str) -> list:
    """Hyperonymes DIRECTS sains de `mot` : seed curé (prioritaire) + classe(s) curée(s) + genre de la définition.
    Normalisés, sans doublon. Le seed vient EN TÊTE (fait certain incontestable, prime sur un genre bruité)."""
    n = _norm(mot)
    res = []
    s = _seed().get(n)                               # fait certain curé -> en tête, FAIT AUTORITÉ
    if s:
        res.append(s)
    for h in sorted(_classe().get(n, ())):
        if h not in res:
            res.append(h)
    if not s:                                        # mot seedé : on IGNORE le genre de définition (souvent bruité
        g = _defs().get(n)                           # pour ces mots courants : « chêne = representants… ») — le
        if g and g not in res:                       # seed est la vérité curée pour ce mot
            res.append(g)
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


_ENFANTS = None              # {hyperonyme_norm : set(entités_norm ayant cet hyperonyme direct)} — index inverse


def _enfants() -> dict:
    """Index inverse, valeurs stockées en TUPLES PRÉ-TRIÉS (pas des sets) : ~40 % de RAM en moins sur 292k entrées,
    et `hyponymes` n'a plus à retrier à chaque requête."""
    global _ENFANTS
    if _ENFANTS is None:
        brut = {}
        entites = set(_defs().keys()) | set(_classe().keys()) | set(_seed().keys())
        for e in entites:
            for h in hyperonymes_directs(e):
                brut.setdefault(h, []).append(e)
        _ENFANTS = {h: tuple(sorted(set(l))) for h, l in brut.items()}
    return _ENFANTS


def hyponymes(categorie: str, limite: int = 30, max_prof: int = 6) -> list:
    """Membres (hyponymes) d'une catégorie, transitivement (« félin » -> chat, lion, tigre… ; « poisson » -> requin,
    thon…). Descente en largeur dans l'index inverse. Faits/définitions réels uniquement. Liste triée, bornée."""
    from collections import deque
    dep = _norm(categorie)
    vus = {dep}
    trouve = []
    q = deque([(dep, 0)])
    enf = _enfants()
    while q and len(trouve) < limite * 3:
        c, d = q.popleft()
        if d >= max_prof:
            continue
        for e in enf.get(c, ()):                     # déjà trié à la construction de l'index
            if e not in vus:
                vus.add(e)
                trouve.append(e)
                q.append((e, d + 1))
    # NOTORIÉTÉ : les termes du lexique COMMUN (19k) d'abord (lion, tigre, léopard…), les obscurs ensuite (« engri »,
    # « pard ») — on ne les montre que pour compléter. Excellence : une liste d'exemples RECONNAISSABLES.
    pos = _pos()
    communs = sorted(e for e in trouve if e in pos)
    obscurs = sorted(e for e in trouve if e not in pos)
    if len(communs) >= 5:                # assez d'exemples RECONNAISSABLES -> on ne montre QU'EUX (liste propre)
        return communs[:limite]
    return (communs + obscurs)[:limite]  # catégorie peu couverte -> on complète avec les termes rares


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
